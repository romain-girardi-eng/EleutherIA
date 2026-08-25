# Public glossary factual repair and publication review

Date: 2026-08-24  
Scope: `frontend/src/content/glossary.json`, its public explanatory copy, and
fail-closed SEO publication behavior. No KG, corpus, bibliography, or source
claim was changed by this repair.

## Outcome

- Previous glossary SHA-256:
  `4bff80bc4173c44f3ef5f2cf2fad4c1fafc44d9a067891358614c0a1ce100dd6`.
- Reviewed glossary SHA-256:
  `dd130950f4ea784607f98025578364d309fc4d8bac2e4017f7c244144ca98de7`.
- 26 definitions were replaced by the source-bounded paraphrases proposed in
  the three claim audits. `Hekousion`, the one definition previously approved,
  remains byte-for-byte and semantically unchanged (entry-block SHA prefix
  `5bfa89fc`).
- All ten definitions previously classified `BLOCK` now pass their corrected
  claim contracts. The remaining `REVISE` definitions were also replaced.
- The false ancient technical equivalent `ἀσύμβατον` was removed. Modern
  incompatibilism is explicitly labelled as a modern comparison category.
- Periods and labels were repaired where the previous value created a false
  chronology, including Stoic fate, `autexousion`, `liberum arbitrium`, and
  `voluntas`.
- The 27 IDs, 58 related IDs, and canonical `/visualizer/{id}` routes remain
  active and internally valid.

## Evidence base

The write was bounded by three read-only audits:

- A–I: `docs/academic/2026-08-24-glossary-entities-a-i-audit.md`, SHA prefix
  `306eb6fc`;
- J–R: `docs/academic/2026-08-24-glossary-entities-j-r-audit.md`, SHA prefix
  `fb71fdc3`;
- S–Z: `docs/academic/2026-08-24-glossary-entities-s-z-audit.md`, SHA prefix
  `a419ecf6`.

Those reports preserve the ancient loci, secondary page maps, local artifact
hashes, manifestation cautions, and exact replacement prose. Definitions do not
inherit the factual status of legacy KG descriptions.

## Independent review

Two independent post-write reviews were run against the reviewed hash.

1. A full entry-by-entry factual review returned **PASS 27/27**. It initially
   rejected the unsupported `Hellenistic` lower bound for `autexousion`; after
   correction to `Roman Imperial to Patristic`, it found no remaining blocker.
2. A publication/SEO review verified valid JSON, 27 active entity IDs, all 58
   related IDs, route identity, absence of the false Greek equivalent, and
   semantic agreement with the three audit replacements.

This is sufficient for a corrected review candidate, but not for search-engine
promotion: the publication policy also requires a separately recorded
adversarial pass. `frontend/src/seo/entity-publication.json` therefore remains
unchanged with `approved_ids: []` (SHA
`82d01f6ca533f9aa3b3cf96452e18954bed3fc42fd29bc6c9706e1950d126f9f`).
All 27 candidate pages remain `noindex, follow`, without canonical, hreflang,
JSON-LD, or sitemap entries.

## Public integrity copy

The About page previously claimed that every node, edge, citation, Greek/Latin
text, and bibliographic provenance was already verified. That contradicted the
live evidence registry. The English, French, German, Italian, and Greek copy now
states that collation, provenance, and lemmatization are progressive and that
unresolved evidence remains explicit and fail-closed.

Two regression tests lock the corrected public contract:

- `frontend/src/content/glossary.test.ts`, SHA
  `efb7223b85c2b43b900baed16ae041ac1571c7891cb9baa71b5fb6efdb8819b9`;
- `frontend/src/i18n/aboutIntegrity.test.ts`, SHA
  `5f413085f8d838135617b9cbc69a694800404e1787112cd5029b75667c98ed2a`.

## Validation

- Frontend tests: **231 passed in 39 files**.
- ESLint: PASS.
- Production build: PASS, 4,160 modules.
- SEO output contract: PASS.
- Workspace split contract: PASS.
- Static output: 24 general pages + 27 review-candidate entity pages, zero
  indexable entity pages.
- Final SEO release fingerprint:
  `seo-source-sha256-2eb4a45a1dff0f37fcff7c3a5eba3bca6e44f6248b5a6baa31c56777e95e391f`.

The remaining non-blocking performance warning is the isolated Cosmograph
vendor chunk (about 410 KiB gzip); Atlas, Chronos, and Scholar mode chunks remain
separate and within the workspace split contract.
