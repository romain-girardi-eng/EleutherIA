"""CTS URN syntactic validator + fixer for ``passages.cts_urn``.

Validates each URN against the canonical CTS form:

    urn:cts:<namespace>:<textgroup>(.<work>(.<version>)?)?:<passage_ref>

Issues detected:

1. **Whitespace inside passage_ref** -- ``M. 232`` becomes ``M.232``.
   The Adversus Mathematicos URNs in tlg0544 are the bulk of this.
2. **Unknown book sentinel** (``?.17a``) -- some Plato Apology URNs use
   a literal ``?`` as book separator. We rewrite ``urn:...:?.17a`` to
   ``urn:...:17a`` (drop the unknown level).
3. **Missing work segment** -- ``tlg0544:M.232`` has no ``.tlgNNN``
   work id. Flagged but not auto-rewritten because we don't know the
   work number a priori.
4. **Missing namespace** -- anything not in {greekLit, latinLit,
   pdlpsci, csel} flagged for review.

We never *invent* URNs for null-cts passages -- those are flagged at
the passage level so the work-level ingestion can decide.
"""

from __future__ import annotations

import argparse
import asyncio
import re
import sys
from typing import Any

import asyncpg
from _common import REPORTS_DIR, connect, emit_summary, write_jsonl

KNOWN_NAMESPACES = {"greekLit", "latinLit", "pdlpsci", "csel", "cwkb"}

# Format check (post-normalisation):
CANONICAL_RE = re.compile(
    r"^urn:cts:[A-Za-z0-9_]+:[A-Za-z0-9_-]+(\.[A-Za-z0-9_-]+)*(:[^\s]+)?$"
)


def normalize_urn(urn: str) -> tuple[str, list[str]]:
    """Return (normalized, applied_fixes_list).

    Only mechanical transformations are applied:
    - strip leading/trailing whitespace
    - collapse spaces inside the passage_ref
    - drop the unknown-book sentinel `?.`
    """
    fixes: list[str] = []
    s = urn.strip()
    if s != urn:
        fixes.append("trimmed_whitespace")

    head, _, ref = s.rpartition(":")
    if ref and " " in ref:
        new_ref = ref.replace(" ", "")
        if new_ref != ref:
            s = f"{head}:{new_ref}"
            fixes.append("removed_inner_space_from_ref")
            ref = new_ref

    # Drop unknown-book sentinel "?." at the start of passage_ref
    if ref.startswith("?."):
        new_ref = ref[2:]
        s = f"{head}:{new_ref}"
        fixes.append("dropped_unknown_book_sentinel")

    return s, fixes


async def audit(conn: asyncpg.Connection) -> list[dict[str, Any]]:
    rows = await conn.fetch(
        "SELECT passage_id, cts_urn FROM free_will.passages WHERE cts_urn IS NOT NULL"
    )
    findings: list[dict[str, Any]] = []
    for row in rows:
        urn = row["cts_urn"]
        passage_id = str(row["passage_id"])
        normalized, fixes = normalize_urn(urn)

        if fixes:
            findings.append(
                {
                    "passage_id": passage_id,
                    "dimension": "cts_urn",
                    "issue": "fixable_format",
                    "current": urn,
                    "suggested_fix": {"cts_urn": normalized, "applied_fixes": fixes},
                    "confidence": 0.95,
                    "auto_apply": True,
                }
            )
            continue

        if not CANONICAL_RE.match(urn):
            findings.append(
                {
                    "passage_id": passage_id,
                    "dimension": "cts_urn",
                    "issue": "non_canonical_format",
                    "current": urn,
                    "suggested_fix": None,
                    "confidence": 0.6,
                    "auto_apply": False,
                }
            )
            continue

        parts = urn.split(":")
        if len(parts) >= 3 and parts[2] not in KNOWN_NAMESPACES:
            findings.append(
                {
                    "passage_id": passage_id,
                    "dimension": "cts_urn",
                    "issue": "unknown_namespace",
                    "current": urn,
                    "suggested_fix": None,
                    "confidence": 0.7,
                    "auto_apply": False,
                }
            )

        if len(parts) >= 4:
            tg_work = parts[3]
            if "." not in tg_work:
                findings.append(
                    {
                        "passage_id": passage_id,
                        "dimension": "cts_urn",
                        "issue": "missing_work_segment",
                        "current": urn,
                        "suggested_fix": None,
                        "confidence": 0.65,
                        "auto_apply": False,
                    }
                )

    # Passages with no cts_urn -- emit one summary row
    null_count = await conn.fetchval(
        "SELECT count(*) FROM free_will.passages WHERE cts_urn IS NULL"
    )
    if null_count:
        findings.append(
            {
                "passage_id": "*",
                "dimension": "cts_urn",
                "issue": "null_cts_urn",
                "current": None,
                "suggested_fix": {
                    "note": (
                        "Re-ingest source XML/JSON; we do not synthesize URNs. "
                        "Set ancient_works.metadata.needs_cts_urn = true."
                    )
                },
                "confidence": 1.0,
                "auto_apply": False,
                "passage_count": int(null_count),
            }
        )

    return findings


async def apply_fixes(conn: asyncpg.Connection, findings: list[dict[str, Any]]) -> int:
    applied = 0
    for f in findings:
        if not f.get("auto_apply"):
            continue
        passage_id = f["passage_id"]
        fix = f.get("suggested_fix") or {}
        new_urn = fix.get("cts_urn")
        if not new_urn:
            continue
        await conn.execute(
            "UPDATE free_will.passages SET cts_urn=$2 WHERE passage_id=$1::uuid",
            passage_id,
            new_urn,
        )
        applied += 1
    return applied


async def amain(args: argparse.Namespace) -> int:
    conn = await connect()
    try:
        findings = await audit(conn)
        report_path = REPORTS_DIR / "cts_urns_report.jsonl"
        write_jsonl(findings, report_path)

        by_issue: dict[str, int] = {}
        auto = 0
        for f in findings:
            by_issue[f["issue"]] = by_issue.get(f["issue"], 0) + 1
            if f["auto_apply"]:
                auto += 1
        counts = {
            "total_findings": len(findings),
            "auto_apply_pending": auto,
            **{f"issue.{k}": v for k, v in sorted(by_issue.items())},
        }
        emit_summary("cts_urns", counts)
        print(f"[cts_urns] wrote {report_path}", file=sys.stderr)

        if args.apply:
            applied = await apply_fixes(conn, findings)
            print(f"[cts_urns] applied {applied} passages", file=sys.stderr)
    finally:
        await conn.close()
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit passages.cts_urn syntax")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    return asyncio.run(amain(args))


if __name__ == "__main__":
    sys.exit(main())
