"""Per-session in-process cache for MCP tool results.

Cuts duplicate tool invocations during a single deep-mode session (the
scholar-orchestrator + sub-agents repeatedly ask for the same nodes /
passages). Keyed on ``(tool_name, args_hash)``; entries expire after a
TTL and the oldest entries are evicted once a per-session ceiling is
hit.

The cache is intentionally process-local: results returned by the MCP
tools are read-only structured data with no PII, and we want zero
external dependencies on the hot path. A second LRU bucket keyed on
``"__global__"`` is used when no session id is available from the MCP
context (e.g. tools invoked directly in unit tests).
"""

from __future__ import annotations

import hashlib
import json
import logging
import threading
import time
from collections import OrderedDict
from typing import Any

logger = logging.getLogger(__name__)

DEFAULT_TTL_SECONDS = 30 * 60
DEFAULT_MAX_ENTRIES = 200
GLOBAL_BUCKET = "__global__"


def _hash_args(args: Any) -> str:
    """Return a stable hash for the tool arguments.

    ``json.dumps(..., sort_keys=True, default=str)`` is good enough — every
    tool argument we cache is a JSON-serialisable primitive or a small
    list of primitives. ``default=str`` keeps the call total whenever a
    caller passes an ``Enum`` / ``UUID`` / ``date`` by accident.
    """
    try:
        canonical = json.dumps(args, sort_keys=True, default=str, ensure_ascii=False)
    except (TypeError, ValueError):
        canonical = repr(args)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class SessionCache:
    """Per-session LRU cache with TTL.

    Thread-safe (the FastMCP server can dispatch tools from multiple
    workers). The instance is shared across every tool wrapper.
    """

    def __init__(
        self,
        *,
        max_entries: int = DEFAULT_MAX_ENTRIES,
        default_ttl_seconds: int = DEFAULT_TTL_SECONDS,
    ) -> None:
        self._max_entries = max_entries
        self._default_ttl = default_ttl_seconds
        # bucket -> OrderedDict[cache_key, (expires_at, value)]
        self._buckets: dict[str, OrderedDict[str, tuple[float, dict[str, Any]]]] = {}
        self._lock = threading.Lock()
        self._hits = 0
        self._misses = 0
        self._evictions = 0

    @staticmethod
    def _bucket_id(session_id: str | None) -> str:
        return session_id or GLOBAL_BUCKET

    def _make_key(self, tool: str, args: Any) -> str:
        return f"{tool}::{_hash_args(args)}"

    def get(self, session_id: str | None, tool: str, args: Any) -> dict[str, Any] | None:
        """Return a cached result or ``None`` if absent / expired."""
        bucket_id = self._bucket_id(session_id)
        key = self._make_key(tool, args)
        now = time.time()
        with self._lock:
            bucket = self._buckets.get(bucket_id)
            if not bucket:
                self._misses += 1
                return None
            entry = bucket.get(key)
            if entry is None:
                self._misses += 1
                return None
            expires_at, value = entry
            if expires_at <= now:
                # Expired — drop it.
                del bucket[key]
                self._misses += 1
                return None
            # LRU touch.
            bucket.move_to_end(key)
            self._hits += 1
            return value

    def put(
        self,
        session_id: str | None,
        tool: str,
        args: Any,
        result: dict[str, Any],
        ttl_s: int | None = None,
    ) -> None:
        """Store a tool result under ``(session_id, tool, args)``."""
        if not isinstance(result, dict):
            # Tools always return dicts at the MCP boundary; refuse anything
            # else rather than risk caching mutable state we don't own.
            return
        bucket_id = self._bucket_id(session_id)
        key = self._make_key(tool, args)
        ttl = ttl_s if ttl_s is not None else self._default_ttl
        expires_at = time.time() + max(1, ttl)
        with self._lock:
            bucket = self._buckets.setdefault(bucket_id, OrderedDict())
            bucket[key] = (expires_at, result)
            bucket.move_to_end(key)
            while len(bucket) > self._max_entries:
                bucket.popitem(last=False)
                self._evictions += 1

    def evict_session(self, session_id: str) -> int:
        """Drop every entry for a session. Returns the number of evictions."""
        with self._lock:
            bucket = self._buckets.pop(session_id, None)
            n = len(bucket) if bucket else 0
            self._evictions += n
            return n

    def stats(self) -> dict[str, int]:
        with self._lock:
            return {
                "hits": self._hits,
                "misses": self._misses,
                "evictions": self._evictions,
                "sessions": len(self._buckets),
                "entries": sum(len(b) for b in self._buckets.values()),
            }

    def clear(self) -> None:
        with self._lock:
            self._buckets.clear()
            self._hits = 0
            self._misses = 0
            self._evictions = 0


# Module-level singleton — every tool wrapper imports this.
_cache = SessionCache()


def get_cache() -> SessionCache:
    return _cache


def reset_cache() -> None:
    """Test hook."""
    _cache.clear()


def session_id_from_context(ctx: Any) -> str | None:
    """Best-effort extraction of a session id from an MCP context.

    The FastMCP request context exposes a ``client_id`` /
    ``session_id`` depending on transport. We fall back to ``None``
    (which routes to the global LRU bucket) when nothing is available.
    """
    if ctx is None:
        return None
    for attr in ("session_id", "client_id", "request_id"):
        value = getattr(ctx, attr, None)
        if isinstance(value, str) and value:
            return value
    return None
