-- Page-level evidence store for modern secondary literature.
--
-- This migration creates a provenance boundary between KG claims and the
-- actual manifestation/page text used by CitationVerifierV2.  It deliberately
-- does not backfill from kg_nodes.description, quote_page, or inferred PDF
-- offsets: those fields are discovery metadata, not an independently checked
-- page concordance.
--
-- Apply:
--   python database/scripts/apply_schema.py \
--       --migration database/migrations/20260824_03_secondary_page_evidence.sql
--
-- Then validate a local manifest without writing:
--   python scripts/ingest_secondary_evidence_manifest.py \
--       --manifest /trusted/local/secondary-evidence.json
--
-- Ingest only after manual page concordance/review:
--   python scripts/ingest_secondary_evidence_manifest.py \
--       --manifest /trusted/local/secondary-evidence.json --apply
--
-- Backfill policy (intentionally manual):
--   1. Register the exact local source artifact and its SHA-256.
--   2. Map physical PDF/image pages to printed pages by inspection; printed_page
--      stays NULL when the source has no printed pagination.
--   3. Extract each selected page, record its NFC-text SHA-256, and review it
--      against the registered artifact.
--   4. Mark artifact/page review_status='reviewed' only with reviewer + time.
--   5. Never derive a page mapping from an existing KG claim or biography.
--
-- Runtime access is private.  No anon/authenticated policy is created because
-- page text may be copyrighted; the service_role gets read-only access and
-- ingestion is performed through a maintenance connection.

CREATE TABLE IF NOT EXISTS free_will.secondary_source_artifacts (
    manifestation_id TEXT PRIMARY KEY,
    publication_id TEXT NOT NULL
        REFERENCES free_will.kg_nodes(node_id) ON DELETE RESTRICT,
    source_locator TEXT NOT NULL,
    source_sha256 TEXT NOT NULL,
    media_type TEXT NOT NULL,
    rights_status TEXT NOT NULL,
    reuse_status TEXT NOT NULL,
    extraction_status TEXT NOT NULL DEFAULT 'registered',
    review_status TEXT NOT NULL DEFAULT 'unreviewed',
    reviewed_by TEXT,
    reviewed_at TIMESTAMPTZ,
    manifest_metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_secondary_artifact_manifestation_source
        UNIQUE (manifestation_id, source_sha256),
    CONSTRAINT chk_secondary_artifact_manifestation_id
        CHECK (manifestation_id ~ '^[a-z0-9][a-z0-9_.:-]{2,127}$'),
    CONSTRAINT chk_secondary_artifact_source_locator
        CHECK (btrim(source_locator) <> ''),
    CONSTRAINT chk_secondary_artifact_source_sha256
        CHECK (source_sha256 ~ '^[0-9a-f]{64}$'),
    CONSTRAINT chk_secondary_artifact_media_type
        CHECK (btrim(media_type) <> ''),
    CONSTRAINT chk_secondary_artifact_rights_status
        CHECK (rights_status IN (
            'public_domain', 'licensed', 'copyrighted', 'unknown'
        )),
    CONSTRAINT chk_secondary_artifact_reuse_status
        CHECK (reuse_status IN (
            'full_text_allowed', 'quotation_only', 'internal_research_only',
            'metadata_only', 'prohibited', 'unverified_do_not_republish'
        )),
    CONSTRAINT chk_secondary_artifact_extraction_status
        CHECK (extraction_status IN (
            'registered', 'pending', 'partial', 'complete', 'failed'
        )),
    CONSTRAINT chk_secondary_artifact_review_status
        CHECK (review_status IN (
            'unreviewed', 'in_review', 'reviewed', 'rejected'
        )),
    CONSTRAINT chk_secondary_artifact_review_provenance
        CHECK (
            review_status <> 'reviewed'
            OR (
                extraction_status IN ('partial', 'complete')
                AND
                reviewed_by IS NOT NULL AND btrim(reviewed_by) <> ''
                AND reviewed_at IS NOT NULL
            )
        )
);

CREATE TABLE IF NOT EXISTS free_will.secondary_evidence_pages (
    manifestation_id TEXT NOT NULL,
    source_sha256 TEXT NOT NULL,
    physical_page INTEGER NOT NULL,
    printed_page TEXT,
    page_locator TEXT,
    text_content TEXT,
    text_sha256 TEXT,
    extraction_status TEXT NOT NULL DEFAULT 'pending',
    review_status TEXT NOT NULL DEFAULT 'unreviewed',
    reviewed_by TEXT,
    reviewed_at TIMESTAMPTZ,
    extraction_metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (manifestation_id, physical_page),
    CONSTRAINT fk_secondary_page_artifact_source
        FOREIGN KEY (manifestation_id, source_sha256)
        REFERENCES free_will.secondary_source_artifacts(
            manifestation_id, source_sha256
        )
        ON DELETE RESTRICT,
    CONSTRAINT chk_secondary_page_physical_page
        CHECK (physical_page > 0),
    CONSTRAINT chk_secondary_page_printed_page
        CHECK (
            printed_page IS NULL
            OR printed_page ~* '^([1-9][0-9]*[a-z]?|[ivxlcdm]+)$'
        ),
    CONSTRAINT chk_secondary_page_source_sha256
        CHECK (source_sha256 ~ '^[0-9a-f]{64}$'),
    CONSTRAINT chk_secondary_page_text_sha256
        CHECK (text_sha256 IS NULL OR text_sha256 ~ '^[0-9a-f]{64}$'),
    CONSTRAINT chk_secondary_page_extraction_status
        CHECK (extraction_status IN ('pending', 'extracted', 'failed')),
    CONSTRAINT chk_secondary_page_review_status
        CHECK (review_status IN (
            'unreviewed', 'in_review', 'reviewed', 'rejected'
        )),
    CONSTRAINT chk_secondary_page_extracted_payload
        CHECK (
            extraction_status <> 'extracted'
            OR (
                text_content IS NOT NULL AND btrim(text_content) <> ''
                AND text_sha256 IS NOT NULL
            )
        ),
    CONSTRAINT chk_secondary_page_review_provenance
        CHECK (
            review_status <> 'reviewed'
            OR (
                extraction_status = 'extracted'
                AND text_content IS NOT NULL AND btrim(text_content) <> ''
                AND text_sha256 IS NOT NULL
                AND reviewed_by IS NOT NULL AND btrim(reviewed_by) <> ''
                AND reviewed_at IS NOT NULL
            )
        )
);

CREATE INDEX IF NOT EXISTS idx_secondary_artifacts_publication
    ON free_will.secondary_source_artifacts (publication_id);

CREATE INDEX IF NOT EXISTS idx_secondary_artifacts_reviewed
    ON free_will.secondary_source_artifacts (publication_id, review_status)
    WHERE review_status = 'reviewed';

CREATE INDEX IF NOT EXISTS idx_secondary_pages_printed_page
    ON free_will.secondary_evidence_pages (manifestation_id, printed_page)
    WHERE printed_page IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_secondary_pages_reviewed
    ON free_will.secondary_evidence_pages (manifestation_id, review_status)
    WHERE review_status = 'reviewed';

ALTER TABLE free_will.secondary_source_artifacts ENABLE ROW LEVEL SECURITY;
ALTER TABLE free_will.secondary_evidence_pages ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON TABLE free_will.secondary_source_artifacts
    FROM PUBLIC, anon, authenticated;
REVOKE ALL ON TABLE free_will.secondary_evidence_pages
    FROM PUBLIC, anon, authenticated;

GRANT SELECT ON TABLE free_will.secondary_source_artifacts TO service_role;
GRANT SELECT ON TABLE free_will.secondary_evidence_pages TO service_role;

COMMENT ON TABLE free_will.secondary_source_artifacts IS
    'Exact manifestations of secondary publications; source SHA and review metadata are provenance, never inferred from KG claims.';
COMMENT ON TABLE free_will.secondary_evidence_pages IS
    'Physical-to-printed page concordance and reviewed extracted page text for independent secondary-source verification.';
COMMENT ON COLUMN free_will.secondary_evidence_pages.printed_page IS
    'Printed page label transcribed by review; NULL means no verified printed pagination.';
COMMENT ON COLUMN free_will.secondary_evidence_pages.text_sha256 IS
    'SHA-256 of NFC-normalized text_content, verified again by GraphRAG at read time.';
