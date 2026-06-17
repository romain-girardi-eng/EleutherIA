# Incident playbook

What to do when things break during or after the migration. Organized by
symptom. Each entry: 2–3 line diagnostic + exact recovery commands.

For end-to-end rollback strategy (full Layer 1 → Layer 4), see
[`migration-master-runbook.md` § End-to-end rollback strategy](./migration-master-runbook.md#end-to-end-rollback-strategy).

---

## Symptom: `free-will.app` returns 502

**Diagnostic.** The Cloudflare tunnel reached an origin that responded with 502
or no response at all. Either the tunnel itself is broken, or the
`eleutheria-api` container is unhealthy.

```bash
# 1. Tunnel status
ssh deploy-host cloudflared tunnel info <deploy-tunnel-id>

# 2. Container healthcheck
ssh deploy-host docker compose ps eleutheria-api

# 3. Direct call to the container (bypassing tunnel)
ssh deploy-host curl -v http://localhost:8015/api/health
```

**Recovery, in order:**

1. If container `(unhealthy)`: `ssh deploy-host docker compose restart eleutheria-api`. Wait 60s, recheck. If still unhealthy, inspect logs: `docker compose logs --tail=200 eleutheria-api`.
2. If container healthy but tunnel info shows degraded: `ssh deploy-host systemctl restart cloudflared`.
3. If both healthy but external 502 persists for ≥ 5 min: **DNS revert** to Railway. Edit `free-will.app` CNAME back to the old Railway target. Investigate root cause after.

---

## Symptom: backend logs show `supabase connection refused`

**Diagnostic.** The Postgres connection to Supabase failed. Almost always one
of: wrong port, expired service-role key, wrong DSN.

```bash
ssh deploy-host docker compose logs --tail=50 eleutheria-api | grep -i supabase
ssh deploy-host docker compose exec eleutheria-api env | grep DATABASE_URL
```

**Check, in order:**

1. **Port.** DSN must end `:5432/postgres` for migrations and `:5432` for runtime via session pooler. The transaction pooler `:6543` breaks long-lived connections. Fix: re-export with port 5432.
2. **Service-role key expired or rotated.** Supabase dashboard → Settings → API → check `service_role` key matches the `.env`. Regenerate if needed and update `.env`, then `docker compose restart eleutheria-api`.
3. **DSN host.** Direct DSN is `db.<REF>.supabase.co`. Pooler DSN is `aws-0-<region>.pooler.supabase.com`. Confirm which one is in use vs which is needed (direct for migrations, pooler for runtime).
4. **IP allowlist.** If the new Supabase project has the "Restrict network access" feature on, add the the platform host's egress IP. Find IP: `ssh deploy-host curl -s ifconfig.me`.

---

## Symptom: GraphRAG queries return empty answers

**Diagnostic.** The agent reached the synthesis step but produced no answer.
Three usual causes: KG snapshot not loaded, LLM key not resolved, retrieval
returned zero hits.

```bash
# Check snapshot
ssh deploy-host docker compose exec eleutheria-api \
  python -c "from eleutheria_graphrag.services.snapshot_retrieval import SnapshotRetrieval; r=SnapshotRetrieval(); print(len(r._nodes))"

# Check LLM provider
ssh deploy-host docker compose exec eleutheria-api \
  python -c "from backend.services.credentials import resolve_provider; print(resolve_provider('gemini')[:10] + '...')"

# Run eval harness on the failing query
python tests/eval/run_eval.py --queries tests/eval/queries/<failing>.yaml --base-url https://free-will.app
```

**Recovery:**

1. Snapshot count is 0 → snapshot bucket not reachable or file missing. Re-upload: `python -m cli.main snapshot upload`.
2. LLM key resolves to `None` → CredentialsBridge misconfigured. Confirm `EXTERNAL_INTEGRATION=true` and `CREDENTIALS_ENCRYPTION_KEY` matches the one used to write the credentials. Re-store keys via the platform admin UI under `user_id=eleutheria-system`.
3. Eval shows the query has zero entity hits → confirms retrieval-side issue; see next entry.

---

## Symptom: eval shows > 5% recall drop after vectorless cutover

**Diagnostic.** Phase B acceptance gate failed. Lemma expansion didn't cover
the paraphrase variation that vector search used to handle.

```bash
python tests/eval/run_eval.py --compare baseline.json vectorless.json
# inspect the per-query diff, identify the worst offenders
```

**Recovery, in order:**

1. **Tune lemma expansion prompts.** Add the failing query's expected lemmas to the few-shot examples in `services/lemma_expansion.py`. Re-run only failing queries: `python tests/eval/run_eval.py --queries <failing.yaml> ...`.
2. **Increase tree depth.** For multi-hop concept queries, bump `TreeIndexService.max_depth` 2 → 3.
3. **Partial rollback.** If 3rd iteration still fails: keep the lemma expansion improvement, restore `VectorStrategy` from git history. The vector-leg deletion commits were separate by design.
   ```bash
   git revert <vectorstrategy-deletion-commit>
   git push origin main
   ```
   Qdrant Cloud is still running (decommission only happens +7 days post-cutover), so the path is live.

---

## Symptom: Temporal worker crash-looping

**Diagnostic.** The worker container restarts every few seconds. Usually:
unreachable Temporal cluster, mismatched task-queue name, or a workflow
definition that fails to parse.

```bash
ssh deploy-host docker compose logs --tail=100 eleutheria-worker
ssh deploy-host docker compose exec eleutheria-worker \
  python -c "import temporalio; print(temporalio.__version__)"
```

**Recovery:**

1. **Temporal unreachable.** Confirm `temporal:7233` resolves from inside the worker container: `docker compose exec eleutheria-worker nc -zv temporal 7233`. If DNS fails, the worker isn't on the `app-network`. Fix: ensure `deploy-compose.yml` attaches the worker to `app-network` as `external: true`.
2. **Task queue mismatch.** Worker logs `task_queue=...` — confirm it matches `TEMPORAL_TASK_QUEUE` in the `.env`. Default is `eleutheria-ingestion`.
3. **Workflow parse error.** Log will show `ImportError` or `AttributeError` at startup. Fix the workflow code, rebuild image: `docker compose build eleutheria-worker && docker compose up -d eleutheria-worker`.
4. **Last resort.** Stop the worker: `docker compose stop eleutheria-worker`. Run the underlying script directly. The API is unaffected.

---

## Symptom: `credentials-provider` fails to install

**Diagnostic.** `pip install -e .` errors on the `credentials-provider` git
dependency. Usually: wrong Python version, unreachable git URL, or a
subdirectory path mismatch.

```bash
python --version   # must be 3.14.x
git ls-remote <EXTERNAL_COMMON_REPO_URL>   # must list refs
```

**Recovery:**

1. **Wrong Python.** Activate 3.14 venv. Confirm: `which python` points to a 3.14 binary.
2. **Git URL unreachable.** Check SSH key for the repo: `ssh -T git@<host>`. If the repo is private, the install host needs SSH credentials. On the platform host, mount an SSH key into the build context, or switch to a `https://` URL with a token.
3. **Subdirectory path drift.** `credentials-provider` lives at `modules/shared/credentials-provider` inside `private-repo`. If that path moved, update the pyproject `subdirectory=` parameter.
4. **Fallback: vendor `credentials_service.py`.** Copy the single file into `backend/services/credentials_service_vendored.py` and import from there. Cleaner than a broken dep. Mark the vendor with a `# VENDORED FROM credentials-provider@<sha>` comment and a +30-day calendar reminder to re-sync.

---

## Symptom: DNS swap propagation slow

**Diagnostic.** DNS still returns old target > 60s after the CNAME edit.

```bash
dig free-will.app +short
dig @1.1.1.1 free-will.app +short
dig @8.8.8.8 free-will.app +short
```

**Recovery:** Confirm CNAME save persisted (session expiry can silently fail).
Confirm TTL was 60 at edit time — if 3600, the 24h-ahead lowering was skipped,
wait it out, Railway fallback serves. Split state across resolvers > 5 min is
acceptable during the cutover window since both targets serve the same data.

---

## Symptom: container OOM-killed

**Diagnostic.** `docker compose ps` shows `Exited (137)`. Memory limit exceeded.

```bash
ssh deploy-host docker stats --no-stream eleutheria-api
ssh deploy-host dmesg | grep -i "killed process"
```

**Recovery:** Bump memory limit in `deploy/deploy-compose.yml` from `1g` to
`1.5g`, restart. Common cause: KG snapshot loaded twice — confirm
`SnapshotRetrieval` is a singleton in `backend/dependencies.py`.

---

## Quick reference — recovery commands

| Action | Command |
|--------|---------|
| Revert API container | `ssh deploy-host docker compose restart eleutheria-api` |
| Stop API container | `ssh deploy-host docker compose stop eleutheria-api` |
| DNS revert to Railway | Cloudflare dashboard → edit `free-will.app` CNAME → `<old-railway>.up.railway.app` ⚠️ **Railway KG is stale vs Supabase (different node/edge counts as of 2026-05-26); rollback serves out-of-date data — sync Railway DB to current Supabase first or accept data drift for the incident window.** |
| Revert DB | `export DATABASE_URL="<old-supabase>"` + restart |
| Reload tunnel | `ssh deploy-host cloudflared tunnel reload <deploy-tunnel-id>` |
| Tail logs | `ssh deploy-host docker compose logs -f eleutheria-api` |
| Stop worker | `ssh deploy-host docker compose stop eleutheria-worker` |
| Re-run eval on one query | `python tests/eval/run_eval.py --queries <file.yaml> --base-url <url>` |
