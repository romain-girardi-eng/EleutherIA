# Vectorless Fallback + Multi-Model Selection + Reasoning Trace

**Date:** 2026-03-30
**Status:** Approved
**Author:** Romain Girardi

---

## Problem

The GraphRAG pipeline is locked to Google Gemini for both embeddings (`gemini-embedding-001` via Qdrant) and reasoning (`gemini-3.1-pro-preview`). When the Gemini API hits its spending cap or rate limit (HTTP 429), the entire pipeline fails — semantic search returns nothing, and the FSM produces empty answers.

Additionally, there is no way to:
- Compare how different LLMs perform on the same scholarly question
- Inspect the LLM's reasoning at each FSM step
- Continue a conversation with follow-up questions

## Solution

Three interlocking features:

1. **Vectorless retrieval** — a SQL-only alternative to Qdrant that uses passage_citations, full-text search, lemmatic search, and canonical work loading to seed the FSM without any embedding call
2. **Multi-model selection** — a model registry with OpenRouter routing so users can pick their reasoning model (Gemini, Claude, Qwen, DeepSeek)
3. **Reasoning trace + conversation threads** — full FSM step-by-step trace exposed in the UI, with tabbed multi-response comparison and follow-up support

---

## 1. RetrievalStrategy — Injection Point

### Architecture

A `RetrievalStrategy` protocol with two implementations. The single injection point is `_discover_corpus()` in `graph_nodes.py` (line 3632) — currently a direct Qdrant call.

```python
class RetrievalStrategy(Protocol):
    async def discover_seeds(
        self, queries: list[str], deps: Deps, budget: RetrievalBudget
    ) -> tuple[list[str], list[str]]:
        """Returns (seed_node_ids, passage_anchor_ids)."""
        ...

class VectorStrategy(RetrievalStrategy):
    """Existing behavior: embed query via Gemini → Qdrant search → seed nodes."""

class SQLStrategy(RetrievalStrategy):
    """New: 4-step escalation without any Qdrant or embedding call."""
```

### Mode Selection

The retrieval mode is determined by (in priority order):

1. **Request parameter:** `"retrieval_mode": "auto" | "vector" | "sql"` in the API call
2. **Environment variable:** `RETRIEVAL_MODE=auto|vector|sql` (global override)
3. **Default:** `"auto"`

In `"auto"` mode: attempt VectorStrategy first. If it fails (Qdrant connection error, Gemini 429, embedding timeout), automatically fall back to SQLStrategy. The `retrieval_mode_used` field in the response indicates which strategy actually ran.

### FSM Impact

**Nothing changes after DiscoverCorpus.** The remaining 11 FSM nodes receive the same `seed_node_ids` + `passage_anchor_ids` regardless of which strategy produced them.

---

## 2. SQLStrategy — 4-Step Escalation

### Step 1: Direct passage_citations (fast, ~100ms)

```sql
-- Find KG nodes matching the expanded query terms
SELECT node_id FROM free_will.kg_nodes
WHERE label ILIKE ANY(ARRAY['%term1%', '%term2%', ...])
   OR description ILIKE ANY(ARRAY['%term1%', '%term2%', ...])
LIMIT 200;

-- Fetch their cited passages
SELECT passage_id, kg_node_id, confidence
FROM free_will.passage_citations
WHERE kg_node_id = ANY($1)
ORDER BY confidence DESC
LIMIT 100;
```

Plus 1-hop graph expansion via `deps.outgoing_edges` / `deps.incoming_edges` (already in RAM).

**Exit condition:** if >= 4 evidence bundles found, skip to FSM continuation.

### Step 2: HybridSearch — FTS + Lemmatic (~300ms)

Inject `HybridSearchService` (existing code in `database/src/eleutheria_database/services/hybrid_search.py`, currently wired to `Deps` but never called by the FSM).

- `fulltext_search(query)` — PostgreSQL `ts_rank` on `passages.search_vector`
- `lemmatic_search(lemma)` — JSONB `passages.morphology @> '[{"l": "<lemma>"}]'`
- RRF fusion (k=60) of results
- Reverse-lookup `passage_citations` to extract `kg_node_ids` from matched passages

**Exit condition:** if >= 4 evidence bundles found, skip to FSM continuation.

### Step 2bis: Canonical works safety net (the key innovation)

For each philosopher/concept identified in steps 1-2:
- Resolve canonical works via `kg_edges` (`authored_by`, `discusses`, `source_for`)
- Example: "Chrysippus + fate" → Cicero De Fato, SVF fragments, Alexander De Fato
- Load ALL passages of these works via `tree_index.extract_passages(work_id)`
- A complete De Fato is ~30k tokens — budget allows 15-20 complete works

**This is the real advantage of vectorless with 1M context:** instead of surgically finding the right passages (and risking misses), load entire canonical works and let the LLM find relevant evidence. Impossible in vector mode (too many tokens for embedding search), trivial with 1M context.

### Step 3: Expanded context stuffing (last resort)

If steps 1-2bis still yield insufficient evidence:
- Take all works identified so far
- Load adjacent sections via `tree_index`
- Budget cap: 300k tokens of raw passages
- These become seed evidence for the remaining FSM

### Escalation Summary

| Step | Action | Safety guarantee |
|---|---|---|
| 1 | Direct passage_citations | KG citation links (confidence >= 0.7) |
| 2 | HybridSearch FTS + lemmatic | Covers lexical variants (synonyms, alternate forms) |
| 2bis | Load entire canonical works | Zero missed passages on key texts |
| 3 | Expanded context stuffing | Adjacent sections, last chance |

Note: `ExpandQuery` (FSM node 2) runs BEFORE `DiscoverCorpus`, so SQLStrategy benefits from the expanded Greek/Latin terms, philosopher names, and concept synonyms.

---

## 3. Model Registry + OpenRouter Routing

### Registry

```python
MODEL_REGISTRY = {
    "gemini-3.1-pro": {
        "id": "gemini-3.1-pro-preview",
        "provider": "gemini",
        "context": 1_000_000,
        "label": "Gemini 3.1 Pro",
        "tier": "default",
        "pricing": {"input": 2.00, "output": 12.00},  # per 1M tokens
    },
    "claude-sonnet-4.6": {
        "id": "anthropic/claude-sonnet-4.6",
        "provider": "openrouter",
        "context": 1_000_000,
        "label": "Claude Sonnet 4.6",
        "tier": "premium",
        "pricing": {"input": 3.00, "output": 15.00},
    },
    "qwen-3.5-plus": {
        "id": "qwen/qwen3.5-plus-02-15",
        "provider": "openrouter",
        "context": 1_000_000,
        "label": "Qwen 3.5 Plus",
        "tier": "value",
        "pricing": {"input": 0.26, "output": 1.56},
    },
    "deepseek-r1": {
        "id": "deepseek/deepseek-r1-0528",
        "provider": "openrouter",
        "context": 163_840,
        "label": "DeepSeek R1",
        "tier": "budget",
        "pricing": {"input": 0.45, "output": 2.15},
    },
}
```

### Routing Logic

- **Gemini:** direct Google Generative AI API (existing `LLMService` path)
- **All others:** OpenRouter API (OpenAI-compatible format, single `OPENROUTER_API_KEY`)
- The existing `LLMService` already supports OpenRouter — the change is to make the model dynamic per-request instead of per-provider

### Budget Adaptation

`RetrievalBudget.model_window` adapts to the selected model's context size:
- Gemini / Claude / Qwen (1M): `model_window = 1_000_000`
- DeepSeek R1 (164k): `model_window = 163_840`

This automatically constrains SQLStrategy step 2bis (fewer canonical works loaded for smaller context models) and the passage bundle budget.

### API Parameter

```json
POST /graphrag/query
{
    "question": "What did the Stoics believe about fate?",
    "retrieval_mode": "auto",
    "model": "claude-sonnet-4.6"
}
```

If `model` is omitted → `"gemini-3.1-pro"` (default, no change for existing users).

---

## 4. Conversation Threads + Tabbed Responses

### UX Flow

1. User asks a question → response with default model/mode
2. **"Retry with..."** button below the response → dropdown: pick model + mode
3. New response opens in a **tab** next to the first (browser-tab style)
4. Tabs are labeled: `Gemini 3.1 Pro · vector` | `Claude 4.6 · sql` | ...
5. Tabs accumulate — nothing is deleted
6. Each tab has its own citations, metrics, and reasoning trace

### Follow-ups with Context

Each tab maintains an independent conversation thread:

```
Initial question: "What did Chrysippus think about fate?"
    |
    +-- Tab 1 (Gemini · vector)
    |   +-- Initial response
    |   +-- Follow-up: "How does Bobzien interpret this?"
    |   +-- Follow-up response (context = previous turns + accumulated evidence)
    |
    +-- Tab 2 (Claude 4.6 · sql)
        +-- Initial response
        +-- (no follow-up yet)
```

### ConversationThread Data Model

```python
@dataclass
class ConversationThread:
    thread_id: str
    model: str
    retrieval_mode: str
    turns: list[Turn]                           # question + answer pairs
    accumulated_evidence: list[EvidenceBundle]   # all sources found across turns
    reasoning_traces: list[ReasoningTrace]       # one per turn
```

On each follow-up:
- `accumulated_evidence` from previous turns is injected into context (no need to re-retrieve already-found sources)
- The pipeline still runs to find NEW sources related to the follow-up question
- Both are merged before synthesis

### API

```json
POST /graphrag/query
{
    "question": "How does Bobzien interpret this?",
    "thread_id": "abc-123",
    "model": "claude-sonnet-4.6",
    "retrieval_mode": "sql"
}
```

- `thread_id` omitted → new thread
- `thread_id` provided → follow-up with accumulated context
- **Retry button** creates a new thread with the same initial question but different model/mode

### Thread Storage

Threads are stored in-memory on the backend (dict keyed by `thread_id`, `dict[str, ConversationThread]`). No database persistence — threads are ephemeral per server process. A TTL of 30 minutes applies: each API call touching a thread resets its TTL. Cleanup runs lazily on each new request (check and evict expired threads before processing). On server restart, all threads are lost — this is acceptable for a research tool.

---

## 5. Reasoning Trace

### Data Structure

```python
@dataclass
class ReasoningStep:
    node_name: str              # "ClassifyQueryType", "DraftClaimLedger", etc.
    timestamp_ms: int
    duration_ms: int
    model: str | None           # null for ProgrammaticVerify (zero LLM)
    prompt_summary: str         # First line / summary (not full prompt — too heavy)
    full_prompt_tokens: int
    raw_output: str             # Complete LLM response — the raw reasoning
    thinking: str | None        # Chain-of-thought if model supports it (DeepSeek R1, Kimi)
    parsed_result: dict | None  # Structured result after parsing (claims, query type, etc.)
    skipped: bool               # True if node was skipped
    skip_reason: str | None     # "SPECIFIC_ENTITY query type"
```

### Collection

Each LLM call in the FSM appends a `ReasoningStep` to `state.reasoning_trace`. Skipped nodes add a step with `skipped=True` for a complete trace. `ProgrammaticVerify` (zero LLM) adds a step with verification results.

### API Response

```json
{
    "answer": "...",
    "citations": [...],
    "metrics": {
        "latency_ms": 4200,
        "input_tokens": 45000,
        "output_tokens": 1800,
        "estimated_cost_usd": 0.112,
        "quality_badge": "High",
        "quality_score": 0.85,
        "evidence_bundles": 8,
        "unique_works_cited": 5,
        "retrieval_mode_used": "sql"
    },
    "reasoning_trace": [
        {
            "node": "ClassifyQueryType",
            "duration_ms": 340,
            "model": "gemini-3.1-pro-preview",
            "skipped": false,
            "raw_output": "Query type: COMPARATIVE\nReasoning: ...",
            "thinking": null,
            "parsed_result": {"query_type": "comparative", "confidence": 0.92}
        }
    ]
}
```

### UI — "Reasoning" Tab in Right Panel

- **"Reasoning"** tab alongside existing sources/citations tabs
- Vertical timeline of FSM nodes, one block per step
- Each block: node name, model used, duration, skipped badge
- Click to expand `raw_output` + `thinking`
- Skipped nodes are greyed out with reason
- When switching conversation tabs, the reasoning panel follows the active thread
- Multiple turns in a thread: traces stacked chronologically with turn separator

### Thinking Field

- **DeepSeek R1, Kimi K2.5:** `thinking` captures the separate chain-of-thought (these models expose it natively)
- **Gemini, Claude, Qwen:** `thinking` is null — reasoning is embedded in `raw_output`

---

## 6. Scope of Change

### Files Changed

| Component | File | Change |
|---|---|---|
| **New** | `graphrag/src/eleutheria_graphrag/services/retrieval_strategy.py` | `RetrievalStrategy` protocol, `VectorStrategy`, `SQLStrategy` |
| **New** | `graphrag/src/eleutheria_graphrag/services/model_registry.py` | Model registry, pricing metadata, OpenRouter routing helper |
| Modified | `graphrag/src/eleutheria_graphrag/agents/graph_nodes.py` | `_discover_corpus()` delegates to strategy; all LLM calls append `ReasoningStep` |
| Modified | `graphrag/src/eleutheria_graphrag/agents/state.py` | Add `reasoning_trace`, `retrieval_mode`, `model` to `PipelineState`; adapt `RetrievalBudget` |
| Modified | `graphrag/src/eleutheria_graphrag/agents/pipeline_config.py` | Add `retrieval_mode`, `model` parameters |
| Modified | `graphrag/src/eleutheria_graphrag/services/llm_service.py` | Accept dynamic model per-call, route non-Gemini to OpenRouter |
| Modified | `graphrag/src/eleutheria_graphrag/services/graphrag_service.py` | Thread management (in-memory dict, TTL), strategy instantiation |
| Modified | `backend/routes/graphrag.py` | Accept `retrieval_mode`, `model`, `thread_id` params; return `reasoning_trace` + `metrics` |
| Modified | `frontend/src/pages/GraphRAGPage/` | Model/mode selector, Retry button, tabbed responses, follow-up input |
| Modified | `frontend/src/components/` | New: `ReasoningPanel`, `ResponseTabs`, `ModelSelector` components |

### Files NOT Changed

- Database schema (0 migrations)
- KG ontology
- Qdrant collections or embedding pipeline
- Existing search endpoint
- Existing streaming SSE (still works for single-response mode)

### New Dependencies

- None for backend (OpenRouter uses the same `httpx` / `aiohttp` already in use for OpenRouter fallback)
- None for frontend (tabs and panels use existing UI primitives)

---

## Model Comparison Reference (March 2026)

| Model | Context | Input/1M | Output/1M | Best for |
|---|---|---|---|---|
| Gemini 3.1 Pro | 1M | $2.00 | $12.00 | Default, massive context, good at Greek |
| Claude Sonnet 4.6 | 1M | $3.00 | $15.00 | Best scholarly reasoning, nuance, hedging |
| Qwen 3.5 Plus | 1M | $0.26 | $1.56 | Best value for 1M context (8x cheaper than Gemini) |
| DeepSeek R1 | 164k | $0.45 | $2.15 | Deep reasoning, budget option, free tier available |

Sources:
- [OpenRouter pricing](https://openrouter.ai/pricing)
- [Gemini 3.1 Pro pricing](https://ai.google.dev/gemini-api/docs/pricing)
- [Claude Sonnet 4.6 on OpenRouter](https://openrouter.ai/anthropic/claude-sonnet-4.6)
- [Qwen 3.5 Plus on OpenRouter](https://openrouter.ai/qwen/qwen3.5-plus-02-15)
- [DeepSeek R1 on OpenRouter](https://openrouter.ai/deepseek/deepseek-r1-0528)
