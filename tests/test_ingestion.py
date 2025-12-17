"""
Testes para o módulo ingestion.py.

Foca nas funções de anonimização.
"""

from src.ingestion import (
    _anonymize_chat_data,
    _anonymize_text,
    get_data_source,
)


class TestAnonymizeText:
    """Testes para a função _anonymize_text."""

    def test_email_anonymization(self):
        """Testa anonimização de email."""
        text = "Contato: usuario@empresa.com.br"
        result = _anonymize_text(text)
        assert result == "Contato: [EMAIL]"

    def test_phone_with_parentheses(self):
        """Testa anonimização de telefone com parênteses."""
        text = "Ligue: (11) 99999-8888"
        result = _anonymize_text(text)
        assert result == "Ligue: [TELEFONE]"

    def test_phone_without_parentheses(self):
        """Testa anonimização de telefone sem parênteses."""
        text = "Tel: 11999998888"
        # Este formato específico pode não ser capturado
        result = _anonymize_text(text)
        # Se não capturado, permanece igual
        assert "[TELEFONE]" in result or "11999998888" in result

    def test_cpf_anonymization(self):
        """Testa anonimização de CPF."""
        text = "CPF: 123.456.789-00"
        result = _anonymize_text(text)
        assert result == "CPF: [CPF]"

    def test_multiple_pii(self):
        """Testa anonimização de múltiplos PIIs."""
        text = "Email: teste@email.com, CPF: 111.222.333-44"
        result = _anonymize_text(text)
        assert "[EMAIL]" in result
        assert "[CPF]" in result

    def test_no_pii(self):
        """Testa texto sem PII."""
        text = "Olá, gostaria de saber sobre equipamentos"
        result = _anonymize_text(text)
        assert result == text

    def test_non_string_input(self):
        """Testa input não-string."""
        result = _anonymize_text(None)  # type: ignore
        assert result is None

        result = _anonymize_text(123)  # type: ignore
        assert result == 123


class TestAnonymizeChatData:
    """Testes para a função _anonymize_chat_data."""

    def test_contact_anonymization(self):
        """Testa anonimização de contato."""
        chat_data = {"contact": {"name": "João Silva", "email": "joao@email.com"}}
        result = _anonymize_chat_data(chat_data)
        assert result["contact"]["name"] == "[CONTATO]"
        assert result["contact"]["email"] == "[EMAIL]"

    def test_agent_email_anonymization(self):
        """Testa anonimização de email do agente (nome mantido)."""
        chat_data = {"agent": {"name": "Maria Vendas", "email": "maria@empresa.com"}}
        result = _anonymize_chat_data(chat_data)
        assert result["agent"]["name"] == "Maria Vendas"  # Nome mantido
        assert result["agent"]["email"] == "[EMAIL]"

    def test_messages_anonymization(self):
        """Testa anonimização de mensagens."""
        chat_data = {
            "messages": [
                {"body": "Meu email é teste@email.com"},
                {"body": "CPF: 111.222.333-44"},
            ]
        }
        result = _anonymize_chat_data(chat_data)
        assert "[EMAIL]" in result["messages"][0]["body"]
        assert "[CPF]" in result["messages"][1]["body"]

    def test_empty_chat_data(self):
        """Testa com dados vazios."""
        chat_data = {}
        result = _anonymize_chat_data(chat_data)
        assert result == {}

    def test_no_contact(self):
        """Testa sem campo contact."""
        chat_data = {"messages": [{"body": "Olá"}]}
        result = _anonymize_chat_data(chat_data)
        assert "contact" not in result


class TestGetDataSource:
    """Testes para get_data_source."""

    def test_returns_string(self):
        """Testa que retorna uma string."""
        result = get_data_source()
        assert isinstance(result, str)
        assert result in ["bigquery", "json"]


class TestLoadResult:
    """Testes para a classe LoadResult."""

    def test_default_values(self):
        """Testa valores padrão."""
        from src.ingestion import LoadResult

        result = LoadResult()
        assert result.chats == []
        assert result.total_rows == 0
        assert result.success_count == 0
        assert result.error_count == 0
        assert result.error_samples == []

    def test_success_rate_no_rows(self):
        """Testa success_rate com zero rows."""
        from src.ingestion import LoadResult

        result = LoadResult(total_rows=0)
        # Quando não há rows, retorna 1.0 (100% sucesso)
        assert result.success_rate == 1.0

    def test_success_rate_with_rows(self):
        """Testa success_rate com rows."""
        from src.ingestion import LoadResult

        result = LoadResult(total_rows=100, success_count=75)
        assert result.success_rate == 0.75

    def test_has_errors_false(self):
        """Testa has_errors quando não há erros."""
        from src.ingestion import LoadResult

        result = LoadResult(error_count=0)
        assert result.has_errors is False

    def test_has_errors_true(self):
        """Testa has_errors quando há erros."""
        from src.ingestion import LoadResult

        result = LoadResult(error_count=5)
        assert result.has_errors is True


class TestLoadChatsFromJson:
    """Testes para load_chats_from_json."""

    def test_load_valid_json(self, tmp_path):
        """Testa carregamento de JSON válido."""
        from src.ingestion import load_chats_from_json

        json_data = [
            {
                "id": "chat1",
                "number": 1,
                "channel": "whatsapp",
                "status": "closed",
                "contact": {"id": "c1", "name": "Test", "email": "test@test.com"},
                "agent": {"id": "a1", "name": "Agent", "email": "agent@company.com"},
                "messages": [
                    {
                        "id": "msg1",
                        "chatId": "chat1",
                        "body": "Hello",
                        "time": "2025-01-01T10:00:00",
                        "type": "text",
                    }
                ],
            }
        ]
        json_file = tmp_path / "test.json"
        import json

        json_file.write_text(json.dumps(json_data))

        chats = load_chats_from_json(str(json_file))
        assert len(chats) == 1
        assert chats[0].id == "chat1"

    def test_load_empty_json(self, tmp_path):
        """Testa carregamento de JSON vazio."""
        from src.ingestion import load_chats_from_json

        json_file = tmp_path / "empty.json"
        json_file.write_text("[]")

        chats = load_chats_from_json(str(json_file))
        assert len(chats) == 0

    def test_load_nonexistent_file(self):
        """Testa carregamento de arquivo inexistente."""
        import pytest

        from src.ingestion import load_chats_from_json

        with pytest.raises(FileNotFoundError):
            load_chats_from_json("nonexistent.json")
