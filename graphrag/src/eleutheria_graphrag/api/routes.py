"""
FastAPI routes for GraphRAG Q&A.
"""

import json
from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from eleutheria_graphrag.models.query import QueryRequest, QueryResponse
from eleutheria_graphrag.services.graphrag_service import GraphRAGService

router = APIRouter(tags=["graphrag"])

# Service instance (to be injected by main app)
_graphrag: GraphRAGService | None = None


def set_service(graphrag: GraphRAGService) -> None:
    """Set GraphRAG service instance."""
    global _graphrag
    _graphrag = graphrag


def get_graphrag() -> GraphRAGService:
    """Get GraphRAG service."""
    if _graphrag is None:
        raise RuntimeError("GraphRAG service not initialized")
    return _graphrag


@router.post("/query", response_model=QueryResponse)
async def query(
    request: QueryRequest,
    graphrag: Annotated[GraphRAGService, Depends(get_graphrag)],
) -> QueryResponse:
    """
    Execute a GraphRAG query.

    Combines semantic search, graph traversal, and LLM synthesis
    to generate a scholarly answer with citations.
    """
    try:
        result = await graphrag.query(
            question=request.question,
            semantic_k=request.semantic_k,
            graph_depth=request.graph_depth,
            max_context_nodes=request.max_context_nodes,
            include_passages=request.include_passages,
        )
        return QueryResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/query/stream")
async def query_stream(
    question: str,
    graphrag: Annotated[GraphRAGService, Depends(get_graphrag)],
    semantic_k: int = 10,
    graph_depth: int = 2,
    max_context_nodes: int = 30,
    model: str = "gemini-3.1-pro",
    retrieval_mode: str = "auto",
) -> StreamingResponse:
    """
    Execute a GraphRAG query with streaming response.

    Returns Server-Sent Events (SSE) with answer chunks.
    """

    async def generate() -> AsyncIterator[str]:
        try:
            complete_sent = False
            yield f'data: {json.dumps({"type": "status", "data": {"message": "Initializing scholarly agent...", "step": 1}})}\n\n'
            async for chunk in graphrag.query_stream(
                question=question,
                semantic_k=semantic_k,
                graph_depth=graph_depth,
                max_context_nodes=max_context_nodes,
                selected_model=model,
                retrieval_mode=retrieval_mode,
            ):
                # The agent yields plain text for answer chunks, but the
                # final yield is a JSON string with {"type": "complete", ...}
                # containing the full response (citations, metadata, etc.).
                # Detect it and forward as a proper SSE complete event.
                if chunk.startswith('{"type":'):
                    try:
                        parsed = json.loads(chunk)
                        event_type = parsed.get("type", "")

                        # Forward agent events (thinking, tool calls) directly
                        if event_type in ("agent_thinking", "tool_start", "tool_result", "status", "error"):
                            yield f"data: {chunk}\n\n"
                            continue

                        if event_type == "complete":
                            # Transform agent data to match the frontend
                            # GraphRAGResponse shape (same as /answer).
                            raw = parsed.get("data") or {}
                            raw_citations = raw.get("citations", [])
                            ancient = [
                                (c.get("label") or c.get("citationText") or "")
                                for c in raw_citations
                                if isinstance(c, dict) and c.get("type") == "passage"
                            ] or [
                                (c.get("label") or c.get("citationText") or "")
                                for c in raw_citations
                                if isinstance(c, dict)
                            ]
                            seed_ids = raw.get("seed_nodes", [])
                            ctx_ids = raw.get("context_nodes", [])
                            lookup = graphrag.node_lookup
                            starting = [
                                {
                                    "id": nid,
                                    "label": lookup.get(nid, {}).get("label", nid),
                                    "type": lookup.get(nid, {}).get("type", "concept"),
                                    "reason": "Retrieved via agent search",
                                }
                                for nid in seed_ids
                            ]
                            expanded = [
                                {
                                    "id": nid,
                                    "label": lookup.get(nid, {}).get("label", nid),
                                    "type": lookup.get(nid, {}).get("type", "concept"),
                                    "reason": "Explored via agent traversal",
                                }
                                for nid in ctx_ids
                                if nid not in seed_ids
                            ]
                            sources = []
                            # Include both seed nodes and top context nodes
                            all_source_ids = list(dict.fromkeys(seed_ids + ctx_ids))[:15]
                            for i, nid in enumerate(all_source_ids):
                                node = lookup.get(nid, {})
                                if not node:
                                    continue
                                sources.append({
                                    "id": i + 1,
                                    "nodeId": nid,
                                    "nodeLabel": node.get("label", nid),
                                    "nodeType": node.get("type", "concept"),
                                    "content": (node.get("description") or "")[:300],
                                    "metadata": {
                                        "school": node.get("school"),
                                        "period": node.get("period"),
                                    },
                                })
                            complete_payload = {
                                "type": "complete",
                                "data": {
                                    "query": raw.get("question", question),
                                    "answer": raw.get("answer", ""),
                                    "citations": {
                                        "ancient_sources": [a for a in ancient if a],
                                        "modern_scholarship": [],
                                    },
                                    "sources": sources,
                                    "reasoning_path": {
                                        "starting_nodes": starting,
                                        "expanded_nodes": expanded[:20],
                                        "traversed_edges": [],
                                        "total_nodes": len(ctx_ids),
                                        "total_edges": 0,
                                    },
                                    "llm_model": raw.get("llm_model", ""),
                                    "llm_provider": raw.get("llm_provider", ""),
                                    "metadata": raw.get("metadata", {}),
                                    "nodes_used": len(ctx_ids),
                                },
                            }
                            yield f"data: {json.dumps(complete_payload, default=str)}\n\n"
                            complete_sent = True
                            continue
                    except json.JSONDecodeError:
                        pass
                event = json.dumps({"type": "answer_chunk", "data": chunk})
                yield f"data: {event}\n\n"
            if not complete_sent:
                yield f'data: {json.dumps({"type": "complete", "data": None})}\n\n'
        except Exception as e:
            yield f'data: {json.dumps({"type": "error", "message": str(e)})}\n\n'

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


@router.get("/health")
async def health() -> dict:
    """Check GraphRAG service health."""
    if _graphrag is None:
        return {"status": "not_initialized"}

    return {
        "status": "healthy",
        "kg_loaded": _graphrag._kg_loaded,
        "nodes_count": len(_graphrag.node_lookup) if _graphrag._kg_loaded else 0,
    }
