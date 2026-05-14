# opencode Event Protocol — Track O spike findings

Date: 2026-05-14
Spike: A/B comparison of sst/opencode (1.14.31) vs Python-native ReAct as the
agent runtime for EleutherIA's scholarly research workflow.

This document is the operational reference for what an EleutherIA backend would
have to speak to drive (or consume from) opencode in production. It is the
result of black-box probing of a local `opencode serve --port 4096` instance
plus `opencode run --format json` runs against `scholar-orchestrator` with the
EleutherIA MCP server (`mcp_server/transports/stdio.py`) attached.

## TL;DR

opencode exposes two event surfaces, with different shapes:

| Surface | Transport | Shape | Use case |
|---|---|---|---|
| `opencode run --format json` | stdout JSONL | Coarse-grained: `step_start` / `tool_use` / `text` / `step_finish` | One-shot CLI batch invocation |
| `GET /event` on `opencode serve` | SSE (text/event-stream) | Fine-grained: `session.*` / `message.*` / `message.part.delta` | Live UI streaming |

**The SSE channel is global, not per-session.** A single `/event` stream receives
events for every active session on the server. Filtering is the client's job
(match on `properties.sessionID`).

## HTTP API exposed by `opencode serve`

Discovered by probing — only a 2-path OpenAPI spec at `/doc` advertises the auth
surface; the session/event/message endpoints are undocumented but functional.

```
GET  /session                        list all sessions (JSON array)
GET  /session/{id}                   session metadata (info object)
GET  /session/{id}/message           full message history with parts (JSON array)
GET  /event                          live SSE stream of all session events
POST /log                            write log line
PUT  /auth/{providerID}              set provider credentials
DELETE /auth/{providerID}            remove provider credentials
```

Session creation and message-send endpoints exist (used by `opencode run --attach`)
but are not visible via `/doc` and were not probed in the spike. Reverse-engineer
from the running TUI or accept that for the spike we drive via CLI.

There is **no `?session_id=` filter** on `/event`. Production clients will need to
de-multiplex.

## SSE event types — `GET /event`

Captured by tailing `/event` for 30 s during one full `scholar-orchestrator` run.
All payloads are wrapped: `{"type": <event_type>, "properties": {...}}`.

| Event type | Count in sample | Purpose |
|---|--:|---|
| `server.connected` | 1 | Initial handshake; sent on every connect |
| `server.heartbeat` | 2 | Keep-alive ping |
| `session.created` | 1 | New session born |
| `session.updated` | 5 | Title / token-count / timestamp changes |
| `session.status` | 4 | Coarse session lifecycle (`busy` / `idle`) |
| `session.idle` | 1 | Terminal — session completed |
| `session.diff` | 2 | Workspace file diffs (irrelevant for read-only agents) |
| `message.updated` | 6 | Message metadata refresh (cost, tokens, completion) |
| `message.part.updated` | 7 | Whole-part snapshot (text/reasoning/tool/step-start) |
| `message.part.delta` | 37 | Streaming token delta — most frequent event |

### `message.part.delta` (streaming text)

```json
{
  "type": "message.part.delta",
  "properties": {
    "sessionID": "ses_...",
    "messageID": "msg_...",
    "partID": "prt_...",
    "field": "text",
    "delta": "The"
  }
}
```

`field` can be `"text"` or `"reasoning"`. Concatenate deltas keyed by `partID` to
reconstruct streaming output.

### `message.part.updated` (tool / step lifecycle)

When a tool call completes, opencode emits a full `message.part.updated` with the
final `part.state.status = "completed"` and `part.state.output` populated.
The Task tool uses this to surface subagent completion; MCP tools use it the same
way.

```json
{
  "type": "message.part.updated",
  "properties": {
    "sessionID": "ses_...",
    "part": {
      "type": "tool",
      "tool": "eleutheria_search_nodes",
      "callID": "...",
      "state": {
        "status": "completed",
        "input": { "query": "prohairesis", "type_filter": "concept", "limit": 10 },
        "output": "<JSON string returned by the MCP tool>",
        "metadata": { ... },
        "time": { "start": ..., "end": ... }
      }
    }
  }
}
```

### `session.status`

```json
{ "type": "session.status",
  "properties": { "sessionID": "ses_...", "status": { "type": "busy" } } }
```

Lifecycle: `busy` → `idle` once the agent's step loop exits.

## CLI `--format json` event shape (alternative)

`opencode run --format json` emits a **flatter, coarser** JSONL stream — useful
for batch scripts but missing token deltas:

```json
{"type":"step_start","timestamp":1778788409643,"sessionID":"ses_...","part":{...}}
{"type":"tool_use","timestamp":...,"sessionID":"...","part":{"type":"tool","tool":"task","callID":"...","state":{"status":"completed","input":{...},"output":"...","metadata":{"sessionId":"ses_<subagent>"}}}}
{"type":"text","timestamp":...,"sessionID":"...","part":{"type":"text","text":"<full final answer>"}}
{"type":"step_finish","timestamp":...,"sessionID":"...","part":{...}}
```

CLI events seen across the three spike queries: `step_start`, `tool_use`,
`text`, `step_finish`. No reasoning, no token deltas, no streaming — the `text`
event arrives once with the full answer.

**Important:** the CLI format only surfaces the **orchestrator's** events. Subagent
tool calls (MCP calls inside `concept-mapper` / `source-finder`) are invisible in
the JSONL — only the parent `task` tool_use shows up. To see subagent activity
you must call `opencode export <subagent-sessionID>` (the subagent session id is
stashed in `tool_use.part.state.metadata.sessionId`).

## Diff vs EleutherIA's `frontend/src/types/agent-events.ts`

EleutherIA's current contract is a flat, semantic, citation-aware union:

```ts
type AgentEvent =
  | { type: 'agent_start'; agent: string; query: string; trace_id?: string }
  | { type: 'agent_step'; agent: string; subagent: string; status: SubagentStatus }
  | { type: 'tool_call'; agent: string; tool: string; args: ToolArgs; id: string }
  | { type: 'tool_result'; tool_call_id: string; result_summary: string;
      nodes_touched?: string[]; passages_touched?: string[] }
  | { type: 'citation_found'; passage_id: string; cts_urn?: string;
      excerpt: string; node_ids: string[]; confidence: number }
  | { type: 'kg_node_activated'; node_id: string; label: string;
      node_type: string; period?: string }
  | { type: 'token'; delta: string }
  | { type: 'citation_verified'; passage_id: string; verified: boolean }
  | { type: 'final_answer'; answer: string; citations: FinalAnswerCitation[];
      trace_id: string }
  | { type: 'error'; agent: string; message: string };
```

### Mapping table — opencode SSE → existing protocol

| EleutherIA event | opencode source | Adapter complexity |
|---|---|---|
| `agent_start` | Synthesise from `session.created` + initial user `message.part.updated` | Trivial (1 join) |
| `agent_step` | `message.updated` with `part.tool == "task"` | Trivial (filter by tool name) |
| `tool_call` | `message.part.updated` where `part.type == "tool"` AND `part.state.status in ("running","completed")`, tool starts with `eleutheria_` | Trivial |
| `tool_result` | Same event, but only when `status == "completed"`. `result_summary` requires parsing the MCP tool's JSON output | Moderate — must parse MCP output strings to extract `nodes_touched` / `passages_touched` |
| `citation_found` | Derive from `eleutheria_read_passages` / `eleutheria_search_passages` tool outputs (no native event) | **Heavy** — need a side-channel that watches MCP tool results and synthesises `citation_found` |
| `kg_node_activated` | Derive from `eleutheria_search_nodes` / `eleutheria_get_node_detail` outputs | **Heavy** — same as above |
| `token` | `message.part.delta` with `field == "text"` | Trivial (1-to-1) |
| `citation_verified` | No equivalent — verifier is a separate Python step in Track P | **Missing entirely** — would need to be implemented as a post-stream pass or as a third subagent |
| `final_answer` | Synthesise from terminal `message.part.updated` (type text) at `session.idle` | Trivial |
| `error` | Tool state `status == "failed"` or `session.error` event (not observed; assume exists) | Light |

### Estimate: adapter code needed

- **Pure SSE proxy (token streaming only):** ~80 LOC TypeScript on a Workers/Node
  edge function that connects to `opencode serve /event`, filters by sessionID,
  and re-emits as the existing 10-event shape. Token deltas and tool-call lifecycle
  map 1-to-1.
- **Citation enrichment (the hard part):** ~300–500 LOC to parse MCP tool result
  JSON strings, look up KG metadata, score confidence, and emit synthetic
  `citation_found` + `kg_node_activated` events. This is logic that today lives
  in the Python ReAct agent's `result_summary` synthesis.
- **Verification pass:** opencode has no notion of post-hoc citation
  verification. Either fold it into a fourth subagent (`citation-verifier`,
  pure MCP, no fabrication risk) or run it as a Python post-processor on
  `final_answer`. Choose 30 LOC of agent markdown if the spike comparison
  shows the subagent path is cheap.

**Realistic production adapter total: 600–900 LOC + 1 new subagent prompt.**

## Operational observations from the spike

### Three spike queries against real Supabase + Fireworks/Kimi K2.6

| Query | Latency | Subagents | MCP tool calls | Answer chars | URN citations |
|---|--:|--:|--:|--:|--:|
| Q1 "Aristotle voluntary action NE III" | 213 s | 2 | **78** | 6120 | 0 (KG node ids only) |
| Q2 "Stoic compatibilism vs Aristotle" | 452 s | 4 | **141** | 6432 | 20 |
| Q3 "Origen autexousion vs astrology" | 278 s | 3 | **126** | 5286 | 0 (KG node ids) |

MCP tool breakdown (Q2, representative):

```
eleutheria_search_passages    78
eleutheria_search_nodes       29
eleutheria_get_neighbors      19
eleutheria_get_node_detail     8
eleutheria_read_passages       4
eleutheria_explore_subgraph    2
eleutheria_read_work_section   1
```

All 7 MCP tools were exercised. Zero MCP errors. Subagent delegation worked
without prompt-engineering surgery — the orchestrator decomposed and dispatched
2–4 subagents per query.

### Caveats

- 200–450 s latency is high for an interactive scholar UI. Kimi K2.6 on Fireworks
  emits reasoning blocks for every step and the orchestrator runs subagents
  sequentially by default. Track P's PageIndex V3 path (2 LLM calls, no
  subagents) is ~10–20× faster.
- The orchestrator sometimes prefers to cite KG node ids (`concept_hekousion_...`)
  over CTS URNs, even when subagents returned URNs. Tighter prompt enforcement
  or a post-stream pass should fix this.
- No fabricated Greek detected in the three answers — every Greek string traced
  back to a real MCP tool output. The integrity rule survives the round trip.
- `opencode serve` ships unauthenticated by default; `OPENCODE_SERVER_PASSWORD`
  must be set in any deployment.

## Recommendation

opencode is **operationally viable** as a Track O runtime: MCP works, subagents
work, streaming works, Fireworks/Kimi K2.6 works. The event protocol is richer
than ours (delta-level reasoning + tool state machines) and would force us to
either (a) consume opencode's native shape end-to-end in the frontend (rewrite
`useResearchStream`) or (b) write a 600–900 LOC adapter. The latency gap to
Track P is the bigger concern for production.

Decision blockers documented in the parent spike report.
