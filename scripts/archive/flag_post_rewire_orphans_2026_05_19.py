#!/usr/bin/env python3
"""Flag ``needs_evidence=true`` on argument nodes that became fully orphan
(zero incident edges) after the Phase B / post-dedupe rewire.

Context
-------
The 2026-05-18/19 independent audit found several scholarly_argument_* nodes
with zero incident edges that were NOT carrying ``metadata.needs_evidence:
true``, a transparency gap for the FAIR dataset publication.

After the post-dedupe rewire (FIX 1, ``rewire_post_dedupe_2026_05_19.py``)
some additional shell-twin arguments were stripped of their edges. We flag
them and any other argument with zero incident edges and no
``needs_evidence`` flag.

Scope
-----
- ``type == "argument"`` only (other typed nodes use a SHACL pipeline; this
  script is a focused, fallback fix for orphan args).
- An argument is "orphan" if ``incoming + outgoing == 0`` *and*
  ``metadata.needs_evidence`` is not ``true``.

Each flagged node receives::

    metadata.needs_evidence = true
    metadata.flagged_at = "2026-05-19"
    metadata.flagged_reason = "orphan node — no incident edges (post-rewire)"
    metadata.flagged_by = "p0_fixes_2026_05_19"

Idempotent — a second run is a no-op.
Snapshot of ``nodes.jsonl`` written to
``data/kg/snapshots/2026-05-19-pre-orphan-flag/`` before mutation.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
NODES_PATH = ROOT / "data" / "kg" / "nodes.jsonl"
EDGES_PATH = ROOT / "data" / "kg" / "edges.jsonl"
SNAPSHOT_DIR = ROOT / "data" / "kg" / "snapshots" / "2026-05-19-pre-orphan-flag"

FLAG_DATE = "2026-05-19"
FLAG_REASON = "orphan node — no incident edges (post-rewire)"
FLAG_BY = "p0_fixes_2026_05_19"
NOW = datetime.now(UTC).isoformat(sep=" ")


def parse_metadata(raw: Any) -> dict[str, Any]:
    if raw is None or raw == "":
        return {}
    if isinstance(raw, dict):
        return raw
    try:
        return json.loads(raw)
    except (TypeError, json.JSONDecodeError):
        return {}


def serialize_metadata(md: dict[str, Any], original: Any) -> Any:
    if isinstance(original, str) or original is None:
        return json.dumps(md, ensure_ascii=False)
    return md


def main(commit: bool = False) -> int:
    # Index edges
    incoming: dict[str, int] = defaultdict(int)
    outgoing: dict[str, int] = defaultdict(int)
    with EDGES_PATH.open(encoding="utf-8") as fh:
        for raw in fh:
            raw = raw.strip()
            if not raw:
                continue
            e = json.loads(raw)
            if e.get("source"):
                outgoing[e["source"]] += 1
            if e.get("target"):
                incoming[e["target"]] += 1

    lines = NODES_PATH.read_text(encoding="utf-8").splitlines()
    to_flag: list[tuple[int, dict, dict]] = []  # (idx, node, md)
    for i, ln in enumerate(lines):
        if not ln.strip():
            continue
        try:
            n = json.loads(ln)
        except json.JSONDecodeError:
            continue
        if n.get("type") != "argument":
            continue
        nid = n.get("id")
        if not nid:
            continue
        if incoming[nid] + outgoing[nid] > 0:
            continue
        md = parse_metadata(n.get("metadata"))
        if md.get("needs_evidence") is True:
            continue
        to_flag.append((i, n, md))

    print(f"orphan args without needs_evidence: {len(to_flag)}")
    for i, n, md in to_flag[:10]:
        print(f"  {n['id']:<70} | {n.get('label', '')[:60]}")

    if not commit:
        print("\n[DRY-RUN] use --commit to apply")
        return 0
    if not to_flag:
        print("\nOK: nothing to flag (idempotent).")
        return 0

    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(NODES_PATH, SNAPSHOT_DIR / NODES_PATH.name)
    print(f"snapshot: {SNAPSHOT_DIR / NODES_PATH.name}")

    for i, n, md in to_flag:
        original_md = n.get("metadata")
        md["needs_evidence"] = True
        md["flagged_at"] = FLAG_DATE
        md["flagged_reason"] = FLAG_REASON
        md["flagged_by"] = FLAG_BY
        n["metadata"] = serialize_metadata(md, original_md)
        n["updated_at"] = NOW
        lines[i] = json.dumps(n, ensure_ascii=False)

    NODES_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"written: {NODES_PATH} (flagged {len(to_flag)} nodes)")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--commit", action="store_true")
    args = ap.parse_args()
    sys.exit(main(commit=args.commit))
