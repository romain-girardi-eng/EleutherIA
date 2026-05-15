"""
FastAPI routes for GraphRAG Q&A.
"""

import contextlib
import json
import logging
import time
import uuid
from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import PlainTextResponse, Response, StreamingResponse
from pydantic import ValidationError

from eleutheria_graphrag.models.query import QueryRequest, QueryResponse
from eleutheria_graphrag.models.thesis_output import ThesisDraft
from eleutheria_graphrag.services.graphrag_service import GraphRAGService
from eleutheria_graphrag.services.thesis_renderer import (
    CitationStyle,
    ExportFormat,
    export_draft,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["graphrag"])

# Service instance (to be injected by main app)
_graphrag: GraphRAGService | None = None

# In-memory store for ThesisDraft results, keyed by trace_id. Bounded to keep
# memory under control; the FE downloads the export shortly after streaming.
_DRAFT_TTL_SECONDS = 60 * 60
_DRAFT_STORE_MAX = 256
_draft_store: dict[str, tuple[float, ThesisDraft]] = {}


def store_draft(trace_id: str, draft: ThesisDraft) -> None:
    """Cache a synthesizer draft for later export.

    Drops the oldest entry once the store crosses ``_DRAFT_STORE_MAX``.
    """

    now = time.time()
    expired = [
        k for k, (ts, _) in _draft_store.items() if now - ts > _DRAFT_TTL_SECONDS
    ]
    for k in expired:
        _draft_store.pop(k, None)
    if len(_draft_store) >= _DRAFT_STORE_MAX:
        oldest = min(_draft_store.items(), key=lambda kv: kv[1][0])[0]
        _draft_store.pop(oldest, None)
    _draft_store[trace_id] = (now, draft)


def _load_draft(trace_id: str) -> ThesisDraft:
    entry = _draft_store.get(trace_id)
    if entry is None:
        raise HTTPException(status_code=404, detail=f"no draft for trace_id={trace_id}")
    return entry[1]


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

    Returns Server-Sent Events (SSE) with answer chunks. Token + USD cost
    are captured by a :class:`TraceWriter` for the duration of the request
    (via the ``active_trace_writer`` ContextVar) and surfaced to the UI
    through periodic ``tokens_used_rollup`` events plus a terminal
    ``cost_summary``.
    """

    trace_id = uuid.uuid4().hex
    # Lazy imports: backend depends on graphrag, not the other way around —
    # keep these inside the request handler so the package remains usable
    # standalone (CLI, notebooks) even when backend isn't installed.
    writer = None
    ctx_token = None
    try:
        from backend.dependencies import get_db
        from backend.services.trace_writer import (
            TraceWriter,
            active_trace_writer,
        )

        try:
            writer = TraceWriter(
                get_db(),
                trace_id,
                query=question,
                mode="react",
                metadata={"endpoint": "graphrag.query_stream"},
            )
            await writer.start()
            ctx_token = active_trace_writer.set(writer)
        except RuntimeError:
            # Services not initialized (tests, CLI) — degrade silently.
            writer = None
            ctx_token = None
    except ImportError:
        writer = None
        ctx_token = None

    async def generate() -> AsyncIterator[str]:
        nonlocal writer, ctx_token
        last_emit_t = 0.0
        last_emitted_tokens = -1
        emit_interval_s = 0.8

        def _running_payload() -> dict | None:
            if writer is None:
                return None
            try:
                totals = writer.get_running_totals()
            except Exception:  # noqa: BLE001
                return None
            return {
                "trace_id": trace_id,
                "total_tokens": totals.get("total_tokens", 0),
                "total_cost_usd": totals.get("total_cost_usd", 0.0),
                "by_model": totals.get("by_model", {}),
                "by_agent": totals.get("by_agent", {}),
            }

        try:
            complete_sent = False
            yield f"data: {json.dumps({'type': 'status', 'data': {'message': 'Initializing scholarly agent...', 'step': 1, 'trace_id': trace_id}})}\n\n"
            async for chunk in graphrag.query_stream(
                question=question,
                semantic_k=semantic_k,
                graph_depth=graph_depth,
                max_context_nodes=max_context_nodes,
                selected_model=model,
                retrieval_mode=retrieval_mode,
            ):
                now = time.monotonic()
                rollup = _running_payload()
                if (
                    rollup is not None
                    and rollup["total_tokens"] > last_emitted_tokens
                    and (now - last_emit_t) >= emit_interval_s
                ):
                    yield f"data: {json.dumps({'type': 'tokens_used_rollup', 'data': rollup})}\n\n"
                    last_emit_t = now
                    last_emitted_tokens = rollup["total_tokens"]
                # The agent yields plain text for answer chunks, but the
                # final yield is a JSON string with {"type": "complete", ...}
                # containing the full response (citations, metadata, etc.).
                # Detect it and forward as a proper SSE complete event.
                if chunk.startswith('{"type":'):
                    try:
                        parsed = json.loads(chunk)
                        event_type = parsed.get("type", "")

                        # Forward agent events (thinking, tool calls) directly
                        if event_type in (
                            "agent_thinking",
                            "tool_start",
                            "tool_result",
                            "status",
                            "error",
                        ):
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
                            all_source_ids = list(dict.fromkeys(seed_ids + ctx_ids))[
                                :15
                            ]
                            for i, nid in enumerate(all_source_ids):
                                node = lookup.get(nid, {})
                                if not node:
                                    continue
                                sources.append(
                                    {
                                        "id": i + 1,
                                        "nodeId": nid,
                                        "nodeLabel": node.get("label", nid),
                                        "nodeType": node.get("type", "concept"),
                                        "content": (node.get("description") or "")[
                                            :300
                                        ],
                                        "metadata": {
                                            "school": node.get("school"),
                                            "period": node.get("period"),
                                        },
                                    }
                                )
                            final_answer = raw.get("answer", "")
                            final_citations = [
                                c for c in raw_citations if isinstance(c, dict)
                            ]
                            merged_metadata = dict(raw.get("metadata") or {})
                            cost_payload = _running_payload()
                            if cost_payload is not None:
                                merged_metadata["total_tokens"] = cost_payload[
                                    "total_tokens"
                                ]
                                merged_metadata["total_cost_usd"] = cost_payload[
                                    "total_cost_usd"
                                ]
                                merged_metadata["token_breakdown"] = {
                                    "by_agent": cost_payload["by_agent"],
                                    "by_model": cost_payload["by_model"],
                                }
                                # Surface trace_id so the FE can deep-link to
                                # the audit / export endpoints.
                                merged_metadata["trace_id"] = trace_id
                                yield f"data: {json.dumps({'type': 'cost_summary', 'data': cost_payload})}\n\n"
                            complete_payload = {
                                "type": "complete",
                                "data": {
                                    "query": raw.get("question", question),
                                    "answer": final_answer,
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
                                    "metadata": merged_metadata,
                                    "nodes_used": len(ctx_ids),
                                    "trace_id": trace_id,
                                },
                            }
                            yield f"data: {json.dumps(complete_payload, default=str)}\n\n"
                            complete_sent = True
                            if writer is not None:
                                try:
                                    await writer.finalize(
                                        final_answer=final_answer,
                                        citations=final_citations,
                                    )
                                except Exception:  # noqa: BLE001
                                    logger.exception(
                                        "TraceWriter.finalize failed for %s",
                                        trace_id,
                                    )
                            continue
                    except json.JSONDecodeError:
                        pass
                event = json.dumps({"type": "answer_chunk", "data": chunk})
                yield f"data: {event}\n\n"
            if not complete_sent:
                yield f"data: {json.dumps({'type': 'complete', 'data': {'trace_id': trace_id}})}\n\n"
                if writer is not None:
                    try:
                        await writer.finalize(final_answer="", citations=[])
                    except Exception:  # noqa: BLE001
                        logger.exception(
                            "TraceWriter.finalize (no-answer) failed for %s",
                            trace_id,
                        )
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e), 'trace_id': trace_id})}\n\n"
            if writer is not None:
                try:
                    await writer.finalize(
                        final_answer=f"[error] {e}", citations=[], success=False
                    )
                except Exception:  # noqa: BLE001
                    logger.exception(
                        "TraceWriter.finalize (error path) failed for %s",
                        trace_id,
                    )
        finally:
            if ctx_token is not None:
                with contextlib.suppress(Exception):
                    active_trace_writer.reset(ctx_token)

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


_FORMAT_EXTENSIONS = {
    "markdown": "md",
    "latex": "tex",
    "bibtex": "bib",
    "ris": "ris",
    "zotero": "json",
    "json": "json",
    "docx": "docx",
}


@router.post("/query/draft", response_model=dict)
async def submit_draft(payload: dict) -> dict:
    """Validate + cache a ThesisDraft payload.

    Used by the orchestrator after a streaming run completes so the FE can
    request renderings without re-synthesising. Returns the trace_id under
    which the draft is stored.
    """

    trace_id = payload.get("trace_id")
    if not trace_id or not isinstance(trace_id, str):
        raise HTTPException(status_code=400, detail="trace_id is required")
    raw = payload.get("draft")
    if not isinstance(raw, dict):
        raise HTTPException(status_code=400, detail="draft (object) is required")
    try:
        draft = ThesisDraft.model_validate(raw)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.errors()) from exc
    store_draft(trace_id, draft)
    return {"trace_id": trace_id, "footnotes": len(draft.footnotes)}


@router.get("/query/{trace_id}/export")
async def export_trace(
    trace_id: str,
    format: Annotated[ExportFormat, Query(description="Export format")] = "markdown",
    citation_style: Annotated[
        CitationStyle, Query(description="Citation style for Markdown")
    ] = "chicago",
    download: Annotated[bool, Query(description="Force file download")] = False,
) -> Response:
    """Render a cached ``ThesisDraft`` as Markdown / LaTeX / BibTeX / Zotero / RIS / JSON."""

    draft = _load_draft(trace_id)
    body, media_type = export_draft(draft, format, citation_style=citation_style)
    headers: dict[str, str] = {}
    if download:
        ext = _FORMAT_EXTENSIONS.get(format, "txt")
        headers["Content-Disposition"] = (
            f'attachment; filename="thesis-{trace_id}.{ext}"'
        )
    if format == "markdown":
        return PlainTextResponse(body, media_type=media_type, headers=headers)
    return Response(content=body, media_type=media_type, headers=headers)


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
