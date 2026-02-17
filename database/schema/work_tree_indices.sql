-- Work Tree Indices Schema
-- Supports the TreeIndexService (PageIndex-inspired hierarchical navigation).
--
-- Each ancient work is decomposed into a hierarchical tree of sections
-- (books → chapters → sections). The LLM uses this tree to navigate
-- and identify high-precision passage ranges before fetching full text.
--
-- Schema: free_will (configurable via ELEUTHERIA_DB_SCHEMA env var)

SET search_path TO free_will;

-- ---------------------------------------------------------------------------
-- work_tree_indices
--
-- One row per ancient work. The tree structure is stored as JSONB to
-- support arbitrary nesting depths without recursive table joins.
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS free_will.work_tree_indices (
    -- Primary key
    index_id        BIGSERIAL PRIMARY KEY,

    -- Work identity (FK to ancient_works.work_id)
    work_id         TEXT        NOT NULL,
    title           TEXT        NOT NULL,
    author          TEXT        NOT NULL,

    -- Metadata
    period          TEXT,                           -- e.g. "Hellenistic", "Republican"
    total_passages  INTEGER     NOT NULL DEFAULT 0, -- count of passages in this work

    -- Hierarchical tree (nested JSON: node_id, title, start_passage, end_passage, summary, nodes[])
    tree_json       JSONB       NOT NULL,

    -- Bookkeeping
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Unique constraint: one index per work
CREATE UNIQUE INDEX IF NOT EXISTS uq_work_tree_indices_work_id
    ON free_will.work_tree_indices (work_id);

-- Index for lookups by work_id (used in tree index loads)
CREATE INDEX IF NOT EXISTS idx_work_tree_indices_work_id
    ON free_will.work_tree_indices (work_id);

-- Index for listing by author / period
CREATE INDEX IF NOT EXISTS idx_work_tree_indices_author
    ON free_will.work_tree_indices (author);

CREATE INDEX IF NOT EXISTS idx_work_tree_indices_period
    ON free_will.work_tree_indices (period);

-- GIN index for JSONB full-text search within tree summaries
CREATE INDEX IF NOT EXISTS idx_work_tree_indices_tree_json_gin
    ON free_will.work_tree_indices USING GIN (tree_json);

-- ---------------------------------------------------------------------------
-- Trigger: auto-update updated_at on row change
-- ---------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION free_will.update_work_tree_indices_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_work_tree_indices_updated_at ON free_will.work_tree_indices;

CREATE TRIGGER trg_work_tree_indices_updated_at
    BEFORE UPDATE ON free_will.work_tree_indices
    FOR EACH ROW EXECUTE FUNCTION free_will.update_work_tree_indices_updated_at();

-- ---------------------------------------------------------------------------
-- Comments
-- ---------------------------------------------------------------------------

COMMENT ON TABLE free_will.work_tree_indices IS
    'Hierarchical tree index for each ancient work, enabling LLM-guided '
    'passage navigation (PageIndex-inspired TreeReasoningRetrieve node).';

COMMENT ON COLUMN free_will.work_tree_indices.tree_json IS
    'JSONB tree: {node_id, title, start_passage, end_passage, summary, nodes:[...]}. '
    'Unlimited nesting depth. Top-level nodes are books or major sections.';

COMMENT ON COLUMN free_will.work_tree_indices.total_passages IS
    'Total passage count cached here for quick range validation.';
