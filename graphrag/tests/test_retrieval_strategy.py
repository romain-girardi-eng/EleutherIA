# graphrag/tests/test_retrieval_strategy.py
from unittest.mock import AsyncMock, MagicMock

import pytest

from eleutheria_graphrag.services.retrieval_strategy import (
    SnapshotStrategy,
    SQLStrategy,
)


@pytest.mark.asyncio
async def test_sql_strategy_step1_passage_citations():
    """Step 1: finds seeds via kg_nodes label match + passage_citations."""
    mock_deps = MagicMock()
    mock_deps.db = AsyncMock()
    mock_deps.db.fetch = AsyncMock(
        side_effect=[
            # Tree-routed passage fetch (no work titles in plain "Stoic fate" query)
            # First call: label match
            [{"node_id": "concept_fate"}, {"node_id": "person_chrysippus"}],
            # Second call: passage_citations
            [
                {"passage_id": "p1", "kg_node_id": "concept_fate", "confidence": 0.9},
                {"passage_id": "p2", "kg_node_id": "concept_fate", "confidence": 0.8},
                {
                    "passage_id": "p3",
                    "kg_node_id": "person_chrysippus",
                    "confidence": 0.85,
                },
                {
                    "passage_id": "p4",
                    "kg_node_id": "person_chrysippus",
                    "confidence": 0.7,
                },
            ],
        ]
    )
    mock_deps.outgoing_edges = {
        "concept_fate": [{"target": "concept_determinism", "relation": "related_to"}]
    }
    mock_deps.incoming_edges = {}
    mock_deps.search = None
    mock_deps.tree_index = None  # No tree routing for this test

    strategy = SQLStrategy(min_bundles=4)
    seeds, anchors = await strategy.discover_seeds(
        queries=["Stoic fate"],
        deps=mock_deps,
        node_limit=100,
    )
    assert "concept_fate" in seeds
    assert "person_chrysippus" in seeds
    assert "concept_determinism" in seeds  # 1-hop expansion
    assert len(anchors) >= 2


@pytest.mark.asyncio
async def test_sql_strategy_escalates_to_hybrid_search():
    """When earlier steps find < min_bundles, escalates to HybridSearch."""
    mock_deps = MagicMock()
    mock_deps.db = AsyncMock()
    mock_deps.db.fetch = AsyncMock(
        side_effect=[
            # Step: label match
            [{"node_id": "concept_fate"}],
            # Step: passage citations
            [{"passage_id": "p1", "kg_node_id": "concept_fate", "confidence": 0.9}],
            # Lemma lookup makes no fetch here: without a LemmaExpander there
            # are no expanded terms, so the step (and its capability probe)
            # short-circuits before touching the DB.
        ]
    )
    mock_deps.outgoing_edges = {}
    mock_deps.incoming_edges = {}
    mock_deps.tree_index = None
    mock_search = AsyncMock()
    mock_search.hybrid_search = AsyncMock(
        return_value=[
            {"passage_id": "p2", "work_id": "w1", "text_content": "about fate..."},
            {"passage_id": "p3", "work_id": "w1", "text_content": "heimarmene..."},
            {
                "passage_id": "p4",
                "work_id": "w2",
                "text_content": "Chrysippus argues...",
            },
        ]
    )
    mock_deps.search = mock_search

    strategy = SQLStrategy(min_bundles=4)
    seeds, anchors = await strategy.discover_seeds(
        queries=["Stoic fate"],
        deps=mock_deps,
        node_limit=100,
    )
    mock_search.hybrid_search.assert_called()
    assert len(anchors) >= 1


@pytest.mark.asyncio
async def test_sql_strategy_returns_empty_gracefully():
    """SQLStrategy returns empty lists when nothing matches."""
    mock_deps = MagicMock()
    mock_deps.db = AsyncMock()
    mock_deps.db.fetch = AsyncMock(return_value=[])
    mock_deps.outgoing_edges = {}
    mock_deps.incoming_edges = {}
    mock_deps.search = None
    mock_deps.tree_index = None

    strategy = SQLStrategy(min_bundles=4)
    seeds, anchors = await strategy.discover_seeds(
        queries=["nonexistent topic xyz"],
        deps=mock_deps,
        node_limit=100,
    )
    assert seeds == []
    assert anchors == []


@pytest.mark.asyncio
async def test_sql_strategy_uses_lemma_expander_when_available():
    """When a LemmaExpander is wired, SQLStrategy queries oga_tokens.lemma."""
    mock_deps = MagicMock()
    mock_deps.db = AsyncMock()
    # Step order:
    #   1. label tier-1 match → empty
    #   2. description tier-2 match → empty
    #   3. oga_tokens.passage_id capability probe → column present
    #   4. lemma lookup → 2 hits
    mock_deps.db.fetch = AsyncMock(
        side_effect=[
            [],  # label match
            [],  # description match
            [{"?column?": 1}],  # information_schema probe
            [{"passage_id": "p_lemma_1"}, {"passage_id": "p_lemma_2"}],  # lemma lookup
        ]
    )
    mock_deps.outgoing_edges = {}
    mock_deps.incoming_edges = {}
    mock_deps.search = None
    mock_deps.tree_index = None

    expander = MagicMock()
    expander.expand = AsyncMock(return_value=["hekousi", "prohaires", "voluntary"])

    strategy = SQLStrategy(min_bundles=2, lemma_expander=expander)
    seeds, anchors = await strategy.discover_seeds(
        queries=["voluntary action"],
        deps=mock_deps,
        node_limit=100,
    )
    expander.expand.assert_awaited_once()
    assert "p_lemma_1" in anchors


@pytest.mark.asyncio
async def test_sql_strategy_tree_routing_picks_up_work_title():
    """When the query mentions a known author/work, tree routing resolves it."""
    mock_deps = MagicMock()
    mock_deps.db = AsyncMock()
    # Order of fetch calls when tree resolves a work:
    #   1) tree-routed passage fetch (returned passage IDs)
    #   2) label match
    #   3) citations
    mock_deps.db.fetch = AsyncMock(
        side_effect=[
            [{"passage_id": "tree_p_1"}, {"passage_id": "tree_p_2"}],
            [{"node_id": "person_aristotle"}],
            [
                {
                    "passage_id": "tree_p_3",
                    "kg_node_id": "person_aristotle",
                    "confidence": 0.9,
                }
            ],
        ]
    )
    mock_deps.outgoing_edges = {}
    mock_deps.incoming_edges = {}
    mock_deps.search = None

    tree = MagicMock()
    tree.resolve_work_ids = AsyncMock(return_value=["w-nicomachean-ethics"])
    mock_deps.tree_index = tree

    strategy = SQLStrategy(min_bundles=2)
    seeds, anchors = await strategy.discover_seeds(
        queries=["voluntary action in Aristotle Nicomachean Ethics"],
        deps=mock_deps,
        node_limit=100,
    )
    tree.resolve_work_ids.assert_awaited()
    assert "tree_p_1" in anchors


@pytest.mark.asyncio
async def test_snapshot_strategy_finds_seed_and_passage_anchor():
    mock_deps = MagicMock()
    mock_deps.node_lookup = {
        "concept_fate": {
            "id": "concept_fate",
            "label": "Fate",
            "type": "concept",
            "description": "Stoic heimarmene and providence",
            "metadata": {},
        },
        "passage_plut_fat_1": {
            "id": "passage_plut_fat_1",
            "label": "Plutarch, De fato 1",
            "type": "passage",
            "description": "Greek and translation about fate as energeia and ousia",
            "metadata": {
                "author": "Plutarch",
                "work_title": "De fato",
                "canonical_ref": "Plut. Fat. 1",
                "language": "grc",
            },
        },
    }
    mock_deps.outgoing_edges = {
        "concept_fate": [
            {
                "source": "concept_fate",
                "target": "passage_plut_fat_1",
                "relation": "evidenced_by",
                "weight": 0.9,
                "metadata": {"confidence": 0.9},
            }
        ]
    }
    mock_deps.incoming_edges = {}

    strategy = SnapshotStrategy(min_passages=1)
    seeds, anchors = await strategy.discover_seeds(
        queries=["Stoic fate"],
        deps=mock_deps,
        node_limit=10,
    )

    assert "concept_fate" in seeds
    assert "passage_plut_fat_1" in anchors
