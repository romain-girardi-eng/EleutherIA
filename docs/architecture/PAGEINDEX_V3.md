# PageIndex V3: Direct Agentic Search

**Date:** 2026-02-20
**Version:** v5.0.0
**Production:** https://free-will.app

## Summary

PageIndex V3 replaces the former HiRAG V2 pipeline (13 stages) with a direct retrieval architecture that leverages the curated `passage_citations` database and modern LLM context windows (~1M tokens). Instead of 10+ LLM calls per query (HyDE, CRAG, Self-RAG, LLM reranking, query expansion, sufficiency checks), PageIndex V3 uses **2 LLM calls**: one embedding and one synthesis.

## Motivation

The former HiRAG V2 pipeline (deployed Feb 13, 2026) suffered from:

1. **Over-engineering:** 13 pipeline stages with 10+ LLM calls per query added latency and compounding error
2. **Aggressive truncation:** Context was sliced at 500-800 characters, destroying Greek diacritics and corrupting passage text before it reached the synthesis LLM
3. **Underutilized passage_citations:** The most valuable retrieval signal (curated KG-to-passage links with confidence scores) was buried behind multiple reranking stages
4. **Unnecessary meta-reasoning:** With 17k passages and Gemini's 1M token context, we don't need 10 LLM calls to find and validate context — we need ONE good retrieval step and ONE good synthesis call

## Architecture

### Pipeline (5 steps, 2 LLM calls)

```
User Question
    │
    ▼
┌─────────────────────────────────────┐
│ Step 1: Embed + Detect References   │  ONE embedding call
│   Query → Gemini embedding          │  + regex CTS URN detection
│   + passage reference detection     │
└──────────────────┬──────────────────┘
                   │
                   ▼
┌─────────────────────────────────────┐
│ Step 2: Parallel Search (no LLM)    │  3 Qdrant queries in parallel
│   KG nodes + text passages + edges  │  Pure vector similarity
└──────────────────┬──────────────────┘
                   │
                   ▼
┌─────────────────────────────────────┐
│ Step 3: Parallel Enrichment         │  3 DB queries in parallel
│   passage_citations lookup          │  Supabase REST (no LLM)
│   + KG neighbor expansion           │
│   + textual grounding               │
└──────────────────┬──────────────────┘
                   │
                   ▼
┌─────────────────────────────────────┐
│ Step 4: Build FULL Context          │  No truncation
│   Primary sources (passage_citations)│  Gemini handles ~1M tokens
│   + supplementary passages           │
│   + KG entities + relationships      │
└──────────────────┬──────────────────┘
                   │
                   ▼
┌─────────────────────────────────────┐
│ Step 5: ONE Synthesis Call          │  ONE LLM call
│   Strong scholarly prompt            │  Anti-hallucination instructions
│   → Answer with citations            │  Full passage text available
└──────────────────┬──────────────────┘
                   │
                   ▼
            Answer + Sources
```

### Key Design Decisions

1. **No HyDE** — Gemini embeddings are strong enough for direct semantic search on this corpus
2. **No query expansion** — The embedding model handles Greek/Latin terms well; expansion added noise
3. **No CRAG validation** — With full passage text in context, the LLM can self-validate
4. **No LLM reranking** — Vector similarity + passage_citations confidence scores suffice
5. **No Self-RAG** — Quality comes from giving the LLM complete, untruncated source text
6. **No truncation** — Gemini's 1M token context handles the full corpus context

### Core Retrieval: passage_citations

The `passage_citations` table is the primary retrieval signal. It links KG node IDs to actual ancient text passages with confidence scores:

```
kg_nodes → passage_citations → passages → ancient_works
```

Query via Supabase PostgREST embedded resources:
```
GET /rest/v1/passage_citations
  ?kg_node_id=in.(id1,id2,...)
  &select=citation_id,kg_node_id,confidence,passages!inner(
    passage_id,cts_urn,canonical_ref,text_content,
    ancient_works!inner(author,title,language)
  )
  &order=confidence.desc.nullslast
  &limit=100
```

### Context Structure

The context builder produces four sections with NO truncation:

1. **PRIMARY ANCIENT SOURCES** — From passage_citations (highest quality, with CTS URNs)
2. **SUPPLEMENTARY PASSAGES** — From semantic search (vector similarity)
3. **KNOWLEDGE GRAPH ENTITIES** — Seed nodes with descriptions
4. **RELATIONSHIPS & CONNECTIONS** — KG neighbors and edges

## What Was Removed

| Removed Stage | Why |
|---------------|-----|
| HyDE (Hypothetical Document Embeddings) | Added latency; direct embeddings work well on this corpus |
| Query Classification | Unnecessary routing complexity; one pipeline handles all query types |
| Query Expansion | Greek/Latin expansion added noise; embedding model handles terms directly |
| CRAG Validation | Full context lets the LLM self-validate |
| LLM Reranking | Vector similarity + confidence scores are sufficient |
| Sufficiency Loop | Removed re-retrieval iterations; single retrieval pass is sufficient |
| Self-RAG Evaluation | Quality comes from complete source text, not post-hoc evaluation |
| Evidence Layering | Simplified to direct section-based context building |
| Weighted Traversal | Replaced with simpler 1-hop neighbor expansion |
| Pipeline Config Selection | Single pipeline for all query types |

## Files

### New
| File | Purpose |
|------|---------|
| `deploy/cloudflare/src/services/pageindex-retrieval.ts` | Core retrieval: passage_citations lookup, KG neighbor expansion, context builder |

### Modified
| File | Changes |
|------|---------|
| `deploy/cloudflare/src/routes/graphrag.ts` | Replaced `/answer` endpoint with PageIndex V3 pipeline (~700 lines removed, ~250 added) |
| `deploy/cloudflare/src/services/llm.ts` | Fixed SSE line-splitting bug (TCP buffer handling) |

### Removed (from active pipeline)
| File | Status |
|------|--------|
| `deploy/cloudflare/src/services/passage-retrieval.ts` | Superseded by pageindex-retrieval.ts |
| `deploy/cloudflare/src/services/evidence-layering.ts` | No longer needed |
| `deploy/cloudflare/src/services/weighted-traversal.ts` | Replaced by simple neighbor query |
| `deploy/cloudflare/src/services/graph-data-store.ts` | No longer needed |
| `deploy/cloudflare/src/services/agentic/orchestrator.ts` | Removed; logic inlined in route |

## API Response

The `/answer` endpoint response now includes a `pageIndexInfo` field:

```json
{
  "answer": "...",
  "citations": [...],
  "sources": [...],
  "pageIndexInfo": {
    "linkedPassagesCount": 12,
    "neighborsCount": 8,
    "semanticPassagesCount": 5,
    "totalContextChars": 28500,
    "estimatedTokens": 7125
  }
}
```

Removed fields from the former HiRAG V2 pipeline: `hiragInfo`, `queryExpansion`, `cragValidation`, `selfEvaluation`, `hydeDetails`.

## Results

- **Bundle size:** 628 KiB (former HiRAG V2) → 606 KiB (PageIndex V3)
- **LLM calls per query:** 10+ → 2
- **Context quality:** Full passage text with CTS URNs instead of 500-char truncated fragments
- **Latency:** Significantly reduced (fewer LLM round-trips)

## Backward Compatibility

- `/answer/hirag-v2` and `/answer/v2` legacy aliases forward to the new PageIndex V3 endpoint
- Frontend receives the same response shape (answer, citations, sources, metadata)
- The `pageIndexInfo` field is additive; old clients ignore it
