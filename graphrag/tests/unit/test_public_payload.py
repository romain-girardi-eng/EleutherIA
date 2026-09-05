"""Every public/cache copy must exclude drafts, including nested diagnostics."""

import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from eleutheria_graphrag.agents.scholarly_agent import ScholarlyAgent
from eleutheria_graphrag.agents.state import ScholarlyAnswer
from eleutheria_graphrag.public_payload import public_payload

DRAFT = "PRIVATE_REJECTED_DRAFT_DO_NOT_PUBLISH"


def private_metadata():
    return {
        "publication_gate": {
            "publishable": False,
            "reasons": ["citation_audit_not_passed"],
        },
        "debug_trace": {"dialectical_synthesis": {"raw_excerpt": DRAFT}},
        "research_graph": {
            "stages": [{"details": {"answer_excerpt": DRAFT}}],
            "claims": [{"claim": DRAFT, "status": "supported"}],
        },
        "citation_verifier_v2": {
            "failed_citations": [
                {
                    "citation_id": "p1",
                    "claim": DRAFT,
                    "reasoning": DRAFT,
                    "pairs": [
                        {"sentence": DRAFT, "sentence_index": 2, "status": "WEAK"}
                    ],
                }
            ],
        },
        "text_verification": {
            "unverified": 1,
            "unverified_texts": [{"text": DRAFT, "action": "removed"}],
        },
    }


def test_public_projection_keeps_verdict_and_ids_without_mutating_internal_trace():
    original = {
        "metadata": private_metadata(),
        "claim_ledger": [
            {"claim": DRAFT, "status": "insufficient"},
            {"claim": "Published claim", "status": "supported", "evidence_ids": ["p2"]},
        ],
    }
    before = json.dumps(original)
    public = public_payload(original)
    assert DRAFT not in json.dumps(public)
    assert (
        public["metadata"]["publication_gate"]
        == original["metadata"]["publication_gate"]
    )
    assert public["claim_ledger"] == [original["claim_ledger"][1]]
    assert (
        public["metadata"]["citation_verifier_v2"]["failed_citations"][0]["citation_id"]
        == "p1"
    )
    assert json.dumps(original) == before
    assert public_payload(public) == public


@pytest.mark.asyncio
async def test_sync_and_stream_public_boundaries_keep_full_draft_only_in_internal_answer():
    answer = ScholarlyAnswer(answer="", question="test", metadata=private_metadata())
    agent = ScholarlyAgent(
        SimpleNamespace(
            llm=SimpleNamespace(last_model_used="test", last_provider_used="test")
        )
    )
    agent.query = AsyncMock(return_value=answer)
    sync = await agent.query_dict("test")
    terminal = json.loads(agent._build_complete_event(answer))["data"]
    for result in (sync, terminal):
        assert DRAFT not in json.dumps(result)
        assert result["metadata"]["publication_gate"]["publishable"] is False
    assert DRAFT in json.dumps(answer.metadata)
