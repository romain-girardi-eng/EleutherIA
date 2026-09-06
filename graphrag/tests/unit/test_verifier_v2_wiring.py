"""Production wiring tests for the v2 adversarial citation verifier (G2).

Covers: service construction (env gate), the fresh-SELECT passage fetcher,
risk-ordered claim sampling, verdict merging into citations / claim ledger /
grounding, and per-citation SSE emission on the streaming path.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any
from unittest.mock import AsyncMock

import pytest

from eleutheria_graphrag.agents.scholarly_agent import (
    ScholarlyAgent,
    _citation_audit_max_wait,
    _sample_citations_for_verification,
    _verifier_v2_max_claims,
)
from eleutheria_graphrag.agents.state import (
    Citation,
    ClaimLedgerItem,
    ClaimStatus,
    ScholarlyAnswer,
)
from eleutheria_graphrag.agents.structured_models import SelfRAGEvaluation
from eleutheria_graphrag.models.verification import (
    CitationCheck,
    CitationStatus,
    VerificationReport,
)
from eleutheria_graphrag.services.citation_verifier_v2 import (
    NODE_TEXT_MIN_CHARS,
    CitationVerifierV2,
    build_db_passage_fetcher,
    node_statement,
)
from eleutheria_graphrag.services.graphrag_service import GraphRAGService

from .conftest import make_deps
from .test_programmatic_verify_quotes import BUNDLE_GREEK

# A UUID-shaped passage id: the passages arm of the fetcher only runs for
# ids that parse as UUIDs (index scan via ``passage_id = $1::uuid``).
PASSAGE_UUID = "123e4567-e89b-12d3-a456-426614174000"

# --------------------------------------------------------------------- helpers


class _FakeDB:
    """DB stub: returns queued responses (a list of rows or an Exception)."""

    def __init__(self, responses: list[Any]) -> None:
        self._responses = list(responses)
        self.calls: list[tuple[str, tuple[Any, ...]]] = []

    async def fetch(self, query: str, *args: Any) -> list[dict[str, Any]]:
        self.calls.append((query, args))
        result = self._responses.pop(0)
        if isinstance(result, Exception):
            raise result
        return result


def _answer_with_citations() -> ScholarlyAnswer:
    return ScholarlyAnswer(
        answer=(
            f"Justin quotes {BUNDLE_GREEK} [P1]. "
            "A weakly sourced claim [2]. "
            "A well sourced claim [3]."
        ),
        question="What did Justin say about fate?",
        citations=[
            Citation(
                ref="P1",
                type="passage",
                id="p1",
                label="Apologia Prima 43",
                verified=True,
            ),
            Citation(
                ref="2",
                type="node",
                id="node-2",
                label="Chrysippus",
                confidence=0.4,
                verified=True,
            ),
            Citation(
                ref="3",
                type="node",
                id="node-3",
                label="Justin Martyr",
                confidence=0.9,
                verified=True,
            ),
        ],
        claim_ledger=[
            ClaimLedgerItem(
                claim="Justin quotes the fate passage.",
                evidence_ids=["work-1::p1"],
                status=ClaimStatus.SUPPORTED,
            ),
            ClaimLedgerItem(
                claim="A weakly sourced claim.",
                evidence_ids=["node-2"],
                status=ClaimStatus.SUPPORTED,
            ),
        ],
        self_rag_evaluation=SelfRAGEvaluation(
            relevance=80,
            grounding=100,
            completeness=80,
            confidence=80,
        ),
    )


def _report(checks: list[CitationCheck]) -> VerificationReport:
    return VerificationReport.from_checks(checks)


def _agent_with_verifier(report: VerificationReport) -> ScholarlyAgent:
    deps = make_deps()
    verifier = AsyncMock()
    verifier.verify_draft = AsyncMock(return_value=report)
    deps.verifier_v2 = verifier
    return ScholarlyAgent(deps)


# ----------------------------------------------------------- service wiring


@pytest.mark.asyncio
async def test_load_kg_wires_verifier_v2_by_default(monkeypatch) -> None:
    monkeypatch.delenv("ELEUTHERIA_VERIFIER_V2", raising=False)
    service = GraphRAGService(
        db_service=AsyncMock(),
        llm_service=AsyncMock(),
        kg_data={"nodes": [], "edges": []},
    )
    await service.load_kg()
    assert service._agent is not None
    assert service._agent.deps.verifier_v2 is not None


@pytest.mark.asyncio
async def test_load_kg_skips_verifier_v2_when_env_disabled(monkeypatch) -> None:
    monkeypatch.setenv("ELEUTHERIA_VERIFIER_V2", "false")
    service = GraphRAGService(
        db_service=AsyncMock(),
        llm_service=AsyncMock(),
        kg_data={"nodes": [], "edges": []},
    )
    await service.load_kg()
    assert service._agent is not None
    assert service._agent.deps.verifier_v2 is None


# ----------------------------------------------------------- passage fetcher


@pytest.mark.asyncio
async def test_fetcher_returns_fresh_passage_text() -> None:
    db = _FakeDB(
        [
            [
                {
                    "passage_id": PASSAGE_UUID,
                    "text_content": BUNDLE_GREEK,
                    "canonical_ref": "43",
                    "cts_urn": "urn:cts:greekLit:test:43",
                    "passage_role": "original",
                    "title": "Apologia Prima",
                    "author": "Justin Martyr",
                    "language": "grc",
                }
            ]
        ]
    )
    fetch = build_db_passage_fetcher(db)

    fetched = await fetch(PASSAGE_UUID)

    assert fetched is not None
    assert fetched["text"] == BUNDLE_GREEK
    assert fetched["label"] == "43"
    assert fetched["source"] == "passages"


@pytest.mark.asyncio
async def test_fetcher_uses_uuid_cast_for_uuid_id() -> None:
    """Regression: ``passage_id::text = $1`` forced a seq scan over 69k rows."""
    db = _FakeDB(
        [
            [
                {
                    "passage_id": PASSAGE_UUID,
                    "text_content": "textus",
                    "passage_role": "original",
                    "language": "lat",
                }
            ]
        ]
    )
    fetch = build_db_passage_fetcher(db)

    await fetch(PASSAGE_UUID)

    sql, args = db.calls[0]
    assert "p.passage_id = $1::uuid" in sql
    assert "passage_id::text = $1" not in sql
    assert args == (PASSAGE_UUID,)


@pytest.mark.asyncio
async def test_passage_slug_uses_corpus_uuid_not_false_kg_description() -> None:
    """Adversarial: a false KG description must never beat the corpus text."""
    db = _FakeDB(
        [
            [
                {
                    "passage_id": PASSAGE_UUID,
                    "text_content": BUNDLE_GREEK,
                    "canonical_ref": "43",
                    "passage_role": "original",
                    "title": "Apologia Prima",
                    "author": "Justin Martyr",
                    "language": "grc",
                }
            ]
        ]
    )
    fetch = build_db_passage_fetcher(
        db,
        node_lookup={
            "passage_justin_apol_43": {
                "id": "passage_justin_apol_43",
                "type": "passage",
                "label": "Justin, Apol. 43",
                "description": "FALSE KG DESCRIPTION: Justin endorses fatalism.",
                "metadata": {
                    "db_passage_id": PASSAGE_UUID,
                    "passage_role": "original",
                },
            }
        },
    )

    fetched = await fetch("passage_justin_apol_43")

    assert fetched is not None
    assert fetched["text"] == BUNDLE_GREEK
    assert "FALSE KG DESCRIPTION" not in fetched["text"]
    assert fetched["source"] == "passages"
    assert fetched["passage_id"] == PASSAGE_UUID
    assert len(db.calls) == 1
    assert "FROM free_will.passages" in db.calls[0][0]
    assert "kg_nodes" not in db.calls[0][0]


@pytest.mark.asyncio
async def test_passage_slug_resolves_via_exact_citation_mapping() -> None:
    db = _FakeDB(
        [
            [
                {
                    "passage_id": PASSAGE_UUID,
                    "citation_type": "snapshot_passage_node",
                    "confidence": 1.0,
                }
            ],
            [
                {
                    "passage_id": PASSAGE_UUID,
                    "text_content": BUNDLE_GREEK,
                    "canonical_ref": "43",
                    "passage_role": "original",
                    "language": "grc",
                }
            ],
        ]
    )
    fetch = build_db_passage_fetcher(
        db,
        node_lookup={
            "passage_justin_unmapped": {
                "id": "passage_justin_unmapped",
                "type": "passage",
                "metadata": {"passage_role": "original"},
            }
        },
    )

    fetched = await fetch("passage_justin_unmapped")

    assert fetched is not None
    assert fetched["passage_id"] == PASSAGE_UUID
    assert "passage_citations" in db.calls[0][0]
    assert "FROM free_will.passages" in db.calls[1][0]


@pytest.mark.asyncio
async def test_passage_slug_without_exact_uuid_mapping_is_missing() -> None:
    db = _FakeDB([[]])
    fetch = build_db_passage_fetcher(
        db,
        node_lookup={
            "passage_unmapped": {
                "id": "passage_unmapped",
                "type": "passage",
                "description": "Convincing but unauditable text",
                "metadata": {"passage_role": "original"},
            }
        },
    )

    fetched = await fetch("passage_unmapped")

    assert fetched is None
    assert len(db.calls) == 1
    assert "passage_citations" in db.calls[0][0]


@pytest.mark.asyncio
async def test_holder_biography_never_substitutes_for_position_page_evidence() -> None:
    position_id = "scholarly_argument_bobzien_two_conceptions"
    publication_id = "pub_bobzien_2001_determinism"
    page_quote = "The two-sided conception arose only later."
    page_hash = hashlib.sha256(page_quote.encode()).hexdigest()
    db = _FakeDB(
        [
            [
                {
                    "node_id": position_id,
                    "label": "Bobzien: two conceptions",
                    "type": "argument",
                    "metadata": {
                        "scholarly_work_id": publication_id,
                        "quote_page": "p. 412",
                        "quote_verbatim": (
                            "MISLEADING KG QUOTE: the two-sided conception is ancient."
                        ),
                        "citation_verdict": "verified",
                    },
                }
            ],
            [
                {
                    "node_id": publication_id,
                    "label": "Bobzien 2001, Determinism and Freedom",
                    "type": "publication",
                    "metadata": {"citation_verdict": "verified"},
                }
            ],
            [
                {
                    "manifestation_id": "bobzien_2001_pdf_v1",
                    "publication_id": publication_id,
                    "source_locator": "local://bobzien-2001.pdf",
                    "artifact_source_sha256": "a" * 64,
                    "rights_status": "copyrighted",
                    "reuse_status": "internal_research_only",
                    "artifact_extraction_status": "partial",
                    "artifact_review_status": "reviewed",
                    "page_source_sha256": "a" * 64,
                    "physical_page": 430,
                    "printed_page": "412",
                    "page_locator": "local://bobzien-2001.pdf#page=430",
                    "text_content": page_quote,
                    "text_sha256": page_hash,
                    "page_extraction_status": "extracted",
                    "page_review_status": "reviewed",
                }
            ],
        ]
    )
    fetch = build_db_passage_fetcher(
        db,
        node_lookup={
            position_id: {
                "id": position_id,
                "type": "argument",
                "metadata": {"scholar_id": "person_bobzien"},
            },
            "person_bobzien": {
                "id": "person_bobzien",
                "type": "person",
                "description": "MISLEADING BIOGRAPHY: unrelated life dates.",
            },
        },
    )

    fetched = await fetch(position_id)

    assert fetched is not None
    assert fetched["text"] == page_quote
    assert fetched["position_id"] == position_id
    assert fetched["publication_id"] == publication_id
    assert fetched["page_ref"] == "p. 412"
    assert fetched["source"] == "secondary_evidence_pages"
    assert "MISLEADING BIOGRAPHY" not in fetched["text"]
    assert "MISLEADING KG QUOTE" not in fetched["text"]
    assert all(call[1] != ("person_bobzien",) for call in db.calls)


@pytest.mark.asyncio
async def test_position_without_reviewed_page_evidence_is_missing_verdict() -> None:
    position_id = "scholarly_argument_unmapped_page"
    publication_id = "pub_unmapped_page"
    db = _FakeDB(
        [
            [
                {
                    "node_id": position_id,
                    "label": "A page-unmapped position",
                    "type": "argument",
                    "metadata": {
                        "scholarly_work_id": publication_id,
                        "quote_page": "p. 99",
                        "quote_verbatim": "Plausible KG text is not page evidence.",
                        "citation_verdict": "verified",
                    },
                }
            ],
            [
                {
                    "node_id": publication_id,
                    "label": "Unmapped publication",
                    "type": "publication",
                    "metadata": {"citation_verdict": "verified"},
                }
            ],
            [],
        ]
    )
    fetch = build_db_passage_fetcher(
        db,
        node_lookup={position_id: {"id": position_id, "type": "argument"}},
    )
    llm = AsyncMock()
    verifier = CitationVerifierV2(llm=llm, passage_fetcher=fetch)

    check = await verifier.verify_one("The publication makes this claim.", position_id)

    assert check.status is CitationStatus.MISSING
    assert check.suggested_action == "remove citation"
    llm.generate.assert_not_called()


# A curated scholarly_argument statement of the kind the graph actually holds
# (~500 chars): well above the node-evidence threshold.
ELIASSON_ID = "scholarly_argument_eliasson_roman_stoa_eudaimonist_shift"
ELIASSON_STATEMENT = (
    "In his synthesis of the pre-Plotinian tradition Eliasson argues that from "
    "Seneca onwards the Aristotelian-Chrysippean conception vanishes: for "
    "Seneca, Musonius, Epictetus and Marcus Aurelius what is primarily eph' "
    "hemin is strictly the correct use of impressions, which refers not to what "
    "we are responsible for but to that by which alone we may attain "
    "eudaimonia. Action is entirely excluded from what is eph' hemin on the "
    "grounds that it depends on the body, which is subject to hindrance."
)


def _eliasson_row() -> dict[str, Any]:
    return {
        "node_id": ELIASSON_ID,
        "label": (
            "Eliasson: in the Roman Stoa eph' hemin shifts from responsibility "
            "to well-being"
        ),
        "type": "argument",
        "description": ELIASSON_STATEMENT,
        "metadata": {
            "argument_type": "modern_scholarly_position",
            "scholarly_work_id": "pub_eliasson_2008",
            "quote_page": "p. 218",
            "quote_verbatim": (
                "what is primarily eph' hemin is strictly the correct use of "
                "impressions"
            ),
            "quote_source": "Eliasson, E. (2008). The Notion of That Which Depends on Us.",
            "quote_source_file": "/Users/romain/private/eliasson.md",
            "citation_verified": True,
        },
    }


def _eliasson_db_rows() -> list[Any]:
    """kg_nodes position row, its publication, and no reviewed page."""
    return [
        [_eliasson_row()],
        [
            {
                "node_id": "pub_eliasson_2008",
                "label": "Eliasson 2008",
                "type": "publication",
                "metadata": {"citation_verdict": "verified"},
            }
        ],
        [],
    ]


def _eliasson_person_row() -> dict[str, Any]:
    return {
        "node_id": "scholar_eliasson",
        "label": "Erik Eliasson",
        "type": "person",
        "description": "Swedish historian of ancient philosophy.",
        "metadata": {"specialty": "Plotinus"},
    }


@pytest.mark.asyncio
async def test_scholarly_argument_without_page_evidence_audits_node_statement() -> None:
    """Regression: 54/55 MISSING verdicts were nodes like this one."""
    db = _FakeDB(_eliasson_db_rows())
    fetch = build_db_passage_fetcher(db)

    fetched = await fetch(ELIASSON_ID)

    assert fetched is not None
    assert fetched["kind"] == "node"
    assert fetched["source"] == "kg_nodes"
    assert fetched["node_id"] == ELIASSON_ID
    assert fetched["node_type"] == "argument"
    assert fetched["text_chars"] >= NODE_TEXT_MIN_CHARS
    assert ELIASSON_STATEMENT in fetched["text"]
    assert "Label: Eliasson: in the Roman Stoa" in fetched["text"]
    assert "Curated quotation: what is primarily eph' hemin" in fetched["text"]
    assert "Source: Eliasson, E. (2008)" in fetched["text"]
    assert "Page: p. 218" in fetched["text"]
    # Local file paths are curation plumbing, never audit evidence.
    assert "/Users/romain" not in fetched["text"]
    # The node is read fresh from kg_nodes, description included.
    assert "kg_nodes" in db.calls[0][0]
    assert "description" in db.calls[0][0]

    llm = AsyncMock()
    llm.generate = AsyncMock(
        return_value=json.dumps(
            {"status": "VERIFIED", "reasoning": "the record states the shift"}
        )
    )
    verifier = CitationVerifierV2(
        llm=llm, passage_fetcher=build_db_passage_fetcher(_FakeDB(_eliasson_db_rows()))
    )
    check = await verifier.verify_one(
        "Eliasson argues that for the Roman Stoics what is eph' hemin is the "
        "correct use of impressions.",
        ELIASSON_ID,
    )

    assert check.status is CitationStatus.VERIFIED
    assert check.evidence_kind == "node"
    prompt = llm.generate.call_args.args[0]
    assert ELIASSON_STATEMENT in prompt
    assert "curated knowledge-graph record (node type: argument)" in prompt


@pytest.mark.asyncio
async def test_reviewed_page_evidence_still_beats_node_statement() -> None:
    """When a reviewed page resolves, the position is audited as a passage."""
    page_quote = "What is primarily eph' hemin is the correct use of impressions."
    db = _FakeDB(
        [
            [_eliasson_row()],
            [
                {
                    "node_id": "pub_eliasson_2008",
                    "label": "Eliasson 2008",
                    "type": "publication",
                    "metadata": {"citation_verdict": "verified"},
                }
            ],
            [
                {
                    "manifestation_id": "eliasson_2008_pdf",
                    "publication_id": "pub_eliasson_2008",
                    "source_locator": "local://eliasson-2008.pdf",
                    "artifact_source_sha256": "b" * 64,
                    "rights_status": "copyrighted",
                    "reuse_status": "internal_research_only",
                    "artifact_extraction_status": "partial",
                    "artifact_review_status": "reviewed",
                    "page_source_sha256": "b" * 64,
                    "physical_page": 240,
                    "printed_page": "218",
                    "page_locator": "local://eliasson-2008.pdf#page=240",
                    "text_content": page_quote,
                    "text_sha256": hashlib.sha256(page_quote.encode()).hexdigest(),
                    "page_extraction_status": "extracted",
                    "page_review_status": "reviewed",
                }
            ],
        ]
    )
    fetch = build_db_passage_fetcher(db)

    fetched = await fetch(ELIASSON_ID)

    assert fetched is not None
    assert fetched.get("kind") != "node"
    assert fetched["source"] == "secondary_evidence_pages"
    assert fetched["text"] == page_quote


@pytest.mark.asyncio
async def test_scholar_node_with_one_line_bio_is_missing_with_reason() -> None:
    db = _FakeDB([[_eliasson_person_row()]])
    fetch = build_db_passage_fetcher(db)

    fetched = await fetch("scholar_eliasson")

    assert fetched is not None
    assert fetched["kind"] == "node"
    assert fetched["text"] == ""
    assert fetched["text_chars"] == len("Swedish historian of ancient philosophy.")

    llm = AsyncMock()
    verifier = CitationVerifierV2(
        llm=llm,
        passage_fetcher=build_db_passage_fetcher(_FakeDB([[_eliasson_person_row()]])),
    )
    check = await verifier.verify_one(
        "Eliasson argues that action is excluded from eph' hemin.",
        "scholar_eliasson",
    )

    assert check.status is CitationStatus.MISSING
    assert check.evidence_kind == "node"
    assert "'Erik Eliasson' (person)" in check.reasoning
    assert f"minimum {NODE_TEXT_MIN_CHARS}" in check.reasoning
    llm.generate.assert_not_called()


@pytest.mark.asyncio
async def test_discovery_only_node_is_not_node_evidence() -> None:
    row = _eliasson_row()
    row["metadata"]["citability"] = "discoverable_only"
    db = _FakeDB([[row]])
    fetch = build_db_passage_fetcher(
        db, node_lookup={ELIASSON_ID: {"id": ELIASSON_ID, "type": "concept"}}
    )

    assert await fetch(ELIASSON_ID) is None


@pytest.mark.asyncio
async def test_passage_slug_never_falls_back_to_node_statement() -> None:
    """A passage citation is corpus text or nothing — never its KG blurb."""
    db = _FakeDB([[]])
    fetch = build_db_passage_fetcher(
        db,
        node_lookup={
            "passage_unmapped_long": {
                "id": "passage_unmapped_long",
                "type": "passage",
                "description": ELIASSON_STATEMENT,
                "metadata": {"passage_role": "original"},
            }
        },
    )

    fetched = await fetch("passage_unmapped_long")

    assert fetched is None
    assert len(db.calls) == 1
    assert "passage_citations" in db.calls[0][0]


@pytest.mark.asyncio
async def test_node_evidence_is_read_fresh_not_from_snapshot() -> None:
    """The snapshot node is a handle; the audited statement comes from the DB."""
    db = _FakeDB([[_eliasson_person_row() | {"description": ELIASSON_STATEMENT}]])
    fetch = build_db_passage_fetcher(
        db,
        node_lookup={
            "scholar_eliasson": {
                "id": "scholar_eliasson",
                "type": "person",
                "description": "STALE SNAPSHOT TEXT that must not be audited.",
            }
        },
    )

    fetched = await fetch("scholar_eliasson")

    assert fetched is not None
    assert fetched["kind"] == "node"
    assert ELIASSON_STATEMENT in fetched["text"]
    assert "STALE SNAPSHOT" not in fetched["text"]
    assert db.calls[0][1] == ("scholar_eliasson",)


def test_node_statement_counts_only_substantive_fields() -> None:
    text, substantive = node_statement(
        {
            "label": "A very long label that must not count toward the threshold "
            "because a label is identity, not evidence at all",
            "type": "person",
            "description": "Short bio.",
            "metadata": {
                "quote_source": "Some reference that is long but is only an anchor",
                "stance": "sceptical",
            },
        }
    )

    assert substantive == len("Short bio.") + len("sceptical")
    assert substantive < NODE_TEXT_MIN_CHARS
    assert text.startswith("Label: A very long label")
    assert "Statement: Short bio." in text
    assert "Stance: sceptical" in text
    assert "Source: Some reference" in text


@pytest.mark.asyncio
async def test_machine_translation_is_not_authoritative_evidence() -> None:
    db = _FakeDB(
        [
            [
                {
                    "passage_id": PASSAGE_UUID,
                    "text_content": "Machine translation that looks plausible.",
                    "canonical_ref": "43",
                    "passage_role": "translation",
                    "language": "eng",
                }
            ]
        ]
    )
    fetch = build_db_passage_fetcher(
        db,
        node_lookup={
            "passage_justin_43_en": {
                "id": "passage_justin_43_en",
                "type": "passage",
                "description": "Machine translation that looks plausible.",
                "metadata": {
                    "db_passage_id": PASSAGE_UUID,
                    "passage_role": "translation",
                    "translation_type": "machine",
                },
            }
        },
    )

    assert await fetch("passage_justin_43_en") is None


@pytest.mark.asyncio
async def test_published_human_translation_is_authoritative_evidence() -> None:
    db = _FakeDB(
        [
            [
                {
                    "passage_id": PASSAGE_UUID,
                    "text_content": "A reviewed published human translation.",
                    "canonical_ref": "43",
                    "passage_role": "translation",
                    "language": "eng",
                }
            ]
        ]
    )
    fetch = build_db_passage_fetcher(
        db,
        node_lookup={
            "passage_justin_43_published_en": {
                "id": "passage_justin_43_published_en",
                "type": "passage",
                "metadata": {
                    "db_passage_id": PASSAGE_UUID,
                    "passage_role": "translation",
                    "translation_type": "published_human",
                },
            }
        },
    )

    evidence = await fetch("passage_justin_43_published_en")

    assert evidence is not None
    assert evidence["passage_role"] == "translation"
    assert evidence["text"] == "A reviewed published human translation."


@pytest.mark.asyncio
async def test_ancient_human_literal_translation_is_authoritative_evidence() -> None:
    """A labelled ancient version is primary transmission, not machine prose."""

    db = _FakeDB(
        [
            [
                {
                    "passage_id": PASSAGE_UUID,
                    "text_content": "Ancient Latin version of a lost Greek locus.",
                    "canonical_ref": "Adv. haer. III.20.3",
                    "passage_role": "translation",
                    "language": "lat",
                }
            ]
        ]
    )
    fetch = build_db_passage_fetcher(
        db,
        node_lookup={
            "passage_irenaeus_iii_20_3_lat": {
                "id": "passage_irenaeus_iii_20_3_lat",
                "type": "passage",
                "metadata": {
                    "db_passage_id": PASSAGE_UUID,
                    "passage_role": "translation",
                    "translation_type": "ancient_human_literal",
                    "source_passage_status": "lost_continuous_greek_not_mapped",
                },
            }
        },
    )

    evidence = await fetch("passage_irenaeus_iii_20_3_lat")

    assert evidence is not None
    assert evidence["passage_role"] == "translation"
    assert evidence["language"] == "lat"
    assert evidence["text"] == "Ancient Latin version of a lost Greek locus."


@pytest.mark.asyncio
async def test_fetcher_returns_none_when_unknown() -> None:
    db = _FakeDB([[]])
    fetch = build_db_passage_fetcher(db)

    assert await fetch("ghost") is None


@pytest.mark.asyncio
async def test_fetcher_refetches_on_every_call_no_caching() -> None:
    row = [
        {
            "passage_id": PASSAGE_UUID,
            "text_content": "textus",
            "canonical_ref": "1",
            "passage_role": "original",
            "language": "lat",
        }
    ]
    db = _FakeDB([list(row), list(row)])
    fetch = build_db_passage_fetcher(db)

    await fetch(PASSAGE_UUID)
    await fetch(PASSAGE_UUID)

    assert len(db.calls) == 2


# ----------------------------------------------------------- claim sampling


def test_sampling_prioritizes_greek_quoting_then_low_confidence() -> None:
    answer = _answer_with_citations()

    sampled = _sample_citations_for_verification(answer, max_claims=3)

    ids = [pair.citation.id for pair in sampled]
    # Greek-quoting claim first, then ascending confidence.
    assert ids == ["p1", "node-2", "node-3"]
    # The sampled claim text is the sentence carrying the ref marker.
    assert BUNDLE_GREEK in sampled[0].claim
    assert [pair.sentence_index for pair in sampled] == [0, 1, 2]


def test_sampling_treats_node_citations_like_passages() -> None:
    """Risk ordering is kind-blind: a low-confidence node outranks a
    high-confidence passage, and node citations are never dropped from the
    sample for being nodes."""
    answer = ScholarlyAnswer(
        answer="Eliasson argues the shift [A1]. Justin says so [P2]. Bobzien [N3].",
        question="q",
        citations=[
            Citation(
                ref="A1",
                type="node",
                id=ELIASSON_ID,
                label="Eliasson: Roman Stoa shift",
                confidence=0.95,
            ),
            Citation(
                ref="P2",
                type="passage",
                id="p2",
                label="Apol. 43",
                confidence=0.5,
            ),
            Citation(
                ref="N3",
                type="node",
                id="scholar_bobzien",
                label="Susanne Bobzien",
                confidence=0.2,
            ),
        ],
    )

    sampled = _sample_citations_for_verification(answer, max_claims=3)

    assert [p.citation.id for p in sampled] == ["scholar_bobzien", "p2", ELIASSON_ID]
    assert sampled[2].claim == "Eliasson argues the shift [A1]."
    # Budget cuts by risk, not by kind.
    assert [p.citation.id for p in _sample_citations_for_verification(answer, 2)] == [
        "scholar_bobzien",
        "p2",
    ]


def test_sampling_respects_budget() -> None:
    answer = _answer_with_citations()

    sampled = _sample_citations_for_verification(answer, max_claims=1)

    assert len(sampled) == 1
    assert sampled[0].citation.id == "p1"


def test_max_claims_env_parsing(monkeypatch) -> None:
    monkeypatch.delenv("ELEUTHERIA_VERIFIER_V2_MAX_CLAIMS", raising=False)
    # 160: a benchmark answer carrying 84 citations had 20 withheld as
    # "unaudited" under the former default of 64.
    assert _verifier_v2_max_claims() == 160
    monkeypatch.setenv("ELEUTHERIA_VERIFIER_V2_MAX_CLAIMS", "3")
    assert _verifier_v2_max_claims() == 3
    monkeypatch.setenv("ELEUTHERIA_VERIFIER_V2_MAX_CLAIMS", "not-a-number")
    assert _verifier_v2_max_claims() == 160
    monkeypatch.setenv("ELEUTHERIA_VERIFIER_V2_MAX_CLAIMS", "-4")
    assert _verifier_v2_max_claims() == 0


def test_citation_audit_max_wait_env_parsing(monkeypatch) -> None:
    monkeypatch.delenv("ELEUTHERIA_CITATION_AUDIT_MAX_WAIT_S", raising=False)
    # 900 s: the pair-level audit of a long answer exceeded the former 180 s
    # ceiling, was abandoned, and the gate blocked the answer as unaudited.
    assert _citation_audit_max_wait() == 900.0
    monkeypatch.setenv("ELEUTHERIA_CITATION_AUDIT_MAX_WAIT_S", "240")
    assert _citation_audit_max_wait() == 240.0
    monkeypatch.setenv("ELEUTHERIA_CITATION_AUDIT_MAX_WAIT_S", "not-a-number")
    assert _citation_audit_max_wait() == 900.0
    monkeypatch.setenv("ELEUTHERIA_CITATION_AUDIT_MAX_WAIT_S", "0")
    assert _citation_audit_max_wait() == 900.0


# ----------------------------------------------------------- verdict merging


@pytest.mark.asyncio
async def test_verdicts_merge_into_citations_ledger_and_grounding(
    monkeypatch,
) -> None:
    monkeypatch.delenv("ELEUTHERIA_VERIFIER_V2_MAX_CLAIMS", raising=False)
    report = _report(
        [
            CitationCheck(
                citation_id="p1",
                status=CitationStatus.REJECTED,
                reasoning='"different passage" does not assert the claim',
                claim="Justin quotes the fate passage.",
            ),
            CitationCheck(
                citation_id="node-2",
                status=CitationStatus.VERIFIED,
                reasoning="explicit support",
            ),
            CitationCheck(
                citation_id="node-3",
                status=CitationStatus.WEAK,
                reasoning='"same topic" but not asserted',
            ),
        ]
    )
    agent = _agent_with_verifier(report)
    answer = _answer_with_citations()

    updated, returned_report = await agent._run_citation_verifier_v2(answer)

    assert returned_report is report
    by_id = {c.id: c for c in updated.citations}
    assert by_id["p1"].verified is False
    assert (by_id["p1"].verification_note or "").startswith("[REJECTED]")
    assert by_id["node-2"].verified is True
    assert by_id["node-3"].verified is False  # WEAK kept but not verified

    # REJECTED citation downgrades the ledger claim citing it (bundle-id
    # suffix match: "work-1::p1" cites passage "p1").
    assert updated.claim_ledger[0].status is ClaimStatus.INSUFFICIENT
    assert updated.claim_ledger[1].status is ClaimStatus.SUPPORTED

    # Honest grounding: 1 verified / 3 audited.
    assert updated.self_rag_evaluation.grounding == 33

    meta = updated.metadata["citation_verifier_v2"]
    assert meta["total"] == 3
    assert meta["rejected"] == 1
    assert meta["failed_citations"][0]["citation_id"] == "p1"
    assert meta["failed_citations"][0]["status"] == "REJECTED"

    # All 3 citations audited → the overwritten grounding is full-coverage.
    grounding_meta = updated.metadata["grounding"]
    assert grounding_meta["score"] == 33
    assert grounding_meta["method"] == "verifier_v2_sample"
    assert grounding_meta["coverage"] == "full"


@pytest.mark.asyncio
async def test_node_verdicts_flow_through_with_their_evidence_kind(
    monkeypatch,
) -> None:
    """Node citations reach the verifier as ``citation_kind="node"`` and the
    audit record keeps the evidence layer of every verdict."""
    monkeypatch.delenv("ELEUTHERIA_VERIFIER_V2_MAX_CLAIMS", raising=False)
    report = _report(
        [
            CitationCheck(
                citation_id="p1",
                status=CitationStatus.VERIFIED,
                reasoning="explicit clause",
            ),
            CitationCheck(
                citation_id="node-2",
                status=CitationStatus.VERIFIED,
                reasoning="record states it",
                evidence_kind="node",
            ),
            CitationCheck(
                citation_id="node-3",
                status=CitationStatus.MISSING,
                reasoning="identity record, 14 characters",
                evidence_kind="node",
            ),
        ]
    )
    agent = _agent_with_verifier(report)

    updated, _ = await agent._run_citation_verifier_v2(_answer_with_citations())

    draft = agent.deps.verifier_v2.verify_draft.call_args.args[0]
    kinds = {claim.citation_id: claim.citation_kind for claim in draft.claims}
    assert kinds == {"p1": "passage", "node-2": "node", "node-3": "node"}

    by_id = {c.id: c for c in updated.citations}
    assert by_id["node-2"].verified is True
    assert by_id["node-3"].verified is False

    meta = updated.metadata["citation_verifier_v2"]
    assert meta["evidence_kinds"] == {
        "p1": "passage",
        "node-2": "node",
        "node-3": "node",
    }
    assert meta["verified_citations"] == ["p1", "node-2"]
    assert meta["failed_citations"] == [
        {
            "citation_id": "node-3",
            "status": "MISSING",
            "claim": "",
            "reasoning": "identity record, 14 characters",
            "parse_error": False,
            "evidence_kind": "node",
            "verified_pairs": 0,
            "pairs": [
                {
                    "sentence_index": 2,
                    "sentence": "A well sourced claim [3].",
                    "clause": "",
                    "status": "MISSING",
                    "reasoning": "identity record, 14 characters",
                    "parse_error": False,
                    "evidence_kind": "node",
                }
            ],
        }
    ]
    assert meta["pairs"] == {
        "total": 3,
        "audited": 3,
        "verified": 2,
        "weak": 0,
        "rejected": 0,
        "missing": 1,
        "unaudited": 0,
    }


@pytest.mark.asyncio
async def test_verifier_receives_only_sampled_claims(monkeypatch) -> None:
    monkeypatch.setenv("ELEUTHERIA_VERIFIER_V2_MAX_CLAIMS", "1")
    report = _report(
        [
            CitationCheck(
                citation_id="p1",
                status=CitationStatus.VERIFIED,
                reasoning="ok",
            )
        ]
    )
    agent = _agent_with_verifier(report)
    answer = _answer_with_citations()

    updated, _ = await agent._run_citation_verifier_v2(answer)

    draft = agent.deps.verifier_v2.verify_draft.call_args.args[0]
    assert [claim.citation_id for claim in draft.claims] == ["p1"]
    assert updated.metadata["citation_verifier_v2"]["sampled"] == 1

    # Only 1 of 3 citations audited: a perfect score on the sample must be
    # presented as partial coverage, never as full grounding.
    grounding_meta = updated.metadata["grounding"]
    assert grounding_meta["score"] == 100
    assert grounding_meta["method"] == "verifier_v2_sample"
    assert grounding_meta["audited_citations"] == 1
    assert grounding_meta["total_citations"] == 3
    assert grounding_meta["coverage"] == "partial: 1/3 audited"


@pytest.mark.asyncio
async def test_zero_budget_skips_verifier(monkeypatch) -> None:
    monkeypatch.setenv("ELEUTHERIA_VERIFIER_V2_MAX_CLAIMS", "0")
    agent = _agent_with_verifier(_report([]))
    answer = _answer_with_citations()

    updated, report = await agent._run_citation_verifier_v2(answer)

    assert report is None
    assert updated.answer == answer.answer  # internal draft retained for diagnosis
    assert all(c.verified is False for c in updated.citations)
    assert updated.metadata["citation_verifier_v2"]["status"] == "disabled"
    assert updated.metadata["citation_verifier_v2"]["aborted"] is True
    agent.deps.verifier_v2.verify_draft.assert_not_awaited()


# ----------------------------------------------------------- SSE emission


@pytest.mark.asyncio
async def test_stream_citation_audit_emits_citation_verified_events(
    monkeypatch,
) -> None:
    monkeypatch.delenv("ELEUTHERIA_VERIFIER_V2_MAX_CLAIMS", raising=False)
    report = _report(
        [
            CitationCheck(
                citation_id="p1",
                status=CitationStatus.REJECTED,
                reasoning='"mismatch quote"',
            ),
            CitationCheck(
                citation_id="node-2",
                status=CitationStatus.VERIFIED,
                reasoning="ok",
            ),
        ]
    )
    agent = _agent_with_verifier(report)
    answer = _answer_with_citations()
    holder: dict[str, Any] = {}

    events = [
        json.loads(ev) async for ev in agent._stream_citation_audit(answer, holder)
    ]

    verified_events = [e for e in events if e["type"] == "citation_verified"]
    assert [(e["passage_id"], e["verified"], e["status"]) for e in verified_events] == [
        ("p1", False, "REJECTED"),
        ("node-2", True, "VERIFIED"),
    ]
    assert all("reason" in e for e in verified_events)

    stage_events = [e for e in events if e["type"] == "stage_complete"]
    assert stage_events[-1]["stage"] == "citation_audit"
    assert stage_events[-1]["metadata"]["rejected"] == 1

    merged = holder["answer"]
    assert merged.metadata["citation_verifier_v2"]["rejected"] == 1


@pytest.mark.asyncio
async def test_stream_citation_audit_fails_closed_on_error() -> None:
    deps = make_deps()
    verifier = AsyncMock()
    verifier.verify_draft = AsyncMock(side_effect=RuntimeError("provider down"))
    deps.verifier_v2 = verifier
    agent = ScholarlyAgent(deps)
    answer = _answer_with_citations()
    holder: dict[str, Any] = {}

    events = [
        json.loads(ev) async for ev in agent._stream_citation_audit(answer, holder)
    ]

    # No citation_verified events; the stage closes with an explicit blocking
    # status and every citation loses the optimistic resolution-only flag.
    assert not [e for e in events if e["type"] == "citation_verified"]
    assert events[-1]["type"] == "stage_complete"
    assert events[-1]["metadata"] == {"status": "error", "publishable": False}
    merged = holder["answer"]
    assert merged.answer == answer.answer
    assert all(c.verified is False for c in merged.citations)
    v2_meta = merged.metadata["citation_verifier_v2"]
    assert v2_meta["status"] == "error"
    assert "provider down" in v2_meta["reason"]


# ------------------------------------- modern-language "original" rows (lead run)

# Works ingested in English carry ``passage_role="original"`` with
# ``ancient_works.language="eng"``. The lead pipeline registered them by bare
# UUID from the sub-agent dossiers and the judge answered "could not be
# re-fetched" for every one (8 MISSING pairs on one answer). Shapes measured
# in production; the text is a stand-in of the same length class.
MODERN_ORIGINAL_ROWS = [
    ("68fced1b-0000-4000-8000-000000000001", "Origen, Philocalia 26.5", 3915),
    ("e63373b3-0000-4000-8000-000000000002", "Diss. 2.8.13-21", 1408),
    ("688bbd38-0000-4000-8000-000000000003", "Justin, 1 Apology 43", 1238),
    ("0338fcd0-0000-4000-8000-000000000004", "via Cicero, De Fato 42-43", 349),
    ("7a3ff0e3-0000-4000-8000-000000000005", "1.45", 951),
]


def _english_original_row(passage_id: str, ref: str, chars: int) -> dict[str, Any]:
    text = ("That which is in our power is the use of impressions. " * 80)[:chars]
    text = text.rstrip() + "x" * (chars - len(text.rstrip()))
    return {
        "passage_id": passage_id,
        "text_content": text,
        "canonical_ref": ref,
        "cts_urn": None,
        "passage_role": "original",
        "title": "An English edition",
        "author": "An ancient author",
        "language": "eng",
    }


@pytest.mark.asyncio
@pytest.mark.parametrize(("passage_id", "ref", "chars"), MODERN_ORIGINAL_ROWS)
async def test_english_original_row_is_fetched_as_translation_tier_evidence(
    passage_id: str, ref: str, chars: int
) -> None:
    db = _FakeDB([[_english_original_row(passage_id, ref, chars)]])
    fetch = build_db_passage_fetcher(db)

    fetched = await fetch(passage_id)

    assert fetched is not None
    assert fetched["kind"] == "translation"
    assert fetched["modern_language_original"] is True
    assert fetched["passage_role"] == "original"
    assert fetched["language"] == "eng"
    assert fetched["label"] == ref
    assert len(fetched["text"]) == chars
    assert fetched["source"] == "passages"


@pytest.mark.asyncio
async def test_ancient_original_row_carries_no_translation_flag() -> None:
    db = _FakeDB(
        [
            [
                {
                    "passage_id": PASSAGE_UUID,
                    "text_content": BUNDLE_GREEK,
                    "canonical_ref": "43",
                    "passage_role": "original",
                    "language": "grc",
                }
            ]
        ]
    )
    fetch = build_db_passage_fetcher(db)

    fetched = await fetch(PASSAGE_UUID)

    assert fetched is not None
    assert "kind" not in fetched
    assert "modern_language_original" not in fetched
    assert fetched["text"] == BUNDLE_GREEK


@pytest.mark.asyncio
async def test_original_row_in_an_unknown_language_stays_unfetchable() -> None:
    db = _FakeDB(
        [
            [
                {
                    "passage_id": PASSAGE_UUID,
                    "text_content": "some text",
                    "passage_role": "original",
                    "language": "xxx",
                }
            ]
        ]
    )
    fetch = build_db_passage_fetcher(db)

    assert await fetch(PASSAGE_UUID) is None


@pytest.mark.asyncio
async def test_translation_row_without_an_authoritative_node_stays_none() -> None:
    """A bare-UUID translation row has no provenance: still ``None``."""
    db = _FakeDB(
        [
            [
                {
                    "passage_id": PASSAGE_UUID,
                    "text_content": "A translation of unknown provenance.",
                    "passage_role": "translation",
                    "language": "eng",
                }
            ]
        ]
    )
    fetch = build_db_passage_fetcher(db)

    assert await fetch(PASSAGE_UUID) is None


@pytest.mark.asyncio
async def test_english_original_blocked_by_citability_stays_none() -> None:
    db = _FakeDB([[_english_original_row(PASSAGE_UUID, "26.5", 400)]])
    fetch = build_db_passage_fetcher(
        db,
        node_lookup={
            PASSAGE_UUID: {
                "id": PASSAGE_UUID,
                "type": "passage",
                "metadata": {
                    "passage_role": "original",
                    "citability": "discoverable_only",
                },
            }
        },
    )

    assert await fetch(PASSAGE_UUID) is None


@pytest.mark.asyncio
@pytest.mark.parametrize("status", ["VERIFIED", "WEAK", "REJECTED"])
async def test_translation_tier_evidence_is_audited_and_follows_the_judge(
    status: str,
) -> None:
    passage_id, ref, chars = MODERN_ORIGINAL_ROWS[0]
    db = _FakeDB([[_english_original_row(passage_id, ref, chars)]])
    llm = AsyncMock()
    llm.generate = AsyncMock(
        return_value=json.dumps({"status": status, "reasoning": "judged"})
    )
    verifier = CitationVerifierV2(
        llm=llm, passage_fetcher=build_db_passage_fetcher(db), tool_mode="off"
    )

    check = await verifier.verify_one(
        "Origen holds that the use of impressions is in our power", passage_id
    )

    assert check.status is CitationStatus(status)
    assert check.evidence_kind == "translation"
    assert check.parse_error is False
    assert check.passage_excerpt.startswith("That which is in our power")
    prompt = llm.generate.call_args.args[0]
    assert "translation-tier" in prompt
    assert "not the ancient-language original" in prompt
    assert "a verbatim Greek or Latin quotation cannot be VERIFIED" in prompt
    assert f'<passage id="citation:{passage_id}">' in prompt


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("returned_urn", "accepted"),
    [
        ("urn:cts:latinLit:phi0474.phi054.perseus-lat1:41", True),
        ("urn:cts:latinLit:phi0474.phi054.other-edition:41", True),
        ("urn:cts:latinLit:phi0474.phi054.perseus-lat1:42", False),
        ("urn:cts:latinLit:phi1254.phi001.perseus-lat1:41", False),
    ],
)
async def test_ancient_reference_accepts_another_edition_of_same_locus_not_another_passage(
    returned_urn, accepted
):
    node = {
        "id": "passage_cicero_test",
        "type": "passage",
        "metadata": {
            "language": "lat",
            "author": "Cicero",
            "work_title": "De Fato",
            "canonical_ref": "De Fato 41",
            "cts_urn": "urn:cts:latinLit:phi0474.phi054:41",
            "passage_role": "original",
            "related_corpus_passage_id": PASSAGE_UUID,
            "parity_status": "related_non_exact_pending_edition_adjudication",
            "needs_page_verification": "No edition page recorded",
        },
    }
    db = _FakeDB(
        [
            [
                {
                    "passage_id": PASSAGE_UUID,
                    "citation_type": "related_passage_non_exact",
                }
            ],
            [
                {
                    "passage_id": PASSAGE_UUID,
                    "canonical_ref": "41",
                    "cts_urn": returned_urn,
                    "text_content": "Source text fetched from the selected witness.",
                    "passage_role": "original",
                    "language": "lat",
                    "author": "Cicero",
                    "title": "De Fato",
                }
            ],
        ]
    )
    fetch = build_db_passage_fetcher(db, node_lookup={"passage_cicero_test": node})
    result = await fetch("passage_cicero_test")
    assert (result is not None) is accepted
    if accepted:
        assert result["source_resolution"] == "same_conventional_locus"
        assert result["cts_urn"] == returned_urn
        assert result["text"] == "Source text fetched from the selected witness."
