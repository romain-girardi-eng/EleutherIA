-- EleutherIA production hardening
-- Step 3: replace the slow / unsafe RPC implementations and tighten exposure.

-- ---------------------------------------------------------------------------
-- Search RPC internals
-- ---------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION free_will.search_passages_core(
    p_query_text text,
    p_max_results integer DEFAULT 20,
    p_filter_author text DEFAULT NULL,
    p_filter_period text DEFAULT NULL,
    p_filter_language text DEFAULT NULL
)
RETURNS TABLE (
    passage_id uuid,
    work_id uuid,
    canonical_ref text,
    text_content text,
    author text,
    title text,
    language text,
    period text,
    rank real
)
LANGUAGE sql
STABLE
SET search_path TO pg_catalog, free_will
AS $$
    WITH query_input AS (
        SELECT
            NULLIF(BTRIM(p_query_text), '') AS qtext,
            plainto_tsquery('english', NULLIF(BTRIM(p_query_text), '')) AS tsq
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
    p_query_text text,
    p_max_results integer DEFAULT 20,
    p_filter_author text DEFAULT NULL,
    p_filter_period text DEFAULT NULL,
    p_filter_language text DEFAULT NULL
)
RETURNS TABLE (
    passage_id uuid,
    work_id uuid,
    canonical_ref text,
    text_content text,
    author text,
    title text,
    language text,
    period text
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

REVOKE ALL ON FUNCTION free_will.search_passages_core(text, integer, text, text, text) FROM PUBLIC, anon, authenticated, service_role;
REVOKE ALL ON FUNCTION free_will.search_passages_simple_core(text, integer, text, text, text) FROM PUBLIC, anon, authenticated, service_role;

-- ---------------------------------------------------------------------------
-- Critical search RPCs exposed through PostgREST
-- ---------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION public.search_passages(
    query_text text,
    max_results integer DEFAULT 10
)
RETURNS TABLE (
    passage_id uuid,
    work_id uuid,
    canonical_ref text,
    text_content text,
    author text,
    title text,
    rank real
)
LANGUAGE sql
STABLE
SECURITY DEFINER
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

CREATE OR REPLACE FUNCTION public.search_passages(payload jsonb)
RETURNS TABLE (
    passage_id uuid,
    work_id uuid,
    canonical_ref text,
    text_content text,
    author text,
    title text,
    rank real
)
LANGUAGE sql
STABLE
SECURITY DEFINER
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
                THEN COALESCE(payload ->> 'max_results', payload ->> 'p_max_results', payload ->> 'maxResults', payload ->> 'limit')::integer
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
    query_text text,
    max_results integer DEFAULT 10
)
RETURNS TABLE (
    passage_id uuid,
    work_id uuid,
    canonical_ref text,
    text_content text,
    author text,
    title text
)
LANGUAGE sql
STABLE
SECURITY DEFINER
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

CREATE OR REPLACE FUNCTION public.search_passages_simple(payload jsonb)
RETURNS TABLE (
    passage_id uuid,
    work_id uuid,
    canonical_ref text,
    text_content text,
    author text,
    title text
)
LANGUAGE sql
STABLE
SECURITY DEFINER
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
                THEN COALESCE(payload ->> 'max_results', payload ->> 'p_max_results', payload ->> 'maxResults', payload ->> 'limit')::integer
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

-- ---------------------------------------------------------------------------
-- Listing / lookup RPCs
-- ---------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION free_will.count_ancient_works(
    p_author text DEFAULT NULL,
    p_language text DEFAULT NULL
)
RETURNS bigint
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path TO pg_catalog, free_will
AS $$
    SELECT COUNT(*)::bigint
    FROM free_will.ancient_works aw
    WHERE (p_author IS NULL OR aw.author ILIKE '%' || p_author || '%')
      AND (p_language IS NULL OR aw.language ILIKE p_language);
$$;

CREATE OR REPLACE FUNCTION public.count_ancient_works(
    p_author text DEFAULT NULL,
    p_language text DEFAULT NULL
)
RETURNS bigint
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path TO pg_catalog, free_will
AS $$
    SELECT COUNT(*)::bigint
    FROM free_will.ancient_works aw
    WHERE (p_author IS NULL OR aw.author ILIKE '%' || p_author || '%')
      AND (p_language IS NULL OR aw.language ILIKE p_language);
$$;

CREATE OR REPLACE FUNCTION public.count_ancient_works(payload jsonb)
RETURNS bigint
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path TO pg_catalog, free_will
AS $$
    SELECT public.count_ancient_works(
        COALESCE(
            NULLIF(BTRIM(payload ->> 'p_author'), ''),
            NULLIF(BTRIM(payload ->> 'author'), '')
        ),
        COALESCE(
            NULLIF(BTRIM(payload ->> 'p_language'), ''),
            NULLIF(BTRIM(payload ->> 'language'), '')
        )
    );
$$;

CREATE OR REPLACE FUNCTION free_will.list_ancient_works(
    p_author text DEFAULT NULL,
    p_language text DEFAULT NULL,
    p_sort_by text DEFAULT 'author',
    p_limit integer DEFAULT 50,
    p_offset integer DEFAULT 0
)
RETURNS TABLE (
    id uuid,
    work_id uuid,
    kg_work_id text,
    canonical_id text,
    title text,
    title_original text,
    author text,
    author_original text,
    language text,
    period text,
    date_composed text,
    school text,
    source text,
    source_url text,
    license text,
    division_scheme text,
    total_divisions integer,
    total_words integer,
    total_chars integer,
    notes text,
    metadata jsonb,
    created_at timestamptz,
    updated_at timestamptz,
    citation_count bigint
)
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
SET search_path TO pg_catalog, free_will
AS $$
DECLARE
    v_sort_by text := COALESCE(NULLIF(p_sort_by, ''), 'author');
    v_limit integer := LEAST(GREATEST(COALESCE(p_limit, 50), 1), 200);
    v_offset integer := GREATEST(COALESCE(p_offset, 0), 0);
BEGIN
    IF v_sort_by = 'most_cited' THEN
        RETURN QUERY
        WITH citation_counts AS MATERIALIZED (
            SELECT
                p.work_id,
                COUNT(DISTINCT pc.kg_node_id) AS citation_count
            FROM free_will.passages p
            JOIN free_will.passage_citations pc
              ON pc.passage_id = p.passage_id
            GROUP BY p.work_id
        ),
        filtered AS MATERIALIZED (
            SELECT
                aw.work_id AS id,
                aw.work_id,
                aw.kg_work_id,
                aw.canonical_id,
                aw.title,
                aw.title_original,
                aw.author,
                aw.author_original,
                aw.language,
                aw.period,
                aw.date_composed,
                aw.school,
                aw.source,
                aw.source_url,
                aw.license,
                aw.division_scheme,
                aw.total_divisions,
                aw.total_words,
                aw.total_chars,
                aw.notes,
                aw.metadata,
                aw.created_at,
                aw.updated_at,
                COALESCE(cc.citation_count, 0) AS citation_count
            FROM free_will.ancient_works aw
            LEFT JOIN citation_counts cc
              ON cc.work_id = aw.work_id
            WHERE (p_author IS NULL OR aw.author ILIKE '%' || p_author || '%')
              AND (p_language IS NULL OR aw.language ILIKE p_language)
        )
        SELECT *
        FROM filtered
        ORDER BY citation_count DESC, author ASC, title ASC
        LIMIT v_limit
        OFFSET v_offset;
    ELSE
        RETURN QUERY
        WITH filtered AS MATERIALIZED (
            SELECT
                aw.work_id,
                aw.kg_work_id,
                aw.canonical_id,
                aw.title,
                aw.title_original,
                aw.author,
                aw.author_original,
                aw.language,
                aw.period,
                aw.date_composed,
                aw.school,
                aw.source,
                aw.source_url,
                aw.license,
                aw.division_scheme,
                aw.total_divisions,
                aw.total_words,
                aw.total_chars,
                aw.notes,
                aw.metadata,
                aw.created_at,
                aw.updated_at
            FROM free_will.ancient_works aw
            WHERE (p_author IS NULL OR aw.author ILIKE '%' || p_author || '%')
              AND (p_language IS NULL OR aw.language ILIKE p_language)
            ORDER BY
                CASE
                    WHEN v_sort_by = 'title' THEN aw.title
                    ELSE aw.author
                END ASC,
                CASE
                    WHEN v_sort_by = 'title' THEN aw.author
                    ELSE aw.title
                END ASC
            LIMIT v_limit
            OFFSET v_offset
        ),
        citation_counts AS MATERIALIZED (
            SELECT
                p.work_id,
                COUNT(DISTINCT pc.kg_node_id) AS citation_count
            FROM filtered f
            JOIN free_will.passages p
              ON p.work_id = f.work_id
            JOIN free_will.passage_citations pc
              ON pc.passage_id = p.passage_id
            GROUP BY p.work_id
        )
        SELECT
            f.work_id AS id,
            f.work_id,
            f.kg_work_id,
            f.canonical_id,
            f.title,
            f.title_original,
            f.author,
            f.author_original,
            f.language,
            f.period,
            f.date_composed,
            f.school,
            f.source,
            f.source_url,
            f.license,
            f.division_scheme,
            f.total_divisions,
            f.total_words,
            f.total_chars,
            f.notes,
            f.metadata,
            f.created_at,
            f.updated_at,
            COALESCE(cc.citation_count, 0) AS citation_count
        FROM filtered f
        LEFT JOIN citation_counts cc
          ON cc.work_id = f.work_id
        ORDER BY
            CASE
                WHEN v_sort_by = 'title' THEN f.title
                ELSE f.author
            END ASC,
            CASE
                WHEN v_sort_by = 'title' THEN f.author
                ELSE f.title
            END ASC;
    END IF;
END;
$$;

CREATE OR REPLACE FUNCTION public.list_ancient_works(
    p_author text DEFAULT NULL,
    p_language text DEFAULT NULL,
    p_sort_by text DEFAULT 'author',
    p_limit integer DEFAULT 50,
    p_offset integer DEFAULT 0
)
RETURNS TABLE (
    id uuid,
    work_id uuid,
    kg_work_id text,
    canonical_id text,
    title text,
    title_original text,
    author text,
    author_original text,
    language text,
    period text,
    date_composed text,
    school text,
    source text,
    source_url text,
    license text,
    division_scheme text,
    total_divisions integer,
    total_words integer,
    total_chars integer,
    notes text,
    metadata jsonb,
    created_at timestamptz,
    updated_at timestamptz,
    citation_count bigint
)
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
SET search_path TO pg_catalog, free_will
AS $$
DECLARE
    v_sort_by text := COALESCE(NULLIF(p_sort_by, ''), 'author');
    v_limit integer := LEAST(GREATEST(COALESCE(p_limit, 50), 1), 200);
    v_offset integer := GREATEST(COALESCE(p_offset, 0), 0);
BEGIN
    IF v_sort_by = 'most_cited' THEN
        RETURN QUERY
        WITH citation_counts AS MATERIALIZED (
            SELECT
                p.work_id,
                COUNT(DISTINCT pc.kg_node_id) AS citation_count
            FROM free_will.passages p
            JOIN free_will.passage_citations pc
              ON pc.passage_id = p.passage_id
            GROUP BY p.work_id
        ),
        filtered AS MATERIALIZED (
            SELECT
                aw.work_id AS id,
                aw.work_id,
                aw.kg_work_id,
                aw.canonical_id,
                aw.title,
                aw.title_original,
                aw.author,
                aw.author_original,
                aw.language,
                aw.period,
                aw.date_composed,
                aw.school,
                aw.source,
                aw.source_url,
                aw.license,
                aw.division_scheme,
                aw.total_divisions,
                aw.total_words,
                aw.total_chars,
                aw.notes,
                aw.metadata,
                aw.created_at,
                aw.updated_at,
                COALESCE(cc.citation_count, 0) AS citation_count
            FROM free_will.ancient_works aw
            LEFT JOIN citation_counts cc
              ON cc.work_id = aw.work_id
            WHERE (p_author IS NULL OR aw.author ILIKE '%' || p_author || '%')
              AND (p_language IS NULL OR aw.language ILIKE p_language)
        )
        SELECT *
        FROM filtered
        ORDER BY citation_count DESC, author ASC, title ASC
        LIMIT v_limit
        OFFSET v_offset;
    ELSE
        RETURN QUERY
        WITH filtered AS MATERIALIZED (
            SELECT
                aw.work_id,
                aw.kg_work_id,
                aw.canonical_id,
                aw.title,
                aw.title_original,
                aw.author,
                aw.author_original,
                aw.language,
                aw.period,
                aw.date_composed,
                aw.school,
                aw.source,
                aw.source_url,
                aw.license,
                aw.division_scheme,
                aw.total_divisions,
                aw.total_words,
                aw.total_chars,
                aw.notes,
                aw.metadata,
                aw.created_at,
                aw.updated_at
            FROM free_will.ancient_works aw
            WHERE (p_author IS NULL OR aw.author ILIKE '%' || p_author || '%')
              AND (p_language IS NULL OR aw.language ILIKE p_language)
            ORDER BY
                CASE
                    WHEN v_sort_by = 'title' THEN aw.title
                    ELSE aw.author
                END ASC,
                CASE
                    WHEN v_sort_by = 'title' THEN aw.author
                    ELSE aw.title
                END ASC
            LIMIT v_limit
            OFFSET v_offset
        ),
        citation_counts AS MATERIALIZED (
            SELECT
                p.work_id,
                COUNT(DISTINCT pc.kg_node_id) AS citation_count
            FROM filtered f
            JOIN free_will.passages p
              ON p.work_id = f.work_id
            JOIN free_will.passage_citations pc
              ON pc.passage_id = p.passage_id
            GROUP BY p.work_id
        )
        SELECT
            f.work_id AS id,
            f.work_id,
            f.kg_work_id,
            f.canonical_id,
            f.title,
            f.title_original,
            f.author,
            f.author_original,
            f.language,
            f.period,
            f.date_composed,
            f.school,
            f.source,
            f.source_url,
            f.license,
            f.division_scheme,
            f.total_divisions,
            f.total_words,
            f.total_chars,
            f.notes,
            f.metadata,
            f.created_at,
            f.updated_at,
            COALESCE(cc.citation_count, 0) AS citation_count
        FROM filtered f
        LEFT JOIN citation_counts cc
          ON cc.work_id = f.work_id
        ORDER BY
            CASE
                WHEN v_sort_by = 'title' THEN f.title
                ELSE f.author
            END ASC,
            CASE
                WHEN v_sort_by = 'title' THEN f.author
                ELSE f.title
            END ASC;
    END IF;
END;
$$;

CREATE OR REPLACE FUNCTION public.list_ancient_works(payload jsonb)
RETURNS TABLE (
    id uuid,
    work_id uuid,
    kg_work_id text,
    canonical_id text,
    title text,
    title_original text,
    author text,
    author_original text,
    language text,
    period text,
    date_composed text,
    school text,
    source text,
    source_url text,
    license text,
    division_scheme text,
    total_divisions integer,
    total_words integer,
    total_chars integer,
    notes text,
    metadata jsonb,
    created_at timestamptz,
    updated_at timestamptz,
    citation_count bigint
)
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path TO pg_catalog, free_will
AS $$
    SELECT *
    FROM public.list_ancient_works(
        COALESCE(
            NULLIF(BTRIM(payload ->> 'p_author'), ''),
            NULLIF(BTRIM(payload ->> 'author'), '')
        ),
        COALESCE(
            NULLIF(BTRIM(payload ->> 'p_language'), ''),
            NULLIF(BTRIM(payload ->> 'language'), '')
        ),
        COALESCE(
            NULLIF(BTRIM(payload ->> 'p_sort_by'), ''),
            NULLIF(BTRIM(payload ->> 'sort_by'), ''),
            'author'
        ),
        CASE
            WHEN COALESCE(payload ->> 'p_limit', payload ->> 'limit') ~ '^[0-9]+$'
                THEN COALESCE(payload ->> 'p_limit', payload ->> 'limit')::integer
            ELSE 50
        END,
        CASE
            WHEN COALESCE(payload ->> 'p_offset', payload ->> 'offset') ~ '^[0-9]+$'
                THEN COALESCE(payload ->> 'p_offset', payload ->> 'offset')::integer
            ELSE 0
        END
    );
$$;

CREATE OR REPLACE FUNCTION free_will.get_ancient_work(
    p_work_id uuid
)
RETURNS TABLE (
    id uuid,
    work_id uuid,
    kg_work_id text,
    canonical_id text,
    title text,
    title_original text,
    author text,
    author_original text,
    language text,
    period text,
    date_composed text,
    school text,
    full_text text,
    full_text_normalized text,
    tei_xml text,
    source text,
    source_url text,
    license text,
    division_scheme text,
    total_divisions integer,
    total_words integer,
    total_chars integer,
    notes text,
    metadata jsonb,
    created_at timestamptz,
    updated_at timestamptz
)
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path TO pg_catalog, free_will
AS $$
    SELECT
        aw.work_id AS id,
        aw.work_id,
        aw.kg_work_id,
        aw.canonical_id,
        aw.title,
        aw.title_original,
        aw.author,
        aw.author_original,
        aw.language,
        aw.period,
        aw.date_composed,
        aw.school,
        aw.full_text,
        NULL::text AS full_text_normalized,
        aw.tei_xml,
        aw.source,
        aw.source_url,
        aw.license,
        aw.division_scheme,
        aw.total_divisions,
        aw.total_words,
        aw.total_chars,
        aw.notes,
        aw.metadata,
        aw.created_at,
        aw.updated_at
    FROM free_will.ancient_works aw
    WHERE aw.work_id = p_work_id;
$$;

CREATE OR REPLACE FUNCTION free_will.get_ancient_work_by_kg_id(
    p_kg_work_id text
)
RETURNS TABLE (
    id uuid,
    work_id uuid,
    kg_work_id text,
    canonical_id text,
    title text,
    title_original text,
    author text,
    author_original text,
    language text,
    period text,
    date_composed text,
    school text,
    full_text text,
    full_text_normalized text,
    tei_xml text,
    source text,
    source_url text,
    license text,
    division_scheme text,
    total_divisions integer,
    total_words integer,
    total_chars integer,
    notes text,
    metadata jsonb,
    created_at timestamptz,
    updated_at timestamptz
)
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path TO pg_catalog, free_will
AS $$
    SELECT
        aw.work_id AS id,
        aw.work_id,
        aw.kg_work_id,
        aw.canonical_id,
        aw.title,
        aw.title_original,
        aw.author,
        aw.author_original,
        aw.language,
        aw.period,
        aw.date_composed,
        aw.school,
        aw.full_text,
        NULL::text AS full_text_normalized,
        aw.tei_xml,
        aw.source,
        aw.source_url,
        aw.license,
        aw.division_scheme,
        aw.total_divisions,
        aw.total_words,
        aw.total_chars,
        aw.notes,
        aw.metadata,
        aw.created_at,
        aw.updated_at
    FROM free_will.ancient_works aw
    WHERE aw.kg_work_id = p_kg_work_id;
$$;

CREATE OR REPLACE FUNCTION public.list_passages(
    p_work_id uuid,
    p_book text DEFAULT NULL,
    p_chapter text DEFAULT NULL,
    p_section text DEFAULT NULL,
    p_limit integer DEFAULT 100,
    p_offset integer DEFAULT 0
)
RETURNS SETOF free_will.passages
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path TO pg_catalog, free_will
AS $$
    SELECT *
    FROM free_will.passages
    WHERE work_id = p_work_id
      AND (p_book IS NULL OR book = p_book)
      AND (p_chapter IS NULL OR chapter = p_chapter)
      AND (p_section IS NULL OR section = p_section)
    ORDER BY sequence_number
    LIMIT LEAST(GREATEST(COALESCE(p_limit, 100), 1), 500)
    OFFSET GREATEST(COALESCE(p_offset, 0), 0);
$$;

CREATE OR REPLACE FUNCTION public.list_passages(payload jsonb)
RETURNS SETOF free_will.passages
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path TO pg_catalog, free_will
AS $$
    SELECT *
    FROM public.list_passages(
        CASE
            WHEN COALESCE(payload ->> 'p_work_id', payload ->> 'work_id') ~* '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
                THEN COALESCE(payload ->> 'p_work_id', payload ->> 'work_id')::uuid
            ELSE NULL::uuid
        END,
        COALESCE(
            NULLIF(BTRIM(payload ->> 'p_book'), ''),
            NULLIF(BTRIM(payload ->> 'book'), '')
        ),
        COALESCE(
            NULLIF(BTRIM(payload ->> 'p_chapter'), ''),
            NULLIF(BTRIM(payload ->> 'chapter'), '')
        ),
        COALESCE(
            NULLIF(BTRIM(payload ->> 'p_section'), ''),
            NULLIF(BTRIM(payload ->> 'section'), '')
        ),
        CASE
            WHEN COALESCE(payload ->> 'p_limit', payload ->> 'limit') ~ '^[0-9]+$'
                THEN COALESCE(payload ->> 'p_limit', payload ->> 'limit')::integer
            ELSE 100
        END,
        CASE
            WHEN COALESCE(payload ->> 'p_offset', payload ->> 'offset') ~ '^[0-9]+$'
                THEN COALESCE(payload ->> 'p_offset', payload ->> 'offset')::integer
            ELSE 0
        END
    );
$$;

CREATE OR REPLACE FUNCTION public.get_passage(
    p_passage_id uuid
)
RETURNS SETOF free_will.passages
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path TO pg_catalog, free_will
AS $$
    SELECT *
    FROM free_will.passages
    WHERE passage_id = p_passage_id;
$$;

CREATE OR REPLACE FUNCTION public.get_passage(payload jsonb)
RETURNS SETOF free_will.passages
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path TO pg_catalog, free_will
AS $$
    SELECT *
    FROM public.get_passage(
        CASE
            WHEN COALESCE(payload ->> 'p_passage_id', payload ->> 'passage_id', payload ->> 'id') ~* '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
                THEN COALESCE(payload ->> 'p_passage_id', payload ->> 'passage_id', payload ->> 'id')::uuid
            ELSE NULL::uuid
        END
    );
$$;

CREATE OR REPLACE FUNCTION public.get_text_stats()
RETURNS json
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path TO pg_catalog, free_will
AS $$
    SELECT json_build_object(
        'total_works', COUNT(*),
        'total_passages', (SELECT COUNT(*) FROM free_will.passages),
        'total_authors', COUNT(DISTINCT aw.author),
        'languages', json_agg(DISTINCT aw.language),
        'works_by_language', (
            SELECT json_object_agg(lang.language, lang.lang_count)
            FROM (
                SELECT language, COUNT(*) AS lang_count
                FROM free_will.ancient_works
                WHERE language IS NOT NULL
                GROUP BY language
            ) lang
        )
    )
    FROM free_will.ancient_works aw;
$$;

CREATE OR REPLACE FUNCTION public.get_ancient_work(payload jsonb)
RETURNS SETOF free_will.ancient_works
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path TO pg_catalog, free_will
AS $$
    SELECT *
    FROM public.get_ancient_work(
        CASE
            WHEN COALESCE(payload ->> 'p_work_id', payload ->> 'work_id', payload ->> 'id') ~* '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
                THEN COALESCE(payload ->> 'p_work_id', payload ->> 'work_id', payload ->> 'id')::uuid
            ELSE NULL::uuid
        END
    );
$$;

CREATE OR REPLACE FUNCTION public.get_ancient_work_by_kg_id(payload jsonb)
RETURNS SETOF free_will.ancient_works
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path TO pg_catalog, free_will
AS $$
    SELECT *
    FROM public.get_ancient_work_by_kg_id(
        COALESCE(
            NULLIF(BTRIM(payload ->> 'p_kg_work_id'), ''),
            NULLIF(BTRIM(payload ->> 'kg_work_id'), '')
        )
    );
$$;

ALTER FUNCTION public.get_ancient_work(uuid) SET search_path TO pg_catalog, free_will;
ALTER FUNCTION public.get_ancient_work_by_kg_id(text) SET search_path TO pg_catalog, free_will;
ALTER FUNCTION public.get_passage_by_reference(text, text, text, text, text) SET search_path TO pg_catalog, free_will;
ALTER FUNCTION public.autocomplete_lemmas_fuzzy(text, text, integer, integer, boolean) SET search_path TO pg_catalog, free_will;
ALTER FUNCTION public.autocomplete_lemmas_prefix(text, text, integer, integer, boolean) SET search_path TO pg_catalog, free_will;
ALTER FUNCTION public.get_dictionary_lsj(text, text, text) SET search_path TO pg_catalog, free_will;
ALTER FUNCTION public.get_dictionary_lewis_short(text, text) SET search_path TO pg_catalog, free_will;
ALTER FUNCTION public.search_dictionary_lsj(text, integer) SET search_path TO pg_catalog, free_will;
ALTER FUNCTION public.search_dictionary_lewis_short(text, integer) SET search_path TO pg_catalog, free_will;
ALTER FUNCTION free_will.autocomplete_lemmas_fuzzy(text, text, integer, integer, boolean) SET search_path TO pg_catalog, free_will, extensions;

-- ---------------------------------------------------------------------------
-- Function exposure: remove implicit PUBLIC execute and keep only app roles
-- ---------------------------------------------------------------------------

REVOKE ALL ON FUNCTION free_will.count_ancient_works(text, text) FROM PUBLIC;
REVOKE ALL ON FUNCTION free_will.get_ancient_work(uuid) FROM PUBLIC;
REVOKE ALL ON FUNCTION free_will.get_ancient_work_by_kg_id(text) FROM PUBLIC;
REVOKE ALL ON FUNCTION free_will.list_ancient_works(text, text, text, integer, integer) FROM PUBLIC;
REVOKE ALL ON FUNCTION free_will.autocomplete_lemmas_fuzzy(text, text, integer, integer, boolean) FROM PUBLIC;
REVOKE ALL ON FUNCTION free_will.autocomplete_lemmas_prefix(text, text, integer, integer, boolean) FROM PUBLIC;

GRANT EXECUTE ON FUNCTION free_will.count_ancient_works(text, text) TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION free_will.get_ancient_work(uuid) TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION free_will.get_ancient_work_by_kg_id(text) TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION free_will.list_ancient_works(text, text, text, integer, integer) TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION free_will.autocomplete_lemmas_fuzzy(text, text, integer, integer, boolean) TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION free_will.autocomplete_lemmas_prefix(text, text, integer, integer, boolean) TO anon, authenticated, service_role;

REVOKE ALL ON FUNCTION public.count_ancient_works(text, text) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.count_ancient_works(jsonb) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.get_ancient_work(uuid) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.get_ancient_work(jsonb) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.get_ancient_work_by_kg_id(text) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.get_ancient_work_by_kg_id(jsonb) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.list_ancient_works(text, text, text, integer, integer) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.list_ancient_works(jsonb) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.list_passages(uuid, text, text, text, integer, integer) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.list_passages(jsonb) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.get_passage(uuid) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.get_passage(jsonb) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.get_text_stats() FROM PUBLIC;
REVOKE ALL ON FUNCTION public.search_passages(text, integer) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.search_passages(jsonb) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.search_passages_simple(text, integer) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.search_passages_simple(jsonb) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.get_kg_stats() FROM PUBLIC;
REVOKE ALL ON FUNCTION public.list_kg_nodes(text, integer, integer) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.list_kg_edges(text, integer, integer) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.get_kg_node(text) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.autocomplete_lemmas_fuzzy(text, text, integer, integer, boolean) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.autocomplete_lemmas_prefix(text, text, integer, integer, boolean) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.get_dictionary_lsj(text, text, text) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.get_dictionary_lewis_short(text, text) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.search_dictionary_lsj(text, integer) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.search_dictionary_lewis_short(text, integer) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.get_passage_by_reference(text, text, text, text, text) FROM PUBLIC;

GRANT EXECUTE ON FUNCTION public.count_ancient_works(text, text) TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.count_ancient_works(jsonb) TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.get_ancient_work(uuid) TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.get_ancient_work(jsonb) TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.get_ancient_work_by_kg_id(text) TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.get_ancient_work_by_kg_id(jsonb) TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.list_ancient_works(text, text, text, integer, integer) TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.list_ancient_works(jsonb) TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.list_passages(uuid, text, text, text, integer, integer) TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.list_passages(jsonb) TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.get_passage(uuid) TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.get_passage(jsonb) TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.get_text_stats() TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.search_passages(text, integer) TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.search_passages(jsonb) TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.search_passages_simple(text, integer) TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.search_passages_simple(jsonb) TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.get_kg_stats() TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.list_kg_nodes(text, integer, integer) TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.list_kg_edges(text, integer, integer) TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.get_kg_node(text) TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.autocomplete_lemmas_fuzzy(text, text, integer, integer, boolean) TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.autocomplete_lemmas_prefix(text, text, integer, integer, boolean) TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.get_dictionary_lsj(text, text, text) TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.get_dictionary_lewis_short(text, text) TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.search_dictionary_lsj(text, integer) TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.search_dictionary_lewis_short(text, integer) TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.get_passage_by_reference(text, text, text, text, text) TO anon, authenticated, service_role;

-- ---------------------------------------------------------------------------
-- Table exposure hardening
-- ---------------------------------------------------------------------------

REVOKE ALL ON SCHEMA free_will FROM PUBLIC;
GRANT USAGE ON SCHEMA free_will TO anon, authenticated, service_role;

REVOKE ALL ON TABLE free_will.ancient_works FROM PUBLIC, anon, authenticated, service_role;
REVOKE ALL ON TABLE free_will.passages FROM PUBLIC, anon, authenticated, service_role;
REVOKE ALL ON TABLE free_will.passage_citations FROM PUBLIC, anon, authenticated, service_role;
REVOKE ALL ON TABLE free_will.kg_nodes FROM PUBLIC, anon, authenticated, service_role;
REVOKE ALL ON TABLE free_will.kg_edges FROM PUBLIC, anon, authenticated, service_role;
REVOKE ALL ON TABLE free_will.dictionary_lsj FROM PUBLIC, anon, authenticated, service_role;
REVOKE ALL ON TABLE free_will.dictionary_lewis_short FROM PUBLIC, anon, authenticated, service_role;
REVOKE ALL ON TABLE free_will.users FROM PUBLIC, anon, authenticated, service_role;
REVOKE ALL ON TABLE free_will.auth_audit_log FROM PUBLIC, anon, authenticated, service_role;

GRANT SELECT ON TABLE free_will.ancient_works TO anon, authenticated, service_role;
GRANT SELECT ON TABLE free_will.passages TO anon, authenticated, service_role;
GRANT SELECT ON TABLE free_will.passage_citations TO anon, authenticated, service_role;
GRANT SELECT ON TABLE free_will.kg_nodes TO anon, authenticated, service_role;
GRANT SELECT ON TABLE free_will.kg_edges TO anon, authenticated, service_role;

-- ---------------------------------------------------------------------------
-- RLS for directly exposed tables
-- ---------------------------------------------------------------------------

ALTER TABLE free_will.ancient_works ENABLE ROW LEVEL SECURITY;
ALTER TABLE free_will.passages ENABLE ROW LEVEL SECURITY;
ALTER TABLE free_will.passage_citations ENABLE ROW LEVEL SECURITY;
ALTER TABLE free_will.kg_nodes ENABLE ROW LEVEL SECURITY;
ALTER TABLE free_will.kg_edges ENABLE ROW LEVEL SECURITY;
ALTER TABLE free_will.dictionary_lsj ENABLE ROW LEVEL SECURITY;
ALTER TABLE free_will.dictionary_lewis_short ENABLE ROW LEVEL SECURITY;
ALTER TABLE free_will.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE free_will.auth_audit_log ENABLE ROW LEVEL SECURITY;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_policies
        WHERE schemaname = 'free_will'
          AND tablename = 'ancient_works'
          AND policyname = 'ancient_works_read_api'
    ) THEN
        CREATE POLICY ancient_works_read_api
            ON free_will.ancient_works
            FOR SELECT
            TO anon, authenticated
            USING (true);
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM pg_policies
        WHERE schemaname = 'free_will'
          AND tablename = 'passages'
          AND policyname = 'passages_read_api'
    ) THEN
        CREATE POLICY passages_read_api
            ON free_will.passages
            FOR SELECT
            TO anon, authenticated
            USING (true);
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM pg_policies
        WHERE schemaname = 'free_will'
          AND tablename = 'passage_citations'
          AND policyname = 'passage_citations_read_api'
    ) THEN
        CREATE POLICY passage_citations_read_api
            ON free_will.passage_citations
            FOR SELECT
            TO anon, authenticated
            USING (true);
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM pg_policies
        WHERE schemaname = 'free_will'
          AND tablename = 'kg_nodes'
          AND policyname = 'kg_nodes_read_api'
    ) THEN
        CREATE POLICY kg_nodes_read_api
            ON free_will.kg_nodes
            FOR SELECT
            TO anon, authenticated
            USING (true);
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM pg_policies
        WHERE schemaname = 'free_will'
          AND tablename = 'kg_edges'
          AND policyname = 'kg_edges_read_api'
    ) THEN
        CREATE POLICY kg_edges_read_api
            ON free_will.kg_edges
            FOR SELECT
            TO anon, authenticated
            USING (true);
    END IF;
END;
$$;

-- ---------------------------------------------------------------------------
-- Default privileges: stop recreating PUBLIC exposure on new objects
-- ---------------------------------------------------------------------------

ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE EXECUTE ON FUNCTIONS FROM PUBLIC;
ALTER DEFAULT PRIVILEGES IN SCHEMA free_will REVOKE EXECUTE ON FUNCTIONS FROM PUBLIC;
ALTER DEFAULT PRIVILEGES IN SCHEMA free_will REVOKE ALL ON TABLES FROM PUBLIC;
ALTER DEFAULT PRIVILEGES IN SCHEMA free_will REVOKE ALL ON SEQUENCES FROM PUBLIC;
