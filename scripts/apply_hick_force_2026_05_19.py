#!/usr/bin/env python3
"""Force re-apply the Hick E2 patch onto the 8 Hick scholarly_argument nodes.

Background
----------
A first-pass E2 run stamped the 8 Hick argument nodes with
``e2_confidence = "not_found"`` (the original local PDF was only a 20-page
front-matter excerpt). After re-acquisition of the full Hick 1966 PDF
(libgen md5 37337ca1bdeec6ea6851e70851325ca2, 410 pp.), the Hick agent
produced ``data/kg/e2_patches/hick.json`` with verified ``high`` confidence
verbatims for all 8 arguments — but the main integration script
``integrate_e2_patches_2026_05_19.py`` skips any node already carrying
``e2_verified_at``, so the new ``high``-confidence data is not applied.

Action
------
Targeted overwrite of the 8 Hick nodes only:
  - Replace ``e2_*`` fields with the new patch values
  - Lift ``needs_evidence`` to false (was true from the "not_found" pass)
  - Stamp ``e2_force_overwrite_at = 2026-05-19`` and
    ``e2_force_overwrite_reason = "full PDF re-acquired; high confidence"``
  - Preserve the previous confidence in ``e2_previous_confidence`` for audit

Idempotent — second run skips nodes that already carry
``e2_force_overwrite_at == "2026-05-19"``.

Snapshot of ``nodes.jsonl`` is written to
``data/kg/snapshots/2026-05-19-pre-hick-force/`` before mutation.
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
PATCH_PATH = ROOT / "data" / "kg" / "e2_patches" / "hick.json"
SNAPSHOT_DIR = ROOT / "data" / "kg" / "snapshots" / "2026-05-19-pre-hick-force"

FORCE_DATE = "2026-05-19"
FORCE_REASON = "full PDF re-acquired; high confidence"
NOW = datetime.now(UTC).isoformat(sep=" ")
WAVE_TAG = "e2_hick_force_2026_05_19"


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
    scholar = patch.get("scholar", "John Hick")
    print(f"loaded {len(patches)} Hick arg patches")

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

    forced = 0
    already = 0
    not_found = 0
    needs_evidence_lifted = 0

    for arg_id, p in patches.items():
        i = idx_by_id.get(arg_id)
        if i is None:
            not_found += 1
            print(f"  NOT FOUND: {arg_id}", file=sys.stderr)
            continue
        node = json.loads(lines[i])
        md_raw = node.get("metadata")
        md = parse_metadata(md_raw)

        if md.get("e2_force_overwrite_at") == FORCE_DATE:
            already += 1
            continue

        confidence = p.get("verification_confidence", "unknown")

        # Preserve previous values
        if md.get("e2_confidence"):
            md["e2_previous_confidence"] = md["e2_confidence"]
        if md.get("e2_verified_at"):
            md["e2_previous_verified_at"] = md["e2_verified_at"]

        # Overwrite e2_* with new patch values
        md["e2_verified_at"] = NOW
        md["e2_verified_by"] = WAVE_TAG
        md["e2_verifying_scholar"] = scholar
        if p.get("pdf_source"):
            md["e2_pdf_source"] = p["pdf_source"]
        if p.get("page"):
            md["e2_page"] = p["page"]
        if p.get("chapter"):
            md["e2_chapter"] = p["chapter"]
        if p.get("quote_verbatim"):
            md["e2_quote_verbatim"] = p["quote_verbatim"]
        if p.get("translation_en"):
            md["e2_translation_en"] = p["translation_en"]
        if p.get("language_original"):
            md["e2_language_original"] = p["language_original"]
        if p.get("context"):
            md["e2_context"] = p["context"]
        md["e2_confidence"] = confidence

        # Force-overwrite stamps
        md["e2_force_overwrite_at"] = FORCE_DATE
        md["e2_force_overwrite_reason"] = FORCE_REASON

        # Lift needs_evidence for high/medium
        if confidence in ("high", "medium") and md.get("needs_evidence") is True:
            md["needs_evidence"] = False
            md["needs_evidence_lifted_at"] = NOW
            md["needs_evidence_lifted_reason"] = (
                f"E2 force-overwrite via full PDF, confidence={confidence}"
            )
            needs_evidence_lifted += 1

        node["metadata"] = serialize_metadata(md, md_raw)
        node["updated_at"] = NOW
        lines[i] = json.dumps(node, ensure_ascii=False)
        forced += 1

    print(f"\nforced overwrites: {forced}")
    print(f"already force-overwritten (skipped): {already}")
    print(f"not found in nodes.jsonl: {not_found}")
    print(f"needs_evidence lifted: {needs_evidence_lifted}")

    if not commit:
        print("\n[DRY-RUN] use --commit to apply")
        return 0
    if forced == 0:
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
