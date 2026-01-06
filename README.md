# Projeto Análise SDR

[![CI](https://github.com/gabrielpastega-bcmed/projeto_analise_SDR/actions/workflows/ci.yml/badge.svg)](https://github.com/gabrielpastega-bcmed/projeto_analise_SDR/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%20%7C%203.13%20%7C%203.14-blue.svg)](https://www.python.org/downloads/)
[![Coverage](https://img.shields.io/badge/coverage-82%25-brightgreen.svg)]()
[![Tests](https://img.shields.io/badge/tests-200%2B%20passing-brightgreen.svg)]()

Sistema de análise de conversas de atendimento (chat logs) para extração de insights de **CX**, **Inteligência de Produto**, **Performance Operacional** e **Conversão de Vendas**.

## 🚀 Funcionalidades

### Dashboard Multi-Página

O sistema inclui um **dashboard interativo** com páginas especializadas:

| Página | Descrição |
|--------|-----------|
| 🔐 **Login** | Autenticação híbrida (usuário/senha + Google OAuth) |
| 📊 **Visão Geral** | KPIs macro, distribuição de qualificação, volume por origem, filtros avançados |
| 👥 **Agentes** | Ranking de TME, taxa de qualificação, scatter TME vs Volume |
| 📈 **Análise Temporal** | Volume por hora, TME por hora, comparativo horário comercial |
| 🎯 **Leads** | Performance por origem, funil de qualificação, distribuição de tags |
| 🧠 **Insights** | Dashboard consolidado com métricas agregadas do BigQuery |
| ⚙️ **Admin** | Gerenciamento de usuários (superadmin only) |
| 🔔 **Alertas** | Monitoramento de métricas em tempo real com notificações |
| 🏥 **Health** | Status de integrações e saúde do sistema |
| 🤖 **Automação** | Monitoramento de GitHub Actions e análises automáticas |

### 🆕 Novidades v2.0.0 (Janeiro 2026)

#### 🔒 Prompts Externalizados
- Prompts de LLM movidos para `config/prompts/`
- Arquivos `.txt` para customização fácil
- Templates `.example.txt` incluídos para referência
- Separação entre código e metodologia de análise

#### 🐛 Correções de Bugs
- Corrigido import quebrado em `dashboard.py`
- Removido código morto em `dashboard_utils.py`
- Corrigidos nomes de propriedades em `filters.py` (alinhamento com modelo `Chat`)
- Corrigido `asyncio.get_event_loop()` deprecado → `asyncio.get_running_loop()`
- Adicionado import `Dict` faltante em `ingestion.py`
- Corrigido `use_container_width` deprecado → `width="stretch"` (Streamlit 1.41+)

#### 🔔 Sistema de Alertas
- Monitoramento automático de TME, Volume e Taxa de Conversão
- Notificações em tempo real na sidebar
- Histórico completo de incidentes
- Configuração de thresholds personalizáveis

#### 🔍 Filtros Avançados
- Filtro por período (data início/fim com presets)
- Filtro por agente (multiselect)
- Filtro por origem e qualificação
- Persistência em sessão

#### 📥 Exportação Profissional
- Excel com múltiplas abas (Resumo, Detalhes, Por Agente)
- Formatação rica (cores, bordas, zebra stripes)
- Download com timestamp

### Análise Operacional (Algorítmica)
- **TME** (Tempo Médio de Espera): Tempo até primeira resposta humana
- **TMA** (Tempo Médio de Atendimento): Duração total da conversa
- **Ranking de Agentes**: Ordenação por velocidade e volume
- **Filtro de Horário Comercial**: Seg-Sex (08:00-18:00)

### Análise Qualitativa (LLM)
- **CX**: Sentimento, Score de Humanização (1-5), Status de Resolução
- **Produtos**: "Top of Mind", Tendências de busca
- **Vendas**: Taxa de Conversão, Motivos de Perda
- **Cache Redis**: Economia de custos em LLM com cache de respostas

### Performance & Escalabilidade
- **BigQuery Streaming**: Paginação automática para grandes datasets
- **Chunked Writes**: Inserções em chunks de 500 linhas
- **Memory Optimization**: ~80% menos memória para datasets >1000 chats

## 📦 Instalação

```bash
# Clone o repositório
git clone https://github.com/seu-usuario/projeto_analise_SDR.git
cd projeto_analise_SDR

# Instale as dependências com Poetry
poetry install

# Configure os prompts (copie os templates e customize)
cp config/prompts/*.example.txt config/prompts/
# Renomeie removendo .example e edite conforme necessário
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

# Executar com cobertura
poetry run pytest --cov=src --cov-report=term-missing

# Verificar linting
poetry run ruff check .

# Verificar tipos
poetry run mypy .
```

## 📁 Estrutura do Projeto

```
projeto_analise_SDR/
├── dashboard.py            # Entry point do dashboard
├── config/
│   └── prompts/            # Prompts de LLM (gitignored, exceto .example)
│       ├── cx_analysis.txt
│       ├── product_analysis.txt
│       ├── sales_analysis.txt
│       ├── qa_analysis.txt
│       └── *.example.txt   # Templates (committed)
├── pages/                  # Páginas do dashboard multi-page
│   ├── 0_🔐_Login.py
│   ├── 1_📊_Visão_Geral.py
│   ├── 2_👥_Agentes.py
│   ├── 3_📈_Análise_Temporal.py
│   ├── 4_🎯_Leads.py
│   ├── 5_🧠_Insights.py
│   ├── 6_⚙️_Admin.py
│   ├── 7_🔔_Alertas.py
│   ├── 8_🏥_Health.py
│   └── 9_🤖_Automação.py
├── src/                    # Código fonte principal
│   ├── auth/               # Módulo de autenticação
│   ├── filters.py          # Componente de filtros avançados
│   ├── excel_export.py     # Exportação Excel profissional
│   ├── models.py           # Modelos Pydantic
│   ├── ingestion.py        # Carregamento (JSON/BigQuery)
│   ├── ops_analysis.py     # Análise operacional
│   ├── gemini_client.py    # Cliente Gemini API (carrega prompts de arquivos)
│   ├── batch_analyzer.py   # ETL com checkpoint
│   └── dashboard_utils.py  # Utilitários (ECharts, temas)
├── tests/                  # Testes unitários (200+ testes, 82% cobertura)
├── .github/workflows/      # CI/CD
└── pyproject.toml          # Configuração
```

## 🔧 Configuração

O projeto usa as seguintes ferramentas:
- **Python 3.12+** (compatível com 3.13 e 3.14)
- **Poetry** para gerenciamento de dependências
- **Streamlit 1.41+** para o dashboard
- **Pydantic 2.10+** para validação de dados
- **Plotly 6.1+** para gráficos interativos
- **google-genai 1.56+** para análise LLM
- **pytest** para testes
- **ruff** para linting
- **mypy** para type checking

### Variáveis de Ambiente

Copie `.env.example` para `.env` e configure:

```bash
# Gemini API (Análise LLM)
GEMINI_API_KEY=sua-api-key

# BigQuery (Opcional - para dados em produção)
BIGQUERY_PROJECT_ID=seu-projeto
BIGQUERY_DATASET=seu-dataset
BIGQUERY_TABLE=sua-tabela
GOOGLE_APPLICATION_CREDENTIALS=caminho/para/credentials.json

# Google OAuth (Login Social)
GOOGLE_OAUTH_ENABLED=true
GOOGLE_OAUTH_CLIENT_ID=seu_client_id.apps.googleusercontent.com
GOOGLE_OAUTH_CLIENT_SECRET=seu_client_secret
GOOGLE_OAUTH_REDIRECT_URI=http://localhost:8501
GOOGLE_OAUTH_COOKIE_NAME=sdr_analytics_auth
GOOGLE_OAUTH_COOKIE_KEY=chave_secreta_32_caracteres

# PostgreSQL (Autenticação e Resultados)
AUTH_DATABASE_HOST=localhost
AUTH_DATABASE_PORT=5432
AUTH_DATABASE_NAME=sdr_analytics
AUTH_DATABASE_USER=postgres
AUTH_DATABASE_PASSWORD=sua-senha

# Configuração de Análise
ANALYSIS_DAYS=7
```

## 📊 Qualidade do Código

- ✅ **200+ testes unitários** com **82% de cobertura**
- ✅ **CI/CD** automatizado (GitHub Actions)
- ✅ **Type hints** com validação mypy
- ✅ **Linting** com ruff
- ✅ **Pre-commit hooks** para qualidade

## 🎓 Documentação

Para mais detalhes sobre as implementações, consulte:
- [AUTHENTICATION_GUIDE.md](AUTHENTICATION_GUIDE.md) - Guia de autenticação
- [CHANGELOG.md](CHANGELOG.md) - Histórico de versões

## 📄 Licença

Este projeto está licenciado sob a [Apache License 2.0](LICENSE).
