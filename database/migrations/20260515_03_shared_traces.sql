-- shared_traces: read-only public share links for query traces
--
-- A share token is a 64-char random hex string that grants read-only
-- access to a single trace for a limited time (default 30 days).

SET search_path = free_will;

CREATE TABLE IF NOT EXISTS shared_traces (
    token VARCHAR(64) PRIMARY KEY,
    trace_id UUID NOT NULL REFERENCES free_will.query_traces(trace_id) ON DELETE CASCADE,
    created_by UUID NOT NULL REFERENCES free_will.users(user_id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at TIMESTAMPTZ NOT NULL,
    view_count INTEGER DEFAULT 0,
    last_viewed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_shared_traces_token
    ON free_will.shared_traces(token);

CREATE INDEX IF NOT EXISTS idx_shared_traces_trace_id
    ON free_will.shared_traces(trace_id);
