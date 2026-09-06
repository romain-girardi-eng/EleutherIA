-- French is a language of published translations of ancient works, not English.
-- Preserve conventional loci and the existing role/citation constraints.
BEGIN;
SET LOCAL lock_timeout = '10s';
ALTER TABLE free_will.ancient_works
    DROP CONSTRAINT IF EXISTS ancient_works_language_check,
    ADD CONSTRAINT ancient_works_language_check
        CHECK (language IN ('grc', 'lat', 'eng', 'fra', 'hbo', 'ara'));

CREATE OR REPLACE FUNCTION public.search_passages(payload JSONB)
RETURNS TABLE (
    passage_id UUID,
    work_id UUID,
    canonical_ref TEXT,
    text_content TEXT,
    author TEXT,
    title TEXT,
    rank REAL
)
LANGUAGE sql
STABLE
SECURITY INVOKER
SET search_path TO pg_catalog, free_will
AS $$
    SELECT
        sp.passage_id,
        sp.work_id,
        sp.canonical_ref,
        sp.text_content,
        sp.author,
        sp.title,
        sp.rank
    FROM free_will.search_passages_core(
        COALESCE(
            NULLIF(BTRIM(payload ->> 'query_text'), ''),
            NULLIF(BTRIM(payload ->> 'p_query_text'), ''),
            NULLIF(BTRIM(payload ->> 'queryText'), ''),
            NULLIF(BTRIM(payload ->> 'q'), ''),
            NULLIF(BTRIM(payload ->> 'query'), ''),
            NULLIF(BTRIM(payload ->> 'search_query'), '')
        ),
        CASE
            WHEN COALESCE(payload ->> 'max_results', payload ->> 'p_max_results', payload ->> 'maxResults', payload ->> 'limit') ~ '^[0-9]+$'
                THEN COALESCE(payload ->> 'max_results', payload ->> 'p_max_results', payload ->> 'maxResults', payload ->> 'limit')::INTEGER
            ELSE 10
        END,
        COALESCE(
            NULLIF(BTRIM(payload ->> 'p_filter_author'), ''),
            NULLIF(BTRIM(payload ->> 'filter_author'), ''),
            NULLIF(BTRIM(payload ->> 'author'), '')
        ),
        COALESCE(
            NULLIF(BTRIM(payload ->> 'p_filter_period'), ''),
            NULLIF(BTRIM(payload ->> 'filter_period'), ''),
            NULLIF(BTRIM(payload ->> 'period'), '')
        ),
        CASE
            WHEN LOWER(COALESCE(payload ->> 'p_filter_language', payload ->> 'filter_language', payload ->> 'search_language', payload ->> 'language', '')) IN ('grc', 'lat', 'eng', 'fra', 'hbo', 'ara')
                THEN LOWER(COALESCE(payload ->> 'p_filter_language', payload ->> 'filter_language', payload ->> 'search_language', payload ->> 'language'))
            ELSE NULL
        END
    ) sp;
$$;

CREATE OR REPLACE FUNCTION public.search_passages_simple(payload JSONB)
RETURNS TABLE (
    passage_id UUID,
    work_id UUID,
    canonical_ref TEXT,
    text_content TEXT,
    author TEXT,
    title TEXT
)
LANGUAGE sql
STABLE
SECURITY INVOKER
SET search_path TO pg_catalog, free_will
AS $$
    SELECT
        sp.passage_id,
        sp.work_id,
        sp.canonical_ref,
        sp.text_content,
        sp.author,
        sp.title
    FROM free_will.search_passages_simple_core(
        COALESCE(
            NULLIF(BTRIM(payload ->> 'query_text'), ''),
            NULLIF(BTRIM(payload ->> 'p_query_text'), ''),
            NULLIF(BTRIM(payload ->> 'queryText'), ''),
            NULLIF(BTRIM(payload ->> 'q'), ''),
            NULLIF(BTRIM(payload ->> 'query'), ''),
            NULLIF(BTRIM(payload ->> 'search_query'), '')
        ),
        CASE
            WHEN COALESCE(payload ->> 'max_results', payload ->> 'p_max_results', payload ->> 'maxResults', payload ->> 'limit') ~ '^[0-9]+$'
                THEN COALESCE(payload ->> 'max_results', payload ->> 'p_max_results', payload ->> 'maxResults', payload ->> 'limit')::INTEGER
            ELSE 10
        END,
        COALESCE(
            NULLIF(BTRIM(payload ->> 'p_filter_author'), ''),
            NULLIF(BTRIM(payload ->> 'filter_author'), ''),
            NULLIF(BTRIM(payload ->> 'author'), '')
        ),
        COALESCE(
            NULLIF(BTRIM(payload ->> 'p_filter_period'), ''),
            NULLIF(BTRIM(payload ->> 'filter_period'), ''),
            NULLIF(BTRIM(payload ->> 'period'), '')
        ),
        CASE
            WHEN LOWER(COALESCE(payload ->> 'p_filter_language', payload ->> 'filter_language', payload ->> 'search_language', payload ->> 'language', '')) IN ('grc', 'lat', 'eng', 'fra', 'hbo', 'ara')
                THEN LOWER(COALESCE(payload ->> 'p_filter_language', payload ->> 'filter_language', payload ->> 'search_language', payload ->> 'language'))
            ELSE NULL
        END
    ) sp;
$$;

REVOKE ALL ON FUNCTION public.search_passages(TEXT, INTEGER) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.search_passages(JSONB) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.search_passages_simple(TEXT, INTEGER) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.search_passages_simple(JSONB) FROM PUBLIC;

GRANT EXECUTE ON FUNCTION public.search_passages(TEXT, INTEGER) TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.search_passages(JSONB) TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.search_passages_simple(TEXT, INTEGER) TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.search_passages_simple(JSONB) TO anon, authenticated, service_role;


COMMIT;
