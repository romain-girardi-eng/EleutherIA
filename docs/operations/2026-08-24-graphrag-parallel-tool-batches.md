# GraphRAG same-turn tool parallelism

**Date:** 2026-08-24  
**Status:** implemented and regression-tested; live model latency benchmark open

## Finding

The native tool-calling model can request several tools in one assistant turn.
Those calls cannot depend on one another because the model has not observed any
of their results, yet the runtime executed them sequentially. Historical
profiling already identified the agent loop as a dominant cold-query stage;
sequential same-turn I/O added avoidable wall time without adding evidence.

## Contract

`NativeAgentLoop` now:

1. parses and validates the complete model-emitted batch;
2. reserves the existing total-tool-call budget in original order;
3. emits the existing start events;
4. executes valid, in-budget calls concurrently under
   `MAX_PARALLEL_TOOL_CALLS` (default 4, clamped 1–16);
5. commits evidence, result events, journal entries and tool messages strictly
   in the model's original order;
6. returns a matched no-op tool response for every call rejected by the total
   budget, preserving the provider protocol;
7. records bounded `tool_batch_metrics` on the run metadata: requested,
   executed, concurrency limit, batch wall time, summed sequential tool time
   and observed overlap.

No retrieval result, context cap, tool-call cap, synthesis budget, verifier,
publication verdict or cache-admission rule was loosened.

## Verification

- A regression test uses a deliberately slow first tool and fast second tool.
  It proves simultaneous execution (`max_active == 2`) and original-order tool
  messages (`slow`, then `fast`) despite reverse completion order.
- Existing budget regression still proves a five-call total ceiling when the
  model emits four calls per turn.
- Invalid JSON and unknown tools preserve their prior recovery behavior.
- Machine translations remain fail-closed under the central citability policy;
  two stale tests were corrected to assert absence rather than exposure.
- Targeted native/ReAct/read-passage tests: PASS.
- Full GraphRAG suite: **1,441 passed, 1 skipped**.
- Ruff on changed GraphRAG code/tests: PASS.

This establishes semantic equivalence plus real I/O overlap. It does not claim
an end-to-end latency improvement until the same frozen live query/model/source
release is run before and after with stage, token and cost traces.

