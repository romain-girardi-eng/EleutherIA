"""Tests for the Postgres-side bounded k-hop traversal (db_traversal.py)."""

from __future__ import annotations

from typing import Any

import pytest

from eleutheria_kg.services.db_traversal import (
    HARD_ROW_LIMIT,
    MAX_DEPTH,
    fetch_khop_neighbor_ids,
    fetch_neighborhood,
)


class FakeDB:
    """Records bound params and returns canned rows per query prefix."""

    def __init__(self, responses: dict[str, list[dict[str, Any]]]) -> None:
        self._responses = responses
        self.calls: list[tuple[str, tuple[Any, ...]]] = []

    async def fetch(self, query: str, *args: Any) -> list[dict[str, Any]]:
        self.calls.append((query, args))
        for prefix, rows in self._responses.items():
            if prefix in query:
                return rows
        return []


@pytest.fixture
def db() -> FakeDB:
    return FakeDB(
        {
            "WITH RECURSIVE khop": [
                {"node_id": "concept_fate", "hop": 1},
                {"node_id": "person_chrysippus", "hop": 2},
            ],
            "FROM free_will.kg_nodes": [
                {
                    "id": "person_origen",
                    "label": "Origen",
                    "type": "person",
                    "description": None,
                    "period": "Roman Imperial",
                    "school": None,
                    "metadata": {},
                },
                {
                    "id": "concept_fate",
                    "label": "Fate",
                    "type": "concept",
                    "description": None,
                    "period": "Hellenistic",
                    "school": None,
                    "metadata": {},
                },
                {
                    "id": "person_chrysippus",
                    "label": "Chrysippus",
                    "type": "person",
                    "description": None,
                    "period": "Hellenistic",
                    "school": None,
                    "metadata": {},
                },
            ],
            "FROM free_will.kg_edges": [
                {
                    "source": "person_origen",
                    "target": "concept_fate",
                    "relation": "discusses",
                    "weight": 1.0,
                    "metadata": {},
                },
            ],
        }
    )


async def test_khop_neighbor_ids_clamps_depth_and_limit(db: FakeDB) -> None:
    await fetch_khop_neighbor_ids(db, "person_origen", depth=99, limit=999999)
    query, args = db.calls[0]
    assert "WITH RECURSIVE khop" in query
    node_id, depth, limit = args
    assert node_id == "person_origen"
    assert depth == MAX_DEPTH  # clamped down from 99
    assert limit == HARD_ROW_LIMIT  # clamped down from 999999


async def test_khop_neighbor_ids_shape(db: FakeDB) -> None:
    rows = await fetch_khop_neighbor_ids(db, "person_origen")
    assert rows == [
        {"node_id": "concept_fate", "hop": 1},
        {"node_id": "person_chrysippus", "hop": 2},
    ]


async def test_fetch_neighborhood_includes_start_and_neighbors(db: FakeDB) -> None:
    result = await fetch_neighborhood(db, "person_origen", depth=2)
    node_ids = {n["id"] for n in result["nodes"]}
    assert node_ids == {"person_origen", "concept_fate", "person_chrysippus"}
    assert result["edges"] == [
        {
            "source": "person_origen",
            "target": "concept_fate",
            "relation": "discusses",
            "weight": 1.0,
            "metadata": {},
        }
    ]


async def test_fetch_neighborhood_missing_start_node_returns_empty() -> None:
    empty_db = FakeDB({"WITH RECURSIVE khop": [], "FROM free_will.kg_nodes": []})
    result = await fetch_neighborhood(empty_db, "nonexistent")
    assert result == {"nodes": [], "edges": []}


async def test_fetch_neighborhood_isolated_start_node_skips_edge_query() -> None:
    """A node with zero neighbors must not trigger a wasted edges query."""
    isolated_db = FakeDB(
        {
            "WITH RECURSIVE khop": [],
            "FROM free_will.kg_nodes": [
                {
                    "id": "person_isolated",
                    "label": "Isolated",
                    "type": "person",
                    "description": None,
                    "period": None,
                    "school": None,
                    "metadata": {},
                }
            ],
        }
    )
    result = await fetch_neighborhood(isolated_db, "person_isolated")
    assert result["nodes"] == [
        {
            "id": "person_isolated",
            "label": "Isolated",
            "type": "person",
            "description": None,
            "period": None,
            "school": None,
            "metadata": {},
        }
    ]
    assert result["edges"] == []
    # Only the khop CTE + node lookup ran — no separate edges query for a
    # node with zero neighbors.
    assert len(isolated_db.calls) == 2
