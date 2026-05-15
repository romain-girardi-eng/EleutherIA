-- Real-time token + USD cost tracking for deep-mode queries.
--
-- Adds three columns to free_will.query_traces so each persisted trace
-- carries:
--   - total_cost_usd      : sum of estimated USD spend across all LLM calls
--   - token_breakdown     : { by_model: { model: {tokens, cost_usd, calls}},
--                             by_agent: { agent: {tokens, cost_usd, calls}} }
--   - provider_usage      : { provider: { prompt_tokens, completion_tokens,
--                                          total_tokens, cost_usd, calls } }
--
-- total_tokens already lives inside agent_tree on a per-node basis; we keep
-- a denormalized roll-up here so dashboards and the audit endpoint can read
-- without walking the tree. Idempotent — safe to re-run.

SET search_path = free_will;

ALTER TABLE IF EXISTS free_will.query_traces
    ADD COLUMN IF NOT EXISTS total_cost_usd NUMERIC(10,6) DEFAULT 0,
    ADD COLUMN IF NOT EXISTS total_tokens INTEGER DEFAULT 0,
    ADD COLUMN IF NOT EXISTS token_breakdown JSONB DEFAULT '{}'::jsonb,
    ADD COLUMN IF NOT EXISTS provider_usage JSONB DEFAULT '{}'::jsonb;

CREATE INDEX IF NOT EXISTS idx_query_traces_total_cost
    ON free_will.query_traces (total_cost_usd DESC)
    WHERE total_cost_usd > 0;
