"""KGReindexWorkflow — refresh the `work_tree_indices` cache used by
`TreeIndexService` after the corpus or KG changes.

Two activities:

1. `list_works_to_reindex` — returns the work ids in scope. When
   `work_ids` is None the activity examines every row in
   `ancient_works`; otherwise it filters to the supplied list. With
   `force=False` it also skips works whose recorded `total_passages`
   already matches the current `passages` row count.
2. `reindex_work_tree` — recomputes one work's tree and upserts it
   into `work_tree_indices`.

The reindex step is parallelised in chunks of `CHUNK_SIZE` to keep
Postgres load predictable; within a chunk activities run concurrently
via `asyncio.gather` (Temporal's `workflow.execute_activity` integrates
with `asyncio`, so this is safe inside a workflow).

Recommended workflow id format:
    kg-reindex-<iso-timestamp>  (full reindex)
    kg-reindex-<work-id-list-hash>  (targeted)
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy

LIST_WORKS_TO_REINDEX_ACTIVITY = "list_works_to_reindex"
REINDEX_WORK_TREE_ACTIVITY = "reindex_work_tree"

CHUNK_SIZE = 10


@dataclass
class KGReindexInput:
    """Inputs for `KGReindexWorkflow`.

    `work_ids=None` reindexes every work in `ancient_works`. `force=True`
    rebuilds every targeted work even if its index is up to date.
    """

    work_ids: list[str] | None = None
    force: bool = False


@dataclass
class ListWorksToReindexActivityInput:
    work_ids: list[str] | None
    force: bool


@dataclass
class ReindexWorkTreeActivityInput:
    work_id: str


@dataclass
class ReindexWorkTreeActivityResult:
    work_id: str
    passage_count: int
    was_indexed: bool


@dataclass
class KGReindexResult:
    reindexed_work_ids: list[str] = field(default_factory=list)
    skipped_work_ids: list[str] = field(default_factory=list)
    total_passages_indexed: int = 0


@workflow.defn
class KGReindexWorkflow:
    """Recompute hierarchical tree indices for ancient works.

    Pure Postgres workload — no external APIs, so retries are tight
    (3 attempts, 5s → 1m) and timeouts are short (5m per activity).
    """

    @workflow.run
    async def run(self, params: KGReindexInput) -> KGReindexResult:
        list_input = ListWorksToReindexActivityInput(
            work_ids=params.work_ids,
            force=params.force,
        )
        targets: list[str] = await workflow.execute_activity(
            LIST_WORKS_TO_REINDEX_ACTIVITY,
            args=[list_input],
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=RetryPolicy(
                maximum_attempts=3,
                initial_interval=timedelta(seconds=5),
                backoff_coefficient=2.0,
                maximum_interval=timedelta(minutes=1),
            ),
        )

        if not targets:
            workflow.logger.info("KGReindexWorkflow: nothing to reindex")
            return KGReindexResult()

        workflow.logger.info(
            f"KGReindexWorkflow: reindexing {len(targets)} works "
            f"in chunks of {CHUNK_SIZE}"
        )

        reindexed: list[str] = []
        skipped: list[str] = []
        total_passages = 0

        for chunk_start in range(0, len(targets), CHUNK_SIZE):
            chunk = targets[chunk_start : chunk_start + CHUNK_SIZE]
            workflow.logger.info(
                f"KGReindexWorkflow: chunk {chunk_start // CHUNK_SIZE + 1} "
                f"({len(chunk)} works)"
            )

            results = await asyncio.gather(
                *[
                    workflow.execute_activity(
                        REINDEX_WORK_TREE_ACTIVITY,
                        args=[ReindexWorkTreeActivityInput(work_id=work_id)],
                        start_to_close_timeout=timedelta(minutes=5),
                        retry_policy=RetryPolicy(
                            maximum_attempts=3,
                            initial_interval=timedelta(seconds=5),
                            backoff_coefficient=2.0,
                            maximum_interval=timedelta(minutes=1),
                        ),
                    )
                    for work_id in chunk
                ]
            )

            for res in results:
                if res.was_indexed:
                    reindexed.append(res.work_id)
                    total_passages += res.passage_count
                else:
                    skipped.append(res.work_id)

        return KGReindexResult(
            reindexed_work_ids=reindexed,
            skipped_work_ids=skipped,
            total_passages_indexed=total_passages,
        )
