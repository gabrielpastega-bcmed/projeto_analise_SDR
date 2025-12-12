"""
Página: Visão Geral
KPIs macro, métricas gerais e overview do dashboard.
"""

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.dashboard_utils import (
    apply_chart_theme,
    apply_custom_css,
    classify_lead_qualification,
    get_chat_tags,
    get_colors,
    get_lead_origin,
    setup_plotly_theme,
)

st.set_page_config(page_title="Visão Geral", page_icon="📊", layout="wide")

# Setup
setup_plotly_theme()
apply_custom_css()
COLORS = get_colors()

st.title("📊 Visão Geral")
st.markdown("---")

# Check if data is loaded
if "chats" not in st.session_state or not st.session_state.chats:
    st.warning("⚠️ Dados não carregados. Volte para a página principal e carregue os dados.")
    st.stop()

chats = st.session_state.chats


# ================================================================
# KPIs PRINCIPAIS
# ================================================================

col1, col2, col3, col4 = st.columns(4)

# Total de chats
total_chats = len(chats)
col1.metric("Total de Atendimentos", f"{total_chats:,}")

# TME médio (waitingTime)
waiting_times = [c.waitingTime for c in chats if c.waitingTime is not None]
avg_tme_seconds = sum(waiting_times) / len(waiting_times) if waiting_times else 0
avg_tme_minutes = avg_tme_seconds / 60
col2.metric("TME Médio", f"{avg_tme_minutes:.1f} min")

# Taxa de qualificação
qualifications = [classify_lead_qualification(get_chat_tags(c)) for c in chats]
qualified_count = sum(1 for q in qualifications if q == "qualificado")
qualification_rate = (qualified_count / total_chats * 100) if total_chats > 0 else 0
col3.metric("Taxa de Qualificação", f"{qualification_rate:.1f}%")

# Mensagens por chat (média)
msg_counts = [c.messagesCount or len(c.messages) for c in chats]
avg_messages = sum(msg_counts) / len(msg_counts) if msg_counts else 0
col4.metric("Msgs por Chat (Média)", f"{avg_messages:.1f}")

st.markdown("---")


# ================================================================
# GRÁFICOS PRINCIPAIS
# ================================================================

col_left, col_right = st.columns(2)

# Distribuição de Qualificação
with col_left:
    st.subheader("🎯 Distribuição de Qualificação")

    qual_counts = {}
    for q in qualifications:
        qual_counts[q] = qual_counts.get(q, 0) + 1

    labels_map = {
        "qualificado": "Qualificado",
        "nao_qualificado": "Não Qualificado",
        "outro": "Outros",
        "sem_tag": "Sem Tag",
    }

    qual_df_data = [{"Qualificação": labels_map.get(k, k), "Quantidade": v} for k, v in qual_counts.items()]

    if qual_df_data:
        import pandas as pd

        qual_df = pd.DataFrame(qual_df_data)
        fig_qual = px.pie(
            qual_df,
            values="Quantidade",
            names="Qualificação",
            color_discrete_sequence=[COLORS["success"], COLORS["danger"], COLORS["warning"], COLORS["info"]],
            hole=0.4,
        )
        fig_qual = apply_chart_theme(fig_qual)
        st.plotly_chart(fig_qual, width="stretch")


# Volume por Origem
with col_right:
    st.subheader("📈 Volume por Origem")

    origins = [get_lead_origin(c) for c in chats]
    origin_counts = {}
    for origin in origins:
        origin_counts[origin] = origin_counts.get(origin, 0) + 1

    # Ordenar por quantidade
    sorted_origins = sorted(origin_counts.items(), key=lambda x: x[1], reverse=True)[:10]

    if sorted_origins:
        import pandas as pd

        origin_df = pd.DataFrame(sorted_origins, columns=["Origem", "Quantidade"])
        fig_origin = px.bar(
            origin_df,
            x="Quantidade",
            y="Origem",
            orientation="h",
            color="Quantidade",
            color_continuous_scale=[[0, COLORS["info"]], [1, COLORS["primary"]]],
        )
        fig_origin = apply_chart_theme(fig_origin)
        fig_origin.update_layout(showlegend=False, coloraxis_showscale=False)
        st.plotly_chart(fig_origin, width="stretch")


# ================================================================
# HEATMAP (se disponível)
# ================================================================

st.markdown("---")
st.subheader("🔥 Mapa de Calor - Mensagens por Dia/Hora")

try:
    from src.ops_analysis import analyze_heatmap

    heatmap_data = analyze_heatmap(chats)

    if heatmap_data:
        import numpy as np
        import pandas as pd

        # Converter para matriz
        days = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
        hours = list(range(24))

        matrix = np.zeros((7, 24))
        for item in heatmap_data:
            matrix[item["weekday"]][item["hour"]] = item["count"]

        fig_heatmap = go.Figure(
            data=go.Heatmap(
                z=matrix,
                x=[f"{h:02d}h" for h in hours],
                y=days,
                colorscale="Viridis",
            )
        )
        fig_heatmap = apply_chart_theme(fig_heatmap)
        fig_heatmap.update_layout(
            xaxis_title="Hora do Dia",
            yaxis_title="Dia da Semana",
        )
        st.plotly_chart(fig_heatmap, width="stretch")
except Exception as e:
    st.info(f"Heatmap não disponível: {e}")


# ================================================================
# TAGS MAIS FREQUENTES
# ================================================================

st.markdown("---")
st.subheader("🏷️ Tags Mais Frequentes")

all_tags = []
for c in chats:
    all_tags.extend(get_chat_tags(c))

if all_tags:
    tag_counts = {}
    for tag in all_tags:
        tag_counts[tag] = tag_counts.get(tag, 0) + 1

    sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10]

    import pandas as pd

    tag_df = pd.DataFrame(sorted_tags, columns=["Tag", "Quantidade"])
    fig_tags = px.bar(
        tag_df,
        x="Quantidade",
        y="Tag",
        orientation="h",
        color="Quantidade",
        color_continuous_scale=[[0, COLORS["secondary"]], [1, COLORS["primary"]]],
    )
    fig_tags = apply_chart_theme(fig_tags)
    fig_tags.update_layout(showlegend=False, coloraxis_showscale=False)
    st.plotly_chart(fig_tags, width="stretch")
