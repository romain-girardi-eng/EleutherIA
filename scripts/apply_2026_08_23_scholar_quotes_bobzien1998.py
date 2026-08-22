#!/usr/bin/env python3
"""Apply the Bobzien 1998 scholar-quote wave to data/kg/nodes.jsonl.

Dry-run is the default; ``--write`` is required to modify the file. Unchanged
lines are written back byte-for-byte; only the edited nodes are re-serialized.

Per-edit preconditions (skip + log, never apply blindly):
  - the node exists, is unique, and has ``type == "argument"``;
  - its description contains the declared ``precondition_description``;
  - ``metadata.quote_verbatim`` is absent, or already equal (idempotent no-op).

Invariants asserted before writing: node count unchanged, no duplicate ids,
every edited row still parses, and every edit is stamped
``metadata.scholar_quotes_2026_08_23`` so a re-run is a no-op.

Writes a report to data/audit/2026-08-23_scholar_quotes_bobzien1998_applied.md.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from data_2026_08_23_scholar_quotes_bobzien1998 import (  # noqa: E402
    EDITS,
    SOURCE,
    WAVE_STAMP,
)

NODES = ROOT / "data" / "kg" / "nodes.jsonl"
BACKUP = NODES.with_name("nodes.jsonl.bak-scholar-quotes-bobzien1998")
REPORT = ROOT / "data" / "audit" / "2026-08-23_scholar_quotes_bobzien1998_applied.md"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="apply (default: dry-run)")
    args = parser.parse_args()

    raw_lines = NODES.read_text(encoding="utf-8").splitlines(keepends=True)
    nodes = [json.loads(line) for line in raw_lines]
    ids = Counter(n.get("id") for n in nodes)
    index = {n.get("id"): i for i, n in enumerate(nodes)}

    applied, skipped, noop = [], [], []
    for edit in EDITS:
        nid = edit["node_id"]
        if ids[nid] != 1:
            skipped.append((nid, f"node count is {ids[nid]}, expected exactly 1"))
            continue
        node = nodes[index[nid]]
        if node.get("type") != "argument":
            skipped.append((nid, f"type is {node.get('type')!r}, not 'argument'"))
            continue
        if edit["precondition_description"] not in (node.get("description") or ""):
            skipped.append((nid, "description precondition no longer holds"))
            continue
        md = node.get("metadata")
        if isinstance(md, str):
            try:
                md = json.loads(md)
            except json.JSONDecodeError:
                skipped.append((nid, "metadata is an unparseable string"))
                continue
        if not isinstance(md, dict):
            md = {}
        existing = md.get("quote_verbatim")
        if isinstance(existing, str) and existing.strip():
            if existing.strip() == edit["quote_verbatim"]:
                noop.append(nid)
            else:
                skipped.append((nid, "a DIFFERENT quote_verbatim already present"))
            continue
        md["quote_verbatim"] = edit["quote_verbatim"]
        md["quote_page"] = edit["quote_page"]
        md["quote_source"] = SOURCE
        md[WAVE_STAMP] = True
        node["metadata"] = md
        applied.append((nid, edit["quote_page"]))

    # Invariants before writing.
    assert len(nodes) == len(raw_lines), "node count changed"
    assert max(ids.values() or [1]) == 1 or all(
        ids[e["node_id"]] == 1 for e in EDITS
    ), "duplicate node ids among targets"

    touched = {nid for nid, _ in applied}
    out_lines = []
    for line, node in zip(raw_lines, nodes):
        if node.get("id") in touched:
            rendered = json.dumps(node, ensure_ascii=False)
            json.loads(rendered)  # every edited row still parses
            out_lines.append(rendered + ("\n" if line.endswith("\n") else ""))
        else:
            out_lines.append(line)  # unchanged rows byte-for-byte

    mode = "WRITE" if args.write else "DRY-RUN"
    print(f"[{mode}] applied={len(applied)} noop={len(noop)} skipped={len(skipped)}")
    for nid, page in applied:
        print(f"  + {nid} ({page})")
    for nid in noop:
        print(f"  = {nid} (already stamped, no-op)")
    for nid, why in skipped:
        print(f"  ! SKIP {nid}: {why}")

    if not args.write:
        return 0
    if not applied:
        print("nothing to write")
        return 0

    shutil.copy2(NODES, BACKUP)
    NODES.write_text("".join(out_lines), encoding="utf-8")

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Scholar-quote wave 1 — Bobzien 1998 (applied 2026-08-23)",
        "",
        f"Source: {SOURCE}.",
        "Quotes verified against the curated extraction AND the raw full-text",
        "extraction in `04_Littérature_secondaire` (whitespace-insensitive),",
        "copied byte-for-byte (including the printed 'what depends us', p. 144).",
        "",
        f"Backup: `{BACKUP.name}`. Stamp: `metadata.{WAVE_STAMP}`.",
        "",
        "| node | page |",
        "|---|---|",
    ]
    lines += [f"| `{nid}` | {page} |" for nid, page in applied]
    if skipped:
        lines += ["", "Skipped:", ""]
        lines += [f"- `{nid}`: {why}" for nid, why in skipped]
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"report -> {REPORT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
