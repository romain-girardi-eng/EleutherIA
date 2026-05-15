"""GraphRAG audit-trail endpoint.

``GET /api/graphrag/query/{trace_id}/audit`` returns the persisted state of a
single deep-mode query — agent tree, tool calls, verifier / counter-evidence /
methodology / polishing reports, final answer text, and timing totals. The
data is written by :class:`backend.services.trace_writer.TraceWriter` during
the lifetime of the query.
"""

from __future__ import annotations

import logging
import uuid
from typing import Annotated, Any

from eleutheria_database.services.db import DatabaseService
from fastapi import APIRouter, Depends, HTTPException, Request

from backend.dependencies import get_db
from backend.routes.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(tags=["graphrag-audit"])


def _coerce_uuid(value: str) -> uuid.UUID:
    try:
        return uuid.UUID(value)
    except (TypeError, ValueError):
        return uuid.uuid5(uuid.NAMESPACE_URL, f"eleutheria:trace:{value}")


@router.get("/query/{trace_id}/audit")
async def get_query_audit(
    trace_id: str,
    request: Request,
    db: Annotated[DatabaseService, Depends(get_db)],
) -> dict[str, Any]:
    """Return the full audit trail for one query."""
    await get_current_user(request, db)

    trace_uuid = _coerce_uuid(trace_id)
    row = await db.fetchrow(
        """
        SELECT
            trace_id, user_id, query, started_at, completed_at, mode,
            agent_tree,
            citation_verifier_report,
            counter_evidence_report,
            methodology_report,
            polishing_report,
            final_answer_text,
            final_answer_citations,
            total_latency_ms,
            total_tool_calls,
            metadata,
            total_tokens,
            total_cost_usd,
            token_breakdown,
            provider_usage
        FROM free_will.query_traces
        WHERE trace_id = $1
        """,
        trace_uuid,
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Trace not found")

    agent_tree = row.get("agent_tree") or {}
    root_agents = (
        agent_tree.get("root_agents") if isinstance(agent_tree, dict) else None
    ) or []
    primary = root_agents[0] if root_agents else None

    final_text = row.get("final_answer_text") or ""

    total_cost_raw = row.get("total_cost_usd")
    total_cost_usd = float(total_cost_raw) if total_cost_raw is not None else 0.0
    return {
        "trace_id": trace_id,
        "query": row.get("query"),
        "started_at": row.get("started_at").isoformat()
        if row.get("started_at")
        else None,
        "completed_at": row.get("completed_at").isoformat()
        if row.get("completed_at")
        else None,
        "mode": row.get("mode"),
        "agent_tree": primary or agent_tree,
        "citation_verifier_report": row.get("citation_verifier_report"),
        "counter_evidence_report": row.get("counter_evidence_report"),
        "methodology_report": row.get("methodology_report"),
        "polishing_report": row.get("polishing_report"),
        "final_answer_length_chars": len(final_text),
        "final_answer_citations": row.get("final_answer_citations") or [],
        "total_latency_ms": row.get("total_latency_ms"),
        "total_tool_calls": row.get("total_tool_calls"),
        "metadata": row.get("metadata") or {},
        "total_tokens": int(row.get("total_tokens") or 0),
        "total_cost_usd": total_cost_usd,
        "token_breakdown": row.get("token_breakdown") or {},
        "provider_usage": row.get("provider_usage") or {},
    }
