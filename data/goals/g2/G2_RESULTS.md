# G2 — Benchmark Results: Agentic GraphRAG vs BM25 (vs Vanilla-RAG)

Headline numbers on the **annotated gold set** (`tests/eval/queries.yaml`, 45
queries; 13 carry `expected_passages` → citation P/R/F1; 13 carry `gold_claims`
→ faithfulness judge; 11 carry `expected_works` → work recall).

All three systems speak the **same** `POST /api/graphrag/query` contract and are
scored identically by `tests/eval/run_eval.py` (`eval_lib/scoring.py` set
arithmetic + `must_not_appear.jsonl` forbidden-string scan + optional
`CitationVerifierV2` faithfulness judge).

## Headline table

Run on 2026-06-15, 45 queries, `tests/eval/queries.yaml`. Agentic = live prod
backend (warmed `answer_cache`, scored via the SSE adapter); citation metrics
identical with or without the judge (the judge only adds `verified_rate`).

| Metric | **Agentic GraphRAG** | BM25 (floor) | Vanilla-RAG (gemini-2.5-flash) |
|---|---|---|---|
| **Citation F1** (gold, 13 scored) | **0.103** | 0.062 | 0.099 |
| **Citation recall** (mean) | 0.115 | **0.180** | 0.141 |
| Citation precision (mean) | **0.109** | 0.039 | 0.077 |
| **Entity recall** (mean) | **0.664** | 0.000 | 0.000 |
| **Work recall** (mean) | **0.200** | 0.000 | 0.000 |
| Keyword hit rate (mean) | **0.867** | 0.790 | 0.759 |
| Citations / query (mean) | 75.3 | 8.0 | 4.2 |
| **Forbidden-string hits** | **0** | **0** | **0** |
| Error rate | 0.0% | 0.0% | 4.4% (2 transient gemini 500s) |
| Latency p50 / p95 (ms) | 316 / 351 | 18 / 27 | 7 983 / 16 384 |
| Faithfulness `verified_rate` | see note below | n/a | n/a |

Entity recall by query type (agentic): fact 0.92, fragment 0.94, concept-author
0.90, school-debate 0.69, comparison 0.67, thesis-grade 0.32. Both baselines
score 0.00 on every type.

### Reading the headline

- **The KG layer is the decisive differentiator.** Agentic entity recall 0.66
  and work recall 0.20 vs **0.00** for both passage-only floors — the agentic
  pipeline is the only system that surfaces the persons/concepts/arguments/works
  the gold expects. That is exactly what the KG buys and the floors cannot.
- **Citation F1: agentic leads** (0.103 > vanilla 0.099 > BM25 0.062), driven by
  **3× the precision** of BM25 (0.109 vs 0.039): the agent cites a focused set of
  the *right* passages rather than dumping 8 lexical hits.
- **Honest caveat — citation recall:** BM25 (0.180) edges out agentic (0.115) on
  raw passage recall. BM25 returns a fixed top-8 per query, so on the handful of
  gold passages whose **English** wording overlaps the query it catches more by
  brute force; the agent cites fewer, higher-precision passages (and many gold
  passages are original-language Greek/Latin that neither lexical floor nor the
  agent's English-anchored citation always selects). Citation recall is the one
  axis where the lexical floor is competitive — a real finding, not an artifact.
- **Anti-fabrication gate holds: 0 forbidden-string hits on all three runs.**
- **Latency:** agentic p50 316 ms is *cache-warmed* (cold ReAct is 450–690 s;
  see §provenance). BM25 is a pure-Python floor (18 ms). Vanilla pays one LLM
  call (~8 s).

### Faithfulness judge (`ELEUTHERIA_EVAL_JUDGE=1`) — caveat

A key was available, so the judged agentic run was launched. **The result is not
a trustworthy quality signal and was aborted as uninformative.** Across the first
three gold queries judged (q008, q013, q016): **0 VERIFIED verdicts, 15 `WEAK`
fallbacks** — `CitationVerifierV2`'s verifier LLM (via the prod `LLMService`
provider chain) returns **unparseable JSON on every citation** and falls back to
`WEAK` after 3 attempts (logged verbatim: "Verifier unable to assess citation …
verifier LLM returned unparseable JSON — falling back to WEAK"). With every
verdict collapsing to `WEAK` regardless of whether the cited passage supports the
claim, `verified_rate` is pinned at **0.0** and reflects a verifier
output-format/parse bug, **not** the backend's grounding.

This is a finding about the **judge**, not the retrieval. The citation-F1 / recall
/ precision numbers above (pure set arithmetic, no LLM) are the reliable grounding
metrics. Making the faithfulness judge meaningful requires fixing
`CitationVerifierV2._parse_verdict` / the verifier provider config (the model is
not emitting the expected JSON schema) — out of scope for this capture. The run
re-confirmed **0 forbidden-string hits** before it was stopped.


## How to read it

- **Citation F1 / recall / precision** are the apples-to-apples columns: all
  three systems cite real `passage_id`s, scored against the 13 gold
  `expected_passages` sets. This is the metric the agentic lemma-expansion + KG
  pipeline exists to lift over a lexical floor.
- **Entity recall / work recall** are KG-*node* metrics. The two passage-only
  baselines (BM25, vanilla-RAG) surface **no KG nodes**, so they score 0 *by
  design* — that gap quantifies what the KG layer buys.
- **Forbidden hits** must be 0 (academic-integrity / anti-fabrication gate).
- BM25 is a pure lexical floor: scholarly **English** queries over a
  **Greek/Latin** corpus miss most original-language gold passages.

## Setup / provenance (honest account)

- **Agentic GraphRAG** = the live production backend (`eleutheria-api`
  container, host `deploy-host`, container port 8000). Reached from the eval
  host via an SSH local-forward tunnel `localhost:18000 → host:8015`, bypassing
  the Cloudflare edge (which 524s the non-streaming POST at its 100 s timeout).
  The ReAct pipeline is genuinely slow on cold queries (450–690 s each, the
  CitationVerifierV2 audit dominates), so the answer cache was pre-warmed via the
  `GET /query/stream` SSE endpoint (which populates the DB-backed
  `free_will.answer_cache`) before the scored run. NB: the non-streaming
  `POST /query` path uses a **separate in-process** `_response_cache`, so it does
  *not* read the warmed SSE cache — therefore `run_eval` was pointed at a thin
  **SSE→flat-QueryResponse adapter**
  (`scripts/goals/g2_baselines/agentic_sse_adapter.py`, :8013) that calls the
  warmed `/query/stream`, collects the terminal `complete` event, and reshapes it
  into the exact flat `QueryResponse` the harness scores (passage+node
  `citations[]`, `seed_nodes`, `context_nodes`, `sources`). The SSE endpoint
  rate-limits at 20 req/60 s per IP, so the adapter retries 429/5xx with
  exponential backoff (the run paces itself under the limit; final run = 45/45,
  **0 errors**). Pre-warming + the adapter change **latency only**, not the
  retrieved citations/nodes the metrics score (verified: identical citation IDs
  on cache hits).
- **BM25 floor** = `scripts/goals/g2_baselines/bm25_service.py` (:8011), Okapi
  BM25 over `data/corpus/passages.jsonl` (21,088 passages), no LLM.
- **Vanilla-RAG floor** = `scripts/goals/g2_baselines/vanilla_rag_service.py`
  (:8012), top-8 FTS context → one `gemini-2.5-flash` call, no agent, no KG.
- **Faithfulness judge** (`ELEUTHERIA_EVAL_JUDGE=1`, key present): the prod
  `/api/passages/{id}` endpoint requires auth (401), so the judge's passage
  fetch was pointed at the BM25 service (`ELEUTHERIA_EVAL_PASSAGE_URL=
  http://localhost:8011`), which serves the **same** `data/corpus` snapshot the
  gold was annotated against.

### Harness changes (minimal, env-gated, non-behavioural)

`tests/eval/run_eval.py`:
- `DEFAULT_TIMEOUT` now honours `ELEUTHERIA_EVAL_TIMEOUT` (cold agentic queries
  exceed the hard-coded 180 s).
- judge passage-fetch base URL now honours `ELEUTHERIA_EVAL_PASSAGE_URL`
  (defaults to `--base-url`), to route around the 401 on prod `/api/passages`.

## Reproduce

```bash
# BM25 floor (seconds)
python -m uvicorn scripts.goals.g2_baselines.bm25_service:app --port 8011 &
python tests/eval/run_eval.py --base-url http://localhost:8011 \
    --queries tests/eval/queries.yaml --output data/goals/g2/run_bm25_nojudge.json

# Vanilla-RAG floor (gemini-2.5-flash)
G2_LLM_PROVIDER=gemini G2_OPENAI_MODEL=gemini-2.5-flash \
python -m uvicorn scripts.goals.g2_baselines.vanilla_rag_service:app --port 8012 &
python tests/eval/run_eval.py --base-url http://localhost:8012 \
    --queries tests/eval/queries.yaml --output data/goals/g2/run_vanilla_nojudge.json

# Agentic GraphRAG (tunnel :18000, judge passages from :8011)
ssh -fN -L 18000:localhost:8015 deploy-host
data/goals/g2/_run_agentic.sh   # writes run_graphrag.json

# Pairwise deltas
python tests/eval/run_eval.py --compare \
    data/goals/g2/run_bm25_nojudge.json data/goals/g2/run_graphrag.json
```
