"""get_node_detail tool — full metadata for a specific node."""

from __future__ import annotations

import logging
import os
from typing import Any

from pydantic import BaseModel

from eleutheria_graphrag.agents.dependencies import Deps
from eleutheria_graphrag.agents.graph_helpers import node_integrity_status
from eleutheria_graphrag.services.snapshot_retrieval import (
    db_is_connected,
    linked_passage_rows,
)

logger = logging.getLogger(__name__)

DB_SCHEMA = os.getenv("ELEUTHERIA_DB_SCHEMA", "free_will")


class NodeDetail(BaseModel):
    node_id: str
    label: str
    type: str
    description: str  # Full, not truncated
    period: str | None = None
    school: str | None = None
    metadata: dict[str, Any] = {}
    neighbor_count: int = 0
    passage_count: int = 0
    #: False only when the id resolves to nothing in the graph. Consumers use
    #: this (never the ``(not found)`` label string) to tell a real read from a
    #: miss — a successful read is evidence even when the node has no linked
    #: passages, and must never be counted as a dead end.
    found: bool = True


class GetNodeDetailTool:
    """Get full metadata for a specific KG node."""

    def __init__(self, deps: Deps) -> None:
        self._deps = deps

    @property
    def name(self) -> str:
        return "get_node_detail"

    @property
    def description(self) -> str:
        return (
            "Get detailed information about a specific knowledge graph node, "
            "including its full description, metadata, and counts of neighbors "
            "and linked passages. Use this to inspect a node found via search "
            "or neighbor exploration."
        )

    @property
    def parameters_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "node_id": {"type": "string", "description": "The node ID to inspect"},
            },
            "required": ["node_id"],
        }

    async def execute(self, args: dict[str, Any]) -> NodeDetail:
        node_id = args["node_id"]

        node = self._deps.node_lookup.get(node_id)
        if not node:
            return NodeDetail(
                node_id=node_id,
                label="(not found)",
                type="",
                description=f"Node '{node_id}' not found in the knowledge graph.",
                found=False,
            )

        # Count edges
        out_count = len(self._deps.outgoing_edges.get(node_id, []))
        in_count = len(self._deps.incoming_edges.get(node_id, []))

        # Count passages via DB
        passage_count = 0
        if db_is_connected(self._deps.db):
            try:
                count = await self._deps.db.fetchval(
                    f"SELECT COUNT(*) FROM {DB_SCHEMA}.passage_citations WHERE kg_node_id = $1",
                    node_id,
                )
                passage_count = count or 0
            except Exception:
                logger.debug(
                    "Passage count query failed for %s", node_id, exc_info=True
                )
                passage_count = len(linked_passage_rows(self._deps, [node_id]))
        else:
            passage_count = len(linked_passage_rows(self._deps, [node_id]))

        # Build clean metadata dict (exclude huge fields)
        raw_meta = node.get("metadata") or {}
        clean_meta: dict[str, Any] = {}
        for key, value in raw_meta.items():
            if isinstance(value, str) and len(value) > 500:
                continue  # Skip very large metadata values
            clean_meta[key] = value

        # Integrity-flagged descriptions are not citable text: never surface
        # them in tool results (they would land in Evidence and whitelist
        # their own fabricated Greek in the text verifier). The node itself
        # stays traversable; metadata keeps integrity_status so the agent
        # can see why the description is withheld.
        description = (
            "" if node_integrity_status(node) else (node.get("description") or "")
        )

        return NodeDetail(
            node_id=node_id,
            label=node.get("label", ""),
            type=node.get("type", ""),
            description=description,
            period=node.get("period"),
            school=node.get("school"),
            metadata=clean_meta,
            neighbor_count=out_count + in_count,
            passage_count=passage_count,
        )
