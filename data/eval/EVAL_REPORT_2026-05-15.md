# Eval Re-Baseline — 2026-05-15 (Wave 7)

Capture run after the Wave 7 perf optimizations were merged (MCP cache,
parallel sub-agent dispatch, Fireworks `prompt_cache_id`, `stage_complete`
SSE event, +15 Romain thesis queries).

## Run config

- Backend: `https://free-will.app`
- Query set: `tests/eval/queries.yaml` (45 queries total — 30 baseline + 15
  `romain_thesis_queries`).
- Limit: 10 queries (q001–q010, concept-author).
- Output: `data/eval/baseline-opencode-deep-2026-05-15.json`.
- Harness: `tests/eval/run_eval.py` (latency p50/p95, entity recall,
  citation count, keyword hit rate).

## Result — production currently broken

**All 10 queries returned HTTP 500 with body `{"detail":"No module named 'rdflib'"}`.**
The the platform-host deployment is missing the `rdflib` import dependency, so
every `/api/graphrag/query` POST 500s before the pipeline ever boots.

| Metric                | Value      |
|-----------------------|------------|
| successes / total     | 0 / 10     |
| error rate            | 100.00 %   |
| entity recall (mean)  | 0.000      |
| entity precision      | 0.000      |
| keyword hit rate      | 0.000      |
| citations / query     | 0.00       |
| latency p50           | n/a (errored before stream) |
| latency p95           | n/a        |

## Comparison to partial Python-native baseline (2026-05-14)

`data/eval/baseline-prod-railway-partial-2026-05-14.txt` (Railway, pre-the platform):
- 16 queries attempted before the harness crashed on `int.lower()` (since
  fixed at run_eval.py:233).
- 5 read-timeouts (q005, q008, q009, q011, q014).
- 11 partial successes:
  - recall mean (successful): ~0.35
  - keyword hit rate (successful): ~0.94
  - latency: **126–179 s per query** (well above the 60 s budget we want).
  - citation count: 4–8 per query.

The the platform deployment regression blocks an apples-to-apples Wave 6 → Wave 7
delta. The harness itself ran cleanly (no crashes, JSON written), so the
re-baseline can be re-captured the moment the `rdflib` dependency is
restored on the the platform host.

## Failure modes observed

1. **`No module named 'rdflib'`** — the platform deployment missing dep. Likely a
   `uv pip install` step skipped or a stale image. Re-deploy with
   `eleutheria-graphrag[api]` to pull `rdflib` (used by KG ontology
   inspection). **P0 — blocker for any further eval.**
2. **Read-timeouts (carry-over from 2026-05-14)** — five of the 16
   Python-native queries timed out at 180 s. Wave 7 optimisations (parallel
   sub-agents + MCP cache) target exactly this — the eval re-baseline once
   prod is restored should show a measurable p95 drop.

## Wave 7 mitigations now live (code-only — pending deploy)

1. **MCP per-session LRU cache** (`mcp_server/cache.py`) — 200 entries,
   30 min TTL, keyed `(session_id, tool, args_hash)`. Wraps every tool in
   `mcp_server/tools/{kg,read,search}.py`. Local tests: 10/10 pass; mcp
   suite 20/20 pass.
2. **Parallel sub-agent dispatch** (`.opencode/agent/scholar-orchestrator.md`)
   — explicit "DISPATCH IN PARALLEL (do not await between)" rubric for the
   concept-mapper / source-finder / doxographical-mapper trio. Expected
   ~40 % latency cut on exploration phase.
3. **Fireworks `prompt_cache_id`** (`graphrag/.../llm_service.py`) — keyed
   on agent identity, version-bumpable via
   `ELEUTHERIA_PROMPT_CACHE_VERSION`. 7/7 new unit tests pass; 52/52 in
   the full LLMService suite remain green. Expected ~30 % Fireworks bill
   reduction on multi-query sessions.
4. **`stage_complete` SSE event** (`sse_emitter.py`,
   `scholarly_agent._stream_react`, `agent-events.ts`,
   `useResearchStream.ts`) — emits classify / agent_loop / synthesis /
   verify durations. Frontend reducer accumulates them; AgentTrace can
   render a stacked bar in a follow-up polish pass.

## Next steps

1. the platform host: fix the `rdflib` ImportError (re-install deps or rebuild
   image). Re-run `tests/eval/run_eval.py --limit 10` and replace this
   report's empty numbers with real ones.
2. Once captured, run the full 30-baseline + 15 Romain queries and save
   to `data/eval/romain_thesis_queries_baseline.json`.
3. Compare back-to-back via `run_eval.py --compare
   baseline-prod-railway-partial-2026-05-14.txt
   baseline-opencode-deep-2026-05-15.json` (the partial txt file would
   need to be re-captured as JSON for the comparator — small follow-up).
