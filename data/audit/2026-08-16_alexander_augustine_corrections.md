# 2026-08-16 — Alexander / Augustine audit corrections (applied)

Applier: `scripts/apply_2026_08_16_alexander_augustine_corrections.py`  
Data: `scripts/data_2026_08_16_alexander_augustine_corrections.py`  
Target: `data/kg/nodes.jsonl` (+ `data/kg/publications.bib` regenerated from it).  
`data/kg/edges.jsonl` untouched — no id was renamed.

## Summary

- nodes read: 19992
- target nodes: 20 (found 20, missing 0)
- nodes changed: 20
- nodes already stamped (skipped): 0
- U+02BC -> U+2019: 18104 occurrence(s) in 2830 node line(s)
- SKIPPED: Frede node: record 'fundamentally flawed' (pp. 177-178) as Frede's verified wording -> SKIPPED — the phrase is not Frede's
- SKIPPED: Sorabji 2017: set metadata.reference_status='unverified — title-only shell; four-strands thesis authentic to Sorabji but this 2017 citation could not be confirmed' -> SKIPPED — the citation was confirmed locally
- SKIPPED: Alexander De fato 19: 'ἐπὶ τίσιν οὐν αἱ κολάσεις' vs TLG 'οὖν' -> OBSERVED, NOT APPLIED — outside the audited item list
- SKIPPED: data/corpus/passages.jsonl carries the same 'futurumfiturum' defect -> OBSERVED, NOT APPLIED — outside the declared file scope
- SKIPPED: data/kg/edges.jsonl carries 12 U+02BC occurrences -> OBSERVED, NOT APPLIED — outside the declared file scope

## Note on `data/kg/publications.bib`

`publications.bib` and `publications_bibtex_report.json` are *generated* artifacts: `scripts/export_publications_bibtex.py` derives them wholly from the `type == "publication"` nodes of `data/kg/nodes.jsonl`. This pass regenerates them, which produces a diff larger than the pass itself, because the committed `.bib` had drifted out of sync with the graph. The two parts were measured separately:

- **This pass's own contribution — 11 field lines across 5 entries:** `author = {Ernesto Bonaiuti}`, `publisher` → `journal` + `pages`/`volume`/`number` on the Bonaiuti entry; `author = {John Moon}`; `author = {Mako A. Nagasawa}`; `author = {Richard Sorabji}` + `booktitle` + `editor` + `pages` on the Sorabji 2017 entry.
- **Pre-existing drift, ~445 lines, NOT produced here:** regenerating from the *unmodified* `HEAD` nodes already yields the same 319 entries against the committed file's 357. The 38 dropped entries are publication nodes that no longer exist in the graph (merged by earlier dedup waves) and whose BibTeX entries were therefore dangling; several keys also move to the year/type the node metadata already carried — including `publication-2015-la-causalite-humaine-…` (`@article`, 2015, authorless) → `publication-2019-la-causalite-humaine-…` (`@book`, 2019, `author = {Isabelle Koch}`, Classiques Garnier, ISBN), which is the §3 fix the audit asked for.
- `nodes_with_missing_fields` in the report: 198 → 194 (the four `author` fields added above).

## Per-node before → after

### `argument_frede_2011_alexander_libertarian_dead_end`

- **description (span)** — `span`
  - before: `Conclusion: Alexander the only major ancient philosopher whose notion is fundamentally flawed, and he is precisely`
  - after:  `Conclusion: Frede's headline answer to 'was the notion of a free will flawed from its very beginning?' is NEGATIVE, and Alexander is the single exception he carves out of it — all the other authors have notions that 'do not seem to be basically flawed in the way a notion like Alexander's is' (pp. 177-178; Frede's adjective is 'basically', not 'fundamentally', and the verdict on Alexander is delivered obliquely). Alexander is precisely`
- **description (span)** — `span`
  - before: `the notion attacked by Ryle, Williams, and Frede`
  - after:  `the notion attacked by Ryle, Williams, and Frede. ⏎  ⏎ WORDING WARNING (verified 2026-08-16 against the local extraction of Frede 2011): 'dead end' is NOT Frede's phrase — it is this node's id slug (argument_frede_2011_alexander_libertarian_dead_end) and occurs nowhere in the book. Never quote the slug as Frede's words. Frede's verified wording is: (i) p. 100, verbatim and exact, 'the ancestor of the notion that to have a free will is to be able, in the very same circumstances, to choose between doing A and doing B'; (ii) pp. 177-178, 'basically flawed' — NOT 'fundamentally flawed' — and said of the other authors, not predicated directly of Alexander; (iii) the metaphor Frede actually applies to Alexander is 'a hopeless tangle' (p. 97; 'Alexander got into this tangle', p. 100), the phrase Sorabji also quotes back at him.`
- **id_slug_warning** — `set`
  - before: `<absent>`
  - after:  `'dead end' is NOT Frede's phrase — it is this node's id slug. The phrase occurs nowhere in Frede 2011. Never quote the slug as Frede's words.`
- **frede_verified_wording** — `set`
  - before: `<absent>`
  - after:  `{"p_100_ancestor": "the ancestor of the notion that to have a free will is to be able, in the very same circumstances, to choose between doing A and doing B", "p_100_ancestor_status": "verbatim exact (Frede 2011, p. 100, on Alexander)", "pp_177_178_flawed": "do not seem to be basically flawed in the way a notion like Alexander's is", "pp_177_178_status": "Frede writes 'basically flawed', NOT 'fundamentally flawed', and predicates it obliquely — of the other authors, from whom Alexander is the single exception carved out of an otherwise negative answer to 'was the notion of a free will flawed from its very beginning?'", "p_97_metaphor": "In trying to explicate this, Alexander seems to be driven into a hopeless tangle.", "dead_end": "absent from Frede 2011 — zero occurrences"}`
- **wording_verified_2026_08_16** — `set`
  - before: `<absent>`
  - after:  `true`
- **verification_notes** — `note`
  - before: _(none)_
  - after:  `[Vérif. 2026-08-16, local Frede_2011_Free_Will.txt] The audit brief asked for 'fundamentally flawed (pp. 177-178)' to be recorded as Frede's verified wording. It is NOT: 'fundamentally' occurs once in the whole book, in A. A. Long's foreword. Frede writes 'basically flawed'. The description and metadata.frede_verified_wording carry the corrected reading. The p. 100 'ancestor' sentence is confirmed verbatim and exact. 'dead end' is a slug artefact, absent from the book; Frede's metaphor is 'a hopeless tangle' (p. 97, p. 100).`

### `scholarly_argument_guyomarc_h_alexander_of_aphrodisias_de_fa_0`

- **scholarly_work_id** — `set_if`
  - before: `scholarly_work_koch_2019_la_causalite_humaine_sur_le_de_fato_d_alexandre`
  - after:  `scholarly_work_guyomarc_h_2015_la_causalit_humaine_sur_le_de_fato_d_ale`
- **verification_notes** — `note`
  - before: _(none)_
  - after:  `[Vérif. 2026-08-16] metadata.scholarly_work_id pointed at 'scholarly_work_koch_2019_la_causalite_humaine_sur_le_de_fato_d_alexandre', which is not a node in the graph (dangling reference left behind when the Koch attribution was corrected on the label only). Retargeted to the node that actually carries the record, 'scholarly_work_guyomarc_h_2015_la_causalit_humaine_sur_le_de_fato_d_ale', whose id slug is stale but whose label and metadata are correct (Koch 2019).`

### `scholarly_argument_guyomarc_h_alexander_s_aristotelian_sourc_5`

- **scholarly_work_id** — `set_if`
  - before: `scholarly_work_koch_2019_la_causalite_humaine_sur_le_de_fato_d_alexandre`
  - after:  `scholarly_work_guyomarc_h_2015_la_causalit_humaine_sur_le_de_fato_d_ale`
- **verification_notes** — `note`
  - before: _(none)_
  - after:  `[Vérif. 2026-08-16] metadata.scholarly_work_id pointed at 'scholarly_work_koch_2019_la_causalite_humaine_sur_le_de_fato_d_alexandre', which is not a node in the graph (dangling reference left behind when the Koch attribution was corrected on the label only). Retargeted to the node that actually carries the record, 'scholarly_work_guyomarc_h_2015_la_causalit_humaine_sur_le_de_fato_d_ale', whose id slug is stale but whose label and metadata are correct (Koch 2019).`

### `scholarly_argument_guyomarc_h_alexander_s_conception_of_what_2`

- **scholarly_work_id** — `set_if`
  - before: `scholarly_work_koch_2019_la_causalite_humaine_sur_le_de_fato_d_alexandre`
  - after:  `scholarly_work_guyomarc_h_2015_la_causalit_humaine_sur_le_de_fato_d_ale`
- **verification_notes** — `note`
  - before: _(none)_
  - after:  `[Vérif. 2026-08-16] metadata.scholarly_work_id pointed at 'scholarly_work_koch_2019_la_causalite_humaine_sur_le_de_fato_d_alexandre', which is not a node in the graph (dangling reference left behind when the Koch attribution was corrected on the label only). Retargeted to the node that actually carries the record, 'scholarly_work_guyomarc_h_2015_la_causalit_humaine_sur_le_de_fato_d_ale', whose id slug is stale but whose label and metadata are correct (Koch 2019).`

### `scholarly_argument_guyomarc_h_alexander_s_rhetorical_strateg_6`

- **scholarly_work_id** — `set_if`
  - before: `scholarly_work_koch_2019_la_causalite_humaine_sur_le_de_fato_d_alexandre`
  - after:  `scholarly_work_guyomarc_h_2015_la_causalit_humaine_sur_le_de_fato_d_ale`
- **verification_notes** — `note`
  - before: _(none)_
  - after:  `[Vérif. 2026-08-16] metadata.scholarly_work_id pointed at 'scholarly_work_koch_2019_la_causalite_humaine_sur_le_de_fato_d_alexandre', which is not a node in the graph (dangling reference left behind when the Koch attribution was corrected on the label only). Retargeted to the node that actually carries the record, 'scholarly_work_guyomarc_h_2015_la_causalit_humaine_sur_le_de_fato_d_ale', whose id slug is stale but whose label and metadata are correct (Koch 2019).`

### `scholarly_argument_guyomarc_h_alexander_s_target_stoic_deter_1`

- **scholarly_work_id** — `set_if`
  - before: `scholarly_work_koch_2019_la_causalite_humaine_sur_le_de_fato_d_alexandre`
  - after:  `scholarly_work_guyomarc_h_2015_la_causalit_humaine_sur_le_de_fato_d_ale`
- **verification_notes** — `note`
  - before: _(none)_
  - after:  `[Vérif. 2026-08-16] metadata.scholarly_work_id pointed at 'scholarly_work_koch_2019_la_causalite_humaine_sur_le_de_fato_d_alexandre', which is not a node in the graph (dangling reference left behind when the Koch attribution was corrected on the label only). Retargeted to the node that actually carries the record, 'scholarly_work_guyomarc_h_2015_la_causalit_humaine_sur_le_de_fato_d_ale', whose id slug is stale but whose label and metadata are correct (Koch 2019).`

### `scholarly_argument_guyomarc_h_necessity_and_fate_alexander_s_3`

- **scholarly_work_id** — `set_if`
  - before: `scholarly_work_koch_2019_la_causalite_humaine_sur_le_de_fato_d_alexandre`
  - after:  `scholarly_work_guyomarc_h_2015_la_causalit_humaine_sur_le_de_fato_d_ale`
- **verification_notes** — `note`
  - before: _(none)_
  - after:  `[Vérif. 2026-08-16] metadata.scholarly_work_id pointed at 'scholarly_work_koch_2019_la_causalite_humaine_sur_le_de_fato_d_alexandre', which is not a node in the graph (dangling reference left behind when the Koch attribution was corrected on the label only). Retargeted to the node that actually carries the record, 'scholarly_work_guyomarc_h_2015_la_causalit_humaine_sur_le_de_fato_d_ale', whose id slug is stale but whose label and metadata are correct (Koch 2019).`

### `scholarly_argument_guyomarc_h_the_human_problem_of_free_will_4`

- **scholarly_work_id** — `set_if`
  - before: `scholarly_work_koch_2019_la_causalite_humaine_sur_le_de_fato_d_alexandre`
  - after:  `scholarly_work_guyomarc_h_2015_la_causalit_humaine_sur_le_de_fato_d_ale`
- **verification_notes** — `note`
  - before: _(none)_
  - after:  `[Vérif. 2026-08-16] metadata.scholarly_work_id pointed at 'scholarly_work_koch_2019_la_causalite_humaine_sur_le_de_fato_d_alexandre', which is not a node in the graph (dangling reference left behind when the Koch attribution was corrected on the label only). Retargeted to the node that actually carries the record, 'scholarly_work_guyomarc_h_2015_la_causalit_humaine_sur_le_de_fato_d_ale', whose id slug is stale but whose label and metadata are correct (Koch 2019).`

### `passage_alex_fat_19`

- **description (span)** — `span`
  - before: `κολάζειν τὸν ποιήσαντα`
  - after:  `κολάζειν τὸ ποιήσαντα`
- **verification_notes** — `note`
  - before: _(none)_
  - after:  `[Vérif. 2026-08-16, TLG E via scripts/tlg_search.py] the Phalaris sentence read 'κολάζειν τὸν ποιήσαντα'. That form returns 0 hits in the whole TLG E; the Bruns text as carried by TLG0732 @byte 7373803 reads 'ὡς ἐπί τινι τῶν οὕτως γινομένων κολάζειν τὸ ποιήσαντα' (1 hit, this locus). Aligned to the TLG/Bruns reading. NOT touched in this pass, and left for a later item-by-item review: the node also reads 'ἐπὶ τίσιν οὐν αἱ κολάσεις' where TLG reads 'οὖν'.`
- **ocr_correction_2026_08_16** — `set`
  - before: `<absent>`
  - after:  `true`

### `passage_eusebius_praep_ev_6_6_17`

- **description (span)** — `span`
  - before: `ἐξουσίας σίας εἰς`
  - after:  `ἐξουσίας εἰς`
- **description (span)** — `span`
  - before: `οὕτω γὰρ ἐπεὶ ἐναργῶς`
  - after:  `οὕτως γὰρ ἐπεὶ ἐναργῶς`
- **verification_notes** — `note`
  - before: _(none)_
  - after:  `[Vérif. 2026-08-16, TLG E via scripts/tlg_search.py] two readings corrected against TLG2018 (Eusebius, Praep. Ev.): (a) the dittography 'ἐκ τῆς ἰδίας ἐξουσίας σίας' (0 hits in TLG E) → 'ἐκ τῆς ἰδίας ἐξουσίας' (TLG2018 @byte 528481, 1 hit, in this exact sentence); (b) 'οὕτω γὰρ ἐπεὶ ἐναργῶς' (0 hits) → 'οὕτως γὰρ ἐπεὶ ἐναργῶς' (TLG2018 @byte 528238, 1 hit). The First1KGreek TEI re-encoding of Dindorf t. I (1867) that this node was ingested from carried both defects.`
- **ocr_correction_2026_08_16** — `set`
  - before: `<absent>`
  - after:  `true`

### `passage_firmicus_math_1_2_5`

- **description (span)** — `span`
  - before: `omnia ex rebus bumanis virtutum`
  - after:  `omnia ex rebus humanis virtutum`
- **description (span)** — `span`
  - before: `cupiditates secarus stellarum`
  - after:  `cupiditates securus stellarum`
- **verification_notes** — `note`
  - before: _(none)_
  - after:  `[Vérif. 2026-08-16] description reproduced two OCR residues of the archive.org DjVu scan of Kroll–Skutsch (Teubner t. I, 1897): 'ex rebus bumanis' and 'cupiditates secarus'. Both are adjudicated in the node's own cited source file, data/scholarly_sources/ocr/firmicusmathesis/source.md, section '### Math I.2.5' > 'Anomalies OCR observées': 'bumanis' → canon. 'humanis' (confusion h → b); 'secarus' → canon. 'securus' (confusion u → a). Applied. The remaining sections I.2.6-11 of the same OCR still carry their documented residues and are NOT touched by this pass.`
- **ocr_correction_2026_08_16** — `set`
  - before: `<absent>`
  - after:  `true`

### `passage_gellius_na_vii_2_7_2_5`

- **description (span)** — `span`
  - before: `quicquid futurumfiturum est`
  - after:  `quicquid futurum est`
- **verification_notes** — `note`
  - before: _(none)_
  - after:  `[Vérif. 2026-08-16] description read 'quicquid futurumfiturum est'. That is a TEI <choice> flattening artefact of the Perseus phi1254.phi001.perseus-lat2 ingestion (the same cache shows 'scriptumscripturm', 'futurumfuturunm', 'tumTurn', 'eamearn'), not a transmitted reading. Corrected to 'quicquid futurum est' on the authority of von Arnim, SVF II.1000, local TEI OCR data/scholarly_sources/ocr/svf_chrysippus/svf_ii_tei.xml l. 3189: 'per quam necesse sit fieri, quicquid futurum est'.`
- **ocr_correction_2026_08_16** — `set`
  - before: `<absent>`
  - after:  `true`

### `scholar_guyomarc_h_g`

- **verified_reference** — `set_if`
  - before: `Gweltaz Guyomarc'h, work on Alexander of Aphrodisias' De fato ('La causalité humaine. Sur le De fato d'Alexandre d'Aphrodise'); Guyomarc'h is MCF at Université Jean Moulin Lyon 3, specialist of Aristotle/Alexander.`
  - after:  `Gweltaz Guyomarc'h, MCF at Université Jean Moulin Lyon 3, specialist of Aristotle and Alexander of Aphrodisias (Wikidata Q110853446). He is NOT the author of 'La causalité humaine. Sur le De fato d'Alexandre d'Aphrodise' — that volume is by Isabelle Koch (Classiques Garnier 2019) and cites Guyomarc'h 2015 in its own footnotes. His 2015 book is 'L'unité de la métaphysique selon Alexandre d'Aphrodise' (Vrin), which is not held locally and has no node in this graph.`
- **citation_verdict** — `set_if`
  - before: `verified`
  - after:  `corrected`
- **verification_notes** — `note`
  - before: _(none)_
  - after:  `[Vérif. 2026-08-16] verified_reference attributed Isabelle Koch's 2019 Classiques Garnier volume to Guyomarc'h and was flagged citation_verdict='verified'. Corrected; verdict downgraded to 'corrected'. Evidence: the volume cites 'Guyomarc'h, 2015' in the third person in its own footnotes (local .md, ll. 648-649, 917, 1039, 1082, 1489).`

### `pub_sytsma_2020_universal_salvation_origen`

- **source_rank** — `set`
  - before: `<absent>`
  - after:  `PhD dissertation — Marquette University, May 2018, no. 769 (this is the copy actually held and collated); the 2020 Gorgias Press monograph is bibliographically attested (ISBN/DOI checked) but no copy was collated [unverified as monograph]`
- **synthesis_disclosure_required** — `set`
  - before: `<absent>`
  - after:  `Any synthesis citing this node must disclose that the verifiable object behind it is the 2018 Marquette dissertation, not the claimed 2020 monograph; page references taken from the local PDF are dissertation pages.`
- **verification_notes** — `note`
  - before: _(none)_
  - after:  `[Vérif. 2026-08-16] the dissertation-vs-monograph caveat already existed in the description and in metadata.phd_version / metadata.isbn_doi_note, but only as prose. Copied into the machine-readable metadata.source_rank field established by this pass. No bibliographic value changed.`

### `scholarly_work_bonaiuti_1924_the_genesis_of_st_augustine_s_idea_of_or`

- **author** — `set`
  - before: `<absent>`
  - after:  `Ernesto Bonaiuti`
- **journal** — `set`
  - before: `<absent>`
  - after:  `Harvard Theological Review`
- **publisher** — `delete`
  - before: `Harvard Theological Review`
  - after:  `<removed>`
- **volume** — `set`
  - before: `<absent>`
  - after:  `10`
- **number** — `set`
  - before: `<absent>`
  - after:  `2`
- **pages** — `set`
  - before: `<absent>`
  - after:  `159-175`
- **id_year_discrepancy** — `set`
  - before: `<absent>`
  - after:  `id slug and bibtex_key encode 1924; the article is Harvard Theological Review 10.2 (1917) 159-175, trans. Giorgio La Piana. Both kept for referential stability (edges and the exported .bib key resolve through them) — cite the label/year, never the slug.`
- **verification_notes** — `note`
  - before: _(none)_
  - after:  `[Vérif. 2026-08-16] label and metadata.year already read 1917; only the id slug and bibtex_key still say 1924, and metadata carried no 'author', so the exported BibTeX entry was authorless (flagged in data/kg/publications_bibtex_report.json). Added author/journal/volume/number from the node's own verified_reference (local source file: 06_Patristique/genesis_of_st_augustines_idea_of_original_sin.md). Id and bibtex_key deliberately unchanged.`

### `scholarly_work_guyomarc_h_2015_la_causalit_humaine_sur_le_de_fato_d_ale`

- **verification_notes** — `note`
  - before: _(none)_
  - after:  `[Vérif. 2026-08-16] id/node_id slug still encodes the superseded attribution 'guyomarc_h_2015'. The volume is by Isabelle Koch (Classiques Garnier 2019) — established from local evidence alone: the work cites 'Guyomarc'h, 2015' in its own footnotes in the third person (La_Causalite_humaine_Sur_le_De_fato_dAle.md ll. 648-649, 917, 1039, 1082, 1489); biblio_overrides.json records the file with authors: null; Koch is separately attested locally on the same topic (Le Destin, Vrin 2011). Guyomarc'h's own 2015 book is a different title (L'unité de la métaphysique selon Alexandre d'Aphrodise, Vrin) and has no node. The id is DELIBERATELY NOT RENAMED: edges and the seven scholarly_argument_guyomarc_h_* nodes resolve through it.`
- **id_attribution_note** — `set`
  - before: `<absent>`
  - after:  `id slug says 'guyomarc_h_2015'; the verified attribution is Isabelle Koch, 2019, Classiques Garnier. id kept for referential stability — cite the label/verified_reference, never the slug.`
- **attribution_conflict_resolved** — `set`
  - before: `<absent>`
  - after:  `2026-08-16`

### `scholarly_work_moon_2016_a_history_of_interpretation_of_romans_in`

- **source_rank** — `set`
  - before: `<absent>`
  - after:  `MA thesis — University of British Columbia (Classical, Near Eastern and Religious Studies), December 2016; not peer-reviewed`
- **synthesis_disclosure_required** — `set`
  - before: `<absent>`
  - after:  `Any synthesis citing this node must disclose that it is an unpublished master's thesis, not a peer-reviewed publication.`
- **author** — `set`
  - before: `<absent>`
  - after:  `John Moon`
- **verification_notes** — `note`
  - before: _(none)_
  - after:  `[Vérif. 2026-08-16] the MA-thesis caveat was present only inside the prose of metadata.verified_reference ('MA thesis …, The University of British Columbia, Vancouver, December 2016, 115 pp.'). Copied into the machine-readable metadata.source_rank field established by this pass.`

### `scholarly_work_nagasawa_2013_human_free_will_and_god_s_grace_in_the_e`

- **description (span)** — `span`
  - before: `Human Free Will and God's Grace in the Early Church Fathers`
  - after:  `Mako A. Nagasawa, 'Human Free Will and God's Grace in the Early Church Fathers' (New Humanity Institute, 2013). A patristic survey arguing that the early Fathers — Justin (1 Apol. 43-44, against heimarmene: if all happens by fate, praise and blame are unjust), Irenaeus, Origen, and others — held human self-determination together with divine grace. SOURCE RANK: online essay, not peer-reviewed, no publisher, no DOI, no page range (see metadata.source_rank). Usable for orientation; not an authority for a contested claim.`
- **source_rank** — `set`
  - before: `<absent>`
  - after:  `online essay — not peer-reviewed [unverified]`
- **synthesis_disclosure_required** — `set`
  - before: `<absent>`
  - after:  `Any synthesis citing this node must disclose its rank: it is a New Humanity Institute web essay, with no publisher, no DOI, no page range and no peer review. It may be used for orientation, never as the authority for a contested claim.`
- **author** — `set`
  - before: `<absent>`
  - after:  `Mako A. Nagasawa`
- **citation_verdict** — `set_if`
  - before: `verified`
  - after:  `corrected`
- **verification_notes** — `note`
  - before: _(none)_
  - after:  `[Vérif. 2026-08-16] node was flagged citation_verdict='verified' with metadata.type='article' while its own verified_reference identifies it as a New Humanity Institute web essay with no publisher, no DOI and no page range. Rank recorded in the new machine-readable field metadata.source_rank; verdict downgraded to 'corrected'. The node is kept — the essay is real and locally held (06_Patristique/Mako-Nagasawa-free-will-in-patristics.md) — but it is grey literature.`

### `scholarly_work_sorabji_2017_freedom_and_will_graeco_roman_origins`

- **description (span)** — `span`
  - before: `Freedom and Will: Graeco-Roman Origins`
  - after:  `Richard Sorabji, 'Freedom and Will: Graeco-Roman Origins', ch. 3 (pp. 49-66) in R. Seaford, J. Wilkins and M. Wright (eds.), *Selfhood and the Soul: Essays on Ancient Thought and Literature in Honour of Christopher Gill*, Oxford: Oxford University Press, 2017. Section 3 ('WILL: FOUR CHARACTERISTICS') distinguishes the four strands that make up the ancient idea of the will — rationality, freedom, will power, and will perverted by pride — each found separately in earlier thinkers and assembled only in Augustine; Sorabji credits the underlying point to Charles Kahn (1988) and to his own *Emotion and Peace of Mind* (2000) ch. 21. Against Frede 2011 he argues that none of the four strands is present in Epictetus. Verified 2026-08-16 against the local copy of the volume (filed under the editors, not under Sorabji).`
- **author** — `set`
  - before: `<absent>`
  - after:  `Richard Sorabji`
- **booktitle** — `set`
  - before: `<absent>`
  - after:  `Selfhood and the Soul: Essays on Ancient Thought and Literature in Honour of Christopher Gill`
- **editor** — `set`
  - before: `<absent>`
  - after:  `Richard Seaford, John Wilkins and Matthew Wright`
- **pages** — `set`
  - before: `<absent>`
  - after:  `49-66`
- **reference_status** — `set`
  - before: `<absent>`
  - after:  `verified 2026-08-16 — chapter located and collated in the local library; title, chapter number, page range, editors, publisher and ISBN all match the source file`
- **source_rank** — `set`
  - before: `<absent>`
  - after:  `peer-reviewed volume chapter — Oxford University Press Festschrift, 2017`
- **four_strands_provenance** — `set`
  - before: `<absent>`
  - after:  `The four strands (rationality, freedom, will power, will perverted by pride, assembled only in Augustine) are set out in §3 'WILL: FOUR CHARACTERISTICS'. Sorabji credits the underlying 'different strands' point to Charles Kahn (1988) and to his own Emotion and Peace of Mind (2000) ch. 21 — the thesis is restated in 2017, not first stated.`
- **homonym_warning** — `set`
  - before: `<absent>`
  - after:  `A SECOND, DISTINCT Sorabji 2017 exists: 'A Neglected Strategy of the Aristotelian Alexander on Necessity and Responsibility', in V. Harte and R. Woolf (eds.), Rereading Ancient Philosophy (Cambridge). That is where Sorabji defends Alexander against Frede. It is NOT held locally and must not be conflated with this chapter.`
- **verification_notes** — `note`
  - before: _(none)_
  - after:  `[Vérif. 2026-08-16] The audit brief classed this node as an unresolvable title-only shell and asked for reference_status='unverified'. That was refuted: the chapter is held locally (filed under the editors Seaford/Wilkins/Wright, which defeats a filename search on 'sorabji'), and the node's title, chapter, pages 49-66, editors, publisher and ISBN all check out against it. The 'unverified' marking was therefore NOT applied; the description was expanded from the title alone, and author/booktitle/editor/pages were added so the exported BibTeX entry stops being an authorless @incollection.`

### `passage_aug_civ_21_12`

- **description** — `set`
  - before: `<absent/empty>`
  - after:  `Augustine, *De ciuitate Dei* XXI.12 — the *massa damnata* chapter. Augustine argues that the greater the good Adam enjoyed, the greater the impiety of abandoning God, and that from that first transgression the whole human race becomes a condemned mass (*uniuersa generis humani massa damnata*), from which no one is delivered except by merciful and undeserved grace — so that in some God shows what mercy can do and in the rest what just retribution is. The locus is one of the two anchors (with *Enchiridion* 99) of the mature Augustinian position that the will's freedom after the fall is freedom only to sin. ⏎  ⏎ LOCUS ONLY — TEXT NOT YET COLLATED. No critical edition of *De ciuitate Dei* is held in the local library (survey 2026-08-16: CCSL 47-48 Dombart–Kalb and CSEL 40 Hoffmann are both absent; the Brepols LLT harvest under 02_Corpus/ carries no Augustinus directory; there is no PHI Latin […]`
- **verification_notes** — `note`
  - before: _(none)_
  - after:  `[Vérif. 2026-08-16] metadata.source read 'Dombart-Kalb (CCSL 47-48 basis)' and metadata.note read 'verbatim excerpt'. Both overstate the provenance: no critical De ciuitate Dei exists in the local library (LLT_brepols has no Augustinus directory; no CCSL/CSEL/PHI on disk), and the audit trail at data/audit/primary_wave/description_patches.json records the evidence actually used as thelatinlibrary.com/augustine/civ21.shtml, which carries no apparatus. The Latin in text_content is left untouched (it is a genuine excerpt, not a fabrication) but is re-described as partial and uncollated, and the node is put under the needs_text_ingestion convention.`
- **source** — `set_if`
  - before: `Dombart-Kalb (CCSL 47-48 basis)`
  - after:  `thelatinlibrary.com/augustine/civ21.shtml (no apparatus, uncollated) — target critical edition: CCSL 48, Dombart–Kalb, 1955`
- **note** — `set_if`
  - before: `verbatim excerpt`
  - after:  `partial verbatim excerpt — begins and ends mid-sentence, no chapter boundary; provenance uncollated (see verification_notes)`
- **needs_text_ingestion** — `set`
  - before: `<absent>`
  - after:  `true`
- **ingestion_blocked_reason** — `set`
  - before: `<absent>`
  - after:  `No critical edition of De ciuitate Dei is held locally (survey 2026-08-16: CCSL 47-48 Dombart–Kalb absent, CSEL 40 Hoffmann absent, no PHI Latin corpus on disk, Brepols LLT harvest carries no Augustinus author directory). The stored text is a partial non-critical excerpt from thelatinlibrary.com. Unblocking requires CCSL 48 pp. 778-779 (Dombart–Kalb 1955) or CSEL 40/2 (Hoffmann).`
- **text_excerpt_partial** — `set`
  - before: `<absent>`
  - after:  `true`
- **canonical_ref** — `set`
  - before: `<absent>`
  - after:  `De ciu. Dei XXI.12`

## Mandated but not applied

### Frede node: record 'fundamentally flawed' (pp. 177-178) as Frede's verified wording

**SKIPPED — the phrase is not Frede's**

Local extraction 04_Littérature_secondaire/01_Philosophie_antique/Frede_2011_Free_Will.txt: 'fundamentally' occurs exactly once in the whole book (l. 166), in A. A. Long's editorial foreword, about Frede's prose style. Frede's adjective is 'basically', four times, and the pp. 177-178 sentence predicates it of the OTHER authors: '…notions of a free will which … do not seem to be basically flawed in the way a notion like Alexander's is'. The corrected wording was written to the node instead.

### Sorabji 2017: set metadata.reference_status='unverified — title-only shell; four-strands thesis authentic to Sorabji but this 2017 citation could not be confirmed'

**SKIPPED — the citation was confirmed locally**

The chapter is held locally as ch. 3, pp. 49-66 of Seaford/Wilkins/Wright (eds.), Selfhood and the Soul (OUP 2017) — the file is catalogued under the editors, which is why a filename search on 'sorabji' misses it. Title, chapter number, page range, editors, publisher and ISBN all match the node. reference_status was set to 'verified 2026-08-16' instead, and the description was expanded from the bare title.

### Alexander De fato 19: 'ἐπὶ τίσιν οὐν αἱ κολάσεις' vs TLG 'οὖν'

**OBSERVED, NOT APPLIED — outside the audited item list**

Noticed while verifying the Phalaris sentence. TLG0732 reads 'ἐπὶ τίσιν οὖν αἱ κολάσεις εὔλογοι'. Recorded in the node's verification_notes for a later item-by-item pass rather than fixed in this one.

### data/corpus/passages.jsonl carries the same 'futurumfiturum' defect

**OBSERVED, NOT APPLIED — outside the declared file scope**

The Gellius NA VII.2.5 record in data/corpus/passages.jsonl (and the Perseus audit cache it came from) still reads 'quicquid futurumfiturum est'. This pass was scoped to data/kg/nodes.jsonl + publications.bib; the corpus copy needs the same correction in a corpus-scoped pass.

### data/kg/edges.jsonl carries 12 U+02BC occurrences

**OBSERVED, NOT APPLIED — outside the declared file scope**

All 12 are 'ἐφʼ ἡμῖν' inside edge metadata notes. The pass was authorised to touch edges only for id retargeting, and no id was renamed, so edges were left byte-identical.

