-- EleutherIA production hardening
-- Step 1: persist the passage search vector so RPC search stops recomputing
-- to_tsvector(...) over every candidate row at runtime.

ALTER TABLE free_will.passages
    ADD COLUMN IF NOT EXISTS search_vector tsvector
    GENERATED ALWAYS AS (
        to_tsvector('english', COALESCE(text_content, ''))
    ) STORED;
