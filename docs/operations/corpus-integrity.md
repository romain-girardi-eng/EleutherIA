# Corpus Integrity — Tamper-Evidence & Edition Provenance

How EleutherIA proves that the ancient text stored in `free_will.passages`
is the text that was ingested from a verified critical edition, and that it
has not silently drifted since.

## Invariant

> **No script may mutate `passages.text_content` outside an ingest pipeline.**
>
> The only code allowed to write `text_content` is the ingest paths listed
> below (which set `text_sha256` at insert time). Audit and repair scripts
> are report-only with respect to text: they may flag, never rewrite.
> Any legitimate re-ingest (e.g. replacing an OCR batch with a better
> transcription) goes through the normal ingest script, produces fresh
> checksums, and is followed by a reviewed `--update-baseline` run.

## Components

| Piece | Location |
|---|---|
| Migration (columns + constraints) | `database/migrations/20260610_03_text_integrity.sql` |
| Canonical hashing + drift comparison | `database/src/eleutheria_database/services/text_integrity.py` |
| Drift auditor | `database/scripts/philological_audit/audit_text_drift.py` |
| Checksum baseline | `data/integrity/text_checksums.jsonl.gz` |
| Drift report output | `data/philological_audit/text_drift.jsonl` |
| Provenance backfill generator | `database/scripts/generate_text_provenance_backfill.py` |
| Unit tests (pure functions) | `database/tests/unit/test_text_integrity.py` |

## Checksum contract

`passages.text_sha256` = SHA-256 hex digest of the **NFC-normalized**,
UTF-8 encoded `text_content`.

- NFC normalization makes the digest independent of how polytonic Greek
  diacritics happen to be encoded (precomposed vs combining), which is the
  one byte-level difference that is *not* a textual change.
- Everything else — whitespace, punctuation, casing, a single iota — changes
  the digest. Nothing is stripped or rewritten before hashing.
- Canonical implementation: `eleutheria_database.services.text_integrity.text_sha256`.
  The standalone ingest scripts carry an identical inline fallback (guarded
  by `try/except ImportError`); a unit test pins the two to the same output.

### Ingest paths that populate `text_sha256`

All three are **deploy-safe before the migration runs**: they probe
`information_schema.columns` for `passages.text_sha256` and only include the
column once it exists.

1. `database/src/eleutheria_database/services/scaife.py::parse_and_insert`
   (Temporal Scaife ingestion workflow)
2. `database/scripts/ingest_scaife_work.py` (CLI Scaife ingest)
3. `database/scripts/import_sc/importer.py::SCImporter.import_work`
   (Sources Chrétiennes corpus import)

Rows ingested before this change have `text_sha256 IS NULL`; the first
baseline run still covers them because the auditor recomputes digests from
`text_content` directly. Backfilling the column for historical rows is a
separate, reviewed operation.

## Tamper-evidence workflow

### 1. Create the baseline (one-time, trusted state)

```bash
set -a; source .env; set +a   # DATABASE_URL must point at the corpus DB
.venv/bin/python database/scripts/philological_audit/audit_text_drift.py
```

First run (no `data/integrity/text_checksums.jsonl.gz` yet) snapshots every
passage's `{passage_id, sha256, work_canonical_id, canonical_ref,
passage_role}` into the gzipped JSONL baseline. Only create the baseline
from a database state you have just verified (e.g. right after the
integrity audit waves). The baseline file is deterministic (sorted by
passage_id, fixed gzip mtime) so it diffs cleanly in git — commit it.

### 2. Nightly drift check

```bash
.venv/bin/python database/scripts/philological_audit/audit_text_drift.py
```

Every later run recomputes digests from the live table and reports, per
passage:

- `added` — passage exists now but not in the baseline (new ingest?);
- `removed` — passage vanished (deletion, re-import under new UUIDs?);
- `changed` — same passage_id, different text digest — **the tamper signal**;
- `stored_text_sha256_mismatch` — the stored column disagrees with the
  recomputed digest (a write bypassed the ingest pipeline, or corruption).

Exit code `1` on any drift, `0` when clean — suitable for a cron/CI gate.
The report goes to `data/philological_audit/text_drift.jsonl`. The auditor
is strictly read-only against the database.

### 3. Manual adjudication

For every drifted row, decide which of these it is — individually, never in
bulk (per the project's no-auto-fix policy):

- **Legitimate ingest/re-ingest** (matching a reviewed PR or ingest log):
  accept, then `--update-baseline`.
- **Unexplained change**: treat as an incident. Recover the original text
  from the source edition under
  `~/Desktop/DOCTORAT/Doctorat SHAL/02_Corpus/` (SC editions) or the ingest
  JSON, re-ingest through the normal pipeline, and only then re-baseline.

```bash
# only after every diff is explained:
.venv/bin/python database/scripts/philological_audit/audit_text_drift.py --update-baseline
```

## Edition provenance (`passages.text_provenance`)

JSONB, nullable. Schema:

```jsonc
{
  "edition": "P.-Th. Camelot, 1958 (3rd ed.)",  // or null — see flag below
  "series": "SC 10bis",                          // edition series/volume, if any
  "source_collection": "sources_chretiennes",    // or "perseus_scaife", ...
  "source_type": "critical_edition",             // or "digital_corpus"
  "ingest_pipeline": "database/scripts/import_sc",
  "verified_from": "WORK_REGISTRY",              // where the edition claim was verified
  "needs_manual_edition_attribution": true,      // ONLY when edition is null
  "generated_on": "2026-06-10"
}
```

Rules:

- **Critical-editions-only**: `edition` is filled only from a verified
  source (the SC `WORK_REGISTRY` transcribes the editor/date from the
  published Cerf volumes). For Scaife/Perseus-ingested works the underlying
  edition is *not guessed*: the backfill emits `"edition": null` plus
  `needs_manual_edition_attribution: true`, and each work is attributed by
  hand afterwards.
- Backfill SQL is **generated, reviewed, then applied** — never executed by
  the generator itself:

```bash
.venv/bin/python database/scripts/generate_text_provenance_backfill.py \
    --output data/integrity/text_provenance_backfill.sql
# review every UPDATE, then apply manually, e.g.:
# .venv/bin/python database/scripts/apply_schema.py \
#     --migration data/integrity/text_provenance_backfill.sql
```

- Every generated UPDATE is guarded by `text_provenance IS NULL`, so
  manually curated provenance is never overwritten and re-running is
  idempotent.

## Migration notes

`20260610_03_text_integrity.sql` is single-transaction-safe (no
`CONCURRENTLY`) and defensive:

- columns added `IF NOT EXISTS`; digest format `CHECK` added `NOT VALID`;
- `passage_citations.kg_node_id → kg_nodes(node_id)` FK added `NOT VALID`
  (run the orphan pre-check in the file header, repair, then
  `VALIDATE CONSTRAINT fk_passage_citations_kg_node_id`);
- unique indexes (`passage_citations(passage_id, kg_node_id, citation_type)`
  and `passages(work_id, canonical_ref) WHERE passage_role = 'original'`)
  are only created when the duplicate pre-checks pass — otherwise the block
  raises a `WARNING` and skips, and the duplicates are adjudicated manually.

Translations/paraphrases (`passage_role <> 'original'`) intentionally share
their source passage's `canonical_ref`, hence the partial unique index.
