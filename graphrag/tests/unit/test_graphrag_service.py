"""Tests for GraphRAGService wrapper."""

import warnings
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from eleutheria_graphrag.services.graphrag_service import GraphRAGService
from tests.publication_fixtures import verified_result


class TestGraphRAGServiceInit:
    """Tests for service initialization."""

    def test_init_defaults(self):
        svc = GraphRAGService(db_service=MagicMock())
        assert svc._kg_loaded is False
        assert svc._agent is None
        assert svc.kg_data is None

    def test_init_with_optional_services(self):
        svc = GraphRAGService(
            db_service=MagicMock(),
            reranker=MagicMock(),
            verifier=MagicMock(),
            analytics=MagicMock(),
        )
        assert svc._reranker is not None
        assert svc._verifier is not None


class TestEnsureAgent:
    """Tests for _ensure_agent method."""

    def test_raises_when_not_initialized(self):
        svc = GraphRAGService(db_service=MagicMock())
        with pytest.raises(RuntimeError, match="ScholarlyAgent not initialized"):
            svc._ensure_agent()

    def test_returns_agent_when_initialized(self):
        svc = GraphRAGService(db_service=MagicMock())
        mock_agent = MagicMock()
        svc._agent = mock_agent
        assert svc._ensure_agent() is mock_agent


class TestDeprecationWarnings:
    """Tests for deprecated parameter warnings."""

    @pytest.mark.asyncio
    async def test_warns_on_non_default_params(self):
        svc = GraphRAGService(db_service=MagicMock())
        mock_agent = AsyncMock()
        mock_agent.query_dict = AsyncMock(return_value=verified_result("test"))
        svc._agent = mock_agent
        svc._kg_loaded = True

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            await svc.query("test", semantic_k=20, graph_depth=3)
            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "deprecated" in str(w[0].message).lower()

    @pytest.mark.asyncio
    async def test_no_warning_on_defaults(self):
        svc = GraphRAGService(db_service=MagicMock())
        mock_agent = AsyncMock()
        mock_agent.query_dict = AsyncMock(return_value=verified_result("test"))
        svc._agent = mock_agent
        svc._kg_loaded = True

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            await svc.query("test")
            deprecation_warnings = [
                x for x in w if issubclass(x.category, DeprecationWarning)
            ]
            assert len(deprecation_warnings) == 0


class TestLoadKG:
    """Tests for load_kg."""

    @pytest.mark.asyncio
    async def test_load_kg_idempotent(self):
        db = AsyncMock()
        db.fetch = AsyncMock(return_value=[])
        svc = GraphRAGService(db_service=db)

        with patch("eleutheria_graphrag.services.graphrag_service.ScholarlyAgent"):
            await svc.load_kg()
            call_count = db.fetch.call_count
            await svc.load_kg()
            # Second call should be a no-op
            assert db.fetch.call_count == call_count

    @pytest.mark.asyncio
    async def test_auto_loads_on_query(self):
        db = AsyncMock()
        db.fetch = AsyncMock(return_value=[])
        svc = GraphRAGService(db_service=db)

        mock_agent = AsyncMock()
        mock_agent.query_dict = AsyncMock(return_value=verified_result("test"))

        with patch(
            "eleutheria_graphrag.services.graphrag_service.ScholarlyAgent",
            return_value=mock_agent,
        ):
            result = await svc.query("test")
            assert result["answer"] == "test"
            assert svc._kg_loaded is True

    @pytest.mark.asyncio
    async def test_load_kg_injects_tree_index_and_llm_reranker(self):
        db = AsyncMock()
        db.fetch = AsyncMock(return_value=[])
        svc = GraphRAGService(db_service=db)

        with patch(
            "eleutheria_graphrag.services.graphrag_service.ScholarlyAgent"
        ) as mock_agent_cls:
            await svc.load_kg()

        deps = mock_agent_cls.call_args.args[0]
        assert deps.tree_index is not None
        assert deps.llm_reranker is not None
        assert deps.traversal is not None
        # Vectorless: an SQL strategy is wired when DB is connected.
        assert deps.retrieval_strategy is not None

    @pytest.mark.asyncio
    async def test_load_kg_orders_nodes_and_edges_deterministically(self):
        """Adjacency lists are built in result-set order; without a stable
        ORDER BY the traversal would depend on the planner."""
        db = AsyncMock()
        db.fetch = AsyncMock(return_value=[])
        svc = GraphRAGService(db_service=db)

        with patch("eleutheria_graphrag.services.graphrag_service.ScholarlyAgent"):
            await svc.load_kg()

        queries = [call.args[0] for call in db.fetch.await_args_list]
        nodes_sql = next(q for q in queries if "FROM free_will.kg_nodes" in q)
        edges_sql = next(q for q in queries if "FROM free_will.kg_edges" in q)
        assert "ORDER BY node_id" in nodes_sql
        assert "ORDER BY source_id, target_id, relation, edge_id" in edges_sql

    @pytest.mark.asyncio
    async def test_load_kg_uses_provided_snapshot_data_without_db(self):
        db = MagicMock()
        db.is_connected.return_value = False
        db.fetch = AsyncMock()
        kg_data = {
            "nodes": [
                {
                    "id": "concept_fate",
                    "label": "Fate",
                    "type": "concept",
                    "description": "Stoic fate",
                    "metadata": {},
                },
                {
                    "id": "passage_plut_fat_1",
                    "label": "Plutarch, De fato 1",
                    "type": "passage",
                    "description": "Passage text",
                    "metadata": {"author": "Plutarch", "work_title": "De fato"},
                },
            ],
            "edges": [
                {
                    "source": "concept_fate",
                    "target": "passage_plut_fat_1",
                    "relation": "evidenced_by",
                    "weight": "0.9",
                    "metadata": {},
                }
            ],
        }
        svc = GraphRAGService(db_service=db, kg_data=kg_data)

        with patch(
            "eleutheria_graphrag.services.graphrag_service.ScholarlyAgent"
        ) as mock_agent_cls:
            await svc.load_kg()

        db.fetch.assert_not_called()
        assert svc._kg_loaded is True
        assert svc.node_lookup["concept_fate"]["label"] == "Fate"
        assert svc.outgoing_edges["concept_fate"][0]["target"] == "passage_plut_fat_1"
        deps = mock_agent_cls.call_args.args[0]
        assert deps.tree_index is None

    @pytest.mark.asyncio
    async def test_load_kg_normalizes_json_metadata_strings(self):
        db = AsyncMock()
        db.fetch = AsyncMock(
            side_effect=[
                [
                    {
                        "id": "n1",
                        "label": "Stoicism",
                        "type": "school",
                        "description": "A school",
                        "period": "Hellenistic",
                        "school": None,
                        "role": None,
                        "metadata": '{"school": "Stoicism"}',
                        "date": None,
                        "birth": None,
                        "death": None,
                        "floruit": None,
                        "approximate_dates": None,
                        "scholarly_role": None,
                    }
                ],
                [
                    {
                        "source": "n1",
                        "target": "n2",
                        "relation": "influenced",
                        "description": None,
                        "weight": 1.0,
                        "metadata": '{"weight": 0.7}',
                    }
                ],
            ]
        )
        svc = GraphRAGService(db_service=db)

        with patch("eleutheria_graphrag.services.graphrag_service.ScholarlyAgent"):
            await svc.load_kg()

        assert svc.node_lookup["n1"]["metadata"] == {"school": "Stoicism"}
        assert svc.outgoing_edges["n1"][0]["metadata"] == {"weight": 0.7}
