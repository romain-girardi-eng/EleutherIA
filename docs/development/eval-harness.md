# GraphRAG Evaluation Harness

A lightweight, dependency-free evaluator for the EleutherIA GraphRAG pipeline.
It captures a snapshot of retrieval quality against a curated set of queries so
that regressions can be detected when the pipeline changes (e.g. the vectorless
migration: capture a baseline before deletions, re-run after, diff the two).

The harness lives in `tests/eval/` and is intentionally simple — stdlib +
`httpx` + `pyyaml`. No ragas, no deepeval.

## What it measures

For each of ~30 curated queries (`tests/eval/queries.yaml`), the runner calls
`POST /api/graphrag/query` and records:

- **`entity_recall`** — `|expected ∩ returned| / |expected|`. The returned
  set is the union of `citations[].id` (node-typed), `sources[].node_id`,
  `context_nodes`, `seed_nodes`, and `evidence_map` keys/`node_id`s.
- **`entity_precision`** — `|expected ∩ returned| / |returned|`.
- **`keyword_hit_rate`** — substring matches of `expected_entity_keywords`
  against returned ids + answer text. A robust fallback when exact node IDs
  drift.
- **`work_recall`** — same as entity recall but restricted to `work_*` /
  `sc*` ids vs `expected_works`.
- **`citation_count`**, **`answer_chars`**, **`latency_ms`** per query.
- Aggregates: means of the above, `latency_p50_ms`, `latency_p95_ms`,
  `error_rate`, and per-`query_type` breakdowns.

Queries are tagged by `query_type` (`concept-author`, `school-debate`, `fact`,
`comparison`, `fragment`) and `difficulty` so regressions can be localised.

## Capture a baseline

Start the backend (it must be reachable at the URL you pass), then:

```bash
python tests/eval/run_eval.py --output baseline.json
```

The runner prints per-query progress and a final aggregate block, then writes
the full result document (schema_version, timestamp, base_url, per-query
results, aggregates) to `baseline.json`.

Useful flags:

- `--base-url http://localhost:8000` — point at a remote backend.
- `--filter-type concept-author` — only run one bucket.
- `--limit 5` — first N queries (smoke test).
- `--quiet` — suppress progress lines.

## Compare two runs

After the change (e.g. post-vectorless rewrite), capture a second run and diff:

```bash
python tests/eval/run_eval.py --output vectorless.json
python tests/eval/run_eval.py --compare baseline.json vectorless.json
```

The compare mode prints a per-query side-by-side table (recall, precision,
keyword hit rate, latency, each with delta), an aggregate delta block, and a
by-query-type breakdown. No file is written; redirect stdout if you want one.

## Add a new query

Append an entry to `tests/eval/queries.yaml`:

```yaml
  - id: q031
    query: "..."
    expected_entities:
      - person_xyz_...
      - concept_abc_...
    expected_entity_keywords:
      - xyz
      - abc
    expected_works:
      - work_...
    query_type: concept-author      # one of the five types
    difficulty: medium              # easy | medium | hard
```

Discover real node IDs by either:
- `psql "$DATABASE_URL" -c "SELECT id, label FROM kg_nodes WHERE label ILIKE '%aristotle%';"`
- or grepping `data/kg/nodes.jsonl` if present locally.

Keep `expected_entity_keywords` populated even when you list exact IDs — it is
the fallback when an id is renamed.

## How to interpret the metrics

- **Recall trending down** between baseline and candidate is the most reliable
  regression signal. Pair with the per-query table to see *which* queries lost
  their expected entities.
- **Precision** is noisier: GraphRAG often returns large context windows, so
  precision is naturally low. Use it as a sanity check (a sharp drop suggests
  the pipeline started returning lots of off-topic nodes).
- **Keyword hit rate** is the cheapest "did the answer at least mention the
  right things" signal and is the metric to watch when IDs change shape.
- **Latency p95** spikes often co-occur with retrieval quality drops (e.g. a
  fallback path taking over).
- **Error rate > 0** in either run means investigate that subset before
  trusting the aggregates.

A reasonable post-migration acceptance bar: aggregate `entity_recall_mean`
must not drop by more than 0.05, and no individual query may drop by more
than 0.30 without a documented rationale.

## Pytest integration

The harness ships with a tiny smoke subset for CI:

```bash
pytest tests/eval/ -v --run-eval --eval-limit 3 \
    --eval-base-url http://localhost:8000
```

Without `--run-eval`, only the pure-unit tests (yaml validity, metric maths,
payload parsing) run — they do not touch the network.
