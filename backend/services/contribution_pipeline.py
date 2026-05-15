"""Synchronous (inline) PDF contribution pipeline.

Mirrors :class:`eleutheria_worker.workflows.process_contribution.ProcessContributionWorkflow`
but runs straight on the asyncio event loop of the caller. Two consumers:

* The upload route uses this as a **fallback** when Temporal is unavailable
  (local dev, the platform cluster outage). The route owns its own retry budget.
* The operator CLI (``database/scripts/process_contribution_cli.py``) uses
  this for manual reruns, e.g. when a previous workflow run failed and we
  want to re-trigger it without paying a Temporal round-trip.

The activity logic lives in
:mod:`eleutheria_worker.activities.contribution_activities`; this module is a
thin orchestrator that wires the same activities together as straight
``await`` calls.
"""

from __future__ import annotations

import logging
from typing import Any

from eleutheria_database.services.db import DatabaseService
from eleutheria_graphrag.services.llm_service import LLMService

# Bound at module level so tests can monkeypatch individual pipeline stages
# (e.g. ``ca.extract_pdf_text``) and have those overrides actually take effect.
from eleutheria_worker.activities import contribution_activities as ca

logger = logging.getLogger(__name__)


async def process_contribution_sync(
    contribution_id: str,
    db: DatabaseService,
    llm: LLMService,
    *,
    model_override: str | None = None,
) -> dict[str, Any]:
    """Run the full pipeline inline (no Temporal).

    Returns a small status dict::

        {
            "status": "ready" | "failed",
            "contribution_id": "...",
            "relevance_score": float | None,
            "proposals": int,
        }

    Any unhandled exception is caught, recorded in ``processing_error`` on
    the contribution row, and rethrown — callers wanting fire-and-forget
    semantics should wrap this in a task.
    """
    logger.info("process_contribution_sync: %s", contribution_id)

    try:
        row = await ca.load_contribution(db, contribution_id)
        await ca.mark_processing(db, contribution_id)

        extracted = await ca.extract_pdf_text(row["pdf_url"])
        relevance = await ca.classify_relevance(extracted, llm)

        if relevance.score < ca.RELEVANCE_THRESHOLD:
            logger.info(
                "process_contribution_sync: %s relevance=%.2f < %.2f — skipping",
                contribution_id,
                relevance.score,
                ca.RELEVANCE_THRESHOLD,
            )
            await ca.persist_low_relevance(
                db,
                contribution_id,
                extracted.structured_metadata,
                relevance,
            )
            return {
                "status": "ready",
                "contribution_id": contribution_id,
                "relevance_score": relevance.score,
                "proposals": 0,
            }

        proposals = await ca.extract_kg_proposals(
            extracted,
            relevance,
            db,
            llm,
            model_override=model_override,
        )
        await ca.persist_proposals(
            db,
            contribution_id,
            extracted.structured_metadata,
            relevance,
            proposals,
        )
        return {
            "status": "ready",
            "contribution_id": contribution_id,
            "relevance_score": relevance.score,
            "proposals": len(proposals),
        }
    except Exception as exc:
        logger.exception("process_contribution_sync failed: %s", contribution_id)
        try:
            await ca.mark_failed(db, contribution_id, str(exc))
        except Exception:  # noqa: BLE001
            logger.exception("Could not mark contribution failed")
        raise


__all__ = ["process_contribution_sync"]
