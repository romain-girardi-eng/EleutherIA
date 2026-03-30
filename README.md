<p align="center">
  <img src="frontend/public/logo.svg" alt="EleutherIA" width="400">
</p>

<h2 align="center">
  <a href="https://free-will.app">https://free-will.app</a>
</h2>

<p align="center">
  <strong>An AI-powered scholarly research platform for ancient philosophical debates on free will, fate, and moral responsibility</strong>
</p>

<p align="center">
  <a href="https://doi.org/10.5281/zenodo.17379489"><img src="https://zenodo.org/badge/DOI/10.5281/zenodo.17379489.svg" alt="DOI"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey.svg" alt="License: CC BY 4.0"></a>
</p>

---

## What Is EleutherIA?

EleutherIA (from Greek *ἐλευθερία*, "freedom" -- and *IA*, French for AI) is a full-stack scholarly research platform that combines a FAIR-compliant knowledge graph, an ancient texts corpus, and an agentic AI reasoning engine to make 1,200 years of philosophical debate on free will searchable, explorable, and queryable.

It spans from the Presocratics (6th c. BCE) to Boethius and the late Church Fathers (6th c. CE), covering Stoics, Epicureans, Peripatetics, Platonists, Pyrrhonists, and Early Christian thinkers, together with their modern reception in contemporary scholarship.

### The Problem

The ancient free will debate is scattered across hundreds of Greek and Latin texts, dozens of scholarly traditions, and centuries of interpretive frameworks. A researcher studying Chrysippus's compatibilism must navigate Stoic fragments, Cicero's Latin transmissions, Alexander of Aphrodisias's critiques, and modern reconstructions by Bobzien, Frede, and others. No single tool connects these layers.

### The Solution

EleutherIA unifies three systems into one platform:

**1. Ancient Texts Corpus** -- 487 works, 69,000+ passages in Greek, Latin, and English with lemmatization, CTS URN referencing, and hierarchical structure from Presocratic fragments to Boethius's *Consolation*.

**2. Knowledge Graph** -- 17,700+ nodes and 42,900+ edges mapping philosophers, concepts, arguments, schools, and works with 56 relation types across 12 categories. A dual-layer architecture separates ancient primary sources from modern scholarly reception.

**3. Agentic GraphRAG** -- A 12-node reasoning engine (pydantic-graph FSM) that decomposes complex scholarly questions, retrieves evidence across the knowledge graph and text corpus, synthesizes answers with verified citations, and self-evaluates quality, all grounded in actual ancient sources with zero fabrication.

### Why It Matters

- **For scholars:** Ask multi-hop questions ("How did Chrysippus's cylinder argument respond to Aristotle's critique of determinism, and how does Bobzien reconstruct this exchange?") and get sourced, citation-verified answers.
- **For students:** Explore the intellectual networks connecting ancient thinkers through an interactive graph with 3D visualization, timeline analysis, and community detection.
- **For digital humanities:** A working example of FAIR-compliant knowledge graph + RAG architecture applied to classical studies, with a full API, multilingual support (EN/FR/DE/IT/EL), and reproducible dataset.

## Quick Start

```bash
# Clone and configure
git clone https://github.com/romain-girardi-eng/EleutherIA.git
cd EleutherIA
cp .env.example .env
# Add your API key(s) to .env

# Start all services
make run
```

**Access:** http://localhost (frontend) | http://localhost:8000/docs (API)

## CLI

```bash
pip install eleutheria

# Services
eleutheria run              # Start all services (Docker)
eleutheria run -p full      # With monitoring (Prometheus + Grafana)
eleutheria stop             # Stop services
eleutheria status           # Check service health
eleutheria doctor           # Diagnose issues

# Search & Query
eleutheria search "Stoic fate"           # Search knowledge graph
eleutheria ask "What is free will?"      # Ask with GraphRAG
eleutheria ask -t "Complex question"     # Extended reasoning mode

# Explore Data
eleutheria stats            # Database statistics
eleutheria philosophers     # List philosophers
eleutheria concepts         # List concepts
eleutheria works -l grc     # List works by language

# Export
eleutheria export kg        # Export knowledge graph
eleutheria export passages  # Export passages

# Development
eleutheria test all         # Run all tests
eleutheria lint --fix       # Lint + auto-fix
eleutheria quality          # Full quality check

# Quick Access
eleutheria web              # Open free-will.app
eleutheria docs             # Open documentation
eleutheria shell            # Interactive mode
```

## Architecture

```
EleutherIA/
├── database/       Ancient texts corpus (487 works, 69k passages)
├── knowledge graph/  Knowledge graph (17.7k nodes, 42.9k edges)
├── graphrag/       Agentic RAG engine (12-node FSM, multi-LLM)
├── backend/        FastAPI gateway (auth, search, migrations)
├── frontend/       React 19 app (graph viz, search, i18n)
├── cli/            Command-line interface
├── deploy/         Docker Compose, Cloudflare Workers, production configs
├── scripts/        Maintenance & data quality tools
└── docs/           Architecture, API reference, examples, methodology
```

### The Three Packages

| Package | Purpose |
|---------|---------|
| [`database/`](database/) | Ancient Greek/Latin texts corpus with PostgreSQL, lemmatization, and hybrid search (full-text + lemmatic + semantic, merged via RRF) |
| [`knowledge graph/`](knowledge%20graph/) | FAIR-compliant knowledge graph with Qdrant vector embeddings, community detection, centrality analytics, and a formal ontology (22 node types, 56 edge types) |
| [`graphrag/`](graphrag/) | Agentic query engine: 12-node pydantic-graph FSM with query decomposition, multi-hop retrieval, CRAG validation, dual reranking, citation verification, and self-RAG refinement |

Each package can be installed and used independently.

### Key Capabilities

| Capability | Details |
|------------|---------|
| **Agentic reasoning** | 12-node finite state machine routes queries by complexity, decomposes multi-hop questions, and iteratively refines answers |
| **Multi-LLM orchestration** | Gemini (gemini-3.1-pro-preview, 1M token context) + Kimi K2.5 Thinking (extended reasoning) + OpenRouter fallback with automatic failover |
| **Hybrid search** | Full-text (PostgreSQL ts_rank) + lemmatic (Greek/Latin morphology) + semantic (Qdrant vectors), merged via Reciprocal Rank Fusion |
| **Citation verification** | Post-generation check that every citation maps to an actual passage in the database; zero tolerance for fabricated ancient text |
| **Interactive visualization** | Cosmograph GPU-accelerated graph (17k+ nodes), D3.js timelines, Three.js 3D embeddings, community detection overlays |
| **Dual-layer KG** | Primary layer (ancient sources) separated from secondary layer (modern scholarship), enabling source-vs-interpretation distinction |
| **Internationalization** | Full UI in English, French, German, Italian, and Modern Greek |
| **Streaming answers** | Server-Sent Events for real-time answer generation with source attribution |

## Tech Stack

| Layer | Technologies |
|-------|-------------|
| **Backend** | FastAPI, Python 3.11+, PostgreSQL 16, Qdrant, Alembic |
| **Frontend** | React 19, TypeScript, Vite, Tailwind CSS, Cosmograph, D3.js, Three.js, Framer Motion, react-i18next |
| **LLM** | Gemini (gemini-3.1-pro-preview, primary), Kimi K2.5 Thinking (extended reasoning), OpenRouter (fallback) |
| **Search** | PostgreSQL GIN indexes, Qdrant vector DB, Reciprocal Rank Fusion |
| **Deployment** | Docker Compose (local), Cloudflare Workers (production), Vercel (frontend) |
| **Quality** | Ruff, mypy, ESLint, Vitest, pytest (330+ tests), pre-commit hooks |

## Statistics

| Metric | Count |
|--------|-------|
| Knowledge graph nodes | 17,746 |
| Knowledge graph edges | 42,925 |
| Ancient works | 487 |
| Text passages | 69,277 |
| Node types | 22 |
| Relation types | 56 (12 categories) |
| Passage citations | 13,293 |
| Supported languages | 5 (EN, FR, DE, IT, EL) |

## Documentation

Full documentation is available in the [`docs/`](docs/INDEX.md) folder:

- [Quick Start](docs/guides/QUICK_START.md) -- Get running in 5 minutes
- [Architecture](docs/architecture/OVERVIEW.md) -- System design and components
- [API Reference](docs/reference/API.md) -- REST API documentation
- [Data Dictionary](docs/reference/DATA_DICTIONARY.md) -- Database schema reference
- [Academic Methodology](docs/academic/METHODOLOGY.md) -- FAIR principles, citation standards
- [Development Setup](docs/development/SETUP.md) -- Contributing guide

## Citation

```bibtex
@software{girardi2026eleutheria,
  author       = {Girardi, Romain},
  title        = {EleutherIA: An AI-Powered Scholarly Research Platform
                   for Ancient Philosophy on Free Will},
  year         = 2026,
  publisher    = {Zenodo},
  doi          = {10.5281/zenodo.17379489},
  url          = {https://doi.org/10.5281/zenodo.17379489}
}
```

## License

CC BY 4.0 -- See [LICENSE](LICENSE)

## Links

- [Production Site](https://free-will.app)
- [Full Documentation](docs/INDEX.md)
- [Zenodo Archive](https://doi.org/10.5281/zenodo.17379489)
- [Contributing](.github/CONTRIBUTING.md)
