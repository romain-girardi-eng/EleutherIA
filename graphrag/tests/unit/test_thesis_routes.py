"""Tests for the ThesisDraft submission + export endpoints."""

from __future__ import annotations

from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from eleutheria_graphrag.api import routes as graphrag_routes
from eleutheria_graphrag.models.thesis_output import ThesisDraft

_VALID_DRAFT: dict[str, Any] = {
    "title": "Test",
    "sections": [
        {"heading": "Intro", "paragraphs": [{"text": "Hello.", "footnote_refs": [1]}]}
    ],
    "footnotes": [
        {
            "n": 1,
            "text": "note",
            "citations": [
                {"passage_id": "p1", "work_label": "Eth. Nic.", "author": "Aristotle"}
            ],
        }
    ],
    "bibliography": [
        {"kind": "primary", "author": "Aristotle", "title": "Eth. Nic.", "year": 1894}
    ],
}


_DRAFT_TOKEN = "test-draft-token"
_DRAFT_AUTH = {"Authorization": f"Bearer {_DRAFT_TOKEN}"}


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    # Reset the in-memory cache between tests.
    graphrag_routes._draft_store.clear()
    monkeypatch.setenv("GRAPHRAG_DRAFT_SUBMIT_TOKEN", _DRAFT_TOKEN)
    app = FastAPI()
    app.include_router(graphrag_routes.router, prefix="/api/graphrag")
    return TestClient(app)


def test_submit_draft_validates(client: TestClient) -> None:
    resp = client.post(
        "/api/graphrag/query/draft",
        json={"trace_id": "abc-123", "draft": _VALID_DRAFT},
        headers=_DRAFT_AUTH,
    )
    assert resp.status_code == 200
    assert resp.json()["footnotes"] == 1


def test_submit_draft_rejects_invalid(client: TestClient) -> None:
    resp = client.post(
        "/api/graphrag/query/draft",
        json={"trace_id": "x", "draft": {"title": "broken"}},
        headers=_DRAFT_AUTH,
    )
    assert resp.status_code == 422


def test_submit_draft_requires_token(client: TestClient) -> None:
    resp = client.post(
        "/api/graphrag/query/draft",
        json={"trace_id": "abc-123", "draft": _VALID_DRAFT},
    )
    assert resp.status_code == 401


def test_submit_draft_rejects_wrong_token(client: TestClient) -> None:
    resp = client.post(
        "/api/graphrag/query/draft",
        json={"trace_id": "abc-123", "draft": _VALID_DRAFT},
        headers={"Authorization": "Bearer wrong"},
    )
    assert resp.status_code == 401


def test_submit_draft_disabled_without_env(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("GRAPHRAG_DRAFT_SUBMIT_TOKEN", raising=False)
    resp = client.post(
        "/api/graphrag/query/draft",
        json={"trace_id": "abc-123", "draft": _VALID_DRAFT},
        headers=_DRAFT_AUTH,
    )
    assert resp.status_code == 403


def test_export_markdown(client: TestClient) -> None:
    graphrag_routes.store_draft("trace-1", ThesisDraft.model_validate(_VALID_DRAFT))
    resp = client.get("/api/graphrag/query/trace-1/export?format=markdown")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/markdown")
    assert "[^1]" in resp.text


def test_export_bibtex_download(client: TestClient) -> None:
    graphrag_routes.store_draft("trace-2", ThesisDraft.model_validate(_VALID_DRAFT))
    resp = client.get("/api/graphrag/query/trace-2/export?format=bibtex&download=true")
    assert resp.status_code == 200
    assert "attachment" in resp.headers["content-disposition"]
    assert "@book{aristotle" in resp.text


def test_export_unknown_trace(client: TestClient) -> None:
    resp = client.get("/api/graphrag/query/missing/export?format=markdown")
    assert resp.status_code == 404
