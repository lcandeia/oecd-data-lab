"""Valida dados Bronze e produz a camada Silver em Parquet."""

from pathlib import Path

import pandas as pd

from oecd_data_lab.config import (
    INITIAL_OECD_COUNTRIES, START_PERIOD, END_PERIOD,
)
from oecd_data_lab.ingestion import project_root
from oecd_data_lab.validation import validate_cpi

# Exceção documentada: USA 2025-10 não teve índice geral de CPI publicado.
KNOWN_MISSING = {("USA", "2025-10")}


def process_cpi() -> pd.DataFrame:
    print("=== OECD DATA LAB | BRONZE -> SILVER ===")
    root = project_root()
    stem = f"oecd_cpi_{START_PERIOD[:4]}_{END_PERIOD[:4]}"
    raw_file = root / "data" / "raw" / f"{stem}_raw.csv"
    silver_file = root / "data" / "silver" / f"{stem}.parquet"
    if not raw_file.is_file():
        raise FileNotFoundError(f"Arquivo Bronze não encontrado: {raw_file}")

    df = pd.read_csv(raw_file, low_memory=False)
    print(f"Observações recebidas: {len(df)}")
    validate_cpi(
        df,
        start_period=START_PERIOD,
        end_period=END_PERIOD,
        expected_countries=set(INITIAL_OECD_COUNTRIES),
        allowed_missing=KNOWN_MISSING,
    )

    columns = {
        "REF_AREA": "country", "TIME_PERIOD": "period",
        "OBS_VALUE": "cpi_index", "FREQ": "frequency",
        "METHODOLOGY": "methodology", "MEASURE": "measure",
        "UNIT_MEASURE": "unit", "EXPENDITURE": "expenditure",
        "ADJUSTMENT": "adjustment", "TRANSFORMATION": "transformation",
        "BASE_PER": "base_period", "OBS_STATUS": "observation_status",
    }
    silver = df[list(columns)].rename(columns=columns).copy()
    silver["period"] = pd.to_datetime(silver["period"], format="%Y-%m")
    silver["cpi_index"] = pd.to_numeric(silver["cpi_index"], errors="raise")
    silver = silver.sort_values(["country", "period"]).reset_index(drop=True)
    silver_file.parent.mkdir(parents=True, exist_ok=True)
    silver.to_parquet(silver_file, index=False, engine="pyarrow")
    print(f"Arquivo Silver: {silver_file}")
    print(silver.groupby("country").agg(
        observacoes=("cpi_index", "size"),
        inicio=("period", "min"), fim=("period", "max"),
    ))
    return silver


if __name__ == "__main__":
    process_cpi()
