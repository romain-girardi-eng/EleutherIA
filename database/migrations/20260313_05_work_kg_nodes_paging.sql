-- EleutherIA production hardening
-- Step 5: paginate work KG node lookups so PostgREST row caps cannot truncate
-- the frontend modal for heavily cited works.

CREATE OR REPLACE FUNCTION public.list_work_kg_nodes(
    p_work_id uuid,
    p_limit integer DEFAULT 1000,
    p_offset integer DEFAULT 0
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
            p.sequence_number
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
    ORDER BY a.first_sequence NULLS LAST, a.kg_node_id
    LIMIT LEAST(GREATEST(COALESCE(p_limit, 1000), 1), 5000)
    OFFSET GREATEST(COALESCE(p_offset, 0), 0);
$$;

REVOKE ALL ON FUNCTION public.list_work_kg_nodes(uuid, integer, integer) FROM PUBLIC;

GRANT EXECUTE ON FUNCTION public.list_work_kg_nodes(uuid, integer, integer) TO anon, authenticated, service_role;
