"""Tests for the infer_transitive ReAct tool."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock

import pytest

from eleutheria_graphrag.agents.dependencies import Deps
from eleutheria_graphrag.agents.state import RAGState
from eleutheria_graphrag.agents.tools.infer_transitive import (
    InferTransitiveFactsTool,
)


def _make_deps() -> Deps:
    """Synthetic KG with a part_of chain and a wrote/authored_by pair.

    Topology:
        work_x  contains  book_b
        book_b  contains  chapter_c
        chapter_c  contains  passage_p

        passage_p  part_of  chapter_c
        chapter_c  part_of  book_b
        book_b     part_of  work_x

        person_plato  wrote  work_x
    """
    nodes: dict[str, dict[str, Any]] = {
        "work_x": {"id": "work_x", "label": "Work X", "type": "work"},
        "book_b": {"id": "book_b", "label": "Book B", "type": "work"},
        "chapter_c": {"id": "chapter_c", "label": "Chapter C", "type": "work"},
        "passage_p": {"id": "passage_p", "label": "Passage P", "type": "passage"},
        "person_plato": {
            "id": "person_plato",
            "label": "Plato",
            "type": "person",
        },
    }

    outgoing: dict[str, list[dict[str, Any]]] = {
        "work_x": [
            {"source": "work_x", "target": "book_b", "relation": "contains"},
        ],
        "book_b": [
            {"source": "book_b", "target": "chapter_c", "relation": "contains"},
            {"source": "book_b", "target": "work_x", "relation": "part_of"},
        ],
        "chapter_c": [
            {"source": "chapter_c", "target": "passage_p", "relation": "contains"},
            {"source": "chapter_c", "target": "book_b", "relation": "part_of"},
        ],
        "passage_p": [
            {"source": "passage_p", "target": "chapter_c", "relation": "part_of"},
        ],
        "person_plato": [
            {"source": "person_plato", "target": "work_x", "relation": "wrote"},
        ],
    }

    incoming: dict[str, list[dict[str, Any]]] = {
        "book_b": [
            {"source": "work_x", "target": "book_b", "relation": "contains"},
        ],
        "chapter_c": [
            {"source": "book_b", "target": "chapter_c", "relation": "contains"},
        ],
        "passage_p": [
            {"source": "chapter_c", "target": "passage_p", "relation": "contains"},
        ],
        "work_x": [
            {"source": "book_b", "target": "work_x", "relation": "part_of"},
            {"source": "person_plato", "target": "work_x", "relation": "wrote"},
        ],
    }

    return Deps(
        db=AsyncMock(),
        llm=AsyncMock(),
        node_lookup=nodes,
        outgoing_edges=outgoing,
        incoming_edges=incoming,
    )


@pytest.fixture
def deps() -> Deps:
    return _make_deps()


@pytest.mark.asyncio
async def test_descendants_via_contains(deps: Deps) -> None:
    tool = InferTransitiveFactsTool(deps)
    result = await tool.execute({"node_id": "work_x", "relation": "contains"})
    ids = {n.node_id for n in result.derived_nodes}
    assert {"book_b", "chapter_c", "passage_p"}.issubset(ids)
    assert result.is_transitive is True
    assert result.inverse_relation == "part_of"


@pytest.mark.asyncio
async def test_ancestors_via_part_of(deps: Deps) -> None:
    tool = InferTransitiveFactsTool(deps)
    result = await tool.execute({"node_id": "passage_p", "relation": "part_of"})
    ids = {n.node_id for n in result.derived_nodes}
    assert {"chapter_c", "book_b", "work_x"}.issubset(ids)


@pytest.mark.asyncio
async def test_inverse_wrote_to_authored_by(deps: Deps) -> None:
    """Asking for ``authored_by`` on work_x should surface the author via
    the declared inverse with ``wrote``."""
    tool = InferTransitiveFactsTool(deps)
    result = await tool.execute({"node_id": "work_x", "relation": "authored_by"})
    ids = {n.node_id for n in result.derived_nodes}
    assert "person_plato" in ids
    assert result.inverse_relation == "wrote"
    assert ["work_x", "authored_by", "person_plato"] in result.inferred_edges


@pytest.mark.asyncio
async def test_max_depth_caps_breadth(deps: Deps) -> None:
    tool = InferTransitiveFactsTool(deps)
    result = await tool.execute(
        {"node_id": "passage_p", "relation": "part_of", "max_depth": 1}
    )
    ids = {n.node_id for n in result.derived_nodes}
    assert "chapter_c" in ids
    assert "book_b" not in ids
    assert "work_x" not in ids


@pytest.mark.asyncio
async def test_unknown_node_returns_empty(deps: Deps) -> None:
    tool = InferTransitiveFactsTool(deps)
    result = await tool.execute({"node_id": "nonexistent_node", "relation": "contains"})
    assert result.derived_nodes == []
    assert result.start_node_id == "nonexistent_node"


@pytest.mark.asyncio
async def test_invalid_relation_raises_cleanly(deps: Deps) -> None:
    tool = InferTransitiveFactsTool(deps)
    with pytest.raises(ValueError, match="relation"):
        await tool.execute({"node_id": "work_x", "relation": ""})


@pytest.mark.asyncio
async def test_missing_node_id_raises_cleanly(deps: Deps) -> None:
    tool = InferTransitiveFactsTool(deps)
    with pytest.raises(ValueError, match="node_id"):
        await tool.execute({"node_id": "", "relation": "contains"})


@pytest.mark.asyncio
async def test_distance_increases_with_depth(deps: Deps) -> None:
    tool = InferTransitiveFactsTool(deps)
    result = await tool.execute({"node_id": "work_x", "relation": "contains"})
    by_id = {n.node_id: n for n in result.derived_nodes}
    # Direct child distance 1, descendants increase
    assert by_id["book_b"].distance == 1
    assert by_id["chapter_c"].distance == 2
    assert by_id["passage_p"].distance == 3


@pytest.mark.asyncio
async def test_non_transitive_relation_caps_at_one_hop(deps: Deps) -> None:
    """``wrote`` is not in the transitive set; only direct neighbors return."""
    tool = InferTransitiveFactsTool(deps)
    result = await tool.execute(
        {"node_id": "person_plato", "relation": "wrote", "max_depth": 5}
    )
    ids = {n.node_id for n in result.derived_nodes}
    assert "work_x" in ids
    # Descendants of work_x must NOT appear — chaining wrote is unsound.
    assert "book_b" not in ids
    assert result.is_transitive is False
    assert result.max_depth == 1


@pytest.mark.asyncio
async def test_inferred_edges_are_recorded_on_state(deps: Deps) -> None:
    state = RAGState(question="who authored work x")
    deps.state = state
    tool = InferTransitiveFactsTool(deps)

    await tool.execute({"node_id": "work_x", "relation": "authored_by"})

    assert ("work_x", "authored_by", "person_plato") in state.inferred_edges
