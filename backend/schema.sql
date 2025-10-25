-- Ancient Free Will Database - PostgreSQL Schema
-- Version: 1.0.0
-- Database: ancient_free_will_db
-- Generated: 2025-10-25

-- ============================================
-- Extensions
-- ============================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- Trigram similarity for fuzzy search

-- ============================================
-- Tables
-- ============================================

-- Texts table: Stores ancient Greek and Latin texts
CREATE TABLE IF NOT EXISTS texts (
    text_id VARCHAR(255) PRIMARY KEY,
    title TEXT NOT NULL,
    author VARCHAR(255),
    category VARCHAR(100),
    language VARCHAR(20) CHECK (language IN ('greek', 'latin', 'english')),
    content TEXT NOT NULL,
    lemmatized_content TEXT,
    word_count INTEGER,
    metadata JSONB DEFAULT '{}',
    tei_xml TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Full-text search index
CREATE INDEX IF NOT EXISTS idx_texts_fulltext
    ON texts USING GIN (to_tsvector('english', content));

-- Lemmatized search index
CREATE INDEX IF NOT EXISTS idx_texts_lemmatic
    ON texts USING GIN (to_tsvector('simple', lemmatized_content));

-- Trigram index for fuzzy search
CREATE INDEX IF NOT EXISTS idx_texts_title_trgm
    ON texts USING GIN (title gin_trgm_ops);

CREATE INDEX IF NOT EXISTS idx_texts_author_trgm
    ON texts USING GIN (author gin_trgm_ops);

-- Category and language indexes
CREATE INDEX IF NOT EXISTS idx_texts_category ON texts(category);
CREATE INDEX IF NOT EXISTS idx_texts_language ON texts(language);
CREATE INDEX IF NOT EXISTS idx_texts_author ON texts(author);

-- Metadata JSONB index
CREATE INDEX IF NOT EXISTS idx_texts_metadata ON texts USING GIN (metadata);

-- Embeddings table: Stores vector embeddings for semantic search
CREATE TABLE IF NOT EXISTS text_embeddings (
    embedding_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    text_id VARCHAR(255) REFERENCES texts(text_id) ON DELETE CASCADE,
    embedding_vector FLOAT8[] NOT NULL,
    embedding_model VARCHAR(100) DEFAULT 'gemini-embedding-004',
    embedding_dimensions INTEGER DEFAULT 3072,
    chunk_index INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_embeddings_text_id ON text_embeddings(text_id);

-- Users table: For authentication
CREATE TABLE IF NOT EXISTS users (
    user_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active);

-- API Keys table: For programmatic access
CREATE TABLE IF NOT EXISTS api_keys (
    key_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(user_id) ON DELETE CASCADE,
    key_hash VARCHAR(255) NOT NULL,
    key_name VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_api_keys_user_id ON api_keys(user_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_active ON api_keys(is_active);

-- Query logs table: For analytics and monitoring
CREATE TABLE IF NOT EXISTS query_logs (
    log_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(user_id) ON DELETE SET NULL,
    query_type VARCHAR(50) NOT NULL,  -- graphrag, search, kg
    query_text TEXT,
    response_time_ms INTEGER,
    results_count INTEGER,
    status VARCHAR(20),  -- success, error
    error_message TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_query_logs_user_id ON query_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_query_logs_query_type ON query_logs(query_type);
CREATE INDEX IF NOT EXISTS idx_query_logs_created_at ON query_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_query_logs_status ON query_logs(status);

-- Cache table: For caching expensive operations
CREATE TABLE IF NOT EXISTS cache_entries (
    cache_key VARCHAR(255) PRIMARY KEY,
    cache_value JSONB NOT NULL,
    ttl_seconds INTEGER DEFAULT 3600,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_cache_expires_at ON cache_entries(expires_at);

-- ============================================
-- Functions
-- ============================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for texts table
CREATE TRIGGER update_texts_updated_at
    BEFORE UPDATE ON texts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Function to clean expired cache entries
CREATE OR REPLACE FUNCTION clean_expired_cache()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM cache_entries WHERE expires_at < CURRENT_TIMESTAMP;
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- Views
-- ============================================

-- View for text statistics
CREATE OR REPLACE VIEW text_statistics AS
SELECT
    category,
    language,
    COUNT(*) as text_count,
    SUM(word_count) as total_words,
    COUNT(CASE WHEN lemmatized_content IS NOT NULL THEN 1 END) as lemmatized_count,
    AVG(word_count) as avg_word_count
FROM texts
GROUP BY category, language;

-- View for user activity
CREATE OR REPLACE VIEW user_activity AS
SELECT
    u.user_id,
    u.username,
    u.email,
    COUNT(q.log_id) as total_queries,
    COUNT(CASE WHEN q.status = 'success' THEN 1 END) as successful_queries,
    AVG(q.response_time_ms) as avg_response_time,
    MAX(q.created_at) as last_query_at
FROM users u
LEFT JOIN query_logs q ON u.user_id = q.user_id
GROUP BY u.user_id, u.username, u.email;

-- ============================================
-- Initial Data
-- ============================================

-- Create default admin user (password: admin123 - CHANGE IN PRODUCTION!)
-- Password hash is bcrypt of 'admin123'
INSERT INTO users (username, email, password_hash, is_admin)
VALUES (
    'admin',
    'admin@ancientfreewill.org',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5lBN0jHnJJe3W',
    TRUE
) ON CONFLICT (username) DO NOTHING;

-- ============================================
-- Performance Tuning
-- ============================================

-- Analyze tables for query optimization
ANALYZE texts;
ANALYZE text_embeddings;
ANALYZE users;
ANALYZE query_logs;

-- ============================================
-- Maintenance
-- ============================================

-- Schedule cache cleanup (requires pg_cron extension)
-- SELECT cron.schedule('clean-cache', '0 */6 * * *', 'SELECT clean_expired_cache();');

-- Vacuum and analyze periodically
-- VACUUM ANALYZE texts;
-- VACUUM ANALYZE query_logs;

-- ============================================
-- Backup Recommendations
-- ============================================

-- Daily backups:
-- pg_dump -h localhost -U free_will_user -d ancient_free_will_db -F c -b -v -f backup_$(date +%Y%m%d).dump

-- Restore from backup:
-- pg_restore -h localhost -U free_will_user -d ancient_free_will_db -v backup_20251025.dump

-- ============================================
-- Security
-- ============================================

-- Grant appropriate permissions
GRANT SELECT ON ALL TABLES IN SCHEMA public TO readonly_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_user;

-- Revoke public access
REVOKE ALL ON SCHEMA public FROM PUBLIC;

-- ============================================
-- End of Schema
-- ============================================
