# G1 — Concept-emergence timelines

Read-only KG analysis. Generator: `scripts/goals/g1_emergence.py`. Snapshot:
`data/kg/nodes.jsonl` + `data/kg/edges.jsonl`. Per-concept JSON:
`data/goals/g1/emergence_<concept>.json`.

**Method.** For a concept node, collect every neighbor reached via the attestation
relations `discusses | employs | advanced_in | defines | evidenced_by |
grounded_in`. Bucket neighbors by their `period` field. For each period, the
*earliest grounded passage* is the passage-type neighbor with the lowest derivable
year (passage `metadata.date`/`source_date`/`year`, else the author's person-node
birth/floruit year, else the period itself). Every emitted point carries its
`passage_id` (or, for periods with only non-passage attestations, the neighbor node
ids). Modern labels (libertarian / compatibilism / "invention of the will") are
attributed to their proponents in the node descriptions, never asserted here.

For **autexousion** the curve is computed over the *merged* concept defined by the
staged proposal `data/goals/g1/autexousion_merge_proposal.jsonl` (1 canonical + 6
aliases), passed via `--merge-map`. The proposal is **not applied** to the KG.

---

## Figure 1 (thesis) — Emergence curve of αὐτεξούσιον ("self-determination")

**Canonical node:** `concept_autexousion_christian_freedom_u1v2w3x4`
(merging `_christian`, `_methodian_doctrine_141258ec`, `_alex`,
`eleutheron_kai_autexousion`, `_pe_vi_6_eusebius`, `to_eph_hemin_basil`).
**Totals (merged):** 115 attestations · 100 distinct neighbors · 8 periods.

### Plot spec

- **Chart type:** stepped attestation curve (x = period, ordered chronologically;
  y = number of grounded attestations), with a secondary marker layer for the
  *earliest grounded passage* of each period (annotated with its `passage_id`).
- **X axis (period, left→right):** Classical Greek · Hellenistic · Roman Imperial ·
  Late Antiquity · Patristic · Medieval · Modern · Contemporary.
- **Y axis:** `n_attestations` (full curve) over-plotted with `n_passages` (the
  text-grounded subset, the publishable line). Use `n_passages` as the solid line;
  `n_attestations` as a faint envelope.
- **Two-phase shading:** ancient *pagan* emergence (Roman Imperial: Alexander +
  Epictetus) → Christian *crystallisation* (Patristic peak). The curve's mass sits
  in **Patristic** (51 attestations / 38 passages), the empirical signature of the
  thesis claim that αὐτεξούσιον is the term in which a self-origination ("libertarian"
  — Frede 2011, attributed) reading of freedom is foregrounded in early Christianity.
- **Annotation callouts:** label the three grounded earliest-passage anchors below.

### Data — period → earliest grounded attestation (each with `passage_id`)

| Period | Attest. | Passages | Earliest grounded attestation (`passage_id`) | Source text | Year est. |
|---|---:|---:|---|---|---|
| Classical Greek | 1 | 0 | — (concept-level only, no passage) | — | — |
| Hellenistic | 2 | 0 | — (concept-level only, no passage) | — | — |
| Roman Imperial | 24 | 12 | `passage_epict_104` | Epictetus, *Discourses* I.1 (prohairesis cannot be hindered) | author: Epictetus |
| Late Antiquity | 3 | 2 | `passage_plotinus_enn_4_4_30` | Plotinus, *Enn.* IV.4.30 (self-determining principle) | 204 |
| **Patristic** | **51** | **38** | `passage_justin_1apol_43` | Justin, *1 Apology* 43 (antifatalist argument) | c. 100 |
| Medieval | 1 | 0 | — (concept-level only, no passage) | — | — |
| Modern | 17 | 0 | — (reception scholarship, no ancient passage) | — | — |
| Contemporary | 16 | 0 | — (reception scholarship, no ancient passage) | — | — |

**Reading.** Grounded text-attestation of αὐτεξούσιον begins in the **Roman Imperial**
period (pagan: Alexander of Aphrodisias' Peripatetic sense + Epictetus' prohairesis
vocabulary that feeds it), then *crystallises* in the **Patristic** period, which
carries 38 of the 50 grounded passages — the database signature of the concept's
Christian career (Justin → Origen → Cappadocians). The **earliest grounded passage
overall** is `passage_justin_1apol_43` (Justin Martyr, *1 Apology* 43, c. 100-114 CE).
The "Modern"/"Contemporary" bars are pure *reception* (scholar/argument nodes:
Bobzien, Frede, Kane, Dihle's "invention of the will" thesis — all attributed in the
underlying node descriptions, never asserted as historical fact).

**Earliest-formula caveat.** The historically earliest *coinage* of the Christian
doctrine is the formula ἐλεύθερον καὶ αὐτεξούσιον (Theophilus, *Autol.* II.27;
Irenaeus, *Dem.* 11), captured by the alias node `concept_eleutheron_kai_autexousion`.
Because that node's own grounding passages attach to the *formula* node rather than
to the canonical concept, they do not transit into the merged neighbor set; the
curve therefore reports Justin (c. 100) as the earliest *passage*, while the formula
provenance (Theophilus, late 2nd c.) is preserved in the merge proposal's
`has_variant` record. See caveats below.

---

## Cross-concept summary (for comparative timeline figure)

Earliest grounded passage per concept, by first attested period:

| Concept | Canonical node | Periods | Total attest. | First grounded period | Earliest `passage_id` |
|---|---|---:|---:|---|---|
| **to eph' hēmin** (τὸ ἐφ' ἡμῖν) | `concept_eph_hemin_in_our_power_aristotle_d4e5f6g7` | 9 | 494 | Classical Greek | `passage_arist_en_3_2` (Aristotle, *EN* III.2, c. 384 BCE) |
| **prohairesis** (προαίρεσις) | `concept_prohairesis_deliberate_choice_aristotle_c3d4e5f6` | 8 | 323 | Classical Greek | `passage_arist_en_3_2` (Aristotle, *EN* III.2, c. 384 BCE) |
| **heimarmenê** (εἱμαρμένη) | `concept_heimarmene_fate_stoics_j0k1l2m3` | 11 | 176 | Roman Republican (earliest *passage*) | `passage_cic_fat_1` (Cicero, *De Fato* 1, c. 106 BCE) |
| **autexousion** (αὐτεξούσιον) | `concept_autexousion_christian_freedom_u1v2w3x4` (merged) | 8 | 115 | Roman Imperial (earliest *passage*) | `passage_epict_104` → Patristic peak `passage_justin_1apol_43` |
| **voluntas** (will) | `concept_voluntas_y7z8a9b0` | 8 | 279 | Roman Republican | `passage_cic_fat_11` (Cicero, *De Fato* 11, c. 106 BCE); peak Late Antiquity (`passage_aug_civ_12_1_2`, Augustine) |

**Comparative narrative (grounded).** The two Aristotelian terms (`to eph' hēmin`,
`prohairesis`) anchor earliest, in **Classical Greek** (`passage_arist_en_3_2`),
both peaking in **Roman Imperial** (Epictetus-dominated: 372 and 240 grounded
passages respectively). `heimarmenê` (Stoic fate) and `voluntas` first get
text-grounded in the **Roman Republican** period via Cicero's *De Fato*; `voluntas`
then peaks in **Late Antiquity** with Augustine (222 grounded passages) — the corpus
locus of Dihle's attributed "invention of the will" claim. `autexousion` is the
latest-emerging and most Christian-weighted of the five.

---

## Data-quality caveats

1. **Period is the chronological axis, not absolute dates.** Passage nodes almost
   never carry an explicit year (only 64 of ~17k passages have any date field), so
   buckets are periods. Within a period the earliest-passage tie-break uses the
   *author's* person-node date (41 persons carry dates). Where neither exists, the
   period fallback year is used (deterministic but coarse).
2. **"Patristic" vs "Roman Imperial" overlap in real time.** Several 2nd-4th c. CE
   Christian authors are bucketed `Patristic`; some duplicate concept nodes (e.g.
   `concept_autexousion_christian`) were tagged `Roman Imperial`. The merge proposal
   notes this; the curve preserves both buckets as the KG labels them.
3. **Earliest-formula vs earliest-passage gap (autexousion).** The earliest Christian
   coinage (Theophilus' ἐλεύθερον καὶ αὐτεξούσιον, *Autol.* II.27) sits on a separate
   formula node whose passages do not transit into the merged concept; the reported
   earliest passage is therefore Justin (c. 100). The formula provenance is retained
   in the proposal's `has_variant` field.
4. **Two aliases flagged for human review before any merge is applied:**
   `concept_autexousion_alex` (a genuinely *pagan Peripatetic* sense — the
   Aristotle→Christian bridge; consider keeping separate) and
   `concept_to_eph_hemin_basil` (a dual-membership node that *identifies*
   to eph' hēmin with autexousion — also belongs under the eph'-hēmin concept).
5. **`heimarmenê` "Cross-period" / "Unknown" buckets** (1 + 17 attestations) and
   `to eph' hēmin` "Unknown" (3) are nodes with absent/non-standard `period` values —
   real KG metadata gaps, surfaced rather than silently dropped.
6. **Modern/Contemporary attestations are reception, not ancient evidence.** They are
   scholar/argument/debate nodes; their modern labels (libertarian, compatibilism,
   "invention of the will") are attributed to named scholars in the node
   descriptions and must never be read off this curve as historical assertions.
7. **`evidenced_by` confidence varies.** Many autexousion passage links were added by
   a `terminology_scan` (confidence 0.9) or `heuristic` doxographical method; the
   per-edge `metadata` (preserved in each JSON point's `edge_meta`) records this.

---

## Reproduce

```bash
python3 scripts/goals/g1_emergence.py concept_autexousion_christian_freedom_u1v2w3x4 \
  --merge-map data/goals/g1/autexousion_merge_proposal.jsonl \
  --out data/goals/g1/emergence_autexousion.json
python3 scripts/goals/g1_emergence.py concept_eph_hemin_in_our_power_aristotle_d4e5f6g7 --out data/goals/g1/emergence_to_eph_hemin.json
python3 scripts/goals/g1_emergence.py concept_prohairesis_deliberate_choice_aristotle_c3d4e5f6 --out data/goals/g1/emergence_prohairesis.json
python3 scripts/goals/g1_emergence.py concept_heimarmene_fate_stoics_j0k1l2m3 --out data/goals/g1/emergence_heimarmene.json
python3 scripts/goals/g1_emergence.py concept_voluntas_y7z8a9b0 --out data/goals/g1/emergence_voluntas.json
```
