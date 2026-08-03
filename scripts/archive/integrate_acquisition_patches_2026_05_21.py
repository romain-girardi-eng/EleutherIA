#!/usr/bin/env python3
"""Integrate 9 acquisition reading-patches into the KG (2026-05-21).

Sub-agents read 9 newly acquired full-text works and produced JSON patches in
data/kg/acquisition_patches/ with: scholar (if new) + publication + arguments
(verbatim + page) + suggested edges + new concepts.

Schemas vary across agents — this script normalises:
  - arguments under `arguments` | `scholarly_arguments`
  - targets under `discusses` | `relates_to` | `related_persons` | `edges`
  - quote under `quote_verbatim` | `verbatim_evidence` | `verbatim_anchors`
  - page under `page` | `page_or_loc` | metadata

Also creates the missing canonical node `person_paul_apostle` (flagged by the
Barclay + Eastman agents — no apostle-Paul node existed, only J.-P. Sartre).

Idempotent. Snapshot before mutation. Dry-run by default; --commit to write.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
NODES_PATH = ROOT / "data" / "kg" / "nodes.jsonl"
EDGES_PATH = ROOT / "data" / "kg" / "edges.jsonl"
PATCHES_DIR = ROOT / "data" / "kg" / "acquisition_patches"
SNAPSHOT_DIR = ROOT / "data" / "kg" / "snapshots" / "2026-05-21-pre-acquisition-patches"

WAVE = "acquisition_patches_2026_05_21"
NOW = datetime.now(UTC).isoformat(sep=" ")

ID_PAUL = "person_paul_apostle"

# Ontology: arg→person/concept/work/school = discusses (valid). pub→person = authored_by.
# scholarly_argument → scholar = created_by (KG convention).


def load_jsonl(path: Path) -> list[str]:
    return [ln.rstrip("\n") for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]


def node_id(line: str) -> str:
    return json.loads(line).get("id") or ""


def edge_sig(e: dict) -> tuple:
    return (e.get("source") or e.get("source_id") or "",
            e.get("target") or e.get("target_id") or "",
            e.get("relation") or "")


def norm_targets(arg: dict) -> list[str]:
    """Collect all target node-ids referenced by an arg, across schema variants."""
    out: list[str] = []
    for key in ("discusses", "relates_to", "related_persons", "related_arguments", "related_groups"):
        v = arg.get(key)
        if isinstance(v, list):
            out.extend(x for x in v if isinstance(x, str))
    # Blowers-style edges: list of {target, relation}
    for e in arg.get("edges", []) or []:
        if isinstance(e, dict):
            t = e.get("target") or e.get("target_id")
            if isinstance(t, str):
                out.append(t)
    return out


def norm_quote(arg: dict) -> dict:
    """Extract quote/page/chapter into a normalised metadata sub-dict."""
    md: dict[str, Any] = {}
    for k in ("quote_verbatim", "quote_de", "quote_fr", "translation_en",
              "verbatim_evidence", "page", "page_or_loc", "chapter",
              "confidence", "verbatim_anchors"):
        if arg.get(k) is not None:
            md[k] = arg[k]
    return md


def main(commit: bool) -> int:
    node_lines = load_jsonl(NODES_PATH)
    edge_lines = load_jsonl(EDGES_PATH)
    existing_ids = {node_id(ln) for ln in node_lines}
    edge_sigs = {edge_sig(json.loads(ln)) for ln in edge_lines}

    new_nodes: list[dict] = []
    new_edges: list[dict] = []
    report: list[str] = []

    # --- canonical Paul node (if missing) ---
    if ID_PAUL not in existing_ids:
        new_nodes.append({
            "id": ID_PAUL, "node_id": ID_PAUL, "type": "person",
            "label": "Paul the Apostle",
            "description": (
                "Paul of Tarsus (c. 5 – c. 64/67 CE), apôtre, auteur des "
                "épîtres pauliniennes authentiques (Rm, 1-2 Co, Ga, Ph, "
                "1 Th, Phm). Figure centrale pour l'hypothèse H1 de la "
                "thèse : agentivité divine/humaine, grâce, et le « moi » "
                "paulinien (Rm 7, Rm 9) comme arrière-plan de la "
                "question du libre arbitre chrétien. Node créé 2026-05-21 "
                "pour combler une lacune structurelle (aucun node Paul "
                "n'existait)."
            ),
            "period": "Second Temple Judaism", "role": None, "school": None,
            "alternative_names": json.dumps(["Paul of Tarsus", "Saint Paul", "Saul of Tarsus", "Apôtre Paul"], ensure_ascii=False),
            "metadata": json.dumps({
                "birth_date": "c. 5 CE", "death_date": "c. 64-67 CE",
                "role": "apostle", "wave": WAVE,
            }, ensure_ascii=False),
            "created_at": NOW, "updated_at": NOW,
        })
        existing_ids.add(ID_PAUL)
        report.append(f"NEW PERSON {ID_PAUL}")

    patch_files = sorted(PATCHES_DIR.glob("*.json"))
    for pf in patch_files:
        d = json.loads(pf.read_text(encoding="utf-8"))
        pname = pf.stem

        # --- scholar (optional) ---
        sch = d.get("scholar")
        scholar_id = None
        if isinstance(sch, dict) and sch.get("id"):
            scholar_id = sch["id"]
            if scholar_id not in existing_ids:
                md = sch.get("metadata") or {}
                md["wave"] = WAVE
                new_nodes.append({
                    "id": scholar_id, "node_id": scholar_id, "type": "person",
                    "label": sch.get("label", scholar_id),
                    "description": sch.get("description", ""),
                    "period": "Modern", "role": "scholar", "school": None,
                    "alternative_names": json.dumps([], ensure_ascii=False),
                    "metadata": json.dumps(md, ensure_ascii=False),
                    "created_at": NOW, "updated_at": NOW,
                })
                existing_ids.add(scholar_id)
                report.append(f"NEW SCHOLAR {scholar_id}")

        # --- publication ---
        pub = d.get("publication")
        pub_id = None
        pub_scholar = None
        if isinstance(pub, dict) and pub.get("id"):
            pub_id = pub["id"]
            pub_scholar = pub.get("scholar_id") or scholar_id
            if pub_id not in existing_ids:
                md = pub.get("metadata") or {}
                md["wave"] = WAVE
                new_nodes.append({
                    "id": pub_id, "node_id": pub_id, "type": "publication",
                    "label": pub.get("label", pub_id),
                    "description": pub.get("description", ""),
                    "period": "Modern", "role": None, "school": None,
                    "alternative_names": json.dumps([], ensure_ascii=False),
                    "metadata": json.dumps(md, ensure_ascii=False),
                    "created_at": NOW, "updated_at": NOW,
                })
                existing_ids.add(pub_id)
                report.append(f"NEW PUB    {pub_id}")
            # authored_by edge
            if pub_scholar:
                sig = (pub_id, pub_scholar, "authored_by")
                if sig not in edge_sigs:
                    new_edges.append({"source": pub_id, "target": pub_scholar,
                                      "relation": "authored_by", "confidence": 1.0,
                                      "metadata": {"wave": WAVE}})
                    edge_sigs.add(sig)

        # --- new concepts (explicit only) ---
        for c in (d.get("new_concepts") or []):
            if not isinstance(c, dict):
                continue
            cid = c.get("id")
            if not cid or cid in existing_ids:
                continue
            md = c.get("metadata") or {}
            md["wave"] = WAVE
            new_nodes.append({
                "id": cid, "node_id": cid, "type": "concept",
                "label": c.get("label", cid),
                "description": c.get("description", ""),
                "period": c.get("period", "Late Antiquity"), "role": None, "school": None,
                "alternative_names": json.dumps([], ensure_ascii=False),
                "metadata": json.dumps(md, ensure_ascii=False),
                "created_at": NOW, "updated_at": NOW,
            })
            existing_ids.add(cid)
            report.append(f"NEW CONCEPT {cid}")

        eff_scholar = scholar_id or pub_scholar  # for created_by when patch has no scholar dict

        # --- arguments ---
        args = d.get("arguments") or d.get("scholarly_arguments") or []
        for arg in args:
            aid = arg.get("id")
            if not aid:
                continue
            if aid not in existing_ids:
                amd = norm_quote(arg)
                amd["wave"] = WAVE
                amd["needs_evidence"] = False  # carries verbatim from reading
                amd["e2_verified_at"] = NOW
                amd["e2_verified_by"] = f"acquisition_read_{pname}"
                if pub_id:
                    amd["e2_publication_id"] = pub_id
                new_nodes.append({
                    "id": aid, "node_id": aid, "type": "argument",
                    "label": arg.get("label", aid),
                    "description": arg.get("description", ""),
                    "period": arg.get("period", "Modern"), "role": None, "school": None,
                    "alternative_names": json.dumps([], ensure_ascii=False),
                    "metadata": json.dumps(amd, ensure_ascii=False),
                    "confidence": 0.9,
                    "created_at": NOW, "updated_at": NOW,
                })
                existing_ids.add(aid)
                report.append(f"NEW ARG    {aid}")
            # created_by edge → scholar (fall back to publication's scholar)
            if eff_scholar:
                sig = (aid, eff_scholar, "created_by")
                if sig not in edge_sigs:
                    new_edges.append({"source": aid, "target": eff_scholar,
                                      "relation": "created_by", "confidence": 1.0,
                                      "metadata": {"wave": WAVE}})
                    edge_sigs.add(sig)
            # discusses edges → only to EXISTING targets
            for tgt in norm_targets(arg):
                if tgt not in existing_ids:
                    continue
                sig = (aid, tgt, "discusses")
                if sig not in edge_sigs:
                    new_edges.append({"source": aid, "target": tgt,
                                      "relation": "discusses", "confidence": 0.85,
                                      "metadata": {"wave": WAVE}})
                    edge_sigs.add(sig)

    # Summary
    n_persons = sum(1 for r in report if r.startswith("NEW PERSON") or r.startswith("NEW SCHOLAR"))
    n_pubs = sum(1 for r in report if r.startswith("NEW PUB"))
    n_concepts = sum(1 for r in report if r.startswith("NEW CONCEPT"))
    n_args = sum(1 for r in report if r.startswith("NEW ARG"))
    print(f"Patches: {len(patch_files)}")
    print(f"New nodes: {len(new_nodes)} (persons/scholars={n_persons}, pubs={n_pubs}, concepts={n_concepts}, args={n_args})")
    print(f"New edges: {len(new_edges)}")

    if not new_nodes and not new_edges:
        print("OK: nothing to apply (idempotent).")
        return 0

    if not commit:
        print("\n[DRY-RUN] --commit to write. Sample:")
        for r in report[:25]:
            print("  ", r)
        if len(report) > 25:
            print(f"   ... +{len(report)-25} more")
        return 0

    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(NODES_PATH, SNAPSHOT_DIR / NODES_PATH.name)
    shutil.copy2(EDGES_PATH, SNAPSHOT_DIR / EDGES_PATH.name)
    print(f"snapshot: {SNAPSHOT_DIR}")

    node_lines.extend(json.dumps(n, ensure_ascii=False) for n in new_nodes)
    edge_lines.extend(json.dumps(e, ensure_ascii=False) for e in new_edges)
    NODES_PATH.write_text("\n".join(node_lines) + "\n", encoding="utf-8")
    EDGES_PATH.write_text("\n".join(edge_lines) + "\n", encoding="utf-8")
    print(f"DONE: +{len(new_nodes)} nodes, +{len(new_edges)} edges")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--commit", action="store_true")
    sys.exit(main(ap.parse_args().commit))
