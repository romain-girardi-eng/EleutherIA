-- Persist scholarly account requests as auditable access-review dossiers.
-- Applicant consent is captured with the exact privacy-notice version.

CREATE TABLE IF NOT EXISTS free_will.account_requests (
    request_id VARCHAR(32) PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL
        CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'),
    affiliation VARCHAR(160),
    requested_role VARCHAR(32) NOT NULL
        CHECK (requested_role IN (
            'doctoral_researcher', 'researcher', 'student', 'teacher',
            'independent_scholar', 'other'
        )),
    research_focus TEXT NOT NULL
        CHECK (char_length(research_focus) BETWEEN 20 AND 800),
    intended_use TEXT[] NOT NULL
        CHECK (cardinality(intended_use) BETWEEN 1 AND 5),
    locale VARCHAR(12) NOT NULL,
    privacy_acknowledged BOOLEAN NOT NULL CHECK (privacy_acknowledged),
    privacy_notice_version VARCHAR(32) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'approved', 'rejected', 'withdrawn')),
    reviewer_notification_status VARCHAR(20) NOT NULL DEFAULT 'pending'
        CHECK (reviewer_notification_status IN ('pending', 'sent', 'failed')),
    reviewer_notified_at TIMESTAMPTZ,
    approval_email_status VARCHAR(20) NOT NULL DEFAULT 'pending'
        CHECK (approval_email_status IN ('pending', 'sent', 'failed')),
    approval_email_sent_at TIMESTAMPTZ,
    reviewed_at TIMESTAMPTZ,
    reviewed_by UUID REFERENCES free_will.users(user_id) ON DELETE SET NULL,
    approved_user_id UUID REFERENCES free_will.users(user_id) ON DELETE SET NULL,
    decision_notes TEXT,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_account_requests_email
    ON free_will.account_requests (lower(email));
CREATE INDEX IF NOT EXISTS idx_account_requests_status_created
    ON free_will.account_requests (status, created_at DESC);

REVOKE ALL ON TABLE free_will.account_requests FROM PUBLIC;

COMMENT ON TABLE free_will.account_requests IS
    'Consent-backed scholarly access requests and their human review lifecycle.';
COMMENT ON COLUMN free_will.account_requests.research_focus IS
    'Applicant-provided research context retained for access review and scholarly support.';
