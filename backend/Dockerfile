# =============================================================================
# EleutherIA Backend — Multi-Stage Production Build
# =============================================================================
# Build context must be the repository root:
#   docker build -f backend/Dockerfile .

# -----------------------------------------------------------------------------
# Stage 1: Build dependencies + install packages
# -----------------------------------------------------------------------------
FROM python:3.14-slim-bookworm AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /build

# Copy package metadata first for better layer caching
COPY database/pyproject.toml database/README.md ./database/
COPY database/src ./database/src/

# Use JSON form for paths with spaces (knowledge graph/)
COPY ["knowledge graph/pyproject.toml", "knowledge graph/README.md", "./kg/"]
COPY ["knowledge graph/src", "./kg/src/"]

COPY graphrag/pyproject.toml graphrag/README.md ./graphrag/
COPY graphrag/src ./graphrag/src/

# Install all three packages + auth dependencies
RUN pip install --no-cache-dir --no-compile \
    ./database \
    ./kg \
    "./graphrag[api,llm]" \
    "passlib[bcrypt]" \
    PyJWT

# -----------------------------------------------------------------------------
# Stage 2: Production runtime
# -----------------------------------------------------------------------------
FROM python:3.14-slim-bookworm

LABEL org.opencontainers.image.title="EleutherIA Backend" \
      org.opencontainers.image.description="FastAPI backend for ancient philosophy knowledge graph" \
      org.opencontainers.image.source="https://github.com/romain-girardi-eng/EleutherIA" \
      org.opencontainers.image.licenses="CC-BY-4.0"

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    tini \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

RUN groupadd --gid 1000 eleutherai \
    && useradd --uid 1000 --gid eleutherai --shell /bin/bash --create-home eleutherai

COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONFAULTHANDLER=1

WORKDIR /app

# Copy backend orchestrator (main.py, routes/, dependencies.py, etc.)
COPY --chown=eleutherai:eleutherai backend/ ./backend/
COPY --chown=eleutherai:eleutherai data/kg/ ./data/kg/

USER eleutherai

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/api/health || exit 1

ENTRYPOINT ["/usr/bin/tini", "--"]

CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers ${UVICORN_WORKERS:-1} --loop uvloop --http httptools"]
