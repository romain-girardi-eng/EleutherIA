# EleutherIA Full Optimization Plan

**Date:** 2026-03-31
**Goal:** Reduce GraphRAG latency from 112-236s to <30s, improve retrieval quality, and fill KG gaps.

---

## Phase A: Pipeline Speed (112s → <30s)

### A1. Parallelize TreeNavigateWorks LLM calls
**Impact:** HIGHEST. Currently 5-50 sequential LLM calls (~2-5s each). With `asyncio.gather()`, goes from O(N × latency) to O(latency).
- Change the per-work loop (lines 4649-4700) to dispatch all `_navigate_sections_with_llm()` calls concurrently
- Cap at 10 parallel calls to avoid rate limiting
- **Expected gain: -50 to -200s on complex queries**

### A2. Parallelize ExpandEvidenceBundles DB calls
**Impact:** HIGH. Currently 100-200+ sequential DB calls (passage extraction + translation lookup per passage).
- Batch `extract_passages()` into one SQL query for all sections
- Batch `_fetch_translation_for_passage()` into one query with all passage IDs
- **Expected gain: -5 to -15s**

### A3. Skip polish step in RenderGroundedAnswer
**Impact:** MEDIUM. The "scholarly polish" is a full extra LLM call after synthesis. In practice, synthesis quality is good enough.
- Make polish conditional: only run if synthesis answer length < 500 chars or fails a quality heuristic
- **Expected gain: -3 to -8s per query**

### A4. Response-level cache (semantic)
**Impact:** MEDIUM. Same questions recur ("What is Stoic fate?"). Cache full responses for 10min.
- In-memory dict keyed by `(normalized_query, model, mode)` hash
- TTL 10 minutes, max 100 entries
- **Expected gain: instant response (<100ms) on cache hit (~80% estimated hit rate for repeated queries)**

### A5. Smarter ClassifyQueryType heuristic
**Impact:** LOW-MEDIUM. Currently only SPECIFIC_ENTITY gets the heuristic fast-path. Extend to detect SIMPLE queries without an LLM call.
- Pattern: query < 10 words, contains a known philosopher/concept name → SIMPLE
- **Expected gain: -1 to -3s on simple queries**

---

## Phase B: KG Quality (direct retrieval improvement)

### B1. Add passage_citations for ~256 `needs_evidence` nodes
**Impact:** CRITICAL. These are arguments, concepts, debates — the core query targets — invisible to SQLStrategy step 1.
- Script: query `kg_nodes` for `metadata->>'needs_evidence' = 'true'`
- For each: find the best matching passage in `passages` via FTS, insert into `passage_citations`
- Can be semi-automated: LLM identifies the best passage, human verifies
- **Expected gain: +30-50% SQL retrieval hit rate**

### B2. Create position nodes + holds_position edges
**Impact:** HIGH. Queries about compatibilism/determinism/libertarianism (the core domain) have no graph routing.
- Create ~8 position nodes: compatibilism, hard_determinism, libertarianism, fatalism, soft_determinism, academic_skepticism, theological_determinism, indeterminism
- Add `holds_position` edges for ~40 persons/schools
- **Expected gain: dramatically better routing for the most common query types**

### B3. Complete P0 translations (96 remaining)
**Impact:** HIGH. English FTS is the backbone of SQLStrategy step 2. Greek/Latin passages return near-zero ts_rank.
- Resume `batch_translate_passages.py --priority P0 --resume`
- Use OpenRouter (Qwen 3.5 Plus at $0.26/1M) instead of Gemini to avoid spending cap
- **Expected gain: step 2 FTS becomes useful for core texts**

### B4. Add `discusses` edges for ingested works
**Impact:** MEDIUM. Step 2bis resolves works via `discusses` edges. Most Scaife-ingested works lack these.
- For each work with passages: add 3-5 `discusses` edges to the most relevant concepts
- ~12 works × 4 edges = ~48 edges
- **Expected gain: better work-to-concept routing in step 2bis**

### B5. Fix `_en` nodes missing `part_of` edges
**Impact:** LOW. Translation nodes without `part_of` break tree loading.
- Single SQL CTE to back-fill from source node's `part_of`
- **Expected gain: complete tree navigation for translated works**

---

## Phase C: Architecture Polish

### C1. Remove debug logging from SQLStrategy
- Clean up the diagnostic `logger.info` calls added during debugging

### C2. Add response metrics to all queries
- Return `input_tokens`, `output_tokens`, `estimated_cost_usd` in every response
- Calculate from model registry pricing

### C3. Frontend: wire ResponseTabs + ReasoningPanel
- Complete the tab-based multi-response UI
- Wire ReasoningPanel to display FSM trace per tab

---

## Execution Order

```
A1 (parallel TreeNav)     ← biggest latency win, do first
A2 (parallel DB calls)    ← second biggest, independent of A1
B1 (passage_citations)    ← biggest quality win, can run in parallel with A1/A2
B2 (position nodes)       ← quick, high impact
A4 (response cache)       ← easy, good ROI
B3 (translations)         ← batch job, can run overnight
A3 (skip polish)          ← easy 1-line change
B4 (discusses edges)      ← medium effort
C1 (cleanup)              ← trivial
B5 (part_of fix)          ← trivial SQL
A5 (smarter heuristic)    ← low priority
C2 (metrics)              ← nice to have
C3 (frontend wiring)      ← when everything else works
```

## Expected End State

| Metric | Before | After |
|---|---|---|
| SQL mode latency (simple) | 112s | <15s |
| SQL mode latency (complex) | 236s | <45s |
| SQL step 1 hit rate | ~60% | ~90% |
| FTS on core texts | Greek only | English available |
| Position query routing | text match only | graph-guided |
| Cache hit response time | N/A | <100ms |
