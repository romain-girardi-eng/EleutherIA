"""ScaifeIngestionWorkflow — Temporal-native replacement for the manual
two-script pipeline (`fetch_scaife_work.py` + `ingest_scaife_work.py`).

The workflow drives three activities in sequence:

1. `scaife_fetch` — calls the Scaife CTS API, returns the raw payload as a
   JSON-friendly dict. Aggressive retries (5 attempts, 10s → 5m backoff)
   because Perseus' API is occasionally flaky.
2. `scaife_parse_and_insert` — parses the payload, idempotently inserts
   into `ancient_works` + `passages`. Heartbeats every 100 passages.
3. `scaife_link_to_kg` — upserts the `kg_nodes` work entry and the
   `authored_by` edge if a person node was supplied.

Recommended workflow id format:
    scaife-ingestion-<sanitized-cts-urn>

so duplicate ingestions for the same work surface as Temporal id-reuse
collisions rather than silent double-writes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta
from typing import Any

from temporalio import workflow
from temporalio.common import RetryPolicy

# Activity names are referenced by string so the workflow module stays
# importable under Temporal's sandbox without pulling psycopg2/urllib.
SCAIFE_FETCH_ACTIVITY = "scaife_fetch"
SCAIFE_PARSE_AND_INSERT_ACTIVITY = "scaife_parse_and_insert"
SCAIFE_LINK_TO_KG_ACTIVITY = "scaife_link_to_kg"


@dataclass
class ScaifeIngestionInput:
    """Inputs for `ScaifeIngestionWorkflow`.

    `cts_urn` is the edition-level URN passed straight to Scaife (e.g.
    `urn:cts:greekLit:tlg0085.tlg002.opp-grc4`). `canonical_id` defaults
    to the work-group URN — the URN minus the trailing edition segment —
    but callers can override it when the edition differs from the
    canonical identifier already in `ancient_works`.
    """

    cts_urn: str
    canonical_id: str | None = None
    title: str = ""
    author: str = ""
    language: str = "grc"
    period: str = ""
    school: str | None = None
    ref_prefix: str = ""
    level: int = 1
    work_label: str | None = None
    work_node_id: str = ""
    author_node_id: str | None = None
    overwrite: bool = False
    source_policy: str = "scaife"
    fallback_sources: list[str] = field(default_factory=list)
    source_options: dict[str, Any] = field(default_factory=dict)


@dataclass
class ScaifeFetchActivityInput:
    cts_urn: str
    language: str
    ref_prefix: str
    level: int
    source_policy: str = "scaife"
    fallback_sources: list[str] = field(default_factory=list)
    source_options: dict[str, Any] = field(default_factory=dict)


@dataclass
class ScaifeParseAndInsertActivityInput:
    payload: dict[str, Any]
    canonical_id: str
    title: str
    author: str
    language: str
    period: str
    school: str | None
    work_node_id: str
    author_node_id: str | None
    overwrite: bool


@dataclass
class ScaifeParseAndInsertActivityResult:
    work_id: str
    inserted_passages: int
    skipped_existing: bool


@dataclass
class ScaifeLinkToKGActivityInput:
    work_node_id: str
    work_id: str
    canonical_id: str
    title: str
    author: str
    language: str
    period: str
    author_node_id: str | None
    source: str | None = None
    source_url: str | None = None


@dataclass
class ScaifeLinkToKGActivityResult:
    work_node_id: str
    created_work_node: bool
    edges_added: int


@dataclass
class ScaifeIngestionResult:
    """Final workflow output."""

    work_node_id: str
    work_id: str
    passage_count: int
    kg_edges_added: int
    skipped_existing: bool = False
    errors_during_fetch: int = 0
    source_name: str = "scaife_cts"


def _derive_canonical_id(cts_urn: str) -> str:
    """The work-group URN is the edition URN minus the trailing edition
    segment (e.g. `tlg0085.tlg002.opp-grc4` → `tlg0085.tlg002`)."""
    if ":" not in cts_urn:
        return cts_urn
    prefix, last = cts_urn.rsplit(":", 1)
    parts = last.split(".")
    if len(parts) <= 2:
        return cts_urn
    return f"{prefix}:{'.'.join(parts[:2])}"


@workflow.defn
class ScaifeIngestionWorkflow:
    """Fetch a work from Scaife and persist it into Postgres + the KG.

    The three activities are sequenced because each depends on the
    previous one's output. The workflow short-circuits if the work
    already exists in `ancient_works` and `overwrite` is False.
    """

    @workflow.run
    async def run(self, params: ScaifeIngestionInput) -> ScaifeIngestionResult:
        canonical_id = params.canonical_id or _derive_canonical_id(params.cts_urn)
        workflow.logger.info(
            f"ScaifeIngestionWorkflow: cts_urn={params.cts_urn} "
            f"canonical_id={canonical_id} overwrite={params.overwrite}"
        )

        fetch_input = ScaifeFetchActivityInput(
            cts_urn=params.cts_urn,
            language=params.language,
            ref_prefix=params.ref_prefix,
            level=params.level,
            source_policy=params.source_policy,
            fallback_sources=params.fallback_sources,
            source_options=params.source_options,
        )
        payload: dict[str, Any] = await workflow.execute_activity(
            SCAIFE_FETCH_ACTIVITY,
            args=[fetch_input],
            start_to_close_timeout=timedelta(minutes=10),
            heartbeat_timeout=timedelta(minutes=2),
            retry_policy=RetryPolicy(
                maximum_attempts=5,
                initial_interval=timedelta(seconds=10),
                backoff_coefficient=2.0,
                maximum_interval=timedelta(minutes=5),
            ),
        )

        errors_during_fetch = int(payload.get("errors", 0))
        source_name = str(payload.get("source_name") or "scaife_cts")

        ingest_input = ScaifeParseAndInsertActivityInput(
            payload=payload,
            canonical_id=canonical_id,
            title=params.title,
            author=params.author,
            language=params.language,
            period=params.period,
            school=params.school,
            work_node_id=params.work_node_id,
            author_node_id=params.author_node_id,
            overwrite=params.overwrite,
        )
        ingest: ScaifeParseAndInsertActivityResult = await workflow.execute_activity(
            SCAIFE_PARSE_AND_INSERT_ACTIVITY,
            args=[ingest_input],
            start_to_close_timeout=timedelta(minutes=30),
            heartbeat_timeout=timedelta(minutes=2),
            retry_policy=RetryPolicy(
                maximum_attempts=3,
                initial_interval=timedelta(seconds=10),
                backoff_coefficient=2.0,
                maximum_interval=timedelta(minutes=2),
            ),
        )

        # Short-circuit if the work already existed and overwrite was off:
        # skip the KG-link step entirely, since the work node must already
        # exist (the ingest activity refused to write anything).
        if ingest.skipped_existing:
            workflow.logger.info(
                f"ScaifeIngestionWorkflow: work already ingested, "
                f"work_id={ingest.work_id} — skipping KG link"
            )
            return ScaifeIngestionResult(
                work_node_id=params.work_node_id,
                work_id=ingest.work_id,
                passage_count=0,
                kg_edges_added=0,
                skipped_existing=True,
                errors_during_fetch=errors_during_fetch,
                source_name=source_name,
            )

        link_input = ScaifeLinkToKGActivityInput(
            work_node_id=params.work_node_id,
            work_id=ingest.work_id,
            canonical_id=canonical_id,
            title=params.title,
            author=params.author,
            language=params.language,
            period=params.period,
            author_node_id=params.author_node_id,
            source=source_name,
            source_url=payload.get("source_url"),
        )
        link: ScaifeLinkToKGActivityResult = await workflow.execute_activity(
            SCAIFE_LINK_TO_KG_ACTIVITY,
            args=[link_input],
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=RetryPolicy(
                maximum_attempts=3,
                initial_interval=timedelta(seconds=5),
                backoff_coefficient=2.0,
                maximum_interval=timedelta(minutes=1),
            ),
        )

        return ScaifeIngestionResult(
            work_node_id=link.work_node_id or params.work_node_id,
            work_id=ingest.work_id,
            passage_count=ingest.inserted_passages,
            kg_edges_added=link.edges_added,
            skipped_existing=False,
            errors_during_fetch=errors_during_fetch,
            source_name=source_name,
        )


# Re-export field for downstream typing tools; harmless at runtime.
_ = field
