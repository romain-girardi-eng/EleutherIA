"""SSE→flat-QueryResponse adapter for the agentic GraphRAG backend.

WHY: ``tests/eval/run_eval.py`` POSTs ``/api/graphrag/query`` (non-streaming),
which on the prod backend runs ``GraphRAGService.query()`` — a path whose
in-process ``_response_cache`` is SEPARATE from the DB-backed ``answer_cache``
that the SSE ``/query/stream`` endpoint reads/writes. We pre-warmed the SSE
``answer_cache`` (so cold ReAct latency doesn't blow the eval), therefore the
eval must go through the SSE path to benefit from that warm cache.

This adapter exposes the SAME contract run_eval expects:
  - ``POST /api/graphrag/query`` -> calls the upstream SSE ``/query/stream``,
    collects the terminal ``complete`` (or earlier ``citations_preview``) event,
    and reshapes its ``data`` into the flat ``QueryResponse`` shape run_eval's
    ``extract_returned_ids`` / ``extract_predicted_passages`` read:
      citations[] (type passage|node), seed_nodes[], context_nodes[], sources[].
  - ``GET /api/passages/{id}`` -> proxied to a passage server (default the BM25
    baseline on :8011) so the faithfulness judge can fetch text_content.

Env:
  G2_UPSTREAM_BASE   upstream agentic API base (default http://localhost:18000)
  G2_PASSAGE_BASE    passage server base for the judge (default http://localhost:8011)
  G2_SSE_TIMEOUT     per-query SSE read timeout seconds (default 800)

Run:
  .venv/bin/python -m uvicorn \
      scripts.goals.g2_baselines.agentic_sse_adapter:app --port 8013
"""

from __future__ import annotations

import json
import os
import time
import urllib.parse
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

UPSTREAM = os.environ.get("G2_UPSTREAM_BASE", "http://localhost:18000").rstrip("/")
PASSAGE_BASE = os.environ.get("G2_PASSAGE_BASE", "http://localhost:8011").rstrip("/")
SSE_TIMEOUT = float(os.environ.get("G2_SSE_TIMEOUT", "800"))

app = FastAPI(title="EleutherIA g2 — agentic SSE adapter")


class QueryRequest(BaseModel):
    question: str
    stream: bool = False


def _reshape(data: dict[str, Any]) -> dict[str, Any]:
    """Map the SSE complete-event `data` to the flat QueryResponse shape."""
    answer = data.get("answer") or ""
    # passage_citations are the structured {ref,id,type,label} tuples; keep them
    # verbatim so run_eval sees type=='passage' ids for citation P/R/F1.
    passage_citations = [c for c in (data.get("passage_citations") or []) if isinstance(c, dict)]

    rp = data.get("reasoning_path") or {}
    starting = [n.get("id") for n in (rp.get("starting_nodes") or []) if isinstance(n, dict) and n.get("id")]
    expanded = [n.get("id") for n in (rp.get("expanded_nodes") or []) if isinstance(n, dict) and n.get("id")]
    sources_in = data.get("sources") or []
    sources = [
        {"node_id": s.get("nodeId"), "node_label": s.get("nodeLabel")}
        for s in sources_in
        if isinstance(s, dict) and s.get("nodeId")
    ]

    # Node-typed citations too: surface seed/expanded node ids as node citations
    # so entity/work recall can score them (run_eval reads citations[].id where
    # type in {None,'node'} plus seed_nodes/context_nodes directly).
    node_citations = [
        {"type": "node", "id": nid}
        for nid in dict.fromkeys(starting + expanded)
    ]

    return {
        "answer": answer,
        "question": data.get("query", ""),
        "confidence": 0.0,
        "citations": passage_citations + node_citations,
        "sources": sources,
        "evidence_map": {},
        "seed_nodes": starting,
        "context_nodes": expanded,
        "passages_used": len(passage_citations),
        "claim_ledger": data.get("claim_ledger") or [],
        "metadata": data.get("metadata") or {},
    }


MAX_RETRIES = int(os.environ.get("G2_SSE_RETRIES", "8"))


def _stream_once(url: str) -> dict[str, Any] | None:
    """One SSE pass; returns the best complete/preview data or raises on HTTP error."""
    best: dict[str, Any] | None = None
    with httpx.Client(timeout=httpx.Timeout(SSE_TIMEOUT, connect=30.0)) as client:
        with client.stream("GET", url) as resp:
            resp.raise_for_status()  # raises HTTPStatusError on 429/5xx
            for line in resp.iter_lines():
                if not line or not line.startswith("data: "):
                    continue
                try:
                    evt = json.loads(line[6:])
                except json.JSONDecodeError:
                    continue
                etype = evt.get("type")
                if etype in ("complete", "citations_preview"):
                    d = evt.get("data") or {}
                    if etype == "complete":
                        return d
                    if best is None:
                        best = d
    return best


@app.post("/api/graphrag/query")
def query(req: QueryRequest) -> dict[str, Any]:
    url = (
        f"{UPSTREAM}/api/graphrag/query/stream?mode=fast&question="
        + urllib.parse.quote(req.question)
    )
    # The upstream SSE endpoint rate-limits (429) under rapid sequential load;
    # retry with exponential backoff so a serial eval doesn't lose queries.
    last_exc: Exception | None = None
    for attempt in range(MAX_RETRIES):
        try:
            best = _stream_once(url)
            if best is not None:
                return _reshape(best)
            last_exc = RuntimeError("no complete/preview event")
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            last_exc = exc
            if status not in (429, 500, 502, 503, 504):
                raise HTTPException(status_code=502, detail=f"upstream {status}") from exc
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
        time.sleep(min(2.0 * (2 ** attempt), 30.0))  # 2,4,8,16,30,30,30,30s

    raise HTTPException(status_code=504, detail=f"upstream exhausted retries: {last_exc}")


@app.get("/api/passages/{passage_id}")
def get_passage(passage_id: str) -> dict[str, Any]:
    try:
        r = httpx.get(f"{PASSAGE_BASE}/api/passages/{passage_id}", timeout=30.0)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    if r.status_code != 200:
        raise HTTPException(status_code=r.status_code, detail="passage not found")
    return r.json()


@app.get("/health")
def health() -> dict[str, Any]:
    return {"status": "ok", "upstream": UPSTREAM, "passage_base": PASSAGE_BASE}
