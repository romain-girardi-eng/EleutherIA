"""Deterministic publication-gate truth table.

Two classes of outcome: safety-class failures BLOCK the whole answer; per-
citation verdicts WITHHOLD the citing sentences and leave the answer
publishable (``status == "partial"``).
"""

from __future__ import annotations

import pytest

from eleutheria_graphrag.agents.publication_gate import (
    POLICY,
    evaluate_publication,
    is_cacheable,
    is_publishable,
)


def _failed(citation_id: str, status: str, *, parse_error: bool = False) -> dict:
    return {
        "citation_id": citation_id,
        "status": status,
        "claim": "claim",
        "reasoning": "reasoning",
        "parse_error": parse_error,
    }


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
        "verified_citations": [f"c{i}" for i in range(20)],
        "failed_citations": [],
    }
    audit.update(audit_overrides)
    return {
        "scholar_synthesis": {"status": "ok", "degraded": False},
        "content_gate": {"status": "passed", "passed": True},
        "citation_verifier_v2": audit,
    }


def _one_failure(status: str, *, parse_error: bool = False) -> dict:
    counter = {
        "WEAK": "weak",
        "REJECTED": "rejected",
        "MISSING": "missing",
    }[status]
    overrides = {
        "status": "failed",
        "verified": 19,
        counter: 1,
        "verified_citations": [f"c{i}" for i in range(19)],
        "failed_citations": [_failed("c19", status, parse_error=parse_error)],
    }
    if parse_error:
        overrides["parse_errors"] = 1
    return _metadata(**overrides)


def test_full_clean_audit_is_publishable_with_nothing_withheld() -> None:
    decision = evaluate_publication(_metadata())
    assert decision.publishable is True
    assert decision.status == "passed"
    assert decision.withheld == {}
    assert decision.as_metadata()["policy"] == (
        "content_gate_and_sentence_withholding_v2"
    )


# Formerly every one of these blocked the whole answer.  A recorded per-
# citation verdict now withholds that citation's sentences instead.
@pytest.mark.parametrize(
    ("status", "parse_error", "reason"),
    [
        ("WEAK", False, "weak"),
        ("REJECTED", False, "rejected"),
        ("MISSING", False, "missing"),
        ("WEAK", True, "verifier_error"),
    ],
)
def test_recorded_verdict_withholds_instead_of_blocking(
    status, parse_error, reason
) -> None:
    decision = evaluate_publication(_one_failure(status, parse_error=parse_error))
    assert decision.publishable is True
    assert decision.status == "partial"
    assert decision.withheld == {"c19": reason}
    assert decision.reasons == ()


def test_per_citation_verifier_failure_is_not_an_infrastructure_block() -> None:
    """One provider failure among many verdicts withholds one sentence."""
    decision = evaluate_publication(_one_failure("WEAK", parse_error=True))
    assert decision.publishable is True
    assert "citation_audit_infrastructure_failure" not in decision.reasons
    assert decision.withheld == {"c19": "verifier_error"}


def test_failure_counts_without_recorded_ids_block() -> None:
    """Fail closed: counts alone cannot say WHICH sentences to withhold."""
    metadata = _metadata(verified=19, weak=1, status="failed")
    decision = evaluate_publication(metadata)
    assert decision.publishable is False
    assert "citation_verdicts_unrecorded" in decision.reasons


def test_verifier_exception_blocks_the_whole_answer() -> None:
    metadata = _metadata(
        status="error",
        total=0,
        audited_citations=0,
        verified=0,
        aborted=True,
        infrastructure_failure=True,
        reason="RuntimeError: provider down",
    )
    del metadata["citation_verifier_v2"]["verified_citations"]
    decision = evaluate_publication(metadata)
    assert decision.publishable is False
    assert "citation_audit_not_passed" in decision.reasons
    assert "citation_audit_infrastructure_failure" in decision.reasons


def test_audit_aborted_before_any_verdict_blocks() -> None:
    metadata = _metadata(
        status="failed",
        total=0,
        audited_citations=0,
        verified=0,
        aborted=True,
        verified_citations=[],
    )
    decision = evaluate_publication(metadata)
    assert decision.publishable is False
    assert "citation_audit_aborted" in decision.reasons


def test_rejection_rate_abort_with_verdicts_withholds() -> None:
    """A rejection-rate abort still carries verdicts: apply them per sentence."""
    failed = [_failed(f"c{i}", "REJECTED") for i in range(10, 20)]
    metadata = _metadata(
        status="failed",
        verified=10,
        rejected=10,
        aborted=True,
        warning="Citation rejection rate 50% exceeds abort threshold 50%",
        verified_citations=[f"c{i}" for i in range(10)],
        failed_citations=failed,
    )
    decision = evaluate_publication(metadata)
    assert decision.publishable is True
    assert decision.status == "partial"
    assert len(decision.withheld) == 10
    assert decision.audit_warning is not None


def test_partial_audit_without_verified_record_blocks() -> None:
    metadata = _metadata(total=8, sampled=8, audited_citations=8, verified=8)
    del metadata["citation_verifier_v2"]["verified_citations"]
    decision = evaluate_publication(metadata)
    assert decision.publishable is False
    assert "citation_audit_partial" in decision.reasons


def test_partial_audit_with_verified_record_is_publishable() -> None:
    """Unaudited citations are withheld at apply time, not blocked."""
    metadata = _metadata(
        total=8,
        sampled=8,
        audited_citations=8,
        verified=8,
        verified_citations=[f"c{i}" for i in range(8)],
    )
    decision = evaluate_publication(metadata)
    assert decision.publishable is True
    assert decision.verdict_record is True


@pytest.mark.parametrize(
    "audit_status", ["unavailable", "disabled", "skipped_content_gate", ""]
)
def test_audit_that_never_ran_blocks(audit_status) -> None:
    metadata = _metadata(
        status=audit_status,
        total=0,
        audited_citations=0,
        verified=0,
        aborted=True,
        verified_citations=[],
    )
    decision = evaluate_publication(metadata)
    assert decision.publishable is False
    assert "citation_audit_not_passed" in decision.reasons


def test_zero_auditable_citations_block() -> None:
    metadata = _metadata(
        status="failed",
        total=0,
        audited_citations=0,
        total_citations=0,
        verified=0,
        aborted=True,
        verified_citations=[],
    )
    decision = evaluate_publication(metadata)
    assert decision.publishable is False
    assert "no_auditable_citations" in decision.reasons


def test_content_gate_failure_blocks_even_clean_citations() -> None:
    metadata = _metadata()
    metadata["content_gate"] = {"status": "failed", "passed": False}
    decision = evaluate_publication(metadata)
    assert decision.publishable is False
    assert "content_gate_not_passed" in decision.reasons


def test_degraded_synthesis_is_a_warning_not_a_block() -> None:
    """Synthesis quality is not a safety-class failure: the audited answer is
    published, flagged, and kept out of the caches."""
    metadata = _metadata()
    metadata["scholar_synthesis"] = {"status": "degraded", "degraded": True}
    decision = evaluate_publication(metadata)
    assert decision.publishable is True
    assert decision.reasons == ()
    assert decision.warnings == ("scholar_synthesis_degraded",)
    assert is_publishable(metadata) is True
    assert is_cacheable(metadata) is False
    assert is_cacheable(_metadata()) is True


def test_partial_verdict_is_publishable_but_not_cacheable() -> None:
    """One WEAK verdict withholds a sentence and is published; the holed
    prose is never admitted to a cache (an unapplied evaluation, an applied
    ``partial`` record, and a partial audit under a verified-id record)."""
    metadata = _metadata(
        status="failed",
        verified=19,
        weak=1,
        failed_citations=[_failed("c19", "WEAK")],
    )
    assert is_publishable(metadata) is True
    assert is_cacheable(metadata) is False

    applied = {
        **_metadata(),
        "publication_gate": {
            "policy": POLICY,
            "applied": True,
            "publishable": True,
            "status": "partial",
            "reasons": [],
            "warnings": [],
        },
    }
    assert is_publishable(applied) is True
    assert is_cacheable(applied) is False
    applied["publication_gate"]["status"] = "passed"
    assert is_cacheable(applied) is True

    unaudited = _metadata(audited_citations=19)
    assert is_publishable(unaudited) is True
    assert is_cacheable(unaudited) is False


def test_unrecorded_failure_ids_without_verified_record_block() -> None:
    """Counts announce two failures, one id is recorded and there is no
    verified-id record: the second failure could not be withheld."""
    metadata = _metadata(
        status="failed",
        verified=18,
        rejected=2,
        failed_citations=[_failed("c19", "REJECTED")],
    )
    del metadata["citation_verifier_v2"]["verified_citations"]
    decision = evaluate_publication(metadata)
    assert decision.publishable is False
    assert "citation_verdicts_unrecorded" in decision.reasons


def test_unrecorded_failure_ids_with_verified_record_withhold() -> None:
    """Same counts, but the audit recorded which ids it verified: the
    unrecorded failure is withheld as unaudited at apply time."""
    metadata = _metadata(
        status="failed",
        verified=18,
        rejected=2,
        verified_citations=[f"c{i}" for i in range(18)],
        failed_citations=[_failed("c19", "REJECTED")],
    )
    decision = evaluate_publication(metadata)
    assert decision.publishable is True
    assert decision.withheld == {"c19": "rejected"}


def test_unverified_ancient_text_left_in_prose_blocks() -> None:
    metadata = _metadata()
    metadata["text_verification"] = {"verified": 3, "unverified": 1, "enforced": False}
    decision = evaluate_publication(metadata)
    assert decision.publishable is False
    assert "unverified_ancient_text_present" in decision.reasons


def test_unverified_ancient_text_already_removed_does_not_block() -> None:
    metadata = _metadata()
    metadata["text_verification"] = {"verified": 3, "unverified": 1, "enforced": True}
    decision = evaluate_publication(metadata)
    assert decision.publishable is True


def test_missing_metadata_blocks() -> None:
    decision = evaluate_publication({})
    assert decision.publishable is False
    assert "content_gate_not_passed" in decision.reasons
    assert "citation_audit_not_passed" in decision.reasons


@pytest.mark.parametrize("marker", ["P99", "passage_missing: Invented locus"])
def test_unregistered_inline_reference_cannot_escape_the_audit_denominator(marker):
    from eleutheria_graphrag.agents.publication_gate import apply_publication_verdict

    payload = {
        "answer": f"Supported [P1]. Unchecked assertion [{marker}].",
        "citations": [{"id": "c0", "ref": "P1", "type": "passage"}],
        "metadata": _metadata(),
        "claim_ledger": [],
    }
    public = apply_publication_verdict(payload)
    assert "Supported [P1]" in public["answer"]
    assert "Unchecked assertion" not in public["answer"]
    assert public["metadata"]["publication_gate"]["status"] == "partial"


def test_full_prefixed_passage_id_is_a_registered_citation():
    from eleutheria_graphrag.agents.publication_gate import apply_publication_verdict

    payload = {
        "answer": "Supported [passage_cic_fat_41: Cicero, De fato 41].",
        "citations": [
            {"id": "passage_cic_fat_41", "ref": "passage_cic_fat_41", "type": "passage"}
        ],
        "metadata": _metadata(verified_citations=["passage_cic_fat_41"]),
        "claim_ledger": [],
    }
    public = apply_publication_verdict(payload)
    assert public["answer"] == payload["answer"]
