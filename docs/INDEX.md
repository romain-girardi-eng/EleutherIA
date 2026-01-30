# EleutherIA Documentation

Welcome to the EleutherIA documentation.

## Quick Links

| Guide | Description |
|-------|-------------|
| [Quick Start](guides/QUICK_START.md) | Get running in 5 minutes |
| [Architecture](architecture/OVERVIEW.md) | System design and components |
| [API Reference](reference/API.md) | REST API documentation |
| [Data Dictionary](reference/DATA_DICTIONARY.md) | Database schema reference |

## For Developers

- [Development Setup](development/SETUP.md) - Environment setup, testing, code quality
- [Contributing](../CONTRIBUTING.md) - How to contribute

## For Researchers

- [Methodology](academic/METHODOLOGY.md) - Scholarly methodology, FAIR principles, citation standards

## The Three Packages

Each package can be installed independently:

```bash
pip install eleutheria-database   # Ancient texts corpus
pip install eleutheria-kg         # Knowledge graph framework
pip install eleutheria-graphrag   # Graph-based RAG
```

See the [Architecture Overview](architecture/OVERVIEW.md) for how they work together.

## Documentation Structure

```
docs/
├── INDEX.md              # This file
├── guides/
│   └── QUICK_START.md    # Getting started
├── architecture/
│   └── OVERVIEW.md       # System design
├── reference/
│   ├── API.md            # REST API docs
│   └── DATA_DICTIONARY.md # Database schema
├── development/
│   └── SETUP.md          # Dev environment
└── academic/
    └── METHODOLOGY.md    # Research methodology
```
