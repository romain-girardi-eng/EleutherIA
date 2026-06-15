# CORRECTIONS_VS_QUICKPASS — precise diff of the fast pass against the deep re-verification

**Baseline corrected:** `data/goals/g5/debate_map.md` (the quick pass) + its companion `positions_*.jsonl` and `arbitrable_debates.md`, where flagged.
**Authority:** the deep dossiers `read_*.md` and the per-debate audits `verified_A–E.md` in this directory, re-checked for the highest-stakes anchors against the critical editions / extractions themselves.

**Headline finding:** the quick pass is **substantively sound on every scholar's stance** — *no position was assigned to the wrong scholar* and *no modern label was asserted as historical fact* (all stay attributed). The defects are: recurring **line-number-as-page** citation slips, a few **wrong/imprecise pages**, two **ASSERT-vs-REPORT overstatements**, several **omitted positions and one omitted scholar each in A and B/D**, and **one dossier (not the map) that read the wrong book**. Severity tags: 🔴 misattribution/overstatement of substance · 🟠 wrong page/locus · 🟡 citation hygiene / under-coverage · 🟢 confirmed-correct (no change).

---

## A. Misattributions of a *stance* to the wrong scholar

**NONE found in any of the five debates.** Every pole/position is genuinely held by the named scholar on the cited (now corrected) page. This is the single most reassuring result of the deep read.

The one *near-misattribution risk* is pre-emptive, in Debate E: **never cite Amand in support of Ramelli's "Alexander → Origen" priority** — Amand routes both back to Carneades and is explicit (p.586) he cannot decide whether Alexander even reproduces Carneades. They are neighbouring, not aligned. (Currently NOT conflated in the corpus; flagged so a future Debate-E build does not.) 🔴 *(would-be major if introduced)*

---

## B. Overstatements & ASSERT-vs-REPORT corrections (substance)

**[B-DFrede] 🔴 D. Frede 1982 — "coins *katēnankasmenōs*" is WRONG.** (Debate C)
- Fast pass: parenthetical "(… coins *katēnankasmenōs*)".
- Truth (p.288): she says Alexander "repeatedly **uses**" the adverb (loci 185,15; 190,8; 191,12; 200,2; 206,6) and explicitly **leaves its origin open**: "even if the Stoics used the term … and it is not Alexander's addition." She neither asserts a coinage nor that it is his neologism.
- **Fix:** "coins *katēnankasmenōs*" → "repeatedly **uses** *katēnankasmenōs* (origin left open)." This is a genuine REPORT-as-ASSERT inflation.

**[B-Voelke] 🔴 Voelke 1973 — "proto" understates + "no OCR" is false.** (Debate A)
- Fast pass annotation: "image-scan PDF, no OCR; quote null" + classifies Voelke as "proto."
- Truth: the PDF is OCR-readable throughout (the dossier transcribes ~10 verbatim French passages); and Voelke argues for a **full, worked-out** *idée de volonté* in the early Stoa ("la raison est volonté," p.7), explicitly NOT an anticipation — his target is precisely the "intellectualism-ignoring-will" reading.
- **Fix:** delete "no OCR / quote null"; relabel "proto" → "FOR volition (full, not proto)."

**[B-Inwood] 🔴/🟠 Inwood 1985 — mis-associated with the *eph' hēmin* semantic argument.** (Debate A)
- Fast pass clusters Inwood with Bobzien's "one-sided/causative *eph' hēmin*" terminology.
- Truth: Inwood argues from the **criterion of responsibility** (assent vs do-otherwise), NOT from the etymological valence of *eph' hēmin* — the one-sided/two-sided distinction is Bobzien's 1998 coinage, thirteen years later. The convergence is real *at the level of conclusions only*.
- **Fix:** flag the convergence as retrospective/conclusion-level; note Inwood deploys Origen *De Princ.* III.1 as a *Stoic doxographic witness*, not as a philosopher of free will.

**[B-Salles] 🔴 Salles 2005 — "three compatibilist theories" mis-counts.** (Debate A)
- Fast pass: Salles identifies "three compatibilist theories of Chrysippus."
- Truth: Salles argues **T₂ is a purely modal/metaphysical theory, NOT a responsibility/compatibilist theory** (pp.82–89). Only **T₁ and T₃** are responsibility theories. He also frames the Epictetus chapter around the Normative Argument / precipitancy, not *eph' hēmin* semantics.
- **Fix:** "three compatibilist theories" → "two compatibilist responsibility theories (T₁, T₃) + one purely modal theory (T₂)"; re-label the Epictetus locus.

**[B-Brennan] 🔴 Brennan 2005 — two omissions + a misleading support-locus.** (Debate A)
- Fast pass lists only Brennan's compatibilism and puts the **"Idle Argument" in the support column** alongside the cylinder.
- Truth: ch. 16 (Lazy/Idle Argument) is where Brennan finds Chrysippus **fails** ("a surprising and disappointing failure," p.285) — it does NOT support the compatibilist reading. The map also OMITS the **"shrinking of the self"** developmental thesis (pp.292–294), Brennan's main original contribution.
- **Fix:** move the Idle Argument out of the support column (or mark it the *failure* locus); add (a) the Lazy-Argument failure verdict and (b) the self-shrinkage thesis.

**[B-S] 🟢 Sorabji "four strands" — DOSSIER error, MAP is correct.** (Debate B; the most serious *dossier*-level issue)
- The deep dossier `read_sorabji.md` raised a "CRITICAL FLAG" accusing the map of hanging the four-strands/anti-Frede thesis on the wrong work/date.
- **The dossier is wrong:** it deep-read **Sorabji 1980, *Necessity, Cause and Blame*** — a different book the map never cites. The map cites the **2017 Festschrift essay** ("Freedom and Will: Graeco-Roman Origins," *Selfhood and the Soul*, OUP), which exists locally and **does contain the four-strands thesis with the p.63 anchor correct** (four strands from p.54; the four Epictetus-hesitations to p.63).
- **Resolution:** map = VERIFIED, no change. **Retract the `read_sorabji.md` §0 critical flag.** (The 1980 book the dossier read is itself a legitimate Debate-A/Aristotle-indeterminism source — just not the source behind this Debate-B row.) One refinement: the JSONL verbatim anchor is the *editors' 3rd-person abstract*; for an ASSERT anchor prefer Sorabji's own p.62 sentence ("Epictetus does not mention the will power that is so important to Augustine").

---

## C. Wrong / imprecise pages and loci (🟠)

**[C-Frede-Alex] 🟠 M. Frede 2011 — "Alexander ancestor" page 99–100 → 100.** (Debates B & C)
- Fast pass cites the "ancestor … not able to provide a coherent account" verdict at "99–100."
- Truth: the load-bearing sentence is on **p. 100** (build-up begins p.99; the "two reasons" elaboration runs to p.101).
- **Fix:** cite **p. 100** (or 100–101 to include the elaboration). Off-by-one.

**[C-Inwood-pp] 🟠 Inwood 1985 — page ranges.** (Debate A)
- Cleanthes *Hymn* = **pp. 69–71**, not "66–70." Alexander *eph' hēmin* discussion = **pp. 88–91**, not "88–89."

**[C-Bobzien2001-gloss] 🟠 Bobzien 2001 — "*eph' hēmin* = *di' hēmōn*" is an imprecise gloss.** (Debates A & D)
- Bobzien's one-sided/causative term for Chrysippus is **παρ' ἡμᾶς / ἐξ ἡμῶν** (with γίγνεσθαι), NOT *di' hēmōn*; the two-sided/potestative pair is **ἐφ' ἡμῖν (with εἶναι)**.
- **Fix:** state the contrast as παρ' ἡμᾶς (one-sided) vs ἐφ' ἡμῖν (two-sided); tighten the definition locus to **pp. 281–285** (map folds it into "276–282").

**[C-Salles-Idle] 🟠 Salles 2005 — Idle/Lazy Argument locus.** (Debate A) — *De Fato* **28–29** (confatalia at 30); the Epictetus chapter is *prohairesis*/Normative Argument, not *eph' hēmin*.

**[C-Furst] 🟠 Fürst 2022 — load-bearing quote on the wrong page (page conflation).** (Debate B)
- Fast pass + JSONL put "Diese Wege zur Freiheit … von Origenes dann erstmals systematisch konzipiert wurde" on **p. 178**.
- Truth: that sentence falls after the printed "179" marker → it is on **p. 179**. Only the *christlicher Kompatibilismus* (a)–(d) quote is on **p. 178**.
- **Fix:** (a)–(d) compatibilism quote = p.178; "Origenes … erstmals systematisch konzipiert" = **p.179**.

**[C-Eliasson-fn] 🟠 Eliasson 2008 — footnote number.** (Debate D-ii) — synonymy/Nemesius datum is at **p.6 n.32**, NOT "6 n.23" (n.23 is the unrelated Christian-authors list). Add **p.9** for the three-stage statement in the running text.

**[C-Dihle-term] 🟠 Dihle 1982 — Aristotelian key term mislabelled.** (Debate B) — Dihle's decisive Aristotelian term is **προαίρεσις** (*NE* III), not *boulēsis* (secondary in his text).

**[C-AmandLoci] 🟠 Amand dossier — three downstream OCR locus slips.** (Debate E; dossier-level, not map)
- Witness #1 (Philo): canonical témoin locus is *Περὶ προνοίας* **I, 79–83** (Aucher I, 36–39), not the body-discussion range "I,77–88."
- Witness #2 (Alexander): the dossier silently corrected the OCR-corrupt witness-list line ("Περὶ προνοίας" dittographed) to *De Fato* — correct, but flag it as a *silent emendation of a corrupt source line*.
- Nemesius cross-ref: ch. **35** (PG 40, 741C), not "85" (a 3→8 OCR digit error; *De nat. hom.* has ~43 chapters).

---

## D. Citation hygiene — line-numbers mislabelled as printed pages (🟡)

A systematic class of slip: several rows cite `.md`/`.txt`/`.summary` **line offsets** as if they were printed pages.

- **[D-Bob98] Bobzien 1998** Debate-A/D rows: "375–412", "1504–1611" are `.md` **line numbers**. Printed pages: causative/potestative = **139–142**; ἐξουσία = **163–167**; Justin/Tatian-absence datum = **p.164 n.55**.
- **[D-Frede] Frede 2011** Debate-A row "ch. 2–6, esp. 2770–2773" uses `Frede_2011.summary.md` **line offsets**. The "first actual notion of a free will" sentence is printed **p.77**; will-from-assent = **pp.44–46**; *autexousion*/Justin = **pp.74–75**.
- **[D-Frede-Arist] Frede 2011** the Kahn-node "94–96" (re no will in Aristotle) are line offsets; the printed rebuttal is **pp.27–28**. **Do not port "94–96" into any citation.**
- **[D-Bob98-art] Bobzien 1998** Debate-D rows "165–167, 173–175" and "142–143" are pages of the **1998 *Phronesis* article**, which is **not extracted in the repo** → mark those rows **WEAK** for provenance, or re-tag to the 2001 monograph (synonymous=**p.330**, *eleutheria*-never-linked=**p.341**, Justin "earliest"=**p.345**, which ARE verified).

---

## E. Omissions — positions and scholars the fast pass missed

**[E-Blackson] 🟡 Debate A: Blackson omitted entirely.** Directly contests Frede's timeline from the *opposite* direction to Bobzien (the *early* Stoics probably already had a notion of a will). **Add as a "FOR (early-Stoa, contra Frede)" row, WEAK** as a consensus claim (his own conclusion is hedged "probably"). **Dating correction:** the dossier `verified_A.md` wrote "Blackson 2025"; the KG node `pub_blackson_epictetus_frede_argument` records **Apeiron 51(4), 2018** — the **2018** dating is authoritative.

**[E-Karamanolis] 🟡 Debates B & D: Karamanolis 2021 omitted entirely** (grep over `debate_map.md` = 0 hits). He is a primary B/D witness (POLE 2: Stoic/Epictetan origin, "with Bobzien and Frede against Dihle," ch.4 n.15; patristic *autexousion* swaps Stoic single-track for the Peripatetic two-sided conception). **Add to both B and D-ii.**

**[E-Sharples2008] 🟡 Debate C: Sharples' 2008 retrospective omitted.** The map captures only the 1983 stance. His mature, signed position is the **"accident/coincidence of determinism"** thesis + a **self-critique** of the 1983 "Laplacian" framing + broad **endorsement of Bobzien's "inadvertent" framework**. **Add a Sharples-2008 row.**

**[E-Donini-ch7] 🟡 Debate C: Donini presented as flatly "tendentious/distortion."** His *settled* (ch. VII, pp.165–176) verdict **rehabilitates** Alexander as "substantially consistent" on a two-class reading. **Add the ch. VII rehabilitation as a qualifier** — the map's single "distortion" row is one-sided.

**[E-Kahn-stale] 🟡 Debate B: Kahn row says page "null / not held locally."** Stale — the source is local and page-grounded **235–259**. Also the locus cell "Aristotle (*prohairesis*)" **inverts** Kahn's argument (he denies *prohairesis* is a will), and "Cicero/Lucretius/Seneca" flattens a *staged* argument (Lucretius = earliest *libera voluntas* p.248; Cicero = *hekousion*→*voluntarium* p.241; Seneca = later Latin parallel p.251ff).

**[E-DebateE] 🟡 Debate E never built.** The quick-pass map has Debates A–D only; the Carneadean-transmission material rests on a single source (Amand) + the distinct Ramelli flank. A future build should add an Amand position record + a `precedes`/`discusses` chain Carneades → {Philo, Alexander, Firmicus, Eusebius, Origen, Gregory, Chrysostom, Nemesius} grounded on the six témoins, keeping Amand and Ramelli separate.

---

## F. Confirmed-correct (🟢 no change — re-anchored against the source)

- **Sorabji 2017 four-strands row** (Debate B): map VERIFIED; the *dossier* erred (read the 1980 book). 
- **Frede KG data-flag** (`scholar_position_kahn_will_emerges_seneca_epictetus` rationale wrongly says Frede holds the will was "already present in Aristotle"): **flag is CORRECT** — Frede asserts the opposite (p.28); the "already in Aristotle" view is Irwin/Kenny's. Cite the rebuttal at **pp.27–28**, never "94–96."
- **Bobzien 1998** pp.135/139/142, **Salles** p.xiv, **Frede** p.77, **Bobzien 2001** pp.285/330/341/345, **Sharples 1983** pp.9/22, **Donini** pp.74–77, **D. Frede** pp.287–288 (locus 192.18), **Ramelli** pp.237–238, **Eliasson** pp.2/9/6n.32, **Karamanolis** pp.133/142, **Amand** pp.41/65–67/322/573/586: all quotes physically present on the cited pages, all stances the scholars' own committed claims (or correctly flagged as REPORT/HEDGE).
- **"Amand–Carneades precedent" as method label** in `arbitrable_debates.md`: fair distillation of Amand's ≥3/6 *règle de fer* (p.573). Keep.
- **Brennan "soft determinist," Sharples "libertarian," Bobzien "one-sided/two-sided," Karamanolis "Stoic compatibilism":** all correctly attributed as the scholars' OWN analytic vocabulary, never asserted as fact.

---

## Tally

| Class | Count | Where |
|---|---|---|
| 🔴 Substance overstatement / ASSERT-vs-REPORT | 5 | D. Frede "coins" (C); Voelke "proto"+"no OCR" (A); Inwood *eph'hēmin* mis-association (A); Salles "three compatibilist theories" (A); Brennan Idle-Argument-as-support + 2 omissions (A) |
| 🟠 Wrong/imprecise page or locus | 8 | Frede-Alex p.100 (B/C); Inwood pp. (A); Bobzien2001 gloss (A/D); Salles Idle locus (A); Fürst p.179 (B); Eliasson n.32 (D); Dihle προαίρεσις (B); Amand 3 OCR slips (E) |
| 🟡 Citation hygiene (line# as page) | 4 classes | Bobzien 1998 lines; Frede summary lines; Frede "94–96"; Bobzien-1998-article rows WEAK (D) |
| 🟡 Omission (position/scholar/debate) | 6 | Blackson (A); Karamanolis (B+D); Sharples 2008 (C); Donini ch.VII (C); Kahn stale-null (B); Debate E never built |
| 🔵 Dossier-level error (not the map) | 2 | `read_sorabji.md` read wrong book (B); Amand dossier OCR loci (E) |
| 🟢 Confirmed-correct, re-anchored | ~20 anchors | all 5 debates |

**Bottom line:** no stance was wrong and no label was de-attributed. The corrections are page-precision, two REPORT-as-ASSERT inflations (D. Frede "coins"; Brennan Idle-Argument-as-support), a handful of substance under-counts/omissions (Salles T₂; Brennan's two theses; Blackson, Karamanolis, Sharples-2008, Donini-ch.VII), and one dossier that adjudicated the wrong book.
