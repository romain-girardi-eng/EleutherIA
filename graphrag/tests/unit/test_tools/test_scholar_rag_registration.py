"""Scholar-RAG M1 — the relational tools register ONLY behind the flag.

Guards the hard rule that the new debate-first path is additive and gated by
``ELEUTHERIA_SCHOLAR_RAG`` (default OFF): with the flag off the default tool
surface is byte-for-byte unchanged; with it on, ``find_debates`` /
``build_controversy_frame`` appear and produce valid OpenAI function schemas.
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from eleutheria_graphrag.agents.dependencies import Deps
from eleutheria_graphrag.agents.tool_schemas import build_tool_function_schemas
from eleutheria_graphrag.agents.tools import build_tool_registry

_SCHOLAR_TOOLS = {"find_debates", "build_controversy_frame"}


def _deps() -> Deps:
    return Deps(db=AsyncMock(), llm=AsyncMock())


def test_flag_off_excludes_scholar_tools(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ELEUTHERIA_SCHOLAR_RAG", raising=False)
    registry = build_tool_registry(_deps())
    for name in _SCHOLAR_TOOLS:
        assert name not in registry
    # The default 8 tools are untouched.
    assert "search_nodes" in registry
    assert "get_neighbors" in registry


def test_flag_on_registers_scholar_tools(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ELEUTHERIA_SCHOLAR_RAG", "true")
    registry = build_tool_registry(_deps())
    for name in _SCHOLAR_TOOLS:
        assert name in registry


def test_scholar_tools_produce_valid_function_schemas(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ELEUTHERIA_SCHOLAR_RAG", "1")
    registry = build_tool_registry(_deps())
    schemas = build_tool_function_schemas(registry)
    by_name = {s["function"]["name"]: s for s in schemas}
    for name in _SCHOLAR_TOOLS:
        assert name in by_name
        params = by_name[name]["function"]["parameters"]
        assert params["type"] == "object"
        assert "properties" in params

    fd = by_name["find_debates"]["function"]["parameters"]
    assert "topic" in fd["properties"]
    bcf = by_name["build_controversy_frame"]["function"]["parameters"]
    assert "seed_id" in bcf["properties"]
