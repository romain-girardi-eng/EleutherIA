"""Regression tests: GET /query/stream ``mode`` param validation.

Previously the param was accepted verbatim — ``mode=Deep`` silently ran
fast mode AND occupied its own answer-cache slot. The route now normalises
to lowercase and rejects anything outside {fast, deep} with a 422.
"""

from __future__ import annotations

import inspect
from collections.abc import AsyncIterator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from eleutheria_graphrag.api import routes as graphrag_routes


class _StubGraphRAG:
    """Minimal stand-in: an immediately-exhausted answer stream."""

    async def query_stream(self, **_kwargs: object) -> AsyncIterator[str]:
        return
        yield ""  # pragma: no cover — makes this an async generator


@pytest.fixture
def client() -> TestClient:
    app = FastAPI()
    app.include_router(graphrag_routes.router, prefix="/api/graphrag")
    app.dependency_overrides[graphrag_routes.get_graphrag] = _StubGraphRAG
    return TestClient(app)


@pytest.mark.parametrize("bad_mode", ["Deepish", "turbo", "fastdeep", ""])
def test_invalid_mode_is_422(client: TestClient, bad_mode: str) -> None:
    resp = client.get(
        "/api/graphrag/query/stream",
        params={"question": "q", "mode": bad_mode},
    )
    assert resp.status_code == 422
    assert "mode" in resp.json()["detail"]


@pytest.mark.parametrize("ok_mode", ["fast", "deep", "Deep", "FAST", " deep "])
def test_valid_mode_case_insensitive(client: TestClient, ok_mode: str) -> None:
    # Regression: 'Deep' used to be accepted verbatim and silently ran fast
    # mode under a distinct cache key. It must now normalise and stream.
    resp = client.get(
        "/api/graphrag/query/stream",
        params={"question": "q", "mode": ok_mode},
    )
    assert resp.status_code == 200


def test_trace_persistence_uses_the_normalized_requested_mode() -> None:
    source = inspect.getsource(graphrag_routes.query_stream)
    assert "mode=mode," in source
    assert 'mode="react"' not in source
