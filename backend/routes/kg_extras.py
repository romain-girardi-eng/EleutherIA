"""
KG compatibility routes — aliases for endpoints where the frontend uses
different paths than the kg package provides.

These routes bridge the gap between what the frontend API client calls
and what the eleutheria_kg package exposes.
"""

import logging
from typing import Annotated, Any

from eleutheria_kg.services.analytics import ANCIENT_PERIODS, KGAnalytics
from eleutheria_kg.services.cache import KGCache
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from backend.dependencies import get_analytics, get_cache

logger = logging.getLogger(__name__)

router = APIRouter(tags=["kg-extras"])


# ---------- Path aliases ----------

@router.get("/node/{node_id}")
async def get_node_alias(
    node_id: str,
    analytics: Annotated[KGAnalytics, Depends(get_analytics)],
) -> dict[str, Any]:
    """Get a node by ID (alias for /nodes/{node_id})."""
    for node in analytics.kg_data.get("nodes", []):
        if node.get("id") == node_id:
            return node
    raise HTTPException(status_code=404, detail="Node not found")


@router.get("/node/{node_id}/connections")
async def get_node_connections(
    node_id: str,
    analytics: Annotated[KGAnalytics, Depends(get_analytics)],
    depth: int = Query(1, ge=1, le=3),
) -> dict[str, Any]:
    """Get node connections (alias for /nodes/{node_id}/neighbors)."""
    result = analytics.get_node_neighbors(node_id, depth)
    if not result["nodes"]:
        raise HTTPException(status_code=404, detail="Node not found")
    return result


@router.get("/stats")
async def get_kg_stats(
    analytics: Annotated[KGAnalytics, Depends(get_analytics)],
    cache: Annotated[KGCache, Depends(get_cache)],
) -> dict[str, Any]:
    """Get KG statistics (alias for /statistics)."""
    cached = cache.get("kg_statistics")
    if cached:
        return cached
    stats = analytics.get_statistics()
    cache.set("kg_statistics", stats, ttl=300)
    return stats


# ---------- Viz endpoint ----------

@router.get("/viz/cytoscape")
async def get_cytoscape_data(
    analytics: Annotated[KGAnalytics, Depends(get_analytics)],
    cache: Annotated[KGCache, Depends(get_cache)],
    communityAlgorithm: str = Query("greedy", description="Community detection algorithm"),
    ancientOnly: bool = Query(False, description="Filter to ancient-period nodes only"),
) -> dict[str, Any]:
    """
    Get KG data in Cytoscape.js format for the Cosmograph visualizer.

    Returns nodes and edges formatted as Cytoscape elements with
    community coloring metadata.
    """
    cache_key = f"cytoscape_{communityAlgorithm}_{ancientOnly}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    nodes = analytics.kg_data.get("nodes", [])
    edges = analytics.kg_data.get("edges", [])

    # Filter to ancient-period nodes if requested
    if ancientOnly:
        ancient_ids = {n["id"] for n in nodes if n.get("period") in ANCIENT_PERIODS}
        nodes = [n for n in nodes if n["id"] in ancient_ids]
        edges = [e for e in edges if e["source"] in ancient_ids and e["target"] in ancient_ids]

    # Detect communities
    communities = analytics.detect_communities(communityAlgorithm)
    colors = analytics.get_community_colors()

    # Build Cytoscape elements
    elements = []
    for node in nodes:
        nid = node["id"]
        comm_id = communities.get(nid, 0)
        elements.append({
            "data": {
                "id": nid,
                "label": node.get("label", nid),
                "type": node.get("type", "concept"),
                "period": node.get("period"),
                "school": node.get("school"),
                "community": comm_id,
                "color": colors.get(comm_id, "#888888"),
                "description": (node.get("description") or "")[:200],
            },
            "group": "nodes",
        })

    for edge in edges:
        elements.append({
            "data": {
                "source": edge["source"],
                "target": edge["target"],
                "relation": edge.get("relation", ""),
                "label": edge.get("relation", ""),
            },
            "group": "edges",
        })

    # Build community metadata
    community_groups: dict[int, list[str]] = {}
    for nid, cid in communities.items():
        if cid not in community_groups:
            community_groups[cid] = []
        community_groups[cid].append(nid)

    community_list = sorted(community_groups.items(), key=lambda x: len(x[1]), reverse=True)

    result = {
        "elements": elements,
        "meta": {
            "totalNodes": len(nodes),
            "totalEdges": len(edges),
            "community": {
                "algorithmRequested": communityAlgorithm,
                "algorithmUsed": communityAlgorithm,
                "quality": None,
                "communities": [
                    {
                        "id": cid,
                        "size": len(members),
                        "order": idx,
                        "color": colors.get(cid, "#888888"),
                        "label": f"Community {idx + 1}",
                    }
                    for idx, (cid, members) in enumerate(community_list)
                ],
                "availableAlgorithms": [
                    {"name": "greedy", "available": True, "description": "Greedy modularity optimization"},
                    {"name": "leiden", "available": analytics._graph is not None, "description": "Leiden algorithm"},
                    {"name": "louvain", "available": analytics._graph is not None, "description": "Louvain algorithm"},
                    {"name": "semantic", "available": True, "description": "Semantic person-centric clustering"},
                ],
            },
        },
    }

    cache.set(cache_key, result, ttl=300)
    return result


# ---------- Analytics endpoints ----------

@router.get("/analytics/timeline")
async def get_timeline_analytics(
    analytics: Annotated[KGAnalytics, Depends(get_analytics)],
    cache: Annotated[KGCache, Depends(get_cache)],
) -> dict[str, Any]:
    """Get timeline overview data (alias for /timeline)."""
    cached = cache.get("timeline_overview")
    if cached:
        return cached

    timeline = analytics.get_timeline_data()
    result = {
        "periods": timeline,
        "total_nodes": sum(p["node_count"] for p in timeline),
    }
    cache.set("timeline_overview", result, ttl=600)
    return result


@router.get("/analytics/influence-matrix")
async def get_influence_matrix(
    analytics: Annotated[KGAnalytics, Depends(get_analytics)],
    cache: Annotated[KGCache, Depends(get_cache)],
) -> dict[str, Any]:
    """Get influence matrix between philosophers/schools."""
    cached = cache.get("influence_matrix")
    if cached:
        return cached

    edges = analytics.kg_data.get("edges", [])
    nodes = analytics.kg_data.get("nodes", [])

    # Collect person nodes
    persons = [n for n in nodes if str(n.get("type", "")).strip().lower() == "person"]

    # Build influence matrix
    matrix: dict[str, dict[str, int]] = {}
    for p in persons:
        matrix[p["id"]] = {}

    influence_rels = {"influences", "influenced_by", "develops", "criticizes", "responds_to"}
    for e in edges:
        if e.get("relation") in influence_rels:
            src = e["source"]
            tgt = e["target"]
            if src in matrix:
                matrix[src][tgt] = matrix[src].get(tgt, 0) + 1
            if tgt in matrix:
                matrix[tgt][src] = matrix[tgt].get(src, 0) + 1

    result = {
        "persons": [{"id": p["id"], "label": p.get("label", p["id"]), "school": p.get("school")} for p in persons],
        "matrix": matrix,
    }
    cache.set("influence_matrix", result, ttl=600)
    return result


class PathRequest(BaseModel):
    source: str
    target: str


@router.post("/analytics/path")
async def compute_path(
    body: PathRequest,
    analytics: Annotated[KGAnalytics, Depends(get_analytics)],
) -> dict[str, Any]:
    """Find shortest path between two nodes (POST version)."""
    path = analytics.get_shortest_path(body.source, body.target)

    if path is None:
        raise HTTPException(
            status_code=404,
            detail=f"No path found between {body.source} and {body.target}",
        )

    nodes_by_id = {n["id"]: n for n in analytics.kg_data.get("nodes", [])}
    path_nodes = [nodes_by_id.get(nid, {"id": nid}) for nid in path]

    return {
        "source": body.source,
        "target": body.target,
        "length": len(path) - 1,
        "path": path,
        "nodes": path_nodes,
    }
