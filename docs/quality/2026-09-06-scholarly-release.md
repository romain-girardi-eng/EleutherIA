# Scholarly publication and source-identity release — 2026-09-06

This release resolves the supplied streaming audit and the concrete source and
evaluation defects found in the authenticated production checks. It makes no
claim of universal scholarly infallibility.

## Scholarly method

Ancient references use author/work and the exact conventional locus: book,
chapter, section, fragment collection/number, Bekker or Stephanus. A printed or
PDF page is not required, and an unspecified edition is not a finding of
inauthenticity. When a different edition supplies the same CTS work and locus,
the verifier can use that witness's actual text; another work or chapter cannot
substitute. Explicit identity corruption and contaminated excerpts are separate
issues. Modern scholarly claims normally use a printed page or stable locator.

A focused answer can be supported by one primary locus. The content precheck no
longer demands three references; the complete citation audit and quote-fidelity
checks still run. The synthesis is question-led, permits a precise paraphrase,
quotes when wording matters, preserves the language of a published translation,
and does not force either controversy or a preferred verdict unsupported by the
evidence. The interface uses the same ancient-locus/pagination distinction.

## Source repairs

| Material | Result and evidence |
|---|---|
| Cicero, De fato | 48 sections copied from pinned Perseus TEI, Müller/Teubner 1915; existing IDs retained and exact corpus links restored |
| Romans 9 | Missing work added with one 33-verse chapter unit from Westcott–Hort/Perseus; chapter-only coverage explicit |
| Augustine, De libero arbitrio | 170 conventional loci (171 pre-existing corpus records) reattached to PL 32/Migne via the named sections on Augustinus.it; correct work identity CPL 260; false City-of-God CTS identity removed |
| Augustine, De civitate Dei | 81 chapter units for books 5, 12, 14 copied from pinned Hoffmann/CSEL 40 TEI; production's 5.10 paragraph-2 citation restored to actual Latin and correct work |
| Legacy City-of-God excerpts | 160 old records retained as research notes, excluded from quotation evidence because of mixed apparatus/crossed boundaries; this is not a rejection for missing pagination |
| Dihle 1982 | Existing quotation visually checked on printed p. 68 / PDF p. 75; file offsets removed from the active citation fields; no copyrighted PDF/image redistributed |
| Origen evaluation translations | Three existing SC 268 / SC 226 French translations get separate French manifestations and correct translation roles; conventional loci retained and uncertain machine CTS identifiers removed |

The source files, hashes, extraction policies and licensing notices are under
`data/corpus/sources/2026-09-05/`. No Greek or Latin was generated. All data
mutations have replayable data/apply scripts, dry-run validation, backups, and
idempotence checks. The ingestion checker can preflight updated existing records
alongside a new-node delta, while rejecting new IDs disguised as updates.

The database loader now respects declared manifestation language before guessing
from an old identifier suffix. This prevents a French translation with a legacy
`_eng` identifier from becoming an English witness in the served database.

## Evaluation repair

All **29 invalid gold references** are resolved individually, including works
previously put in the non-work entity channel. The Romans expectation is
strengthened with an exact primary chapter UUID. All existing passage
requirements are retained. The Origen query now distinguishes De Principiis
III.1 from the Commentary-on-Genesis excerpt transmitted in Philocalia 23.
Two gold sentences are corrected from the actual French evidence: Philocalia is
not labelled a catena witness of De Principiis, and the original gold's reversed
attribution of wrongdoing to God is corrected. These edits and their hashes are
recorded in `data/audit/2026-09-05_eval_gold_repair.json`.

Schema/gold validity does not imply perfect retrieval. The deterministic lexical
baseline is kept as a baseline, not relabelled as the live GraphRAG's quality.
Strict evaluation rejects individual missing evidence sets and unobserved required
safety checks; the thresholds are not averaged into a flattering single score.

## Publication and CLI

The original audit's draft-storage leak, lost verdict citations, and read-error
persistence are repaired at agent, cache and browser boundaries. A public ledger
contains published claims; rejected draft wording stays out of public payloads.
The answer cache uses a new schema version. The full verdict survives EOF and
terminal enrichment; previews and loose chunks never become fallback answers.

The CLI uses the same authenticated SSE endpoint as the site, can log in by OTP
without a browser, preserves structured evidence, writes private atomic JSON
artifacts, and returns distinct failure codes. Its test commands are noninteractive
and use the same Python interpreter. See `docs/operations/headless-answer-quality.md`.

## Validation and deployment

Before release: 361 frontend tests; 1869 GraphRAG tests (plus the subsequently
added focused prompt/locus cases); 257 backend/source/checker tests; 35 source and
historical-repair compatibility tests. Full corpus referential invariants, the
KG/corpus locus-parity gate, and KG work-identity uniqueness pass with zero
violations. TypeScript/build and targeted lint checks are recorded in the release
execution log. Production rollout and the latest headless acceptance results are recorded in
[release PR #8](https://github.com/romain-girardi-eng/EleutherIA/pull/8).

## Production acceptance findings

The atomic corpus deployment passed its staging and live gates: 23,330 KG nodes,
55,889 asserted edges, 190 served works, 23,394 passages and 22,854 citation links.
The prior database generation and a full pre-release dump remain available for rollback.
The API and public Cloudflare Pages frontend were deployed from `3fb901d141c55c2680d4182960454049c37635cd`.

The first four-case Gemini run exposed a false acceptance in the evaluation
harness: it read a legacy citation shape and did not fail an unobserved required
retrieval channel. Replaying its captured SSE with the corrected observer
rejects Cicero 41, accepts the two Augustine loci, and records abstention for the
unattested title. This first run is not a passed scientific acceptance test.
The corrected observer reads actual tool-result IDs, maps only declared exact
passage twins, and separately requires retrieved and published evidence sets.
It verifies the served release through `/api/health` before sending live queries.

The same investigation fixed work-scoped search: a KG work ID could be compared
with a corpus UUID in global hybrid results and silently discard the source.
Scoped SQL now resolves work identities and searches conventional loci as well as
text. Anteposed source markers ("In De fato 41 [P1], Cicero distinguishes...")
now carry the complete proposition to verification, instead of a bare label.
Explicit answer-length requests take precedence over an essay-length default.

GPT's configured proxy reported an exhausted quota and Claude an unavailable
authentication session; Gemini passed an actual generation probe. Those provider
conditions are not scholarly findings. A provider failure now stops the research
loop before an expensive degraded synthesis; the live CLI outage regression
returned exit 3 in 11.2 seconds, with no answer published. Cancellation returns
130 consistently, including a signalled evaluation subprocess.
