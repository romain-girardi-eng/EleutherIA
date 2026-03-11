#!/usr/bin/env python3
"""
Batch 04: Programmatic provenance repair for ALL remaining unsupported claim-bearing nodes.

Strategy (in priority order):
1. HAS_WORK_EDGE  — node already connected to a work → add source_for FROM work
2. HAS_PUB_EDGE   — node already connected to a publication → add source_for FROM pub
3. HAS_PERSON      — node connected to a person who has known works →
                     match metadata.source_work to person's works if possible,
                     else use the person's single unambiguous work
4. HAS_META_ONLY  — metadata references a source but no person/work edge →
                     try to find the referenced work/pub in KG
5. ISOLATED        — no connections → flag for manual review

What this script does NOT do:
- Generate or fabricate any ancient text
- Invent passage IDs or citation references
- Create new nodes (only adds edges and metadata patches)
- Guess at source attributions

Usage:
    set -a; source .env; set +a
    uv run --directory database python database/scripts/apply_manual_review_batch_04.py
    uv run --directory database python database/scripts/apply_manual_review_batch_04.py --confirm
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import asyncpg

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = "free_will"
RUN_TAG = "kg_provenance_batch_04_2026_03_10"
REPORT_JSON = ROOT / "docs" / "reports" / "2026-03-10-kg-provenance-batch-04-results.json"
REPORT_MD = ROOT / "docs" / "reports" / "2026-03-10-kg-provenance-batch-04-results.md"

# Types valid as source_for targets (must match ontology)
SOURCE_FOR_TARGET_TYPES = {
    "argument", "argument_framework", "concept", "conceptual_evolution",
    "controversy", "debate", "group", "publication", "quote", "school",
    "synthesis", "work",
}

CLAIM_TYPES = [
    "argument", "concept", "quote", "synthesis", "debate",
    "controversy", "school", "conceptual_evolution", "group",
]


@dataclass
class ProvenanceFix:
    node_id: str
    node_type: str
    node_label: str
    category: str  # HAS_WORK_EDGE, HAS_PUB_EDGE, HAS_PERSON, HAS_META_ONLY, ISOLATED
    source_id: str | None = None
    source_label: str | None = None
    source_type: str | None = None  # work or publication
    relation: str = "source_for"
    match_reason: str = ""
    metadata_patch: dict[str, Any] = field(default_factory=dict)
    flagged_manual: bool = False


def normalize_title(s: str) -> str:
    """Normalize a title for fuzzy matching."""
    s = s.lower().strip()
    s = re.sub(r"[^\w\s]", "", s)
    s = re.sub(r"\s+", " ", s)
    # Remove common prefixes
    for prefix in ["on ", "the ", "a ", "an "]:
        if s.startswith(prefix):
            s = s[len(prefix):]
    return s


def extract_work_references(text: str) -> list[str]:
    """Extract potential work title references from a text field.

    Handles patterns like:
    - "Confessiones VIII.8-10"  → "Confessiones"
    - "De Gratia et Libero Arbitrio (426-427); De Correptione..."  → each title
    - "Epictetus, Discourses I.1, I.17"  → "Discourses"
    """
    refs: list[str] = []
    if not text:
        return refs

    # Split on semicolons for multi-source references
    parts = re.split(r";\s*", text)
    for part in parts:
        part = part.strip()
        if not part:
            continue
        # Remove author prefix "Author, " or "Author's "
        part = re.sub(r"^[A-Z][a-z]+(?:\s+[a-z]+)?\s*,\s*", "", part)
        part = re.sub(r"^[A-Z][a-z]+'s\s+", "", part)
        # Remove trailing reference numbers like "VIII.8-10", "I.1", etc.
        part = re.sub(r"\s+[IVXLCDM]+(?:\.\d+(?:-\d+)?)?(?:,\s*[IVXLCDM]+(?:\.\d+)?)*\s*$", "", part)
        # Remove trailing parenthetical dates
        part = re.sub(r"\s*\([^)]*\d{3,4}[^)]*\)\s*$", "", part)
        # Remove trailing "Book N" references
        part = re.sub(r"\s+Book\s+\d+\s*$", "", part, flags=re.IGNORECASE)
        # Remove trailing section references
        part = re.sub(r"\s+\d+[\.\-]\d+.*$", "", part)
        part = part.strip()
        # Filter out catalogue numbers (SC 123, PG 45, etc.)
        if re.match(r"^(SC|PG|PL|CSEL|GCS|CCL)\b", part, re.IGNORECASE):
            continue
        if len(part) > 3:
            refs.append(part)
    return refs


def extract_label_work_ref(label: str) -> str | None:
    """Extract work reference from node label parenthetical.

    E.g. "Augustine's Two Wills Argument (Confessions VIII)" → "Confessions"
    """
    m = re.search(r"\(([^)]+)\)\s*$", label)
    if m:
        ref = m.group(1)
        # Remove section numbers
        ref = re.sub(r"\s+[IVXLCDM]+(?:\.\d+(?:-\d+)?)*\s*$", "", ref)
        ref = re.sub(r"\s+\d+[\.\-]\d+.*$", "", ref)
        ref = ref.strip()
        if len(ref) > 3 and not re.match(r"^\d+", ref):
            return ref
    return None


def try_match_work(
    candidate: str, works: list[dict], strict: bool = False
) -> dict | None:
    """Try to match a candidate string against a list of works.

    If strict=True, only allow exact matches (no substring).
    """
    cand_norm = normalize_title(candidate)
    if len(cand_norm) < 3:
        return None

    # Exact match
    for w in works:
        if normalize_title(w["label"]) == cand_norm:
            return w

    if strict:
        return None

    # Substring match — require at least 15 chars and bidirectional length check
    # to avoid "De Anima" matching "De Anima et Corpore" by wrong author
    for w in works:
        w_norm = normalize_title(w["label"])
        if len(cand_norm) >= 15 and cand_norm in w_norm:
            return w
        if len(w_norm) >= 15 and w_norm in cand_norm:
            return w

    # Word overlap: if >70% of candidate words (min 3) appear in work label
    cand_words = set(cand_norm.split())
    if len(cand_words) >= 3:
        for w in works:
            w_words = set(normalize_title(w["label"]).split())
            overlap = len(cand_words & w_words)
            if overlap >= len(cand_words) * 0.7 and overlap >= 3:
                return w

    return None


def match_metadata_to_work(
    metadata: dict,
    node_label: str,
    person_works: list[dict],
    all_works: dict[str, dict],
    node_description: str = "",  # noqa: ARG001
    strict: bool = False,
) -> tuple[str, str, str] | None:
    """Try to match metadata/label/description references to a known work.
    Returns (work_id, work_label, match_reason) or None.

    If strict=True, only allow exact matches (no substring/word-overlap).
    """
    all_works_list = [{"id": k, "label": v["label"], "type": v["type"]} for k, v in all_works.items()]

    # 1. Try source_work field
    source_work = metadata.get("source_work", "")
    if source_work:
        m = (try_match_work(source_work, person_works, strict=strict)
             or try_match_work(source_work, all_works_list, strict=strict))
        if m:
            return (m["id"], m["label"], f"metadata source_work match: {source_work}")

    # 2. Try primary_source field (may contain multiple refs)
    primary = metadata.get("primary_source", "")
    if primary:
        refs = extract_work_references(primary)
        for ref in refs:
            m = (try_match_work(ref, person_works, strict=strict)
                 or try_match_work(ref, all_works_list, strict=strict))
            if m:
                return (m["id"], m["label"], f"primary_source match: {ref}")

    # 3. Try ancient_sources list — only against person_works (not global)
    #    to avoid matching the wrong author's work with a similar title
    if person_works:
        for src in metadata.get("ancient_sources", []):
            if isinstance(src, str):
                refs = extract_work_references(src)
                for ref in refs:
                    m = try_match_work(ref, person_works, strict=strict)
                    if m:
                        return (m["id"], m["label"], f"ancient_sources match: {ref}")

    # 4. Try node label parenthetical — only if sufficiently specific (>= 15 chars)
    label_ref = extract_label_work_ref(node_label)
    if label_ref and len(label_ref) >= 15:
        m = try_match_work(label_ref, person_works) or try_match_work(label_ref, all_works_list)
        if m:
            return (m["id"], m["label"], f"label parenthetical match: {label_ref}")

    return None


async def get_unsupported_nodes(conn: asyncpg.Connection) -> list[dict]:
    """Get all unsupported claim-bearing nodes."""
    types_sql = ", ".join(f"'{t}'" for t in CLAIM_TYPES)
    rows = await conn.fetch(f"""
        WITH has_citation AS (
            SELECT DISTINCT kg_node_id FROM {SCHEMA}.passage_citations
        ),
        has_evidence_edge AS (
            SELECT DISTINCT target_id AS nid FROM {SCHEMA}.kg_edges
            WHERE relation IN ('evidenced_by','source_for','grounded_in')
            UNION
            SELECT DISTINCT source_id FROM {SCHEMA}.kg_edges
            WHERE relation IN ('evidenced_by','source_for','grounded_in')
        ),
        has_passage_edge AS (
            SELECT DISTINCT e.source_id AS nid FROM {SCHEMA}.kg_edges e
            JOIN {SCHEMA}.kg_nodes n ON n.node_id = e.target_id WHERE n.type = 'passage'
            UNION
            SELECT DISTINCT e.target_id FROM {SCHEMA}.kg_edges e
            JOIN {SCHEMA}.kg_nodes n ON n.node_id = e.source_id WHERE n.type = 'passage'
        )
        SELECT n.node_id, n.type, n.label, n.description, n.metadata
        FROM {SCHEMA}.kg_nodes n
        WHERE n.type IN ({types_sql})
          AND n.node_id NOT IN (SELECT kg_node_id FROM has_citation)
          AND n.node_id NOT IN (SELECT nid FROM has_evidence_edge)
          AND n.node_id NOT IN (SELECT nid FROM has_passage_edge)
        ORDER BY n.type, n.label
    """)
    nodes = []
    for r in rows:
        meta = r["metadata"]
        if meta and isinstance(meta, str):
            meta = json.loads(meta)
        elif meta:
            meta = dict(meta)
        else:
            meta = {}
        nodes.append({
            "node_id": r["node_id"],
            "type": r["type"],
            "label": r["label"],
            "description": r["description"] or "",
            "metadata": meta,
        })
    return nodes


async def get_node_connections(
    conn: asyncpg.Connection, node_id: str
) -> dict[str, list[dict]]:
    """Get works, publications, and persons connected to a node."""
    rows = await conn.fetch(f"""
        SELECT e.source_id, e.target_id, e.relation,
               n2.node_id as other_id, n2.type as other_type, n2.label as other_label
        FROM {SCHEMA}.kg_edges e
        JOIN {SCHEMA}.kg_nodes n2
          ON n2.node_id = CASE WHEN e.source_id = $1 THEN e.target_id ELSE e.source_id END
        WHERE e.source_id = $1 OR e.target_id = $1
    """, node_id)

    result: dict[str, list[dict]] = {"works": [], "pubs": [], "persons": []}
    for r in rows:
        item = {"id": r["other_id"], "label": r["other_label"], "rel": r["relation"]}
        if r["other_type"] == "work":
            result["works"].append(item)
        elif r["other_type"] == "publication":
            result["pubs"].append(item)
        elif r["other_type"] == "person":
            result["persons"].append(item)
    return result


async def get_person_works(
    conn: asyncpg.Connection, person_id: str
) -> list[dict]:
    """Get works and publications authored by a person.

    Respects edge direction:
    - wrote: person (source) → work (target)
    - authored_by: work (source) → person (target)
    - created_by: work (source) → person (target)
    """
    rows = await conn.fetch(f"""
        SELECT w.node_id, w.label, w.type
        FROM {SCHEMA}.kg_edges e
        JOIN {SCHEMA}.kg_nodes w ON w.node_id = e.target_id
        WHERE e.source_id = $1
          AND e.relation = 'wrote'
          AND w.type IN ('work', 'publication')
        UNION
        SELECT w.node_id, w.label, w.type
        FROM {SCHEMA}.kg_edges e
        JOIN {SCHEMA}.kg_nodes w ON w.node_id = e.source_id
        WHERE e.target_id = $1
          AND e.relation IN ('authored_by', 'created_by')
          AND w.type IN ('work', 'publication')
    """, person_id)
    return [{"id": r["node_id"], "label": r["label"], "type": r["type"]} for r in rows]


async def get_all_works(conn: asyncpg.Connection) -> dict[str, dict]:
    """Get all work and publication nodes for global matching."""
    rows = await conn.fetch(f"""
        SELECT node_id, label, type FROM {SCHEMA}.kg_nodes
        WHERE type IN ('work', 'publication')
    """)
    return {r["node_id"]: {"label": r["label"], "type": r["type"]} for r in rows}


async def check_edge_exists(
    conn: asyncpg.Connection, source_id: str, target_id: str, relation: str
) -> bool:
    row = await conn.fetchval(f"""
        SELECT 1 FROM {SCHEMA}.kg_edges
        WHERE source_id = $1 AND target_id = $2 AND relation = $3
    """, source_id, target_id, relation)
    return row is not None


async def build_fixes(conn: asyncpg.Connection) -> list[ProvenanceFix]:
    """Analyze all unsupported nodes and determine fixes."""
    nodes = await get_unsupported_nodes(conn)
    all_works = await get_all_works(conn)
    fixes: list[ProvenanceFix] = []

    for node in nodes:
        nid = node["node_id"]
        ntype = node["type"]
        meta = node["metadata"]

        conns = await get_node_connections(conn, nid)

        fix = ProvenanceFix(
            node_id=nid,
            node_type=ntype,
            node_label=node["label"],
            category="UNKNOWN",
        )

        # --- Priority 1: Direct work connection ---
        if conns["works"]:
            fix.category = "HAS_WORK_EDGE"
            # Pick the best work: prefer one matching metadata, else first
            best_work = conns["works"][0]
            if meta.get("source_work"):
                for w in conns["works"]:
                    if normalize_title(meta["source_work"]) in normalize_title(w["label"]):
                        best_work = w
                        break

            fix.source_id = best_work["id"]
            fix.source_label = best_work["label"]
            fix.source_type = "work"
            fix.match_reason = f"existing edge: {best_work['rel']}"

        # --- Priority 2: Direct publication connection ---
        elif conns["pubs"]:
            fix.category = "HAS_PUB_EDGE"
            best_pub = conns["pubs"][0]
            fix.source_id = best_pub["id"]
            fix.source_label = best_pub["label"]
            fix.source_type = "publication"
            fix.match_reason = f"existing edge: {best_pub['rel']}"

        # --- Priority 3: Person connection → find their works ---
        elif conns["persons"]:
            fix.category = "HAS_PERSON"
            # Collect all works from all connected persons
            all_person_works: list[dict] = []
            for p in conns["persons"]:
                pw = await get_person_works(conn, p["id"])
                all_person_works.extend(pw)

            if all_person_works:
                # Try metadata match first
                matched = match_metadata_to_work(meta, node["label"], all_person_works, all_works, node["description"])
                if matched:
                    fix.source_id, fix.source_label, fix.match_reason = matched
                    fix.source_type = "work"
                elif len(all_person_works) == 1:
                    # Single unambiguous work — but verify it's plausible
                    w = all_person_works[0]
                    # Find which person owns this work
                    owner = conns["persons"][0]["label"]
                    for p in conns["persons"]:
                        pw = await get_person_works(conn, p["id"])
                        if any(x["id"] == w["id"] for x in pw):
                            owner = p["label"]
                            break

                    # Guard: skip sole-work for school/group types
                    # (a school is not sourced from one work)
                    if ntype in ("school", "group"):
                        fix.flagged_manual = True
                        fix.match_reason = (
                            f"sole work by {owner} but node type is {ntype}"
                        )
                    # Guard: if multiple persons connected and the formulator
                    # is different from the work owner, skip
                    elif (
                        len(conns["persons"]) > 1
                        and meta.get("formulator")
                        and meta["formulator"] not in owner
                        and owner not in meta["formulator"]
                    ):
                        fix.flagged_manual = True
                        fix.match_reason = (
                            f"sole work by {owner} but formulator is "
                            f"{meta['formulator']}"
                        )
                    else:
                        fix.source_id = w["id"]
                        fix.source_label = w["label"]
                        fix.source_type = w["type"]
                        fix.match_reason = (
                            f"sole work by {owner}"
                        )
                else:
                    # Multiple works, no metadata match → flag
                    fix.flagged_manual = True
                    fix.match_reason = (
                        f"ambiguous: {len(all_person_works)} works by "
                        f"{', '.join(p['label'] for p in conns['persons'])}"
                    )
            else:
                # Person has no known works — try metadata/label against all works
                # but use strict mode to avoid false positives
                matched = match_metadata_to_work(
                    meta, node["label"], [], all_works, node["description"],
                    strict=True,
                )
                if matched:
                    fix.source_id, fix.source_label, fix.match_reason = matched
                    fix.source_type = "work"
                else:
                    fix.flagged_manual = True
                    fix.match_reason = (
                        f"person(s) {', '.join(p['label'] for p in conns['persons'])} "
                        f"have no authored works in KG; no metadata/label match"
                    )

        # --- Priority 4: Metadata only ---
        elif meta:
            fix.category = "HAS_META_ONLY"
            matched = match_metadata_to_work(meta, node["label"], [], all_works, node["description"])
            if matched:
                fix.source_id, fix.source_label, fix.match_reason = matched
                fix.source_type = "work"
            else:
                fix.flagged_manual = True
                source_ref = meta.get("source_work") or meta.get("primary_source") or ""
                fix.match_reason = (
                    f"metadata source '{source_ref}' not matched to any KG node"
                    if source_ref
                    else "no source reference in metadata"
                )

        # --- Priority 5: Truly isolated ---
        else:
            fix.category = "ISOLATED"
            fix.flagged_manual = True
            fix.match_reason = "no connections and no metadata"

        # Metadata patch for all nodes
        fix.metadata_patch = {
            "provenance_batch": RUN_TAG,
        }
        if fix.flagged_manual:
            fix.metadata_patch["provenance_status"] = "unsupported - pending manual review"
            fix.metadata_patch["provenance_note"] = fix.match_reason
        else:
            fix.metadata_patch["provenance_status"] = "work-level sourcing added programmatically"

        fixes.append(fix)

    return fixes


async def apply_fixes(
    conn: asyncpg.Connection, fixes: list[ProvenanceFix], dry_run: bool
) -> dict[str, Any]:
    """Apply all fixes. Returns report data."""
    edges_added = 0
    edges_skipped = 0
    metadata_patched = 0
    flagged = 0
    errors: list[str] = []

    for fix in fixes:
        # Add source_for edge if we have a source
        if fix.source_id and not fix.flagged_manual:
            if fix.node_type not in SOURCE_FOR_TARGET_TYPES:
                errors.append(
                    f"SKIP edge: {fix.node_type} not in source_for target_types "
                    f"for {fix.node_id}"
                )
                continue

            # Check if edge already exists
            exists = await check_edge_exists(
                conn, fix.source_id, fix.node_id, "source_for"
            )
            if exists:
                edges_skipped += 1
                continue

            if not dry_run:
                await conn.execute(f"""
                    INSERT INTO {SCHEMA}.kg_edges (source_id, target_id, relation, metadata)
                    VALUES ($1, $2, 'source_for', $3::jsonb)
                """, fix.source_id, fix.node_id, json.dumps({
                    "added_by": RUN_TAG,
                    "match_reason": fix.match_reason,
                }))
            edges_added += 1
        elif fix.flagged_manual:
            flagged += 1

        # Patch metadata
        if fix.metadata_patch:
            if not dry_run:
                # Merge patch into existing metadata
                await conn.execute(f"""
                    UPDATE {SCHEMA}.kg_nodes
                    SET metadata = COALESCE(metadata, '{{}}'::jsonb) || $2::jsonb,
                        updated_at = NOW()
                    WHERE node_id = $1
                """, fix.node_id, json.dumps(fix.metadata_patch))
            metadata_patched += 1

    return {
        "total_nodes": len(fixes),
        "edges_added": edges_added,
        "edges_skipped_existing": edges_skipped,
        "metadata_patched": metadata_patched,
        "flagged_manual_review": flagged,
        "errors": errors,
        "dry_run": dry_run,
    }


def generate_reports(
    fixes: list[ProvenanceFix], stats: dict[str, Any]
) -> None:
    """Generate JSON and Markdown reports."""
    ts = datetime.now(UTC).isoformat()

    # JSON report
    json_data = {
        "generated": ts,
        "run_tag": RUN_TAG,
        "stats": stats,
        "fixes": [],
    }
    for f in fixes:
        json_data["fixes"].append({
            "node_id": f.node_id,
            "node_type": f.node_type,
            "node_label": f.node_label,
            "category": f.category,
            "source_id": f.source_id,
            "source_label": f.source_label,
            "source_type": f.source_type,
            "match_reason": f.match_reason,
            "flagged_manual": f.flagged_manual,
        })

    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(
        json.dumps(json_data, indent=2, ensure_ascii=False) + "\n"
    )

    # Markdown report
    lines = [
        "# KG Provenance Batch 04 — Programmatic Repair",
        "",
        f"Generated: {ts}",
        f"Run tag: `{RUN_TAG}`",
        "",
        "## Summary",
        "",
        f"- Total unsupported nodes processed: {stats['total_nodes']}",
        f"- `source_for` edges added: {stats['edges_added']}",
        f"- Edges skipped (already exist): {stats['edges_skipped_existing']}",
        f"- Metadata patches applied: {stats['metadata_patched']}",
        f"- Flagged for manual review: {stats['flagged_manual_review']}",
        f"- Errors: {len(stats['errors'])}",
        f"- Dry run: {stats['dry_run']}",
        "",
    ]

    if stats["errors"]:
        lines.append("## Errors")
        lines.append("")
        for e in stats["errors"]:
            lines.append(f"- {e}")
        lines.append("")

    # Group by category
    by_cat: dict[str, list[ProvenanceFix]] = {}
    for f in fixes:
        by_cat.setdefault(f.category, []).append(f)

    for cat in ["HAS_WORK_EDGE", "HAS_PUB_EDGE", "HAS_PERSON", "HAS_META_ONLY", "ISOLATED"]:
        cat_fixes = by_cat.get(cat, [])
        if not cat_fixes:
            continue

        linked = [f for f in cat_fixes if not f.flagged_manual]
        flagged = [f for f in cat_fixes if f.flagged_manual]

        lines.append(f"## {cat} ({len(cat_fixes)} nodes)")
        lines.append("")

        if linked:
            lines.append(f"### Linked ({len(linked)})")
            lines.append("")
            for f in linked:
                lines.append(
                    f"- **{f.node_label}** (`{f.node_id}`, {f.node_type})"
                )
                lines.append(
                    f"  - source_for FROM `{f.source_label}` (`{f.source_id}`)"
                )
                lines.append(f"  - reason: {f.match_reason}")
            lines.append("")

        if flagged:
            lines.append(f"### Flagged for manual review ({len(flagged)})")
            lines.append("")
            for f in flagged:
                lines.append(
                    f"- **{f.node_label}** (`{f.node_id}`, {f.node_type})"
                )
                lines.append(f"  - reason: {f.match_reason}")
            lines.append("")

    REPORT_MD.write_text("\n".join(lines) + "\n")


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--confirm", action="store_true")
    args = parser.parse_args()
    dry_run = not args.confirm

    dsn = os.environ["DATABASE_URL"]
    conn = await asyncpg.connect(dsn=dsn, statement_cache_size=0)

    try:
        print(f"{'DRY RUN' if dry_run else 'LIVE RUN'} — {RUN_TAG}")
        print()

        # Build fixes
        print("Analyzing unsupported nodes...")
        fixes = await build_fixes(conn)

        print(f"Total unsupported nodes: {len(fixes)}")

        by_cat: dict[str, list[ProvenanceFix]] = {}
        for f in fixes:
            by_cat.setdefault(f.category, []).append(f)
        for cat, cat_fixes in sorted(by_cat.items()):
            linked = sum(1 for f in cat_fixes if not f.flagged_manual)
            flagged = sum(1 for f in cat_fixes if f.flagged_manual)
            print(f"  {cat}: {len(cat_fixes)} ({linked} linkable, {flagged} flagged)")

        print()

        # Apply
        if not dry_run:
            # Use a transaction
            async with conn.transaction():
                stats = await apply_fixes(conn, fixes, dry_run=False)
        else:
            stats = await apply_fixes(conn, fixes, dry_run=True)

        print(f"Edges to add:    {stats['edges_added']}")
        print(f"Edges skipped:   {stats['edges_skipped_existing']}")
        print(f"Metadata patches: {stats['metadata_patched']}")
        print(f"Flagged manual:  {stats['flagged_manual_review']}")
        if stats["errors"]:
            print(f"Errors: {len(stats['errors'])}")
            for e in stats["errors"]:
                print(f"  - {e}")

        # Generate reports
        generate_reports(fixes, stats)
        print("\nReports written to:")
        print(f"  {REPORT_JSON}")
        print(f"  {REPORT_MD}")

        if dry_run:
            print("\n  Re-run with --confirm to apply changes.")

    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
