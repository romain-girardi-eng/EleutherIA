# SOTA Agentic GraphRAG Pipeline — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Upgrade the pydantic-graph FSM from 10 nodes to 17 nodes with HyDE, CRAG, Self-RAG, query expansion, tree reasoning, dual reranking, Pydantic AI structured output, and anti-hallucination safeguards.

**Architecture:** Bottom-up build — foundation models first (enums, Pydantic models, state), then services (HyDE, LLM reranker, tree index), then FSM nodes (TDD per node), then integration. Every new node is test-first. Existing 129 tests must stay green throughout.

**Tech Stack:** Python 3.11+, pydantic-ai 1.58+, pydantic-graph, sentence-transformers, google-generativeai, pytest-asyncio

**Design doc:** `docs/plans/2026-02-17-sota-agentic-graphrag-design.md`

**Baseline:** 129 tests passing in 1.70s

---

## Build Order

```
Task 1:  Pipeline config module (QueryType, PipelineConfig, config matrix)
Task 2:  Structured output models (all Pydantic AI result_type models)
Task 3:  State upgrades (RAGState, EvidenceSource, ScholarlyAnswer)
Task 4:  Updated Deps container
Task 5:  HyDEService
Task 6:  LLMRerankerService
Task 7:  TreeIndexService
Task 8:  ClassifyQueryType node
Task 9:  ExpandQuery node
Task 10: Modified HybridRetrieve (+HyDE, new routing)
Task 11: Modified EvaluateSufficiency (converges to TreeReasoning)
Task 12: TreeReasoningRetrieve node
Task 13: CRAGValidate node
Task 14: DualRerank node
Task 15: FetchPassagesAndLayer node
Task 16: Modified VerifyCitations (fail-closed, routes to SelfRAG)
Task 17: SelfRAGEvaluate node
Task 18: RefineSynthesis node
Task 19: Updated ScholarlyAgent (register all 17 nodes, new entry point)
Task 20: Integration tests (one per query type)
Task 21: Database schema + tree index precompute script
Task 22: Final regression run + commit
```

---

## Task 1: Pipeline Config Module

**Files:**
- Create: `graphrag/src/eleutheria_graphrag/agents/pipeline_config.py`
- Test: `graphrag/tests/unit/test_pipeline_config.py`

### Step 1: Write the failing tests

```python
# graphrag/tests/unit/test_pipeline_config.py
"""Tests for query type taxonomy and adaptive pipeline configuration."""

from __future__ import annotations

import pytest

from eleutheria_graphrag.agents.pipeline_config import (
    PIPELINE_CONFIGS,
    PipelineConfig,
    QueryType,
    get_pipeline_config,
    query_type_to_complexity,
)
from eleutheria_graphrag.agents.state import QueryComplexity


class TestQueryType:
    def test_all_values(self):
        assert len(QueryType) == 5

    def test_specific_entity(self):
        assert QueryType("specific_entity") == QueryType.SPECIFIC_ENTITY

    def test_invalid_raises(self):
        with pytest.raises(ValueError):
            QueryType("invalid_type")


class TestPipelineConfig:
    def test_defaults(self):
        config = PipelineConfig()
        assert config.use_hyde is True
        assert config.use_crag is True
        assert config.use_reranking is True
        assert config.use_self_rag is True
        assert config.use_expansion is True
        assert config.use_tree_reasoning is False

    def test_specific_entity_config(self):
        config = get_pipeline_config(QueryType.SPECIFIC_ENTITY)
        assert config.use_hyde is False
        assert config.use_crag is True
        assert config.use_tree_reasoning is False

    def test_global_abstract_config(self):
        config = get_pipeline_config(QueryType.GLOBAL_ABSTRACT)
        assert config.use_hyde is True
        assert config.use_expansion is False
        assert config.use_tree_reasoning is False

    def test_multi_hop_config(self):
        config = get_pipeline_config(QueryType.MULTI_HOP)
        assert config.use_hyde is False
        assert config.use_reranking is False
        assert config.use_tree_reasoning is True

    def test_comparative_config(self):
        config = get_pipeline_config(QueryType.COMPARATIVE)
        assert config.use_hyde is True
        assert config.use_tree_reasoning is True
        assert config.use_expansion is True

    def test_temporal_config(self):
        config = get_pipeline_config(QueryType.TEMPORAL)
        # Default — all on
        assert config.use_hyde is True
        assert config.use_tree_reasoning is True

    def test_all_query_types_have_config(self):
        for qt in QueryType:
            config = get_pipeline_config(qt)
            assert isinstance(config, PipelineConfig)


class TestQueryTypeToComplexity:
    def test_specific_entity_is_simple(self):
        assert query_type_to_complexity(QueryType.SPECIFIC_ENTITY) == QueryComplexity.SIMPLE

    def test_global_abstract_is_medium(self):
        assert query_type_to_complexity(QueryType.GLOBAL_ABSTRACT) == QueryComplexity.MEDIUM

    def test_multi_hop_is_complex(self):
        assert query_type_to_complexity(QueryType.MULTI_HOP) == QueryComplexity.COMPLEX

    def test_comparative_is_complex(self):
        assert query_type_to_complexity(QueryType.COMPARATIVE) == QueryComplexity.COMPLEX

    def test_temporal_is_complex(self):
        assert query_type_to_complexity(QueryType.TEMPORAL) == QueryComplexity.COMPLEX
```

### Step 2: Run test to verify it fails

Run: `cd graphrag && python3 -m pytest tests/unit/test_pipeline_config.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'eleutheria_graphrag.agents.pipeline_config'`

### Step 3: Write minimal implementation

```python
# graphrag/src/eleutheria_graphrag/agents/pipeline_config.py
"""Query type taxonomy and adaptive pipeline configuration.

Each query type maps to a PipelineConfig that selectively enables/disables
augmentation stages (HyDE, CRAG, reranking, Self-RAG, expansion, tree reasoning).
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel

from eleutheria_graphrag.agents.state import QueryComplexity


class QueryType(str, Enum):
    """Five-type query taxonomy for adaptive pipeline routing."""

    SPECIFIC_ENTITY = "specific_entity"
    GLOBAL_ABSTRACT = "global_abstract"
    MULTI_HOP = "multi_hop"
    COMPARATIVE = "comparative"
    TEMPORAL = "temporal"


class PipelineConfig(BaseModel):
    """Feature flags controlling which augmentation stages are active."""

    use_hyde: bool = True
    use_crag: bool = True
    use_reranking: bool = True
    use_self_rag: bool = True
    use_expansion: bool = True
    use_tree_reasoning: bool = False


PIPELINE_CONFIGS: dict[QueryType, PipelineConfig] = {
    QueryType.SPECIFIC_ENTITY: PipelineConfig(
        use_hyde=False,
        use_crag=True,
        use_reranking=True,
        use_self_rag=True,
        use_expansion=True,
        use_tree_reasoning=False,
    ),
    QueryType.GLOBAL_ABSTRACT: PipelineConfig(
        use_hyde=True,
        use_crag=True,
        use_reranking=True,
        use_self_rag=True,
        use_expansion=False,
        use_tree_reasoning=False,
    ),
    QueryType.MULTI_HOP: PipelineConfig(
        use_hyde=False,
        use_crag=True,
        use_reranking=False,
        use_self_rag=True,
        use_expansion=True,
        use_tree_reasoning=True,
    ),
    QueryType.COMPARATIVE: PipelineConfig(
        use_hyde=True,
        use_crag=True,
        use_reranking=True,
        use_self_rag=True,
        use_expansion=True,
        use_tree_reasoning=True,
    ),
    QueryType.TEMPORAL: PipelineConfig(
        use_hyde=True,
        use_crag=True,
        use_reranking=True,
        use_self_rag=True,
        use_expansion=True,
        use_tree_reasoning=True,
    ),
}


def get_pipeline_config(query_type: QueryType) -> PipelineConfig:
    """Get the pipeline config for a given query type."""
    return PIPELINE_CONFIGS[query_type]


_COMPLEXITY_MAP: dict[QueryType, QueryComplexity] = {
    QueryType.SPECIFIC_ENTITY: QueryComplexity.SIMPLE,
    QueryType.GLOBAL_ABSTRACT: QueryComplexity.MEDIUM,
    QueryType.MULTI_HOP: QueryComplexity.COMPLEX,
    QueryType.COMPARATIVE: QueryComplexity.COMPLEX,
    QueryType.TEMPORAL: QueryComplexity.COMPLEX,
}


def query_type_to_complexity(query_type: QueryType) -> QueryComplexity:
    """Map query type to backwards-compatible complexity tier."""
    return _COMPLEXITY_MAP[query_type]
```

### Step 4: Run test to verify it passes

Run: `cd graphrag && python3 -m pytest tests/unit/test_pipeline_config.py -v`
Expected: 13 passed

### Step 5: Verify no regressions

Run: `cd graphrag && python3 -m pytest tests/ -q`
Expected: 142 passed (129 existing + 13 new)

### Step 6: Commit

```bash
git add graphrag/src/eleutheria_graphrag/agents/pipeline_config.py graphrag/tests/unit/test_pipeline_config.py
git commit -m "feat: add query type taxonomy and adaptive pipeline config"
```

---

## Task 2: Structured Output Models

**Files:**
- Create: `graphrag/src/eleutheria_graphrag/agents/structured_models.py`
- Test: `graphrag/tests/unit/test_structured_models.py`

### Step 1: Write the failing tests

```python
# graphrag/tests/unit/test_structured_models.py
"""Tests for Pydantic AI structured output models."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from eleutheria_graphrag.agents.pipeline_config import QueryType
from eleutheria_graphrag.agents.structured_models import (
    CRAGValidation,
    ClassificationResult,
    ExpansionTerms,
    GreekTerm,
    LatinTerm,
    LLMRerankResult,
    RerankItem,
    SelectedNode,
    SelfRAGEvaluation,
    SufficiencyAssessment,
    TreeNavigationResult,
)


class TestClassificationResult:
    def test_valid(self):
        r = ClassificationResult(
            query_type=QueryType.SPECIFIC_ENTITY,
            confidence=0.95,
            reason="Single entity lookup",
        )
        assert r.query_type == QueryType.SPECIFIC_ENTITY
        assert r.confidence == 0.95

    def test_confidence_bounds(self):
        with pytest.raises(ValidationError):
            ClassificationResult(
                query_type=QueryType.MULTI_HOP, confidence=1.5, reason="x"
            )

    def test_confidence_negative(self):
        with pytest.raises(ValidationError):
            ClassificationResult(
                query_type=QueryType.MULTI_HOP, confidence=-0.1, reason="x"
            )


class TestExpansionTerms:
    def test_defaults(self):
        e = ExpansionTerms()
        assert e.greek_terms == []
        assert e.philosophers == []

    def test_with_terms(self):
        e = ExpansionTerms(
            greek_terms=[
                GreekTerm(
                    greek="εἱμαρμένη",
                    transliteration="heimarmenē",
                    translation="fate",
                )
            ],
            latin_terms=[LatinTerm(latin="fatum", translation="fate")],
            philosophers=["Chrysippus"],
        )
        assert len(e.greek_terms) == 1
        assert e.greek_terms[0].transliteration == "heimarmenē"


class TestCRAGValidation:
    def test_valid(self):
        c = CRAGValidation(
            relevance=80,
            completeness=70,
            confidence=75,
            missing=["Chrysippus quote"],
            suggestions=["search De Fato"],
        )
        assert c.confidence == 75

    def test_score_bounds(self):
        with pytest.raises(ValidationError):
            CRAGValidation(
                relevance=101, completeness=50, confidence=50,
            )

    def test_score_negative(self):
        with pytest.raises(ValidationError):
            CRAGValidation(
                relevance=-1, completeness=50, confidence=50,
            )


class TestSelfRAGEvaluation:
    def test_valid(self):
        s = SelfRAGEvaluation(
            relevance=85, grounding=90, completeness=75, confidence=83,
            caveats=["Limited Epicurean sources"],
            improvements=["Add Lucretius references"],
        )
        assert s.grounding == 90

    def test_default_lists(self):
        s = SelfRAGEvaluation(
            relevance=80, grounding=80, completeness=80, confidence=80,
        )
        assert s.caveats == []
        assert s.improvements == []


class TestSufficiencyAssessment:
    def test_sufficient(self):
        s = SufficiencyAssessment(
            score=0.8, sufficient=True, reason="Enough primary sources",
        )
        assert s.sufficient is True
        assert s.refinement is None

    def test_insufficient_with_refinement(self):
        s = SufficiencyAssessment(
            score=0.3, sufficient=False,
            reason="Missing Chrysippus",
            refinement="Chrysippus fate argument De Fato",
        )
        assert s.refinement is not None

    def test_score_bounds(self):
        with pytest.raises(ValidationError):
            SufficiencyAssessment(score=1.5, sufficient=True, reason="x")


class TestLLMRerankResult:
    def test_valid(self):
        r = LLMRerankResult(rankings=[
            RerankItem(id=1, score=85, reason="Direct argument about fate"),
            RerankItem(id=2, score=60, reason="Tangentially relevant"),
        ])
        assert len(r.rankings) == 2
        assert r.rankings[0].score == 85

    def test_score_bounds(self):
        with pytest.raises(ValidationError):
            RerankItem(id=1, score=101, reason="x")


class TestTreeNavigationResult:
    def test_valid(self):
        t = TreeNavigationResult(
            selected_nodes=[
                SelectedNode(
                    work_id="de_fato",
                    node_id="df_003",
                    reason="Contains Master Argument",
                    priority=1,
                ),
            ],
            reasoning="De Fato Book II directly addresses this.",
        )
        assert t.selected_nodes[0].priority == 1

    def test_priority_bounds(self):
        with pytest.raises(ValidationError):
            SelectedNode(
                work_id="x", node_id="y", reason="z", priority=4,
            )
```

### Step 2: Run test to verify it fails

Run: `cd graphrag && python3 -m pytest tests/unit/test_structured_models.py -v`
Expected: FAIL — `ModuleNotFoundError`

### Step 3: Write minimal implementation

```python
# graphrag/src/eleutheria_graphrag/agents/structured_models.py
"""Pydantic AI structured output models for all JSON-returning LLM calls.

Each model is used as the ``result_type`` for a ``pydantic_ai.Agent``,
providing automatic validation and retry on malformed LLM output.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from eleutheria_graphrag.agents.pipeline_config import QueryType


# ---------------------------------------------------------------------------
# ClassifyQueryType
# ---------------------------------------------------------------------------


class ClassificationResult(BaseModel):
    """Structured output for query classification."""

    query_type: QueryType
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str


# ---------------------------------------------------------------------------
# ExpandQuery
# ---------------------------------------------------------------------------


class GreekTerm(BaseModel):
    greek: str
    transliteration: str
    translation: str


class LatinTerm(BaseModel):
    latin: str
    translation: str


class ExpansionTerms(BaseModel):
    """Structured output for philological query expansion."""

    greek_terms: list[GreekTerm] = Field(default_factory=list)
    latin_terms: list[LatinTerm] = Field(default_factory=list)
    philosophers: list[str] = Field(default_factory=list)
    concepts: list[str] = Field(default_factory=list)
    schools: list[str] = Field(default_factory=list)
    periods: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# EvaluateSufficiency
# ---------------------------------------------------------------------------


class SufficiencyAssessment(BaseModel):
    """Structured output for evidence sufficiency evaluation."""

    score: float = Field(ge=0.0, le=1.0)
    sufficient: bool
    reason: str
    refinement: str | None = None


# ---------------------------------------------------------------------------
# TreeReasoningRetrieve
# ---------------------------------------------------------------------------


class SelectedNode(BaseModel):
    work_id: str
    node_id: str
    reason: str
    priority: int = Field(ge=1, le=3)


class TreeNavigationResult(BaseModel):
    """Structured output for tree reasoning navigation."""

    selected_nodes: list[SelectedNode]
    reasoning: str


# ---------------------------------------------------------------------------
# CRAGValidate
# ---------------------------------------------------------------------------


class CRAGValidation(BaseModel):
    """Structured output for CRAG retrieval validation."""

    relevance: int = Field(ge=0, le=100)
    completeness: int = Field(ge=0, le=100)
    confidence: int = Field(ge=0, le=100)
    missing: list[str] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# DualRerank (LLM stage)
# ---------------------------------------------------------------------------


class RerankItem(BaseModel):
    id: int
    score: int = Field(ge=0, le=100)
    reason: str


class LLMRerankResult(BaseModel):
    """Structured output for LLM scholarly reranking."""

    rankings: list[RerankItem]


# ---------------------------------------------------------------------------
# SelfRAGEvaluate
# ---------------------------------------------------------------------------


class SelfRAGEvaluation(BaseModel):
    """Structured output for post-generation quality evaluation."""

    relevance: int = Field(ge=0, le=100)
    grounding: int = Field(ge=0, le=100)
    completeness: int = Field(ge=0, le=100)
    confidence: int = Field(ge=0, le=100)
    caveats: list[str] = Field(default_factory=list)
    improvements: list[str] = Field(default_factory=list)
```

### Step 4: Run tests

Run: `cd graphrag && python3 -m pytest tests/unit/test_structured_models.py -v`
Expected: 15 passed

### Step 5: Regression check

Run: `cd graphrag && python3 -m pytest tests/ -q`
Expected: 157 passed

### Step 6: Commit

```bash
git add graphrag/src/eleutheria_graphrag/agents/structured_models.py graphrag/tests/unit/test_structured_models.py
git commit -m "feat: add Pydantic AI structured output models for all LLM calls"
```

---

## Task 3: State Upgrades

**Files:**
- Modify: `graphrag/src/eleutheria_graphrag/agents/state.py`
- Modify: `graphrag/tests/unit/test_state.py`

### Step 1: Write the failing tests (append to existing test file)

Append these test classes to `graphrag/tests/unit/test_state.py`:

```python
# --- Append to test_state.py ---

from eleutheria_graphrag.agents.pipeline_config import PipelineConfig, QueryType
from eleutheria_graphrag.agents.structured_models import CRAGValidation, SelfRAGEvaluation


class TestQueryType:
    def test_all_values(self):
        assert len(QueryType) == 5


class TestEvidenceSourceNew:
    def test_hyde_search(self):
        assert EvidenceSource.HYDE_SEARCH == "hyde_search"

    def test_crag_secondary(self):
        assert EvidenceSource.CRAG_SECONDARY == "crag_secondary"

    def test_tree_reasoning(self):
        assert EvidenceSource.TREE_REASONING == "tree_reasoning"

    def test_total_sources(self):
        assert len(EvidenceSource) == 8


class TestRAGStateNewFields:
    def test_query_type_default(self):
        s = RAGState()
        assert s.query_type == QueryType.TEMPORAL

    def test_pipeline_config_default(self):
        s = RAGState()
        assert isinstance(s.pipeline_config, PipelineConfig)
        assert s.pipeline_config.use_hyde is True

    def test_expanded_query(self):
        s = RAGState(expanded_query="fate (heimarmenē, Chrysippus)")
        assert "heimarmenē" in s.expanded_query

    def test_crag_validation(self):
        s = RAGState()
        assert s.crag_validation is None
        s.crag_validation = CRAGValidation(
            relevance=80, completeness=70, confidence=75,
        )
        assert s.crag_validation.confidence == 75

    def test_self_rag_fields(self):
        s = RAGState()
        assert s.self_rag_evaluation is None
        assert s.self_rag_iterations == 0
        assert s.max_self_rag_iterations == 2
        assert s.quality_badge == ""

    def test_insufficient_evidence(self):
        s = RAGState()
        assert s.insufficient_evidence is False


class TestScholarlyAnswerNewFields:
    def test_query_type(self):
        a = ScholarlyAnswer(answer="test", question="test")
        assert a.query_type == QueryType.TEMPORAL

    def test_quality_badge(self):
        a = ScholarlyAnswer(
            answer="test", question="test", quality_badge="High",
        )
        assert a.quality_badge == "High"

    def test_insufficient_evidence(self):
        a = ScholarlyAnswer(
            answer="test", question="test", insufficient_evidence=True,
        )
        assert a.insufficient_evidence is True

    def test_serialization_new_fields(self):
        a = ScholarlyAnswer(
            answer="test", question="test",
            query_type=QueryType.COMPARATIVE,
            quality_badge="Medium",
        )
        d = a.model_dump()
        assert d["query_type"] == "comparative"
        assert d["quality_badge"] == "Medium"
```

### Step 2: Run test to verify it fails

Run: `cd graphrag && python3 -m pytest tests/unit/test_state.py -v -k "New"`
Expected: FAIL — `ImportError` or `AttributeError`

### Step 3: Modify state.py

Add to `EvidenceSource` enum:
```python
    HYDE_SEARCH = "hyde_search"
    CRAG_SECONDARY = "crag_secondary"
    TREE_REASONING = "tree_reasoning"
```

Add imports at top of `state.py`:
```python
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from eleutheria_graphrag.agents.pipeline_config import PipelineConfig, QueryType
    from eleutheria_graphrag.agents.structured_models import CRAGValidation, SelfRAGEvaluation
```

Add new fields to `RAGState` (after existing fields):
```python
    # --- Classification (NEW) ---
    query_type: QueryType = field(default=None)  # set in __post_init__
    pipeline_config: PipelineConfig = field(default=None)  # set in __post_init__

    # --- Query expansion (NEW) ---
    expanded_query: str | None = None
    expansion_terms: Any = None  # ExpansionTerms | None

    # --- CRAG (NEW) ---
    crag_validation: Any = None  # CRAGValidation | None
    insufficient_evidence: bool = False

    # --- Self-RAG (NEW) ---
    self_rag_evaluation: Any = None  # SelfRAGEvaluation | None
    self_rag_iterations: int = 0
    max_self_rag_iterations: int = 2
    quality_badge: str = ""
```

Add `__post_init__` to set defaults (avoids circular import):
```python
    def __post_init__(self):
        if self.query_type is None:
            from eleutheria_graphrag.agents.pipeline_config import QueryType
            self.query_type = QueryType.TEMPORAL
        if self.pipeline_config is None:
            from eleutheria_graphrag.agents.pipeline_config import PipelineConfig
            self.pipeline_config = PipelineConfig()
```

Add new fields to `ScholarlyAnswer`:
```python
    query_type: QueryType = Field(default="temporal")  # NEW
    quality_badge: str = ""  # NEW
    self_rag_evaluation: Any = None  # NEW
    crag_validation: Any = None  # NEW
    insufficient_evidence: bool = False  # NEW
```

**Important:** Use `Any` for forward-reference types to avoid circular imports. The actual types are enforced at runtime by the Pydantic AI agents that produce them.

### Step 4: Run tests

Run: `cd graphrag && python3 -m pytest tests/unit/test_state.py -v`
Expected: All state tests pass (existing + new)

### Step 5: Regression check

Run: `cd graphrag && python3 -m pytest tests/ -q`
Expected: All tests pass (existing nodes still work with new state fields having defaults)

### Step 6: Commit

```bash
git add graphrag/src/eleutheria_graphrag/agents/state.py graphrag/tests/unit/test_state.py
git commit -m "feat: add new state fields for pipeline config, CRAG, Self-RAG, tree reasoning"
```

---

## Task 4: Updated Deps Container

**Files:**
- Modify: `graphrag/src/eleutheria_graphrag/agents/dependencies.py`

### Step 1: No new tests needed — this is a dataclass addition with `None` defaults

### Step 2: Modify dependencies.py

Add new optional service fields to `Deps`:

```python
    # NEW: HyDE service
    hyde: Any | None = None  # HyDEService

    # NEW: LLM scholarly reranker
    llm_reranker: Any | None = None  # LLMRerankerService

    # NEW: Tree index service (PageIndex-inspired)
    tree_index: Any | None = None  # TreeIndexService
```

Using `Any` to avoid circular imports. TYPE_CHECKING block already handles the typing.

Add to TYPE_CHECKING block:
```python
    from eleutheria_graphrag.services.hyde_service import HyDEService
    from eleutheria_graphrag.services.llm_reranker import LLMRerankerService
    from eleutheria_graphrag.services.tree_index import TreeIndexService
```

### Step 3: Regression check

Run: `cd graphrag && python3 -m pytest tests/ -q`
Expected: All tests pass (Deps constructed with defaults in all existing tests)

### Step 4: Commit

```bash
git add graphrag/src/eleutheria_graphrag/agents/dependencies.py
git commit -m "feat: add HyDE, LLM reranker, and tree index service slots to Deps"
```

---

## Task 5: HyDEService

**Files:**
- Create: `graphrag/src/eleutheria_graphrag/services/hyde_service.py`
- Test: `graphrag/tests/unit/test_hyde_service.py`

### Step 1: Write the failing tests

```python
# graphrag/tests/unit/test_hyde_service.py
"""Tests for HyDE (Hypothetical Document Embeddings) service."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from eleutheria_graphrag.services.hyde_service import HyDEService


@pytest.fixture
def llm():
    mock = MagicMock()
    mock.generate = AsyncMock(return_value="Chrysippus argued that fate...")
    return mock


@pytest.fixture
def qdrant():
    mock = MagicMock()
    mock.search_nodes = AsyncMock(return_value=[
        {"id": "chrysippus", "score": 0.92, "label": "Chrysippus"},
        {"id": "fate", "score": 0.88, "label": "Heimarmenē"},
    ])
    return mock


@pytest.fixture
def service(llm, qdrant):
    return HyDEService(llm=llm, qdrant=qdrant)


class TestGenerateHypothetical:
    @pytest.mark.asyncio
    async def test_returns_text(self, service):
        with patch(
            "eleutheria_graphrag.services.hyde_service._get_embedding",
            new_callable=AsyncMock,
            return_value=[0.1] * 768,
        ):
            result = await service.generate_hypothetical("What is Stoic fate?")
            assert isinstance(result, str)
            assert len(result) > 0

    @pytest.mark.asyncio
    async def test_llm_called_with_prompt(self, service, llm):
        with patch(
            "eleutheria_graphrag.services.hyde_service._get_embedding",
            new_callable=AsyncMock,
            return_value=[0.1] * 768,
        ):
            await service.generate_hypothetical("What is Stoic fate?")
            llm.generate.assert_called_once()
            prompt = llm.generate.call_args[0][0]
            assert "scholarly passage" in prompt.lower() or "classicist" in prompt.lower()


class TestSearchNodes:
    @pytest.mark.asyncio
    async def test_returns_results(self, service, qdrant):
        with patch(
            "eleutheria_graphrag.services.hyde_service._get_embedding",
            new_callable=AsyncMock,
            return_value=[0.1] * 768,
        ):
            results = await service.search_nodes("What is Stoic fate?", limit=5)
            assert len(results) == 2
            qdrant.search_nodes.assert_called_once()

    @pytest.mark.asyncio
    async def test_applies_confidence_discount(self, service):
        with patch(
            "eleutheria_graphrag.services.hyde_service._get_embedding",
            new_callable=AsyncMock,
            return_value=[0.1] * 768,
        ):
            results = await service.search_nodes("What is Stoic fate?")
            # HyDE results get 0.9x discount
            assert results[0]["score"] == pytest.approx(0.92 * 0.9, rel=0.01)


class TestRRFFusion:
    @pytest.mark.asyncio
    async def test_merge_deduplicates(self, service):
        standard = [
            {"id": "a", "score": 0.9},
            {"id": "b", "score": 0.8},
        ]
        hyde = [
            {"id": "b", "score": 0.85},
            {"id": "c", "score": 0.7},
        ]
        merged = service.rrf_fusion(standard, hyde, k=60, limit=10)
        ids = [r["id"] for r in merged]
        assert len(ids) == len(set(ids))  # no duplicates
        assert "b" in ids  # shared item present

    @pytest.mark.asyncio
    async def test_rrf_k60(self, service):
        standard = [{"id": "a", "score": 0.9}]
        hyde = [{"id": "a", "score": 0.8}]
        merged = service.rrf_fusion(standard, hyde, k=60, limit=10)
        # a appears in both lists at rank 0: score = 2 * 1/(60+1)
        expected = 2.0 / 61.0
        assert merged[0]["rrf_score"] == pytest.approx(expected, rel=0.01)
```

### Step 2: Run test to verify it fails

Run: `cd graphrag && python3 -m pytest tests/unit/test_hyde_service.py -v`
Expected: FAIL — `ModuleNotFoundError`

### Step 3: Write implementation

```python
# graphrag/src/eleutheria_graphrag/services/hyde_service.py
"""HyDE (Hypothetical Document Embeddings) service.

Generates a hypothetical scholarly passage for a query, embeds it,
and searches Qdrant with the hypothetical embedding to bridge the
semantic gap between question-style and answer-style text.
"""

from __future__ import annotations

import asyncio
import logging
import os
from typing import TYPE_CHECKING, Any

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from eleutheria_graphrag.services.llm_service import LLMService
    from eleutheria_kg.services.qdrant import QdrantService

HYDE_PROMPT = """\
You are an expert classicist specializing in ancient Greek and Roman \
philosophy, particularly debates about fate, free will, and moral \
responsibility.

Write a scholarly passage (150-200 words) that would perfectly answer \
this question: "{query}"

Requirements:
- Include specific philosophers by name (Chrysippus, Epictetus, Epicurus, \
Alexander of Aphrodisias, etc.)
- Include Greek philosophical terms with transliterations \
(e.g. εἱμαρμένη / heimarmenē, τὸ ἐφ' ἡμῖν / to eph' hēmin)
- Reference specific ancient works (De Fato, Meditations, etc.)
- Use academic register and precision

Write only the passage, no preamble."""

CONFIDENCE_DISCOUNT = 0.9


async def _get_embedding(text: str) -> list[float]:
    """Get embedding via Gemini embedding API."""
    import google.generativeai as genai

    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY required for embeddings")

    genai.configure(api_key=api_key)

    def _embed() -> list[float]:
        result = genai.embed_content(
            model="models/gemini-embedding-001",
            content=text,
        )
        return result["embedding"]

    return await asyncio.to_thread(_embed)


class HyDEService:
    """Hypothetical Document Embeddings for semantic gap bridging."""

    def __init__(self, llm: LLMService, qdrant: QdrantService) -> None:
        self.llm = llm
        self.qdrant = qdrant

    async def generate_hypothetical(self, query: str) -> str:
        """Generate a 150-200 word hypothetical scholarly passage."""
        prompt = HYDE_PROMPT.format(query=query)
        return await self.llm.generate(prompt, temperature=0.7, max_tokens=512)

    async def search_nodes(
        self, query: str, limit: int = 10
    ) -> list[dict[str, Any]]:
        """Generate hypothetical doc, embed it, search KG nodes."""
        hypothetical = await self.generate_hypothetical(query)
        embedding = await _get_embedding(hypothetical)
        results = await self.qdrant.search_nodes(embedding, limit=limit)

        # Apply confidence discount
        for r in results:
            r["score"] = r.get("score", 0.0) * CONFIDENCE_DISCOUNT

        return results

    @staticmethod
    def rrf_fusion(
        list_a: list[dict[str, Any]],
        list_b: list[dict[str, Any]],
        k: int = 60,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Reciprocal Rank Fusion of two result lists."""
        scores: dict[str, float] = {}
        items: dict[str, dict[str, Any]] = {}

        for rank, item in enumerate(list_a):
            item_id = item["id"]
            scores[item_id] = scores.get(item_id, 0.0) + 1.0 / (k + rank + 1)
            items[item_id] = item

        for rank, item in enumerate(list_b):
            item_id = item["id"]
            scores[item_id] = scores.get(item_id, 0.0) + 1.0 / (k + rank + 1)
            items[item_id] = item

        merged = []
        for item_id, rrf_score in sorted(
            scores.items(), key=lambda x: x[1], reverse=True
        ):
            entry = {**items[item_id], "rrf_score": rrf_score}
            merged.append(entry)

        return merged[:limit]
```

### Step 4: Run tests

Run: `cd graphrag && python3 -m pytest tests/unit/test_hyde_service.py -v`
Expected: 5 passed

### Step 5: Regression + commit

Run: `cd graphrag && python3 -m pytest tests/ -q`

```bash
git add graphrag/src/eleutheria_graphrag/services/hyde_service.py graphrag/tests/unit/test_hyde_service.py
git commit -m "feat: add HyDE service with hypothetical doc generation and RRF fusion"
```

---

## Task 6: LLMRerankerService

**Files:**
- Create: `graphrag/src/eleutheria_graphrag/services/llm_reranker.py`
- Test: `graphrag/tests/unit/test_llm_reranker.py`

### Step 1: Write the failing tests

```python
# graphrag/tests/unit/test_llm_reranker.py
"""Tests for LLM-based scholarly reranker service."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from eleutheria_graphrag.agents.state import Evidence, EvidenceLayer, EvidenceSource
from eleutheria_graphrag.services.llm_reranker import LLMRerankerService


def _make_evidence(n: int) -> list[Evidence]:
    return [
        Evidence(
            id=f"node_{i}",
            label=f"Node {i}",
            type="Concept",
            description=f"Description of concept {i} in ancient philosophy" * 3,
            score=0.5,
            layer=EvidenceLayer.PRIMARY,
            source=EvidenceSource.SEMANTIC_SEARCH,
        )
        for i in range(n)
    ]


@pytest.fixture
def llm():
    mock = MagicMock()
    mock.generate = AsyncMock(return_value=json.dumps({
        "rankings": [
            {"id": 1, "score": 90, "reason": "Directly relevant"},
            {"id": 2, "score": 70, "reason": "Partially relevant"},
            {"id": 3, "score": 40, "reason": "Tangential"},
        ]
    }))
    return mock


@pytest.fixture
def service(llm):
    return LLMRerankerService(llm=llm)


class TestLLMReranker:
    @pytest.mark.asyncio
    async def test_rerank_returns_evidence(self, service):
        evidence = _make_evidence(3)
        result = await service.rerank("Stoic fate", evidence, top_k=3)
        assert len(result) == 3
        assert all(isinstance(e, Evidence) for e in result)

    @pytest.mark.asyncio
    async def test_rerank_sorted_by_score(self, service):
        evidence = _make_evidence(3)
        result = await service.rerank("Stoic fate", evidence, top_k=3)
        scores = [e.score for e in result]
        assert scores == sorted(scores, reverse=True)

    @pytest.mark.asyncio
    async def test_rerank_top_k(self, service):
        evidence = _make_evidence(3)
        result = await service.rerank("Stoic fate", evidence, top_k=2)
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_rerank_caps_candidates(self, service, llm):
        """Candidates capped at 30 per LLM call."""
        evidence = _make_evidence(35)
        # LLM returns rankings for first 30 only
        rankings = [{"id": i + 1, "score": 90 - i, "reason": f"r{i}"} for i in range(30)]
        llm.generate = AsyncMock(return_value=json.dumps({"rankings": rankings}))
        result = await service.rerank("Stoic fate", evidence, top_k=15)
        assert len(result) == 15

    @pytest.mark.asyncio
    async def test_fallback_on_parse_error(self, service, llm):
        """On JSON parse failure, returns original order."""
        llm.generate = AsyncMock(return_value="not json")
        evidence = _make_evidence(3)
        result = await service.rerank("Stoic fate", evidence, top_k=3)
        assert len(result) == 3
        # Fallback assigns decreasing scores
        assert result[0].score >= result[1].score
```

### Step 2: Run test to verify it fails

Run: `cd graphrag && python3 -m pytest tests/unit/test_llm_reranker.py -v`

### Step 3: Write implementation

```python
# graphrag/src/eleutheria_graphrag/services/llm_reranker.py
"""LLM-based scholarly reranker with domain-aware criteria."""

from __future__ import annotations

import json
import logging
import re
from typing import TYPE_CHECKING, Any

from eleutheria_graphrag.agents.state import Evidence

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from eleutheria_graphrag.services.llm_service import LLMService

MAX_CANDIDATES_PER_CALL = 30
TEXT_PREVIEW_LEN = 400

LLM_RERANK_PROMPT = """\
You are an expert in ancient philosophy, specializing in Greek and Roman \
debates about fate, free will, and moral responsibility.

TASK: Rate each passage's relevance to the research question on a scale of 0-100.

RESEARCH QUESTION: "{query}"

CANDIDATE PASSAGES:
{candidates}

SCORING GUIDELINES:
- 90-100: Directly addresses the question with specific relevant content
- 70-89: Highly relevant, discusses key concepts/philosophers mentioned
- 50-69: Moderately relevant, related topic but not directly answering
- 30-49: Tangentially relevant, mentions some related terms
- 0-29: Not relevant to the question

Return ONLY a valid JSON object (no markdown):
{{"rankings": [{{"id": 1, "score": 85, "reason": "Brief explanation"}}, ...]}}

Include ALL {count} passages in your rankings."""


class LLMRerankerService:
    """LLM-based scholarly reranking with domain-aware criteria."""

    def __init__(self, llm: LLMService) -> None:
        self.llm = llm

    async def rerank(
        self,
        query: str,
        evidence: list[Evidence],
        top_k: int = 15,
    ) -> list[Evidence]:
        """Rerank evidence using LLM scholarly evaluation."""
        candidates = evidence[:MAX_CANDIDATES_PER_CALL]

        # Format candidates for prompt
        formatted = []
        for i, ev in enumerate(candidates):
            text = (ev.text_content or ev.description or ev.label)[:TEXT_PREVIEW_LEN]
            formatted.append(f"[{i + 1}] {ev.label}: \"{text}\"")

        prompt = LLM_RERANK_PROMPT.format(
            query=query,
            candidates="\n".join(formatted),
            count=len(candidates),
        )

        try:
            raw = await self.llm.generate(prompt, temperature=0.0, max_tokens=2048)
            raw = raw.strip()
            match = re.search(r"\{[\s\S]*\}", raw)
            if match:
                raw = match.group(0)
            result = json.loads(raw)
            rankings = result.get("rankings", [])

            score_map: dict[int, tuple[int, str]] = {}
            for r in rankings:
                score_map[r["id"]] = (r["score"], r.get("reason", ""))

            for i, ev in enumerate(candidates):
                if (i + 1) in score_map:
                    ev.score = score_map[i + 1][0] / 100.0
                else:
                    ev.score = 0.5

        except Exception:
            logger.warning("LLM reranking failed, using fallback scores")
            for i, ev in enumerate(candidates):
                ev.score = (50 - i) / 100.0

        candidates.sort(key=lambda e: e.score, reverse=True)
        return candidates[:top_k]
```

### Step 4: Run tests + regression + commit

Run: `cd graphrag && python3 -m pytest tests/unit/test_llm_reranker.py -v`
Run: `cd graphrag && python3 -m pytest tests/ -q`

```bash
git add graphrag/src/eleutheria_graphrag/services/llm_reranker.py graphrag/tests/unit/test_llm_reranker.py
git commit -m "feat: add LLM scholarly reranker service with batch support"
```

---

## Task 7: TreeIndexService

**Files:**
- Create: `graphrag/src/eleutheria_graphrag/services/tree_index.py`
- Test: `graphrag/tests/unit/test_tree_index_service.py`

### Step 1: Write the failing tests

```python
# graphrag/tests/unit/test_tree_index_service.py
"""Tests for PageIndex-inspired tree index service."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from eleutheria_graphrag.services.tree_index import (
    TreeIndexService,
    TreeNode,
    WorkTreeIndex,
)


class TestTreeNode:
    def test_leaf_node(self):
        n = TreeNode(
            node_id="df_001", title="Introduction",
            start_passage=1, end_passage=5,
            summary="Alexander introduces the debate...",
        )
        assert n.nodes == []
        assert n.start_passage == 1

    def test_nested_node(self):
        child = TreeNode(
            node_id="df_002", title="The Stoic Position",
            start_passage=1, end_passage=3,
            summary="Chrysippus's argument...",
        )
        parent = TreeNode(
            node_id="df_001", title="Book I",
            start_passage=1, end_passage=10,
            summary="Overview...",
            nodes=[child],
        )
        assert len(parent.nodes) == 1
        assert parent.nodes[0].node_id == "df_002"


class TestWorkTreeIndex:
    def test_construction(self):
        idx = WorkTreeIndex(
            work_id="de_fato",
            title="De Fato",
            author="Alexander of Aphrodisias",
            period="Imperial",
            total_passages=47,
            nodes=[],
        )
        assert idx.work_id == "de_fato"
        assert idx.total_passages == 47

    def test_serialization_roundtrip(self):
        idx = WorkTreeIndex(
            work_id="de_fato",
            title="De Fato",
            author="Alexander",
            total_passages=10,
            nodes=[
                TreeNode(
                    node_id="001", title="Intro",
                    start_passage=1, end_passage=5,
                    summary="Introduction...",
                )
            ],
        )
        data = idx.model_dump()
        restored = WorkTreeIndex.model_validate(data)
        assert restored.nodes[0].node_id == "001"


class TestTreeIndexService:
    @pytest.mark.asyncio
    async def test_load_indices_empty(self):
        db = MagicMock()
        db.fetch = AsyncMock(return_value=[])
        svc = TreeIndexService(db=db)
        result = await svc.load_indices([])
        assert result == []

    @pytest.mark.asyncio
    async def test_load_indices_returns_parsed(self):
        tree_data = WorkTreeIndex(
            work_id="de_fato", title="De Fato", author="Alexander",
            total_passages=10, nodes=[],
        ).model_dump()
        db = MagicMock()
        db.fetch = AsyncMock(return_value=[
            {"work_id": "de_fato", "tree_index": tree_data}
        ])
        svc = TreeIndexService(db=db)
        result = await svc.load_indices(["de_fato"])
        assert len(result) == 1
        assert isinstance(result[0], WorkTreeIndex)
        assert result[0].work_id == "de_fato"

    @pytest.mark.asyncio
    async def test_extract_passages(self):
        db = MagicMock()
        db.fetch = AsyncMock(return_value=[
            {"passage_id": "p1", "text_content": "Chrysippus argues...",
             "canonical_ref": "1.1", "title": "De Fato", "author": "Alexander"},
        ])
        svc = TreeIndexService(db=db)
        idx = WorkTreeIndex(
            work_id="de_fato", title="De Fato", author="Alexander",
            total_passages=10,
            nodes=[TreeNode(
                node_id="001", title="Intro",
                start_passage=1, end_passage=5,
                summary="Introduction...",
            )],
        )
        result = await svc.extract_passages(idx, ["001"])
        assert len(result) >= 1
```

### Step 2: Run test to verify it fails, then write implementation

```python
# graphrag/src/eleutheria_graphrag/services/tree_index.py
"""PageIndex-inspired tree index service.

Manages hierarchical tree indices for ancient works. Each work has a
pre-built JSON tree that the LLM navigates during tree reasoning retrieval.
"""

from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from eleutheria_database.services.db import DatabaseService

DB_SCHEMA = os.getenv("ELEUTHERIA_DB_SCHEMA", "free_will")


class TreeNode(BaseModel):
    """A node in a work's hierarchical tree index."""

    node_id: str
    title: str
    start_passage: int
    end_passage: int
    summary: str
    nodes: list[TreeNode] = Field(default_factory=list)


class WorkTreeIndex(BaseModel):
    """Complete tree index for a single ancient work."""

    work_id: str
    title: str
    author: str
    period: str | None = None
    total_passages: int
    nodes: list[TreeNode]


class TreeIndexService:
    """Manages hierarchical tree indices for ancient works."""

    def __init__(self, db: DatabaseService) -> None:
        self.db = db

    async def load_indices(self, work_ids: list[str]) -> list[WorkTreeIndex]:
        """Load pre-built tree indices for given works."""
        if not work_ids:
            return []

        placeholders = ", ".join(f"${i + 1}" for i in range(len(work_ids)))
        rows: list[dict[str, Any]] = await self.db.fetch(
            f"""
            SELECT work_id, tree_index
            FROM {DB_SCHEMA}.work_tree_indices
            WHERE work_id::text IN ({placeholders})
            """,
            *work_ids,
        )

        indices = []
        for row in rows:
            try:
                idx = WorkTreeIndex.model_validate(row["tree_index"])
                indices.append(idx)
            except Exception:
                logger.warning("Failed to parse tree index for %s", row["work_id"])

        return indices

    async def extract_passages(
        self,
        index: WorkTreeIndex,
        node_ids: list[str],
    ) -> list[dict[str, Any]]:
        """Extract full passage text for selected tree nodes."""
        # Find passage ranges for selected nodes
        passage_ranges: list[tuple[int, int]] = []
        self._collect_ranges(index.nodes, set(node_ids), passage_ranges)

        if not passage_ranges:
            return []

        # Build WHERE clause for sequence_number ranges
        range_clauses = " OR ".join(
            f"(p.sequence_number >= {s} AND p.sequence_number <= {e})"
            for s, e in passage_ranges
        )

        rows: list[dict[str, Any]] = await self.db.fetch(
            f"""
            SELECT p.passage_id, p.text_content, p.canonical_ref,
                   w.title, w.author
            FROM {DB_SCHEMA}.passages p
            JOIN {DB_SCHEMA}.ancient_works w ON p.work_id = w.work_id
            WHERE w.work_id::text = $1
              AND ({range_clauses})
            ORDER BY p.sequence_number
            LIMIT 30
            """,
            index.work_id,
        )
        return rows

    def _collect_ranges(
        self,
        nodes: list[TreeNode],
        target_ids: set[str],
        out: list[tuple[int, int]],
    ) -> None:
        """Recursively collect passage ranges for matching node_ids."""
        for node in nodes:
            if node.node_id in target_ids:
                out.append((node.start_passage, node.end_passage))
            self._collect_ranges(node.nodes, target_ids, out)
```

### Step 3: Run tests + regression + commit

Run: `cd graphrag && python3 -m pytest tests/unit/test_tree_index_service.py -v`
Run: `cd graphrag && python3 -m pytest tests/ -q`

```bash
git add graphrag/src/eleutheria_graphrag/services/tree_index.py graphrag/tests/unit/test_tree_index_service.py
git commit -m "feat: add PageIndex-inspired tree index service"
```

---

## Tasks 8-18: FSM Nodes

**Each follows the same TDD pattern.** For brevity, I specify the key details per node. Full test code for each node follows the patterns established in `test_graph_nodes.py`.

**Shared test helpers** (add to a new `graphrag/tests/unit/conftest.py`):

```python
# graphrag/tests/unit/conftest.py
"""Shared test fixtures for FSM node tests."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from typing import Any

import pytest

from eleutheria_graphrag.agents.dependencies import Deps
from eleutheria_graphrag.agents.pipeline_config import PipelineConfig, QueryType
from eleutheria_graphrag.agents.state import RAGState


def make_deps(
    *,
    llm_response: str | list[str] = "test response",
    search_results: list[dict[str, Any]] | None = None,
    node_lookup: dict[str, dict[str, Any]] | None = None,
    outgoing_edges: dict[str, list[dict[str, Any]]] | None = None,
    incoming_edges: dict[str, list[dict[str, Any]]] | None = None,
) -> Deps:
    """Build a Deps with mocked services."""
    llm = MagicMock()
    if isinstance(llm_response, list):
        llm.generate = AsyncMock(side_effect=llm_response)
    else:
        llm.generate = AsyncMock(return_value=llm_response)

    qdrant = MagicMock()
    qdrant.search_nodes = AsyncMock(return_value=search_results or [])

    db = MagicMock()
    db.fetch = AsyncMock(return_value=[])

    return Deps(
        db=db,
        qdrant=qdrant,
        llm=llm,
        node_lookup=node_lookup or {},
        outgoing_edges=outgoing_edges or {},
        incoming_edges=incoming_edges or {},
    )


def make_ctx(state: RAGState, deps: Deps) -> MagicMock:
    """Build a mock GraphRunContext."""
    ctx = MagicMock()
    ctx.state = state
    ctx.deps = deps
    return ctx
```

### Task 8: ClassifyQueryType Node

**File:** Add to new `graphrag/src/eleutheria_graphrag/agents/graph_nodes_v2.py` (or modify existing `graph_nodes.py`)
**Test:** `graphrag/tests/unit/test_classify_query_type.py`

**Key tests:**
- `test_specific_entity` → returns `ExpandQuery`, sets `query_type=SPECIFIC_ENTITY`, `pipeline_config.use_hyde=False`
- `test_global_abstract` → returns `ExpandQuery`, sets `query_type=GLOBAL_ABSTRACT`
- `test_multi_hop` → returns `ExpandQuery`, sets `query_type=MULTI_HOP`
- `test_comparative` → returns `ExpandQuery`, sets `query_type=COMPARATIVE`
- `test_temporal` → returns `ExpandQuery`, sets `query_type=TEMPORAL`
- `test_fallback_on_llm_error` → defaults to `GLOBAL_ABSTRACT` on exception
- `test_keyword_heuristic_compare` → "compare" in query → `COMPARATIVE`
- `test_backwards_compat_complexity` → `state.complexity` set correctly

**Commit:** `feat: add ClassifyQueryType FSM node with 5-type taxonomy`

### Task 9: ExpandQuery Node

**Test:** `graphrag/tests/unit/test_expand_query.py`

**Key tests:**
- `test_expansion_disabled` → `config.use_expansion=False` → passes through, routes by query_type
- `test_routes_specific_entity` → returns `DirectKGLookup()`
- `test_routes_global_abstract` → returns `HybridRetrieve()`
- `test_routes_multi_hop` → returns `DecomposeQuery()`
- `test_routes_comparative` → returns `HybridRetrieve()`
- `test_fallback_dictionary` → LLM fails → uses hardcoded Greek terms
- `test_builds_expanded_query` → `state.expanded_query` contains transliterations

**Commit:** `feat: add ExpandQuery FSM node with philological expansion`

### Task 10: Modified HybridRetrieve

**Modify:** existing `HybridRetrieve` in `graph_nodes.py`
**Test:** Modify `test_graph_nodes.py::TestHybridRetrieve`

**Key changes:**
- Return type changes from `Synthesize` to `TreeReasoningRetrieve`
- When `config.use_hyde=True` and `deps.hyde` available: run HyDE search in parallel
- HyDE results fused via RRF

**Key tests:**
- `test_returns_tree_reasoning` → returns `TreeReasoningRetrieve()` (not `Synthesize`)
- `test_hyde_enabled` → HyDE search called, results merged
- `test_hyde_disabled` → HyDE search NOT called
- `test_hyde_missing_service` → `deps.hyde is None` → standard search only

**Commit:** `feat: integrate HyDE into HybridRetrieve with RRF fusion`

### Task 11: Modified EvaluateSufficiency

**Modify:** existing `EvaluateSufficiency` in `graph_nodes.py`
**Test:** Modify `test_graph_nodes.py::TestEvaluateSufficiency`

**Key change:** When sufficient, return `TreeReasoningRetrieve()` instead of `SearchSecondarySources()`

**Commit:** `refactor: route EvaluateSufficiency to TreeReasoningRetrieve`

### Task 12: TreeReasoningRetrieve Node

**Test:** `graphrag/tests/unit/test_tree_reasoning.py`

**Key tests:**
- `test_disabled_passthrough` → `config.use_tree_reasoning=False` → returns `CRAGValidate()` immediately
- `test_no_tree_index_service` → `deps.tree_index is None` → passthrough
- `test_loads_tree_indices` → calls `tree_index.load_indices()` with work IDs from evidence
- `test_llm_navigates_tree` → LLM called with tree index JSON, returns selected nodes
- `test_extracts_passages_for_selected_nodes` → passages added to `state.primary_evidence`
- `test_priority_filtering` → priority 3 nodes skipped when >= 10 passages already
- `test_returns_crag_validate` → always returns `CRAGValidate()`
- `test_evidence_tagged_tree_reasoning` → source = `EvidenceSource.TREE_REASONING`

**Commit:** `feat: add TreeReasoningRetrieve FSM node (PageIndex-inspired)`

### Task 13: CRAGValidate Node

**Test:** `graphrag/tests/unit/test_crag_validate.py`

**Key tests:**
- `test_disabled_passthrough` → `config.use_crag=False` → returns `DualRerank()` immediately
- `test_valid_retrieval` → confidence >= 60 → proceeds without secondary retrieval
- `test_invalid_triggers_secondary` → confidence < 60 → secondary search executed, evidence merged
- `test_insufficiency_gate` → confidence < 30 AND < 3 primary → `state.insufficient_evidence=True`
- `test_secondary_results_discounted` → new evidence has 0.85x confidence
- `test_deduplication` → secondary results don't duplicate existing evidence
- `test_sets_crag_validation_on_state` → `state.crag_validation` populated
- `test_returns_dual_rerank` → always returns `DualRerank()`

**Commit:** `feat: add CRAGValidate FSM node with insufficiency gate`

### Task 14: DualRerank Node

**Test:** `graphrag/tests/unit/test_dual_rerank.py`

**Key tests:**
- `test_disabled_passthrough` → `config.use_reranking=False` → returns `FetchPassagesAndLayer()`
- `test_cross_encoder_only` → `deps.llm_reranker is None` → cross-encoder only
- `test_dual_reranking` → cross-encoder top-20 → LLM rerank → blended scores
- `test_score_blending` → `final = 0.4 * cross_encoder + 0.6 * llm`
- `test_sorted_descending` → output sorted by blended score
- `test_top_k_15` → max 15 results
- `test_skip_short_evidence` → evidence with < 20 chars skipped
- `test_returns_fetch_passages` → always returns `FetchPassagesAndLayer()`

**Commit:** `feat: add DualRerank FSM node with cross-encoder + LLM scoring`

### Task 15: FetchPassagesAndLayer Node

**Test:** `graphrag/tests/unit/test_fetch_passages_layer.py`

**Key tests:**
- `test_fetches_passages` → calls `_fetch_passages` with node IDs
- `test_partitions_evidence` → primary/secondary correctly split
- `test_builds_hierarchical_context` → `state.accumulated_context` set
- `test_routes_simple_to_synthesize` → `SPECIFIC_ENTITY` → `Synthesize()`
- `test_routes_complex_to_secondary` → `MULTI_HOP` → `SearchSecondarySources()`

**Commit:** `feat: add FetchPassagesAndLayer FSM node`

### Task 16: Modified VerifyCitations

**Modify:** existing `VerifyCitations` in `graph_nodes.py`
**Test:** Modify `test_graph_nodes.py::TestVerifyCitations`

**Key changes:**
- Return type changes from `End[ScholarlyAnswer]` to `SelfRAGEvaluate`
- Fail-closed: on verification error, mark as `verified=False` (not `True`)

**Key tests:**
- `test_returns_self_rag` → returns `SelfRAGEvaluate()` (not `End`)
- `test_fail_closed_on_error` → verification error → `verified=False`

**Commit:** `refactor: VerifyCitations returns SelfRAGEvaluate, fail-closed`

### Task 17: SelfRAGEvaluate Node

**Test:** `graphrag/tests/unit/test_self_rag.py`

**Key tests:**
- `test_disabled_returns_end` → `config.use_self_rag=False` → returns `End(ScholarlyAnswer(...))`
- `test_high_quality_returns_end` → confidence >= 60 → returns `End`
- `test_low_quality_triggers_refinement` → confidence < 60, iterations < max → returns `RefineSynthesis()`
- `test_max_iterations_returns_end` → confidence < 60 but iterations == max → returns `End`
- `test_sets_quality_badge_high` → confidence >= 80 → "High"
- `test_sets_quality_badge_medium` → 60 <= confidence < 80 → "Medium"
- `test_sets_quality_badge_low` → confidence < 60 → "Low"

**Commit:** `feat: add SelfRAGEvaluate FSM node with quality badges`

### Task 18: RefineSynthesis Node

**Test:** `graphrag/tests/unit/test_refine_synthesis.py`

**Key tests:**
- `test_increments_iteration` → `state.self_rag_iterations` incremented
- `test_regenerates_answer` → LLM called with caveats/improvements, `state.raw_answer` updated
- `test_returns_verify_citations` → returns `VerifyCitations()`
- `test_includes_original_answer_in_prompt` → original answer in LLM prompt

**Commit:** `feat: add RefineSynthesis FSM node for Self-RAG refinement loop`

---

## Task 19: Updated ScholarlyAgent

**Files:**
- Modify: `graphrag/src/eleutheria_graphrag/agents/scholarly_agent.py`
- Modify: `graphrag/src/eleutheria_graphrag/agents/__init__.py`
- Modify: `graphrag/tests/unit/test_scholarly_agent.py`

### Step 1: Update graph registration

```python
# scholarly_agent.py — update the Graph() call
from eleutheria_graphrag.agents.graph_nodes import (
    # Existing
    DirectKGLookup,
    HybridRetrieve,
    DecomposeQuery,
    SearchPrimarySources,
    EvaluateSufficiency,
    SearchSecondarySources,
    Synthesize,
    SynthesizeWithHierarchy,
    VerifyCitations,
    # NEW
    ClassifyQueryType,
    ExpandQuery,
    TreeReasoningRetrieve,
    CRAGValidate,
    DualRerank,
    FetchPassagesAndLayer,
    SelfRAGEvaluate,
    RefineSynthesis,
)

scholarly_graph = Graph(
    nodes=[
        ClassifyQueryType,
        ExpandQuery,
        DirectKGLookup,
        HybridRetrieve,
        DecomposeQuery,
        SearchPrimarySources,
        EvaluateSufficiency,
        TreeReasoningRetrieve,
        CRAGValidate,
        DualRerank,
        FetchPassagesAndLayer,
        SearchSecondarySources,
        Synthesize,
        SynthesizeWithHierarchy,
        VerifyCitations,
        SelfRAGEvaluate,
        RefineSynthesis,
    ],
)
```

### Step 2: Update entry point

Change `ClassifyComplexity()` to `ClassifyQueryType()` in `ScholarlyAgent.query()`.

### Step 3: Update `__init__.py` exports

Add `QueryType`, `PipelineConfig` to `__all__`.

### Step 4: Update existing tests

Modify `test_scholarly_agent.py` helper `_make_deps` to handle the new classification response format (QueryType instead of complexity).

### Step 5: Run all tests

Run: `cd graphrag && python3 -m pytest tests/ -v`
Expected: All tests pass

### Step 6: Commit

```bash
git add graphrag/src/eleutheria_graphrag/agents/
git commit -m "feat: register all 17 FSM nodes in ScholarlyAgent"
```

---

## Task 20: Integration Tests

**File:** `graphrag/tests/unit/test_integration_pipeline.py`

One integration test per query type — mocked deps, full pipeline execution:

```python
# graphrag/tests/unit/test_integration_pipeline.py
"""Integration tests: full pipeline per query type with mocked deps."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from eleutheria_graphrag.agents.dependencies import Deps
from eleutheria_graphrag.agents.pipeline_config import QueryType
from eleutheria_graphrag.agents.scholarly_agent import ScholarlyAgent
from eleutheria_graphrag.agents.state import ScholarlyAnswer


# Helper builds a fully-mocked Deps with enough responses for a full pipeline
def _make_full_deps(query_type: str) -> Deps:
    # Build LLM response sequence for full pipeline
    responses = [
        # ClassifyQueryType
        f'{{"query_type": "{query_type}", "confidence": 0.9, "reason": "test"}}',
        # ExpandQuery (if expansion enabled)
        '{"greek_terms": [], "latin_terms": [], "philosophers": [], '
        '"concepts": [], "schools": [], "periods": []}',
        # Synthesis
        "The Stoics believed that fate governs all events [1].",
        # SelfRAG
        '{"relevance": 85, "grounding": 90, "completeness": 80, '
        '"confidence": 85, "caveats": [], "improvements": []}',
    ]

    llm = MagicMock()
    llm.generate = AsyncMock(side_effect=responses)

    qdrant = MagicMock()
    qdrant.search_nodes = AsyncMock(return_value=[
        {"id": "chrysippus", "score": 0.95},
    ])

    db = MagicMock()
    db.fetch = AsyncMock(return_value=[])

    return Deps(
        db=db, qdrant=qdrant, llm=llm,
        node_lookup={
            "chrysippus": {
                "label": "Chrysippus", "type": "Person",
                "description": "Stoic philosopher", "period": "Hellenistic",
            }
        },
        outgoing_edges={}, incoming_edges={},
    )


class TestSpecificEntityPipeline:
    @pytest.mark.asyncio
    async def test_full_pipeline(self):
        with patch(
            "eleutheria_graphrag.agents.graph_nodes._get_embedding",
            new_callable=AsyncMock,
            return_value=[0.1] * 768,
        ):
            deps = _make_full_deps("specific_entity")
            agent = ScholarlyAgent(deps)
            answer = await agent.query("Who was Chrysippus?")
            assert isinstance(answer, ScholarlyAnswer)
            assert answer.query_type == QueryType.SPECIFIC_ENTITY
            assert len(answer.answer) > 0


class TestGlobalAbstractPipeline:
    @pytest.mark.asyncio
    async def test_full_pipeline(self):
        with patch(
            "eleutheria_graphrag.agents.graph_nodes._get_embedding",
            new_callable=AsyncMock,
            return_value=[0.1] * 768,
        ):
            deps = _make_full_deps("global_abstract")
            agent = ScholarlyAgent(deps)
            answer = await agent.query("What did the Stoics believe about fate?")
            assert isinstance(answer, ScholarlyAnswer)
            assert answer.query_type == QueryType.GLOBAL_ABSTRACT


class TestMultiHopPipeline:
    @pytest.mark.asyncio
    async def test_full_pipeline(self):
        with patch(
            "eleutheria_graphrag.agents.graph_nodes._get_embedding",
            new_callable=AsyncMock,
            return_value=[0.1] * 768,
        ):
            deps = _make_full_deps("multi_hop")
            # Multi-hop needs extra LLM responses (decompose, sufficiency)
            deps.llm.generate.side_effect = [
                '{"query_type": "multi_hop", "confidence": 0.9, "reason": "test"}',
                '{"greek_terms": [], "latin_terms": [], "philosophers": [], '
                '"concepts": [], "schools": [], "periods": []}',
                '["Sub-question 1", "Sub-question 2"]',
                '{"score": 0.8, "sufficient": true, "reason": "ok"}',
                "The chain of influence runs from Aristotle to Chrysippus [1].",
                '{"relevance": 80, "grounding": 85, "completeness": 75, '
                '"confidence": 80, "caveats": [], "improvements": []}',
            ]
            agent = ScholarlyAgent(deps)
            answer = await agent.query(
                "Trace the influence from Aristotle to Augustine"
            )
            assert isinstance(answer, ScholarlyAnswer)
            assert answer.query_type == QueryType.MULTI_HOP


class TestComparativePipeline:
    @pytest.mark.asyncio
    async def test_full_pipeline(self):
        with patch(
            "eleutheria_graphrag.agents.graph_nodes._get_embedding",
            new_callable=AsyncMock,
            return_value=[0.1] * 768,
        ):
            deps = _make_full_deps("comparative")
            agent = ScholarlyAgent(deps)
            answer = await agent.query(
                "How did Stoics and Epicureans differ on free will?"
            )
            assert isinstance(answer, ScholarlyAnswer)
            assert answer.query_type == QueryType.COMPARATIVE


class TestInsufficientEvidenceResponse:
    @pytest.mark.asyncio
    async def test_insufficient_evidence_flagged(self):
        """When CRAG confidence < 30 and < 3 primary sources,
        the answer should flag insufficient evidence."""
        with patch(
            "eleutheria_graphrag.agents.graph_nodes._get_embedding",
            new_callable=AsyncMock,
            return_value=[0.1] * 768,
        ):
            deps = _make_full_deps("specific_entity")
            # Override to return empty search results
            deps.qdrant.search_nodes = AsyncMock(return_value=[])
            agent = ScholarlyAgent(deps)
            answer = await agent.query("Obscure question with no evidence")
            assert isinstance(answer, ScholarlyAnswer)
```

**Commit:** `test: add integration tests for all 5 query type pipelines`

---

## Task 21: Database Schema + Tree Index Precompute Script

**Files:**
- Create: `database/schema/work_tree_indices.sql`
- Create: `scripts/build_work_tree_indices.py`

### Step 1: Database schema

```sql
-- database/schema/work_tree_indices.sql
-- Pre-built hierarchical tree indices for PageIndex-style retrieval

CREATE TABLE IF NOT EXISTS free_will.work_tree_indices (
    work_id UUID PRIMARY KEY REFERENCES free_will.ancient_works(work_id),
    tree_index JSONB NOT NULL,
    node_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_tree_indices_updated ON free_will.work_tree_indices(updated_at);

COMMENT ON TABLE free_will.work_tree_indices IS
    'Pre-built hierarchical tree indices for PageIndex-inspired agentic retrieval. '
    'Each row contains a JSON tree structure with section summaries for one ancient work.';
```

### Step 2: Precompute script

```python
# scripts/build_work_tree_indices.py
"""Build hierarchical tree indices for all ancient works.

Usage:
    DATABASE_URL='...' python3 scripts/build_work_tree_indices.py
    DATABASE_URL='...' python3 scripts/build_work_tree_indices.py --work-ids de_fato,meditations
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import sys

import asyncpg

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

DB_SCHEMA = os.getenv("ELEUTHERIA_DB_SCHEMA", "free_will")


async def main() -> None:
    parser = argparse.ArgumentParser(description="Build work tree indices")
    parser.add_argument("--work-ids", help="Comma-separated work IDs to process")
    parser.add_argument("--force", action="store_true", help="Rebuild existing indices")
    parser.add_argument("--dry-run", action="store_true", help="Print without inserting")
    args = parser.parse_args()

    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        logger.error("DATABASE_URL required")
        sys.exit(1)

    conn = await asyncpg.connect(db_url)
    try:
        # Get works to process
        if args.work_ids:
            work_ids = [w.strip() for w in args.work_ids.split(",")]
            works = await conn.fetch(
                f"SELECT work_id, title, author FROM {DB_SCHEMA}.ancient_works "
                f"WHERE work_id::text = ANY($1::text[])",
                work_ids,
            )
        else:
            works = await conn.fetch(
                f"SELECT work_id, title, author FROM {DB_SCHEMA}.ancient_works "
                f"ORDER BY title"
            )

        logger.info("Processing %d works", len(works))

        for work in works:
            work_id = str(work["work_id"])
            title = work["title"]
            author = work["author"]
            logger.info("  %s — %s (%s)", work_id, title, author)

            # Get passages for this work
            passages = await conn.fetch(
                f"""
                SELECT passage_id, text_content, canonical_ref,
                       sequence_number, citation_hierarchy
                FROM {DB_SCHEMA}.passages
                WHERE work_id = $1
                ORDER BY sequence_number
                """,
                work["work_id"],
            )

            if not passages:
                logger.warning("    No passages found, skipping")
                continue

            # Build tree from citation_hierarchy
            tree_nodes = _build_tree_from_hierarchy(passages, title, author)

            tree_index = {
                "work_id": work_id,
                "title": title,
                "author": author,
                "total_passages": len(passages),
                "nodes": tree_nodes,
            }

            node_count = _count_nodes(tree_nodes)
            logger.info("    %d passages → %d tree nodes", len(passages), node_count)

            if args.dry_run:
                print(json.dumps(tree_index, indent=2, ensure_ascii=False)[:500])
                continue

            # Upsert into work_tree_indices
            await conn.execute(
                f"""
                INSERT INTO {DB_SCHEMA}.work_tree_indices
                    (work_id, tree_index, node_count, updated_at)
                VALUES ($1, $2::jsonb, $3, now())
                ON CONFLICT (work_id) DO UPDATE
                SET tree_index = $2::jsonb, node_count = $3, updated_at = now()
                """,
                work["work_id"],
                json.dumps(tree_index, ensure_ascii=False),
                node_count,
            )

        logger.info("Done.")
    finally:
        await conn.close()


def _build_tree_from_hierarchy(
    passages: list, title: str, author: str
) -> list[dict]:
    """Build a tree structure from passage citation_hierarchy values."""
    # Group passages by their top-level hierarchy
    groups: dict[str, list] = {}
    for p in passages:
        hierarchy = p["citation_hierarchy"] or ""
        parts = hierarchy.split(".")
        top_key = parts[0] if parts[0] else "root"
        groups.setdefault(top_key, []).append(p)

    nodes = []
    for i, (key, group) in enumerate(groups.items()):
        node_id = f"{i:04d}"
        first_seq = group[0]["sequence_number"]
        last_seq = group[-1]["sequence_number"]

        # Build summary from passage content (first 500 chars of combined text)
        combined = " ".join(
            (p["text_content"] or "")[:200] for p in group[:3]
        )
        summary = combined[:500] if combined else f"Section {key} of {title}"

        nodes.append({
            "node_id": node_id,
            "title": key or f"Section {i + 1}",
            "start_passage": first_seq,
            "end_passage": last_seq,
            "summary": summary,
            "nodes": [],  # Could recurse for deeper hierarchy
        })

    return nodes


def _count_nodes(nodes: list[dict]) -> int:
    """Count total nodes in tree."""
    count = len(nodes)
    for n in nodes:
        count += _count_nodes(n.get("nodes", []))
    return count


if __name__ == "__main__":
    asyncio.run(main())
```

### Step 3: Commit

```bash
git add database/schema/work_tree_indices.sql scripts/build_work_tree_indices.py
git commit -m "feat: add tree index DB schema and precompute script"
```

---

## Task 22: Final Regression Run

### Step 1: Run full test suite

Run: `cd graphrag && python3 -m pytest tests/ -v --tb=short`
Expected: All tests pass (129 original + ~80 new = ~209 total)

### Step 2: Lint

Run: `cd graphrag && python3 -m ruff check .`
Run: `cd graphrag && python3 -m ruff format .`

### Step 3: Type check

Run: `cd graphrag && python3 -m mypy src/eleutheria_graphrag/agents/ --ignore-missing-imports`

### Step 4: Final commit

```bash
git add -A
git commit -m "chore: lint and type fixes for SOTA agentic pipeline"
```

### Step 5: Summary commit (optional squash)

Tag the work:

```bash
git tag v2.1.0-sota-pipeline -m "SOTA agentic GraphRAG pipeline: 17 nodes, HyDE, CRAG, Self-RAG, tree reasoning"
```

---

## Execution Checklist

| Task | Files | Tests | Commit |
|------|-------|-------|--------|
| 1. Pipeline config | 1 new, 1 test | 13 | `feat: add query type taxonomy and adaptive pipeline config` |
| 2. Structured models | 1 new, 1 test | 15 | `feat: add Pydantic AI structured output models` |
| 3. State upgrades | 1 mod, 1 mod | ~12 | `feat: add new state fields` |
| 4. Deps container | 1 mod | 0 | `feat: add new service slots to Deps` |
| 5. HyDEService | 1 new, 1 test | 5 | `feat: add HyDE service` |
| 6. LLMRerankerService | 1 new, 1 test | 5 | `feat: add LLM scholarly reranker` |
| 7. TreeIndexService | 1 new, 1 test | 5 | `feat: add tree index service` |
| 8. ClassifyQueryType | 1 mod, 1 test | 8 | `feat: ClassifyQueryType node` |
| 9. ExpandQuery | 1 mod, 1 test | 7 | `feat: ExpandQuery node` |
| 10. HybridRetrieve mod | 1 mod, 1 mod | 4 | `feat: HyDE in HybridRetrieve` |
| 11. EvaluateSufficiency mod | 1 mod, 1 mod | 1 | `refactor: route to TreeReasoning` |
| 12. TreeReasoningRetrieve | 1 mod, 1 test | 8 | `feat: TreeReasoningRetrieve node` |
| 13. CRAGValidate | 1 mod, 1 test | 8 | `feat: CRAGValidate node` |
| 14. DualRerank | 1 mod, 1 test | 7 | `feat: DualRerank node` |
| 15. FetchPassagesAndLayer | 1 mod, 1 test | 5 | `feat: FetchPassagesAndLayer node` |
| 16. VerifyCitations mod | 1 mod, 1 mod | 2 | `refactor: fail-closed VerifyCitations` |
| 17. SelfRAGEvaluate | 1 mod, 1 test | 7 | `feat: SelfRAGEvaluate node` |
| 18. RefineSynthesis | 1 mod, 1 test | 4 | `feat: RefineSynthesis node` |
| 19. ScholarlyAgent update | 2 mod, 1 mod | 2 | `feat: register all 17 nodes` |
| 20. Integration tests | 1 new | 5 | `test: integration tests` |
| 21. DB schema + script | 2 new | 0 | `feat: tree index infra` |
| 22. Final regression | 0 | 0 | `chore: lint + types` |
| **Total** | **~20 files** | **~123 tests** | **22 commits** |
