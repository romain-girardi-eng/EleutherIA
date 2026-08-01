"""Email one-time-code (OTP) login flow — allowlist, expiry, attempts, single-use."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.dependencies import get_db
from backend.routes import auth as auth_module
from backend.services import auth_service

_AUTHORIZED = "romain-girardi@hotmail.fr"
_OWNER = {
    "user_id": uuid.UUID("dddddddd-0000-0000-0000-000000000001"),
    "username": "romain",
    "email": _AUTHORIZED,
    "role": "admin",
    "is_active": True,
}


@pytest.fixture(autouse=True)
def _only_owner_authorized(monkeypatch: pytest.MonkeyPatch) -> None:
    # Override the session-wide test allowlist: this module tests the allowlist.
    monkeypatch.setenv("AUTHORIZED_EMAILS", _AUTHORIZED)


class _StubDB:
    """Minimal async DB stub backing a single login_codes row + one user."""

    def __init__(self, *, user: dict[str, Any] | None = _OWNER) -> None:
        self._user = user
        self.codes: list[dict[str, Any]] = []
        self.sent: list[tuple[str, str]] = []

    async def fetchrow(self, query: str, *args: Any) -> dict[str, Any] | None:
        q = " ".join(query.split())
        if "FROM free_will.users" in q:
            if self._user and args[0] == self._user["email"].lower():
                return dict(self._user)
            return None
        if "created_at FROM free_will.login_codes" in q:
            live = [c for c in self.codes if c["consumed_at"] is None]
            return {"created_at": live[-1]["created_at"]} if live else None
        if "code_hash, attempts, expires_at" in q:
            live = [c for c in self.codes if c["consumed_at"] is None]
            return live[-1] if live else None
        return None

    async def execute(self, query: str, *args: Any) -> None:
        q = " ".join(query.split())
        if "DELETE FROM free_will.login_codes" in q:
            self.codes = [c for c in self.codes if c["consumed_at"] is not None]
        elif "INSERT INTO free_will.login_codes" in q:
            self.codes.append(
                {
                    "code_id": uuid.uuid4(),
                    "email": args[0],
                    "code_hash": args[1],
                    "expires_at": args[2],
                    "attempts": 0,
                    "consumed_at": None,
                    "created_at": datetime.now(UTC),
                }
            )
        elif "SET attempts = attempts + 1" in q:
            for c in self.codes:
                if c["code_id"] == args[0]:
                    c["attempts"] += 1
        elif "SET consumed_at = now()" in q:
            for c in self.codes:
                if c["code_id"] == args[0]:
                    c["consumed_at"] = datetime.now(UTC)


def _client(stub: _StubDB, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    captured: list[tuple[str, str]] = []

    async def _fake_send(email: str, code: str, ttl: int) -> bool:
        captured.append((email, code))
        stub.sent.append((email, code))
        return True

    monkeypatch.setattr(auth_module, "send_login_code", _fake_send)
    app = FastAPI()
    app.include_router(auth_module.router, prefix="/api/auth")
    app.dependency_overrides[get_db] = lambda: stub
    return TestClient(app, raise_server_exceptions=False)


# --------------------------------------------------------------------------- #


def test_request_code_sends_to_authorized_user(monkeypatch: pytest.MonkeyPatch) -> None:
    stub = _StubDB()
    client = _client(stub, monkeypatch)
    resp = client.post("/api/auth/request-code", json={"email": _AUTHORIZED})
    assert resp.status_code == 200
    assert len(stub.sent) == 1
    assert stub.sent[0][0] == _AUTHORIZED


def test_request_code_unauthorized_email_sends_nothing_but_same_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stub = _StubDB()
    client = _client(stub, monkeypatch)
    resp = client.post("/api/auth/request-code", json={"email": "intruder@evil.com"})
    # Identical 200 + message — no enumeration signal — but no code sent.
    assert resp.status_code == 200
    assert stub.sent == []
    assert stub.codes == []


def test_request_code_authorized_but_no_active_user_sends_nothing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stub = _StubDB(user=None)  # email allowlisted but no active DB row
    client = _client(stub, monkeypatch)
    resp = client.post("/api/auth/request-code", json={"email": _AUTHORIZED})
    assert resp.status_code == 200
    assert stub.sent == []


def test_verify_correct_code_returns_jwt(monkeypatch: pytest.MonkeyPatch) -> None:
    stub = _StubDB()
    client = _client(stub, monkeypatch)
    client.post("/api/auth/request-code", json={"email": _AUTHORIZED})
    code = stub.sent[0][1]

    resp = client.post(
        "/api/auth/verify-code", json={"email": _AUTHORIZED, "code": code}
    )
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    payload = auth_service.decode_token(token)
    assert payload["sub"] == str(_OWNER["user_id"])


def test_verify_wrong_code_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    stub = _StubDB()
    client = _client(stub, monkeypatch)
    client.post("/api/auth/request-code", json={"email": _AUTHORIZED})
    resp = client.post(
        "/api/auth/verify-code", json={"email": _AUTHORIZED, "code": "000000"}
    )
    assert resp.status_code == 401


def test_code_is_single_use(monkeypatch: pytest.MonkeyPatch) -> None:
    stub = _StubDB()
    client = _client(stub, monkeypatch)
    client.post("/api/auth/request-code", json={"email": _AUTHORIZED})
    code = stub.sent[0][1]
    first = client.post(
        "/api/auth/verify-code", json={"email": _AUTHORIZED, "code": code}
    )
    assert first.status_code == 200
    second = client.post(
        "/api/auth/verify-code", json={"email": _AUTHORIZED, "code": code}
    )
    assert second.status_code == 401


def test_expired_code_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    stub = _StubDB()
    client = _client(stub, monkeypatch)
    client.post("/api/auth/request-code", json={"email": _AUTHORIZED})
    stub.codes[-1]["expires_at"] = datetime.now(UTC) - timedelta(minutes=1)
    code = stub.sent[0][1]
    resp = client.post(
        "/api/auth/verify-code", json={"email": _AUTHORIZED, "code": code}
    )
    assert resp.status_code == 401


def test_attempts_are_capped(monkeypatch: pytest.MonkeyPatch) -> None:
    stub = _StubDB()
    client = _client(stub, monkeypatch)
    client.post("/api/auth/request-code", json={"email": _AUTHORIZED})
    code = stub.sent[0][1]
    for _ in range(auth_service.LOGIN_CODE_MAX_ATTEMPTS):
        client.post(
            "/api/auth/verify-code", json={"email": _AUTHORIZED, "code": "999999"}
        )
    # Even the correct code is now refused — the code is burned.
    resp = client.post(
        "/api/auth/verify-code", json={"email": _AUTHORIZED, "code": code}
    )
    assert resp.status_code == 401


def test_verify_unauthorized_email_never_checks_code(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stub = _StubDB()
    client = _client(stub, monkeypatch)
    resp = client.post(
        "/api/auth/verify-code", json={"email": "intruder@evil.com", "code": "123456"}
    )
    assert resp.status_code == 401
