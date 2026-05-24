"""Backfill work-level CTS URNs + ingest classification into the corpus manifest.

ingest_class: 'scaife' (resolved URN -> fetchable), 'manual_source' (no URN,
needs a DOCTORAT/SC edition), 'ambiguous' (>1 work URN, needs disambiguation).
Dry-run by default; --commit writes data/corpus/manifest.jsonl.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path

from scripts.corpus_lib import read_jsonl, write_jsonl
from scripts.corpus_urn import derive_work_urn

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data" / "corpus" / "manifest.jsonl"
PASSAGES = ROOT / "data" / "corpus" / "passages.jsonl"


def main(commit: bool) -> int:
    urns_by_work: dict[str, list[str]] = defaultdict(list)
    for p in read_jsonl(PASSAGES):
        urns_by_work[p["work_canonical_id"]].append(p.get("cts_urn"))

    manifest = read_jsonl(MANIFEST)
    counts = {"scaife": 0, "manual_source": 0, "ambiguous": 0}
    for w in manifest:
        urn, status = derive_work_urn(urns_by_work.get(w["canonical_id"], []))
        if status == "resolved":
            w["cts_urn"] = urn
            w["source"] = f"scaife:{urn}"
            w["ingest_class"] = "scaife"
        elif status == "ambiguous":
            w["ingest_class"] = "ambiguous"
        else:
            w["ingest_class"] = "manual_source"
        counts[w["ingest_class"]] += 1

    print(f"scaife: {counts['scaife']}  manual_source: {counts['manual_source']}  ambiguous: {counts['ambiguous']}")
    if not commit:
        print("[DRY-RUN] --commit to write manifest")
        return 0
    write_jsonl(MANIFEST, sorted(manifest, key=lambda w: w["canonical_id"]))
    print(f"wrote {MANIFEST}")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--commit", action="store_true")
    raise SystemExit(main(ap.parse_args().commit))
