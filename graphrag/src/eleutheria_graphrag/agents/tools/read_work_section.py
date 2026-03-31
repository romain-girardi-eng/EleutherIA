"""read_work_section tool — navigate hierarchical tree index of a work."""

from __future__ import annotations

import logging
from typing import Any

from pydantic import BaseModel

from eleutheria_graphrag.agents.dependencies import Deps

logger = logging.getLogger(__name__)


class SectionSummary(BaseModel):
    node_id: str
    title: str
    path: str = ""
    summary: str = ""
    passage_count: int = 0
    has_subsections: bool = False
    concept_tags: list[str] = []


class ReadWorkSectionResult(BaseModel):
    work_id: str
    work_title: str = ""
    author: str = ""
    sections: list[SectionSummary]


class ReadWorkSectionTool:
    """Navigate the hierarchical structure of an ancient work."""

    def __init__(self, deps: Deps) -> None:
        self._deps = deps

    @property
    def name(self) -> str:
        return "read_work_section"

    @property
    def description(self) -> str:
        return (
            "Browse the table of contents of an ancient work. "
            "Call with just a work_id to see the top-level sections. "
            "Call with a section_path to see subsections of that section. "
            "Use this to navigate deep into a specific part of a work."
        )

    @property
    def parameters_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "work_id": {
                    "type": "string",
                    "description": "The work ID (UUID or canonical_id)",
                },
                "section_path": {
                    "type": "string",
                    "description": "Hierarchical path to navigate to (e.g. 'Book III/Chapter 1'). Omit for top-level.",
                },
            },
            "required": ["work_id"],
        }

    async def execute(self, args: dict[str, Any]) -> ReadWorkSectionResult:
        work_id = args["work_id"]
        section_path = args.get("section_path")

        if not self._deps.tree_index:
            return ReadWorkSectionResult(
                work_id=work_id,
                sections=[],
            )

        try:
            indices = await self._deps.tree_index.load_indices([work_id])
        except Exception:
            logger.warning("TreeIndex load failed for %s", work_id, exc_info=True)
            return ReadWorkSectionResult(work_id=work_id, sections=[])

        if not indices:
            return ReadWorkSectionResult(work_id=work_id, sections=[])

        index = indices[0]

        # Navigate to the requested path
        target_nodes = index.nodes
        if section_path:
            path_parts = [p.strip() for p in section_path.split("/") if p.strip()]
            for part in path_parts:
                found = False
                for node in target_nodes:
                    if node.title.lower() == part.lower() or (
                        node.path and node.path.lower().endswith(part.lower())
                    ):
                        target_nodes = node.nodes
                        found = True
                        break
                if not found:
                    # Fuzzy match: check if part is contained in title
                    for node in target_nodes:
                        if part.lower() in node.title.lower():
                            target_nodes = node.nodes
                            found = True
                            break
                if not found:
                    break

        sections = [
            SectionSummary(
                node_id=node.node_id,
                title=node.title,
                path=node.path or "",
                summary=(node.summary or "")[:300],
                passage_count=max(0, node.end_passage - node.start_passage + 1)
                if node.end_passage >= node.start_passage
                else 0,
                has_subsections=len(node.nodes) > 0,
                concept_tags=node.concept_tags[:5] if node.concept_tags else [],
            )
            for node in target_nodes
        ]

        return ReadWorkSectionResult(
            work_id=work_id,
            work_title=index.title,
            author=index.author,
            sections=sections,
        )
