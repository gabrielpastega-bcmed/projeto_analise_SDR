"""
Página: Insights Qualitativos
Análise qualitativa de conversas usando IA (Google Gemini).
"""

import streamlit as st

from src.dashboard_utils import (
    apply_chart_theme,
    apply_custom_css,
    get_colors,
    setup_plotly_theme,
)

st.set_page_config(page_title="Insights", page_icon="🧠", layout="wide")

# Setup
setup_plotly_theme()
apply_custom_css()
COLORS = get_colors()

st.title("🧠 Insights Qualitativos")
st.markdown("Análise de conversas com **Google Gemini** (processamento semanal)")
st.markdown("---")


# ================================================================
# VERIFICAR RESULTADOS EXISTENTES
# ================================================================


def load_analysis_results():
    """Carrega os resultados de análise mais recentes."""
    try:
        from src.batch_analyzer import BatchAnalyzer

        analyzer = BatchAnalyzer()
        results = analyzer.load_latest_results()
        if results:
            aggregated = analyzer.aggregate_results(results)
            return results, aggregated
    except Exception as e:
        st.error(f"Erro ao carregar resultados: {e}")
    return None, None


# Carregar resultados existentes
results, aggregated = load_analysis_results()

if aggregated and "error" not in aggregated:
    # ================================================================
    # KPIs DE ANÁLISE QUALITATIVA
    # ================================================================

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Chats Analisados",
        f"{aggregated['total_analyzed']:,}",
    )

    col2.metric(
        "NPS Médio",
        f"{aggregated['cx']['avg_nps_prediction']:.1f}/10",
    )

    col3.metric(
        "Humanização",
        f"{aggregated['cx']['avg_humanization_score']:.1f}/5",
    )

    col4.metric(
        "Taxa de Conversão",
        f"{aggregated['sales']['conversion_rate']:.1f}%",
    )

    st.markdown("---")

    # ================================================================
    # GRÁFICOS
    # ================================================================

    col_left, col_right = st.columns(2)

    # Distribuição de Sentimento
    with col_left:
        st.subheader("😊 Distribuição de Sentimento")

        import pandas as pd
        import plotly.express as px

        sentiment_data = aggregated["cx"]["sentiment_distribution"]
        df_sentiment = pd.DataFrame(
            [{"Sentimento": k.capitalize(), "Quantidade": v} for k, v in sentiment_data.items()]
        )

        fig_sentiment = px.pie(
            df_sentiment,
            values="Quantidade",
            names="Sentimento",
            color="Sentimento",
            color_discrete_map={
                "Positivo": COLORS["success"],
                "Neutro": COLORS["warning"],
                "Negativo": COLORS["danger"],
            },
            hole=0.4,
        )
        fig_sentiment = apply_chart_theme(fig_sentiment)
        st.plotly_chart(fig_sentiment, width="stretch")

    # Funil de Vendas
    with col_right:
        st.subheader("📈 Resultados de Vendas")

        outcome_data = aggregated["sales"]["outcome_distribution"]
        df_outcome = pd.DataFrame([{"Resultado": k.capitalize(), "Quantidade": v} for k, v in outcome_data.items()])

        fig_outcome = px.bar(
            df_outcome,
            x="Resultado",
            y="Quantidade",
            color="Resultado",
            color_discrete_map={
                "Convertido": COLORS["success"],
                "Perdido": COLORS["danger"],
                "Em andamento": COLORS["info"],
            },
        )
        fig_outcome = apply_chart_theme(fig_outcome)
        fig_outcome.update_layout(showlegend=False)
        st.plotly_chart(fig_outcome, width="stretch")

    # Top Produtos
    st.markdown("---")
    st.subheader("🏆 Produtos Mais Mencionados")

    if aggregated["product"]["top_products"]:
        df_products = pd.DataFrame(
            aggregated["product"]["top_products"],
            columns=["Produto", "Menções"],
        )

        fig_products = px.bar(
            df_products,
            x="Menções",
            y="Produto",
            orientation="h",
            color="Menções",
            color_continuous_scale=[[0, COLORS["info"]], [1, COLORS["primary"]]],
        )
        fig_products = apply_chart_theme(fig_products)
        fig_products.update_layout(showlegend=False, coloraxis_showscale=False)
        st.plotly_chart(fig_products, width="stretch")
    else:
        st.info("Nenhum produto mencionado nos chats analisados.")

else:
    st.info("📊 Nenhuma análise disponível. Execute a análise abaixo.")


# ================================================================
# EXECUTAR NOVA ANÁLISE
# ================================================================

st.markdown("---")
st.subheader("🔄 Executar Nova Análise")

# Verifica se tem dados carregados
if "chats" not in st.session_state or not st.session_state.chats:
    st.warning("⚠️ Carregue os dados na página principal antes de executar a análise.")
else:
    chats = st.session_state.chats

    # Filtrar apenas chats com mensagens
    chats_with_messages = [c for c in chats if c.messages]

    col1, col2 = st.columns([2, 1])

    with col1:
        num_chats = st.slider(
            "Número de chats a analisar",
            min_value=1,
            max_value=min(100, len(chats_with_messages)),
            value=min(10, len(chats_with_messages)),
            help="Quanto mais chats, maior o tempo e custo de processamento.",
        )

    with col2:
        st.metric("Chats disponíveis", len(chats_with_messages))

    if st.button("🚀 Executar Análise com Gemini", type="primary"):
        import os

        if not os.getenv("GEMINI_API_KEY"):
            st.error("❌ GEMINI_API_KEY não configurada. Adicione ao arquivo .env")
        else:
            import asyncio

            from src.batch_analyzer import BatchAnalyzer

            progress_bar = st.progress(0)
            status_text = st.empty()

            def update_progress(current, total):
                progress_bar.progress(current / total)
                status_text.text(f"Processando... {current}/{total}")

            async def run_analysis():
                analyzer = BatchAnalyzer()
                selected_chats = chats_with_messages[:num_chats]
                results = await analyzer.run_batch(
                    selected_chats,
                    batch_size=5,
                    progress_callback=update_progress,
                )
                analyzer.save_results(results)
                return results

            with st.spinner("Analisando chats com Gemini..."):
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    analysis_results = loop.run_until_complete(run_analysis())

                    st.success(f"✅ Análise concluída! {len(analysis_results)} chats processados.")
                    st.rerun()

                except Exception as e:
                    st.error(f"❌ Erro na análise: {e}")


# ================================================================
# DETALHES DOS RESULTADOS
# ================================================================

if results:
    st.markdown("---")
    with st.expander("📋 Ver Detalhes das Análises Individuais"):
        for r in results[:10]:  # Mostra apenas os 10 primeiros
            if "error" in r:
                st.error(f"❌ Chat {r.get('chat_id', 'N/A')}: {r['error']}")
            else:
                with st.container():
                    st.markdown(f"**Chat:** `{r['chat_id']}` | **Agente:** {r.get('agent', 'N/A')}")
                    if "analysis" in r:
                        col1, col2 = st.columns(2)
                        with col1:
                            st.json(r["analysis"].get("cx", {}))
                        with col2:
                            st.json(r["analysis"].get("sales", {}))
                    st.markdown("---")
