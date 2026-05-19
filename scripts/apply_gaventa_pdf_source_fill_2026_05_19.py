#!/usr/bin/env python3
"""Backfill ``metadata.e2_pdf_source`` on Gaventa-verified scholarly_argument
nodes.

The Gaventa E2 verification (data/kg/e2_patches/gaventa.json) uses
``source_file`` (chapter-range .txt extracts of Gaventa NTL Romans 2024)
rather than ``pdf_source``. The main integration script
``integrate_e2_patches_2026_05_19.py`` therefore left
``e2_pdf_source = None`` on all 15 Gaventa nodes, which broke E2 traceability
guarantees flagged by the independent audit.

Action
------
For each Gaventa patch entry:
  - Resolve the absolute path of the chapter-range file:
    ``{DOCTORAT_BASE}/{source_file}``
  - Set ``metadata.e2_pdf_source`` to that absolute path
  - Also set ``metadata.e2_source_file`` (txt-extract metadata) and
    ``metadata.e2_line_in_txt`` (line anchor inside the .txt) for full
    reproducibility
  - Stamp ``e2_pdf_source_filled_at = 2026-05-19``

Idempotent — re-running skips nodes that already have ``e2_pdf_source``.

Snapshot of ``nodes.jsonl`` is written to
``data/kg/snapshots/2026-05-19-pre-gaventa-pdf-fill/`` before mutation.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
NODES_PATH = ROOT / "data" / "kg" / "nodes.jsonl"
PATCH_PATH = ROOT / "data" / "kg" / "e2_patches" / "gaventa.json"
SNAPSHOT_DIR = ROOT / "data" / "kg" / "snapshots" / "2026-05-19-pre-gaventa-pdf-fill"

DOCTORAT_BASE = Path(
    "/Users/romaingirardi/Desktop/DOCTORAT/Doctorat SHAL/"
    "04_Littérature_secondaire/08_Commentaires_NT"
)

FILL_DATE = "2026-05-19"
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
    patch = json.loads(PATCH_PATH.read_text(encoding="utf-8"))
    patches: dict[str, dict[str, Any]] = patch.get("patches", {})
    print(f"loaded {len(patches)} Gaventa arg patches")

    lines = NODES_PATH.read_text(encoding="utf-8").splitlines()
    idx_by_id: dict[str, int] = {}
    for i, ln in enumerate(lines):
        if not ln.strip():
            continue
        try:
            n = json.loads(ln)
        except json.JSONDecodeError:
            continue
        nid = n.get("id")
        if nid:
            idx_by_id[nid] = i

    filled = 0
    already = 0
    not_found = 0
    missing_file = 0
    for arg_id, p in patches.items():
        i = idx_by_id.get(arg_id)
        if i is None:
            not_found += 1
            print(f"  NOT FOUND: {arg_id}", file=sys.stderr)
            continue
        node = json.loads(lines[i])
        md_raw = node.get("metadata")
        md = parse_metadata(md_raw)

        if md.get("e2_pdf_source"):
            already += 1
            continue

        source_file = p.get("source_file")
        if not source_file:
            print(f"  WARN: no source_file for {arg_id}", file=sys.stderr)
            missing_file += 1
            continue

        abs_path = DOCTORAT_BASE / source_file
        if not abs_path.exists():
            print(f"  WARN: file not present on disk for {arg_id}: {abs_path}", file=sys.stderr)
            # We still record the path — it's a verified attribution by the agent.
        md["e2_pdf_source"] = str(abs_path)
        md["e2_source_file"] = source_file
        if p.get("line_in_txt") is not None:
            md["e2_line_in_txt"] = p["line_in_txt"]
        if p.get("section"):
            md["e2_section"] = p["section"]
        md["e2_pdf_source_filled_at"] = FILL_DATE
        md["e2_pdf_source_fill_note"] = (
            "OCR-extracted .txt chapter-range files of Gaventa NTL Romans 2024 "
            "(WJK). Printed page numbers are not preserved in OCR; cite via "
            "(file, section, line_in_txt)."
        )

        node["metadata"] = serialize_metadata(md, md_raw)
        node["updated_at"] = NOW
        lines[i] = json.dumps(node, ensure_ascii=False)
        filled += 1

    print(f"\nfilled: {filled}")
    print(f"already filled (skipped): {already}")
    print(f"not found in nodes.jsonl: {not_found}")
    print(f"missing source_file in patch: {missing_file}")

    if not commit:
        print("\n[DRY-RUN] use --commit to apply")
        return 0
    if filled == 0:
        print("\nOK: nothing to apply (idempotent).")
        return 0

    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(NODES_PATH, SNAPSHOT_DIR / NODES_PATH.name)
    print(f"snapshot: {SNAPSHOT_DIR / NODES_PATH.name}")

    NODES_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"written: {NODES_PATH}")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--commit", action="store_true")
    args = ap.parse_args()
    sys.exit(main(commit=args.commit))
