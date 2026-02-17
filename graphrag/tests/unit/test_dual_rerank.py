"""Tests for DualRerank FSM node."""

from unittest.mock import AsyncMock

import pytest

from eleutheria_graphrag.agents.graph_nodes import DualRerank, FetchPassagesAndLayer
from eleutheria_graphrag.agents.pipeline_config import PipelineConfig
from eleutheria_graphrag.agents.state import Evidence, EvidenceLayer, RAGState

from .conftest import make_ctx, make_deps


class TestDualRerank:
    @pytest.mark.asyncio
    async def test_passthrough_when_disabled(self):
        """DualRerank should pass through when use_reranking=False."""
        deps = make_deps()
        state = RAGState(question="test")
        state.pipeline_config = PipelineConfig(use_reranking=False)
        ctx = make_ctx(state, deps)

        node = DualRerank()
        result = await node.run(ctx)

        assert isinstance(result, FetchPassagesAndLayer)

    @pytest.mark.asyncio
    async def test_passthrough_when_no_eligible_evidence(self):
        """Empty or short-description evidence → skip reranking."""
        deps = make_deps()
        state = RAGState(question="test")
        state.primary_evidence = [Evidence(id="n1", label="X", type="Person")]
        ctx = make_ctx(state, deps)

        node = DualRerank()
        result = await node.run(ctx)

        assert isinstance(result, FetchPassagesAndLayer)

    @pytest.mark.asyncio
    async def test_cross_encoder_reranking(self):
        """Cross-encoder reranker should be called when available and evidence present."""
        mock_reranker = AsyncMock()
        evidence = [
            Evidence(id=f"n{i}", label=f"Node{i}", type="Person",
                     description="A" * 25, layer=EvidenceLayer.PRIMARY)
            for i in range(5)
        ]
        mock_reranker.rerank = AsyncMock(return_value=evidence[:3])

        deps = make_deps()
        deps.reranker = mock_reranker

        state = RAGState(question="test question about Stoics")
        state.primary_evidence = evidence
        ctx = make_ctx(state, deps)

        node = DualRerank()
        result = await node.run(ctx)

        assert isinstance(result, FetchPassagesAndLayer)
        mock_reranker.rerank.assert_called_once()

    @pytest.mark.asyncio
    async def test_llm_reranker_called_after_cross_encoder(self):
        """LLM reranker should be called on cross-encoder output."""
        mock_reranker = AsyncMock()
        evidence = [
            Evidence(id=f"n{i}", label=f"Node{i}", type="Person",
                     description="A" * 25, layer=EvidenceLayer.PRIMARY)
            for i in range(5)
        ]
        mock_reranker.rerank = AsyncMock(return_value=evidence)

        mock_llm_reranker = AsyncMock()
        mock_llm_reranker.rerank = AsyncMock(return_value=evidence[:3])

        deps = make_deps()
        deps.reranker = mock_reranker
        deps.llm_reranker = mock_llm_reranker

        state = RAGState(question="test question about Stoics")
        state.primary_evidence = evidence
        ctx = make_ctx(state, deps)

        node = DualRerank()
        result = await node.run(ctx)

        assert isinstance(result, FetchPassagesAndLayer)
        mock_llm_reranker.rerank.assert_called_once()

    @pytest.mark.asyncio
    async def test_graceful_on_reranker_failure(self):
        """Reranker errors should not crash the node."""
        mock_reranker = AsyncMock()
        mock_reranker.rerank = AsyncMock(side_effect=RuntimeError("reranker failed"))

        evidence = [
            Evidence(id=f"n{i}", label=f"Node{i}", type="Person",
                     description="A" * 25, layer=EvidenceLayer.PRIMARY)
            for i in range(3)
        ]

        deps = make_deps()
        deps.reranker = mock_reranker

        state = RAGState(question="test")
        state.primary_evidence = evidence
        ctx = make_ctx(state, deps)

        node = DualRerank()
        result = await node.run(ctx)

        assert isinstance(result, FetchPassagesAndLayer)
