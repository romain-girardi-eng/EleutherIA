"""Pytest smoke subset for the GraphRAG eval harness.

These tests are skipped unless ``--run-eval`` is passed (see conftest.py). They
exist to let CI run a tiny live-backend sanity check; the full evaluation is
driven by ``run_eval.py``.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.eval.run_eval import (
    aggregate,
    compute_query_metrics,
    extract_predicted_passages,
    extract_returned_ids,
    load_queries,
    run,
)

# --- Pure unit tests (always run) ------------------------------------------


def test_load_queries_yaml_is_valid() -> None:
    path = Path(__file__).parent / "queries.yaml"
    cases = load_queries(path)
    assert len(cases) >= 20, "expected at least 20 curated queries"

    seen_ids: set[str] = set()
    valid_types = {
        "concept-author",
        "school-debate",
        "fact",
        "comparison",
        "fragment",
        "romain_thesis_queries",
    }
    valid_difficulty = {"easy", "medium", "hard"}
    for c in cases:
        assert c.id not in seen_ids, f"duplicate id {c.id}"
        seen_ids.add(c.id)
        assert c.query.strip(), c.id
        assert c.query_type in valid_types, f"{c.id}: bad type {c.query_type}"
        assert c.difficulty in valid_difficulty, f"{c.id}: bad difficulty"
        assert c.expected_entities or c.expected_entity_keywords, (
            f"{c.id}: needs at least one expected_entity or keyword"
        )
        # Gold annotation fields are optional but must parse as lists.
        assert isinstance(c.expected_passages, list), c.id
        assert isinstance(c.gold_claims, list), c.id


def test_extract_returned_ids_from_payload() -> None:
    payload = {
        "citations": [
            {"ref": "1", "type": "node", "id": "person_aristotle", "label": "A"},
            {"ref": "P2", "type": "passage", "id": "passage_xyz", "label": "P"},
        ],
        "sources": [
            {
                "id": 1,
                "node_id": "concept_hekousion",
                "node_label": "C",
                "node_type": "concept",
                "content": "",
            },
        ],
        "context_nodes": ["work_nicomachean_ethics", "person_aristotle"],
        "seed_nodes": ["concept_eph_hemin"],
        "evidence_map": {
            "argument_x": {"node_id": "argument_x", "confidence": 0.7, "type": "direct"}
        },
    }
    ids, works = extract_returned_ids(payload)
    assert "person_aristotle" in ids
    assert "concept_hekousion" in ids
    assert "work_nicomachean_ethics" in ids
    assert "concept_eph_hemin" in ids
    assert "argument_x" in ids
    # Passage citation should NOT pollute node ids.
    assert "passage_xyz" not in ids
    # Dedup
    assert ids.count("person_aristotle") == 1
    # Works bucket
    assert "work_nicomachean_ethics" in works


def test_extract_predicted_passages_only_passage_citations() -> None:
    payload = {
        "citations": [
            {"ref": "1", "type": "node", "id": "person_aristotle", "label": "A"},
            {"ref": "P1", "type": "passage", "id": "passage_abc", "label": "P"},
            {"ref": "P2", "type": "passage", "id": "passage_abc", "label": "P"},
            {"ref": "P3", "type": "passage", "id": "passage_xyz", "label": "P"},
        ],
    }
    assert extract_predicted_passages(payload) == ["passage_abc", "passage_xyz"]


def test_compute_query_metrics_basic() -> None:
    from tests.eval.run_eval import QueryCase

    case = QueryCase(
        id="q",
        query="t",
        query_type="fact",
        difficulty="easy",
        expected_entities=["a", "b", "c"],
        expected_entity_keywords=["foo", "bar"],
        expected_works=["work_x"],
    )
    metrics = compute_query_metrics(
        case,
        returned_entities=["a", "b", "z"],
        returned_works=["work_x"],
        answer_text="this mentions foo only",
    )
    # 2/3 expected found, 2/3 returned matched
    assert metrics["entity_recall"] == round(2 / 3, 4)
    assert metrics["entity_precision"] == round(2 / 3, 4)
    # Only "foo" hits out of 2 keywords
    assert metrics["keyword_hit_rate"] == 0.5
    assert metrics["work_recall"] == 1.0


def test_aggregate_handles_empty_and_errors() -> None:
    agg = aggregate([])
    assert agg["total_queries"] == 0
    assert agg["error_rate"] == 0.0


# --- Live smoke test (only with --run-eval) ---------------------------------


@pytest.mark.eval
def test_eval_smoke_subset(
    eval_base_url: str,
    eval_limit: int,
    eval_binding: dict[str, str],
    queries_path: Path,
) -> None:
    cases = load_queries(queries_path)[:eval_limit]
    doc = run(
        eval_base_url,
        cases,
        query_files=[queries_path],
        verbose=False,
        **eval_binding,
    )
    assert doc["summary"]["counts"]["successes"] == len(cases), (
        f"some queries failed: {doc['summary']['counts']}"
    )
