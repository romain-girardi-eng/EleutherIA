#!/usr/bin/env python3
"""Apply the review of the C3 likely-wrong discusses edges. Dry-run first.

    PYTHONPATH=. python3 scripts/apply_2026_09_24_c3_discusses_edges.py --dry-run
    PYTHONPATH=. python3 scripts/apply_2026_09_24_c3_discusses_edges.py --apply

A removal withdraws the edge, its discussed_in twin on the same pair, and the
corpus citation that mirrors a passage -> concept edge (the concept citing the
passage's snapshot row with citation_type "discusses").
"""

from __future__ import annotations

import argparse
import collections
import json

from scripts.apply_2026_09_24_c4_duplicate_merges import INVERSE
from scripts.data_2026_09_24_c3_discusses_edges import DECISIONS
from scripts.verification_2026_09_24_lib import Store, write_decisions

SLUG = "c3_discusses_edges"
QUEUE = "c3_edges_links/queue_A_likely_wrong.csv"
REL = "discusses"
VERDICT = {"remove": "removed", "false_positive": "false_positive", "needs_romain": "needs_romain"}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    apply = args.apply and not args.dry_run

    store = Store()
    snapshot_rows = collections.defaultdict(set)
    for c in store.rows["citations"]:
        if c["citation_type"] == "snapshot_passage_node":
            snapshot_rows[c["kg_node_id"]].add(c["passage_id"])
    edge_ids = {e["edge_id"] for e in store.edges}

    decisions, skipped = [], []
    counts: collections.Counter = collections.Counter()
    for edge_id, src, tgt, p, verdict, note in DECISIONS:
        record = {"item_id": edge_id, "queue": QUEUE, "claim_checked": f"{src} -{REL}-> {tgt}",
                  "verdict": VERDICT[verdict], "evidence": note,
                  "source": "text of both nodes and provenance of the edge",
                  "method": "read the source node (text or summary) against the target; checked the edge's generator",
                  "jev": {"question": "p_specific", "probability": p}, "change": "none"}
        if verdict == "remove":
            if edge_id not in edge_ids:
                skipped.append((edge_id, "edge absent"))
                continue
            reason = f"C3 discusses review 2026-09-24: {note}"
            n_e = store.remove_edges(lambda e: e["edge_id"] == edge_id or (
                e["source"] == tgt and e["target"] == src and e["relation"] == INVERSE.get(REL)), reason)
            rows = snapshot_rows.get(src, set())
            n_c = store.remove_citations(lambda c: c["kg_node_id"] == tgt and c["citation_type"] == REL
                                         and c["passage_id"] in rows, reason)
            record["change"] = f"{n_e} edge(s) and {n_c} mirrored corpus citation(s) withdrawn"
        counts[verdict] += 1
        decisions.append(record)

    summary = store.commit(SLUG, apply=apply)
    if apply and not skipped:
        write_decisions(SLUG, decisions)
    print(json.dumps({"mode": "apply" if apply else "dry_run", "counts": counts, "n_skipped": len(skipped),
                      "changes": summary}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
