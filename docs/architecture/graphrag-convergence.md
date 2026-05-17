# GraphRAG Convergence: Pipeline Enhancement Report

**Date:** 2026-02-13
**Branch:** `main` (commits `0f70aea`, `7eec0f3`)
**Production:** https://free-will.app

## Status

This February 2026 report is historical. The production backend now uses the Python/FastAPI agentic GraphRAG stack with vectorless SQLStrategy retrieval: lemma expansion, tree routing, KG label/description matching, `passage_citations`, and full-text/lemmatic RRF. The Cloudflare Worker/vector-search path described below is no longer the active architecture.

## Overview

The GraphRAG Convergence plan unified two parallel agentic implementations into a single production pipeline on Cloudflare Workers:

- **Python side:** Pydantic-graph FSM (`ScholarlyAgent`) with 10 reasoning nodes
- **TypeScript side:** `AgenticOrchestrator` on Cloudflare Workers with 6 retrieval services

The convergence wired 12 previously disconnected TypeScript services into the production orchestrator, added passage-level retrieval with evidence layering, ported the weighted graph traversal from Python to TypeScript, and deployed precomputed PageRank + Leiden community data to Cloudflare KV.

## Architecture

### Pipeline Stages (Post-Convergence)

```
Query
  |
  v
[1. Query Classification] --- specific_entity | global_abstract | multi_hop | comparative
  |
  v
[2. Pipeline Config Selection] --- auto-selects HyDE, CRAG, reranking, expansion per query type
  |
  v
[3. Query Expansion] --- Greek/Latin philological terms (e.g. to eph' hemin, heimarmene)
  |
  v
[4. HyDE] --- Hypothetical Document Embeddings for semantic gap bridging
  |
  v
[5. Legacy Vector Search] --- retired vector top-k path with fused standard + HyDE results
  |
  v
[6. Weighted Graph Traversal] --- PageRank-boosted min-heap BFS with edge-type multipliers
  |
  v
[7. CRAG Validation] --- Corrective RAG checks retrieval relevance
  |
  v
[8. LLM Reranking] --- Domain-specific reranking via Gemini
  |
  v
[9. Passage Retrieval] --- Supabase REST: passage_citations -> passages -> ancient_works
  |
  v
[10. Evidence Layering] --- Primary (ancient) / Secondary (modern) partitioning
  |
  v
[11. Sufficiency Check] --- LLM-driven re-retrieval loop (max 3 iterations)
  |
  v
[12. Synthesis + Citations] --- LLM answer generation with source mapping
  |
  v
[13. Self-RAG Evaluation] --- Post-generation quality assessment
  |
  v
Response (answer + sources + evidence + quality metrics)
```

### Pipeline Config Per Query Type

| Query Type | HyDE | CRAG | Reranking | Self-RAG | Expansion | Grounding |
|-----------|------|------|-----------|----------|-----------|-----------|
| `specific_entity` | Off | On | On | On | On | On |
| `global_abstract` | On | On | On | On | Off | On |
| `multi_hop` | Off | On | Off | On | On | On |
| `comparative` | On | On | On | On | On | On |

### New Services Added

| Service | File | Purpose |
|---------|------|---------|
| Passage Retrieval | `passage-retrieval.ts` | Fetches ancient text passages via Supabase REST (joins passage_citations, passages, ancient_works) |
| Evidence Layering | `evidence-layering.ts` | Partitions evidence into primary (ancient sources) and secondary (modern scholarship), builds hierarchical context |
| Weighted Traversal | `weighted-traversal.ts` | Min-heap BFS with edge-type multipliers and PageRank centrality scoring |
| Graph Data Store | `graph-data-store.ts` | Shared KV-cached loader for nodes, edges, and PageRank scores |

### Weighted Traversal Scoring

```
score = parentScore * edgeWeight * typeMultiplier * (0.5 + centrality) * decay
```

**Edge Category Multipliers:**

| Category | Multiplier | Relations |
|----------|-----------|-----------|
| Argumentative | 1.5x | argues_for, argues_against, responds_to, objects_to |
| Doctrinal | 1.3x | develops, reforms, adopts, rejects |
| Intellectual | 1.2x | influences, influenced_by, student_of, teacher_of |
| Semantic | 1.1x | related_to, discusses, mentions |
| Hermeneutic | 0.6x | interprets, comments_on, cites |
| Temporal | 0.5x | contemporary_of, precedes, succeeds |

### LLM Task Routing

| Task Type | Primary Provider | Fallback |
|-----------|-----------------|----------|
| Synthesis, Reasoning | Kimi K2.5 (256k context) | Gemini 3 Flash |
| Classification, Reranking, Sufficiency | Gemini 3 Flash | - |
| Expansion, Citation Verification | Gemini 3 Flash | - |

## Precomputed Data (Cloudflare KV)

**Script:** `scripts/precompute_kg_data.py`

Computed from 2,193 nodes and 8,616 edges:

| KV Key | Size | Content |
|--------|------|---------|
| `pagerank_scores` | 89 KB | Node ID to PageRank score map (alpha=0.85) |
| `kg_nodes_index` | 261 KB | All nodes as `{id, label, type}` array |
| `kg_edges_index` | 1.1 MB | All edges as `{source, target, relation, weight}` array |

**PageRank Top 5:**

| Node | Score | Type |
|------|-------|------|
| Heimarmene (Stoic Fate) | 0.0347 | concept |
| To Eph' Hemin (What is In Our Power) | 0.0343 | concept |
| Alexander of Aphrodisias | 0.0251 | person |
| Endechomenon (Contingent) | 0.0242 | concept |
| De Fato (Alexander) | 0.0222 | work |

**Leiden Community Detection (3-level hierarchy):**

| Level | Resolution | Communities | Modularity |
|-------|-----------|-------------|------------|
| 0 (coarse) | 0.50 | 23 | 0.6655 |
| 1 (balanced) | 1.00 | 25 | 0.6671 |
| 2 (fine) | 2.00 | 38 | 0.5688 |

## A/B Test Results

### Test Setup

- **Old system:** Previously deployed Cloudflare Workers (no weighted traversal, no PageRank, no evidence layering)
- **New system:** Post-convergence deployment with all 6 wired services + PageRank in KV
- **Queries tested:** 3 (entity lookup, comparative, multi-hop)

### Query 1: "What did Chrysippus believe about fate and human responsibility?"

| Metric | Old System | New System |
|--------|-----------|------------|
| Quality Score | 83 (High) | 83 (High) |
| Processing Time | 73.5s | 77.8s |
| Sources | 28 | 27 |
| Textual Groundings | 8 | 8 |
| Evidence Chains | 5 | 5 |
| CTS URNs | 8 | 8 |
| Bridge Mode | No | No |

**Analysis:** Single-entity queries produce equivalent results. The core retrieval path is unchanged for simple lookups.

### Query 2: "How did the Stoics and Epicureans differ on free will?"

| Metric | Old System | New System |
|--------|-----------|------------|
| Quality Score | 83 (High) | 83 (High) |
| Processing Time | 109.3s | 85.1s |
| Query Type | comparative | comparative |
| Sources | 26 | 26 |
| Evidence Chains | 4 | 5 |

**Analysis:** 24-second speed improvement. Additional evidence chain detected.

### Query 3: "Trace the chain of influence from Aristotle through the Stoics to Augustine on moral responsibility"

| Metric | New System |
|--------|------------|
| Quality Score | 83 (High) |
| Processing Time | 75.2s |
| Query Type | `multi_hop` (conf 0.9) |
| Sources | 25 |
| Textual Groundings | 7 (original Greek/Latin) |
| Evidence Chains | 4 |
| **Bridge Mode** | **True** |
| Unique Authors | 10 |

**Authors found (in chronological order):**
1. Aristotle (4th c. BCE)
2. Marcus Tullius Cicero (1st c. BCE)
3. Aulus Gellius (2nd c. CE)
4. Plutarch (1st-2nd c. CE)
5. Plotinus (3rd c. CE)
6. Origen (3rd c. CE)
7. Eusebius (4th c. CE)
8. Justin Martyr (2nd c. CE)
9. Theodoret (5th c. CE)
10. Augustine of Hippo (4th-5th c. CE)

**Analysis:** This is the key improvement. The old system would have treated this as a generic query. The new system:
- Correctly classified as `multi_hop`
- Activated bridge mode to trace influence chains
- Found authors spanning the entire requested temporal arc (Aristotle through Augustine)
- Included transitional figures (Plotinus, Origen) that bridge Greco-Roman and Christian thought

## Files Changed

### New Files (8)

| File | Lines | Purpose |
|------|-------|---------|
| `deploy/cloudflare/src/services/passage-retrieval.ts` | 168 | Passage-level retrieval via Supabase |
| `deploy/cloudflare/src/services/evidence-layering.ts` | 144 | Primary/secondary evidence partitioning |
| `deploy/cloudflare/src/services/weighted-traversal.ts` | 254 | PageRank-boosted graph BFS |
| `deploy/cloudflare/src/services/graph-data-store.ts` | 173 | KV-cached graph data loader |
| `deploy/cloudflare/tests/weighted-traversal.test.ts` | 162 | 9 tests for traversal |
| `deploy/cloudflare/tests/evidence-layering.test.ts` | 149 | 13 tests for layering |
| `deploy/cloudflare/tests/pipeline-config.test.ts` | 70 | 5 tests for config selection |
| `scripts/precompute_kg_data.py` | 604 | PageRank + Leiden precomputation |

### Modified Files (5)

| File | Changes |
|------|---------|
| `deploy/cloudflare/src/services/agentic/orchestrator.ts` | Wired 6 services, added sufficiency loop, pipeline config |
| `deploy/cloudflare/src/services/llm.ts` | Added `generateForTask()` for task-based model routing |
| `deploy/cloudflare/src/types/agentic.ts` | Added PipelineConfig, passage fields, SufficiencyResult |
| `graphrag/src/eleutheria_graphrag/models/query.py` | Added SourceCitation, EvidenceMapEntry, QualityMetrics |
| `backend/routes/graphrag_extras.py` | Added evidenceMap, qualityMetrics, confidence to response |

### Test Results

| Suite | Tests | Status |
|-------|-------|--------|
| TypeScript (Vitest) | 27 | All passing |
| Python (pytest) | 28 | All passing |
| **Total** | **55** | **All passing** |

## Deployment

```bash
# 1. Precompute KG data (PageRank + Leiden)
DATABASE_URL='...' python3 scripts/precompute_kg_data.py --upload-kv

# 2. Upload to Cloudflare KV (if not using --upload-kv)
cd deploy/cloudflare
npx wrangler kv key put "pagerank_scores" --namespace-id <id> --path kv_data/pagerank_scores.json --remote
npx wrangler kv key put "kg_nodes_index" --namespace-id <id> --path kv_data/kg_nodes_index.json --remote
npx wrangler kv key put "kg_edges_index" --namespace-id <id> --path kv_data/kg_edges_index.json --remote

# 3. Deploy Workers
npx wrangler deploy
```

**KV Namespace ID:** `9506f86aab4845818bd7644508d504e6`

## Known Limitations

1. **Evidence quality badge** stays at "Fair" (0.5) due to simplified scoring in the current pipeline; a future pass should weight PageRank-boosted nodes higher in the quality calculation.
2. **Bridge paths** are not yet reported in the response metadata (count shows 0 even when bridge mode is active) — the bridge retrieval service logs internally but doesn't surface path details.
3. **Precompute script** requires manual re-run when the KG changes; consider a scheduled Cloudflare Cron Trigger or GitHub Action.
4. **Pydantic-AI ScholarlyAgent** (Python FSM) is not used in the Cloudflare Workers pipeline. It remains available for the FastAPI backend but is a separate execution path.

---

## Superseded by PageIndex V3 (2026-02-20)

The former 13-stage HiRAG V2 pipeline documented above has been replaced by **PageIndex V3**, a direct retrieval architecture that reduces the pipeline to 5 steps and 2 LLM calls. The key insight: with Gemini's ~1M token context window and the curated `passage_citations` database, most of the meta-reasoning stages (HyDE, CRAG, Self-RAG, LLM reranking, query expansion) were adding latency and compounding errors without improving answer quality.

See [PageIndex V3 documentation](PAGEINDEX_V3.md) for the current architecture.
