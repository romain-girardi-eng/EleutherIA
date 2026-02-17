"""Integration tests: one full-pipeline run per query type.

These tests exercise the complete 17-node FSM from ClassifyQueryType
to End, with mocked external dependencies (LLM, Qdrant, DB).
Each test covers one of the 5 query types in the taxonomy.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from eleutheria_graphrag.agents.dependencies import Deps
from eleutheria_graphrag.agents.scholarly_agent import ScholarlyAgent
from eleutheria_graphrag.agents.pipeline_config import QueryType


# ---------------------------------------------------------------------------
# Shared mock factory
# ---------------------------------------------------------------------------


def _make_deps(llm_responses: list[str]) -> Deps:
    """Build a mock Deps with a cycling LLM response list."""
    _responses = list(llm_responses)
    _idx = [0]

    async def _side_effect(*args, **kwargs):
        r = _responses[min(_idx[0], len(_responses) - 1)]
        _idx[0] += 1
        return r

    llm = AsyncMock()
    llm.generate = AsyncMock(side_effect=_side_effect)

    qdrant = AsyncMock()
    qdrant.search_nodes = AsyncMock(
        return_value=[
            {"id": "chrysippus", "score": 0.93},
            {"id": "fate_concept", "score": 0.85},
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
                "description": "Third head of the Stoic school. Leading Stoic philosopher.",
                "period": "Hellenistic",
                "school": "Stoicism",
                "role": None,
            },
            "fate_concept": {
                "id": "fate_concept",
                "label": "Fate (heimarmenē)",
                "type": "Concept",
                "description": "The Stoic concept of deterministic fate, linked to the world-reason.",
                "period": "Hellenistic",
                "school": "Stoicism",
                "role": None,
            },
            "epicurus": {
                "id": "epicurus",
                "label": "Epicurus",
                "type": "Person",
                "description": "Founder of Epicureanism.",
                "period": "Hellenistic",
                "school": "Epicureanism",
                "role": None,
            },
        },
        outgoing_edges={},
        incoming_edges={},
    )


_EMB_PATCH = patch(
    "eleutheria_graphrag.agents.graph_nodes._get_embedding",
    new_callable=AsyncMock,
    return_value=[0.1] * 768,
)

# Shared self-RAG eval (high quality) reused in all tests
_SELF_RAG_OK = '{"relevance": 85, "grounding": 88, "completeness": 82, "confidence": 85, "caveats": [], "improvements": []}'
_CRAG_OK = '{"relevance": 80, "completeness": 75, "confidence": 78, "reasoning": "sufficient"}'


# ---------------------------------------------------------------------------
# Test 1: specific_entity
# ---------------------------------------------------------------------------


class TestSpecificEntityPipeline:
    """simple: ClassifyQueryType → ExpandQuery → DirectKGLookup → TreeReasoningRetrieve
    → CRAGValidate → DualRerank → FetchPassagesAndLayer → Synthesize
    → VerifyCitations → SelfRAGEvaluate → End"""

    @pytest.mark.asyncio
    async def test_specific_entity_full_pipeline(self):
        # specific_entity: use_expansion=True, use_hyde=False, use_crag=True, use_self_rag=True
        responses = [
            '{"query_type": "specific_entity", "complexity": "simple", "reason": "single person"}',
            # ExpandQuery (use_expansion=True for specific_entity)
            '{"expanded_query": "Chrysippus (Chrysippos)", "greek_terms": [], "latin_terms": [], "related_philosophers": ["Chrysippus"], "related_concepts": []}',
            # CRAGValidate
            _CRAG_OK,
            # Synthesize
            "Chrysippus (c. 280-207 BCE) was the third head of the Stoic school [1].",
            # SelfRAGEvaluate
            _SELF_RAG_OK,
        ]
        deps = _make_deps(responses)
        agent = ScholarlyAgent(deps)

        with _EMB_PATCH:
            answer = await agent.query("Who was Chrysippus?")

        assert answer.query_type == QueryType.SPECIFIC_ENTITY
        assert "Chrysippus" in answer.answer
        assert answer.quality_badge == "High"


# ---------------------------------------------------------------------------
# Test 2: global_abstract
# ---------------------------------------------------------------------------


class TestGlobalAbstractPipeline:
    """medium: ClassifyQueryType → ExpandQuery (skip) → HybridRetrieve
    → TreeReasoningRetrieve → CRAGValidate → DualRerank → FetchPassagesAndLayer
    → Synthesize → VerifyCitations → SelfRAGEvaluate → End"""

    @pytest.mark.asyncio
    async def test_global_abstract_full_pipeline(self):
        # global_abstract: use_expansion=False, use_hyde=True (but no deps.hyde), use_crag=True
        responses = [
            '{"query_type": "global_abstract", "complexity": "medium", "reason": "abstract doctrine"}',
            # ExpandQuery skips LLM (use_expansion=False for global_abstract)
            # CRAGValidate
            _CRAG_OK,
            # Synthesize
            "The Stoics believed fate (heimarmenē) was the all-encompassing causal chain [1].",
            # SelfRAGEvaluate
            _SELF_RAG_OK,
        ]
        deps = _make_deps(responses)
        agent = ScholarlyAgent(deps)

        with _EMB_PATCH:
            answer = await agent.query("What did the Stoics believe about fate?")

        assert answer.query_type == QueryType.GLOBAL_ABSTRACT
        assert "fate" in answer.answer.lower() or "Stoic" in answer.answer
        assert answer.quality_badge in ("High", "Medium")


# ---------------------------------------------------------------------------
# Test 3: multi_hop
# ---------------------------------------------------------------------------


class TestMultiHopPipeline:
    """complex: ClassifyQueryType → ExpandQuery → DecomposeQuery
    → SearchPrimarySources → EvaluateSufficiency (LLM) → TreeReasoningRetrieve
    → CRAGValidate → DualRerank → FetchPassagesAndLayer → SearchSecondarySources
    → SynthesizeWithHierarchy → VerifyCitations → SelfRAGEvaluate → End"""

    @pytest.mark.asyncio
    async def test_multi_hop_full_pipeline(self):
        responses = [
            # ClassifyQueryType
            '{"query_type": "multi_hop", "complexity": "complex", "reason": "multi-hop evolution"}',
            # ExpandQuery (use_expansion=True for multi_hop)
            '{"expanded_query": "Stoic fate Chrysippus Epictetus", "greek_terms": [], "latin_terms": [], "related_philosophers": ["Chrysippus", "Epictetus"], "related_concepts": ["fate"]}',
            # DecomposeQuery
            '["What was Chrysippus\'s view of fate?", "How did Epictetus modify this?"]',
            # EvaluateSufficiency (heuristic won't pass: 2 nodes, 0 passages)
            '{"score": 0.85, "sufficient": true, "reason": "enough primary sources"}',
            # CRAGValidate
            _CRAG_OK,
            # SynthesizeWithHierarchy
            "Chrysippus [1] established fate as an unbroken chain of causes. Epictetus [2] emphasized what is in our power.",
            # SelfRAGEvaluate
            _SELF_RAG_OK,
        ]
        deps = _make_deps(responses)
        agent = ScholarlyAgent(deps)

        with _EMB_PATCH:
            answer = await agent.query(
                "How did Stoic views on fate evolve from Chrysippus to Epictetus?"
            )

        assert answer.query_type == QueryType.MULTI_HOP
        assert len(answer.sub_queries) >= 1
        assert answer.quality_badge in ("High", "Medium")


# ---------------------------------------------------------------------------
# Test 4: comparative
# ---------------------------------------------------------------------------


class TestComparativePipeline:
    """complex: ClassifyQueryType → ExpandQuery → HybridRetrieve
    → TreeReasoningRetrieve → CRAGValidate → DualRerank → FetchPassagesAndLayer
    → SearchSecondarySources → SynthesizeWithHierarchy → VerifyCitations
    → SelfRAGEvaluate → End"""

    @pytest.mark.asyncio
    async def test_comparative_full_pipeline(self):
        responses = [
            # ClassifyQueryType
            '{"query_type": "comparative", "complexity": "complex", "reason": "compare two schools"}',
            # ExpandQuery (use_expansion=True for comparative)
            '{"expanded_query": "Stoic Epicurean fate determinism comparison", "greek_terms": [], "latin_terms": [], "related_philosophers": [], "related_concepts": ["fate", "determinism"]}',
            # CRAGValidate
            _CRAG_OK,
            # SynthesizeWithHierarchy (comparative routes to SearchSecondarySources first)
            "Stoics held fate as an unbroken causal chain [1], while Epicureans introduced the swerve [2] to escape necessity.",
            # SelfRAGEvaluate
            _SELF_RAG_OK,
        ]
        deps = _make_deps(responses)
        agent = ScholarlyAgent(deps)

        with _EMB_PATCH:
            answer = await agent.query(
                "Compare Stoic and Epicurean views on fate and determinism"
            )

        assert answer.query_type == QueryType.COMPARATIVE
        assert "Stoic" in answer.answer or "Epicurean" in answer.answer


# ---------------------------------------------------------------------------
# Test 5: temporal
# ---------------------------------------------------------------------------


class TestTemporalPipeline:
    """complex: ClassifyQueryType → ExpandQuery → DecomposeQuery
    → SearchPrimarySources → EvaluateSufficiency → TreeReasoningRetrieve
    → CRAGValidate → DualRerank → FetchPassagesAndLayer → SearchSecondarySources
    → SynthesizeWithHierarchy → VerifyCitations → SelfRAGEvaluate → End"""

    @pytest.mark.asyncio
    async def test_temporal_full_pipeline(self):
        responses = [
            # ClassifyQueryType
            '{"query_type": "temporal", "complexity": "complex", "reason": "historical evolution"}',
            # ExpandQuery (use_expansion=True for temporal)
            '{"expanded_query": "Stoic free will history evolution", "greek_terms": [], "latin_terms": [], "related_philosophers": ["Chrysippus", "Epictetus", "Marcus Aurelius"], "related_concepts": ["free will"]}',
            # DecomposeQuery
            '["Early Stoicism on free will", "Late Stoicism on free will"]',
            # EvaluateSufficiency
            '{"score": 0.8, "sufficient": true, "reason": "sufficient"}',
            # CRAGValidate
            _CRAG_OK,
            # SynthesizeWithHierarchy
            "The Stoic position on free will evolved significantly from Early [1] to Late Stoicism [2].",
            # SelfRAGEvaluate
            _SELF_RAG_OK,
        ]
        deps = _make_deps(responses)
        agent = ScholarlyAgent(deps)

        with _EMB_PATCH:
            answer = await agent.query(
                "How did Stoic views on free will change historically?"
            )

        assert answer.query_type == QueryType.TEMPORAL
        assert "Stoic" in answer.answer or "free will" in answer.answer.lower()
