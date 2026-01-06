"""
Página: Visão Geral
KPIs macro, métricas gerais e overview do dashboard.
"""

from datetime import datetime

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.dashboard_utils import (
    TAGS_CONVERTIDO,
    TAGS_NAO_CONVERTIDO,
    apply_chart_theme,
    apply_custom_css,
    calculate_delta,
    classify_lead_qualification,
    get_chat_tags,
    get_colors,
    get_lead_origin,
    get_lead_status,
    render_echarts_bar,
    render_echarts_pie,
    render_user_sidebar,
    setup_plotly_theme,
    split_chats_by_period,
)

st.set_page_config(page_title="Visão Geral", page_icon="📊", layout="wide")

# Require authentication
from src.auth.auth_manager import AuthManager

AuthManager.require_auth()

# Setup
setup_plotly_theme()
apply_custom_css()
render_user_sidebar()
COLORS = get_colors()


st.title("📊 Visão Geral")
st.markdown("---")

# Check if data is loaded
if "chats" not in st.session_state or not st.session_state.chats:
    st.warning(
        "⚠️ Dados não carregados. Volte para a página principal e carregue os dados."
    )
    st.stop()

# Advanced Filters
from src.filters import FilterComponent

filter_component = FilterComponent(key_prefix="visao_geral")
filter_component.render()

# Apply filters
chats = filter_component.apply_to_chats(st.session_state.chats)

# Show filter summary and export button
col1, col2 = st.columns([3, 1])
with col1:
    if filter_component.has_active_filters():
        st.info(f"🔍 Filtros: {filter_component.get_filter_summary()}")
with col2:
    if st.button("📥 Exportar Excel", width="stretch"):
        from src.excel_export import create_chat_export

        excel_bytes = create_chat_export(chats, filter_component.get_current_filters())
        st.download_button(
            label="⬇️ Download",
            data=excel_bytes,
            file_name=f"visao_geral_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            width="stretch",
        )

if not chats:
    st.warning("⚠️ Nenhum dado encontrado com os filtros aplicados.")
    st.stop()

st.markdown("---")


# ================================================================
# KPIs PRINCIPAIS COM COMPARATIVO
# ================================================================

# Dividir chats por período (últimos 7 dias vs 7 dias anteriores)
current_chats, previous_chats = split_chats_by_period(chats, days=7)


# Calcular métricas do período anterior para comparativo
def calc_metrics(chat_list):
    total = len(chat_list)
    waiting = [c.waitingTime for c in chat_list if c.waitingTime is not None]
    avg_tme = (sum(waiting) / len(waiting) / 60) if waiting else 0
    quals = [get_lead_status(c) for c in chat_list]
    qual_rate = (
        (sum(1 for q in quals if q == "qualificado") / total * 100) if total > 0 else 0
    )
    msgs = [c.messagesCount or len(c.messages) for c in chat_list]
    avg_msg = (sum(msgs) / len(msgs)) if msgs else 0
    return total, avg_tme, qual_rate, avg_msg


curr_total, curr_tme, curr_qual, curr_msg = calc_metrics(chats)
prev_total, prev_tme, prev_qual, prev_msg = (
    calc_metrics(previous_chats) if previous_chats else (0, 0, 0, 0)
)

# Calcular deltas
_, delta_total, _ = calculate_delta(curr_total, prev_total)
_, delta_tme, _ = calculate_delta(curr_tme, prev_tme)
_, delta_qual, _ = calculate_delta(curr_qual, prev_qual)
_, delta_msg, _ = calculate_delta(curr_msg, prev_msg)

col1, col2, col3, col4 = st.columns(4)

# KPIs com deltas
col1.metric(
    "Total de Atendimentos",
    f"{curr_total:,}",
    delta=delta_total if prev_total > 0 else None,
    help="Comparativo com período anterior",
)
col2.metric(
    "TME Médio",
    f"{curr_tme:.1f} min",
    delta=delta_tme if prev_tme > 0 else None,
    delta_color="inverse",  # Menos TME é melhor
    help="Tempo Médio de Espera - menos é melhor",
)
col3.metric(
    "Taxa de Qualificação",
    f"{curr_qual:.1f}%",
    delta=delta_qual if prev_qual > 0 else None,
    help="% de leads qualificados",
)
col4.metric(
    "Msgs por Chat",
    f"{curr_msg:.1f}",
    delta=delta_msg if prev_msg > 0 else None,
    delta_color="off",
    help="Média de mensagens por atendimento",
)

st.markdown("---")


# ================================================================
# GRÁFICOS PRINCIPAIS
# ================================================================

col_left, col_right = st.columns(2)

# Distribuição de Qualificação
with col_left:
    st.subheader("🎯 Distribuição de Qualificação")

    # Calcular qualificações para o gráfico
    qualifications = [get_lead_status(c) for c in chats]
    qual_counts = {}
    for q in qualifications:
        qual_counts[q] = qual_counts.get(q, 0) + 1

    labels_map = {
        "qualificado": "Qualificado",
        "nao_qualificado": "Não Qualificado",
        "outro": "Outros",
        "sem_tag": "Sem Tag",
    }

    color_map = {
        "Qualificado": COLORS["success"],
        "Não Qualificado": COLORS["danger"],
        "Outros": COLORS["warning"],
        "Sem Tag": COLORS["info"],
    }

    qual_df_data = [
        {"Qualificação": labels_map.get(k, k), "Quantidade": v}
        for k, v in qual_counts.items()
    ]

    if qual_df_data:
        # Usar gráfico de pizza ECharts
        render_echarts_pie(
            data=qual_df_data,
            name_key="Qualificação",
            value_key="Quantidade",
            color_map=color_map,
            height="350px",
            key="distribuicao_qualificacao",
        )


# Volume por Origem
with col_right:
    st.subheader("📈 Volume por Origem")

    # Extrair origens de cada chat
    origins = [get_lead_origin(c) for c in chats]
    origin_counts = {}
    for origin in origins:
        origin_counts[origin] = origin_counts.get(origin, 0) + 1

    # Ordenar por quantidade (top 10)
    sorted_origins = sorted(origin_counts.items(), key=lambda x: x[1], reverse=True)[
        :10
    ]

    if len(sorted_origins) > 0:
        # Converter para lista de dicts
        origin_data = [{"Origem": o, "Quantidade": q} for o, q in sorted_origins]

        # Gráfico de barras ECharts
        render_echarts_bar(
            data=origin_data,
            x_key="Origem",
            y_key="Quantidade",
            horizontal=True,
            height="350px",
            key="volume_por_origem",
        )
    else:
        st.info("📊 Nenhuma origem encontrada nos dados carregados.")


# ================================================================
# HEATMAP (se disponível)
# ================================================================

st.markdown("---")
st.subheader("🔥 Mapa de Calor - Mensagens por Dia/Hora")
st.caption("💼 Horário comercial: Segunda a Sexta, 08:00-18:00")

try:
    from src.ops_analysis import analyze_heatmap_lightweight

    heatmap_data = analyze_heatmap_lightweight(chats)

    if heatmap_data:
        import numpy as np
        import pandas as pd

        # Dias da semana (0=Segunda, 6=Domingo)
        days = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
        hours = list(range(24))

        # Converter o dict para matriz
        # heatmap_data é Dict[str, Dict[int, int]] onde chave é weekday (0-6) e valor é dict de horas
        matrix = np.zeros((7, 24))
        for weekday_str, hour_counts in heatmap_data.items():
            weekday = int(weekday_str)
            for hour, count in hour_counts.items():
                matrix[weekday][int(hour)] = count

        # Criar anotações para horário comercial
        annotations = []
        # Destacar horário comercial (Seg-Sex, 08-18)
        for day_idx in range(5):  # Seg-Sex
            for hour in range(8, 18):  # 08h-18h
                annotations.append(
                    dict(
                        x=f"{hour:02d}h",
                        y=days[day_idx],
                        text="",
                        showarrow=False,
                    )
                )

        fig_heatmap = go.Figure(
            data=go.Heatmap(
                z=matrix,
                x=[f"{h:02d}h" for h in hours],
                y=days,
                colorscale="Viridis",  # Gradiente verde-amarelo-roxo
                hoverongaps=False,
                hovertemplate="Dia: %{y}<br>Hora: %{x}<br>Mensagens: %{z}<extra></extra>",
            )
        )
        fig_heatmap = apply_chart_theme(fig_heatmap)
        fig_heatmap.update_layout(
            xaxis_title="Hora do Dia",
            yaxis_title="Dia da Semana",
        )

        # Adicionar retângulo para destacar horário comercial
        fig_heatmap.add_shape(
            type="rect",
            x0=7.5,
            x1=17.5,  # 08h a 18h (índices)
            y0=-0.5,
            y1=4.5,  # Seg a Sex
            line=dict(color=COLORS["success"], width=2, dash="dash"),
            fillcolor="rgba(0,0,0,0)",
        )

        st.plotly_chart(fig_heatmap, key="heatmap_mensagens")
    else:
        st.info("📊 Dados insuficientes para gerar o heatmap.")
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

    # Criar DataFrame com categoria de cor
    tag_data = []
    for tag, count in sorted_tags:
        if tag in TAGS_CONVERTIDO:
            category = "Qualificado"
        elif tag in TAGS_NAO_CONVERTIDO:
            category = "Não Qualificado"
        else:
            category = "Outros"
        tag_data.append({"Tag": tag, "Quantidade": count, "Categoria": category})

    tag_df = pd.DataFrame(tag_data)
    fig_tags = px.bar(
        tag_df,
        x="Quantidade",
        y="Tag",
        orientation="h",
        color="Categoria",
        color_discrete_map={
            "Qualificado": COLORS["success"],
            "Não Qualificado": COLORS["danger"],
            "Outros": COLORS["secondary"],
        },
        text="Quantidade",
    )
    fig_tags = apply_chart_theme(fig_tags)
    fig_tags.update_traces(textposition="outside")
    fig_tags.update_layout(
        yaxis=dict(categoryorder="total ascending"),
    )
    st.plotly_chart(fig_tags, key="tags_frequentes")
