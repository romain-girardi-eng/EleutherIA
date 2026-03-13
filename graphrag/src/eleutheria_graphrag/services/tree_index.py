"""Tree index service for hierarchical, section-aware work navigation."""

from __future__ import annotations

import json
import logging
import os
from typing import TYPE_CHECKING, Any
from uuid import UUID

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
    path: str | None = None
    canonical_refs: list[str] = Field(default_factory=list)
    abstract: str | None = None
    concept_tags: list[str] = Field(default_factory=list)
    entity_tags: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)
    translation_available: bool = False
    quote_density: float = Field(0.0, ge=0.0)
    token_estimate: int = Field(0, ge=0)
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
    """Load tree indices and extract passage ranges for selected sections."""

    def __init__(self, db: DatabaseService) -> None:
        self.db = db

    async def load_indices(self, work_ids: list[str]) -> list[WorkTreeIndex]:
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

        indices: list[WorkTreeIndex] = []
        for row in rows:
            try:
                tree_data = row["tree_json"]
                if isinstance(tree_data, str):
                    tree_data = json.loads(tree_data)
                if (
                    isinstance(tree_data, dict)
                    and "nodes" in tree_data
                    and "work_id" not in tree_data
                ):
                    idx = WorkTreeIndex(
                        work_id=str(row["work_id"]),
                        title=row["title"],
                        author=row["author"],
                        period=row.get("period"),
                        total_passages=row["total_passages"],
                        nodes=[TreeNode.model_validate(node) for node in tree_data["nodes"]],
                    )
                else:
                    idx = WorkTreeIndex.model_validate(tree_data)
                indices.append(idx)
            except Exception:
                logger.warning("Failed to parse tree index for %s", row["work_id"])
        return indices

    async def resolve_work_ids(self, titles: list[str]) -> list[str]:
        """Resolve work titles or UUID-looking strings to DB work IDs."""
        if not titles:
            return []

        normalized_titles: list[str] = []
        resolved_ids: list[str] = []
        seen: set[str] = set()

        for title in titles:
            value = title.strip()
            if not value:
                continue
            try:
                UUID(value)
            except ValueError:
                normalized_titles.append(value)
                continue

            if value not in seen:
                resolved_ids.append(value)
                seen.add(value)

        if normalized_titles:
            rows: list[dict[str, Any]] = await self.db.fetch(
                f"""
                SELECT work_id::text AS work_id, title
                FROM {DB_SCHEMA}.ancient_works
                WHERE lower(title) = ANY($1::text[])
                ORDER BY title, author, work_id
                """,
                [title.lower() for title in normalized_titles],
            )

            rows_by_title: dict[str, list[str]] = {}
            for row in rows:
                key = str(row["title"]).strip().lower()
                rows_by_title.setdefault(key, []).append(str(row["work_id"]))

            for title in normalized_titles:
                for work_id in rows_by_title.get(title.lower(), []):
                    if work_id not in seen:
                        resolved_ids.append(work_id)
                        seen.add(work_id)

        return resolved_ids

    async def extract_passages(
        self,
        index: WorkTreeIndex,
        node_ids: list[str],
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        """Extract passages for selected section node IDs."""
        passage_ranges: list[tuple[int, int]] = []
        self._collect_ranges(index.nodes, set(node_ids), passage_ranges)
        if not passage_ranges:
            return []

        range_clauses = " OR ".join(
            f"(p.sequence_number >= {start} AND p.sequence_number <= {end})"
            for start, end in passage_ranges
        )
        limit_clause = f"LIMIT {limit}" if limit is not None else ""

        rows: list[dict[str, Any]] = await self.db.fetch(
            f"""
            SELECT
                p.passage_id,
                p.work_id::text AS work_id,
                p.text_content,
                p.canonical_ref,
                p.sequence_number,
                w.title,
                w.author,
                w.language
            FROM {DB_SCHEMA}.passages p
            JOIN {DB_SCHEMA}.ancient_works w ON p.work_id = w.work_id
            WHERE w.work_id::text = $1
              AND ({range_clauses})
            ORDER BY p.sequence_number
            {limit_clause}
            """,
            index.work_id,
        )
        return rows

    def flatten_sections(self, index: WorkTreeIndex) -> list[dict[str, Any]]:
        """Flatten a tree index into section summaries."""
        sections: list[dict[str, Any]] = []

        def visit(nodes: list[TreeNode], parent_path: str = "") -> None:
            for node in nodes:
                path = node.path or f"{parent_path} > {node.title}".strip(" >")
                sections.append(
                    {
                        "work_id": index.work_id,
                        "node_id": node.node_id,
                        "title": node.title,
                        "path": path,
                        "summary": node.summary,
                        "abstract": node.abstract or node.summary,
                        "canonical_refs": node.canonical_refs,
                        "concept_tags": node.concept_tags,
                        "entity_tags": node.entity_tags,
                        "languages": node.languages,
                        "translation_available": node.translation_available,
                        "quote_density": node.quote_density,
                        "token_estimate": node.token_estimate,
                        "start_passage": node.start_passage,
                        "end_passage": node.end_passage,
                    }
                )
                visit(node.nodes, path)

        visit(index.nodes)
        return sections

    def _collect_ranges(
        self,
        nodes: list[TreeNode],
        target_ids: set[str],
        out: list[tuple[int, int]],
    ) -> None:
        for node in nodes:
            if node.node_id in target_ids:
                out.append((node.start_passage, node.end_passage))
            self._collect_ranges(node.nodes, target_ids, out)
