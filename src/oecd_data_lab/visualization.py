"""Exporta gráfico interativo da inflação em 12 meses para HTML."""
import pandas as pd
import plotly.express as px

from oecd_data_lab.analytics import build_gold
from oecd_data_lab.config import START_PERIOD, END_PERIOD
from oecd_data_lab.ingestion import project_root


def main() -> None:
    stem = f"oecd_cpi_{START_PERIOD[:4]}_{END_PERIOD[:4]}"
    gold_path = project_root() / "data" / "gold" / f"{stem}_yoy.parquet"
    if not gold_path.is_file():
        gold_path = build_gold()
    gold = pd.read_parquet(gold_path)
    valid = gold.dropna(subset=["inflation_yoy_pct"]).copy()
    if valid.empty:
        raise ValueError("Nenhuma taxa YoY calculada; verifique o histórico.")
    fig = px.line(
        valid,
        x="period", y="inflation_yoy_pct", color="country",
        title="Inflação acumulada em 12 meses — OCDE",
        labels={"period": "Mês", "inflation_yoy_pct": "Inflação em 12 meses (%)", "country": "País"},
    )
    fig.update_layout(template="plotly_white", hovermode="x unified")
    output = project_root() / "reports" / "inflation_yoy_comparison.html"
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.write_html(output, include_plotlyjs=True)
    print(f"Gráfico exportado: {output}")


if __name__ == "__main__":
    main()
