# Enrichment proposals — review (2026-06-14)

3 reader waves over the secondary-literature library produced **162 staged proposals**. All validated against `nodes.jsonl`: every referenced id resolves (0 unresolved), all duplicate pairs confirmed real, all 8 quotes flagged `found_verbatim`.

Files: `wave1_maximus.jsonl` (55) · `wave2_amand.jsonl` (72) · `wave3_wiring.jsonl` (35).

## Headline correction
The KG content was **further along than the gap audit suggested** — most "missing" entities exist as **orphaned/unwired shells**, not absences. The real problem is **wiring + duplication + grounding**, not missing nodes. Two genuinely missing items confirmed: a monothelite/dyothelite **debate** node and a Carneadean-anti-astrology **debate** node (both proposed); plus Honorius I (person) and Maximus corpus passages (ingestion).

## Tier 1 — safe, mechanical, high confidence (apply now)
- **6 duplicate merges** (all pairs verified present):
  - `scholarly_work_voelke_1973_…` → `pub_voelke_1973_idee_volonte`
  - `pub_dihle_1982_theory_will` → `pub_dihle_1982_theory_of_will` (23 edges to re-point)
  - `pub_eliasson_2008_…` → `scholarly_work_eliasson_2008_…` (fuller metadata)
  - `pub_sharples_2008_…` → `scholarly_work_sharples_2008_…`
  - `scholarly_work_sharples_1983_alex_de_fato` → delete (0 edges, orphan of `pub_sharples_1983_alexander_fate`)
  - `scholar_dihle_albrecht` (50 edges) → `scholar_albrecht_dihle` (73 edges) — **person merge, confirm first**
- **2 Amand pub duplicates** → canonical `pub_amand_1945_fatalisme` (same ISBN as `pub_amand_1973_fatalisme_liberte`; 1945 1st ed. vs 1973 reprint, identical pagination).
- **3 corrupted edges** referencing ghost `scholarly_work_bobzien_2001_…` (not a node) → repoint `source_id` to `scholarly_work_bobzien_1998_…`.
- **22 `grounded_in` edges** linking unwired scholarly arguments to their pub node: Bobzien ×15, Dihle ×1, Sorabji ×1, Voelke ×2, + others.
- **Orphan-concept rescue:** `concept_gnomic_will_gnome` + `concept_thelema_physikon_natural_will` (both degree 0) → `developed_by` Maximus, `contrasts_with` each other, `employs` from the dyothelite arguments.

## Tier 2 — new nodes (review before apply)
- **`debate_monothelite_dyothelite_controversy`** + 11 edges tying in 5 person shells (Maximus, Sophronius, Sergius, Pyrrhus, Martin I) + the 6 floating dyothelite/monothelite arguments + 3 will-concepts.
- **`debate_carneadean_antiastrology_tradition`** + 20 edges encoding Amand's Carneades→Clitomachus→Cicero→Philo→Origen→Basil/Gregory/Eusebius→Diodore→Nemesius chain.
- **`person_honorius_i_pope_d638`** (was only referenced in metadata).
- **3 publication_nodes** (Maximus secondary lit: Blowers 2016 already present; check `existing_duplicate_ids`).

## Tier 3 — grounding edges (locus → passage match needed)
28 `ground_locus` records. Corpus-coverage check splits them:
- **Groundable now** (corpus has the passages — needs locus→passage_id matching): Cicero *De Div.* II (~40 passages), Philo *De Prov.* (~372), Origen *Philocalia* 23 (~250), Chrysostom (~50), Firmicus *Mathesis* (~21), Gellius/Favorinus *NA* (~51), Aristotle *NE*.
- **Needs ingestion first** (no corpus passages): **Maximus PG 91** (all 4 works — the dyothelite grounding), **Nemesius *De Nat. Hom.* 35–38**, **Gregory Nyssa *Oratio Cat.* 31**, **Cicero *De Nat. Deor.* III**.

## Tier 4 — content gaps requiring ingestion (critical editions on disk?)
- **Maximus the Confessor** corpus (Disp. cum Pyrrho, Opuscula, Ambigua, Q. Thal.) — PG 91 / CCSG / SC. The will-invention endpoint cannot be grounded to primary text until ingested.
- **Nemesius De Natura Hominis** (Morani ed.) — 4 anti-fatalist arguments floating.
- **Gregory of Nyssa Oratio Catechetica** 31 (Srawley / SC 453).
- **Bathrellos *The Byzantine Christ*** (OUP 2004) — standard dyothelite monograph, **not in local library** → acquire.

## Verbatim quotes harvested (8, all `found_verbatim: true`)
- 5 Greek Maximus formulations (γνώμη as διάθεσις; ὄρεξις ἐνδιάθετος; ἐκχώρησις γνωμική; τὸ πῶς θέλειν; γνωμικὴν μεταβολήν) from the Blowers 2016 PDF, with PG/CCSG loci.
- 2 Latin Firmicus *Mathesis* I.2 blocks (nomima barbarika + ethnographic catalogue) from Amand p. 57 OCR.
- 1 Greek topos label νόμιμα βαρβαρικά.
(Each needs a final spot-check against the critical edition before the quote node is created.)

## Open judgment calls
1. Bobzien 15 args mistyped `type=argument` + ancient `period` though they are modern scholarship → reclassify to `scholarly_argument`/`Contemporary`? (frontend-presentation policy).
2. Confirm `scholar_dihle_albrecht` = `scholar_albrecht_dihle` before person merge.
3. Retire the 29 `authored_by → scholar_amand` edges (ontology stretch) in favour of `source_for`?
4. Verify the 8 quotes against critical editions before creating quote nodes.
