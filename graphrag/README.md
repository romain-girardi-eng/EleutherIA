# eleutheria-graphrag

Graph-based Retrieval-Augmented Generation for scholarly Q&A on ancient philosophy.

## Installation

```bash
pip install eleutheria-graphrag
```

With LLM providers:
```bash
pip install eleutheria-graphrag[llm]
```

For FastAPI integration:
```bash
pip install eleutheria-graphrag[api]
```

## Quick Start

```python
from eleutheria_graphrag import GraphRAGService
from eleutheria_database import DatabaseService

# Connect services
db = DatabaseService()
await db.connect()

# Initialize GraphRAG
graphrag = GraphRAGService(db)
await graphrag.load_kg()

# Ask a question
result = await graphrag.query(
    "What did the Stoics believe about fate and free will?"
)

print(result["answer"])
print(f"Sources: {result['citations']}")
```

## Features

- **Agentic vectorless pipeline**:
  1. Expand query terms and lemmas; detect CTS URNs and author/work mentions
  2. Discover seeds via SQLStrategy: tree routing, KG label/description match, `passage_citations`, lemmatic lookup, and full-text/lemmatic RRF
  3. Enrich with KG neighbor expansion, proof chains, and passage evidence
  4. Build full context for long-context synthesis
  5. Generate a scholarly answer with verified citations

- **Streaming responses** via Server-Sent Events
- **Citation grounding** to specific ancient passages with CTS URNs
- **Multi-provider LLM support** (Kimi K2, Gemini)
- **passage_citations** as primary retrieval signal (curated KG-to-passage links)

## Fail-closed publication contract

Generated prose is an internal draft until one deterministic publication verdict
passes. The public service boundary and both answer caches use the same verdict:

- the post-referee dialectical content gate must pass;
- every emitted citation must be audited (partial samples cannot publish);
- every verdict must be `VERIFIED`; any `WEAK`, `REJECTED`, `MISSING`, parser
  error, verifier exception, or aggregate `aborted=true` blocks publication;
- modern position citations must resolve `publication_id + page_ref` to one
  reviewed, hashed `secondary_evidence_pages` manifestation. KG claims and
  scholar biographies are never verifier evidence; missing or ambiguous page
  mappings are `MISSING`;
- a blocked run keeps diagnostic metadata but exposes an empty answer, citation
  list, and claim ledger, and is never cached;
- SSE keeps status/reasoning heartbeats live but buffers answer prose until the
  verdict passes. There is no unaudited citation preview.

`ELEUTHERIA_VERIFIER_V2_MAX_CLAIMS` is an audit ceiling (default `64`). Setting
it below an answer's citation count is allowed operationally, but the resulting
partial audit fails closed rather than publishing a sampled score as if it were
complete verification.

## Pipeline Overview

```
User Query
    │
    ▼
┌─────────────────┐
│ 1. Expand +     │  Query terms + lemmas
│    Detect Refs  │  + CTS URN reference detection
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 2. Discover     │  SQLStrategy:
│    Seeds        │  tree + KG labels + citations
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 3. Enrich       │  passage_citations → full text
│                 │  + KG neighbor expansion
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 4. Build FULL   │  No truncation
│    Context      │  Gemini handles ~1M tokens
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 5. ONE          │  Kimi K2 / Gemini
│    Synthesis    │  → Answer + citations
└────────┴────────┘
         │
         ▼
    Answer + Citations
```

## Configuration

Environment variables:
```bash
# LLM Providers (at least one required)
LLM_PREFERRED_PROVIDER=kimi  # kimi, openrouter, or gemini
CODEX_PROXY_API_KEY=your-key   # Codex proxy (primary)
CLAUDE_PROXY_API_KEY=your-key  # Claude proxy (fallback)
GEMINI_API_KEY=your-key      # For Gemini

# Retrieval
RETRIEVAL_MODE=auto  # auto uses SQL when DB is connected, snapshot otherwise
```

## API Routes (Optional)

If installed with `[api]`:

```python
from fastapi import FastAPI
from eleutheria_graphrag.api import router as graphrag_router

app = FastAPI()
app.include_router(graphrag_router, prefix="/api/graphrag")
```

Endpoints:
- `POST /query` - Submit a question
- `GET /query/stream` - Streaming response via SSE
- `GET /health` - Service health check

## License

CC BY 4.0
