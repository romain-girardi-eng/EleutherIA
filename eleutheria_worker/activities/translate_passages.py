"""Activity implementations for `BatchTranslateWorkflow`.

Two activities live here:

- `list_passages_for_priority` — resolves a priority tier ("P0"…"P3") into a
  list of `kg_node` ids that still need an `_en` sibling.
- `translate_passage_batch` — loads the original-language text for a chunk of
  node ids, calls Gemini through the shared translation service, heartbeats
  between sub-batches, and returns the resulting translations plus any
  passages the model failed to produce.

Both activities reuse `eleutheria_database.services.translation` so the CLI
script and the Temporal worker share a single implementation.
"""

from __future__ import annotations

import asyncio
import os
from collections.abc import Sequence

from eleutheria_database.services.translation import (
    PRIORITY_TIERS,
    PassageToTranslate,
    batch_passages,
    get_api_key_from_env,
    translate_batch,
)
from temporalio import activity

from eleutheria_worker.workflows.batch_translate import (
    BatchTranslateActivityInput,
    BatchTranslateActivityResult,
)

SCHEMA = "free_will"


def _get_db_url() -> str:
    url = os.environ.get("DATABASE_URL", "")
    if not url:
        raise RuntimeError("DATABASE_URL is not set in the activity environment")
    return url


def _fetch_passages_by_node_ids(node_ids: Sequence[str]) -> list[PassageToTranslate]:
    """Fetch original-language passages by node_id from the KG.

    psycopg2 is used (matching the existing CLI script's transport) and the
    call is intentionally synchronous — the activity wraps it in a thread so
    the worker event loop stays responsive.
    """
    if not node_ids:
        return []

    import psycopg2  # local import keeps activity module importable without psycopg2

    conn = psycopg2.connect(_get_db_url())
    try:
        cur = conn.cursor()
        cur.execute(f"SET search_path TO {SCHEMA}")
        cur.execute(
            """
            SELECT n.node_id,
                   n.description,
                   n.metadata->>'language' AS lang,
                   n.metadata->>'author' AS author,
                   n.metadata->>'work_title' AS title,
                   n.metadata->>'canonical_ref' AS ref
            FROM kg_nodes n
            WHERE n.node_id = ANY(%s)
            """,
            (list(node_ids),),
        )
        rows = cur.fetchall()
    finally:
        conn.close()

    return [
        PassageToTranslate(
            node_id=r[0],
            text=r[1] or "",
            language=r[2] or "unknown",
            author=r[3] or "",
            title=r[4] or "",
            ref=r[5] or "",
        )
        for r in rows
    ]


def _list_priority_passages(priority: str) -> list[str]:
    """Return passage node_ids belonging to a priority tier that lack `_en`."""
    import psycopg2

    tiers = PRIORITY_TIERS.get(priority)
    if not tiers:
        raise ValueError(f"Unknown priority tier '{priority}'")

    conn = psycopg2.connect(_get_db_url())
    try:
        cur = conn.cursor()
        cur.execute(f"SET search_path TO {SCHEMA}")

        like_clauses: list[str] = []
        params: list[str] = []
        for t in tiers:
            like_clauses.append("n.metadata->>'work_canonical_id' LIKE %s")
            params.append(t + "%")

        cur.execute(
            f"""
            SELECT n.node_id
            FROM kg_nodes n
            WHERE n.type = 'passage'
              AND n.node_id NOT LIKE '%%\\_en'
              AND NOT EXISTS (
                  SELECT 1 FROM kg_nodes en
                  WHERE en.node_id = n.node_id || '_en'
              )
              AND ({" OR ".join(like_clauses)})
            ORDER BY n.metadata->>'work_canonical_id', n.node_id
            """,
            tuple(params),
        )
        rows = cur.fetchall()
    finally:
        conn.close()

    return [r[0] for r in rows]


@activity.defn(name="list_passages_for_priority")
async def list_passages_for_priority(priority: str) -> list[str]:
    """Resolve a priority tier into the list of node_ids needing translation."""
    activity.logger.info(f"list_passages_for_priority: {priority}")
    return await asyncio.to_thread(_list_priority_passages, priority)


@activity.defn(name="translate_passage_batch")
async def translate_passage_batch(
    params: BatchTranslateActivityInput,
) -> BatchTranslateActivityResult:
    """Translate one chunk of passages and return the merged results.

    The chunk may exceed Gemini's per-call character budget, so we re-batch
    via `batch_passages` and heartbeat between sub-batches.
    """
    activity.logger.info(
        f"translate_passage_batch: {len(params.node_ids)} passages, model={params.model}"
    )
    if not params.node_ids:
        return BatchTranslateActivityResult(translations={}, failed_node_ids=[])

    api_key = await asyncio.to_thread(get_api_key_from_env)
    passages = await asyncio.to_thread(_fetch_passages_by_node_ids, params.node_ids)

    fetched_ids = {p.node_id for p in passages}
    missing_input = [nid for nid in params.node_ids if nid not in fetched_ids]
    if missing_input:
        activity.logger.warning(
            f"translate_passage_batch: {len(missing_input)} requested node_ids not "
            "found in kg_nodes (already translated or never imported)"
        )

    sub_batches = batch_passages(passages)
    translations: dict[str, str] = {}
    failed: list[str] = list(missing_input)

    for idx, sub in enumerate(sub_batches):
        activity.heartbeat({"sub_batch": idx, "total": len(sub_batches)})
        result = await asyncio.to_thread(translate_batch, sub, api_key, params.model)
        for t in result.translations:
            translations[t.node_id] = t.translation
        failed.extend(result.failed_node_ids)

    return BatchTranslateActivityResult(
        translations=translations,
        failed_node_ids=failed,
    )
