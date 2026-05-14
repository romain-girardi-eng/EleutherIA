"""MCP wrappers for search tools (passages + KG nodes)."""

from __future__ import annotations

from typing import Any, Literal

from eleutheria_graphrag.agents.tools.search_nodes import SearchNodesTool
from eleutheria_graphrag.agents.tools.search_passages import SearchPassagesTool
from mcp.server.fastmcp import FastMCP

from mcp_server.deps import get_deps

NodeTypeFilter = Literal[
    "person", "concept", "argument", "work", "school", "passage", "debate", "group"
]


def register(mcp: FastMCP) -> None:
    """Register search tools on the given FastMCP server."""

    @mcp.tool()
    async def search_passages(
        query: str,
        work_filter: str | None = None,
        limit: int = 5,
    ) -> dict[str, Any]:
        """Search the ancient text corpus by keyword.

        Combines PostgreSQL full-text search + lemmatic search (for Greek and
        Latin lemmas). Use this to find specific textual evidence without going
        through the knowledge graph, or to narrow a search to one work.

        Args:
            query: Search text. Supports polytonic Greek and Latin.
            work_filter: Optional ``work_id`` / ``kg_work_id`` / ``canonical_id``
                to restrict the search to a single work.
            limit: 1–10 passages to return.

        Returns:
            ``{"passages": [...], "total_found": int}``. Each passage carries
            ``passage_id``, ``work_title``, ``author``, ``canonical_ref``,
            ``language``, ``text_content`` (up to 800 chars), and ``score``.
        """
        deps = await get_deps()
        tool = SearchPassagesTool(deps)
        result = await tool.execute({"query": query, "work_filter": work_filter, "limit": limit})
        return dict(result.model_dump())

    @mcp.tool()
    async def search_nodes(
        query: str,
        type_filter: NodeTypeFilter | None = None,
        period_filter: str | None = None,
        limit: int = 10,
    ) -> dict[str, Any]:
        """Search the knowledge graph for nodes by label or description.

        Returns persons, concepts, arguments, works, schools, debates, or
        groups ranked by a label-match score blended with PageRank centrality.

        Args:
            query: Search text. Matches label first, then description.
            type_filter: Restrict to a single node type.
            period_filter: Historical period filter (e.g. ``"Hellenistic"``).
            limit: 1–30 nodes to return.

        Returns:
            ``{"nodes": [...], "total_found": int}``. Each node carries
            ``node_id``, ``label``, ``type``, truncated ``description``,
            ``period``, ``school``, and ``score``.
        """
        deps = await get_deps()
        tool = SearchNodesTool(deps)
        result = await tool.execute(
            {
                "query": query,
                "type_filter": type_filter,
                "period_filter": period_filter,
                "limit": limit,
            }
        )
        return dict(result.model_dump())
