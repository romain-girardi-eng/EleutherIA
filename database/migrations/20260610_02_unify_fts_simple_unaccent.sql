-- G5 retrieval correctness — unify the FTS configuration.
--
-- Problem: three inconsistent configs coexisted —
--   * stored passages.search_vector used to_tsvector('english', ...) but no
--     runtime query ever matched it with an 'english' tsquery except the
--     Supabase RPC;
--   * hybrid_search.py and api/works.py recomputed to_tsvector('simple', ...)
--     at runtime, so the stored GIN index was never used (seq scans).
--
-- Fix: standardize on to_tsvector('simple', free_will.f_unaccent(text)).
-- 'simple' avoids English stemming, which is meaningless for Greek/Latin;
-- f_unaccent makes Greek search diacritic-insensitive on the index side
-- (display text is never altered). The stored generated column is
-- redefined and the GIN index recreated; the old 'english' vector and its
-- index are dropped with the column.
--
-- Deployment notes:
--   * Redefining the generated column rewrites free_will.passages (~69k
--     rows) and takes an exclusive lock for the duration — schedule
--     accordingly.
--   * Python code probes for free_will.f_unaccent and keeps the legacy
--     runtime expression until this migration is applied, so code and
--     migration can deploy in either order.
--   * free_will.search_passages_core is redefined INLINE below (last
--     statement) so the column and its query-side function change
--     atomically: an 'english'-stemmed tsquery against the new 'simple'
--     vector would silently return near-empty results ('causes'→'caus'
--     matches no unstemmed lexeme). database/schema/supabase_functions.sql
--     carries the same definition as the canonical copy for fresh installs
--     — keep the two in sync.
--   * database/schema/schema.sql still declares the old 'english' column
--     for fresh installs; migrations run after schema and converge it.

CREATE EXTENSION IF NOT EXISTS unaccent WITH SCHEMA extensions;

-- unaccent() is only STABLE; generated columns and expression indexes need
-- an IMMUTABLE callable. The wrapper pins the dictionary explicitly, which
-- is the standard safe pattern.
CREATE OR REPLACE FUNCTION free_will.f_unaccent(text)
RETURNS text
LANGUAGE sql
IMMUTABLE
PARALLEL SAFE
STRICT
SET search_path TO pg_catalog
AS $$
    SELECT extensions.unaccent('extensions.unaccent'::regdictionary, $1)
$$;

-- passage_search view depends on search_vector; recreate it around the
-- column swap.
DROP VIEW IF EXISTS free_will.passage_search;

ALTER TABLE free_will.passages DROP COLUMN IF EXISTS search_vector;

ALTER TABLE free_will.passages
    ADD COLUMN search_vector tsvector
    GENERATED ALWAYS AS (
        to_tsvector('simple', free_will.f_unaccent(COALESCE(text_content, '')))
    ) STORED;

-- The old GIN index was dropped together with the column; recreate it
-- under the same name so existing query plans and docs stay valid.
CREATE INDEX idx_passages_search_vector_gin
    ON free_will.passages
    USING gin (search_vector);

CREATE OR REPLACE VIEW free_will.passage_search AS
SELECT
    p.passage_id,
    p.work_id,
    p.canonical_ref,
    p.text_content,
    p.passage_role,
    p.source_passage_id,
    p.sequence_number,
    p.char_length,
    p.word_count,
    p.created_at,
    w.title,
    w.author,
    w.language,
    w.period,
    w.school,
    w.canonical_id AS work_canonical_id,
    p.search_vector
FROM free_will.passages p
JOIN free_will.ancient_works w ON p.work_id = w.work_id;

-- Query-side function updated atomically with the column: the RPC is the
-- one consistent user of the GIN index, and an 'english' tsquery against
-- the 'simple' vector would be a silent recall collapse, not an error.
-- Verbatim copy of database/schema/supabase_functions.sql (canonical).
CREATE OR REPLACE FUNCTION free_will.search_passages_core(
    p_query_text TEXT,
    p_max_results INTEGER DEFAULT 20,
    p_filter_author TEXT DEFAULT NULL,
    p_filter_period TEXT DEFAULT NULL,
    p_filter_language TEXT DEFAULT NULL
)
RETURNS TABLE (
    passage_id UUID,
    work_id UUID,
    canonical_ref TEXT,
    text_content TEXT,
    author TEXT,
    title TEXT,
    language TEXT,
    period TEXT,
    rank REAL
)
LANGUAGE sql
STABLE
SET search_path TO pg_catalog, free_will
AS $$
    WITH query_input AS (
        SELECT
            NULLIF(BTRIM(p_query_text), '') AS qtext,
            -- Must mirror the stored search_vector config:
            -- to_tsvector('simple', free_will.f_unaccent(text_content)).
            -- See migration 20260610_02_unify_fts_simple_unaccent.sql.
            plainto_tsquery(
                'simple',
                free_will.f_unaccent(NULLIF(BTRIM(p_query_text), ''))
            ) AS tsq
    ),
    ranked AS MATERIALIZED (
        SELECT
            p.passage_id,
            p.work_id,
            p.canonical_ref,
            ts_rank(p.search_vector, q.tsq) AS rank
        FROM free_will.passages p
        JOIN free_will.ancient_works w
          ON w.work_id = p.work_id
        CROSS JOIN query_input q
        WHERE q.qtext IS NOT NULL
          AND p.search_vector @@ q.tsq
          AND (p_filter_author IS NULL OR w.author ILIKE '%' || p_filter_author || '%')
          AND (p_filter_period IS NULL OR w.period = p_filter_period)
          AND (p_filter_language IS NULL OR w.language = p_filter_language)
        ORDER BY rank DESC, p.passage_id
        LIMIT LEAST(GREATEST(COALESCE(p_max_results, 20), 1), 100)
    )
    SELECT
        r.passage_id,
        r.work_id,
        r.canonical_ref,
        p.text_content,
        w.author,
        w.title,
        w.language,
        w.period,
        r.rank
    FROM ranked r
    JOIN free_will.passages p
      ON p.passage_id = r.passage_id
    JOIN free_will.ancient_works w
      ON w.work_id = r.work_id
    ORDER BY r.rank DESC, r.passage_id;
$$;

ANALYZE free_will.passages;
