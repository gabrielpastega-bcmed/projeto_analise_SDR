"""
Dashboard Principal - Entry Point
Carrega dados e configura filtros globais para as páginas.
"""

import nest_asyncio
import streamlit as st

# Apply nest_asyncio to allow nested event loops in Streamlit
# This MUST run before importing modules that use asyncio
nest_asyncio.apply()

from src.auth.auth_manager import AuthManager  # noqa: E402
from src.dashboard_utils import (  # noqa: E402
    apply_custom_css,
    get_colors,
    get_lead_origin,
    init_session_state,
    render_user_sidebar,
    setup_plotly_theme,
)
from src.ingestion import (  # noqa: E402
    get_data_source,
    load_chats_from_bigquery,
    load_chats_from_json,
)

# Require authentication for all pages
AuthManager.require_auth()

# Page config
st.set_page_config(
    page_title="Dashboard SDR - Demo",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Setup
setup_plotly_theme()
apply_custom_css()
init_session_state()
render_user_sidebar()
COLORS = get_colors()

# ================================================================
# TÍTULO E DESCRIÇÃO
# ================================================================

st.title("📊 Dashboard de Análise SDR")
st.markdown(
    """
**Bem-vindo ao Dashboard de Análise SDR.**

Use o menu lateral para navegar entre as diferentes análises:
- **📊 Visão Geral** - KPIs macro, métricas gerais
- **👥 Agentes** - Performance comparativa de agentes
- **📈 Análise Temporal** - TME por horário, primeiro contato
- **🎯 Leads** - Origem, qualificação, funil
"""
)

st.markdown("---")


# ================================================================
# SIDEBAR - CONFIGURAÇÕES E FILTROS
# ================================================================

st.sidebar.header("⚙️ Configurações")

# Fonte de dados
data_source = get_data_source()
st.sidebar.info(f"📁 Fonte de dados: **{data_source.upper()}**")

# Opções de carregamento
st.sidebar.subheader("📊 Opções de Carregamento")
days = st.sidebar.slider("Dias para análise", min_value=1, max_value=90, value=7)
limit = st.sidebar.slider("Limite de chats", min_value=100, max_value=10000, value=2000, step=100)
lightweight = st.sidebar.checkbox(
    "Modo leve (mais rápido)",
    value=True,
    help="Exclui mensagens individuais para carregamento mais rápido",
)

# Botão para carregar dados
if st.sidebar.button("🔄 Carregar/Atualizar Dados", type="primary"):
    with st.spinner(f"Carregando dados ({days} dias, limite {limit})..."):
        try:
            if data_source == "bigquery":
                chats = load_chats_from_bigquery(days=days, limit=limit, lightweight=lightweight)
            else:
                chats = load_chats_from_json("data/raw/mock_dashboard_data.json")

            st.session_state.chats = chats
            st.session_state.data_loaded = True
            st.success(f"✅ Carregados {len(chats)} chats com sucesso!")
        except Exception as e:
            st.error(f"❌ Erro ao carregar dados: {e}")
            st.session_state.data_loaded = False

# Se não há dados carregados, tenta carregar automaticamente (modo leve)
if not st.session_state.data_loaded:
    with st.spinner("Carregando dados iniciais (modo leve)..."):
        try:
            if data_source == "bigquery":
                # Carregamento inicial leve: 7 dias, limite 1000, sem mensagens
                chats = load_chats_from_bigquery(days=7, limit=1000, lightweight=True)
            else:
                chats = load_chats_from_json("data/raw/mock_dashboard_data.json")

            st.session_state.chats = chats
            st.session_state.data_loaded = True
        except Exception as e:
            st.warning(f"⚠️ Não foi possível carregar dados automaticamente: {e}")

# ================================================================
# FILTROS GLOBAIS
# ================================================================

if st.session_state.data_loaded and st.session_state.chats:
    chats = st.session_state.chats

    st.sidebar.markdown("---")
    st.sidebar.header("🔍 Filtros Globais")

    # Filtro por período (datas)
    dates = [c.firstMessageDate for c in chats if c.firstMessageDate]
    date_range: tuple | None = None  # Inicializar antes do if
    if dates:
        min_date = min(dates).date()
        max_date = max(dates).date()
        date_range = st.sidebar.date_input(
            "Período",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date,
            help="Filtrar por período de atendimento",
        )

    # Filtro por agente
    agents = list(set(c.agent.name for c in chats if c.agent and c.agent.name))
    agents.sort()

    selected_agents = st.sidebar.multiselect(
        "Agentes",
        options=agents,
        default=[],
        placeholder="Todos os agentes",
    )

    # Filtro por origem
    origins = list(set(get_lead_origin(c) for c in chats if get_lead_origin(c)))
    origins.sort()

    selected_origins = st.sidebar.multiselect(
        "Origem do Lead",
        options=origins,
        default=[],
        placeholder="Todas as origens",
    )

    # Filtro por tags
    from src.dashboard_utils import get_chat_tags

    all_available_tags_set: set[str] = set()
    for c in chats:
        all_available_tags_set.update(get_chat_tags(c))
    all_available_tags = sorted(list(all_available_tags_set))

    selected_tags = st.sidebar.multiselect(
        "Tags de Qualificação",
        options=all_available_tags,
        default=[],
        placeholder="Todas as tags",
    )

    # Filtro horário comercial
    business_hours_only = st.sidebar.checkbox(
        "Apenas Horário Comercial",
        value=False,
        help="Filtrar apenas contatos em horário comercial (Seg-Sex, 08:00-18:00)",
    )

    # Salvar filtros no session_state
    st.session_state.filters = {
        "agents": selected_agents,
        "origins": selected_origins,
        "tags": selected_tags,
        "business_hours_only": business_hours_only,
        "date_range": date_range if date_range and len(date_range) == 2 else None,
    }

    # ================================================================
    # RESUMO DOS DADOS CARREGADOS
    # ================================================================

    st.subheader("📋 Resumo dos Dados")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total de Chats", f"{len(chats):,}")

    agents_count = len(set(c.agent.name for c in chats if c.agent))
    col2.metric("Agentes", agents_count)

    origins_count = len(set(get_lead_origin(c) for c in chats))
    col3.metric("Origens de Lead", origins_count)

    # Período dos dados
    dates = [c.firstMessageDate for c in chats if c.firstMessageDate]
    if dates:
        min_date_str = min(dates).strftime("%d/%m/%Y")
        max_date_str = max(dates).strftime("%d/%m/%Y")
        col4.metric("Período", f"{min_date_str} - {max_date_str}")

    st.markdown("---")

    # ================================================================
    # MÉTRICAS RÁPIDAS
    # ================================================================

    st.subheader("📈 Métricas Rápidas")

    col1, col2, col3, col4 = st.columns(4)

    # TME médio
    waiting_times = [c.waitingTime for c in chats if c.waitingTime]
    avg_tme = (sum(waiting_times) / len(waiting_times) / 60) if waiting_times else 0
    col1.metric("TME Médio", f"{avg_tme:.1f} min")

    # Com bot
    with_bot = sum(1 for c in chats if c.withBot == "true")
    bot_rate = (with_bot / len(chats) * 100) if chats else 0
    col2.metric("% Com Bot", f"{bot_rate:.1f}%")

    # Tags mais comum
    from src.dashboard_utils import get_chat_tags

    all_tags = []
    for c in chats:
        all_tags.extend(get_chat_tags(c))
    if all_tags:
        from collections import Counter

        most_common = Counter(all_tags).most_common(1)[0]
        col3.metric("Tag Mais Comum", most_common[0][:20])

    # Origem mais comum
    all_origins = [get_lead_origin(c) for c in chats]
    if all_origins:
        most_common_origin = Counter(all_origins).most_common(1)[0]
        col4.metric("Origem Principal", most_common_origin[0][:25])

    st.markdown("---")

    # ================================================================
    # QUICK LINKS - NAVEGAÇÃO RÁPIDA
    # ================================================================

    st.subheader("🚀 Navegação Rápida")

    link_col1, link_col2, link_col3, link_col4 = st.columns(4)

    with link_col1:
        st.markdown(
            """
        <div style="padding: 15px; border-radius: 12px;
             background: linear-gradient(135deg, #3b82f6, #1d4ed8); text-align: center;">
            <div style="font-size: 2em;">📊</div>
            <div style="color: white; font-weight: 600; margin-top: 8px;">Visão Geral</div>
            <div style="color: rgba(255,255,255,0.8); font-size: 0.85em;">KPIs e métricas macro</div>
        </div>
        """,
            unsafe_allow_html=True,
        )
        if st.button("Acessar →", key="nav_visao"):
            st.switch_page("pages/1_📊_Visão_Geral.py")

    with link_col2:
        st.markdown(
            """
        <div style="padding: 15px; border-radius: 12px;
             background: linear-gradient(135deg, #22c55e, #16a34a); text-align: center;">
            <div style="font-size: 2em;">👥</div>
            <div style="color: white; font-weight: 600; margin-top: 8px;">Agentes</div>
            <div style="color: rgba(255,255,255,0.8); font-size: 0.85em;">Performance comparativa</div>
        </div>
        """,
            unsafe_allow_html=True,
        )
        if st.button("Acessar →", key="nav_agentes"):
            st.switch_page("pages/2_👥_Agentes.py")

    with link_col3:
        st.markdown(
            """
        <div style="padding: 15px; border-radius: 12px;
             background: linear-gradient(135deg, #f59e0b, #d97706); text-align: center;">
            <div style="font-size: 2em;">📈</div>
            <div style="color: white; font-weight: 600; margin-top: 8px;">Temporal</div>
            <div style="color: rgba(255,255,255,0.8); font-size: 0.85em;">Análise por horário</div>
        </div>
        """,
            unsafe_allow_html=True,
        )
        if st.button("Acessar →", key="nav_temporal"):
            st.switch_page("pages/3_📈_Análise_Temporal.py")

    with link_col4:
        st.markdown(
            """
        <div style="padding: 15px; border-radius: 12px;
             background: linear-gradient(135deg, #8b5cf6, #7c3aed); text-align: center;">
            <div style="font-size: 2em;">🎯</div>
            <div style="color: white; font-weight: 600; margin-top: 8px;">Leads</div>
            <div style="color: rgba(255,255,255,0.8); font-size: 0.85em;">Origem e qualificação</div>
        </div>
        """,
            unsafe_allow_html=True,
        )
        if st.button("Acessar →", key="nav_leads"):
            st.switch_page("pages/4_🎯_Leads.py")

else:
    st.warning("⚠️ Carregue os dados usando o botão na barra lateral para visualizar as análises.")
    st.info(
        "Se estiver usando BigQuery, certifique-se de que as variáveis de ambiente estão configuradas corretamente."
    )
