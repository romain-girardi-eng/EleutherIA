# Independent factual audit of the KG, corpus and public docs (2026-09-26)

Branch `claude/exciting-cerf-20fuqd`, from `cdda1ea`. Goal: find and remove
wrong facts — hallucinations, misquotations, wrong loci, wrong attributions,
wrong dates, garbled bibliography — at the standard of a scholarly edition.

## 1. Method

1. **Review.** 14 reviewers, one per slice: persons (496), works (247),
   publications (509, two halves), concepts/debates/quotes (303), syntheses
   (155), arguments (1,682, five slices), public docs and eval gold, a Latin
   quotation sweep (the repo has a Greek gate but no Latin one), my own
   chronology check of directional edges, and a machine locus check of
   passages against their editions (the Plotinus drift test of 2026-09-24,
   extended to every work with a reachable TEI).
2. **Adversarial verification.** Every finding went to a second reviewer
   whose brief was to refute it, against the primary text (PerseusDL
   canonical-greekLit / canonical-latinLit, OpenGreekAndLatin First1KGreek and
   csel-dev, fetched from GitHub), the corpus, or a bibliographic source.
   Verdicts: CONFIRMED, CONFIRMED_ADJUST (error real, correction rewritten),
   PLAUSIBLE, REJECTED.
3. **Application.** Only CONFIRMED items with a drop-in correction were
   applied, by two replayable, idempotent scripts built on
   `scripts/verification_2026_09_24_lib.py`. Every corrected sentence was then
   re-read in its context before writing; replacements that broke a sentence
   or left a now-false clause were rewritten.
4. **Gates** after every batch (§5).

Two of my own initial suspicions were refuted at step 2 and were never
counted: the "Phalaris reductio" is in Alexander, *De fato* 19 (Bruns 189),
and Alexander's chair is placed at Athens by the Aphrodisias inscription
(Chaniotis 2004).

## 2. Numbers

| | N |
|---|---|
| Raw findings | 582 (484 slice findings + 67 passage-locus + 31 Latin, of which 17 duplicated other slices) |
| Verified | 565 → CONFIRMED 342, CONFIRMED_ADJUST 214, PLAUSIBLE 5, REJECTED 4 |
| Decisions file | `2026-09-26_independent_audit_decisions.jsonl` (606 records incl. follow-ups) |
| KG nodes corrected | 567 (233 passages, 130 arguments, 55 persons, 44 works, 36 publications, 33 concepts, 20 syntheses, …) + 1 node created (`work_plato_crito`) |
| KG edges | 71 modified (12 reversed/relabelled, 59 `part_of` re-pointed), 9 withdrawn (quarantined), 1 added |
| Corpus rows | 84 modified (83 locus-parity twins, 1 invented Greek text replaced) |
| Docs / UI / eval files | 23 files |
| Greek allowlist | 16 runs added, each located verbatim in a named TEI |

Rejected (left as they were): Frede's methodological stance
(`scholarly_argument_frede_methodology_8`), "head of the Peripatetic school in
Athens" (`debate_alexander_stoics_determinism`), "Stoic = compatibilist" in
`docs/academic/METHODOLOGY.md`, and the edge *Orphic view of embodiment →
influences → Plotinus* (the node describes the ancient doctrine; *Enn.* IV.8.1).

## 3. Most serious errors found (all corrected)

**Invented or misattributed ancient text**
- Origen, *De oratione* 6: the corpus row (`passages.jsonl`) still served two
  Greek sentences labelled "GCS 3 Koetschau" that occur nowhere in Koetschau;
  the KG node had been cleaned on 2026-08-16, the corpus row had not.
- Frankfurt deck: a Greek sentence captioned "Chrysippus, *SVF* 2.952" exists
  in no edition (SVF II.952 is Cicero's Latin); replaced by Alexander, *De fato* 19.
- Augustine: "Noli ergo quaerere efficientem causam… non enim est efficiens,
  sed deficiens" certified "genuine, verbatim" for *DLA* II.20.54; the real
  sentence is *civ.* XII.7 "Nemo igitur quaerat…". Three more *DLA* "KEY
  passage" quotations were paraphrases.
- Boethius: "fatum ex providentiae fonte proficiscitur" (not his wording);
  "nunc fluens facit tempus, nunc stans facit aeternitatem" (Aquinas's
  paraphrase, not in Boethius); an ellipsis that dropped "Non enim" and turned
  a sentence about the non-eternal world into one about divine eternity.
- Plotinus: αὐθυπόστατος tagged "direct" from VI.8 (absent from the
  *Enneads*); "Sextus Empiricus' error" invented in the VI.8 summary.
- Justin: αὐτεξούσιον claimed, some "TLG-confirmed", at *1 Apol.* 43–44
  (absent from the whole *1 Apology*); a modern sentence on foreknowledge
  placed in Justin.
- Philo: "Philo writes Σκύθαι" in *De providentia* I, which survives only in
  Armenian.
- Alexander: Greek "quotations" absent from *De fato* (ἀξίωμα as dignity,
  αὐτεξούσιοι), a *Mantissa* phrase cited as *De fato*, and a dozen wrong
  chapter/page references.

**Wrong texts under wrong loci (passages)**
- 59 nodes "Plato, Φαίδων 43a–54e" hold the *Crito*; they now belong to a new
  `work_plato_crito`.
- Didache 1–6, Ps.-Plutarch *De fato* ("Fat. 4–19" were dossier numbers),
  Methodius ("PG 18.N" were chunk numbers), 51 Epictetus loci and labels (the
  opening of the *Enchiridion* was labelled *Discourses* I.1.1), Boethius
  book numbers, Augustine *civ.* V.XXXIII → V.XXIII.

**Wrong facts**
- Chrysippus said to accept premise (2) of the Master Argument (Epict. *Diss.*
  II.19: he rejects it); Diodorus's position inverted.
- Suárez given predestination *post praevisa merita* (he held *ante*).
- Eight Wikidata IDs pointing to other people (Spinoza → Locke, Cicero → the
  actress Frances Fisher, Mill → Marianne Faithfull, …).
- CTS URNs naming other works (Tertullian *Adv. Marc.* = stoa015 *De exh.
  cast.*; Cicero *De div.* = phi042 *Topica*; Augustine *De nat. boni* =
  stoa054 *De nat. et gratia*; Simplicius *In Ench.* = tlg4013.tlg001 *In De
  caelo*).
- Bayle "anticipating" Descartes (1641, before his birth) and attacking the
  *Théodicée* (1710, after his death).
- Chronologically impossible edges: Alexander's *De fato* "influences"
  Aristotle's *De int.*, *Met.* Θ and *EN*; Kant → Leibniz; Luther's *servum
  arbitrium* → Augustine; Molina → Scotus; Posidonius → Plato; Philo → Ben
  Sira; Cicero, Favorinus, Diogenianus → Carneades.
- Bibliography: reviewers made into authors (van der Eijk ×2), a dental
  journal for *Alpha Omega*, wrong years (Paczkowski, Tappen, Secord, Lekkas,
  Tzamalikos, Koch), wrong series, pages and volumes; the whole
  Destrée–Salles–Zingano 2014 chapter/page table.

**Public claims**
- "Every passage carries a SHA-256 hash" (≈3,900 of 23,027 do); "the gates run
  in pre-commit and CI" (the Greek gate is pre-commit only, on changed nodes,
  with a 1,759-run debt baseline); withdrawn "487 works / 69,277 passages /
  Hebrew and Arabic" figures; stale counts everywhere; an eval gold set whose
  query named *Strom.* II.6–15 while its answers are *Strom.* I.17.83–84; the
  README's flagship question presupposed Chrysippus answering Aristotle's
  critique of determinism (Cicero, *Fat.* 39 lists Aristotle among the
  necessitarians).

## 4. Commits

| Commit | Content |
|---|---|
| `4cc560a` | apply script |
| `79ab3d2` | 378 source-verified KG corrections, 21 edge decisions, Greek allowlist |
| `e1d0ff9` | passage-locus repairs (344 fields, Crito work node, corpus twins) |
| `6632fa5` | docs, UI copy (5 locales), eval gold, Origen corpus row, regenerated `data/stats.*` |
| `593f5f0` | 14 Latin/Greek quotations |
| `2cafd6f` | the same corrections carried into `description_fr` and parallel fields |

Replay: `PYTHONPATH=. python3 scripts/apply_2026_09_26_independent_audit.py --dry-run`
and `… apply_2026_09_26_passage_loci.py --dry-run` (both report 0 changes on
the current data). Removed records are in the `*_quarantine.jsonl` files;
before/after text of every change is in the decisions file and apply logs. Touched
nodes carry `metadata.independent_audit_2026_09_26` (finding ids only — the
wrong text is deliberately not copied back into the node).

## 5. Gates (final state)

- `check_corpus_invariants --strict`, `check_citations_gate`,
  `check_kg_work_id_uniqueness`, `check_kg_corpus_locus_parity --strict`
  (13,978 pairs), `check_kg_work_child_canonical`, `check_greek_gate`
  (changed-node mode): **OK**.
- `check_snapshot_passage_integrity --strict`: fails, as on `cdda1ea`, with the
  **identical** set of 66 violations.
- `check_greek_gate --all --no-tlg`: 55 unverified runs on `cdda1ea` → 50 now.
  The one Koch fragment that could not be verified (see §6) is among them.
- `check_ingestion_rules`: one more R2 warning — a real pre-existing duplicate
  made visible by the corrected URN (`passage_origen_pa_3_1_3` =
  `passage_origen_philocalia_21_3`, *De princ.* III.1.3 = Philocalia 21.3).

## 6. Open items for the owner

**Not applied because the permission system stopped the edit — GraphRAG prompts**
- `graphrag/src/eleutheria_graphrag/agents/graph_nodes.py` (worked example that
  every long answer imitates, ~l. 676–690). It inverts Chrysippus: Cicero,
  *Fat.* 41, "non hoc intellegi volumus: causis perfectis et principalibus,
  sed causis adiuvantibus et proximis". Proposed text:
  - l. 676: "Chrysippus's answer to the objection that fate removes assent from
    our power (Cicero, *De fato* 40–43) turns on a taxonomy of causes that"
  - l. 687: "Chrysippus's point is that the antecedent causes through which fate
    operates are the auxiliary and proximate ones (the impression), while the
    perfect and principal cause of assent is the agent's own nature [P4]." —
    deleting the rest of that sentence. The reply to the Lazy Argument is the
    co-fated argument (*Fat.* 28–30), not the cause distinction. Also mark as
    modern reconstruction, or delete, the Greek parentheticals (αἴτιον
    αὐτοτελὲς καὶ προηγούμενον / αἴτια συνεργὰ καὶ προσεχῆ), which the Latin
    [P3] cannot ground and which contradict the example's own τέλειον καὶ
    προηγούμενον.
- `graphrag/src/eleutheria_graphrag/services/methodology_agent.py` l. 78:
  "Frede yes, Bobzien no, Dihle later still" misstates Bobzien. Proposed:
  "Frede: yes, first with Epictetus; Bobzien: only late and inadvertently, in
  2nd-century CE Peripatetics such as Alexander, not in the early Stoa or
  Epicurus; Dihle: with Augustine".

**Composed Greek presented as Epictetus (critical, needs a rewrite)**
- 11 commentary nodes stored as passages (`passage_epict_69, 80, 87, 88, 89,
  90, 108, 109, 118, 119, 120`) list "Greek: • …" phrases that occur nowhere in
  Schenkl's *Discourses*, *Enchiridion* or fragments (e.g. τὸ φύσει ἀκόλουθον,
  δύναμις ἀγωνιστική, ὁ θεὸς πάντα ἐφορᾷ). This is exactly what
  `docs/ACADEMIC_INTEGRITY.md` forbids. Strip those bullets or replace them with
  verbatim Schenkl text; the whole `passage_epict_*` commentary series deserves
  a review.

**Needs your sources or your decision**
- Owner facts: recommended-citation title in `frontend/src/content/faq.json`
  and the locales vs CITATION.cff (depends on the Zenodo record's title);
  CITATION.cff affiliation "Faculté de Théologie Jean Calvin" (the UNIGE
  faculty is the Faculté autonome de théologie protestante / Faculté de
  théologie; "Faculté Jean Calvin" is the Aix-en-Provence institution); your
  bio (`en.json` l. 933: "despite being absent from biblical texts" — Sir
  15:14–17 and Deut 30:15–19 thematise choice; perhaps "despite the absence of
  the philosophical vocabulary of self-determination from biblical texts").
- `person_bobzien_susanne_contemporary`: fields contradict each other on
  whether Michael Frede supervised her DPhil (the preface of Bobzien 1998
  settles it).
- Page ranges needing the printed tables of contents: `person_porphyry`
  (Taormina in Destrée 2014, ≈ pp. 265–281), `synthesis_dihle1982_lec3_*`
  (overlaps Lecture IV), `pub_meyer_2011_*` (introduction is not 38 pp.),
  `scholarly_argument_hall_…_8` (page_range holds e-book line numbers),
  `scholarly_argument_belcastro_…` (p. ~205 is impossible for pp. 211–243).
- Work identity: `sc79_chrysostomus_de_providentia` conflates SC 79 (*Sur la
  providence de Dieu*, PG 52) with the six *Discourses on Fate* (PG 50);
  missing identifiers for Augustine *De gratia et libero arbitrio* (stoa044 is
  *De gestis Pelagii*; 75 KG nodes and 50 corpus rows carry it), *De
  correptione* (stoa045 unverified), Simplicius *In Ench.*, Rufinus' Latin
  *Comm. Rom.*
- Arguments needing new work nodes or re-anchoring: Bayle art. "Pyrrhon",
  Spinoza *Ethica* and Hume *Enquiry* VIII, Tertullian *Adv. Prax.* 1–2,
  `argument_theodicy_alex`, `concept_exousia_alex.key_passages` (impossible
  "Fat. 54–56 / 242 / 262 / 297"), the Dihle "Indian parallel" quotation,
  Graeser on Epictetus/Plotinus.
- `period` vocabulary: Ezekiel is neither "Second Temple" nor "First Temple";
  modern scholars are split arbitrarily between "Modern" and "Contemporary";
  Stoic heimarmenê is tagged "Roman Imperial". A tagging rule is needed.
- Texts to re-ingest: 227 Diogenes Laertius and 60 Seneca *Epistulae* nodes
  drop their verse and block quotations (e.g. `passage_dl_lives_3_1_16` is
  "καὶ πάλιν·"); ≈78 Methodius nodes mix Bonwetsch's German apparatus into the
  text; `passage_epictetus_disc_i_1_23` adds αὐτός and changes the word order of
  *Diss.* 1.1.23; `passage_firmicus_math_1_2_7` has OCR errors.
- Greek gate: one pre-existing run in
  `scholarly_argument_koch_alexander_s_target_stoic_deter_1.quote_verbatim`
  ("ἀναγνώρισις ἡἐκ συλλογισμοῦ εἱμαρμένην εἵμαρτο") is PDF-extraction debris
  mixing *Poetics* terms; it is not verbatim of anything and was not
  allowlisted. Re-extract Koch's text from the PDF.
- `data/kg/stats.json` is stale (20,060 nodes / 56,448 edges); regenerate it or
  drop it in favour of `data/stats.json`.

**Not a factual error, but public:** about 20 tracked files record where source
PDFs came from, naming shadow libraries (Anna's Archive, LibGen), e.g.
`data/doxographical_audit/scholarly_refs_index.json` (107 mentions) and one
`quote_verbatim` header in `scholarly_argument_gerson_plotinus_s_philosophical_signi_1`.

## 7. Systemic causes and recommendations

1. **"Verified" flags are not evidence.** `citation_verdict: verified`,
   `verified_reference`, "verbatim-confirmed", "TLG-confirmed" sat on many of
   the errors above. Treat them as unreviewed until a check names the edition
   and locus it used.
2. **Corrections did not propagate.** Earlier audits fixed `description` and
   left `stance`, `label`, `premises`, `supporting_evidence`, `description_fr`
   stating the old error (≈35 stale stances in one slice alone; 56 nodes
   needed the French fix here). Any fix should search the whole node.
3. **Chunk numbers read as loci.** Didache, Ps.-Plutarch, Methodius, Boethius
   and the Plotinus drift all come from sequential ingestion chunks later
   treated as canonical references. Generalise
   `scripts/data_2026_09_24_plotinus_locus_drift.py` (locate the stored text in
   the reference TEI by normalised letter-sequence search, compare the found
   locus with the declared one) into a gate for every work with a pinned TEI;
   this audit ran that check on 14,098 passages of 67 works.
4. **Latin has no gate.** Add a Latin attestation gate analogous to
   `check_greek_gate.py` (≥3-word quoted Latin must occur in the corpus or a
   registered edition, u/v and i/j normalised).
5. **The Greek gate protects only changed nodes.** Run `--all` in CI and work
   the baseline down; it silently exposes old debt only when a node is touched.
6. **Edge generators without chronology.** A simple check — no `influences` /
   `precedes` from later to earlier, no `responds_to` / `critiques` /
   `extends` from earlier to later — would have caught every reversed edge in §3.
7. **Catalogue imports.** Errors cluster in bulk imports (Origenality
   catalogue: reviewers as authors, reprint years, institutions as co-authors,
   duplicate book nodes); hand-curated `scholarly_work_*` records were almost
   error-free.

## 8. Limits

- The shared web-search budget was exhausted mid-audit and most catalogue and
  encyclopedia sites were blocked; some bibliographic points rest on expert
  knowledge and are marked PLAUSIBLE or left open.
- About 270 argument descriptions summarise local PDFs of modern scholarship
  that are not in the repo; they were checked for internal consistency and for
  every ancient locus they cite, not against the PDFs.
- 303 passage nodes had no reachable TEI (Seneca *De providentia*, minor
  Augustine works, Evodius, the French *De principiis*, …) and 4,466 have no
  CTS work; their loci were not machine-checked.
- Findings rated below "medium" confidence were not reported, so the audit
  errs toward missing errors rather than inventing them.
