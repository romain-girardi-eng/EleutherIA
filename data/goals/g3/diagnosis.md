# G3 — GraphRAG citation-divergence diagnosis

**Date:** 2026-06-15
**Question:** Why does prod (Arm A, `free-will.app/api/graphrag/answer`) return long
answers with ZERO structured citations, while the cited pipeline (Arm B) returns the
same answer WITH structured citations?

## TL;DR — Root cause

There is **no proxy rewrite, no FSM-vs-ReAct split, and (in the current code) no schema
field mismatch**. The citation-building code is correct and *does* populate
`result["citations"]` / `passage_citations` (proven below). The divergence is a
**latency / transport failure**:

- The public non-streaming endpoint **`POST /api/graphrag/answer`** (the path Arm A hit)
  runs the *entire* ReAct + synthesis + citation-verification pipeline **synchronously**
  before returning a single JSON body. For a fresh (uncached) scholarly query this takes
  **> 360 s** end-to-end.
- Everything in the public path is behind **Cloudflare**, which severs any request that
  produces no response bytes within ~100 s → **HTTP 524**.
- So the response object — which *would* contain the structured `citations` array — is
  never serialized to the client. Arm A's harness recorded `citations: 0` because it
  scored a **timed-out / truncated / older-deploy** response, not because the handler
  emits empty citations.
- The streaming endpoint **`GET /api/graphrag/query/stream`** (what the UI actually uses)
  streams prose live, but the **terminal `complete` SSE event — the only frame that
  carries the structured `citations` / `passage_citations` / `claim_ledger`** — is emitted
  only after the *full* pipeline (including the citation-verifier-v2 audit) finishes. For
  slow queries that event also never arrives before the connection is dropped.

Arm B ("new system") succeeds because it is a **different, faster invocation** (cached or a
direct in-process/local call that is allowed to run to completion) and therefore reaches
the point where citations are serialized.

## Evidence (actual measurements, 2026-06-15)

### 1. Reproduction — every non-streaming attempt 524s / times out

| Request | Result |
|---|---|
| `POST free-will.app/api/graphrag/query` | **HTTP 000**, 120 s (curl cap) — no body |
| `POST free-will.app/api/graphrag/answer` | **HTTP 000**, 90 s — no body |
| `POST free-will.app/api/graphrag/answer` | **HTTP 524** at 125 s — Cloudflare `524: A timeout occurred` HTML page (saved as `direct_answer.json`, it is the CF error page, not JSON) |
| `POST http://localhost:8015/api/graphrag/answer` (on host, **no Cloudflare**) | **HTTP 000**, did not return within **360 s** — the pipeline itself is the bottleneck, not the proxy |

The localhost:8015 test is decisive: with Cloudflare entirely removed from the path, the
non-streaming `/answer` still does not finish in 6 minutes. The proxy is **not** the cause;
the synchronous pipeline latency is.

### 2. Streaming SSE — prose streams, `complete` event never arrives

`GET free-will.app/api/graphrag/query/stream?...&mode=fast` (and the same against
`free-will.app` directly, HTTP 200) ran 150 s, 300 s, and 280 s. Event histogram
(`prod_stream.sse`, `prod_stream2.sse`, `direct_stream.sse`):

```
status, agent_thinking, tool_start, tool_result, stage_complete,
answer_chunk (150–287×), tokens_used_rollup
complete: 0     <-- the citation-bearing event never fired before timeout
```

Last frame seen on every run: `status … "Rendering grounded answer… (20s)"`. The prose
(`answer_chunk`) streams fine and contains inline `[Source N]` markers, but the structured
`citations` array rides **only** on the terminal `complete` event, which is gated behind
the full citation-verifier-v2 audit and is never reached.

### 3. The citation code IS correct — proven by the answer cache

On the host DB, `free_will.answer_cache` holds a completed entry with **9
passage_citations**:

```
SELECT count(*), max(jsonb_array_length(passage_citations_json)) FROM free_will.answer_cache;
=> 1 | 9
```

So when the pipeline is *allowed to finish* (and the result is cached), it produces
structured citations exactly as designed. A cache hit replays them instantly
(`routes.py` lines 228–330, the `cache_hit` SSE path). The failure is confined to fresh,
uncached, slow queries.

### 4. Path trace — handler identification

- **`/api/graphrag/answer`** (the Arm-A URL) is handled by
  `backend/routes/graphrag_extras.py::graphrag_answer` (lines 157–316), **not** the
  graphrag-package router. It calls `graphrag.query()` →
  `ScholarlyAgent.query_dict()` → `_run_react()` (the **ReAct** path; the FSM is
  `_run_fsm`, not used in prod). It builds `citations.ancient_sources` from
  `result.get("citations", [])` (lines 217–225). **The FSM is not involved.**
- **`/api/graphrag/query/stream`** (the UI path) is
  `graphrag/src/eleutheria_graphrag/api/routes.py::query_stream` (lines 107–624) →
  `graphrag.query_stream()` → `ScholarlyAgent._stream_react()`. Same ReAct pipeline; the
  route maps the agent `complete` event into `citations.ancient_sources` +
  `passage_citations` + `claim_ledger` (lines 389–509).
- Both non-streaming (`query_dict`, scholarly_agent.py:1068–1094) and streaming
  (`_chunk_answer`, scholarly_agent.py:1594–1647) build `citations` identically from
  `answer.citations`, which is populated by `ProgrammaticVerify` →
  `_verify_answer_programmatically` (graph_nodes.py:5816–5842, 4826–4868).
  `_extract_line_refs` (graph_nodes.py:4422–4428) with `REF_RE = r"\[(.*?)\]"` correctly
  parses both `[Source 1]` and `[P9]` style markers, so **marker format is not the bug
  in the current code.**

### 5. Worker proxy ruled out

`free-will.app/api/*` → CF Worker `ancient-free-will-api` → since 2026-06-12 a **minimal
transparent proxy** to `free-will.app` (per the
`eleutheria-prod-supabase` skill, routing chain §2–3). It does not rewrite the JSON body.
`/tmp/fw-proxy` no longer exists on the host (cleaned on reboot; Worker lives on CF edge).
Both proxy and direct-tunnel paths sit behind Cloudflare's ~100 s cap, so both 524.

### 6. The March-13 AB report reflects an OLDER deploy

The archived `arm_a_prod.response_json` (docs/reports/2026-03-13-001902-graphrag-ab-test.json)
has keys `ancientCitations, evidenceChains, ctsUrns, textualGroundings, citationIntegrity,
modernBibliography` and `citations: null`. **None of those keys exist in the current repo
or in the deployed container** (`grep -rln ancientCitations /app` → empty). That report
captured a *legacy* `/answer` handler whose structured data lived under `ancientCitations`,
which the harness — looking for `citations` — scored as 0. The currently deployed
`graphrag_extras.py` returns the new `citations.ancient_sources` shape. So the historical
"0 citations" had **two** contributing causes over time:
  (a) **legacy schema** (old deploy: data under `ancientCitations`, not `citations`), and
  (b) **the still-live latency/524 problem** that prevents any fresh non-streaming
      response — new schema or old — from reaching the client.

## Root cause (precise)

**The structured-citation payload is produced only at the very end of a synchronous
multi-tool pipeline that takes longer than Cloudflare's request timeout, so on the
public path it is never delivered for fresh queries.** Specifically:

1. `POST /api/graphrag/answer` is fully blocking and exceeds ~100 s → CF 524 → client
   gets no body (and thus no `citations`).
2. `GET /api/graphrag/query/stream` streams prose but emits `citations` only on the
   terminal `complete` event, which is gated behind the citation-verifier-v2 audit and
   does not fire before the stream is dropped on slow queries.

It is **not** a worker rewrite, **not** an FSM-vs-ReAct handler split, and — in the
current build — **not** a `[Source N]`-vs-`[PN]` regex mismatch.

## Precise fix location

Primary (transport / ordering — fixes the user-visible symptom):

- **`graphrag/src/eleutheria_graphrag/agents/scholarly_agent.py`**, `_stream_react`
  (lines ~1131–1360). Emit the structured `citations` / `passage_citations` /
  `claim_ledger` to the client **before** the long `verifier_v2` citation audit
  (lines 1347–1352), rather than only inside the final `_chunk_answer` `complete` event
  (lines 1359, 1623–1647). i.e. emit an early "draft complete with citations" event right
  after `ProgrammaticVerify` populates `state.citations`, then stream the verifier
  verdicts as incremental updates. This guarantees citations reach the UI even when the
  audit/connection is cut.

Secondary (non-streaming endpoint — stop pretending it can be synchronous):

- **`backend/routes/graphrag_extras.py`**, `graphrag_answer` (lines 157–316). The blocking
  `POST /answer` cannot complete inside Cloudflare's window. Either (a) deprecate it for
  the UI in favor of the SSE endpoint, or (b) make it cache-first / job-based (return
  `202 + trace_id`, poll), or (c) front it with the answer-cache so only cold queries are
  slow. As-is it will 524 on every uncached query regardless of citation handling.

Latency (reduce the >360 s pipeline so the `complete` event can actually arrive):

- **`graphrag/src/eleutheria_graphrag/agents/graph_nodes.py`** /
  `ScholarlyAgent._run_react` / `_post_loop_quality_phase` — the dominant cost is the
  multi-round tool loop + render + verifier-v2 audit run end-to-end. Bounding tool
  iterations / parallelizing or sampling the verifier audit is what ultimately lets the
  cited `complete` event fire within the transport window.

## Verification that the data layer is sound

`free_will.answer_cache` proves a completed run yields 9 structured `passage_citations`,
and the cache-replay path (`routes.py` 228–330) serves them instantly. Fixing the
emission-ordering + latency is sufficient; no change to the citation-building code
(`_verify_answer_programmatically`, `query_dict`, `_chunk_answer`) is required.
