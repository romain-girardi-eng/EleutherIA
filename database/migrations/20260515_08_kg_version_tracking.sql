-- kg_version tracking — Feature 7 (reproducibility certificates)
--
-- Automates two things that today require a manual lever:
--
-- 1. Bump `free_will.kg_version.version` on every mutation of kg_nodes,
--    kg_edges, or passage_citations. The answer-cache layer keys its TTL
--    on that counter, so a single KG edit now invalidates every reusable
--    cached answer cleanly.
--
-- 2. Record the kg_version a `query_traces` row was produced against, so
--    the `/recherches/:slug/reproducibility` endpoint can emit a
--    reproducibility certificate (cached_at vs. current) and the
--    `/reverify` endpoint can diff the cached answer against a fresh run.

-- ---------------------------------------------------------------------------
-- 1. bump_kg_version trigger function + triggers
-- ---------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION free_will.bump_kg_version() RETURNS trigger AS $$
BEGIN
    UPDATE free_will.kg_version
    SET version = version + 1, updated_at = now()
    WHERE id = 1;
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS kg_nodes_bump_version ON free_will.kg_nodes;
CREATE TRIGGER kg_nodes_bump_version
    AFTER INSERT OR UPDATE OR DELETE ON free_will.kg_nodes
    FOR EACH STATEMENT EXECUTE FUNCTION free_will.bump_kg_version();

DROP TRIGGER IF EXISTS kg_edges_bump_version ON free_will.kg_edges;
CREATE TRIGGER kg_edges_bump_version
    AFTER INSERT OR UPDATE OR DELETE ON free_will.kg_edges
    FOR EACH STATEMENT EXECUTE FUNCTION free_will.bump_kg_version();

DROP TRIGGER IF EXISTS passage_citations_bump_version ON free_will.passage_citations;
CREATE TRIGGER passage_citations_bump_version
    AFTER INSERT OR UPDATE OR DELETE ON free_will.passage_citations
    FOR EACH STATEMENT EXECUTE FUNCTION free_will.bump_kg_version();

-- ---------------------------------------------------------------------------
-- 2. Record the KG version on query_traces rows
-- ---------------------------------------------------------------------------

ALTER TABLE free_will.query_traces
    ADD COLUMN IF NOT EXISTS kg_version_at_creation bigint NOT NULL DEFAULT 0;

-- Backfill existing rows with the current version. They're best-effort
-- historical records; the diff endpoint treats anything matching the current
-- version as `unchanged` and the explicit zero as `stale_unknown` if a row
-- somehow slips through.
UPDATE free_will.query_traces
SET kg_version_at_creation = COALESCE(
    (SELECT version FROM free_will.kg_version WHERE id = 1), 0
)
WHERE kg_version_at_creation = 0;
