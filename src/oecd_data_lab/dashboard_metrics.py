"""Funções puras para indicadores e qualidade do OECD Inflation Explorer.

Este módulo não importa Streamlit; assim pode ser testado sem iniciar a interface.
"""
from __future__ import annotations

import pandas as pd

REQUIRED = {"country", "period", "inflation_yoy", "cpi_index"}


def standardize_gold(frame: pd.DataFrame) -> pd.DataFrame:
    """Normaliza o contrato da Gold e recusa duplicatas ou dados inválidos."""
    df = frame.copy()
    if "inflation_yoy" not in df and "inflation_yoy_pct" in df:
        df = df.rename(columns={"inflation_yoy_pct": "inflation_yoy"})
    missing = REQUIRED - set(df.columns)
    if missing:
        raise ValueError(f"Colunas obrigatórias ausentes na Gold: {sorted(missing)}")
    if df.empty:
        raise ValueError("Gold vazia")
    df["period"] = pd.to_datetime(df["period"], errors="raise")
    if df["period"].isna().any() or not df["period"].dt.is_month_start.all():
        raise ValueError("A competência deve ser o primeiro dia de cada mês")
    df["cpi_index"] = pd.to_numeric(df["cpi_index"], errors="coerce")
    df["inflation_yoy"] = pd.to_numeric(df["inflation_yoy"], errors="coerce")
    if df["country"].isna().any() or df["cpi_index"].isna().any():
        raise ValueError("País ou índice CPI ausente")
    if (df["cpi_index"] <= 0).any():
        raise ValueError("Índice CPI não positivo")
    if df.duplicated(["country", "period"]).any():
        raise ValueError("Gold contém duplicatas de país e mês")
    return df.sort_values(["country", "period"]).reset_index(drop=True)


def latest_common_snapshot(frame: pd.DataFrame, countries: list[str],
                           start: pd.Timestamp | None = None,
                           end: pd.Timestamp | None = None) -> tuple[pd.Timestamp | None, pd.DataFrame]:
    """Localiza a última competência com inflação observada para TODOS os países."""
    if not countries:
        return None, frame.iloc[0:0].copy()
    part = frame.loc[frame["country"].isin(countries) & frame["inflation_yoy"].notna()].copy()
    if start is not None:
        part = part[part["period"] >= pd.Timestamp(start)]
    if end is not None:
        part = part[part["period"] <= pd.Timestamp(end)]
    counts = part.groupby("period")["country"].nunique()
    valid = counts[counts.eq(len(set(countries)))].index
    if valid.empty:
        return None, part.iloc[0:0].copy()
    period = valid.max()
    snap = part[part["period"].eq(period)].copy()
    return pd.Timestamp(period), snap.sort_values("inflation_yoy", ascending=False)


def snapshot_metrics(snapshot: pd.DataFrame) -> dict:
    """Métricas de corte transversal: NUNCA mistura competências."""
    if snapshot.empty:
        return {"n": 0, "median": None, "spread": None, "top": None,
                "bottom": None, "top_value": None, "bottom_value": None}
    ordered = snapshot.sort_values("inflation_yoy", ascending=False)
    return {
        "n": len(ordered),
        "median": float(ordered["inflation_yoy"].median()),
        "spread": float(ordered["inflation_yoy"].max() - ordered["inflation_yoy"].min()),
        "top": str(ordered.iloc[0]["country"]),
        "bottom": str(ordered.iloc[-1]["country"]),
        "top_value": float(ordered.iloc[0]["inflation_yoy"]),
        "bottom_value": float(ordered.iloc[-1]["inflation_yoy"]),
    }


def missing_index_report(frame: pd.DataFrame, countries: list[str],
                         start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    """Distingue ausência de CPI de inflação YoY indisponível."""
    months = pd.date_range(pd.Timestamp(start), pd.Timestamp(end), freq="MS")
    results = []
    for country in countries:
        part = frame[frame["country"].eq(country)].set_index("period").reindex(months)
        absent_cpi = part["cpi_index"].isna()
        missing_rate = part["inflation_yoy"].isna()
        gaps = list(months[absent_cpi].strftime("%Y-%m"))
        original = frame[frame["country"].eq(country)]
        results.append({
            "country": country,
            "meses_esperados": len(months),
            "meses_com_indice": int((~absent_cpi).sum()),
            "meses_sem_indice": int(absent_cpi.sum()),
            "taxas_disponiveis": int((~missing_rate).sum()),
            "taxas_indisponiveis": int(missing_rate.sum()),
            "lacunas_indice": ", ".join(gaps) if gaps else "—",
            "source_dataset": (str(original["source_dataset"].dropna().iloc[0])
                               if "source_dataset" in original and original["source_dataset"].notna().any()
                               else "não informado"),
            "base_period": (str(original["base_period"].dropna().iloc[0])
                            if "base_period" in original and original["base_period"].notna().any()
                            else "não informado"),
        })
    return pd.DataFrame(results)


def yearly_median_rates(frame: pd.DataFrame) -> pd.DataFrame:
    """Resumo exploratório por ano: mediana das taxas mensais de 12 meses."""
    good = frame.dropna(subset=["inflation_yoy"]).copy()
    good["year"] = good["period"].dt.year
    return (good.groupby(["country", "year"], as_index=False)
            .agg(mediana_taxas_mensais=("inflation_yoy", "median"),
                 meses=("inflation_yoy", "size")))
