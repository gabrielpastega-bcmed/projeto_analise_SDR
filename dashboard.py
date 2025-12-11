"""
Streamlit Dashboard for SDR Chat Analysis
"""

import asyncio

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

from src.ingestion import load_chats_from_json
from src.llm_analysis import LLMAnalyzer
from src.ops_analysis import analyze_heatmap, analyze_tags, calculate_response_times
from src.reporting import generate_report

# Set Plotly theme for dark mode
pio.templates.default = "plotly_dark"

# Page config
st.set_page_config(page_title="Análise SDR Dashboard", page_icon="📊", layout="wide", initial_sidebar_state="expanded")

# Custom CSS for dark theme
st.markdown(
    """
<style>
    /* Dark mode compatible metric cards */
    .stMetric {
        background: linear-gradient(135deg, #1e3a5f 0%, #2d1b4e 100%);
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #3d5a80;
    }

    /* Headers styling */
    h1, h2, h3 {
        color: #e0e0e0 !important;
    }

    /* Sidebar styling */
    .css-1d391kg {
        background-color: #1a1a2e;
    }

    /* Info box dark mode */
    .stAlert {
        background-color: #1e3a5f;
        border: 1px solid #3d5a80;
    }

    /* Divider color */
    hr {
        border-color: #3d5a80;
    }
</style>
""",
    unsafe_allow_html=True,
)


# Dark mode color palette for charts
COLORS = {
    "primary": "#6366f1",  # Indigo
    "secondary": "#8b5cf6",  # Violet
    "success": "#22c55e",  # Green
    "warning": "#f59e0b",  # Amber
    "danger": "#ef4444",  # Red
    "info": "#06b6d4",  # Cyan
    "gradient": ["#6366f1", "#8b5cf6", "#a855f7", "#d946ef"],  # Purple gradient
}

# Title
st.title("📊 Dashboard de Análise SDR")
st.markdown("---")

# Sidebar
st.sidebar.header("⚙️ Configurações")
data_source = st.sidebar.selectbox("Fonte de Dados", ["data/raw/mock_dashboard_data.json", "data/raw/exemplo.json"])


# Load data
@st.cache_data
def load_data(file_path: str):
    """Load and process the chat data."""
    chats = load_chats_from_json(file_path)
    return chats


@st.cache_data
def run_analysis(_chats):
    """Run the full analysis pipeline."""
    llm_analyzer = LLMAnalyzer()
    processed_data = []

    for chat in _chats:
        ops_metrics = calculate_response_times(chat)
        # Run async in sync context
        llm_results = asyncio.run(llm_analyzer.analyze_chat(chat))

        processed_data.append(
            {
                "chat_id": chat.id,
                "agent_name": chat.agent.name if chat.agent else "Unknown",
                "contact_name": chat.contact.name,
                "ops_metrics": ops_metrics,
                "llm_results": llm_results,
            }
        )

    # Quantitative Analysis
    heatmap_data = analyze_heatmap(_chats)
    tags_data = analyze_tags(_chats)

    report = generate_report(processed_data)
    return processed_data, report, heatmap_data, tags_data


# Load and process
with st.spinner("Carregando dados..."):
    chats = load_data(data_source)
    processed_data, report, heatmap_data, tags_data = run_analysis(chats)

# === METRICS ROW ===
st.header("📈 Métricas Gerais")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(label="Total de Chats", value=len(chats), delta=None)

with col2:
    avg_tme = sum(d["ops_metrics"]["tme_seconds"] for d in processed_data) / len(processed_data)
    st.metric(label="TME Médio", value=f"{avg_tme:.1f}s", delta=None, help="Tempo Médio de Espera")

with col3:
    avg_tma = sum(d["ops_metrics"]["tma_seconds"] for d in processed_data) / len(processed_data)
    st.metric(label="TMA Médio", value=f"{avg_tma / 60:.1f} min", delta=None, help="Tempo Médio de Atendimento")

with col4:
    conversion_rate = report["sales_funnel"].get("converted", 0) / len(chats) * 100
    st.metric(label="Taxa de Conversão", value=f"{conversion_rate:.1f}%", delta=None)

st.markdown("---")

# === QUANTITATIVE ANALYSIS ===
st.header("📊 Análise Quantitativa")

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Mapa de Calor de Mensagens")
    # Prepare heatmap data
    heatmap_rows = []
    days_map = {"0": "Seg", "1": "Ter", "2": "Qua", "3": "Qui", "4": "Sex", "5": "Sáb", "6": "Dom"}
    for day_key, hours in heatmap_data.items():
        for hour, count in hours.items():
            heatmap_rows.append({"Dia": days_map.get(day_key, day_key), "Hora": hour, "Mensagens": count})

    if heatmap_rows:
        df_heatmap = pd.DataFrame(heatmap_rows)
        # Pivot for heatmap matrix
        heatmap_matrix = df_heatmap.pivot(index="Dia", columns="Hora", values="Mensagens")
        # Ensure correct order of days
        ordered_days = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
        heatmap_matrix = heatmap_matrix.reindex(ordered_days)

        fig = px.imshow(
            heatmap_matrix,
            labels=dict(x="Hora do Dia", y="Dia da Semana", color="Volume"),
            x=list(range(24)),
            y=ordered_days,
            color_continuous_scale="Viridis",
        )
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, width="stretch")
    else:
        st.info("Sem dados suficientes para o mapa de calor.")

with col2:
    st.subheader("Tags Mais Frequentes")
    if tags_data:
        df_tags = pd.DataFrame(list(tags_data.items()), columns=["Tag", "Frequência"])
        df_tags = df_tags.sort_values("Frequência", ascending=True)  # Sort for horizontal bar

        fig = px.bar(
            df_tags,
            x="Frequência",
            y="Tag",
            orientation="h",
            title="Top Tags",
            color="Frequência",
            color_continuous_scale="Plasma",
        )
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, width="stretch")
    else:
        st.info("Nenhuma tag encontrada.")

st.markdown("---")

# === AGENT RANKING ===
st.header("🏆 Ranking de Agentes")

if report["agent_ranking"]:
    df_agents = pd.DataFrame(report["agent_ranking"])
    df_agents["avg_tme_formatted"] = df_agents["avg_tme"].apply(lambda x: f"{x:.1f}s")
    df_agents["avg_tma_formatted"] = df_agents["avg_tma"].apply(lambda x: f"{x / 60:.1f} min")

    col1, col2 = st.columns([2, 1])

    with col1:
        fig = px.bar(
            df_agents.head(10),
            x="agent",
            y="avg_tme",
            title="Top 10 Agentes por Tempo de Resposta (TME)",
            labels={"agent": "Agente", "avg_tme": "TME (segundos)"},
            color="avg_humanization",
            color_continuous_scale="Viridis",
        )
        fig.update_layout(xaxis_tickangle=-45, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, width="stretch")

    with col2:
        st.dataframe(
            df_agents[["agent", "chats", "avg_tme_formatted", "avg_humanization"]].rename(
                columns={
                    "agent": "Agente",
                    "chats": "Chats",
                    "avg_tme_formatted": "TME",
                    "avg_humanization": "Humanização",
                }
            ),
            hide_index=True,
            width="stretch",
        )

st.markdown("---")

# === PRODUCT CLOUD ===
st.header("🔥 Produtos Mais Mencionados (Top of Mind)")

if report["product_cloud"]:
    col1, col2 = st.columns([1, 1])

    with col1:
        products = [p[0] for p in report["product_cloud"]]
        counts = [p[1] for p in report["product_cloud"]]

        fig = px.pie(values=counts, names=products, title="Distribuição de Produtos", hole=0.4)
        st.plotly_chart(fig, width="stretch")

    with col2:
        fig = px.bar(
            x=products[:10],
            y=counts[:10],
            title="Top 10 Produtos",
            labels={"x": "Produto", "y": "Menções"},
            color=counts[:10],
            color_continuous_scale="Plasma",
        )
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, width="stretch")

st.markdown("---")

# === QUALITATIVE ANALYSIS (IA) ===
st.header("🧠 Análise Qualitativa (IA)")

col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("Sentimento")
    sentiments = [d["llm_results"]["cx"]["sentiment"] for d in processed_data]
    sentiment_counts = pd.Series(sentiments).value_counts()

    fig = px.pie(
        values=sentiment_counts.values,
        names=sentiment_counts.index,
        title="Distribuição de Sentimento",
        hole=0.4,
        color_discrete_map={"positive": COLORS["success"], "neutral": COLORS["info"], "negative": COLORS["danger"]},
    )
    st.plotly_chart(fig, width="stretch")

with col2:
    st.subheader("NPS Preditivo (IA)")
    nps_scores = [d["llm_results"]["cx"].get("nps_prediction", 0) for d in processed_data]
    avg_nps = sum(nps_scores) / len(nps_scores) if nps_scores else 0

    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=avg_nps,
            domain={"x": [0, 1], "y": [0, 1]},
            title={"text": "Média NPS"},
            gauge={
                "axis": {"range": [0, 10]},
                "bar": {"color": COLORS["primary"]},
                "steps": [
                    {"range": [0, 6], "color": "#333"},
                    {"range": [6, 8], "color": "#555"},
                    {"range": [8, 10], "color": "#777"},
                ],
            },
        )
    )
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig, width="stretch")

with col3:
    st.subheader("Estágio do Funil")
    stages = [d["llm_results"]["sales"].get("funnel_stage", "unknown") for d in processed_data]
    stage_counts = pd.Series(stages).value_counts()

    fig = px.bar(
        x=stage_counts.index,
        y=stage_counts.values,
        title="Distribuição do Funil",
        labels={"x": "Estágio", "y": "Chats"},
        color=stage_counts.values,
        color_continuous_scale="Viridis",
    )
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig, width="stretch")

st.markdown("---")

# === SALES FUNNEL ===
st.header("📊 Funil de Vendas")

col1, col2 = st.columns([1, 1])

with col1:
    funnel_data = report["sales_funnel"]
    stages = list(funnel_data.keys())
    values = list(funnel_data.values())

    # Translate stages
    stage_labels = {"converted": "✅ Convertido", "lost": "❌ Perdido", "in_progress": "⏳ Em Progresso"}
    stages_pt = [stage_labels.get(s, s) for s in stages]

    fig = go.Figure(
        go.Funnel(
            y=stages_pt,
            x=values,
            textinfo="value+percent initial",
            marker={"color": [COLORS["success"], COLORS["danger"], COLORS["warning"]][: len(stages)]},
        )
    )
    fig.update_layout(title="Status das Conversas", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig, width="stretch")

with col2:
    st.subheader("Motivos de Perda")
    loss_reasons = report.get("loss_reasons", {})

    if loss_reasons:
        reasons = list(loss_reasons.keys())
        counts = list(loss_reasons.values())

        fig = px.bar(
            x=reasons,
            y=counts,
            title="Distribuição de Motivos",
            labels={"x": "Motivo", "y": "Quantidade"},
            color=counts,
            color_continuous_scale="Reds",
        )
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, width="stretch")
    else:
        st.info("Nenhum motivo de perda registrado.")

# === FOOTER ===
st.markdown("---")
st.caption("📌 Dashboard de Análise SDR | Desenvolvido com Streamlit")
