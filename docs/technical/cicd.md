# CI/CD

## GitHub Actions

O projeto usa GitHub Actions para automação de CI/CD.

### Workflow Principal (`.github/workflows/ci.yml`)

```yaml
name: CI

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]
```

### Jobs

| Job | Descrição | Python |
|-----|-----------|--------|
| `lint` | Ruff check + format | 3.12 |
| `typecheck` | Mypy | 3.12 |
| `test` | Pytest + Coverage | 3.11, 3.12 |
| `security` | Bandit | 3.12 |

---

## Pre-commit Hooks

### Configuração

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    hooks:
      - id: ruff
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    hooks:
      - id: mypy
```

### Instalação

```bash
poetry run pre-commit install
```

### Execução Manual

```bash
poetry run pre-commit run --all-files
```

---

## Coverage

### Configuração (`pyproject.toml`)

```toml
[tool.coverage.run]
source = ["src"]
branch = true

[tool.coverage.report]
fail_under = 70
show_missing = true
```

### Execução

```bash
poetry run pytest --cov=src --cov-report=term-missing
```

---

## Documentação (MkDocs)

### Servir Localmente

```bash
poetry run mkdocs serve
```

### Build

```bash
poetry run mkdocs build
```

### Deploy GitHub Pages

```bash
poetry run mkdocs gh-deploy
```

---

## Deploy da Documentação

O workflow de deploy é automático via GitHub Actions:

```yaml
# .github/workflows/docs.yml
name: Deploy Docs

on:
  push:
    branches: [ main ]
    paths:
      - 'docs/**'
      - 'mkdocs.yml'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
      - run: pip install mkdocs-material
      - run: mkdocs gh-deploy --force
```
