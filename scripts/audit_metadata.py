#!/usr/bin/env python3
"""
Audit knowledge graph and PostgreSQL metadata for the Ancient Free Will Database.

The report surfaces:
  • Duplicate works (by normalized title and author combinations)
  • Missing or ambiguous author information
  • Knowledge-graph / relational mismatches on KG work identifiers

Usage examples:
  python3 scripts/audit_metadata.py
  python3 scripts/audit_metadata.py --kg-path ./ancient_free_will_database.json
  POSTGRES_HOST=... POSTGRES_DB=... python3 scripts/audit_metadata.py --pg
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

logger = None  # Lazy initialisation


# ---------- Helpers ----------

def setup_logging() -> None:
    """Defer logging configuration until script execution."""
    import logging

    global logger
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    logger = logging.getLogger("audit_metadata")


def normalize(value: Optional[str]) -> Optional[str]:
    """Normalize strings for duplicate detection."""
    if not value:
        return None
    value = value.lower()
    value = value.replace("–", "-")  # En dash → hyphen
    value = re.sub(r"\s+", " ", value)
    value = re.sub(r"[^a-z0-9\s]", "", value)
    return value.strip() or None


UNCERTAIN_TOKENS = (
    "uncertain",
    "possibly",
    "probable",
    "prob.",
    "disputed",
    "?",
    "pseudo-",
)

SUSPICIOUS_SCHOLARSHIP_TOKENS = (
    "academia.edu",
    "wikipedia",
    "blog",
    "blogspot",
    "wordpress",
    "medium.com",
    "substack",
    "youtube",
    "podcast",
    "lecture notes",
    "slideshare",
    "quora",
    "stackexchange",
    "wordpress",
    "patheos",
    "desiringgod.org",
    "gotquestions.org",
    "britannica.com",
)


# ---------- Knowledge Graph Audit ----------

def audit_knowledge_graph(kg_path: Path) -> Dict[str, Any]:
    """Inspect work nodes in the KG for duplicate titles and weak metadata."""
    if not kg_path.exists():
        raise FileNotFoundError(f"Knowledge graph file not found: {kg_path}")

    logger.info("Loading knowledge graph from %s", kg_path)
    data = json.loads(kg_path.read_text(encoding="utf-8"))
    nodes: List[Dict[str, Any]] = data.get("nodes", [])
    works = [node for node in nodes if node.get("type") == "work"]
    logger.info("Found %d nodes (%d works) in the KG", len(nodes), len(works))

    duplicates: Dict[Tuple[Optional[str], Optional[str]], List[Dict[str, Any]]] = defaultdict(list)
    title_collisions: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    missing_author: List[Dict[str, Any]] = []
    uncertain_author: List[Dict[str, Any]] = []
    works_missing_doi: List[Dict[str, Any]] = []

    suspicious_citations: List[Dict[str, Any]] = []

    for work in works:
        label: str = work.get("label", "")
        author: Optional[str] = work.get("author")
        # Normalized key for duplicates by title+author
        norm_title = normalize(label.split(" - ")[0])
        norm_author = normalize(author)
        duplicates[(norm_title, norm_author)].append(work)
        title_collisions[norm_title].append(work)

        if not author:
            missing_author.append(work)
        elif any(token in author.lower() for token in UNCERTAIN_TOKENS):
            uncertain_author.append(work)

        if not work.get("doi"):
            works_missing_doi.append(
                {
                    "label": label,
                    "author": author,
                    "id": work.get("id"),
                }
            )

    # Scan all nodes for modern scholarship issues
    for node in nodes:
        for entry in node.get("modern_scholarship", []) or []:
            entry_lower = entry.lower()
            if any(token in entry_lower for token in SUSPICIOUS_SCHOLARSHIP_TOKENS):
                suspicious_citations.append(
                    {
                        "node_id": node.get("id"),
                        "node_label": node.get("label"),
                        "citation": entry,
                    }
                )

    duplicate_groups = [
        {
            "title": key[0],
            "author": key[1],
            "count": len(items),
            "labels": [item.get("label") for item in items],
        }
        for key, items in duplicates.items()
        if key[0] and len(items) > 1
    ]

    title_groups = [
        {
            "title": key,
            "count": len(items),
            "labels": [item.get("label") for item in items],
            "authors": list({item.get("author") for item in items}),
        }
        for key, items in title_collisions.items()
        if key and len(items) > 1
    ]

    report = {
        "totals": {
            "works": len(works),
            "missing_author": len(missing_author),
            "uncertain_author": len(uncertain_author),
            "duplicate_title_author": len(duplicate_groups),
            "title_collisions": len(title_groups),
            "missing_doi": len(works_missing_doi),
        },
        "duplicate_title_author_groups": duplicate_groups,
        "title_collision_groups": title_groups,
        "missing_author_labels": [work.get("label") for work in missing_author],
        "uncertain_author_labels": [
            {"label": work.get("label"), "author": work.get("author")} for work in uncertain_author
        ],
        "suspicious_citations": suspicious_citations,
        "works_missing_doi": works_missing_doi,
    }

    logger.info(
        "KG audit complete: %d missing authors, %d uncertain authors, %d duplicate (title+author) groups",
        report["totals"]["missing_author"],
        report["totals"]["uncertain_author"],
        report["totals"]["duplicate_title_author"],
    )
    return report


# ---------- PostgreSQL Audit ----------

async def audit_postgres(config: Dict[str, Any]) -> Dict[str, Any]:
    """Connect to PostgreSQL and surface duplicate or ambiguous records."""
    try:
        import asyncpg
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise RuntimeError("asyncpg not installed; install requirements-dev.txt") from exc

    logger.info("Connecting to PostgreSQL at %s:%s", config.get("host"), config.get("port"))
    conn = await asyncpg.connect(**config)
    try:
        results: Dict[str, Any] = {}

        duplicate_query = """
            SELECT
                LOWER(REGEXP_REPLACE(title, '[^a-z0-9]+', '', 'g')) AS norm_title,
                LOWER(COALESCE(author, '')) AS norm_author,
                COUNT(*) AS occurrences,
                ARRAY_AGG(id::text ORDER BY created_at DESC) AS text_ids,
                ARRAY_AGG(title ORDER BY created_at DESC) AS titles,
                ARRAY_AGG(author ORDER BY created_at DESC) AS authors
            FROM free_will.texts
            GROUP BY 1, 2
            HAVING COUNT(*) > 1
            ORDER BY occurrences DESC;
        """
        duplicates = await conn.fetch(duplicate_query)
        results["duplicate_title_author"] = [dict(row) for row in duplicates]

        conflicting_authors_query = """
            WITH normalized AS (
                SELECT
                    LOWER(REGEXP_REPLACE(title, '[^a-z0-9]+', '', 'g')) AS norm_title,
                    ARRAY_AGG(DISTINCT author) FILTER (WHERE author IS NOT NULL) AS authors,
                    ARRAY_AGG(DISTINCT kg_work_id) FILTER (WHERE kg_work_id IS NOT NULL) AS kg_ids,
                    ARRAY_AGG(id::text ORDER BY created_at DESC) AS text_ids,
                    COUNT(*) AS occurrences
                FROM free_will.texts
                GROUP BY 1
            )
            SELECT *
            FROM normalized
            WHERE ARRAY_LENGTH(authors, 1) > 1
            ORDER BY occurrences DESC;
        """
        conflicting = await conn.fetch(conflicting_authors_query)
        results["conflicting_authors"] = [dict(row) for row in conflicting]

        missing_author_query = """
            SELECT id::text, title, author, kg_work_id
            FROM free_will.texts
            WHERE author IS NULL OR TRIM(author) = '' OR author ILIKE 'unknown%'
            ORDER BY title;
        """
        missing = await conn.fetch(missing_author_query)
        results["missing_authors"] = [dict(row) for row in missing]

        ambiguous_author_query = """
            SELECT id::text, title, author
            FROM free_will.texts
            WHERE author ~* '(uncertain|possibly|pseudo|\\?|prob\\.?|disputed)'
            ORDER BY title;
        """
        ambiguous = await conn.fetch(ambiguous_author_query)
        results["ambiguous_authors"] = [dict(row) for row in ambiguous]

        kg_dup_query = """
            SELECT kg_work_id, COUNT(*) AS occurrences,
                   ARRAY_AGG(id::text ORDER BY created_at DESC) AS text_ids,
                   ARRAY_AGG(title ORDER BY created_at DESC) AS titles
            FROM free_will.texts
            WHERE kg_work_id IS NOT NULL
            GROUP BY kg_work_id
            HAVING COUNT(*) > 1
            ORDER BY occurrences DESC;
        """
        kg_duplicates = await conn.fetch(kg_dup_query)
        results["duplicate_kg_work_id"] = [dict(row) for row in kg_duplicates]

        totals_query = """
            SELECT
                COUNT(*) AS total_texts,
                COUNT(*) FILTER (WHERE author IS NULL OR TRIM(author) = '' OR author ILIKE 'unknown%') AS missing_author,
                COUNT(*) FILTER (WHERE kg_work_id IS NULL) AS missing_kg_id
            FROM free_will.texts;
        """
        totals = await conn.fetchrow(totals_query)
        results["totals"] = dict(totals) if totals else {}

        logger.info(
            "PostgreSQL audit complete: %d duplicate (title+author) clusters, %d conflicting author clusters",
            len(results["duplicate_title_author"]),
            len(results["conflicting_authors"]),
        )
        return results
    finally:
        await conn.close()


# ---------- Reporting ----------

def print_section(title: str) -> None:
    print("\n" + title)
    print("-" * len(title))


def render_report(kg_report: Dict[str, Any], pg_report: Optional[Dict[str, Any]]) -> None:
    """Pretty-print the collected findings to stdout."""
    print_section("Knowledge Graph Findings")
    print(f"Total work nodes: {kg_report['totals']['works']}")
    print(f"Missing author metadata: {kg_report['totals']['missing_author']}")
    print(f"Uncertain author strings: {kg_report['totals']['uncertain_author']}")
    print(f"Duplicate (title+author) groups: {kg_report['totals']['duplicate_title_author']}")
    print(f"Title collisions (same work title, differing authors/labels): {kg_report['totals']['title_collisions']}")
    print(f"Suspicious modern scholarship entries: {len(kg_report.get('suspicious_citations', []))}")
    print(f"Works missing DOI: {len(kg_report.get('works_missing_doi', []))}")

    if kg_report["missing_author_labels"]:
        print("\nWorks missing authors:")
        for label in kg_report["missing_author_labels"]:
            print(f"  • {label}")

    if kg_report["uncertain_author_labels"]:
        print("\nWorks with uncertain authors:")
        for entry in kg_report["uncertain_author_labels"]:
            print(f"  • {entry['label']} — {entry['author']}")

    if kg_report["title_collision_groups"]:
        print("\nPotential title collisions:")
        for group in kg_report["title_collision_groups"]:
            print(f"  • {group['title']} ({group['count']} variants)")
            for label in group["labels"]:
                print(f"      - {label}")

    suspicious_citations = kg_report.get("suspicious_citations", [])
    if suspicious_citations:
        print("\nPotentially non-scholarly modern scholarship entries:")
        for item in suspicious_citations[:20]:
            print(f"  • {item['citation']}  — linked to {item['node_label']} ({item['node_id']})")
        if len(suspicious_citations) > 20:
            print(f"  ... {len(suspicious_citations) - 20} more")

    works_missing_doi = kg_report.get("works_missing_doi", [])
    if works_missing_doi:
        print("\nWorks lacking DOI metadata (set to blank):")
        for item in works_missing_doi[:20]:
            print(f"  • {item['label']} — {item['author']} ({item['id']})")
        if len(works_missing_doi) > 20:
            print(f"  ... {len(works_missing_doi) - 20} more")

    if pg_report is None:
        return

    print_section("PostgreSQL Findings")
    totals = pg_report.get("totals", {})
    if totals:
        print(
            f"Total texts: {totals.get('total_texts', 0)}; "
            f"missing author: {totals.get('missing_author', 0)}; "
            f"missing KG link: {totals.get('missing_kg_id', 0)}"
        )

    def _print_cluster(name: str, records: Iterable[Dict[str, Any]], limit: int = 10) -> None:
        records = list(records)
        print(f"\n{name}: {len(records)}")
        for idx, row in enumerate(records[:limit], start=1):
            print(f"  {idx}. occurrences={row.get('occurrences', len(row.get('titles', [])))}")
            if "norm_title" in row:
                print(f"     title key: {row['norm_title']}")
            if row.get("authors"):
                print(f"     authors: {row['authors']}")
            if row.get("titles"):
                sample_titles = row["titles"][:3]
                print(f"     sample titles: {sample_titles}")
            if row.get("kg_ids"):
                print(f"     kg ids: {row['kg_ids']}")
            if row.get("kg_work_id"):
                print(f"     kg_work_id: {row['kg_work_id']}")
            if row.get("text_ids"):
                print(f"     text ids: {row['text_ids'][:3]}")
        if len(records) > limit:
            print(f"  ... {len(records) - limit} more")

    _print_cluster("Duplicate title+author clusters", pg_report.get("duplicate_title_author", []))
    _print_cluster("Conflicting author clusters", pg_report.get("conflicting_authors", []))
    _print_cluster("Duplicate KG work IDs", pg_report.get("duplicate_kg_work_id", []))

    missing_authors = pg_report.get("missing_authors", [])
    print(f"\nTexts with missing author fields: {len(missing_authors)}")
    for item in missing_authors[:10]:
        print(f"  • {item['title']} (text_id={item['id']})")
    if len(missing_authors) > 10:
        print(f"  ... {len(missing_authors) - 10} more")

    ambiguous_authors = pg_report.get("ambiguous_authors", [])
    print(f"\nTexts with ambiguous author strings: {len(ambiguous_authors)}")
    for item in ambiguous_authors[:10]:
        print(f"  • {item['title']} — {item['author']} (text_id={item['id']})")
    if len(ambiguous_authors) > 10:
        print(f"  ... {len(ambiguous_authors) - 10} more")


# ---------- CLI ----------

def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit metadata quality for the Ancient Free Will Database.")
    parser.add_argument(
        "--kg-path",
        type=Path,
        default=Path("ancient_free_will_database.json"),
        help="Path to the knowledge graph JSON export.",
    )
    parser.add_argument(
        "--pg",
        action="store_true",
        help="Attempt to audit the PostgreSQL database using environment credentials.",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        help="Optional path to write the combined report as JSON.",
    )
    return parser.parse_args(argv)


def load_pg_config() -> Dict[str, Any]:
    """Read PostgreSQL credentials from environment variables."""
    env = os.environ
    return {
        "host": env.get("POSTGRES_HOST", "localhost"),
        "port": int(env.get("POSTGRES_PORT", 5432)),
        "database": env.get("POSTGRES_DB", "ancient_free_will_db"),
        "user": env.get("POSTGRES_USER", "free_will_user"),
        "password": env.get("POSTGRES_PASSWORD", ""),
    }


async def main(argv: Optional[List[str]] = None) -> int:
    setup_logging()
    args = parse_args(argv)

    try:
        kg_report = audit_knowledge_graph(args.kg_path)
    except Exception as exc:
        logger.error("Failed to audit knowledge graph: %s", exc)
        return 1

    pg_report: Optional[Dict[str, Any]] = None
    if args.pg:
        config = load_pg_config()
        try:
            pg_report = await audit_postgres(config)
        except Exception as exc:
            logger.error("PostgreSQL audit failed: %s", exc)

    render_report(kg_report, pg_report)

    if args.output_json:
        combined = {"knowledge_graph": kg_report, "postgres": pg_report}
        args.output_json.write_text(json.dumps(combined, indent=2, ensure_ascii=False))
        logger.info("Wrote JSON report to %s", args.output_json)

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(asyncio.run(main()))
    except KeyboardInterrupt:
        raise SystemExit(130)
