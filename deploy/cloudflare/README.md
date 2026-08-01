# Cloudflare Workers Pipeline — RETIRED

This edge pipeline was retired on **2026-05-14** as part of the platform migration (Phase C).

It duplicated the FastAPI GraphRAG logic at the edge (Workers + Hono + a standalone Qdrant client). In the new architecture, the canonical backend is the FastAPI app under `backend/` and `graphrag/`, exposed publicly through the platform's Cloudflare tunnel (`free-will.app`). The vectorless retrieval path further removed the need for an edge-side vector client.

The TypeScript sources, tests, `wrangler.toml`, and build configuration have been removed. The full historical implementation lives in git history — inspect the last commit that touched `deploy/cloudflare/src/` before the deletion to recover it.

See `docs/plans/2026-05-14-migration-design.md` (Phase C, step 7) for context.
