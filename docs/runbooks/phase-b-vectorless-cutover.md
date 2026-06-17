# Phase B — Vectorless cutover

Delete Qdrant. Replace the vector retrieval leg with lemma expansion + tree
navigation + SQL FTS. Gate on an evaluation harness, not on vibes.

Spec: [`../plans/2026-05-14-migration-design.md` § Phase B](../plans/2026-05-14-migration-design.md#phase-b--vectorless-agentic-graph-rag).

This runbook assumes the code work (lemma expansion wired in front of
`SQLStrategy`, `VectorStrategy` deletion commits prepared on a branch) is
complete. The procedure here is **capture baseline → deploy → re-run eval →
compare → confirm or rollback**.

## Pre-cutover

| Check | Command | Expected |
|-------|---------|----------|
| Eval harness installed | `ls tests/eval/run_eval.py` | File exists |
| pyyaml installed | `python -c "import yaml; print(yaml.__version__)"` | `6.x` or newer |
| Eval queries authored | `ls tests/eval/queries/*.yaml` | At least 30 query files |
| Backend running locally | `curl http://localhost:8000/api/health` | `200 OK` |
| Qdrant still up | `curl http://localhost:6333/healthz` | `passed` |
| Phase A complete | See [`phase-a-supabase-rebuild.md`](./phase-a-supabase-rebuild.md) | All 9 verification checks green |

If any row fails, fix it before starting. The backend must be healthy against
the **new** Supabase (Phase A) for the baseline to mean anything.

## Step 1 — Capture baseline (vector still on)

Run the eval harness against the current vector-enabled stack. This is what
Phase B must not break.

```bash
python tests/eval/run_eval.py \
  --output baseline.json \
  --base-url http://localhost:8000
```

Expected duration: **3–5 minutes** for ~30 queries.

Inspect the summary at the end:

```bash
python tests/eval/run_eval.py --summary baseline.json
```

| Metric | Pass criterion |
|--------|----------------|
| Error rate | < 10% |
| Mean entity recall | Note value as `BASELINE_ENTITY_RECALL` |
| Mean citation precision | Note value as `BASELINE_CITATION_PRECISION` |
| p95 latency | Note value as `BASELINE_P95_MS` |

If error rate ≥ 10%, the backend is broken. Stop. Fix backend. Re-run baseline.
Do not move to Step 2 with a noisy baseline.

## Step 2 — Deploy the vectorless branch

```bash
git checkout phase-b/vectorless-cutover
git pull
git log --oneline -10   # confirm the VectorStrategy-deletion commits are there
```

Push to production:

```bash
git push origin phase-b/vectorless-cutover:main
```

On the production host (currently Railway — Phase C moves this):

```bash
# Railway auto-redeploys on push to main; wait ~3 min then:
curl https://free-will.app/api/health
```

Expect `200 OK`. If `502`, see [`incident-playbook.md`](./incident-playbook.md)
"Symptom: free-will.app returns 502".

Smoke test locally too — restart your local backend on the same branch:

```bash
docker compose -f deploy/docker-compose.yml up -d --build backend
curl http://localhost:8000/api/health
```

## Step 3 — Re-capture against vectorless

```bash
python tests/eval/run_eval.py \
  --output vectorless.json \
  --base-url https://free-will.app
```

Same ~30 queries, same harness, against production with the vectorless branch
live.

## Step 4 — Compare

```bash
python tests/eval/run_eval.py --compare baseline.json vectorless.json
```

The compare output is a table per query plus aggregates. The acceptance gate:

| Acceptance criterion | Threshold |
|----------------------|-----------|
| Aggregate `entity_recall` delta | ≥ **-0.05** (i.e. at most 5 pts worse) |
| Worst single-query `entity_recall` delta | ≥ **-0.30** (no query may collapse) |
| Aggregate `citation_precision` delta | ≥ **-0.05** |
| p95 latency multiplier | ≤ **1.5×** baseline |
| Error rate | ≤ baseline + 2 pts |

**Continue if all five pass. Otherwise tune or rollback.**

### Tuning loop (if a query regresses)

Inspect the per-query diff. Common patterns:

| Symptom in diff | Tune |
|-----------------|------|
| Single Greek query misses lemma variants | Add the term to the lemma-expansion few-shot examples in `services/lemma_expansion.py` |
| Author-specific query returns wrong work | Confirm `work_tree_indices` is populated for that work; see [`incident-playbook.md`](./incident-playbook.md) |
| Multi-hop concept query returns zero | Increase `TreeIndexService.max_depth` from 2 to 3 |
| Latency blow-up on long queries | Cap `SQLStrategy.max_lemmas` to 12 |

Re-run **only the failing queries**, not the whole suite:

```bash
python tests/eval/run_eval.py \
  --queries tests/eval/queries/failed-001.yaml,tests/eval/queries/failed-007.yaml \
  --output vectorless-iter2.json \
  --base-url https://free-will.app
```

If the third iteration still fails, rollback.

## Step 5 — Confirm

Once aggregate metrics pass, lock the result:

```bash
mv vectorless.json tests/eval/results/$(date +%Y%m%d)-vectorless-pass.json
git add tests/eval/results/
git -c commit.gpgsign=true commit -m "test(eval): vectorless cutover pass at $(date +%Y-%m-%d)"
```

Set a calendar reminder: **+7 days** before any Qdrant Cloud decommission.

## Rollback

If Step 4 acceptance fails after tuning, or if production error rate spikes
post-deploy:

```bash
git revert <hash-of-vectorstrategy-deletion>..<hash-of-qdrant-removal>
git push origin main
```

Each Phase B deletion was its own commit; revert in reverse order. Partial
rollback is allowed (keep lemma expansion, restore only `VectorStrategy`).

**Qdrant Cloud cluster stays running** until Phase B is verified stable for
1 week. Only after the 7-day soak do you decommission it. Until then, the
rollback path is live.

## Verification — final

| Check | Command | Expected |
|-------|---------|----------|
| No qdrant imports in Python | `grep -rn "qdrant" --include="*.py" .` | Zero hits |
| No QDRANT env vars referenced | `grep -rn "QDRANT" .env.example` | Zero hits |
| docker-compose has no qdrant service | `grep -c "qdrant:" deploy/docker-compose.yml` | `0` |
| 5 spot-check queries return grounded answers | Manual via UI | All 5 cite real passages |
| Aggregate metrics pass | Step 4 | Yes |

Phase B is done. Open Phase C: [`phase-c-cutover.md`](./phase-c-cutover.md).
