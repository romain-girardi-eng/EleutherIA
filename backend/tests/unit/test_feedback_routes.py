"""Answer-feedback endpoints: auth, validation, upsert, reports, and export."""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.dependencies import get_db
from backend.routes import feedback as feedback_module
from backend.services import auth_service
from backend.services.auth_service import create_access_token
from backend.services.rate_limit import SlidingWindowLimiter

USER_ID = uuid.UUID("aaaaaaaa-0000-0000-0000-000000000001")
TRACE_ID = uuid.UUID("bbbbbbbb-0000-0000-0000-000000000001")


class StubDB:
    def __init__(self, *, role: str = "researcher") -> None:
        self.user = {
            "user_id": USER_ID,
            "username": "alice",
            "email": "Alice@Example.com",
            "role": role,
            "is_active": True,
        }
        self.rows: list[dict[str, Any]] = []
        self._clock = datetime(2026, 8, 17, 10, 0, tzinfo=UTC)

    def _new_row(self, **values: Any) -> dict[str, Any]:
        self._clock += timedelta(seconds=1)
        row: dict[str, Any] = {
            "id": uuid.uuid4(),
            "trace_id": None,
            "user_email": "",
            "rating": None,
            "comment": None,
            "report_type": None,
            "report_text": None,
            "answer_excerpt": None,
            "app_commit": None,
            "model": None,
            "created_at": self._clock,
        }
        row.update(values)
        return row

    async def fetchrow(self, query: str, *args: Any) -> dict[str, Any] | None:
        normalized = " ".join(query.split())
        if "FROM free_will.users" in normalized:
            return dict(self.user) if args[0] == USER_ID else None

        if normalized.startswith("INSERT INTO free_will.answer_feedback"):
            if "trace_id, user_email, report_type, report_text" in normalized:
                row = self._new_row(
                    trace_id=args[0],
                    user_email=args[1],
                    report_type=args[2],
                    report_text=args[3],
                    answer_excerpt=args[4],
                    app_commit=args[5],
                    model=args[6],
                )
                self.rows.append(row)
                return dict(row)

            if "ON CONFLICT" in normalized:
                current = next(
                    (
                        row
                        for row in self.rows
                        if row["trace_id"] == args[0]
                        and row["user_email"] == args[1]
                        and row["rating"] is not None
                        and row["report_type"] is None
                    ),
                    None,
                )
                if current is None:
                    current = self._new_row(
                        trace_id=args[0],
                        user_email=args[1],
                        rating=args[2],
                        comment=args[3],
                        app_commit=args[4],
                        model=args[5],
                    )
                    self.rows.append(current)
                else:
                    current["rating"] = args[2]
                    if args[3] is not None:
                        current["comment"] = args[3]
                    if args[4] is not None:
                        current["app_commit"] = args[4]
                    if args[5] is not None:
                        current["model"] = args[5]
                return dict(current)

            row = self._new_row(
                trace_id=args[0],
                user_email=args[1],
                comment=args[2],
                app_commit=args[3],
                model=args[4],
            )
            self.rows.append(row)
            return dict(row)

        candidates = [
            row
            for row in self.rows
            if row["trace_id"] == args[0]
            and row["user_email"] == args[1]
            and row["report_type"] is None
        ]
        candidates.sort(key=lambda row: row["created_at"], reverse=True)
        if "SELECT rating" in normalized:
            return next(
                ({"rating": row["rating"]} for row in candidates if row["rating"]),
                None,
            )
        if "SELECT comment" in normalized:
            return next(
                (
                    {"comment": row["comment"]}
                    for row in candidates
                    if row["comment"] is not None
                ),
                None,
            )
        return None

    async def fetch(self, query: str, *args: Any) -> list[dict[str, Any]]:
        del args
        assert "FROM free_will.answer_feedback" in query
        return [dict(row) for row in sorted(self.rows, key=lambda row: row["created_at"])]


@pytest.fixture(autouse=True)
def _fresh_feedback_limiter(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(auth_service, "JWT_SECRET_KEY", "f" * 64)
    monkeypatch.setattr(
        feedback_module,
        "_feedback_limiter",
        SlidingWindowLimiter(max_requests=12, window_seconds=60),
    )


def _client(db: StubDB) -> TestClient:
    app = FastAPI()
    app.include_router(feedback_module.router)
    app.dependency_overrides[get_db] = lambda: db
    return TestClient(app, raise_server_exceptions=False)


def _auth_headers() -> dict[str, str]:
    token = create_access_token({"sub": str(USER_ID), "role": "researcher"})
    return {"Authorization": f"Bearer {token}"}


def test_feedback_requires_authentication() -> None:
    response = _client(StubDB()).post(
        "/api/feedback", json={"trace_id": str(TRACE_ID), "rating": 4}
    )
    assert response.status_code == 401


@pytest.mark.parametrize(
    "path,payload",
    [
        ("/api/feedback", {"trace_id": str(TRACE_ID)}),
        ("/api/feedback", {"trace_id": str(TRACE_ID), "rating": 0}),
        ("/api/feedback", {"trace_id": str(TRACE_ID), "comment": "   "}),
        (
            "/api/feedback/report",
            {
                "trace_id": str(TRACE_ID),
                "report_type": "not-a-report-type",
                "report_text": "Incorrect",
            },
        ),
        (
            "/api/feedback/report",
            {
                "trace_id": str(TRACE_ID),
                "report_type": "factual_error",
                "report_text": "x" * (feedback_module.REPORT_MAX_LENGTH + 1),
            },
        ),
    ],
)
def test_feedback_validates_at_the_boundary(
    path: str, payload: dict[str, Any]
) -> None:
    response = _client(StubDB()).post(path, json=payload, headers=_auth_headers())
    assert response.status_code == 422


def test_rating_upserts_but_later_comment_is_a_separate_submission() -> None:
    db = StubDB()
    client = _client(db)
    headers = _auth_headers()

    first = client.post(
        "/api/feedback",
        json={"trace_id": str(TRACE_ID), "rating": 4, "model": "kimi-k2.6"},
        headers=headers,
    )
    updated = client.post(
        "/api/feedback",
        json={"trace_id": str(TRACE_ID), "rating": 2},
        headers=headers,
    )
    comment = client.post(
        "/api/feedback",
        json={"trace_id": str(TRACE_ID), "comment": "Les sources sont solides."},
        headers=headers,
    )

    assert first.status_code == updated.status_code == comment.status_code == 200
    assert first.json()["id"] == updated.json()["id"]
    assert comment.json()["id"] != updated.json()["id"]
    assert len(db.rows) == 2

    mine = client.get(
        "/api/feedback/mine",
        params={"trace_id": str(TRACE_ID)},
        headers=headers,
    )
    assert mine.status_code == 200
    assert mine.json() == {
        "trace_id": str(TRACE_ID),
        "rating": 2,
        "comment": "Les sources sont solides.",
    }


def test_typed_report_captures_selected_excerpt() -> None:
    response = _client(StubDB()).post(
        "/api/feedback/report",
        json={
            "trace_id": str(TRACE_ID),
            "report_type": "wrong_citation",
            "report_text": "Cette citation renvoie au mauvais passage.",
            "answer_excerpt": "Chrysippe affirme…",
            "app_commit": "abc123",
            "model": "kimi-k2.6",
        },
        headers=_auth_headers(),
    )
    assert response.status_code == 200
    assert response.json()["report_type"] == "wrong_citation"
    assert response.json()["answer_excerpt"] == "Chrysippe affirme…"


def test_feedback_is_lightly_rate_limited_per_user_and_trace(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        feedback_module,
        "_feedback_limiter",
        SlidingWindowLimiter(max_requests=1, window_seconds=60),
    )
    client = _client(StubDB())
    headers = _auth_headers()

    first = client.post(
        "/api/feedback",
        json={"trace_id": str(TRACE_ID), "rating": 5},
        headers=headers,
    )
    limited = client.post(
        "/api/feedback",
        json={"trace_id": str(TRACE_ID), "rating": 4},
        headers=headers,
    )

    assert first.status_code == 200
    assert limited.status_code == 429
    assert int(limited.headers["retry-after"]) >= 1


def test_export_is_admin_only_and_streams_jsonl() -> None:
    db = StubDB(role="researcher")
    client = _client(db)
    headers = _auth_headers()
    client.post(
        "/api/feedback",
        json={"trace_id": str(TRACE_ID), "rating": 5},
        headers=headers,
    )

    forbidden = client.get("/api/feedback/export", headers=headers)
    assert forbidden.status_code == 403

    db.user["role"] = "admin"
    exported = client.get("/api/feedback/export", headers=headers)
    assert exported.status_code == 200
    assert exported.headers["content-type"].startswith("application/x-ndjson")
    lines = [json.loads(line) for line in exported.text.splitlines()]
    assert len(lines) == 1
    assert lines[0]["rating"] == 5
    assert lines[0]["user_email"] == "alice@example.com"
