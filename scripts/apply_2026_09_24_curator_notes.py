#!/usr/bin/env python3
"""Move curator notes out of public descriptions. Dry-run first.

    PYTHONPATH=. python3 scripts/apply_2026_09_24_curator_notes.py --dry-run
    PYTHONPATH=. python3 scripts/apply_2026_09_24_curator_notes.py --apply

Nothing is deleted: every note removed from a description is kept verbatim
in metadata.curator_note_2026_09_24.
"""

from __future__ import annotations

import argparse
import ast
import collections
import csv
import json

from scripts.data_2026_09_24_curator_notes import (
    QUEUE, SPECIALTY_AS_DESCRIPTION, STANCE_AS_DESCRIPTION, TRAILING_LOCAL_PATH, UNSUPPORTED)
from scripts.verification_2026_09_24_lib import DATA, Store, meta, set_meta, write_decisions

SLUG = "curator_notes"
STAMP = "curator_note_2026_09_24"
NOW = "2026-09-24 00:00:00+00:00"


def audit_verdict(m: dict) -> str | None:
    raw = m.get("scholarly_audit")
    if isinstance(raw, str):
        try:
            raw = ast.literal_eval(raw)
        except (ValueError, SyntaxError):
            return None
    return raw.get("verdict") if isinstance(raw, dict) else None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    apply = args.apply and not args.dry_run

    store = Store()
    nodes = store.nodes
    queue = {r["node_id"]: float(r["p_curator_notes"]) for r in csv.DictReader((DATA / "quality/jev_2026_09_24" / QUEUE).open())}
    decisions, skipped = [], []
    counts: collections.Counter = collections.Counter()

    def record(nid, verdict, evidence, change):
        decisions.append({"item_id": nid, "queue": QUEUE if nid in queue else f"{QUEUE} (same defect, outside the queue)",
                          "claim_checked": "The public description is content, not a curator note.",
                          "verdict": verdict, "evidence": evidence, "source": "the node's own description and metadata",
                          "method": "read the description; located the content it should carry in the node's metadata",
                          "jev": {"question": "curator_notes", "probability": queue.get(nid)}, "change": change})
        counts[verdict] += 1

    for nid in STANCE_AS_DESCRIPTION:
        n = nodes.get(nid)
        m = meta(n) if n else {}
        if not n or m.get(STAMP) is not None or not (m.get("stance") or "").strip():
            skipped.append(nid)
            continue
        m[STAMP] = n["description"]
        change = "description (a verification note) moved to metadata; description := metadata.stance"
        verdict = audit_verdict(m)
        if verdict in UNSUPPORTED:
            m["citability_before_2026_09_24"] = m.get("citability")
            m["citability"] = "discoverable_only"
            change += f"; citability discoverable_only (scholarly_audit verdict {verdict})"
        n["description"] = m["stance"].strip()
        set_meta(n, m)
        n["updated_at"] = NOW
        record(nid, "corrected", f"description was a note; audit verdict {verdict}", change)

    for nid in SPECIALTY_AS_DESCRIPTION:
        n = nodes.get(nid)
        m = meta(n) if n else {}
        spec = (m.get("specialty") or "").strip()
        if not n or m.get(STAMP) is not None or not spec or not n["description"].startswith(spec) or n["description"] == spec:
            skipped.append(nid)
            continue
        m[STAMP] = n["description"]
        n["description"] = spec
        set_meta(n, m)
        n["updated_at"] = NOW
        record(nid, "corrected", "description ends in a fragment of an editing instruction", "description := metadata.specialty (its intact prefix)")

    for nid, marker in TRAILING_LOCAL_PATH.items():
        n = nodes.get(nid)
        m = meta(n) if n else {}
        d = n["description"] if n else ""
        i = d.rfind(marker)
        if not n or m.get(STAMP) is not None or i < 0:
            skipped.append(nid)
            continue
        m[STAMP] = d[i:].strip()
        n["description"] = d[:i].rstrip()
        set_meta(n, m)
        n["updated_at"] = NOW
        record(nid, "corrected", "private file path at the end of the public description", "trailing acquisition note with local path moved to metadata")

    done = set(STANCE_AS_DESCRIPTION) | set(SPECIALTY_AS_DESCRIPTION) | set(TRAILING_LOCAL_PATH)
    for nid in queue:
        if nid not in done:
            record(nid, "needs_romain", "curator remarks woven into the scholarly prose; separating them means rewriting the text",
                   "none")

    summary = store.commit(SLUG, apply=apply)
    if apply and not skipped:
        write_decisions(SLUG, decisions)
    print(json.dumps({"mode": "apply" if apply else "dry_run", "counts": counts, "skipped": skipped,
                      "changes": summary}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
