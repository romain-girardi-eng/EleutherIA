-- ============================================
-- Phase 1: Audit Alexander De Fato Data
-- ============================================
-- Run these queries against Supabase to confirm
-- current state before cleanup.
-- ============================================

-- 1. Count De Fato passages and sample content quality
SELECT
    COUNT(*) AS total_passages,
    MIN(char_length) AS min_chars,
    MAX(char_length) AS max_chars,
    AVG(char_length)::int AS avg_chars,
    SUM(word_count) AS total_words
FROM free_will.passages p
JOIN free_will.ancient_works w ON p.work_id = w.work_id
WHERE w.author ILIKE '%alexander%' AND w.title ILIKE '%fato%';

-- 2. Sample first 5 passages (inspect for mixed content)
SELECT
    p.passage_id,
    p.canonical_ref,
    p.cts_urn,
    p.chapter,
    p.sequence_number,
    p.char_length,
    LEFT(p.text_content, 200) AS text_preview
FROM free_will.passages p
JOIN free_will.ancient_works w ON p.work_id = w.work_id
WHERE w.author ILIKE '%alexander%' AND w.title ILIKE '%fato%'
ORDER BY p.sequence_number
LIMIT 5;

-- 3. Check current canonical_id and work details
SELECT
    w.work_id,
    w.canonical_id,
    w.kg_work_id,
    w.title,
    w.author,
    w.language,
    w.period,
    w.school,
    w.cts_urn,
    w.source,
    w.total_divisions,
    w.total_words,
    w.total_chars
FROM free_will.ancient_works w
WHERE w.author ILIKE '%alexander%' AND w.title ILIKE '%fato%';

-- 4. List ALL existing KG nodes for Alexander / De Fato
SELECT
    n.node_id,
    n.label,
    n.type,
    n.period,
    LEFT(n.description, 150) AS desc_preview,
    n.metadata
FROM free_will.kg_nodes n
WHERE n.label ILIKE '%alexander%de fato%'
   OR n.node_id ILIKE '%alex%fat%'
   OR (n.metadata->>'work_title' ILIKE '%de fato%')
   OR (n.metadata->>'author' ILIKE '%alexander%' AND n.label ILIKE '%fato%');

-- 5. Find argument/quote nodes with empty or missing source_text
SELECT
    n.node_id,
    n.label,
    n.type,
    LEFT(n.description, 200) AS desc_preview,
    n.metadata->>'source_text' AS source_text
FROM free_will.kg_nodes n
WHERE n.type IN ('argument', 'quote')
  AND (n.label ILIKE '%alexander%' OR n.label ILIKE '%de fato%'
       OR n.description ILIKE '%de fato%');

-- 6. Find the Alexander person node (for AUTHORED_BY edges)
SELECT
    n.node_id,
    n.label,
    n.type,
    n.period
FROM free_will.kg_nodes n
WHERE n.label ILIKE '%alexander%aphrodis%'
   OR n.node_id ILIKE '%alexander_aphrodis%';

-- 7. Find the De Fato work node (for PART_OF edges)
SELECT
    n.node_id,
    n.label,
    n.type,
    n.metadata
FROM free_will.kg_nodes n
WHERE n.type IN ('work', 'Work')
  AND (n.label ILIKE '%de fato%' OR n.node_id ILIKE '%de_fato%');

-- 8. Check existing edges involving De Fato nodes
SELECT
    e.edge_id,
    e.source_id,
    e.target_id,
    e.relation,
    e.metadata
FROM free_will.kg_edges e
WHERE e.source_id ILIKE '%alex%fat%'
   OR e.target_id ILIKE '%alex%fat%'
   OR e.source_id IN (
       SELECT node_id FROM free_will.kg_nodes
       WHERE label ILIKE '%de fato%'
   );

-- 9. Check for passages with mixed Latin/English content (quality issue)
SELECT
    p.passage_id,
    p.canonical_ref,
    p.char_length,
    LEFT(p.text_content, 300) AS text_preview
FROM free_will.passages p
JOIN free_will.ancient_works w ON p.work_id = w.work_id
WHERE w.author ILIKE '%alexander%' AND w.title ILIKE '%fato%'
  AND p.text_content ~ '[a-zA-Z]{15,}'  -- Long Latin/English runs
ORDER BY p.sequence_number
LIMIT 10;

-- 10. Check passage_citations linked to De Fato passages
SELECT
    pc.citation_id,
    pc.passage_id,
    pc.kg_node_id,
    pc.citation_type,
    pc.confidence
FROM free_will.passage_citations pc
WHERE pc.passage_id IN (
    SELECT p.passage_id
    FROM free_will.passages p
    JOIN free_will.ancient_works w ON p.work_id = w.work_id
    WHERE w.author ILIKE '%alexander%' AND w.title ILIKE '%fato%'
);
