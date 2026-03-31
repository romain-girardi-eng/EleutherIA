#!/usr/bin/env python3
"""Backfill passage_citations for nodes flagged needs_evidence.

Uses three strategies to find ACTUAL matching passages — never fabricates links:
1. KG edge traversal: follow existing edges to passage nodes with passage_id
2. Greek/Latin term search: extract ancient-language terms from descriptions, search text
3. Work-scoped search: identify referenced works, search passages within them

All links use conservative confidence (0.5) and are logged for audit.
"""

import asyncio
import os
import re
import sys
import unicodedata
from collections import defaultdict
from typing import NamedTuple

import asyncpg

DATABASE_URL = os.environ["DATABASE_URL"]
SCHEMA = "free_will"
DRY_RUN = "--dry-run" in sys.argv
MIN_TERM_MATCHES = 2  # require at least 2 terms to match
CONFIDENCE = 0.5
CITATION_TYPE = "auto_backfill"
MAX_PASSAGES_PER_NODE = 5  # cap to avoid noise


class Citation(NamedTuple):
    passage_id: str
    kg_node_id: str
    strategy: str


# ── Greek/Latin term extraction ──────────────────────────────────────────

GREEK_RE = re.compile(r"[\u0370-\u03FF\u1F00-\u1FFF]{3,}")
# Latin philosophical terms (stems) commonly found in ancient texts
LATIN_STEMS = [
    "liberum arbitrium",
    "libero arbitrio",
    "liberi arbitrii",
    "fatum",
    "fato",
    "fati",
    "providentia",
    "voluntas",
    "voluntat",
    "necessitas",
    "necessitat",
    "praedestinatio",
    "praescientia",
    "peccatum",
    "gratia",
    "natura",
    "anima",
    "consilium",
]

ENGLISH_STOPWORDS = {
    "that", "this", "with", "from", "have", "been", "were", "they",
    "their", "which", "would", "could", "should", "about", "into",
    "also", "than", "then", "when", "what", "more", "some", "only",
    "very", "most", "such", "each", "both", "does", "many", "much",
    "just", "over", "other", "after", "being", "those", "these",
    "will", "make", "like", "time", "well", "made", "come", "long",
    "first", "between", "against", "through", "before", "under",
    "must", "however", "because", "since", "while", "where",
    "argument", "argues", "argued", "theory", "structure",
    "modern", "scholars", "characterized", "term", "terms",
}


def extract_greek_terms(text: str) -> list[str]:
    """Extract Greek words >= 3 chars from text."""
    return list(set(GREEK_RE.findall(text)))


def extract_latin_terms(text: str) -> list[str]:
    """Extract known Latin philosophical terms from text."""
    found = []
    lower = text.lower()
    for stem in LATIN_STEMS:
        if stem in lower:
            found.append(stem)
    return found


def extract_search_terms(label: str, description: str) -> dict[str, list[str]]:
    """Extract searchable terms from a KG node.

    Returns dict with keys 'greek', 'latin', 'english_key'.
    """
    full_text = f"{label} {description}"
    greek = extract_greek_terms(full_text)
    latin = extract_latin_terms(full_text)
    return {"greek": greek, "latin": latin}


def normalize_greek(text: str) -> str:
    """Strip diacritics for fuzzy matching."""
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c)).lower()


# ── Work reference extraction ─────────────────────────────────────────

# Patterns like "De Fato 42", "Contra Celsum II.20", "1 Apol. 43"
WORK_REF_PATTERNS = [
    (r"De Fato\b", "de fato"),
    (r"De Principiis\b", "de principiis"),
    (r"Contra Celsum\b", "contra celsum"),
    (r"De Libero Arbitrio\b", "de libero arbitrio"),
    (r"De Consolatione\b", "de consolatione"),
    (r"Consolation\b", "de consolatione"),
    (r"Adversus Marcionem\b", "adversus marcionem"),
    (r"Adv\.\s*Marc\.?\b", "adversus marcionem"),
    (r"De Anima\b", "de anima"),
    (r"De Civitate Dei\b", "de civitate dei"),
    (r"Com\.\s*Rm\b", "commentarii in epistulam"),
    (r"Commentary on Romans\b", "commentarii in epistulam"),
    (r"Adversus Haereses\b", "adversus haereses"),
    (r"Stromata\b", "stromata"),
    (r"Oratio\b", "oratio"),
    (r"De Oratione\b", "de oratione"),
    (r"Enchiridion\b", "enchiridion"),
    (r"Dissertationes\b", "dissertationes"),
    (r"Discourses\b", "dissertationes"),
    (r"Meditations\b", "meditations"),
    (r"De Rerum Natura\b", "de rerum natura"),
    (r"De Natura Deorum\b", "de natura deorum"),
    (r"1\s*Apol", "apologia"),
    (r"2\s*Apol", "apologia"),
    (r"Dialogue\s+(with\s+)?Trypho", "dialogue"),
    (r"Nicomachean Ethics\b", "nicomachean"),
    (r"De Interpretatione\b", "de interpretatione"),
    (r"Republic\b", "republic"),
    (r"Laws\b", "laws"),
    (r"Timaeus\b", "timaeus"),
    (r"Phaedrus\b", "phaedrus"),
    (r"Letter to Menoeceus\b", "menoeceus"),
    (r"Letter to Herodotus\b", "herodotus"),
    (r"Philocalia\b", "philocalia"),
    (r"De Hom\.\s*Opif", "hominis opificio"),
    (r"Hexaemeron\b", "hexaemeron"),
    (r"Vita Plotini\b", "vita plotini"),
]


def extract_work_refs(text: str) -> list[str]:
    """Extract work title fragments for matching against ancient_works."""
    refs = []
    for pattern, key in WORK_REF_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            refs.append(key)
    return list(set(refs))


# ── Main script ──────────────────────────────────────────────────────

async def main() -> None:
    conn = await asyncpg.connect(dsn=DATABASE_URL, statement_cache_size=0)

    # 1. Load all needs_evidence nodes
    ne_nodes = await conn.fetch(f"""
        SELECT node_id, label, type, description, metadata
        FROM {SCHEMA}.kg_nodes
        WHERE metadata->>'needs_evidence' = 'true'
    """)
    print(f"Loaded {len(ne_nodes)} needs_evidence nodes")

    # 2. Load work lookup (title -> work_id)
    works = await conn.fetch(f"""
        SELECT work_id, title, author FROM {SCHEMA}.ancient_works
    """)
    work_lookup: dict[str, list[str]] = {}  # lowercase fragment -> [work_id]
    for w in works:
        title_lower = (w["title"] or "").lower()
        for _, key in WORK_REF_PATTERNS:
            if key in title_lower:
                work_lookup.setdefault(key, []).append(str(w["work_id"]))

    # 3. Load existing passage_citations to avoid duplicates
    existing = await conn.fetch(f"""
        SELECT passage_id, kg_node_id FROM {SCHEMA}.passage_citations
    """)
    existing_set = {(str(r["passage_id"]), r["kg_node_id"]) for r in existing}
    print(f"Existing citations: {len(existing_set)}")

    # 4. Collect citations from all strategies
    all_citations: list[Citation] = []
    nodes_with_citations: set[str] = set()
    strategy_stats: dict[str, int] = defaultdict(int)

    # ── Strategy 1: KG edge traversal ──
    print("\n--- Strategy 1: KG edge traversal ---")
    edge_citations = await conn.fetch(f"""
        SELECT DISTINCT kn.node_id as ne_id, p_kn.metadata->>'passage_id' as pid
        FROM {SCHEMA}.kg_nodes kn
        JOIN {SCHEMA}.kg_edges e ON (e.source_id = kn.node_id OR e.target_id = kn.node_id)
        JOIN {SCHEMA}.kg_nodes p_kn ON (
            p_kn.node_id = CASE
                WHEN e.source_id = kn.node_id THEN e.target_id
                ELSE e.source_id
            END
        )
        WHERE kn.metadata->>'needs_evidence' = 'true'
        AND p_kn.type = 'passage'
        AND p_kn.metadata->>'passage_id' IS NOT NULL
    """)
    for row in edge_citations:
        pid = row["pid"]
        nid = row["ne_id"]
        if (pid, nid) not in existing_set:
            all_citations.append(Citation(pid, nid, "kg_edge"))
            nodes_with_citations.add(nid)
            strategy_stats["kg_edge"] += 1
    print(f"  Found {strategy_stats['kg_edge']} citations via KG edges")

    # ── Strategy 2: Greek/Latin term search in passage text ──
    print("\n--- Strategy 2: Greek/Latin term search ---")
    for node in ne_nodes:
        nid = node["node_id"]
        label = node["label"] or ""
        desc = node["description"] or ""
        terms = extract_search_terms(label, desc)

        greek_terms = terms["greek"]
        latin_terms = terms["latin"]

        if not greek_terms and not latin_terms:
            continue

        # Build search queries for Greek terms (use ILIKE with stems)
        matching_pids: dict[str, int] = {}  # passage_id -> match_count

        for gterm in greek_terms:
            # Use first 4+ chars as stem for fuzzy matching
            stem = gterm[:min(len(gterm), 6)]
            if len(stem) < 3:
                continue
            try:
                rows = await conn.fetch(f"""
                    SELECT passage_id FROM {SCHEMA}.passages
                    WHERE text_content ILIKE $1
                    LIMIT 50
                """, f"%{stem}%")
                for r in rows:
                    pid = str(r["passage_id"])
                    matching_pids[pid] = matching_pids.get(pid, 0) + 1
            except Exception:
                continue

        for lterm in latin_terms:
            try:
                rows = await conn.fetch(f"""
                    SELECT passage_id FROM {SCHEMA}.passages
                    WHERE text_content ILIKE $1
                    LIMIT 50
                """, f"%{lterm}%")
                for r in rows:
                    pid = str(r["passage_id"])
                    matching_pids[pid] = matching_pids.get(pid, 0) + 1
            except Exception:
                continue

        # Only keep passages matching >= MIN_TERM_MATCHES terms
        good_pids = [
            (pid, cnt)
            for pid, cnt in matching_pids.items()
            if cnt >= MIN_TERM_MATCHES
        ]
        # Sort by match count descending, cap at MAX
        good_pids.sort(key=lambda x: -x[1])
        good_pids = good_pids[:MAX_PASSAGES_PER_NODE]

        for pid, _cnt in good_pids:
            if (pid, nid) not in existing_set:
                already_added = any(
                    c.passage_id == pid and c.kg_node_id == nid
                    for c in all_citations
                )
                if not already_added:
                    all_citations.append(Citation(pid, nid, "term_search"))
                    nodes_with_citations.add(nid)
                    strategy_stats["term_search"] += 1

    print(f"  Found {strategy_stats['term_search']} citations via term search")

    # ── Strategy 3: Work-scoped search ──
    print("\n--- Strategy 3: Work-scoped search ---")
    for node in ne_nodes:
        nid = node["node_id"]
        label = node["label"] or ""
        desc = node["description"] or ""
        full = f"{label} {desc}"

        work_refs = extract_work_refs(full)
        if not work_refs:
            continue

        # Get work_ids for referenced works
        target_work_ids: list[str] = []
        for ref in work_refs:
            if ref in work_lookup:
                target_work_ids.extend(work_lookup[ref])

        if not target_work_ids:
            continue

        # Extract Greek terms for this node
        greek_terms = extract_greek_terms(full)
        if not greek_terms:
            continue

        # Search within those specific works
        matching_pids: dict[str, int] = {}
        for gterm in greek_terms:
            stem = gterm[:min(len(gterm), 5)]
            if len(stem) < 3:
                continue
            for wid in target_work_ids:
                try:
                    rows = await conn.fetch(f"""
                        SELECT passage_id FROM {SCHEMA}.passages
                        WHERE work_id = $1::uuid
                        AND text_content ILIKE $2
                        LIMIT 20
                    """, wid, f"%{stem}%")
                    for r in rows:
                        pid = str(r["passage_id"])
                        matching_pids[pid] = matching_pids.get(pid, 0) + 1
                except Exception:
                    continue

        # For work-scoped, a single term match is enough (the work context
        # already narrows scope significantly)
        good_pids = [
            (pid, cnt)
            for pid, cnt in matching_pids.items()
            if cnt >= 1
        ]
        good_pids.sort(key=lambda x: -x[1])
        good_pids = good_pids[:MAX_PASSAGES_PER_NODE]

        for pid, _cnt in good_pids:
            if (pid, nid) not in existing_set:
                already_added = any(
                    c.passage_id == pid and c.kg_node_id == nid
                    for c in all_citations
                )
                if not already_added:
                    all_citations.append(Citation(pid, nid, "work_scoped"))
                    nodes_with_citations.add(nid)
                    strategy_stats["work_scoped"] += 1

    print(f"  Found {strategy_stats['work_scoped']} citations via work-scoped search")

    # ── Deduplicate and summarize ──
    print(f"\n=== SUMMARY ===")
    print(f"Total citations to create: {len(all_citations)}")
    print(f"Nodes with new citations: {len(nodes_with_citations)}/{len(ne_nodes)}")
    print(f"Nodes still without citations: {len(ne_nodes) - len(nodes_with_citations)}")
    print(f"By strategy: {dict(strategy_stats)}")

    # ── Log all citations ──
    print(f"\n--- Citation log ---")
    for c in all_citations:
        print(f"  [{c.strategy}] node={c.kg_node_id} -> passage={c.passage_id}")

    # ── Insert ──
    if DRY_RUN:
        print(f"\nDRY RUN: would insert {len(all_citations)} citations")
    else:
        if not all_citations:
            print("\nNo citations to insert.")
        else:
            inserted = 0
            for c in all_citations:
                try:
                    await conn.execute(f"""
                        INSERT INTO {SCHEMA}.passage_citations
                            (citation_id, passage_id, kg_node_id, citation_type, confidence, notes)
                        VALUES (
                            gen_random_uuid(),
                            $1::uuid,
                            $2,
                            $3,
                            $4,
                            $5
                        )
                        ON CONFLICT DO NOTHING
                    """, c.passage_id, c.kg_node_id, CITATION_TYPE, CONFIDENCE,
                        f"auto_backfill via {c.strategy}")
                    inserted += 1
                except Exception as e:
                    print(f"  ERROR inserting {c}: {e}")
            print(f"\nInserted {inserted} passage_citations")

    # ── Verification ──
    final_count = await conn.fetchval(f"""
        SELECT count(*) FROM {SCHEMA}.passage_citations
        WHERE citation_type = '{CITATION_TYPE}'
    """)
    print(f"Total auto_backfill citations in DB: {final_count}")

    still_without = await conn.fetchval(f"""
        SELECT count(*) FROM {SCHEMA}.kg_nodes kn
        WHERE kn.metadata->>'needs_evidence' = 'true'
        AND NOT EXISTS (
            SELECT 1 FROM {SCHEMA}.passage_citations pc
            WHERE pc.kg_node_id = kn.node_id
        )
    """)
    print(f"Nodes still without ANY citation: {still_without}")

    await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
