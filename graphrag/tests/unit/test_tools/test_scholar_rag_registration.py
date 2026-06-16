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


def test_scholar_tools_hidden_from_llm_function_schemas(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The relational tools are deterministically driven by the pipeline, so
    they are registered (orchestration fetches them) but HIDDEN from the
    LLM-facing function schemas — otherwise the ReAct agent double-retrieves.
    """
    monkeypatch.setenv("ELEUTHERIA_SCHOLAR_RAG", "1")
    registry = build_tool_registry(_deps())
    # Registered (so _assemble_controversy_map can fetch them)…
    for name in _SCHOLAR_TOOLS:
        assert registry.get(name) is not None
    # …but excluded from the schemas the LLM sees (no double-retrieval).
    schemas = build_tool_function_schemas(registry)
    by_name = {s["function"]["name"]: s for s in schemas}
    for name in _SCHOLAR_TOOLS:
        assert name not in by_name
    # The retrieval tools the agent SHOULD drive are still exposed.
    assert "search_nodes" in by_name
    assert "search_passages" in by_name

    # The tools' own JSON schemas remain valid (they are still callable via
    # the deterministic path); validate them directly off the registry.
    fd = registry.get("find_debates").parameters_schema  # type: ignore[union-attr]
    assert "topic" in fd["properties"]
    bcf = registry.get("build_controversy_frame").parameters_schema  # type: ignore[union-attr]
    assert "seed_id" in bcf["properties"]


def test_scholar_tools_excluded_from_tool_descriptions(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The legacy text-mode prompt surface (``tool_descriptions``) also hides
    the deterministically-driven relational tools."""
    monkeypatch.setenv("ELEUTHERIA_SCHOLAR_RAG", "1")
    registry = build_tool_registry(_deps())
    described = {d["name"] for d in registry.tool_descriptions()}
    for name in _SCHOLAR_TOOLS:
        assert name not in described
    assert "search_nodes" in described
