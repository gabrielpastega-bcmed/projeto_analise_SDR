"""
Página: Health Check
Status do sistema e suas dependências.
"""

import streamlit as st

from src.auth.auth_manager import AuthManager
from src.dashboard_utils import apply_custom_css, render_user_sidebar
from src.observability.health import get_health_status

st.set_page_config(page_title="Health Check", page_icon="🏥", layout="wide")

# Require authentication (optional - pode ser público para monitoramento)
AuthManager.require_auth()

# Setup
apply_custom_css()
render_user_sidebar()

st.title("🏥 System Health Check")
st.markdown("Status do sistema e suas dependências")
st.markdown("---")

# Get health status
status = get_health_status()

# Overall status with color
overall_status = status["status"]
status_colors = {
    "healthy": "🟢",
    "degraded": "🟡",
    "unhealthy": "🔴",
}

status_messages = {
    "healthy": "Todos os sistemas operacionais",
    "degraded": "Alguns componentes com problemas",
    "unhealthy": "Sistema crítico indisponível",
}

st.header(f"{status_colors.get(overall_status, '⚪')} Status: {overall_status.upper()}")
st.caption(status_messages.get(overall_status, "Status desconhecido"))
st.caption(f"Última verificação: {status['timestamp']}")

st.markdown("---")

# Component statuses
st.subheader("📊 Componentes")

components = status.get("components", {})

for component_name, component_status in components.items():
    with st.container():
        col1, col2, col3, col4 = st.columns([3, 2, 2, 5])

        component_display_names = {
            "postgres": "PostgreSQL (Auth)",
            "bigquery": "BigQuery (Analytics)",
            "gemini_api": "Gemini API (LLM)",
        }

        with col1:
            st.markdown(f"**{component_display_names.get(component_name, component_name)}**")

        with col2:
            status_val = component_status.get("status", "unknown")
            if status_val == "healthy":
                st.success("✅ Healthy")
            elif status_val == "degraded":
                st.warning("⚠️ Degraded")
            elif status_val == "unhealthy":
                st.error("🔴 Unhealthy")
            elif status_val == "not_configured":
                st.info("ℹ️ Not Configured")
            else:
                st.info(f"ℹ️ {status_val.title()}")

        with col3:
            latency = component_status.get("latency_ms")
            if latency is not None:
                if latency < 100:
                    st.success(f"{latency}ms")
                elif latency < 500:
                    st.warning(f"{latency}ms")
                else:
                    st.error(f"{latency}ms")
            else:
                st.text("-")

        with col4:
            error = component_status.get("error")
            if error:
                with st.expander("Ver Erro"):
                    st.code(error, language="text")

        st.markdown("---")

# Actions
st.subheader("🔧 Ações")

col1, col2 = st.columns(2)
with col1:
    if st.button("🔄 Recarregar Status", use_container_width=True):
        st.rerun()

with col2:
    if st.button("📊 Ver Métricas", use_container_width=True):
        st.info("Métricas detalhadas serão implementadas em breve")

# Tips
with st.expander("💡 Troubleshooting"):
    st.markdown(
        """
    ### PostgreSQL Unhealthy
    - Verificar se o serviço está rodando
    - Validar credenciais no `.env`
    - Verificar conexão de rede

    ### BigQuery Unhealthy
    - Verificar GOOGLE_APPLICATION_CREDENTIALS
    - Validar permissões do service account
    - Confirmar projeto/dataset/tabela existem

    ### Gemini API Issues
    - Verificar GEMINI_API_KEY no `.env`
    - Confirmar quota da API não esgotada
    """
    )

# Footer
st.markdown("---")
st.caption("🏥 Health Check • Atualizado automaticamente a cada requisição")
