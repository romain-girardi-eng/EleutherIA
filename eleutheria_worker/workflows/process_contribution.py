"""``ProcessContributionWorkflow`` — Feature 8 (community PDF contributions).

A contribution row is inserted by the upload route in
``free_will.kg_contributions`` and dispatches this workflow. The workflow:

1. Downloads the PDF and extracts structural metadata (60s, 3 retries)
2. Scores free-will relevance with the LLM (90s, 3 retries)
3. If score ≥ 0.4 → extracts KG proposals via 3 tool-calls (240s, 3 retries)
   else → writes the score and short-circuits
4. Persists everything (30s, 3 retries)

Activity I/O is JSON-friendly dicts (see ``_extracted_to_dict`` etc.) so
Temporal payload serialization stays portable. On any failure the workflow's
final ``except`` block marks the contribution row as ``status='failed'`` and
records ``processing_error``.

Workflow id convention: ``process-contribution-<contribution_id>`` so dupe
dispatches collide on Temporal's id-reuse policy.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Any

from temporalio import workflow
from temporalio.common import RetryPolicy
from temporalio.exceptions import ActivityError, ApplicationError

EXTRACT_PDF_ACTIVITY = "extract_pdf_text"
CLASSIFY_RELEVANCE_ACTIVITY = "classify_relevance"
EXTRACT_PROPOSALS_ACTIVITY = "extract_kg_proposals"
PERSIST_LOW_RELEVANCE_ACTIVITY = "persist_low_relevance"
PERSIST_PROPOSALS_ACTIVITY = "persist_proposals"
MARK_FAILED_ACTIVITY = "mark_contribution_failed"

RELEVANCE_THRESHOLD = 0.4


@dataclass
class ProcessContributionResult:
    status: str
    contribution_id: str
    relevance_score: float | None = None
    proposals: int = 0


@workflow.defn
class ProcessContributionWorkflow:
    """Run the full PDF ingestion pipeline for one ``kg_contributions`` row."""

    @workflow.run
    async def run(self, contribution_id: str) -> ProcessContributionResult:
        workflow.logger.info(
            f"ProcessContributionWorkflow: contribution_id={contribution_id}"
        )

        try:
            extracted = await workflow.execute_activity(
                EXTRACT_PDF_ACTIVITY,
                contribution_id,
                start_to_close_timeout=timedelta(seconds=60),
                retry_policy=RetryPolicy(
                    maximum_attempts=3,
                    initial_interval=timedelta(seconds=5),
                    backoff_coefficient=2.0,
                ),
            )

            relevance: dict[str, Any] = await workflow.execute_activity(
                CLASSIFY_RELEVANCE_ACTIVITY,
                extracted,
                start_to_close_timeout=timedelta(seconds=90),
                retry_policy=RetryPolicy(
                    maximum_attempts=3,
                    initial_interval=timedelta(seconds=5),
                    backoff_coefficient=2.0,
                ),
            )

            score = float(relevance.get("score", 0.0))
            if score < RELEVANCE_THRESHOLD:
                workflow.logger.info(
                    f"ProcessContributionWorkflow: relevance={score:.2f} < "
                    f"{RELEVANCE_THRESHOLD} — skipping proposal extraction"
                )
                await workflow.execute_activity(
                    PERSIST_LOW_RELEVANCE_ACTIVITY,
                    args=[contribution_id, extracted, relevance],
                    start_to_close_timeout=timedelta(seconds=30),
                    retry_policy=RetryPolicy(
                        maximum_attempts=3,
                        initial_interval=timedelta(seconds=5),
                        backoff_coefficient=2.0,
                    ),
                )
                return ProcessContributionResult(
                    status="ready",
                    contribution_id=contribution_id,
                    relevance_score=score,
                    proposals=0,
                )

            proposals = await workflow.execute_activity(
                EXTRACT_PROPOSALS_ACTIVITY,
                args=[extracted, relevance],
                start_to_close_timeout=timedelta(seconds=240),
                retry_policy=RetryPolicy(
                    maximum_attempts=3,
                    initial_interval=timedelta(seconds=10),
                    backoff_coefficient=2.0,
                ),
            )

            await workflow.execute_activity(
                PERSIST_PROPOSALS_ACTIVITY,
                args=[contribution_id, extracted, relevance, proposals],
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=RetryPolicy(
                    maximum_attempts=3,
                    initial_interval=timedelta(seconds=5),
                    backoff_coefficient=2.0,
                ),
            )

            return ProcessContributionResult(
                status="ready",
                contribution_id=contribution_id,
                relevance_score=score,
                proposals=len(proposals),
            )

        except ActivityError as exc:
            cause = exc.cause
            message = (
                getattr(cause, "message", None)
                or (str(cause) if cause else "")
                or str(exc)
            )
            workflow.logger.exception(f"ProcessContributionWorkflow failed: {message}")
            # Best-effort failure marker. We never raise from this branch —
            # rethrowing would crash the workflow before persistence runs.
            try:
                await workflow.execute_activity(
                    MARK_FAILED_ACTIVITY,
                    args=[contribution_id, message],
                    start_to_close_timeout=timedelta(seconds=30),
                    retry_policy=RetryPolicy(maximum_attempts=2),
                )
            except Exception:  # noqa: BLE001
                workflow.logger.exception(
                    "ProcessContributionWorkflow: failed to mark contribution failed"
                )
            raise ApplicationError(message, non_retryable=True) from exc
