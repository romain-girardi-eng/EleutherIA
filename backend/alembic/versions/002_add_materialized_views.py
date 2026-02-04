"""add_materialized_views

Revision ID: 002_materialized
Revises: 93f054a88815
Create Date: 2025-02-04

Adds materialized views for frequently accessed aggregations:
- mv_kg_stats: Knowledge graph statistics
- mv_search_facets: Search facet counts
- mv_author_network: Author collaboration/influence network
- mv_concept_hierarchy: Concept parent-child relationships

These views are refreshed periodically (e.g., hourly) to provide
fast access to expensive aggregate queries.
"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '002_materialized'
down_revision: Union[str, Sequence[str], None] = '93f054a88815'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create materialized views for caching expensive aggregations."""

    # ==========================================================================
    # 1. Knowledge Graph Statistics
    # ==========================================================================
    op.execute("""
        CREATE MATERIALIZED VIEW IF NOT EXISTS mv_kg_stats AS
        SELECT
            -- Node counts by type
            (SELECT COUNT(*) FROM kg_nodes) AS total_nodes,
            (SELECT COUNT(*) FROM kg_nodes WHERE node_type = 'person') AS person_nodes,
            (SELECT COUNT(*) FROM kg_nodes WHERE node_type = 'concept') AS concept_nodes,
            (SELECT COUNT(*) FROM kg_nodes WHERE node_type = 'work') AS work_nodes,
            (SELECT COUNT(*) FROM kg_nodes WHERE node_type = 'argument') AS argument_nodes,
            (SELECT COUNT(*) FROM kg_nodes WHERE node_type = 'school') AS school_nodes,

            -- Edge counts
            (SELECT COUNT(*) FROM kg_edges) AS total_edges,

            -- Passage counts
            (SELECT COUNT(*) FROM free_will.passages) AS total_passages,
            (SELECT COUNT(*) FROM free_will.ancient_works) AS total_works,

            -- Timestamp
            NOW() AS refreshed_at
        WITH DATA
    """)

    # Create unique index for REFRESH CONCURRENTLY
    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS mv_kg_stats_singleton
        ON mv_kg_stats ((1))
    """)

    # ==========================================================================
    # 2. Search Facets (for fast faceted search)
    # ==========================================================================
    op.execute("""
        CREATE MATERIALIZED VIEW IF NOT EXISTS mv_search_facets AS
        WITH
        author_counts AS (
            SELECT
                author,
                COUNT(*) AS passage_count
            FROM free_will.passages p
            JOIN free_will.ancient_works w ON p.work_id = w.id
            WHERE w.author IS NOT NULL
            GROUP BY author
        ),
        language_counts AS (
            SELECT
                COALESCE(language, 'unknown') AS language,
                COUNT(*) AS passage_count
            FROM free_will.passages p
            JOIN free_will.ancient_works w ON p.work_id = w.id
            GROUP BY language
        ),
        century_counts AS (
            SELECT
                COALESCE(FLOOR(date_start / 100)::text || 'c', 'unknown') AS century,
                COUNT(*) AS passage_count
            FROM free_will.passages p
            JOIN free_will.ancient_works w ON p.work_id = w.id
            GROUP BY FLOOR(date_start / 100)
        )
        SELECT
            'author' AS facet_type,
            author AS facet_value,
            passage_count AS count
        FROM author_counts
        WHERE passage_count > 0
        UNION ALL
        SELECT
            'language' AS facet_type,
            language AS facet_value,
            passage_count AS count
        FROM language_counts
        UNION ALL
        SELECT
            'century' AS facet_type,
            century AS facet_value,
            passage_count AS count
        FROM century_counts
        WITH DATA
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS mv_search_facets_type_idx
        ON mv_search_facets (facet_type)
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS mv_search_facets_value_idx
        ON mv_search_facets (facet_value)
    """)

    # ==========================================================================
    # 3. Author Network (influences, citations)
    # ==========================================================================
    op.execute("""
        CREATE MATERIALIZED VIEW IF NOT EXISTS mv_author_network AS
        SELECT
            n1.label AS source_author,
            n2.label AS target_author,
            e.relation,
            COUNT(*) AS connection_count
        FROM kg_edges e
        JOIN kg_nodes n1 ON e.source_id = n1.id
        JOIN kg_nodes n2 ON e.target_id = n2.id
        WHERE n1.node_type = 'person'
          AND n2.node_type = 'person'
          AND e.relation IN ('influenced', 'taught', 'cited', 'responded_to', 'critiqued')
        GROUP BY n1.label, n2.label, e.relation
        WITH DATA
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS mv_author_network_source_idx
        ON mv_author_network (source_author)
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS mv_author_network_target_idx
        ON mv_author_network (target_author)
    """)

    # ==========================================================================
    # 4. Concept Hierarchy
    # ==========================================================================
    op.execute("""
        CREATE MATERIALIZED VIEW IF NOT EXISTS mv_concept_hierarchy AS
        WITH RECURSIVE concept_tree AS (
            -- Base: concepts with no parent
            SELECT
                n.id,
                n.label,
                n.label AS root_concept,
                0 AS depth,
                ARRAY[n.id] AS path
            FROM kg_nodes n
            WHERE n.node_type = 'concept'
              AND NOT EXISTS (
                  SELECT 1 FROM kg_edges e
                  WHERE e.source_id = n.id
                    AND e.relation IN ('is_a', 'part_of', 'subtype_of')
              )

            UNION ALL

            -- Recursive: concepts with parents
            SELECT
                child.id,
                child.label,
                ct.root_concept,
                ct.depth + 1,
                ct.path || child.id
            FROM concept_tree ct
            JOIN kg_edges e ON e.target_id = ct.id
            JOIN kg_nodes child ON e.source_id = child.id
            WHERE child.node_type = 'concept'
              AND e.relation IN ('is_a', 'part_of', 'subtype_of')
              AND NOT (child.id = ANY(ct.path))  -- Prevent cycles
              AND ct.depth < 10  -- Limit depth
        )
        SELECT DISTINCT ON (id)
            id,
            label,
            root_concept,
            depth,
            path
        FROM concept_tree
        ORDER BY id, depth
        WITH DATA
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS mv_concept_hierarchy_root_idx
        ON mv_concept_hierarchy (root_concept)
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS mv_concept_hierarchy_depth_idx
        ON mv_concept_hierarchy (depth)
    """)

    # ==========================================================================
    # Create refresh function
    # ==========================================================================
    op.execute("""
        CREATE OR REPLACE FUNCTION refresh_materialized_views()
        RETURNS void AS $$
        BEGIN
            REFRESH MATERIALIZED VIEW CONCURRENTLY mv_kg_stats;
            REFRESH MATERIALIZED VIEW mv_search_facets;
            REFRESH MATERIALIZED VIEW mv_author_network;
            REFRESH MATERIALIZED VIEW mv_concept_hierarchy;
        END;
        $$ LANGUAGE plpgsql
    """)


def downgrade() -> None:
    """Remove materialized views."""
    op.execute("DROP FUNCTION IF EXISTS refresh_materialized_views()")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS mv_concept_hierarchy")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS mv_author_network")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS mv_search_facets")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS mv_kg_stats")
