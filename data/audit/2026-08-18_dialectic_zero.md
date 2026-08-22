# R16 dialectical-debt zeroing — 2026-08-18

## Result

This additive checkpoint audits the complete current population of **518**
edges in Scholar-RAG's rendered fault-line relation set that lack
`metadata.attested_by`.

The repair was applied and reaches **zero unattested fault-line edges**:

| Measure | Before | Projected |
|---|---:|---:|
| KG nodes | 20,271 | 20,271 |
| KG edges | 50,169 | 49,840 |
| Unattested rendered fault lines | 518 | **0** |
| Existing edges supplied with precise attestations | 0 | 189 |
| Unsupported asserted edges removed | 0 | 329 |

No node, corpus row, runtime module, ontology, or shared gate is changed by the
plan. The only writable target of the companion applier is
`data/kg/edges.jsonl`.

Application created
`data/kg/edges.jsonl.bak-dialectic-zero-2026-08-18`; a second `--write` was a
byte-identical no-op. CI now calls `check_ingestion_rules.py --strict-r16`, so
any future unattested rendered fault-line edge fails independently of other
legacy ingestion-rule findings.

## Relation-by-relation verdicts

| Relation | Unattested before | Retain + attest | Delete | Total relation edges after |
|---|---:|---:|---:|---:|
| `agrees_with` | 5 | 4 | 1 | 22 |
| `contrasts_with` | 5 | 0 | 5 | 3 |
| `critiques` | 263 | 98 | 165 | 122 |
| `opposes` | 5 | 2 | 3 | 21 |
| `responds_to` | 59 | 11 | 48 | 18 |
| `supports` | 181 | 74 | 107 | 74 |
| **Total** | **518** | **189** | **329** | **260** |

There are no current unattested `refutes` edges, so that relation requires no
operation.

## Evidence buckets

The retention policy is intentionally narrower than “the endpoints look
related.” It accepts only existing, relation-specific evidence.

| Retention bucket | Edges | Rule |
|---|---:|---|
| Existing edge page/locus | 44 | An existing relation note/evidence field names the relation and a page, section, chapter, note, CTS URN, or classical locus. |
| Verified endpoint locus | 112 | A citation-verified argument/work/synthesis source gives precise pages/loci, and the target is the concept, school, debate, or primary argument instantiated by that source. |
| Primary passage locus | 29 | The source passage already carries a canonical reference or CTS URN that directly grounds the relation. |
| Explicit whole-work counter-locus | 4 | The work itself names its opponent (`Contra Celsum`, Philoponus *contra Proclum* / *contra Aristotelem*, or Bobzien's full refutation of Huby), and existing endpoint/edge provenance identifies the edition or publication range. |
| **Total retained** | **189** | |

Attestations are copied from those existing fields. Dates alone, confidence
values, weights, generic bibliographies, publication years, article existence,
and inferred thematic agreement never qualify.

## Deletion buckets

| Deletion bucket | Edges | Rationale |
|---|---:|---|
| No relation-specific attestation | 320 | Existing provenance may verify one or both nodes, but it does not verify the directed `source —relation→ target` claim. |
| Comparison miscast as response | 7 | Augustine passages share a foreknowledge topic with an Alexander argument; they do not historically “respond to” Alexander. Canonical Augustine loci therefore cannot launder that relation. |
| Prior audit found no evidence | 2 | The 2026-08-17 audit explicitly recorded that the Brennan→Origen/Bobzien and Sorabji→Frede critiques could not be verified. Pages cited in those negative notes are not attestations. |
| **Total deleted** | **329** | |

The plan deletes rather than silently retyping unsupported edges. A replacement
relation would itself be a new scholarly claim and would need its own evidence.

## Discoverability impact

The 329 deletions remove edges, not endpoints.

- For 318 deletion decisions, both endpoints retain at least one existing
  non-fault-line edge.
- Fourteen deleted endpoint pairs already have a direct non-fault-line relation
  between the same pair.
- Eleven deletions involve at least one endpoint without another non-fault-line
  link. Three historical nodes become isolated: `council_carthage_418`,
  `person_jacobus_arminius_1i5d6e24`, and
  `person_vincent_lerins_d450`. They are left visible as node-quality backlog;
  an unattested dialectical claim is not retained merely to hide an orphan.

## Exactness and reproducibility

The frozen baseline SHA-256 is:

`0721cef735a6858c92801d3a821a3f2933e308a80bc56c14ee0e73a2d0180b3d`

It hashes every one of the 518 edge IDs, triples, and metadata objects. The
derived action-plan SHA-256 is:

`6c0af062192dbd8b61d8a0d4976207367c5a0beb44b1626d1ab3d638cb31988d`

The data module exposes every verdict, including its edge ID, triple, evidence
bucket, and rationale:

```bash
python3 scripts/data_2026_08_18_dialectic_zero.py --details
```

The applier is a no-write dry run by default:

```bash
python3 scripts/apply_2026_08_18_dialectic_zero.py
```

The reviewed write is explicit:

```bash
python3 scripts/apply_2026_08_18_dialectic_zero.py --write
```

Before any write, every edit rechecks its exact edge ID, source, relation,
target, and metadata hash. A write creates
`data/kg/edges.jsonl.bak-dialectic-zero-2026-08-18`, writes through an atomic
temporary file, and refuses to overwrite an existing backup. Re-running after
a completed application is a no-op once the shared R16 contract reports zero.

## Gate result

The dry-run executes the repository's actual R1–R18 checker against the current
and projected in-memory snapshots:

```text
R1-R18 full-graph findings: 3149 -> 2630; no non-R16 regression
R16 debt: 518 -> 0
```

The 2,630 remaining full-graph findings are pre-existing non-R16 findings
(principally duplicate-identity debt exposed when the whole historical graph is
passed through a gate designed primarily for new ingestions). This checkpoint
does not claim to repair them. Its strict invariant is that no non-R16 finding
is introduced, all counts match, all endpoints resolve, and R16 reaches zero.

## Files

- `scripts/data_2026_08_18_dialectic_zero.py` — frozen population, evidence
  policy, per-edge plan, hashes, and detailed audit output.
- `scripts/apply_2026_08_18_dialectic_zero.py` — dry-run-default, idempotent,
  preconditioned, backed-up edges-only applier.
- `data/audit/2026-08-18_dialectic_zero.md` — this rationale and count ledger.
