-- EleutherIA production hardening
-- Step 2: create the online indexes needed by the new RPC fast path.
-- Apply this file outside a transaction because it uses CONCURRENTLY.

CREATE EXTENSION IF NOT EXISTS pg_trgm WITH SCHEMA extensions;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_passages_search_vector_gin
    ON free_will.passages
    USING gin (search_vector);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_passages_text_content_trgm
    ON free_will.passages
    USING gin (text_content extensions.gin_trgm_ops);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_passages_canonical_ref_trgm
    ON free_will.passages
    USING gin (canonical_ref extensions.gin_trgm_ops);

ANALYZE free_will.passages;
