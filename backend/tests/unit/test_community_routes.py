"""Unit tests for the public community gallery endpoints.

Exercises the SQL/routing/shape logic in ``backend.routes.community`` using a
fake asyncpg-style DB that records the SQL it sees and returns curated rows.
"""

from __future__ import annotations

import base64
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.dependencies import get_db
from backend.routes.community import router as community_router

# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------


def _slug_from_uuid(value: uuid.UUID) -> str:
    return value.hex[:12]


def _make_row(
    *,
    slug: str | None = None,
    query: str = "What does Bobzien argue about Stoic compatibilism?",
    answer_length: int = 2000,
    citations: list[dict[str, Any]] | None = None,
    is_public: bool = True,
    started_at: datetime | None = None,
    topic_tags: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
    total_cost_usd: float = 0.034,
    total_tokens: int = 12_348,
    trace_id: uuid.UUID | None = None,
) -> dict[str, Any]:
    trace_uuid = trace_id or uuid.uuid4()
    return {
        "trace_id": trace_uuid,
        "share_slug": slug or _slug_from_uuid(trace_uuid),
        "query": query,
        "final_answer_text": "x" * answer_length if answer_length else None,
        "final_answer_citations": citations if citations is not None else [],
        "metadata": metadata or {},
        "total_cost_usd": total_cost_usd,
        "total_tokens": total_tokens,
        "started_at": started_at or datetime(2026, 5, 15, 10, 0, 0, tzinfo=UTC),
        "topic_tags": topic_tags or [],
        "is_public": is_public,
    }


def _matches_filters(row: dict[str, Any], conds: list[tuple[str, Any]]) -> bool:
    """Mimic the WHERE clause filters that the route applies."""
    for kind, value in conds:
        if kind == "is_public" and not row.get("is_public"):
            return False
        if kind == "has_answer" and not row.get("final_answer_text"):
            return False
        if kind == "min_len" and len(row.get("final_answer_text") or "") < value:
            return False
        if kind == "topic" and value not in (row.get("topic_tags") or []):
            return False
        if kind == "cursor":
            cursor_dt, cursor_slug = value
            row_started: datetime = row["started_at"]
            row_slug: str = row["share_slug"]
            if not ((row_started, row_slug) < (cursor_dt, cursor_slug)):
                return False
    return True


class _CommunityStubDB:
    """In-memory fake of the asyncpg-pool-backed ``DatabaseService``.

    Reads the bind parameters from each query, applies the same filters the
    route does, then returns matching rows in the requested order.
    """

    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self._rows = rows
        self.fetch_calls: list[tuple[str, tuple[Any, ...]]] = []
        self.fetchrow_calls: list[tuple[str, tuple[Any, ...]]] = []

    def is_connected(self) -> bool:
        return True

    async def fetch(self, sql: str, *args: Any) -> list[dict[str, Any]]:
        self.fetch_calls.append((sql, args))

        # First positional is always the min answer length.
        min_len = args[0]
        conds: list[tuple[str, Any]] = [
            ("is_public", True),
            ("has_answer", True),
            ("min_len", min_len),
        ]

        # Remaining bind params are appended in this order in the route:
        #   topic_tags @> $i  (for period, then philosopher)
        #   cursor (created_at, slug)
        #   limit (always last)
        remaining = list(args[1:-1])
        for arg in remaining:
            if isinstance(arg, list) and arg and isinstance(arg[0], str):
                conds.append(("topic", arg[0]))
            elif isinstance(arg, datetime):
                # Cursor: this datetime is paired with the next string arg.
                idx = remaining.index(arg)
                slug = remaining[idx + 1]
                conds.append(("cursor", (arg, slug)))
        limit = args[-1]

        matching = [r for r in self._rows if _matches_filters(r, conds)]

        if "ORDER BY coalesce(jsonb_array_length(final_answer_citations)" in sql:
            matching.sort(
                key=lambda r: (
                    -(len(r.get("final_answer_citations") or [])),
                    -r["started_at"].timestamp(),
                    r["share_slug"],
                )
            )
        else:
            matching.sort(key=lambda r: (-r["started_at"].timestamp(), r["share_slug"]))

        return matching[:limit]

    async def fetchrow(self, sql: str, *args: Any) -> dict[str, Any] | None:
        self.fetchrow_calls.append((sql, args))
        slug = args[0]
        for row in self._rows:
            if row.get("share_slug") == slug:
                result = dict(row)
                result["answer_length"] = len(row.get("final_answer_text") or "")
                return result
        return None


def _build_app(db: _CommunityStubDB) -> FastAPI:
    application = FastAPI()
    application.include_router(community_router)
    application.dependency_overrides[get_db] = lambda: db
    return application


@pytest.fixture(autouse=True)
def _jwt(monkeypatch: pytest.MonkeyPatch) -> None:
    # Community routes do not require auth but other imports do.
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-not-for-prod-32b")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_list_returns_only_public_queries() -> None:
    public = _make_row(query="Public one")
    private = _make_row(query="Private one", is_public=False)
    db = _CommunityStubDB([public, private])
    client = TestClient(_build_app(db))

    response = client.get("/api/graphrag/community/queries")
    assert response.status_code == 200, response.text
    body = response.json()
    queries = [item["query"] for item in body["items"]]
    assert "Public one" in queries
    assert "Private one" not in queries


def test_list_respects_min_answer_length() -> None:
    long_enough = _make_row(answer_length=1500, query="Long")
    too_short = _make_row(answer_length=200, query="Stub")
    db = _CommunityStubDB([long_enough, too_short])
    client = TestClient(_build_app(db))

    response = client.get("/api/graphrag/community/queries")
    assert response.status_code == 200
    queries = [item["query"] for item in response.json()["items"]]
    assert "Long" in queries
    assert "Stub" not in queries

    # And the bind for min length matches our constant.
    assert db.fetch_calls, "fetch should have been called"
    bind_args = db.fetch_calls[0][1]
    assert bind_args[0] == 1000


def test_list_sort_recent_vs_popular() -> None:
    older_with_many = _make_row(
        slug="aaaaaaaaaaaa",
        query="Older but cited",
        started_at=datetime(2026, 5, 10, 8, 0, 0, tzinfo=UTC),
        citations=[{"passage_id": f"p{i}"} for i in range(8)],
    )
    newer_with_few = _make_row(
        slug="bbbbbbbbbbbb",
        query="Newer but lonely",
        started_at=datetime(2026, 5, 14, 8, 0, 0, tzinfo=UTC),
        citations=[{"passage_id": "p1"}],
    )
    db = _CommunityStubDB([older_with_many, newer_with_few])
    client = TestClient(_build_app(db))

    recent = client.get("/api/graphrag/community/queries?sort=recent").json()["items"]
    assert recent[0]["query"] == "Newer but lonely"
    assert recent[1]["query"] == "Older but cited"

    popular = client.get("/api/graphrag/community/queries?sort=popular").json()["items"]
    assert popular[0]["query"] == "Older but cited"
    assert popular[0]["citation_count"] == 8


def test_list_pagination_cursor_roundtrip() -> None:
    rows = [
        _make_row(
            slug=f"slug-{i:02d}",
            query=f"Q{i}",
            started_at=datetime(2026, 5, 1, tzinfo=UTC) + timedelta(days=i),
        )
        for i in range(5)
    ]
    db = _CommunityStubDB(rows)
    client = TestClient(_build_app(db))

    first = client.get("/api/graphrag/community/queries?limit=2").json()
    assert [item["query"] for item in first["items"]] == ["Q4", "Q3"]
    assert first["next_cursor"], "Expected a continuation cursor"

    # Confirm the cursor is base64-decodable and points at the last row of page 1.
    decoded = base64.urlsafe_b64decode(first["next_cursor"].encode("ascii")).decode(
        "utf-8"
    )
    assert decoded.endswith("|slug-03")

    second = client.get(
        f"/api/graphrag/community/queries?limit=2&cursor={first['next_cursor']}"
    ).json()
    assert [item["query"] for item in second["items"]] == ["Q2", "Q1"]

    third = client.get(
        f"/api/graphrag/community/queries?limit=2&cursor={second['next_cursor']}"
    ).json()
    assert [item["query"] for item in third["items"]] == ["Q0"]
    assert third["next_cursor"] is None


def test_get_by_slug_returns_404_when_missing_or_private() -> None:
    private = _make_row(slug="private01", is_public=False)
    short = _make_row(slug="shortans01", answer_length=200)
    db = _CommunityStubDB([private, short])
    client = TestClient(_build_app(db))

    assert client.get("/api/graphrag/community/queries/private01").status_code == 404
    assert client.get("/api/graphrag/community/queries/shortans01").status_code == 404
    assert client.get("/api/graphrag/community/queries/doesnotexist").status_code == 404


def test_get_by_slug_includes_passage_citations() -> None:
    citations = [
        {"passage_id": "p1", "claim": "claim-1", "verified": True},
        {"passage_id": "p2", "claim": "claim-2", "verified": False},
    ]
    metadata = {
        "model": "kimi-k2.5-thinking",
        "sources": [{"label": "Bobzien 1998"}],
        "reasoning_path": {"steps": ["expand_lemma", "sql_retrieval", "synthesize"]},
    }
    row = _make_row(
        slug="slugxyz1234",
        citations=citations,
        metadata=metadata,
    )
    db = _CommunityStubDB([row])
    client = TestClient(_build_app(db))

    response = client.get("/api/graphrag/community/queries/slugxyz1234")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["slug"] == "slugxyz1234"
    assert body["trace_id"] == str(row["trace_id"])
    assert body["passage_citations"] == citations
    assert body["sources"] == [{"label": "Bobzien 1998"}]
    assert body["reasoning_path"]["steps"][0] == "expand_lemma"
    assert body["model"] == "kimi-k2.5-thinking"
