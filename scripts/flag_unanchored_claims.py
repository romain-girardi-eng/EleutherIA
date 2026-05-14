#!/usr/bin/env python3
"""Flag claim-bearing KG nodes that lack any evidence anchor.

The SHACL ``NeedsEvidence`` quality shape exempts nodes whose
``metadata.needs_evidence`` is ``true``. This script:

1. Builds the RDF graph from ``data/kg/{nodes,edges}.jsonl``
2. Runs SHACL validation against the loaded shapes
3. Collects every node IRI flagged by a ``*_NeedsEvidence`` shape
4. Rewrites ``data/kg/nodes.jsonl`` in place, setting
   ``metadata.needs_evidence = true`` on each violating node
5. Re-validates and prints the resulting count

This converts "no evidence" from a passive gap into an *explicit*
acknowledgement — the audit-batch convention already in use in the project.

The transformation is conservative: only the ``needs_evidence`` key is added.
No other metadata, label, description, or relations are touched.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NODES_PATH = ROOT / "data" / "kg" / "nodes.jsonl"
EDGES_PATH = ROOT / "data" / "kg" / "edges.jsonl"


def _flagged_ids() -> set[str]:
    from eleutheria_kg.semantic import build_graph, validate_kg
    from eleutheria_kg.semantic.shapes import load_shapes

    g = build_graph(NODES_PATH, EDGES_PATH)
    report = validate_kg(g, load_shapes())
    out: set[str] = set()
    for v in report.violations:
        shape = v.source_shape or ""
        if "NeedsEvidence" not in shape:
            continue
        # focus_node is the full IRI; strip the resource prefix.
        node_id = v.focus_node.replace("https://free-will.app/kg/", "")
        out.add(node_id)
    return out


def _rewrite_jsonl(target_ids: set[str]) -> tuple[int, int]:
    """Mutate ``nodes.jsonl`` in place: set ``metadata.needs_evidence=true``.

    Returns ``(touched, total)``.
    """
    rows: list[dict] = []
    with NODES_PATH.open(encoding="utf-8") as fh:
        for raw in fh:
            raw = raw.strip()
            if not raw:
                continue
            rows.append(json.loads(raw))

    touched = 0
    for n in rows:
        if n.get("id") not in target_ids:
            continue
        metadata = n.get("metadata")
        if not isinstance(metadata, dict):
            metadata = {}
        if metadata.get("needs_evidence") is True:
            continue  # already flagged
        metadata["needs_evidence"] = True
        n["metadata"] = metadata
        touched += 1

    tmp = NODES_PATH.with_suffix(".jsonl.tmp")
    with tmp.open("w", encoding="utf-8") as fh:
        for n in rows:
            fh.write(json.dumps(n, ensure_ascii=False))
            fh.write("\n")
    tmp.replace(NODES_PATH)
    return touched, len(rows)


def main() -> int:
    ids = _flagged_ids()
    print(f"Flagged by SHACL NeedsEvidence: {len(ids)} nodes")
    if not ids:
        return 0
    touched, total = _rewrite_jsonl(ids)
    print(f"Touched {touched}/{total} rows in {NODES_PATH}")
    # Re-validate
    from eleutheria_kg.semantic import build_graph, validate_kg
    from eleutheria_kg.semantic.shapes import load_shapes

    g = build_graph(NODES_PATH, EDGES_PATH)
    report = validate_kg(g, load_shapes())
    remaining = sum(
        1 for v in report.violations if "NeedsEvidence" in (v.source_shape or "")
    )
    print(f"NeedsEvidence after rewrite: {remaining}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
