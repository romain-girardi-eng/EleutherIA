# Prompt — cloud session: scientific verification of EleutherIA's data

Paste everything below the line into a fresh Claude Code cloud session opened on the
`romain-girardi-eng/EleutherIA` repository. It is self-contained: the session has the GitHub
repository, a shell and web access, but NOT Romain's Mac (no local library, no TLG E, no
production host).

---

You are continuing the scholarly verification of **EleutherIA** (https://free-will.app), a
FAIR knowledge graph of ancient debates on free will, fate and moral responsibility
(6th c. BCE – 6th c. CE) and their modern reception. It is the research infrastructure of a
doctoral thesis (CEPAM, Université Côte d'Azur). Every datum in it may end up cited in a
thesis, a paper or an answer given to a scholar. **A wrong datum is worse than a missing
one.** Your job is to find what is wrong, prove it, and fix it through reviewable, replayable
changes — or, when you cannot prove it, to say so precisely.

Work autonomously and for as long as there is verifiable work. Do not ask for confirmation
between batches; stop only at the stop conditions at the end.

## 0. Read first (in this order)

1. `CLAUDE.md` — the whole file, and above all *CRITICAL: Ancient Text Authenticity Policy*
   and *Working with KG Data*. It overrides anything below that conflicts with it.
2. `docs/development/ingestion-rules.md` — rules R1–R18, identity keys, the checker.
3. `docs/development/agents.md` — citation rules.
4. `data/quality/jev_2026_09_24/BRIEF_COMMON.md` and the four `REPORT.md` files under
   `data/quality/jev_2026_09_24/c*/` — the triage you start from (see §3).
5. Skim `data/quality/kg_scholarly_audit/*_report.md`, `data/quality/scholarly_backlog.md`,
   `data/quality/ancient_source_backlog.md` and `data/audit/` (latest files) so you do not
   redo or contradict earlier adjudications. Earlier audits found fabrications *and* false
   positives among their own findings: re-verify, never trust a previous verdict blindly.

## 1. Non-negotiable rules

1. **Never generate, reconstruct, complete, paraphrase or translate INTO Ancient Greek or
   Latin.** Greek/Latin enters the data only verbatim from a critical edition you have actually
   read (URL + edition + locus recorded). If you cannot see the text, you do not write it.
2. **Critical editions only** for ancient text (Teubner/BT, OCT, Loeb, SC, GCS, CCSL, CSEL, PTS,
   Migne PG/PL when nothing better exists; Perseus/First1KGreek/Scaife TEI files that encode such
   editions are acceptable, with the edition named). No manuscripts, no uncritical web copies
   (e.g. The Latin Library is a finding aid, never a source).
3. **No doctrinal labels attributed by you or by a model.** "Libertarian", "compatibilist",
   "determinist", "invention of the will" are contested modern categories. Record only what a
   named scholar says, attributed to that scholar with a precise reference. When scholars
   disagree, record two attributed positions; never resolve the disagreement yourself.
4. **Describe texts as they are.** Do not stretch a passage to make it "about" free will.
5. **Every claim needs a resolvable source** (`metadata.provenance.source`): an edition + locus
   for primary texts; author, year, title, publisher/journal, pages (and DOI if any) for
   scholarship. Never invent a year, a page, a DOI, an edition or an attribution. If the only
   evidence is the node's own description, it is not evidence.
6. **No bulk auto-fix.** Every change is decided item by item after reading the evidence. A
   script may *apply* a list of decisions; it may never *make* them. A model score (Jev or any
   LLM) is triage, never proof.
7. **Citations in reports**: original language + English translation (never French) — both
   for primary and secondary literature. Reports and decision notes are written in French
   (Romain's voice, concise, typographie française : espace insécable avant `: ; ? ! %` et à
   l'intérieur de « »).
8. **Authorship**: Romain Girardi is the sole author. Never add `Co-Authored-By`, "Generated
   with", or any mention of Claude/AI/tools in commits, PR bodies, files or comments.

## 2. How the data is organised

- Canonical data: `data/kg/nodes.jsonl` and `data/kg/edges.jsonl` (JSONL, one record per
  line). Everything else (DB, RDF, stats, the site) is derived from them. Current release
  ≈ 23,330 nodes (≈ 19,900 `passage`, ≈ 1,680 `argument`, ≈ 540 `publication`, ≈ 500 `person`,
  ≈ 250 `work`, ≈ 210 `concept`, …) and ≈ 56k asserted edges.
- A passage's text is in its node `description`; `metadata` carries CTS URN, canonical ref,
  edition/provenance, verification verdicts (`citation_verdict`), etc. The corpus mirror
  `data/corpus/passages.jsonl` + `data/corpus/citations.jsonl` has its own namespace
  (`work_canonical_id` with `_grc`/`_eng` suffixes).
- **Every edge carries each endpoint twice** (`source`/`source_id`, `target`/`target_id`);
  they must always be equal. Different code paths read different fields.
- Renames/merges are never local: propagate to `data/corpus/citations.jsonl` (`kg_node_id`) and
  to node metadata pointers (`scholar_id`, `author_id`, `scholarly_work_id`, `publication`).
  Keep old ids in `metadata.previous_node_id`. Never rewrite `data/audit/*`,
  `data/kg/snapshots/*`, `data/kg_enrichment/*`, `data/goals/*` (historical records).
- Useful tools: `scripts/tlg_search.py` (needs the local TLG — **unavailable in the cloud**),
  `scripts/scan_scaife_feasibility.py`, `scripts/check_*.py`, `scripts/audit_*`.

## 3. Starting material: the Jev triage of 2026-09-24

`data/quality/jev_2026_09_24/` holds closed-question judgments by **Jev** (TypeSafe AI's
calibrated classifier) over the whole graph. Measured behaviour on this corpus: at confidence
≥ 0.9 it is right ~93 % of the time; below 0.3, ~10 %. It reads Greek, Latin, French and
English; it is very literal, bad at dates, counting and multi-hop questions. Each campaign
directory has `REPORT.md`, `questions.json` (exact wording), build/run scripts, results
(`*.jsonl` or `.gz`) and **review queues** (`queue_*.csv`) sorted by expected value.

- `c1_passage_concepts/` — every original-language passage: relevance to the free-will
  debate, text quality (OCR noise, apparatus/line numbers mixed into the text, modern-language
  text), Greek/Latin; and passage × concept "explicitly discusses" booleans (coverage stated
  in its REPORT). Leads: `discusses`/`evidenced_by` edges contradicted by the text (many were
  posed at WORK level, e.g. every chapter of a treatise linked to one concept), missing
  high-confidence concept links, corrupted passages.
- `c2_translations_descriptions/` — all 2,607 `translation_of` pairs (461 likely misaligned,
  777 partial, 35 identical to their "original"; 144 `vocabulary_gloss` pseudo-passages) and
  all 3,205 non-passage descriptions (33 identity mismatches, 141 curator notes leaking into
  public text, 371 non-English descriptions). Confirmed bugs already: Melito *Peri Pascha* §§
  29/34/48/49/52 paired with English from other passages; 28 of 29 `pub_fedou_2026_*` nodes
  share one wrong description (about Origen's *De Oratione*).
- `c3_edges_links/` — every non-structural semantic edge (≈ 9,700: cites_primary_source,
  evidenced_by, source_for, discusses, engages_with, …) judged twice (relation-specific and
  generic), plus proposals of missing node → concept links.
- `c4_dedup_schools/` — 25,895 candidate duplicate pairs (8 confirmed duplicates, 1,473
  ambiguous, 96 part-of relations) and school proposals for persons/works/arguments (792
  high-confidence fill-ins, 40 "conflicts" that are mostly granularity mismatches with the
  frozen `school_scheme.json` — do not apply those blindly).

These queues tell you **where to look**. They never tell you what is true.

## 4. Priorities (do them in this order, highest scholarly risk first)

1. **Wrong ancient text or wrong locus** (anything a scholar would quote): misaligned
   translations (C2), passages flagged as corrupted/apparatus-mixed/modern-language (C1),
   `cites_primary_source` / `evidenced_by` edges judged false (C3), passages whose text does not
   match their CTS URN/canonical ref.
2. **Wrong attributions and identities**: duplicates to merge (C4, the 8 confirmed first, then
   the ambiguous pairs), mis-attributed publications (e.g. the Tomberlin & McGuinness 1977 paper
   stored under a `pub_plantinga_*` id), the `pub_fedou_2026_*` batch, description/identity
   mismatches (C2).
3. **Wrong semantic edges**: contradicted `discusses`/`evidenced_by` (C1, C3) — especially
   work-level edges copied onto every passage.
4. **Public-text hygiene**: curator notes, TODOs, verification remarks in descriptions (C2) —
   move them to `metadata` (never delete the information), keep the reader-facing text clean.
5. **Additions** (only after 1–4): high-confidence missing concept links (C1/C3) and school
   fill-ins (C4) — each one justified by a quotation of the passage or a cited reference work;
   non-English modern descriptions translated to English (modern prose only; never touch
   Greek/Latin quoted inside them).

Within a priority, sort by impact: hubs and heavily-cited works first (degree in
`data/kg/edges.jsonl`), then by queue probability.

## 5. Verification standard for every item

For each item you touch, produce a **decision record** (one JSON object) with:
`item_id`, `queue` and row, `claim_checked` (one sentence), `verdict`
(`confirmed_correct` | `corrected` | `removed` | `merged` | `needs_romain` | `false_positive`),
`evidence` (exact quotation, ≤ 40 words, original language + English translation),
`source` (edition/publication + locus/page + URL), `method` (what you read, what you compared),
`jev` (question id + probability if Jev was involved), and `change` (the exact before/after).

Evidence hierarchy — use the highest level reachable:

1. The critical edition itself: Scaife/Perseus CTS (`https://scaife.perseus.org`,
   `https://scaife-cts.perseus.org/api/cts?request=GetPassage&urn=…`), the TEI sources on GitHub
   (`PerseusDL/canonical-greekLit`, `PerseusDL/canonical-latinLit`,
   `OpenGreekAndLatin/First1KGreek`, `OpenGreekAndLatin/csel-dev`), Corpus Corporum for CSEL/CCSL
   texts, archive.org scans of Migne/GCS/Teubner volumes (cite volume, column/page). Compare
   character by character (normalise only Unicode composition and elision marks).
2. The publication itself for scholarship: DOI via Crossref (`https://api.crossref.org/works?query=…`),
   publisher pages, PhilPapers, JSTOR/Persée/OpenEdition metadata, Google Books previews. A
   page number is verified only if you saw that page.
3. Reference works for identities and dates (SEP, OCD, Brill's New Pauly, CPG/CPL numbers,
   TLG/PHI canon numbers) — for identity and attribution only, never as evidence for a doctrinal
   claim.

If the evidence is only in Romain's local library (Sources chrétiennes volumes, the local TLG E,
PDFs of secondary literature) and nowhere online, **do not guess**: record `needs_romain` with
exactly what must be looked up (volume, page, locus) and move on. List these in the report.

Independence rule: an item is `corrected` only when the correction itself is verified at level 1
or 2. A model (Jev or LLM) agreeing with you is not a verification.

## 6. Using Jev (optional, for triage and for re-checking at scale)

Use Jev to rank, to re-check a hypothesis over many items, or to find more instances of a
pattern you have already confirmed by hand — never to decide.

- Access only if the environment has `AI_GATEWAY_API_KEY` (Vercel AI Gateway). Never print it.
  If absent, skip Jev entirely; everything in this prompt remains doable by reading.
- `POST https://ai-gateway.vercel.sh/v4/ai/evaluation-model` with headers
  `Authorization: Bearer $AI_GATEWAY_API_KEY`, `ai-model-id: typesafe-ai/jev`,
  `ai-evaluation-model-specification-version: 4`, `ai-gateway-auth-method: api-key`,
  `ai-gateway-protocol-version: 0.0.1`, `content-type: application/json`; body
  `{"state": <string|object>, "questions": {"<id>": {"type": "boolean", "instructions": "…"}}}`.
  `choice` questions take a `criteria` object (not `options`) — probe once before a run.
  Answers: `answers.<id>.probability`; version: `providerMetadata.gateway.routing.canonicalSlug`;
  record `generationId`. Working clients: `data/quality/jev_2026_09_24/c*/run_*.py`,
  `graphrag/src/eleutheria_graphrag/services/jev_reranker.py`.
- Limits: 64k tokens state+questions (Greek ≈ 1.4 tokens/char); the gateway is rate-limited by
  tokens — keep ≤ 12 concurrent requests, back off with jitter on 429/503, make runners
  resumable. Price ≈ $0.04 per million input tokens: log the cost of every run.
- Question design: one literal, observable fact per question ("The passage contains the word
  αὐτεξούσιον", "The translation renders the same passage as the original"); no dates, no
  counting, no stance labels; decompose broad questions. Re-ask with a paraphrase when a
  decision depends on one answer. Store questions and results under
  `data/quality/<yyyy_mm_dd>_<slug>/`.

## 7. How changes are made (house procedure — follow it exactly)

For each coherent batch (≤ ~100 decisions, one theme):

1. Write the pair `scripts/data_YYYY_MM_DD_<slug>.py` (the WHAT: one entry per decision, with a
   `#` comment quoting its evidence and source) and `scripts/apply_YYYY_MM_DD_<slug>.py` (the HOW),
   modelled on recent `scripts/apply_2026_08_*` / `apply_2026_09_*` scripts.
2. The apply script: `--dry-run` first; **preconditions** re-checked at run time (the value you
   expect to replace is still there, the ids still exist) — skip and log if not; **idempotent**
   (stamp `metadata.<wave>_<date>` and skip stamped records); back up
   (`data/kg/nodes.jsonl.bak-<slug>`, same for edges; do not commit backups if `.gitignore`
   excludes them); **assert invariants before writing**: no duplicate node ids, no dangling
   endpoints, `source == source_id` and `target == target_id`, no duplicate triples, no
   self-loops, no dangling metadata pointers.
3. New nodes: gate them with `python3 scripts/check_ingestion_rules.py --new-only delta.json`
   (must exit 0). A node without an edge does not count as ingested.
4. After applying, run all gates from the repo root with `PYTHONPATH=.`:
   `scripts/check_corpus_invariants.py`, `scripts/check_greek_gate.py`,
   `scripts/check_citations_gate.py`, `scripts/check_kg_work_id_uniqueness.py`, plus
   `scripts/check_kg_corpus_locus_parity.py` and `scripts/check_scholarly_sources_manifest.py`
   when relevant. Then regenerate `scripts/gen_stats.py` and
   `scripts/export_publications_bibtex.py`. Any new failure = revert the batch and fix.
5. Write `data/audit/YYYY-MM-DD_<slug>_applied.md` (French): what changed, why, the decision
   records (or a link to `data/audit/YYYY-MM-DD_<slug>_decisions.jsonl`), counts, and every
   `needs_romain` item.
6. Commit the batch alone (conventional commit, e.g. `fix(kg): realign Melito Peri Pascha
   translations with their sections`), body = summary + evidence pointers. No AI attribution.

Work on a branch `data/verification-<yyyy-mm-dd>`; push it and open **one pull request** that you
keep updating (never push to `main`, never deploy, never touch the production DB — deployment is
Romain's decision).

## 8. Final deliverable

`data/audit/YYYY-MM-DD_cloud_verification_summary.md` (French) and the PR description with:
counts by verdict and by priority; every correction with its source; false positives found in
the Jev queues (they calibrate the next campaign); the full `needs_romain` list grouped by
volume/source to look up; systemic defects discovered (patterns, not only items) with a proposed
structural fix; what you did not reach.

## 9. Stop conditions

Stop and report when: the queues of priorities 1–4 are exhausted; or every remaining item is
`needs_romain`; or a gate fails in a way you cannot fix without touching unrelated data; or you
find evidence that a rule in `CLAUDE.md` conflicts with a required fix (report it, do not work
around it).
