"""
Página: Performance de Agentes
Métricas comparativas e análises por agente.
"""

import pandas as pd
import plotly.express as px
import streamlit as st

from src.dashboard_utils import (
    apply_chart_theme,
    apply_custom_css,
    apply_filters,
    classify_contact_context,
    classify_lead_qualification,
    get_chat_tags,
    get_colors,
    setup_plotly_theme,
)

st.set_page_config(page_title="Agentes", page_icon="👥", layout="wide")

# Setup
setup_plotly_theme()
apply_custom_css()
COLORS = get_colors()

st.title("👥 Performance de Agentes")
st.markdown("---")

# Check data
if "chats" not in st.session_state or not st.session_state.chats:
    st.warning("⚠️ Dados não carregados. Volte para a página principal e carregue os dados.")
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
        c for c in chats if c.firstMessageDate and classify_contact_context(c.firstMessageDate) == "horario_comercial"
    ]
    if len(filtered_chats) == 0:
        st.warning("Nenhum chat com horário comercial encontrado. Desmarque o filtro para ver todos os dados.")
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
            "qualificados": 0,
            "total": 0,
        }

    agent_data[agent_name]["chats"].append(chat)
    agent_data[agent_name]["total"] += 1

    if chat.waitingTime:
        agent_data[agent_name]["waiting_times"].append(chat.waitingTime)

    qual = classify_lead_qualification(get_chat_tags(chat))
    if qual == "qualificado":
        agent_data[agent_name]["qualificados"] += 1


# Calcular métricas
agents_metrics = []
for agent_name, data in agent_data.items():
    if agent_name == "Sem Agente":
        continue

    avg_tme = sum(data["waiting_times"]) / len(data["waiting_times"]) if data["waiting_times"] else 0
    qual_rate = (data["qualificados"] / data["total"] * 100) if data["total"] > 0 else 0

    agents_metrics.append(
        {
            "Agente": agent_name,
            "Atendimentos": data["total"],
            "TME (s)": avg_tme,
            "TME (min)": avg_tme / 60,
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

# Disclaimer
if business_hours_only:
    st.info("📌 Métricas calculadas apenas para contatos em **horário comercial** (Seg-Sex 08h-18h).")

st.markdown("---")


# ================================================================
# RANKING DE TME
# ================================================================

col_left, col_right = st.columns(2)

with col_left:
    st.subheader("⏱️ Ranking de TME (Melhor → Pior)")

    df_sorted_tme = df_agents.sort_values("TME (min)").head(15)

    fig_tme = px.bar(
        df_sorted_tme,
        x="TME (min)",
        y="Agente",
        orientation="h",
        color="TME (min)",
        color_continuous_scale=[[0, COLORS["success"]], [0.5, COLORS["warning"]], [1, COLORS["danger"]]],
        text=df_sorted_tme["TME (min)"].apply(lambda x: f"{x:.1f} min"),
    )
    fig_tme = apply_chart_theme(fig_tme)
    fig_tme.update_layout(showlegend=False, coloraxis_showscale=False, yaxis=dict(autorange="reversed"))
    fig_tme.update_traces(textposition="outside")
    st.plotly_chart(fig_tme, key="ranking_tme")


with col_right:
    st.subheader("🎯 Ranking de Qualificação")

    df_sorted_qual = df_agents.sort_values("Taxa Qualificação (%)", ascending=False).head(15)

    fig_qual = px.bar(
        df_sorted_qual,
        x="Taxa Qualificação (%)",
        y="Agente",
        orientation="h",
        color="Taxa Qualificação (%)",
        color_continuous_scale=[[0, COLORS["danger"]], [0.5, COLORS["warning"]], [1, COLORS["success"]]],
        text=df_sorted_qual["Taxa Qualificação (%)"].apply(lambda x: f"{x:.1f}%"),
    )
    fig_qual = apply_chart_theme(fig_qual)
    fig_qual.update_layout(showlegend=False, coloraxis_showscale=False, yaxis=dict(autorange="reversed"))
    fig_qual.update_traces(textposition="outside")
    st.plotly_chart(fig_qual, key="ranking_qualificacao")


# ================================================================
# VOLUME E TME POR AGENTE (2 gráficos separados)
# ================================================================

st.markdown("---")
st.subheader("📊 Volume e TME por Agente")

col_vol, col_tme = st.columns(2)

with col_vol:
    st.markdown("**📈 Volume de Atendimentos**")
    df_vol = df_agents.sort_values("Atendimentos", ascending=True).head(15)
    fig_vol = px.bar(
        df_vol,
        x="Atendimentos",
        y="Agente",
        orientation="h",
        color="Atendimentos",
        color_continuous_scale=[[0, COLORS["info"]], [1, COLORS["primary"]]],
        text="Atendimentos",
    )
    fig_vol = apply_chart_theme(fig_vol)
    fig_vol.update_traces(textposition="outside")
    fig_vol.update_layout(showlegend=False, coloraxis_showscale=False)
    st.plotly_chart(fig_vol, key="agentes_volume")

with col_tme:
    st.markdown("**⏱️ TME Médio (minutos)**")
    df_tme_sorted = df_agents.sort_values("TME (min)", ascending=True).head(15)
    fig_tme_agents = px.bar(
        df_tme_sorted,
        x="TME (min)",
        y="Agente",
        orientation="h",
        color="TME (min)",
        color_continuous_scale=[[0, COLORS["success"]], [0.5, COLORS["warning"]], [1, COLORS["danger"]]],
        text=df_tme_sorted["TME (min)"].apply(lambda x: f"{x:.1f}"),
    )
    fig_tme_agents = apply_chart_theme(fig_tme_agents)
    fig_tme_agents.update_traces(textposition="outside")
    fig_tme_agents.update_layout(showlegend=False, coloraxis_showscale=False, yaxis=dict(autorange="reversed"))
    st.plotly_chart(fig_tme_agents, key="agentes_tme")


# ================================================================
# TABELA DETALHADA
# ================================================================

st.markdown("---")
st.subheader("📋 Tabela Detalhada")

df_display = df_agents.copy()
df_display["TME (min)"] = df_display["TME (min)"].apply(lambda x: f"{x:.1f}")
df_display["Taxa Qualificação (%)"] = df_display["Taxa Qualificação (%)"].apply(lambda x: f"{x:.1f}%")
df_display = df_display.drop(columns=["TME (s)"])

st.dataframe(
    df_display.sort_values("Atendimentos", ascending=False),
    width="stretch",
    hide_index=True,
)
