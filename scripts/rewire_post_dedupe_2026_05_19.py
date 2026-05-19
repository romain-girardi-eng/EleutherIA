#!/usr/bin/env python3
"""Rewire edges sourced from deprecated shell nodes onto their canonical
replacements.

Background
----------
Phase B (2026-05-18) marked 38 duplicate nodes as ``metadata.deprecated=true``
and pointed each at its canonical via ``metadata.superseded_by``. Post-Phase B,
two wiring passes (E1 modern args, ``wire_orphan_arguments_2026_05_18``) did
not consult the deprecated flag and emitted 106 edges originating from those
shells. The 2026-05-18/19 independent audit broke the 106 down as:

  - 37 are *duplicates*: the canonical node already has the same
    (target, relation) edge → these shell edges are redundant and must be
    **deleted**.
  - 69 are *unique to the shell*: the canonical does not carry the edge
    → these must be **rebased** onto the canonical (change ``source``).

Idempotency
-----------
A second run is a no-op: once all source-side references to a deprecated shell
are either removed or rebased, no edge matches the rewrite predicate.

A snapshot of ``edges.jsonl`` is written to
``data/kg/snapshots/2026-05-19-pre-rewire-post-dedupe/`` before mutation.

Each rewired edge gains in its metadata::

    rewired_from_shell: <shell_id>
    rewired_at: 2026-05-19

Ontology check
--------------
After rebasement we verify that (canonical_type, target_type) is permitted by
``knowledge graph/ontology/edge_types.json`` for the edge relation. Violations
are reported (not auto-deleted) so a human can decide.

Usage::

    python3 scripts/rewire_post_dedupe_2026_05_19.py            # dry-run
    python3 scripts/rewire_post_dedupe_2026_05_19.py --commit   # apply
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
NODES_PATH = ROOT / "data" / "kg" / "nodes.jsonl"
EDGES_PATH = ROOT / "data" / "kg" / "edges.jsonl"
ONTOLOGY_PATH = ROOT / "knowledge graph" / "ontology" / "edge_types.json"
SNAPSHOT_DIR = ROOT / "data" / "kg" / "snapshots" / "2026-05-19-pre-rewire-post-dedupe"

REWIRE_DATE = "2026-05-19"
NOW = datetime.now(UTC).isoformat(sep=" ")


def parse_metadata(raw: Any) -> dict[str, Any]:
    if raw is None or raw == "":
        return {}
    if isinstance(raw, dict):
        return raw
    try:
        return json.loads(raw)
    except (TypeError, json.JSONDecodeError):
        return {}


def serialize_metadata(md: dict[str, Any], original: Any) -> Any:
    if isinstance(original, str) or original is None:
        return json.dumps(md, ensure_ascii=False)
    return md


def main(commit: bool = False) -> int:
    # ------------------------------------------------------------------ load
    nodes_lines = NODES_PATH.read_text(encoding="utf-8").splitlines()
    nodes_by_id: dict[str, dict] = {}
    node_type_by_id: dict[str, str] = {}
    deprecated_shells: dict[str, str] = {}  # shell_id -> canonical_id
    for ln in nodes_lines:
        if not ln.strip():
            continue
        try:
            n = json.loads(ln)
        except json.JSONDecodeError:
            continue
        nid = n.get("id")
        if not nid:
            continue
        nodes_by_id[nid] = n
        node_type_by_id[nid] = n.get("type", "")
        md = parse_metadata(n.get("metadata"))
        if md.get("deprecated") is True:
            sup = md.get("superseded_by")
            if sup:
                deprecated_shells[nid] = sup

    print(f"loaded {len(nodes_by_id)} nodes; {len(deprecated_shells)} deprecated shells with canonical")

    # ------------------------------------------------------------- ontology
    edge_ontology: dict[str, dict] = {}
    try:
        with ONTOLOGY_PATH.open() as fh:
            edge_ontology = json.load(fh).get("edge_types", {})
    except Exception as exc:
        print(f"WARN: cannot read ontology ({exc}); skipping post-rewire ontology check")

    # ------------------------------------------------------------------ load edges
    edges: list[dict] = []
    with EDGES_PATH.open(encoding="utf-8") as fh:
        for raw in fh:
            raw = raw.strip()
            if not raw:
                continue
            edges.append(json.loads(raw))
    print(f"loaded {len(edges)} edges")

    # ---------------------------------------- index canonical edges (target, relation)
    canonical_edge_keys: dict[str, set[tuple[str, str]]] = defaultdict(set)
    for e in edges:
        s = e.get("source")
        t = e.get("target")
        r = e.get("relation")
        if s and t and r:
            # source of canonical edges only (we'll dedupe against them)
            canonical_edge_keys[s].add((t, r))

    # ------------------------------------------------------------------ rewire
    new_edges: list[dict] = []
    deleted_count = 0
    rebased_count = 0
    deleted_examples: list[tuple[str, str, str]] = []
    rebased_examples: list[tuple[str, str, str, str]] = []
    ontology_violations: list[tuple[str, str, str, str, str]] = []
    relation_stats_del = Counter()
    relation_stats_rebase = Counter()

    seen_after: set[tuple[str, str, str]] = set()

    for e in edges:
        s = e.get("source")
        t = e.get("target")
        r = e.get("relation")
        if not (s and t and r):
            new_edges.append(e)
            continue

        if s in deprecated_shells:
            canonical = deprecated_shells[s]
            if (t, r) in canonical_edge_keys.get(canonical, set()):
                # Duplicate — drop
                deleted_count += 1
                relation_stats_del[r] += 1
                if len(deleted_examples) < 5:
                    deleted_examples.append((s, t, r))
                continue
            # Unique — rebase
            # Avoid emitting twice if multiple shell edges collapse onto same canonical key
            key = (canonical, t, r)
            if key in seen_after:
                deleted_count += 1
                relation_stats_del[r] += 1
                if len(deleted_examples) < 5:
                    deleted_examples.append((s, t, r))
                continue
            new_e = dict(e)
            new_e["source"] = canonical
            new_e["source_id"] = canonical
            md = parse_metadata(new_e.get("metadata"))
            md["rewired_from_shell"] = s
            md["rewired_at"] = REWIRE_DATE
            new_e["metadata"] = serialize_metadata(md, e.get("metadata"))
            new_e["updated_at"] = NOW
            # Ontology check
            ct = node_type_by_id.get(canonical, "")
            tt = node_type_by_id.get(t, "")
            spec = edge_ontology.get(r)
            if spec:
                src_ok = ct in spec.get("source_types", []) or not spec.get("source_types")
                tgt_ok = tt in spec.get("target_types", []) or not spec.get("target_types")
                if not (src_ok and tgt_ok):
                    ontology_violations.append((canonical, ct, r, t, tt))
            new_edges.append(new_e)
            canonical_edge_keys[canonical].add((t, r))
            seen_after.add(key)
            rebased_count += 1
            relation_stats_rebase[r] += 1
            if len(rebased_examples) < 5:
                rebased_examples.append((s, canonical, t, r))
            continue

        new_edges.append(e)

    # -------------------------------------------------------------- report
    print("\n=== Rewire stats ===")
    print(f"  edges deleted (duplicates of canonical): {deleted_count}")
    print(f"  edges rebased (shell -> canonical):      {rebased_count}")
    print(f"  edges total before: {len(edges)}")
    print(f"  edges total after:  {len(new_edges)}")
    print(f"  delta: {len(new_edges) - len(edges)}")

    print("\nTop relations deleted:")
    for r, c in relation_stats_del.most_common(10):
        print(f"  {c:>4}  {r}")
    print("\nTop relations rebased:")
    for r, c in relation_stats_rebase.most_common(10):
        print(f"  {c:>4}  {r}")

    if deleted_examples:
        print("\nDeleted examples:")
        for s, t, r in deleted_examples:
            print(f"  {s[:55]:<55} -[{r}]-> {t[:55]}")
    if rebased_examples:
        print("\nRebased examples (shell -> canonical):")
        for s, c, t, r in rebased_examples:
            print(f"  {s[:55]:<55} => {c[:55]:<55} -[{r}]-> {t[:55]}")

    if ontology_violations:
        print(f"\nWARNING: ontology violations after rebase: {len(ontology_violations)}")
        for ct_src, ct, r, tt_tgt, tt in ontology_violations[:20]:
            print(f"  {ct_src[:40]} ({ct}) -[{r}]-> {tt_tgt[:40]} ({tt})")
    else:
        print("\nOntology check: all rebased edges fit canonical source_type / target_type")

    if not commit:
        print("\n[DRY-RUN] use --commit to apply")
        return 0

    if deleted_count == 0 and rebased_count == 0:
        print("\nOK: nothing to apply (already idempotent).")
        return 0

    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(EDGES_PATH, SNAPSHOT_DIR / EDGES_PATH.name)
    print(f"\nSnapshot written: {SNAPSHOT_DIR / EDGES_PATH.name}")

    tmp = EDGES_PATH.with_suffix(".jsonl.tmp")
    with tmp.open("w", encoding="utf-8") as fh:
        for e in new_edges:
            fh.write(json.dumps(e, ensure_ascii=False) + "\n")
    tmp.replace(EDGES_PATH)
    print(f"Written: {EDGES_PATH}")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--commit", action="store_true")
    args = ap.parse_args()
    sys.exit(main(commit=args.commit))
