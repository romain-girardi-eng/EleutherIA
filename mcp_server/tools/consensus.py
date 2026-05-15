"""MCP wrapper for the scholarly_consensus_topics table.

Surfaces unresolved scholarly disputes that touch the concepts / persons
cited in a claim. Used by the Counter-Evidence Hunter v2 to attach the
``consensus_dispute`` dimension to a finding.

The table is built by a sibling workstream (Z4). When it is absent, this
tool returns an empty result and a ``table_available=False`` flag so
callers degrade gracefully rather than failing the whole hunt.

Expected table shape (when present):

    CREATE TABLE free_will.scholarly_consensus_topics (
        topic_slug              TEXT PRIMARY KEY,
        label                   TEXT NOT NULL,
        methodological_warning  TEXT,
        positions               JSONB,         -- [{label, proponents, summary}, ...]
        related_concepts        TEXT[],        -- KG node ids
        related_persons         TEXT[],        -- KG node ids
        updated_at              TIMESTAMPTZ DEFAULT now()
    );
"""

from __future__ import annotations

import logging
from typing import Any

from mcp.server.fastmcp import FastMCP

from mcp_server.deps import get_deps

logger = logging.getLogger(__name__)


# Errors that indicate the table or schema is simply absent. We swallow
# those quietly so the hunt continues; everything else is logged.
_MISSING_TABLE_TOKENS = (
    "scholarly_consensus_topics",
    "does not exist",
    "undefinedtable",
    "undefined_table",
)


def _looks_like_missing_table(exc: BaseException) -> bool:
    msg = str(exc).lower()
    return any(token in msg for token in _MISSING_TABLE_TOKENS)


def register(mcp: FastMCP) -> None:
    """Register the consensus tool on the FastMCP server."""

    @mcp.tool()
    async def query_scholarly_consensus(
        concepts: list[str] | None = None,
        persons: list[str] | None = None,
        limit: int = 5,
    ) -> dict[str, Any]:
        """Find unresolved scholarly disputes touching these concepts/persons.

        Queries the ``free_will.scholarly_consensus_topics`` table for rows
        whose ``related_concepts`` or ``related_persons`` arrays intersect the
        supplied KG node ids. Used by the Counter-Evidence Hunter v2 to surface
        the ``consensus_dispute`` dimension.

        If the consensus table is not yet provisioned (sibling workstream),
        the tool returns ``{"topics": [], "table_available": False}`` and the
        caller should skip the consensus dimension.

        Args:
            concepts: KG node ids of concept nodes touched by a claim.
            persons: KG node ids of person nodes touched by a claim.
            limit: 1-20 topics to return.

        Returns:
            ``{"topics": [...], "table_available": bool}``. Each topic carries
            ``topic_slug``, ``label``, ``methodological_warning``,
            ``positions`` (list of rival scholarly positions),
            ``related_concepts``, ``related_persons``.
        """
        concept_ids = [c for c in (concepts or []) if c]
        person_ids = [p for p in (persons or []) if p]
        if not concept_ids and not person_ids:
            return {"topics": [], "table_available": True}

        bounded_limit = max(1, min(int(limit), 20))
        deps = await get_deps()
        db = deps.db

        if not getattr(db, "is_connected", lambda: False)():
            return {"topics": [], "table_available": False}

        sql = """
            SELECT
                topic_slug,
                label,
                methodological_warning,
                COALESCE(positions, '[]'::jsonb)        AS positions,
                COALESCE(related_concepts, '{}'::text[]) AS related_concepts,
                COALESCE(related_persons,  '{}'::text[]) AS related_persons
            FROM free_will.scholarly_consensus_topics
            WHERE related_concepts && $1::text[]
               OR related_persons  && $2::text[]
            ORDER BY updated_at DESC NULLS LAST
            LIMIT $3
        """
        try:
            rows = await db.fetch(sql, concept_ids, person_ids, bounded_limit)
        except Exception as exc:
            if _looks_like_missing_table(exc):
                logger.info(
                    "consensus DB not available — scholarly_consensus_topics absent"
                )
                return {"topics": [], "table_available": False}
            logger.warning("query_scholarly_consensus failed", exc_info=True)
            return {"topics": [], "table_available": True, "error": str(exc)}

        topics: list[dict[str, Any]] = []
        for row in rows or []:
            topics.append(
                {
                    "topic_slug": row.get("topic_slug"),
                    "label": row.get("label"),
                    "methodological_warning": row.get("methodological_warning") or "",
                    "positions": list(row.get("positions") or []),
                    "related_concepts": list(row.get("related_concepts") or []),
                    "related_persons": list(row.get("related_persons") or []),
                }
            )
        return {"topics": topics, "table_available": True}
