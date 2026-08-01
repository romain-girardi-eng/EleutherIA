"""get_neighbors tool — explore graph edges from a known node."""

from __future__ import annotations

import logging
from typing import Any

from pydantic import BaseModel

from eleutheria_graphrag.agents.dependencies import Deps

logger = logging.getLogger(__name__)

# Default k-hop depth used for the DB-backed fallback (see
# `_fetch_db_neighborhood`). Kept at 1 to match this tool's "immediate
# neighbors" contract.
_DB_FALLBACK_DEPTH = 1


class EdgeSummary(BaseModel):
    edge_node_id: str
    label: str
    type: str
    relation: str
    direction: str  # "outgoing" or "incoming"
    weight: float = 1.0


class GetNeighborsResult(BaseModel):
    center_node: str
    center_label: str
    edges: list[EdgeSummary]


class GetNeighborsTool:
    """Explore graph connections from a known node."""

    def __init__(self, deps: Deps) -> None:
        self._deps = deps

    @property
    def name(self) -> str:
        return "get_neighbors"

    @property
    def description(self) -> str:
        return (
            "Get the graph neighbors of a node — all entities connected by edges. "
            "Use relation_filter to see only specific relationship types. "
            "Common relations: extends, discusses, created_by, authored_by, "
            "critiques, influenced_by, member_of, part_of, wrote, supports, "
            "interprets, participates_in, contemporary_of, holds_position, "
            "evidenced_by, employs, developed_by, precedes. "
            "Without a filter, returns ALL neighbors sorted by relevance. "
            "Tip: call without relation_filter first to see available relations."
        )

    @property
    def parameters_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "node_id": {
                    "type": "string",
                    "description": "The node ID to explore from",
                },
                "relation_filter": {
                    "type": "string",
                    "description": "Filter by edge relation type (e.g. influenced_by, discusses, authored_by)",
                },
                "direction": {
                    "type": "string",
                    "enum": ["out", "in", "both"],
                    "default": "both",
                    "description": "Edge direction: outgoing, incoming, or both",
                },
                "limit": {
                    "type": "integer",
                    "default": 15,
                    "minimum": 1,
                    "maximum": 30,
                },
            },
            "required": ["node_id"],
        }

    async def execute(self, args: dict[str, Any]) -> GetNeighborsResult:
        node_id = args["node_id"]
        relation_filter = args.get("relation_filter")
        direction = args.get("direction", "both")
        limit = min(max(args.get("limit", 15), 1), 30)

        # The RAG synthesis path always warms `Deps.node_lookup` with the
        # full KG at startup (weighted traversal needs it). Lightweight
        # MCP/REST callers may not have paid that cost — in that case fall
        # back to a bounded Postgres k-hop CTE instead of returning an
        # empty result for every node. See `eleutheria_kg.services.db_traversal`.
        if self._deps.node_lookup:
            node_lookup = self._deps.node_lookup
            outgoing_edges = self._deps.outgoing_edges
            incoming_edges = self._deps.incoming_edges
        else:
            (
                node_lookup,
                outgoing_edges,
                incoming_edges,
            ) = await self._fetch_db_neighborhood(node_id)

        center = node_lookup.get(node_id, {})
        center_label = center.get("label", node_id)

        edges: list[tuple[EdgeSummary, float]] = []

        # Outgoing edges
        if direction in ("out", "both"):
            for edge in outgoing_edges.get(node_id, []):
                rel = edge.get("relation", "")
                if relation_filter and rel.lower() != relation_filter.lower():
                    continue
                target_id = edge.get("target", "")
                target = node_lookup.get(target_id, {})
                weight = edge.get("weight", 1.0)
                pr = self._deps.pagerank_scores.get(target_id, 0.0)
                sort_score = weight + pr * 10

                edges.append(
                    (
                        EdgeSummary(
                            edge_node_id=target_id,
                            label=target.get("label", target_id),
                            type=target.get("type", ""),
                            relation=rel,
                            direction="outgoing",
                            weight=weight,
                        ),
                        sort_score,
                    )
                )

        # Incoming edges
        if direction in ("in", "both"):
            for edge in incoming_edges.get(node_id, []):
                rel = edge.get("relation", "")
                if relation_filter and rel.lower() != relation_filter.lower():
                    continue
                source_id = edge.get("source", "")
                source = node_lookup.get(source_id, {})
                weight = edge.get("weight", 1.0)
                pr = self._deps.pagerank_scores.get(source_id, 0.0)
                sort_score = weight + pr * 10

                edges.append(
                    (
                        EdgeSummary(
                            edge_node_id=source_id,
                            label=source.get("label", source_id),
                            type=source.get("type", ""),
                            relation=rel,
                            direction="incoming",
                            weight=weight,
                        ),
                        sort_score,
                    )
                )

        # Sort by combined score (weight × pagerank), take top limit
        edges.sort(key=lambda x: x[1], reverse=True)
        result_edges = [e[0] for e in edges[:limit]]

        return GetNeighborsResult(
            center_node=node_id,
            center_label=center_label,
            edges=result_edges,
        )

    async def _fetch_db_neighborhood(
        self, node_id: str
    ) -> tuple[
        dict[str, dict[str, Any]],
        dict[str, list[dict[str, Any]]],
        dict[str, list[dict[str, Any]]],
    ]:
        """Bounded 1-hop lookup via the Postgres k-hop CTE, shaped like the
        in-memory `node_lookup`/`outgoing_edges`/`incoming_edges` indices so
        the rest of `execute` doesn't need to know which path served it.
        Returns empty structures (never raises) when the DB is unavailable
        or the query fails — the caller then reports zero neighbors, same
        as an unknown node in the in-memory path.
        """
        if self._deps.db is None:
            return {}, {}, {}
        try:
            from eleutheria_kg.services.db_traversal import fetch_neighborhood

            result = await fetch_neighborhood(
                self._deps.db, node_id, depth=_DB_FALLBACK_DEPTH
            )
        except Exception:
            logger.warning(
                "get_neighbors: DB fallback failed for %s", node_id, exc_info=True
            )
            return {}, {}, {}

        node_lookup = {n["id"]: n for n in result["nodes"]}
        outgoing: dict[str, list[dict[str, Any]]] = {}
        incoming: dict[str, list[dict[str, Any]]] = {}
        for edge in result["edges"]:
            src, tgt = edge.get("source"), edge.get("target")
            if src == node_id:
                outgoing.setdefault(src, []).append(edge)
            if tgt == node_id:
                incoming.setdefault(tgt, []).append(edge)
        return node_lookup, outgoing, incoming
