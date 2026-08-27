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
from eleutheria_graphrag.agents.state import ScholarlyAnswer
from eleutheria_graphrag.models.verification import (
    CitationCheck,
    CitationStatus,
    VerificationReport,
)

from .test_dialectical_render_cutover import DIALECTICAL_PROSE, make_stream_segmented
from .test_dialectical_stream_plumbing import _classify_like_route, _collect_stream


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


def _agent_with(verifier: AsyncMock) -> ScholarlyAgent:
    llm = AsyncMock()
    llm.generate = AsyncMock(return_value=DIALECTICAL_PROSE)
    llm.stream_segmented = make_stream_segmented(DIALECTICAL_PROSE)
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
            prose.append(chunk)
        elif kind == "verification_warning" and parsed is not None:
            warnings.append(parsed["data"])
    assert complete is not None, "no terminal complete frame"
    return complete, prose, warnings


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
    assert "cic_fat_41" not in {c["id"] for c in complete["citations"]}

    assert warnings and warnings[-1]["stage"] == "publication_gate"
    assert warnings[-1]["status"] == "partial"


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
    # push it through the facade's application: the outputs must coincide.
    facade = annotate_publication_decision(
        ScholarlyAnswer(
            answer=DIALECTICAL_PROSE,
            question=complete["question"],
            citations=[],
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
