"""Activity implementations for `KGReindexWorkflow`.

Two activities:

- `list_works_to_reindex` — figures out which work ids need a refresh,
  honouring `force=True` and detecting stale indices by comparing the
  recorded `total_passages` against the live `passages` row count.
- `reindex_work_tree` — recomputes the tree for one work and upserts it
  into `work_tree_indices`.

Both activities reuse `eleutheria_database.services.tree_indexer` so the
standalone CLI script and the Temporal worker share a single
implementation. psycopg2 is imported lazily to keep the module
importable without the binary driver present.
"""

from __future__ import annotations

import asyncio
import os

from eleutheria_database.services import tree_indexer
from temporalio import activity

from eleutheria_worker.workflows.kg_reindex import (
    ListWorksToReindexActivityInput,
    ReindexWorkTreeActivityInput,
    ReindexWorkTreeActivityResult,
)


def _get_db_url() -> str:
    url = os.environ.get("DATABASE_URL", "")
    if not url:
        raise RuntimeError("DATABASE_URL is not set in the activity environment")
    return url


def _do_list_works_to_reindex(
    params: ListWorksToReindexActivityInput,
) -> list[str]:
    import psycopg2

    conn = psycopg2.connect(_get_db_url())
    try:
        works = tree_indexer.list_works_to_reindex(
            conn,
            work_ids=params.work_ids,
            force=params.force,
        )
    finally:
        conn.close()
    return [str(w["work_id"]) for w in works]


def _do_reindex_work_tree(
    params: ReindexWorkTreeActivityInput,
) -> ReindexWorkTreeActivityResult:
    import psycopg2

    conn = psycopg2.connect(_get_db_url())
    try:
        passage_count, was_indexed = tree_indexer.reindex_one_work(
            conn,
            params.work_id,
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    return ReindexWorkTreeActivityResult(
        work_id=params.work_id,
        passage_count=passage_count,
        was_indexed=was_indexed,
    )


@activity.defn(name="list_works_to_reindex")
async def list_works_to_reindex(
    params: ListWorksToReindexActivityInput,
) -> list[str]:
    """Return work ids in scope, optionally filtered to stale-only."""
    activity.logger.info(
        f"list_works_to_reindex: force={params.force} "
        f"work_ids={'all' if params.work_ids is None else len(params.work_ids)}"
    )
    return await asyncio.to_thread(_do_list_works_to_reindex, params)


@activity.defn(name="reindex_work_tree")
async def reindex_work_tree(
    params: ReindexWorkTreeActivityInput,
) -> ReindexWorkTreeActivityResult:
    """Recompute one work's tree and upsert into `work_tree_indices`."""
    activity.logger.info(f"reindex_work_tree: work_id={params.work_id}")
    return await asyncio.to_thread(_do_reindex_work_tree, params)
