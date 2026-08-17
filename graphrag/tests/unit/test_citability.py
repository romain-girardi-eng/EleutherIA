"""Regression tests for the central honesty/citability policy (C-03)."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from eleutheria_graphrag.agents.citability import (
    CitabilityTier,
    evidence_policy,
)
from eleutheria_graphrag.agents.controversy_map import serialize_controversy_frames
from eleutheria_graphrag.agents.scholar_verification import verify_citations_on_frames
from eleutheria_graphrag.agents.state import (
    ClaimStatus,
    ControversyFrame,
    ControversyMap,
    PassageRef,
)
from eleutheria_graphrag.agents.tools.search_nodes import SearchNodesTool
from eleutheria_graphrag.services.snapshot_retrieval import passage_row_from_node


@pytest.mark.parametrize(
    "metadata",
    [
        {"citation_verdict": "verified"},
        {"citation_verdict": "corrected"},
        {"citation_verdict": "false_positive_attested"},
        {},
    ],
)
def test_verified_marker_classes_are_citable(metadata: dict) -> None:
    assert evidence_policy(metadata).tier is CitabilityTier.CITABLE


@pytest.mark.parametrize(
    ("metadata", "marker"),
    [
        ({"citation_verdict": "bibliographic_import"}, "bibliographic_import"),
        ({"bibliographic_import": True}, "bibliographic_import"),
        ({"needs_reocr": True}, "needs_reocr"),
        ({"needs_locus_mapping": True}, "needs_locus_mapping"),
        ({"needs_text_ingestion": True}, "needs_text_ingestion"),
        ({"needs_reference_remapping": True}, "needs_reference_remapping"),
        ({"translation_blocked_ocr": True}, "translation_blocked_ocr"),
        ({"passage_role": "apparatus"}, "passage_role=apparatus"),
        ({"passage_role": "editorial_synthesis"}, "passage_role=editorial_synthesis"),
    ],
)
def test_debt_marker_classes_are_discoverable_only(
    metadata: dict, marker: str
) -> None:
    decision = evidence_policy(metadata)
    assert decision.tier is CitabilityTier.DISCOVERABLE_ONLY
    assert marker in decision.marker
    assert "do not" in decision.prompt_notice.lower()


def test_explicit_block_wins_over_discovery_marker() -> None:
    decision = evidence_policy(
        {"citation_verdict": "blocked", "needs_text_ingestion": True}
    )
    assert decision.tier is CitabilityTier.BLOCKED
    assert decision.discoverable is False


def test_stringified_node_metadata_is_normalized() -> None:
    decision = evidence_policy(
        {"metadata": '{"passage_role":"apparatus","needs_reocr":false}'}
    )
    assert decision.tier is CitabilityTier.DISCOVERABLE_ONLY
    assert decision.marker == "passage_role=apparatus"


@pytest.mark.asyncio
async def test_discovery_node_informs_search_without_exposing_claim_text() -> None:
    raw_claim = "UNREAD ABSTRACT MUST NOT BECOME QUOTABLE EVIDENCE"
    node = {
        "id": "pub_unread",
        "label": "Unread bibliography on Origen",
        "type": "publication",
        "description": raw_claim,
        "metadata": {"citation_verdict": "bibliographic_import"},
    }
    deps = SimpleNamespace(node_lookup={"pub_unread": node}, pagerank_scores={})
    result = await SearchNodesTool(deps).execute({"query": "Origen"})
    assert result.nodes[0].node_id == "pub_unread"
    assert result.nodes[0].evidence_tier == "discoverable_only"
    assert result.nodes[0].description == ""
    assert "UNREAD BIBLIOGRAPHY" in result.nodes[0].evidence_notice


def test_flagged_snapshot_passage_keeps_locus_but_not_text() -> None:
    raw_text = "BROKEN OCR MUST NEVER ENTER A QUOTE"
    node = {
        "id": "passage_flagged",
        "label": "Flagged passage",
        "type": "passage",
        "description": raw_text,
        "metadata": {
            "canonical_ref": "Cons. 2.3",
            "needs_reocr": True,
        },
    }
    deps = SimpleNamespace(
        node_lookup={"passage_flagged": node},
        outgoing_edges={},
        incoming_edges={},
    )
    row = passage_row_from_node(deps, "passage_flagged")
    assert row is not None
    assert row["canonical_ref"] == "Cons. 2.3"
    assert row["evidence_tier"] == "discoverable_only"
    assert row["text_content"] == ""
    assert raw_text not in str(row)


def test_flagged_passage_is_prompt_notice_not_primary_quote() -> None:
    raw_text = "TEXT THAT MUST NOT APPEAR"
    flagged = PassageRef(
        passage_id="flagged",
        canonical_ref="PG 18.1",
        original_text=raw_text,
        evidence_tier="discoverable_only",
        evidence_notice="FLAGGED TEXT — apparatus; discovery only; do not quote",
    )
    frame = ControversyFrame(
        frame_id="f",
        title="Debt",
        flagged_passages=[flagged],
    )
    rendered = serialize_controversy_frames([frame])
    assert "DISCOVERY-ONLY TEXTS" in rendered
    assert "do not quote" in rendered
    assert raw_text not in rendered

    cmap = ControversyMap(frames=[frame])
    report = verify_citations_on_frames("Claim [passage_flagged].", cmap)
    assert report.verdicts[0].status is ClaimStatus.UNVERIFIED

