from __future__ import annotations

import copy
import shutil
from pathlib import Path

import pytest

import scripts.apply_2026_08_24_aristotle_en_iii_5_manifest_gap_followup as repair

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
FOLLOWUP_QUARANTINE = DATA / repair.QUARANTINE_RELATIVE
LONG_QUARANTINE = (
    DATA / "audit/2026-08-24_long_sedley_vol2_p0_quarantine.jsonl"
)
HISTORICAL_LONG_EVIDENCE_ID = "ev_sec_long_sedley_sections55_62_pp332_388"
HISTORICAL_LONG_EVIDENCE_SHA256 = (
    "b87da1c828ff734477adb1a82002ec75d3513b7a3a5c74315fe2cba6ca1c34b9"
)


def _by(rows: list[dict], field: str) -> dict[str, dict]:
    return {str(row.get(field) or ""): row for row in rows}


def _immutable(row: dict) -> tuple:
    return tuple(
        row.get(field)
        for field in (
            "text_content",
            "passage_id",
            "canonical_ref",
            "cts_urn",
            "sequence_number",
        )
    )


def _historical_long_evidence() -> dict:
    """Load the exact Long dependency removed by the later Long transaction."""

    matches = [
        row["record"]
        for row in repair.read_jsonl(LONG_QUARANTINE)
        if row.get("record_type") == "registry_evidence_removed"
        and row.get("record", {}).get("evidence_id")
        == HISTORICAL_LONG_EVIDENCE_ID
    ]
    assert len(matches) == 1
    record = matches[0]
    assert repair.record_hash(record) == HISTORICAL_LONG_EVIDENCE_SHA256
    return copy.deepcopy(record)


def _pre_followup_snapshot() -> repair.DataSnapshot:
    """Reverse the committed follow-up from its 51 authoritative before-images."""

    applied = repair.load_data_snapshot(DATA)
    repair._validate_existing_artifacts(applied)
    rows = copy.deepcopy(applied.rows)
    quarantine = repair.read_jsonl(FOLLOWUP_QUARANTINE)
    before_config = {
        "corpus_passage_before": ("passages", "passage_id"),
        "kg_node_before": ("nodes", "node_id"),
        "corpus_manifest_before": ("manifest", "canonical_id"),
        "registry_source_before": ("registry_sources", "source_id"),
        "registry_evidence_before": ("registry_evidence", "evidence_id"),
        "registry_issue_before": ("registry_issues", "issue_id"),
        "registry_wave_before": ("registry_waves", "wave_id"),
    }
    absence_config = {
        "corpus_manifest_absence_before": ("manifest", "canonical_id"),
        "registry_issue_absence_before": ("registry_issues", "issue_id"),
        "registry_verification_absence_before": (
            "registry_verifications",
            "verification_id",
        ),
    }
    for entry in quarantine:
        config = before_config.get(str(entry.get("record_type") or ""))
        if config is None:
            continue
        label, field = config
        record = copy.deepcopy(entry["record"])
        identifier = str(record[field])
        matches = [
            index
            for index, row in enumerate(rows[label])
            if str(row.get(field) or "") == identifier
        ]
        assert len(matches) == 1
        rows[label][matches[0]] = record
    for entry in quarantine:
        config = absence_config.get(str(entry.get("record_type") or ""))
        if config is None:
            continue
        label, field = config
        identifier = str(entry[field])
        before = len(rows[label])
        rows[label] = [
            row for row in rows[label] if str(row.get(field) or "") != identifier
        ]
        assert len(rows[label]) == before - 1

    # Aristotle's historical wave referenced this discovery unit.  Long's later
    # transaction split and removed it, so a composable post-Long reconstruction
    # must restore the exact quarantined record in the temporary Snapshot-A.
    historical_long = _historical_long_evidence()
    long_matches = [
        row
        for row in rows["registry_evidence"]
        if row.get("evidence_id") == HISTORICAL_LONG_EVIDENCE_ID
    ]
    assert len(long_matches) <= 1
    if long_matches:
        assert long_matches == [historical_long]
    else:
        rows["registry_evidence"].append(historical_long)

    raw = dict(applied.raw)
    for label in repair.MUTABLE_LABELS:
        raw[label] = repair._jsonl_content_preserving(
            applied.raw[label], rows[label], repair.JSONL_KEYS[label], label
        )
    return repair.DataSnapshot(
        rows=rows,
        raw=raw,
        optional_artifacts={
            repair.QUARANTINE_RELATIVE: None,
            repair.REPORT_RELATIVE: None,
        },
    )


def _copy_data_root(tmp_path: Path) -> Path:
    data_root = tmp_path / "repo" / "data"
    shutil.copytree(DATA / "goals" / "sota", data_root / "goals" / "sota")
    snapshot = _pre_followup_snapshot()
    for label, relative in repair.INPUT_RELATIVES.items():
        target = data_root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(snapshot.raw[label])
    return data_root


def _link_unmodified_repo_inputs(repo_root: Path) -> None:
    data_root = repo_root / "data"
    for source in DATA.iterdir():
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
    for source in (DATA / "audit").iterdir():
        target = audit_target / source.name
        if not target.exists():
            target.symlink_to(source, target_is_directory=source.is_dir())
    for name in ("docs", "scripts", "tests"):
        (repo_root / name).symlink_to(ROOT / name, target_is_directory=True)


def test_prospective_split_is_exactly_one_bobzien_and_sixteen_unresolved() -> None:
    snapshot = _pre_followup_snapshot()
    result = repair.transform(snapshot)
    assert result.mode == "planned"
    assert result.quarantine == repair.read_jsonl(FOLLOWUP_QUARANTINE)
    assert result.changes == {
        "corpus_passages_enriched": 2,
        "kg_nodes_enriched": 1,
        "legacy_corpus_rows_failclosed": 16,
        "legacy_kg_nodes_failclosed": 16,
        "manifest_rows_added": 2,
        "manifest_rows_enriched": 1,
        "registry_evidence_updated": 2,
        "registry_issues_added": 1,
        "registry_issues_updated": 1,
        "registry_sources_updated": 2,
        "registry_verifications_added": 5,
        "registry_waves_updated": 2,
    }

    before = _by(snapshot.rows["passages"], "passage_id")
    after = _by(result.rows["passages"], "passage_id")
    for passage_id in (repair.PASSAGE_1113_GRC, repair.PASSAGE_1113_ENG):
        assert _immutable(after[passage_id]) == _immutable(before[passage_id])
    changed_passages = {
        repair.PASSAGE_1113_GRC,
        repair.PASSAGE_1113_ENG,
        *repair.LEGACY_ENGLISH_PASSAGE_IDS,
    }
    for passage_id in repair.LEGACY_ENGLISH_PASSAGE_IDS:
        assert _immutable(after[passage_id]) == _immutable(before[passage_id])
    assert [
        row
        for row in result.rows["passages"]
        if row["passage_id"] not in changed_passages
    ] == [
        row
        for row in snapshot.rows["passages"]
        if row["passage_id"] not in changed_passages
    ]

    bobzien = [
        row
        for row in result.rows["passages"]
        if row.get("work_canonical_id") == repair.BOBZIEN_MANIFEST_ID
    ]
    legacy = [
        row
        for row in result.rows["passages"]
        if row.get("work_canonical_id") == repair.LEGACY_ENGLISH_MANIFEST_ID
    ]
    assert [row["passage_id"] for row in bobzien] == [repair.PASSAGE_1113_ENG]
    assert len(legacy) == 16
    assert all(row.get("translator") != "Susanne Bobzien" for row in legacy)
    assert all(
        row.get("source_publication_id") != repair.PUBLICATION_NODE for row in legacy
    )
    assert all(repair.DOI not in repair.canonical_json(row) for row in legacy)
    CitabilityTier, evidence_policy = repair.load_citability_policy()
    assert all(
        evidence_policy(row).tier is CitabilityTier.DISCOVERABLE_ONLY
        for row in legacy
    )

    english = bobzien[0]
    assert english["language"] == "eng"
    assert english["passage_role"] == "translation"
    assert english["source_passage_id"] == repair.PASSAGE_1113_GRC
    assert english["text_sha256_nfc"] == repair.text_hash(repair.ENGLISH_1113)
    assert english["rights"] == repair.RIGHTS_CAVEAT
    assert "edition_urn" not in english
    assert "source_artifact_sha256" not in english

    manifests = _by(result.rows["manifest"], "canonical_id")
    assert manifests[repair.BOBZIEN_MANIFEST_ID] == repair.desired_bobzien_manifest()
    assert manifests[repair.BOBZIEN_MANIFEST_ID]["cts_urn"] == repair.WORK_URN
    assert manifests[repair.LEGACY_ENGLISH_MANIFEST_ID]["passages"] == 16
    assert (
        manifests[repair.LEGACY_ENGLISH_MANIFEST_ID]["status"]
        == "identity_unresolved_non_citable"
    )
    assert manifests[repair.LEGACY_ENGLISH_MANIFEST_ID]["source"] == ""
    assert (
        manifests[repair.LEGACY_ENGLISH_MANIFEST_ID]["translator"]
        == "unknown_not_established"
    )
    assert manifests[repair.GREEK_MANIFEST_ID]["passages"] == 117
    assert manifests[repair.GREEK_MANIFEST_ID]["language"] == "grc"

    before_nodes = _by(snapshot.rows["nodes"], "node_id")
    after_nodes = _by(result.rows["nodes"], "node_id")
    changed_nodes = {repair.ENGLISH_NODE_1113, *repair.LEGACY_ENGLISH_NODE_IDS}
    assert [
        row
        for row in result.rows["nodes"]
        if repair.node_id(row) not in changed_nodes
    ] == [
        row
        for row in snapshot.rows["nodes"]
        if repair.node_id(row) not in changed_nodes
    ]
    assert (
        after_nodes[repair.ENGLISH_NODE_1113]["description"]
        == before_nodes[repair.ENGLISH_NODE_1113]["description"]
        == repair.ENGLISH_1113
    )
    node_data = repair.metadata(after_nodes[repair.ENGLISH_NODE_1113])
    assert node_data["manifestation_id"] == repair.BOBZIEN_MANIFEST_ID
    assert node_data["intellectual_work_cts_urn"] == repair.WORK_URN
    assert node_data["work_canonical_id"] == repair.KG_WORK_CANONICAL_ID
    assert "edition" not in node_data
    for wanted in repair.LEGACY_ENGLISH_NODE_IDS:
        legacy_node = after_nodes[wanted]
        legacy_data = repair.metadata(legacy_node)
        assert legacy_data["citability"] == "discoverable_only"
        assert legacy_data["passage_role"] == "unresolved_english_research_record"
        assert evidence_policy(legacy_node).tier is not CitabilityTier.CITABLE

    assert result.rows["edges"] == snapshot.rows["edges"]
    assert result.rows["citations"] == snapshot.rows["citations"]
    assert result.validation["bobzien_manifestation_rows"] == 1
    assert result.validation["legacy_unresolved_rows"] == 16
    assert result.validation["legacy_non_citable_snapshot_nodes"] == 16
    assert result.validation["eval_gold_admission"]["status"] == "valid"
    assert result.validation["corpus_violations"] == 0
    assert result.validation["snapshot_target_violations"] == 0
    assert result.validation["work_child_mismatches"] == 0
    assert result.validation["work_id_collisions"] == 0


def test_registry_records_partial_coverage_followup_and_real_open_debt() -> None:
    result = repair.transform(_pre_followup_snapshot())
    sources = _by(result.rows["registry_sources"], "source_id")
    evidence = _by(result.rows["registry_evidence"], "evidence_id")
    issues = _by(result.rows["registry_issues"], "issue_id")
    waves = _by(result.rows["registry_waves"], "wave_id")
    verifications = _by(result.rows["registry_verifications"], "verification_id")

    bobzien_source = sources[repair.BOBZIEN_SOURCE_ID]
    assert bobzien_source["coverage"]["state"] == "partial"
    assert bobzien_source["acquisition"]["status"] == "missing"
    assert bobzien_source["coverage"]["corpus_manifestation_ids"] == [
        repair.BOBZIEN_MANIFEST_ID
    ]
    assert bobzien_source["coverage"]["corpus_passage_ids"] == [
        repair.PASSAGE_1113_ENG
    ]

    exact = evidence[repair.BOBZIEN_EVIDENCE_ID]
    assert exact["claim_status"] == "in_review"
    assert exact["quotation"]["corpus_passage_ids"] == [repair.PASSAGE_1113_ENG]
    assert exact["quotation"]["rights"] == repair.RIGHTS_CAVEAT
    assert exact["locator"]["page_map_status"] == "unmapped"
    assert exact["review_state"]["independent_review"] == "pending_root_review"
    assert exact["review_state"]["printed_page_concordance"] == "pending"

    resolved = issues[repair.RESOLVED_ISSUE_ID]
    assert resolved["status"] == "resolved"
    assert any(
        followup["opened_issue_id"] == repair.LEGACY_ISSUE_ID
        for followup in resolved["followups"]
    )
    legacy = issues[repair.LEGACY_ISSUE_ID]
    assert legacy["status"] == "open"
    assert legacy["affected_count"] == 17
    assert legacy["affected_record_count"] == 16
    assert legacy["affected_id_count"] == 17
    assert len(legacy["affected_ids"]) == 17
    assert len(legacy["affected_corpus_ids"]) == 17
    assert legacy["affected_corpus_ids"][0] == repair.LEGACY_ENGLISH_MANIFEST_ID
    assert repair.RESOLVED_ISSUE_ID not in waves[repair.WAVE_01]["blocked_by"]
    assert repair.LEGACY_ISSUE_ID in waves[repair.WAVE_01]["blocked_by"]
    assert all(
        wanted["verification_id"] in verifications
        for wanted in repair.NEW_VERIFICATIONS
    )
    assert result.report["registry"]["bobzien_source_coverage"] == "partial"
    assert result.report["registry"]["full_article_acquisition"] == "missing"
    assert len(result.quarantine) == 51
    assert sum(
        row["record_type"] == "corpus_passage_before"
        for row in result.quarantine
    ) == 18
    assert sum(
        row["record_type"] == "kg_node_before" for row in result.quarantine
    ) == 17


def test_dry_run_is_byte_for_byte_noop(capsys: pytest.CaptureFixture[str]) -> None:
    before = {
        label: (DATA / relative).read_bytes()
        for label, relative in repair.INPUT_RELATIVES.items()
    }
    artifact_before = {
        relative: (DATA / relative).read_bytes()
        for relative in (repair.REPORT_RELATIVE, repair.QUARANTINE_RELATIVE)
    }
    assert repair.main(["--dry-run", "--data-root", str(DATA)]) == 0
    output = capsys.readouterr().out
    assert "mode: DRY-RUN" in output
    assert "state: already_applied" in output
    assert "dry-run: nothing written" in output
    after = {
        label: (DATA / relative).read_bytes()
        for label, relative in repair.INPUT_RELATIVES.items()
    }
    assert after == before
    assert {
        relative: (DATA / relative).read_bytes()
        for relative in (repair.REPORT_RELATIVE, repair.QUARANTINE_RELATIVE)
    } == artifact_before


def test_live_postwrite_is_exact_record_scoped_already_applied_noop() -> None:
    prospective = repair.transform(_pre_followup_snapshot())
    live = repair.load_data_snapshot(DATA)
    before = {
        label: (DATA / relative).read_bytes()
        for label, relative in repair.INPUT_RELATIVES.items()
    }

    target_records = {
        "passages": (
            "passage_id",
            {
                repair.PASSAGE_1113_GRC,
                repair.PASSAGE_1113_ENG,
                *repair.LEGACY_ENGLISH_PASSAGE_IDS,
            },
        ),
        "nodes": (
            "node_id",
            {repair.ENGLISH_NODE_1113, *repair.LEGACY_ENGLISH_NODE_IDS},
        ),
        "manifest": (
            "canonical_id",
            {
                repair.GREEK_MANIFEST_ID,
                repair.BOBZIEN_MANIFEST_ID,
                repair.LEGACY_ENGLISH_MANIFEST_ID,
            },
        ),
        "registry_sources": (
            "source_id",
            {repair.ANCIENT_SOURCE_ID, repair.BOBZIEN_SOURCE_ID},
        ),
        "registry_evidence": (
            "evidence_id",
            {repair.ANCIENT_EVIDENCE_ID, repair.BOBZIEN_EVIDENCE_ID},
        ),
        "registry_issues": (
            "issue_id",
            {repair.RESOLVED_ISSUE_ID, repair.LEGACY_ISSUE_ID},
        ),
        "registry_verifications": (
            "verification_id",
            {row["verification_id"] for row in repair.NEW_VERIFICATIONS},
        ),
    }
    for label, (field, identifiers) in target_records.items():
        expected = {
            row[field]: row
            for row in prospective.rows[label]
            if row.get(field) in identifiers
        }
        current = {
            row[field]: row
            for row in live.rows[label]
            if row.get(field) in identifiers
        }
        assert expected.keys() == current.keys() == identifiers
        assert current == expected

    waves = _by(live.rows["registry_waves"], "wave_id")
    assert repair.desired_wave_00(waves[repair.WAVE_00]) == waves[repair.WAVE_00]
    assert repair.desired_wave_01(waves[repair.WAVE_01]) == waves[repair.WAVE_01]

    result = repair.transform(live)
    assert result.mode == "already_applied"
    assert result.changes == {}
    assert result.quarantine == []
    assert repair.build_outputs(DATA, live, result) == {}
    repair._validate_existing_artifacts(live)
    assert {
        label: (DATA / relative).read_bytes()
        for label, relative in repair.INPUT_RELATIVES.items()
    } == before


def test_transaction_write_on_copy_is_idempotent_and_preserves_readonly_inputs(
    tmp_path: Path,
) -> None:
    data_root = _copy_data_root(tmp_path)
    snapshot = repair.load_data_snapshot(data_root)
    result = repair.transform(snapshot)
    readonly_before = {
        label: snapshot.raw[label]
        for label in ("edges", "citations", "publications_bib")
    }
    repair.write_result(data_root, snapshot, result)
    assert (data_root / repair.REPORT_RELATIVE).is_file()
    assert (data_root / repair.QUARANTINE_RELATIVE).is_file()
    assert not (data_root / repair.TRANSACTION_RELATIVE).exists()
    assert not (data_root / repair.LOCK_RELATIVE).exists()

    applied_snapshot = repair.load_data_snapshot(data_root)
    second = repair.transform(applied_snapshot)
    assert second.mode == "already_applied"
    assert second.changes == {}
    assert second.quarantine == []
    repair._validate_existing_artifacts(applied_snapshot)
    assert repair.build_outputs(data_root, applied_snapshot, second) == {}
    for label, raw in readonly_before.items():
        assert (data_root / repair.INPUT_RELATIVES[label]).read_bytes() == raw


def test_applied_copy_passes_full_registry_structural_audit(tmp_path: Path) -> None:
    from scripts.audit_sota_registry import audit_registry

    data_root = _copy_data_root(tmp_path)
    snapshot = repair.load_data_snapshot(data_root)
    repair.write_result(data_root, snapshot, repair.transform(snapshot))
    repo_root = data_root.parent
    _link_unmodified_repo_inputs(repo_root)
    report = audit_registry(data_root / "goals" / "sota", repo_root)
    assert report["structurally_valid"] is True, report["errors"]
    assert report["errors"] == []
    assert report["metrics"]["issues"] >= 1
    assert report["metrics"]["source_coverage_states"]["partial"] >= 1


def test_snapshot_a_drift_aborts_without_overwriting_the_drift(tmp_path: Path) -> None:
    data_root = _copy_data_root(tmp_path)
    snapshot = repair.load_data_snapshot(data_root)
    result = repair.transform(snapshot)
    manifest_path = data_root / repair.INPUT_RELATIVES["manifest"]
    drift = manifest_path.read_bytes() + b"\n"
    manifest_path.write_bytes(drift)
    with pytest.raises(RuntimeError, match="snapshot-A drift"):
        repair.write_result(data_root, snapshot, result)
    assert manifest_path.read_bytes() == drift
    assert not (data_root / repair.REPORT_RELATIVE).exists()
    assert not (data_root / repair.QUARANTINE_RELATIVE).exists()
    assert not (data_root / repair.TRANSACTION_RELATIVE).exists()
    assert not (data_root / repair.LOCK_RELATIVE).exists()


def test_hard_crash_journal_rolls_back_on_next_write(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    data_root = _copy_data_root(tmp_path)
    snapshot = repair.load_data_snapshot(data_root)
    result = repair.transform(snapshot)
    before = {
        label: (data_root / relative).read_bytes()
        for label, relative in repair.INPUT_RELATIVES.items()
    }
    original_replace = repair._replace_staged_file

    class HardCrash(BaseException):
        pass

    crashed = False

    def crash_after_first_public_replace(staged: Path, target: Path) -> None:
        nonlocal crashed
        original_replace(staged, target)
        if target == data_root / repair.QUARANTINE_RELATIVE and not crashed:
            crashed = True
            raise HardCrash("simulated process death")

    monkeypatch.setattr(repair, "_replace_staged_file", crash_after_first_public_replace)
    with pytest.raises(HardCrash):
        repair.write_result(data_root, snapshot, result)
    assert (data_root / repair.TRANSACTION_RELATIVE).exists()
    assert (data_root / repair.QUARANTINE_RELATIVE).exists()

    recovery = repair.recover_incomplete_transaction(data_root)
    assert recovery == "partial_commit_rolled_back"
    assert not (data_root / repair.TRANSACTION_RELATIVE).exists()
    assert not (data_root / repair.QUARANTINE_RELATIVE).exists()
    assert not (data_root / repair.REPORT_RELATIVE).exists()
    after = {
        label: (data_root / relative).read_bytes()
        for label, relative in repair.INPUT_RELATIVES.items()
    }
    assert after == before


def test_production_write_requires_explicit_approval() -> None:
    with pytest.raises(SystemExit):
        repair.main(["--write", "--data-root", str(DATA)])


def test_eval_files_are_outside_transaction_scope() -> None:
    transaction_targets = {
        str(relative) for relative in repair.INPUT_RELATIVES.values()
    } | {str(repair.REPORT_RELATIVE), str(repair.QUARANTINE_RELATIVE)}
    assert not any(target.startswith("tests/eval/") for target in transaction_targets)
    assert "eval" not in repair.MUTABLE_LABELS
