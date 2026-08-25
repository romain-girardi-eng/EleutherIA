from __future__ import annotations

import uuid
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.dependencies import get_db
from backend.routes import admin as admin_module

ADMIN = {
    "user_id": str(uuid.UUID("20000000-0000-0000-0000-000000000001")),
    "username": "owner",
    "email": "owner@example.org",
    "role": "admin",
    "is_active": True,
}


class _DB:
    async def fetch(self, query: str, *_args: Any) -> list[dict[str, Any]]:
        if "WITH usage AS" in query:
            return [
                {
                    "user_id": ADMIN["user_id"],
                    "username": "owner",
                    "email": "owner@example.org",
                    "role": "admin",
                    "is_active": True,
                    "month_tokens": 800,
                    "month_cost_usd": 0.2,
                    "month_queries": 2,
                    "lifetime_tokens": 1000,
                    "lifetime_cost_usd": 0.3,
                    "lifetime_queries": 3,
                    "allow_deep_mode": True,
                    "latest_request": None,
                }
            ]
        if "FROM free_will.account_requests" in query:
            return []
        raise AssertionError(query)

    async def fetchrow(self, query: str, *_args: Any) -> dict[str, Any]:
        if "FROM free_will.users" in query:
            return {"users": 1, "active_users": 1, "active_admins": 1}
        if "FROM free_will.query_traces" in query:
            return {
                "lifetime_queries": 3,
                "lifetime_tokens": 1000,
                "lifetime_cost_usd": 0.3,
                "month_queries": 2,
                "month_tokens": 800,
                "month_cost_usd": 0.2,
                "unassigned_queries": 0,
                "unassigned_cost_usd": 0,
            }
        raise AssertionError(query)


def _client(monkeypatch: pytest.MonkeyPatch, role: str = "admin") -> TestClient:
    async def _user(*_args: Any) -> dict[str, Any]:
        return {**ADMIN, "role": role}

    monkeypatch.setattr(admin_module, "get_current_user", _user)
    app = FastAPI()
    app.include_router(admin_module.router)
    app.dependency_overrides[get_db] = _DB
    return TestClient(app, raise_server_exceptions=False)


def test_admin_sees_users_and_cost_rollup(monkeypatch: pytest.MonkeyPatch) -> None:
    response = _client(monkeypatch).get("/api/admin/users")
    assert response.status_code == 200
    body = response.json()
    assert body["summary"]["month_tokens"] == 800
    assert body["summary"]["month_cost_usd"] == 0.2
    assert body["users"][0]["email"] == "owner@example.org"
    assert "hashed_password" not in body["users"][0]


def test_non_admin_cannot_read_user_finance(monkeypatch: pytest.MonkeyPatch) -> None:
    response = _client(monkeypatch, role="researcher").get("/api/admin/users")
    assert response.status_code == 403


def test_admin_can_list_retained_requests(monkeypatch: pytest.MonkeyPatch) -> None:
    response = _client(monkeypatch).get("/api/admin/account-requests")
    assert response.status_code == 200
    assert response.json() == {"requests": []}
