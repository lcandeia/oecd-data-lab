import pandas as pd
import pytest

from oecd_data_lab.dashboard_metrics import (
    latest_common_snapshot, missing_index_report, snapshot_metrics,
    standardize_gold, yearly_median_rates,
)


def sample():
    return pd.DataFrame({
        "country": ["BRA", "BRA", "BRA", "USA", "USA"],
        "period": pd.to_datetime(["2025-09-01", "2025-10-01", "2025-11-01",
                                  "2025-09-01", "2025-11-01"]),
        "cpi_index": [100., 101., 102., 105., 107.],
        "inflation_yoy": [4., 4.2, 4.1, 2.5, 2.3],
        "source_dataset": ["1999"] * 5,
        "base_period": [2015] * 5,
    })


def test_snapshot_uses_same_month():
    period, snapshot = latest_common_snapshot(sample(), ["BRA", "USA"])
    assert period == pd.Timestamp("2025-11-01")
    assert set(snapshot.country) == {"BRA", "USA"}


def test_snapshot_handles_no_common_month():
    _, snapshot = latest_common_snapshot(sample(), ["BRA", "USA"],
                                       start=pd.Timestamp("2025-10-01"),
                                       end=pd.Timestamp("2025-10-01"))
    assert snapshot.empty


def test_metrics_median_spread():
    _, snap = latest_common_snapshot(sample(), ["BRA", "USA"])
    metrics = snapshot_metrics(snap)
    assert metrics["median"] == pytest.approx(3.2)
    assert metrics["spread"] == pytest.approx(1.8)
    assert metrics["top"] == "BRA"


def test_reports_missing_index_oct_2025():
    report = missing_index_report(sample(), ["USA"], pd.Timestamp("2025-09-01"),
                                  pd.Timestamp("2025-11-01"))
    assert report.loc[0, "meses_sem_indice"] == 1
    assert report.loc[0, "lacunas_indice"] == "2025-10"


def test_reject_duplicate_country_month():
    df = pd.concat([sample(), sample().iloc[[0]]], ignore_index=True)
    with pytest.raises(ValueError, match="duplicatas"):
        standardize_gold(df)


def test_accept_legacy_column_name():
    df = standardize_gold(sample().rename(columns={"inflation_yoy": "inflation_yoy_pct"}))
    assert "inflation_yoy" in df


def test_yearly_stat_is_median_not_yearly_inflation():
    report = yearly_median_rates(sample())
    bra = report[report.country.eq("BRA")].iloc[0]
    assert bra.mediana_taxas_mensais == pytest.approx(4.1)
    assert bra.meses == 3
