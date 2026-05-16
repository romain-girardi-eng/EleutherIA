# KG Deploy & Backup — Operations Runbook

**Last reviewed:** 2026-05-16 — by Romain.

This document covers how knowledge-graph state flows between git and the live
the platform Postgres, what backups exist, and how to recover from common incidents.

## TL;DR for the next incident

- **Production data is in the platform Supabase Postgres** (free_will schema). Live
  API: <https://free-will.app>.
- **Git is a daily mirror** of prod (`.github/workflows/kg-snapshot.yml`) — NOT
  the deploy source.
- **To push git → prod**: `scripts/deploy_kg_to_supabase.py` (idempotent,
  upsert-only by default, dry-run by default).
- **Backups** live in `data/kg/snapshots/<date>-<reason>/` (local, untracked).
  Plus annotated git tags `safe-point/<date>-<reason>` push to origin.

## The two flows

```
                     daily 04:00 UTC (currently DISABLED)
                     ┌────────────────────────────────────┐
                     │                                    │
                     ▼                                    │
            ┌────────────────┐                  ┌──────────────────┐
            │  git/main      │                  │  the platform Supabase │
            │  data/kg/*.jsonl                  │  free_will.kg_*  │
            │                │                  │                  │
            └────────┬───────┘                  └──────────────────┘
                     │                                    ▲
                     │   scripts/deploy_kg_to_supabase.py │
                     │   (manual, idempotent)             │
                     └────────────────────────────────────┘
```

### Flow 1: prod → git (snapshot)

- Workflow: `.github/workflows/kg-snapshot.yml`
- Triggers: **manual only** (workflow_dispatch). Cron schedule was DISABLED
  on 2026-05-16 to prevent overwriting unsynced local edits.
- Behavior: fetches via the public API, writes `data/kg/nodes.jsonl` and
  `data/kg/edges.jsonl`, commits as `chore(kg): snapshot <timestamp>`.
- Safety gate: refuses to commit if the snapshot would shrink the KG by
  >10 nodes or >50 edges (the most common symptom of "git is ahead of prod").
  Override via workflow_dispatch input `allow_destructive=true`.

### Flow 2: git → prod (deploy)

- Script: `scripts/deploy_kg_to_supabase.py`
- Not automated — invoked manually from a machine that holds
  `$SUPABASE_DATABASE_URL`.
- Dry-run by default. Use `--apply` to actually write.
- Schema mapping: extra fields on jsonl rows (`description_en`,
  `description_la`, `description_grc`, `description_grc_robinson_with_apparatus`,
  `description_de`, `description_fr`, `confidence`, `needs_evidence`) are
  STASHED into `metadata` jsonb (prod schema is denormalized — single
  `description` column).
- Upsert-only: never deletes prod-only rows. (Rename cleanups in git produce
  orphan rows in prod that this script intentionally leaves alone — must be
  reviewed and deleted manually.)

## How to deploy git state to prod

```bash
cd /Users/romaingirardi/Projects/EleutherIA

# 1. Sanity check git state
git status                                  # working tree should be clean
git log --oneline -5

# 2. Tag a safe-point (recoverable git ref)
git tag -a "safe-point/$(date +%Y-%m-%d)-pre-deploy" \
    -m "Safe point before deploy: $(wc -l < data/kg/nodes.jsonl) nodes, $(wc -l < data/kg/edges.jsonl) edges"
git push origin "safe-point/$(date +%Y-%m-%d)-pre-deploy"

# 3. Dry-run the deploy script (no DB writes)
.venv/bin/python3 scripts/deploy_kg_to_supabase.py --dump-delta /tmp/deploy_delta.json

# 4. Review the delta: nodes-to-upsert, new-by-type, prod-only items.
#    Pay special attention to "prod-only nodes" — these are NOT deleted but
#    should be inspected: are they legitimately orphaned (renamed in git)?
cat /tmp/deploy_delta.json | jq '.summary'
cat /tmp/deploy_delta.json | jq '.nodes_only_in_prod_sample'

# 5. If delta looks correct, apply
export SUPABASE_DATABASE_URL="postgresql://..."   # production connection string
.venv/bin/python3 scripts/deploy_kg_to_supabase.py --apply

# 6. Verify parity post-deploy
.venv/bin/python3 scripts/deploy_kg_to_supabase.py   # rerun dry-run — should show 0/0 to upsert/insert
```

### First-time apply — be conservative

For the first apply after a long divergence, use the limit flags to verify
the transformation pipeline works end-to-end before committing thousands of
rows:

```bash
# Start with 50 nodes + 100 edges, all under a single transaction
.venv/bin/python3 scripts/deploy_kg_to_supabase.py --apply --max-nodes 50 --max-edges 100

# Inspect a sample in the live API
curl -s -H "User-Agent: Mozilla/5.0" \
  "https://free-will.app/api/kg/nodes/<one-id-you-just-pushed>" | jq

# If happy, run the full apply
.venv/bin/python3 scripts/deploy_kg_to_supabase.py --apply
```

## Backups

### Local snapshots

`data/kg/snapshots/<date>-<reason>/{nodes,edges}.jsonl` — the project convention
is to copy `data/kg/*.jsonl` into a dated subdirectory before any large mutation.
Currently 19+ snapshots covering 2026-05-14 through 2026-05-16.

These are LOCAL ONLY (not in git — large files). The snapshot dirs are useful
for `git checkout`/diff-style recovery on the same machine. Some are checked
in for specific milestones (e.g. `2026-05-16-pre-5-scholars-b1/` was committed
in `dd788288`).

### Git tags

Annotated, named `safe-point/<date>-<reason>`. Pushed to origin.

```bash
git tag -l 'safe-point*'
git show safe-point/2026-05-16-pre-deploy
```

To recover the KG to a tagged state:

```bash
# Identify the tag
git tag -l 'safe-point*'

# Restore just the jsonl files (preserves all other current work)
git checkout safe-point/2026-05-16-pre-deploy -- data/kg/nodes.jsonl data/kg/edges.jsonl
.venv/bin/python3 scripts/validate_kg_shacl.py    # verify clean
git commit -m "chore(kg): restore from safe-point/2026-05-16-pre-deploy"
```

### GitHub remote

The repo is on GitHub at `romain-girardi-eng/EleutherIA`. Every push to `main`
preserves history; reflogs keep ~90 days of refs locally.

### the platform Supabase backups

Supabase auto-snapshots Postgres daily (point-in-time recovery up to 7 days on
their free tier; longer on paid). Use the Supabase dashboard to restore.

## Integrity audit — what to check periodically

Run this every time you push major KG changes:

```bash
# 1. SHACL invariants pass?
.venv/bin/python3 scripts/validate_kg_shacl.py

# 2. All edges resolve to existing nodes?
.venv/bin/python3 -c "
import json
nodes = {json.loads(l)['id'] for l in open('data/kg/nodes.jsonl')}
orphans = [(e['source'], e['target'], e['relation'])
           for e in (json.loads(l) for l in open('data/kg/edges.jsonl'))
           if e['source'] not in nodes or e['target'] not in nodes]
print(f'Orphan edges: {len(orphans)}')
"

# 3. git vs prod parity (run after deploy)
.venv/bin/python3 scripts/deploy_kg_to_supabase.py
# Look for: "Nodes to upsert: 0  Edges to insert: 0  Prod-only: <previously known orphans>"
```

## Incident log

### 2026-05-16: Snapshot-bot overwrite risk + 403 from the platform API

**Symptom:** Daily kg-snapshot workflow failed at 04:00 UTC with `HTTP 403:
Forbidden` from the platform's API. Investigation revealed that the GH Actions runner
IPs are blocked by the platform's Cloudflare front (User-Agent and/or IP filtering).

Simultaneously discovered that git had ~759 unsynced nodes and ~5,168 unsynced
edges ahead of prod (multiple sessions of local-only work — 5-scholars B1,
primary-source deep dives, Origen ingestions, dedupe merge, etc.). Had the
snapshot succeeded, the destructive diff would have OVERWRITTEN all of it.

**Mitigations applied:**
1. Disabled the daily cron in `kg-snapshot.yml`; manual trigger only.
2. Added a destructive-snapshot safety gate to the workflow (refuses to commit
   if delta would shrink the KG by >10 nodes or >50 edges).
3. Built `scripts/deploy_kg_to_supabase.py` to close the git → prod gap.
4. Tagged `safe-point/2026-05-16-pre-deploy` at HEAD.
5. Audited the 29 prod-only nodes — all confirmed as legitimate rename orphans
   (content present in git under proper IDs). ZERO actual data loss.

**Open issues:**
- Re-enable the daily snapshot cron only after either (a) deploys become
  routine, or (b) the the platform Cloudflare 403 is resolved (likely needs API key
  in `KG_API_BASE` or IP allowlist for GH Actions ranges).
- Prod has 29 orphan node IDs (renamed-in-git) and 503 orphan edges. Decide
  whether to clean them up via a one-time targeted DELETE.

## Quick reference

```
data/kg/nodes.jsonl                      ← git's view of nodes
data/kg/edges.jsonl                      ← git's view of edges
data/kg/snapshots/                       ← local backups (untracked)
scripts/deploy_kg_to_supabase.py         ← git → prod (manual)
scripts/export_kg_snapshot.py            ← prod → git (manual/CI)
scripts/validate_kg_shacl.py             ← integrity gate
.github/workflows/kg-snapshot.yml        ← snapshot CI (cron DISABLED)
```
