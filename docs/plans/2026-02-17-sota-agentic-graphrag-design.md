# SOTA Agentic GraphRAG Pipeline: Design Document

**Date:** 2026-02-17
**Status:** Approved
**Branch:** `main` (planned)
**Builds on:** GraphRAG Convergence (`docs/graphrag-convergence.md`)

---

## 1. Objective

Upgrade the Python pydantic-graph FSM (`ScholarlyAgent`) to a state-of-the-art agentic search pipeline by integrating:

- **HyDE** (Hypothetical Document Embeddings) for semantic gap bridging
- **CRAG** (Corrective RAG) for retrieval validation and self-correction
- **Self-RAG** for post-generation quality evaluation with refinement loop
- **Philological query expansion** (Greek/Latin term injection)
- **Adaptive pipeline config** (5 query types with per-type feature flags)
- **Dual reranking** (cross-encoder + LLM scholarly reranking)
- **PageIndex-inspired tree reasoning** for precision passage extraction
- **Pydantic AI structured output** for all JSON-returning LLM calls
- **Anti-hallucination safeguards** with zero tolerance for fabrication

The TypeScript Cloudflare Workers orchestrator remains the production frontend. This Python pipeline serves as the high-quality backend for complex queries and as the reference implementation for all SOTA techniques.

---

## 2. Architecture Overview

### Three Pillars

| Pillar | What | Why |
|--------|------|-----|
| **A. Pipeline Augmentation** | 7 new FSM nodes, adaptive pipeline config, Pydantic AI structured output | Better retrieval, ranking, synthesis, self-correction |
| **B. Tree Reasoning Retrieval** | PageIndex-inspired LLM navigation of work tree indices | Precision passage extraction beyond vector similarity |
| **C. Anti-Hallucination** | Fail-closed citation verification, evidence sufficiency gate, grounding checks | Zero tolerance for fabrication in a scholarly database |

### Design Decisions (Confirmed)

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Query taxonomy | 5-type + pipeline config | Matches TypeScript production; per-type feature toggling |
| Reranking | Dual: cross-encoder then LLM | Cross-encoder prunes noise; LLM adds domain awareness |
| Citation verification | Enhanced claim-citation pairing | Per-citation LLM verification; fail-closed on error |
| Structured LLM output | Pydantic AI Agent with `result_type` | Automatic validation and retries; type-safe pipeline |
| Tree reasoning integration | Dedicated FSM node | Clean separation; activated by pipeline config |

---

## 3. Query Taxonomy and Pipeline Config

### 3.1 QueryType Enum (replaces QueryComplexity)

```python
class QueryType(str, Enum):
    SPECIFIC_ENTITY = "specific_entity"   # Single-entity factual lookup
    GLOBAL_ABSTRACT = "global_abstract"   # Broad topic requiring multiple sources
    MULTI_HOP       = "multi_hop"         # Chain of influence / multi-step reasoning
    COMPARATIVE     = "comparative"       # Compare schools, philosophers, or positions
    TEMPORAL        = "temporal"           # Default / temporal trace / fallback
```

`QueryComplexity` is kept for backwards compatibility. Mapping:

| QueryType | QueryComplexity |
|-----------|-----------------|
| `specific_entity` | `SIMPLE` |
| `global_abstract` | `MEDIUM` |
| `multi_hop` | `COMPLEX` |
| `comparative` | `COMPLEX` |
| `temporal` | `COMPLEX` |

### 3.2 PipelineConfig

```python
class PipelineConfig(BaseModel):
    use_hyde: bool = True
    use_crag: bool = True
    use_reranking: bool = True
    use_self_rag: bool = True
    use_expansion: bool = True
    use_tree_reasoning: bool = False
```

### 3.3 Config Matrix

| Query Type | HyDE | CRAG | Reranking | Self-RAG | Expansion | Tree Reasoning |
|------------|------|------|-----------|----------|-----------|----------------|
| `specific_entity` | Off | On | On | On | On | Off |
| `global_abstract` | On | On | On | On | Off | Off |
| `multi_hop` | Off | On | Off | On | On | **On** |
| `comparative` | On | On | On | On | On | **On** |
| `temporal` | On | On | On | On | On | **On** |

**Rationale:**
- **HyDE off** for `specific_entity` (direct lookup is better than hypothetical generation) and `multi_hop` (decomposition handles the semantic gap)
- **Expansion off** for `global_abstract` (too broad to benefit from specific Greek/Latin terms)
- **Reranking off** for `multi_hop` (bridge paths are already scored by PageRank in weighted traversal)
- **Tree reasoning on** for `multi_hop`, `comparative`, `temporal` (these benefit most from cross-reference following and structural navigation)

---

## 4. FSM Graph Topology

### 4.1 Current Graph (10 nodes, 3 paths)

```
ClassifyComplexity
 ├─ simple  → DirectKGLookup → Synthesize → VerifyCitations → End
 ├─ medium  → HybridRetrieve → Synthesize → VerifyCitations → End
 └─ complex → DecomposeQuery → SearchPrimary ↔ EvalSufficiency
               → SearchSecondary → SynthesizeHierarchy → VerifyCitations → End
```

### 4.2 New Graph (17 nodes, convergent post-retrieval pipeline)

```
ClassifyQueryType                         ← replaces ClassifyComplexity
  │
  ▼
ExpandQuery                               ← NEW (if config.use_expansion)
  │
  ├─ specific_entity ─→ DirectKGLookup ──────────────────────────────┐
  │                                                                   │
  ├─ global_abstract ─→ HybridRetrieve (+HyDE) ─────────────────────┤
  │                                                                   │
  ├─ multi_hop ───────→ DecomposeQuery → SearchPrimarySources        │
  │                       ↔ EvaluateSufficiency ─────────────────────┤
  │                                                                   │
  └─ comparative ─────→ HybridRetrieve (+HyDE) ─────────────────────┤
                                                                      │
                             ALL RETRIEVAL PATHS CONVERGE HERE        │
                                          ┌───────────────────────────┘
                                          ▼
                              TreeReasoningRetrieve               ← NEW (if config.use_tree_reasoning)
                                          │
                                          ▼
                                    CRAGValidate                  ← NEW (if config.use_crag)
                                          │
                                          ▼
                                     DualRerank                   ← NEW (if config.use_reranking)
                                          │
                                          ▼
                              FetchPassagesAndLayer               ← NEW (extracted from retrieval)
                                ├─ simple/medium → Synthesize ──────────────┐
                                └─ complex/comp → SearchSecondarySources    │
                                      → SynthesizeWithHierarchy ────────────┤
                                                                            │
                                                    ┌───────────────────────┘
                                                    ▼
                                            VerifyCitations               ← MODIFIED (fail-closed)
                                                    │
                                                    ▼
                                           SelfRAGEvaluate                ← NEW (if config.use_self_rag)
                                             ├─ quality OK → End
                                             └─ quality low → RefineSynthesis ← NEW (max 2 iterations)
                                                                │
                                                                └──→ VerifyCitations (loop)
```

### 4.3 Node Inventory

| # | Node | Status | Returns | Purpose |
|---|------|--------|---------|---------|
| 1 | `ClassifyQueryType` | **New** (replaces `ClassifyComplexity`) | `ExpandQuery` | 5-type classification + pipeline config |
| 2 | `ExpandQuery` | **New** | `DirectKGLookup \| HybridRetrieve \| DecomposeQuery` | Greek/Latin philological expansion + routing |
| 3 | `DirectKGLookup` | Kept | `TreeReasoningRetrieve` | Fast semantic search (simple queries) |
| 4 | `HybridRetrieve` | **Modified** (+HyDE) | `TreeReasoningRetrieve` | Semantic + graph + HyDE augmentation |
| 5 | `DecomposeQuery` | Kept | `SearchPrimarySources` | Multi-hop query decomposition |
| 6 | `SearchPrimarySources` | Kept | `EvaluateSufficiency` | Primary source retrieval with weighted traversal |
| 7 | `EvaluateSufficiency` | **Modified** (structured output) | `SearchPrimarySources \| TreeReasoningRetrieve` | Sufficiency loop (converges to post-retrieval) |
| 8 | `TreeReasoningRetrieve` | **New** | `CRAGValidate` | PageIndex-style tree navigation |
| 9 | `CRAGValidate` | **New** | `DualRerank` | Corrective RAG validation + secondary retrieval |
| 10 | `DualRerank` | **New** | `FetchPassagesAndLayer` | Cross-encoder + LLM scholarly reranking |
| 11 | `FetchPassagesAndLayer` | **New** (extracted) | `Synthesize \| SearchSecondarySources` | Passage retrieval + primary/secondary layering |
| 12 | `SearchSecondarySources` | Kept | `SynthesizeWithHierarchy` | Modern scholarship retrieval |
| 13 | `Synthesize` | Kept | `VerifyCitations` | Single-pass LLM synthesis |
| 14 | `SynthesizeWithHierarchy` | Kept | `VerifyCitations` | Hierarchical primary/secondary synthesis |
| 15 | `VerifyCitations` | **Modified** (fail-closed) | `SelfRAGEvaluate` | Citation extraction + LLM verification |
| 16 | `SelfRAGEvaluate` | **New** | `End \| RefineSynthesis` | Post-generation quality evaluation |
| 17 | `RefineSynthesis` | **New** | `VerifyCitations` | Answer refinement from Self-RAG feedback |

---

## 5. New Nodes: Detailed Specifications

### 5.1 ClassifyQueryType

**Replaces:** `ClassifyComplexity`

**Pydantic AI structured output:**

```python
class ClassificationResult(BaseModel):
    query_type: QueryType
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str
```

**LLM prompt:**

```
Classify the following scholarly question about ancient philosophy
into one of five query types. Return a JSON object.

Classification criteria:
- **specific_entity**: Single-entity factual lookup (who, what, when).
  E.g. "Who was Chrysippus?" or "What school did Epictetus belong to?"
- **global_abstract**: Requires combining information about one broad topic
  from multiple sources.
  E.g. "What did the Stoics believe about fate?"
- **multi_hop**: Requires tracing chains of influence, transmission, or
  argument across multiple philosophers or time periods.
  E.g. "How did Stoic fate evolve from Chrysippus to Epictetus?"
- **comparative**: Requires explicit comparison between schools, philosophers,
  or positions.
  E.g. "How did Stoics and Epicureans differ on free will?"
- **temporal**: Temporal traces, dialectical analysis, or questions that don't
  fit the above categories.
  E.g. "How did views on moral responsibility change from Classical to
  Late Antiquity?"

Question: {question}
```

**Fallback (no LLM):** Keyword heuristic — "compare"/"differ"/"vs" -> `comparative`; "trace"/"chain"/"influence...through" -> `multi_hop`; "who"/"what is"/"define" -> `specific_entity`; default -> `global_abstract`.

**Behaviour:**
1. Classify query type via Pydantic AI Agent
2. Map query type to `PipelineConfig` via `PIPELINE_CONFIGS` dict
3. Map query type to `QueryComplexity` for backwards compat
4. Set `state.query_type`, `state.pipeline_config`, `state.complexity`
5. Return `ExpandQuery()`

### 5.2 ExpandQuery

**Purpose:** Enrich the query with Greek/Latin philosophical terms, philosopher names, and school/period context to improve downstream retrieval.

**Pydantic AI structured output:**

```python
class GreekTerm(BaseModel):
    greek: str          # e.g. "τὸ ἐφ' ἡμῖν"
    transliteration: str  # e.g. "to eph' hēmin"
    translation: str    # e.g. "what is in our power"

class LatinTerm(BaseModel):
    latin: str          # e.g. "liberum arbitrium"
    translation: str    # e.g. "free will"

class ExpansionTerms(BaseModel):
    greek_terms: list[GreekTerm] = Field(default_factory=list, max_length=5)
    latin_terms: list[LatinTerm] = Field(default_factory=list, max_length=3)
    philosophers: list[str] = Field(default_factory=list, max_length=5)
    concepts: list[str] = Field(default_factory=list, max_length=5)
    schools: list[str] = Field(default_factory=list, max_length=3)
    periods: list[str] = Field(default_factory=list, max_length=3)
```

**LLM prompt:**

```
You are an expert classicist. Analyze this research question about
ancient philosophy and identify relevant terms.

Question: "{question}"

Guidelines:
- Include 2-5 Greek terms with correct polytonic diacritics
- Include 1-3 Latin terms if relevant
- Include all mentioned or implied philosophers
- Include philosophical concepts in modern English
- Identify relevant schools and periods
```

**Fallback dictionary (no LLM):** 20 Greek terms, 8 Latin terms, 18 philosopher names — matched by substring inclusion in the query. Identical to TypeScript `COMMON_GREEK_TERMS`.

Static terms include:

| English trigger | Greek | Transliteration |
|----------------|-------|-----------------|
| free will / in our power | τὸ ἐφ' ἡμῖν | to eph' hēmin |
| self-determination | αὐτεξούσιον | autexousion |
| fate / destiny | εἱμαρμένη | heimarmenē |
| assent | συγκατάθεσις | synkatathesis |
| moral choice | προαίρεσις | prohairesis |
| swerve / clinamen | παρέγκλισις | parenklisis |
| necessity | ἀνάγκη | anankē |
| possibility | δυνατόν | dynaton |
| cause | αἰτία | aitia |
| impression | φαντασία | phantasia |

**Behaviour:**
1. If `config.use_expansion` is False, skip to routing
2. Try LLM expansion; on failure, use fallback dictionary
3. Build `expanded_query`: `"{query} ({transliteration_1}, {transliteration_2}, {philosopher_1})"`
4. Set `state.expanded_query` and `state.expansion_terms`
5. Route to retrieval node based on `state.query_type`:
   - `specific_entity` -> `DirectKGLookup()`
   - `global_abstract` | `comparative` -> `HybridRetrieve()`
   - `multi_hop` | `temporal` -> `DecomposeQuery()`

### 5.3 HybridRetrieve (Modified: +HyDE)

**Changes from current:** When `config.use_hyde` is True, run HyDE search in parallel with standard semantic search, then fuse results via RRF.

**HyDE integration:**

```python
# Inside HybridRetrieve.run():
if ctx.state.pipeline_config.use_hyde:
    # Run standard search + HyDE in parallel
    standard_task = _semantic_search(ctx.deps, query, limit=10)
    hyde_task = ctx.deps.hyde.search_nodes(query, limit=10)
    standard_hits, hyde_hits = await asyncio.gather(standard_task, hyde_task)

    # RRF fusion (k=60)
    fused = _reciprocal_rank_fusion(standard_hits, hyde_hits, k=60)
else:
    fused = await _semantic_search(ctx.deps, query, limit=10)
```

HyDE results get a 0.9x confidence discount to mark them as hypothetical-match rather than direct retrieval.

**Now returns:** `TreeReasoningRetrieve()` (instead of `Synthesize()`)

### 5.4 TreeReasoningRetrieve (New)

**Purpose:** PageIndex-inspired tree reasoning. For candidate works identified by Stage 1 (vector search), load pre-built tree indices and let the LLM reason about exactly which passages to retrieve.

**Pydantic AI structured output:**

```python
class TreeNavigationResult(BaseModel):
    selected_nodes: list[SelectedNode]
    reasoning: str

class SelectedNode(BaseModel):
    work_id: str
    node_id: str
    reason: str
    priority: int = Field(ge=1, le=3)  # 1=must-read, 2=important, 3=supplementary
```

**LLM prompt:**

```
You are a scholar of ancient philosophy navigating document indices
to find passages that answer a specific question.

QUESTION: {question}

DOCUMENT INDICES:
{tree_indices_json}

For each document, examine the section summaries and reason step by step
about which sections are most likely to contain information that answers
the question. Consider:
- Which sections discuss the specific topic, argument, or philosopher?
- Are there cross-references to other sections you should also check?
- Which sections contain primary arguments vs. passing mentions?
- Prioritize sections with direct philosophical argumentation.

Select ALL sections worth examining. Assign priority:
1 = must-read (directly addresses the question)
2 = important (strong supporting context)
3 = supplementary (useful background)
```

**Behaviour:**
1. If `config.use_tree_reasoning` is False, pass through to `CRAGValidate()`
2. Extract unique `work_id` values from current evidence
3. Load tree indices for top-5 works from `TreeIndexService`
4. LLM navigates tree indices, selects passage nodes with reasoning
5. Extract full passage text for selected nodes (priority 1 and 2 only; priority 3 only if < 10 passages so far)
6. Add to evidence with `source=EvidenceSource.TREE_REASONING`
7. Return `CRAGValidate()`

**Tree index structure (per work):**

```json
{
  "work_id": "de_fato_alexander",
  "title": "De Fato (Alexander of Aphrodisias)",
  "author": "Alexander of Aphrodisias",
  "period": "Imperial",
  "total_passages": 47,
  "nodes": [
    {
      "node_id": "df_001",
      "title": "Introduction: The Problem of Fate",
      "start_passage": 1,
      "end_passage": 8,
      "summary": "Alexander introduces the debate between Stoic determinism and Peripatetic libertarianism. Sets up the central question: whether everything happens by necessity (heimarmenē) or whether some things are 'up to us' (eph' hēmin). References Chrysippus, Cleanthes, and Aristotle.",
      "nodes": [
        {
          "node_id": "df_002",
          "title": "The Stoic Position on Universal Causation",
          "start_passage": 1,
          "end_passage": 4,
          "summary": "Chrysippus's argument that every event has a prior cause forming an infinite chain..."
        }
      ]
    }
  ]
}
```

### 5.5 CRAGValidate (New)

**Purpose:** Corrective RAG — validate retrieval quality and trigger secondary retrieval if insufficient.

**Pydantic AI structured output:**

```python
class CRAGValidation(BaseModel):
    relevance: int = Field(ge=0, le=100)
    completeness: int = Field(ge=0, le=100)
    confidence: int = Field(ge=0, le=100)
    missing: list[str] = Field(default_factory=list, max_length=5)
    suggestions: list[str] = Field(default_factory=list, max_length=3)
```

**LLM prompt:**

```
You are a scholarly validation system for ancient philosophy research.

TASK: Evaluate if the retrieved context can adequately answer the
research question.

RESEARCH QUESTION: "{question}"

RETRIEVED CONTEXT:
\"\"\"{context[:3000]}\"\"\"

EVALUATE on 0-100 scale:
1. RELEVANCE: Does the context address the question topic?
2. COMPLETENESS: Is sufficient information present to answer fully?
3. CONFIDENCE: Can a good scholarly answer be generated from this?

Also identify what is MISSING and suggest specific search queries
to fill the gaps.
```

**Thresholds:**
- `confidence >= 60`: valid, proceed
- `confidence < 60`: invalid, trigger secondary retrieval
- `confidence < 30 AND primary_count < 3`: **evidence insufficiency gate** — pipeline will return "insufficient evidence" response instead of fabricating an answer

**Secondary retrieval:** Takes up to 3 `missing` items + 2 `suggestions` as search queries. Runs semantic search for each (Qdrant threshold 0.4). Results get 0.85x confidence discount. Deduplicates against existing evidence.

**Behaviour:**
1. If `config.use_crag` is False, pass through to `DualRerank()`
2. Build context string from current evidence (truncated to 3000 chars)
3. Run validation via Pydantic AI Agent
4. If valid: set `state.crag_validation`, proceed
5. If invalid: run secondary retrieval, merge evidence
6. If below insufficiency gate: set `state.insufficient_evidence = True`
7. Return `DualRerank()`

### 5.6 DualRerank (New)

**Purpose:** Two-stage reranking — fast cross-encoder prunes noise, then LLM adds domain-aware scholarly scoring.

**Stage 1: Cross-encoder (existing `RerankerService`)**
- Model: `BAAI/bge-reranker-v2-m3`
- Input: all evidence with text > 20 chars
- Output: top-20 by cross-encoder score
- Runs via `asyncio.to_thread()` (non-blocking)

**Stage 2: LLM scholarly reranking (new `LLMRerankerService`)**

Pydantic AI structured output:

```python
class RerankItem(BaseModel):
    id: int           # 1-indexed position in candidate list
    score: int = Field(ge=0, le=100)
    reason: str

class LLMRerankResult(BaseModel):
    rankings: list[RerankItem]
```

LLM prompt:

```
You are a scholar of ancient Greek and Roman philosophy evaluating
passages for academic research.

RESEARCH QUESTION: "{query}"

CANDIDATE PASSAGES:
{candidates_formatted}

Rate each passage's relevance to the research question on 0-100.

SCORING GUIDELINES:
- 90-100: Directly addresses the question with specific relevant content
- 70-89: Highly relevant, discusses key concepts/philosophers
- 50-69: Moderately relevant, related topic
- 30-49: Tangentially relevant
- 0-29: Not relevant

Include ALL passages in your rankings.
```

**Score blending:**
```
final_score = 0.4 * cross_encoder_score + 0.6 * (llm_score / 100)
```

LLM weighted higher (0.6) because it provides domain-aware scoring that the cross-encoder lacks.

**Behaviour:**
1. If `config.use_reranking` is False, pass through to `FetchPassagesAndLayer()`
2. Run cross-encoder reranking → top-20
3. Run LLM reranking on the 20 survivors → blended scores
4. Sort by blended score descending, keep top-15
5. Update evidence scores in state
6. Return `FetchPassagesAndLayer()`

### 5.7 FetchPassagesAndLayer (New — extracted)

**Purpose:** Extracted from `HybridRetrieve` and `SearchPrimarySources`. Provides a clean convergence point where all retrieval paths get passages fetched and evidence partitioned.

**Behaviour:**
1. Extract KG node IDs from all current evidence (primary + secondary)
2. Fetch passages via `passage_citations` JOIN (existing `_fetch_passages`, limit=15)
3. Add passages as `Evidence` items with `source=PASSAGE_CITATION`
4. Partition all evidence into `state.primary_evidence` / `state.secondary_evidence` using `_is_primary_node()`
5. Build hierarchical context string (`_build_hierarchical_context()`)
6. Route based on query type:
   - `specific_entity` | `global_abstract` -> `Synthesize()`
   - `multi_hop` | `comparative` | `temporal` -> `SearchSecondarySources()`

### 5.8 SelfRAGEvaluate (New)

**Purpose:** Post-generation quality evaluation. Determines if the answer meets scholarly standards or needs refinement.

**Pydantic AI structured output:**

```python
class SelfRAGEvaluation(BaseModel):
    relevance: int = Field(ge=0, le=100)
    grounding: int = Field(ge=0, le=100)
    completeness: int = Field(ge=0, le=100)
    confidence: int = Field(ge=0, le=100)
    caveats: list[str] = Field(default_factory=list, max_length=5)
    improvements: list[str] = Field(default_factory=list, max_length=5)
```

**LLM prompt:**

```
You are a scholarly quality evaluator for ancient philosophy research.

TASK: Evaluate this answer's quality and reliability.

RESEARCH QUESTION: "{question}"

GENERATED ANSWER:
\"\"\"{answer[:2500]}\"\"\"

SOURCES CITED: {source_count} sources
SOURCE LABELS: {source_labels}

EVALUATE on 0-100 scale:
1. RELEVANCE: Does the answer directly address the research question?
2. GROUNDING: Are ALL claims supported by the cited sources? (NOT hallucinated)
3. COMPLETENESS: Does it cover the key aspects of the question?
4. CONFIDENCE: Overall reliability for scholarly use?

Pay special attention to GROUNDING — any claim not directly supported
by the cited evidence should lower the grounding score significantly.
```

**Quality badges:**
- `confidence >= 80`: "High"
- `60 <= confidence < 80`: "Medium"
- `confidence < 60`: "Low"

**Behaviour:**
1. If `config.use_self_rag` is False, proceed directly to `End`
2. Run evaluation via Pydantic AI Agent
3. Set `state.self_rag_evaluation` and `state.quality_badge`
4. If `confidence >= 60` OR `state.self_rag_iterations >= state.max_self_rag_iterations`:
   - Return `End(ScholarlyAnswer(...))`
5. If `confidence < 60` AND iterations remaining:
   - Return `RefineSynthesis()`

### 5.9 RefineSynthesis (New)

**Purpose:** Re-synthesize the answer incorporating Self-RAG feedback (caveats and suggested improvements).

**LLM prompt:**

```
You are refining a scholarly answer based on quality feedback.

ORIGINAL QUESTION: "{question}"

ORIGINAL ANSWER:
\"\"\"{raw_answer}\"\"\"

QUALITY ISSUES IDENTIFIED:
- Caveats: {caveats}
- Suggested improvements: {improvements}
- Grounding score: {grounding}/100
- Completeness score: {completeness}/100

AVAILABLE CONTEXT:
\"\"\"{accumulated_context[:3000]}\"\"\"

TASK: Rewrite the answer to address the identified issues:
1. Strengthen claims with better source citations
2. Add missing aspects mentioned in improvements
3. Acknowledge limitations mentioned in caveats
4. If a claim cannot be grounded in the evidence, remove it or
   explicitly state "The available sources do not address this point"
5. Maintain scholarly register and accuracy

Write the improved answer directly.
```

**Behaviour:**
1. Increment `state.self_rag_iterations`
2. Build refinement prompt from Self-RAG caveats + improvements
3. Generate refined answer via LLM
4. Set `state.raw_answer` to refined answer
5. Return `VerifyCitations()` (re-verify the refined answer)

---

## 6. New Services

### 6.1 HyDEService

```python
class HyDEService:
    """Hypothetical Document Embeddings for semantic gap bridging."""

    def __init__(self, llm: LLMService, qdrant: QdrantService) -> None: ...

    async def generate_hypothetical(self, query: str) -> str:
        """Generate a 150-200 word hypothetical scholarly passage."""

    async def search_nodes(self, query: str, limit: int = 10) -> list[dict]:
        """Embed hypothetical document and search KG nodes."""

    async def enhanced_search(
        self, query: str, standard_hits: list[dict], limit: int = 10
    ) -> list[dict]:
        """RRF fusion of standard + HyDE results (k=60)."""
```

**HyDE generation prompt:**

```
You are an expert classicist specializing in ancient Greek and Roman
philosophy, particularly debates about fate, free will, and moral
responsibility.

Write a scholarly passage (150-200 words) that would perfectly answer
this question: "{query}"

Requirements:
- Include specific philosophers by name
- Include Greek philosophical terms with transliterations
- Reference specific ancient works
- Use academic register and precision

Write only the passage, no preamble.
```

**RRF fusion algorithm:**
```
For each result list L at rank r (0-indexed):
    rrf_score(item) += 1 / (k + r + 1)    where k = 60
Merge by item ID, sort descending, take top limit.
```

### 6.2 LLMRerankerService

```python
class LLMRerankerService:
    """LLM-based scholarly reranking with domain-aware criteria."""

    def __init__(self, llm: LLMService) -> None: ...

    async def rerank(
        self, query: str, evidence: list[Evidence], top_k: int = 15
    ) -> list[Evidence]:
        """Rerank evidence using LLM scholarly evaluation."""

    async def batch_rerank(
        self, query: str, evidence: list[Evidence],
        top_k: int = 15, batch_size: int = 15
    ) -> list[Evidence]:
        """Batch reranking for large evidence sets."""
```

Candidates capped at 30 per LLM call. Batches of 15 run in parallel for larger sets. Unranked candidates get fallback score of 50.

### 6.3 TreeIndexService

```python
class TreeIndexService:
    """Manages hierarchical tree indices for ancient works (PageIndex-inspired)."""

    def __init__(self, db: DatabaseService) -> None: ...

    async def build_index(self, work_id: str) -> WorkTreeIndex:
        """Build tree index from passages hierarchy.
        Queries passages grouped by citation_hierarchy,
        generates LLM summaries for each tree node."""

    async def load_indices(self, work_ids: list[str]) -> list[WorkTreeIndex]:
        """Load pre-built tree indices for given works."""

    async def extract_passages(
        self, index: WorkTreeIndex, node_ids: list[str]
    ) -> list[Evidence]:
        """Extract full passage text for selected tree nodes."""
```

**WorkTreeIndex model:**

```python
class TreeNode(BaseModel):
    node_id: str
    title: str
    start_passage: int
    end_passage: int
    summary: str
    nodes: list[TreeNode] = Field(default_factory=list)

class WorkTreeIndex(BaseModel):
    work_id: str
    title: str
    author: str
    period: str | None = None
    total_passages: int
    nodes: list[TreeNode]
```

### 6.4 Updated Dependencies Container

```python
@dataclass
class Deps:
    # Core services (required)
    db: DatabaseService
    qdrant: QdrantService
    llm: LLMService

    # Analytics (PageRank / centrality)
    analytics: KGAnalytics | None = None

    # Hybrid search (fulltext + lemmatic + RRF)
    search: HybridSearchService | None = None

    # Weighted graph traversal
    traversal: WeightedTraversal | None = None

    # Cross-encoder reranker
    reranker: RerankerService | None = None

    # Citation verification
    verifier: CitationVerifier | None = None

    # NEW: HyDE service
    hyde: HyDEService | None = None

    # NEW: LLM reranker
    llm_reranker: LLMRerankerService | None = None

    # NEW: Tree index service
    tree_index: TreeIndexService | None = None

    # Pre-loaded KG data
    kg_data: dict[str, Any] = field(default_factory=dict)
    node_lookup: dict[str, dict[str, Any]] = field(default_factory=dict)
    outgoing_edges: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    incoming_edges: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    pagerank_scores: dict[str, float] = field(default_factory=dict)
```

---

## 7. State Changes

### 7.1 New RAGState Fields

```python
@dataclass
class RAGState:
    # --- Input ---
    question: str = ""
    sub_queries: list[str] = field(default_factory=list)

    # --- Classification (NEW: replaces complexity-only) ---
    query_type: QueryType = QueryType.TEMPORAL
    pipeline_config: PipelineConfig = field(default_factory=lambda: DEFAULT_PIPELINE_CONFIG)
    complexity: QueryComplexity = QueryComplexity.MEDIUM  # backwards compat

    # --- Query expansion (NEW) ---
    expanded_query: str | None = None
    expansion_terms: ExpansionTerms | None = None

    # --- Evidence ---
    primary_evidence: list[Evidence] = field(default_factory=list)
    secondary_evidence: list[Evidence] = field(default_factory=list)
    seed_node_ids: list[str] = field(default_factory=list)
    context_node_ids: list[str] = field(default_factory=list)
    accumulated_context: str = ""

    # --- Synthesis ---
    raw_answer: str = ""
    citations: list[Citation] = field(default_factory=list)

    # --- Sufficiency tracking ---
    sufficiency_score: float = 0.0
    iteration: int = 0
    max_iterations: int = 5
    passages_used: int = 0

    # --- CRAG validation (NEW) ---
    crag_validation: CRAGValidation | None = None
    insufficient_evidence: bool = False

    # --- Self-RAG (NEW) ---
    self_rag_evaluation: SelfRAGEvaluation | None = None
    self_rag_iterations: int = 0
    max_self_rag_iterations: int = 2
    quality_badge: str = ""  # "High" / "Medium" / "Low"

    # --- Metadata ---
    metadata: dict[str, Any] = field(default_factory=dict)
```

### 7.2 New EvidenceSource Values

```python
class EvidenceSource(str, Enum):
    SEMANTIC_SEARCH = "semantic_search"
    GRAPH_TRAVERSAL = "graph_traversal"
    HYBRID_SEARCH = "hybrid_search"
    PASSAGE_CITATION = "passage_citation"
    DIRECT_LOOKUP = "direct_lookup"
    HYDE_SEARCH = "hyde_search"              # NEW
    CRAG_SECONDARY = "crag_secondary"        # NEW
    TREE_REASONING = "tree_reasoning"        # NEW
```

### 7.3 Updated ScholarlyAnswer

```python
class ScholarlyAnswer(BaseModel):
    answer: str
    question: str
    complexity: QueryComplexity = QueryComplexity.MEDIUM
    query_type: QueryType = QueryType.TEMPORAL                  # NEW
    citations: list[Citation] = Field(default_factory=list)
    seed_nodes: list[str] = Field(default_factory=list)
    context_nodes: list[str] = Field(default_factory=list)
    passages_used: int = 0
    iterations: int = 1
    sub_queries: list[str] = Field(default_factory=list)
    quality_badge: str = ""                                     # NEW
    self_rag_evaluation: SelfRAGEvaluation | None = None        # NEW
    crag_validation: CRAGValidation | None = None               # NEW
    insufficient_evidence: bool = False                         # NEW
    metadata: dict[str, Any] = Field(default_factory=dict)
```

---

## 8. Pydantic AI Integration

### 8.1 Agent Factory

All structured LLM calls use a shared agent factory pattern:

```python
from pydantic_ai import Agent

def create_agent(result_type: type, system_prompt: str, model: str = "gemini-3-flash") -> Agent:
    """Create a Pydantic AI agent with structured output."""
    return Agent(
        model,
        result_type=result_type,
        system_prompt=system_prompt,
        retries=2,  # automatic retry on validation failure
    )

# Usage in nodes:
classify_agent = create_agent(
    result_type=ClassificationResult,
    system_prompt=CLASSIFY_SYSTEM_PROMPT,
)
result = await classify_agent.run(user_prompt)
# result.data is a ClassificationResult (guaranteed valid)
```

### 8.2 Structured Output Models Summary

| Node | Result Type | Fields |
|------|------------|--------|
| `ClassifyQueryType` | `ClassificationResult` | query_type, confidence, reason |
| `ExpandQuery` | `ExpansionTerms` | greek_terms, latin_terms, philosophers, concepts, schools, periods |
| `EvaluateSufficiency` | `SufficiencyAssessment` | score, sufficient, reason, refinement |
| `TreeReasoningRetrieve` | `TreeNavigationResult` | selected_nodes, reasoning |
| `CRAGValidate` | `CRAGValidation` | relevance, completeness, confidence, missing, suggestions |
| `DualRerank` (LLM stage) | `LLMRerankResult` | rankings (list of id, score, reason) |
| `SelfRAGEvaluate` | `SelfRAGEvaluation` | relevance, grounding, completeness, confidence, caveats, improvements |

### 8.3 Benefits Over Current `_parse_json()`

| Aspect | Current (`_parse_json`) | Pydantic AI Agent |
|--------|------------------------|-------------------|
| Validation | None (raw `json.loads`) | Full Pydantic model validation |
| Malformed output | Crashes or silent corruption | Automatic retry (up to 2x) |
| Type safety | `dict[str, Any]` | Typed model instance |
| Missing fields | KeyError at runtime | Default values or validation error |
| Extra fields | Silently ignored | Stripped or rejected per config |
| Field constraints | None | `Field(ge=0, le=100)` enforced |

---

## 9. Anti-Hallucination Safeguards

### 9.1 Synthesis Prompt Hardening

All synthesis prompts include:

```
CRITICAL INSTRUCTION: Only use information from the provided context.
If the provided evidence does not contain information to answer a
specific aspect of the question, you MUST state:
"The available sources do not address this point."
Do NOT speculate, infer, or generate information beyond what is
explicitly present in the evidence.
```

### 9.2 Enhanced Citation Verification (Fail-Closed)

**Change from current:** The current verifier assumes `True` (supported) on error. The new verifier assumes `False` (NOT supported) on error.

```python
# OLD (fail-open):
except Exception:
    return True  # assume supported

# NEW (fail-closed):
except Exception:
    logger.warning("Verification failed for [%s], marking as unverified", ref)
    return False  # assume NOT supported
```

Unverified citations are included in the output but flagged with `verified=False` and `verification_note="Verification failed — treat as unverified"`. The frontend can display these differently.

### 9.3 Evidence Insufficiency Gate

In `CRAGValidate`:

```python
if crag.confidence < 30 and primary_count < 3:
    ctx.state.insufficient_evidence = True
    ctx.state.metadata["insufficiency_reason"] = (
        f"CRAG confidence {crag.confidence}/100 with only "
        f"{primary_count} primary sources. Insufficient evidence "
        f"to generate a reliable scholarly answer."
    )
```

When `insufficient_evidence` is True, the synthesis nodes generate a response explaining what was found and what is missing, rather than attempting a full answer.

### 9.4 Self-RAG Grounding Check

The `grounding` score in `SelfRAGEvaluation` specifically measures: "Are ALL claims in the answer supported by cited sources?"

- `grounding < 50`: mandatory refinement (regardless of other scores)
- `grounding < 30`: treated as potential hallucination — logged as warning

### 9.5 Ancient Text Policy Enforcement

From `CLAUDE.md`:

> If it's not in the database with a verifiable source, it doesn't exist. Use English instead.

This is enforced by:
1. Never generating Greek/Latin text in synthesis (English paraphrase only)
2. All ancient text quotations come from retrieved `passage.text_content`
3. Citation verification checks that quoted text matches the passage in the DB

---

## 10. Tree Index Precomputation

### 10.1 Script: `scripts/build_work_tree_indices.py`

**Purpose:** Build hierarchical tree indices for all 189 ancient works.

**Algorithm:**

1. For each `ancient_works` row:
   a. Query `passages` ordered by `sequence_number`, grouped by `citation_hierarchy`
   b. Parse hierarchy (e.g., `"Book 1.Chapter 3.Section 2"`) into tree structure
   c. For each tree node (typically 5-30 per work), generate a 100-200 word summary via LLM:
      ```
      Summarize the philosophical content of the following passages
      from {author}'s {title}. Focus on: arguments made, philosophers
      mentioned, key terms used, and conclusions reached.
      Be precise and scholarly. 100-200 words.

      PASSAGES:
      {passage_texts}
      ```
   d. Store as JSON in PostgreSQL `work_tree_indices` table

2. **Cost estimate:** ~189 works x ~20 nodes/work x ~$0.001/summary = ~$4 total

3. **Output:** Also writes `kv_data/work_tree_indices.json` for optional Cloudflare KV upload

### 10.2 Database Table

```sql
CREATE TABLE IF NOT EXISTS free_will.work_tree_indices (
    work_id UUID PRIMARY KEY REFERENCES free_will.ancient_works(work_id),
    tree_index JSONB NOT NULL,
    node_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);
```

### 10.3 Incremental Updates

When the corpus changes (new passages added), re-run the script for affected works only:

```bash
python scripts/build_work_tree_indices.py --work-ids "de_fato,meditations" --force
```

---

## 11. Testing Strategy

### 11.1 Test Structure

```
graphrag/tests/unit/
├── test_graph_nodes.py          # EXISTING (modify for new nodes)
├── test_scholarly_agent.py      # EXISTING (add new query types)
├── test_state.py                # EXISTING (add new state fields)
├── test_classify_query_type.py  # NEW
├── test_expand_query.py         # NEW
├── test_crag_validate.py        # NEW
├── test_dual_rerank.py          # NEW
├── test_tree_reasoning.py       # NEW
├── test_self_rag.py             # NEW
├── test_refine_synthesis.py     # NEW
├── test_hyde_service.py         # NEW
├── test_llm_reranker.py         # NEW
├── test_tree_index_service.py   # NEW
└── test_pipeline_config.py      # NEW
```

### 11.2 Test Counts (Target)

| Category | Tests | Notes |
|----------|-------|-------|
| Existing (regression) | 28 | Must all pass |
| ClassifyQueryType | 8 | 5 types + fallback + confidence + backwards compat |
| ExpandQuery | 7 | LLM expansion, fallback dict, pass-through, routing |
| CRAGValidate | 8 | Valid, invalid + secondary, insufficiency gate, pass-through |
| DualRerank | 7 | Cross-encoder only, dual, pass-through, batch, blending |
| TreeReasoningRetrieve | 8 | Navigation, cross-refs, pass-through, priority filtering |
| FetchPassagesAndLayer | 5 | Passage fetch, layering, routing |
| SelfRAGEvaluate | 7 | High/Medium/Low, refinement trigger, max iterations, pass-through |
| RefineSynthesis | 4 | Refinement, re-verification loop, iteration counter |
| HyDEService | 5 | Generation, search, RRF fusion, error handling |
| LLMRerankerService | 5 | Single batch, multi-batch, score blending, error handling |
| TreeIndexService | 5 | Build, load, extract, hierarchy parsing |
| PipelineConfig | 5 | Config matrix, defaults, query type mapping |
| Integration (full pipeline) | 5 | One per query type, mocked deps |
| **Total** | **~107** | |

### 11.3 Test Patterns

All tests follow existing patterns from `test_graph_nodes.py`:

```python
@pytest.mark.asyncio
async def test_classify_specific_entity():
    """specific_entity classification routes to DirectKGLookup."""
    deps = _make_deps(llm_response='{"query_type":"specific_entity","confidence":0.95,"reason":"..."}')
    state = RAGState(question="Who was Chrysippus?")
    ctx = _make_ctx(state, deps)

    node = ClassifyQueryType()
    result = await node.run(ctx)

    assert isinstance(result, ExpandQuery)
    assert state.query_type == QueryType.SPECIFIC_ENTITY
    assert state.pipeline_config.use_hyde is False
    assert state.pipeline_config.use_tree_reasoning is False
```

Pydantic AI Agents tested with `pydantic_ai.models.test.TestModel` (built-in mock):

```python
from pydantic_ai.models.test import TestModel

async def test_crag_validation_structured():
    """CRAG uses Pydantic AI for structured validation output."""
    test_model = TestModel(custom_result_data=CRAGValidation(
        relevance=80, completeness=70, confidence=75,
        missing=[], suggestions=[]
    ))
    # ... test that the node correctly processes structured output
```

---

## 12. File Changes Summary

### 12.1 New Files

| File | Purpose |
|------|---------|
| `graphrag/src/eleutheria_graphrag/agents/graph_nodes_v2.py` | All 17 FSM nodes (replaces `graph_nodes.py`) |
| `graphrag/src/eleutheria_graphrag/agents/pipeline_config.py` | QueryType, PipelineConfig, config matrix |
| `graphrag/src/eleutheria_graphrag/agents/structured_models.py` | All Pydantic AI result_type models |
| `graphrag/src/eleutheria_graphrag/services/hyde_service.py` | HyDE service |
| `graphrag/src/eleutheria_graphrag/services/llm_reranker.py` | LLM scholarly reranker |
| `graphrag/src/eleutheria_graphrag/services/tree_index.py` | Tree index service |
| `scripts/build_work_tree_indices.py` | Tree index precomputation |
| `database/schema/work_tree_indices.sql` | Tree indices table DDL |
| `graphrag/tests/unit/test_classify_query_type.py` | Classification tests |
| `graphrag/tests/unit/test_expand_query.py` | Expansion tests |
| `graphrag/tests/unit/test_crag_validate.py` | CRAG tests |
| `graphrag/tests/unit/test_dual_rerank.py` | Dual reranking tests |
| `graphrag/tests/unit/test_tree_reasoning.py` | Tree reasoning tests |
| `graphrag/tests/unit/test_self_rag.py` | Self-RAG tests |
| `graphrag/tests/unit/test_refine_synthesis.py` | Refinement tests |
| `graphrag/tests/unit/test_hyde_service.py` | HyDE service tests |
| `graphrag/tests/unit/test_llm_reranker.py` | LLM reranker tests |
| `graphrag/tests/unit/test_tree_index_service.py` | Tree index tests |
| `graphrag/tests/unit/test_pipeline_config.py` | Pipeline config tests |

### 12.2 Modified Files

| File | Changes |
|------|---------|
| `graphrag/src/eleutheria_graphrag/agents/state.py` | Add QueryType, PipelineConfig, new RAGState fields, new EvidenceSource values, updated ScholarlyAnswer |
| `graphrag/src/eleutheria_graphrag/agents/dependencies.py` | Add hyde, llm_reranker, tree_index to Deps |
| `graphrag/src/eleutheria_graphrag/agents/scholarly_agent.py` | Register new nodes in Graph, update entry point |
| `graphrag/src/eleutheria_graphrag/services/citation_verifier.py` | Fail-closed on error |
| `graphrag/tests/unit/test_graph_nodes.py` | Update for modified nodes (HybridRetrieve, EvaluateSufficiency, VerifyCitations) |
| `graphrag/tests/unit/test_scholarly_agent.py` | Add integration tests for new query types |
| `graphrag/tests/unit/test_state.py` | Add tests for new state fields |
| `database/schema/schema.sql` | Add work_tree_indices table |

### 12.3 Unchanged Files

All existing services (`reranker.py`, `weighted_traversal.py`, `llm_service.py`, `citation_verifier.py` logic) remain unchanged. New capabilities are additive — no existing service is replaced or broken.

---

## 13. Dependency Changes

### 13.1 pyproject.toml Updates

```toml
[project]
dependencies = [
    "eleutheria-database>=2.0.0",
    "eleutheria-kg>=2.0.0",
    "pydantic>=2.0.0",
    "httpx>=0.27.0",
    "pydantic-ai[graph]>=1.0.0",      # already present
    "sentence-transformers>=3.0.0",     # already present
    "google-generativeai>=0.5.0",       # move from [llm] optional to core
]
```

No new external dependencies. `pydantic-ai[graph]` and `google-generativeai` (for embeddings) are already installed. The Pydantic AI `Agent` class is included in `pydantic-ai[graph]>=1.0.0`.

---

## 14. Migration and Backwards Compatibility

### 14.1 API Compatibility

`ScholarlyAgent.query()` and `ScholarlyAgent.query_dict()` signatures are unchanged. The `query_dict()` response includes new fields (`query_type`, `quality_badge`, etc.) but all existing fields remain in the same positions.

### 14.2 Graceful Degradation

Every new service in `Deps` is optional (`| None`). If a service is not wired:

- `hyde is None` -> HyDE disabled (standard search only)
- `llm_reranker is None` -> cross-encoder only reranking
- `tree_index is None` -> tree reasoning disabled

This means the existing deployment continues to work without any new infrastructure. New capabilities activate incrementally as services are wired in.

### 14.3 Old Entry Point

`ClassifyComplexity` is removed from the graph. The entry point changes from `ClassifyComplexity()` to `ClassifyQueryType()`. The `scholarly_graph` definition in `scholarly_agent.py` is updated to register all 17 nodes.

---

## 15. Performance Considerations

### 15.1 Latency Budget

| Stage | Estimated Latency | Notes |
|-------|-------------------|-------|
| ClassifyQueryType | 0.5-1s | Single LLM call |
| ExpandQuery | 0.5-1s | Single LLM call (or instant for fallback) |
| Retrieval (vector + graph) | 1-3s | Existing, unchanged |
| HyDE augmentation | 1-2s | Parallel with retrieval |
| TreeReasoningRetrieve | 3-8s | LLM reads tree indices for 3-5 works |
| CRAGValidate | 1-2s | Single LLM call; +2-3s if secondary retrieval |
| DualRerank | 2-4s | Cross-encoder ~0.5s + LLM ~2s |
| FetchPassagesAndLayer | 0.5-1s | SQL query |
| Synthesis | 3-8s | LLM generation |
| VerifyCitations | 1-3s | 1 LLM call per citation (parallelized) |
| SelfRAGEvaluate | 1-2s | Single LLM call |
| **Total (simple query)** | **~8-15s** | No tree reasoning, no HyDE |
| **Total (complex query)** | **~15-30s** | All stages active |

### 15.2 LLM Call Budget

| Query Type | LLM Calls | Cost Estimate |
|------------|-----------|---------------|
| `specific_entity` | 4-6 | ~$0.01 |
| `global_abstract` | 6-8 | ~$0.02 |
| `multi_hop` | 8-12 | ~$0.03-0.05 |
| `comparative` | 8-12 | ~$0.03-0.05 |

### 15.3 Parallelization Opportunities

- HyDE search runs in parallel with standard retrieval (`asyncio.gather`)
- Cross-encoder and LLM reranking are sequential (LLM needs cross-encoder output)
- Citation verification calls run in parallel per citation (`asyncio.gather`)
- CRAG secondary retrieval queries run in parallel
- Expansion terms embedding runs in parallel

---

## 16. Future Work (Out of Scope)

These are noted for future phases but explicitly out of scope for this design:

1. **Passage-to-passage citation graph** — Populate `passage_relationships` table using LLM-based citation detection. Would enable true document-level PageRank.
2. **Contextual embeddings re-indexing** — Re-embed passages with authority scores in the payload for Qdrant boost filtering.
3. **Streaming synthesis** — True token-by-token streaming in `SynthesizeWithHierarchy` instead of post-hoc chunking.
4. **TypeScript port** — Port new Python nodes back to TypeScript Cloudflare Workers for edge deployment.
5. **Hybrid routing** — Route simple queries to TypeScript (edge, fast), complex queries to Python (server, high quality).
6. **Agentic tool calling** — Let the LLM decide dynamically when to retrieve more via tool calls rather than fixed pipeline stages.

---

## Appendix A: Full Node Type Signatures

```python
ClassifyQueryType.run()        -> ExpandQuery
ExpandQuery.run()              -> DirectKGLookup | HybridRetrieve | DecomposeQuery
DirectKGLookup.run()           -> TreeReasoningRetrieve
HybridRetrieve.run()           -> TreeReasoningRetrieve
DecomposeQuery.run()           -> SearchPrimarySources
SearchPrimarySources.run()     -> EvaluateSufficiency
EvaluateSufficiency.run()      -> SearchPrimarySources | TreeReasoningRetrieve
TreeReasoningRetrieve.run()    -> CRAGValidate
CRAGValidate.run()             -> DualRerank
DualRerank.run()               -> FetchPassagesAndLayer
FetchPassagesAndLayer.run()    -> Synthesize | SearchSecondarySources
SearchSecondarySources.run()   -> SynthesizeWithHierarchy
Synthesize.run()               -> VerifyCitations
SynthesizeWithHierarchy.run()  -> VerifyCitations
VerifyCitations.run()          -> SelfRAGEvaluate
SelfRAGEvaluate.run()          -> End[ScholarlyAnswer] | RefineSynthesis
RefineSynthesis.run()          -> VerifyCitations
```

## Appendix B: Pipeline Config Defaults

```python
PIPELINE_CONFIGS: dict[QueryType, PipelineConfig] = {
    QueryType.SPECIFIC_ENTITY: PipelineConfig(
        use_hyde=False, use_crag=True, use_reranking=True,
        use_self_rag=True, use_expansion=True, use_tree_reasoning=False,
    ),
    QueryType.GLOBAL_ABSTRACT: PipelineConfig(
        use_hyde=True, use_crag=True, use_reranking=True,
        use_self_rag=True, use_expansion=False, use_tree_reasoning=False,
    ),
    QueryType.MULTI_HOP: PipelineConfig(
        use_hyde=False, use_crag=True, use_reranking=False,
        use_self_rag=True, use_expansion=True, use_tree_reasoning=True,
    ),
    QueryType.COMPARATIVE: PipelineConfig(
        use_hyde=True, use_crag=True, use_reranking=True,
        use_self_rag=True, use_expansion=True, use_tree_reasoning=True,
    ),
    QueryType.TEMPORAL: PipelineConfig(
        use_hyde=True, use_crag=True, use_reranking=True,
        use_self_rag=True, use_expansion=True, use_tree_reasoning=True,
    ),
}
```
