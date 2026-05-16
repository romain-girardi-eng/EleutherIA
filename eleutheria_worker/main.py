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
    classify_relevance_activity,
    extract_kg_proposals_activity,
    extract_pdf_text_activity,
    list_passages_for_priority,
    list_works_to_reindex,
    mark_failed_activity,
    persist_low_relevance_activity,
    persist_proposals_activity,
    reindex_work_tree,
    scaife_fetch,
    scaife_link_to_kg,
    scaife_parse_and_insert,
    translate_passage_batch,
)
from eleutheria_worker.activities import contribution_activities as _ca
from eleutheria_worker.workflows import (
    BatchTranslateWorkflow,
    KGReindexWorkflow,
    ProcessContributionWorkflow,
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
            ProcessContributionWorkflow,
        ],
        activities=[
            list_passages_for_priority,
            translate_passage_batch,
            scaife_fetch,
            scaife_parse_and_insert,
            scaife_link_to_kg,
            list_works_to_reindex,
            reindex_work_tree,
            extract_pdf_text_activity,
            classify_relevance_activity,
            extract_kg_proposals_activity,
            persist_low_relevance_activity,
            persist_proposals_activity,
            mark_failed_activity,
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

    # Optional override for the proposal-extraction model. The default in
    # ``contribution_activities.PROPOSAL_MODEL`` points at a slug that
    # doesn't exist on Fireworks, so prod sets ELEUTHERIA_PROPOSAL_MODEL
    # to a known-good slug (e.g. ``accounts/fireworks/models/kimi-k2p6``).
    proposal_model = os.getenv("ELEUTHERIA_PROPOSAL_MODEL")
    if proposal_model:
        logger.info(f"Overriding PROPOSAL_MODEL -> {proposal_model}")
        _ca.PROPOSAL_MODEL = proposal_model

    # Kimi K2P6 needs more headroom for its reasoning_content before it
    # emits the tool_call — the activity's hard-coded 2048 leaves the model
    # stuck mid-thought and it falls back to plain content. Monkey-patch
    # ``_call_tool`` to bump max_tokens. Default 8192; opt-out via env=0.
    extractor_max_tokens = int(os.getenv("ELEUTHERIA_EXTRACTOR_MAX_TOKENS", "8192"))
    if extractor_max_tokens > 0:
        logger.info(
            f"Bumping extractor max_tokens -> {extractor_max_tokens} (default 2048)"
        )
        from typing import Any

        async def _call_tool_patched(
            llm: Any,
            messages: list[dict[str, Any]],
            tool: dict[str, Any],
            *,
            model_override: str | None,
        ) -> list[dict[str, Any]]:
            import json as _json

            tool_name = tool["function"]["name"]
            msg = await llm.generate_with_tools(
                messages=messages,
                tools=[tool],
                tool_choice={"type": "function", "function": {"name": tool_name}},
                temperature=0.1,
                max_tokens=extractor_max_tokens,
                model_override=model_override,
            )
            calls = msg.get("tool_calls") or []
            if not calls:
                _ca.logger.warning(
                    "Extractor returned no tool_calls for %s", tool_name
                )
                return []
            raw_args = calls[0].get("function", {}).get("arguments", "{}")
            try:
                args = (
                    _json.loads(raw_args) if isinstance(raw_args, str) else raw_args
                )
            except _json.JSONDecodeError:
                _ca.logger.exception(
                    "Bad JSON in tool_call for %s: %r", tool_name, raw_args
                )
                return []
            proposals = args.get("proposals") or []
            return [p for p in proposals if isinstance(p, dict)]

        _ca._call_tool = _call_tool_patched  # type: ignore[attr-defined]

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
