"""Importer: writes mapped payloads into PostgreSQL.

Supports dry-run mode (statistics only) and confirmed mode (actual INSERTs).
Each work is imported within a single transaction with rollback on error.
"""

from __future__ import annotations

import json
import logging
import uuid
from dataclasses import dataclass, field

import psycopg2
import psycopg2.extras

from .config import SC_COLLECTION_NODE
from .mapper import map_work
from .models import SCWork

logger = logging.getLogger(__name__)


@dataclass
class ImportStats:
    """Statistics accumulated during import."""

    files_processed: int = 0
    works_created: int = 0
    passages_created: int = 0
    work_kg_nodes: int = 0
    chapter_kg_nodes: int = 0
    kg_edges: int = 0
    passage_citations: int = 0
    errors: list[str] = field(default_factory=list)

    def summary(self) -> str:
        lines = [
            "=" * 60,
            "SC Import Statistics",
            "=" * 60,
            f"  Files processed:     {self.files_processed}",
            f"  Works created:       {self.works_created}",
            f"  Passages created:    {self.passages_created}",
            f"  Work KG nodes:       {self.work_kg_nodes}",
            f"  Chapter KG nodes:    {self.chapter_kg_nodes}",
            f"  Total KG nodes:      {self.work_kg_nodes + self.chapter_kg_nodes}",
            f"  KG edges:            {self.kg_edges}",
            f"  Passage citations:   {self.passage_citations}",
            "=" * 60,
        ]
        if self.errors:
            lines.append(f"  ERRORS: {len(self.errors)}")
            for e in self.errors:
                lines.append(f"    - {e}")
        else:
            lines.append("  Errors: 0")
        return "\n".join(lines)


class SCImporter:
    """Handles PostgreSQL insertion for the SC import pipeline."""

    SCHEMA = "free_will"

    def __init__(self, db_url: str, dry_run: bool = True):
        self.db_url = db_url
        self.dry_run = dry_run
        self.run_id = str(uuid.uuid4())
        self.stats = ImportStats()

    def _connect(self) -> psycopg2.extensions.connection:
        """Open a connection and set search_path to the project schema."""
        conn = psycopg2.connect(self.db_url)
        with conn.cursor() as cur:
            cur.execute("SET search_path TO %s", (self.SCHEMA,))
        return conn

    def ensure_collection_node(self) -> None:
        """Create the SC collection KG node if it doesn't exist."""
        if self.dry_run:
            logger.info("[DRY RUN] Would create/verify SC collection node")
            return

        conn = self._connect()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO kg_nodes (node_id, label, type, description, metadata)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (node_id) DO NOTHING
                    """,
                    (
                        SC_COLLECTION_NODE["node_id"],
                        SC_COLLECTION_NODE["label"],
                        SC_COLLECTION_NODE["type"],
                        SC_COLLECTION_NODE["description"],
                        json.dumps(SC_COLLECTION_NODE["metadata"]),
                    ),
                )
            conn.commit()
            logger.info("SC collection node ensured: %s", SC_COLLECTION_NODE["node_id"])
        finally:
            conn.close()

    def find_duplicates(self, works: list[SCWork]) -> list[dict]:
        """Find existing works in the DB that overlap with SC works.

        Searches by author+title substring match and returns a list of
        dicts with work_id, canonical_id, title, author, and source.
        """
        conn = self._connect()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                # Get all SC node_ids we plan to insert
                sc_node_ids = [w.node_id for w in works]

                # 1. Check for exact canonical_id matches
                cur.execute(
                    """
                    SELECT work_id, canonical_id, title, author, source
                    FROM ancient_works
                    WHERE canonical_id = ANY(%s)
                    """,
                    (sc_node_ids,),
                )
                exact = list(cur.fetchall())

                # 2. Check for existing works by same authors with similar titles
                cur.execute(
                    """
                    SELECT work_id, canonical_id, title, author, source,
                           kg_work_id
                    FROM ancient_works
                    WHERE source != 'sources_chretiennes'
                    ORDER BY author, title
                    """,
                )
                all_existing = list(cur.fetchall())

                # 3. Check for existing KG nodes that would conflict
                cur.execute(
                    """
                    SELECT node_id, label, type
                    FROM kg_nodes
                    WHERE node_id = ANY(%s)
                    """,
                    (sc_node_ids,),
                )
                existing_nodes = list(cur.fetchall())

            return {
                "exact_canonical_matches": exact,
                "all_existing_works": all_existing,
                "existing_kg_nodes": existing_nodes,
            }
        finally:
            conn.close()

    def remove_work(self, work_id: str, canonical_id: str) -> dict:
        """Remove an existing work and all its associated data.

        Deletes in order: passage_citations, kg_edges, kg_nodes (Passage),
        passages, kg_nodes (Work), ancient_works.
        Returns counts of deleted rows.
        """
        conn = self._connect()
        counts = {}
        try:
            with conn.cursor() as cur:
                # 1. Delete passage_citations for this work's passages
                cur.execute(
                    """
                    DELETE FROM passage_citations
                    WHERE passage_id IN (
                        SELECT passage_id FROM passages WHERE work_id = %s
                    )
                    """,
                    (work_id,),
                )
                counts["passage_citations"] = cur.rowcount

                # 2. Delete kg_edges where source or target is the work node
                #    or any of its chapter nodes
                cur.execute(
                    """
                    DELETE FROM kg_edges
                    WHERE source_id = %s
                       OR target_id = %s
                       OR source_id IN (
                           SELECT node_id FROM kg_nodes
                           WHERE metadata->>'work_node_id' = %s
                       )
                       OR target_id IN (
                           SELECT node_id FROM kg_nodes
                           WHERE metadata->>'work_node_id' = %s
                       )
                    """,
                    (canonical_id, canonical_id, canonical_id, canonical_id),
                )
                counts["kg_edges"] = cur.rowcount

                # 3. Delete chapter/paragraph KG nodes for this work
                cur.execute(
                    """
                    DELETE FROM kg_nodes
                    WHERE metadata->>'work_node_id' = %s
                    """,
                    (canonical_id,),
                )
                counts["chapter_kg_nodes"] = cur.rowcount

                # 4. Delete passages
                cur.execute(
                    "DELETE FROM passages WHERE work_id = %s",
                    (work_id,),
                )
                counts["passages"] = cur.rowcount

                # 5. Delete the Work KG node
                cur.execute(
                    "DELETE FROM kg_nodes WHERE node_id = %s",
                    (canonical_id,),
                )
                counts["work_kg_node"] = cur.rowcount

                # 6. Delete ancient_works row
                cur.execute(
                    "DELETE FROM ancient_works WHERE work_id = %s",
                    (work_id,),
                )
                counts["ancient_works"] = cur.rowcount

            conn.commit()
            logger.info(
                "Removed existing work %s (%s): %s",
                canonical_id,
                work_id,
                counts,
            )
        except Exception as exc:
            conn.rollback()
            logger.error("Error removing work %s: %s", canonical_id, exc)
            raise
        finally:
            conn.close()
        return counts

    def _kg_node_row(self, node: dict) -> tuple:
        """Build a kg_nodes INSERT tuple, folding school/role into metadata."""
        meta = dict(node["metadata"])
        if node.get("school"):
            meta["school"] = node["school"]
        if node.get("role"):
            meta["role"] = node["role"]
        return (
            node["node_id"],
            node["label"],
            node["type"],
            node["description"],
            node.get("period"),
            json.dumps(meta),
        )

    def _ensure_author_nodes(self, works: list[SCWork]) -> None:
        """Create Person kg_nodes for authors referenced by 'wrote' edges."""
        if self.dry_run:
            return

        author_ids: dict[str, SCWork] = {}
        for w in works:
            if w.author_kg_id and w.author_kg_id not in author_ids:
                author_ids[w.author_kg_id] = w

        if not author_ids:
            return

        conn = self._connect()
        try:
            with conn.cursor() as cur:
                rows = [
                    (
                        aid,
                        w.author,
                        "Person",
                        "Author of ancient texts (auto-created by SC import)",
                        w.period,
                        json.dumps({
                            "run_id": self.run_id,
                            "phase": 1,
                            "auto_created": True,
                        }),
                    )
                    for aid, w in author_ids.items()
                ]
                psycopg2.extras.execute_values(
                    cur,
                    """
                    INSERT INTO kg_nodes
                        (node_id, label, type, description, period, metadata)
                    VALUES %s
                    ON CONFLICT (node_id) DO NOTHING
                    """,
                    rows,
                )
            conn.commit()
            logger.info(
                "Ensured %d author node(s): %s",
                len(author_ids),
                ", ".join(author_ids.keys()),
            )
        finally:
            conn.close()

    def import_work(self, work: SCWork) -> dict:
        """Import one work into all tables within a transaction.

        Returns the mapped payload (needed for deferred edge insertion).
        Edges are NOT inserted here — they are deferred to import_corpus()
        so that all kg_nodes exist before FK-constrained edges are created.
        """
        payload = map_work(work, self.run_id)

        # Accumulate statistics
        self.stats.files_processed += 1
        self.stats.works_created += 1
        self.stats.passages_created += len(payload["passages"])
        self.stats.work_kg_nodes += 1
        self.stats.chapter_kg_nodes += len(payload["chapter_kg_nodes"])
        self.stats.kg_edges += len(payload["kg_edges"])
        self.stats.passage_citations += len(payload["passage_citations"])

        if self.dry_run:
            logger.info(
                "[DRY RUN] [%d/%d] %s %s: %d passages, %d chapter nodes, "
                "%d edges, %d citations",
                self.stats.files_processed,
                40,
                work.node_id,
                work.title,
                len(payload["passages"]),
                len(payload["chapter_kg_nodes"]),
                len(payload["kg_edges"]),
                len(payload["passage_citations"]),
            )
            return payload

        conn = self._connect()
        try:
            with conn.cursor() as cur:
                # 1. INSERT ancient_works
                aw = payload["ancient_work"]
                cur.execute(
                    """
                    INSERT INTO ancient_works
                        (work_id, canonical_id, kg_work_id, title, title_original,
                         author, language, period, date_composed, school,
                         source, division_scheme, citation_levels,
                         total_divisions, total_words, total_chars, metadata)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                            %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        str(aw["work_id"]),
                        aw["canonical_id"],
                        aw["kg_work_id"],
                        aw["title"],
                        aw["title_original"],
                        aw["author"],
                        aw["language"],
                        aw["period"],
                        aw["date_composed"],
                        aw["school"],
                        aw["source"],
                        aw["division_scheme"],
                        aw["citation_levels"],
                        aw["total_divisions"],
                        aw["total_words"],
                        aw["total_chars"],
                        json.dumps(aw["metadata"]),
                    ),
                )

                # 2. INSERT passages (batched)
                passage_rows = [
                    (
                        str(p["passage_id"]),
                        str(p["work_id"]),
                        p["canonical_ref"],
                        p["cts_urn"],
                        p["book"],
                        p["chapter"],
                        p["section"],
                        p["sequence_number"],
                        p["text_content"],
                        p["char_length"],
                        p["word_count"],
                        json.dumps(p["citation_hierarchy"]),
                    )
                    for p in payload["passages"]
                ]
                psycopg2.extras.execute_values(
                    cur,
                    """
                    INSERT INTO passages
                        (passage_id, work_id, canonical_ref, cts_urn,
                         book, chapter, section, sequence_number,
                         text_content, char_length, word_count,
                         citation_hierarchy)
                    VALUES %s
                    """,
                    passage_rows,
                    page_size=500,
                )

                # 3. INSERT kg_nodes (Work)
                cur.execute(
                    """
                    INSERT INTO kg_nodes
                        (node_id, label, type, description, period, metadata)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (node_id) DO NOTHING
                    """,
                    self._kg_node_row(payload["work_kg_node"]),
                )

                # 4. INSERT kg_nodes (Chapters/Paragraphs — batched)
                chapter_rows = [
                    self._kg_node_row(cn)
                    for cn in payload["chapter_kg_nodes"]
                ]
                psycopg2.extras.execute_values(
                    cur,
                    """
                    INSERT INTO kg_nodes
                        (node_id, label, type, description, period, metadata)
                    VALUES %s
                    ON CONFLICT (node_id) DO NOTHING
                    """,
                    chapter_rows,
                    page_size=500,
                )

                # 5. INSERT passage_citations (batched)
                citation_rows = [
                    (
                        str(c["citation_id"]),
                        str(c["passage_id"]),
                        c["kg_node_id"],
                        c["citation_type"],
                        c["confidence"],
                    )
                    for c in payload["passage_citations"]
                ]
                psycopg2.extras.execute_values(
                    cur,
                    """
                    INSERT INTO passage_citations
                        (citation_id, passage_id, kg_node_id,
                         citation_type, confidence)
                    VALUES %s
                    """,
                    citation_rows,
                    page_size=500,
                )

                # NOTE: kg_edges are inserted in a separate pass by
                # import_corpus() after ALL nodes exist, to satisfy FKs.

            conn.commit()
            logger.info(
                "[%d] Imported %s: %d passages, %d chapter nodes",
                self.stats.files_processed,
                work.node_id,
                len(payload["passages"]),
                len(payload["chapter_kg_nodes"]),
            )
        except Exception as exc:
            conn.rollback()
            msg = f"ERROR importing {work.file_name}: {exc}"
            logger.error(msg)
            self.stats.errors.append(msg)
            raise
        finally:
            conn.close()

        return payload

    def _insert_all_edges(self, all_edges: list[dict]) -> None:
        """Insert all kg_edges in one batch after all nodes exist."""
        if self.dry_run or not all_edges:
            return

        conn = self._connect()
        try:
            with conn.cursor() as cur:
                edge_rows = [
                    (
                        str(e["edge_id"]),
                        e["source_id"],
                        e["target_id"],
                        e["relation"],
                        json.dumps(e["metadata"]),
                    )
                    for e in all_edges
                ]
                psycopg2.extras.execute_values(
                    cur,
                    """
                    INSERT INTO kg_edges
                        (edge_id, source_id, target_id, relation, metadata)
                    VALUES %s
                    """,
                    edge_rows,
                    page_size=500,
                )
            conn.commit()
            logger.info("Inserted %d kg_edges", len(all_edges))
        except Exception as exc:
            conn.rollback()
            msg = f"ERROR inserting edges: {exc}"
            logger.error(msg)
            self.stats.errors.append(msg)
            raise
        finally:
            conn.close()

    def import_corpus(self, works: list[SCWork]) -> ImportStats:
        """Import all works in 3 phases to satisfy FK constraints.

        Phase 1: Create prerequisite nodes (collection, authors).
        Phase 2: Import each work (ancient_works, passages, kg_nodes, citations).
        Phase 3: Insert all kg_edges (all node targets now exist).
        """
        # Phase 1: prerequisite nodes
        self.ensure_collection_node()
        self._ensure_author_nodes(works)

        # Phase 2: per-work data
        all_edges: list[dict] = []
        for work in works:
            try:
                payload = self.import_work(work)
                all_edges.extend(payload["kg_edges"])
            except Exception:
                # Error already logged and recorded in stats
                continue

        # Phase 3: edges (all source_id/target_id nodes now exist)
        if all_edges:
            logger.info("Phase 3: inserting %d edges...", len(all_edges))
            self._insert_all_edges(all_edges)

        return self.stats

    def rollback_run(self, run_id: str) -> None:
        """Delete all data created in a specific run."""
        if self.dry_run:
            logger.info("[DRY RUN] Would rollback run %s", run_id)
            return

        conn = self._connect()
        try:
            with conn.cursor() as cur:
                # Delete passage_citations via passages via ancient_works
                cur.execute(
                    """
                    DELETE FROM passage_citations
                    WHERE passage_id IN (
                        SELECT p.passage_id FROM passages p
                        JOIN ancient_works w ON p.work_id = w.work_id
                        WHERE w.metadata->>'run_id' = %s
                    )
                    """,
                    (run_id,),
                )
                pc_count = cur.rowcount

                # Delete kg_edges by run_id in metadata
                cur.execute(
                    "DELETE FROM kg_edges WHERE metadata->>'run_id' = %s",
                    (run_id,),
                )
                edge_count = cur.rowcount

                # Delete kg_nodes by run_id in metadata
                cur.execute(
                    "DELETE FROM kg_nodes WHERE metadata->>'run_id' = %s",
                    (run_id,),
                )
                node_count = cur.rowcount

                # Delete passages via ancient_works
                cur.execute(
                    """
                    DELETE FROM passages
                    WHERE work_id IN (
                        SELECT work_id FROM ancient_works
                        WHERE metadata->>'run_id' = %s
                    )
                    """,
                    (run_id,),
                )
                passage_count = cur.rowcount

                # Delete ancient_works
                cur.execute(
                    "DELETE FROM ancient_works WHERE metadata->>'run_id' = %s",
                    (run_id,),
                )
                work_count = cur.rowcount

            conn.commit()
            logger.info(
                "Rollback complete for run %s: %d works, %d passages, "
                "%d nodes, %d edges, %d citations deleted",
                run_id,
                work_count,
                passage_count,
                node_count,
                edge_count,
                pc_count,
            )
        finally:
            conn.close()
