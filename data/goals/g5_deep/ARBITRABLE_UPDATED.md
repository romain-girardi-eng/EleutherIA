# ARBITRABLE_UPDATED — which G5 debates the corpus can arbitrate, after the deep read

Refines `data/goals/g5/arbitrable_debates.md` in light of the deep re-verification (`verified_A–E.md`, `read_*.md`). The framework is unchanged: a debate is **arbitrable** when the scholars' disagreement turns on a *philological / attestational* fact the primary-text graph holds (or can hold) — a word's presence/absence in a critical edition, a passage's actual claim, a cross-reference — on the model of the **Amand–Carneades precedent** (a contested attribution decided by checking the ancient text against the corpus).

**Honest limit, restated:** most of G5 is *interpretive*, not attestational. Whether *eph' hēmin* "is" free will, whether Alexander's libertarianism is "coherent," whether Augustine "invented" the will — these are conceptual verdicts no text settles. The corpus can (a) supply the shared evidentiary base all sides accept, and (b) settle the *factual sub-claims* the interpretive disputes rest on. The deep read **did not change any headline verdict**, but it **sharpened three sub-claims into runnable arbitrations** and **added two** (one in Debate A, one in Debate E) that the fast pass did not surface.

---

## What the deep read changed

1. **No headline verdict flipped.** A, B, C remain interpretively underdetermined; D remains the most arbitrable (it is largely a *Wortgeschichte*); A's Cleanthes-*Hymn* sub-claim and the Ramelli ἦν ποτε ὅτε οὐκ ἦν priority claim remain the cleanest Amand-style arbitrations.
2. **Debate A gains a new arbitrable sub-claim** via **Blackson** (omitted by the fast pass): his D-vs-E dispute with Frede turns partly on *what Epictetus actually says the carried-away person did wrong* — a readable-text question on specific Epictetus loci.
3. **Debate E is now first-class.** The fast pass never built it; the deep read confirms it rests on a single witness (Amand) + a distinct flank (Ramelli) and specifies the **six *textes témoins*** as concrete corpus targets, plus the Amand≠Ramelli guardrail.
4. **Two corpus *facts* the deep read pinned down** (so they no longer need arbitrating, only ingesting/anchoring): Bobzien's one-sided term is **παρ' ἡμᾶς** (not *di' hēmōn*); the patristic "earliest surviving" *eleuthera prohairesis* locus is **Justin *1 Apol.* 43 (80e)** per Bobzien 2001 p.345 — a datable token the TLG-E run in D-2 should confirm.

---

## ARBITRABLE (factual sub-claim the corpus can settle)

### D-2 — Where/when does *autexousion* first appear; does it supersede *eph' hēmin*? **[strongest — unchanged, now better targeted]**
**Disagreement:** first-technical dating (Labarrière/Gauthier: Epictetus; Bonhöffer/Harl: Musonius; Telfer et al.: Chrysippus/Zeno via SVF II.975 — Bobzien disputes). Equation timing (Eliasson's 3 stages → synonymy in Nemesius).
**Why arbitrable:** pure attestation — a *Wortgeschichte*. TLG-E (`scripts/tlg_search.py`) gives the actual chronology of αὐτεξούσ- and ἐφ' ἡμῖν tokens.
**Method:** (1) `tlg_search.py αὐτεξουσ*` → first datable occurrences (test Diodorus Siculus 19.105.4, Musonius fr.12/16, Epictetus *Diss.* II.2.3 / IV.1.56–100, the disputed Hippolytus *Haer.* = SVF II.975). (2) Tabulate αὐτεξούσιον vs ἐφ' ἡμῖν by author/century → tests Bobzien's "supersedes from late 2nd c., synonymous by Nemesius" + Eliasson's 3-stage scheme. (3) Check Nemesius *NH* 39 (311.7 Morani) for title/text co-use.
**Deep-read refinement:** also search **ἐλευθέρα προαίρεσις** to test Bobzien 2001 p.345 ("Justin *1 Apol.* 43 80e perhaps the earliest surviving evidence") and **ἐλευθερία τῆς προαιρέσεως** to test Frede p.74–75 (Tatian *Or.* 7.1 "the first person ever").
**Settles:** the dating sub-claim (b) of the Christianization consensus jointly asserted by Bobzien/Eliasson/Karamanolis. **Does NOT settle:** whether the term *means* "free will."

### D-2b — Does Origen's *De princ.* III.1 define freedom via *eph' hēmin* while titled *Peri autexousiou*? **[unchanged]**
**Disagreement:** Frede ("along standard Stoic lines," transmitter) vs Fürst (Origen = first systematic libertarian, leaning on *In Hier. hom.* 18,3 τὸ γὰρ αὐτεξούσιον ἐλεύθερόν ἐστι).
**Why arbitrable:** both are checkable text facts. The Greek of *De princ.* III.1 survives in **Philocalia 21–27** — local **SC 226 (Junod 1976)** + verified `Philocalia.txt` (Robinson 1893, MEMORY-confirmed). *In Hier. hom.* 18,3 = GCS Orig. 32, 154.
**Method:** (1) Read Philocalia 21 (= III.1.1): confirm the opening defines freedom with ἐφ' ἡμῖν and the title is περὶ αὐτεξουσίου → corroborates/refutes Frede p.112–113. (2) Locate *In Hier. hom.* 18,3 verbatim → grounds Fürst **p.178** (note: Fürst's "Origen first systematically conceived" sentence is **p.179**, per the deep-read page-split correction). (3) Compare token distribution within III.1 against an Epictetus *Diss.* IV.1 handbook locus.
**Settles:** the *textual* premises both camps share. **Does NOT settle:** "transmitter vs systematic inventor" (same text, rival weightings).

### D/C — Does Alexander *De fato* 192.22ff assert "same circumstances, choose otherwise"? Does he suppress Aristotle's "for the most part"? **[unchanged — Donini negative-attestation is the decisive item]**
**Disagreement:** Bobzien (192.22 = "same causes, same effects" determinism he opposes), M. Frede (192.22ff = the incoherent "ability to choose otherwise in the very same circumstances"), Donini (the *De Fato* never mentions ἐπὶ τὸ πολύ / *hopoter' etyche*, unlike *In An. Pr.* 162.31–163.7).
**Why arbitrable:** Donini's claim is a **negative attestation** — exactly the presence/absence the corpus checks.
**Method:** (1) Search `passage_alex_fat_11/12/22` for ἐπὶ τὸ πολύ / ὡς ἐπὶ τὸ πολύ / ὁπότερ' ἔτυχεν → confirm/refute Donini's "never mentions." (2) Compare against *In An. Pr.* 162.31–163.7 (ingest from CAG if absent). (3) Read `passage_alex_fat_22` (Bruns 192.18–24) verbatim → which line says the determinist principle (Bobzien) vs the do-otherwise requirement (Frede).
**Deep-read refinement:** Donini's verdict is **two-part** — ch. III "distortion" *and* ch. VII "substantially consistent" (two-class reading). The corpus arbitrates only the ch. III negative-attestation; the ch. VII rehabilitation is interpretive. Keep both.
**Settles:** Donini's negative-attestation thesis + the Bobzien/Frede citation-locus question. **Does NOT settle:** "coherent or not," "fair trial or not."

### A/D — Does Cleanthes' *Hymn to Zeus* contain a "free will" claim? **[unchanged]**
**Disagreement:** Inwood (the "without you nothing comes to be" lines are NOT autonomous free will; "without you" = normative deviation from Right Reason — pp.69–71, "this must be wrong") vs the older reading he rebuts.
**Why arbitrable:** the *Hymn* is short, fixed text (von Arnim/Thom); the dispute is over ~4 lines.
**Method:** ingest/verify the *Hymn* (SVF I.537 / Thom 2005) as a corpus passage; read the relevant lines verbatim; "bad men are not exempt from the causal chain" is decidable from text + grammar (πλὴν ὁπόσα ῥέζουσι κακοί …).
**Settles:** whether the text grammatically supports a libertarian-exemption reading. **Does NOT settle:** "did Stoics have volition" (interpretive).

### A — Epictetus on the carried-away person: did he err by *choosing to assent* (Frede's D) or by *failing to exercise the ability rightly* (Blackson's E)? **[NEW — surfaced by the deep read]**
**Disagreement:** Frede (proposition D: adults choose to assent) vs **Blackson** (proposition E: adults choose to exercise the ability to use impressions, assent downstream). Blackson (pp.90–92) claims Epictetus never says the carried-away person's error was *choosing to assent*, only that they failed to think rightly first.
**Why partly arbitrable:** this is a readable-text question about *what Epictetus predicates of the error* in specific, named loci — **Disc. II.18.23–26; Manual 34; Disc. I.28.2**. The corpus can display exactly whether the object of the faulted "choice" is assent or the prior exercise of the faculty.
**Method:** read the three loci verbatim (ingest from the Epictetus corpus if absent); check the grammatical object of the verbs of choosing/failing. If Epictetus consistently faults the *prior exercise* rather than the *assent*, the text favours Blackson's E (and his "early Stoics probably had it too" follows only by the further, interpretive, inference).
**Settles:** the textual base of the D-vs-E dispute. **Does NOT settle:** whether the early Stoics "probably believed E too" (Blackson's own hedge — an inference, not an attestation), nor whether E *amounts to* "a notion of a will."

### B — Does Aristotle use *boulēsis* as a third element, and is *eph' hēmin* in *NE* III two-sided? **[unchanged]**
**Why partly arbitrable:** Bobzien's claim that *NE* 1113b5–8 is two-sided-but-determinism-neutral, and Irwin's that *boulēsis* is rational desire, are both anchored to one short passage already citable (Arist. *NE* III.5).
**Method:** read *NE* 1113b3–14 verbatim (Labarrière's "seven occurrences of *eph' hēmin* in eight lines"); display what is and isn't said.
**Settles:** the textual base (the passage is two-sided; *boulēsis* is listed alongside *prohairesis*). **Does NOT settle:** whether that *amounts to* a concept of will (Irwin yes / Frede no / Dihle no) — the textbook impasse. **Deep-read fix:** Dihle's decisive Aristotelian term is **προαίρεσις**, not *boulēsis* — so the *boulēsis*-anchored sub-claim adjudicates Irwin/Bobzien, not Dihle.

### E — The six *textes témoins*: is the Carneadean moral anti-fatalist topos attested in ≥3 of them? **[NEW as a first-class arbitration]**
**Disagreement:** internal to Amand's reconstruction (his own ≥3/6 *règle de fer*, p.573) — but it is the *most* Amand-style of all, because Amand built it as an explicit attestation rule.
**Why arbitrable:** each témoin is a locatable critical-edition passage. The corpus can hold all six and check, argument-by-argument, whether each reconstructed reductio (abolish laws/courts; collapse virtue/vice; pointless praise-blame; sloth; ruin piety/prayer) clears the ≥3/6 bar.
**Method / targets (corpus ingest, then `discusses`/`precedes` edges):**
1. Philo, *Περὶ προνοίας* **I, 79–83** (Aucher I, 36–39).
2. Alexander, *De Fato* **16–20** (Bruns 186,13–191,2).
3. Firmicus Maternus, *Mathesis* I,2,5–11.
4. Eusebius, *PE* VI,6,4–21.
5. Chrysostom, Goth-hom. 6 (PG 63, 500–510).
6. ps.-Chrysostom, *De fato* V (PG 50, 765–768).
Confirmatory (not témoins): Bardesanes, Basil *Hex.* VI,7, **Nemesius *De nat. hom.* 35** (PG 40, 741C).
**Settles:** Amand's ≥3/6 attestation for each reconstructed argument (a genuinely checkable claim, the cleanest in G5). **Does NOT settle:** whether Carneades *invented* vs merely *sharpened* the topos (Amand himself hedges: "sinon inventée, du moins aiguisée," p.IX), nor whether Alexander reproduces Carneades verbatim ("impossible de décider," p.586).
**Guardrail:** keep **Amand (Carneades → all) and Ramelli (Alexander → Origen direct) separate**; do not let an Amand edge support Ramelli's priority.

### C/E — Ramelli's ἦν ποτε ὅτε οὐκ ἦν priority claim. **[unchanged — the single highest-value runnable arbitration]**
**Claim:** "the expression ἦν ποτε ὅτε οὐκ ἦν was used for the first time exactly by Alexander and Origen" (Ramelli 2014 p.238).
**Why arbitrable:** a *pure attestation* claim of the Amand–Carneades type.
**Method:** whole-corpus TLG-E search (`tlg_search.py ἦν ποτε ὅτε οὐκ ἦν`) → list every occurrence with author/date. If attested in Alexander *before* Origen and nowhere earlier, it materially supports Ramelli's "Alexander as source" against Bobzien's "dead-end" — without interpretive leap.
**Settles:** the priority/attestation fact. **Does NOT settle:** whether Alexander's argument *works* (coherence — interpretive).

---

## UNDERDETERMINED (genuinely not arbitrable by the corpus)

- **A — "Did the early Stoa have *free will*?"** Near-consensus NO; the residual **Bobzien ⟂ Frede** split (genuine free will *within* Stoicism with Epictetus, or only inadvertently in Alexander?) is a judgement about what *counts* as "a free will" — same Epictetus *Disc.* 4.1 text, opposite verdicts. **Underdetermined.** (The new Blackson D-vs-E item arbitrates a *textual sub-fact*, not the headline.)
- **B — "Who invented the will?"** The now-seven-witness disagreement (Dihle/Augustine, Frede/Epictetus, Sorabji/Augustine-four-strands, Fürst/Origen, Kahn/trajectory, Irwin/Aristotle, Karamanolis/Stoic-import) rests on *different definitions of "will"*. The corpus dates terms and verifies texts (D-2, D-2b, B) but cannot decide whose *criterion* is right. **Underdetermined** headline; **partly arbitrable** sub-claims.
- **C — "Is Alexander a *coherent* libertarian / did he *establish* it?"** Sharples "does not really solve it," M. Frede "hopeless tangle," D. Frede "not a fair trial," Donini ch.III "distortion" (vs ch.VII "substantially consistent"), Ramelli "robust source," Sharples 2008 "accident" — assessments of cogency and polemical intent. The corpus settles *what Alexander wrote* (D/C) and *whether Origen could have read him* (ἦν ποτε ὅτε οὐκ ἦν), not whether the argument *works*. **Underdetermined** on coherence.
- **Sorabji ⟂ Frede (four strands in Epictetus?)** Partly checkable (does Epictetus deploy "will power" / perversion-by-pride vocabulary? — a TLG attestation task), but "do the four strands form a *cluster*" is a Gestalt judgement. **Mostly underdetermined.** (NB: the four-strands thesis is Sorabji **2017**, not the 1980 book the dossier mistakenly read.)

---

## Summary

| Debate | Headline question | Verdict | Decisive corpus evidence | Δ vs fast pass |
|---|---|---|---|---|
| **A** Stoic free will | Did early Stoa have free will? | **Underdetermined** (interp.); 2 sub-claims arbitrable | Cleanthes *Hymn* (SVF I.537); Epictetus *Disc.* II.18.23–26 / *Manual* 34 / *Disc.* I.28.2 (Blackson D-vs-E) | **+1 new arbitrable sub-claim (Blackson)** |
| **B** Origins of the will | Who invented the will? | **Underdetermined** headline; sub-claims arbitrable | TLG-E αὐτεξουσ* chronology; *NE* 1113b3–14 (note: *boulēsis* item adjudicates Irwin/Bobzien, not Dihle, whose term is προαίρεσις) | witnesses now 7 (+ Sorabji-2017, Karamanolis) |
| **C** Alexander libertarian | Coherent libertarian? Source of Origen? | **Underdetermined** on coherence; arbitrable on text + influence | `passage_alex_fat_11/12/22`; ἦν ποτε ὅτε οὐκ ἦν; *In An. Pr.* 162.31–163.7 | Donini now two-part (ch.III + ch.VII); Sharples-2008 added |
| **D** *eph'hēmin*/*autexousion* | Meaning + Greek→Christian shift | **Arbitrable** (attestational) | `tlg_search.py` αὐτεξουσ* / ἐφ' ἡμῖν / ἐλευθέρα προαίρεσις; Philocalia 21 (SC 226); Nemesius 39 | Justin *1 Apol.* 43(80e) + Tatian *Or.* 7.1 pinned as token tests; Karamanolis added |
| **E** Carneadean transmission | Identifiable & transmitted topos? | **Arbitrable** (Amand's own ≥3/6 rule) | the six *textes témoins* + Nemesius 35; ἦν ποτε ὅτε οὐκ ἦν (Ramelli flank, kept separate) | **now first-class** (fast pass had no Debate E) |

**Bottom line (unchanged in direction, sharper in detail):** Debate **D** is the most arbitrable (largely a *Wortgeschichte*; local TLG-E + DOCTORAT corpus hold the evidence). Debate **E** is now a first-class, genuinely Amand-style attestation task (the six témoins + the ≥3/6 rule). Debates **B** and **C** are arbitrable only at their factual sub-claims; their headline interpretive verdicts are underdetermined. Debate **A**'s headline is underdetermined; **two** ancient loci are now arbitrable (Cleanthes' *Hymn*; the Epictetus D-vs-E loci). The single highest-value, immediately runnable arbitration remains **Ramelli's ἦν ποτε ὅτε οὐκ ἦν priority claim** (pure attestation), with the **αὐτεξούσιον / ἐλευθέρα προαίρεσις chronology (D-2)** a close second.
