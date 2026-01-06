"""
Página: Performance de Agentes
Métricas comparativas e análises por agente.
"""

import pandas as pd
import streamlit as st

from src.dashboard_utils import (
    apply_custom_css,
    apply_filters,
    classify_contact_context,
    classify_lead_qualification,
    create_excel_download,
    get_chat_tags,
    get_colors,
    get_lead_status,
    render_echarts_bar,
    render_echarts_bar_gradient,
    render_user_sidebar,
    setup_plotly_theme,
)

st.set_page_config(page_title="Agentes", page_icon="👥", layout="wide")

# Require authentication
from src.auth.auth_manager import AuthManager

AuthManager.require_auth()

# Setup
setup_plotly_theme()
apply_custom_css()
render_user_sidebar()
COLORS = get_colors()

st.title("👥 Performance de Agentes")
st.markdown("---")

# Check data
if "chats" not in st.session_state or not st.session_state.chats:
    st.warning(
        "⚠️ Dados não carregados. Volte para a página principal e carregue os dados."
    )
    st.stop()

# Aplicar filtros globais
filters = st.session_state.get("filters", {})
chats = apply_filters(st.session_state.chats, filters)

if not chats:
    st.warning("⚠️ Nenhum dado encontrado com os filtros aplicados.")
    st.stop()


# ================================================================
# FILTROS ESPECÍFICOS
# ================================================================

st.sidebar.header("🔧 Filtros de Agente")
business_hours_only = st.sidebar.checkbox(
    "Apenas horário comercial",
    value=False,
    help="Filtrar apenas contatos feitos em horário comercial (Seg-Sex 08h-18h)",
)

# Filtrar chats
filtered_chats = chats
if business_hours_only:
    filtered_chats = [
        c
        for c in chats
        if c.firstMessageDate
        and classify_contact_context(c.firstMessageDate) == "horario_comercial"
    ]
    if len(filtered_chats) == 0:
        st.warning(
            "Nenhum chat com horário comercial encontrado. Desmarque o filtro para ver todos os dados."
        )
        filtered_chats = chats  # Fallback to all chats

if len(filtered_chats) == 0:
    st.warning("Nenhum chat encontrado.")
    st.stop()


# ================================================================
# AGRUPAR POR AGENTE
# ================================================================

agent_data = {}

for chat in filtered_chats:
    agent_name = chat.agent.name if chat.agent else "Sem Agente"

    if agent_name not in agent_data:
        agent_data[agent_name] = {
            "chats": [],
            "waiting_times": [],
            "qa_scores": [],
            "qualificados": 0,
            "total": 0,
        }

    agent_data[agent_name]["chats"].append(chat)
    agent_data[agent_name]["total"] += 1

    if chat.waitingTime:
        agent_data[agent_name]["waiting_times"].append(chat.waitingTime)

    # Coletar QA Score se disponivel
    if hasattr(chat, "qa_score") and chat.qa_score is not None:
        agent_data[agent_name]["qa_scores"].append(chat.qa_score)

    qual = get_lead_status(chat)
    if qual == "qualificado":
        agent_data[agent_name]["qualificados"] += 1


# Calcular métricas
agents_metrics = []
for agent_name, data in agent_data.items():
    if agent_name == "Sem Agente":
        continue

    avg_tme = (
        sum(data["waiting_times"]) / len(data["waiting_times"])
        if data["waiting_times"]
        else 0
    )
    avg_qa = sum(data["qa_scores"]) / len(data["qa_scores"]) if data["qa_scores"] else 0
    qual_rate = (data["qualificados"] / data["total"] * 100) if data["total"] > 0 else 0

    agents_metrics.append(
        {
            "Agente": agent_name,
            "Atendimentos": data["total"],
            "TME (s)": avg_tme,
            "TME (min)": avg_tme / 60,
            "Nota QA": avg_qa,
            "Qualificados": data["qualificados"],
            "Taxa Qualificação (%)": qual_rate,
        }
    )

if not agents_metrics:
    st.warning("Nenhum dado de agente disponível.")
    st.stop()

df_agents = pd.DataFrame(agents_metrics)


# ================================================================
# KPIs
# ================================================================

col1, col2, col3 = st.columns(3)

total_agents = len(df_agents)
col1.metric("Total de Agentes", total_agents)

avg_tme_all = df_agents["TME (min)"].mean()
col2.metric("TME Médio (todos)", f"{avg_tme_all:.1f} min")

avg_qual_all = df_agents["Taxa Qualificação (%)"].mean()
col3.metric("Taxa Qualificação Média", f"{avg_qual_all:.1f}%")

# KPI de QA
col4 = st.empty()
with col4:
    avg_qa_all = (
        df_agents[df_agents["Nota QA"] > 0]["Nota QA"].mean()
        if not df_agents[df_agents["Nota QA"] > 0].empty
        else 0
    )
    st.metric("Nota QA Média", f"{avg_qa_all:.1f}/5.0")

# Disclaimer
if business_hours_only:
    st.info(
        "📌 Métricas calculadas apenas para contatos em **horário comercial** (Seg-Sex 08h-18h)."
    )

st.markdown("---")


# ================================================================
# RANKING DE TME
# ================================================================

col_left, col_right = st.columns(2)

with col_left:
    st.subheader("⏱️ Ranking de TME (Melhor → Pior)")

    df_sorted_tme = df_agents.sort_values("TME (min)").head(15)
    tme_data = df_sorted_tme.to_dict("records")

    # ECharts com gradiente (verde = baixo TME, vermelho = alto)
    render_echarts_bar_gradient(
        data=tme_data,
        x_key="Agente",
        y_key="TME (min)",
        gradient_type="success_to_danger",
        height="400px",
        key="ranking_tme",
    )


with col_right:
    st.subheader("🎯 Ranking de Qualificação")

    df_sorted_qual = df_agents.sort_values(
        "Taxa Qualificação (%)", ascending=False
    ).head(15)
    qual_data = df_sorted_qual.to_dict("records")

    # ECharts com gradiente (verde = alta qualificação)
    render_echarts_bar_gradient(
        data=qual_data,
        x_key="Agente",
        y_key="Taxa Qualificação (%)",
        gradient_type="danger_to_success",
        reverse_y=True,
        height="400px",
        key="ranking_qualificacao",
    )

# Rank de QA
st.markdown("---")
st.subheader("⭐ Ranking de Qualidade (QA Score)")
df_sorted_qa = (
    df_agents[df_agents["Nota QA"] > 0].sort_values("Nota QA", ascending=False).head(15)
)

if not df_sorted_qa.empty:
    qa_data = df_sorted_qa.to_dict("records")
    render_echarts_bar_gradient(
        data=qa_data,
        x_key="Agente",
        y_key="Nota QA",
        gradient_type="danger_to_success",  # Maior é melhor
        reverse_y=True,
        height="350px",
        key="ranking_qa",
    )
else:
    st.info("ℹ️ Nenhuma nota de QA disponível (requer análise de IA).")


# ================================================================
# VOLUME E TME POR AGENTE (2 gráficos separados)
# ================================================================

st.markdown("---")
st.subheader("📊 Volume e TME por Agente")

col_vol, col_tme = st.columns(2)

with col_vol:
    st.markdown("**📈 Volume de Atendimentos**")
    df_vol = df_agents.sort_values("Atendimentos", ascending=False).head(15)
    vol_data = df_vol.to_dict("records")

    # Barras simples para volume
    render_echarts_bar(
        data=vol_data,
        x_key="Agente",
        y_key="Atendimentos",
        horizontal=True,
        height="400px",
        key="agentes_volume",
    )

with col_tme:
    st.markdown("**⏱️ TME Médio (minutos)**")
    df_tme_sorted = df_agents.sort_values("TME (min)", ascending=True).head(15)
    tme_agents_data = df_tme_sorted.to_dict("records")

    # ECharts com gradiente
    render_echarts_bar_gradient(
        data=tme_agents_data,
        x_key="Agente",
        y_key="TME (min)",
        gradient_type="success_to_danger",
        height="400px",
        key="agentes_tme",
    )


# ================================================================
# TABELA DETALHADA
# ================================================================

st.markdown("---")
st.subheader("📋 Tabela Detalhada")

df_display = df_agents.copy()
df_display["TME (min)"] = df_display["TME (min)"].apply(lambda x: f"{x:.1f}")
df_display["Nota QA"] = df_display["Nota QA"].apply(
    lambda x: f"{x:.1f}" if x > 0 else "-"
)
df_display["Taxa Qualificação (%)"] = df_display["Taxa Qualificação (%)"].apply(
    lambda x: f"{x:.1f}%"
)
df_display = df_display.drop(columns=["TME (s)"])

st.dataframe(
    df_display.sort_values("Atendimentos", ascending=False),
    width="stretch",
    hide_index=True,
)

# Exportar para Excel
col_export, _ = st.columns([1, 3])
with col_export:
    create_excel_download(
        df_agents.drop(columns=["TME (s)"]),
        filename="agentes_performance",
        sheet_name="Performance Agentes",
        key="export_agentes",
    )
