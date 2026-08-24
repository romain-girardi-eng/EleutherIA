from __future__ import annotations

import copy
import hashlib
import json
import shutil
from pathlib import Path

import scripts.apply_2026_08_24_galen_tlg010_identity_repair as repair

ROOT = Path(__file__).resolve().parents[1]


def load_data(data_root: Path = ROOT / "data"):
    return (
        repair.read_jsonl(data_root / "kg/nodes.jsonl"),
        repair.read_jsonl(data_root / "kg/edges.jsonl"),
        repair.read_jsonl(data_root / "corpus/passages.jsonl"),
        repair.read_jsonl(data_root / "corpus/citations.jsonl"),
        repair.read_jsonl(data_root / "corpus/manifest.jsonl"),
    )


def legacy_data(data_root: Path = ROOT / "data"):
    rows = list(load_data(data_root))
    manifest = copy.deepcopy(rows[4])
    target = next(
        row for row in manifest if row["canonical_id"] == repair.NATURAL_CANONICAL_ID
    )
    target["title"] = repair.WRONG_TITLE
    target["cts_urn"] = ""
    for key in (
        "work_urn",
        "language",
        "edition",
        "license",
        "source_commit",
        "identity_repair_2026_08_24",
    ):
        target.pop(key, None)
    rows[4] = manifest
    return tuple(rows)


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_galen_tlg010_identity_and_all_surfaces_are_consistent() -> None:
    original = legacy_data()
    nodes, edges, passages, citations, manifest, changed = repair.transform(*original)
    counts = repair.validate(nodes, edges, passages, citations, manifest)

    assert changed == ["manifest:" + repair.NATURAL_CANONICAL_ID]
    assert counts == {
        "work_nodes": 2,
        "passage_nodes": 3,
        "corpus_passages": 3,
        "snapshot_citations": 3,
        "part_of_edges": 3,
        "manifest_rows": 1,
    }
    row = next(
        item for item in manifest if item["canonical_id"] == repair.NATURAL_CANONICAL_ID
    )
    assert row["title"] == repair.NATURAL_TITLE
    assert row["work_urn"] == repair.NATURAL_WORK_URN
    assert row["cts_urn"] == repair.NATURAL_EDITION_URN
    assert row["source"] == "scaife:" + repair.NATURAL_EDITION_URN
    assert "vol. 2" in row["edition"]


def test_committed_snapshot_is_already_current() -> None:
    result = repair.transform(*load_data())
    repair.validate(*result[:5])
    assert result[5] == []


def test_only_the_proved_manifest_row_changes() -> None:
    original = legacy_data()
    transformed = repair.transform(*original)
    assert transformed[0] == original[0]  # nodes
    assert transformed[1] == original[1]  # edges
    assert transformed[2] == original[2]  # passages
    assert transformed[3] == original[3]  # citations

    old_manifest = {
        row["canonical_id"]: row for row in original[4]
    }
    new_manifest = {
        row["canonical_id"]: row for row in transformed[4]
    }
    changed_keys = {
        key for key in old_manifest if old_manifest[key] != new_manifest[key]
    }
    assert changed_keys == {repair.NATURAL_CANONICAL_ID}


def test_galen_full_book_texts_are_exact_snapshot_twins() -> None:
    transformed = repair.transform(*load_data())
    repair.validate(*transformed[:5])

    by_node = {repair.node_id(node): node for node in transformed[0]}
    by_passage = {row["passage_id"]: row for row in transformed[2]}
    for spec in repair.PASSAGES:
        node_text = str(by_node[spec["node_id"]]["description"])
        corpus_text = str(by_passage[spec["passage_id"]]["text_content"])
        assert repair.nfc(node_text) == repair.nfc(corpus_text)
        assert repair.sha256_text(corpus_text) == spec["text_sha256"]


def test_galen_identity_repair_is_idempotent() -> None:
    first = repair.transform(*legacy_data())
    second = repair.transform(*first[:5])
    assert second[:5] == first[:5]
    assert second[5] == []


def test_dry_run_write_and_quarantine_contract(tmp_path: Path, monkeypatch) -> None:
    data_root = tmp_path / "data"
    for relative in (
        "kg/nodes.jsonl",
        "kg/edges.jsonl",
        "corpus/passages.jsonl",
        "corpus/citations.jsonl",
        "corpus/manifest.jsonl",
    ):
        target = data_root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / "data" / relative, target)

    legacy_manifest = legacy_data()[4]
    (data_root / "corpus/manifest.jsonl").write_text(
        "\n".join(
            json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            for row in legacy_manifest
        )
        + "\n",
        encoding="utf-8",
    )

    tracked = [
        data_root / relative
        for relative in (
            "kg/nodes.jsonl",
            "kg/edges.jsonl",
            "corpus/passages.jsonl",
            "corpus/citations.jsonl",
            "corpus/manifest.jsonl",
        )
    ]
    before = {path: file_sha256(path) for path in tracked}
    assert repair.main(["--data-root", str(data_root)]) == 0
    assert {path: file_sha256(path) for path in tracked} == before
    assert not (data_root / repair.REPORT_RELATIVE).exists()

    monkeypatch.setattr(
        repair,
        "verify_authority_snapshot",
        lambda passages: {
            "authority": "test pinned OGL fixture",
            "text_proofs": [spec["passage_id"] for spec in repair.PASSAGES],
        },
    )
    assert repair.main(["--write", "--data-root", str(data_root)]) == 0
    after_write = {path: file_sha256(path) for path in tracked}
    assert after_write[data_root / "corpus/manifest.jsonl"] != before[
        data_root / "corpus/manifest.jsonl"
    ]
    for path in tracked[:-1]:
        assert after_write[path] == before[path]

    quarantine = repair.read_jsonl(data_root / repair.QUARANTINE_RELATIVE)
    assert quarantine[0]["record"]["title"] == repair.WRONG_TITLE
    row = next(
        item
        for item in repair.read_jsonl(data_root / "corpus/manifest.jsonl")
        if item["canonical_id"] == repair.NATURAL_CANONICAL_ID
    )
    assert row["title"] == repair.NATURAL_TITLE

    assert repair.main(["--write", "--data-root", str(data_root)]) == 0
    assert {path: file_sha256(path) for path in tracked} == after_write


def test_registry_records_have_independent_and_adversarial_reviews() -> None:
    issue = repair.registry_issue()
    reviews = repair.registry_verifications()
    assert issue["status"] == "resolved"
    assert issue["issue_id"] == repair.ISSUE_ID
    assert {review["stage"] for review in reviews} == {
        "primary",
        "independent",
        "adversarial",
    }
    assert len({review["verifier"]["independence_group"] for review in reviews}) == 3
    # Ensure JSON serializability matches the JSONL registry writer.
    json.dumps([copy.deepcopy(issue), *copy.deepcopy(reviews)], ensure_ascii=False)
