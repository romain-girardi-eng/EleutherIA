#!/usr/bin/env python3
"""Wave 4: factual corrections exposed by the work-conflation split.

See ``data_2026_08_17_factual_corrections.py`` for the evidence behind each edit.

Usage:
    python3 scripts/apply_2026_08_17_factual_corrections.py [--dry-run]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from data_2026_08_17_factual_corrections import (  # noqa: E402
    CTS_PLACEHOLDER_PREFIX,
    DATE_FIELD_FIXES,
    PASSAGE_AUTHOR_REPOINT,
    PERIOD_FIXES,
    PERIOD_VOCAB_FIXES,
    REVERSED_INFLUENCES,
    WHOLLY_FOREIGN_WORKS,
)

ROOT = Path(__file__).resolve().parent.parent
NODES_PATH = ROOT / "data" / "kg" / "nodes.jsonl"
EDGES_PATH = ROOT / "data" / "kg" / "edges.jsonl"

STAMP = "factual_corrections_2026_08_17"

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


def edge_note(edge: dict, op: str, why: str) -> None:
    data = edge.get("metadata") or {}
    if isinstance(data, dict):
        data[STAMP] = op
        data[f"{STAMP}_note"] = why
        edge["metadata"] = data


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    nodes = read_jsonl(NODES_PATH)
    edges = read_jsonl(EDGES_PATH)
    before = (len(nodes), len(edges))
    N = {nid(n): n for n in nodes}
    by_edge = {e.get("edge_id"): e for e in edges}
    triples = {(e["source"], e["relation"], e["target"]) for e in edges}

    # ---- 1. reversed influences -> influenced_by --------------------------
    drop_edge_ids: set[str] = set()
    for edge_id, why in REVERSED_INFLUENCES:
        edge = by_edge.get(edge_id)
        if edge is None:
            warn("fix_reversed_influences", f"{edge_id} not found")
            continue
        if edge["relation"] == "influenced_by":
            continue  # idempotent
        if edge["relation"] != "influences":
            warn(
                "fix_reversed_influences",
                f"{edge_id}: relation is {edge['relation']!r}",
            )
            continue
        target_triple = (edge["source"], "influenced_by", edge["target"])
        if target_triple in triples:
            drop_edge_ids.add(edge_id)
            note(
                "fix_reversed_influences",
                f"{edge_id}: dropped, influenced_by already asserted",
            )
            continue
        triples.discard((edge["source"], "influences", edge["target"]))
        triples.add(target_triple)
        edge["relation"] = "influenced_by"
        edge_note(edge, "fix_reversed_influences", why)
        note(
            "fix_reversed_influences", f"{edge_id}: influences -> influenced_by ({why})"
        )

    # ---- 2. wholly-foreign works ------------------------------------------
    for host, (real_home, why) in WHOLLY_FOREIGN_WORKS.items():
        if host not in N:
            warn("drop_foreign_parenting", f"{host} not found")
            continue
        kids = [
            e
            for e in edges
            if e["relation"] == "part_of"
            and e["target"] == host
            and N.get(e["source"], {}).get("type") == "passage"
        ]
        if not kids:
            continue  # idempotent
        safe = []
        for e in kids:
            if (e["source"], "part_of", real_home) in triples:
                safe.append(e)
            else:
                warn(
                    "drop_foreign_parenting",
                    f"{e['source']} not parented to {real_home}; kept",
                )
        for e in safe:
            drop_edge_ids.add(e["edge_id"])
        note(
            "drop_foreign_parenting",
            f"{host}: dropped {len(safe)} part_of edges ({why})",
        )
        data = meta(N[host])
        data["needs_text_ingestion"] = True
        data[f"{STAMP}_note"] = (
            "Its 51 children were Clement's Protrepticus, filed here by a title collision "
            f"('Exhortation'); they remain under {real_home}. No text of this work is ingested."
        )
        set_meta(N[host], data)

    # ---- 3. passages attributed to the wrong ancient author ---------------
    for spec in PASSAGE_AUTHOR_REPOINT:
        work = spec["work"]
        if work not in N:
            warn("repoint_passage_author", f"{work} not found")
            continue
        kids = {
            e["source"]
            for e in edges
            if e["relation"] == "part_of"
            and e["target"] == work
            and N.get(e["source"], {}).get("type") == "passage"
        }
        moved = 0
        for e in edges:
            if e["relation"] != "authored_by" or e["source"] not in kids:
                continue
            if e["target"] == spec["right"]:
                continue
            if e["target"] != spec["wrong"]:
                warn(
                    "repoint_passage_author", f"{e['source']}: author is {e['target']}"
                )
                continue
            new_triple = (e["source"], "authored_by", spec["right"])
            if new_triple in triples:
                drop_edge_ids.add(e["edge_id"])
                continue
            triples.discard((e["source"], "authored_by", e["target"]))
            triples.add(new_triple)
            e["target"] = e["target_id"] = spec["right"]
            edge_note(e, "repoint_passage_author", spec["why"])
            moved += 1
        for pid in kids:
            data = meta(N[pid])
            if data.get("author") == spec["author"]:
                continue
            if spec.get("keep_ms_attribution") and data.get("author"):
                data["manuscript_attribution"] = spec["keep_ms_attribution"]
            data[f"{STAMP}_author_fix"] = (
                f"{data.get('author')!r} -> {spec['author']!r}; {spec['why']}"
            )
            data["author"] = spec["author"]
            set_meta(N[pid], data)
        if moved:
            note(
                "repoint_passage_author", f"{work}: {moved} passages -> {spec['right']}"
            )

    # ---- 4. CTS URNs with a '?' placeholder --------------------------------
    for node in nodes:
        data = meta(node)
        urn = data.get("cts_urn")
        if not isinstance(urn, str) or CTS_PLACEHOLDER_PREFIX not in urn:
            continue
        fixed = urn.replace(CTS_PLACEHOLDER_PREFIX, ":", 1)
        data["cts_urn"] = fixed
        data[f"{STAMP}_urn_fix"] = (
            f"{urn} -> {fixed}: '?' is a reserved URI character and made the URN unresolvable; "
            "this Plato work is cited by flat Stephanus pagination and has no book division"
        )
        set_meta(node, data)
        counts["fix_cts_placeholder"] = counts.get("fix_cts_placeholder", 0) + 1

    # ---- 5. periods --------------------------------------------------------
    for node_id, (wrong, right, why) in PERIOD_FIXES.items():
        node = N.get(node_id)
        if node is None:
            warn("fix_period", f"{node_id} not found")
            continue
        if node.get("period") == right:
            continue
        if node.get("period") != wrong:
            warn("fix_period", f"{node_id}: period is {node.get('period')!r}")
            continue
        node["period"] = right
        data = meta(node)
        data[f"{STAMP}_period_fix"] = f"{wrong} -> {right}; {why}"
        set_meta(node, data)
        note("fix_period", f"{node_id}: {wrong} -> {right}")

    for node in nodes:
        right = PERIOD_VOCAB_FIXES.get(node.get("period"))
        if not right:
            continue
        data = meta(node)
        data[f"{STAMP}_period_fix"] = (
            f"{node['period']} -> {right}; period vocabulary normalisation"
        )
        set_meta(node, data)
        node["period"] = right
        counts["normalise_period_vocab"] = counts.get("normalise_period_vocab", 0) + 1

    # ---- 6. date field misuse ---------------------------------------------
    for spec in DATE_FIELD_FIXES:
        node = N.get(spec["node"])
        if node is None:
            warn("fix_date_field", f"{spec['node']} not found")
            continue
        data = meta(node)
        if data.get(spec["to_field"]) == spec["value"]:
            continue
        if data.get(spec["from_field"]) != spec["value"]:
            warn(
                "fix_date_field",
                f"{spec['node']}: {spec['from_field']} is {data.get(spec['from_field'])!r}",
            )
            continue
        data[spec["to_field"]] = spec["value"]
        data[spec["from_field"]] = None
        data[f"{STAMP}_date_fix"] = (
            f"{spec['from_field']} -> {spec['to_field']}; {spec['why']}"
        )
        set_meta(node, data)
        note(
            "fix_date_field",
            f"{spec['node']}: {spec['from_field']} -> {spec['to_field']}",
        )

    edges = [e for e in edges if e.get("edge_id") not in drop_edge_ids]

    # ---- invariants --------------------------------------------------------
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
    tl = [(e["source"], e["relation"], e["target"]) for e in edges]
    assert len(tl) == len(set(tl)), "duplicate triples"
    assert not [e for e in edges if e["source"] == e["target"]], "self-loops"
    assert not [
        n
        for n in nodes
        if isinstance(meta(n).get("cts_urn"), str) and "?" in meta(n)["cts_urn"]
    ], "CTS placeholders remain"

    print(f"nodes {before[0]} -> {len(nodes)}   edges {before[1]} -> {len(edges)}")
    for k in sorted(counts):
        print(f"  {k}: {counts[k]}")
    print("invariants: OK")

    if args.dry_run:
        print("\n--dry-run: nothing written")
        return 0

    write_jsonl(NODES_PATH, nodes)
    write_jsonl(EDGES_PATH, edges)
    report = ROOT / "data" / "audit" / "2026-08-17_factual_corrections_applied.md"
    report.write_text(
        "# Factual corrections (wave 4) — applied 2026-08-17\n\n"
        f"nodes {before[0]} -> {len(nodes)}, edges {before[1]} -> {len(edges)}\n\n"
        + "\n".join(f"- {line}" for line in log)
        + "\n",
        encoding="utf-8",
    )
    print(f"\nwrote {NODES_PATH}\nwrote {EDGES_PATH}\nwrote {report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
