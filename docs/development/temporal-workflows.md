# Temporal workflows

EleutherIA dispatches long-running ingestion jobs onto a Temporal
cluster. The worker lives in `eleutheria_worker/`; the FastAPI process holds a
client and dispatches workflows when an API or CLI command asks it to.

## Architecture

```
CLI / FastAPI handler ─► backend/services/temporal.py
                                │
                                │ (gRPC, plain)
                                ▼
                          <temporal-host>:7233
                                │
                                ▼
              eleutheria_worker container
              ├── workflows/  (@workflow.defn)
              └── activities/ (@activity.defn)
                       │
                       ▼
              EleutherIA Supabase + Gemini API
```

The worker is the same Docker image as `eleutheria-api`, started with a
different entrypoint (`python -m eleutheria_worker.main`).

## Task queues

EleutherIA uses two dedicated task queues:

| Task queue | Purpose |
|---|---|
| `eleutheria-default` | General workflows (signals, low-latency dispatches). |
| `eleutheria-ingestion` | Long-running corpus jobs (translation, Scaife fetches, KG rebuilds). |

The worker reads its queue from `TEMPORAL_TASK_QUEUE` (default
`eleutheria-ingestion`). Run two replicas with different env values to cover
both queues.

## Workflow inventory

| Workflow | Status | Notes |
|---|---|---|
| `BatchTranslateWorkflow` | Implemented | Translates KG passage nodes priority-tier-wide; replaces `batch_translate_passages.py --resume`. |
| `ScaifeIngestWorkflow` | Planned (Phase D follow-up) | Wraps `fetch_scaife_work.py` + `ingest_scaife_work.py`. |
| `BootstrapSupabaseWorkflow` | Planned | One-shot, idempotent retry for `bootstrap_supabase.py`. |
| `ReindexTreeWorkflow` | Planned | Refreshes `work_tree_indices` after corpus changes. |

## Running the worker locally

```bash
# 1. Start a local Temporal dev server
temporal server start-dev   # see https://docs.temporal.io/cli

# 2. Run the worker against it
TEMPORAL_HOST=localhost:7233 \
TEMPORAL_TASK_QUEUE=eleutheria-ingestion \
DATABASE_URL=postgresql://... \
GEMINI_API_KEY=... \
python -m eleutheria_worker.main
```

Against a cluster on the shared Docker network:

```bash
TEMPORAL_HOST=<temporal-host>:7233 \
TEMPORAL_TASK_QUEUE=eleutheria-ingestion \
python -m eleutheria_worker.main
```

No TLS, no API key — the cluster sits on a private bridge network.

## Dispatching from the CLI

Add the following to `cli/main.py` (do not commit blindly — verify imports
against the file's current shape):

```python
import asyncio
import os
from uuid import uuid4

import typer

from backend.services.temporal import get_temporal_client
from eleutheria_worker.workflows import BatchTranslateInput, BatchTranslateWorkflow

app = typer.Typer()  # if not already defined


@app.command()
def translate(
    priority: str = typer.Option("P0", help="Priority tier: P0, P1, P2, P3"),
    batch_size: int = typer.Option(5, help="Passages per Temporal activity batch"),
    local: bool = typer.Option(
        False,
        help="Bypass Temporal and run the legacy script directly (offline dev)",
    ),
) -> None:
    """Translate all KG passages in a priority tier to English."""
    if local:
        # Defer to the existing script for offline dev.
        from database.scripts import batch_translate_passages

        batch_translate_passages.main()
        return

    async def _dispatch() -> str:
        client = await get_temporal_client()
        handle = await client.start_workflow(
            BatchTranslateWorkflow.run,
            BatchTranslateInput(priority=priority, batch_size=batch_size),
            id=f"translate-{priority}-{uuid4()}",
            task_queue=os.getenv("TEMPORAL_TASK_QUEUE", "eleutheria-ingestion"),
        )
        result = await handle.result()
        return (
            f"{len(result.translations)} translated, "
            f"{len(result.failed_node_ids)} failed, "
            f"{result.batches_completed} batches"
        )

    typer.echo(asyncio.run(_dispatch()))
```

`get_temporal_client()` lives in `backend/services/temporal.py` and caches the
gRPC channel for the process lifetime.

## Dispatching from a FastAPI handler

```python
from fastapi import APIRouter, Depends
from temporalio.client import Client

from backend.services.temporal import get_temporal_client
from eleutheria_worker.workflows import BatchTranslateInput, BatchTranslateWorkflow

router = APIRouter()


@router.post("/api/admin/translate/{priority}")
async def dispatch_translate(
    priority: str,
    client: Client = Depends(get_temporal_client),
) -> dict:
    handle = await client.start_workflow(
        BatchTranslateWorkflow.run,
        BatchTranslateInput(priority=priority),
        id=f"translate-{priority}-{handle_id()}",
        task_queue="eleutheria-ingestion",
    )
    return {"workflow_id": handle.id, "run_id": handle.run_id}
```

The handler returns immediately; the workflow runs in the background and is
queryable via `temporal workflow show -w <id>` from the CLI.

## Testing pattern

Use `temporalio.testing.WorkflowEnvironment.start_time_skipping()` to spin up
an in-memory cluster and register stub activities:

```python
import pytest
from temporalio import activity
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Worker

from eleutheria_worker.workflows.batch_translate import (
    BatchTranslateActivityInput,
    BatchTranslateActivityResult,
    BatchTranslateInput,
    BatchTranslateWorkflow,
)


@activity.defn(name="translate_passage_batch")
async def fake_translate(params: BatchTranslateActivityInput) -> BatchTranslateActivityResult:
    return BatchTranslateActivityResult(
        translations={nid: f"EN[{nid}]" for nid in params.node_ids},
        failed_node_ids=[],
    )


@pytest.mark.asyncio
async def test_workflow_translates() -> None:
    async with await WorkflowEnvironment.start_time_skipping() as env:
        async with Worker(
            env.client,
            task_queue="test",
            workflows=[BatchTranslateWorkflow],
            activities=[fake_translate],
        ):
            result = await env.client.execute_workflow(
                BatchTranslateWorkflow.run,
                BatchTranslateInput(node_ids=["a", "b"], batch_size=10),
                id="t",
                task_queue="test",
            )
    assert result.translations == {"a": "EN[a]", "b": "EN[b]"}
```

`start_time_skipping()` lets the test fast-forward through Temporal's retry
delays without real waiting.

See `eleutheria_worker/tests/test_batch_translate.py` for the full reference
test set (explicit node lists, priority resolution, failure reporting, empty
input).

## Code layout

```
eleutheria_worker/
├── __init__.py
├── main.py                       # entrypoint — connects, builds Worker, waits for shutdown
├── pyproject.toml                # temporalio + python-dotenv + eleutheria-database
├── workflows/
│   ├── __init__.py
│   └── batch_translate.py        # BatchTranslateWorkflow + I/O dataclasses
├── activities/
│   ├── __init__.py
│   └── translate_passages.py     # list_passages_for_priority + translate_passage_batch
└── tests/
    ├── __init__.py
    └── test_batch_translate.py
```

The activity layer imports
`eleutheria_database.services.translation` (the same module the legacy
`batch_translate_passages.py` script now uses), so there is a single
implementation of the translation prompt, batching rules, and Gemini call.

## Operational notes

- **Retries.** Each batch activity is configured for 3 attempts, exponential
  backoff (initial 10s, max 2m, multiplier 2.0), 5-minute start-to-close
  timeout, and a 24-hour schedule-to-close ceiling that fails the activity
  rather than retrying forever.
- **Heartbeats.** The activity heartbeats once per sub-batch via
  `activity.heartbeat({"sub_batch": idx, "total": total})`. The
  `heartbeat_timeout` is 2 minutes — comfortably longer than one Gemini call.
- **Idempotency.** `BatchTranslateWorkflow` re-queries which nodes still lack
  `_en` before starting (when `priority` is set), so re-running a failed
  workflow naturally resumes — no `--resume` flag needed.
- **Local fallback.** `cli/main.py --local` keeps the ability to run the
  legacy script inline for offline development. The script and the workflow
  share `eleutheria_database.services.translation`, so behavior matches.
- **Quota safety.** Gemini Flash free tier is ~15 RPM. The default
  `batch_size=5` keeps each batch under a minute even with retries; reduce
  further if you start seeing 429s.
