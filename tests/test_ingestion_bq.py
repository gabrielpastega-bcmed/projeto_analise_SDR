"""Tests for ingestion BigQuery functions."""

import os
from unittest.mock import patch

import pytest

# Set default environment variables for testing (before imports)
os.environ.setdefault("BIGQUERY_PROJECT_ID", "test-project")
os.environ.setdefault("BIGQUERY_DATASET_ID", "test-dataset")
os.environ.setdefault("BIGQUERY_TABLE_ID", "test-table")

pytest.importorskip("google.cloud.bigquery")
from src.ingestion import load_chats_from_bigquery  # noqa: E402


class TestLoadChatsFromBigQuery:
    """Tests for load_chats_from_bigquery."""

    @pytest.fixture
    def mock_bq_client(self):
        with patch("google.cloud.bigquery.Client") as mock:
            yield mock

    def test_load_chats_from_bigquery_with_days(self, mock_bq_client, monkeypatch):
        """Test loading chats with days parameter."""

        # Mock environment
        monkeypatch.setenv("BIGQUERY_PROJECT_ID", "test-project")
        monkeypatch.setenv("BIGQUERY_DATASET_ID", "test-dataset")
        monkeypatch.setenv("BIGQUERY_TABLE_ID", "test-table")

        # Mock BigQuery response
        client_instance = mock_bq_client.return_value
        mock_row = {
            "id": "chat1",
            "number": 1,
            "channel": "whatsapp",
            "status": "closed",
            "contact": {"id": "c1", "name": "Test", "email": "test@test.com"},
            "agent": {"id": "a1", "name": "Agent"},
            "messages": [],
        }
        client_instance.query.return_value.result.return_value = [mock_row]

        chats = load_chats_from_bigquery(days=7)

        assert len(chats) == 1
        assert chats[0].id == "chat1"

    def test_load_chats_from_bigquery_with_limit(self, mock_bq_client, monkeypatch):
        """Test loading with limit parameter."""

        monkeypatch.setenv("BIGQUERY_PROJECT_ID", "test-project")
        monkeypatch.setenv("BIGQUERY_DATASET_ID", "test-dataset")
        monkeypatch.setenv("BIGQUERY_TABLE_ID", "test-table")

        client_instance = mock_bq_client.return_value
        client_instance.query.return_value.result.return_value = []

        load_chats_from_bigquery(limit=100)

        query_call = client_instance.query.call_args[0][0]
        assert "LIMIT" in query_call
