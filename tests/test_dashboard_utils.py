"""
Testes para o módulo dashboard_utils.py.

Foca nas funções puras que não dependem do Streamlit.
"""

from datetime import datetime

from src.dashboard_utils import (
    TIMEZONE,
    classify_contact_context,
    classify_lead_qualification,
    is_bot_message,
    is_business_hour,
    is_human_agent_message,
)


class TestClassifyContactContext:
    """Testes para classify_contact_context."""

    def test_none_date(self):
        """Testa com data None."""
        result = classify_contact_context(None)
        assert result == "desconhecido"

    def test_business_hour_weekday(self):
        """Testa horário comercial em dia útil."""
        # Terça-feira 10:00
        dt = datetime(2024, 12, 10, 10, 0, 0)
        result = classify_contact_context(dt)
        assert result == "horario_comercial"

    def test_before_business_hours(self):
        """Testa antes do expediente."""
        # Segunda-feira 7:00
        dt = datetime(2024, 12, 9, 7, 0, 0)
        result = classify_contact_context(dt)
        assert result == "fora_expediente"

    def test_after_business_hours(self):
        """Testa após o expediente."""
        # Quarta-feira 19:00
        dt = datetime(2024, 12, 11, 19, 0, 0)
        result = classify_contact_context(dt)
        assert result == "fora_expediente"

    def test_weekend_saturday(self):
        """Testa final de semana (sábado)."""
        # Sábado 10:00
        dt = datetime(2024, 12, 14, 10, 0, 0)
        result = classify_contact_context(dt)
        assert result == "fora_expediente"

    def test_weekend_sunday(self):
        """Testa final de semana (domingo)."""
        # Domingo 14:00
        dt = datetime(2024, 12, 15, 14, 0, 0)
        result = classify_contact_context(dt)
        assert result == "fora_expediente"

    def test_timezone_aware_datetime(self):
        """Testa com datetime timezone-aware."""
        dt = TIMEZONE.localize(datetime(2024, 12, 10, 14, 0, 0))
        result = classify_contact_context(dt)
        assert result == "horario_comercial"

    def test_boundary_start_hour(self):
        """Testa exatamente no início do expediente."""
        dt = datetime(2024, 12, 10, 8, 0, 0)
        result = classify_contact_context(dt)
        assert result == "horario_comercial"

    def test_boundary_end_hour(self):
        """Testa exatamente no fim do expediente (18:00 é fora)."""
        dt = datetime(2024, 12, 10, 18, 0, 0)
        result = classify_contact_context(dt)
        assert result == "fora_expediente"


class TestIsBusinessHour:
    """Testes para is_business_hour."""

    def test_is_business(self):
        """Testa horário comercial retorna True."""
        dt = datetime(2024, 12, 10, 10, 0, 0)
        assert is_business_hour(dt) is True

    def test_not_business(self):
        """Testa fora do horário retorna False."""
        dt = datetime(2024, 12, 14, 10, 0, 0)  # Sábado
        assert is_business_hour(dt) is False


class TestIsBotMessage:
    """Testes para is_bot_message."""

    def test_bot_by_email(self):
        """Testa detecção de bot por email."""
        message = {"sentBy": {"email": "octabot@octachat.com"}, "type": "text"}
        assert is_bot_message(message) is True

    def test_bot_by_type(self):
        """Testa detecção de bot por tipo automático."""
        message = {"sentBy": {"email": "agent@company.com"}, "type": "automatic"}
        assert is_bot_message(message) is True

    def test_human_message(self):
        """Testa mensagem humana."""
        message = {"sentBy": {"email": "agent@company.com"}, "type": "text"}
        assert is_bot_message(message) is False

    def test_empty_message(self):
        """Testa mensagem vazia."""
        message = {}
        assert is_bot_message(message) is False


class TestIsHumanAgentMessage:
    """Testes para is_human_agent_message."""

    def test_human_agent(self):
        """Testa agente humano."""
        message = {
            "sentBy": {"type": "agent", "email": "agent@company.com"},
            "type": "text",
        }
        assert is_human_agent_message(message) is True

    def test_bot_agent(self):
        """Testa que bot não é agente humano."""
        message = {
            "sentBy": {"type": "agent", "email": "octabot@octachat.com"},
            "type": "text",
        }
        assert is_human_agent_message(message) is False

    def test_contact_message(self):
        """Testa que contato não é agente."""
        message = {"sentBy": {"type": "contact", "email": ""}, "type": "text"}
        assert is_human_agent_message(message) is False


class TestClassifyLeadQualification:
    """Testes para classify_lead_qualification."""

    def test_qualified_bigquery(self):
        """Testa lead qualificado (formato BigQuery)."""
        tags = ["Perfil Qualificado Plus"]
        assert classify_lead_qualification(tags) == "qualificado"

    def test_qualified_mock(self):
        """Testa lead qualificado (formato Mock)."""
        tags = ["Lead Qualificado"]
        assert classify_lead_qualification(tags) == "qualificado"

    def test_not_qualified(self):
        """Testa lead não qualificado."""
        tags = ["Perfil Indefinido"]
        assert classify_lead_qualification(tags) == "nao_qualificado"

    def test_outro(self):
        """Testa categoria outro."""
        tags = ["Procedimento"]
        assert classify_lead_qualification(tags) == "outro"

    def test_pos_vendas(self):
        """Testa pós-vendas."""
        tags = ["Pós-Vendas"]
        assert classify_lead_qualification(tags) == "outro"

    def test_empty_tags(self):
        """Testa sem tags."""
        tags = []
        assert classify_lead_qualification(tags) == "sem_tag"

    def test_unknown_tag(self):
        """Testa tag desconhecida."""
        tags = ["Tag Desconhecida"]
        assert classify_lead_qualification(tags) == "sem_tag"

    def test_multiple_tags_priority(self):
        """Testa prioridade com múltiplas tags."""
        # Primeira tag matching ganha
        tags = ["Perfil Qualificado", "Fora de perfil"]
        assert classify_lead_qualification(tags) == "qualificado"


class TestThemeAndColors:
    """Tests for UI helper functions."""

    def test_get_theme_mode_default(self, monkeypatch):
        """Test default theme mode."""
        from src import dashboard_utils

        # Mock streamlit
        class MockSt:
            def get_option(self, key):
                return "light"

        monkeypatch.setattr(dashboard_utils, "st", MockSt())
        assert dashboard_utils.get_theme_mode() == "light"

    def test_get_theme_mode_exception(self, monkeypatch):
        """Test theme mode fallback on exception."""
        from src import dashboard_utils

        class MockSt:
            def get_option(self, key):
                raise Exception("Error")

        monkeypatch.setattr(dashboard_utils, "st", MockSt())
        assert dashboard_utils.get_theme_mode() == "dark"

    def test_get_colors_dark(self, monkeypatch):
        """Test color palette for dark mode."""
        from src import dashboard_utils

        class MockSt:
            def get_option(self, key):
                return "dark"

        monkeypatch.setattr(dashboard_utils, "st", MockSt())
        colors = dashboard_utils.get_colors()
        assert colors["primary"] == "#6366f1"
        assert colors["text"] == "#e0e0e0"

    def test_get_colors_light(self, monkeypatch):
        """Test color palette for light mode."""
        from src import dashboard_utils

        class MockSt:
            def get_option(self, key):
                return "light"

        monkeypatch.setattr(dashboard_utils, "st", MockSt())
        colors = dashboard_utils.get_colors()
        assert colors["primary"] == "#4f46e5"
        assert colors["text"] == "#1f2937"
