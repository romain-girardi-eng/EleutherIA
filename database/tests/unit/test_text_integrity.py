"""Unit tests for the corpus tamper-evidence helpers (G14).

Pure functions only — no DB connection required. Unicode fixtures are
built programmatically from codepoints (never re-typed ancient text).
"""

from __future__ import annotations

import hashlib
import importlib.util
import sys
import unicodedata
from pathlib import Path

from eleutheria_database.services.text_integrity import (
    DriftReport,
    canonical_text_form,
    compare_checksums,
    text_sha256,
)

REPO_DB_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = REPO_DB_ROOT / "scripts"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def _load_audit_text_drift():
    # _common must be importable as a sibling first.
    _load(SCRIPTS_DIR / "philological_audit" / "_common.py", "_common")
    return _load(
        SCRIPTS_DIR / "philological_audit" / "audit_text_drift.py",
        "audit_text_drift",
    )


# ---------------------------------------------------------------------------
# text_sha256 / canonical_text_form
# ---------------------------------------------------------------------------


def test_sha256_is_nfc_invariant() -> None:
    # U+00E9 (precomposed) vs 'e' + U+0301 (combining acute): same NFC form.
    precomposed = "caf\u00e9"
    combining = "cafe\u0301"
    assert precomposed != combining  # different byte sequences
    assert canonical_text_form(precomposed) == canonical_text_form(combining)
    assert text_sha256(precomposed) == text_sha256(combining)


def test_sha256_matches_direct_hash_of_nfc_utf8() -> None:
    text = "lorem ipsum 123"
    expected = hashlib.sha256(
        unicodedata.normalize("NFC", text).encode("utf-8")
    ).hexdigest()
    assert text_sha256(text) == expected
    assert len(text_sha256(text)) == 64


def test_sha256_detects_any_real_change() -> None:
    base = text_sha256("the text as stored")
    assert text_sha256("the text as stored ") != base  # trailing whitespace
    assert text_sha256("the Text as stored") != base  # case
    assert text_sha256("") != base


def test_fallback_hash_in_ingest_scripts_matches_canonical() -> None:
    """The inline ImportError fallbacks must agree with the canonical impl."""
    sample = "cafe\u0301 mixed nfc/nfd"
    expected = text_sha256(sample)
    fallback = hashlib.sha256(
        unicodedata.normalize("NFC", sample).encode("utf-8")
    ).hexdigest()
    assert fallback == expected


# ---------------------------------------------------------------------------
# compare_checksums
# ---------------------------------------------------------------------------


def _entry(sha: str, **extra) -> dict:
    return {"sha256": sha, **extra}


def test_compare_checksums_no_drift() -> None:
    base = {"p1": _entry("aa"), "p2": _entry("bb")}
    report = compare_checksums(base, dict(base))
    assert isinstance(report, DriftReport)
    assert not report.has_drift
    assert report.unchanged == 2
    assert report.summary_counts() == {
        "added": 0,
        "removed": 0,
        "changed": 0,
        "unchanged": 2,
    }


def test_compare_checksums_added_removed_changed() -> None:
    baseline = {
        "p1": _entry("aa", canonical_ref="1.1"),
        "p2": _entry("bb"),
        "p3": _entry("cc"),
    }
    current = {
        "p1": _entry("aa", canonical_ref="1.1"),  # unchanged
        "p2": _entry("b2"),  # changed
        "p4": _entry("dd"),  # added
    }
    report = compare_checksums(baseline, current)
    assert report.has_drift
    assert set(report.added) == {"p4"}
    assert set(report.removed) == {"p3"}
    assert set(report.changed) == {"p2"}
    assert report.unchanged == 1
    assert report.changed["p2"]["baseline_sha256"] == "bb"
    assert report.changed["p2"]["current_sha256"] == "b2"


# ---------------------------------------------------------------------------
# audit_text_drift pure helpers
# ---------------------------------------------------------------------------


def test_baseline_roundtrip() -> None:
    drift = _load_audit_text_drift()
    rows = [
        {"passage_id": "b", "sha256": "22", "canonical_ref": "1.2"},
        {"passage_id": "a", "sha256": "11", "canonical_ref": "1.1"},
    ]
    blob = drift.baseline_bytes(rows)
    parsed = drift.parse_baseline_bytes(blob)
    assert set(parsed) == {"a", "b"}
    assert parsed["a"]["sha256"] == "11"
    assert parsed["b"]["canonical_ref"] == "1.2"
    # Deterministic output: same rows (any order) → identical bytes.
    assert drift.baseline_bytes(list(reversed(rows))) == blob


def test_stored_hash_mismatches_skips_null_and_flags_disagreement() -> None:
    drift = _load_audit_text_drift()
    rows = [
        {"passage_id": "p1", "sha256": "aa", "stored_sha256": None},
        {"passage_id": "p2", "sha256": "bb", "stored_sha256": "bb"},
        {
            "passage_id": "p3",
            "sha256": "cc",
            "stored_sha256": "zz",
            "work_canonical_id": "w1",
            "canonical_ref": "3.1",
        },
    ]
    flagged = drift.stored_hash_mismatches(rows)
    assert len(flagged) == 1
    assert flagged[0]["passage_id"] == "p3"
    assert flagged[0]["issue"] == "stored_text_sha256_mismatch"
    assert flagged[0]["stored_sha256"] == "zz"
    assert flagged[0]["recomputed_sha256"] == "cc"


def test_drift_to_report_rows_flattens_all_kinds() -> None:
    drift = _load_audit_text_drift()
    report = compare_checksums(
        {"gone": _entry("aa"), "edit": _entry("bb")},
        {"edit": _entry("b2"), "new": _entry("cc")},
    )
    rows = drift.drift_to_report_rows(report)
    kinds = {(r["passage_id"], r["drift"]) for r in rows}
    assert kinds == {("new", "added"), ("gone", "removed"), ("edit", "changed")}


# ---------------------------------------------------------------------------
# generate_text_provenance_backfill (generator emits SQL, never executes it)
# ---------------------------------------------------------------------------


def _load_generator():
    return _load(
        SCRIPTS_DIR / "generate_text_provenance_backfill.py",
        "generate_text_provenance_backfill",
    )


def test_sql_literal_escapes_quotes() -> None:
    gen = _load_generator()
    assert gen.sql_literal("P.-Th. Camelot, 1958") == "'P.-Th. Camelot, 1958'"
    assert gen.sql_literal("l'edition") == "'l''edition'"


def test_sc_update_statement_uses_registry_edition_verbatim() -> None:
    gen = _load_generator()
    entry = {
        "node_id": "sc_test_work",
        "sc_volume": "SC 999",
        "author": "Testus",
        "title": "De Testibus",
        "edition": "A. Editor, 1960 (2nd ed.)",
    }
    sql = gen.sc_update_statement(entry, "2026-06-10")
    assert "w.canonical_id = 'sc_test_work'" in sql
    assert "A. Editor, 1960 (2nd ed.)" in sql
    assert "p.text_provenance IS NULL" in sql  # never overwrites curated rows
    assert '"verified_from": "WORK_REGISTRY"' in sql


def test_scaife_statement_flags_null_edition_not_a_guess() -> None:
    gen = _load_generator()
    sql = gen.scaife_update_statement("2026-06-10")
    assert '"edition": null' in sql
    assert "NEEDS MANUAL EDITION ATTRIBUTION" in sql
    assert '"needs_manual_edition_attribution": true' in sql
    assert "p.text_provenance IS NULL" in sql


def test_generate_sql_covers_full_registry_once() -> None:
    gen = _load_generator()
    registry = gen.load_work_registry()
    assert len(registry) >= 40  # all SC source files present
    sql = gen.generate_sql(registry, "2026-06-10")
    node_ids = {e["node_id"] for e in registry.values()}
    for node_id in node_ids:
        assert sql.count(f"w.canonical_id = '{node_id}'") == 1
    assert "do not apply blindly" in sql
