# Repository Guidelines

## Project Structure & Module Organization
- `backend/` (FastAPI): `api/` routers, `models/` Pydantic/SQL models, `services/` integration layers, `utils/` helpers; Docker entrypoint in `backend/Dockerfile`.
- `frontend/` (React + Vite): `src/` components and views, `public/` static assets, `tailwind.config.ts` for design tokens; production bundles land in `dist/`.
- Data and reference assets live under `assets/`, `exported_texts/`, and `ancient_free_will_database.json`; do not edit generated files without documenting provenance.
- Automation and ingestion scripts sit at the repo root (e.g., `setup_database.py`, `generate_kg_embeddings.py`); Python tests accompany them as `test_*.py`.

## Build, Test, and Development Commands
- `./setup.sh` — turnkey bootstrap: spins up Docker services, installs Python deps, seeds sample data, runs smoke tests.
- `docker-compose up` — launches PostgreSQL + PgAdmin for local experimentation.
- `cd backend && pip install -r requirements-dev.txt && uvicorn api.main:app --reload --host 0.0.0.0 --port 8000` — install backend toolchain and start the API.
- `cd frontend && npm install && npm run dev` — install UI deps and serve the Vite dev app on port 5173.
- `pytest` (root) — execute the Python suite; add `--cov=backend` to review coverage deltas before pushing.
- `cd frontend && npm run build` — ensure production bundles compile without warnings.

## Coding Style & Naming Conventions
- Python: 4-space indentation; snake_case modules/functions, PascalCase data models; format with `black`, order imports via `isort`, lint using `flake8`, and guard new types with `mypy`.
- TypeScript/React: honor ESLint rules (`npm run lint`); name components in PascalCase, hooks/handlers in camelCase; co-locate Tailwind utility classes with JSX.
- Keep environment configuration in `.env` files referenced by scripts; never commit credentials exported by `setup_environment.py`.

## Testing Guidelines
- Prefer focused `pytest` modules mirroring the feature (`test_database.py`, `test_graphrag_pipeline.py`); structure new tests as `test_<subject>.py` and isolate fixtures in-module.
- When a test touches Postgres or Qdrant, document required datasets and ensure containers from `docker-compose up` are running.
- Aim to keep new backend modules covered ≥80%; use `pytest --cov=<package>` to verify and capture regressions in pull request notes.

## Commit & Pull Request Guidelines
- Follow Conventional Commits as seen in history (`feat:`, `fix:`, `refactor:`); keep tense imperative and scope narrow.
- Each PR should describe the change, list migrations or data reload steps, and paste relevant command outputs; add screenshots/gifs for UI tweaks from `frontend/src`.
- Link issues, docs, or research notes (e.g., `PROJECT_SUMMARY.md`) so reviewers can trace assumptions; request review once automated checks pass.
