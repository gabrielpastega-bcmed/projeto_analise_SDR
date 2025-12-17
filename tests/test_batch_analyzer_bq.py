"""Tests for BatchAnalyzer BigQuery interactions."""

from datetime import datetime
from unittest.mock import patch

import pytest

from src.batch_analyzer import BatchAnalyzer


class TestBatchAnalyzerBQ:
    """Testes para interações do BatchAnalyzer com BigQuery."""

    @pytest.fixture
    def mock_bq_client(self):
        with patch("google.cloud.bigquery.Client") as mock:
            yield mock

    @pytest.fixture
    def analyzer(self):
        return BatchAnalyzer()

    def test_save_to_bigquery_success(self, mock_bq_client, analyzer):
        """Testa salvamento bem-sucedido no BigQuery."""
        # Setup mock
        client_instance = mock_bq_client.return_value
        client_instance.insert_rows_json.return_value = []  # Sem erros

        results = [
            {
                "chat_id": "chat1",
                "agent": "Agent1",
                "analysis": {
                    "cx": {"sentiment": "positive"},
                    "sales": {"funnel_stage": "closed"},
                    "product": {"products_mentioned": ["p1"]},
                    "qa": {"script_adherence": True},
                },
            }
        ]
        week_start = datetime(2025, 1, 1)
        week_end = datetime(2025, 1, 7)

        count = analyzer.save_to_bigquery(results, week_start, week_end)

        assert count == 1
        client_instance.insert_rows_json.assert_called_once()
        args = client_instance.insert_rows_json.call_args
        rows = args[0][1]
        assert rows[0]["chat_id"] == "chat1"
        assert rows[0]["cx_sentiment"] == "positive"

    def test_save_to_bigquery_error(self, mock_bq_client, analyzer):
        """Testa erro ao salvar no BigQuery."""
        client_instance = mock_bq_client.return_value
        client_instance.insert_rows_json.return_value = [{"error": "some_error"}]

        results = [{"chat_id": "chat1", "analysis": {}}]
        count = analyzer.save_to_bigquery(results, datetime.now(), datetime.now())

        assert count == 0

    def test_save_to_bigquery_empty_results(self, mock_bq_client, analyzer):
        """Testa salvamento de lista vazia."""
        count = analyzer.save_to_bigquery([], datetime.now(), datetime.now())
        assert count == 0
        mock_bq_client.return_value.insert_rows_json.assert_not_called()

    def test_load_from_bigquery_with_date(self, mock_bq_client, analyzer):
        """Testa carregamento com data específica."""
        client_instance = mock_bq_client.return_value
        mock_results = [{"chat_id": "c1", "week_start": "2025-01-01"}]
        client_instance.query.return_value.result.return_value = mock_results

        week_start = datetime(2025, 1, 1)
        results = analyzer.load_from_bigquery(week_start)

        assert len(results) == 1
        assert results[0]["chat_id"] == "c1"

        args = client_instance.query.call_args
        assert "@week_start" in args[0][0]

    def test_load_from_bigquery_latest(self, mock_bq_client, analyzer):
        """Testa carregamento sem data (busca recente)."""
        client_instance = mock_bq_client.return_value
        client_instance.query.return_value.result.return_value = []

        analyzer.load_from_bigquery()

        args = client_instance.query.call_args
        assert "MAX(week_start)" in args[0][0]
