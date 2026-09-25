#!/usr/bin/env python3
"""Apply the review of the C1 contradiction queue. Dry-run first.

    PYTHONPATH=. python3 scripts/apply_2026_09_24_c1_contradictions.py --dry-run
    PYTHONPATH=. python3 scripts/apply_2026_09_24_c1_contradictions.py --apply

A removal withdraws every passage -> concept edge of the pair (with its
ontology-inverse twin) and the corpus citations that mirror it.
"""

from __future__ import annotations

import argparse
import collections
import json

from scripts.apply_2026_09_24_c4_duplicate_merges import INVERSE
from scripts.data_2026_09_24_c1_contradictions import DECISIONS
from scripts.verification_2026_09_24_lib import Store, write_decisions

SLUG = "c1_contradictions"
QUEUE = "c1_passage_concepts/queue_contradictions.csv"
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
    decisions = []
    counts: collections.Counter = collections.Counter()
    for passage, concept, p, verdict, note in DECISIONS:
        record = {"item_id": f"{passage} -> {concept}", "queue": QUEUE,
                  "claim_checked": f"{passage} discusses {concept}", "verdict": VERDICT[verdict],
                  "evidence": note, "source": "text of the passage (for Alexander, the complete chapter in the First1KGreek TEI)",
                  "method": "stem search in the chapter, read against the edge rationale", "jev": {"question": "discusses", "probability": p},
                  "change": "none"}
        if verdict == "remove":
            pair = [e for e in store.edges if e["source"] == passage and e["target"] == concept]
            if not pair:
                record["change"] = "no edge left on the pair (already withdrawn, e.g. by the c3_discusses_edges batch)"
            else:
                rels = {e["relation"] for e in pair}
                invs = {INVERSE.get(r) for r in rels}
                reason = f"C1 contradiction review 2026-09-24: {note}"
                n_e = store.remove_edges(lambda e: (e["source"], e["target"]) == (passage, concept) or (
                    (e["source"], e["target"]) == (concept, passage) and e["relation"] in invs), reason)
                rows = snapshot_rows.get(passage, set())
                n_c = store.remove_citations(lambda c: c["kg_node_id"] == concept and c["citation_type"] in rels
                                             and c["passage_id"] in rows, reason)
                record["change"] = f"{n_e} edge(s) ({', '.join(sorted(rels))}) and {n_c} mirrored corpus citation(s) withdrawn"
        counts[verdict] += 1
        decisions.append(record)

    summary = store.commit(SLUG, apply=apply)
    if apply and summary["edges"]["removed"]:
        write_decisions(SLUG, decisions)
    print(json.dumps({"mode": "apply" if apply else "dry_run", "counts": counts, "changes": summary},
                     ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
