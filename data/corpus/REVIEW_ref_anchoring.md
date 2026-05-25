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
| Calcidius, In Timaeum (`digiliblt_dlt000607`, 5) | local |
| Cicero, De Fato (real Latin, if a clean-text node exists) | Ax / SC |
| Ps-Plutarch, De Fato (`tlg0007.tlg099` eng, 19) | local |

**Note:** the `phi0474.phi049` Cicero *De Fato* slots (eng+lat) currently hold
English summaries (category 3), not the Latin text — confirm whether a genuine
Latin De Fato text node exists before aligning.

---

## Principle
Wrong anchoring is worse than honest non-anchoring. Every committed ref is adopted
verbatim from a published edition the passage text demonstrably reproduces.
