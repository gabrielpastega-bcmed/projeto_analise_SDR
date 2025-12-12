# Projeto Análise SDR

[![CI](https://github.com/gabrielpastega-empresa/projeto_analise_SDR/actions/workflows/ci.yml/badge.svg)](https://github.com/gabrielpastega-empresa/projeto_analise_SDR/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/gabrielpastega-empresa/projeto_analise_SDR/graph/badge.svg)](https://codecov.io/gh/gabrielpastega-empresa/projeto_analise_SDR)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)

Sistema de análise de conversas de atendimento (chat logs) para extração de insights de **CX**, **Inteligência de Produto**, **Performance Operacional** e **Conversão de Vendas**.

## 🚀 Funcionalidades

### Dashboard Multi-Página

O sistema inclui um **dashboard interativo** com 4 páginas especializadas:

| Página | Descrição |
|--------|-----------|
| 📊 **Visão Geral** | KPIs macro, distribuição de qualificação, volume por origem, heatmap |
| 👥 **Agentes** | Ranking de TME, taxa de qualificação, scatter TME vs Volume |
| 📈 **Análise Temporal** | Volume por hora, TME por hora, comparativo horário comercial |
| 🎯 **Leads** | Performance por origem, funil de qualificação, distribuição de tags |

### Análise Operacional (Algorítmica)
- **TME** (Tempo Médio de Espera): Tempo até primeira resposta humana
- **TMA** (Tempo Médio de Atendimento): Duração total da conversa
- **Ranking de Agentes**: Ordenação por velocidade e volume
- **Filtro de Horário Comercial**: Seg-Sex (08:00-18:00)

### Análise Qualitativa (LLM)
- **CX**: Sentimento, Score de Humanização (1-5), Status de Resolução
- **Produtos**: "Top of Mind", Tendências de busca
- **Vendas**: Taxa de Conversão, Motivos de Perda

### Relatórios
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
# Inicie o dashboard interativo
poetry run streamlit run dashboard.py

# Execute a análise via CLI
poetry run python main.py
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
├── dashboard.py            # Entry point do dashboard
├── pages/                  # Páginas do dashboard multi-page
│   ├── 1_📊_Visão_Geral.py
│   ├── 2_👥_Agentes.py
│   ├── 3_📈_Análise_Temporal.py
│   └── 4_🎯_Leads.py
├── src/                    # Código fonte principal
│   ├── models.py           # Modelos Pydantic para parsing de dados
│   ├── ingestion.py        # Carregamento de dados (JSON/BigQuery)
│   ├── ops_analysis.py     # Análise operacional (TMA, TME)
│   ├── llm_analysis.py     # Análise qualitativa (LLM)
│   ├── dashboard_utils.py  # Utilitários do dashboard
│   └── reporting.py        # Agregação e relatórios
├── tests/                  # Testes unitários
├── data/raw/               # Dados de exemplo
├── .github/workflows/      # CI/CD com GitHub Actions
└── pyproject.toml          # Configuração do projeto
```

## 🔧 Configuração

O projeto usa as seguintes ferramentas:
- **Python 3.12+**
- **Poetry** para gerenciamento de dependências
- **Streamlit** para o dashboard
- **Pydantic** para validação de dados
- **Plotly** para gráficos interativos
- **pytest** para testes
- **ruff** para linting
- **mypy** para type checking

### Variáveis de Ambiente (Opcional - BigQuery)

```bash
BIGQUERY_PROJECT_ID=seu-projeto
BIGQUERY_DATASET=seu-dataset
BIGQUERY_TABLE=sua-tabela
GOOGLE_APPLICATION_CREDENTIALS=caminho/para/credentials.json
ANALYSIS_DAYS=7
```

## 📜 Changelog

Veja o histórico completo de versões na [documentação](https://gabrielpastega-empresa.github.io/projeto_analise_SDR/changelog/).

## 📄 Licença

Este projeto está licenciado sob os termos da licença incluída no arquivo LICENSE.
