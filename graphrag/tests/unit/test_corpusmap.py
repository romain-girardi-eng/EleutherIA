"""Tests for the CorpusMap entity-centric navigation layer (arXiv:2609.37226)."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from eleutheria_graphrag.agents.dependencies import Deps
from eleutheria_graphrag.agents.react_loop import NativeAgentLoop
from eleutheria_graphrag.agents.sse_emitter import NullEmitter
from eleutheria_graphrag.agents.state import QueryComplexity, RAGState
from eleutheria_graphrag.agents.tools import build_tool_registry
from eleutheria_graphrag.agents.tools.entity_pages import (
    ReadEntityPageTool,
    SearchEntityPagesTool,
)
from eleutheria_graphrag.corpusmap import build_corpus_map, select_candidates
from eleutheria_graphrag.corpusmap.builder import build_corpus_map_from_rows
from eleutheria_graphrag.corpusmap.runtime import corpusmap_candidate_context

NODES = [
    {
        "id": "person_origen",
        "type": "person",
        "label": "Origen of Alexandria",
        "alternative_names": '["Origenes"]',
        "description": "Christian theologian of Alexandria.",
    },
    {
        "id": "person_lonely",
        "type": "person",
        "label": "Lonely Author",
        "description": "Mentioned once.",
    },
    {
        "id": "concept_autexousion",
        "type": "concept",
        "label": "Autexousion",
        "description": "Self-determination of the rational creature.",
    },
    {
        "id": "work_de_principiis",
        "type": "work",
        "label": "De Principiis",
        "description": "Origen's treatise.",
    },
    {
        "id": "argument_frede_origen",
        "type": "argument",
        "label": "Frede: Origen's doctrine is basically Stoic",
        "description": "Frede argues that Origen explicates autexousion along Stoic lines. It is anti-Gnostic.",
    },
    {
        "id": "argument_bobzien_eph_hemin",
        "type": "argument",
        "label": "Bobzien: two conceptions of eph hemin",
        "description": "Bobzien distinguishes the one-sided and the two-sided conceptions of what depends on us.",
    },
    {
        "id": "passage_princ_3_1_3",
        "type": "passage",
        "label": "De Princ. III.1.3",
        "description": "τὸ ἐφ᾽ ἡμῖν ... αὐτεξούσιον",
    },
    {
        "id": "passage_princ_3_1_4",
        "type": "passage",
        "label": "De Princ. III.1.4",
        "description": "κρίσις",
    },
]
EDGES = [
    {
        "source": "argument_frede_origen",
        "target": "person_origen",
        "relation": "discusses",
    },
    {
        "source": "argument_frede_origen",
        "target": "concept_autexousion",
        "relation": "discusses",
    },
    {
        "source": "argument_bobzien_eph_hemin",
        "target": "concept_autexousion",
        "relation": "discusses",
    },
    {
        "source": "argument_frede_origen",
        "target": "passage_princ_3_1_3",
        "relation": "cites_primary_source",
    },
    {
        "source": "passage_princ_3_1_3",
        "target": "work_de_principiis",
        "relation": "part_of",
    },
    {
        "source": "passage_princ_3_1_4",
        "target": "work_de_principiis",
        "relation": "part_of",
    },
    {
        "source": "passage_princ_3_1_3",
        "target": "person_origen",
        "relation": "authored_by",
    },
    {
        "source": "argument_bobzien_eph_hemin",
        "target": "person_lonely",
        "relation": "discusses",
    },
    # entity-entity edge: deliberately not rendered on pages (paper §B.4)
    {
        "source": "person_origen",
        "target": "concept_autexousion",
        "relation": "develops",
    },
]


def _map():
    return build_corpus_map_from_rows(NODES, EDGES)


def test_keeps_only_cross_document_entities() -> None:
    cmap = _map()
    assert "person_lonely" not in cmap.pages  # linked to a single document
    assert {"person_origen", "concept_autexousion", "work_de_principiis"} <= set(
        cmap.pages
    )


def test_bipartite_links_and_inherited_evidence() -> None:
    cmap = _map()
    origen = cmap.pages["person_origen"]
    assert origen.facts == ["argument_frede_origen"]
    # authored passages are summarised as holdings, not listed as evidence
    assert "passage_princ_3_1_3" in origen.holdings["work_de_principiis"]
    # a passage cited by a linked argument is evidence for the entity
    assert "passage_princ_3_1_3" in cmap.pages["concept_autexousion"].evidence
    assert set(cmap.doc_pages["argument_frede_origen"]) == {
        "person_origen",
        "concept_autexousion",
    }


def test_render_tags_every_fact_with_its_source_and_omits_entity_edges() -> None:
    page = _map().render("concept_autexousion", focus="Bobzien eph hemin")
    assert "[argument_bobzien_eph_hemin]" in page and "[argument_frede_origen]" in page
    assert "develops" not in page


def test_aliases_are_searchable() -> None:
    assert _map().search_pages("Origenes", k=1)[0][0] == "person_origen"


def test_candidates_are_ids_and_titles_from_linked_documents() -> None:
    cand = select_candidates(
        _map(), "How does Frede read Origen on autexousion?", n_pages=3, n_docs=3
    )
    assert cand.pages[0][0] in {"person_origen", "concept_autexousion"}
    assert cand.documents[0][0] == "argument_frede_origen"
    assert "Stoic lines" not in cand.render()  # titles only, no content


def _deps() -> Deps:
    return Deps(
        db=AsyncMock(),
        llm=AsyncMock(),
        kg_data={"nodes": NODES, "edges": EDGES},
        node_lookup={n["id"]: n for n in NODES},
        outgoing_edges={},
        incoming_edges={},
    )


def test_candidate_context_is_flag_and_query_type_gated(monkeypatch) -> None:
    deps = _deps()
    state = RAGState(question="Origen autexousion Frede", query_type="multi_hop")
    monkeypatch.delenv("ELEUTHERIA_CORPUSMAP", raising=False)
    assert corpusmap_candidate_context(deps, state) == ""
    monkeypatch.setenv("ELEUTHERIA_CORPUSMAP", "1")
    assert "argument_frede_origen" in corpusmap_candidate_context(deps, state)
    single = RAGState(question="Origen autexousion Frede", query_type="specific_entity")
    assert corpusmap_candidate_context(deps, single) == ""


def test_tools_registered_only_with_flag(monkeypatch) -> None:
    monkeypatch.delenv("ELEUTHERIA_CORPUSMAP", raising=False)
    assert build_tool_registry(_deps()).get("read_entity_page") is None
    monkeypatch.setenv("ELEUTHERIA_CORPUSMAP", "1")
    registry = build_tool_registry(_deps())
    assert registry.get("read_entity_page") is not None
    assert registry.get("search_entity_pages") is not None


@pytest.mark.asyncio
async def test_entity_page_tools() -> None:
    deps = _deps()
    hits = await SearchEntityPagesTool(deps).execute({"query": "De Principiis"})
    assert hits.pages[0].entity_id == "work_de_principiis"
    page = await ReadEntityPageTool(deps).execute({"entity_id": "person_origen"})
    assert page.found and "Origen of Alexandria" in page.page
    missing = await ReadEntityPageTool(deps).execute({"entity_id": "nope"})
    assert not missing.found


@pytest.mark.asyncio
async def test_native_loop_opening_message_carries_candidates(monkeypatch) -> None:
    monkeypatch.setenv("ELEUTHERIA_CORPUSMAP", "1")
    deps = _deps()
    deps.llm.generate_with_tools = AsyncMock(
        return_value={"role": "assistant", "content": "done"}
    )
    state = RAGState(
        question="How does Frede read Origen on autexousion?",
        complexity=QueryComplexity.SIMPLE,
        query_type="multi_hop",
    )
    loop = NativeAgentLoop(
        deps=deps, state=state, tools=build_tool_registry(deps), emitter=NullEmitter()
    )
    await loop.run()
    assert "CorpusMap candidates" in loop.messages[1]["content"]


def test_snapshot_build_smoke() -> None:
    """The real snapshot builds and resolves the reference benchmark's entities."""
    from pathlib import Path

    repo = Path(__file__).resolve().parents[3]
    if not (repo / "data/kg/nodes.jsonl").exists():
        pytest.skip("KG snapshot not available")
    cmap = build_corpus_map(repo / "data/kg", repo / "data/corpus")
    assert len(cmap.pages) > 500
    top = [
        e for e, _ in cmap.search_pages("Origen De Principiis self-determination", k=5)
    ]
    assert "work_de_principiis_origen_230s_v2w3x4y5" in top
