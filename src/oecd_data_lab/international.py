
from pathlib import Path

import pandas as pd

from oecd_data_lab.config import START_PERIOD, END_PERIOD


SOURCE_BY_COUNTRY = {
    "BRA": "COICOP_1999",
    "MEX": "COICOP_2018",
    "CHL": "COICOP_2018",
    "COL": "COICOP_1999",
    "CRI": "COICOP_2018",
    "USA": "COICOP_1999",
    "DEU": "COICOP_1999",
    "JPN": "COICOP_2018",
    "GBR": "COICOP_1999",
    "CAN": "COICOP_1999",
    "TUR": "COICOP_1999",
}

EXPECTED_DIMENSIONS = {
    "FREQ": "M",
    "METHODOLOGY": "N",
    "MEASURE": "CPI",
    "UNIT_MEASURE": "IX",
    "EXPENDITURE": "_T",
    "ADJUSTMENT": "N",
    "TRANSFORMATION": "_Z",
}


def project_root() -> Path:
    for directory in Path(__file__).resolve().parents:
        if (directory / "pyproject.toml").is_file():
            return directory
    raise FileNotFoundError("Raiz do projeto não encontrada.")


def build_international_silver() -> pd.DataFrame:
    root = project_root()

    sources = {
        "COICOP_1999": (
            root / "data/coverage/coverage_response.csv"
        ),
        "COICOP_2018": (
            root / "data/coverage/coverage_2018_response.csv"
        ),
    }

    selected = []

    for source, path in sources.items():
        if not path.exists():
            raise FileNotFoundError(path)

        df = pd.read_csv(path, low_memory=False)

        countries = [
            code
            for code, chosen_source in SOURCE_BY_COUNTRY.items()
            if chosen_source == source
        ]

        subset = df[df["REF_AREA"].isin(countries)].copy()

        required = (
            set(EXPECTED_DIMENSIONS)
            | {
                "REF_AREA", "TIME_PERIOD", "OBS_VALUE",
                "BASE_PER", "OBS_STATUS",
            }
        )

        missing_columns = required - set(subset.columns)
        if missing_columns:
            raise ValueError(
                f"{source}: colunas ausentes: "
                f"{sorted(missing_columns)}"
            )

        for column, expected in EXPECTED_DIMENSIONS.items():
            if not subset[column].eq(expected).all():
                raise ValueError(
                    f"{source}: dimensão {column} incompatível."
                )

        subset["source_dataset"] = source
        selected.append(subset)

    silver = pd.concat(selected, ignore_index=True)

    silver = silver.rename(columns={
        "REF_AREA": "country",
        "TIME_PERIOD": "period",
        "OBS_VALUE": "cpi_index",
        "BASE_PER": "base_period",
        "OBS_STATUS": "observation_status",
    })

    silver["period"] = pd.to_datetime(
        silver["period"], format="%Y-%m"
    )
    silver["cpi_index"] = pd.to_numeric(
        silver["cpi_index"], errors="coerce"
    )

    if silver["cpi_index"].isna().any():
        raise ValueError("Índices inválidos ou ausentes.")

    if (silver["cpi_index"] <= 0).any():
        raise ValueError("Índices não positivos.")

    if silver.duplicated(["country", "period"]).any():
        raise ValueError("Duplicatas por país e mês.")

    expected = pd.period_range(
        START_PERIOD, END_PERIOD, freq="M"
    )

    for country, group in silver.groupby("country"):
        observed = pd.PeriodIndex(
            group["period"], freq="M"
        )

        missing = expected.difference(observed)
        extra = observed.difference(expected)

        allowed = (
            {"2025-10"} if country == "USA" else set()
        )

        unexpected = set(map(str, missing)) - allowed

        if unexpected or len(extra):
            raise ValueError(
                f"{country}: cobertura inesperada. "
                f"Ausentes: {sorted(unexpected)}; "
                f"extras: {list(map(str, extra))}"
            )

        if group["base_period"].isna().any():
            raise ValueError(
                f"{country}: ano-base ausente."
            )

        if group["base_period"].nunique() != 1:
            raise ValueError(
                f"{country}: mudança de ano-base na série."
            )

    actual_countries = set(silver["country"])

    if actual_countries != set(SOURCE_BY_COUNTRY):
        raise ValueError(
            "Países retornados não correspondem ao catálogo."
        )

    silver = silver.sort_values(
        ["country", "period"]
    ).reset_index(drop=True)

    output = (
        root / "data/silver"
        / "oecd_cpi_international_2014_2025.parquet"
    )

    output.parent.mkdir(parents=True, exist_ok=True)
    silver.to_parquet(output, index=False)

    print("=== SILVER INTERNACIONAL ===")
    print(f"Arquivo: {output}")
    print(
        silver.groupby("country")
        .agg(
            observacoes=("cpi_index", "size"),
            fonte=("source_dataset", "first"),
            ano_base=("base_period", "first"),
        )
        .to_string()
    )

    return silver


if __name__ == "__main__":
    build_international_silver()
