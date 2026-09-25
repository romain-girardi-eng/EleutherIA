#!/usr/bin/env python3
"""Apply the review of the C3 likely-wrong citation edges. Dry-run first.

    PYTHONPATH=. python3 scripts/apply_2026_09_24_c3_citation_edges.py --dry-run
    PYTHONPATH=. python3 scripts/apply_2026_09_24_c3_citation_edges.py --apply

"remove" withdraws the edge, its ontology-inverse twin on the same pair and the
corpus citation that mirrors it (same citing node, same relation, the target's
snapshot row). "retarget:<node>" moves the edge to the named node, keeping the
old target in metadata, and withdraws the mirrored corpus citation (a work node
has no corpus row). Other verdicts only produce a decision record.
"""

from __future__ import annotations

import argparse
import collections
import json

from scripts.apply_2026_09_24_c4_duplicate_merges import INVERSE
from scripts.data_2026_09_24_c3_citation_edges import DECISIONS, EXTRA_REMOVALS
from scripts.verification_2026_09_24_lib import Store, write_decisions

SLUG = "c3_citation_edges"
STAMP = "c3_citation_review_2026_09_24"
NOW = "2026-09-24 00:00:00+00:00"
QUEUE = "c3_edges_links/queue_A_likely_wrong.csv"
VERDICT = {"remove": "removed", "retarget": "corrected", "false_positive": "false_positive",
           "needs_romain": "needs_romain", "corrected_elsewhere": "corrected"}


def edge_meta(edge: dict) -> dict:
    raw = edge.get("metadata") or {}
    return json.loads(raw) if isinstance(raw, str) else dict(raw)


def put_edge_meta(edge: dict, data: dict) -> None:
    edge["metadata"] = json.dumps(data, ensure_ascii=False) if isinstance(edge.get("metadata"), str) else data


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    apply = args.apply and not args.dry_run

    store = Store()
    nodes = store.nodes
    snapshot_rows = collections.defaultdict(set)
    for c in store.rows["citations"]:
        if c["citation_type"] == "snapshot_passage_node":
            snapshot_rows[c["kg_node_id"]].add(c["passage_id"])

    def mirrored(source: str, relation: str, target: str):
        rows = snapshot_rows.get(target, set())
        return lambda c: c["kg_node_id"] == source and c["citation_type"] == relation and c["passage_id"] in rows

    decisions, skipped = [], []
    counts: collections.Counter = collections.Counter()
    for row, edge_id, rel, src, tgt, p, verdict, note in DECISIONS:
        kind, _, new_target = verdict.partition(":")
        record = {
            "item_id": edge_id,
            "queue": f"{QUEUE} (row {row} of the citation-edge extract)",
            "claim_checked": f"{src} -{rel}-> {tgt}",
            "verdict": VERDICT[kind],
            "evidence": note,
            "source": "text of the target node and metadata of the edge and of both endpoints",
            "method": "read the target text and the edge provenance; for removals, the text or the edge's own metadata contradicts the claim",
            "jev": {"question": "p_specific", "probability": p},
        }
        edge = next((e for e in store.edges if e["edge_id"] == edge_id), None)
        if kind in ("remove", "retarget"):
            if edge is None or (edge["source"], edge["relation"], edge["target"]) != (src, rel, tgt):
                skipped.append((row, edge_id, "edge absent or changed"))
                continue
        if kind == "remove":
            reason = f"C3 citation review 2026-09-24, row {row}: {note}"
            n_e = store.remove_edges(lambda e: e["edge_id"] == edge_id or (
                e["source"] == tgt and e["target"] == src and e["relation"] == INVERSE.get(rel)), reason)
            n_c = store.remove_citations(mirrored(src, rel, tgt), reason)
            record["change"] = f"edge withdrawn ({n_e} with its inverse twin), {n_c} mirrored corpus citation(s) withdrawn"
        elif kind == "retarget":
            if new_target not in nodes:
                skipped.append((row, edge_id, f"new target {new_target} absent"))
                continue
            if any(e["source"] == src and e["relation"] == rel and e["target"] == new_target for e in store.edges):
                skipped.append((row, edge_id, "retargeted edge would duplicate an existing one"))
                continue
            n_c = store.remove_citations(mirrored(src, rel, tgt),
                                         f"C3 citation review 2026-09-24, row {row}: edge retargeted to {new_target}")
            m = edge_meta(edge)
            m[STAMP] = {"previous_target": tgt, "reason": note}
            put_edge_meta(edge, m)
            edge["target"] = edge["target_id"] = new_target
            record["change"] = f"target {tgt} -> {new_target}; {n_c} mirrored corpus citation(s) withdrawn"
        elif kind == "corrected_elsewhere":
            record["change"] = "target text restored by the plotinus_locus_drift batch; edge unchanged"
        else:
            record["change"] = "none"
        counts[kind] += 1
        decisions.append(record)

    for src, rel, tgt, row in EXTRA_REMOVALS:
        reason = f"C3 citation review 2026-09-24, same pair and evidence as row {row}"
        n_e = store.remove_edges(lambda e: (e["source"], e["relation"], e["target"]) == (src, rel, tgt), reason)
        n_c = store.remove_citations(mirrored(src, rel, tgt), reason)
        if n_e:
            counts["remove_extra"] += 1
            decisions.append({"item_id": f"{src} -{rel}-> {tgt}", "queue": f"{QUEUE} (companion of row {row})",
                              "claim_checked": f"{src} -{rel}-> {tgt}", "verdict": "removed",
                              "evidence": f"same pair and evidence as row {row}", "source": "text of the passage",
                              "method": "read the passage", "jev": None,
                              "change": f"{n_e} edge(s), {n_c} mirrored corpus citation(s) withdrawn"})

    summary = store.commit(SLUG, apply=apply)
    # A re-run finds the edges gone: keep the first run's decision record.
    if apply and not skipped:
        write_decisions(SLUG, decisions)
    print(json.dumps({"mode": "apply" if apply else "dry_run", "counts": counts, "skipped": skipped,
                      "changes": summary}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
