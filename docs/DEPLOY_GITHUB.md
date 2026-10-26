# Publicar GitHub + Streamlit Community Cloud

## Passo 0 — Começar do diretório limpo

Use a pasta **`oecd-data-lab_publicacao/`** deste pacote, que não contém `.git`, `.venv`, `.idea`, caches ou dados brutos. **Não publique o ZIP original de 231 MB** e não copie o `.git` antigo. Crie um repositório Git novo a partir da pasta limpa para não carregar histórico de arquivos privados/grandes.

Confira a licença MIT e os direitos de redistribuição do snapshot Gold antes de seguir. Caso deseje outra licença para o código, altere `LICENSE` antes do primeiro commit.

## Passo 1 — Verificação local (PowerShell, PyCharm)

```powershell
uv sync --locked
uv run python -m pytest -q
uv run streamlit run apps/inflation_explorer/app.py
```

O Streamlit deve abrir com os 11 países e dados até a competência existente no arquivo. Teste filtro, ranking, abas, atualização da página e modo incógnito no deploy posterior.

## Passo 2 — Criar repositório no GitHub

No GitHub, crie um repositório **público** chamado `oecd-data-lab`. Se usar os comandos abaixo, deixe desmarcadas as opções de criar README, `.gitignore` ou LICENSE pelo site, pois já existem.

Na pasta limpa:

```powershell
git init -b main
git add .
git status --short
git diff --cached --stat
git commit -m "feat: initial public OECD Inflation Explorer"
git remote add origin https://github.com/SEU-USUARIO/oecd-data-lab.git
git push -u origin main
```

Substitua `SEU-USUARIO` pelo seu perfil real. Antes de confirmar o commit, verifique que `.venv`, `.git`, `.idea`, `.env` e arquivos brutos **não** aparecem em `git status` / `git diff --cached --stat`.

## Passo 3 — Conferir CI

Abra **GitHub → Actions**. O workflow `CI` testa o projeto com Python 3.13 e `uv.lock`. **Só avance quando a primeira execução estiver verde**. Se houver falha, inspecione o log e corrija o repositório.

## Passo 4 — Implantar no Streamlit Community Cloud

1. Abra https://share.streamlit.io/ e faça login com GitHub.
2. Crie um app a partir do repositório público `SEU-USUARIO/oecd-data-lab`, branch `main`.
3. Selecione **Main file path**: `apps/inflation_explorer/app.py`.
4. Nas configurações avançadas, escolha **Python 3.13**.
5. Confirme que `uv.lock` foi encontrado na raiz do repositório; ele é priorizado na instalação de dependências.
6. Clique em deploy e espere a aplicação abrir. Teste também sem login e em janela anônima.
7. Insira no README a **URL real** gerada pelo Streamlit e inclua uma captura de tela real, sem inventar URL.

O Cloud lê arquivos do GitHub, **não** o disco do seu PyCharm. Se o snapshot Gold for removido do repositório, o app precisará de uma estratégia alternativa de dados.

## Passo 5 — Lançamento do portfólio

- Adicionar link ao perfil GitHub e imagem real do dashboard.
- Tag sugerida `v0.1.0` para coincidir com o `pyproject.toml`.
- Criar release com resumo, limites e datasets utilizados.
- Abrir issues para expansão LATAM, melhorias dos painéis e refresh automatizado.

## Troubleshooting breve

- **`FileNotFoundError` Gold:** o `.parquet` não foi versionado ou o caminho foi alterado.
- **`ModuleNotFoundError`:** conferir `uv.lock`, `pyproject.toml` e build do pacote `src/oecd_data_lab`.
- **Versão de Python:** `requires-python = ">=3.13"`; selecionar 3.13 no Cloud.
- **Valores de 2026 não aparecem:** o arquivo `latest` ainda não foi aprovado/distribuído ao servidor. A mensagem sobre Gold não aparece na interface; é responsabilidade do backend.
- **Falha no CI:** rodar `uv run python -m pytest -q` localmente e conferir os logs do job.

Referência Streamlit: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy e https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/app-dependencies .
