"""Integration tests for ScholarlyAgent (full FSM execution)."""

from unittest.mock import AsyncMock, patch

import pytest

from eleutheria_graphrag.agents.dependencies import Deps
from eleutheria_graphrag.agents.scholarly_agent import ScholarlyAgent


def _make_deps(llm_responses: list[str] | None = None) -> Deps:
    """Create a mock Deps for integration testing.

    The new 17-node FSM needs more LLM responses than the old 10-node FSM.
    Sequence per simple query:
      1. ClassifyQueryType     → JSON classification + query_type
      2. ExpandQuery           → JSON expansion terms (or fallback static)
      3. TreeReasoningRetrieve → JSON tree navigation (or no tree_index → skip)
      4. CRAGValidate          → JSON CRAG validation
      5. Synthesize / SynthesizeWithHierarchy → plain text answer
      6. SelfRAGEvaluate       → JSON self-RAG evaluation

    The mock uses a cycling side_effect so excess responses are silently
    ignored and missing ones repeat the last value.
    """
    responses = llm_responses or [
        # 1. ClassifyQueryType — returns query_type JSON
        '{"query_type": "specific_entity", "complexity": "simple", "reason": "single entity lookup"}',
        # 2. ExpandQuery — returns expansion JSON (may fall back to static if parse fails)
        '{"expanded_query": "Chrysippus (Chrysippos)", "greek_terms": [{"greek": "Chrysippos", "transliteration": "Chrysippos", "meaning": "Chrysippus"}], "latin_terms": [], "related_philosophers": ["Chrysippus"], "related_concepts": []}',
        # 3. CRAGValidate (TreeReasoningRetrieve is a passthrough with no tree_index)
        '{"relevance": 80, "completeness": 70, "confidence": 75, "verdict": "proceed", "reasoning": "ok"}',
        # 4. Synthesis (DualRerank passthrough, FetchPassagesAndLayer routes to Synthesize)
        "Chrysippus was the third head of the Stoic school [1].",
        # 5. SelfRAGEvaluate
        '{"confidence": 80, "factual_accuracy": 85, "citation_quality": 75, "completeness": 70, "reasoning": "good", "should_refine": false}',
    ]

    llm = AsyncMock()
    # Use a cycling iterator so extra calls return the last response
    _iter = iter(responses)

    async def _side_effect(*args, **kwargs):  # noqa: ARG001
        try:
            return next(_iter)
        except StopIteration:
            return responses[-1]

    llm.generate = AsyncMock(side_effect=_side_effect)

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
    """Test the simple query path through the 17-node FSM."""

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
                # ClassifyQueryType
                '{"query_type": "global_abstract", "complexity": "medium", "reason": "multi-source"}',
                # ExpandQuery skips LLM for GLOBAL_ABSTRACT (use_expansion=False)
                # CRAGValidate (TreeReasoningRetrieve passthrough — no tree_index)
                '{"relevance": 75, "completeness": 65, "confidence": 70, "verdict": "proceed", "reasoning": "ok"}',
                # Synthesis (FetchPassagesAndLayer routes GLOBAL_ABSTRACT to Synthesize)
                "The Stoics believed fate was a chain of causes [1].",
                # SelfRAGEvaluate
                '{"confidence": 75, "factual_accuracy": 80, "citation_quality": 70, "completeness": 65, "reasoning": "acceptable", "should_refine": false}',
            ]
        )
        agent = ScholarlyAgent(deps)

        with patch(
            "eleutheria_graphrag.agents.graph_nodes._get_embedding",
            new_callable=AsyncMock,
            return_value=[0.1] * 768,
        ):
            answer = await agent.query("What did Stoics believe about fate?")

        assert "fate" in answer.answer.lower() or "Stoic" in answer.answer


class TestScholarlyAgentComplex:
    """Test the complex query path (decompose → search → evaluate → tree → synthesize → self-rag)."""

    @pytest.mark.asyncio
    async def test_complex_query(self):
        deps = _make_deps(
            llm_responses=[
                # ClassifyQueryType
                '{"query_type": "multi_hop", "complexity": "complex", "reason": "comparative multi-hop"}',
                # ExpandQuery
                '{"expanded_query": "Stoic fate evolution Chrysippus Epictetus", "greek_terms": [], "latin_terms": [], "related_philosophers": ["Chrysippus", "Epictetus"], "related_concepts": ["fate"]}',
                # DecomposeQuery
                '["What was Stoic fate?", "How did it evolve?"]',
                # EvaluateSufficiency (LLM check since heuristic doesn't trigger with few nodes)
                '{"score": 0.9, "sufficient": true, "reason": "enough"}',
                # CRAGValidate (TreeReasoningRetrieve passthrough — no tree_index)
                '{"relevance": 80, "completeness": 70, "confidence": 75, "verdict": "proceed", "reasoning": "ok"}',
                # SynthesizeWithHierarchy (FetchPassagesAndLayer → SearchSecondarySources → SynthesizeWithHierarchy)
                "The concept of fate evolved from Chrysippus [1] to Epictetus.",
                # SelfRAGEvaluate
                '{"confidence": 80, "factual_accuracy": 82, "citation_quality": 75, "completeness": 70, "reasoning": "good", "should_refine": false}',
            ]
        )
        agent = ScholarlyAgent(deps)

        with patch(
            "eleutheria_graphrag.agents.graph_nodes._get_embedding",
            new_callable=AsyncMock,
            return_value=[0.1] * 768,
        ):
            answer = await agent.query("How did Stoic fate evolve?")

        assert len(answer.sub_queries) >= 1
        assert "Chrysippus" in answer.answer or "fate" in answer.answer.lower()
