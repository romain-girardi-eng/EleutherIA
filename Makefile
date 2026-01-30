# EleutherIA Makefile
# Simple commands for development, testing, and deployment

.PHONY: help install install-database install-kg install-graphrag \
        run dev stop clean test test-database test-kg test-graphrag test-coverage \
        lint format typecheck quality fix \
        frontend-install frontend-dev frontend-build frontend-test \
        docker-build docker-up docker-down docker-logs \
        db-migrate db-backup db-restore docs docs-serve

# Default target
help:
	@echo "EleutherIA Development Commands"
	@echo ""
	@echo "Quick Start:"
	@echo "  make install          Install all 3 packages in editable mode"
	@echo "  make run              Start full stack (Docker)"
	@echo "  make dev              Start development servers"
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
	@echo ""
	@echo "Frontend:"
	@echo "  make frontend-install Install frontend dependencies"
	@echo "  make frontend-dev     Start frontend dev server"
	@echo "  make frontend-build   Build frontend for production"
	@echo "  make frontend-test    Run frontend tests"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build     Build all Docker images"
	@echo "  make docker-up        Start full stack"
	@echo "  make docker-down      Stop full stack"
	@echo "  make docker-logs      View logs"
	@echo ""
	@echo "Database:"
	@echo "  make db-migrate       Run database migrations"
	@echo "  make db-backup        Backup PostgreSQL"
	@echo "  make db-restore       Restore from backup"
	@echo ""
	@echo "Documentation:"
	@echo "  make docs             Build documentation"
	@echo "  make docs-serve       Serve docs locally"
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
	cd kg && pip install -e ".[dev]"

install-graphrag:
	cd graphrag && pip install -e ".[dev]"

# =============================================================================
# Running
# =============================================================================

run:
	docker compose -f deploy/docker/docker-compose.yml up -d
	@echo ""
	@echo "EleutherIA is running!"
	@echo "  Frontend: http://localhost"
	@echo "  API Docs: http://localhost:8000/docs"
	@echo "  Qdrant:   http://localhost:6333/dashboard"

dev:
	docker compose -f deploy/docker/docker-compose.dev.yml up -d

stop:
	docker compose -f deploy/docker/docker-compose.yml down

# =============================================================================
# Testing
# =============================================================================

test: test-database test-kg test-graphrag frontend-test
	@echo "All tests passed!"

test-database:
	cd database && python -m pytest tests/ -v

test-kg:
	cd kg && python -m pytest tests/ -v

test-graphrag:
	cd graphrag && python -m pytest tests/ -v

test-coverage:
	cd database && python -m pytest tests/ --cov=src --cov-report=html
	cd kg && python -m pytest tests/ --cov=src --cov-report=html
	cd graphrag && python -m pytest tests/ --cov=src --cov-report=html
	@echo "Coverage reports generated in */htmlcov/"

# =============================================================================
# Code Quality
# =============================================================================

lint:
	ruff check database/src kg/src graphrag/src

format:
	ruff format database/src kg/src graphrag/src

typecheck:
	mypy database/src kg/src graphrag/src

quality: lint typecheck
	@echo "Code quality checks passed!"

fix:
	ruff check --fix database/src kg/src graphrag/src
	ruff format database/src kg/src graphrag/src
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
# Docker
# =============================================================================

docker-build:
	docker compose -f deploy/docker/docker-compose.yml build

docker-up:
	docker compose -f deploy/docker/docker-compose.yml up -d

docker-down:
	docker compose -f deploy/docker/docker-compose.yml down

docker-logs:
	docker compose -f deploy/docker/docker-compose.yml logs -f

# =============================================================================
# Database
# =============================================================================

db-migrate:
	cd database && alembic upgrade head

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
	@echo "Documentation is in docs/ - no build step required (Markdown)"

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
