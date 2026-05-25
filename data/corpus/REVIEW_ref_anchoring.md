# REVIEW: Ref Anchoring — Epictetus & Sextus PH

**Date:** 2026-05-25  
**Status:** Investigation only — no DB mutations made.

---

## 1. Epictetus — "Epict. N" opaque labels

### Scope

- Works: `urn_cts_greeklit_tlg0557_grc` (Greek, 235 passages) and `urn_cts_greeklit_tlg0557_eng` (English, 187 passages)
- Passages with `canonical_ref ~ '^Epict\. [0-9]+$'`: **248 total** across both works
- These are the "flat section" passages — e.g. `Epict. 6`, `Epict. 26`, `Epict. 51`, `Epict. 100` … `Epict. 235`
- `book`, `chapter`, `section` structure: `section = N` (flat global), `book = NULL`; some passages have duplicate `canonical_ref` values with different `book` fields (e.g. `Epict. 51` appears twice: once with `book=NULL, section=51` and once with `book='I', section=NULL`)

### Root cause

The Epictetus corpus was ingested from multiple sources in parallel:
1. A clean ingest with proper `Discourses I.1.1` refs (small set, e.g. `Discourses I.1.1 (τὰ ἐφ' ἡμῖν) (English)`)
2. A bulk "key phrases + Greek snippet" extraction that assigned flat `Epict. N` sequential labels, ignoring the Discourses book/chapter/section structure

The flat `N` does NOT correspond to any published reference scheme for the Discourses. The standard CTS for Epictetus Discourses is `tlg0557.tlg001`, with ref structure `book.chapter.section` (e.g. `1.1.1` through `4.13.24`). `N = 51` does not map to a CTS reference without knowing which (book, chapter, section) combination that chunk falls in.

### Feasibility

**Not recoverable without text-alignment.** The path to correct anchoring requires:

1. Fetch the authoritative TEI from `urn:cts:greekLit:tlg0557.tlg001` (First1KGreek or Perseus)
2. For each "Epict. N" passage, align its Greek text (or English key-phrase snippet) against the TEI sections
3. Assign the matching `book.chapter.section` ref

This is feasible **in principle** for the Greek passages (text comparison can be automated). For the English "key phrases" passages, alignment is harder because the text is a synthetic summary, not a literal translation. Confidence would be lower.

**Recommendation:** Dedicate a separate ingestion pass for Epictetus. The preferred approach is to discard the flat-section passages and re-ingest the Discourses from `urn:cts:greekLit:tlg0557.tlg001.perseus-grc2` using the standard `fetch_scaife_work.py` / `ingest_scaife_work.py` pipeline. The existing passages have `passage_id`s that may be referenced by citations — check `passage_citations` before deleting any.

**Current state:** Leave as-is. The `Epict. N` labels are internally consistent, just not CTS-anchored.

---

## 2. Sextus Empiricus PH — "M. N" sequential refs

### Scope

- Work: `urn_cts_greeklit_tlg0544_tlg001_grc` (PH = Outlines of Pyrrhonism), 534 passages
- `canonical_ref` format: `M. 1` through `M. 534` — flat global sequence
- `cts_urn`: `urn:cts:greekLit:tlg0544:M.N` — this is a **non-CTS URN**: the standard CTS work identifier for PH is `tlg0544.tlg001`, not bare `tlg0544`, and the ref scheme `M.N` does not conform to CTS reference protocol

### Root cause

The label `M.` (for "Μ" = book marker, or an artefact of the ingest) combined with a global section number is an ingest-era convention, not a CTS standard. Pyrrhoneion Hypotyposeis is structured as three books (I, II, III), with sections numbered **within each book** (I.1–I.236, II.1–II.229, III.1–III.481). The passage index N = 1–534 does NOT directly map to book+section because: 534 < 236+229+481 = 946. This means `M. 1..534` covers only a subset of PH (likely the free-will-relevant passages that were cherry-picked), not the whole work.

Verify: the final passage `M. 534` would require knowing the book-level offset. Since the corpus does not store a per-book section counter and `book = NULL` for all PH passages, reconstruction is not possible from the DB alone.

### Feasibility

**Recoverable with text-alignment, but requires care.**

1. Fetch the authoritative TEI from `urn:cts:greekLit:tlg0544.tlg001.1st1K-grc1`
2. Align each passage's `text_content` against the TEI sections (Greek text comparison)
3. Assign the proper `book.section` ref (e.g. `I.1`, `II.13`, `III.12`)
4. Rebuild `cts_urn` = `urn:cts:greekLit:tlg0544.tlg001.1st1K-grc1:I.1` etc.

Unlike Epictetus, the PH passages contain actual Greek text (not summaries), so alignment should be high-confidence. This is a well-defined engineering task.

**Recommendation:** Defer to a dedicated pass. Script outline:
- Use `corpus_github_fetch` (or equivalent Scaife API call) to download PH TEI
- Parse `<div1 n="1">` ... `<div2 n="1">` structure
- Fuzzy-match each passage `text_content` against TEI section text
- Only apply update if cosine similarity > 0.85 and match is unique

**Current state:** Leave as-is. The `M. N` labels are internally consistent. The `cts_urn` field (`urn:cts:greekLit:tlg0544:M.N`) is non-standard but stable as an internal identifier.

---

## Summary table

| Work | Passages | Problem | Recoverable? | Path |
|------|----------|---------|-------------|------|
| Epictetus Discourses (`tlg0557`) | 248 opaque | `Epict. N` flat, no book/chapter | Partial (Greek texts only) | Re-ingest from Scaife `tlg0557.tlg001`; discard flat-section passages |
| Sextus PH (`tlg0544.tlg001`) | 534 | `M. N` flat, no per-book section; non-CTS URN | Yes (text alignment) | Fetch TEI, align, rebuild `book.section` refs |

Neither set should be touched until a careful dedicated pass with text-alignment verification. Wrong anchoring is worse than the current unanchored state.
