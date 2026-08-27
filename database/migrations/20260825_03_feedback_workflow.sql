-- Turn answer feedback into a broader, admin-triaged product/scholarly inbox.

ALTER TABLE free_will.answer_feedback
    ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES free_will.users(user_id) ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS scope TEXT NOT NULL DEFAULT 'answer',
    ADD COLUMN IF NOT EXISTS severity TEXT NOT NULL DEFAULT 'normal',
    ADD COLUMN IF NOT EXISTS page_url TEXT,
    ADD COLUMN IF NOT EXISTS entity_id TEXT,
    ADD COLUMN IF NOT EXISTS contact_allowed BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS status TEXT NOT NULL DEFAULT 'new',
    ADD COLUMN IF NOT EXISTS admin_notes TEXT,
    ADD COLUMN IF NOT EXISTS assigned_to UUID REFERENCES free_will.users(user_id) ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    ADD COLUMN IF NOT EXISTS resolved_at TIMESTAMPTZ;

ALTER TABLE free_will.answer_feedback
    DROP CONSTRAINT IF EXISTS answer_feedback_report_type_check,
    ADD CONSTRAINT answer_feedback_report_type_check CHECK (
        report_type IS NULL OR report_type IN (
            'factual_error', 'wrong_citation', 'missing_source', 'ui_issue',
            'accessibility', 'performance', 'account_access', 'feature_request',
            'improvement', 'other'
        )
    ),
    -- Every deploy replays the whole migration list (there is no applied-
    -- migrations ledger), so each constraint must be droppable before re-add.
    DROP CONSTRAINT IF EXISTS answer_feedback_scope_check,
    ADD CONSTRAINT answer_feedback_scope_check CHECK (
        scope IN ('answer', 'page', 'node', 'source', 'data', 'ux', 'account', 'other')
    ),
    DROP CONSTRAINT IF EXISTS answer_feedback_severity_check,
    ADD CONSTRAINT answer_feedback_severity_check CHECK (
        severity IN ('low', 'normal', 'high', 'critical')
    ),
    DROP CONSTRAINT IF EXISTS answer_feedback_status_check,
    ADD CONSTRAINT answer_feedback_status_check CHECK (
        status IN ('new', 'triaged', 'in_progress', 'resolved', 'dismissed')
    );

CREATE INDEX IF NOT EXISTS idx_answer_feedback_status_created
    ON free_will.answer_feedback(status, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_answer_feedback_user_id_created
    ON free_will.answer_feedback(user_id, created_at DESC);

COMMENT ON COLUMN free_will.answer_feedback.scope IS
    'Product or scholarly surface the feedback concerns.';
COMMENT ON COLUMN free_will.answer_feedback.status IS
    'Admin triage lifecycle for the feedback inbox.';
