"""add_embedding_backup

Revision ID: 004_embeddings
Revises: 003_indexes
Create Date: 2025-02-04

Adds pgvector-based embedding backup table for PostgreSQL-native
vector storage. This complements Qdrant by providing:
- Backup storage for embeddings
- SQL-based vector search fallback
- Audit trail of embedding versions

Requires pgvector extension to be installed.
"""
from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '004_embeddings'
down_revision: str | Sequence[str] | None = '003_indexes'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add embedding backup tables with pgvector support."""

    # ==========================================================================
    # Enable pgvector extension (if available)
    # ==========================================================================
    # This will fail gracefully if pgvector is not installed
    op.execute("""
        DO $$
        BEGIN
            CREATE EXTENSION IF NOT EXISTS vector;
        EXCEPTION WHEN OTHERS THEN
            RAISE NOTICE 'pgvector extension not available, skipping vector columns';
        END $$
    """)

    # ==========================================================================
    # Passage Embeddings Table
    # ==========================================================================
    op.execute("""
        CREATE TABLE IF NOT EXISTS free_will.passage_embeddings (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            passage_id UUID NOT NULL REFERENCES free_will.passages(id) ON DELETE CASCADE,
            model_name VARCHAR(100) NOT NULL,
            model_version VARCHAR(50),
            embedding_dim INTEGER NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

            -- Constraints
            CONSTRAINT unique_passage_model UNIQUE (passage_id, model_name)
        )
    """)

    # Add vector column if pgvector is available
    op.execute("""
        DO $$
        BEGIN
            ALTER TABLE free_will.passage_embeddings
            ADD COLUMN IF NOT EXISTS embedding vector(3072);
        EXCEPTION WHEN OTHERS THEN
            RAISE NOTICE 'Could not add vector column, pgvector may not be installed';
        END $$
    """)

    # ==========================================================================
    # KG Node Embeddings Table
    # ==========================================================================
    op.execute("""
        CREATE TABLE IF NOT EXISTS kg_node_embeddings (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            node_id VARCHAR(255) NOT NULL REFERENCES kg_nodes(id) ON DELETE CASCADE,
            model_name VARCHAR(100) NOT NULL,
            model_version VARCHAR(50),
            embedding_dim INTEGER NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

            -- Constraints
            CONSTRAINT unique_node_model UNIQUE (node_id, model_name)
        )
    """)

    # Add vector column if pgvector is available
    op.execute("""
        DO $$
        BEGIN
            ALTER TABLE kg_node_embeddings
            ADD COLUMN IF NOT EXISTS embedding vector(3072);
        EXCEPTION WHEN OTHERS THEN
            RAISE NOTICE 'Could not add vector column, pgvector may not be installed';
        END $$
    """)

    # ==========================================================================
    # Embedding Models Registry
    # ==========================================================================
    op.execute("""
        CREATE TABLE IF NOT EXISTS embedding_models (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL UNIQUE,
            provider VARCHAR(50) NOT NULL,
            dimension INTEGER NOT NULL,
            is_active BOOLEAN DEFAULT true,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            metadata JSONB
        )
    """)

    # Insert default models
    op.execute("""
        INSERT INTO embedding_models (name, provider, dimension, metadata)
        VALUES
            ('text-embedding-3-large', 'openai', 3072, '{"max_tokens": 8191}'::jsonb),
            ('text-embedding-ada-002', 'openai', 1536, '{"max_tokens": 8191}'::jsonb),
            ('embed-multilingual-v3.0', 'cohere', 1024, '{"max_tokens": 512}'::jsonb)
        ON CONFLICT (name) DO NOTHING
    """)

    # ==========================================================================
    # Indexes for embedding tables
    # ==========================================================================
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_passage_embeddings_passage
        ON free_will.passage_embeddings (passage_id)
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_passage_embeddings_model
        ON free_will.passage_embeddings (model_name)
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_node_embeddings_node
        ON kg_node_embeddings (node_id)
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_node_embeddings_model
        ON kg_node_embeddings (model_name)
    """)

    # ==========================================================================
    # Vector similarity indexes (if pgvector available)
    # ==========================================================================
    # These use IVFFlat for approximate nearest neighbor search
    op.execute("""
        DO $$
        BEGIN
            -- Create IVFFlat index for passage embeddings
            CREATE INDEX IF NOT EXISTS idx_passage_embeddings_vector
            ON free_will.passage_embeddings
            USING ivfflat (embedding vector_cosine_ops)
            WITH (lists = 100);
        EXCEPTION WHEN OTHERS THEN
            RAISE NOTICE 'Could not create vector index, pgvector may not be installed';
        END $$
    """)

    op.execute("""
        DO $$
        BEGIN
            -- Create IVFFlat index for node embeddings
            CREATE INDEX IF NOT EXISTS idx_node_embeddings_vector
            ON kg_node_embeddings
            USING ivfflat (embedding vector_cosine_ops)
            WITH (lists = 50);
        EXCEPTION WHEN OTHERS THEN
            RAISE NOTICE 'Could not create vector index, pgvector may not be installed';
        END $$
    """)

    # ==========================================================================
    # Update trigger for timestamps
    # ==========================================================================
    op.execute("""
        CREATE OR REPLACE FUNCTION update_embedding_timestamp()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
    """)

    op.execute("""
        DROP TRIGGER IF EXISTS trigger_passage_embedding_timestamp
        ON free_will.passage_embeddings
    """)

    op.execute("""
        CREATE TRIGGER trigger_passage_embedding_timestamp
        BEFORE UPDATE ON free_will.passage_embeddings
        FOR EACH ROW EXECUTE FUNCTION update_embedding_timestamp()
    """)

    op.execute("""
        DROP TRIGGER IF EXISTS trigger_node_embedding_timestamp
        ON kg_node_embeddings
    """)

    op.execute("""
        CREATE TRIGGER trigger_node_embedding_timestamp
        BEFORE UPDATE ON kg_node_embeddings
        FOR EACH ROW EXECUTE FUNCTION update_embedding_timestamp()
    """)


def downgrade() -> None:
    """Remove embedding backup tables."""
    # Drop triggers
    op.execute("DROP TRIGGER IF EXISTS trigger_passage_embedding_timestamp ON free_will.passage_embeddings")
    op.execute("DROP TRIGGER IF EXISTS trigger_node_embedding_timestamp ON kg_node_embeddings")
    op.execute("DROP FUNCTION IF EXISTS update_embedding_timestamp()")

    # Drop tables
    op.execute("DROP TABLE IF EXISTS embedding_models")
    op.execute("DROP TABLE IF EXISTS kg_node_embeddings")
    op.execute("DROP TABLE IF EXISTS free_will.passage_embeddings")
