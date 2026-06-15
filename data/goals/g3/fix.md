# G3 — Fix: deliver adversarially-verified structured citations on the public SSE path

**Date:** 2026-06-15
**Builds on:** `data/goals/g3/diagnosis.md`

## What was wrong (one line)

Structured citations rode **only** on the terminal `complete` SSE event, which is
gated behind the 10–60 s adversarial verifier-v2 audit; on slow doctoral queries that
event never fired before Cloudflare's ~100 s idle cut, so the public UI showed prose
with **zero clickable citations** even though the citation data layer was correct.

## The fix (transport / event-ordering — APPLIED)

Emit the structured-citation payload **as soon as it exists** — right after
`ProgrammaticVerify` populates `answer.citations` and the deterministic passage
injection runs — as a new **`citations_preview`** SSE frame, *before* the long
verifier-v2 audit. The audit verdicts still stream afterwards as `citation_verified`
events, and the authoritative `complete` frame still supersedes the preview at the end.
This guarantees verified, clickable citations reach the UI even if the audit or the
Cloudflare connection is cut.

The citations in the preview are **already adversarially grounded**: `ProgrammaticVerify`
→ `_verify_answer_programmatically` only admits citations whose `[ref]` markers resolve
to real retrieved evidence (the ref-resolution gate). Verifier-v2 then *annotates* each
with a pass/weak/reject verdict (streamed live as `citation_verified` + folded into the
final `complete`). So the preview is "verified-resolvable"; the `complete` is
"verified-resolvable + audited".

### Files changed (staged in the working tree; patch: `data/goals/g3/fix.patch`)

1. **`graphrag/src/eleutheria_graphrag/agents/scholarly_agent.py`**
   - `_stream_react`: after Phase 4 (text verify) and before Phase 5 (verifier-v2),
     `yield self._build_complete_event(answer, event_type="citations_preview")`.
   - Refactored `_chunk_answer`'s payload builder into a shared
     **`_build_complete_event(answer, event_type=...)`** helper so the preview and the
     terminal `complete` emit an **identical** structured payload (no schema drift).

2. **`graphrag/src/eleutheria_graphrag/api/routes.py`** (`query_stream`)
   - The `if event_type == "complete"` branch now also accepts `"citations_preview"`
     and runs the **same** agent→frontend transform (`citations.ancient_sources`,
     `passage_citations`, `claim_ledger`, `sources`, …).
   - The preview is **non-terminal**: it does **not** set `complete_sent`, does **not**
     emit a second `cost_summary`, does **not** write the answer cache, and does **not**
     finalize the trace (`if is_preview: continue`). Only the real `complete` does those.

3. **`frontend/src/pages/GraphRAGPage/index.tsx`**
   - New `case 'citations_preview'`: adopts the frame as the working `finalResponse`
     (same as `complete`) so a connection drop after the preview still renders structured
     citations. The authoritative `complete` overwrites it on arrival.

4. **`frontend/src/types/index.ts`** — add `'citations_preview'` to the
   `GraphRAGStreamEvent.type` union (TS strict).

5. **`graphrag/tests/unit/test_streaming_render.py`** — contract smoke test (below).

### Why this is low-risk

- Additive: a new optional SSE frame type. Old clients ignore unknown `type`s
  (`useResearchStream`'s `isAgentEvent` returns `false` → no-op; `GraphRAGPage`'s
  `switch` falls through).
- The preview and `complete` share one serializer, so they cannot diverge.
- Heartbeats (`_await_with_heartbeat`, `_stream_render`) already keep the wire warm
  inside the ~100 s window; the preview adds the *citation* payload to that early traffic.
- No change to `_verify_answer_programmatically`, `query_dict`, or `_chunk_answer`'s
  data — the citation-building code was already correct (diagnosis §3, §4).

### Applied? Yes — code + frontend staged in the working tree.

Verification run locally:

```
.venv/bin/python -m pytest graphrag/tests/unit/test_streaming_render.py -q   # 7 passed
.venv/bin/python -m pytest graphrag/tests/unit/test_query_stream_mode_validation.py \
                          graphrag/tests/unit/test_scholarly_agent.py -q      # 13 passed
cd frontend && npx tsc --noEmit                                              # 0 errors
```

## Deploy steps (required to make it live — host rebuild, NOT a code change)

The fix is server-side Python in the `eleutheria-api` container plus a static-SPA
rebuild. The CF Worker (`ancient-free-will-api`) is a transparent pass-through and needs
**no** change. Steps:

1. Merge to `main` (the host deploy pulls `main`).
2. Rebuild + restart the API container on the the platform host:
   ```bash
   make deploy        # ssh's to the host, git pull main, docker compose up -d --build \
                      #   --no-deps eleutheria-api eleutheria-worker
   make prod-status   # confirm eleutheria-api healthy on host port 8015
   ```
   (Equivalent manual path per the `eleutheria-prod-supabase` skill:
   `ssh deploy-host` → `cd <PROD_DIR> && git pull` → compose up `--build eleutheria-api`.)
3. Rebuild + redeploy the frontend SPA (the `citations_preview` consumer) the usual way
   for the nginx static bundle.

No host config, no env var, no CF Worker redeploy needed.

## Secondary endpoint (`POST /api/graphrag/answer`) — NOT applied, deliberate

`backend/routes/graphrag_extras.py::graphrag_answer` is fully synchronous and 524s on
every uncached query (diagnosis §1). The UI does **not** use it — it uses the SSE
`query/stream` path fixed above. Recommended follow-up (out of scope for this low-risk
change): make `/answer` **cache-first** (serve from `free_will.answer_cache` when warm)
and return `202 + trace_id` for cold queries, or deprecate it for the UI. Left as a
documented next step rather than reworked here.

## Smoke test

### 1. Contract test (CI / offline — no network)

`graphrag/tests/unit/test_streaming_render.py::test_citations_preview_event_carries_structured_citations`
asserts the `citations_preview` frame carries `>= 3` structured `{ref,type,id,label}`
citations and is byte-identical in payload to the `complete` frame.

```bash
.venv/bin/python -m pytest \
  "graphrag/tests/unit/test_streaming_render.py::test_citations_preview_event_carries_structured_citations" -q
```

### 2. End-to-end smoke (against a running deploy)

`data/goals/g3/smoke_citations.py` opens the public SSE stream for a canonical query and
asserts a `citations_preview` (or `complete`) frame delivers `>= N` **structured**
citations (clickable tuples, not bare label strings):

```bash
# against prod (after deploy):
python3 data/goals/g3/smoke_citations.py \
  --base https://free-will.app \
  --question "What did Chrysippus argue about fate and moral responsibility?" \
  --min-citations 3 --timeout 150

# bypass Cloudflare (host) or local dev:
python3 data/goals/g3/smoke_citations.py --base http://localhost:8000
```

Exit 0 = PASS (≥ N structured citations seen on an SSE frame *before* the terminal
`complete`, proving the preview delivers them inside the transport window).
The reference answer-cache entry holds 9 `passage_citations`, so `--min-citations 3` is a
conservative floor.
```
