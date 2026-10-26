"""Contratos de qualidade para séries mensais de CPI da OCDE."""

from collections.abc import Iterable

import pandas as pd

REQUIRED_COLUMNS = {
    "REF_AREA", "FREQ", "METHODOLOGY", "MEASURE", "UNIT_MEASURE",
    "EXPENDITURE", "ADJUSTMENT", "TRANSFORMATION", "TIME_PERIOD",
    "OBS_VALUE", "BASE_PER", "OBS_STATUS",
}
EXPECTED_DIMENSIONS = {
    "FREQ": "M", "METHODOLOGY": "N", "MEASURE": "CPI",
    "UNIT_MEASURE": "IX", "EXPENDITURE": "_T",
    "ADJUSTMENT": "N", "TRANSFORMATION": "_Z",
}
DEFAULT_COUNTRIES = {"USA", "DEU"}


def validate_cpi(
    df: pd.DataFrame,
    start_period: str = "2024-01",
    end_period: str = "2024-12",
    allowed_missing: set[tuple[str, str]] | None = None,
    expected_countries: Iterable[str] | None = None,
) -> None:
    """Valida esquema, dimensões e cobertura; aceita somente lacunas autorizadas.

    Lança ValueError se algum contrato falhar. Não modifica o DataFrame.
    """
    allowed_missing = set() if allowed_missing is None else set(allowed_missing)
    expected_countries = (
        DEFAULT_COUNTRIES if expected_countries is None else set(expected_countries)
    )
    if df.empty:
        raise ValueError("O dataset está vazio.")
    missing_columns = REQUIRED_COLUMNS - set(df.columns)
    if missing_columns:
        raise ValueError(f"Colunas ausentes: {sorted(missing_columns)}")

    for column, expected in EXPECTED_DIMENSIONS.items():
        if not df[column].eq(expected).all():
            raise ValueError(
                f"Dimensão inválida: {column}. Esperado: {expected}. "
                f"Encontrado: {df[column].unique().tolist()}"
            )

    countries = set(df["REF_AREA"].dropna())
    if countries != expected_countries or df["REF_AREA"].isna().any():
        raise ValueError(
            f"Países inesperados: {sorted(countries)}; "
            f"esperados: {sorted(expected_countries)}"
        )

    if df.duplicated(["REF_AREA", "TIME_PERIOD"]).any():
        raise ValueError("Existem observações duplicadas por país e mês.")

    expected_periods = pd.period_range(start_period, end_period, freq="M")
    if expected_periods.empty:
        raise ValueError("Intervalo de datas inválido.")

    # A API usa YYYY-MM em observações mensais.
    if not df["TIME_PERIOD"].astype(str).str.fullmatch(r"\d{4}-(0[1-9]|1[0-2])").all():
        raise ValueError("TIME_PERIOD deve usar o formato mensal YYYY-MM.")

    for country, group in df.groupby("REF_AREA"):
        actual = pd.PeriodIndex(group["TIME_PERIOD"], freq="M")
        missing = expected_periods.difference(actual)
        extra = actual.difference(expected_periods)
        unexpected_missing = [
            str(month) for month in missing
            if (country, str(month)) not in allowed_missing
        ]
        if unexpected_missing or len(extra):
            raise ValueError(
                f"Cobertura inválida para {country}. "
                f"Ausências inesperadas: {unexpected_missing}. "
                f"Meses extras: {[str(p) for p in extra]}."
            )
        if len(missing):
            print(f"AVISO [{country}]: lacunas documentadas: {[str(p) for p in missing]}")

    values = pd.to_numeric(df["OBS_VALUE"], errors="coerce")
    if values.isna().any():
        raise ValueError("Existem valores de índice ausentes ou inválidos.")
    if (values <= 0).any():
        raise ValueError("O índice de preços deve ser positivo.")
    if df["BASE_PER"].isna().any():
        raise ValueError("Existem observações sem período-base.")
    # Dentro de cada país, mudanças de base precisam ser harmonizadas antes da análise.
    if df.groupby("REF_AREA")["BASE_PER"].nunique(dropna=False).gt(1).any():
        raise ValueError("Há diferentes períodos-base dentro da série de um país.")
    if df["OBS_STATUS"].isna().any():
        raise ValueError("Existem observações sem status da fonte.")

    print("Contrato de qualidade validado com sucesso!")
