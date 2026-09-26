#!/usr/bin/env python3
"""Apply the confirmed KG corrections of the 2026-09-26 independent audit. Dry-run first.

    PYTHONPATH=. python3 scripts/apply_2026_09_26_independent_audit.py --dry-run
    PYTHONPATH=. python3 scripts/apply_2026_09_26_independent_audit.py --apply

Input: data/audit/2026-09-26_independent_audit_decisions.jsonl, one record per
finding, with the reviewer's claim and the second reviewer's verdict. Only
records with ``apply`` set are touched:

* ``text``   — replace the exact ``claim`` substring by ``replacement`` inside the
  named field (``description``, ``label``, ``period`` or a ``metadata.<key>``
  subtree). The same claim is also replaced wherever else it occurs in the same
  node when it is at least 25 characters long (the English/French doublets of a
  description repeat the same wording). A record whose claim is absent is
  skipped, so a re-run is a no-op.
* ``edge``   — ``drop``, ``reverse`` or ``relabel:<relation>`` (combinable with
  ``;``) on the edge ``source -[relation]-> target``. A reversal that would
  duplicate an existing triple becomes a drop. Dropped edges are quarantined.

Every touched node gets ``metadata.independent_audit_2026_09_26``: the list of
(finding id, field, before, after). Nothing else changes.
"""

from __future__ import annotations

import argparse
import collections
import json
import shutil
from pathlib import Path

from scripts.apply_2026_09_24_c4_duplicate_merges import INVERSE
from scripts.verification_2026_09_24_lib import DATA, Store, meta, set_meta

SLUG = "independent_audit_2026_09_26"
DECISIONS = DATA / "audit" / "2026-09-26_independent_audit_decisions.jsonl"
STAMP = "independent_audit_2026_09_26"
PROPAGATE_MIN = 25


def replace_in(value, old: str, new: str):
    """Replace ``old`` in every string of a JSON-like value; return (value, count)."""
    if isinstance(value, str):
        n = value.count(old)
        return (value.replace(old, new), n) if n else (value, 0)
    if isinstance(value, list):
        out, total = [], 0
        for v in value:
            v2, n = replace_in(v, old, new)
            out.append(v2)
            total += n
        return out, total
    if isinstance(value, dict):
        out, total = {}, 0
        for k, v in value.items():
            v2, n = replace_in(v, old, new)
            out[k] = v2
            total += n
        return out, total
    return value, 0


def apply_text(node: dict, field: str, old: str, new: str) -> tuple[int, int]:
    """Return (hits in the named field, hits propagated elsewhere in the node)."""
    data = meta(node)
    if field.startswith("metadata."):
        key = field.split(".")[1]
        if key not in data:
            return 0, 0
        data[key], hits = replace_in(data[key], old, new)
    else:
        if field not in node:
            return 0, 0
        node[field], hits = replace_in(node[field], old, new)
    extra = 0
    if hits and len(old) >= PROPAGATE_MIN:
        for top in ("description", "label"):
            if top != field:
                node[top], n = replace_in(node.get(top), old, new)
                extra += n
        for key in list(data):
            if field != f"metadata.{key}" and key != STAMP:
                data[key], n = replace_in(data[key], old, new)
                extra += n
    if hits:
        set_meta(node, data)
    return hits, extra


def stamp(node: dict, entry: dict) -> None:
    data = meta(node)
    data.setdefault(STAMP, []).append(entry)
    set_meta(node, data)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    apply = args.apply and not args.dry_run

    store = Store()
    nodes = store.nodes
    counts: collections.Counter = collections.Counter()
    skipped, log = [], []
    for line in DECISIONS.read_text().splitlines():
        d = json.loads(line)
        op = d.get("apply")
        if not op:
            continue
        if op == "text":
            node = nodes.get(d["id"])
            if node is None:
                skipped.append((d["fid"], "node absent"))
                continue
            hits, extra = apply_text(node, d["field"], d["claim"], d["replacement"])
            if not hits:
                skipped.append((d["fid"], "claim absent (already applied?)"))
                continue
            stamp(node, {"finding": d["fid"], "field": d["field"], "before": d["claim"],
                         "after": d["replacement"], "propagated": extra})
            counts["text"] += 1
            counts["text_propagated"] += extra
            log.append((d["fid"], d["id"], d["field"], hits, extra))
        elif op == "edge":
            src, rel, tgt = d["edge"]
            edge = next((e for e in store.edges
                         if (e["source"], e["relation"], e["target"]) == (src, rel, tgt)), None)
            if edge is None:
                skipped.append((d["fid"], "edge absent (already applied?)"))
                continue
            steps = [s.strip() for s in d["edge_op"].split(";") if s.strip()]
            new_s, new_r, new_t = src, rel, tgt
            for s in steps:
                if s == "reverse":
                    new_s, new_t = new_t, new_s
                elif s.startswith("relabel:"):
                    new_r = s.split(":", 1)[1]
            reason = f"independent audit 2026-09-26, {d['fid']}: {d['problem']}"
            exists = any((e["source"], e["relation"], e["target"]) == (new_s, new_r, new_t)
                         for e in store.edges)
            if "drop" in steps or exists:
                n = store.remove_edges(lambda e: e is edge, reason)
                counts["edge_dropped"] += n
                log.append((d["fid"], f"{src} -{rel}-> {tgt}", "drop" if "drop" in steps else "drop (target triple exists)", n, 0))
                continue
            m = edge.get("metadata") or {}
            m = json.loads(m) if isinstance(m, str) else dict(m)
            m[STAMP] = {"finding": d["fid"], "previous": [src, rel, tgt], "reason": d["problem"]}
            edge["metadata"] = json.dumps(m, ensure_ascii=False) if isinstance(edge.get("metadata"), str) else m
            edge["source"] = edge["source_id"] = new_s
            edge["target"] = edge["target_id"] = new_t
            edge["relation"] = new_r
            # an inverse twin on the old pair now contradicts the corrected edge
            inv = INVERSE.get(rel)
            if inv:
                store.remove_edges(lambda e: (e["source"], e["relation"], e["target"]) == (tgt, inv, src),
                                   reason + " (inverse twin of the corrected edge)")
            counts["edge_corrected"] += 1
            log.append((d["fid"], f"{src} -{rel}-> {tgt}", f"-> {new_s} -{new_r}-> {new_t}", 1, 0))

    summary = store.commit(SLUG, apply=apply)
    if apply and store.quarantine:
        # the shared library names quarantines after the 2026-09-24 campaign
        src = DATA / "audit" / f"2026-09-24_{SLUG}_quarantine.jsonl"
        dst = DATA / "audit" / f"2026-09-26_{SLUG}_quarantine.jsonl"
        if src.exists():
            shutil.move(src, dst)
    print(json.dumps({"mode": "apply" if apply else "dry_run", "counts": counts,
                      "skipped": skipped, "changes": summary}, ensure_ascii=False, indent=1))
    Path(DATA / "audit" / f"2026-09-26_{SLUG}_apply_log.json").write_text(
        json.dumps(log, ensure_ascii=False, indent=1) + "\n") if apply else None


if __name__ == "__main__":
    main()
