-- G5 retrieval correctness — passage-level anchoring for oga_tokens.
--
-- Problem: oga_tokens only carries work_id, so the lemmatic retrieval leg
-- (SQLStrategy._step_lemma_lookup) joined passages on work_id and returned
-- up to 40 arbitrary passages per matching work. This migration adds
-- oga_tokens.passage_id and backfills it mechanically where the join key
-- is derivable from existing data.
--
-- Derivation: oga_tokens.cts_urn ↔ passages.cts_urn (within the same work).
-- The passages table has no token-position ranges, so position-based
-- derivation is NOT possible from the schema alone; CTS URNs are the only
-- shared key. Two passes:
--   1. exact URN match;
--   2. token URNs carrying a subreference (e.g. ...:1.1@word[3]) matched
--      after stripping everything from '@'.
-- Both passes only assign when the (work_id, cts_urn) pair resolves to
-- exactly ONE passage, so no token is ever anchored ambiguously.
--
-- MANUAL VERIFICATION STEP (required after applying):
--   Tokens left with passage_id IS NULL have a NULL/unmatched/ambiguous
--   cts_urn and cannot be derived mechanically. Inspect with:
--     SELECT work_id, count(*) FROM free_will.oga_tokens
--     WHERE passage_id IS NULL GROUP BY work_id ORDER BY count(*) DESC;
--   These need re-ingestion with passage anchoring or per-work manual
--   alignment. The application code is capability-aware and keeps working
--   either way (NULL-anchored tokens simply do not contribute hits on the
--   passage-level path).
--
-- Runs inside a single transaction — apply_schema.py executes each file as
-- one statement, so the whole migration applies (or rolls back) atomically.
-- The index is a plain CREATE INDEX: CONCURRENTLY cannot run in a
-- transaction block, and a brief lock on oga_tokens during a maintenance
-- window is acceptable.

ALTER TABLE free_will.oga_tokens
    ADD COLUMN IF NOT EXISTS passage_id UUID
    REFERENCES free_will.passages(passage_id) ON DELETE SET NULL;

-- Pass 1: exact CTS URN match, unambiguous within the work.
UPDATE free_will.oga_tokens t
SET passage_id = u.passage_id
FROM (
    SELECT work_id, cts_urn, MIN(passage_id::text)::uuid AS passage_id
    FROM free_will.passages
    WHERE cts_urn IS NOT NULL
    GROUP BY work_id, cts_urn
    HAVING count(*) = 1
) u
WHERE t.passage_id IS NULL
  AND t.cts_urn IS NOT NULL
  AND u.work_id = t.work_id
  AND u.cts_urn = t.cts_urn;

-- Pass 2: token-level URNs with a @subreference — strip and re-match.
UPDATE free_will.oga_tokens t
SET passage_id = u.passage_id
FROM (
    SELECT work_id, cts_urn, MIN(passage_id::text)::uuid AS passage_id
    FROM free_will.passages
    WHERE cts_urn IS NOT NULL
    GROUP BY work_id, cts_urn
    HAVING count(*) = 1
) u
WHERE t.passage_id IS NULL
  AND t.cts_urn LIKE '%@%'
  AND u.work_id = t.work_id
  AND u.cts_urn = split_part(t.cts_urn, '@', 1);

CREATE INDEX IF NOT EXISTS idx_oga_tokens_passage_id
    ON free_will.oga_tokens(passage_id);

ANALYZE free_will.oga_tokens;
