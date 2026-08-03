#!/usr/bin/env python3
"""Integrate full-text enrichment patches for Long 2002 + Dobbin 1991.

Both publication nodes and both scholar nodes already exist (created from
secondary references). The acquired full texts let us attach local_pdf_path +
verbatim-evidenced argument nodes (quote + exact page) to the existing nodes.

Per patch (data/kg/enrichment_patches/*.json):
  - enrich the existing publication node: local_pdf_path, fulltext_reading_note
  - create scholarly_argument nodes with quote_verbatim + page (e2-verified)
  - wire created_by (arg -> scholar) + discusses (arg -> existing targets)

Plus one cross-work scholarly disagreement (a genuine find from the reading):
Long 2002 explicitly rejects Dobbin 1991's reading that prohairesis breaks the
causal nexus / is "immune to fate" -> `critiques` edge between the two args.

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
PATCHES_DIR = ROOT / "data" / "kg" / "enrichment_patches"
SNAPSHOT_DIR = ROOT / "data" / "kg" / "snapshots" / "2026-05-21-pre-enrichment-patches"

WAVE = "enrichment_patches_2026_05_21"
NOW = datetime.now(UTC).isoformat(sep=" ")

# Long 2002 (p.221/229) contests Dobbin 1991 (p.133): freedom "immune to fate"
CRITIQUES = (
    "scholarly_argument_long_2002_freedom_not_freedom_from_fate",
    "scholarly_argument_dobbin_1991_preserve_of_freedom_bounded_by_self",
)
CRITIQUE_NOTE = (
    "Long 2002 (esp. pp. 221, 229) rejects Dobbin 1991's reading that "
    "Epictetus' prohairesis is a preserve of freedom 'immune to fate' / "
    "breaking the causal nexus: 'I do not find it ultimately compelling' "
    "(p. 229). Long holds Epictetus' freedom is compliance with fate, not "
    "freedom from antecedent causation."
)


def edge_key(e: dict) -> tuple:
    return ((e.get("source") or e.get("source_id")),
            (e.get("target") or e.get("target_id")), e.get("relation"))


def main(commit: bool) -> int:
    node_lines = NODES_PATH.read_text(encoding="utf-8").splitlines()
    node_lines = [ln for ln in node_lines if ln.strip()]
    idx_by_id: dict[str, int] = {}
    ids: set[str] = set()
    for i, ln in enumerate(node_lines):
        nid = json.loads(ln).get("id")
        idx_by_id[nid] = i
        ids.add(nid)

    edge_lines = [ln for ln in EDGES_PATH.read_text(encoding="utf-8").splitlines() if ln.strip()]
    sigs = {edge_key(json.loads(ln)) for ln in edge_lines}

    new_nodes: list[dict] = []
    new_edges: list[dict] = []
    pubs_enriched = 0
    args_created = 0

    for pf in sorted(PATCHES_DIR.glob("*.json")):
        d = json.loads(pf.read_text(encoding="utf-8"))
        pub_id = d["publication_id"]
        scholar_id = d["scholar_id"]
        assert pub_id in ids, f"pub {pub_id} missing"
        assert scholar_id in ids, f"scholar {scholar_id} missing"

        # enrich publication node (in place, idempotent)
        pi = idx_by_id[pub_id]
        pub = json.loads(node_lines[pi])
        pmd = pub.get("metadata")
        pmd = json.loads(pmd) if isinstance(pmd, str) and pmd else (pmd or {})
        if not pmd.get("fulltext_read"):
            pmd["fulltext_read"] = True
            pmd["fulltext_read_at"] = NOW
            pmd["local_pdf_path"] = d.get("local_pdf_path")
            if d.get("pub_description_note"):
                pmd["fulltext_reading_note"] = d["pub_description_note"]
            pmd["wave"] = WAVE
            pub["metadata"] = json.dumps(pmd, ensure_ascii=False)
            pub["updated_at"] = NOW
            node_lines[pi] = json.dumps(pub, ensure_ascii=False)
            pubs_enriched += 1

        # create argument nodes
        for a in d.get("arguments", []):
            aid = a["id"]
            if aid in ids:
                continue
            amd = {
                "quote_verbatim": a.get("quote_verbatim"),
                "page": a.get("page"),
                "e2_verified_at": NOW,
                "e2_verified_by": f"fulltext_read_{pf.stem}",
                "e2_publication_id": pub_id,
                "needs_evidence": False,
                "wave": WAVE,
            }
            new_nodes.append({
                "id": aid, "node_id": aid, "type": "argument",
                "label": a.get("label", aid), "description": a.get("description", ""),
                "period": "Modern", "role": None, "school": None,
                "alternative_names": json.dumps([], ensure_ascii=False),
                "metadata": json.dumps(amd, ensure_ascii=False),
                "confidence": 0.9, "created_at": NOW, "updated_at": NOW,
            })
            ids.add(aid)
            args_created += 1
            # created_by -> scholar
            k = (aid, scholar_id, "created_by")
            if k not in sigs:
                new_edges.append({"source": aid, "target": scholar_id,
                                  "relation": "created_by", "confidence": 1.0,
                                  "metadata": {"wave": WAVE}})
                sigs.add(k)
            # discusses -> existing targets
            for tgt in (a.get("discusses") or []):
                if tgt not in ids:
                    continue
                k = (aid, tgt, "discusses")
                if k not in sigs:
                    new_edges.append({"source": aid, "target": tgt,
                                      "relation": "discusses", "confidence": 0.85,
                                      "metadata": {"wave": WAVE}})
                    sigs.add(k)

    # cross-work critiques edge
    src, tgt = CRITIQUES
    crit_added = False
    if src in ids and tgt in ids and (src, tgt, "critiques") not in sigs:
        new_edges.append({"source": src, "target": tgt, "relation": "critiques",
                          "confidence": 0.9, "metadata": {"wave": WAVE, "note": CRITIQUE_NOTE}})
        sigs.add((src, tgt, "critiques"))
        crit_added = True

    print(f"pubs enriched: {pubs_enriched} | args created: {args_created} | "
          f"new edges: {len(new_edges)} | critiques edge: {crit_added}")
    if not new_nodes and not new_edges and pubs_enriched == 0:
        print("OK: nothing to apply (idempotent).")
        return 0
    if not commit:
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
    print(f"DONE: +{len(new_nodes)} nodes, +{len(new_edges)} edges, {pubs_enriched} pubs enriched")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--commit", action="store_true")
    sys.exit(main(ap.parse_args().commit))
