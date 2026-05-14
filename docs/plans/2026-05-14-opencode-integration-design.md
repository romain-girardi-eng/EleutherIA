# Opencode Integration Design for EleutherIA

**Date:** 2026-05-14
**Author:** Romain Girardi
**Status:** Research / Design

---

## 1. What is sst/opencode?

`sst/opencode` (opencode.ai) is an open-source agent that **writes code in your terminal, IDE, or desktop**. It is explicitly a *coding agent* — the marketing copy targets developers, the built-in agents are `build` / `plan` / `general`, and the workflow assumes a working tree, LSPs, file edits, and shell access. It is not a research/Q&A framework, but the underlying primitives (provider-agnostic LLM, MCP tools, custom agents, headless HTTP server) are general-purpose enough that we *could* repurpose them.

### Architecture

| Aspect | Details |
|---|---|
| **Runtime** | Bun/Node.js (TypeScript, ~57% TS; uses Turbo monorepo + SST infra). Bun is the primary target — custom tools call `Bun.$` for shelling out. |
| **Client/server split** | The TUI is *one of many possible clients*. The actual brain runs as a server you launch via `opencode serve [--port 4096] [--hostname …]`. Clients (TUI, mobile app, IDE plugin) drive it remotely over HTTP. |
| **HTTP API** | REST + OpenAPI 3.1 spec exposed at `/doc`. Covers sessions, messages, files, commands, providers. Auth via HTTP Basic (`OPENCODE_SERVER_PASSWORD` / `OPENCODE_SERVER_USERNAME`). |
| **Streaming** | Yes — the server streams tokens and tool-call events to whichever client drives it. Spec is documented in the OpenAPI schema (sessions/messages endpoints). |
| **Agents** | Configured via `opencode.json`, `.opencode/agents/*.md` (Markdown + frontmatter), or `opencode agent create`. **Primary** agents (top-level personas) and **subagents** (invoked auto, via `@mention`, or via the `Task` tool). Subagents are first-class — a primary can delegate with scoped permissions. |
| **Tool integration** | Three layers: (1) **built-in tools** (read/write file, bash, LSP, etc.), (2) **MCP servers** — local (`{type:"local", command:[…]}`) or remote (`{type:"remote", url:"…"}`), (3) **custom TS/JS tools** in `.opencode/tools/*.ts` using `tool({description, args: zod, async execute(args, ctx) {…}})`. Custom tools run in Bun and may shell out to Python via `Bun.$`. |
| **LLM providers** | Wraps Vercel's **AI SDK** + Models.dev (75+ providers). Custom providers go in `opencode.json` under `provider.<id>` with `npm: "@ai-sdk/openai-compatible"`, `baseURL`, `apiKey: "{env:VAR}"`. So Fireworks/Kimi works as an OpenAI-compatible endpoint. |
| **OpenCode Zen** | Curated hosted gateway (`https://opencode.ai/zen/v1/responses`). `OPENCODE_API_KEY` authenticates against Zen — it is **not** a generic key, it's a billing account. the platform uses it as a fallback alongside `CEREBRAS_API_KEY` / `FIREWORKS_API_KEY`. |
| **Deployment** | `opencode serve` as a long-running process. No official Docker image, but trivially containerised (Bun + the binary). **No multi-tenant model** — one server per user/workspace, isolation is by process. |

### How the platform already uses it

the platform's `private-repo` invokes opencode via **subprocess CLI** (`execute_opencode(...)`) inside Temporal worker activities. The agent is treated as a black-box code generator: stdin = prompt, stdout = generated app code, parse `_APP_RESULT_RE` to find the `preview_url`. The `opencode.json` at the root has empty `mcp: {}`. So the platform uses opencode in its native mode (coding agent → preview URL), not as a research orchestrator.

---

## 2. Three integration architectures

### A. Replace agent runtime entirely

> opencode runs on the platform host, talks to EleutherIA via MCP/HTTP. Backend reduces to "tool server + data API". Frontend rebuilt against opencode's API or TUI.

**What gets thrown away (~8.7k LOC):**
- `graphrag/.../agents/react_loop.py` (452)
- `agents/graph_nodes.py` (6,600) — the entire FSM
- `agents/scholarly_agent.py`, `evidence_collector.py`, `sse_emitter.py`, `state.py`, `structured_models.py`, `prompts.py`, `text_verifier.py`
- `services/graphrag_service.py` (457) — replaced by HTTP shim
- The frontend GraphRAG pages (`graphragQuery`, `graphragQueryStream`, the whole conversations stack, ~700 lines in `client.ts`)

**What gets reused:**
- The 8 retrieval tools (`search_passages`, `search_nodes`, `get_node_detail`, `read_passages`, `read_work_section`, `explore_subgraph`, `get_neighbors`) — re-wrapped as an MCP server.
- `services/llm_service.py` (1,202) — discarded, since opencode handles LLM routing.
- `services/lemma_expansion.py`, `citation_verifier.py`, `tree_index.py`, `weighted_traversal.py`, `snapshot_retrieval.py`, `retrieval_strategy.py` — kept as primitives behind the MCP.

**Effort:** ~20-25 days.

**Pros:** Smallest agentic codebase to maintain long-term; gain UI streaming/multi-session/IDE plugins for free; opencode evolves and we ride that.
**Cons:** opencode's primary agents (`build`, `plan`) are coding personas — we'd hack a `scholar` agent on top, but the system prompts, default tools (bash, edit_file, LSP) are coding-flavoured. Frontend has to be rebuilt against opencode's HTTP API. Streaming format is opencode's, not ours — we lose control of reasoning-trace shape. Multi-tenant on free-will.app is awkward (one server-per-user model). Citation verification + claim ledger logic is hard to express as "agent prompts only".

### B. opencode as orchestrator, Python keeps sub-agents (MCP)

> opencode handles user-facing query + UI + multi-turn. It delegates to Python sub-agents (ConceptMapper, SourceFinder, Synthesizer) exposed as MCP tools.

**What gets thrown away:** `react_loop.py` + the top-level FSM nodes (Classify, EvidenceSufficiency, RenderGroundedAnswer). The mid-tier specialist work stays Python.

**What gets reused:** Most retrieval tools, citation_verifier, evidence_collector, claim ledger. Re-shaped as MCP tools with structured inputs/outputs.

**Frontend impact:** Same as (A) — opencode owns the user surface, so free-will.app's React app either consumes opencode's HTTP API directly, or we keep a thin FastAPI shim that proxies to opencode.

**Effort:** ~15-18 days (less code thrown away, but you maintain *both* runtimes — opencode JSON config *and* Python services, plus an MCP server bridging them).

**Pros:** Preserves scholarly logic in Python where the team's expertise is. Specialist sub-agents stay testable and version-controlled in our repo.
**Cons:** Two runtimes to ops — Bun *and* Python. MCP latency overhead (each delegation = network roundtrip + JSON serialisation). Debugging crosses a language boundary. The dev loop "edit Python tool → restart opencode → re-issue query in TUI" is slower than pure Python. opencode is still doing the *orchestration* — but our orchestration needs (citation verification, structured claim ledger, RenderGroundedAnswer with Greek+English) don't map cleanly onto opencode's free-form ReAct.

### C. Inspiration only — implement in Python

> Keep Python. Adopt opencode's *patterns* — multi-agent (primary + subagent), MCP tools, streaming protocol — natively. No new runtime.

**What gets thrown away:** Nothing forcibly. We can incrementally refactor `react_loop.py` + the FSM to clean primary/subagent semantics, formalise tools as MCP-compatible (so they're reusable from the platform later), and emit a cleaner SSE envelope.

**What gets reused:** Everything, modernised in place.

**Frontend impact:** Zero forced rewrite. We can layer new streaming events incrementally (the `sse_emitter.py` is already there).

**Effort:** ~6-10 days for a tight refactor (formalise tool registry as MCP-compatible, add a `pydantic-ai` ReAct that's robust against Kimi K2.6's tool-call format — the issue from task #35).

**Pros:** No new runtime, no new ops surface, no new auth model. Romain is already fluent in the Python stack. Citation verification + KG semantics stay first-class. the platform can still consume EleutherIA via MCP from opencode if needed — best of both. We fix the actual current blocker (Kimi tool-call parser) without bringing in a 6.5M-user coding tool that we'd be using sideways.
**Cons:** No "free UI" — we keep building free-will.app ourselves. No third-party clients/IDE plugins. We don't ride opencode's roadmap.

---

## 3. Recommendation: **C — Inspiration only**

EleutherIA is a scholarly research interface for ancient philosophy with a hand-curated KG, polytonic Greek, citation verification, a claim ledger, and a public-facing site at free-will.app. Opencode is a coding agent: its agents, prompts, default tools, and entire UX assume an editable working tree. Adopting it as our runtime would mean (a) bending a coding tool into a research role, (b) introducing a Bun runtime alongside our Python stack, (c) tossing 8k+ LOC of carefully-tuned scholarly orchestration to replace it with prompt engineering inside an external project we don't control, and (d) rebuilding the frontend against opencode's API.

The actual problems we need to solve — Kimi K2.6 tool-call parsing (#35), streaming polish, conversation threads, citation-grounded synthesis — are *Python-side* problems that don't get cheaper because opencode exists. Opencode's real gifts are its *patterns*: clean primary/subagent delegation, MCP tool boundaries, headless HTTP server with streaming. Those patterns are free to copy; the runtime is not.

The right move: refactor the existing ReAct loop into a clean primary + subagent shape, formalise the 8 retrieval tools behind an MCP-compatible interface (so the platform's opencode *can* talk to EleutherIA later via MCP if we want cross-project agentic flows), and fix the Kimi parser. If a year from now opencode has matured into a generic agent platform — revisit. For now, Python is the right home.

---

## 4. Implementation roadmap (recommended approach C)

### Phase 1 — Fix Kimi K2.6 tool-call parser (unblocks production)
- **Goal:** ReAct loop reliably parses Kimi K2.6 tool calls so the primary agent works in prod.
- **Files:** `graphrag/src/eleutheria_graphrag/agents/react_loop.py`, `agents/graph_helpers.py` (`parse_json`), `services/model_registry.py`.
- **Effort:** 2 days.
- **Tests:** Regression suite of real Kimi K2.6 transcripts in `graphrag/tests/unit/test_react_loop_parsing.py`. Test: malformed JSON, partial tool blocks, embedded prose.
- **Unblocks:** Stop defaulting to FSM (per MEMORY feedback). All downstream phases.

### Phase 2 — Formalise tool registry as MCP-compatible
- **Goal:** Each of the 8 tools in `agents/tools/` exposes a Pydantic schema + JSON-RPC handler matching MCP `tools/list` + `tools/call` semantics. Keep the in-process Python path (current behaviour); add an optional MCP transport.
- **Files:** `agents/tools/__init__.py`, new `agents/tools/mcp_server.py`, each tool file gets explicit `input_schema` / `output_schema`.
- **Effort:** 2 days.
- **Tests:** `tests/unit/test_tools_mcp_contract.py` — schema validation, round-trip via MCP stdio.
- **Unblocks:** the platform's opencode can call EleutherIA tools as a remote MCP later. Also gives us a clean tool contract for evals.

### Phase 3 — Primary + subagent split
- **Goal:** Refactor `react_loop.py` → one **primary** agent (broker, owns user dialogue + final synthesis) + N **subagents** (`SourceFinder`, `ConceptMapper`, `Synthesizer`, `Verifier`). Subagents are dispatched via a Python `Task`-style call with their own scoped tool subset + budget.
- **Files:** Split `react_loop.py`, new `agents/subagents/{source_finder,concept_mapper,synthesizer,verifier}.py`, retire most of `graph_nodes.py` (keep the structured-output models in `structured_models.py`).
- **Effort:** 4 days.
- **Tests:** `tests/unit/test_subagent_dispatch.py`, `tests/integration/test_primary_loop.py`, eval-harness regression against existing baseline.
- **Unblocks:** Multi-agent UI surface; cleaner traces.

### Phase 4 — Streaming protocol v2 (SSE event envelope)
- **Goal:** Replace ad-hoc SSE events with a documented envelope (`type: token|tool_call|tool_result|subagent_start|subagent_end|citation|done`) inspired by opencode's stream shape. Versioned, with TypeScript types in `frontend/src/types/stream.ts` and Python emitters in `agents/sse_emitter.py`.
- **Files:** `agents/sse_emitter.py`, `frontend/src/api/client.ts` (`graphragQueryStream`), new `frontend/src/types/stream.ts`, new `frontend/src/hooks/useGraphragStream.ts`.
- **Effort:** 3 days.
- **Tests:** Contract tests + Vitest snapshots for stream decoding.
- **Unblocks:** Frontend animation of reasoning trace; conversation thread UI.

### Phase 5 — Citation verifier as first-class subagent
- **Goal:** `citation_verifier.py` becomes a real subagent (`Verifier`) the primary calls after Synthesiser. Returns structured `ClaimLedger` with verified passages + caveats.
- **Files:** `services/citation_verifier.py` → `agents/subagents/verifier.py` (wraps existing service), update `RenderGroundedAnswer` equivalent.
- **Effort:** 2 days.
- **Tests:** Verifier regression set against known-hallucinated answers.
- **Unblocks:** Academic integrity policy enforced by code, not just prompts.

### Phase 6 — Headless HTTP server profile (optional)
- **Goal:** Add a thin `eleutheria_graphrag.server` module that exposes the primary agent over a stable HTTP + SSE contract, mirroring opencode's `serve` shape. Makes free-will.app, the CLI, and the platform all consume the same endpoint.
- **Files:** `backend/main.py` (registration), new `graphrag/.../api/agent_routes.py`.
- **Effort:** 2 days.
- **Tests:** End-to-end SSE test via httpx.
- **Unblocks:** Frontend rewrite of `client.ts`'s GraphRAG section to consume the new endpoint; downstream CLI integration.

### Phase 7 — Eval harness regression gate
- **Goal:** Before Phase 3's refactor lands, capture baseline answers on the eval set. After each subsequent phase, re-run eval; gate merges on no regression in citation-precision or completeness.
- **Files:** `graphrag/evals/` (extend existing harness).
- **Effort:** 1 day setup + ongoing.
- **Tests:** N/A (it *is* the test).
- **Unblocks:** Confidence that refactor doesn't degrade scholarly output.

### Phase 8 — Frontend reasoning-trace UI polish (optional, parallel)
- **Goal:** Render the new stream-v2 events with Framer Motion (per project_ui_overhaul). Subagent timeline, citation hover-cards, claim-ledger drawer.
- **Files:** `frontend/src/pages/GraphRAG*.tsx`, new components under `frontend/src/components/agent-trace/`.
- **Effort:** 3-5 days.
- **Tests:** Vitest + Playwright smoke.
- **Unblocks:** Public-facing polish for free-will.app.

**Total:** ~20 days, but it's reusable refactor that strengthens what exists rather than throwing it away.

---

## 5. Risk register

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| R1 | Phase 3 refactor breaks eval baseline (regression in citation precision or answer quality). | Medium | High | Capture baseline before refactor (Phase 7 first). Gate merges on eval. Keep `react_loop.py` available behind a feature flag for one release cycle. |
| R2 | Kimi K2.6 tool-call format changes again upstream (Moonshot/Fireworks). | Medium | Medium | Make the parser tolerant — accept both `tool_calls` field and inline `<tool>…</tool>` blocks, with fallback to JSON sniffing. Maintain a fixture set of real responses. |
| R3 | Adopting "MCP-compatible" tool shape adds boilerplate that slows tool authoring. | Low | Low | Generate the MCP wrapper from the Pydantic schema; tool authors write Python as today, get MCP for free. |
| R4 | Opencode matures into a research-capable platform in 12 months → we'd want to re-revisit. | Low | Low | Phase 2's MCP boundary keeps that option open — at minimal cost. No lock-in either way. |
| R5 | Streaming-v2 envelope breaks existing free-will.app clients during rollout. | Medium | Medium | Version the SSE endpoint (`/api/graphrag/query/stream` stays, `/v2/stream` ships new); migrate clients then deprecate. |

---

## 6. Decision points for Romain

1. **Kill the Python FSM (`graph_nodes.py`, 6.6k LOC) entirely, or keep as fallback?**
   Recommendation: kill after Phase 3 lands and eval is green for 2 weeks. The FSM was the *predecessor* to ReAct, not a redundant safety net — keeping both indefinitely doubles maintenance.

2. **Frontend: full rewrite of GraphRAG pages, or incremental Stream-v2 layer?**
   Recommendation: incremental. The current `client.ts` is fine; only `graphragQueryStream` + the pages that render trace events need replacement.

3. **Expose EleutherIA tools as an MCP server *now* (Phase 2) or defer?**
   Recommendation: do it now. It's cheap (2 days), it formalises the tool contract, and it lets the platform's opencode call EleutherIA in 2026 without re-engineering.

4. **Stick with `pydantic-ai` (in deps already) or roll bespoke loop?**
   Recommendation: stick with `pydantic-ai` for structured I/O + tool definitions; keep the bespoke primary/subagent dispatcher (`ScholarlyAgent`) for budget + streaming control. Hybrid is fine.

5. **Add opencode to the platform host as a *consumer* of EleutherIA's MCP endpoint, for power-user workflows (e.g. dev asks "rewrite this passage's KG metadata" in opencode TUI)?**
   Recommendation: yes, eventually — but only after Phase 2 lands. No blocker on EleutherIA's roadmap.

6. **Do we deprecate `/api/graphrag/answer` (non-streaming) once Stream-v2 ships?**
   Recommendation: keep it. Non-streaming is useful for CLI, batch eval, and curl debugging. Cost is low.
