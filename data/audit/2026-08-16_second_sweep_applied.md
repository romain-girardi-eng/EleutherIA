# Second curation sweep — applied

**Date:** 2026-08-16 · **Predecessor:** `data/audit/2026-08-14_curation_artifact_cleanup_applied.md` (commit `be4c085`)
**Applied by:** `scripts/apply_2026_08_16_second_sweep.py` + `scripts/data_2026_08_16_second_sweep.py`
**Targets:** `data/kg/nodes.jsonl`, `data/kg/edges.jsonl`, `data/audit/greek_allowlist.json` (working tree, not committed)

The 2026-08-14 cleanup deliberately stayed inside the reader-facing fields and archived
every `[Vérif. …]` tag into `metadata.verification_notes`. Its review listed five piles of
follow-ups (§5.5, §6.1–6.6). This sweep closes them.

---

## 1. Counts

| item | scope | result |
|---|---|---|
| **1. metadata-field defects** | the ~100 nodes of §5.5 + the 16 tags of §6.2 whose defect lives in metadata | **54 nodes, 96 metadata operations** (38 from §5.5, 11 from §6.2, 9 from §6.6 — the tables overlap) |
| **2. truncated corrections** | the 44 nodes of §6.6 | **31 completed** (prose, `description_en`, label or metadata), **13 left as-is** — see §7 |
| **3. other curator-bracket shapes** | §6.5 said 8 nodes | **7 nodes, 8 brackets** merged-then-archived; the 8th match is a false positive — see §7 |
| **4. Alcinous mislabel** | §6.1 escalation | **1 node relabelled, 2 edges deleted** — see §5 |
| **5. Greek-gate allowlist** | §6.4 | **2 entries added**, gate green |

| operation | count |
|---|---|
| nodes touched | 84 |
| nodes created | 1 (`scholar_simonetti_m`) |
| authored prose spans applied | 22 (`description`) + 8 (`metadata.description_en`) |
| label rewrites | 2 |
| metadata operations applied | 96 (+ 11 on the Alcinous node = 107) |
| curator brackets moved to `metadata.verification_notes` | 8 |
| duplicate paragraph blocks removed | 4 (2 nodes) |
| edges deleted | 2 |
| edges retargeted | 1 |
| Greek allowlist entries added | 2 |
| spans skipped (`old` not unique) | 0 |
| planned nodes missing from `nodes.jsonl` | 0 |

Zero-fabrication: no ancient-language string was composed. Every Greek/Latin run that
entered a description is verbatim from that node's own `label`, `description` or
`metadata.verified_reference`, or from a named printed source quoted in the data
module's `#` comment. Three descriptions gained a short Greek phrase
(`ἀργὸς λόγος`, `γένεα αὐτεξούσια`, `Περὶ τοῦ ἐφ' ἡμῖν`), each already present elsewhere
on the same node.

## 2. Validation

| check | result |
|---|---|
| `nodes.jsonl` reparses, one JSON object per line | 19 992 lines, 0 parse failures |
| node count | 19 991 → 19 992 (+1 new scholar node) |
| duplicate node ids | 0 |
| `edges.jsonl` reparses | 57 374 → 57 372 (−2) |
| any edge endpoint missing from `nodes.jsonl` | 0 |
| `scripts/audit_structural.py` | TOTAL 2 321 before → **2 321 after**; `uncited_claim_node` 1381 = 1381, `cts_urn_format` 934 = 934, `duplicate_node_candidate` 6 = 6 — **0 new findings, 0 regressions** |
| `scripts/check_greek_gate.py` | **OK** (26 Greek runs in 16 changed nodes; the 2 pre-existing `tlg_only` failures are now allowlisted) |
| `scripts/check_citations_gate.py` | OK (208 verified references) |
| `scripts/check_kg_work_id_uniqueness.py` | WARN — only pre-existing allowlisted collisions (unchanged) |
| `python3 -m scripts.check_corpus_invariants` | citations = 19 893, passages = 21 088, 0 dangling |
| curator brackets remaining in `description` / `label` / `metadata.description_en` | **0** |
| curator brackets remaining anywhere outside `verification_notes` | 1, deliberate (see §7) |
| re-running the applier | no-op (84 nodes stamped `metadata.second_sweep_2026_08_16`) |

## 3. The new node

`scholar_simonetti_m` — **Manlio Simonetti**. Created only so that
`scholarly_argument_crouzel_manuscript_tradition_and_textu_1` could point its
`metadata.scholar_id` and its `created_by` edge at the right person: the tag records that
the manuscript-tradition section of SC 312 is Simonetti's, not Crouzel's, and named the
absence of a Simonetti node as "the outstanding step". The node carries only what the SC
312 Avant-Propos (quoted in the node's own `verified_reference`) supports; no dates,
affiliations or other works were invented.

Edge retargeted: `950a2601-bf64-4059-8530-b9ecda110622`
`scholarly_argument_crouzel_manuscript_tradition_and_textu_1 -created_by-> scholar_crouzel_henri`
→ `… -created_by-> scholar_simonetti_m`.

## 4. Re-verifications that unlocked a correction

| source consulted | what it settled |
|---|---|
| local .md of Destrée–Salles–Zingano, *What Is Up to Us?* (2014) — running heads and chapter openings extracted | The volume's contributions, in order with their opening pages: Johnson 7, Destrée 25, D. Frede 39, Bobzien 59, Meyer 75, Echeñique 91, Vogt 107, **Gómez 121**, Gourinat 141, Vimercati 151, Salles 169, Boeri 183, Zingano 199, Morel 221, Maso 235, **Gerson 251**, Taormina 265, **Bonazzi 283**, Horn 295, Steel 311, **Wildberg 329**, M. Frede 351. This confirms Wildberg's chapter exists and is the 21st (not the 18th), fixes Gómez's authorship and pages, and restores Bonazzi's page span. The numbering is corroborated by the node metadata already in the graph (Destrée "ch. 2, pp. 25-38"; Boeri "12th contribution, pp. 183-197"; Zingano "13th contribution, pp. 199-219"). |
| local OCR .md of Amand, *Fatalisme et liberté* (1945 / Hakkert 1973) | (a) p. 243 verbatim: «…que Bardesane est peut-être le premier à avoir mis en œuvre avec une telle profusion et une telle exactitude documentaire» — the quotation and page the 2026-08-14 pass had to drop. (b) «III. SA CONCEPTION PRAGMATISTE DE LA LIBERTÉ» stands under «CHAPITRE III», page marker 65 → the description's locus was right, the backfilled `amand_location` wrong. (c) Plato is section III of «CHAPITRE PREMIER», and the «Αἰτία ἑλομένου· θεὸς ἀναίτιος / ἀρετὴ ἀδέσποτον» passage sits under page marker 32 → the description's p. 31-33 was right, the metadata's p. 20-40 wrong. |
| printed Contents of Long & Sedley, *The Hellenistic Philosophers* vol. 1 (local PDF, pp. viii-ix) | LS **57** = "Impulse and appropriateness" (p. 346) and LS **65** = "The passions" (p. 410). The tag's doubt was unfounded; both section numbers, deleted on 2026-08-14, are restored with their titles and pages. |
| `data/corpus/manifest.jsonl` | Adversus Marcionem is ingested under `scaife:urn:cts:latinLit:stoa0275.stoa015.opp-lat1` (stoa007 being De Anima) → the stoa006-vs-stoa015 contradiction is adjudicated for **stoa015**, the value already in `metadata.canonical_id`. |
| `nodes.jsonl` id existence check | Every `passage_alex_fat_5xx` / `_6xx` id referenced in a `metadata.sources` array is absent from the graph, while `_11`, `_12`, `_16`, `_19`, `_26`, `_30` all exist — the basis for the three `sources` repairs. |
| `scripts/tlg_search.py` against local TLG E | The Alcinous payload (§5) and the two allowlisted Greek runs (§6). |

## 5. The Alcinous escalation — decision and evidence

**Node:** `passage_alcin_alcinous_untitled_full_text`
**Decision:** relabelled truthfully as the **Hegesippus fragment collection**; the two edges
asserting Alcinean authorship deleted; node kept (not deleted).

**Evidence.**

1. **Content.** `scripts/tlg_search.py` (local TLG E, accent-insensitive) on three phrases
   taken verbatim from the stored payload:
   - `ἀπεσκληκέναι τὰ γόνατα αὐτοῦ δίκην καμήλου` → 3 hits: **TLG1398** (Hegesippus),
     **TLG2018** (Eusebius, *HE* II.23 — James the Just), TLG3045 (Syncellus).
   - `ἦσαν δὲ γνῶμαι διάφοροι ἐν τῇ περιτομῇ` → 1 hit: **TLG2018** (Eusebius, *HE* IV.22 —
     the Jewish sects).
   - `Μακάριοι οἱ ὀφθαλμοὶ ὑμῶν οἱ βλέποντες` → 2 hits: **TLG1398** and TLG4040 (Photius,
     from Stephanus Gobarus).
   The payload also carries the martyrdom of Symeon son of Clopas under Trajan and the
   consular Atticus (= *HE* III.32). Only one text contains **all four** together: the
   Hegesippus fragment collection, TLG 1398. Nothing in it is Alcinous.
2. **The node's own history.** `data/audit/primary_wave/urn_fix_changelog.jsonl` records
   its original CTS URN as `urn:cts:greekLit:tlg1398:passage1` — **tlg1398 is Hegesippus**.
   The URN was cleared as a "fake placeholder" and the node was left filed under Alcinous.
3. **Root cause.** `data/corpus/manifest.jsonl` shows the ingest bug directly: the work row
   `urn_cts_greeklit_tlg0720_tlg001` ("Alcinous, Handbook of Platonism (Didaskalikos)",
   1 passage, `thin_needs_ingestion`) has `source: "scaife:urn:cts:greekLit:tlg1398"`.
   The Alcinous shelf was filled from the Hegesippus URN.
4. **Dependants.** Edges referencing the node: exactly 2, both structural
   (`-authored_by-> person_alcinous_2c_ce`, `-part_of-> work_didaskalikos_alcinous_2nd_ce_q7r8s9t0`).
   No argument, concept or synthesis cites it. `data/corpus/citations.jsonl` has exactly one
   row (`snapshot_passage_node` → passage `6c05b0e0-…`), which stays valid.

**Why relabel rather than delete.** No correct Alcinous passage node exists elsewhere, so
this is not a broken duplicate. Deleting it would orphan the `citations.jsonl` row and
raise a new `fk_orphan_citation` finding in `audit_structural.py` — a regression in a file
outside this sweep's targets. Relabelling loses nothing and destroys no text.

**Applied.**

- `label`: `Alcinous, Handbook of Platonism (Didaskalikos), Didasc. 1` → `Hegesippus, Hypomnemata (fragments ap. Eusebius, HE II.23 / III.32 / IV.22 and ap. Photius) — mis-ingested under Alcinous`
- `school`: `Middle Platonist` → `null`; `period` unchanged (`Roman Imperial`, correct for Hegesippus, fl. c. 165-175)
- `metadata.author`: `Alcinous` → `Hegesippus`; `metadata.school` → `null`
- `metadata.work_title`: `Handbook of Platonism (Didaskalikos)` → `Hypomnemata (fragments, ed. as TLG 1398)`
- `metadata.work_canonical_id`: `urn:cts:greekLit:tlg0720.tlg001` → `urn:cts:greekLit:tlg1398`
- `metadata.canonical_ref`: `Didasc. 1` → `null`
- `metadata.attestation_type`: `direct` → `fragment_collection`
- `metadata.doxographical_source` / `doxographical_confidence` (`heuristic` / `medium`) → `null`
- `metadata.cts_urn_note` rewritten; `metadata.mislabel_correction_2026_08_16` and
  `metadata.needs_evidence_note` added (the latter records that the stored text is a lossy
  beta-code extraction — `*̓ιάκωβος`, `τινε\ς`, dropped words — and must be re-ingested from
  a critical edition before any use)
- **Edges deleted (2):**
  - `75cb6e7d-eca1-4409-becd-4f7247ccaaef` — `passage_alcin_alcinous_untitled_full_text -authored_by-> person_alcinous_2c_ce`
  - `256726d2-1fdc-419b-bd7a-09cd1778428d` — `passage_alcin_alcinous_untitled_full_text -part_of-> work_didaskalikos_alcinous_2nd_ce_q7r8s9t0`

The node id keeps its legacy `alcin` prefix: `data/corpus/citations.jsonl` and the corpus
passage row reference it, and renaming ids is out of scope here.

**Not done (outside this sweep's targets):** `data/corpus/manifest.jsonl` still describes
the work row as Alcinous, and `data/corpus/passages.jsonl` still carries
`canonical_ref: "Didasc. 1"` / `work_canonical_id: urn_cts_greeklit_tlg0720_tlg001` on
passage `6c05b0e0-2af2-4d4f-ba3a-27bdf930d106`. Both need the same correction in a corpus
pass.

## 6. Greek gate

`scripts/check_greek_gate.py` reported two `tlg_only` runs — attested in TLG E, absent from
the ingested corpus, missing an allowlist entry. Both were re-confirmed with
`scripts/tlg_search.py` on 2026-08-16 before being allowlisted in
`data/audit/greek_allowlist.json`:

| node | run | hash | attestation |
|---|---|---|---|
| `concept_axia_biblos_tou_theou_origen_amand1945` | `τὰ σημεῖα τοῦ θεοῦ` | `076cbcdc1b8b6830` | **TLG2042 (Origen)**, 3 occurrences, e.g. «…ἀναγινώσκειν τὰ σημεῖα τοῦ θεοῦ» — Philocalia 23.20 = Comm. in Gen. III; cf. Amand 1945, pp. 315-316 |
| `concept_inner_freedom_alex` | `ἐνταῦθα λῃσταὶ καὶ κλέπται καὶ δικαστήρια καὶ οἱ καλούμενοι τύραννοι δοκοῦντες ἔχειν τινὰ ἐφ' ἡμῖν ἐξουσίαν διὰ τὸ σωμάτ…` | `bab1627d58b40847` | **TLG0557 (Epictetus)**, single hit, *Dissertationes* I.9 (the node cites I.9.12-17), ed. Schenkl (Teubner) |

Gate result after the sweep: `greek-gate: OK` (26 runs across the 16 changed nodes that
carry Greek).

The other follow-up of §6.4 is already closed: `scripts/tlg_search.py` line 20 now defaults
`TLGE` to `~/Desktop/Romain/TLGE`, so the gate's TLG fallback works without exporting
`TLGE_DIR`.

## 7. Not done, and why

**§6.6 — 13 of the 44 truncated corrections left as the conservative edit made them.**
In each case the tag truncates before the information needed, and no local source settles it;
inventing a replacement would violate the zero-fabrication rule.

| node | why not completed |
|---|---|
| `argument_origen_argos_logos` | The conservative edit already says what the tag says: *C. Cels.* II.20 is the foreknowledge/prophecy passage. The tag's further point (where the argos-logos refutation proper sits) is lost with the truncation, and `verified_reference` adds nothing beyond II.20. |
| `argument_skeptical_argument_from_divine_power_d217cdac` | The tag's object is the grounding of all ten premises to `work_bayle_rorarius_1702`. The prose already stops presenting 'Rorarius' as the locus; re-pointing the premises requires the correct Bayle article, which the tag truncates before giving. `verified_reference` names 'Pyrrhon' rem. B, but the premise-by-premise re-anchoring is an interpretive job, not a mechanical one. |
| `concept_frede_inner_life_late_stoic` | Tag truncated at 'Chapter numbers'; no correction to Frede's chapter/page loci is recoverable. |
| `concept_gnomic_will_gnome` | Tag truncated at 'The co…'; whether the dropped figure '28' is itself correct cannot be recovered. |
| `concept_orphic_zagreus_dionysus_myth` | Interpretive caveat, already hedged and attributed; tag truncated after 'Olympiodorus (6th c'. |
| `person_diogenes_babylon_240_152bce` | Tag truncated at 'The CHHP treats'; the correct *Cambridge History of Hellenistic Philosophy* locus is not recoverable and the volume is not in the local library. |
| `pub_belcastro_predestinazione_origene` | Only the genre error was recoverable; the rest of the objection is lost. |
| `scholar_stump_e` | Tag truncated at 'an intellectualist account without '; the missing qualifier cannot be recovered. |
| `scholarly_argument_bonaiuti_ambrosiaster_s_influence_on_au_1` | The date correction is already applied where it matters: the linked work node `scholarly_work_bonaiuti_1924_…` carries `year: 1917` and `page_range: 159-175`. Only the node **id** and `bibtex_key` still encode 1924; renaming ids would break edges and citations, so they are left with the discrepancy documented here. |
| `scholarly_argument_rousseau_irenaeus_s_own_position_on_fre_1` | Already qualified exactly as the tag's 'slightly overreaches' asks. |
| `scholarly_argument_wolfson_comparison_with_plato_s_timaeu_3` | Same as Bonaiuti: the linked work node `scholarly_work_wolfson_1947_…` already carries `year: 1942`, `page_range: 131-169`; only the id/bibtex_key are stale. The Timaeus loci correction applies to metadata absent from the description and the tag truncates on the second locus. |
| `work_methodius_de_libero_arbitrio` | Tag truncated before naming *De autexousio*'s actual adversaries; the wrong character was removed, none substituted. |
| `work_philo_de_providentia` | The correct Cohn–Wendland volume for the Greek fragments is not recoverable from the truncated tag; the reference stays hedged. |

**§6.5 — the "8th" curator bracket is a false positive.**
`argument_cafma_framework_5a7b9e12.attribution_review` matches a `[Vérif.` grep, but the
string there is a *mention* — "This node carried no [Vérif.] note but was flagged uncertain"
— not a tag. The field's first-person `RESOLVED 2026-08-03 (adjudication des 85 « incertains »…)`
stamp is a graph-wide convention on `attribution_review`, and metadata is allowed to carry
curator prose under the agreed policy. Left untouched; flag it if that field is ever surfaced
to readers.

**§6.2 items deliberately recorded rather than resolved.**

- `sc79_chrysostomus_de_providentia` — the node's SC/edition metadata (SC 79 = Malingrey,
  *Sur la providence de Dieu* = PG 52:479-528) and its description/ingested passages (the six
  *Discourses on Fate and Providence*, PG 50:749-774) describe **two different works**.
  Changing either field would silently pick a side. A `metadata.work_identity_conflict` note
  records the conflict; the corpus rows must be re-homed first.
- `work_salles_stoics_determinism_2008` — `year: 2005` and `publisher: Ashgate` added, but
  the node **id** still says `_2008`. `metadata.node_id_note` records it; edges and citations
  reference the id.
- `concept_death_therapeutic_remedy_methodius_5eaaf3a2` (§6.2) — no change: the metadata the
  tag flags ("ambiguous: 4 works", the Greek φάρμακον without a locus) is no longer present;
  `provenance_note` already gives *De resurrectione* I / Epiphanius, *Panarion* 64.
- `argument_lazy_argument_alex` label — the tag rejects the ἀργὸς λόγος conflation but gives
  no replacement name, so the new label states the argument's own content
  (consequences-for-motivation, *De Fato* 11) and marks the distinction, rather than inventing
  a scholarly title.

**Files not touched.** `data/corpus/passages.jsonl`, `data/corpus/manifest.jsonl` and
`data/corpus/citations.jsonl` are outside this sweep's declared targets; the Alcinous /
Hegesippus correction needs a matching corpus pass (§5).

## 8. Reproducing

```bash
python3 scripts/apply_2026_08_16_second_sweep.py --dry-run   # report only
python3 scripts/apply_2026_08_16_second_sweep.py             # write
python3 scripts/audit_structural.py
python3 scripts/check_greek_gate.py
python3 scripts/check_citations_gate.py
python3 -m scripts.check_corpus_invariants
```

Every edit lives in `scripts/data_2026_08_16_second_sweep.py`
(`METADATA_OPS` / `DESCRIPTION_REWRITES` / `DESCRIPTION_EN_REWRITES` / `LABEL_REWRITES` /
`BRACKET_NODES` / `DEDUPE_BLOCKS` / `NEW_NODES` / `EDGE_RETARGETS` / `ALCINOUS_*` /
`GREEK_ALLOWLIST_ADDITIONS`), one `#` comment per edit quoting the tag or the source that
justifies it. A span whose `old` text does not occur exactly once is reported and skipped,
never applied blind; a node stamped `metadata.second_sweep_2026_08_16` is skipped entirely
on re-runs.

---

## 9. Every content-changing edit, before → after

85 sections: the 84 nodes modified plus the 1 node created. Curator brackets moved into
`metadata.verification_notes` are shown verbatim so
that no provenance is lost from this record.

#### `argument_adversity_exercise_seneca_g8h9i0j1`

- **`metadata.legacy_premises`**
  - removed → `{"id": "P2", "text": "Virtue languishes without an opponent (marcet sine adversario virtus).", "attestation": "direct", "primary_sources": ["passage_sen_prov_2_3"], "secondary_sources": []}`
  - added → `{"id": "P2", "text": "Virtue languishes without an opponent (marcet sine adversario virtus).", "attestation": "direct", "primary_sources": ["passage_sen_prov_2_4"], "secondary_sources": []}`
- **`metadata.needs_evidence_note`**  
  before → `"<absent>"`  
  after → `"legacy_premises P2 ('Virtue languishes without an opponent') was re-anchored 2026-08-16 from passage_sen_prov_2_3 to passage_sen_prov_2_4, matching the 2.3→2.4 relocation of the maxim already applied to the prose. The other premises keep their own anchors: the tag flags only the maxim."`

#### `argument_anselms_necessity_of_the_past_f7947dab`

- **`metadata.verification_notes`** += curator bracket, moved verbatim out of the description:  
  `"[Vérifié 2026-08-02 : terminologie d’Anselme = necessitas praecedens/sequens (De concordia, q.I, cc.2-3), non antecedens/consequens.]"`

#### `argument_aquinass_intellectualism_f0058bf9`

- **`description`** span  
  before → Key texts: Summa Theologica I-II, q.1-5 (on happiness and voluntary action); De Veritate q.24, a.1-2 (on liberum arbitrium)  
  after → Key texts: Summa Theologica I-II, qq.1-5 (on the ultimate end and beatitude) and qq.6-17 (on the voluntary and on human action); the sharpest intellectualist texts are ST I, qq.82-83 and I-II, qq.9-10; De Veritate q.24, a.1-2 (on liberum arbitrium)
- **`metadata.verification_notes`** += curator bracket, moved verbatim out of the description:  
  `"[Correction 2026-08-02 : ST I-II qq.1-5 traitent de la fin ultime/béatitude ; l’action volontaire et humaine est aux qq.6-17. Les textes intellectualistes les plus nets : ST I q.82-83 et I-II q.9-10.]"`

#### `argument_bardesanes_nomima_barbarika_amplified`

- **`description`** span  
  before → Selon Amand, Bardesane serait l'un des premiers à mettre en œuvre l'argument carnéadien des nomima barbarika avec une profusion et une exactitude documentaires remarquables.  
  after → Selon Amand (1945, p. 243), on reconnaît là l'argument antiastrologique carnéadien tiré des *nomima barbarika*, « fondé cette fois sur une ample moisson de renseignements ethnographiques, que Bardesane est peut-être le premier à avoir mis en œuvre avec une telle profusion et une telle exactitude documentaire ».

#### `argument_cafma_futility_of_sanctions_0e5f7h43`

- **`metadata.ancient_sources`**
  - removed → `"Aulus Gellius, Noctes Atticae VII.2.1-15"`

#### `argument_civilization_alex`

- **`description`** duplicate paragraph blocks removed: 5 blocks → 3 blocks (1774 → 1015 chars); each dropped block was byte-identical to one kept earlier in the same field.
- **`metadata.verification_notes`** += curator bracket, moved verbatim out of the description:  
  `"[Greek removed: the original node attached two unverifiable Greek phrases to non-existent Bruns page references (Fat. 508-510); De Fato in Bruns runs only to p. 212. Restore verbatim Greek only from a checked edition with correct page/line citation.]"`

#### `argument_clement_grace_synergy_assent`

- **`description`** span  
  before → θεοσεβείας συγκατάθεσις, Strom. II)  
  after → θεοσεβείας συγκατάθεσις, Strom. II.2.8.3-4)

#### `argument_deliberation_complete_alex`

- **`metadata.needs_evidence_note`**  
  before → `"<absent>"`  
  after → `"metadata.sources previously listed passage_alex_fat_554-558, none of which exists in the graph; replaced 2026-08-16 by the loci the premises themselves cite (De Fato 11-12 = Bruns 178-180)."`
- **`metadata.sources`**
  - removed → `"passage_alex_fat_554"`
  - removed → `"passage_alex_fat_555"`
  - removed → `"passage_alex_fat_556"`
  - removed → `"passage_alex_fat_557"`
  - removed → `"passage_alex_fat_558"`
  - added → `"passage_alex_fat_11"`
  - added → `"passage_alex_fat_12"`

#### `argument_future_contingents_alex`

- **`metadata.key_passages`**  
  before → `["471-480"]`  
  after → `"<absent>"`
- **`metadata.needs_evidence_note`**  
  before → `"<absent>"`  
  after → `"metadata.key_passages ['471-480'] removed 2026-08-16: outside Bruns 164-212 and matching no De Fato citation scheme. The surviving locus is bruns_pages '200-201' (De Fato 30), which the tag confirms."`

#### `argument_gersonides_limited_omniscience_s9t0u1v2`

- **`description`** span  
  before → When Peter sins, God knows it. Omniscience is perfect knowledge of all knowables; but indeterminate futures aren't yet knowable.  
  after → God is not said to *learn* anything when Peter sins — ascribing acquired temporal knowledge to God contradicts Gersonides; God knows the particular only in so far as it is ordered by the general natural order. Omniscience is perfect knowledge of all knowables; but indeterminate futures aren't yet knowable.
- **`metadata.verification_notes`** += curator bracket, moved verbatim out of the description:  
  `"[Correction 2026-08-02 : ne pas dire que Dieu « apprend » quand Pierre pèche (savoir temporel acquis) — cela contredit Gersonide ; Dieu connaît le particulier seulement en tant qu’ordonné par l’ordre naturel général.]"`

#### `argument_gomez_2014_chrysippus_reactive_compatibilism`

- **`description`** span  
  before → , dont l'auteur du chapitre n'a pu être confirmé :   
  after →  — chapitre de Laura Liliana Gómez, « Chrysippean compatibilistic theory of fate, what is up to us, and moral responsibility » (8e contribution, p. 121-139) : 

#### `argument_human_constitution_alex`

- **`description`** duplicate paragraph blocks removed: 5 blocks → 3 blocks (1586 → 610 chars); each dropped block was byte-identical to one kept earlier in the same field.
- **`metadata.verification_notes`** += curator bracket, moved verbatim out of the description:  
  `"[Bruns page references to 'Fat. 498/499/500' removed as fabricated.]"`
- **`metadata.verification_notes`** += curator bracket, moved verbatim out of the description:  
  `"[The node previously embedded two further Greek phrases — glosses for 'our being human' and 'necessary for being' — anchored to Bruns references Fat. 498-500. These loci are impossible (De Fato in Bruns ends at p. 212) and the phrases are unattested in the corpus, in Sharples 1983, or in any catalogued Greek of De Fato; they are removed pending a checked edition.]"`

#### `argument_human_dignity_alex`

- **`metadata.needs_evidence_note`**  
  before → `"<absent>"`  
  after → `"metadata.sources previously listed passage_alex_fat_628/629/630/633/634/635/636 — none of these nodes exists in the graph and the Bruns loci Fat. 628-636 they encode are impossible (De Fato ends at Bruns 212). Removed 2026-08-16; the surviving grounding is passage_alex_fat_19, the locus every premise already cites."`
- **`metadata.sources`**
  - removed → `"passage_alex_fat_633"`
  - removed → `"passage_alex_fat_634"`
  - removed → `"passage_alex_fat_635"`
  - removed → `"passage_alex_fat_636"`
  - removed → `"passage_alex_fat_628"`
  - removed → `"passage_alex_fat_629"`
  - removed → `"passage_alex_fat_630"`
  - added → `"passage_alex_fat_19"`

#### `argument_lazy_argument_alex`

- **`label`**  
  before → `Lazy Argument (Argos Logos) in Alexander`  
  after → `Consequences-for-Motivation Argument (Alexander, De Fato 11 — not the argos logos)`
- **`description`** span  
  before → This is a PRAGMATIC argument: even if determinism were true, believing it would be catastrophic. The Stoics famously tried to answer this argument - Alexander thinks they failed.  
  after → This is a PRAGMATIC argument: even if determinism were true, believing it would be catastrophic. The Stoics famously tried to answer this argument - Alexander thinks they failed.

Terminological caveat: this is not the ἀργὸς λόγος ("Lazy Argument") proper. That is a fatalist sophism — if it is fated that you will recover, you will recover whether or not you call the doctor, so effort is idle — attested at Cicero, De fato 28-30 and Origen, Contra Celsum II.20, and answered by Chrysippus through co-fated events. What this node reconstructs is Alexander's deliberation-in-vain / consequences-for-motivation argument of De fato 11.
- **`metadata.greek_status`**  
  before → `"<absent>"`  
  after → `"«ἀργὸς λόγος» is the name of a different argument (the fatalist sophism at Cic. Fat. 28-30 / Orig. C. Cels. II.20), not of the consequences-for-motivation argument this node reconstructs"`
- **`metadata.key_passages`**  
  before → `["Fat. 265", "Fat. 267", "Fat. 268", "Fat. 260", "Fat. 284"]`  
  after → `"<absent>"`
- **`metadata.needs_evidence_note`**  
  before → `"<absent>"`  
  after → `"metadata.key_passages ['Fat. 260/265/267/268/284'] removed 2026-08-16: all outside Bruns 164-212. The tag gives no replacement, so none was invented; the confirmed locus is De Fato 11 (ancient_attestation_locus_classicus = passage_alex_fat_11)."`

#### `argument_moral_assessment_alex`

- **`description`** span  
  before → Sources: Fat. 19-20: Virtue presupposes choice; necessity undermines voluntariness; virtue's existence refutes determinism
Fat. 28: Vices also presuppose freedom; moral assessment is universal human practice  
  after → Sources: the definition of virtue as a hexis proairetikē (P1) is Aristotelian (EN II.6, 1106b36); in Alexander's corpus the formula occurs only in the In Topica and the Ethical Problems (Bruns 143), never in the De fato, so P1 is doctrinal rather than verbatim. What the De fato does carry verbatim is the praise/blame/punishment argument at De fato 19-20 (Bruns 189-191) and the virtue-and-vice argument at De fato 26-29 (Bruns 196.24-197.3).
- **`metadata.verification_notes`** += curator bracket, moved verbatim out of the description:  
  `"[Précision philologique 2026-08-03 : la définition ἕξις προαιρετική est aristotélicienne (EN II.6, 1106b36) ; dans le corpus d'Alexandre, la formule n'apparaît que dans l'In Topica et les Problèmes éthiques (Bruns 143), jamais dans le De fato — P1 est donc doctrinal, non verbatim. Ce qui est verbatim au De fato 19-20 (Bruns 189-191) est l'argument de l'éloge, du blâme et du châtiment, et au De fato 26-29 (Bruns 196.24-197.3) celui de la vertu et du vice.]"`

#### `argument_pascals_wager_and_voluntarism_4519ad75`

- **`description`** span  
  before → "Abêtissez-vous" (Make yourself stupid/dull your reason): Participate in religious practices (Mass, holy water, etc.).  
  after → The traditional catchphrase "abêtissez-vous" ("make yourself stupid", i.e. dull your reason) is a later reformulation: the Wager fragment (Laf. 418) has the future indicative "vous fera croire". Pascal's point is practical: participate in religious practices (Mass, holy water, etc.).
- **`metadata.verification_notes`** += curator bracket, moved verbatim out of the description:  
  `"[Correction 2026-08-02 : le fragment du Pari (Laf. 418) porte « vous fera croire » (futur), non l’impératif « abêtissez-vous », qui est une reformulation.]"`

#### `argument_plutarch_providence_cooperation_8c5a9d3f`

- **`metadata.formulator`**  
  before → `"Plutarch"`  
  after → `"Pseudo-Plutarch"`

#### `argument_pseudo_chrysostom_de_fato_v_witness6_amand1945`

- **`description`** span  
  before → Amand publie d'abord la traduction française intégrale, puis le texte grec original d'après Montfaucon (l'ensemble p. 519-532).  
  after → Amand publie d'abord la traduction française intégrale (p. 520-527), puis le texte grec original d'après Montfaucon (p. 527-532), l'ensemble occupant p. 519-532.

#### `argument_reactive_attitudes_alex`

- **`metadata.needs_evidence_note`**  
  before → `"<absent>"`  
  after → `"metadata.sources previously listed passage_alex_fat_611-616, none of which exists in the graph; replaced 2026-08-16 by the loci the premises cite (De Fato 16 and 26). The unconfirmable joint publication 'Marmodoro & Bobzien 2015' was replaced by Bobzien 1998, the work actually discussed."`
- **`metadata.sources`**
  - removed → `"passage_alex_fat_611"`
  - removed → `"passage_alex_fat_612"`
  - removed → `"passage_alex_fat_613"`
  - removed → `"passage_alex_fat_614"`
  - removed → `"passage_alex_fat_615"`
  - removed → `"passage_alex_fat_616"`
  - added → `"passage_alex_fat_16"`
  - added → `"passage_alex_fat_26"`
- **`metadata.validity_assessment`**  
  before → `{"rationale": "The argument is formally valid as a reductio: if P1-P5 hold, then Stoic practice contradicts Stoic doctrine. However, scholarly acceptance is disputed because (a) the Stoics may distinguish between first-order emotional responses (which even the sage may experience as 'pre-passions') and second-order assent; (b) the argument conflates psychological phenomenology with metaphysical commitment—experiencing anger does not logically entail believing in libertarian freedom; (c) Chrysippus's compatibilist framework (cylinder analogy) allows for 'up to us' (eph' hēmin) as a compatibilist notion, rendering the contradiction merely apparent. See Bobzien 1998, ch. 6 on Stoic causal distinctions: the principal cause (hegemonikon) remains 'in us' even under determinism. Alexander's argument assumes without proof that eph' hēmin requires indeterminism (the libertarian premise).", "formally_valid": "disputed", "scholarly_consensus": "The argument is widely recognized as Alexander's cen…`  
  after → `{"rationale": "The argument is formally valid as a reductio: if P1-P5 hold, then Stoic practice contradicts Stoic doctrine. However, scholarly acceptance is disputed because (a) the Stoics may distinguish between first-order emotional responses (which even the sage may experience as 'pre-passions') and second-order assent; (b) the argument conflates psychological phenomenology with metaphysical commitment—experiencing anger does not logically entail believing in libertarian freedom; (c) Chrysippus's compatibilist framework (cylinder analogy) allows for 'up to us' (eph' hēmin) as a compatibilist notion, rendering the contradiction merely apparent. See Bobzien 1998, ch. 6 on Stoic causal distinctions: the principal cause (hegemonikon) remains 'in us' even under determinism. Alexander's argument assumes without proof that eph' hēmin requires indeterminism (the libertarian premise).", "formally_valid": "disputed", "scholarly_consensus": "The argument is widely recognized as Alexander's cen…`

#### `argument_sea_battle_aristotle_f6g7h8i9`

- **`metadata.bobzien_2001_chapter`**  
  before → `"Ch. 2 Two Chrysippean Arguments for Causal Determinism"`  
  after → `"Ch. 2"`

#### `argument_tertullians_antimarcionite_argument_for_free_will_f49cad73`

- **`metadata.needs_evidence_note`**  
  before → `"<absent>"`  
  after → `"primary_sources cleared on premises P1-P4 2026-08-16: the tag records that these four premises are verbatim from a different Tertullianic work than the Adversus Marcionem / De anima loci they were anchored to, but truncates before naming it. No replacement locus invented; the node's genuine anti-Marcionite grounding is Adv. Marc. II.5-7 (verified_reference)."`
- **`metadata.premises`**
  - removed → `{"id": "P1", "text": "God is the unique, omnipotent creator of the world (unus deus, omnipotens mundi conditor).", "attestation": "direct", "primary_sources": ["(Adversus Marcionem II.5-7)"], "secondary_sources": []}`
  - removed → `{"id": "P2", "text": "The Father, Son, and Holy Spirit constitute an economic dispensation (oikonomia) of this one God, not a division of divinity.", "attestation": "direct", "primary_sources": ["passage_tert_de_anima_2"], "secondary_sources": []}`
  - removed → `{"id": "P3", "text": "The Son (Word/Sermo) proceeded from the Father, through whom all things were made, and was sent by the Father into the Virgin, born as both human and God.", "attestation": "direct", "primary_sources": ["passage_tert_de_anima_2"], "secondary_sources": []}`
  - removed → `{"id": "P4", "text": "The devil emulates truth by defending it in order to shake it, specifically by claiming the unique Lord as sole creator in a way that generates heresy.", "attestation": "direct", "primary_sources": ["(Adversus Marcionem II.5-7)"], "secondary_sources": []}`
  - added → `{"id": "P1", "text": "God is the unique, omnipotent creator of the world (unus deus, omnipotens mundi conditor).", "attestation": "unverified", "primary_sources": [], "secondary_sources": []}`
  - added → `{"id": "P2", "text": "The Father, Son, and Holy Spirit constitute an economic dispensation (oikonomia) of this one God, not a division of divinity.", "attestation": "unverified", "primary_sources": [], "secondary_sources": []}`
  - added → `{"id": "P3", "text": "The Son (Word/Sermo) proceeded from the Father, through whom all things were made, and was sent by the Father into the Virgin, born as both human and God.", "attestation": "unverified", "primary_sources": [], "secondary_sources": []}`
  - added → `{"id": "P4", "text": "The devil emulates truth by defending it in order to shake it, specifically by claiming the unique Lord as sole creator in a way that generates heresy.", "attestation": "unverified", "primary_sources": [], "secondary_sources": []}`

#### `argument_wildberg_2014_simplicius_neoplatonist_reading_epictetus_prohairesis_not_free_will`

- **`description`** span  
  before → Argument scholarly attribué à Wildberg (Destrée 2014, chapitre non identifié) : deux thèses.  
  after → Argument scholarly de Christian Wildberg, « The will and its freedom: Epictetus and Simplicius on what is up to us », 21e contribution du volume Destrée–Salles–Zingano 2014 (p. 329-349) : deux thèses.

#### `collection_ls`

- **`description`** span  
  before → Sections-clés pour le KG : 20 (clinamen épicurien), 55 (causalité et destin), 62 (responsabilité morale), 68–70 (scepticisme académique, y compris Carnéade), 71–72 (renouveau pyrrhonien : Énésidème).  
  after → Sections-clés pour le KG : 20 (« Free will » — clinamen épicurien, p. 102), 55 (« Causation and fate », p. 333), 57 (« Impulse and appropriateness » — impulsion et oikeiôsis, p. 346), 62 (« Moral responsibility », p. 386), 65 (« The passions », p. 410), 68–70 (les Académiciens, y compris Carnéade, p. 438-467), 71–72 (renouveau pyrrhonien, p. 468-488).

#### `concept_arche_alex`

- **`metadata.key_passages`**
  - removed → `"Fat. 233"`
  - removed → `"Fat. 235"`
  - removed → `"Fat. 246"`
  - removed → `"Fat. 247"`
  - removed → `"Fat. 253"`
  - removed → `"Fat. 254"`
- **`metadata.needs_evidence_note`**  
  before → `"<absent>"`  
  after → `"metadata.key_passages: Fat. 233/235/246/247/253/254 removed 2026-08-16 as outside Bruns 164-212; only Fat. 180 survives, plus the verified locus De Fato 15 (Bruns 185) in verified_reference."`

#### `concept_carneadean_probabilism_amand1945`

- **`metadata.amand_location`**  
  before → `{"chapter": "Introduction §II Ch. II", "page_range": "p. 41-58"}`  
  after → `{"chapter": "Introduction, Chapitre III §III (« Sa conception pragmatiste de la liberté »)", "page_range": "p. 65"}`

#### `concept_common_cause_alex`

- **`metadata.key_passages`**  
  before → `["351-370"]`  
  after → `"<absent>"`
- **`metadata.needs_evidence_note`**  
  before → `"<absent>"`  
  after → `"metadata.key_passages ['351-370'] removed 2026-08-16: outside Bruns 164-212. The node's own bruns_pages '194-195' and verified_reference (TLG-E collation, Bruns 192.23-195.28) carry the real locus."`

#### `concept_external_principle_action`

- **`period`**  
  before → `"Classical Greek"`  
  after → `"Roman Imperial"`

#### `concept_fortuna_boethius_j5k6l7m8`

- **`description`** span  
  before → Latin texts: • "Haec nostra vis est, hunc continuum ludum ludimus: rotam volubili orbe versamus"
 (This is my power, this is the game I play: I turn the wheel with its spinning circle)  
  after → Latin texts: • "Haec nostra vis est, hunc continuum ludum ludimus; rotam volubili orbe versamus, infima summis summa infimis mutare gaudemus" (II, pr. 2)
 (This is my power, this is the game I play: I turn the wheel with its spinning circle, and delight to change the lowest for the highest and the highest for the lowest)

#### `concept_gratia_cooperans`

- **`metadata.coinage_note`**  
  before → `"«χάρις συνεργοῦσα» is a modern back-translation, unattested in TLG. The concept node (Augustine's Latin doctrine) is sound. Fix the 'greek_term' field: drop 'χάρις συνεργοῦσα' or relabel it explicitly as a modern conventional Greek rendering of the Latin 'gratia cooperans' — not an ancient/Augustinian Greek term. Keep 'gratia cooperans' as the re"`  
  after → `"«χάρις συνεργοῦσα» is a modern back-translation, unattested in TLG. The concept node (Augustine's Latin doctrine) is sound. Fix the 'greek_term' field: drop 'χάρις συνεργοῦσα' or relabel it explicitly as a modern conventional Greek rendering of the Latin 'gratia cooperans' — not an ancient/Augustinian Greek term."`
- **`metadata.greek_term`**  
  before → `"χάρις συνεργοῦσα (charis synerg ousa)"`  
  after → `"χάρις συνεργοῦσα (charis synergousa) — modern scholarly rendering of the Latin, NOT an attested ancient term"`

#### `concept_gratia_operans`

- **`metadata.greek_status`**  
  before → `"<absent>"`  
  after → `"modern_scholarly_rendering — NOT an attested ancient term"`
- **`metadata.greek_term`**  
  before → `"χάρις ἐνεργοῦσα (charis energousa)"`  
  after → `"χάρις ἐνεργοῦσα (charis energousa) — modern scholarly rendering of the Latin, NOT an attested ancient term"`

#### `concept_intellectualism_medieval_i3j4k5l6`

- **`metadata.latin_status`**  
  before → `"<absent>"`  
  after → `"modern_scholarly_coinage — 'intellectualismus' is post-medieval and is NOT a term used by Aquinas or his contemporaries"`

#### `concept_libertas_spontaneitatis_5g9b0c68`

- **`metadata.latin_locus`**  
  before → `"Leibniz / Wolffian scholasticism; reported by Kant, Kritik der praktischen Vernunft (Ak. V.96) as 'libertas spontaneitatis'; contrast 'libertas indifferentiae'"`  
  after → `"Leibniz / Wolffian scholasticism; contrast 'libertas indifferentiae'"`
- **`metadata.needs_evidence_note`**  
  before → `"<absent>"`  
  after → `"The attribution of the term to Kant, KpV Ak. V:96, was removed from latin_locus 2026-08-16: that passage is the Bratenwender/turnspit argument and does not report 'libertas spontaneitatis'. No replacement locus invented."`

#### `concept_non_necessitating_cause_alex`

- **`label`**  
  before → `Non-Necessitating Cause (αἴτιον οὐκ ἀναγκαστικόν)`  
  after → `Non-Necessitating Cause (modern rendering: αἴτιον οὐκ ἀναγκαστικόν — not Alexander's own term)`
- **`metadata.bruns_pages`**  
  before → `"211-212"`  
  after → `"<absent>"`
- **`metadata.key_passages`**  
  before → `["459-462"]`  
  after → `"<absent>"`
- **`metadata.needs_evidence_note`**  
  before → `"<absent>"`  
  after → `"metadata.key_passages ['459-462'] and bruns_pages '211-212' removed 2026-08-16: the first matches no Alexander citation scheme, the second is the peroration (ch. 38) rather than the locus of the doctrine. The adjudicated loci are in verified_reference (De Fato chs. 22-26, 33-38)."`

#### `concept_providentia_stoic_seneca_b3c4d5e6`

- **`description`** span  
  before → • "praeesse universis providentiam" - providence presides over all
• "interesse nobis deum" - god is involved in our affairs  
  after → • "praeesse universis providentiam" (1.1) - providence presides over all
• "interesse nobis deum" (1.1) - god is involved in our affairs

#### `concept_self_happiness_alex`

- **`metadata.needs_evidence_note`**  
  before → `"<absent>"`  
  after → `"metadata.transliteration 'di hautōn eudaimonein' removed 2026-08-16: it transliterates a phrase the node's own greek_attestation field records as unattested in Alexander (εὐδαιμον-: 0 occurrences in the De fato). No replacement invented."`
- **`metadata.transliteration`**  
  before → `"di hautōn eudaimonein"`  
  after → `"<absent>"`

#### `concept_synkatathesis_logike_alex`

- **`metadata.key_passages`**
  - removed → `"Fat. 230-231"`
  - removed → `"Fat. 257"`
  - added → `"De anima libri mantissa, Bruns 184.11 (Περὶ τοῦ ἐφ' ἡμῖν)"`
- **`metadata.needs_evidence_note`**  
  before → `"<absent>"`  
  after → `"metadata.key_passages ['Fat. 230-231', 'Fat. 257'] removed 2026-08-16 as impossible De Fato loci; replaced by the locus this node's own verified_reference confirms verbatim in TLG0732."`

#### `passage_alcin_alcinous_untitled_full_text`

- **`school`**  
  before → `"Middle Platonist"`  
  after → `null`
- **`metadata.attestation_type`**  
  before → `"direct"`  
  after → `"fragment_collection"`
- **`metadata.author`**  
  before → `"Alcinous"`  
  after → `"Hegesippus"`
- **`metadata.canonical_ref`**  
  before → `"Didasc. 1"`  
  after → `null`
- **`metadata.cts_urn_note`**  
  before → `"previous value was a fake placeholder (passage1); no edition locus known"`  
  after → `"Original value was urn:cts:greekLit:tlg1398:passage1 (Hegesippus); it was cleared as a fake placeholder during the primary-source wave, after which the node was left filed under Alcinous. tlg1398 is the correct author number; no edition locus is known for this extraction."`
- **`metadata.doxographical_confidence`**  
  before → `"medium"`  
  after → `null`
- **`metadata.doxographical_source`**  
  before → `"heuristic"`  
  after → `null`
- **`metadata.mislabel_correction_2026_08_16`**  
  before → `"<absent>"`  
  after → `"This node was labelled 'Alcinous, Handbook of Platonism (Didaskalikos), Didasc. 1' with work_canonical_id urn:cts:greekLit:tlg0720.tlg001. Its 8,218-character Greek payload is in fact the Hegesippus fragment collection (TLG 1398): the martyrdom of Symeon son of Clopas under Trajan and the consular Atticus (= Eusebius, HE III.32), the account of James the Just (= Eusebius, HE II.23, incl. 'ἀπεσκληκέναι τὰ γόνατα αὐτοῦ δίκην καμήλου'), the list of Jewish sects (= Eusebius, HE IV.22, 'ἦσαν δὲ γνῶμαι διάφοροι ἐν τῇ περιτομῇ'), and the fragment transmitted by Photius from Stephanus Gobarus ('Μακάριοι οἱ ὀφθαλμοὶ ὑμῶν οἱ βλέποντες'). Verified 2026-08-16 with scripts/tlg_search.py against TLG1398, TLG2018 and TLG4040. Root cause: data/corpus/manifest.jsonl records the Alcinous work row urn_cts_greeklit_tlg0720_tlg001 as ingested from 'scaife:urn:cts:greekLit:tlg1398'. The edges asserting authorship by Alcinous and membership in the Didaskalikos were deleted."`
- **`metadata.needs_evidence_note`**  
  before → `"<absent>"`  
  after → `"Text quality: the stored payload is a lossy, line-shredded extraction with broken beta-code diacritics (e.g. '*̓ιάκωβος', 'τινε\\ς') and dropped words; it must not be quoted. Re-ingest from a critical edition (Eusebius, HE, GCS 9 Schwartz, or the Hegesippus fragments) before any use. The node id still carries the legacy 'alcin' prefix because data/corpus/citations.jsonl and the corpus passage row reference it."`
- **`metadata.school`**  
  before → `"Middle Platonist"`  
  after → `null`
- **`metadata.work_canonical_id`**  
  before → `"urn:cts:greekLit:tlg0720.tlg001"`  
  after → `"urn:cts:greekLit:tlg1398"`
- **`metadata.work_title`**  
  before → `"Handbook of Platonism (Didaskalikos)"`  
  after → `"Hypomnemata (fragments, ed. as TLG 1398)"`

#### `person_cyrus_alexandria_d641`

- **`description`** span  
  before → puis réhabilité ; Alexandrie tombe aux mains des Arabes ('Amr ibn al-'As) en 642. Sources : ACO ser. II ; Théophane, *Chronographia* AM 6121-6132 (éd. de Boor 1883).  
  after → puis réhabilité ; il négocie le traité d'Alexandrie le 8 novembre 641 et meurt le 21 mars 642, avant l'entrée des Arabes ('Amr ibn al-'As) dans la ville le 29 septembre 642. Sources : ACO ser. II ; Théophane, *Chronographia* AM 6121-6134 (éd. de Boor 1883) ; P. Booth, *Crisis of Empire* (2014).

#### `person_ekstrom_laura_1u2v3w4x`

- **`metadata.birth_date`**  
  before → `"fl. late 20th-21st c."`  
  after → `null`
- **`metadata.needs_evidence_note`**  
  before → `"<absent>"`  
  after → `"birth_date cleared 2026-08-16: the placeholder 'fl. late 20th-21st c.' was unverifiable and Wikidata Q113828985 records no date of birth."`

#### `person_ginet_carl_0t1u2v3w`

- **`metadata.death_date`**  
  before → `"2017 CE"`  
  after → `null`
- **`metadata.needs_evidence_note`**  
  before → `"<absent>"`  
  after → `"death_date '2017 CE' cleared 2026-08-16 as unverified; birth_date 1932 is retained (Cornell emeritus). No replacement asserted."`

#### `person_hippolytus_rome_d235`

- **`metadata.description_en`** span  
  before → a near-textual transcription of Sextus Empiricus Adv. Math. V, 50-105 (with poor personal supplements)  
  after → a near-textual transcription of Sextus Empiricus Adv. Math. V (with poor personal supplements)

#### `person_porphyry`

- **`description`** span  
  before → Editions: Ad Marcellam (ed. des Places, Les Belles Lettres, 1982); To Nemertius fragments in Boulnois (2000), reconstructed from Cyril's Contra Iulianum.  
  after → The securely attested Porphyrian material on what is up to us is the set of fragments 268-271 Smith (= Stobaeus, Anthologium II.8.39-42), from a work Περὶ τοῦ ἐφ' ἡμῖν. Editions: Ad Marcellam (ed. des Places, Les Belles Lettres, 1982); To Nemertius fragments in Boulnois (2000), reconstructed from Cyril's Contra Iulianum.

#### `pub_amand_1945_fatalisme`

- **`metadata.isbn`**  
  before → `"9789025606466"`  
  after → `"<absent>"`
- **`metadata.reprint`**  
  before → `"<absent>"`  
  after → `"Amsterdam: A. M. Hakkert, 1973 (ISBN 9789025606466)"`

#### `sc379_athenagoras_legatio`

- **`metadata.total_chapters`**  
  before → `38`  
  after → `37`

#### `sc79_chrysostomus_de_providentia`

- **`metadata.work_identity_conflict`**  
  before → `"<absent>"`  
  after → `"UNRESOLVED (recorded 2026-08-16): the node id and sc_number/sc_volume/sc_edition fields identify SC 79 = Malingrey, Sur la providence de Dieu (Ad eos qui scandalizati sunt) = PG 52:479-528, while the description and the ingested passages are the six Discourses on Fate and Providence, PG 50:749-774 — a different work of disputed authenticity. Both cannot describe the same text; the corpus rows must be re-homed before either field is changed."`

#### `scholar_jacobsen_a`

- **`metadata.birth_date`**  
  before → `"1963"`  
  after → `null`
- **`metadata.key_works`**
  - removed → `"Universal Salvation: The Current Debate (CUP 2019, ed.)"`
- **`metadata.needs_evidence_note`**  
  before → `"<absent>"`  
  after → `"birth_date cleared 2026-08-16 (metadata said 1963, the prose 1962; neither could be confirmed). key_works: 'Universal Salvation: The Current Debate (CUP 2019, ed.)' removed — the title belongs to Parry & Partridge, not to Jacobsen."`

#### `scholar_list_n`

- **`description`** span  
  before → Research fields recorded as Early Christian studies, Middle Platonism and Justin Martyr. These belong to a different scholar than the List discussed by Fürst 2022, which is Christian List,  
  after → Nicholas List — Early Christian studies, Middle Platonism and Justin Martyr; author of 'Justin Martyr's Problem with Platonism', Vigiliae Christianae 78 (2024). Not to be confused with the List discussed by Fürst 2022, who is Christian List,

#### `scholar_simonetti_m`

**NEW NODE.**

```json
{
 "node_id": "scholar_simonetti_m",
 "id": "scholar_simonetti_m",
 "type": "person",
 "label": "Manlio Simonetti",
 "role": "scholar",
 "school": null,
 "period": "Contemporary",
 "alternative_names": "[]",
 "description": "Italian patristics scholar. In Sources Chrétiennes 312 (Origène, Traité des principes, tome V, Cerf 1984) he is the author of the «Compléments sur la tradition manuscrite du Traité des Principes» (pp. 11-17), the section that argues against Koetschau's preference for the lectio facilior; the Addenda et Corrigenda and the indices of that volume are Henri Crouzel's, per the volume's own Avant-Propos.",
 "metadata": {
  "role": "scholar",
  "surname": "Simonetti",
  "given_names": "Manlio",
  "node_origin": "second_sweep_2026_08_16",
  "citation_verified": true,
  "verified_reference": "SC 312 = Origène, Traité des principes, tome V (Crouzel & Simonetti, Cerf, 1984), Avant-Propos: «Ce tome V… contient surtout les index. Ceux-ci sont précédés par des \"compléments sur la tradition manuscrite\" rédigés par M. Simonetti et par quelques \"Addenda et Corrigenda\" qui, avec les index, sont l'œuvre de H. Crouzel.»",
  "needs_evidence_note": "Created 2026-08-16 solely so that scholarly_argument_crouzel_manuscript_tradition_and_textu_1 could point its scholar_id / created_by at the right person. Biographical data (dates, affiliations, other works) is deliberately absent: none was verifiable from the sources in hand.",
  "second_sweep_2026_08_16": true
 }
}
```

#### `scholar_tomberlin_j`

- **`description`** span  
  before → philosophy of religion, free will defence  
  after → James E. Tomberlin — philosophy of religion, free-will defence. Co-author, with F. McGuinness, of 'God, Evil, and the Free Will Defence', Religious Studies 13 (1977), 455-475 (esp. pp. 456-458, engaging Plantinga's God and Other Minds and Rowe).

#### `scholar_wildberg_christian`

- **`description`** span  
  before → Auteur du chapitre « The will and its freedom: Epictetus and Simplicius on what is up to us » du volume Destrée 2014,  
  after → Auteur du chapitre « The will and its freedom: Epictetus and Simplicius on what is up to us » (ch. 21, p. 329-349) du volume Destrée 2014,
- **`metadata.description_en`** span  
  before → Author of ch. 18 of Destrée 2014  
  after → Author of ch. 21 (pp. 329-349) of Destrée 2014

#### `scholarly_argument_bird_paul_s_view_of_salvation_and_d_0`

- **`metadata.needs_evidence_note`**  
  before → `"<absent>"`  
  after → `"page_range 'Introduction' cleared 2026-08-16: the substance cited comes from Schreiner's own essay in the volume, not from Bird's introduction. verified_reference gives only an approximate span (pp. ~19-50), so no exact range was asserted."`
- **`metadata.page_range`**  
  before → `"Introduction"`  
  after → `null`

#### `scholarly_argument_bobzien_justin_martyr_on_fate_9`

- **`metadata.needs_evidence_note`**  
  before → `"<absent>"`  
  after → `"page_range '6801-6802' cleared 2026-08-16: a character-offset marker from the local summary file, not a page range. The real page could not be recovered, so none was invented."`
- **`metadata.page_range`**  
  before → `"6801-6802"`  
  after → `null`

#### `scholarly_argument_bobzien_middle_platonist_synthesis_4`

- **`metadata.page_range`**  
  before → `"905-922"`  
  after → `"133-175"`

#### `scholarly_argument_bobzien_origin_of_the_free_will_proble_0`

- **`metadata.page_range`**  
  before → `"22-31, 187-194, 905-922"`  
  after → `"133-175"`

#### `scholarly_argument_crouzel_manuscript_tradition_and_textu_1`

- **`metadata.scholar_id`**  
  before → `"scholar_crouzel_henri"`  
  after → `"scholar_simonetti_m"`

#### `scholarly_argument_dihle_greek_philosophical_theology_a_0`

- **`metadata.supporting_evidence`**
  - removed → `"Cleanthes ap. Seneca Epistulae 41.1, Quaestiones naturales 2.35"`
  - added → `"Seneca, Epistulae 41.1 (Seneca's own Stoic formulation, not a Cleanthes fragment); Seneca, Quaestiones naturales 2.35"`

#### `scholarly_argument_fee_absence_of_libertarian_free_wi_2`

- **`metadata.needs_evidence_note`**  
  before → `"<absent>"`  
  after → `"page_range '681-687, 912-915, 15682-15694' cleared 2026-08-16: markdown line numbers from Fee_1994.summary.md, not book pages (the book has 992 pp.). No replacement invented."`
- **`metadata.page_range`**  
  before → `"681-687, 912-915, 15682-15694"`  
  after → `null`

#### `scholarly_argument_hick_free_will_and_moral_evil_0`

- **`metadata.engages_with_scholars`**
  - removed → `{"note": "contemporary advocate of Augustinian free-will defense discussed in chapter 17", "stance": "cites", "scholar": "Alvin Plantinga"}`

#### `scholarly_argument_jourdan_determinism_and_fate_vs_free_w_2`

- **`metadata.needs_evidence_note`**  
  before → `"<absent>"`  
  after → `"Two malformed Clement citations ('Stromates I 2,19.94,1-7' and 'Stromates I 3,26.1-27.3') removed from supporting_evidence 2026-08-16; the tag gives no well-formed replacement, so none was invented."`
- **`metadata.supporting_evidence`**
  - removed → `"Clement of Alexandria, Stromates I 2,19.94,1-7"`
  - removed → `"Clement of Alexandria, Stromates I 3,26.1-27.3"`

#### `scholarly_argument_linjamaa_cosmos_as_school_and_community_4`

- **`metadata.needs_evidence_note`**  
  before → `"<absent>"`  
  after → `"supporting_evidence: the five TriTrac loci '140:32-144:16', '144:17-148:21', '148:22-152:26', '152:27-156:31', '156:32-160:36' removed 2026-08-16 as impossible (the tractate ends at 138:27); replaced by the loci this node's own verified_reference confirms."`
- **`metadata.supporting_evidence`**
  - removed → `"TriTrac 140:32-144:16 on the community structure and term 'church'"`
  - removed → `"TriTrac 144:17-148:21 on cosmos as school and early Christian context"`
  - removed → `"TriTrac 148:22-152:26 on school of conduct in Pleroma and gaining of form"`
  - removed → `"TriTrac 152:27-156:31 on silent and oral instruction, formation, baptism, education"`
  - removed → `"TriTrac 156:32-160:36 on duty of pneumatic moral expert and formation of psychic Christians"`
  - added → `"TriTrac (NHC I,5) 71:22-23 ('school of conduct')"`
  - added → `"TriTrac (NHC I,5) 123:12 ('a place of instruction')"`
  - added → `"Linjamaa 2019, ch. 5 'The Cosmos as a School' (pp. 185-226)"`

#### `scholarly_argument_linjamaa_social_and_political_involveme_5`

- **`metadata.needs_evidence_note`**  
  before → `"<absent>"`  
  after → `"supporting_evidence: the four impossible TriTrac codex citations (160:37-176:56, beyond the tractate's extent) removed 2026-08-16; the biblical loci and the chapter reference from verified_reference are retained. No replacement codex locus invented."`
- **`metadata.supporting_evidence`**
  - removed → `"TriTrac 160:37-164:41 on TriTrac and early Christian attitudes toward involvement in society"`
  - removed → `"TriTrac 164:42-168:46 on cosmogony as political commentary"`
  - removed → `"TriTrac 168:47-172:51 on pursuit of honor"`
  - removed → `"TriTrac 172:52-176:56 on psychic humans and their political involvement"`
  - added → `"Linjamaa 2019, ch. 6 'Honor and Attitudes toward Social and Political Involvement' (pp. 227-258)"`

#### `scholarly_argument_list_epistemological_foundation_of__2`

- **`metadata.needs_evidence_note`**  
  before → `"<absent>"`  
  after → `"page_range '429-431' cleared 2026-08-16: extraction line numbers, not journal pages (List, VC 78, 2024, runs pp. 1-21). No replacement invented."`
- **`metadata.page_range`**  
  before → `"429-431"`  
  after → `null`

#### `scholarly_argument_list_justin_martyr_s_anti_heresiolo_1`

- **`metadata.needs_evidence_note`**  
  before → `"<absent>"`  
  after → `"page_range '480-481, 785-787, 952-954' cleared 2026-08-16: extraction line numbers, not journal pages (List, VC 78, 2024, pp. 1-21)."`
- **`metadata.page_range`**  
  before → `"480-481, 785-787, 952-954"`  
  after → `null`

#### `scholarly_argument_prigent_determinism_and_predestination_1`

- **`metadata.supporting_evidence`**
  - removed → `"Barnabas 4.9-5"`
  - added → `"Barnabas 4-5 (eschatological / last-days material)"`

#### `scholarly_argument_telfer_christian_autexousia_and_jewis_2`

- **`description`** span  
  before → In Justin, autexousia applies equally to angels and humans, creating a parity  
  after → In Justin, autexousia applies equally to angels and humans — Telfer's own compressed Greek gloss «γένεα αὐτεξούσια» (JTS n.s. 8, 1957, p. 124), not a verbatim phrase of Justin — creating a parity

#### `scholarly_argument_telfer_free_will_and_determinism_in_e_0`

- **`metadata.engages_with_scholars`**
  - removed → `{"note": "cited for interpretation of 'three days' significance in preceding note by B.M. Metzger", "stance": "cites", "scholar": "E.C. Hoskyns"}`

#### `scholarly_work_dettwiler_2008_l_p_tre_aux_eph_siens`

- **`metadata.doi`**  
  before → `"http://archive-ouverte.unige.ch/unige:39485"`  
  after → `null`
- **`metadata.url`**  
  before → `"<absent>"`  
  after → `"http://archive-ouverte.unige.ch/unige:39485"`

#### `scholarly_work_dettwiler_2008_la_deuxi_me_p_tre_aux_thessaloniciens`

- **`metadata.doi`**  
  before → `"http://archive-ouverte.unige.ch/unige:39486"`  
  after → `null`
- **`metadata.url`**  
  before → `"<absent>"`  
  after → `"http://archive-ouverte.unige.ch/unige:39486"`

#### `scholarly_work_pironet_2003_faiblesse_de_la_raison_ou_faiblesse_de_v`

- **`metadata.additional_authors`**  
  before → `"<absent>"`  
  after → `["Christine Tappolet"]`

#### `scholarly_work_pouderon_2003_aristide_apologie`

- **`metadata.additional_authors`**  
  before → `"<absent>"`  
  after → `["Marie-Joseph Pierre", "Bernard Outtier", "Manana Guiorgadzé"]`

#### `scholarly_work_schiffman_2007_the_dead_sea_scrolls_the_truth_behind_th`

- **`metadata.type`**  
  before → `"monograph"`  
  after → `"audio_lecture_course"`

#### `scholarly_work_sharples_2003_threefold_providence_the_history_and_bac`

- **`metadata.doi`**  
  before → `"https://www.jstor.org/stable/43767935"`  
  after → `null`
- **`metadata.url`**  
  before → `"<absent>"`  
  after → `"https://www.jstor.org/stable/43767935"`

#### `scholarly_work_velardo_2013_notas_teol_gicas_de_bellum_judaicum`

- **`metadata.doi`**  
  before → `"10.2307/25930006008"`  
  after → `null`
- **`metadata.needs_evidence_note`**  
  before → `"<absent>"`  
  after → `"doi '10.2307/25930006008' cleared 2026-08-16 as fabricated: the number is the redalyc.org article id, not a JSTOR DOI. The article (Enfoques XXV.1, 2013, 127-136) has no registered DOI."`
- **`metadata.url`**  
  before → `"<absent>"`  
  after → `"https://www.redalyc.org/articulo.oa?id=25930006008"`

#### `synthesis_amand1945_cicero_ch2i_cadre`

- **`metadata.description_en`** span  
  before → probably from Antiochus of Ascalon or Posidonius;  
  after → probably from Clitomachus or Antiochus of Ascalon — the candidates Amand retains, following Lörcher 1907;

#### `synthesis_amand1945_origen_pivot_witness`

- **`metadata.description_en`** span  
  before → Amand's synthesis: Origen = 1st patristic witness of the Carneadean anti-fatalist lineage, historiographical pivot of Amand's Book II. Structural position: bridge between (a) the 6 witnesses of the Carneadean reconstruction (  
  after → Amand's synthesis: Origen, the historiographical pivot of Amand's Book II in the Carneadean anti-fatalist lineage — he does not open the patristic series, since Justin (Ch. I), Tatian (Ch. II), Bardesanes (Ch. III) and Clement of Alexandria (Ch. IV) precede him. Structural position: bridge between (a) the witnesses of the Carneadean reconstruction (

#### `synthesis_amand1945_plato_partial_anti_fatalism`

- **`metadata.amand_location`**  
  before → `{"chapter": "Introduction §I (Platon)", "page_range": "p. 20-40"}`  
  after → `{"chapter": "Introduction, Chapitre Premier §III (« Platon »)", "page_range": "p. 31-33"}`

#### `synthesis_destree2014_ch18_bonazzi_middle_platonist_hypothetical_fate`

- **`description`** span  
  before → Synthèse du ch. 18 (Bonazzi) :  
  after → Synthèse du ch. 18 (Bonazzi, p. 283-293) :
- **`metadata.description_en`** span  
  before → Synthesis of ch. 18 (Bonazzi):  
  after → Synthesis of ch. 18 (Bonazzi, pp. 283-293):

#### `synthesis_frede2011_ch6_platonist_peripatetic_criticisms`

- **`description`** span  
  before → et 'in Alexander that we find the ancestor of the notion' modern voluntariste critiquée par Ryle, Williams et Frede.  
  after → et « it is in Alexander that we find the ancestor of the notion that to have a free will is to be able… to choose between doing A and doing B » (p. 99-100) — la notion moderne volontariste critiquée par Ryle, Williams et Frede.
- **`metadata.description_en`** span  
  before → Frede concludes (p. 100, and Conclusion p. 177-178): Alexander 'is the only major ancient philosopher' whose conception is basically flawed, and 'it is in Alexander that we find the ancestor of the notion' of free will criticized by Ryle, Williams, and Frede  
  after → Frede concludes (p. 100, and Conclusion p. 177-178) that Alexander's conception is basically flawed — a compressed paraphrase, not a verbatim quotation — and that 'it is in Alexander that we find the ancestor of the notion that to have a free will is to be able… to choose between doing A and doing B' (p. 99-100), the notion of free will criticized by Ryle, Williams, and Frede

#### `synthesis_furst2022_carneades_will_innovation`

- **`metadata.description_en`** span  
  before →  Schallenberg qualifies Carneades-Cicero as 'libertarischer Kompatibilismus' (mirror parallel to the 'kompatibilistischer Libertarismus' Fürst attributes to Origen)  
  after →  Fürst for his part characterizes Origen's own position as a 'kompatibilistischer Libertarismus' — his own coinage, chapter heading VI.4, p. 282.

#### `work_augustine_retractationes`

- **`description`** span  
  before → Les traités anti-pélagiens adressés à Hadrumète et à la Gaule — dont le *De Gratia et Libero Arbitrio* (426/427) — ne figurent pas  
  after → Les traités anti-pélagiens adressés à Hadrumète et à la Gaule — dont le *De Gratia et Libero Arbitrio* (426/427) et le *De Correptione et Gratia* — ne figurent pas

#### `work_exodus_c9d0e1f2`

- **`period`**  
  before → `"Second Temple Judaism"`  
  after → `"First Temple / Pre-exilic Judaism"`

#### `work_gregory_de_anima_resurrectione`

- **`metadata.editions`**
  - removed → `"Maraval, SC 614 (Cerf 2022)"`
- **`metadata.needs_evidence_note`**  
  before → `"<absent>"`  
  after → `"editions: 'Maraval, SC 614 (Cerf 2022)' removed 2026-08-16 as unverifiable (Maraval d. 2017; no SC edition of this work). The French translation actually used is Terrieux, Cerf 1995, recorded in verified_reference."`

#### `work_maximus_tyre_dissertation_13`

- **`metadata.description_en`** span  
  before → Dissertation 13 (Hobein numbering) = 19 (Dübner) of Maximus of Tyre.  
  after → Dissertation 13 (Hobein numbering) of Maximus of Tyre.

#### `work_salles_stoics_determinism_2008`

- **`metadata.needs_edition_metadata`**  
  before → `true`  
  after → `"<absent>"`
- **`metadata.node_id_note`**  
  before → `"<absent>"`  
  after → `"The node id carries '_2008', which is wrong: the monograph is Ashgate 2005. The id is left unchanged because edges and citations reference it; the bibliographic fields are authoritative."`
- **`metadata.publisher`**  
  before → `"<absent>"`  
  after → `"Ashgate"`
- **`metadata.series`**  
  before → `"<absent>"`  
  after → `"Ashgate New Critical Thinking in Philosophy"`
- **`metadata.year`**  
  before → `"<absent>"`  
  after → `2005`

#### `work_tertullian_adv_marcionem`

- **`metadata.cts_urn_note`**  
  before → `"<absent>"`  
  after → `"stoa006-vs-stoa015 adjudicated 2026-08-16 in favour of urn:cts:latinLit:stoa0275.stoa015: that is the URN under which the project corpus ingests Adversus Marcionem (scaife:urn:cts:latinLit:stoa0275.stoa015.opp-lat1, data/corpus/manifest.jsonl). The description's stoa0275.stoa006 was the erroneous value and had already been dropped from the prose."`

