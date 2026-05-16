#!/usr/bin/env python3
"""Wave I — Position ↔ Debate wiring — 2026-05-16.

Audit-fix wave addressing the comprehensive KG audit's "frontend debate
panel blocker" finding: 8 ``position_*`` nodes (Compatibilism,
Libertarianism, Hard/Soft Determinism, Indeterminism, Fatalism,
Theological Determinism, Academic Skepticism on Fate) exist but are
unconnected to any of the 17 ``debate_*`` nodes. The frontend cannot
render the "positions in this debate" sidebar because the
debate → position relation is not materialised.

The script does three things:

1. **I1 — Ontology**: adds two new predicates ``has_position`` and its
   inverse ``position_in_debate`` to ``knowledge graph/ontology/edge_types.json``.
   The canonical RDF-ish predicate for the debate → position relation
   was absent (``argues_for`` targets a position but takes a person /
   argument as source — not a debate). Justification for this
   exceptional ontology addition: no existing predicate captures the
   structural "debate hosts these stances" semantics, and both the
   audit and the Wave I plan explicitly require it.

2. **I2 — Wiring**: inserts ``debate → has_position → position`` edges
   for the 17 debate × ≥2 positions mapping defined below. Every
   debate receives at least 2 positions (the audit's minimum); every
   one of the 8 ``position_*`` nodes is referenced by at least 1 debate.

3. **I3 — Proponents** (``person → holds_position``): deferred to a
   future wave, since matching ancient/modern thinkers to positions
   per debate requires per-claim scholarship verification that exceeds
   the structural scope of Wave I.

ZERO fabricated content. All 17 debate ids and 8 position ids verified
against ``data/kg/nodes.jsonl`` prior to encoding.

Idempotent: signatures ``(source, "has_position", target)`` are
deduplicated against existing edges; rerunning the script is a no-op
(0 added, all skipped_existing).
"""

from __future__ import annotations

import json
import shutil
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
NODES_PATH = ROOT / "data" / "kg" / "nodes.jsonl"
EDGES_PATH = ROOT / "data" / "kg" / "edges.jsonl"
ONTOLOGY_PATH = ROOT / "knowledge graph" / "ontology" / "edge_types.json"

WAVE_TAG = "wave_i_position_debate_wiring_2026_05_16"
SNAPSHOT_DIR = ROOT / "data" / "kg" / "snapshots" / f"2026-05-16-pre-{WAVE_TAG}"

NOW_ISO = datetime.now(UTC).isoformat(sep=" ")


# ---------------------------------------------------------------------------
# Debate → positions mapping
#
# Each debate is wired to ≥2 positions. Coverage check (in main()) verifies
# all 8 position_* nodes are referenced by at least one debate.
# ---------------------------------------------------------------------------

DEBATE_POSITIONS: dict[str, list[str]] = {
    "debate_compatibility_question_ea55e118": [
        "position_compatibilism",
        "position_libertarianism_freewill",
        "position_hard_determinism",
        "position_soft_determinism",
    ],
    "debate_divine_foreknowledge_future_contingents_a7b8c9d0": [
        "position_compatibilism",
        "position_libertarianism_freewill",
        "position_theological_determinism",
    ],
    "debate_divine_foreknowledge_235f2530": [
        "position_libertarianism_freewill",
        "position_theological_determinism",
    ],
    "debate_alexander_stoics_determinism": [
        "position_libertarianism_freewill",
        "position_soft_determinism",
    ],
    "debate_discovery_of_will": [
        "position_libertarianism_freewill",
        "position_compatibilism",
    ],
    "debate_randomness_objection_ae34a974": [
        "position_libertarianism_freewill",
        "position_indeterminism",
    ],
    "debate_prohairesis_meaning": [
        "position_libertarianism_freewill",
        "position_compatibilism",
    ],
    "debate_stoic_compatibilism": [
        "position_soft_determinism",
        "position_compatibilism",
        "position_libertarianism_freewill",
    ],
    "debate_stoic_academic_hellenistic": [
        "position_soft_determinism",
        "position_compatibilism",
        "position_academic_skepticism_fate",
    ],
    "debate_lazy_argument": [
        "position_fatalism",
        "position_compatibilism",
        "position_soft_determinism",
    ],
    "debate_epicurus_free_will": [
        "position_libertarianism_freewill",
        "position_indeterminism",
        "position_hard_determinism",
    ],
    "debate_augustine_pelagius_grace": [
        "position_libertarianism_freewill",
        "position_theological_determinism",
    ],
    "debate_christian_gnostic_freedom": [
        "position_libertarianism_freewill",
        "position_theological_determinism",
        "position_fatalism",
    ],
    "debate_intellectualism_vs_voluntarism_w3x4y5z6": [
        "position_compatibilism",
        "position_libertarianism_freewill",
    ],
    "debate_middle_platonist_fate_interpretation": [
        "position_compatibilism",
        "position_soft_determinism",
    ],
    "debate_occasionalism_vs_secondary_causation_e1f2g3h4": [
        "position_theological_determinism",
        "position_compatibilism",
        "position_libertarianism_freewill",
    ],
    "debate_source_of_action_90c57974": [
        "position_compatibilism",
        "position_libertarianism_freewill",
    ],
}


# ---------------------------------------------------------------------------
# Ontology additions
# ---------------------------------------------------------------------------

NEW_PREDICATES: dict[str, dict[str, Any]] = {
    "has_position": {
        "description": (
            "A debate or controversy has a stance/position as one of its sides. "
            "Modern scholars and ancient thinkers can hold the position via "
            "'holds_position' (inverse)."
        ),
        "category": "structural",
        "inverse": "position_in_debate",
        "source_types": ["debate", "controversy"],
        "target_types": ["position"],
    },
    "position_in_debate": {
        "description": (
            "A position belongs to a debate or controversy (inverse of has_position)."
        ),
        "category": "structural",
        "inverse": "has_position",
        "source_types": ["position"],
        "target_types": ["debate", "controversy"],
    },
}


# ---------------------------------------------------------------------------
# IO helpers
# ---------------------------------------------------------------------------


def load_nodes() -> list[dict[str, Any]]:
    with NODES_PATH.open() as fh:
        return [json.loads(line) for line in fh if line.strip()]


def load_edges() -> list[dict[str, Any]]:
    with EDGES_PATH.open() as fh:
        return [json.loads(line) for line in fh if line.strip()]


def write_edges(edges: list[dict[str, Any]]) -> None:
    with EDGES_PATH.open("w") as fh:
        for e in edges:
            fh.write(json.dumps(e, ensure_ascii=False) + "\n")


def get_node_id(n: dict[str, Any]) -> str:
    return n.get("node_id") or n.get("id") or ""


def make_snapshot() -> None:
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    snap_nodes = SNAPSHOT_DIR / "nodes.jsonl"
    snap_edges = SNAPSHOT_DIR / "edges.jsonl"
    snap_onto = SNAPSHOT_DIR / "edge_types.json"
    if snap_nodes.exists() and snap_edges.exists() and snap_onto.exists():
        print(f"[snapshot] already exists at {SNAPSHOT_DIR.relative_to(ROOT)} - skip")
        return
    shutil.copy2(NODES_PATH, snap_nodes)
    shutil.copy2(EDGES_PATH, snap_edges)
    shutil.copy2(ONTOLOGY_PATH, snap_onto)
    print(f"[snapshot] written to {SNAPSHOT_DIR.relative_to(ROOT)}")


# ---------------------------------------------------------------------------
# Ontology mutation (preserves existing serialization style)
# ---------------------------------------------------------------------------


def update_ontology() -> tuple[bool, bool]:
    """Add has_position + position_in_debate to ontology, preserving style.

    Returns (added_has_position, added_position_in_debate).
    The file uses json.dumps(o, indent=2, ensure_ascii=False, sort_keys=False) +
    trailing newline; preserving insertion order keeps the diff minimal.
    """
    with ONTOLOGY_PATH.open() as fh:
        ontology = json.load(fh)

    edge_types = ontology.get("edge_types", {})
    added_hp = "has_position" not in edge_types
    added_pid = "position_in_debate" not in edge_types

    if added_hp:
        edge_types["has_position"] = NEW_PREDICATES["has_position"]
    if added_pid:
        edge_types["position_in_debate"] = NEW_PREDICATES["position_in_debate"]

    if not (added_hp or added_pid):
        return (False, False)

    # Re-serialise with the exact same options as the existing file. Verified
    # by roundtrip equality: `json.dumps(o, indent=2, ensure_ascii=False,
    # sort_keys=False)` reproduces the file byte-for-byte plus trailing \n.
    serialised = json.dumps(ontology, indent=2, ensure_ascii=False, sort_keys=False)
    if not serialised.endswith("\n"):
        serialised += "\n"
    with ONTOLOGY_PATH.open("w") as fh:
        fh.write(serialised)

    return (added_hp, added_pid)


# ---------------------------------------------------------------------------
# Edge construction
# ---------------------------------------------------------------------------


def edge_signature(e: dict[str, Any]) -> tuple[str, str, str]:
    return (
        e.get("source_id") or e.get("source") or "",
        e.get("relation") or "",
        e.get("target_id") or e.get("target") or "",
    )


def build_has_position_edge(debate_id: str, position_id: str) -> dict[str, Any]:
    metadata: dict[str, Any] = {
        "wave": WAVE_TAG,
        "confidence": 0.9,
    }
    return {
        "created_at": NOW_ISO,
        "edge_id": str(uuid.uuid4()),
        "metadata": json.dumps(metadata, ensure_ascii=False),
        "relation": "has_position",
        "source": debate_id,
        "source_id": debate_id,
        "target": position_id,
        "target_id": position_id,
        "weight": 1.0,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    print(f"[wave-i] start :: wave={WAVE_TAG}")

    make_snapshot()

    # ---- I1 — Ontology
    added_hp, added_pid = update_ontology()
    print(
        f"[wave-i] ontology_has_position_added={added_hp}  "
        f"ontology_position_in_debate_added={added_pid}"
    )

    # ---- Load
    nodes = load_nodes()
    edges = load_edges()
    print(f"[load] nodes={len(nodes):,} ; edges={len(edges):,}")

    node_ids: set[str] = {get_node_id(n) for n in nodes}
    edges_signatures: set[tuple[str, str, str]] = {edge_signature(e) for e in edges}

    # ---- Verify all debates + positions exist in KG (defensive)
    for debate_id, positions in DEBATE_POSITIONS.items():
        if debate_id not in node_ids:
            print(f"[wave-i][FATAL] debate not found in KG: {debate_id}")
            return 1
        for pos in positions:
            if pos not in node_ids:
                print(f"[wave-i][FATAL] position not found in KG: {pos}")
                return 1

    # ---- I2 — Wire debates → positions
    added = 0
    skipped_existing = 0
    debates_wired: set[str] = set()
    positions_used: set[str] = set()
    new_edges: list[dict[str, Any]] = []

    for debate_id, positions in DEBATE_POSITIONS.items():
        for pos in positions:
            sig = (debate_id, "has_position", pos)
            if sig in edges_signatures:
                skipped_existing += 1
                debates_wired.add(debate_id)
                positions_used.add(pos)
                continue
            edge = build_has_position_edge(debate_id, pos)
            new_edges.append(edge)
            edges_signatures.add(sig)
            added += 1
            debates_wired.add(debate_id)
            positions_used.add(pos)

    if new_edges:
        edges.extend(new_edges)
        write_edges(edges)

    # ---- Counters
    print(
        f"[wave-i] has_position_edges_added={added}  "
        f"has_position_edges_skipped_existing={skipped_existing}"
    )
    print(
        f"[wave-i] debates_wired={len(debates_wired)}/17  "
        f"positions_used={len(positions_used)}/8"
    )
    print("[wave-i] proponent_edges_added=0  # deferred to future wave (Wave I3)")
    print(f"[wave-i] done :: edges {len(edges) - len(new_edges):,} → {len(edges):,}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
