# Irenaeus free-will evidence audit - 2026-08-24

Status: **independent read-only audit**. No `data/kg`, `data/corpus`, registry, or
runtime file was changed by this task.

Post-audit implementation note: the subsequent atomic repair is recorded in
`data/audit/2026-08-24_irenaeus_primary_evidence_repair.json`. During the final
visual re-collation, Greek fragment 21 proved to be discontinuous: SC 100
assigns lines 1-19 to IV.37.2 (printed pp. 922-928) and lines 20-29 to IV.37.4
(pp. 928-930). The repair therefore stores them as two passage units sharing
fragment number 21; it does not concatenate them. The four false twins described
below are now historical/quarantined rather than active data. The broader issue
remains open for Armenian/Syriac witnesses, modern translation, IV.37.3-7,
IV.38-39 and premise-level secondary grounding.

## Executive verdict

The current Irenaeus primary-evidence slice is not publishable. All four
Irenaeus passage nodes are editorial summaries or machine-generated prose, yet
all four are still classified `citable` by `evidence_policy()` and each has a
`snapshot_passage_node` citation. Two of them can be independently re-fetched
as if they were primary text because their corpus twins default to
`passage_role=original` during deployment.

Confirmed P0 findings:

1. `passage_irenaeus_ah_3_20` is English editorial prose containing modern
   Greek retroversions. AH III.20.3 is transmitted here through the ancient
   Latin version; the continuous Greek printed by SC 211 is an editorial
   retroversion, not a surviving Greek witness.
2. `passage_irenaeus_ah_4_37` mixes English commentary, short transmitted Greek
   fragments, modern translation, and metadata. It conflates IV.37.1 with
   material transmitted for IV.37.2.
3. `_en` nodes are respectively a byte-identical non-translation and an AI
   paraphrase. Neither is a citable translation.
4. The same work-level URI `urn:cts:greekLit:tlg1447.tlg003` is attached to
   III.20 and IV.37 in both language cohorts. It identifies neither passage.
5. Only `work_irenaeus_adversus_haereses_book3_grc` has a corpus manifest, and
   that manifest has no source, source hash, version/locus URI, or rights
   provenance. The three other work IDs used by corpus rows have no manifest.
6. Ten downstream citation rows rely on the four false twins, including claims
   about `autexousion`, `eph' hemin`, recapitulation, and the praise/blame
   argument.

Existing audits had already detected parts of this debt:
`2026-08-16_deep_audit_linguistic.jsonl` flags the Greek-language mismatch, and
`2026-08-16_deep_audit_bibliographic.jsonl` flags the non-unique CTS URI. The
defects were not closed at runtime.

## Transmission strata - do not merge

| Stratum | Actual status | Citable rule |
|---|---|---|
| Greek original | Lost as a continuous work; exact fragments survive through later Greek authors and catenae | Citable only as an explicitly delimited indirect fragment with transmitting witness and fragment number |
| Ancient Latin | Complete ancient translation; its date is uncertain (possibly third century or around the end of the fourth), not securely “late second century” | Citable as `translation`, language `lat`, with the critical Latin manifestation |
| Armenian | Complete ancient Armenian version of Books IV-V | Separate `translation` manifestation; never label it Greek or Latin |
| Syriac | Fragments/quotations, not a complete Syriac work | Separate fragment manifestations only where the exact locus is demonstrated |
| Greek retroversion | Editorial reconstruction from Latin, Armenian and fragments in SC | `editorial_reconstruction`, discovery-only; never `original` and never a snapshot twin |
| French/English translation | Modern published translation | Separate published-human translation with edition/translator provenance |
| Editorial notice | Modern summary, thematic dossier, Markdown commentary | Discovery-only, no `snapshot_passage_node` |
| Machine prose | AI paraphrase or translation | Blocked/quarantined; never publication evidence |

External controls agree on this stratification. The official Cerf description
of [SC 100](https://www.editionsducerf.fr/librairie/sc-100-contre-les-heresies-livre-iv-1/)
states that it presents the Latin and Armenian versions plus a Greek
retroversion. A detailed scholarly review describes the separate Latin,
Armenian, Greek-fragment and Syriac traditions
([Persée](https://www.persee.fr/doc/antiq_0770-2817_1966_num_35_1_1477_t1_0303_0000_1)).
The date of the Latin translation remains uncertain
([Oxford Academic](https://academic.oup.com/book/12425/chapter/162891141)).
The Armenian manuscript contains Books IV-V
([CCEL introduction](https://ccel.org/ccel/irenaeus/demonstr.iii.i.html)).

## Exact node/passage/manifest/citation matrix

| KG node | Corpus UUID / work ID | Manifest | Citation rows | Actual content | Risk / action |
|---|---|---|---|---|---|
| `passage_irenaeus_ah_3_20` | `02ba0ce3-5810-5bed-860d-5f45de51f4f2`; `work_irenaeus_adversus_haereses_book3_grc` | Present but empty/thin (`book3_grc`) | snapshot; `argument_irenaeus_recapitulation_theodicy:grounded_in` | English editorial summary; unattested continuous Greek phrases; inaccurate Latin paraphrase | **P0 quarantine** node, passage and snapshot. Replace with exact SC 211 Latin III.20.3. Rewire argument only after claim-level audit. |
| `passage_irenaeus_ah_3_20_en` | `e565acd2-c206-5491-bca7-7f85d964b702`; `book3_eng` | Missing | snapshot | Byte-identical duplicate of the summary; metadata admits no translation was produced | **P0 quarantine/delete** node, passage and snapshot. Do not migrate as translation. |
| `passage_irenaeus_ah_4_37` | `4b7e7f9b-c7ef-5c62-b62f-6be046bdaffa`; `book4_grc` | Missing | snapshot plus seven `discussion/evidenced_by` dependents | English editorial dossier mixing IV.37.1 Latin concepts with Greek fragment 21 from IV.37.2 | **P0 quarantine**. Split by language, paragraph and witness. Rewire praise/blame and `autexousion` claims to IV.37.2, not IV.37.1. |
| `passage_irenaeus_ah_4_37_en` | `00164aae-dd76-5d71-b526-b530fd715fa3`; `book4_eng` | Missing | snapshot | AI English paraphrase, not a translation of any ingested original | **P0 quarantine/delete** node, passage and snapshot. Replace only with reviewed published translation. |

All four currently return `CitabilityTier.CITABLE`.

### Downstream rows that must be adjudicated atomically

| False passage UUID | Dependent KG node | Current relation | Required destination |
|---|---|---|---|
| `02ba...f4f2` | `passage_irenaeus_ah_3_20` | snapshot | New exact Latin III.20.3 node |
| `02ba...f4f2` | `argument_irenaeus_recapitulation_theodicy` | grounded_in | Latin III.20.3, but only for the exact incapacity propositions; reconstructed free-will/salvation synthesis remains secondary |
| `e565...b702` | `passage_irenaeus_ah_3_20_en` | snapshot | Quarantine; no replacement until a published translation is ingested |
| `4b7e...affa` | `passage_irenaeus_ah_4_37` | snapshot | Remove; create separate exact nodes |
| `4b7e...affa` | `argument_irenaeus_adv_haer_iv_37_praise_blame_transposed` | evidenced_by | Greek fragment 21 and/or Latin IV.37.2 |
| `4b7e...affa` | `argument_furst_2022_irenaeus_against_gnostic_natures` | discussion | Latin IV.37.6 plus reviewed Fürst p. 180 secondary page |
| `4b7e...affa` | `concept_autexousion_christian_freedom_u1v2w3x4` | discusses + evidenced_by | Greek fragment 21, IV.37.2 |
| `4b7e...affa` | `concept_eph_hemin_in_our_power_aristotle_d4e5f6g7` | evidenced_by | Greek fragment 21 only if the exact `eph' hemin` clause is retained |
| `0016...5fa3` | `passage_irenaeus_ah_4_37_en` | snapshot | Quarantine; reviewed human translation only |

## What SC 100 and SC 211 actually show

Visual inspection was performed on the local PDFs.

- SC 211, physical PDF page 196 / printed pp. 392-393, prints AH III.20.3:
  ancient Latin on the left, French translation above right, and editorial
  Greek retroversion below right. The exact Latin begins at line 76. The KG's
  “those who could not save themselves” Greek is not a transmitted witness.
- SC 100, physical PDF page 460 / printed pp. 920-921, prints IV.37.1 Latin and
  French. Greek fragment 20 from John of Damascus is separately labelled and
  consists of the short non-coercion sentence.
- SC 100, physical PDF page 461 / printed pp. 922-923, begins IV.37.2 and
  separately labels Greek fragment 21. The praise/blame argument and the
  `eph' hemin` / `autexousion` clauses belong to IV.37.2.
- SC 100 provides the wider free-agency sequence at printed pp. 918-940;
  IV.38.1 begins at printed p. 942 and IV.39.1 at p. 960. IV.29.1 (Pharaoh's
  hardening) begins at p. 764.

## Primary loci required for a complete free-will cohort

| Priority | Locus | Needed strata | Current coverage |
|---|---|---|---|
| P0 | AH III.20.3 | Latin SC 211; modern published translation; Greek retroversion stored only as editorial | False summary only |
| P0 | AH IV.37.1 | Latin; Armenian; Greek fragment 20; published translation | Mixed false twin |
| P0 | AH IV.37.2 | Latin; Armenian; Greek fragment 21; published translation | Mislabelled inside IV.37.1 dossier |
| P0 | AH IV.37.3-7 | Latin/Armenian; Greek fragments where individually attested | No exact passages |
| P0 | AH IV.38.1-4 | Latin/Armenian; transmitted Greek fragments; published translation | Concepts only (`nepios`, dynamic anthropology) |
| P0 | AH IV.39.1-4 | Latin/Armenian; Greek fragments; published translation | No exact passage; required for freedom, clay/potter and hardening claims |
| P1 | AH IV.29.1-2 | Latin/Armenian and any demonstrated fragments | Currado secondary argument only |
| P1 | AH I.6.1-4; I.7.5 | Latin plus surviving Greek where exact | Secondary descriptions of Valentinian “natures” only |
| P1 | AH II.14.4 | Latin and demonstrated fragments | Löhr/Grant discussion only |
| P1 | AH III.18-23 | Latin; exact Greek fragments only where extant | One false III.20 summary and recapitulation concepts |
| P1 | AH V.1-3; V.7.2; V.12.2-3; V.13.3; V.27-28 | Latin + Armenian + exact Greek/Syriac fragments | Fantino/Hick/Grant secondary claims only |
| P2 | Epideixis 11-14 | Armenian original-version witness; modern translation; Greek retroversion explicitly editorial | Duplicate work nodes and retroversion warnings, no exact cohort |

## Concept and internal-argument dependencies

| Node | Current risk | Repair rule |
|---|---|---|
| `argument_irenaeus_recapitulation_theodicy` | Direct premises cite a false summary; its moral-capacity vs salvific-capacity resolution is reconstructed | Split exact Latin propositions from modern synthesis; add secondary authorities to reconstructed premises |
| `argument_irenaeus_adv_haer_iv_37_praise_blame_transposed` | Sound secondary hypothesis, wrong mixed primary target | Ground in IV.37.2 Latin + Greek fragment 21 and Amand/Löhr pages |
| `argument_irenaeuss_antignostic_argument_for_free_will_f54fe920` | `unsupported - pending manual review`; many reconstructed premises | Retain discovery-only until each premise receives exact IV.37-39/V evidence or a secondary page |
| `synthesis_amand1945_irenaeus_transposed_topos` | Depends on the mixed IV.37 false twin | Reground through Amand pp. 222-223 + exact IV.37.2 witnesses |
| `concept_nepios_adam_infant_doctrine` | Greek clause appears genuine, but no exact passage node | Ingest the specific transmitted IV.38.1 Greek fragment with witness provenance |
| `concept_agathos_vs_teleios_distinction` | Strong interpretive generalization, `unsupported` | Ground exact IV.38-39 language; keep interpretive expansion secondary |
| `concept_dynamic_anthropology_temporal` | Modern ontological synthesis, `unsupported` | Secondary-only claim; Blackwell/Fantino/Meijering pages required |
| `concept_anakephalaiosis_recapitulation` | `unsupported`; broad III.18-23/V.21 synthesis | Exact Latin loci plus modern secondary support |
| `concept_autexousion_christian_freedom_u1v2w3x4` | Irenaeus dependency points to mixed false twin | Rewire only to Greek fragment 21 / Latin IV.37.2 |
| `concept_eph_hemin_in_our_power_aristotle_d4e5f6g7` | Broad concept is valid, Irenaeus citation is not | Remove false Irenaeus citation; optional exact fragment 21 link |

## Work and person records

| Node | Current state | Required action |
|---|---|---|
| `person_irenaeus_d202` | Bibliographically useful, but its prose treats “AH IV.37” as one undifferentiated Greek/Latin source | Retain; replace passage links with transmission-specific exact loci |
| `work_irenaeus_adversus_haereses_book2` | No corpus manifestation; relevant through II.14.4 | Add reviewed Latin/fragment manifestation only when ingested |
| `work_irenaeus_adversus_haereses_book3` | One false summary cohort; `needs_edition_metadata=true` | Link SC 210/211 Latin manifestation and exact III loci |
| `work_irenaeus_adversus_haereses_book4` | Rich interpretive description, no corpus manifest; continuous reconstructed Greek can be mistaken for original | Add Latin/Armenian/fragment manifests and make reconstruction explicitly editorial |
| `work_irenaeus_adversus_haereses_book5` | No corpus manifestation; several secondary claims depend on it | Add Latin/Armenian/fragment manifests before citing V loci |
| `work_irenaeus_demonstratio_apostolic` | Armenian-preserved work; metadata itself warns that Greek formulations are retroversions | Keep discovery-only until an Armenian manifestation and reviewed translation exist |
| `work_irenaeus_epideixis` | Duplicate intellectual-work family for the Demonstration | Resolve/merge identity without deleting provenance; do not attach retroverted Greek as original |

## Secondary-node inventory

Risk codes: `S` strong page evidence located; `R` relevant but requires narrow
page extraction/review; `M` misframed or wrong edition/locus; `D` derivative
modern reception; `U` unsupported internal synthesis.

| Node | Evidence status | Risk/action |
|---|---|---|
| `argument_furst_2022_irenaeus_against_gnostic_natures` | Exact quote verified at Fürst printed p. 180 / physical PDF p. 195 | **S**; link to `pub_furst_2022_wege_freiheit`, ingest reviewed page 180; primary locus is IV.37.6, not current mixed IV.37.1 |
| `scholarly_argument_l_hr_irenaeus_s_anti_determinist_ar_1` | Exact quote visually verified at Löhr p. 383 / physical PDF p. 3 | **S**; high-priority secondary anchor for IV.37.2 |
| `scholarly_argument_mueller_irenaeus_recapitulation_coordinates_choice_and_grace` | Printed pp. 210-217 / physical PDF pp. 34-41 located | **S/R**; ingest page-level claims individually |
| `argument_irenaeus_adv_haer_iv_37_praise_blame_transposed` | Amand pp. 222-223, local OCR; no quote field | **R**; collate Amand against exact IV.37.2 before verification |
| `scholarly_argument_blackwell_irenaeus_on_human_moral_progre_1` | Blackwell pp. 50-58 | **R**; relevant to IV.38-39, broad range must be split |
| `scholarly_argument_blackwell_methodology_history_of_interpr_2` | Blackwell pp. 14-24 | **R/P2**; methodological, not primary evidence for Irenaeus's free will |
| `scholarly_argument_fantino_free_will_and_the_psychike_spi_0` | Fantino pp. 418-429 | **R**; inspect exact pages/loci V.7, V.12-13 |
| `scholarly_argument_grant_irenaeus_against_gnostic_deter_1` | Grant pp. 8-15, 45-79 | **R**; overbroad, split heresiology from positive doctrine |
| `scholarly_argument_grant_irenaeus_on_free_will_and_mora_0` | Grant pp. 1-2 and translated selections 41-142 | **M/R**; translation selections are primary translation, not Grant's secondary argument |
| `scholarly_argument_grant_irenaeus_synthesis_of_biblical_3` | Exact introduction quote, p. 1 | **S**, but supports Grant's architectural metaphor, not a detailed agency claim |
| `scholarly_argument_grant_tradition_and_memory_as_founda_2` | Exact introduction quote, p. 1 | **S/P2**; tradition/memory, only indirectly related to free will |
| `scholarly_argument_currado_irenaeus_on_pharaoh_s_hardenin_3` | Exact p. 1 quote; local 15-page advocacy paper | **M/P2**; use only as a lead. Replace with SC 100 IV.29 and peer-reviewed commentary |
| `scholarly_argument_hick_free_will_and_moral_evil_0` | Hick pp. 243-280 | **D**; modern “Irenaean-type” theodicy, not evidence for Irenaeus without source comparison |
| `scholarly_argument_hick_the_fall_and_original_human_co_2` | Hick pp. 201-234 | **D**; same restriction |
| `scholarly_argument_rousseau_editorial_methodology_on_deter_3` | SC 263/264 apparatus | **M/P2**; editorial method, not philosophical conclusion |
| `scholarly_argument_rousseau_free_will_in_gnosticism_0` | AH I.6-7 text | **R**; ancient heresiological evidence, not a secondary Rousseau thesis |
| `scholarly_argument_rousseau_free_will_in_irenaeus_0` | SC 152/153 pp. 9-11 | **M**; record itself admits this is an edition, not an interpretive free-will claim |
| `scholarly_argument_rousseau_incompleteness_of_editorial_wo_1` | SC 152 introduction | **P3**; valid editorial observation, unrelated to the free-will KG core |
| `scholarly_argument_rousseau_irenaeus_s_own_position_on_fre_1` | Book I edition, positive doctrine actually in Book IV | **M**; rehome to exact IV.37-39 + secondary commentary |
| `scholarly_argument_rousseau_marcus_s_deterministic_numerol_2` | SC 264 I.14-16, corrected | **R/P2**; keep indirect astrology framing separate from human free will |
| `scholarly_argument_sagnard_free_will_and_moral_responsibi_0` | SC 34 Book III introduction, while cited doctrine is Book IV | **M**; do not attribute Book-IV doctrine to the Book-III edition without an exact Sagnard discussion |
| `argument_irenaeus_recapitulation_theodicy` | No secondary page evidence | **U/P0**; reconstructed synthesis, not direct ancient argument |
| `argument_irenaeuss_antignostic_argument_for_free_will_f54fe920` | Work-level citation only | **U/P0**; premise-level grounding required |
| `synthesis_amand1945_irenaeus_transposed_topos` | Amand-based synthesis | **R**; retain only after Amand + IV.37.2 collation |

Associated publication records present in KG:

- `scholarly_work_blackwell_2011_christosis_pauline_soteriology_in_light_`
- `scholarly_work_fantino_1998_le_passage_du_premier_adam_au_second_ada`
- `scholarly_work_grant_1996_irenaeus_of_lyons`
- `scholarly_work_rousseau_1965_ir_n_e_de_lyon_contre_les_h_r_sies_livre`
- `scholarly_work_rousseau_1969_ir_n_e_de_lyon_contre_les_h_r_sies_livre`
- `scholarly_work_rousseau_1979_ir_n_e_de_lyon_contre_les_h_r_sies_livre`
- `scholarly_work_rousseau_1982_ir_n_e_de_lyon_contre_les_h_r_sies_livre`
- `scholarly_work_sagnard_1952_ir_n_e_de_lyon_contre_les_h_r_sies_livre`

The Fürst, Löhr, Müller, Currado, Hick and Amand argument nodes reference other
publication families. Several arguments still lack a structured
`publication_id`, which prevents page-level GraphRAG verification.

## Local primary authorities and PDF priorities

No copyrighted page text should be committed. Register only locator, SHA,
rights/reuse, page mapping and reviewed text hash in the private secondary-page
store.

| Priority | Local artifact | SHA-256 / pages | Use |
|---|---|---|---|
| P0 | SC 100, AH IV (combined introduction + text/translation PDF) | `81b1204de818ad9c06891f354f3b1728007c36a2f49abe40d6f835b0db194917`, 503 pp. | Latin, Armenian apparatus, exact Greek fragments, retroversion and French translation; IV.37 physical 460-470 |
| P0 | SC 211, AH III text/translation | `1a0e4876113d65e70cc7282b84094fa731ebb7933c5860a0d1954abb08fa0b67`, 254 spreads | III.20.3 physical p. 196 / printed 392-393 |
| P0 | SCO/Brepols AH III Latin source | `2e404c862ffb19b9aa954bf5ad660b95584d273ec9d59ffe33a36714cba556fc` | Machine-readable exact Latin; research-only, outside git |
| P0 | SCO/Brepols AH IV Latin source | `33220a5e4d8033d42c2907e7f99f271c25d09fabb8797e06c62e203688e64359` | Exact Latin IV.29, 37-39 |
| P0 | SCO/Brepols AH IV Greek fragments | `7dc29c3512848ee1520a1cdff260d9a36f94c46e66eb3bb1b63e8af9e43b3dba` | Only transmitted Greek fragments; fragment/witness metadata is explicit |
| P0-negative | SCO/Brepols AH IV reconstructed Greek | `3f700bf62d85152d882bf4fd678f7db5430c4a9fc5e6e532c43735289551609c` | Negative control: editorial reconstruction, never primary evidence |
| P1 | Fürst, *Wege zur Freiheit* (2022) | `a4996520472881f9318f667873eb0b9dffa25168075cddc629b56c5d466e6fb9`, 351 pp. | Direct Irenaeus analysis pp. 172-180; p. 180 visually checked |
| P1 | Löhr, “Gnostic Determinism Reconsidered” (1992) | `7cce3e63b1c2caad497058124672b9687c102dbe991091e28c474ef2c80bd4ee`, 10 pp. | Direct IV.37.2 interpretation; p. 383 visually checked |
| P1 | Müller, “Freiheit. Über Autonomie und Gnade...” (1926) | `d8103b3f0354a0bce14031ddbf2ae4d3b84caca48bf4837ba507880906298189`, 60 pp. | Irenaeus printed pp. 210-217 / physical 34-41 |
| P2 | Grant, *Irenaeus of Lyons* (1996) | `0d673d849d73a7abc746332215907a81c9a646798d25692fb68f006ae81a9119`, 176 pp. | Broad secondary context and English selections |
| P2 | Blackwell, *Christosis* (2011) | `6ee96cf4dae4f6dfbd3bb6320bb5774b8f3cf67a356abda66bbb79b1a47512e6`, 332 pp. | Moral progression/deification, pp. 50-58 |
| P2 | Fantino (1998) | `868cbde84dc225f1c48efe8dad258c49185c3d7601bc0aa9936edbc11ae65689`, 14 pp. | AH V and psychical/spiritual development |
| P3/lead | Currado, *Early Church Fathers...Romans 9* | `423020e3d3cca128a22680c465e4b4233f205efd207a2be9bde8249d47302846`, 15 pp. | Lead for IV.29 only; polemical/non-critical source |
| Reception | Hick, full *Evil and the God of Love* | `68509c4b9bffe44c691f8db2dca0d91b19e76af22cda0506d763e43bed9eafd8`, 410 pp. | Modern Irenaean-type reception only |

Public-domain fallback: W. Wigan Harvey's 1857 edition is available via
[Internet Archive/Google Books](https://books.google.com/books/about/Adversus_Haereses.html?id=8IMOAAAAQAAJ)
and includes Greek, Latin, Syriac and Armenian fragments. It is useful for
independent control but must not silently replace SC readings.

Priority acquisition gaps:

1. E. P. Meijering, “Irenaeus' Relation to Philosophy in the Light of His
   Concept of Free Will,” *Romanitas et Christianitas* (1973), pp. 221-232;
   reprinted in *God Being History* (1975), pp. 19-30
   ([bibliographic control](https://ouci.dntb.gov.ua/en/works/4EJLvzBl/)).
2. A modern critical study of IV.37-39 and the Armenian evidence, not merely a
   general Irenaeus introduction.
3. A source-critical English translation with explicit base edition for Books
   III-V.
4. Exact Armenian/Syriac witness editions for any fragments actually used.

## Atomic repair plan

1. **Freeze inputs.** Record SHA-256 for nodes, edges, passages, citations,
   manifests and every local source artifact. Refuse concurrent drift.
2. **Pre-register manifestations.** At minimum: AH III Latin SC 211; AH IV
   Latin SC 100; AH IV Armenian SC 100; AH IV Greek fragments SC 100; any
   published French/English translation. Do not register reconstructed Greek as
   an original manifestation.
3. **Extract exact loci only.** Hash NFC-normalized text per paragraph and keep
   source page, printed page, language, transmission class and witness.
4. **Create language/witness-specific passage nodes.** Examples:
   `...iii_20_3_lat_sc211`, `...iv_37_1_lat_sc100`,
   `...iv_37_1_grc_frag20_joh_dam`, `...iv_37_2_lat_sc100`, and
   `...iv_37_2_grc_frag21_joh_dam`. Names are illustrative; the repair script
   must derive stable IDs from reviewed manifestation+locus keys.
5. **Quarantine the four current nodes, four passage rows and their snapshot
   citations.** Preserve the records verbatim in an audit JSONL. Do not recycle
   their UUIDs for different text.
6. **Rewire ten citation rows claim by claim.** IV.37.2 receives praise/blame,
   `eph' hemin` and `autexousion`; IV.37.1 receives the initial freedom and
   non-coercion argument; III.20.3 receives only exact incapacity propositions.
7. **Demote reconstructions.** Any retained editorial summaries or Greek
   retroversions receive explicit `citability=non_citable`, an editorial role,
   no corpus UUID and only `related_passage_non_exact` links.
8. **Replace work-level CTS misuse.** Keep canonical scholarly loci such as
   `Adv. haer. IV.37.2`. Mint no CTS passage URI until the real version inventory
   and citation scheme of TLG1447 is independently established.
9. **Write atomically.** One deterministic repair script, dry-run by default,
   temporary files + rename, quarantine/report artifacts, then an offline
   idempotent second pass.
10. **Publish only after all gates pass.** Any missing manifestation, hash,
    witness, page or review status remains `MISSING`/discovery-only.

## Required tests

- exact source-language/role matrix for Greek fragment, Latin, Armenian,
  Syriac fragment, retroversion, editorial notice and published translation;
- byte/hash parity between every exact KG node and its corpus passage;
- one-to-one exact snapshot citation bijection;
- no summary, reconstruction, untranslated duplicate or machine prose has an
  exact snapshot citation;
- III.20.3 continuous Greek is absent or explicitly editorial;
- IV.37.1 fragment 20 and IV.37.2 fragment 21 cannot be conflated;
- dependent praise/blame/autexousion citations resolve to IV.37.2;
- distinct complete manifests for every work/language ID used by a passage;
- no empty source/CTS fields presented as verified provenance;
- all old four UUIDs absent from active citations and present in quarantine;
- `evidence_policy` strips text from every retained editorial node;
- CitationVerifier returns `MISSING` for non-exact or machine evidence;
- staged deploy and bootstrap preserve language, role and source links;
- global no-orphan citation check, touched-cohort snapshot zero-debt check,
  dry-run/write/idempotence tests, and deterministic quarantine/report hashes.

## Final assessment

The authoritative materials needed for a high-quality repair are already
available locally. The blocker is not acquisition of AH III.20 or IV.37; it is
the absence of a transmission-aware data model in the current four records.
Until the atomic repair is applied, all four passage nodes and all citations
derived from their text should be treated as non-publishable.
