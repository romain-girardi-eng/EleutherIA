"""BatchTranslateWorkflow — Temporal-native replacement for the manual
`batch_translate_passages.py --resume` loop.

The workflow drives translation of every passage in a given priority tier in
fixed-size sub-batches. Each sub-batch is a single activity invocation:

- 3 attempts per batch, exponential backoff
- 5-minute start-to-close timeout per batch (matches Gemini's 300s urllib
  timeout in the underlying service)
- 24h schedule-to-close ceiling so a stuck workflow eventually fails over to
  the dead-letter queue
- Heartbeat between batches via `workflow.logger.info`; the activity itself
  also heartbeats inside its loop so long single-batch translations don't
  time out
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy

# Activity name is referenced by string so the workflow doesn't need to import
# the activity module at workflow-definition time (Temporal sandbox-safety).
TRANSLATE_BATCH_ACTIVITY = "translate_passage_batch"

DEFAULT_BATCH_SIZE = 5
DEFAULT_MODEL = "gemini-2.5-flash"


@dataclass
class BatchTranslateInput:
    """Inputs for `BatchTranslateWorkflow`.

    Either `priority` or `node_ids` must be supplied. When `node_ids` is given
    the workflow translates exactly that set (useful for retries and tests).
    """

    priority: str | None = None
    node_ids: list[str] = field(default_factory=list)
    batch_size: int = DEFAULT_BATCH_SIZE
    model: str = DEFAULT_MODEL


@dataclass
class BatchTranslateActivityInput:
    """Inputs handed to `translate_passage_batch` for a single batch."""

    node_ids: list[str]
    model: str


@dataclass
class BatchTranslateActivityResult:
    """Activity output: which node_ids translated, which failed."""

    translations: dict[str, str]
    failed_node_ids: list[str]


@dataclass
class BatchTranslateResult:
    """Final workflow output once every batch has been attempted."""

    translations: dict[str, str]
    failed_node_ids: list[str]
    batches_completed: int


@workflow.defn
class BatchTranslateWorkflow:
    """Translate KG passage nodes priority-tier-wide.

    The workflow is intentionally stateless across replays: it asks an
    activity to list candidate node_ids (when a priority tier is given),
    chunks them, and dispatches one activity per chunk. Heartbeats inside the
    activity prevent worker timeouts on long batches.
    """

    @workflow.run
    async def run(self, params: BatchTranslateInput) -> BatchTranslateResult:
        node_ids = list(params.node_ids)
        if not node_ids and params.priority:
            node_ids = await workflow.execute_activity(
                "list_passages_for_priority",
                args=[params.priority],
                start_to_close_timeout=timedelta(minutes=5),
                retry_policy=RetryPolicy(
                    maximum_attempts=3,
                    initial_interval=timedelta(seconds=5),
                    backoff_coefficient=2.0,
                ),
            )

        if not node_ids:
            workflow.logger.info("BatchTranslateWorkflow: nothing to translate")
            return BatchTranslateResult(
                translations={},
                failed_node_ids=[],
                batches_completed=0,
            )

        batch_size = max(1, params.batch_size)
        batches: list[list[str]] = [
            node_ids[i : i + batch_size] for i in range(0, len(node_ids), batch_size)
        ]

        translations: dict[str, str] = {}
        failed: list[str] = []

        for idx, chunk in enumerate(batches):
            workflow.logger.info(
                f"BatchTranslateWorkflow: batch {idx + 1}/{len(batches)} "
                f"({len(chunk)} passages)"
            )
            result: BatchTranslateActivityResult = await workflow.execute_activity(
                TRANSLATE_BATCH_ACTIVITY,
                args=[BatchTranslateActivityInput(node_ids=chunk, model=params.model)],
                start_to_close_timeout=timedelta(minutes=5),
                schedule_to_close_timeout=timedelta(hours=24),
                heartbeat_timeout=timedelta(minutes=2),
                retry_policy=RetryPolicy(
                    maximum_attempts=3,
                    initial_interval=timedelta(seconds=10),
                    backoff_coefficient=2.0,
                    maximum_interval=timedelta(minutes=2),
                ),
            )
            translations.update(result.translations)
            failed.extend(result.failed_node_ids)

        return BatchTranslateResult(
            translations=translations,
            failed_node_ids=failed,
            batches_completed=len(batches),
        )
