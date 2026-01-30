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

- **5-stage RAG pipeline:**
  1. Semantic search (Qdrant vectors)
  2. Graph traversal (BFS expansion)
  3. Context building (node descriptions + passages)
  4. LLM synthesis (Kimi K2 / Gemini)
  5. Citation extraction (grounded in ancient sources)

- **Streaming responses** via Server-Sent Events
- **Citation grounding** to specific ancient passages
- **Multi-provider LLM support** (Kimi K2, OpenRouter, Gemini)

## Pipeline Overview

```
User Query
    │
    ▼
┌─────────────────┐
│ 1. Semantic     │  Query → embedding → Qdrant top-k
│    Search       │  Returns relevant KG nodes
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 2. Graph        │  BFS from seed nodes
│    Traversal    │  Configurable depth (1-3)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 3. Context      │  Aggregate descriptions
│    Building     │  Include ancient passages
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 4. LLM          │  Academic prompt template
│    Synthesis    │  Streaming generation
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 5. Citation     │  Parse [1], [2] refs
│    Extraction   │  Map to KG nodes/passages
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
