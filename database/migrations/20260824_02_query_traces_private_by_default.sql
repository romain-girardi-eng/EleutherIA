-- Privacy repair: GraphRAG traces are private unless a future, explicit
-- publication workflow records consent.  Capability-token shares live in the
-- separate shared_traces table and do not require is_public=true.

SET search_path TO free_will, public;

ALTER TABLE free_will.query_traces
    ALTER COLUMN is_public SET DEFAULT false;

-- The old default published every trace automatically and did not record a
-- consent bit.  There is therefore no safe way to distinguish curated rows;
-- fail closed and require deliberate republication by an accountable owner.
UPDATE free_will.query_traces
SET is_public = false
WHERE is_public = true;

COMMENT ON COLUMN free_will.query_traces.is_public IS
    'Explicit public-gallery publication consent; false by default. Private trace sharing uses shared_traces capability tokens.';
