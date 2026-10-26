# Auditoria do ZIP recebido — 25/10/2026

## Escopo auditado

Arquivo original `oecd-data-lab.zip` (aprox. **231 MB**, **24.630 entradas**, incluindo diretórios, com `.venv`, `.git`, IDE e caches). Foram analisados código Python, configuração, testes, dados e arquivos de interface efetivamente presentes na cópia enviada.

### Observações relevantes

1. O ZIP contém `.venv/`, `.git/`, `.idea/` e caches. **Não devem seguir para um novo repositório público**, sobretudo o histórico Git antigo que não foi auditado integralmente.
2. O `app.py` do ZIP apresenta hero, filtros, 4 métricas, abas com ícones, linha de inflação, tabela, barras e bloco de fontes. **Não inclui** as funcionalidades de destaque seletivo por país e download CSV mencionadas em versões anteriores da conversa; o pacote público preserva a interface do ZIP de fato.
3. O `app.py` referenciava somente a Gold histórica, embora `refresh_2026.py` produzisse uma `Gold latest`. A cópia preparada dá preferência à latest se ela existir, com fallback para a histórica.
4. A definição do último mês comparável foi corrigida para exigir uma taxa de inflação válida para **todos** os países selecionados naquele mês, evitando erro quando houver lacunas.
5. O teste `test_validation.py` misturava `src.oecd_data_lab` com `oecd_data_lab`; padronizado.
6. O arquivo `coveragem details.py` possuía espaço e nome inconsistente; renomeado `coverage_details.py`.
7. O `pyproject.toml` tinha descrição provisória, ponto de entrada `oecd_data_lab:main` não definido e metadados pessoais de autoria; corrigidos/retirados na cópia publicável.
8. Não havia `README.md`, `LICENSE`, `.gitignore` raiz ou CI dentro do ZIP recebido. Estes foram acrescentados.
9. Um snapshot Gold de aproximadamente 53 KB foi mantido para o app abrir no Streamlit sem consultar a API. A distribuição pública ainda está sujeita à checagem de direitos e atribuição de terceiros na fonte da OCDE.

## Verificações realizadas

- **29 testes unitários aprovados** ao executar `PYTHONPATH=src python -m pytest -q` no ambiente desta revisão.
- Sintaxe Python compilada sem erros (`compileall`).
- `uv lock --check --offline` confirmou consistência da resolução do lockfile com a configuração revisada.
- Integridade do snapshot: assinatura Parquet reconhecida; **não foi feita auditoria numérica da Gold com o backend pyarrow**, indisponível nesta sessão.
- **Não realizado:** abrir Streamlit num navegador com o runtime de produção, executar o GitHub Actions no repositório remoto ou deploy no Streamlit Cloud. Essas validações dependem da publicação e estão detalhadas no roadmap.

## Decisões aplicadas

Sem modificar textos, títulos e layout visível do usuário. Os ajustes de código no front-end são exclusivamente seleção do snapshot, cache de leitura e cálculo correto do mês comparável. Nenhuma alteração destrutiva foi feita no ZIP original enviado.
