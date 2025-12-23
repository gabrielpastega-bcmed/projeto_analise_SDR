"""
Página: Análise Temporal
TME por horário, primeiro contato, e análises de tempo.
"""

import pandas as pd
import pytz
import streamlit as st

from src.dashboard_utils import (
    apply_custom_css,
    apply_filters,
    classify_contact_context,
    get_colors,
    is_business_hour,
    render_echarts_bar,
    render_echarts_line,
    render_user_sidebar,
    setup_plotly_theme,
)

st.set_page_config(page_title="Análise Temporal", page_icon="📈", layout="wide")

# Require authentication
from src.auth.auth_manager import AuthManager

AuthManager.require_auth()

# Setup
setup_plotly_theme()
apply_custom_css()
render_user_sidebar()
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
    [
        {
            "Hora": f"{h:02d}h",
            "Total": hour_counts[h],
            "Horário Comercial": hour_counts_bh[h],
        }
        for h in range(24)
    ]
)

# Converter para lista de dicts para ECharts
hours_data = df_hours.to_dict("records")

# Gráfico de barras ECharts
render_echarts_bar(
    data=hours_data,
    x_key="Hora",
    y_key="Total",
    height="400px",
    show_label=False,
    key="volume_por_hora",
)

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
    # Converter para lista de dicts para ECharts
    tme_hour_data = df_tme_hour_filtered.to_dict("records")

    # Gráfico de linha ECharts
    render_echarts_line(
        data=tme_hour_data,
        x_key="Hora",
        y_key="TME (min)",
        height="400px",
        smooth=True,
        fill_area=True,
        key="tme_por_hora",
    )
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

# Gráfico de barras ECharts para comparação
comparison_bar_data = df_comparison.to_dict("records")
render_echarts_bar(
    data=comparison_bar_data,
    x_key="Contexto",
    y_key="TME (min)",
    horizontal=False,
    height="350px",
    key="comparacao_tme",
)

st.info(
    """
📌 **Nota sobre TME fora do expediente:**
O tempo de espera para contatos feitos fora do horário comercial inclui o período
até a abertura do expediente. Isso é esperado e não indica problema de atendimento.
"""
)


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
    df_dates = pd.DataFrame([{"Data": str(d), "Contatos": c} for d, c in sorted(date_counts.items())])

    # Gráfico de linha ECharts
    dates_data = df_dates.to_dict("records")
    render_echarts_line(
        data=dates_data,
        x_key="Data",
        y_key="Contatos",
        height="400px",
        smooth=True,
        fill_area=True,
        key="tendencia_diaria",
    )
else:
    st.info("Sem dados de tendência temporal.")
