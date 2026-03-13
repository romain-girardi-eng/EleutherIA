#!/usr/bin/env python3
"""
Correct quote_aristotle_origin_principle_9cb3c262 to a single exact Greek quotation.

This script:
- replaces the paraphrastic composite node text with a verbatim Greek clause from EN III.1
- removes the extra EN III.5 citation added during batch 02
- preserves the EN III.1 citation as the sole primary passage anchor
- writes a small correction report

Usage:
    set -a; source .env; set +a
    uv run --directory database python database/scripts/fix_quote_aristotle_origin_principle_verbatim.py
    uv run --directory database python database/scripts/fix_quote_aristotle_origin_principle_verbatim.py --confirm
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import uuid
from pathlib import Path
from typing import Any

import asyncpg

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = "free_will"
RUN_TAG = "kg_quote_origin_principle_verbatim_fix_2026_03_08"
REPORT_JSON = ROOT / "docs" / "reports" / "2026-03-08-kg-quote-origin-principle-fix.json"
REPORT_MD = ROOT / "docs" / "reports" / "2026-03-08-kg-quote-origin-principle-fix.md"

NODE_ID = "quote_aristotle_origin_principle_9cb3c262"
REMOVE_PASSAGE_ID = "28b16b62-34cb-4db0-a445-c778d696cb4e"
KEEP_PASSAGE_ID = "61f93a32-769e-498b-968d-de545a9bd124"

VERBATIM_GREEK = (
    "ὧν δʼ ἐν αὐτῷ ἡ ἀρχή, ἐπʼ αὐτῷ καὶ τὸ πράττειν καὶ μή."
)
SOURCE_CTS_URN = "urn:cts:greekLit:tlg0086.tlg010.perseus-grc2:3.1"
VERIFICATION_URL = "https://el.wikisource.org/wiki/%CE%97%CE%B8%CE%B9%CE%BA%CE%AC_%CE%9D%CE%B9%CE%BA%CE%BF%CE%BC%CE%AC%CF%87%CE%B5%CE%B9%CE%B1/%CE%93"


def jd(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


async def ensure_node_exists(conn: asyncpg.Connection, node_id: str) -> None:
    exists = await conn.fetchval(
        f"SELECT 1 FROM {SCHEMA}.kg_nodes WHERE node_id = $1",
        node_id,
    )
    if not exists:
        raise RuntimeError(f"Required node missing: {node_id}")


async def ensure_passage_exists(conn: asyncpg.Connection, passage_id: str) -> None:
    exists = await conn.fetchval(
        f"SELECT 1 FROM {SCHEMA}.passages WHERE passage_id = $1",
        passage_id,
    )
    if not exists:
        raise RuntimeError(f"Required passage missing: {passage_id}")


async def update_quote_node(conn: asyncpg.Connection, apply: bool) -> None:
    await ensure_node_exists(conn, NODE_ID)
    alt_names = await conn.fetchval(
        f"SELECT alternative_names FROM {SCHEMA}.kg_nodes WHERE node_id = $1",
        NODE_ID,
    )
    if isinstance(alt_names, str):
        alt_names = json.loads(alt_names)
    metadata = {
        "source_work": "Nicomachean Ethics III.1",
        "primary_source": "Aristotle, Nicomachean Ethics III.1",
        "ancient_sources": ["Aristotle, Nicomachean Ethics III.1"],
        "quote_status": "verbatim Greek quotation",
        "quote_text_original": VERBATIM_GREEK,
        "quote_language": "grc",
        "source_cts_urn": SOURCE_CTS_URN,
        "verification_url": VERIFICATION_URL,
        "related_concepts": ["To Eph' Hêmin (Τὸ ἐφ' ἡμῖν) - What is In Our Power"],
    }
    description = "Verbatim Greek quotation from Aristotle, Nicomachean Ethics III.1."
    if apply:
        await conn.execute(
            f"""
            UPDATE {SCHEMA}.kg_nodes
            SET label = $2,
                description = $3,
                alternative_names = $4::jsonb,
                metadata = $5::jsonb,
                updated_at = NOW()
            WHERE node_id = $1
            """,
            NODE_ID,
            VERBATIM_GREEK,
            description,
            jd(alt_names or []),
            jd(metadata),
        )


async def delete_citation(conn: asyncpg.Connection, passage_id: str, apply: bool) -> bool:
    exists = await conn.fetchval(
        f"""
        SELECT 1
        FROM {SCHEMA}.passage_citations
        WHERE passage_id = $1 AND kg_node_id = $2
        """,
        passage_id,
        NODE_ID,
    )
    if not exists:
        return False
    if apply:
        await conn.execute(
            f"""
            DELETE FROM {SCHEMA}.passage_citations
            WHERE passage_id = $1 AND kg_node_id = $2
            """,
            passage_id,
            NODE_ID,
        )
    return True


async def ensure_keep_citation(conn: asyncpg.Connection, apply: bool) -> bool:
    await ensure_passage_exists(conn, KEEP_PASSAGE_ID)
    exists = await conn.fetchval(
        f"""
        SELECT 1
        FROM {SCHEMA}.passage_citations
        WHERE passage_id = $1 AND kg_node_id = $2
        """,
        KEEP_PASSAGE_ID,
        NODE_ID,
    )
    if exists:
        if apply:
            await conn.execute(
                f"""
                UPDATE {SCHEMA}.passage_citations
                SET citation_type = 'primary_source',
                    confidence = 0.99,
                    notes = $3
                WHERE passage_id = $1 AND kg_node_id = $2
                """,
                KEEP_PASSAGE_ID,
                NODE_ID,
                "Verbatim Greek quotation from Nicomachean Ethics III.1.",
            )
        return False
    if apply:
        await conn.execute(
            f"""
            INSERT INTO {SCHEMA}.passage_citations (
                citation_id, passage_id, kg_node_id, citation_type, confidence, notes, created_at
            )
            VALUES ($1, $2, $3, 'primary_source', 0.99, $4, NOW())
            """,
            uuid.uuid4(),
            KEEP_PASSAGE_ID,
            NODE_ID,
            "Verbatim Greek quotation from Nicomachean Ethics III.1.",
        )
    return True


async def main(confirm: bool) -> None:
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is not set")

    conn = await asyncpg.connect(dsn=database_url, statement_cache_size=0)
    try:
        await update_quote_node(conn, confirm)
        removed = await delete_citation(conn, REMOVE_PASSAGE_ID, confirm)
        inserted = await ensure_keep_citation(conn, confirm)
        current_citations = await conn.fetch(
            f"""
            SELECT passage_id, citation_type, confidence, notes
            FROM {SCHEMA}.passage_citations
            WHERE kg_node_id = $1
            ORDER BY passage_id
            """,
            NODE_ID,
        )

        summary = {
            "run_tag": RUN_TAG,
            "applied": confirm,
            "node_id": NODE_ID,
            "label": VERBATIM_GREEK,
            "source": "Aristotle, Nicomachean Ethics III.1",
            "source_cts_urn": SOURCE_CTS_URN,
            "verification_url": VERIFICATION_URL,
            "removed_composite_citation_passage_id": REMOVE_PASSAGE_ID if removed else None,
            "kept_verbatim_citation_passage_id": KEEP_PASSAGE_ID,
            "inserted_keep_citation": inserted,
            "current_citations": [
                {
                    "passage_id": str(row["passage_id"]),
                    "citation_type": row["citation_type"],
                    "confidence": row["confidence"],
                    "notes": row["notes"],
                }
                for row in current_citations
            ],
        }

        REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
        REPORT_JSON.write_text(jd(summary) + "\n", encoding="utf-8")
        REPORT_MD.write_text(
            "\n".join(
                [
                    "# Aristotle Origin Principle Quote Fix",
                    "",
                    f"- Applied: `{confirm}`",
                    f"- Node: `{NODE_ID}`",
                    f"- Exact Greek: `{VERBATIM_GREEK}`",
                    "- Source: `Aristotle, Nicomachean Ethics III.1`",
                    f"- CTS URN: `{SOURCE_CTS_URN}`",
                    f"- Verification URL: `{VERIFICATION_URL}`",
                    f"- Removed EN III.5 citation: `{removed}`",
                    f"- EN III.1 citation inserted: `{inserted}`",
                    "",
                ]
            ),
            encoding="utf-8",
        )

        print(json.dumps(summary, ensure_ascii=False, indent=2))
        if not confirm:
            print("\nDry run only. Re-run with --confirm to apply changes.")
    finally:
        await conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--confirm", action="store_true", help="Apply the quote correction")
    args = parser.parse_args()
    asyncio.run(main(confirm=args.confirm))
