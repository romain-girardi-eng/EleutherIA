-- login_codes — email one-time-code (OTP) authentication.
--
-- Passwordless login: a user enters their email, receives a short numeric
-- code by email, and exchanges it for a JWT. A code is issued ONLY for an
-- authorized, active user (see backend AUTHORIZED_EMAILS + free_will.users).
--
-- Codes are stored hashed (bcrypt), single-use, short-lived, and
-- attempt-limited. Expired/consumed rows are pruned opportunistically by
-- the backend on each new request.

SET search_path = free_will;

CREATE TABLE IF NOT EXISTS free_will.login_codes (
    code_id     UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    email       VARCHAR(255) NOT NULL,
    code_hash   VARCHAR(255) NOT NULL,
    expires_at  TIMESTAMPTZ NOT NULL,
    attempts    INT         NOT NULL DEFAULT 0,
    consumed_at TIMESTAMPTZ,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_login_codes_email
    ON free_will.login_codes (lower(email));
CREATE INDEX IF NOT EXISTS idx_login_codes_expires_at
    ON free_will.login_codes (expires_at);

COMMENT ON TABLE free_will.login_codes IS
    'Email one-time login codes (OTP). Hashed, single-use, short-lived.';
