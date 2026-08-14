"""Production-grade integration tests: full pipeline per query type.

These tests hit real services — PostgreSQL and a live LLM.
They are skipped automatically when the required environment variables
are not set, so they never break CI without infrastructure.

Run locally:
    DATABASE_URL='...' CODEX_PROXY_API_KEY='...' \
    pytest tests/integration/ -v -m integration

Required env vars (at least one LLM key must be present):
    DATABASE_URL     — asyncpg-compatible PostgreSQL connection string
    CODEX_PROXY_API_KEY — Codex proxy (preferred)
    GEMINI_API_KEY   — Gemini (fallback)
    CLAUDE_PROXY_API_KEY — Claude proxy (fallback)
"""

from __future__ import annotations

import os

import pytest

from eleutheria_graphrag.agents.pipeline_config import QueryType
from eleutheria_graphrag.agents.state import ScholarlyAnswer
from eleutheria_graphrag.services.graphrag_service import GraphRAGService
from eleutheria_graphrag.services.llm_service import LLMService, ModelProvider

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _require_env() -> None:
    """Skip the entire module if infrastructure is not available."""
    missing = []
    if not os.getenv("DATABASE_URL"):
        missing.append("DATABASE_URL")
    has_llm = any(
        os.getenv(k)
        for k in ("CODEX_PROXY_API_KEY", "CLAUDE_PROXY_API_KEY", "GEMINI_API_KEY")
    )
    if not has_llm:
        missing.append(
            "CODEX_PROXY_API_KEY / CLAUDE_PROXY_API_KEY / GEMINI_API_KEY"
        )
    if missing:
        pytest.skip(
            f"Integration env vars not set: {', '.join(missing)}",
            allow_module_level=True,
        )


_require_env()


def _build_llm() -> LLMService:
    """Return an LLMService using whichever key is available."""
    if os.getenv("CODEX_PROXY_API_KEY"):
        return LLMService(preferred_provider=ModelProvider.CODEX)
    if os.getenv("CLAUDE_PROXY_API_KEY"):
        return LLMService(preferred_provider=ModelProvider.CLAUDE)
    return LLMService(preferred_provider=ModelProvider.GEMINI)


# ---------------------------------------------------------------------------
# Session-scoped fixture — real services, KG loaded once
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
async def graphrag() -> GraphRAGService:
    """Boot a real GraphRAGService backed by live DB + LLM (vectorless)."""
    import sys

    sys.path.insert(
        0, os.path.join(os.path.dirname(__file__), "../../../../database/src")
    )
    sys.path.insert(
        0, os.path.join(os.path.dirname(__file__), "../../../../knowledge graph/src")
    )

    from eleutheria_database.services.db import DatabaseService

    db = DatabaseService()
    await db.connect()

    llm = _build_llm()

    svc = GraphRAGService(db_service=db, llm_service=llm)
    await svc.load_kg()

    yield svc

    await svc.close()


# ---------------------------------------------------------------------------
# Test 1 — specific_entity
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestSpecificEntityPipeline:
    """Single philosopher or concept: direct KG lookup path."""

    async def test_chrysippus_query(self, graphrag: GraphRAGService) -> None:
        agent = graphrag._ensure_agent()
        answer: ScholarlyAnswer = await agent.query("Who was Chrysippus?")

        assert isinstance(answer, ScholarlyAnswer)
        assert len(answer.answer) > 100, "Answer should be substantive"
        assert answer.query_type == QueryType.SPECIFIC_ENTITY
        assert answer.quality_badge in ("High", "Medium", "Low")
        assert not answer.insufficient_evidence, "Should find Chrysippus in KG"


# ---------------------------------------------------------------------------
# Test 2 — global_abstract
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestGlobalAbstractPipeline:
    """Broad doctrinal question: hybrid retrieval path."""

    async def test_stoic_fate_query(self, graphrag: GraphRAGService) -> None:
        agent = graphrag._ensure_agent()
        answer: ScholarlyAnswer = await agent.query(
            "What did the Stoics believe about fate?"
        )

        assert isinstance(answer, ScholarlyAnswer)
        assert len(answer.answer) > 150
        assert answer.query_type == QueryType.GLOBAL_ABSTRACT
        assert answer.quality_badge in ("High", "Medium", "Low")
        # Stoic doctrine should be well-attested in the KG
        assert not answer.insufficient_evidence


# ---------------------------------------------------------------------------
# Test 3 — multi_hop
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestMultiHopPipeline:
    """Multi-step reasoning across philosophers: decompose + traverse path."""

    async def test_chrysippus_to_epictetus_evolution(
        self, graphrag: GraphRAGService
    ) -> None:
        agent = graphrag._ensure_agent()
        answer: ScholarlyAnswer = await agent.query(
            "How did Stoic views on fate evolve from Chrysippus to Epictetus?"
        )

        assert isinstance(answer, ScholarlyAnswer)
        assert len(answer.answer) > 150
        assert answer.query_type == QueryType.MULTI_HOP
        assert answer.quality_badge in ("High", "Medium", "Low")
        # Multi-hop should decompose into sub-questions
        assert len(answer.sub_queries) >= 1


# ---------------------------------------------------------------------------
# Test 4 — comparative
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestComparativePipeline:
    """Comparing two schools: dual retrieval + synthesis path."""

    async def test_stoic_vs_epicurean_determinism(
        self, graphrag: GraphRAGService
    ) -> None:
        agent = graphrag._ensure_agent()
        answer: ScholarlyAnswer = await agent.query(
            "Compare Stoic and Epicurean views on determinism and free will"
        )

        assert isinstance(answer, ScholarlyAnswer)
        assert len(answer.answer) > 150
        assert answer.query_type == QueryType.COMPARATIVE
        assert answer.quality_badge in ("High", "Medium", "Low")


# ---------------------------------------------------------------------------
# Test 5 — temporal
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestTemporalPipeline:
    """Historical development across periods: chronological traversal path."""

    async def test_free_will_plato_to_augustine(
        self, graphrag: GraphRAGService
    ) -> None:
        agent = graphrag._ensure_agent()
        answer: ScholarlyAnswer = await agent.query(
            "How did debates about free will develop from Plato to Augustine?"
        )

        assert isinstance(answer, ScholarlyAnswer)
        assert len(answer.answer) > 150
        assert answer.query_type == QueryType.TEMPORAL
        assert answer.quality_badge in ("High", "Medium", "Low")


# ---------------------------------------------------------------------------
# Test 6 — answer quality invariants (run on any query type)
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestAnswerQualityInvariants:
    """Cross-cutting quality checks that hold regardless of query type."""

    async def test_answer_never_empty(self, graphrag: GraphRAGService) -> None:
        agent = graphrag._ensure_agent()
        answer: ScholarlyAnswer = await agent.query(
            "What is the Stoic concept of heimarmenē?"
        )
        assert answer.answer.strip(), "Answer must never be empty"
        assert answer.question == "What is the Stoic concept of heimarmenē?"

    async def test_self_rag_badge_always_set(self, graphrag: GraphRAGService) -> None:
        agent = graphrag._ensure_agent()
        answer: ScholarlyAnswer = await agent.query(
            "What is moral responsibility in Aristotle?"
        )
        assert answer.quality_badge in ("High", "Medium", "Low"), (
            f"Unexpected badge: {answer.quality_badge!r}"
        )

    async def test_kg_loaded_with_real_data(self, graphrag: GraphRAGService) -> None:
        """The KG must have been loaded with production data."""
        assert len(graphrag.node_lookup) >= 100, (
            f"Expected ≥100 KG nodes, got {len(graphrag.node_lookup)}"
        )
        assert len(graphrag.outgoing_edges) >= 50, (
            f"Expected ≥50 edge sources, got {len(graphrag.outgoing_edges)}"
        )
