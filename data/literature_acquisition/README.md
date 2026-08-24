# Literature acquisition archive

`manifest.jsonl` fingerprints every top-level PDF and EPUB in this directory.
It distinguishes intellectual works from their scan/OCR manifestations and
records scope, completeness and audit status. `reuse_status` is deliberately
fail-closed: local availability or public downloadability is not a republication
license.

Regenerate and verify with:

```bash
python3 scripts/build_literature_acquisition_manifest.py
python3 -m pytest tests/test_literature_acquisition_manifest.py
```

This artifact inventory complements `data/scholarly_sources/manifest.jsonl`.
The latter is currently an OCR/KG-ingestion manifest with a known schema drift;
the SOTA program will migrate both into one versioned source/manifestation
model without treating partial ingestion as complete.
