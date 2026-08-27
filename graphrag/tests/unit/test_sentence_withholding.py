"""Sentence-level withholding: prose surgery and verdict application.

Covers the pure text helper (:func:`withhold_sentences`), the model-form
application (:func:`annotate_publication_decision`) and the mapping-form
application (:func:`apply_publication_verdict`), and pins that both forms make
the same decision on the same draft.
"""

from __future__ import annotations

from eleutheria_graphrag.agents.publication_gate import (
    WITHHELD_SENTENCE_MARKER,
    annotate_publication_decision,
    apply_publication_verdict,
    is_cacheable,
    is_publishable,
    withhold_sentences,
)
from eleutheria_graphrag.agents.state import (
    Citation,
    ClaimLedgerItem,
    ClaimStatus,
    ScholarlyAnswer,
)

MARK = WITHHELD_SENTENCE_MARKER

LEGACY_PROSE = (
    "Justin quotes the fate passage [P1]. A weakly sourced claim [2]. "
    "A well sourced claim [3]."
)

DIALECTICAL_SENTENCE = (
    "Bobzien holds the ancients had no free-will problem "
    "[P_bobzien_no_problem: Bobzien, 1998 p. 330], whereas Frede dates a notion "
    "of will to Epictetus [P_frede_epictetus: Frede, 2011 p. 44]; the two "
    "positions argue over the Stoic doctrine of assent recorded at "
    "[passage_cic_fat_41: Cicero, De Fato 41]."
)
DIALECTICAL_PROSE = (
    "The liveliest dispute is whether they had the concept at all. "
    + DIALECTICAL_SENTENCE
    + " What remains genuinely open is the dating of the concept."
)


# ----------------------------------------------------------- withhold_sentences


def test_nothing_withheld_returns_text_unchanged() -> None:
    outcome = withhold_sentences(LEGACY_PROSE)
    assert outcome.text == LEGACY_PROSE
    assert outcome.withheld_sentences == 0
    assert outcome.published_sentences == 3


def test_legacy_ref_marker_withholds_only_its_sentence() -> None:
    outcome = withhold_sentences(LEGACY_PROSE, refs={"2"}, ids={"node-2"})
    assert outcome.text == (
        f"Justin quotes the fate passage [P1]. {MARK} A well sourced claim [3]."
    )
    assert outcome.withheld_sentences == 1
    assert outcome.published_sentences == 2


def test_ref_list_block_matches_each_token() -> None:
    text = "Shared claim [P1, 2]. Other claim [3]."
    outcome = withhold_sentences(text, refs={"2"})
    assert outcome.text == f"{MARK} Other claim [3]."


def test_digits_inside_dialectical_marker_do_not_match_a_numeric_ref() -> None:
    text = "A claim at [passage_cic_fat_41: Cicero, De Fato 41]. Another [P1]."
    outcome = withhold_sentences(text, refs={"41"})
    assert outcome.text == text
    assert outcome.withheld_sentences == 0


def test_dialectical_marker_withholds_by_citation_id() -> None:
    outcome = withhold_sentences(DIALECTICAL_PROSE, ids={"cic_fat_41"})
    assert DIALECTICAL_SENTENCE not in outcome.text
    assert outcome.text.startswith(
        "The liveliest dispute is whether they had the concept at all. "
    )
    assert outcome.text.endswith(
        f"{MARK} What remains genuinely open is the dating of the concept."
    )
    assert outcome.withheld_sentences == 1
    assert outcome.text.count(MARK) == 1


def test_position_marker_withholds_by_position_id() -> None:
    outcome = withhold_sentences(DIALECTICAL_PROSE, ids={"frede_epictetus"})
    assert "[P_frede_epictetus" not in outcome.text
    assert "The liveliest dispute" in outcome.text
    assert "What remains genuinely open" in outcome.text


def test_withheld_ledger_claim_removes_its_sentence() -> None:
    outcome = withhold_sentences(DIALECTICAL_PROSE, claims=[DIALECTICAL_SENTENCE])
    assert DIALECTICAL_SENTENCE not in outcome.text
    assert "[P_bobzien_no_problem" not in outcome.text
    assert "What remains genuinely open" in outcome.text


def test_blockquote_block_stands_or_falls_as_a_whole() -> None:
    text = (
        "Intro sentence [P2].\n\n"
        "> ἀρχὴ τοῦ λόγου [P1]\n"
        "> The beginning of the argument.\n\n"
        "Closing sentence [P2]."
    )
    outcome = withhold_sentences(text, refs={"P1"})
    assert outcome.text == (f"Intro sentence [P2].\n\n{MARK}\n\nClosing sentence [P2].")
    assert outcome.withheld_sentences == 1
    assert outcome.published_sentences == 2


def test_list_bullets_and_headings_keep_their_prefix() -> None:
    text = "## Evidence\n- First point [P1]. Second point [P2].\n1. Numbered [P1]."
    outcome = withhold_sentences(text, refs={"P1"})
    assert outcome.text == f"## Evidence\n- {MARK} Second point [P2].\n1. {MARK}"


def test_unwithheld_text_is_preserved_byte_for_byte() -> None:
    text = "Alpha [P1].  Two spaces then Beta [P2].\n\n\nGamma (p. 3). Delta [P3]."
    outcome = withhold_sentences(text, refs={"P2"})
    assert outcome.text == f"Alpha [P1].  {MARK}\n\n\nGamma (p. 3). Delta [P3]."


# ----------------------------------------------------------- fixtures


def _audit(
    *,
    verified: list[str],
    failed: list[tuple[str, str, bool]],
    total_citations: int,
    unaudited: int = 0,
) -> dict:
    audited = len(verified) + len(failed)
    parse_errors = sum(1 for _, _, pe in failed if pe)
    counts = {"WEAK": 0, "REJECTED": 0, "MISSING": 0}
    for _, status, _ in failed:
        counts[status] += 1
    return {
        "status": "passed" if not failed and not unaudited else "failed",
        "total": audited,
        "sampled": audited,
        "audited_citations": audited,
        "total_citations": total_citations,
        "verified": len(verified),
        "weak": counts["WEAK"],
        "rejected": counts["REJECTED"],
        "missing": counts["MISSING"],
        "parse_errors": parse_errors,
        "aborted": False,
        "verified_citations": verified,
        "failed_citations": [
            {
                "citation_id": cid,
                "status": status,
                "claim": "claim",
                "reasoning": "reasoning",
                "parse_error": pe,
            }
            for cid, status, pe in failed
        ],
    }


def _metadata(audit: dict) -> dict:
    return {
        "scholar_synthesis": {"status": "ok", "degraded": False},
        "content_gate": {"status": "passed", "passed": True},
        "citation_verifier_v2": audit,
    }


def _legacy_answer(audit: dict) -> ScholarlyAnswer:
    return ScholarlyAnswer(
        answer=LEGACY_PROSE,
        question="q",
        quality_badge="Low",
        passages_used=3,
        citations=[
            Citation(
                ref="P1", type="passage", id="p1", label="Apol. 43", verified=True
            ),
            Citation(
                ref="2", type="node", id="node-2", label="Chrysippus", verified=True
            ),
            Citation(ref="3", type="node", id="node-3", label="Justin", verified=True),
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
            ClaimLedgerItem(
                claim="A well sourced claim.",
                evidence_ids=["node-3"],
                status=ClaimStatus.SUPPORTED,
            ),
        ],
        metadata=_metadata(audit),
    )


def _one_weak_audit() -> dict:
    return _audit(
        verified=["p1", "node-3"],
        failed=[("node-2", "WEAK", False)],
        total_citations=3,
    )


# ----------------------------------------------------------- model form


def test_partial_withholding_publishes_verified_sentences() -> None:
    public = annotate_publication_decision(
        _legacy_answer(_one_weak_audit()), withhold_prose=True
    )

    assert public.answer == (
        f"Justin quotes the fate passage [P1]. {MARK} A well sourced claim [3]."
    )
    assert [c.id for c in public.citations] == ["p1", "node-3"]
    assert public.quality_badge == "Partial"
    assert public.insufficient_evidence is False
    assert public.passages_used == 3

    ledger = {item.claim: item for item in public.claim_ledger}
    assert ledger["A weakly sourced claim."].status is ClaimStatus.INSUFFICIENT
    assert ledger["A weakly sourced claim."].status_reason == "withheld: weak"
    assert ledger["Justin quotes the fate passage."].status is ClaimStatus.SUPPORTED
    assert ledger["Justin quotes the fate passage."].status_reason is None

    gate = public.metadata["publication_gate"]
    assert gate["status"] == "partial"
    assert gate["publishable"] is True
    assert gate["applied"] is True
    assert gate["withholding"] == {
        "withheld_sentences": 1,
        "published_sentences": 2,
        "withheld_citations": [{"citation_id": "node-2", "ref": "2", "reason": "weak"}],
        "reasons": {"weak": 1},
        "audit_warning": None,
    }


def test_clean_audit_publishes_everything_as_high() -> None:
    audit = _audit(verified=["p1", "node-2", "node-3"], failed=[], total_citations=3)
    public = annotate_publication_decision(_legacy_answer(audit), withhold_prose=True)

    assert public.answer == LEGACY_PROSE
    assert public.quality_badge == "High"
    assert len(public.citations) == 3
    assert all(i.status is ClaimStatus.SUPPORTED for i in public.claim_ledger)
    gate = public.metadata["publication_gate"]
    assert gate["status"] == "passed"
    assert gate["withholding"]["withheld_sentences"] == 0
    assert gate["withholding"]["published_sentences"] == 3


def test_verifier_error_on_one_citation_withholds_that_sentence_only() -> None:
    audit = _audit(
        verified=["p1", "node-3"],
        failed=[("node-2", "WEAK", True)],
        total_citations=3,
    )
    public = annotate_publication_decision(_legacy_answer(audit), withhold_prose=True)

    assert public.answer.count(MARK) == 1
    assert "A well sourced claim [3]." in public.answer
    assert public.metadata["publication_gate"]["withholding"]["reasons"] == {
        "verifier_error": 1
    }


def test_unaudited_citation_is_withheld_under_a_partial_audit() -> None:
    audit = _audit(verified=["p1", "node-3"], failed=[], total_citations=3, unaudited=1)
    public = annotate_publication_decision(_legacy_answer(audit), withhold_prose=True)

    assert public.metadata["publication_gate"]["publishable"] is True
    assert "A weakly sourced claim [2]." not in public.answer
    assert public.metadata["publication_gate"]["withholding"]["reasons"] == {
        "unaudited": 1
    }


def test_all_sentences_withheld_blocks() -> None:
    audit = _audit(
        verified=[],
        failed=[
            ("p1", "REJECTED", False),
            ("node-2", "REJECTED", False),
            ("node-3", "MISSING", False),
        ],
        total_citations=3,
    )
    public = annotate_publication_decision(_legacy_answer(audit), withhold_prose=True)

    assert public.answer == ""
    assert public.citations == []
    assert public.claim_ledger == []
    assert public.quality_badge == "Blocked"
    assert "all_sentences_withheld" in public.metadata["publication_gate"]["reasons"]


def test_infrastructure_failure_blocks_even_with_prose() -> None:
    audit = {
        "status": "error",
        "reason": "RuntimeError: provider down",
        "total_citations": 3,
        "audited_citations": 0,
        "total": 0,
        "verified": 0,
        "weak": 0,
        "rejected": 0,
        "missing": 0,
        "parse_errors": 0,
        "aborted": True,
        "infrastructure_failure": True,
    }
    public = annotate_publication_decision(_legacy_answer(audit), withhold_prose=True)

    assert public.answer == ""
    assert public.quality_badge == "Blocked"
    reasons = public.metadata["publication_gate"]["reasons"]
    assert "citation_audit_infrastructure_failure" in reasons


def test_internal_draft_keeps_prose_but_records_the_verdict() -> None:
    internal = annotate_publication_decision(
        _legacy_answer(_one_weak_audit()), withhold_prose=False
    )
    assert internal.answer == LEGACY_PROSE
    assert len(internal.citations) == 3
    gate = internal.metadata["publication_gate"]
    assert gate["status"] == "partial"
    assert gate["applied"] is False
    assert gate["withholding"]["withheld_citations"][0]["citation_id"] == "node-2"


def test_applying_twice_is_a_no_op() -> None:
    once = annotate_publication_decision(
        _legacy_answer(_one_weak_audit()), withhold_prose=True
    )
    twice = annotate_publication_decision(once, withhold_prose=True)
    assert twice == once


# ----------------------------------------------------------- mapping form


def _as_mapping(answer: ScholarlyAnswer) -> dict:
    return {
        "answer": answer.answer,
        "question": answer.question,
        "citations": [c.model_dump() for c in answer.citations],
        "claim_ledger": [c.model_dump() for c in answer.claim_ledger],
        "passages_used": answer.passages_used,
        "insufficient_evidence": answer.insufficient_evidence,
        "metadata": {**answer.metadata, "quality_badge": answer.quality_badge},
    }


def test_mapping_form_makes_the_same_decision_as_the_model_form() -> None:
    draft = _legacy_answer(_one_weak_audit())

    from_model = annotate_publication_decision(draft, withhold_prose=True)
    from_mapping = apply_publication_verdict(_as_mapping(draft))

    assert from_mapping["answer"] == from_model.answer
    assert [c["id"] for c in from_mapping["citations"]] == [
        c.id for c in from_model.citations
    ]
    assert [
        (c["claim"], c["status"], c.get("status_reason"))
        for c in from_mapping["claim_ledger"]
    ] == [(c.claim, c.status.value, c.status_reason) for c in from_model.claim_ledger]
    assert from_mapping["metadata"]["quality_badge"] == from_model.quality_badge
    assert (
        from_mapping["metadata"]["publication_gate"]
        == from_model.metadata["publication_gate"]
    )
    assert from_mapping["insufficient_evidence"] is False


def test_mapping_form_blocks_the_same_drafts_as_the_model_form() -> None:
    audit = _audit(
        verified=[],
        failed=[("p1", "REJECTED", False)],
        total_citations=3,
        unaudited=2,
    )
    draft = _legacy_answer(audit)
    from_model = annotate_publication_decision(draft, withhold_prose=True)
    from_mapping = apply_publication_verdict(_as_mapping(draft))

    assert from_model.answer == "" and from_mapping["answer"] == ""
    assert from_mapping["citations"] == [] and from_mapping["claim_ledger"] == []
    assert from_mapping["metadata"]["quality_badge"] == "Blocked"
    assert (
        from_mapping["metadata"]["publication_gate"]["reasons"]
        == from_model.metadata["publication_gate"]["reasons"]
    )


def test_mapping_form_is_idempotent() -> None:
    once = apply_publication_verdict(_as_mapping(_legacy_answer(_one_weak_audit())))
    twice = apply_publication_verdict(once)
    assert twice == once


# ------------------------------------------- surviving-evidence invariants


def test_citation_orphaned_by_a_mixed_sentence_leaves_the_public_list() -> None:
    """One sentence cites a verified and a weak citation.  Withholding the
    sentence removes the verified citation's only use: it is dropped as
    orphaned and its ledger claim is downgraded, instead of standing in the
    public list with no surviving claim."""
    draft = _legacy_answer(_one_weak_audit()).model_copy(
        update={
            "answer": (
                "Justin quotes the fate passage [P1]. A well sourced claim [2, 3]."
            )
        }
    )
    public = annotate_publication_decision(draft, withhold_prose=True)

    assert public.answer == f"Justin quotes the fate passage [P1]. {MARK}"
    assert [c.id for c in public.citations] == ["p1"]
    ledger = {item.claim: item for item in public.claim_ledger}
    assert ledger["A well sourced claim."].status is ClaimStatus.INSUFFICIENT
    assert ledger["A well sourced claim."].status_reason == "withheld: orphaned"
    assert ledger["Justin quotes the fate passage."].status is ClaimStatus.SUPPORTED
    withholding = public.metadata["publication_gate"]["withholding"]
    assert withholding["reasons"] == {"orphaned": 1, "weak": 1}
    assert {
        c["citation_id"]: c["reason"] for c in withholding["withheld_citations"]
    } == {
        "node-2": "weak",
        "node-3": "orphaned",
    }
    assert public.quality_badge == "Partial"


def test_ledger_only_citation_survives_on_its_supported_claim() -> None:
    """A citation with no inline marker (dialectical position) stays public
    while a supported ledger claim still cites it."""
    audit = _audit(
        verified=["p1", "node-3"],
        failed=[("node-2", "WEAK", False)],
        total_citations=3,
    )
    draft = _legacy_answer(audit).model_copy(
        update={
            "answer": "Justin quotes the fate passage [P1]. A weakly sourced claim [2].",
        }
    )
    public = annotate_publication_decision(draft, withhold_prose=True)
    assert [c.id for c in public.citations] == ["p1", "node-3"]
    assert public.metadata["publication_gate"]["withholding"]["reasons"] == {"weak": 1}


def test_uncited_remnants_alone_do_not_publish() -> None:
    """Headings and framing sentences survive the surgery, but the answer's
    only citation was rejected: nothing citable is left, so the answer is
    blocked rather than published as uncited prose."""
    audit = _audit(verified=[], failed=[("p1", "REJECTED", False)], total_citations=1)
    draft = ScholarlyAnswer(
        answer=(
            "## Fate in Justin\n\nThe question is old. Justin quotes the fate "
            "passage [P1]. Much remains open."
        ),
        question="q",
        citations=[Citation(ref="P1", type="passage", id="p1", label="Apol. 43")],
        claim_ledger=[
            ClaimLedgerItem(
                claim="Justin quotes the fate passage.",
                evidence_ids=["p1"],
                status=ClaimStatus.SUPPORTED,
            )
        ],
        metadata=_metadata(audit),
    )
    public = annotate_publication_decision(draft, withhold_prose=True)

    assert public.answer == ""
    assert public.citations == []
    assert public.quality_badge == "Blocked"
    gate = public.metadata["publication_gate"]
    assert gate["publishable"] is False
    assert "no_cited_claims_survive" in gate["reasons"]

    mapping = apply_publication_verdict(_as_mapping(draft))
    assert mapping["answer"] == ""
    assert (
        "no_cited_claims_survive" in mapping["metadata"]["publication_gate"]["reasons"]
    )


def test_publishable_verdict_preserves_insufficient_evidence() -> None:
    """Citation verification does not establish evidence sufficiency: the
    pipeline's own flag survives a publishable verdict."""
    audit = _audit(verified=["p1", "node-2", "node-3"], failed=[], total_citations=3)
    draft = _legacy_answer(audit).model_copy(update={"insufficient_evidence": True})
    public = annotate_publication_decision(draft, withhold_prose=True)
    assert public.insufficient_evidence is True
    assert (
        apply_publication_verdict(_as_mapping(draft))["insufficient_evidence"] is True
    )


def test_degraded_synthesis_is_published_flagged_and_keeps_its_grade() -> None:
    audit = _audit(verified=["p1", "node-2", "node-3"], failed=[], total_citations=3)
    draft = _legacy_answer(audit)
    draft.metadata["scholar_synthesis"] = {"status": "degraded", "degraded": True}
    public = annotate_publication_decision(draft, withhold_prose=True)

    assert public.answer == LEGACY_PROSE
    assert public.quality_badge == "Low"  # the pipeline's grade, not "High"
    gate = public.metadata["publication_gate"]
    assert gate["status"] == "passed"
    assert gate["warnings"] == ["scholar_synthesis_degraded"]
    assert is_publishable(public.metadata) is True
    assert is_cacheable(public.metadata) is False


# ----------------------------------------------- prose rewritten after gate


def test_prose_rewritten_after_the_gate_is_withheld_again() -> None:
    """An applied record is authoritative for the verdict, not for the prose:
    a stage that rewrites the answer afterwards (resynthesis) gets the
    rewrite withheld from the recorded verdict."""
    once = apply_publication_verdict(_as_mapping(_legacy_answer(_one_weak_audit())))
    rewritten = {
        **once,
        "answer": (
            "Justin quotes the fate passage [P1]. A weakly sourced claim, "
            "restated after the gate [2]. A well sourced claim [3]."
        ),
    }
    again = apply_publication_verdict(rewritten)

    assert again["answer"] == (
        f"Justin quotes the fate passage [P1]. {MARK} A well sourced claim [3]."
    )
    assert [c["id"] for c in again["citations"]] == ["p1", "node-3"]
    gate = again["metadata"]["publication_gate"]
    assert gate["status"] == "partial"
    assert gate["withholding"]["withheld_sentences"] == 1
    # The withheld citation left the public list at the first application;
    # the re-check still records it (with its ref) for the next re-check.
    assert gate["withholding"]["withheld_citations"] == [
        {"citation_id": "node-2", "ref": "2", "reason": "weak"}
    ]
    # The rewrite collapsed back onto the same published text, so the record
    # is unchanged and a further application is a no-op.
    assert (
        gate["answer_digest"] == once["metadata"]["publication_gate"]["answer_digest"]
    )
    assert apply_publication_verdict(again) == again


def test_polished_markdown_added_after_the_gate_is_withheld() -> None:
    once = apply_publication_verdict(_as_mapping(_legacy_answer(_one_weak_audit())))
    polished = {**once, "polished_markdown": f"# Polished\n\n{LEGACY_PROSE}"}
    again = apply_publication_verdict(polished)

    assert again["answer"] == once["answer"]
    assert "A weakly sourced claim [2]." not in again["polished_markdown"]
    assert again["polished_markdown"] == (
        f"# Polished\n\nJustin quotes the fate passage [P1]. {MARK} "
        "A well sourced claim [3]."
    )
    assert again["metadata"]["publication_gate"] == once["metadata"]["publication_gate"]


def test_blocked_record_stays_blocked_when_prose_is_reinstated() -> None:
    audit = _audit(
        verified=[],
        failed=[("p1", "REJECTED", False)],
        total_citations=3,
        unaudited=2,
    )
    blocked = apply_publication_verdict(_as_mapping(_legacy_answer(audit)))
    reinstated = {
        **blocked,
        "answer": LEGACY_PROSE,
        "polished_markdown": LEGACY_PROSE,
        "citations": _as_mapping(_legacy_answer(audit))["citations"],
    }
    again = apply_publication_verdict(reinstated)
    assert again["answer"] == ""
    assert again["polished_markdown"] == ""
    assert again["citations"] == []
    assert again["metadata"]["quality_badge"] == "Blocked"
