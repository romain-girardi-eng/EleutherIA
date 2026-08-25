# REVIEW: Canonical Reference Recovery — status & remaining work

**Date:** 2026-05-25
**Tool:** `scripts/recover_canonical_refs.py` — text-aligns each passage to its
authoritative published TEI edition and adopts the edition's own canonical
reference verbatim (Stephanus / Bekker / book.chapter.section / prose-metre …),
as a range when a passage spans several leaves. Zero fabrication; a ≥55 % text-
match gate refuses to touch a work whose stored text does not reproduce the
edition. Only `cts_urn` + `canonical_ref` are rewritten; `passage_id` is never
touched, so `passage_citations` FKs are preserved.

---

## DONE — faithful refs recovered & committed (13 works)

| Work | Edition adopted | Passages |
|------|-----------------|----------|
| Plato, Phaedo | tlg0059.tlg004.perseus-grc2 (Stephanus pages) | 6 |
| Plato, Gorgias | tlg0059.tlg023.perseus-grc2 (Stephanus pages) | 21 |
| Plato, Timaeus | tlg0059.tlg031.perseus-grc2 (Stephanus pages) | 75 |
| Justin, 1 Apology | tlg0645.tlg001.1st1K-grc1 (chapters) | 66 |
| Justin, 2 Apology | tlg0645.tlg002 (chapters) | 15 |
| Plutarch, De Stoic. Repugn. | tlg0007.tlg136 | 47 |
| Plutarch, De Comm. Not. | tlg0007.tlg135 | 6 |
| Simplicius, In Ench. | tlg0093.tlg001 (chapter.section.line ranges) | 9 |
| Galen, De Plac. | tlg0057.tlg010 (book.chapter ranges) | 3 |
| Aspasius, In EN | tlg0615.tlg001 (CAG) | 6 |
| Philo, De Opif. | tlg0018.tlg001.1st1K-grc1 (fixed dangling opp-grc1) | 172 |
| Clement/Origen, Protrepticus | tlg2042.tlg007.perseus-grc1 (completed URN version) | 51 |

Already-faithful works the tool confirmed need NO change (NOCHANGE): Tertullian
(stoa0275 ×3), Gregory Naz. (tlg2022 ×3), Porphyry (tlg2034), Alexander De Fato
grc (tlg0732.tlg014), Plutarch De Fato (tlg0007.tlg108), Aristotle slot tlg0086.tlg003.

**Corpus ref-health after this pass:** 10,337 / 17,889 passages (58 %) carry a
complete CTS URN (with edition version) + a labelled reference.

---

## REMAINING — needs a decision or a dedicated pass

### 1. Epictetus, Discourses (`tlg0557`, ~422 passages across grc+eng)
Flat `Epict. N` labels from a bulk extraction, plus a heterogeneous mix of
`I.x` / `§N` refs. Text-alignment to `tlg0557.tlg001.perseus-grc2` recovers only
58 % and shows a **book-number collapse** (DB `II.1` → TEI `1.29`), so automated
alignment is unreliable here. **Path:** dedicated pass — re-ingest the Discourses
cleanly from `tlg0557.tlg001` and discard the flat-section passages (check
`passage_citations` before deleting). Do NOT auto-apply the 58 % result.

### 2. Sextus Empiricus, PH (`tlg0544.tlg001`, 534 passages)
Same text as the edition, but our 534 passages are a cherry-picked, non-document-
order subset vs 789 TEI leaves, so the cursor-based aligner only catches 136.
**Path:** dedicated pass with a per-passage best-window cosine match (threshold
> 0.85, unique), not the sequential cursor; then rebuild `book.section` refs.

### 3. Non-standard (descriptive) refs — DE-MANGLED (DONE)
An earlier estimate of "~4,378 shell passages" was wrong: that count was mostly
SC-edition **primary text + translations** with *good* structured refs that merely
lack a *CTS URN* (e.g. Contra Celsum `1.18`). The genuinely non-standard refs were
only **658 (3.7%)**. `scripts/demangle_refs_2026_05_25.py` reformatted **593** of
them in place — zero fabrication, only restructuring locus data already in the
string:
- **French SC-importer refs** (`'1.chap.: 4, verset: 9b-14'` → `1.4.9b-14`;
  `'2.liv.: 2 (gloss), chap.: 36'` → `2.36`): Barnabas, Theophilus, Clement Cor.,
  Athenagoras — matched to the corpus `{book}.{chapter}[.{section}]` convention.
- **Summary refs with a locus** (`'Origen, De Principiis III.1.3: …'` → that
  citation; `'Lucretius on the swerve (DRN II.251-293)'` → `DRN II.251-293`;
  `'De Fato 14 (gloss)'` → `De Fato 14`): Philocalia, Methodius, Augustine *De
  Civ.*, Justin *Dialogue*, Alexander, Lucretius, etc.

**65 left flagged** (irreducible — locus not safely recoverable):
- Contra Celsum (16): `'SC 150, par.: 65, §118'` — book ambiguous from the SC
  volume (Borret SC 132/136/147/150 each span two books); Koetschau §-only.
- Aristides (17): papyrus-fragment / Barlaam-romance prose, no clean scheme.
- Epictetus *Fragments* (22): `'Epictetus, Fragments: …'` — fragment, no number.
- Melito *Apologia* (6): `'1.fragm.: 1, chap.: 1, par.: 4-5'` — fragment scheme.
- 4 pure-prose summaries / Greek-incipit refs (Plotinus, Boethius, Aristotle EN,
  Alexander) with no locus at all.

### 4. NO-TEI primary works → local DOCTORAT critical editions
Genuine primary text absent from Perseus / First1KGreek, to be aligned against the
local critical editions on disk (per the agreed plan):

| Work | Likely local edition |
|------|----------------------|
| Boethius, Consolatio (`phi2089.phi002` eng+lat, 258) | (Boethius critical ed.) |
| Origen, De Principiis (`...de_principiis...`, 24) | SC 252/253/268/269 |
| Augustine, City of God (`stoa0040.stoa054` + `adv_fulg`, 65) | CCSL / local |
| Evodius, De Fide (`cpl_evodius_de_fide_lat`, 36) | CPL / local |
| Melito, Peri Pascha (`tlg1098`, 4) | SC 123 |
| Calcidius, In Timaeum 142–146 (`stoa0071b.stoa001`, 5) | Wrobel 1876 checked transcription + visually mapped scan; DLT000070 and DLT000607 retained as distinct external records |
| Cicero, De Fato (`phi0474.phi054`, Latin + Yonge English) | Latin edition identity still open; English manifestation declared |
| Ps.-Plutarch, De Fato (`tlg0007.tlg108`, 12 Greek + 12 English) | pinned Bernardakis 1891 + A. G./Goodwin 1874 |

**2026-08-24 update:** the legacy Cicero `phi049`/`phi056`, Ps.-Plutarch
`tlg099`/`tlg9857` and Calcidius `DLT000607` identities cited by this historical
review have been superseded by audited repair scripts. See `data/audit/` and
the SOTA registry; unresolved edition-level debt remains explicit there.

---

## Greek TEXT corruption — REPAIRED (638 passages)
A deeper integrity problem than references: stored Greek with unconverted betacode.
- **Betacode-residue repair** (`fix_betacode_text_2026_05_25.py`, 592 passages):
  grave `\`, acute `/`, circumflex `=`, capital `*`+breathing left as literal ASCII
  (`περι\`→`περὶ`, `*̔ρώμῃ`→`Ῥώμῃ`) → proper polytonic Unicode. Mainly Sextus PH
  (all 534), Epictetus (48), Didache. Gated to the unambiguous residue marker;
  passage_id preserved.
- **Embedded raw betacode** (`fix_embedded_betacode_2026_05_25.py`, 46 passages):
  Greek quoted in betacode inside Latin/Greek classical works (Cicero De Div/Nat
  Deorum, Seneca, Augustine, Plutarch): `ei(marme/nhn`→`εἱμαρμένην`. Allowlisted to
  genuine classical works; rejects Latin apex (`U/bi`), English or-slashes, OCR `e(`.
- Residual: 3 non-betacode artifacts (Latin OCR `e(iiciens`, an Aspasius apparatus
  line, a French parenthetical) — correctly left untouched.

## MISATTRIBUTION — NEEDS A DECISION (not auto-fixed: destructive + scholarly)
**`urn_cts_greeklit_tlg0086_tlg003_grc`** is titled *Aristotle, De Generatione et
Corruptione* but its 69 passages are the **Constitution of Athens** (Ἀθηναίων
Πολιτεία): ch.1 (Cylonian affair) … ch.69 (jury-voting urns). The refs `1`–`69`
are actually correct *for Ath. Pol.* — only the identity is false. The mis-ingestion
fetched `tlg0086.tlg003` (Ath. Pol.) instead of the De Gen. et Corr. tlg number.
**Blast radius:** the `ancient_works` row + 69 passages + 69 `passage_citations`
+ KG work node `work_de_gen_corr_aristotle` + 69 `passage_arist_gen_corr_*` KG nodes
+ 138 edges. **Options:** (a) re-ingest genuine De Gen. et Corr. (free-will-relevant
Book II on necessity) into the slot — fulfils original intent but needs section
selection; (b) relabel everything truthfully to *Athenaion Politeia* — honest but
out-of-scope for free will; (c) remove the erroneous subgraph entirely. Recommended
(a) if DGC is wanted in the corpus, else (c).

## Sextus + Epictetus — IN-PLACE REF RECOVERY (DONE; citations preserved)
A full re-ingest was rejected after a dry-run showed it would delete 738
concept→passage evidential citations (the existing passages are a heavily-cited
curated evidence base). Instead, refs were recovered in place on the now-clean text
(`--global` per-passage best-match aligner, conservative 0.7 threshold):
- **Epictetus** (`tlg0557_grc`): 46 `Epict. N` flat → `Epict. Disc. b.c.s`; 189
  summary/excerpt passages left untouched. All 235 passages + 738 citations kept.
- **Sextus** (`tlg0544.tlg001`): 136 PH passages → `PH 1.x`; 396 → `AM 7.x`
  (confirming the `M.137+` are Adversus Mathematicos VII, not PH). 532/534 refs
  fixed; all 538 citations kept. (The node still mixes PH + AM passages — a
  structural mislabel; refs are now individually correct. Split deferred.)

## Boethius — DONE (Latin)
Consolatio is on Perseus at **stoa0058.stoa001.perseus-lat2** (the stored
`lat7127.011` URN is fabricated/404). 127 Latin passages `Cons. N` flat →
`Cons. 1.M1` / `Cons. 3.P9` (book.prose/metre). English translation node
(`phi2089.phi002_eng`) left flagged — its TEI div structure didn't parse.

## Follow-up round — DONE
- **KG export repointed to Supabase** (`export_kg_snapshot.py` now reads the live
  DB, not the stale Railway backend). Mirror resynced: dropped 27 malformed
  null-endpoint edges + stale Railway edge_ids, added ~2160 legitimate edges git
  was missing; the 227 quarantined drift triples stay excluded. git now == Supabase
  minus quarantine.
- **Sextus PH/AM split**: 396 Adversus Mathematicos passages moved out of the
  Pyrrhonism node into the AM work node (new AM KG work node + retargeted anchors);
  PH node now holds only its 138 PH passages. Citations preserved.
- **Boethius English node**: 127 refs copied from the Latin node by sequence
  (`Cons. b.M/P`). **Origen De Principiis**: 32 fragments → `De Princ. 3.1.x`
  (Peri autexousiou + IV).

## Still flagged (no clean source / genuinely irreducible)
- Evodius *De Fide Contra Manichaeos* (not on Perseus, no local edition) — refs
  unrecoverable without a source.
- ~189 Epictetus + 2 Sextus passages: genuine **Greek primary text** (role=original)
  that the conservative aligner (0.7) couldn't place precisely — left with internal-
  index refs (forcing refs would risk misassignment; honest as-is).
- 65 descriptive refs (Contra Celsum book-ambiguous from SC vol, Aristides papyrus,
  Epictetus *Fragments*, Melito) + 3 non-betacode OCR artifacts.

## Second follow-up round — DONE
- **187 dangling citation→kg_node FKs resolved**: all 187 pointed at one missing
  alias (`concept_epict_eph_hemin_synthesis`); every affected passage already cited
  the canonical `synthesis_epict_eph_hemin_doctrine`, so all 187 were deduplicated.
  Both invariants (dangling citation→passage + →kg_node) now **0**.
- **227-edge quarantine resolved**: all were ontology violations (195 reversed
  person→created_by→work; 23 wrong source-types for related_to; 4 unknown
  teacher_of relation; 5 group→created_by). Deleted from Supabase (cleaning prod,
  not just git); restored 148 canonical inverses (145 authored_by + 3 student_of)
  where the only authorship info was the reversed edge. Quarantine file removed
  (resolved). DB↔git now matched on edges (no deliberate exclusions).
- **SC text verification (4,081 passages)**: 26/26 original-language SC works
  (Greek + Latin, incl. all 987 Contra Celsum) match their on-disk SC critical
  editions at **85–100 %** (22 of 26 at ≥95 %). No fabrication, no misattribution
  in the Greek/Latin SC content. The 26 English translation nodes can't be
  verified against SC (SC has no English) — they need a separate audit against
  Falls / Schoedel / Ehrman / Chadwick / Butterworth / Crouzel / Grant / Harvey.

## Third follow-up round — DONE
- **Sextus AM IX–X granularity redundancy**: decision = keep both. The 791
  per-section AM IX–X passages + the 109 overlapping-window books 9–10 are
  complementary (different granularity, both cited); deletion would lose
  citations without an integrity gain.
- **Railway-staleness warnings added** to the three rollback runbooks
  (`incident-playbook.md`, `phase-c-cutover.md`, `migration-master-runbook.md`):
  a rollback to Railway now flags that Railway's DB has diverged from Supabase
  and serves out-of-date data unless re-synced.
- **2 of 3 OCR artifacts cleaned**: Seneca *Ep.* phi1017 `e(iiciens` → `efficiens`;
  Origen *Philocalia* `(pneumatiques)mais` → `(pneumatiques) mais`. The Aspasius
  apparatus line (`A.SPA.Sil L\ ETli. MCOM. I 11 [Ari.st. p.`) is OCR/apparatus
  garbage in a single passage — left, no clean source.

## Still flagged (genuinely irreducible / out of scope)
- **English translation nodes** (~2,250 passages across 26 nodes): unverified
  against published English critical editions (Falls, Schoedel, Ehrman, Chadwick,
  Butterworth, Crouzel, Grant, Harvey). Separate audit category.
- Evodius *De Fide Contra Manichaeos*: no source available.
- ~189 Epictetus + 2 Sextus Greek excerpt passages with internal-index refs
  (genuine primary text, conservative-non-misassignment policy).
- 65 descriptive refs (Contra Celsum book-ambiguous from SC vol, Aristides
  papyrus, Epictetus *Fragments*, Melito) + 1 Aspasius OCR-garbage passage.

## Final corpus state (verified)
passages 17,823 · citations 19,766 (dangling **0**, kg-node dangling **0**)
· kg_nodes 20,060 · kg_edges 56,775 (DB == git, no quarantine)
· betacode residue **0** · non-standard refs **65 (0.4%)** · roles original/
translation/paraphrase · **SC Greek/Latin content text-verified faithful to the
critical editions on disk**.

## Final corpus state
betacode-grave residue **0** · non-standard refs **65 (0.4%)** · dangling
citations **0** · passage roles original/translation/**paraphrase** (174 English
summaries honestly tagged) · DB↔git in parity (corpus + KG subgraphs).

## Principle
Wrong anchoring is worse than honest non-anchoring. Every committed ref is adopted
verbatim from a published edition the passage text demonstrably reproduces; every
text repair is a deterministic, verifiable conversion of data already present.
