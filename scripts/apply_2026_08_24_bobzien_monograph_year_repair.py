#!/usr/bin/env python3
"""Distinguish Bobzien monograph first publication (1998) from 2001 paperback."""

from __future__ import annotations

import argparse
import copy
import json
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
NODES_PATH = ROOT / "data/kg/nodes.jsonl"
NODE_ID = "scholarly_work_bobzien_1998_determinism_and_freedom_in_stoic_philoso"
STAMP = "bobzien_monograph_year_repair_2026_08_24"


def read_nodes(path: Path = NODES_PATH) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def node_id(node: dict[str, Any]) -> str:
    return str(node.get("id") or node.get("node_id") or "")


def transform(nodes: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], bool]:
    nodes = copy.deepcopy(nodes)
    found = [node for node in nodes if node_id(node) == NODE_ID]
    if len(found) != 1:
        raise RuntimeError(f"expected one Bobzien monograph node, found {len(found)}")
    node = found[0]
    data = node.get("metadata")
    if not isinstance(data, dict):
        raise RuntimeError("Bobzien monograph metadata is not an object")
    if data.get("year") == 1998 and data.get(STAMP):
        return nodes, False
    if data.get("year") != 2001 or data.get("year_first_published") != 1998:
        raise RuntimeError("unexpected Bobzien year precondition")
    data.update(
        {
            "year": 1998,
            "year_first_published": 1998,
            "edition_used_year": 2001,
            "publication_history": "Clarendon hardback 1998; Oxford paperback 2001",
            STAMP: True,
        }
    )
    node["label"] = "Bobzien 1998/2001 — Determinism and Freedom in Stoic Philosophy"
    node["updated_at"] = "2026-08-24 00:00:00+00:00"
    return nodes, True


def write_preserving(path: Path, nodes: list[dict[str, Any]]) -> None:
    desired = {node_id(node): node for node in nodes}
    output: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        old = json.loads(line)
        new = desired[node_id(old)]
        output.append(line if old == new else json.dumps(new, ensure_ascii=False, sort_keys=True))
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        tmp = Path(handle.name)
        handle.write("\n".join(output) + "\n")
    tmp.replace(path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    nodes, changed = transform(read_nodes())
    print("Bobzien monograph year repair", "WRITE" if args.write else "DRY-RUN")
    print("changed:", changed)
    if args.write and changed:
        write_preserving(NODES_PATH, nodes)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
