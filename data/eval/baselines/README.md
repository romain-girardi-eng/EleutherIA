# GraphRAG eval artifacts

`tests/eval/run_eval.py` writes schema-v2 artifacts. A v2 run is valid only
when it binds the query/gold digest, runner config digest, harness code digest,
Python runtime, git revision/dirty state, and the separate + combined SHA-256
values for passages, nodes, edges, citations, and manifest.

The historical files in `data/eval/` are immutable evidence. In particular,
`baseline-opencode-deep-2026-05-15.json` remains a schema-v1 0/10 HTTP-500
capture. Do not overwrite or silently migrate it. Schema-v1 and schema-v2 runs
are not deterministic-gate comparable.

## Offline retrieval baseline (no key, no service)

```bash
python tests/eval/run_eval.py \
  --runner snapshot-lexical \
  --output data/eval/baselines/eval-v2-$(date +%F)-snapshot-lexical.json

python tests/eval/run_eval.py \
  --runner snapshot-ppr-bidirectional \
  --output data/eval/baselines/eval-v2-$(date +%F)-snapshot-ppr-bi.json
```

These runners never generate prose. Their generation, citation, quote,
publication, token, and cost fields remain `null` / `not_run`, never zero.

## Live frozen-release capture

This command calls the running SSE API with every existing eval query. It sets
`force_refresh=true`, so a baseline measures pipeline work rather than cache
replay. Running it invokes live model providers; do not use it in unit tests.

```bash
PYTHONPATH=graphrag/src:. python tests/eval/run_eval.py \
  --runner live-http \
  --base-url http://localhost:8000 \
  --mode deep \
  --release-id <deployed-release> \
  --model-id <exact-model> \
  --config-id <frozen-config> \
  --output data/eval/baselines/eval-v2-$(date +%F)-<release>.json
```

The declared backend release must use the snapshot whose hashes appear in the
artifact. The harness preserves each safe request, HTTP status, SSE response
body, parsed events, retrieval set, answer, verification metadata, and error.

Every schema-v2 summary includes the operational baseline alongside the
quality gates:

- `summary.retention`: retained/withheld rates overall and by requested mode,
  with withholding-reason counts;
- `summary.operations.stage_latency`: per-stage p50/p95/max latency from
  `stage_complete` frames;
- `summary.operations.estimated_cost_usd`: observed query count, sum,
  p50, mean, and max cost per query.

A missing metric remains unobserved (`null` or an empty stage map); it is
never coerced to a successful zero.

## Deterministic comparison

```bash
python tests/eval/run_eval.py --compare BASELINE.json CANDIDATE.json
```

Comparison exits non-zero when any evaluated dimension fails. It rejects
different query/gold digests or invalid gold identifiers and reports separate decisions for entity, work,
manifestation, passage, complete-evidence, citation, abstention, source
identity, quote, publication, and forbidden-string safety. There is no
composite score.

See `docs/operations/graphrag-eval-runbook.md` for the full capture/review
procedure.
