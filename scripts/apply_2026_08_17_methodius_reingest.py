#!/usr/bin/env python3
"""Apply the source-blocked Methodius locus-mapping delta.

Dry-run is the default.  ``--write`` is intended for an out-of-repository copy
selected with ``--data-dir``.  This wave never writes corpus passages and never
replaces Greek: the required TLG2959 source is absent.  It marks the 82 GCS
apparatus nodes as needing locus mapping while retaining their descriptions.

If TLG2959 later becomes available, this provisional delta refuses to run; a
new payload must then be built from the source rather than preserving a stale
"missing source" diagnosis.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import unicodedata
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from data_2026_08_17_methodius_reingest import (  # noqa: E402
    BACKUP_SUFFIX,
    DEFAULT_TLGE,
    RECORD_COUNT,
    SOURCE_BLOCKER_REASON,
    STAMP,
    blocked_records,
    check_data,
    metadata,
    node_id,
    source_inventory,
)

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_NODES = ROOT / "data" / "kg" / "nodes.jsonl"
DEFAULT_EDGES = ROOT / "data" / "kg" / "edges.jsonl"
DATA_DIR_ENV = "METHODIUS_REINGEST_DATA_DIR"
GREEK = re.compile(r"[\u0370-\u03ff\u1f00-\u1fff]")
REPLACEMENT_STAMP_VALUE = "description_replaced_from_tlg2959"
BLOCKED_STAMP_VALUE = "blocked_missing_tlg2959_source"


def read_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def write_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def set_metadata(node: dict, value: dict) -> None:
    if isinstance(node.get("metadata"), str):
        node["metadata"] = json.dumps(value, ensure_ascii=False)
    else:
        node["metadata"] = value


def greek_fraction(text: str) -> float:
    denominator = [
        char
        for char in text
        if not char.isspace()
        and not char.isdigit()
        and not unicodedata.category(char).startswith("P")
    ]
    return len(GREEK.findall(text)) / max(1, len(denominator))


def resolve_paths(data_dir: str | None) -> tuple[Path, Path]:
    selected = data_dir or os.environ.get(DATA_DIR_ENV)
    if selected:
        directory = Path(selected).expanduser().resolve()
        return directory / "nodes.jsonl", directory / "edges.jsonl"
    return DEFAULT_NODES, DEFAULT_EDGES


def rewrite(nodes: list[dict], records: tuple[dict, ...]) -> tuple[Counter, Counter, list[str], dict[str, str]]:
    nodes_by_id = {node_id(node): node for node in nodes}
    done: Counter = Counter()
    skipped: Counter = Counter()
    details: list[str] = []
    preserved_descriptions: dict[str, str] = {}

    for record in records:
        wanted_id = record["node_id"]
        node = nodes_by_id.get(wanted_id)
        if node is None:
            skipped["node missing"] += 1
            details.append(f"{wanted_id}: node missing")
            continue
        current = node.get("description") or ""
        preserved_descriptions[wanted_id] = current
        meta = metadata(node)
        current_sha = hashlib.sha256(current.encode("utf-8")).hexdigest()
        precondition_error = None
        if current_sha != record["description_sha256"]:
            precondition_error = "description hash drift"
        elif meta.get("canonical_ref") != record["canonical_ref"]:
            precondition_error = "canonical_ref drift"
        elif meta.get("db_passage_id") != record["corpus_uuid"]:
            precondition_error = "db_passage_id drift"
        elif meta.get("content_kind") != "apparatus_gcs":
            precondition_error = "content_kind is not apparatus_gcs"
        elif meta.get("passage_role") != "apparatus":
            precondition_error = "passage_role is not apparatus"
        elif meta.get("language") != "deu":
            precondition_error = "language is not deu"
        elif meta.get("needs_text_ingestion") is not True:
            precondition_error = "needs_text_ingestion is not true"
        elif not current:
            precondition_error = "empty apparatus description"
        if precondition_error:
            skipped[f"precondition: {precondition_error}"] += 1
            details.append(f"{wanted_id}: {precondition_error}")
            continue

        before = json.dumps(node, ensure_ascii=False, sort_keys=True)
        meta["needs_locus_mapping"] = True
        meta["needs_locus_mapping_reason"] = SOURCE_BLOCKER_REASON
        meta[STAMP] = BLOCKED_STAMP_VALUE
        meta[f"{STAMP}_note"] = (
            "No description or language field was changed; restore and verify "
            "TLG2959.TXT + TLG2959.IDT before building any Greek replacement."
        )
        set_metadata(node, meta)
        after = json.dumps(node, ensure_ascii=False, sort_keys=True)
        if before == after:
            skipped["already applied"] += 1
        else:
            done["nodes"] += 1
    return done, skipped, details, preserved_descriptions


def check_invariants(
    nodes: list[dict],
    edges: list[dict],
    preserved_descriptions: dict[str, str],
) -> dict[str, int]:
    ids = [node_id(node) for node in nodes]
    assert len(ids) == len(set(ids)), "duplicate node ids"
    nodes_by_id = {node_id(node): node for node in nodes}
    present = set(ids)
    dangling = [
        edge
        for edge in edges
        if edge.get("source") not in present or edge.get("target") not in present
    ]
    assert not dangling, f"{len(dangling)} dangling edges"
    split = [
        edge
        for edge in edges
        if edge.get("source") != edge.get("source_id")
        or edge.get("target") != edge.get("target_id")
    ]
    assert not split, f"{len(split)} edges with split endpoint fields"
    triples = [
        (edge.get("source"), edge.get("relation"), edge.get("target"))
        for edge in edges
    ]
    assert len(triples) == len(set(triples)), "duplicate edge triples"

    changed_descriptions = [
        wanted_id
        for wanted_id, description in preserved_descriptions.items()
        if (nodes_by_id[wanted_id].get("description") or "") != description
    ]
    assert not changed_descriptions, (
        f"{len(changed_descriptions)} blocked records changed descriptions"
    )

    flagged = [
        node
        for node in nodes
        if metadata(node).get(STAMP) == BLOCKED_STAMP_VALUE
    ]
    assert len(flagged) == RECORD_COUNT, (
        f"flagged {len(flagged)} Methodius nodes; expected {RECORD_COUNT}"
    )
    assert all(metadata(node).get("needs_locus_mapping") is True for node in flagged)
    assert all(metadata(node).get("needs_text_ingestion") is True for node in flagged)
    assert all(metadata(node).get("content_kind") == "apparatus_gcs" for node in flagged)
    assert all(metadata(node).get("passage_role") == "apparatus" for node in flagged)
    assert all(metadata(node).get("language") == "deu" for node in flagged)

    rewritten = [
        node
        for node in nodes
        if metadata(node).get(STAMP) == REPLACEMENT_STAMP_VALUE
    ]
    thin = [
        node_id(node)
        for node in rewritten
        if greek_fraction(node.get("description") or "") < 0.90
    ]
    assert not thin, f"{len(thin)} rewritten descriptions are under 90% Greek"
    question_marks = [
        node_id(node) for node in rewritten if "?" in (node.get("description") or "")
    ]
    assert not question_marks, f"{len(question_marks)} rewritten descriptions contain '?'"
    missing_apparatus = [
        node_id(node)
        for node in rewritten
        if not metadata(node).get("apparatus_gcs_content")
    ]
    assert not missing_apparatus, (
        f"{len(missing_apparatus)} rewritten nodes lost apparatus_gcs_content"
    )
    return {
        "unique_node_ids": len(ids),
        "dangling_edges": len(dangling),
        "split_edge_endpoints": len(split),
        "duplicate_triples": len(triples) - len(set(triples)),
        "blocked_records": len(flagged),
        "changed_descriptions": len(changed_descriptions),
        "rewritten_descriptions": len(rewritten),
        "thin_rewritten_descriptions": len(thin),
        "question_marks": len(question_marks),
        "rewritten_without_apparatus_copy": len(missing_apparatus),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="validate only (default)")
    mode.add_argument("--write", action="store_true", help="write selected data copy")
    parser.add_argument(
        "--data-dir",
        help=(
            "directory containing nodes.jsonl and edges.jsonl; "
            f"or set {DATA_DIR_ENV}"
        ),
    )
    parser.add_argument("--tlge-dir", type=Path, default=DEFAULT_TLGE)
    args = parser.parse_args()

    inventory = source_inventory(args.tlge_dir.expanduser())
    if inventory["source_available"]:
        parser.error(
            "TLG2959 is now available; this missing-source blocker delta is stale. "
            "Build and review the authentic Greek payload instead."
        )
    canonical_records = check_data(DEFAULT_NODES)
    nodes_path, edges_path = resolve_paths(args.data_dir)
    for path in (nodes_path, edges_path):
        if not path.is_file():
            parser.error(f"data file not found: {path}")
    nodes = read_jsonl(nodes_path)
    edges = read_jsonl(edges_path)
    done, skipped, details, preserved = rewrite(nodes, canonical_records)
    invariants = check_invariants(nodes, edges, preserved)

    print(f"mode: {'write' if args.write else 'dry-run'}")
    print("source: BLOCKED")
    print(f"source reason: {SOURCE_BLOCKER_REASON}")
    print(f"records: {RECORD_COUNT} metadata-only locus blockers")
    print("Greek replacement records: 0")
    print(f"nodes done: {done['nodes']}")
    print("descriptions changed: 0")
    print("corpus changes: 0")
    print("skipped/reasons:")
    if skipped:
        for reason, count in sorted(skipped.items()):
            print(f"  {reason}: {count}")
    else:
        print("  none: 0")
    if details:
        print("unexpected skip details:")
        for detail in details[:20]:
            print(f"  {detail}")
    print(
        "invariants: OK "
        f"(unique ids={invariants['unique_node_ids']}; "
        f"dangling={invariants['dangling_edges']}; "
        f"split endpoints={invariants['split_edge_endpoints']}; "
        f"duplicate triples={invariants['duplicate_triples']}; "
        f"blocked={invariants['blocked_records']}; "
        f"changed descriptions={invariants['changed_descriptions']}; "
        f"rewritten={invariants['rewritten_descriptions']}; "
        f"under 90% Greek={invariants['thin_rewritten_descriptions']}; "
        f"question marks={invariants['question_marks']}; "
        f"missing apparatus copies={invariants['rewritten_without_apparatus_copy']})"
    )

    if not args.write:
        print("write: disabled (--dry-run default)")
        return 0
    if done["nodes"] == 0:
        print("write: no-op (0 changes)")
        return 0
    for path in (nodes_path, edges_path):
        shutil.copyfile(path, Path(str(path) + BACKUP_SUFFIX))
    write_jsonl(nodes_path, nodes)
    print(f"wrote: {nodes_path}")
    print(
        "backups: "
        + ", ".join(
            str(Path(str(path) + BACKUP_SUFFIX)) for path in (nodes_path, edges_path)
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
