"""Unit tests for the research project routes (backend/routes/projects.py).

The database layer is replaced by a configurable stub. Tests cover:
- create project
- list projects (ownership-scoped — user B cannot see user A's projects)
- get project with documents
- update project
- delete project (cascade)
- upload document (PDF happy path, text/plain happy path)
- ownership isolation for document endpoints
"""

from __future__ import annotations

import io
import json
import uuid
from datetime import UTC, datetime
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.dependencies import get_db
from backend.routes import auth as auth_route_module
from backend.routes.projects import router as projects_router

# ---------------------------------------------------------------------------
# Fixtures / shared state
# ---------------------------------------------------------------------------

USER_A = {
    "user_id": "aaaaaaaa-0000-0000-0000-000000000001",
    "username": "alice",
    "email": "alice@example.com",
    "role": "researcher",
    "is_active": True,
}

USER_B = {
    "user_id": "bbbbbbbb-0000-0000-0000-000000000002",
    "username": "bob",
    "email": "bob@example.com",
    "role": "researcher",
    "is_active": True,
}

_PROJECT_ID = uuid.UUID("11111111-0000-0000-0000-000000000001")
_DOC_ID = uuid.UUID("22222222-0000-0000-0000-000000000001")
_NOW = datetime(2026, 6, 16, 12, 0, 0, tzinfo=UTC)

_BASE_PROJECT = {
    "project_id": _PROJECT_ID,
    "user_id": uuid.UUID(USER_A["user_id"]),
    "name": "Free Will in Stoics",
    "description": "Collecting primary sources",
    "status": "active",
    "created_at": _NOW,
    "updated_at": _NOW,
}

_BASE_DOC = {
    "document_id": _DOC_ID,
    "project_id": _PROJECT_ID,
    "user_id": uuid.UUID(USER_A["user_id"]),
    "filename": "bobzien1998.pdf",
    "content_type": "application/pdf",
    "size_bytes": 1024,
    "page_count": None,
    "extracted_text": None,
    "page_texts": None,
    "status": "processing",
    "metadata": {},
    "created_at": _NOW,
}


# ---------------------------------------------------------------------------
# Stub DB
# ---------------------------------------------------------------------------


class _StubDB:
    """Minimal asyncpg-alike stub for route-level tests.

    Callers configure it with an initial ``store`` that maps (table substring
    keyword) -> list[row] for fetch, or a single row dict for fetchrow.
    INSERT/UPDATE calls return the ``insert_return`` value, deletes succeed
    silently.
    """

    def __init__(
        self,
        *,
        user: dict[str, Any] = USER_A,
        project_row: dict[str, Any] | None = None,
        project_rows: list[dict[str, Any]] | None = None,
        doc_row: dict[str, Any] | None = None,
        doc_rows: list[dict[str, Any]] | None = None,
        insert_project_return: dict[str, Any] | None = None,
        insert_doc_return: dict[str, Any] | None = None,
        blob_bytes: bytes | None = None,
        doc_count: int = 0,
    ) -> None:
        self._user = user
        self._project_row = project_row
        self._project_rows = project_rows or []
        self._doc_row = doc_row
        self._doc_rows = doc_rows or []
        self._insert_project_return = insert_project_return
        self._insert_doc_return = insert_doc_return
        self._blob_bytes = blob_bytes
        self._doc_count = doc_count
        # Records calls for assertions
        self.executed: list[tuple[str, tuple[Any, ...]]] = []

    def is_connected(self) -> bool:
        return True

    async def fetchrow(self, sql: str, *args: Any) -> dict[str, Any] | None:
        self.executed.append((sql, args))
        if "FROM free_will.users" in sql:
            return self._user
        if "project_document_blobs" in sql:
            if self._blob_bytes is None:
                return None
            return {"bytes": self._blob_bytes}
        if "COUNT(*)" in sql and "project_documents" in sql:
            return {"n": self._doc_count}
        if "INSERT INTO free_will.research_projects" in sql:
            return self._insert_project_return
        if "INSERT INTO free_will.project_documents" in sql:
            return self._insert_doc_return
        if "INSERT INTO free_will.project_document_blobs" in sql:
            return None
        if "UPDATE free_will.research_projects" in sql:
            return self._project_row
        if "FROM free_will.research_projects" in sql:
            return self._project_row
        if "FROM free_will.project_documents" in sql:
            return self._doc_row
        return None

    async def fetch(self, sql: str, *args: Any) -> list[dict[str, Any]]:
        self.executed.append((sql, args))
        if "research_projects" in sql:
            return self._project_rows
        if "project_documents" in sql:
            return self._doc_rows
        return []

    async def execute(self, sql: str, *args: Any) -> None:
        self.executed.append((sql, args))


# ---------------------------------------------------------------------------
# App builder
# ---------------------------------------------------------------------------


def _build_app(
    monkeypatch: pytest.MonkeyPatch,
    stub: _StubDB,
    user: dict[str, Any] = USER_A,
) -> TestClient:
    app = FastAPI()
    app.include_router(projects_router)
    monkeypatch.setattr(
        auth_route_module,
        "decode_token",
        lambda token: {"sub": user["user_id"]},
    )
    app.dependency_overrides[get_db] = lambda: stub
    return TestClient(app, raise_server_exceptions=False)


_AUTH = {"Authorization": "Bearer test"}


# ---------------------------------------------------------------------------
# Tests — project CRUD
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _jwt(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-not-for-prod-32b")


def test_create_project(monkeypatch: pytest.MonkeyPatch) -> None:
    returned = {**_BASE_PROJECT}
    stub = _StubDB(insert_project_return=returned)
    client = _build_app(monkeypatch, stub)

    resp = client.post(
        "/api/projects", json={"name": "Free Will in Stoics"}, headers=_AUTH
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["project_id"] == str(_PROJECT_ID)
    assert body["name"] == "Free Will in Stoics"
    assert body["document_count"] == 0
    assert "created_at" in body


def test_list_projects_ownership_scoped(monkeypatch: pytest.MonkeyPatch) -> None:
    """User A's projects are not visible to user B."""
    project_with_count = {**_BASE_PROJECT, "document_count": 2}

    # User A sees their project
    stub_a = _StubDB(user=USER_A, project_rows=[project_with_count])
    client_a = _build_app(monkeypatch, stub_a, USER_A)
    resp = client_a.get("/api/projects", headers=_AUTH)
    assert resp.status_code == 200
    assert len(resp.json()["projects"]) == 1

    # User B's stub returns no rows (scoped to B's user_id by the SQL)
    stub_b = _StubDB(user=USER_B, project_rows=[])
    client_b = _build_app(monkeypatch, stub_b, USER_B)
    resp = client_b.get("/api/projects", headers=_AUTH)
    assert resp.status_code == 200
    assert resp.json()["projects"] == []


def test_get_project_with_documents(monkeypatch: pytest.MonkeyPatch) -> None:
    stub = _StubDB(
        project_row=_BASE_PROJECT,
        doc_rows=[_BASE_DOC],
    )
    client = _build_app(monkeypatch, stub)

    resp = client.get(f"/api/projects/{_PROJECT_ID}", headers=_AUTH)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["project_id"] == str(_PROJECT_ID)
    assert len(body["documents"]) == 1
    assert body["documents"][0]["filename"] == "bobzien1998.pdf"
    # Extracted text must NOT appear in this response
    assert "extracted_text" not in body["documents"][0]


def test_get_project_404_for_other_user(monkeypatch: pytest.MonkeyPatch) -> None:
    """A project owned by user A must return 404 for user B."""
    # project_row exists but belongs to user A; stub returns it for any query
    # — the ownership check in the route compares user_id fields
    stub = _StubDB(user=USER_B, project_row=_BASE_PROJECT)
    client = _build_app(monkeypatch, stub, USER_B)

    resp = client.get(f"/api/projects/{_PROJECT_ID}", headers=_AUTH)
    assert resp.status_code == 404


def test_update_project(monkeypatch: pytest.MonkeyPatch) -> None:
    updated = {**_BASE_PROJECT, "name": "Renamed project"}
    stub = _StubDB(project_row=updated, doc_count=1)
    client = _build_app(monkeypatch, stub)

    resp = client.put(
        f"/api/projects/{_PROJECT_ID}",
        json={"name": "Renamed project"},
        headers=_AUTH,
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["name"] == "Renamed project"
    assert resp.json()["document_count"] == 1


def test_delete_project_cascade(monkeypatch: pytest.MonkeyPatch) -> None:
    stub = _StubDB(project_row=_BASE_PROJECT)
    client = _build_app(monkeypatch, stub)

    resp = client.delete(f"/api/projects/{_PROJECT_ID}", headers=_AUTH)
    assert resp.status_code == 204
    # Verify a DELETE was executed against research_projects
    delete_calls = [
        sql
        for sql, _ in stub.executed
        if "DELETE" in sql and "research_projects" in sql
    ]
    assert delete_calls, "Expected DELETE on research_projects"


def test_delete_project_404_for_other_user(monkeypatch: pytest.MonkeyPatch) -> None:
    stub = _StubDB(user=USER_B, project_row=_BASE_PROJECT)
    client = _build_app(monkeypatch, stub, USER_B)

    resp = client.delete(f"/api/projects/{_PROJECT_ID}", headers=_AUTH)
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Tests — document upload
# ---------------------------------------------------------------------------


def _minimal_pdf() -> bytes:
    """Smallest valid single-page PDF that pypdf can parse."""
    return (
        b"%PDF-1.4\n"
        b"1 0 obj<</Type /Catalog /Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type /Pages /Kids [3 0 R] /Count 1>>endobj\n"
        b"3 0 obj<</Type /Page /Parent 2 0 R /MediaBox [0 0 612 792]"
        b" /Contents 4 0 R /Resources <<>>>>endobj\n"
        b"4 0 obj<</Length 44>>stream\n"
        b"BT /F1 12 Tf 100 700 Td (Hello World) Tj ET\n"
        b"endstream endobj\n"
        b"xref\n0 5\n"
        b"0000000000 65535 f \n"
        b"0000000009 00000 n \n"
        b"0000000058 00000 n \n"
        b"0000000115 00000 n \n"
        b"0000000266 00000 n \n"
        b"trailer<</Size 5 /Root 1 0 R>>\n"
        b"startxref\n361\n%%EOF"
    )


def test_upload_pdf_happy_path(monkeypatch: pytest.MonkeyPatch) -> None:
    doc_insert_return = {
        "document_id": _DOC_ID,
        "filename": "test.pdf",
        "content_type": "application/pdf",
        "size_bytes": len(_minimal_pdf()),
        "page_count": None,
        "status": "processing",
        "created_at": _NOW,
    }
    stub = _StubDB(
        project_row=_BASE_PROJECT,
        insert_doc_return=doc_insert_return,
    )
    client = _build_app(monkeypatch, stub)

    resp = client.post(
        f"/api/projects/{_PROJECT_ID}/documents",
        files={"file": ("test.pdf", io.BytesIO(_minimal_pdf()), "application/pdf")},
        headers=_AUTH,
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["document_id"] == str(_DOC_ID)
    assert body["filename"] == "test.pdf"
    assert body["status"] == "processing"


def test_upload_text_happy_path(monkeypatch: pytest.MonkeyPatch) -> None:
    content = b"Free will is the topic of this document."
    doc_insert_return = {
        "document_id": _DOC_ID,
        "filename": "notes.txt",
        "content_type": "text/plain",
        "size_bytes": len(content),
        "page_count": None,
        "status": "processing",
        "created_at": _NOW,
    }
    stub = _StubDB(
        project_row=_BASE_PROJECT,
        insert_doc_return=doc_insert_return,
    )
    client = _build_app(monkeypatch, stub)

    resp = client.post(
        f"/api/projects/{_PROJECT_ID}/documents",
        files={"file": ("notes.txt", io.BytesIO(content), "text/plain")},
        headers=_AUTH,
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["filename"] == "notes.txt"


def test_upload_rejects_wrong_content_type(monkeypatch: pytest.MonkeyPatch) -> None:
    stub = _StubDB(project_row=_BASE_PROJECT)
    client = _build_app(monkeypatch, stub)

    resp = client.post(
        f"/api/projects/{_PROJECT_ID}/documents",
        files={"file": ("data.csv", io.BytesIO(b"a,b,c"), "text/csv")},
        headers=_AUTH,
    )
    assert resp.status_code == 415


def test_upload_rejects_oversized_file(monkeypatch: pytest.MonkeyPatch) -> None:
    stub = _StubDB(project_row=_BASE_PROJECT)
    client = _build_app(monkeypatch, stub)

    big = b"x" * (26 * 1024 * 1024)
    resp = client.post(
        f"/api/projects/{_PROJECT_ID}/documents",
        files={"file": ("big.pdf", io.BytesIO(big), "application/pdf")},
        headers=_AUTH,
    )
    assert resp.status_code == 413


def test_upload_404_for_wrong_project(monkeypatch: pytest.MonkeyPatch) -> None:
    """Uploading to a project that belongs to user A should 404 for user B."""
    stub = _StubDB(user=USER_B, project_row=_BASE_PROJECT)
    client = _build_app(monkeypatch, stub, USER_B)

    resp = client.post(
        f"/api/projects/{_PROJECT_ID}/documents",
        files={"file": ("t.pdf", io.BytesIO(b"%PDF"), "application/pdf")},
        headers=_AUTH,
    )
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Tests — document retrieval
# ---------------------------------------------------------------------------


def test_get_document_full(monkeypatch: pytest.MonkeyPatch) -> None:
    doc = {
        **_BASE_DOC,
        "status": "ready",
        "extracted_text": "Ancient Greek thought on free will.",
        "page_texts": json.dumps(
            [{"page": 1, "text": "Ancient Greek thought on free will."}]
        ),
        "page_count": 1,
    }
    stub = _StubDB(doc_row=doc)
    client = _build_app(monkeypatch, stub)

    resp = client.get(f"/api/projects/documents/{_DOC_ID}", headers=_AUTH)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["document_id"] == str(_DOC_ID)
    assert body["extracted_text"] == "Ancient Greek thought on free will."
    assert isinstance(body["page_texts"], list)
    assert body["page_texts"][0]["page"] == 1


def test_get_document_404_for_other_user(monkeypatch: pytest.MonkeyPatch) -> None:
    stub = _StubDB(user=USER_B, doc_row=_BASE_DOC)
    client = _build_app(monkeypatch, stub, USER_B)

    resp = client.get(f"/api/projects/documents/{_DOC_ID}", headers=_AUTH)
    assert resp.status_code == 404


def test_delete_document(monkeypatch: pytest.MonkeyPatch) -> None:
    stub = _StubDB(doc_row=_BASE_DOC)
    client = _build_app(monkeypatch, stub)

    resp = client.delete(f"/api/projects/documents/{_DOC_ID}", headers=_AUTH)
    assert resp.status_code == 204
    delete_calls = [
        sql
        for sql, _ in stub.executed
        if "DELETE" in sql and "project_documents" in sql
    ]
    assert delete_calls


def test_list_project_documents(monkeypatch: pytest.MonkeyPatch) -> None:
    stub = _StubDB(project_row=_BASE_PROJECT, doc_rows=[_BASE_DOC])
    client = _build_app(monkeypatch, stub)

    resp = client.get(f"/api/projects/{_PROJECT_ID}/documents", headers=_AUTH)
    assert resp.status_code == 200, resp.text
    docs = resp.json()["documents"]
    assert len(docs) == 1
    assert docs[0]["filename"] == "bobzien1998.pdf"
    # Must NOT include extracted_text or page_texts
    assert "extracted_text" not in docs[0]
    assert "page_texts" not in docs[0]
