from __future__ import annotations

import copy
import shutil
from pathlib import Path

import scripts.apply_2026_08_24_origen_exhortatio_registry_reconciliation as repair
from scripts.audit_sota_registry import audit_registry

ROOT = Path(__file__).resolve().parents[1]
SOTA = ROOT / "data/goals/sota"
REGISTRY = SOTA / "registry"


def load_files(root: Path = REGISTRY):
    return {
        rel: repair.read_jsonl(root / rel)
        for rel in (
            repair.SOURCE_REL,
            repair.ISSUE_REL,
            repair.WAVE_REL,
            repair.EVIDENCE_REL,
            repair.VERIFICATION_REL,
        )
    }


def legacy_files():
    files = copy.deepcopy(load_files())
    source = repair.find_one(files[repair.SOURCE_REL], "source_id", repair.SOURCE_ID)
    issue = repair.find_one(files[repair.ISSUE_REL], "issue_id", repair.ISSUE_ID)
    wave = repair.find_one(files[repair.WAVE_REL], "wave_id", repair.WAVE_ID)
    current_source = repair.find_one(load_files()[repair.SOURCE_REL], "source_id", repair.SOURCE_ID)
    source.clear()
    source.update(repair.legacy_source_record(current_source))
    current_issue = repair.find_one(load_files()[repair.ISSUE_REL], "issue_id", repair.ISSUE_ID)
    issue.clear()
    issue.update(repair.legacy_issue_record(current_issue))
    current_wave = repair.find_one(load_files()[repair.WAVE_REL], "wave_id", repair.WAVE_ID)
    wave.clear()
    wave.update(repair.legacy_wave_record(current_wave))
    files[repair.EVIDENCE_REL] = []
    files[repair.VERIFICATION_REL] = []
    return files


def reconciled_from_legacy():
    result, changed, mode = repair.transform(legacy_files())
    assert mode == "legacy"
    assert sum(changed.values()) == 7
    repair.validate(result)
    return result


def test_transform_adds_exact_registry_cohort() -> None:
    result, changed, mode = repair.transform(legacy_files())
    assert mode == "legacy"
    assert changed == {
        "source": 1,
        "issue": 1,
        "wave": 1,
        "evidence": 1,
        "verification": 3,
    }
    repair.validate(result)


def test_source_records_resolved_identity_but_partial_coverage() -> None:
    files = reconciled_from_legacy()
    source = repair.find_one(files[repair.SOURCE_REL], "source_id", repair.SOURCE_ID)
    assert source["identity_status"] == "authority_verified"
    assert source["coverage"]["state"] == "partial"
    assert len(source["coverage"]["kg_node_ids"]) == 52
    assert "manifest remains mislabeled" not in source["coverage"]["basis"]
    assert "Historical state retained" in source["notes"]
    artifact_hashes = {
        item["locator"]: item.get("sha256")
        for item in source["acquisition"]["artifacts"]
    }
    assert artifact_hashes[
        "data/audit/2026-08-24_origen_exhortatio_identity_repair.json"
    ] == repair.REPAIR_REPORT_SHA256
    assert artifact_hashes[
        "data/audit/2026-08-24_origen_exhortatio_node_aliases.json"
    ] == repair.ALIASES_SHA256


def test_issue_stays_open_and_preserves_ten_cohort_history() -> None:
    files = reconciled_from_legacy()
    issue = repair.find_one(files[repair.ISSUE_REL], "issue_id", repair.ISSUE_ID)
    assert issue["status"] == "open"
    assert issue["affected_count"] == 10
    assert "Historical opening scope: ten" in issue["summary"]
    assert "Exhortatio ad martyrium cohort is resolved" in issue["summary"]
    assert "nine De principiis, Philocalia and Commentary on Romans" in issue["summary"]
    assert "Exhortatio Wave 0.2 is resolved" in issue["resolution_criteria"]
    assert "adjudication" not in issue


def test_atomic_evidence_has_all_51_uuids_hashes_and_targets() -> None:
    files = reconciled_from_legacy()
    evidence = repair.find_one(
        files[repair.EVIDENCE_REL], "evidence_id", repair.EVIDENCE_ID
    )
    assert evidence["claim_status"] == "verified"
    assert evidence["attestation"] == "direct"
    assert evidence["quotation"]["text_sha256"] == repair.NFC_TEXT_COHORT_SHA256
    assert evidence["quotation"]["corpus_passage_ids"] == repair.CORPUS_PASSAGE_IDS
    assert len(set(evidence["quotation"]["corpus_passage_ids"])) == 51
    assert evidence["kg_targets"] == [
        "work_origen_exhortation_martyrdom",
        *repair.PASSAGE_NODE_IDS,
    ]
    assert repair.OGL_COMMIT in evidence["locator"]["edition_or_witness"]
    assert repair.OGL_CTS_SHA256 in evidence["notes"]
    assert repair.OGL_TEI_SHA256 in evidence["notes"]


def test_evidence_has_primary_independent_and_adversarial_reviews() -> None:
    files = reconciled_from_legacy()
    reviews = files[repair.VERIFICATION_REL]
    assert {row["stage"] for row in reviews} == {
        "primary",
        "independent",
        "adversarial",
    }
    assert {row["verdict"] for row in reviews} == {"pass"}
    assert len({row["verifier"]["independence_group"] for row in reviews}) == 3
    independent = next(row for row in reviews if row["stage"] == "independent")
    assert independent["verifier"]["verifier_id"] == "root_exhortatio_wave02_review"
    adversarial = next(row for row in reviews if row["stage"] == "adversarial")
    assert adversarial["verifier"]["kind"] == "deterministic_tool"


def test_wave00_references_evidence_and_non_targets_are_unchanged() -> None:
    original = legacy_files()
    files = reconciled_from_legacy()
    wave = repair.find_one(files[repair.WAVE_REL], "wave_id", repair.WAVE_ID)
    assert repair.EVIDENCE_ID in wave["evidence_ids"]

    for rel, id_field, target_id in (
        (repair.SOURCE_REL, "source_id", repair.SOURCE_ID),
        (repair.ISSUE_REL, "issue_id", repair.ISSUE_ID),
        (repair.WAVE_REL, "wave_id", repair.WAVE_ID),
    ):
        before = {row[id_field]: row for row in original[rel]}
        after = {row[id_field]: row for row in files[rel]}
        for key in before.keys() - {target_id}:
            assert after[key] == before[key]


def test_reconciled_transform_is_idempotent() -> None:
    first = reconciled_from_legacy()
    second, changed, mode = repair.transform(first)
    assert second == first
    assert changed == {}
    assert mode == "reconciled"


def test_transactional_temp_write_audits_and_is_idempotent(
    tmp_path: Path, monkeypatch
) -> None:
    sota_root = tmp_path / "sota"
    shutil.copytree(SOTA, sota_root)
    registry_root = sota_root / "registry"
    legacy = legacy_files()
    for rel, rows in legacy.items():
        path = registry_root / rel
        if rows:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(repair.encode_jsonl(rows))
        else:
            path.unlink(missing_ok=True)
    monkeypatch.setattr(
        repair,
        "LEGACY_FILE_SHA256",
        {
            rel.as_posix(): repair.file_sha256(registry_root / rel)
            for rel in (repair.SOURCE_REL, repair.ISSUE_REL, repair.WAVE_REL)
        },
    )
    baseline_report = audit_registry(sota_root, repo_root=ROOT)

    before = {
        rel: repair.file_sha256(registry_root / rel)
        for rel in (repair.SOURCE_REL, repair.ISSUE_REL, repair.WAVE_REL)
    }
    assert repair.main(["--registry-root", str(registry_root)]) == 0
    assert before == {
        rel: repair.file_sha256(registry_root / rel)
        for rel in (repair.SOURCE_REL, repair.ISSUE_REL, repair.WAVE_REL)
    }
    assert not (registry_root / repair.EVIDENCE_REL).exists()

    assert repair.main(["--write", "--registry-root", str(registry_root)]) == 0
    report = audit_registry(sota_root, repo_root=ROOT)
    assert set(report["errors"]) <= set(baseline_report["errors"])
    assert not [
        error
        for error in report["errors"]
        if repair.EVIDENCE_ID in error or "origen_exhortatio_20260824" in error
    ]
    assert report["metrics"]["active_evidence_fully_reviewed"] == (
        baseline_report["metrics"]["active_evidence_fully_reviewed"] + 1
    )
    hashes = {
        rel: repair.file_sha256(registry_root / rel)
        for rel in (
            repair.SOURCE_REL,
            repair.ISSUE_REL,
            repair.WAVE_REL,
            repair.EVIDENCE_REL,
            repair.VERIFICATION_REL,
        )
    }
    assert repair.main(["--write", "--registry-root", str(registry_root)]) == 0
    assert hashes == {
        rel: repair.file_sha256(registry_root / rel) for rel in hashes
    }
