"""MCP wrappers for read tools (passages, work sections)."""

from __future__ import annotations

from typing import Any

from eleutheria_graphrag.agents.tools.read_passages import ReadPassagesTool
from eleutheria_graphrag.agents.tools.read_work_section import ReadWorkSectionTool
from mcp.server.fastmcp import FastMCP

from mcp_server.deps import get_deps


def register(mcp: FastMCP) -> None:
    """Register read tools on the given FastMCP server."""

    @mcp.tool()
    async def read_passages(node_id: str, limit: int = 5) -> dict[str, Any]:
        """Load the ancient text passages linked to a KG node.

        Looks up ``passage_citations`` first; falls back to (a) passages of a
        work node, (b) works authored by a person node, then (c) author-name
        match. Returns passage text alongside English translation when an
        ``_en`` mirror node exists.

        Args:
            node_id: Knowledge graph node ID.
            limit: 1–10 passages.

        Returns:
            ``{"node_id": ..., "node_label": ..., "passages": [...]}``. Each
            passage carries ``passage_id``, ``work_title``, ``author``,
            ``canonical_ref``, ``language``, ``text_content``, optional
            ``translation``, and ``confidence``.
        """
        deps = await get_deps()
        tool = ReadPassagesTool(deps)
        result = await tool.execute({"node_id": node_id, "limit": limit})
        return dict(result.model_dump())

    @mcp.tool()
    async def read_work_section(work_id: str, section_path: str | None = None) -> dict[str, Any]:
        """Browse the hierarchical table of contents of an ancient work.

        Call with just ``work_id`` for the top-level sections; pass a
        slash-separated ``section_path`` (e.g. ``"Book III/Chapter 1"``) to
        descend.

        Args:
            work_id: Work ID (UUID, ``canonical_id``, or ``kg_work_id``).
            section_path: Optional hierarchical path.

        Returns:
            ``{"work_id": ..., "work_title": ..., "author": ..., "sections": [...]}``.
            Each section has ``node_id``, ``title``, ``path``, ``summary``,
            ``passage_count``, ``has_subsections``, and up to 5 ``concept_tags``.
        """
        deps = await get_deps()
        tool = ReadWorkSectionTool(deps)
        result = await tool.execute({"work_id": work_id, "section_path": section_path})
        return dict(result.model_dump())
