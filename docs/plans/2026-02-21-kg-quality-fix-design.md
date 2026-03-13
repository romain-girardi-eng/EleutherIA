# KG Quality Fix Design

**Date:** 2026-02-21
**Scope:** 4,247 nodes / 10,681 edges / 2,464 passage citations on Supabase production

## Problem

The KG audit revealed systemic quality issues:
- Complete ontology/DB case mismatch (PascalCase ontology vs lowercase DB)
- 7 undocumented node types, ~20 undocumented edge types
- Mixed-case edge relations (UPPERCASE + lowercase coexist)
- Period labels inconsistent with ontology definitions
- Near-duplicate concept nodes (to eph' hemin, fate variants)
- 15 groups of duplicate edges
- Schema drift between schema.sql and actual Supabase
- 10 orphan passage citations
- Thin nodes with 100% empty metadata

## Decisions

1. **Lowercase convention** for all node types — update ontology to match DB/frontend/backend
2. **Lowercase convention** for all edge relations — normalize DB UPPERCASE to lowercase
3. **Merge obvious duplicates** only — keep school-specific variants separate

## Phase 1: Ontology Alignment (code-only)

Update `knowledge graph/ontology/node_types.json`:
- Lowercase all 15 existing types (Person → person, Concept → concept, etc.)
- Add 7 new types: publication, quote, synthesis, controversy, conceptual_evolution, group, argument_framework

Update `knowledge graph/ontology/edge_types.json`:
- Add ~20 new edge types: has_section, has_chapter, evidenced_by, created_by, grounded_in, source_for, critiques, supports, extends, employs, exemplifies, contributes_to, belongs_to_corpus, participated_in, presupposes, member_of, developed_by, represents, specializes_in, parallel_to, student_of

## Phase 2: DB Edge Normalization (SQL on Supabase)

Normalize all UPPERCASE relations to lowercase:
- DISCUSSES → discusses
- AUTHORED_BY → authored_by
- PART_OF → part_of
- CREATED_BY → created_by
- GROUNDED_IN → grounded_in
- SOURCE_FOR → source_for
- CRITIQUES → critiques
- SUPPORTS → supports
- EXTENDS → extends
- INTERPRETS → interprets
- INFLUENCED → influenced
- EMPLOYS → employs
- CONTAINS → contains
- EXEMPLIFIES → exemplifies
- CONTRIBUTES_TO → contributes_to
- RESPONDS_TO → responds_to
- PARTICIPATED_IN → participated_in
- PRESUPPOSES → presupposes
- MEMBER_OF → member_of
- DEVELOPED_BY → developed_by
- REPRESENTS → represents
- SPECIALIZES_IN → specializes_in
- RELATES_TO → relates_to
- DEFINES → defines
- CONTEMPORARY_OF → contemporary_of
- PARALLEL_TO → parallel_to
- INFLUENCED_BY → influenced_by
- CONTRASTS_WITH → contrasts_with
- STUDENT_OF → student_of
- FOLLOWS → follows
- PRECEDES → precedes

Already lowercase (no change): has_section, has_chapter, evidenced_by, belongs_to_corpus, wrote

## Phase 3: Period Label Standardization

Rename in kg_nodes:
- Imperial → Roman Imperial (2,869 nodes)
- Classical → Classical Greek (58 nodes)
- Late Republican → Roman Republican (52 nodes)

Add to PERIOD_METADATA in analytics.py:
- Contemporary, Early Modern, Medieval, Second Temple Judaism, Rabbinic, Modern

Update frontend AdvancedSearchPage.tsx dropdown.

## Phase 4: Duplicate Merging

### Exact duplicate
- Merge passage `sc20_theophilus_ad_autolycum_ii_liv_2_...chap_35_36` INTO `...chap_35`

### Concept near-duplicate
- Merge `concept_to_eph_hemin_stoic_a1b2c3d4` (196 edges) INTO `concept_eph_hemin_in_our_power_aristotle_d4e5f6g7` (967 edges)
  - Reassign all edges from stoic variant to canonical node
  - Add stoic label to alternative_names
  - Delete stoic variant node

### Edge deduplication
- Remove 15 groups of duplicate (source_id, target_id, relation) triples, keeping the oldest edge_id

## Phase 5: Schema Sync

Update `database/schema/schema.sql` to match Supabase:
- Remove `school` and `role` columns from kg_nodes
- Remove `description` and `weight` columns from kg_edges
- Add `alternative_names JSONB` and `updated_at TIMESTAMPTZ` to kg_nodes

## Phase 6: Orphan Cleanup

Fix 10 orphan passage_citations pointing to non-existent KG nodes:
- `person_justin_martyr_100_165ce_t0u1v2w3` (9 citations) — find correct node_id
- `concept_autexousion_methodian_g78i9j0k` (1 citation) — find correct node_id

## Phase 7: Thin Node Enrichment

Add minimal metadata to nodes with 100% empty metadata:
- controversy (5 nodes)
- conceptual_evolution (3 nodes)
- group (3 nodes)
- event (2 nodes)
- argument_framework (1 node)

Extract metadata from descriptions: period, key_concepts, related nodes.
