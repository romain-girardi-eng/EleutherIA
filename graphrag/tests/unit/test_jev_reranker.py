"""Tests for JevRerankerService: grouped scoring, pruning, degradation."""

from __future__ import annotations

import json
from typing import Any

import httpx
import pytest

from eleutheria_graphrag.agents.state import Evidence, EvidenceLayer, EvidenceSource
from eleutheria_graphrag.services.jev_reranker import (
    DEFAULT_MODEL,
    JevRerankerService,
)


def _rows(n: int) -> list[dict[str, Any]]:
    return [
        {
            "passage_id": f"p{i}",
            "author": "Cicero",
            "title": "De fato",
            "canonical_ref": f"De fato {i}",
            "language": "lat",
            "text_content": f"passage {i} " * 50,
        }
        for i in range(n)
    ]


def _service(handler: Any, **kwargs: Any) -> JevRerankerService:
    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    return JevRerankerService(api_key="k", client=client, **kwargs)


def _answers_from_request(request: httpx.Request, prob_of: Any) -> httpx.Response:
    body = json.loads(request.content)
    answers = {
        qid: {"type": "boolean", "probability": prob_of(int(qid[1:]))}
        for qid in body["questions"]
    }
    return httpx.Response(
        200,
        json={
            "answers": answers,
            "providerMetadata": {
                "gateway": {"routing": {"canonicalSlug": "typesafe-ai/jev"}}
            },
        },
    )


async def test_prune_rows_orders_by_probability_and_chunks() -> None:
    calls: list[dict[str, Any]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        calls.append(body)
        assert request.headers["ai-model-id"] == DEFAULT_MODEL
        assert request.headers["Authorization"] == "Bearer k"
        # Probability grows with the global index: the last rows win.
        return _answers_from_request(request, lambda i: i / 100)

    svc = _service(handler, chunk_size=4)
    rows = _rows(10)
    pruned = await svc.prune_rows("fate in Cicero", rows, keep=3)

    assert [r["passage_id"] for r in pruned] == ["p9", "p8", "p7"]
    assert pruned[0]["jev_probability"] == pytest.approx(0.09)
    assert len(calls) == 3  # 4 + 4 + 2 candidates
    assert calls[0]["state"]["research_question"] == "fate in Cicero"
    assert len(calls[0]["state"]["candidates"]) == 4
    assert set(calls[0]["questions"]) == {"c0", "c1", "c2", "c3"}
    assert set(calls[2]["questions"]) == {"c8", "c9"}
    assert "`candidates[1]`" in calls[0]["questions"]["c1"]["instructions"]
    assert svc.last_report["applied"] is True
    assert svc.last_report["model"] == "typesafe-ai/jev"
    assert svc.last_report["scored"] == 10
    assert svc.last_report["calls"] == 3


async def test_prune_rows_truncates_text_and_keeps_metadata() -> None:
    seen: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen.update(json.loads(request.content))
        return _answers_from_request(request, lambda _i: 0.5)

    svc = _service(handler, text_chars=60)
    await svc.prune_rows("q", _rows(1), keep=1)
    cand = seen["state"]["candidates"][0]
    assert len(cand["text"]) == 60
    assert cand == {
        "author": "Cicero",
        "work": "De fato",
        "reference": "De fato 0",
        "language": "lat",
        "text": cand["text"],
    }


async def test_prune_rows_falls_back_to_input_order_on_http_error() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(429, json={"error": {"message": "rate limited"}})

    svc = _service(handler)
    rows = _rows(5)
    pruned = await svc.prune_rows("q", rows, keep=2)
    assert pruned == rows[:2]
    assert svc.last_report["applied"] is False
    assert svc.last_report["reason"] == "HTTPStatusError"


async def test_prune_rows_falls_back_on_malformed_answer() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"answers": {}})

    svc = _service(handler)
    rows = _rows(3)
    assert await svc.prune_rows("q", rows, keep=3) == rows
    assert svc.last_report["reason"] == "KeyError"


async def test_prune_rows_without_api_key_is_a_no_op() -> None:
    svc = JevRerankerService(api_key="")
    rows = _rows(3)
    assert await svc.prune_rows("q", rows, keep=2) == rows[:2]
    assert svc.last_report == {"applied": False, "reason": "no_api_key"}
    assert svc.configured is False


async def test_score_rows_empty_input() -> None:
    svc = JevRerankerService(api_key="k")
    assert await svc.score_rows("q", []) == []


async def test_rerank_keeps_reranker_service_contract() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return _answers_from_request(request, lambda i: [0.2, 0.9, 0.6][i])

    svc = _service(handler)
    evidence = [
        Evidence(
            id=f"e{i}",
            label=f"E{i}",
            type="passage",
            layer=EvidenceLayer.PRIMARY,
            source=EvidenceSource.HYBRID_SEARCH,
            text_content=f"text {i}",
            score=0.0,
        )
        for i in range(3)
    ]
    ranked = await svc.rerank("q", evidence, top_k=2, score_threshold=0.5)
    assert [ev.id for ev in ranked] == ["e1", "e2"]
    assert ranked[0].score == pytest.approx(0.9)

    def failing(_request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("down")

    degraded = _service(failing)
    assert await degraded.rerank("q", evidence, top_k=2) == evidence[:2]
