# GraphRAG publication integrity and research experience — 2026-09-05

This change fixes the supplied `needs_fix` audit and defects observed in the
actual research workflow at https://free-will.app/graphrag/. It is not a
certification of factual infallibility or of the entire scholarly corpus.

## Production observations before the change

The serving API checkout and Cloudflare Pages production deployment both identify
`70e2673af6e1b6b29fb680648fd029462145ecdc`. The separately running frontend Docker
image is older; updating that container alone does not update the public website.
Pages project: `eleutheria`. Previous production deployment:
`de261e44-8123-48aa-a28e-8796f5611229`.

An authenticated browser query asked (French):

> Comment distinguer le témoignage de Cicéron sur Chrysippe de l’interprétation
> moderne du déterminisme stoïcien ? Donne les passages précis et signale les
> limites des preuves.

Observed timestamps: question 21:57:40, answer 22:10:05 (Europe/Paris), about
12 minutes 25 seconds. This is one observed run, not a latency distribution.
The final UI reported **21 sentences withheld**, 42 exportable citations,
35 modern references and 15 graph sources. The last count describes a different
object from citations and should not be read as a verification count.

The answer expanded into separate sections on Epictetus, the discovery of the
will, and Augustine/grace. The synthesis template explicitly demanded every
retrieved debate and use of the entire available output budget, even for a
focused question.

A published Dihle citation advertised `p.3054-3057, 3110-3127`. The exact node
`scholarly_argument_dihle_greek_concept_of_will_0` already carries
`needs_page_verification: "Four-digit values: offsets, not page ranges."`.
The citation policy did not recognize that field or textual debt notes. Its
source panel also displayed the older `citation_verified: true` without the
outstanding verification note. This is an observed publication defect, not a
claim that Dihle's underlying argument is false.

An Augustine draft citation also exposed conflicting source metadata:
`passage_aug_civ_5_10_2` labels *De Civitate Dei* but carries `work_title:
De Libero Arbitrio` and an inconsistent work URN. The linked corpus passage
`978fc8cb-d39e-4fd7-a690-1a2c958c634a` uses the corrected
`stoa0040.stoa003.opp-lat3:5.10` identifier. A full identity/manifestation repair
is separate data work; this change does not silently rewrite the corpus.
The [Perseus catalogue](https://catalog.perseus.tufts.edu/catalog/urn%3Acts%3AlatinLit%3Astoa0040.stoa003)
identifies `stoa0040.stoa003` as *De civitate dei*.

## Publication and persistence changes

- One shared public serializer covers synchronous, preview and terminal agent
  payloads. The working/internal answer remains intact.
- Private draft diagnostics are removed from nested public payloads, the persistent
  answer cache and browser snapshots. This includes `debug_trace`, answer/raw
  excerpts, raw output and private reasoning. Pre-verification research-graph
  claims are excluded; the post-verdict claim ledger supplies public claims.
- Rejected/unverified ledger wording and diagnostic copies of failed claims,
  sentences and quoted spans are excluded. Gate results, evidence identifiers,
  sentence indices, failure classes and counters remain inspectable.
- Persistent answer-cache schema advances to v4, making earlier rows miss without
  deleting database records. Read sanitization also protects legacy payloads.
- `answer_final` retains citations, claim ledger, publication gate and quality
  metadata immediately. Terminal graph/trace enrichment cannot erase received
  provenance with empty defaults. A blocking verdict from either boundary wins.
- EOF and `reader.read()` exceptions use the same settlement/persistence path.
  A connection error remains visible and survives rehydration with the answer.
- Citation previews and loose chunks never become fallback assistant answers.
  Existing browser snapshots are sanitized during rehydration.

The serializer is a deliberate public projection; new diagnostic fields must be
reviewed against it. Tests inspect the complete serialized payload, not just the
answer-bearing fields.

## Relevance and source policy

The synthesis now selects the frames needed to answer the actual question, with
600–1200 words as a normal focused-answer target rather than an output cap. Broad
surveys and explicit requests for depth can still be longer. Source attribution,
verbatim quotation requirements, objections and uncertainty remain required.
This is a prompt correction, not a measured guarantee of improved live relevance.

Page-verification and source-identity debt are discovery-only. Explanatory strings
activate debt flags, just as booleans do; explicit false/empty values do not.
Existing search, dossier and verifier consumers use the central policy. A stale
`verified` label no longer overrides unresolved page debt. The UI presents that
debt beside the source and disables citation export from that record.

## Research experience

The entry screen has a stable scholarly heading, a labelled multiline question,
three useful research examples, and progressively disclosed model/settings.
It uses the project's existing Instrument Serif / DM Sans, parchment and ink
visual direction. The continuously changing heading and animated input border
are removed from this workflow.

The answer begins with an evidence review: checks passed, partial, withheld, or
no report. Automatic checks are explicitly distinguished from scholarly
certification. Readers can inspect the published claim ledger and open its
supporting passage or node. Completion foregrounds the sources while preserving
an already-open passage. Unverified draft prose is no longer displayed as an
answer preview. New copy is supplied in EN, FR, DE, IT and modern Greek.

The new review region uses semantic status messages and source actions retain
keyboard focus indicators, following the W3C guidance on
[status messages](https://www.w3.org/WAI/WCAG22/Understanding/status-messages.html)
and [labels](https://www.w3.org/WAI/WCAG22/Understanding/labels-or-instructions.html).
This is not a whole-site WCAG conformance claim.

### Heuristic critique of the observed original workflow

Subjective inspection scores, not measured user research:

| Heuristic | Score / 4 | Main finding |
|---|---:|---|
| System status | 2 | Draft appears long before citation verification completes |
| Domain language | 2 | Pipeline jargon dominates the entry point |
| User control | 3 | Stop and concurrent questions exist |
| Consistency | 2 | Citation counts differ by surface without explanation |
| Error prevention | 1 | Known page debt still becomes a published citation |
| Recognition | 2 | Verification evidence is not adjacent to the answer |
| Efficiency | 2 | Targeted question becomes a 12-minute expansive essay |
| Minimal design | 2 | Changing headline and multiple technical badges compete |
| Recovery | 1 | Verdict provenance can disappear on transport failure |
| Help | 2 | Wait estimate exists, little guidance on a useful question |
| Total | 19 | Targeted fixes required |

Anti-pattern verdict: the animated heading/shine input and implementation-led
labels weaken the otherwise distinctive manuscript visual identity. Strong
existing elements are the ancient/modern citation distinction, adjacent source
panel and visible stop control. The cognitive-load checklist has three failures
(hierarchy, distraction and progressive disclosure): moderate in this workflow.

Persona concerns: a doctoral researcher cannot safely export an offset as a
printed page; a first-time student lacks a concrete research starting point;
a keyboard/screen-reader user encounters an unlabelled question field and
continuous draft announcements. The changes above address these observed issues.

## Evaluation limits

The offline lexical baseline completed 57/57 retrieval requests and its schema
validated. **This is not 57 correct generated answers.** Generation and its safety
dimensions were not run. The gold validator found **29 invalid identifiers**, so
release comparison remains blocked. On the explicitly valid subset, passage
recall was 0.2667 (20 cases) and complete-evidence recall 0.25. These figures
measure the snapshot lexical runner, not the deployed agentic GraphRAG.

The diagnostic artifact is `/tmp/eleutheria-eval-20260905-lexical.json`; run it via
`tests/eval/run_eval.py --runner snapshot-lexical --include-ood --include-repair-wave`.
No historic baseline was overwritten or gold expectation weakened.

Release validation must record code/build results and a new authenticated live
run after deployment. A single passing answer cannot establish zero hallucination
or academic irreproachability across the corpus.

## Headless CLI validation added during the review

Both browser test tabs were closed at the user's request. `eleutheria ask` now
uses the real SSE endpoint, supports API-scoped login, `--json`, `--output`,
`--model`, `--mode`, `--fresh` and a configurable 1200-second timeout. It preserves
verdict provenance on EOF/network errors and returns distinct exit codes. The
quality harness can be invoked as `eleutheria test answers`; strict gates are
enabled there, and invalid gold blocks live evaluation before any provider call.
See [headless instructions](../operations/headless-answer-quality.md).

An authenticated production CLI test, before deployment of these backend fixes,
asked specifically about *De fato* 41 in at most 200 words. It took **155.394 s**,
reported model `gpt-5.6-sol`, and returned HTTP 200 with CLI exit **2**: partial
publication, one sentence removed, two surviving modern citations and no surviving
primary citation. Both `answer_final` and `complete` were received (207 events).
The private diagnostic output is
`/tmp/eleutheria-cli-live-cicero-before-20260905.json`.

The missing primary citation was `passage_cic_fat_41`. Its snapshot explicitly
records `related_non_exact_pending_edition_adjudication` and only a related corpus
UUID; it does not provide an exact verified twin. The text verifier independently
found wording in *SVF* II.974, which is not sufficient to silently replace a
Ciceronian edition/reference. The central citation policy now also recognizes
this pending-edition parity state as discovery-only. Repairing the source mapping
requires actual edition adjudication, not a fuzzy fallback that bypasses the gate.

Verified local results at this stage: GraphRAG 1859 passed / 1 skipped, backend
228 passed / 1 skipped, all frontend suites 360 passed. The subsequently added
pending-edition policy regression and CLI/evaluation suites are recorded separately
in the final validation record. The offline strict CLI run correctly returned
failure for the 29 invalid gold identifiers; that failure is not hidden as a
passing academic benchmark.


A second authenticated CLI test asked about a deliberately unattested Chrysippus
work on quantum mechanics, explicitly requesting no invented reference. In
**100.646 s** the server returned a blocked verdict: **empty answer, zero
citations**, HTTP 200 and CLI exit 2. Both verdict and terminal arrived (195
events). Private output: `/tmp/eleutheria-cli-live-unanswerable-20260905.json`.
This demonstrates correct abstention for this one adversarial case, not universal
absence of fabrication.

Production deployment status at handoff: **not deployed**. The live observations
above concern the previous serving code; they do not measure the new synthesis
prompt. Changes remain reviewable in the local working tree. The pre-existing
credential-related edits were preserved. No production corpus or account policy
was modified. CLI login used the user's normal OTP flow and stores only the
API-scoped private session.


Final additional validation: **134 CLI/evaluation tests passed, 1 optional live
smoke test skipped**; the pending-edition source policy and verifier wiring
passed 88 focused tests; shared public serialization and service publication
boundaries passed 14 focused tests. TypeScript, targeted ESLint/Ruff, production
frontend build and SEO output validation passed. The full frontend suite was
run through `eleutheria test frontend` and exited successfully (360 tests).
The development Vite process was stopped after the browser checks.
