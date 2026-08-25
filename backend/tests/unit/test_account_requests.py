"""Public account-request flow: validation, delivery, and abuse controls."""

from __future__ import annotations

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
        self.executions: list[tuple[str, tuple[Any, ...]]] = []

    async def execute(self, query: str, *args: Any) -> str:
        self.executions.append((query, args))
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
    assert len(request_db.executions) == 2
    insert_query, insert_args = request_db.executions[0]
    assert "INSERT INTO free_will.account_requests" in insert_query
    assert insert_args[1:6] == (
        "Ada Researcher",
        "ada@example.org",
        "Academy of Ancient Studies",
        "researcher",
        "I compare ancient theories of agency across Stoic and early Christian sources.",
    )
    assert insert_args[6] == ["research", "writing"]
    assert request_db.executions[1][1][1] == "sent"


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
    assert len(request_db.executions) == 2
    assert request_db.executions[1][1][1] == "failed"


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
    assert captured["headers"]["Idempotency-Key"] == (
        "account-approved/EAR-APPROVED"
    )
    assert captured["json"]["to"] == ["ada@example.org"]
    assert "https://free-will.app/login" in captured["json"]["text"]
    assert "No password is required" in captured["json"]["html"]
