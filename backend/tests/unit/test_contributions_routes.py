"""Unit tests for ``backend.routes.contributions`` (Feature 8 backbone).

Mocks the asyncpg-backed ``DatabaseService`` with a fake that records the
SQL it sees, and mocks the Supabase Storage wrapper so no network is hit.
"""

from __future__ import annotations

import io
import json
import uuid
from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.dependencies import get_db
from backend.routes import auth as auth_route_module
from backend.routes import contributions as contributions_module
from backend.routes.contributions import get_storage
from backend.routes.contributions import router as contributions_router

# ---------------------------------------------------------------------------
# Fixtures / fakes
# ---------------------------------------------------------------------------


ADMIN_USER = {
    "user_id": "00000000-0000-0000-0000-000000000001",
    "username": "romain",
    "email": "romain@free-will.app",
    "role": "admin",
    "is_active": True,
}

RESEARCHER_USER = {
    "user_id": "00000000-0000-0000-0000-000000000002",
    "username": "alice",
    "email": "alice@example.com",
    "role": "researcher",
    "is_active": True,
}


class _FakeConnection:
    """Minimal asyncpg-style connection with a working transaction()."""

    def __init__(
        self, db: _ContributionsStubDB, raise_on_apply: str | None = None
    ) -> None:
        self.db = db
        self.raise_on_apply = raise_on_apply
        self.executed: list[tuple[str, tuple[Any, ...]]] = []
        self.inserted_nodes: list[tuple[Any, ...]] = []
        self.inserted_edges: list[tuple[Any, ...]] = []
        self.inserted_citations: list[tuple[Any, ...]] = []
        self._rolled_back = False
        self._txn_active = False

    def transaction(self) -> _FakeTransaction:
        return _FakeTransaction(self)

    async def fetchrow(self, sql: str, *args: Any) -> dict[str, Any] | None:
        if "INSERT INTO free_will.kg_nodes" in sql:
            if self.raise_on_apply == "node":
                raise RuntimeError("boom-node")
            self.inserted_nodes.append(args)
            return {"node_id": args[0]}
        if "INSERT INTO free_will.kg_edges" in sql:
            if self.raise_on_apply == "edge":
                raise RuntimeError("boom-edge")
            self.inserted_edges.append(args)
            return {"edge_id": uuid.uuid4()}
        if "INSERT INTO free_will.passage_citations" in sql:
            if self.raise_on_apply == "passage_citation":
                raise RuntimeError("boom-pc")
            self.inserted_citations.append(args)
            return {"citation_id": uuid.uuid4()}
        if "FROM free_will.kg_version" in sql:
            return {"version": 42}
        return None

    async def execute(self, sql: str, *args: Any) -> str:
        self.executed.append((sql, args))
        return "OK"


class _FakeTransaction:
    def __init__(self, conn: _FakeConnection) -> None:
        self._conn = conn

    async def __aenter__(self) -> _FakeTransaction:
        self._conn._txn_active = True
        return self

    async def __aexit__(self, exc_type, exc, tb) -> bool:
        if exc_type is not None:
            self._conn._rolled_back = True
        self._conn._txn_active = False
        return False


class _ContributionsStubDB:
    """In-memory fake of the asyncpg-pool-backed DatabaseService."""

    def __init__(
        self,
        *,
        contributions: list[dict[str, Any]] | None = None,
        proposals: list[dict[str, Any]] | None = None,
        user_row: dict[str, Any] | None = None,
    ) -> None:
        self.contributions = contributions or []
        self.proposals = proposals or []
        self.user_row = user_row or ADMIN_USER
        self.fetch_calls: list[tuple[str, tuple[Any, ...]]] = []
        self.fetchrow_calls: list[tuple[str, tuple[Any, ...]]] = []
        self.execute_calls: list[tuple[str, tuple[Any, ...]]] = []
        self.connection_handle: _FakeConnection | None = None
        self.raise_on_apply: str | None = None

    def is_connected(self) -> bool:
        return True

    def connection(self) -> _ConnectionCM:
        conn = _FakeConnection(self, raise_on_apply=self.raise_on_apply)
        self.connection_handle = conn
        return _ConnectionCM(conn)

    async def fetch(self, sql: str, *args: Any) -> list[dict[str, Any]]:
        self.fetch_calls.append((sql, args))

        if (
            "FROM free_will.kg_contributions c" in sql
            and "ORDER BY c.submitted_at DESC" in sql
        ):
            statuses = args[0]
            rows = [c for c in self.contributions if c["status"] in statuses]
            params = list(args[1:-1])
            limit = args[-1]
            if params:
                # (submitted_at, contribution_id) < (cursor_dt, cursor_id)
                cursor_dt = params[0]
                cursor_id = params[1]
                rows = [
                    r
                    for r in rows
                    if (r["submitted_at"], str(r["contribution_id"]))
                    < (cursor_dt, str(cursor_id))
                ]
            rows.sort(
                key=lambda r: (
                    -r["submitted_at"].timestamp(),
                    str(r["contribution_id"]),
                ),
                reverse=False,
            )
            return rows[:limit]

        if (
            "FROM free_will.kg_contribution_proposals" in sql
            and "WHERE contribution_id = $1" in sql
            and "status = 'accepted'" in sql
        ):
            contribution_id = str(args[0])
            return [
                p
                for p in self.proposals
                if str(p["contribution_id"]) == contribution_id
                and p["status"] == "accepted"
            ]

        if (
            "FROM free_will.kg_contribution_proposals" in sql
            and "WHERE contribution_id = $1" in sql
        ):
            contribution_id = str(args[0])
            return [
                p
                for p in self.proposals
                if str(p["contribution_id"]) == contribution_id
            ]

        return []

    async def fetchrow(self, sql: str, *args: Any) -> dict[str, Any] | None:
        self.fetchrow_calls.append((sql, args))

        if "FROM free_will.users" in sql:
            return self.user_row

        if (
            "INSERT INTO free_will.kg_contributions" in sql
            and "RETURNING contribution_id" in sql
        ):
            cid = uuid.uuid4()
            row = {
                "contribution_id": cid,
                "submitter_user_id": args[0],
                "pdf_url": args[1],
                "pdf_filename": args[2],
                "pdf_size_bytes": args[3],
                "title": args[4],
                "authors": list(args[5]) if args[5] is not None else [],
                "doi": args[6],
                "publication_year": args[7],
                "status": "uploaded",
                "submitted_at": datetime.now(UTC),
                "relevance_score": None,
                "free_will_concepts": [],
                "pdf_metadata": {},
                "relevance_summary": None,
                "reviewer_notes": None,
                "reviewer_user_id": None,
                "reviewed_at": None,
                "proposal_count": 0,
            }
            self.contributions.append(row)
            return {"contribution_id": cid, "status": "uploaded"}

        if (
            "UPDATE free_will.kg_contributions" in sql
            and "SET status = 'rejected'" in sql
        ):
            cid = args[0]
            for c in self.contributions:
                if str(c["contribution_id"]) == str(cid):
                    c["status"] = "rejected"
                    c["reviewer_user_id"] = args[1]
                    c["reviewer_notes"] = args[2] or c.get("reviewer_notes")
                    c["reviewed_at"] = datetime.now(UTC)
                    return {**c, "proposal_count": 0}
            return None

        if (
            "UPDATE free_will.kg_contribution_proposals" in sql
            and "RETURNING proposal_id" in sql
        ):
            proposal_id = args[0]
            contribution_id = args[1]
            new_status = args[2]
            notes = args[3]
            for p in self.proposals:
                if str(p["proposal_id"]) == str(proposal_id) and str(
                    p["contribution_id"]
                ) == str(contribution_id):
                    p["status"] = new_status
                    if notes is not None:
                        p["reviewer_notes"] = notes
                    return {
                        "proposal_id": p["proposal_id"],
                        "kind": p["kind"],
                        "confidence": p.get("confidence", 0.5),
                        "payload": p.get("payload", {}),
                        "target_kg_id": p.get("target_kg_id"),
                        "evidence": p.get("evidence", {}),
                        "status": p["status"],
                        "reviewer_notes": p.get("reviewer_notes"),
                    }
            return None

        if (
            "FROM free_will.kg_contributions c" in sql
            and "WHERE c.contribution_id = $1" in sql
        ):
            cid = str(args[0])
            for c in self.contributions:
                if str(c["contribution_id"]) == cid:
                    proposal_count = sum(
                        1
                        for p in self.proposals
                        if str(p["contribution_id"]) == cid
                        and p["status"] in {"pending", "accepted"}
                    )
                    return {**c, "proposal_count": proposal_count}
            return None

        return None

    async def execute(self, sql: str, *args: Any) -> str:
        self.execute_calls.append((sql, args))
        return "OK"


class _ConnectionCM:
    def __init__(self, conn: _FakeConnection) -> None:
        self.conn = conn

    async def __aenter__(self) -> _FakeConnection:
        return self.conn

    async def __aexit__(self, *_: Any) -> None:
        return None


def _fake_storage() -> Any:
    storage = MagicMock()
    storage.put_pdf = AsyncMock(return_value="abc/contribution.pdf")
    storage.get_signed_url = AsyncMock(return_value="https://signed.example/x.pdf")
    storage.delete = AsyncMock(return_value=None)
    return storage


def _build_app(
    monkeypatch: pytest.MonkeyPatch,
    db: _ContributionsStubDB,
    storage: Any | None = None,
    *,
    user: dict[str, Any] | None = None,
) -> FastAPI:
    user_row = user or db.user_row
    db.user_row = user_row

    application = FastAPI()
    application.include_router(contributions_router)
    monkeypatch.setattr(
        auth_route_module,
        "decode_token",
        lambda token: {"sub": user_row["user_id"]},
    )
    monkeypatch.setattr(
        contributions_module,
        "_enqueue_processing",
        AsyncMock(return_value=None),
    )
    application.dependency_overrides[get_db] = lambda: db
    application.dependency_overrides[get_storage] = lambda: storage or _fake_storage()
    return application


@pytest.fixture(autouse=True)
def _jwt(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-not-for-prod-32b")


def _make_contribution(
    *,
    contribution_id: uuid.UUID | None = None,
    title: str = "Bobzien on Stoic Determinism",
    status: str = "ready",
    submitted_at: datetime | None = None,
    authors: list[str] | None = None,
    free_will_concepts: list[str] | None = None,
    relevance_score: float | None = 0.92,
) -> dict[str, Any]:
    cid = contribution_id or uuid.uuid4()
    return {
        "contribution_id": cid,
        "submitter_user_id": uuid.UUID(RESEARCHER_USER["user_id"]),
        "submitted_at": submitted_at or datetime(2026, 5, 15, 10, 0, tzinfo=UTC),
        "pdf_url": f"{cid}/paper.pdf",
        "pdf_filename": "paper.pdf",
        "pdf_size_bytes": 12345,
        "title": title,
        "authors": authors or ["Susanne Bobzien"],
        "doi": "10.1093/example/123",
        "publication_year": 2014,
        "pdf_metadata": {"pages": 30},
        "relevance_score": relevance_score,
        "relevance_summary": "Discusses Chrysippus on assent and the cylinder.",
        "free_will_concepts": free_will_concepts or ["compatibilism", "assent"],
        "status": status,
        "processing_error": None,
        "reviewer_notes": None,
        "reviewer_user_id": None,
        "reviewed_at": None,
        "merged_at": None,
    }


def _make_proposal(
    *,
    contribution_id: uuid.UUID,
    kind: str = "node",
    payload: dict[str, Any] | None = None,
    status: str = "pending",
) -> dict[str, Any]:
    default_payload: dict[str, Any]
    if kind == "node":
        default_payload = {
            "label": "Chrysippus",
            "type": "person",
            "metadata": {"school": "Stoic"},
        }
    elif kind == "edge":
        default_payload = {
            "source_id": "person_chrysippus",
            "target_id": "concept_assent",
            "relation": "discusses",
        }
    elif kind == "passage_citation":
        default_payload = {
            "passage_id": str(uuid.uuid4()),
            "kg_node_id": "person_chrysippus",
            "citation_type": "primary_source",
            "confidence": 0.9,
        }
    else:
        default_payload = payload or {}
    return {
        "proposal_id": uuid.uuid4(),
        "contribution_id": contribution_id,
        "kind": kind,
        "payload": payload or default_payload,
        "target_kg_id": None,
        "confidence": 0.8,
        "evidence": {"page_number": 12, "excerpt": "..."},
        "status": status,
        "reviewer_notes": None,
        "created_at": datetime.now(UTC),
    }


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def _pdf_bytes() -> bytes:
    return b"%PDF-1.4\n%fakefile\n" + b"x" * 1024


def test_upload_rejects_non_pdf_content_type(monkeypatch: pytest.MonkeyPatch) -> None:
    db = _ContributionsStubDB(user_row=RESEARCHER_USER)
    app = _build_app(monkeypatch, db, user=RESEARCHER_USER)
    client = TestClient(app)
    response = client.post(
        "/api/contributions/upload",
        headers={"Authorization": "Bearer test"},
        files={"pdf": ("paper.txt", io.BytesIO(b"hello"), "text/plain")},
    )
    assert response.status_code == 415, response.text
    assert "PDF required" in response.json()["detail"]


def test_upload_rejects_too_large(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(contributions_module, "_MAX_PDF_BYTES", 1024)
    db = _ContributionsStubDB(user_row=RESEARCHER_USER)
    app = _build_app(monkeypatch, db, user=RESEARCHER_USER)
    client = TestClient(app)
    response = client.post(
        "/api/contributions/upload",
        headers={"Authorization": "Bearer test"},
        files={"pdf": ("paper.pdf", io.BytesIO(b"x" * 2048), "application/pdf")},
    )
    assert response.status_code == 413
    assert "too large" in response.json()["detail"]


def test_upload_creates_row_and_uploads_blob(monkeypatch: pytest.MonkeyPatch) -> None:
    db = _ContributionsStubDB(user_row=RESEARCHER_USER)
    storage = _fake_storage()
    app = _build_app(monkeypatch, db, storage, user=RESEARCHER_USER)
    client = TestClient(app)
    response = client.post(
        "/api/contributions/upload",
        headers={"Authorization": "Bearer test"},
        files={"pdf": ("paper.pdf", io.BytesIO(_pdf_bytes()), "application/pdf")},
        data={
            "title": "Determinism and Freedom",
            "authors": "Susanne Bobzien, Michael Frede",
            "doi": "10.1093/example/abc",
            "publication_year": "2014",
        },
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["status"] == "uploaded"
    assert body["pdf_signed_url"].startswith("https://signed.example")
    storage.put_pdf.assert_awaited_once()
    upload_kwargs = storage.put_pdf.await_args.kwargs
    assert upload_kwargs["filename"] == "paper.pdf"
    assert upload_kwargs["contribution_id"] == body["contribution_id"]
    # Assert the row was inserted with title + authors split.
    assert len(db.contributions) == 1
    inserted = db.contributions[0]
    assert inserted["title"] == "Determinism and Freedom"
    assert inserted["authors"] == ["Susanne Bobzien", "Michael Frede"]
    assert inserted["doi"] == "10.1093/example/abc"
    assert inserted["publication_year"] == 2014


def test_list_filters_status(monkeypatch: pytest.MonkeyPatch) -> None:
    contributions = [
        _make_contribution(status="ready", title="Ready one"),
        _make_contribution(status="failed", title="Failed one"),
        _make_contribution(status="merged", title="Merged one"),
    ]
    db = _ContributionsStubDB(contributions=contributions)
    app = _build_app(monkeypatch, db)
    client = TestClient(app)

    # Default filter excludes failed.
    response = client.get("/api/contributions")
    assert response.status_code == 200
    titles = [item["title"] for item in response.json()["items"]]
    assert "Ready one" in titles
    assert "Merged one" in titles
    assert "Failed one" not in titles

    # Explicit failed-only.
    response = client.get("/api/contributions?status=failed")
    titles = [item["title"] for item in response.json()["items"]]
    assert titles == ["Failed one"]

    # Bogus status.
    response = client.get("/api/contributions?status=bogus")
    assert response.status_code == 400


def test_list_paginates(monkeypatch: pytest.MonkeyPatch) -> None:
    contributions = [
        _make_contribution(
            title=f"Q{i}",
            submitted_at=datetime(2026, 5, 1, tzinfo=UTC).replace(day=i + 1),
            status="ready",
        )
        for i in range(5)
    ]
    db = _ContributionsStubDB(contributions=contributions)
    app = _build_app(monkeypatch, db)
    client = TestClient(app)

    first = client.get("/api/contributions?limit=2").json()
    assert len(first["items"]) == 2
    assert first["next_cursor"], "Expected continuation cursor"
    titles_first = [it["title"] for it in first["items"]]
    second = client.get(
        f"/api/contributions?limit=2&cursor={first['next_cursor']}"
    ).json()
    titles_second = [it["title"] for it in second["items"]]
    assert set(titles_first).isdisjoint(set(titles_second))


def test_get_detail_includes_proposals(monkeypatch: pytest.MonkeyPatch) -> None:
    contribution = _make_contribution()
    cid = contribution["contribution_id"]
    proposals = [
        _make_proposal(contribution_id=cid, kind="node"),
        _make_proposal(contribution_id=cid, kind="edge"),
    ]
    db = _ContributionsStubDB(contributions=[contribution], proposals=proposals)
    app = _build_app(monkeypatch, db)
    client = TestClient(app)

    response = client.get(f"/api/contributions/{cid}")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["contribution_id"] == str(cid)
    assert body["pdf_signed_url"].startswith("https://signed.example")
    assert len(body["proposals"]) == 2
    kinds = sorted(p["kind"] for p in body["proposals"])
    assert kinds == ["edge", "node"]
    assert body["relevance_summary"] is not None


def test_accept_marks_proposal_accepted(monkeypatch: pytest.MonkeyPatch) -> None:
    contribution = _make_contribution()
    cid = contribution["contribution_id"]
    proposal = _make_proposal(contribution_id=cid, kind="node")
    db = _ContributionsStubDB(contributions=[contribution], proposals=[proposal])
    app = _build_app(monkeypatch, db)  # admin by default
    client = TestClient(app)

    response = client.post(
        f"/api/contributions/{cid}/proposals/{proposal['proposal_id']}/accept",
        headers={"Authorization": "Bearer test"},
        json={"reviewer_notes": "Looks correct."},
    )
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "accepted"
    assert response.json()["reviewer_notes"] == "Looks correct."
    assert proposal["status"] == "accepted"


def test_apply_requires_admin(monkeypatch: pytest.MonkeyPatch) -> None:
    contribution = _make_contribution()
    cid = contribution["contribution_id"]
    db = _ContributionsStubDB(contributions=[contribution])
    app = _build_app(monkeypatch, db, user=RESEARCHER_USER)
    client = TestClient(app)
    response = client.post(
        f"/api/contributions/{cid}/apply",
        headers={"Authorization": "Bearer test"},
        json={"reviewer_notes": "go"},
    )
    assert response.status_code == 403


def test_apply_merges_all_accepted_proposals(monkeypatch: pytest.MonkeyPatch) -> None:
    contribution = _make_contribution(status="ready")
    cid = contribution["contribution_id"]
    proposals = [
        _make_proposal(contribution_id=cid, kind="node", status="accepted"),
        _make_proposal(contribution_id=cid, kind="edge", status="accepted"),
        _make_proposal(
            contribution_id=cid,
            kind="passage_citation",
            status="accepted",
            payload={
                "passage_id": str(uuid.uuid4()),
                "kg_node_id": "person_chrysippus",
                "citation_type": "primary_source",
                "confidence": 0.9,
            },
        ),
        # A pending one — should NOT be applied.
        _make_proposal(contribution_id=cid, kind="node", status="pending"),
    ]
    db = _ContributionsStubDB(contributions=[contribution], proposals=proposals)
    app = _build_app(monkeypatch, db)
    client = TestClient(app)

    response = client.post(
        f"/api/contributions/{cid}/apply",
        headers={"Authorization": "Bearer test"},
        json={"reviewer_notes": "Approved by Romain."},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["merged_proposals"] == 3
    assert body["kg_version_after"] == 42
    assert db.connection_handle is not None
    assert len(db.connection_handle.inserted_nodes) == 1
    assert len(db.connection_handle.inserted_edges) == 1
    assert len(db.connection_handle.inserted_citations) == 1
    assert not db.connection_handle._rolled_back


def test_apply_rolls_back_when_any_proposal_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    contribution = _make_contribution(status="ready")
    cid = contribution["contribution_id"]
    proposals = [
        _make_proposal(contribution_id=cid, kind="node", status="accepted"),
        _make_proposal(contribution_id=cid, kind="edge", status="accepted"),
    ]
    db = _ContributionsStubDB(contributions=[contribution], proposals=proposals)
    db.raise_on_apply = "edge"
    app = _build_app(monkeypatch, db)
    client = TestClient(app)

    response = client.post(
        f"/api/contributions/{cid}/apply",
        headers={"Authorization": "Bearer test"},
        json={"reviewer_notes": "Approved."},
    )
    assert response.status_code == 500
    assert "rolled back" in response.json()["detail"]
    assert db.connection_handle is not None
    assert db.connection_handle._rolled_back


# Silence unused import warning for `json` in stricter setups.
_ = json
