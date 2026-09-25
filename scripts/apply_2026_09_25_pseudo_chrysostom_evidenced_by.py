#!/usr/bin/env python3
"""Apply data_2026_09_25_pseudo_chrysostom_evidenced_by. Dry-run first.

    PYTHONPATH=. python3 scripts/apply_2026_09_25_pseudo_chrysostom_evidenced_by.py --dry-run
    PYTHONPATH=. python3 scripts/apply_2026_09_25_pseudo_chrysostom_evidenced_by.py --apply
"""

from __future__ import annotations

import argparse
import json

from scripts.data_2026_09_25_pseudo_chrysostom_evidenced_by import DECISIONS, TARGET
from scripts.verification_2026_09_24_lib import Store, write_decisions

SLUG = "c3_pseudo_chrysostom_evidenced_by"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    apply = args.apply and not args.dry_run

    store = Store()
    decisions, skipped = [], []
    for source in DECISIONS:
        edges = store.edges
        kept = any(e["source"] == source and e["relation"] == "cites_primary_source" and e["target"] == TARGET
                   for e in edges)
        present = any(e["source"] == source and e["relation"] == "evidenced_by" and e["target"] == TARGET
                      for e in edges)
        if not present:
            skipped.append((source, "evidenced_by edge absent (already applied)"))
            continue
        if not kept:
            skipped.append((source, "no cites_primary_source to the work: withdrawal would lose the citation"))
            continue
        n = store.remove_edges(
            lambda e, s=source: e["source"] == s and e["relation"] == "evidenced_by" and e["target"] == TARGET,
            "evidenced_by admits only a passage target; the same citation is kept as cites_primary_source",
        )
        decisions.append({
            "item_id": f"{source} -evidenced_by-> {TARGET}",
            "queue": "follow-up of c3_citation_edges (KG RDF/SHACL gate)",
            "claim_checked": "evidenced_by edge with a work target",
            "verdict": "removed",
            "evidence": "edge_types.json: evidenced_by target_types = ['passage']",
            "source": "knowledge graph/ontology/edge_types.json; existing cites_primary_source edge to the same work",
            "method": "ontology type check; confirmed the equivalent cites_primary_source edge exists",
            "jev": None,
            "change": f"{n} edge withdrawn; cites_primary_source -> {TARGET} kept",
        })

    summary = store.commit(SLUG, apply=apply)
    if apply and decisions:
        write_decisions(SLUG, decisions)
    print(json.dumps({"mode": "apply" if apply else "dry_run", "withdrawn": len(decisions),
                      "skipped": skipped, "changes": summary}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
