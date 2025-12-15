"""
Página: Análise de Leads
Origem, qualificação, funil e conversão.
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.dashboard_utils import (
    TAGS_CONVERTIDO,
    TAGS_NAO_CONVERTIDO,
    TAGS_OUTROS,
    apply_chart_theme,
    apply_custom_css,
    apply_filters,
    classify_lead_qualification,
    get_chat_tags,
    get_colors,
    get_lead_origin,
    setup_plotly_theme,
)

st.set_page_config(page_title="Leads", page_icon="🎯", layout="wide")

# Setup
setup_plotly_theme()
apply_custom_css()
COLORS = get_colors()

st.title("🎯 Análise de Leads")
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
# KPIs DE LEADS
# ================================================================

col1, col2, col3, col4 = st.columns(4)

# Contar qualificações
qualifications = [classify_lead_qualification(get_chat_tags(c)) for c in chats]
qual_counts = {
    "qualificado": sum(1 for q in qualifications if q == "qualificado"),
    "nao_qualificado": sum(1 for q in qualifications if q == "nao_qualificado"),
    "outro": sum(1 for q in qualifications if q == "outro"),
    "sem_tag": sum(1 for q in qualifications if q == "sem_tag"),
}

total = len(chats)
col1.metric("Total de Leads", f"{total:,}")
col2.metric("Qualificados", f"{qual_counts['qualificado']:,}")
col3.metric("Não Qualificados", f"{qual_counts['nao_qualificado']:,}")

# Taxa de qualificação
qual_rate = (qual_counts["qualificado"] / total * 100) if total > 0 else 0
col4.metric("Taxa de Qualificação", f"{qual_rate:.1f}%")

st.markdown("---")


# ================================================================
# ANÁLISE POR ORIGEM
# ================================================================

st.subheader("📈 Performance por Origem do Lead")

# Agrupar por origem
origin_data = {}
for chat in chats:
    origin = get_lead_origin(chat)
    if origin not in origin_data:
        origin_data[origin] = {"total": 0, "qualificados": 0, "tme_sum": 0, "tme_count": 0}

    origin_data[origin]["total"] += 1

    qual = classify_lead_qualification(get_chat_tags(chat))
    if qual == "qualificado":
        origin_data[origin]["qualificados"] += 1

    if chat.waitingTime:
        origin_data[origin]["tme_sum"] += chat.waitingTime
        origin_data[origin]["tme_count"] += 1

# Criar DataFrame
origin_metrics = []
for origin, data in origin_data.items():
    if data["total"] >= 1:  # Mínimo de 1 lead para análise
        avg_tme = (data["tme_sum"] / data["tme_count"] / 60) if data["tme_count"] > 0 else 0
        qual_rate = (data["qualificados"] / data["total"] * 100) if data["total"] > 0 else 0

        origin_metrics.append(
            {
                "Origem": origin,
                "Total": data["total"],
                "Qualificados": data["qualificados"],
                "Taxa Qualificação (%)": qual_rate,
                "TME (min)": avg_tme,
            }
        )

if origin_metrics:
    df_origins = pd.DataFrame(origin_metrics)
    df_origins = df_origins.sort_values("Total", ascending=False)

    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("**Volume por Origem**")
        fig_vol = px.bar(
            df_origins.head(10),
            x="Total",
            y="Origem",
            orientation="h",
            color="Total",
            color_continuous_scale=[[0, COLORS["info"]], [1, COLORS["primary"]]],
            text="Total",  # Labels visíveis
        )
        fig_vol = apply_chart_theme(fig_vol)
        fig_vol.update_traces(textposition="outside")
        fig_vol.update_layout(
            showlegend=False,
            coloraxis_showscale=False,
            yaxis=dict(categoryorder="total descending"),  # Ordenar maior→menor
        )
        st.plotly_chart(fig_vol, width="stretch")

    with col_right:
        st.markdown("**Taxa de Qualificação por Origem**")
        fig_qual = px.bar(
            df_origins.head(10),
            x="Taxa Qualificação (%)",
            y="Origem",
            orientation="h",
            color="Taxa Qualificação (%)",
            color_continuous_scale=[[0, COLORS["danger"]], [0.5, COLORS["warning"]], [1, COLORS["success"]]],
            text=df_origins.head(10)["Taxa Qualificação (%)"].apply(lambda x: f"{x:.1f}%"),  # Labels
        )
        fig_qual = apply_chart_theme(fig_qual)
        fig_qual.update_traces(textposition="outside")
        fig_qual.update_layout(
            showlegend=False,
            coloraxis_showscale=False,
            yaxis=dict(categoryorder="total descending"),  # Ordenar maior→menor
        )
        st.plotly_chart(fig_qual, width="stretch")
else:
    st.info("📊 Nenhum dado de origem disponível. Verifique o campo `contact.customFields.origem_do_negocio`.")


# ================================================================
# FUNIL DE QUALIFICAÇÃO
# ================================================================

st.markdown("---")
st.subheader("🔄 Funil de Qualificação")

# Dados do funil
funnel_data = [
    {"Etapa": "Total de Leads", "Quantidade": total},
    {"Etapa": "Respondidos pelo Bot", "Quantidade": sum(1 for c in chats if c.withBot == "true")},
    {"Etapa": "Atendidos por Humano", "Quantidade": sum(1 for c in chats if c.agent is not None)},
    {"Etapa": "Qualificados (Q/Q+)", "Quantidade": qual_counts["qualificado"]},
]

df_funnel = pd.DataFrame(funnel_data)

fig_funnel = go.Figure(
    go.Funnel(
        y=df_funnel["Etapa"],
        x=df_funnel["Quantidade"],
        textinfo="value+percent initial",
        marker=dict(color=[COLORS["info"], COLORS["secondary"], COLORS["primary"], COLORS["success"]]),
    )
)
fig_funnel = apply_chart_theme(fig_funnel)
st.plotly_chart(fig_funnel, width="stretch")


# ================================================================
# DISTRIBUIÇÃO DE TAGS
# ================================================================

st.markdown("---")
st.subheader("🏷️ Distribuição de Tags de Qualificação")

all_tags = []
for c in chats:
    all_tags.extend(get_chat_tags(c))

if all_tags:
    tag_counts = {}
    for tag in all_tags:
        tag_counts[tag] = tag_counts.get(tag, 0) + 1

    # Separar por categoria
    tag_data = []
    for tag, count in tag_counts.items():
        if tag in TAGS_CONVERTIDO:
            category = "Qualificado"
        elif tag in TAGS_NAO_CONVERTIDO:
            category = "Não Qualificado"
        elif tag in TAGS_OUTROS:
            category = "Outros"
        else:
            category = "Outros"

        tag_data.append({"Tag": tag, "Quantidade": count, "Categoria": category})

    df_tags = pd.DataFrame(tag_data)
    df_tags = df_tags.sort_values("Quantidade", ascending=False)

    fig_tags = px.bar(
        df_tags,
        x="Quantidade",
        y="Tag",
        orientation="h",
        color="Categoria",
        color_discrete_map={
            "Qualificado": COLORS["success"],
            "Não Qualificado": COLORS["danger"],
            "Outros": COLORS["warning"],
        },
        text="Quantidade",  # Labels visíveis
    )
    fig_tags = apply_chart_theme(fig_tags)
    fig_tags.update_traces(textposition="outside")
    fig_tags.update_layout(yaxis=dict(categoryorder="total descending"))  # Ordenar maior→menor
    st.plotly_chart(fig_tags, width="stretch")


# ================================================================
# TABELA DE PERFORMANCE POR ORIGEM
# ================================================================

st.markdown("---")
st.subheader("📊 Tabela Detalhada por Origem")

if origin_metrics:
    df_display = df_origins.copy()
    df_display["Taxa Qualificação (%)"] = df_display["Taxa Qualificação (%)"].apply(lambda x: f"{x:.1f}%")
    df_display["TME (min)"] = df_display["TME (min)"].apply(lambda x: f"{x:.1f}")

    st.dataframe(df_display, width="stretch", hide_index=True)
