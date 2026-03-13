-- Migration: add missing get_kg_node RPC
-- The function was referenced in REVOKE/GRANT statements but never created.
-- This caused PGRST202 errors in the streaming GraphRAG route, which triggered
-- an expensive fallback that fetched all 17k nodes, exceeding Worker memory limits.

CREATE OR REPLACE FUNCTION public.get_kg_node(p_node_id text)
RETURNS TABLE (
    node_id   text,
    label     text,
    type      text,
    description text,
    period    text,
    alternative_names jsonb,
    metadata  jsonb,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
)
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path TO pg_catalog, free_will
AS $$
    SELECT
        n.node_id,
        n.label,
        n.type,
        n.description,
        n.period,
        n.alternative_names,
        n.metadata,
        n.created_at,
        n.updated_at
    FROM free_will.kg_nodes n
    WHERE n.node_id = p_node_id
    LIMIT 1;
$$;

REVOKE ALL ON FUNCTION public.get_kg_node(text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.get_kg_node(text) TO anon, authenticated, service_role;
