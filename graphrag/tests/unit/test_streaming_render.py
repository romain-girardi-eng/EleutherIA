"""Regression tests for the streaming render path (``_stream_render``).

Guards the fix for the "synthesis never finishes" bug: the final answer used
to be produced by a single blocking ``llm.generate()`` and only chunked
*after* it completed, so a mid-render proxy/tunnel drop left the user with
nothing. The render now streams prose token-by-token, so partial prose reaches
the client as it is generated and survives a cut.
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from types import SimpleNamespace
from typing import Any

import pytest

from eleutheria_graphrag.agents.graph_nodes import build_render_prompt
from eleutheria_graphrag.agents.scholarly_agent import ScholarlyAgent
from eleutheria_graphrag.agents.state import RAGState


class _FakeLLM:
    """Minimal LLM stub that records stream() kwargs and yields fixed chunks."""

    def __init__(self, chunks: list[str], *, raise_after: int | None = None) -> None:
        self._chunks = chunks
        self._raise_after = raise_after
        self.last_model_used = "fake-model"
        self.last_provider_used = "fake"
        self.stream_kwargs: dict[str, Any] = {}

    async def stream(self, _prompt: str, **kwargs: Any) -> AsyncIterator[str]:
        self.stream_kwargs = kwargs
        for i, chunk in enumerate(self._chunks):
            if self._raise_after is not None and i == self._raise_after:
                raise RuntimeError("provider exploded mid-stream")
            yield chunk


def _agent_with(llm: _FakeLLM) -> ScholarlyAgent:
    return ScholarlyAgent(SimpleNamespace(llm=llm))  # type: ignore[arg-type]


def _is_prose(event: str) -> bool:
    """A raw prose chunk — what the route forwards as an answer_chunk."""
    return not event.startswith('{"type":')


async def _collect(gen: AsyncIterator[str]) -> list[str]:
    return [ev async for ev in gen]


@pytest.mark.asyncio
async def test_render_streams_prose_chunks_live() -> None:
    # Long enough to clear the >200-char survival threshold the FE uses.
    chunks = [f"The Stoics held that fate governs all things (sentence {i}). " for i in range(40)]
    llm = _FakeLLM(chunks)
    agent = _agent_with(llm)
    state = RAGState(question="What did the Stoics believe about fate?")

    events = await _collect(agent._stream_render(state))

    # The exact prose chunks were emitted as raw strings (the route wraps each
    # as an answer_chunk). This is the cut-survival property: prose is on the
    # wire *during* render, not withheld until a final blocking call returns.
    prose = [e for e in events if _is_prose(e)]
    assert prose == chunks
    # Enough prose reached the client to clear the FE's >200-char threshold,
    # so a mid-render cut would still render a partial answer.
    assert len("".join(prose)) > 200
    # The render persisted a non-empty answer for the complete event.
    assert state.raw_answer


@pytest.mark.asyncio
async def test_render_passes_model_override_to_stream() -> None:
    llm = _FakeLLM(["some grounded prose. " * 30])
    agent = _agent_with(llm)
    state = RAGState(question="Who was Chrysippus?")

    await _collect(agent._stream_render(state))

    expected_model = build_render_prompt(state)["model_api_id"]
    assert llm.stream_kwargs.get("model_override") == expected_model
    assert llm.stream_kwargs.get("max_tokens") == 16000


@pytest.mark.asyncio
async def test_render_falls_back_when_stream_errors_immediately() -> None:
    # Provider raises before any token — render must still yield an answer
    # (the fallback), never an empty raw_answer that trips synthesisIncomplete.
    llm = _FakeLLM(["unused"], raise_after=0)
    agent = _agent_with(llm)
    state = RAGState(question="What is fate?")

    await _collect(agent._stream_render(state))

    assert state.raw_answer  # non-empty fallback
    assert state.metadata.get("render_answer_mode") == "fallback"
    assert state.metadata.get("render_streamed") is True


@pytest.mark.asyncio
async def test_render_keeps_partial_prose_when_stream_errors_midway() -> None:
    chunks = [f"Partial grounded sentence number {i}. " for i in range(40)]
    llm = _FakeLLM(chunks, raise_after=20)
    agent = _agent_with(llm)
    state = RAGState(question="Compare Chrysippus and Epictetus on fate")

    events = await _collect(agent._stream_render(state))

    streamed = [e for e in events if _is_prose(e)]
    # The 20 chunks emitted before the error reached the client.
    assert streamed == chunks[:20]
    # raw_answer is non-empty (partial prose or fallback), never blank.
    assert state.raw_answer


@pytest.mark.asyncio
async def test_first_event_is_a_render_status_ping() -> None:
    llm = _FakeLLM(["prose " * 50])
    agent = _agent_with(llm)
    state = RAGState(question="What is Stoic fate?")

    events = await _collect(agent._stream_render(state))

    first = json.loads(events[0])
    assert first["type"] == "status"
    assert first["data"]["stage"] == "render_grounded_answer"


@pytest.mark.asyncio
async def test_complete_event_carries_claim_ledger() -> None:
    """Regression: the streaming complete payload omitted claim_ledger
    (only claim_ledger_size in metadata), so the SSE route, the answer
    cache and the /share page always saw an empty ledger on the streaming
    product path."""
    from eleutheria_graphrag.agents.state import ClaimLedgerItem, ScholarlyAnswer

    llm = _FakeLLM(["unused"])
    agent = _agent_with(llm)
    answer = ScholarlyAnswer(
        answer="A grounded answer.",
        question="q",
        claim_ledger=[
            ClaimLedgerItem(
                claim="Chrysippus distinguishes perfect and auxiliary causes",
                evidence_ids=["P1"],
            )
        ],
    )

    events = await _collect(agent._chunk_answer(answer, stream_prose=False))

    complete = json.loads(events[-1])
    assert complete["type"] == "complete"
    ledger = complete["data"]["claim_ledger"]
    assert len(ledger) == 1
    assert ledger[0]["claim"] == (
        "Chrysippus distinguishes perfect and auxiliary causes"
    )
    assert ledger[0]["evidence_ids"] == ["P1"]
    assert complete["data"]["metadata"]["claim_ledger_size"] == 1


def _answer_with_citations(n: int) -> "ScholarlyAnswer":
    from eleutheria_graphrag.agents.state import Citation, ScholarlyAnswer

    return ScholarlyAnswer(
        answer=(
            "The Stoics held that fate (heimarmenē) governs all things "
            + " ".join(f"[P{i + 1}]" for i in range(n))
        ),
        question="What did the Stoics believe about fate?",
        citations=[
            Citation(
                ref=f"P{i + 1}",
                type="passage",
                id=f"passage-uuid-{i + 1}",
                label=f"Chrysippus, On Fate {i + 1}",
                verified=True,
            )
            for i in range(n)
        ],
    )


@pytest.mark.asyncio
async def test_citations_preview_event_carries_structured_citations() -> None:
    """Smoke contract: the early ``citations_preview`` frame (emitted by the
    agent right after ProgrammaticVerify, BEFORE the long verifier-v2 audit)
    carries the SAME structured-citation payload as the terminal ``complete``.

    This is the transport fix for the divergence diagnosed in
    ``data/goals/g3/diagnosis.md``: structured citations used to ride ONLY on
    the terminal ``complete`` event, which is gated behind the audit and never
    arrived before Cloudflare's ~100s idle cut on slow queries — so the public
    path returned prose with zero clickable citations. The preview guarantees
    >=N structured citations reach the client even if the audit/connection is
    later cut.
    """
    MIN_CITATIONS = 3
    llm = _FakeLLM(["unused"])
    agent = _agent_with(llm)
    answer = _answer_with_citations(MIN_CITATIONS)

    preview = json.loads(
        agent._build_complete_event(answer, event_type="citations_preview")
    )
    complete = json.loads(agent._build_complete_event(answer, event_type="complete"))

    # The preview is a distinct, non-terminal frame...
    assert preview["type"] == "citations_preview"
    assert complete["type"] == "complete"
    # ...but carries an identical structured-citation payload (no schema drift).
    assert preview["data"]["citations"] == complete["data"]["citations"]

    cites = preview["data"]["citations"]
    assert len(cites) >= MIN_CITATIONS
    # Each citation is a structured, clickable tuple — not a bare label string.
    for c in cites:
        assert c["ref"]
        assert c["type"] == "passage"
        assert c["id"]
        assert c["label"]
