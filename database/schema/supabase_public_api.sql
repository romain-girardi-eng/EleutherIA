-- EleutherIA Supabase public API functions
--
-- Apply after schema.sql. These SECURITY INVOKER wrappers are the stable
-- PostgREST surface used by the Cloudflare worker. They intentionally avoid
-- depending on historical dictionary/morphology objects so a rebuilt Supabase
-- project can come online from the recovered KG snapshot first. Read access is
-- controlled by explicit grants and RLS policies rather than RLS bypass.

CREATE SCHEMA IF NOT EXISTS free_will;

-- ---------------------------------------------------------------------------
-- Ancient works
-- ---------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION public.count_ancient_works(
    p_author TEXT DEFAULT NULL,
    p_language TEXT DEFAULT NULL
)
RETURNS BIGINT
LANGUAGE sql
STABLE
SECURITY INVOKER
SET search_path TO pg_catalog, free_will
AS $$
    SELECT COUNT(*)::BIGINT
    FROM free_will.ancient_works aw
    WHERE (p_author IS NULL OR aw.author ILIKE '%' || p_author || '%')
      AND (p_language IS NULL OR aw.language = p_language);
$$;

CREATE OR REPLACE FUNCTION public.count_ancient_works(payload JSONB)
RETURNS BIGINT
LANGUAGE sql
STABLE
SECURITY INVOKER
SET search_path TO pg_catalog, free_will
AS $$
    SELECT public.count_ancient_works(
        COALESCE(NULLIF(BTRIM(payload ->> 'p_author'), ''), NULLIF(BTRIM(payload ->> 'author'), '')),
        COALESCE(NULLIF(BTRIM(payload ->> 'p_language'), ''), NULLIF(BTRIM(payload ->> 'language'), ''))
    );
$$;

CREATE OR REPLACE FUNCTION public.list_ancient_works(
    p_author TEXT DEFAULT NULL,
    p_language TEXT DEFAULT NULL,
    p_sort_by TEXT DEFAULT 'author',
    p_limit INTEGER DEFAULT 50,
    p_offset INTEGER DEFAULT 0
)
RETURNS TABLE (
    id UUID,
    work_id UUID,
    kg_work_id TEXT,
    canonical_id TEXT,
    title TEXT,
    title_original TEXT,
    author TEXT,
    author_original TEXT,
    language TEXT,
    period TEXT,
    date_composed TEXT,
    school TEXT,
    source TEXT,
    source_url TEXT,
    license TEXT,
    division_scheme TEXT,
    total_divisions INTEGER,
    total_words INTEGER,
    total_chars INTEGER,
    notes TEXT,
    metadata JSONB,
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ,
    citation_count BIGINT
)
LANGUAGE sql
STABLE
SECURITY INVOKER
SET search_path TO pg_catalog, free_will
AS $$
    WITH filtered AS MATERIALIZED (
        SELECT aw.*
        FROM free_will.ancient_works aw
        WHERE (p_author IS NULL OR aw.author ILIKE '%' || p_author || '%')
          AND (p_language IS NULL OR aw.language = p_language)
    ),
    cited AS MATERIALIZED (
        SELECT
            p.work_id,
            COUNT(DISTINCT pc.kg_node_id)::BIGINT AS citation_count
        FROM free_will.passages p
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
        COALESCE(c.citation_count, 0) AS citation_count
    FROM filtered f
    LEFT JOIN cited c
      ON c.work_id = f.work_id
    ORDER BY
        CASE WHEN p_sort_by = 'most_cited' THEN COALESCE(c.citation_count, 0) END DESC NULLS LAST,
        CASE WHEN p_sort_by = 'title' THEN f.title ELSE f.author END ASC,
        CASE WHEN p_sort_by = 'title' THEN f.author ELSE f.title END ASC,
        f.work_id
    LIMIT LEAST(GREATEST(COALESCE(p_limit, 50), 1), 500)
    OFFSET GREATEST(COALESCE(p_offset, 0), 0);
$$;

CREATE OR REPLACE FUNCTION public.list_ancient_works(payload JSONB)
RETURNS TABLE (
    id UUID,
    work_id UUID,
    kg_work_id TEXT,
    canonical_id TEXT,
    title TEXT,
    title_original TEXT,
    author TEXT,
    author_original TEXT,
    language TEXT,
    period TEXT,
    date_composed TEXT,
    school TEXT,
    source TEXT,
    source_url TEXT,
    license TEXT,
    division_scheme TEXT,
    total_divisions INTEGER,
    total_words INTEGER,
    total_chars INTEGER,
    notes TEXT,
    metadata JSONB,
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ,
    citation_count BIGINT
)
LANGUAGE sql
STABLE
SECURITY INVOKER
SET search_path TO pg_catalog, free_will
AS $$
    SELECT *
    FROM public.list_ancient_works(
        COALESCE(NULLIF(BTRIM(payload ->> 'p_author'), ''), NULLIF(BTRIM(payload ->> 'author'), '')),
        COALESCE(NULLIF(BTRIM(payload ->> 'p_language'), ''), NULLIF(BTRIM(payload ->> 'language'), '')),
        COALESCE(NULLIF(BTRIM(payload ->> 'p_sort_by'), ''), NULLIF(BTRIM(payload ->> 'sort_by'), ''), 'author'),
        CASE
            WHEN COALESCE(payload ->> 'p_limit', payload ->> 'limit') ~ '^[0-9]+$'
                THEN COALESCE(payload ->> 'p_limit', payload ->> 'limit')::INTEGER
            ELSE 50
        END,
        CASE
            WHEN COALESCE(payload ->> 'p_offset', payload ->> 'offset') ~ '^[0-9]+$'
                THEN COALESCE(payload ->> 'p_offset', payload ->> 'offset')::INTEGER
            ELSE 0
        END
    );
$$;

CREATE OR REPLACE FUNCTION public.get_ancient_work(p_work_id UUID)
RETURNS SETOF free_will.ancient_works
LANGUAGE sql
STABLE
SECURITY INVOKER
SET search_path TO pg_catalog, free_will
AS $$
    SELECT *
    FROM free_will.ancient_works aw
    WHERE aw.work_id = p_work_id;
$$;

CREATE OR REPLACE FUNCTION public.get_ancient_work(payload JSONB)
RETURNS SETOF free_will.ancient_works
LANGUAGE sql
STABLE
SECURITY INVOKER
SET search_path TO pg_catalog, free_will
AS $$
    SELECT *
    FROM public.get_ancient_work(
        CASE
            WHEN COALESCE(payload ->> 'p_work_id', payload ->> 'work_id', payload ->> 'id') ~* '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
                THEN COALESCE(payload ->> 'p_work_id', payload ->> 'work_id', payload ->> 'id')::UUID
            ELSE NULL::UUID
        END
    );
$$;

CREATE OR REPLACE FUNCTION public.get_ancient_work_by_kg_id(p_kg_work_id TEXT)
RETURNS SETOF free_will.ancient_works
LANGUAGE sql
STABLE
SECURITY INVOKER
SET search_path TO pg_catalog, free_will
AS $$
    SELECT *
    FROM free_will.ancient_works aw
    WHERE aw.kg_work_id = p_kg_work_id;
$$;

CREATE OR REPLACE FUNCTION public.get_ancient_work_by_kg_id(payload JSONB)
RETURNS SETOF free_will.ancient_works
LANGUAGE sql
STABLE
SECURITY INVOKER
SET search_path TO pg_catalog, free_will
AS $$
    SELECT *
    FROM public.get_ancient_work_by_kg_id(
        COALESCE(NULLIF(BTRIM(payload ->> 'p_kg_work_id'), ''), NULLIF(BTRIM(payload ->> 'kg_work_id'), ''))
    );
$$;

-- ---------------------------------------------------------------------------
-- Passages
-- ---------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION public.list_passages(
    p_work_id UUID,
    p_book TEXT DEFAULT NULL,
    p_chapter TEXT DEFAULT NULL,
    p_section TEXT DEFAULT NULL,
    p_limit INTEGER DEFAULT 100,
    p_offset INTEGER DEFAULT 0
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
      AND (p_book IS NULL OR p.book = p_book)
      AND (p_chapter IS NULL OR p.chapter = p_chapter)
      AND (p_section IS NULL OR p.section = p_section)
    ORDER BY p.sequence_number, p.passage_id
    LIMIT LEAST(GREATEST(COALESCE(p_limit, 100), 1), 10000)
    OFFSET GREATEST(COALESCE(p_offset, 0), 0);
$$;

CREATE OR REPLACE FUNCTION public.list_passages(payload JSONB)
RETURNS SETOF free_will.passages
LANGUAGE sql
STABLE
SECURITY INVOKER
SET search_path TO pg_catalog, free_will
AS $$
    SELECT *
    FROM public.list_passages(
        CASE
            WHEN COALESCE(payload ->> 'p_work_id', payload ->> 'work_id') ~* '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
                THEN COALESCE(payload ->> 'p_work_id', payload ->> 'work_id')::UUID
            ELSE NULL::UUID
        END,
        COALESCE(NULLIF(BTRIM(payload ->> 'p_book'), ''), NULLIF(BTRIM(payload ->> 'book'), '')),
        COALESCE(NULLIF(BTRIM(payload ->> 'p_chapter'), ''), NULLIF(BTRIM(payload ->> 'chapter'), '')),
        COALESCE(NULLIF(BTRIM(payload ->> 'p_section'), ''), NULLIF(BTRIM(payload ->> 'section'), '')),
        CASE
            WHEN COALESCE(payload ->> 'p_limit', payload ->> 'limit') ~ '^[0-9]+$'
                THEN COALESCE(payload ->> 'p_limit', payload ->> 'limit')::INTEGER
            ELSE 100
        END,
        CASE
            WHEN COALESCE(payload ->> 'p_offset', payload ->> 'offset') ~ '^[0-9]+$'
                THEN COALESCE(payload ->> 'p_offset', payload ->> 'offset')::INTEGER
            ELSE 0
        END
    );
$$;

CREATE OR REPLACE FUNCTION public.get_passage(p_passage_id UUID)
RETURNS SETOF free_will.passages
LANGUAGE sql
STABLE
SECURITY INVOKER
SET search_path TO pg_catalog, free_will
AS $$
    SELECT *
    FROM free_will.passages p
    WHERE p.passage_id = p_passage_id;
$$;

CREATE OR REPLACE FUNCTION public.get_passage(payload JSONB)
RETURNS SETOF free_will.passages
LANGUAGE sql
STABLE
SECURITY INVOKER
SET search_path TO pg_catalog, free_will
AS $$
    SELECT *
    FROM public.get_passage(
        CASE
            WHEN COALESCE(payload ->> 'p_passage_id', payload ->> 'passage_id', payload ->> 'id') ~* '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
                THEN COALESCE(payload ->> 'p_passage_id', payload ->> 'passage_id', payload ->> 'id')::UUID
            ELSE NULL::UUID
        END
    );
$$;

CREATE OR REPLACE FUNCTION public.get_passage_by_reference(
    p_author_pattern TEXT,
    p_title_pattern TEXT,
    p_section TEXT DEFAULT NULL,
    p_book TEXT DEFAULT NULL,
    p_chapter TEXT DEFAULT NULL
)
RETURNS TABLE (
    passage_id UUID,
    work_id UUID,
    cts_urn TEXT,
    canonical_ref TEXT,
    book TEXT,
    chapter TEXT,
    section TEXT,
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
        p.passage_id,
        p.work_id,
        p.cts_urn,
        p.canonical_ref,
        p.book,
        p.chapter,
        p.section,
        p.text_content,
        w.author,
        w.title
    FROM free_will.passages p
    JOIN free_will.ancient_works w
      ON w.work_id = p.work_id
    WHERE (p_author_pattern IS NULL OR w.author ILIKE p_author_pattern)
      AND (p_title_pattern IS NULL OR w.title ILIKE '%' || p_title_pattern || '%')
      AND (p_book IS NULL OR p.book = p_book OR p.canonical_ref ILIKE '%' || p_book || '%')
      AND (p_chapter IS NULL OR p.chapter = p_chapter OR p.canonical_ref ILIKE '%' || p_chapter || '%')
      AND (p_section IS NULL OR p.section = p_section OR p.canonical_ref ILIKE '%' || p_section || '%')
    ORDER BY p.sequence_number, p.passage_id
    LIMIT 20;
$$;

CREATE OR REPLACE FUNCTION public.get_text_stats()
RETURNS JSON
LANGUAGE sql
STABLE
SECURITY INVOKER
SET search_path TO pg_catalog, free_will
AS $$
    SELECT json_build_object(
        'total_works', (SELECT COUNT(*) FROM free_will.ancient_works),
        'total_passages', (SELECT COUNT(*) FROM free_will.passages),
        'total_authors', (SELECT COUNT(DISTINCT author) FROM free_will.ancient_works),
        'languages', COALESCE((SELECT json_agg(DISTINCT language) FROM free_will.ancient_works), '[]'::JSON),
        'works_by_language', COALESCE((
            SELECT json_object_agg(lang.language, lang.total)
            FROM (
                SELECT language, COUNT(*) AS total
                FROM free_will.ancient_works
                GROUP BY language
            ) lang
        ), '{}'::JSON)
    );
$$;

-- ---------------------------------------------------------------------------
-- Function permissions and read-only table exposure
-- ---------------------------------------------------------------------------

REVOKE ALL ON FUNCTION public.count_ancient_works(TEXT, TEXT) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.count_ancient_works(JSONB) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.list_ancient_works(TEXT, TEXT, TEXT, INTEGER, INTEGER) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.list_ancient_works(JSONB) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.get_ancient_work(UUID) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.get_ancient_work(JSONB) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.get_ancient_work_by_kg_id(TEXT) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.get_ancient_work_by_kg_id(JSONB) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.list_passages(UUID, TEXT, TEXT, TEXT, INTEGER, INTEGER) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.list_passages(JSONB) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.get_passage(UUID) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.get_passage(JSONB) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.get_passage_by_reference(TEXT, TEXT, TEXT, TEXT, TEXT) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.get_text_stats() FROM PUBLIC;

GRANT EXECUTE ON FUNCTION public.count_ancient_works(TEXT, TEXT) TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.count_ancient_works(JSONB) TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.list_ancient_works(TEXT, TEXT, TEXT, INTEGER, INTEGER) TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.list_ancient_works(JSONB) TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.get_ancient_work(UUID) TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.get_ancient_work(JSONB) TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.get_ancient_work_by_kg_id(TEXT) TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.get_ancient_work_by_kg_id(JSONB) TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.list_passages(UUID, TEXT, TEXT, TEXT, INTEGER, INTEGER) TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.list_passages(JSONB) TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.get_passage(UUID) TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.get_passage(JSONB) TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.get_passage_by_reference(TEXT, TEXT, TEXT, TEXT, TEXT) TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.get_text_stats() TO anon, authenticated, service_role;

GRANT USAGE ON SCHEMA free_will TO anon, authenticated, service_role;
GRANT SELECT ON TABLE free_will.ancient_works TO anon, authenticated, service_role;
GRANT SELECT ON TABLE free_will.passages TO anon, authenticated, service_role;
GRANT SELECT ON TABLE free_will.passage_citations TO anon, authenticated, service_role;

ALTER TABLE free_will.ancient_works ENABLE ROW LEVEL SECURITY;
ALTER TABLE free_will.passages ENABLE ROW LEVEL SECURITY;
ALTER TABLE free_will.passage_citations ENABLE ROW LEVEL SECURITY;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
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
        SELECT 1 FROM pg_policies
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
        SELECT 1 FROM pg_policies
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
END;
$$;
