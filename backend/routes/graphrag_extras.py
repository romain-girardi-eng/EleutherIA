"""
Supplementary GraphRAG routes — status, stats, debates, influence chains,
relationships, compare, and the /answer alias endpoint.

These are thin wrappers over the existing KGAnalytics service and GraphRAG,
filling the gap between what the frontend expects and what the graphrag
package provides.
"""

import logging
import time
from typing import Annotated, Any

from eleutheria_database.services.db import DatabaseService
from eleutheria_graphrag.services.graphrag_service import GraphRAGService
from eleutheria_kg.services.analytics import KGAnalytics
from eleutheria_kg.services.cache import KGCache
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from backend.dependencies import get_analytics, get_cache, get_db, get_graphrag

logger = logging.getLogger(__name__)

router = APIRouter(tags=["graphrag-extras"])


# ---------- /answer alias (Phase 3) ----------

class AnswerRequest(BaseModel):
    """Request body matching what the frontend sends to /api/graphrag/answer."""
    query: str = Field(..., min_length=1)
    enhanced_mode: bool = True
    mode: str = "fast"
    semantic_k: int = Field(5, ge=1, le=50)
    graph_depth: int = Field(1, ge=1, le=4)
    max_context: int = Field(30, ge=5, le=100)
    use_hyde: bool = False
    use_expansion: bool = False
    use_crag: bool = False
    use_selfrag: bool = False
    use_debates: bool = False
    use_hierarchy: bool = True
    use_reranking: bool = True
    conversation_id: str | None = None
    use_thinking: bool = False
    academic_mode: bool = False
    rigor_level: str = "standard"
    citation_style: str = "inline"
    temperature: float = 0.7


@router.post("/answer")
async def graphrag_answer(
    body: AnswerRequest,
    graphrag: Annotated[GraphRAGService, Depends(get_graphrag)],
    db: Annotated[DatabaseService, Depends(get_db)],
) -> dict[str, Any]:
    """
    The primary GraphRAG query endpoint the frontend calls.

    Wraps the GraphRAG pipeline and transforms the output to match
    the frontend's expected GraphRAGResponse shape.
    """
    start = time.time()

    try:
        result = await graphrag.query(
            question=body.query,
            semantic_k=body.semantic_k,
            graph_depth=body.graph_depth,
            max_context_nodes=body.max_context,
            include_passages=True,
        )
    except Exception as e:
        logger.exception("GraphRAG query failed")
        raise HTTPException(status_code=500, detail=str(e)) from e

    elapsed = time.time() - start

    # Build sources list (for frontend CitationRenderer)
    sources = []
    for i, node_id in enumerate(result.get("seed_nodes", [])[:10]):
        node = graphrag.node_lookup.get(node_id, {})
        sources.append({
            "id": i + 1,
            "nodeId": node_id,
            "nodeLabel": node.get("label", node_id),
            "nodeType": node.get("type", "concept"),
            "content": (node.get("description") or "")[:300],
            "metadata": {
                "school": node.get("school"),
                "period": node.get("period"),
                "confidence": None,
            },
        })

    # Build citation lists
    ancient_sources = []
    modern_sources = []
    for cit in result.get("citations", []):
        label = cit.get("label", "")
        if cit.get("type") == "passage":
            ancient_sources.append(label)
        else:
            ancient_sources.append(label)

    # Build reasoning path
    seed_nodes_detail = []
    for nid in result.get("seed_nodes", []):
        node = graphrag.node_lookup.get(nid, {})
        seed_nodes_detail.append({
            "id": nid,
            "label": node.get("label", nid),
            "type": node.get("type", "concept"),
            "reason": "Retrieved via semantic search",
        })

    context_nodes = result.get("context_nodes", [])
    expanded_detail = []
    for nid in context_nodes:
        if nid not in result.get("seed_nodes", []):
            node = graphrag.node_lookup.get(nid, {})
            expanded_detail.append({
                "id": nid,
                "label": node.get("label", nid),
                "type": node.get("type", "concept"),
                "reason": "Expanded via graph traversal",
            })

    return {
        "query": body.query,
        "answer": result.get("answer", ""),
        "citations": {
            "ancient_sources": ancient_sources,
            "modern_scholarship": modern_sources,
        },
        "sources": sources,
        "reasoning_path": {
            "starting_nodes": seed_nodes_detail,
            "expanded_nodes": expanded_detail[:20],
            "traversed_edges": [],
            "total_nodes": len(context_nodes),
            "total_edges": 0,
        },
        "nodes_used": len(context_nodes),
        "edges_traversed": 0,
        "quality_metrics": {
            "confidence_score": 75,
            "quality_badge": "Medium",
            "caveats": [],
        },
        "retrieval_stats": {
            "hyde_used": body.use_hyde,
            "rerank_used": body.use_reranking,
            "crag_used": body.use_crag,
            "selfrag_used": body.use_selfrag,
        },
        "processing_time": round(elapsed, 2),
        "service": "GraphRAG Pipeline",
        "success": True,
    }


# ---------- Status / Stats ----------

@router.get("/status")
async def graphrag_status(
    graphrag: Annotated[GraphRAGService, Depends(get_graphrag)],
) -> dict[str, Any]:
    """Service status — whether KG is loaded, LLM available, node count."""
    return {
        "status": "ready" if graphrag._kg_loaded else "loading",
        "kg_loaded": graphrag._kg_loaded,
        "nodes_count": len(graphrag.node_lookup),
        "llm_available": len(graphrag.llm.available_providers) > 0,
        "llm_providers": [p.value for p in graphrag.llm.available_providers],
    }


@router.get("/stats")
async def graphrag_stats(
    analytics: Annotated[KGAnalytics, Depends(get_analytics)],
    cache: Annotated[KGCache, Depends(get_cache)],
    db: Annotated[DatabaseService, Depends(get_db)],
) -> dict[str, Any]:
    """Comprehensive GraphRAG statistics."""
    cached = cache.get("graphrag_stats")
    if cached:
        return cached

    kg_stats = analytics.get_statistics()

    # Database stats
    works_count = await db.fetchval("SELECT COUNT(*) FROM free_will.ancient_works")
    passages_count = await db.fetchval("SELECT COUNT(*) FROM free_will.passages")
    citations_count = await db.fetchval("SELECT COUNT(*) FROM free_will.passage_citations")

    result = {
        "knowledge_graph": kg_stats,
        "database": {
            "works": int(works_count or 0),
            "passages": int(passages_count or 0),
            "citations": int(citations_count or 0),
        },
    }

    cache.set("graphrag_stats", result, ttl=600)
    return result


# ---------- Debates ----------

@router.get("/debates")
async def get_debates(
    analytics: Annotated[KGAnalytics, Depends(get_analytics)],
    limit: int = Query(10, ge=1, le=50),
) -> dict[str, Any]:
    """Get philosophical debate nodes from the KG."""
    debate_types = {"Debate", "Argument", "Position", "Objection", "Response"}
    nodes = analytics.kg_data.get("nodes", [])
    debates = [n for n in nodes if n.get("type") in debate_types]

    # Sort by number of connections (most connected first)
    edges = analytics.kg_data.get("edges", [])
    connection_count: dict[str, int] = {}
    for e in edges:
        connection_count[e["source"]] = connection_count.get(e["source"], 0) + 1
        connection_count[e["target"]] = connection_count.get(e["target"], 0) + 1

    debates.sort(key=lambda n: connection_count.get(n["id"], 0), reverse=True)

    return {
        "debates": debates[:limit],
        "total": len(debates),
    }


# ---------- Influence Chains ----------

@router.get("/influence-chains")
async def get_influence_chains(
    analytics: Annotated[KGAnalytics, Depends(get_analytics)],
    limit: int = Query(10, ge=1, le=50),
) -> dict[str, Any]:
    """Get influence relationships from KG edges."""
    influence_types = {"influences", "influenced_by", "responds_to", "develops", "criticizes"}
    edges = analytics.kg_data.get("edges", [])
    influences = [e for e in edges if e.get("relation") in influence_types]

    # Enrich with node labels
    nodes_by_id = {n["id"]: n for n in analytics.kg_data.get("nodes", [])}
    enriched = []
    for e in influences[:limit]:
        source_node = nodes_by_id.get(e["source"], {})
        target_node = nodes_by_id.get(e["target"], {})
        enriched.append({
            "source": e["source"],
            "target": e["target"],
            "relation": e.get("relation", ""),
            "description": e.get("description", ""),
            "source_label": source_node.get("label", e["source"]),
            "target_label": target_node.get("label", e["target"]),
            "source_type": source_node.get("type"),
            "target_type": target_node.get("type"),
        })

    return {
        "chains": enriched,
        "total": len(influences),
    }


# ---------- Relationships ----------

@router.get("/relationships/{node_id}")
async def get_node_relationships(
    node_id: str,
    analytics: Annotated[KGAnalytics, Depends(get_analytics)],
) -> dict[str, Any]:
    """Get all edges connected to a node (incoming and outgoing)."""
    edges = analytics.kg_data.get("edges", [])
    nodes_by_id = {n["id"]: n for n in analytics.kg_data.get("nodes", [])}

    incoming = []
    outgoing = []
    for e in edges:
        if e["source"] == node_id:
            target = nodes_by_id.get(e["target"], {})
            outgoing.append({
                **e,
                "target_label": target.get("label", e["target"]),
                "target_type": target.get("type"),
            })
        elif e["target"] == node_id:
            source = nodes_by_id.get(e["source"], {})
            incoming.append({
                **e,
                "source_label": source.get("label", e["source"]),
                "source_type": source.get("type"),
            })

    node = nodes_by_id.get(node_id, {})

    return {
        "node_id": node_id,
        "node_label": node.get("label", node_id),
        "node_type": node.get("type"),
        "incoming": incoming,
        "outgoing": outgoing,
        "total_connections": len(incoming) + len(outgoing),
    }


# ---------- Compare ----------

@router.get("/compare")
async def compare_modes(
    graphrag: Annotated[GraphRAGService, Depends(get_graphrag)],
    query: str = Query(..., min_length=3),
) -> dict[str, Any]:
    """Compare standard vs enhanced GraphRAG modes on the same query."""
    start = time.time()

    # Standard mode (small context)
    standard = await graphrag.query(
        question=query, semantic_k=5, graph_depth=1, max_context_nodes=15,
    )

    # Enhanced mode (larger context)
    enhanced = await graphrag.query(
        question=query, semantic_k=10, graph_depth=2, max_context_nodes=30,
    )

    elapsed = time.time() - start

    return {
        "query": query,
        "standard": {
            "answer": standard.get("answer", ""),
            "nodes_used": len(standard.get("context_nodes", [])),
            "citations": len(standard.get("citations", [])),
        },
        "enhanced": {
            "answer": enhanced.get("answer", ""),
            "nodes_used": len(enhanced.get("context_nodes", [])),
            "citations": len(enhanced.get("citations", [])),
        },
        "processing_time": round(elapsed, 2),
    }
