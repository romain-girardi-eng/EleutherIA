-- answer_feedback — provenance-bound feedback on GraphRAG answers.
--
-- A rating row is unique per (trace_id, user_email) and can be updated by the
-- same user. Comment-only submissions and typed reports remain append-only so
-- the export preserves every distinct submission.
--
-- trace_id deliberately has no hard foreign key: query trace persistence is
-- best-effort and traces may be pruned independently. Keeping the UUID and an
-- index preserves provenance whenever the trace exists without discarding
-- valuable feedback when it does not.

CREATE SCHEMA IF NOT EXISTS free_will;
SET search_path = free_will;

CREATE TABLE IF NOT EXISTS free_will.answer_feedback (
    id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    trace_id       uuid,
    user_email     text NOT NULL,
    rating         smallint CHECK (rating IS NULL OR rating BETWEEN 1 AND 5),
    comment        text,
    report_type    text CHECK (
        report_type IS NULL OR report_type IN (
            'factual_error',
            'wrong_citation',
            'missing_source',
            'ui_issue',
            'improvement',
            'other'
        )
    ),
    report_text    text,
    answer_excerpt text,
    app_commit     text,
    model          text,
    created_at     timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT answer_feedback_has_content CHECK (
        rating IS NOT NULL
        OR NULLIF(btrim(comment), '') IS NOT NULL
        OR report_type IS NOT NULL
    ),
    CONSTRAINT answer_feedback_report_is_complete CHECK (
        (report_type IS NULL AND report_text IS NULL)
        OR (report_type IS NOT NULL AND NULLIF(btrim(report_text), '') IS NOT NULL)
    )
);

-- Only rating-bearing rows are upserted. A later comment-only submission gets
-- its own row, as do all error/improvement reports.
CREATE UNIQUE INDEX IF NOT EXISTS uq_answer_feedback_rating_per_user_trace
    ON free_will.answer_feedback (trace_id, user_email)
    WHERE rating IS NOT NULL AND report_type IS NULL;

CREATE INDEX IF NOT EXISTS idx_answer_feedback_trace_created
    ON free_will.answer_feedback (trace_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_answer_feedback_user_created
    ON free_will.answer_feedback (user_email, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_answer_feedback_created
    ON free_will.answer_feedback (created_at DESC);

COMMENT ON TABLE free_will.answer_feedback IS
    'User ratings, impressions, and typed reports attached to GraphRAG trace provenance.';

COMMENT ON COLUMN free_will.answer_feedback.trace_id IS
    'Logical reference to free_will.query_traces.trace_id; intentionally not a hard FK.';
