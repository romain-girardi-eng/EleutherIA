-- query_traces: persistent audit trail of every deep-mode GraphRAG query
--
-- Captures the full agent tree (orchestrator + sub-agents + tool calls),
-- verifier / counter-evidence / methodology / polishing reports, the final
-- answer, and timing/cost totals. Wired in by GraphRAGService and the
-- opencode SSE proxy; surfaced through GET /api/graphrag/query/{trace_id}/audit.

CREATE SCHEMA IF NOT EXISTS free_will;
SET search_path = free_will;

CREATE TABLE IF NOT EXISTS query_traces (
    trace_id UUID PRIMARY KEY,
    user_id UUID REFERENCES free_will.users(user_id) ON DELETE SET NULL,
    query TEXT NOT NULL,
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at TIMESTAMPTZ,
    mode TEXT,
    agent_tree JSONB DEFAULT '{}'::jsonb,
    citation_verifier_report JSONB,
    counter_evidence_report JSONB,
    methodology_report JSONB,
    polishing_report JSONB,
    final_answer_text TEXT,
    final_answer_citations JSONB,
    total_latency_ms INTEGER,
    total_tool_calls INTEGER,
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_query_traces_user_id
    ON free_will.query_traces (user_id, started_at DESC);

CREATE INDEX IF NOT EXISTS idx_query_traces_started_at
    ON free_will.query_traces (started_at DESC);
