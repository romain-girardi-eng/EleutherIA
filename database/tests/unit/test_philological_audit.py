"""Unit tests for the philological-audit pass.

These tests exercise the pure helpers -- no DB connection is required.
"""

from __future__ import annotations

import importlib.util
import sys
import unicodedata
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
AUDIT_DIR = REPO_ROOT / "scripts" / "philological_audit"


def _load(module_name: str):
    path = AUDIT_DIR / f"{module_name}.py"
    spec = importlib.util.spec_from_file_location(module_name, path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    # _common is loaded first so siblings can import it
    if module_name != "_common":
        common_path = AUDIT_DIR / "_common.py"
        common_spec = importlib.util.spec_from_file_location("_common", common_path)
        assert common_spec is not None and common_spec.loader is not None
        common = importlib.util.module_from_spec(common_spec)
        sys.modules["_common"] = common
        common_spec.loader.exec_module(common)
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------------------
# audit_polytonic
# ---------------------------------------------------------------------------


def test_polytonic_strip_backslash_artifacts() -> None:
    mod = _load("audit_polytonic")
    assert mod.strip_backslash_artifacts("οὐδε\\ κρίσει") == "οὐδε κρίσει"
    # Multi-line whitespace counts as boundary
    assert mod.strip_backslash_artifacts("κατα\\\nτου") == "κατα\nτου"
    # Backslash NOT followed by whitespace must stay
    assert mod.strip_backslash_artifacts("γα\\ρ") == "γα\\ρ"


def test_polytonic_nfc_idempotent_on_already_nfc() -> None:
    mod = _load("audit_polytonic")
    s = unicodedata.normalize("NFC", "ἀρετή")
    findings = mod._audit_text("n1", "passage", "description", s)
    # No NFC issue (the string is already NFC)
    assert not any(f["issue"] == "not_in_nfc" for f in findings)


def test_polytonic_detects_nfd_form() -> None:
    mod = _load("audit_polytonic")
    s = unicodedata.normalize("NFD", "ἀρετή")
    findings = mod._audit_text("n1", "passage", "description", s)
    nfc_issues = [f for f in findings if f["issue"] == "not_in_nfc"]
    assert nfc_issues, "must detect NFD form"
    assert nfc_issues[0]["auto_apply"] is True
    assert nfc_issues[0]["suggested_fix"]["replace_with"] == "ἀρετή"


# ---------------------------------------------------------------------------
# audit_editions
# ---------------------------------------------------------------------------


def test_editions_lookup_matches_known_work() -> None:
    mod = _load("audit_editions")
    editions = mod.lookup_edition(
        "work_alexander_de_fato_x123", None, "Alexander, De Fato"
    )
    assert editions is not None
    editor_set = {e["editor"] for e in editions}
    assert "Bruns" in editor_set
    assert "Thillet" in editor_set


def test_editions_lookup_returns_none_for_unknown() -> None:
    mod = _load("audit_editions")
    assert mod.lookup_edition("work_random_xyz", None, "Mystery Treatise") is None


# ---------------------------------------------------------------------------
# audit_cts_urns
# ---------------------------------------------------------------------------


def test_cts_urn_strips_inner_space() -> None:
    mod = _load("audit_cts_urns")
    new, fixes = mod.normalize_urn("urn:cts:greekLit:tlg0544:M. 232")
    assert new == "urn:cts:greekLit:tlg0544:M.232"
    assert "removed_inner_space_from_ref" in fixes


def test_cts_urn_drops_unknown_book_sentinel() -> None:
    mod = _load("audit_cts_urns")
    new, fixes = mod.normalize_urn("urn:cts:greekLit:tlg0059.tlg002.perseus-grc2:?.17a")
    assert new == "urn:cts:greekLit:tlg0059.tlg002.perseus-grc2:17a"
    assert "dropped_unknown_book_sentinel" in fixes


def test_cts_urn_passes_clean_urn_through() -> None:
    mod = _load("audit_cts_urns")
    clean = "urn:cts:greekLit:tlg0086.tlg031.1st1K-grc1:7.3"
    new, fixes = mod.normalize_urn(clean)
    assert new == clean
    assert fixes == []


# ---------------------------------------------------------------------------
# audit_person_dates
# ---------------------------------------------------------------------------


def test_person_dates_needs_circa_for_bare_year() -> None:
    mod = _load("audit_person_dates")
    assert mod.needs_circa("185 CE") is True
    assert mod.needs_circa("c. 185 CE") is False
    assert mod.needs_circa("fl. 2nd c. CE") is False
    assert mod.needs_circa("d. 868 CE") is False


def test_person_dates_hedge_bce() -> None:
    mod = _load("audit_person_dates")
    # The double-E regression-test: BCE must NOT become BCEE
    assert mod.hedge("135 BCE") == "c. 135 BCE"
    assert mod.hedge("51 BC") == "c. 51 BCE"
    assert mod.hedge("185 CE") == "c. 185 CE"
    assert mod.hedge("185 AD") == "c. 185 CE"
    assert mod.hedge("185") == "c. 185 CE"


# ---------------------------------------------------------------------------
# audit_translation_provenance
# ---------------------------------------------------------------------------


def test_translation_provenance_module_loads() -> None:
    # We can't exercise audit() without a DB. Just ensure the module imports
    # cleanly and exposes the expected helpers.
    mod = _load("audit_translation_provenance")
    assert hasattr(mod, "audit")
    assert hasattr(mod, "apply_fixes")
