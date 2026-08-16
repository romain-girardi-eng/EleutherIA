#!/usr/bin/env python3
"""Wave 2 of the 2026-08-16 deep audit: the externally-verified bibliography.

Wave 1 (``apply_2026_08_16_deep_audit_structural.py``) fixed everything provable
from the data itself. This wave applies the corrections that needed an outside
source; each is justified in ``data_2026_08_16_deep_audit_bibliographic.py``
with the reference that settles it.

The attribution renames are *derived*, not hardcoded: for each node whose id
embeds a surname, the script reads the scholar the node is actually attributed
to (its ``created_by`` / ``authored_by`` edge, already verified in wave 1) and
renames only if that scholar is one of the confirmed corrections. A node whose
edge does not point at a corrected scholar is left alone — which is why the five
genuine Gourinat arguments keep their ids while the five D'Jeranian ones change.

Usage:
    python3 scripts/apply_2026_08_16_deep_audit_bibliographic.py [--dry-run]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from data_2026_08_16_deep_audit_bibliographic import (  # noqa: E402
    BIBLIOGRAPHIC_MERGES,
    EDITOR_NOT_AUTHOR,
    GREY_LITERATURE,
    ID_YEAR_FIXES,
    LABEL_FIXES,
    META_YEAR_FIXES,
    SLUG_FIXES,
    SURNAME_FIXES,
    YEAR_BACKFILL,
)

ROOT = Path(__file__).resolve().parent.parent
NODES_PATH = ROOT / "data" / "kg" / "nodes.jsonl"
EDGES_PATH = ROOT / "data" / "kg" / "edges.jsonl"
CITATIONS_PATH = ROOT / "data" / "corpus" / "citations.jsonl"

STAMP = "deep_audit_biblio_2026_08_16"
ATTRIBUTION_EDGES = ("created_by", "authored_by")

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


def record(node: dict, op: str, detail: str) -> None:
    data = meta(node)
    data.setdefault(f"{STAMP}_ops", []).append(f"{op}: {detail}")
    set_meta(node, data)


# --------------------------------------------------------------------------- 1
def derive_surname_renames(nodes: list[dict], edges: list[dict]) -> dict[str, str]:
    """Rename ids whose embedded surname contradicts the attributed scholar.

    The attribution is taken from the node's own created_by / authored_by edge,
    so the rename can never disagree with the graph.
    """
    op = "derive_surname_renames"
    attributed: dict[str, str] = {}
    for edge in edges:
        if edge["relation"] in ATTRIBUTION_EDGES:
            attributed.setdefault(edge["source"], edge["target"])
    # Many scholarly_argument_* nodes carry no created_by of their own; their
    # attribution runs through the publication they were advanced in. Follow
    # that chain so an argument inherits the (verified) author of its paper.
    for edge in edges:
        if edge["relation"] == "advanced_in" and edge["source"] not in attributed:
            inherited = attributed.get(edge["target"])
            if inherited:
                attributed[edge["source"]] = inherited

    renames: dict[str, str] = {}
    present = {nid(n) for n in nodes}
    for node in nodes:
        node_id = nid(node)
        scholar = attributed.get(node_id)
        fix = SURNAME_FIXES.get(scholar) if scholar else None
        if not fix:
            continue
        wrong, right = fix
        if f"_{wrong}_" not in node_id:
            continue  # id already carries the right surname
        new_id = node_id.replace(f"_{wrong}_", f"_{right}_", 1)
        if new_id in present or new_id in renames.values():
            warn(op, f"{node_id}: target {new_id} already exists")
            continue
        renames[node_id] = new_id
        note(op, f"{node_id} -> {new_id} (attributed to {scholar})")
    return renames


# --------------------------------------------------------------------------- 2
def apply_renames(
    nodes: list[dict], edges: list[dict], renames: dict[str, str], op: str, reason: str
) -> None:
    if not renames:
        return
    for node in nodes:
        node_id = nid(node)
        new_id = renames.get(node_id)
        if not new_id:
            continue
        data = meta(node)
        data["previous_node_id"] = node_id
        set_meta(node, data)
        record(node, op, f"{node_id} -> {new_id}; {reason}")
        if "node_id" in node:
            node["node_id"] = new_id
        if "id" in node:
            node["id"] = new_id
    for edge in edges:
        for side in ("source", "target"):
            if edge.get(side) in renames:
                edge[side] = renames[edge[side]]
                edge[f"{side}_id"] = edge[side]


# --------------------------------------------------------------------------- 3
def fix_metadata_years(nodes: list[dict]) -> None:
    op = "fix_metadata_years"
    by_id = {nid(n): n for n in nodes}
    for node_id, (wrong, right, source) in META_YEAR_FIXES.items():
        node = by_id.get(node_id)
        if node is None:
            warn(op, f"{node_id} not found")
            continue
        data = meta(node)
        if data.get("year") == right:
            continue  # idempotent
        if data.get("year") != wrong:
            warn(op, f"{node_id}: expected year {wrong}, found {data.get('year')}")
            continue
        data["year"] = right
        set_meta(node, data)
        record(node, op, f"metadata.year {wrong} -> {right}; {source}")
        note(op, f"{node_id}: year {wrong} -> {right}")


# --------------------------------------------------------------------------- 4
def set_backfilled_years(nodes: list[dict]) -> None:
    """After the id rename, make metadata.year agree with the resolved year."""
    op = "set_backfilled_years"
    by_id = {nid(n): n for n in nodes}
    for _old, new_id, year, source in YEAR_BACKFILL:
        node = by_id.get(new_id)
        if node is None:
            continue
        data = meta(node)
        if data.get("year") == year:
            continue
        data["year"] = year
        set_meta(node, data)
        record(node, op, f"metadata.year set to {year}; {source}")
        note(op, f"{new_id}: year := {year}")


# --------------------------------------------------------------------------- 5
def merge_nodes(nodes: list[dict], edges: list[dict]) -> tuple[list[dict], list[dict]]:
    op = "merge_nodes"
    by_id = {nid(n): n for n in nodes}
    remap: dict[str, str] = {}
    for merge in BIBLIOGRAPHIC_MERGES:
        keep, drop = by_id.get(merge["keep"]), by_id.get(merge["drop"])
        if drop is None:
            continue  # idempotent
        if keep is None:
            warn(op, f"survivor {merge['keep']} not found")
            continue
        keep_meta, drop_meta = meta(keep), meta(drop)
        for field, value in drop_meta.items():
            if field not in keep_meta and not field.startswith(
                ("deep_audit", "previous_node")
            ):
                keep_meta[field] = value
        keep_meta.setdefault(f"{STAMP}_merged_from", []).append(merge["drop"])
        set_meta(keep, keep_meta)
        record(keep, op, f"absorbed {merge['drop']}: {merge['reason']}")
        remap[merge["drop"]] = merge["keep"]
        note(op, f"{merge['drop']} -> {merge['keep']} ({merge['reason']})")
    if not remap:
        return nodes, edges
    nodes = [n for n in nodes if nid(n) not in remap]
    seen, kept = set(), []
    for edge in edges:
        src = remap.get(edge["source"], edge["source"])
        tgt = remap.get(edge["target"], edge["target"])
        if src == tgt:
            continue
        triple = (src, edge["relation"], tgt)
        if triple in seen:
            continue
        seen.add(triple)
        edge["source"] = edge["source_id"] = src
        edge["target"] = edge["target_id"] = tgt
        kept.append(edge)
    return nodes, kept


# --------------------------------------------------------------------------- 6
def fix_editor_not_author(edges: list[dict]) -> list[dict]:
    """Retype an editor's authored_by to edited_by and drop the bogus creates."""
    op = "fix_editor_not_author"
    pairs = set(EDITOR_NOT_AUTHOR)
    kept: list[dict] = []
    existing = {(e["source"], e["relation"], e["target"]) for e in edges}
    for edge in edges:
        pair = (edge["source"], edge["target"])
        if edge["relation"] == "authored_by" and pair in pairs:
            if (edge["source"], "edited_by", edge["target"]) in existing:
                note(op, f"dropped redundant authored_by {pair[0]} -> {pair[1]}")
                continue
            edge["relation"] = "edited_by"
            data = edge.get("metadata") or {}
            if isinstance(data, dict):
                data[STAMP] = op
                data[f"{STAMP}_note"] = (
                    "R.W. Sharples is the EDITOR (with R. Sorabji) of Greek and Roman Philosophy "
                    "100 BC-200 AD, BICS Suppl. 94 (2007), in which Boys-Stones' chapter appeared; "
                    "he is not a co-author of the chapter. DOI 10.1111/j.2041-5370.2007.tb02440.x"
                )
                edge["metadata"] = data
            note(op, f"authored_by -> edited_by: {pair[0]} -> {pair[1]}")
            kept.append(edge)
            continue
        if edge["relation"] == "creates" and (edge["target"], edge["source"]) in pairs:
            note(
                op,
                f"dropped creates {edge['source']} -> {edge['target']} (editor, not creator)",
            )
            continue
        kept.append(edge)
    return kept


# --------------------------------------------------------------------------- 7
def flag_grey_literature(nodes: list[dict]) -> None:
    op = "flag_grey_literature"
    by_id = {nid(n): n for n in nodes}
    for node_id, reason in GREY_LITERATURE.items():
        node = by_id.get(node_id)
        if node is None:
            warn(op, f"{node_id} not found")
            continue
        data = meta(node)
        if data.get("grey_literature"):
            continue
        data["grey_literature"] = True
        data["grey_literature_reason"] = reason
        set_meta(node, data)
        note(op, f"{node_id}: flagged grey literature")


# --------------------------------------------------------------------------- 8
def fix_labels(nodes: list[dict]) -> None:
    op = "fix_labels"
    by_id = {nid(n): n for n in nodes}
    for node_id, (old, new, source) in LABEL_FIXES.items():
        node = by_id.get(node_id)
        if node is None:
            warn(op, f"{node_id} not found")
            continue
        if node.get("label") == new:
            continue
        if node.get("label") != old:
            warn(
                op,
                f"{node_id}: label is {node.get('label')!r}, not the expected {old!r}",
            )
            continue
        node["label"] = new
        record(node, op, f"label corrected; {source}")
        note(op, f"{node_id}: label corrected")


# --------------------------------------------------------------------------- 8b
def propagate_renames_to_metadata(
    nodes: list[dict], remap: dict[str, str], present: set[str]
) -> None:
    """Carry renames and merges into the metadata pointer fields.

    ``scholar_id`` / ``author_id`` / ``scholarly_work_id`` / ``publication`` are
    the join keys of the secondary (reception) layer. Renaming a node without
    rewriting them re-creates exactly the dangling-pointer defect wave 1 fixed.
    """
    op = "propagate_renames_to_metadata"
    fields = ("scholar_id", "author_id", "scholarly_work_id", "publication")
    for node in nodes:
        data = meta(node)
        if not data:
            continue
        changed = []
        for field in fields:
            value = data.get(field)
            if not isinstance(value, str) or value in present:
                continue
            replacement = remap.get(value)
            if replacement and replacement in present:
                data[field] = replacement
                changed.append(f"{field}: {value} -> {replacement}")
        if changed:
            set_meta(node, data)
            record(node, op, "; ".join(changed))
            note(op, f"{nid(node)}: " + "; ".join(changed))


# --------------------------------------------------------------------------- 9
def propagate_to_citations(remap: dict[str, str], present: set[str]) -> None:
    op = "propagate_to_citations"
    if not CITATIONS_PATH.exists():
        return
    rows = read_jsonl(CITATIONS_PATH)
    changed = 0
    for row in rows:
        current = row.get("kg_node_id")
        if current in present or current is None:
            continue
        replacement = remap.get(current)
        if replacement and replacement in present:
            row["kg_node_id"] = replacement
            changed += 1
            note(op, f"{current} -> {replacement}")
        else:
            warn(op, f"no mapping for dangling kg_node_id {current}")
    if changed:
        write_jsonl(CITATIONS_PATH, rows)


# --------------------------------------------------------------------------- main
def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    nodes = read_jsonl(NODES_PATH)
    edges = read_jsonl(EDGES_PATH)
    before = (len(nodes), len(edges))
    remap: dict[str, str] = {}

    surname = derive_surname_renames(nodes, edges)
    apply_renames(
        nodes,
        edges,
        surname,
        "surname_rename",
        "id surname contradicted the attributed scholar",
    )
    remap.update(surname)

    slug = dict(SLUG_FIXES)
    apply_renames(
        nodes, edges, slug, "slug_rename", "id slug did not match the person node id"
    )
    remap.update(slug)

    years = {}
    for old, new, _source in ID_YEAR_FIXES:
        years[remap.get(old, old)] = new
        remap[old] = new
    apply_renames(
        nodes,
        edges,
        years,
        "id_year_rename",
        "id year contradicted the printed edition",
    )

    backfill = {}
    for old, new, _year, _source in YEAR_BACKFILL:
        backfill[remap.get(old, old)] = new
        remap[old] = new
    apply_renames(
        nodes,
        edges,
        backfill,
        "year_backfill_rename",
        "'_0_' year placeholder resolved",
    )

    fix_metadata_years(nodes)
    set_backfilled_years(nodes)
    nodes, edges = merge_nodes(nodes, edges)
    for merge in BIBLIOGRAPHIC_MERGES:
        remap[merge["drop"]] = merge["keep"]
    edges = fix_editor_not_author(edges)
    flag_grey_literature(nodes)
    fix_labels(nodes)

    # Compose so a node renamed then merged resolves in one hop.
    remap = {old: remap.get(new, new) for old, new in remap.items()}

    ids = [nid(n) for n in nodes]
    propagate_renames_to_metadata(nodes, remap, set(ids))
    assert len(ids) == len(set(ids)), "duplicate node ids produced"
    present = set(ids)
    assert not [
        e for e in edges if e["source"] not in present or e["target"] not in present
    ], "dangling edges produced"
    assert not [
        e
        for e in edges
        if e["source"] != e["source_id"] or e["target"] != e["target_id"]
    ], "source/target field divergence produced"
    triples = [(e["source"], e["relation"], e["target"]) for e in edges]
    assert len(triples) == len(set(triples)), "duplicate triples produced"
    stale = [
        (nid(n), f, meta(n)[f])
        for n in nodes
        for f in ("scholar_id", "author_id", "scholarly_work_id", "publication")
        if isinstance(meta(n).get(f), str)
        and meta(n)[f] not in present
        and meta(n)[f].startswith(("person_", "scholar_", "pub_", "scholarly_work_"))
    ]
    assert not stale, f"dangling metadata pointers produced: {stale[:5]}"

    print(f"nodes {before[0]} -> {len(nodes)}   edges {before[1]} -> {len(edges)}")
    for key in sorted(counts):
        print(f"  {key}: {counts[key]}")
    print("invariants: OK")

    if args.dry_run:
        print("\n--dry-run: nothing written")
        return 0

    write_jsonl(NODES_PATH, nodes)
    write_jsonl(EDGES_PATH, edges)
    propagate_to_citations(remap, present)
    report = ROOT / "data" / "audit" / "2026-08-16_deep_audit_bibliographic_applied.md"
    report.write_text(
        "# Deep audit wave 2 — externally verified bibliography, applied 2026-08-16\n\n"
        f"nodes {before[0]} -> {len(nodes)}, edges {before[1]} -> {len(edges)}\n\n"
        + "\n".join(f"- {line}" for line in log)
        + "\n",
        encoding="utf-8",
    )
    print(f"\nwrote {NODES_PATH}\nwrote {EDGES_PATH}\nwrote {report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
