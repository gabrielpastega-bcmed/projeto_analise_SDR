"""LLM response caching using Redis."""

import hashlib
import json
import logging
from typing import Any, Dict, Optional

import redis  # type: ignore
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class CacheStats(BaseModel):
    """Cache statistics."""

    hits: int = 0
    misses: int = 0
    total_requests: int = 0
    hit_rate: float = 0.0
    size_bytes: int = 0


class LLMCache:
    """Redis-based cache for LLM responses.

    Supports both local Redis (Docker) and Railway Redis instances.
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        ttl_seconds: int = 86400,  # 24 hours
        enabled: bool = True,
    ):
        """Initialize LLM cache.

        Args:
            redis_url: Redis connection URL (works with Docker local or Railway)
            ttl_seconds: Time-to-live for cached entries (default 24h)
            enabled: Whether caching is enabled
        """
        self.enabled = enabled
        self.ttl_seconds = ttl_seconds
        self._stats = CacheStats()
        self.client = None

        if not enabled:
            logger.info("LLM cache disabled")
            return

        try:
            self.client = redis.from_url(
                redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
            )
            # Test connection
            self.client.ping()
            logger.info(f"LLM cache connected to Redis: {redis_url}")
        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {e}. Cache disabled.")
            self.enabled = False
            self.client = None

    def _generate_key(self, chat_id: str, model: str = "gemini-2.0-flash") -> str:
        """Generate cache key from chat_id and model.

        Args:
            chat_id: Unique chat identifier
            model: LLM model name

        Returns:
            Cache key (hash of chat_id + model)
        """
        # Hash to keep keys short and consistent
        content = f"{chat_id}:{model}"
        hash_digest = hashlib.sha256(content.encode()).hexdigest()[:16]
        return f"llm:cache:{hash_digest}"

    def get(self, chat_id: str, model: str = "gemini-2.0-flash") -> Optional[Dict[str, Any]]:
        """Get cached LLM response.

        Args:
            chat_id: Chat identifier
            model: LLM model name

        Returns:
            Cached response dict or None if not found
        """
        if not self.enabled or not self.client:
            return None

        self._stats.total_requests += 1

        try:
            key = self._generate_key(chat_id, model)
            cached = self.client.get(key)

            if cached:
                self._stats.hits += 1
                self._update_hit_rate()
                logger.debug(f"Cache HIT for chat {chat_id}")
                return json.loads(cached)

            self._stats.misses += 1
            self._update_hit_rate()
            logger.debug(f"Cache MISS for chat {chat_id}")
            return None

        except (redis.RedisError, json.JSONDecodeError) as e:
            logger.error(f"Cache GET error: {e}")
            return None

    def set(
        self,
        chat_id: str,
        response: Dict[str, Any],
        model: str = "gemini-2.0-flash",
        ttl: Optional[int] = None,
    ) -> bool:
        """Store LLM response in cache.

        Args:
            chat_id: Chat identifier
            response: LLM response to cache
            model: LLM model name
            ttl: Optional TTL override (seconds)

        Returns:
            True if successfully cached, False otherwise
        """
        if not self.enabled or not self.client:
            return False

        try:
            key = self._generate_key(chat_id, model)
            value = json.dumps(response)
            ttl_seconds = ttl or self.ttl_seconds

            self.client.setex(key, ttl_seconds, value)
            logger.debug(f"Cache SET for chat {chat_id} (TTL: {ttl_seconds}s)")
            return True

        except (redis.RedisError, TypeError) as e:
            logger.error(f"Cache SET error: {e}")
            return False

    def delete(self, chat_id: str, model: str = "gemini-2.0-flash") -> bool:
        """Delete cached response.

        Args:
            chat_id: Chat identifier
            model: LLM model name

        Returns:
            True if deleted, False otherwise
        """
        if not self.enabled or not self.client:
            return False

        try:
            key = self._generate_key(chat_id, model)
            deleted = self.client.delete(key)
            return deleted > 0
        except redis.RedisError as e:
            logger.error(f"Cache DELETE error: {e}")
            return False

    def clear_all(self) -> int:
        """Clear all cached LLM responses.

        Returns:
            Number of keys deleted
        """
        if not self.enabled or not self.client:
            return 0

        try:
            keys = self.client.keys("llm:cache:*")
            if keys:
                deleted = self.client.delete(*keys)
                logger.info(f"Cleared {deleted} cached responses")
                return deleted
            return 0
        except redis.RedisError as e:
            logger.error(f"Cache CLEAR error: {e}")
            return 0

    def stats(self) -> CacheStats:
        """Get cache statistics.

        Returns:
            CacheStats with hit rate and metrics
        """
        if self.enabled and self.client:
            try:
                # Calculate approximate size
                keys = self.client.keys("llm:cache:*")
                total_size = sum(len(self.client.get(k) or "") for k in keys if self.client.exists(k))
                self._stats.size_bytes = total_size
            except redis.RedisError as e:
                logger.error(f"Cache STATS error: {e}")

        return self._stats

    def _update_hit_rate(self) -> None:
        """Update hit rate calculation."""
        if self._stats.total_requests > 0:
            self._stats.hit_rate = self._stats.hits / self._stats.total_requests

    def reset_stats(self) -> None:
        """Reset cache statistics."""
        self._stats = CacheStats()
