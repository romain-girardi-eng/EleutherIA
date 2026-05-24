"""Phase 0: derive the corpus manifest (in-scope works) from the git KG.

A work is in scope if it is a `type==work` node, or it is referenced via
`work_canonical_id` on a `type==passage` node. The manifest is the curated
scope-of-truth AND the deterministic rebuild recipe; this script proposes rows,
the user then curates `data/corpus/manifest.jsonl` by hand.

Dry-run by default; --commit writes data/corpus/manifest.jsonl (refuses to clobber
an existing curated manifest unless --force).
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from scripts.corpus_lib import read_jsonl, write_jsonl

ROOT = Path(__file__).resolve().parents[1]
NODES_PATH = ROOT / "data" / "kg" / "nodes.jsonl"
EDGES_PATH = ROOT / "data" / "kg" / "edges.jsonl"
MANIFEST_PATH = ROOT / "data" / "corpus" / "manifest.jsonl"


def _meta(node: dict) -> dict[str, Any]:
    m = node.get("metadata")
    if isinstance(m, str) and m:
        try:
            return json.loads(m)
        except json.JSONDecodeError:
            return {}
    return m or {}


def derive_manifest(nodes: list[dict], edges: list[dict]) -> list[dict]:
    nodes_by_id = {n["id"]: n for n in nodes}
    author_of: dict[str, str] = {}
    for e in edges:
        if e.get("relation") == "authored_by":
            src, tgt = e.get("source"), e.get("target")
            person = nodes_by_id.get(tgt)
            if src and person:
                author_of[src] = person.get("label", "")

    in_scope: set[str] = set()
    for n in nodes:
        if n.get("type") == "work":
            in_scope.add(n["id"])
        elif n.get("type") == "passage":
            wid = _meta(n).get("work_canonical_id")
            if wid:
                in_scope.add(wid)

    rows: list[dict] = []
    for wid in in_scope:
        work = nodes_by_id.get(wid)
        meta = _meta(work) if work else {}
        cts = meta.get("cts_urn", "") if work else ""
        source = f"scaife:{cts}" if cts else ""
        status = "pending" if (work is not None and cts) else "needs_source"
        rows.append({
            "canonical_id": wid,
            "label": (work.get("label") if work else "") or "",
            "author": author_of.get(wid, ""),
            "period": (work.get("period") if work else "") or "",
            "cts_urn": cts,
            "source": source,
            "status": status,
            "expected_passages": None,
        })
    rows.sort(key=lambda r: r["canonical_id"])
    return rows


def main(commit: bool, force: bool) -> int:
    nodes = read_jsonl(NODES_PATH)
    edges = read_jsonl(EDGES_PATH)
    rows = derive_manifest(nodes, edges)
    n_pending = sum(1 for r in rows if r["status"] == "pending")
    n_needs = sum(1 for r in rows if r["status"] == "needs_source")
    print(f"derived {len(rows)} works ({n_pending} pending, {n_needs} needs_source)")
    if not commit:
        print("[DRY-RUN] --commit to write data/corpus/manifest.jsonl")
        return 0
    if MANIFEST_PATH.exists() and not force:
        print(f"REFUSING: {MANIFEST_PATH} exists (curated). Use --force to overwrite.")
        return 1
    write_jsonl(MANIFEST_PATH, rows)
    print(f"wrote {MANIFEST_PATH}")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--commit", action="store_true")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    raise SystemExit(main(a.commit, a.force))
