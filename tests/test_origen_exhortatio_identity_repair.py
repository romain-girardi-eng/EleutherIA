from __future__ import annotations

import copy
import hashlib
import json
from collections import Counter
from pathlib import Path

import pytest

import scripts.apply_2026_08_24_origen_exhortatio_identity_repair as repair

ROOT = Path(__file__).resolve().parents[1]


def load_data(data_root: Path = ROOT / "data"):
    return (
        repair.read_jsonl(data_root / "kg/nodes.jsonl"),
        repair.read_jsonl(data_root / "kg/edges.jsonl"),
        repair.read_jsonl(data_root / "corpus/passages.jsonl"),
        repair.read_jsonl(data_root / "corpus/citations.jsonl"),
        repair.read_jsonl(data_root / "corpus/manifest.jsonl"),
    )


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def legacy_data():
    """Rebuild the frozen pre-Wave-0.2 cohort from committed before-images."""

    rows = [copy.deepcopy(items) for items in load_data()]
    quarantine = repair.read_jsonl(ROOT / "data" / repair.QUARANTINE_RELATIVE)
    assert len(quarantine) == 258

    node_before: dict[str, dict] = {}
    edge_before: dict[str, dict] = {}
    passage_before: dict[str, dict] = {}
    citation_before: dict[str, dict] = {}
    manifest_before: dict[str, dict] = {}
    for item in quarantine:
        record = copy.deepcopy(item["record"])
        record_type = item["record_type"]
        if record_type == "kg_passage_node_before":
            node_before[item["alias_to"]] = record
        elif record_type == "kg_work_node_before":
            node_before[repair.node_id(record)] = record
        elif record_type == "kg_edge_before":
            edge_before[record["edge_id"]] = record
        elif record_type == "corpus_passage_before":
            passage_before[record["passage_id"]] = record
        elif record_type == "corpus_citation_before":
            citation_before[record["passage_id"]] = record
        elif record_type == "corpus_manifest_before":
            manifest_before[record["canonical_id"]] = record
        else:  # pragma: no cover - quarantine schema is itself under test
            raise AssertionError(record_type)

    rows[0] = [node_before.get(repair.node_id(row), row) for row in rows[0]]
    rows[1] = [edge_before.get(str(row.get("edge_id") or ""), row) for row in rows[1]]
    rows[2] = [
        passage_before.get(str(row.get("passage_id") or ""), row) for row in rows[2]
    ]
    rows[3] = [
        citation_before.get(str(row.get("passage_id") or ""), row)
        if row.get("citation_type") == "snapshot_passage_node"
        else row
        for row in rows[3]
    ]
    rows[4] = [
        manifest_before.get(str(row.get("canonical_id") or ""), row)
        for row in rows[4]
    ]
    rebuilt = tuple(rows)
    assert repair.target_node_mode(rebuilt[0]) == "legacy"
    repair.validate_legacy_preimage(*rebuilt)
    return rebuilt


def copy_data_root(tmp_path: Path) -> Path:
    data_root = tmp_path / "data"
    current = load_data()
    legacy = legacy_data()
    for relative, before_rows, after_rows in zip(
        (
            "kg/nodes.jsonl",
            "kg/edges.jsonl",
            "corpus/passages.jsonl",
            "corpus/citations.jsonl",
            "corpus/manifest.jsonl",
        ),
        current,
        legacy,
        strict=True,
    ):
        target = data_root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(
            repair.render_jsonl_preserving_unchanged(
                ROOT / "data" / relative, before_rows, after_rows
            )
        )
    return data_root


def authority_fixture(passages):
    repair.validate_immutable_passages(passages)
    return {
        "authority": "pinned OGL test fixture",
        "authority_commit": repair.OGL_COMMIT,
        "selected_passages": 51,
        "text_verdict": "51/51 NFC-exact",
        "verdict": "pass",
    }


def transaction_payload(data_root: Path):
    paths = repair._paths(data_root)
    original = load_data(data_root)
    result = repair.transform(*original)
    repaired = result[:5]
    core_contents = {
        name: repair.render_jsonl_preserving_unchanged(
            paths[name], before_rows, after_rows
        )
        for name, before_rows, after_rows in zip(
            ("nodes", "edges", "passages", "citations", "manifest"),
            original,
            repaired,
            strict=True,
        )
    }
    artifact_contents = {
        data_root / repair.REPORT_RELATIVE: b'{"test":"report"}\n',
        data_root / repair.QUARANTINE_RELATIVE: b'{"test":"quarantine"}\n',
        data_root / repair.ALIASES_RELATIVE: b'{"test":"aliases"}\n',
    }
    return (
        paths,
        repair.core_file_hashes(paths),
        core_contents,
        artifact_contents,
    )


def test_exhortatio_transform_repairs_all_surfaces_and_cardinalities() -> None:
    original = legacy_data()
    result = repair.transform(*original)
    nodes, edges, passages, citations, manifest, quarantine, changed, mode = result

    assert mode == "legacy"
    assert changed == Counter(
        {
            "kg_passage_node_before": 51,
            "kg_work_node_before": 2,
            "kg_edge_before": 102,
            "corpus_passage_before": 51,
            "corpus_citation_before": 51,
            "corpus_manifest_before": 1,
        }
    )
    assert len(quarantine) == 258
    assert repair.validate_repaired(
        nodes, edges, passages, citations, manifest
    ) == {
        "work_nodes": 2,
        "passage_nodes": 51,
        "corpus_passages": 51,
        "snapshot_citations": 51,
        "authored_by_edges": 51,
        "part_of_edges": 51,
        "manifest_rows": 1,
        "clement_corpus_children": 0,
    }


def test_exhortatio_preserves_all_51_uuid_text_ref_and_cts_values() -> None:
    original = legacy_data()
    repaired = repair.transform(*original)
    old_rows = {
        row["passage_id"]: row for row in repair.passage_rows(original[2])
    }
    new_rows = {
        row["passage_id"]: row for row in repair.passage_rows(repaired[2])
    }
    assert old_rows.keys() == new_rows.keys()
    for passage_id in old_rows:
        old = old_rows[passage_id]
        new = new_rows[passage_id]
        for field in (
            "passage_id",
            "sequence_number",
            "text_content",
            "canonical_ref",
            "cts_urn",
            "work_canonical_id",
        ):
            assert new[field] == old[field]
        section = int(new["sequence_number"])
        assert new["parity_propagation_2026_08_17"]["kg_node_id"] == (
            repair.expected_new_node(section)
        )


def test_alias_cohort_remaps_nodes_edges_citations_and_parity_atomically() -> None:
    nodes, edges, passages, citations, manifest, *_ = repair.transform(*legacy_data())
    node_ids = {repair.node_id(node) for node in nodes}
    assert node_ids >= repair.NEW_NODE_IDS
    assert not (repair.OLD_NODE_IDS & node_ids)

    by_node = {repair.node_id(node): node for node in nodes}
    for section in range(1, 52):
        new_id = repair.expected_new_node(section)
        old_id = repair.expected_old_node(section)
        assert repair.metadata(by_node[new_id])["legacy_node_ids"] == [old_id]

    affected_edges = [
        edge
        for edge in edges
        if edge.get("source") in repair.NEW_NODE_IDS
        or edge.get("target") in repair.NEW_NODE_IDS
    ]
    assert len(affected_edges) == 102
    assert not [
        edge
        for edge in edges
        if edge.get("source") in repair.OLD_NODE_IDS
        or edge.get("target") in repair.OLD_NODE_IDS
        or edge.get("source_id") in repair.OLD_NODE_IDS
        or edge.get("target_id") in repair.OLD_NODE_IDS
    ]
    assert len(
        [row for row in citations if row.get("kg_node_id") in repair.NEW_NODE_IDS]
    ) == 51
    assert not [
        row for row in citations if row.get("kg_node_id") in repair.OLD_NODE_IDS
    ]
    assert {
        row["parity_propagation_2026_08_17"]["kg_node_id"]
        for row in repair.passage_rows(passages)
    } == repair.NEW_NODE_IDS
    repair.validate_repaired(nodes, edges, passages, citations, manifest)


def test_exhortatio_work_nodes_and_manifest_are_distinct_and_truthful() -> None:
    nodes, edges, passages, citations, manifest, *_ = repair.transform(*legacy_data())
    by_node = {repair.node_id(node): node for node in nodes}
    origen = repair.metadata(by_node[repair.ORIGEN_WORK_NODE])
    clement = repair.metadata(by_node[repair.CLEMENT_WORK_NODE])
    assert origen["work_canonical_id"] == repair.ORIGEN_WORK_URN
    assert origen["cts_urn"] == repair.ORIGEN_EDITION_URN
    assert origen["needs_text_ingestion"] is False
    assert origen["passage_count"] == 51
    assert clement["work_canonical_id"] == repair.CLEMENT_WORK_URN
    assert clement["cts_urn"] == repair.CLEMENT_EDITION_URN
    assert clement["needs_text_ingestion"] is True
    assert clement["passage_count"] == 0
    assert "ingestion_debt_2026_08_17_canonical_derived" not in clement

    row = repair.target_manifest_rows(manifest)[0]
    assert row["author"] == "Origen"
    assert row["title"] == "Exhortatio ad martyrium"
    assert row["source"] == "scaife:" + repair.ORIGEN_EDITION_URN
    assert row["work_urn"] == repair.ORIGEN_WORK_URN
    assert row["cts_urn"] == repair.ORIGEN_EDITION_URN
    assert row["passages"] == 51


def test_non_target_records_are_byte_semantically_unchanged_in_memory() -> None:
    original = legacy_data()
    repaired = repair.transform(*original)
    old_nodes = {repair.node_id(node): node for node in original[0]}
    new_nodes = {repair.node_id(node): node for node in repaired[0]}
    excluded = {
        repair.ORIGEN_WORK_NODE,
        repair.CLEMENT_WORK_NODE,
        *repair.OLD_NODE_IDS,
    }
    for wanted in old_nodes.keys() - excluded:
        assert new_nodes[wanted] == old_nodes[wanted]

    for old, new in zip(original[1], repaired[1], strict=True):
        if old.get("source") not in repair.OLD_NODE_IDS:
            assert new == old
    for old, new in zip(original[2], repaired[2], strict=True):
        if old.get("work_canonical_id") != repair.CORPUS_CANONICAL_ID:
            assert new == old
    for old, new in zip(original[3], repaired[3], strict=True):
        if old.get("kg_node_id") not in repair.OLD_NODE_IDS:
            assert new == old
    for old, new in zip(original[4], repaired[4], strict=True):
        if old.get("canonical_id") != repair.CORPUS_CANONICAL_ID:
            assert new == old


def test_exhortatio_transform_is_idempotent() -> None:
    current = load_data()
    repair.validate_repaired(*current)
    committed_again = repair.transform(*current)
    assert committed_again[:5] == current
    assert committed_again[5] == []
    assert committed_again[6] == Counter()
    assert committed_again[7] == "repaired"

    first = repair.transform(*legacy_data())
    second = repair.transform(*first[:5])
    assert second[:5] == first[:5]
    assert second[5] == []
    assert second[6] == Counter()
    assert second[7] == "repaired"


def test_partial_alias_cutover_is_rejected() -> None:
    rows = list(legacy_data())
    nodes = copy.deepcopy(rows[0])
    target = next(
        node
        for node in nodes
        if repair.node_id(node) == repair.expected_old_node(1)
    )
    target["id"] = repair.expected_new_node(1)
    target["node_id"] = repair.expected_new_node(1)
    rows[0] = nodes
    with pytest.raises(RuntimeError, match="mixed/incomplete"):
        repair.transform(*rows)


def test_text_or_target_preimage_drift_is_rejected() -> None:
    rows = list(legacy_data())
    passages = copy.deepcopy(rows[2])
    target = next(
        row
        for row in passages
        if row.get("work_canonical_id") == repair.CORPUS_CANONICAL_ID
    )
    target["text_content"] += " corruption"
    rows[2] = passages
    with pytest.raises(RuntimeError, match="evidence cohort drift|raw text cohort drift"):
        repair.transform(*rows)


def test_dry_run_writes_nothing_and_temp_write_is_idempotent(
    tmp_path: Path, monkeypatch
) -> None:
    data_root = copy_data_root(tmp_path)
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
    monkeypatch.setattr(repair, "verify_authority_snapshot", authority_fixture)

    assert repair.main(["--data-root", str(data_root)]) == 0
    assert {path: file_sha256(path) for path in tracked} == before
    assert not (data_root / repair.REPORT_RELATIVE).exists()
    assert not (data_root / repair.QUARANTINE_RELATIVE).exists()
    assert not (data_root / repair.ALIASES_RELATIVE).exists()

    assert repair.main(["--write", "--data-root", str(data_root)]) == 0
    after_write = {path: file_sha256(path) for path in tracked}
    assert all(after_write[path] != before[path] for path in tracked)
    assert len(repair.read_jsonl(data_root / repair.QUARANTINE_RELATIVE)) == 258
    aliases = json.loads((data_root / repair.ALIASES_RELATIVE).read_text())
    assert aliases["alias_count"] == 51
    assert len(aliases["aliases"]) == 51
    report = json.loads((data_root / repair.REPORT_RELATIVE).read_text())
    assert report["write_performed"] is True
    assert report["changed_records_total"] == 258

    assert repair.main(["--write", "--data-root", str(data_root)]) == 0
    assert {path: file_sha256(path) for path in tracked} == after_write


def test_alias_artifact_is_complete_and_deterministic() -> None:
    first = repair.alias_artifact()
    second = repair.alias_artifact()
    assert first == second
    assert first["alias_count"] == 51
    assert {
        row["legacy_node_id"]: row["canonical_node_id"]
        for row in first["aliases"]
    } == repair.NODE_ALIASES
    json.dumps(first, ensure_ascii=False)


def test_transaction_detects_concurrent_drift_after_fsync_staging(
    tmp_path: Path,
) -> None:
    data_root = copy_data_root(tmp_path)
    paths, expected, core_contents, artifacts = transaction_payload(data_root)
    before = {name: file_sha256(path) for name, path in paths.items()}

    def concurrent_change() -> None:
        with paths["manifest"].open("ab") as handle:
            handle.write(b"\n")
            handle.flush()

    with pytest.raises(RuntimeError, match="concurrent core-file drift at pre-commit"):
        repair.commit_transaction(
            data_root=data_root,
            core_paths=paths,
            expected_core_hashes=expected,
            core_contents=core_contents,
            artifact_contents=artifacts,
            before_commit=concurrent_change,
        )

    # The concurrent writer's byte is retained; the migration itself committed nothing.
    assert file_sha256(paths["manifest"]) != before["manifest"]
    for name, path in paths.items():
        if name != "manifest":
            assert file_sha256(path) == before[name]
    assert not [path for path in artifacts if path.exists()]
    assert not list(data_root.glob(".origen-exhortatio-wave-0-2-*"))


def test_transaction_rolls_back_a_mid_commit_replace_failure(
    tmp_path: Path, monkeypatch
) -> None:
    data_root = copy_data_root(tmp_path)
    paths, expected, core_contents, artifacts = transaction_payload(data_root)
    before = {name: file_sha256(path) for name, path in paths.items()}
    real_replace = repair._replace_file
    calls = 0

    def fail_once(source: Path, target: Path) -> None:
        nonlocal calls
        calls += 1
        if calls == 3:
            raise OSError("simulated third replace failure")
        real_replace(source, target)

    monkeypatch.setattr(repair, "_replace_file", fail_once)
    with pytest.raises(RuntimeError, match="rollback succeeded"):
        repair.commit_transaction(
            data_root=data_root,
            core_paths=paths,
            expected_core_hashes=expected,
            core_contents=core_contents,
            artifact_contents=artifacts,
        )

    assert {name: file_sha256(path) for name, path in paths.items()} == before
    assert not [path for path in artifacts if path.exists()]
    assert not list(data_root.glob(".origen-exhortatio-wave-0-2-*"))


def test_transaction_rolls_back_when_directory_fsync_fails_after_replace(
    tmp_path: Path, monkeypatch
) -> None:
    data_root = copy_data_root(tmp_path)
    paths, expected, core_contents, artifacts = transaction_payload(data_root)
    before = {name: file_sha256(path) for name, path in paths.items()}
    real_fsync_directory = repair._fsync_directory
    failed = False

    def fail_first_commit_fsync(path: Path) -> None:
        nonlocal failed
        # Staging and journal fsyncs use the transaction directory. The first
        # fsync of data/kg follows the first successful os.replace.
        if not failed and path.resolve() == paths["nodes"].parent.resolve():
            failed = True
            raise OSError("simulated post-replace directory fsync failure")
        real_fsync_directory(path)

    monkeypatch.setattr(repair, "_fsync_directory", fail_first_commit_fsync)
    with pytest.raises(RuntimeError, match="rollback succeeded"):
        repair.commit_transaction(
            data_root=data_root,
            core_paths=paths,
            expected_core_hashes=expected,
            core_contents=core_contents,
            artifact_contents=artifacts,
        )

    assert {name: file_sha256(path) for name, path in paths.items()} == before
    assert not [path for path in artifacts if path.exists()]
    assert not list(data_root.glob(".origen-exhortatio-wave-0-2-*"))


def test_journal_recovers_a_simulated_hard_crash_on_next_write(
    tmp_path: Path, monkeypatch
) -> None:
    class SimulatedHardCrash(BaseException):
        pass

    data_root = copy_data_root(tmp_path)
    paths, expected, core_contents, artifacts = transaction_payload(data_root)
    before = {name: file_sha256(path) for name, path in paths.items()}
    real_replace = repair._replace_file
    calls = 0

    def crash_on_third_replace(source: Path, target: Path) -> None:
        nonlocal calls
        calls += 1
        if calls == 3:
            raise SimulatedHardCrash()
        real_replace(source, target)

    monkeypatch.setattr(repair, "_replace_file", crash_on_third_replace)
    with pytest.raises(SimulatedHardCrash):
        repair.commit_transaction(
            data_root=data_root,
            core_paths=paths,
            expected_core_hashes=expected,
            core_contents=core_contents,
            artifact_contents=artifacts,
        )

    stage_dirs = list(data_root.glob(f"{repair.TRANSACTION_PREFIX}*"))
    assert len(stage_dirs) == 1
    assert (stage_dirs[0] / repair.TRANSACTION_JOURNAL).exists()
    assert {name: file_sha256(path) for name, path in paths.items()} != before

    monkeypatch.setattr(repair, "_replace_file", real_replace)
    recovered = repair.recover_interrupted_transactions(
        data_root=data_root, core_paths=paths
    )
    assert [row["action"] for row in recovered] == ["rolled_back"]
    assert {name: file_sha256(path) for name, path in paths.items()} == before
    assert not [path for path in artifacts if path.exists()]
    assert not list(data_root.glob(f"{repair.TRANSACTION_PREFIX}*"))


@pytest.mark.parametrize(
    "artifact_relative",
    [
        repair.REPORT_RELATIVE,
        repair.QUARANTINE_RELATIVE,
        repair.ALIASES_RELATIVE,
    ],
)
def test_write_refuses_to_overwrite_any_existing_audit_artifact(
    tmp_path: Path, monkeypatch, artifact_relative: str
) -> None:
    data_root = copy_data_root(tmp_path)
    paths = repair._paths(data_root)
    before = repair.core_file_hashes(paths)
    sentinel = data_root / artifact_relative
    sentinel.parent.mkdir(parents=True, exist_ok=True)
    sentinel.write_text("do-not-overwrite\n", encoding="utf-8")
    monkeypatch.setattr(repair, "verify_authority_snapshot", authority_fixture)

    with pytest.raises(RuntimeError, match="refusing to overwrite"):
        repair.main(["--write", "--data-root", str(data_root)])

    assert repair.core_file_hashes(paths) == before
    assert sentinel.read_text(encoding="utf-8") == "do-not-overwrite\n"
    for relative in (
        repair.REPORT_RELATIVE,
        repair.QUARANTINE_RELATIVE,
        repair.ALIASES_RELATIVE,
    ):
        target = data_root / relative
        if target != sentinel:
            assert not target.exists()


def test_authority_inputs_are_commit_and_hash_pinned() -> None:
    assert repair.OGL_COMMIT == "7881c563436f52fb3550e6daa6df94be1b83b0e3"
    assert set(repair.OGL_URLS) == {"origen_cts", "origen_tei", "clement_cts"}
    assert set(repair.OGL_SHA256) == set(repair.OGL_URLS)
    assert all(repair.OGL_COMMIT in url for url in repair.OGL_URLS.values())
    assert all(len(value) == 64 for value in repair.OGL_SHA256.values())
