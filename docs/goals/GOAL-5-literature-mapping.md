# G5 — Secondary-Literature Mapping & Arbitration

**Objective:** Read deeply across the modern scholarship on ancient free will, **map where scholars agree and
disagree**, surface the **great standing debates**, and — where the primary evidence permits — have EleutherIA
**arbitrate** specific debates with a structured, fully-cited verdict. This is the project's most distinctive
contribution: *the digital-humanities resource as quantifiable arbiter*.

**Why (from analysis):** The reception layer is already first-class data — **304 modern scholars, 929
reception-arguments, 779 typed edges onto dated ancient nodes** — and the Amand-vs-Bobzien Carneades paper
(`docs/papers/2026-05-amand-piste1-RESUME.md`) is the working prototype: a 6×4 provenance matrix computed from the
graph that adjudicates a 28-year dispute pivot by pivot. But the reception layer is **under-anchored to concepts**
(the Carneades conceptual test scored 0/24 because reception links point to `passage_*`, not `concept_*`), and the
cross-scholar agree/contest structure is not yet systematically modeled. The library on disk
(`04_Littérature_secondaire/`: 289 PDFs, 330 `.md`/`.txt` extractions) is largely unread into the KG.

**Deliverables (artifacts under `data/goals/g5/`):**
1. **Debate map** — for the major standing controversies (e.g. Did the Stoics have a notion of free will? [Bobzien
   *no* vs others]; Who "invents" the will? [Dihle/Augustine vs Frede/Epictetus vs Fürst/Origen — keep as *contested
   modern paradigm*]; Is Alexander a libertarian? [Sharples' hedge]; Carneadean anti-astrology transmission), a
   structured **for/against scholar map** with each position grounded in publication + page + the ancient locus contested.
2. **Consensus/contested matrices** — for each ancient passage/concept with ≥2 scholars linked, a pairwise stance
   classification (agree / contest / extend) → a consensus-vs-contested matrix. Ship αὐτεξούσιον and *to eph' hēmin* first.
3. **Arbitration reports** — for debates the primary evidence can settle, an Amand-style provenance matrix yielding a
   defensible verdict with full citation (and an honest "underdetermined" verdict where it can't).
4. **Staged KG enrichment** — new/updated `scholar_*`, `scholarly_argument_*`, `publication_*` nodes + `agrees_with`/
   `critiques`/`contrasts_with`/`discusses` edges (reusing existing ontology; grep for existing shells first), re-anchored
   to `concept_*` not just `passage_*`. All staged for human review.

**First increment:** the "Did the early Stoics have free will?" debate map (Bobzien 2001 *no* vs the engaged positions)
— the clusters already exist (`argument_bobzien_2001_*`, Frede, Voelke) and only need the for/against structuring.

**Success criteria:** A scholar can see, for any major debate, *who holds what, on what page, contesting which ancient
line*; at least one debate gets a defensible EleutherIA arbitration with provenance; the reception layer is anchored to
concepts, not just passages.

**Anti-anachronism guardrail:** positions like "invention of the will", "libertarian", "compatibilism" stay **attributed
to named scholars**, never asserted as fact (see `feedback_no_invention_of_will_teleology`). Arbitration verdicts state
their evidential limits.

**Dynamic workflow design:** Continuous, self-paced. Phase 1 (read): parallel agents read batches of the secondary-lit
library, extracting each scholar's position + the loci they contest. Phase 2 (map): cluster by debate, classify pairwise
stances → matrices. Phase 3 (arbitrate): where evidence permits, run the Amand-style analyzer → verdict report. Phase 4
(enrich): stage KG nodes/edges for review. Feeds G1's reception layer; runs until the library is mapped.
