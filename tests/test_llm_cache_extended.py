"""Comprehensive tests for LLM cache module."""

import json
from unittest.mock import MagicMock, patch

import redis  # type: ignore

from src.llm_cache import CacheStats, LLMCache


class TestCacheStats:
    """Tests for CacheStats Pydantic model."""

    def test_initial_stats(self):
        """Test initial state of cache stats."""
        stats = CacheStats()
        assert stats.hits == 0
        assert stats.misses == 0
        assert stats.total_requests == 0
        assert stats.hit_rate == 0.0
        assert stats.size_bytes == 0


class TestLLMCacheInit:
    """Tests for LLMCache initialization."""

    @patch("src.llm_cache.redis.from_url")
    def test_init_success(self, mock_redis):
        """Test successful Redis connection."""
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        mock_redis.return_value = mock_client

        cache = LLMCache(redis_url="redis://localhost:6379", enabled=True)

        assert cache.enabled is True
        assert cache.client is not None
        mock_redis.assert_called_once()
        mock_client.ping.assert_called_once()

    @patch("src.llm_cache.redis.from_url")
    def test_init_connection_failure(self, mock_redis):
        """Test cache disables when Redis connection fails."""
        mock_redis.side_effect = redis.ConnectionError("Cannot connect")

        cache = LLMCache(redis_url="redis://localhost:6379", enabled=True)

        assert cache.enabled is False
        assert cache.client is None

    @patch("src.llm_cache.redis.from_url")
    def test_init_ping_failure(self, mock_redis):
        """Test cache disables when ping fails."""
        mock_client = MagicMock()
        mock_client.ping.side_effect = redis.RedisError("Ping failed")
        mock_redis.return_value = mock_client

        cache = LLMCache(redis_url="redis://localhost:6379", enabled=True)

        assert cache.enabled is False

    def test_init_disabled(self):
        """Test cache initialization when disabled."""
        cache = LLMCache(enabled=False)

        assert cache.enabled is False
        assert cache.client is None


class TestLLMCacheGet:
    """Tests for cache GET operations."""

    @patch("src.llm_cache.redis.from_url")
    def test_get_cache_hit(self, mock_redis):
        """Test successful cache hit."""
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        test_data = {"result": "success", "analysis": {"score": 9}}
        mock_client.get.return_value = json.dumps(test_data)
        mock_redis.return_value = mock_client

        cache = LLMCache()
        result = cache.get("chat_123")

        assert result == test_data
        assert cache._stats.hits == 1
        assert cache._stats.misses == 0
        assert cache._stats.total_requests == 1

    @patch("src.llm_cache.redis.from_url")
    def test_get_cache_miss(self, mock_redis):
        """Test cache miss (key not found)."""
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        mock_client.get.return_value = None
        mock_redis.return_value = mock_client

        cache = LLMCache()
        result = cache.get("chat_456")

        assert result is None
        assert cache._stats.hits == 0
        assert cache._stats.misses == 1
        assert cache._stats.total_requests == 1

    @patch("src.llm_cache.redis.from_url")
    def test_get_when_disabled(self, mock_redis):
        """Test get returns None when cache is disabled."""
        cache = LLMCache(enabled=False)
        result = cache.get("chat_789")

        assert result is None
        mock_redis.assert_not_called()

    @patch("src.llm_cache.redis.from_url")
    def test_get_redis_error(self, mock_redis):
        """Test get handles Redis errors gracefully."""
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        mock_client.get.side_effect = redis.RedisError("Connection lost")
        mock_redis.return_value = mock_client

        cache = LLMCache()
        result = cache.get("chat_error")

        assert result is None

    @patch("src.llm_cache.redis.from_url")
    def test_get_json_decode_error(self, mock_redis):
        """Test get handles invalid JSON gracefully."""
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        mock_client.get.return_value = "invalid json {{"
        mock_redis.return_value = mock_client

        cache = LLMCache()
        result = cache.get("chat_badjson")

        assert result is None


class TestLLMCacheSet:
    """Tests for cache SET operations."""

    @patch("src.llm_cache.redis.from_url")
    def test_set_success(self, mock_redis):
        """Test successful cache set."""
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        mock_redis.return_value = mock_client

        cache = LLMCache(ttl_seconds=3600)
        test_data = {"result": "cached", "score": 10}
        success = cache.set("chat_123", test_data)

        assert success is True
        mock_client.setex.assert_called_once()
        # Verify TTL was passed
        call_args = mock_client.setex.call_args
        assert call_args[0][1] == 3600  # TTL

    @patch("src.llm_cache.redis.from_url")
    def test_set_custom_ttl(self, mock_redis):
        """Test set with custom TTL override."""
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        mock_redis.return_value = mock_client

        cache = LLMCache(ttl_seconds=3600)
        cache.set("chat_123", {"data": "test"}, ttl=7200)

        call_args = mock_client.setex.call_args
        assert call_args[0][1] == 7200  # Custom TTL

    @patch("src.llm_cache.redis.from_url")
    def test_set_when_disabled(self, mock_redis):
        """Test set returns False when cache disabled."""
        cache = LLMCache(enabled=False)
        success = cache.set("chat_123", {"data": "test"})

        assert success is False
        mock_redis.assert_not_called()

    @patch("src.llm_cache.redis.from_url")
    def test_set_redis_error(self, mock_redis):
        """Test set handles Redis errors gracefully."""
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        mock_client.setex.side_effect = redis.RedisError("Write failed")
        mock_redis.return_value = mock_client

        cache = LLMCache()
        success = cache.set("chat_error", {"data": "test"})

        assert success is False

    @patch("src.llm_cache.redis.from_url")
    def test_set_serialization_error(self, mock_redis):
        """Test set handles non-serializable data."""
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        mock_redis.return_value = mock_client

        cache = LLMCache()
        # Object with non-serializable content
        bad_data = {"func": lambda x: x}
        success = cache.set("chat_bad", bad_data)

        assert success is False


class TestLLMCacheDelete:
    """Tests for cache DELETE operations."""

    @patch("src.llm_cache.redis.from_url")
    def test_delete_success(self, mock_redis):
        """Test successful delete."""
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        mock_client.delete.return_value = 1  # 1 key deleted
        mock_redis.return_value = mock_client

        cache = LLMCache()
        deleted = cache.delete("chat_123")

        assert deleted is True
        mock_client.delete.assert_called_once()

    @patch("src.llm_cache.redis.from_url")
    def test_delete_key_not_found(self, mock_redis):
        """Test delete when key doesn't exist."""
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        mock_client.delete.return_value = 0  # No keys deleted
        mock_redis.return_value = mock_client

        cache = LLMCache()
        deleted = cache.delete("nonexistent")

        assert deleted is False

    @patch("src.llm_cache.redis.from_url")
    def test_delete_when_disabled(self, mock_redis):
        """Test delete when cache disabled."""
        cache = LLMCache(enabled=False)
        deleted = cache.delete("chat_123")

        assert deleted is False


class TestLLMCacheClearAll:
    """Tests for cache clear operations."""

    @patch("src.llm_cache.redis.from_url")
    def test_clear_all_success(self, mock_redis):
        """Test clearing all cache entries."""
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        mock_client.keys.return_value = ["llm:cache:key1", "llm:cache:key2"]
        mock_client.delete.return_value = 2
        mock_redis.return_value = mock_client

        cache = LLMCache()
        count = cache.clear_all()

        assert count == 2
        mock_client.keys.assert_called_with("llm:cache:*")

    @patch("src.llm_cache.redis.from_url")
    def test_clear_all_empty(self, mock_redis):
        """Test clear when no keys exist."""
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        mock_client.keys.return_value = []
        mock_redis.return_value = mock_client

        cache = LLMCache()
        count = cache.clear_all()

        assert count == 0


class TestLLMCacheStats:
    """Tests for cache statistics."""

    @patch("src.llm_cache.redis.from_url")
    def test_hit_rate_calculation(self, mock_redis):
        """Test hit rate is calculated correctly."""
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        mock_redis.return_value = mock_client

        cache = LLMCache()

        # Simulate 3 hits
        mock_client.get.return_value = json.dumps({"data": "test"})
        cache.get("chat1")
        cache.get("chat2")
        cache.get("chat3")

        # Simulate 1 miss
        mock_client.get.return_value = None
        cache.get("chat4")

        stats = cache.stats()
        assert stats.hits == 3
        assert stats.misses == 1
        assert stats.total_requests == 4
        assert stats.hit_rate == 0.75  # 3/4

    @patch("src.llm_cache.redis.from_url")
    def test_stats_when_disabled(self, mock_redis):
        """Test stats return zeros when cache disabled."""
        cache = LLMCache(enabled=False)
        stats = cache.stats()

        assert stats.hits == 0
        assert stats.misses == 0
        assert stats.hit_rate == 0.0


class TestCacheKeyGeneration:
    """Tests for cache key generation."""

    @patch("src.llm_cache.redis.from_url")
    def test_key_generation_consistency(self, mock_redis):
        """Test same chat_id generates same key."""
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        mock_redis.return_value = mock_client

        cache = LLMCache()

        # Generate key twice for same chat
        key1 = cache._generate_key("chat_123", "gemini-2.0-flash")
        key2 = cache._generate_key("chat_123", "gemini-2.0-flash")

        assert key1 == key2
        assert key1.startswith("llm:cache:")

    @patch("src.llm_cache.redis.from_url")
    def test_key_generation_different_models(self, mock_redis):
        """Test different models generate different keys."""
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        mock_redis.return_value = mock_client

        cache = LLMCache()

        key1 = cache._generate_key("chat_123", "gemini-2.0-flash")
        key2 = cache._generate_key("chat_123", "gemini-1.5-pro")

        assert key1 != key2
