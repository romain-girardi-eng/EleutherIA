from __future__ import annotations

import json
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import pytest

from scripts.graphrag_trace_report import (
    TRACE_QUERY,
    fetch_rows,
    render_markdown,
    summarize_rows,
)


class FakePool:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self.rows = rows
        self.calls: list[tuple[str, tuple[object, ...]]] = []

    async def fetch(self, query: str, *args: object) -> list[dict[str, Any]]:
        self.calls.append((query, args))
        return self.rows


def _rows() -> list[dict[str, Any]]:
    return [
        {
            "trace_id": "trace-1",
            "started_at": datetime(2026, 7, 10, tzinfo=UTC),
            "completed_at": datetime(2026, 7, 10, 0, 0, 1, tzinfo=UTC),
            "mode": "fast",
            "total_latency_ms": 500,
            "total_cost_usd": 0.03,
            "metadata": {
                "stage_metrics": [
                    {"stage": "classify", "ms": 100, "tokens": 10},
                    {"stage": "synthesis", "ms": 400, "tokens": 90},
                ],
                "answer_metadata": {
                    "quality_badge": "Gold",
                    "publication_gate": {
                        "status": "passed",
                        "publishable": True,
                        "reasons": [],
                    },
                },
            },
            "provider_usage": {
                "codex": {"cost_usd": 0.03, "total_tokens": 100, "calls": 2}
            },
            "final_answer_citations": [
                {"type": "passage", "layer": "primary", "verified": True},
                {"type": "node", "layer": "secondary", "verified": False},
            ],
        },
        {
            "trace_id": "trace-2",
            "started_at": "2026-07-11T00:00:00Z",
            "completed_at": None,
            "mode": "deep",
            "total_latency_ms": 1000,
            "total_cost_usd": 0.01,
            "metadata": json.dumps(
                {
                    "answer_metadata": {
                        "quality_badge": "Blocked",
                        "citation_verifier_v2": {
                            "status": "failed",
                            "total_citations": 2,
                            "verified": 1,
                            "rejected": 1,
                        },
                    }
                }
            ),
            "provider_usage": json.dumps(
                {
                    "gemini": {
                        "cost_usd": 0.01,
                        "total_tokens": 50,
                        "calls": 1,
                    }
                }
            ),
            "final_answer_citations": json.dumps(
                [{"type": "passage", "layer": "primary", "verified": False}]
            ),
        },
        {
            "trace_id": "trace-3",
            "started_at": datetime(2026, 8, 1, tzinfo=UTC),
            "completed_at": datetime(2026, 8, 1, 0, 0, 1, tzinfo=UTC),
            "mode": "react",
            "total_latency_ms": 20,
            "total_cost_usd": 0.0,
            "metadata": {
                "cache_hit": True,
                "answer_metadata": {
                    "quality_badge": "Gold",
                    "publication_gate": {
                        "status": "passed",
                        "publishable": True,
                        "reasons": [],
                    },
                },
            },
            "provider_usage": {},
            "final_answer_citations": [],
        },
        {
            # asyncpg decodes NUMERIC(10,6) columns as Decimal, as in production.
            "trace_id": "trace-4",
            "started_at": datetime(2026, 8, 2, tzinfo=UTC),
            "completed_at": datetime(2026, 8, 2, 0, 0, 2, tzinfo=UTC),
            "mode": "deep",
            "total_latency_ms": 2000,
            "total_cost_usd": Decimal("0.020000"),
            "metadata": {
                "answer_metadata": {
                    "quality_badge": "Gold",
                    "publication_gate": {
                        "status": "passed",
                        "publishable": True,
                        "reasons": [],
                    },
                },
            },
            "provider_usage": {
                "codex": {"cost_usd": 0.02, "total_tokens": 80, "calls": 1}
            },
            "final_answer_citations": [
                {"type": "passage", "layer": "primary", "verified": True},
            ],
        },
    ]


@pytest.mark.asyncio
async def test_fetch_rows_uses_only_the_read_only_trace_select() -> None:
    pool = FakePool(_rows())
    since = datetime(2026, 7, 1, tzinfo=UTC)

    rows = await fetch_rows(pool, since=since)

    assert rows == pool.rows
    assert pool.calls == [(TRACE_QUERY, (since,))]
    assert TRACE_QUERY.lstrip().startswith("SELECT")
    assert "INSERT" not in TRACE_QUERY
    assert "UPDATE" not in TRACE_QUERY
    assert "DELETE" not in TRACE_QUERY


def test_summarize_rows_covers_operational_baseline_metrics() -> None:
    report = summarize_rows(_rows())

    assert report["counts"] == {
        "traces": 4,
        "pipeline_runs": 3,
        "cache_hits": 1,
        "incomplete_runs": 1,
        "rows_with_stage_metrics": 1,
    }
    assert report["latency_ms"]["overall"]["p50"] == 750
    assert report["latency_ms"]["overall"]["p95"] == 1850
    assert report["latency_ms"]["by_stage"]["classify"]["p50"] == 100
    assert report["latency_ms"]["by_stage"]["synthesis"]["p95"] == 400
    assert report["latency_ms"]["by_stage"]["total_fallback"]["count"] == 3
    assert report["cost_usd"]["per_query"]["count"] == 4
    assert report["cost_usd"]["per_query"]["p50"] == 0.015
    assert report["cost_usd"]["per_query"]["mean"] == pytest.approx(0.015)
    assert report["cost_usd"]["per_query"]["max"] == 0.03
    assert report["cost_usd"]["per_query"]["total"] == pytest.approx(0.06)
    assert report["cost_usd"]["by_provider"]["codex"] == {
        "cost_usd": 0.05,
        "tokens": 180,
        "calls": 3,
    }
    assert report["quality_badge_by_month"]["2026-07"] == {
        "Blocked": 1,
        "Gold": 1,
    }
    assert report["publication"]["verdicts"] == {"blocked": 1, "passed": 3}
    assert report["publication"]["withholding_reasons"] == {
        "citation_audit_not_passed": 1,
        "not_all_citations_verified": 1,
        "rejected_citations_present": 1,
    }
    assert report["citations"]["verified_by_type_layer"]["passage/primary"] == {
        "verified": 2,
        "total": 3,
        "verified_ratio": 0.6667,
    }


def test_decimal_total_cost_usd_feeds_the_per_query_distribution() -> None:
    """Regression: a Decimal ``total_cost_usd`` (asyncpg NUMERIC) used to be
    dropped, leaving the per-query cost line at ``None`` while the
    per-provider table (JSONB floats) was populated."""
    rows = [row for row in _rows() if row["trace_id"] == "trace-4"]

    report = summarize_rows(rows)
    per_query = report["cost_usd"]["per_query"]

    assert per_query == {
        "count": 1,
        "p50": 0.02,
        "p95": 0.02,
        "mean": 0.02,
        "max": 0.02,
        "total": 0.02,
    }
    markdown = render_markdown(report, since=None)
    assert "Per query p50 / mean / max: 0.02 / 0.02 / 0.02 USD" in markdown
    assert "Per query p50 / mean / max: None" not in markdown


def test_render_markdown_exposes_each_required_section() -> None:
    markdown = render_markdown(summarize_rows(_rows()), since=None)

    assert "Pipeline runs / cache hits: 3 / 1" in markdown
    assert "Overall p50 / p90 / p95" in markdown
    assert "| synthesis | 1 | 400.0 | 400.0 | 400.0 |" in markdown
    assert "## Quality badge by month" in markdown
    assert "## Publication and withholding" in markdown
    assert "## Citation verification" in markdown
