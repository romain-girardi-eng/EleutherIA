# =============================================================================
# EleutherIA — opencode runtime container
# =============================================================================
# Bundles the sst/opencode CLI (Node 24 base) and Python 3.14 so opencode can
# launch the EleutherIA MCP server as a stdio subprocess. One image is simpler
# to operate than splitting into two and avoids an internal MCP-over-HTTP hop
# during agent runs.
#
# Build context must be the repository root:
#   docker build -f deploy/opencode/Dockerfile .

# -----------------------------------------------------------------------------
# Stage 1: Python build — install EleutherIA packages and the MCP server.
# -----------------------------------------------------------------------------
FROM python:3.14-slim-bookworm AS py-builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /build

# Copy package metadata first for better layer caching.
COPY database/pyproject.toml database/README.md ./database/
COPY database/src ./database/src/

COPY ["knowledge graph/pyproject.toml", "knowledge graph/README.md", "./kg/"]
COPY ["knowledge graph/src", "./kg/src/"]

COPY graphrag/pyproject.toml graphrag/README.md ./graphrag/
COPY graphrag/src ./graphrag/src/

COPY mcp_server/pyproject.toml mcp_server/README.md ./mcp_server/
COPY mcp_server ./mcp_server/

RUN pip install --no-cache-dir --no-compile \
    ./database \
    ./kg \
    "./graphrag[api,llm]" \
    ./mcp_server

# -----------------------------------------------------------------------------
# Stage 2: Final image — Node 24 base with Python 3.14 + opencode CLI.
# -----------------------------------------------------------------------------
FROM node:24-bookworm-slim

LABEL org.opencontainers.image.title="EleutherIA opencode runtime" \
      org.opencontainers.image.description="sst/opencode serve with the EleutherIA MCP server bundled" \
      org.opencontainers.image.source="https://github.com/romain-girardi-eng/EleutherIA" \
      org.opencontainers.image.licenses="CC-BY-4.0"

# System deps for the runtime: libpq5 for asyncpg/psycopg, curl for the
# opencode installer + healthcheck, ca-certificates for HTTPS, tini for
# proper signal handling. Python 3.14 itself is not in Debian bookworm
# repos — we copy the full Python install from the python:3.14 image
# below (same minor version as py-builder so the venv is binary-compatible).
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    libffi8 \
    libssl3 \
    libsqlite3-0 \
    libbz2-1.0 \
    zlib1g \
    libreadline8 \
    libncursesw6 \
    libgdbm6 \
    liblzma5 \
    curl \
    ca-certificates \
    bash \
    tini \
    unzip \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy the Python 3.14 interpreter and stdlib from the official image.
# /usr/local contains the python binary plus its standard library.
COPY --from=python:3.14-slim-bookworm /usr/local /usr/local

# Install the opencode CLI. The upstream installer drops the binary under
# /root/.opencode/bin/opencode by default. We run it explicitly as root in
# the build stage and then symlink it into /usr/local/bin.
RUN curl -fsSL https://opencode.ai/install | bash \
    && ln -s /root/.opencode/bin/opencode /usr/local/bin/opencode \
    && opencode --version

# Bring in the Python venv built above. Path-stable because /opt/venv was
# the build path and stage 2 copies python's /usr/local from the same
# python:3.14-slim-bookworm image.
COPY --from=py-builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONFAULTHANDLER=1

WORKDIR /app

# Bake the EleutherIA opencode config into the image. We rewrite the MCP
# command path so it resolves inside the container, then copy the agent
# markdown files.
COPY deploy/opencode/opencode.container.json /app/opencode.json
COPY .opencode /app/.opencode
COPY data/kg /app/data/kg

EXPOSE 4096

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -fsS http://localhost:4096/doc > /dev/null || exit 1

ENTRYPOINT ["/usr/bin/tini", "--"]

# opencode serve picks up opencode.json from the working directory.
CMD ["sh", "-c", "opencode serve --hostname 0.0.0.0 --port 4096"]
