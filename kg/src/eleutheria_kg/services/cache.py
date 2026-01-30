"""
KG Cache - TTL-based caching for expensive knowledge graph operations.

Caches results of community detection, centrality calculations, and
other computationally expensive graph analytics.
"""

import logging
import time
from typing import Any, Callable, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class KGCache:
    """
    Simple TTL-based cache for knowledge graph analytics.

    Usage:
        cache = KGCache(default_ttl=300)  # 5 minutes

        # Check cache
        result = cache.get("communities")
        if result is None:
            result = expensive_computation()
            cache.set("communities", result)

        # Or use decorator
        @cache.cached("centrality", ttl=600)
        async def compute_centrality():
            return analytics.calculate_centrality()
    """

    def __init__(self, default_ttl: int = 300) -> None:
        """
        Initialize cache.

        Args:
            default_ttl: Default time-to-live in seconds (default: 5 minutes)
        """
        self._cache: dict[str, tuple[Any, float]] = {}
        self._default_ttl = default_ttl

    def get(self, key: str) -> Any | None:
        """
        Get value from cache if not expired.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        if key not in self._cache:
            return None

        value, expires_at = self._cache[key]

        if time.time() > expires_at:
            del self._cache[key]
            logger.debug(f"Cache expired for key: {key}")
            return None

        logger.debug(f"Cache hit for key: {key}")
        return value

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (uses default if not specified)
        """
        ttl = ttl or self._default_ttl
        expires_at = time.time() + ttl
        self._cache[key] = (value, expires_at)
        logger.debug(f"Cached {key} for {ttl}s")

    def delete(self, key: str) -> bool:
        """
        Delete key from cache.

        Args:
            key: Cache key

        Returns:
            True if key was deleted, False if not found
        """
        if key in self._cache:
            del self._cache[key]
            return True
        return False

    def clear(self) -> None:
        """Clear all cached values."""
        self._cache.clear()
        logger.info("Cache cleared")

    def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate all keys matching a pattern.

        Args:
            pattern: String pattern to match (simple substring match)

        Returns:
            Number of keys invalidated
        """
        keys_to_delete = [key for key in self._cache if pattern in key]
        for key in keys_to_delete:
            del self._cache[key]
        return len(keys_to_delete)

    def cached(
        self,
        key: str,
        ttl: int | None = None,
    ) -> Callable[[Callable[..., T]], Callable[..., T]]:
        """
        Decorator for caching function results.

        Args:
            key: Cache key
            ttl: Time-to-live in seconds

        Usage:
            @cache.cached("my_key", ttl=600)
            def expensive_function():
                return compute_something()
        """
        def decorator(func: Callable[..., T]) -> Callable[..., T]:
            def wrapper(*args: Any, **kwargs: Any) -> T:
                cached_value = self.get(key)
                if cached_value is not None:
                    return cached_value

                result = func(*args, **kwargs)
                self.set(key, result, ttl)
                return result

            return wrapper

        return decorator

    def get_stats(self) -> dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache stats
        """
        now = time.time()
        active_keys = [
            key for key, (_, expires_at) in self._cache.items()
            if expires_at > now
        ]
        expired_keys = [
            key for key, (_, expires_at) in self._cache.items()
            if expires_at <= now
        ]

        return {
            "total_keys": len(self._cache),
            "active_keys": len(active_keys),
            "expired_keys": len(expired_keys),
            "keys": active_keys,
        }
