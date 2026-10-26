# OECD Inflation Explorer

**Laboratório de dados econômicos · Python + Streamlit + OCDE**

Aplicação de comparação internacional da inflação medida pelo **CPI (Consumer Price Index / Índice de Preços ao Consumidor)**. A implementação combina coleta por API SDMX, contratos de qualidade, tratamento tabular, cálculos de inflação em 12 meses e visualização interativa. Projeto independente, **não oficial nem afiliado à OCDE**.

> **Dados exibidos:** um snapshot curado da OCDE com séries mensais de 11 países. A competência máxima é determinada pelos dados efetivamente publicados no arquivo. A atualização é executada separadamente da aplicação.

## O que a aplicação oferece

- Filtros por países e período;
- Trajetórias mensais da inflação em 12 meses;
- Competência comum para comparar países no mesmo mês;
- Mediana, maior taxa e amplitude em pontos percentuais;
- Ranking e médias exploratórias para o recorte selecionado;
- Informações sobre fonte, metodologia e cobertura.

**Atenção:** médias das taxas interanuais mensais **não** são a inflação acumulada no período. A comparação não constitui inferência causal.

## Visão da arquitetura

```text
OECD API SDMX (COICOP 1999 / 2018)
          │
       CSV bruto  → Bronze (local)
          │
    validação e padronização
          │
       Parquet    → Silver (local)
          │
       CPI(t)/CPI(t-12)-1
          │
       Parquet    → Gold (snapshot publicável)
          │
        Streamlit + Plotly
```

O processamento usa **correspondência exata de mês**, não a posição de linhas, para preservar a integridade do cálculo na presença de lacunas temporais.

## Dados atuais

- **Países (11):** Brasil, Canadá, Chile, Colômbia, Costa Rica, Alemanha, Reino Unido, Japão, México, Turquia e Estados Unidos.
- **CPI de origem:** 1.583 observações mensais entre janeiro/2014 e dezembro/2025.
- **Inflação em 12 meses:** 1.451 taxas calculáveis no mesmo recorte.
- **Lacuna documentada:** CPI geral dos EUA em outubro/2025.
- **Países futuros no catálogo:** Argentina, Peru e Uruguai, ainda sem série integrada nessa versão.

O arquivo publicável incluído neste pacote é `data/gold/oecd_inflation_international_yoy.parquet` (snapshot histórico). Os números acima descrevem este snapshot, não dados em tempo real.

## Executar localmente

**Requisitos:** Python **3.13**, Git e [uv](https://docs.astral.sh/uv/).

```powershell
uv sync --locked
uv run python -m pytest -q
uv run streamlit run apps/inflation_explorer/app.py
```

No Windows, se `uv` não estiver no `PATH` mas estiver no ambiente Python, pode executar os comandos correspondentes usando `python -m uv`.

O painel abre normalmente em `http://localhost:8501`. Para executar a aplicação, não é necessário baixar o histórico bruto: o Parquet Gold curado está incluído.

## Atualizações e reprodutibilidade

- O módulo `src/oecd_data_lab/refresh_2026.py` consulta novas observações e gera `data/gold/oecd_inflation_international_latest.parquet`, sem substituir o arquivo histórico.
- A aplicação **prioriza o snapshot `latest` quando ele está presente**, ou usa o histórico como fallback.
- Para atualizar a versão publicada, valide o novo snapshot, verifique direitos de redistribuição e inclua deliberadamente o novo arquivo no repositório/deploy. O Cloud não recebe arquivos novos criados apenas no computador local.
- O pipeline completo de reconstrução histórica depende das respostas brutas da OCDE, omitidas deste repositório público; veja [`docs/REPRODUCAO.md`](docs/REPRODUCAO.md).

## Qualidade e limitações

A suíte de testes verifica contratos da série, rejeição de duplicatas, lacunas autorizadas, cálculo YoY, medição de competência comum e procedimentos de atualização. Os testes não substituem uma auditoria completa de comparabilidade metodológica. Veja [`docs/METODOLOGIA.md`](docs/METODOLOGIA.md) e [`docs/QUALIDADE.md`](docs/QUALIDADE.md).

## Deploy

A aplicação é destinada ao **Streamlit Community Cloud** com:

- repositório GitHub público;
- entrada: `apps/inflation_explorer/app.py`;
- Python **3.13**;
- dependências via `uv.lock` e `pyproject.toml`;
- snapshot Gold versionado em `data/gold/`.

Tutorial completo: [`docs/DEPLOY_GITHUB.md`](docs/DEPLOY_GITHUB.md). Roadmap: [`docs/ROADMAP.md`](docs/ROADMAP.md).

## Fontes e créditos

**Fonte:** OECD Data Explorer, conjuntos *Consumer Price Indices* (COICOP 1999 e 2018). Dados obtidos da API SDMX em outubro de 2026. As taxas de inflação YoY são transformação própria a partir dos índices. Consulte [`docs/DADOS_E_LICENCAS.md`](docs/DADOS_E_LICENCAS.md) para identificadores dos datasets, atribuição e cautelas sobre conteúdo de terceiros.

**Licença:** MIT para o código original do projeto. **A licença não altera os direitos relativos aos dados da OCDE ou de terceiros.** Antes da divulgação, revise titularidade e atribuição de cada série.

## Próximos incrementos

- Países adicionais na América Latina;
- séries harmonizadas e cobertura de 2026 validada;
- indicadores econômicos adicionais;
- aprimoramentos de comparabilidade, documentação e monitoramento do pipeline.

> Este é um projeto independente de educação e portfólio; não representa análise oficial da OCDE e não utiliza sua logomarca.
