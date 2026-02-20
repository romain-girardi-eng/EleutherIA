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
from eleutheria_kg import QdrantService

# Connect services
db = DatabaseService()
qdrant = QdrantService()
await db.connect()
await qdrant.connect()

# Initialize GraphRAG
graphrag = GraphRAGService(db, qdrant)
await graphrag.load_kg()

# Ask a question
result = await graphrag.query(
    "What did the Stoics believe about fate and free will?"
)

print(result["answer"])
print(f"Sources: {result['citations']}")
```

## Features

- **PageIndex V3 pipeline** (2 LLM calls, direct retrieval):
  1. Embed query → parallel Qdrant search (KG nodes + passages + edges)
  2. Enrich → passage_citations lookup + KG neighbor expansion
  3. Build FULL context (no truncation — Gemini 1M token context)
  4. ONE synthesis call → scholarly answer with citations

- **Streaming responses** via Server-Sent Events
- **Citation grounding** to specific ancient passages with CTS URNs
- **Multi-provider LLM support** (Kimi K2, Gemini)
- **passage_citations** as primary retrieval signal (curated KG-to-passage links)

## Pipeline Overview (PageIndex V3)

```
User Query
    │
    ▼
┌─────────────────┐
│ 1. Embed +      │  Query → Gemini embedding
│    Detect Refs  │  + CTS URN reference detection
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 2. Parallel     │  KG nodes + passages + edges
│    Search       │  via Qdrant (no LLM calls)
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
MOONSHOT_API_KEY=your-key    # For Kimi K2
OPENROUTER_API_KEY=your-key  # For OpenRouter
GEMINI_API_KEY=your-key      # For Gemini

# Vector DB
QDRANT_HOST=localhost
QDRANT_HTTP_PORT=6333
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
