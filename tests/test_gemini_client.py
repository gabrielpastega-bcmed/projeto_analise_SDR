"""
Testes para o GeminiClient com mocks.
"""

import asyncio
import json
from unittest.mock import MagicMock, patch

import pytest

from src.gemini_client import GeminiClient

# ============================================================
# Tests for _parse_response
# ============================================================


def test_parse_response_clean_json():
    """Testa parse de JSON limpo."""
    client = GeminiClient.__new__(GeminiClient)

    result = client._parse_response('{"key": "value"}')

    assert result == {"key": "value"}


def test_parse_response_with_markdown_fences():
    """Testa parse de JSON com marcadores markdown."""
    client = GeminiClient.__new__(GeminiClient)

    result = client._parse_response('```json\n{"key": "value"}\n```')

    assert result == {"key": "value"}


def test_parse_response_with_plain_fences():
    """Testa parse de JSON com fences sem language."""
    client = GeminiClient.__new__(GeminiClient)

    result = client._parse_response('```\n{"key": "value"}\n```')

    assert result == {"key": "value"}


def test_parse_response_invalid_json():
    """Testa que JSON invalido levanta excecao."""
    client = GeminiClient.__new__(GeminiClient)

    with pytest.raises(json.JSONDecodeError):
        client._parse_response("not valid json")


# ============================================================
# Tests for analyze method
# ============================================================


@pytest.mark.asyncio
async def test_analyze_success():
    """Testa chamada bem-sucedida a analyze."""
    with patch("src.gemini_client.genai") as mock_genai:
        # Mock do modelo
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = '{"result": "success"}'
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model

        client = GeminiClient(api_key="fake_key")
        result = await client.analyze("Test prompt")

        assert result == {"result": "success"}


@pytest.mark.asyncio
async def test_analyze_json_error_retries():
    """Testa que erro de JSON causa retry."""
    with patch("src.gemini_client.genai") as mock_genai:
        mock_model = MagicMock()

        # Primeira chamada retorna JSON invalido, segunda retorna valido
        responses = [
            MagicMock(text="invalid json"),
            MagicMock(text='{"result": "success"}'),
        ]
        mock_model.generate_content.side_effect = responses
        mock_genai.GenerativeModel.return_value = mock_model

        client = GeminiClient(api_key="fake_key")
        result = await client.analyze("Test prompt", max_retries=2)

        # Deve retornar sucesso na segunda tentativa
        assert result == {"result": "success"}


@pytest.mark.asyncio
async def test_analyze_timeout_returns_error():
    """Testa que timeout retorna erro estruturado."""
    with patch("src.gemini_client.genai") as mock_genai:
        mock_model = MagicMock()

        # Simula timeout fazendo a chamada demorar
        async def slow_call(*args, **kwargs):
            await asyncio.sleep(10)  # Mais que o timeout

        mock_model.generate_content.side_effect = slow_call
        mock_genai.GenerativeModel.return_value = mock_model

        # Timeout de 0.1s para teste rapido
        client = GeminiClient(api_key="fake_key", timeout=1)

        # Patch run_in_executor para simular timeout
        with patch.object(asyncio, "timeout") as mock_timeout:
            mock_timeout.side_effect = asyncio.TimeoutError()

            result = await client.analyze("Test prompt", max_retries=1)

            assert "error" in result
            assert "Timeout" in result["error"] or "timeout" in result["error"].lower()


# ============================================================
# Tests for initialization
# ============================================================


def test_init_raises_without_api_key():
    """Testa que inicializacao sem API key levanta excecao."""
    with patch.dict("os.environ", {}, clear=True):
        with patch("src.gemini_client.os.getenv", return_value=None):
            with pytest.raises(ValueError, match="GEMINI_API_KEY"):
                GeminiClient()


def test_init_with_custom_timeout():
    """Testa inicializacao com timeout customizado."""
    with patch("src.gemini_client.genai"):
        client = GeminiClient(api_key="fake_key", timeout=120)

        assert client.timeout == 120


# ============================================================
# Tests for analyze_chat_full with validation
# ============================================================


@pytest.mark.asyncio
async def test_analyze_chat_full_returns_all_keys():
    """Testa que analyze_chat_full retorna todas as chaves."""
    with patch("src.gemini_client.genai") as mock_genai:
        mock_model = MagicMock()
        # Mock resposta válida
        mock_json = '{"sentiment": "positivo", "humanization_score": 4}'
        mock_response = MagicMock(text=mock_json)
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model

        client = GeminiClient(api_key="fake_key")
        result = await client.analyze_chat_full("Test transcript", validate=False)

        assert "cx" in result
        assert "product" in result
        assert "sales" in result
        assert "qa" in result


@pytest.mark.asyncio
async def test_analyze_chat_full_validation_adds_errors():
    """Testa que validação adiciona erros quando schema é inválido."""
    with patch("src.gemini_client.genai") as mock_genai:
        mock_model = MagicMock()
        # Mock resposta com valor inválido
        mock_response = MagicMock(text='{"sentiment": "muito_positivo"}')  # Valor inválido
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model

        client = GeminiClient(api_key="fake_key")
        result = await client.analyze_chat_full("Test transcript", validate=True)

        # Deve ter erros de validação em cx (sentiment inválido)
        assert "validation_errors" in result["cx"]
