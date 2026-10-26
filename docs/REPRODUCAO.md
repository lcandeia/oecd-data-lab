# Reprodutibilidade e atualização

## Dois modos de uso

**Modo de apresentação (rápido):** roda diretamente com o snapshot versionado em `data/gold/oecd_inflation_international_yoy.parquet`. Não exige acesso à API.

**Modo de pesquisa (pipeline):** consulta a API SDMX e cria `data/raw/`, `data/coverage/`, `data/silver/` e `data/gold/`. O histórico bruto **não** é distribuído neste repositório por padrão.

## Consultas exploratórias e base histórica

Com `uv sync --locked` executado e internet disponível, os módulos de diagnóstico podem ser executados via `uv run python -m oecd_data_lab.coverage` e `uv run python -m oecd_data_lab.coverage_2018`.

A consolidação internacional por `uv run python -m oecd_data_lab.international` **exige os CSVs de cobertura** `data/coverage/coverage_response.csv` e `data/coverage/coverage_2018_response.csv`, que são gerados pelas consultas de cobertura. Para criar a Gold internacional, use `uv run python -m oecd_data_lab.international_gold`.

A ingestão `oecd_data_lab.ingestion` e o processamento `oecd_data_lab.processing` trabalham com o lote inicial EUA+Alemanha e não substituem o fluxo internacional.

## Atualizar a partir de 2026

```powershell
uv run python -m oecd_data_lab.refresh_2026
```

O atualizador espera a Silver histórica `data/silver/oecd_cpi_international_2014_2025.parquet`. Caso não exista, gere-a primeiro com o pipeline internacional. A atualização consulta as fontes, avalia sobreposição e ano-base e grava `data/silver/oecd_cpi_international_latest.parquet` e `data/gold/oecd_inflation_international_latest.parquet`.

**Não publique o novo snapshot automaticamente:** confira cobertura, status, base, anomalias e condições de distribuição. Em seguida, versiona-se o snapshot aprovado (ou publica-se em artefato externo confiável) para que o Cloud enxergue a atualização. O front-end prioriza o `latest` quando presente.

## Checklist de atualização manual

1. Rodar o atualizador em ambiente local/CI controlado, com cache e respeito aos limites da API.
2. Conferir o relatório de revisões e as competências disponíveis por país.
3. Executar pytest e validações de schema/coverage na Gold recém-produzida.
4. Fazer revisão dos direitos de terceiros e da atribuição da fonte.
5. Distribuir snapshot aprovado e verificar novo mês no painel público.

A automação agendada de coleta, aprovação e publicação **não faz parte desta primeira release**.
