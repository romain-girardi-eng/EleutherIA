"""Unit tests for ``GET /api/works/{work_id}/section?around=...``."""

from __future__ import annotations

import uuid
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.dependencies import get_db
from backend.routes import auth as auth_route_module
from backend.routes.works_extras import router as works_extras_router

USER = {
    "user_id": "00000000-0000-0000-0000-000000000001",
    "username": "alice",
    "email": "alice@example.com",
    "role": "researcher",
    "is_active": True,
}


class _SectionStubDB:
    def __init__(self) -> None:
        self.work_uuid = uuid.UUID("22222222-2222-2222-2222-222222222222")
        self.calls: list[str] = []

    def is_connected(self) -> bool:
        return True

    async def fetchrow(self, sql: str, *args: Any) -> dict[str, Any] | None:
        self.calls.append(sql.strip().split("\n")[0])
        if "FROM free_will.users" in sql:
            return USER
        if "FROM free_will.ancient_works WHERE work_id" in sql:
            return None
        if "FROM free_will.ancient_works WHERE canonical_id" in sql:
            return {
                "work_id": self.work_uuid,
                "title": "Nicomachean Ethics",
                "canonical_id": "aristotle_nicomachean_ethics",
            }
        if "FROM free_will.passage_citations pc" in sql:
            return {
                "passage_id": uuid.UUID("11111111-1111-1111-1111-111111111111"),
                "sequence_number": 10,
                "canonical_ref": "EN III.1, 1110a4-6",
                "text_content": "δοκεῖ δὴ ἑκούσιον εἶναι",
                "cts_urn": "urn:cts:greekLit:tlg0086.tlg010:1110a4-6",
            }
        return None

    async def fetch(self, sql: str, *args: Any) -> list[dict[str, Any]]:
        self.calls.append(sql.strip().split("\n")[0])
        if "FROM free_will.passages" in sql and "BETWEEN" in sql:
            return [
                {
                    "passage_id": uuid.UUID("00000000-0000-0000-0000-000000000009"),
                    "sequence_number": 9,
                    "canonical_ref": "EN III.1, 1110a2-3",
                    "text_content": "previous",
                    "cts_urn": "urn:cts:greekLit:tlg0086.tlg010:1110a2-3",
                },
                {
                    "passage_id": uuid.UUID("11111111-1111-1111-1111-111111111111"),
                    "sequence_number": 10,
                    "canonical_ref": "EN III.1, 1110a4-6",
                    "text_content": "δοκεῖ δὴ ἑκούσιον εἶναι",
                    "cts_urn": "urn:cts:greekLit:tlg0086.tlg010:1110a4-6",
                },
                {
                    "passage_id": uuid.UUID("00000000-0000-0000-0000-000000000011"),
                    "sequence_number": 11,
                    "canonical_ref": "EN III.1, 1110a7-9",
                    "text_content": "next",
                    "cts_urn": "urn:cts:greekLit:tlg0086.tlg010:1110a7-9",
                },
            ]
        return []

    async def execute(self, sql: str, *args: Any) -> str:
        return "OK"


@pytest.fixture(autouse=True)
def _jwt(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-not-for-prod-32b")


@pytest.fixture
def app(monkeypatch: pytest.MonkeyPatch) -> FastAPI:
    application = FastAPI()
    application.include_router(works_extras_router, prefix="/api/works")
    monkeypatch.setattr(
        auth_route_module,
        "decode_token",
        lambda token: {"sub": USER["user_id"]},
    )
    application.dependency_overrides[get_db] = lambda: _SectionStubDB()
    return application


def test_section_returns_before_target_after(app: FastAPI) -> None:
    client = TestClient(app)
    response = client.get(
        "/api/works/aristotle_nicomachean_ethics/section",
        params={
            "around": "passage_aristotle_eth_nic_3_1_1110a4",
            "before": 1,
            "after": 1,
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["target_passage_id"] == "11111111-1111-1111-1111-111111111111"
    assert len(body["before"]) == 1
    assert body["before"][0]["sequence_number"] == 9
    assert body["target"]["sequence_number"] == 10
    assert len(body["after"]) == 1
    assert body["after"][0]["sequence_number"] == 11
    assert body["section_label"] == "EN III.1"
    assert body["work_title"] == "Nicomachean Ethics"
