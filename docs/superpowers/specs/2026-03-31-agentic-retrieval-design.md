# Agentic Retrieval Architecture — Design Spec

**Date:** 2026-03-31
**Status:** Draft
**Replaces:** 12-node pydantic-graph FSM pipeline (DiscoverCorpus → EvidenceSufficiency)

## Context

The current GraphRAG pipeline is a rigid 12-node FSM. Retrieval is one-shot: `DiscoverCorpus` seeds nodes once via ILIKE/vector search, and subsequent stages work with that fixed set. When a user asks "What did Plato and Origen say about free will?", the pipeline returns 200 noisy nodes instead of precisely finding the 2 relevant persons and exploring their connections.

**Root cause:** The pipeline can't *reason* about relevance. A human would: search Origen → found. Search Plato → found. Explore connections → Middle Platonism, autexousion. Read the texts → De Principiis III.1. That's what the agent must do.

**Research basis:** ToG 2.0 (ICLR 2024), IRCoT (ACL 2023), HippoRAG (NeurIPS 2024), Paths-over-Graph (ACM 2025), Debate-on-Graph (AAAI 2025), CRAG (ICLR 2024), Self-RAG (ICLR 2024). Full literature review in `docs/superpowers/specs/agentic-retrieval-research.md`.

---

## Architecture

Three phases. The middle phase (currently 8 FSM nodes) is replaced by a ReAct agent loop.

```
┌──────────────────┐     ┌──────────────────────────┐     ┌──────────────────────┐
│  PHASE 1: CLASSIFY│     │  PHASE 2: AGENT LOOP     │     │  PHASE 3: SYNTHESIS   │
│  (deterministic)  │────▶│  (ReAct, ~15 tool calls) │────▶│  (deterministic)      │
│                   │     │                          │     │                       │
│  ClassifyQueryType│     │  LLM reasons + 7 tools   │     │  DraftClaimLedger     │
│  → query_type     │     │  → EvidenceCollector     │     │  RenderGroundedAnswer │
│  → complexity     │     │  → SSE streaming steps   │     │  ProgrammaticVerify   │
│  → budget         │     │                          │     │  → ScholarlyAnswer    │
└──────────────────┘     └──────────────────────────┘     └──────────────────────┘
```

**Phase 1** (unchanged): `ClassifyQueryType` from `graph_nodes.py`. Produces `query_type`, `complexity`, and sets tool budget.

**Phase 2** (new): ReAct loop. The LLM receives 7 tools to explore the KG. It decides what to search, in what order, and when it has enough evidence. Each step is streamed as an SSE event. Budget: SIMPLE=5, MEDIUM=10, COMPLEX=15 tool calls.

**Phase 3** (unchanged): `DraftClaimLedger` → `RenderGroundedAnswer` → `ProgrammaticVerify`. The `EvidenceCollector` populates the existing `RAGState` so these nodes work without modification.

The pydantic-graph `Graph` object is removed. `ScholarlyAgent` calls phases sequentially.

---

## Agent Tools (7)

### 1. `search_nodes`

Find KG nodes by label/description match.

```python
# Input
query: str                          # Search text
type_filter: str | None = None      # "person", "concept", "work", "school", etc.
period_filter: str | None = None    # "Hellenistic", "Imperial", etc.
limit: int = 10                     # 1-30

# Output
nodes: list[{node_id, label, type, description[200c], period, school, score}]
total_found: int
```

**Implementation:** In-memory label/description match + Qdrant semantic search, merged via RRF. Descriptions truncated to 200 chars in LLM context (full text goes to EvidenceCollector).

### 2. `get_neighbors`

Explore graph edges from a known node.

```python
# Input
node_id: str
relation_filter: str | None = None  # "influenced_by", "authored_by", etc.
direction: str = "both"             # "out", "in", "both"
limit: int = 15                     # 1-30

# Output
center_node: str
center_label: str
edges: list[{edge_node_id, label, type, relation, direction, weight}]
```

**Implementation:** In-memory `outgoing_edges`/`incoming_edges`. Sorted by `weight × pagerank_score`. Filtered by relation if provided.

### 3. `read_passages`

Load passage text linked to a KG node via `passage_citations`.

```python
# Input
node_id: str
limit: int = 5                     # 1-10

# Output
node_id: str
node_label: str
passages: list[{passage_id, work_title, author, canonical_ref, language, text_content[800c], confidence}]
```

**Implementation:** `passage_citations` JOIN `passages` JOIN `ancient_works`, ordered by confidence DESC.

### 4. `search_passages`

Full-text search across the passage corpus.

```python
# Input
query: str
work_filter: str | None = None     # Filter by work_id
limit: int = 5                     # 1-10

# Output (same shape as read_passages)
passages: list[{passage_id, work_title, author, canonical_ref, language, text_content[800c], confidence}]
```

**Implementation:** `HybridSearchService.hybrid_search()` (FTS + lemmatic + RRF). Falls back to `ts_rank` if HybridSearch unavailable.

### 5. `get_node_detail`

Full metadata for a specific node.

```python
# Input
node_id: str

# Output
node_id: str
label: str
type: str
description: str                   # Full, not truncated
period: str | None
school: str | None
metadata: dict
neighbor_count: int
passage_count: int
```

**Implementation:** `node_lookup[id]` + edge counts from in-memory dicts + passage count via SQL.

### 6. `read_work_section`

Navigate the hierarchical tree index of a work.

```python
# Input
work_id: str
section_path: str | None = None    # "Book I/Chapter 3". None = top-level TOC

# Output
work_id: str
work_title: str
author: str
sections: list[{node_id, title, path, summary, passage_count, has_subsections}]
```

**Implementation:** `TreeIndexService.load_indices()` → navigate to path. If leaf section, returns passages from range.

### 7. `explore_subgraph`

PPR-based broad exploration from seed nodes (HippoRAG-inspired).

```python
# Input
seed_node_ids: list[str]           # 1-5 seed nodes
top_k: int = 20                    # 5-50

# Output
nodes: list[{node_id, label, type, ppr_score, distance_from_seed}]
```

**Implementation:** Personalized PageRank from seed nodes on the in-memory KG. Uses existing `KGAnalytics` infrastructure (which already computes global PageRank). Single step, no LLM calls. Returns the top-K most relevant nodes in the subgraph surrounding the seeds.

---

## ReAct Loop

### System Prompt Structure

```
You are a scholarly research agent for ancient philosophy. You have access to a
knowledge graph (17,700 nodes, 42,900 edges) and a corpus of 487 ancient works
(69,000 passages) covering philosophical debates on free will, fate, and moral
responsibility from 6th c. BCE to 6th c. CE.

## Instructions
- Think step by step. Identify key entities, explore their connections, read the
  relevant texts, then check for counter-evidence before concluding.
- After every 2-3 tool calls, evaluate: "Do I have enough evidence to answer
  this question thoroughly?" If yes, respond with SYNTHESIZE.
- If a search returns irrelevant results, reformulate your query or try a
  different tool (CRAG self-correction).
- You have {remaining} tool calls remaining. Use them wisely.

## Available Tools
{tool_descriptions_json}

## Response Format
To call a tool:
{"tool": "<name>", "args": {<arguments>}, "reason": "<why this call>"}

To stop and synthesize:
{"action": "SYNTHESIZE", "summary": "<what you found>"}
```

### Loop Pseudocode

```python
class AgentLoop:
    def __init__(self, deps, state, emitter):
        self.deps = deps
        self.state = state
        self.emitter = emitter          # SSEEmitter for streaming
        self.evidence = EvidenceCollector()
        self.tools = register_tools(deps)
        self.messages: list[dict] = []
        self.budget = compute_budget(state.complexity)  # 5/10/15
        self.calls_made = 0

    async def run(self) -> None:
        self.messages = [
            {"role": "system", "content": system_prompt(self.budget)},
            {"role": "user", "content": user_prompt(self.state.question)},
        ]

        while self.calls_made < self.budget:
            # Budget warning at N-2
            if self.budget - self.calls_made == 2:
                self.messages.append(system_msg(
                    "2 tool calls remaining. Consider synthesizing."
                ))

            # LLM reasons
            raw = await self.deps.llm.generate(
                prompt=format_messages(self.messages),
                temperature=0.1,
                max_tokens=1024,
            )

            # Parse action
            action = parse_action(raw)

            if action is None:
                # Parse failure → retry with format reminder
                self.messages.append(assistant_msg(raw))
                self.messages.append(system_msg("Respond with a single JSON block."))
                continue

            if action.type == "synthesize":
                await self.emitter.emit_thinking(action.summary)
                break

            # Execute tool
            await self.emitter.emit_tool_start(action.tool, action.args, action.reason)
            try:
                result = await self.tools[action.tool].execute(action.args)
                self.evidence.ingest(action.tool, action.args, result)
            except Exception as e:
                result = ErrorResult(error=str(e))

            await self.emitter.emit_tool_result(action.tool, summarize(result))

            # Append to context (summarized, not full)
            self.messages.append(assistant_msg(raw))
            self.messages.append(tool_msg(summarize_for_context(result)))
            self.calls_made += 1

            # Context management: compress old results after 10 messages
            if len(self.messages) > 12:
                compress_old_tool_results(self.messages)

        # Transfer evidence to RAGState for synthesis phase
        self.evidence.populate_state(self.state)
```

### Action Parsing

JSON extraction from LLM output. Reuses the existing `_parse_json` helper from `graph_nodes.py`. Validates tool name exists in registry and args match input schema.

### Context Management (IRCoT + Google Cloud pattern)

- Tool results in LLM context are **summarized**: node lists show `id+label+type` only, passage text truncated to 400 chars
- Full untruncated evidence always stored in `EvidenceCollector`
- After 12 messages: oldest tool results compressed to one-line summaries (e.g., `"search_nodes('Origen') → 5 nodes: [Origen of Alexandria, ...]"`)
- Accumulated context monitored against 50% of model window

### Budget Management

| Complexity | Budget | Typical pattern |
|-----------|--------|-----------------|
| SIMPLE | 5 | 1 search + 1 detail + 1 read_passages + SYNTHESIZE |
| MEDIUM | 10 | 2 searches + 1 explore_subgraph + 2 get_neighbors + 2 read_passages + SYNTHESIZE |
| COMPLEX | 15 | 2 searches + 1 explore_subgraph + 3 get_neighbors + 3 read_passages + 2 search_passages + SYNTHESIZE |

Budget warning at N-2. Hard cap forces synthesis with whatever evidence is collected.

### Agent Behaviors (from literature)

1. **IRCoT interleaving**: Each tool call is informed by reasoning from previous results
2. **ToG 2.0 alternation**: Agent alternates between graph structure (`get_neighbors`) and text evidence (`read_passages`)
3. **DoG sufficiency**: After 2-3 calls, agent evaluates "do I have enough?" → natural early stopping
4. **CRAG self-correction**: If search returns noise, agent reformulates or switches tools
5. **PoG path pruning**: `get_neighbors` returns metadata; agent selects which paths to follow
6. **GCR grounding**: Synthesis constrained to only reference retrieved entities/passages

---

## EvidenceCollector

Bridges agent tool results to `RAGState` for the synthesis phase.

```python
class EvidenceCollector:
    seen_node_ids: set[str]
    seen_passage_ids: set[str]
    primary_evidence: list[Evidence]     # From search_nodes, explore_subgraph
    secondary_evidence: list[Evidence]   # From get_neighbors
    evidence_bundles: list[EvidenceBundle]  # From read_passages, search_passages
    seed_node_ids: list[str]
    context_node_ids: list[str]
    tool_calls: list[ToolCallRecord]     # Full audit trail

    def ingest(tool_name, args, result) -> None:
        # Route results to appropriate lists based on tool type
        # Deduplicate by node_id / passage_id

    def populate_state(state: RAGState) -> None:
        # Write all accumulated evidence into RAGState
        # Build context_pack and scholarly_dossier
        # Set passages_used, seed_node_ids, context_node_ids
```

The collector deduplicates across tool calls (same node found by search and by neighbor traversal is stored once). The `tool_calls` list provides a complete audit trail for scholarly transparency (GvD pattern).

---

## SSE Streaming Protocol

### New Event Types

```typescript
// Existing (unchanged)
type: "status"         // { message, step }
type: "answer_chunk"   // string
type: "complete"       // { data: GraphRAGResponse }
type: "error"          // { message }

// New (agent loop)
type: "agent_thinking" // { thinking: string, step: number, remaining: number }
type: "tool_start"     // { tool: string, args: object, reason: string, step: number }
type: "tool_result"    // { tool: string, summary: string, duration_ms: number,
                       //   node_count?: number, passage_count?: number, step: number }
```

### Frontend Integration

`useSSEStream.ts` switch statement extended with 3 new cases. The `SSEStreamEvent` type union updated. A new "Agent Activity" UI component displays tool calls in real time:

```
🔍 Searching for "Origen" (person)...
   → Found 3 nodes: Origen of Alexandria, Origen the Pagan, ...
🔗 Exploring neighbors of Origen of Alexandria...
   → 12 connections: influenced_by → Middle Platonism, wrote → De Principiis, ...
📖 Reading passages from De Principiis...
   → 5 passages loaded (III.1.1-5, on free will and self-determination)
💭 Agent: "I have Origen's position. Now searching for Plato..."
```

### Backend Emitter

`SSEEmitter` class wraps an `asyncio.Queue`. The streaming endpoint runs the agent loop in a task, reads events from the queue, and yields them as SSE lines.

---

## Integration with Existing Code

### Unchanged
- `state.py` — all models (RAGState, Evidence, EvidenceBundle, ScholarlyAnswer, etc.)
- `dependencies.py` — Deps dataclass
- `pipeline_config.py` — QueryType, PipelineConfig, complexity mapping
- `structured_models.py` — ClassificationResult
- `llm_service.py` — LLMService.generate() (only LLM interface)
- `retrieval_strategy.py` — VectorStrategy/SQLStrategy (used inside tools)
- `tree_index.py` — TreeIndexService (used by `read_work_section` tool)

### Extracted from graph_nodes.py → shared modules
- `graph_helpers.py` — `_parse_json`, `_scholarly_dossier_payload`, `_build_research_graph_payload`, `_claim_reference_markers`, `_render_evidence_packet`, `_verify_answer_programmatically`, `_quality_badge_from_state`, `_make_answer`, `_append_reasoning_step`, `_resolve_model_api_id`
- `prompts.py` — All prompt templates (`CLASSIFY_QUERY_TYPE_PROMPT`, `CLAIM_LEDGER_PROMPT`, `RENDER_ANSWER_PROMPT`, `SCHOLARLY_POLISH_PROMPT`, etc.)

### Modified
- `scholarly_agent.py` — New orchestrator: classify → agent loop → synthesis. Feature flag `ELEUTHERIA_AGENT_MODE=fsm|react` for parallel operation.
- `graph_nodes.py` — Slimmed to 4 nodes: ClassifyQueryType, DraftClaimLedger, RenderGroundedAnswer, ProgrammaticVerify. Imports helpers from extracted modules.
- `routes.py` — New SSE event types from agent loop.
- `graphrag_service.py` — `query_stream()` updated for queue-based SSE events.
- `useSSEStream.ts` — 3 new event type cases.

### New Files
```
graphrag/src/eleutheria_graphrag/agents/
  react_loop.py              # AgentLoop class, action parsing, context management
  evidence_collector.py      # EvidenceCollector
  sse_emitter.py             # SSEEmitter
  graph_helpers.py           # Extracted helpers from graph_nodes.py
  prompts.py                 # Extracted prompt templates
  tools/
    __init__.py              # Tool registry + BaseTool protocol
    search_nodes.py
    get_neighbors.py
    read_passages.py
    search_passages.py
    get_node_detail.py
    read_work_section.py
    explore_subgraph.py      # PPR-based exploration
```

---

## Migration Path

### Phase 1: Extract & scaffold (no behavior change)
1. Create `graph_helpers.py` + `prompts.py` — extract shared code from `graph_nodes.py`
2. Update imports, verify all tests pass
3. Create `tools/` with 7 tool implementations backed by existing services
4. Create `evidence_collector.py` and `sse_emitter.py`
5. Unit tests for each tool

### Phase 2: Build AgentLoop (coexistence)
1. Create `react_loop.py`
2. Feature flag in `scholarly_agent.py`: `ELEUTHERIA_AGENT_MODE=fsm|react`
3. Both pipelines coexist for A/B comparison
4. Integration tests for agent loop

### Phase 3: Frontend streaming
1. New SSE event types in `useSSEStream.ts`
2. Agent Activity UI component
3. Updated `graphrag.ts` type definitions

### Phase 4: Validation & cutover
1. Regression suite: 5-10 reference queries, compare FSM vs ReAct
2. Golden tests: "Plato and Origen", "Stoic fate", "Epicurean swerve"
3. Flip default to `react` when quality meets or exceeds FSM

### Phase 5: Cleanup
1. Remove 8 replaced FSM nodes
2. Remove `fsm` code path
3. Remove pydantic-graph dependency from agent module

---

## Verification

### Unit tests
- Each tool: mock Deps, assert correct filtering/ranking/truncation/error handling
- AgentLoop: mock LLMService.generate() with scripted JSON, verify parsing/budget/SYNTHESIZE
- EvidenceCollector: feed mock results, verify RAGState population

### Integration tests
- Full pipeline with test database fixture (subset of real KG)
- Golden queries:
  1. "Who is Origen?" (SIMPLE — should stop in ~3 calls)
  2. "What did Plato and Origen say about free will?" (COMPLEX — the motivating example)
  3. "How did Stoic views on fate evolve?" (MEDIUM/COMPLEX)
- Assert: answer contains expected citations, bundles reference correct passages, no fabricated Greek/Latin

### SSE streaming tests
- Mock agent loop, verify event sequence: status → tool_start → tool_result → ... → answer_chunk → complete

### Regression comparison
- Run both pipelines on same 10 queries, compare: citation count, passage count, answer relevance, latency
