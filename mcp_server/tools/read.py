"""MCP wrappers for read tools (passages, work sections)."""

from __future__ import annotations

from typing import Any

from eleutheria_graphrag.agents.tools.read_passages import ReadPassagesTool
from eleutheria_graphrag.agents.tools.read_work_section import ReadWorkSectionTool
from mcp.server.fastmcp import FastMCP

from mcp_server.cache import get_cache, session_id_from_context
from mcp_server.deps import get_deps


def register(mcp: FastMCP) -> None:
    """Register read tools on the given FastMCP server."""
    cache = get_cache()

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
            ``translation`` with its provenance (``translation_type``, e.g.
            ``"machine"``, and ``translation_ai_generated``), and
            ``confidence``. When ``translation_ai_generated`` is true or
            provenance is unknown, do NOT attribute the translation to a
            named scholar.
        """
        args = {"node_id": node_id, "limit": limit}
        sid = session_id_from_context(getattr(mcp, "request_context", None))
        cached = cache.get(sid, "read_passages", args)
        if cached is not None:
            return cached
        deps = await get_deps()
        tool = ReadPassagesTool(deps)
        result = await tool.execute(args)
        result_dict = dict(result.model_dump())
        cache.put(sid, "read_passages", args, result_dict)
        return result_dict

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
        args = {"work_id": work_id, "section_path": section_path}
        sid = session_id_from_context(getattr(mcp, "request_context", None))
        cached = cache.get(sid, "read_work_section", args)
        if cached is not None:
            return cached
        deps = await get_deps()
        tool = ReadWorkSectionTool(deps)
        result = await tool.execute(args)
        result_dict = dict(result.model_dump())
        cache.put(sid, "read_work_section", args, result_dict)
        return result_dict
