"""PART B.1 -- deterministic normalization table of existing `school` string
values -> canonical label, with counts. No Jev call. Read-only on nodes.jsonl.

The project already froze a controlled vocabulary for `school` on
2026-08-17 (knowledge graph/ontology/school_scheme.json, R18 in
ingestion-rules.md). This script (a) tallies every literal `school` string
value currently on data/kg/nodes.jsonl (all node types, since passages carry
most of the assignments) and (b) maps each one deterministically: exact
match against the frozen scheme's prefLabels is the canonical mapping;
anything else is normalized (casefold, strip whitespace/punctuation,
singular/plural, known synonym table) and flagged if it still doesn't land
on a canonical label.
"""

from __future__ import annotations

import csv
import json
from collections import Counter

from lib_common import CAMPAIGN_DIR, REPO_ROOT, load_all_nodes_school_field

SCHEME_PATH = REPO_ROOT / "knowledge graph" / "ontology" / "school_scheme.json"

# Deliberately small: synonym / spelling variants seen in comparable projects
# and in the frozen scheme's own `deprecated_mappings`. Anything not covered
# here and not already a canonical label is left as `NEEDS_REVIEW`.
SYNONYM_MAP = {
    "stoics": "Stoic",
    "stoicism": "Stoic",
    "epicureans": "Epicurean",
    "epicureanism": "Epicurean",
    "peripatetics": "Peripatetic",
    "peripateticism": "Peripatetic",
    "aristotelian": "Peripatetic",
    "aristotelianism": "Peripatetic",
    "neoplatonism": "Neoplatonist",
    "neoplatonic": "Neoplatonist",
    "neo-platonist": "Neoplatonist",
    "neo-platonism": "Neoplatonist",
    "platonism": "Platonist",
    "platonic": "Platonist",
    "middle platonism": "Middle Platonist",
    "middle-platonist": "Middle Platonist",
    "skeptics": "Skeptic",
    "skepticism": "Skeptic",
    "sceptic": "Skeptic",
    "scepticism": "Skeptic",
    "pyrrhonist": "Skeptic",
    "pyrrhonism": "Skeptic",
    "academic skepticism": "Skeptic",
    "cynics": "Cynic",
    "cynicism": "Cynic",
    "christian apologetic": "Christian Apologetics",
    "apologetic": "Christian Apologetics",
    "apologetics": "Christian Apologetics",
    "christian platonist": "Christian Platonism",
    "christian platonic": "Christian Platonism",
    "patristics": "Patristic",
    "latin patristics": "Latin Patristic",
    "presocratics": "Presocratic Philosophy",
    "presocratic": "Presocratic Philosophy",
    "doxographic": "Doxographer",
    "doxography": "Doxographer",
}


def main() -> None:
    scheme = json.loads(SCHEME_PATH.read_text(encoding="utf-8"))
    canonical_labels = {c["prefLabel"] for c in scheme["concepts"]}
    canonical_by_casefold = {lbl.casefold(): lbl for lbl in canonical_labels}

    nodes = load_all_nodes_school_field()
    counts: Counter[str] = Counter()
    counts_by_type: dict[str, Counter[str]] = {}
    for n in nodes:
        s = n.get("school")
        if not s or not isinstance(s, str):
            continue
        s = s.strip()
        if not s:
            continue
        counts[s] += 1
        counts_by_type.setdefault(s, Counter())[n.get("type") or "?"] += 1

    rows = []
    for raw, n in counts.most_common():
        if raw in canonical_labels:
            canonical, method = raw, "already_canonical"
        else:
            cf = raw.casefold().strip()
            if cf in canonical_by_casefold:
                canonical, method = canonical_by_casefold[cf], "casefold_match"
            elif cf in SYNONYM_MAP:
                canonical, method = SYNONYM_MAP[cf], "synonym_table"
            else:
                canonical, method = "NEEDS_REVIEW", "unmapped"
        types = ",".join(f"{t}:{c}" for t, c in counts_by_type[raw].most_common())
        rows.append({
            "raw_value": raw, "count": n, "proposed_canonical": canonical,
            "method": method, "by_type": types,
        })

    out_csv = CAMPAIGN_DIR / "school_normalization_table.csv"
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["raw_value", "count", "proposed_canonical", "method", "by_type"])
        w.writeheader()
        w.writerows(rows)

    n_unmapped = sum(1 for r in rows if r["method"] == "unmapped")
    n_total_assignments = sum(counts.values())
    print(f"distinct raw school strings: {len(rows)}")
    print(f"total non-null school assignments (all types): {n_total_assignments}")
    print(f"unmapped (NEEDS_REVIEW): {n_unmapped}")
    print(f"wrote -> {out_csv}")


if __name__ == "__main__":
    main()
