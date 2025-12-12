---
description: boas práticas de desenvolvimento para este projeto
---

# Workflow de Desenvolvimento - Projeto Análise SDR

## Checklist Obrigatório para Novos Desenvolvimentos

### 1. Antes de Começar
- [ ] Criar branch a partir de `main` (ex: `feat/nome-feature`, `fix/descricao-bug`)
- [ ] Verificar se há testes existentes relacionados

### 2. Durante o Desenvolvimento
- [ ] Rodar `poetry run ruff check . --fix` para lint
- [ ] Rodar `poetry run ruff format .` para formatação
- [ ] Manter linhas com máximo de 120 caracteres

### 3. Documentação (OBRIGATÓRIO!)
// turbo
Atualizar os seguintes arquivos quando necessário:
- [ ] `README.md` - Se adicionar nova funcionalidade visível
- [ ] `docs/user-guide/dashboard.md` - Se adicionar nova página ou KPI
- [ ] `docs/technical/` - Se adicionar nova integração ou arquitetura
- [ ] `.env.example` - Se adicionar nova variável de ambiente

### 4. Deploy da Documentação (GitHub Pages)
Após atualizar arquivos em `docs/`, fazer deploy:
```bash
// turbo
poetry run mkdocs gh-deploy --force
```

### 5. Commit e Push
- [ ] Usar Conventional Commits: `feat:`, `fix:`, `docs:`, `refactor:`
- [ ] Rodar `git commit` (SEM --no-verify) para validar pre-commit hooks
- [ ] Push apenas do branch: `git push origin nome-do-branch`

### 6. Pull Request (NO GITHUB!)
- [ ] Criar PR pelo link fornecido após o push
- [ ] NÃO fazer merge local - deixar o GitHub gerenciar
- [ ] Aguardar CI passar antes de fazer merge

## Variáveis de Ambiente do Projeto

```bash
# BigQuery
BIGQUERY_PROJECT_ID=
BIGQUERY_DATASET=
BIGQUERY_TABLE=
GOOGLE_APPLICATION_CREDENTIALS=

# Análise
ANALYSIS_DAYS=7

# Gemini (análise qualitativa)
GEMINI_API_KEY=
```

## Estrutura de Páginas do Dashboard

| Página | Arquivo | Descrição |
|--------|---------|-----------|
| 📊 Visão Geral | `pages/1_📊_Visão_Geral.py` | KPIs macro |
| 👥 Agentes | `pages/2_👥_Agentes.py` | Performance individual |
| 📈 Análise Temporal | `pages/3_📈_Análise_Temporal.py` | Padrões de horário |
| 🎯 Leads | `pages/4_🎯_Leads.py` | Qualidade por origem |
| 🧠 Insights | `pages/5_🧠_Insights.py` | Análise qualitativa IA |

## Horário Comercial

Configurado em `src/dashboard_utils.py`:
- Segunda a Sexta
- 08:00 às 18:00
- Timezone: America/Sao_Paulo
