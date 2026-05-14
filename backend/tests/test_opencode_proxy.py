"""Tests for the opencode proxy routes.

Uses an httpx MockTransport in place of the real upstream opencode server.
The DB and auth layer are stubbed via FastAPI dependency overrides so we
exercise only the proxy logic.
"""

from __future__ import annotations

import asyncio
import json
import time
from collections.abc import Iterator
from typing import Any

import httpx
import jwt
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.dependencies import get_db
from backend.integrations import opencode as opencode_integration
from backend.routes import auth as auth_route_module
from backend.routes import opencode_proxy
from backend.routes.opencode_proxy import router as opencode_router

SECRET = "test-session-secret-do-not-use-in-prod-32b"
USER = {
    "user_id": "00000000-0000-0000-0000-000000000001",
    "username": "alice",
    "email": "alice@example.com",
    "role": "researcher",
    "is_active": True,
}


# ---------- Fixtures ----------


@pytest.fixture(autouse=True)
def _configure_opencode_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENCODE_BASE_URL", "https://opencode.test")
    monkeypatch.setenv("OPENCODE_USERNAME", "opencode")
    monkeypatch.setenv("OPENCODE_SERVER_PASSWORD", "shh")
    monkeypatch.setenv("OPENCODE_SESSION_SECRET", SECRET)
    monkeypatch.setenv("JWT_SECRET_KEY", SECRET)
    opencode_integration.reset_opencode_settings_cache()
    opencode_proxy._reset_session_agent_cache()
    yield
    opencode_integration.reset_opencode_settings_cache()
    opencode_proxy.reset_client_factory()
    opencode_proxy._reset_session_agent_cache()


@pytest.fixture
def upstream_calls() -> list[httpx.Request]:
    return []


@pytest.fixture
def mock_upstream(
    upstream_calls: list[httpx.Request],
) -> Iterator[None]:
    """Install an httpx MockTransport-backed client factory."""

    def handler(request: httpx.Request) -> httpx.Response:
        upstream_calls.append(request)
        # opencode endpoints we model:
        if request.method == "POST" and request.url.path == "/session":
            return httpx.Response(
                200,
                json={"session_id": "ses_abc123", "agent": "scholar-orchestrator"},
            )
        if request.method == "POST" and request.url.path.endswith("/prompt_async"):
            return httpx.Response(202, json={"accepted": True})
        if request.method == "POST" and request.url.path.endswith("/abort"):
            return httpx.Response(200, json={"aborted": True})
        return httpx.Response(404, json={"error": "unknown_path"})

    transport = httpx.MockTransport(handler)

    def factory(settings: Any) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            transport=transport,
            base_url=settings.opencode_base_url,
            auth=(settings.opencode_username, settings.opencode_server_password or ""),
        )

    opencode_proxy.set_client_factory(factory)
    yield
    opencode_proxy.reset_client_factory()


@pytest.fixture
def app(monkeypatch: pytest.MonkeyPatch) -> FastAPI:
    application = FastAPI()
    application.include_router(opencode_router, prefix="/api/opencode")

    class _StubDB:
        async def fetchrow(self, *_args: Any, **_kwargs: Any) -> dict[str, Any]:
            return USER

    application.dependency_overrides[get_db] = lambda: _StubDB()
    # Bypass real JWT verification — accept any "Bearer test" header.
    monkeypatch.setattr(
        auth_route_module,
        "decode_token",
        lambda token: {"sub": USER["user_id"]},
    )
    return application


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    return TestClient(app)


def _auth() -> dict[str, str]:
    return {"Authorization": "Bearer test"}


# ---------- Happy path ----------


def test_create_session_returns_sse_token(
    client: TestClient, mock_upstream: None, upstream_calls: list[httpx.Request]
) -> None:
    response = client.post(
        "/api/opencode/session",
        json={"agent": "scholar-orchestrator", "title": "free will"},
        headers=_auth(),
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["session_id"] == "ses_abc123"
    assert body["agent"] == "scholar-orchestrator"
    assert body["sse_token"], "sse_token must be present"
    decoded = jwt.decode(body["sse_token"], SECRET, algorithms=["HS256"])
    assert decoded["session_id"] == "ses_abc123"
    assert decoded["sub"] == USER["user_id"]
    assert decoded["scope"] == "opencode_sse"

    # Forwarded payload had the agent + title and used Basic auth.
    sent = upstream_calls[0]
    assert sent.url.path == "/session"
    assert json.loads(sent.content)["agent"] == "scholar-orchestrator"
    assert sent.headers["authorization"].startswith("Basic ")


def test_prompt_returns_trace_id(
    client: TestClient, mock_upstream: None, upstream_calls: list[httpx.Request]
) -> None:
    # The proxy needs to know which agent owns this session. In production
    # the cache is populated by `POST /session`; here we prime it directly.
    opencode_proxy._cache_session_agent("ses_abc123", "scholar-orchestrator")

    response = client.post(
        "/api/opencode/session/ses_abc123/prompt",
        json={"prompt": "What did Origen say about autexousion?", "mode": "deep"},
        headers=_auth(),
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["trace_id"] == "ses_abc123"
    assert body["started_at"].endswith("Z")

    # The upstream payload must match opencode's current schema:
    # {"agent": "...", "parts": [{"type":"text","text":"..."}], "mode": "..."}
    sent = next(c for c in upstream_calls if c.url.path.endswith("/prompt_async"))
    payload = json.loads(sent.content)
    assert payload["agent"] == "scholar-orchestrator"
    assert payload["parts"] == [
        {"type": "text", "text": "What did Origen say about autexousion?"}
    ]
    assert payload["mode"] == "deep"
    # Crucially the old flat `prompt` field must NOT be sent.
    assert "prompt" not in payload


def test_prompt_without_cached_agent_returns_410(
    client: TestClient, mock_upstream: None
) -> None:
    """If the api process restarted (or the TTL elapsed) the session→agent
    mapping is gone and we can't safely forward the prompt — surface 410 so
    the client recreates the session rather than guessing an agent."""
    response = client.post(
        "/api/opencode/session/ses_missing/prompt",
        json={"prompt": "hi"},
        headers=_auth(),
    )
    assert response.status_code == 410
    assert response.json()["detail"] == "session_agent_unknown_recreate_session"


def test_create_session_populates_agent_cache(
    client: TestClient, mock_upstream: None
) -> None:
    """`POST /session` must seed the cache so the very first `/prompt` works."""
    response = client.post(
        "/api/opencode/session",
        json={"agent": "scholar-orchestrator"},
        headers=_auth(),
    )
    assert response.status_code == 200
    assert opencode_proxy._lookup_session_agent("ses_abc123") == "scholar-orchestrator"


def test_abort_evicts_agent_cache(client: TestClient, mock_upstream: None) -> None:
    opencode_proxy._cache_session_agent("ses_abc123", "scholar-orchestrator")
    response = client.post("/api/opencode/session/ses_abc123/abort", headers=_auth())
    assert response.status_code == 200
    assert opencode_proxy._lookup_session_agent("ses_abc123") is None


def test_abort_returns_aborted_true(client: TestClient, mock_upstream: None) -> None:
    response = client.post("/api/opencode/session/ses_abc123/abort", headers=_auth())
    assert response.status_code == 200
    assert response.json() == {"aborted": True}


# ---------- Auth ----------


def test_create_session_requires_auth(client: TestClient, mock_upstream: None) -> None:
    response = client.post(
        "/api/opencode/session", json={"agent": "scholar-orchestrator"}
    )
    assert response.status_code == 401


def test_prompt_requires_auth(client: TestClient, mock_upstream: None) -> None:
    response = client.post("/api/opencode/session/x/prompt", json={"prompt": "hi"})
    assert response.status_code == 401


def test_abort_requires_auth(client: TestClient, mock_upstream: None) -> None:
    response = client.post("/api/opencode/session/x/abort")
    assert response.status_code == 401


def test_unknown_agent_is_400(client: TestClient, mock_upstream: None) -> None:
    response = client.post(
        "/api/opencode/session",
        json={"agent": "evil-coder"},
        headers=_auth(),
    )
    assert response.status_code == 400


def test_unknown_mode_is_400(client: TestClient, mock_upstream: None) -> None:
    response = client.post(
        "/api/opencode/session/ses_abc123/prompt",
        json={"prompt": "hi", "mode": "yolo"},
        headers=_auth(),
    )
    assert response.status_code == 400


# ---------- Session token ----------


def test_event_rejects_missing_token(client: TestClient, mock_upstream: None) -> None:
    response = client.get("/api/opencode/event?session_id=ses_abc123")
    assert response.status_code == 422  # missing required query param


def test_event_rejects_token_for_different_session(
    client: TestClient, mock_upstream: None
) -> None:
    token = opencode_integration.make_session_token(
        user_id=USER["user_id"], session_id="ses_OTHER"
    )
    response = client.get(f"/api/opencode/event?session_id=ses_abc123&token={token}")
    assert response.status_code == 401


def test_event_rejects_expired_token(client: TestClient, mock_upstream: None) -> None:
    payload = {
        "sub": USER["user_id"],
        "session_id": "ses_abc123",
        "scope": "opencode_sse",
        "exp": int(time.time()) - 60,
    }
    expired = jwt.encode(payload, SECRET, algorithm="HS256")
    response = client.get(f"/api/opencode/event?session_id=ses_abc123&token={expired}")
    assert response.status_code == 401


# ---------- SSE filtering ----------


def _sse_block(envelope: dict[str, Any], event_id: str | None = None) -> str:
    lines: list[str] = []
    if event_id:
        lines.append(f"id: {event_id}")
    lines.append(f"data: {json.dumps(envelope)}")
    lines.append("")
    lines.append("")
    return "\n".join(lines)


@pytest.fixture
def sse_upstream_factory() -> Any:
    """Return a factory builder accepting an SSE body and capturing requests."""

    def build(sse_body: str, captured: list[httpx.Request]) -> Any:
        def handler(request: httpx.Request) -> httpx.Response:
            captured.append(request)
            return httpx.Response(
                200,
                headers={"content-type": "text/event-stream"},
                content=sse_body.encode(),
            )

        transport = httpx.MockTransport(handler)

        def factory(settings: Any) -> httpx.AsyncClient:
            return httpx.AsyncClient(
                transport=transport,
                base_url=settings.opencode_base_url,
                auth=(
                    settings.opencode_username,
                    settings.opencode_server_password or "",
                ),
            )

        return factory

    return build


def test_event_stream_filters_by_session_id(
    client: TestClient, sse_upstream_factory: Any
) -> None:
    captured: list[httpx.Request] = []
    body = (
        _sse_block({"type": "server.connected", "properties": {}})
        + _sse_block(
            {
                "type": "message.part.delta",
                "properties": {"sessionID": "ses_OTHER", "delta": "ignore"},
            }
        )
        + _sse_block(
            {
                "type": "message.part.delta",
                "properties": {"sessionID": "ses_abc123", "delta": "keep"},
            },
            event_id="42",
        )
    )
    opencode_proxy.set_client_factory(sse_upstream_factory(body, captured))

    token = opencode_integration.make_session_token(
        user_id=USER["user_id"], session_id="ses_abc123"
    )
    with client.stream(
        "GET", f"/api/opencode/event?session_id=ses_abc123&token={token}"
    ) as response:
        assert response.status_code == 200
        chunks = b"".join(response.iter_bytes())

    text = chunks.decode()
    assert "ses_OTHER" not in text, "events for other sessions must not leak"
    assert "ses_abc123" in text
    assert "id: 42" in text
    assert "server.connected" in text  # server-level event forwarded


def test_event_stream_forwards_last_event_id(
    client: TestClient, sse_upstream_factory: Any
) -> None:
    captured: list[httpx.Request] = []
    body = _sse_block({"type": "server.connected", "properties": {}})
    opencode_proxy.set_client_factory(sse_upstream_factory(body, captured))

    token = opencode_integration.make_session_token(
        user_id=USER["user_id"], session_id="ses_abc123"
    )
    with client.stream(
        "GET",
        f"/api/opencode/event?session_id=ses_abc123&token={token}",
        headers={"Last-Event-ID": "99"},
    ) as response:
        # Drain so the request is fully sent.
        b"".join(response.iter_bytes())
        assert response.status_code == 200

    assert captured, "upstream must have been hit"
    assert captured[0].headers.get("last-event-id") == "99"


# ---------- Heartbeat ----------


def test_heartbeat_emitted_when_upstream_idle(monkeypatch: pytest.MonkeyPatch) -> None:
    """When the upstream stream stalls past HEARTBEAT_INTERVAL_SECONDS the proxy
    must emit a `: heartbeat` comment so Cloudflare doesn't close the tunnel.

    We exercise the generator directly with a custom AsyncClient that yields
    blank lines slowly — TestClient can't easily simulate the time gap.
    """

    monkeypatch.setattr(opencode_proxy, "HEARTBEAT_INTERVAL_SECONDS", 0.01)

    class _FakeStreamCtx:
        def __init__(self) -> None:
            self.status_code = 200

        async def __aenter__(self) -> Any:
            return self

        async def __aexit__(self, *exc: Any) -> None:
            pass

        async def aiter_lines(self) -> Any:
            # First emit one server event, then deliver many empty keepalive
            # lines so the proxy stays idle long enough to trigger heartbeats.
            yield 'data: {"type":"server.connected","properties":{}}'
            yield ""
            for _ in range(5):
                await asyncio.sleep(0.02)
                yield ""

    class _FakeClient:
        async def __aenter__(self) -> Any:
            return self

        async def __aexit__(self, *exc: Any) -> None:
            pass

        def stream(self, *_args: Any, **_kwargs: Any) -> _FakeStreamCtx:
            return _FakeStreamCtx()

    def factory(_settings: Any) -> Any:
        return _FakeClient()

    opencode_proxy.set_client_factory(factory)

    async def drive() -> bytes:
        settings = opencode_integration.get_opencode_settings()
        collected = b""
        gen = opencode_proxy._proxy_event_stream("ses_abc123", None, settings)
        async for chunk in gen:
            collected += chunk
            if b": heartbeat" in collected:
                break
        return collected

    out = asyncio.run(drive())
    assert b": heartbeat\n\n" in out
