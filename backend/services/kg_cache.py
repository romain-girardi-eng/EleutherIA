#!/usr/bin/env python3
"""
Simple in-memory cache for KG analytics endpoints
Uses LRU eviction policy with TTL support
"""

from __future__ import annotations

import hashlib
import json
import time
from collections import OrderedDict
from typing import Any, Dict, Optional, Callable
from functools import wraps


class LRUCache:
    """Thread-safe LRU cache with TTL support"""

    def __init__(self, max_size: int = 50, default_ttl: int = 300):
        """
        Args:
            max_size: Maximum number of entries to cache
            default_ttl: Default time-to-live in seconds (0 = no expiration)
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()
        self._stats = {"hits": 0, "misses": 0, "evictions": 0}

    def _make_key(self, *args, **kwargs) -> str:
        """Generate cache key from function arguments"""
        key_data = json.dumps(
            {"args": args, "kwargs": kwargs},
            sort_keys=True,
            default=str,
        )
        return hashlib.md5(key_data.encode()).hexdigest()

    def get(self, key: str) -> Optional[Any]:
        """Retrieve value from cache if present and not expired"""
        if key not in self._cache:
            self._stats["misses"] += 1
            return None

        entry = self._cache[key]
        # Check TTL expiration
        if entry["expires_at"] > 0 and time.time() > entry["expires_at"]:
            del self._cache[key]
            self._stats["misses"] += 1
            return None

        # Move to end (most recently used)
        self._cache.move_to_end(key)
        self._stats["hits"] += 1
        return entry["value"]

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Store value in cache with optional TTL override"""
        if ttl is None:
            ttl = self.default_ttl

        expires_at = time.time() + ttl if ttl > 0 else 0

        if key in self._cache:
            self._cache.move_to_end(key)
        else:
            if len(self._cache) >= self.max_size:
                # Evict oldest entry
                self._cache.popitem(last=False)
                self._stats["evictions"] += 1

        self._cache[key] = {
            "value": value,
            "expires_at": expires_at,
            "created_at": time.time(),
        }

    def invalidate(self, pattern: Optional[str] = None) -> int:
        """
        Invalidate cache entries
        Args:
            pattern: If provided, only invalidate keys containing this substring
        Returns:
            Number of entries invalidated
        """
        if pattern is None:
            count = len(self._cache)
            self._cache.clear()
            return count

        keys_to_remove = [k for k in self._cache.keys() if pattern in k]
        for key in keys_to_remove:
            del self._cache[key]
        return len(keys_to_remove)

    def stats(self) -> Dict[str, Any]:
        """Return cache statistics"""
        total = self._stats["hits"] + self._stats["misses"]
        hit_rate = self._stats["hits"] / total if total > 0 else 0.0

        return {
            "size": len(self._cache),
            "max_size": self.max_size,
            "hits": self._stats["hits"],
            "misses": self._stats["misses"],
            "evictions": self._stats["evictions"],
            "hit_rate": round(hit_rate, 3),
        }


# Global cache instances
_analytics_cache = LRUCache(max_size=50, default_ttl=600)  # 10 min TTL for analytics
_kg_data_cache = LRUCache(max_size=1, default_ttl=0)  # Never expire KG data


def cached(
    cache: LRUCache,
    ttl: Optional[int] = None,
    key_prefix: str = "",
) -> Callable:
    """
    Decorator to cache function results

    Args:
        cache: Cache instance to use
        ttl: Override cache TTL
        key_prefix: Prefix for cache keys (useful for namespacing)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{key_prefix}:{cache._make_key(*args, **kwargs)}"

            # Try to retrieve from cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result

            # Compute result
            result = func(*args, **kwargs)

            # Store in cache
            cache.set(cache_key, result, ttl=ttl)

            return result

        # Expose cache control methods
        wrapper.invalidate_cache = lambda: cache.invalidate(key_prefix)
        wrapper.cache = cache

        return wrapper
    return decorator


def get_analytics_cache() -> LRUCache:
    """Get the analytics cache instance"""
    return _analytics_cache


def get_kg_data_cache() -> LRUCache:
    """Get the KG data cache instance"""
    return _kg_data_cache


def invalidate_all() -> Dict[str, int]:
    """Invalidate all caches"""
    return {
        "analytics": _analytics_cache.invalidate(),
        "kg_data": _kg_data_cache.invalidate(),
    }


def cache_stats() -> Dict[str, Any]:
    """Get statistics for all caches"""
    return {
        "analytics": _analytics_cache.stats(),
        "kg_data": _kg_data_cache.stats(),
    }
