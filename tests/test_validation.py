"""Testes unitários independentes da API e dos arquivos de dados."""

import pandas as pd
import pytest

from oecd_data_lab.validation import validate_cpi


@pytest.fixture
def valid_cpi_data():
    rows = []
    for country in ("USA", "DEU"):
        for month in range(1, 13):
            rows.append({
                "REF_AREA": country, "FREQ": "M", "METHODOLOGY": "N",
                "MEASURE": "CPI", "UNIT_MEASURE": "IX",
                "EXPENDITURE": "_T", "ADJUSTMENT": "N",
                "TRANSFORMATION": "_Z", "TIME_PERIOD": f"2024-{month:02d}",
                "OBS_VALUE": 120.0 + month, "BASE_PER": 2015,
                "OBS_STATUS": "A",
            })
    return pd.DataFrame(rows)


def test_valid_dataset(valid_cpi_data):
    validate_cpi(valid_cpi_data)


def test_duplicate_observation(valid_cpi_data):
    df = pd.concat([valid_cpi_data, valid_cpi_data.iloc[[0]]], ignore_index=True)
    with pytest.raises(ValueError, match="duplicadas"):
        validate_cpi(df)


def test_missing_month(valid_cpi_data):
    df = valid_cpi_data.loc[
        ~((valid_cpi_data.REF_AREA == "USA") & (valid_cpi_data.TIME_PERIOD == "2024-06"))
    ]
    with pytest.raises(ValueError, match="Cobertura inválida"):
        validate_cpi(df)


def test_invalid_indicator(valid_cpi_data):
    df = valid_cpi_data.copy()
    df.loc[0, "MEASURE"] = "INVALID"
    with pytest.raises(ValueError, match="Dimensão inválida"):
        validate_cpi(df)


def test_missing_value(valid_cpi_data):
    df = valid_cpi_data.copy()
    df.loc[0, "OBS_VALUE"] = None
    with pytest.raises(ValueError, match="ausentes ou inválidos"):
        validate_cpi(df)


def test_documented_missing_month(valid_cpi_data):
    df = valid_cpi_data.loc[
        ~((valid_cpi_data.REF_AREA == "USA") & (valid_cpi_data.TIME_PERIOD == "2024-06"))
    ]
    validate_cpi(df, allowed_missing={("USA", "2024-06")})


def test_unexpected_missing_month(valid_cpi_data):
    df = valid_cpi_data.loc[
        ~((valid_cpi_data.REF_AREA == "USA") & (valid_cpi_data.TIME_PERIOD == "2024-06"))
    ]
    with pytest.raises(ValueError, match="Cobertura inválida"):
        validate_cpi(df, allowed_missing={("USA", "2024-10")})


def test_other_expected_country(valid_cpi_data):
    df = valid_cpi_data.replace({"REF_AREA": {"DEU": "CHL"}})
    validate_cpi(df, expected_countries={"USA", "CHL"})


def test_nonpositive_index(valid_cpi_data):
    df = valid_cpi_data.copy()
    df.loc[0, "OBS_VALUE"] = 0
    with pytest.raises(ValueError, match="positivo"):
        validate_cpi(df)


def test_wrong_period_format(valid_cpi_data):
    df = valid_cpi_data.copy()
    df.loc[0, "TIME_PERIOD"] = "2024-1"
    with pytest.raises(ValueError, match="YYYY-MM"):
        validate_cpi(df)
