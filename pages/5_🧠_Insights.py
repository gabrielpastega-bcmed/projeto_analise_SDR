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
                    st.success(f"✅ Análise concluída! {len(results)} chats processados e salvos no BigQuery.")
                    st.rerun()
                else:
                    # Salva apenas localmente e exibe resultados na tela
                    analyzer.save_results(results)
                    st.success(
                        f"✅ Análise de teste concluída! {len(results)} chats processados (não salvo no BigQuery)."
                    )

                    # Armazenar em session_state para exibir abaixo
                    st.session_state["test_results"] = results

# ================================================================
# CARREGAR ANÁLISE LOCAL
# ================================================================

st.markdown("---")
with st.expander("📂 Carregar Análise Local", expanded=False):
    st.info("Carregue uma análise previamente salva em `data/analysis_results/`")

    import json
    from pathlib import Path

    results_dir = Path("data/analysis_results")
    if results_dir.exists():
        json_files = sorted(results_dir.glob("analysis_*.json"), reverse=True)

        if json_files:
            file_options = {f.name: f for f in json_files[:10]}  # Últimos 10
            selected_file = st.selectbox(
                "Selecione o arquivo de análise:",
                options=list(file_options.keys()),
            )

            if st.button("📥 Carregar Análise", type="primary"):
                try:
                    with open(file_options[selected_file], encoding="utf-8") as f:
                        loaded_results = json.load(f)
                    st.session_state["test_results"] = loaded_results
                    st.success(f"✅ Carregados {len(loaded_results)} resultados de `{selected_file}`")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao carregar: {e}")
        else:
            st.warning("Nenhum arquivo de análise encontrado em `data/analysis_results/`")
    else:
        st.warning("Diretório `data/analysis_results/` não existe.")

# ================================================================
# EXIBIÇÃO DE RESULTADOS DE TESTE / LOCAL
# ================================================================

if "test_results" in st.session_state and st.session_state["test_results"]:
    test_results = st.session_state["test_results"]

    st.markdown("---")
    st.subheader("🧪 Resultados da Análise")

    # Função para agregar resultados (compatível com formato local)
    def aggregate_local_results(results):
        """Agrega resultados locais para exibição."""
        if not results:
            return None

        total = len(results)

        # Sentimentos
        sentiments = {"positivo": 0, "neutro": 0, "negativo": 0}
        nps_scores = []
        humanization_scores = []
        outcomes = {"convertido": 0, "perdido": 0, "em andamento": 0}

        for r in results:
            # Suporta formato aninhado { analysis: { cx, sales } } ou direto { cx, sales }
            analysis = r.get("analysis", r)
            cx = analysis.get("cx", r.get("cx", {}))
            sales = analysis.get("sales", r.get("sales", {}))

            # CX
            s = cx.get("sentiment") or r.get("cx_sentiment", "neutro")
            if s and s.lower() in sentiments:
                sentiments[s.lower()] += 1

            nps = cx.get("nps_prediction") or r.get("cx_nps_prediction")
            if nps:
                nps_scores.append(float(nps))

            hum = cx.get("humanization_score") or r.get("cx_humanization_score")
            if hum:
                humanization_scores.append(float(hum))

            # Sales
            o = sales.get("outcome") or r.get("sales_outcome", "em andamento")
            if o and o.lower() in outcomes:
                outcomes[o.lower()] += 1

        return {
            "total_analyzed": total,
            "cx": {
                "sentiment_distribution": sentiments,
                "avg_nps_prediction": sum(nps_scores) / len(nps_scores) if nps_scores else 0,
                "avg_humanization_score": sum(humanization_scores) / len(humanization_scores)
                if humanization_scores
                else 0,
            },
            "sales": {
                "outcome_distribution": outcomes,
                "conversion_rate": outcomes["convertido"] / total * 100 if total else 0,
            },
        }

    test_aggregated = aggregate_local_results(test_results)

    if test_aggregated:
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Chats Analisados", f"{test_aggregated['total_analyzed']:,}")
        col2.metric("NPS Médio", f"{test_aggregated['cx']['avg_nps_prediction']:.1f}/10")
        col3.metric("Humanização", f"{test_aggregated['cx']['avg_humanization_score']:.1f}/5")
        col4.metric("Taxa de Conversão", f"{test_aggregated['sales']['conversion_rate']:.1f}%")

        # Gráficos agregados
        import pandas as pd
        import plotly.express as px

        col_left, col_right = st.columns(2)

        with col_left:
            st.markdown("**😊 Distribuição de Sentimento**")
            sentiment_data = test_aggregated["cx"]["sentiment_distribution"]
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
            st.plotly_chart(fig_sentiment, use_container_width=True)

        with col_right:
            st.markdown("**📈 Resultados de Vendas**")
            outcome_data = test_aggregated["sales"]["outcome_distribution"]
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
            st.plotly_chart(fig_outcome, use_container_width=True)

    st.markdown("---")

    # ================================================================
    # VISUALIZAÇÃO LADO-A-LADO: CHAT + ANÁLISE
    # ================================================================

    st.subheader("🔍 Comparar Chat vs Análise")

    # Seletor de chat
    chat_options = {
        f"{r.get('chat_id', 'N/A')} - {r.get('agent') or r.get('agent_name', 'N/A')}": idx
        for idx, r in enumerate(test_results)
    }

    selected_chat_label = st.selectbox("Selecione um chat para visualizar:", options=list(chat_options.keys()))

    selected_idx = chat_options[selected_chat_label]
    selected_result = test_results[selected_idx]

    col_chat, col_analysis = st.columns(2)

    # Coluna da esquerda: Transcrição do Chat
    with col_chat:
        st.markdown("### 💬 Transcrição do Chat")

        transcript = selected_result.get("transcript")
        if transcript:
            # Exibir transcrição formatada
            st.text_area(
                "Conversa",
                value=transcript,
                height=400,
                disabled=True,
                label_visibility="collapsed",
            )
        else:
            # Tentar carregar do BigQuery se não tiver transcrição salva
            chat_id = selected_result.get("chat_id")
            if chat_id:
                st.info(f"Transcrição não salva. Carregando chat `{chat_id}` do BigQuery...")
                try:
                    from src.ingestion import load_chats_from_bigquery

                    # Buscar chat específico (últimos 30 dias)
                    chats = load_chats_from_bigquery(days=30, limit=500, lightweight=False)
                    chat_match = [c for c in chats if c.id == chat_id]

                    if chat_match:
                        chat = chat_match[0]
                        messages_text = []
                        for msg in chat.messages or []:
                            # Determinar tipo de remetente usando sentBy.type
                            sender_type = msg.sentBy.type if msg.sentBy else None
                            sender_name = msg.sentBy.name if msg.sentBy and msg.sentBy.name else ""

                            if sender_type == "bot":
                                sender = "🤖 Bot"
                            elif sender_type == "agent":
                                sender = f"👤 {sender_name}" if sender_name else "👤 Agente"
                            else:
                                sender = f"📱 {sender_name}" if sender_name else "📱 Cliente"
                            messages_text.append(f"[{sender}]: {msg.body}")

                        transcript_loaded = "\n\n".join(messages_text)
                        st.text_area(
                            "Conversa",
                            value=transcript_loaded,
                            height=400,
                            disabled=True,
                            label_visibility="collapsed",
                        )
                    else:
                        st.warning("Chat não encontrado no BigQuery.")
                except Exception as e:
                    st.error(f"Erro ao carregar chat: {e}")
            else:
                st.warning("ID do chat não disponível.")

    # Coluna da direita: Análise da LLM
    with col_analysis:
        st.markdown("### 🧠 Análise da IA")

        # Tabs para cada tipo de análise
        tab_cx, tab_sales, tab_product, tab_qa = st.tabs(["😊 CX", "📈 Vendas", "📦 Produto", "✅ QA"])

        # Suporta formato aninhado { analysis: {...} } ou direto { cx, sales... }
        analysis = selected_result.get("analysis", selected_result)
        cx = analysis.get("cx", {})
        sales = analysis.get("sales", {})
        product = analysis.get("product", {})
        qa = analysis.get("qa", {})

        with tab_cx:
            st.metric("Sentimento", cx.get("sentiment", "N/A"))
            st.metric("NPS Previsto", f"{cx.get('nps_prediction', 'N/A')}/10")
            st.metric("Humanização", f"{cx.get('humanization_score', 'N/A')}/5")
            st.write(f"**Status:** {cx.get('resolution_status', 'N/A')}")
            if cx.get("satisfaction_comment"):
                st.info(f"💬 {cx.get('satisfaction_comment')}")

        with tab_sales:
            st.metric("Estágio do Funil", sales.get("funnel_stage", "N/A"))
            st.metric("Resultado", sales.get("outcome", "N/A"))
            if sales.get("rejection_reason"):
                st.warning(f"❌ Motivo de perda: {sales.get('rejection_reason')}")
            if sales.get("next_step"):
                st.info(f"➡️ Próximo passo: {sales.get('next_step')}")

        with tab_product:
            products = product.get("products_mentioned", [])
            if products:
                st.write("**Produtos mencionados:**")
                for p in products:
                    st.markdown(f"- {p}")
            else:
                st.write("Nenhum produto identificado.")

            st.metric("Nível de Interesse", product.get("interest_level", "N/A"))

            trends = product.get("trends", [])
            if trends:
                st.write("**Tendências:**")
                for t in trends:
                    st.markdown(f"- {t}")

        with tab_qa:
            adherence = qa.get("script_adherence")
            st.metric("Aderência ao Script", "✅ Sim" if adherence else "❌ Não")

            questions = qa.get("key_questions_asked", [])
            if questions:
                st.write("**Perguntas-chave feitas:**")
                for q in questions:
                    st.markdown(f"- {q}")

            improvements = qa.get("improvement_areas", [])
            if improvements:
                st.write("**Áreas de melhoria:**")
                for i in improvements:
                    st.markdown(f"- {i}")

    if st.button("🗑️ Limpar Resultados"):
        del st.session_state["test_results"]
        st.rerun()
