"""Provisional-answer SSE protocol on the agentic stream path.

Nothing un-audited may look like an answer on the wire. Before the content
gate, the ancient-text verifier and the citation audit have ruled, prose only
crosses as ``answer_provisional`` frames (``provisional: true``); the verdict
arrives as one ``answer_final`` frame carrying the gated text — or an empty
answer with ``withheld: true`` — and only then do the plain ``answer_chunk``
frames (kept for older consumers) and the terminal ``complete`` follow.
"""

from __future__ import annotations

import json

import pytest

from eleutheria_graphrag.agents.scholarly_agent import (
    ANSWER_FINAL_EVENT,
    ANSWER_PROVISIONAL_EVENT,
)

from .test_dialectical_stream_plumbing import (
    _classify_like_route,
    _collect_stream,
    _make_agent,
)

_QUESTION = "big open debates about free will"


def _kinds(events: list[str]) -> list[str]:
    return [_classify_like_route(c)[0] for c in events]


def _first_index(events: list[str], kind: str) -> int:
    return next(i for i, c in enumerate(events) if _classify_like_route(c)[0] == kind)


def _frames(events: list[str], kind: str) -> list[dict]:
    return [
        parsed
        for c in events
        if (parsed := _classify_like_route(c)[1]) is not None
        and parsed.get("type") == kind
    ]


@pytest.mark.asyncio
async def test_prose_is_provisional_until_the_verdict_then_released(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ELEUTHERIA_SCHOLAR_RAG", "true")
    events = await _collect_stream(_make_agent(), _QUESTION)
    kinds = _kinds(events)

    provisional = _frames(events, ANSWER_PROVISIONAL_EVENT)
    assert provisional, "expected the draft to stream as answer_provisional frames"
    for frame in provisional:
        assert frame["provisional"] is True
        assert isinstance(frame["data"], str) and frame["data"]
        # Never a serialized event smuggled as prose.
        assert not frame["data"].lstrip().startswith("{")

    finals = _frames(events, ANSWER_FINAL_EVENT)
    assert len(finals) == 1, "exactly one verdict frame per run"
    final = finals[0]
    assert final["provisional"] is False
    assert final["data"]["withheld"] is False
    assert final["data"]["reasons"] == []
    assert final["data"]["publication_gate"]["publishable"] is True
    assert (
        "Bobzien holds the ancients had no free-will problem" in final["data"]["answer"]
    )

    # Ordering: every provisional frame precedes the verdict, and no plain
    # answer_chunk prose exists before the verdict.
    final_idx = _first_index(events, ANSWER_FINAL_EVENT)
    last_provisional_idx = max(
        i for i, k in enumerate(kinds) if k == ANSWER_PROVISIONAL_EVENT
    )
    assert last_provisional_idx < final_idx
    assert all(k != "answer_chunk" for k in kinds[:final_idx])
    assert "answer_chunk" in kinds[final_idx:], (
        "gated prose must still stream as plain answer_chunks for older consumers"
    )
    assert kinds[-1] == "complete"

    # The released text is the verdict text, byte for byte.
    released = "".join(
        c for c in events if _classify_like_route(c)[0] == "answer_chunk"
    )
    assert released == final["data"]["answer"]
    complete = _frames(events, "complete")[0]
    assert complete["data"]["answer"] == final["data"]["answer"]
    assert final["data"]["citations"] == complete["data"]["citations"]


@pytest.mark.asyncio
async def test_blocked_verdict_withholds_prose_but_still_flags_the_draft(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ELEUTHERIA_SCHOLAR_RAG", "true")
    agent = _make_agent()
    # No citation auditor configured: the publication gate must fail closed.
    agent.deps.verifier_v2 = None

    events = await _collect_stream(agent, _QUESTION)
    kinds = _kinds(events)

    # The live draft still crossed the wire — but only as provisional frames.
    assert ANSWER_PROVISIONAL_EVENT in kinds
    assert "answer_chunk" not in kinds

    final = _frames(events, ANSWER_FINAL_EVENT)[0]
    assert final["data"]["withheld"] is True
    assert final["data"]["answer"] == ""
    assert "citation_audit_not_passed" in final["data"]["reasons"]
    assert final["data"]["quality_badge"] == "Blocked"
    assert final["data"]["citations"] == []

    complete = _frames(events, "complete")[0]
    assert complete["data"]["answer"] == ""
    assert complete["data"]["metadata"]["publication_gate"]["publishable"] is False
    assert kinds[-1] == "complete"


@pytest.mark.asyncio
async def test_provisional_text_never_enters_the_terminal_payload_when_blocked(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The draft text that streamed provisionally must not resurface in the
    answer-bearing fields of the verdict or terminal frames of a blocked run.

    (Diagnostic ``metadata`` keeps stage excerpts for the audit trail; the
    answer, citations and claim ledger are the fields a client renders.)
    """
    monkeypatch.setenv("ELEUTHERIA_SCHOLAR_RAG", "true")
    agent = _make_agent()
    agent.deps.verifier_v2 = None

    events = await _collect_stream(agent, _QUESTION)
    draft = "".join(f["data"] for f in _frames(events, ANSWER_PROVISIONAL_EVENT))
    assert "Bobzien holds the ancients had no free-will problem" in draft

    for kind in (ANSWER_FINAL_EVENT, "complete"):
        data = _frames(events, kind)[0]["data"]
        rendered = json.dumps(
            {k: data.get(k) for k in ("answer", "citations", "claim_ledger")},
            default=str,
        )
        assert "Bobzien holds the ancients had no free-will problem" not in rendered
