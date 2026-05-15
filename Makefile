# EleutherIA Makefile
# Simple commands for development, testing, and deployment

.PHONY: help install install-database install-kg install-graphrag \
        run local stop local-clean prod prod-stop \
        cf-deploy cf-dev cf-logs \
        test test-database test-kg test-graphrag test-coverage \
        lint format typecheck quality fix \
        kg-rdf kg-shacl kg-bibtex scholarly-backlog sparql sparql-stop \
        frontend-install frontend-dev frontend-build frontend-test \
        logs docs docs-serve clean

# Default target
help:
	@echo "EleutherIA Development Commands"
	@echo ""
	@echo "Quick Start:"
	@echo "  make install          Install all 3 packages in editable mode"
	@echo "  make run              Start local stack (Docker, self-contained)"
	@echo "  make stop             Stop local stack"
	@echo ""
	@echo "Individual Packages:"
	@echo "  make install-database Install database package only"
	@echo "  make install-kg       Install kg package only"
	@echo "  make install-graphrag Install graphrag package only"
	@echo ""
	@echo "Testing:"
	@echo "  make test             Run all tests"
	@echo "  make test-database    Test database package"
	@echo "  make test-kg          Test kg package"
	@echo "  make test-graphrag    Test graphrag package"
	@echo "  make test-coverage    Tests with coverage report"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint             Run ruff linter"
	@echo "  make format           Format code with ruff"
	@echo "  make typecheck        Run mypy type checker"
	@echo "  make quality          Run lint + typecheck"
	@echo "  make fix              Auto-fix + format"
	@echo "  make kg-shacl         Validate KG invariant SHACL and write quality report"
	@echo "  make kg-rdf           Export KG RDF into data/rdf/eleutheria.{ttl,jsonld,nt}"
	@echo "  make kg-bibtex        Export publication nodes to data/kg/publications.bib"
	@echo "  make scholarly-backlog Export evidence/edition/date backlog reports"
	@echo "  make sparql           Start local Fuseki sidecar from data/rdf/eleutheria.ttl"
	@echo ""
	@echo "Frontend:"
	@echo "  make frontend-install Install frontend dependencies"
	@echo "  make frontend-dev     Start frontend dev server"
	@echo "  make frontend-build   Build frontend for production"
	@echo "  make frontend-test    Run frontend tests"
	@echo ""
	@echo "Docker (Local):"
	@echo "  make run              Start all services (PG + Qdrant + backend + frontend)"
	@echo "  make stop             Stop all services"
	@echo "  make local-clean      Stop and remove volumes (data loss!)"
	@echo "  make logs             Tail service logs"
	@echo ""
	@echo "Docker (Production — Supabase + Qdrant Cloud):"
	@echo "  make prod             Start backend + frontend"
	@echo "  make prod-stop        Stop production services"
	@echo ""
	@echo "Cloudflare Workers (Production — free-will.app):"
	@echo "  make cf-deploy        Deploy to Cloudflare Workers"
	@echo "  make cf-dev           Start local CF dev server"
	@echo "  make cf-logs          Tail production logs"
	@echo ""
	@echo "Database:"
	@echo "  make db-backup        Backup PostgreSQL"
	@echo "  make db-restore       Restore from backup"
	@echo ""
	@echo "Utilities:"
	@echo "  make clean            Remove cache files"

# =============================================================================
# Installation
# =============================================================================

install: install-database install-kg install-graphrag frontend-install
	@echo "All packages installed successfully!"

install-database:
	cd database && pip install -e ".[dev]"

install-kg:
	cd "knowledge graph" && pip install -e ".[dev,semantic]"

install-graphrag:
	cd graphrag && pip install -e ".[dev]"

# =============================================================================
# Docker — Local (self-contained)
# =============================================================================

run local:
	docker compose -f deploy/docker-compose.yml up -d --build
	@echo ""
	@echo "EleutherIA is running!"
	@echo "  Frontend: http://localhost"
	@echo "  API Docs: http://localhost:8000/docs"
	@echo "  Qdrant:   http://localhost:6333/dashboard"

stop:
	docker compose -f deploy/docker-compose.yml down

local-clean:
	docker compose -f deploy/docker-compose.yml down -v --remove-orphans

logs:
	docker compose -f deploy/docker-compose.yml logs -f

sparql: kg-rdf
	docker compose -f deploy/docker-compose.yml --profile sparql up -d fuseki
	@echo "SPARQL endpoint: http://localhost:$${FUSEKI_PORT:-3030}/eleutheria/sparql"

sparql-stop:
	docker compose -f deploy/docker-compose.yml --profile sparql stop fuseki

# =============================================================================
# Docker — Production (Supabase + Qdrant Cloud)
# =============================================================================

prod:
	docker compose -f deploy/production/docker-compose.yml up -d --build
	@echo ""
	@echo "Production services started."
	@echo "  Backend:  http://localhost:8000/api/health"
	@echo "  Frontend: http://localhost"

prod-stop:
	docker compose -f deploy/production/docker-compose.yml down

# =============================================================================
# Cloudflare Workers (Production — free-will.app)
# =============================================================================

cf-deploy:
	cd deploy/cloudflare && npx wrangler deploy

cf-dev:
	cd deploy/cloudflare && npx wrangler dev

cf-logs:
	cd deploy/cloudflare && npx wrangler tail

# =============================================================================
# Testing
# =============================================================================

test: test-database test-kg test-graphrag frontend-test
	@echo "All tests passed!"

test-database:
	cd database && python -m pytest tests/ -v

test-kg:
	cd "knowledge graph" && python -m pytest tests/ -v

test-graphrag:
	cd graphrag && python -m pytest tests/ -v

test-coverage:
	cd database && python -m pytest tests/ --cov=src --cov-report=html
	cd "knowledge graph" && python -m pytest tests/ --cov=src --cov-report=html
	cd graphrag && python -m pytest tests/ --cov=src --cov-report=html
	@echo "Coverage reports generated in */htmlcov/"

# =============================================================================
# Code Quality
# =============================================================================

lint:
	ruff check database/src "knowledge graph/src" graphrag/src

format:
	ruff format database/src "knowledge graph/src" graphrag/src

typecheck:
	mypy database/src "knowledge graph/src" graphrag/src

quality: lint typecheck
	@echo "Code quality checks passed!"

kg-rdf:
	python -m cli.main export kg --format rdf --output data/rdf/eleutheria

kg-shacl:
	python "knowledge graph/src/eleutheria_kg/semantic/shapes/generate_shapes.py"
	python scripts/validate_kg_shacl.py

kg-bibtex:
	python scripts/export_publications_bibtex.py

scholarly-backlog:
	python scripts/audit_scholarly_backlog.py

fix:
	ruff check --fix database/src "knowledge graph/src" graphrag/src
	ruff format database/src "knowledge graph/src" graphrag/src
	@echo "Auto-fix and formatting complete!"

# =============================================================================
# Frontend
# =============================================================================

frontend-install:
	cd frontend && npm install

frontend-dev:
	cd frontend && npm run dev

frontend-build:
	cd frontend && npm run build

frontend-test:
	cd frontend && npm test

# =============================================================================
# Database
# =============================================================================

db-backup:
	@echo "Backing up database..."
	pg_dump $${DATABASE_URL} > backups/backup_$$(date +%Y%m%d_%H%M%S).sql
	@echo "Backup complete!"

db-restore:
	@echo "Usage: make db-restore FILE=backups/backup_YYYYMMDD_HHMMSS.sql"
	@test -n "$(FILE)" || (echo "FILE is required"; exit 1)
	psql $${DATABASE_URL} < $(FILE)

# =============================================================================
# Documentation
# =============================================================================

docs:
	@echo "Documentation is in docs/ — no build step required (Markdown)"

docs-serve:
	cd docs && python -m http.server 8080

# =============================================================================
# Utilities
# =============================================================================

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
	@echo "Cache files cleaned!"
