"""The FSM streaming fallback (``agent_mode != "react"``) is a supported path
and must honour the same fail-closed protocol as the agentic stream.

The legacy graph ends at ``ProgrammaticVerify``, which is not a publication
verdict. ``query_stream`` therefore runs the FSM answer through the shared
verification + publication tail: the content gate, the citation audit and the
single publication decision, then ``answer_final`` and — only when publishable
— the plain ``answer_chunk`` frames before ``complete``.
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest

from eleutheria_graphrag.agents.scholarly_agent import (
    ANSWER_FINAL_EVENT,
    ANSWER_PROVISIONAL_EVENT,
    ScholarlyAgent,
)
from eleutheria_graphrag.agents.state import (
    Citation,
    ClaimLedgerItem,
    ClaimStatus,
    ScholarlyAnswer,
)

from .test_dialectical_stream_plumbing import (
    _answer_chunk_text,
    _classify_like_route,
    _clean_verifier,
)

_QUESTION = "Did Chrysippus hold that assent is up to us?"
_PROSE = "Chrysippus holds that assent is up to us [P1]. " * 12


def _fsm_answer() -> ScholarlyAnswer:
    return ScholarlyAnswer(
        answer=_PROSE.strip(),
        question=_QUESTION,
        citations=[
            Citation(
                ref="P1",
                type="passage",
                id="passage_cicero_fato_41",
                label="Cicero, De fato 41",
                confidence=0.9,
            )
        ],
        claim_ledger=[
            ClaimLedgerItem(
                claim="Chrysippus holds that assent is up to us",
                evidence_ids=["passage_cicero_fato_41"],
                status=ClaimStatus.SUPPORTED,
                confidence=0.9,
            )
        ],
    )


def _agent(*, verifier: AsyncMock | None) -> ScholarlyAgent:
    llm = AsyncMock()
    llm.last_model_used = "fake-model"
    llm.last_provider_used = "fake"
    deps = AsyncMock()
    deps.llm = llm
    deps.verifier_v2 = verifier
    return ScholarlyAgent(deps)


async def _collect(agent: ScholarlyAgent) -> list[str]:
    with patch.object(
        ScholarlyAgent, "_run_fsm", AsyncMock(return_value=_fsm_answer())
    ):
        return [ev async for ev in agent.query_stream(_QUESTION, agent_mode="fsm")]


def _kinds(events: list[str]) -> list[str]:
    return [_classify_like_route(c)[0] for c in events]


def _frames(events: list[str], kind: str) -> list[dict]:
    return [
        parsed
        for c in events
        if (parsed := _classify_like_route(c)[1]) is not None
        and parsed.get("type") == kind
    ]


@pytest.mark.asyncio
async def test_fsm_stream_withholds_prose_when_the_audit_cannot_run() -> None:
    events = await _collect(_agent(verifier=None))
    kinds = _kinds(events)

    assert "answer_chunk" not in kinds, "ungated FSM prose crossed as an answer"
    assert ANSWER_PROVISIONAL_EVENT not in kinds  # the FSM has no live draft
    finals = _frames(events, ANSWER_FINAL_EVENT)
    assert len(finals) == 1
    assert finals[0]["data"]["withheld"] is True
    assert finals[0]["data"]["answer"] == ""
    assert "citation_audit_not_passed" in finals[0]["data"]["reasons"]

    complete = _frames(events, "complete")[0]
    assert kinds[-1] == "complete"
    assert complete["data"]["answer"] == ""
    assert complete["data"]["metadata"]["publication_gate"]["publishable"] is False
    assert "Chrysippus holds" not in json.dumps(
        {k: complete["data"].get(k) for k in ("answer", "citations", "claim_ledger")}
    )


@pytest.mark.asyncio
async def test_fsm_stream_releases_prose_only_after_a_passing_verdict() -> None:
    events = await _collect(_agent(verifier=_clean_verifier()))
    kinds = _kinds(events)

    finals = _frames(events, ANSWER_FINAL_EVENT)
    assert len(finals) == 1
    final = finals[0]
    assert final["data"]["withheld"] is False
    assert final["data"]["publication_gate"]["publishable"] is True
    assert "Chrysippus holds that assent is up to us" in final["data"]["answer"]

    final_idx = kinds.index(ANSWER_FINAL_EVENT)
    assert all(k != "answer_chunk" for k in kinds[:final_idx])
    assert "answer_chunk" in kinds[final_idx:]
    assert kinds[-1] == "complete"
    released = "".join(
        text for c in events if (text := _answer_chunk_text(c)) is not None
    )
    assert released == final["data"]["answer"]
    complete = _frames(events, "complete")[0]
    assert complete["data"]["answer"] == final["data"]["answer"]
    assert complete["data"]["metadata"]["content_gate"]["status"] == "not_applicable"
    assert complete["data"]["metadata"]["citation_verifier_v2"]["status"] == "passed"
