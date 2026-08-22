from __future__ import annotations

import json

import pytest

from scripts.apply_2026_08_18_related_citation_types import (
    TARGET_TYPE,
    ApplyBlocked,
    build_plan,
    parse_jsonl_bytes,
    render_citations,
)


def _node(node_id: str, passage_id: str) -> dict:
    return {
        "id": node_id,
        "type": "passage",
        "metadata": {
            "parity_status": "related_not_exact_twin",
            "related_corpus_passage_id": passage_id,
        },
    }


def _plan(nodes: list[dict], citations: list[dict]):
    return build_plan(
        nodes,
        citations,
        expected_count=len(nodes),
        expected_node_ids_sha256=None,
        expected_plan_sha256=None,
        expected_source_rows_sha256=None,
        expected_target_rows_sha256=None,
    )


def test_retype_is_line_local_and_second_pass_is_byte_noop() -> None:
    raw = (
        b'{"confidence":1.0, "citation_type":"snapshot_passage_node",'
        b'"kg_node_id":"passage_a","passage_id":"p1"}\n'
        b'{"citation_type":"primary_source","kg_node_id":"concept_a",'
        b'"passage_id":"p1","confidence":0.8}\n'
    )
    raw_lines, citations = parse_jsonl_bytes(raw, label="fixture")
    nodes = [_node("passage_a", "p1")]

    plan = _plan(nodes, citations)
    output = render_citations(raw_lines, citations, plan)

    assert plan.state == "baseline"
    assert output.splitlines(keepends=True)[1] == raw.splitlines(keepends=True)[1]
    assert output == raw.replace(
        b'"snapshot_passage_node"', b'"related_passage_non_exact"', 1
    )

    output_lines, output_rows = parse_jsonl_bytes(output, label="applied fixture")
    second_plan = _plan(nodes, output_rows)
    assert second_plan.state == "applied"
    assert render_citations(output_lines, output_rows, second_plan) == output


def test_retype_rejects_partial_or_non_one_to_one_state() -> None:
    nodes = [_node("passage_a", "p1"), _node("passage_b", "p2")]
    partial = [
        {
            "citation_type": "snapshot_passage_node",
            "kg_node_id": "passage_a",
            "passage_id": "p1",
        },
        {
            "citation_type": TARGET_TYPE,
            "kg_node_id": "passage_b",
            "passage_id": "p2",
        },
    ]
    with pytest.raises(ApplyBlocked, match="partial citation state"):
        _plan(nodes, partial)

    duplicate = [
        partial[0],
        dict(partial[0]),
        partial[1] | {"citation_type": TARGET_TYPE},
    ]
    with pytest.raises(ApplyBlocked, match="exactly one citation row"):
        _plan(nodes, duplicate)


def test_repository_cohort_projects_exactly_289_related_types() -> None:
    from scripts.apply_2026_08_18_related_citation_types import ROOT, read_jsonl

    _node_lines, nodes = read_jsonl(ROOT / "data" / "kg" / "nodes.jsonl")
    citation_lines, citations = read_jsonl(ROOT / "data" / "corpus" / "citations.jsonl")
    plan = build_plan(nodes, citations)
    projected = render_citations(citation_lines, citations, plan)
    _projected_lines, projected_rows = parse_jsonl_bytes(
        projected, label="projected repository citations"
    )

    related_rows = [
        row for row in projected_rows if row.get("citation_type") == TARGET_TYPE
    ]
    assert len(plan.changes) == 289
    assert len(related_rows) == 289
    assert {row["kg_node_id"] for row in related_rows} == {
        change.node_id for change in plan.changes
    }
    assert all(
        json.loads(line) == row
        for line, row in zip(_projected_lines, projected_rows, strict=True)
    )
