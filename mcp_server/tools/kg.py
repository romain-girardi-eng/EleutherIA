"""MCP wrappers for KG inspection tools."""

from __future__ import annotations

from typing import Any, Literal

from eleutheria_graphrag.agents.tools.explore_subgraph import ExploreSubgraphTool
from eleutheria_graphrag.agents.tools.get_neighbors import GetNeighborsTool
from eleutheria_graphrag.agents.tools.get_node_detail import GetNodeDetailTool
from mcp.server.fastmcp import FastMCP

from mcp_server.cache import get_cache, session_id_from_context
from mcp_server.deps import get_deps

Direction = Literal["out", "in", "both"]


def register(mcp: FastMCP) -> None:
    """Register KG tools on the given FastMCP server."""
    cache = get_cache()

    @mcp.tool()
    async def get_node_detail(node_id: str) -> dict[str, Any]:
        """Get full metadata for a specific KG node.

        Returns the node's label, type, full description, metadata, and counts
        of neighbors and linked passages. Use after ``search_nodes`` to inspect
        a single node before deciding to traverse from it.

        Args:
            node_id: Knowledge graph node ID.

        Returns:
            ``{"node_id": ..., "label": ..., "type": ..., "description": ...,
            "period": ..., "school": ..., "metadata": {...},
            "neighbor_count": int, "passage_count": int}``.
        """
        args = {"node_id": node_id}
        sid = session_id_from_context(getattr(mcp, "request_context", None))
        cached = cache.get(sid, "get_node_detail", args)
        if cached is not None:
            return cached
        deps = await get_deps()
        tool = GetNodeDetailTool(deps)
        result = await tool.execute(args)
        result_dict = dict(result.model_dump())
        cache.put(sid, "get_node_detail", args, result_dict)
        return result_dict

    @mcp.tool()
    async def get_neighbors(
        node_id: str,
        relation_filter: str | None = None,
        direction: Direction = "both",
        limit: int = 15,
    ) -> dict[str, Any]:
        """List the immediate graph neighbors of a node.

        Common relations: ``extends``, ``discusses``, ``created_by``,
        ``authored_by``, ``critiques``, ``influenced_by``, ``member_of``,
        ``part_of``, ``wrote``, ``supports``, ``interprets``,
        ``participates_in``, ``contemporary_of``, ``holds_position``,
        ``evidenced_by``, ``employs``, ``developed_by``, ``precedes``.

        Tip: call once without ``relation_filter`` to discover what relations
        exist from this node, then re-query with a filter.

        Args:
            node_id: Knowledge graph node ID.
            relation_filter: Optional relation type filter.
            direction: ``"out"``, ``"in"``, or ``"both"`` (default).
            limit: 1–30 edges.

        Returns:
            ``{"center_node": ..., "center_label": ..., "edges": [...]}``.
        """
        args = {
            "node_id": node_id,
            "relation_filter": relation_filter,
            "direction": direction,
            "limit": limit,
        }
        sid = session_id_from_context(getattr(mcp, "request_context", None))
        cached = cache.get(sid, "get_neighbors", args)
        if cached is not None:
            return cached
        deps = await get_deps()
        tool = GetNeighborsTool(deps)
        result = await tool.execute(args)
        result_dict = dict(result.model_dump())
        cache.put(sid, "get_neighbors", args, result_dict)
        return result_dict

    @mcp.tool()
    async def explore_subgraph(seed_node_ids: list[str], top_k: int = 20) -> dict[str, Any]:
        """Run Personalized PageRank from seed nodes to discover the surrounding subgraph.

        HippoRAG-inspired single-step exploration — no LLM calls. Returns the
        top-K most relevant non-passage nodes surrounding the seeds, ranked by
        PPR score and annotated with BFS distance from the seed set.

        Args:
            seed_node_ids: 1–5 seed node IDs.
            top_k: 5–50 nodes to return.

        Returns:
            ``{"nodes": [...], "seed_count": int}``. Each node carries
            ``node_id``, ``label``, ``type``, ``ppr_score``,
            ``distance_from_seed``.
        """
        args = {"seed_node_ids": list(seed_node_ids), "top_k": top_k}
        sid = session_id_from_context(getattr(mcp, "request_context", None))
        cached = cache.get(sid, "explore_subgraph", args)
        if cached is not None:
            return cached
        deps = await get_deps()
        tool = ExploreSubgraphTool(deps)
        result = await tool.execute(args)
        result_dict = dict(result.model_dump())
        cache.put(sid, "explore_subgraph", args, result_dict)
        return result_dict
