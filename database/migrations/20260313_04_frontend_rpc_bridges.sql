-- EleutherIA production hardening
-- Step 4: add public RPC bridges for worker/front flows that should not depend
-- on direct REST access to the free_will schema.

CREATE OR REPLACE FUNCTION public.search_passages_filtered(
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
SECURITY DEFINER
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
SECURITY DEFINER
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
    p_work_id uuid,
    p_limit integer DEFAULT 1000,
    p_offset integer DEFAULT 0
)
RETURNS TABLE (
    passage_id uuid,
    canonical_ref text,
    sequence_number integer,
    book text,
    chapter text,
    section text
)
LANGUAGE sql
STABLE
SECURITY DEFINER
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
    p_work_id uuid,
    p_center_sequence integer,
    p_window integer DEFAULT 5
)
RETURNS SETOF free_will.passages
LANGUAGE sql
STABLE
SECURITY DEFINER
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
    p_work_id uuid
)
RETURNS bigint
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path TO pg_catalog, free_will
AS $$
    SELECT COUNT(*)::bigint
    FROM free_will.passages p
    WHERE p.work_id = p_work_id;
$$;

CREATE OR REPLACE FUNCTION public.get_best_passage_for_kg_node(
    p_kg_node_id text
)
RETURNS TABLE (
    passage_id uuid
)
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path TO pg_catalog, free_will
AS $$
    SELECT pc.passage_id
    FROM free_will.passage_citations pc
    WHERE pc.kg_node_id = p_kg_node_id
    ORDER BY pc.confidence DESC NULLS LAST, pc.passage_id
    LIMIT 1;
$$;

CREATE OR REPLACE FUNCTION public.get_work_kg_nodes(
    p_work_id uuid
)
RETURNS TABLE (
    kg_node_id text,
    citation_count bigint,
    passage_ids uuid[],
    canonical_refs text[],
    first_sequence integer,
    first_passage_id uuid,
    first_canonical_ref text
)
LANGUAGE sql
STABLE
SECURITY DEFINER
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
            COUNT(*)::bigint AS citation_count,
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

REVOKE ALL ON FUNCTION public.search_passages_filtered(text, integer, text, text, text) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.search_passages_simple_filtered(text, integer, text, text, text) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.list_passage_refs(uuid, integer, integer) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.list_passages_window(uuid, integer, integer) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.count_passages_for_work(uuid) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.get_best_passage_for_kg_node(text) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.get_work_kg_nodes(uuid) FROM PUBLIC;

GRANT EXECUTE ON FUNCTION public.search_passages_filtered(text, integer, text, text, text) TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.search_passages_simple_filtered(text, integer, text, text, text) TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.list_passage_refs(uuid, integer, integer) TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.list_passages_window(uuid, integer, integer) TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.count_passages_for_work(uuid) TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.get_best_passage_for_kg_node(text) TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.get_work_kg_nodes(uuid) TO anon, authenticated, service_role;
