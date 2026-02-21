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

    def __init__(self, db_url: str, dry_run: bool = True):
        self.db_url = db_url
        self.dry_run = dry_run
        self.run_id = str(uuid.uuid4())
        self.stats = ImportStats()

    def ensure_collection_node(self) -> None:
        """Create the SC collection KG node if it doesn't exist."""
        if self.dry_run:
            logger.info("[DRY RUN] Would create/verify SC collection node")
            return

        conn = psycopg2.connect(self.db_url)
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

    def import_work(self, work: SCWork) -> None:
        """Import one work into all 5 tables within a transaction."""
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
            return

        conn = psycopg2.connect(self.db_url)
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

                # 2. INSERT passages (batch)
                for p in payload["passages"]:
                    cur.execute(
                        """
                        INSERT INTO passages
                            (passage_id, work_id, canonical_ref, cts_urn,
                             book, chapter, section, sequence_number,
                             text_content, char_length, word_count,
                             citation_hierarchy)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """,
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
                        ),
                    )

                # 3. INSERT kg_nodes (Work)
                wn = payload["work_kg_node"]
                cur.execute(
                    """
                    INSERT INTO kg_nodes
                        (node_id, label, type, description, period, school,
                         role, metadata)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (node_id) DO NOTHING
                    """,
                    (
                        wn["node_id"],
                        wn["label"],
                        wn["type"],
                        wn["description"],
                        wn["period"],
                        wn["school"],
                        wn["role"],
                        json.dumps(wn["metadata"]),
                    ),
                )

                # 4. INSERT kg_nodes (Chapters/Paragraphs)
                for cn in payload["chapter_kg_nodes"]:
                    cur.execute(
                        """
                        INSERT INTO kg_nodes
                            (node_id, label, type, description, period, school,
                             role, metadata)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (node_id) DO NOTHING
                        """,
                        (
                            cn["node_id"],
                            cn["label"],
                            cn["type"],
                            cn["description"],
                            cn["period"],
                            cn["school"],
                            cn["role"],
                            json.dumps(cn["metadata"]),
                        ),
                    )

                # 5. INSERT kg_edges
                for e in payload["kg_edges"]:
                    cur.execute(
                        """
                        INSERT INTO kg_edges
                            (edge_id, source_id, target_id, relation, metadata)
                        VALUES (%s, %s, %s, %s, %s)
                        """,
                        (
                            str(e["edge_id"]),
                            e["source_id"],
                            e["target_id"],
                            e["relation"],
                            json.dumps(e["metadata"]),
                        ),
                    )

                # 6. INSERT passage_citations
                for c in payload["passage_citations"]:
                    cur.execute(
                        """
                        INSERT INTO passage_citations
                            (citation_id, passage_id, kg_node_id,
                             citation_type, confidence)
                        VALUES (%s, %s, %s, %s, %s)
                        """,
                        (
                            str(c["citation_id"]),
                            str(c["passage_id"]),
                            c["kg_node_id"],
                            c["citation_type"],
                            c["confidence"],
                        ),
                    )

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

    def import_corpus(self, works: list[SCWork]) -> ImportStats:
        """Import all works. Returns statistics."""
        self.ensure_collection_node()

        for work in works:
            try:
                self.import_work(work)
            except Exception:
                # Error already logged and recorded in stats
                continue

        return self.stats

    def rollback_run(self, run_id: str) -> None:
        """Delete all data created in a specific run."""
        if self.dry_run:
            logger.info("[DRY RUN] Would rollback run %s", run_id)
            return

        conn = psycopg2.connect(self.db_url)
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
