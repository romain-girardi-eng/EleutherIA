from __future__ import annotations

import json
import shutil
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

import pytest

import scripts.apply_2026_08_24_tatian_p0_repair as repair

ROOT = Path(__file__).resolve().parents[1]
LIVE_DATA = ROOT / "data"
DATA = LIVE_DATA
POSTWRITE_DATA = LIVE_DATA
LIVE_TATIAN_APPLIED = False
AUTHORITY_XML = Path("/tmp/tatian-otto-1851-release-1.1.32401591783.xml")
TATIAN_REPORT_SHA256 = (
    "b832d77849e1de9a767457afd1cb773609adf58a3d0165d47a9489743f9ee98c"
)
TATIAN_QUARANTINE_SHA256 = (
    "906013db5a2201252e67e2ff5b13ca88af1419c21c970a1cdddb9c5ad89963c7"
)


def _by(rows: list[dict], field: str) -> dict[str, dict]:
    return {str(row.get(field) or ""): row for row in rows}


def _nodes(rows: list[dict]) -> dict[str, dict]:
    return {repair.node_id(row): row for row in rows}


def _chapter_rows(rows: list[dict]) -> dict[int, dict]:
    return {
        repair.passage_chapter(row): row
        for row in rows
        if row.get("work_canonical_id") == repair.MANIFEST_ID
    }


def _authority() -> repair.Authority:
    return repair.load_authority()


def _assert_tatian_postwrite_record_state(data_root: Path) -> None:
    report_path = data_root / repair.REPORT_RELATIVE
    quarantine_path = data_root / repair.QUARANTINE_RELATIVE
    assert repair.sha256_bytes(report_path.read_bytes()) == TATIAN_REPORT_SHA256
    assert repair.sha256_bytes(quarantine_path.read_bytes()) == (
        TATIAN_QUARANTINE_SHA256
    )
    report = json.loads(report_path.read_text(encoding="utf-8"))
    validation = report["validation"]
    assert validation["record_diff_ids"] == repair.EXPECTED_RECORD_DIFF_IDS
    assert validation["record_diff_digests"] == repair.EXPECTED_RECORD_DIFF_DIGESTS
    for label in repair.MUTABLE_LABELS:
        key = repair.JSONL_KEYS[label]
        current = {
            key(row): row
            for row in repair.read_jsonl(data_root / repair.INPUT_RELATIVES[label])
        }
        diff = validation["record_diff"][label]
        for identifier, hashes in diff["added"].items():
            assert repair.record_hash(current[identifier]) == hashes["after"]
        for identifier, hashes in diff["modified"].items():
            assert repair.record_hash(current[identifier]) == hashes["after"]
        for identifier in diff["removed"]:
            assert identifier not in current
    assert len(repair.rows_from_bytes(quarantine_path.read_bytes())) == 101


def _reconstruct_postwrite_snapshot_a(tmp_path: Path) -> Path:
    data_root = tmp_path / "repo" / "data"
    shutil.copytree(
        LIVE_DATA / "goals" / "sota", data_root / "goals" / "sota"
    )
    for _label, relative in repair.INPUT_RELATIVES.items():
        source = LIVE_DATA / relative
        target = data_root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)

    quarantine = repair.rows_from_bytes(
        (LIVE_DATA / repair.QUARANTINE_RELATIVE).read_bytes()
    )
    specs = {
        "nodes": (
            "kg_node_before",
            "kg_node_absence_before",
            repair.node_id,
            lambda row: str(row["node_id"]),
        ),
        "edges": (
            "kg_edge_before",
            "kg_edge_absence_before",
            repair.edge_id,
            lambda row: str(row["edge_id"]),
        ),
        "passages": (
            "corpus_passage_before",
            None,
            lambda row: str(row.get("passage_id") or ""),
            None,
        ),
        "citations": (
            "corpus_citation_before",
            "corpus_citation_absence_before",
            repair.citation_key,
            lambda row: str(row["citation_key"]),
        ),
        "manifest": (
            "corpus_manifest_before",
            None,
            lambda row: str(row.get("canonical_id") or ""),
            None,
        ),
        "registry_sources": (
            "registry_source_before",
            "registry_source_absence_before",
            lambda row: str(row.get("source_id") or ""),
            lambda row: str(row["source_id"]),
        ),
        "registry_evidence": (
            "registry_evidence_before",
            "registry_evidence_absence_before",
            lambda row: str(row.get("evidence_id") or ""),
            lambda row: str(row["evidence_id"]),
        ),
        "registry_issues": (
            None,
            "registry_issue_absence_before",
            lambda row: str(row.get("issue_id") or ""),
            lambda row: str(row["issue_id"]),
        ),
        "registry_waves": (
            "registry_wave_before",
            None,
            lambda row: str(row.get("wave_id") or ""),
            None,
        ),
    }
    for label, (before_type, absence_type, key, absence_key) in specs.items():
        path = data_root / repair.INPUT_RELATIVES[label]
        order: list[str] = []
        records: dict[str, dict] = {}
        raw_lines: dict[str, str] = {}
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            record = json.loads(line)
            identifier = key(record)
            order.append(identifier)
            records[identifier] = record
            raw_lines[identifier] = line
        if before_type is not None:
            for item in quarantine:
                if item.get("record_type") != before_type:
                    continue
                record = item["record"]
                identifier = key(record)
                if identifier not in records:
                    order.append(identifier)
                records[identifier] = record
                raw_lines[identifier] = repair.canonical_json(record)
        if absence_type is not None and absence_key is not None:
            for item in quarantine:
                if item.get("record_type") != absence_type:
                    continue
                identifier = absence_key(item)
                records.pop(identifier, None)
                raw_lines.pop(identifier, None)
        payload = "\n".join(
            raw_lines[identifier]
            for identifier in order
            if identifier in records
        ) + "\n"
        path.write_text(payload, encoding="utf-8")
    return data_root


@pytest.fixture(scope="session", autouse=True)
def _use_prospective_snapshot_a_postwrite(tmp_path_factory: pytest.TempPathFactory):
    global DATA, LIVE_TATIAN_APPLIED, POSTWRITE_DATA
    live_hashes = {
        label: repair.sha256_bytes(
            (LIVE_DATA / repair.INPUT_RELATIVES[label]).read_bytes()
        )
        for label in repair.MUTABLE_LABELS
    }
    if live_hashes == repair.INPUT_BEFORE_SHA256:
        yield
        return
    _assert_tatian_postwrite_record_state(LIVE_DATA)
    LIVE_TATIAN_APPLIED = True
    POSTWRITE_DATA = LIVE_DATA
    prospective = _reconstruct_postwrite_snapshot_a(
        tmp_path_factory.mktemp("tatian-preapply")
    )
    reconstructed = {
        label: repair.sha256_bytes(
            (prospective / repair.INPUT_RELATIVES[label]).read_bytes()
        )
        for label in repair.MUTABLE_LABELS
    }
    original_before = dict(repair.INPUT_BEFORE_SHA256)
    original_after = dict(repair.INPUT_AFTER_SHA256)
    repair.INPUT_BEFORE_SHA256.clear()
    repair.INPUT_BEFORE_SHA256.update(reconstructed)
    prospective_snapshot = repair.load_data_snapshot(prospective)
    prospective_result = repair.transform(prospective_snapshot, _authority())
    synthetic_after = {
        label: repair.sha256_bytes(
            repair._jsonl_preserving(
                prospective_snapshot.raw[label],
                prospective_result.rows[label],
                repair.JSONL_KEYS[label],
                label,
            )
        )
        for label in repair.MUTABLE_LABELS
    }
    repair.INPUT_AFTER_SHA256.clear()
    repair.INPUT_AFTER_SHA256.update(synthetic_after)
    postwrite = tmp_path_factory.mktemp("tatian-postwrite") / "data"
    shutil.copytree(prospective, postwrite)
    postwrite_snapshot = repair.load_data_snapshot(postwrite)
    postwrite_result = repair.transform(postwrite_snapshot, _authority())
    repair.write_result(postwrite, postwrite_snapshot, postwrite_result)
    assert {
        label: repair.sha256_bytes(
            (postwrite / repair.INPUT_RELATIVES[label]).read_bytes()
        )
        for label in repair.MUTABLE_LABELS
    } == synthetic_after
    DATA = prospective
    POSTWRITE_DATA = postwrite
    try:
        yield
    finally:
        DATA = LIVE_DATA
        POSTWRITE_DATA = LIVE_DATA
        LIVE_TATIAN_APPLIED = False
        repair.INPUT_BEFORE_SHA256.clear()
        repair.INPUT_BEFORE_SHA256.update(original_before)
        repair.INPUT_AFTER_SHA256.clear()
        repair.INPUT_AFTER_SHA256.update(original_after)


def _copy_data_root(tmp_path: Path) -> Path:
    data_root = tmp_path / "repo" / "data"
    shutil.copytree(DATA / "goals" / "sota", data_root / "goals" / "sota")
    for _label, relative in repair.INPUT_RELATIVES.items():
        source = DATA / relative
        target = data_root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    return data_root


def _link_unmodified_repo_inputs(repo_root: Path) -> None:
    data_root = repo_root / "data"
    for source in LIVE_DATA.iterdir():
        target = data_root / source.name
        if not target.exists():
            target.symlink_to(source, target_is_directory=source.is_dir())
        elif source.is_dir() and target.is_dir():
            for child in source.iterdir():
                child_target = target / child.name
                if not child_target.exists():
                    child_target.symlink_to(
                        child, target_is_directory=child.is_dir()
                    )
    audit_target = data_root / "audit"
    audit_target.mkdir(exist_ok=True)
    for source in (LIVE_DATA / "audit").iterdir():
        target = audit_target / source.name
        if not target.exists():
            target.symlink_to(source, target_is_directory=source.is_dir())
    for name in ("docs", "scripts", "tests"):
        (repo_root / name).symlink_to(ROOT / name, target_is_directory=True)


def test_authority_fixture_is_complete_pinned_and_internally_hashed() -> None:
    assert repair.sha256_bytes(repair.DEFAULT_AUTHORITY.read_bytes()) == (
        repair.AUTHORITY_FIXTURE_SHA256
    )
    assert repair.sha256_bytes(repair.INDEPENDENT_REVIEW_V2.read_bytes()) == (
        repair.INDEPENDENT_REVIEW_V2_SHA256
    )
    assert repair.sha256_bytes(repair.HILDEBRANDT_REPORT.read_bytes()) == (
        repair.HILDEBRANDT_REPORT_SHA256
    )
    authority = _authority()
    assert authority.mode == "derived_fixture_pinned_to_raw_tei_sha256"
    assert authority.source["release"] == "1.1.32401591783"
    assert authority.source["commit"] == "78f9df37d694a9e0e92de2963f2fa8852e49efb6"
    assert authority.source["tei_sha256"] == (
        "bfe1671160c9155552055a24bd86345d2efb5392cd03e70a947d4a7a9ce00e4a"
    )
    assert authority.source["license"] == "CC BY-SA 4.0"
    assert set(authority.first_segment_hashes) == set(range(1, 43))
    assert set(authority.replacement_chapters) == {7, 8, 11}
    assert authority.exact_evidence_segments == {
        "15.9": {
            "chapter": 15,
            "segment_n": "26",
            "sha256_nfc": "c1c7d081eb9fed87d936019df642d1b6bdbae222eed64a7e6ad855d0ce6e6730",
            "required_marker": "θανάτου νόμους",
        }
    }
    assert {
        chapter: repair.text_hash(text)
        for chapter, text in authority.replacement_chapters.items()
    } == {
        7: "10d5f5de95045e8c9754a2c431cbfa14042a72b1f87b6fa9ab277f5079c3b4fd",
        8: "9194a6ddb13cec8fcf74d4d20392688a5787d1aff18c29872a738205e10bdb6f",
        11: "65be1c120ed652dfc6e6bc4d0d94a86bd23d32fb76b12821d411c64ddaaffd20",
    }


def test_block_aware_join_preserves_inline_text_and_inserts_boundaries() -> None:
    chapter = ET.fromstring(
        """<div xmlns="http://www.tei-c.org/ns/1.0" type="textpart"
        subtype="chapter" n="1"><p><seg n="1">τρόπον.</seg><seg n="2">Ἡ
        <hi>δύναμις</hi> μένει.</seg></p><pb n="2"/><p><seg n="3">Λόγος,
        <milestone n="x"/>ἄλλος.</seg></p></div>"""
    )
    segments = chapter.findall(".//tei:seg", repair.TEI_NS)
    expected_blocks = [repair.inline_reading_text(segment) for segment in segments]
    assert repair.chapter_semantic_blocks(chapter) == expected_blocks
    assert repair.chapter_reading_text(chapter) == (
        "τρόπον. Ἡ δύναμις μένει. Λόγος, ἄλλος."
    )
    assert "δύναμις" in repair.chapter_reading_text(chapter)


@pytest.mark.parametrize(
    "blocks,bad",
    [
        (["τρόπον.", "Ἡ δύναμις"], "τρόπον.Ἡ δύναμις"),
        (["Λόγος,", "ἄλλος"], "Λόγος,ἄλλος"),
        (["περιγίνεται.", "Τί μοι"], "περιγίνεται.Τί μοι"),
    ],
)
def test_semantic_boundary_validator_rejects_fused_blocks(
    blocks: list[str], bad: str
) -> None:
    with pytest.raises(RuntimeError, match="semantic block boundary defect"):
        repair.validate_semantic_block_join(blocks, bad)


def test_corrected_otto_chapters_change_only_four_block_spaces() -> None:
    authority = _authority()
    fused = {
        7: authority.replacement_chapters[7].replace("τρόπον. Ἡ", "τρόπον.Ἡ"),
        8: authority.replacement_chapters[8]
        .replace("ἐγίνετο. Ταύτην", "ἐγίνετο.Ταύτην")
        .replace("ὤνατο. Λεγέτω", "ὤνατο.Λεγέτω"),
        11: authority.replacement_chapters[11].replace(
            "περιγίνεται. Τί", "περιγίνεται.Τί"
        ),
    }
    assert {chapter: repair.text_hash(text) for chapter, text in fused.items()} == {
        7: "db3c5f88bd6f820cd9527f3b05467204347761f2ac505b6249b5c0acd3c48ca5",
        8: "fecabd2a915ec4de3788ed6160e31841b763e0da49067b650c946476ad368470",
        11: "ca33d2ba0600e7cbdd0a5cc4b67e9aeff2fb0bad95638730e1a96935a77b90b4",
    }


def test_fixture_hash_gate_rejects_semantically_modified_copy(tmp_path: Path) -> None:
    payload = repair.DEFAULT_AUTHORITY.read_text(encoding="utf-8").replace(
        "τρόπον. Ἡ", "τρόπον.Ἡ", 1
    )
    fixture = tmp_path / "authority.json"
    fixture.write_text(payload, encoding="utf-8")
    with pytest.raises(RuntimeError, match="fixture SHA-256 drift"):
        repair.load_authority(fixture_path=fixture)


def test_full_official_tei_when_available_matches_derived_fixture() -> None:
    if not AUTHORITY_XML.is_file():
        pytest.skip("pinned official TEI is not present in /tmp")
    authority = repair.load_authority(authority_xml=AUTHORITY_XML)
    assert authority.mode == "full_tei_verified"


def test_transform_restores_three_full_chapters_and_preserves_other_39() -> None:
    snapshot = repair.load_data_snapshot(DATA)
    result = repair.transform(snapshot, _authority())
    assert result.mode == "planned"
    before = _chapter_rows(snapshot.rows["passages"])
    after = _chapter_rows(result.rows["passages"])
    assert set(before) == set(after) == set(range(1, 43))
    for chapter in set(range(1, 43)) - set(repair.TARGET_PASSAGES):
        for field in (
            "text_content",
            "passage_id",
            "canonical_ref",
            "cts_urn",
            "sequence_number",
        ):
            assert after[chapter].get(field) == before[chapter].get(field)
        assert (
            after[chapter]["source_alignment_status"]
            == "exact_first_tei_segment_legacy_chapter_excerpt"
        )
    for chapter, passage_id in repair.TARGET_PASSAGES.items():
        for field in ("passage_id", "cts_urn", "sequence_number"):
            assert after[chapter].get(field) == before[chapter].get(field)
        assert after[chapter]["passage_id"] == passage_id
        assert after[chapter]["canonical_ref"] == f"Orat. {chapter}"
        assert (
            after[chapter]["text_content"]
            == _authority().replacement_chapters[chapter]
        )
        assert after[chapter]["source_alignment_status"] == "exact_full_tei_chapter"
    assert result.validation["full_chapters"] == 3
    assert result.validation["first_segment_legacy_excerpts"] == 39
    assert result.validation["snapshot_global_new_fingerprints"] == 0


def test_manifest_never_overstates_legacy_excerpt_granularity_or_sapere_rights() -> None:
    result = repair.transform(repair.load_data_snapshot(DATA), _authority())
    manifest = _by(result.rows["manifest"], "canonical_id")[repair.MANIFEST_ID]
    assert manifest["cts_urn"] == repair.VERSION_URN
    assert manifest["license"] == "CC BY-SA 4.0"
    granularity = manifest["cohort_granularity"]
    assert granularity["full_chapter_passages"] == [7, 8, 11]
    assert len(granularity["first_segment_legacy_excerpts"]) == 39
    assert granularity["coverage_status"] == "partial_mixed_granularity"
    assert "not complete" in granularity["warning"]
    sapere = manifest["sapere_collation"]
    assert sapere["text_source_for_manifestation"] is False
    assert sapere["sha256"] == repair.SAPERE_SHA256
    assert "No open licence" in sapere["rights"]


def test_exact_snapshots_are_bijective_and_machine_synthesis_nodes_fail_closed() -> None:
    result = repair.transform(repair.load_data_snapshot(DATA), _authority())
    nodes = _nodes(result.rows["nodes"])
    corpus = _chapter_rows(result.rows["passages"])
    pairs = {
        (str(row.get("kg_node_id") or ""), str(row.get("passage_id") or ""))
        for row in result.rows["citations"]
        if row.get("citation_type") == "snapshot_passage_node"
        and row.get("passage_id") in {item["passage_id"] for item in corpus.values()}
    }
    assert len(pairs) == 42
    assert {
        (repair.EXACT_NODES[chapter], repair.TARGET_PASSAGES[chapter])
        for chapter in (7, 8, 11)
    }.issubset(pairs)
    assert not ({*repair.MACHINE_NODES, repair.SYNTHESIS_NODE} & {node for node, _ in pairs})

    CitabilityTier, evidence_policy = repair.load_citability_policy()
    for wanted in repair.MACHINE_NODES:
        assert evidence_policy(nodes[wanted]).tier is CitabilityTier.BLOCKED
        data = repair.metadata(nodes[wanted])
        assert data["translation_type"] == "machine"
        assert "passage_id" not in data
    assert (
        evidence_policy(nodes[repair.SYNTHESIS_NODE]).tier
        is CitabilityTier.DISCOVERABLE_ONLY
    )
    for chapter, wanted in repair.EXACT_NODES.items():
        assert nodes[wanted]["description"] == corpus[chapter]["text_content"]
        assert evidence_policy(nodes[wanted]).tier is CitabilityTier.CITABLE


def test_sapere_corrections_are_confined_to_non_snapshot_fine_nodes() -> None:
    result = repair.transform(repair.load_data_snapshot(DATA), _authority())
    nodes = _nodes(result.rows["nodes"])
    corpus = _chapter_rows(result.rows["passages"])
    assert "τῶν ἀνδρῶν κατασκευῆς" in corpus[7]["text_content"]
    assert "τῶν ἀνδρῶν κατασκευῆς" in nodes[repair.EXACT_NODES[7]]["description"]
    assert "τῶν ἀνθρώπων κατασκευῆς" in nodes["passage_tatian_7_1"]["description"]
    assert "πλουσιώτατοι σιώτατοι" in corpus[11]["text_content"]
    assert "πλουσιώτατοι σιώτατοι" in nodes[repair.EXACT_NODES[11]]["description"]
    assert "πλουσιώτατοι σιώτατοι" not in nodes["passage_tatian_11_1"]["description"]
    for wanted in ("passage_tatian_7_1", "passage_tatian_11_1"):
        data = repair.metadata(nodes[wanted])
        assert data["edition_context"] == "SAPERE 28 / Nesselrath 2016 collation"
        assert data["snapshot_eligible"] is False
        assert data["citability"] == "discoverable_only"


def test_public_loci_and_arguments_are_cautious_and_atomized() -> None:
    result = repair.transform(repair.load_data_snapshot(DATA), _authority())
    nodes = _nodes(result.rows["nodes"])
    person = nodes[repair.PERSON_NODE]
    work = nodes[repair.WORK_NODE]
    assert "7.2" in person["description"]
    assert "9.3" in person["description"]
    assert "11.4" in person["description"]
    assert "11.4" in work["description"]
    for public_node in (person, work):
        public_data = repair.metadata(public_node)
        assert "citation_verified" not in public_data
        assert "verified_reference" not in public_data
        assert public_data["citation_verdict"] != "verified"
        assert "pending" in public_data["claim_review_status"]
    CitabilityTier, evidence_policy = repair.load_citability_policy()
    for wanted in (repair.ARGUMENT_ABOVE, repair.ARGUMENT_FREEWILL):
        argument = nodes[wanted]
        data = repair.metadata(argument)
        roles = {premise["evidence_role"] for premise in data["premises"]}
        assert roles == {
            "primary_text",
            "secondary_in_review",
            "editorial_reconstruction",
        }
        assert data["citation_verified"] is False
        assert data["citability"] == "discoverable_only"
        assert evidence_policy(argument).tier is CitabilityTier.DISCOVERABLE_ONLY
        assert data["validity_assessment"]["scholarly_consensus"] == "not_claimed"
    serialized = repair.canonical_json(
        {
            wanted: nodes[wanted]
            for wanted in (
                repair.PERSON_NODE,
                repair.WORK_NODE,
                repair.ARGUMENT_ABOVE,
                repair.ARGUMENT_FREEWILL,
            )
        }
    ).lower()
    for stale in (
        "or. 7.1 declares",
        "unique to the apologists",
        "means of human salvation",
        "standard scholarly topos",
    ):
        assert stale not in serialized


def test_registry_stays_partial_open_and_has_no_new_verification_pass() -> None:
    snapshot = repair.load_data_snapshot(DATA)
    result = repair.transform(snapshot, _authority())
    sources = _by(result.rows["registry_sources"], "source_id")
    evidence = _by(result.rows["registry_evidence"], "evidence_id")
    issues = _by(result.rows["registry_issues"], "issue_id")
    assert sources[repair.OTTO_SOURCE_ID]["coverage"]["state"] == "partial"
    assert sources[repair.TIMOTIN_SOURCE_ID]["coverage"]["state"] == "partial"
    assert sources[repair.STRUTWOLF_SOURCE_ID]["coverage"]["state"] == "partial"
    for wanted in (
        *repair.ANCIENT_EVIDENCE_IDS.values(),
        repair.TIMOTIN_EVIDENCE_ID,
        repair.STRUTWOLF_EVIDENCE_ID,
    ):
        assert evidence[wanted]["claim_status"] == "in_review"
    issue = issues[repair.ISSUE_ID]
    assert issue["status"] == "open"
    assert issue["severity"] == "critical"
    assert "first-segment" in issue["resolution_criteria"]
    schema = result.validation["registry_schema_debt"]
    assert schema["baseline_errors"] == schema["preview_errors"] == 41
    assert schema["new_errors"] == schema["touched_record_errors"] == 0
    for source_id in (
        repair.OTTO_SOURCE_ID,
        repair.TIMOTIN_SOURCE_ID,
        repair.STRUTWOLF_SOURCE_ID,
    ):
        assert "rights" not in sources[source_id]
    for wanted in repair.ANCIENT_EVIDENCE_IDS.values():
        assert evidence[wanted]["quotation"]["status"] == "collated"
        assert evidence[wanted]["locator"]["page_map_status"] == "visually_verified"
    evidence_15_9 = evidence[repair.ANCIENT_EVIDENCE_IDS["tat_p06"]]
    assert evidence_15_9["quotation"]["text_sha256"] == (
        "c1c7d081eb9fed87d936019df642d1b6bdbae222eed64a7e6ad855d0ce6e6730"
    )
    assert "corpus_passage_ids" not in evidence_15_9["quotation"]
    assert evidence_15_9["kg_targets"] == [repair.WORK_NODE]
    assert "seg n=26" in evidence_15_9["locator"]["edition_or_witness"]
    assert "first seg n=24" in evidence_15_9["notes"]
    assert evidence[repair.TIMOTIN_EVIDENCE_ID]["quotation"]["status"] == (
        "paraphrase_only"
    )
    assert evidence[repair.STRUTWOLF_EVIDENCE_ID]["quotation"]["status"] == (
        "paraphrase_only"
    )
    assert "registry_verifications" not in repair.MUTABLE_LABELS


def test_editorial_synthesis_has_no_active_primary_or_authorship_edges() -> None:
    result = repair.transform(repair.load_data_snapshot(DATA), _authority())
    edges = result.rows["edges"]
    assert not repair.SYNTHESIS_UNSAFE_EDGE_IDS & {
        repair.edge_id(edge) for edge in edges
    }
    assert not any(
        repair.edge_target(edge) == repair.SYNTHESIS_NODE
        and edge.get("relation") == "cites_primary_source"
        for edge in edges
    )
    assert not any(
        repair.edge_source(edge) == repair.SYNTHESIS_NODE
        and edge.get("relation") == "authored_by"
        for edge in edges
    )


def test_exact_record_diff_hashes_and_ids_are_frozen() -> None:
    result = repair.transform(repair.load_data_snapshot(DATA), _authority())
    assert result.validation["record_diff_ids"] == repair.EXPECTED_RECORD_DIFF_IDS
    assert result.validation["record_diff_digests"] == (
        repair.EXPECTED_RECORD_DIFF_DIGESTS
    )
    assert set(result.validation["record_diff"]) == set(repair.MUTABLE_LABELS)
    assert set(result.validation["record_diff"]["nodes"]["added"]) == {
        repair.EXACT_NODES[8]
    }
    assert len(
        result.validation["record_diff"]["nodes"]["added"][
            repair.EXACT_NODES[8]
        ]["after"]
    ) == 64
    assert set(result.validation["record_diff"]["edges"]["removed"]) >= (
        repair.SYNTHESIS_UNSAFE_EDGE_IDS
    )


def test_raw_lines_outside_exact_changed_sets_are_byte_identical() -> None:
    snapshot = repair.load_data_snapshot(DATA)
    result = repair.transform(snapshot, _authority())
    outputs = repair.build_outputs(DATA.resolve(), snapshot, result)
    ids = result.validation["record_diff_ids"]
    for label in repair.MUTABLE_LABELS:
        key = repair.JSONL_KEYS[label]
        before = {
            key(json.loads(line)): line
            for line in snapshot.raw[label].decode("utf-8").splitlines()
            if line.strip()
        }
        after_raw = outputs[DATA.resolve() / repair.INPUT_RELATIVES[label]]
        after = {
            key(json.loads(line)): line
            for line in after_raw.decode("utf-8").splitlines()
            if line.strip()
        }
        changed = {
            *ids[label]["added"],
            *ids[label]["removed"],
            *ids[label]["modified"],
        }
        for identifier in set(before) & set(after) - changed:
            assert before[identifier] == after[identifier], (label, identifier)


def test_output_paths_and_mutable_hashes_are_exact() -> None:
    snapshot = repair.load_data_snapshot(DATA)
    result = repair.transform(snapshot, _authority())
    outputs = repair.build_outputs(DATA.resolve(), snapshot, result)
    assert {
        str(path.relative_to(DATA.resolve())) for path in outputs
    } == repair.EXPECTED_OUTPUT_RELATIVES
    for label in repair.MUTABLE_LABELS:
        path = DATA.resolve() / repair.INPUT_RELATIVES[label]
        assert repair.sha256_bytes(outputs[path]) == repair.INPUT_AFTER_SHA256[label]


def test_quarantine_types_ids_and_before_hashes_match_exact_record_diff() -> None:
    result = repair.transform(repair.load_data_snapshot(DATA), _authority())
    assert Counter(row["record_type"] for row in result.quarantine) == Counter(
        {
            "corpus_passage_before": 42,
            "kg_edge_before": 18,
            "kg_node_before": 16,
            "registry_evidence_absence_before": 7,
            "corpus_citation_before": 6,
            "corpus_citation_absence_before": 2,
            "kg_edge_absence_before": 2,
            "registry_source_absence_before": 2,
            "corpus_manifest_before": 1,
            "kg_node_absence_before": 1,
            "registry_source_before": 1,
            "registry_evidence_before": 1,
            "registry_issue_absence_before": 1,
            "registry_wave_before": 1,
        }
    )
    diff = result.validation["record_diff"]

    def before_map(record_type: str, key) -> dict[str, str]:
        return {
            str(key(row["record"])): row["record_sha256"]
            for row in result.quarantine
            if row["record_type"] == record_type
        }

    assert before_map("kg_node_before", repair.node_id) == {
        identifier: hashes["before"]
        for identifier, hashes in diff["nodes"]["modified"].items()
    }
    assert before_map("kg_edge_before", repair.edge_id) == {
        identifier: hashes["before"]
        for operation in ("modified", "removed")
        for identifier, hashes in diff["edges"][operation].items()
    }
    assert before_map("corpus_passage_before", lambda row: row["passage_id"]) == {
        identifier: hashes["before"]
        for identifier, hashes in diff["passages"]["modified"].items()
    }
    assert {
        row["node_id"]
        for row in result.quarantine
        if row["record_type"] == "kg_node_absence_before"
    } == set(diff["nodes"]["added"])
    assert {
        row["edge_id"]
        for row in result.quarantine
        if row["record_type"] == "kg_edge_absence_before"
    } == set(diff["edges"]["added"])
    assert len(result.quarantine) == result.report["quarantine_records"] == 101


def test_dry_run_is_byte_noop(capsys: pytest.CaptureFixture[str]) -> None:
    before = {
        label: (DATA / relative).read_bytes()
        for label, relative in repair.INPUT_RELATIVES.items()
    }
    assert repair.main(["--dry-run", "--data-root", str(DATA)]) == 0
    output = capsys.readouterr().out
    assert "mode: DRY-RUN" in output
    assert "state: planned" in output
    assert "dry-run: nothing written" in output
    after = {
        label: (DATA / relative).read_bytes()
        for label, relative in repair.INPUT_RELATIVES.items()
    }
    assert after == before
    assert not (DATA / repair.REPORT_RELATIVE).exists()
    assert not (DATA / repair.QUARANTINE_RELATIVE).exists()


def test_live_postwrite_is_exact_already_applied_noop(
    capsys: pytest.CaptureFixture[str],
) -> None:
    if not LIVE_TATIAN_APPLIED:
        pytest.skip("live repository is still at the Tatian preapply state")
    before = {
        label: (POSTWRITE_DATA / relative).read_bytes()
        for label, relative in repair.INPUT_RELATIVES.items()
    }
    snapshot = repair.load_data_snapshot(POSTWRITE_DATA)
    result = repair.transform(snapshot, _authority())
    assert result.mode == "already_applied"
    assert result.changes == {}
    assert result.quarantine == []
    assert repair.build_outputs(POSTWRITE_DATA, snapshot, result) == {}
    repair.validate_existing_artifacts(snapshot)
    assert repair.main(["--dry-run", "--data-root", str(POSTWRITE_DATA)]) == 0
    output = capsys.readouterr().out
    assert "state: already_applied" in output
    assert "changes: {}" in output
    assert "dry-run: nothing written" in output
    assert {
        label: (POSTWRITE_DATA / relative).read_bytes()
        for label, relative in repair.INPUT_RELATIVES.items()
    } == before
    assert len(
        repair.rows_from_bytes(
            (POSTWRITE_DATA / repair.QUARANTINE_RELATIVE).read_bytes()
        )
    ) == 101
    assert not (POSTWRITE_DATA / repair.TRANSACTION_RELATIVE).exists()


def test_copy_transaction_is_idempotent_and_preserves_readonly_inputs(
    tmp_path: Path,
) -> None:
    data_root = _copy_data_root(tmp_path)
    snapshot = repair.load_data_snapshot(data_root)
    result = repair.transform(snapshot, _authority())
    pdf_before = snapshot.raw["sapere_pdf"]
    repair.write_result(data_root, snapshot, result)
    assert (data_root / repair.REPORT_RELATIVE).is_file()
    assert (data_root / repair.QUARANTINE_RELATIVE).is_file()
    assert not (data_root / repair.TRANSACTION_RELATIVE).exists()
    applied = repair.load_data_snapshot(data_root)
    second = repair.transform(applied, _authority())
    assert second.mode == "already_applied"
    assert second.changes == {}
    assert second.quarantine == []
    repair.validate_existing_artifacts(applied)
    assert repair.build_outputs(data_root, applied, second) == {}
    assert (data_root / repair.INPUT_RELATIVES["sapere_pdf"]).read_bytes() == pdf_before


def test_applied_copy_passes_full_registry_structural_audit(tmp_path: Path) -> None:
    from scripts.audit_sota_registry import audit_registry

    data_root = _copy_data_root(tmp_path)
    snapshot = repair.load_data_snapshot(data_root)
    repair.write_result(data_root, snapshot, repair.transform(snapshot, _authority()))
    repo_root = data_root.parent
    _link_unmodified_repo_inputs(repo_root)
    report = audit_registry(data_root / "goals" / "sota", repo_root)
    assert report["structurally_valid"] is True, report["errors"]
    assert report["metrics"]["issue_statuses"]["open"] >= 1


def test_snapshot_a_drift_aborts_and_preserves_concurrent_bytes(tmp_path: Path) -> None:
    data_root = _copy_data_root(tmp_path)
    snapshot = repair.load_data_snapshot(data_root)
    result = repair.transform(snapshot, _authority())
    manifest = data_root / repair.INPUT_RELATIVES["manifest"]
    drift = manifest.read_bytes() + b"\n"
    manifest.write_bytes(drift)
    with pytest.raises(RuntimeError, match="snapshot-A drift"):
        repair.write_result(data_root, snapshot, result)
    assert manifest.read_bytes() == drift
    assert not (data_root / repair.REPORT_RELATIVE).exists()
    assert not (data_root / repair.QUARANTINE_RELATIVE).exists()
    assert not (data_root / repair.TRANSACTION_RELATIVE).exists()


@pytest.mark.parametrize("label", repair.MUTABLE_LABELS)
def test_preexisting_record_drift_is_rejected_on_every_mutable_surface(
    label: str, tmp_path: Path
) -> None:
    data_root = _copy_data_root(tmp_path)
    path = data_root / repair.INPUT_RELATIVES[label]
    lines = path.read_text(encoding="utf-8").splitlines()
    index = next(i for i, line in enumerate(lines) if line.strip())
    row = json.loads(lines[index])
    row["unexpected_tatian_drift"] = label
    lines[index] = json.dumps(row, ensure_ascii=False, sort_keys=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    snapshot = repair.load_data_snapshot(data_root)
    with pytest.raises(RuntimeError, match="frozen input hashes"):
        repair.transform(snapshot, _authority())


def test_hard_crash_journal_rolls_back_on_recovery(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    data_root = _copy_data_root(tmp_path)
    snapshot = repair.load_data_snapshot(data_root)
    result = repair.transform(snapshot, _authority())
    before = {
        label: (data_root / relative).read_bytes()
        for label, relative in repair.INPUT_RELATIVES.items()
    }
    original_replace = repair._replace_staged_file

    class HardCrash(BaseException):
        pass

    crashed = False

    def crash_after_quarantine(staged: Path, target: Path) -> None:
        nonlocal crashed
        original_replace(staged, target)
        if target == data_root / repair.QUARANTINE_RELATIVE and not crashed:
            crashed = True
            raise HardCrash("simulated process death")

    monkeypatch.setattr(repair, "_replace_staged_file", crash_after_quarantine)
    with pytest.raises(HardCrash):
        repair.write_result(data_root, snapshot, result)
    assert (data_root / repair.TRANSACTION_RELATIVE).exists()
    assert repair.recover_incomplete_transaction(data_root) == "partial_commit_rolled_back"
    assert not (data_root / repair.TRANSACTION_RELATIVE).exists()
    assert not (data_root / repair.REPORT_RELATIVE).exists()
    assert not (data_root / repair.QUARANTINE_RELATIVE).exists()
    assert {
        label: (data_root / relative).read_bytes()
        for label, relative in repair.INPUT_RELATIVES.items()
    } == before


def test_replace_failure_restores_snapshot_and_cleans_transaction(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    data_root = _copy_data_root(tmp_path)
    snapshot = repair.load_data_snapshot(data_root)
    result = repair.transform(snapshot, _authority())
    before = dict(snapshot.raw)
    real_replace = repair._replace_staged_file
    failed = False
    target_failure = data_root / repair.INPUT_RELATIVES["citations"]

    def fail_once(staged: Path, target: Path) -> None:
        nonlocal failed
        if target == target_failure and not failed:
            failed = True
            raise OSError("injected replace failure")
        real_replace(staged, target)

    monkeypatch.setattr(repair, "_replace_staged_file", fail_once)
    with pytest.raises(OSError, match="injected replace failure"):
        repair.write_result(data_root, snapshot, result)
    assert failed is True
    assert not (data_root / repair.TRANSACTION_RELATIVE).exists()
    assert {
        label: (data_root / relative).read_bytes()
        for label, relative in repair.INPUT_RELATIVES.items()
    } == before


def test_fsync_failure_restores_snapshot_and_cleans_transaction(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    data_root = _copy_data_root(tmp_path)
    snapshot = repair.load_data_snapshot(data_root)
    result = repair.transform(snapshot, _authority())
    before = dict(snapshot.raw)
    real_fsync = repair._fsync_directory
    failed = False
    corpus_dir = (data_root / repair.INPUT_RELATIVES["citations"]).parent

    def fail_corpus_once(directory: Path) -> None:
        nonlocal failed
        if directory == corpus_dir and not failed:
            failed = True
            raise OSError("injected fsync failure")
        real_fsync(directory)

    monkeypatch.setattr(repair, "_fsync_directory", fail_corpus_once)
    with pytest.raises(OSError, match="injected fsync failure"):
        repair.write_result(data_root, snapshot, result)
    assert failed is True
    assert not (data_root / repair.TRANSACTION_RELATIVE).exists()
    assert {
        label: (data_root / relative).read_bytes()
        for label, relative in repair.INPUT_RELATIVES.items()
    } == before


def test_rollback_failure_keeps_durable_material_and_second_recovery_succeeds(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    data_root = _copy_data_root(tmp_path)
    snapshot = repair.load_data_snapshot(data_root)
    result = repair.transform(snapshot, _authority())
    before = dict(snapshot.raw)
    real_replace = repair._replace_staged_file
    commit_failed = False
    rollback_failed = False
    commit_target = data_root / repair.INPUT_RELATIVES["nodes"]
    rollback_target = data_root / repair.INPUT_RELATIVES["edges"]

    def fail_commit_then_rollback(staged: Path, target: Path) -> None:
        nonlocal commit_failed, rollback_failed
        if target == commit_target and not commit_failed:
            commit_failed = True
            raise OSError("injected commit failure")
        if target == rollback_target and commit_failed and not rollback_failed:
            rollback_failed = True
            raise OSError("injected rollback failure")
        real_replace(staged, target)

    monkeypatch.setattr(repair, "_replace_staged_file", fail_commit_then_rollback)
    with pytest.raises(OSError, match="injected rollback failure"):
        repair.write_result(data_root, snapshot, result)
    transaction = data_root / repair.TRANSACTION_RELATIVE
    journal = transaction / "journal.json"
    assert commit_failed and rollback_failed
    assert journal.is_file()
    assert (transaction / "backup").is_dir()
    assert json.loads(journal.read_text())["state"] == "rolling_back"

    monkeypatch.setattr(repair, "_replace_staged_file", real_replace)
    assert repair.recover_incomplete_transaction(data_root) == (
        "partial_commit_rolled_back"
    )
    assert not transaction.exists()
    assert {
        label: (data_root / relative).read_bytes()
        for label, relative in repair.INPUT_RELATIVES.items()
    } == before


def test_interwindow_foreign_drift_is_never_overwritten_or_falsely_cleaned(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    data_root = _copy_data_root(tmp_path)
    snapshot = repair.load_data_snapshot(data_root)
    result = repair.transform(snapshot, _authority())
    citations = data_root / repair.INPUT_RELATIVES["citations"]
    report = data_root / repair.REPORT_RELATIVE
    foreign = b'foreign concurrent citations bytes\n'
    real_replace = repair._replace_staged_file
    injected = False

    def inject_after_report(staged: Path, target: Path) -> None:
        nonlocal injected
        real_replace(staged, target)
        if target == report and not injected:
            injected = True
            citations.write_bytes(foreign)

    monkeypatch.setattr(repair, "_replace_staged_file", inject_after_report)
    with pytest.raises(RuntimeError, match="foreign drift blocks rollback"):
        repair.write_result(data_root, snapshot, result)
    transaction = data_root / repair.TRANSACTION_RELATIVE
    journal = transaction / "journal.json"
    assert injected is True
    assert citations.read_bytes() == foreign
    assert journal.is_file()
    assert (transaction / "backup").is_dir()
    journal_payload = json.loads(journal.read_text())
    assert journal_payload["state"] == "recovery_blocked_foreign_drift"
    assert any(
        row["target"] == str(repair.INPUT_RELATIVES["citations"])
        for row in journal_payload["foreign_drift"]
    )

    monkeypatch.setattr(repair, "_replace_staged_file", real_replace)
    with pytest.raises(RuntimeError, match="foreign drift blocks rollback"):
        repair.recover_incomplete_transaction(data_root)
    assert citations.read_bytes() == foreign
    assert journal.is_file()
    assert json.loads(journal.read_text())["state"] == (
        "recovery_blocked_foreign_drift"
    )

    citations.write_bytes(snapshot.raw["citations"])
    assert repair.recover_incomplete_transaction(data_root) == (
        "partial_commit_rolled_back"
    )
    assert not transaction.exists()
    assert {
        label: (data_root / relative).read_bytes()
        for label, relative in repair.INPUT_RELATIVES.items()
    } == snapshot.raw


def test_prepared_committed_and_orphan_recovery_states(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    class HardCrash(BaseException):
        pass

    prepared_root = _copy_data_root(tmp_path / "prepared")
    prepared_snapshot = repair.load_data_snapshot(prepared_root)
    prepared_result = repair.transform(prepared_snapshot, _authority())

    def crash_before_commit(_data_root: Path, _snapshot: repair.DataSnapshot) -> None:
        raise HardCrash("prepared crash")

    monkeypatch.setattr(repair, "_verify_snapshot_a", crash_before_commit)
    with pytest.raises(HardCrash, match="prepared crash"):
        repair.write_result(prepared_root, prepared_snapshot, prepared_result)
    prepared_journal = prepared_root / repair.TRANSACTION_RELATIVE / "journal.json"
    assert json.loads(prepared_journal.read_text())["state"] == "prepared"
    assert repair.recover_incomplete_transaction(prepared_root) == (
        "prepared_stage_removed"
    )

    monkeypatch.undo()
    committed_root = _copy_data_root(tmp_path / "committed")
    committed_snapshot = repair.load_data_snapshot(committed_root)
    committed_result = repair.transform(committed_snapshot, _authority())
    real_cleanup = repair._cleanup_transaction

    def crash_during_cleanup(_data_root: Path) -> None:
        raise HardCrash("committed cleanup crash")

    monkeypatch.setattr(repair, "_cleanup_transaction", crash_during_cleanup)
    with pytest.raises(HardCrash, match="committed cleanup crash"):
        repair.write_result(committed_root, committed_snapshot, committed_result)
    committed_journal = committed_root / repair.TRANSACTION_RELATIVE / "journal.json"
    assert json.loads(committed_journal.read_text())["state"] == "committed"
    monkeypatch.setattr(repair, "_cleanup_transaction", real_cleanup)
    assert repair.recover_incomplete_transaction(committed_root) == (
        "committed_cleanup_finished"
    )

    orphan_root = _copy_data_root(tmp_path / "orphan")
    orphan = orphan_root / repair.TRANSACTION_RELATIVE
    orphan.mkdir(parents=True)
    (orphan / "private-stage").write_bytes(b"stage")
    assert repair.recover_incomplete_transaction(orphan_root) == (
        "orphan_prejournal_stage_removed"
    )
    assert not orphan.exists()


def test_production_write_is_locked_without_root_approval() -> None:
    with pytest.raises(SystemExit):
        repair.main(["--write", "--data-root", str(LIVE_DATA)])


def test_touched_scope_excludes_eval_sorabji_long_and_deploy() -> None:
    targets = {
        str(repair.INPUT_RELATIVES[label]) for label in repair.MUTABLE_LABELS
    } | {str(repair.REPORT_RELATIVE), str(repair.QUARANTINE_RELATIVE)}
    assert not any(
        forbidden in target.lower()
        for target in targets
        for forbidden in ("eval", "sorabji", "long", "deploy")
    )


def test_post_sharples_out_of_scope_surfaces_are_frozen_and_not_outputs() -> None:
    expected = {
        "data/kg/publications.bib": (
            "3e21f88fe06e9e61d7444f724d66a1eabdadd2af27ec42dca22bd8651e94b825"
        ),
        "data/kg/publications_bibtex_report.json": (
            "bba25a9d4d57dd9f82fe1eeb4b410f262312050345fb27fc9fb4b7cce2478e69"
        ),
        "scripts/build_literature_acquisition_manifest.py": (
            "d6519cf1192db6ae3dccb5ebc25599c145f5c472b88e2da4d821c4761333f9f6"
        ),
        "data/literature_acquisition/manifest.jsonl": (
            "e1a5c1bf0ed25615005c9cd3107f3be25235b535faa563e5fa847eb5e9522933"
        ),
        "data/scholarly_sources/manifest.jsonl": (
            "c16553ff02c6cfdcd8402551bcd128fcf8cf0f6d5855a7b38d0be670fbe2a42e"
        ),
        "data/audit/2026-08-24_hildebrandt_p0_repair.json": (
            "cb30674aff6f4a6012cbb4a6266b9d1b49138da615c14147837f29820dfec59c"
        ),
        "data/audit/2026-08-24_hildebrandt_p0_quarantine.jsonl": (
            "3f35c44a02a000db342097a274e50a0398b822c363fb13c59ce0a03a1cbb7714"
        ),
        "data/audit/2026-08-24_alexander_sharples_global_p0.json": (
            "98b9b76ebe1a6f2f608ef52cdc6f7b0d7c96bfb675a0087656859fbba2a6733b"
        ),
        "data/audit/2026-08-24_alexander_sharples_global_p0_quarantine.jsonl": (
            "bc6fa40a1cd461dfe13550d26a03d750aa42c41233c316af608fa3c0ff7d8d63"
        ),
    }
    for relative, wanted in expected.items():
        assert repair.sha256_bytes((ROOT / relative).read_bytes()) == wanted
    normalized = {
        relative.removeprefix("data/")
        for relative in expected
    }
    assert not normalized & repair.EXPECTED_OUTPUT_RELATIVES
