"""read_passages tool — load passage text linked to a KG node."""

from __future__ import annotations

import logging
import os
from typing import Any

from pydantic import BaseModel, Field

from eleutheria_graphrag.agents.dependencies import Deps

logger = logging.getLogger(__name__)

DB_SCHEMA = os.getenv("ELEUTHERIA_DB_SCHEMA", "free_will")


class PassageSummary(BaseModel):
    passage_id: str
    work_title: str = ""
    author: str | None = None
    canonical_ref: str | None = None
    language: str | None = None
    text_content: str = Field(default="", description="Original text up to 800 chars")
    translation: str | None = Field(default=None, description="English translation if available")
    confidence: float = 0.0


class ReadPassagesResult(BaseModel):
    node_id: str
    node_label: str
    passages: list[PassageSummary]


class ReadPassagesTool:
    """Load passage text linked to a KG node via passage_citations."""

    def __init__(self, deps: Deps) -> None:
        self._deps = deps

    @property
    def name(self) -> str:
        return "read_passages"

    @property
    def description(self) -> str:
        return (
            "Read the actual ancient text passages linked to a knowledge graph node. "
            "Returns passage text with work title, author, and canonical reference. "
            "Use this to get textual evidence for a philosopher, concept, or argument."
        )

    @property
    def parameters_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "node_id": {"type": "string", "description": "The KG node ID to read passages for"},
                "limit": {"type": "integer", "default": 5, "minimum": 1, "maximum": 10},
            },
            "required": ["node_id"],
        }

    async def execute(self, args: dict[str, Any]) -> ReadPassagesResult:
        node_id = args["node_id"]
        limit = min(max(args.get("limit", 5), 1), 10)

        node = self._deps.node_lookup.get(node_id, {})
        node_label = node.get("label", node_id)
        node_type = (node.get("type") or "").lower()

        rows: list[dict[str, Any]] = []

        # Strategy 1: passage_citations (works for person, concept, argument nodes)
        try:
            rows = await self._deps.db.fetch(f"""
                SELECT
                    p.passage_id::text,
                    w.title,
                    w.author,
                    p.canonical_ref,
                    w.language,
                    p.text_content,
                    pc.confidence
                FROM {DB_SCHEMA}.passage_citations pc
                JOIN {DB_SCHEMA}.passages p ON p.passage_id = pc.passage_id
                JOIN {DB_SCHEMA}.ancient_works w ON w.work_id = p.work_id
                WHERE pc.kg_node_id = $1
                ORDER BY pc.confidence DESC, p.sequence_number
                LIMIT $2
            """, node_id, limit)
        except Exception:
            logger.warning("passage_citations query failed for %s", node_id, exc_info=True)

        # Strategy 2: if node is a work, load passages directly via kg_work_id
        if not rows and node_type == "work":
            try:
                rows = await self._deps.db.fetch(f"""
                    SELECT
                        p.passage_id::text,
                        w.title,
                        w.author,
                        p.canonical_ref,
                        w.language,
                        p.text_content,
                        1.0 AS confidence
                    FROM {DB_SCHEMA}.passages p
                    JOIN {DB_SCHEMA}.ancient_works w ON w.work_id = p.work_id
                    WHERE w.kg_work_id = $1
                    ORDER BY p.sequence_number
                    LIMIT $2
                """, node_id, limit)
            except Exception:
                logger.warning("work passages query failed for %s", node_id, exc_info=True)

        passages: list[PassageSummary] = []
        for row in rows:
            translation = await self._fetch_translation(row.get("passage_id", ""), node_id)
            passages.append(PassageSummary(
                passage_id=row["passage_id"],
                work_title=row.get("title") or "",
                author=row.get("author"),
                canonical_ref=row.get("canonical_ref"),
                language=row.get("language"),
                text_content=(row.get("text_content") or "")[:800],
                translation=translation,
                confidence=row.get("confidence", 0.0),
            ))

        return ReadPassagesResult(
            node_id=node_id,
            node_label=node_label,
            passages=passages,
        )

    async def _fetch_translation(self, passage_id: str, kg_node_id: str) -> str | None:
        """Look up English translation via KG _en nodes linked by translation_of.

        The translation is stored as the description of the _en suffixed KG node.
        """
        # Try: find _en node that translates the passage's KG node
        en_node_id = f"{kg_node_id}_en"
        en_node = self._deps.node_lookup.get(en_node_id)
        if en_node and en_node.get("description"):
            return (en_node["description"] or "")[:800]

        # Try: find translation_of edge from any _en node to this passage's KG node
        for edge in self._deps.incoming_edges.get(kg_node_id, []):
            if edge.get("relation") == "translation_of":
                src_id = edge.get("source", "")
                src_node = self._deps.node_lookup.get(src_id, {})
                if src_node.get("description"):
                    return (src_node["description"] or "")[:800]

        return None
