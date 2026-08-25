from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from scripts.apply_2026_08_24_aristotle_gc_identity_repair import (
    CHILD_IDS,
    NEW_CORPUS_CANONICAL,
    NEW_EDITION_URN,
    NEW_WORK_URN,
    OGL_COMMIT,
    OGL_SHA256,
    PASSAGES,
    REPORT_RELATIVE,
    WORK_NODE,
    metadata,
    node_id,
    read_jsonl,
    transform,
    validate,
)
from scripts.check_kg_work_child_canonical import find_mismatches
from scripts.check_snapshot_passage_integrity import audit_integrity

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


def load_data():
    return (
        read_jsonl(DATA / "kg/nodes.jsonl"),
        read_jsonl(DATA / "kg/edges.jsonl"),
        read_jsonl(DATA / "corpus/passages.jsonl"),
        read_jsonl(DATA / "corpus/citations.jsonl"),
        read_jsonl(DATA / "corpus/manifest.jsonl"),
    )


def test_gc_identity_is_tlg013_on_every_current_surface() -> None:
    nodes, edges, passages, citations, manifest = load_data()
    result = transform(nodes, edges, passages, citations, manifest)
    repaired_nodes, repaired_passages, repaired_manifest = result[:3]
    validate(repaired_nodes, edges, repaired_passages, citations, repaired_manifest)
    by_node = {node_id(node): node for node in repaired_nodes}

    work = metadata(by_node[WORK_NODE])
    assert work["canonical_id"] == NEW_WORK_URN
    assert work["work_canonical_id"] == NEW_WORK_URN
    assert work["cts_urn"] == NEW_EDITION_URN
    assert "TLG 0086.013." in by_node[WORK_NODE]["description"]

    corpus_by_id = {row["passage_id"]: row for row in repaired_passages}
    for child_id, spec in PASSAGES.items():
        child = metadata(by_node[child_id])
        assert child["work_canonical_id"] == NEW_WORK_URN
        assert child["cts_urn"] == f"{NEW_EDITION_URN}:{spec['locus']}"
        assert child["text_content_sha256_nfc"] == spec["text_sha256_nfc"]
        assert corpus_by_id[spec["passage_id"]]["work_canonical_id"] == (
            NEW_CORPUS_CANONICAL
        )

    row = next(
        row
        for row in repaired_manifest
        if row.get("canonical_id") == NEW_CORPUS_CANONICAL
    )
    assert row["cts_urn"] == NEW_EDITION_URN
    assert row["source"] == f"scaife:{NEW_EDITION_URN}"
    assert row["passages"] == 3
    if result[3]:
        assert len(result[3]) == 8


def test_gc_repair_does_not_change_other_works_or_any_text_uuid_locus() -> None:
    nodes, edges, passages, citations, manifest = load_data()
    repaired_nodes, repaired_passages, repaired_manifest, _, _ = transform(
        nodes, edges, passages, citations, manifest
    )

    old_nodes = {node_id(row): row for row in nodes}
    new_nodes = {node_id(row): row for row in repaired_nodes}
    for wanted in old_nodes.keys() - {WORK_NODE, *CHILD_IDS}:
        assert new_nodes[wanted] == old_nodes[wanted]

    target_passages = {spec["passage_id"] for spec in PASSAGES.values()}
    old_passages = {row["passage_id"]: row for row in passages}
    new_passages = {row["passage_id"]: row for row in repaired_passages}
    for wanted in old_passages.keys() - target_passages:
        assert new_passages[wanted] == old_passages[wanted]
    for wanted in target_passages:
        for field in ("passage_id", "canonical_ref", "cts_urn", "text_content"):
            assert new_passages[wanted][field] == old_passages[wanted][field]

    old_other_manifest = [
        row
        for row in manifest
        if row.get("title") != "De Generatione et Corruptione"
    ]
    new_other_manifest = [
        row
        for row in repaired_manifest
        if row.get("title") != "De Generatione et Corruptione"
    ]
    assert new_other_manifest == old_other_manifest
    assert citations == load_data()[3]


def test_gc_work_child_and_snapshot_cohorts_are_clean() -> None:
    nodes, edges, passages, citations, manifest = load_data()
    repaired_nodes, repaired_passages, repaired_manifest, _, _ = transform(
        nodes, edges, passages, citations, manifest
    )
    assert find_mismatches(repaired_nodes, edges, repaired_manifest) == []
    violations = audit_integrity(repaired_nodes, repaired_passages, citations)
    assert not [
        row for row in violations if row.get("node_id") in CHILD_IDS
    ]


def test_gc_repair_is_idempotent() -> None:
    nodes, edges, passages, citations, manifest = load_data()
    first = transform(nodes, edges, passages, citations, manifest)
    second = transform(first[0], edges, first[1], citations, first[2])
    assert second[:3] == first[:3]
    assert second[3] == []
    assert second[4] == Counter()


def test_gc_authority_report_is_pinned_and_passed() -> None:
    report = json.loads((ROOT / REPORT_RELATIVE).read_text(encoding="utf-8"))
    authority = report["authority_verification"]
    assert authority["verdict"] == "pass"
    assert authority["authority_commit"] == OGL_COMMIT
    assert authority["catalog_facts"][NEW_WORK_URN] == (
        "De generatione et corruptione"
    )
    assert authority["catalog_facts"]["urn:cts:greekLit:tlg0086.tlg003"] == (
        "Res Publica Atheniensium"
    )
    assert {row["label"]: row["sha256"] for row in authority["files"]} == OGL_SHA256
    assert {row["passage_id"] for row in authority["selected_passages"]} == {
        spec["passage_id"] for spec in PASSAGES.values()
    }
