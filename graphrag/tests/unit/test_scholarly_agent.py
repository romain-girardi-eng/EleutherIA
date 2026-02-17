"""Integration tests for ScholarlyAgent (full FSM execution)."""

from unittest.mock import AsyncMock, patch

import pytest

from eleutheria_graphrag.agents.dependencies import Deps
from eleutheria_graphrag.agents.scholarly_agent import ScholarlyAgent
from eleutheria_graphrag.agents.state import QueryComplexity


def _make_deps(llm_responses: list[str] | None = None) -> Deps:
    """Create a mock Deps for integration testing.

    Args:
        llm_responses: Sequence of LLM responses to return in order.
    """
    responses = llm_responses or [
        # Classification
        '{"complexity": "simple", "reason": "single entity lookup"}',
        # Synthesis
        "Chrysippus was the third head of the Stoic school [1].",
    ]
    llm = AsyncMock()
    llm.generate = AsyncMock(side_effect=responses)

    qdrant = AsyncMock()
    qdrant.search_nodes = AsyncMock(
        return_value=[
            {"id": "chrysippus", "score": 0.95},
        ]
    )

    db = AsyncMock()
    db.fetch = AsyncMock(return_value=[])

    return Deps(
        db=db,
        qdrant=qdrant,
        llm=llm,
        node_lookup={
            "chrysippus": {
                "id": "chrysippus",
                "label": "Chrysippus",
                "type": "Person",
                "description": "Third head of the Stoic school",
                "period": "Hellenistic",
                "school": "Stoicism",
                "role": None,
            },
        },
        outgoing_edges={},
        incoming_edges={},
    )


class TestScholarlyAgentSimple:
    """Test the simple query path (ClassifyComplexity → DirectKGLookup → Synthesize → VerifyCitations → End)."""

    @pytest.mark.asyncio
    async def test_simple_query(self):
        deps = _make_deps()
        agent = ScholarlyAgent(deps)

        with patch(
            "eleutheria_graphrag.agents.graph_nodes._get_embedding",
            new_callable=AsyncMock,
            return_value=[0.1] * 768,
        ):
            answer = await agent.query("Who was Chrysippus?")

        assert answer.question == "Who was Chrysippus?"
        assert answer.complexity == QueryComplexity.SIMPLE
        assert "Chrysippus" in answer.answer
        assert answer.iterations == 1

    @pytest.mark.asyncio
    async def test_query_dict_format(self):
        deps = _make_deps()
        agent = ScholarlyAgent(deps)

        with patch(
            "eleutheria_graphrag.agents.graph_nodes._get_embedding",
            new_callable=AsyncMock,
            return_value=[0.1] * 768,
        ):
            result = await agent.query_dict("Who was Chrysippus?")

        assert "answer" in result
        assert "question" in result
        assert "citations" in result
        assert "seed_nodes" in result
        assert "context_nodes" in result
        assert "metadata" in result
        assert result["metadata"]["complexity"] == "simple"

    @pytest.mark.asyncio
    async def test_query_stream(self):
        deps = _make_deps()
        agent = ScholarlyAgent(deps)

        chunks: list[str] = []
        with patch(
            "eleutheria_graphrag.agents.graph_nodes._get_embedding",
            new_callable=AsyncMock,
            return_value=[0.1] * 768,
        ):
            async for chunk in agent.query_stream("Who was Chrysippus?"):
                chunks.append(chunk)

        full_text = "".join(chunks)
        assert "Chrysippus" in full_text


class TestScholarlyAgentMedium:
    """Test the medium query path."""

    @pytest.mark.asyncio
    async def test_medium_query(self):
        deps = _make_deps(
            llm_responses=[
                '{"complexity": "medium", "reason": "multi-source"}',
                "The Stoics believed fate was a chain of causes [1].",
            ]
        )
        agent = ScholarlyAgent(deps)

        with patch(
            "eleutheria_graphrag.agents.graph_nodes._get_embedding",
            new_callable=AsyncMock,
            return_value=[0.1] * 768,
        ):
            answer = await agent.query("What did Stoics believe about fate?")

        assert answer.complexity == QueryComplexity.MEDIUM


class TestScholarlyAgentComplex:
    """Test the complex query path (decompose → search → evaluate → secondary → synthesize)."""

    @pytest.mark.asyncio
    async def test_complex_query(self):
        deps = _make_deps(
            llm_responses=[
                # Classification
                '{"complexity": "complex", "reason": "comparative multi-hop"}',
                # Decomposition
                '["What was Stoic fate?", "How did it evolve?"]',
                # Sufficiency (iteration reaches max or passes heuristic)
                '{"score": 0.9, "sufficient": true, "reason": "enough"}',
                # Hierarchical synthesis
                "The concept of fate evolved from Chrysippus [1] to Epictetus.",
            ]
        )
        agent = ScholarlyAgent(deps)

        with patch(
            "eleutheria_graphrag.agents.graph_nodes._get_embedding",
            new_callable=AsyncMock,
            return_value=[0.1] * 768,
        ):
            answer = await agent.query("How did Stoic fate evolve?")

        assert answer.complexity == QueryComplexity.COMPLEX
        assert len(answer.sub_queries) >= 1
