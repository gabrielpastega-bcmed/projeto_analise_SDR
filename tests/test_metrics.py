"""Tests for metrics module - cost and latency tracking."""

import pytest

from src.metrics import APIMetrics, BatchMetrics


class TestAPIMetrics:
    """Tests for APIMetrics dataclass."""

    def test_calculate_cost_basic(self):
        """Test cost calculation with standard token counts."""
        # Gemini Flash pricing: $0.075/1M input, $0.30/1M output
        cost = APIMetrics.calculate_cost(input_tokens=1000, output_tokens=500)

        expected = (1000 / 1_000_000) * 0.075 + (500 / 1_000_000) * 0.30
        assert cost == pytest.approx(expected, rel=1e-6)
        assert cost == pytest.approx(0.000225, rel=1e-6)

    def test_calculate_cost_zero_tokens(self):
        """Test cost with zero tokens."""
        cost = APIMetrics.calculate_cost(input_tokens=0, output_tokens=0)
        assert cost == 0.0

    def test_calculate_cost_large_numbers(self):
        """Test cost calculation with large token counts."""
        # 1M tokens each
        cost = APIMetrics.calculate_cost(input_tokens=1_000_000, output_tokens=1_000_000)

        expected = 0.075 + 0.30  # $0.375
        assert cost == pytest.approx(expected, rel=1e-6)

    def test_from_api_response(self):
        """Test creating metrics from API response data."""
        metrics = APIMetrics.from_api_response(
            input_tokens=100, output_tokens=50, latency_ms=1500, model="gemini-2.0-flash"
        )

        assert metrics.input_tokens == 100
        assert metrics.output_tokens == 50
        assert metrics.total_tokens == 150
        assert metrics.latency_ms == 1500
        assert metrics.model == "gemini-2.0-flash"
        assert metrics.cost_usd > 0

    def test_total_tokens_calculation(self):
        """Test that total_tokens is sum of input+output."""
        metrics = APIMetrics.from_api_response(input_tokens=1000, output_tokens=500, latency_ms=2000)

        assert metrics.total_tokens == 1500

    def test_cost_calculation_in_from_api_response(self):
        """Test that cost is calculated correctly in constructor."""
        metrics = APIMetrics.from_api_response(input_tokens=10_000, output_tokens=5_000, latency_ms=1000)

        expected_cost = (10_000 / 1_000_000) * 0.075 + (5_000 / 1_000_000) * 0.30
        assert metrics.cost_usd == pytest.approx(expected_cost, rel=1e-6)


class TestBatchMetrics:
    """Tests for BatchMetrics dataclass."""

    def test_initial_state(self):
        """Test initial state of BatchMetrics."""
        metrics = BatchMetrics()

        assert metrics.total_chats == 0
        assert metrics.cache_hits == 0
        assert metrics.api_calls == 0
        assert metrics.total_input_tokens == 0
        assert metrics.total_output_tokens == 0
        assert metrics.total_cost_usd == 0.0
        assert metrics.avg_latency_ms == 0.0
        assert metrics.errors == 0

    def test_cache_hit_rate_zero_chats(self):
        """Test cache hit rate with zero chats."""
        metrics = BatchMetrics()
        assert metrics.cache_hit_rate == 0.0

    def test_cache_hit_rate_calculation(self):
        """Test cache hit rate calculation."""
        metrics = BatchMetrics(total_chats=100, cache_hits=30)
        assert metrics.cache_hit_rate == 0.3

    def test_cache_hit_rate_all_hits(self):
        """Test cache hit rate when all are hits."""
        metrics = BatchMetrics(total_chats=50, cache_hits=50)
        assert metrics.cache_hit_rate == 1.0

    def test_total_tokens_property(self):
        """Test total_tokens property."""
        metrics = BatchMetrics(total_input_tokens=10_000, total_output_tokens=5_000)
        assert metrics.total_tokens == 15_000

    def test_add_api_call(self):
        """Test adding API call metrics."""
        batch = BatchMetrics()
        api_metrics = APIMetrics.from_api_response(input_tokens=100, output_tokens=50, latency_ms=1500)

        batch.add_api_call(api_metrics)

        assert batch.api_calls == 1
        assert batch.total_input_tokens == 100
        assert batch.total_output_tokens == 50
        assert batch.total_cost_usd == api_metrics.cost_usd
        assert batch.avg_latency_ms == 1500

    def test_add_multiple_api_calls(self):
        """Test adding multiple API calls."""
        batch = BatchMetrics()

        # First call: 1000ms
        api1 = APIMetrics.from_api_response(input_tokens=100, output_tokens=50, latency_ms=1000)
        batch.add_api_call(api1)

        # Second call: 2000ms
        api2 = APIMetrics.from_api_response(input_tokens=200, output_tokens=100, latency_ms=2000)
        batch.add_api_call(api2)

        assert batch.api_calls == 2
        assert batch.total_input_tokens == 300
        assert batch.total_output_tokens == 150
        assert batch.avg_latency_ms == 1500  # (1000 + 2000) / 2

    def test_avg_latency_running_average(self):
        """Test that average latency is calculated correctly as running average."""
        batch = BatchMetrics()

        latencies = [1000, 2000, 3000]
        for latency in latencies:
            metrics = APIMetrics.from_api_response(input_tokens=100, output_tokens=50, latency_ms=latency)
            batch.add_api_call(metrics)

        expected_avg = sum(latencies) / len(latencies)
        assert batch.avg_latency_ms == expected_avg

    def test_add_cache_hit(self):
        """Test adding cache hit."""
        batch = BatchMetrics()
        batch.add_cache_hit()

        assert batch.cache_hits == 1

    def test_add_multiple_cache_hits(self):
        """Test adding multiple cache hits."""
        batch = BatchMetrics()
        batch.add_cache_hit()
        batch.add_cache_hit()
        batch.add_cache_hit()

        assert batch.cache_hits == 3

    def test_add_error(self):
        """Test adding error."""
        batch = BatchMetrics()
        batch.add_error()

        assert batch.errors == 1

    def test_summary_format(self):
        """Test summary dictionary format."""
        batch = BatchMetrics(
            total_chats=100,
            cache_hits=30,
            api_calls=70,
            total_input_tokens=70_000,
            total_output_tokens=35_000,
            total_cost_usd=0.15,
            avg_latency_ms=1500,
            errors=2,
        )

        summary = batch.summary()

        assert summary["total_chats"] == 100
        assert summary["cache_hits"] == 30
        assert summary["cache_hit_rate"] == "30.0%"
        assert summary["api_calls"] == 70
        assert summary["total_tokens"] == 105_000
        assert summary["total_cost_usd"] == "$0.1500"
        assert summary["avg_latency_ms"] == "1500ms"
        assert summary["errors"] == 2

    def test_summary_with_zero_values(self):
        """Test summary with zero values."""
        batch = BatchMetrics()
        summary = batch.summary()

        assert summary["cache_hit_rate"] == "0.0%"
        assert summary["total_cost_usd"] == "$0.0000"
        assert summary["avg_latency_ms"] == "0ms"

    def test_cost_accumulation(self):
        """Test that costs are accumulated correctly."""
        batch = BatchMetrics()

        # Add 3 API calls with known costs
        for _ in range(3):
            metrics = APIMetrics.from_api_response(
                input_tokens=1_000_000,  # $0.075
                output_tokens=1_000_000,  # $0.30
                latency_ms=1000,
            )
            batch.add_api_call(metrics)

        # Total: 3 × ($0.075 + $0.30) = $1.125
        expected_cost = 3 * (0.075 + 0.30)
        assert batch.total_cost_usd == pytest.approx(expected_cost, rel=1e-6)
