"""CI gate: audited fabricated strings must never reappear.

Scans (all offline, no network/DB):

- the committed KG export (``data/kg/*.jsonl``) for strings whose audit fix
  was applied and verified absent at derivation time (``scan_kg``);
- answer-bearing eval fixture files (``data/eval/baselines/*.json`` and the
  legacy ``data/eval/*.json`` run documents) for the answer-scannable set.

The ``assert_no_forbidden_strings`` helper re-exported here is the same one
the online harness (``run_eval.py``) applies to every live answer.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from tests.eval.eval_lib.forbidden import (
    REPO_ROOT,
    ForbiddenString,
    assert_no_forbidden_strings,
    find_forbidden_strings,
    load_forbidden_strings,
)

__all__ = ["assert_no_forbidden_strings", "find_forbidden_strings"]

KG_EXPORT_DIR = REPO_ROOT / "data" / "kg"
BASELINE_DIRS = (REPO_ROOT / "data" / "eval" / "baselines", REPO_ROOT / "data" / "eval")


@pytest.fixture(scope="module")
def forbidden() -> list[ForbiddenString]:
    entries = load_forbidden_strings()
    assert entries, "must_not_appear.jsonl is empty — regenerate the gold fixtures"
    return entries


def test_forbidden_fixture_traceability(forbidden: list[ForbiddenString]) -> None:
    for entry in forbidden:
        assert entry.string.strip(), "empty forbidden string"
        assert entry.source_file.startswith("data/audit/"), entry.source_file
        assert entry.source_line >= 1


def _kg_export_files() -> list[Path]:
    if not KG_EXPORT_DIR.is_dir():
        return []
    return sorted(KG_EXPORT_DIR.glob("*.jsonl"))


def _running_in_ci() -> bool:
    return os.environ.get("CI", "").strip().lower() in {"true", "1", "yes"}


def _skip_or_fail_missing_input(reason: str) -> None:
    """Vacuous-pass guard: a missing scan target is a CI failure, not a skip.

    Locally the KG export may legitimately be absent (fresh clone without
    data), so we skip. In CI the export is expected — silently skipping
    would let the forbidden-string gate pass without scanning anything.
    """
    if _running_in_ci():
        pytest.fail(f"{reason} — refusing to vacuously pass in CI (CI=true)")
    pytest.skip(reason)


def test_kg_export_contains_no_fixed_fabrications(
    forbidden: list[ForbiddenString],
) -> None:
    kg_files = _kg_export_files()
    if not kg_files:
        _skip_or_fail_missing_input(
            "data/kg/*.jsonl not present locally — nothing to scan"
        )

    scannable = [e for e in forbidden if e.scan_kg]
    assert scannable, "no scan_kg entries — regenerate the gold fixtures"

    violations: list[str] = []
    for path in kg_files:
        with path.open(encoding="utf-8") as handle:
            for line_no, line in enumerate(handle, start=1):
                for entry in scannable:
                    if entry.string in line:
                        violations.append(
                            f"{path.name}:{line_no} reintroduces {entry.string!r} "
                            f"(removed by {entry.source_file}:{entry.source_line})"
                        )
    assert not violations, "\n".join(violations)


def _answer_fixture_files() -> list[Path]:
    files: list[Path] = []
    for directory in BASELINE_DIRS:
        if directory.is_dir():
            files.extend(sorted(directory.glob("*.json")))
    return files


def test_answer_fixtures_contain_no_fabrications(
    forbidden: list[ForbiddenString],
) -> None:
    fixture_files = _answer_fixture_files()
    if not fixture_files:
        pytest.skip("no answer fixture files present — nothing to scan")

    violations: list[str] = []
    for path in fixture_files:
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue  # not a run document
        results = doc.get("results", []) if isinstance(doc, dict) else []
        for result in results:
            if not isinstance(result, dict):
                continue
            answer = result.get("answer") or result.get("answer_text") or ""
            for hit in find_forbidden_strings(str(answer), forbidden):
                violations.append(
                    f"{path.name} query {result.get('id')}: answer contains "
                    f"{hit.string!r} ({hit.source_file}:{hit.source_line})"
                )
    assert not violations, "\n".join(violations)


def test_missing_kg_export_fails_in_ci(monkeypatch: pytest.MonkeyPatch) -> None:
    """Regression: CI=true must turn the missing-export skip into a failure."""
    monkeypatch.setenv("CI", "true")
    with pytest.raises(pytest.fail.Exception, match="vacuously"):
        _skip_or_fail_missing_input("data/kg/*.jsonl not present")


def test_missing_kg_export_skips_locally(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CI", raising=False)
    with pytest.raises(pytest.skip.Exception):
        _skip_or_fail_missing_input("data/kg/*.jsonl not present")


def test_helper_flags_known_fabrication(forbidden: list[ForbiddenString]) -> None:
    fabricated = next(e for e in forbidden if e.scan_answers)
    text = f"The philosopher writes: {fabricated.string} [P1]."
    with pytest.raises(AssertionError, match="audited fabricated strings"):
        assert_no_forbidden_strings(text, forbidden)


def test_helper_passes_clean_text(forbidden: list[ForbiddenString]) -> None:
    assert_no_forbidden_strings(
        "Alexander defends what modern scholars characterize as an "
        "incompatibilist account of responsibility.",
        forbidden,
    )
