# Development Setup

Guide for setting up the EleutherIA development environment.

## Prerequisites

- Python 3.11+
- Node.js 20+
- Docker and Docker Compose
- Git

## Clone Repository

```bash
git clone https://github.com/romain-girardi-eng/EleutherIA.git
cd EleutherIA
```

## Environment Setup

```bash
cp .env.example .env
# Edit .env with your API keys
```

Required keys (at least one):
- `MOONSHOT_API_KEY` - Kimi K2 (recommended)
- `OPENROUTER_API_KEY` - OpenRouter
- `GEMINI_API_KEY` - Google Gemini

## Install Packages

### All Packages (Editable Mode)

```bash
make install
```

Or individually:

```bash
# Database package
cd database && pip install -e ".[dev]"

# KG package
cd kg && pip install -e ".[dev]"

# GraphRAG package
cd graphrag && pip install -e ".[dev,llm]"

# Frontend
cd frontend && npm install
```

## Start Development Services

### Option 1: Docker (Recommended)

```bash
make dev
# Or: docker compose -f deploy/docker/docker-compose.dev.yml up -d
```

### Option 2: Manual

Start PostgreSQL and Qdrant:
```bash
docker run -d -p 5432:5432 \
  -e POSTGRES_USER=eleutheria \
  -e POSTGRES_PASSWORD=eleutheria \
  -e POSTGRES_DB=eleutheria \
  postgres:16-alpine

docker run -d -p 6333:6333 qdrant/qdrant
```

Start backend:
```bash
cd graphrag
uvicorn eleutheria_graphrag.api:router --reload --port 8000
```

Start frontend:
```bash
cd frontend
npm run dev
```

## Code Quality

### Linting

```bash
make lint
# Or: ruff check database/src kg/src graphrag/src
```

### Auto-fix

```bash
make fix
# Or: ruff check --fix ... && ruff format ...
```

### Type Checking

```bash
make typecheck
# Or: mypy database/src kg/src graphrag/src
```

### All Quality Checks

```bash
make quality
```

## Testing

### All Tests

```bash
make test
```

### Individual Packages

```bash
make test-database
make test-kg
make test-graphrag
```

### With Coverage

```bash
make test-coverage
```

## Pre-commit Hooks

```bash
pip install pre-commit
pre-commit install
```

Hooks run automatically on commit:
- Trailing whitespace removal
- Ruff linting and formatting
- Secret detection
- Large file detection

## Project Structure

```
EleutherIA/
├── database/           # Ancient texts package
│   ├── src/
│   ├── schema/
│   └── tests/
├── kg/                 # Knowledge graph package
│   ├── src/
│   ├── ontology/
│   └── tests/
├── graphrag/           # GraphRAG package
│   ├── src/
│   └── tests/
├── frontend/           # React UI
├── deploy/             # Docker configuration
└── docs/               # Documentation
```

## IDE Setup

### VS Code

Recommended extensions:
- Python (Microsoft)
- Pylance
- Ruff
- ESLint
- Prettier
- GitLens

Settings (`.vscode/settings.json`):
```json
{
  "python.defaultInterpreterPath": "./venv/bin/python",
  "python.analysis.typeCheckingMode": "basic",
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.formatOnSave": true
  }
}
```

### PyCharm

1. Set Python interpreter to venv
2. Enable Ruff integration
3. Configure test runner for pytest

## Troubleshooting

### Port Conflicts

```bash
# Check what's using ports
lsof -i :5432  # PostgreSQL
lsof -i :6333  # Qdrant
lsof -i :8000  # Backend
lsof -i :5173  # Frontend
```

### Database Connection

```bash
# Test PostgreSQL
psql -h localhost -U eleutheria -d eleutheria

# Reset database
docker compose -f deploy/docker/docker-compose.dev.yml down -v
docker compose -f deploy/docker/docker-compose.dev.yml up -d
```

### Import Errors

```bash
# Reinstall packages in editable mode
pip install -e database/
pip install -e kg/
pip install -e graphrag/
```
