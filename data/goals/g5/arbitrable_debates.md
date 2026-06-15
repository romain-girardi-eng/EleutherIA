# G5 — Which debates can EleutherIA's primary-text graph ARBITRATE?

A debate is **arbitrable** by the corpus when the scholars' disagreement turns on a *philological / attestational* fact that the primary-text graph already holds (or can hold) — a word's presence/absence in a critical edition, a passage's actual claim, a cross-reference — rather than on an *interpretive* judgement that no amount of text settles. The model is the **Amand–Carneades precedent**: a contested attribution decided by checking what the ancient text actually says against the corpus.

**Honest limit up front:** most of G5 is *interpretive*, not attestational. Whether *eph' hēmin* "is" free will, whether Alexander's libertarianism is "coherent", whether Augustine "invented" the will — these are conceptual verdicts. The corpus cannot adjudicate them; it can only (a) supply the shared evidentiary base all sides already accept, and (b) settle the *factual sub-claims* the interpretive disputes rest on. Where it can do (b), the debate is **partly arbitrable**: the corpus removes a factual disagreement, narrowing the interpretive one without closing it. All positions remain attributed.

---

## ARBITRABLE (factual sub-claim the corpus can settle)

### D-2 — Where and when does *autexousion* first appear, and does it supersede *eph' hēmin*?
**Disagreement:** first-technical dating (Labarrière/Gauthier: Epictetus; Bonhöffer/Harl: Musonius; Telfer et al.: Chrysippus/Zeno via SVF II.975 — Bobzien disputes). Equation timing (Eliasson's 3 stages → synonymy in Nemesius).
**Why arbitrable:** this is pure attestation — a *Wortgeschichte*. The TLG-E local corpus (`scripts/tlg_search.py`, accent-insensitive whole-corpus Greek attestation) can produce the actual chronology of αὐτεξούσ- and ἐφ' ἡμῖν tokens.
**Decisive evidence / method:**
1. Run `tlg_search.py` for αὐτεξουσ* across the corpus → first datable occurrences (test the Diodorus Siculus 19.105.4 claim, Musonius fr. 12/16, Epictetus *Diss.* II.2.3 / IV.1.56–100, the disputed Hippolytus *Haer.* 1.21.2 = SVF II.975 Zeno/Chrysippus attribution).
2. Tabulate αὐτεξούσιον vs ἐφ' ἡμῖν frequency by author/century → tests Bobzien's "supersedes from late 2nd c., synonymous by Nemesius" and Eliasson's 3-stage scheme directly.
3. Check Nemesius *De nat. hom.* ch. 39 (311.7 Morani) for the title/text co-use → corpus passage if ingested; else flag `needs_text_ingestion` after checking the DOCTORAT disk.
**Settles:** the dating sub-claim (b) of the Christianization consensus. **Does NOT settle:** whether the term *means* "free will" (interpretive).
**Edges/nodes to add:** `attested_in` edges from a `concept_autexousion` node to the first-occurrence passages, with century; this is genuinely new graph value.

### D-2b — Does Origen's *De princ.* III.1 define freedom via *eph' hēmin* while titled *Peri autexousiou*?
**Disagreement:** Frede's specific philological claim (title = *autexousion*, body defines via *eph' hēmin*, "proceeds along standard Stoic lines") underpins his "transmitter not inventor" reading; Fürst's "first systematic libertarian" reading leans on *In Hier. hom.* 18,3 (τὸ γὰρ αὐτεξούσιον ἐλεύθερόν ἐστι).
**Why arbitrable:** both are checkable text facts. The Greek of *De princ.* III.1 survives in **Philocalia 21–27** — and the library holds **SC 226 (Junod 1976)** + the verified `Philocalia.txt` (Robinson 1893 OCR, confirmed in MEMORY). *In Hier. hom.* 18,3 = GCS Orig. 32, 154.
**Decisive evidence / method:**
1. Read Philocalia 21 (= *De princ.* III.1.1) from SC 226 / verified `Philocalia.txt`; confirm the opening defines freedom with ἐφ' ἡμῖν and the treatise title is περὶ αὐτεξουσίου. → directly corroborates or refutes Frede p.112–113.
2. Locate *In Hier. hom.* 18,3 (check DOCTORAT SC Jérémie volume; else GCS) for the verbatim τὸ γὰρ αὐτεξούσιον ἐλεύθερόν ἐστι → grounds Fürst p.178.
3. Compare the *eph' hēmin*/*autexousion* token distribution within III.1 against a Stoic handbook locus (e.g. the Epictetus *Diss.* IV.1 cluster) → tests "could have been taken straight from a late Stoic handbook".
**Settles:** the *textual* premises both camps share. **Does NOT settle:** "transmitter vs systematic inventor" (interpretive — same text, rival weightings).

### D/C — Does Alexander *De fato* 192.22ff actually assert "same circumstances, choose otherwise"? Does he suppress Aristotle's "for the most part"?
**Disagreement:** Bobzien (192.22 = "same causes, same effects" determinism he opposes), M. Frede (192.22ff = the "ability to choose otherwise in the very same circumstances" he calls incoherent), Donini (the *De Fato* never mentions ἐπὶ τὸ πολύ / *hopoter' etyche*, unlike the *In An. Pr.* commentary).
**Why arbitrable:** Donini's claim in particular is a **negative attestation** — "Alexander never mentions 'for the most part' in *De Fato* chs. XI–XII" — exactly the kind of presence/absence the corpus checks.
**Decisive evidence / method:**
1. Corpus passages `passage_alex_fat_11`, `_12`, `_22` already exist (Bruns chapter-numbered). Search them for ἐπὶ τὸ πολύ / ὡς ἐπὶ τὸ πολύ / ὁπότερ' ἔτυχεν → confirm/refute Donini's "never mentions".
2. Compare against Alexander *In An. Pr.* 162.31–163.7 (ingest from CAG if absent) where Donini says the frequencies *are* present → the contrast is the whole of his thesis.
3. Read `passage_alex_fat_22` (Bruns 192.18–24) verbatim → adjudicate whether 192.22 states the determinist principle (Bobzien) or the do-otherwise requirement (Frede); likely both sentences are present and the scholars cite adjacent lines — the corpus shows *which line says what*.
**Settles:** Donini's negative-attestation thesis and the Bobzien/Frede citation-locus question. **Does NOT settle:** "coherent or not", "fair trial or not" (interpretive).

### A/D — Does Cleanthes' *Hymn to Zeus* contain a "free will" claim?
**Disagreement:** Inwood (the "without you nothing comes to be" lines are NOT autonomous free will; "without you" = normative deviation from Right Reason) vs the older reading he rebuts.
**Why arbitrable:** the *Hymn* is short, fixed text (von Arnim/Thom edition); the dispute is over what 4 lines say.
**Decisive evidence / method:** ingest/verify the *Hymn* (SVF I.537 / Thom 2005) if not already a corpus passage; read the relevant lines verbatim; the claim "bad men are not exempt from the causal chain" is decidable from the text + grammar (πλὴν ὁπόσα ῥέζουσι κακοί …). **Settles:** whether the text grammatically supports a libertarian-exemption reading. **Does NOT settle:** the broader "did Stoics have volition" question (interpretive).

### B — Does Aristotle use *boulēsis* as a third element beyond belief and desire (Irwin/Aquinas), and does *eph' hēmin* in *NE* III read as two-sided?
**Why partly arbitrable:** Bobzien's specific claim that *NE* 1113b5–8 is two-sided-but-determinism-neutral, and Irwin's that *boulēsis* is rational desire, are both anchored to a single short passage already citable in the corpus (Aristotle *NE* III.5).
**Method:** read *NE* 1113b3–14 (the cluster Labarrière notes has "seven occurrences of *eph' hēmin* in eight lines") verbatim; the corpus can display exactly what is and isn't said. **Settles:** the textual base (the passage is two-sided; *boulēsis* is listed alongside *prohairesis*). **Does NOT settle:** whether that *amounts to* a concept of will (Irwin yes / Frede no / Dihle no) — the textbook interpretive impasse.

---

## UNDERDETERMINED (genuinely not arbitrable by the corpus)

These turn on conceptual criteria external to any ancient text. The corpus furnishes the evidence everyone already cites; it cannot referee the verdict.

- **A — "Did the early Stoa have *free will*?"** Near-consensus NO, but the residual Bobzien⟂Frede split (does a genuine free will emerge *within* Stoicism with Epictetus, or only inadvertently in Alexander?) is a judgement about what *counts* as "a free will". Same Epictetus *Diss.* 4.1 text, opposite verdicts. **Underdetermined.**
- **B — "Who invented the will?"** The five-pole disagreement (Dihle/Augustine, Frede/Epictetus, Fürst/Origen, Kahn/trajectory, Irwin/Aristotle) rests on *different definitions of "will"* (voluntarist vs rationalist; will vs free will; four-strand cluster vs single faculty). The KG node correctly marks the whole frame contested. The corpus can date terms and verify texts (see D-2, D-2b) but cannot decide whose *criterion* is right. **Underdetermined** at the level of the headline question; **partly arbitrable** at the sub-claims.
- **C — "Is Alexander a *coherent* libertarian / did he *establish* it?"** Sharples "does not really solve it", M. Frede "hopeless tangle", D. Frede "not a fair trial", Donini "distortion", Ramelli "robust source" — these are assessments of philosophical cogency and polemical intent. The corpus settles *what Alexander wrote* (D/C above) and *whether Origen could have read him* (attestation of the ἦν ποτε ὅτε οὐκ ἦν formula in both — checkable!), but not whether his argument *works*. **Underdetermined** on coherence; **partly arbitrable** on the textual and influence sub-facts.
- **Sorabji ⟂ Frede (four strands in Epictetus?)** Partly checkable (does Epictetus deploy "will power" / perversion-by-pride vocabulary? — a TLG attestation task), but "do the four strands form a *cluster*" is a Gestalt judgement. **Mostly underdetermined.**

---

## One genuinely Amand-style arbitration the corpus can deliver now

**Ramelli's influence claim (Debate C):** "the expression ἦν ποτε ὅτε οὐκ ἦν was used for the first time exactly by Alexander and Origen." This is a *pure attestation* claim of the Amand–Carneades type — checkable against TLG-E (`tlg_search.py` for ἦν ποτε ὅτε οὐκ ἦν) and the Alexander + Origen corpus passages. If the phrase is attested in Alexander *before* Origen and nowhere earlier, it materially supports Ramelli's "Alexander as source of Origen" against Bobzien's "dead-end" — without any interpretive leap. **Recommended first arbitration to run.** Method: whole-corpus search → list every occurrence with author/date → build `attested_in` / `precedes` edges; report the chronology verbatim.

---

## Summary

| Debate | Headline question | Verdict | Decisive corpus evidence |
|---|---|---|---|
| **A** Stoic free will | Did early Stoa have free will? | **Underdetermined** (interpretive); Cleanthes *Hymn* sub-claim arbitrable | *Hymn to Zeus* lines (SVF I.537); Cic. *De fato* 39–44 |
| **B** Origins of the will | Who invented the will? | **Underdetermined** headline; **arbitrable** sub-claims (term-dating, Aristotle *NE* III text) | TLG-E αὐτεξουσ* chronology; *NE* 1113b3–14 |
| **C** Alexander libertarian | Coherent libertarian? Source of Origen? | **Underdetermined** on coherence; **arbitrable** on text + influence | `passage_alex_fat_11/12/22`; ἦν ποτε ὅτε οὐκ ἦν attestation |
| **D** *eph'hēmin*/*autexousion* | Meaning + Greek→Christian shift | **Arbitrable** (attestational): term origin, supersession, Origen *De princ.* III.1 wording | `tlg_search.py` αὐτεξουσ* / ἐφ' ἡμῖν; Philocalia 21 (SC 226); Nemesius 39 |

**Bottom line:** Debate **D** is the most arbitrable (it is largely a *Wortgeschichte*, and the local TLG-E + DOCTORAT corpus already hold the evidence). Debates **B** and **C** are arbitrable *only at their factual sub-claims*; their headline interpretive verdicts are underdetermined. Debate **A**'s headline is underdetermined; one ancient locus (Cleanthes' *Hymn*) is arbitrable. The single highest-value, immediately runnable arbitration is **Ramelli's ἦν ποτε ὅτε οὐκ ἦν priority claim** (Amand-style, pure attestation).
