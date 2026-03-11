"""Shared test fixtures for unit tests."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

from eleutheria_graphrag.agents.dependencies import Deps
from eleutheria_graphrag.agents.state import RAGState

# ---------------------------------------------------------------------------
# Core shared fixtures
# ---------------------------------------------------------------------------


def make_deps(
    *,
    llm_response: str = "test answer",
    search_results: list | None = None,
    node_lookup: dict | None = None,
    outgoing_edges: dict | None = None,
    incoming_edges: dict | None = None,
    db_fetch_results: list | None = None,
) -> Deps:
    """Create a mock Deps for testing."""
    llm = AsyncMock()
    llm.generate = AsyncMock(return_value=llm_response)

    qdrant = AsyncMock()
    qdrant.search_nodes = AsyncMock(
        return_value=search_results
        if search_results is not None
        else [{"id": "chrysippus", "score": 0.9}]
    )

    db = AsyncMock()
    db.fetch = AsyncMock(
        return_value=db_fetch_results if db_fetch_results is not None else []
    )

    _node_lookup = node_lookup or {
        "chrysippus": {
            "id": "chrysippus",
            "label": "Chrysippus",
            "type": "Person",
            "description": "Third head of the Stoic school",
            "period": "Hellenistic",
            "school": "Stoicism",
            "role": None,
        },
        "fate_concept": {
            "id": "fate_concept",
            "label": "Fate (heimarmenē)",
            "type": "Concept",
            "description": "Stoic concept of deterministic fate",
            "period": "Hellenistic",
            "school": "Stoicism",
            "role": None,
        },
    }

    return Deps(
        db=db,
        qdrant=qdrant,
        llm=llm,
        node_lookup=_node_lookup,
        outgoing_edges=outgoing_edges or {},
        incoming_edges=incoming_edges or {},
    )


def make_ctx(state: RAGState, deps: Deps) -> MagicMock:
    """Create a mock GraphRunContext."""
    ctx = MagicMock()
    ctx.state = state
    ctx.deps = deps
    return ctx
