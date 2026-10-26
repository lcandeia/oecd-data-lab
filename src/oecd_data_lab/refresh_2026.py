"""Atualização conservadora e rastreável do CPI internacional até 2026.

- Consulta somente dois datasets SDMX já selecionados no projeto.
- Não modifica a Silver/Gold histórica: cria arquivos *_latest.parquet.
- Verifica dimensões, ano-base, duplicatas e sobreposição antes de unir dados.
- Dados revisados pela fonte oficial substituem observações sobrepostas somente
  se o ano-base continuar compatível e não houver salto anormal de nível.
- Preserva meses faltantes; não interpola.

Executar: uv run python -m oecd_data_lab.refresh_2026
"""
from __future__ import annotations

from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
import json
import os

import pandas as pd
import requests

from oecd_data_lab.international import SOURCE_BY_COUNTRY
from oecd_data_lab.international_gold import calculate_inflation_yoy

BASE = "https://sdmx.oecd.org/public/rest/data"
DATASETS = {
    "COICOP_1999": "OECD.SDD.TPS,DSD_PRICES@DF_PRICES_ALL,1.0",
    "COICOP_2018": "OECD.SDD.TPS,DSD_PRICES_COICOP2018@DF_PRICES_C2018_ALL,1.0",
}
DIMENSIONS = {
    "FREQ": "M", "METHODOLOGY": "N", "MEASURE": "CPI",
    "UNIT_MEASURE": "IX", "EXPENDITURE": "_T",
    "ADJUSTMENT": "N", "TRANSFORMATION": "_Z",
}
REQUIRED_API = set(DIMENSIONS) | {"REF_AREA", "TIME_PERIOD", "OBS_VALUE", "BASE_PER", "OBS_STATUS"}


def get_root() -> Path:
    for p in Path(__file__).resolve().parents:
        if (p / "pyproject.toml").is_file():
            return p
    raise FileNotFoundError("Não encontrei pyproject.toml")


def retrieve_source(dataset_type: str, countries: list[str], end_period: str,
                    directory: Path) -> pd.DataFrame:
    """Lê a API e registra conteúdo original e metadados de cada download."""
    dataset = DATASETS[dataset_type]
    key = f"{'+'.join(countries)}.M.N.CPI.IX._T.N._Z"
    url = f"{BASE}/{dataset}/{key}"
    params = {
        "startPeriod": "2025-01", "endPeriod": end_period,
        "dimensionAtObservation": "AllDimensions", "format": "csvfile",
    }
    print(f"Coletando {dataset_type}: {', '.join(countries)}")
    try:
        r = requests.get(url, params=params, timeout=120)
        r.raise_for_status()
    except requests.RequestException as exc:
        raise RuntimeError(f"Falha em {dataset_type}: {exc}") from exc
    if not r.content:
        raise ValueError(f"Resposta vazia de {dataset_type}")

    directory.mkdir(parents=True, exist_ok=True)
    (directory / f"{dataset_type}.csv").write_bytes(r.content)
    (directory / f"{dataset_type}_metadata.json").write_text(
        json.dumps({"dataset": dataset, "countries": countries, "url": r.url,
                    "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
                    "requested_end": end_period}, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    result = pd.read_csv(BytesIO(r.content), low_memory=False)
    if result.empty:
        print(f"AVISO: {dataset_type} retornou zero registros. Mantendo apenas o histórico local.")
        return pd.DataFrame(columns=list(REQUIRED_API))
    missing = REQUIRED_API - set(result.columns)
    if missing:
        raise ValueError(f"{dataset_type}: campos ausentes: {sorted(missing)}")
    if set(result.REF_AREA.unique()) - set(countries):
        raise ValueError(f"{dataset_type}: país não solicitado na resposta")
    for col, code in DIMENSIONS.items():
        if not result[col].eq(code).all():
            raise ValueError(f"{dataset_type}: dimensão incompatível {col}: {result[col].unique()}")
    result["period"] = pd.to_datetime(result.TIME_PERIOD, format="%Y-%m", errors="raise")
    result["cpi_index"] = pd.to_numeric(result.OBS_VALUE, errors="coerce")
    # Observações sem índice são lacunas (não as converter para CPI=0).
    unavailable = result["cpi_index"].isna()
    if unavailable.any():
        print(f"AVISO: {dataset_type} retornou {unavailable.sum()} índices ausentes (ignorados).")
        result = result.loc[~unavailable].copy()
    if (result["cpi_index"] <= 0).any():
        raise ValueError(f"{dataset_type}: índices não positivos")
    result = result.rename(columns={
        "REF_AREA": "country", "BASE_PER": "base_period",
        "OBS_STATUS": "observation_status",
    })
    result["source_dataset"] = dataset_type
    result["base_period"] = pd.to_numeric(result["base_period"], errors="raise").astype("Int64").astype(str)
    keep = ["country", "period", "cpi_index", "source_dataset", "base_period", "observation_status"]
    # Mantém as dimensões técnicas e os atributos originais na Silver atualizada.
    keep += [col for col in ["DATAFLOW", *DIMENSIONS, "UNIT_MULT", "DURABILITY", "DECIMALS"]
             if col in result.columns]
    result = result[keep]
    if result.duplicated(["country", "period"]).any():
        raise ValueError(f"{dataset_type}: país/mês duplicado no retorno")
    if (result.period > pd.Timestamp(end_period + "-01")).any():
        raise ValueError(f"{dataset_type}: observações após fim solicitado")
    return result


def merge_historical_data(history: pd.DataFrame, updates: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Une históricos sem rebase e com auditoria de eventuais revisões.

    O percentual de 5% no mesmo mês é uma salvaguarda operacional para evitar
    substituir em massa índices aparentemente rebased, não um teste estatístico.
    """
    cols = ["country", "period", "cpi_index", "source_dataset", "base_period", "observation_status"]
    old, new = history.copy(), updates.copy()
    for label, data in (("histórico", old), ("atualização", new)):
        missing = set(cols) - set(data.columns)
        if missing:
            raise ValueError(f"{label}: faltam {sorted(missing)}")
        data["period"] = pd.to_datetime(data["period"], errors="raise")
        data["cpi_index"] = pd.to_numeric(data["cpi_index"], errors="raise")
        data["base_period"] = pd.to_numeric(data["base_period"], errors="raise").astype("Int64").astype(str)
        if data.duplicated(["country", "period"]).any():
            raise ValueError(f"{label}: duplicata país/mês")
        if (data["cpi_index"] <= 0).any() or data["cpi_index"].isna().any():
            raise ValueError(f"{label}: índice inválido")
    if set(new.country) - set(old.country):
        raise ValueError("Atualização contém país não pertencente ao catálogo já validado")
    prior = old[["country", "period", "cpi_index", "base_period", "source_dataset"]]
    now = new[["country", "period", "cpi_index", "base_period", "source_dataset"]]
    overlap = prior.merge(now, on=["country", "period"], suffixes=("_old", "_new"))
    if not overlap.empty:
        if (~overlap.base_period_old.eq(overlap.base_period_new)).any():
            raise ValueError("Ano-base mudou na sobreposição. NÃO mesclar índices sem rebasing explícito.")
        if (~overlap.source_dataset_old.eq(overlap.source_dataset_new)).any():
            raise ValueError("Fonte/classificação mudou na sobreposição")
        relative = ((overlap.cpi_index_new / overlap.cpi_index_old) - 1).abs()
        if relative.gt(0.05).any():
            raise ValueError("Divergência de índice superior a 5% em meses sobrepostos. Investigar antes de mesclar.")
        revisions = overlap.loc[~overlap.cpi_index_old.eq(overlap.cpi_index_new),
                                ["country", "period", "cpi_index_old", "cpi_index_new"]].copy()
    else:
        revisions = pd.DataFrame(columns=["country", "period", "cpi_index_old", "cpi_index_new"])
    for country, group in new.groupby("country"):
        prior_bases = set(old.loc[old.country.eq(country), "base_period"])
        new_bases = set(group["base_period"])
        if len(prior_bases | new_bases) != 1:
            raise ValueError(f"{country}: mudança de ano-base detectada")
        old_source = set(old.loc[old.country.eq(country), "source_dataset"])
        if old_source != set(group["source_dataset"]):
            raise ValueError(f"{country}: mudou o dataset de origem")
    combined = pd.concat([old, new], ignore_index=True, sort=False)
    # Na mesma competência, a observação mais recente substitui a histórica.
    combined = combined.drop_duplicates(["country", "period"], keep="last")
    combined = combined.sort_values(["country", "period"]).reset_index(drop=True)
    return combined, revisions


def main():
    root = get_root()
    historical_file = root / "data/silver/oecd_cpi_international_2014_2025.parquet"
    if not historical_file.exists():
        raise FileNotFoundError(f"Silver histórica ausente: {historical_file}")
    current_utc = datetime.now(timezone.utc)
    # O script foi projetado para consultar até a competência do mês corrente.
    end_period = f"{current_utc.year}-{current_utc.month:02d}"
    if current_utc.year < 2026:
        raise ValueError("O módulo de atualização está configurado para dados de 2026 em diante")
    raw_dir = root / "data/raw/refresh_2026"
    fetched = []
    for source in DATASETS:
        countries = sorted(c for c, selected in SOURCE_BY_COUNTRY.items() if selected == source)
        if countries:
            fetched.append(retrieve_source(source, countries, end_period, raw_dir))
    newer = pd.concat(fetched, ignore_index=True)
    if not (newer.period.dt.year.eq(2026).any()):
        raise ValueError("A API não devolveu nenhuma observação de 2026. Gold original preservada.")
    old = pd.read_parquet(historical_file)
    # Garante rótulos e tipos para comparar/mesclar séries previamente curadas.
    if "base_period" in old:
        old["base_period"] = pd.to_numeric(old["base_period"], errors="raise").astype("Int64").astype(str)
    combined, revisions = merge_historical_data(old, newer)
    newest = combined.loc[combined.period.dt.year.ge(2026)]
    gold = calculate_inflation_yoy(combined)
    silver_path = root / "data/silver/oecd_cpi_international_latest.parquet"
    gold_path = root / "data/gold/oecd_inflation_international_latest.parquet"
    for path, data in [(silver_path, combined), (gold_path, gold)]:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_name(path.stem + ".pending.parquet")
        data.to_parquet(tmp, index=False)
        os.replace(tmp, path)
    revisions.to_csv(raw_dir / "revisions_overlap.csv", index=False)
    print("=== ATUALIZAÇÃO 2026 CONCLUÍDA ===")
    print(f"Observações da nova consulta em 2026: {len(newest)}")
    print(f"Revisões em períodos sobrepostos: {len(revisions)}")
    print("Competência máxima por país (dados com índice):")
    print(combined.groupby("country").period.max().dt.strftime("%Y-%m").to_string())
    print(f"Silver nova: {silver_path}\nGold nova: {gold_path}")
    print("O histórico original 2014–2025 não foi sobrescrito.")


if __name__ == "__main__":
    main()
