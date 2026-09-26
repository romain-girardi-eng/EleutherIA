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
* ``list_remove`` / ``list_remove_prefix`` — drop the list element of
  ``metadata.<key>`` equal to (or starting with) ``element``.
* ``meta_delete`` — delete ``metadata.<key>`` (an unattested value).

Every touched node gets ``metadata.independent_audit_2026_09_26``: the list of
(finding id, field) it received. The wrong text itself is not copied into the
node (it would be served again); it is kept in the decisions file, and the
replaced/dropped records are in the apply log and the quarantine.
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
# Live text fields only: history (``*_pre_*``, ``previous_*``), audit records,
# notes and identifiers keep what they recorded at the time.
PROPAGATE_KEYS = ("description_en", "description_fr", "stance", "verified_reference")


def bounded_replace(text: str, old: str, new: str) -> tuple[str, int]:
    """Replace ``old`` only where it does not start or end inside a word."""
    out, i, n = [], 0, 0
    while True:
        j = text.find(old, i)
        if j < 0:
            out.append(text[i:])
            return "".join(out), n
        before = text[j - 1] if j else " "
        after = text[j + len(old)] if j + len(old) < len(text) else " "
        ok = not (old[0].isalnum() and before.isalnum()) and not (old[-1].isalnum() and after.isalnum())
        out.append(text[i:j] + (new if ok else old))
        n += ok
        i = j + len(old)


def replace_in(value, old: str, new: str, bounded: bool = False):
    """Replace ``old`` in every string of a JSON-like value; return (value, count)."""
    if isinstance(value, bool):
        return value, 0
    if isinstance(value, (int, float)) and str(value) == old:
        return (int(new) if new.isdigit() else new), 1
    if isinstance(value, str) and bounded:
        return bounded_replace(value, old, new)
    if isinstance(value, str):
        n = value.count(old)
        return (value.replace(old, new), n) if n else (value, 0)
    if isinstance(value, list):
        out, total = [], 0
        for v in value:
            v2, n = replace_in(v, old, new, bounded)
            out.append(v2)
            total += n
        return out, total
    if isinstance(value, dict):
        out, total = {}, 0
        for k, v in value.items():
            v2, n = replace_in(v, old, new, bounded)
            out[k] = v2
            total += n
        return out, total
    return value, 0


def apply_text(node: dict, field: str, old: str, new: str) -> tuple[int, int]:
    """Return (hits in the named field, hits propagated elsewhere in the node)."""
    data = meta(node)
    current = data.get(field.split(".", 1)[1]) if field.startswith("metadata.") else node.get(field)
    if old in new and new and new in json.dumps(current, ensure_ascii=False).replace('\\"', '"'):
        return 0, 0  # already applied; the replacement contains the claim
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
                node[top], n = replace_in(node.get(top), old, new, bounded=True)
                extra += n
        for key in PROPAGATE_KEYS:
            if field != f"metadata.{key}" and key in data:
                data[key], n = replace_in(data[key], old, new, bounded=True)
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
            stamp(node, {"finding": d["fid"], "field": d["field"], "propagated": extra})
            counts["text"] += 1
            counts["text_propagated"] += extra
            log.append((d["fid"], d["id"], d["field"], hits, extra, d["claim"], d["replacement"]))
        elif op in ("list_remove", "list_remove_prefix", "meta_delete"):
            node = nodes.get(d["id"])
            key = d["field"].split(".", 1)[1]
            data = meta(node) if node else {}
            if key not in data:
                skipped.append((d["fid"], "field absent (already applied?)"))
                continue
            before = data[key]
            if op == "meta_delete":
                del data[key]
            else:
                if not isinstance(before, list):
                    skipped.append((d["fid"], "field is not a list"))
                    continue
                hit = (lambda x: x == d["element"]) if op == "list_remove" else (
                    lambda x: isinstance(x, str) and x.startswith(d["element"]))
                data[key] = [x for x in before if not hit(x)]
                if len(data[key]) == len(before):
                    skipped.append((d["fid"], "element absent (already applied?)"))
                    continue
            set_meta(node, data)
            stamp(node, {"finding": d["fid"], "field": d["field"], "operation": op})
            counts[op] += 1
            log.append((d["fid"], d["id"], d["field"], 1, 0))
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
            m[STAMP] = {"finding": d["fid"], "previous": [src, rel, tgt]}
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
