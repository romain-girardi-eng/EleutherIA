-- Admin-controlled user budgets, capabilities, and immutable action audit.

CREATE TABLE IF NOT EXISTS free_will.user_access_policies (
    user_id UUID PRIMARY KEY
        REFERENCES free_will.users(user_id) ON DELETE CASCADE,
    monthly_token_limit BIGINT CHECK (monthly_token_limit IS NULL OR monthly_token_limit >= 0),
    monthly_cost_limit_usd NUMERIC(12,4)
        CHECK (monthly_cost_limit_usd IS NULL OR monthly_cost_limit_usd >= 0),
    monthly_query_limit INTEGER
        CHECK (monthly_query_limit IS NULL OR monthly_query_limit >= 0),
    allow_deep_mode BOOLEAN NOT NULL DEFAULT TRUE,
    notes TEXT,
    updated_by UUID REFERENCES free_will.users(user_id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS free_will.user_admin_actions (
    action_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    actor_user_id UUID REFERENCES free_will.users(user_id) ON DELETE SET NULL,
    target_user_id UUID NOT NULL REFERENCES free_will.users(user_id) ON DELETE CASCADE,
    action VARCHAR(40) NOT NULL CHECK (action IN (
        'account_approved', 'role_changed', 'activation_changed',
        'limits_changed', 'welcome_resent'
    )),
    before_state JSONB NOT NULL DEFAULT '{}'::jsonb,
    after_state JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_user_admin_actions_target_created
    ON free_will.user_admin_actions(target_user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_user_admin_actions_actor_created
    ON free_will.user_admin_actions(actor_user_id, created_at DESC);

REVOKE ALL ON TABLE free_will.user_access_policies FROM PUBLIC;
REVOKE ALL ON TABLE free_will.user_admin_actions FROM PUBLIC;

COMMENT ON TABLE free_will.user_access_policies IS
    'Admin-managed monthly LLM budgets and feature capabilities per user.';
COMMENT ON TABLE free_will.user_admin_actions IS
    'Immutable audit trail for changes to user access, roles, and budgets.';
