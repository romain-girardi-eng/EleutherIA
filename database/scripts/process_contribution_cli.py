"""Operator-facing CLI to process a single ``kg_contributions`` row.

Use this for manual reruns when:

* A workflow run failed and you've fixed the underlying issue
* You're testing the pipeline end-to-end on a hand-crafted contribution row
* Temporal is unavailable and you need to push a contribution through

The CLI calls into the same synchronous pipeline that the FastAPI fallback
path uses (``backend.services.contribution_pipeline.process_contribution_sync``)
so behaviour stays identical across reruns.

Usage::

    python -m database.scripts.process_contribution_cli <contribution_id>
    python -m database.scripts.process_contribution_cli <id> --model <model>
    python -m database.scripts.process_contribution_cli <id> --dry-run

``--dry-run`` runs stages 1–3 in memory and prints the result without
touching the contribution row.
"""

from __future__ import annotations

import asyncio
import json
import logging
import sys
from typing import Any

import typer

logger = logging.getLogger(__name__)

app = typer.Typer(
    add_completion=False,
    help="Process a single free_will.kg_contributions row.",
)


async def _run(
    contribution_id: str,
    model_override: str | None,
    dry_run: bool,
) -> dict[str, Any]:
    # Late imports — keep CLI startup snappy and avoid pulling backend deps
    # when the user just asked for --help.
    from backend.services.contribution_pipeline import process_contribution_sync
    from eleutheria_graphrag.services.llm_service import LLMService
    from eleutheria_worker.activities.contribution_activities import (
        RELEVANCE_THRESHOLD,
        classify_relevance,
        extract_kg_proposals,
        extract_pdf_text,
        load_contribution,
    )

    from eleutheria_database.services.db import DatabaseService

    db = DatabaseService()
    llm = LLMService()
    await db.connect()
    try:
        if not dry_run:
            return await process_contribution_sync(
                contribution_id, db, llm, model_override=model_override
            )

        row = await load_contribution(db, contribution_id)
        extracted = await extract_pdf_text(row["pdf_url"])
        relevance = await classify_relevance(extracted, llm)
        if relevance.score < RELEVANCE_THRESHOLD:
            return {
                "dry_run": True,
                "relevance_score": relevance.score,
                "relevance_summary": relevance.summary,
                "proposals": 0,
            }
        proposals = await extract_kg_proposals(
            extracted, relevance, db, llm, model_override=model_override
        )
        return {
            "dry_run": True,
            "relevance_score": relevance.score,
            "relevance_summary": relevance.summary,
            "proposals": [
                {
                    "kind": p.kind,
                    "target_kg_id": p.target_kg_id,
                    "confidence": p.confidence,
                    "payload": p.payload,
                }
                for p in proposals
            ],
        }
    finally:
        await db.close()


@app.command()
def main(
    contribution_id: str = typer.Argument(
        ..., help="UUID of the kg_contributions row to process."
    ),
    model_override: str | None = typer.Option(
        None,
        "--model",
        help="Override the LLM model for stage 3 (e.g. an OpenRouter id).",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Run the pipeline in memory and print results without writing.",
    ),
    verbose: bool = typer.Option(False, "--verbose", help="Verbose logging."),
) -> None:
    """Process one contribution row end-to-end."""
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    try:
        result = asyncio.run(_run(contribution_id, model_override, dry_run))
    except Exception as exc:  # noqa: BLE001
        typer.secho(f"FAILED: {exc}", fg=typer.colors.RED, err=True)
        sys.exit(1)

    typer.echo(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    app()
