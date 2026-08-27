"""SSE boundary of the publication gate: the terminal ``complete`` frame.

The streamed dialectical answer is buffered until the citation audit ran.
When one citation fails the adversarial audit, the terminal frame (and the
prose chunks released with it) must carry the SAME withheld prose the sync
facade and the answer caches publish — never the unaudited draft, never an
empty answer for a single failing citation.  A crashed audit still blocks.
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock

import pytest

from eleutheria_graphrag.agents.publication_gate import (
    WITHHELD_SENTENCE_MARKER,
    annotate_publication_decision,
)
from eleutheria_graphrag.agents.scholarly_agent import ScholarlyAgent
from eleutheria_graphrag.agents.state import Citation, ScholarlyAnswer
from eleutheria_graphrag.models.verification import (
    CitationCheck,
    CitationStatus,
    VerificationReport,
)

from .test_dialectical_render_cutover import DIALECTICAL_PROSE, make_stream_segmented
from .test_dialectical_stream_plumbing import (
    _answer_chunk_text,
    _classify_like_route,
    _collect_stream,
)


def _verifier_rejecting(rejected_id: str) -> AsyncMock:
    async def _verify(draft):
        return VerificationReport.from_checks(
            [
                CitationCheck(
                    citation_id=claim.citation_id,
                    status=(
                        CitationStatus.REJECTED
                        if claim.citation_id == rejected_id
                        else CitationStatus.VERIFIED
                    ),
                    reasoning='"quote" contradicts the claim'
                    if claim.citation_id == rejected_id
                    else "fixture explicitly supports the claim",
                    claim=claim.claim,
                )
                for claim in draft.claims
            ]
        )

    verifier = AsyncMock()
    verifier.verify_draft = AsyncMock(side_effect=_verify)
    return verifier


# The cutover fixture cites everything in ONE sentence; here the Cicero
# passage gets its own sentence so a single rejection can be withheld without
# orphaning the two positions cited beside it.
SPLIT_PROSE = (
    "The liveliest dispute is not whether the ancients were free but whether they "
    "had the concept at all. Bobzien holds the ancients had no free-will problem "
    "[P_bobzien_no_problem: Bobzien, 1998 p. 330], whereas Frede dates a notion of "
    "will to Epictetus [P_frede_epictetus: Frede, 2011 p. 44]; the two positions "
    "[edge: opposes P_bobzien_no_problem->P_frede_epictetus] argue over the Stoic "
    "doctrine of assent. That doctrine is recorded at "
    "[passage_cic_fat_41: Cicero, De Fato 41]. What remains genuinely open is the "
    "dating of the concept."
)


def _agent_with(verifier: AsyncMock, prose: str = SPLIT_PROSE) -> ScholarlyAgent:
    llm = AsyncMock()
    llm.generate = AsyncMock(return_value=prose)
    llm.stream_segmented = make_stream_segmented(prose)
    llm.last_reasoning_content = ""
    llm.last_model_used = "accounts/fireworks/models/kimi-k2p6"
    llm.last_provider_used = "fireworks"
    deps = AsyncMock()
    deps.llm = llm
    deps.verifier_v2 = verifier
    return ScholarlyAgent(deps)


def _terminal_frames(events: list[str]) -> tuple[dict, list[str], list[dict]]:
    complete = None
    prose: list[str] = []
    warnings: list[dict] = []
    for chunk in events:
        kind, parsed = _classify_like_route(chunk)
        if kind == "complete" and parsed is not None:
            complete = parsed["data"]
        elif kind == "answer_chunk":
            # The publication tail releases gated prose as TYPED answer_chunk
            # frames; read the payload the way the route does.
            text = _answer_chunk_text(chunk)
            if text is not None:
                prose.append(text)
        elif kind == "verification_warning" and parsed is not None:
            warnings.append(parsed["data"])
    assert complete is not None, "no terminal complete frame"
    return complete, prose, warnings


def _answer_final(events: list[str]) -> dict:
    finals = [
        parsed["data"]
        for chunk in events
        if (parsed := _classify_like_route(chunk)[1]) is not None
        and parsed.get("type") == "answer_final"
    ]
    assert len(finals) == 1, "exactly one answer_final verdict frame"
    return finals[0]


@pytest.mark.asyncio
async def test_terminal_frame_withholds_only_the_rejected_sentence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ELEUTHERIA_SCHOLAR_RAG", "true")
    agent = _agent_with(_verifier_rejecting("cic_fat_41"))

    events = await _collect_stream(agent, "big open debates about free will")
    complete, prose, warnings = _terminal_frames(events)

    answer = complete["answer"]
    assert answer, "a single rejected citation must not empty the answer"
    assert "[passage_cic_fat_41" not in answer
    assert WITHHELD_SENTENCE_MARKER in answer
    assert answer.startswith("The liveliest dispute")
    assert answer.endswith("the dating of the concept.")
    # The prose released after the gate is exactly the published answer.
    assert "".join(prose) == answer

    gate = complete["metadata"]["publication_gate"]
    assert gate["status"] == "partial"
    assert gate["publishable"] is True
    assert gate["withholding"]["reasons"] == {"rejected": 1}
    assert gate["withholding"]["withheld_citations"][0]["citation_id"] == "cic_fat_41"
    assert complete["metadata"]["quality_badge"] == "Partial"
    surviving = {c["id"] for c in complete["citations"]}
    assert "cic_fat_41" not in surviving
    # The positions cited in the sentence that survived stay public.
    assert {"bobzien_no_problem", "frede_epictetus"} <= surviving

    assert warnings and warnings[-1]["stage"] == "publication_gate"
    assert warnings[-1]["status"] == "partial"

    # The answer_final verdict frame carries the same sentence-level verdict
    # the terminal frame does: the withheld prose, and the withholding record.
    final = _answer_final(events)
    assert final["withheld"] is False
    assert final["status"] == "partial"
    assert final["answer"] == answer
    assert final["withholding"]["reasons"] == {"rejected": 1}
    assert final["publication_gate"]["status"] == "partial"


@pytest.mark.asyncio
async def test_terminal_frame_matches_the_sync_facade_verdict(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Same draft, same verdict on the SSE boundary and on the sync facade."""
    monkeypatch.setenv("ELEUTHERIA_SCHOLAR_RAG", "true")
    agent = _agent_with(_verifier_rejecting("cic_fat_41"))

    events = await _collect_stream(agent, "big open debates about free will")
    complete, _prose, _warnings = _terminal_frames(events)

    # Rebuild the pre-gate draft from the terminal frame's own metadata and
    # citations (plus the one the gate dropped) and push it through the
    # facade's application: the outputs must coincide.
    facade = annotate_publication_decision(
        ScholarlyAnswer(
            answer=SPLIT_PROSE,
            question=complete["question"],
            citations=[
                *(Citation.model_validate(c) for c in complete["citations"]),
                Citation(
                    ref="cic_fat_41",
                    type="passage",
                    id="cic_fat_41",
                    label="Cicero, De Fato 41",
                ),
            ],
            metadata={
                k: v for k, v in complete["metadata"].items() if k != "publication_gate"
            },
        ),
        withhold_prose=True,
    )
    assert facade.answer == complete["answer"]
    assert facade.metadata["publication_gate"]["status"] == "partial"
    assert (
        facade.metadata["publication_gate"]["withholding"]["reasons"]
        == (complete["metadata"]["publication_gate"]["withholding"]["reasons"])
    )


@pytest.mark.asyncio
async def test_terminal_frame_blocks_on_verifier_crash(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ELEUTHERIA_SCHOLAR_RAG", "true")
    verifier = AsyncMock()
    verifier.verify_draft = AsyncMock(side_effect=RuntimeError("provider down"))
    agent = _agent_with(verifier)

    events = await _collect_stream(agent, "big open debates about free will")
    complete, prose, warnings = _terminal_frames(events)

    assert complete["answer"] == ""
    assert complete["citations"] == []
    assert prose == []
    gate = complete["metadata"]["publication_gate"]
    assert gate["publishable"] is False
    assert "citation_audit_infrastructure_failure" in gate["reasons"]
    assert complete["metadata"]["quality_badge"] == "Blocked"
    assert warnings[-1]["status"] == "blocked"
    assert json.dumps(gate)  # machine-readable


@pytest.mark.asyncio
async def test_terminal_frame_blocks_when_no_cited_claim_survives(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Every citation sits in the one sentence the rejection takes down: the
    verified positions are orphaned with it, and uncited framing alone is not
    an answer.  The SSE boundary blocks instead of publishing the remnant."""
    monkeypatch.setenv("ELEUTHERIA_SCHOLAR_RAG", "true")
    agent = _agent_with(_verifier_rejecting("cic_fat_41"), prose=DIALECTICAL_PROSE)

    events = await _collect_stream(agent, "big open debates about free will")
    complete, prose, warnings = _terminal_frames(events)

    assert complete["answer"] == ""
    assert complete["citations"] == []
    assert prose == []
    gate = complete["metadata"]["publication_gate"]
    assert gate["publishable"] is False
    assert "no_cited_claims_survive" in gate["reasons"]
    reasons = gate["withholding"]["reasons"]
    assert reasons["rejected"] == 1
    assert reasons["orphaned"] >= 2
    assert complete["metadata"]["quality_badge"] == "Blocked"
    assert warnings[-1]["status"] == "blocked"
