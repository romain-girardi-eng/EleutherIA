from __future__ import annotations

import copy
import json
import os
from collections import Counter
from pathlib import Path

import pytest

import scripts.apply_2026_08_24_sextus_registry_reconciliation as repair
from scripts.audit_sota_registry import audit_registry

ROOT = Path(__file__).resolve().parents[1]
SOTA_ROOT = ROOT / "data/goals/sota"
REGISTRY_ROOT = SOTA_ROOT / "registry"
TARGET_PATHS = [
    repair.SOURCE_REL,
    repair.ISSUE_REL,
    repair.WAVE_REL,
    repair.EVIDENCE_REL,
    repair.VERIFICATION_REL,
    repair.PLAN_REL,
    repair.QUARANTINE_REL,
    repair.REPORT_REL,
]


def load_current():
    return repair.load_files(REGISTRY_ROOT)


def legacy_files() -> dict[Path, list[dict]]:
    files, _snapshot = load_current()
    if not files[repair.EVIDENCE_REL] and not files[repair.VERIFICATION_REL]:
        return files
    quarantine = files[repair.QUARANTINE_REL]
    assert len(quarantine) == 4
    files = copy.deepcopy(files)
    source_index = {
        row["source_id"]: index
        for index, row in enumerate(files[repair.SOURCE_REL])
    }
    for item in quarantine:
        record = copy.deepcopy(item["record"])
        if item["record_type"] == "registry_source_before":
            files[repair.SOURCE_REL][source_index[record["source_id"]]] = record
        elif item["record_type"] == "registry_issue_before":
            files[repair.ISSUE_REL] = [record]
        elif item["record_type"] == "registry_wave_before":
            files[repair.WAVE_REL] = [record]
        else:  # pragma: no cover
            raise AssertionError(item["record_type"])
    for rel in (
        repair.EVIDENCE_REL,
        repair.VERIFICATION_REL,
        repair.PLAN_REL,
        repair.QUARANTINE_REL,
        repair.REPORT_REL,
    ):
        files[rel] = []
    return files


def desired_files():
    facts = repair.cohort_facts(ROOT)
    transformed, changed, quarantine, mode = repair.transform(legacy_files(), facts)
    assert mode == "legacy"
    artifacts = repair.artifact_payloads(changed, quarantine, facts)
    transformed[repair.PLAN_REL] = [json.loads(artifacts[repair.PLAN_REL])]
    transformed[repair.QUARANTINE_REL] = [
        json.loads(line)
        for line in artifacts[repair.QUARANTINE_REL].decode().splitlines()
        if line.strip()
    ]
    transformed[repair.REPORT_REL] = [json.loads(artifacts[repair.REPORT_REL])]
    repair.validate(transformed)
    return transformed, changed, quarantine, artifacts


def write_fixture(root: Path, files: dict[Path, list[dict]]) -> None:
    for rel in TARGET_PATHS:
        target = root / rel
        if not files[rel]:
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        if rel.suffix == ".jsonl":
            target.write_bytes(repair.encode_jsonl(files[rel]))
        else:
            target.write_text(
                json.dumps(files[rel][0], ensure_ascii=False, indent=2, sort_keys=True)
                + "\n"
            )


def test_exact_cohort_facts_and_claim_rewire_loci_are_live() -> None:
    facts = repair.cohort_facts(ROOT)
    assert facts == repair.CohortFacts(
        ph_count=781,
        am_count=2732,
        ph_cohort_sha=repair.PH_COHORT_SHA,
        am_cohort_sha=repair.AM_COHORT_SHA,
        ph_passage_ids_sha=repair.PH_PASSAGE_IDS_SHA,
        am_passage_ids_sha=repair.AM_PASSAGE_IDS_SHA,
    )
    assert set(repair.CLAIM_REWIRES) == {
        "PH I.4",
        "PH I.7",
        "AM VII.19",
        "AM VII.93",
    }


def test_legacy_has_six_obsolete_refs_and_transform_quarantines_them() -> None:
    legacy = legacy_files()
    source_text = json.dumps(legacy[repair.SOURCE_REL], ensure_ascii=False)
    issue = legacy[repair.ISSUE_REL][0]
    assert sum(source_text.count(old) for old in repair.OLD_IDS) == 4
    assert sum(issue["affected_ids"].count(old) for old in repair.OLD_IDS) == 2

    transformed, changed, quarantine, _artifacts = desired_files()
    assert changed == {
        "source": 2,
        "issue": 1,
        "wave": 1,
        "evidence": 2,
        "verification": 9,
    }
    assert len(quarantine) == 4
    active_source = json.dumps(transformed[repair.SOURCE_REL], ensure_ascii=False)
    issue = transformed[repair.ISSUE_REL][0]
    assert not any(old in active_source for old in repair.OLD_IDS)
    assert not any(old in issue["affected_ids"] for old in repair.OLD_IDS)
    assert issue["historical_quarantined_ids"] == repair.OLD_IDS
    assert issue["status"] == "resolved"


def test_sources_remain_partial_and_evidence_does_not_claim_translation_or_human_review() -> None:
    transformed, _changed, _quarantine, _artifacts = desired_files()
    for source in transformed[repair.SOURCE_REL]:
        assert source["coverage"]["state"] == "partial"
        assert "No reviewed modern translation is asserted" in source["notes"]
        assert "No human scholarly sign-off is asserted" in source["notes"]
        assert source["languages"] == ["grc"]
    for evidence in transformed[repair.EVIDENCE_REL]:
        assert evidence["claim_status"] == "verified"
        assert evidence["quotation"]["language"] == "grc"
        assert "does not attest a modern translation" in evidence["notes"]


def test_issue_and_both_evidence_atoms_have_independent_adversarial_proof() -> None:
    transformed, _changed, _quarantine, _artifacts = desired_files()
    reviews = transformed[repair.VERIFICATION_REL]
    assert len(reviews) == 9
    for target in (repair.ISSUE_ID, repair.EVIDENCE_PH, repair.EVIDENCE_AM):
        target_rows = [row for row in reviews if row["target_id"] == target]
        assert {row["stage"] for row in target_rows} == {
            "primary",
            "independent",
            "adversarial",
        }
        assert len(
            {row["verifier"]["independence_group"] for row in target_rows}
        ) == 3
    root_rows = [row for row in reviews if row["stage"] == "independent"]
    assert all("15/15" in row["notes"] for row in root_rows)
    assert all(row["verifier"]["kind"] == "agent" for row in root_rows)


def test_transform_is_idempotent() -> None:
    transformed, _changed, _quarantine, _artifacts = desired_files()
    second, changed, quarantine, mode = repair.transform(
        transformed, repair.cohort_facts(ROOT)
    )
    assert mode == "reconciled"
    assert changed == Counter()
    assert quarantine == []
    assert second == transformed


def test_copy_write_is_transactional_and_second_run_is_noop(tmp_path: Path) -> None:
    registry = tmp_path / "registry"
    write_fixture(registry, legacy_files())
    assert repair.main(["--registry-root", str(registry)]) == 0
    assert not (registry / repair.EVIDENCE_REL).exists()
    assert repair.main(["--write", "--registry-root", str(registry)]) == 0
    files, _snapshot = repair.load_files(registry)
    repair.validate(files)
    assert len(files[repair.QUARANTINE_REL]) == 4
    hashes = {
        rel: repair.file_sha256(registry / rel)
        for rel in TARGET_PATHS
    }
    assert repair.main(["--write", "--registry-root", str(registry)]) == 0
    assert {
        rel: repair.file_sha256(registry / rel)
        for rel in TARGET_PATHS
    } == hashes


def test_transaction_rejects_snapshot_drift(tmp_path: Path) -> None:
    registry = tmp_path / "registry"
    write_fixture(registry, legacy_files())
    files, snapshot = repair.load_files(registry)
    facts = repair.cohort_facts(ROOT)
    transformed, changed, quarantine, _mode = repair.transform(files, facts)
    artifacts = repair.artifact_payloads(changed, quarantine, facts)
    payloads = {
        repair.SOURCE_REL: repair.encode_jsonl(transformed[repair.SOURCE_REL]),
        repair.ISSUE_REL: repair.encode_jsonl(transformed[repair.ISSUE_REL]),
        repair.WAVE_REL: repair.encode_jsonl(transformed[repair.WAVE_REL]),
        repair.EVIDENCE_REL: repair.encode_jsonl(transformed[repair.EVIDENCE_REL]),
        repair.VERIFICATION_REL: repair.encode_jsonl(
            transformed[repair.VERIFICATION_REL]
        ),
        **artifacts,
    }
    source = registry / repair.SOURCE_REL
    drift = source.read_bytes() + b"\n"
    source.write_bytes(drift)
    with pytest.raises(RuntimeError, match="drift since snapshot A"):
        repair.commit_registry(registry, snapshot, payloads)
    assert source.read_bytes() == drift
    assert not (registry / repair.EVIDENCE_REL).exists()


def test_transaction_rolls_back_injected_replace_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    registry = tmp_path / "registry"
    write_fixture(registry, legacy_files())
    files, snapshot = repair.load_files(registry)
    facts = repair.cohort_facts(ROOT)
    transformed, changed, quarantine, _mode = repair.transform(files, facts)
    artifacts = repair.artifact_payloads(changed, quarantine, facts)
    payloads = {
        repair.SOURCE_REL: repair.encode_jsonl(transformed[repair.SOURCE_REL]),
        repair.ISSUE_REL: repair.encode_jsonl(transformed[repair.ISSUE_REL]),
        repair.WAVE_REL: repair.encode_jsonl(transformed[repair.WAVE_REL]),
        repair.EVIDENCE_REL: repair.encode_jsonl(transformed[repair.EVIDENCE_REL]),
        repair.VERIFICATION_REL: repair.encode_jsonl(
            transformed[repair.VERIFICATION_REL]
        ),
        **artifacts,
    }
    real_replace = os.replace
    calls = 0

    def fail_fourth(source: str | Path, target: str | Path) -> None:
        nonlocal calls
        calls += 1
        if calls == 4:
            raise OSError("injected registry rollback")
        real_replace(source, target)

    monkeypatch.setattr(repair.os, "replace", fail_fourth)
    with pytest.raises(RuntimeError, match="rollback succeeded"):
        repair.commit_registry(registry, snapshot, payloads)
    for rel, before in snapshot.items():
        path = registry / rel
        actual = path.read_bytes() if path.exists() else None
        assert actual == before


def test_current_phase_and_full_registry_audit() -> None:
    files, _snapshot = load_current()
    if files[repair.EVIDENCE_REL]:
        repair.validate(files)
        report = audit_registry(SOTA_ROOT, ROOT)
        assert report["structurally_valid"] is True, report["errors"]
        issue = files[repair.ISSUE_REL][0]
        assert issue["status"] == "resolved"
    else:
        transformed, _changed, _quarantine, _artifacts = desired_files()
        repair.validate(transformed)
