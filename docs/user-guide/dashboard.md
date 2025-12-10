# O Dashboard

O dashboard é o painel visual onde você acompanha todos os resultados das análises.

---

## Como Acessar

```bash
poetry run streamlit run dashboard.py
```

Após executar, abra o navegador em: `http://localhost:8501`

---

## Seções do Dashboard

### 📈 Métricas Gerais

No topo do dashboard você encontra 4 cards com os números principais:

| Card | O que mostra |
|------|--------------|
| **Total de Chats** | Quantas conversas foram analisadas |
| **TME Médio** | Tempo médio de espera por resposta |
| **TMA Médio** | Duração média das conversas |
| **Taxa de Conversão** | % de chats que viraram vendas |

---

### 🏆 Ranking de Atendentes

Um gráfico de barras mostra os atendentes ordenados por velocidade de resposta.

!!! tip "Dica"
    Quanto menor o TME, mais rápido o atendente responde.

A tabela ao lado mostra:
- Nome do atendente
- Quantidade de chats
- TME (tempo de espera)
- Score de humanização (1-5)

---

### 🔥 Produtos Mais Mencionados

Dois gráficos mostram os produtos mais falados nas conversas:

- **Gráfico de Pizza**: Distribuição proporcional
- **Gráfico de Barras**: Top 10 produtos

!!! info "Top of Mind"
    São os produtos que estão "na cabeça" dos clientes.

---

### 📊 Funil de Vendas

Visualização do "caminho" das conversas:

```
┌─────────────────────────────┐
│     ⏳ Em Progresso         │
└─────────────────────────────┘
          │
          ▼
    ┌───────────┐
    │ ✅ Venda  │
    └───────────┘
          │
    ┌───────────┐
    │ ❌ Perda  │
    └───────────┘
```

Ao lado, você vê os **motivos de perda** mais comuns.

---

## Filtros (Em Desenvolvimento)

!!! warning "Em breve"
    Futuramente será possível filtrar por:

    - Período (data inicial/final)
    - Agente específico
    - Canal (WhatsApp, Chat, etc.)

---

## Exportar Dados

O relatório completo é salvo automaticamente em `analysis_report.json` após cada execução do pipeline principal.
