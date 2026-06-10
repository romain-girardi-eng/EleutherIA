"""Per-IP sliding-window rate limiting for the LLM-invoking endpoints.

Pure ASGI middleware (not ``BaseHTTPMiddleware``) so non-limited requests and
SSE streaming responses pass through completely untouched — only request
*admission* is gated, never the stream itself.

Configuration (all optional):

- ``LLM_RATE_LIMIT_ENABLED``      — "true"/"false", default "true"
- ``LLM_RATE_LIMIT_MAX``          — requests per window per IP, default 20
- ``LLM_RATE_LIMIT_WINDOW``       — window length in seconds, default 60
- ``LLM_RATE_LIMIT_TRUST_PROXY``  — "true"/"false", default "true". When
  true, the last ``X-Forwarded-For`` hop is the rate key. Default is true
  because in the production deployment (``deploy/deploy-compose.yml``) the
  API is fronted by the platform's Cloudflare tunnel (cloudflared → host port
  8015), which appends the real client IP to ``X-Forwarded-For``. Set to
  false whenever the API is reachable directly (no trusted proxy in front),
  otherwise the header is client-controlled and the limit is spoofable.
- ``LLM_RATE_LIMIT_MAX_KEYS``     — max tracked client keys, default 10000.
  The per-key windows dict is pruned (expired first, then least-recently
  seen) so a spray of unique IPs cannot grow memory without bound.

Localhost callers (direct connections from 127.0.0.1/::1 with no
``X-Forwarded-For``) are exempt so local development and in-host tooling are
never throttled.
"""

from __future__ import annotations

import json
import os
import time
from collections import OrderedDict
from collections.abc import Awaitable, Callable
from typing import Any

Scope = dict[str, Any]
Receive = Callable[[], Awaitable[dict[str, Any]]]
Send = Callable[[dict[str, Any]], Awaitable[None]]

_LOCALHOST = frozenset({"127.0.0.1", "::1", "localhost"})

# Endpoints that trigger LLM synthesis. Exact paths only — siblings like
# /query/draft and /query/{id}/export are cheap and stay unlimited.
LLM_EXACT_PATHS = frozenset(
    {
        "/api/graphrag/query",
        "/api/graphrag/query/stream",
        "/api/graphrag/answer",
        "/api/graphrag/compare",
    }
)
_REVERIFY_PREFIX = "/api/graphrag/community/queries/"
_REVERIFY_SUFFIX = "/reverify"


def _env_bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name, "").strip().lower()
    if not raw:
        return default
    return raw not in {"0", "false", "no", "off"}


def is_llm_path(path: str) -> bool:
    if path in LLM_EXACT_PATHS:
        return True
    return path.startswith(_REVERIFY_PREFIX) and path.endswith(_REVERIFY_SUFFIX)


class SlidingWindowLimiter:
    """In-process sliding window, same shape as auth_service's login limiter."""

    def __init__(
        self, max_requests: int, window_seconds: float, max_keys: int = 10_000
    ) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.max_keys = max(1, max_keys)
        self._windows: OrderedDict[str, list[float]] = OrderedDict()

    def admit(self, key: str) -> bool:
        now = time.monotonic()
        cutoff = now - self.window_seconds
        window = [ts for ts in self._windows.get(key, []) if ts > cutoff]
        admitted = len(window) < self.max_requests
        if admitted:
            window.append(now)
        self._windows[key] = window
        self._windows.move_to_end(key)
        if len(self._windows) > self.max_keys:
            self._prune(cutoff)
        return admitted

    def _prune(self, cutoff: float) -> None:
        """Bound memory: drop expired windows, then evict least-recently seen."""
        # Timestamps are appended in order, so window[-1] is the newest hit.
        expired = [
            key
            for key, window in self._windows.items()
            if not window or window[-1] <= cutoff
        ]
        for key in expired:
            del self._windows[key]
        while len(self._windows) > self.max_keys:
            self._windows.popitem(last=False)

    def retry_after(self, key: str) -> int:
        window = self._windows.get(key) or []
        if not window:
            return 1
        oldest = min(window)
        return max(1, int(oldest + self.window_seconds - time.monotonic()) + 1)


class LLMRateLimitMiddleware:
    """Throttle the expensive LLM endpoints per client IP."""

    def __init__(
        self,
        app: Callable[[Scope, Receive, Send], Awaitable[None]],
        max_requests: int | None = None,
        window_seconds: float | None = None,
        enabled: bool | None = None,
        trust_proxy: bool | None = None,
        max_keys: int | None = None,
    ) -> None:
        self.app = app
        self.enabled = (
            enabled
            if enabled is not None
            else _env_bool("LLM_RATE_LIMIT_ENABLED", True)
        )
        self.trust_proxy = (
            trust_proxy
            if trust_proxy is not None
            else _env_bool("LLM_RATE_LIMIT_TRUST_PROXY", True)
        )
        self.limiter = SlidingWindowLimiter(
            max_requests=max_requests
            if max_requests is not None
            else int(os.environ.get("LLM_RATE_LIMIT_MAX", "20")),
            window_seconds=window_seconds
            if window_seconds is not None
            else float(os.environ.get("LLM_RATE_LIMIT_WINDOW", "60")),
            max_keys=max_keys
            if max_keys is not None
            else int(os.environ.get("LLM_RATE_LIMIT_MAX_KEYS", "10000")),
        )

    @staticmethod
    def _client_key(scope: Scope, trust_proxy: bool = True) -> tuple[str, bool]:
        """Return (rate key, is_exempt_localhost) for a connection scope.

        With ``trust_proxy`` the last X-Forwarded-For hop (appended by the
        trusted proxy in front of us — see module docstring) is the key; the
        localhost exemption then only applies to direct connections, so a
        forwarded request claiming localhost is not exempt. Without it the
        header is client-controlled and ignored entirely: the direct peer
        address is the key, closing the spoofed-XFF bypass.
        """
        headers = {
            k.decode("latin-1").lower(): v.decode("latin-1")
            for k, v in scope.get("headers") or []
        }
        forwarded = headers.get("x-forwarded-for", "")
        peer = (scope.get("client") or ("unknown", 0))[0]
        if forwarded:
            if not trust_proxy:
                return peer, False
            hops = [h.strip() for h in forwarded.split(",") if h.strip()]
            if hops:
                return hops[-1], False
        return peer, peer in _LOCALHOST

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if (
            not self.enabled
            or scope.get("type") != "http"
            or not is_llm_path(scope.get("path", ""))
        ):
            await self.app(scope, receive, send)
            return

        key, exempt = self._client_key(scope, trust_proxy=self.trust_proxy)
        if exempt or self.limiter.admit(key):
            await self.app(scope, receive, send)
            return

        retry_after = self.limiter.retry_after(key)
        body = json.dumps(
            {
                "detail": "Rate limit exceeded for LLM endpoints. "
                "Please retry later.",
                "retry_after": retry_after,
            }
        ).encode()
        await send(
            {
                "type": "http.response.start",
                "status": 429,
                "headers": [
                    (b"content-type", b"application/json"),
                    (b"retry-after", str(retry_after).encode()),
                ],
            }
        )
        await send({"type": "http.response.body", "body": body})
