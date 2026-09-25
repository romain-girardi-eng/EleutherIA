#!/usr/bin/env python3
"""Apply the person-identity review of the C3 engages_with edges. Dry-run first.

    PYTHONPATH=. python3 scripts/apply_2026_09_24_c3_person_identity.py --dry-run
    PYTHONPATH=. python3 scripts/apply_2026_09_24_c3_person_identity.py --apply

engages_with is its own inverse: a removal also withdraws the reversed edge on
the same pair, and a retarget moves it too.
"""

from __future__ import annotations

import argparse
import collections
import csv
import json

from scripts.data_2026_09_24_c3_person_identity import DECISIONS, QUEUE
from scripts.verification_2026_09_24_lib import DATA, Store, write_decisions

SLUG = "c3_person_identity"
STAMP = "c3_person_identity_2026_09_24"
REL = "engages_with"


def edge_meta(edge: dict) -> dict:
    raw = edge.get("metadata") or {}
    return json.loads(raw) if isinstance(raw, str) else dict(raw)


def put_edge_meta(edge: dict, data: dict) -> None:
    edge["metadata"] = json.dumps(data, ensure_ascii=False) if isinstance(edge.get("metadata"), str) else data


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    apply = args.apply and not args.dry_run

    store = Store()
    nodes = store.nodes
    queue = [r for r in csv.DictReader((DATA / "quality/jev_2026_09_24" / QUEUE).open()) if r["relation"] == REL]
    jev = {r["edge_id"]: float(r["p_specific"]) for r in queue}
    decided = {d[0] for d in DECISIONS}
    decisions, skipped = [], []
    counts: collections.Counter = collections.Counter()

    for edge_id, src, tgt, verdict, note in DECISIONS:
        kind, _, new_target = verdict.partition(":")
        record = {"item_id": edge_id, "queue": QUEUE if edge_id in jev else f"{QUEUE} (same defect, outside the queue)",
                  "claim_checked": f"{nodes.get(src, {}).get('label')} engages with {nodes.get(tgt, {}).get('label')} ({tgt})",
                  "evidence": note, "source": "the edge's own note against the target node's identity",
                  "method": "read the extraction note and the description of the target person", "jev": {"question": "p_specific", "probability": jev.get(edge_id)}}
        edge = next((e for e in store.edges if e["edge_id"] == edge_id), None)
        if kind != "needs_romain" and (edge is None or (edge["source"], edge["relation"], edge["target"]) != (src, REL, tgt)):
            skipped.append((edge_id, "edge absent or changed"))
            continue
        twin = lambda e: e["relation"] == REL and e["source"] == tgt and e["target"] == src
        if kind == "remove":
            reason = f"C3 person-identity review 2026-09-24: {note}"
            n = store.remove_edges(lambda e: e["edge_id"] == edge_id or twin(e), reason)
            record.update(verdict="removed", change=f"{n} edge(s) withdrawn (with the reversed twin if any)")
        elif kind == "retarget":
            assert nodes.get(new_target, {}).get("type") in ("person", "scholar"), new_target
            if any(e["relation"] == REL and e["source"] == src and e["target"] == new_target for e in store.edges):
                reason = f"C3 person-identity review 2026-09-24: duplicate of an existing edge to {new_target}. {note}"
                n = store.remove_edges(lambda e: e["edge_id"] == edge_id or twin(e), reason)
                record.update(verdict="removed", change=f"the right edge to {new_target} already exists; {n} withdrawn")
            else:
                for e in store.edges:
                    if e["edge_id"] == edge_id or twin(e):
                        m = edge_meta(e)
                        m[STAMP] = {"previous_endpoint": tgt, "reason": note}
                        put_edge_meta(e, m)
                        if e["target"] == tgt:
                            e["target"] = e["target_id"] = new_target
                        else:
                            e["source"] = e["source_id"] = new_target
                record.update(verdict="corrected", change=f"endpoint {tgt} -> {new_target}")
        else:
            record.update(verdict="needs_romain", change="none")
        counts[record["verdict"]] += 1
        decisions.append(record)

    for r in queue:
        if r["edge_id"] in decided:
            continue
        decisions.append({"item_id": r["edge_id"], "queue": QUEUE,
                          "claim_checked": f"{r['source_name']} engages with {r['target_name']} ({r['target_id']})",
                          "verdict": "false_positive",
                          "evidence": "identity of the target consistent with the extraction note; the engagement itself keeps its needs_review flag",
                          "source": "the edge's own note against the target node's identity",
                          "method": "read the extraction note and the description of the target person",
                          "jev": {"question": "p_specific", "probability": float(r["p_specific"])}, "change": "none"})
        counts["false_positive"] += 1

    summary = store.commit(SLUG, apply=apply)
    if apply and not skipped:
        write_decisions(SLUG, decisions)
    print(json.dumps({"mode": "apply" if apply else "dry_run", "counts": counts, "skipped": skipped,
                      "changes": summary}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
