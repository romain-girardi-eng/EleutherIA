"""Release contract shared by KG list and statistics endpoints."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

import pytest

pytest.importorskip("fastapi")

from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from eleutheria_kg.api.routes import router, set_services  # noqa: E402
from eleutheria_kg.services.analytics import KGAnalytics  # noqa: E402
from eleutheria_kg.services.cache import KGCache  # noqa: E402


def _kg_data() -> dict[str, list[dict[str, Any]]]:
    return {
        "nodes": [
            {"id": "a", "label": "A", "type": "concept"},
            {"id": "b", "label": "B", "type": "argument"},
            {"id": "c", "label": "C", "type": "work"},
        ],
        "edges": [
            {"edge_id": "e1", "source": "a", "target": "b", "relation": "supports"},
            {
                "edge_id": "derived-inverse:e1:supported_by",
                "source": "b",
                "target": "a",
                "relation": "supported_by",
                "derived": True,
            },
        ],
    }


def _client(analytics: KGAnalytics) -> TestClient:
    cache = KGCache(default_ttl=10)
    set_services(analytics, cache)
    app = FastAPI()
    app.include_router(router, prefix="/api/kg")
    return TestClient(app)


def test_release_id_is_deterministic_and_content_sensitive() -> None:
    first = KGAnalytics(deepcopy(_kg_data()))
    second = KGAnalytics(deepcopy(_kg_data()))
    assert first.get_release_metadata() == second.get_release_metadata()

    changed = deepcopy(_kg_data())
    changed["nodes"][0]["label"] = "A revised"
    second.set_data(changed)
    assert (
        second.get_release_metadata()["release_id"]
        != first.get_release_metadata()["release_id"]
    )


def test_nodes_edges_and_statistics_expose_one_served_release() -> None:
    analytics = KGAnalytics(_kg_data())
    client = _client(analytics)

    nodes = client.get("/api/kg/nodes?limit=2&offset=0")
    edges = client.get("/api/kg/edges?limit=1&offset=0")
    stats = client.get("/api/kg/statistics")

    assert nodes.status_code == edges.status_code == stats.status_code == 200
    release = analytics.get_release_metadata()
    for response in (nodes, edges, stats):
        assert response.headers["x-eleutheria-kg-release-id"] == release["release_id"]
        assert response.headers["x-eleutheria-kg-served-total-nodes"] == "3"
        assert response.headers["x-eleutheria-kg-served-total-edges"] == "2"
        exposed = response.headers["access-control-expose-headers"].lower()
        assert "x-eleutheria-kg-release-id" in exposed

    assert len(nodes.json()) == 2
    assert len(edges.json()) == 1
    body = stats.json()
    assert body["release_id"] == release["release_id"]
    assert body["served_total_nodes"] == body["total_nodes"] == 3
    assert body["served_total_edges"] == body["total_edges"] == 2
    assert body["served_total_asserted_edges"] == 1


def test_reload_changes_contract_before_the_next_page() -> None:
    analytics = KGAnalytics(_kg_data())
    client = _client(analytics)
    first = client.get("/api/kg/edges?limit=1&offset=0")

    replacement = deepcopy(_kg_data())
    replacement["edges"].append(
        {"edge_id": "e2", "source": "b", "target": "c", "relation": "discusses"}
    )
    analytics.set_data(replacement)
    second = client.get("/api/kg/edges?limit=1&offset=1")

    assert first.headers["x-eleutheria-kg-release-id"] != second.headers[
        "x-eleutheria-kg-release-id"
    ]
    assert first.headers["x-eleutheria-kg-served-total-edges"] == "2"
    assert second.headers["x-eleutheria-kg-served-total-edges"] == "3"
