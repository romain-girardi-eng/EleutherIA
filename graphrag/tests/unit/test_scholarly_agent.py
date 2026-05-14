"""Integration tests for the long-context ScholarlyAgent."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from eleutheria_graphrag.agents.dependencies import Deps
from eleutheria_graphrag.agents.scholarly_agent import ScholarlyAgent
from eleutheria_graphrag.agents.state import (
    ClaimLedgerItem,
    ClaimStatus,
    ScholarlyAnswer,
)


def _llm_side_effect():
    async def _generate(prompt: str, **kwargs):  # noqa: ARG001
        if "Classify the following question" in prompt:
            return '{"query_type": "global_abstract", "confidence": 0.9, "reason": "broad doctrinal question", "complexity": "medium"}'
        if "You are framing a scholarly search query" in prompt:
            return '{"expanded_query": "Stoic fate heimarmene", "greek_terms": [], "latin_terms": [], "philosophers": ["Chrysippus"], "concepts": ["fate"], "schools": ["Stoicism"], "periods": ["Hellenistic"]}'
        if "opening a research notebook" in prompt:
            return '{"question_frame": "Stoic doctrine of fate", "sub_questions": ["What is heimarmene?"], "competing_hypotheses": [], "open_questions": []}'
        if "Assess whether the current evidence bundle set is sufficient" in prompt:
            return '{"score": 0.8, "sufficient": true, "reason": "enough coverage"}'
        if "Build a claim ledger" in prompt:
            return '{"claims": [{"claim": "Stoic fate is a chain of causes.", "evidence_ids": ["work-1::p1"], "quote_original": "Fate is a chain of causes.", "quote_translation": null, "support_type": "passage", "confidence": 0.9, "status": "supported"}]}'
        if "Render a grounded scholarly answer" in prompt:
            return "- Stoic fate is described as a chain of causes [P1]"
        return "[]"

    return _generate


class _FakeStrategy:
    """Strategy double — yields fixed seeds without touching the DB."""

    def __init__(self, seeds: list[str], anchors: list[str]) -> None:
        self._seeds = seeds
        self._anchors = anchors

    async def discover_seeds(self, queries, deps, node_limit=100):  # noqa: ARG002
        return list(self._seeds), list(self._anchors)


def _make_deps() -> Deps:
    llm = AsyncMock()
    llm.generate = AsyncMock(side_effect=_llm_side_effect())
    llm.last_model_used = "gemini-test"
    llm.last_provider_used = "gemini"

    db = AsyncMock()
    db.fetch = AsyncMock(
        return_value=[
            {
                "passage_id": "p1",
                "work_id": "work-1",
                "text_content": "Fate is a chain of causes.",
                "canonical_ref": "1.1",
                "sequence_number": 1,
                "title": "De Fato",
                "author": "Cicero",
                "language": "lat",
                "confidence": 0.9,
            }
        ]
    )

    return Deps(
        db=db,
        llm=llm,
        node_lookup={
            "chrysippus": {
                "id": "chrysippus",
                "label": "Chrysippus",
                "type": "Person",
                "description": "Stoic philosopher associated with fate.",
                "period": "Hellenistic",
                "school": "Stoicism",
                "role": None,
            }
        },
        outgoing_edges={},
        incoming_edges={},
        retrieval_strategy=_FakeStrategy(seeds=["chrysippus"], anchors=["chrysippus"]),
    )


class TestScholarlyAgent:
    @pytest.mark.asyncio
    async def test_query_returns_grounded_answer(self):
        deps = _make_deps()
        agent = ScholarlyAgent(deps)

        answer = await agent.query(
            "What did the Stoics believe about fate?", agent_mode="fsm"
        )

        assert "fate" in answer.answer.lower()
        assert answer.citations[0].ref == "P1"
        assert answer.quality_badge in {"High", "Medium", "Low"}

    @pytest.mark.asyncio
    async def test_query_dict_includes_new_metadata(self):
        deps = _make_deps()
        agent = ScholarlyAgent(deps)

        result = await agent.query_dict(
            "What did the Stoics believe about fate?", agent_mode="fsm"
        )

        assert result["metadata"]["grounding_policy"] == "mixed_evidence"
        assert result["metadata"]["claim_ledger_size"] >= 1

    @pytest.mark.asyncio
    async def test_query_stream_emits_answer_and_complete_payload(self):
        deps = _make_deps()
        agent = ScholarlyAgent(deps)
        chunks: list[str] = []

        async for chunk in agent.query_stream(
            "What did the Stoics believe about fate?", agent_mode="fsm"
        ):
            chunks.append(chunk)

        text = "".join(chunks)
        assert "fate" in text.lower()
        assert '"type": "complete"' in text


def _make_simple_deps():
    deps = MagicMock()
    deps.llm.last_model_used = "gemini-2.5-flash"
    deps.llm.last_provider_used = "google"
    return deps


@pytest.mark.asyncio
async def test_query_stream_includes_claim_ledger_size():
    """query_stream complete payload must include claim_ledger_size."""
    deps = _make_simple_deps()
    agent = ScholarlyAgent(deps)

    answer = ScholarlyAnswer(
        answer="Stoic fate [P1].",
        question="What is fate?",
        claim_ledger=[
            ClaimLedgerItem(
                claim="Stoic fate is determinism.",
                evidence_ids=["P1"],
                support_type="passage",
                confidence=0.9,
                status=ClaimStatus.SUPPORTED,
            )
        ],
    )
    with patch.object(agent, "query", new=AsyncMock(return_value=answer)):
        chunks = [
            chunk
            async for chunk in agent.query_stream("What is fate?", agent_mode="fsm")
        ]

    complete_chunk = next(c for c in chunks if c.startswith("{"))
    data = json.loads(complete_chunk)
    assert data["type"] == "complete"
    assert data["data"]["metadata"]["claim_ledger_size"] == 1
