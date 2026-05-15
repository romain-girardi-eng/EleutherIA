-- query_traces public gallery: expose the community Q&A endpoints
--
-- Adds:
--   * is_public flag (default true)
--   * stable, URL-friendly share_slug (12-char lowercase hex from trace_id)
--   * topic_tags array for filtering by period / philosopher
--   * indexes for the two new read endpoints
--   * BEFORE INSERT trigger so new rows always get a slug without touching
--     trace_writer.py
--
-- Wired in by backend/routes/community.py — see
-- GET /api/graphrag/community/queries  and
-- GET /api/graphrag/community/queries/{slug}

SET search_path = free_will;

ALTER TABLE free_will.query_traces
    ADD COLUMN IF NOT EXISTS is_public boolean NOT NULL DEFAULT true,
    ADD COLUMN IF NOT EXISTS share_slug text UNIQUE,
    ADD COLUMN IF NOT EXISTS topic_tags text[] NOT NULL DEFAULT ARRAY[]::text[];

-- Backfill share_slug for all existing rows: 12-char lowercase hex from
-- the trace_id uuid (first 12 chars, stripped of dashes).
UPDATE free_will.query_traces
SET share_slug = substr(lower(translate(trace_id::text, '-', '')), 1, 12)
WHERE share_slug IS NULL;

-- Make the slug NOT NULL going forward.
ALTER TABLE free_will.query_traces
    ALTER COLUMN share_slug SET NOT NULL;

CREATE INDEX IF NOT EXISTS idx_query_traces_is_public_started_at
    ON free_will.query_traces(is_public, started_at DESC)
    WHERE is_public = true;

CREATE INDEX IF NOT EXISTS idx_query_traces_topic_tags
    ON free_will.query_traces USING gin (topic_tags);

-- BEFORE INSERT trigger so trace_writer.py keeps working unmodified: any new
-- trace lands with a stable, URL-safe slug derived from its uuid.
CREATE OR REPLACE FUNCTION free_will.auto_query_trace_slug() RETURNS trigger AS $$
BEGIN
    IF NEW.share_slug IS NULL THEN
        NEW.share_slug := substr(lower(translate(NEW.trace_id::text, '-', '')), 1, 12);
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS query_traces_autoslug ON free_will.query_traces;
CREATE TRIGGER query_traces_autoslug BEFORE INSERT ON free_will.query_traces
    FOR EACH ROW EXECUTE FUNCTION free_will.auto_query_trace_slug();
