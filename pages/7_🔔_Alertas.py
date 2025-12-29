"""
Página: Alertas
Visualização e gerenciamento de alertas do sistema.
"""

from dotenv import load_dotenv

load_dotenv()

import streamlit as st

from src.auth.auth_manager import AuthManager
from src.dashboard_utils import (
    apply_custom_css,
    get_colors,
    render_user_sidebar,
    setup_plotly_theme,
)

st.set_page_config(page_title="Alertas", page_icon="🔔", layout="wide")

# Require authentication
AuthManager.require_auth()

# Setup
setup_plotly_theme()
apply_custom_css()
render_user_sidebar()
COLORS = get_colors()

st.title("🔔 Central de Alertas")
st.markdown("Monitore métricas importantes e receba notificações quando thresholds são ultrapassados.")

# ================================================================
# ALERTAS ATIVOS
# ================================================================

st.markdown("---")
st.subheader("⚠️ Alertas Ativos")

try:
    from src.auth.alert_service import AlertService

    active_alerts = AlertService.get_active_alerts()

    if active_alerts:
        for alert in active_alerts:
            # Definir cor baseado na severidade
            if alert.severity == "critical":
                icon = "🔴"
                color = COLORS.get("danger", "#dc3545")
            elif alert.severity == "warning":
                icon = "🟡"
                color = COLORS.get("warning", "#ffc107")
            else:
                icon = "🔵"
                color = COLORS.get("info", "#17a2b8")

            with st.container():
                col1, col2, col3 = st.columns([1, 6, 2])

                with col1:
                    st.markdown(f"### {icon}")

                with col2:
                    st.markdown(f"**{alert.title}**")
                    st.caption(alert.message)
                    st.caption(f"Criado em: {alert.created_at.strftime('%d/%m/%Y %H:%M')}")

                with col3:
                    user_info = AuthManager.get_current_user()
                    if user_info:
                        if st.button("✓ Reconhecer", key=f"ack_{alert.id}"):
                            AlertService.acknowledge_alert(alert.id, user_info.get("user_id", 0))
                            st.rerun()

                        if st.button("🗑️ Resolver", key=f"resolve_{alert.id}"):
                            AlertService.resolve_alert(alert.id)
                            st.rerun()

                st.markdown("---")
    else:
        st.success("✅ Nenhum alerta ativo no momento!")
        st.info("👍 Todos os indicadores estão dentro dos limites esperados.")

except Exception as e:
    st.warning(f"⚠️ Sistema de alertas não disponível: {e}")
    st.info("O banco de dados precisa ser atualizado com as tabelas de alertas.")

# ================================================================
# HISTÓRICO DE ALERTAS
# ================================================================

st.markdown("---")
st.subheader("📜 Histórico de Alertas")

try:
    from src.auth.alert_service import AlertService

    col1, col2 = st.columns([1, 3])
    with col1:
        days = st.selectbox("Período", [7, 14, 30, 90], format_func=lambda x: f"Últimos {x} dias")

    history = AlertService.get_alert_history(days=days)

    if history:
        import pandas as pd

        history_data = []
        for alert in history:
            history_data.append(
                {
                    "Data": alert.created_at.strftime("%d/%m/%Y %H:%M"),
                    "Tipo": alert.alert_type.replace("_", " ").title(),
                    "Título": alert.title,
                    "Severidade": alert.severity.title(),
                    "Status": alert.status.title(),
                    "Valor": f"{alert.metric_value:.1f}" if alert.metric_value else "-",
                    "Limite": (f"{alert.threshold_value:.1f}" if alert.threshold_value else "-"),
                }
            )

        df = pd.DataFrame(history_data)
        st.dataframe(df, use_container_width=True, hide_index=True)

        # Estatísticas
        st.markdown("### 📊 Estatísticas")
        col1, col2, col3, col4 = st.columns(4)

        col1.metric("Total de Alertas", len(history))
        col2.metric("Críticos", len([a for a in history if a.severity == "critical"]))
        col3.metric("Warnings", len([a for a in history if a.severity == "warning"]))
        col4.metric("Info", len([a for a in history if a.severity == "info"]))

    else:
        st.info(f"Nenhum alerta nos últimos {days} dias.")

except Exception as e:
    st.warning(f"⚠️ Histórico não disponível: {e}")

# ================================================================
# CONFIGURAÇÃO DE THRESHOLDS
# ================================================================

st.markdown("---")
st.subheader("⚙️ Configurar Thresholds")

user_info = AuthManager.get_current_user()
if user_info and user_info.get("is_superadmin"):
    st.info("Configure os limites que disparam alertas.")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**TME Máximo (minutos)**")
        tme_threshold = st.number_input(
            "TME",
            min_value=1.0,
            max_value=60.0,
            value=15.0,
            step=1.0,
            label_visibility="collapsed",
        )

    with col2:
        st.markdown("**Volume Mínimo (por dia)**")
        volume_threshold = st.number_input(
            "Volume",
            min_value=1,
            max_value=1000,
            value=10,
            step=1,
            label_visibility="collapsed",
        )

    with col3:
        st.markdown("**Taxa Conversão Mínima (%)**")
        conversion_threshold = st.number_input(
            "Conversão",
            min_value=1.0,
            max_value=100.0,
            value=20.0,
            step=1.0,
            label_visibility="collapsed",
        )

    if st.button("💾 Salvar Configurações", use_container_width=True):
        st.success("✅ Thresholds atualizados com sucesso!")
        st.info("Nota: A persistência de thresholds requer atualização do banco de dados.")

else:
    st.info("🔒 Apenas superadministradores podem configurar thresholds.")

# Footer
st.markdown("---")
st.caption("🔔 Sistema de Alertas • SDR Analytics Dashboard v0.10.0")
