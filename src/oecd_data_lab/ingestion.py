"""Coleta CPI da OCDE e preserva a resposta bruta e sua proveniência."""

from datetime import datetime, timezone
from io import BytesIO
import json
from pathlib import Path

import pandas as pd
import requests

from oecd_data_lab.config import (
    INITIAL_OECD_COUNTRIES,
    START_PERIOD,
    END_PERIOD,
    FREQUENCY,
)

BASE_URL = "https://sdmx.oecd.org/public/rest/data"
DATASET = "OECD.SDD.TPS,DSD_PRICES@DF_PRICES_ALL,1.0"
SERIES_KEY = f"{'+'.join(INITIAL_OECD_COUNTRIES)}.{FREQUENCY}.N.CPI.IX._T.N._Z"
URL = f"{BASE_URL}/{DATASET}/{SERIES_KEY}"
PARAMS = {
    "startPeriod": START_PERIOD,
    "endPeriod": END_PERIOD,
    "dimensionAtObservation": "AllDimensions",
    "format": "csvfile",
}


def project_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / "pyproject.toml").is_file():
            return parent
    raise FileNotFoundError("pyproject.toml não encontrado na árvore do projeto.")


def fetch_oecd_data() -> tuple[pd.DataFrame, bytes, str]:
    print("Conectando à API da OCDE...")
    try:
        response = requests.get(URL, params=PARAMS, timeout=60)
        print(f"Status HTTP: {response.status_code}")
        response.raise_for_status()
    except requests.RequestException as exc:
        raise RuntimeError(f"Falha na consulta à OCDE: {exc}") from exc

    if not response.content:
        raise ValueError("A API retornou uma resposta vazia.")
    try:
        df = pd.read_csv(BytesIO(response.content), low_memory=False)
    except (pd.errors.ParserError, UnicodeError, ValueError) as exc:
        raise ValueError("Não foi possível interpretar o CSV retornado.") from exc
    if df.empty:
        raise ValueError("A API retornou zero observações.")
    required = {"REF_AREA", "TIME_PERIOD", "OBS_VALUE"}
    if missing := required - set(df.columns):
        raise ValueError(f"Colunas obrigatórias ausentes: {sorted(missing)}")
    return df, response.content, response.url


def save_raw_data(raw: bytes, request_url: str, rows: int) -> Path:
    directory = project_root() / "data" / "raw"
    directory.mkdir(parents=True, exist_ok=True)
    stem = f"oecd_cpi_{START_PERIOD[:4]}_{END_PERIOD[:4]}"
    csv_path = directory / f"{stem}_raw.csv"
    csv_path.write_bytes(raw)
    metadata = {
        "source": "OECD SDMX API", "dataset": DATASET,
        "series_key": SERIES_KEY, "countries": INITIAL_OECD_COUNTRIES,
        "start_period": START_PERIOD, "end_period": END_PERIOD,
        "request_url": request_url,
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "rows": rows, "file": csv_path.name,
    }
    (directory / f"{stem}_metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return csv_path


def main() -> None:
    print("=== OECD DATA LAB | INGESTÃO ===")
    df, raw, request_url = fetch_oecd_data()
    filepath = save_raw_data(raw, request_url, len(df))
    print(f"Arquivo original: {filepath}")
    print(f"Observações por país:\n{df.groupby('REF_AREA').size()}")
    print("Períodos por país:")
    print(df.groupby("REF_AREA")["TIME_PERIOD"].agg(["min", "max"]))
    print("=== INGESTÃO FINALIZADA ===")


if __name__ == "__main__":
    main()
