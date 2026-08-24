from pathlib import Path

from scripts.apply_2026_08_24_cicero_de_fato_identity_repair import (
    NEW_ENG,
    NEW_LAT,
    NEW_WORK_URN,
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


def test_cicero_work_and_both_language_manifests_use_phi054() -> None:
    nodes, passages, manifest, _ = transform(*load_data())
    validate(nodes, passages, manifest)
    by_node = {node_id(node): node for node in nodes}
    assert metadata(by_node[WORK_NODE])["cts_urn"] == NEW_WORK_URN
    assert sum(row.get("work_canonical_id") == NEW_LAT for row in passages) == 48
    assert sum(row.get("work_canonical_id") == NEW_ENG for row in passages) == 48
    assert {row["canonical_id"] for row in manifest if "phi0474_phi054" in row["canonical_id"]} >= {
        NEW_LAT,
        NEW_ENG,
    }
    for i in range(1, 49):
        english = metadata(by_node[f"passage_cic_fat_{i}_en"])
        assert english["db_passage_id"] == english["source_passage_id"]
        assert english["primary_text_status"] == "published_translation"


def test_cicero_identity_repair_is_idempotent() -> None:
    first = transform(*load_data())
    second = transform(first[0], first[1], first[2])
    assert second[:3] == first[:3]
    assert second[3] == []
