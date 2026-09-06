"""The v2 verifier audits (sentence, citation) PAIRS, and judges substance.

Two production defects of the citation judge, replayed with stubs:

* Verdicts were per citation id while withholding was per sentence: one
  WEAK use of a scholar node cited in many sentences took every sentence
  citing it down. Now every pair is enumerated and keyed, the record carries
  the pair, and the publication gate withholds only the sentence of a
  failing pair while the citation stays public on its verified uses.
* Literalism: the judge marked WEAK when the record supported the substance
  of the proposition but not every element of the writer's paraphrase. The
  prompts now carry an explicit standard of support with paired examples;
  the assertions are on what the judge is shown.
"""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import AsyncMock

import pytest

from eleutheria_graphrag.agents.publication_gate import (
    WITHHELD_SENTENCE_MARKER,
    annotate_publication_decision,
    apply_publication_verdict,
    evaluate_publication,
    is_cacheable,
)
from eleutheria_graphrag.agents.scholarly_agent import (
    ScholarlyAgent,
    _draft_claim_for,
    _enumerate_audit_pairs,
    _order_audit_pairs,
    _sample_citations_for_verification,
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
    SynthesizedDraft,
    VerificationReport,
)
from eleutheria_graphrag.services.citation_verifier_v2 import (
    NODE_VERIFY_PROMPT,
    SUPPORT_STANDARD_INSTRUCTION,
    VERIFY_PROMPT,
    CitationVerifierV2,
)
from tests.unit.conftest import make_deps
from tests.unit.test_programmatic_verify_quotes import BUNDLE_GREEK

MARK = WITHHELD_SENTENCE_MARKER

# --------------------------------------------------------------------- fixtures

FREDE_ID = "scholarly_argument_frede_2011"
FREDE_TEXT = (
    "Frede argues that the notion of a free will was invented by Epictetus, "
    "for whom what is up to us is the use of impressions, above all assent."
)
S0 = "Frede locates the invention of a free will in Epictetus [N1]."
S1 = "Frede reads the partition of impressions and assent as Epictetan [N1]."
S2 = "Frede also holds that Alexander borrowed the partition [N1]."
S3 = "Frede dates the move to the early second century [N1]."
FOUR_SENTENCES = " ".join((S0, S1, S2, S3))


def _frede(confidence: float | None = None) -> Citation:
    return Citation(
        ref="N1",
        type="node",
        id=FREDE_ID,
        label="Frede 2011",
        confidence=confidence,
        verified=True,
    )


def _citation(
    ref: str, cid: str, label: str, confidence: float | None = None
) -> Citation:
    return Citation(
        ref=ref, type="node", id=cid, label=label, confidence=confidence, verified=True
    )


def _metadata(audit: dict[str, Any]) -> dict[str, Any]:
    return {
        "scholar_synthesis": {"status": "ok", "degraded": False},
        "content_gate": {"status": "passed", "passed": True},
        "citation_verifier_v2": audit,
    }


def _pair(index: int, sentence: str, status: str, parse_error: bool = False) -> dict:
    return {
        "sentence_index": index,
        "sentence": sentence,
        "clause": sentence,
        "status": status,
        "reasoning": "stub",
        "parse_error": parse_error,
        "evidence_kind": "node",
    }


def _audit(
    *,
    verified: list[str],
    failed: list[dict[str, Any]],
    total_citations: int,
    unaudited_pairs: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """A pair-level audit record in the runner's shape (id-level counts on
    top, pairs beneath)."""
    audited_ids = len(verified) + len(failed)
    counts = {"WEAK": 0, "REJECTED": 0, "MISSING": 0}
    for entry in failed:
        counts[entry["status"]] += 1
    return {
        "status": "failed" if failed or unaudited_pairs else "passed",
        "total": audited_ids,
        "sampled": audited_ids,
        "audited_citations": audited_ids,
        "total_citations": total_citations,
        "verified": len(verified),
        "weak": counts["WEAK"],
        "rejected": counts["REJECTED"],
        "missing": counts["MISSING"],
        "parse_errors": sum(1 for e in failed if e.get("parse_error")),
        "aborted": False,
        "verified_citations": verified,
        "failed_citations": failed,
        "unaudited_pairs": list(unaudited_pairs or []),
    }


def _failed(cid: str, verified_pairs: int, *pairs: dict[str, Any]) -> dict[str, Any]:
    harshest = max(
        pairs, key=lambda p: ("WEAK", "MISSING", "REJECTED").index(p["status"])
    )
    return {
        "citation_id": cid,
        "status": harshest["status"],
        "claim": harshest["clause"],
        "reasoning": harshest["reasoning"],
        "parse_error": bool(harshest["parse_error"]),
        "evidence_kind": "node",
        "verified_pairs": verified_pairs,
        "pairs": list(pairs),
    }


def _answer(text: str, *citations: Citation, **kwargs: Any) -> ScholarlyAnswer:
    return ScholarlyAnswer(
        answer=text, question="q", citations=list(citations), **kwargs
    )


def _report(checks: list[CitationCheck]) -> VerificationReport:
    return VerificationReport.from_checks(checks)


def _agent_with(report: VerificationReport) -> ScholarlyAgent:
    deps = make_deps()
    verifier = AsyncMock()
    verifier.verify_draft = AsyncMock(return_value=report)
    deps.verifier_v2 = verifier
    return ScholarlyAgent(deps)


def _check(
    cid: str, index: int | None, status: CitationStatus, **extra: Any
) -> CitationCheck:
    return CitationCheck(
        citation_id=cid,
        status=status,
        reasoning=extra.pop("reasoning", "stub"),
        sentence_index=index,
        evidence_kind="node",
        **extra,
    )


# ------------------------------------------------------- enumeration and keys


def test_every_sentence_citing_an_id_is_its_own_pair() -> None:
    text = FOUR_SENTENCES.replace(S1, S1[:-1] + " [N2].")
    other = _citation("N2", "scholarly_argument_bobzien", "Bobzien 1998")
    ledger_only = _citation("N3", "scholarly_argument_long", "Long 2002")
    answer = _answer(
        text,
        _frede(),
        other,
        ledger_only,
        claim_ledger=[
            ClaimLedgerItem(
                claim="Long endorses the reading.",
                evidence_ids=[ledger_only.id],
                status=ClaimStatus.SUPPORTED,
            )
        ],
    )

    pairs = _enumerate_audit_pairs(answer)

    keys = [(pair.citation.id, pair.sentence_index) for pair in pairs]
    assert keys == [
        (FREDE_ID, 0),
        (FREDE_ID, 1),
        (other.id, 1),
        (FREDE_ID, 2),
        (FREDE_ID, 3),
        (ledger_only.id, None),
    ]
    assert pairs[0].claim == S0
    assert pairs[1].clause == S1[:-6]
    # The uncited citation audits its ledger sentence as a whole.
    assert pairs[-1].claim == "Long endorses the reading."


def test_draft_claim_and_verdict_carry_the_pair_key() -> None:
    answer = _answer(FOUR_SENTENCES, _frede())

    claim = _draft_claim_for(answer, _frede(), S2, sentence_index=2)
    check = CitationCheck(
        citation_id=FREDE_ID, status=CitationStatus.WEAK, sentence_index=2
    )

    assert claim.pair_key == (FREDE_ID, 2)
    assert claim.sentence == S2
    assert claim.claim == "Frede also holds that Alexander borrowed the partition"
    assert check.pair_key == claim.pair_key


# ------------------------------------------------------------ sampler and cap


def test_sampler_orders_greek_then_one_look_per_id_then_the_rest() -> None:
    text = (
        f"A first use [N1]. Justin quotes {BUNDLE_GREEK} [N2]. "
        "A second use [N1]. A second Justin use [N2]."
    )
    low = _citation("N1", "n_low", "Low", confidence=0.3)
    high = _citation("N2", "n_high", "High", confidence=0.9)
    answer = _answer(text, low, high)

    ordered = _order_audit_pairs(_enumerate_audit_pairs(answer))

    assert [(p.citation.id, p.sentence_index) for p in ordered] == [
        ("n_high", 1),  # Greek-bearing proposition first, whatever its confidence
        ("n_low", 0),  # one look per remaining id
        ("n_low", 2),  # then the rest, ascending confidence
        ("n_high", 3),
    ]
    sampled = _sample_citations_for_verification(answer, max_claims=2)
    assert [(p.citation.id, p.sentence_index) for p in sampled] == [
        ("n_high", 1),
        ("n_low", 0),
    ]


@pytest.mark.asyncio
async def test_runner_records_pair_verdicts_and_cap_accounting(monkeypatch) -> None:
    monkeypatch.setenv("ELEUTHERIA_VERIFIER_V2_MAX_CLAIMS", "3")
    report = _report(
        [
            _check(FREDE_ID, 0, CitationStatus.VERIFIED),
            _check(FREDE_ID, 1, CitationStatus.VERIFIED),
            _check(
                FREDE_ID,
                2,
                CitationStatus.WEAK,
                reasoning="Alexander is not in the record",
                claim="Frede also holds that Alexander borrowed the partition",
            ),
        ]
    )
    agent = _agent_with(report)
    answer = _answer(
        FOUR_SENTENCES,
        _frede(),
        self_rag_evaluation=SelfRAGEvaluation(
            relevance=80, grounding=100, completeness=80, confidence=80
        ),
    )

    updated, _ = await agent._run_citation_verifier_v2(answer)

    draft = agent.deps.verifier_v2.verify_draft.call_args.args[0]
    assert [claim.pair_key for claim in draft.claims] == [
        (FREDE_ID, 0),
        (FREDE_ID, 1),
        (FREDE_ID, 2),
    ]
    meta = updated.metadata["citation_verifier_v2"]
    assert meta["status"] == "failed"
    assert meta["pairs"] == {
        "total": 4,
        "audited": 3,
        "verified": 2,
        "weak": 1,
        "rejected": 0,
        "missing": 0,
        "unaudited": 1,
    }
    assert meta["unaudited_pairs"] == [
        {
            "citation_id": FREDE_ID,
            "sentence_index": 3,
            "sentence": S3,
            "clause": "Frede dates the move to the early second century",
        }
    ]
    # Backward-compatible id-level record: the id is not all-verified, its
    # failing pair is listed with sentence index and clause.
    assert meta["verified_citations"] == []
    assert meta["total"] == meta["audited_citations"] == 1
    assert meta["weak"] == 1 and meta["verified"] == 0
    [entry] = meta["failed_citations"]
    assert entry["citation_id"] == FREDE_ID
    assert entry["status"] == "WEAK"
    assert entry["verified_pairs"] == 2
    assert entry["pairs"] == [
        {
            "sentence_index": 2,
            "sentence": S2,
            "clause": "Frede also holds that Alexander borrowed the partition",
            "status": "WEAK",
            "reasoning": "Alexander is not in the record",
            "parse_error": False,
            "evidence_kind": "node",
        }
    ]
    [citation] = updated.citations
    assert citation.verified is False
    assert citation.verification_note == "[WEAK] Alexander is not in the record"
    assert updated.metadata["grounding"]["coverage"] == "partial: 1/1 audited"
    assert updated.metadata["grounding"]["score"] == 67


# ------------------------------------------------------------- the gate


def _four_sentence_answer(audit: dict[str, Any]) -> ScholarlyAnswer:
    return ScholarlyAnswer(
        answer=FOUR_SENTENCES,
        question="q",
        quality_badge="Low",
        passages_used=1,
        citations=[_frede()],
        claim_ledger=[
            ClaimLedgerItem(
                claim=S2, evidence_ids=[FREDE_ID], status=ClaimStatus.SUPPORTED
            ),
            ClaimLedgerItem(
                claim=S0, evidence_ids=[FREDE_ID], status=ClaimStatus.SUPPORTED
            ),
        ],
        metadata=_metadata(audit),
    )


def test_one_weak_pair_withholds_its_sentence_and_keeps_the_citation() -> None:
    audit = _audit(
        verified=[],
        failed=[_failed(FREDE_ID, 3, _pair(2, S2, "WEAK"))],
        total_citations=1,
    )
    public = annotate_publication_decision(
        _four_sentence_answer(audit), withhold_prose=True
    )

    assert public.answer == f"{S0} {S1} {MARK} {S3}"
    assert [c.id for c in public.citations] == [FREDE_ID]
    assert public.quality_badge == "Partial"
    gate = public.metadata["publication_gate"]
    assert gate["status"] == "partial"
    assert gate["publishable"] is True
    assert gate["withholding"]["withheld_sentences"] == 1
    assert gate["withholding"]["published_sentences"] == 3
    assert gate["withholding"]["withheld_citations"] == []
    assert gate["withholding"]["reasons"] == {}
    assert gate["withholding"]["withheld_pairs"] == [
        {
            "citation_id": FREDE_ID,
            "ref": "N1",
            "sentence_index": 2,
            "reason": "weak",
        }
    ]
    assert gate["withholding"]["pair_reasons"] == {"weak": 1}
    ledger = {item.claim: item for item in public.claim_ledger}
    assert ledger[S2].status is ClaimStatus.INSUFFICIENT
    assert ledger[S2].status_reason == "withheld: sentence_withheld"
    assert ledger[S0].status is ClaimStatus.SUPPORTED
    assert is_cacheable(public.metadata) is False


def test_an_id_without_a_verified_pair_is_withheld_as_a_whole() -> None:
    audit = _audit(
        verified=[],
        failed=[_failed(FREDE_ID, 0, _pair(2, S2, "WEAK"), _pair(0, S0, "REJECTED"))],
        total_citations=1,
    )
    decision = evaluate_publication(_metadata(audit))

    assert decision.withheld == {FREDE_ID: "rejected"}
    assert decision.withheld_pairs == ()


def test_legacy_record_without_pairs_withholds_by_id() -> None:
    legacy = {
        "citation_id": FREDE_ID,
        "status": "WEAK",
        "claim": S2,
        "reasoning": "stub",
        "parse_error": False,
    }
    audit = _audit(verified=[], failed=[legacy], total_citations=1)
    public = annotate_publication_decision(
        _four_sentence_answer(audit), withhold_prose=True
    )

    assert public.quality_badge == "Blocked"
    assert "all_sentences_withheld" in public.metadata["publication_gate"]["reasons"]


def test_unaudited_pairs_left_by_the_cap_are_withheld_and_counted() -> None:
    audit = _audit(
        verified=[FREDE_ID],
        failed=[],
        total_citations=1,
        unaudited_pairs=[
            {"citation_id": FREDE_ID, "sentence_index": 3, "sentence": S3, "clause": S3}
        ],
    )
    audit["pairs"] = {
        "total": 4,
        "audited": 3,
        "verified": 3,
        "weak": 0,
        "rejected": 0,
        "missing": 0,
        "unaudited": 1,
    }
    public = annotate_publication_decision(
        _four_sentence_answer(audit), withhold_prose=True
    )

    assert public.answer == f"{S0} {S1} {S2} {MARK}"
    assert [c.id for c in public.citations] == [FREDE_ID]
    withholding = public.metadata["publication_gate"]["withholding"]
    assert withholding["withheld_pairs"] == [
        {
            "citation_id": FREDE_ID,
            "ref": "N1",
            "sentence_index": 3,
            "reason": "unaudited",
        }
    ]
    assert withholding["pair_reasons"] == {"unaudited": 1}
    assert public.metadata["citation_verifier_v2"]["pairs"]["unaudited"] == 1


def test_an_id_with_no_audited_pair_is_still_withheld_as_unaudited() -> None:
    other = _citation("N2", "scholarly_argument_bobzien", "Bobzien 1998")
    text = f"{S0} Bobzien disagrees [N2]."
    audit = _audit(verified=[FREDE_ID], failed=[], total_citations=2)
    answer = ScholarlyAnswer(
        answer=text,
        question="q",
        citations=[_frede(), other],
        metadata=_metadata(audit),
    )
    public = annotate_publication_decision(answer, withhold_prose=True)

    assert public.answer == f"{S0} {MARK}"
    assert [c.id for c in public.citations] == [FREDE_ID]
    assert public.metadata["publication_gate"]["withholding"]["reasons"] == {
        "unaudited": 1
    }


def test_orphan_rule_drops_a_citation_whose_only_sentence_was_withheld() -> None:
    long_ = _citation("N2", "scholarly_argument_long", "Long 2002")
    text = f"Long endorses Frede's reading [N2] [N1]. {S1}"
    audit = _audit(
        verified=[long_.id],
        failed=[
            _failed(
                FREDE_ID,
                1,
                _pair(0, "Long endorses Frede's reading [N2] [N1].", "WEAK"),
            )
        ],
        total_citations=2,
    )
    result = apply_publication_verdict(
        {
            "answer": text,
            "citations": [_frede().model_dump(), long_.model_dump()],
            "claim_ledger": [],
            "metadata": _metadata(audit),
        }
    )

    assert result["answer"] == f"{MARK} {S1}"
    # Frede survives on its verified use; Long's only sentence went with the
    # failing pair, so Long is orphaned and leaves the public list.
    assert [c["id"] for c in result["citations"]] == [FREDE_ID]
    withholding = result["metadata"]["publication_gate"]["withholding"]
    assert withholding["withheld_citations"] == [
        {"citation_id": long_.id, "ref": "N2", "reason": "orphaned"}
    ]
    assert withholding["withheld_pairs"] == [
        {"citation_id": FREDE_ID, "ref": "N1", "sentence_index": 0, "reason": "weak"}
    ]


def test_a_rewrite_after_the_gate_folds_the_pair_onto_its_id() -> None:
    audit = _audit(
        verified=[],
        failed=[_failed(FREDE_ID, 3, _pair(2, S2, "WEAK"))],
        total_citations=1,
    )
    first = apply_publication_verdict(
        {
            "answer": FOUR_SENTENCES,
            "citations": [_frede().model_dump()],
            "claim_ledger": [],
            "metadata": _metadata(audit),
        }
    )
    assert first["answer"].count(MARK) == 1
    # Replaying the unchanged result is a no-op.
    assert apply_publication_verdict(first) == first

    # Prose rewritten after the gate: the pair's sentence can no longer be
    # located, so the id is withheld as a whole (fail-closed).
    rewritten = {**first, "answer": "Frede says something new [N1]. And more [N1]."}
    again = apply_publication_verdict(rewritten)
    assert again["metadata"]["publication_gate"]["status"] == "blocked"
    assert "all_sentences_withheld" in again["metadata"]["publication_gate"]["reasons"]


# ------------------------------------------------------------ end to end


def _keyed_llm(verdicts: dict[str, str]) -> AsyncMock:
    """A judge stub that answers by the proposition it is shown."""

    def generate(prompt: str, **_: Any) -> str:
        head = prompt.split("Proposition being audited", 1)[1]
        proposition = head.split(":\n", 1)[1].split("\n", 1)[0]
        status = verdicts.get(proposition, "VERIFIED")
        return json.dumps(
            {
                "status": status,
                "reasoning": "stub",
                "evidence_quote": FREDE_TEXT[:40] if status != "VERIFIED" else "",
            }
        )

    llm = AsyncMock()
    llm.generate = AsyncMock(side_effect=generate)
    return llm


@pytest.mark.asyncio
async def test_end_to_end_one_weak_use_keeps_the_other_three_sentences(
    monkeypatch,
) -> None:
    monkeypatch.delenv("ELEUTHERIA_VERIFIER_V2_MAX_CLAIMS", raising=False)
    node = {
        "kind": "node",
        "text": FREDE_TEXT,
        "label": "Frede 2011",
        "node_type": "argument",
        "text_chars": len(FREDE_TEXT),
    }

    async def fetch(citation_id: str) -> dict[str, Any] | None:
        return dict(node) if citation_id == FREDE_ID else None

    llm = _keyed_llm({"Frede also holds that Alexander borrowed the partition": "WEAK"})
    agent = ScholarlyAgent(make_deps())
    agent.deps.verifier_v2 = CitationVerifierV2(
        llm=llm, passage_fetcher=fetch, tool_mode="off"
    )
    answer = ScholarlyAnswer(
        answer=FOUR_SENTENCES,
        question="q",
        citations=[_frede()],
        metadata={
            "scholar_synthesis": {"status": "ok", "degraded": False},
            "content_gate": {"status": "passed", "passed": True},
        },
    )

    audited, report = await agent._run_citation_verifier_v2(answer)
    public = annotate_publication_decision(audited, withhold_prose=True)

    assert report is not None
    assert sorted(check.pair_key for check in report.checks) == [
        (FREDE_ID, 0),
        (FREDE_ID, 1),
        (FREDE_ID, 2),
        (FREDE_ID, 3),
    ]
    assert audited.metadata["citation_verifier_v2"]["pairs"]["audited"] == 4
    assert public.answer == f"{S0} {S1} {MARK} {S3}"
    assert [c.id for c in public.citations] == [FREDE_ID]
    assert public.quality_badge == "Partial"


# ------------------------------------------------- the standard of support

PARAPHRASE_CASES = [
    (
        "Dihle's opposing genealogy denies that Greek theories of rational "
        "choice had isolated a distinct faculty of will, and places the "
        "decisive innovation much later in Christian reflection, especially "
        "Augustine",
        "Dihle argues that the notion of the will emerges principally with "
        "Augustine and the Christian tradition rather than in classical Greek "
        "thought.",
    ),
    (
        "Alexander defends indeterminist freedom, defining what depends on us "
        "through deliberation and control over acting and not acting",
        "Alexander held a same-circumstances power to act or choose otherwise.",
    ),
    (
        "Frede treats this external/internal partition as recognizably "
        "Epictetan: what depends on us is not the occurrence of impressions "
        "or external outcomes but the rational use made of impressions, above "
        "all through assent",
        "Frede: for Epictetus what is up to us is how we deal with "
        "impressions, especially assent.",
    ),
    (
        "Origen distinguishes foreknowledge from causation: divine cognition "
        "and providential ordering follow the foreseen value of the agent's "
        "own movement rather than producing it",
        "Origen: God's eternal knowledge has free human choices as its "
        "object, not as its effect.",
    ),
]

ADDED_RELATION_CASES = [
    (
        "Gibbons agrees with Frede that Origen's basic mechanism is Stoic",
        "Gibbons argues that Origen's account of assent to impressions is "
        "Stoic in its basic mechanism.",
        "Frede",
    ),
    (
        "The spider's weaving and the bee's wax-making illustrate the "
        "difference between natural activity and rational assent",
        "Gibbons argues that Origen's account of assent to impressions is "
        "Stoic in its basic mechanism.",
        "spider",
    ),
    (
        "Bobzien and Frede also differ methodologically because they ask "
        "different genealogical questions",
        "Bobzien asks when the problem of free will and determinism first "
        "arose in ancient philosophy.",
        "Frede",
    ),
]


async def _judge(
    proposition: str, record: str, *, verdict: str, kind: str = "node"
) -> tuple[CitationCheck, str]:
    evidence = (
        {
            "kind": "node",
            "text": record,
            "label": "record",
            "node_type": "argument",
            "text_chars": len(record),
        }
        if kind == "node"
        else {"text": record, "label": "passage"}
    )

    async def fetch(_: str) -> dict[str, Any]:
        return dict(evidence)

    llm = AsyncMock()
    llm.generate = AsyncMock(
        return_value=json.dumps(
            {"status": verdict, "reasoning": "stub", "evidence_quote": record[:30]}
        )
    )
    verifier = CitationVerifierV2(llm=llm, passage_fetcher=fetch, tool_mode="off")
    answer = _answer(f"{proposition} [N1].", _citation("N1", "n1", "record"))
    claim = _draft_claim_for(answer, answer.citations[0], answer.answer)
    report = await verifier.verify_draft(SynthesizedDraft(claims=[claim]))
    return report.checks[0], llm.generate.call_args.args[0]


@pytest.mark.parametrize("kind", ["node", "passage"])
@pytest.mark.asyncio
async def test_both_prompts_carry_the_standard_and_its_four_examples(kind) -> None:
    _check_, prompt = await _judge(
        "Frede says X", "Frede says X.", verdict="VERIFIED", kind=kind
    )

    assert "Standard of support" in prompt
    assert "supports the SUBSTANCE of the proposition" in prompt
    assert "hunting for missing wording is NOT the job" in prompt
    assert "the absence of a phrase is not a mismatch" in prompt
    # The equivalences the production judge refused.
    assert "'power to do otherwise' is 'control over acting and not acting'" in prompt
    assert (
        "'has free choices as its object, not as its effect' is 'does not produce them'"
        in prompt
    )
    assert "'emerges principally with Augustine'" in prompt
    # Two VERIFIED-by-paraphrase and two WEAK-by-added-relation examples.
    assert prompt.count("VERIFIED by paraphrase:") == 2
    assert prompt.count("WEAK by added relation:") == 2
    assert "Alexander defines what depends on us" in prompt
    assert "Origen distinguishes foreknowledge" in prompt
    assert "Gibbons agrees with Frede" in prompt
    assert "Bobzien and Frede differ" in prompt
    # The adversarial stance stays.
    assert "ADVERSARIAL citation auditor" in prompt
    assert "a false approval of a fabrication" in prompt
    # The literalist bias is gone from both templates.
    for template in (VERIFY_PROMPT, NODE_VERIFY_PROMPT):
        assert "choose WEAK" not in template
        assert "explicitly" not in template
    assert SUPPORT_STANDARD_INSTRUCTION in prompt


@pytest.mark.parametrize(("proposition", "record"), PARAPHRASE_CASES)
@pytest.mark.asyncio
async def test_paraphrase_cases_are_judged_under_the_substance_standard(
    proposition, record
) -> None:
    check, prompt = await _judge(proposition, record, verdict="VERIFIED")

    assert check.status is CitationStatus.VERIFIED
    assert check.claim == proposition
    assert proposition in prompt
    assert record in prompt
    assert "A faithful paraphrase, a reasonable summary" in prompt
    assert "need not contain every sub-clause of the writer's wording" in prompt


@pytest.mark.parametrize(("proposition", "record", "absent"), ADDED_RELATION_CASES)
@pytest.mark.asyncio
async def test_added_relation_cases_stay_weak_and_the_prompt_exposes_it(
    proposition, record, absent
) -> None:
    check, prompt = await _judge(proposition, record, verdict="WEAK")

    assert check.status is CitationStatus.WEAK
    # The judge sees the proposition with its added relation and the record
    # that does not carry it.
    assert proposition in prompt
    assert record in prompt
    assert absent not in record
    assert "ADDS an attribution or a relation the evidence does not carry" in prompt
    assert "X agrees with Y, X differs from Y, X's method" in prompt


def test_unmarked_list_items_and_paragraph_extensions_are_audited():
    answer = ScholarlyAnswer(
        answer=(
            "Cicero distinguishes causes [P1]:\n"
            "1. Principal causes have a property absent from this locus.\n"
            "2. Auxiliary causes precede the event [P1].\n\n"
            "An unsupported historical assertion follows without a marker."
        ),
        question="De fato 41",
        citations=[_citation("P1", "cicero41", "Cicero, De fato 41")],
    )
    pairs = _enumerate_audit_pairs(answer)
    assert any(
        "property absent" in p.claim and p.citation.id == "cicero41" for p in pairs
    )
    assert any("unsupported historical" in p.claim for p in pairs)
    assert {p.sentence_index for p in pairs} == {0, 1, 2, 3}
