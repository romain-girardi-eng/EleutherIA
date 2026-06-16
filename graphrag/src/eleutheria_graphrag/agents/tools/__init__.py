"""
Agent tools for the ReAct-based scholarly retrieval loop.

Each tool provides the LLM agent with a specific capability to explore
the knowledge graph and text corpus.
"""

from __future__ import annotations

import logging
from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel

from eleutheria_graphrag.agents.dependencies import Deps

logger = logging.getLogger(__name__)


@runtime_checkable
class BaseTool(Protocol):
    """Protocol for agent tools."""

    @property
    def name(self) -> str: ...

    @property
    def description(self) -> str: ...

    @property
    def parameters_schema(self) -> dict[str, Any]: ...

    async def execute(self, args: dict[str, Any]) -> BaseModel: ...


class ToolRegistry:
    """Registry of available tools for the agent loop."""

    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> BaseTool | None:
        return self._tools.get(name)

    def __contains__(self, name: str) -> bool:
        return name in self._tools

    def __getitem__(self, name: str) -> BaseTool:
        return self._tools[name]

    def tool_descriptions(self) -> list[dict[str, Any]]:
        """Return JSON-serializable tool descriptions for the LLM prompt."""
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters_schema,
            }
            for tool in self._tools.values()
        ]


def build_tool_registry(deps: Deps) -> ToolRegistry:
    """Create a fully populated tool registry from dependencies.

    The two Scholar-RAG (G6) relational tools — ``find_debates`` and
    ``build_controversy_frame`` — are registered ONLY when
    ``ELEUTHERIA_SCHOLAR_RAG`` is on, so the default pipeline's tool surface is
    unchanged.
    """
    from eleutheria_graphrag.agents.state import scholar_rag_enabled
    from eleutheria_graphrag.agents.tools.explore_subgraph import ExploreSubgraphTool
    from eleutheria_graphrag.agents.tools.get_neighbors import GetNeighborsTool
    from eleutheria_graphrag.agents.tools.get_node_detail import GetNodeDetailTool
    from eleutheria_graphrag.agents.tools.infer_transitive import (
        InferTransitiveFactsTool,
    )
    from eleutheria_graphrag.agents.tools.read_passages import ReadPassagesTool
    from eleutheria_graphrag.agents.tools.read_work_section import ReadWorkSectionTool
    from eleutheria_graphrag.agents.tools.search_nodes import SearchNodesTool
    from eleutheria_graphrag.agents.tools.search_passages import SearchPassagesTool

    registry = ToolRegistry()
    registry.register(SearchNodesTool(deps))
    registry.register(GetNeighborsTool(deps))
    registry.register(ReadPassagesTool(deps))
    registry.register(SearchPassagesTool(deps))
    registry.register(GetNodeDetailTool(deps))
    registry.register(ReadWorkSectionTool(deps))
    registry.register(ExploreSubgraphTool(deps))
    registry.register(InferTransitiveFactsTool(deps))

    if scholar_rag_enabled():
        from eleutheria_graphrag.agents.tools.build_controversy_frame import (
            BuildControversyFrameTool,
        )
        from eleutheria_graphrag.agents.tools.find_debates import FindDebatesTool

        registry.register(FindDebatesTool(deps))
        registry.register(BuildControversyFrameTool(deps))

    return registry
