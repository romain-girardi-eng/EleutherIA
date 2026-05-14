# EleutherIA → the platform migration runbooks

Operator-facing companions to the design spec at
[`../plans/2026-05-14-migration-design.md`](../plans/2026-05-14-migration-design.md).
The spec answers *why*; these runbooks answer *how, exactly, step by step, with
checkpoints and rollback*.

## Execution order

| # | Phase | Runbook | Notes |
|---|-------|---------|-------|
| 0 | Python 3.14 upgrade | See [Phase 0 verification](./migration-master-runbook.md#phase-0-verification-checklist) in the master runbook | Already executed 2026-05-14; verify only |
| A | Supabase rebuild | [`phase-a-supabase-rebuild.md`](./phase-a-supabase-rebuild.md) | Fresh Supabase project + idempotent bootstrap |
| B | Vectorless cutover | [`phase-b-vectorless-cutover.md`](./phase-b-vectorless-cutover.md) | Delete Qdrant; eval-gated |
| C | the platform hosting | [`phase-c-cutover.md`](./phase-c-cutover.md) | Compose-include, tunnel, DNS swap |
| D | Temporal rollout | [`phase-d-rollout.md`](./phase-d-rollout.md) | Ingestion workflows |
| — | Incidents | [`incident-playbook.md`](./incident-playbook.md) | Symptom → recovery |

## Master runbook

[`migration-master-runbook.md`](./migration-master-runbook.md) orchestrates the
whole migration: preflight inventory, phase ordering, go/no-go gates,
end-to-end rollback. Read it once before starting Phase A; consult it between
phases.
