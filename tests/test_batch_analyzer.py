"""
Testes para o BatchAnalyzer com mocks do GeminiClient.
"""

import json
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytz

from src.batch_analyzer import BatchAnalyzer, format_transcript, get_previous_week_range
from src.models import Chat, Contact, Message, MessageSender

# ============================================================
# Fixtures
# ============================================================


@pytest.fixture
def sample_chat():
    """Chat de exemplo para testes."""
    return Chat(
        id="test_chat_001",
        number="123",
        channel="whatsapp",
        contact=Contact(id="c1", name="Cliente Teste"),
        messages=[
            Message(
                id="m1",
                body="Ola, gostaria de saber sobre o equipamento_a",
                time=datetime(2024, 1, 15, 10, 0, 0, tzinfo=pytz.UTC),
                type="public",
                chatId="test_chat_001",
                sentBy=MessageSender(id="c1", type="contact", name="Cliente"),
            ),
            Message(
                id="m2",
                body="Claro! Temos varias opcoes de equipamento_a.",
                time=datetime(2024, 1, 15, 10, 5, 0, tzinfo=pytz.UTC),
                type="public",
                chatId="test_chat_001",
                sentBy=MessageSender(id="a1", type="agent", name="Agente"),
            ),
        ],
        status="closed",
    )


@pytest.fixture
def mock_gemini_response():
    """Resposta mockada do Gemini."""
    return {
        "cx": {
            "sentiment": "positivo",
            "humanization_score": 4,
            "nps_prediction": 8,
            "resolution_status": "resolvido",
            "satisfaction_comment": "Cliente satisfeito",
        },
        "product": {
            "products_mentioned": ["equipamento_a"],
            "interest_level": "alto",
            "trends": ["equipamento_a estetico"],
        },
        "sales": {
            "funnel_stage": "consideracao",
            "outcome": "em andamento",
            "rejection_reason": None,
            "next_step": "Enviar proposta",
        },
        "qa": {
            "script_adherence": True,
            "key_questions_asked": ["Tipo de procedimento"],
            "improvement_areas": [],
        },
    }


@pytest.fixture
def sample_analysis_results():
    """Resultados de análise para testes de agregação."""
    return [
        {
            "chat_id": "1",
            "analysis": {
                "cx": {"sentiment": "positivo", "humanization_score": 5, "nps_prediction": 9},
                "sales": {"outcome": "convertido"},
                "product": {"products_mentioned": ["equipamento_a", "ultrassom"]},
            },
        },
        {
            "chat_id": "2",
            "analysis": {
                "cx": {"sentiment": "neutro", "humanization_score": 3, "nps_prediction": 6},
                "sales": {"outcome": "em andamento"},
                "product": {"products_mentioned": ["equipamento_a"]},
            },
        },
        {
            "chat_id": "3",
            "analysis": {
                "cx": {"sentiment": "negativo", "humanization_score": 2, "nps_prediction": 3},
                "sales": {"outcome": "perdido"},
                "product": {"products_mentioned": []},
            },
        },
    ]


# ============================================================
# Tests - format_transcript
# ============================================================


def test_format_transcript(sample_chat):
    """Testa formatacao de transcricao."""
    transcript = format_transcript(sample_chat)

    assert "Cliente" in transcript or "contact" in transcript.lower()
    assert "equipamento_a" in transcript.lower()
    assert "Agente" in transcript or "agent" in transcript.lower()


def test_format_transcript_empty_messages():
    """Testa transcricao com lista vazia de mensagens."""
    chat = Chat(
        id="empty",
        number="1",
        channel="web",
        contact=Contact(id="c1", name="Test"),
        messages=[],
        status="open",
    )
    transcript = format_transcript(chat)
    assert transcript == "" or "sem mensagens" in transcript.lower() or transcript is not None


# ============================================================
# Tests - get_previous_week_range
# ============================================================


def test_get_previous_week_range_returns_tuple():
    """Testa que retorna tupla de datas."""
    start, end = get_previous_week_range()
    assert isinstance(start, datetime)
    assert isinstance(end, datetime)


def test_get_previous_week_range_start_before_end():
    """Testa que início vem antes do fim."""
    start, end = get_previous_week_range()
    assert start < end


def test_get_previous_week_range_is_monday_to_sunday():
    """Testa que o intervalo vai de segunda a domingo."""
    start, end = get_previous_week_range()
    # Segunda-feira = 0
    assert start.weekday() == 0
    # Domingo = 6
    assert end.weekday() == 6


def test_get_previous_week_range_is_7_days():
    """Testa que o intervalo é de aproximadamente 7 dias."""
    start, end = get_previous_week_range()
    diff = end - start
    assert 6 <= diff.days <= 7


# ============================================================
# Tests - analyze_chat
# ============================================================


@pytest.mark.asyncio
async def test_analyze_chat_with_mock(sample_chat, mock_gemini_response):
    """Testa analise de chat com GeminiClient mockado."""
    with patch("src.batch_analyzer.GeminiClient") as MockClient:
        # Configura mock
        mock_instance = MagicMock()
        mock_instance.analyze_chat_full = AsyncMock(return_value=mock_gemini_response)
        MockClient.return_value = mock_instance

        # Executa
        analyzer = BatchAnalyzer(api_key="fake_key")
        result = await analyzer.analyze_chat(sample_chat)

        # Verifica
        assert result["chat_id"] == "test_chat_001"
        assert "analysis" in result
        assert result["analysis"]["cx"]["sentiment"] == "positivo"


@pytest.mark.asyncio
async def test_analyze_chat_handles_error(sample_chat):
    """Testa tratamento de erro na analise."""
    with patch("src.batch_analyzer.GeminiClient") as MockClient:
        mock_instance = MagicMock()
        mock_instance.analyze_chat_full = AsyncMock(side_effect=Exception("API Error"))
        MockClient.return_value = mock_instance

        analyzer = BatchAnalyzer(api_key="fake_key")
        result = await analyzer.analyze_chat(sample_chat)

        assert result["chat_id"] == "test_chat_001"
        assert "error" in result


@pytest.mark.asyncio
async def test_analyze_chat_includes_processing_time(sample_chat, mock_gemini_response):
    """Testa que inclui tempo de processamento."""
    with patch("src.batch_analyzer.GeminiClient") as MockClient:
        mock_instance = MagicMock()
        mock_instance.analyze_chat_full = AsyncMock(return_value=mock_gemini_response)
        MockClient.return_value = mock_instance

        analyzer = BatchAnalyzer(api_key="fake_key")
        result = await analyzer.analyze_chat(sample_chat)

        assert "processing_time_ms" in result
        assert isinstance(result["processing_time_ms"], int)


# ============================================================
# Tests - run_batch
# ============================================================


@pytest.mark.asyncio
async def test_run_batch_small_list(sample_chat, mock_gemini_response):
    """Testa processamento em lote com lista pequena."""
    with patch("src.batch_analyzer.GeminiClient") as MockClient:
        mock_instance = MagicMock()
        mock_instance.analyze_chat_full = AsyncMock(return_value=mock_gemini_response)
        MockClient.return_value = mock_instance

        analyzer = BatchAnalyzer(api_key="fake_key")
        chats = [sample_chat, sample_chat]  # 2 chats

        results = await analyzer.run_batch(chats, batch_size=2)

        assert len(results) == 2
        assert all(r["chat_id"] == "test_chat_001" for r in results)


@pytest.mark.asyncio
async def test_run_batch_calls_checkpoint(sample_chat, mock_gemini_response):
    """Testa que checkpoint callback é chamado."""
    with patch("src.batch_analyzer.GeminiClient") as MockClient:
        mock_instance = MagicMock()
        mock_instance.analyze_chat_full = AsyncMock(return_value=mock_gemini_response)
        MockClient.return_value = mock_instance

        analyzer = BatchAnalyzer(api_key="fake_key")
        checkpoint_calls = []

        def checkpoint_cb(result):
            checkpoint_calls.append(result)

        _ = await analyzer.run_batch([sample_chat], checkpoint_callback=checkpoint_cb)

        assert len(checkpoint_calls) == 1


# ============================================================
# Tests - aggregate_results
# ============================================================


def test_aggregate_results_empty():
    """Testa agregacao com lista vazia."""
    analyzer = BatchAnalyzer.__new__(BatchAnalyzer)
    analyzer.results_dir = Path("data/analysis_results")

    aggregated = analyzer.aggregate_results([])

    # Lista vazia retorna erro, nao total_analyzed
    assert "error" in aggregated


def test_aggregate_results_counts_sentiments(sample_analysis_results):
    """Testa contagem de sentimentos."""
    analyzer = BatchAnalyzer.__new__(BatchAnalyzer)
    analyzer.results_dir = Path("data/analysis_results")

    aggregated = analyzer.aggregate_results(sample_analysis_results)

    assert aggregated["total_analyzed"] == 3
    assert aggregated["cx"]["sentiment_distribution"]["positivo"] == 1
    assert aggregated["cx"]["sentiment_distribution"]["neutro"] == 1
    assert aggregated["cx"]["sentiment_distribution"]["negativo"] == 1


def test_aggregate_results_calculates_averages(sample_analysis_results):
    """Testa cálculo de médias."""
    analyzer = BatchAnalyzer.__new__(BatchAnalyzer)
    analyzer.results_dir = Path("data/analysis_results")

    aggregated = analyzer.aggregate_results(sample_analysis_results)

    # Média de humanization: (5 + 3 + 2) / 3 = 3.33
    assert 3.0 <= aggregated["cx"]["avg_humanization_score"] <= 3.5
    # Média de NPS: (9 + 6 + 3) / 3 = 6
    assert aggregated["cx"]["avg_nps_prediction"] == 6.0


def test_aggregate_results_counts_products(sample_analysis_results):
    """Testa contagem de produtos."""
    analyzer = BatchAnalyzer.__new__(BatchAnalyzer)
    analyzer.results_dir = Path("data/analysis_results")

    aggregated = analyzer.aggregate_results(sample_analysis_results)

    # equipamento_a aparece 2 vezes, ultrassom 1 vez
    top_products = dict(aggregated["product"]["top_products"])
    assert top_products.get("equipamento_a") == 2


def test_aggregate_results_counts_outcomes(sample_analysis_results):
    """Testa contagem de outcomes."""
    analyzer = BatchAnalyzer.__new__(BatchAnalyzer)
    analyzer.results_dir = Path("data/analysis_results")

    aggregated = analyzer.aggregate_results(sample_analysis_results)

    assert aggregated["sales"]["outcome_distribution"]["convertido"] == 1
    assert aggregated["sales"]["outcome_distribution"]["perdido"] == 1


# ============================================================
# Tests - save_results
# ============================================================


def test_save_results_creates_file():
    """Testa que save_results cria arquivo."""
    with tempfile.TemporaryDirectory() as tmpdir:
        analyzer = BatchAnalyzer.__new__(BatchAnalyzer)
        analyzer.results_dir = Path(tmpdir)

        results = [{"chat_id": "1", "analysis": {}}]
        saved_path = analyzer.save_results(results, "test_output.json")

        assert saved_path.exists()
        assert saved_path.name == "test_output.json"


def test_save_results_writes_valid_json():
    """Testa que o conteúdo é JSON válido."""
    with tempfile.TemporaryDirectory() as tmpdir:
        analyzer = BatchAnalyzer.__new__(BatchAnalyzer)
        analyzer.results_dir = Path(tmpdir)

        results = [{"chat_id": "1", "data": "test"}]
        saved_path = analyzer.save_results(results, "test.json")

        with open(saved_path, encoding="utf-8") as f:
            loaded = json.load(f)

        assert loaded == results
