from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from scripts.audit_sota_registry import (
    audit_registry,
    has_independent_pair,
    input_set_sha256,
    recompute_wave_score,
)

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "data/goals/sota"


def review(
    stage: str,
    verifier_id: str,
    independence_group: str,
    verdict: str = "pass",
) -> dict:
    return {
        "stage": stage,
        "verdict": verdict,
        "verifier": {
            "verifier_id": verifier_id,
            "independence_group": independence_group,
        },
    }


def test_committed_registry_is_valid_but_makes_no_false_completion_claim() -> None:
    report = audit_registry(REGISTRY, ROOT)
    assert report["structurally_valid"] is True, report["errors"]
    assert report["exit_ready"] is False
    assert report["next_wave"]["wave_id"] == "wave_00_known_factual_blockers"
    assert report["metrics"]["active_evidence_fully_reviewed"] >= 1
    gate_status = {gate["gate_id"]: gate["status"] for gate in report["gates"]}
    assert gate_status["gate_registry_integrity"] == "pass"
    assert gate_status["gate_zero_known_factual_errors"] == "fail"
    assert gate_status["gate_human_release_signoff"] == "fail"


def test_bobzien_2013_is_not_conflated_with_distinct_2014_chapter() -> None:
    report = audit_registry(REGISTRY, ROOT)
    wave = report["next_wave"]
    assert "issue_aristotle_en_1113b7_shared_uuid_contamination" in wave[
        "issue_ids"
    ]

    source_lines = (
        REGISTRY / "registry/sources/seed_priority_20260824.jsonl"
    ).read_text(encoding="utf-8")
    assert '"source_id":"src_sec_bobzien_2013_found_translation"' in source_lines
    assert '"source_id":"src_sec_bobzien_2014_found_translation"' not in source_lines
    found_record = json.loads(
        next(
            line
            for line in source_lines.splitlines()
            if '"source_id":"src_sec_bobzien_2013_found_translation"' in line
        )
    )
    assert found_record["canonical_identifiers"]["kg_publication_id"] == (
        "pub_bobzien_2013_found_in_translation"
    )
    assert found_record["coverage"]["state"] == "partial"
    assert "argument_bobzien_2013_1113b7_8_vice_versa_translation" in (
        found_record["coverage"]["kg_node_ids"]
    )


def test_double_review_requires_distinct_people_and_independence_groups() -> None:
    same_person = [
        review("primary", "agent_a", "same_extraction"),
        review("independent", "agent_a", "other_extraction"),
    ]
    same_evidence_chain = [
        review("primary", "agent_a", "same_extraction"),
        review("independent", "agent_b", "same_extraction"),
    ]
    genuinely_independent = [
        review("primary", "agent_a", "critical_edition_a"),
        review("independent", "scholar_b", "critical_edition_b"),
    ]
    assert has_independent_pair(same_person) is False
    assert has_independent_pair(same_evidence_chain) is False
    assert has_independent_pair(genuinely_independent) is True


def test_wave_score_is_deterministically_recomputed() -> None:
    model = {
        "factual_risk": 30,
        "centrality": 20,
        "coverage_gap": 20,
        "source_readiness": 15,
        "controversy_value": 15,
    }
    wave = {
        "score_components": {
            "factual_risk": 1.0,
            "centrality": 1.0,
            "coverage_gap": 0.8,
            "source_readiness": 0.9,
            "controversy_value": 1.0,
        }
    }
    assert recompute_wave_score(wave, model) == 94.5


def test_integrity_input_hash_is_order_independent_and_content_sensitive(
    tmp_path: Path,
) -> None:
    (tmp_path / "tree").mkdir()
    (tmp_path / "tree/a.txt").write_text("alpha\n", encoding="utf-8")
    (tmp_path / "b.txt").write_text("beta\n", encoding="utf-8")
    first = input_set_sha256(tmp_path, ["tree", "b.txt"])
    assert first == input_set_sha256(tmp_path, ["b.txt", "tree", "tree"])

    (tmp_path / "tree/__pycache__").mkdir()
    (tmp_path / "tree/__pycache__/ignored.pyc").write_bytes(b"ignored")
    assert input_set_sha256(tmp_path, ["tree", "b.txt"]) == first

    (tmp_path / "tree/a.txt").write_text("changed\n", encoding="utf-8")
    assert input_set_sha256(tmp_path, ["tree", "b.txt"]) != first


def test_require_exit_gates_returns_dedicated_incomplete_code() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/audit_sota_registry.py",
            "--require-exit-gates",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 2, result.stdout + result.stderr
    assert "structurally_valid: true" in result.stdout
    assert "exit_ready: false" in result.stdout
