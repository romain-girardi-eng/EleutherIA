"""PageIndex-inspired tree index service.

Manages hierarchical tree indices for ancient works. Each work has a
pre-built JSON tree that the LLM navigates during tree reasoning retrieval.
"""

from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from eleutheria_database.services.db import DatabaseService

DB_SCHEMA = os.getenv("ELEUTHERIA_DB_SCHEMA", "free_will")


class TreeNode(BaseModel):
    """A node in a work's hierarchical tree index."""

    node_id: str
    title: str
    start_passage: int
    end_passage: int
    summary: str
    nodes: list[TreeNode] = Field(default_factory=list)


class WorkTreeIndex(BaseModel):
    """Complete tree index for a single ancient work."""

    work_id: str
    title: str
    author: str
    period: str | None = None
    total_passages: int
    nodes: list[TreeNode]


class TreeIndexService:
    """Manages hierarchical tree indices for ancient works."""

    def __init__(self, db: DatabaseService) -> None:
        self.db = db

    async def load_indices(self, work_ids: list[str]) -> list[WorkTreeIndex]:
        """Load pre-built tree indices for given works."""
        if not work_ids:
            return []

        placeholders = ", ".join(f"${i + 1}" for i in range(len(work_ids)))
        rows: list[dict[str, Any]] = await self.db.fetch(
            f"""
            SELECT work_id, title, author, period, total_passages, tree_json
            FROM {DB_SCHEMA}.work_tree_indices
            WHERE work_id::text IN ({placeholders})
            """,
            *work_ids,
        )

        indices = []
        for row in rows:
            try:
                tree_data = row["tree_json"]
                # tree_json stores WorkTreeIndex (work_id, title, author, period, total_passages, nodes)
                # or legacy root node format with "nodes" key (from older build script)
                if isinstance(tree_data, dict) and "nodes" in tree_data and "work_id" not in tree_data:
                    idx = WorkTreeIndex(
                        work_id=str(row["work_id"]),
                        title=row["title"],
                        author=row["author"],
                        period=row.get("period"),
                        total_passages=row["total_passages"],
                        nodes=[TreeNode.model_validate(n) for n in tree_data["nodes"]],
                    )
                else:
                    idx = WorkTreeIndex.model_validate(tree_data)
                indices.append(idx)
            except Exception:
                logger.warning("Failed to parse tree index for %s", row["work_id"])

        return indices

    async def extract_passages(
        self,
        index: WorkTreeIndex,
        node_ids: list[str],
    ) -> list[dict[str, Any]]:
        """Extract full passage text for selected tree nodes."""
        # Find passage ranges for selected nodes
        passage_ranges: list[tuple[int, int]] = []
        self._collect_ranges(index.nodes, set(node_ids), passage_ranges)

        if not passage_ranges:
            return []

        # Build WHERE clause for sequence_number ranges
        range_clauses = " OR ".join(
            f"(p.sequence_number >= {s} AND p.sequence_number <= {e})"
            for s, e in passage_ranges
        )

        rows: list[dict[str, Any]] = await self.db.fetch(
            f"""
            SELECT p.passage_id, p.text_content, p.canonical_ref,
                   w.title, w.author
            FROM {DB_SCHEMA}.passages p
            JOIN {DB_SCHEMA}.ancient_works w ON p.work_id = w.work_id
            WHERE w.work_id::text = $1
              AND ({range_clauses})
            ORDER BY p.sequence_number
            LIMIT 30
            """,
            index.work_id,
        )
        return rows

    def _collect_ranges(
        self,
        nodes: list[TreeNode],
        target_ids: set[str],
        out: list[tuple[int, int]],
    ) -> None:
        """Recursively collect passage ranges for matching node_ids."""
        for node in nodes:
            if node.node_id in target_ids:
                out.append((node.start_passage, node.end_passage))
            self._collect_ranges(node.nodes, target_ids, out)
