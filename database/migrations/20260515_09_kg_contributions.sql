-- kg_contributions — Feature 8 backbone (community PDF contributions).
--
-- A researcher uploads a scholarly PDF (Bobzien, Frede, etc.); a downstream
-- Temporal workflow extracts free-will-relevant entities and proposes new
-- nodes / edges / passage_citations against the live KG. Romain (admin)
-- reviews each proposal, accepts/rejects, and applies the accepted set in
-- one atomic merge.
--
-- Two tables:
--   * kg_contributions          — one row per uploaded PDF (lifecycle status)
--   * kg_contribution_proposals — N rows per contribution (one per atom
--                                  extracted from the PDF: node, edge,
--                                  passage_citation, scholar_ref,
--                                  concept_attestation)
--
-- The kg_version trigger installed by 20260515_08 will fire on the kg_nodes
-- / kg_edges / passage_citations INSERTs that happen at apply-time, so the
-- answer cache invalidates cleanly the moment a contribution is merged.

SET search_path = free_will;

CREATE TABLE IF NOT EXISTS free_will.kg_contributions (
    contribution_id    uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    submitter_user_id  uuid,
    submitted_at       timestamptz NOT NULL DEFAULT now(),
    pdf_url            text NOT NULL,
    pdf_filename       text NOT NULL,
    pdf_size_bytes     bigint NOT NULL,
    title              text,
    authors            text[] NOT NULL DEFAULT ARRAY[]::text[],
    doi                text,
    publication_year   integer,
    pdf_metadata       jsonb NOT NULL DEFAULT '{}'::jsonb,
    relevance_score    numeric(4,3),
    relevance_summary  text,
    free_will_concepts text[] NOT NULL DEFAULT ARRAY[]::text[],
    status             text NOT NULL DEFAULT 'pending'
                       CHECK (status IN (
                           'uploaded', 'processing', 'ready',
                           'approved', 'rejected', 'merged', 'failed'
                       )),
    processing_error   text,
    reviewer_notes     text,
    reviewer_user_id   uuid,
    reviewed_at        timestamptz,
    merged_at          timestamptz
);

-- submitter FK only when the user exists in free_will.users (nullable for
-- anonymous uploads). The FK is added separately so the migration tolerates
-- environments where the users table lives in a different schema.
DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.tables
        WHERE table_schema = 'free_will' AND table_name = 'users'
    ) AND NOT EXISTS (
        SELECT 1
        FROM information_schema.table_constraints
        WHERE table_schema = 'free_will'
          AND table_name = 'kg_contributions'
          AND constraint_name = 'kg_contributions_submitter_user_id_fkey'
    ) THEN
        ALTER TABLE free_will.kg_contributions
            ADD CONSTRAINT kg_contributions_submitter_user_id_fkey
            FOREIGN KEY (submitter_user_id)
            REFERENCES free_will.users(user_id)
            ON DELETE SET NULL;
    END IF;
END
$$;

CREATE INDEX IF NOT EXISTS idx_kg_contributions_status_submitted
    ON free_will.kg_contributions(status, submitted_at DESC);
CREATE INDEX IF NOT EXISTS idx_kg_contributions_submitter
    ON free_will.kg_contributions(submitter_user_id);


CREATE TABLE IF NOT EXISTS free_will.kg_contribution_proposals (
    proposal_id      uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    contribution_id  uuid NOT NULL
                     REFERENCES free_will.kg_contributions(contribution_id)
                     ON DELETE CASCADE,
    kind             text NOT NULL CHECK (kind IN (
                         'node', 'edge', 'passage_citation',
                         'scholar_ref', 'concept_attestation'
                     )),
    payload          jsonb NOT NULL,
    target_kg_id     text,
    confidence       numeric(4,3) NOT NULL DEFAULT 0.5,
    evidence         jsonb NOT NULL DEFAULT '{}'::jsonb,
    status           text NOT NULL DEFAULT 'pending'
                     CHECK (status IN (
                         'pending', 'accepted', 'rejected',
                         'superseded', 'applied'
                     )),
    reviewer_notes   text,
    applied_at       timestamptz,
    created_at       timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_proposals_contribution
    ON free_will.kg_contribution_proposals(contribution_id);
CREATE INDEX IF NOT EXISTS idx_proposals_status
    ON free_will.kg_contribution_proposals(status);
CREATE INDEX IF NOT EXISTS idx_proposals_kind
    ON free_will.kg_contribution_proposals(kind);
