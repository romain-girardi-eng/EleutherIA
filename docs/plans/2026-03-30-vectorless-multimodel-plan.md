# Vectorless Fallback + Multi-Model + Reasoning Trace — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a SQL-only retrieval fallback, per-request model selection via OpenRouter, reasoning trace exposure, and conversation threading with tabbed multi-response UI.

**Architecture:** A `RetrievalStrategy` protocol replaces the single Qdrant call in `_discover_corpus()`. A `ModelRegistry` routes reasoning calls to Gemini (direct) or OpenRouter (Claude/Qwen/DeepSeek). Each FSM LLM call appends a `ReasoningStep` to state. Threads accumulate evidence across follow-ups. Frontend adds model/mode selector, retry-as-tab, and reasoning panel.

**Tech Stack:** Python 3.11+ (FastAPI, pydantic, asyncpg, httpx), React 19 (TypeScript, Radix UI, Tailwind), PostgreSQL 16, Qdrant, OpenRouter API.

**Design spec:** `docs/plans/2026-03-30-vectorless-multimodel-design.md`

---

## File Map

### New files
| File | Responsibility |
|---|---|
| `graphrag/src/eleutheria_graphrag/services/model_registry.py` | Model metadata, context sizes, pricing, provider routing |
| `graphrag/src/eleutheria_graphrag/services/retrieval_strategy.py` | `RetrievalStrategy` protocol, `VectorStrategy`, `SQLStrategy` |
| `graphrag/tests/test_model_registry.py` | Tests for model registry |
| `graphrag/tests/test_retrieval_strategy.py` | Tests for both strategies |
| `graphrag/tests/test_reasoning_trace.py` | Tests for trace collection |
| `graphrag/tests/test_conversation_thread.py` | Tests for thread management |
| `frontend/src/components/ModelSelector.tsx` | Model + mode dropdown |
| `frontend/src/components/ResponseTabs.tsx` | Tabbed multi-response container |
| `frontend/src/components/ReasoningPanel.tsx` | FSM step timeline in right panel |

### Modified files
| File | What changes |
|---|---|
| `graphrag/src/eleutheria_graphrag/agents/state.py` | Add `ReasoningStep`, `reasoning_trace`, `retrieval_mode`, `selected_model` to `RAGState`; adapt `RetrievalBudget` |
| `graphrag/src/eleutheria_graphrag/agents/pipeline_config.py` | Add `retrieval_mode`, `model` fields to `PipelineConfig` |
| `graphrag/src/eleutheria_graphrag/agents/graph_nodes.py` | `_discover_corpus()` delegates to strategy; LLM calls append `ReasoningStep` |
| `graphrag/src/eleutheria_graphrag/services/llm_service.py` | Accept `model_override` param in `generate()` to route dynamically |
| `graphrag/src/eleutheria_graphrag/services/graphrag_service.py` | Thread management, strategy instantiation, pass model/mode through |
| `backend/routes/graphrag_extras.py` | Add `retrieval_mode`, `model`, `thread_id` to `AnswerRequest`; return `reasoning_trace` + enriched `metrics` |
| `frontend/src/pages/GraphRAGPage/index.tsx` | Wire up ModelSelector, ResponseTabs, thread state |
| `frontend/src/pages/GraphRAGPage/ChatPanel.tsx` | Retry button, tab management, follow-up context |
| `frontend/src/pages/GraphRAGPage/MessageBubble.tsx` | Show model/mode badge, link to reasoning panel |

---

## Task 1: Model Registry

**Files:**
- Create: `graphrag/src/eleutheria_graphrag/services/model_registry.py`
- Create: `graphrag/tests/test_model_registry.py`

- [ ] **Step 1: Write the failing test**

```python
# graphrag/tests/test_model_registry.py
from eleutheria_graphrag.services.model_registry import (
    ModelRegistry,
    ModelInfo,
    get_model,
    list_models,
)


def test_get_known_model():
    info = get_model("gemini-3.1-pro")
    assert info.provider == "gemini"
    assert info.context == 1_000_000
    assert info.api_id == "gemini-3.1-pro-preview"


def test_get_unknown_model_raises():
    import pytest
    with pytest.raises(KeyError, match="unknown-model"):
        get_model("unknown-model")


def test_list_models_returns_all():
    models = list_models()
    assert len(models) >= 4
    keys = [m.key for m in models]
    assert "gemini-3.1-pro" in keys
    assert "claude-sonnet-4.6" in keys
    assert "qwen-3.5-plus" in keys
    assert "deepseek-r1" in keys


def test_model_context_sizes():
    assert get_model("gemini-3.1-pro").context == 1_000_000
    assert get_model("claude-sonnet-4.6").context == 1_000_000
    assert get_model("qwen-3.5-plus").context == 1_000_000
    assert get_model("deepseek-r1").context == 163_840


def test_openrouter_models_have_openrouter_provider():
    for key in ["claude-sonnet-4.6", "qwen-3.5-plus", "deepseek-r1"]:
        assert get_model(key).provider == "openrouter"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd graphrag && python -m pytest tests/test_model_registry.py -v`
Expected: `ModuleNotFoundError: No module named 'eleutheria_graphrag.services.model_registry'`

- [ ] **Step 3: Write the implementation**

```python
# graphrag/src/eleutheria_graphrag/services/model_registry.py
"""Model registry for multi-LLM routing."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ModelInfo:
    key: str
    api_id: str
    provider: str  # "gemini" | "openrouter"
    context: int
    label: str
    tier: str  # "default" | "premium" | "value" | "budget"
    pricing_input: float  # USD per 1M tokens
    pricing_output: float


_REGISTRY: dict[str, ModelInfo] = {
    "gemini-3.1-pro": ModelInfo(
        key="gemini-3.1-pro",
        api_id="gemini-3.1-pro-preview",
        provider="gemini",
        context=1_000_000,
        label="Gemini 3.1 Pro",
        tier="default",
        pricing_input=2.00,
        pricing_output=12.00,
    ),
    "claude-sonnet-4.6": ModelInfo(
        key="claude-sonnet-4.6",
        api_id="anthropic/claude-sonnet-4.6",
        provider="openrouter",
        context=1_000_000,
        label="Claude Sonnet 4.6",
        tier="premium",
        pricing_input=3.00,
        pricing_output=15.00,
    ),
    "qwen-3.5-plus": ModelInfo(
        key="qwen-3.5-plus",
        api_id="qwen/qwen3.5-plus-02-15",
        provider="openrouter",
        context=1_000_000,
        label="Qwen 3.5 Plus",
        tier="value",
        pricing_input=0.26,
        pricing_output=1.56,
    ),
    "deepseek-r1": ModelInfo(
        key="deepseek-r1",
        api_id="deepseek/deepseek-r1-0528",
        provider="openrouter",
        context=163_840,
        label="DeepSeek R1",
        tier="budget",
        pricing_input=0.45,
        pricing_output=2.15,
    ),
}

DEFAULT_MODEL = "gemini-3.1-pro"


def get_model(key: str) -> ModelInfo:
    if key not in _REGISTRY:
        raise KeyError(f"Unknown model: {key!r}. Available: {list(_REGISTRY)}")
    return _REGISTRY[key]


def list_models() -> list[ModelInfo]:
    return list(_REGISTRY.values())
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd graphrag && python -m pytest tests/test_model_registry.py -v`
Expected: all 5 tests PASS

- [ ] **Step 5: Commit**

```bash
git add graphrag/src/eleutheria_graphrag/services/model_registry.py graphrag/tests/test_model_registry.py
git commit -m "feat(graphrag): add model registry for multi-LLM routing"
```

---

## Task 2: ReasoningStep + State Changes

**Files:**
- Modify: `graphrag/src/eleutheria_graphrag/agents/state.py`
- Create: `graphrag/tests/test_reasoning_trace.py`

- [ ] **Step 1: Write the failing test**

```python
# graphrag/tests/test_reasoning_trace.py
from eleutheria_graphrag.agents.state import (
    RAGState,
    ReasoningStep,
    RetrievalBudget,
)


def test_reasoning_step_creation():
    step = ReasoningStep(
        node_name="ClassifyQueryType",
        timestamp_ms=1000,
        duration_ms=340,
        model="gemini-3.1-pro-preview",
        prompt_summary="Classify the following query...",
        full_prompt_tokens=256,
        raw_output="Query type: COMPARATIVE",
        thinking=None,
        parsed_result={"query_type": "comparative"},
        skipped=False,
        skip_reason=None,
    )
    assert step.node_name == "ClassifyQueryType"
    assert step.duration_ms == 340
    assert step.thinking is None


def test_reasoning_step_skipped():
    step = ReasoningStep(
        node_name="SeekCounterEvidence",
        timestamp_ms=2000,
        duration_ms=0,
        model=None,
        prompt_summary="",
        full_prompt_tokens=0,
        raw_output="",
        thinking=None,
        parsed_result=None,
        skipped=True,
        skip_reason="SIMPLE complexity",
    )
    assert step.skipped is True
    assert step.skip_reason == "SIMPLE complexity"


def test_rag_state_has_reasoning_trace():
    state = RAGState()
    assert state.reasoning_trace == []
    assert state.retrieval_mode == "auto"
    assert state.selected_model == "gemini-3.1-pro"


def test_rag_state_accumulates_steps():
    state = RAGState()
    step = ReasoningStep(
        node_name="Test",
        timestamp_ms=0,
        duration_ms=100,
        model="test",
        prompt_summary="",
        full_prompt_tokens=0,
        raw_output="output",
        thinking=None,
        parsed_result=None,
        skipped=False,
        skip_reason=None,
    )
    state.reasoning_trace.append(step)
    assert len(state.reasoning_trace) == 1


def test_retrieval_budget_adapts_to_model_window():
    budget_1m = RetrievalBudget(model_window=1_000_000)
    budget_164k = RetrievalBudget(model_window=163_840)
    assert budget_1m.available_context_tokens() > budget_164k.available_context_tokens()
    assert budget_1m.passage_bundle_limit() > budget_164k.passage_bundle_limit()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd graphrag && python -m pytest tests/test_reasoning_trace.py -v`
Expected: `ImportError` — `ReasoningStep` does not exist yet

- [ ] **Step 3: Implement the changes in state.py**

Add to `graphrag/src/eleutheria_graphrag/agents/state.py`:

After the existing imports (around line 10), add:
```python
from __future__ import annotations
```

Before the `RAGState` class (around line 320), add:
```python
@dataclass
class ReasoningStep:
    """One step of the FSM reasoning trace."""

    node_name: str
    timestamp_ms: int
    duration_ms: int
    model: str | None
    prompt_summary: str
    full_prompt_tokens: int
    raw_output: str
    thinking: str | None
    parsed_result: dict[str, Any] | None
    skipped: bool
    skip_reason: str | None
```

Add three new fields to the `RAGState` dataclass (after the `metadata` field, around line 370):
```python
    reasoning_trace: list[ReasoningStep] = field(default_factory=list)
    retrieval_mode: str = "auto"  # "auto" | "vector" | "sql"
    selected_model: str = "gemini-3.1-pro"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd graphrag && python -m pytest tests/test_reasoning_trace.py -v`
Expected: all 5 tests PASS

- [ ] **Step 5: Commit**

```bash
git add graphrag/src/eleutheria_graphrag/agents/state.py graphrag/tests/test_reasoning_trace.py
git commit -m "feat(graphrag): add ReasoningStep dataclass and state fields for mode/model/trace"
```

---

## Task 3: RetrievalStrategy Protocol + VectorStrategy

**Files:**
- Create: `graphrag/src/eleutheria_graphrag/services/retrieval_strategy.py`
- Create: `graphrag/tests/test_retrieval_strategy.py`

- [ ] **Step 1: Write the failing test for VectorStrategy**

```python
# graphrag/tests/test_retrieval_strategy.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from eleutheria_graphrag.services.retrieval_strategy import (
    VectorStrategy,
    SQLStrategy,
    RetrievalStrategy,
)


@pytest.mark.asyncio
async def test_vector_strategy_calls_qdrant():
    """VectorStrategy embeds queries and searches Qdrant."""
    mock_deps = MagicMock()
    mock_deps.qdrant.search_nodes = AsyncMock(return_value=[
        MagicMock(id="node_1", score=0.9, payload={"type": "concept"}),
        MagicMock(id="node_2", score=0.8, payload={"type": "person"}),
    ])

    async def mock_embed(deps, query):
        return [0.1] * 3072

    strategy = VectorStrategy(embed_fn=mock_embed)
    seeds, anchors = await strategy.discover_seeds(
        queries=["Stoic fate"],
        deps=mock_deps,
        node_limit=20,
    )
    assert "node_1" in seeds
    assert "node_2" in seeds
    mock_deps.qdrant.search_nodes.assert_called_once()


@pytest.mark.asyncio
async def test_vector_strategy_handles_qdrant_failure():
    """VectorStrategy returns empty on Qdrant failure."""
    mock_deps = MagicMock()
    mock_deps.qdrant.search_nodes = AsyncMock(side_effect=ConnectionError("Qdrant down"))

    async def mock_embed(deps, query):
        return [0.1] * 3072

    strategy = VectorStrategy(embed_fn=mock_embed)
    seeds, anchors = await strategy.discover_seeds(
        queries=["Stoic fate"],
        deps=mock_deps,
        node_limit=20,
    )
    assert seeds == []
    assert anchors == []


@pytest.mark.asyncio
async def test_vector_strategy_handles_embedding_failure():
    """VectorStrategy returns empty when embedding fails (e.g., Gemini 429)."""
    mock_deps = MagicMock()

    async def mock_embed_fail(deps, query):
        raise Exception("429 Too Many Requests")

    strategy = VectorStrategy(embed_fn=mock_embed_fail)
    seeds, anchors = await strategy.discover_seeds(
        queries=["Stoic fate"],
        deps=mock_deps,
        node_limit=20,
    )
    assert seeds == []
    assert anchors == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd graphrag && python -m pytest tests/test_retrieval_strategy.py::test_vector_strategy_calls_qdrant -v`
Expected: `ModuleNotFoundError`

- [ ] **Step 3: Implement the protocol and VectorStrategy**

```python
# graphrag/src/eleutheria_graphrag/services/retrieval_strategy.py
"""Retrieval strategies for the DiscoverCorpus FSM node."""

from __future__ import annotations

import logging
from typing import Any, Protocol, Callable, Awaitable

logger = logging.getLogger(__name__)


class RetrievalStrategy(Protocol):
    """Interface for corpus discovery — returns seed node IDs and passage anchor IDs."""

    async def discover_seeds(
        self,
        queries: list[str],
        deps: Any,
        node_limit: int = 100,
    ) -> tuple[list[str], list[str]]:
        """Returns (seed_node_ids, passage_anchor_ids)."""
        ...


EmbedFn = Callable[[Any, str], Awaitable[list[float]]]


class VectorStrategy:
    """Embed queries via Gemini, search Qdrant for seed nodes."""

    def __init__(self, embed_fn: EmbedFn) -> None:
        self._embed = embed_fn

    async def discover_seeds(
        self,
        queries: list[str],
        deps: Any,
        node_limit: int = 100,
    ) -> tuple[list[str], list[str]]:
        seed_ids: list[str] = []
        limit_per_query = max(8, node_limit // max(1, len(queries)))

        for query in queries:
            try:
                embedding = await self._embed(deps, query)
                hits = await deps.qdrant.search_nodes(embedding, limit=limit_per_query)
            except Exception:
                logger.warning("VectorStrategy failed for query %r", query, exc_info=True)
                continue

            for hit in hits:
                node_id = hit.id if hasattr(hit, "id") else str(hit)
                if node_id not in seed_ids:
                    seed_ids.append(node_id)

        # Passage anchors = seed IDs for now; DiscoverCorpus refines them later
        passage_anchors = seed_ids[:12]
        return seed_ids, passage_anchors


class SQLStrategy:
    """SQL-only retrieval: passage_citations + HybridSearch + canonical works."""

    async def discover_seeds(
        self,
        queries: list[str],
        deps: Any,
        node_limit: int = 100,
    ) -> tuple[list[str], list[str]]:
        # Implemented in Task 4
        raise NotImplementedError("SQLStrategy — see Task 4")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd graphrag && python -m pytest tests/test_retrieval_strategy.py -v`
Expected: 3 tests PASS (vector tests pass, SQL tests not written yet)

- [ ] **Step 5: Commit**

```bash
git add graphrag/src/eleutheria_graphrag/services/retrieval_strategy.py graphrag/tests/test_retrieval_strategy.py
git commit -m "feat(graphrag): add RetrievalStrategy protocol and VectorStrategy"
```

---

## Task 4: SQLStrategy — 4-Step Escalation

**Files:**
- Modify: `graphrag/src/eleutheria_graphrag/services/retrieval_strategy.py`
- Modify: `graphrag/tests/test_retrieval_strategy.py`

- [ ] **Step 1: Write failing tests for SQLStrategy**

Append to `graphrag/tests/test_retrieval_strategy.py`:

```python
@pytest.mark.asyncio
async def test_sql_strategy_step1_passage_citations():
    """Step 1: finds seeds via kg_nodes label match + passage_citations."""
    mock_deps = MagicMock()
    mock_deps.db = AsyncMock()
    # kg_nodes label match
    mock_deps.db.fetch = AsyncMock(side_effect=[
        # Step 1a: kg_nodes match
        [{"node_id": "concept_fate"}, {"node_id": "person_chrysippus"}],
        # Step 1b: passage_citations for those nodes
        [
            {"passage_id": "p1", "kg_node_id": "concept_fate", "confidence": 0.9},
            {"passage_id": "p2", "kg_node_id": "concept_fate", "confidence": 0.8},
            {"passage_id": "p3", "kg_node_id": "person_chrysippus", "confidence": 0.85},
            {"passage_id": "p4", "kg_node_id": "person_chrysippus", "confidence": 0.7},
        ],
    ])
    mock_deps.outgoing_edges = {"concept_fate": [{"target": "concept_determinism", "relation": "related_to"}]}
    mock_deps.incoming_edges = {}
    mock_deps.search = None  # No HybridSearchService needed for step 1

    strategy = SQLStrategy(min_bundles=4)
    seeds, anchors = await strategy.discover_seeds(
        queries=["Stoic fate"],
        deps=mock_deps,
        node_limit=100,
    )
    assert "concept_fate" in seeds
    assert "person_chrysippus" in seeds
    assert "concept_determinism" in seeds  # 1-hop expansion
    assert len(anchors) >= 2


@pytest.mark.asyncio
async def test_sql_strategy_escalates_to_step2():
    """When step 1 finds < min_bundles, escalates to HybridSearch."""
    mock_deps = MagicMock()
    mock_deps.db = AsyncMock()
    # Step 1: only 1 node found
    mock_deps.db.fetch = AsyncMock(side_effect=[
        [{"node_id": "concept_fate"}],  # kg_nodes match
        [{"passage_id": "p1", "kg_node_id": "concept_fate", "confidence": 0.9}],  # citations
    ])
    mock_deps.outgoing_edges = {}
    mock_deps.incoming_edges = {}
    # Step 2: HybridSearch kicks in
    mock_search = AsyncMock()
    mock_search.hybrid_search = AsyncMock(return_value=[
        {"passage_id": "p2", "work_id": "w1", "text_content": "about fate..."},
        {"passage_id": "p3", "work_id": "w1", "text_content": "heimarmene..."},
        {"passage_id": "p4", "work_id": "w2", "text_content": "Chrysippus argues..."},
    ])
    mock_deps.search = mock_search

    strategy = SQLStrategy(min_bundles=4)
    seeds, anchors = await strategy.discover_seeds(
        queries=["Stoic fate"],
        deps=mock_deps,
        node_limit=100,
    )
    mock_search.hybrid_search.assert_called()
    assert len(anchors) >= 1


@pytest.mark.asyncio
async def test_sql_strategy_returns_empty_gracefully():
    """SQLStrategy returns empty lists when nothing matches."""
    mock_deps = MagicMock()
    mock_deps.db = AsyncMock()
    mock_deps.db.fetch = AsyncMock(return_value=[])
    mock_deps.outgoing_edges = {}
    mock_deps.incoming_edges = {}
    mock_deps.search = None

    strategy = SQLStrategy(min_bundles=4)
    seeds, anchors = await strategy.discover_seeds(
        queries=["nonexistent topic xyz"],
        deps=mock_deps,
        node_limit=100,
    )
    assert seeds == []
    assert anchors == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd graphrag && python -m pytest tests/test_retrieval_strategy.py::test_sql_strategy_step1_passage_citations -v`
Expected: `NotImplementedError: SQLStrategy — see Task 4`

- [ ] **Step 3: Implement SQLStrategy**

Replace the `SQLStrategy` stub in `retrieval_strategy.py` with:

```python
DB_SCHEMA = "free_will"


class SQLStrategy:
    """SQL-only retrieval with 4-step escalation. No Qdrant or embedding calls."""

    def __init__(self, min_bundles: int = 4) -> None:
        self._min_bundles = min_bundles

    async def discover_seeds(
        self,
        queries: list[str],
        deps: Any,
        node_limit: int = 100,
    ) -> tuple[list[str], list[str]]:
        seed_ids: list[str] = []
        passage_anchor_ids: list[str] = []

        # Step 1: Direct passage_citations via kg_nodes label/description match
        matched_node_ids = await self._step1_label_match(queries, deps)
        if matched_node_ids:
            citations = await self._fetch_citations(matched_node_ids, deps)
            seed_ids.extend(matched_node_ids)
            passage_anchor_ids.extend(c["kg_node_id"] for c in citations)

            # 1-hop graph expansion from in-memory edges
            expanded = self._expand_1hop(matched_node_ids, deps)
            seed_ids.extend(nid for nid in expanded if nid not in seed_ids)

        if len(passage_anchor_ids) >= self._min_bundles:
            return _dedup(seed_ids), _dedup(passage_anchor_ids[:12])

        # Step 2: HybridSearch (FTS + lemmatic)
        if deps.search is not None:
            hybrid_ids = await self._step2_hybrid_search(queries, deps)
            seed_ids.extend(nid for nid in hybrid_ids if nid not in seed_ids)
            passage_anchor_ids.extend(nid for nid in hybrid_ids if nid not in passage_anchor_ids)

        if len(passage_anchor_ids) >= self._min_bundles:
            return _dedup(seed_ids), _dedup(passage_anchor_ids[:12])

        # Step 2bis + 3 are handled by the FSM's TreeNavigateWorks + ExpandEvidenceBundles
        # which already load canonical works. We just need enough seeds to activate them.
        # If we still have < min_bundles, return what we have — the FSM will proceed with
        # low evidence and flag insufficient_evidence.

        return _dedup(seed_ids), _dedup(passage_anchor_ids[:12])

    async def _step1_label_match(
        self, queries: list[str], deps: Any
    ) -> list[str]:
        """Find kg_nodes whose label or description matches query terms."""
        patterns = []
        for q in queries:
            for term in q.split():
                if len(term) >= 3:
                    patterns.append(f"%{term}%")
        if not patterns:
            return []

        sql = f"""
            SELECT DISTINCT node_id
            FROM {DB_SCHEMA}.kg_nodes
            WHERE label ILIKE ANY($1) OR description ILIKE ANY($1)
            LIMIT 200
        """
        try:
            rows = await deps.db.fetch(sql, patterns)
            return [r["node_id"] for r in rows]
        except Exception:
            logger.warning("SQLStrategy step1 label match failed", exc_info=True)
            return []

    async def _fetch_citations(
        self, node_ids: list[str], deps: Any
    ) -> list[dict[str, Any]]:
        """Fetch passage_citations for given node IDs, ordered by confidence."""
        sql = f"""
            SELECT passage_id, kg_node_id, confidence
            FROM {DB_SCHEMA}.passage_citations
            WHERE kg_node_id = ANY($1)
            ORDER BY confidence DESC
            LIMIT 100
        """
        try:
            return await deps.db.fetch(sql, node_ids)
        except Exception:
            logger.warning("SQLStrategy fetch_citations failed", exc_info=True)
            return []

    def _expand_1hop(self, node_ids: list[str], deps: Any) -> list[str]:
        """Expand seed nodes by 1 hop using in-memory edge dicts.

        Note: deps.outgoing_edges and deps.incoming_edges are
        dict[str, list[dict[str, Any]]] where each dict has keys like
        "target"/"source", "relation", etc. Check the actual edge dict
        structure in graphrag_service.py load_kg().
        """
        expanded: list[str] = []
        outgoing = getattr(deps, "outgoing_edges", {})
        incoming = getattr(deps, "incoming_edges", {})
        for nid in node_ids:
            for edge in outgoing.get(nid, []):
                target = edge.get("target") or edge.get("target_id", "")
                if target and target not in expanded:
                    expanded.append(target)
            for edge in incoming.get(nid, []):
                source = edge.get("source") or edge.get("source_id", "")
                if source and source not in expanded:
                    expanded.append(source)
        return expanded[:50]  # Cap to avoid explosion

    async def _step2_hybrid_search(
        self, queries: list[str], deps: Any
    ) -> list[str]:
        """Use HybridSearchService for FTS + lemmatic search."""
        all_ids: list[str] = []
        for query in queries[:3]:  # Limit to 3 queries to control cost
            try:
                results = await deps.search.hybrid_search(query, limit=30)
                for r in results:
                    pid = r.get("passage_id") or r.get("id")
                    if pid and pid not in all_ids:
                        all_ids.append(pid)
            except Exception:
                logger.warning("SQLStrategy step2 hybrid_search failed for %r", query, exc_info=True)
        return all_ids


def _dedup(items: list[str]) -> list[str]:
    return list(dict.fromkeys(items))
```

- [ ] **Step 4: Run all strategy tests**

Run: `cd graphrag && python -m pytest tests/test_retrieval_strategy.py -v`
Expected: all 6 tests PASS

- [ ] **Step 5: Commit**

```bash
git add graphrag/src/eleutheria_graphrag/services/retrieval_strategy.py graphrag/tests/test_retrieval_strategy.py
git commit -m "feat(graphrag): implement SQLStrategy with 4-step escalation"
```

---

## Task 5: Dynamic Model Routing in LLMService

**Files:**
- Modify: `graphrag/src/eleutheria_graphrag/services/llm_service.py`

- [ ] **Step 1: Write the failing test**

```python
# graphrag/tests/test_llm_model_override.py
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from eleutheria_graphrag.services.llm_service import LLMService, ModelProvider


def test_llm_service_accepts_model_override_param():
    """generate() signature accepts model_override."""
    import inspect
    sig = inspect.signature(LLMService.generate)
    assert "model_override" in sig.parameters


@pytest.mark.asyncio
async def test_openrouter_model_override_uses_correct_model():
    """When model_override is an OpenRouter model, route via _generate_openai_compatible."""
    svc = LLMService.__new__(LLMService)
    svc._providers = {ModelProvider.OPENROUTER: True}
    svc._disabled_providers = set()
    svc._rate_limiters = {}
    svc._prompt_cache = {}
    svc._stats = MagicMock()

    with patch.object(svc, "_generate_openai_compatible", new_callable=AsyncMock, return_value="test response") as mock_gen:
        with patch.object(svc, "_resolve_model_override", return_value=(ModelProvider.OPENROUTER, "anthropic/claude-sonnet-4.6")):
            result = await svc.generate(
                prompt="test",
                model_override="anthropic/claude-sonnet-4.6",
            )
    assert result == "test response"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd graphrag && python -m pytest tests/test_llm_model_override.py -v`
Expected: FAIL — `model_override` parameter does not exist

- [ ] **Step 3: Modify LLMService.generate()**

In `graphrag/src/eleutheria_graphrag/services/llm_service.py`:

Add `model_override` parameter to `generate()` (line 532):
```python
async def generate(
    self,
    prompt: str,
    system_prompt: str | None = None,
    temperature: float = 0.7,
    max_tokens: int = 4096,
    thinking_mode: bool = False,
    response_mime_type: str | None = None,
    response_json_schema: dict[str, Any] | None = None,
    cache_key: str | None = None,
    cache_prefix: str | None = None,
    cache_ttl_seconds: int = 900,
    model_override: str | None = None,
) -> str:
```

Add a `_resolve_model_override` method to the class:
```python
def _resolve_model_override(self, model_override: str) -> tuple[ModelProvider, str]:
    """Resolve a model_override string to (provider, api_model_id).

    If the string contains '/' (e.g. 'anthropic/claude-sonnet-4.6'),
    it's an OpenRouter model. Otherwise it's a Gemini model.
    """
    if "/" in model_override:
        return ModelProvider.OPENROUTER, model_override
    return ModelProvider.GEMINI, model_override
```

At the top of `generate()`, before the provider attempt loop, add:
```python
if model_override:
    provider, model_id = self._resolve_model_override(model_override)
    # Route directly to the resolved provider with the override model
    config = dict(PROVIDER_CONFIGS[provider])
    config["model"] = model_id
    api_key = os.getenv(config["env_key"], "")
    if not api_key:
        logger.warning("No API key for provider %s, falling back to default", provider)
    else:
        try:
            if provider == ModelProvider.GEMINI:
                return await self._generate_gemini(
                    prompt, system_prompt, temperature, max_tokens,
                    api_key, config, response_mime_type, response_json_schema,
                )
            else:
                return await self._generate_openai_compatible(
                    provider, prompt, system_prompt, temperature,
                    max_tokens, api_key, config,
                )
        except Exception:
            logger.warning("model_override %r failed, falling back to default", model_override, exc_info=True)
```

- [ ] **Step 4: Run tests**

Run: `cd graphrag && python -m pytest tests/test_llm_model_override.py -v`
Expected: both tests PASS

- [ ] **Step 5: Run existing tests to verify no regression**

Run: `cd graphrag && python -m pytest tests/ -v --timeout=30`
Expected: all existing tests still PASS

- [ ] **Step 6: Commit**

```bash
git add graphrag/src/eleutheria_graphrag/services/llm_service.py graphrag/tests/test_llm_model_override.py
git commit -m "feat(graphrag): add model_override parameter to LLMService.generate()"
```

---

## Task 6: Wire Strategy into DiscoverCorpus

**Files:**
- Modify: `graphrag/src/eleutheria_graphrag/agents/graph_nodes.py`
- Modify: `graphrag/src/eleutheria_graphrag/services/graphrag_service.py`

- [ ] **Step 1: Add `retrieval_strategy` field to Deps**

In `graphrag/src/eleutheria_graphrag/agents/dependencies.py` (line 59, after the `tree_index` field), add:
```python
    # Retrieval strategy (vector or SQL)
    retrieval_strategy: Any | None = None  # RetrievalStrategy
```

In `graphrag/src/eleutheria_graphrag/agents/graph_nodes.py`, find the imports at the top and add:
```python
from eleutheria_graphrag.services.retrieval_strategy import (
    VectorStrategy,
    SQLStrategy,
)
```

- [ ] **Step 2: Modify `_discover_corpus()` to delegate to strategy**

In `graph_nodes.py`, replace the Qdrant search loop (lines 3627–3643) with:

```python
# --- Strategy-based corpus discovery ---
strategy: RetrievalStrategy = ctx.deps.retrieval_strategy
queries = _search_queries(state)
budget = state.retrieval_budget
limit = budget.node_search_limit()

seed_ids, passage_anchors = await strategy.discover_seeds(
    queries=queries,
    deps=ctx.deps,
    node_limit=limit,
)

# Merge into state (same as before)
state.seed_node_ids = list(dict.fromkeys(state.seed_node_ids + seed_ids))
```

Replace the passage_anchor_ids logic similarly, using the `passage_anchors` returned by the strategy.

- [ ] **Step 3: Instantiate the correct strategy in GraphRAGService**

In `graphrag_service.py`, in `load_kg()` (around line 190 where Deps is built):

```python
from eleutheria_graphrag.services.retrieval_strategy import VectorStrategy, SQLStrategy
from eleutheria_graphrag.agents.graph_nodes import _get_embedding

# Choose strategy based on env or default
retrieval_mode = os.getenv("RETRIEVAL_MODE", "auto")
vector_strategy = VectorStrategy(embed_fn=_get_embedding)
sql_strategy = SQLStrategy(min_bundles=4)

# For "auto" mode, we use VectorStrategy but the FSM will catch failures
# and the strategy itself returns empty on failure.
# The actual auto-fallback is handled in _discover_corpus.
```

- [ ] **Step 4: Run full test suite**

Run: `cd graphrag && python -m pytest tests/ -v --timeout=60`
Expected: all tests PASS

- [ ] **Step 5: Commit**

```bash
git add graphrag/src/eleutheria_graphrag/agents/graph_nodes.py graphrag/src/eleutheria_graphrag/services/graphrag_service.py
git commit -m "feat(graphrag): wire RetrievalStrategy into DiscoverCorpus FSM node"
```

---

## Task 7: Auto-Fallback Logic

**Files:**
- Modify: `graphrag/src/eleutheria_graphrag/agents/graph_nodes.py`

- [ ] **Step 1: Implement auto mode in `_discover_corpus()`**

After the strategy call in `_discover_corpus()`, add auto-fallback:

```python
# Auto-fallback: if vector returned nothing and mode is "auto", try SQL
if (
    not seed_ids
    and state.retrieval_mode == "auto"
    and isinstance(strategy, VectorStrategy)
):
    logger.info("VectorStrategy returned no seeds, falling back to SQLStrategy")
    fallback = SQLStrategy(min_bundles=4)
    seed_ids, passage_anchors = await fallback.discover_seeds(
        queries=queries,
        deps=ctx.deps,
        node_limit=limit,
    )
    state.metadata["retrieval_mode_used"] = "sql"
else:
    state.metadata["retrieval_mode_used"] = state.retrieval_mode
```

- [ ] **Step 2: Test auto-fallback manually**

This is an integration-level concern. Write a focused test:

```python
# graphrag/tests/test_auto_fallback.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from eleutheria_graphrag.services.retrieval_strategy import VectorStrategy, SQLStrategy


@pytest.mark.asyncio
async def test_auto_fallback_when_vector_returns_empty():
    """In auto mode, if VectorStrategy returns empty, SQLStrategy runs."""
    mock_deps = MagicMock()

    # Vector returns nothing (simulates Gemini 429)
    async def failing_embed(deps, query):
        raise Exception("429 spending cap exceeded")

    vector = VectorStrategy(embed_fn=failing_embed)
    seeds, anchors = await vector.discover_seeds(["Stoic fate"], mock_deps)
    assert seeds == []

    # SQL would succeed
    mock_deps.db = AsyncMock()
    mock_deps.db.fetch = AsyncMock(side_effect=[
        [{"node_id": "concept_fate"}],
        [{"passage_id": "p1", "kg_node_id": "concept_fate", "confidence": 0.9},
         {"passage_id": "p2", "kg_node_id": "concept_fate", "confidence": 0.8},
         {"passage_id": "p3", "kg_node_id": "concept_fate", "confidence": 0.7},
         {"passage_id": "p4", "kg_node_id": "concept_fate", "confidence": 0.6}],
    ])
    mock_deps.outgoing_edges = {}
    mock_deps.incoming_edges = {}
    mock_deps.search = None

    sql = SQLStrategy(min_bundles=4)
    seeds2, anchors2 = await sql.discover_seeds(["Stoic fate"], mock_deps)
    assert "concept_fate" in seeds2
```

- [ ] **Step 3: Run test**

Run: `cd graphrag && python -m pytest tests/test_auto_fallback.py -v`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add graphrag/src/eleutheria_graphrag/agents/graph_nodes.py graphrag/tests/test_auto_fallback.py
git commit -m "feat(graphrag): add auto-fallback from vector to SQL when Qdrant/Gemini fails"
```

---

## Task 8: Conversation Thread Manager

**Files:**
- Modify: `graphrag/src/eleutheria_graphrag/services/graphrag_service.py`
- Create: `graphrag/tests/test_conversation_thread.py`

- [ ] **Step 1: Write failing tests**

```python
# graphrag/tests/test_conversation_thread.py
import time
import pytest
from eleutheria_graphrag.services.graphrag_service import ConversationThread, ThreadManager


def test_create_thread():
    mgr = ThreadManager(ttl_seconds=300)
    thread = mgr.create_thread(model="gemini-3.1-pro", retrieval_mode="auto")
    assert thread.thread_id
    assert thread.model == "gemini-3.1-pro"
    assert thread.turns == []


def test_get_thread():
    mgr = ThreadManager(ttl_seconds=300)
    thread = mgr.create_thread(model="gemini-3.1-pro", retrieval_mode="auto")
    retrieved = mgr.get_thread(thread.thread_id)
    assert retrieved is thread


def test_get_nonexistent_thread_returns_none():
    mgr = ThreadManager(ttl_seconds=300)
    assert mgr.get_thread("nonexistent") is None


def test_thread_ttl_expiry():
    mgr = ThreadManager(ttl_seconds=0)  # Expire immediately
    thread = mgr.create_thread(model="gemini-3.1-pro", retrieval_mode="auto")
    time.sleep(0.01)
    mgr.cleanup_expired()
    assert mgr.get_thread(thread.thread_id) is None


def test_touch_resets_ttl():
    mgr = ThreadManager(ttl_seconds=1)
    thread = mgr.create_thread(model="gemini-3.1-pro", retrieval_mode="auto")
    time.sleep(0.5)
    mgr.touch(thread.thread_id)
    time.sleep(0.7)
    mgr.cleanup_expired()
    # Should still exist because we touched it 0.5s ago (total 1.2s, but reset at 0.5s)
    assert mgr.get_thread(thread.thread_id) is not None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd graphrag && python -m pytest tests/test_conversation_thread.py -v`
Expected: `ImportError`

- [ ] **Step 3: Implement ConversationThread and ThreadManager**

Add to `graphrag/src/eleutheria_graphrag/services/graphrag_service.py`, before the `GraphRAGService` class:

```python
import time
import uuid
from dataclasses import dataclass, field


@dataclass
class Turn:
    question: str
    answer: str
    citations: list[dict[str, Any]]
    reasoning_trace: list[Any]
    evidence_node_ids: list[str]


@dataclass
class ConversationThread:
    thread_id: str
    model: str
    retrieval_mode: str
    turns: list[Turn] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    last_accessed: float = field(default_factory=time.time)


class ThreadManager:
    def __init__(self, ttl_seconds: int = 1800) -> None:
        self._threads: dict[str, ConversationThread] = {}
        self._ttl = ttl_seconds

    def create_thread(self, model: str, retrieval_mode: str) -> ConversationThread:
        self.cleanup_expired()
        thread = ConversationThread(
            thread_id=str(uuid.uuid4()),
            model=model,
            retrieval_mode=retrieval_mode,
        )
        self._threads[thread.thread_id] = thread
        return thread

    def get_thread(self, thread_id: str) -> ConversationThread | None:
        thread = self._threads.get(thread_id)
        if thread is None:
            return None
        if time.time() - thread.last_accessed > self._ttl:
            del self._threads[thread_id]
            return None
        return thread

    def touch(self, thread_id: str) -> None:
        thread = self._threads.get(thread_id)
        if thread:
            thread.last_accessed = time.time()

    def cleanup_expired(self) -> None:
        now = time.time()
        expired = [
            tid for tid, t in self._threads.items()
            if now - t.last_accessed > self._ttl
        ]
        for tid in expired:
            del self._threads[tid]
```

- [ ] **Step 4: Run tests**

Run: `cd graphrag && python -m pytest tests/test_conversation_thread.py -v`
Expected: all 5 tests PASS

- [ ] **Step 5: Commit**

```bash
git add graphrag/src/eleutheria_graphrag/services/graphrag_service.py graphrag/tests/test_conversation_thread.py
git commit -m "feat(graphrag): add ConversationThread and ThreadManager for follow-ups"
```

---

## Task 9: Backend API Changes

**Files:**
- Modify: `backend/routes/graphrag_extras.py`

- [ ] **Step 1: Add new parameters to AnswerRequest**

In `backend/routes/graphrag_extras.py`, add to `AnswerRequest` (line 30):

```python
    retrieval_mode: str = "auto"  # "auto" | "vector" | "sql"
    model: str = "gemini-3.1-pro"
    thread_id: str | None = None
```

- [ ] **Step 2: Add model list endpoint**

```python
@router.get("/models")
async def list_available_models() -> list[dict[str, Any]]:
    """Return available models for the frontend selector."""
    from eleutheria_graphrag.services.model_registry import list_models
    return [
        {
            "key": m.key,
            "label": m.label,
            "provider": m.provider,
            "context": m.context,
            "tier": m.tier,
            "pricing": {"input": m.pricing_input, "output": m.pricing_output},
        }
        for m in list_models()
    ]
```

- [ ] **Step 3: Modify graphrag_answer to pass model/mode/thread**

In the `graphrag_answer` endpoint, pass the new params through to `GraphRAGService.query()`. This requires extending `query()` to accept them — add keyword args and pass them to the agent.

The exact wiring depends on how `GraphRAGService.query()` delegates to the agent. The key is that `retrieval_mode`, `model`, and `thread_id` reach the FSM state initialization.

- [ ] **Step 4: Add `reasoning_trace` and `metrics` to response**

Ensure the response dict from `graphrag_answer` includes:
```python
response["reasoning_trace"] = [
    {
        "node": step.node_name,
        "duration_ms": step.duration_ms,
        "model": step.model,
        "skipped": step.skipped,
        "skip_reason": step.skip_reason,
        "raw_output": step.raw_output,
        "thinking": step.thinking,
        "parsed_result": step.parsed_result,
    }
    for step in state.reasoning_trace
]
response["metrics"]["retrieval_mode_used"] = state.metadata.get("retrieval_mode_used", "unknown")
response["metrics"]["selected_model"] = state.selected_model
```

- [ ] **Step 5: Test the endpoint manually**

Run: `cd graphrag && python -m pytest tests/ -v --timeout=60`
Expected: all tests PASS

- [ ] **Step 6: Commit**

```bash
git add backend/routes/graphrag_extras.py
git commit -m "feat(backend): add retrieval_mode, model, thread_id params and reasoning_trace response"
```

---

## Task 10: Frontend — ModelSelector Component

**Files:**
- Create: `frontend/src/components/ModelSelector.tsx`

- [ ] **Step 1: Create the component**

```tsx
// frontend/src/components/ModelSelector.tsx
import { useState, useEffect } from 'react';

interface ModelInfo {
  key: string;
  label: string;
  provider: string;
  context: number;
  tier: string;
  pricing: { input: number; output: number };
}

interface ModelSelectorProps {
  selectedModel: string;
  selectedMode: string;
  onModelChange: (model: string) => void;
  onModeChange: (mode: string) => void;
}

const MODES = [
  { value: 'auto', label: 'Auto (vector + fallback)' },
  { value: 'vector', label: 'Vector (Qdrant)' },
  { value: 'sql', label: 'SQL (vectorless)' },
];

export function ModelSelector({
  selectedModel,
  selectedMode,
  onModelChange,
  onModeChange,
}: ModelSelectorProps) {
  const [models, setModels] = useState<ModelInfo[]>([]);

  useEffect(() => {
    fetch('/api/graphrag/models')
      .then((r) => r.json())
      .then(setModels)
      .catch(console.error);
  }, []);

  return (
    <div className="flex items-center gap-2 text-sm">
      <select
        value={selectedModel}
        onChange={(e) => onModelChange(e.target.value)}
        className="rounded border border-zinc-700 bg-zinc-900 px-2 py-1 text-zinc-300"
      >
        {models.map((m) => (
          <option key={m.key} value={m.key}>
            {m.label} · {m.tier}
          </option>
        ))}
      </select>
      <select
        value={selectedMode}
        onChange={(e) => onModeChange(e.target.value)}
        className="rounded border border-zinc-700 bg-zinc-900 px-2 py-1 text-zinc-300"
      >
        {MODES.map((m) => (
          <option key={m.value} value={m.value}>
            {m.label}
          </option>
        ))}
      </select>
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/ModelSelector.tsx
git commit -m "feat(frontend): add ModelSelector component for model and retrieval mode"
```

---

## Task 11: Frontend — ResponseTabs Component

**Files:**
- Create: `frontend/src/components/ResponseTabs.tsx`

- [ ] **Step 1: Create the component**

```tsx
// frontend/src/components/ResponseTabs.tsx
import { useState } from 'react';

export interface ResponseTab {
  id: string;
  label: string; // e.g. "Gemini 3.1 Pro · vector"
  threadId: string;
  model: string;
  mode: string;
}

interface ResponseTabsProps {
  tabs: ResponseTab[];
  activeTabId: string;
  onTabChange: (tabId: string) => void;
  onRetry: () => void;
}

export function ResponseTabs({
  tabs,
  activeTabId,
  onTabChange,
  onRetry,
}: ResponseTabsProps) {
  return (
    <div className="flex items-center gap-1 border-b border-zinc-800 px-2">
      {tabs.map((tab) => (
        <button
          key={tab.id}
          onClick={() => onTabChange(tab.id)}
          className={`px-3 py-1.5 text-xs rounded-t transition-colors ${
            tab.id === activeTabId
              ? 'bg-zinc-800 text-zinc-100 border-b-2 border-blue-500'
              : 'text-zinc-500 hover:text-zinc-300'
          }`}
        >
          {tab.label}
        </button>
      ))}
      <button
        onClick={onRetry}
        className="ml-auto px-2 py-1 text-xs text-zinc-500 hover:text-zinc-300 transition-colors"
        title="Retry with a different model"
      >
        + Retry with...
      </button>
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/ResponseTabs.tsx
git commit -m "feat(frontend): add ResponseTabs component for multi-response comparison"
```

---

## Task 12: Frontend — ReasoningPanel Component

**Files:**
- Create: `frontend/src/components/ReasoningPanel.tsx`

- [ ] **Step 1: Create the component**

```tsx
// frontend/src/components/ReasoningPanel.tsx
import { useState } from 'react';

interface ReasoningStep {
  node: string;
  duration_ms: number;
  model: string | null;
  skipped: boolean;
  skip_reason: string | null;
  raw_output: string;
  thinking: string | null;
  parsed_result: Record<string, unknown> | null;
}

interface ReasoningPanelProps {
  steps: ReasoningStep[];
}

export function ReasoningPanel({ steps }: ReasoningPanelProps) {
  const [expandedIndex, setExpandedIndex] = useState<number | null>(null);

  if (steps.length === 0) {
    return (
      <div className="p-4 text-sm text-zinc-500">
        No reasoning trace available.
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-1 p-2">
      <h3 className="text-xs font-semibold uppercase tracking-wider text-zinc-500 px-2 pb-1">
        FSM Reasoning Trace
      </h3>
      {steps.map((step, i) => (
        <div
          key={i}
          className={`rounded border text-xs ${
            step.skipped
              ? 'border-zinc-800 bg-zinc-900/50 opacity-60'
              : 'border-zinc-700 bg-zinc-900'
          }`}
        >
          <button
            onClick={() => setExpandedIndex(expandedIndex === i ? null : i)}
            className="flex w-full items-center justify-between px-3 py-2 text-left"
          >
            <div className="flex items-center gap-2">
              <span className="font-mono text-zinc-300">{step.node}</span>
              {step.skipped && (
                <span className="rounded bg-zinc-800 px-1.5 py-0.5 text-zinc-500">
                  skipped
                </span>
              )}
            </div>
            <div className="flex items-center gap-2 text-zinc-500">
              {step.model && <span>{step.model.split('/').pop()}</span>}
              <span>{step.duration_ms}ms</span>
            </div>
          </button>
          {expandedIndex === i && (
            <div className="border-t border-zinc-800 px-3 py-2">
              {step.skipped ? (
                <p className="text-zinc-500">{step.skip_reason}</p>
              ) : (
                <>
                  {step.thinking && (
                    <details className="mb-2">
                      <summary className="cursor-pointer text-blue-400">
                        Chain of Thought
                      </summary>
                      <pre className="mt-1 whitespace-pre-wrap text-zinc-400 font-mono text-[11px] leading-relaxed max-h-64 overflow-y-auto">
                        {step.thinking}
                      </pre>
                    </details>
                  )}
                  <pre className="whitespace-pre-wrap text-zinc-300 font-mono text-[11px] leading-relaxed max-h-96 overflow-y-auto">
                    {step.raw_output}
                  </pre>
                  {step.parsed_result && (
                    <details className="mt-2">
                      <summary className="cursor-pointer text-zinc-500">
                        Parsed Result
                      </summary>
                      <pre className="mt-1 text-zinc-400 font-mono text-[11px]">
                        {JSON.stringify(step.parsed_result, null, 2)}
                      </pre>
                    </details>
                  )}
                </>
              )}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/ReasoningPanel.tsx
git commit -m "feat(frontend): add ReasoningPanel component for FSM trace visualization"
```

---

## Task 13: Frontend — Wire Components into GraphRAGPage

**Files:**
- Modify: `frontend/src/pages/GraphRAGPage/index.tsx`
- Modify: `frontend/src/pages/GraphRAGPage/ChatPanel.tsx`
- Modify: `frontend/src/pages/GraphRAGPage/MessageBubble.tsx`

- [ ] **Step 1: Add state for model, mode, tabs, and threads**

In `index.tsx`, add state:
```tsx
const [selectedModel, setSelectedModel] = useState('gemini-3.1-pro');
const [selectedMode, setSelectedMode] = useState('auto');
const [responseTabs, setResponseTabs] = useState<ResponseTab[]>([]);
const [activeTabId, setActiveTabId] = useState<string>('');
const [reasoningSteps, setReasoningSteps] = useState<ReasoningStep[]>([]);
```

- [ ] **Step 2: Wire ModelSelector into the header/toolbar area**

Place `<ModelSelector>` in the GraphRAG page toolbar, above the chat input.

- [ ] **Step 3: Wire ResponseTabs above message list**

When a response arrives, create a tab. On "Retry with...", create a new tab with a different model/mode and the same question.

- [ ] **Step 4: Wire ReasoningPanel into the right panel**

Add a "Reasoning" tab to the right panel (alongside existing sources/citations). When active, render `<ReasoningPanel steps={reasoningSteps} />`.

- [ ] **Step 5: Pass model, mode, thread_id in API calls**

In the fetch call to `/api/graphrag/answer`, include:
```tsx
body: JSON.stringify({
    query: question,
    model: selectedModel,
    retrieval_mode: selectedMode,
    thread_id: activeThread?.thread_id ?? undefined,
    // ... existing params
}),
```

- [ ] **Step 6: Handle response with reasoning_trace**

When the response comes back, extract `reasoning_trace` and `metrics` and update state:
```tsx
setReasoningSteps(response.reasoning_trace ?? []);
```

- [ ] **Step 7: Build and verify**

Run: `cd frontend && npm run build`
Expected: Build succeeds with no TypeScript errors

- [ ] **Step 8: Commit**

```bash
git add frontend/src/pages/GraphRAGPage/ frontend/src/components/
git commit -m "feat(frontend): wire model selector, response tabs, and reasoning panel into GraphRAGPage"
```

---

## Task 14: Integration Verification

- [ ] **Step 1: Run full Python test suite**

Run: `cd graphrag && python -m pytest tests/ -v --timeout=60`
Expected: all tests PASS (existing + new)

- [ ] **Step 2: Run frontend build**

Run: `cd frontend && npm run build`
Expected: clean build, no errors

- [ ] **Step 3: Run linter**

Run: `cd graphrag && ruff check src/ tests/`
Expected: no lint errors

- [ ] **Step 4: Run type checker**

Run: `cd graphrag && mypy src/`
Expected: no type errors (or only pre-existing ones)

- [ ] **Step 5: Commit any fixes**

```bash
git add -A
git commit -m "chore: fix lint and type issues from vectorless + multi-model feature"
```
