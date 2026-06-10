"""Unit tests for the per-IP LLM rate-limit middleware."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.services.rate_limit import (
    LLMRateLimitMiddleware,
    SlidingWindowLimiter,
    is_llm_path,
)


def _build_app(**middleware_kwargs: Any) -> TestClient:
    app = FastAPI()

    @app.post("/api/graphrag/answer")
    async def answer() -> dict[str, str]:
        return {"answer": "ok"}

    @app.get("/api/graphrag/stats")
    async def stats() -> dict[str, str]:
        return {"stats": "ok"}

    app.add_middleware(LLMRateLimitMiddleware, **middleware_kwargs)
    return TestClient(app)


# ---------- path matching ----------

def test_llm_paths_protected() -> None:
    assert is_llm_path("/api/graphrag/query")
    assert is_llm_path("/api/graphrag/query/stream")
    assert is_llm_path("/api/graphrag/answer")
    assert is_llm_path("/api/graphrag/compare")
    assert is_llm_path("/api/graphrag/community/queries/some-slug/reverify")


def test_cheap_paths_not_protected() -> None:
    assert not is_llm_path("/api/graphrag/query/draft")
    assert not is_llm_path("/api/graphrag/query/abc123/export")
    assert not is_llm_path("/api/graphrag/stats")
    assert not is_llm_path("/api/health")


# ---------- limiter admission ----------

def test_limiter_admits_up_to_max_then_rejects() -> None:
    limiter = SlidingWindowLimiter(max_requests=3, window_seconds=60)
    assert all(limiter.admit("1.2.3.4") for _ in range(3))
    assert not limiter.admit("1.2.3.4")
    assert limiter.retry_after("1.2.3.4") >= 1


def test_limiter_keys_are_independent() -> None:
    limiter = SlidingWindowLimiter(max_requests=1, window_seconds=60)
    assert limiter.admit("1.1.1.1")
    assert not limiter.admit("1.1.1.1")
    assert limiter.admit("2.2.2.2")


def test_limiter_window_expiry() -> None:
    limiter = SlidingWindowLimiter(max_requests=1, window_seconds=0.0)
    assert limiter.admit("1.2.3.4")
    # Zero-length window: the previous hit is already outside the window.
    assert limiter.admit("1.2.3.4")


# ---------- middleware end-to-end ----------

def test_middleware_returns_429_over_limit() -> None:
    client = _build_app(max_requests=2, window_seconds=60, enabled=True)
    headers = {"X-Forwarded-For": "203.0.113.7"}
    assert client.post("/api/graphrag/answer", headers=headers).status_code == 200
    assert client.post("/api/graphrag/answer", headers=headers).status_code == 200
    resp = client.post("/api/graphrag/answer", headers=headers)
    assert resp.status_code == 429
    assert "retry-after" in resp.headers
    assert resp.json()["retry_after"] >= 1


def test_middleware_ignores_non_llm_paths() -> None:
    client = _build_app(max_requests=1, window_seconds=60, enabled=True)
    headers = {"X-Forwarded-For": "203.0.113.7"}
    for _ in range(5):
        assert client.get("/api/graphrag/stats", headers=headers).status_code == 200


def test_middleware_disabled_passes_everything() -> None:
    client = _build_app(max_requests=1, window_seconds=60, enabled=False)
    headers = {"X-Forwarded-For": "203.0.113.7"}
    for _ in range(5):
        assert client.post("/api/graphrag/answer", headers=headers).status_code == 200


def test_forwarded_ips_get_separate_buckets() -> None:
    client = _build_app(max_requests=1, window_seconds=60, enabled=True)
    a = client.post(
        "/api/graphrag/answer", headers={"X-Forwarded-For": "203.0.113.1"}
    )
    b = client.post(
        "/api/graphrag/answer", headers={"X-Forwarded-For": "203.0.113.2"}
    )
    assert a.status_code == 200
    assert b.status_code == 200


def test_localhost_direct_connection_exempt() -> None:
    key, exempt = LLMRateLimitMiddleware._client_key(
        {"client": ("127.0.0.1", 4321), "headers": []}
    )
    assert key == "127.0.0.1"
    assert exempt is True


def test_forwarded_localhost_claim_not_exempt() -> None:
    key, exempt = LLMRateLimitMiddleware._client_key(
        {
            "client": ("127.0.0.1", 4321),
            "headers": [(b"x-forwarded-for", b"127.0.0.1")],
        }
    )
    assert key == "127.0.0.1"
    assert exempt is False


# ---------- proxy trust ----------

def test_untrusted_proxy_ignores_forwarded_header() -> None:
    key, exempt = LLMRateLimitMiddleware._client_key(
        {
            "client": ("198.51.100.9", 4321),
            "headers": [(b"x-forwarded-for", b"203.0.113.7")],
        },
        trust_proxy=False,
    )
    assert key == "198.51.100.9"
    assert exempt is False


def test_spoofed_forwarded_ips_cannot_bypass_when_proxy_untrusted() -> None:
    # Every request comes from the same direct peer; rotating XFF values
    # must not mint fresh rate buckets.
    client = _build_app(
        max_requests=1, window_seconds=60, enabled=True, trust_proxy=False
    )
    first = client.post(
        "/api/graphrag/answer", headers={"X-Forwarded-For": "203.0.113.1"}
    )
    second = client.post(
        "/api/graphrag/answer", headers={"X-Forwarded-For": "203.0.113.2"}
    )
    assert first.status_code == 200
    assert second.status_code == 429


def test_trust_proxy_env_default_true(monkeypatch: Any) -> None:
    monkeypatch.delenv("LLM_RATE_LIMIT_TRUST_PROXY", raising=False)
    middleware = LLMRateLimitMiddleware(app=None)  # type: ignore[arg-type]
    assert middleware.trust_proxy is True

    monkeypatch.setenv("LLM_RATE_LIMIT_TRUST_PROXY", "false")
    middleware = LLMRateLimitMiddleware(app=None)  # type: ignore[arg-type]
    assert middleware.trust_proxy is False


# ---------- memory bound ----------

def test_windows_dict_is_bounded() -> None:
    limiter = SlidingWindowLimiter(max_requests=5, window_seconds=60, max_keys=10)
    for i in range(100):
        assert limiter.admit(f"10.0.0.{i}")
    assert len(limiter._windows) <= 10


def test_prune_evicts_expired_windows_first() -> None:
    limiter = SlidingWindowLimiter(max_requests=5, window_seconds=0.0, max_keys=3)
    # Zero-length window: every recorded hit is immediately expired, so the
    # prune pass clears stale keys instead of evicting live ones.
    for i in range(10):
        limiter.admit(f"10.0.0.{i}")
    assert len(limiter._windows) <= 3


def test_lru_eviction_keeps_recently_seen_keys() -> None:
    limiter = SlidingWindowLimiter(max_requests=5, window_seconds=60, max_keys=3)
    limiter.admit("old-key")
    for i in range(5):
        limiter.admit(f"10.0.0.{i}")
    assert "old-key" not in limiter._windows
    assert "10.0.0.4" in limiter._windows


def test_rejected_key_still_rejected_after_flood() -> None:
    limiter = SlidingWindowLimiter(max_requests=1, window_seconds=60, max_keys=100)
    assert limiter.admit("1.2.3.4")
    assert not limiter.admit("1.2.3.4")
    for i in range(50):
        limiter.admit(f"10.0.0.{i}")
    assert not limiter.admit("1.2.3.4")
