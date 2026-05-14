"""Unit tests for the MCP server.

These tests stub the global ``DepsContainer`` so no real Postgres or
Qdrant instance is required. They cover:

  * every expected tool is registered on the FastMCP server;
  * each tool call returns a plain-dict, JSON-serializable shape;
  * the HTTP transport refuses unauthenticated traffic.
"""

from __future__ import annotations

import importlib
import json
from collections.abc import Iterator
from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock

import pytest
from eleutheria_graphrag.agents.dependencies import Deps

from mcp_server import deps as deps_module
from mcp_server.server import build_server

EXPECTED_TOOLS = {
    "search_passages",
    "search_nodes",
    "read_passages",
    "read_work_section",
    "get_node_detail",
    "get_neighbors",
    "explore_subgraph",
}


def _fake_node_lookup() -> dict[str, dict[str, Any]]:
    return {
        "person_aristotle": {
            "id": "person_aristotle",
            "label": "Aristotle",
            "type": "person",
            "description": "Greek philosopher (384–322 BCE)",
            "period": "Classical",
            "school": "Peripatetic",
        },
        "concept_prohairesis": {
            "id": "concept_prohairesis",
            "label": "prohairesis",
            "type": "concept",
            "description": "Deliberate choice",
            "period": "Classical",
        },
        "work_ne": {
            "id": "work_ne",
            "label": "Nicomachean Ethics",
            "type": "work",
            "description": "Aristotle's ethical treatise",
        },
    }


def _fake_edges() -> tuple[dict[str, list[dict[str, Any]]], dict[str, list[dict[str, Any]]]]:
    out: dict[str, list[dict[str, Any]]] = {
        "person_aristotle": [
            {
                "source": "person_aristotle",
                "target": "work_ne",
                "relation": "wrote",
                "weight": 1.0,
            },
            {
                "source": "person_aristotle",
                "target": "concept_prohairesis",
                "relation": "developed_by",
                "weight": 1.0,
            },
        ]
    }
    incoming: dict[str, list[dict[str, Any]]] = {
        "work_ne": [out["person_aristotle"][0]],
        "concept_prohairesis": [out["person_aristotle"][1]],
    }
    return out, incoming


def _build_fake_deps() -> Deps:
    out, incoming = _fake_edges()
    db = MagicMock()
    db.is_connected = MagicMock(return_value=False)
    db.fetch = AsyncMock(return_value=[])
    db.fetchval = AsyncMock(return_value=0)
    db.close = AsyncMock()

    return Deps(
        db=db,
        llm=MagicMock(),
        analytics=None,
        search=None,
        tree_index=None,
        kg_data={"nodes": list(_fake_node_lookup().values())},
        node_lookup=_fake_node_lookup(),
        outgoing_edges=out,
        incoming_edges=incoming,
        pagerank_scores={"person_aristotle": 0.5},
    )


class _StubContainer:
    def __init__(self, deps: Deps) -> None:
        self._deps = deps

    async def get(self) -> Deps:
        return self._deps

    async def shutdown(self) -> None:
        return None


@pytest.fixture(autouse=True)
def _stub_deps() -> Iterator[None]:
    fake = _build_fake_deps()
    deps_module.override_container(cast(deps_module.DepsContainer, _StubContainer(fake)))
    yield
    deps_module.reset_container()


def _extract_payload(result: Any) -> dict[str, Any]:
    """FastMCP returns ``(content_seq, structured_dict | None)``; unwrap to dict."""
    structured = result[1] if isinstance(result, tuple) and len(result) >= 2 else result
    assert isinstance(structured, dict)
    payload = structured.get("result", structured)
    return cast(dict[str, Any], payload)


@pytest.mark.asyncio
async def test_all_expected_tools_registered() -> None:
    mcp = build_server()
    tools = await mcp.list_tools()
    names = {t.name for t in tools}
    assert names >= EXPECTED_TOOLS, f"Missing: {EXPECTED_TOOLS - names}"


@pytest.mark.asyncio
async def test_search_nodes_returns_plain_dict() -> None:
    mcp = build_server()
    payload = _extract_payload(await mcp.call_tool("search_nodes", {"query": "Aristotle"}))
    assert "nodes" in payload
    assert any(n["label"] == "Aristotle" for n in payload["nodes"])
    json.dumps(payload)  # must be JSON-serializable


@pytest.mark.asyncio
async def test_get_node_detail_returns_full_description() -> None:
    mcp = build_server()
    payload = _extract_payload(
        await mcp.call_tool("get_node_detail", {"node_id": "person_aristotle"})
    )
    assert payload["label"] == "Aristotle"
    assert payload["neighbor_count"] == 2
    assert payload["passage_count"] == 0


@pytest.mark.asyncio
async def test_get_neighbors_returns_two_edges() -> None:
    mcp = build_server()
    payload = _extract_payload(
        await mcp.call_tool("get_neighbors", {"node_id": "person_aristotle"})
    )
    assert payload["center_node"] == "person_aristotle"
    assert len(payload["edges"]) == 2


@pytest.mark.asyncio
async def test_explore_subgraph_runs_without_llm() -> None:
    mcp = build_server()
    payload = _extract_payload(
        await mcp.call_tool("explore_subgraph", {"seed_node_ids": ["person_aristotle"], "top_k": 5})
    )
    assert payload["seed_count"] == 1
    assert isinstance(payload["nodes"], list)


@pytest.mark.asyncio
async def test_search_passages_falls_back_to_snapshot() -> None:
    mcp = build_server()
    payload = _extract_payload(
        await mcp.call_tool("search_passages", {"query": "anything", "limit": 3})
    )
    assert "passages" in payload
    assert payload["total_found"] >= 0


@pytest.mark.asyncio
async def test_read_passages_handles_missing_node() -> None:
    mcp = build_server()
    payload = _extract_payload(await mcp.call_tool("read_passages", {"node_id": "nonexistent"}))
    assert payload["node_id"] == "nonexistent"
    assert payload["passages"] == []


@pytest.mark.asyncio
async def test_read_work_section_no_tree_index() -> None:
    mcp = build_server()
    payload = _extract_payload(await mcp.call_tool("read_work_section", {"work_id": "work_ne"}))
    assert payload["work_id"] == "work_ne"
    assert payload["sections"] == []


def test_http_transport_refuses_without_token(monkeypatch: pytest.MonkeyPatch) -> None:
    """The HTTP transport must exit with code 2 if MCP_API_TOKEN is unset."""
    monkeypatch.delenv("MCP_API_TOKEN", raising=False)
    http = importlib.import_module("mcp_server.transports.http")
    monkeypatch.setattr("sys.argv", ["http"])
    with pytest.raises(SystemExit) as exc:
        http.main()
    assert exc.value.code == 2


def test_http_transport_builds_with_token(monkeypatch: pytest.MonkeyPatch) -> None:
    """Setting the token + a fake uvicorn lets main() build the app cleanly."""
    monkeypatch.setenv("MCP_API_TOKEN", "test-token")
    http = importlib.import_module("mcp_server.transports.http")

    started: dict[str, Any] = {}

    def _fake_run(app: Any, **kwargs: Any) -> None:
        started["app"] = app
        started["kwargs"] = kwargs

    import uvicorn

    monkeypatch.setattr(uvicorn, "run", _fake_run)
    monkeypatch.setattr("sys.argv", ["http", "--host", "127.0.0.1", "--port", "9999"])

    http.main()
    assert "app" in started
    assert started["kwargs"]["host"] == "127.0.0.1"
    assert started["kwargs"]["port"] == 9999
