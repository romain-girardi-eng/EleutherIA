# EleutherIA Makefile
# Simple commands for development, testing, and deployment

.PHONY: help install install-database install-kg install-graphrag \
        run local stop local-clean prod prod-stop \
        test test-database test-kg test-graphrag test-coverage \
        lint format typecheck quality fix \
        kg-rdf kg-shacl kg-shacl-strict kg-bibtex scholarly-backlog sparql sparql-stop \
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
	@echo "  make kg-shacl-strict  Validate KG invariants only; exit 2 on any violation (CI gate)"
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
	@echo "  make deploy-data      Stage, verify and atomically publish KG + corpus"
	@echo "  make deploy-data-dry-run  Load/verify staging without publishing"
	@echo "  make deploy-data-rollback Swap the retained data generation back"
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

kg-shacl-strict:
	.venv/bin/python scripts/validate_kg_shacl.py --invariants-only --fail-on-violation

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

# ==========================================================================
# Production lifecycle
# ==========================================================================
PROD_SSH ?= ben@65.108.9.16
PROD_DIR ?= /home/ben/EleutherIA
PROD_BACKUP_DIR ?= /home/ben/eleutheria-backups
PROD_COMPOSE ?= docker compose -p deploy -f deploy/pragma-compose.yml -f /tmp/eleutheria-compose-runtime.yml
RC_SHA ?=

.PHONY: check require-rc-sha deploy rollback deploy-data deploy-data-dry-run \
	deploy-data-rollback prod-status prod-logs prod-recreate

# Fast quality gate
check: lint

# Production operations are release-addressed. Refuse branch names, short SHAs
# and an empty value so backend/data can never race a mutable Pages deployment.
require-rc-sha:
	@printf '%s' '$(RC_SHA)' | grep -Eq '^[0-9a-f]{40}$$' || { \
	  echo 'RC_SHA must be the exact 40-character verified release commit'; exit 2; }

# Deploy one immutable backend/data release. The API is never recreated ahead
# of its schema/data: dump -> build only -> migrations -> staging dry-run ->
# atomic swap -> recreate. Cloudflare Pages remains a separate, later push.
# Writes a deploy record to .deploys/<epoch>.json so rollback can return to the
# previous SHA.
deploy: require-rc-sha
	ssh -o BatchMode=yes $(PROD_SSH) 'set -eu; cd $(PROD_DIR); \
	  git fetch -q origin; git cat-file -e $(RC_SHA)^{commit}; git checkout -q --detach $(RC_SHA); \
	  BACKUP_DIR=$(PROD_BACKUP_DIR); mkdir -p "$$BACKUP_DIR"; \
	  BACKUP="$$BACKUP_DIR/predeploy-$$(date -u +%Y%m%dT%H%M%SZ)-$(RC_SHA).dump"; \
	  docker exec eleutheria-db sh -lc '\''pg_dump -U "$$POSTGRES_USER" -d "$$POSTGRES_DB" -Fc -f /tmp/eleutheria-predeploy.dump'\''; \
	  docker cp eleutheria-db:/tmp/eleutheria-predeploy.dump "$$BACKUP" >/dev/null; \
	  docker exec eleutheria-db rm -f /tmp/eleutheria-predeploy.dump; test -s "$$BACKUP"; \
	  $(PROD_COMPOSE) build eleutheria-api eleutheria-worker; \
	  NETWORK=$$(docker inspect -f "{{json .NetworkSettings.Networks}}" eleutheria-api | python3 -c "import json,sys; print(next(iter(json.load(sys.stdin))))"); test -n "$$NETWORK"; \
	  RUNNER="docker run --rm --network $$NETWORK -v $(PROD_DIR):/repo -w /repo --env-file $(PROD_DIR)/.env python:3.12-slim bash -lc"; \
	  $$RUNNER "pip install -q asyncpg && python database/scripts/apply_schema.py \
	    --migration database/migrations/20260824_01_bobzien_consensus_correction.sql \
	    --migration database/migrations/20260824_02_query_traces_private_by_default.sql \
	    --migration database/migrations/20260824_03_secondary_page_evidence.sql \
	    --migration database/migrations/20260825_01_account_requests.sql \
	    --migration database/migrations/20260825_02_user_access_policies.sql \
	    --migration database/migrations/20260825_03_feedback_workflow.sql \
	    --migration database/migrations/20260825_04_account_request_idempotency.sql"; \
	  $$RUNNER "pip install -q asyncpg && python scripts/deploy_data_staged.py --dry-run"; \
	  $$RUNNER "pip install -q asyncpg && python scripts/deploy_data_staged.py"; \
	  $(PROD_COMPOSE) up -d --force-recreate --no-deps --no-build eleutheria-api eleutheria-worker; \
	  echo "predeploy backup: $$BACKUP"'
	@ATTEMPT=0; until curl -sf https://free-will.app/api/health | python3 -c \
	  'import json,sys; h=json.load(sys.stdin); assert h["status"] == "healthy"; assert h["database"] == "connected"; assert h["graphrag"] == "ready"'; do \
	  ATTEMPT=$$((ATTEMPT + 1)); [ $$ATTEMPT -lt 30 ] || { echo 'API health timeout'; exit 1; }; sleep 2; \
	done
	@RELEASE=$$(curl -sf https://free-will.app/api/kg/workspace/stats | python3 -c \
	  'import json,sys; remote=json.load(sys.stdin); local=json.load(open("data/stats.json"))["kg"]; assert remote["served_total_nodes"] == local["nodes"]; assert remote["served_total_edges"] == local["edges"]; print(remote["release_id"])'); \
	test -n "$$RELEASE"; \
	for ATTEMPT in 1 2 3 4 5 6 7 8; do \
	  curl -sfG --data-urlencode "expected_release_id=$$RELEASE" https://free-will.app/api/health | python3 -c \
	    'import json,sys; h=json.load(sys.stdin); assert h["status"] == "healthy"; assert h["database"] == "connected"; assert h["graphrag"] == "ready"' || exit 1; \
	done; \
	echo "public API release verified across 8 probes: $$RELEASE"
	@mkdir -p .deploys
	@SHA=$$(ssh -o BatchMode=yes $(PROD_SSH) 'git -C $(PROD_DIR) rev-parse HEAD'); \
	printf '{"sha":"%s","image":"git:%s","actor":"%s","ts":"%s"}\n' "$$SHA" "$$SHA" "$${USER:-unknown}" "$$(date -u +%FT%TZ)" > .deploys/$$(date -u +%s).json; \
	echo "deploy record: $$SHA"

# Rollback: redeploy the SHA from the previous deploy record (.deploys
# semantics; here rollback = checkout that SHA on the host and rebuild,
# since images are built on the host from git rather than tagged).
rollback:
	@PREV=$$(ls -1t .deploys/*.json 2>/dev/null | sed -n 2p); \
	[ -n "$$PREV" ] || { echo "no previous deploy on record"; exit 1; }; \
	SHA=$$(python3 -c "import json;print(json.load(open('$$PREV'))['sha'])"); \
	printf '%s' "$$SHA" | grep -Eq '^[0-9a-f]{40}$$' || { echo 'invalid rollback SHA'; exit 2; }; \
	echo "rolling back prod to $$SHA"; \
	ssh -o BatchMode=yes $(PROD_SSH) 'cd $(PROD_DIR) && git fetch -q origin && git checkout -q '"$$SHA"' && $(PROD_COMPOSE) up -d --build --no-deps eleutheria-api eleutheria-worker'; \
	sleep 10 && curl -sf https://free-will.app/api/health && echo; \
	printf '{"sha":"%s","image":"git:%s","actor":"%s","ts":"%s","rollback":true}\n' "$$SHA" "$$SHA" "$${USER:-unknown}" "$$(date -u +%FT%TZ)" > .deploys/$$(date -u +%s).json

# Deploy data: load+verify shadow tables, atomically swap all five data tables,
# then recreate API/worker so their in-memory KG observes the new generation.
deploy-data: require-rc-sha
	ssh -o BatchMode=yes $(PROD_SSH) 'cd $(PROD_DIR) && \
	  test "$$(git rev-parse HEAD)" = "$(RC_SHA)" && \
	  NETWORK=$$(docker inspect -f "{{json .NetworkSettings.Networks}}" eleutheria-api | python3 -c "import json,sys; print(next(iter(json.load(sys.stdin))))") && \
	  test -n "$$NETWORK" && \
	  docker run --rm --network "$$NETWORK" -v $(PROD_DIR):/repo -w /repo \
	    --env-file $(PROD_DIR)/.env python:3.12-slim bash -lc \
	    "pip install -q asyncpg && python scripts/deploy_data_staged.py" && \
	  $(PROD_COMPOSE) up -d --force-recreate --no-deps --no-build eleutheria-api eleutheria-worker'
	@sleep 10 && curl -sf https://free-will.app/api/health && echo

deploy-data-dry-run: require-rc-sha
	ssh -o BatchMode=yes $(PROD_SSH) 'cd $(PROD_DIR) && \
	  test "$$(git rev-parse HEAD)" = "$(RC_SHA)" && \
	  NETWORK=$$(docker inspect -f "{{json .NetworkSettings.Networks}}" eleutheria-api | python3 -c "import json,sys; print(next(iter(json.load(sys.stdin))))") && \
	  test -n "$$NETWORK" && \
	  docker run --rm --network "$$NETWORK" -v $(PROD_DIR):/repo -w /repo \
	    --env-file $(PROD_DIR)/.env python:3.12-slim bash -lc \
	    "pip install -q asyncpg && python scripts/deploy_data_staged.py --dry-run"'

deploy-data-rollback:
	ssh -o BatchMode=yes $(PROD_SSH) 'cd $(PROD_DIR) && \
	  NETWORK=$$(docker inspect -f "{{json .NetworkSettings.Networks}}" eleutheria-api | python3 -c "import json,sys; print(next(iter(json.load(sys.stdin))))") && \
	  test -n "$$NETWORK" && \
	  docker run --rm --network "$$NETWORK" -v $(PROD_DIR):/repo -w /repo \
	    --env-file $(PROD_DIR)/.env python:3.12-slim bash -lc \
	    "pip install -q asyncpg && python scripts/deploy_data_staged.py --rollback" && \
	  $(PROD_COMPOSE) up -d --force-recreate --no-deps --no-build eleutheria-api eleutheria-worker'
	@sleep 10 && curl -sf https://free-will.app/api/health && echo

prod-status:
	@ssh -o BatchMode=yes $(PROD_SSH) 'docker ps --filter name=eleutheria --format "table {{.Names}}\t{{.Status}}"'
	@curl -s https://free-will.app/api/health && echo

prod-logs:
	ssh -o BatchMode=yes $(PROD_SSH) 'docker logs --tail 100 -f eleutheria-api'

# Recreate api+worker after a .env change (docker restart does NOT re-read env)
prod-recreate:
	ssh -o BatchMode=yes $(PROD_SSH) 'cd $(PROD_DIR) && $(PROD_COMPOSE) up -d --force-recreate --no-deps --no-build eleutheria-api eleutheria-worker'
