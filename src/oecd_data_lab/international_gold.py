
from pathlib import Path

import pandas as pd


def find_project_root() -> Path:
    """Localiza a raiz do projeto."""
    for directory in Path(__file__).resolve().parents:
        if (directory / "pyproject.toml").is_file():
            return directory

    raise FileNotFoundError("Raiz do projeto não encontrada.")


def calculate_inflation_yoy(
    silver: pd.DataFrame,
) -> pd.DataFrame:
    """
    Calcula a inflação acumulada em 12 meses.

    Usa correspondência exata por país e mês.
    Não preenche dados ausentes.
    """
    required = {
        "country", "period", "cpi_index",
        "source_dataset", "base_period",
    }

    missing = required - set(silver.columns)

    if missing:
        raise ValueError(
            f"Colunas ausentes: {sorted(missing)}"
        )

    df = silver.copy()

    df["period"] = pd.to_datetime(df["period"])
    df["cpi_index"] = pd.to_numeric(
        df["cpi_index"], errors="raise"
    )

    if df[["country", "period", "cpi_index"]].isna().any().any():
        raise ValueError("Dados essenciais ausentes.")

    if (df["cpi_index"] <= 0).any():
        raise ValueError("Índices devem ser positivos.")

    if df.duplicated(["country", "period"]).any():
        raise ValueError("Duplicatas por país e mês.")

    # Cria uma tabela dos índices históricos.
    previous = df[
        ["country", "period", "cpi_index"]
    ].copy()

    # Desloca as datas históricas 12 meses à frente.
    # Exemplo: 2024-01 -> 2025-01
    previous["period"] = (
        previous["period"] + pd.DateOffset(months=12)
    )

    previous = previous.rename(
        columns={"cpi_index": "cpi_index_12m_ago"}
    )

    # Associa cada mês ao mesmo mês do ano anterior.
    gold = df.merge(
        previous,
        on=["country", "period"],
        how="left",
        validate="one_to_one",
    )

    gold["inflation_yoy"] = (
        (
            gold["cpi_index"]
            / gold["cpi_index_12m_ago"]
        ) - 1
    ) * 100

    gold["indicator"] = "CPI_YOY"
    gold["unit"] = "PERCENT"

    gold = gold.sort_values(
        ["country", "period"]
    ).reset_index(drop=True)

    return gold


def main() -> None:
    root = find_project_root()

    silver_file = (
        root / "data" / "silver"
        / "oecd_cpi_international_2014_2025.parquet"
    )

    gold_file = (
        root / "data" / "gold"
        / "oecd_inflation_international_yoy.parquet"
    )

    if not silver_file.is_file():
        raise FileNotFoundError(silver_file)

    silver = pd.read_parquet(silver_file)

    gold = calculate_inflation_yoy(silver)

    gold_file.parent.mkdir(
        parents=True, exist_ok=True
    )

    gold.to_parquet(gold_file, index=False)

    summary = gold.groupby("country").agg(
        observacoes=("cpi_index", "size"),
        taxas_disponiveis=("inflation_yoy", "count"),
        primeira_data=("period", "min"),
        ultima_data=("period", "max"),
    )

    print("=== OECD INFLATION LAB | GOLD ===")
    print(summary.to_string())

    print("\nTotal de taxas disponíveis:")
    print(gold["inflation_yoy"].count())

    print(f"\nGold criada: {gold_file}")


if __name__ == "__main__":
    main()
