"""Unit tests for the grouped ``GET /api/kg/nodes/{node_id}/neighbors``
endpoint and the deprecated ``/api/kg/node/{node_id}/connections`` redirect.
"""

from __future__ import annotations

from typing import Any

import pytest
from eleutheria_kg.api.routes import router as kg_router
from eleutheria_kg.api.routes import set_services
from eleutheria_kg.services.analytics import KGAnalytics
from eleutheria_kg.services.cache import KGCache
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.dependencies import get_analytics, get_cache
from backend.routes.kg_extras import router as kg_extras_router


def _kg_data() -> dict[str, Any]:
    return {
        "nodes": [
            {
                "id": "passage_X",
                "label": "Passage X",
                "type": "passage",
                "period": "Classical Greek",
            },
            {"id": "work_Y", "label": "Work Y", "type": "work"},
            {"id": "scholar_Z", "label": "Scholar Z", "type": "argument"},
        ],
        "edges": [
            {"source": "passage_X", "target": "work_Y", "relation": "part_of"},
            {
                "source": "scholar_Z",
                "target": "passage_X",
                "relation": "cites_primary_source",
            },
        ],
    }


@pytest.fixture
def analytics() -> KGAnalytics:
    a = KGAnalytics()
    a.set_data(_kg_data())
    return a


@pytest.fixture
def cache() -> KGCache:
    return KGCache(default_ttl=10)


@pytest.fixture
def app(analytics: KGAnalytics, cache: KGCache) -> FastAPI:
    set_services(analytics, cache)
    application = FastAPI()
    application.include_router(kg_router, prefix="/api/kg")
    application.include_router(kg_extras_router, prefix="/api/kg")
    application.dependency_overrides[get_analytics] = lambda: analytics
    application.dependency_overrides[get_cache] = lambda: cache
    return application


def test_neighbors_grouped_by_direction_and_relation(app: FastAPI) -> None:
    client = TestClient(app)
    response = client.get("/api/kg/nodes/passage_X/neighbors")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["node_id"] == "passage_X"
    assert body["node"]["label"] == "Passage X"
    out = body["neighbors"]["outgoing"]
    inc = body["neighbors"]["incoming"]
    assert "part_of" in out
    assert out["part_of"][0]["node_id"] == "work_Y"
    assert out["part_of"][0]["node_type"] == "work"
    assert "cites_primary_source" in inc
    assert inc["cites_primary_source"][0]["node_id"] == "scholar_Z"
    assert body["total_count"] == 2


def test_neighbors_unknown_node_404(app: FastAPI) -> None:
    client = TestClient(app)
    response = client.get("/api/kg/nodes/passage_missing/neighbors")
    assert response.status_code == 404


def test_legacy_connections_redirects_301(app: FastAPI) -> None:
    client = TestClient(app)
    response = client.get(
        "/api/kg/node/passage_X/connections",
        follow_redirects=False,
    )
    assert response.status_code == 301
    assert response.headers["location"] == "/api/kg/nodes/passage_X/neighbors"


def test_legacy_connections_preserves_query(app: FastAPI) -> None:
    client = TestClient(app)
    response = client.get(
        "/api/kg/node/passage_X/connections?depth=2",
        follow_redirects=False,
    )
    assert response.status_code == 301
    assert "depth=2" in response.headers["location"]
