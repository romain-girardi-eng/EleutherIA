"""Snapshot-only corpus stats remain a typed 200 response."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.dependencies import get_db
from backend.routes import works_extras


class _UnavailableDB:
    async def fetchrow(self, _query: str, *_args: Any) -> dict[str, Any]:
        raise RuntimeError("database pool is not connected")


def _client(db: object) -> TestClient:
    app = FastAPI()
    app.include_router(works_extras.router, prefix="/api/works")
    app.dependency_overrides[get_db] = lambda: db
    return TestClient(app)


def test_snapshot_only_stats_use_known_counts_without_inventing_unknowns(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    snapshot = tmp_path / "stats.json"
    snapshot.write_text(
        json.dumps(
            {
                "generated_at": "2026-08-24T00:00:00Z",
                "kg": {"works": 251},
                "corpus": {"passages": 21158, "passage_citations": 19836},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(works_extras, "resolve_data_stats_snapshot", lambda: snapshot)

    response = _client(_UnavailableDB()).get("/api/works/stats")

    assert response.status_code == 200, response.text
    assert response.json() == {
        "status": "partial",
        "available": True,
        "source": "snapshot",
        "snapshot_generated_at": "2026-08-24T00:00:00Z",
        "works": {
            "total_works": 251,
            "unique_authors": None,
            "total_words": None,
            "languages_count": None,
        },
        "passages": {"total_passages": 21158, "avg_passage_words": None},
        "total_citations": 19836,
        "unavailable_fields": [
            "works.unique_authors",
            "works.total_words",
            "works.languages_count",
            "passages.avg_passage_words",
        ],
    }


def test_missing_snapshot_is_typed_unavailable_not_500(monkeypatch: Any) -> None:
    monkeypatch.setattr(works_extras, "resolve_data_stats_snapshot", lambda: None)

    response = _client(_UnavailableDB()).get("/api/works/stats")

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == body["source"] == "unavailable"
    assert body["available"] is False
    assert body["works"]["total_works"] is None
    assert body["passages"]["total_passages"] is None
    assert body["total_citations"] is None
