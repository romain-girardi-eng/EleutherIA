"""Tests for KG cache service."""

import time

from eleutheria_kg.services.cache import KGCache


class TestKGCache:
    """Tests for KGCache class."""

    def test_init_default(self):
        """Test default initialization."""
        cache = KGCache()
        assert cache._default_ttl == 300
        assert len(cache._cache) == 0

    def test_init_custom_ttl(self):
        """Test initialization with custom TTL."""
        cache = KGCache(default_ttl=600)
        assert cache._default_ttl == 600

    def test_set_and_get(self):
        """Test basic set and get operations."""
        cache = KGCache()
        cache.set("key1", {"data": "value1"})

        result = cache.get("key1")
        assert result == {"data": "value1"}

    def test_get_missing_key(self):
        """Test get with missing key."""
        cache = KGCache()
        result = cache.get("nonexistent")
        assert result is None

    def test_set_with_custom_ttl(self):
        """Test set with custom TTL."""
        cache = KGCache(default_ttl=300)
        cache.set("key1", "value1", ttl=1)

        # Should exist immediately
        assert cache.get("key1") == "value1"

        # Wait for expiration
        time.sleep(1.1)
        assert cache.get("key1") is None

    def test_delete_existing(self):
        """Test delete operation on existing key."""
        cache = KGCache()
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

        result = cache.delete("key1")
        assert result is True
        assert cache.get("key1") is None

    def test_delete_nonexistent(self):
        """Test delete with nonexistent key."""
        cache = KGCache()
        result = cache.delete("nonexistent")
        assert result is False

    def test_clear(self):
        """Test clear operation."""
        cache = KGCache()
        cache.set("key1", "value1")
        cache.set("key2", "value2")

        cache.clear()

        assert cache.get("key1") is None
        assert cache.get("key2") is None
        assert len(cache._cache) == 0

    def test_invalidate_pattern(self):
        """Test invalidate_pattern operation."""
        cache = KGCache()
        cache.set("community:greedy", "value1")
        cache.set("community:leiden", "value2")
        cache.set("centrality:degree", "value3")

        count = cache.invalidate_pattern("community:")

        assert count == 2
        assert cache.get("community:greedy") is None
        assert cache.get("community:leiden") is None
        assert cache.get("centrality:degree") == "value3"

    def test_invalidate_pattern_no_match(self):
        """Test invalidate_pattern with no matches."""
        cache = KGCache()
        cache.set("key1", "value1")

        count = cache.invalidate_pattern("nonexistent:")
        assert count == 0
        assert cache.get("key1") == "value1"

    def test_get_stats(self):
        """Test get_stats."""
        cache = KGCache()
        cache.set("active1", "value1", ttl=300)
        cache.set("active2", "value2", ttl=300)

        stats = cache.get_stats()

        assert stats["total_keys"] == 2
        assert stats["active_keys"] == 2
        assert stats["expired_keys"] == 0
        assert "active1" in stats["keys"]
        assert "active2" in stats["keys"]

    def test_get_stats_empty(self):
        """Test get_stats with empty cache."""
        cache = KGCache()
        stats = cache.get_stats()

        assert stats["total_keys"] == 0
        assert stats["active_keys"] == 0
        assert stats["expired_keys"] == 0
        assert stats["keys"] == []

    def test_expiration_cleanup_on_get(self):
        """Test that expired entries are cleaned up on get."""
        cache = KGCache()
        cache.set("short", "value1", ttl=1)

        # Key exists
        assert cache.get("short") == "value1"

        time.sleep(1.1)

        # Key expired and removed
        assert cache.get("short") is None
        assert "short" not in cache._cache

    def test_multiple_values(self):
        """Test storing multiple values."""
        cache = KGCache()
        cache.set("key1", "value1")
        cache.set("key2", {"nested": "value2"})
        cache.set("key3", [1, 2, 3])

        assert cache.get("key1") == "value1"
        assert cache.get("key2") == {"nested": "value2"}
        assert cache.get("key3") == [1, 2, 3]

    def test_overwrite_value(self):
        """Test overwriting existing value."""
        cache = KGCache()
        cache.set("key1", "original")
        cache.set("key1", "updated")

        assert cache.get("key1") == "updated"


class TestKGCacheDecorator:
    """Tests for cache decorator."""

    def test_cached_decorator_caches_result(self):
        """Test the cached decorator caches function results."""
        cache = KGCache()
        call_count = 0

        @cache.cached("my_key", ttl=300)
        def expensive_function():
            nonlocal call_count
            call_count += 1
            return "computed_value"

        # First call - should compute
        result1 = expensive_function()
        assert result1 == "computed_value"
        assert call_count == 1

        # Second call - should use cache
        result2 = expensive_function()
        assert result2 == "computed_value"
        assert call_count == 1  # Not incremented

    def test_cached_decorator_respects_ttl(self):
        """Test the cached decorator respects TTL."""
        cache = KGCache()
        call_count = 0

        @cache.cached("expiring_key", ttl=1)
        def expensive_function():
            nonlocal call_count
            call_count += 1
            return "computed_value"

        # First call
        expensive_function()
        assert call_count == 1

        # Wait for expiration
        time.sleep(1.1)

        # Should recompute
        expensive_function()
        assert call_count == 2

    def test_cached_decorator_with_arguments(self):
        """Test cached decorator with function arguments."""
        cache = KGCache()

        @cache.cached("sum_key", ttl=300)
        def add(a, b):
            return a + b

        result = add(1, 2)
        assert result == 3

        # Note: This implementation caches by key only, not by arguments
        # So all calls to add() will return the same cached value
        result2 = add(3, 4)
        assert result2 == 3  # Returns cached value, not 7
