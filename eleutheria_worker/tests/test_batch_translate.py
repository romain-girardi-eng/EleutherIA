"""Tests for `BatchTranslateWorkflow` using `temporalio.testing`.

These tests stand up an in-memory Temporal environment, register stub
activities that bypass Gemini and the database, then run the workflow
end-to-end and assert it dispatched the expected work.
"""

from __future__ import annotations

import uuid

import pytest
from temporalio import activity
from temporalio.client import Client
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Worker

from eleutheria_worker.workflows.batch_translate import (
    BatchTranslateActivityInput,
    BatchTranslateActivityResult,
    BatchTranslateInput,
    BatchTranslateWorkflow,
)


@activity.defn(name="list_passages_for_priority")
async def stub_list_passages_for_priority(priority: str) -> list[str]:
    # Pretend P-test has 7 passages; tests using `node_ids` directly skip this.
    if priority == "P-test":
        return [f"passage_{i:02d}" for i in range(7)]
    return []


@activity.defn(name="translate_passage_batch")
async def stub_translate_passage_batch(
    params: BatchTranslateActivityInput,
) -> BatchTranslateActivityResult:
    # Echo every requested node_id with a deterministic fake translation.
    # Mark the synthetic node `passage_fail` as failed to exercise the
    # failure-collection path.
    translations = {
        nid: f"EN[{nid}]" for nid in params.node_ids if nid != "passage_fail"
    }
    failed = [nid for nid in params.node_ids if nid == "passage_fail"]
    return BatchTranslateActivityResult(
        translations=translations,
        failed_node_ids=failed,
    )


async def _run_workflow(
    client: Client,
    task_queue: str,
    params: BatchTranslateInput,
):
    return await client.execute_workflow(
        BatchTranslateWorkflow.run,
        params,
        id=f"batch-translate-test-{uuid.uuid4()}",
        task_queue=task_queue,
    )


@pytest.mark.asyncio
async def test_workflow_translates_explicit_node_ids() -> None:
    async with await WorkflowEnvironment.start_time_skipping() as env:
        task_queue = "eleutheria-test"
        async with Worker(
            env.client,
            task_queue=task_queue,
            workflows=[BatchTranslateWorkflow],
            activities=[stub_list_passages_for_priority, stub_translate_passage_batch],
        ):
            result = await _run_workflow(
                env.client,
                task_queue,
                BatchTranslateInput(
                    node_ids=["p1", "p2", "p3", "p4", "p5"],
                    batch_size=2,
                ),
            )

    # 5 ids split by batch_size=2 → 3 batches.
    assert result.batches_completed == 3
    assert result.failed_node_ids == []
    assert result.translations == {
        "p1": "EN[p1]",
        "p2": "EN[p2]",
        "p3": "EN[p3]",
        "p4": "EN[p4]",
        "p5": "EN[p5]",
    }


@pytest.mark.asyncio
async def test_workflow_resolves_priority_tier() -> None:
    async with await WorkflowEnvironment.start_time_skipping() as env:
        task_queue = "eleutheria-test"
        async with Worker(
            env.client,
            task_queue=task_queue,
            workflows=[BatchTranslateWorkflow],
            activities=[stub_list_passages_for_priority, stub_translate_passage_batch],
        ):
            result = await _run_workflow(
                env.client,
                task_queue,
                BatchTranslateInput(priority="P-test", batch_size=3),
            )

    # The stub returns 7 ids; batch_size=3 → 3 batches (3+3+1).
    assert result.batches_completed == 3
    assert len(result.translations) == 7
    assert result.failed_node_ids == []
    assert result.translations["passage_00"] == "EN[passage_00]"


@pytest.mark.asyncio
async def test_workflow_reports_failed_node_ids() -> None:
    async with await WorkflowEnvironment.start_time_skipping() as env:
        task_queue = "eleutheria-test"
        async with Worker(
            env.client,
            task_queue=task_queue,
            workflows=[BatchTranslateWorkflow],
            activities=[stub_list_passages_for_priority, stub_translate_passage_batch],
        ):
            result = await _run_workflow(
                env.client,
                task_queue,
                BatchTranslateInput(
                    node_ids=["ok_1", "passage_fail", "ok_2"],
                    batch_size=10,
                ),
            )

    assert result.batches_completed == 1
    assert result.failed_node_ids == ["passage_fail"]
    assert result.translations == {"ok_1": "EN[ok_1]", "ok_2": "EN[ok_2]"}


@pytest.mark.asyncio
async def test_workflow_handles_empty_input() -> None:
    async with await WorkflowEnvironment.start_time_skipping() as env:
        task_queue = "eleutheria-test"
        async with Worker(
            env.client,
            task_queue=task_queue,
            workflows=[BatchTranslateWorkflow],
            activities=[stub_list_passages_for_priority, stub_translate_passage_batch],
        ):
            result = await _run_workflow(
                env.client,
                task_queue,
                BatchTranslateInput(node_ids=[]),
            )

    assert result.batches_completed == 0
    assert result.translations == {}
    assert result.failed_node_ids == []
