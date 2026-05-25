#!/usr/bin/env python3
"""Re-home Cicero citations to genuine works via difflib text-match.

Citations on phi042 passages (KG nodes passage_cic_div_*) should reference
De Divinatione (phi053). Citations on phi041 passages (KG nodes passage_cic_nat_deor_*)
should reference De Natura Deorum (phi050).

TEXT-MATCH STRATEGY:
  For each KG node:
    1. Extract its description (the Latin text it carries).
    2. Normalize (NFC, collapse whitespace, lowercase).
    3. Compare against each passage in the genuine target work using
       difflib.SequenceMatcher ratio.
    4. Re-home ONLY if the best match ratio >= 0.90 AND the best match is
       uniquely best (no tie within 0.02 of the best ratio).
    5. Otherwise: leave unchanged, record in manual-review report.

IMPORTANT — known limitation:
  The KG node descriptions contain text from the WRONG work (phi042 Topica /
  phi041 Orator) because the passages were ingested under misidentified CTS URNs.
  The genuine De Divinatione / De Natura Deorum passages contain entirely different
  Cicero texts. Text-match between Topica prose and De Div prose, or between Orator
  prose and De Nat Deor prose, yields ratios << 0.90 (empirically 0.15-0.26).
  This means 0 confident re-homes are expected. This is reported honestly.

Dry-run by default; --commit to re-home confident matches in DB. Snapshot taken
before any mutation.

Usage:
    .venv/bin/python -m scripts.rehome_cicero_textmatch_2026_05_25 [--commit]
"""
from __future__ import annotations

import argparse
import asyncio
import difflib
import json
import re
import sys
import unicodedata
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT_DIR = ROOT / "data" / "corpus" / "fix_snapshots" / "rehome_cicero_textmatch_2026_05_25"
NODES_PATH = ROOT / "data" / "kg" / "nodes.jsonl"

# Works that currently hold misbound citations
PHI042_CANONICAL = "urn_cts_latinlit_phi0474_phi042_lat"   # Topica (was "De Div" slot)
PHI041_CANONICAL = "urn_cts_latinlit_phi0474_phi041_lat"   # Orator (was "Nat Deor" slot)

# Genuine target works
DIV_CANONICAL = "urn_cts_latinlit_phi0474_phi053_lat"      # De Divinatione
NATDEOR_CANONICAL = "urn_cts_latinlit_phi0474_phi050_lat"  # De Natura Deorum

# Minimum difflib ratio to accept a match
MIN_RATIO = 0.90
# If best minus second-best < AMBIGUITY_DELTA, reject as ambiguous
AMBIGUITY_DELTA = 0.02


def _db_url() -> str:
    for line in (ROOT / ".env").open(encoding="utf-8"):
        if line.startswith("DATABASE_URL="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit("DATABASE_URL not found in .env")


def _pg_url(url: str) -> str:
    if url.startswith("postgresql://"):
        return "postgres://" + url[len("postgresql://"):]
    return url


def _normalize(text: str) -> str:
    """NFC normalize, collapse whitespace, lowercase."""
    if not text:
        return ""
    text = unicodedata.normalize("NFC", text)
    return " ".join(text.split()).lower()


def _load_kg_nodes(prefixes: tuple[str, ...]) -> dict[str, dict[str, Any]]:
    """Load all KG nodes whose id starts with any of the given prefixes."""
    result: dict[str, dict[str, Any]] = {}
    with NODES_PATH.open(encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            obj = json.loads(line)
            nid = obj.get("id") or obj.get("node_id", "")
            if any(nid.startswith(p) for p in prefixes):
                result[nid] = obj
    return result


def _get_node_text(node: dict) -> str | None:
    """Extract the description text from a KG node."""
    return node.get("description") or None


async def _collect_citations(conn, source_canonical_id: str) -> list[dict[str, Any]]:
    rows = await conn.fetch(
        """
        SELECT pc.citation_id, pc.passage_id, pc.kg_node_id,
               pc.citation_type, pc.confidence,
               p.canonical_ref AS passage_canonical_ref,
               p.cts_urn       AS passage_cts_urn
        FROM free_will.passage_citations pc
        JOIN free_will.passages p  ON p.passage_id  = pc.passage_id
        JOIN free_will.ancient_works w ON w.work_id = p.work_id
        WHERE w.canonical_id = $1
        ORDER BY p.canonical_ref, pc.kg_node_id
        """,
        source_canonical_id,
    )
    return [dict(r) for r in rows]


async def _collect_target_passages(conn, target_canonical_id: str) -> list[dict[str, Any]]:
    rows = await conn.fetch(
        """
        SELECT p.passage_id, p.canonical_ref, p.cts_urn, p.text_content
        FROM free_will.passages p
        JOIN free_will.ancient_works w ON w.work_id = p.work_id
        WHERE w.canonical_id = $1
        ORDER BY p.sequence_number
        """,
        target_canonical_id,
    )
    return [dict(r) for r in rows]


def _text_match(
    node_text: str,
    target_passages: list[dict],
) -> tuple[dict | None, float, str]:
    """
    Find the best-matching target passage via difflib ratio.
    Returns (best_passage_or_None, best_ratio, reason).
    """
    norm_node = _normalize(node_text)
    if not norm_node:
        return None, 0.0, "empty node text"

    scored: list[tuple[float, dict]] = []
    for p in target_passages:
        norm_p = _normalize(p.get("text_content") or "")
        if not norm_p:
            continue
        ratio = difflib.SequenceMatcher(None, norm_node, norm_p).ratio()
        scored.append((ratio, p))

    if not scored:
        return None, 0.0, "no target passages with text"

    scored.sort(key=lambda x: x[0], reverse=True)
    best_ratio, best_p = scored[0]

    if best_ratio < MIN_RATIO:
        return None, best_ratio, f"best ratio {best_ratio:.3f} < {MIN_RATIO}"

    if len(scored) > 1:
        second_ratio = scored[1][0]
        if best_ratio - second_ratio < AMBIGUITY_DELTA:
            return None, best_ratio, (
                f"ambiguous: best={best_ratio:.3f}, second={second_ratio:.3f}, "
                f"delta={best_ratio - second_ratio:.3f} < {AMBIGUITY_DELTA}"
            )

    return best_p, best_ratio, "ok"


async def process_group(
    conn,
    label: str,
    source_canonical_id: str,
    target_canonical_id: str,
    node_prefixes: tuple[str, ...],
    *,
    commit: bool,
) -> dict[str, Any]:
    print(f"\n{'='*60}")
    print(f"Group: {label}")
    print(f"  Source (wrong):   {source_canonical_id}")
    print(f"  Target (genuine): {target_canonical_id}")

    citations = await _collect_citations(conn, source_canonical_id)
    target_passages = await _collect_target_passages(conn, target_canonical_id)
    print(f"  Citations to process: {len(citations)}")
    print(f"  Target passages: {len(target_passages)}")

    if not target_passages:
        print(f"  ERROR: no passages in {target_canonical_id}")
        return {"total": len(citations), "rehomed": 0, "manual": len(citations), "error": True}

    # Snapshot citations before any mutation
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    snap_file = SNAPSHOT_DIR / f"citations_{label}.json"
    snap_data = [
        {
            "citation_id": str(r["citation_id"]),
            "passage_id": str(r["passage_id"]),
            "kg_node_id": r["kg_node_id"],
            "citation_type": r["citation_type"],
            "confidence": r["confidence"],
            "passage_canonical_ref": r["passage_canonical_ref"],
        }
        for r in citations
    ]
    snap_file.write_text(json.dumps(snap_data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  Snapshot: {snap_file}")

    # Load KG nodes
    kg_nodes = _load_kg_nodes(node_prefixes)

    rehomed: list[dict] = []
    manual: list[dict] = []

    for cit in citations:
        kg_node_id = cit["kg_node_id"]
        node = kg_nodes.get(kg_node_id)
        node_text = _get_node_text(node) if node else None

        if not node_text:
            # No text to match on
            manual.append({
                "citation_id": str(cit["citation_id"]),
                "kg_node_id": kg_node_id,
                "old_passage_id": str(cit["passage_id"]),
                "node_text_preview": None,
                "best_ratio": 0.0,
                "reason": "no node description text",
            })
            continue

        best_passage, best_ratio, reason = _text_match(node_text, target_passages)

        if best_passage:
            rehomed.append({
                "citation_id": str(cit["citation_id"]),
                "kg_node_id": kg_node_id,
                "old_passage_id": str(cit["passage_id"]),
                "new_passage_id": str(best_passage["passage_id"]),
                "node_text_preview": node_text[:80],
                "matched_canonical_ref": best_passage["canonical_ref"],
                "ratio": best_ratio,
            })
        else:
            manual.append({
                "citation_id": str(cit["citation_id"]),
                "kg_node_id": kg_node_id,
                "old_passage_id": str(cit["passage_id"]),
                "node_text_preview": node_text[:80] if node_text else None,
                "best_ratio": best_ratio,
                "reason": reason,
            })

    print(f"\n  Text-match confident re-homes (ratio >= {MIN_RATIO}): {len(rehomed)}")
    print(f"  Manual (below threshold or no text): {len(manual)}")

    if rehomed:
        for r in rehomed:
            print(f"    REHOME {r['kg_node_id']}: ratio={r['ratio']:.3f} -> {r['matched_canonical_ref']}")

    # Show distribution of best ratios for manual items
    ratios = [m["best_ratio"] for m in manual if m["best_ratio"] > 0]
    if ratios:
        ratios.sort(reverse=True)
        print(f"\n  Best-ratio distribution for manual items (top 10):")
        for ratio in ratios[:10]:
            print(f"    {ratio:.3f}")
        print(f"  Max ratio in manual: {max(ratios):.3f} (threshold: {MIN_RATIO})")

    # Save reports
    report_file = SNAPSHOT_DIR / f"report_{label}.json"
    report_file.write_text(
        json.dumps({"rehomed": rehomed, "manual": manual}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\n  Report: {report_file}")

    if commit and rehomed:
        print(f"\n  Committing {len(rehomed)} re-homes...")
        async with conn.transaction():
            for r in rehomed:
                await conn.execute(
                    """UPDATE free_will.passage_citations
                          SET passage_id = $1::uuid
                        WHERE citation_id = $2::uuid""",
                    r["new_passage_id"],
                    r["citation_id"],
                )
        print(f"  Done: {len(rehomed)} citations updated.")
    elif not commit and rehomed:
        print(f"  [DRY-RUN] Would re-home {len(rehomed)} citations.")
    else:
        print(f"  Nothing to commit (0 confident matches).")

    return {
        "total": len(citations),
        "rehomed": len(rehomed),
        "manual": len(manual),
        "error": False,
    }


async def main(commit: bool) -> int:
    import asyncpg

    conn: asyncpg.Connection = await asyncio.wait_for(
        asyncpg.connect(_pg_url(_db_url())), timeout=30
    )
    try:
        print(f"Mode: {'COMMIT' if commit else 'DRY-RUN'}")
        print(f"Timestamp: {datetime.now(UTC).isoformat()}")
        print(f"Text-match threshold: ratio >= {MIN_RATIO}")
        print()
        print("NOTE: KG node descriptions contain text from the wrong works (Topica/Orator).")
        print("      Text-match against genuine De Div/Nat Deor will yield ratios << 0.90.")
        print("      Expected result: 0 confident re-homes, 123 manual.")

        result_div = await process_group(
            conn,
            label="cic_div",
            source_canonical_id=PHI042_CANONICAL,
            target_canonical_id=DIV_CANONICAL,
            node_prefixes=("passage_cic_div_", "argument_cicero_de_div_"),
            commit=commit,
        )

        result_nd = await process_group(
            conn,
            label="cic_nat_deor",
            source_canonical_id=PHI041_CANONICAL,
            target_canonical_id=NATDEOR_CANONICAL,
            node_prefixes=("passage_cic_nat_deor_",),
            commit=commit,
        )

        print(f"\n{'='*60}")
        print("SUMMARY")
        print(
            f"  cic_div:      total={result_div['total']} "
            f"re-homed={result_div['rehomed']} manual={result_div['manual']}"
        )
        print(
            f"  cic_nat_deor: total={result_nd['total']} "
            f"re-homed={result_nd['rehomed']} manual={result_nd['manual']}"
        )
        total = result_div["total"] + result_nd["total"]
        total_rehomed = result_div["rehomed"] + result_nd["rehomed"]
        total_manual = result_div["manual"] + result_nd["manual"]
        print(
            f"  TOTAL:        total={total} re-homed={total_rehomed} manual={total_manual}"
        )
        print()
        print("DIAGNOSIS: Zero confident text-matches because KG node descriptions")
        print("  contain Topica/Orator prose (wrongly assigned), not De Div/Nat Deor prose.")
        print("  These 123 citations require a different approach:")
        print("  - Inspect scholarly intent of each citation (requires human judgment)")
        print("  - Or: after new De Div/Nat Deor passage ingestion with correct labels,")
        print("    compare the Topica/Orator passage content that was cited and find the")
        print("    philosophically corresponding De Div/Nat Deor passage manually.")

        if not commit:
            print("\n[DRY-RUN] Pass --commit to write (nothing will be committed for 0 matches).")

    finally:
        await conn.close()

    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--commit", action="store_true", help="Write to DB (default: dry-run)")
    args = ap.parse_args()
    sys.exit(asyncio.run(main(args.commit)))
