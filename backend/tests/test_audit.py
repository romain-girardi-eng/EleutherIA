"""Unit tests for ``GET /api/graphrag/query/{trace_id}/audit``."""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.dependencies import get_db
from backend.routes import auth as auth_route_module
from backend.routes.audit import router as audit_router

USER = {
    "user_id": "00000000-0000-0000-0000-000000000001",
    "username": "alice",
    "email": "alice@example.com",
    "role": "researcher",
    "is_active": True,
}


class _AuditStubDB:
    def __init__(
        self, row: dict[str, Any] | None, user: dict[str, Any] = USER
    ) -> None:
        self._row = row
        self._user = user

    def is_connected(self) -> bool:
        return True

    async def fetchrow(self, sql: str, *args: Any) -> dict[str, Any] | None:
        if "FROM free_will.users" in sql:
            return self._user
        if "FROM free_will.query_traces" in sql:
            return self._row
        return None


@pytest.fixture(autouse=True)
def _jwt(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-not-for-prod-32b")


def _build_app(
    monkeypatch: pytest.MonkeyPatch,
    row: dict[str, Any] | None,
    user: dict[str, Any] = USER,
) -> FastAPI:
    application = FastAPI()
    application.include_router(audit_router, prefix="/api/graphrag")
    monkeypatch.setattr(
        auth_route_module,
        "decode_token",
        lambda token: {"sub": user["user_id"]},
    )
    application.dependency_overrides[get_db] = lambda: _AuditStubDB(row, user)
    return application


def _row(trace_uuid: uuid.UUID) -> dict[str, Any]:
    started = datetime(2026, 5, 15, 10, 0, 0, tzinfo=UTC)
    completed = datetime(2026, 5, 15, 10, 14, 5, tzinfo=UTC)
    return {
        "trace_id": trace_uuid,
        "user_id": uuid.UUID(USER["user_id"]),
        "query": "What does Bobzien argue about Stoic compatibilism?",
        "started_at": started,
        "completed_at": completed,
        "mode": "deep",
        "agent_tree": {
            "root_agents": [
                {
                    "agent_id": "scholar-orchestrator",
                    "started_at": started.isoformat(),
                    "completed_at": completed.isoformat(),
                    "success": True,
                    "tools_called": [
                        {
                            "tool": "eleutheria_search_nodes",
                            "args": {},
                            "result_summary": "ok",
                            "duration_ms": 1234,
                        }
                    ],
                    "subagents": [
                        {
                            "agent_id": "concept-mapper",
                            "tools_called": [],
                            "subagents": [],
                        }
                    ],
                }
            ]
        },
        "citation_verifier_report": {"ok": True},
        "counter_evidence_report": {"total_testimonia": 0},
        "methodology_report": {"approved": True},
        "polishing_report": {"sections_modified": 2},
        "final_answer_text": "x" * 6432,
        "final_answer_citations": [
            {"passage_id": "passage_x", "claim": "y", "verified": True}
        ],
        "total_latency_ms": 845000,
        "total_tool_calls": 141,
        "metadata": {},
    }


def test_audit_returns_full_trace(monkeypatch: pytest.MonkeyPatch) -> None:
    trace_uuid = uuid.uuid4()
    app = _build_app(monkeypatch, _row(trace_uuid))
    client = TestClient(app)
    response = client.get(
        f"/api/graphrag/query/{trace_uuid}/audit",
        headers={"Authorization": "Bearer test"},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["trace_id"] == str(trace_uuid)
    assert body["mode"] == "deep"
    assert body["final_answer_length_chars"] == 6432
    assert body["total_tool_calls"] == 141
    assert body["agent_tree"]["agent_id"] == "scholar-orchestrator"
    assert body["agent_tree"]["subagents"][0]["agent_id"] == "concept-mapper"
    assert body["citation_verifier_report"]["ok"] is True
    assert body["counter_evidence_report"]["total_testimonia"] == 0
    assert body["methodology_report"]["approved"] is True
    assert body["polishing_report"]["sections_modified"] == 2


def test_audit_404_when_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    app = _build_app(monkeypatch, None)
    client = TestClient(app)
    response = client.get(
        "/api/graphrag/query/" + str(uuid.uuid4()) + "/audit",
        headers={"Authorization": "Bearer test"},
    )
    assert response.status_code == 404


def test_audit_accepts_non_uuid_trace_id(monkeypatch: pytest.MonkeyPatch) -> None:
    """Opencode session_ids are not UUIDs; the route derives a v5 UUID."""
    derived = uuid.uuid5(uuid.NAMESPACE_URL, "eleutheria:trace:ses_abc123")
    app = _build_app(monkeypatch, _row(derived))
    client = TestClient(app)
    response = client.get(
        "/api/graphrag/query/ses_abc123/audit",
        headers={"Authorization": "Bearer test"},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["trace_id"] == "ses_abc123"


def test_audit_404_for_non_owner(monkeypatch: pytest.MonkeyPatch) -> None:
    """A trace owned by someone else must be invisible to other users."""
    trace_uuid = uuid.uuid4()
    row = _row(trace_uuid)
    row["user_id"] = uuid.UUID("00000000-0000-0000-0000-000000000099")
    app = _build_app(monkeypatch, row)
    client = TestClient(app)
    response = client.get(
        f"/api/graphrag/query/{trace_uuid}/audit",
        headers={"Authorization": "Bearer test"},
    )
    assert response.status_code == 404


def test_audit_admin_can_read_any_trace(monkeypatch: pytest.MonkeyPatch) -> None:
    trace_uuid = uuid.uuid4()
    row = _row(trace_uuid)
    row["user_id"] = uuid.UUID("00000000-0000-0000-0000-000000000099")
    admin = {**USER, "role": "admin"}
    app = _build_app(monkeypatch, row, user=admin)
    client = TestClient(app)
    response = client.get(
        f"/api/graphrag/query/{trace_uuid}/audit",
        headers={"Authorization": "Bearer test"},
    )
    assert response.status_code == 200, response.text


def test_audit_legacy_trace_without_owner_readable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    trace_uuid = uuid.uuid4()
    row = _row(trace_uuid)
    row["user_id"] = None
    app = _build_app(monkeypatch, row)
    client = TestClient(app)
    response = client.get(
        f"/api/graphrag/query/{trace_uuid}/audit",
        headers={"Authorization": "Bearer test"},
    )
    assert response.status_code == 200, response.text


_ = json  # silence unused import flake on some setups
