#!/usr/bin/env python3
"""Re-home mis-bound Cicero passage citations to the genuine works.

Citations on phi042 passages (KG nodes passage_cic_div_*) should reference
De Divinatione (phi053); citations on phi041 passages (KG nodes passage_cic_nat_deor_*)
should reference De Natura Deorum (phi050).

Matching strategy (exact-only — no fabrication):
  1. Exact ref match: node canonical_ref vs real passage canonical_ref
     (= cts_urn after last ':').  e.g. "De Div. 1" vs "1.1" — likely no match.
  2. Bare number fallback: extract integer N from node's canonical_ref
     (e.g. "De Div. 29" → 29), find passages in the real work whose ref
     ends with ".{N}" (e.g. "1.29", "2.29"). Re-home ONLY if exactly one
     passage in the real work matches that section number.

Any citation that does not resolve to a unique exact match is left unchanged
and listed in the manual-review report.

Dry-run by default; --commit to re-home exact matches in DB. Snapshot taken
before any mutation.

Usage:
    .venv/bin/python -m scripts.rehome_cicero_citations_2026_05_25 [--commit]
"""
from __future__ import annotations

import argparse
import asyncio
import json
import re
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import asyncpg

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT_DIR = ROOT / "data" / "corpus" / "fix_snapshots" / "rehome_cicero_citations_2026_05_25"
NODES_PATH = ROOT / "data" / "kg" / "nodes.jsonl"

# Source work canonical_ids (wrong home — Topica / Orator)
PHI042_CANONICAL = "urn_cts_latinlit_phi0474_phi042_lat"  # Topica (was "De Divinatione")
PHI041_CANONICAL = "urn_cts_latinlit_phi0474_phi041_lat"  # Orator (was "De Natura Deorum")

# Target canonical_ids (genuine works)
DIV_CANONICAL = "urn_cts_latinlit_phi0474_phi053_lat"   # De Divinatione
NATDEOR_CANONICAL = "urn_cts_latinlit_phi0474_phi050_lat"  # De Natura Deorum


def _db_url() -> str:
    for line in (ROOT / ".env").open(encoding="utf-8"):
        if line.startswith("DATABASE_URL="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit("DATABASE_URL not found in .env")


def _pg_url(url: str) -> str:
    if url.startswith("postgresql://"):
        return "postgres://" + url[len("postgresql://"):]
    return url


def _load_kg_node_canonical_ref(node_id: str) -> str | None:
    """Scan nodes.jsonl for the node and return its canonical_ref from metadata."""
    for line in NODES_PATH.open(encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        obj = json.loads(line)
        if obj.get("id") != node_id and obj.get("node_id") != node_id:
            continue
        meta_raw = obj.get("metadata")
        if isinstance(meta_raw, str):
            meta = json.loads(meta_raw)
        elif isinstance(meta_raw, dict):
            meta = meta_raw
        else:
            return None
        val = meta.get("canonical_ref")
        return str(val) if val is not None else None
    return None


def _extract_bare_number(canonical_ref: str | None) -> int | None:
    """Extract the bare integer from e.g. 'De Div. 29' → 29, 'De Nat. Deor. 12' → 12."""
    if not canonical_ref:
        return None
    m = re.search(r"\b(\d+)\s*$", canonical_ref.strip())
    return int(m.group(1)) if m else None


async def _collect_citations(conn: asyncpg.Connection, source_canonical_id: str) -> list[dict[str, Any]]:
    """Return all citation rows for passages of the given work."""
    rows = await conn.fetch(
        """
        SELECT pc.citation_id, pc.passage_id, pc.kg_node_id,
               pc.citation_type, pc.confidence,
               p.canonical_ref  AS passage_canonical_ref,
               p.cts_urn        AS passage_cts_urn
        FROM free_will.passage_citations pc
        JOIN free_will.passages p ON p.passage_id = pc.passage_id
        JOIN free_will.ancient_works w ON w.work_id = p.work_id
        WHERE w.canonical_id = $1
        ORDER BY p.canonical_ref, pc.kg_node_id
        """,
        source_canonical_id,
    )
    return [dict(r) for r in rows]


async def _collect_real_passages(conn: asyncpg.Connection, target_canonical_id: str) -> list[dict[str, Any]]:
    """Return all passages of the real target work."""
    rows = await conn.fetch(
        """
        SELECT p.passage_id, p.canonical_ref, p.cts_urn
        FROM free_will.passages p
        JOIN free_will.ancient_works w ON w.work_id = p.work_id
        WHERE w.canonical_id = $1
        ORDER BY p.sequence_number
        """,
        target_canonical_id,
    )
    return [dict(r) for r in rows]


def _build_ref_index(passages: list[dict]) -> dict[str, list[dict]]:
    """Build index: canonical_ref → [passage, ...].
    Also adds section-number index: bare integer N → [passage with ref ending .N].
    """
    by_ref: dict[str, list[dict]] = {}
    for p in passages:
        ref = p["canonical_ref"]
        by_ref.setdefault(ref, []).append(p)
    return by_ref


def _find_unique_match(
    node_canonical_ref: str | None,
    real_passages: list[dict],
    ref_index: dict[str, list[dict]],
) -> dict | None:
    """Return the unique matching real passage, or None."""
    # 1. Exact ref match
    if node_canonical_ref and node_canonical_ref in ref_index:
        candidates = ref_index[node_canonical_ref]
        if len(candidates) == 1:
            return candidates[0]
        return None  # ambiguous

    # 2. Bare number fallback
    n = _extract_bare_number(node_canonical_ref)
    if n is None:
        return None

    suffix = f".{n}"
    matches = [p for p in real_passages if p["canonical_ref"].endswith(suffix)]
    if len(matches) == 1:
        return matches[0]

    return None  # not unique


async def _snapshot_citations(rows: list[dict], label: str) -> None:
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
            "passage_cts_urn": r["passage_cts_urn"],
        }
        for r in rows
    ]
    snap_file.write_text(json.dumps(snap_data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  Snapshot: {snap_file} ({len(snap_data)} rows)")


async def process_group(
    conn: asyncpg.Connection,
    label: str,
    source_canonical_id: str,
    target_canonical_id: str,
    node_prefix: str,
    *,
    commit: bool,
) -> dict[str, Any]:
    """Process one group (cic_div or cic_nat_deor). Returns result summary."""
    print(f"\n{'='*60}")
    print(f"Group: {label}")
    print(f"  Source (wrong):  {source_canonical_id}")
    print(f"  Target (genuine): {target_canonical_id}")

    citations = await _collect_citations(conn, source_canonical_id)
    real_passages = await _collect_real_passages(conn, target_canonical_id)
    print(f"  Citations to process: {len(citations)}")
    print(f"  Real passages available: {len(real_passages)}")

    if not real_passages:
        print(f"  ERROR: no passages found for target {target_canonical_id} — did Step 1 run?")
        return {"total": len(citations), "rehomed": 0, "manual": len(citations), "error": True}

    ref_index = _build_ref_index(real_passages)

    # Snapshot citations before mutation
    await _snapshot_citations(citations, label)

    rehomed: list[dict] = []
    manual: list[dict] = []

    for cit in citations:
        kg_node_id = cit["kg_node_id"]
        node_canon_ref = _load_kg_node_canonical_ref(kg_node_id)

        match = _find_unique_match(node_canon_ref, real_passages, ref_index)
        if match:
            rehomed.append({
                "citation_id": str(cit["citation_id"]),
                "kg_node_id": kg_node_id,
                "old_passage_id": str(cit["passage_id"]),
                "new_passage_id": str(match["passage_id"]),
                "node_canonical_ref": node_canon_ref,
                "matched_real_ref": match["canonical_ref"],
                "matched_real_cts_urn": match["cts_urn"],
            })
        else:
            manual.append({
                "citation_id": str(cit["citation_id"]),
                "kg_node_id": kg_node_id,
                "old_passage_id": str(cit["passage_id"]),
                "node_canonical_ref": node_canon_ref,
                "passage_canonical_ref": cit["passage_canonical_ref"],
                "reason": "no unique ref match in real work",
            })

    print(f"\n  Exact-match re-homes: {len(rehomed)}")
    print(f"  Manual (no unique match): {len(manual)}")

    if rehomed:
        for r in rehomed:
            print(
                f"    REHOME {r['kg_node_id']}: node_ref={r['node_canonical_ref']!r} "
                f"→ real ref={r['matched_real_ref']!r} (passage {r['new_passage_id'][:8]}...)"
            )

    if manual:
        print(f"\n  Manual review required ({len(manual)} citations):")
        for m in manual[:20]:
            print(
                f"    {m['kg_node_id']}: node_ref={m['node_canonical_ref']!r} | "
                f"reason={m['reason']}"
            )
        if len(manual) > 20:
            print(f"    ... and {len(manual) - 20} more")

    # Save manual review report
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    report_file = SNAPSHOT_DIR / f"manual_review_{label}.json"
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
                    """
                    UPDATE free_will.passage_citations
                       SET passage_id = $1
                     WHERE citation_id = $2::uuid
                    """,
                    r["new_passage_id"],
                    r["citation_id"],
                )
        print(f"  Re-homed: {len(rehomed)} citations updated.")
    elif not commit and rehomed:
        print(f"  [DRY-RUN] Would re-home {len(rehomed)} citations.")

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

        result_div = await process_group(
            conn,
            label="cic_div",
            source_canonical_id=PHI042_CANONICAL,
            target_canonical_id=DIV_CANONICAL,
            node_prefix="passage_cic_div_",
            commit=commit,
        )
        result_nd = await process_group(
            conn,
            label="cic_nat_deor",
            source_canonical_id=PHI041_CANONICAL,
            target_canonical_id=NATDEOR_CANONICAL,
            node_prefix="passage_cic_nat_deor_",
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

        if not commit:
            print("\n[DRY-RUN] Pass --commit to write re-homes to DB.")

    finally:
        await conn.close()

    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--commit", action="store_true", help="Write re-homes to DB (default: dry-run)")
    args = ap.parse_args()
    sys.exit(asyncio.run(main(args.commit)))
