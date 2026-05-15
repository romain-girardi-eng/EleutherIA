# Zenodo Versioning Strategy

EleutherIA uses a Zenodo concept DOI for the rolling archive and version DOIs
for frozen scholarly releases.

## Policy

- Concept DOI: `10.5281/zenodo.17379489`
- Frozen release cadence: semi-annual, normally June and December.
- Release labels: `v5.1.0`, `v5.2.0`, and so on.
- Each thesis or article citation must include the version DOI, Git commit hash,
  and KG snapshot date.
- The concept DOI is acceptable for general project references, but not for
  reproducibility claims.

## Release Checklist

1. Export the live KG snapshot:

   ```bash
   python scripts/export_kg_snapshot.py
   ```

2. Regenerate RDF and validate SHACL:

   ```bash
   make kg-rdf
   make kg-shacl
   ```

3. Export the bibliography:

   ```bash
   make kg-bibtex
   ```

4. Record checksums:

   ```bash
   shasum -a 256 data/kg/nodes.jsonl data/kg/edges.jsonl data/rdf/eleutheria.ttl data/kg/publications.bib
   ```

5. Create the GitHub release and upload to Zenodo under the existing concept
   record.

6. Update `CITATION.cff`, `.zenodo.json`, and the release notes with the
   version DOI returned by Zenodo.

## Citation Template

Girardi, Romain. *EleutherIA: An AI-Powered Scholarly Research Platform for
Ancient Philosophy on Free Will*. Version `vX.Y.Z`, Zenodo version DOI
`10.5281/zenodo.NNNNNNN`, Git commit `COMMIT`, KG snapshot `YYYY-MM-DD`,
CC BY 4.0.
