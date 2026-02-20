# Quick Start Guide

Get EleutherIA running in 5 minutes.

## Prerequisites

- Docker and Docker Compose
- One LLM API key (Kimi, OpenRouter, or Gemini)

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/romain-girardi-eng/EleutherIA.git
cd EleutherIA
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` and add at least one API key:
```bash
# Primary: Gemini 3 (fast, high quality)
GEMINI_API_KEY=your-key-here

# Thinking mode: Kimi K2.5 Thinking (extended reasoning, 256k context)
MOONSHOT_API_KEY=your-key-here

# Alternative: OpenRouter (multi-model access)
OPENROUTER_API_KEY=your-key-here
```

### 3. Start Services

```bash
make run
# Or: docker compose -f deploy/docker/docker-compose.yml up -d
```

### 4. Access the Application

| Service | URL |
|---------|-----|
| Frontend | http://localhost |
| API Docs | http://localhost:8000/docs |
| Qdrant Dashboard | http://localhost:6333/dashboard |

## Using the Application

### Search Ancient Texts

1. Go to http://localhost
2. Click "Search" in the navigation
3. Enter a Greek term (e.g., "ἐφ' ἡμῖν") or English query
4. Results show passages with highlighted matches

### Ask Questions (GraphRAG — PageIndex V3)

1. Go to http://localhost/graphrag
2. Enter a question like "What did the Stoics believe about fate?"
3. The system will:
   - Search the knowledge graph and passage database in parallel
   - Retrieve linked ancient text passages (via passage_citations)
   - Build full context with no truncation
   - Generate a scholarly answer with ONE synthesis call
   - Cite ancient sources with CTS URNs

### Explore the Knowledge Graph

1. Go to http://localhost/visualizer
2. Use filters to focus on:
   - Specific philosophers (Chrysippus, Epictetus)
   - Schools (Stoic, Epicurean)
   - Concepts (fate, free will)
3. Click nodes to see details and relationships

## Using as Python Packages

```bash
# Install individual packages
pip install eleutheria-database
pip install eleutheria-kg
pip install eleutheria-graphrag[llm]
```

```python
from eleutheria_database import DatabaseService
from eleutheria_kg import QdrantService, KGAnalytics
from eleutheria_graphrag import GraphRAGService

# Connect
db = DatabaseService()
await db.connect()

# Query ancient works
works = await db.fetch("""
    SELECT title, author FROM free_will.ancient_works
    WHERE school = 'Stoic' LIMIT 10
""")
```

## Stopping Services

```bash
make stop
# Or: docker compose -f deploy/docker/docker-compose.yml down
```

## Next Steps

- [Architecture Overview](../architecture/OVERVIEW.md)
- [API Reference](../reference/API.md)
- [GraphRAG Guide](GRAPHRAG.md)
