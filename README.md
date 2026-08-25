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

EleutherIA (from Greek *ἐλευθερία*, "freedom" -- and *IA*, French for AI) is a full-stack scholarly research platform that combines a FAIR-oriented knowledge graph, an ancient texts corpus, and an agentic AI reasoning engine to make ancient debates on freedom, fate and responsibility searchable, explorable, and queryable.

Its research scope spans from archaic and Presocratic antecedents to Boethius and late antique Christianity, covering Stoic, Epicurean, Peripatetic, Platonist, sceptical and Christian dossiers together with modern reception. Coverage is uneven by source: the project publishes its gaps and factual-risk queue instead of treating scope as proof of completeness.

### The Problem

The ancient free will debate is scattered across hundreds of Greek and Latin texts, dozens of scholarly traditions, and centuries of interpretive frameworks. A researcher studying Chrysippus's compatibilism must navigate Stoic fragments, Cicero's Latin transmissions, Alexander of Aphrodisias's critiques, and modern reconstructions by Bobzien, Frede, and others. No single tool connects these layers.

### The Solution

EleutherIA unifies three systems into one platform:

**1. Ancient Texts Corpus** -- 21,000+ passage records in Greek, Latin and translation layers, with lemmatization, CTS-oriented referencing and hierarchical structure. Edition, witness, language and translation provenance are being normalized under strict no-growth integrity gates.

**2. Knowledge Graph** -- 20,000+ nodes and 49,000+ tracked edges mapping people, concepts, arguments, passages, schools, works and publications with 76 edge types. A dual-layer architecture distinguishes ancient evidence from modern scholarly reception.

**3. Agentic GraphRAG** -- An agentic reasoning engine that decomposes research questions, retrieves across the graph and corpus, synthesizes attributed positions and audits citations. Its publication boundary is fail-closed: a partial audit, weak/rejected/missing citation, parser error, abort or verifier failure withholds the answer and prevents caching. This reduces known failure modes; it is not a claim of infallibility.

The graph workspace has three synchronized projections: **Atlas** for spatial
exploration, **Chronos** for transmission through time, and **Scholar** for an
accessible light research table and comparison dossier. They share release,
selection, filters, comparison set, Evidence Thread, URL and undo/redo state;
the WebGL renderer is loaded only by Atlas.

### Why It Matters

- **For scholars:** Ask multi-hop questions ("How did Chrysippus's cylinder argument respond to Aristotle's critique of determinism, and how does Bobzien reconstruct this exchange?") and inspect the source and verification trail of answers that pass publication gates.
- **For students:** Explore the intellectual networks connecting ancient thinkers through an interactive graph with 3D visualization, timeline analysis, and community detection.
- **For digital humanities:** A working, openly audited knowledge-graph + RAG architecture for classical studies, with an API, localized interface, reproducible artifacts and explicit unresolved-debt registers.

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
├── database/       Ancient texts corpus (21k+ passage records)
├── knowledge graph/  Knowledge graph (20k+ nodes, 49k+ tracked edges)
├── graphrag/       Agentic RAG engine (12-node FSM, multi-LLM)
├── backend/        FastAPI gateway (auth, search, migrations)
├── frontend/       React 19 app (graph viz, search, i18n)
├── cli/            Command-line interface
├── deploy/         Docker Compose and production configs
├── scripts/        Maintenance & data quality tools
└── docs/           Architecture, API reference, examples, methodology
```

### The Three Packages

| Package | Purpose |
|---------|---------|
| [`database/`](database/) | Ancient Greek/Latin texts corpus with PostgreSQL, lemmatization, and hybrid text search (full-text + lemmatic, merged via RRF) |
| [`knowledge graph/`](knowledge%20graph/) | FAIR-oriented, openly audited knowledge graph with community detection, centrality analytics, a formal ontology (24 declared node types, 76 declared edge types), and a neurosymbolic layer (RDF/OWL/SHACL exports aligned on CIDOC-CRM, FOAF, SKOS, Dublin Core, PROV-O, BIBO, Wikidata) |
| [`graphrag/`](graphrag/) | Agentic query engine: 12-node pydantic-graph FSM with vectorless SQL/tree/lemma discovery, multi-hop retrieval, CRAG validation, reranking, citation verification, and self-RAG refinement |

Each package can be installed and used independently.

### Key Capabilities

| Capability | Details |
|------------|---------|
| **Agentic reasoning** | 12-node finite state machine routes queries by complexity, decomposes multi-hop questions, and iteratively refines answers |
| **Multi-LLM orchestration** | Gemini (gemini-3.1-pro-preview, 1M token context) + Kimi K2.5 Thinking (extended reasoning) + OpenRouter fallback with automatic failover |
| **Hybrid search** | Full-text (PostgreSQL ts_rank) + lemmatic (Greek/Latin morphology), merged via Reciprocal Rank Fusion |
| **Citation verification** | Post-referee, fail-closed verification against fresh corpus passages or reviewed secondary pages; missing, weak, rejected, ambiguous or unauthoritative evidence withholds publication |
| **Neurosymbolic reasoning** | OWL2-RL forward-chaining (inverse + transitive closure on `part_of`/`contains`/`belongs_to_corpus`) materialises ~40k inferred facts in &lt;1 s; SHACL validation gate catches data invariants on every snapshot; claim ledger carries proof chains showing how each inferred fact was derived |
| **FAIR / Linked Data export** | Turtle, JSON-LD and N-Triples export with provenance reification and VoID/DCAT metadata; complete production dereferencing under `/kg/{id}` remains an explicit release blocker |
| **Interactive visualization** | Synchronized Atlas/Chronos/Scholar modes: GPU graph only in Atlas, timeline projection in Chronos, accessible table/comparison workspace in Scholar |
| **Dual-layer KG** | Primary layer (ancient sources) separated from secondary layer (modern scholarship), enabling source-vs-interpretation distinction |
| **Internationalization** | UI translation catalogs for English, French, German, Italian and Modern Greek; only English is currently independently prerendered/indexable |
| **Streaming answers** | Server-Sent Events for real-time answer generation with source attribution |

## Tech Stack

| Layer | Technologies |
|-------|-------------|
| **Backend** | FastAPI, Python 3.11+, PostgreSQL 16, Alembic |
| **Frontend** | React 19, TypeScript, Vite, Tailwind CSS, Cosmograph, D3.js, Three.js, Framer Motion, react-i18next |
| **LLM** | Gemini (gemini-3.1-pro-preview, primary), Kimi K2.5 Thinking (extended reasoning), OpenRouter (fallback) |
| **Search** | PostgreSQL GIN indexes, lemmatic indexes, tree routing, passage_citations, Reciprocal Rank Fusion |
| **Deployment** | Docker Compose (local), Docker Compose + Cloudflare tunnel (production API, worker, public SPARQL), hosted SPA at `free-will.app` |
| **Quality** | Ruff, mypy, ESLint, Vitest, pytest, snapshot/corpus gates and a persistent source/evidence/issue verification registry |

## Statistics

Current Wave 0 working-snapshot counts (2026-08-24). They are not a release
certification; the machine-readable SOTA registry intentionally remains red.

| Metric | Count |
|--------|-------|
| Knowledge graph nodes | 20,265 |
| Knowledge graph edges | 49,826 |
| Work nodes | 251 |
| Text passages | 21,138 |
| Node types used / declared | 16 / 24 |
| Edge relations used / declared | 53 / 76 |
| RDF triples (older v5.1.0 export; regeneration required) | 560,110 |
| Passage citations | 19,812 |
| UI locale catalogs / independently indexed locales | 5 / 1 (EN) |

## Documentation

Full documentation is available in the [`docs/`](docs/INDEX.md) folder:

- [Quick Start](docs/guides/QUICK_START.md) -- Get running in 5 minutes
- [Architecture](docs/architecture/OVERVIEW.md) -- System design and components
- [API Reference](docs/reference/API.md) -- REST API documentation
- [Data Dictionary](docs/reference/DATA_DICTIONARY.md) -- Database schema reference
- [Academic Methodology](docs/academic/METHODOLOGY.md) -- FAIR principles, citation standards
- [Academic Integrity](docs/ACADEMIC_INTEGRITY.md) -- Authenticity policy and enforcement gates
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
