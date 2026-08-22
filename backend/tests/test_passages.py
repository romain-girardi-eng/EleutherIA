"""Unit tests for ``GET /api/passages/{passage_id}``.

The DB layer is replaced by a stub recording the SQL it sees so the test
exercises only the routing + shaping logic in ``backend.routes.passages``.
"""

from __future__ import annotations

import json
import uuid
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.dependencies import get_db
from backend.routes import auth as auth_route_module
from backend.routes.passages import _fetch_passage_row
from backend.routes.passages import router as passages_router

USER = {
    "user_id": "00000000-0000-0000-0000-000000000001",
    "username": "alice",
    "email": "alice@example.com",
    "role": "researcher",
    "is_active": True,
}


def _passage_row(passage_uuid: uuid.UUID, work_uuid: uuid.UUID) -> dict[str, Any]:
    return {
        "passage_id": passage_uuid,
        "work_id": work_uuid,
        "text_content": "δοκεῖ δὴ ἑκούσιον εἶναι",
        "canonical_ref": "EN III.1, 1110a4-6",
        "cts_urn": "urn:cts:greekLit:tlg0086.tlg010:1110a4-6",
        "sequence_number": 4321,
        "morphology": None,
        "work_title": "Nicomachean Ethics",
        "author": "Aristotle",
        "language": "grc",
        "work_canonical_id": "aristotle_nicomachean_ethics",
        "kg_work_id": "work_aristotle_nicomachean_ethics",
        "citation_hierarchy": None,
        "metadata": None,
    }


class _StubDB:
    """Records each fetch / fetchrow / fetchval call for assertion."""

    def __init__(self, behavior: dict[str, Any] | None = None) -> None:
        self._behavior = behavior or {}
        self.calls: list[tuple[str, tuple[Any, ...]]] = []

    def is_connected(self) -> bool:
        return True

    async def fetchrow(self, sql: str, *args: Any) -> dict[str, Any] | None:
        self.calls.append((sql, args))
        # Auth lookup — return the test user.
        if "FROM free_will.users" in sql:
            return USER
        for marker, value in self._behavior.items():
            if marker in sql:
                return value(*args) if callable(value) else value
        return None

    async def fetch(self, sql: str, *args: Any) -> list[dict[str, Any]]:
        self.calls.append((sql, args))
        return []

    async def execute(self, sql: str, *args: Any) -> str:
        self.calls.append((sql, args))
        return "OK"


@pytest.fixture(autouse=True)
def _jwt_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-not-for-prod-32b")


@pytest.fixture
def app(monkeypatch: pytest.MonkeyPatch) -> FastAPI:
    application = FastAPI()
    application.include_router(passages_router, prefix="/api/passages")
    monkeypatch.setattr(
        auth_route_module,
        "decode_token",
        lambda token: {"sub": USER["user_id"]},
    )
    return application


def _auth_headers() -> dict[str, str]:
    return {"Authorization": "Bearer test"}


def test_passage_by_kg_node_id_returns_rich_shape(app: FastAPI) -> None:
    node_id = "passage_aristotle_eth_nic_3_1_1110a4"
    p_uuid = uuid.UUID("11111111-1111-1111-1111-111111111111")
    w_uuid = uuid.UUID("22222222-2222-2222-2222-222222222222")

    db_passage_row = _passage_row(p_uuid, w_uuid)

    def passages_handler(*args: Any) -> dict[str, Any] | None:
        # The 2nd arg path uses passage_citations bridge — accept either way.
        return db_passage_row

    behavior: dict[str, Any] = {
        "SELECT node_id, label, type, description, period, metadata\n        FROM free_will.kg_nodes": lambda nid: (
            {
                "node_id": nid,
                "label": "EN III.1, 1110a4-6",
                "type": "passage",
                "description": "Voluntary action requires the origin in the agent.",
                "period": "Classical Greek",
                "metadata": json.dumps(
                    {
                        "db_passage_id": str(p_uuid),
                        "language": "grc",
                        "edition": "Bywater 1894",
                        "translator": "Crisp 2000",
                        "source": "published",
                        "attestation_type": "direct",
                    }
                ),
            }
            if nid == f"{node_id}_en" or nid == node_id
            else None
        ),
        "JOIN free_will.ancient_works w ON p.work_id = w.work_id\n            WHERE p.passage_id = $1::uuid": lambda *_a: (
            None
        ),
        "FROM free_will.passage_citations pc\n        JOIN free_will.passages p ON pc.passage_id": passages_handler,
        "JOIN free_will.passage_citations pc\n        JOIN free_will.passages p ON pc.passage_id": passages_handler,
        "FROM free_will.kg_edges e\n        JOIN free_will.kg_nodes n ON e.target_id": lambda *_: {
            "node_id": "person_aristotle",
            "label": "Aristotle",
        },
    }

    db = _StubDB(behavior)
    app.dependency_overrides[get_db] = lambda: db
    client = TestClient(app)

    response = client.get(f"/api/passages/{node_id}", headers=_auth_headers())
    assert response.status_code == 200, response.text
    body = response.json()

    assert body["node_id"] == node_id
    assert body["passage_id"] == str(p_uuid)
    assert body["work_label"] == "Nicomachean Ethics"
    assert body["author"] == {"node_id": "person_aristotle", "label": "Aristotle"}
    assert body["text_content_original"].startswith("δοκεῖ")
    assert body["text_content_english"].startswith("Voluntary action")
    assert body["translation_metadata"]["source"] == "published"
    assert body["attestation_type"] == "direct"
    assert body["edition_metadata"]["section"] == "EN III.1, 1110a4-6"
    assert body["language"] == "grc"
    bridge_sql = next(
        sql for sql, _args in db.calls if "FROM free_will.passage_citations pc" in sql
    )
    assert "pc.citation_type = 'snapshot_passage_node'" in bridge_sql


@pytest.mark.asyncio
async def test_passage_bridge_requires_exact_snapshot_citation() -> None:
    db = _StubDB()
    await _fetch_passage_row(db, "passage_related")

    bridge_sql = next(
        sql for sql, _args in db.calls if "FROM free_will.passage_citations pc" in sql
    )
    assert "pc.citation_type = 'snapshot_passage_node'" in bridge_sql


def test_passage_not_found_returns_404(app: FastAPI) -> None:
    app.dependency_overrides[get_db] = lambda: _StubDB({})
    client = TestClient(app)
    response = client.get("/api/passages/passage_unknown", headers=_auth_headers())
    assert response.status_code == 404


def test_passage_requires_auth(app: FastAPI) -> None:
    app.dependency_overrides[get_db] = lambda: _StubDB({})
    client = TestClient(app)
    response = client.get("/api/passages/passage_anything")
    assert response.status_code == 401
