"""
Utilitários compartilhados para o dashboard multi-página.
"""

from datetime import datetime
from typing import Any, Dict, List, Union

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
    """Detecta se o Streamlit está em modo claro ou escuro."""
    try:
        theme_base = st.get_option("theme.base")
        if theme_base:
            return theme_base
    except Exception:
        pass
    return "dark"


def get_colors() -> Dict[str, Any]:
    """Retorna paleta de cores baseada no tema atual."""
    is_dark = get_theme_mode() == "dark"

    if is_dark:
        return {
            "primary": "#6366f1",
            "secondary": "#8b5cf6",
            "success": "#22c55e",
            "warning": "#f59e0b",
            "danger": "#ef4444",
            "info": "#06b6d4",
            "chart_bg": "rgba(0,0,0,0)",
            "text": "#e0e0e0",
            "gauge_steps": ["#555", "#777", "#999"],
        }
    else:
        return {
            "primary": "#4f46e5",
            "secondary": "#7c3aed",
            "success": "#16a34a",
            "warning": "#d97706",
            "danger": "#dc2626",
            "info": "#0891b2",
            "chart_bg": "rgba(255,255,255,0)",
            "text": "#1f2937",
            "gauge_steps": ["#ddd", "#bbb", "#999"],
        }


def apply_chart_theme(fig):
    """Aplica tema aos gráficos Plotly."""
    colors = get_colors()
    fig.update_layout(
        paper_bgcolor=colors["chart_bg"],
        plot_bgcolor=colors["chart_bg"],
    )
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
        return [tag.get("name", "") if isinstance(tag, dict) else str(tag) for tag in chat.tags]
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


def get_lead_origin(chat) -> str:
    """Extrai a origem do lead do customFields do contato."""
    try:
        if hasattr(chat, "contact") and chat.contact:
            custom_fields = getattr(chat.contact, "customFields", None)
            if custom_fields and isinstance(custom_fields, dict):
                origin = custom_fields.get("origem_do_negocio", None)
                # Tratar null, None, vazio, 'null', 'None' como 'Não Informado'
                if origin is None or origin == "" or origin == "null" or origin == "None":
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
        filtered = [c for c in filtered if c.firstMessageDate and start_date <= c.firstMessageDate.date() <= end_date]

    # Filtro por agente
    if filters.get("agents"):
        filtered = [c for c in filtered if hasattr(c, "agent") and c.agent and c.agent.name in filters["agents"]]

    # Filtro por origem
    if filters.get("origins"):
        filtered = [c for c in filtered if get_lead_origin(c) in filters["origins"]]

    # Filtro por tags
    if filters.get("tags"):
        filtered = [c for c in filtered if any(tag in get_chat_tags(c) for tag in filters["tags"])]

    # Filtro por horário comercial
    if filters.get("business_hours_only"):
        filtered = [c for c in filtered if hasattr(c, "firstMessageDate") and is_business_hour(c.firstMessageDate)]

    return filtered


# ================================================================
# CSS HELPERS
# ================================================================


def apply_custom_css():
    """Aplica CSS customizado baseado no tema."""
    is_dark = get_theme_mode() == "dark"

    if is_dark:
        css = """
        <style>
            .stMetric {
                background: linear-gradient(135deg, #1e3a5f 0%, #2d1b4e 100%);
                padding: 15px;
                border-radius: 10px;
                border: 1px solid #3d5a80;
            }
            .stMetric label { color: #a5b4fc !important; }
            .stMetric [data-testid="stMetricValue"] { color: #ffffff !important; }
            hr { border-color: #3d5a80; }
        </style>
        """
    else:
        css = """
        <style>
            .stMetric {
                background: linear-gradient(135deg, #e0e7ff 0%, #ede9fe 100%);
                padding: 15px;
                border-radius: 10px;
                border: 1px solid #c7d2fe;
            }
            .stMetric label { color: #4338ca !important; }
            .stMetric [data-testid="stMetricValue"] { color: #1e1b4b !important; }
            hr { border-color: #e5e7eb; }
        </style>
        """

    st.markdown(css, unsafe_allow_html=True)
