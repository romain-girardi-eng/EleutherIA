#!/usr/bin/env python3
"""Generate integrity_status flagging SQL from the review queue (NEVER auto-run).

Reads data/audit/review_queue.jsonl, keeps entries in the greek-fabrication
categories (greek_fabrication, greek_unverified), and emits one UPDATE per
node setting metadata.integrity_status:

- 'fabrication_confirmed_pending_fix' — entry adjudicated 'accepted', or the
  source audit already recorded verdict='confirmed' (fabrication confirmed,
  corrective fix still pending)
- 'greek_unverified' — entry still pending adjudication with no confirmed verdict

Entries adjudicated 'rejected' or 'fixed' are skipped (nothing to flag). When
a node appears in several queue entries, the confirmed status wins.

Each UPDATE sits on its own line with a comment carrying the queue id(s) and
source location, so each statement can be reviewed and executed selectively.
This script only WRITES SQL text; it never touches a database.

Usage:
    python3 scripts/audit_queue/generate_flag_sql.py                  # stdout
    python3 scripts/audit_queue/generate_flag_sql.py --output flag.sql
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from scripts.audit_queue.build_queue import (
    DEFAULT_OUTPUT as DEFAULT_QUEUE_PATH,
)
from scripts.audit_queue.build_queue import (
    GREEK_CATEGORIES,
    read_jsonl,
)

CONFIRMED_STATUS = "fabrication_confirmed_pending_fix"
UNVERIFIED_STATUS = "greek_unverified"


def entry_integrity_status(entry: dict[str, Any]) -> str | None:
    """Map a queue entry to an integrity_status value, or None to skip."""
    if entry.get("category") not in GREEK_CATEGORIES:
        return None
    resolution = entry.get("resolution")
    if resolution == "accepted":
        return CONFIRMED_STATUS
    if resolution in ("rejected", "fixed"):
        return None
    if entry.get("evidence", {}).get("verdict") == "confirmed":
        return CONFIRMED_STATUS
    return UNVERIFIED_STATUS


def generate_sql(queue_entries: list[dict[str, Any]]) -> str:
    # node_id -> (status, [queue refs]); confirmed wins over unverified.
    flags: dict[str, tuple[str, list[str]]] = {}
    for entry in queue_entries:
        status = entry_integrity_status(entry)
        node_id = entry.get("node_id")
        if status is None or not node_id:
            continue
        ref = f"queue_id={entry['id']} source={entry['source_file']}:{entry['source_line']}"
        prior = flags.get(node_id)
        if prior is None:
            flags[node_id] = (status, [ref])
        else:
            prior_status, refs = prior
            refs.append(ref)
            if status == CONFIRMED_STATUS and prior_status != CONFIRMED_STATUS:
                flags[node_id] = (CONFIRMED_STATUS, refs)

    lines = [
        "-- integrity_status flags generated from data/audit/review_queue.jsonl",
        "-- by scripts/audit_queue/generate_flag_sql.py",
        "-- REVIEW EACH LINE; execute statements selectively, one at a time.",
        "-- Never run this file blindly — no bulk apply.",
        "",
    ]
    for node_id in sorted(flags):
        status, refs = flags[node_id]
        node = node_id.replace("'", "''")
        lines.append(
            "UPDATE free_will.kg_nodes "
            "SET metadata = jsonb_set(COALESCE(metadata, '{}'::jsonb), "
            f"'{{integrity_status}}', '\"{status}\"'), updated_at = now() "
            f"WHERE node_id = '{node}'; -- {'; '.join(refs)}"
        )
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--queue", type=Path, default=DEFAULT_QUEUE_PATH)
    parser.add_argument(
        "--output", type=Path, default=None, help="Write SQL here (default: stdout)"
    )
    args = parser.parse_args(argv)

    if not args.queue.exists():
        print(
            f"queue not found: {args.queue} — run build_queue.py first", file=sys.stderr
        )
        return 1

    sql = generate_sql(read_jsonl(args.queue))
    if args.output is None:
        sys.stdout.write(sql)
    else:
        args.output.write_text(sql, encoding="utf-8")
        n = sum(1 for line in sql.splitlines() if line.startswith("UPDATE "))
        print(
            f"wrote {n} UPDATE statements to {args.output} (review before running any)"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
