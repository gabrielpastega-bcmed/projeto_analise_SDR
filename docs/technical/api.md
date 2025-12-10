# API Reference

## Módulo: `src.models`

### `Chat`
Modelo principal de um chat.

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | `str` | ID único do chat |
| `number` | `str` | Número do chat |
| `channel` | `str` | Canal (whatsapp, etc.) |
| `contact` | `Contact` | Dados do cliente |
| `agent` | `Optional[Agent]` | Dados do atendente |
| `messages` | `List[Message]` | Lista de mensagens |
| `status` | `str` | Status do chat |

---

## Módulo: `src.ingestion`

### `load_chats_from_json(file_path: str) -> List[Chat]`
Carrega chats de um arquivo JSON.

**Parâmetros:**
- `file_path`: Caminho para o arquivo JSON

**Retorna:**
- Lista de objetos `Chat`

---

## Módulo: `src.ops_analysis`

### `is_business_hour(dt: datetime) -> bool`
Verifica se datetime está dentro do horário comercial.

**Horário Comercial:**
- Seg-Qui: 08:00 - 18:00
- Sex: 08:00 - 17:00

**Parâmetros:**
- `dt`: Datetime (timezone aware)

**Retorna:**
- `True` se estiver no expediente

---

### `calculate_response_times(chat: Chat) -> Dict[str, Any]`
Calcula métricas de tempo de resposta.

**Retorna:**
```python
{
    "tme_seconds": float,    # Tempo Médio de Espera
    "tma_seconds": float,    # Tempo Médio de Atendimento
    "response_count": int    # Quantidade de respostas
}
```

---

### `analyze_agent_performance(chats: List[Chat]) -> List[Dict]`
Gera ranking de agentes.

**Retorna:**
```python
[
    {
        "agent": str,
        "chats": int,
        "avg_tme_seconds": float,
        "avg_tma_seconds": float
    }
]
```

---

## Módulo: `src.llm_analysis`

### `LLMAnalyzer`
Classe para análise qualitativa com LLM.

#### `__init__(api_key: str = "mock_key")`
Inicializa o analisador.

#### `async analyze_chat(chat: Chat) -> Dict[str, Any]`
Analisa um chat e retorna insights.

**Retorna:**
```python
{
    "cx": {
        "sentiment": str,
        "humanization_score": int,
        "resolution_status": str
    },
    "product": {
        "products_mentioned": List[str],
        "interest_level": str
    },
    "sales": {
        "outcome": str,
        "rejection_reason": Optional[str]
    }
}
```

---

## Módulo: `src.reporting`

### `generate_report(processed_data: List[Dict]) -> Dict`
Gera relatório agregado.

**Retorna:**
```python
{
    "agent_ranking": List[Dict],
    "product_cloud": List[Tuple[str, int]],
    "sales_funnel": Dict[str, int],
    "loss_reasons": Dict[str, int]
}
```
