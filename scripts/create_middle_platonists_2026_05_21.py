#!/usr/bin/env python3
"""Create 4 Middle Platonist source-author nodes flagged by Boys-Stones 2018.

The Boys-Stones reading agent flagged 5 source-authors absent from the KG.
Four are securely Middle Platonist and wirable to existing Boys-Stones args
without overclaiming (Numenius, Atticus, Celsus, Nicostratus). The fifth,
Aristides Quintilianus (a music theorist, only a minor witness), is deferred
to avoid a forced school membership.

Wiring (only what Boys-Stones' chapter notes support):
  - member_of school_middle_platonism for all 4
  - discusses (arg -> person) for the providence / cyclical-recurrence args
  - discusses (person -> concept_sea_battle) for Nicostratus (De Int. 9 witness)
  - critiques (Origen -> Celsus): Contra Celsum is a refutation of Celsus

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
SNAPSHOT_DIR = ROOT / "data" / "kg" / "snapshots" / "2026-05-21-pre-middle-platonists"

WAVE = "middle_platonists_2026_05_21"
NOW = datetime.now(UTC).isoformat(sep=" ")
SCHOOL = "school_middle_platonism"
ORIGEN = "person_origen_alexandria_185_254ce_s9t0u1v2"
SEA_BATTLE = "concept_sea_battle_future_contingents"

PERSONS = [
    {
        "id": "person_numenius_apamea_2c_ce", "label": "Numenius of Apamea",
        "description": (
            "Greek philosopher (fl. later 2nd c. CE), a leading Neopythagorean "
            "and Middle Platonist from Apamea in Syria. Author of On the Good "
            "(Περὶ τἀγαθοῦ) and On the Secret Doctrines of Plato; distinguished "
            "a first god (pure intellect) from a demiurgic second god, a "
            "structure that deeply influenced Plotinus and Origen. Cited by "
            "Boys-Stones (2018) for the Middle Platonist 'providence by proxy' "
            "scheme and a reading of the Myth of Er."),
        "alt": ["Numenius", "Noumenios"],
    },
    {
        "id": "person_atticus_2c_ce", "label": "Atticus (Middle Platonist)",
        "description": (
            "Middle Platonist (fl. c. 176 CE), possibly holder of the imperial "
            "chair of Platonic philosophy at Athens under Marcus Aurelius. A "
            "vigorous critic of Aristotle, especially on divine providence and "
            "the immortality of the soul; his fragments survive chiefly in "
            "Eusebius' Praeparatio Evangelica. Boys-Stones (2018) treats him as "
            "a key source for the doctrine that divine providence does not "
            "determine individuals."),
        "alt": ["Atticus"],
    },
    {
        "id": "person_celsus_platonist_2c_ce", "label": "Celsus (the Platonist)",
        "description": (
            "2nd-c. CE Platonist philosopher, author of the anti-Christian "
            "polemic Alēthēs Logos (Ἀληθὴς Λόγος, 'True Doctrine', c. 175-180 "
            "CE), known almost entirely through Origen's refutation Contra "
            "Celsum (c. 248 CE). A witness to Middle Platonist views on "
            "providence, fate, and exact cyclical recurrence; relevant to the "
            "thesis through Origen's reception."),
        "alt": ["Celsus", "Kelsos"],
    },
    {
        "id": "person_nicostratus_2c_ce", "label": "Nicostratus (Middle Platonist)",
        "description": (
            "2nd-c. CE Middle Platonist, known for critical aporiai on "
            "Aristotle's Categories. Cited by Boys-Stones (2018) as a Platonist "
            "witness on future contingents and the sea-battle problem of "
            "Aristotle's De Interpretatione 9."),
        "alt": ["Nicostratus"],
    },
]

MEMBER_OF = [p["id"] for p in PERSONS]

# discusses: argument -> person
ARG_DISCUSSES = {
    "scholarly_argument_boys_stones_2018_secondary_tertiary_providence":
        ["person_numenius_apamea_2c_ce", "person_atticus_2c_ce"],
    "scholarly_argument_boys_stones_2018_myth_of_er_discarnate_indeterminacy":
        ["person_numenius_apamea_2c_ce"],
    "scholarly_argument_boys_stones_2018_no_divine_determination_individuals":
        ["person_atticus_2c_ce"],
    "scholarly_argument_boys_stones_2018_cyclical_recurrence_no_astral_determinism":
        ["person_celsus_platonist_2c_ce"],
    "scholarly_argument_boys_stones_2018_origen_platonists_no_better_than_stoics":
        ["person_celsus_platonist_2c_ce"],
}


def edge_key(e: dict) -> tuple:
    return ((e.get("source") or e.get("source_id")),
            (e.get("target") or e.get("target_id")), e.get("relation"))


def main(commit: bool) -> int:
    node_lines = [ln for ln in NODES_PATH.read_text(encoding="utf-8").splitlines() if ln.strip()]
    ids = {json.loads(ln).get("id") for ln in node_lines}
    edge_lines = [ln for ln in EDGES_PATH.read_text(encoding="utf-8").splitlines() if ln.strip()]
    sigs = {edge_key(json.loads(ln)) for ln in edge_lines}

    new_nodes, new_edges = [], []

    for p in PERSONS:
        if p["id"] in ids:
            continue
        new_nodes.append({
            "id": p["id"], "node_id": p["id"], "type": "person", "label": p["label"],
            "description": p["description"], "period": "Imperial", "role": None,
            "school": "Middle Platonism",
            "alternative_names": json.dumps(p["alt"], ensure_ascii=False),
            "metadata": json.dumps({"wave": WAVE, "source": "Boys-Stones 2018 source-author tier"}, ensure_ascii=False),
            "created_at": NOW, "updated_at": NOW,
        })
        ids.add(p["id"])

    def add_edge(s, t, rel, conf, note=None):
        if s not in ids or t not in ids:
            return
        k = (s, t, rel)
        if k in sigs:
            return
        md = {"wave": WAVE}
        if note:
            md["note"] = note
        new_edges.append({"source": s, "target": t, "relation": rel, "confidence": conf, "metadata": md})
        sigs.add(k)

    for pid in MEMBER_OF:
        add_edge(pid, SCHOOL, "member_of", 0.85)
    for arg, persons in ARG_DISCUSSES.items():
        for pid in persons:
            add_edge(arg, pid, "discusses", 0.8)
    add_edge("person_nicostratus_2c_ce", SEA_BATTLE, "discusses", 0.7,
             "Boys-Stones 2018: Nicostratus witness on De Int. 9 future contingents")
    add_edge(ORIGEN, "person_celsus_platonist_2c_ce", "critiques", 0.95,
             "Origen's Contra Celsum (c. 248 CE) refutes Celsus' Alēthēs Logos")

    print(f"new persons: {len(new_nodes)} | new edges: {len(new_edges)}")
    if not new_nodes and not new_edges:
        print("OK: nothing to apply (idempotent).")
        return 0
    if not commit:
        for n in new_nodes:
            print("  NODE", n["id"])
        for e in new_edges:
            print(f"  EDGE {e['source']} --{e['relation']}--> {e['target']}")
        print("[DRY-RUN] --commit to write.")
        return 0

    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(NODES_PATH, SNAPSHOT_DIR / NODES_PATH.name)
    shutil.copy2(EDGES_PATH, SNAPSHOT_DIR / EDGES_PATH.name)
    node_lines.extend(json.dumps(n, ensure_ascii=False) for n in new_nodes)
    edge_lines.extend(json.dumps(e, ensure_ascii=False) for e in new_edges)
    NODES_PATH.write_text("\n".join(node_lines) + "\n", encoding="utf-8")
    EDGES_PATH.write_text("\n".join(edge_lines) + "\n", encoding="utf-8")
    print(f"snapshot: {SNAPSHOT_DIR}")
    print(f"DONE: +{len(new_nodes)} nodes, +{len(new_edges)} edges")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--commit", action="store_true")
    sys.exit(main(ap.parse_args().commit))
