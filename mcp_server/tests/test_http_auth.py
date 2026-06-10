"""Unit tests for the HTTP transport's bearer-token middleware."""

from __future__ import annotations

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from mcp_server.transports.http import BearerAuthMiddleware

TOKEN = "unit-test-token-not-a-secret"


async def _ok(_: Request) -> JSONResponse:
    return JSONResponse({"ok": True})


def _client() -> TestClient:
    app = Starlette(
        routes=[
            Route("/tool", _ok, methods=["GET"]),
            Route("/health", _ok, methods=["GET"]),
        ]
    )
    app.add_middleware(BearerAuthMiddleware, token=TOKEN)
    return TestClient(app)


def test_valid_token_passes() -> None:
    resp = _client().get("/tool", headers={"Authorization": f"Bearer {TOKEN}"})
    assert resp.status_code == 200


def test_missing_token_rejected() -> None:
    resp = _client().get("/tool")
    assert resp.status_code == 401


def test_wrong_token_rejected() -> None:
    resp = _client().get("/tool", headers={"Authorization": "Bearer nope"})
    assert resp.status_code == 401


def test_token_prefix_rejected() -> None:
    # Regression for the == comparison: a strict prefix must not pass.
    resp = _client().get("/tool", headers={"Authorization": f"Bearer {TOKEN[:-1]}"})
    assert resp.status_code == 401


def test_health_bypasses_auth() -> None:
    resp = _client().get("/health")
    assert resp.status_code == 200
