"""
Utilitários compartilhados para o dashboard multi-página.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union

import plotly.io as pio
import pytz
import streamlit as st

# ================================================================
# CONSTANTES DE NEGÓCIO
# ================================================================

TIMEZONE = pytz.timezone("America/Sao_Paulo")

BUSINESS_HOURS: Dict[str, Union[int, List[int]]] = {
    "start": 8,
    "end": 18,
    "weekdays": [0, 1, 2, 3, 4],  # Seg-Sex
}

# Tags de qualificação de leads
# Suporta tanto dados reais do BigQuery quanto dados mock genéricos
TAG_GROUPS = {
    "qualificado_plus": ["Perfil Qualificado Plus", "Lead Qualificado Plus"],
    "qualificado": ["Perfil Qualificado", "Lead Qualificado"],
    "indefinido": ["Perfil Indefinido", "Lead Indefinido"],
    "fora_perfil": ["Fora de perfil", "Fora de Perfil"],
    "procedimento": ["Procedimento"],
    "pos_vendas": ["Pós-Vendas"],
    "neutro": ["Neutro"],
}

# Classificação para métricas de conversão (suporta ambos formatos)
TAGS_CONVERTIDO = [
    "Perfil Qualificado Plus",
    "Perfil Qualificado",  # BigQuery
    "Lead Qualificado Plus",
    "Lead Qualificado",  # Mock
]
TAGS_NAO_CONVERTIDO = [
    "Perfil Indefinido",
    "Fora de perfil",
    "Neutro",  # BigQuery
    "Lead Indefinido",
    "Fora de Perfil",  # Mock
]
TAGS_OUTROS = ["Procedimento", "Pós-Vendas"]

# Origens de leads
ORIGENS_PRINCIPAIS = [
    "SDR - Whats Anuncio",
    "SDR - Site",
    "SDR - Whatsapp",
    "SDR - Instagram",
    "SDR - Google Pago",
    "SDR - SMS",
    "Anúncio Online",  # Mock
    "Site",  # Mock
    "Indicação",  # Mock
    "Instagram",  # Mock
    "Google",  # Mock
]


# ================================================================
# FUNÇÕES DE TEMA
# ================================================================


def get_theme_mode() -> str:
    """
    Detecta o modo de tema atual.

    Prioridade:
    1. Preferência do usuário em session_state
    2. Configuração do Streamlit
    3. Fallback para 'dark'
    """
    # Prioridade 1: preferência do usuário
    if "theme_mode" in st.session_state:
        return st.session_state["theme_mode"]

    # Prioridade 2: configuração do Streamlit
    try:
        theme_base = st.get_option("theme.base")
        if theme_base:
            return theme_base
    except Exception:
        pass

    # Fallback
    return "dark"


def get_colors() -> Dict[str, Any]:
    """
    Retorna paleta de cores corporate sóbria baseada no tema atual.

    Design corporativo com azul profissional e tons neutros.
    """
    is_dark = get_theme_mode() == "dark"

    if is_dark:
        return {
            # Cores principais - Corporate Blue
            "primary": "#2563eb",  # Azul corporativo
            "secondary": "#3b82f6",  # Azul mais claro
            "tertiary": "#60a5fa",  # Azul suave
            # Cores semânticas - Sutis
            "success": "#22c55e",  # Verde
            "warning": "#eab308",  # Amarelo
            "danger": "#ef4444",  # Vermelho
            "info": "#3b82f6",  # Azul info
            # Backgrounds
            "chart_bg": "rgba(0,0,0,0)",
            "card_bg": "#1e293b",
            "grid": "rgba(148, 163, 184, 0.15)",
            "border": "#334155",
            # Texto - Hierarquia clara
            "text": "#f8fafc",  # Branco suave
            "text_muted": "#94a3b8",  # Cinza médio
            "text_accent": "#60a5fa",  # Azul accent
            # Sequência de cores para gráficos - Corporate
            "chart_sequence": [
                "#2563eb",  # Azul primário
                "#0891b2",  # Cyan
                "#059669",  # Verde
                "#ca8a04",  # Amarelo escuro
                "#7c3aed",  # Roxo
                "#db2777",  # Rosa
                "#ea580c",  # Laranja
                "#475569",  # Cinza
            ],
            # Gradientes (não usados em design sóbrio)
            "gradient_primary": ["#2563eb", "#3b82f6"],
            "gradient_success": ["#16a34a", "#22c55e"],
            "gradient_warning": ["#ca8a04", "#eab308"],
            "gradient_danger": ["#dc2626", "#ef4444"],
            # Gauge
            "gauge_steps": ["#334155", "#475569", "#64748b"],
        }
    else:
        return {
            # Cores principais - Corporate Blue
            "primary": "#1d4ed8",  # Azul corporativo escuro
            "secondary": "#2563eb",  # Azul médio
            "tertiary": "#3b82f6",  # Azul claro
            # Cores semânticas - Sutis
            "success": "#16a34a",  # Verde
            "warning": "#ca8a04",  # Amarelo escuro
            "danger": "#dc2626",  # Vermelho
            "info": "#2563eb",  # Azul info
            # Backgrounds
            "chart_bg": "rgba(255,255,255,0)",
            "card_bg": "#ffffff",
            "grid": "rgba(15, 23, 42, 0.08)",
            "border": "#e2e8f0",
            # Texto - Hierarquia clara
            "text": "#0f172a",  # Quase preto
            "text_muted": "#64748b",  # Cinza médio
            "text_accent": "#1d4ed8",  # Azul accent
            # Sequência de cores para gráficos - Corporate
            "chart_sequence": [
                "#1d4ed8",  # Azul primário
                "#0e7490",  # Cyan escuro
                "#047857",  # Verde escuro
                "#a16207",  # Amarelo escuro
                "#6d28d9",  # Roxo
                "#be185d",  # Rosa
                "#c2410c",  # Laranja
                "#374151",  # Cinza
            ],
            # Gradientes
            "gradient_primary": ["#1d4ed8", "#2563eb"],
            "gradient_success": ["#047857", "#16a34a"],
            "gradient_warning": ["#a16207", "#ca8a04"],
            "gradient_danger": ["#b91c1c", "#dc2626"],
            # Gauge
            "gauge_steps": ["#e2e8f0", "#cbd5e1", "#94a3b8"],
        }


def get_premium_layout() -> Dict[str, Any]:
    """
    Retorna configurações de layout premium para gráficos Plotly.
    """
    colors = get_colors()

    return {
        "paper_bgcolor": colors["chart_bg"],
        "plot_bgcolor": colors["chart_bg"],
        "font": {
            "family": "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', sans-serif",
            "size": 14,
            "color": colors["text"],
        },
        "title": {
            "font": {
                "size": 20,
                "color": colors["text"],
                "family": "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
            },
            "x": 0,
            "xanchor": "left",
        },
        "margin": {"l": 60, "r": 30, "t": 50, "b": 50},
        "xaxis": {
            "showgrid": True,
            "gridcolor": colors["grid"],
            "gridwidth": 1,
            "zeroline": False,
            "tickfont": {"size": 13, "color": colors["text_muted"]},
            "title_font": {"size": 14, "color": colors["text_muted"]},
        },
        "yaxis": {
            "showgrid": True,
            "gridcolor": colors["grid"],
            "gridwidth": 1,
            "zeroline": False,
            "tickfont": {"size": 13, "color": colors["text_muted"]},
            "title_font": {"size": 14, "color": colors["text_muted"]},
        },
        "legend": {
            "font": {"size": 13, "color": colors["text_muted"]},
            "bgcolor": "rgba(0,0,0,0)",
            "borderwidth": 0,
        },
        "hoverlabel": {
            "bgcolor": colors["card_bg"],
            "font_size": 14,
            "font_family": "-apple-system, BlinkMacSystemFont, sans-serif",
            "font_color": colors["text"],
            "bordercolor": colors["primary"],
        },
        "colorway": colors["chart_sequence"],
    }


def apply_chart_theme(fig, title: Optional[str] = None):
    """
    Aplica tema corporate sóbrio aos gráficos Plotly.

    Args:
        fig: Figura Plotly
        title: Título opcional para o gráfico
    """
    layout = get_premium_layout()

    if title:
        layout["title"]["text"] = title

    fig.update_layout(**layout)

    return fig


def setup_plotly_theme():
    """Configura tema global do Plotly."""
    is_dark = get_theme_mode() == "dark"
    pio.templates.default = "plotly_dark" if is_dark else "plotly_white"


# ================================================================
# FUNÇÕES DE CONTEXTO DE HORÁRIO
# ================================================================


def classify_contact_context(first_message_date: datetime) -> str:
    """Classifica se o contato foi em horário comercial ou fora."""
    if first_message_date is None:
        return "desconhecido"

    # Converter para timezone local se necessário
    if first_message_date.tzinfo is None:
        local_dt = TIMEZONE.localize(first_message_date)
    else:
        local_dt = first_message_date.astimezone(TIMEZONE)

    hour = local_dt.hour
    weekday = local_dt.weekday()

    # Cast explicit para mypy
    weekdays = BUSINESS_HOURS["weekdays"]
    start_hour = BUSINESS_HOURS["start"]
    end_hour = BUSINESS_HOURS["end"]

    if weekday not in weekdays:  # type: ignore[operator]
        return "fora_expediente"
    elif hour < start_hour or hour >= end_hour:  # type: ignore[operator]
        return "fora_expediente"
    else:
        return "horario_comercial"


def is_business_hour(dt: datetime) -> bool:
    """Verifica se um datetime está em horário comercial."""
    return classify_contact_context(dt) == "horario_comercial"


# ================================================================
# FUNÇÕES DE FILTRAGEM DE BOT
# ================================================================


def is_bot_message(message: Dict) -> bool:
    """Identifica se a mensagem é do bot (não agente humano)."""
    sent_by = message.get("sentBy", {})
    msg_type = message.get("type", "")
    sender_email = sent_by.get("email", "")

    return sender_email == "octabot@octachat.com" or msg_type == "automatic"


def is_human_agent_message(message: Dict) -> bool:
    """Identifica se a mensagem é de um agente humano."""
    sent_by = message.get("sentBy", {})
    sender_type = sent_by.get("type", "")

    return sender_type == "agent" and not is_bot_message(message)


# ================================================================
# FUNÇÕES DE CLASSIFICAÇÃO DE LEADS
# ================================================================


def get_chat_tags(chat) -> List[str]:
    """Extrai lista de nomes de tags de um chat."""
    if hasattr(chat, "tags") and chat.tags:
        return [
            tag.get("name", "") if isinstance(tag, dict) else str(tag)
            for tag in chat.tags
        ]
    return []


def classify_lead_qualification(tags: List[str]) -> str:
    """Classifica um lead baseado em suas tags."""
    for tag in tags:
        if tag in TAGS_CONVERTIDO:
            return "qualificado"
        if tag in TAGS_NAO_CONVERTIDO:
            return "nao_qualificado"
        if tag in TAGS_OUTROS:
            return "outro"
    return "sem_tag"


def get_lead_status(chat) -> str:
    """
    Retorna o status unificado do lead, priorizando a análise da IA (sales_outcome).

    Regra de precedência:
    1. chat.sales_outcome (Campo populado pelo backend/Postgres)
    2. Tags do chat (chat.tags)

    Returns:
        One of: 'qualificado', 'nao_qualificado', 'outro', 'sem_tag'
    """
    # 1. Tentar sales_outcome do Postgres/AI
    if hasattr(chat, "sales_outcome") and chat.sales_outcome:
        outcome = chat.sales_outcome.lower().strip()

        # Mapeamento direto dos outcomes do LLM
        if outcome == "qualificado":
            return "qualificado"
        if outcome == "nao_qualificado":
            return "nao_qualificado"

    # 2. Fallback para tags (comportamento original)
    tags = get_chat_tags(chat)
    return classify_lead_qualification(tags)


def get_lead_origin(chat) -> str:
    """Extrai a origem do lead do customFields do contato."""
    try:
        if hasattr(chat, "contact") and chat.contact:
            custom_fields = getattr(chat.contact, "customFields", None)
            if custom_fields and isinstance(custom_fields, dict):
                origin = custom_fields.get("origem_do_negocio", None)
                # Tratar null, None, vazio, 'null', 'None' como 'Não Informado'
                if (
                    origin is None
                    or origin == ""
                    or origin == "null"
                    or origin == "None"
                ):
                    return "Não Informado"
                return origin
    except Exception:
        pass
    return "Não Informado"


# ================================================================
# FUNÇÕES DE SESSION STATE
# ================================================================


def init_session_state():
    """Inicializa variáveis de sessão para filtros globais."""
    if "filters" not in st.session_state:
        st.session_state.filters = {
            "date_range": None,
            "agents": [],
            "origins": [],
            "tags": [],
            "business_hours_only": False,
        }

    if "data_loaded" not in st.session_state:
        st.session_state.data_loaded = False

    if "chats" not in st.session_state:
        st.session_state.chats = []


def apply_filters(chats: List, filters: Dict) -> List:
    """Aplica filtros globais à lista de chats."""
    filtered = chats

    # Filtro por período (datas)
    if filters.get("date_range"):
        start_date, end_date = filters["date_range"]
        filtered = [
            c
            for c in filtered
            if c.firstMessageDate
            and start_date <= c.firstMessageDate.date() <= end_date
        ]

    # Filtro por agente
    if filters.get("agents"):
        filtered = [
            c
            for c in filtered
            if hasattr(c, "agent") and c.agent and c.agent.name in filters["agents"]
        ]

    # Filtro por origem
    if filters.get("origins"):
        filtered = [c for c in filtered if get_lead_origin(c) in filters["origins"]]

    # Filtro por tags
    if filters.get("tags"):
        filtered = [
            c
            for c in filtered
            if any(tag in get_chat_tags(c) for tag in filters["tags"])
        ]

    # Filtro por horário comercial
    if filters.get("business_hours_only"):
        filtered = [
            c
            for c in filtered
            if hasattr(c, "firstMessageDate") and is_business_hour(c.firstMessageDate)
        ]

    return filtered


# ================================================================
# CSS HELPERS
# ================================================================


def apply_custom_css():
    """Aplica CSS customizado baseado no tema - Estilo Corporate Sóbrio."""
    is_dark = get_theme_mode() == "dark"

    if is_dark:
        css = """
        <style>
            /* KPI Cards - Dark Theme - Corporate */
            .stMetric {
                background: #1e293b;
                padding: 20px;
                border-radius: 8px;
                border: 1px solid #334155;
                box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
            }
            .stMetric label {
                color: #94a3b8 !important;
                font-size: 0.85rem;
                font-weight: 500;
                text-transform: uppercase;
                letter-spacing: 0.05em;
            }
            .stMetric [data-testid="stMetricValue"] {
                color: #f8fafc !important;
                font-size: 1.75rem !important;
                font-weight: 600;
            }
            .stMetric [data-testid="stMetricDelta"] {
                font-size: 0.875rem;
            }

            /* Dividers */
            hr { border-color: #334155; }

            /* User Profile Card */
            .user-profile-card {
                background: #1e293b;
                padding: 16px;
                border-radius: 8px;
                border: 1px solid #334155;
                margin-bottom: 12px;
            }
            .user-profile-card .username {
                color: #f8fafc;
                font-weight: 600;
                font-size: 0.95rem;
            }
            .user-profile-card .role {
                color: #94a3b8;
                font-size: 0.8rem;
            }

            /* Buttons */
            .stButton > button {
                border-radius: 6px;
                font-weight: 500;
            }

            /* Sidebar */
            .stSidebar [data-testid="stSidebarContent"] {
                padding-top: 1rem;
            }

            /* Headers */
            h1, h2, h3 {
                color: #f8fafc;
                font-weight: 600;
            }
        </style>
        """
    else:
        css = """
        <style>
            /* KPI Cards - Light Theme - Corporate */
            .stMetric {
                background: #ffffff;
                padding: 20px;
                border-radius: 8px;
                border: 1px solid #e2e8f0;
                box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
            }
            .stMetric label {
                color: #64748b !important;
                font-size: 0.85rem;
                font-weight: 500;
                text-transform: uppercase;
                letter-spacing: 0.05em;
            }
            .stMetric [data-testid="stMetricValue"] {
                color: #0f172a !important;
                font-size: 1.75rem !important;
                font-weight: 600;
            }
            .stMetric [data-testid="stMetricDelta"] {
                font-size: 0.875rem;
            }

            /* Dividers */
            hr { border-color: #e2e8f0; }

            /* User Profile Card */
            .user-profile-card {
                background: #ffffff;
                padding: 16px;
                border-radius: 8px;
                border: 1px solid #e2e8f0;
                margin-bottom: 12px;
            }
            .user-profile-card .username {
                color: #0f172a;
                font-weight: 600;
                font-size: 0.95rem;
            }
            .user-profile-card .role {
                color: #64748b;
                font-size: 0.8rem;
            }

            /* Buttons */
            .stButton > button {
                border-radius: 6px;
                font-weight: 500;
            }

            /* Sidebar */
            .stSidebar [data-testid="stSidebarContent"] {
                padding-top: 1rem;
            }

            /* Headers */
            h1, h2, h3 {
                color: #0f172a;
                font-weight: 600;
            }
        </style>
        """

    st.markdown(css, unsafe_allow_html=True)


# ================================================================
# COMPONENTES DE AUTENTICAÇÃO (SIDEBAR)
# ================================================================


def render_user_sidebar() -> None:
    """
    Renderiza perfil do usuário e botão de logout no sidebar.

    Deve ser chamado em todas as páginas protegidas para manter
    consistência visual e funcionalidade de logout.
    """
    from src.auth.auth_manager import AuthManager

    if not AuthManager.is_authenticated():
        return

    # Obter dados do usuário da sessão
    username = st.session_state.get("username", "Usuário")
    st.session_state.get("role", "user")
    is_superadmin = st.session_state.get("is_superadmin", False)

    # Ícone baseado no role
    role_icon = "👑" if is_superadmin else "👤"
    role_label = "Super Admin" if is_superadmin else "Usuário"

    # Card do usuário
    st.sidebar.markdown(
        f"""
    <div class="user-profile-card">
        <div class="username">{role_icon} {username}</div>
        <div class="role">{role_label}</div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Botão de logout
    if st.sidebar.button("🚪 Sair", key="logout_btn", width="stretch"):
        AuthManager.logout()
        st.rerun()

    # Toggle de tema
    current_theme = st.session_state.get("theme_mode", "dark")
    theme_options = ["🌙 Dark", "☀️ Light"]
    default_idx = 0 if current_theme == "dark" else 1

    selected_theme = st.sidebar.selectbox(
        "Tema",
        theme_options,
        index=default_idx,
        key="theme_selector",
        label_visibility="collapsed",
    )

    new_theme = "dark" if "Dark" in selected_theme else "light"
    if new_theme != current_theme:
        st.session_state["theme_mode"] = new_theme
        st.rerun()

    # Alert badge
    try:
        from src.auth.alert_service import AlertService

        alert_count = AlertService.get_alert_count()
        if alert_count > 0:
            st.sidebar.markdown(
                f"""
                <div style="
                    background: linear-gradient(135deg, #ff6b6b, #ee5a24);
                    color: white;
                    padding: 8px 12px;
                    border-radius: 8px;
                    text-align: center;
                    margin: 10px 0;
                    font-weight: 600;
                ">
                    🔔 {alert_count} alerta{"s" if alert_count > 1 else ""} ativo{"s" if alert_count > 1 else ""}
                </div>
                """,
                unsafe_allow_html=True,
            )
    except Exception:
        pass  # Alert service not available

    st.sidebar.markdown("---")


# ================================================================
# COMPONENTES DE LOADING
# ================================================================


def loading_with_progress(
    message: str = "Carregando...",
    show_progress: bool = True,
) -> tuple:
    """
    Cria um contexto de loading com mensagem e barra de progresso.

    Usage:
        placeholder, progress = loading_with_progress("Carregando dados...")
        for i, item in enumerate(items):
            progress.progress((i + 1) / len(items))
            # process item
        placeholder.empty()

    Returns:
        Tuple of (placeholder, progress_bar)
    """
    placeholder = st.empty()
    with placeholder.container():
        st.markdown(f"### ⏳ {message}")
        if show_progress:
            progress_bar = st.progress(0)
        else:
            progress_bar = None
        st.info("Aguarde enquanto processamos os dados...")

    return placeholder, progress_bar


def render_skeleton(height: int = 200, message: str = "Carregando gráfico...") -> None:
    """
    Renderiza um placeholder de skeleton loading para gráficos.

    Args:
        height: Altura do placeholder em pixels
        message: Mensagem a exibir
    """
    is_dark = get_theme_mode() == "dark"
    bg_color = "#1f2937" if is_dark else "#f3f4f6"
    text_color = "#9ca3af" if is_dark else "#6b7280"

    st.markdown(
        f"""
    <div style="
        background: {bg_color};
        height: {height}px;
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        animation: pulse 1.5s infinite;
    ">
        <span style="color: {text_color}; font-size: 14px;">
            ⏳ {message}
        </span>
    </div>
    <style>
        @keyframes pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.5; }}
        }}
    </style>
    """,
        unsafe_allow_html=True,
    )


def render_loading_placeholder(
    cols: int = 4, message: str = "Carregando métricas..."
) -> None:
    """
    Renderiza placeholders de loading para KPIs.

    Args:
        cols: Número de colunas de KPIs
        message: Mensagem a exibir
    """
    is_dark = get_theme_mode() == "dark"
    bg_color = "#1f2937" if is_dark else "#f3f4f6"
    text_color = "#9ca3af" if is_dark else "#6b7280"

    columns = st.columns(cols)
    for col in columns:
        with col:
            st.markdown(
                f"""
            <div style="
                background: {bg_color};
                padding: 20px;
                border-radius: 10px;
                text-align: center;
                animation: pulse 1.5s infinite;
            ">
                <div style="color: {text_color}; font-size: 12px;">⏳</div>
                <div style="color: {text_color}; font-size: 20px; font-weight: bold;">---</div>
            </div>
            """,
                unsafe_allow_html=True,
            )


# ================================================================
# COMPONENTES DE EXPORTAÇÃO
# ================================================================


def create_excel_download(
    df,
    filename: str = "dados",
    sheet_name: str = "Dados",
    button_label: str = "📥 Baixar Excel",
    key: Optional[str] = None,
) -> None:
    """
    Cria um botão de download de Excel para um DataFrame.

    Args:
        df: DataFrame do pandas
        filename: Nome do arquivo (sem extensão)
        sheet_name: Nome da aba do Excel
        button_label: Texto do botão
        key: Chave única do botão (para evitar duplicatas)
    """
    import io
    from datetime import datetime

    import pandas as pd

    # Gerar nome do arquivo com timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    full_filename = f"{filename}_{timestamp}.xlsx"

    # Criar arquivo Excel em memória
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        df.to_excel(writer, sheet_name=sheet_name, index=False)

        # Formatação básica
        workbook = writer.book
        worksheet = writer.sheets[sheet_name]

        # Ajustar largura das colunas
        for i, col in enumerate(df.columns):
            max_length = max(
                df[col].astype(str).map(len).max() if len(df) > 0 else 0, len(str(col))
            )
            worksheet.set_column(i, i, min(max_length + 2, 50))

        # Header formatting
        header_format = workbook.add_format(
            {"bold": True, "bg_color": "#6366f1", "font_color": "white", "border": 1}
        )
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_format)

    buffer.seek(0)

    # Botão de download
    st.download_button(
        label=button_label,
        data=buffer,
        file_name=full_filename,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key=key or f"download_excel_{filename}",
    )


def create_csv_download(
    df,
    filename: str = "dados",
    button_label: str = "📥 Baixar CSV",
    key: Optional[str] = None,
) -> None:
    """
    Cria um botão de download de CSV para um DataFrame.

    Args:
        df: DataFrame do pandas
        filename: Nome do arquivo (sem extensão)
        button_label: Texto do botão
        key: Chave única do botão
    """
    from datetime import datetime

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    full_filename = f"{filename}_{timestamp}.csv"

    csv_data = df.to_csv(index=False).encode("utf-8")

    st.download_button(
        label=button_label,
        data=csv_data,
        file_name=full_filename,
        mime="text/csv",
        key=key or f"download_csv_{filename}",
    )


# ================================================================
# FUNÇÕES DE COMPARATIVO DE PERÍODOS
# ================================================================


def split_chats_by_period(chats: List, days: int = 7) -> tuple:
    """
    Divide chats em período atual e período anterior.

    Args:
        chats: Lista de chats
        days: Número de dias para cada período

    Returns:
        Tuple of (current_period_chats, previous_period_chats)
    """
    from datetime import datetime, timedelta

    now = datetime.now()
    current_start = now - timedelta(days=days)
    previous_start = current_start - timedelta(days=days)

    current_period = []
    previous_period = []

    for chat in chats:
        if chat.firstMessageDate:
            chat_date = (
                chat.firstMessageDate.replace(tzinfo=None)
                if chat.firstMessageDate.tzinfo
                else chat.firstMessageDate
            )
            if chat_date >= current_start:
                current_period.append(chat)
            elif chat_date >= previous_start:
                previous_period.append(chat)

    return current_period, previous_period


def calculate_delta(current: float, previous: float) -> tuple:
    """
    Calcula o delta entre dois valores e retorna formatação.

    Args:
        current: Valor do período atual
        previous: Valor do período anterior

    Returns:
        Tuple of (delta_value, delta_formatted, is_positive)
    """
    if previous == 0:
        return 0, "N/A", True

    delta = ((current - previous) / previous) * 100
    is_positive = delta >= 0

    if abs(delta) >= 1:
        formatted = f"{delta:+.1f}%"
    else:
        formatted = f"{delta:+.2f}%"

    return delta, formatted, is_positive


def render_kpi_with_delta(
    col,
    label: str,
    current_value: str,
    delta: Optional[str] = None,
    delta_color: str = "normal",
    help_text: Optional[str] = None,
) -> None:
    """
    Renderiza um KPI com delta opcional.

    Args:
        col: Streamlit column
        label: Label do KPI
        current_value: Valor atual formatado
        delta: Delta formatado (opcional)
        delta_color: 'normal', 'inverse', ou 'off'
        help_text: Texto de ajuda opcional
    """
    if delta:
        col.metric(
            label=label,
            value=current_value,
            delta=delta,
            delta_color=delta_color,
            help=help_text,
        )
    else:
        col.metric(
            label=label,
            value=current_value,
            help=help_text,
        )


# ================================================================
# GRÁFICOS PREMIUM
# ================================================================


def create_premium_bar_chart(
    df,
    x: str,
    y: str,
    orientation: str = "v",
    color: Optional[str] = None,
    color_discrete_map: Optional[dict] = None,
    color_continuous_scale: Optional[list] = None,
    title: Optional[str] = None,
    show_values: bool = True,
    rounded_bars: bool = True,
):
    """
    Cria um gráfico de barras com estilo premium.

    Args:
        df: DataFrame com os dados
        x: Coluna para eixo X
        y: Coluna para eixo Y
        orientation: 'v' (vertical) ou 'h' (horizontal)
        color: Coluna para colorir as barras
        color_discrete_map: Mapeamento de cores discretas
        color_continuous_scale: Escala de cores contínua
        title: Título do gráfico
        show_values: Mostrar valores nas barras
        rounded_bars: Usar cantos arredondados
    """
    import plotly.express as px

    colors = get_colors()

    # Criar figura base
    fig = px.bar(
        df,
        x=x,
        y=y,
        orientation=orientation,
        color=color,
        color_discrete_map=color_discrete_map,
        color_continuous_scale=color_continuous_scale
        or [colors["primary"], colors["secondary"], colors["tertiary"]],
        text=y if show_values and orientation == "v" else (x if show_values else None),
    )

    # Estilizar barras
    fig.update_traces(
        marker=dict(
            line=dict(width=0),
            cornerradius=8 if rounded_bars else 0,
        ),
        textposition="outside" if show_values else None,
        textfont=dict(size=11, color=colors["text_muted"]),
        hovertemplate=(
            "<b>%{x}</b><br>%{y}<extra></extra>"
            if orientation == "v"
            else "<b>%{y}</b><br>%{x}<extra></extra>"
        ),
    )

    # Aplicar tema premium
    apply_chart_theme(fig, title)

    # Ajustes específicos
    fig.update_layout(
        showlegend=color is not None,
        bargap=0.3,
        bargroupgap=0.1,
    )

    return fig


def create_premium_pie_chart(
    df,
    values: str,
    names: str,
    hole: float = 0.4,
    title: Optional[str] = None,
    color_discrete_map: Optional[dict] = None,
):
    """
    Cria um gráfico de pizza/donut com estilo premium.

    Args:
        df: DataFrame com os dados
        values: Coluna com os valores
        names: Coluna com os nomes/categorias
        hole: Tamanho do buraco (0 para pizza, 0.4+ para donut)
        title: Título do gráfico
        color_discrete_map: Mapeamento de cores
    """
    import plotly.express as px

    colors = get_colors()

    fig = px.pie(
        df,
        values=values,
        names=names,
        hole=hole,
        color=names,
        color_discrete_map=color_discrete_map,
    )

    # Estilizar
    fig.update_traces(
        textposition="inside",
        textinfo="percent+label",
        textfont=dict(size=12, color="#ffffff"),
        marker=dict(
            line=dict(color=colors["chart_bg"], width=2),
        ),
        hovertemplate="<b>%{label}</b><br>%{value:,} (%{percent})<extra></extra>",
        pull=[0.02] * len(df),  # Pequena separação entre fatias
    )

    # Aplicar tema
    apply_chart_theme(fig, title)

    fig.update_layout(
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.2,
            xanchor="center",
            x=0.5,
        ),
    )

    return fig


def create_premium_line_chart(
    df,
    x: str,
    y: str,
    color: Optional[str] = None,
    title: Optional[str] = None,
    show_markers: bool = True,
    fill: bool = False,
):
    """
    Cria um gráfico de linhas com estilo premium.

    Args:
        df: DataFrame com os dados
        x: Coluna para eixo X
        y: Coluna para eixo Y
        color: Coluna para separar séries
        title: Título do gráfico
        show_markers: Mostrar marcadores nos pontos
        fill: Preencher área abaixo da linha
    """
    import plotly.express as px

    colors = get_colors()

    fig = px.line(
        df,
        x=x,
        y=y,
        color=color,
        markers=show_markers,
    )

    # Estilizar linhas
    fig.update_traces(
        line=dict(width=3),
        marker=dict(size=8, line=dict(width=2, color=colors["chart_bg"])),
        hovertemplate="<b>%{x}</b><br>%{y:,.1f}<extra></extra>",
    )

    if fill:
        fig.update_traces(fill="tozeroy", fillcolor="rgba(99, 102, 241, 0.1)")

    # Aplicar tema
    apply_chart_theme(fig, title)

    return fig


def create_premium_heatmap(
    df,
    x: str,
    y: str,
    z: str,
    title: Optional[str] = None,
):
    """
    Cria um heatmap com estilo premium.
    """
    import plotly.express as px

    colors = get_colors()

    fig = px.density_heatmap(
        df,
        x=x,
        y=y,
        z=z,
        color_continuous_scale=[
            [0, colors["chart_bg"]],
            [0.5, colors["primary"]],
            [1, colors["secondary"]],
        ],
    )

    apply_chart_theme(fig, title)

    return fig


# ================================================================
# ECHARTS - GRÁFICOS MODERNOS
# ================================================================


def get_echarts_theme() -> Dict[str, Any]:
    """
    Retorna configuração de tema para ECharts baseado no tema atual.
    """
    colors = get_colors()

    return {
        "backgroundColor": "transparent",
        "textStyle": {
            "color": colors["text"],
            "fontFamily": "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
            "fontSize": 14,
        },
        "title": {
            "textStyle": {
                "color": colors["text"],
                "fontSize": 18,
                "fontWeight": 600,
            }
        },
        "legend": {
            "textStyle": {
                "color": colors["text_muted"],
                "fontSize": 13,
            }
        },
        "tooltip": {
            "backgroundColor": colors["card_bg"],
            "borderColor": colors.get("border", colors["grid"]),
            "textStyle": {
                "color": colors["text"],
                "fontSize": 13,
            },
        },
        "color": colors["chart_sequence"],
    }


def render_echarts_bar(
    data: List[Dict],
    x_key: str,
    y_key: str,
    title: Optional[str] = None,
    horizontal: bool = False,
    height: str = "400px",
    show_label: bool = True,
    key: Optional[str] = None,
) -> None:
    """
    Renderiza um gráfico de barras ECharts.

    Args:
        data: Lista de dicionários com os dados
        x_key: Chave para eixo X (categorias)
        y_key: Chave para eixo Y (valores)
        title: Título do gráfico
        horizontal: Se True, barras horizontais
        height: Altura do gráfico
        show_label: Mostrar valores nas barras
    """
    from streamlit_echarts import st_echarts

    colors = get_colors()
    theme = get_echarts_theme()

    x_data = [d[x_key] for d in data]
    y_data = [d[y_key] for d in data]

    # Formatar valores para labels
    formatted_y = []
    for v in y_data if not horizontal else x_data:
        if isinstance(v, float):
            if v >= 100:
                formatted_y.append(f"{int(round(v))}")
            elif v >= 10:
                formatted_y.append(f"{v:.1f}")
            else:
                formatted_y.append(f"{v:.2f}")
        else:
            formatted_y.append(str(v))

    option = {
        "backgroundColor": "transparent",
        "title": {"text": title, **theme["title"]} if title else None,
        "tooltip": {
            "trigger": "axis",
            "axisPointer": {"type": "shadow"},
            "valueFormatter": "(value) => typeof value === 'number' ? value.toFixed(2) : value",
            **theme["tooltip"],
        },
        "grid": {
            "left": "3%",
            "right": "4%",
            "bottom": "3%",
            "containLabel": True,
        },
        "xAxis": {
            "type": "category" if not horizontal else "value",
            "data": x_data if not horizontal else None,
            "axisLabel": {
                "color": colors["text_muted"],
                "fontSize": 12,
                "rotate": 0 if horizontal else (45 if len(x_data) > 5 else 0),
            },
            "axisLine": {"lineStyle": {"color": colors["grid"]}},
            "splitLine": (
                {"lineStyle": {"color": colors["grid"]}} if horizontal else None
            ),
        },
        "yAxis": {
            "type": "value" if not horizontal else "category",
            "data": x_data if horizontal else None,
            "axisLabel": {"color": colors["text_muted"], "fontSize": 12},
            "axisLine": {"lineStyle": {"color": colors["grid"]}},
            "splitLine": (
                {"lineStyle": {"color": colors["grid"]}} if not horizontal else None
            ),
        },
        "series": [
            {
                "type": "bar",
                "data": [
                    {"value": v, "label": {"formatter": f}}
                    for v, f in zip(y_data, formatted_y)
                ],
                "itemStyle": {
                    "color": colors["primary"],
                    "borderRadius": [4, 4, 0, 0] if not horizontal else [0, 4, 4, 0],
                },
                "label": {
                    "show": show_label,
                    "position": "top" if not horizontal else "right",
                    "color": colors["text_muted"],
                    "fontSize": 12,
                },
                "emphasis": {
                    "itemStyle": {"color": colors["secondary"]},
                },
            }
        ],
    }

    st_echarts(options=option, height=height, key=key)


def render_echarts_pie(
    data: List[Dict],
    name_key: str,
    value_key: str,
    title: Optional[str] = None,
    height: str = "400px",
    donut: bool = True,
    color_map: Optional[Dict[str, str]] = None,
    key: Optional[str] = None,
) -> None:
    """
    Renderiza um gráfico de pizza/donut ECharts.

    Args:
        data: Lista de dicionários com os dados
        name_key: Chave para nomes/categorias
        value_key: Chave para valores
        title: Título do gráfico
        height: Altura do gráfico
        donut: Se True, exibe como donut
        color_map: Mapeamento de cores por categoria
    """
    from streamlit_echarts import st_echarts

    colors = get_colors()
    theme = get_echarts_theme()

    pie_data = [{"name": d[name_key], "value": d[value_key]} for d in data]

    # Aplicar cores customizadas se fornecidas
    if color_map:
        for item in pie_data:
            if item["name"] in color_map:
                item["itemStyle"] = {"color": color_map[item["name"]]}

    option = {
        "backgroundColor": "transparent",
        "title": {"text": title, **theme["title"]} if title else None,
        "tooltip": {
            "trigger": "item",
            "formatter": "{b}: {c} ({d}%)",
            **theme["tooltip"],
        },
        "legend": {
            "orient": "horizontal",
            "bottom": "5%",
            **theme["legend"],
        },
        "series": [
            {
                "type": "pie",
                "radius": ["45%", "75%"] if donut else ["0%", "75%"],
                "center": ["50%", "45%"],
                "avoidLabelOverlap": True,
                "itemStyle": {
                    "borderRadius": 8,
                    "borderColor": colors["card_bg"],
                    "borderWidth": 2,
                },
                "label": {
                    "show": True,
                    "formatter": "{b}: {d}%",
                    "color": colors["text"],
                    "fontSize": 13,
                },
                "emphasis": {
                    "label": {"show": True, "fontSize": 16, "fontWeight": "bold"},
                    "itemStyle": {
                        "shadowBlur": 10,
                        "shadowColor": "rgba(0, 0, 0, 0.3)",
                    },
                },
                "data": pie_data,
            }
        ],
    }

    st_echarts(options=option, height=height, key=key)


def render_echarts_line(
    data: List[Dict],
    x_key: str,
    y_key: str,
    title: Optional[str] = None,
    height: str = "400px",
    smooth: bool = True,
    fill_area: bool = True,
    key: Optional[str] = None,
) -> None:
    """
    Renderiza um gráfico de linha ECharts.

    Args:
        data: Lista de dicionários com os dados
        x_key: Chave para eixo X
        y_key: Chave para eixo Y
        title: Título do gráfico
        height: Altura do gráfico
        smooth: Linha suave
        fill_area: Preencher área abaixo
    """
    from streamlit_echarts import st_echarts

    colors = get_colors()
    theme = get_echarts_theme()

    x_data = [d[x_key] for d in data]
    y_data = [d[y_key] for d in data]

    option = {
        "backgroundColor": "transparent",
        "title": {"text": title, **theme["title"]} if title else None,
        "tooltip": {
            "trigger": "axis",
            "valueFormatter": "(value) => typeof value === 'number' ? value.toFixed(2) : value",
            **theme["tooltip"],
        },
        "grid": {
            "left": "3%",
            "right": "4%",
            "bottom": "3%",
            "containLabel": True,
        },
        "xAxis": {
            "type": "category",
            "data": x_data,
            "boundaryGap": False,
            "axisLabel": {"color": colors["text_muted"], "fontSize": 12},
            "axisLine": {"lineStyle": {"color": colors["grid"]}},
        },
        "yAxis": {
            "type": "value",
            "axisLabel": {"color": colors["text_muted"], "fontSize": 12},
            "axisLine": {"lineStyle": {"color": colors["grid"]}},
            "splitLine": {"lineStyle": {"color": colors["grid"]}},
        },
        "series": [
            {
                "type": "line",
                "data": y_data,
                "smooth": smooth,
                "symbol": "circle",
                "symbolSize": 8,
                "itemStyle": {"color": colors["primary"]},
                "lineStyle": {"width": 3, "color": colors["primary"]},
                "areaStyle": (
                    {
                        "color": {
                            "type": "linear",
                            "x": 0,
                            "y": 0,
                            "x2": 0,
                            "y2": 1,
                            "colorStops": [
                                {"offset": 0, "color": colors["primary"] + "40"},
                                {"offset": 1, "color": colors["primary"] + "05"},
                            ],
                        }
                    }
                    if fill_area
                    else None
                ),
            }
        ],
    }

    st_echarts(options=option, height=height, key=key)


def render_echarts_bar_gradient(
    data: List[Dict],
    x_key: str,
    y_key: str,
    title: Optional[str] = None,
    horizontal: bool = True,
    height: str = "400px",
    gradient_type: str = "success_to_danger",
    reverse_y: bool = False,
    key: Optional[str] = None,
) -> None:
    """
    Renderiza um gráfico de barras ECharts com gradiente baseado nos valores.

    Args:
        data: Lista de dicionários com os dados
        x_key: Chave para eixo X (categorias)
        y_key: Chave para eixo Y (valores)
        title: Título do gráfico
        horizontal: Se True, barras horizontais
        height: Altura do gráfico
        gradient_type: "success_to_danger" (verde→vermelho) ou "danger_to_success" (vermelho→verde)
        reverse_y: Se True, inverte ordem do eixo Y
    """
    from streamlit_echarts import st_echarts

    colors = get_colors()
    theme = get_echarts_theme()

    # Extrair dados
    categories = [d[x_key] for d in data]
    values = [d[y_key] for d in data]

    # Calcular cores baseadas nos valores
    if values:
        min_val = min(values)
        max_val = max(values)
        range_val = max_val - min_val if max_val != min_val else 1

        bar_colors = []
        for v in values:
            ratio = (v - min_val) / range_val
            if gradient_type == "success_to_danger":
                # Verde para vermelho (bom = baixo)
                if ratio < 0.5:
                    bar_colors.append(colors["success"])
                elif ratio < 0.75:
                    bar_colors.append(colors["warning"])
                else:
                    bar_colors.append(colors["danger"])
            else:
                # Vermelho para verde (bom = alto)
                if ratio > 0.5:
                    bar_colors.append(colors["success"])
                elif ratio > 0.25:
                    bar_colors.append(colors["warning"])
                else:
                    bar_colors.append(colors["danger"])
    else:
        bar_colors = [colors["primary"]] * len(values)

    # Formatar valores para exibição
    formatted_values = []
    for v in values:
        if isinstance(v, float):
            formatted_values.append(f"{v:.1f}")
        else:
            formatted_values.append(str(v))

    # Dados com cores individuais
    series_data = [
        {"value": v, "itemStyle": {"color": c}, "label": {"formatter": f}}
        for v, c, f in zip(values, bar_colors, formatted_values)
    ]

    option = {
        "backgroundColor": "transparent",
        "title": {"text": title, **theme["title"]} if title else None,
        "tooltip": {
            "trigger": "axis",
            "axisPointer": {"type": "shadow"},
            "valueFormatter": "(value) => typeof value === 'number' ? value.toFixed(2) : value",
            **theme["tooltip"],
        },
        "grid": {
            "left": "3%",
            "right": "10%",
            "bottom": "3%",
            "containLabel": True,
        },
        "xAxis": {
            "type": "value" if horizontal else "category",
            "data": None if horizontal else categories,
            "axisLabel": {"color": colors["text_muted"], "fontSize": 12},
            "axisLine": {"lineStyle": {"color": colors["grid"]}},
            "splitLine": {"lineStyle": {"color": colors["grid"]}},
        },
        "yAxis": {
            "type": "category" if horizontal else "value",
            "data": categories if horizontal else None,
            "inverse": reverse_y,
            "axisLabel": {"color": colors["text_muted"], "fontSize": 12},
            "axisLine": {"lineStyle": {"color": colors["grid"]}},
        },
        "series": [
            {
                "type": "bar",
                "data": series_data,
                "itemStyle": {
                    "borderRadius": [0, 4, 4, 0] if horizontal else [4, 4, 0, 0]
                },
                "label": {
                    "show": True,
                    "position": "right" if horizontal else "top",
                    "color": colors["text_muted"],
                    "fontSize": 12,
                },
            }
        ],
    }

    st_echarts(options=option, height=height, key=key)


def render_echarts_gauge(
    value: float,
    title: Optional[str] = None,
    min_value: float = 0,
    max_value: float = 100,
    height: str = "300px",
    color: Optional[str] = None,
    key: Optional[str] = None,
) -> None:
    """
    Renderiza um gráfico gauge ECharts para visualização de KPIs.

    Args:
        value: Valor atual a ser exibido
        title: Título do gauge
        min_value: Valor mínimo da escala
        max_value: Valor máximo da escala
        height: Altura do gráfico
        color: Cor personalizada (usa padrão baseado no valor se None)
        key: Chave única para o componente
    """
    from streamlit_echarts import st_echarts

    colors = get_colors()
    theme = get_echarts_theme()

    # Cor baseada no percentual se não especificada
    if color is None:
        pct = (value - min_value) / (max_value - min_value) * 100
        if pct >= 70:
            color = colors["success"]
        elif pct >= 40:
            color = colors["warning"]
        else:
            color = colors["danger"]

    option = {
        "backgroundColor": "transparent",
        "title": {"text": title, **theme["title"]} if title else None,
        "series": [
            {
                "type": "gauge",
                "min": min_value,
                "max": max_value,
                "progress": {"show": True, "width": 18},
                "axisLine": {
                    "lineStyle": {
                        "width": 18,
                        "color": [[1, colors["grid"]]],
                    }
                },
                "axisTick": {"show": False},
                "splitLine": {"show": False},
                "axisLabel": {"show": False},
                "pointer": {"show": False},
                "anchor": {"show": False},
                "title": {"show": False},
                "detail": {
                    "valueAnimation": True,
                    "fontSize": 32,
                    "fontWeight": "bold",
                    "color": colors["text"],
                    "formatter": "{value}",
                    "offsetCenter": [0, "0%"],
                },
                "data": [{"value": value, "itemStyle": {"color": color}}],
            }
        ],
    }

    st_echarts(options=option, height=height, key=key)


def render_echarts_radar(
    data: List[Dict],
    indicators: List[Dict],
    title: Optional[str] = None,
    height: str = "400px",
    key: Optional[str] = None,
) -> None:
    """
    Renderiza um gráfico radar ECharts para comparação de múltiplas dimensões.

    Args:
        data: Lista de séries [{"name": "Agent1", "values": [80, 90, 70, 85, 60]}]
        indicators: Lista de indicadores [{"name": "Metric", "max": 100}]
        title: Título do gráfico
        height: Altura do gráfico
        key: Chave única para o componente
    """
    from streamlit_echarts import st_echarts

    colors = get_colors()
    theme = get_echarts_theme()

    # Cores para múltiplas séries
    series_colors = [
        colors["primary"],
        colors["secondary"],
        colors["success"],
        colors["warning"],
        colors["danger"],
        colors["info"],
    ]

    series_data = []
    for i, d in enumerate(data):
        series_data.append(
            {
                "value": d["values"],
                "name": d.get("name", f"Series {i + 1}"),
                "itemStyle": {"color": series_colors[i % len(series_colors)]},
                "areaStyle": {"opacity": 0.2},
            }
        )

    option = {
        "backgroundColor": "transparent",
        "title": {"text": title, **theme["title"]} if title else None,
        "tooltip": {**theme["tooltip"]},
        "legend": {
            "data": [d.get("name", f"Series {i + 1}") for i, d in enumerate(data)],
            "bottom": "5%",
            **theme["legend"],
        },
        "radar": {
            "indicator": indicators,
            "shape": "polygon",
            "splitNumber": 4,
            "axisName": {"color": colors["text_muted"], "fontSize": 12},
            "splitLine": {"lineStyle": {"color": colors["grid"]}},
            "splitArea": {"show": False},
            "axisLine": {"lineStyle": {"color": colors["grid"]}},
        },
        "series": [{"type": "radar", "data": series_data}],
    }

    st_echarts(options=option, height=height, key=key)
