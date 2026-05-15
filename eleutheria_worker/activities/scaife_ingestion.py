"""Activity implementations for `ScaifeIngestionWorkflow`.

Three activities live here:

- `scaife_fetch` — calls Perseus' Scaife CTS API via the shared
  `eleutheria_database.services.scaife` service and returns the cleaned
  payload as a JSON-friendly dict. Heartbeats after every fetched section.
- `scaife_parse_and_insert` — parses the payload and inserts the work +
  passages into Postgres. Idempotent on `canonical_id` unless
  `overwrite=True`. Heartbeats every 100 inserted passages.
- `scaife_link_to_kg` — upserts the `kg_nodes` work entry plus the
  `authored_by` edge if a person node id was supplied.

All three reuse the synchronous `scaife` service so the standalone
scripts and the worker share a single implementation. psycopg2 is
imported lazily to keep the activity module importable without the
binary driver present.
"""

from __future__ import annotations

import asyncio
import os
from typing import Any

from eleutheria_database.services import scaife
from temporalio import activity

from eleutheria_worker.workflows.scaife_ingestion import (
    ScaifeFetchActivityInput,
    ScaifeLinkToKGActivityInput,
    ScaifeLinkToKGActivityResult,
    ScaifeParseAndInsertActivityInput,
    ScaifeParseAndInsertActivityResult,
)


def _get_db_url() -> str:
    url = os.environ.get("DATABASE_URL", "")
    if not url:
        raise RuntimeError("DATABASE_URL is not set in the activity environment")
    return url


def _do_fetch(params: ScaifeFetchActivityInput) -> dict[str, Any]:
    def progress(idx: int, total: int) -> None:
        # Heartbeating from the worker thread keeps the activity alive on
        # large works (thousands of sections × 0.5s rate-limit each).
        activity.heartbeat({"fetched": idx, "total": total})

    payload = scaife.fetch_work_with_fallbacks(
        work_urn=params.cts_urn,
        language=params.language,
        ref_prefix=params.ref_prefix,
        level=params.level,
        source_policy=params.source_policy,
        fallback_sources=params.fallback_sources,
        source_options=params.source_options,
        progress_callback=progress,
    )
    return scaife.payload_to_dict(payload)


def _do_parse_and_insert(
    params: ScaifeParseAndInsertActivityInput,
) -> ScaifeParseAndInsertActivityResult:
    import psycopg2  # local import keeps module importable without psycopg2

    payload = scaife.payload_from_dict(params.payload)
    meta = scaife.IngestMetadata(
        canonical_id=params.canonical_id,
        title=params.title,
        author=params.author,
        language=params.language,
        period=params.period,
        school=params.school,
        work_node_id=params.work_node_id,
        author_node_id=params.author_node_id,
        overwrite=params.overwrite,
    )

    conn = psycopg2.connect(_get_db_url())
    try:

        def heartbeat(inserted: int, total: int) -> None:
            activity.heartbeat({"inserted": inserted, "total": total})

        result = scaife.parse_and_insert(
            conn,
            payload,
            meta,
            heartbeat_callback=heartbeat,
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    return ScaifeParseAndInsertActivityResult(
        work_id=result.work_id,
        inserted_passages=result.inserted_passages,
        skipped_existing=result.skipped_existing,
    )


def _do_link_to_kg(
    params: ScaifeLinkToKGActivityInput,
) -> ScaifeLinkToKGActivityResult:
    import psycopg2

    meta = scaife.IngestMetadata(
        canonical_id=params.canonical_id,
        title=params.title,
        author=params.author,
        language=params.language,
        period=params.period,
        work_node_id=params.work_node_id,
        author_node_id=params.author_node_id,
        source=params.source,
        source_url=params.source_url,
    )

    conn = psycopg2.connect(_get_db_url())
    try:
        result = scaife.link_to_kg(conn, meta, params.work_id)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    return ScaifeLinkToKGActivityResult(
        work_node_id=result.work_node_id,
        created_work_node=result.created_work_node,
        edges_added=result.edges_added,
    )


@activity.defn(name="scaife_fetch")
async def scaife_fetch(params: ScaifeFetchActivityInput) -> dict[str, Any]:
    """Fetch all sections of a work from Scaife and return a JSON payload."""
    activity.logger.info(f"scaife_fetch: cts_urn={params.cts_urn} level={params.level}")
    return await asyncio.to_thread(_do_fetch, params)


@activity.defn(name="scaife_parse_and_insert")
async def scaife_parse_and_insert(
    params: ScaifeParseAndInsertActivityInput,
) -> ScaifeParseAndInsertActivityResult:
    """Insert fetched payload into `ancient_works` and `passages`."""
    activity.logger.info(
        f"scaife_parse_and_insert: canonical_id={params.canonical_id} "
        f"overwrite={params.overwrite}"
    )
    return await asyncio.to_thread(_do_parse_and_insert, params)


@activity.defn(name="scaife_link_to_kg")
async def scaife_link_to_kg(
    params: ScaifeLinkToKGActivityInput,
) -> ScaifeLinkToKGActivityResult:
    """Create or update the KG work node and (optionally) the authored_by edge."""
    activity.logger.info(
        f"scaife_link_to_kg: work_node_id={params.work_node_id} "
        f"author_node_id={params.author_node_id}"
    )
    return await asyncio.to_thread(_do_link_to_kg, params)
