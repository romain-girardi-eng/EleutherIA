#!/usr/bin/env python3
"""Integrate E2 verification patches into KG nodes.jsonl.

Each E2 sub-agent produced a per-scholar JSON patch in data/kg/e2_patches/
containing for each argument: page exacte, quote_verbatim (+ optional
translation_en), chapter, context, confidence — all verified by direct PDF
reading.

This script merges the patches into nodes.jsonl metadata:
- metadata.e2_verified_at: 2026-05-19
- metadata.e2_pdf_source: path
- metadata.e2_page: ...
- metadata.e2_chapter: ...
- metadata.e2_quote_verbatim: ...
- metadata.e2_translation_en: ...  (if non-English original)
- metadata.e2_context: ...
- metadata.e2_confidence: high|medium|low
- metadata.needs_evidence: false (only for high+medium confidence)

Idempotent. Snapshot before mutation. Dry-run by default.
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
SNAPSHOT_DIR = ROOT / "data" / "kg" / "snapshots" / "2026-05-19-pre-e2-integration"
PATCHES_DIR = ROOT / "data" / "kg" / "e2_patches"

WAVE_TAG = "e2_integration_2026_05_19"
NOW = datetime.now(UTC).isoformat(sep=" ")


def parse_metadata(raw: Any) -> dict[str, Any]:
    if raw is None or raw == "":
        return {}
    if isinstance(raw, dict):
        return raw
    return json.loads(raw)


def serialize_metadata(md: dict[str, Any], original: Any) -> Any:
    if isinstance(original, str) or original is None:
        return json.dumps(md, ensure_ascii=False)
    return md


def main(commit: bool = False) -> int:
    if not PATCHES_DIR.exists():
        print(f"ERROR: {PATCHES_DIR} not found", file=sys.stderr)
        return 2

    # Load all patches
    all_patches: dict[str, dict[str, Any]] = {}
    scholar_files = sorted(PATCHES_DIR.glob("*.json"))
    print(f"Loading {len(scholar_files)} patch files:")
    for pf in scholar_files:
        with pf.open() as fh:
            data = json.load(fh)
        patches = data.get("patches", {})
        scholar = data.get("scholar", "?")
        # Bobzien/Sorabji also have wiring corrections — capture those separately later if present
        for arg_id, p in patches.items():
            if arg_id in all_patches:
                print(
                    f"  WARN: arg_id {arg_id} appears in multiple patches "
                    f"— keeping first",
                    file=sys.stderr,
                )
                continue
            p["_scholar"] = scholar
            all_patches[arg_id] = p
        print(f"  {pf.name}: {len(patches)} patches ({scholar})")

    print(f"\nTotal unique args to patch: {len(all_patches)}")

    # Load nodes
    lines = NODES_PATH.read_text(encoding="utf-8").splitlines()
    nodes_by_id_idx: dict[str, int] = {}
    for i, ln in enumerate(lines):
        if not ln.strip():
            continue
        try:
            n = json.loads(ln)
            nid = n.get("id")
            if nid:
                nodes_by_id_idx[nid] = i
        except json.JSONDecodeError:
            continue

    # Apply patches
    patched_count = 0
    already_count = 0
    not_found_count = 0
    confidence_counts: dict[str, int] = {}
    needs_evidence_lifted = 0
    for arg_id, p in all_patches.items():
        idx = nodes_by_id_idx.get(arg_id)
        if idx is None:
            not_found_count += 1
            print(f"  NOT FOUND: {arg_id}", file=sys.stderr)
            continue
        node = json.loads(lines[idx])
        md_raw = node.get("metadata")
        md = parse_metadata(md_raw)

        # Idempotence: skip if already patched
        if md.get("e2_verified_at"):
            already_count += 1
            continue

        confidence = p.get("verification_confidence", "unknown")
        confidence_counts[confidence] = confidence_counts.get(confidence, 0) + 1

        # Apply patch fields
        md["e2_verified_at"] = NOW
        md["e2_verified_by"] = WAVE_TAG
        md["e2_verifying_scholar"] = p.get("_scholar")
        if p.get("pdf_source"):
            md["e2_pdf_source"] = p["pdf_source"]
        if p.get("publication_id"):
            md["e2_publication_id"] = p["publication_id"]
        if p.get("page"):
            md["e2_page"] = p["page"]
        if p.get("chapter"):
            md["e2_chapter"] = p["chapter"]
        if p.get("quote_verbatim"):
            md["e2_quote_verbatim"] = p["quote_verbatim"]
        if p.get("quote_de"):
            md["e2_quote_de"] = p["quote_de"]
        if p.get("translation_en"):
            md["e2_translation_en"] = p["translation_en"]
        if p.get("context"):
            md["e2_context"] = p["context"]
        md["e2_confidence"] = confidence

        # Lift needs_evidence for high+medium (low stays flagged)
        if confidence in ("high", "medium") and md.get("needs_evidence"):
            md["needs_evidence"] = False
            md["needs_evidence_lifted_at"] = NOW
            md["needs_evidence_lifted_reason"] = (
                f"E2 verified via direct PDF reading, confidence={confidence}"
            )
            needs_evidence_lifted += 1

        node["metadata"] = serialize_metadata(md, md_raw)
        node["updated_at"] = NOW
        lines[idx] = json.dumps(node, ensure_ascii=False)
        patched_count += 1

    print(f"\nApplied: {patched_count}")
    print(f"Already patched (skipped): {already_count}")
    print(f"Not found in nodes.jsonl: {not_found_count}")
    print(f"needs_evidence lifted: {needs_evidence_lifted}")
    print(f"Confidence distribution: {confidence_counts}")

    if not commit:
        print("\n[DRY-RUN] Use --commit to apply.")
        return 0

    if patched_count == 0:
        print("\nOK: nothing to apply.")
        return 0

    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(NODES_PATH, SNAPSHOT_DIR / NODES_PATH.name)
    print(f"\nSnapshot: {SNAPSHOT_DIR / NODES_PATH.name}")

    NODES_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Written: {NODES_PATH}")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--commit", action="store_true")
    args = ap.parse_args()
    sys.exit(main(commit=args.commit))
