#!/usr/bin/env python3
"""Relabel English editorial passages declared as Greek/Latin. Dry-run first.

    PYTHONPATH=. python3 scripts/apply_2026_09_24_editorial_passage_language.py --dry-run
    PYTHONPATH=. python3 scripts/apply_2026_09_24_editorial_passage_language.py --apply
"""

from __future__ import annotations

import argparse
import json

from scripts.data_2026_09_24_editorial_passage_language import PASSAGES
from scripts.verification_2026_09_24_lib import Store, meta, set_meta, write_decisions

SLUG = "editorial_passage_language"
STAMP = "editorial_passage_language_2026_09_24"
NOW = "2026-09-24 00:00:00+00:00"
EDITORIAL_ROLES = {"editorial_synthesis", "summary"}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    store = Store()
    nodes = store.nodes
    decisions, skipped = [], []
    for nid, old in PASSAGES.items():
        node = nodes.get(nid)
        if node is None:
            skipped.append((nid, "absent"))
            continue
        data = meta(node)
        if data.get(STAMP):
            continue
        if data.get("language") != old or data.get("passage_role") not in EDITORIAL_ROLES:
            skipped.append((nid, "precondition failed (language or role changed)"))
            continue
        data["language_before_2026_09_24"] = old
        data["quoted_language"] = old
        data["language"] = "eng"
        data[STAMP] = True
        set_meta(node, data)
        node["updated_at"] = NOW
        decisions.append({
            "item_id": nid,
            "queue": "c1_passage_concepts/queue_quality_flags.csv + queue_language_mismatch.csv (pattern extended)",
            "claim_checked": f"The passage text is in the declared language ({old}).",
            "verdict": "corrected",
            "evidence": (node.get("description") or "")[:200],
            "source": "the node's own text and its own passage_role (" + data.get("passage_role", "") + ")",
            "method": "read the node: English editorial prose quoting short phrases in " + old,
            "jev": "c1 'mostly modern-language text' / language mismatch on the EN III syntheses",
            "change": f"metadata.language {old} -> eng (quoted_language = {old})",
        })
    summary = store.commit(SLUG, apply=args.apply and not args.dry_run)
    if args.apply and not args.dry_run:
        write_decisions(SLUG, decisions)
    print(json.dumps({"relabelled": len(decisions), "skipped": skipped, "changes": summary["nodes"]}, indent=1))


if __name__ == "__main__":
    main()
