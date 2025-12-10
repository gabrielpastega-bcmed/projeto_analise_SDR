# Componentes do Sistema

## 1. Models (`src/models.py`)

Define os modelos de dados usando **Pydantic** para validação.

### Classes

```python
class Organization(BaseModel):
    id: str = Field(alias="_id")
    name: str
    description: Optional[str] = None

class Contact(BaseModel):
    id: str
    name: str
    email: Optional[str] = None
    organization: Optional[Organization] = None
    customFields: Optional[Dict[str, Any]] = None

class Message(BaseModel):
    id: str
    body: str
    time: datetime
    sentBy: Optional[MessageSender] = None
    type: str
    chatId: str

class Chat(BaseModel):
    id: str
    contact: Contact
    agent: Optional[Agent] = None
    messages: List[Message]
    status: str
```

### Validadores

Os validadores lidam com campos que vêm como **strings JSON**:

```python
@field_validator('contact', mode='before')
def parse_contact(cls, v):
    if isinstance(v, str):
        return json.loads(v)
    return v
```

---

## 2. Ingestão (`src/ingestion.py`)

Carrega dados de diferentes fontes.

```python
def load_chats_from_json(file_path: str) -> List[Chat]:
    """Carrega chats de um arquivo JSON."""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    return [Chat(**item) for item in data]
```

!!! info "Extensão Futura"
    Adicionar `load_chats_from_bigquery()` para integração direta.

---

## 3. Análise Operacional (`src/ops_analysis.py`)

Calcula métricas quantitativas.

### Constantes

```python
TZ = pytz.timezone('America/Sao_Paulo')
```

### Funções

#### `is_business_hour(dt: datetime) -> bool`
Verifica se datetime está no expediente.

- **Seg-Qui**: 08:00 - 18:00
- **Sex**: 08:00 - 17:00

#### `calculate_response_times(chat: Chat) -> Dict`
Calcula TME e TMA para um chat.

```python
{
    "tme_seconds": 99.27,
    "tma_seconds": 1781.24,
    "response_count": 5
}
```

#### `analyze_agent_performance(chats: List[Chat]) -> List`
Ranking de agentes por performance.

---

## 4. Análise Qualitativa (`src/llm_analysis.py`)

Análise usando LLM (atualmente **mockada**).

### Prompts

```python
PROMPT_CX = """
Analyze the following chat transcript for Customer Experience (CX).
Return a JSON object with:
- sentiment: "positive", "neutral", or "negative"
- humanization_score: integer from 1 to 5
- resolution_status: "resolved", "unresolved", or "pending"
"""
```

### Retorno

```python
{
    "cx": {
        "sentiment": "neutral",
        "humanization_score": 4,
        "resolution_status": "resolved"
    },
    "product": {
        "products_mentioned": ["Ultrassom Microfocado"],
        "interest_level": "high"
    },
    "sales": {
        "outcome": "in_progress",
        "rejection_reason": None
    }
}
```

!!! warning "Mock"
    Para usar LLM real, configure a API key e descomente o código em `_call_llm()`.

---

## 5. Relatórios (`src/reporting.py`)

Agrega resultados e gera relatório final.

```python
def generate_report(processed_data: List[Dict]) -> Dict:
    return {
        "agent_ranking": [...],
        "product_cloud": [...],
        "sales_funnel": {...},
        "loss_reasons": {...}
    }
```
