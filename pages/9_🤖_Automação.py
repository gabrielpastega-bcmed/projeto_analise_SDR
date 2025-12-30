"""
Página de Automação - Monitoramento de GitHub Actions.

Exibe status e histórico das execuções automatizadas de análise.
"""

from datetime import datetime, timedelta

import requests
import streamlit as st

from src.auth.auth_manager import AuthManager

# Configuração da página
st.set_page_config(page_title="Automação", page_icon="🤖", layout="wide")

# Verificar autenticação
if not AuthManager.is_authenticated():
    st.warning("⚠️ Você precisa fazer login para acessar esta página.")
    st.stop()

# Configurações do repositório
REPO_OWNER = "gabrielpastega-bcmed"
REPO_NAME = "projeto_analise_SDR"
WORKFLOWS = {
    "weekly": "weekly_analysis.yml",
    "manual": "manual_analysis.yml",
    "monitoring": "monitoring.yml",
}

# Header
st.title("🤖 Automação de Análises")
st.markdown("Monitoramento das execuções automatizadas via GitHub Actions")

# ========================================
# Funções de API
# ========================================


@st.cache_data(ttl=300)  # Cache por 5 minutos
def get_workflow_runs(workflow_name: str, limit: int = 30) -> list:
    """Busca últimas execuções de um workflow específico."""
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/actions/workflows/{workflow_name}/runs"
    headers = {"Accept": "application/vnd.github+json"}

    try:
        response = requests.get(url, headers=headers, params={"per_page": limit}, timeout=10)
        if response.status_code == 200:
            return response.json().get("workflow_runs", [])
        else:
            st.error(f"Erro ao buscar dados: HTTP {response.status_code}")
            return []
    except Exception as e:
        st.error(f"Erro ao conectar com GitHub API: {e}")
        return []


def format_duration(start: str, end: str) -> str:
    """Calcula duração entre dois timestamps ISO."""
    try:
        start_dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
        end_dt = datetime.fromisoformat(end.replace("Z", "+00:00"))
        duration = (end_dt - start_dt).total_seconds()
        return f"{duration / 60:.1f} min"
    except Exception:
        return "N/A"


def format_timestamp(timestamp: str) -> str:
    """Formata timestamp ISO para formato brasileiro."""
    try:
        dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        # Converter para BRT (UTC-3)
        dt_brt = dt - timedelta(hours=3)
        return dt_brt.strftime("%d/%m/%Y %H:%M")
    except Exception:
        return timestamp


def get_status_emoji(status: str) -> str:
    """Retorna emoji baseado no status."""
    status_map = {
        "success": "✅",
        "failure": "❌",
        "cancelled": "⚠️",
        "in_progress": "🔄",
        "queued": "⏳",
    }
    return status_map.get(status, "❓")


# ========================================
# Status Card - Última Execução Semanal
# ========================================

st.subheader("📊 Status Atual")

weekly_runs = get_workflow_runs(WORKFLOWS["weekly"], limit=1)

if weekly_runs:
    last_run = weekly_runs[0]

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        status = last_run.get("conclusion") or "in_progress"
        status_emoji = get_status_emoji(status)
        status_text = "Em execução" if status == "in_progress" else status.title()

        if status == "success":
            st.metric("Status", f"{status_emoji} Sucesso", delta="Última execução")
        elif status == "failure":
            st.metric(
                "Status",
                f"{status_emoji} Falha",
                delta="Requer atenção",
                delta_color="inverse",
            )
        else:
            st.metric("Status", f"{status_emoji} {status_text}")

    with col2:
        created = last_run["created_at"]
        st.metric("Última Execução", format_timestamp(created))

    with col3:
        if last_run.get("updated_at"):
            duration = format_duration(last_run["created_at"], last_run["updated_at"])
            st.metric("Duração", duration)
        else:
            st.metric("Duração", "Em andamento...")

    with col4:
        st.link_button("📋 Ver Logs", last_run["html_url"], use_container_width=True)

    # Detalhes adicionais
    with st.expander("ℹ️ Mais Informações"):
        col_a, col_b = st.columns(2)

        with col_a:
            st.write(f"**Run ID:** #{last_run['run_number']}")
            st.write(f"**Branch:** {last_run['head_branch']}")
            st.write(f"**Trigger:** {last_run['event']}")

        with col_b:
            st.write(f"**Commit:** `{last_run['head_sha'][:7]}`")
            st.write(f"**Actor:** @{last_run['triggering_actor']['login']}")

else:
    st.info("📭 Nenhuma execução automática encontrada ainda.")

st.divider()

# ========================================
# Histórico de Execuções
# ========================================

st.subheader("📜 Histórico de Execuções")

# Tabs para diferentes workflows
tab1, tab2, tab3 = st.tabs(["🗓️ Semanal", "⚡ Manual", "📊 Monitoring"])

with tab1:
    st.caption("Execuções automáticas (toda segunda-feira 6AM UTC)")

    runs = get_workflow_runs(WORKFLOWS["weekly"], limit=30)

    if runs:
        # Preparar dados para tabela
        table_data = []
        for run in runs:
            table_data.append(
                {
                    "Status": get_status_emoji(run.get("conclusion") or "in_progress"),
                    "Data/Hora": format_timestamp(run["created_at"]),
                    "Duração": format_duration(run["created_at"], run.get("updated_at", run["created_at"])),
                    "Trigger": run["event"],
                    "Run": f"#{run['run_number']}",
                    "Logs": run["html_url"],
                }
            )

        st.dataframe(
            table_data,
            use_container_width=True,
            column_config={
                "Logs": st.column_config.LinkColumn("Logs", display_text="Ver"),
            },
            hide_index=True,
        )

        # Estatísticas
        success_count = sum(1 for r in runs if r.get("conclusion") == "success")
        total = len(runs)

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total de Runs", total)
        with col2:
            st.metric("Sucessos", success_count)
        with col3:
            success_rate = (success_count / total * 100) if total > 0 else 0
            st.metric("Taxa de Sucesso", f"{success_rate:.1f}%")
    else:
        st.info("Nenhum histórico disponível.")

with tab2:
    st.caption("Execuções manuais via GitHub Actions")

    manual_runs = get_workflow_runs(WORKFLOWS["manual"], limit=30)

    if manual_runs:
        table_data = []
        for run in manual_runs:
            table_data.append(
                {
                    "Status": get_status_emoji(run.get("conclusion") or "in_progress"),
                    "Data/Hora": format_timestamp(run["created_at"]),
                    "Duração": format_duration(run["created_at"], run.get("updated_at", run["created_at"])),
                    "Por": f"@{run['triggering_actor']['login']}",
                    "Run": f"#{run['run_number']}",
                    "Logs": run["html_url"],
                }
            )

        st.dataframe(
            table_data,
            use_container_width=True,
            column_config={"Logs": st.column_config.LinkColumn("Logs", display_text="Ver")},
            hide_index=True,
        )
    else:
        st.info("Nenhuma execução manual registrada.")

with tab3:
    st.caption("Verificações diárias de monitoramento")

    monitoring_runs = get_workflow_runs(WORKFLOWS["monitoring"], limit=30)

    if monitoring_runs:
        table_data = []
        for run in monitoring_runs:
            table_data.append(
                {
                    "Status": get_status_emoji(run.get("conclusion") or "in_progress"),
                    "Data": format_timestamp(run["created_at"]),
                    "Resultado": run.get("conclusion", "running").title(),
                    "Run": f"#{run['run_number']}",
                    "Logs": run["html_url"],
                }
            )

        st.dataframe(
            table_data,
            use_container_width=True,
            column_config={"Logs": st.column_config.LinkColumn("Logs", display_text="Ver")},
            hide_index=True,
        )
    else:
        st.info("Nenhum monitoramento registrado.")

st.divider()

# ========================================
# Executar Manualmente
# ========================================

st.subheader("⚡ Executar Análise Manualmente")

st.info(
    """
    **Instruções:**

    Para executar uma análise manual, use uma das opções abaixo:

    **Opção 1: GitHub UI (Recomendado)**
    1. Vá para [Actions > Manual Chat Analysis](https://github.com/{}/{}/actions/workflows/manual_analysis.yml)
    2. Clique em "Run workflow"
    3. Configure os parâmetros
    4. Clique em "Run workflow" (botão verde)
    """.format(REPO_OWNER, REPO_NAME)
)

with st.expander("📋 Opção 2: GitHub CLI", expanded=False):
    col1, col2 = st.columns(2)

    with col1:
        max_chats = st.number_input("Máximo de chats", min_value=10, max_value=10000, value=1000, step=100)

    with col2:
        week_start = st.date_input("Início da semana (opcional)", value=None)

    save_bq = st.checkbox("Salvar no BigQuery", value=True)

    week_param = f"-f week_start={week_start.strftime('%Y-%m-%d')}" if week_start else ""

    command = f"""gh workflow run manual_analysis.yml \\
  -f max_chats={max_chats} \\
  {week_param} \\
  -f save_to_bigquery={str(save_bq).lower()}"""

    st.code(command, language="bash")
    st.caption("💡 Requer [GitHub CLI](https://cli.github.com/) instalado e autenticado")

st.divider()

# ========================================
# Documentação
# ========================================

with st.expander("📚 Documentação de Secrets", expanded=False):
    st.markdown(
        """
    ### Secrets Configurados

    Os seguintes secrets devem estar configurados no GitHub para os workflows funcionarem:

    **Essenciais:**
    - `GEMINI_API_KEY` - API key do Google Gemini
    - `BIGQUERY_PROJECT_ID` - ID do projeto GCP
    - `BIGQUERY_DATASET_ID` - Nome do dataset
    - `GCP_SA_KEY` - Service Account JSON completo

    **Notificações:**
    - `MAIL_USERNAME` - Email para enviar notificações
    - `MAIL_PASSWORD` - Senha ou App Password
    - `NOTIFICATION_EMAIL` - Email para receber alertas

    **Opcional:**
    - `REDIS_URL` - URL do Redis para caching

    📄 [Ver documentação completa](https://github.com/{}/{}/blob/main/.github/SECRETS.md)
    """.format(REPO_OWNER, REPO_NAME)
    )

# Footer
st.caption(
    """
🤖 **Automação powered by GitHub Actions**
| 📊 Dados atualizados a cada 5 minutos
| [Ver Workflows](https://github.com/{}/{}/actions)
""".format(REPO_OWNER, REPO_NAME)
)
