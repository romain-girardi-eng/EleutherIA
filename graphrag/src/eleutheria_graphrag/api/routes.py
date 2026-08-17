"""
FastAPI routes for GraphRAG Q&A.
"""

import asyncio
import contextlib
import hmac
import inspect
import json
import logging
import os
import re
import time
import uuid
from collections.abc import AsyncIterator
from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse, Response, StreamingResponse
from pydantic import ValidationError

from eleutheria_graphrag.agents.answer_subgraph import build_answer_subgraph
from eleutheria_graphrag.agents.dialectical_synthesis import (
    referee_enabled,
    resolve_scholar_synthesis_model,
)
from eleutheria_graphrag.agents.relevance_triage import relevance_triage_enabled
from eleutheria_graphrag.agents.state import scholar_rag_enabled
from eleutheria_graphrag.models.query import QueryRequest, QueryResponse
from eleutheria_graphrag.models.thesis_output import ThesisDraft
from eleutheria_graphrag.services.graphrag_service import GraphRAGService
from eleutheria_graphrag.services.llm_service import CLIENT_LLM_ERROR_MESSAGE
from eleutheria_graphrag.services.thesis_renderer import (
    CitationStyle,
    ExportFormat,
    export_draft,
)

logger = logging.getLogger(__name__)


def _synthesis_is_cacheable(metadata: dict[str, Any]) -> bool:
    """Whether this answer is good enough to replay to future askers.

    ``scholar_synthesis`` is set by the dialectical synthesis: ``status="ok"``
    with ``degraded`` falsy is a real synthesis; ``degraded`` /
    ``deterministic_map`` / ``failed`` mean the synthesis model was unavailable
    and the prose is a structural hedge. Absent metadata means the legacy
    (non-Scholar-RAG) path, which is cacheable as before.
    """
    synthesis = metadata.get("scholar_synthesis")
    if not isinstance(synthesis, dict):
        return True
    if synthesis.get("degraded"):
        return False
    return synthesis.get("status") == "ok"


def _traversed_edges(
    graphrag: GraphRAGService,
    seed_ids: list[str],
    context_ids: list[str],
) -> list[dict[str, str]]:
    """Edges of the retrieved subgraph, in the frontend's reasoning-path shape.

    Both endpoints must be nodes the agent actually retrieved, so this reports
    the traversal that happened rather than inventing connections.
    """
    visited = {nid for nid in (*seed_ids, *context_ids) if nid}
    if not visited:
        return []
    lookup = graphrag.node_lookup
    edges: list[dict[str, str]] = []
    seen: set[tuple[str, str, str]] = set()
    for source in visited:
        for edge in graphrag.outgoing_edges.get(source, []):
            target = edge.get("target", "")
            if target not in visited:
                continue
            relation = edge.get("relation", "related_to")
            key = (source, target, relation)
            if key in seen:
                continue
            seen.add(key)
            edges.append(
                {
                    "source": source,
                    "target": target,
                    "relation": relation,
                    "description": (
                        edge.get("description")
                        or lookup.get(target, {}).get("label", target)
                    ),
                }
            )
    return edges


router = APIRouter(tags=["graphrag"])

# Strong refs to background finalize tasks so a shielded finalize survives the
# cancellation that triggered it (a task with no strong ref can be GC'd).
_BACKGROUND_FINALIZE_TASKS: set[asyncio.Task[None]] = set()

# Defensive guard (GOAL-8, B7): a citation label that is actually a raw KG/
# passage node id must NEVER reach the frontend. Any candidate whose label
# matches this shape is re-resolved via node_lookup; if still unresolved, it is
# OMITTED rather than rendered verbatim. Protects cached replays too.
_LEAKED_ID_RE = re.compile(
    r"^(?:b_[0-9a-f]+"
    r"|scholarly_argument_"
    r"|scholar_position_"
    r"|concept_"
    r"|person_"
    r"|work_"
    r"|argument_"
    r"|publication_"
    r"|pub_)"
)


def _deleak_label(label: str, lookup: dict[str, Any] | None) -> str | None:
    """Return a display-safe label, or ``None`` if it can't be resolved.

    If ``label`` looks like a raw node id, try to resolve it to a human-readable
    label via ``lookup`` (the in-memory KG node dicts). If that fails, return
    ``None`` so the caller OMITS it — a raw id must never render.
    """
    text = (label or "").strip()
    if not text:
        return None
    if not _LEAKED_ID_RE.match(text):
        return text
    node = (lookup or {}).get(text) or {}
    resolved = ""
    if isinstance(node, dict):
        resolved = str(node.get("label") or "").strip()
    if resolved and not _LEAKED_ID_RE.match(resolved):
        return resolved
    return None


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
            hunt_counter_evidence=request.mode == "deep",
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
    force_refresh: bool = False,
    mode: str = "fast",
) -> StreamingResponse:
    """
    Execute a GraphRAG query with streaming response.

    Returns Server-Sent Events (SSE) with answer chunks. Token + USD cost
    are captured by a :class:`TraceWriter` for the duration of the request
    (via the ``active_trace_writer`` ContextVar) and surfaced to the UI
    through periodic ``tokens_used_rollup`` events plus a terminal
    ``cost_summary``.

    A pre-flight lookup against ``free_will.answer_cache`` short-circuits the
    pipeline when an unexpired entry exists for the
    ``(normalized_question, model, retrieval_mode, mode)`` tuple — fast and
    deep (counter-evidence) answers never share a slot. Pass
    ``force_refresh=true`` to bypass the cache and re-synthesise.

    ``mode`` is normalised to lowercase and must be ``fast`` or ``deep`` —
    anything else is a 422 (previously ``Deep`` silently ran fast mode AND
    occupied its own cache slot).
    """
    mode = mode.strip().lower()
    if mode not in {"fast", "deep"}:
        raise HTTPException(
            status_code=422,
            detail="mode must be 'fast' or 'deep'",
        )

    trace_id = uuid.uuid4().hex
    # Lazy imports: backend depends on graphrag, not the other way around —
    # keep these inside the request handler so the package remains usable
    # standalone (CLI, notebooks) even when backend isn't installed.
    writer = None
    ctx_token = None
    cache_hit: dict | None = None
    answer_cache = None
    try:
        from backend.dependencies import get_db
        from backend.services.answer_cache import AnswerCache
        from backend.services.trace_writer import (
            TraceWriter,
            active_trace_writer,
        )

        # Cache lookup BEFORE TraceWriter init so a hit doesn't pollute the
        # query_traces table with a fake pipeline run — we still create a
        # writer below to record the cache_hit in the audit log.
        if not force_refresh:
            try:
                answer_cache = AnswerCache(get_db())
                cache_hit = await answer_cache.lookup(
                    question=question,
                    model=model,
                    retrieval_mode=retrieval_mode,
                    mode=mode,
                )
            except Exception:  # noqa: BLE001
                logger.exception("answer cache lookup failed")
                cache_hit = None

        try:
            writer_metadata: dict = {"endpoint": "graphrag.query_stream"}
            if cache_hit is not None:
                writer_metadata["cache_hit"] = True
                writer_metadata["cached_from_trace_id"] = cache_hit.get("trace_id")
            writer = TraceWriter(
                get_db(),
                trace_id,
                query=question,
                mode="react",
                metadata=writer_metadata,
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
        answer_cache = None

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

        # Fix 8: TraceWriter.finalize used to run only inside the `try`, so an
        # asyncio.CancelledError / GeneratorExit (BaseException — the client
        # disconnecting mid-stream) skipped every call site and left the trace
        # row with NULL completed_at / final_answer_text. `finalized` is set at
        # each call site and the `finally` compensates on any BaseException.
        finalized = False
        complete_sent = False
        partial_answer_parts: list[str] = []
        # KG nodes the agent actually touched during retrieval, in activation
        # order — the live truth behind the curated answer subgraph. The agent's
        # terminal payload only carries the seed/context id lists, which are
        # capped and often thinner than what retrieval really walked.
        activated_nodes: dict[str, dict[str, Any]] = {}

        async def _finalize_once(
            *, final_answer: str, citations: list, success: bool = True
        ) -> None:
            nonlocal finalized
            if finalized or writer is None:
                return
            finalized = True
            await writer.finalize(
                final_answer=final_answer, citations=citations, success=success
            )

        try:
            # ---- Cache replay path -------------------------------------
            # If the pre-flight lookup found a fresh entry, emit a
            # synthesized `cache_hit` + `cost_summary` + `complete` and
            # bail out before touching the agent pipeline.
            if cache_hit is not None:
                cached_payload = cache_hit
                cached_at = cached_payload.get("created_at")
                cached_at_iso = (
                    cached_at.isoformat()
                    if isinstance(cached_at, datetime)
                    else str(cached_at)
                )
                yield (
                    "data: "
                    + json.dumps(
                        {
                            "type": "cache_hit",
                            "data": {
                                "cache_key_short": str(
                                    cached_payload.get("cache_key", "")
                                )[:12],
                                "original_trace_id": cached_payload.get("trace_id"),
                                "original_cost_usd": float(
                                    cached_payload.get("total_cost_usd") or 0
                                ),
                                "original_tokens": int(
                                    cached_payload.get("total_tokens") or 0
                                ),
                                "cached_at": cached_at_iso,
                                "hit_count": int(cached_payload.get("hit_count") or 0),
                            },
                        }
                    )
                    + "\n\n"
                )

                cache_hit_cost_summary: dict[str, Any] = {
                    "trace_id": trace_id,
                    "total_tokens": 0,
                    "total_cost_usd": 0.0,
                    "by_model": {},
                    "by_agent": {},
                }
                yield f"data: {json.dumps({'type': 'cost_summary', 'data': cache_hit_cost_summary})}\n\n"

                cached_passage_citations = cached_payload.get("passage_citations") or []
                cached_sources = cached_payload.get("sources") or []
                cached_reasoning = cached_payload.get("reasoning_path") or {
                    "starting_nodes": [],
                    "expanded_nodes": [],
                    "traversed_edges": [],
                    "total_nodes": 0,
                    "total_edges": 0,
                }
                cached_ancient = cached_payload.get("citations") or []
                # B6/B7 — rebuild BOTH citation layers from the persisted typed
                # citations (passage_citations carry {type, layer, label}); fall
                # back to the legacy ancient string list. Every label is deleaked
                # so a cached row written before GOAL-8 can never replay a raw id.
                replay_lookup = getattr(graphrag, "node_lookup", {}) or {}
                _typed = [c for c in cached_passage_citations if isinstance(c, dict)]
                if _typed:
                    cached_ancient_labels = [
                        lbl
                        for c in _typed
                        if c.get("layer") != "secondary"
                        and (
                            lbl := _deleak_label(
                                c.get("label") or c.get("citationText") or "",
                                replay_lookup,
                            )
                        )
                    ]
                    cached_modern_labels = [
                        lbl
                        for c in _typed
                        if c.get("layer") == "secondary"
                        and (
                            lbl := _deleak_label(
                                c.get("label") or c.get("citationText") or "",
                                replay_lookup,
                            )
                        )
                    ]
                else:
                    cached_ancient_labels = [
                        lbl
                        for a in cached_ancient
                        if (lbl := _deleak_label(a, replay_lookup))
                    ]
                    cached_modern_labels = []
                # Replay the provenance persisted at store time
                # (text_verification, grounding, citation_verifier_v2,
                # research graph keys, …) — without it, cache hits silently
                # downgraded the answer to an unverified shell.
                stored_metadata = cached_payload.get("metadata") or {}
                cached_claim_ledger = cached_payload.get("claim_ledger") or []
                cached_metadata = {
                    **(stored_metadata if isinstance(stored_metadata, dict) else {}),
                    "cached": True,
                    "cached_from_trace_id": cached_payload.get("trace_id"),
                    "cached_at": cached_at_iso,
                    "cache_key_short": str(cached_payload.get("cache_key", ""))[:12],
                    "total_tokens": 0,
                    "total_cost_usd": 0.0,
                    "trace_id": trace_id,
                }
                complete_payload = {
                    "type": "complete",
                    "data": {
                        "query": question,
                        "answer": cached_payload.get("answer", ""),
                        "citations": {
                            "ancient_sources": [a for a in cached_ancient_labels if a],
                            "modern_scholarship": [
                                m for m in cached_modern_labels if m
                            ],
                        },
                        "passage_citations": cached_passage_citations,
                        "claim_ledger": cached_claim_ledger,
                        "sources": cached_sources,
                        "reasoning_path": cached_reasoning,
                        "llm_model": model,
                        "llm_provider": "",
                        "metadata": cached_metadata,
                        "nodes_used": cached_reasoning.get("total_nodes", 0)
                        if isinstance(cached_reasoning, dict)
                        else 0,
                        "trace_id": trace_id,
                    },
                }
                yield f"data: {json.dumps(complete_payload, default=str)}\n\n"
                complete_sent = True
                try:
                    await _finalize_once(
                        final_answer=cached_payload.get("answer", ""),
                        citations=cached_passage_citations,
                    )
                except Exception:  # noqa: BLE001
                    logger.exception(
                        "TraceWriter.finalize (cache hit) failed for %s",
                        trace_id,
                    )
                return

            # Scholar-RAG (G6) flag, read once per stream. When ON we forward
            # the full frontend-protocol trace-event set (and any other typed
            # event) on its own SSE channel so NONE leak into `answer_chunk`
            # prose. When OFF the legacy narrow allowlist is preserved
            # byte-for-byte so the flag-OFF wire stays identical.
            from eleutheria_graphrag.agents.state import scholar_rag_enabled

            _scholar_rag_on = scholar_rag_enabled()

            yield f"data: {json.dumps({'type': 'status', 'data': {'message': 'Initializing scholarly agent...', 'step': 1, 'trace_id': trace_id}})}\n\n"
            # mode='deep' pass-through: GraphRAGService.query() already honors
            # hunt_counter_evidence, but query_stream() does not accept it yet
            # (the streaming pipeline is being extended separately). Forward
            # the flag only when the signature supports it so the wiring
            # activates automatically once the service lands the parameter.
            stream_kwargs: dict[str, Any] = {
                "question": question,
                "semantic_k": semantic_k,
                "graph_depth": graph_depth,
                "max_context_nodes": max_context_nodes,
                "selected_model": model,
                "retrieval_mode": retrieval_mode,
            }
            if (
                "hunt_counter_evidence"
                in inspect.signature(graphrag.query_stream).parameters
            ):
                stream_kwargs["hunt_counter_evidence"] = mode == "deep"
            elif mode == "deep":
                logger.warning(
                    "mode=deep requested but GraphRAGService.query_stream does "
                    "not accept hunt_counter_evidence yet — running fast mode"
                )
            async for chunk in graphrag.query_stream(**stream_kwargs):
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

                        # Record every KG node the agent activated so the
                        # curated answer subgraph reflects the retrieval that
                        # actually happened (see `activated_nodes`).
                        if event_type == "kg_node_activated":
                            _nid = str(parsed.get("node_id") or "")
                            if _nid and _nid not in activated_nodes:
                                activated_nodes[_nid] = {
                                    "id": _nid,
                                    "label": parsed.get("label") or _nid,
                                    "type": parsed.get("node_type") or "concept",
                                }

                        # Forward agent trace events directly on their own
                        # channel. The legacy (flag-OFF) allowlist is preserved
                        # byte-for-byte; with Scholar-RAG ON we ALSO forward the
                        # full frontend-protocol trace-event set so NONE of them
                        # ever fall through to the `answer_chunk` prose branch
                        # below (which would leak raw `{"type":"tool_call"…}`
                        # JSON into the dialectical answer).
                        _legacy_trace_events = (
                            "agent_thinking",
                            "tool_start",
                            "tool_result",
                            "status",
                            "error",
                            "citation_verified",
                            "stage_complete",
                            # Research journal: what the agent abandoned, ruled
                            # out or could not find. Flag-independent — it is a
                            # trace channel, never answer_chunk prose.
                            "research_note",
                            # F6: per-query grounding diagnostics — forwarded on
                            # its own channel regardless of the scholar-RAG flag
                            # so it never leaks into answer_chunk prose.
                            "scholar_diagnostics",
                        )
                        _scholar_extra_trace_events = (
                            "agent_start",
                            "agent_complete",
                            "tool_call",
                            "kg_node_activated",
                            "citation_found",
                            "final_answer",
                            "cost_summary",
                            "tokens_used_rollup",
                            "verification_warning",
                            # LIVE dialectical-synthesis chain-of-thought — its
                            # OWN channel, NEVER folded into answer_chunk prose.
                            "synthesis_reasoning",
                        )
                        if event_type in _legacy_trace_events or (
                            _scholar_rag_on
                            and event_type in _scholar_extra_trace_events
                        ):
                            yield f"data: {chunk}\n\n"
                            continue

                        if event_type in ("complete", "citations_preview"):
                            # Transform agent data to match the frontend
                            # GraphRAGResponse shape (same as /answer).
                            #
                            # `citations_preview` is an EARLY frame the agent
                            # emits right after ProgrammaticVerify populates the
                            # structured citations, BEFORE the long verifier-v2
                            # audit. It has the identical `data` shape as the
                            # terminal `complete`, so it runs through the same
                            # transform — but it does NOT terminate the stream,
                            # is NOT persisted to the answer cache, and does NOT
                            # finalize the trace. Its sole purpose is to deliver
                            # structured, clickable citations to the UI even if
                            # the audit or the Cloudflare connection is cut
                            # before the authoritative `complete` arrives.
                            is_preview = event_type == "citations_preview"
                            raw = parsed.get("data") or {}
                            raw_citations = raw.get("citations", [])
                            seed_ids = raw.get("seed_nodes", [])
                            ctx_ids = raw.get("context_nodes", [])
                            lookup = graphrag.node_lookup
                            # B6 — ancient (primary/passage) labels, deleaked.
                            ancient_raw = [
                                (c.get("label") or c.get("citationText") or "")
                                for c in raw_citations
                                if isinstance(c, dict) and c.get("type") == "passage"
                            ] or [
                                (c.get("label") or c.get("citationText") or "")
                                for c in raw_citations
                                if isinstance(c, dict) and c.get("layer") != "secondary"
                            ]
                            ancient = [
                                lbl
                                for c in ancient_raw
                                if (lbl := _deleak_label(c, lookup))
                            ]
                            # B6 — modern scholarship (secondary layer), deleaked.
                            modern = [
                                lbl
                                for c in raw_citations
                                if isinstance(c, dict)
                                and c.get("layer") == "secondary"
                                and (
                                    lbl := _deleak_label(
                                        c.get("label") or c.get("citationText") or "",
                                        lookup,
                                    )
                                )
                            ]
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
                            # Typed claim-ledger entries from the agent's
                            # complete payload (emitted by _chunk_answer).
                            final_claim_ledger = [
                                c
                                for c in (raw.get("claim_ledger") or [])
                                if isinstance(c, dict)
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
                                # Cost rollup belongs to the authoritative
                                # `complete`; don't double-emit it on the early
                                # preview (verifier-v2 costs are not yet in).
                                if not is_preview:
                                    yield f"data: {json.dumps({'type': 'cost_summary', 'data': cost_payload})}\n\n"
                            # Fix 10b: the traversal used to ship hardcoded
                            # empty edges, so the FE research graph and
                            # TraversalDAG rendered nodes with no connections.
                            # Derive the real edges from the KG: every edge of
                            # the snapshot whose BOTH endpoints are nodes the
                            # agent actually retrieved.
                            # Activated nodes count as retrieved: an edge
                            # between two nodes the agent walked IS part of the
                            # traversal, even when the terminal context list
                            # (capped) dropped one of them.
                            traversed_edges = _traversed_edges(
                                graphrag,
                                seed_ids,
                                [*ctx_ids, *activated_nodes],
                            )
                            # The curated per-answer knowledge graph: the
                            # controversy map (frames -> positions -> contested
                            # passages, with the real dialectical links) joined
                            # with the KG nodes retrieval actually activated.
                            # `controversy_skeleton` is the agent-side seam and
                            # is consumed here, not shipped to the client.
                            subgraph = build_answer_subgraph(
                                skeleton=merged_metadata.pop(
                                    "controversy_skeleton", None
                                ),
                                seed_ids=seed_ids,
                                context_ids=ctx_ids,
                                activated=list(activated_nodes.values()),
                                node_lookup=lookup,
                                outgoing_edges=getattr(graphrag, "outgoing_edges", {}),
                            )
                            # Real counts: every distinct node retrieval used
                            # (seeds + context + activated), and every KG edge
                            # found between them. `total_nodes` used to report
                            # the context list alone, which under-counted the
                            # seeds the answer was actually built on.
                            retrieved_ids = {
                                nid
                                for nid in (
                                    *seed_ids,
                                    *ctx_ids,
                                    *activated_nodes,
                                )
                                if nid
                            }
                            reasoning_path_payload: dict[str, Any] = {
                                "starting_nodes": starting,
                                "expanded_nodes": expanded[:20],
                                "traversed_edges": traversed_edges[:200],
                                "subgraph": subgraph,
                                "total_nodes": len(retrieved_ids),
                                "total_edges": len(traversed_edges),
                            }
                            complete_payload = {
                                "type": event_type,
                                "data": {
                                    "query": raw.get("question", question),
                                    "answer": final_answer,
                                    "citations": {
                                        "ancient_sources": [a for a in ancient if a],
                                        "modern_scholarship": [m for m in modern if m],
                                    },
                                    # Structured claim-ledger entries — the
                                    # frontend needs the {ref, id, type, label}
                                    # tuples (not just label strings) to make
                                    # [P3] badges clickable and route them to
                                    # the right passage UUID.
                                    "passage_citations": final_citations,
                                    "claim_ledger": final_claim_ledger,
                                    "sources": sources,
                                    "reasoning_path": reasoning_path_payload,
                                    "llm_model": raw.get("llm_model", ""),
                                    "llm_provider": raw.get("llm_provider", ""),
                                    "metadata": merged_metadata,
                                    "nodes_used": len(ctx_ids),
                                    "trace_id": trace_id,
                                },
                            }
                            yield f"data: {json.dumps(complete_payload, default=str)}\n\n"

                            # The preview is non-terminal: deliver structured
                            # citations now, but let the pipeline finish so the
                            # authoritative `complete` (audited + cost-rolled)
                            # supersedes it. No cache write, no trace finalize.
                            if is_preview:
                                continue

                            complete_sent = True

                            # Persist this answer for future cache hits. Length
                            # alone is NOT a quality proxy: a degraded
                            # structural answer (the deterministic map hedge,
                            # emitted when the synthesis model was unavailable)
                            # easily clears 1000 chars and would then be
                            # replayed to every future asker of the question.
                            # Gate on the synthesis status instead.
                            if (
                                answer_cache is not None
                                and isinstance(final_answer, str)
                                and len(final_answer) >= 1000
                                and _synthesis_is_cacheable(merged_metadata)
                            ):
                                cached_tokens = int(
                                    cost_payload["total_tokens"] if cost_payload else 0
                                )
                                cached_cost = float(
                                    cost_payload["total_cost_usd"]
                                    if cost_payload
                                    else 0
                                )
                                try:
                                    await answer_cache.store(
                                        question=question,
                                        model=model,
                                        retrieval_mode=retrieval_mode,
                                        mode=mode,
                                        answer=final_answer,
                                        citations=[a for a in ancient if a],
                                        passage_citations=final_citations,
                                        sources=sources,
                                        reasoning_path=reasoning_path_payload,
                                        total_tokens=cached_tokens,
                                        total_cost_usd=cached_cost,
                                        trace_id=trace_id,
                                        # Provenance payload — replayed on
                                        # cache hits so verification data
                                        # (text_verification, grounding,
                                        # citation_verifier_v2, research
                                        # graph) survives the cache.
                                        metadata=merged_metadata,
                                        claim_ledger=final_claim_ledger,
                                    )
                                except Exception:  # noqa: BLE001
                                    logger.exception(
                                        "answer_cache.store failed for %s",
                                        trace_id,
                                    )

                            if writer is not None:
                                try:
                                    # Persist provenance on the trace row so
                                    # the share renderer (/share/{token}) can
                                    # surface claims + verification verdicts.
                                    writer.metadata["answer_metadata"] = {
                                        k: merged_metadata.get(k)
                                        for k in (
                                            "text_verification",
                                            "grounding",
                                            "citation_verifier_v2",
                                            "quality_badge",
                                            "grounding_policy",
                                        )
                                        if merged_metadata.get(k) is not None
                                    }
                                    if final_claim_ledger:
                                        writer.metadata["claim_ledger"] = (
                                            final_claim_ledger
                                        )
                                    await _finalize_once(
                                        final_answer=final_answer,
                                        citations=final_citations,
                                    )
                                except Exception:  # noqa: BLE001
                                    logger.exception(
                                        "TraceWriter.finalize failed for %s",
                                        trace_id,
                                    )
                            continue

                        # Safety net (Scholar-RAG path only): any OTHER chunk
                        # that parsed as a typed JSON event is a trace event by
                        # construction (prose chunks are raw text, never typed
                        # JSON). Forward it raw rather than letting it fall
                        # through to the `answer_chunk` branch and pollute the
                        # dialectical answer stream. Flag-OFF keeps the legacy
                        # fall-through unchanged.
                        if _scholar_rag_on and event_type:
                            yield f"data: {chunk}\n\n"
                            continue
                    except json.JSONDecodeError:
                        pass
                # Keep the prose that has actually reached the client so a
                # cancelled/disconnected stream finalizes with the partial
                # answer instead of NULL.
                if isinstance(chunk, str):
                    partial_answer_parts.append(chunk)
                event = json.dumps({"type": "answer_chunk", "data": chunk})
                yield f"data: {event}\n\n"
            if not complete_sent:
                complete_sent = True
                yield f"data: {json.dumps({'type': 'complete', 'data': {'trace_id': trace_id}})}\n\n"
                try:
                    await _finalize_once(
                        final_answer="".join(partial_answer_parts), citations=[]
                    )
                except Exception:  # noqa: BLE001
                    logger.exception(
                        "TraceWriter.finalize (no-answer) failed for %s",
                        trace_id,
                    )
        except Exception:
            # Fix 5d: never put the raw provider exception on the wire — it can
            # carry credentials (httpx embeds the request URL) and provider
            # internals. The client gets a generic message; the detail stays in
            # the server log.
            logger.exception("Query stream failed for %s", trace_id)
            yield (
                "data: "
                + json.dumps(
                    {
                        "type": "error",
                        "message": CLIENT_LLM_ERROR_MESSAGE,
                        "trace_id": trace_id,
                    }
                )
                + "\n\n"
            )
            # TERMINAL-FRAME GUARANTEE: the client waits on `complete`. Without
            # it an errored stream leaves the UI spinning forever, even though
            # some prose may already have shipped.
            if not complete_sent:
                complete_sent = True
                yield (
                    "data: "
                    + json.dumps(
                        {
                            "type": "complete",
                            "data": {
                                "trace_id": trace_id,
                                "answer": "".join(partial_answer_parts),
                                "error": CLIENT_LLM_ERROR_MESSAGE,
                            },
                        }
                    )
                    + "\n\n"
                )
            try:
                await _finalize_once(
                    final_answer="".join(partial_answer_parts),
                    citations=[],
                    success=False,
                )
            except Exception:  # noqa: BLE001
                logger.exception(
                    "TraceWriter.finalize (error path) failed for %s",
                    trace_id,
                )
        finally:
            # BaseException-safe: CancelledError / GeneratorExit unwind straight
            # through the `except Exception` above, so this is the only place
            # guaranteed to run when the client disconnects mid-stream.
            if not finalized and writer is not None:
                # `contextlib.suppress(Exception)` would not cover the
                # CancelledError that put us here, and a bare await would be
                # cancelled instantly. Shield it: the finalize runs to
                # completion on the loop while the cancellation propagates.
                finalize_task = asyncio.ensure_future(
                    _finalize_once(
                        final_answer="".join(partial_answer_parts),
                        citations=[],
                        success=complete_sent,
                    )
                )
                _BACKGROUND_FINALIZE_TASKS.add(finalize_task)
                finalize_task.add_done_callback(_BACKGROUND_FINALIZE_TASKS.discard)
                with contextlib.suppress(BaseException):
                    await asyncio.shield(finalize_task)
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


def _require_draft_token(request: Request) -> None:
    """Refuse draft submission unless the shared-secret token matches.

    The endpoint writes into the export cache keyed by trace_id, so leaving it
    open would let anyone replace the rendered thesis for a real trace. When
    ``GRAPHRAG_DRAFT_SUBMIT_TOKEN`` is unset the endpoint is disabled outright.
    """
    expected = os.environ.get("GRAPHRAG_DRAFT_SUBMIT_TOKEN", "").strip()
    if not expected:
        raise HTTPException(status_code=403, detail="draft submission disabled")
    provided = request.headers.get("authorization", "")
    if not hmac.compare_digest(provided.encode(), f"Bearer {expected}".encode()):
        raise HTTPException(status_code=401, detail="unauthorized")


@router.post("/query/draft", response_model=dict)
async def submit_draft(payload: dict, request: Request) -> dict:
    """Validate + cache a ThesisDraft payload.

    Used by the orchestrator after a streaming run completes so the FE can
    request renderings without re-synthesising. Returns the trace_id under
    which the draft is stored.
    """

    _require_draft_token(request)
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
    scholarly_configuration = {
        "scholar_rag": scholar_rag_enabled(),
        "referee": referee_enabled(),
        "relevance_triage": relevance_triage_enabled(),
        "synthesis_model": resolve_scholar_synthesis_model(),
    }
    if _graphrag is None:
        return {
            "status": "not_initialized",
            "scholarly_configuration": scholarly_configuration,
        }

    return {
        "status": "healthy",
        "kg_loaded": _graphrag._kg_loaded,
        "nodes_count": len(_graphrag.node_lookup) if _graphrag._kg_loaded else 0,
        "scholarly_configuration": scholarly_configuration,
    }


# F7: internal smoke endpoint. The Cloudflare tunnel severs long EXTERNAL SSE
# streams (a `curl …/query/stream` is cut mid-retrieval), so CI/cron cannot
# E2E-test the answer path from outside. This runs ONE canned scholar-RAG query
# IN-PROCESS (localhost, no tunnel) and returns pass/fail metrics — the
# regression catch the external curl cannot do.
_SMOKE_QUESTION = "Did Epictetus think freedom is up to us?"
# Greek polytonic ranges — used to assert ≥1 quotable-Greek primary source
# actually reached the answer (the F3/GOAL-7 grounding contract).
_GREEK_CHAR_RE = re.compile(r"[Ͱ-Ͽἀ-῿]")


def _require_smoke_token(request: Request) -> None:
    """Refuse the smoke run unless the shared-secret token matches.

    The endpoint spends real LLM budget and exercises the full pipeline, so it
    is authenticated. When ``GRAPHRAG_SMOKE_TOKEN`` is unset the endpoint is
    disabled outright (403) — it never runs unauthenticated.
    """
    expected = os.environ.get("GRAPHRAG_SMOKE_TOKEN", "").strip()
    if not expected:
        raise HTTPException(status_code=403, detail="smoke endpoint disabled")
    provided = request.headers.get("authorization", "")
    if not hmac.compare_digest(provided.encode(), f"Bearer {expected}".encode()):
        raise HTTPException(status_code=401, detail="unauthorized")


def _smoke_metrics(result: dict[str, Any], elapsed_s: float) -> dict[str, Any]:
    """Reduce one canned-query result to pass/fail smoke metrics (F7).

    Pure + defensive — a malformed result yields a failing (not crashing)
    report. Metrics:

    * ``non_empty``      — the answer prose is substantive (≥200 chars).
    * ``greek``          — quotable-Greek primary sources that reached the
      answer (prefers the F6 ``scholar_diagnostics`` count; falls back to
      scanning citation labels + the answer prose for polytonic Greek).
    * ``ancient``        — distinct ancient sources (diagnostics, else the
      count of non-secondary citations).
    * ``leaked_ids``     — citation labels that are raw node ids (MUST be 0;
      a raw ``b_…``/``person_…`` id must never render — see ``_deleak_label``).
    """
    answer = result.get("answer") or ""
    citations = [c for c in (result.get("citations") or []) if isinstance(c, dict)]
    metadata = result.get("metadata") or {}
    diagnostics = metadata.get("scholar_diagnostics") or {}
    if not isinstance(diagnostics, dict):
        diagnostics = {}

    non_empty = isinstance(answer, str) and len(answer.strip()) >= 200

    greek = int(diagnostics.get("passages_with_quotable_greek") or 0)
    if greek == 0:
        greek = sum(
            1 for c in citations if _GREEK_CHAR_RE.search(str(c.get("label") or ""))
        )
        if greek == 0 and isinstance(answer, str) and _GREEK_CHAR_RE.search(answer):
            greek = 1

    ancient = int(diagnostics.get("ancient_sources") or 0)
    if ancient == 0:
        ancient = sum(1 for c in citations if c.get("layer") != "secondary")

    leaked_ids = sum(
        1 for c in citations if _LEAKED_ID_RE.match(str(c.get("label") or "").strip())
    )

    metrics = {
        "non_empty": non_empty,
        "greek": greek,
        "ancient": ancient,
        "leaked_ids": leaked_ids,
        "elapsed_s": round(elapsed_s, 2),
    }
    metrics["pass"] = bool(
        non_empty and greek >= 1 and ancient >= 1 and leaked_ids == 0
    )
    return metrics


@router.get("/_smoke")
async def smoke(
    request: Request,
    graphrag: Annotated[GraphRAGService, Depends(get_graphrag)],
) -> dict[str, Any]:
    """Run ONE canned scholar-RAG query end-to-end and return pass/fail metrics.

    Authenticated (``GRAPHRAG_SMOKE_TOKEN`` shared secret). Runs IN-PROCESS so
    CI/cron can exercise the full answer path without the Cloudflare tunnel that
    cuts external streams. Returns ``{pass, non_empty, greek, ancient,
    leaked_ids, elapsed_s, …}`` with HTTP 200 on pass and 503 on fail so a
    cron/healthcheck can alert on a non-200.
    """
    _require_smoke_token(request)
    started = time.monotonic()
    try:
        result = await graphrag.query(
            question=_SMOKE_QUESTION,
            include_passages=True,
        )
    except Exception as exc:  # noqa: BLE001 - convert to a 503 so cron alerts
        # A total pipeline failure (LLM down, DB unreachable, OOM) is EXACTLY
        # what the smoke test exists to catch — it must be a non-200 like the
        # metrics-fail path below, not a 200 that a healthcheck reads as healthy.
        elapsed = time.monotonic() - started
        raise HTTPException(
            status_code=503,
            detail={
                "pass": False,
                "non_empty": False,
                "greek": 0,
                "ancient": 0,
                "leaked_ids": 0,
                "elapsed_s": round(elapsed, 2),
                "error": f"{type(exc).__name__}: {exc}"[:300],
                "question": _SMOKE_QUESTION,
            },
        ) from exc
    elapsed = time.monotonic() - started
    metrics = _smoke_metrics(result, elapsed)
    metrics["question"] = _SMOKE_QUESTION
    metrics["llm_model"] = result.get("llm_model", "")
    if not metrics["pass"]:
        raise HTTPException(status_code=503, detail=metrics)
    return metrics
