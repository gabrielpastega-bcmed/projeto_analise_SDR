"""Tests for BatchAnalyzer streaming and chunked write functionality."""

import os
from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest

# Set default environment variables for testing
os.environ.setdefault("GEMINI_API_KEY", "test-key-12345")
os.environ.setdefault("BIGQUERY_PROJECT_ID", "test-project")
os.environ.setdefault("BIGQUERY_DATASET", "test-dataset")
os.environ.setdefault("BIGQUERY_TABLE", "test-table")

pytest.importorskip("google.cloud.bigquery")
from src.batch_analyzer import BatchAnalyzer  # noqa: E402
from src.models import Chat  # noqa: E402


class TestBatchAnalyzerStreaming:
    """Tests for BatchAnalyzer streaming capabilities."""

    @pytest.fixture
    def mock_bq_client(self):
        with patch("google.cloud.bigquery.Client") as mock:
            yield mock

    @pytest.fixture
    def analyzer(self):
        return BatchAnalyzer()

    @pytest.fixture
    def sample_chat(self):
        """Create a sample Chat object."""
        return Chat(
            id="chat1",
            number=1,
            channel="whatsapp",
            status="closed",
            contact={"id": "c1", "name": "Test"},
            agent={"id": "a1", "name": "Agent"},
            messages=[],
        )

    def test_save_to_bigquery_chunked_writes(self, mock_bq_client, analyzer):
        """Test that save_to_bigquery splits large batches into chunks."""
        client_instance = mock_bq_client.return_value
        client_instance.insert_rows_json.return_value = []  # No errors

        # Create 1200 results (should split into 3 chunks with chunk_size=500)
        results = []
        for i in range(1200):
            results.append(
                {
                    "chat_id": f"chat{i}",
                    "agent": "Agent1",
                    "analysis": {
                        "cx": {"sentiment": "positive"},
                        "sales": {"funnel_stage": "closed"},
                        "product": {"products_mentioned": []},
                        "qa": {"script_adherence": True},
                    },
                }
            )

        week_start = datetime(2025, 1, 1)
        week_end = datetime(2025, 1, 7)

        count = analyzer.save_to_bigquery(results, week_start, week_end, chunk_size=500)

        # Verify: should have made 3 calls (1200 / 500 = 2.4 -> 3 chunks)
        assert client_instance.insert_rows_json.call_count == 3
        assert count == 1200

        # Verify chunk sizes
        calls = client_instance.insert_rows_json.call_args_list
        assert len(calls[0][0][1]) == 500  # First chunk: 500
        assert len(calls[1][0][1]) == 500  # Second chunk: 500
        assert len(calls[2][0][1]) == 200  # Third chunk: 200

    def test_save_to_bigquery_chunk_size_configurable(self, mock_bq_client, analyzer):
        """Test that chunk_size parameter is respected."""
        client_instance = mock_bq_client.return_value
        client_instance.insert_rows_json.return_value = []

        # Create 250 results
        results = [
            {
                "chat_id": f"chat{i}",
                "agent": "Agent",
                "analysis": {
                    "cx": {},
                    "sales": {},
                    "product": {},
                    "qa": {},
                },
            }
            for i in range(250)
        ]

        # Use chunk_size=100
        analyzer.save_to_bigquery(
            results,
            datetime.now(),
            datetime.now(),
            chunk_size=100,
        )

        # Should be 3 chunks (100, 100, 50)
        assert client_instance.insert_rows_json.call_count == 3

    def test_save_to_bigquery_partial_failure_handling(self, mock_bq_client, analyzer):
        """Test behavior when some chunks fail."""
        client_instance = mock_bq_client.return_value

        # First chunk succeeds, second fails, third succeeds
        client_instance.insert_rows_json.side_effect = [
            [],  # Success
            [{"error": "some_error"}],  # Failure
            [],  # Success
        ]

        results = [
            {
                "chat_id": f"chat{i}",
                "agent": "Agent",
                "analysis": {"cx": {}, "sales": {}, "product": {}, "qa": {}},
            }
            for i in range(150)
        ]

        count = analyzer.save_to_bigquery(
            results,
            datetime.now(),
            datetime.now(),
            chunk_size=50,
        )

        # Should return count of successfully inserted rows (100 out of 150)
        assert count == 100

    @pytest.mark.asyncio
    async def test_run_batch_with_generator(self, analyzer, sample_chat):
        """Test that run_batch accepts and processes generators."""

        # Create a generator of chats
        def chat_generator():
            for i in range(5):
                yield Chat(
                    id=f"chat{i}",
                    number=i,
                    channel="whatsapp",
                    status="closed",
                    contact={"id": f"c{i}", "name": "Test"},
                    agent={"id": f"a{i}", "name": "Agent"},
                    messages=[],
                )

        # Mock analyze_chat to avoid actual API calls
        analyzer.analyze_chat = AsyncMock(
            side_effect=lambda chat: {
                "chat_id": chat.id,
                "agent": "Agent",
                "analysis": {"cx": {}, "sales": {}, "product": {}, "qa": {}},
                "processing_time_ms": 100,
            }
        )

        # Process generator
        results = await analyzer.run_batch(chat_generator())

        assert len(results) == 5
        assert results[0]["chat_id"] == "chat0"
        assert results[4]["chat_id"] == "chat4"

    @pytest.mark.asyncio
    async def test_run_batch_with_list_backward_compat(self, analyzer):
        """Test that run_batch still works with lists (backward compatibility)."""

        # Create list of chats
        chats = [
            Chat(
                id=f"chat{i}",
                number=i,
                channel="whatsapp",
                status="closed",
                contact={"id": f"c{i}", "name": "Test"},
                agent={"id": f"a{i}", "name": "Agent"},
                messages=[],
            )
            for i in range(3)
        ]

        # Mock analyze_chat
        analyzer.analyze_chat = AsyncMock(
            side_effect=lambda chat: {
                "chat_id": chat.id,
                "agent": "Agent",
                "analysis": {"cx": {}, "sales": {}, "product": {}, "qa": {}},
                "processing_time_ms": 100,
            }
        )

        # Process list (original behavior)
        results = await analyzer.run_batch(chats)

        assert len(results) == 3
        assert all("chat_id" in r for r in results)

    @pytest.mark.asyncio
    async def test_run_batch_generator_progress_callback(self, analyzer):
        """Test that progress callback works correctly with generators."""

        def chat_generator():
            for i in range(3):
                yield Chat(
                    id=f"chat{i}",
                    number=i,
                    channel="whatsapp",
                    status="closed",
                    contact={"id": f"c{i}", "name": "Test"},
                    agent={"id": f"a{i}", "name": "Agent"},
                    messages=[],
                )

        analyzer.analyze_chat = AsyncMock(
            side_effect=lambda chat: {
                "chat_id": chat.id,
                "analysis": {"cx": {}, "sales": {}, "product": {}, "qa": {}},
                "processing_time_ms": 100,
            }
        )

        progress_calls = []

        def progress_cb(current, total):
            progress_calls.append((current, total))

        await analyzer.run_batch(chat_generator(), progress_callback=progress_cb)

        # With generator, total is unknown, so current == total
        assert len(progress_calls) == 3
        assert progress_calls[0] == (1, 1)
        assert progress_calls[1] == (2, 2)
        assert progress_calls[2] == (3, 3)

    @pytest.mark.asyncio
    async def test_run_batch_list_progress_callback(self, analyzer):
        """Test that progress callback works correctly with lists."""

        chats = [
            Chat(
                id=f"chat{i}",
                number=i,
                channel="whatsapp",
                status="closed",
                contact={"id": f"c{i}", "name": "Test"},
                agent={"id": f"a{i}", "name": "Agent"},
                messages=[],
            )
            for i in range(3)
        ]

        analyzer.analyze_chat = AsyncMock(
            side_effect=lambda chat: {
                "chat_id": chat.id,
                "analysis": {"cx": {}, "sales": {}, "product": {}, "qa": {}},
                "processing_time_ms": 100,
            }
        )

        progress_calls = []

        def progress_cb(current, total):
            progress_calls.append((current, total))

        await analyzer.run_batch(chats, progress_callback=progress_cb)

        # With list, total is known
        assert len(progress_calls) == 3
        assert progress_calls[0] == (1, 3)
        assert progress_calls[1] == (2, 3)
        assert progress_calls[2] == (3, 3)
