"""Tests for `KGReindexWorkflow` using `temporalio.testing`.

Stubs replace both activities so the workflow runs end-to-end without
Postgres. The stubs record which work ids each activity was called with
so we can assert on the chunked-parallel dispatch and on force-vs-skip
semantics.
"""

from __future__ import annotations

import uuid
from typing import Any

import pytest
from temporalio import activity
from temporalio.client import Client
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Worker

from eleutheria_worker.workflows.kg_reindex import (
    KGReindexInput,
    KGReindexWorkflow,
    ListWorksToReindexActivityInput,
    ReindexWorkTreeActivityInput,
    ReindexWorkTreeActivityResult,
)

# ---------------------------------------------------------------------------
# Stub state
# ---------------------------------------------------------------------------


class _State:
    """Configurable stub state for each test."""

    all_works: list[str] = []
    stale_works: list[str] = []
    reindexed: list[str] = []
    passages_per_work: int = 50
    empty_works: set[str] = set()


STATE = _State()


def _reset(**overrides: Any) -> None:
    STATE.all_works = []
    STATE.stale_works = []
    STATE.reindexed = []
    STATE.passages_per_work = 50
    STATE.empty_works = set()
    for key, value in overrides.items():
        setattr(STATE, key, value)


@activity.defn(name="list_works_to_reindex")
async def stub_list_works_to_reindex(
    params: ListWorksToReindexActivityInput,
) -> list[str]:
    # `work_ids=None` → all works; `force` returns the full set
    if params.work_ids is None:
        if params.force:
            return list(STATE.all_works)
        return list(STATE.stale_works)
    if params.force:
        return list(params.work_ids)
    requested = set(params.work_ids)
    return [w for w in STATE.stale_works if w in requested]


@activity.defn(name="reindex_work_tree")
async def stub_reindex_work_tree(
    params: ReindexWorkTreeActivityInput,
) -> ReindexWorkTreeActivityResult:
    STATE.reindexed.append(params.work_id)
    if params.work_id in STATE.empty_works:
        return ReindexWorkTreeActivityResult(
            work_id=params.work_id,
            passage_count=0,
            was_indexed=False,
        )
    return ReindexWorkTreeActivityResult(
        work_id=params.work_id,
        passage_count=STATE.passages_per_work,
        was_indexed=True,
    )


ALL_STUBS = [stub_list_works_to_reindex, stub_reindex_work_tree]


async def _run(
    client: Client,
    task_queue: str,
    params: KGReindexInput,
):
    return await client.execute_workflow(
        KGReindexWorkflow.run,
        params,
        id=f"kg-reindex-test-{uuid.uuid4()}",
        task_queue=task_queue,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_workflow_reindexes_all_works() -> None:
    _reset(
        all_works=[f"work_{i}" for i in range(25)],
        stale_works=[f"work_{i}" for i in range(25)],
    )
    async with await WorkflowEnvironment.start_time_skipping() as env:
        task_queue = "eleutheria-test"
        async with Worker(
            env.client,
            task_queue=task_queue,
            workflows=[KGReindexWorkflow],
            activities=ALL_STUBS,
        ):
            result = await _run(env.client, task_queue, KGReindexInput())

    assert sorted(result.reindexed_work_ids) == sorted(STATE.all_works)
    assert result.skipped_work_ids == []
    assert result.total_passages_indexed == 25 * STATE.passages_per_work
    # Every work passed through the reindex activity exactly once.
    assert sorted(STATE.reindexed) == sorted(STATE.all_works)


@pytest.mark.asyncio
async def test_workflow_targets_single_work() -> None:
    _reset(
        all_works=["work_a", "work_b", "work_c"],
        stale_works=["work_a", "work_b", "work_c"],
    )
    async with await WorkflowEnvironment.start_time_skipping() as env:
        task_queue = "eleutheria-test"
        async with Worker(
            env.client,
            task_queue=task_queue,
            workflows=[KGReindexWorkflow],
            activities=ALL_STUBS,
        ):
            result = await _run(
                env.client,
                task_queue,
                KGReindexInput(work_ids=["work_b"]),
            )

    assert result.reindexed_work_ids == ["work_b"]
    assert STATE.reindexed == ["work_b"]
    assert result.total_passages_indexed == STATE.passages_per_work


@pytest.mark.asyncio
async def test_workflow_force_includes_unchanged_works() -> None:
    # No works are "stale", but `force=True` should reindex everything anyway.
    _reset(
        all_works=["work_a", "work_b"],
        stale_works=[],
    )
    async with await WorkflowEnvironment.start_time_skipping() as env:
        task_queue = "eleutheria-test"
        async with Worker(
            env.client,
            task_queue=task_queue,
            workflows=[KGReindexWorkflow],
            activities=ALL_STUBS,
        ):
            result = await _run(env.client, task_queue, KGReindexInput(force=True))

    assert sorted(result.reindexed_work_ids) == ["work_a", "work_b"]
    assert sorted(STATE.reindexed) == ["work_a", "work_b"]


@pytest.mark.asyncio
async def test_workflow_skips_when_nothing_stale() -> None:
    _reset(
        all_works=["work_a", "work_b"],
        stale_works=[],
    )
    async with await WorkflowEnvironment.start_time_skipping() as env:
        task_queue = "eleutheria-test"
        async with Worker(
            env.client,
            task_queue=task_queue,
            workflows=[KGReindexWorkflow],
            activities=ALL_STUBS,
        ):
            result = await _run(env.client, task_queue, KGReindexInput(force=False))

    assert result.reindexed_work_ids == []
    assert result.skipped_work_ids == []
    assert result.total_passages_indexed == 0
    assert STATE.reindexed == []


@pytest.mark.asyncio
async def test_workflow_reports_skipped_when_work_has_no_passages() -> None:
    _reset(
        all_works=["work_a", "work_empty"],
        stale_works=["work_a", "work_empty"],
        empty_works={"work_empty"},
    )
    async with await WorkflowEnvironment.start_time_skipping() as env:
        task_queue = "eleutheria-test"
        async with Worker(
            env.client,
            task_queue=task_queue,
            workflows=[KGReindexWorkflow],
            activities=ALL_STUBS,
        ):
            result = await _run(env.client, task_queue, KGReindexInput())

    assert result.reindexed_work_ids == ["work_a"]
    assert result.skipped_work_ids == ["work_empty"]
    assert result.total_passages_indexed == STATE.passages_per_work
