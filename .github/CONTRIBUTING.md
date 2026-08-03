# Contributing to EleutherIA

Thank you for your interest in contributing to EleutherIA! This document provides guidelines for contributions.

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment.

## How to Contribute

### Reporting Issues

1. Check existing issues to avoid duplicates
2. Use the issue template
3. Include steps to reproduce for bugs
4. For ancient text errors, include the passage ID and CTS URN

### Pull Requests

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make your changes
4. Run quality checks: `make quality`
5. Run tests: `make test`
6. Commit with conventional commits: `feat:`, `fix:`, `docs:`, etc.
7. Push and open a PR

### Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/EleutherIA.git
cd EleutherIA

# Install all packages in editable mode
make install

# Start development environment
make dev
```

### Code Style

- **Python:** Follow PEP 8, enforced by Ruff
- **TypeScript:** Follow ESLint configuration
- **Commits:** Use [Conventional Commits](https://www.conventionalcommits.org/)

Run before committing:
```bash
make fix      # Auto-fix and format
make quality  # Lint + type check
make test     # Run tests
```

### Academic Integrity

**Critical:** This is a scholarly database. Never fabricate ancient Greek or Latin text.

- All ancient text must come from verified sources in the database
- Include CTS URNs or passage IDs for citations
- When uncertain, paraphrase in English instead
- See [docs/ACADEMIC_INTEGRITY.md](../docs/ACADEMIC_INTEGRITY.md) for the full Ancient Text Authenticity Policy

## Package Structure

The project has three independent packages:

| Package | Purpose | Maintainer Focus |
|---------|---------|------------------|
| `database/` | Ancient texts corpus | Data accuracy, schema |
| `knowledge graph/` | Knowledge graph | Ontology, relationships |
| `graphrag/` | RAG pipeline | Search quality, citations |

Contributions should target the appropriate package.

## Testing

Each package has its own test suite:

```bash
make test-database    # Database tests
make test-kg          # Knowledge graph tests
make test-graphrag    # GraphRAG tests
```

New features should include tests. Aim for >80% coverage.

## Documentation

- Update relevant docs when changing functionality
- Keep documentation in `docs/` organized in the 7-folder structure
- Use clear, concise language

## Questions?

Open a discussion or issue on GitHub.

## License

Contributions are licensed under CC BY 4.0, same as the project.
