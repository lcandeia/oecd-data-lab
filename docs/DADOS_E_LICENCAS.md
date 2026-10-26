# Dados, origem, atribuição e licenças

## Origem

A fonte principal é o **OECD Data Explorer**, acessado via API SDMX em outubro de 2026. Dois dataflows foram utilizados:

1. **COICOP 1999:** `OECD.SDD.TPS,DSD_PRICES@DF_PRICES_ALL,1.0`
2. **COICOP 2018:** `OECD.SDD.TPS,DSD_PRICES_COICOP2018@DF_PRICES_C2018_ALL,1.0`

A ferramenta original de exploração está em https://data-explorer.oecd.org/ e a documentação de termos está em https://www.oecd.org/en/about/terms-conditions.html.

**Atribuição sugerida no README e relatórios:**

> OECD (2026), *Consumer Price Indices* (COICOP 1999 e COICOP 2018), OECD Data Explorer, https://data-explorer.oecd.org/ (acessado em outubro de 2026). Cálculo da variação em 12 meses realizado pelo OECD Data Lab.

Confirme a **citação específica de cada dataset** nos metadados da fonte antes da publicação pública. Se houver DOI ou crédito específico associado à série, prefira essa atribuição oficial.

## Uso de dados

Segundo os termos da OCDE, a utilização, redistribuição e adaptação de dados são permitidas em geral, com citação apropriada; **podem existir restrições adicionais de terceiros**. O responsável pela publicação deve verificar o campo de fonte/direitos nas séries e assegurar autorização quando necessária. A licença MIT deste repositório cobre o **código original**, não reclassifica os dados como MIT.

**Ponto de verificação obrigatório antes do push público:** conferir as restrições dos dataflows/países e a adequação do snapshot `data/gold/oecd_inflation_international_yoy.parquet` para redistribuição. Se houver impedimento, remova o snapshot e ajuste a hospedagem para consumir uma fonte autorizada.

## Organização dos dados no Git

- `data/raw/`, `data/silver/`, `data/coverage/`: mantidos no ambiente de trabalho, ignorados pelo Git.
- `data/gold/oecd_inflation_international_yoy.parquet`: único snapshot curado incluído nesta entrega, necessário para a aplicação abrir no deploy.
- `data/gold/oecd_inflation_international_latest.parquet`: inicialmente ignorado; só publicar após validação e liberação de atribuição/terceiros.

Nenhum dado sintético foi inserido no snapshot. O dashboard não representa dados de 2026 se o arquivo carregado ainda terminar em 2025.

## Revisões e precisão

A atualização oficial de uma série pode alterar meses passados. Comparações devem registrar a data da extração e a referência exata. O formato Parquet é escolhido para preservar tipos e reduzir tamanho; não substitui a documentação de metodologia original.
