# syntax=docker/dockerfile:1.7
# =============================================================================
# EleutherIA Backend - Production-Ready Multi-Stage Build
# =============================================================================

# -----------------------------------------------------------------------------
# Stage 1: Build dependencies
# -----------------------------------------------------------------------------
FROM python:3.11-slim-bookworm AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /build
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-compile -r requirements.txt

# -----------------------------------------------------------------------------
# Stage 2: Production runtime
# -----------------------------------------------------------------------------
FROM python:3.11-slim-bookworm AS production

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

COPY --chown=eleutherai:eleutherai api/ ./api/
COPY --chown=eleutherai:eleutherai services/ ./services/
COPY --chown=eleutherai:eleutherai utils/ ./utils/

USER eleutherai

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

ENTRYPOINT ["/usr/bin/tini", "--"]

CMD ["sh", "-c", "uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers ${UVICORN_WORKERS:-1} --loop uvloop --http httptools"]
