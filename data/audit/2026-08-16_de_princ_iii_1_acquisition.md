# Acquisition wave — 2026-08-16

**Applier:** `scripts/apply_2026_08_16_de_princ_iii_1_acquisition.py`
**Data:** `scripts/data_2026_08_16_de_princ_iii_1_greek.py`, `scripts/data_2026_08_16_historiography_nodes.py`
**Backups:** `data/kg/nodes.jsonl.bak-acq_2026_08_16`, `data/kg/edges.jsonl.bak-acq_2026_08_16`,
`data/corpus/passages.jsonl.bak-acq_2026_08_16`, `data/corpus/citations.jsonl.bak-acq_2026_08_16`

| | before | after |
|---|---|---|
| kg nodes | 19 992 | 20 021 (+29) |
| kg edges | 57 372 | 57 424 (+52) |
| corpus passages | 21 088 | 21 112 (+24) |
| corpus citations | 19 893 | 19 917 (+24) |

Applier is idempotent (verified: a second and third run change nothing).

---

## PART A — De principiis III.1 (= Philocalia 21) in Greek

### A.0 What was actually on disk

Three candidate witnesses were investigated:

| candidate | verdict |
|---|---|
| `02_Corpus/Sources chrétiennes txt/03_Origene/source/SC268_..._Extraits_grecs_livre_3_source.txt` | **Contains the complete Greek of III.1.1-24 and the SC 268 French.** Greek unusable as payload: the text extraction lost every line-final space (`περιέχεταιὁ`, `βιοῦνκαὶ`, `ἀκούοντας,πιστευθεὶς`) and kept the printed line-break hyphens (`συγκατα-τιθεμένους`). Restoring the lost word boundaries would be editorial invention. **Used as the alignment key and as the source of the French.** |
| `02_Corpus/SC 226 - Origène, Philocalie 21-27 (Sur le libre arbitre).rtf` (Junod) | The existing KG nodes already record it: the RTF export **contains only Philocalia 23, 25, 26, 27** — chapter 21 is absent. Re-confirmed. Not usable. |
| `02_Corpus/Philocalia_21-22-24.txt` (Robinson 1893, Internet Archive djvu OCR) | Contains ch. 21, but its own audit file (`Philocalia_21-22-24.OCR_AUDIT.md`) documents systematic Latin↔Greek OCR failure (`al`→`αἱ` 608×, `oiover`→`οἱονεὶ`, `yap`→`γάρ`). **Rejected — ingesting it would import garbage.** |

A fourth witness was then found and used: **the local TLG E disk**, `~/Desktop/Romain/TLGE/TLG2042.TXT`,
author 2042 = Origenes, **work 002 = De principiis** (citation levels Book.chapter.section.line,
read from `TLG2042.IDT`). The digitized edition is **P. Koetschau, _Origenes Werke_ V,
GCS 22, Leipzig: Hinrichs, 1913**. Word-separated, unhyphenated at the source, byte-clean.

### A.1 How the 24 section spans were fixed and verified

1. Space-insensitive, accent-insensitive, letter-only matching of each SC 268 section's head and
   tail against the TLG stream. Result: 24 contiguous spans, letter indices 847 008 → 881 251.
2. **Independent confirmation of every boundary:** each of the 24 spans begins exactly at a TLG
   section-level citation byte (`0x90`). The span contains **exactly 24** such bytes — no more, no
   fewer — and the next work-section header after §24 is
   `ΠΕΡΙ ΤΟΥ ΘΕΟΠΝΕΥΣΤΟΥ ΤΗΣ ΘΕΙΑΣ ΓΡΑΦΗΣ` (= De princ. IV.1 = Philocalia 1). The section division
   is therefore the TLG's own, not an editorial guess of mine.
3. Beta-code → Unicode with documented conventions (see the data module's docstring):
   `0x80` line-break byte → space; a line-break hyphen before it → words rejoined;
   `[2 ]2` → ⟨ ⟩; `[1 ]1` → ( ); `[ ]` → [ ]; `"1 "2` → “ ”; `"3` → `"`; `%` → † (Koetschau's crux);
   `_` → —. Word-initial breathings/accents and word-final iota subscripts are preserved
   (an early pass truncated them; fixed and re-verified).
4. **Collation against SC 268 per section** (letter-only similarity, stored in
   `metadata.sc268_collation_similarity`):

| § | sim | § | sim | § | sim | § | sim |
|---|---|---|---|---|---|---|---|
| 1 | 0.8975 * | 7 | 0.9994 | 13 | 1.0000 | 19 | 0.9965 † |
| 2 | 1.0000 | 8 | 1.0000 | 14 | 1.0000 | 20 | 0.9982 |
| 3 | 0.9988 | 9 | 1.0000 | 15 | 1.0000 | 21 | 1.0000 |
| 4 | 1.0000 | 10 | 0.9970 | 16 | 1.0000 | 22 | 1.0000 |
| 5 | 1.0000 | 11 | 1.0000 | 17 | 1.0000 | 23 | 0.9978 |
| 6 | 0.9991 | 12 | 1.0000 | 18 | 1.0000 | 24 | 1.0000 |

\* §1: the SC 268 block additionally carries the volume heading
`ΠΕΡΙ ΑΡΧΩΝ ΤΟΜΟΣ ΤΡΙΤΟΣ` and the chapter title; the title is stored separately in
`metadata.chapter_title_grc` and the §1 payload starts at the incipit `Ἐπεὶ δὲ ἐν τῷ κηρύγματι`.
The only other divergence is one letter (`τῷ ἐφ' ἡμῖν` Koetschau / `τὸ ἐφ' ἡμῖν` SC 268).

† §19: a **genuine editorial divergence, not damage**. Koetschau daggers
`†οὐχὶ δέ γε καὶ†` where SC 268 (Junod / Crouzel–Simonetti) prints `εἰκῆ δὲ καὶ ἐπὶ τό`.
The dagger is Koetschau's own crux and is reproduced. Recorded in
`SECTIONS[19]["variant_note"]`. §6 carries the second crux, `†μὴ†`.

5. **TLG re-attestation:** a 12-word markup-free window from the middle of every section was run
   through `scripts/tlg_search.py --authors 2042`. **24/24 hit.** Re-run afterwards against the
   text as actually written to `data/kg/nodes.jsonl`: 23/24 direct hits; §15's window is attested
   too (`ἐξελῶ τὰς λιθίνας καρδίας ἀπ' αὐτῶν καὶ ἐμβαλῶ σαρκίνας` → 1 hit), the automated miss
   being caused by the search tool not de-hyphenating the TLG's own `δι-καιώμασί` — i.e. the miss
   is an artefact of the tool, and confirms the de-hyphenation in the ingested text is real work.

### A.2 Integrity finding uncovered in passing (important)

The four pre-existing nodes `passage_origen_philocalia_21_{5,7,18,23}` **all** held the SC 268
**French** translation as their entire description, verified byte-for-byte against the local file
(`desc ⊂ file TRADUCTION` for all four). Three of them (§5, §7, §18) advertised **"Greek text"** in
their label and carried `metadata.language = "grc"`. This is exactly the defect corrected for §23
alone on 2026-08-16; it was in fact graph-wide for Philocalia 21.

All four are now corrected: they carry the real Greek, the previous description and label are
archived in `metadata.description_pre_greek_ingestion_2026_08_16` /
`label_pre_greek_ingestion_2026_08_16`, `citation_verdict` is set to `corrected`, and a
`verification_notes` entry records the finding.

### A.3 What was written

* **20 passage nodes created**, `passage_origen_philocalia_21_{1,2,3,4,6,8..17,19..22,24}`
* **4 passage nodes enriched**, `…_21_{5,7,18,23}`
* **40 edges** (2 per new node), mirroring the four pre-existing nodes exactly:
  `part_of → work_origen_philocalia` and `discusses → work_de_principiis_origen_230s_v2w3x4y5`
* **24 corpus passages**, work id `work_de_principiis_origen_230s_v2w3x4y5_grc`,
  CTS `urn:cts:greekLit:tlg2042.tlg002:3.1.{n}`, deterministic uuid5 passage ids
* **24 corpus citations** (`snapshot_passage_node`, confidence 1.0) binding each KG node to its
  corpus passage
* **1 manifest row**

**Greek ingested: 42 150 characters** across §§1-24 (per section: 504, 1133, 1034, 928, 1503,
2816, 2097, 1730, 1034, 1643, 1897, 2068, 1393, 2013, 2339, 2159, 3274, 1253, 3146, 1377, 2935,
1397, 1368, 1109). Each node also carries the SC 268 French (page numbers recorded in
`metadata.sc268_french_pages`, Greek pages in `sc268_greek_pages`; SC 268 prints Greek on
even pages 16-150 and the French facing on odd pages 17-151).

**Side-effect worth having:** the 42 k characters are now in `data/corpus/passages.jsonl`, which is
the corpus blob `check_greek_gate.py` matches against. Any future KG quotation from De princ. III.1
will now pass the gate on corpus evidence alone.

### A.4 Pre-existing anomalies noted, NOT fixed (out of scope, per "verify each item individually")

* `work_de_principiis_origen_230s_v2w3x4y5_eng` holds III.1.1-24 **in French**, not English
  (it is the SC 268 translation), and §3 is missing from it. Left alone.
* One passage already carried `work_canonical_id = work_de_principiis_origen_230s_v2w3x4y5_grc`
  before this wave — `"Origen, De Principiis III.1.3"`, 662 chars, **English** text. The manifest
  row records this honestly (`passages: 25`, with a note).

---

## PART B — civ. 21.12

**Verdict: genuinely absent locally. Leave `needs_text_ingestion` as is.**

Checked: `02_Corpus/LLT_brepols/` (20 author folders — no Augustinus), `02_Corpus/SCO_brepols/`
(34 folders — no Augustinus), `02_Corpus/Editions_critiques/`, `03_Sources_critiques/`
(only `Augustinus_Rm5-12_Latin_CSEL60.txt`), plus a content grep for
`de ciuitate dei | de civitate dei | massa damnata | damnata massa` across `02_Corpus` and
`03_Sources_critiques`. The single hit is
`02_Corpus/SCO_brepols/_harvest/works_llta_c45.json`, which is a Brepols **work catalogue**
(`{"title": "De ciuitate Dei", "author": "Augustinus Hipponensis"}`), not the text.

---

## PART C — Historiography nodes

Grounding rule applied: a position is stated only where the supporting text was READ locally.
None of the six works below is held; every position is *reported*, and each node carries
`held_locally: false`, `source_rank`, `reference_status` and a `grounding` list of verbatim
anchors with file + locator.

### C.1 Created — Benjamins

| node | type | grounding |
|---|---|---|
| `scholar_benjamins_hendrik_s` | person | bibliographic entry verbatim in **Fürst 2022 Literaturverzeichnis, printed p. 302**: `Benjamins, Hendrik S., Eingeordnete Freiheit. Freiheit und Vorsehung bei Origenes (SVigChr 28), Leiden 1994.`; imprint in Belcastro n. 27 (`Brill, Leiden-New York-Köln 1994`); page range in Markschies 2007 n. 63 |
| `pub_benjamins_1994_eingeordnete_freiheit` | publication | **four** independent held witnesses, quoted verbatim in `metadata.grounding` |

The audit brief's claim about **Fürst n. 100 is verified**. Fürst 2022, printed p. 283, n. 100
(.md ll. 10176-10179):

> `Diese Problematik, auf die Geyer, Geschichtsphilosophie bei Origenes 18, hinweist, ist das Thema
> der Studie von Benjamins, Eingeordnete Freiheit, bes. 71–121. Siehe dazu Fürst, Origenes als
> Theologe der Geschichte 147–149; Hengstermann, Freiheitsmetaphysik 321–351.`

hanging off the body text (same page, ll. 10148-10152):

> `taucht das Problem auf, ob nicht auch dieses durch und durch libertarische Konzept am Ende in
> einen Determinismus mündet.`

Corroborated by **Gibbons 2016 n. 3** (English summary of the thesis: Origen, like Alexander of
Aphrodisias, holds human action undetermined by prior causes, yet God uses foreknowledge to arrange
universal restoration) and **Belcastro n. 27**, which quotes Benjamins p. 1 in German
(`Die zwei Themen der menschlichen Freiheit und göttlichen Vorsehung bilden den Kern der Systematik
der Theologie des Origenes`) and p. 68 via Tolan 2021 n. 310.

Edges: `authored_by → scholar_benjamins_hendrik_s`;
`discusses → work_de_principiis_origen_230s_v2w3x4y5` (Fürst p. 249 n. 6 cites Benjamins 58-71 on
the De princ. III.1 doctrine of motion); `pub_furst_2022_wege_freiheit --engages_with-->` it
(stance `qualifies`).

### C.2 Enriched — Hengstermann (nodes already existed; **not** duplicated)

`pub_hengstermann_2016_freiheitsmetaphysik` and `scholar_hengstermann_christian` were already in
the graph and already broadly correct. They gained **eight verbatim German/English anchors** with
Fürst page numbers, plus `source_rank`, `reference_status`, `held_locally: false`, ISBN, series and
page count. The audit brief's claim that Fürst relies on Hengstermann for the Freiheitsmetaphysik
thesis **is verified**: Fürst 2022, printed p. 247, ch. VI n. 1:

> `Eine umfassende und grundlegende Studie über Origenes und den Ursprung der Freiheitsmetaphysik
> hat Christian Hengstermann 2016 vorgelegt.`

— footnoted to Fürst's own governing claim `indem er die Freiheit zum Prinzip der Anthropologie und
der Metaphysik, kurzum: der ganzen Wirklichkeit machte. Das war die grundlegende Innovation des
Origenes.` Further anchors: p. 189 n. 27 (`die eingehende philosophische Analyse von Origenes'
Freiheitstraktat bei Hengstermann, Freiheitsmetaphysik 13–93`), p. 210 n. 63 (against a voluntarist
reading), p. 205 n. 50 (Fürst's one **disagreement**), p. 260 n. 42, p. 267 n. 67, Fürst 2021
(`the seminal study of Christian Hengstermann…`), and Tolan 2021 n. 554 quoting Hengstermann 2016
p. 17 verbatim.

**Two corrections to the audit brief, recorded on the node:**
1. **Authorship** — the brief listed it as "Alfons Fürst / Christian Hengstermann". Every held
   witness (Fürst's own Literaturverzeichnis p. 305, Origeniana Duodecima n. 35, Aschendorff's
   series list, Brouwer/Vimercati 2020) gives **Hengstermann alone**. The KG already had this right.
2. **Date** — 2016. Claire Hall 2021 cites `(2017a)`; outlier against five witnesses.

**Page count corrected** — the node read `386pp`; Aschendorff's own series list, printed in
`fuerst_2021_perspectives_origen_adamantiana21.pdf`, gives `2016, 368 Seiten, gebunden, 48,– €.
ISBN 978-3-402-13719-2`. Now `368 pp.`, with the evidence in
`metadata.page_count_correction_2026_08_16`. (The applier carries a `HIST_REVISION` stamp so an
already-stamped node is revisited exactly once when an enrichment spec changes; spans that no
longer match are reported and skipped, never applied blind.)

**Contested-status flag added** (per the standing "no invention-of-the-will teleology" rule): the
IFB review of Kobusch, *Metaphysik der Freiheit* (Adamantiana 28), after quoting the Münster school's
core claim (`Origenes ist der erste Denker … der sie als ontologisches Prinzip begreift`), adds
`Wie auch immer man zu dieser historischen Rekonstruktion stehen mag – man wird wohl nicht
fehlgehen, wenn man vermutet, sie sei durchaus kontrovers –`.

New edge: `pub_furst_2022_wege_freiheit --engages_with--> pub_hengstermann_2016_freiheitsmetaphysik`
(stance `agrees`).

### C.3 Created — Augustine historiography

| node | grounding | verdict |
|---|---|---|
| `scholar_brown_peter`, `pub_brown_1967_augustine_of_hippo` | **Wetzel 1992 p. 158 n. 82** quotes Brown p. 170 verbatim: `"Surprisingly enough... the austere answer to the Second Problem of the Various Problems for Simplicianus is the intellectual charter for the Confessions. … the will is now seen as dependent on a capacity of 'delight,'…"` + **Barclay 2015 n. 17**. Imprint verbatim in Gorday 1983 and Wetzel p. 87 n. 3. | substantive position node (the 396 rupture) |
| `scholar_harrison_carol`, `pub_harrison_2006_rethinking_augustines_early_theology` | **Barclay 2015 n. 17**: `(the latter insisting, against Brown, Fredriksen et al., that little actually changes in the Ad Simpl. of 396)`; **Ramelli 2021**: `scholars such as Carol Harrison (2006) stress more the continuity of Augustine's thought during all of his life`. Ramelli n. 2 flags Drecoll's 2009 review → `contested` field set. | substantive position node (continuity) |
| `pub_rist_1969_augustine_free_will_predestination` | **Wetzel 1992 pp. 199, 202, 220-221**, incl. two verbatim Rist quotations (`What we should call psychological compulsions are not compulsions for Augustine. They are simply the individual working out his own nature.`; `this would make us little more than living puppets.`) | substantive position node |
| `scholar_teselle_eugene`, `pub_teselle_1970_augustine_the_theologian` | **Wetzel 1992 p. 198 + n. 75** (`TeSelle, Augustine the Theologian, 291.`), p. 188 n. 58, p. 199, p. 202 | substantive position node |

`scholar_rist_john` already existed and was **not** duplicated; the new publication node hangs off it.

**Two disambiguations/scope corrections, recorded on the nodes:**

* **Rist** — the position is attributable to **Rist 1969, JTS N.S. 20, 420-47** (reprinted in
  Markus ed., 1972), *not* to *Augustine: Ancient Thought Baptized* (1994). The 1994 book is
  nowhere attested in the local library and post-dates Wetzel 1992. The pub node is the 1969
  article and says so.
* **Harrison** — Carol Harrison, *Rethinking Augustine's Early Theology* (OUP 2006) is **not**
  Simon Harrison, *Augustine's Way into the Will* (Oxford 2006), whom Frede 2011 cites. A
  `disambiguation` field guards against a future merge.

### C.4 Correction applied — `pub_wetzel_1992_augustine_limits_virtue`

The node's description claimed Wetzel overturns *"the conventional wisdom of Brown, Rist, O'Daly,
Burnaby, Arendt"*. The held PDF is structurally corrupt with an empty (space-only) OCR layer; it was
rebuilt (catalog / page tree / xref) and its 254 page scans re-OCR'd for this wave. Across all 254
pages **Brown appears only as an authority Wetzel relies on**:

* p. 144 — `I owe debts to Brown, Augustine of Hippo, 146-57, Eugene TeSelle, Augustine the
  Theologian … 176-82, J. Patout Burns…`
* p. 110 — `in Peter Brown's memorable words`
* p. 88 — `For a judicious assessment … see Brown`
* p. 158 n. 82 — quotes Brown p. 170 approvingly

Wetzel's "conventional wisdom" passage (p. 3) names nobody and concerns the Platonism /
two-conversions reading. The opposition to **Rist, O'Daly, Burnaby, TeSelle and Arendt** *is*
attested (pp. 9, 198-203, 220-221).

Applied: Brown removed from the "overturning" list in `description`, `description_en` and
`description_fr`; evidence stored in `metadata.brown_relation_correction_2026_08_16`; PDF condition
recorded in `metadata.local_pdf_condition`; `citation_verdict → corrected`.

Consequently **no `Wetzel opposes Brown` edge was created**, contrary to the brief's suggestion.
Instead: `pub_wetzel_1992_augustine_limits_virtue --engages_with--> pub_brown_1967_augustine_of_hippo`
with `stance: agrees`, plus `opposes` edges to Rist 1969 and TeSelle 1970.

### C.5 Nothing was created without grounding

No bibliographic-shell-only node was needed: all four Augustine figures and Benjamins turned out to
have substantive READ evidence. All OCR-derived quotations are flagged `ocr: true` in
`metadata.grounding`, and the OCR artefacts observed (`22h` for 221, `vol. u` for vol. II,
`lberum` for liberum) are noted so no one mistakes them for the printed text.

---

## Gates

| gate | result |
|---|---|
| reparse `nodes.jsonl` | 20 021 rows, 20 021 unique ids, 0 `id`/`node_id` mismatches |
| reparse `edges.jsonl` | 57 424 rows, edge_ids unique, **0 dangling endpoints** |
| reparse `passages.jsonl` / `citations.jsonl` | 21 112 / 19 917, passage_ids unique |
| `check_greek_gate.py` (changed scope, pre-commit) | **OK** |
| `check_greek_gate.py --all` | 2 `tlg_only` findings — **both pre-existing at HEAD, untouched by this wave**: `argument_origen_witness_diss_problem4_angelic_knowledge_amand1945` (`δυνάμεσι θείαις τὰ σημεῖα ἔκκειται`) and `person_ignatius_antioch_d110` (`ἐνδεδεμένος δέκα λεοπάρδοις`). Each needs an allowlist entry with provenance; not in scope here. |
| `check_citations_gate.py` (changed + `--all`) | **OK** (208 verified references in manifest) |
| `check_corpus_invariants.py` | citations 19 917, passages 21 112, **dangling → passage 0, dangling → kg_node 0** |
| `check_kg_work_id_uniqueness.py` | WARN, allowlisted collisions only — **no new collision** |
| `audit_structural.py` | `uncited_claim_node` 1381, `cts_urn_format` 934, `duplicate_node_candidate` 6, **TOTAL 2321 — identical to the pre-wave baseline. Delta = 0, i.e. not even the expected uncited-shell entries** (the new nodes are `publication`/`person`/`passage`, not `argument`/`synthesis`, and every one of them is edge-connected). |
| applier idempotency | 2nd and 3rd runs: 0 nodes, 0 edges, 0 passages, 0 citations added |
