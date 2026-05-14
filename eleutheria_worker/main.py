"""Entry point for the EleutherIA Temporal worker.

Connects to the platform's Temporal cluster, registers EleutherIA workflows and
activities on the configured task queue, then waits for SIGTERM/SIGINT.

Environment variables:
    TEMPORAL_HOST       (default: temporal:7233)
    TEMPORAL_TASK_QUEUE (default: eleutheria-ingestion)

Run locally with:
    TEMPORAL_HOST=localhost:7233 \
        python -m eleutheria_worker.main
"""

from __future__ import annotations

import asyncio
import logging
import os
import signal
from datetime import timedelta

from temporalio.client import Client
from temporalio.worker import Worker

from eleutheria_worker.activities import (
    list_passages_for_priority,
    list_works_to_reindex,
    reindex_work_tree,
    scaife_fetch,
    scaife_link_to_kg,
    scaife_parse_and_insert,
    translate_passage_batch,
)
from eleutheria_worker.workflows import (
    BatchTranslateWorkflow,
    KGReindexWorkflow,
    ScaifeIngestionWorkflow,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def connect_with_retry(
    address: str,
    max_retries: int = 10,
    delay: float = 2.0,
) -> Client:
    """Connect to Temporal with bounded retry — the platform's cluster sits on a
    private Docker network with no TLS, so a plain `Client.connect` is enough
    once the cluster is reachable."""
    last_exc: Exception | None = None
    for attempt in range(max_retries):
        try:
            return await Client.connect(address)
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            logger.warning(
                f"Temporal connect attempt {attempt + 1}/{max_retries} failed: {exc}"
            )
            if attempt == max_retries - 1:
                break
            await asyncio.sleep(delay)
    raise RuntimeError(f"Could not reach Temporal at {address}") from last_exc


def create_worker(client: Client, task_queue: str) -> Worker:
    """Build the worker with EleutherIA's workflow + activity registry."""
    return Worker(
        client,
        task_queue=task_queue,
        workflows=[
            BatchTranslateWorkflow,
            ScaifeIngestionWorkflow,
            KGReindexWorkflow,
        ],
        activities=[
            list_passages_for_priority,
            translate_passage_batch,
            scaife_fetch,
            scaife_parse_and_insert,
            scaife_link_to_kg,
            list_works_to_reindex,
            reindex_work_tree,
        ],
        graceful_shutdown_timeout=timedelta(seconds=10),
    )


async def main() -> None:
    """Run the worker until SIGTERM/SIGINT."""
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        pass  # dotenv is optional; env is enough in production containers

    temporal_address = os.getenv("TEMPORAL_HOST", "temporal:7233")
    task_queue = os.getenv("TEMPORAL_TASK_QUEUE", "eleutheria-ingestion")

    logger.info(f"Connecting to Temporal at {temporal_address}")
    client = await connect_with_retry(temporal_address)

    logger.info(f"Worker starting on task queue: {task_queue}")
    worker = create_worker(client, task_queue)

    shutdown_event = asyncio.Event()

    def _signal_handler(sig_name: str) -> None:
        logger.info(f"Received {sig_name}, initiating graceful shutdown")
        shutdown_event.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, _signal_handler, sig.name)

    logger.info("Worker started. Waiting for tasks.")
    async with worker:
        await shutdown_event.wait()
    logger.info("Worker stopped.")


if __name__ == "__main__":
    asyncio.run(main())
