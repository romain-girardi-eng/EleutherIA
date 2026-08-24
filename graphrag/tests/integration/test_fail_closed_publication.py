"""Boundary tests for the fail-closed GraphRAG publication contract.

These tests exercise the public ``GraphRAGService`` facade and its in-process
cache, not just the pure verdict helper.  A rejected/error draft may exist
internally for diagnostics, but it must cross the boundary as no answer and
must never create a cache entry.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from eleutheria_graphrag.agents.scholarly_agent import ScholarlyAgent
from eleutheria_graphrag.agents.state import ScholarlyAnswer
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
) -> dict:
    return {
        "scholar_synthesis": {"status": "ok", "degraded": False},
        "content_gate": {"status": "passed", "passed": True},
        "citation_verifier_v2": {
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
        },
    }


def _service_with_result(result: dict) -> tuple[GraphRAGService, AsyncMock]:
    service = GraphRAGService(db_service=MagicMock())
    service._kg_loaded = True
    agent = AsyncMock()
    agent.query_dict = AsyncMock(return_value=result)
    service._agent = agent
    return service, agent


@pytest.mark.asyncio
async def test_fully_verified_result_is_the_only_result_admitted_to_cache() -> None:
    result = {
        "answer": "Verified answer.",
        "question": "q",
        "citations": [{"id": f"c{i}"} for i in range(20)],
        "claim_ledger": [],
        "metadata": _audit_metadata(),
    }
    service, agent = _service_with_result(result)

    first = await service.query("verified question")
    second = await service.query("verified question")

    assert first["answer"] == second["answer"] == "Verified answer."
    assert second["cached"] is True
    assert agent.query_dict.await_count == 1


@pytest.mark.asyncio
async def test_one_rejection_out_of_twenty_withholds_and_never_caches() -> None:
    metadata = _audit_metadata(
        verified=19,
        rejected=1,
        status="failed",
        # One rejection in twenty is below the aggregate abort threshold. The
        # stricter publication contract must still block it.
        aborted=False,
    )
    draft = {
        "answer": "Internal draft that must never be published.",
        "question": "q",
        "citations": [{"id": f"c{i}"} for i in range(20)],
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
        "rejected_citations_present" in first["metadata"]["publication_gate"]["reasons"]
    )
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
async def test_verifier_exception_withholds_and_never_caches() -> None:
    metadata = _audit_metadata(total=0, verified=0, status="error", aborted=True)
    metadata["citation_verifier_v2"].update(
        {
            "total_citations": 20,
            "audited_citations": 0,
            "reason": "RuntimeError: provider down",
        }
    )
    draft = {
        "answer": "Unaudited draft.",
        "question": "q",
        "citations": [{"id": f"c{i}"} for i in range(20)],
        "claim_ledger": [],
        "metadata": metadata,
    }
    service, agent = _service_with_result(draft)

    result = await service.query("provider failure")

    assert result["answer"] == ""
    assert result["citations"] == []
    assert result["metadata"]["publication_gate"]["publishable"] is False
    assert (
        "citation_audit_not_passed" in result["metadata"]["publication_gate"]["reasons"]
    )
    assert service._response_cache._cache == {}
    agent.query_dict.assert_awaited_once()


@pytest.mark.asyncio
async def test_public_scholarly_agent_facade_withholds_internal_blocked_draft() -> None:
    metadata = _audit_metadata(
        verified=19,
        weak=1,
        status="failed",
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
