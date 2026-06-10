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


def _build_quality_metrics(
    metadata: dict[str, Any],
    *,
    citation_count: int,
    node_count: int,
    has_sources: bool,
) -> dict[str, Any]:
    """Honest quality metrics for the /answer payload.

    Measured values come from the pipeline reports carried in the answer
    metadata: ``grounding`` (verifier-v2 sample score), ``citation_verifier_v2``
    (adversarial citation audit) and ``text_verification`` (ancient-text
    verifier). When a measured value is absent we fall back to count-based
    estimates — labelled as estimates via ``*_method`` fields and caveats,
    never presented as measurements.
    """
    caveats: list[str] = []

    def _dict(key: str) -> dict[str, Any] | None:
        value = metadata.get(key)
        return value if isinstance(value, dict) else None

    grounding = _dict("grounding")
    verifier = _dict("citation_verifier_v2")
    text_verification = _dict("text_verification")

    # Accuracy / grounding — measured by the adversarial verifier when it ran.
    grounding_score: int | None = None
    if grounding is not None and isinstance(grounding.get("score"), int | float):
        grounding_score = int(grounding["score"])
        accuracy = round(grounding_score / 100, 2)
        accuracy_method = f"measured:{grounding.get('method', 'grounding')}"
        coverage = grounding.get("coverage")
        if isinstance(coverage, str) and coverage != "full":
            caveats.append(f"Grounding audited on a sample ({coverage}).")
    else:
        accuracy = min(1.0, citation_count / 5) if citation_count > 0 else 0.5
        accuracy_method = "estimate:citation_count_heuristic"
        caveats.append(
            "Accuracy is a citation-count estimate — no citation audit ran "
            "for this answer."
        )

    # Completeness has no measured counterpart yet — always an estimate.
    completeness = min(1.0, node_count / 20)
    completeness_method = "estimate:context_node_count"

    if grounding_score is not None:
        confidence_score = grounding_score
        confidence_method = accuracy_method
    else:
        confidence_score = round(
            (completeness * 40 + accuracy * 40 + 20) if has_sources else 50
        )
        confidence_method = "estimate:count_heuristics"
        caveats.append(
            "Confidence is heuristic (citation/node counts) — not a "
            "measured verification score."
        )

    # Quality badge: pipeline-computed when present, else derived estimate.
    badge = metadata.get("quality_badge")
    if not isinstance(badge, str) or not badge:
        badge = (
            "High"
            if confidence_score >= 75
            else "Medium"
            if confidence_score >= 50
            else "Low"
        )

    if verifier is not None:
        rejected = int(verifier.get("rejected") or 0)
        missing = int(verifier.get("missing") or 0)
        if rejected or missing:
            caveats.append(
                f"Citation audit flagged {rejected + missing} claim(s) whose "
                "cited source does not support them."
            )
    if text_verification is not None and int(
        text_verification.get("unverified") or 0
    ):
        caveats.append(
            f"{text_verification['unverified']} quoted ancient text(s) could "
            "not be verified against the corpus."
        )

    return {
        "confidence_score": confidence_score,
        "confidence_method": confidence_method,
        "grounding_score": grounding_score,
        "completeness": round(completeness, 2),
        "completeness_method": completeness_method,
        "accuracy": round(accuracy, 2),
        "accuracy_method": accuracy_method,
        "citation_audit": verifier,
        "text_verification": text_verification,
        "quality_badge": badge,
        "caveats": caveats,
    }

class AnswerRequest(BaseModel):
    """Request body matching what the frontend sends to /api/graphrag/answer."""
    query: str = Field(..., min_length=1)
    enhanced_mode: bool = True
    mode: str = "fast"
    semantic_k: int = Field(5, ge=1, le=50)
    graph_depth: int = Field(1, ge=1, le=4)
    max_context: int = Field(30, ge=5, le=100)
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
    retrieval_mode: str = "auto"  # "auto" | legacy "vector" alias | "sql"
    model: str = "gemini-3.1-pro"
    thread_id: str | None = None


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
            selected_model=body.model,
            retrieval_mode=body.retrieval_mode,
            # mode='deep' → two-pass adversarial counter-evidence hunt +
            # methodology/polishing (GraphRAGService gates both on this flag).
            hunt_counter_evidence=body.mode == "deep",
        )
    except Exception as e:
        logger.exception("GraphRAG query failed")
        raise HTTPException(status_code=500, detail=str(e)) from e

    elapsed = time.time() - start

    # Calculate cost/token metrics
    try:
        from eleutheria_graphrag.services.model_registry import get_model
        model_info = get_model(body.model)
        answer_tokens = len(result.get("answer", "")) // 4
        estimated_cost = (model_info.pricing_input * 50000 / 1_000_000) + (model_info.pricing_output * answer_tokens / 1_000_000)
    except (KeyError, ImportError):
        model_info = None
        estimated_cost = None

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
            "reason": "Retrieved via vectorless SQL/tree/lemma discovery",
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

    # Build evidenceMap keyed by citation number
    evidence_map: dict[str, Any] = {}
    for s in sources:
        evidence_map[str(s["id"])] = {
            "nodeId": s["nodeId"],
            "confidence": s["metadata"].get("confidence") or 0.75,
            "type": s["nodeType"],
        }

    # Quality metrics — measured values from the pipeline when available,
    # explicit count-based estimates otherwise (never presented as measured).
    citation_count = len(result.get("citations", []))
    node_count = len(context_nodes)
    answer_metadata = result.get("metadata", {}) or {}
    quality_metrics = _build_quality_metrics(
        answer_metadata, citation_count=citation_count, node_count=node_count,
        has_sources=bool(sources),
    )
    confidence_score = quality_metrics["confidence_score"]

    return {
        "query": body.query,
        "answer": result.get("answer", ""),
        "confidence": round(confidence_score / 100, 2),
        "citations": {
            "ancient_sources": ancient_sources,
            "modern_scholarship": modern_sources,
        },
        "sources": sources,
        "evidenceMap": evidence_map,
        "reasoning_path": {
            "starting_nodes": seed_nodes_detail,
            "expanded_nodes": expanded_detail[:20],
            "traversed_edges": [],
            "total_nodes": node_count,
            "total_edges": 0,
        },
        "nodes_used": node_count,
        "edges_traversed": 0,
        "llm_model": result.get("llm_model", ""),
        "llm_provider": result.get("llm_provider", ""),
        "quality_metrics": quality_metrics,
        "claim_ledger": result.get("claim_ledger", []),
        "metadata": answer_metadata,
        "retrieval_stats": {
            "rerank_used": body.use_reranking,
            "crag_used": body.use_crag,
            "selfrag_used": body.use_selfrag,
        },
        "metrics": {
            "processing_time_s": elapsed,
            "model_key": body.model,
            "model_label": model_info.label if model_info else body.model,
            "retrieval_mode_requested": body.retrieval_mode,
            "retrieval_mode_used": result.get("metadata", {}).get("retrieval_mode_used", "unknown"),
            "estimated_cost_usd": round(estimated_cost, 4) if estimated_cost is not None else None,
            "answer_length_chars": len(result.get("answer", "")),
        },
        "processing_time": round(elapsed, 2),
        "service": "GraphRAG Pipeline",
        "success": True,
        "retrieval_config": {
            "retrieval_mode": body.retrieval_mode,
            "model": body.model,
            "thread_id": body.thread_id,
        },
    }


@router.get("/models")
async def list_available_models() -> list[dict[str, Any]]:
    """Return available models for the frontend selector."""
    from eleutheria_graphrag.services.model_registry import list_models

    return [
        {
            "key": m.key,
            "label": m.label,
            "provider": m.provider,
            "context": m.context,
            "tier": m.tier,
            "pricing": {"input": m.pricing_input, "output": m.pricing_output},
        }
        for m in list_models()
    ]


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
    debate_types = {"debate", "argument", "position", "objection", "response"}
    nodes = analytics.kg_data.get("nodes", [])
    debates = [
        n for n in nodes
        if str(n.get("type", "")).strip().lower() in debate_types
    ]

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


# ---------- Workflow Stubs (Cloudflare Workflows not available on Railway) ----------


class WorkflowStartRequest(BaseModel):
    query: str = Field(..., min_length=1)
    mode: str = "thorough"
    options: dict[str, Any] = Field(default_factory=dict)


@router.post("/workflow/start", status_code=501)
async def workflow_start(body: WorkflowStartRequest) -> dict[str, Any]:
    """Stub: Cloudflare Workflows not available on Railway. Use /answer instead."""
    return {
        "error": "Workflow execution not available on Railway deployment. Use /api/graphrag/answer instead.",
        "status": "unsupported",
        "instanceId": None,
    }


@router.get("/workflow/status/{instance_id}", status_code=501)
async def workflow_status(instance_id: str) -> dict[str, Any]:
    """Stub: Cloudflare Workflows not available on Railway."""
    return {
        "error": "Workflow execution not available on Railway deployment.",
        "status": "unsupported",
        "instanceId": instance_id,
        "result": None,
    }
