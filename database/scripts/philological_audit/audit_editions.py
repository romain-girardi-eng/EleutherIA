"""Edition-metadata completeness sweep over ``work`` kg_nodes.

For each ``work`` node we check:

1. Whether ``metadata.editions`` exists and is a non-empty list.
2. If absent, whether the *singular* ``metadata.edition`` field is
   populated (a few legacy nodes from Phase 9-11 use this form).
3. If neither, propose a fallback fix:

   - For nodes with a recognized author + canonical short title, map
     to the consensus critical edition from a curated lookup table
     (Bekker, OCT, SC, GCS, SVF, Usener, Loeb, Bruns, etc.).
   - Otherwise flag ``metadata.needs_edition_metadata = true``.

Zero fabrication: the curated lookup only contains editions Romain has
explicitly cited in earlier phases (per project memory). When in doubt
we flag rather than invent.
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

# Curated editions lookup. Keys match against node_id substrings (lowercased)
# OR the canonical short title from ancient_works. Values are a list of
# {"editor": str, "year": int|str, "series": str, "note": str?} entries.
#
# This table is *small and conservative on purpose*. It only contains
# editions Romain has explicitly cited in earlier phases (see project
# memory Phase 9-11). Anything not in here is flagged for manual review,
# not auto-completed.
CURATED_EDITIONS: dict[str, list[dict[str, str]]] = {
    "aristotle_nicomachean_ethics": [
        {"editor": "Bywater", "year": "1894", "series": "OCT"},
        {"editor": "Bekker", "year": "1831", "series": "Berlin Academy"},
    ],
    "aristotle_eudemian_ethics": [
        {"editor": "Walzer & Mingay", "year": "1991", "series": "OCT"},
    ],
    "aristotle_metaphysics": [
        {"editor": "Ross", "year": "1924", "series": "Oxford"},
        {"editor": "Jaeger", "year": "1957", "series": "OCT"},
    ],
    "aristotle_de_interpretatione": [
        {"editor": "Minio-Paluello", "year": "1949", "series": "OCT"},
    ],
    "aristotle_physics": [
        {"editor": "Ross", "year": "1936", "series": "OCT"},
    ],
    "alexander_de_fato": [
        {"editor": "Bruns", "year": "1892", "series": "Suppl. Arist. II.2"},
        {"editor": "Thillet", "year": "1984", "series": "Budé"},
        {"editor": "Sharples", "year": "1983", "series": "Duckworth (transl.)"},
    ],
    "alexander_mantissa": [
        {"editor": "Bruns", "year": "1887", "series": "Suppl. Arist. II.1"},
    ],
    "alexander_quaestiones": [
        {"editor": "Bruns", "year": "1892", "series": "Suppl. Arist. II.2"},
    ],
    "cicero_de_fato": [
        {"editor": "Ax", "year": "1938", "series": "Teubner"},
        {"editor": "Sharples", "year": "1991", "series": "Aris & Phillips (transl.)"},
        {"editor": "Yon", "year": "1933", "series": "Budé"},
    ],
    "cicero_de_divinatione": [
        {"editor": "Giomini", "year": "1975", "series": "Teubner"},
    ],
    "cicero_academica": [
        {"editor": "Plasberg", "year": "1922", "series": "Teubner"},
    ],
    "cicero_de_natura_deorum": [
        {"editor": "Plasberg & Ax", "year": "1933", "series": "Teubner"},
    ],
    "origen_de_principiis": [
        {
            "editor": "Görgemanns & Karpp",
            "year": "1976",
            "series": "Behr (Oxford 2017)",
        },
        {
            "editor": "Crouzel & Simonetti",
            "year": "1978-84",
            "series": "SC 252-253, 268-269, 312",
        },
        {"editor": "Butterworth", "year": "1936", "series": "SPCK (transl.)"},
    ],
    "origen_contra_celsum": [
        {"editor": "Borret", "year": "1967-76", "series": "SC 132, 136, 147, 150"},
        {"editor": "Koetschau", "year": "1899", "series": "GCS 2-3"},
        {"editor": "Chadwick", "year": "1953", "series": "Cambridge (transl.)"},
    ],
    "origen_de_oratione": [
        {"editor": "Koetschau", "year": "1899", "series": "GCS 3"},
    ],
    "origen_commentary_on_romans": [
        {"editor": "Hammond Bammel", "year": "1990-98", "series": "AGLB 16, 33, 34"},
        {"editor": "Scheck", "year": "2001-02", "series": "FOTC 103-104 (transl.)"},
    ],
    "origen_philocalia": [
        {"editor": "Junod / Harl", "year": "1976-83", "series": "SC 226, 302"},
        {"editor": "Robinson", "year": "1893", "series": "Cambridge"},
    ],
    "justin_first_apology": [
        {"editor": "Marcovich", "year": "1994", "series": "PTS 38"},
        {"editor": "Goodspeed", "year": "1915", "series": "Göttingen"},
        {"editor": "Minns & Parvis", "year": "2009", "series": "OECT"},
    ],
    "justin_dialogue_trypho": [
        {"editor": "Marcovich", "year": "1997", "series": "PTS 47"},
        {"editor": "Bobichon", "year": "2003", "series": "Paradosis 47/1-2"},
        {"editor": "Archambault", "year": "1909", "series": "Textes et documents 8"},
    ],
    "boethius_consolation": [
        {"editor": "Bieler", "year": "1957", "series": "CCSL 94"},
        {"editor": "Moreschini", "year": "2005", "series": "Teubner"},
        {"editor": "Tester", "year": "1973", "series": "Loeb 74"},
    ],
    "boethius_second_commentary_de_interpretatione": [
        {"editor": "Meiser", "year": "1880", "series": "Teubner"},
    ],
    "epicurus_letter_herodotus": [
        {"editor": "Usener", "year": "1887", "series": "Epicurea"},
        {"editor": "Arrighetti", "year": "1973", "series": "Einaudi"},
    ],
    "epicurus_letter_menoeceus": [
        {"editor": "Usener", "year": "1887", "series": "Epicurea"},
    ],
    "epicurus_kuriai_doxai": [
        {"editor": "Usener", "year": "1887", "series": "Epicurea"},
    ],
    "lucretius_de_rerum_natura": [
        {"editor": "Bailey", "year": "1947", "series": "Oxford"},
        {"editor": "Munro", "year": "1886", "series": "Cambridge"},
    ],
    "plato_republic": [
        {"editor": "Burnet", "year": "1900-07", "series": "OCT"},
        {"editor": "Slings", "year": "2003", "series": "OCT"},
    ],
    "plato_timaeus": [
        {"editor": "Burnet", "year": "1900-07", "series": "OCT"},
    ],
    "plato_laws": [
        {"editor": "Burnet", "year": "1900-07", "series": "OCT"},
    ],
    "plato_apology": [
        {"editor": "Burnet", "year": "1900-07", "series": "OCT"},
    ],
    "plato_phaedo": [
        {"editor": "Burnet", "year": "1900-07", "series": "OCT"},
    ],
    "augustine_de_libero_arbitrio": [
        {"editor": "Green", "year": "1956", "series": "CCSL 29"},
    ],
    "augustine_confessions": [
        {"editor": "O'Donnell", "year": "1992", "series": "Oxford"},
        {"editor": "Verheijen", "year": "1981", "series": "CCSL 27"},
    ],
    "augustine_de_civitate_dei": [
        {"editor": "Dombart & Kalb", "year": "1955", "series": "CCSL 47-48"},
    ],
    "augustine_de_gratia": [
        {"editor": "Migne", "year": "1865", "series": "PL 44"},
    ],
    "chrysippus_on_fate": [
        {"editor": "von Arnim", "year": "1903-05", "series": "SVF II"},
        {"editor": "Long & Sedley", "year": "1987", "series": "Cambridge"},
    ],
}


def lookup_edition(
    node_id: str, canonical_id: str | None, label: str | None
) -> list[dict[str, str]] | None:
    haystack = " ".join(
        filter(
            None, [node_id.lower(), (canonical_id or "").lower(), (label or "").lower()]
        )
    )
    # Normalize: replace separators
    haystack = re.sub(r"[\s\-]+", "_", haystack)
    for key, editions in CURATED_EDITIONS.items():
        # all underscore-separated tokens of key must appear in haystack
        tokens = key.split("_")
        if all(tok in haystack for tok in tokens):
            return editions
    return None


async def audit(conn: asyncpg.Connection) -> list[dict[str, Any]]:
    rows = await conn.fetch(
        "SELECT node_id, label, metadata FROM free_will.kg_nodes WHERE type='work'"
    )
    # Try to map kg work_id -> ancient_works.canonical_id for richer matching
    aw_rows = await conn.fetch(
        "SELECT kg_work_id, canonical_id FROM free_will.ancient_works WHERE kg_work_id IS NOT NULL"
    )
    canonical_by_kg: dict[str, str] = {
        r["kg_work_id"]: r["canonical_id"] for r in aw_rows
    }

    findings: list[dict[str, Any]] = []
    for row in rows:
        node_id = row["node_id"]
        label = row["label"]
        metadata = normalize_meta(row["metadata"])
        editions = metadata.get("editions")
        if isinstance(editions, list) and editions:
            continue  # already covered

        singular = metadata.get("edition")
        if isinstance(singular, str) and singular.strip():
            # normalize singular -> list
            findings.append(
                {
                    "node_id": node_id,
                    "dimension": "editions",
                    "issue": "edition_singular_should_be_list",
                    "current": {"edition": singular},
                    "suggested_fix": {
                        "set_metadata": {"editions": [{"raw": singular}]}
                    },
                    "confidence": 0.9,
                    "auto_apply": True,
                }
            )
            continue

        canonical_id = canonical_by_kg.get(node_id)
        matched = lookup_edition(node_id, canonical_id, label)
        if matched:
            findings.append(
                {
                    "node_id": node_id,
                    "dimension": "editions",
                    "issue": "missing_edition_metadata_curated_match",
                    "current": None,
                    "suggested_fix": {"set_metadata": {"editions": matched}},
                    "confidence": 0.95,
                    "auto_apply": True,
                    "label": label,
                    "canonical_id": canonical_id,
                }
            )
        else:
            findings.append(
                {
                    "node_id": node_id,
                    "dimension": "editions",
                    "issue": "missing_edition_metadata_no_match",
                    "current": None,
                    "suggested_fix": {"set_metadata": {"needs_edition_metadata": True}},
                    "confidence": 1.0,
                    "auto_apply": True,
                    "label": label,
                    "canonical_id": canonical_id,
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
        # Drop legacy singular when replaced by list
        if "editions" in fix and "edition" in metadata:
            metadata.pop("edition", None)
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
        report_path = REPORTS_DIR / "editions_report.jsonl"
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
        emit_summary("editions", counts)
        print(f"[editions] wrote {report_path}", file=sys.stderr)

        if args.apply:
            applied = await apply_fixes(conn, findings)
            print(f"[editions] applied {applied} nodes", file=sys.stderr)
    finally:
        await conn.close()
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit work-node edition metadata")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    return asyncio.run(amain(args))


if __name__ == "__main__":
    sys.exit(main())
