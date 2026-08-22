# Non-exact corpus relations: citation typing and runtime enforcement

Date: 2026-08-18  
Status: applied and verified

The parity-zero repair correctly removed `db_passage_id` from 292 false or
stale twins. Of those, 289 retained a useful relationship to a current corpus
passage through `related_corpus_passage_id`. This follow-up closes the runtime
semantic gap left by the historical citation type.

## Data repair

Exactly 289 one-to-one citation rows were retyped:

```text
snapshot_passage_node -> related_passage_non_exact
```

No row was added, deleted, reordered, or otherwise changed. KG nodes and
corpus passages were read-only. Corpus invariant counts remain zero. The
deterministic final citation SHA-256 is
`d3d74079b280c2038495e9e396dee8339331b9b764432c1669ef1e132e3d1293`.

The applier is dry-run-first, exact-cohort/hash preconditioned, backed up, and
byte-idempotent:

`scripts/apply_2026_08_18_related_citation_types.py`

## Runtime enforcement

- exact passage detail, section/context anchors, and translation lookup accept
  only `snapshot_passage_node` links;
- the frontend batch-citation endpoint also filters exact snapshots and emits
  no KG description text for a `related_not_exact_twin` fallback;
- GraphRAG retains `related_passage_non_exact` links for discovery, but central
  citability marks them `discoverable_only`, strips source text, and emits an
  explicit non-exact-twin notice;
- direct corpus UUID retrieval remains citable and unchanged;
- SQL seed discovery keeps the KG node anchor and citation type, rather than
  laundering the relationship through an untyped raw passage UUID.

This preserves useful navigation without presenting cross-language,
coarse/fine, conflicting-edition, or wrong-work relationships as exact
textual identity.

Focused verification passed for the citation applier, backend passage/section
routes, database translation joins, GraphRAG citability, passage retrieval,
and SQL seed discovery.
