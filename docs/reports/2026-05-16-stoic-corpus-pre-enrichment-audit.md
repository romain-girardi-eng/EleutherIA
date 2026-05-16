---
date: 2026-05-16
status: baseline
context: DHQ article "Algorithmic provenance analysis of six moral anti-fatalist pivots"
plan: docs/superpowers/plans/2026-05-16-amand-piste1-article-implementation.md
task: T1
mutates_kg: false
---

# Stoic Primary Corpus — Pre-Enrichment Audit

## Purpose

Establish the baseline coverage of the Stoic primary corpus (Chrysippus, Cléanthe, Posidonios, Panétius) in the EleutherIA KG before Tasks T2-T4 enrich it with SVF fragments and additional testimonia. This audit conditions the provenance analysis underpinning the DHQ article: without measurable primary-source anchoring, the six anti-fatalist pivots (Carnéade → Origène / Eusèbe / Basile / Grégoire de Nysse / Chrysostome / Némésios) cannot be cleanly attributed downstream of an explicit Stoic source layer.

## Method

Read-only inspection of `data/kg/nodes.jsonl`, `data/kg/edges.jsonl`, `data/kg/publications.bib`. Availability probes against archive.org (SVF I-IV) and the OpenGreekAndLatin First1KGreek repository (CTS-encoded Greek XML).

## Findings

### Chrysippus (c. 279-206 BCE)

| Metric | Count |
|---|---|
| `argument` nodes | 19 |
| `passage` nodes (direct primary text) | **0** |
| `work` nodes | 1 (`work_chrysippus_svf_ii` — empty shell) |
| `evidenced_by` edges sourced from Chrysippus nodes | **0** |
| Total edges incident to `chrysippus*` ids | 339 distinct edges incident to `chrysippus*` ids (234 out / 119 in, with 14 self-internal edges deduped) |

**Argument breakdown** (19):
- 2 native ancient arguments (`argument_chrysippus_causal_taxonomy`, `argument_cylinder_analogy_chrysippus_*`)
- 14 modern `scholarly_argument_*` nodes (Bobzien × 6, Salles × 2, Gourinat, Eliasson, Šuster, Fürst, plus two Salles position summaries)
- 3 Amand-derived `argument_*_chrysippus_*` nodes wired in Phase 11 (Bobzien bivalence, Gómez compatibilism, Salles eph' hêmin)

**Critical gap.** `work_chrysippus_svf_ii` exists in the KG as a placeholder (only 3 edges: `part_of → collection_svf`, `authored_by → person_chrysippus_280_206bce_*`, one `cites_primary_source` from Fürst 2022) **and contains zero child passages**. Every Chrysippus-related claim in the KG is therefore unanchored to a verifiable SVF fragment. This is the single largest provenance hole in the Stoic layer.

### Cléanthe d'Assos (c. 330-230 BCE)

| Metric | Count |
|---|---|
| `argument` nodes | 1 (`argument_cleanthes_hymn_to_zeus_argument_*`) |
| `passage` nodes | **0** |
| `work` nodes | 1 (`work_cleanthes_hymn_to_zeus` — empty shell) |
| `person` nodes | 1 (`person_cleanthes_assos_330_230bce`) |

Only the Hymn to Zeus is referenced. No SVF I fragments (theology, cosmology, ethics) are anchored. The Hymn itself has no passage children — the Greek text is not yet ingested.

### Posidonios d'Apamée (c. 135-51 BCE)

| Metric | Count |
|---|---|
| `argument` nodes | 1 (`scholarly_argument_koch_posidonius_*`) |
| `passage` nodes | **0** |
| `work` nodes | 0 |
| `person` nodes | 1 (`person_posidonius_apameia_135_51bce`) |
| `publication` nodes | 2 (Edelstein-Kidd 1972, Kidd 1971) |
| `synthesis` nodes | 1 (`synthesis_amand1945_posidonius_scientific_foundation_astrology`) |
| `concept` nodes | 1 (`concept_sympatheia_universal_posidonius_nyssa`) |

Edelstein-Kidd is bibliographically registered but **no testimonia node has been linked to it**. Amand 1945 §I situates Posidonios as the scientific founder of Hellenistic astrology — directly relevant to the article's pivot #5 (Grégoire de Nysse) and pivot #6 (Némésios), both of which engage astrological fatalism. Currently this connection is mediated only by a `synthesis_*` node with no primary anchor.

### Panétius de Rhodes (c. 185-109 BCE)

| Metric | Count |
|---|---|
| `argument` nodes | 1 (`argument_vimercati_2014_panaetius_eph_hemin_unique_occurrence`) |
| `passage` nodes | **0** |
| `work` nodes | 0 |
| `person` nodes | 1 (`person_panaetius_rhodes_185_109bce`) |
| `synthesis` nodes | 1 (`synthesis_destree2014_ch10_vimercati_panaetius`) |

Vimercati 2014 anchors one observation (the lone Panaetian ἐφ' ἡμῖν occurrence preserved by Némésios) but no testimonia are linked. Van Straaten 1962 fragments not present in `publications.bib`.

## Source Availability

### Archive.org — Arnim, SVF (Teubner 1903-1905, indices 1924)

All four volumes are accessible via the canonical `stoicorumveterum0Xarniuoft` identifiers (the variant `stoicorumveterumfra0X*` referenced in older notes returns 404 — superseded).

| Volume | Identifier | PDF | OCR (`_djvu.txt`) |
|---|---|---|---|
| SVF I (Zeno, Cléanthe & early Stoics) | `stoicorumveterum01arniuoft` | 16.0 MB | 620 KB |
| **SVF II (Chrysippus — Logica & Physica)** | `stoicorumveterum02arniuoft` | 28.2 MB | 1.53 MB |
| SVF III (Chrysippus — Moralia + early successors) | `stoicorumveterum03arniuoft` | 22.5 MB | 747 KB |
| SVF IV (indices, Adler 1924) | `stoicorumveterum04arniuoft` | 21.9 MB | 1.01 MB |

Each item also exposes hOCR / chocr / DjVu XML. Download path for ingestion: `https://archive.org/download/<identifier>/<identifier>.pdf` (or `_djvu.txt` for fast OCR text). OCR quality is adequate for fragment-number anchoring but Greek diacritics will require manual verification on cited fragments.

### OpenGreekAndLatin — First1KGreek (CTS-encoded XML)

Authoritative TEI XML transcription of SVF II + III is available under the TLG canon **tlg1264 = Chrysippus**:

| URN | Source edition | XML size |
|---|---|---|
| `urn:cts:greekLit:tlg1264.tlg001.1st1K-grc1` (Fragmenta Logica et Physica) | Arnim SVF II, Teubner 1903 (1964 reprint) | 1.58 MB |
| `urn:cts:greekLit:tlg1264.tlg002.1st1K-grc1` (Fragmenta Moralia) | Arnim SVF III, Teubner 1903 (1964 reprint) | 901 KB |
| `urn:cts:greekLit:tlg1264.tlg003.1st1K-grc1` | (smaller fragment collection) | 9 KB |
| `urn:cts:greekLit:tlg1264.tlg004.1st1K-grc1` | (smaller fragment collection) | 79 KB |

**This is the recommended ingestion path** (already a known pattern in `database/scripts/ingest_scaife_work.py`/`fetch_scaife_work.py`): clean, structured, citable by SVF fragment number via the CTS URN, no OCR noise.

For Cléanthe SVF I fragments, Posidonios, and Panétius the OGL coverage is thinner — those will require Edelstein-Kidd / van Straaten / Arnim SVF I extraction via OCR or a curated subset.

### Other notable cross-references

- `collection_svf` exists as a `source_collection` node — destination for `part_of` edges.
- `pub_furst_2022_wege_freiheit` already cites `work_chrysippus_svf_ii` as primary source — once passages exist they can be wired to Fürst's interpretive claims.
- Amand 1945 §I (Posidonios → astrology) is anchored to `synthesis_amand1945_posidonius_*`; needs a primary testimonium (Cic. *Div.* I.125-126 or Aug. *CD* V.2) to satisfy SHACL provenance shapes.

## Estimated Enrichment Scope

For the article's argumentative requirements (six pivots must each be grounded in a verifiable Stoic source layer the patristic authors can be shown to react against), the following minimum coverage is needed.

| Stoic | Target fragments to ingest | Notes |
|---|---|---|
| Chrysippus | **80-120** (SVF II 939-1000 fate/causation/freedom + SVF III 169-215 prohairesis/akrasia + selected SVF II 974-979 cylinder) | OGL XML; pick fragments cited in Bobzien 1998, Salles 2005, Fürst 2022, Frede 2011 |
| Cléanthe | **15-25** (SVF I 527, 537, 562, 563 — fate + Zeus + Hymne) | SVF I via archive.org OCR; Hymne to Zeus from Scaife if available, fallback OGL |
| Posidonios | **10-20** testimonia (Edelstein-Kidd F25-30 on astrology + sympathy fragments cited in Cic. *Div.* I.130) | Already-registered publication; need cross-source extraction |
| Panétius | **5-10** testimonia (Némésios *De Nat. Hom.* 35 + Cic. *Off.* I-II eph' hêmin contexts) | Van Straaten 1962 to add to bib |
| **TOTAL** | **~110-175** new `passage` nodes | Compatible with the "~100-200 fragments" working estimate |

Each ingested passage also generates ≥1 `evidenced_by` or `cites_primary_source` edge, plus `part_of → work_*` + `authored_by → person_*` — likely ~400-600 new edges total. SHACL invariants (`shapes/invariants/`) require validation post-ingest.

## Conclusion

The Stoic primary layer in the KG is currently a **bibliographic shell**: persons and publication references are wired, but **0 anchored passages exist** across the four target Stoics. All current Chrysippus/Cléanthe/Posidonios/Panétius arguments rely either on modern scholarly interpretation (Bobzien, Salles, Fürst, Vimercati) or on Amand 1945's synthesis — never on a directly retrievable fragment.

For the DHQ article to make a defensible provenance claim ("pivot N at author M directly engages Stoic position X"), the missing primary anchor must be supplied. Targeting **~100-200 supplementary fragments** (concentrated on Chrysippus SVF II/III via OGL XML, supplemented by SVF I and Edelstein-Kidd testimonia for the other three Stoics) brings each pivot to a verifiable source chain.

**Next steps (sequenced)**:
1. **T2** — Bulk-ingest `tlg1264.tlg001` (SVF II) from First1KGreek, parsing by Arnim fragment number; wire `part_of → work_chrysippus_svf_ii`.
2. **T3** — Ingest SVF I targeted fragments + Hymne à Zeus complete text.
3. **T4** — Add Edelstein-Kidd + van Straaten testimonia by cross-reference (Cicéron / Némésios already in the KG).
4. **T5** — Re-run SHACL invariants + tests; close Phase 1 with a delta report.

The current task is read-only and does not mutate `data/kg/`.
