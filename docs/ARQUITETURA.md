# Arquitetura e inventário do repositório

## Estrutura publicável

```text
apps/inflation_explorer/app.py     Interface Streamlit, filtros, métricas e gráficos
data/gold/oecd_inflation_international_yoy.parquet  Snapshot curado para o deploy
src/oecd_data_lab/config.py        Países desejados e janela histórica
src/oecd_data_lab/ingestion.py     Ingestão inicial COICOP 1999 (EUA/Alemanha)
src/oecd_data_lab/coverage.py      Verificação de cobertura 1999
src/oecd_data_lab/coverage_2018.py Verificação de cobertura 2018
src/oecd_data_lab/coverage_details.py Detalhamento de lacunas
src/oecd_data_lab/validation.py    Regras de qualidade
src/oecd_data_lab/processing.py    Bronze → Silver para o lote inicial
src/oecd_data_lab/international.py Consolidação Silver de 11 países
src/oecd_data_lab/international_gold.py Silver → Gold internacional
src/oecd_data_lab/dashboard_metrics.py Indicadores puros/testáveis
src/oecd_data_lab/refresh_2026.py Atualização incremental (separada)
tests/                             Testes unitários sem chamada à API
.github/workflows/ci.yml           CI com uv e Python 3.13
.streamlit/config.toml             Tema de interface
```

## Separação de responsabilidades

1. **Fonte:** dados em formato SDMX-CSV disponibilizados pela OCDE. O relatório de cobertura já foi utilizado para selecionar uma classificação por país.
2. **Bronze:** arquivos originais e metadados com URL/data da coleta; guardados localmente e **não** incluídos no repositório público.
3. **Silver:** padronização com proveniência, deduplicação por país/competência e verificações de cobertura/ano-base; guardada localmente.
4. **Gold:** cálculo da inflação interanual (por chave país+período) e exportação Parquet. O snapshot aprovado é pequeno e suficiente para execução offline do dashboard.
5. **Interface:** lê a Gold local; não dispara chamadas à API ao selecionar filtros.

## Contrato Gold consumido pelo dashboard

Os campos principais são `country` (código), `period` (primeiro dia do mês), `cpi_index` (índice CPI positivo) e `inflation_yoy` (taxa em % ou nulo se não calculável). O pipeline internacional preserva, ainda, `source_dataset`, `base_period` e `observation_status`.

## Atualização de 2026

`refresh_2026` mantém o histórico original, compara sobreposição e ano-base, registra revisões e gera snapshots Silver/Gold com sufixo `_latest`. O módulo deve ser executado **fora do serviço Streamlit**, em ambiente controlado; sua atualização não é programada automaticamente neste pacote.

### Regra de seleção no frontend

Se `data/gold/oecd_inflation_international_latest.parquet` estiver presente no servidor, ele tem prioridade. Caso contrário, usa o snapshot histórico. A presença de um arquivo local no PyCharm **não atualiza** o servidor na nuvem: o snapshot precisa ser enviado em commit ou por pipeline de distribuição explicitamente configurado.


