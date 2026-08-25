from __future__ import annotations

import copy
import hashlib
import json
from collections import Counter
from pathlib import Path

import pytest

import scripts.apply_2026_08_24_sextus_exact_cohort_repair as repair
import scripts.apply_2026_08_24_sextus_postcutover_citation_repair as postcutover

ROOT = Path(__file__).resolve().parents[1]
ORIGINAL_QUARANTINE = (
    ROOT / "data/audit/2026-08-24_sextus_exact_cohort_quarantine.jsonl"
)
POSTCUTOVER_QUARANTINE = ROOT / "data" / postcutover.QUARANTINE_RELATIVE


def load_data(data_root: Path = ROOT / "data"):
    return repair.load_data(data_root)


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            for row in rows
        )
        + "\n",
        encoding="utf-8",
    )


def active_authority(data=None) -> repair.AuthoritySnapshot:
    data = data or load_data()
    sections: list[repair.ExactSection] = []
    for row in data[2]:
        urn = str(row.get("cts_urn") or "")
        if urn.startswith(repair.PH_EDITION_URN + ":"):
            work_key = "ph"
        elif urn.startswith(repair.AM_EDITION_URN + ":"):
            work_key = "am"
        else:
            continue
        book, section = (int(value) for value in urn.rsplit(":", 1)[1].split("."))
        text = repair.normalize_text(str(row.get("text_content") or ""))
        exact = repair.ExactSection(
            work_key=work_key,
            book=book,
            section=section,
            text=text,
            text_sha256_nfc=repair.sha256_text(text),
        )
        assert row["passage_id"] == exact.passage_id
        assert row["sequence_number"] == exact.sequence_number
        assert row["text_sha256_nfc"] == exact.text_sha256_nfc
        sections.append(exact)
    sections.sort(key=lambda row: (row.work_key, row.book, row.section))
    assert Counter(row.work_key for row in sections) == Counter({"am": 2732, "ph": 781})
    assert len(sections) == repair.EXPECTED_EXACT_TOTAL
    return repair.AuthoritySnapshot(
        sections=tuple(sections),
        file_sha256=copy.deepcopy(repair.OGL_SHA256),
        catalog_facts={
            "ph": {
                "work_urn": repair.PH_WORK_URN,
                "title": "Pyrrhoniae Hypotyposes",
                "edition_urn": repair.PH_EDITION_URN,
            },
            "am": {
                "work_urn": repair.AM_WORK_URN,
                "title": "Adversus Mathematicos",
                "edition_urn": repair.AM_EDITION_URN,
            },
        },
    )


def expected_postcutover_data(data=None):
    data = tuple(copy.deepcopy(rows) for rows in (data or load_data()))
    result = postcutover.transform(data[0], data[2], data[3])
    return data[0], data[1], data[2], result.citations, data[4]


def postcutover_before_rows() -> list[dict]:
    if POSTCUTOVER_QUARANTINE.exists():
        rows = postcutover.core.read_jsonl(POSTCUTOVER_QUARANTINE)
        assert len(rows) == 4
        before = [row["record"] for row in rows]
    else:
        before = [
            postcutover.old_row(decision)
            for decision in repair.CITATION_REWIRE_DECISIONS
        ]
    assert {repair.citation_key(row) for row in before} == {
        repair.citation_key(postcutover.old_row(decision))
        for decision in repair.CITATION_REWIRE_DECISIONS
    }
    return before


def frozen_legacy_fixture(data=None):
    """Rebuild the exact pre-cutover state from committed before-images."""

    current = expected_postcutover_data(data)
    authority = active_authority(current)
    nodes, edges, passages, citations, manifest = (
        copy.deepcopy(rows) for rows in current
    )
    exact_node_ids = {row.node_id for row in authority.sections}
    exact_passage_ids = {row.passage_id for row in authority.sections}
    exact_edge_ids = {
        repair.edge_id(repair.make_edge(row.node_id, "authored_by", repair.PERSON_NODE))
        for row in authority.sections
    } | {
        repair.edge_id(repair.make_edge(row.node_id, "part_of", row.work.work_node))
        for row in authority.sections
    }
    semantic_edges, _plans = repair._replacement_edges(authority)
    exact_edge_ids |= {repair.edge_id(row) for row in semantic_edges}
    exact_snapshot_keys = {
        repair.citation_key(repair.make_snapshot_citation(row))
        for row in authority.sections
    }
    exact_related_keys = {
        repair.citation_key(repair.make_rewired_citation(decision, authority))
        for decision in repair.CITATION_REWIRE_DECISIONS
    }

    nodes = [row for row in nodes if repair.node_id(row) not in exact_node_ids]
    edges = [row for row in edges if repair.edge_id(row) not in exact_edge_ids]
    passages = [
        row
        for row in passages
        if str(row.get("passage_id") or "") not in exact_passage_ids
    ]
    citations = [
        row
        for row in citations
        if repair.citation_key(row) not in exact_snapshot_keys | exact_related_keys
    ]

    quarantine = repair.read_jsonl(ORIGINAL_QUARANTINE)
    assert len(quarantine) == 3475
    node_index = {repair.node_id(row): index for index, row in enumerate(nodes)}
    edge_ids = {repair.edge_id(row) for row in edges}
    passage_ids = {str(row.get("passage_id") or "") for row in passages}
    citation_keys = {repair.citation_key(row) for row in citations}
    manifest_index = {
        str(row.get("canonical_id") or ""): index for index, row in enumerate(manifest)
    }
    for item in quarantine:
        record = copy.deepcopy(item["record"])
        kind = item["record_type"]
        if kind == "kg_node_before":
            identifier = repair.node_id(record)
            if identifier in node_index:
                nodes[node_index[identifier]] = record
            else:
                node_index[identifier] = len(nodes)
                nodes.append(record)
        elif kind == "kg_edge_before":
            identifier = repair.edge_id(record)
            assert identifier not in edge_ids
            edge_ids.add(identifier)
            edges.append(record)
        elif kind == "corpus_passage_before":
            identifier = str(record["passage_id"])
            assert identifier not in passage_ids
            passage_ids.add(identifier)
            passages.append(record)
        elif kind == "corpus_citation_before":
            identifier = repair.citation_key(record)
            assert identifier not in citation_keys
            citation_keys.add(identifier)
            citations.append(record)
        elif kind == "corpus_manifest_before":
            identifier = str(record["canonical_id"])
            manifest[manifest_index[identifier]] = record
        else:  # pragma: no cover - quarantine schema is closed by the assertion.
            raise AssertionError(kind)
    for record in postcutover_before_rows():
        identifier = repair.citation_key(record)
        assert identifier not in citation_keys
        citation_keys.add(identifier)
        citations.append(copy.deepcopy(record))

    assert sum(repair._legacy_number(repair.node_id(row)) is not None for row in nodes) == 534
    assert sum(repair._is_current_exact_row(row) for row in passages) == 791
    assert len(
        [
            row
            for row in citations
            if str(row.get("passage_id") or "")
            in {decision.old_passage_id for decision in repair.CITATION_REWIRE_DECISIONS}
            and row.get("citation_type") != "snapshot_passage_node"
        ]
    ) == 4
    return nodes, edges, passages, citations, manifest


def keyed(rows, key):
    result = {key(row): row for row in rows}
    assert len(result) == len(rows)
    return result


def assert_surfaces_equal(actual, expected) -> None:
    assert keyed(actual[0], repair.node_id) == keyed(expected[0], repair.node_id)
    assert keyed(actual[1], repair.edge_id) == keyed(expected[1], repair.edge_id)
    assert keyed(actual[2], lambda row: str(row["passage_id"])) == keyed(
        expected[2], lambda row: str(row["passage_id"])
    )
    assert keyed(actual[3], repair.citation_key) == keyed(
        expected[3], repair.citation_key
    )
    assert keyed(actual[4], lambda row: str(row["canonical_id"])) == keyed(
        expected[4], lambda row: str(row["canonical_id"])
    )


def test_active_exact_cohort_is_complete_and_deterministic() -> None:
    authority = active_authority()
    assert len(authority.sections) == 3513
    assert len({row.node_id for row in authority.sections}) == 3513
    assert len({row.passage_id for row in authority.sections}) == 3513
    assert len({row.cts_urn for row in authority.sections}) == 3513


def test_tei_parser_excludes_editorial_material_and_repairs_ph_splits() -> None:
    xml = f"""<TEI xmlns='http://www.tei-c.org/ns/1.0'><text><body>
      <div type='edition' n='{repair.PH_EDITION_URN}'>
       <div type='textpart' subtype='book' n='2'><div type='textpart' subtype='chapter' n='32'>
        <div type='textpart' subtype='section' n='259'><p>II.259 first.</p></div>
       </div></div>
       <div type='textpart' subtype='book' n='3'>
        <div type='textpart' subtype='chapter' n='0'><div type='textpart' subtype='section' n='1'><p>II.259 tail.</p></div></div>
        <div type='textpart' subtype='chapter' n='1'><div type='textpart' subtype='section' n='1'><head>DROP</head><p>III.1 first <note>APP</note> text.</p></div></div>
        <div type='textpart' subtype='chapter' n='2'><div type='textpart' subtype='section' n='1'><p>III.1 tail.</p></div></div>
        <div type='textpart' subtype='chapter' n='29'><div type='textpart' subtype='section' n='265'><p>265 first.</p></div></div>
        <div type='textpart' subtype='chapter' n='30'><div type='textpart' subtype='section' n='265'><p>265 tail.</p></div></div>
       </div>
      </div></body></text></TEI>""".encode()
    parsed = repair.parse_tei_sections(xml, "ph", enforce_complete=False)
    assert parsed[(2, 259)] == "II.259 first. II.259 tail."
    assert parsed[(3, 1)] == "III.1 first text. III.1 tail."
    assert parsed[(3, 265)] == "265 first. 265 tail."
    assert "APP" not in "\n".join(parsed.values())
    assert "DROP" not in "\n".join(parsed.values())


def test_frozen_legacy_roundtrip_equals_repaired_current_state() -> None:
    current = expected_postcutover_data()
    authority = active_authority(current)
    result = repair.transform(*frozen_legacy_fixture(current), authority)
    actual = (
        result.nodes,
        result.edges,
        result.passages,
        result.citations,
        result.manifest,
    )
    assert_surfaces_equal(actual, current)
    assert result.changes["quarantine_records"] == 3479
    assert result.changes["legacy_non_snapshot_citations_rewired"] == 4
    assert result.changes["exact_non_snapshot_citations_added"] == 4
    assert len(result.plan["citation_rewire_decisions"]) == 4
    assert result.plan["target"]["exact_non_snapshot_citations"] == 4


def test_updated_migration_is_idempotent_on_expected_post_state() -> None:
    current = expected_postcutover_data()
    authority = active_authority(current)
    repair.validate_zero_debt(*current, authority)
    second = repair.transform(*current, authority)
    assert second.changes == Counter()
    assert second.quarantine == []
    assert_surfaces_equal(
        (second.nodes, second.edges, second.passages, second.citations, second.manifest),
        current,
    )


def test_legacy_partial_exact_text_drift_fails_closed() -> None:
    current = expected_postcutover_data()
    authority = active_authority(current)
    legacy = list(frozen_legacy_fixture(current))
    passages = copy.deepcopy(legacy[2])
    row = next(
        item
        for item in passages
        if item.get("cts_urn") == repair.AM_EDITION_URN + ":9.1"
    )
    row["text_content"] += " drift"
    legacy[2] = passages
    with pytest.raises(RuntimeError, match="existing exact Sextus text drift"):
        repair.transform(*legacy, authority)


def write_fixture(data_root: Path, data) -> None:
    for relative, rows in zip(
        (
            "kg/nodes.jsonl",
            "kg/edges.jsonl",
            "corpus/passages.jsonl",
            "corpus/citations.jsonl",
            "corpus/manifest.jsonl",
        ),
        data,
        strict=True,
    ):
        write_jsonl(data_root / relative, rows)


def test_original_transaction_rejects_snapshot_drift(tmp_path: Path) -> None:
    current = expected_postcutover_data()
    authority = active_authority(current)
    data_root = tmp_path / "data"
    write_fixture(data_root, frozen_legacy_fixture(current))
    snapshot = repair.load_data_snapshot(data_root)
    result = repair.transform(*snapshot.rows, authority)
    manifest_path = data_root / "corpus/manifest.jsonl"
    drift = manifest_path.read_bytes() + b"\n"
    manifest_path.write_bytes(drift)
    with pytest.raises(RuntimeError, match="since parsed Sextus snapshot A"):
        repair.write_result(data_root, result, snapshot.original_bytes)
    assert manifest_path.read_bytes() == drift
    assert not (data_root / repair.QUARANTINE_RELATIVE).exists()
    assert not list(data_root.rglob(".sextus-stage-*"))


def test_original_transaction_rolls_back_injected_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    current = expected_postcutover_data()
    authority = active_authority(current)
    data_root = tmp_path / "data"
    write_fixture(data_root, frozen_legacy_fixture(current))
    snapshot = repair.load_data_snapshot(data_root)
    result = repair.transform(*snapshot.rows, authority)
    real_replace = repair._replace_staged_file
    calls = 0

    def fail_fourth(staged: Path, target: Path) -> None:
        nonlocal calls
        calls += 1
        if calls == 4:
            raise OSError("injected rollback proof")
        real_replace(staged, target)

    monkeypatch.setattr(repair, "_replace_staged_file", fail_fourth)
    with pytest.raises(OSError, match="injected rollback proof"):
        repair.write_result(data_root, result, snapshot.original_bytes)
    paths = {
        "nodes": data_root / "kg/nodes.jsonl",
        "edges": data_root / "kg/edges.jsonl",
        "passages": data_root / "corpus/passages.jsonl",
        "citations": data_root / "corpus/citations.jsonl",
        "manifest": data_root / "corpus/manifest.jsonl",
    }
    assert {name: path.read_bytes() for name, path in paths.items()} == snapshot.original_bytes
    assert not (data_root / repair.QUARANTINE_RELATIVE).exists()
    assert not list(data_root.rglob(".sextus-stage-*"))


def test_current_phase_is_explicit_and_final_state_validates() -> None:
    current = load_data()
    post = postcutover.transform(current[0], current[2], current[3])
    if POSTCUTOVER_QUARANTINE.exists():
        assert post.changes == 0
        repair.validate_zero_debt(*current, active_authority(current))
    else:
        assert post.changes == 4
        expected = (current[0], current[1], current[2], post.citations, current[4])
        repair.validate_zero_debt(*expected, active_authority(expected))
