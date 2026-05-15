# Corpus Restoration Runbook

This runbook restores corpus coverage after a Scaife/Perseus outage or a KG
snapshot regression.

## Baseline

- The target corpus baseline is the pre-the platform migration corpus: roughly 69,000
  passages.
- The post-the platform KG snapshot currently exposes about 16,000 passage nodes. This
  is a KG snapshot coverage problem, not proof that the underlying philological
  target has changed.
- Do not use synthetic Greek or Latin to fill gaps. Every restored passage must
  come from an identified corpus source and retain source metadata.

## Source Order

Use sources in this order:

1. Scaife CTS when `https://scaife-cts.perseus.org/api/cts` is healthy.
2. PHI Latin Texts for Latin authors covered by Packard Humanities Institute.
3. Institutional JSON mirrors for TLG/UCA, Stoa direct exports, or authorized
   local dumps.
4. Patristic source exports only when the source has a traceable edition or
   scan provenance.

The shared service is `eleutheria_database.services.scaife.fetch_work_with_fallbacks`.
It accepts:

- `source_policy="scaife"` for the legacy path.
- `source_policy="auto"` plus `fallback_sources=["phi", "json_mirror"]`.
- A direct source name such as `phi` or `json_mirror`.

## PHI Example

```bash
python - <<'PY'
from eleutheria_database.services.corpus_sources import fetch_phi_latin_work

payload = fetch_phi_latin_work(
    work_urn="urn:cts:latinLit:phi0474.phi049.perseus-lat1",
    author_num=474,
    work_num=54,
)
print(payload.source_name, len(payload.sections))
PY
```

## Re-dispatch The 2026-05-15 Blocked Batch

Dry-run first:

```bash
python database/scripts/redispatch_blocked_scaife_workflows.py \
  --source-policy auto \
  --fallback-source phi \
  --fallback-source json_mirror \
  --source-options-file data/ingestion_log/20260515-scaife-fallback-options.example.json \
  --dry-run
```

Dispatch when the preview shows correct source options:

```bash
TEMPORAL_HOST=localhost:7233 \
TEMPORAL_TASK_QUEUE=eleutheria-ingestion \
python database/scripts/redispatch_blocked_scaife_workflows.py \
  --source-policy auto \
  --fallback-source phi \
  --fallback-source json_mirror \
  --source-options-file data/ingestion_log/20260515-scaife-fallback-options.example.json
```

For JSON mirrors, the options file can use `{work_node_id}` and `{cts_urn}`
templates in URI fields.

## Validation

After ingestion:

```bash
python scripts/export_kg_snapshot.py
make kg-shacl
python scripts/export_publications_bibtex.py
```

The invariant SHACL report must conform. The quality SHACL report is allowed to
contain warnings, but it is the queue for scholarly review.

## Passage Role Policy

Every passage should eventually carry `metadata.passage_role`:

- `original`: Greek, Latin, Hebrew, Arabic, or another source language text.
- `translation`: English/French/etc. translation tied to `source_passage_id`.
- `paraphrase`: non-verbatim scholarly paraphrase.

Linguistic analysis must filter to `passage_role="original"`.
