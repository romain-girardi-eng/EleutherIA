# G3 — Fix the Production Pipeline Divergence

**Objective:** Ensure `free-will.app` users hit the **verified, cited** GraphRAG pipeline, not an older
0-citation path.

**Why (from analysis):** Every AB-test report shows **Arm A (production, `free-will.app/api/graphrag/answer` via the
CF Worker proxy) returns long, polished, but 0 structured citations** — `[Source N]` markers that don't resolve. The new
cited/verified pipeline (Arm B) is a *different* path. Per project memory the FSM has been broken since the
Railway→self-host migration, and prod + the good pipeline have diverged. Latency is also volatile (Origen deep query
143s) flirting with the CF ~100s idle cutoff.

**Deliverables (artifacts under `data/goals/g3/`):**
1. **Root-cause report** — trace the exact request path `free-will.app/api/graphrag/*` → CF Worker → host API → which
   handler, and identify where citations are dropped (worker proxy? FSM vs ReAct route? response schema mismatch?).
2. **Fix** — route the public endpoint to the verified ReAct scholarly-agent path (the one that produces verified
   citations); confirm streaming (SSE) is what the UI consumes (memory: SSE healthy, non-streaming POST 524s at CF).
3. **Latency guard** — verify the heartbeat machinery keeps deep queries under the CF cutoff; add a synthesis quality
   floor so answers don't silently collapse (the Origen 1-paragraph case).
4. **Smoke test** — a prod assertion: a canonical query returns ≥N structured, verified citations.

**First increment:** Diagnose — reproduce the 0-citation prod response, diff the request path vs the local cited
pipeline, pinpoint where citations are lost.

**Success criteria:** A live query on `free-will.app` returns structured, adversarially-verified citations; a smoke
test enforces it; latency stays under the CF idle cutoff.

**Dynamic workflow design:** Phase 1 (diagnosis): agent traces the routing chain (CF Worker → `eleutheria-api`) and the
two pipeline paths in `graphrag/`. Phase 2 (fix + verify): apply the routing/handler fix, redeploy, assert citations live.
Smaller scope, can run parallel to G1/G2.
