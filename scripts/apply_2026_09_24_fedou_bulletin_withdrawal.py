#!/usr/bin/env python3
"""Withdraw the contaminated Fédou bulletin rows. Dry-run first.

    PYTHONPATH=. python3 scripts/apply_2026_09_24_fedou_bulletin_withdrawal.py --dry-run
    PYTHONPATH=. python3 scripts/apply_2026_09_24_fedou_bulletin_withdrawal.py --apply
"""

from __future__ import annotations

import argparse
import json

from scripts.data_2026_09_24_fedou_bulletin_withdrawal import (
    ABSTRACT_MARKERS,
    ALLOWED_EDGE_TARGETS,
    REQUIRED_INTEGRITY_STATUS,
    WITHDRAW,
)
from scripts.verification_2026_09_24_lib import Store, meta, write_decisions

SLUG = "fedou_bulletin_withdrawal"
REASON = (
    "Fédou bulletin row: description/abstract describe Origen's De oratione "
    "(Vigne) while the title names another book; edges derived from that abstract"
)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    store = Store()
    nodes = store.nodes
    decisions, skipped = [], []
    for nid in WITHDRAW:
        node = nodes.get(nid)
        if node is None:
            skipped.append((nid, "absent (already withdrawn?)"))
            continue
        data = meta(node)
        desc = node.get("description") or ""
        # Preconditions: the contamination we read is still exactly there.
        if data.get("integrity_status") != REQUIRED_INTEGRITY_STATUS:
            skipped.append((nid, "integrity_status changed"))
            continue
        if not any(m in desc for m in ABSTRACT_MARKERS):
            skipped.append((nid, "description no longer the De oratione abstract"))
            continue
        if any(m in (node.get("label") or "") for m in ABSTRACT_MARKERS):
            skipped.append((nid, "title itself is about De oratione"))
            continue
        touching = [e for e in store.edges if nid in (e["source"], e["target"])]
        if any(
            e["relation"] != "discusses" or e["source"] != nid or e["target"] not in ALLOWED_EDGE_TARGETS
            for e in touching
        ):
            skipped.append((nid, "carries an edge not derived from the abstract"))
            continue
        removed_edges = store.remove_edges(lambda e, nid=nid: nid in (e["source"], e["target"]), REASON)
        store.remove_citations(lambda c, nid=nid: c["kg_node_id"] == nid, REASON)
        store.remove_node(nid, REASON)
        decisions.append(
            {
                "item_id": nid,
                "queue": "c2_translations_descriptions/queue_b_identity_mismatch.csv (+ cold audit H-01)",
                "claim_checked": "The publication node describes the book named in its title.",
                "verdict": "removed",
                "evidence": {
                    "title": node.get("label"),
                    "description_head": desc[:160],
                },
                "source": "the node itself (title vs abstract); data/audit/2026-08-17_cold_audit_sol.md H-01",
                "method": "read label, metadata.title, description, metadata.abstract and both edges",
                "jev": "c2 B about_entity ≤ 0.3 on the rows scored",
                "change": f"node removed with {removed_edges} discusses edges (records in quarantine file)",
            }
        )
    summary = store.commit(SLUG, apply=args.apply and not args.dry_run)
    if args.apply and not args.dry_run:
        write_decisions(SLUG, decisions)
    print(json.dumps({"mode": "apply" if args.apply and not args.dry_run else "dry_run",
                      "withdrawn": len(decisions), "skipped": skipped, "changes": summary},
                     ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
