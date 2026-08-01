"""
FastAPI routes for knowledge graph operations.

Provides REST endpoints for browsing and analyzing the knowledge graph.
"""

import logging
from typing import TYPE_CHECKING, Annotated, Any, cast

from fastapi import APIRouter, Depends, HTTPException, Query

from eleutheria_kg.models.kg import KGStatistics
from eleutheria_kg.services.analytics import KGAnalytics
from eleutheria_kg.services.bibliography import collect_modern_scholarship
from eleutheria_kg.services.cache import KGCache
from eleutheria_kg.services.db_traversal import fetch_neighborhood

if TYPE_CHECKING:
    from eleutheria_database.services.db import DatabaseService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["knowledge-graph"])

# Service instances (to be injected by main app)
_analytics: KGAnalytics | None = None
_cache: KGCache | None = None
# Optional — only used as the bounded-CTE fallback when the in-memory KG
# graph on `_analytics` has not been warmed (see `get_node_neighbors`).
_db: DatabaseService | None = None


def set_services(
    analytics: KGAnalytics,
    cache: KGCache,
    db: DatabaseService | None = None,
) -> None:
    """Set service instances for dependency injection.

    ``db`` is optional and backward-compatible: existing callers that only
    pass ``analytics``/``cache`` keep working with no DB-backed fallback.
    """
    global _analytics, _cache, _db
    _analytics = analytics
    _cache = cache
    _db = db


def get_analytics() -> KGAnalytics:
    """Get analytics service."""
    if _analytics is None:
        raise RuntimeError("KGAnalytics not initialized")
    return _analytics


def get_cache() -> KGCache:
    """Get cache service."""
    if _cache is None:
        raise RuntimeError("KGCache not initialized")
    return _cache


@router.get("/nodes")
async def list_nodes(
    analytics: Annotated[KGAnalytics, Depends(get_analytics)],
    node_type: str | None = Query(None, description="Filter by node type"),
    period: str | None = Query(None, description="Filter by period"),
    school: str | None = Query(None, description="Filter by school"),
    search: str | None = Query(None, description="Search in label/description"),
    limit: int = Query(100, ge=1, le=50000),
    offset: int = Query(0, ge=0),
) -> list[dict[str, Any]]:
    """
    List knowledge graph nodes with optional filtering.
    """
    nodes = analytics.kg_data.get("nodes", [])

    # Apply filters
    if node_type:
        nodes = [n for n in nodes if n.get("type") == node_type]
    if period:
        nodes = [n for n in nodes if n.get("period") == period]
    if school:
        nodes = [n for n in nodes if n.get("school") == school]
    if search:
        search_lower = search.lower()
        nodes = [
            n
            for n in nodes
            if search_lower in n.get("label", "").lower()
            or search_lower in n.get("description", "").lower()
        ]

    # Paginate
    return cast(list[dict[str, Any]], nodes[offset : offset + limit])


@router.get("/nodes/{node_id}")
async def get_node(
    node_id: str,
    analytics: Annotated[KGAnalytics, Depends(get_analytics)],
) -> dict[str, Any]:
    """Get a specific node by ID."""
    for node in analytics.kg_data.get("nodes", []):
        if node.get("id") == node_id:
            return cast(dict[str, Any], node)

    raise HTTPException(status_code=404, detail="Node not found")


@router.get("/nodes/{node_id}/neighbors")
async def get_node_neighbors(
    node_id: str,
    analytics: Annotated[KGAnalytics, Depends(get_analytics)],
    depth: int = Query(
        1, ge=1, le=3, description="Traversal depth (1 = direct neighbors)"
    ),
    grouped: bool = Query(
        True, description="Return 1-hop neighbors grouped by edge type + direction"
    ),
) -> dict[str, Any]:
    """
    Get the direct neighbors of a knowledge-graph node.

    The default (``grouped=True``, ``depth=1``) shape is the doctoral-UI
    canonical: ``{node_id, node, neighbors: {outgoing: {<relation>: [...]},
    incoming: {<relation>: [...]}}, total_count}``. Pass ``grouped=false`` to
    fall back to the legacy ``{nodes, edges}`` neighborhood payload (used by
    Cosmograph subgraph rendering).
    """
    all_nodes = analytics.kg_data.get("nodes", [])
    nodes_by_id = {n["id"]: n for n in all_nodes}

    # The in-memory KG (networkx graph behind `analytics`) is not warm —
    # fall back to a bounded Postgres-side k-hop CTE over kg_edges instead
    # of requiring the full node/edge dump in process memory. See
    # `eleutheria_kg.services.db_traversal`. Degrades to the normal 404
    # path below (never a 500) if the DB turns out to be unreachable too.
    if not all_nodes and _db is not None and _db.is_connected():
        try:
            db_result = await fetch_neighborhood(_db, node_id, depth=depth)
        except Exception:
            logger.warning(
                "get_node_neighbors: DB fallback failed for %s", node_id, exc_info=True
            )
            db_result = None
        if db_result is not None:
            if not db_result["nodes"]:
                raise HTTPException(status_code=404, detail="Node not found")
            if not grouped:
                return db_result
            nodes_by_id = {n["id"]: n for n in db_result["nodes"]}
            return _grouped_neighbors(node_id, nodes_by_id, db_result["edges"])

    if node_id not in nodes_by_id:
        raise HTTPException(status_code=404, detail="Node not found")

    if not grouped:
        result = analytics.get_node_neighbors(node_id, depth)
        if not result["nodes"]:
            raise HTTPException(status_code=404, detail="Node not found")
        return result

    return _grouped_neighbors(node_id, nodes_by_id, analytics.kg_data.get("edges", []))


def _grouped_neighbors(
    node_id: str,
    nodes_by_id: dict[str, dict[str, Any]],
    edges: list[dict[str, Any]],
) -> dict[str, Any]:
    """Shape a flat (nodes_by_id, edges) neighborhood into the grouped
    ``{node_id, node, neighbors: {outgoing, incoming}, total_count}``
    payload. Shared by the in-memory (`analytics.kg_data`) and DB-backed
    (`db_traversal.fetch_neighborhood`) code paths.
    """
    outgoing: dict[str, list[dict[str, Any]]] = {}
    incoming: dict[str, list[dict[str, Any]]] = {}
    total = 0

    def _summary(other_id: str) -> dict[str, Any]:
        other = nodes_by_id.get(other_id, {"id": other_id})
        return {
            "node_id": other_id,
            "label": other.get("label", other_id),
            "node_type": other.get("type"),
            "period": other.get("period"),
        }

    for edge in edges:
        relation = edge.get("relation") or "related"
        src = edge.get("source", "")
        tgt = edge.get("target", "")
        if src == node_id:
            outgoing.setdefault(relation, []).append(_summary(tgt))
            total += 1
        elif tgt == node_id:
            incoming.setdefault(relation, []).append(_summary(src))
            total += 1

    return {
        "node_id": node_id,
        "node": nodes_by_id[node_id],
        "neighbors": {"outgoing": outgoing, "incoming": incoming},
        "total_count": total,
    }


@router.get("/edges")
async def list_edges(
    analytics: Annotated[KGAnalytics, Depends(get_analytics)],
    relation: str | None = Query(None, description="Filter by relation type"),
    source: str | None = Query(None, description="Filter by source node"),
    target: str | None = Query(None, description="Filter by target node"),
    limit: int = Query(100, ge=1, le=50000),
    offset: int = Query(0, ge=0),
) -> list[dict[str, Any]]:
    """
    List knowledge graph edges with optional filtering.
    """
    edges = analytics.kg_data.get("edges", [])

    if relation:
        edges = [e for e in edges if e.get("relation") == relation]
    if source:
        edges = [e for e in edges if e.get("source") == source]
    if target:
        edges = [e for e in edges if e.get("target") == target]

    return cast(list[dict[str, Any]], edges[offset : offset + limit])


@router.get("/bibliography")
async def get_bibliography(
    analytics: Annotated[KGAnalytics, Depends(get_analytics)],
    cache: Annotated[KGCache, Depends(get_cache)],
) -> dict[str, Any]:
    """All unique modern-scholarship references in the knowledge graph."""
    cached = cache.get("kg_bibliography")
    if cached:
        return cast(dict[str, Any], cached)

    references = collect_modern_scholarship(analytics.kg_data.get("nodes", []))
    result = {"references": references, "count": len(references)}
    cache.set("kg_bibliography", result, ttl=3600)
    return result


@router.get("/statistics", response_model=KGStatistics)
async def get_statistics(
    analytics: Annotated[KGAnalytics, Depends(get_analytics)],
    cache: Annotated[KGCache, Depends(get_cache)],
) -> dict[str, Any]:
    """Get knowledge graph statistics."""
    cached = cache.get("kg_statistics")
    if cached:
        return cast(dict[str, Any], cached)

    stats = analytics.get_statistics()
    cache.set("kg_statistics", stats, ttl=300)
    return stats


@router.get("/communities")
async def get_communities(
    analytics: Annotated[KGAnalytics, Depends(get_analytics)],
    cache: Annotated[KGCache, Depends(get_cache)],
    algorithm: str = Query(
        "leiden", description="Algorithm: leiden, louvain, greedy, semantic"
    ),
    resolution: float = Query(1.0, ge=0.1, le=5.0, description="Resolution parameter"),
) -> dict[str, Any]:
    """
    Detect and return community assignments.
    """
    cache_key = f"communities_{algorithm}_{resolution}"
    cached = cache.get(cache_key)
    if cached:
        return cast(dict[str, Any], cached)

    communities = analytics.detect_communities(algorithm, resolution)
    colors = analytics.get_community_colors()

    # Group nodes by community
    community_groups: dict[int, list[str]] = {}
    for node_id, comm_id in communities.items():
        if comm_id not in community_groups:
            community_groups[comm_id] = []
        community_groups[comm_id].append(node_id)

    result = {
        "algorithm": algorithm,
        "resolution": resolution,
        "total_communities": len(community_groups),
        "assignments": communities,
        "colors": colors,
        "communities": [
            {
                "id": comm_id,
                "color": colors.get(comm_id, "#888888"),
                "node_count": len(nodes),
                "nodes": nodes[:10],  # First 10 nodes as sample
            }
            for comm_id, nodes in sorted(community_groups.items())
        ],
    }

    cache.set(cache_key, result, ttl=600)
    return result


@router.get("/centrality")
async def get_centrality(
    analytics: Annotated[KGAnalytics, Depends(get_analytics)],
    cache: Annotated[KGCache, Depends(get_cache)],
    metric: str = Query(
        "betweenness", description="Metric: betweenness, pagerank, degree, eigenvector"
    ),
    top_k: int = Query(20, ge=1, le=100, description="Number of top nodes to return"),
) -> dict[str, Any]:
    """
    Calculate centrality scores for nodes.
    """
    cache_key = f"centrality_{metric}_{top_k}"
    cached = cache.get(cache_key)
    if cached:
        return cast(dict[str, Any], cached)

    scores = analytics.calculate_centrality(metric, top_k)

    # Enrich with node info
    nodes_by_id = {n["id"]: n for n in analytics.kg_data.get("nodes", [])}
    top_nodes = [
        {
            "id": node_id,
            "score": score,
            "label": nodes_by_id.get(node_id, {}).get("label", node_id),
            "type": nodes_by_id.get(node_id, {}).get("type"),
        }
        for node_id, score in scores.items()
    ]

    result = {
        "metric": metric,
        "top_k": top_k,
        "top_nodes": top_nodes,
    }

    cache.set(cache_key, result, ttl=600)
    return result


@router.get("/path/{source}/{target}")
async def get_shortest_path(
    source: str,
    target: str,
    analytics: Annotated[KGAnalytics, Depends(get_analytics)],
) -> dict[str, Any]:
    """
    Find shortest path between two nodes.
    """
    path = analytics.get_shortest_path(source, target)

    if path is None:
        raise HTTPException(
            status_code=404, detail=f"No path found between {source} and {target}"
        )

    # Enrich with node info
    nodes_by_id = {n["id"]: n for n in analytics.kg_data.get("nodes", [])}
    path_nodes = [nodes_by_id.get(node_id, {"id": node_id}) for node_id in path]

    return {
        "source": source,
        "target": target,
        "length": len(path) - 1,
        "path": path,
        "nodes": path_nodes,
    }


@router.get("/timeline")
async def get_timeline(
    analytics: Annotated[KGAnalytics, Depends(get_analytics)],
    cache: Annotated[KGCache, Depends(get_cache)],
) -> list[dict[str, Any]]:
    """
    Get timeline data for visualization.

    Returns nodes grouped by historical period.
    """
    cached = cache.get("timeline")
    if cached:
        return cast(list[dict[str, Any]], cached)

    timeline = analytics.get_timeline_data()
    cache.set("timeline", timeline, ttl=600)
    return timeline
