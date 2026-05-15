-- answer_cache: replay-cache for /api/graphrag/query/stream answers
--
-- Looked up by GraphRAGService BEFORE running the agent pipeline.
-- A hit replays the cached `complete` SSE event immediately, skipping the
-- ~$0.45 / 7-minute synthesis. Indexed by (normalized_question, model,
-- retrieval_mode); invalidated by TTL or by bumping free_will.kg_version.

CREATE SCHEMA IF NOT EXISTS free_will;
SET search_path = free_will;

CREATE TABLE IF NOT EXISTS free_will.answer_cache (
    cache_key       text PRIMARY KEY,
    normalized_question text NOT NULL,
    raw_question    text NOT NULL,
    model           text NOT NULL,
    retrieval_mode  text NOT NULL,
    answer          text NOT NULL,
    citations_json  jsonb NOT NULL DEFAULT '[]'::jsonb,
    passage_citations_json jsonb NOT NULL DEFAULT '[]'::jsonb,
    sources_json    jsonb NOT NULL DEFAULT '[]'::jsonb,
    reasoning_path_json jsonb NOT NULL DEFAULT '{}'::jsonb,
    total_tokens    integer NOT NULL DEFAULT 0,
    total_cost_usd  numeric(10,6) NOT NULL DEFAULT 0,
    trace_id        uuid,
    kg_version_at_creation  bigint NOT NULL DEFAULT 0,
    hit_count       integer NOT NULL DEFAULT 0,
    last_hit_at     timestamptz,
    created_at      timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_answer_cache_created_at
    ON free_will.answer_cache(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_answer_cache_hit_count
    ON free_will.answer_cache(hit_count DESC);

-- kg_version: monotonic counter; bump (UPDATE) to globally invalidate the
-- answer cache. Not auto-incremented on KG mutations yet (follow-up).
CREATE TABLE IF NOT EXISTS free_will.kg_version (
    id integer PRIMARY KEY DEFAULT 1,
    version bigint NOT NULL DEFAULT 0,
    updated_at timestamptz NOT NULL DEFAULT now(),
    CHECK (id = 1)
);

INSERT INTO free_will.kg_version (id, version)
VALUES (1, 0)
ON CONFLICT DO NOTHING;
