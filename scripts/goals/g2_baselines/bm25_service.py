"""Baseline 1 — BM25/FTS-only retrieval with a thin answer template (no LLM).

Drop-in replacement for the EleutherIA backend *as the eval harness sees it*:
it exposes the same POST contract ``run_eval.py`` calls
(``POST /api/graphrag/query`` with ``{"question", "stream"}``) and returns a
``QueryResponse``-shaped payload whose ``citations[]`` carry the retrieved
passage ids (``type: "passage"``). It also serves ``GET /api/passages/{id}`` so
the faithfulness judge (``ELEUTHERIA_EVAL_JUDGE=1``) can fetch passage text.

There is NO language model here. The "answer" is a deterministic template that
stitches the top-k retrieved passages together — a pure-retrieval floor that
isolates how far BM25 alone gets you on the gold set. Because the answer simply
lists the retrieved passages, citation recall == retrieval recall, which is
exactly the quantity this baseline exists to measure.

Run
---
    .venv/bin/python -m uvicorn \
        scripts.goals.g2_baselines.bm25_service:app --port 8011

    # then point the harness at it:
    .venv/bin/python tests/eval/run_eval.py \
        --base-url http://localhost:8011 \
        --queries data/goals/g2/gold_thesis_1.yaml \
        --output data/goals/g2/run_bm25.json

Tuning via env: ``G2_TOP_K`` (default 8).
"""

from __future__ import annotations

import os
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from scripts.goals.g2_baselines.corpus_index import (
    BM25Index,
    Passage,
    build_index,
)

TOP_K = int(os.environ.get("G2_TOP_K", "8"))

app = FastAPI(title="EleutherIA g2 baseline — BM25/FTS-only")

_index: BM25Index | None = None
_by_id: dict[str, Passage] = {}


def get_index() -> BM25Index:
    global _index
    if _index is None:
        _index = build_index()
        _by_id.clear()
        _by_id.update({p.passage_id: p for p in _index.passages})
    return _index


class QueryRequest(BaseModel):
    question: str
    stream: bool = False


def _snippet(text: str, limit: int = 320) -> str:
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 1] + "…"


def _template_answer(question: str, hits: list[Any]) -> str:
    """Deterministic, no-LLM answer that quotes the retrieved passages."""
    if not hits:
        return (
            f"No corpus passage was retrieved for: {question!r}. "
            "(BM25/FTS-only baseline — no answer can be grounded.)"
        )
    lines = [
        f"Retrieved {len(hits)} passage(s) for: {question}",
        "(BM25/FTS-only baseline — passages are listed verbatim, not synthesised.)",
        "",
    ]
    for n, sp in enumerate(hits, start=1):
        p = sp.passage
        ref = p.canonical_ref or p.cts_urn or p.passage_id
        lines.append(f"[P{n}] {ref} (score={sp.score:.3f})")
        lines.append(f"    {_snippet(p.text_content)}")
    return "\n".join(lines)


@app.post("/api/graphrag/query")
def query(req: QueryRequest) -> dict[str, Any]:
    index = get_index()
    hits = index.search(req.question, k=TOP_K)

    citations = [
        {
            "ref": f"P{n}",
            "type": "passage",
            "id": sp.passage.passage_id,
            "label": sp.passage.canonical_ref or sp.passage.cts_urn,
            "confidence": None,
        }
        for n, sp in enumerate(hits, start=1)
    ]

    return {
        "answer": _template_answer(req.question, hits),
        "question": req.question,
        "confidence": 0.0,
        "citations": citations,
        "sources": [],
        "evidence_map": {},
        "quality_metrics": None,
        "seed_nodes": [],
        "context_nodes": [],
        "passages_used": len(hits),
        "claim_ledger": [],
        "metadata": {"baseline": "bm25_fts_only", "top_k": TOP_K},
    }


@app.get("/api/passages/{passage_id}")
def get_passage(passage_id: str) -> dict[str, Any]:
    get_index()  # ensure _by_id populated
    p = _by_id.get(passage_id)
    if p is None:
        raise HTTPException(status_code=404, detail="Passage not found")
    return {
        "passage_id": p.passage_id,
        "cts_urn": p.cts_urn,
        "canonical_ref": p.canonical_ref,
        "text_content": p.text_content,
        "work_canonical_id": p.work_canonical_id,
    }


@app.get("/api/graphrag/health")
@app.get("/health")
def health() -> dict[str, Any]:
    index = get_index()
    return {"status": "ok", "baseline": "bm25_fts_only", "passages": len(index.passages)}
