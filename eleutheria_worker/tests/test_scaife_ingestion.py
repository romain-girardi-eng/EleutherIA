"""Tests for `ScaifeIngestionWorkflow` using `temporalio.testing`.

Stubs replace the three activities so the workflow runs end-to-end
without Postgres or Perseus connectivity. The stubs track call counts
to assert on retry behaviour and idempotency short-circuits.
"""

from __future__ import annotations

import uuid
from typing import Any

import pytest
from temporalio import activity
from temporalio.client import Client
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Worker

from eleutheria_worker.workflows.scaife_ingestion import (
    ScaifeFetchActivityInput,
    ScaifeIngestionInput,
    ScaifeIngestionWorkflow,
    ScaifeLinkToKGActivityInput,
    ScaifeLinkToKGActivityResult,
    ScaifeParseAndInsertActivityInput,
    ScaifeParseAndInsertActivityResult,
)

# ---------------------------------------------------------------------------
# Stubs
# ---------------------------------------------------------------------------


class _Counters:
    """Shared mutable counters so the test can drive retry behaviour."""

    fetch_calls: int = 0
    fetch_failures_remaining: int = 0
    parse_calls: int = 0
    link_calls: int = 0
    skipped_existing: bool = False
    work_id: str = "00000000-0000-0000-0000-000000000abc"
    inserted_passages: int = 42


COUNTERS = _Counters()


def _reset_counters(**overrides: Any) -> None:
    COUNTERS.fetch_calls = 0
    COUNTERS.fetch_failures_remaining = 0
    COUNTERS.parse_calls = 0
    COUNTERS.link_calls = 0
    COUNTERS.skipped_existing = False
    COUNTERS.work_id = "00000000-0000-0000-0000-000000000abc"
    COUNTERS.inserted_passages = 42
    for key, value in overrides.items():
        setattr(COUNTERS, key, value)


@activity.defn(name="scaife_fetch")
async def stub_scaife_fetch(params: ScaifeFetchActivityInput) -> dict[str, Any]:
    COUNTERS.fetch_calls += 1
    if COUNTERS.fetch_failures_remaining > 0:
        COUNTERS.fetch_failures_remaining -= 1
        raise RuntimeError("simulated Scaife flake")
    return {
        "work_urn": params.cts_urn,
        "language": params.language,
        "ref_prefix": params.ref_prefix,
        "level": params.level,
        "errors": 0,
        "source_name": params.source_policy if params.source_policy != "auto" else "scaife_cts",
        "source_url": "https://example.test/source",
        "sections": [
            {
                "section_n": 1,
                "canonical_ref": "1.1",
                "cts_urn": f"{params.cts_urn}:1.1",
                "text": "Sample passage text.",
                "word_count": 3,
                "char_length": 20,
                "char_ratio": 1.0,
                "language": params.language,
                "source_name": "scaife_cts",
            }
        ],
    }


@activity.defn(name="scaife_parse_and_insert")
async def stub_scaife_parse_and_insert(
    params: ScaifeParseAndInsertActivityInput,
) -> ScaifeParseAndInsertActivityResult:
    COUNTERS.parse_calls += 1
    if COUNTERS.skipped_existing:
        return ScaifeParseAndInsertActivityResult(
            work_id=COUNTERS.work_id,
            inserted_passages=0,
            skipped_existing=True,
        )
    return ScaifeParseAndInsertActivityResult(
        work_id=COUNTERS.work_id,
        inserted_passages=COUNTERS.inserted_passages,
        skipped_existing=False,
    )


@activity.defn(name="scaife_link_to_kg")
async def stub_scaife_link_to_kg(
    params: ScaifeLinkToKGActivityInput,
) -> ScaifeLinkToKGActivityResult:
    COUNTERS.link_calls += 1
    return ScaifeLinkToKGActivityResult(
        work_node_id=params.work_node_id,
        created_work_node=True,
        edges_added=1 if params.author_node_id else 0,
    )


ALL_STUBS = [
    stub_scaife_fetch,
    stub_scaife_parse_and_insert,
    stub_scaife_link_to_kg,
]


async def _run(
    client: Client,
    task_queue: str,
    params: ScaifeIngestionInput,
):
    return await client.execute_workflow(
        ScaifeIngestionWorkflow.run,
        params,
        id=f"scaife-ingestion-test-{uuid.uuid4()}",
        task_queue=task_queue,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_workflow_happy_path() -> None:
    _reset_counters()
    async with await WorkflowEnvironment.start_time_skipping() as env:
        task_queue = "eleutheria-test"
        async with Worker(
            env.client,
            task_queue=task_queue,
            workflows=[ScaifeIngestionWorkflow],
            activities=ALL_STUBS,
        ):
            result = await _run(
                env.client,
                task_queue,
                ScaifeIngestionInput(
                    cts_urn="urn:cts:greekLit:tlg0085.tlg002.opp-grc4",
                    title="Choephoroi",
                    author="Aeschylus",
                    language="grc",
                    period="Classical",
                    work_node_id="work_aeschylus_choephoroi",
                    author_node_id="person_aeschylus",
                ),
            )

    assert COUNTERS.fetch_calls == 1
    assert COUNTERS.parse_calls == 1
    assert COUNTERS.link_calls == 1
    assert result.work_id == COUNTERS.work_id
    assert result.passage_count == COUNTERS.inserted_passages
    assert result.kg_edges_added == 1
    assert result.skipped_existing is False
    assert result.source_name == "scaife"


@pytest.mark.asyncio
async def test_workflow_skips_kg_link_when_existing() -> None:
    _reset_counters(skipped_existing=True)
    async with await WorkflowEnvironment.start_time_skipping() as env:
        task_queue = "eleutheria-test"
        async with Worker(
            env.client,
            task_queue=task_queue,
            workflows=[ScaifeIngestionWorkflow],
            activities=ALL_STUBS,
        ):
            result = await _run(
                env.client,
                task_queue,
                ScaifeIngestionInput(
                    cts_urn="urn:cts:greekLit:tlg0085.tlg002.opp-grc4",
                    title="Choephoroi",
                    author="Aeschylus",
                    language="grc",
                    period="Classical",
                    work_node_id="work_aeschylus_choephoroi",
                    author_node_id="person_aeschylus",
                ),
            )

    assert COUNTERS.fetch_calls == 1
    assert COUNTERS.parse_calls == 1
    assert COUNTERS.link_calls == 0
    assert result.skipped_existing is True
    assert result.passage_count == 0
    assert result.kg_edges_added == 0
    assert result.source_name == "scaife"


@pytest.mark.asyncio
async def test_workflow_retries_failed_fetch() -> None:
    _reset_counters(fetch_failures_remaining=1)
    async with await WorkflowEnvironment.start_time_skipping() as env:
        task_queue = "eleutheria-test"
        async with Worker(
            env.client,
            task_queue=task_queue,
            workflows=[ScaifeIngestionWorkflow],
            activities=ALL_STUBS,
        ):
            result = await _run(
                env.client,
                task_queue,
                ScaifeIngestionInput(
                    cts_urn="urn:cts:greekLit:tlg0085.tlg002.opp-grc4",
                    title="Choephoroi",
                    author="Aeschylus",
                    language="grc",
                    period="Classical",
                    work_node_id="work_aeschylus_choephoroi",
                ),
            )

    # The retry policy gives 5 attempts; one simulated failure → 2 fetch calls
    assert COUNTERS.fetch_calls == 2
    assert COUNTERS.parse_calls == 1
    assert COUNTERS.link_calls == 1
    assert result.passage_count == COUNTERS.inserted_passages


@pytest.mark.asyncio
async def test_workflow_passes_fallback_source_options() -> None:
    _reset_counters()
    captured: dict[str, Any] = {}

    @activity.defn(name="scaife_fetch")
    async def capturing_fetch(params: ScaifeFetchActivityInput) -> dict[str, Any]:
        captured["source_policy"] = params.source_policy
        captured["fallback_sources"] = params.fallback_sources
        captured["source_options"] = params.source_options
        return await stub_scaife_fetch(params)

    async with await WorkflowEnvironment.start_time_skipping() as env:
        task_queue = "eleutheria-test"
        async with Worker(
            env.client,
            task_queue=task_queue,
            workflows=[ScaifeIngestionWorkflow],
            activities=[
                capturing_fetch,
                stub_scaife_parse_and_insert,
                stub_scaife_link_to_kg,
            ],
        ):
            result = await _run(
                env.client,
                task_queue,
                ScaifeIngestionInput(
                    cts_urn="urn:cts:latinLit:phi0474.phi049.perseus-lat1",
                    title="De Fato",
                    author="Cicero",
                    language="lat",
                    period="Roman Republican",
                    work_node_id="work_de_fato_cicero_44bce_b9c4e5d2",
                    source_policy="auto",
                    fallback_sources=["phi"],
                    source_options={"phi": {"author_num": 474, "work_num": 54}},
                ),
            )

    assert captured["source_policy"] == "auto"
    assert captured["fallback_sources"] == ["phi"]
    assert captured["source_options"]["phi"]["work_num"] == 54
    assert result.source_name == "scaife_cts"


@pytest.mark.asyncio
async def test_workflow_derives_canonical_id_from_urn() -> None:
    _reset_counters()
    captured: dict[str, Any] = {}

    @activity.defn(name="scaife_parse_and_insert")
    async def capturing_parse(
        params: ScaifeParseAndInsertActivityInput,
    ) -> ScaifeParseAndInsertActivityResult:
        captured["canonical_id"] = params.canonical_id
        return ScaifeParseAndInsertActivityResult(
            work_id=COUNTERS.work_id,
            inserted_passages=1,
            skipped_existing=False,
        )

    async with await WorkflowEnvironment.start_time_skipping() as env:
        task_queue = "eleutheria-test"
        async with Worker(
            env.client,
            task_queue=task_queue,
            workflows=[ScaifeIngestionWorkflow],
            activities=[
                stub_scaife_fetch,
                capturing_parse,
                stub_scaife_link_to_kg,
            ],
        ):
            await _run(
                env.client,
                task_queue,
                ScaifeIngestionInput(
                    cts_urn="urn:cts:greekLit:tlg0085.tlg002.opp-grc4",
                    title="Choephoroi",
                    author="Aeschylus",
                    language="grc",
                    period="Classical",
                    work_node_id="work_aeschylus_choephoroi",
                ),
            )

    # tlg0085.tlg002.opp-grc4 → tlg0085.tlg002 (drop edition segment)
    assert captured["canonical_id"] == "urn:cts:greekLit:tlg0085.tlg002"
