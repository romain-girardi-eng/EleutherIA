"""Tamper-evidence audit: detect drift in ``passages.text_content``.

Workflow (see docs/operations/corpus-integrity.md):

1. **First run** (baseline absent): snapshot every passage's SHA-256 (NFC
   normalization, see ``eleutheria_database.services.text_integrity``) into
   ``data/integrity/text_checksums.jsonl.gz``. Requires ``DATABASE_URL``;
   only ever point it at a database you trust as a baseline.
2. **Subsequent runs**: recompute checksums from the live table and report
   passages that were **added**, **removed**, or whose text **changed**
   since the baseline. Also cross-checks the stored ``text_sha256`` column
   (when populated) against the recomputed digest and reports mismatches.
3. Drift is *reported, never repaired*: this script performs zero writes to
   the database and never rewrites the baseline unless ``--update-baseline``
   is passed explicitly after manual adjudication.

Exit codes: 0 = no drift (or baseline just created), 1 = drift detected,
2 = configuration error.

Usage:
    DATABASE_URL=... python audit_text_drift.py            # report drift
    DATABASE_URL=... python audit_text_drift.py --update-baseline
"""

from __future__ import annotations

import argparse
import asyncio
import gzip
import json
import sys
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

import asyncpg
from _common import REPORTS_DIR, connect, emit_summary, write_jsonl

from eleutheria_database.services.text_integrity import (
    DriftReport,
    compare_checksums,
    text_sha256,
)

BASELINE_PATH = (
    Path(__file__).resolve().parents[3] / "data" / "integrity" / "text_checksums.jsonl.gz"
)

# ---------------------------------------------------------------------------
# Pure helpers (unit-tested in database/tests/unit/test_text_integrity.py)
# ---------------------------------------------------------------------------


def rows_to_checksum_map(
    rows: Iterable[Mapping[str, Any]],
) -> dict[str, dict[str, Any]]:
    """Index baseline/current rows by passage_id.

    Each row must carry ``passage_id`` and ``sha256``; extra keys
    (work_canonical_id, canonical_ref, passage_role) are kept for reporting.
    """
    return {str(row["passage_id"]): dict(row) for row in rows}


def baseline_bytes(rows: Iterable[Mapping[str, Any]]) -> bytes:
    """Serialize baseline rows to gzipped JSONL bytes (deterministic order)."""
    lines = "".join(
        json.dumps(dict(row), sort_keys=True, ensure_ascii=False) + "\n"
        for row in sorted(rows, key=lambda r: str(r["passage_id"]))
    )
    return gzip.compress(lines.encode("utf-8"), mtime=0)


def parse_baseline_bytes(blob: bytes) -> dict[str, dict[str, Any]]:
    """Parse gzipped JSONL baseline bytes into a checksum map."""
    text = gzip.decompress(blob).decode("utf-8")
    rows = [json.loads(line) for line in text.splitlines() if line.strip()]
    return rows_to_checksum_map(rows)


def stored_hash_mismatches(
    rows: Iterable[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Rows whose stored text_sha256 column disagrees with the recomputed one.

    Rows with a NULL stored hash are skipped (column not yet backfilled).
    """
    out: list[dict[str, Any]] = []
    for row in rows:
        stored = row.get("stored_sha256")
        if stored and stored != row["sha256"]:
            out.append(
                {
                    "passage_id": str(row["passage_id"]),
                    "issue": "stored_text_sha256_mismatch",
                    "stored_sha256": stored,
                    "recomputed_sha256": row["sha256"],
                    "work_canonical_id": row.get("work_canonical_id"),
                    "canonical_ref": row.get("canonical_ref"),
                }
            )
    return out


def drift_to_report_rows(report: DriftReport) -> list[dict[str, Any]]:
    """Flatten a DriftReport into JSONL report rows (one per drifted passage)."""
    rows: list[dict[str, Any]] = []
    for kind in ("added", "removed", "changed"):
        for pid, entry in sorted(getattr(report, kind).items()):
            row = {"passage_id": pid, "drift": kind}
            row.update(entry)
            rows.append(row)
    return rows


# ---------------------------------------------------------------------------
# DB access (read-only)
# ---------------------------------------------------------------------------


async def fetch_current(conn: asyncpg.Connection) -> list[dict[str, Any]]:
    records = await conn.fetch(
        """
        SELECT p.passage_id::text AS passage_id,
               p.canonical_ref,
               p.passage_role,
               p.text_content,
               p.text_sha256 AS stored_sha256,
               w.canonical_id AS work_canonical_id
          FROM free_will.passages p
          JOIN free_will.ancient_works w ON w.work_id = p.work_id
         ORDER BY p.passage_id
        """
    )
    rows: list[dict[str, Any]] = []
    for rec in records:
        rows.append(
            {
                "passage_id": rec["passage_id"],
                "sha256": text_sha256(rec["text_content"]),
                "stored_sha256": rec["stored_sha256"],
                "work_canonical_id": rec["work_canonical_id"],
                "canonical_ref": rec["canonical_ref"],
                "passage_role": rec["passage_role"],
            }
        )
    return rows


def _baseline_row(row: Mapping[str, Any]) -> dict[str, Any]:
    """Strip volatile keys before persisting a row into the baseline."""
    return {
        "passage_id": row["passage_id"],
        "sha256": row["sha256"],
        "work_canonical_id": row["work_canonical_id"],
        "canonical_ref": row["canonical_ref"],
        "passage_role": row["passage_role"],
    }


async def amain(args: argparse.Namespace) -> int:
    try:
        conn = await connect()
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    try:
        current_rows = await fetch_current(conn)
    finally:
        await conn.close()

    baseline_path = Path(args.baseline) if args.baseline else BASELINE_PATH
    persistable = [_baseline_row(r) for r in current_rows]

    if not baseline_path.exists() or args.update_baseline:
        action = "updated" if baseline_path.exists() else "created"
        baseline_path.parent.mkdir(parents=True, exist_ok=True)
        baseline_path.write_bytes(baseline_bytes(persistable))
        emit_summary(
            "audit_text_drift",
            {f"baseline_{action}": len(persistable)},
        )
        print(f"Baseline {action}: {baseline_path} ({len(persistable)} passages)")
        return 0

    baseline_map = parse_baseline_bytes(baseline_path.read_bytes())
    current_map = rows_to_checksum_map(persistable)
    report = compare_checksums(baseline_map, current_map)

    report_rows = drift_to_report_rows(report)
    report_rows.extend(stored_hash_mismatches(current_rows))

    out_path = REPORTS_DIR / "text_drift.jsonl"
    write_jsonl(report_rows, out_path)

    counts = dict(report.summary_counts())
    counts["stored_hash_mismatches"] = len(report_rows) - (
        counts["added"] + counts["removed"] + counts["changed"]
    )
    emit_summary("audit_text_drift", counts)
    print(f"Report written: {out_path} ({len(report_rows)} rows)")

    if report.has_drift or counts["stored_hash_mismatches"]:
        print(
            "DRIFT DETECTED — adjudicate manually (this script never auto-fixes). "
            "After review, re-snapshot with --update-baseline.",
            file=sys.stderr,
        )
        return 1
    print("No drift detected.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Detect tampering/drift in passages.text_content via SHA-256"
    )
    parser.add_argument(
        "--baseline",
        default=None,
        help=f"Baseline snapshot path (default: {BASELINE_PATH})",
    )
    parser.add_argument(
        "--update-baseline",
        action="store_true",
        help="Re-snapshot the baseline from the live DB (after manual adjudication)",
    )
    args = parser.parse_args()
    return asyncio.run(amain(args))


if __name__ == "__main__":
    sys.exit(main())
