-- Philological publication-quality metadata.
-- Adds explicit passage roles, source links for translations/paraphrases, and
-- a relational apparatus table that mirrors KG textual_variant nodes.

SET search_path TO free_will, public;

ALTER TABLE passages
    ADD COLUMN IF NOT EXISTS passage_role TEXT NOT NULL DEFAULT 'original',
    ADD COLUMN IF NOT EXISTS source_passage_id UUID REFERENCES passages(passage_id),
    ADD COLUMN IF NOT EXISTS source_metadata JSONB DEFAULT '{}'::jsonb;

ALTER TABLE passages
    DROP CONSTRAINT IF EXISTS passages_passage_role_check;

ALTER TABLE passages
    ADD CONSTRAINT passages_passage_role_check
    CHECK (passage_role IN ('original', 'translation', 'paraphrase'));

CREATE INDEX IF NOT EXISTS idx_passages_passage_role
    ON passages(passage_role);

CREATE INDEX IF NOT EXISTS idx_passages_source_passage_id
    ON passages(source_passage_id);

CREATE TABLE IF NOT EXISTS textual_variants (
    variant_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    passage_id UUID NOT NULL REFERENCES passages(passage_id) ON DELETE CASCADE,
    kg_node_id TEXT REFERENCES kg_nodes(node_id) ON DELETE SET NULL,
    lemma TEXT NOT NULL,
    lection_principale TEXT NOT NULL,
    lections_alternatives JSONB NOT NULL DEFAULT '[]'::jsonb,
    source_critique TEXT,
    confidence DOUBLE PRECISION CHECK (
        confidence IS NULL OR (confidence >= 0.0 AND confidence <= 1.0)
    ),
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_textual_variants_passage_id
    ON textual_variants(passage_id);

CREATE INDEX IF NOT EXISTS idx_textual_variants_kg_node_id
    ON textual_variants(kg_node_id);

CREATE INDEX IF NOT EXISTS idx_textual_variants_alternatives
    ON textual_variants USING GIN (lections_alternatives);

COMMENT ON COLUMN passages.passage_role IS
    'original, translation, or paraphrase; mirrors kg_nodes.metadata.passage_role.';

COMMENT ON TABLE textual_variants IS
    'Critical-apparatus records linked to passage KG nodes via variant_of/has_variant.';
