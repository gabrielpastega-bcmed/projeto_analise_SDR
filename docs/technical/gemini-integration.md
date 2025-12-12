# Integração Gemini - Análise Qualitativa

Este documento descreve a arquitetura e uso da análise qualitativa de conversas usando Google Gemini.

## Arquitetura

```
┌─────────────────────────────────────────────────────────────────┐
│                         BigQuery                                 │
│  ┌────────────────────┐     ┌──────────────────────────────┐   │
│  │  octadesk_chats    │     │  octadesk_analysis_results   │   │
│  │  (dados brutos)    │     │  (análises processadas)      │   │
│  └─────────┬──────────┘     └──────────────┬───────────────┘   │
└────────────┼───────────────────────────────┼────────────────────┘
             │                               │
             ▼                               ▼
┌────────────────────────┐    ┌────────────────────────────────┐
│  Dashboard Quantitativo │    │   Dashboard Qualitativo        │
│  (tempo real)           │    │   (histórico por semana)       │
└────────────────────────┘    └────────────────────────────────┘
```

## Componentes

### GeminiClient (`src/gemini_client.py`)

Cliente assíncrono para a API do Gemini 2.5 Flash.

**Métodos:**

| Método | Descrição |
|--------|-----------|
| `analyze(prompt)` | Envia prompt e retorna JSON |
| `analyze_chat_cx(transcript)` | Análise de experiência do cliente |
| `analyze_chat_product(transcript)` | Inteligência de produto |
| `analyze_chat_sales(transcript)` | Conversão de vendas |
| `analyze_chat_qa(transcript)` | Quality Assurance |
| `analyze_chat_full(transcript)` | Todas as análises em paralelo |

### BatchAnalyzer (`src/batch_analyzer.py`)

Processador de lotes com rate limiting e persistência.

**Métodos principais:**

| Método | Descrição |
|--------|-----------|
| `run_batch(chats, batch_size)` | Processa lista de chats |
| `save_to_bigquery(results, week_start, week_end)` | Salva no BigQuery |
| `load_from_bigquery(week_start)` | Carrega resultados de uma semana |
| `get_available_weeks()` | Lista semanas disponíveis |
| `get_analyzed_chat_ids(week_start)` | IDs já analisados (evita duplicatas) |

## Tabela BigQuery

**Nome:** `octadesk.octadesk_analysis_results`

```sql
CREATE TABLE octadesk.octadesk_analysis_results (
    chat_id STRING NOT NULL,
    week_start DATE NOT NULL,
    week_end DATE NOT NULL,
    analyzed_at TIMESTAMP NOT NULL,
    agent_name STRING,
    -- CX
    cx_sentiment STRING,
    cx_humanization_score FLOAT64,
    cx_nps_prediction FLOAT64,
    cx_resolution_status STRING,
    cx_satisfaction_comment STRING,
    -- Sales
    sales_funnel_stage STRING,
    sales_outcome STRING,
    sales_rejection_reason STRING,
    sales_next_step STRING,
    -- Product
    products_mentioned ARRAY<STRING>,
    interest_level STRING,
    trends ARRAY<STRING>,
    -- QA
    qa_script_adherence BOOL,
    key_questions_asked ARRAY<STRING>,
    improvement_areas ARRAY<STRING>
)
PARTITION BY week_start
CLUSTER BY agent_name;
```

## Scripts

### Executar Análise Semanal

```bash
# Semana anterior (padrão)
python scripts/run_weekly_analysis.py

# Semana específica
python scripts/run_weekly_analysis.py --week 2025-12-02

# Limitar quantidade
python scripts/run_weekly_analysis.py --max-chats 100
```

### Criar Tabela (primeira vez)

```bash
python scripts/create_analysis_table.py
```

## Variáveis de Ambiente

```bash
# Obrigatório
GEMINI_API_KEY=sua_api_key

# BigQuery (já existentes)
BIGQUERY_PROJECT_ID=seu-projeto
BIGQUERY_DATASET=octadesk
```

## Custos Estimados

| Modelo | Custo por 1M tokens | Estimativa mensal (5k chats) |
|--------|--------------------|-----------------------------|
| Gemini 2.5 Flash | $0.15 input / $0.60 output | ~$1.50 |

## Fluxo de Dados

1. **Batch semanal** processa chats da semana anterior
2. **Resultados salvos** no BigQuery (`octadesk_analysis_results`)
3. **Dashboard Insights** consulta BigQuery (sem LLM)
4. **Histórico disponível** via seletor de semana
