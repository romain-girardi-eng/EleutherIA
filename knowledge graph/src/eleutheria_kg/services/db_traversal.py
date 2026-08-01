"""Postgres-side bounded k-hop graph traversal over ``kg_edges``.

Lightweight DB-backed alternative to the in-memory NetworkX/PPR traversal in
``KGAnalytics`` (see ``analytics.py``) and to the fully-warm ``Deps`` graph
indices used by the agentic RAG synthesis path. Both of those require the
*entire* KG (currently ~20k nodes / ~57k edges) to be loaded into process
memory before a single node's neighbors can be listed.

This module answers the same "what's near this node" question with one
bounded ``WITH RECURSIVE`` CTE over ``free_will.kg_edges``, which is already
indexed on ``source_id``/``target_id`` (see
``database/schema/schema.sql``). It is meant as a fallback path for the
lightweight REST (``/kg/nodes/{id}/neighbors``) and MCP (``get_neighbors``,
``explore_subgraph``) tools when the in-memory graph is not warm — the
in-memory ``WeightedTraversal``/PPR path used for RAG synthesis is
untouched.

Safety: depth is hard-clamped to ``MAX_DEPTH`` and result rows to
``HARD_ROW_LIMIT`` regardless of caller input, cycles are broken via a
``path`` array carried through the recursion, and every identifier is a
bound parameter (``$1``, ``$2``, ...) — never string-interpolated.
"""

from __future__ import annotations

from typing import Any, Protocol

MAX_DEPTH = 3
DEFAULT_DEPTH = 1
HARD_ROW_LIMIT = 500


class QueryableDB(Protocol):
    """Minimal shape required from the DB service (see ``DatabaseService``)."""

    async def fetch(self, query: str, *args: Any) -> list[dict[str, Any] | Any]: ...


# Walks both outgoing and incoming edges from the start node, up to `$2`
# hops. `path` accumulates visited node ids so cycles terminate recursion
# instead of looping; the final SELECT collapses to the shortest hop per
# node and caps the row count at `$3`.
_KHOP_SQL = """
WITH RECURSIVE khop(node_id, hop, path) AS (
    SELECT $1::text, 0, ARRAY[$1::text]
    UNION ALL
    SELECT
        nxt.neighbor_id,
        khop.hop + 1,
        khop.path || nxt.neighbor_id
    FROM khop
    CROSS JOIN LATERAL (
        SELECT e.target_id AS neighbor_id
        FROM free_will.kg_edges e
        WHERE e.source_id = khop.node_id
        UNION ALL
        SELECT e.source_id AS neighbor_id
        FROM free_will.kg_edges e
        WHERE e.target_id = khop.node_id
    ) nxt
    WHERE khop.hop < $2::int
      AND NOT (nxt.neighbor_id = ANY(khop.path))
)
SELECT node_id, MIN(hop) AS hop
FROM khop
WHERE hop > 0
GROUP BY node_id
ORDER BY hop, node_id
LIMIT $3::int
"""

_NODE_COLUMNS = "id, label, type, description, period, school, metadata"


def _clamp(depth: int, limit: int) -> tuple[int, int]:
    depth = max(1, min(int(depth), MAX_DEPTH))
    limit = max(1, min(int(limit), HARD_ROW_LIMIT))
    return depth, limit


async def fetch_khop_neighbor_ids(
    db: QueryableDB,
    node_id: str,
    depth: int = DEFAULT_DEPTH,
    limit: int = HARD_ROW_LIMIT,
) -> list[dict[str, Any]]:
    """Bounded-depth neighbor node ids via a single recursive CTE.

    Returns ``[{"node_id": ..., "hop": ...}, ...]`` (``hop >= 1``, the start
    node itself excluded), ordered by hop distance then node id. ``depth``
    and ``limit`` are clamped server-side before the query runs — callers
    cannot request an unbounded traversal.
    """
    depth, limit = _clamp(depth, limit)
    rows = await db.fetch(_KHOP_SQL, node_id, depth, limit)
    return [dict(row) for row in rows]


async def fetch_neighborhood(
    db: QueryableDB,
    node_id: str,
    depth: int = DEFAULT_DEPTH,
    limit: int = HARD_ROW_LIMIT,
) -> dict[str, Any]:
    """DB-backed neighborhood lookup shaped like ``KGAnalytics.get_node_neighbors``.

    Returns ``{"nodes": [...], "edges": [...]}`` where ``nodes`` includes the
    start node (when it exists) plus every node reached within ``depth``
    hops, and ``edges`` is every ``kg_edges`` row whose source *and* target
    both fall inside that neighborhood. Returns ``{"nodes": [], "edges": []}``
    when the start node does not exist.
    """
    depth, limit = _clamp(depth, limit)
    hop_rows = await fetch_khop_neighbor_ids(db, node_id, depth=depth, limit=limit)
    neighbor_ids = [row["node_id"] for row in hop_rows]
    all_ids = [node_id, *neighbor_ids]

    node_rows = await db.fetch(
        f"SELECT {_NODE_COLUMNS} FROM free_will.kg_nodes WHERE id = ANY($1::text[])",
        all_ids,
    )
    nodes = [dict(row) for row in node_rows]
    if not any(n.get("id") == node_id for n in nodes):
        # Start node itself does not exist — nothing to report.
        return {"nodes": [], "edges": []}

    if not neighbor_ids:
        return {"nodes": nodes, "edges": []}

    edge_rows = await db.fetch(
        """
        SELECT source, target, relation, weight, metadata
        FROM free_will.kg_edges
        WHERE source = ANY($1::text[]) AND target = ANY($1::text[])
        """,
        all_ids,
    )
    return {"nodes": nodes, "edges": [dict(row) for row in edge_rows]}
