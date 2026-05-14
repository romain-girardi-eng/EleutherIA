"""Tests for RerankerService."""

from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from eleutheria_graphrag.agents.state import Evidence, EvidenceLayer, EvidenceSource
from eleutheria_graphrag.services.reranker import (
    DEFAULT_MODEL,
    DEFAULT_SCORE_THRESHOLD,
    DEFAULT_TOP_K,
    RerankerService,
)


def _make_evidence(n: int = 5) -> list[Evidence]:
    """Create a list of test Evidence items."""
    return [
        Evidence(
            id=f"node_{i}",
            label=f"Node {i}",
            type="Concept",
            layer=EvidenceLayer.PRIMARY,
            source=EvidenceSource.SEMANTIC_SEARCH,
            description=f"Description for node {i} about ancient philosophy",
            score=0.5,
        )
        for i in range(n)
    ]


class TestRerankerServiceInit:
    """Tests for RerankerService initialization."""

    def test_defaults(self):
        svc = RerankerService()
        assert svc.model_name == DEFAULT_MODEL
        assert svc.top_k == DEFAULT_TOP_K
        assert svc.score_threshold == DEFAULT_SCORE_THRESHOLD
        assert svc._model is None

    def test_custom_params(self):
        svc = RerankerService(
            model_name="custom/model",
            top_k=10,
            score_threshold=0.5,
        )
        assert svc.model_name == "custom/model"
        assert svc.top_k == 10
        assert svc.score_threshold == 0.5


class TestRerankerServiceRerank:
    """Tests for the rerank() method."""

    @pytest.mark.asyncio
    async def test_empty_evidence(self):
        svc = RerankerService()
        result = await svc.rerank("test query", [])
        assert result == []

    @pytest.mark.asyncio
    async def test_rerank_orders_by_score(self):
        svc = RerankerService(score_threshold=0.0)
        evidence = _make_evidence(3)

        # Mock the model to return known scores
        mock_model = MagicMock()
        mock_model.predict.return_value = np.array([0.3, 0.9, 0.6])
        svc._model = mock_model

        result = await svc.rerank("test query", evidence)
        assert len(result) == 3
        assert result[0].id == "node_1"  # highest score (0.9)
        assert result[1].id == "node_2"  # 0.6
        assert result[2].id == "node_0"  # 0.3

    @pytest.mark.asyncio
    async def test_rerank_respects_threshold(self):
        svc = RerankerService(score_threshold=0.5)
        evidence = _make_evidence(3)

        mock_model = MagicMock()
        mock_model.predict.return_value = np.array([0.3, 0.9, 0.6])
        svc._model = mock_model

        result = await svc.rerank("test query", evidence)
        # 0.3 is below threshold
        assert len(result) == 2
        assert all(ev.score >= 0.5 for ev in result)

    @pytest.mark.asyncio
    async def test_rerank_respects_top_k(self):
        svc = RerankerService(top_k=2, score_threshold=0.0)
        evidence = _make_evidence(5)

        mock_model = MagicMock()
        mock_model.predict.return_value = np.array([0.1, 0.9, 0.5, 0.7, 0.3])
        svc._model = mock_model

        result = await svc.rerank("test query", evidence)
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_rerank_updates_scores(self):
        svc = RerankerService(score_threshold=0.0)
        evidence = _make_evidence(2)

        mock_model = MagicMock()
        mock_model.predict.return_value = np.array([0.8, 0.4])
        svc._model = mock_model

        result = await svc.rerank("test query", evidence)
        assert result[0].score == pytest.approx(0.8)
        assert result[1].score == pytest.approx(0.4)

    @pytest.mark.asyncio
    async def test_rerank_uses_text_content(self):
        svc = RerankerService(score_threshold=0.0)
        evidence = [
            Evidence(
                id="p1",
                label="Passage",
                type="passage",
                text_content="Full passage text here",
                description="Short desc",
            ),
        ]

        mock_model = MagicMock()
        mock_model.predict.return_value = np.array([0.9])
        svc._model = mock_model

        await svc.rerank("query", evidence)
        # Should use text_content (preferred) not description
        pair = mock_model.predict.call_args[0][0][0]
        assert pair[1].startswith("Full passage text")

    @pytest.mark.asyncio
    async def test_rerank_fallback_on_prediction_error(self):
        svc = RerankerService(score_threshold=0.0, top_k=3)
        evidence = _make_evidence(5)

        mock_model = MagicMock()
        mock_model.predict.side_effect = RuntimeError("GPU OOM")
        svc._model = mock_model

        result = await svc.rerank("query", evidence)
        # Should fallback to first top_k items
        assert len(result) == 3

    @pytest.mark.asyncio
    async def test_rerank_override_params(self):
        svc = RerankerService(top_k=20, score_threshold=0.3)
        evidence = _make_evidence(5)

        mock_model = MagicMock()
        mock_model.predict.return_value = np.array([0.9, 0.8, 0.7, 0.6, 0.5])
        svc._model = mock_model

        result = await svc.rerank("query", evidence, top_k=2, score_threshold=0.7)
        assert len(result) == 2


class TestRerankerServiceModel:
    """Tests for model loading."""

    def test_lazy_load(self):
        svc = RerankerService()
        assert svc._model is None

    def test_load_model_caches(self):
        """Model is loaded once and cached."""
        mock_instance = MagicMock()
        mock_ce_cls = MagicMock(return_value=mock_instance)
        mock_st = MagicMock(CrossEncoder=mock_ce_cls)

        with patch.dict("sys.modules", {"sentence_transformers": mock_st}):
            svc = RerankerService()
            m1 = svc._load_model()
            m2 = svc._load_model()
            assert m1 is m2
            # CrossEncoder constructor should only be called once
            mock_ce_cls.assert_called_once()
