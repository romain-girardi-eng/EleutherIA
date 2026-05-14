# eleutheria-worker

Temporal worker for EleutherIA ingestion workflows.

Runs against the platform's Temporal cluster. The package is importable without
Temporal infrastructure running — only `eleutheria_worker.main` actively
connects.

## Workflows

- `BatchTranslateWorkflow` — bulk passage translation via Gemini
- `ScaifeIngestionWorkflow` — fetch + ingest works from Perseus/Scaife
- `KGReindexWorkflow` — rebuild `work_tree_indices` after schema changes

## Activities

Backed by `eleutheria_database` services (`translation`, `scaife`,
`tree_indexer`). Connections are managed per-activity via psycopg2.

## Usage

```bash
eleutheria-worker
```

Reads Temporal config (`TEMPORAL_HOST`, `TEMPORAL_NAMESPACE`, `TEMPORAL_TASK_QUEUE`)
from the environment. See `docs/development/temporal-workflows.md` for the
full operator guide.
