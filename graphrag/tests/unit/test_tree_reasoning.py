"""Tests for TreeReasoningRetrieve FSM node."""

from unittest.mock import AsyncMock

import pytest

from eleutheria_graphrag.agents.graph_nodes import CRAGValidate, TreeReasoningRetrieve
from eleutheria_graphrag.agents.pipeline_config import PipelineConfig
from eleutheria_graphrag.agents.state import Evidence, EvidenceLayer, EvidenceSource, RAGState

from .conftest import make_ctx, make_deps


class TestTreeReasoningRetrieve:
    @pytest.mark.asyncio
    async def test_passthrough_no_tree_index(self):
        """When tree_index is None, should pass through to CRAGValidate."""
        deps = make_deps()
        state = RAGState(question="test")
        ctx = make_ctx(state, deps)

        node = TreeReasoningRetrieve()
        result = await node.run(ctx)

        assert isinstance(result, CRAGValidate)
        deps.llm.generate.assert_not_called()

    @pytest.mark.asyncio
    async def test_passthrough_when_disabled(self):
        """When use_tree_reasoning=False, should pass through."""
        deps = make_deps()
        state = RAGState(question="test")
        state.pipeline_config = PipelineConfig(use_tree_reasoning=False)
        ctx = make_ctx(state, deps)

        node = TreeReasoningRetrieve()
        result = await node.run(ctx)

        assert isinstance(result, CRAGValidate)

    @pytest.mark.asyncio
    async def test_passthrough_on_index_load_failure(self):
        """Tree index load failure should pass through gracefully."""
        mock_tree_index = AsyncMock()
        mock_tree_index.load_indices = AsyncMock(side_effect=RuntimeError("DB error"))

        deps = make_deps()
        deps.tree_index = mock_tree_index

        state = RAGState(question="test")
        state.pipeline_config = PipelineConfig(use_tree_reasoning=True)
        state.primary_evidence = [Evidence(id="n1", type="passage", work_title="De Fato")]
        ctx = make_ctx(state, deps)

        node = TreeReasoningRetrieve()
        result = await node.run(ctx)

        assert isinstance(result, CRAGValidate)

    @pytest.mark.asyncio
    async def test_llm_navigation_extracts_passages(self):
        """When tree index has data, LLM navigates and extracts passages."""
        from eleutheria_graphrag.services.tree_index import TreeNode, WorkTreeIndex

        tree = WorkTreeIndex(
            work_id="de_fato",
            title="De Fato",
            author="Cicero",
            period="Republican",
            total_passages=100,
            nodes=[
                TreeNode(
                    node_id="root",
                    title="De Fato",
                    start_passage=1,
                    end_passage=100,
                    summary="Cicero's work on fate and determinism",
                    nodes=[
                        TreeNode(
                            node_id="ch1",
                            title="Chapter 1: Fate",
                            start_passage=1,
                            end_passage=20,
                            summary="Introduction to fate",
                        ),
                    ],
                ),
            ],
        )

        mock_tree_index = AsyncMock()
        mock_tree_index.load_indices = AsyncMock(return_value=[tree])
        mock_tree_index.extract_passages = AsyncMock(return_value=[
            {
                "passage_id": 1,
                "text_content": "Fate is the eternal cause of all things.",
                "canonical_ref": "De Fat. 1",
                "title": "De Fato",
                "author": "Cicero",
                "confidence": 0.9,
            }
        ])

        deps = make_deps(
            llm_response='{"selected_nodes": [{"node_id": "ch1", "work_id": "de_fato", "priority": 1, "reasoning": "directly relevant"}], "reasoning": "Chapter 1 covers fate"}'
        )
        deps.tree_index = mock_tree_index

        state = RAGState(question="What is fate in Cicero?")
        state.pipeline_config = PipelineConfig(use_tree_reasoning=True)
        state.primary_evidence = [Evidence(id="n1", type="passage", work_title="De Fato")]
        ctx = make_ctx(state, deps)

        node = TreeReasoningRetrieve()
        result = await node.run(ctx)

        assert isinstance(result, CRAGValidate)
        # Should have added tree-retrieved passages
        tree_evidence = [
            e for e in ctx.state.primary_evidence
            if e.source == EvidenceSource.TREE_REASONING
        ]
        assert len(tree_evidence) >= 1
