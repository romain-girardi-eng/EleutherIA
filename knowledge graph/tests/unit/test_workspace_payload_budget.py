"""Release-level transfer budget for the browser's complete graph view."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

pytest.importorskip("fastapi")

from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from starlette.middleware.gzip import GZipMiddleware  # noqa: E402

from eleutheria_kg.api.routes import router, set_services  # noqa: E402
from eleutheria_kg.services.analytics import KGAnalytics  # noqa: E402
from eleutheria_kg.services.cache import KGCache  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
TRANSFER_BUDGET_BYTES = 2_000_000


def _jsonl(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text().splitlines() if line]


def test_current_complete_workspace_release_stays_below_two_megabytes() -> None:
    analytics = KGAnalytics(
        {
            "nodes": _jsonl(ROOT / "data/kg/nodes.jsonl"),
            "edges": _jsonl(ROOT / "data/kg/edges.jsonl"),
        }
    )
    set_services(analytics, KGCache(default_ttl=10))
    application = FastAPI()
    application.add_middleware(
        GZipMiddleware,
        minimum_size=1024,
        compresslevel=6,
    )
    application.include_router(router, prefix="/api/kg")
    client = TestClient(application)

    stats = client.get("/api/kg/workspace/stats").json()
    release_id = stats["release_id"]
    requests = [
        ("nodes", 0),
        *[
            ("edges", offset)
            for offset in range(0, stats["served_total_edges"], 50_000)
        ],
    ]
    compressed_bytes = 0
    for resource, offset in requests:
        response = client.get(
            f"/api/kg/workspace/{resource}",
            params={"limit": 50_000, "offset": offset, "release_id": release_id},
            headers={"Accept-Encoding": "gzip"},
        )
        assert response.status_code == 200
        assert response.headers["content-encoding"] == "gzip"
        compressed_bytes += int(response.headers["content-length"])

    assert compressed_bytes <= TRANSFER_BUDGET_BYTES, (
        f"workspace release transfer {compressed_bytes:,} exceeds "
        f"{TRANSFER_BUDGET_BYTES:,} bytes"
    )
