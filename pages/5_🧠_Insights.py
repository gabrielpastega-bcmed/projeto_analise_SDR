"""
Página: Insights Qualitativos
Análise qualitativa de conversas usando IA (Google Gemini).
Consulta resultados armazenados no BigQuery - sem chamar LLM na visualização.
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
st.markdown("Análise semanal de conversas com **Google Gemini**")
st.markdown("---")


# ================================================================
# SELETOR DE SEMANA
# ================================================================


def load_available_weeks():
    """Carrega as semanas disponíveis do BigQuery."""
    try:
        from src.batch_analyzer import BatchAnalyzer

        analyzer = BatchAnalyzer()
        return analyzer.get_available_weeks()
    except Exception as e:
        st.error(f"Erro ao carregar semanas: {e}")
        return []


def load_week_results(week_start):
    """Carrega resultados de uma semana específica."""
    try:
        from src.batch_analyzer import BatchAnalyzer

        analyzer = BatchAnalyzer()
        return analyzer.load_from_bigquery(week_start)
    except Exception as e:
        st.error(f"Erro ao carregar resultados: {e}")
        return []


def aggregate_bigquery_results(results):
    """Agrega resultados do BigQuery para exibição."""
    if not results:
        return None

    total = len(results)

    # Sentimentos
    sentiments = {"positivo": 0, "neutro": 0, "negativo": 0}
    for r in results:
        s = r.get("cx_sentiment", "neutro")
        if s in sentiments:
            sentiments[s] += 1

    # NPS e Humanização
    nps_scores = [r.get("cx_nps_prediction") for r in results if r.get("cx_nps_prediction")]
    humanization = [r.get("cx_humanization_score") for r in results if r.get("cx_humanization_score")]

    # Outcomes
    outcomes = {"convertido": 0, "perdido": 0, "em andamento": 0}
    for r in results:
        o = r.get("sales_outcome", "em andamento")
        if o in outcomes:
            outcomes[o] += 1

    # Produtos
    all_products = []
    for r in results:
        prods = r.get("products_mentioned") or []
        all_products.extend(prods)

    product_counts = {}
    for p in all_products:
        product_counts[p] = product_counts.get(p, 0) + 1
    top_products = sorted(product_counts.items(), key=lambda x: x[1], reverse=True)[:10]

    return {
        "total_analyzed": total,
        "cx": {
            "sentiment_distribution": sentiments,
            "avg_nps_prediction": sum(nps_scores) / len(nps_scores) if nps_scores else 0,
            "avg_humanization_score": sum(humanization) / len(humanization) if humanization else 0,
        },
        "sales": {
            "outcome_distribution": outcomes,
            "conversion_rate": outcomes["convertido"] / total * 100 if total else 0,
        },
        "product": {
            "top_products": top_products,
        },
    }


# Carregar semanas disponíveis
weeks = load_available_weeks()

if weeks:
    # Seletor de semana
    week_options = {
        f"Semana {w['week_start'].strftime('%d/%m')} - "
        f"{w['week_end'].strftime('%d/%m/%Y')} ({w['total_chats']} chats)": w
        for w in weeks
    }

    selected_label = st.selectbox(
        "📅 Selecionar Semana",
        options=list(week_options.keys()),
        help="Selecione a semana para visualizar os insights",
    )

    selected_week = week_options[selected_label]
    week_start = selected_week["week_start"]

    # Carregar dados da semana selecionada
    results = load_week_results(week_start)
    aggregated = aggregate_bigquery_results(results)

    if aggregated:
        st.markdown("---")

        # ================================================================
        # KPIs
        # ================================================================

        col1, col2, col3, col4 = st.columns(4)

        col1.metric("Chats Analisados", f"{aggregated['total_analyzed']:,}")
        col2.metric("NPS Médio", f"{aggregated['cx']['avg_nps_prediction']:.1f}/10")
        col3.metric("Humanização", f"{aggregated['cx']['avg_humanization_score']:.1f}/5")
        col4.metric("Taxa de Conversão", f"{aggregated['sales']['conversion_rate']:.1f}%")

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

            import pandas as pd
            import plotly.express as px

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
        if aggregated["product"]["top_products"]:
            st.markdown("---")
            st.subheader("🏆 Produtos Mais Mencionados")

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

        # Detalhes
        st.markdown("---")
        with st.expander("📋 Ver Análises Individuais"):
            for r in results[:20]:
                with st.container():
                    st.markdown(f"**Chat:** `{r['chat_id']}` | **Agente:** {r.get('agent_name', 'N/A')}")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Sentimento:** {r.get('cx_sentiment', 'N/A')}")
                        st.write(f"**NPS:** {r.get('cx_nps_prediction', 'N/A')}")
                    with col2:
                        st.write(f"**Outcome:** {r.get('sales_outcome', 'N/A')}")
                        st.write(f"**Estágio:** {r.get('sales_funnel_stage', 'N/A')}")
                    st.markdown("---")

else:
    st.info("📊 Nenhuma análise disponível ainda.")
    st.markdown("""
    ### Como começar?

    1. Execute o script de análise semanal:
    ```bash
    python scripts/run_weekly_analysis.py
    ```

    2. Ou aguarde a próxima execução automática (segundas-feiras).
    """)

# ================================================================
# EXECUTAR NOVA ANÁLISE (Admin)
# ================================================================

st.markdown("---")
with st.expander("🔧 Executar Nova Análise (Admin)"):
    st.warning("⚠️ Esta operação consome créditos do Gemini API.")

    from datetime import datetime, timedelta

    # Calcular semana anterior
    today = datetime.now()
    days_since_monday = today.weekday()
    this_monday = today - timedelta(days=days_since_monday)
    last_monday = this_monday - timedelta(days=7)
    last_sunday = this_monday - timedelta(days=1)

    st.write(f"**Semana a analisar:** {last_monday.strftime('%d/%m/%Y')} - {last_sunday.strftime('%d/%m/%Y')}")

    col1, col2 = st.columns(2)
    with col1:
        max_chats = st.number_input("Máximo de chats", min_value=10, max_value=500, value=100)
    with col2:
        save_to_bq = st.checkbox("Salvar no BigQuery", value=True)

    if st.button("🚀 Executar Análise", type="primary"):
        import os

        if not os.getenv("GEMINI_API_KEY"):
            st.error("GEMINI_API_KEY não configurada.")
        else:
            st.info("Carregando chats do BigQuery...")

            from src.batch_analyzer import BatchAnalyzer
            from src.ingestion import load_chats_from_bigquery

            # Carregar chats da semana
            chats = load_chats_from_bigquery(days=14, limit=max_chats, lightweight=False)
            chats_with_messages = [c for c in chats if c.messages]

            if not chats_with_messages:
                st.error("Nenhum chat com mensagens encontrado.")
            else:
                st.info(f"Analisando {len(chats_with_messages)} chats...")

                import asyncio

                analyzer = BatchAnalyzer()

                progress = st.progress(0)

                def update_progress(current, total):
                    progress.progress(current / total)

                async def run():
                    return await analyzer.run_batch(
                        chats_with_messages,
                        batch_size=5,
                        progress_callback=update_progress,
                    )

                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                results = loop.run_until_complete(run())

                if save_to_bq:
                    analyzer.save_to_bigquery(results, last_monday, last_sunday)

                analyzer.save_results(results)
                st.success(f"Análise concluída! {len(results)} chats processados.")
                st.rerun()
