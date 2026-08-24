from __future__ import annotations

from collections import Counter
from pathlib import Path

from scripts.apply_2026_08_24_augustine_dla_1_11_21_repair import (
    CORRUPT_NODE,
    CORRUPT_PASSAGE,
    EXACT_NODE,
    EXACT_PASSAGE,
    metadata,
    node_id,
    read_jsonl,
    transform,
    validate,
)

ROOT = Path(__file__).resolve().parents[1]


def load_graph():
    return (
        read_jsonl(ROOT / "data/kg/nodes.jsonl"),
        read_jsonl(ROOT / "data/kg/edges.jsonl"),
        read_jsonl(ROOT / "data/corpus/passages.jsonl"),
        read_jsonl(ROOT / "data/corpus/citations.jsonl"),
    )


def test_augustine_repair_keeps_only_exact_latin_snapshot() -> None:
    nodes, edges, passages, citations, quarantine, counts = transform(*load_graph())
    validate(nodes, edges, passages, citations)
    by_node = {node_id(node): node for node in nodes}
    by_passage = {row["passage_id"]: row for row in passages}
    assert CORRUPT_NODE not in by_node
    assert CORRUPT_PASSAGE not in by_passage
    assert by_node[EXACT_NODE]["description"] == by_passage[EXACT_PASSAGE]["text_content"]
    assert metadata(by_node[EXACT_NODE])["citable_as_primary"] is True
    assert "Augustine coins" not in by_node[EXACT_NODE]["description"]
    assert "Tertullian" in by_node["concept_liberum_arbitrium_u3v4w5x6"]["description"]
    if counts:
        assert quarantine


def test_augustine_repair_is_idempotent() -> None:
    first = transform(*load_graph())
    second = transform(first[0], first[1], first[2], first[3])
    assert second[:4] == first[:4]
    assert second[4] == []
    assert second[5] == Counter()
