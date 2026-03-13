#!/usr/bin/env python3
"""Build and persist hierarchical tree indices for ancient works.

The generated JSON is intentionally richer than the original structural tree.
Each node stores a compact abstract, canonical refs, languages, token estimates,
and placeholders for concept/entity tags so the runtime can navigate works
coarse-to-fine before loading many passages.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import re
import sys
from collections import defaultdict
from typing import Any

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


def _parse_ref(canonical_ref: str) -> tuple[str, str, str]:
    parts = re.split(r"[.\s]+", canonical_ref.strip(), maxsplit=2)
    book = parts[0] if len(parts) > 0 else ""
    chapter = parts[1] if len(parts) > 1 else ""
    section = parts[2] if len(parts) > 2 else ""
    return book, chapter, section


def _estimate_tokens(text: str) -> int:
    return max(1, (len(text) + 3) // 4)


def _canonical_refs(passages: list[dict[str, Any]], limit: int = 3) -> list[str]:
    refs: list[str] = []
    seen: set[str] = set()
    for passage in passages:
        ref = str(passage.get("canonical_ref") or "").strip()
        if not ref or ref in seen:
            continue
        refs.append(ref)
        seen.add(ref)
        if len(refs) >= limit:
            break
    return refs


def _languages(passages: list[dict[str, Any]], work_language: str | None) -> list[str]:
    values = {str(passage.get("language")).strip() for passage in passages if passage.get("language")}
    if work_language:
        values.add(str(work_language).strip())
    return sorted(value for value in values if value)


def _abstract_for_node(
    work: dict[str, Any],
    title: str,
    passages: list[dict[str, Any]],
) -> str:
    refs = _canonical_refs(passages, limit=2)
    sample = " ".join(
        str(passage.get("text_content") or "").strip()
        for passage in passages[:2]
    )
    sample = re.sub(r"\s+", " ", sample).strip()
    sample = sample[:220].rstrip()
    ref_part = f" Key refs: {', '.join(refs)}." if refs else ""
    sample_part = f" Sample: {sample}" if sample else ""
    return f"{work.get('author', 'Unknown')} - {title}.{ref_part}{sample_part}".strip()


def _make_tree_node(
    *,
    node_id: str,
    title: str,
    path: str,
    passages: list[dict[str, Any]],
    work: dict[str, Any],
    children: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    children = children or []
    start_passage = passages[0]["sequence_number"] if passages else 0
    end_passage = passages[-1]["sequence_number"] if passages else 0
    refs = _canonical_refs(passages)
    abstract = _abstract_for_node(work, title, passages)
    languages = _languages(passages, work.get("language"))
    summary = f"{len(passages)} passages"
    if children:
        summary += f" across {len(children)} subsection(s)"
    text_sample = " ".join(str(p.get("text_content") or "") for p in passages[:2])
    return {
        "node_id": node_id,
        "title": title,
        "start_passage": start_passage,
        "end_passage": end_passage,
        "summary": summary,
        "path": path,
        "canonical_refs": refs,
        "abstract": abstract,
        "concept_tags": [],
        "entity_tags": [],
        "languages": languages,
        "translation_available": "en" in languages,
        "quote_density": round(len(refs) / max(1, len(passages)), 3),
        "token_estimate": _estimate_tokens(text_sample or abstract),
        "nodes": children,
    }


def build_tree_for_work(
    work: dict[str, Any],
    passages: list[dict[str, Any]],
) -> dict[str, Any]:
    if not passages:
        return _make_tree_node(
            node_id=f"work_{work['work_id']}",
            title=work["title"],
            path=work["title"],
            passages=[],
            work=work,
        )

    passages = sorted(passages, key=lambda item: item["sequence_number"])
    by_book: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for passage in passages:
        book, _, _ = _parse_ref(str(passage.get("canonical_ref") or ""))
        by_book[book or "main"].append(passage)

    book_nodes: list[dict[str, Any]] = []
    for book_label, book_passages in sorted(by_book.items()):
        by_chapter: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for passage in book_passages:
            _, chapter, _ = _parse_ref(str(passage.get("canonical_ref") or ""))
            by_chapter[chapter or "main"].append(passage)

        chapter_nodes: list[dict[str, Any]] = []
        book_title = f"Book {book_label}" if book_label != "main" else work["title"]
        book_path = book_title
        for chapter_label, chapter_passages in sorted(by_chapter.items()):
            chapter_title = (
                f"{book_title}, Chapter {chapter_label}"
                if chapter_label != "main"
                else book_title
            )
            chapter_path = chapter_title
            chapter_nodes.append(
                _make_tree_node(
                    node_id=f"book_{book_label}_ch_{chapter_label}",
                    title=chapter_title,
                    path=chapter_path,
                    passages=chapter_passages,
                    work=work,
                )
            )

        book_nodes.append(
            _make_tree_node(
                node_id=f"book_{book_label}",
                title=book_title,
                path=book_path,
                passages=book_passages,
                work=work,
                children=chapter_nodes,
            )
        )

    return _make_tree_node(
        node_id=f"work_{work['work_id']}",
        title=work["title"],
        path=work["title"],
        passages=passages,
        work=work,
        children=book_nodes,
    )


async def _fetch_works(conn: Any, schema: str) -> list[dict[str, Any]]:
    rows = await conn.fetch(
        f"""
        SELECT work_id, title, author, period, language
        FROM {schema}.ancient_works
        ORDER BY author, title
        """
    )
    return [dict(row) for row in rows]


async def _fetch_passages_for_work(
    conn: Any,
    schema: str,
    work_id: Any,
) -> list[dict[str, Any]]:
    rows = await conn.fetch(
        f"""
        SELECT passage_id, canonical_ref, sequence_number, text_content
        FROM {schema}.passages
        WHERE work_id = $1
        ORDER BY sequence_number
        """,
        work_id,
    )
    return [dict(row) for row in rows]


async def _upsert_index(
    conn: Any,
    schema: str,
    work: dict[str, Any],
    work_index: dict[str, Any],
    total_passages: int,
    dry_run: bool,
) -> None:
    if dry_run:
        logger.info(
            "[DRY RUN] Would upsert tree index for %s (%s) - %d passages",
            work["title"],
            work.get("author", "?"),
            total_passages,
        )
        return

    await conn.execute(
        f"""
        INSERT INTO {schema}.work_tree_indices
            (work_id, title, author, period, total_passages, tree_json)
        VALUES ($1, $2, $3, $4, $5, $6::jsonb)
        ON CONFLICT (work_id) DO UPDATE SET
            title = EXCLUDED.title,
            author = EXCLUDED.author,
            period = EXCLUDED.period,
            total_passages = EXCLUDED.total_passages,
            tree_json = EXCLUDED.tree_json,
            updated_at = now()
        """,
        str(work["work_id"]),
        work["title"],
        work.get("author", "Unknown"),
        work.get("period"),
        total_passages,
        json.dumps(work_index, ensure_ascii=False),
    )


async def main(schema: str, dry_run: bool) -> None:
    import asyncpg

    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        logger.error("DATABASE_URL environment variable is required")
        sys.exit(1)

    conn = await asyncpg.connect(database_url, statement_cache_size=0)
    try:
        works = await _fetch_works(conn, schema)
        logger.info("Found %d works to index", len(works))

        success = 0
        skipped = 0
        for work in works:
            passages = await _fetch_passages_for_work(conn, schema, work["work_id"])
            if not passages:
                skipped += 1
                continue

            for passage in passages:
                passage["language"] = work.get("language")

            tree = build_tree_for_work(work, passages)
            work_index = {
                "work_id": str(work["work_id"]),
                "title": work["title"],
                "author": work.get("author", "Unknown"),
                "period": work.get("period"),
                "total_passages": len(passages),
                "nodes": tree["nodes"],
            }
            await _upsert_index(conn, schema, work, work_index, len(passages), dry_run)
            success += 1
            logger.info(
                "Indexed %s (%s) - %d passages, %d top sections",
                work["title"],
                work.get("author", "?"),
                len(passages),
                len(work_index["nodes"]),
            )

        logger.info("Done. Indexed=%d skipped=%d dry_run=%s", success, skipped, dry_run)
    finally:
        await conn.close()


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--schema",
        default="free_will",
        help="PostgreSQL schema name (default: free_will)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned writes without persisting anything",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    asyncio.run(main(schema=args.schema, dry_run=args.dry_run))
