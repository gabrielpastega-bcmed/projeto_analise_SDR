# Projeto Análise SDR

[![CI](https://github.com/gabrielpastega-empresa/projeto_analise_SDR/actions/workflows/ci.yml/badge.svg)](https://github.com/gabrielpastega-empresa/projeto_analise_SDR/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/gabrielpastega-empresa/projeto_analise_SDR/graph/badge.svg)](https://codecov.io/gh/gabrielpastega-empresa/projeto_analise_SDR)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)

Sistema de análise de conversas de atendimento (chat logs) para extração de insights de **CX**, **Inteligência de Produto**, **Performance Operacional** e **Conversão de Vendas**.

## 🚀 Funcionalidades

### 1. Análise Operacional (Algorítmica)
- **Filtro de Horário Comercial**: Seg-Qui (08:00-18:00), Sex (08:00-17:00)
- **TME** (Tempo Médio de Espera): Tempo que o cliente aguarda por resposta
- **TMA** (Tempo Médio de Atendimento): Duração total da conversa
- **Ranking de Agentes**: Ordenação por velocidade e volume

### 2. Análise Qualitativa (LLM)
- **CX**: Sentimento, Score de Humanização (1-5), Status de Resolução
- **Produtos**: "Top of Mind", Tendências de busca
- **Vendas**: Taxa de Conversão, Motivos de Perda

### 3. Relatórios
- Ranking de Agentes
- Nuvem de Produtos (mais mencionados)
- Funil de Vendas
- Análise de "Loss"

## 📦 Instalação

```bash
# Clone o repositório
git clone https://github.com/gabrielpastega-empresa/projeto_analise_SDR.git
cd projeto_analise_SDR

# Instale as dependências com Poetry
poetry install
```

## 🎯 Uso

```bash
# Execute a análise
poetry run python main.py

# Inicie o dashboard interativo
poetry run streamlit run dashboard.py
```

O dashboard estará disponível em `http://localhost:8501`.

## 🧪 Desenvolvimento

```bash
# Executar testes
poetry run pytest

# Verificar linting
poetry run ruff check .

# Verificar tipos
poetry run mypy .
```

## 📁 Estrutura do Projeto

```
projeto_analise_SDR/
├── src/                    # Código fonte principal
│   ├── models.py           # Modelos Pydantic para parsing de dados
│   ├── ingestion.py        # Carregamento de dados
│   ├── ops_analysis.py     # Análise operacional (TMA, TME)
│   ├── llm_analysis.py     # Análise qualitativa (LLM)
│   └── reporting.py        # Agregação e relatórios
├── tests/                  # Testes unitários
├── data/raw/               # Dados brutos (exemplo.json)
├── .github/workflows/      # CI/CD com GitHub Actions
├── main.py                 # Script principal
└── pyproject.toml          # Configuração do projeto
```

## 🔧 Configuração

O projeto usa as seguintes ferramentas:
- **Python 3.12+**
- **Poetry** para gerenciamento de dependências
- **Pydantic** para validação de dados
- **pytest** para testes
- **ruff** para linting
- **mypy** para type checking

## 📜 Histórico de Versões

### v0.2.0
- **Otimização de Performance:** Refatoração do `ops_analysis` para usar `pandas` e do `llm_analysis` para usar `asyncio`, resultando em um processamento de dados significativamente mais rápido.
- **Segurança e LGPD:** Implementação da anonimização de dados PII (e-mails, telefones, CPFs) na camada de ingestão.
- **Robustez Aprimorada:** Melhora na validação de dados com `Pydantic` e adição de tratamento de erros no pipeline principal.
- **Legibilidade:** Adição de `docstrings` e comentários em português em todos os módulos.
- **Testes:** Fortalecimento da suíte de testes para cobrir as novas funcionalidades e garantir a correção da lógica.


## 📄 Licença

Este projeto está licenciado sob os termos da licença incluída no arquivo LICENSE.
