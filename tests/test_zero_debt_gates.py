from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run_gate(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def test_full_graph_parity_is_zero() -> None:
    result = run_gate("scripts/check_kg_corpus_locus_parity.py", "--strict")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "violations: 0" in result.stdout


def test_full_graph_r16_debt_is_zero() -> None:
    result = run_gate("scripts/check_ingestion_rules.py", "--strict-r16")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "R16 existing unattested fault-line edges: 0" in result.stdout
    assert "STRICT R16: zero unattested fault-line edges -> OK" in result.stdout


def test_work_child_ambiguity_is_zero() -> None:
    result = run_gate("scripts/check_kg_work_child_canonical.py", "--strict")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "work/child canonical mismatches: 0" in result.stdout


def test_committed_parity_baseline_is_empty() -> None:
    payload = json.loads(
        (ROOT / "data/audit/kg_corpus_parity_baseline.json").read_text(encoding="utf-8")
    )
    assert payload["violations"] == {
        "canonical_ref_mismatch": [],
        "cts_urn_mismatch": [],
        "missing_twin": [],
    }
