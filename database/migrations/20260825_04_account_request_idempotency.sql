-- Make public account-request persistence and reviewer notification retry-safe.

ALTER TABLE free_will.account_requests
    ADD COLUMN IF NOT EXISTS deduplication_key CHAR(64);

-- Historical rows predate the semantic key. Give each one a stable unique
-- value without merging audit records automatically.
UPDATE free_will.account_requests
SET deduplication_key = md5(request_id) || md5(request_id)
WHERE deduplication_key IS NULL;

ALTER TABLE free_will.account_requests
    ALTER COLUMN deduplication_key SET NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS idx_account_requests_deduplication_key
    ON free_will.account_requests (deduplication_key);

ALTER TABLE free_will.account_requests
    DROP CONSTRAINT IF EXISTS account_requests_reviewer_notification_status_check;

ALTER TABLE free_will.account_requests
    ADD CONSTRAINT account_requests_reviewer_notification_status_check
    CHECK (reviewer_notification_status IN ('pending', 'sending', 'sent', 'failed'));

COMMENT ON COLUMN free_will.account_requests.deduplication_key IS
    'Server-generated daily semantic key preventing duplicate dossiers and notifications on retry.';
