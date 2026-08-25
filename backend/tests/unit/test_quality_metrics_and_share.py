"""Unit tests for the G9 citation/claim-ledger contract pieces.

* :func:`backend.routes.graphrag_extras._build_quality_metrics` — measured
  values must come from the pipeline reports; estimates must be labelled.
* :func:`backend.routes.share._render_claims_section` — the share page must
  surface claims + verification provenance, never silently drop it.
"""

from __future__ import annotations

import uuid

import pytest
from fastapi import HTTPException

from backend.routes.graphrag_extras import _build_quality_metrics
from backend.routes.share import (
    _render_claims_section,
    _render_page,
    create_share_link,
)

# ---------- _build_quality_metrics ----------


def test_quality_metrics_uses_measured_grounding_when_present() -> None:
    metadata = {
        "grounding": {
            "score": 88,
            "method": "verifier_v2_sample",
            "coverage": "full",
        },
        "quality_badge": "High",
    }
    metrics = _build_quality_metrics(
        metadata, citation_count=2, node_count=10, has_sources=True
    )
    assert metrics["confidence_score"] == 88
    assert metrics["grounding_score"] == 88
    assert metrics["accuracy"] == 0.88
    assert metrics["accuracy_method"] == "measured:verifier_v2_sample"
    assert metrics["confidence_method"].startswith("measured:")
    assert metrics["quality_badge"] == "High"
    # No estimate caveat for accuracy/confidence when measured
    assert not any("heuristic" in c for c in metrics["caveats"])


def test_quality_metrics_labels_estimates_when_no_audit_ran() -> None:
    metrics = _build_quality_metrics(
        {}, citation_count=3, node_count=10, has_sources=True
    )
    assert metrics["grounding_score"] is None
    assert metrics["accuracy_method"] == "estimate:citation_count_heuristic"
    assert metrics["confidence_method"] == "estimate:count_heuristics"
    assert metrics["completeness_method"] == "estimate:context_node_count"
    assert any("estimate" in c for c in metrics["caveats"])
    # No fabricated clarity value anymore
    assert "clarity" not in metrics


def test_quality_metrics_partial_coverage_gets_caveat() -> None:
    metadata = {
        "grounding": {
            "score": 100,
            "method": "verifier_v2_sample",
            "coverage": "partial: 5/12 audited",
        }
    }
    metrics = _build_quality_metrics(
        metadata, citation_count=12, node_count=30, has_sources=True
    )
    assert metrics["confidence_score"] == 100
    assert any("sample" in c for c in metrics["caveats"])


def test_quality_metrics_surfaces_failed_audit_and_text_verification() -> None:
    metadata = {
        "citation_verifier_v2": {"total": 6, "verified": 4, "rejected": 1, "missing": 1},
        "text_verification": {"verified": 2, "unverified": 1},
    }
    metrics = _build_quality_metrics(
        metadata, citation_count=6, node_count=10, has_sources=True
    )
    assert metrics["citation_audit"]["rejected"] == 1
    assert metrics["text_verification"]["unverified"] == 1
    assert any("flagged 2 claim" in c for c in metrics["caveats"])
    assert any("could not be verified" in c for c in metrics["caveats"])


# ---------- share renderer ----------


def test_share_claims_section_renders_claims_and_notes() -> None:
    html_out = _render_claims_section(
        [
            {
                "claim": "Chrysippus distinguishes perfect and auxiliary causes",
                "evidence_ids": ["P1"],
                "status": "supported",
            },
            {"claim": "An unsupported claim", "evidence_ids": [], "status": "insufficient"},
        ],
        {
            "citation_verifier_v2": {"total": 4, "verified": 3},
            "text_verification": {"verified": 2, "unverified": 1},
            "grounding": {"score": 75, "coverage": "full"},
        },
        {"P1": "Cic. De Fato 41"},
    )
    assert "Affirmations et preuves" in html_out
    assert "Chrysippus distinguishes" in html_out
    assert "Cic. De Fato 41" in html_out
    assert "insuffisante" in html_out
    assert "3/4" in html_out
    assert "non vérifié" in html_out
    assert "75/100" in html_out


def test_share_claims_section_empty_for_legacy_traces() -> None:
    assert _render_claims_section([], {}, {}) == ""


def test_share_page_escapes_claim_text_and_renders_verdicts() -> None:
    page = _render_page(
        "q",
        "a",
        [
            {
                "ref": "P1",
                "id": "P1",
                "type": "passage",
                "label": "Cic. De Fato 41",
                "verified": True,
                "verification_note": "[VERIFIED] supports the claim",
            },
            {
                "ref": "P2",
                "id": "P2",
                "type": "passage",
                "label": "Other",
                "verified": False,
            },
        ],
        None,
        claim_ledger=[
            {
                "claim": "<script>alert(1)</script>",
                "evidence_ids": ["P1"],
                "status": "supported",
            }
        ],
        answer_metadata={},
    )
    assert "<script>" not in page
    assert "&lt;script&gt;" in page
    assert "vérifiée" in page
    assert "non vérifiée" in page
    assert "Cic. De Fato 41" in page


class _AnonymousTraceDB:
    async def fetchrow(self, *_args, **_kwargs):
        return {"trace_id": uuid.uuid4(), "user_id": None}

    async def execute(self, *_args, **_kwargs):  # pragma: no cover - must not run
        raise AssertionError("anonymous trace must not reach share INSERT")


async def test_anonymous_trace_cannot_be_claimed_and_shared() -> None:
    with pytest.raises(HTTPException) as exc:
        await create_share_link(
            str(uuid.uuid4()),
            {"user_id": str(uuid.uuid4())},
            _AnonymousTraceDB(),  # type: ignore[arg-type]
        )
    assert exc.value.status_code == 403


# ---------- producer/consumer contract integration ----------
# Regression for the G4/G9 contract mismatch: both sides' suites passed
# against hand-written dicts while the real producer
# (VerificationResult.to_metadata) emitted a different shape and every
# consumer surface stayed silently dead. These tests feed the REAL
# producer output through the consumers.


def _real_text_verification_metadata() -> dict:
    from eleutheria_graphrag.agents.text_verifier import (
        SpanCheck,
        VerificationResult,
    )

    result = VerificationResult()
    result.verified_spans.append(
        SpanCheck(
            text="placeholder verified span (English, no ancient text)",
            language="greek",
            position=0,
            status="bundle",
        )
    )
    result.unverified_spans.append(
        SpanCheck(
            text="placeholder unverified span (English, no ancient text)",
            language="greek",
            position=10,
            status="unverified",
        )
    )
    result.bundle_whitelisted = 1
    result.db_checked = 1
    return {**result.to_metadata(), "enforced": False}


def test_quality_metrics_consumes_real_verifier_output() -> None:
    metadata = {"text_verification": _real_text_verification_metadata()}
    metrics = _build_quality_metrics(
        metadata, citation_count=2, node_count=10, has_sources=True
    )
    assert metrics["text_verification"]["unverified"] == 1
    assert any("could not be verified" in c for c in metrics["caveats"])


def test_share_claims_section_consumes_real_verifier_output() -> None:
    html_out = _render_claims_section(
        [{"claim": "A claim", "evidence_ids": ["P1"], "status": "supported"}],
        {"text_verification": _real_text_verification_metadata()},
        {"P1": "Cic. De Fato 41"},
    )
    assert "non vérifié" in html_out
