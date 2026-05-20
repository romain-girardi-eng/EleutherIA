# KG CHANGELOG

Index navigable des waves d'enrichissement. Chaque wave porte un marqueur metadata sur ses nodes touchés (`<wave_tag>: true`), traçable via grep `data/kg/nodes.jsonl`.

Snapshots préservés sous `data/kg/snapshots/<date>-pre-<wave>/`. Scripts sous `scripts/<wave>.py`.

---

## État final (2026-05-21)

| Métrique | Valeur |
|---|---:|
| Total nodes | 20 208 |
| Total edges | 56 531 |
| `needs_evidence` flaggés | 1 087 (-32.4% depuis 1 608) |
| E2 verified verbatim+page | 551 (513 high + 19 medium + 4 low + 14 not_found + 1 not_applicable) |
| Audit indépendant n=98 | 99% CORRECT (IC95 [94%, 100%]) |
| Scholars couverts E2 | 27 |

---

## Session 2026-05-21

### Intégration 9 acquisitions full-text (sub-agents lecteurs → verbatim + pages)
- `integrate_acquisition_patches_2026_05_21.py` — **+98 nodes** (8 persons/scholars, 9 publications, 3 concepts, 78 arguments) + **314 edges** (9 authored_by + 78 created_by + 227 discusses)
- Normalise les schémas hétérogènes des 9 patches (`arguments`/`scholarly_arguments`, `discusses`/`relates_to`/`related_persons`/`edges`, `quote_verbatim`/`verbatim_evidence`/`verbatim_anchors`, `page`/`page_or_loc`)
- Args portent `e2_verified` (verbatim + page depuis lecture directe), `needs_evidence=false`
- **9 ouvrages** : Barclay 2020 *Paul and the Power of Grace*, Blowers 2016 *Maximus the Confessor*, Boys-Stones 2018 *Platonist Philosophy*, Brand (Qumrân/Belial), Carter 2024 (fatalisme De Int. 9), Eastman 2017 *Paul and the Person*, Hildebrandt, Klawans (Second Temple), Sytsma (autexousion ↔ apocatastase)
- **3 nouveaux concepts** : θέλημα φυσικόν (natural will), gnomic will (γνώμη), belial demonic source
- **Lacune structurelle comblée** : création de `person_paul_apostle` (aucun node Paul n'existait — seulement J.-P. Sartre)

### Wire Paul node
- `wire_paul_node_2026_05_21.py` — 16 discusses → `person_paul_apostle` depuis les args Eastman (8) + Barclay (8), tous deux exégèse paulinienne intégrale

### Reste de cette wave
- Boys-Stones suggérait persons_to_create Numénius/Atticus (placeholders sans id dans le patch) — non créés ; leurs discusses sont skippés (targets absents)
- Carter 2024 contredit le node `sea_battle` existant — à arbitrer dans une passe future

---

## Session 2026-05-18

### Bobzien 1998 nuance + OSAP→Phronesis fix
- `bobzien_1998_nuance_patch_2026_05_18.py` — ajout §XII volatility framing
- `bobzien_1998_osap_phronesis_fix_2026_05_18.py` — 5 nodes corrigés (Bobzien 1998 = Phronesis, pas OSAP)

### Intégration Mitsis 2021 + Lienemann 2012 + Brennan 2005
- `integrate_mitsis_lienemann_brennan_2026_05_18.py` — 6 nodes + 12 edges
- `enrich_mitsis_lienemann_fulltext_2026_05_18.py` — citations verbatim après acquisition PDF
- `fix_lienemann_french_to_english_2026_05_18.py` — règle citation `original + English` (jamais français)

### Acquisition wave (16 publications) + recovery bonus
- `integrate_acquisition_wave_2026_05_18.py` — Coope 2020, Bobzien 2021, Huby 1967, Kahn 1988, Sorabji 1980, etc.
- `integrate_recovery_bonus_2026_05_18.py` — Adamantiana 13/21, Magris 2021

### Fürst 2022 full audit
- `audit_furst_2022_full_2026_05_18.py` — 18 nodes enrichis, 4 nouveaux args, 41 edges, citations bilingue DE+EN

### Wire orphan arguments (massif)
- `wire_orphan_arguments_2026_05_18.py` — **843 arguments orphan → 0** (1887 edges créées : 843 created_by + 565 discusses + 5 cites_primary_source)

### Phases A/B/C/D quality fixes
- `fix_phase_a_ontology_violations_2026_05_18.py` — 27 violations corrigées (2 DELETE + 23 REQUALIFY + 2 INVERT)
- `fix_phase_b_dedupe_publications_2026_05_18.py` — 32 paires merged, 35 shells deprecated
- `fix_phase_c_wire_orphans_2026_05_18.py` — 89 edges (pubs, persons, works, schools)
- `fix_phase_d_enrich_pub_metadata_2026_05_18.py` — 114 local_pdf_path + ~50 DOIs Crossref

### Misc
- `fix_long_1988_misattribution_2026_05_18.py` — pub_long_1988_discovering_will = misattribution (vrai auteur = Kahn 1988)
- `create_missing_scholars_2026_05_18.py` — 17 nouveaux scholars créés (Frankfurt, Williams, Hardie, Ryle, etc.)

---

## Session 2026-05-19

### Phase E (needs_evidence campaign)
- `wire_modern_args_to_pubs_2026_05_19.py` — **E1** : 249 edges modern args → publication scholar (heuristique surname+year+jaccard)
- `wire_ancient_args_to_passages_2026_05_19.py` — **E3** : 267 edges ancient args → passages KG existants (regex De Princ. III.1 → passage_origen_pa_3_1_*, etc.)

### E2 verbatim PDF verification (15 batches, 27 scholars)
**Pattern** : agent lit le PDF en DOCTORAT, extrait verbatim + page exacte + chapter + context → patch JSON `data/kg/e2_patches/<scholar>.json` → merge via `integrate_e2_patches_2026_05_19.py`

| Scholar | Args verified | PDFs lus |
|---|---:|---|
| Bobzien | 69 | 1998 Phronesis + 2001 OUP + 2021 Essays |
| Dettwiler | 46 | 9 publications désambigïsées par épître |
| Frede | 37 | A Free Will 2011 (+ 5 args réattribués → Dorothea Frede) |
| Pouderon | 27 | Apologistes II s. + Athénagore |
| Dihle | 26 | Theory of Will 1982 |
| Jewett | 25 | Hermeneia Romans (verses, pas pages) |
| Crouzel | 15 | Théologie image 1956 + Origène philosophie 1962 |
| Eliasson | 15 | Notion eph hêmin Plotinus 2008 + article 2009 |
| Hendriksen | 15 | NTC Romans (verses) |
| Gaventa | 15 | NTL Romans (verses) |
| Fitzmyer | 14 | AYB Romans (verses) |
| Maston | 13 | Divine and Human Agency 2010 |
| Telfer | 13 | Autexousia JTS 1957 |
| Wells | 12 | Grace and Agency Brill 2014 |
| Ramelli | 12 | Alexander → Origen 2014 |
| Boys-Stones | 12 | Middle Platonists BICS 2007 |
| Hall | 12 | Origen and Prophecy 2021 (1 node Melito déprécié) |
| Fürst | 10 | (déjà 19 vérifiés via audit du 18-mai) |
| Sorabji | 10 | Necessity 1980 (intros + body après OCR 19-mai) |
| Engberg-Pedersen | 10 | Paul and the Stoics 2000 + Cosmology 2010 |
| Belcastro | 9 | La predestinazione 2016 (Adamantius) |
| Cary | 9 | A Brief History 2007 (BSL) |
| Rousseau | 9 | SC 100/152/264 Irénée |
| Donini | 9 | Aristotle and Determinism 2010 (+ 4 medium via Huby review) |
| Barclay | 9 | Divine and Human Agency 2006 |
| Minns | 8 | Justin Apologies OECT 2009 |
| Grant | 8 | Irénée 1996 + Early Alex. Christ. 1971 (3 nodes need rephrasing) |
| Hick | 8 | Evil and God of Love (re-acquis Palgrave 2010) |
| Sapolsky | 6 | Determined 2023 |
| Frick | 6 | Providence in Philo 1999 |
| Irwin | 7 | Who Discovered the Will 1992 + Development of Ethics 2007 |
| Brouwer | 7 | Fate Providence Free Will 2020 (co-éd. Vimercati) |
| Byerly | 7 | Free Will Theodicies Sophia 2017 |
| Craig | 7 | Divine Foreknowledge 1990 |
| Linjamaa | 7 | Ethics Tripartite Tractate 2019 |
| Tolan | 6 | Thèse Cambridge 2020 |
| Salles | 6 | Stoics Determinism 2005 |
| Sharples | 4+1 | De Fato Duckworth 1983 (re-acquis OCR'd 19-mai) — **trouvaille Lienemann** |
| **Total** | **551** | |

### 12 corrections findings (apply_12_corrections_2026_05_19.py)
1. Donini PDF mis-label → créé `pub_huby_1991_review_donini_ethos`
2. Frede→Dorothea Frede (5 args réattribués)
3. Hall/Melito : node déprécié (Melito absent du livre)
4. Boys-Stones : 2 reformulations + 1 réattribution → Andresen 1952
5. Dihle : 4 reformulations (apparat hébreu/indien retiré, augustinien précisé)
6. Belcastro : 2 re-wirings 2017→2016
7. Minns : 1 doublon `superseded_by`
8. Belcastro : 1 doublon `superseded_by`
9. Dettwiler : date Colossiens 60s→70-80s
10. Sharples 1983 : `re_acquisition_priority: high`
11. Sorabji 1980 : `ocr_priority: high`
12. Pouderon : 5 args orphelins flaggés `e2_not_found_reason`

### Audit indépendant + P0 fixes
- Audit n=98, 99% CORRECT, 0 fabrication détectée
- `rewire_post_dedupe_2026_05_19.py` — 37 edges supprimées + 69 rebasculées (zéro edges sortant de shells deprecated)
- `apply_gaventa_pdf_source_fill_2026_05_19.py` — 15 pdf_source remplis
- `flag_post_rewire_orphans_2026_05_19.py` — 1 orphan flagué
- `apply_hick_force_2026_05_19.py` — 8 Hick force-applied après re-acquisition PDF complet

### Acquisition PDFs manquants (16/21)
**Acquis** : Knobe 2003, Erasmus/Luther Winter, Hick 2010 Palgrave (re-acq.), Sharples 1983 OCR'd, Sorabji 1980 OCR'd, L&S 1987 vol.2
**Déjà présents** : Frankfurt, Kane, Pereboom, Mele, van Inwagen, Reid, Spinoza, Hadot 1992, HLGC V, SC 470, Mitsis 2021, Lienemann 2012
**Échecs** : Meyer 1993 (archive.org borrow-only), Mitsis FR Brepols, Kobusch 2018 Mohr Siebeck, Hengstermann 2016 Aschendorff, Mitsis 2021 FR

### Finding pivot pour thèse H3 — encodé en KG
**`scholarly_position_sharples_alexander_libertarian_unsupported`** (`finalize_sharples_landmark_2026_05_19.py`)

Chaîne Sharples 1983 ← Lienemann 2012 ← contre Frede 2011, grep-traversable :
> « Alexander is wrong to assume that determinism implies that deliberation will make no difference to our actions ; it is perfectly compatible with determinism that deliberation should lead us to decide against the course of action that initially appeared favourable, only it will be predetermined that it should do so. » (Sharples 1983, Commentary p. 141)

+ distinction Sharples p. 22 entre ce qu'Alexandre **stipule** (libertarianism) vs ce qu'il **démontre** (peu) — distinction que Frede 2011 collapse et que Lienemann 2012 ressuscite.

Edges : `critiques → pub_frede_2011_free_will`, `discussed_in ← pub_sharples_1983 + pub_lienemann_2012`.

### Mis-attributions Sharples corrigées
4 args réattribués (1 → Sharples 1982 *Providence*, 2 → Sharples 2008 *L'accident du déterminisme*, 1 → Sharples 1991 Cicéron/Boèce) + 1 pub flag `needs_pub_node_creation` (Sharples 1983 *Vigiliae Christianae* Némésius).

---

## Reste

- **Bin B** (94 nodes, dont 52% wirables via metadata existante Amand/Bobzien/Dihle, 32% reattributable, 16% needs PDF) — 1 session ciblée
- **Scholars PDFs à acquérir** : Meyer 1993 monograph (archive.org login), Kobusch 2018, Hengstermann 2016, Sharples 1983 *Vigiliae Christianae* Némésius
- **Amand Bin C** : ~191 nodes bloqués externe (SC 35bis Hadas-Lebel)
- **Concepts + synthesis sans evidence** : ~360 nodes (stratégie séparée)

---

## Convention de citation (mémoire `citation-original-plus-english`)

Toujours : **original language verbatim + English translation** dans les fields `quote_<lang>` + `translation_en`. Jamais français pour traduction (English = lingua franca scholarly).

Pour anglais original : `quote_verbatim` seul, pas de traduction.

---

## Audit & rollback

Chaque wave a son snapshot pré-mutation sous `data/kg/snapshots/<date>-pre-<wave>/{nodes,edges}.jsonl`. Rollback ciblé toujours possible.

Idempotence : tous les scripts vérifient leur marqueur metadata avant ré-application. 2ᵉ run = no-op.
