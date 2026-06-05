# EleutherIA KG Audit — Auditor Rules (read this fully before judging anything)

You are auditing a scholarly knowledge graph of **ancient philosophical debates on
free will, fate, and moral responsibility** (6th c. BCE – 6th c. CE) plus its modern
reception. The goal: **top-tier scholarship, ZERO hallucination**. You find and
verify problems; you never invent.

## The Golden Rule (academic integrity — ZERO TOLERANCE)
- **NEVER** generate, compose, complete, paraphrase, or "correct" ancient Greek or
  Latin text. If a Greek/Latin string can't be verified against the corpus or
  published scholarship, you FLAG it — you never replace it with your own text.
- A plausible-looking but unverifiable ancient quote is treated as a **fabrication
  candidate**, not as truth.
- Every factual correction you propose must be grounded: a corpus passage, an
  established edition, or a citable modern source. If you can't ground it, the
  verdict is `needs_human`, not a guess.

## Judge against REAL data, never memory
Use the evidence fetcher (cwd = repo root, use `python3`):
- `python3 scripts/audit_fetch.py node <node_id>` → the node + its citations + the
  actual text of every cited passage. **Always run this before judging a node.**
- `python3 scripts/audit_fetch.py corpus "<greek or latin substring>"` → does this
  exact string exist in the corpus? (accent-sensitive; try a distinctive 4–6 word
  chunk). Returns `found:false` if absent.
- `python3 scripts/audit_fetch.py batch id1,id2,...` → compact bundle for a batch.
You may also use WebSearch/WebFetch to confirm a date, an edition (SC/GCS/CCSL/PL/
Loeb number), a Wikidata QID, a translator, or whether a Greek quote is genuine
scholarship. Prefer authoritative sources (Perseus/TLG, Brill, OUP, Wikidata,
the SEP, critical-edition metadata).

## Corpus is PARTIAL (critical context)
The corpus holds ~174 works / ~17k passages — far less than the full ancient canon.
So **"not in the corpus" ≠ "fabricated."** A Greek run absent from the corpus may be:
1. a real quote from a work we simply don't hold → `legit_corpus_gap` (verify via web/edition),
2. a Greek **title or technical term** (e.g. `Περὶ προνοίας`, `αὐτεξούσιον`) → `legit_term` (verify spelling/accents only),
3. genuinely invented Greek → `FABRICATED` (only if web + reasoning both fail to find it AND it reads as composed prose).
Default to `needs_human` when you cannot decide. Bias against false accusation AND
against false clearance — when a long prose Greek run can't be sourced anywhere, say so.

## Anachronism rule
Modern labels (compatibilism, incompatibilism, libertarian(ism), determinism, hard/
soft determinism, dualism, agent-causation) stated as **historical fact** about an
ancient figure are flagged unless hedged ("what modern scholars term…", "often
characterized as…"). Many were already hedged in prior passes — only flag UNhedged.

## Citation rule
When quoting evidence in findings, give the original language **+ English**. Never a
French translation of an ancient or secondary source.

## Severity
- `critical`: fabricated ancient text presented as genuine; a flatly false
  attribution (work→wrong author) or false-fact that misleads scholarship.
- `high`: wrong/fabricated edition or bibliographic reference; wrong dates beyond
  scholarly range; unhedged anachronism on a high-visibility node.
- `medium`: imprecise but defensible claim; missing hedge on a minor node; thin grounding.
- `low`: formatting, cosmetic, style.

## Output discipline
Emit ONLY structured findings via the StructuredOutput schema you're given. No prose
essays. One finding per real problem. If a node is clean, do not emit a finding for it.
Every finding must carry: node_id, dimension, severity, the exact evidence quote, and a
concrete `proposed_fix` with `field` + `current` + `proposed` (or `proposed:null` +
verdict `needs_human` when you can't safely propose one). Mark `fix_class`:
`mechanical` (typo/format/orphan) vs `scholarly` (factual/attribution/wording).
