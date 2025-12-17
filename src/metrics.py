"""Dataclasses for API response metrics."""

from dataclasses import dataclass


@dataclass
class APIMetrics:
    """Metrics for a single API call."""

    input_tokens: int
    output_tokens: int
    total_tokens: int
    latency_ms: int
    cost_usd: float
    model: str = "gemini-2.0-flash"

    @classmethod
    def calculate_cost(cls, input_tokens: int, output_tokens: int, model: str = "gemini-2.0-flash") -> float:
        """Calculate cost based on Gemini pricing.

        Gemini 2.0 Flash pricing (as of Dec 2024):
        - Input: $0.075 per 1M tokens
        - Output: $0.30 per 1M tokens
        """
        cost_per_1m_input = 0.075  # USD
        cost_per_1m_output = 0.30  # USD

        input_cost = (input_tokens / 1_000_000) * cost_per_1m_input
        output_cost = (output_tokens / 1_000_000) * cost_per_1m_output

        return input_cost + output_cost

    @classmethod
    def from_api_response(
        cls,
        input_tokens: int,
        output_tokens: int,
        latency_ms: int,
        model: str = "gemini-2.0-flash",
    ) -> "APIMetrics":
        """Create metrics from API response data."""
        total_tokens = input_tokens + output_tokens
        cost_usd = cls.calculate_cost(input_tokens, output_tokens, model)

        return cls(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            latency_ms=latency_ms,
            cost_usd=cost_usd,
            model=model,
        )


@dataclass
class BatchMetrics:
    """Aggregated metrics for a batch of API calls."""

    total_chats: int = 0
    cache_hits: int = 0
    api_calls: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cost_usd: float = 0.0
    avg_latency_ms: float = 0.0
    errors: int = 0

    @property
    def cache_hit_rate(self) -> float:
        """Calculate cache hit rate."""
        if self.total_chats == 0:
            return 0.0
        return self.cache_hits / self.total_chats

    @property
    def total_tokens(self) -> int:
        """Total tokens (input + output)."""
        return self.total_input_tokens + self.total_output_tokens

    def add_api_call(self, metrics: APIMetrics) -> None:
        """Add an API call's metrics to the batch."""
        self.api_calls += 1
        self.total_input_tokens += metrics.input_tokens
        self.total_output_tokens += metrics.output_tokens
        self.total_cost_usd += metrics.cost_usd

        # Update running average for latency
        prev_total = (self.api_calls - 1) * self.avg_latency_ms
        self.avg_latency_ms = (prev_total + metrics.latency_ms) / self.api_calls

    def add_cache_hit(self) -> None:
        """Record a cache hit."""
        self.cache_hits += 1

    def add_error(self) -> None:
        """Record an error."""
        self.errors += 1

    def summary(self) -> dict:
        """Get summary dict of metrics."""
        return {
            "total_chats": self.total_chats,
            "cache_hits": self.cache_hits,
            "cache_hit_rate": f"{self.cache_hit_rate:.1%}",
            "api_calls": self.api_calls,
            "total_tokens": self.total_tokens,
            "total_cost_usd": f"${self.total_cost_usd:.4f}",
            "avg_latency_ms": f"{self.avg_latency_ms:.0f}ms",
            "errors": self.errors,
        }
