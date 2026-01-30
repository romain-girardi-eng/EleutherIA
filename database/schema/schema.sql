-- EleutherIA Database Schema
-- Version: 2.0.0
-- Schema: free_will
-- Updated: 2025-11-17
--
-- This schema reflects the actual production database structure.
-- The legacy `texts` table was dropped on 2025-11-11 in favor of
-- the canonical `ancient_works` + `passages` system.

-- ============================================
-- Schema Setup
-- ============================================

CREATE SCHEMA IF NOT EXISTS free_will;
SET search_path = free_will;

-- ============================================
-- Core Tables: Ancient Works System
-- ============================================

-- Ancient Works: Canonical scholarly texts with CTS URN support
CREATE TABLE IF NOT EXISTS ancient_works (
    work_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    kg_work_id TEXT,  -- Reference to KG node if applicable
    canonical_id TEXT NOT NULL UNIQUE,  -- e.g., 'chrysippus_on_fate'
    title TEXT NOT NULL,
    title_original TEXT,  -- Original Greek/Latin title
    author TEXT NOT NULL,
    author_original TEXT,  -- Original Greek/Latin author name
    language TEXT NOT NULL CHECK (language IN ('grc', 'lat', 'eng', 'hbo', 'ara')),
    period TEXT,  -- e.g., 'Hellenistic', 'Imperial'
    date_composed TEXT,  -- Approximate date, e.g., '3rd c. BCE'
    school TEXT,  -- Philosophical school, e.g., 'Stoic'
    full_text TEXT,  -- Complete text (for smaller works)
    tei_xml TEXT,  -- TEI XML markup if available
    source TEXT,  -- Data source (e.g., 'perseus', 'tlg', 'sblgnt')
    source_url TEXT,
    license TEXT,
    division_scheme TEXT,  -- e.g., 'book.chapter.section'
    total_divisions INTEGER,
    total_words INTEGER CHECK (total_words IS NULL OR total_words >= 0),
    total_chars INTEGER CHECK (total_chars IS NULL OR total_chars >= 0),
    notes TEXT,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    tlg_code TEXT,  -- TLG identifier if applicable
    cts_urn TEXT,  -- Canonical Text Services URN
    citation_levels TEXT[],  -- e.g., ARRAY['book', 'chapter', 'verse']
    has_morphology BOOLEAN DEFAULT FALSE  -- Whether OGA lemmatization exists
);

-- Indexes for ancient_works
CREATE INDEX IF NOT EXISTS idx_ancient_works_author ON ancient_works(author);
CREATE INDEX IF NOT EXISTS idx_ancient_works_language ON ancient_works(language);
CREATE INDEX IF NOT EXISTS idx_ancient_works_period ON ancient_works(period);
CREATE INDEX IF NOT EXISTS idx_ancient_works_school ON ancient_works(school);
CREATE INDEX IF NOT EXISTS idx_ancient_works_source ON ancient_works(source);
CREATE INDEX IF NOT EXISTS idx_ancient_works_kg_work_id ON ancient_works(kg_work_id);
CREATE INDEX IF NOT EXISTS idx_ancient_works_cts_urn ON ancient_works(cts_urn);
CREATE INDEX IF NOT EXISTS idx_ancient_works_metadata ON ancient_works USING GIN (metadata);

-- Passages: Hierarchical text units with CTS URN support
CREATE TABLE IF NOT EXISTS passages (
    passage_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    work_id UUID NOT NULL REFERENCES ancient_works(work_id) ON DELETE CASCADE,
    canonical_ref TEXT NOT NULL,  -- e.g., '3.191' or 'Matthew 5:3'
    cts_urn TEXT,  -- Full CTS URN for this passage
    book TEXT,
    chapter TEXT,
    section TEXT,
    subsection TEXT,
    line_start TEXT,
    line_end TEXT,
    sequence_number INTEGER NOT NULL CHECK (sequence_number >= 0),
    text_content TEXT NOT NULL,
    char_length INTEGER CHECK (char_length IS NULL OR char_length >= 0),
    word_count INTEGER CHECK (word_count IS NULL OR word_count >= 0),
    previous_passage_id UUID REFERENCES passages(passage_id),
    next_passage_id UUID REFERENCES passages(passage_id),
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    citation_hierarchy JSONB,  -- Structured citation path
    morphology JSONB  -- Lemmatization data if available
);

-- Indexes for passages
CREATE INDEX IF NOT EXISTS idx_passages_work_id ON passages(work_id);
CREATE INDEX IF NOT EXISTS idx_passages_canonical_ref ON passages(canonical_ref);
CREATE INDEX IF NOT EXISTS idx_passages_cts_urn ON passages(cts_urn);
CREATE INDEX IF NOT EXISTS idx_passages_sequence ON passages(work_id, sequence_number);
CREATE INDEX IF NOT EXISTS idx_passages_book ON passages(book);
CREATE INDEX IF NOT EXISTS idx_passages_chapter ON passages(chapter);
CREATE INDEX IF NOT EXISTS idx_passages_fulltext ON passages USING GIN (to_tsvector('simple', text_content));
CREATE INDEX IF NOT EXISTS idx_passages_citation_hierarchy ON passages USING GIN (citation_hierarchy);

-- Passage Citations: Links passages to knowledge graph nodes
CREATE TABLE IF NOT EXISTS passage_citations (
    citation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    passage_id UUID NOT NULL REFERENCES passages(passage_id) ON DELETE CASCADE,
    kg_node_id TEXT NOT NULL,  -- Knowledge graph node identifier
    citation_type TEXT,  -- e.g., 'primary_source', 'secondary_source'
    confidence DOUBLE PRECISION CHECK (confidence IS NULL OR (confidence >= 0.0 AND confidence <= 1.0)),
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Indexes for passage_citations
CREATE INDEX IF NOT EXISTS idx_passage_citations_passage_id ON passage_citations(passage_id);
CREATE INDEX IF NOT EXISTS idx_passage_citations_kg_node_id ON passage_citations(kg_node_id);
CREATE INDEX IF NOT EXISTS idx_passage_citations_confidence ON passage_citations(confidence);

-- Passage Relationships: Inter-passage references and parallels
CREATE TABLE IF NOT EXISTS passage_relationships (
    relationship_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_passage_id UUID NOT NULL REFERENCES passages(passage_id) ON DELETE CASCADE,
    target_passage_id UUID NOT NULL REFERENCES passages(passage_id) ON DELETE CASCADE,
    relationship_type TEXT NOT NULL,  -- e.g., 'quotes', 'alludes_to', 'parallel'
    confidence DOUBLE PRECISION DEFAULT 1.0 CHECK (confidence IS NULL OR (confidence >= 0.0 AND confidence <= 1.0)),
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Indexes for passage_relationships
CREATE INDEX IF NOT EXISTS idx_passage_relationships_source ON passage_relationships(source_passage_id);
CREATE INDEX IF NOT EXISTS idx_passage_relationships_target ON passage_relationships(target_passage_id);
CREATE INDEX IF NOT EXISTS idx_passage_relationships_type ON passage_relationships(relationship_type);

-- ============================================
-- Views for Search Optimization
-- ============================================

-- passage_search: Lightweight view for search (no storage overhead)
CREATE OR REPLACE VIEW passage_search AS
SELECT
    p.passage_id,
    p.work_id,
    p.canonical_ref,
    p.text_content,
    p.sequence_number,
    p.char_length,
    p.word_count,
    p.created_at,
    w.title,
    w.author,
    w.language,
    w.period,
    w.school,
    w.canonical_id AS work_canonical_id,
    to_tsvector('simple', p.text_content) AS search_vector
FROM passages p
JOIN ancient_works w ON p.work_id = w.work_id;

-- ============================================
-- Authentication & Authorization
-- ============================================

-- Users with security features
CREATE TABLE IF NOT EXISTS users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) NOT NULL UNIQUE
        CHECK (char_length(username) >= 3 AND char_length(username) <= 50),
    email VARCHAR(255) NOT NULL UNIQUE
        CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'),
    hashed_password VARCHAR(255) NOT NULL
        CHECK (char_length(hashed_password) > 0),
    role VARCHAR(20) NOT NULL DEFAULT 'researcher'
        CHECK (role IN ('admin', 'researcher', 'viewer')),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ,
    last_login_at TIMESTAMPTZ,
    failed_login_attempts INTEGER NOT NULL DEFAULT 0,
    locked_until TIMESTAMPTZ
);

-- Indexes for users
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active);

-- Authentication audit log
CREATE TABLE IF NOT EXISTS auth_audit_log (
    log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(user_id) ON DELETE SET NULL,
    event_type VARCHAR(50) NOT NULL
        CHECK (event_type IN (
            'login_success', 'login_failure', 'logout',
            'password_change', 'password_reset_request', 'password_reset_complete',
            'account_locked', 'account_unlocked', 'account_created',
            'account_deactivated', 'role_changed', 'token_refresh'
        )),
    ip_address INET,
    user_agent TEXT,
    additional_info JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Indexes for auth_audit_log
CREATE INDEX IF NOT EXISTS idx_auth_audit_user_id ON auth_audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_auth_audit_event_type ON auth_audit_log(event_type);
CREATE INDEX IF NOT EXISTS idx_auth_audit_created_at ON auth_audit_log(created_at);

-- ============================================
-- OGA (Open Greek and Latin) Morphology
-- ============================================

-- OGA Tokens: Word-level morphological analysis
CREATE TABLE IF NOT EXISTS oga_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    work_id UUID NOT NULL REFERENCES ancient_works(work_id) ON DELETE CASCADE,
    position INTEGER NOT NULL,
    surface_form TEXT NOT NULL,
    lemma TEXT,
    pos VARCHAR(10),  -- Part of speech
    morphology JSONB,  -- Full morphological features
    cts_urn TEXT,  -- CTS URN for this token
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Indexes for oga_tokens
CREATE INDEX IF NOT EXISTS idx_oga_tokens_work_id ON oga_tokens(work_id);
CREATE INDEX IF NOT EXISTS idx_oga_tokens_lemma ON oga_tokens(lemma);
CREATE INDEX IF NOT EXISTS idx_oga_tokens_pos ON oga_tokens(pos);
CREATE INDEX IF NOT EXISTS idx_oga_tokens_surface ON oga_tokens(surface_form);

-- OGA Dependencies: Syntactic dependencies between tokens
CREATE TABLE IF NOT EXISTS oga_dependencies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dependent_token_id UUID NOT NULL REFERENCES oga_tokens(id) ON DELETE CASCADE,
    head_token_id UUID REFERENCES oga_tokens(id) ON DELETE SET NULL,
    relation VARCHAR(50),  -- e.g., 'nsubj', 'obj', 'amod'
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Indexes for oga_dependencies
CREATE INDEX IF NOT EXISTS idx_oga_deps_dependent ON oga_dependencies(dependent_token_id);
CREATE INDEX IF NOT EXISTS idx_oga_deps_head ON oga_dependencies(head_token_id);
CREATE INDEX IF NOT EXISTS idx_oga_deps_relation ON oga_dependencies(relation);

-- ============================================
-- OGA Analytical Views
-- ============================================

-- Enriched token view with work metadata
CREATE OR REPLACE VIEW oga_tokens_enriched AS
SELECT
    t.id,
    t.position,
    t.surface_form,
    t.lemma,
    t.pos,
    t.morphology,
    t.cts_urn,
    t.work_id,
    w.title AS work_title,
    w.author,
    w.language
FROM oga_tokens t
JOIN ancient_works w ON t.work_id = w.work_id;

-- Work statistics view
CREATE OR REPLACE VIEW oga_work_statistics AS
SELECT
    t.work_id,
    w.title,
    w.author,
    COUNT(*) AS token_count,
    COUNT(DISTINCT t.lemma) AS unique_lemma_count,
    COUNT(DISTINCT t.pos) AS pos_variety
FROM oga_tokens t
JOIN ancient_works w ON t.work_id = w.work_id
GROUP BY t.work_id, w.title, w.author;

-- ============================================
-- Text Sections (Legacy TEI Support)
-- ============================================

CREATE TABLE IF NOT EXISTS text_sections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    text_id UUID NOT NULL,  -- Reference to legacy text ID
    division_id UUID,
    type TEXT NOT NULL,  -- e.g., 'paragraph', 'verse', 'line'
    subtype TEXT,
    n TEXT,  -- Section number/identifier
    content TEXT NOT NULL,
    language TEXT,
    speaker TEXT,  -- For dialogue/drama
    char_position INTEGER,
    xml_id TEXT,  -- Original TEI @xml:id
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- Functions
-- ============================================

-- Update timestamp trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql
SET search_path = free_will;

-- Apply trigger to ancient_works
DROP TRIGGER IF EXISTS update_ancient_works_updated_at ON ancient_works;
CREATE TRIGGER update_ancient_works_updated_at
    BEFORE UPDATE ON ancient_works
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- Statistics & Monitoring Views
-- ============================================

-- Works statistics overview
CREATE OR REPLACE VIEW works_statistics AS
SELECT
    COUNT(*) AS total_works,
    COUNT(DISTINCT author) AS unique_authors,
    SUM(total_words) AS total_words,
    SUM(total_chars) AS total_characters,
    COUNT(CASE WHEN has_morphology THEN 1 END) AS works_with_morphology,
    COUNT(DISTINCT language) AS languages_count
FROM ancient_works;

-- Passages statistics overview
CREATE OR REPLACE VIEW passages_statistics AS
SELECT
    COUNT(*) AS total_passages,
    SUM(word_count) AS total_words,
    SUM(char_length) AS total_characters,
    AVG(word_count) AS avg_passage_words,
    COUNT(DISTINCT work_id) AS works_with_passages
FROM passages;

-- Citation coverage statistics
CREATE OR REPLACE VIEW citation_statistics AS
SELECT
    COUNT(DISTINCT kg_node_id) AS total_kg_nodes_cited,
    COUNT(DISTINCT passage_id) AS total_passages_with_citations,
    AVG(confidence) AS avg_citation_confidence,
    COUNT(*) AS total_citations
FROM passage_citations;

-- ============================================
-- Security & Performance
-- ============================================

-- Grant appropriate permissions (adjust for your environment)
-- GRANT SELECT ON ALL TABLES IN SCHEMA free_will TO readonly_user;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA free_will TO app_user;

-- Analyze all tables for query optimization
ANALYZE ancient_works;
ANALYZE passages;
ANALYZE passage_citations;
ANALYZE users;
ANALYZE oga_tokens;

-- ============================================
-- Migration Notes
-- ============================================

-- The legacy `texts` table (29 texts) was dropped on 2025-11-11.
-- All functionality now uses the canonical `ancient_works` + `passages` system
-- which provides:
-- - 487 ancient works (including complete SBLGNT + LXX)
-- - 69,277 passages with hierarchical structure
-- - Full CTS URN support for canonical scholarly references
-- - Optional OGA morphological analysis for Greek texts

-- ============================================
-- End of Schema
-- ============================================
