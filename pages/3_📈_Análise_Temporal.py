"""
Página: Análise Temporal
TME por horário, primeiro contato, e análises de tempo.
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import pytz
import streamlit as st

from src.dashboard_utils import (
    BUSINESS_HOURS,
    apply_chart_theme,
    apply_custom_css,
    apply_filters,
    classify_contact_context,
    get_colors,
    is_business_hour,
    setup_plotly_theme,
)

st.set_page_config(page_title="Análise Temporal", page_icon="📈", layout="wide")

# Setup
setup_plotly_theme()
apply_custom_css()
COLORS = get_colors()

st.title("📈 Análise Temporal")
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
# ANÁLISE DE PRIMEIRO CONTATO POR HORA
# ================================================================

st.subheader("📞 Volume de Primeiros Contatos por Hora do Dia")

# Agrupar por hora (usando timezone local)
TIMEZONE = pytz.timezone("America/Sao_Paulo")
hour_counts = {h: 0 for h in range(24)}
hour_counts_bh = {h: 0 for h in range(24)}  # Business hours only

for chat in chats:
    if chat.firstMessageDate:
        # Converter para timezone local
        if chat.firstMessageDate.tzinfo is None:
            local_dt = TIMEZONE.localize(chat.firstMessageDate)
        else:
            local_dt = chat.firstMessageDate.astimezone(TIMEZONE)
        hour = local_dt.hour
        hour_counts[hour] += 1

        if is_business_hour(chat.firstMessageDate):
            hour_counts_bh[hour] += 1

df_hours = pd.DataFrame(
    [{"Hora": f"{h:02d}h", "Total": hour_counts[h], "Horário Comercial": hour_counts_bh[h]} for h in range(24)]
)

fig_hours = go.Figure()
fig_hours.add_trace(
    go.Bar(
        x=df_hours["Hora"],
        y=df_hours["Total"],
        name="Total",
        marker_color=COLORS["info"],
        opacity=0.6,
    )
)
fig_hours.add_trace(
    go.Bar(
        x=df_hours["Hora"],
        y=df_hours["Horário Comercial"],
        name="Horário Comercial",
        marker_color=COLORS["success"],
    )
)

fig_hours = apply_chart_theme(fig_hours)

# Adicionar destaque de horário comercial (08:00-18:00)
fig_hours.add_vrect(
    x0="08h",
    x1="18h",
    fillcolor=COLORS["success"],
    opacity=0.1,
    annotation_text="Horário Comercial",
    annotation_position="top left",
    line_width=0,
)

fig_hours.update_layout(
    barmode="overlay",
    xaxis_title="Hora do Dia",
    yaxis_title="Quantidade de Contatos",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
)
st.plotly_chart(fig_hours, key="volume_por_hora")

# Insight
peak_hour = max(hour_counts.items(), key=lambda x: x[1])
st.caption(f"💡 **Pico de demanda:** {peak_hour[0]:02d}h com {peak_hour[1]} contatos.")


# ================================================================
# TME POR HORA DO DIA
# ================================================================

st.markdown("---")
st.subheader("⏱️ TME Médio por Hora do Dia")

# Agrupar TME por hora
tme_by_hour = {h: [] for h in range(24)}

for chat in chats:
    if chat.firstMessageDate and chat.waitingTime:
        hour = chat.firstMessageDate.hour
        tme_by_hour[hour].append(chat.waitingTime)

df_tme_hour = pd.DataFrame(
    [
        {
            "Hora": f"{h:02d}h",
            "TME (min)": (sum(times) / len(times) / 60) if times else 0,
            "Contatos": len(times),
        }
        for h, times in tme_by_hour.items()
    ]
)

# Apenas horas com dados
df_tme_hour_filtered = df_tme_hour[df_tme_hour["Contatos"] > 0]

if not df_tme_hour_filtered.empty:
    fig_tme_hour = px.line(
        df_tme_hour_filtered,
        x="Hora",
        y="TME (min)",
        markers=True,
        text=df_tme_hour_filtered["TME (min)"].apply(lambda x: f"{x:.1f}"),  # Labels
        color_discrete_sequence=[COLORS["primary"]],
    )
    fig_tme_hour = apply_chart_theme(fig_tme_hour)
    fig_tme_hour.update_traces(textposition="top center")
    fig_tme_hour.update_layout(
        xaxis_title="Hora do Primeiro Contato",
        yaxis_title="TME Médio (minutos)",
    )

    # Adicionar área de horário comercial (08:00-18:00)
    fig_tme_hour.add_vrect(
        x0=f"{BUSINESS_HOURS['start']:02d}h",
        x1=f"{BUSINESS_HOURS['end']:02d}h",
        fillcolor=COLORS["success"],
        opacity=0.1,
        annotation_text="Horário Comercial",
        annotation_position="top left",
    )

    st.plotly_chart(fig_tme_hour, key="tme_por_hora")
else:
    st.info("Sem dados de TME por hora.")


# ================================================================
# COMPARATIVO: HORÁRIO COMERCIAL vs FORA
# ================================================================

st.markdown("---")
st.subheader("🕐 TME: Horário Comercial vs Fora do Expediente")

col1, col2 = st.columns(2)

# Segmentar chats por contexto
chats_bh = []  # Business hours
chats_off = []  # Off hours

for chat in chats:
    if chat.firstMessageDate:
        context = classify_contact_context(chat.firstMessageDate)
        if context == "horario_comercial":
            chats_bh.append(chat)
        elif context == "fora_expediente":
            chats_off.append(chat)

# Calcular métricas
bh_times = [c.waitingTime for c in chats_bh if c.waitingTime]
off_times = [c.waitingTime for c in chats_off if c.waitingTime]

avg_bh = (sum(bh_times) / len(bh_times) / 60) if bh_times else 0
avg_off = (sum(off_times) / len(off_times) / 60) if off_times else 0

with col1:
    st.metric(
        "TME Horário Comercial",
        f"{avg_bh:.1f} min",
        f"{len(chats_bh):,} chats",
    )

with col2:
    st.metric(
        "TME Fora do Expediente",
        f"{avg_off:.1f} min",
        f"{len(chats_off):,} chats",
    )

# Gráfico de comparação
comparison_data = [
    {"Contexto": "Horário Comercial", "TME (min)": avg_bh, "Chats": len(chats_bh)},
    {"Contexto": "Fora do Expediente", "TME (min)": avg_off, "Chats": len(chats_off)},
]
df_comparison = pd.DataFrame(comparison_data)

fig_comparison = px.bar(
    df_comparison,
    x="Contexto",
    y="TME (min)",
    color="Contexto",
    color_discrete_map={
        "Horário Comercial": COLORS["success"],
        "Fora do Expediente": COLORS["warning"],
    },
    text=df_comparison["TME (min)"].apply(lambda x: f"{x:.1f} min"),
)
fig_comparison = apply_chart_theme(fig_comparison)
fig_comparison.update_traces(textposition="outside")
fig_comparison.update_layout(showlegend=False)
st.plotly_chart(fig_comparison, key="comparacao_tme")

st.info("""
📌 **Nota sobre TME fora do expediente:**
O tempo de espera para contatos feitos fora do horário comercial inclui o período
até a abertura do expediente. Isso é esperado e não indica problema de atendimento.
""")


# ================================================================
# TENDÊNCIA TEMPORAL
# ================================================================

st.markdown("---")
st.subheader("📅 Tendência de Volume por Dia")

# Agrupar por data
date_counts = {}
for chat in chats:
    if chat.firstMessageDate:
        date_key = chat.firstMessageDate.date()
        date_counts[date_key] = date_counts.get(date_key, 0) + 1

if date_counts:
    df_dates = pd.DataFrame([{"Data": d, "Contatos": c} for d, c in sorted(date_counts.items())])

    fig_trend = px.line(
        df_dates,
        x="Data",
        y="Contatos",
        markers=True,
        text="Contatos",  # Labels visíveis
        color_discrete_sequence=[COLORS["primary"]],
    )
    fig_trend = apply_chart_theme(fig_trend)
    fig_trend.update_traces(textposition="top center")
    fig_trend.update_layout(
        xaxis_title="Data",
        yaxis_title="Número de Contatos",
    )
    st.plotly_chart(fig_trend, key="tendencia_diaria")
else:
    st.info("Sem dados de tendência temporal.")
