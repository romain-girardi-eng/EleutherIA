#!/usr/bin/env python3
"""Fix Carter 2024 edges (SHACL violation) + arbitrate the sea-battle reading.

The acquisition wave created 4 `discusses` edges from Carter args to
`position_fatalism`, but `discusses` excludes `position` from its target range
(only argues_for/argues_against allow argument->position). This broke the
KG RDF/SHACL gate.

Fix, scholarly-accurate:
  - the reconstructed fatalist arguments argue FOR fatalism  -> argues_for
  - Carter's both-false interpretation is Aristotle's anti-fatalist solution
    -> argues_against

Arbitration of the contradiction Carter raises against the existing sea-battle
node:
  - add `critiques` edge: Carter's both-false reading -> Boethius' future-
    contingents argument (the bivalence-denial / truth-value-gap reading Carter
    rejects: he retains Bivalence and drops the Rule of Contradictory Pairs).
  - nuance concept_sea_battle_future_contingents to present the three
    interpretive families instead of only the bivalence-restriction one.

Idempotent. Snapshot before mutation. Dry-run by default; --commit to write.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NODES_PATH = ROOT / "data" / "kg" / "nodes.jsonl"
EDGES_PATH = ROOT / "data" / "kg" / "edges.jsonl"
SNAPSHOT_DIR = ROOT / "data" / "kg" / "snapshots" / "2026-05-21-pre-carter-fix"

WAVE = "carter_sea_battle_fix_2026_05_21"
NOW = datetime.now(UTC).isoformat(sep=" ")

POSITION = "position_fatalism"
CONCEPT = "concept_sea_battle_future_contingents"
BOETHIUS = "argument_boethius_future_contingents"
BOTH_FALSE = "argument_carter_2024_both_false_interpretation"

# arg -> new relation toward position_fatalism (replacing the bad `discusses`)
EDGE_FIXES = {
    BOTH_FALSE: "argues_against",
    "argument_carter_2024_first_fatalist_argument": "argues_for",
    "argument_carter_2024_second_fatalist_argument": "argues_for",
    "argument_carter_2024_objections_are_fatalist": "argues_for",
}

OLD_CLAUSE = ("Aristotle's solution (whether restricting bivalence or "
              "introducing indeterminate truth-values) remains debated.")
NEW_CLAUSE = (
    "Aristotle's solution remains debated among at least three interpretive "
    "families: (i) the traditional bivalence-restriction or truth-value-gap "
    "reading (the 'Boethian' interpretation, later associated with "
    "Łukasiewicz's many-valued logic), on which future contingents are "
    "not yet determinately true or false; (ii) a reading on which Aristotle "
    "denies only the necessity of each disjunct while retaining unrestricted "
    "bivalence; and (iii) the 'both-false' reading defended by Jason W. Carter "
    "(OSAP 63, 2024), on which singular future contingents satisfy the "
    "Principle of Bivalence but violate the Rule of Contradictory Pairs, so "
    "that the affirmation and the denial are contraries (jointly falsifiable) "
    "rather than contradictories."
)


def edge_key(e: dict) -> tuple:
    return ((e.get("source") or e.get("source_id")),
            (e.get("target") or e.get("target_id")),
            e.get("relation"))


def main(commit: bool) -> int:
    # --- edges ---
    edge_lines = [ln for ln in EDGES_PATH.read_text(encoding="utf-8").splitlines() if ln.strip()]
    existing = {edge_key(json.loads(ln)) for ln in edge_lines}

    fixed = 0
    new_edge_lines: list[str] = []
    for ln in edge_lines:
        e = json.loads(ln)
        k = edge_key(e)
        if k[1] == POSITION and k[2] == "discusses" and k[0] in EDGE_FIXES:
            e["relation"] = EDGE_FIXES[k[0]]
            md = e.get("metadata") or {}
            if isinstance(md, str):
                md = json.loads(md) if md else {}
            md["wave_fix"] = WAVE
            md["fix_reason"] = "discusses excludes position range; reclassified"
            e["metadata"] = md
            new_edge_lines.append(json.dumps(e, ensure_ascii=False))
            fixed += 1
        else:
            new_edge_lines.append(ln)

    # arbitration critiques edge
    crit_key = (BOTH_FALSE, BOETHIUS, "critiques")
    added_crit = False
    if crit_key not in existing:
        new_edge_lines.append(json.dumps({
            "source": BOTH_FALSE, "target": BOETHIUS, "relation": "critiques",
            "confidence": 0.75,
            "metadata": {
                "wave": WAVE,
                "note": ("Carter's both-false reading retains Bivalence and "
                         "rejects the Rule of Contradictory Pairs, opposing the "
                         "bivalence-denial / truth-value-gap reading canonized "
                         "by Boethius (2nd Commentary on De Int. 9)."),
            },
        }, ensure_ascii=False))
        added_crit = True

    # --- concept node nuance ---
    node_lines = NODES_PATH.read_text(encoding="utf-8").splitlines()
    concept_fixed = False
    for i, ln in enumerate(node_lines):
        if not ln.strip() or f'"{CONCEPT}"' not in ln:
            continue
        n = json.loads(ln)
        if n.get("id") != CONCEPT:
            continue
        desc = n.get("description", "")
        md = n.get("metadata")
        md_d = json.loads(md) if isinstance(md, str) and md else (md or {})
        if md_d.get("wave_arbitration") == WAVE:
            break  # idempotent
        if OLD_CLAUSE in desc:
            n["description"] = desc.replace(OLD_CLAUSE, NEW_CLAUSE)
        md_d["wave_arbitration"] = WAVE
        md_d["interpretive_readings"] = [
            {"id": "bivalence_restriction_gap", "label": "Bivalence-restriction / truth-value-gap (Boethian, Łukasiewicz)"},
            {"id": "necessity_only", "label": "Denies necessity of disjuncts, retains bivalence"},
            {"id": "both_false_rcp", "label": "Both-false / rejects Rule of Contradictory Pairs (Carter 2024)"},
        ]
        md_d["needs_evidence"] = False
        md_d["needs_evidence_lifted_reason"] = (
            "Interpretive spectrum documented with citations (Carter OSAP 63 "
            "2024 + Boethian/Łukasiewicz readings)")
        n["metadata"] = json.dumps(md_d, ensure_ascii=False)
        n["updated_at"] = NOW
        node_lines[i] = json.dumps(n, ensure_ascii=False)
        concept_fixed = True
        break

    print(f"edges reclassified: {fixed}/4 | critiques added: {added_crit} | concept nuanced: {concept_fixed}")
    if fixed == 0 and not added_crit and not concept_fixed:
        print("OK: nothing to apply (idempotent).")
        return 0
    if not commit:
        print("[DRY-RUN] --commit to write.")
        return 0

    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(NODES_PATH, SNAPSHOT_DIR / NODES_PATH.name)
    shutil.copy2(EDGES_PATH, SNAPSHOT_DIR / EDGES_PATH.name)
    EDGES_PATH.write_text("\n".join(new_edge_lines) + "\n", encoding="utf-8")
    NODES_PATH.write_text("\n".join(node_lines) + "\n", encoding="utf-8")
    print(f"snapshot: {SNAPSHOT_DIR}")
    print("DONE")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--commit", action="store_true")
    sys.exit(main(ap.parse_args().commit))
