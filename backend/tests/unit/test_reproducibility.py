"""Unit tests for the reproducibility certificate + reverify endpoints.

Exercises ``GET /queries/{slug}/reproducibility`` and the SSE
``POST /queries/{slug}/reverify`` endpoint added in
``backend.routes.community`` (Feature 7).

The KG-version trigger behavior is asserted in
``test_kg_version_trigger_bumps_on_kg_nodes_change`` — Postgres-only, so it
skips when no live database is available.
"""

from __future__ import annotations

import json
import os
import uuid
from datetime import UTC, datetime
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.dependencies import get_db, get_graphrag
from backend.routes.community import router as community_router

# ---------------------------------------------------------------------------
# Fakes
# ---------------------------------------------------------------------------


def _slug_from_uuid(value: uuid.UUID) -> str:
    return value.hex[:12]


def _make_row(
    *,
    slug: str | None = None,
    query: str = "What does Bobzien argue about Stoic compatibilism?",
    answer: str = "x" * 2000,
    citations: list[dict[str, Any]] | None = None,
    is_public: bool = True,
    started_at: datetime | None = None,
    kg_version_at_creation: int = 12,
    metadata: dict[str, Any] | None = None,
    trace_id: uuid.UUID | None = None,
) -> dict[str, Any]:
    trace_uuid = trace_id or uuid.uuid4()
    return {
        "trace_id": trace_uuid,
        "share_slug": slug or _slug_from_uuid(trace_uuid),
        "query": query,
        "final_answer_text": answer,
        "final_answer_citations": citations if citations is not None else [],
        "metadata": metadata or {},
        "kg_version_at_creation": kg_version_at_creation,
        "is_public": is_public,
        "started_at": started_at or datetime(2026, 5, 15, 10, 0, 0, tzinfo=UTC),
    }


class _ReproStubDB:
    """In-memory fake DB sized for the reproducibility/reverify endpoints."""

    def __init__(
        self,
        rows: list[dict[str, Any]],
        *,
        current_version: int = 12,
        version_updated_at: datetime | None = None,
    ) -> None:
        self._rows = rows
        self.current_version = current_version
        self.version_updated_at = version_updated_at or datetime(
            2026, 5, 15, 11, 0, 0, tzinfo=UTC
        )
        self.executed: list[tuple[str, tuple[Any, ...]]] = []

    def is_connected(self) -> bool:
        return True

    async def fetchrow(self, sql: str, *args: Any) -> dict[str, Any] | None:
        if "FROM free_will.kg_version" in sql:
            return {
                "version": self.current_version,
                "updated_at": self.version_updated_at,
            }
        slug = args[0]
        for row in self._rows:
            if row.get("share_slug") == slug:
                enriched = dict(row)
                enriched["answer_length"] = len(row.get("final_answer_text") or "")
                return enriched
        return None

    async def fetchval(self, sql: str, *args: Any) -> Any:
        if "FROM free_will.kg_version" in sql:
            return self.current_version
        return None

    async def execute(self, sql: str, *args: Any) -> str:
        self.executed.append((sql, args))
        return "INSERT 0 1"


class _StubGraphRAG:
    """Tracks calls + returns a canned answer for reverify."""

    def __init__(
        self, answer: str, citations: list[dict[str, Any]] | None = None
    ) -> None:
        self._answer = answer
        self._citations = citations or []
        self.calls: list[dict[str, Any]] = []

    async def query(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(kwargs)
        return {
            "answer": self._answer,
            "passage_citations": self._citations,
        }


def _build_app(db: _ReproStubDB, graphrag: Any | None = None) -> FastAPI:
    application = FastAPI()
    application.include_router(community_router)
    application.dependency_overrides[get_db] = lambda: db
    if graphrag is not None:
        application.dependency_overrides[get_graphrag] = lambda: graphrag
    return application


@pytest.fixture(autouse=True)
def _jwt(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-not-for-prod-32b")


# ---------------------------------------------------------------------------
# /reproducibility
# ---------------------------------------------------------------------------


def test_reproducibility_unchanged_when_versions_match() -> None:
    row = _make_row(slug="slugmatch01", kg_version_at_creation=42)
    db = _ReproStubDB([row], current_version=42)
    client = TestClient(_build_app(db))

    resp = client.get("/api/graphrag/community/queries/slugmatch01/reproducibility")
    assert resp.status_code == 200, resp.text

    body = resp.json()
    assert body["slug"] == "slugmatch01"
    assert body["cached_at_kg_version"] == 42
    assert body["current_kg_version"] == 42
    assert body["kg_advanced_by"] == 0
    assert body["status"] == "unchanged"


def test_reproducibility_kg_advanced() -> None:
    row = _make_row(slug="advanced001", kg_version_at_creation=10)
    db = _ReproStubDB([row], current_version=27)
    client = TestClient(_build_app(db))

    resp = client.get("/api/graphrag/community/queries/advanced001/reproducibility")
    assert resp.status_code == 200, resp.text

    body = resp.json()
    assert body["status"] == "kg_advanced"
    assert body["cached_at_kg_version"] == 10
    assert body["current_kg_version"] == 27
    assert body["kg_advanced_by"] == 17


def test_reproducibility_stale_unknown_when_creation_version_zero() -> None:
    row = _make_row(slug="prehistor01", kg_version_at_creation=0)
    db = _ReproStubDB([row], current_version=99)
    client = TestClient(_build_app(db))

    resp = client.get("/api/graphrag/community/queries/prehistor01/reproducibility")
    assert resp.status_code == 200, resp.text

    body = resp.json()
    assert body["status"] == "stale_unknown"
    assert body["cached_at_kg_version"] == 0
    assert body["current_kg_version"] == 99
    # Delta is meaningless for unknown baselines — keep it at zero so the
    # FE doesn't render a false "stale by 99" badge.
    assert body["kg_advanced_by"] == 0


def test_reproducibility_404_when_slug_unknown() -> None:
    db = _ReproStubDB([])
    client = TestClient(_build_app(db))

    resp = client.get("/api/graphrag/community/queries/doesnotexist/reproducibility")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# /reverify
# ---------------------------------------------------------------------------


def _parse_sse_events(text: str) -> list[dict[str, Any]]:
    """Parse the multipart SSE body into a list of decoded JSON payloads."""
    events: list[dict[str, Any]] = []
    for block in text.split("\n\n"):
        for line in block.splitlines():
            if line.startswith("data: "):
                events.append(json.loads(line[len("data: ") :]))
    return events


def test_reverify_returns_diff_struct() -> None:
    original_citations = [
        {"passage_id": "P-old1", "claim": "c1"},
        {"passage_id": "P-shared", "claim": "c2"},
    ]
    original_answer = (
        "An ancient debate on free will (P-old1, P-shared). "
        "The Stoics held a compatibilist position. " * 40
    )
    row = _make_row(
        slug="rerunslug01",
        answer=original_answer,
        citations=original_citations,
        kg_version_at_creation=5,
        metadata={"model": "kimi-k2.5-thinking", "retrieval_mode": "auto"},
    )
    db = _ReproStubDB([row], current_version=9)

    new_citations = [
        {"passage_id": "P-shared", "claim": "c2"},
        {"passage_id": "P-new1", "claim": "c-new"},
    ]
    new_answer = (
        "An ancient debate on free will (P-shared, P-new1). "
        "The Stoics held a nuanced compatibilist position. " * 40
    )
    graphrag = _StubGraphRAG(answer=new_answer, citations=new_citations)
    client = TestClient(_build_app(db, graphrag=graphrag))

    with client.stream(
        "POST",
        "/api/graphrag/community/queries/rerunslug01/reverify",
        json={},
    ) as resp:
        assert resp.status_code == 200, resp.read()
        body = resp.read().decode("utf-8")

    events = _parse_sse_events(body)
    assert events, "expected at least one SSE event"

    progress = [e for e in events if e.get("type") == "progress"]
    completes = [e for e in events if e.get("type") == "complete"]
    assert progress, "expected progress events"
    assert len(completes) == 1, "expected exactly one complete event"

    data = completes[0]["data"]
    assert data["slug"] == "rerunslug01"
    assert data["original_trace_id"] == str(row["trace_id"])
    assert data["new_trace_id"] and data["new_trace_id"] != data["original_trace_id"]

    # Diff: P-old1 removed, P-new1 added; P-shared stays.
    assert "P-new1" in data["citation_diff"]["added"]
    assert "P-old1" in data["citation_diff"]["removed"]
    assert "P-shared" not in data["citation_diff"]["added"]
    assert "P-shared" not in data["citation_diff"]["removed"]

    assert data["char_count_diff"] == len(new_answer) - len(original_answer)
    assert 0.0 <= data["similarity"] <= 1.0
    # Both texts share most tokens — similarity should be well above zero.
    assert data["similarity"] > 0.5
    assert data["kg_advanced_by"] == 4
    assert data["new_answer_excerpt"].startswith("An ancient debate on free will")
    assert len(data["new_answer_excerpt"]) <= 400

    # The graphrag fake was actually called with model + mode pulled from
    # the cached trace's metadata.
    assert len(graphrag.calls) == 1
    call = graphrag.calls[0]
    assert call["question"] == row["query"]
    assert call["selected_model"] == "kimi-k2.5-thinking"
    assert call["retrieval_mode"] == "auto"

    # A new trace row was inserted with the current KG version stamped.
    insert_calls = [
        sql for sql, _ in db.executed if "INSERT INTO free_will.query_traces" in sql
    ]
    assert insert_calls, "expected the reverify trace to be persisted"


def test_reverify_404_when_slug_unknown() -> None:
    db = _ReproStubDB([])
    graphrag = _StubGraphRAG(answer="never called")
    client = TestClient(_build_app(db, graphrag=graphrag))

    resp = client.post(
        "/api/graphrag/community/queries/doesnotexist/reverify",
        json={},
    )
    assert resp.status_code == 404
    assert graphrag.calls == []


# ---------------------------------------------------------------------------
# KG-version trigger — Postgres-only integration test
# ---------------------------------------------------------------------------


@pytest.mark.skipif(
    not os.getenv("INTEGRATION_DATABASE_URL"),
    reason=(
        "kg_version trigger uses plpgsql + per-statement triggers — exercised by "
        "the integration suite; set INTEGRATION_DATABASE_URL to a Postgres "
        "instance with the EleutherIA schema to run."
    ),
)
def test_kg_version_trigger_bumps_on_kg_nodes_change() -> None:
    """Documents the contract; ran out-of-band against staging.

    Asserts that an INSERT into ``free_will.kg_nodes`` bumps
    ``free_will.kg_version.version``. The trigger is plpgsql + per-statement,
    so sqlite (the only easily-available in-process driver) cannot stand in
    for it; we skip unless an integration URL is set."""
    import asyncio

    import asyncpg

    async def _run() -> None:
        conn = await asyncpg.connect(os.environ["INTEGRATION_DATABASE_URL"])
        try:
            before = await conn.fetchval(
                "SELECT version FROM free_will.kg_version WHERE id = 1"
            )
            test_node_id = f"test_repro_{uuid.uuid4().hex[:8]}"
            try:
                await conn.execute(
                    """
                    INSERT INTO free_will.kg_nodes (node_id, label, type)
                    VALUES ($1, 'test', 'concept')
                    """,
                    test_node_id,
                )
                after = await conn.fetchval(
                    "SELECT version FROM free_will.kg_version WHERE id = 1"
                )
                assert after == before + 1
            finally:
                await conn.execute(
                    "DELETE FROM free_will.kg_nodes WHERE node_id = $1",
                    test_node_id,
                )
        finally:
            await conn.close()

    asyncio.run(_run())
