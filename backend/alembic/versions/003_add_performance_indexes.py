"""add_performance_indexes

Revision ID: 003_indexes
Revises: 002_materialized
Create Date: 2025-02-04

Adds performance indexes for common query patterns:
- Full-text search indexes (GIN)
- Embedding similarity indexes (if pgvector available)
- Composite indexes for filtered queries
- Partial indexes for common filters
"""
from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '003_indexes'
down_revision: str | Sequence[str] | None = '002_materialized'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add performance indexes."""

    # ==========================================================================
    # Knowledge Graph Indexes
    # ==========================================================================

    # Composite index for node type + school filtering
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_kg_nodes_type_school
        ON kg_nodes (node_type, school)
        WHERE school IS NOT NULL
    """)

    # Index for node label search (case-insensitive)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_kg_nodes_label_lower
        ON kg_nodes (LOWER(label))
    """)

    # Full-text search index on node descriptions
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_kg_nodes_description_fts
        ON kg_nodes USING GIN (to_tsvector('english', COALESCE(description, '')))
    """)

    # Edge relation type index
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_kg_edges_relation
        ON kg_edges (relation)
    """)

    # Composite index for graph traversal
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_kg_edges_source_relation
        ON kg_edges (source_id, relation)
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_kg_edges_target_relation
        ON kg_edges (target_id, relation)
    """)

    # ==========================================================================
    # Passage Indexes (free_will schema)
    # ==========================================================================

    # Full-text search on passage content
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_passages_content_fts
        ON free_will.passages USING GIN (to_tsvector('simple', COALESCE(text_content, '')))
    """)

    # Index for CTS URN lookups
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_passages_cts_urn
        ON free_will.passages (cts_urn)
        WHERE cts_urn IS NOT NULL
    """)

    # Composite index for work + section filtering
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_passages_work_section
        ON free_will.passages (work_id, section_ref)
    """)

    # ==========================================================================
    # Ancient Works Indexes
    # ==========================================================================

    # Author index for filtering
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_works_author
        ON free_will.ancient_works (author)
        WHERE author IS NOT NULL
    """)

    # Language index
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_works_language
        ON free_will.ancient_works (language)
    """)

    # Date range index for chronological queries
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_works_date_range
        ON free_will.ancient_works (date_start, date_end)
        WHERE date_start IS NOT NULL
    """)

    # ==========================================================================
    # Passage Citations Indexes (KG-to-passage links)
    # ==========================================================================

    # Index for looking up citations by node
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_passage_citations_node
        ON free_will.passage_citations (node_id)
    """)

    # Index for looking up citations by passage
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_passage_citations_passage
        ON free_will.passage_citations (passage_id)
    """)

    # Composite index for confidence-based filtering
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_passage_citations_confidence
        ON free_will.passage_citations (node_id, confidence_score DESC)
        WHERE confidence_score >= 0.7
    """)


def downgrade() -> None:
    """Remove performance indexes."""
    # KG indexes
    op.execute("DROP INDEX IF EXISTS idx_kg_nodes_type_school")
    op.execute("DROP INDEX IF EXISTS idx_kg_nodes_label_lower")
    op.execute("DROP INDEX IF EXISTS idx_kg_nodes_description_fts")
    op.execute("DROP INDEX IF EXISTS idx_kg_edges_relation")
    op.execute("DROP INDEX IF EXISTS idx_kg_edges_source_relation")
    op.execute("DROP INDEX IF EXISTS idx_kg_edges_target_relation")

    # Passage indexes
    op.execute("DROP INDEX IF EXISTS free_will.idx_passages_content_fts")
    op.execute("DROP INDEX IF EXISTS free_will.idx_passages_cts_urn")
    op.execute("DROP INDEX IF EXISTS free_will.idx_passages_work_section")

    # Works indexes
    op.execute("DROP INDEX IF EXISTS free_will.idx_works_author")
    op.execute("DROP INDEX IF EXISTS free_will.idx_works_language")
    op.execute("DROP INDEX IF EXISTS free_will.idx_works_date_range")

    # Citation indexes
    op.execute("DROP INDEX IF EXISTS free_will.idx_passage_citations_node")
    op.execute("DROP INDEX IF EXISTS free_will.idx_passage_citations_passage")
    op.execute("DROP INDEX IF EXISTS free_will.idx_passage_citations_confidence")
