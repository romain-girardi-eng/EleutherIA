# Two-Node Passage Architecture: Source + English Translation

**Date:** 2026-02-24
**Author:** Romain Girardi
**Status:** IMPLEMENTED (De Fato), IN PROGRESS (all passages)

---

## Problem

Passage KG nodes contain descriptions in their original language (Greek, Latin). The GraphRAG pipeline's first retrieval step is Qdrant vector similarity search, where user queries (typically in English) are embedded and compared against node description embeddings.

**Greek/Latin-only passage descriptions are invisible to English semantic search.** A query like "What does Alexander say about fate?" produces near-zero similarity with `Ἀλέξανδρος Ἀφροδισιεὺς πεποίηται τήνδε τὴν πραγματείαν...` because the embedding spaces for English and ancient Greek barely overlap.

This means the pipeline's most valuable nodes — primary source passages — are unreachable unless a passage_citation link already exists. Direct agentic search and open-ended queries miss them entirely.

## Solution: Two-Node Architecture

For every passage node, create two linked nodes:

```
┌──────────────────────┐     translation_of     ┌──────────────────────┐
│  passage_alex_fat_1  │ ◄──────────────────── │ passage_alex_fat_1_en│
│                      │                        │                      │
│  type: passage       │                        │  type: passage       │
│  lang: grc           │                        │  lang: eng           │
│  description: Greek  │                        │  description: English│
│  (authoritative)     │                        │  (AI translation)    │
└──────────────────────┘                        └──────────────────────┘
```

### Greek/Latin Node (Source of Truth)
- **Untouched.** Pure original text in description field.
- **Zero hallucination.** Text comes directly from CTS API or verified corpus.
- Node ID: existing convention (e.g., `passage_alex_fat_1`)
- `metadata.language`: `grc` or `lat`

### English Translation Node (RAG-Discoverable)
- **Separate node.** AI-translated English in description field.
- **Clearly marked.** `metadata.source: "ai_translation"`, `metadata.source_model: "claude-opus-4-6"`
- Node ID: `{original_id}_en` (e.g., `passage_alex_fat_1_en`)
- `metadata.language`: `eng`
- Linked via `translation_of` edge (target → source)

### Edges

Each English node gets:
1. `translation_of` → original passage node
2. `part_of` → work node (same as original)
3. `authored_by` → person node (same as original)

The `translation_of` edge metadata includes:
```json
{
  "auto_generated": true,
  "source_model": "claude-opus-4-6",
  "source_language": "grc"
}
```

## Why Two Nodes (Not One Bilingual Node)

| Approach | Pros | Cons |
|----------|------|------|
| **Bilingual description** | Simpler, fewer nodes | Mixes AI text with authoritative source; embedding is diluted; unclear what's original vs translated |
| **English-only description** | Good for search | Destroys the primary source; violates zero-hallucination policy |
| **Two nodes (chosen)** | Source text untouched; English discoverable; clear provenance; each node has focused embedding | More nodes and edges |

The two-node approach respects the project's **zero-hallucination policy** while solving the RAG discoverability problem. The `source: "ai_translation"` metadata makes provenance unambiguous.

## RAG Pipeline Impact

### Before (Greek-only passages)
```
English query → Qdrant → ❌ Greek passages invisible → only finds passages via passage_citations
```

### After (Greek + English nodes)
```
English query → Qdrant → ✅ English _en nodes discovered → translation_of edge → original Greek text
```

The pipeline can:
1. Find relevant passages via English semantic search
2. Follow `translation_of` edges to get authoritative Greek/Latin text
3. Present both to the synthesis LLM with clear provenance

## Node ID Convention

```
{original_node_id}_en
```

Examples:
- `passage_alex_fat_1_en` (De Fato chapter 1 English)
- `passage_sc_clem_strom2_3_en` (SC Clement Stromata II.3 English)

## Metadata Convention

English translation nodes always include:
```json
{
  "language": "eng",
  "source": "ai_translation",
  "source_model": "claude-opus-4-6",
  "source_language": "grc",
  "original_node_id": "passage_alex_fat_1",
  "work_title": "De Fato",
  "author": "Alexander of Aphrodisias",
  "edition": "Bruns 1892 (1st1K-grc1)",
  "auto_generated": true
}
```

## Current State

| Scope | Status | Count |
|-------|--------|-------|
| De Fato (Alexander) | Done | 39 Greek + 39 English |
| SC corpus (Greek) | Pending | ~1,822 nodes |
| SC corpus (Latin) | Pending | ~687 nodes |
| SC corpus (no-lang) | Pending | ~306 nodes |
| **Total** | | **2,854 source + 39 English** |

## Implementation Script

See `database/scripts/create_passage_translations.py` for the bulk translation pipeline.
