"""
KG compatibility routes — aliases for endpoints where the frontend uses
different paths than the kg package provides.

These routes bridge the gap between what the frontend API client calls
and what the eleutheria_kg package exposes.
"""

import logging
from typing import Annotated, Any

import anyio
from eleutheria_database.services.db import DatabaseService
from eleutheria_kg.services.analytics import ANCIENT_PERIODS, KGAnalytics
from eleutheria_kg.services.cache import KGCache
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from backend.dependencies import get_analytics, get_cache, get_db, get_services

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


@router.get("/node/{node_id}/connections", deprecated=True)
async def get_node_connections(
    node_id: str,
    request: Request,
) -> RedirectResponse:
    """Deprecated: use ``/api/kg/nodes/{node_id}/neighbors``.

    Kept as a 301 redirect for six months (until 2026-11-15) so any
    bookmarked or hard-coded client URLs continue to resolve. The new
    canonical returns 1-hop neighbors grouped by edge type + direction.
    """
    query = str(request.url.query) if request.url.query else ""
    target = f"/api/kg/nodes/{node_id}/neighbors"
    if query:
        target = f"{target}?{query}"
    return RedirectResponse(url=target, status_code=301)


@router.get("/stats")
async def get_kg_stats(
    analytics: Annotated[KGAnalytics, Depends(get_analytics)],
    cache: Annotated[KGCache, Depends(get_cache)],
    db: Annotated[DatabaseService, Depends(get_db)],
) -> dict[str, Any]:
    """KG statistics with LIVE counts.

    `total_nodes`, `total_edges`, and the `node_types` / `edge_types` histograms
    are queried from Postgres on every call (cheap — backed by indexes on
    `type` / `relation`, ~10ms total). This guarantees the numbers shown in
    the frontend, in `/api/health`, and in the CLI track the actual DB rather
    than the in-memory analytics snapshot, which is loaded once at startup and
    would otherwise drift after every deploy.

    The heavier analytics-derived fields (`density`, `connected_components`)
    still come from the cached snapshot — they're expensive to recompute and
    can lag the DB by minutes without confusing users.
    """
    live: dict[str, Any] = {}
    try:
        nrow = await db.fetchrow("SELECT count(*)::int AS n FROM free_will.kg_nodes")
        erow = await db.fetchrow("SELECT count(*)::int AS n FROM free_will.kg_edges")
        ntype_rows = await db.fetch(
            "SELECT type, count(*)::int AS n FROM free_will.kg_nodes GROUP BY type"
        )
        etype_rows = await db.fetch(
            "SELECT relation, count(*)::int AS n FROM free_will.kg_edges GROUP BY relation"
        )
        live["total_nodes"] = int(nrow["n"]) if nrow else 0
        live["total_edges"] = int(erow["n"]) if erow else 0
        live["node_types"] = {r["type"]: int(r["n"]) for r in ntype_rows if r["type"]}
        live["edge_types"] = {
            r["relation"]: int(r["n"]) for r in etype_rows if r["relation"]
        }
        live["live"] = True
    except Exception as e:
        logger.warning(
            "Live KG stats query failed (%s); falling back to in-memory snapshot", e
        )
        live["live"] = False

    # Cached analytics-derived fields (density, connected_components, etc.)
    cached = cache.get("kg_statistics_analytics")
    if cached:
        analytics_part = cached
    else:
        analytics_part = analytics.get_statistics()
        cache.set("kg_statistics_analytics", analytics_part, ttl=300)

    # Live fields override the cached snapshot
    merged = {**analytics_part, **{k: v for k, v in live.items() if k != "live"}}
    merged["live_counts"] = bool(live.get("live", False))
    return merged


@router.post("/reload")
async def reload_kg(
    request: Request,
) -> dict[str, Any]:
    """Re-load the in-memory KG snapshot from Postgres.

    Designed to be called by `scripts/deploy_kg_to_supabase.py` immediately
    after a successful `--apply`, so the running backend serves fresh KG data
    without a pod restart. The heavy services (`KGAnalytics`, `GraphRAGService`)
    read from this in-memory snapshot for performance.

    Best-effort: returns 200 with `{ok: false, reason: ...}` on partial failure
    rather than raising, so the deploy script's reload call never breaks a
    successful deploy.
    """
    svc = get_services()
    try:
        kg_data = await svc._load_kg_data()
        svc.analytics.set_data(kg_data)
        if svc.graphrag is not None:
            svc.graphrag.kg_data = kg_data
            await svc.graphrag.load_kg()
        # Bust any cached statistics
        cache: KGCache = svc.cache
        for key in ("kg_statistics", "kg_statistics_analytics"):
            try:
                cache.delete(key)
            except Exception:
                pass
        return {
            "ok": True,
            "kg_nodes": len(kg_data.get("nodes", [])),
            "kg_edges": len(kg_data.get("edges", [])),
            "kg_source": svc.kg_source,
        }
    except Exception as e:
        logger.exception("KG reload failed")
        return {"ok": False, "reason": str(e)}


# ---------- Viz endpoint ----------


@router.get("/viz/cytoscape")
async def get_cytoscape_data(
    analytics: Annotated[KGAnalytics, Depends(get_analytics)],
    cache: Annotated[KGCache, Depends(get_cache)],
    communityAlgorithm: str = Query(
        "greedy", description="Community detection algorithm"
    ),
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
        edges = [
            e
            for e in edges
            if e["source"] in ancient_ids and e["target"] in ancient_ids
        ]

    # Detect communities — CPU-bound networkx work (~2 min cold on the full
    # graph); run in a thread so it doesn't freeze the event loop, and rely
    # on the per-algorithm memo in KGAnalytics for repeat calls.
    communities = await anyio.to_thread.run_sync(
        lambda: analytics.detect_communities(communityAlgorithm)
    )
    colors = analytics.get_community_colors()

    # Build Cytoscape elements
    elements = []
    for node in nodes:
        nid = node["id"]
        comm_id = communities.get(nid, 0)
        elements.append(
            {
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
            }
        )

    for edge in edges:
        elements.append(
            {
                "data": {
                    "source": edge["source"],
                    "target": edge["target"],
                    "relation": edge.get("relation", ""),
                    "label": edge.get("relation", ""),
                },
                "group": "edges",
            }
        )

    # Build community metadata
    community_groups: dict[int, list[str]] = {}
    for nid, cid in communities.items():
        if cid not in community_groups:
            community_groups[cid] = []
        community_groups[cid].append(nid)

    community_list = sorted(
        community_groups.items(), key=lambda x: len(x[1]), reverse=True
    )

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
                    {
                        "name": "greedy",
                        "available": True,
                        "description": "Greedy modularity optimization",
                    },
                    {
                        "name": "leiden",
                        "available": analytics._graph is not None,
                        "description": "Leiden algorithm",
                    },
                    {
                        "name": "louvain",
                        "available": analytics._graph is not None,
                        "description": "Louvain algorithm",
                    },
                    {
                        "name": "semantic",
                        "available": True,
                        "description": "Semantic person-centric clustering",
                    },
                ],
            },
        },
    }

    # KG data only changes on deploy/reload; a 5-minute TTL forced the
    # 2-minute community recomputation on nearly every page load.
    cache.set(cache_key, result, ttl=86400)
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

    influence_rels = {
        "influences",
        "influenced_by",
        "develops",
        "criticizes",
        "responds_to",
    }
    for e in edges:
        if e.get("relation") in influence_rels:
            src = e["source"]
            tgt = e["target"]
            if src in matrix:
                matrix[src][tgt] = matrix[src].get(tgt, 0) + 1
            if tgt in matrix:
                matrix[tgt][src] = matrix[tgt].get(src, 0) + 1

    result = {
        "persons": [
            {"id": p["id"], "label": p.get("label", p["id"]), "school": p.get("school")}
            for p in persons
        ],
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
