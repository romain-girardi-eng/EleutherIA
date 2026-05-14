"""Doxographical mapper.

Classifies passage_* KG nodes by attestation type and attaches canonical
fragment-collection references (SVF / LS / DK / Wehrli / Edelstein-Kidd / FHSG
/ Usener / Marcovich / GCS / SC / PG / PL).

Two layers of work:

1. **Curated high-confidence mappings** (data/doxographical_audit/fragment_mappings.jsonl).
   These are hand-verified canonical fragments (Bobzien 1998/2001, Long-Sedley
   1987). Applied with full metadata + ``attested_by`` edges.

2. **Heuristic bulk classifier**. Every passage_* node gets a baseline
   ``attestation_type`` based on its author + work pattern. NO fragment
   numbers are invented — those only come from the curated layer.

Idempotent: re-running merges into existing metadata via ``jsonb_set``.

Usage::

    DATABASE_URL=... python -m database.scripts.doxographical_mapper [--dry-run]
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import psycopg2
from psycopg2.extras import Json, execute_values

logger = logging.getLogger("doxographical_mapper")

MAPPINGS_PATH = Path(__file__).resolve().parents[2] / "data" / "doxographical_audit" / "fragment_mappings.jsonl"

# Authors who write in their own voice (mostly direct attestations).
DIRECT_AUTHORS: set[str] = {
    "Plato",
    "Aristotle",
    "Epictetus",
    "Marcus Aurelius",
    "Seneca",
    "Augustine",
    "Boethius",
    "Boethius d. 524",
    "Origen of Alexandria",
    "Origen",
    "Justin Martyr",
    "Plotinus",
    "Philo of Alexandria",
    "Lucretius",
    "Titus Lucretius Carus",
    "Tatian",
    "Methodius",
    "Methodius of Olympus",
    "Hermas",
    "Ignatius of Antioch",
    "Clement of Rome",
    "Theophilus of Antioch",
    "Pamphilus of Caesarea",
    "Tertullian",
    "Athenagoras of Athens",
    "Aristides of Athens",
    "Melito of Sardis",
    "Gregory of Nazianzus",
    "Anonymous (Pseudo-Barnabas)",
    "Hilary of Poitiers",
    "Irenaeus",
}

# Authors whose works are predominantly doxographical reports of earlier figures.
DOXOGRAPHICAL_AUTHORS: set[str] = {
    "Diogenes Laertius",
    "Pseudo-Plutarch",
    "Aulus Gellius",
}

# Authors who frequently report earlier philosophers but also speak in own voice
# (use work/passage-level heuristics; default to ``testimonium``).
MIXED_AUTHORS: set[str] = {
    "Plutarch",
    "Plutarch of Chaeronea",
    "Cicero",
    "Marcus Tullius Cicero",
    "Sextus Empiricus",
    "Alexander of Aphrodisias",
    "Eusebius",
    "Eusebius of Caesarea",
    "Simplicius",
    "Simplicius of Cilicia",
    "Stobaeus",
    "Hippolytus",
    "Clement of Alexandria",
}


@dataclass(frozen=True)
class Mapping:
    """A single curated mapping row."""

    passage_id: str
    attestation_type: str
    primary_attestation: dict[str, Any]
    fragment_collections: list[dict[str, Any]]
    extant_in_original: bool
    extant_in_translation_only: bool
    confidence: str
    note: str = ""
    fragmented_philosopher: str | None = None
    philosopher_node_id: str | None = None


def load_curated_mappings(path: Path = MAPPINGS_PATH) -> list[Mapping]:
    """Parse the JSONL of curated fragment mappings."""

    if not path.exists():
        logger.warning("No curated mappings file at %s", path)
        return []
    out: list[Mapping] = []
    with path.open("r", encoding="utf-8") as fh:
        for line_no, line in enumerate(fh, 1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_no} invalid JSON: {exc}") from exc
            out.append(
                Mapping(
                    passage_id=row["passage_id"],
                    attestation_type=row["attestation_type"],
                    primary_attestation=row.get("primary_attestation") or {},
                    fragment_collections=row.get("fragment_collections") or [],
                    extant_in_original=bool(row.get("extant_in_original", False)),
                    extant_in_translation_only=bool(row.get("extant_in_translation_only", False)),
                    confidence=row.get("confidence", "medium"),
                    note=row.get("note", ""),
                    fragmented_philosopher=row.get("fragmented_philosopher"),
                    philosopher_node_id=row.get("philosopher_node_id"),
                )
            )
    return out


def classify_attestation(author: str | None, work_node_id: str | None, label: str | None) -> str:  # noqa: ARG001
    """Heuristic baseline classifier — never invents fragment numbers.

    ``work_node_id`` and ``label`` are kept in the signature for future
    refinements (e.g. work-level overrides) even though the current heuristic
    only consults ``author``.
    """

    a = (author or "").strip()
    if not a:
        return "unknown"
    if a in DIRECT_AUTHORS:
        return "direct"
    if a in DOXOGRAPHICAL_AUTHORS:
        # Whole work is a report of others.
        return "doxographical_fragment"
    if a in MIXED_AUTHORS:
        return "testimonium"
    # Unknown / fall-through.
    return "direct"


def merge_metadata_sql() -> str:
    """SQL fragment to merge attestation metadata into kg_nodes.metadata.

    Uses ``COALESCE(metadata, '{}'::jsonb) || %s::jsonb`` so previously-applied
    runs are overwritten field-by-field but unrelated metadata is preserved.
    """

    return (
        "UPDATE free_will.kg_nodes "
        "SET metadata = COALESCE(metadata, '{}'::jsonb) || %s::jsonb, "
        "    updated_at = NOW() "
        "WHERE node_id = %s AND type = 'passage'"
    )


def apply_curated(conn: psycopg2.extensions.connection, mappings: list[Mapping], *, dry_run: bool) -> dict[str, int]:
    """Apply curated metadata to passage nodes."""

    stats = {"curated_attempted": 0, "curated_applied": 0, "curated_missing": 0}
    with conn.cursor() as cur:
        cur.execute("SET search_path TO free_will, public")
        ids = [m.passage_id for m in mappings]
        if not ids:
            return stats
        cur.execute("SELECT node_id FROM kg_nodes WHERE node_id = ANY(%s) AND type='passage'", (ids,))
        present = {r[0] for r in cur.fetchall()}
        for m in mappings:
            stats["curated_attempted"] += 1
            if m.passage_id not in present:
                stats["curated_missing"] += 1
                logger.warning("Curated passage missing: %s", m.passage_id)
                continue
            payload = {
                "attestation_type": m.attestation_type,
                "primary_attestation": m.primary_attestation,
                "fragment_collections": m.fragment_collections,
                "extant_in_original": m.extant_in_original,
                "extant_in_translation_only": m.extant_in_translation_only,
                "doxographical_confidence": m.confidence,
                "doxographical_note": m.note,
                "doxographical_source": "curated",
            }
            if m.fragmented_philosopher:
                payload["fragmented_philosopher"] = m.fragmented_philosopher
            if m.philosopher_node_id:
                payload["fragmented_philosopher_node_id"] = m.philosopher_node_id
            if dry_run:
                logger.info("[DRY] curated %s ← %s", m.passage_id, m.attestation_type)
            else:
                cur.execute(merge_metadata_sql(), (Json(payload), m.passage_id))
            stats["curated_applied"] += 1
        if not dry_run:
            conn.commit()
    return stats


def apply_bulk_classification(conn: psycopg2.extensions.connection, *, dry_run: bool, batch_size: int = 50) -> dict[str, int]:
    """Apply heuristic attestation_type to every passage that lacks one.

    Updates one row at a time inside batches and commits after each batch so
    that a server-side timeout never loses already-committed work.
    """

    stats: dict[str, int] = {
        "bulk_scanned": 0,
        "bulk_updated": 0,
        "type_direct": 0,
        "type_testimonium": 0,
        "type_doxographical_fragment": 0,
        "type_unknown": 0,
    }
    rows: list[tuple[str, str | None, dict[str, Any] | None]]
    with conn.cursor() as cur:
        cur.execute("SET statement_timeout = '120s'")
        cur.execute("SET search_path TO free_will, public")
        cur.execute(
            """
            SELECT node_id, label, metadata
            FROM kg_nodes
            WHERE type = 'passage'
              AND (metadata->>'attestation_type') IS NULL
            """
        )
        rows = cur.fetchall()
        stats["bulk_scanned"] = len(rows)

    updates: list[tuple[str, str]] = []  # (payload_json, node_id)
    for node_id, label, metadata in rows:
        md = metadata or {}
        author = md.get("author")
        work = md.get("work_node_id")
        cls = classify_attestation(author, work, label)
        stats[f"type_{cls}"] = stats.get(f"type_{cls}", 0) + 1
        payload = {
            "attestation_type": cls,
            "doxographical_source": "heuristic",
            "doxographical_confidence": "medium" if cls != "unknown" else "needs_review",
        }
        if cls == "unknown":
            payload["doxographical_note"] = "no author metadata — needs manual classification"
        updates.append((json.dumps(payload), node_id))

    if dry_run:
        logger.info("[DRY] would update %d passages with bulk classification", len(updates))
        stats["bulk_updated"] = len(updates)
        return stats

    # Commit per batch so a server-side timeout never undoes already-applied work.
    for i in range(0, len(updates), batch_size):
        batch = updates[i : i + batch_size]
        with conn.cursor() as cur:
            cur.execute("SET statement_timeout = '120s'")
            cur.executemany(merge_metadata_sql(), batch)
        conn.commit()
        stats["bulk_updated"] += len(batch)
        if i // batch_size % 20 == 0:
            logger.info("bulk batch %d-%d applied (%d/%d)", i, i + len(batch), stats["bulk_updated"], len(updates))
    return stats


def insert_attested_by_edges(conn: psycopg2.extensions.connection, mappings: list[Mapping], *, dry_run: bool) -> dict[str, int]:
    """Insert ``attested_by`` edges from fragment passage → transmitting passage.

    Only created when ``transmitting_passage`` is distinct from the passage
    itself (i.e. when the fragmentary passage is from a different work than
    the transmitter — for canonical cases like Cic. De Fato we use a self-edge
    pattern; here we skip self-edges and rely on the philosopher_node_id link).
    """

    stats = {"edges_attempted": 0, "edges_inserted": 0, "edges_skipped_self": 0}
    with conn.cursor() as cur:
        cur.execute("SET search_path TO free_will, public")
        rows: list[tuple[str, str, str, dict[str, Any]]] = []
        for m in mappings:
            tp = (m.primary_attestation or {}).get("transmitting_passage")
            if not tp:
                continue
            if tp == m.passage_id:
                stats["edges_skipped_self"] += 1
                continue
            stats["edges_attempted"] += 1
            meta = {
                "doxographical": True,
                "confidence": m.confidence,
                "fragment_collections": m.fragment_collections,
                "fragmented_philosopher_node_id": m.philosopher_node_id,
            }
            rows.append((m.passage_id, tp, "attested_by", meta))
        if not rows:
            return stats
        if dry_run:
            logger.info("[DRY] would insert %d attested_by edges", len(rows))
            stats["edges_inserted"] = len(rows)
            return stats
        execute_values(
            cur,
            """
            INSERT INTO free_will.kg_edges (source_id, target_id, source, target, relation, weight, metadata)
            VALUES %s
            ON CONFLICT DO NOTHING
            """,
            [(s, t, s, t, r, 1.0, Json(m)) for (s, t, r, m) in rows],
            template="(%s,%s,%s,%s,%s,%s,%s)",
        )
        stats["edges_inserted"] = cur.rowcount if cur.rowcount and cur.rowcount > 0 else len(rows)
    return stats


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Doxographical mapper")
    parser.add_argument("--dry-run", action="store_true", help="Do not write to DB")
    parser.add_argument("--skip-bulk", action="store_true", help="Skip heuristic bulk classification")
    parser.add_argument("--skip-edges", action="store_true", help="Skip attested_by edge insertion")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    url = os.environ.get("DATABASE_URL")
    if not url:
        print("DATABASE_URL not set", file=sys.stderr)
        return 2

    mappings = load_curated_mappings()
    logger.info("Loaded %d curated mappings", len(mappings))

    with psycopg2.connect(url) as conn:
        with conn.cursor() as _c:
            # Bump the per-session timeout — Supabase pooler default is short.
            _c.execute("SET statement_timeout = '120s'")
        cur_stats = apply_curated(conn, mappings, dry_run=args.dry_run)
        edge_stats = (
            insert_attested_by_edges(conn, mappings, dry_run=args.dry_run)
            if not args.skip_edges
            else {"edges_inserted": 0, "edges_attempted": 0, "edges_skipped_self": 0}
        )
        bulk_stats = (
            apply_bulk_classification(conn, dry_run=args.dry_run)
            if not args.skip_bulk
            else {"bulk_scanned": 0, "bulk_updated": 0}
        )
        if not args.dry_run:
            conn.commit()

    report = {
        "curated": cur_stats,
        "edges": edge_stats,
        "bulk": bulk_stats,
        "dry_run": args.dry_run,
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
