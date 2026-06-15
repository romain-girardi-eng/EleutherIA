"""Baseline 2 — vanilla LLM + top-k-FTS-context RAG (no agent, no KG).

Same POST contract the eval harness uses (``POST /api/graphrag/query`` ->
``QueryResponse`` shape; ``GET /api/passages/{id}`` for the judge). The pipeline
is the textbook RAG floor:

    1. BM25/FTS retrieve top-k passages over data/corpus (corpus_index).
    2. Build a single prompt: question + the k passages, each tagged ``[P#]``.
    3. ONE LLM call (provider-pluggable, see providers.py) — no tools, no graph,
       no re-retrieval, no verification loop.
    4. Parse the ``[P#]`` markers the model actually used back into passage
       citations so the harness scores citation P/R/F1 on what was *cited*,
       not merely what was retrieved.

The LLM provider is pluggable and the default (``extractive``) needs NO API key,
so this file imports and runs on a key-less machine. Point it at a real model by
setting ``G2_LLM_PROVIDER`` (+ the provider's key) — see baselines_README.md.

Run
---
    G2_LLM_PROVIDER=openrouter OPENROUTER_API_KEY=... \
    .venv/bin/python -m uvicorn \
        scripts.goals.g2_baselines.vanilla_rag_service:app --port 8012

    .venv/bin/python tests/eval/run_eval.py \
        --base-url http://localhost:8012 \
        --queries data/goals/g2/gold_thesis_1.yaml \
        --output data/goals/g2/run_vanilla.json
"""

from __future__ import annotations

import os
import re
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from scripts.goals.g2_baselines.corpus_index import (
    BM25Index,
    Passage,
    ScoredPassage,
    build_index,
)
from scripts.goals.g2_baselines.providers import Provider, build_provider

TOP_K = int(os.environ.get("G2_TOP_K", "8"))

SYSTEM_PROMPT = (
    "You are a scholar of ancient philosophy answering a research question using "
    "ONLY the numbered context passages provided. Cite every claim with the "
    "passage marker in square brackets, e.g. [P2]. If the passages do not answer "
    "the question, say so. Never invent ancient Greek or Latin text. Quote "
    "originals verbatim from the context when you quote at all."
)

app = FastAPI(title="EleutherIA g2 baseline — vanilla LLM + FTS RAG")

_index: BM25Index | None = None
_provider: Provider | None = None
_by_id: dict[str, Passage] = {}

_MARKER_RE = re.compile(r"\[P(\d+)\]")


def get_index() -> BM25Index:
    global _index
    if _index is None:
        _index = build_index()
        _by_id.clear()
        _by_id.update({p.passage_id: p for p in _index.passages})
    return _index


def get_provider() -> Provider:
    global _provider
    if _provider is None:
        _provider = build_provider()
    return _provider


class QueryRequest(BaseModel):
    question: str
    stream: bool = False


def _build_user_prompt(question: str, hits: list[ScoredPassage]) -> str:
    blocks = ["QUESTION:", question, "", "CONTEXT PASSAGES:"]
    for n, sp in enumerate(hits, start=1):
        p = sp.passage
        ref = p.canonical_ref or p.cts_urn or p.passage_id
        blocks.append(f"[P{n}] {ref}")
        blocks.append(p.text_content)
        blocks.append("")
    blocks.append(
        "Answer the question using only these passages, citing markers like [P1]."
    )
    return "\n".join(blocks)


def _cited_markers(answer: str, n_hits: int) -> set[int]:
    used = {int(m) for m in _MARKER_RE.findall(answer)}
    return {i for i in used if 1 <= i <= n_hits}


@app.post("/api/graphrag/query")
def query(req: QueryRequest) -> dict[str, Any]:
    index = get_index()
    provider = get_provider()
    hits = index.search(req.question, k=TOP_K)

    user_prompt = _build_user_prompt(req.question, hits)
    answer = provider.generate(SYSTEM_PROMPT, user_prompt)

    used = _cited_markers(answer, len(hits))
    # If the model cited nothing parseable (or the extractive provider echoed
    # everything), fall back to crediting all retrieved passages so the run is
    # still scored against retrieval — flagged in metadata for transparency.
    cited_all_fallback = not used
    marker_set = used if used else set(range(1, len(hits) + 1))

    citations = [
        {
            "ref": f"P{n}",
            "type": "passage",
            "id": sp.passage.passage_id,
            "label": sp.passage.canonical_ref or sp.passage.cts_urn,
            "confidence": None,
        }
        for n, sp in enumerate(hits, start=1)
        if n in marker_set
    ]

    return {
        "answer": answer,
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
        "metadata": {
            "baseline": "vanilla_fts_rag",
            "provider": provider.name,
            "top_k": TOP_K,
            "retrieved_passages": [sp.passage.passage_id for sp in hits],
            "cited_all_fallback": cited_all_fallback,
        },
    }


@app.get("/api/passages/{passage_id}")
def get_passage(passage_id: str) -> dict[str, Any]:
    get_index()
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
    return {
        "status": "ok",
        "baseline": "vanilla_fts_rag",
        "provider": get_provider().name,
        "passages": len(index.passages),
    }
