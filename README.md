# EleutherIA

A FAIR-compliant knowledge graph for ancient philosophical debates on free will, fate, and moral responsibility (6th c. BCE - 6th c. CE).

## Quick Start

```bash
# Clone and start
git clone https://github.com/romain-girardi-eng/EleutherIA.git
cd EleutherIA
cp .env.example .env
# Add your API key(s) to .env

# Start all services
make run
# Or: docker compose -f deploy/docker/docker-compose.yml up
```

**Access:** http://localhost (frontend) | http://localhost:8000/docs (API)

## The Three Systems

| Package | Install | Purpose |
|---------|---------|---------|
| [database/](database/) | `pip install eleutheria-database` | Ancient Greek/Latin texts corpus (189 works, 17k passages) |
| [kg/](kg/) | `pip install eleutheria-kg` | Knowledge graph framework (2,193 nodes, 8,616 edges) |
| [graphrag/](graphrag/) | `pip install eleutheria-graphrag` | Graph-based RAG for scholarly Q&A |

Install only what you need. Each package works independently.

## Features

- **Dual-layer structure:** Primary layer (ancient sources) + secondary layer (modern scholarship)
- **Hybrid search:** Full-text + lemmatic + semantic search with RRF fusion
- **GraphRAG:** 5-stage RAG pipeline with citation grounding to ancient passages
- **Lemmatization:** Token-level analysis of Ancient Greek and Latin texts
- **Interactive visualization:** Cosmograph GPU-accelerated graph exploration

## Documentation

Full documentation is available in the [docs/](docs/INDEX.md) folder:

- [Quick Start](docs/guides/QUICK_START.md) - Get running in 5 minutes
- [Architecture](docs/architecture/OVERVIEW.md) - System design and components
- [API Reference](docs/reference/API.md) - REST API documentation
- [Data Dictionary](docs/reference/DATA_DICTIONARY.md) - Database schema reference
- [Development Setup](docs/development/SETUP.md) - Contributing guide

## Tech Stack

- **Backend:** FastAPI + Python 3.11+ + PostgreSQL + Qdrant
- **Frontend:** React 19 + TypeScript + Vite + Tailwind CSS + Cosmograph
- **LLM:** Gemini 3 (primary) + Kimi K2.5 Thinking (extended reasoning)
- **Deployment:** Docker Compose

## Statistics

| Metric | Count |
|--------|-------|
| Knowledge graph nodes | 2,193 |
| Knowledge graph edges | 8,616 |
| Ancient works | 189 |
| Passages | 16,968 |
| Node types | 15 |
| Relation types | 32 |

## Citation

```bibtex
@software{girardi2025eleutheria,
  author       = {Girardi, Romain},
  title        = {EleutherIA: A FAIR-Compliant Knowledge Graph for Ancient Philosophy on Free Will},
  year         = 2025,
  publisher    = {Zenodo},
  doi          = {10.5281/zenodo.17379490},
  url          = {https://doi.org/10.5281/zenodo.17379490}
}
```

## License

CC BY 4.0 - See [LICENSE](LICENSE)

## Links

- [Full Documentation](docs/INDEX.md)
- [Dataset (Zenodo)](https://doi.org/10.5281/zenodo.17379490)
- [Contributing](CONTRIBUTING.md)
