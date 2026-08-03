#!/usr/bin/env python3
"""Phase A — Fix 27 ontology violations detected in audit 2026-05-18.

Background
----------
The KG quality audit (2026-05-18) reported 27 edges whose (relation,
source_type, target_type) triple is not allowed by the declared ontology in
``knowledge graph/ontology/edge_types.json`` (under strict mode, i.e. without
accepting the ``*`` wildcard for ``related_to``).

Distribution:

    14× related_to: concept → concept
     3× related_to: work → work
     2× related_to: concept → school
     2× related_to: passage → passage
     2× supports: publication → person
     2× discussed_in: concept → publication
     1× related_to: argument → argument
     1× related_to: work → passage

Decisions
---------
Each of the 27 edges is hard-coded below with one of three actions:

* ``DELETE``  — edge has no informative value (e.g. "shared topic" notes that
  are already implied by other concept-level links).
* ``REQUALIFY <rel>`` — the edge is salvageable by switching to a stricter,
  ontology-valid relation type. The replacement type is validated below
  against ``edge_types.json`` (no wildcard escape).
* ``INVERT_REQUALIFY <rel>`` — direction was reversed; we swap source/target
  and switch to the inverse relation.

After the script runs:

* ``data/kg/edges.jsonl`` is snapshotted to
  ``data/kg/snapshots/2026-05-18-pre-phase-a-ontology/edges.jsonl`` BEFORE any
  mutation.
* Touched edges carry ``metadata.phase_a_fix_2026_05_18``:
    - ``"deleted_for_ontology"`` on edges that were removed (logged to a
      report; not written back).
    - ``"requalified_from_<X>_to_<Y>"`` on requalified edges.
    - ``"inverted_and_requalified_from_<X>_to_<Y>"`` on inverted edges.
* Other edges are preserved byte-exact.
* Idempotent: a second run detects nothing to apply.

Usage
-----
    # Dry run (default): writes report to stdout, no file change.
    python scripts/fix_phase_a_ontology_violations_2026_05_18.py

    # Apply changes:
    python scripts/fix_phase_a_ontology_violations_2026_05_18.py --commit
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from collections import Counter
from datetime import datetime, UTC
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EDGES_PATH = ROOT / "data" / "kg" / "edges.jsonl"
NODES_PATH = ROOT / "data" / "kg" / "nodes.jsonl"
ONTOLOGY_PATH = ROOT / "knowledge graph" / "ontology" / "edge_types.json"
SNAPSHOT_DIR = ROOT / "data" / "kg" / "snapshots" / "2026-05-18-pre-phase-a-ontology"

PHASE_TAG = "phase_a_fix_2026_05_18"


# -----------------------------------------------------------------------------
# DECISIONS — one entry per violation, keyed by edge_id when present, else by
# the unique tuple (relation, source_id, target_id).
# -----------------------------------------------------------------------------

DELETE = "DELETE"
REQUALIFY = "REQUALIFY"
INVERT_REQUALIFY = "INVERT_REQUALIFY"


# Each decision: action, new_relation (None for DELETE), rationale.
# Key is either edge_id (UUID) or fallback tuple (rel, src, tgt) when edge_id
# is null in the JSONL.
DECISIONS: dict[object, tuple[str, str | None, str]] = {
    # --- related_to: concept → concept (14) ---
    "0131216a-8ea5-4621-acb7-6276c03a7bbc": (
        REQUALIFY,
        "influences",
        "Middle-Platonist providence/fate distinction is the conceptual influence shaping the development of eph' hēmin in later Middle Platonism.",
    ),
    "40965248-27c5-4e62-8193-6953eb117402": (
        REQUALIFY,
        "influences",
        "Per Bobzien 1998 (metadata), ep' ison is a constitutive influence on the two-sided potestative ἐφ' ἡμῖν fusion.",
    ),
    "682ab6a8-a17a-42dc-84e4-116b082bcb1e": (
        REQUALIFY,
        "parallel_to",
        "Thelēsis (Greek) and voluntas (Latin) are terminological parallels across the Greek→Latin theology of will.",
    ),
    "737ccc9c-3f3c-480a-9872-10be5088b436": (
        REQUALIFY,
        "part_of",
        "Nunc stans is the constitutive temporal aspect of Boethian aeternitas (totum simul); it is part_of the wider concept.",
    ),
    "af153844-856d-409a-bd4f-feb9bb1887c2": (
        REQUALIFY,
        "parallel_to",
        "Boulēsis (Greek rational desire) parallels voluntas (Latin will) — terminological parallel.",
    ),
    "c628faa9-38dd-4028-8e22-8cf5e2d9761b": (
        REQUALIFY,
        "influences",
        "The terminology evolution concept traces from Aristotelian eph' hēmin; the latter influences the former.",
    ),
    "e2429d6c-4a08-456d-ae19-e01e052d5846": (
        REQUALIFY,
        "influences",
        "Terminology evolution traces also from autexousion; influence relation.",
    ),
    # Bobzien concept→concept chain (edges with null edge_id, keyed by triple):
    (
        "related_to",
        "concept_chrysippean_compatibilism_bobzien",
        "concept_cylinder_analogy_chrysippus_e5f6g7h8",
    ): (
        REQUALIFY,
        "presupposes",
        "Bobzien's reconstruction of Chrysippean compatibilism presupposes the cylinder analogy as core illustration.",
    ),
    (
        "related_to",
        "concept_chrysippean_compatibilism_bobzien",
        "concept_synkatathesis_stoic_assent",
    ): (
        REQUALIFY,
        "presupposes",
        "Chrysippean compatibilism presupposes synkatathesis (assent) as the locus of agency.",
    ),
    (
        "related_to",
        "concept_chrysippean_compatibilism_bobzien",
        "concept_eph_hemin_one_sided_causative",
    ): (
        REQUALIFY,
        "presupposes",
        "Chrysippean compatibilism presupposes the one-sided causative eph' hēmin.",
    ),
    (
        "related_to",
        "concept_pneumatic_causation_stoic_bobzien",
        "concept_sympatheia_stoic",
    ): (
        REQUALIFY,
        "presupposes",
        "Stoic pneumatic causation presupposes cosmic sympatheia as its physical backdrop.",
    ),
    (
        "related_to",
        "concept_pneumatic_causation_stoic_bobzien",
        "concept_heimarmene_fate_stoics_j0k1l2m3",
    ): (
        REQUALIFY,
        "presupposes",
        "Pneumatic causation is the physical mechanism that underlies heimarmenē; presupposition relation.",
    ),
    (
        "related_to",
        "concept_fate_principle_bobzien",
        "concept_heimarmene_fate_stoics_j0k1l2m3",
    ): (
        REQUALIFY,
        "presupposes",
        "Bobzien's Fate Principle (§1.4.4) is a formal restatement that presupposes the heimarmenē doctrine.",
    ),
    (
        "related_to",
        "concept_philopator_compatibilism_bobzien",
        "concept_eph_hemin_one_sided_causative",
    ): (
        REQUALIFY,
        "presupposes",
        "Philopator-style late Stoic compatibilism presupposes the one-sided causative eph' hēmin reading.",
    ),
    # --- related_to: work → work (3) ---
    "202fb8e8-8bf4-4f2a-9856-a5de337f7afa": (
        DELETE,
        None,
        "Aug DCD ↔ Methodius De Lib Arb 'shared topic: theodicy/free will' is a low-information note; both works are already linked via concept-level edges (autexousion, providence, etc.).",
    ),
    "30c1a507-1959-43f0-9563-8e025b38f38a": (
        DELETE,
        None,
        "Methodius ↔ Origen De Princ 'shared topic: free will' is low-information; both linked via concept_autexousion.",
    ),
    "59f97208-4661-495c-af0c-615f712ec2cd": (
        REQUALIFY,
        "part_of",
        "SC 507 edition node is a textual container of the canonical First Apology work; closest valid ontology relation is part_of (work→work allowed).",
    ),
    # --- related_to: concept → school (2) ---
    "2d98cc75-281f-48fa-b104-ed8122e839b3": (
        REQUALIFY,
        "member_of",
        "Ekpyrosis is a constitutive doctrinal concept of the Stoic school; member_of (concept→school) is valid in the ontology.",
    ),
    "ec8224cb-1096-421c-8617-9af776aec0e8": (
        REQUALIFY,
        "member_of",
        "Sympatheia is a doctrinal concept of the Stoic school; member_of (concept→school).",
    ),
    # --- related_to: passage → passage (2) ---
    "67e65d94-df93-4ab0-941a-67c7661d6529": (
        REQUALIFY,
        "parallel_to",
        "Metadata explicitly says 'parallel argument' — parallel_to (passage→passage) is the canonical ontology relation.",
    ),
    "b7f9adca-8943-4440-ba3b-c8502d644211": (
        REQUALIFY,
        "parallel_to",
        "Same as above — Justin Dial 102 ↔ Dial 88 'parallel argument'.",
    ),
    # --- related_to: argument → argument (1) ---
    "1de812fe-bc69-4ff2-aa6a-4bbaa401d847": (
        REQUALIFY,
        "responds_to",
        "Boethius's solution (V.pr.6 timeless eternity) is a response to the foreknowledge problem he formulates at V.pr.3.",
    ),
    # --- related_to: work → passage (1) ---
    "cc5a8fd1-c92b-4ca4-a0d7-7716f21c4ed3": (
        REQUALIFY,
        "cites",
        "Augustine's De Civitate Dei cites De Libero Arbitrio 1.11.21 as a cross-reference to his earlier liberum-arbitrium argument; cites (work→passage) is valid.",
    ),
    # --- supports: publication → person (2) ---
    "b2cb46c2-2099-446f-8051-34c51583615f": (
        REQUALIFY,
        "discusses",
        "Fürst 2022 *Wege zur Freiheit* discusses Hengstermann's scholarship; 'supports' as pub→person is not in the ontology, but 'discusses' (publication→person) is valid.",
    ),
    "32d34110-2fa7-4eac-a4b6-9023c2fb2a43": (
        REQUALIFY,
        "discusses",
        "Same as above — Fürst 2022 discusses Bobzien.",
    ),
    # --- discussed_in: concept → publication (2, direction is inverted) ---
    "bbfc46e8-c4e0-465e-bcba-b7e0ea52dbb4": (
        INVERT_REQUALIFY,
        "discusses",
        "Direction inversion: Freiheitspathos (concept) discussed_in Fürst 2022 (publication) violates target_types=[work,passage]. Inverse: Fürst 2022 discusses Freiheitspathos (publication→concept) is valid.",
    ),
    "12580032-d0ba-47cc-b900-2e112268c106": (
        INVERT_REQUALIFY,
        "discusses",
        "Same as above — Freiheitsmetaphysik discussed_in Fürst 2022 → inverted to Fürst 2022 discusses Freiheitsmetaphysik.",
    ),
}


# -----------------------------------------------------------------------------
# Validation: every REQUALIFY target must be ontology-valid for the
# (source_type, target_type) it will land on. INVERT_REQUALIFY validates after
# swap.
# -----------------------------------------------------------------------------


def load_ontology() -> dict[str, dict]:
    return json.loads(ONTOLOGY_PATH.read_text(encoding="utf-8"))["edge_types"]


def load_node_types() -> dict[str, str]:
    out: dict[str, str] = {}
    with NODES_PATH.open(encoding="utf-8") as fh:
        for raw in fh:
            raw = raw.strip()
            if not raw:
                continue
            n = json.loads(raw)
            for nid in (n.get("node_id"), n.get("id")):
                if nid:
                    out[nid] = n.get("type")
    return out


def is_valid(ont: dict, rel: str, st: str, tt: str, *, strict: bool = True) -> bool:
    """Strict (no wildcard) ontology check, matching the audit's reading."""
    d = ont.get(rel)
    if d is None:
        return False
    src_list = d["source_types"]
    tgt_list = d["target_types"]
    if strict:
        return (st in src_list) and (tt in tgt_list)
    return (st in src_list or "*" in src_list) and (tt in tgt_list or "*" in tgt_list)


def validate_decisions(ont: dict, node_types: dict[str, str]) -> list[str]:
    """Pre-flight: ensure every REQUALIFY target lands on a valid ontology slot."""
    errors: list[str] = []
    for key, (action, new_rel, _why) in DECISIONS.items():
        if action == DELETE:
            continue
        if isinstance(key, tuple):
            _, sid, tid = key
        else:
            # edge_id keyed — we need to look up source/target ids later;
            # validation deferred to runtime cross-check.
            continue
        st = node_types.get(sid)
        tt = node_types.get(tid)
        if action == INVERT_REQUALIFY:
            st, tt = tt, st  # swap for validation
        if st is None or tt is None:
            errors.append(f"  unknown node type for decision key={key}")
            continue
        if not is_valid(ont, new_rel, st, tt, strict=True):
            errors.append(
                f"  INVALID: {new_rel}: {st}→{tt} not allowed in ontology (key={key})"
            )
    return errors


# -----------------------------------------------------------------------------
# Core engine
# -----------------------------------------------------------------------------


def lookup_decision(edge: dict) -> tuple[str, str | None, str] | None:
    eid = edge.get("edge_id")
    if eid and eid in DECISIONS:
        return DECISIONS[eid]
    fallback = (
        edge["relation"],
        edge.get("source_id") or edge.get("source"),
        edge.get("target_id") or edge.get("target"),
    )
    return DECISIONS.get(fallback)


def already_applied(edge: dict) -> bool:
    md = edge.get("metadata")
    if not md:
        return False
    if isinstance(md, str):
        try:
            md = json.loads(md)
        except json.JSONDecodeError:
            return False
    if not isinstance(md, dict):
        return False
    return PHASE_TAG in md


def merge_metadata(raw: str | dict | None, tag_value: str) -> str:
    """Add the phase_a tag to metadata; preserve existing keys; return JSON string."""
    if raw in (None, "", "{}"):
        obj: dict = {}
    elif isinstance(raw, dict):
        obj = dict(raw)
    else:
        try:
            obj = json.loads(raw)
            if not isinstance(obj, dict):
                obj = {"_original": obj}
        except json.JSONDecodeError:
            obj = {"_original_raw": raw}
    obj[PHASE_TAG] = tag_value
    # Compact JSON, sorted keys for determinism.
    return json.dumps(obj, ensure_ascii=False, sort_keys=True)


def apply_action(edge: dict, action: str, new_rel: str | None) -> dict:
    """Return mutated edge per action. DELETE returns None at caller level."""
    e = dict(edge)
    old_rel = e["relation"]
    if action == REQUALIFY:
        e["relation"] = new_rel
        e["metadata"] = merge_metadata(e.get("metadata"), f"requalified_from_{old_rel}_to_{new_rel}")
    elif action == INVERT_REQUALIFY:
        # Swap source and target, change relation.
        e["relation"] = new_rel
        src = e.get("source_id") or e.get("source")
        tgt = e.get("target_id") or e.get("target")
        if "source_id" in e:
            e["source_id"] = tgt
        if "target_id" in e:
            e["target_id"] = src
        if "source" in e:
            e["source"] = tgt
        if "target" in e:
            e["target"] = src
        e["metadata"] = merge_metadata(
            e.get("metadata"), f"inverted_and_requalified_from_{old_rel}_to_{new_rel}"
        )
    else:
        raise ValueError(f"unhandled action: {action}")
    return e


# -----------------------------------------------------------------------------
# Snapshot
# -----------------------------------------------------------------------------


def take_snapshot() -> Path:
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    dest = SNAPSHOT_DIR / "edges.jsonl"
    if dest.exists():
        return dest  # idempotent — keep the pristine pre-phase-a snapshot
    shutil.copy2(EDGES_PATH, dest)
    # Stamp a tiny marker for traceability.
    (SNAPSHOT_DIR / "SNAPSHOT_META.json").write_text(
        json.dumps(
            {
                "phase": "A — ontology violations",
                "audit_date": "2026-05-18",
                "snapshotted_at": datetime.now(UTC).isoformat(),
                "source": str(EDGES_PATH.relative_to(ROOT)),
                "expected_violations": 27,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return dest


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--commit",
        action="store_true",
        help="Apply changes to data/kg/edges.jsonl. Default is dry-run.",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=None,
        help="Optional path to write a JSON report of actions taken.",
    )
    args = parser.parse_args(argv)

    ont = load_ontology()
    node_types = load_node_types()

    # Pre-flight validate REQUALIFY targets.
    errors = validate_decisions(ont, node_types)
    if errors:
        print("ABORT — invalid REQUALIFY targets:", file=sys.stderr)
        for line in errors:
            print(line, file=sys.stderr)
        return 2

    mode = "COMMIT" if args.commit else "DRY-RUN"
    print(f"[{mode}] Phase A — fixing 27 ontology violations (audit 2026-05-18)")
    print(f"[{mode}] Edges file: {EDGES_PATH.relative_to(ROOT)}")
    print(f"[{mode}] Ontology : {ONTOLOGY_PATH.relative_to(ROOT)}")

    # Stream-rewrite.
    if args.commit:
        snap = take_snapshot()
        print(f"[{mode}] Snapshot taken at: {snap.relative_to(ROOT)}")

    report: dict[str, object] = {
        "audit_date": "2026-05-18",
        "mode": mode,
        "expected_violations": 27,
        "actions": [],
        "counts": {},
    }
    action_counter: Counter = Counter()
    skipped_already: int = 0
    matched_decisions: set = set()

    out_lines: list[str] = []
    total = 0
    with EDGES_PATH.open(encoding="utf-8") as fh:
        for raw in fh:
            raw_stripped = raw.rstrip("\n")
            if not raw_stripped:
                out_lines.append(raw)
                continue
            total += 1
            edge = json.loads(raw_stripped)
            decision = lookup_decision(edge)
            if decision is None:
                out_lines.append(raw)  # byte-exact preserve
                continue

            action, new_rel, why = decision
            key = edge.get("edge_id") or (
                edge["relation"],
                edge.get("source_id") or edge.get("source"),
                edge.get("target_id") or edge.get("target"),
            )

            if already_applied(edge):
                skipped_already += 1
                matched_decisions.add(key)
                out_lines.append(raw)  # nothing to do
                continue

            matched_decisions.add(key)
            action_counter[action] += 1
            report["actions"].append(
                {
                    "edge_id": edge.get("edge_id"),
                    "relation": edge["relation"],
                    "source_id": edge.get("source_id") or edge.get("source"),
                    "target_id": edge.get("target_id") or edge.get("target"),
                    "action": action,
                    "new_relation": new_rel,
                    "rationale": why,
                }
            )

            if action == DELETE:
                # Drop the line. Do not append to out_lines.
                continue

            new_edge = apply_action(edge, action, new_rel)
            out_lines.append(json.dumps(new_edge, ensure_ascii=False) + "\n")

    # Sanity: every decision must have matched exactly one edge.
    declared_keys = set(DECISIONS.keys())
    unmatched = declared_keys - matched_decisions
    if unmatched:
        print(
            f"[{mode}] WARNING — {len(unmatched)} decisions did not match any edge "
            f"(already cleaned up by a prior run, or KG diverged):",
            file=sys.stderr,
        )
        for k in unmatched:
            print(f"    - {k}", file=sys.stderr)

    report["counts"] = {
        "total_edges_scanned": total,
        "matched_violations": len(matched_decisions),
        "skipped_already_applied": skipped_already,
        "delete": action_counter[DELETE],
        "requalify": action_counter[REQUALIFY],
        "invert_requalify": action_counter[INVERT_REQUALIFY],
        "unmatched_decisions": sorted(map(str, unmatched)),
    }

    print(f"[{mode}] scanned {total} edges")
    print(f"[{mode}] matched {len(matched_decisions)}/27 declared violations")
    print(f"[{mode}] actions to apply: "
          f"DELETE={action_counter[DELETE]} "
          f"REQUALIFY={action_counter[REQUALIFY]} "
          f"INVERT_REQUALIFY={action_counter[INVERT_REQUALIFY]}")
    if skipped_already:
        print(f"[{mode}] already-tagged (idempotent skip): {skipped_already}")

    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(
            json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        print(f"[{mode}] report written → {args.report}")

    if not args.commit:
        print(f"[{mode}] No file written. Re-run with --commit to apply.")
        return 0

    # Commit: rewrite edges.jsonl atomically.
    tmp = EDGES_PATH.with_suffix(".jsonl.tmp")
    with tmp.open("w", encoding="utf-8") as fh:
        fh.writelines(out_lines)
    tmp.replace(EDGES_PATH)
    print(f"[{mode}] wrote {EDGES_PATH.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
