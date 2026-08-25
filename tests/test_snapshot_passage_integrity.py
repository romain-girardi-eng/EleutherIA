from __future__ import annotations

import json

from scripts.check_snapshot_passage_integrity import (
    audit_integrity,
    compare_baseline,
    make_baseline,
)


def passage_node(node_id: str, passage_id: str, **metadata):
    data = {
        "passage_id": passage_id,
        "canonical_ref": "Ref 1",
        "cts_urn": "urn:test:1",
        **metadata,
    }
    return {
        "id": node_id,
        "node_id": node_id,
        "type": "passage",
        "description": "Greek text",
        "metadata": json.dumps(data),
    }


def corpus(passage_id: str):
    return {
        "passage_id": passage_id,
        "canonical_ref": "Ref 1",
        "cts_urn": "urn:test:1",
        "text_content": "Greek text",
    }


def snapshot(node_id: str, passage_id: str):
    return {
        "kg_node_id": node_id,
        "passage_id": passage_id,
        "citation_type": "snapshot_passage_node",
    }


def test_clean_exact_twin_has_no_violation() -> None:
    assert audit_integrity(
        [passage_node("passage_a", "p1")], [corpus("p1")], [snapshot("passage_a", "p1")]
    ) == []


def test_detects_bijection_and_editorial_failures() -> None:
    nodes = [
        passage_node("passage_a", "p1"),
        passage_node(
            "passage_b",
            "p1",
            attestation_type="editorial_synthesis",
            citable_as_primary=False,
        ),
    ]
    violations = audit_integrity(
        nodes,
        [corpus("p1")],
        [snapshot("passage_a", "p1"), snapshot("passage_b", "p1")],
    )
    codes = [row["code"] for row in violations]
    assert codes.count("snapshot_passage_not_bijective") == 2
    assert codes.count("snapshot_editorial_or_non_primary") == 1


def test_baseline_allows_shrink_but_rejects_new_exact_debt() -> None:
    initial = audit_integrity(
        [passage_node("a", "p1"), passage_node("b", "p1")],
        [corpus("p1")],
        [snapshot("a", "p1"), snapshot("b", "p1")],
    )
    baseline = make_baseline(initial)
    new, ceilings = compare_baseline(initial[:-1], baseline)
    assert new == []
    assert ceilings == {}

    changed = audit_integrity(
        [passage_node("a", "p1", canonical_ref="Wrong")],
        [corpus("p1")],
        [snapshot("a", "p1")],
    )
    new, _ = compare_baseline(changed, baseline)
    assert any(row["code"] == "declared_canonical_ref_mismatch" for row in new)
