# syntax=docker/dockerfile:1.7
# =============================================================================
# EleutherIA Frontend - Production-Ready Multi-Stage Build
# =============================================================================

# -----------------------------------------------------------------------------
# Stage 1: Build React application
# -----------------------------------------------------------------------------
FROM node:22-alpine AS builder

# Build context is the REPOSITORY ROOT, not frontend/: `npm run build` ends
# with scripts/prerender-seo.mjs, which reads the knowledge-graph exports
# from ../data relative to frontend/. Keep the same layout inside the image
# so those relative paths resolve unchanged.
WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN --mount=type=cache,target=/root/.npm \
    npm ci --legacy-peer-deps

COPY data/kg/nodes.jsonl data/kg/edges.jsonl /app/data/kg/
COPY data/corpus/manifest.jsonl /app/data/corpus/
COPY data/scholarly_sources/manifest.jsonl /app/data/scholarly_sources/
COPY frontend/ ./

ARG VITE_API_URL=http://localhost:8000
ARG VITE_APP_COMMIT=unknown
ENV VITE_API_URL=${VITE_API_URL}
ENV VITE_APP_COMMIT=${VITE_APP_COMMIT}

RUN npm run build

# -----------------------------------------------------------------------------
# Stage 2: Production nginx runtime
# -----------------------------------------------------------------------------
FROM nginx:1.27-alpine AS production

LABEL org.opencontainers.image.title="EleutherIA Frontend" \
      org.opencontainers.image.description="React frontend for ancient philosophy knowledge graph" \
      org.opencontainers.image.source="https://github.com/romain-girardi-eng/EleutherIA" \
      org.opencontainers.image.licenses="CC-BY-4.0"

RUN apk add --no-cache curl

COPY frontend/nginx.conf /etc/nginx/nginx.conf

COPY --from=builder /app/frontend/dist /usr/share/nginx/html

RUN mkdir -p /var/cache/nginx/client_temp \
             /var/cache/nginx/proxy_temp \
             /var/cache/nginx/fastcgi_temp \
             /var/cache/nginx/uwsgi_temp \
             /var/cache/nginx/scgi_temp \
    && chown -R nginx:nginx /var/cache/nginx \
    && chown -R nginx:nginx /var/log/nginx \
    && chown -R nginx:nginx /usr/share/nginx/html \
    && touch /var/run/nginx.pid \
    && chown nginx:nginx /var/run/nginx.pid

USER nginx

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:80/health || curl -f http://localhost:80/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
