# Qualidade, testes e verificações de aceite

## Cobertura dos testes

O projeto contém testes unitários para validação CPI, detecção de duplicatas, meses ausentes, cálculo YoY por mês exato, resumo estatístico de dashboard e mesclagem de atualizações históricas. São **29 testes** no ZIP auditado, aprovados em ambiente local com as dependências necessárias à parte testada (`PYTHONPATH=src python -m pytest -q`).

A execução efetiva com o lockfile e Python 3.13 no GitHub Actions **ainda deverá ser confirmada** após o primeiro push. Não afirmar CI verde antes da execução pública.

## Executar

```powershell
uv sync --locked
uv run python -m pytest -q
uv run python -m compileall -q src apps tests
uv run streamlit run apps/inflation_explorer/app.py
```

## Pré-publicação

- [ ] Testes passam no ambiente recém-criado a partir de `uv.lock`.
- [ ] A aplicação inicia usando apenas o snapshot curado versionado.
- [ ] A seleção por país e período funciona sem erro.
- [ ] KPI e ranking comparam a mesma competência para todos os países selecionados.
- [ ] Período exibido não extrapola o arquivo realmente publicado.
- [ ] Referência da OCDE, metodologia, lacunas e licença estão corretas.
- [ ] Nenhum segredo, e-mail pessoal indesejado, dados locais ou `.venv` foi incluído.
- [ ] O repositório público usa histórico Git novo/limpo (sem objetos antigos inadvertidos).
- [ ] Workflow `.github/workflows/ci.yml` ficou verde no GitHub.
- [ ] Deploy abre por URL pública e funciona em janela anônima.

## Riscos conhecidos

O novo pacote não executou uma sessão de navegador Streamlit na infraestrutura da hospedagem. O snapshot foi copiado do arquivo ZIP enviado, e sua correspondência científica com a fonte depende da auditoria de proveniência e direitos descrita em `DADOS_E_LICENCAS.md`.
