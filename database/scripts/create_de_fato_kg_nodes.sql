-- ============================================
-- Phase 4: Create KG Nodes for De Fato Chapters
-- ============================================
-- Prerequisites:
--   1. Phase 3 reimport completed (39 clean passages exist,
--      old KG nodes/edges already deleted by reimport script)
--
-- Node IDs confirmed by Phase 1 audit:
--   Work:   work_de_fato_alexander_c200ce_o6p7q8r9
--   Person: person_alexander_aphrodisias_fl200ce_n5o6p7q8
-- ============================================

-- ============================================
-- Step 1: Insert 39 passage KG nodes
-- ============================================

INSERT INTO free_will.kg_nodes (node_id, label, type, description, period, metadata)
SELECT
    'passage_alex_fat_' || p.chapter AS node_id,
    'Alexander of Aphrodisias, De Fato, chap. ' || p.chapter AS label,
    'passage' AS type,
    p.text_content AS description,
    'Roman Imperial' AS period,
    jsonb_build_object(
        'edition', 'Bruns 1892 (1st1K-grc1)',
        'author', 'Alexander of Aphrodisias',
        'canonical_ref', p.canonical_ref,
        'db_passage_id', p.passage_id::text,
        'word_count', p.word_count,
        'char_length', p.char_length,
        'work_title', 'De Fato',
        'cts_urn', p.cts_urn,
        'language', 'grc',
        'school', 'Peripatetic',
        'auto_generated', true
    ) AS metadata
FROM free_will.passages p
JOIN free_will.ancient_works w ON p.work_id = w.work_id
WHERE w.canonical_id = 'tlg0732.tlg014'
ORDER BY p.sequence_number
ON CONFLICT (node_id) DO NOTHING;

-- Verify: should return 39
SELECT COUNT(*) AS new_passage_nodes
FROM free_will.kg_nodes
WHERE node_id LIKE 'passage_alex_fat_%';


-- ============================================
-- Step 2: Create PART_OF edges (passage → work)
-- ============================================

INSERT INTO free_will.kg_edges (source_id, target_id, relation, metadata)
SELECT
    n.node_id,
    'work_de_fato_alexander_c200ce_o6p7q8r9',
    'part_of',
    '{"auto_generated": true}'::jsonb
FROM free_will.kg_nodes n
WHERE n.node_id LIKE 'passage_alex_fat_%'
  AND NOT EXISTS (
      SELECT 1 FROM free_will.kg_edges e
      WHERE e.source_id = n.node_id
        AND e.relation = 'part_of'
        AND e.target_id = 'work_de_fato_alexander_c200ce_o6p7q8r9'
  );

-- Verify: should return 39
SELECT COUNT(*) AS part_of_edges
FROM free_will.kg_edges
WHERE source_id LIKE 'passage_alex_fat_%'
  AND relation = 'part_of';


-- ============================================
-- Step 3: Create AUTHORED_BY edges (passage → person)
-- ============================================

INSERT INTO free_will.kg_edges (source_id, target_id, relation, metadata)
SELECT
    n.node_id,
    'person_alexander_aphrodisias_fl200ce_n5o6p7q8',
    'authored_by',
    '{"auto_generated": true}'::jsonb
FROM free_will.kg_nodes n
WHERE n.node_id LIKE 'passage_alex_fat_%'
  AND NOT EXISTS (
      SELECT 1 FROM free_will.kg_edges e
      WHERE e.source_id = n.node_id
        AND e.relation = 'authored_by'
        AND e.target_id = 'person_alexander_aphrodisias_fl200ce_n5o6p7q8'
  );

-- Verify: should return 39
SELECT COUNT(*) AS authored_by_edges
FROM free_will.kg_edges
WHERE source_id LIKE 'passage_alex_fat_%'
  AND relation = 'authored_by';


-- ============================================
-- Step 4: Create DISCUSSES edges (passage → core concepts)
-- ============================================
-- De Fato discusses these concepts throughout: heimarmene, eph'hemin, endechomenon

INSERT INTO free_will.kg_edges (source_id, target_id, relation, metadata)
SELECT
    n.node_id,
    'concept_heimarmene_fate_stoics_j0k1l2m3',
    'discusses',
    '{"auto_generated": true}'::jsonb
FROM free_will.kg_nodes n
WHERE n.node_id LIKE 'passage_alex_fat_%'
  AND NOT EXISTS (
      SELECT 1 FROM free_will.kg_edges e
      WHERE e.source_id = n.node_id
        AND e.relation = 'discusses'
        AND e.target_id = 'concept_heimarmene_fate_stoics_j0k1l2m3'
  );

INSERT INTO free_will.kg_edges (source_id, target_id, relation, metadata)
SELECT
    n.node_id,
    'concept_eph_hemin_in_our_power_aristotle_d4e5f6g7',
    'discusses',
    '{"auto_generated": true}'::jsonb
FROM free_will.kg_nodes n
WHERE n.node_id LIKE 'passage_alex_fat_%'
  AND NOT EXISTS (
      SELECT 1 FROM free_will.kg_edges e
      WHERE e.source_id = n.node_id
        AND e.relation = 'discusses'
        AND e.target_id = 'concept_eph_hemin_in_our_power_aristotle_d4e5f6g7'
  );

INSERT INTO free_will.kg_edges (source_id, target_id, relation, metadata)
SELECT
    n.node_id,
    'concept_endechomenon_contingent_aristotle_e5f6g7h8',
    'discusses',
    '{"auto_generated": true}'::jsonb
FROM free_will.kg_nodes n
WHERE n.node_id LIKE 'passage_alex_fat_%'
  AND NOT EXISTS (
      SELECT 1 FROM free_will.kg_edges e
      WHERE e.source_id = n.node_id
        AND e.relation = 'discusses'
        AND e.target_id = 'concept_endechomenon_contingent_aristotle_e5f6g7h8'
  );


-- ============================================
-- Step 5: Create passage_citations (link passages ↔ KG nodes)
-- ============================================

INSERT INTO free_will.passage_citations (passage_id, kg_node_id, citation_type, confidence)
SELECT
    p.passage_id,
    'passage_alex_fat_' || p.chapter,
    'primary_source',
    1.0
FROM free_will.passages p
JOIN free_will.ancient_works w ON p.work_id = w.work_id
WHERE w.canonical_id = 'tlg0732.tlg014'
  AND NOT EXISTS (
      SELECT 1 FROM free_will.passage_citations pc
      WHERE pc.passage_id = p.passage_id
        AND pc.kg_node_id = 'passage_alex_fat_' || p.chapter
  );

-- Verify: should return 39
SELECT COUNT(*) AS passage_citations
FROM free_will.passage_citations pc
WHERE pc.kg_node_id LIKE 'passage_alex_fat_%';


-- ============================================
-- Final Verification
-- ============================================

-- 1. No messy passages remain
SELECT COUNT(*) AS messy_passages_remaining
FROM free_will.passages p
JOIN free_will.ancient_works w ON p.work_id = w.work_id
WHERE w.canonical_id IN ('tlg0732.tlg003', 'tlg0732.tlg014')
  AND (p.text_content ~ '[a-zA-Z]{15,}' OR LENGTH(p.text_content) = 0);

-- 2. All new passages contain Greek
SELECT COUNT(*) AS passages_without_greek
FROM free_will.passages p
JOIN free_will.ancient_works w ON p.work_id = w.work_id
WHERE w.canonical_id = 'tlg0732.tlg014'
  AND p.text_content !~ '[\u0370-\u1FFF]';

-- 3. Exactly 39 clean passages
SELECT COUNT(*) AS total_de_fato_passages
FROM free_will.passages p
JOIN free_will.ancient_works w ON p.work_id = w.work_id
WHERE w.canonical_id = 'tlg0732.tlg014';

-- 4. KG nodes fully linked (no orphan passage nodes)
SELECT COUNT(*) AS unlinked_passage_nodes
FROM free_will.kg_nodes n
WHERE n.node_id LIKE 'passage_alex_fat_%'
  AND NOT EXISTS (
      SELECT 1 FROM free_will.kg_edges e
      WHERE e.source_id = n.node_id AND e.relation = 'part_of'
  );

-- 5. canonical_id corrected
SELECT canonical_id
FROM free_will.ancient_works
WHERE author ILIKE '%alexander%' AND title ILIKE '%fato%';
