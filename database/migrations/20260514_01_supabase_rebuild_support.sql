-- EleutherIA Supabase rebuild support
--
-- Apply after database/schema/schema.sql when recreating a Supabase project from
-- scratch. It keeps the canonical free_will tables compatible with both:
-- - Python backend SQL, which uses node_id/source_id/target_id
-- - Cloudflare/PostgREST flows, some of which select id/source/target/weight

CREATE SCHEMA IF NOT EXISTS free_will;
CREATE SCHEMA IF NOT EXISTS extensions;

CREATE EXTENSION IF NOT EXISTS pg_trgm WITH SCHEMA extensions;

-- ---------------------------------------------------------------------------
-- REST compatibility columns
-- ---------------------------------------------------------------------------

ALTER TABLE free_will.kg_nodes
    ADD COLUMN IF NOT EXISTS id TEXT GENERATED ALWAYS AS (node_id) STORED;

ALTER TABLE free_will.kg_nodes
    ADD COLUMN IF NOT EXISTS school TEXT GENERATED ALWAYS AS (
        COALESCE(metadata ->> 'school', metadata ->> 'school_affiliation')
    ) STORED;

ALTER TABLE free_will.kg_nodes
    ADD COLUMN IF NOT EXISTS role TEXT GENERATED ALWAYS AS (
        COALESCE(metadata ->> 'role', metadata ->> 'scholarly_role')
    ) STORED;

ALTER TABLE free_will.kg_edges
    ADD COLUMN IF NOT EXISTS source TEXT GENERATED ALWAYS AS (source_id) STORED;

ALTER TABLE free_will.kg_edges
    ADD COLUMN IF NOT EXISTS target TEXT GENERATED ALWAYS AS (target_id) STORED;

ALTER TABLE free_will.kg_edges
    ADD COLUMN IF NOT EXISTS weight DOUBLE PRECISION DEFAULT 1.0;

UPDATE free_will.kg_edges
SET weight = CASE
    WHEN COALESCE(metadata ->> 'weight', '') ~ '^[0-9]+(\.[0-9]+)?$'
        THEN (metadata ->> 'weight')::DOUBLE PRECISION
    ELSE COALESCE(weight, 1.0)
END;

CREATE INDEX IF NOT EXISTS idx_kg_nodes_rest_id
    ON free_will.kg_nodes(id);

CREATE INDEX IF NOT EXISTS idx_kg_nodes_school
    ON free_will.kg_nodes(school);

CREATE INDEX IF NOT EXISTS idx_kg_edges_rest_source
    ON free_will.kg_edges(source);

CREATE INDEX IF NOT EXISTS idx_kg_edges_rest_target
    ON free_will.kg_edges(target);

-- ---------------------------------------------------------------------------
-- Public RPCs used by Cloudflare Workers and frontend flows
-- ---------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION public.get_kg_stats()
RETURNS JSON
LANGUAGE sql
STABLE
SECURITY INVOKER
SET search_path TO pg_catalog, free_will
AS $$
    SELECT json_build_object(
        'totalNodes', (SELECT COUNT(*) FROM free_will.kg_nodes),
        'totalEdges', (SELECT COUNT(*) FROM free_will.kg_edges),
        'nodeTypes', COALESCE((
            SELECT json_object_agg(type_counts.type, type_counts.total)
            FROM (
                SELECT n.type, COUNT(*) AS total
                FROM free_will.kg_nodes n
                GROUP BY n.type
                ORDER BY n.type
            ) type_counts
        ), '{}'::JSON),
        'edgeTypes', COALESCE((
            SELECT json_object_agg(edge_counts.relation, edge_counts.total)
            FROM (
                SELECT e.relation, COUNT(*) AS total
                FROM free_will.kg_edges e
                GROUP BY e.relation
                ORDER BY e.relation
            ) edge_counts
        ), '{}'::JSON)
    );
$$;

CREATE OR REPLACE FUNCTION public.list_kg_nodes(
    p_type TEXT DEFAULT NULL,
    p_limit INTEGER DEFAULT 1000,
    p_offset INTEGER DEFAULT 0
)
RETURNS TABLE (
    node_id TEXT,
    id TEXT,
    label TEXT,
    type VARCHAR,
    description TEXT,
    period VARCHAR,
    school TEXT,
    role TEXT,
    alternative_names JSONB,
    metadata JSONB,
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ
)
LANGUAGE sql
STABLE
SECURITY INVOKER
SET search_path TO pg_catalog, free_will
AS $$
    SELECT
        n.node_id,
        n.id,
        n.label,
        n.type,
        n.description,
        n.period,
        n.school,
        n.role,
        n.alternative_names,
        n.metadata,
        n.created_at,
        n.updated_at
    FROM free_will.kg_nodes n
    WHERE p_type IS NULL OR n.type = p_type
    ORDER BY n.node_id
    LIMIT LEAST(GREATEST(COALESCE(p_limit, 1000), 1), 5000)
    OFFSET GREATEST(COALESCE(p_offset, 0), 0);
$$;

CREATE OR REPLACE FUNCTION public.list_kg_edges(
    p_relation TEXT DEFAULT NULL,
    p_limit INTEGER DEFAULT 1000,
    p_offset INTEGER DEFAULT 0
)
RETURNS TABLE (
    edge_id UUID,
    source_id VARCHAR,
    target_id VARCHAR,
    source TEXT,
    target TEXT,
    relation VARCHAR,
    weight DOUBLE PRECISION,
    metadata JSONB,
    created_at TIMESTAMPTZ
)
LANGUAGE sql
STABLE
SECURITY INVOKER
SET search_path TO pg_catalog, free_will
AS $$
    SELECT
        e.edge_id,
        e.source_id,
        e.target_id,
        e.source,
        e.target,
        e.relation,
        e.weight,
        e.metadata,
        e.created_at
    FROM free_will.kg_edges e
    WHERE p_relation IS NULL OR e.relation = p_relation
    ORDER BY e.source_id, e.target_id, e.relation, e.edge_id
    LIMIT LEAST(GREATEST(COALESCE(p_limit, 1000), 1), 5000)
    OFFSET GREATEST(COALESCE(p_offset, 0), 0);
$$;

CREATE OR REPLACE FUNCTION public.get_kg_node(p_node_id TEXT)
RETURNS TABLE (
    node_id TEXT,
    id TEXT,
    label TEXT,
    type VARCHAR,
    description TEXT,
    period VARCHAR,
    school TEXT,
    role TEXT,
    alternative_names JSONB,
    metadata JSONB,
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ
)
LANGUAGE sql
STABLE
SECURITY INVOKER
SET search_path TO pg_catalog, free_will
AS $$
    SELECT
        n.node_id,
        n.id,
        n.label,
        n.type,
        n.description,
        n.period,
        n.school,
        n.role,
        n.alternative_names,
        n.metadata,
        n.created_at,
        n.updated_at
    FROM free_will.kg_nodes n
    WHERE n.node_id = p_node_id
    LIMIT 1;
$$;

REVOKE ALL ON FUNCTION public.get_kg_stats() FROM PUBLIC;
REVOKE ALL ON FUNCTION public.list_kg_nodes(TEXT, INTEGER, INTEGER) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.list_kg_edges(TEXT, INTEGER, INTEGER) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.get_kg_node(TEXT) FROM PUBLIC;

GRANT EXECUTE ON FUNCTION public.get_kg_stats() TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.list_kg_nodes(TEXT, INTEGER, INTEGER) TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.list_kg_edges(TEXT, INTEGER, INTEGER) TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.get_kg_node(TEXT) TO anon, authenticated, service_role;

GRANT USAGE ON SCHEMA free_will TO anon, authenticated, service_role;
GRANT SELECT ON TABLE free_will.kg_nodes TO anon, authenticated, service_role;
GRANT SELECT ON TABLE free_will.kg_edges TO anon, authenticated, service_role;

ALTER TABLE free_will.kg_nodes ENABLE ROW LEVEL SECURITY;
ALTER TABLE free_will.kg_edges ENABLE ROW LEVEL SECURITY;

DO $$
BEGIN
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
