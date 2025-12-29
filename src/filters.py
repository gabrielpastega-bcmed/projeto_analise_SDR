"""
Advanced filter component for dashboards.

Provides reusable filtering UI with persistence.
"""

from datetime import datetime, timedelta
from typing import Any

import streamlit as st


class FilterComponent:
    """Advanced filter component with session state persistence."""

    def __init__(self, key_prefix: str = "filter"):
        """
        Initialize filter component.

        Args:
            key_prefix: Prefix for session state keys
        """
        self.key_prefix = key_prefix
        self._init_session_state()

    def _init_session_state(self) -> None:
        """Initialize filter values in session state if not present."""
        defaults: dict[str, Any] = {
            f"{self.key_prefix}_date_start": None,
            f"{self.key_prefix}_date_end": None,
            f"{self.key_prefix}_agents": [],
            f"{self.key_prefix}_origins": [],
            f"{self.key_prefix}_qualifications": [],
        }

        for key, default_value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = default_value

    def render(self) -> dict[str, Any]:
        """
        Render filter UI components.

        Returns:
            Dictionary with current filter values
        """
        st.markdown("### 🔍 Filtros Avançados")

        with st.expander("Filtrar Dados", expanded=False):
            # Date range filter
            col1, col2 = st.columns(2)

            with col1:
                date_start = st.date_input(
                    "Data Início",
                    value=st.session_state.get(f"{self.key_prefix}_date_start"),
                    key=f"{self.key_prefix}_date_start_input",
                    help="Selecione a data de início do período",
                )
                if date_start:
                    st.session_state[f"{self.key_prefix}_date_start"] = date_start

            with col2:
                date_end = st.date_input(
                    "Data Fim",
                    value=st.session_state.get(f"{self.key_prefix}_date_end"),
                    key=f"{self.key_prefix}_date_end_input",
                    help="Selecione a data final do período",
                )
                if date_end:
                    st.session_state[f"{self.key_prefix}_date_end"] = date_end

            # Quick date presets
            col1, col2, col3, col4 = st.columns(4)

            if col1.button("Hoje", use_container_width=True):
                today = datetime.now().date()
                st.session_state[f"{self.key_prefix}_date_start"] = today
                st.session_state[f"{self.key_prefix}_date_end"] = today
                st.rerun()

            if col2.button("Últimos 7 dias", use_container_width=True):
                today = datetime.now().date()
                week_ago = today - timedelta(days=7)
                st.session_state[f"{self.key_prefix}_date_start"] = week_ago
                st.session_state[f"{self.key_prefix}_date_end"] = today
                st.rerun()

            if col3.button("Últimos 30 dias", use_container_width=True):
                today = datetime.now().date()
                month_ago = today - timedelta(days=30)
                st.session_state[f"{self.key_prefix}_date_start"] = month_ago
                st.session_state[f"{self.key_prefix}_date_end"] = today
                st.rerun()

            if col4.button("🗑️ Limpar Filtros", use_container_width=True):
                self.clear_filters()
                st.rerun()

            # Get available options from data
            chats = st.session_state.get("chats", [])

            if chats:
                # Extract unique agents
                agents = sorted(set(c.agentName for c in chats if hasattr(c, "agentName") and c.agentName))

                # Extract unique origins
                from src.dashboard_utils import get_lead_origin

                origins = sorted(set(get_lead_origin(c) for c in chats if get_lead_origin(c)))

                # Qualifications
                qualifications = ["Qualificado", "Não Qualificado", "Não Identificado"]

                # Multi-select filters
                selected_agents = st.multiselect(
                    "👥 Filtrar por Agente",
                    options=agents,
                    default=st.session_state.get(f"{self.key_prefix}_agents", []),
                    key=f"{self.key_prefix}_agents_input",
                    help="Selecione um ou mais agentes",
                )
                st.session_state[f"{self.key_prefix}_agents"] = selected_agents

                selected_origins = st.multiselect(
                    "📍 Filtrar por Origem",
                    options=origins,
                    default=st.session_state.get(f"{self.key_prefix}_origins", []),
                    key=f"{self.key_prefix}_origins_input",
                    help="Selecione uma ou mais origens",
                )
                st.session_state[f"{self.key_prefix}_origins"] = selected_origins

                selected_quals = st.multiselect(
                    "🎯 Filtrar por Qualificação",
                    options=qualifications,
                    default=st.session_state.get(f"{self.key_prefix}_qualifications", []),
                    key=f"{self.key_prefix}_qualifications_input",
                    help="Selecione uma ou mais qualificações",
                )
                st.session_state[f"{self.key_prefix}_qualifications"] = selected_quals

        return self.get_current_filters()

    def get_current_filters(self) -> dict[str, Any]:
        """
        Get current filter values from session state.

        Returns:
            Dictionary with current filter values
        """
        return {
            "date_start": st.session_state.get(f"{self.key_prefix}_date_start"),
            "date_end": st.session_state.get(f"{self.key_prefix}_date_end"),
            "agents": st.session_state.get(f"{self.key_prefix}_agents", []),
            "origins": st.session_state.get(f"{self.key_prefix}_origins", []),
            "qualifications": st.session_state.get(f"{self.key_prefix}_qualifications", []),
        }

    def clear_filters(self) -> None:
        """Clear all filter values."""
        st.session_state[f"{self.key_prefix}_date_start"] = None
        st.session_state[f"{self.key_prefix}_date_end"] = None
        st.session_state[f"{self.key_prefix}_agents"] = []
        st.session_state[f"{self.key_prefix}_origins"] = []
        st.session_state[f"{self.key_prefix}_qualifications"] = []

    def apply_to_chats(self, chats: list) -> list:
        """
        Apply current filters to chat list.

        Args:
            chats: List of chat objects

        Returns:
            Filtered chat list
        """
        filters = self.get_current_filters()
        filtered = chats

        # Date range filter
        if filters["date_start"]:
            filtered = [
                c
                for c in filtered
                if hasattr(c, "timestamp") and c.timestamp and c.timestamp.date() >= filters["date_start"]
            ]

        if filters["date_end"]:
            filtered = [
                c
                for c in filtered
                if hasattr(c, "timestamp") and c.timestamp and c.timestamp.date() <= filters["date_end"]
            ]

        # Agent filter
        if filters["agents"]:
            filtered = [c for c in filtered if hasattr(c, "agentName") and c.agentName in filters["agents"]]

        # Origin filter
        if filters["origins"]:
            from src.dashboard_utils import get_lead_origin

            filtered = [c for c in filtered if get_lead_origin(c) in filters["origins"]]

        # Qualification filter
        if filters["qualifications"]:
            from src.dashboard_utils import classify_lead_qualification, get_chat_tags

            qual_map = {
                "Qualificado": "qualificado",
                "Não Qualificado": "não_qualificado",
                "Não Identificado": "não_identificado",
            }

            selected_quals = [qual_map[q] for q in filters["qualifications"] if q in qual_map]

            filtered = [c for c in filtered if classify_lead_qualification(get_chat_tags(c)) in selected_quals]

        return filtered

    def has_active_filters(self) -> bool:
        """Check if any filters are currently active."""
        filters = self.get_current_filters()
        return any(
            [
                filters["date_start"] is not None,
                filters["date_end"] is not None,
                len(filters["agents"]) > 0,
                len(filters["origins"]) > 0,
                len(filters["qualifications"]) > 0,
            ]
        )

    def get_filter_summary(self) -> str:
        """Get human-readable summary of active filters."""
        filters = self.get_current_filters()
        summaries = []

        if filters["date_start"]:
            summaries.append(f"Início: {filters['date_start'].strftime('%d/%m/%Y')}")

        if filters["date_end"]:
            summaries.append(f"Fim: {filters['date_end'].strftime('%d/%m/%Y')}")

        if filters["agents"]:
            summaries.append(f"{len(filters['agents'])} agente(s)")

        if filters["origins"]:
            summaries.append(f"{len(filters['origins'])} origem(ns)")

        if filters["qualifications"]:
            summaries.append(f"{len(filters['qualifications'])} qualificação(ões)")

        return " | ".join(summaries) if summaries else "Nenhum filtro ativo"
