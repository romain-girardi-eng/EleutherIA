"""Compact, release-pinned workspace graph contract."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

import pytest

pytest.importorskip("fastapi")
nx = pytest.importorskip("networkx")

from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from eleutheria_kg.api.routes import (  # noqa: E402
    _workspace_asserted_edges,
    router,
    set_services,
)
from eleutheria_kg.services.analytics import KGAnalytics  # noqa: E402
from eleutheria_kg.services.cache import KGCache  # noqa: E402


def _kg_data() -> dict[str, list[dict[str, Any]]]:
    return {
        "nodes": [
            {
                "id": "a",
                "label": "Alpha",
                "type": "person",
                "description": "Long editorial detail",
                "period": "Modern",
                "role": "historian",
                "metadata": {
                    "greek_term": "ἄλφα",
                    "private_provenance": "not a workspace field",
                },
                "duplicated_export_field": "not a workspace field",
            },
            {"id": "b", "label": "Beta", "type": "concept"},
            {"id": "c", "label": "Gamma", "type": "work"},
        ],
        "edges": [
            {
                "edge_id": "e1",
                "source": "a",
                "target": "b",
                "relation": "supports",
                "metadata": {"weight": 0.8},
            },
            {
                "edge_id": "derived-e1",
                "source": "b",
                "target": "a",
                "relation": "supported_by",
                "derived": True,
            },
            {"source": "b", "target": "c", "relation": "discusses"},
            {
                "edge_id": "derived-e2",
                "source": "c",
                "target": "b",
                "relation": "discussed_in",
                "metadata": {"derived": "true"},
            },
        ],
    }


def _client(analytics: KGAnalytics) -> TestClient:
    set_services(analytics, KGCache(default_ttl=10))
    app = FastAPI()
    app.include_router(router, prefix="/api/kg")
    return TestClient(app)


def test_workspace_pages_are_compact_asserted_and_exactly_counted() -> None:
    analytics = KGAnalytics(_kg_data())
    client = _client(analytics)
    release_id = str(analytics.get_release_metadata()["release_id"])

    stats = client.get("/api/kg/workspace/stats")
    nodes = client.get(
        "/api/kg/workspace/nodes",
        params={"limit": 2, "offset": 0, "release_id": release_id},
    )
    edges = client.get(
        "/api/kg/workspace/edges",
        params={"limit": 1, "offset": 1, "release_id": release_id},
    )

    assert stats.status_code == nodes.status_code == edges.status_code == 200
    assert stats.json()["served_total_nodes"] == len(analytics.kg_data["nodes"])
    assert stats.json()["served_total_edges"] == len(
        _workspace_asserted_edges(analytics)
    )
    assert stats.json()["source_total_edges"] == 4
    assert stats.json()["omitted_derived_inverse_edges"] == 2
    assert stats.json()["edge_semantics"] == {
        "set": "asserted",
        "direction": "source_to_target",
        "identity": "release_position_client_derived",
        "inverse_materialization": "omitted",
        "weak_connectivity": "equivalent_to_served_graph",
    }

    alpha = nodes.json()["nodes"][0]
    assert alpha == {
        "id": "a",
        "label": "Alpha",
        "type": "person",
        "period": "Modern",
        "scholarly_role": "historian",
        "greek_term": "ἄλφα",
    }
    assert "description" not in alpha
    assert "metadata" not in alpha
    assert edges.json()["edges"] == [
        {
            "source": "b",
            "target": "c",
            "relation": "discusses",
        }
    ]
    for response in (stats, nodes, edges):
        assert response.json()["release_id"] == release_id
        assert response.headers["x-eleutheria-kg-served-total-edges"] == "2"


def test_workspace_node_detail_is_compact_and_release_bound() -> None:
    analytics = KGAnalytics(_kg_data())
    client = _client(analytics)
    release_id = str(analytics.get_release_metadata()["release_id"])

    response = client.get(
        "/api/kg/workspace/nodes/a", params={"release_id": release_id}
    )

    assert response.status_code == 200
    assert response.json()["node"] == {
        "id": "a",
        "label": "Alpha",
        "type": "person",
        "description": "Long editorial detail",
        "period": "Modern",
        "scholarly_role": "historian",
        "greek_term": "ἄλφα",
    }


def test_old_release_precondition_fails_before_returning_a_new_page() -> None:
    analytics = KGAnalytics(_kg_data())
    client = _client(analytics)
    old_release = str(analytics.get_release_metadata()["release_id"])
    replacement = deepcopy(_kg_data())
    replacement["nodes"].append({"id": "d", "label": "Delta", "type": "argument"})
    analytics.set_data(replacement)
    new_release = str(analytics.get_release_metadata()["release_id"])

    response = client.get(
        "/api/kg/workspace/nodes",
        params={"limit": 2, "offset": 2, "release_id": old_release},
    )

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "kg_release_mismatch"
    assert response.json()["detail"]["served_release_id"] == new_release
    assert response.headers["x-eleutheria-kg-release-id"] == new_release


def test_legacy_lists_keep_full_records_and_materialized_inverses() -> None:
    analytics = KGAnalytics(_kg_data())
    client = _client(analytics)

    nodes = client.get("/api/kg/nodes", params={"limit": 1})
    edges = client.get("/api/kg/edges", params={"limit": 10})

    assert nodes.status_code == edges.status_code == 200
    assert nodes.json()[0]["metadata"]["private_provenance"] == "not a workspace field"
    assert len(edges.json()) == 4
    assert any(edge.get("derived") for edge in edges.json())
    assert edges.headers["x-eleutheria-kg-served-total-edges"] == "4"


def test_omitting_inverse_twins_preserves_weak_connectivity() -> None:
    analytics = KGAnalytics(_kg_data())
    asserted = [edge for _, edge in _workspace_asserted_edges(analytics)]
    full = analytics.kg_data["edges"]

    def graph(edges: list[dict[str, Any]]) -> nx.Graph:
        result = nx.Graph()
        result.add_nodes_from(node["id"] for node in analytics.kg_data["nodes"])
        result.add_edges_from((edge["source"], edge["target"]) for edge in edges)
        return result

    asserted_graph = graph(asserted)
    full_graph = graph(full)
    assert {
        frozenset(component) for component in nx.connected_components(asserted_graph)
    } == {frozenset(component) for component in nx.connected_components(full_graph)}
    assert dict(nx.all_pairs_shortest_path_length(asserted_graph)) == dict(
        nx.all_pairs_shortest_path_length(full_graph)
    )
