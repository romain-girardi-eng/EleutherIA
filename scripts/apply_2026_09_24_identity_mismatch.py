#!/usr/bin/env python3
"""Apply the review of the C2 identity-mismatch queue. Dry-run first.

    PYTHONPATH=. python3 scripts/apply_2026_09_24_identity_mismatch.py --dry-run
    PYTHONPATH=. python3 scripts/apply_2026_09_24_identity_mismatch.py --apply

A wrong abstract is moved to metadata.abstract_rejected_2026_09_24 and the
description is rebuilt from the record's own verified bibliographic fields
(author, title, reference, year, DOI) only.
"""

from __future__ import annotations

import argparse
import collections
import csv
import json

from scripts.data_2026_09_24_identity_mismatch import KEPT, QUEUE, WRONG_ABSTRACT
from scripts.verification_2026_09_24_lib import DATA, Store, meta, set_meta, write_decisions

SLUG = "identity_mismatch"
NOW = "2026-09-24 00:00:00+00:00"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    apply = args.apply and not args.dry_run

    store = Store()
    nodes = store.nodes
    rows = list(csv.DictReader((DATA / "quality/jev_2026_09_24" / QUEUE).open()))
    decisions, skipped = [], []
    counts: collections.Counter = collections.Counter()
    for r in rows:
        nid = r["node_id"]
        rec = {"item_id": nid, "queue": QUEUE, "claim_checked": "The description is about this entity.",
               "source": "the node's description and bibliographic metadata", "method": "read the description against the record",
               "jev": {"question": "about_entity", "probability": float(r["p_about_entity"])}}
        n = nodes.get(nid)
        if n is None:
            rec.update(verdict="removed", evidence="Fédou 2026 bulletin row", change="already withdrawn by the fedou_bulletin_withdrawal batch")
        elif nid in WRONG_ABSTRACT:
            m = meta(n)
            words = WRONG_ABSTRACT[nid]
            if "abstract_rejected_2026_09_24" in m or not all(w in (n.get("description") or "") for w in words):
                skipped.append(nid)
                continue
            parts = [m["author"], f"'{m['title']}'", m["reference"], str(m["year"])]
            new = ", ".join(parts) + f". DOI {m['doi']}."
            m["abstract_rejected_2026_09_24"] = {"text": m.get("abstract"), "reason": "publisher blurb for a constitutional-law commentary, not this article's abstract"}
            m.pop("abstract", None)
            m["description_before_2026_09_24"] = n["description"]
            n["description"] = new
            set_meta(n, m)
            n["updated_at"] = NOW
            rec.update(verdict="corrected", evidence=f"the description quotes a review of a 'Verfassungskommentar' (Grundgesetz); the record is a Jewish Studies Quarterly article on Origen ({m['doi']})",
                       change="abstract moved to metadata.abstract_rejected_2026_09_24; description rebuilt from author, title, reference, year and DOI")
        elif nid in KEPT:
            rec.update(verdict="false_positive", evidence=KEPT[nid], change="none")
        else:
            skipped.append(nid)
            continue
        counts[rec["verdict"]] += 1
        decisions.append(rec)

    summary = store.commit(SLUG, apply=apply)
    if apply and not skipped:
        write_decisions(SLUG, decisions)
    print(json.dumps({"mode": "apply" if apply else "dry_run", "counts": counts, "skipped": skipped,
                      "changes": summary}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
