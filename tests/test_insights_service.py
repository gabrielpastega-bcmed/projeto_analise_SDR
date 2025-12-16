"""
Testes para o InsightsService.
"""

from datetime import datetime

import pytest
import pytz

from src.insights_service import (
    aggregate_bigquery_results,
    aggregate_local_results,
    format_chat_transcript,
    list_local_analysis_files,
)
from src.models import Chat, Contact, Message, MessageSender

# ============================================================
# Fixtures
# ============================================================


@pytest.fixture
def sample_bigquery_results():
    """Resultados simulados do BigQuery."""
    return [
        {
            "chat_id": "chat1",
            "cx_sentiment": "positivo",
            "cx_nps_prediction": 8,
            "cx_humanization_score": 4,
            "sales_outcome": "convertido",
            "products_mentioned": ["equipamento_a", "ultrassom"],
        },
        {
            "chat_id": "chat2",
            "cx_sentiment": "neutro",
            "cx_nps_prediction": 6,
            "cx_humanization_score": 3,
            "sales_outcome": "em andamento",
            "products_mentioned": ["equipamento_a"],
        },
        {
            "chat_id": "chat3",
            "cx_sentiment": "negativo",
            "cx_nps_prediction": 3,
            "cx_humanization_score": 2,
            "sales_outcome": "perdido",
            "products_mentioned": [],
        },
    ]


@pytest.fixture
def sample_local_results():
    """Resultados simulados de analise local."""
    return [
        {
            "chat_id": "chat1",
            "analysis": {
                "cx": {"sentiment": "positivo", "nps_prediction": 9, "humanization_score": 5},
                "sales": {"outcome": "convertido"},
            },
        },
        {
            "chat_id": "chat2",
            "analysis": {
                "cx": {"sentiment": "neutro", "nps_prediction": 5, "humanization_score": 3},
                "sales": {"outcome": "em andamento"},
            },
        },
    ]


@pytest.fixture
def sample_chat():
    """Chat de exemplo para testes de formatacao."""
    return Chat(
        id="test_chat",
        number="123",
        channel="whatsapp",
        contact=Contact(id="c1", name="Cliente"),
        messages=[
            Message(
                id="m1",
                body="Ola, quero saber sobre equipamento_a",
                time=datetime(2024, 1, 15, 10, 0, 0, tzinfo=pytz.UTC),
                type="public",
                chatId="test_chat",
                sentBy=MessageSender(id="c1", type="contact", name="Maria"),
            ),
            Message(
                id="m2",
                body="Ola Maria! Temos varias opcoes.",
                time=datetime(2024, 1, 15, 10, 5, 0, tzinfo=pytz.UTC),
                type="public",
                chatId="test_chat",
                sentBy=MessageSender(id="a1", type="agent", name="Joao"),
            ),
        ],
        status="closed",
    )


# ============================================================
# Tests for aggregate_bigquery_results
# ============================================================


def test_aggregate_bigquery_results(sample_bigquery_results):
    """Testa agregacao de resultados do BigQuery."""
    result = aggregate_bigquery_results(sample_bigquery_results)

    assert result is not None
    assert result["total_analyzed"] == 3

    # CX
    assert result["cx"]["sentiment_distribution"]["positivo"] == 1
    assert result["cx"]["sentiment_distribution"]["neutro"] == 1
    assert result["cx"]["sentiment_distribution"]["negativo"] == 1
    assert result["cx"]["avg_nps_prediction"] == pytest.approx((8 + 6 + 3) / 3)

    # Sales
    assert result["sales"]["outcome_distribution"]["convertido"] == 1
    assert result["sales"]["conversion_rate"] == pytest.approx(100 / 3)

    # Products
    assert ("equipamento_a", 2) in result["product"]["top_products"]


def test_aggregate_bigquery_results_empty():
    """Testa agregacao com lista vazia."""
    result = aggregate_bigquery_results([])
    assert result is None


# ============================================================
# Tests for aggregate_local_results
# ============================================================


def test_aggregate_local_results(sample_local_results):
    """Testa agregacao de resultados locais."""
    result = aggregate_local_results(sample_local_results)

    assert result is not None
    assert result["total_analyzed"] == 2
    assert result["cx"]["sentiment_distribution"]["positivo"] == 1
    assert result["cx"]["sentiment_distribution"]["neutro"] == 1


def test_aggregate_local_results_empty():
    """Testa agregacao local com lista vazia."""
    result = aggregate_local_results([])
    assert result is None


# ============================================================
# Tests for format_chat_transcript
# ============================================================


def test_format_chat_transcript(sample_chat):
    """Testa formatacao de transcricao."""
    transcript = format_chat_transcript(sample_chat)

    assert "Maria" in transcript or "Cliente" in transcript
    assert "Joao" in transcript or "Agente" in transcript
    assert "equipamento_a" in transcript


def test_format_chat_transcript_without_timestamps(sample_chat):
    """Testa formatacao sem timestamps."""
    transcript = format_chat_transcript(sample_chat, include_timestamps=False)

    assert "[10:00]" not in transcript
    assert "equipamento_a" in transcript


def test_format_chat_transcript_empty_messages():
    """Testa formatacao com lista vazia de mensagens."""
    chat = Chat(
        id="empty",
        number="1",
        channel="web",
        contact=Contact(id="c1", name="Test"),
        messages=[],
        status="open",
    )
    transcript = format_chat_transcript(chat)
    assert transcript == ""


# ============================================================
# Tests for list_local_analysis_files
# ============================================================


def test_list_local_analysis_files_nonexistent_dir():
    """Testa listagem em diretorio inexistente."""
    files = list_local_analysis_files("/nonexistent/path")
    assert files == []
