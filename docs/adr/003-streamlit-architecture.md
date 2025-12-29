# ADR-003: Streamlit como Framework de Dashboard

**Status:** Aceita
**Data:** 2024-10-15
**Decisores:** Tech Lead, Product Manager
**Tags:** framework, frontend, architecture

---

## Contexto

Precisamos de um dashboard para visualizar análises de atendimento SDR. Time é composto por 1 backend dev e 1 data analyst. Prazo: 2 semanas para MVP.

### Requisitos

- Protótipo rápido (< 2 semanas)
- Autenticação customizada
- Múltiplas páginas especializadas
- Gráficos interativos
- Filtros dinâmicos
- Deploy simples

---

## Decisão

**Escolhemos Streamlit como framework principal do dashboard.**

---

## Alternativas Consideradas

#### 1. ✅ **Streamlit** (Escolhida)

**Prós:**
- Python puro (sem HTML/CSS/JS)
- Protótipo em dias, não semanas
- Componentes de gráficos built-in
- Multi-page apps nativamente
- Deploy fácil (Streamlit Cloud gratuito)
- Session state para filtros
- Community ativa

**Contras:**
- Customização de UI limitada
- Não é SPA (reloads completos)
- Performance com muitos widgets
- Limitado para apps complexos

#### 2. ❌ Dash (Plotly)

**Prós:**
- Mais controle de layout
- Callbacks explícitos
- Melhor para apps complexos

**Contras:**
- Curva de aprendizado maior
- Mais código para mesma funcionalidade
- Auth não é built-in
- Deploy mais complexo

**Exemplo:**
```python
# Streamlit: 3 linhas
import streamlit as st
st.title("Dashboard")
st.line_chart(data)

# Dash: ~20 linhas
import dash
from dash import dcc, html
app = dash.Dash(__name__)
app.layout = html.Div([
    html.H1("Dashboard"),
    dcc.Graph(figure={"data": [...], "layout": {...}})
])
```

#### 3. ❌ Next.js + FastAPI

**Prós:**
- Máxima customização
- SPA verdadeiro
- Mobile-first
- SEOOptimizado

**Contras:**
- 2-3x mais código
- Requer frontend dev (não temos)
- 4-6 semanas para MVP
- Deploy mais complexo

#### 4. ❌ Jupyter Notebooks + Voilà

**Prós:**
- Familiar para data teams
- Iteração rápida

**Contras:**
- UI muito básica
- Sem autenticação built-in
- Difícil de versionar
- Não é multi-page

---

## Justificativa

### Por que Streamlit?

1. **Velocidade de Desenvolvimento**: MVP em 5 dias
   - Dia 1: Auth + Login
   - Dia 2-3: Dashboards principais
   - Dia 4: Filtros e polimento
   - Dia 5: Deploy e testes

2. **Team Fit**: Time 100% Python
   - Sem necessidade de contratar frontend
   - Data analyst pode contribuir diretamente

3. **Funcionalidades Built-in**:
   ```python
   # Filtros dinâmicos: 1 linha
   selected_agent = st.selectbox("Agente", agents)

   # Gráfico: 1 linha
   st.plotly_chart(fig)

   # File upload: 1 linha
   uploaded_file = st.file_uploader("CSV")
   ```

4. **Auth Flexível**: Permite customização total
   - PostgreSQL próprio (não vendor lock-in)
   - OAuth integrado depois

5. **Cost**: $0 para hospedar (Streamlit Cloud free tier)

---

## Trade-offs Aceitos

### O que Sacrificamos

❌ **SPA Experience**: Full page reloads
❌ **Mobile Inferior**: Não otimizado para touch
❌ **UI Customização**: Limitado a componentes Streamlit
❌ **SEO**: Não é público, então não importa

### O que Ganhamos

✅ **Time to Market**: 2 semanas vs 2 meses
✅ **Manutenibilidade**: Código Python simples
✅ **Custo de Dev**: 1 dev vs 2-3 devs
✅ **Deploy**: Click de botão vs DevOps complexo

---

## Consequências

### Decisões Arquiteturais Derivadas

1. **Session State para Filtros**:
   ```python
   if "filters" not in st.session_state:
       st.session_state.filters = {}
   ```

2. **Cache para Performance**:
   ```python
   @st.cache_data
   def load_data():
       # Evita reload a cada interação
   ```

3. **Multi-page via `pages/`**:
   ```
   pages/
   ├── 1_📊_Visão_Geral.py
   ├── 2_👥_Agentes.py
   └── 3_📈_Temporal.py
   ```

### Limitações Conhecidas

⚠️ **Não é para:**
- Apps com milhares de usuários simultâneos
- UIs altamente customizadas (design system próprio)
- Real-time updates (WebSocket)
- Mobile apps nativos

### Quando Migrar?

Considerar migração para Next.js + FastAPI se:
- > 500 usuários concorrentes
- Necessidade de SPA/offline mode
- Mobile app nativo requerido
- UI customização crítica

---

## Implementação

### Estrutura do Projeto

```
projeto_analise_SDR/
├── dashboard.py          # Entry point
├── pages/                # Multi-page app
│   ├── 0_🔐_Login.py
│   └── 1_📊_Visão_Geral.py
├── src/
│   ├── auth/             # Auth module (custom)
│   ├── dashboard_utils.py  # Shared components
│   └── ingestion.py      # Data loading
```

### Padrões Estabelecidos

1. **Require Auth**: Toda página começa com
   ```python
   from src.auth.auth_manager import AuthManager
   AuthManager.require_auth()
   ```

2. **Sidebar Consistente**:
   ```python
   from src.dashboard_utils import render_user_sidebar
   render_user_sidebar()
   ```

3. **Cache de Dados**:
   ```python
   @st.cache_data(ttl=600)  # 10 min
   def load_chats():
       ...
   ```

---

## Métricas de Sucesso

| Métrica | Target | Real | Status |
|---------|--------|------|--------|
| Time to MVP | 2 semanas | **5 dias** | ✅ +60% faster |
| Lines of Code | < 5000 | **3200** | ✅ 36% abaixo |
| Deploy Time | < 1 hora | **10 min** | ✅ 83% melhor |
| Learning Curve | 1 semana | **2 dias** | ✅ Data analyst contribuiu |

---

## Lições Aprendidas

1. **Simplicidade vence**: Framework simples = entrega rápida
2. **Python-only é produtivo**: Sem context switching entre linguagens
3. **Cache é essencial**: `@st.cache_data` salvou performance
4. **Limitações OK**: Para internal tools, trade-offs valeram a pena

---

## Revisões

| Data | Decisor | Mudança |
|------|---------|---------|
| 2024-10-15 | Tech Lead | Decisão inicial |
| 2024-12-01 | Product | Reafirmado após 6 meses de uso |

---

*Referências:*
- [Streamlit Documentation](https://docs.streamlit.io)
- [Streamlit vs Dash](https://towardsdatascience.com/streamlit-vs-dash)
- [Streamlit Multi-page Apps](https://docs.streamlit.io/library/get-started/multipage-apps)
