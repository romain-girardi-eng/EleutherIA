-- =============================================================================
-- EleutherIA — Supabase RPC Search Functions
-- =============================================================================
-- Optional optimized search functions for Supabase-hosted PostgreSQL.
-- These give 10-100x speedup over direct queries through pgbouncer by
-- executing server-side.
--
-- Local installs don't need these (HybridSearchService queries directly).
--
-- Usage: Run in Supabase Dashboard → SQL Editor after schema.sql.
-- =============================================================================

-- ---------------------------------------------------------------------------
-- search_passages: Full-text search with ts_vector ranking
-- ---------------------------------------------------------------------------
-- Called via Supabase RPC: supabase.rpc('search_passages', { query_text, ... })
--
CREATE OR REPLACE FUNCTION free_will.search_passages(
    query_text TEXT,
    max_results INTEGER DEFAULT 20,
    search_language TEXT DEFAULT NULL,
    filter_author TEXT DEFAULT NULL,
    filter_period TEXT DEFAULT NULL
)
RETURNS TABLE (
    passage_id UUID,
    work_id UUID,
    canonical_ref TEXT,
    text_content TEXT,
    title TEXT,
    author TEXT,
    language TEXT,
    period TEXT,
    rank REAL,
    snippet TEXT
)
LANGUAGE plpgsql STABLE
SET search_path = free_will, public
AS $$
DECLARE
    ts_config REGCONFIG;
BEGIN
    -- Pick text-search config: default to 'simple' for Greek/Latin
    ts_config := COALESCE(search_language, 'simple')::REGCONFIG;

    RETURN QUERY
    SELECT
        p.passage_id,
        p.work_id,
        p.canonical_ref,
        p.text_content,
        w.title,
        w.author,
        w.language,
        w.period,
        ts_rank(
            to_tsvector(ts_config, p.text_content),
            plainto_tsquery(ts_config, query_text)
        ) AS rank,
        ts_headline(
            ts_config::TEXT,
            p.text_content,
            plainto_tsquery(ts_config, query_text),
            'MaxWords=50, MinWords=20'
        ) AS snippet
    FROM free_will.passages p
    JOIN free_will.ancient_works w ON p.work_id = w.work_id
    WHERE
        to_tsvector(ts_config, p.text_content) @@ plainto_tsquery(ts_config, query_text)
        AND (filter_author IS NULL OR w.author ILIKE '%' || filter_author || '%')
        AND (filter_period IS NULL OR w.period = filter_period)
    ORDER BY rank DESC
    LIMIT max_results;
END;
$$;

-- ---------------------------------------------------------------------------
-- search_passages_simple: ILIKE fallback for exact substring matching
-- ---------------------------------------------------------------------------
-- Slower but works when ts_vector misses transliterated Greek/Latin terms.
--
CREATE OR REPLACE FUNCTION free_will.search_passages_simple(
    query_text TEXT,
    max_results INTEGER DEFAULT 20
)
RETURNS TABLE (
    passage_id UUID,
    work_id UUID,
    canonical_ref TEXT,
    text_content TEXT,
    title TEXT,
    author TEXT,
    language TEXT
)
LANGUAGE plpgsql STABLE
SET search_path = free_will, public
AS $$
BEGIN
    RETURN QUERY
    SELECT
        p.passage_id,
        p.work_id,
        p.canonical_ref,
        p.text_content,
        w.title,
        w.author,
        w.language
    FROM free_will.passages p
    JOIN free_will.ancient_works w ON p.work_id = w.work_id
    WHERE p.text_content ILIKE '%' || query_text || '%'
    LIMIT max_results;
END;
$$;

-- ---------------------------------------------------------------------------
-- Permissions: allow Supabase anonymous and authenticated roles to call these
-- ---------------------------------------------------------------------------
GRANT EXECUTE ON FUNCTION free_will.search_passages TO anon, authenticated;
GRANT EXECUTE ON FUNCTION free_will.search_passages_simple TO anon, authenticated;
