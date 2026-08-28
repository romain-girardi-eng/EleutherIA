"""Boundary tests for the GraphRAG publication contract.

These tests exercise the public ``GraphRAGService`` facade and its in-process
cache, not just the pure verdict helper.  A draft with per-citation failures
crosses the boundary with the failing sentences withheld; a draft the gate
blocks (verifier crash, unrecorded verdicts, missing gate metadata) crosses as
no answer and never creates a cache entry.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from eleutheria_graphrag.agents.publication_gate import (
    WITHHELD_SENTENCE_MARKER,
    apply_publication_verdict,
)
from eleutheria_graphrag.agents.scholarly_agent import ScholarlyAgent
from eleutheria_graphrag.agents.state import Citation, ScholarlyAnswer
from eleutheria_graphrag.services.graphrag_service import GraphRAGService


def _audit_metadata(
    *,
    total: int = 20,
    verified: int = 20,
    weak: int = 0,
    rejected: int = 0,
    missing: int = 0,
    status: str = "passed",
    aborted: bool = False,
    record_verdicts: bool = True,
) -> dict:
    audit = {
        "status": status,
        "total": total,
        "sampled": total,
        "audited_citations": total,
        "total_citations": total,
        "verified": verified,
        "weak": weak,
        "rejected": rejected,
        "missing": missing,
        "parse_errors": 0,
        "aborted": aborted,
    }
    if record_verdicts:
        failing = [("WEAK", weak), ("REJECTED", rejected), ("MISSING", missing)]
        failed_ids = []
        next_id = verified
        for verdict, count in failing:
            for _ in range(count):
                failed_ids.append((f"c{next_id}", verdict))
                next_id += 1
        audit["verified_citations"] = [f"c{i}" for i in range(verified)]
        audit["failed_citations"] = [
            {
                "citation_id": cid,
                "status": verdict,
                "claim": "claim",
                "reasoning": "reasoning",
                "parse_error": False,
            }
            for cid, verdict in failed_ids
        ]
    return {
        "scholar_synthesis": {"status": "ok", "degraded": False},
        "content_gate": {"status": "passed", "passed": True},
        "citation_verifier_v2": audit,
    }


def _citations(count: int) -> list[dict]:
    return [
        {"ref": f"P{i}", "type": "passage", "id": f"c{i}", "label": f"Passage {i}"}
        for i in range(count)
    ]


def _prose(count: int) -> str:
    return " ".join(f"Claim number {i} [P{i}]." for i in range(count))


def _service_with_result(result: dict) -> tuple[GraphRAGService, AsyncMock]:
    service = GraphRAGService(db_service=MagicMock())
    service._kg_loaded = True
    agent = AsyncMock()
    agent.query_dict = AsyncMock(return_value=result)
    service._agent = agent
    return service, agent


@pytest.mark.asyncio
async def test_fully_verified_result_is_admitted_to_cache_unchanged() -> None:
    result = {
        "answer": _prose(20),
        "question": "q",
        "citations": _citations(20),
        "claim_ledger": [],
        "metadata": _audit_metadata(),
    }
    service, agent = _service_with_result(result)

    first = await service.query("verified question")
    second = await service.query("verified question")

    assert first["answer"] == second["answer"] == _prose(20)
    assert second["cached"] is True
    assert first["metadata"]["publication_gate"]["status"] == "passed"
    assert first["metadata"]["quality_badge"] == "High"
    assert agent.query_dict.await_count == 1


@pytest.mark.asyncio
async def test_one_rejection_out_of_twenty_withholds_one_sentence() -> None:
    """Formerly an all-or-nothing block; now the failing sentence is withheld
    and the nineteen verified sentences are published.  The holed prose is
    never cached: a one-off verdict is recomputed for the next asker."""
    metadata = _audit_metadata(verified=19, rejected=1, status="failed", aborted=False)
    draft = {
        "answer": _prose(20),
        "question": "q",
        "citations": _citations(20),
        "claim_ledger": [
            {
                "claim": f"Claim number {i}.",
                "evidence_ids": [f"c{i}"],
                "status": "supported",
            }
            for i in range(20)
        ],
        "metadata": metadata,
    }
    service, agent = _service_with_result(draft)

    first = await service.query("same question")
    second = await service.query("same question")

    assert "Claim number 19 [P19]." not in first["answer"]
    assert "Claim number 18 [P18]." in first["answer"]
    assert first["answer"].count(WITHHELD_SENTENCE_MARKER) == 1
    assert [c["id"] for c in first["citations"]] == [f"c{i}" for i in range(19)]
    assert first["claim_ledger"][19]["status"] == "insufficient"
    assert first["claim_ledger"][19]["status_reason"] == "withheld: rejected"
    assert first["claim_ledger"][0]["status"] == "supported"

    gate = first["metadata"]["publication_gate"]
    assert gate["publishable"] is True
    assert gate["status"] == "partial"
    assert gate["withholding"]["withheld_sentences"] == 1
    assert gate["withholding"]["published_sentences"] == 19
    assert gate["withholding"]["reasons"] == {"rejected": 1}
    assert first["metadata"]["quality_badge"] == "Partial"

    # A partial verdict is published but not replayed: the second asker gets
    # a fresh run, with the same deterministic verdict on the same draft.
    assert "cached" not in second
    assert service._response_cache._cache == {}
    assert agent.query_dict.await_count == 2
    for key in ("answer", "citations", "claim_ledger"):
        assert second[key] == first[key]
    assert second["metadata"]["publication_gate"] == gate


@pytest.mark.asyncio
async def test_every_sentence_withheld_blocks_and_never_caches() -> None:
    """A verdict that only exists after application must still govern the
    cache: an answer emptied by withholding is blocked, not replayed."""
    metadata = _audit_metadata(total=2, verified=0, rejected=2, status="failed")
    draft = {
        "answer": _prose(2),
        "question": "q",
        "citations": _citations(2),
        "claim_ledger": [],
        "metadata": metadata,
    }
    service, agent = _service_with_result(draft)

    first = await service.query("hollow question")
    second = await service.query("hollow question")

    assert first["answer"] == second["answer"] == ""
    assert first["metadata"]["publication_gate"]["publishable"] is False
    assert "all_sentences_withheld" in first["metadata"]["publication_gate"]["reasons"]
    assert service._response_cache._cache == {}
    assert agent.query_dict.await_count == 2


@pytest.mark.asyncio
async def test_failure_counts_without_verdict_ids_block_and_never_cache() -> None:
    """A verdict that cannot be applied per sentence is a safety-class block."""
    metadata = _audit_metadata(
        verified=19, rejected=1, status="failed", record_verdicts=False
    )
    draft = {
        "answer": "Internal draft that must never be published.",
        "question": "q",
        "citations": _citations(20),
        "claim_ledger": [{"claim": "unsafe"}],
        "metadata": metadata,
    }
    service, agent = _service_with_result(draft)

    first = await service.query("same question")
    second = await service.query("same question")

    assert first["answer"] == second["answer"] == ""
    assert first["citations"] == first["claim_ledger"] == []
    assert first["metadata"]["publication_gate"]["publishable"] is False
    assert (
        "citation_verdicts_unrecorded"
        in first["metadata"]["publication_gate"]["reasons"]
    )
    assert first["metadata"]["quality_badge"] == "Blocked"
    assert service._response_cache._cache == {}
    assert agent.query_dict.await_count == 2  # second request was not a cache hit


@pytest.mark.asyncio
async def test_missing_gate_metadata_withholds_and_never_caches() -> None:
    draft = {
        "answer": "Legacy unaudited draft.",
        "question": "q",
        "citations": [{"id": "legacy-citation"}],
        "claim_ledger": [{"claim": "legacy claim"}],
        "metadata": {},
    }
    service, agent = _service_with_result(draft)

    first = await service.query("legacy question")
    second = await service.query("legacy question")

    assert first["answer"] == second["answer"] == ""
    assert first["citations"] == first["claim_ledger"] == []
    assert first["metadata"]["publication_gate"]["publishable"] is False
    assert "content_gate_not_passed" in first["metadata"]["publication_gate"]["reasons"]
    assert (
        "citation_audit_not_passed" in first["metadata"]["publication_gate"]["reasons"]
    )
    assert service._response_cache._cache == {}
    assert agent.query_dict.await_count == 2


@pytest.mark.asyncio
async def test_verifier_exception_blocks_everything_and_never_caches() -> None:
    """An infrastructure failure is not a WEAK verdict: nothing is published."""
    metadata = _audit_metadata(
        total=0, verified=0, status="error", aborted=True, record_verdicts=False
    )
    metadata["citation_verifier_v2"].update(
        {
            "total_citations": 20,
            "audited_citations": 0,
            "reason": "RuntimeError: provider down",
            "infrastructure_failure": True,
        }
    )
    draft = {
        "answer": _prose(20),
        "question": "q",
        "citations": _citations(20),
        "claim_ledger": [],
        "metadata": metadata,
    }
    service, agent = _service_with_result(draft)

    result = await service.query("provider failure")

    assert result["answer"] == ""
    assert result["citations"] == []
    reasons = result["metadata"]["publication_gate"]["reasons"]
    assert "citation_audit_not_passed" in reasons
    assert "citation_audit_infrastructure_failure" in reasons
    assert service._response_cache._cache == {}
    agent.query_dict.assert_awaited_once()


@pytest.mark.asyncio
async def test_public_scholarly_agent_facade_withholds_weak_sentence() -> None:
    metadata = _audit_metadata(verified=2, weak=1, status="failed")
    internal = ScholarlyAnswer(
        answer="Solid claim [P0]. Another solid claim [P1]. Extrapolated claim [P2].",
        question="q",
        citations=[
            Citation(ref=f"P{i}", type="passage", id=f"c{i}", label=f"Passage {i}")
            for i in range(3)
        ],
        metadata=metadata,
    )
    agent = ScholarlyAgent(MagicMock())
    agent._run_react = AsyncMock(return_value=internal)  # type: ignore[method-assign]

    public = await agent.query("question", agent_mode="react")

    assert public.answer == (
        f"Solid claim [P0]. Another solid claim [P1]. {WITHHELD_SENTENCE_MARKER}"
    )
    assert [c.id for c in public.citations] == ["c0", "c1"]
    assert public.quality_badge == "Partial"
    assert public.metadata["publication_gate"]["publishable"] is True
    assert public.metadata["publication_gate"]["status"] == "partial"


@pytest.mark.asyncio
async def test_public_scholarly_agent_facade_withholds_internal_blocked_draft() -> None:
    metadata = _audit_metadata(
        verified=19, weak=1, status="failed", record_verdicts=False
    )
    internal = ScholarlyAnswer(
        answer="Internal diagnostic draft.",
        question="q",
        metadata=metadata,
    )
    agent = ScholarlyAgent(MagicMock())
    agent._run_react = AsyncMock(return_value=internal)  # type: ignore[method-assign]

    public = await agent.query("question", agent_mode="react")

    assert public.answer == ""
    assert public.citations == []
    assert public.metadata["publication_gate"]["publishable"] is False


@pytest.mark.asyncio
async def test_sync_facade_and_service_boundary_agree() -> None:
    """The model-form facade and the mapping-form service apply one verdict."""
    metadata = _audit_metadata(verified=2, missing=1, status="failed")
    internal = ScholarlyAnswer(
        answer="Solid claim [P0]. Another solid claim [P1]. Unfetchable claim [P2].",
        question="q",
        citations=[
            Citation(ref=f"P{i}", type="passage", id=f"c{i}", label=f"Passage {i}")
            for i in range(3)
        ],
        metadata=metadata,
    )
    agent = ScholarlyAgent(MagicMock())
    agent._run_react = AsyncMock(return_value=internal)  # type: ignore[method-assign]
    public = await agent.query("question", agent_mode="react")

    draft = {
        "answer": internal.answer,
        "question": "q",
        "citations": [c.model_dump() for c in internal.citations],
        "claim_ledger": [],
        "metadata": internal.metadata,
    }
    service, _agent = _service_with_result(draft)
    via_service = await service.query("question")

    assert via_service["answer"] == public.answer
    assert [c["id"] for c in via_service["citations"]] == [
        c.id for c in public.citations
    ]
    assert (
        via_service["metadata"]["publication_gate"]
        == public.metadata["publication_gate"]
    )
    assert via_service["metadata"]["quality_badge"] == public.quality_badge == "Partial"


@pytest.mark.asyncio
async def test_deep_mode_polish_after_the_gate_is_withheld_from_the_verdict() -> None:
    """The agent facade applies the gate before the deep-mode passes run;
    the polished rewrite produced afterwards must not resurrect the withheld
    sentence, and the service must not trust the stale ``applied`` flag."""
    metadata = _audit_metadata(verified=19, rejected=1, status="failed", aborted=False)
    gated = apply_publication_verdict(
        {
            "answer": _prose(20),
            "question": "q",
            "citations": _citations(20),
            "claim_ledger": [],
            "metadata": metadata,
        }
    )
    assert "Claim number 19 [P19]." not in gated["answer"]
    service, agent = _service_with_result(gated)

    async def _no_counter_evidence(*_args, **_kwargs):
        return MagicMock(total_testimonia=0, model_dump=lambda: {"total": 0})

    async def _polish(*, result, **_kwargs):
        return {**result, "polished_markdown": f"# Polished\n\n{_prose(20)}"}

    service._run_counter_evidence_hunt = _no_counter_evidence  # type: ignore[method-assign]
    service._run_methodology_and_polishing = _polish  # type: ignore[method-assign]

    published = await service.query("deep question", hunt_counter_evidence=True)

    assert published["answer"] == gated["answer"]
    assert "Claim number 19 [P19]." not in published["polished_markdown"]
    assert published["polished_markdown"].count(WITHHELD_SENTENCE_MARKER) == 1
    assert published["polished_markdown"].startswith("# Polished")
    assert published["metadata"]["publication_gate"]["status"] == "partial"


@pytest.mark.asyncio
async def test_deep_mode_passes_are_skipped_on_a_blocked_answer() -> None:
    """The agent's own gate blocked the draft (answer ""): the counter-
    evidence hunt and the resynthesis / polishing passes must not run."""
    blocked = apply_publication_verdict(
        {
            "answer": "Internal draft that must never be published.",
            "question": "q",
            "citations": _citations(20),
            "claim_ledger": [],
            "metadata": _audit_metadata(
                verified=19, rejected=1, status="failed", record_verdicts=False
            ),
        }
    )
    assert blocked["answer"] == ""
    service, agent = _service_with_result(blocked)
    hunt = AsyncMock()
    polish = AsyncMock()
    service._run_counter_evidence_hunt = hunt  # type: ignore[method-assign]
    service._resynthesize_with_counter_evidence = polish  # type: ignore[method-assign]
    service._run_methodology_and_polishing = polish  # type: ignore[method-assign]

    published = await service.query("deep question", hunt_counter_evidence=True)

    hunt.assert_not_awaited()
    polish.assert_not_awaited()
    assert published["answer"] == ""
    assert published["metadata"]["publication_gate"]["publishable"] is False
    assert published["metadata"]["deep_mode_skipped"] == "publication_blocked"
    assert service._response_cache._cache == {}
    agent.query_dict.assert_awaited_once()


@pytest.mark.asyncio
async def test_degraded_synthesis_is_published_but_never_cached() -> None:
    metadata = _audit_metadata()
    metadata["scholar_synthesis"] = {"status": "degraded", "degraded": True}
    metadata["quality_badge"] = "Low"
    result = {
        "answer": _prose(20),
        "question": "q",
        "citations": _citations(20),
        "claim_ledger": [],
        "metadata": metadata,
    }
    service, agent = _service_with_result(result)

    first = await service.query("hedged question")
    second = await service.query("hedged question")

    assert first["answer"] == _prose(20)
    assert first["metadata"]["publication_gate"]["publishable"] is True
    assert first["metadata"]["publication_gate"]["warnings"] == [
        "scholar_synthesis_degraded"
    ]
    assert first["metadata"]["quality_badge"] == "Low"
    assert "cached" not in second
    assert agent.query_dict.await_count == 2
