"""Smoke test do arquivo curado distribuído para o deploy."""
from pathlib import Path

import pandas as pd


def test_gold_snapshot_present_and_consistent():
    root = Path(__file__).resolve().parents[1]
    path = root / "data/gold/oecd_inflation_international_yoy.parquet"
    assert path.is_file(), "Snapshot necessário ao deploy está ausente"
    df = pd.read_parquet(path)
    assert {"country", "period", "cpi_index", "inflation_yoy"}.issubset(df.columns)
    assert df.country.nunique() == 11
    assert not df.duplicated(["country", "period"]).any()
    assert df["inflation_yoy"].notna().any()
