"""Work tree indexer service.

Pure, reusable logic extracted from `scripts/build_work_tree_indices.py`
so that both the standalone script and the Temporal `KGReindexWorkflow`
activities call into the same code.

No CLI concerns here — no argparse, no `sys.exit`, no print statements.
Connection management is left to the caller (the activity wrapper) so
the same code can run inside Temporal's thread executor without forcing
an asyncio dependency at the call site.

The functions are intentionally synchronous so the Temporal activity
can wrap them in `asyncio.to_thread` and stay consistent with the
existing psycopg2-based activity pattern used by the translation
pipeline.
"""

from __future__ import annotations

import json
import re
from collections import defaultdict
from typing import Any

SCHEMA = "free_will"


# ---------------------------------------------------------------------------
# Tree shape helpers (lifted from scripts/build_work_tree_indices.py)
# ---------------------------------------------------------------------------


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
    values = {
        str(passage.get("language")).strip()
        for passage in passages
        if passage.get("language")
    }
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
        str(passage.get("text_content") or "").strip() for passage in passages[:2]
    )
    sample = re.sub(r"\s+", " ", sample).strip()[:220].rstrip()
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
    """Build a hierarchical (book → chapter) tree for one work."""
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
        for chapter_label, chapter_passages in sorted(by_chapter.items()):
            chapter_title = (
                f"{book_title}, Chapter {chapter_label}"
                if chapter_label != "main"
                else book_title
            )
            chapter_nodes.append(
                _make_tree_node(
                    node_id=f"book_{book_label}_ch_{chapter_label}",
                    title=chapter_title,
                    path=chapter_title,
                    passages=chapter_passages,
                    work=work,
                )
            )

        book_nodes.append(
            _make_tree_node(
                node_id=f"book_{book_label}",
                title=book_title,
                path=book_title,
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


# ---------------------------------------------------------------------------
# Synchronous psycopg2 helpers used by Temporal activities
# ---------------------------------------------------------------------------


def list_works(conn: Any, work_ids: list[str] | None = None) -> list[dict[str, Any]]:
    """List works in scope. `None` = all works; otherwise filter by id."""
    cur = conn.cursor()
    cur.execute(f"SET search_path TO {SCHEMA}")
    if work_ids:
        cur.execute(
            """
            SELECT work_id::text, title, author, period, language
            FROM ancient_works
            WHERE work_id::text = ANY(%s)
            ORDER BY author, title
            """,
            (work_ids,),
        )
    else:
        cur.execute(
            """
            SELECT work_id::text, title, author, period, language
            FROM ancient_works
            ORDER BY author, title
            """
        )
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, row, strict=False)) for row in cur.fetchall()]


def list_works_to_reindex(
    conn: Any,
    work_ids: list[str] | None = None,
    force: bool = False,
) -> list[dict[str, Any]]:
    """Return works whose tree index is missing, stale, or `force=True`.

    A work is considered "stale" when there is no existing row in
    `work_tree_indices`, or when the latest passage row for the work has a
    timestamp newer than the index `updated_at`.
    """
    works = list_works(conn, work_ids)
    if force or not works:
        return works

    cur = conn.cursor()
    cur.execute(f"SET search_path TO {SCHEMA}")
    cur.execute("SELECT work_id, total_passages, updated_at FROM work_tree_indices")
    indexed: dict[str, tuple[int, Any]] = {
        str(r[0]): (int(r[1] or 0), r[2]) for r in cur.fetchall()
    }

    to_reindex: list[dict[str, Any]] = []
    for work in works:
        work_id = str(work["work_id"])
        if work_id not in indexed:
            to_reindex.append(work)
            continue
        recorded_count, updated_at = indexed[work_id]
        cur.execute(
            "SELECT COUNT(*) FROM passages WHERE work_id = %s",
            (work_id,),
        )
        current_count = int(cur.fetchone()[0])
        if current_count != recorded_count:
            to_reindex.append(work)
            continue
    return to_reindex


def fetch_passages_for_work(conn: Any, work_id: str) -> list[dict[str, Any]]:
    cur = conn.cursor()
    cur.execute(f"SET search_path TO {SCHEMA}")
    cur.execute(
        """
        SELECT passage_id::text, canonical_ref, sequence_number, text_content
        FROM passages
        WHERE work_id = %s
        ORDER BY sequence_number
        """,
        (work_id,),
    )
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, row, strict=False)) for row in cur.fetchall()]


def upsert_tree_index(
    conn: Any,
    work: dict[str, Any],
    work_index: dict[str, Any],
    total_passages: int,
) -> None:
    cur = conn.cursor()
    cur.execute(f"SET search_path TO {SCHEMA}")
    cur.execute(
        """
        INSERT INTO work_tree_indices
            (work_id, title, author, period, total_passages, tree_json)
        VALUES (%s, %s, %s, %s, %s, %s::jsonb)
        ON CONFLICT (work_id) DO UPDATE SET
            title = EXCLUDED.title,
            author = EXCLUDED.author,
            period = EXCLUDED.period,
            total_passages = EXCLUDED.total_passages,
            tree_json = EXCLUDED.tree_json,
            updated_at = now()
        """,
        (
            str(work["work_id"]),
            work["title"],
            work.get("author", "Unknown"),
            work.get("period"),
            total_passages,
            json.dumps(work_index, ensure_ascii=False),
        ),
    )


def reindex_one_work(conn: Any, work_id: str) -> tuple[int, bool]:
    """Recompute and upsert the tree index for a single work.

    Returns `(passage_count, was_indexed)`. `was_indexed=False` means the
    work has no passages and was skipped.
    """
    works = list_works(conn, [work_id])
    if not works:
        return 0, False
    work = works[0]

    passages = fetch_passages_for_work(conn, work_id)
    if not passages:
        return 0, False

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
    upsert_tree_index(conn, work, work_index, len(passages))
    return len(passages), True


__all__ = [
    "SCHEMA",
    "build_tree_for_work",
    "list_works",
    "list_works_to_reindex",
    "fetch_passages_for_work",
    "upsert_tree_index",
    "reindex_one_work",
]
