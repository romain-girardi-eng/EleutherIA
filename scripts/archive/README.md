# Archived one-off scripts

Dated, single-use maintenance scripts kept as a reproducibility record of the
knowledge-graph curation campaign (enrichment waves, deduplication passes,
citation repairs, corpus ingestion batches). Each script was run once against
a specific dataset snapshot and is preserved exactly as executed.

**Do not re-run these against the current dataset.** They assume the data
state of their date (see the `_YYYY_MM_DD` suffix) and some reference
snapshot files that are archived in the Zenodo releases rather than in this
repository (concept DOI: [10.5281/zenodo.17379489](https://doi.org/10.5281/zenodo.17379489)).

Operational scripts (gates, validators, exporters, deploy tooling) live in
the parent `scripts/` directory.
