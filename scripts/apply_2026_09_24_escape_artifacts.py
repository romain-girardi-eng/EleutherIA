#!/usr/bin/env python3
"""Turn literal import escapes back into line breaks. Dry-run first.

    PYTHONPATH=. python3 scripts/apply_2026_09_24_escape_artifacts.py --dry-run
    PYTHONPATH=. python3 scripts/apply_2026_09_24_escape_artifacts.py --apply
"""

from __future__ import annotations

import argparse
import json

from scripts.data_2026_09_24_escape_artifacts import FIX, NEEDS_ROMAIN
from scripts.verification_2026_09_24_lib import Store, meta, set_meta, write_decisions

SLUG = "escape_artifacts"
NOW = "2026-09-24 00:00:00+00:00"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    apply = args.apply and not args.dry_run
    store = Store()
    nodes = store.nodes
    decisions, skipped = [], []
    for nid, seqs in FIX.items():
        n = nodes[nid]
        d = n["description"]
        if not any(s in d for s in seqs):
            skipped.append(nid)
            continue
        n_rep = sum(d.count(s) for s in seqs)
        for s in seqs:
            d = d.replace(s, "\n")
        m = meta(n)
        m["description_before_2026_09_24"] = n["description"]
        n["description"] = d
        set_meta(n, m)
        n["updated_at"] = NOW
        decisions.append({"item_id": nid, "queue": "pending list of the verification prompt (pub_arfe &#13;)",
                          "claim_checked": "The public description has no import escapes.", "verdict": "corrected",
                          "evidence": f"{n_rep} literal escape sequence(s): {seqs}", "source": "the description itself",
                          "method": "exact string replacement", "jev": None, "change": "escape sequences replaced by line breaks; old text in metadata"})
    for nid, note in NEEDS_ROMAIN.items():
        decisions.append({"item_id": nid, "queue": "same scan", "claim_checked": "The Greek quotation is in Greek script.",
                          "verdict": "needs_romain", "evidence": note, "source": "the passage text", "method": "read", "jev": None, "change": "none"})
    summary = store.commit(SLUG, apply=apply)
    if apply and not skipped:
        write_decisions(SLUG, decisions)
    print(json.dumps({"mode": "apply" if apply else "dry_run", "skipped": skipped, "changes": summary}, indent=1))


if __name__ == "__main__":
    main()
