"""search_nodes tool — find KG nodes by label/description match."""

from __future__ import annotations

import logging
import os
import re
from typing import Any

from pydantic import BaseModel, Field

from eleutheria_graphrag.agents.dependencies import Deps

logger = logging.getLogger(__name__)

DB_SCHEMA = os.getenv("ELEUTHERIA_DB_SCHEMA", "free_will")
_TERM_RE = re.compile(r"[A-Za-zÀ-ÿἀ-῾']+")


class NodeSummary(BaseModel):
    node_id: str
    label: str
    type: str
    description: str = Field(description="Truncated to 200 chars")
    period: str | None = None
    school: str | None = None
    score: float = 0.0


class SearchNodesResult(BaseModel):
    nodes: list[NodeSummary]
    total_found: int


class SearchNodesTool:
    """Find KG nodes by label/description match with optional type/period filters."""

    def __init__(self, deps: Deps) -> None:
        self._deps = deps

    @property
    def name(self) -> str:
        return "search_nodes"

    @property
    def description(self) -> str:
        return (
            "Search the knowledge graph for nodes (persons, concepts, arguments, "
            "works, schools) by label or description. Returns matching nodes ranked "
            "by relevance. Use type_filter to narrow results."
        )

    @property
    def parameters_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search text"},
                "type_filter": {
                    "type": "string",
                    "description": "Node type filter: person, concept, argument, work, school, passage",
                    "enum": [
                        "person",
                        "concept",
                        "argument",
                        "work",
                        "school",
                        "passage",
                        "debate",
                        "group",
                    ],
                },
                "period_filter": {
                    "type": "string",
                    "description": "Historical period filter",
                },
                "limit": {
                    "type": "integer",
                    "default": 10,
                    "minimum": 1,
                    "maximum": 30,
                },
            },
            "required": ["query"],
        }

    async def execute(self, args: dict[str, Any]) -> SearchNodesResult:
        query = args["query"]
        type_filter = args.get("type_filter")
        period_filter = args.get("period_filter")
        limit = min(max(args.get("limit", 10), 1), 30)

        results: dict[str, tuple[NodeSummary, float]] = {}

        # In-memory label/description match (vectorless).
        query_lower = query.lower()
        query_terms = {t.lower() for t in _TERM_RE.findall(query) if len(t) > 2}

        for node_id, node in self._deps.node_lookup.items():
            node_type = (node.get("type") or "").lower()
            if type_filter and node_type != type_filter.lower():
                continue
            if (
                period_filter
                and (node.get("period") or "").lower() != period_filter.lower()
            ):
                continue

            label = (node.get("label") or "").lower()
            desc = (node.get("description") or "").lower()

            # Exact label match = highest score
            if query_lower == label:
                score = 1.0
            elif query_lower in label:
                score = 0.85
            elif label in query_lower:
                score = 0.75
            else:
                # Term overlap scoring
                label_terms = {t.lower() for t in _TERM_RE.findall(label) if len(t) > 2}
                desc_terms = {
                    t.lower() for t in _TERM_RE.findall(desc[:300]) if len(t) > 2
                }
                label_overlap = len(query_terms & label_terms)
                desc_overlap = len(query_terms & desc_terms)
                if label_overlap == 0 and desc_overlap == 0:
                    continue
                score = min(0.7, 0.3 * label_overlap + 0.1 * desc_overlap)

            # Boost by PageRank
            pr = self._deps.pagerank_scores.get(node_id, 0.0)
            score += pr * 0.1

            results[node_id] = (
                NodeSummary(
                    node_id=node_id,
                    label=node.get("label", ""),
                    type=node.get("type", ""),
                    description=(node.get("description") or "")[:200],
                    period=node.get("period"),
                    school=node.get("school"),
                    score=round(score, 3),
                ),
                score,
            )

        # Sort by score descending, take top limit
        sorted_results = sorted(results.values(), key=lambda x: x[1], reverse=True)
        nodes = [r[0] for r in sorted_results[:limit]]

        return SearchNodesResult(nodes=nodes, total_found=len(results))
