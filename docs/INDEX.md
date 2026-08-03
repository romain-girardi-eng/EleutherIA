# EleutherIA Documentation

## Quick Links

| Guide | Description |
|-------|-------------|
| [Quick Start](guides/QUICK_START.md) | Get running in 5 minutes |
| [Architecture](architecture/OVERVIEW.md) | System design and components |
| [API Reference](reference/API.md) | REST API documentation |
| [Data Dictionary](reference/DATA_DICTIONARY.md) | Database schema reference |

## For Developers

- [Development Setup](development/SETUP.md) - Environment setup, testing, code quality
- [Browser Automation](development/agents.md) - Using browser-use for automation tasks
- [API Examples](examples/) - cURL and Python usage examples
- [Contributing](../.github/CONTRIBUTING.md) - How to contribute

## For Researchers

- [Methodology](academic/METHODOLOGY.md) - Scholarly methodology, FAIR principles, citation standards
- [Academic Integrity](ACADEMIC_INTEGRITY.md) - Authenticity policy and enforcement gates

## Architecture Deep Dives

- [PageIndex V3](architecture/PAGEINDEX_V3.md) - GraphRAG pipeline specification
- [GraphRAG Convergence](architecture/graphrag-convergence.md) - Pipeline convergence analysis
- [D3 Graph Engine](architecture/d3-graph/) - Graph visualization design decisions

## The Three Packages

Each package can be installed independently:

```bash
pip install eleutheria-database   # Ancient texts corpus
pip install eleutheria-kg         # Knowledge graph framework
pip install eleutheria-graphrag   # Agentic RAG engine
```

See the [Architecture Overview](architecture/OVERVIEW.md) for how they work together.

## Documentation Structure

```
docs/
├── INDEX.md                   # This file
├── CHANGELOG.md               # Version history
├── codemeta.json              # CodeMeta scholarly metadata
├── guides/
│   └── QUICK_START.md         # Getting started
├── architecture/
│   ├── OVERVIEW.md            # System design
│   ├── PAGEINDEX_V3.md        # GraphRAG pipeline spec
│   ├── graphrag-convergence.md
│   └── d3-graph/              # Graph visualization decisions
├── reference/
│   ├── API.md                 # REST API docs
│   └── DATA_DICTIONARY.md     # Database schema
├── development/
│   ├── SETUP.md               # Dev environment
│   └── agents.md              # Browser automation
├── academic/
│   └── METHODOLOGY.md         # Research methodology
├── examples/
│   ├── curl/                  # cURL examples
│   └── python/                # Python examples
├── plans/                     # Design documents (internal)
├── reports/                   # Audit reports (internal)
└── assets/                    # Images, posters
```
