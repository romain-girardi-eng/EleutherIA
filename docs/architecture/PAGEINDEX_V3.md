# PageIndex V3: Superseded Direct Search Design

**Date:** 2026-02-20
**Version:** v5.0.0
**Production:** https://free-will.app

## Summary

PageIndex V3 was the February 2026 direct-retrieval design. It has since been superseded by the current agentic vectorless GraphRAG pipeline: SQLStrategy, lemma expansion, tree routing, KG label/description matching, `passage_citations`, and full-text/lemmatic RRF. This document is retained as architecture history.

## Motivation

The former HiRAG V2 pipeline (deployed Feb 13, 2026) suffered from:

1. **Over-engineering:** 13 pipeline stages with 10+ LLM calls per query added latency and compounding error
2. **Aggressive truncation:** Context was sliced at 500-800 characters, destroying Greek diacritics and corrupting passage text before it reached the synthesis LLM
3. **Underutilized passage_citations:** The most valuable retrieval signal (curated KG-to-passage links with confidence scores) was buried behind multiple reranking stages
4. **Unnecessary meta-reasoning:** With 17k passages and Gemini's 1M token context, we don't need 10 LLM calls to find and validate context — we need ONE good retrieval step and ONE good synthesis call

## Architecture

### Current Successor Pipeline

```
User Question
    │
    ▼
┌─────────────────────────────────────┐
│ Step 1: Expand + Detect References  │  terms + lemmas
│   CTS URN / passage references      │  + author/work mentions
└──────────────────┬──────────────────┘
                   │
                   ▼
┌─────────────────────────────────────┐
│ Step 2: Vectorless Discovery        │  SQLStrategy
│   tree + KG labels + citations      │  + full-text/lemmatic RRF
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

1. **No vector store dependency** — production retrieval is SQL/tree/lemma/citation based
2. **LLM-driven lemma expansion** — Greek/Latin terms are expanded before lookup
3. **Tree routing** — author/work mentions route directly to hierarchical passage anchors
4. **Curated citation anchors** — `passage_citations` is the primary evidence bridge
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
2. **SUPPLEMENTARY PASSAGES** — From full-text/lemmatic search and tree-routed anchors
3. **KNOWLEDGE GRAPH ENTITIES** — Seed nodes with descriptions
4. **RELATIONSHIPS & CONNECTIONS** — KG neighbors and edges

## What Was Removed

| Removed Stage | Why |
|---------------|-----|
| HyDE (Hypothetical Document Embeddings) | Added latency; replaced by lemma expansion and curated evidence routing |
| Query Classification | Unnecessary routing complexity; one pipeline handles all query types |
| Vector search | Replaced by SQLStrategy, tree routing, and passage_citations |
| CRAG Validation | Full context lets the LLM self-validate |
| LLM Reranking | Current pipeline uses deterministic retrieval signals plus verification |
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
