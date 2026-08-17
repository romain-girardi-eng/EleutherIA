#!/usr/bin/env python3
"""Apply the complete Magna Moralia TLG re-ingestion wave.

Dry-run is the default.  ``--write`` is required to mutate the selected copies.
The optional data directory contains ``nodes.jsonl``, ``edges.jsonl`` and
``passages.jsonl`` and exists specifically for an out-of-repository sandbox.

Usage:
    python3 scripts/apply_2026_08_17_mm_reingest.py
    python3 scripts/apply_2026_08_17_mm_reingest.py --write
    python3 scripts/apply_2026_08_17_mm_reingest.py --data-dir /tmp/mm-data --write

``MM_REINGEST_DATA_DIR`` is the environment equivalent of ``--data-dir``.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
import unicodedata
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from data_2026_08_17_mm_reingest import (  # noqa: E402
    BACKUP_SUFFIX,
    ENGLISH_MM_NODE_IDS,
    LINGUISTIC_STAMP,
    MM_REINGEST_RECORDS,
    RECORD_COUNT,
    STAMP,
    TEXT_SOURCE,
    TLG_FILE,
)

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_NODES = ROOT / "data" / "kg" / "nodes.jsonl"
DEFAULT_EDGES = ROOT / "data" / "kg" / "edges.jsonl"
DEFAULT_CORPUS = ROOT / "data" / "corpus" / "passages.jsonl"
DATA_DIR_ENV = "MM_REINGEST_DATA_DIR"

GREEK = re.compile(r"[\u0370-\u03ff\u1f00-\u1fff]")


def read_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def write_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def node_id(node: dict) -> str:
    return node.get("node_id") or node.get("id") or ""


def metadata(node: dict) -> dict:
    value = node.get("metadata")
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            return {}
    return value if isinstance(value, dict) else {}


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


def resolve_paths(data_dir: str | None) -> tuple[Path, Path, Path]:
    selected = data_dir or os.environ.get(DATA_DIR_ENV)
    if selected:
        directory = Path(selected).expanduser().resolve()
        return (
            directory / "nodes.jsonl",
            directory / "edges.jsonl",
            directory / "passages.jsonl",
        )
    return DEFAULT_NODES, DEFAULT_EDGES, DEFAULT_CORPUS


def check_wave_data() -> None:
    assert len(MM_REINGEST_RECORDS) == RECORD_COUNT == 434
    ids = [record["node_id"] for record in MM_REINGEST_RECORDS]
    uuids = [record["corpus_uuid"] for record in MM_REINGEST_RECORDS]
    assert len(ids) == len(set(ids)), "duplicate ids in re-ingestion data"
    assert len(uuids) == len(set(uuids)), "duplicate corpus UUIDs in data"
    assert not ENGLISH_MM_NODE_IDS, "English MM nodes must not receive Greek"
    assert not [item for item in ids if item.endswith("_en")]
    for left, right in zip(
        MM_REINGEST_RECORDS, MM_REINGEST_RECORDS[1:], strict=False
    ):
        assert (
            left["tlg_anchor"]["end_byte"]
            < right["tlg_anchor"]["start_byte"]
        ), f"non-increasing TLG spans: {left['node_id']} / {right['node_id']}"
    for record in MM_REINGEST_RECORDS:
        evidence = record["anchor_evidence"]
        assert 0.8 <= evidence["span_length_ratio"] <= 1.25
        assert "?" not in record["replacement_greek"]
        assert greek_fraction(record["replacement_greek"]) >= 0.90


def rewrite(
    nodes: list[dict], corpus: list[dict]
) -> tuple[Counter, Counter, list[str]]:
    nodes_by_id = {node_id(node): node for node in nodes}
    corpus_by_id = {row.get("passage_id"): row for row in corpus}
    done: Counter = Counter()
    skipped: Counter = Counter()
    details: list[str] = []

    for record in MM_REINGEST_RECORDS:
        wanted_id = record["node_id"]
        replacement = unicodedata.normalize("NFC", record["replacement_greek"])
        node = nodes_by_id.get(wanted_id)
        if node is None:
            skipped["node missing"] += 1
            skipped["corpus blocked by node"] += 1
            details.append(f"{wanted_id}: node missing")
            continue

        before_node = json.dumps(node, ensure_ascii=False, sort_keys=True)
        current = node.get("description") or ""
        meta = metadata(node)
        had_linguistic_stamp = LINGUISTIC_STAMP in meta

        precondition_error = None
        if meta.get("canonical_ref") != record["canonical_ref"]:
            precondition_error = (
                f"canonical_ref={meta.get('canonical_ref')!r}, "
                f"expected {record['canonical_ref']!r}"
            )
        elif meta.get("db_passage_id") != record["corpus_uuid"]:
            precondition_error = "db_passage_id no longer matches the corpus UUID"
        elif meta.get("language") != "grc":
            precondition_error = f"language={meta.get('language')!r}, expected 'grc'"
        elif wanted_id.endswith("_en"):
            precondition_error = "English twin excluded"
        elif not (
            current.startswith(record["expected_old_incipit"])
            or had_linguistic_stamp
            or meta.get(STAMP)
        ):
            precondition_error = (
                "description no longer starts with the recorded old incipit "
                "and has neither applicable stamp"
            )

        if precondition_error:
            skipped[f"node precondition: {precondition_error}"] += 1
            skipped["corpus blocked by node"] += 1
            details.append(f"{wanted_id}: {precondition_error}")
            continue

        # Validate the twin before mutating the node so each record is atomic in
        # memory: a stale/missing corpus line blocks both sides of the rewrite.
        twin = corpus_by_id.get(record["corpus_uuid"])
        if twin is None:
            skipped["node blocked by missing corpus twin"] += 1
            skipped["corpus twin missing"] += 1
            details.append(f"{wanted_id}: corpus twin missing")
            continue
        current_twin = twin.get("text_content") or ""
        if not (
            current_twin == replacement
            or current_twin.startswith(record["expected_old_corpus_incipit"])
        ):
            skipped["node blocked by corpus precondition"] += 1
            skipped["corpus precondition failed"] += 1
            details.append(
                f"{wanted_id}: corpus text no longer starts with recorded incipit"
            )
            continue

        meta["tlg_anchor"] = dict(record["tlg_anchor"])
        meta["text_source"] = TEXT_SOURCE
        meta["char_length"] = len(replacement)
        meta["word_count"] = len(replacement.split())
        meta.pop("needs_reingestion", None)
        meta[STAMP] = "description_replaced_from_tlg0086"
        meta[f"{STAMP}_note"] = (
            f"Greek replaced from {TLG_FILE} half-open bytes "
            f"{record['tlg_anchor']['start_byte']}-"
            f"{record['tlg_anchor']['end_byte']}"
        )
        node["description"] = replacement
        set_metadata(node, meta)

        after_node = json.dumps(node, ensure_ascii=False, sort_keys=True)
        if after_node == before_node:
            skipped["node already applied"] += 1
        else:
            done["nodes"] += 1

        if current_twin == replacement:
            skipped["corpus already replacement"] += 1
        else:
            twin["text_content"] = replacement
            done["corpus"] += 1

    return done, skipped, details


def check_invariants(
    nodes: list[dict], edges: list[dict], corpus: list[dict]
) -> dict[str, int]:
    ids = [node_id(node) for node in nodes]
    assert len(ids) == len(set(ids)), "duplicate node ids"
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
    assert not split, (
        f"{len(split)} edges with source/source_id or target/target_id mismatch"
    )
    triples = [
        (edge.get("source"), edge.get("relation"), edge.get("target"))
        for edge in edges
    ]
    assert len(triples) == len(set(triples)), "duplicate edge triples"

    corpus_ids = [row.get("passage_id") for row in corpus]
    assert len(corpus_ids) == len(set(corpus_ids)), "duplicate corpus passage ids"
    corpus_by_id = {row.get("passage_id"): row for row in corpus}

    rewritten = [node for node in nodes if metadata(node).get(STAMP)]
    thin = [
        node_id(node)
        for node in rewritten
        if greek_fraction(node.get("description") or "") < 0.90
    ]
    assert not thin, f"{len(thin)} rewritten descriptions are under 90% Greek"
    question_marks = [
        node_id(node) for node in rewritten if "?" in (node.get("description") or "")
    ]
    assert not question_marks, f"{len(question_marks)} rewritten nodes contain '?'"

    inconsistent_twins = []
    for node in rewritten:
        meta = metadata(node)
        twin = corpus_by_id.get(meta.get("db_passage_id"))
        if twin is None or twin.get("text_content") != node.get("description"):
            inconsistent_twins.append(node_id(node))
    assert not inconsistent_twins, (
        f"{len(inconsistent_twins)} rewritten nodes have missing/different corpus twins"
    )
    assert not [node_id(node) for node in rewritten if node_id(node).endswith("_en")]

    return {
        "unique_node_ids": len(ids),
        "dangling_edges": len(dangling),
        "split_edge_endpoints": len(split),
        "duplicate_triples": len(triples) - len(set(triples)),
        "rewritten_descriptions": len(rewritten),
        "thin_rewritten_descriptions": len(thin),
        "question_marks": len(question_marks),
        "inconsistent_twins": len(inconsistent_twins),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="validate only (default)")
    mode.add_argument("--write", action="store_true", help="write selected data files")
    parser.add_argument(
        "--data-dir",
        help=(
            "directory containing nodes.jsonl, edges.jsonl and passages.jsonl; "
            f"or set {DATA_DIR_ENV}"
        ),
    )
    args = parser.parse_args()

    check_wave_data()
    nodes_path, edges_path, corpus_path = resolve_paths(args.data_dir)
    for path in (nodes_path, edges_path, corpus_path):
        if not path.is_file():
            parser.error(f"data file not found: {path}")

    nodes = read_jsonl(nodes_path)
    edges = read_jsonl(edges_path)
    corpus = read_jsonl(corpus_path)
    done, skipped, details = rewrite(nodes, corpus)
    invariants = check_invariants(nodes, edges, corpus)
    changes = done["nodes"] + done["corpus"]

    print(f"mode: {'write' if args.write else 'dry-run'}")
    print(f"records: {RECORD_COUNT}")
    print(f"nodes done: {done['nodes']}")
    print(f"corpus done: {done['corpus']}")
    print(f"total changes: {changes}")
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
        if len(details) > 20:
            print(f"  ... {len(details) - 20} more")
    print(
        "invariants: OK "
        f"(unique ids={invariants['unique_node_ids']}; "
        f"dangling={invariants['dangling_edges']}; "
        f"split endpoints={invariants['split_edge_endpoints']}; "
        f"duplicate triples={invariants['duplicate_triples']}; "
        f"rewritten={invariants['rewritten_descriptions']}; "
        f"under 90% Greek={invariants['thin_rewritten_descriptions']}; "
        f"question marks={invariants['question_marks']}; "
        f"different twins={invariants['inconsistent_twins']})"
    )

    if not args.write:
        print("write: disabled (--dry-run default)")
        return 0
    if changes == 0:
        print("write: no-op (0 changes)")
        return 0

    for path in (nodes_path, edges_path, corpus_path):
        shutil.copyfile(path, Path(str(path) + BACKUP_SUFFIX))
    write_jsonl(nodes_path, nodes)
    write_jsonl(corpus_path, corpus)
    print(f"wrote: {nodes_path}")
    print(f"wrote: {corpus_path}")
    print(
        "backups: "
        + ", ".join(str(Path(str(path) + BACKUP_SUFFIX)) for path in (
            nodes_path,
            edges_path,
            corpus_path,
        ))
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
