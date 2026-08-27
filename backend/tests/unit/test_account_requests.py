"""Public account-request flow: validation, delivery, and abuse controls."""

from __future__ import annotations

from datetime import date
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.dependencies import get_db
from backend.routes import auth as auth_module
from backend.services import auth_service, email_service


def _payload(**overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "full_name": "Ada Researcher",
        "email": "ada@example.org",
        "affiliation": "Academy of Ancient Studies",
        "role": "researcher",
        "research_focus": (
            "I compare ancient theories of agency across Stoic and "
            "early Christian sources."
        ),
        "intended_use": ["research", "writing"],
        "privacy_acknowledged": True,
        "privacy_notice_version": "2026-08-24",
        "locale": "en",
        "website": "",
    }
    payload.update(overrides)
    return payload


@pytest.fixture(autouse=True)
def _clear_rate_limits() -> None:
    auth_service._rate_windows.clear()


@pytest.fixture
def request_db() -> _RequestDB:
    return _RequestDB()


class _RequestDB:
    def __init__(self) -> None:
        self.fetches: list[tuple[str, tuple[Any, ...]]] = []
        self.executions: list[tuple[str, tuple[Any, ...]]] = []
        self.recent_row: dict[str, Any] | None = None
        self.conflict_row: dict[str, Any] | None = None
        self.claim_notification = True
        self.fail_status_update = False

    async def fetchrow(self, query: str, *args: Any) -> dict[str, Any] | None:
        self.fetches.append((query, args))
        if "WHERE lower(email) = $1" in query:
            return self.recent_row
        if "INSERT INTO free_will.account_requests" in query:
            if self.conflict_row is not None:
                return None
            return {
                "request_id": args[0],
                "reviewer_notification_status": "pending",
            }
        if "WHERE deduplication_key = $1" in query:
            return self.conflict_row
        if "SET reviewer_notification_status = 'sending'" in query:
            return {"request_id": args[0]} if self.claim_notification else None
        return None

    async def execute(self, query: str, *args: Any) -> str:
        self.executions.append((query, args))
        if self.fail_status_update and "$2::varchar" in query:
            raise RuntimeError("status update unavailable")
        return "OK"


@pytest.fixture
def client(request_db: _RequestDB) -> TestClient:
    app = FastAPI()
    app.include_router(auth_module.router, prefix="/api/auth")
    app.dependency_overrides[get_db] = lambda: request_db
    return TestClient(app, raise_server_exceptions=False)


def test_account_request_notifies_reviewer(
    client: TestClient,
    request_db: _RequestDB,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    delivered: list[tuple[str, dict[str, Any]]] = []

    async def _fake_send(request_id: str, info: dict[str, Any]) -> bool:
        delivered.append((request_id, info))
        return True

    monkeypatch.setattr(auth_module, "send_account_request_notification", _fake_send)
    response = client.post("/api/auth/request-account", json=_payload())

    assert response.status_code == 202
    assert response.json()["request_id"].startswith("EAR-")
    assert len(delivered) == 1
    assert delivered[0][1]["email"] == "ada@example.org"
    assert delivered[0][1]["privacy_acknowledged"] is True
    assert "website" not in delivered[0][1]
    insert_query, insert_args = next(
        item
        for item in request_db.fetches
        if "INSERT INTO free_will.account_requests" in item[0]
    )
    assert "INSERT INTO free_will.account_requests" in insert_query
    assert len(request_db.executions) == 1
    assert insert_args[2:7] == (
        "Ada Researcher",
        "ada@example.org",
        "Academy of Ancient Studies",
        "researcher",
        "I compare ancient theories of agency across Stoic and early Christian sources.",
    )
    assert insert_args[7] == ["research", "writing"]
    update_query, update_args = request_db.executions[0]
    assert "$2::varchar" in update_query
    assert update_args[1] == "sent"


def test_account_request_requires_privacy_acknowledgement(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def _unexpected_send(*_args: Any) -> bool:
        raise AssertionError("invalid request must not be delivered")

    monkeypatch.setattr(
        auth_module,
        "send_account_request_notification",
        _unexpected_send,
    )
    response = client.post(
        "/api/auth/request-account",
        json=_payload(privacy_acknowledged=False),
    )

    assert response.status_code == 422


def test_honeypot_returns_uniform_success_without_sending(
    client: TestClient,
    request_db: _RequestDB,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    called = False

    async def _fake_send(*_args: Any) -> bool:
        nonlocal called
        called = True
        return True

    monkeypatch.setattr(auth_module, "send_account_request_notification", _fake_send)
    response = client.post(
        "/api/auth/request-account",
        json=_payload(website="https://spam.example"),
    )

    assert response.status_code == 202
    assert called is False
    assert request_db.fetches == []
    assert request_db.executions == []


def test_delivery_failure_is_visible_to_the_applicant(
    client: TestClient,
    request_db: _RequestDB,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def _failed_send(*_args: Any) -> bool:
        return False

    monkeypatch.setattr(auth_module, "send_account_request_notification", _failed_send)
    response = client.post("/api/auth/request-account", json=_payload())

    assert response.status_code == 503
    assert len(request_db.executions) == 1
    assert request_db.executions[0][1][1] == "failed"


def test_duplicate_submission_returns_original_request_without_resending(
    client: TestClient,
    request_db: _RequestDB,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request_db.recent_row = {
        "request_id": "EAR-ORIGINAL",
        "reviewer_notification_status": "sent",
    }

    async def _unexpected_send(*_args: Any) -> bool:
        raise AssertionError("a delivered duplicate must not be sent again")

    monkeypatch.setattr(
        auth_module,
        "send_account_request_notification",
        _unexpected_send,
    )
    response = client.post("/api/auth/request-account", json=_payload())

    assert response.status_code == 202
    assert response.json()["request_id"] == "EAR-ORIGINAL"
    assert len(request_db.fetches) == 1
    assert "intended_use @> $6::text[]" in request_db.fetches[0][0]
    assert "intended_use <@ $6::text[]" in request_db.fetches[0][0]
    assert request_db.executions == []


def test_concurrent_duplicate_cannot_claim_a_second_notification(
    client: TestClient,
    request_db: _RequestDB,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request_db.recent_row = {
        "request_id": "EAR-INFLIGHT",
        "reviewer_notification_status": "pending",
    }
    request_db.claim_notification = False

    async def _unexpected_send(*_args: Any) -> bool:
        raise AssertionError("only the request holding the claim may send")

    monkeypatch.setattr(
        auth_module,
        "send_account_request_notification",
        _unexpected_send,
    )
    response = client.post("/api/auth/request-account", json=_payload())

    assert response.status_code == 202
    assert response.json()["request_id"] == "EAR-INFLIGHT"
    assert request_db.executions == []


def test_delivered_email_still_returns_success_if_status_persistence_fails(
    client: TestClient,
    request_db: _RequestDB,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request_db.fail_status_update = True

    async def _fake_send(*_args: Any) -> bool:
        return True

    monkeypatch.setattr(auth_module, "send_account_request_notification", _fake_send)
    response = client.post("/api/auth/request-account", json=_payload())

    assert response.status_code == 202
    assert response.json()["request_id"].startswith("EAR-")


def test_deduplication_key_is_stable_for_payload_order() -> None:
    info = _payload(intended_use=["writing", "research"])
    normalized = {
        "full_name": info["full_name"],
        "email": info["email"],
        "affiliation": info["affiliation"],
        "role": info["role"],
        "research_focus": info["research_focus"],
        "intended_use": info["intended_use"],
        "privacy_notice_version": info["privacy_notice_version"],
    }
    first = auth_module._account_request_deduplication_key(
        normalized,
        day=date(2026, 8, 25),
    )
    normalized["intended_use"] = ["research", "writing"]
    second = auth_module._account_request_deduplication_key(
        normalized,
        day=date(2026, 8, 25),
    )

    assert first == second
    assert len(first) == 64


def test_account_request_email_escapes_applicant_content() -> None:
    info = _payload(
        full_name="Ada <script>alert(1)</script>",
        research_focus="<b>Ancient agency</b> and reception history research.",
    )
    subject, text, html = email_service._account_request_copy("EAR-TEST", info)

    assert "Ada <script>" in subject
    assert "<b>Ancient agency</b>" in text
    assert "<script>" not in html
    assert "&lt;script&gt;" in html
    assert "<b>Ancient agency</b>" not in html


def test_account_request_email_is_branded_lightweight_and_transactional() -> None:
    subject, text, html = email_service._account_request_copy(
        "EAR-DESIGN",
        _payload(),
    )

    assert subject == "EleutherIA · Nouvelle demande de compte · Ada Researcher"
    assert "ELEUTHERIA — NOUVELLE DEMANDE DE COMPTE" in text
    assert "Message transactionnel" in text
    assert '<table role="presentation"' in html
    assert "https://free-will.app/apple-touch-icon.png" in html
    assert "Georgia,'Times New Roman',serif" in html
    assert "'Trebuchet MS',Helvetica,Arial,sans-serif" in html
    assert "Répondre à la demande" in html
    assert "mailto:ada@example.org" in html
    assert "Aucun suivi marketing" in html
    assert len(html.encode("utf-8")) < 40_000


@pytest.mark.asyncio
async def test_resend_payload_has_plain_text_headers_and_idempotency(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, Any] = {}

    class _Response:
        status_code = 200

    class _Client:
        def __init__(self, **_kwargs: Any) -> None:
            pass

        async def __aenter__(self) -> _Client:
            return self

        async def __aexit__(self, *_args: Any) -> None:
            return None

        async def post(self, url: str, **kwargs: Any) -> _Response:
            captured["url"] = url
            captured.update(kwargs)
            return _Response()

    monkeypatch.setenv("RESEND_API_KEY", "test-key")
    monkeypatch.setattr(email_service.httpx, "AsyncClient", _Client)

    delivered = await email_service.send_account_request_notification(
        "EAR-IDEMPOTENT",
        _payload(),
    )

    assert delivered is True
    assert captured["headers"]["Idempotency-Key"] == ("account-request/EAR-IDEMPOTENT")
    assert captured["headers"]["User-Agent"] == "EleutherIA/2.0"
    assert captured["json"]["text"]
    assert captured["json"]["html"].startswith("<!doctype html>")
    assert captured["json"]["headers"] == {
        "Auto-Submitted": "auto-generated",
        "X-Auto-Response-Suppress": "All",
        "X-Entity-Ref-ID": "EAR-IDEMPOTENT",
    }


@pytest.mark.asyncio
async def test_account_approval_email_is_transactional_and_idempotent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, Any] = {}

    class _Response:
        status_code = 200

    class _Client:
        def __init__(self, **_kwargs: Any) -> None:
            pass

        async def __aenter__(self) -> _Client:
            return self

        async def __aexit__(self, *_args: Any) -> None:
            return None

        async def post(self, url: str, **kwargs: Any) -> _Response:
            captured["url"] = url
            captured.update(kwargs)
            return _Response()

    monkeypatch.setenv("RESEND_API_KEY", "test-key")
    monkeypatch.setattr(email_service.httpx, "AsyncClient", _Client)
    delivered = await email_service.send_account_approved_notification(
        "ada@example.org",
        "Ada Researcher",
        "researcher",
        locale="en",
        transaction_id="EAR-APPROVED",
    )
    assert delivered is True
    assert captured["headers"]["Idempotency-Key"] == ("account-approved/EAR-APPROVED")
    assert captured["json"]["to"] == ["ada@example.org"]
    assert "https://free-will.app/login" in captured["json"]["text"]
    assert "No password is required" in captured["json"]["html"]
