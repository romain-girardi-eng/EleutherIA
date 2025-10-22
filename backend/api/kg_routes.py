#!/usr/bin/env python3
"""
Knowledge Graph API Routes
Endpoints for accessing KG nodes, edges, and visualizations
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional
import json
import logging
from pathlib import Path
from pydantic import BaseModel, Field

from services.kg_analytics import (
    build_argument_evidence,
    build_concept_clusters,
    build_influence_matrix,
    build_timeline_overview,
    compute_shortest_path,
    detect_communities,
)
from services.kg_cache import (
    cached,
    get_analytics_cache,
    get_kg_data_cache,
    cache_stats,
    invalidate_all,
)

logger = logging.getLogger(__name__)

router = APIRouter()

# Path to KG database
# In Docker: /app/api/kg_routes.py -> /app/ancient_free_will_database.json
# Locally: backend/api/kg_routes.py -> ancient_free_will_database.json
KG_PATH = Path(__file__).parent.parent / "ancient_free_will_database.json"


@cached(get_kg_data_cache(), ttl=0, key_prefix="kg_data")
def load_kg_data() -> Dict[str, Any]:
    """Load Knowledge Graph data (cached indefinitely)"""
    try:
        logger.info(f"Loading KG from disk: {KG_PATH}")
        with open(KG_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading KG: {e}")
        raise HTTPException(status_code=500, detail="Failed to load Knowledge Graph")


@router.get("/nodes")
async def get_all_nodes(
    node_type: Optional[str] = None,
    period: Optional[str] = None,
    school: Optional[str] = None
):
    """Get all KG nodes with optional filtering"""
    kg_data = load_kg_data()
    nodes = kg_data.get('nodes', [])

    # Apply filters
    if node_type:
        nodes = [n for n in nodes if n.get('type') == node_type]
    if period:
        nodes = [n for n in nodes if n.get('period') == period]
    if school:
        nodes = [n for n in nodes if n.get('school') == school]

    return {
        'nodes': nodes,
        'total': len(nodes)
    }


@router.get("/edges")
async def get_all_edges(
    relation: Optional[str] = None
):
    """Get all KG edges with optional filtering"""
    kg_data = load_kg_data()
    edges = kg_data.get('edges', [])

    # Apply filters
    if relation:
        edges = [e for e in edges if e.get('relation') == relation]

    return {
        'edges': edges,
        'total': len(edges)
    }


@router.get("/node/{node_id}")
async def get_node_by_id(node_id: str):
    """Get detailed information about a specific node"""
    kg_data = load_kg_data()
    nodes = kg_data.get('nodes', [])

    node = next((n for n in nodes if n.get('id') == node_id), None)

    if not node:
        raise HTTPException(status_code=404, detail=f"Node {node_id} not found")

    return node


@router.get("/node/{node_id}/connections")
async def get_node_connections(node_id: str):
    """Get all edges connected to a specific node"""
    kg_data = load_kg_data()
    edges = kg_data.get('edges', [])

    # Find edges where node is source or target
    connected_edges = [
        e for e in edges
        if e.get('source') == node_id or e.get('target') == node_id
    ]

    return {
        'node_id': node_id,
        'connections': connected_edges,
        'total': len(connected_edges)
    }


@router.get("/viz/cytoscape")
async def get_cytoscape_data(
    community_algorithm: str = Query(
        "auto", alias="communityAlgorithm", description="Community detection algorithm"
    )
):
    """Get KG data formatted for Cytoscape.js (cached)"""
    cache = get_analytics_cache()
    normalized_algorithm = (community_algorithm or "auto").lower()
    cache_key = f"cytoscape:full:{normalized_algorithm}"

    cached_result = cache.get(cache_key)
    if cached_result is not None:
        return cached_result

    kg_data = load_kg_data()
    community_result: Optional[Dict[str, Any]] = None
    available_algorithms: List[Dict[str, Any]] = []

    if normalized_algorithm not in {"none", "off", "disabled"}:
        community_result = detect_communities(kg_data, algorithm=normalized_algorithm)
        available_algorithms = community_result.get("available_algorithms", [])
    else:
        snapshot = detect_communities(kg_data, algorithm="auto")
        available_algorithms = snapshot.get("available_algorithms", [])

    node_assignments = (
        community_result.get("node_assignments", {}) if community_result else {}
    )
    color_map = community_result.get("colors", {}) if community_result else {}

    # Format for Cytoscape.js
    cytoscape_data = {
        'elements': {
            'nodes': [
                {
                    'data': {
                        'id': node['id'],
                        'label': node.get('label', ''),
                        'type': node.get('type', ''),
                        'period': node.get('period', ''),
                        'school': node.get('school', ''),
                        'communityId': (
                            int(node_assignments[node['id']])
                            if node['id'] in node_assignments
                            else None
                        ),
                        'communityColor': (
                            color_map.get(int(node_assignments[node['id']]))
                            if node['id'] in node_assignments
                            else None
                        ),
                        **node,  # Include all node properties
                    }
                }
                for node in kg_data.get('nodes', [])
            ],
            'edges': [
                {
                    'data': {
                        'id': edge.get('id', f"{edge['source']}-{edge['target']}"),
                        'source': edge['source'],
                        'target': edge['target'],
                        'relation': edge.get('relation', ''),
                        'label': edge.get('relation', ''),
                        **edge  # Include all edge properties
                    }
                }
                for edge in kg_data.get('edges', [])
            ]
        },
        'meta': {
            'community': {
                "algorithm_requested": normalized_algorithm,
                "algorithm_used": (
                    community_result.get("algorithm_used")
                    if community_result
                    else "none"
                ),
                "quality": (
                    community_result.get("quality") if community_result else None
                ),
                "communities": (
                    community_result.get("communities")
                    if community_result
                    else []
                ),
                "available_algorithms": available_algorithms,
            }
        },
    }

    cache.set(cache_key, cytoscape_data, ttl=0)  # Never expire
    return cytoscape_data


@router.get("/stats")
async def get_kg_stats():
    """Get Knowledge Graph statistics"""
    kg_data = load_kg_data()
    nodes = kg_data.get('nodes', [])
    edges = kg_data.get('edges', [])

    # Node type counts
    node_types = {}
    for node in nodes:
        node_type = node.get('type', 'unknown')
        node_types[node_type] = node_types.get(node_type, 0) + 1

    # Relation type counts
    relation_types = {}
    for edge in edges:
        relation = edge.get('relation', 'unknown')
        relation_types[relation] = relation_types.get(relation, 0) + 1

    # Period counts
    periods = {}
    for node in nodes:
        period = node.get('period', 'unknown')
        periods[period] = periods.get(period, 0) + 1

    return {
        'total_nodes': len(nodes),
        'total_edges': len(edges),
        'node_types': node_types,
        'relation_types': relation_types,
        'periods': periods
    }


def build_filter_payload(
    node_types: Optional[List[str]],
    periods: Optional[List[str]],
    schools: Optional[List[str]],
    relations: Optional[List[str]],
    search_term: Optional[str],
) -> Dict[str, Any]:
    """Helper to standardize filter payloads for analytics endpoints"""
    return {
        "nodeTypes": node_types or [],
        "periods": periods or [],
        "schools": schools or [],
        "relations": relations or [],
        "searchTerm": search_term or "",
    }


@router.get("/analytics/timeline")
async def get_timeline_overview(
    node_types: Optional[List[str]] = Query(None, alias="nodeTypes"),
    periods: Optional[List[str]] = Query(None),
    schools: Optional[List[str]] = Query(None),
    relations: Optional[List[str]] = Query(None),
    search_term: Optional[str] = Query(None, alias="searchTerm"),
):
    """Return aggregated timeline overview for chronological visualization"""
    kg_data = load_kg_data()
    filters = build_filter_payload(node_types, periods, schools, relations, search_term)

    # Use caching with filter-based key
    cache = get_analytics_cache()
    cache_key = f"timeline:{cache._make_key(filters)}"

    cached_result = cache.get(cache_key)
    if cached_result is not None:
        return cached_result

    result = build_timeline_overview(kg_data, filters)
    cache.set(cache_key, result, ttl=600)  # 10 min TTL
    return result


@router.get("/analytics/argument-flow")
async def get_argument_evidence_overview(
    node_types: Optional[List[str]] = Query(None, alias="nodeTypes"),
    periods: Optional[List[str]] = Query(None),
    schools: Optional[List[str]] = Query(None),
    relations: Optional[List[str]] = Query(None),
    search_term: Optional[str] = Query(None, alias="searchTerm"),
):
    """Return argument evidence flow data"""
    kg_data = load_kg_data()
    filters = build_filter_payload(node_types, periods, schools, relations, search_term)

    cache = get_analytics_cache()
    cache_key = f"argument:{cache._make_key(filters)}"

    cached_result = cache.get(cache_key)
    if cached_result is not None:
        return cached_result

    result = build_argument_evidence(kg_data, filters)
    cache.set(cache_key, result, ttl=600)
    return result


@router.get("/analytics/concept-clusters")
async def get_concept_cluster_overview(
    node_types: Optional[List[str]] = Query(None, alias="nodeTypes"),
    periods: Optional[List[str]] = Query(None),
    schools: Optional[List[str]] = Query(None),
    relations: Optional[List[str]] = Query(None),
    search_term: Optional[str] = Query(None, alias="searchTerm"),
):
    """Return concept cluster overview data (heavily cached due to expensive clustering)"""
    kg_data = load_kg_data()
    filters = build_filter_payload(node_types, periods, schools, relations, search_term)

    cache = get_analytics_cache()
    cache_key = f"clusters:{cache._make_key(filters)}"

    cached_result = cache.get(cache_key)
    if cached_result is not None:
        return cached_result

    # This is the slowest endpoint (~1.9s), cache aggressively
    result = build_concept_clusters(kg_data, filters)
    cache.set(cache_key, result, ttl=1800)  # 30 min TTL
    return result


@router.get("/analytics/influence-matrix")
async def get_influence_matrix(
    node_types: Optional[List[str]] = Query(None, alias="nodeTypes"),
    periods: Optional[List[str]] = Query(None),
    schools: Optional[List[str]] = Query(None),
    relations: Optional[List[str]] = Query(None),
    search_term: Optional[str] = Query(None, alias="searchTerm"),
):
    """Return influence matrix aggregates"""
    kg_data = load_kg_data()
    filters = build_filter_payload(node_types, periods, schools, relations, search_term)

    cache = get_analytics_cache()
    cache_key = f"matrix:{cache._make_key(filters)}"

    cached_result = cache.get(cache_key)
    if cached_result is not None:
        return cached_result

    result = build_influence_matrix(kg_data, filters)
    cache.set(cache_key, result, ttl=600)
    return result


class KGPathRequestModel(BaseModel):
    source_id: str = Field(..., alias="sourceId")
    target_id: str = Field(..., alias="targetId")
    max_depth: Optional[int] = Field(6, alias="maxDepth")
    allow_bidirectional: bool = Field(True, alias="allowBidirectional")
    relation_whitelist: Optional[List[str]] = Field(None, alias="relationWhitelist")
    relation_blacklist: Optional[List[str]] = Field(None, alias="relationBlacklist")

    class Config:
        populate_by_name = True


@router.post("/analytics/path")
async def calculate_graph_path(payload: KGPathRequestModel):
    """Compute shortest path between two nodes for path inspector"""
    kg_data = load_kg_data()
    try:
        result = compute_shortest_path(
            kg_data,
            payload.model_dump(by_alias=True, exclude_none=True),
        )
        return result
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/cache/stats")
async def get_cache_statistics():
    """Get cache statistics for monitoring"""
    return cache_stats()


@router.post("/cache/invalidate")
async def invalidate_cache(pattern: Optional[str] = None):
    """
    Invalidate cache entries
    Query param pattern: only invalidate keys containing this substring
    """
    if pattern:
        analytics_count = get_analytics_cache().invalidate(pattern)
        return {
            "status": "success",
            "pattern": pattern,
            "invalidated": {"analytics": analytics_count},
        }
    else:
        counts = invalidate_all()
        return {
            "status": "success",
            "message": "All caches cleared",
            "invalidated": counts,
        }
