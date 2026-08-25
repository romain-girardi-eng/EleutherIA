# Independent review — current single-API release topology

**Date:** 2026-08-24  
**Target:** `issue_graph_multi_replica_release_atomicity`  
**Verdict:** PASS for `status=adjudicated` on the attested current
single-replica topology; FAIL for any claim that multi-replica cutover is
implemented.

## Evidence reviewed

- `data/audit/2026-08-24_production_single_api_topology.json`;
- `Makefile` exact-SHA production targets;
- `backend/main.py` expected-release health precondition;
- `backend/tests/test_health_release_precondition.py`;
- `tests/test_production_makefile_contract.py`;
- `tests/test_production_topology_attestation.py`;
- `docs/development/staged-deploy.md`;
- `docs/operations/kg-snapshot-release-contract.md`;
- `deploy/README.md`.

## Findings

The versioned, secret-free host capture attests exactly one running
`eleutheria-api` Compose container. `UVICORN_WORKERS` is absent and the Uvicorn
command defaults to one worker. The release runbook refuses a mutable or short
revision, creates a PostgreSQL backup before mutation, builds API/worker images
without recreating them, applies the three migrations, requires a successful
staging dry-run, performs the atomic five-table swap, and only then recreates
the API and worker.

The public cutover checks JSON health (`healthy`, database connected, GraphRAG
ready), compares workspace totals with the exact RC snapshot, and sends eight
`expected_release_id` probes. The API returns 409 for another release and 503
when release identity is unavailable. Rollback rejects a non-40-hex recorded
SHA. Documentation no longer instructs an accidental second swap after the
full deploy.

## Adjudication boundary

The current single-container/single-worker API topology cannot route successive
graph pages across two simultaneously active API generations. PostgreSQL
publication is atomic and client/server release preconditions remain an
independent fail-closed defence.

This is not a multi-replica capability claim. Reopen the issue before any
second API container, second tunnel/load-balancer upstream, independently
reloadable Uvicorn worker, rolling/canary/blue-green deployment, or
multi-process use of `POST /api/kg/reload`. A reopened issue must directly
enumerate candidate replicas, require identical release IDs and totals, shift
traffic atomically, retain rollback replicas, and add a deterministic
multi-replica integration gate.

The Cloudflare tunnel configuration was not inspected. The eight public probes
are a current-topology smoke gate, not proof of future multi-replica atomicity.
