#!/usr/bin/env python3
"""Merge the confirmed C4 duplicate pairs. Dry-run first.

    PYTHONPATH=. python3 scripts/apply_2026_09_24_c4_duplicate_merges.py --dry-run
    PYTHONPATH=. python3 scripts/apply_2026_09_24_c4_duplicate_merges.py --apply
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from scripts.data_2026_09_24_c4_duplicate_merges import (
    DROP_EDGES,
    MERGES,
    NOT_MERGED,
    TAKE_DESCRIPTION_IF_SURVIVOR_IS_TITLE,
)
from scripts.verification_2026_09_24_lib import ROOT, Store, meta, set_meta, write_decisions

SLUG = "c4_duplicate_merges"
STAMP = "c4_duplicate_merges_2026_09_24"
NOW = "2026-09-24 00:00:00+00:00"
ONTOLOGY = json.loads((ROOT / "knowledge graph/ontology/edge_types.json").read_text())
ET = ONTOLOGY.get("edge_types", ONTOLOGY)
INVERSE = {k: v.get("inverse") for k, v in ET.items()} if isinstance(ET, dict) else {}
POINTER_KEYS = ("work_node_id", "work_canonical_id", "scholarly_work_id", "publication",
                "author_id", "scholar_id", "original_node_id", "source_passage_id")


def alt_names(node) -> list[str]:
    raw = node.get("alternative_names") or []
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except json.JSONDecodeError:
            raw = [raw]
    return list(raw)


def set_alt_names(node, names: list[str]) -> None:
    if isinstance(node.get("alternative_names"), str) or node.get("alternative_names") is None:
        node["alternative_names"] = json.dumps(names, ensure_ascii=False)
    else:
        node["alternative_names"] = names


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    store = Store()
    nodes = store.nodes
    decisions, skipped = [], []
    for survivor, absorbed, reason in MERGES:
        if absorbed not in nodes:
            skipped.append((absorbed, "absent (already merged?)"))
            continue
        if survivor not in nodes:
            skipped.append((survivor, "survivor missing"))
            continue
        dst, src = nodes[survivor], nodes[absorbed]
        if dst.get("type") != src.get("type"):
            skipped.append((absorbed, "type differs"))
            continue
        dm, sm = meta(dst), meta(src)
        if dm.get(STAMP):
            skipped.append((survivor, "already stamped"))
            continue
        ported = []
        for key, value in sm.items():
            if key in ("merged_from", "previous_node_id") or value in (None, "", [], {}):
                continue
            # Text variants of the absorbed description are not facts about
            # the survivor; the absorbed record is kept whole in quarantine.
            if key.startswith(("description", "translation_")):
                continue
            if dm.get(key) in (None, "", [], {}):
                dm[key] = value
                ported.append(key)
        desc_note = "survivor description kept"
        title = str(dm.get("title") or "").strip()
        if survivor in TAKE_DESCRIPTION_IF_SURVIVOR_IS_TITLE and (dst.get("description") or "").strip() == title:
            dm[f"{STAMP}_previous_description"] = dst.get("description")
            dst["description"] = src.get("description")
            desc_note = "absorbed description adopted (survivor held only its title)"
        elif src.get("description"):
            dm[f"{STAMP}_absorbed_description"] = src["description"]
        names = alt_names(dst)
        for name in [src.get("label"), *alt_names(src)]:
            if name and name != dst.get("label") and name not in names:
                names.append(name)
        set_alt_names(dst, names)
        dm["merged_from"] = sorted(set((dm.get("merged_from") or []) + [absorbed]))
        prev = dm.get("previous_node_id")
        prev = prev if isinstance(prev, list) else ([prev] if prev else [])
        dm["previous_node_id"] = sorted(set(prev + [absorbed]))
        dm[STAMP] = {"absorbed": absorbed, "reason": reason, "ported_keys": sorted(ported)}
        set_meta(dst, dm)
        dst["updated_at"] = NOW

        # Edges: redirect, then drop self-loops, duplicates and inverse twins.
        log = []
        for (s, r, t), why in DROP_EDGES.items():
            if absorbed in (s, t):
                n = store.remove_edges(lambda e, s=s, r=r, t=t: (e["source"], e["relation"], e["target"]) == (s, r, t), why)
                log.append(f"dropped {s} -{r}-> {t}: {why}" if n else f"expected drop absent: {s} -{r}-> {t}")
        existing = {(e["source"], e["relation"], e["target"]) for e in store.edges if absorbed not in (e["source"], e["target"])}
        to_drop = []
        for e in store.edges:
            if absorbed not in (e["source"], e["target"]):
                continue
            s = survivor if e["source"] == absorbed else e["source"]
            t = survivor if e["target"] == absorbed else e["target"]
            triple = (s, e["relation"], t)
            inv = INVERSE.get(e["relation"])
            if s == t:
                to_drop.append((e["edge_id"], f"self-loop after merge: {e['relation']}"))
            elif triple in existing:
                to_drop.append((e["edge_id"], "duplicate of a survivor edge after merge"))
            elif inv and (t, inv, s) in existing:
                to_drop.append((e["edge_id"], f"inverse twin of survivor edge {t} -{inv}-> {s}"))
            else:
                data = e.get("metadata") if isinstance(e.get("metadata"), dict) else {}
                data = dict(data or {})
                data[STAMP] = {"redirected_from": absorbed}
                e["metadata"] = data
                e["source"] = e["source_id"] = s
                e["target"] = e["target_id"] = t
                existing.add(triple)
                log.append(f"redirected {e['relation']} ({s} -> {t})")
        for eid, why in to_drop:
            store.remove_edges(lambda e, eid=eid: e["edge_id"] == eid, f"merge {absorbed} -> {survivor}: {why}")
            log.append(f"dropped edge {eid}: {why}")
        # Pointers and corpus citations.
        for node in store.rows["nodes"]:
            m = meta(node)
            hit = [k for k in POINTER_KEYS if m.get(k) == absorbed]
            if hit:
                for k in hit:
                    m[k] = survivor
                set_meta(node, m)
                log.append(f"pointer {node['id']}.{','.join(hit)}")
        for c in store.rows["citations"]:
            if c["kg_node_id"] == absorbed:
                c["kg_node_id"] = survivor
                log.append(f"citation {c['passage_id']}")
        store.remove_node(absorbed, f"merged into {survivor}: {reason}")
        decisions.append({
            "item_id": f"{survivor} <- {absorbed}",
            "queue": "c4_dedup_schools/queue_likely_duplicates.csv",
            "claim_checked": "The two nodes denote one and the same entity.",
            "verdict": "merged",
            "evidence": {"survivor_label": dst.get("label"), "absorbed_label": src.get("label")},
            "source": "both nodes' own labels, descriptions and metadata (edition / DOI)",
            "method": "read both records in full and every edge touching them",
            "jev": "c4 same_entity p ≥ 0.9",
            "change": {"ported_metadata": sorted(ported), "description": desc_note, "edges": log},
        })
    for (a, b), why in NOT_MERGED.items():
        decisions.append({
            "item_id": f"{a} / {b}",
            "queue": "c4_dedup_schools/queue_likely_duplicates.csv",
            "claim_checked": "The two nodes should be merged.",
            "verdict": "false_positive",
            "evidence": why,
            "source": "edges.jsonl same_thesis_as (semantic_merges_2026_08_17)",
            "method": "read both records and their edges",
            "jev": "c4 same_entity p = 0.93",
            "change": "none",
        })
    summary = store.commit(SLUG, apply=args.apply and not args.dry_run)
    if args.apply and not args.dry_run:
        write_decisions(SLUG, decisions)
    print(json.dumps({"mode": "apply" if args.apply and not args.dry_run else "dry_run",
                      "merged": sum(d["verdict"] == "merged" for d in decisions),
                      "skipped": skipped, "changes": summary,
                      "log": [d["change"] for d in decisions if d["verdict"] == "merged"]},
                     ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
