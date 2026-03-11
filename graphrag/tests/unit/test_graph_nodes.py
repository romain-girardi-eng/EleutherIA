"""Tests for pydantic-graph FSM nodes."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from eleutheria_graphrag.agents.dependencies import Deps
from eleutheria_graphrag.agents.graph_nodes import (
    ClassifyComplexity,
    DecomposeQuery,
    DirectKGLookup,
    EvaluateSufficiency,
    HybridRetrieve,
    SearchPrimarySources,
    SelfRAGEvaluate,
    Synthesize,
    SynthesizeWithHierarchy,
    TreeReasoningRetrieve,
    VerifyCitations,
    _build_context_from_evidence,
    _build_hierarchical_context,
    _expand_graph,
    _is_primary_node,
    _parse_json,
)
from eleutheria_graphrag.agents.state import (
    Citation,
    Evidence,
    QueryComplexity,
    RAGState,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_deps(
    *,
    llm_response: str = "test",
    search_results: list | None = None,
    node_lookup: dict | None = None,
    outgoing_edges: dict | None = None,
    incoming_edges: dict | None = None,
) -> Deps:
    """Create a mock Deps for testing."""
    llm = AsyncMock()
    llm.generate = AsyncMock(return_value=llm_response)

    qdrant = AsyncMock()
    qdrant.search_nodes = AsyncMock(return_value=search_results or [])

    db = AsyncMock()
    db.fetch = AsyncMock(return_value=[])

    return Deps(
        db=db,
        qdrant=qdrant,
        llm=llm,
        node_lookup=node_lookup or {},
        outgoing_edges=outgoing_edges or {},
        incoming_edges=incoming_edges or {},
    )


def _make_ctx(state: RAGState, deps: Deps) -> MagicMock:
    """Create a mock GraphRunContext."""
    ctx = MagicMock()
    ctx.state = state
    ctx.deps = deps
    return ctx


# ---------------------------------------------------------------------------
# Helper tests
# ---------------------------------------------------------------------------


class TestParseJson:
    def test_plain_json(self):
        result = _parse_json('{"key": "value"}')
        assert result == {"key": "value"}

    def test_markdown_fenced(self):
        result = _parse_json('```json\n{"key": "value"}\n```')
        assert result == {"key": "value"}

    def test_markdown_fenced_no_lang(self):
        result = _parse_json('```\n[1, 2, 3]\n```')
        assert result == [1, 2, 3]

    def test_invalid_json_raises(self):
        with pytest.raises(Exception):  # noqa: B017
            _parse_json("not json at all")


class TestIsPrimaryNode:
    def test_person_is_primary(self):
        assert _is_primary_node({"type": "Person"}) is True

    def test_modern_interpretation_is_secondary(self):
        assert _is_primary_node({"type": "Modern_Interpretation"}) is False

    def test_modern_scholar_role_is_secondary(self):
        assert _is_primary_node({"type": "Person", "role": "modern_scholar"}) is False


class TestExpandGraph:
    def test_basic_bfs(self):
        deps = _make_deps(
            node_lookup={
                "A": {"id": "A"},
                "B": {"id": "B"},
                "C": {"id": "C"},
            },
            outgoing_edges={
                "A": [{"source": "A", "target": "B"}],
                "B": [{"source": "B", "target": "C"}],
            },
            incoming_edges={
                "B": [{"source": "A", "target": "B"}],
                "C": [{"source": "B", "target": "C"}],
            },
        )
        visited = _expand_graph(deps, ["A"], depth=2)
        assert visited == {"A", "B", "C"}

    def test_depth_limit(self):
        deps = _make_deps(
            node_lookup={"A": {}, "B": {}, "C": {}},
            outgoing_edges={
                "A": [{"source": "A", "target": "B"}],
                "B": [{"source": "B", "target": "C"}],
            },
            incoming_edges={
                "B": [{"source": "A", "target": "B"}],
                "C": [{"source": "B", "target": "C"}],
            },
        )
        visited = _expand_graph(deps, ["A"], depth=1)
        assert "A" in visited
        assert "B" in visited
        assert "C" not in visited

    def test_empty_seeds(self):
        deps = _make_deps()
        visited = _expand_graph(deps, [], depth=2)
        assert visited == set()


class TestBuildContextFromEvidence:
    def test_node_evidence(self):
        evidence = [
            Evidence(
                id="n1",
                label="Chrysippus",
                type="Person",
                description="Stoic philosopher",
                period="Hellenistic",
                school="Stoicism",
            ),
        ]
        ctx = _build_context_from_evidence(evidence)
        assert "[1]" in ctx
        assert "Chrysippus" in ctx
        assert "Hellenistic" in ctx

    def test_passage_evidence(self):
        evidence = [
            Evidence(
                id="p1",
                label="SVF 2.912",
                type="passage",
                text_content="He argues that fate...",
            ),
        ]
        ctx = _build_context_from_evidence(evidence)
        assert "[P1]" in ctx
        assert "SVF 2.912" in ctx

    def test_mixed(self):
        evidence = [
            Evidence(id="n1", label="A", type="Person"),
            Evidence(id="p1", label="P1", type="passage", text_content="text"),
            Evidence(id="n2", label="B", type="Concept"),
        ]
        ctx = _build_context_from_evidence(evidence)
        assert "[1]" in ctx
        assert "[P1]" in ctx
        assert "[2]" in ctx


class TestBuildHierarchicalContext:
    def test_primary_and_secondary(self):
        state = RAGState()
        state.primary_evidence = [
            Evidence(id="n1", label="Chrysippus", type="Person", period="Hellenistic"),
        ]
        state.secondary_evidence = [
            Evidence(
                id="s1",
                label="Bobzien",
                type="Modern_Interpretation",
                role="scholar",
            ),
        ]
        ctx = _build_hierarchical_context(state)
        assert "Primary Ancient Sources" in ctx
        assert "Modern Scholarly Interpretations" in ctx
        assert "Chrysippus" in ctx
        assert "Bobzien" in ctx


# ---------------------------------------------------------------------------
# FSM Node tests
# ---------------------------------------------------------------------------


class TestClassifyComplexity:
    @pytest.mark.asyncio
    async def test_simple_classification(self):
        deps = _make_deps(
            llm_response='{"complexity": "simple", "reason": "single entity"}'
        )
        state = RAGState(question="Who was Chrysippus?")
        ctx = _make_ctx(state, deps)

        node = ClassifyComplexity()
        with patch(
            "eleutheria_graphrag.agents.graph_nodes._get_embedding",
            new_callable=AsyncMock,
        ):
            result = await node.run(ctx)

        assert isinstance(result, DirectKGLookup)
        assert state.complexity == QueryComplexity.SIMPLE

    @pytest.mark.asyncio
    async def test_medium_classification(self):
        deps = _make_deps(
            llm_response='{"complexity": "medium", "reason": "multi-source"}'
        )
        state = RAGState(question="What did Stoics believe about fate?")
        ctx = _make_ctx(state, deps)

        node = ClassifyComplexity()
        result = await node.run(ctx)

        assert isinstance(result, HybridRetrieve)
        assert state.complexity == QueryComplexity.MEDIUM

    @pytest.mark.asyncio
    async def test_complex_classification(self):
        deps = _make_deps(
            llm_response='{"complexity": "complex", "reason": "comparative"}'
        )
        state = RAGState(question="How did fate evolve from Chrysippus to Epictetus?")
        ctx = _make_ctx(state, deps)

        node = ClassifyComplexity()
        result = await node.run(ctx)

        assert isinstance(result, DecomposeQuery)
        assert state.complexity == QueryComplexity.COMPLEX

    @pytest.mark.asyncio
    async def test_classification_failure_defaults_to_medium(self):
        deps = _make_deps(llm_response="invalid json garbage")
        state = RAGState(question="test")
        ctx = _make_ctx(state, deps)

        node = ClassifyComplexity()
        result = await node.run(ctx)

        assert isinstance(result, HybridRetrieve)
        assert state.complexity == QueryComplexity.MEDIUM


class TestDirectKGLookup:
    @pytest.mark.asyncio
    async def test_finds_nodes(self):
        deps = _make_deps(
            search_results=[
                {"id": "chrysippus", "score": 0.95},
            ],
            node_lookup={
                "chrysippus": {
                    "id": "chrysippus",
                    "label": "Chrysippus",
                    "type": "Person",
                    "description": "Stoic philosopher",
                    "period": "Hellenistic",
                    "school": "Stoicism",
                    "role": None,
                },
            },
        )
        state = RAGState(question="Who was Chrysippus?")
        ctx = _make_ctx(state, deps)

        node = DirectKGLookup()
        with patch(
            "eleutheria_graphrag.agents.graph_nodes._get_embedding",
            new_callable=AsyncMock,
            return_value=[0.1] * 768,
        ):
            result = await node.run(ctx)

        assert isinstance(result, TreeReasoningRetrieve)
        assert len(state.primary_evidence) == 1
        assert state.primary_evidence[0].label == "Chrysippus"

    @pytest.mark.asyncio
    async def test_no_results(self):
        deps = _make_deps(search_results=[])
        state = RAGState(question="Unknown entity?")
        ctx = _make_ctx(state, deps)

        node = DirectKGLookup()
        with patch(
            "eleutheria_graphrag.agents.graph_nodes._get_embedding",
            new_callable=AsyncMock,
            return_value=[0.1] * 768,
        ):
            result = await node.run(ctx)

        assert isinstance(result, TreeReasoningRetrieve)
        assert len(state.primary_evidence) == 0


class TestDecomposeQuery:
    @pytest.mark.asyncio
    async def test_decomposes_into_subqueries(self):
        deps = _make_deps(
            llm_response='["What was Stoic fate?", "How did Epicureans differ?"]'
        )
        state = RAGState(question="Compare Stoic and Epicurean views on fate")
        ctx = _make_ctx(state, deps)

        node = DecomposeQuery()
        result = await node.run(ctx)

        assert isinstance(result, SearchPrimarySources)
        assert len(state.sub_queries) == 2

    @pytest.mark.asyncio
    async def test_decomposition_failure_uses_original(self):
        deps = _make_deps(llm_response="not valid json")
        state = RAGState(question="test question")
        ctx = _make_ctx(state, deps)

        node = DecomposeQuery()
        result = await node.run(ctx)

        assert isinstance(result, SearchPrimarySources)
        assert state.sub_queries == ["test question"]


class TestEvaluateSufficiency:
    @pytest.mark.asyncio
    async def test_max_iterations_proceeds(self):
        deps = _make_deps()
        state = RAGState(question="test", iteration=5, max_iterations=5)
        ctx = _make_ctx(state, deps)

        node = EvaluateSufficiency()
        result = await node.run(ctx)

        assert isinstance(result, TreeReasoningRetrieve)

    @pytest.mark.asyncio
    async def test_heuristic_sufficiency(self):
        deps = _make_deps()
        state = RAGState(question="test", iteration=1)
        # Add enough primary evidence + passages
        state.primary_evidence = [
            Evidence(id=f"n{i}", type="Person") for i in range(5)
        ] + [Evidence(id=f"p{i}", type="passage") for i in range(3)]
        ctx = _make_ctx(state, deps)

        node = EvaluateSufficiency()
        result = await node.run(ctx)

        assert isinstance(result, TreeReasoningRetrieve)
        assert state.sufficiency_score == 0.8

    @pytest.mark.asyncio
    async def test_insufficient_loops_back(self):
        deps = _make_deps(
            llm_response='{"score": 0.3, "sufficient": false, "refinement": "more about fate"}'
        )
        state = RAGState(question="test", iteration=1, max_iterations=5)
        state.primary_evidence = [Evidence(id="n1", type="Person")]
        ctx = _make_ctx(state, deps)

        node = EvaluateSufficiency()
        result = await node.run(ctx)

        assert isinstance(result, SearchPrimarySources)
        assert state.sub_queries == ["more about fate"]

    @pytest.mark.asyncio
    async def test_sufficient_by_llm(self):
        deps = _make_deps(
            llm_response='{"score": 0.8, "sufficient": true, "reason": "good"}'
        )
        state = RAGState(question="test", iteration=1, max_iterations=5)
        state.primary_evidence = [Evidence(id="n1", type="Person")]
        ctx = _make_ctx(state, deps)

        node = EvaluateSufficiency()
        result = await node.run(ctx)

        assert isinstance(result, TreeReasoningRetrieve)


class TestSynthesize:
    @pytest.mark.asyncio
    async def test_generates_answer(self):
        deps = _make_deps(llm_response="Chrysippus was a Stoic philosopher [1].")
        state = RAGState(question="Who was Chrysippus?")
        state.primary_evidence = [
            Evidence(id="n1", label="Chrysippus", type="Person"),
        ]
        ctx = _make_ctx(state, deps)

        node = Synthesize()
        result = await node.run(ctx)

        assert isinstance(result, VerifyCitations)
        assert "Chrysippus" in state.raw_answer

    @pytest.mark.asyncio
    async def test_builds_context_when_empty(self):
        deps = _make_deps(llm_response="Answer text.")
        state = RAGState(question="test")
        state.primary_evidence = [
            Evidence(id="n1", label="A", type="Person", description="desc"),
        ]
        assert state.accumulated_context == ""
        ctx = _make_ctx(state, deps)

        node = Synthesize()
        await node.run(ctx)

        assert state.accumulated_context != ""


class TestSynthesizeWithHierarchy:
    @pytest.mark.asyncio
    async def test_generates_hierarchical_answer(self):
        deps = _make_deps(llm_response="Layered answer with [1] and [P1].")
        state = RAGState(question="Complex query")
        state.primary_evidence = [
            Evidence(id="n1", label="Chrysippus", type="Person"),
            Evidence(id="p1", label="SVF", type="passage", text_content="text"),
        ]
        state.secondary_evidence = [
            Evidence(id="s1", label="Bobzien", type="Modern_Interpretation"),
        ]
        ctx = _make_ctx(state, deps)

        node = SynthesizeWithHierarchy()
        result = await node.run(ctx)

        assert isinstance(result, VerifyCitations)
        assert state.raw_answer == "Layered answer with [1] and [P1]."
        # Should have called LLM with max_tokens=4096
        call_kwargs = deps.llm.generate.call_args
        assert call_kwargs.kwargs.get("max_tokens") == 4096


class TestVerifyCitations:
    @pytest.mark.asyncio
    async def test_extracts_node_citations(self):
        deps = _make_deps()
        state = RAGState(question="test")
        state.raw_answer = "Chrysippus [1] argued about fate [2]."
        state.primary_evidence = [
            Evidence(id="n1", label="Chrysippus", type="Person"),
            Evidence(id="n2", label="Fate", type="Concept"),
        ]
        ctx = _make_ctx(state, deps)

        node = VerifyCitations()
        result = await node.run(ctx)

        assert isinstance(result, SelfRAGEvaluate)
        assert len(state.citations) == 2
        assert state.citations[0].ref == "1"
        assert state.citations[1].ref == "2"

    @pytest.mark.asyncio
    async def test_extracts_passage_citations(self):
        deps = _make_deps()
        state = RAGState(question="test")
        state.raw_answer = "The text [P1] states..."
        state.primary_evidence = [
            Evidence(id="p1", label="SVF", type="passage"),
        ]
        ctx = _make_ctx(state, deps)

        node = VerifyCitations()
        result = await node.run(ctx)

        assert isinstance(result, SelfRAGEvaluate)
        passage_cites = [c for c in state.citations if c.type == "passage"]
        assert len(passage_cites) == 1
        assert passage_cites[0].ref == "P1"

    @pytest.mark.asyncio
    async def test_no_citations(self):
        deps = _make_deps()
        state = RAGState(question="test")
        state.raw_answer = "No citations in this answer."
        ctx = _make_ctx(state, deps)

        node = VerifyCitations()
        result = await node.run(ctx)

        assert isinstance(result, SelfRAGEvaluate)
        assert state.citations == []

    @pytest.mark.asyncio
    async def test_uses_verifier_when_available(self):
        mock_verifier = AsyncMock()
        mock_verifier.verify_citations = AsyncMock(
            return_value=[
                Citation(
                    ref="1",
                    type="node",
                    id="n1",
                    label="X",
                    verified=True,
                    verification_note="ok",
                ),
            ]
        )
        deps = _make_deps()
        deps.verifier = mock_verifier

        state = RAGState(question="test")
        state.raw_answer = "Something [1]."
        state.primary_evidence = [
            Evidence(id="n1", label="X", type="Person"),
        ]
        ctx = _make_ctx(state, deps)

        node = VerifyCitations()
        result = await node.run(ctx)

        mock_verifier.verify_citations.assert_called_once()
        assert isinstance(result, SelfRAGEvaluate)
        assert state.citations[0].verified is True

    @pytest.mark.asyncio
    async def test_fail_closed_on_verifier_error(self):
        """Verification errors must leave citations unverified (fail-closed)."""
        mock_verifier = AsyncMock()
        mock_verifier.verify_citations = AsyncMock(side_effect=RuntimeError("DB error"))
        deps = _make_deps()
        deps.verifier = mock_verifier

        state = RAGState(question="test")
        state.raw_answer = "Answer [1]."
        state.primary_evidence = [Evidence(id="n1", label="X", type="Person")]
        ctx = _make_ctx(state, deps)

        node = VerifyCitations()
        result = await node.run(ctx)

        assert isinstance(result, SelfRAGEvaluate)
        assert all(c.verified is False for c in state.citations)
