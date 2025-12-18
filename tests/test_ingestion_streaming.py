"""Tests for streaming BigQuery ingestion."""

import os
from unittest.mock import MagicMock, patch

import pytest

# Set default environment variables for testing
os.environ.setdefault("BIGQUERY_PROJECT_ID", "test-project")
os.environ.setdefault("BIGQUERY_DATASET", "test-dataset")
os.environ.setdefault("BIGQUERY_TABLE", "test-table")

pytest.importorskip("google.cloud.bigquery")
from src.ingestion import stream_chats_from_bigquery  # noqa: E402


class TestStreamChatsFromBigQuery:
    """Tests for stream_chats_from_bigquery generator."""

    @pytest.fixture
    def mock_bq_client(self):
        with patch("google.cloud.bigquery.Client") as mock:
            yield mock

    def test_stream_chats_uses_pagination(self, mock_bq_client, monkeypatch):
        """Test that streaming calls result() with page_size parameter."""
        monkeypatch.setenv("BIGQUERY_PROJECT_ID", "test-project")
        monkeypatch.setenv("BIGQUERY_DATASET", "test-dataset")
        monkeypatch.setenv("BIGQUERY_TABLE", "test-table")

        client_instance = mock_bq_client.return_value
        query_job = MagicMock()
        mock_result = MagicMock()
        mock_result.pages = []  # Empty pages for this test
        query_job.result.return_value = mock_result
        client_instance.query.return_value = query_job

        # Call with custom page_size
        list(stream_chats_from_bigquery(days=7, page_size=500))

        # Verify pagination was requested
        query_job.result.assert_called_once_with(page_size=500)
