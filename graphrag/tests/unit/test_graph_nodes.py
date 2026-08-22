"""Tests for the long-context graph nodes and helpers."""

from unittest.mock import AsyncMock

import pytest
from pydantic_graph import End

from eleutheria_graphrag.agents.graph_nodes import (
    ClassifyQueryType,
    DraftClaimLedger,
    ProgrammaticVerify,
    RenderGroundedAnswer,
    _augment_claim_ledger_from_dossier,
    _build_context_from_evidence,
    _build_context_pack,
    _build_hierarchical_context,
    _build_research_graph_payload,
    _build_scholarly_dossier,
    _bundle_query_score,
    _candidate_work_titles,
    _claim_reference_markers,
    _default_research_facets,
    _expand_graph,
    _fetch_translation_for_passage,
    _is_primary_node,
    _normalize_reference_markers,
    _parse_json,
    _quality_badge_from_state,
    _render_answer_fallback,
    _render_evidence_packet,
    _salvage_claim_ledger,
    _verify_answer_programmatically,
)
from eleutheria_graphrag.agents.legacy_fsm_nodes import (
    BuildResearchNotebook,
    DiscoverCorpus,
    EvidenceSufficiency,
    ExpandEvidenceBundles,
    PlanReading,
    SeekCounterEvidence,
    TreeNavigateWorks,
)
from eleutheria_graphrag.agents.pipeline_config import PipelineConfig, QueryType
from eleutheria_graphrag.agents.state import (
    Citation,
    ClaimLedgerItem,
    ClaimStatus,
    ContextPack,
    DossierFacet,
    Evidence,
    EvidenceBundle,
    EvidenceSource,
    QueryComplexity,
    RAGState,
    ReadingDecision,
    ResearchFacet,
    ResearchPlan,
    ResearchToolCall,
    RetrievalBudget,
    ScholarlyDossier,
)
from eleutheria_graphrag.services.tree_index import TreeNode, WorkTreeIndex

from .conftest import make_ctx, make_deps


class TestHelpers:
    def test_parse_json_supports_fences(self):
        assert _parse_json('```json\n{"ok": true}\n```') == {"ok": True}

    def test_parse_json_supports_json_surrounded_by_prose(self):
        raw = 'Here is the result:\n```json\n{"claims": [{"claim": "x"}]}\n```\nUse it carefully.'
        assert _parse_json(raw) == {"claims": [{"claim": "x"}]}

    def test_parse_json_supports_unclosed_leading_fence(self):
        raw = '```json\n{"claims": [{"claim": "x", "evidence_ids": ["P1"]}]}\n'
        assert _parse_json(raw) == {"claims": [{"claim": "x", "evidence_ids": ["P1"]}]}

    def test_parse_json_repairs_trailing_commas(self):
        raw = '{"claims": [{"claim": "x", "evidence_ids": ["P1"],}],}'
        assert _parse_json(raw) == {"claims": [{"claim": "x", "evidence_ids": ["P1"]}]}

    def test_salvage_claim_ledger_recovers_complete_items_from_truncated_output(self):
        raw = """{
  "claims": [
    {"claim": "Stoic fate is determinism.", "evidence_ids": ["P1"], "quote_original": null, "quote_translation": null, "support_type": "passage", "confidence": 0.9, "status": "supported"},
    {"claim": "This second claim is cut off", "evidence_ids": ["""
        salvaged = _salvage_claim_ledger(raw)
        assert salvaged is not None
        assert len(salvaged.claims) == 1
        assert salvaged.claims[0].claim == "Stoic fate is determinism."

    def test_is_primary_node(self):
        assert _is_primary_node({"type": "Person"}) is True
        assert _is_primary_node({"type": "Modern_Interpretation"}) is False

    def test_expand_graph_bfs(self):
        deps = make_deps(
            node_lookup={"a": {}, "b": {}, "c": {}},
            outgoing_edges={
                "a": [{"source": "a", "target": "b"}],
                "b": [{"source": "b", "target": "c"}],
            },
            incoming_edges={
                "b": [{"source": "a", "target": "b"}],
                "c": [{"source": "b", "target": "c"}],
            },
        )
        assert _expand_graph(deps, ["a"], depth=2) == {"a", "b", "c"}

    def test_context_builders(self):
        state = RAGState()
        state.primary_evidence = [
            Evidence(id="n1", label="Chrysippus", type="Person", period="Hellenistic"),
            Evidence(
                id="p1",
                label="SVF 2.912",
                type="passage",
                text_content="Fate is a chain of causes.",
            ),
        ]
        flat = _build_context_from_evidence(state.primary_evidence)
        packed = _build_hierarchical_context(state)
        assert "Chrysippus" in flat
        assert "[P1]" in flat
        assert "SVF 2.912" in packed

    def test_quality_badge_degraded_is_low(self):
        state = RAGState()
        state.sufficiency_score = 0.95
        state.citations = []
        state.metadata["pipeline_degraded"] = True
        assert _quality_badge_from_state(state) == "Low"

    def test_quality_badge_high_when_score_80_and_citations(self):
        state = RAGState()
        state.sufficiency_score = 0.85
        state.citations = [
            Citation(ref="P1", type="passage", id="p1", label="De Fato 1.1")
        ]
        assert _quality_badge_from_state(state) == "High"

    def test_quality_badge_medium_when_score_60_no_citations(self):
        state = RAGState()
        state.sufficiency_score = 0.65
        state.citations = []
        assert _quality_badge_from_state(state) == "Medium"

    def test_quality_badge_low_when_score_below_60(self):
        state = RAGState()
        state.sufficiency_score = 0.5
        state.citations = []
        assert _quality_badge_from_state(state) == "Low"

    def test_candidate_work_titles_prioritize_query_match_over_passage_noise(self):
        state = RAGState(question="Who was Chrysippus?")
        state.primary_evidence = [
            Evidence(
                id="w1",
                label="Chrysippus, Fragments (SVF II)",
                type="work",
                score=0.8,
                source=EvidenceSource.SEMANTIC_SEARCH,
            ),
            Evidence(
                id="p1",
                label="Marcus Tullius Cicero, De Fato Fat. 41",
                type="passage",
                work_title="De Fato",
                author="Marcus Tullius Cicero",
                text_content="Chrysippus autem cum et necessitatem inprobaret...",
                confidence=0.95,
                source=EvidenceSource.PASSAGE_CITATION,
            ),
        ]

        titles = _candidate_work_titles(state)

        assert titles[0] == "Chrysippus, Fragments (SVF II)"

    def test_bundle_query_score_prioritizes_exact_reference_for_quote_queries(self):
        state = RAGState(
            question="Quote Alexander of Aphrodisias, De Fato 1 in Greek and English."
        )
        target = EvidenceBundle(
            bundle_id="b1",
            work_id="w1",
            work_title="De Fato (Περὶ εἱμαρμένης)",
            author="Alexander of Aphrodisias",
            section_path="Book De, Chapter Fato",
            canonical_ref="De Fato 1",
            original_passage_id="p1",
            original_text="Greek text",
            translation_text="English translation",
            language="grc",
            token_estimate=20,
        )
        distractor = target.model_copy(
            update={"bundle_id": "b2", "canonical_ref": "De Fato 38"}
        )

        assert _bundle_query_score(target, state) > _bundle_query_score(
            distractor, state
        )

    def test_default_research_facets_prioritize_doctrinal_structure_for_school_query(
        self,
    ):
        state = RAGState(
            question="What did the Stoics believe about fate and moral responsibility?"
        )
        state.query_type = QueryType.GLOBAL_ABSTRACT

        titles = [facet.title for facet in _default_research_facets(state)]

        assert "Core Doctrinal Thesis" in titles
        assert "Textual Witnesses" in titles
        assert "Agency and Responsibility" in titles

    def test_render_evidence_packet_includes_bundle_and_metadata_entries(self):
        state = RAGState(question="What did the Stoics believe about fate?")
        state.primary_evidence = [
            Evidence(
                id="node-1",
                label="Heimarmenê",
                type="concept",
                description="Stoic fate",
            ),
        ]
        state.context_pack = ContextPack(
            bundle_refs={"bundle-1": "P1"},
            node_refs={"node-1": "1"},
            passage_bundles=[
                EvidenceBundle(
                    bundle_id="bundle-1",
                    work_id="work-1",
                    work_title="De Fato",
                    author="Cicero",
                    canonical_ref="Fat. 1",
                    original_passage_id="p1",
                    original_text="Fate is a chain of causes.",
                    translation_text="Fatum is a chain of causes.",
                    token_estimate=20,
                )
            ],
        )
        state.claim_ledger = [
            ClaimLedgerItem(
                claim="Claim",
                evidence_ids=["node-1", "bundle-1"],
                support_type="passage",
            ),
        ]

        packet = _render_evidence_packet(state)

        assert [item["type"] for item in packet] == ["metadata", "passage"]
        assert packet[1]["ref"] == "P1"

    def test_claim_reference_markers_prefer_passages_for_passage_backed_claims(self):
        state = RAGState(question="What did Justin believe about free will?")
        state.context_pack = ContextPack(
            bundle_refs={"bundle-1": "P1"},
            node_refs={"node-1": "1"},
        )
        item = ClaimLedgerItem(
            claim="Justin defends free choice against fatalism.",
            evidence_ids=["bundle-1", "node-1"],
            support_type="passage",
            confidence=0.9,
            status=ClaimStatus.SUPPORTED,
        )

        assert _claim_reference_markers(state, item) == ["[P1]"]

    def test_normalize_reference_markers_repairs_nested_ref_blocks(self):
        line = "Origen reconciles providence and freedom [P14, [3]]."

        assert (
            _normalize_reference_markers(line, ["P14", "3"])
            == "Origen reconciles providence and freedom [P14, 3]."
        )

    def test_verify_preserves_bilingual_quote_block_when_only_one_line_has_ref(self):
        state = RAGState(question="Quote Justin on fate.")
        bundle = EvidenceBundle(
            bundle_id="bundle-1",
            work_id="work-1",
            work_title="Apologia Prima",
            author="Justin Martyr",
            canonical_ref="43",
            original_passage_id="p1",
            original_text="εἰ γὰρ εἵμαρται τόνδε τινὰ ἀγαθὸν εἶναι",
            translation_text="For if it were fated that this man be good",
            token_estimate=20,
        )
        state.context_pack = ContextPack(
            bundle_refs={"bundle-1": "P1"},
            passage_bundles=[bundle],
        )
        state.raw_answer = "\n".join(
            [
                "### Textual Basis",
                "> εἰ γὰρ εἵμαρται τόνδε τινὰ ἀγαθὸν εἶναι",
                ">",
                '> "For if it were fated that this man be good" [P1]',
            ]
        )

        answer, citations = _verify_answer_programmatically(state)

        assert "> εἰ γὰρ εἵμαρται τόνδε τινὰ ἀγαθὸν εἶναι [P1]" in answer
        assert '> "For if it were fated that this man be good" [P1]' in answer
        assert citations[0].ref == "P1"

    def test_augment_claim_ledger_from_dossier_adds_missing_facets_and_quotes(self):
        state = RAGState(
            question="What did Justin Martyr believe about free will and moral responsibility?"
        )
        state.query_type = QueryType.GLOBAL_ABSTRACT
        state.research_notebook.facets = [
            ResearchFacet(
                facet_id="core_doctrinal_thesis",
                title="Core Doctrinal Thesis",
                question="What is Justin's core thesis?",
                keywords=["justin", "free will"],
                priority=1,
            ),
            ResearchFacet(
                facet_id="agency_and_responsibility",
                title="Agency and Responsibility",
                question="How does Justin connect freedom to praise and blame?",
                keywords=["responsibility", "praise", "blame"],
                priority=2,
            ),
        ]
        state.evidence_bundles = [
            EvidenceBundle(
                bundle_id="bundle-1",
                work_id="work-1",
                work_title="Apologia Prima",
                author="Justin Martyr",
                original_passage_id="p1",
                original_text="If all things happen by fate, there is nothing up to us.",
                translation_text="If everything happens by fate, nothing is up to us.",
                token_estimate=20,
            ),
            EvidenceBundle(
                bundle_id="bundle-2",
                work_id="work-2",
                work_title="Dialogus cum Tryphone",
                author="Justin Martyr",
                original_passage_id="p2",
                original_text="God made angels and humans with free choice and self-determination.",
                translation_text="God made angels and humans with free choice.",
                token_estimate=20,
            ),
        ]
        state.context_pack = ContextPack(
            bundle_refs={"bundle-1": "P1", "bundle-2": "P2"},
            passage_bundles=state.evidence_bundles,
        )
        _build_scholarly_dossier(state)

        augmented = _augment_claim_ledger_from_dossier(
            state,
            [
                ClaimLedgerItem(
                    claim="Justin rejects fatalism in order to preserve what is up to us.",
                    evidence_ids=["bundle-1"],
                    facet_id="core_doctrinal_thesis",
                    support_type="passage",
                    confidence=0.9,
                    status=ClaimStatus.SUPPORTED,
                )
            ],
        )

        assert len({item.facet_id for item in augmented if item.facet_id}) >= 2
        assert any(item.quote_original for item in augmented)

    def test_build_research_graph_payload_exposes_stages_facets_works_and_claims(self):
        state = RAGState(question="What did the Stoics believe about fate?")
        state.metadata.update(
            {
                "query_type": "global_abstract",
                "classification_confidence": 0.91,
                "classification_reason": "llm classifier",
                "claim_ledger_mode": "llm",
                "render_answer_mode": "llm",
                "selected_sections": [
                    {
                        "work_id": "work-1",
                        "node_id": "section-1",
                        "title": "Fate and causation",
                        "path": "Book 1 > Section 1",
                    }
                ],
            }
        )
        state.primary_evidence = [
            Evidence(
                id="node-1", label="Stoicism", type="school", description="Stoic school"
            ),
        ]
        state.research_notebook.question_frame = (
            "Stoic doctrine of fate and responsibility"
        )
        state.research_notebook.facets = (
            [state.research_notebook.facets[0]]
            if state.research_notebook.facets
            else []
        )
        if not state.research_notebook.facets:
            from eleutheria_graphrag.agents.state import ResearchFacet

            state.research_notebook.facets = [
                ResearchFacet(
                    facet_id="definition",
                    title="Definition of fate",
                    question="How do the Stoics define fate?",
                    keywords=["fate", "heimarmene"],
                    required_support="passage",
                    priority=1,
                )
            ]
        state.research_notebook.competing_hypotheses = [
            "Stoic fate is providential determinism."
        ]
        state.research_notebook.open_questions = [
            "How does assent preserve responsibility?"
        ]
        state.evidence_bundles = [
            EvidenceBundle(
                bundle_id="bundle-1",
                work_id="work-1",
                work_title="De Fato",
                author="Cicero",
                section_path="Book 1 > Section 1",
                canonical_ref="1.1",
                original_passage_id="p1",
                original_text="Fate is a chain of causes.",
                translation_text="Fate is an ordered sequence of causes.",
                language="lat",
                token_estimate=20,
                metadata={"evidence_class": "direct_text"},
            )
        ]
        state.context_pack = ContextPack(
            bundle_refs={"bundle-1": "P1"},
            node_refs={"node-1": "1"},
            passage_bundles=state.evidence_bundles,
        )
        state.claim_ledger = [
            ClaimLedgerItem(
                claim="Stoic fate is a rational chain of causes.",
                evidence_ids=["bundle-1"],
                facet_id="definition",
                evidence_class="direct_text",
                support_type="passage",
                confidence=0.92,
                status=ClaimStatus.SUPPORTED,
            )
        ]
        state.research_notebook.tool_calls = [
            ResearchToolCall(
                tool_call_id="discover_corpus:search_entities:1",
                tool_name="search_entities",
                stage_id="discover_corpus",
                query="Stoic fate heimarmene",
                selected_ids=["node-1"],
                detail_count=1,
            )
        ]
        state.research_notebook.reading_decisions = [
            ReadingDecision(
                decision_id="tree_navigation:section_selection:1",
                stage_id="tree_navigation",
                decision_type="section_selection",
                title="Select sections in De Fato",
                rationale="Best coverage for definition of fate.",
                selected_ids=["section-1"],
                supporting_refs=["P1"],
            )
        ]
        state.quality_badge = "High"
        state.citations = []

        from eleutheria_graphrag.agents.graph_nodes import _trace_stage

        _trace_stage(
            state,
            "classify_query",
            {"mode": "llm", "query_type": "global_abstract", "confidence": 0.91},
        )
        _trace_stage(
            state,
            "discover_corpus",
            {
                "semantic_hits": [{"id": "node-1"}],
                "seed_node_ids": ["node-1"],
                "passage_anchor_ids": ["node-1"],
                "linked_passages": [{"passage_id": "p1"}],
            },
        )

        payload = _build_research_graph_payload(state)

        assert payload["overview"]["claim_count"] == 1
        assert payload["stages"][0]["id"] == "classify_query"
        assert any(stage["id"] == "discover_corpus" for stage in payload["stages"])
        assert payload["facets"][0]["facet_id"] == "definition"
        assert payload["works"][0]["work_id"] == "work-1"
        assert payload["claims"][0]["refs"] == ["P1"]
        assert payload["overview"]["tool_call_count"] == 1
        assert payload["overview"]["decision_count"] == 1
        assert payload["tool_calls"][0]["tool_name"] == "search_entities"
        assert payload["reading_decisions"][0]["decision_type"] == "section_selection"

    @pytest.mark.asyncio
    async def test_fetch_translation_falls_back_to_kg_node_description(self):
        deps = make_deps(
            node_lookup={
                "passage_grc_1": {
                    "id": "passage_grc_1",
                    "label": "Original passage",
                    "type": "passage",
                },
                "passage_grc_1_en": {
                    "id": "passage_grc_1_en",
                    "label": "Original passage (English)",
                    "type": "passage",
                    "description": "English translation text.",
                    "metadata": {
                        "language": "eng",
                        "canonical_ref": "1.1",
                        "author": "Alexander",
                        "work_title": "De Fato",
                    },
                },
            },
            outgoing_edges={
                "passage_grc_1_en": [
                    {
                        "source": "passage_grc_1_en",
                        "target": "passage_grc_1",
                        "relation": "translation_of",
                    }
                ]
            },
            incoming_edges={
                "passage_grc_1": [
                    {
                        "source": "passage_grc_1_en",
                        "target": "passage_grc_1",
                        "relation": "translation_of",
                    }
                ]
            },
        )
        deps.db.fetch = AsyncMock(
            side_effect=[
                [{"kg_node_id": "passage_grc_1"}],
                [],
            ]
        )

        translation = await _fetch_translation_for_passage(deps, "p1")

        assert translation is not None
        assert translation["text_content"] == "English translation text."
        assert translation["passage_id"] is None
        assert translation["kg_node_id"] == "passage_grc_1_en"
        assert translation["language"] == "eng"
        assert all(
            "citation_type = 'snapshot_passage_node'" in call.args[0]
            for call in deps.db.fetch.await_args_list
        )

    def test_build_research_graph_work_card_classifies_testimony_bundles_correctly(
        self,
    ):
        """Work cards must count testimony bundles under testimony_count, not primary_count."""
        state = RAGState(question="What did the Stoics believe about fate?")
        testimony_bundle = EvidenceBundle(
            bundle_id="bundle-dl",
            work_id="work_diogenes_laertius",
            work_title="Lives of Eminent Philosophers",
            author="Diogenes Laertius",
            original_passage_id="p1",
            canonical_ref="7.1",
            original_text="Zeno of Citium was the founder of Stoicism.",
            token_estimate=20,
        )
        state.context_pack = ContextPack(
            bundle_refs={"bundle-dl": "P1"},
            passage_bundles=[testimony_bundle],
        )
        state.evidence_bundles = [testimony_bundle]
        state.scholarly_dossier = ScholarlyDossier(
            facets=[
                DossierFacet(
                    facet_id="f1",
                    title="Main thesis",
                    question="Q",
                    primary_bundle_ids=["bundle-dl"],
                )
            ]
        )
        payload = _build_research_graph_payload(state)
        works = payload["works"]
        assert len(works) == 1
        work = works[0]
        assert work["testimony_count"] == 1
        assert work["primary_count"] == 0


class TestBuildResearchNotebook:
    @pytest.mark.asyncio
    async def test_populates_notebook(self):
        deps = make_deps(
            llm_response='{"question_frame": "Stoic doctrine of fate", "sub_questions": ["What is heimarmene?"], "competing_hypotheses": ["Stoic doctrine is internally consistent"], "open_questions": ["Does Epictetus shift emphasis?"]}'
        )
        state = RAGState(question="What did the Stoics believe about fate?")
        state.primary_evidence = [
            Evidence(id="n1", label="Chrysippus", type="Person"),
            Evidence(id="n2", label="De Fato", type="Work"),
        ]
        ctx = make_ctx(state, deps)

        result = await BuildResearchNotebook().run(ctx)

        assert isinstance(result, PlanReading)
        assert state.research_notebook.question_frame == "Stoic doctrine of fate"
        assert state.sub_queries == ["What is heimarmene?"]
        assert "De Fato" in state.research_notebook.work_priorities
        assert state.research_notebook.facets

    @pytest.mark.asyncio
    async def test_specific_entity_uses_heuristic_notebook_without_llm(self):
        deps = make_deps()
        state = RAGState(question="Who was Chrysippus?")
        state.query_type = QueryType.SPECIFIC_ENTITY
        state.complexity = QueryComplexity.SIMPLE
        state.primary_evidence = [Evidence(id="n1", label="Chrysippus", type="Person")]
        ctx = make_ctx(state, deps)

        result = await BuildResearchNotebook().run(ctx)

        assert isinstance(result, PlanReading)
        deps.llm.generate.assert_not_called()
        assert state.research_notebook.question_frame == "Who was Chrysippus?"
        assert state.research_notebook.facets


class TestClassifyQueryType:
    @pytest.mark.asyncio
    async def test_who_query_uses_deterministic_heuristic(self):
        deps = make_deps()
        state = RAGState(question="Who was Chrysippus?")
        ctx = make_ctx(state, deps)

        result = await ClassifyQueryType().run(ctx)

        assert result.__class__.__name__ == "ExpandQuery"
        deps.llm.generate.assert_not_called()
        assert state.query_type == QueryType.SPECIFIC_ENTITY
        assert state.metadata["classification_reason"] == "deterministic heuristic"


class _FakeStrategy:
    """Minimal retrieval strategy double for DiscoverCorpus tests."""

    def __init__(self, seeds: list[str], anchors: list[str]) -> None:
        self._seeds = seeds
        self._anchors = anchors

    async def discover_seeds(self, queries, deps, node_limit=100):  # noqa: ARG002
        return list(self._seeds), list(self._anchors)


class TestDiscoverCorpus:
    @pytest.mark.asyncio
    async def test_discovers_nodes_and_passages(self):
        deps = make_deps(
            db_fetch_results=[
                {
                    "passage_id": "p1",
                    "work_id": "work-1",
                    "text_content": "Fate is a chain of causes.",
                    "canonical_ref": "1.1",
                    "sequence_number": 1,
                    "title": "De Fato",
                    "author": "Chrysippus",
                    "language": "grc",
                    "confidence": 0.9,
                }
            ],
        )
        deps.node_lookup["chrysippus"]["type"] = "Person"
        deps.retrieval_strategy = _FakeStrategy(
            seeds=["chrysippus"], anchors=["chrysippus"]
        )
        state = RAGState(question="Who was Chrysippus?")
        state.expanded_query = "Chrysippus"
        ctx = make_ctx(state, deps)

        result = await DiscoverCorpus().run(ctx)

        assert result.__class__.__name__ == "BuildResearchNotebook"
        assert any(ev.id == "chrysippus" for ev in state.primary_evidence)
        assert any(ev.type == "passage" for ev in state.primary_evidence)
        assert any(
            call.tool_name == "search_entities"
            for call in state.research_notebook.tool_calls
        )
        assert any(
            decision.decision_type == "seed_selection"
            for decision in state.research_notebook.reading_decisions
        )

    @pytest.mark.asyncio
    async def test_fetches_linked_passages_from_seed_anchors_not_full_context(self):
        deps = make_deps(
            node_lookup={
                "chrysippus": {
                    "id": "chrysippus",
                    "label": "Chrysippus",
                    "type": "person",
                    "description": "Stoic philosopher",
                },
                "justin": {
                    "id": "justin",
                    "label": "Justin Martyr",
                    "type": "person",
                    "description": "Christian apologist",
                },
            },
            outgoing_edges={
                "chrysippus": [{"source": "chrysippus", "target": "justin"}],
            },
            incoming_edges={
                "justin": [{"source": "chrysippus", "target": "justin"}],
            },
            db_fetch_results=[],
        )
        deps.retrieval_strategy = _FakeStrategy(
            seeds=["chrysippus"], anchors=["chrysippus"]
        )
        state = RAGState(question="Who was Chrysippus?")
        state.expanded_query = "Chrysippus"
        ctx = make_ctx(state, deps)

        await DiscoverCorpus().run(ctx)

        fetch_args = deps.db.fetch.await_args.args
        assert fetch_args[1:] == ("chrysippus",)
        assert state.metadata["passage_anchor_ids"] == ["chrysippus"]


class TestTreeNavigateWorks:
    @pytest.mark.asyncio
    async def test_selects_sections_from_tree_index(self):
        deps = make_deps(
            llm_response='{"selected_nodes": [{"work_id": "work-1", "node_id": "chapter_1", "title": "Book 1, Chapter 1", "path": "Book 1 > Chapter 1", "reason": "directly relevant", "priority": 1}], "reasoning": "chapter on fate"}'
        )
        deps.tree_index = AsyncMock()
        deps.tree_index.resolve_work_ids = AsyncMock(return_value=["work-1"])
        deps.tree_index.load_indices = AsyncMock(
            return_value=[
                WorkTreeIndex(
                    work_id="work-1",
                    title="De Fato",
                    author="Cicero",
                    total_passages=10,
                    nodes=[
                        TreeNode(
                            node_id="chapter_1",
                            title="Book 1, Chapter 1",
                            start_passage=1,
                            end_passage=5,
                            summary="Discussion of fate",
                            path="Book 1 > Chapter 1",
                            canonical_refs=["1.1"],
                            abstract="Discussion of fate and causation",
                        )
                    ],
                )
            ]
        )
        state = RAGState(question="What is fate in Cicero?")
        state.pipeline_config = PipelineConfig(use_tree_reasoning=True)
        state.research_notebook.work_priorities = ["De Fato"]
        state.primary_evidence = [Evidence(id="w1", label="De Fato", type="Work")]
        ctx = make_ctx(state, deps)

        result = await TreeNavigateWorks().run(ctx)

        assert result.__class__.__name__ == "ExpandEvidenceBundles"
        assert state.metadata["selected_sections"][0]["node_id"] == "chapter_1"


class TestExpandEvidenceBundles:
    @pytest.mark.asyncio
    async def test_builds_evidence_bundles_and_context_pack(self):
        deps = make_deps()
        deps.tree_index = AsyncMock()
        deps.tree_index.load_indices = AsyncMock(
            return_value=[
                WorkTreeIndex(
                    work_id="work-1",
                    title="De Fato",
                    author="Cicero",
                    total_passages=10,
                    nodes=[],
                )
            ]
        )
        deps.tree_index.extract_passages = AsyncMock(
            return_value=[
                {
                    "passage_id": "p1",
                    "work_id": "work-1",
                    "text_content": "Fate is an ordered sequence of causes.",
                    "canonical_ref": "1.1",
                    "sequence_number": 1,
                    "title": "De Fato",
                    "author": "Cicero",
                    "language": "lat",
                }
            ]
        )
        deps.db.fetch = AsyncMock(return_value=[])

        state = RAGState(question="What is fate?")
        state.metadata["selected_sections"] = [
            {
                "work_id": "work-1",
                "node_id": "chapter_1",
                "path": "Book 1 > Chapter 1",
                "summary": "Discussion of fate",
            }
        ]
        ctx = make_ctx(state, deps)

        result = await ExpandEvidenceBundles().run(ctx)

        assert result.__class__.__name__ == "SeekCounterEvidence"
        assert len(state.evidence_bundles) == 1
        assert state.context_pack.passage_bundles[0].bundle_id == "work-1::p1"
        assert "[P1]" in state.context_pack.prompt_context

    @pytest.mark.asyncio
    async def test_uses_translation_node_fallback_without_fake_passage_id(self):
        deps = make_deps(
            node_lookup={
                "passage_grc_1": {
                    "id": "passage_grc_1",
                    "label": "Original passage",
                    "type": "passage",
                },
                "passage_grc_1_en": {
                    "id": "passage_grc_1_en",
                    "label": "Original passage (English)",
                    "type": "passage",
                    "description": "English translation text.",
                    "metadata": {
                        "language": "eng",
                        "canonical_ref": "1.1",
                        "author": "Alexander",
                        "work_title": "De Fato",
                    },
                },
            },
            outgoing_edges={
                "passage_grc_1_en": [
                    {
                        "source": "passage_grc_1_en",
                        "target": "passage_grc_1",
                        "relation": "translation_of",
                    }
                ]
            },
            incoming_edges={
                "passage_grc_1": [
                    {
                        "source": "passage_grc_1_en",
                        "target": "passage_grc_1",
                        "relation": "translation_of",
                    }
                ]
            },
        )
        deps.tree_index = AsyncMock()
        deps.tree_index.load_indices = AsyncMock(
            return_value=[
                WorkTreeIndex(
                    work_id="work-1",
                    title="De Fato",
                    author="Alexander",
                    total_passages=10,
                    nodes=[],
                )
            ]
        )
        deps.tree_index.extract_passages = AsyncMock(
            return_value=[
                {
                    "passage_id": "p1",
                    "work_id": "work-1",
                    "text_content": "Greek text.",
                    "canonical_ref": "1.1",
                    "sequence_number": 1,
                    "title": "De Fato",
                    "author": "Alexander",
                    "language": "grc",
                }
            ]
        )
        deps.db.fetch = AsyncMock(
            side_effect=[
                [{"passage_id": "p1", "kg_node_id": "passage_grc_1"}],
                [],
            ]
        )

        state = RAGState(question="What does Alexander say?")
        state.metadata["selected_sections"] = [
            {
                "work_id": "work-1",
                "node_id": "chapter_1",
                "path": "Book 1 > Chapter 1",
                "summary": "Discussion of fate",
            }
        ]
        ctx = make_ctx(state, deps)

        result = await ExpandEvidenceBundles().run(ctx)

        assert result.__class__.__name__ == "SeekCounterEvidence"
        bundle = state.evidence_bundles[0]
        assert bundle.translation_text == "English translation text."
        assert bundle.translation_passage_id is None
        assert bundle.metadata["translation_source"] == "kg_node_description"
        assert bundle.metadata["translation_node_id"] == "passage_grc_1_en"

    @pytest.mark.asyncio
    async def test_merges_tree_bundles_with_linked_passage_bundles(self):
        deps = make_deps()
        deps.tree_index = AsyncMock()
        deps.tree_index.load_indices = AsyncMock(
            return_value=[
                WorkTreeIndex(
                    work_id="work-1",
                    title="De Fato",
                    author="Cicero",
                    total_passages=10,
                    nodes=[],
                )
            ]
        )
        deps.tree_index.extract_passages = AsyncMock(
            return_value=[
                {
                    "passage_id": "p1",
                    "work_id": "work-1",
                    "text_content": "Fate is a chain of causes.",
                    "canonical_ref": "Fat. 41",
                    "sequence_number": 1,
                    "title": "De Fato",
                    "author": "Cicero",
                    "language": "lat",
                }
            ]
        )
        deps.db.fetch = AsyncMock(return_value=[])

        state = RAGState(
            question="What did the Stoics believe about fate and moral responsibility?"
        )
        state.metadata["selected_sections"] = [
            {
                "work_id": "work-1",
                "node_id": "chapter_1",
                "path": "Book 1 > Chapter 1",
                "summary": "Discussion of fate",
            }
        ]
        state.primary_evidence = [
            Evidence(
                id="p-epictetus",
                passage_id="p-epictetus",
                label="Epictetus, Ench. 1.1",
                type="passage",
                source=EvidenceSource.PASSAGE_CITATION,
                work_id="work-2",
                work_title="Enchiridion",
                author="Epictetus",
                canonical_ref="Ench. 1.1",
                text_content="Some things are up to us and some are not.",
                language="eng",
                confidence=0.92,
            )
        ]
        ctx = make_ctx(state, deps)

        result = await ExpandEvidenceBundles().run(ctx)

        assert result.__class__.__name__ == "SeekCounterEvidence"
        assert {bundle.work_title for bundle in state.evidence_bundles} == {
            "De Fato",
            "Enchiridion",
        }
        assert len(state.context_pack.passage_bundles) == 2

    def test_context_pack_prioritizes_query_relevant_bundles(self):
        state = RAGState(question="Who was Chrysippus?")
        state.evidence_bundles = [
            EvidenceBundle(
                bundle_id="bundle-justin",
                work_id="work-justin",
                work_title="Apologia Prima",
                author="Justin Martyr",
                original_passage_id="p-justin",
                original_text="Justin discusses Christian doctrine.",
                token_estimate=20,
                source=EvidenceSource.PASSAGE_CITATION,
            ),
            EvidenceBundle(
                bundle_id="bundle-chrysippus",
                work_id="work-chrysippus",
                work_title="On Fate",
                author="Chrysippus",
                original_passage_id="p-chrysippus",
                original_text="Chrysippus was the third head of the Stoic school.",
                token_estimate=20,
                source=EvidenceSource.PASSAGE_CITATION,
            ),
        ]

        pack = _build_context_pack(state)

        assert [bundle.bundle_id for bundle in pack.passage_bundles][:2] == [
            "bundle-chrysippus",
            "bundle-justin",
        ]
        assert (
            state.metadata["debug_trace"]["context_pack"]["top_bundle_rankings"][0][
                "bundle_id"
            ]
            == "bundle-chrysippus"
        )

    def test_context_pack_diversifies_across_works_before_repeating_same_work(self):
        state = RAGState(
            question="What did the Stoics believe about fate and moral responsibility?"
        )
        state.evidence_bundles = [
            EvidenceBundle(
                bundle_id="bundle-cicero-1",
                work_id="work-cicero",
                work_title="De Fato",
                author="Cicero",
                original_passage_id="p1",
                original_text="Cicero reports Chrysippus on fate.",
                token_estimate=15,
                source=EvidenceSource.PASSAGE_CITATION,
            ),
            EvidenceBundle(
                bundle_id="bundle-cicero-2",
                work_id="work-cicero",
                work_title="De Fato",
                author="Cicero",
                original_passage_id="p2",
                original_text="Cicero reports the cylinder analogy.",
                token_estimate=15,
                source=EvidenceSource.PASSAGE_CITATION,
            ),
            EvidenceBundle(
                bundle_id="bundle-cicero-3",
                work_id="work-cicero",
                work_title="De Fato",
                author="Cicero",
                original_passage_id="p3",
                original_text="Cicero reports antecedent causes.",
                token_estimate=15,
                source=EvidenceSource.PASSAGE_CITATION,
            ),
            EvidenceBundle(
                bundle_id="bundle-epictetus",
                work_id="work-epictetus",
                work_title="Discourses",
                author="Epictetus",
                original_passage_id="p4",
                original_text="Some things are up to us and some are not.",
                token_estimate=15,
                source=EvidenceSource.PASSAGE_CITATION,
            ),
        ]

        pack = _build_context_pack(state)

        assert [bundle.bundle_id for bundle in pack.passage_bundles[:3]] == [
            "bundle-cicero-1",
            "bundle-cicero-2",
            "bundle-epictetus",
        ]

    def test_scholarly_dossier_distinguishes_direct_text_from_testimony(self):
        state = RAGState(
            question="What did the Stoics believe about fate and moral responsibility?"
        )
        state.research_notebook.work_priorities = ["Discourses", "De Fato"]
        state.research_notebook.facets = state.research_notebook.facets or []
        state.primary_evidence = [
            Evidence(
                id="epictetus",
                label="Epictetus",
                type="Person",
                school="Stoicism",
                period="Imperial",
            ),
            Evidence(
                id="cicero",
                label="Cicero",
                type="Person",
                school="Academic Skepticism",
                period="Late Republic",
            ),
        ]
        state.evidence_bundles = [
            EvidenceBundle(
                bundle_id="bundle-epictetus",
                work_id="work-1",
                work_title="Discourses",
                author="Epictetus",
                original_passage_id="p1",
                original_text="Some things are up to us and some are not.",
                token_estimate=20,
            ),
            EvidenceBundle(
                bundle_id="bundle-cicero",
                work_id="work-2",
                work_title="De Fato",
                author="Cicero",
                original_passage_id="p2",
                original_text="Chrysippus distinguishes kinds of causes.",
                token_estimate=20,
            ),
        ]

        dossier = _build_scholarly_dossier(state)

        assert dossier.primary_bundle_ids[0] == "bundle-epictetus"
        assert "bundle-cicero" in dossier.testimony_bundle_ids


class TestEvidenceSufficiency:
    @pytest.mark.asyncio
    async def test_loops_once_when_insufficient_with_refinement(self):
        deps = make_deps(
            llm_response='{"score": 0.2, "sufficient": false, "reason": "missing Epictetus", "refinement": "Epictetus on fate"}'
        )
        state = RAGState(question="Compare Chrysippus and Epictetus on fate")
        state.pipeline_config = PipelineConfig(use_tree_reasoning=True)
        state.iteration = 0
        ctx = make_ctx(state, deps)

        result = await EvidenceSufficiency().run(ctx)

        assert result.__class__.__name__ == "DiscoverCorpus"
        assert state.sub_queries == ["Epictetus on fate"]
        assert state.insufficient_evidence is True

    @pytest.mark.asyncio
    async def test_proceeds_to_claim_ledger_when_sufficient(self):
        deps = make_deps(
            llm_response='{"score": 0.8, "sufficient": true, "reason": "enough coverage"}'
        )
        state = RAGState(question="What is Stoic fate?")
        state.context_pack = ContextPack(
            passage_bundles=[
                EvidenceBundle(
                    bundle_id="work-1::p1",
                    work_id="work-1",
                    work_title="De Fato",
                    original_passage_id="p1",
                    original_text="Fate is a chain of causes.",
                    token_estimate=20,
                )
            ]
        )
        ctx = make_ctx(state, deps)

        result = await EvidenceSufficiency().run(ctx)

        assert isinstance(result, DraftClaimLedger)
        assert state.insufficient_evidence is False
        assert state.sufficiency_score >= 0.8


class TestRenderAndVerify:
    def test_render_answer_fallback_uses_sectioned_scholarly_structure(self):
        state = RAGState(question="What did the Stoics believe about fate?")
        state.scholarly_dossier.facets = [
            DossierFacet(
                facet_id="core_doctrinal_thesis",
                title="Core Doctrinal Thesis",
                question="What core thesis is defended?",
            )
        ]
        state.context_pack = ContextPack(bundle_refs={"bundle-1": "P1"})
        state.claim_ledger = [
            ClaimLedgerItem(
                claim="Stoic fate is an ordered chain of causes.",
                evidence_ids=["bundle-1"],
                facet_id="core_doctrinal_thesis",
                quote_original="fatum est series causarum",
                quote_translation="fate is a sequence of causes",
                support_type="passage",
                confidence=0.9,
                status=ClaimStatus.SUPPORTED,
            )
        ]

        rendered = _render_answer_fallback(state)

        assert "### Core Doctrinal Thesis" in rendered
        assert '> Original: "fatum est series causarum" [P1]' in rendered
        # The faceted section carries the claim directly (no separate intro
        # line that would duplicate it verbatim).
        assert "Stoic fate is an ordered chain of causes [P1]" in rendered
        # The intro recap is now suppressed when sections will carry the
        # claim — preventing the duplication that produced the production
        # "repetitive" rendering.
        assert rendered.count("Stoic fate is an ordered chain of causes") == 1

    def test_render_answer_fallback_assigns_distinct_claims_to_each_section(self):
        """Regression: when claims have no facet_id, the fallback used to
        emit one section with content + several empty sections (looked
        repetitive in production). Each section now gets a *distinct*
        claim where possible, and empty sections receive a neutral note."""
        state = RAGState(question="Compare Bobzien and Frede on Stoic compatibilism.")
        state.scholarly_dossier.facets = [
            DossierFacet(
                facet_id="core_doctrinal_thesis",
                title="Core Doctrinal Thesis",
                question="Q1",
            ),
            DossierFacet(
                facet_id="textual_witnesses",
                title="Textual Witnesses",
                question="Q2",
            ),
            DossierFacet(
                facet_id="counterpoints",
                title="Counterpoints and Limits",
                question="Q3",
            ),
        ]
        state.context_pack = ContextPack(
            bundle_refs={"bundle-1": "P1", "bundle-2": "P2"}
        )
        # Two unfaceted claims — should land in the first two facets.
        state.claim_ledger = [
            ClaimLedgerItem(
                claim="Bobzien reads Stoic doctrine as compatibilist about responsibility.",
                evidence_ids=["bundle-1"],
                facet_id=None,
                support_type="passage",
                confidence=0.9,
                status=ClaimStatus.SUPPORTED,
            ),
            ClaimLedgerItem(
                claim="Frede stresses the moralised conception of freedom in later Stoicism.",
                evidence_ids=["bundle-2"],
                facet_id=None,
                support_type="passage",
                confidence=0.9,
                status=ClaimStatus.SUPPORTED,
            ),
        ]

        rendered = _render_answer_fallback(state)

        # Both distinct claims appear, in the two filled sections.
        assert "Bobzien reads Stoic doctrine" in rendered
        assert "Frede stresses the moralised conception" in rendered
        # The third (empty) facet must still appear, with a neutral note —
        # NOT a recycled copy of the first claim.
        assert "### Counterpoints and Limits" in rendered
        assert "No direct evidence catalogued" in rendered
        # Neither claim should appear more than once.
        assert rendered.count("Bobzien reads Stoic doctrine") == 1
        assert rendered.count("Frede stresses the moralised conception") == 1
        # The "Section: claim" anti-pattern must not appear.
        assert "Textual Witnesses: " not in rendered
        assert "Counterpoints and Limits: " not in rendered

    def test_render_answer_fallback_strips_section_title_prefix(self):
        """When the LLM prefixes a claim with the facet title, strip it."""
        state = RAGState(question="What did Justin argue?")
        state.scholarly_dossier.facets = [
            DossierFacet(
                facet_id="textual_witnesses",
                title="Textual Witnesses",
                question="Q",
            )
        ]
        state.context_pack = ContextPack(bundle_refs={"bundle-1": "P1"})
        state.claim_ledger = [
            ClaimLedgerItem(
                claim="Textual Witnesses: Justin defends what is up to us.",
                evidence_ids=["bundle-1"],
                facet_id="textual_witnesses",
                support_type="passage",
                confidence=0.9,
                status=ClaimStatus.SUPPORTED,
            )
        ]
        rendered = _render_answer_fallback(state)
        assert "### Textual Witnesses" in rendered
        assert "Textual Witnesses: Justin defends" not in rendered
        assert "Justin defends what is up to us" in rendered

    @pytest.mark.asyncio
    async def test_render_then_verify_keeps_grounded_lines(self):
        deps = make_deps(
            llm_response="- Stoic fate is described as a chain of causes [P1]"
        )
        state = RAGState(question="What is Stoic fate?")
        state.context_pack = ContextPack(
            bundle_refs={"bundle-1": "P1"},
            passage_bundles=[
                EvidenceBundle(
                    bundle_id="bundle-1",
                    work_id="work-1",
                    work_title="De Fato",
                    author="Cicero",
                    original_passage_id="p1",
                    canonical_ref="1.1",
                    original_text="Fate is a chain of causes.",
                    token_estimate=20,
                )
            ],
        )
        state.claim_ledger = [
            ClaimLedgerItem(
                claim="Stoic fate is described as a chain of causes.",
                evidence_ids=["bundle-1"],
                quote_original="Fate is a chain of causes.",
                support_type="passage",
                confidence=0.9,
                status=ClaimStatus.SUPPORTED,
            )
        ]
        ctx = make_ctx(state, deps)

        render_result = await RenderGroundedAnswer().run(ctx)
        assert isinstance(render_result, ProgrammaticVerify)

        verify_result = await ProgrammaticVerify().run(ctx)
        assert isinstance(verify_result, End)
        answer = verify_result.data
        assert "[P1]" in answer.answer
        assert answer.citations[0].ref == "P1"

    @pytest.mark.asyncio
    async def test_render_grounded_answer_repairs_overcompressed_output(self):
        deps = make_deps()
        # Compression repair is now disabled — only render + optional polish
        deps.llm.generate = AsyncMock(
            side_effect=[
                'Opening thesis on Justin\'s doctrine [P1].\n\n### Core Doctrinal Thesis\nJustin rejects fatalism and defends what is up to us [P1].\n> Original: "If everything happens by fate, nothing is up to us." [P1]\n> Translation: "If everything happens by fate, nothing is up to us." [P1]\n\n### Agency and Responsibility\nJustin links free choice to praise and blame before divine judgment [P2].',
            ]
        )
        state = RAGState(
            question="What did Justin Martyr believe about free will and moral responsibility?"
        )
        state.query_type = QueryType.GLOBAL_ABSTRACT
        state.research_notebook.facets = [
            ResearchFacet(
                facet_id="core_doctrinal_thesis",
                title="Core Doctrinal Thesis",
                question="What is Justin's core thesis?",
                keywords=["justin", "free will"],
                priority=1,
            ),
            ResearchFacet(
                facet_id="agency_and_responsibility",
                title="Agency and Responsibility",
                question="How does Justin connect freedom to responsibility?",
                keywords=["responsibility", "free choice"],
                priority=2,
            ),
        ]
        state.evidence_bundles = [
            EvidenceBundle(
                bundle_id="bundle-1",
                work_id="work-1",
                work_title="Apologia Prima",
                author="Justin Martyr",
                original_passage_id="p1",
                original_text="If everything happens by fate, nothing is up to us.",
                translation_text="If everything happens by fate, nothing is up to us.",
                token_estimate=20,
            ),
            EvidenceBundle(
                bundle_id="bundle-2",
                work_id="work-2",
                work_title="Dialogus cum Tryphone",
                author="Justin Martyr",
                original_passage_id="p2",
                original_text="God made angels and humans with free choice.",
                translation_text="God made angels and humans with free choice.",
                token_estimate=20,
            ),
        ]
        state.context_pack = ContextPack(
            bundle_refs={"bundle-1": "P1", "bundle-2": "P2"},
            passage_bundles=state.evidence_bundles,
        )
        _build_scholarly_dossier(state)
        state.claim_ledger = [
            ClaimLedgerItem(
                claim="Justin rejects fatalism to preserve what is up to us.",
                evidence_ids=["bundle-1"],
                facet_id="core_doctrinal_thesis",
                quote_original="If everything happens by fate, nothing is up to us.",
                quote_translation="If everything happens by fate, nothing is up to us.",
                support_type="passage",
                confidence=0.9,
                status=ClaimStatus.SUPPORTED,
            ),
            ClaimLedgerItem(
                claim="Justin grounds praise and blame in free choice.",
                evidence_ids=["bundle-2"],
                facet_id="agency_and_responsibility",
                support_type="passage",
                confidence=0.88,
                status=ClaimStatus.SUPPORTED,
            ),
        ]
        ctx = make_ctx(state, deps)

        render_result = await RenderGroundedAnswer().run(ctx)

        assert isinstance(render_result, ProgrammaticVerify)
        assert state.metadata["compression_repair_mode"] == "skipped"
        assert "### Core Doctrinal Thesis" in state.raw_answer

    @pytest.mark.asyncio
    async def test_verify_preserves_blank_lines_between_sections(self):
        deps = make_deps()
        state = RAGState(question="What is Stoic fate?")
        state.raw_answer = "Opening thesis [1].\n\n### Definition\nStoic fate is universal causal order [1].\n\n### Agency\nAssent remains in our power [1]."
        state.primary_evidence = [
            Evidence(
                id="node-1",
                label="Heimarmenê",
                type="concept",
                description="Stoic fate",
            ),
        ]
        state.context_pack = ContextPack(node_refs={"node-1": "1"})
        ctx = make_ctx(state, deps)

        verify_result = await ProgrammaticVerify().run(ctx)

        answer = verify_result.data
        assert "\n\n### Definition\n" in answer.answer
        assert "\n\n### Agency\n" in answer.answer

    @pytest.mark.asyncio
    async def test_verify_fallback_without_refs_does_not_recurse(self):
        deps = make_deps()
        state = RAGState(question="Unanswerable question")
        state.raw_answer = "Ungrounded text with no refs"
        ctx = make_ctx(state, deps)

        verify_result = await ProgrammaticVerify().run(ctx)

        assert isinstance(verify_result, End)
        answer = verify_result.data
        assert (
            answer.answer
            == "Available evidence in the current corpus is insufficient to answer confidently."
        )
        assert answer.citations == []

    @pytest.mark.asyncio
    async def test_verify_drops_unsupported_exact_quote_lines(self):
        deps = make_deps()
        state = RAGState(question="What is Stoic fate?")
        state.raw_answer = (
            'Original: "Invented Greek text" [P1]\nStoic fate is a chain of causes [P1]'
        )
        state.context_pack = ContextPack(
            bundle_refs={"bundle-1": "P1"},
            passage_bundles=[
                EvidenceBundle(
                    bundle_id="bundle-1",
                    work_id="work-1",
                    work_title="De Fato",
                    author="Cicero",
                    original_passage_id="p1",
                    original_text="Fate is a chain of causes.",
                    token_estimate=20,
                )
            ],
        )
        ctx = make_ctx(state, deps)

        verify_result = await ProgrammaticVerify().run(ctx)

        assert isinstance(verify_result, End)
        answer = verify_result.data
        assert "Invented Greek text" not in answer.answer
        assert "chain of causes" in answer.answer

    @pytest.mark.asyncio
    async def test_verify_keeps_lines_with_grouped_reference_markers(self):
        deps = make_deps()
        state = RAGState(question="What is Stoic fate?")
        state.raw_answer = "Stoic fate is universal causal order [1, P1]."
        state.primary_evidence = [
            Evidence(
                id="node-1",
                label="Heimarmenê",
                type="concept",
                description="Stoic fate",
            ),
        ]
        state.context_pack = ContextPack(
            bundle_refs={"bundle-1": "P1"},
            node_refs={"node-1": "1"},
            passage_bundles=[
                EvidenceBundle(
                    bundle_id="bundle-1",
                    work_id="work-1",
                    work_title="De Fato",
                    author="Cicero",
                    original_passage_id="p1",
                    original_text="Fate is a chain of causes.",
                    token_estimate=20,
                )
            ],
        )
        ctx = make_ctx(state, deps)

        verify_result = await ProgrammaticVerify().run(ctx)

        answer = verify_result.data
        assert "Stoic fate is universal causal order" in answer.answer
        assert {citation.ref for citation in answer.citations} == {"1", "P1"}

    @pytest.mark.asyncio
    async def test_verify_preserves_section_headers_preceding_grounded_lines(self):
        deps = make_deps()
        state = RAGState(question="What is Stoic fate?")
        state.raw_answer = "## Definition\nStoic fate is universal causal order [1]."
        state.primary_evidence = [
            Evidence(
                id="node-1",
                label="Heimarmenê",
                type="concept",
                description="Stoic fate",
            ),
        ]
        state.context_pack = ContextPack(node_refs={"node-1": "1"})
        ctx = make_ctx(state, deps)

        verify_result = await ProgrammaticVerify().run(ctx)

        answer = verify_result.data
        assert "## Definition" in answer.answer
        assert "Stoic fate is universal causal order [1]." in answer.answer

    def test_verify_does_not_recurse_infinitely_when_fallback_has_no_valid_refs(self):
        """If fallback produces refs that aren't in valid_refs, must not recurse.

        The bug: bundle_refs has "bundle-1"→"P1", but passage_bundles is empty,
        so _reverse_ref_maps produces no bundles_by_ref entry for "P1".
        valid_refs is therefore empty.  raw_answer lines have no valid ref →
        kept_lines is empty → fallback is triggered.  _render_answer_fallback
        reads bundle_refs directly via _claim_reference_refs and emits "[P1]",
        so _extract_line_refs(fallback) returns ["P1"] (non-empty) → the old
        guard does not fire → infinite recursion.
        """
        state = RAGState(question="What is Stoic fate?")
        # bundle_refs present so _claim_reference_refs can emit a ref in the
        # fallback, but passage_bundles is empty so _reverse_ref_maps won't
        # include "P1" in valid_refs → any ref the fallback produces is invalid.
        state.context_pack = ContextPack(
            bundle_refs={"bundle-1": "P1"},
            passage_bundles=[],  # ← makes valid_refs empty for "P1"
        )
        state.raw_answer = "A line with no ref."
        state.claim_ledger = [
            ClaimLedgerItem(
                claim="Stoic fate is a chain of causes.",
                evidence_ids=["bundle-1"],
                support_type="passage",
                confidence=0.9,
                status=ClaimStatus.SUPPORTED,
            )
        ]
        # Must return without hanging
        answer, citations = _verify_answer_programmatically(state)
        assert citations == []

    @pytest.mark.asyncio
    async def test_draft_claim_ledger_marks_fallback_in_metadata(self):
        deps = make_deps(llm_response="not json")
        state = RAGState(question="Who was Chrysippus?")
        state.context_pack = ContextPack(
            prompt_context="## Evidence Bundles\n[P1] Chrysippus",
            bundle_refs={"bundle-1": "P1"},
            passage_bundles=[
                EvidenceBundle(
                    bundle_id="bundle-1",
                    work_id="work-1",
                    work_title="On Fate",
                    author="Chrysippus",
                    original_passage_id="p1",
                    original_text="Chrysippus was a Stoic philosopher.",
                    token_estimate=20,
                )
            ],
        )
        ctx = make_ctx(state, deps)

        result = await DraftClaimLedger().run(ctx)

        assert isinstance(result, RenderGroundedAnswer)
        assert state.metadata["claim_ledger_mode"] == "fallback"
        assert state.metadata["pipeline_degraded"] is True
        assert state.metadata["debug_trace"]["draft_claim_ledger"]["mode"] == "fallback"

    @pytest.mark.asyncio
    async def test_draft_claim_ledger_uses_deterministic_quote_bundle(self):
        deps = make_deps(llm_response="should not be used")
        state = RAGState(
            question="Quote Alexander of Aphrodisias, De Fato 1 in Greek and English."
        )
        state.context_pack = ContextPack(
            prompt_context="ctx",
            bundle_refs={"bundle-1": "P1"},
            passage_bundles=[
                EvidenceBundle(
                    bundle_id="bundle-1",
                    work_id="work-1",
                    work_title="De Fato",
                    author="Alexander of Aphrodisias",
                    canonical_ref="De Fato 1",
                    original_passage_id="p1",
                    original_text="Ἦν μὲν δι’ εὐχῆς...",
                    translation_text="It was my prayer...",
                    language="grc",
                    token_estimate=20,
                )
            ],
        )
        ctx = make_ctx(state, deps)

        result = await DraftClaimLedger().run(ctx)

        assert isinstance(result, RenderGroundedAnswer)
        assert state.metadata["claim_ledger_mode"] == "deterministic_quote"
        assert state.claim_ledger[0].quote_original == "Ἦν μὲν δι’ εὐχῆς..."
        assert state.claim_ledger[0].quote_translation == "It was my prayer..."

    @pytest.mark.asyncio
    async def test_specific_entity_fallback_prefers_metadata_claims(self):
        deps = make_deps(llm_response="not json")
        state = RAGState(question="Who was Chrysippus?")
        state.query_type = QueryType.SPECIFIC_ENTITY
        state.primary_evidence = [
            Evidence(
                id="chrysippus",
                label="Chrysippus of Soli",
                type="person",
                description="Third head of the Stoic school and a major Stoic systematizer.",
                score=0.95,
            )
        ]
        state.context_pack = ContextPack(
            prompt_context="ctx",
            bundle_refs={"bundle-1": "P1"},
            node_refs={"chrysippus": "1"},
            passage_bundles=[
                EvidenceBundle(
                    bundle_id="bundle-1",
                    work_id="work-1",
                    work_title="De Fato",
                    author="Cicero",
                    original_passage_id="p1",
                    original_text="Chrysippus is discussed here.",
                    token_estimate=20,
                )
            ],
        )
        ctx = make_ctx(state, deps)

        await DraftClaimLedger().run(ctx)

        assert state.claim_ledger[0].support_type == "metadata"
        assert "Chrysippus of Soli" in state.claim_ledger[0].claim

    @pytest.mark.asyncio
    async def test_draft_claim_ledger_normalizes_passage_refs_to_bundle_ids(self):
        deps = make_deps(
            llm_response="""{"claims":[{"claim":"Stoic fate is discussed here.","evidence_ids":["P1"],"quote_original":"heimarmene","quote_translation":"fate","support_type":"passage","confidence":0.91,"status":"supported"}]}"""
        )
        state = RAGState(question="What did the Stoics believe about fate?")
        state.context_pack = ContextPack(
            prompt_context="## Evidence Bundles\n[P1] Cicero, De Fato Fat. 1",
            bundle_refs={"bundle-1": "P1"},
            node_refs={"node-1": "1"},
            passage_bundles=[
                EvidenceBundle(
                    bundle_id="bundle-1",
                    work_id="work-1",
                    work_title="De Fato",
                    author="Cicero",
                    original_passage_id="p1",
                    original_text="Fate is a chain of causes.",
                    token_estimate=20,
                )
            ],
        )
        ctx = make_ctx(state, deps)

        await DraftClaimLedger().run(ctx)

        assert state.metadata["claim_ledger_mode"] == "llm"
        assert state.claim_ledger[0].evidence_ids == ["bundle-1"]

    @pytest.mark.asyncio
    async def test_draft_claim_ledger_prefers_node_ids_for_metadata_refs(self):
        deps = make_deps(
            llm_response="""{"claims":[{"claim":"Chrysippus was a Stoic philosopher.","evidence_ids":["1"],"quote_original":null,"quote_translation":null,"support_type":"metadata","confidence":0.95,"status":"supported"}]}"""
        )
        state = RAGState(question="Who was Chrysippus?")
        state.context_pack = ContextPack(
            prompt_context="## KG Metadata\n[1] Chrysippus of Soli",
            bundle_refs={"bundle-1": "P1"},
            node_refs={"node-1": "1"},
            passage_bundles=[
                EvidenceBundle(
                    bundle_id="bundle-1",
                    work_id="work-1",
                    work_title="De Fato",
                    author="Cicero",
                    original_passage_id="p1",
                    original_text="Chrysippus is mentioned.",
                    token_estimate=20,
                )
            ],
        )
        ctx = make_ctx(state, deps)

        await DraftClaimLedger().run(ctx)

        assert state.metadata["claim_ledger_mode"] == "llm"
        assert state.claim_ledger[0].evidence_ids == ["node-1"]

    @pytest.mark.asyncio
    async def test_draft_claim_ledger_fuzzy_matches_metadata_ids(self):
        deps = make_deps(
            llm_response="""{"claims":[{"claim":"Stoic fate is called heimarmene.","evidence_ids":["concept_heimarmene_stoic_fate"],"quote_original":"εἱμαρμένη","quote_translation":"fate","support_type":"metadata","confidence":0.88,"status":"supported"}]}"""
        )
        state = RAGState(question="What did the Stoics believe about fate?")
        state.context_pack = ContextPack(
            prompt_context="## KG Metadata\n[1] Heimarmenê (Stoic Fate)",
            node_refs={"concept_heimarmene_fate_stoics_j0k1l2m3": "1"},
        )
        ctx = make_ctx(state, deps)

        await DraftClaimLedger().run(ctx)

        assert state.metadata["claim_ledger_mode"] == "llm"
        assert state.claim_ledger[0].evidence_ids == [
            "concept_heimarmene_fate_stoics_j0k1l2m3"
        ]

    @pytest.mark.asyncio
    async def test_draft_claim_ledger_salvages_truncated_json(self):
        deps = make_deps(
            llm_response="""{"claims":[{"claim":"Stoic fate is determinism.","evidence_ids":["bundle-1"],"quote_original":null,"quote_translation":null,"support_type":"passage","confidence":0.9,"status":"supported"},{"claim":"cut"""
        )
        state = RAGState(question="What did the Stoics believe about fate?")
        state.context_pack = ContextPack(
            prompt_context="## Evidence Bundles\n[P1] Cicero, De Fato Fat. 1",
            bundle_refs={"bundle-1": "P1"},
            passage_bundles=[
                EvidenceBundle(
                    bundle_id="bundle-1",
                    work_id="work-1",
                    work_title="De Fato",
                    author="Cicero",
                    original_passage_id="p1",
                    original_text="Fate is a chain of causes.",
                    token_estimate=20,
                )
            ],
        )
        ctx = make_ctx(state, deps)

        await DraftClaimLedger().run(ctx)

        assert state.metadata["claim_ledger_mode"] == "llm_salvaged"
        assert state.claim_ledger[0].evidence_ids == ["bundle-1"]

    @pytest.mark.asyncio
    async def test_draft_claim_ledger_marks_quote_queries_insufficient_without_passage_support(
        self,
    ):
        deps = make_deps(
            llm_response="""{"claims":[{"claim":"Parmenides could not have used liberum arbitrium.","evidence_ids":["node-1"],"quote_original":null,"quote_translation":null,"support_type":"metadata","confidence":0.95,"status":"supported"}]}"""
        )
        state = RAGState(
            question="Quote a passage where Parmenides uses the phrase liberum arbitrium."
        )
        state.context_pack = ContextPack(
            prompt_context="## KG Metadata\n[1] liberum arbitrium",
            node_refs={"node-1": "1"},
        )
        ctx = make_ctx(state, deps)

        await DraftClaimLedger().run(ctx)

        assert state.insufficient_evidence is True


class TestSeekCounterEvidence:
    @pytest.mark.asyncio
    async def test_marks_selected_bundles_as_counter_evidence_in_metadata(self):
        """LLM-selected bundles must have evidence_class=counter_evidence set in metadata."""
        bundle_a = EvidenceBundle(
            bundle_id="bundle-a",
            work_id="work-1",
            work_title="De Fato",
            author="Cicero",
            original_passage_id="p1",
            canonical_ref="1.1",
            original_text="Fate rules all.",
            token_estimate=20,
        )
        bundle_b = EvidenceBundle(
            bundle_id="bundle-b",
            work_id="work-2",
            work_title="De Principiis",
            author="Origen",
            original_passage_id="p2",
            canonical_ref="3.1.5",
            original_text="Free will contradicts fate.",
            token_estimate=20,
        )
        state = RAGState(question="Is fate compatible with free will?")
        state.evidence_bundles = [bundle_a, bundle_b]
        state.context_pack = ContextPack(
            bundle_refs={"bundle-a": "P1", "bundle-b": "P2"},
            passage_bundles=[bundle_a, bundle_b],
        )
        state.research_notebook.competing_hypotheses = [
            "Fate is compatible with free will",
            "Fate is incompatible with free will",
        ]

        deps = make_deps(
            llm_response='{"bundle_ids": ["bundle-b"], "rationale": "Origen rejects fate"}'
        )
        ctx = make_ctx(state, deps)

        result = await SeekCounterEvidence().run(ctx)

        assert isinstance(result, EvidenceSufficiency)
        assert bundle_b.metadata.get("evidence_class") == "counter_evidence"
        assert bundle_a.metadata.get("evidence_class") != "counter_evidence"

    @pytest.mark.asyncio
    async def test_skips_when_no_competing_hypotheses(self):
        """SeekCounterEvidence must return EvidenceSufficiency immediately when no hypotheses."""
        state = RAGState(question="What is Stoic fate?")
        state.evidence_bundles = [
            EvidenceBundle(
                bundle_id="bundle-a",
                work_id="work-1",
                work_title="De Fato",
                author="Cicero",
                original_passage_id="p1",
                canonical_ref="1.1",
                original_text="Fate is a chain of causes.",
                token_estimate=20,
            )
        ]
        state.research_notebook.competing_hypotheses = []
        deps = make_deps()
        ctx = make_ctx(state, deps)

        result = await SeekCounterEvidence().run(ctx)
        assert isinstance(result, EvidenceSufficiency)


class TestComplexityAdaptiveContextPack:
    """The synthesis pack budget follows the planner's complexity tier."""

    @staticmethod
    def _state_with_big_bundles(tier: str | None) -> RAGState:
        state = RAGState(question="Did Epictetus think freedom is up to us?")
        state.retrieval_budget = RetrievalBudget(model_window=420_000)
        if tier is not None:
            state.research_plan = ResearchPlan(budget_tier=tier)
        state.evidence_bundles = [
            EvidenceBundle(
                bundle_id=f"bundle-{idx}",
                work_id=f"work-{idx}",
                work_title=f"Work {idx}",
                author="Epictetus",
                original_passage_id=f"p{idx}",
                original_text="Some things are up to us and some are not.",
                token_estimate=50_000,
                source=EvidenceSource.PASSAGE_CITATION,
            )
            for idx in range(5)
        ]
        return state

    def test_quick_tier_packs_fewer_bundles_than_deep(self):
        quick_pack = _build_context_pack(self._state_with_big_bundles("quick"))
        deep_pack = _build_context_pack(self._state_with_big_bundles("deep"))

        assert len(quick_pack.passage_bundles) < len(deep_pack.passage_bundles)

    def test_trace_records_tier_budget_and_ceiling(self):
        state = self._state_with_big_bundles("quick")
        _build_context_pack(state)

        trace = state.metadata["debug_trace"]["context_pack"]
        assert trace["synthesis_budget_tokens"] == 120_000
        assert trace["synthesis_budget_ceiling"] == 420_000

    def test_standard_tier_budget(self):
        state = self._state_with_big_bundles("standard")
        _build_context_pack(state)

        assert (
            state.metadata["debug_trace"]["context_pack"]["synthesis_budget_tokens"]
            == 250_000
        )

    def test_plan_less_legacy_path_keeps_the_full_ceiling(self):
        state = self._state_with_big_bundles(None)
        _build_context_pack(state)

        assert (
            state.metadata["debug_trace"]["context_pack"]["synthesis_budget_tokens"]
            == 420_000
        )
