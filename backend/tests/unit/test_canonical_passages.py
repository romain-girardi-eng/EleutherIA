"""Unit tests for the canonical-passages endpoints.

Exercises the SQL/routing/shape logic in ``backend.routes.community`` for
``GET /api/graphrag/community/canonical-passages`` and the detail variant.
Uses a stateful in-memory stub DB mirroring the pattern in
``test_community_routes.py``.
"""

from __future__ import annotations

import uuid
from collections import Counter, defaultdict
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


def _make_trace(
    *,
    slug: str | None = None,
    query: str = "What is the prohairesis in Epictetus?",
    answer_length: int = 2000,
    citations: list[dict[str, Any]] | None = None,
    is_public: bool = True,
    started_at: datetime | None = None,
) -> dict[str, Any]:
    trace_uuid = uuid.uuid4()
    return {
        "trace_id": trace_uuid,
        "share_slug": slug or trace_uuid.hex[:12],
        "query": query,
        "final_answer_text": "x" * answer_length if answer_length else None,
        "final_answer_citations": citations if citations is not None else [],
        "started_at": started_at or datetime(2026, 5, 15, 10, 0, 0, tzinfo=UTC),
        "is_public": is_public,
    }


def _make_passage(
    *,
    passage_id: str,
    text_content: str = "Some Greek text",
    canonical_ref: str = "1.1",
    work_title: str = "Discourses",
    author: str = "Epictetus",
    period: str = "Imperial",
    language: str = "grc",
) -> dict[str, Any]:
    return {
        "passage_id": passage_id,
        "text_content": text_content,
        "canonical_ref": canonical_ref,
        "work_title": work_title,
        "author": author,
        "period": period,
        "language": language,
    }


class _CanonicalStubDB:
    """In-memory fake that supports the canonical-passages SQL shape.

    Holds two collections:
    * ``traces`` — list of public/private query traces with citations
    * ``passages`` — list of joined passage+work rows keyed by passage_id

    Reads the SQL string + bind params and routes to the right computation.
    """

    def __init__(
        self,
        traces: list[dict[str, Any]],
        passages: list[dict[str, Any]] | None = None,
    ) -> None:
        self.traces = traces
        self.passages = {p["passage_id"]: p for p in (passages or [])}
        self.fetch_calls: list[tuple[str, tuple[Any, ...]]] = []
        self.fetchrow_calls: list[tuple[str, tuple[Any, ...]]] = []

    def is_connected(self) -> bool:
        return True

    # ------------------------------------------------------------------
    # Helpers shared across queries
    # ------------------------------------------------------------------

    def _eligible_traces(self, min_len: int) -> list[dict[str, Any]]:
        return [
            t
            for t in self.traces
            if t.get("is_public")
            and t.get("final_answer_text")
            and len(t["final_answer_text"]) >= min_len
        ]

    def _passage_filter_ok(
        self, passage_id: str, period: str | None, author: str | None
    ) -> bool:
        passage = self.passages.get(passage_id)
        if period:
            if not passage or not passage.get("period"):
                return False
            if period.lower() not in passage["period"].lower():
                return False
        if author:
            if not passage or not passage.get("author"):
                return False
            if author.lower() not in passage["author"].lower():
                return False
        return True

    # ------------------------------------------------------------------
    # asyncpg-style API
    # ------------------------------------------------------------------

    async def fetch(self, sql: str, *args: Any) -> list[dict[str, Any]]:
        self.fetch_calls.append((sql, args))

        if "WITH cited AS" in sql and "ORDER BY a.distinct_answer_count" in sql:
            # list_canonical_passages aggregation
            period_param, author_param, limit, min_len = args
            return self._aggregate(period_param, author_param, limit, min_len)

        if "WITH per_trace AS" in sql:
            # detail: per-trace citation counts for one passage
            passage_id, min_len, cap = args
            return self._per_trace(passage_id, min_len, cap)

        raise AssertionError(f"Unexpected fetch SQL:\n{sql}")

    async def fetchrow(self, sql: str, *args: Any) -> dict[str, Any] | None:
        self.fetchrow_calls.append((sql, args))

        if "SELECT count(*)" in sql and "AS total" in sql:
            period_param, author_param, min_len = args
            return {"total": self._total(period_param, author_param, min_len)}

        if "SELECT\n            $1 AS passage_id" in sql:
            passage_id, min_len = args
            return self._aggregate_one(passage_id, min_len)

        raise AssertionError(f"Unexpected fetchrow SQL:\n{sql}")

    # ------------------------------------------------------------------
    # Logic
    # ------------------------------------------------------------------

    def _aggregate(
        self,
        period_param: str | None,
        author_param: str | None,
        limit: int,
        min_len: int,
    ) -> list[dict[str, Any]]:
        per_passage_count: Counter[str] = Counter()
        per_passage_distinct: dict[str, set[str]] = defaultdict(set)
        labels: dict[str, str] = {}

        for trace in self._eligible_traces(min_len):
            for cit in trace["final_answer_citations"]:
                if cit.get("type") != "passage":
                    continue
                pid = cit.get("id")
                if not pid:
                    continue
                per_passage_count[pid] += 1
                per_passage_distinct[pid].add(trace["share_slug"])
                labels.setdefault(pid, cit.get("label") or "")

        rows: list[dict[str, Any]] = []
        for pid, count in per_passage_count.items():
            if not self._passage_filter_ok(pid, period_param, author_param):
                continue
            passage = self.passages.get(pid, {})
            distinct_slugs = sorted(per_passage_distinct[pid])
            rows.append(
                {
                    "passage_id": pid,
                    "label": labels[pid],
                    "citation_count": count,
                    "distinct_answer_count": len(distinct_slugs),
                    "preview_slugs": distinct_slugs[:5],
                    "text_content": passage.get("text_content"),
                    "canonical_ref": passage.get("canonical_ref"),
                    "language": passage.get("language"),
                    "work_title": passage.get("work_title"),
                    "author_label": passage.get("author"),
                    "period": passage.get("period"),
                }
            )

        rows.sort(
            key=lambda r: (
                -r["distinct_answer_count"],
                -r["citation_count"],
                r["passage_id"],
            )
        )
        return rows[:limit]

    def _total(self, period: str | None, author: str | None, min_len: int) -> int:
        seen: set[str] = set()
        for trace in self._eligible_traces(min_len):
            for cit in trace["final_answer_citations"]:
                if cit.get("type") != "passage":
                    continue
                pid = cit.get("id")
                if pid and self._passage_filter_ok(pid, period, author):
                    seen.add(pid)
        return len(seen)

    def _aggregate_one(self, passage_id: str, min_len: int) -> dict[str, Any] | None:
        count = 0
        distinct: set[str] = set()
        labels: list[str] = []
        for trace in self._eligible_traces(min_len):
            for cit in trace["final_answer_citations"]:
                if cit.get("type") != "passage":
                    continue
                if cit.get("id") != passage_id:
                    continue
                count += 1
                distinct.add(trace["share_slug"])
                if cit.get("label"):
                    labels.append(cit["label"])

        if count == 0:
            return None

        passage = self.passages.get(passage_id, {})
        return {
            "passage_id": passage_id,
            "label": min(labels) if labels else "",
            "citation_count": count,
            "distinct_answer_count": len(distinct),
            "preview_slugs": sorted(distinct)[:5],
            "text_content": passage.get("text_content"),
            "canonical_ref": passage.get("canonical_ref"),
            "language": passage.get("language"),
            "work_title": passage.get("work_title"),
            "author_label": passage.get("author"),
            "period": passage.get("period"),
        }

    def _per_trace(
        self, passage_id: str, min_len: int, cap: int
    ) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for trace in self._eligible_traces(min_len):
            occurrences = sum(
                1
                for cit in trace["final_answer_citations"]
                if cit.get("type") == "passage" and cit.get("id") == passage_id
            )
            if occurrences == 0:
                continue
            rows.append(
                {
                    "share_slug": trace["share_slug"],
                    "query": trace["query"],
                    "final_answer_text": trace["final_answer_text"],
                    "started_at": trace["started_at"],
                    "cnt": occurrences,
                }
            )
        rows.sort(
            key=lambda r: (-r["cnt"], -r["started_at"].timestamp(), r["share_slug"]),
        )
        return rows[:cap]


def _build_app(db: _CanonicalStubDB) -> FastAPI:
    application = FastAPI()
    application.include_router(community_router)
    application.dependency_overrides[get_db] = lambda: db
    return application


@pytest.fixture(autouse=True)
def _jwt(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-not-for-prod-32b")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def _cit(passage_id: str, label: str = "Epict. Disc. 1.1") -> dict[str, Any]:
    return {"type": "passage", "id": passage_id, "label": label}


def test_list_excludes_non_public_traces() -> None:
    public = _make_trace(
        slug="public01",
        citations=[_cit("p-1")],
    )
    private = _make_trace(
        slug="private01",
        citations=[_cit("p-2")],
        is_public=False,
    )
    db = _CanonicalStubDB(
        [public, private],
        passages=[_make_passage(passage_id="p-1"), _make_passage(passage_id="p-2")],
    )
    client = TestClient(_build_app(db))

    response = client.get("/api/graphrag/community/canonical-passages")
    assert response.status_code == 200, response.text
    items = response.json()["items"]
    passage_ids = [item["passage_id"] for item in items]
    assert "p-1" in passage_ids
    assert "p-2" not in passage_ids


def test_list_excludes_short_answers() -> None:
    long_one = _make_trace(
        slug="long-one",
        answer_length=1500,
        citations=[_cit("p-1")],
    )
    too_short = _make_trace(
        slug="short-one",
        answer_length=200,
        citations=[_cit("p-2")],
    )
    db = _CanonicalStubDB(
        [long_one, too_short],
        passages=[_make_passage(passage_id="p-1"), _make_passage(passage_id="p-2")],
    )
    client = TestClient(_build_app(db))

    response = client.get("/api/graphrag/community/canonical-passages")
    assert response.status_code == 200
    passage_ids = [item["passage_id"] for item in response.json()["items"]]
    assert "p-1" in passage_ids
    assert "p-2" not in passage_ids


def test_list_groups_same_passage_across_traces() -> None:
    """One passage cited by multiple answers should appear once with
    aggregated counts."""
    t1 = _make_trace(slug="t-aaaaaaaa", citations=[_cit("p-shared")])
    t2 = _make_trace(slug="t-bbbbbbbb", citations=[_cit("p-shared"), _cit("p-shared")])
    t3 = _make_trace(slug="t-cccccccc", citations=[_cit("p-shared")])
    db = _CanonicalStubDB(
        [t1, t2, t3],
        passages=[_make_passage(passage_id="p-shared")],
    )
    client = TestClient(_build_app(db))

    response = client.get("/api/graphrag/community/canonical-passages")
    assert response.status_code == 200
    items = response.json()["items"]
    assert len(items) == 1
    item = items[0]
    assert item["passage_id"] == "p-shared"
    # 4 total citation occurrences (1 + 2 + 1)
    assert item["citation_count"] == 4
    # but only 3 distinct answers
    assert item["distinct_answer_count"] == 3
    assert sorted(item["preview_slugs"]) == ["t-aaaaaaaa", "t-bbbbbbbb", "t-cccccccc"]


def test_list_orders_by_distinct_answer_count_desc() -> None:
    """A passage cited by many distinct answers should rank above one
    that is cited many times by a single answer."""
    many_distinct = [
        _make_trace(slug=f"slug{i:08d}", citations=[_cit("p-broad")]) for i in range(5)
    ]
    one_heavy = _make_trace(
        slug="oneheavy01",
        citations=[_cit("p-narrow")] * 20,
    )
    db = _CanonicalStubDB(
        many_distinct + [one_heavy],
        passages=[
            _make_passage(passage_id="p-broad"),
            _make_passage(passage_id="p-narrow"),
        ],
    )
    client = TestClient(_build_app(db))

    response = client.get("/api/graphrag/community/canonical-passages")
    assert response.status_code == 200
    items = response.json()["items"]
    assert items[0]["passage_id"] == "p-broad"
    assert items[0]["distinct_answer_count"] == 5
    assert items[1]["passage_id"] == "p-narrow"
    assert items[1]["distinct_answer_count"] == 1
    # And the narrow one's citation_count is still 20
    assert items[1]["citation_count"] == 20


def test_list_filters_by_period() -> None:
    trace = _make_trace(
        slug="trace00001",
        citations=[_cit("p-hellen"), _cit("p-imperial")],
    )
    db = _CanonicalStubDB(
        [trace],
        passages=[
            _make_passage(passage_id="p-hellen", period="Hellenistic"),
            _make_passage(passage_id="p-imperial", period="Roman Imperial"),
        ],
    )
    client = TestClient(_build_app(db))

    response = client.get(
        "/api/graphrag/community/canonical-passages?period=hellenistic"
    )
    assert response.status_code == 200
    items = response.json()["items"]
    passage_ids = [i["passage_id"] for i in items]
    assert passage_ids == ["p-hellen"]


def test_detail_returns_citing_answers() -> None:
    t1 = _make_trace(
        slug="alpha00001",
        query="What is fate?",
        citations=[_cit("p-cited"), _cit("p-cited")],
        started_at=datetime(2026, 5, 14, tzinfo=UTC),
    )
    t2 = _make_trace(
        slug="beta000001",
        query="Is there free will?",
        citations=[_cit("p-cited")],
        started_at=datetime(2026, 5, 13, tzinfo=UTC),
    )
    db = _CanonicalStubDB(
        [t1, t2],
        passages=[
            _make_passage(
                passage_id="p-cited",
                text_content="Long Greek text here…",
                canonical_ref="Disc. 1.1",
            )
        ],
    )
    client = TestClient(_build_app(db))

    response = client.get("/api/graphrag/community/canonical-passages/p-cited")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["passage_id"] == "p-cited"
    assert body["citation_count"] == 3  # 2 + 1
    assert body["distinct_answer_count"] == 2
    assert body["full_text"] == "Long Greek text here…"

    citing = body["citing_answers"]
    assert len(citing) == 2
    # alpha has 2 occurrences, should sort first
    assert citing[0]["slug"] == "alpha00001"
    assert citing[0]["citation_count"] == 2
    assert citing[1]["slug"] == "beta000001"
    assert citing[1]["citation_count"] == 1


def test_detail_caps_citing_answers_at_50() -> None:
    traces = [
        _make_trace(
            slug=f"slug{i:08d}",
            citations=[_cit("p-popular")],
            started_at=datetime(2026, 5, 1, tzinfo=UTC) + timedelta(hours=i),
        )
        for i in range(60)
    ]
    db = _CanonicalStubDB(
        traces,
        passages=[_make_passage(passage_id="p-popular")],
    )
    client = TestClient(_build_app(db))

    response = client.get("/api/graphrag/community/canonical-passages/p-popular")
    assert response.status_code == 200
    body = response.json()
    assert body["citation_count"] == 60
    assert body["distinct_answer_count"] == 60
    # citing_answers list is capped, even though all 60 are eligible
    assert len(body["citing_answers"]) == 50


def test_detail_returns_404_when_passage_not_cited() -> None:
    db = _CanonicalStubDB([], passages=[])
    client = TestClient(_build_app(db))
    response = client.get("/api/graphrag/community/canonical-passages/p-unknown")
    assert response.status_code == 404
