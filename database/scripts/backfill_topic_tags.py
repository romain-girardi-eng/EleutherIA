"""Backfill ``free_will.query_traces.topic_tags`` for existing rows.

Usage (from inside the ``eleutheria-api`` container, where
``DATABASE_URL`` is already exported)::

    python -m database.scripts.backfill_topic_tags

Logic:

1. Select every trace where ``topic_tags`` is empty or NULL.
2. Run :class:`backend.services.topic_tagger.TopicTagger` over each row;
   it both computes and writes the tags.
3. Print ``{trace_id} → {tags}`` so the operator can eyeball the result.

The tagger is idempotent and best-effort: a single bad row never fails
the whole batch.
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys

from backend.services.topic_tagger import TopicTagger

from eleutheria_database.services.db import DatabaseService

logger = logging.getLogger(__name__)


async def _run() -> int:
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("DATABASE_URL is not set", file=sys.stderr)
        return 2

    db = DatabaseService()
    await db.connect()
    try:
        rows = await db.fetch(
            """
            SELECT trace_id
            FROM free_will.query_traces
            WHERE topic_tags = ARRAY[]::text[]
               OR topic_tags IS NULL
            ORDER BY started_at DESC
            """
        )
        tagger = TopicTagger(db)
        print(f"Found {len(rows)} trace(s) without topic_tags")
        for row in rows:
            trace_id = str(row["trace_id"])
            try:
                tags = await tagger.tag_and_persist(trace_id)
            except Exception as exc:  # noqa: BLE001
                print(f"  {trace_id} → ERROR: {exc}")
                continue
            print(f"  {trace_id} → {tags}")
        return 0
    finally:
        await db.close()


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    return asyncio.run(_run())


if __name__ == "__main__":
    sys.exit(main())
