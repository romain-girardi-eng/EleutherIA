# Phase A — Supabase rebuild runbook

Operator-facing runbook for redeploying a fresh Supabase project from the in-tree
KG snapshot (`data/kg/nodes.jsonl` + `data/kg/edges.jsonl`). The bootstrap is
idempotent: re-running it upserts rows by `node_id` / `work_id` / `passage_id`,
so the same script applies cleanly to a brand-new project or a re-run.

The full design context for this phase is in
`docs/plans/2026-05-14-migration-design.md`.

## Preflight checklist

Tick every box before touching the new project.

- [ ] New Supabase project provisioned (suggested name: `eleutheria-prod`,
      region close to backend host). Note the project ref.
- [ ] **Service-role key** captured into 1Password / Bitwarden. Never paste
      it in chat or commit it.
- [ ] **Direct database URL** captured (Settings → Database → "Connection
      string" → URI, **port 5432**, not the transaction pooler on `6543`).
      `bootstrap_supabase.py` will warn (line 814) if the URL is the
      transaction pooler — pooled connections break long migrations.
- [ ] Snapshot files present and current:
      `data/kg/nodes.jsonl` (~17,746 lines), `data/kg/edges.jsonl` (~43,000
      lines). If older than the last KG quality phase commit, regenerate
      via the snapshot script under `knowledge graph/src/eleutheria_kg/services/snapshot.py`.
- [ ] Current Supabase project exported (if any) — even a `pg_dump` of
      `free_will.*` is enough as a fallback.
- [ ] `python -c "import asyncpg, typer"` works in the active virtualenv.

## Deploy sequence

All commands assume CWD = repo root.

### 1. Export the direct DSN

```bash
export SUPABASE_DATABASE_URL="postgresql://postgres:<PWD>@db.<REF>.supabase.co:5432/postgres"
```

Sanity check: the URL must contain `:5432/` and **not** `:6543/`.

### 2. Dry-run the bootstrap

```bash
python database/scripts/dry_run_bootstrap.py
```

This verifies the snapshot files, prints their mtime, and runs
`bootstrap_supabase.py --dry-run` (no network calls). Confirm the
counts look right (~17,746 nodes, ~42,925 edges) before continuing.

### 3. Apply schema in order

```bash
psql "$SUPABASE_DATABASE_URL" -v ON_ERROR_STOP=1 -f database/schema/schema.sql
psql "$SUPABASE_DATABASE_URL" -v ON_ERROR_STOP=1 -f database/schema/work_tree_indices.sql
psql "$SUPABASE_DATABASE_URL" -v ON_ERROR_STOP=1 -f database/schema/supabase_functions.sql
psql "$SUPABASE_DATABASE_URL" -v ON_ERROR_STOP=1 -f database/schema/supabase_public_api.sql
psql "$SUPABASE_DATABASE_URL" -v ON_ERROR_STOP=1 -f database/migrations/20260514_01_supabase_rebuild_support.sql
```

`bootstrap_supabase.py` re-applies these by default; this step exists so
operators can see schema errors without snapshot noise interleaved.

### 4. Run the bootstrap (idempotent upsert)

```bash
python database/scripts/bootstrap_supabase.py
```

Do **not** pass `--replace-data` on a fresh project — there is nothing to
truncate. Ce mode est réservé à une reconstruction hors ligne/jetable, service
arrêté. Pour toute base servie, employer le
[déploiement staging transactionnel](../development/staged-deploy.md).

Expected stdout: `kg_nodes`, `kg_edges`, `ancient_works`, `passages`,
`passage_citations` row counts.

### 5. Translation pass

```bash
export DATABASE_URL="$SUPABASE_DATABASE_URL"
python database/scripts/create_passage_translations.py --confirm \
  --translations data/translations/translations_p0.json
```

This inserts `_en` KG nodes + `translation_of` edges for any pre-computed
translations. Skip if `data/translations/` is empty — translations can be
backfilled later.

### 6. Verification

```bash
python database/scripts/verify_supabase_deploy.py
```

Exits `0` if every check passes, `1` on any failure. Output is a plain
checklist. See "Verification" below for what is asserted.

## Verification — what is checked

| # | Check | Expected |
|---|-------|----------|
| 1 | `free_will.ancient_works` count | ≈ 487 (±10%) |
| 2 | `free_will.passages` count | ≈ 69,277 (±10%) |
| 3 | `free_will.kg_nodes` count | ≈ 17,746 (±10%) |
| 4 | `free_will.kg_edges` count | ≈ 42,925 (±10%) |
| 5 | `free_will.passage_citations` count | > 0 |
| 6 | Anon-role SELECT on `kg_nodes` | Returns rows (RLS read policy applied) |
| 7 | Service-role write on `free_will.users` | INSERT + rollback succeeds |
| 8 | English translation nodes (`node_id LIKE '%_en'`) | > 0 (warn if 0) |
| 9 | `public.get_kg_stats()` RPC | Returns a row |

A failed check 7 (RLS denies write) means the service-role key is wrong
or the URL is connected as a non-service role.

## Cutover

1. Update `DATABASE_URL` in production env (Cloudflare worker secrets, Docker
   Compose `.env`, Railway / Fly / etc.) to the new direct connection string.
   Runtime services should use the **session pooler** DSN (port `5432` on
   `aws-0-<region>.pooler.supabase.com`) for connection efficiency — the
   transaction pooler `6543` is fine for stateless reads.
2. Restart backend services: `docker compose -f deploy/docker-compose.yml restart backend`.
3. Smoke test: hit `GET /api/works`, `GET /api/kg/nodes?limit=1`, and one
   GraphRAG query end-to-end. Confirm answers contain citations.
4. Monitor error rate + p95 latency for 24h.

## Rollback

If anything goes wrong within the 24h window:

1. Switch `DATABASE_URL` back to the previous project.
2. Restart backend (same command as cutover step 2).
3. Open a postmortem; do **not** delete the new project yet.

Keep the old Supabase project online for **7 days** as fallback. After 7 days
of clean operation, pause/delete the old project.

## Common failures + remedies

| Symptom | Cause | Fix |
|---------|-------|-----|
| `connection refused on port 6543` | Using transaction pooler for migration | Switch to direct port 5432 |
| `ON CONFLICT not firing`, rows duplicate | `--replace-data` passed unintentionally | Re-run without `--replace-data` |
| `permission denied for table users` | Service-role key wrong / using anon | Re-export `SUPABASE_DATABASE_URL` with the `postgres` user, not the anon role |
| `kg_nodes 0 rows` after bootstrap | Snapshot files missing or empty | Re-run step 2 (dry-run) and inspect mtime |
| Verification check 8 fails (0 translations) | Translation pass skipped | Run step 5, or accept and backfill later |
| `relation "free_will.X" does not exist` | Schema step 3 skipped or failed | Re-run step 3 in order, watch for first error |
| Bootstrap hangs >5min on a batch | Pooler timeout | Cancel, switch DSN to direct, retry |

## Notes

- `bootstrap_supabase.py` est relançable **sans** `--replace-data` grâce aux
  `ON CONFLICT`/gardes `NOT EXISTS`. Sur une base servie, ne jamais utiliser son
  chemin destructif ; suivre le
  [runbook staging](../development/staged-deploy.md).
- `verify_supabase_deploy.py` is **read-only** — it never writes data. The
  service-role write check uses an explicit transaction that is rolled back.
- Tolerances on count checks (±10%) absorb ongoing ingestion. If counts
  drift far above expected, audit `data/kg/` for accidental duplicates.
