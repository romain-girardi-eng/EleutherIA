# G1 — The Thesis Engine: Synthesis

Read-only synthesis over the KG snapshot (`data/kg/nodes.jsonl` + `data/kg/edges.jsonl`).
Generators: `scripts/goals/g1_emergence.py`, `g1_transmission.py`, `g1_research_leads.py`.
Sub-artifacts: `emergence*.json` + `emergence.md`, `transmission_paths.json` + `transmission.md`,
`research_leads.json` + `research_leads.md`, `autexousion_merge_proposal.jsonl` (staged, NOT applied).

Every data point below is anchored by a `passage_id` or an edge/argument node id in the
KG. Modern interpretive labels (libertarian / compatibilism / Dihle's "invention of the
will") are **attributed** to their proponents, never asserted as historical fact.

---

## 1. The αὐτεξούσιον emergence curve (thesis figure)

**Canonical node:** `concept_autexousion_christian_freedom_u1v2w3x4` (computed over the
*merged* concept — 1 canonical + 6 staged aliases, passed as `--merge-map`; the merge is
**not** applied to the KG). 115 attestations · 100 distinct neighbors · 8 periods.

Attestation = a neighbor reached via `discusses | employs | advanced_in | defines |
evidenced_by | grounded_in`. "Passages" = the text-grounded subset (the publishable line).
Within a period, earliest passage is tie-broken by passage date → author date → period.

| Period | Attest. | Passages | Earliest grounded attestation | Source text | Year est. |
|---|---:|---:|---|---|---|
| Classical Greek | 1 | 0 | — concept-level only | — | — |
| Hellenistic | 2 | 0 | — concept-level only | — | — |
| Roman Imperial | 24 | 12 | `passage_epict_104` | Epictetus, *Disc.* I.1 (prohairesis unhinderable) | author: Epictetus |
| Late Antiquity | 3 | 2 | `passage_plotinus_enn_4_4_30` | Plotinus, *Enn.* IV.4.30 | c. 204 |
| **Patristic** | **51** | **38** | `passage_justin_1apol_43` | Justin, *1 Apol.* 43 (antifatalist) | c. 100–114 |
| Medieval | 1 | 0 | — concept-level only | — | — |
| Modern | 17 | 0 | — reception scholarship | — | — |
| Contemporary | 16 | 0 | — reception scholarship | — | — |

**Reading.** Grounded text-attestation of αὐτεξούσιον *begins* in the **Roman Imperial**
period (pagan: Alexander of Aphrodisias' Peripatetic sense + the Epictetan prohairesis
vocabulary that feeds it), then *crystallises* in the **Patristic** period, which carries
**38 of the 50 grounded passages** — the database signature of the term's distinctively
Christian career (Justin → Origen → Cappadocians). Earliest grounded passage overall:
`passage_justin_1apol_43` (Justin Martyr, *1 Apology* 43, c. 100–114 CE).

The Modern/Contemporary bars are pure **reception** (Bobzien, Frede, Kane, Dihle's
"invention of the will" thesis) — attributed in the node descriptions, never read off the
curve as historical fact.

**Comparative anchor (5-concept timeline).** The two Aristotelian terms anchor earliest in
Classical Greek (`passage_arist_en_3_2`, *EN* III.2, c. 384 BCE) — `to eph' hēmin` (494
attest.) and `prohairesis` (323), both Epictetus-dominated at their Roman-Imperial peak.
`heimarmenê` (176) and `voluntas` (279) first get text-grounded in the Roman Republican
period via Cicero (`passage_cic_fat_1`, `passage_cic_fat_11`); `voluntas` peaks in Late
Antiquity with Augustine (`passage_aug_civ_12_1_2`) — the corpus locus of Dihle's
attributed "invention of the will". **αὐτεξούσιον is the latest-emerging and most
Christian-weighted of the five** — the empirical backbone of the dissertation's claim.

---

## 2. Carneades → Boethius transmission path (per-hop licensing)

Built from a directed person-person influence graph (`influences / teaches / precedes /
student_of / responds_to / influenced_by`, inverses normalised forward). Each hop is
anchored by a licensing passage via a 5-tier honesty model (shared grounded argument citing
a primary passage > argument citing the source's own text > `parallel_to` > scholarly
reception > none).

**The strict influence graph has NO path** — Boethius has *zero* incoming person-person
edges (a genuine structural gap, not a bug; his only person edges are two outgoing
`influences` → Plato/Aristotle). The path below is over the **augmented backbone**
(shared-grounded-argument + `parallel_to`, oriented forward by floruit/period), length 3:

1. **Carneades → Alexander of Aphrodisias** (`influences`) — **primary-text anchored**.
   Licence: `argument_frede_2011_alexander_libertarian_dead_end` (discusses both), grounded
   on **`passage_alex_fat_11`** (Alexander, *De Fato* 11; also fat. 14/15/20).
2. **Alexander → Augustine** (`shared_argument`) — **scholarly-reception only**, no primary
   passage. Licence: `scholarly_argument_gill_later_ancient_reception_of_sto_3`.
3. **Augustine → Boethius** (`shared_argument`) — **scholarly-reception only**, no primary
   passage. Licence: `scholarly_argument_brouwer_influence_on_late_antiquity_an_4`.

**Honest verdict:** only hop 1 is primary-text anchored; hops 2–3 rest on modern-reception
nodes. This *is* the finding — a real wiring gap: **no primary `parallel_to`/citation links
Augustine ↔ Boethius (or Alexander ↔ Augustine) in the KG.** This is the single
highest-value transmission lead (the Latin late-antique chain).

The other three canonical paths resolve in the **strict** graph and are better grounded:
- **Carneades → Origen** (1 hop) — licensed by **`passage_cic_fat_23`** (Cicero, *De Fato*
  23) via `argument_cafma_carneades_m3n4o5p6` (authored_by Carneades, extends Origen).
- **Chrysippus → Augustine** (2 hops) — Chrysippus→Origen via `passage_cic_fat_23`,
  Origen→Augustine via a Frede reception node.
- **Alexander → Origen** (1 hop) — scholarly-reception only.

**Top transmission brokers (Brandes betweenness):** 1. Origen **385.8** · 2. Chrysippus
220.8 · 3. Carneades 125.8 · 4. Aristotle 106.3 · 5. Augustine 91.0 · 6. Irenaeus 89.8 ·
7. Epictetus 87.0 · 8. Plotinus 81.7 · 9. Bardaisan 79.0 · 10. Eusebius 73.6. **Origen is by
far the dominant broker** — direct quantitative support for the thesis's claim about his
role transmitting Hellenistic free-will argumentation into the Christian tradition.

---

## 3. Top research leads for the dissertation

From `research_leads.md` (43 grounding gaps + 104 unmodeled debates + 5 transmission gaps).
The five worth pursuing first:

1. **GG-1 — `argument_epictetus_prohairesis_argument_aa13b932`** [Roman Imperial]. Connects
   τὸ ἐφ᾽ ἡμῖν + εἱμαρμένη + προαίρεσις (concept-degree 3, total 9) but has **zero corpus
   passage**. This is the single most-connected ungrounded argument and sits at the center of
   the thesis. *Next step:* ingest *Discourses* I.1, II.23, IV.1 (TLG tlg0557.tlg001).

2. **TG-5 — `concept_autexousion_christian` Patristic gap** (directly feeds Figure 1).
   Attested Roman Imperial + Late Antiquity but **Patristic missing**, yet Justin *2 Apol.*
   6.5, Irenaeus *Adv. Haer.* IV.37, Clement *Strom.* II.4 all use αὐτεξούσιον. Wire
   `argument_irenaeuss_antignostic_argument_for_free_will_f54fe920` + the Justin autexousion
   argument via `employs`. High-priority: it closes a visible hole in the thesis curve.

3. **Latin late-antique transmission chain (from §2)** — the Augustine↔Boethius and
   Alexander↔Augustine hops have *no* primary `parallel_to`/citation, forcing the
   Carneades→Boethius path onto scholarly-reception nodes. Adding primary-text links here
   converts the flagship transmission claim from secondary- to primary-grounded.

4. **GG-3/GG-5 — Maximus the Confessor** [Late Antiquity]. `argument_maximus_natural_vs_gnomic_will`
   (deg 3/7) and `argument_maximus_two_wills` (deg 2/11) share loci (*Disp. cum Pyrrho* PG 91,
   287–354; *Opusc.* 1, 3) but Maximus is **absent from the corpus**. *Next step:* check local
   DOCTORAT for SC Maximus before TLG tlg2892.tlg007 — one ingestion grounds two arguments.

5. **UD-2 — `argument_agent_causation_two_way_powers_alexander_q8r9s0t1` ↔
   `argument_deliberate_choice_analysis_aristotle_h8i9j0k1`**. Share τὸ ἐφ᾽ ἡμῖν +
   prohairesis; Alexander's two-way-powers theory is explicitly derived from Aristotle's
   prohairesis analysis but the edge is missing. Add `extends` — encodes the
   Aristotle→Alexander bridge the curve in §1 depends on.

(Runners-up: GG-2 Aristotelian practical syllogism; GG-4 Qumran 1QS predestination — manual
add from García Martínez 1994, not on TLG/Scaife; TG-1 ἐνδεχόμενον three-period gap.)

---

## 4. Staged cleanups to apply (with review status)

### 4a. Autexousion dedup — `autexousion_merge_proposal.jsonl` (staged, NOT applied)
Canonical `concept_autexousion_christian_freedom_u1v2w3x4` (richest: full etymology,
Justin→Origen→Cappadocian evolution, attributed reception). 6 proposed merges, 61 edges to
re-point, each verified by reading its description:

| Alias | Edges | Action | Status |
|---|---:|---|---|
| `concept_autexousion_christian` | 40 | merge (true duplicate, generic) | **APPLY** |
| `concept_eleutheron_kai_autexousion` | 4 | `has_variant` (formula, Theophilus *Autol.* II.27 — earliest coinage) | **APPLY as variant** |
| `concept_autexousion_methodian_doctrine_141258ec` | 2 | `has_variant` (Methodian ousia-not-accident) | **APPLY as variant** |
| `concept_autexousion_pe_vi_6_eusebius` | 2 | `has_variant` (Carneadean "immediate evidence", PE VI.6.21) | **APPLY as variant** |
| `concept_autexousion_alex` | 10 | `has_variant` — **pagan Peripatetic** (Alexander, *De Fato* 207) | **HOLD — human review** (genuine Aristotle→Christian bridge; may keep separate) |
| `concept_to_eph_hemin_basil` | 3 | `has_variant` — dual-membership (Basil fuses eph'-hēmin = autexousion) | **HOLD — human review** (also belongs under eph'-hēmin) |

Apply order: the 4 "APPLY" rows first (44 edges, low-risk); the 2 flagged rows only after
Romain confirms — they encode real conceptual distinctions, not duplicates. **Do not bulk
re-point; verify each edge individually** (per the no-auto-fix rule).

### 4b. Highest-value grounding fills (per `research_leads.md`)
1. **GG-1** ingest Epictetus *Disc.* I.1 / II.23 / IV.1 → ground
   `argument_epictetus_prohairesis_argument_aa13b932` (3 concept edges become text-anchored).
2. **TG-5** wire Justin/Irenaeus/Clement autexousion passages → `concept_autexousion_christian`
   via `employs` (closes the Patristic hole that §1 reports as a within-period overlap).
3. **UD-2** add `extends` (Alexander two-way-powers → Aristotle prohairesis analysis).

All grounding fills require the actual passages to be ingested from the **critical edition**
(local DOCTORAT first, then TLG/Scaife) — never fabricated.

---

## 5. Data-quality caveats (honest)

1. **Period is the chronological axis, not dates.** Only **64 of ~17k passages** carry an
   explicit year; within-period ordering falls back to author dates (**41 persons dated**)
   then period midpoints — deterministic but coarse.
2. **Earliest-formula gap (autexousion).** The truly earliest coinage (Theophilus,
   ἐλεύθερον καὶ αὐτεξούσιον, late 2nd c.) lives on the formula alias node; its passages
   don't transit into the merged set, so the curve reports **Justin (c. 100)** as earliest
   passage. Formula provenance preserved in the proposal's `has_variant`.
3. **"Patristic" vs "Roman Imperial" overlap in real time** — duplicate concept nodes split
   across both labels (e.g. `concept_autexousion_christian` tagged Roman Imperial). The curve
   preserves both buckets as the KG labels them; TG-5 is the fix.
4. **Sparse influence graph.** Only **160 directed person-person edges across 453 persons**;
   **324 persons isolated** (101 ancient/non-scholar priority + 223 modern scholars). This is
   why 2 of the 4 canonical paths need the augmented backbone or lean on reception nodes. The
   reported counts differ from the task's stated "177 isolated / 255-component" figures — those
   reflect a different snapshot/person-set; the script reports actually-computed counts with
   full provenance.
5. **Reception ≠ evidence.** Modern/Contemporary attestations are scholar/argument/debate
   nodes; libertarian / compatibilism / "invention of the will" stay attributed
   (Bobzien / Frede / Dihle), never asserted.
6. **`heimarmenê` "Cross-period"/"Unknown" buckets** (18 attest.) and `to eph' hēmin`
   "Unknown" (3) are real KG `period` metadata gaps — surfaced, not dropped.
7. **`evidenced_by` confidence varies.** Many autexousion links came from a
   `terminology_scan` (conf. 0.9) or `heuristic` doxographical method; per-edge `metadata`
   preserved in each JSON point's `edge_meta`.
