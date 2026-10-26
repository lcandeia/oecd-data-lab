# Roadmap de publicação — OECD Inflation Explorer

## Caminho crítico: primeira publicação pública

| Gate | Trabalho | Evidência para avançar | Estado |
|---|---|---|---|
| **P0** | Usar pacote limpo, revisar licença e direitos do dataset | Git sem `.venv`, `.git` antigo ou dados indevidos | A validar |
| **P1** | Instalar do lockfile e testar localmente | `uv sync --locked` + pytest + Streamlit funcional | A executar |
| **P2** | Publicar repositório público | Código e README no GitHub; CI verde | A executar |
| **P3** | Fazer deploy no Streamlit Cloud | URL pública acessível, gráficos e filtros operacionais | A executar |
| **P4** | Finalizar apresentação do portfólio | Link, screenshot, descrição e release `v0.1.0` | A executar |

### Verificação para cada fase

**P0 — Higiene:** confirmar atribuição da OCDE e de terceiros, `LICENSE`, dados e permissões; revisar e-mail pessoal, segredos e artefatos antes do commit.

**P1 — QA:** executar suíte; conferir mês de referência, país selecionado, ausência EUA/2025-10, performance e exportação (se adicionada no futuro).

**P2 — CI:** GitHub Actions deve concluir sucesso e evitar instalação de dependências sem lockfile.

**P3 — Deploy:** configurar Python 3.13, `uv.lock`, `apps/inflation_explorer/app.py`, snapshot Gold presente; abrir app por URL anônima.

**P4 — Portfólio:** publicar uma screenshot real, explicitar fontes, 11 países, métricas de transformação e limites; liberar primeira versão.

## Backlog após o lançamento

1. Acrescentar Argentina, Peru e Uruguai com avaliação de fontes e harmonização.
2. Refinar a interface gráfica com destaques por país, rankings avançados e exportação CSV (não presentes no `app.py` do ZIP auditado).
3. Pipeline de atualização CI controlado + checks antes da promoção do snapshot `latest`.
4. Alertas de mudança metodológica, cobertura, revisão e status das séries.
5. Indicadores adicionais (desemprego, PIB, juros, produtividade) em módulos independentes.

O objetivo imediato é uma release simples, demonstrável e correta — não construir toda a automação antes de publicar.
