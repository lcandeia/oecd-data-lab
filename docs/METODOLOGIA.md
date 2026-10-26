# Metodologia estatística

## Indicador

A fonte inicial contém níveis do **Consumer Price Index (CPI)**, frequência mensal, total dos itens, sem ajuste sazonal, com ano-base 2015 nos registros auditados. A métrica exibida no gráfico é a variação percentual em 12 meses:

\[
\pi_{c,t} = 100 \left(\frac{I_{c,t}}{I_{c,t-12}} - 1\right)
\]

Onde `c` identifica o país, `t` o mês e `I` é o CPI original. O cálculo exige o **mesmo mês do ano anterior**, não simplesmente a décima segunda linha anterior. Índice ausente no mês atual ou de referência implica taxa indisponível.

## Composição internacional

O código `SOURCE_BY_COUNTRY` (`src/oecd_data_lab/international.py`) define uma fonte única por país:

| COICOP 1999 | COICOP 2018 |
|---|---|
| Brasil (BRA), Colômbia (COL), EUA (USA), Alemanha (DEU), Reino Unido (GBR), Canadá (CAN), Turquia (TUR) | México (MEX), Chile (CHL), Costa Rica (CRI), Japão (JPN) |

Não se juntam automaticamente segmentos das duas classificações numa mesma série. A seleção resultou de consultas de cobertura no recorte 2014–2025. Ano-base coincidente **não prova** identidade de cesta, pesos ou metodologia entre países.

## Semântica dos gráficos e KPIs

- **Inflação YoY:** taxa de inflação acumulada nos 12 meses anteriores à competência indicada.
- **Competência comum:** último mês do filtro com uma taxa válida para **todos** os países selecionados.
- **Mediana entre países:** mediana das taxas nacionais no mesmo mês, **sem pesos** por população ou PIB.
- **Maior inflação:** máximo entre os países selecionados na competência comum.
- **Diferença máximo–mínimo:** amplitude em **pontos percentuais**, não porcentagem relativa.
- **Inflação média no período:** média aritmética das **taxas interanuais mensais** no recorte, não inflação acumulada ou taxa anualizada.

As estatísticas descritivas dependem da seleção de países e datas do usuário. Rankings de países com escalas muito distintas demandam leitura cuidadosa e não são indicadores de desempenho de política econômica por si sós.

## Ausências e revisões

Nos registros históricos do projeto, `USA / 2025-10` está ausente da série CPI selecionada. O pipeline não interpola a observação. Isso pode impossibilitar a taxa para o mesmo mês do ano seguinte, mesmo quando o índice corrente existir. Revisões oficiais posteriores podem mudar resultados do snapshot, por isso a data de extração é parte da proveniência.

## Limites da análise

Não se infere causalidade, convergência estrutural ou equivalência de políticas com o gráfico. Mudanças de classificação COICOP, metodologia nacional, composição do índice e status da observação devem ser revisitados antes de análises formais mais avançadas.
