from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

# ============================================================
# CONFIGURAÇÃO
# ============================================================

st.set_page_config(
    page_title="OECD Inflation Explorer",
    page_icon="📊",
    layout="wide",
)

ROOT = Path(__file__).resolve().parents[2]

# O backend pode publicar um snapshot mais recente sem alterar o front-end.
GOLD_HISTORICAL = ROOT / "data" / "gold" / "oecd_inflation_international_yoy.parquet"
GOLD_LATEST = ROOT / "data" / "gold" / "oecd_inflation_international_latest.parquet"
GOLD_FILE = GOLD_LATEST if GOLD_LATEST.is_file() else GOLD_HISTORICAL

COUNTRY_NAMES = {
    "BRA": "Brasil",
    "CAN": "Canadá",
    "CHL": "Chile",
    "COL": "Colômbia",
    "CRI": "Costa Rica",
    "DEU": "Alemanha",
    "GBR": "Reino Unido",
    "JPN": "Japão",
    "MEX": "México",
    "TUR": "Turquia",
    "USA": "Estados Unidos",
}

# ============================================================
# ESTILO
# ============================================================

st.markdown(
    """
    <style>
        /* Espaçamento geral da página */
        .block-container {
            padding-top: 2.8rem !important;
            padding-bottom: 2rem !important;
            max-width: 1380px;
        }

        /* Hero / Header */
        .hero-card {
            background: linear-gradient(135deg, #163a63 0%, #1f5b87 100%);
            border-radius: 24px;
            padding: 1.15rem 2rem 1.6rem 2rem;
            margin-top: 0.45rem;
            margin-bottom: 1.15rem;
            color: white;
            box-shadow: 0 10px 28px rgba(13, 38, 76, 0.18);
        }

        .hero-kicker {
            font-size: 0.78rem;
            font-weight: 700;
            letter-spacing: 0.18em;
            text-transform: uppercase;
            opacity: 0.9;
            margin-bottom: 0.65rem;
        }

        .hero-title {
            font-size: 2.45rem;
            font-weight: 800;
            line-height: 1.05;
            margin-bottom: 0.55rem;
        }

        .hero-subtitle {
            font-size: 1.02rem;
            line-height: 1.7;
            max-width: 950px;
            opacity: 0.97;
        }

        .context-line {
            margin-top: 0.95rem;
            margin-bottom: 1.1rem;
            color: #6b7b93;
            font-size: 0.98rem;
        }

        /* Título de seção */
        .section-kicker {
            color: #28527a;
            font-size: 0.88rem;
            font-weight: 800;
            letter-spacing: 0.16em;
            text-transform: uppercase;
            margin-top: 0.6rem;
            margin-bottom: 0.55rem;
        }

        .section-title {
            color: #12345b;
            font-size: 1.95rem;
            font-weight: 800;
            line-height: 1.2;
            margin-bottom: 1rem;
        }

        /* Callout principal */
        .insight-box {
            background: #edf4fb;
            border-left: 5px solid #3f88c5;
            padding: 1rem 1.15rem;
            border-radius: 12px;
            color: #14395b;
            font-size: 1.02rem;
            line-height: 1.65;
            margin-bottom: 1rem;
        }

        /* KPI cards */
        .metric-card {
            background: #ffffff;
            border: 1px solid rgba(21, 61, 99, 0.08);
            border-radius: 18px;
            padding: 1rem 1.15rem 1rem 1.15rem;
            box-shadow: 0 8px 22px rgba(16, 42, 67, 0.06);
            min-height: 142px;
        }

        .metric-label {
            color: #5e738c;
            font-size: 0.92rem;
            font-weight: 600;
            margin-bottom: 0.45rem;
        }

        .metric-value {
            color: #103b66;
            font-size: 2.1rem;
            font-weight: 800;
            line-height: 1.05;
            margin-bottom: 0.35rem;
        }

        .metric-footnote {
            color: #7f90a4;
            font-size: 0.86rem;
            line-height: 1.45;
        }

        /* Tabs mais elegantes */
        div[data-testid="stTabs"] {
            margin-top: 1.35rem;
        }

        div[data-testid="stTabs"] > div:first-child {
            border-bottom: none !important;
        }

        button[data-baseweb="tab"] {
            background: #eef3f8 !important;
            border-radius: 14px !important;
            border: 1px solid #dce6f2 !important;
            color: #35506b !important;
            font-weight: 700 !important;
            padding: 0.6rem 1rem !important;
            margin-right: 0.5rem !important;
            transition: all 0.18s ease-in-out !important;
        }

        button[data-baseweb="tab"]:hover {
            background: #e5eef8 !important;
            color: #163a63 !important;
            border-color: #c8d8ea !important;
        }

        button[aria-selected="true"][data-baseweb="tab"] {
            background: linear-gradient(135deg, #163a63 0%, #235d89 100%) !important;
            color: white !important;
            border-color: transparent !important;
            box-shadow: 0 6px 18px rgba(21, 58, 98, 0.20) !important;
        }

        /* Separador mais leve */
        hr {
            border-color: rgba(16, 59, 102, 0.08);
        }

    </style>
    """,
    unsafe_allow_html=True,
)

# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

@st.cache_data
def load_data(file_path: str, modified_ns: int):
    # Parâmetros identificam a versão do snapshot para o cache do Streamlit.
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Arquivo Gold não encontrado: {path}")

    df = pd.read_parquet(path)
    df["period"] = pd.to_datetime(df["period"])
    df["country_name"] = df["country"].map(COUNTRY_NAMES).fillna(df["country"])
    return df


def metric_card(label: str, value: str, footnote: str):
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-footnote">{footnote}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# DADOS
# ============================================================

if not GOLD_FILE.exists():
    st.error(f"Snapshot Gold não encontrado: {GOLD_FILE}")
    st.stop()
df = load_data(str(GOLD_FILE), GOLD_FILE.stat().st_mtime_ns)
valid_data = df.dropna(subset=["inflation_yoy"]).copy()

# ============================================================
# HERO
# ============================================================

st.markdown(
    """
    <div class="hero-card">
        <div class="hero-kicker">OECD DATA LAB &nbsp;&nbsp</div>
        <div class="hero-title">Inflação - CPI </div>
        <div class="hero-subtitle">
            Consumer Price Index / Índice de Preços ao Consumidor.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ============================================================
# FILTROS
# ============================================================

st.sidebar.header("Filtros")

countries = sorted(valid_data["country"].unique())

selected_countries = st.sidebar.multiselect(
    "Selecione os países",
    options=countries,
    default=["BRA", "USA", "DEU", "CHL", "COL"],
    format_func=lambda x: COUNTRY_NAMES.get(x, x),
)

min_date = valid_data["period"].min().date()
max_date = valid_data["period"].max().date()

start_date, end_date = st.sidebar.slider(
    "Período",
    min_value=min_date,
    max_value=max_date,
    value=(pd.to_datetime("2019-01-01").date(), max_date),
    format="MM/YYYY",
)

filtered = valid_data[
    valid_data["country"].isin(selected_countries)
    & (valid_data["period"].dt.date >= start_date)
    & (valid_data["period"].dt.date <= end_date)
].copy()

if not selected_countries or filtered.empty:
    st.warning("Selecione países e um período com dados disponíveis.")
    st.stop()

# ============================================================
# RETRATO ATUAL
# ============================================================

# Último mês em que TODOS os países selecionados têm taxa calculável.
# Um mínimo de máximos não garante interseção quando há lacunas intermediárias.
counts_by_period = filtered.groupby("period")["country"].nunique()
common_periods = counts_by_period[counts_by_period.eq(len(selected_countries))].index
if common_periods.empty:
    st.warning("Não foi possível identificar uma competência comum entre os países selecionados.")
    st.stop()
latest_common_period = common_periods.max()

latest_comparable = (
    filtered[filtered["period"] == latest_common_period]
    .sort_values("inflation_yoy", ascending=False)
    .copy()
)

if latest_comparable.empty:
    st.warning("Não foi possível identificar uma competência comum entre os países selecionados.")
    st.stop()

leader = latest_comparable.iloc[0]
trailer = latest_comparable.iloc[-1]
median_inflation = latest_comparable["inflation_yoy"].median()
spread = latest_comparable["inflation_yoy"].max() - latest_comparable["inflation_yoy"].min()

st.markdown(
    """
    <div class="section-kicker"> Cenário Atual</div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    f"""
    <div class="insight-box">
        Em <strong>{latest_common_period.strftime('%b/%Y').lower()}</strong>,
        <strong>{leader['country_name']}</strong> registrou
        <strong>{leader['inflation_yoy']:.2f}%</strong> de inflação interanual —
        <strong>{spread:.2f} p.p.</strong> acima de <strong>{trailer['country_name']}</strong>.
    </div>
    """,
    unsafe_allow_html=True,
)


c1, c2, c3, c4 = st.columns(4)

with c1:
    metric_card(
        "Competência comum",
        latest_common_period.strftime("%b/%Y").lower(),
        "Mês mais recente disponível",
    )

with c2:
    metric_card(
        "Mediana entre países",
        f"{median_inflation:.2f}%",
        "Valor central da distribuição no último mês",
    )

with c3:
    metric_card(
        "Maior inflação",
        f"{leader['inflation_yoy']:.2f}%",
        f"{leader['country_name']} lidera o grupo selecionado",
    )

with c4:
    metric_card(
        "Diferença máximo–mínimo",
        f"{spread:.2f} p.p.",
        "Amplitude das taxas do conjunto",
    )



# ============================================================
# TABS
# ============================================================

tab1, tab2, tab3 = st.tabs(
    ["📈 Trajetórias", "📊 Comparações", "🛡️ Fontes e qualidade",]
)

with tab1:
    st.subheader("Evolução da inflação interanual")

    fig = px.line(
        filtered,
        x="period",
        y="inflation_yoy",
        color="country_name",
        labels={
            "period": "Período",
            "inflation_yoy": "Inflação em 12 meses (%)",
            "country_name": "País",
        },
    )

    fig.update_layout(
        hovermode="x unified",
        legend_title_text="País",
        margin=dict(l=10, r=10, t=30, b=10),
    )

    st.plotly_chart(fig, width="stretch")

with tab2:
    st.subheader("Última taxa disponível por país")

    ranking = latest_comparable[
        ["country_name", "period", "inflation_yoy"]
    ].rename(
        columns={
            "country_name": "País",
            "period": "Competência",
            "inflation_yoy": "Inflação (%)",
        }
    )

    st.dataframe(
        ranking,
        width="stretch",
        hide_index=True,
    )

    avg_by_country = (
        filtered.groupby("country_name", as_index=False)["inflation_yoy"]
        .mean()
        .sort_values("inflation_yoy", ascending=False)
    )

    fig_bar = px.bar(
        avg_by_country,
        x="inflation_yoy",
        y="country_name",
        orientation="h",
        labels={
            "inflation_yoy": "Inflação média no período (%)",
            "country_name": "País",
        },
    )

    fig_bar.update_layout(
        yaxis={"categoryorder": "total ascending"},
        margin=dict(l=10, r=10, t=20, b=10),
    )

    st.plotly_chart(fig_bar, width="stretch")

with tab3:
    st.subheader("Fontes, método e qualidade")

    st.markdown(
        """
        - **Fonte principal:** OECD Data Explorer  
        - **Indicador:** CPI (Consumer Price Index), inflação acumulada em 12 meses  
        - **Cobertura atual:** 11 países  
        - **Frequência:** mensal  
        - **Ano-base do índice:** 2015  
        - **Lógica de cálculo:** comparação do índice do mês atual com o índice do mesmo mês do ano anterior  
        - **Lacunas:** valores ausentes não são interpolados  
        """
    )

    quality = (
        filtered.groupby("country_name")
        .agg(
            primeira_competencia=("period", "min"),
            ultima_competencia=("period", "max"),
            observacoes=("inflation_yoy", "count"),
        )
        .reset_index()
        .rename(columns={"country_name": "País"})
    )

    st.dataframe(quality, width="stretch", hide_index=True)