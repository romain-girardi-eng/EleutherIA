#!/usr/bin/env python3
"""Generate (NOT execute) text_provenance backfill SQL for review.

Emits one guarded UPDATE per Sources Chrétiennes work, using the verified
edition metadata in ``database/scripts/import_sc/config.py::WORK_REGISTRY``
(editions transcribed from the published SC volumes — never guessed), plus
one block for Scaife/Perseus-ingested works whose edition is deliberately
left ``null`` pending manual attribution (critical-editions-only policy:
we do not guess which edition underlies a Perseus/Open Greek & Latin text).

This script performs NO database access and NO writes beyond the SQL file.
Romain reviews the output, then applies it manually, e.g.:

    python database/scripts/generate_text_provenance_backfill.py \
        --output data/integrity/text_provenance_backfill.sql
    # review, then:
    # python database/scripts/apply_schema.py --migration data/integrity/text_provenance_backfill.sql

Provenance JSONB schema: docs/operations/corpus-integrity.md.
"""

from __future__ import annotations

import argparse
import datetime
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

SCRIPTS_DIR = Path(__file__).resolve().parent
CONFIG_PATH = SCRIPTS_DIR / "import_sc" / "config.py"


def load_work_registry(config_path: Path = CONFIG_PATH) -> dict[str, dict[str, Any]]:
    """Load WORK_REGISTRY from import_sc/config.py without package imports."""
    spec = importlib.util.spec_from_file_location("import_sc_config", config_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {config_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.WORK_REGISTRY


def sql_literal(value: str) -> str:
    """Escape a string as a single-quoted SQL literal (quote doubling only)."""
    return "'" + value.replace("'", "''") + "'"


def sc_provenance(entry: dict[str, Any], generated_on: str) -> dict[str, Any]:
    """Provenance JSONB payload for one WORK_REGISTRY entry."""
    return {
        "edition": entry["edition"],
        "series": entry.get("sc_volume"),
        "source_collection": "sources_chretiennes",
        "source_type": "critical_edition",
        "ingest_pipeline": "database/scripts/import_sc",
        "verified_from": "WORK_REGISTRY",
        "generated_on": generated_on,
    }


def sc_update_statement(entry: dict[str, Any], generated_on: str) -> str:
    """One reviewable UPDATE for a single SC work, keyed by canonical_id."""
    provenance = sc_provenance(entry, generated_on)
    payload = json.dumps(provenance, ensure_ascii=False, sort_keys=True)
    return (
        f"-- {entry.get('sc_volume', 'SC ?')} — {entry['author']}, {entry['title']}\n"
        f"-- Edition: {entry['edition']} (verified in WORK_REGISTRY)\n"
        "UPDATE free_will.passages p\n"
        f"SET text_provenance = {sql_literal(payload)}::jsonb\n"
        "FROM free_will.ancient_works w\n"
        "WHERE w.work_id = p.work_id\n"
        f"  AND w.canonical_id = {sql_literal(entry['node_id'])}\n"
        "  AND p.text_provenance IS NULL;\n"
    )


def scaife_update_statement(generated_on: str) -> str:
    """Guarded UPDATE for Scaife/Perseus-ingested works — edition stays null.

    Critical-editions-only policy: emitting "edition": null with an explicit
    flag instead of guessing which edition Perseus digitized. Each work must
    be attributed manually afterwards (update the JSONB 'edition' key and
    drop 'needs_manual_edition_attribution').
    """
    payload = json.dumps(
        {
            "edition": None,
            "needs_manual_edition_attribution": True,
            "source_collection": "perseus_scaife",
            "source_type": "digital_corpus",
            "ingest_pipeline": "database/scripts/ingest_scaife_work.py | eleutheria_database.services.scaife",
            "generated_on": generated_on,
        },
        ensure_ascii=False,
        sort_keys=True,
    )
    return (
        "-- Scaife/Perseus-ingested works: \"edition\": null -- NEEDS MANUAL EDITION ATTRIBUTION\n"
        "-- (critical-editions-only policy: never guess the underlying edition).\n"
        "-- Matches works ingested by ingest_scaife_work.py (canonical_id = CTS URN)\n"
        "-- or by the Temporal Scaife workflow (source = 'scaife_cts').\n"
        "UPDATE free_will.passages p\n"
        f"SET text_provenance = {sql_literal(payload)}::jsonb\n"
        "FROM free_will.ancient_works w\n"
        "WHERE w.work_id = p.work_id\n"
        "  AND (w.source = 'scaife_cts' OR w.canonical_id LIKE 'urn:cts:%')\n"
        "  AND p.text_provenance IS NULL;\n"
    )


def generate_sql(registry: dict[str, dict[str, Any]], generated_on: str) -> str:
    seen_nodes: set[str] = set()
    blocks: list[str] = [
        "-- text_provenance backfill — GENERATED FOR MANUAL REVIEW, do not apply blindly.\n"
        f"-- Generated on {generated_on} by database/scripts/generate_text_provenance_backfill.py\n"
        "-- Requires migration 20260610_03_text_integrity.sql (adds passages.text_provenance).\n"
        "-- Every UPDATE only touches rows whose text_provenance IS NULL (idempotent,\n"
        "-- never overwrites manually curated provenance).\n"
    ]
    for entry in registry.values():
        node_id = entry["node_id"]
        if node_id in seen_nodes:
            continue
        seen_nodes.add(node_id)
        blocks.append(sc_update_statement(entry, generated_on))
    blocks.append(scaife_update_statement(generated_on))
    return "\n".join(blocks)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        default=None,
        help="Write SQL to this path (default: stdout)",
    )
    args = parser.parse_args()

    registry = load_work_registry()
    generated_on = datetime.date.today().isoformat()
    sql = generate_sql(registry, generated_on)

    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(sql, encoding="utf-8")
        print(f"Wrote {out} ({len(sql)} chars, {len(registry)} registry entries)")
    else:
        sys.stdout.write(sql)
    return 0


if __name__ == "__main__":
    sys.exit(main())
