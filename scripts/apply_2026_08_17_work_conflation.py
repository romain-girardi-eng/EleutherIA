#!/usr/bin/env python3
"""Split the twelve conflated ``work`` nodes so every passage sits under its own work.

See ``data_2026_08_17_work_conflation.py`` for the evidence behind each operation.

The correct parent is never guessed. A passage's work identity is its own
``metadata.work_canonical_id``; a work node is "pure" when all of its passage
children share one canonical id. Phase A deletes a ``part_of`` edge only when the
passage demonstrably keeps a pure parent carrying its own canonical id.

Usage:
    python3 scripts/apply_2026_08_17_work_conflation.py [--dry-run]
"""

from __future__ import annotations

import argparse
import collections
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from data_2026_08_17_work_conflation import (  # noqa: E402
    NEW_PERSONS,
    NEW_WORKS,
    PASSAGE_AUTHOR_FIXES,
    PASSAGE_CANONICAL_FIXES,
    REPARENT_TO_EXISTING,
)

ROOT = Path(__file__).resolve().parent.parent
NODES_PATH = ROOT / "data" / "kg" / "nodes.jsonl"
EDGES_PATH = ROOT / "data" / "kg" / "edges.jsonl"

STAMP = "work_conflation_2026_08_17"
NOW = "2026-08-17 00:00:00+00:00"

log: list[str] = []
counts: dict[str, int] = {}


def note(op: str, msg: str) -> None:
    log.append(f"[{op}] {msg}")
    counts[op] = counts.get(op, 0) + 1


def warn(op: str, msg: str) -> None:
    log.append(f"[{op}] SKIPPED: {msg}")
    counts[op + "__skipped"] = counts.get(op + "__skipped", 0) + 1


def read_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def write_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def nid(node: dict) -> str:
    return node.get("node_id") or node.get("id") or ""


def meta(node: dict) -> dict:
    value = node.get("metadata")
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            return {}
    return value if isinstance(value, dict) else {}


def set_meta(node: dict, data: dict) -> None:
    if isinstance(node.get("metadata"), str):
        node["metadata"] = json.dumps(data, ensure_ascii=False)
    else:
        node["metadata"] = data


def canon(node: dict) -> str | None:
    return meta(node).get("work_canonical_id")


def make_edge(source: str, relation: str, target: str, why: str) -> dict:
    return {
        "created_at": NOW,
        "edge_id": f"conflation-{source}-{relation}-{target}",
        "metadata": {STAMP: True, f"{STAMP}_note": why},
        "relation": relation,
        "source": source,
        "source_id": source,
        "target": target,
        "target_id": target,
        "weight": 1.0,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    nodes = read_jsonl(NODES_PATH)
    edges = read_jsonl(EDGES_PATH)
    before = (len(nodes), len(edges))
    N = {nid(n): n for n in nodes}

    def is_passage(x: str) -> bool:
        return N.get(x, {}).get("type") == "passage"

    def is_work(x: str) -> bool:
        return N.get(x, {}).get("type") == "work"

    # ---- purity, computed from passage children only -----------------------
    kids: dict[str, list[str]] = collections.defaultdict(list)
    parents: dict[str, list[str]] = collections.defaultdict(list)
    for e in edges:
        if (
            e["relation"] == "part_of"
            and is_work(e["target"])
            and is_passage(e["source"])
        ):
            kids[e["target"]].append(e["source"])
            parents[e["source"]].append(e["target"])
    purity = {w: {canon(N[p]) for p in ps if canon(N[p])} for w, ps in kids.items()}
    conflated = {w for w, cs in purity.items() if len(cs) > 1}
    note("survey", f"{len(conflated)} conflated work nodes: {sorted(conflated)}")

    # ---- Phase A: drop redundant part_of to a conflated work ---------------
    drop: set[tuple[str, str]] = set()
    for p, ws in parents.items():
        if len(ws) < 2:
            continue
        c = canon(N[p])
        pure = [
            w
            for w in ws
            if len(purity.get(w, set())) == 1 and (not c or c in purity[w])
        ]
        if not pure:
            continue
        for w in ws:
            if w in conflated:
                drop.add((p, w))
    counts["phase_a_edges_dropped"] = len(drop)

    # ---- Phase B1: re-parent to an existing work ---------------------------
    reparent: dict[tuple[str, str], str] = {}
    for (host, foreign_canon), target in REPARENT_TO_EXISTING.items():
        if target not in N:
            warn("reparent_existing", f"target work {target} missing")
            continue
        moved = [p for p in kids.get(host, []) if canon(N[p]) == foreign_canon]
        if not moved:
            continue
        for p in moved:
            reparent[(p, host)] = target
        note("reparent_existing", f"{len(moved)} passages {foreign_canon} -> {target}")

    # ---- Phase B2: create missing works, then re-parent --------------------
    new_nodes: list[dict] = []
    for spec in NEW_PERSONS:
        if spec["node_id"] in N:
            continue
        new_nodes.append(
            {
                "alternative_names": "[]",
                "created_at": NOW,
                "description": spec["description"],
                "id": spec["node_id"],
                "label": spec["label"],
                "metadata": {**spec.get("metadata", {}), STAMP: True},
                "node_id": spec["node_id"],
                "period": spec["period"],
                "role": None,
                "school": None,
                "type": "person",
                "updated_at": NOW,
            }
        )
        note("create_person", spec["node_id"])

    new_edges: list[dict] = []
    for spec in NEW_WORKS:
        host, canonical, wid = spec["host"], spec["canonical"], spec["node_id"]
        moved = [p for p in kids.get(host, []) if canon(N[p]) == canonical]
        if not moved:
            warn(
                "create_work",
                f"{wid}: no passages with canonical {canonical} under {host}",
            )
            continue
        if wid not in N and not any(nid(x) == wid for x in new_nodes):
            new_nodes.append(
                {
                    "alternative_names": "[]",
                    "created_at": NOW,
                    "description": spec["description"],
                    "id": wid,
                    "label": spec["label"],
                    "metadata": {
                        "author": spec["author"],
                        "language": spec["language"],
                        "work_canonical_id": canonical,
                        STAMP: True,
                        f"{STAMP}_note": (
                            f"Created to hold the {len(moved)} passages that carry "
                            f"work_canonical_id={canonical} and were parented to {host}. "
                            "Author, title, language and canonical id are taken from those passages."
                        ),
                    },
                    "node_id": wid,
                    "period": spec["period"],
                    "role": None,
                    "school": None,
                    "type": "work",
                    "updated_at": NOW,
                }
            )
            note("create_work", f"{wid} for {len(moved)} passages")
            if spec.get("author_node"):
                new_edges.append(
                    make_edge(
                        wid,
                        "authored_by",
                        spec["author_node"],
                        f"author recorded on all {len(moved)} passages of this work",
                    )
                )
        for p in moved:
            reparent[(p, host)] = wid

    # ---- apply edge changes ------------------------------------------------
    existing_triples = {(e["source"], e["relation"], e["target"]) for e in edges}
    kept: list[dict] = []
    for e in edges:
        if e["relation"] != "part_of":
            kept.append(e)
            continue
        key = (e["source"], e["target"])
        if key in drop:
            continue
        target = reparent.get(key)
        if target:
            triple = (e["source"], "part_of", target)
            if triple in existing_triples:
                continue  # already correctly parented
            existing_triples.add(triple)
            e["target"] = e["target_id"] = target
            data = e.get("metadata") or {}
            if isinstance(data, dict):
                data[STAMP] = True
                data[f"{STAMP}_note"] = (
                    f"re-parented from {key[1]}: the passage's work_canonical_id identifies a "
                    "different work, which now has its own node"
                )
                e["metadata"] = data
            counts["phase_b_reparented"] = counts.get("phase_b_reparented", 0) + 1
        kept.append(e)
    edges = kept + new_edges
    nodes = nodes + new_nodes
    N = {nid(n): n for n in nodes}

    # ---- Phase C: passage author metadata ---------------------------------
    for pid, (wrong, right, why) in PASSAGE_AUTHOR_FIXES.items():
        node = N.get(pid)
        if node is None:
            warn("fix_passage_author", f"{pid} missing")
            continue
        data = meta(node)
        if data.get("author") == right:
            continue
        if data.get("author") != wrong:
            warn(
                "fix_passage_author",
                f"{pid}: author is {data.get('author')!r}, expected {wrong!r}",
            )
            continue
        data["author"] = right
        data[f"{STAMP}_author_fix"] = f"{wrong} -> {right}; {why}"
        set_meta(node, data)
        note("fix_passage_author", f"{pid}: {wrong} -> {right}")

    for pid, (wrong, right, why) in PASSAGE_CANONICAL_FIXES.items():
        node = N.get(pid)
        if node is None:
            warn("fix_passage_canonical", f"{pid} missing")
            continue
        data = meta(node)
        if data.get("work_canonical_id") == right:
            continue
        if data.get("work_canonical_id") != wrong:
            warn(
                "fix_passage_canonical",
                f"{pid}: canonical is {data.get('work_canonical_id')!r}",
            )
            continue
        data["work_canonical_id"] = right
        data[f"{STAMP}_canonical_fix"] = f"{wrong} -> {right}; {why}"
        set_meta(node, data)
        note("fix_passage_canonical", f"{pid}: {wrong} -> {right}")

    # ---- verification ------------------------------------------------------
    kids2: dict[str, list[str]] = collections.defaultdict(list)
    parents2: dict[str, list[str]] = collections.defaultdict(list)
    for e in edges:
        if (
            e["relation"] == "part_of"
            and N.get(e["target"], {}).get("type") == "work"
            and N.get(e["source"], {}).get("type") == "passage"
        ):
            kids2[e["target"]].append(e["source"])
            parents2[e["source"]].append(e["target"])
    purity2 = {w: {canon(N[p]) for p in ps if canon(N[p])} for w, ps in kids2.items()}
    still = {w: cs for w, cs in purity2.items() if len(cs) > 1}

    lost = [p for p in parents if p not in parents2]
    assert not lost, f"passages lost every work parent: {lost[:5]}"
    ids = [nid(n) for n in nodes]
    assert len(ids) == len(set(ids)), "duplicate node ids"
    present = set(ids)
    assert not [
        e for e in edges if e["source"] not in present or e["target"] not in present
    ], "dangling"
    assert not [
        e
        for e in edges
        if e["source"] != e["source_id"] or e["target"] != e["target_id"]
    ], "split fields"
    triples = [(e["source"], e["relation"], e["target"]) for e in edges]
    assert len(triples) == len(set(triples)), "duplicate triples"
    assert not [e for e in edges if e["source"] == e["target"]], "self-loops"

    print(f"nodes {before[0]} -> {len(nodes)}   edges {before[1]} -> {len(edges)}")
    for k in sorted(counts):
        if k != "survey":
            print(f"  {k}: {counts[k]}")
    print(f"conflated work nodes: {len(conflated)} -> {len(still)}")
    for w, cs in still.items():
        print(f"  STILL CONFLATED {w}: {sorted(cs)}")
    print("invariants: OK")

    if args.dry_run:
        print("\n--dry-run: nothing written")
        return 0

    write_jsonl(NODES_PATH, nodes)
    write_jsonl(EDGES_PATH, edges)
    report = ROOT / "data" / "audit" / "2026-08-17_work_conflation_applied.md"
    report.write_text(
        "# Work-conflation split — applied 2026-08-17\n\n"
        f"nodes {before[0]} -> {len(nodes)}, edges {before[1]} -> {len(edges)}\n"
        f"conflated work nodes {len(conflated)} -> {len(still)}\n\n"
        + "\n".join(f"- {line}" for line in log)
        + "\n",
        encoding="utf-8",
    )
    print(f"\nwrote {NODES_PATH}\nwrote {EDGES_PATH}\nwrote {report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
