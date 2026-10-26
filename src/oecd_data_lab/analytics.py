"""Gera inflação interanual (YoY) a partir de índices CPI da camada Silver."""
from pathlib import Path

import pandas as pd

from oecd_data_lab.config import START_PERIOD, END_PERIOD


from pathlib import Path


def find_project_root() -> Path:
    """Localiza a raiz do projeto pelo pyproject.toml."""

    for directory in Path(__file__).resolve().parents:
        if (directory / "pyproject.toml").is_file():
            return directory

    raise FileNotFoundError(
        "Não foi possível localizar o pyproject.toml."
    )


ROOT = find_project_root()



def calculate_yoy(silver: pd.DataFrame) -> pd.DataFrame:
    """Compara cada observação com o mesmo mês do ano anterior.

    Mantém os meses disponíveis na Silver; devolve NaN quando não existe
    observação exatamente 12 meses antes. Não interpola lacunas.
    """
    required = {"country", "period", "cpi_index"}
    missing = required - set(silver.columns)
    if missing:
        raise ValueError(f"Colunas Silver ausentes: {sorted(missing)}")
    if silver.empty:
        raise ValueError("Silver vazia.")

    data = silver.copy()
    data["period"] = pd.to_datetime(data["period"], errors="raise")
    if data["period"].isna().any() or not data["period"].dt.is_month_start.all():
        raise ValueError("'period' deve ser uma data mensal no primeiro dia do mês.")
    data["cpi_index"] = pd.to_numeric(data["cpi_index"], errors="coerce")
    if data["cpi_index"].isna().any() or (data["cpi_index"] <= 0).any():
        raise ValueError("Índices CPI devem ser numéricos e positivos.")
    if data.duplicated(["country", "period"]).any():
        raise ValueError("Há duplicatas por país e mês na Silver.")

    previous = data[["country", "period", "cpi_index"]].copy()
    previous["period"] = (previous["period"].dt.to_period("M") + 12).dt.to_timestamp()
    previous = previous.rename(columns={"cpi_index": "cpi_index_12m_ago"})

    gold = data.merge(previous, on=["country", "period"], how="left", validate="one_to_one")
    gold["inflation_yoy_pct"] = (
        (gold["cpi_index"] / gold["cpi_index_12m_ago"] - 1) * 100
    )
    gold["indicator"] = "CPI_YOY"
    gold["unit"] = "PERCENT"
    return gold.sort_values(["country", "period"]).reset_index(drop=True)


def build_gold() -> Path:
    root = find_project_root()
    stem = f"oecd_cpi_{START_PERIOD[:4]}_{END_PERIOD[:4]}"
    silver_file = root / "data" / "silver" / f"{stem}.parquet"
    gold_file = root / "data" / "gold" / f"{stem}_yoy.parquet"
    if not silver_file.is_file():
        raise FileNotFoundError(f"Silver não encontrada: {silver_file}")
    gold = calculate_yoy(pd.read_parquet(silver_file))
    gold_file.parent.mkdir(parents=True, exist_ok=True)
    gold.to_parquet(gold_file, index=False)
    print(f"Gold criada: {gold_file}")
    print(gold.groupby("country").agg(
        observacoes=("period", "size"),
        taxas_disponiveis=("inflation_yoy_pct", "count"),
    ))
    return gold_file


if __name__ == "__main__":
    build_gold()
