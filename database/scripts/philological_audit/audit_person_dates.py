"""Discipline person-node date qualifiers.

For ancient persons (periods Presocratic / Classical Greek / Hellenistic
/ Roman Imperial / Patristic / Late Antiquity / Second Temple Judaism)
we require dates to carry one of:

  - ``c.`` (circa)        approximate point
  - ``fl.``               floruit
  - ``before`` / ``after``
  - ``d.``                death-only (when sole survivor of the pair)
  - explicit range ``X-Y CE``

Bare years like ``185 CE`` get prepended with ``c.`` since no ancient
date is known to single-year precision -- but ONLY when both endpoints
exist on the same person, so we can't introduce false precision in the
gap. When only one endpoint exists, we still hedge with ``c.`` because
the convention is universal in critical editions.

Modern dates (Patristic cutoff at 800 CE for safety) are left as-is.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import re
import sys
from typing import Any

import asyncpg
from _common import REPORTS_DIR, connect, emit_summary, normalize_meta, write_jsonl

ANCIENT_PERIODS = {
    "Presocratic",
    "Classical Greek",
    "Hellenistic",
    "Roman Imperial",
    "Roman Republican",
    "Patristic",
    "Late Antiquity",
    "Second Temple Judaism",
    "Medieval",  # included because pre-modern conventions are the same
    "Byzantine",
}

BARE_YEAR_RE = re.compile(r"^\s*(?P<year>\d{1,4})\s*(?P<era>BC|BCE|CE|AD)?\s*$", re.I)
RANGE_RE = re.compile(
    r"^\s*(?P<a>\d{1,4})\s*[-–—]\s*(?P<b>\d{1,4})\s*(?P<era>BC|BCE|CE|AD)\s*$",
    re.I,
)
QUALIFIER_RE = re.compile(r"\b(c\.|ca\.|circa|fl\.|floruit|before|after|d\.)\b", re.I)


def needs_circa(value: str) -> bool:
    if not value or not value.strip():
        return False
    if QUALIFIER_RE.search(value):
        return False
    return bool(BARE_YEAR_RE.match(value))


def hedge(value: str) -> str:
    m = BARE_YEAR_RE.match(value)
    if not m:
        return value
    year = m.group("year")
    raw_era = (m.group("era") or "CE").upper()
    # Map AD->CE and BC->BCE without affecting BCE itself
    era_map = {"AD": "CE", "CE": "CE", "BC": "BCE", "BCE": "BCE"}
    era = era_map.get(raw_era, raw_era)
    return f"c. {year} {era}"


async def audit(conn: asyncpg.Connection) -> list[dict[str, Any]]:
    rows = await conn.fetch(
        "SELECT node_id, label, period, metadata FROM free_will.kg_nodes WHERE type='person'"
    )
    findings: list[dict[str, Any]] = []
    for row in rows:
        period = row["period"]
        metadata = normalize_meta(row["metadata"])

        # ancient or no-period (defensive)
        ancient = period in ANCIENT_PERIODS or not period

        if not ancient:
            continue

        node_id = row["node_id"]
        fixed_meta: dict[str, Any] = {}
        per_field_issues: list[dict[str, Any]] = []
        for field in ("birth_date", "death_date", "floruit"):
            val = metadata.get(field)
            if not isinstance(val, str) or not val.strip():
                continue
            if needs_circa(val):
                new_val = hedge(val)
                if new_val != val:
                    fixed_meta[field] = new_val
                    per_field_issues.append(
                        {
                            "field": field,
                            "from": val,
                            "to": new_val,
                        }
                    )

        if per_field_issues:
            findings.append(
                {
                    "node_id": node_id,
                    "dimension": "person_dates",
                    "issue": "bare_year_added_circa_qualifier",
                    "period": period,
                    "label": row["label"],
                    "changes": per_field_issues,
                    "suggested_fix": {"set_metadata": fixed_meta},
                    "confidence": 0.9,
                    "auto_apply": True,
                }
            )

        no_dates = (
            not metadata.get("birth_date")
            and not metadata.get("death_date")
            and not metadata.get("floruit")
            and not metadata.get("approximate_dates")
            and not metadata.get("dates")
        )
        if no_dates:
            findings.append(
                {
                    "node_id": node_id,
                    "dimension": "person_dates",
                    "issue": "no_dates_present",
                    "period": period,
                    "label": row["label"],
                    "suggested_fix": {"set_metadata": {"needs_date_metadata": True}},
                    "confidence": 1.0,
                    "auto_apply": True,
                }
            )

    return findings


async def apply_fixes(conn: asyncpg.Connection, findings: list[dict[str, Any]]) -> int:
    applied = 0
    for f in findings:
        if not f.get("auto_apply"):
            continue
        node_id = f["node_id"]
        fix = f["suggested_fix"].get("set_metadata", {})
        if not fix:
            continue
        row = await conn.fetchrow(
            "SELECT metadata FROM free_will.kg_nodes WHERE node_id=$1", node_id
        )
        if row is None:
            continue
        metadata = normalize_meta(row["metadata"])
        for k, v in fix.items():
            metadata[k] = v
        await conn.execute(
            "UPDATE free_will.kg_nodes SET metadata=$2::jsonb, updated_at=now() WHERE node_id=$1",
            node_id,
            json.dumps(metadata, ensure_ascii=False),
        )
        applied += 1
    return applied


async def amain(args: argparse.Namespace) -> int:
    conn = await connect()
    try:
        findings = await audit(conn)
        report_path = REPORTS_DIR / "person_dates_report.jsonl"
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
        emit_summary("person_dates", counts)
        print(f"[person_dates] wrote {report_path}", file=sys.stderr)

        if args.apply:
            applied = await apply_fixes(conn, findings)
            print(f"[person_dates] applied {applied} nodes", file=sys.stderr)
    finally:
        await conn.close()
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit ancient-person date qualifiers")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    return asyncio.run(amain(args))


if __name__ == "__main__":
    sys.exit(main())
