# EleutherIA Deployment

Docker-based deployment for the EleutherIA platform.

## Quick Start

```bash
# From repo root
cp .env.example .env
# Edit .env with your API keys

# Start all services
docker compose -f deploy/docker/docker-compose.yml up -d

# Or use Makefile
make run
```

## Services

| Service | Port | Description |
|---------|------|-------------|
| Frontend | 80 | React UI |
| Backend | 8000 | FastAPI server |
| PostgreSQL | 5432 | Database |
| Qdrant | 6333 | Vector DB |

## Configurations

### docker-compose.yml (Production)
Full stack with all services, optimized for production.

### docker-compose.dev.yml (Development)
Development setup with hot reload and debugging.

## Monitoring (Optional)

```bash
# Start with monitoring
docker compose -f deploy/docker/docker-compose.yml \
               -f deploy/monitoring/docker-compose.monitoring.yml up -d
```

Adds:
- Prometheus (metrics) - port 9090
- Grafana (dashboards) - port 3000

## Commands

```bash
# View logs
docker compose -f deploy/docker/docker-compose.yml logs -f

# Backend logs only
docker compose -f deploy/docker/docker-compose.yml logs -f backend

# Stop services
docker compose -f deploy/docker/docker-compose.yml down

# Stop and remove volumes (data loss!)
docker compose -f deploy/docker/docker-compose.yml down -v
```

## Environment Variables

See `.env.example` in repo root for all configuration options.

Required:
- `MOONSHOT_API_KEY` or `GEMINI_API_KEY` (for LLM)
- `DATABASE_URL` (auto-configured in Docker)
- `QDRANT_URL` (auto-configured in Docker)
