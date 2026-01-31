#!/bin/bash
# =============================================================================
# EleutherIA - Local Deployment Script
# =============================================================================
# Usage:
#   ./scripts/deploy-local.sh              # Core services
#   ./scripts/deploy-local.sh --admin      # + PgAdmin
#   ./scripts/deploy-local.sh --full       # + Monitoring
#   ./scripts/deploy-local.sh --stop       # Stop all
#   ./scripts/deploy-local.sh --clean      # Stop + remove volumes
# =============================================================================

set -euo pipefail

cd "$(dirname "$0")/.."

case "${1:-}" in
    --stop)
        echo "Stopping services..."
        docker compose --profile full down
        ;;
    --clean)
        echo "Removing containers and volumes..."
        docker compose --profile full down -v --remove-orphans
        ;;
    --admin)
        echo "Starting with admin tools..."
        DOCKER_BUILDKIT=1 docker compose --profile admin up -d --build
        ;;
    --full)
        echo "Starting full stack..."
        DOCKER_BUILDKIT=1 docker compose --profile full up -d --build
        ;;
    *)
        echo "Starting core services..."
        DOCKER_BUILDKIT=1 docker compose up -d --build
        ;;
esac

if [[ "${1:-}" != "--stop" && "${1:-}" != "--clean" ]]; then
    echo ""
    echo "EleutherIA URLs:"
    echo "  Frontend:  http://localhost:80"
    echo "  API Docs:  http://localhost:8000/docs"
    echo "  Qdrant:    http://localhost:6333/dashboard"
    echo ""
    echo "Commands:"
    echo "  Logs:  docker compose logs -f"
    echo "  Stop:  ./scripts/deploy-local.sh --stop"
fi
