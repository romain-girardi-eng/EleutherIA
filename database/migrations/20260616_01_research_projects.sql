-- research_projects + project_documents — per-user research workspaces.
--
-- Users can create named projects, upload PDFs or plain-text documents,
-- and browse the extracted text for use in GraphRAG queries.
--
-- Three tables:
--   * research_projects         — one row per workspace (owned by a user)
--   * project_documents         — document metadata + extracted text
--   * project_document_blobs    — raw bytes stored as BYTEA, split off so
--                                  list queries never drag large payloads

SET search_path = free_will;

-- -----------------------------------------------------------------------
-- research_projects
-- -----------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS free_will.research_projects (
    project_id   UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id      UUID        NOT NULL
                             REFERENCES free_will.users(user_id)
                             ON DELETE CASCADE,
    name         TEXT        NOT NULL,
    description  TEXT,
    status       TEXT        NOT NULL DEFAULT 'active',
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_research_projects_user_id
    ON free_will.research_projects(user_id);

-- -----------------------------------------------------------------------
-- project_documents
-- -----------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS free_will.project_documents (
    document_id    UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id     UUID        NOT NULL
                               REFERENCES free_will.research_projects(project_id)
                               ON DELETE CASCADE,
    user_id        UUID        NOT NULL
                               REFERENCES free_will.users(user_id)
                               ON DELETE CASCADE,
    filename       TEXT        NOT NULL,
    content_type   TEXT,
    size_bytes     BIGINT,
    page_count     INTEGER,
    extracted_text TEXT,
    page_texts     JSONB,
    status         TEXT        NOT NULL DEFAULT 'processing',
    metadata       JSONB       NOT NULL DEFAULT '{}'::jsonb,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_project_documents_project_id
    ON free_will.project_documents(project_id);

-- -----------------------------------------------------------------------
-- project_document_blobs
-- -----------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS free_will.project_document_blobs (
    document_id UUID  PRIMARY KEY
                      REFERENCES free_will.project_documents(document_id)
                      ON DELETE CASCADE,
    bytes       BYTEA NOT NULL
);

-- -----------------------------------------------------------------------
-- Role grants (matching the pattern in 20260313_03_rpc_perf_and_security.sql)
-- These tables are user-owned; the backend service_role account handles all
-- writes. anon/authenticated are granted SELECT so the PostgREST layer
-- (if ever re-enabled) can serve read requests through RLS.
-- -----------------------------------------------------------------------

GRANT SELECT, INSERT, UPDATE, DELETE
    ON TABLE free_will.research_projects
    TO service_role;

GRANT SELECT
    ON TABLE free_will.research_projects
    TO anon, authenticated;

GRANT SELECT, INSERT, UPDATE, DELETE
    ON TABLE free_will.project_documents
    TO service_role;

GRANT SELECT
    ON TABLE free_will.project_documents
    TO anon, authenticated;

GRANT SELECT, INSERT, DELETE
    ON TABLE free_will.project_document_blobs
    TO service_role;
