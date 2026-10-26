
from io import BytesIO
from pathlib import Path
import json
from datetime import datetime, timezone

import pandas as pd
import requests

from oecd_data_lab.config import (
    COUNTRIES,
    START_PERIOD,
    END_PERIOD,
)


BASE_URL = "https://sdmx.oecd.org/public/rest/data"

DATASET = (
    "OECD.SDD.TPS,"
    "DSD_PRICES_COICOP2018@DF_PRICES_C2018_ALL,1.0"
)

# Mesmo indicador utilizado na primeira consulta:
# Mensal, CPI nacional, índice, total, sem ajuste
SERIES_KEY = (
    f"{'+'.join(COUNTRIES)}.M.N.CPI.IX._T.N._Z"
)


def project_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / "pyproject.toml").is_file():
            return parent

    raise FileNotFoundError("Raiz do projeto não encontrada.")


def main() -> None:
    print("=== OECD DATA LAB | COICOP 2018 ===")

    root = project_root()
    output = root / "data" / "coverage"
    output.mkdir(parents=True, exist_ok=True)

    url = f"{BASE_URL}/{DATASET}/{SERIES_KEY}"

    params = {
        "startPeriod": START_PERIOD,
        "endPeriod": END_PERIOD,
        "dimensionAtObservation": "AllDimensions",
        "format": "csvfile",
    }

    print(f"Consultando {len(COUNTRIES)} países...")

    response = requests.get(
        url,
        params=params,
        timeout=120,
    )

    print(f"HTTP: {response.status_code}")
    response.raise_for_status()

    raw_path = output / "coverage_2018_response.csv"
    raw_path.write_bytes(response.content)

    df = pd.read_csv(
        BytesIO(response.content),
        low_memory=False,
    )

    required = {
        "REF_AREA", "TIME_PERIOD", "OBS_VALUE",
        "FREQ", "MEASURE", "UNIT_MEASURE",
        "EXPENDITURE", "ADJUSTMENT", "TRANSFORMATION",
    }

    if df.empty or not required.issubset(df.columns):
        raise ValueError(
            "Resposta vazia ou estrutura inesperada."
        )

    expected = pd.period_range(
        START_PERIOD,
        END_PERIOD,
        freq="M",
    )

    records = []

    for code, name in COUNTRIES.items():
        subset = df[df["REF_AREA"] == code].copy()

        periods = (
            pd.PeriodIndex(
                subset["TIME_PERIOD"], freq="M"
            )
            if not subset.empty
            else pd.PeriodIndex([], freq="M")
        )

        unique_periods = periods.unique()
        missing = expected.difference(unique_periods)

        numeric_values = pd.to_numeric(
            subset["OBS_VALUE"],
            errors="coerce",
        )

        records.append({
            "country": code,
            "country_name": name,
            "dataset": "COICOP_2018",
            "observations": len(subset),
            "months_available": len(unique_periods),
            "months_missing": len(missing),
            "coverage_pct": round(
                100 * len(unique_periods) / len(expected), 2
            ),
            "first_period": (
                str(unique_periods.min())
                if len(unique_periods) else None
            ),
            "last_period": (
                str(unique_periods.max())
                if len(unique_periods) else None
            ),
            "missing_periods": ",".join(
                map(str, missing)
            ),
            "invalid_values": int(
                numeric_values.isna().sum()
            ),
            "duplicate_periods": int(
                subset.duplicated(
                    ["REF_AREA", "TIME_PERIOD"]
                ).sum()
            ),
        })

    report = pd.DataFrame(records)

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

    report_path = output / "country_coverage_2018.csv"

    report.to_csv(
        report_path,
        index=False,
        encoding="utf-8-sig",
    )

    metadata = {
        "source": "OECD SDMX API",
        "dataset": DATASET,
        "request_url": response.url,
        "retrieved_at_utc": datetime.now(
            timezone.utc
        ).isoformat(),
        "rows": len(df),
    }

    (output / "coverage_2018_metadata.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print("\n=== COBERTURA COICOP 2018 ===")
    print(
        report[
            [
                "country", "months_available",
                "months_missing", "coverage_pct",
                "first_period", "last_period", "status",
            ]
        ].to_string(index=False)
    )

    print(f"\nRelatório salvo: {report_path}")


if __name__ == "__main__":
    main()
