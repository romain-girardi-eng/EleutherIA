# 2026-08-16 — Fürst 2022 reception nodes + Origen *De oratione* 6: applied corrections

**Scope**: `data/kg/nodes.jsonl` only (6 nodes). No edge added, retargeted or deleted.
**Applier**: `scripts/apply_2026_08_16_furst_deoratione_corrections.py`
**Data**: `scripts/data_2026_08_16_furst_deoratione_corrections.py`
**Stamp / idempotency key**: `metadata.furst_deoratione_corrections_2026_08_16`
**Not committed** — working tree only.

---

## 0. Source verification performed before applying

### 0.1 German quotations — Fürst 2022

Checked against the local extraction
`~/Desktop/DOCTORAT/Doctorat SHAL/04_Littérature_secondaire/05_Origene/Alfons Fürst - Wege zur Freiheit_ Menschliche Selbstbestimmung von Homer bis Origenes-Mohr Siebeck (2022).md`.

The file soft-hyphenates German words across line breaks (`­` + newline), so a plain
`grep -F` on a quote that straddles a line break returns 0 even when the quote is present.
Every quote below was therefore re-read in its de-hyphenated context.

| Quote (as mandated) | Verbatim? | Page | Context in the file |
|---|---|---|---|
| `ist sein Freiheitskonzept ein Kompatibilismus` | **YES** (grep -F, 1 hit) | 289 | "…sich also auf dem Boden des biblischen Kompatibilismus bewegte, ist sein Freiheitskonzept ein Kompatibilismus." |
| `einen Libertarismus, wie man ihn sich stärker kaum vorstellen kann` | **YES** (line-wrapped; `stärker kaum vorstellen` grep -F, 1 hit) | 289 | "Allerdings propagierte er zugleich einen Libertarismus, wie man ihn sich stärker kaum vorstellen kann." |
| `ein Libertarist, doch ein Libertarist mit kompatibilistischen Neigungen` | **YES** (soft-hyphenated `kompati-­bilistischen`, hence 0 raw grep hits; present de-hyphenated) | 289 | "In dieser Hinsicht war Origenes ein Libertarist, doch ein Libertarist mit kompatibilistischen Neigungen." |
| `wofür auch immer man eher votiert, mehr für Libertarismus, mehr für Kompatibilismus, aber sicher nicht für Determinismus` | **YES** (soft-hyphenated `Liberta-­rismus`, hence 0 raw grep hits; present de-hyphenated) | 289 | "Wofür auch immer man eher votiert, mehr für Libertarismus, mehr für Kompatibilismus, aber sicher nicht für Determinismus, denn ein Determinist – wie seine gnostischen Kontrahenten – wollte Origenes auf gar keinen Fall sein…" |
| `Origenes konzipierte keinen Kausaldeterminismus … das wäre das stoische Modell` | **YES** (`das wäre das stoische Modell` grep -F, 1 hit) | 288 | "Origenes konzipierte keinen Kausaldeterminismus, in den Handlungen, für die Menschen die Ursache sind, eingereiht werden – das wäre das stoische Modell." |
| `Gewebe` (of interconnected free decisions) | **YES** (grep -F, 1 hit) | 288 | "Er dachte vielmehr an ein Gewebe von miteinander zusammenhängenden Entscheidungen und Handlungen freier Wesen, die von Gott, einem seinerseits freien Wesen … in einen sinnvollen Zusammenhang gebracht werden." |
| `das tragfähigste Konzept` | **YES** (soft-hyphenated `trag-­fähigste`) | 290 | "Das würde bedeuten, dass der Kompatibilismus das tragfähigste Konzept ist und es eigentlich nur um die Frage geht … welches Konzept von Kompatibilismus man vertritt." |
| `mit determinierten Aspekten der Wirklichkeit` | **YES** (soft-hyphenated `determi-­nierten`) | 290 | "…dass aber dieser Libertarismus mit determinierten Aspekten der Wirklichkeit kompatibel blieb." |

**Adjustment made vs the audit brief**: the brief cited the εἱρμός re-semanticization as
"Fürst 2022, 287-288". In the file, the εἱρμός discussion runs 286 (quotation of *orat.* 6,3
under n. 107) → 287 ("Allerdings verwendete Origenes zwar diesen stoischen Begriff, füllte
ihn aber mit einer anderen Bedeutung") → 288 (Gewebe). The nodes therefore cite
**286-288**, not 287-288.

Chapter structure confirmed: `4. Kompatibilistischer Libertarismus` is a section of
`VI. Die Freiheitsmetaphysik des Origenes`, opening on **p. 282** (with n. 99) and closing on
**p. 290**; `3. Libertarische Deutung des biblischen Determinismus` is the ch. **V 3** the
old node text actually summarised.

### 0.2 Greek — Origen, *De oratione* 6,3

Source read: `~/Desktop/DOCTORAT/Doctorat SHAL/02_Corpus/TLG/TLG_tlg2042_De_oratione_6_3.txt`
(TLG E `tlg2042.008`, Koetschau GCS Orig. 2, p. 313; file header records the extraction).
The span was taken byte-exact from lines `..6.3.5` → `..6.3.13`, line-joined, starting at
`καὶ ἐν πᾶσιν` and ending at `τάδε θελήσειν·` — **the raised dot is the punctuation the
edition prints there and was kept rather than silently converted to a full stop**.

Re-verification with `scripts/tlg_search.py` (accent/sigma-insensitive, whole local TLG E):

| Needle | Hits |
|---|---|
| `οὐχὶ τῆς προγνώσεως τοῦ θεοῦ αἰτίας γινομένης` | **1** — TLG2042 (Origenes) @byte 2486744 |
| `ἀπολοῦμεν τὸ τάδε τινὰ ἐνεργήσειν` | **1** — TLG2042 (Origenes) @byte 2486983 |

Confirmation that the **removed** Greek was recomposed:

| Needle (from the old description) | Hits |
|---|---|
| `Ἡ πρόγνωσις τοῦ θεοῦ οὐκ ἔστιν αἰτία πάντων τῶν ἐσομένων` | **0** |
| `οὐχ ὅτι γινώσκει ὁ θεὸς τὸ ἐσόμενον` | **0** |
| `ἀπ' αὐτεξουσίου κινήσεως` (was in `metadata.key_terms`) | **0** |

### 0.3 The "reversed order of knowing" sentence

Fürst 2022, 285 n. 105: "…und prägnant in philoc. 23,8 (SC 226, 156) = in Gen. frg. D 7,8
(OWD 1/1, 84): „Denn nicht weil es erkannt ist, geschieht es, sondern weil es geschehen wird,
ist es erkannt."" — i.e. the sentence the old node put into *De oratione* 6 belongs to the
*Philocalia* 23,8 / *in Gen.* fragment. Recorded in `metadata.note` of
`passage_origen_de_orat_6`.

### 0.4 French of *Philocalia* 21.23 — divergence from the audit brief

The brief asked to relabel the node as "French translation (SC 226 Junod)". The stored French
was located verbatim in
`02_Corpus/Sources chrétiennes txt/03_Origene/source/SC268_Origenes_Traite_des_Principes_Extraits_grecs_livre_3_source.txt`,
block `[liv.: 3, chap.: 1, par.: 23]`, `--- TRADUCTION ---` — i.e. **SC 268
(Crouzel–Simonetti)**, not SC 226. The node's own
`metadata.junod_sc226_rtf_status` already records that the SC 226 OCR export lacks
*Philocalia* 21. The label was therefore written as **SC 268 Crouzel–Simonetti**; the
divergence is recorded in the node's `verification_notes`.

Incidentally, the Greek of §23 *is* present in that same SC 268 file
(`23 (22). Τοῖς δὲ τὰς φύσεις εἰσάγουσι…`) — it is simply not ingested into this node. The
new `language_note` says exactly that, so the gap is actionable rather than invisible.

---

## 1. `scholarly_argument_f_rst_origen_s_libertarian_compatibi_4`

### `description`

**BEFORE**
> Origen's libertarian compatibilism — Develops the concept of 'kompatibilistischer Libertarismus' (compatibilist libertarianism) for Origen: Origen maintains genuine libertarian free will (autexousion) as foundational for Christian theology while also interpreting biblical determinism (especially Pauline passages on divine election) in ways that preserve rather than negate human self-determination

**AFTER**
> Origen's kompatibilistischer Libertarismus — Fürst coins 'kompatibilistischer Libertarismus' (compatibilist libertarianism) as a deliberately double-edged characterization of Origen. Insofar as Origen frames freedom within the teleological order of divine providence — on the ground of what Fürst calls biblical compatibilism — his concept of freedom is a compatibilism ('ist sein Freiheitskonzept ein Kompatibilismus'); yet he simultaneously propagates a libertarianism 'as strong as one can imagine' ('einen Libertarismus, wie man ihn sich stärker kaum vorstellen kann'), making freedom the ontological principle of rational being. Fürst's own verdict is deliberately suspended: Origen was 'ein Libertarist, doch ein Libertarist mit kompatibilistischen Neigungen', and 'wofür auch immer man eher votiert, mehr für Libertarismus, mehr für Kompatibilismus, aber sicher nicht für Determinismus'. The compatibility concerns determined aspects of reality (divine foreknowledge, providential pre-arrangement, reliable regularities) — NOT the Stoic causal chain, which Origen expressly does not adopt ('Origenes konzipierte keinen Kausaldeterminismus … das wäre das stoische Modell'): the Stoic term εἱρμός is retained but re-semanticized as a web (Gewebe) of interconnected free decisions ordered by a God who is himself free. Distinct from (though prepared by) Fürst's separate account of Origen's libertarian exegesis of biblical determinism (Pauline election, Pharaoh) in ch. V.3.

### `metadata.stance`

**BEFORE** — verbatim duplicate of the old description (ch. V 3 content).

**AFTER**
> Coins 'kompatibilistischer Libertarismus' as a deliberately double-edged characterization of Origen: a compatibilism insofar as freedom is framed within the teleological order of divine providence (Fürst's 'biblical compatibilism'), yet at the same time a libertarianism 'wie man ihn sich stärker kaum vorstellen kann', freedom being the ontological principle of rational being. The verdict is left suspended — 'ein Libertarist, doch ein Libertarist mit kompatibilistischen Neigungen' — and the compatibility is with determined aspects of reality (foreknowledge, providential pre-arrangement, reliable regularities), expressly not with a Stoic causal chain.

### `metadata.verified_reference`

**BEFORE**
> Fürst, Wege zur Freiheit: Menschliche Selbstbestimmung von Homer bis Origenes (Mohr Siebeck 2022), ch. V §4 'Kompatibilistischer Libertarismus' (p. 282); Origen, De principiis III.1 (Peri autexousiou)

**AFTER**
> Fürst, Wege zur Freiheit (Mohr Siebeck 2022), Kap. VI 4 'Kompatibilistischer Libertarismus', pp. 282-290 (verdict pp. 289-290); libertarian exegesis of biblical determinism = Kap. V 3, pp. 217-239; Origen, orat. 6,3 (GCS Orig. 2, 313); princ. II 1,2 (GCS Orig. 5, 107 f.).

### `metadata.page_range`

`"187-282"` → `"282-290"` (the old span covered the ch. V material the node had summarised).

### Provenance

Full old description + the note about the two conflated chapters appended to
`metadata.verification_notes`. Label untouched (it is a truncation of the old `stance`
introduced by an earlier pipeline; renaming it is out of scope here).

---

## 2. `concept_kompatibilistischer_libertarismus_origenian`

Applied identically to `description`, `metadata.description_en` and `metadata.description_fr`
(the pre-2026-08-16 archive field `description_en_pre_2026_08_16` was deliberately left
untouched — it is an archive).

**BEFORE (en)**
> … while remaining compatible with certain determined aspects of reality—the Stoic chain of causes, divine foreknowledge, providence.

**AFTER (en)**
> … while remaining compatible with certain determined aspects of reality (mit determinierten Aspekten der Wirklichkeit): divine foreknowledge, providential pre-arrangement, and reliable regularities of the world — expressly NOT the Stoic chain of physical causes, which Origen does not adopt: he retains the Stoic term εἱρμός but re-semanticizes it as a web (Gewebe) of interconnected free decisions of free beings, ordered by a God who is himself free (Fürst 2022, 286-288).

**BEFORE (fr)**
> … tout en restant compatible avec des aspects déterminés de la réalité — chaîne stoïcienne des causes, préscience divine, providence.

**AFTER (fr)**
> … tout en restant compatible avec certains aspects déterminés de la réalité (mit determinierten Aspekten der Wirklichkeit) : préscience divine, pré-arrangement providentiel et régularités fiables du monde — expressément PAS la chaîne stoïcienne des causes physiques, qu'Origène n'adopte pas : il conserve le terme stoïcien εἱρμός mais le resémantise en un tissu (Gewebe) de décisions libres interconnectées d'êtres libres, ordonnées par un Dieu lui-même libre (Fürst 2022, 286-288).

**APPENDED (en, at end of description / description_en)**
> Fürst's verdict remains deliberately suspended: 'ein Libertarist, doch ein Libertarist mit kompatibilistischen Neigungen' (p. 289); he even closes by suggesting compatibilism may be 'das tragfähigste Konzept' (p. 290), the real question being which concept of compatibilism one holds — Origen's differing from the Stoic in asking how free human self-determination coheres with the providential action of a God who is himself free.

**APPENDED (fr)**
> Le verdict de Fürst reste délibérément suspendu : « ein Libertarist, doch ein Libertarist mit kompatibilistischen Neigungen » (p. 289) ; il va jusqu'à suggérer, en conclusion, que le compatibilisme est peut-être « das tragfähigste Konzept » (p. 290), la vraie question étant de savoir quel concept de compatibilisme l'on soutient — celui d'Origène différant du stoïcien en ce qu'il demande comment la libre autodétermination humaine s'accorde avec l'action providentielle d'un Dieu lui-même libre.

### `metadata.verified_reference`

**BEFORE** — `C. M. Fürst, Wege zur Freiheit (2022), Kap. VI.4 …`
**AFTER** — `A. Fürst, Wege zur Freiheit (2022), Kap. VI.4 …` (rest unchanged).

---

## 3. `argument_furst_2022_kompatibilistischer_libertarismus`

Same correction, on `description`, `metadata.description_en`, `metadata.description_fr`
(archive field `description_en_pre_2026_08_16` untouched).

**BEFORE (en)**
> Radical libertarianism (freedom is the primary ontological principle) compatible with certain aspects of reality: the Stoic chain of physical causes, divine foreknowledge, ordered providence.

**AFTER (en)**
> Radical libertarianism (freedom is the primary ontological principle) compatible with certain determined aspects of reality (mit determinierten Aspekten der Wirklichkeit): divine foreknowledge, providential pre-arrangement, and reliable regularities of the world — expressly NOT the Stoic chain of physical causes, which Origen does not adopt: he retains the Stoic term εἱρμός but re-semanticizes it as a web (Gewebe) of interconnected free decisions of free beings, ordered by a God who is himself free (Fürst 2022, 286-288).

**BEFORE (fr)**
> … compatible avec des aspects déterminés de la réalité : chaîne stoïcienne des causes physiques, préscience divine, providence ordonnée.

**AFTER (fr)** — same replacement as §2 (fr).

Suspended-verdict paragraph appended to all three fields, as in §2.

`metadata.verified_reference` here already read `Fürst, …` (no `C. M.`), untouched.

---

## 4. `passage_origen_de_orat_6` — academic-integrity correction

### `description`

**BEFORE**
> Crucial distinction for reconciling foreknowledge and freedom. Greek (GCS 3 Koetschau): [6.1] Ἡ πρόγνωσις τοῦ θεοῦ οὐκ ἔστιν αἰτία πάντων τῶν ἐσομένων καὶ τῶν ἀπ' αὐτεξουσίου κινήσεως ἡμῶν ἀποβησομένων. ("GOD'S PRESCIENCE IS NOT THE CAUSE of all future events or of those resulting from our self-determining motion.") [6.2] οὐχ ὅτι γινώσκει ὁ θεὸς τὸ ἐσόμενον, διὰ τοῦτο καὶ ἔσται· ἀλλ' ὅτι ἐσόμενόν ἐστι, διὰ τοῦτο γινώσκεται ὑπὸ τοῦ θεοῦ πρὸ τοῦ γενέσθαι. ("It is NOT BECAUSE God knows that it will be, BUT BECAUSE it will be, that God knows it beforehand.") Astronomer analogy: predicting eclipse doesn't cause it. Source: GCS 3.

Both Greek runs: **0 TLG hits**. The "astronomer analogy" sentence has no support in
*De oratione* 6,3 either and was dropped with the rest.

**AFTER**
> Origen's classic statement that divine foreknowledge is not the cause of what comes to be: God pre-arranges everything in accordance with what he has foreseen of each act that is up to us (τὸ ἐφ' ἡμῖν), and the εἱρμός of future events follows, without his foreknowledge being the cause of them. Greek (Origen, De oratione 6,3 = GCS Orig. 2, p. 313 Koetschau; verbatim from TLG E tlg2042.008): «καὶ ἐν πᾶσιν, οἷς προδιατάσσεται ὁ θεὸς ἀκολούθως οἷς ἑώρακε περὶ ἑκάστου ἔργου τῶν ἐφ' ἡμῖν, προδιατέτακται κατ' ἀξίαν ἑκάστῳ κινήματι τῶν ἐφ' ἡμῖν τὸ καὶ ἀπὸ τῆς προνοίας αὐτῷ ἀπαντησόμενον ἔτι δὲ καὶ κατὰ τὸν εἱρμὸν τῶν ἐσομένων συμβησόμενον, οὐχὶ τῆς προγνώσεως τοῦ θεοῦ αἰτίας γινομένης τοῖς ἐσομένοις πᾶσι καὶ ἐκ τοῦ ἐφ' ἡμῖν κατὰ τὴν ὁρμὴν ἡμῶν ἐνεργηθησομένοις. εἰ γὰρ καὶ καθ' ὑπόθεσιν μὴ γινώσκοι ὁ θεὸς τὰ ἐσόμενα, οὐ παρὰ τοῦτο ἀπολοῦμεν τὸ τάδε τινὰ ἐνεργήσειν καὶ τάδε θελήσειν·» English: "God's foreknowledge is not the cause of all the things that will be, including those effected from what is up to us according to our impulse; even if, per hypothesis, God did not know the future, we would not thereby lose the power to act and to will."

### metadata

| Key | BEFORE | AFTER |
|---|---|---|
| `work_title` | `Contra Celsum` | `De Oratione` |
| `reference` | `De Orat. 6` | `De Orat. 6,3` |
| `source_verified` | `GCS 3 Koetschau` | `GCS Orig. 2, p. 313 (Koetschau 1899); Greek copied byte-exact from the local TLG E extract TLG_tlg2042_De_oratione_6_3.txt on 2026-08-16` |
| `external_edition` | `GCS 3 (Koetschau 1899): Origenes Werke II - De Oratione` | `GCS Orig. 2 (Koetschau 1899): Origenes Werke II, De oratione, p. 313` |
| `greek_text_excerpt` | `οὐχ ὅτι γινώσκει... διὰ τοῦτο ἔσται, ἀλλ' ὅτι ἐσόμενόν ἐστι, διὰ τοῦτο γινώσκεται` (recomposed) | `οὐχὶ τῆς προγνώσεως τοῦ θεοῦ αἰτίας γινομένης τοῖς ἐσομένοις πᾶσι` (verbatim) |
| `key_terms` | `["πρόγνωσις", "αἰτία", "ἀπ' αὐτεξουσίου κινήσεως"]` | `["πρόγνωσις", "εἱρμός", "τὸ ἐφ' ἡμῖν", "ὁρμή"]` |
| `doxographical_source` | `heuristic` | `scholarly_critical_edition` |
| `doxographical_confidence` | `medium` | `high` |
| `note` | *(absent)* | `For the reversed order of knowing ('not because it is known does it happen, but because it will happen it is known') see Philoc. 23,8 = in Gen. frg. D 7,8 (OWD 1/1, 84) — do not attribute that sentence to De oratione.` |
| `citation_verdict` | *(absent)* | `corrected` |
| `citation_verified` | *(absent)* | `true` |
| `verified_reference` | *(absent)* | `Origen, De oratione 6,3 (GCS Orig. 2, 313 Koetschau) = TLG tlg2042.008; Greek re-verified 2026-08-16 against the local TLG E corpus with two distinctive spans (1 hit each, Origen only). Cited for this exact point by Fürst, Wege zur Freiheit (2022) 283 n. 101 and 287 n. 107.` |
| `removed_unattested_text` | *(absent)* | archive object: `reason`, `removed_on`, `runs` (the 3 unattested runs), `previous_description`, `replaced_by` |

`cts_urn` (`urn:cts:greekLit:tlg2042.tlg008`), `language`, `text_status`,
`database_verified`, `acquisition_needed` left as they were — the passage is still not
ingested into `data/corpus/passages.jsonl`.

`verification_notes` records the whole correction, including the "Contra Celsum" fix and
the *Philocalia* 23,8 mis-attribution.

---

## 5. `passage_origen_de_orat_6_en` — corrupted twin restored

The audit's description was correct: the node's `description` was the Greek node's text with
the Greek runs stripped out by an earlier pass, leaving punctuation debris.

**BEFORE**
> Crucial distinction for reconciling foreknowledge and freedom. Greek (GCS 3 Koetschau): [6.1] ' . ("GOD'S PRESCIENCE IS NOT THE CAUSE of all future events or of those resulting from our self-determining motion.") [6.2] , · ' , . ("It is NOT BECAUSE God knows that it will be, BUT BECAUSE it will be, that God knows it beforehand.") Astronomer analogy: predicting eclipse doesn't cause it. Source: GCS 3.

**AFTER**
> God's foreknowledge is not the cause of all the things that will be, including those effected from what is up to us according to our impulse; even if, per hypothesis, God did not know the future, we would not thereby lose the power to act and to will. (Origen, De oratione 6,3 = GCS Orig. 2, p. 313 Koetschau; English rendering of the verbatim Greek restored to passage_origen_de_orat_6 on 2026-08-16.)

| Key | BEFORE | AFTER |
|---|---|---|
| `work_title` | `""` | `De Oratione` |
| `source_language` | `unknown` | `grc` |
| `translation_source` | `AI batch: claude-opus-4-6` | `Re-rendered 2026-08-16 from the verbatim Greek of De oratione 6,3 (GCS Orig. 2, 313) restored to passage_origen_de_orat_6. Supersedes the claude-opus-4-6 batch translation, whose stored text had been reduced to punctuation debris by an earlier Greek-stripping pass.` |
| `citation_verdict` / `citation_verified` | *(absent)* | `corrected` / `true` |
| `removed_unattested_text` | *(absent)* | archive of the debris description |

**Edges checked, none deleted.** The node participates in 3 edges, all still coherent:
`passage_origen_de_orat_6 —has_translation→ passage_origen_de_orat_6_en`,
`passage_origen_de_orat_6_en —translation_of→ passage_origen_de_orat_6`,
`—authored_by→ person_origen_alexandria_185_254ce_s9t0u1v2`, `—part_of→ work_origen_de_oratione`.
(The Greek node itself carries `cites_primary_source` / `grounded_in` / `evidenced_by` /
`employs` / `source_for` edges — all left intact, and all still supported by the restored
text, which *is* the foreknowledge-is-not-a-cause statement they cite.)

---

## 6. `passage_origen_philocalia_21_23` — label honesty

**BEFORE (label)**
> Origen, Philocalia 21.23: Universalist horizon — Greek text (Philocalia 21.23) [= De Princ. III.1.23]

**AFTER (label)**
> Origen, Philocalia 21.23: Universalist horizon — French translation (SC 268 Crouzel–Simonetti); Greek not yet ingested for this section [= De Princ. III.1.23]

| Key | BEFORE | AFTER |
|---|---|---|
| `section_label` | `Universalist horizon — Greek text (Philocalia 21.23)` | `Universalist horizon — French translation (SC 268 Crouzel–Simonetti); Greek not yet ingested for this section` |
| `language` | `grc` | `fra` |
| `language_note` | `Greek text (Philocalia is the principal Greek witness for De Princ III.1)` | `The stored payload is the French translation of Philocalia 21.23 (= De Princ. III 1,23) printed in SC 268 (Crouzel–Simonetti, 'Extraits grecs' companion volume), NOT Greek. Philocalia 21 remains the principal Greek witness for De Princ. III 1, and the Greek of §23 is available in the same local SC 268 extract file, but it has not been ingested into this node.` |
| `citation_verdict` / `citation_verified` | *(absent)* | `corrected` / `true` |

`description` (the French text itself) untouched. Edition metadata (`principal_edition`,
`junod_sc226_*`, Robinson sigla…) untouched.

**Follow-up left open**: ingest the Greek of *Philocalia* 21.23 from
`SC268_Origenes_Traite_des_Principes_Extraits_grecs_livre_3_source.txt`
(`[liv.: 3, chap.: 1, par.: 23]`, `--- SOURCE ---` block) and either add it to this node or
create a sibling Greek node.

---

## Validation

| Check | Result |
|---|---|
| `nodes.jsonl` reparse | **19 992 lines, 19 992 parsed, 0 errors** — count unchanged |
| `git diff --stat data/kg/nodes.jsonl` | 6 lines modified (6 nodes) |
| Applier re-run (`--dry-run`) | **no-op** — all 6 nodes `[STAMPED]`, 0 further edits |
| `scripts/check_greek_gate.py` (changed scope, pre-commit default) | **OK** — "no Greek runs in scope" (the gate skips `type == "passage"` nodes by design; the three non-passage nodes touched contain only sub-threshold runs, `εἱρμός` = 6 chars < `MIN_CHARS` 18) |
| New De oratione Greek, forced through the gate's own `extract_runs` + `tlg_attested` | **PASS** — single 491-char run, `tlg_attested = True`. No allowlist entry needed or added. |
| `scripts/check_greek_gate.py --all` | 2 failures — `argument_origen_witness_diss_problem4_angelic_knowledge_amand1945` and `person_ignatius_antioch_d110`, both `[tlg_only]`. **Pre-existing**, unrelated to these nodes, not touched here. |
| `scripts/check_citations_gate.py` | **OK** (208 verified references in manifest) |
| `scripts/audit_structural.py` before (HEAD nodes.jsonl) | `uncited_claim_node 1381 / cts_urn_format 934 / duplicate_node_candidate 6` — **TOTAL 2321** |
| `scripts/audit_structural.py` after | `uncited_claim_node 1381 / cts_urn_format 934 / duplicate_node_candidate 6` — **TOTAL 2321** → **no new findings** |

Files touched:

- `data/kg/nodes.jsonl` (6 node lines)
- `scripts/apply_2026_08_16_furst_deoratione_corrections.py` (new)
- `scripts/data_2026_08_16_furst_deoratione_corrections.py` (new)
- `data/audit/2026-08-16_furst_deoratione_corrections.md` (this file)

Not committed.
