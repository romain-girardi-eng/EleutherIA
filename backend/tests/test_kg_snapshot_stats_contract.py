"""`/api/kg/stats` separates served-release and live database totals."""

from __future__ import annotations

from typing import Any

from eleutheria_kg.api.routes import router as kg_router
from eleutheria_kg.api.routes import set_services
from eleutheria_kg.services.analytics import KGAnalytics
from eleutheria_kg.services.cache import KGCache
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.dependencies import get_analytics, get_cache, get_db
from backend.routes.kg_extras import router as kg_extras_router


def _analytics() -> KGAnalytics:
    return KGAnalytics(
        {
            "nodes": [
                {"id": "a", "label": "A", "type": "concept"},
                {"id": "b", "label": "B", "type": "argument"},
                {"id": "c", "label": "C", "type": "work"},
            ],
            "edges": [
                {"source": "a", "target": "b", "relation": "supports"},
                {
                    "source": "b",
                    "target": "a",
                    "relation": "supported_by",
                    "derived": True,
                },
            ],
        }
    )


class _LiveDB:
    def __init__(self, nodes: int, asserted_edges: int) -> None:
        self.nodes = nodes
        self.asserted_edges = asserted_edges

    async def fetchrow(self, query: str, *_args: Any) -> dict[str, int]:
        if "kg_nodes" in query:
            return {"n": self.nodes}
        return {"n": self.asserted_edges}

    async def fetch(self, query: str, *_args: Any) -> list[dict[str, Any]]:
        if "GROUP BY type" in query:
            return [{"type": "concept", "n": self.nodes}]
        return [{"relation": "supports", "n": self.asserted_edges}]


def _client(db: _LiveDB) -> TestClient:
    analytics = _analytics()
    cache = KGCache(default_ttl=10)
    set_services(analytics, cache)
    app = FastAPI()
    app.include_router(kg_router, prefix="/api/kg")
    app.include_router(kg_extras_router, prefix="/api/kg")
    app.dependency_overrides[get_analytics] = lambda: analytics
    app.dependency_overrides[get_cache] = lambda: cache
    app.dependency_overrides[get_db] = lambda: db
    return TestClient(app)


def test_live_totals_never_overwrite_the_served_release() -> None:
    response = _client(_LiveDB(nodes=4, asserted_edges=2)).get("/api/kg/stats")
    assert response.status_code == 200, response.text
    body = response.json()

    assert body["total_nodes"] == body["served_total_nodes"] == 3
    assert body["total_edges"] == body["served_total_edges"] == 2
    assert body["served_total_asserted_edges"] == 1
    assert body["live_total_nodes"] == 4
    assert body["live_total_edges"] == 2
    assert body["node_types"] == {"concept": 1, "argument": 1, "work": 1}
    assert body["live_node_types"] == {"concept": 4}
    assert body["snapshot_stale"] is True
    assert body["snapshot_status"] == "stale"
    assert body["snapshot_stale_reasons"] == ["node_count", "asserted_edge_count"]
    assert response.headers["x-eleutheria-kg-release-id"] == body["release_id"]


def test_derived_inverse_edges_do_not_create_a_false_stale_signal() -> None:
    response = _client(_LiveDB(nodes=3, asserted_edges=1)).get("/api/kg/stats")
    assert response.status_code == 200, response.text
    body = response.json()

    assert body["served_total_edges"] == 2
    assert body["served_total_asserted_edges"] == body["live_total_edges"] == 1
    assert body["snapshot_stale"] is False
    assert body["snapshot_status"] == "current"
    assert body["snapshot_stale_reasons"] == []
