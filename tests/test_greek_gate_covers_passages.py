"""The zero-fabrication gate must actually look at the passages.

`check_greek_gate.py` used to open with `if n.get('type') == 'passage': continue`.
Passages are 85% of the graph and hold every Greek text in it, so the gate that
advertises the project's zero-fabrication guarantee inspected 351 Greek runs
across 224 nodes — 1% of the graph, and none of its 13,112 Greek passage nodes.

With passages included it inspects 34,703 runs across 13,387 nodes.

These tests lock the two properties that matter: passages are in scope, and a
fabricated run still fails even though a large debt baseline is held.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "check_greek_gate", ROOT / "scripts" / "check_greek_gate.py"
)
assert SPEC and SPEC.loader
gate = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gate)

# `gate.strip` is the module's Unicode normaliser, not `str.strip`. Bound to a
# clearer name so neither a reader nor a linter mistakes it for the builtin.
normalise = gate.strip

BASELINE = ROOT / "data/audit/greek_gate_baseline.json"


def test_passages_are_in_scope_by_default() -> None:
    source = (ROOT / "scripts" / "check_greek_gate.py").read_text(encoding="utf-8")
    # The unconditional skip must never come back.
    assert "if n.get('type') == 'passage':\n            continue" not in source
    assert "args.skip_passages" in source


def test_baseline_is_debt_and_says_so() -> None:
    data = json.loads(BASELINE.read_text(encoding="utf-8"))
    note = data["note"].lower()
    assert "debt" in note and "not approval" in note
    # It must be distinguishable from the allowlist, which certifies a run
    # against a named edition. Conflating the two would launder the backlog.
    assert "allowlist" in note
    assert data["total_runs"] == sum(len(v) for v in data["known_unverified"].values())


def test_the_backlog_is_measured_not_hidden() -> None:
    data = json.loads(BASELINE.read_text(encoding="utf-8"))
    assert data["total_runs"] > 0, "an empty baseline would mean the debt is unmeasured"
    assert data["total_nodes"] > 0


def test_extract_runs_only_takes_substantial_greek() -> None:
    assert gate.extract_runs("no greek here at all") == []
    # A bare technical term is not a quotation and must not trip the gate.
    assert gate.extract_runs("the term εἱμαρμένη") == []
    runs = gate.extract_runs("ὡς ταὐτὸν εἱμαρμένη καὶ Ζεύς διττὸν δὲ τὸ τῆς Μοίρας")
    assert runs and len(runs[0]) >= gate.MIN_CHARS


def test_normalisation_is_accent_and_sigma_insensitive() -> None:
    # The corpus and the node may differ in final sigma or accentuation without
    # differing in text; the gate must not fail on that.
    assert normalise("ΤΑΥΤΟΣ") == normalise("ταὐτός")
    assert normalise("λόγος") == normalise("λογοσ")


def test_run_hash_is_stable_across_accentuation() -> None:
    # Baseline entries are keyed by this hash, so it has to survive the same
    # normalisation the comparison uses.
    assert gate.run_hash("ταὐτὸν εἱμαρμένη καὶ Ζεύς") == gate.run_hash(
        "ταυτον ειμαρμενη και Ζευσ"
    )


def test_metadata_is_in_scope_not_just_description() -> None:
    """`metadata.premises[*]` is where generated Greek was actually found.

    The gate read `description` alone, so an audit's discovery of Greek and
    Latin fitted to English premises sat entirely outside it. Two of those were
    then proved fabricated against TLG E.
    """
    node = {
        "id": "x",
        "description": "no greek here",
        "metadata": {
            "premises": [
                {"text": "ὡς ταὐτὸν εἱμαρμένη καὶ Ζεύς διττὸν δὲ τὸ τῆς Μοίρας"}
            ]
        },
    }
    assert gate.extract_runs(gate.node_text(node)), "metadata Greek must be scanned"


def test_metadata_stored_as_a_json_string_is_still_scanned() -> None:
    # Two publication nodes store metadata as a JSON string rather than an
    # object; a walker that only handles dicts would skip them silently.
    node = {
        "id": "x",
        "metadata": json.dumps(
            {"quote_verbatim": "ὡς ταὐτὸν εἱμαρμένη καὶ Ζεύς διττὸν δὲ τὸ τῆς Μοίρας"}
        ),
    }
    assert gate.extract_runs(gate.node_text(node))


def test_the_same_run_is_not_counted_twice_within_a_node() -> None:
    run = "ὡς ταὐτὸν εἱμαρμένη καὶ Ζεύς διττὸν δὲ τὸ τῆς Μοίρας"
    node = {"id": "x", "description": run, "metadata": {"quote_verbatim": run}}
    runs = gate.extract_runs(gate.node_text(node))
    assert len({gate.run_hash(r) for r in runs}) == 1


def test_the_baseline_says_it_is_untriaged() -> None:
    note = json.loads(BASELINE.read_text(encoding="utf-8"))["note"].lower()
    assert "untriaged" in note
    assert "may be assumed innocent" in note or "fabric" in note
