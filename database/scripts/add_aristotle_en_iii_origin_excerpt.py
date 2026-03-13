#!/usr/bin/env python3
"""
Add the exact Aristotle EN III.1 excerpt node for the origin-principle clause.

This script only:
- verifies that the exact Greek clause exists in the local EN III.1 passage text
- creates the missing exact excerpt passage node if needed
- adds structural and evidence edges for the excerpt node
- patches the reviewed quote metadata to point at the exact excerpt node
- writes a small verification report

Usage:
    set -a; source .env; set +a
    python database/scripts/add_aristotle_en_iii_origin_excerpt.py
    python database/scripts/add_aristotle_en_iii_origin_excerpt.py --confirm
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import asyncpg

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = "free_will"
RUN_TAG = "kg_aristotle_en_iii_origin_excerpt_2026_03_08"
REPORT_JSON = ROOT / "docs" / "reports" / "2026-03-08-kg-aristotle-en-iii-origin-excerpt.json"
REPORT_MD = ROOT / "docs" / "reports" / "2026-03-08-kg-aristotle-en-iii-origin-excerpt.md"

NEW_NODE_ID = "passage_aristotle_en_iii_1_1110a15"
QUOTE_NODE_ID = "quote_aristotle_origin_principle_9cb3c262"
AUTHOR_NODE_ID = "person_aristotle_384_322bce_c2d4f6a8"
WORK_NODE_ID = "work_nicomachean_ethics_aristotle_c350bce_d3e5f7b9"
CHAPTER_NODE_ID = "passage_arist_en_3_1"
ARGUMENT_NODE_ID = "argument_voluntary_involuntary_distinction_aristotle_g7h8i9j0"
CONCEPT_HEKOUSION_ID = "concept_hekousion_voluntary_aristotle_a1b2c3d4"
PASSAGE_ID = "61f93a32-769e-498b-968d-de545a9bd124"
PASSAGE_CTS_URN = "urn:cts:greekLit:tlg0086.tlg010.perseus-grc2:3.1"
CANONICAL_REF = "Arist. EN III.1, 1110a15-17"
VERIFICATION_URLS = [
    "https://el.wikisource.org/wiki/%CE%97%CE%B8%CE%B9%CE%BA%CE%AC_%CE%9D%CE%B9%CE%BA%CE%BF%CE%BC%CE%AC%CF%87%CE%B5%CE%B9%CE%B1/%CE%93",
    "https://www.greek-language.gr/greekLang/ancient_greek/tools/corpora/anthology/content.html?m=1&t=374",
]
EXACT_GREEK = "ὧν δʼ ἐν αὐτῷ ἡ ἀρχή, ἐπʼ αὐτῷ καὶ τὸ πράττειν καὶ μή."


def jd(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


@dataclass(frozen=True)
class SourceNode:
    node_id: str
    label: str
    node_type: str
    period: str
    description: str
    metadata: dict[str, Any]


@dataclass(frozen=True)
class EdgeSpec:
    source_id: str
    target_id: str
    relation: str
    metadata: dict[str, Any]


NODE = SourceNode(
    node_id=NEW_NODE_ID,
    label="EN III.1, 1110a15-17 (ἐπʼ αὐτῷ καὶ τὸ πράττειν καὶ μή)",
    node_type="passage",
    period="Classical Greek",
    description=(
        "**Reference:** EN III.1, 1110a15-17\n"
        "**Author:** Aristotle\n"
        "**Work:** Nicomachean Ethics\n"
        "**CTS URN:** urn:cts:greekLit:tlg0086.tlg010.perseus-grc2:3.1\n\n"
        "**Original Greek:**\n"
        "ὧν δʼ ἐν αὐτῷ ἡ ἀρχή, ἐπʼ αὐτῷ καὶ τὸ πράττειν καὶ μή.\n\n"
        "**Verification:** exact clause confirmed in the local EN III.1 passage record and "
        "cross-checked against Greek Wikisource and greek-language.gr."
    ),
    metadata={
        "author": "Aristotle",
        "work_title": "Nicomachean Ethics",
        "bekker": "1110a15-17",
        "canonical_ref": CANONICAL_REF,
        "cts_urn": PASSAGE_CTS_URN,
        "language": "grc",
        "school": "Peripatetic",
        "passage_id": PASSAGE_ID,
        "parent_chapter": CHAPTER_NODE_ID,
        "quote_text_original": EXACT_GREEK,
        "verification_urls": VERIFICATION_URLS,
        "reviewed_by": RUN_TAG,
    },
)

EDGES = [
    EdgeSpec(
        source_id=NEW_NODE_ID,
        target_id=AUTHOR_NODE_ID,
        relation="authored_by",
        metadata={"reviewed_by": RUN_TAG},
    ),
    EdgeSpec(
        source_id=NEW_NODE_ID,
        target_id=WORK_NODE_ID,
        relation="part_of",
        metadata={"reviewed_by": RUN_TAG},
    ),
    EdgeSpec(
        source_id=NEW_NODE_ID,
        target_id=CHAPTER_NODE_ID,
        relation="part_of",
        metadata={"reviewed_by": RUN_TAG},
    ),
    EdgeSpec(
        source_id=NEW_NODE_ID,
        target_id=ARGUMENT_NODE_ID,
        relation="source_for",
        metadata={"reference": "III.1, 1110a15-17", "reviewed_by": RUN_TAG},
    ),
    EdgeSpec(
        source_id=NEW_NODE_ID,
        target_id=CONCEPT_HEKOUSION_ID,
        relation="discusses",
        metadata={"reviewed_by": RUN_TAG},
    ),
]


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


async def verify_local_text(conn: asyncpg.Connection) -> dict[str, Any]:
    await ensure_passage_exists(conn, PASSAGE_ID)
    row = await conn.fetchrow(
        f"""
        SELECT passage_id, canonical_ref, cts_urn, text_content
        FROM {SCHEMA}.passages
        WHERE passage_id = $1
        """,
        PASSAGE_ID,
    )
    if row["cts_urn"] != PASSAGE_CTS_URN:
        raise RuntimeError(
            f"Unexpected CTS URN for {PASSAGE_ID}: {row['cts_urn']} != {PASSAGE_CTS_URN}"
        )
    if EXACT_GREEK not in row["text_content"]:
        raise RuntimeError("Exact Greek clause not found in the local EN III.1 passage text")
    return {
        "passage_id": str(row["passage_id"]),
        "canonical_ref": row["canonical_ref"],
        "cts_urn": row["cts_urn"],
        "exact_text_present": True,
    }


async def upsert_node(conn: asyncpg.Connection, node: SourceNode, apply: bool) -> bool:
    existing = await conn.fetchval(
        f"SELECT 1 FROM {SCHEMA}.kg_nodes WHERE node_id = $1",
        node.node_id,
    )
    if existing:
        if apply:
            await conn.execute(
                f"""
                UPDATE {SCHEMA}.kg_nodes
                SET label = $2,
                    type = $3,
                    period = $4,
                    description = $5,
                    alternative_names = '[]'::jsonb,
                    metadata = $6::jsonb,
                    updated_at = NOW()
                WHERE node_id = $1
                """,
                node.node_id,
                node.label,
                node.node_type,
                node.period,
                node.description,
                jd(node.metadata),
            )
        return False
    if apply:
        await conn.execute(
            f"""
            INSERT INTO {SCHEMA}.kg_nodes (
                node_id, label, type, period, description, alternative_names, metadata, created_at, updated_at
            )
            VALUES ($1, $2, $3, $4, $5, '[]'::jsonb, $6::jsonb, NOW(), NOW())
            """,
            node.node_id,
            node.label,
            node.node_type,
            node.period,
            node.description,
            jd(node.metadata),
        )
    return True


async def edge_exists(conn: asyncpg.Connection, edge: EdgeSpec) -> bool:
    exists = await conn.fetchval(
        f"""
        SELECT 1
        FROM {SCHEMA}.kg_edges
        WHERE source_id = $1 AND target_id = $2 AND relation = $3
        """,
        edge.source_id,
        edge.target_id,
        edge.relation,
    )
    return bool(exists)


async def ensure_edge(conn: asyncpg.Connection, edge: EdgeSpec, apply: bool) -> bool:
    if edge.source_id != NEW_NODE_ID or apply:
        await ensure_node_exists(conn, edge.source_id)
    await ensure_node_exists(conn, edge.target_id)
    if await edge_exists(conn, edge):
        return False
    if apply:
        await conn.execute(
            f"""
            INSERT INTO {SCHEMA}.kg_edges (edge_id, source_id, target_id, relation, metadata, created_at)
            VALUES ($1, $2, $3, $4, $5::jsonb, NOW())
            """,
            uuid.uuid4(),
            edge.source_id,
            edge.target_id,
            edge.relation,
            jd(edge.metadata),
        )
    return True


async def patch_quote_metadata(conn: asyncpg.Connection, apply: bool) -> dict[str, Any]:
    await ensure_node_exists(conn, QUOTE_NODE_ID)
    current = await conn.fetchval(
        f"SELECT metadata FROM {SCHEMA}.kg_nodes WHERE node_id = $1",
        QUOTE_NODE_ID,
    )
    if isinstance(current, str):
        current = json.loads(current)
    merged = dict(current or {})
    merged.update(
        {
            "supporting_exact_passage_node_id": NEW_NODE_ID,
            "supporting_exact_reference": "EN III.1, 1110a15-17",
            "supporting_parent_passage_node_id": CHAPTER_NODE_ID,
        }
    )
    if apply:
        await conn.execute(
            f"""
            UPDATE {SCHEMA}.kg_nodes
            SET metadata = $2::jsonb,
                updated_at = NOW()
            WHERE node_id = $1
            """,
            QUOTE_NODE_ID,
            jd(merged),
        )
    return merged


async def count_en_iii_chapter_nodes(conn: asyncpg.Connection) -> int:
    return await conn.fetchval(
        f"""
        SELECT COUNT(*)
        FROM {SCHEMA}.kg_nodes
        WHERE type = 'passage' AND node_id LIKE 'passage_arist_en_3_%'
        """
    )


async def fetch_new_node_state(conn: asyncpg.Connection) -> dict[str, Any] | None:
    row = await conn.fetchrow(
        f"""
        SELECT node_id, label, type, period, description, metadata
        FROM {SCHEMA}.kg_nodes
        WHERE node_id = $1
        """,
        NEW_NODE_ID,
    )
    if not row:
        return None
    return {
        "node_id": row["node_id"],
        "label": row["label"],
        "type": row["type"],
        "period": row["period"],
        "description": row["description"],
        "metadata": row["metadata"],
    }


async def fetch_new_edges(conn: asyncpg.Connection) -> list[dict[str, Any]]:
    rows = await conn.fetch(
        f"""
        SELECT source_id, relation, target_id, metadata
        FROM {SCHEMA}.kg_edges
        WHERE source_id = $1
        ORDER BY relation, target_id
        """,
        NEW_NODE_ID,
    )
    return [dict(row) for row in rows]


async def main(confirm: bool) -> None:
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is not set")

    conn = await asyncpg.connect(dsn=database_url, statement_cache_size=0)
    try:
        for node_id in (
            QUOTE_NODE_ID,
            AUTHOR_NODE_ID,
            WORK_NODE_ID,
            CHAPTER_NODE_ID,
            ARGUMENT_NODE_ID,
            CONCEPT_HEKOUSION_ID,
        ):
            await ensure_node_exists(conn, node_id)

        local_verification = await verify_local_text(conn)
        en_iii_chapter_node_count = await count_en_iii_chapter_nodes(conn)
        node_inserted = await upsert_node(conn, NODE, confirm)
        inserted_edges = 0
        for edge in EDGES:
            inserted_edges += int(await ensure_edge(conn, edge, confirm))
        patched_quote_metadata = await patch_quote_metadata(conn, confirm)

        summary = {
            "run_tag": RUN_TAG,
            "applied": confirm,
            "local_verification": local_verification,
            "existing_en_iii_chapter_node_count": en_iii_chapter_node_count,
            "new_excerpt_node_id": NEW_NODE_ID,
            "new_excerpt_node_inserted": node_inserted,
            "inserted_edge_count": inserted_edges,
            "quote_node_id": QUOTE_NODE_ID,
            "quote_supporting_exact_passage_node_id": patched_quote_metadata[
                "supporting_exact_passage_node_id"
            ],
            "verification_urls": VERIFICATION_URLS,
            "new_excerpt_node": await fetch_new_node_state(conn),
            "new_excerpt_edges": await fetch_new_edges(conn),
        }

        REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
        REPORT_JSON.write_text(jd(summary) + "\n", encoding="utf-8")
        REPORT_MD.write_text(
            "\n".join(
                [
                    "# Aristotle EN III Origin Excerpt",
                    "",
                    f"- Applied: `{confirm}`",
                    f"- Existing EN III chapter-level passage nodes: `{en_iii_chapter_node_count}`",
                    f"- New excerpt node: `{NEW_NODE_ID}`",
                    f"- Exact reference: `{CANONICAL_REF}`",
                    f"- Exact Greek: `{EXACT_GREEK}`",
                    f"- Local passage verified: `{local_verification['exact_text_present']}`",
                    f"- Inserted edge count: `{inserted_edges}`",
                    f"- Quote metadata patched: `{QUOTE_NODE_ID}` -> `{NEW_NODE_ID}`",
                    "",
                    "Verification URLs:",
                    *[f"- `{url}`" for url in VERIFICATION_URLS],
                    "",
                ]
            ),
            encoding="utf-8",
        )

        print(json.dumps(summary, ensure_ascii=False, indent=2, default=str))
        if not confirm:
            print("\nDry run only. Re-run with --confirm to apply changes.")
    finally:
        await conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--confirm", action="store_true", help="Apply the excerpt node insertion")
    args = parser.parse_args()
    asyncio.run(main(confirm=args.confirm))
