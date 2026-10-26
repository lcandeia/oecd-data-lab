"""Testes unitários da inflação interanual; não usam a API."""
import pandas as pd
import pytest

from oecd_data_lab.analytics import calculate_yoy


def make_data(country="USA", months=25):
    periods = pd.date_range("2023-01-01", periods=months, freq="MS")
    return pd.DataFrame({
        "country": [country] * months,
        "period": periods,
        "cpi_index": [100 + i for i in range(months)],
    })


def test_yoy_uses_exact_same_month_previous_year():
    gold = calculate_yoy(make_data())
    assert gold.loc[0:11, "inflation_yoy_pct"].isna().all()
    assert gold.loc[12, "inflation_yoy_pct"] == pytest.approx(12.0)
    assert gold.loc[24, "inflation_yoy_pct"] == pytest.approx((124 / 112 - 1) * 100)


def test_missing_prior_year_month_stays_nan():
    data = make_data()
    data = data[data.period != pd.Timestamp("2023-10-01")]
    gold = calculate_yoy(data)
    value = gold.loc[gold.period == pd.Timestamp("2024-10-01"), "inflation_yoy_pct"].iloc[0]
    assert pd.isna(value)


def test_missing_current_month_is_not_fabricated():
    data = make_data()
    data = data[data.period != pd.Timestamp("2024-10-01")]
    gold = calculate_yoy(data)
    assert not (gold.period == pd.Timestamp("2024-10-01")).any()


def test_duplicate_month_is_rejected():
    data = make_data()
    with pytest.raises(ValueError, match="duplicatas"):
        calculate_yoy(pd.concat([data, data.iloc[[0]]], ignore_index=True))


def test_nonpositive_index_is_rejected():
    data = make_data()
    data.loc[0, "cpi_index"] = 0
    with pytest.raises(ValueError, match="positivos"):
        calculate_yoy(data)


def test_countries_do_not_mix():
    usa = make_data("USA", 13)
    deu = make_data("DEU", 13)
    deu["cpi_index"] *= 2
    gold = calculate_yoy(pd.concat([usa, deu], ignore_index=True))
    rates = gold[gold.period == pd.Timestamp("2024-01-01")]
    assert len(rates) == 2
    assert rates.inflation_yoy_pct.tolist() == pytest.approx([12, 12])
