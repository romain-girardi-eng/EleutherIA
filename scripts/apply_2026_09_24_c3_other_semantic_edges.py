#!/usr/bin/env python3
"""Apply the review of the remaining C3 semantic edges. Dry-run first.

    PYTHONPATH=. python3 scripts/apply_2026_09_24_c3_other_semantic_edges.py --dry-run
    PYTHONPATH=. python3 scripts/apply_2026_09_24_c3_other_semantic_edges.py --apply

A removal withdraws the edge and its ontology-inverse twin on the same pair.
"""

from __future__ import annotations

import argparse
import collections
import json

from scripts.apply_2026_09_24_c4_duplicate_merges import INVERSE
from scripts.data_2026_09_24_c3_other_semantic_edges import DECISIONS
from scripts.verification_2026_09_24_lib import Store, write_decisions

SLUG = "c3_other_semantic_edges"
QUEUE = "c3_edges_links/queue_A_likely_wrong.csv"
VERDICT = {"remove": "removed", "false_positive": "false_positive", "needs_romain": "needs_romain"}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    apply = args.apply and not args.dry_run

    store = Store()
    edge_ids = {e["edge_id"] for e in store.edges}
    decisions, skipped = [], []
    counts: collections.Counter = collections.Counter()
    for edge_id, src, rel, tgt, p, verdict, note in DECISIONS:
        record = {"item_id": edge_id, "queue": QUEUE, "claim_checked": f"{src} -{rel}-> {tgt}",
                  "verdict": VERDICT[verdict], "evidence": note,
                  "source": "descriptions of both nodes and provenance of the edge",
                  "method": "read both nodes and the edge metadata", "jev": {"question": "p_specific", "probability": p},
                  "change": "none"}
        if verdict == "remove":
            if edge_id not in edge_ids:
                skipped.append(edge_id)
                continue
            inv = INVERSE.get(rel)
            n = store.remove_edges(lambda e: e["edge_id"] == edge_id or (
                e["source"] == tgt and e["target"] == src and e["relation"] == inv),
                f"C3 semantic-edge review 2026-09-24: {note}")
            record["change"] = f"{n} edge(s) withdrawn"
        counts[verdict] += 1
        decisions.append(record)

    summary = store.commit(SLUG, apply=apply)
    if apply and not skipped:
        write_decisions(SLUG, decisions)
    print(json.dumps({"mode": "apply" if apply else "dry_run", "counts": counts, "n_skipped": len(skipped),
                      "changes": summary}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
