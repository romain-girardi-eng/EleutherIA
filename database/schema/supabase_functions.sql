-- =============================================================================
-- EleutherIA — Supabase RPC Search Functions
-- =============================================================================
-- These are the public PostgREST wrappers used by the Cloudflare worker.
-- They keep RPC compatibility while ensuring the hot path uses the stored
-- `free_will.passages.search_vector` column and a stable GIN index.
--
-- Apply after `schema.sql`.
-- =============================================================================

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

CREATE OR REPLACE FUNCTION free_will.search_passages_simple_core(
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
    period TEXT
)
LANGUAGE sql
STABLE
SET search_path TO pg_catalog, free_will
AS $$
    WITH query_input AS (
        SELECT NULLIF(BTRIM(p_query_text), '') AS qtext
    )
    SELECT
        p.passage_id,
        p.work_id,
        p.canonical_ref,
        p.text_content,
        w.author,
        w.title,
        w.language,
        w.period
    FROM free_will.passages p
    JOIN free_will.ancient_works w
      ON w.work_id = p.work_id
    CROSS JOIN query_input q
    WHERE q.qtext IS NOT NULL
      AND (
          p.text_content ILIKE '%' || q.qtext || '%'
          OR p.canonical_ref ILIKE '%' || q.qtext || '%'
      )
      AND (p_filter_author IS NULL OR w.author ILIKE '%' || p_filter_author || '%')
      AND (p_filter_period IS NULL OR w.period = p_filter_period)
      AND (p_filter_language IS NULL OR w.language = p_filter_language)
    ORDER BY
        CASE
            WHEN p.canonical_ref ILIKE '%' || q.qtext || '%' THEN 0
            ELSE 1
        END,
        p.sequence_number,
        p.passage_id
    LIMIT LEAST(GREATEST(COALESCE(p_max_results, 20), 1), 100);
$$;

REVOKE ALL ON FUNCTION free_will.search_passages_core(TEXT, INTEGER, TEXT, TEXT, TEXT) FROM PUBLIC, anon, authenticated, service_role;
REVOKE ALL ON FUNCTION free_will.search_passages_simple_core(TEXT, INTEGER, TEXT, TEXT, TEXT) FROM PUBLIC, anon, authenticated, service_role;

CREATE OR REPLACE FUNCTION public.search_passages(
    query_text TEXT,
    max_results INTEGER DEFAULT 10
)
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
    FROM free_will.search_passages_core(query_text, max_results, NULL, NULL, NULL) sp;
$$;

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
            WHEN LOWER(COALESCE(payload ->> 'p_filter_language', payload ->> 'filter_language', payload ->> 'search_language', payload ->> 'language', '')) IN ('grc', 'lat', 'eng', 'hbo', 'ara')
                THEN LOWER(COALESCE(payload ->> 'p_filter_language', payload ->> 'filter_language', payload ->> 'search_language', payload ->> 'language'))
            ELSE NULL
        END
    ) sp;
$$;

CREATE OR REPLACE FUNCTION public.search_passages_simple(
    query_text TEXT,
    max_results INTEGER DEFAULT 10
)
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
    FROM free_will.search_passages_simple_core(query_text, max_results, NULL, NULL, NULL) sp;
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
            WHEN LOWER(COALESCE(payload ->> 'p_filter_language', payload ->> 'filter_language', payload ->> 'search_language', payload ->> 'language', '')) IN ('grc', 'lat', 'eng', 'hbo', 'ara')
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

CREATE OR REPLACE FUNCTION public.search_passages_filtered(
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
SECURITY INVOKER
SET search_path TO pg_catalog, free_will
AS $$
    SELECT *
    FROM free_will.search_passages_core(
        p_query_text,
        p_max_results,
        p_filter_author,
        p_filter_period,
        p_filter_language
    );
$$;

CREATE OR REPLACE FUNCTION public.search_passages_simple_filtered(
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
    period TEXT
)
LANGUAGE sql
STABLE
SECURITY INVOKER
SET search_path TO pg_catalog, free_will
AS $$
    SELECT *
    FROM free_will.search_passages_simple_core(
        p_query_text,
        p_max_results,
        p_filter_author,
        p_filter_period,
        p_filter_language
    );
$$;

CREATE OR REPLACE FUNCTION public.list_passage_refs(
    p_work_id UUID,
    p_limit INTEGER DEFAULT 1000,
    p_offset INTEGER DEFAULT 0
)
RETURNS TABLE (
    passage_id UUID,
    canonical_ref TEXT,
    sequence_number INTEGER,
    book TEXT,
    chapter TEXT,
    section TEXT
)
LANGUAGE sql
STABLE
SECURITY INVOKER
SET search_path TO pg_catalog, free_will
AS $$
    SELECT
        p.passage_id,
        p.canonical_ref,
        p.sequence_number,
        p.book,
        p.chapter,
        p.section
    FROM free_will.passages p
    WHERE p.work_id = p_work_id
    ORDER BY p.sequence_number, p.passage_id
    LIMIT LEAST(GREATEST(COALESCE(p_limit, 1000), 1), 10000)
    OFFSET GREATEST(COALESCE(p_offset, 0), 0);
$$;

CREATE OR REPLACE FUNCTION public.list_passages_window(
    p_work_id UUID,
    p_center_sequence INTEGER,
    p_window INTEGER DEFAULT 5
)
RETURNS SETOF free_will.passages
LANGUAGE sql
STABLE
SECURITY INVOKER
SET search_path TO pg_catalog, free_will
AS $$
    SELECT *
    FROM free_will.passages p
    WHERE p.work_id = p_work_id
      AND p.sequence_number >= GREATEST(
          COALESCE(p_center_sequence, 0) - LEAST(GREATEST(COALESCE(p_window, 5), 0), 50),
          0
      )
      AND p.sequence_number <= COALESCE(p_center_sequence, 0) + LEAST(GREATEST(COALESCE(p_window, 5), 0), 50)
    ORDER BY p.sequence_number, p.passage_id;
$$;

CREATE OR REPLACE FUNCTION public.count_passages_for_work(
    p_work_id UUID
)
RETURNS BIGINT
LANGUAGE sql
STABLE
SECURITY INVOKER
SET search_path TO pg_catalog, free_will
AS $$
    SELECT COUNT(*)::BIGINT
    FROM free_will.passages p
    WHERE p.work_id = p_work_id;
$$;

CREATE OR REPLACE FUNCTION public.get_best_passage_for_kg_node(
    p_kg_node_id TEXT
)
RETURNS TABLE (
    passage_id UUID
)
LANGUAGE sql
STABLE
SECURITY INVOKER
SET search_path TO pg_catalog, free_will
AS $$
    SELECT pc.passage_id
    FROM free_will.passage_citations pc
    WHERE pc.kg_node_id = p_kg_node_id
    ORDER BY pc.confidence DESC NULLS LAST, pc.passage_id
    LIMIT 1;
$$;

CREATE OR REPLACE FUNCTION public.get_work_kg_nodes(
    p_work_id UUID
)
RETURNS TABLE (
    kg_node_id TEXT,
    citation_count BIGINT,
    passage_ids UUID[],
    canonical_refs TEXT[],
    first_sequence INTEGER,
    first_passage_id UUID,
    first_canonical_ref TEXT
)
LANGUAGE sql
STABLE
SECURITY INVOKER
SET search_path TO pg_catalog, free_will
AS $$
    WITH ranked AS (
        SELECT
            pc.kg_node_id,
            p.passage_id,
            p.canonical_ref,
            p.sequence_number,
            ROW_NUMBER() OVER (
                PARTITION BY pc.kg_node_id
                ORDER BY p.sequence_number NULLS LAST, p.passage_id
            ) AS rn
        FROM free_will.passages p
        JOIN free_will.passage_citations pc
          ON pc.passage_id = p.passage_id
        WHERE p.work_id = p_work_id
    ),
    aggregated AS (
        SELECT
            r.kg_node_id,
            COUNT(*)::BIGINT AS citation_count,
            ARRAY_AGG(r.passage_id ORDER BY r.sequence_number NULLS LAST, r.passage_id) AS passage_ids,
            ARRAY_AGG(r.canonical_ref ORDER BY r.sequence_number NULLS LAST, r.passage_id) AS canonical_refs_all,
            MIN(r.sequence_number) AS first_sequence
        FROM ranked r
        GROUP BY r.kg_node_id
    )
    SELECT
        a.kg_node_id,
        a.citation_count,
        a.passage_ids,
        ARRAY_REMOVE(a.canonical_refs_all, NULL) AS canonical_refs,
        a.first_sequence,
        a.passage_ids[1] AS first_passage_id,
        a.canonical_refs_all[1] AS first_canonical_ref
    FROM aggregated a
    ORDER BY citation_count DESC, a.kg_node_id;
$$;

REVOKE ALL ON FUNCTION public.search_passages_filtered(TEXT, INTEGER, TEXT, TEXT, TEXT) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.search_passages_simple_filtered(TEXT, INTEGER, TEXT, TEXT, TEXT) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.list_passage_refs(UUID, INTEGER, INTEGER) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.list_passages_window(UUID, INTEGER, INTEGER) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.count_passages_for_work(UUID) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.get_best_passage_for_kg_node(TEXT) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.get_work_kg_nodes(UUID) FROM PUBLIC;

GRANT EXECUTE ON FUNCTION public.search_passages_filtered(TEXT, INTEGER, TEXT, TEXT, TEXT) TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.search_passages_simple_filtered(TEXT, INTEGER, TEXT, TEXT, TEXT) TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.list_passage_refs(UUID, INTEGER, INTEGER) TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.list_passages_window(UUID, INTEGER, INTEGER) TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.count_passages_for_work(UUID) TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.get_best_passage_for_kg_node(TEXT) TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.get_work_kg_nodes(UUID) TO anon, authenticated, service_role;

CREATE OR REPLACE FUNCTION public.list_work_kg_nodes(
    p_work_id UUID,
    p_limit INTEGER DEFAULT 1000,
    p_offset INTEGER DEFAULT 0
)
RETURNS TABLE (
    kg_node_id TEXT,
    citation_count BIGINT,
    passage_ids UUID[],
    canonical_refs TEXT[],
    first_sequence INTEGER,
    first_passage_id UUID,
    first_canonical_ref TEXT
)
LANGUAGE sql
STABLE
SECURITY INVOKER
SET search_path TO pg_catalog, free_will
AS $$
    WITH ranked AS (
        SELECT
            pc.kg_node_id,
            p.passage_id,
            p.canonical_ref,
            p.sequence_number
        FROM free_will.passages p
        JOIN free_will.passage_citations pc
          ON pc.passage_id = p.passage_id
        WHERE p.work_id = p_work_id
    ),
    aggregated AS (
        SELECT
            r.kg_node_id,
            COUNT(*)::BIGINT AS citation_count,
            ARRAY_AGG(r.passage_id ORDER BY r.sequence_number NULLS LAST, r.passage_id) AS passage_ids,
            ARRAY_AGG(r.canonical_ref ORDER BY r.sequence_number NULLS LAST, r.passage_id) AS canonical_refs_all,
            MIN(r.sequence_number) AS first_sequence
        FROM ranked r
        GROUP BY r.kg_node_id
    )
    SELECT
        a.kg_node_id,
        a.citation_count,
        a.passage_ids,
        ARRAY_REMOVE(a.canonical_refs_all, NULL) AS canonical_refs,
        a.first_sequence,
        a.passage_ids[1] AS first_passage_id,
        a.canonical_refs_all[1] AS first_canonical_ref
    FROM aggregated a
    ORDER BY a.first_sequence NULLS LAST, a.kg_node_id
    LIMIT LEAST(GREATEST(COALESCE(p_limit, 1000), 1), 5000)
    OFFSET GREATEST(COALESCE(p_offset, 0), 0);
$$;

REVOKE ALL ON FUNCTION public.list_work_kg_nodes(UUID, INTEGER, INTEGER) FROM PUBLIC;

GRANT EXECUTE ON FUNCTION public.list_work_kg_nodes(UUID, INTEGER, INTEGER) TO anon, authenticated, service_role;
