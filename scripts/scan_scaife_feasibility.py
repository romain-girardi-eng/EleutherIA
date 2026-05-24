"""Feasibility scan: can each scaife work be gap-filled at matching granularity?

Reffs-ONLY probe (no passage downloads, no DB writes). For each manifest work
with ingest_class == 'scaife', compute the granularity the corpus already uses
(max CTS ref depth of its existing passages) and ask Scaife for reffs at that
level. Classify:

  clean             - reffs at target level returned AND include >=80% of the
                      work's existing passage URNs -> gap-filling will work.
  format_mismatch   - reffs at target level exist but don't match existing URNs
                      (different ref formatting/edition) -> manual.
  granularity_only  - target level unavailable; only a coarser/finer level
                      returns reffs -> filling would duplicate -> manual.
  no_reffs          - Scaife returns nothing usable -> manual.

Writes data/corpus/scaife_feasibility.tsv + prints a summary.
"""
from __future__ import annotations

import time
from collections import Counter, defaultdict
from pathlib import Path

from database.scripts.fetch_scaife_work import get_valid_reff
from scripts.corpus_lib import read_jsonl

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data" / "corpus" / "manifest.jsonl"
PASSAGES = ROOT / "data" / "corpus" / "passages.jsonl"
OUT = ROOT / "data" / "corpus" / "scaife_feasibility.tsv"


def ref_depth(cts_urn: str) -> int:
    ref = cts_urn.split(":")[-1] if ":" in cts_urn else ""
    return ref.count(".") + 1 if ref else 1


def safe_reff(work_urn: str, level: int) -> list[str]:
    try:
        return get_valid_reff(work_urn, level=level) or []
    except Exception:
        return []


def main() -> int:
    existing_urns: dict[str, set[str]] = defaultdict(set)
    for p in read_jsonl(PASSAGES):
        if p.get("cts_urn"):
            existing_urns[p["work_canonical_id"]].add(p["cts_urn"])

    works = [w for w in read_jsonl(MANIFEST) if w.get("ingest_class") == "scaife"]
    lines = ["status\ttarget_lvl\texisting\treff_at_target\toverlap\twould_add\tcanonical_id\tcts_urn"]
    counts: Counter = Counter()

    for i, w in enumerate(works, 1):
        cid, urn = w["canonical_id"], w.get("cts_urn", "")
        ex = existing_urns.get(cid, set())
        tlvl = max((ref_depth(u) for u in ex), default=2)
        reffs = set(safe_reff(urn, tlvl))
        if reffs:
            overlap = len(ex & reffs)
            frac = overlap / len(ex) if ex else 0.0
            if frac >= 0.8:
                status, would_add = "clean", len(reffs - ex)
            else:
                status, would_add = "format_mismatch", 0
        else:
            alt = safe_reff(urn, tlvl - 1) or safe_reff(urn, tlvl + 1)
            status = "granularity_only" if alt else "no_reffs"
            overlap, would_add = 0, 0
        counts[status] += 1
        lines.append(f"{status}\t{tlvl}\t{len(ex)}\t{len(reffs)}\t{overlap}\t{would_add}\t{cid}\t{urn}")
        print(f"[{i:>2}/{len(works)}] {status:16} ex={len(ex):>4} reff={len(reffs):>4} +{would_add:>4}  {cid[:48]}")
        time.sleep(0.5)

    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nSUMMARY: {dict(counts)}")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
