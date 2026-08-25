from pathlib import Path

from scripts.apply_2026_08_24_porphyry_ad_marcellam_identity_repair import (
    NEW_CANONICAL,
    NEW_URN,
    WORK_NODE,
    metadata,
    node_id,
    read_jsonl,
    transform,
    validate,
)

ROOT = Path(__file__).resolve().parents[1]


def load_data():
    return (
        read_jsonl(ROOT / "data/kg/nodes.jsonl"),
        read_jsonl(ROOT / "data/corpus/passages.jsonl"),
        read_jsonl(ROOT / "data/corpus/manifest.jsonl"),
    )


def test_porphyry_identity_is_authoritative_and_consistent() -> None:
    nodes, passages, manifest, _ = transform(*load_data())
    validate(nodes, passages, manifest)
    by_node = {node_id(node): node for node in nodes}
    assert metadata(by_node[WORK_NODE])["cts_urn"] == NEW_URN
    assert sum(row.get("work_canonical_id") == NEW_CANONICAL for row in passages) == 35
    relevant = [
        metadata(node)
        for node in nodes
        if node_id(node) == WORK_NODE or node_id(node).startswith("passage_porph_marc_")
    ]
    assert all(row["work_canonical_id"] == NEW_URN for row in relevant)
    assert all(row.get("cts_urn", NEW_URN).startswith(NEW_URN) for row in relevant)


def test_porphyry_identity_repair_is_idempotent() -> None:
    first = transform(*load_data())
    second = transform(first[0], first[1], first[2])
    assert second[:3] == first[:3]
    assert second[3] == []
