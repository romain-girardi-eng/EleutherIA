"""Deterministic publication-gate truth table."""

from __future__ import annotations

import pytest

from eleutheria_graphrag.agents.publication_gate import evaluate_publication


def _metadata(**audit_overrides):
    audit = {
        "status": "passed",
        "total": 20,
        "sampled": 20,
        "audited_citations": 20,
        "total_citations": 20,
        "verified": 20,
        "weak": 0,
        "rejected": 0,
        "missing": 0,
        "parse_errors": 0,
        "aborted": False,
    }
    audit.update(audit_overrides)
    return {
        "scholar_synthesis": {"status": "ok", "degraded": False},
        "content_gate": {"status": "passed", "passed": True},
        "citation_verifier_v2": audit,
    }


def test_full_clean_audit_is_publishable() -> None:
    assert evaluate_publication(_metadata()).publishable is True


@pytest.mark.parametrize(
    ("overrides", "reason"),
    [
        ({"verified": 19, "weak": 1, "status": "failed"}, "weak_citations_present"),
        (
            {"verified": 19, "rejected": 1, "status": "failed"},
            "rejected_citations_present",
        ),
        (
            {"verified": 19, "missing": 1, "status": "failed"},
            "missing_citations_present",
        ),
        (
            {"verified": 19, "parse_errors": 1, "status": "failed"},
            "citation_audit_parse_errors",
        ),
        ({"aborted": True, "status": "failed"}, "citation_audit_aborted"),
        (
            {"total": 8, "sampled": 8, "audited_citations": 8},
            "citation_audit_partial",
        ),
    ],
)
def test_every_non_clean_or_partial_audit_blocks(overrides, reason) -> None:
    decision = evaluate_publication(_metadata(**overrides))
    assert decision.publishable is False
    assert reason in decision.reasons


def test_content_gate_failure_blocks_even_clean_citations() -> None:
    metadata = _metadata()
    metadata["content_gate"] = {"status": "failed", "passed": False}
    decision = evaluate_publication(metadata)
    assert decision.publishable is False
    assert "content_gate_not_passed" in decision.reasons
