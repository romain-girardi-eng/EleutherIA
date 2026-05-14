"""Tests for OpenAI-style tool schema generation."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock

import pytest
from pydantic import BaseModel

from eleutheria_graphrag.agents.dependencies import Deps
from eleutheria_graphrag.agents.tool_schemas import (
    _normalize_schema,
    build_tool_function_schemas,
)
from eleutheria_graphrag.agents.tools import ToolRegistry


class _FakeResult(BaseModel):
    ok: bool = True


class _FakeTool:
    def __init__(self, name: str, props: dict[str, Any]) -> None:
        self._name = name
        self._props = props

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return f"fake tool {self._name}"

    @property
    def parameters_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": self._props,
            "required": list(self._props.keys()),
        }

    async def execute(self, args: dict[str, Any]) -> _FakeResult:
        _ = args
        return _FakeResult()


def test_normalize_schema_adds_type() -> None:
    out = _normalize_schema({"properties": {"x": {"type": "string"}}})
    assert out["type"] == "object"


def test_normalize_schema_preserves_existing() -> None:
    schema: dict[str, Any] = {
        "type": "object",
        "properties": {"q": {"type": "string"}},
        "required": ["q"],
    }
    out = _normalize_schema(schema)
    assert out == schema


def test_build_schemas_envelope() -> None:
    registry = ToolRegistry()
    registry.register(_FakeTool("search_nodes", {"q": {"type": "string"}}))
    registry.register(_FakeTool("read_passages", {"node_id": {"type": "string"}}))

    schemas = build_tool_function_schemas(registry)
    assert len(schemas) == 2
    for s in schemas:
        assert s["type"] == "function"
        assert "name" in s["function"]
        assert "parameters" in s["function"]
        assert s["function"]["parameters"]["type"] == "object"


def test_build_schemas_for_real_registry() -> None:
    """All 7 production tools should produce valid schemas."""
    db = AsyncMock()
    llm = AsyncMock()
    deps = Deps(
        db=db,
        llm=llm,
        node_lookup={},
        outgoing_edges={},
        incoming_edges={},
        pagerank_scores={},
    )
    from eleutheria_graphrag.agents.tools import build_tool_registry

    registry = build_tool_registry(deps)
    schemas = build_tool_function_schemas(registry)

    names = {s["function"]["name"] for s in schemas}
    expected = {
        "search_passages",
        "search_nodes",
        "read_passages",
        "get_node_detail",
        "explore_subgraph",
        "read_work_section",
        "get_neighbors",
    }
    # All 7 required tools must be present; ``infer_transitive_facts`` may
    # also be registered but is allowed.
    missing = expected - names
    assert not missing, f"missing tool schemas: {missing}"


@pytest.mark.parametrize(
    "schema",
    [
        {
            "type": "function",
            "function": {
                "name": "x",
                "description": "",
                "parameters": {"type": "object", "properties": {}},
            },
        },
    ],
)
def test_schema_shape_is_openai_compatible(schema: dict[str, Any]) -> None:
    """Sanity: top-level keys match Fireworks/OpenAI expectations."""
    assert schema["type"] == "function"
    assert set(schema["function"].keys()) >= {"name", "description", "parameters"}
