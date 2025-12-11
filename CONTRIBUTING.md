# Contributing to Projeto Análise SDR

Obrigado por considerar contribuir para este projeto! 🎉

## 🚀 Configuração do Ambiente

```bash
# Clone o repositório
git clone https://github.com/gabrielpastega-empresa/projeto_analise_SDR.git
cd projeto_analise_SDR

# Instale as dependências
poetry install

# Configure os pre-commit hooks
poetry run pre-commit install
```

## 📋 Padrões de Código

### Estilo
- Usamos **Ruff** para linting e formatação
- Usamos **Mypy** para type checking
- Siga o PEP 8

### Verificação Local
```bash
# Lint
poetry run ruff check .

# Formatação
poetry run ruff format .

# Type checking
poetry run mypy .

# Testes com coverage
poetry run pytest --cov=src --cov-report=term-missing
```

## 🧪 Testes

- Escreva testes para novas funcionalidades
- Mantenha cobertura mínima de 70%
- Testes devem estar em `tests/`

```bash
# Rodar testes
poetry run pytest

# Com coverage
poetry run pytest --cov=src
```

## 📝 Commits

Usamos **Conventional Commits**:

```
<tipo>: <descrição>

[corpo opcional]
```

### Tipos
- `feat`: Nova funcionalidade
- `fix`: Correção de bug
- `docs`: Documentação
- `style`: Formatação (sem mudança de código)
- `refactor`: Refatoração
- `test`: Adição/correção de testes
- `chore`: Tarefas de manutenção

### Exemplos
```
feat: adiciona análise de sentimento por LLM
fix: corrige cálculo de TME para horário comercial
docs: atualiza README com instruções do dashboard
```

## 🔄 Pull Requests

1. Crie um branch a partir de `main`
   ```bash
   git checkout -b feat/minha-feature
   ```

2. Faça suas alterações com commits semânticos

3. Garanta que todos os checks passem
   ```bash
   poetry run pre-commit run --all-files
   poetry run pytest
   ```

4. Abra um Pull Request para `main`

5. Aguarde revisão e aprovação

## � LGPD e Segurança de Dados

**CRÍTICO**: Este projeto lida com dados sensíveis.
- **NUNCA** commite dados reais de clientes (PII) no repositório.
- Use apenas dados fictícios/anonimizados na pasta `data/`.
- Certifique-se de que o `.gitignore` está bloqueando arquivos de dados reais.
- Não inclua lógica no código que dependa de PII (ex: verificar e-mail específico).

## 🔖 Versionamento

Seguimos o **Semantic Versioning (SemVer)**: `MAJOR.MINOR.PATCH`
- `MAJOR`: Mudanças incompatíveis na API/Modelos.
- `MINOR`: Novas funcionalidades compatíveis com versões anteriores.
- `PATCH`: Correções de bugs compatíveis com versões anteriores.

A versão é controlada no arquivo `pyproject.toml`.

## �📁 Estrutura do Projeto

```
projeto_analise_SDR/
├── src/                    # Código fonte
│   ├── models.py           # Modelos Pydantic
│   ├── ingestion.py        # Carregamento de dados
│   ├── ops_analysis.py     # Análise operacional
│   ├── llm_analysis.py     # Análise qualitativa
│   └── reporting.py        # Relatórios
├── tests/                  # Testes unitários
├── data/raw/               # Dados brutos
├── .github/workflows/      # CI/CD
├── dashboard.py            # Dashboard Streamlit
└── main.py                 # Script principal
```

## ❓ Dúvidas

Abra uma [Issue](https://github.com/gabrielpastega-empresa/projeto_analise_SDR/issues) para perguntas ou sugestões.
