
import pandas as pd
import pytest

from oecd_data_lab.international_gold import (
    calculate_inflation_yoy,
)


def make_sample(months, values):
    return pd.DataFrame({
        "country": ["BRA"] * len(months),
        "period": pd.to_datetime(months),
        "cpi_index": values,
        "source_dataset": ["COICOP_1999"] * len(months),
        "base_period": [2015] * len(months),
    })


def test_inflation_12_months():
    months = pd.date_range(
        "2024-01-01", periods=13, freq="MS"
    )

    values = [100.0] * 12 + [110.0]

    df = make_sample(months, values)
    gold = calculate_inflation_yoy(df)

    result = gold.loc[
        gold["period"] == pd.Timestamp("2025-01-01"),
        "inflation_yoy",
    ].iloc[0]

    assert result == pytest.approx(10.0)


def test_missing_reference_month():
    months = pd.to_datetime([
        "2024-01-01",
        "2024-03-01",
        "2025-02-01",
        "2025-03-01",
    ])

    df = make_sample(
        months, [100.0, 105.0, 110.0, 115.0]
    )

    gold = calculate_inflation_yoy(df)

    feb = gold.loc[
        gold["period"] == pd.Timestamp("2025-02-01"),
        "inflation_yoy",
    ].iloc[0]

    mar = gold.loc[
        gold["period"] == pd.Timestamp("2025-03-01"),
        "inflation_yoy",
    ].iloc[0]

    assert pd.isna(feb)
    assert mar == pytest.approx(
        (115.0 / 105.0 - 1) * 100
    )
