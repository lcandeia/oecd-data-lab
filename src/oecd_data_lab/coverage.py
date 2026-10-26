
from io import BytesIO
from pathlib import Path

import pandas as pd
import requests

from oecd_data_lab.config import (
    COUNTRIES,
    LATAM_COUNTRIES,
    START_PERIOD,
    END_PERIOD,
)


BASE_URL = "https://sdmx.oecd.org/public/rest/data"

DATASET = "OECD.SDD.TPS,DSD_PRICES@DF_PRICES_ALL,1.0"

SERIES_KEY = (
    f"{'+'.join(COUNTRIES)}.M.N.CPI.IX._T.N._Z"
)


def find_project_root() -> Path:
    for directory in Path(__file__).resolve().parents:
        if (directory / "pyproject.toml").is_file():
            return directory

    raise FileNotFoundError(
        "Raiz do projeto não encontrada."
    )


def check_coverage() -> pd.DataFrame:
    """Consulta e analisa a cobertura internacional do CPI."""

    print("=== OECD DATA LAB | COUNTRY COVERAGE ===")

    root = find_project_root()

    params = {
        "startPeriod": START_PERIOD,
        "endPeriod": END_PERIOD,
        "dimensionAtObservation": "AllDimensions",
        "format": "csvfile",
    }

    url = f"{BASE_URL}/{DATASET}/{SERIES_KEY}"

    print(f"Países solicitados: {len(COUNTRIES)}")
    print(f"Período: {START_PERIOD} a {END_PERIOD}")

    response = requests.get(
        url,
        params=params,
        timeout=120,
    )
    response.raise_for_status()

    df = pd.read_csv(
        BytesIO(response.content),
        low_memory=False,
    )

    required = {
        "REF_AREA", "TIME_PERIOD", "OBS_VALUE"
    }

    if df.empty or not required.issubset(df.columns):
        raise ValueError(
            "A resposta está vazia ou possui colunas inesperadas."
        )

    # Verificamos a quantidade de períodos distintos.
    expected_periods = pd.period_range(
        START_PERIOD, END_PERIOD, freq="M"
    )

    expected = len(expected_periods)
    records = []

    for code, name in COUNTRIES.items():
        country_df = df[df["REF_AREA"] == code].copy()

        periods = pd.PeriodIndex(
            country_df["TIME_PERIOD"], freq="M"
        ) if not country_df.empty else pd.PeriodIndex([], freq="M")

        observed = periods.unique()
        missing = expected_periods.difference(observed)

        values = pd.to_numeric(
            country_df["OBS_VALUE"], errors="coerce"
        )

        duplicate_count = country_df.duplicated(
            ["REF_AREA", "TIME_PERIOD"]
        ).sum()

        records.append({
            "country": code,
            "country_name": name,
            "region": (
                "LATAM" if code in LATAM_COUNTRIES
                else "REFERENCE"
            ),
            "observations": len(country_df),
            "months_available": len(observed),
            "months_expected": expected,
            "months_missing": len(missing),
            "missing_periods": ",".join(map(str, missing)),
            "invalid_values": int(values.isna().sum()),
            "duplicate_periods": int(duplicate_count),
            "first_period": (
                str(observed.min()) if len(observed) else None
            ),
            "last_period": (
                str(observed.max()) if len(observed) else None
            ),
        })

    report = pd.DataFrame(records)

    report["coverage_pct"] = (
        report["months_available"]
        / report["months_expected"] * 100
    ).round(2)

    report["status"] = "PARTIAL"

    report.loc[
        report["months_available"].eq(0),
        "status",
    ] = "NOT_FOUND"

    report.loc[
        report["months_missing"].eq(0)
        & report["invalid_values"].eq(0)
        & report["duplicate_periods"].eq(0),
        "status",
    ] = "COMPLETE"

    # Salvamos o relatório e a resposta para auditoria.
    output_dir = root / "data" / "coverage"
    output_dir.mkdir(parents=True, exist_ok=True)

    report.to_csv(
        output_dir / "country_coverage.csv",
        index=False,
        encoding="utf-8-sig",
    )

    (output_dir / "coverage_response.csv").write_bytes(
        response.content
    )

    print("\n=== COBERTURA POR PAÍS ===")

    print(
        report[
            [
                "country",
                "region",
                "months_available",
                "months_missing",
                "coverage_pct",
                "status",
            ]
        ].to_string(index=False)
    )

    print("\nRelatório salvo em:")
    print(output_dir / "country_coverage.csv")

    return report


if __name__ == "__main__":
    check_coverage()
