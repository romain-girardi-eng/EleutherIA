#!/usr/bin/env python3
"""Apply the Plotinus canonical-reference remap.

Dry-run is the default.  ``--write`` is required to mutate the selected copy of
``nodes.jsonl``.  The optional data directory is intended for out-of-repository
verification and must contain ``nodes.jsonl`` and ``edges.jsonl``.

This wave changes labels and reference metadata only.  It never reads or writes
``data/corpus`` and it asserts that every node description remains byte-for-byte
unchanged.

Usage:
    python3 scripts/apply_2026_08_17_plotinus_remap.py
    python3 scripts/apply_2026_08_17_plotinus_remap.py --write
    python3 scripts/apply_2026_08_17_plotinus_remap.py \
        --data-dir /tmp/plotinus-remap-data --write
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from data_2026_08_17_plotinus_remap import (  # noqa: E402
    BACKUP_SUFFIX,
    CITATION_SELECTION_METHOD,
    ENNEAD_RUNS,
    IDT_VALIDATION,
    LINGUISTIC_STAMP,
    OFFSET_DISCONTINUITIES,
    PLOTINUS_REMAP_RECORDS,
    RECORD_COUNT,
    REFERENCE_PRECISION,
    STAMP,
    TEXT_SOURCE,
    TLG_FILE,
    TLG_WORK_URN,
    UNRESOLVABLE_RECORDS,
    check_payload,
)

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_NODES = ROOT / "data" / "kg" / "nodes.jsonl"
DEFAULT_EDGES = ROOT / "data" / "kg" / "edges.jsonl"
DATA_DIR_ENV = "PLOTINUS_REMAP_DATA_DIR"
TARGET_ID = re.compile(r"^passage_plotinus_vi_9_\d+$")


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


def description_sha256(node: dict) -> str:
    return hashlib.sha256((node.get("description") or "").encode("utf-8")).hexdigest()


def descriptions_digest(nodes: list[dict]) -> str:
    digest = hashlib.sha256()
    for node in nodes:
        digest.update(node_id(node).encode("utf-8"))
        digest.update(b"\0")
        digest.update((node.get("description") or "").encode("utf-8"))
        digest.update(b"\0")
    return digest.hexdigest()


def resolve_paths(data_dir: str | None) -> tuple[Path, Path]:
    selected = data_dir or os.environ.get(DATA_DIR_ENV)
    if selected:
        directory = Path(selected).expanduser().resolve()
        return directory / "nodes.jsonl", directory / "edges.jsonl"
    return DEFAULT_NODES, DEFAULT_EDGES


def check_wave_data() -> None:
    check_payload()
    assert len(PLOTINUS_REMAP_RECORDS) + len(UNRESOLVABLE_RECORDS) == RECORD_COUNT
    assert not OFFSET_DISCONTINUITIES
    assert sum(run["count"] for run in ENNEAD_RUNS) == len(PLOTINUS_REMAP_RECORDS)
    assert IDT_VALIDATION["boundary_matches"] == IDT_VALIDATION["block_count"]
    for left, right in zip(
        PLOTINUS_REMAP_RECORDS, PLOTINUS_REMAP_RECORDS[1:], strict=False
    ):
        if (
            left["derived_citation"]["ennead"]
            == right["derived_citation"]["ennead"]
        ):
            assert left["byte_anchor"]["start"] < right["byte_anchor"]["start"]
            assert left["byte_anchor"]["end"] < right["byte_anchor"]["end"]
    for record in PLOTINUS_REMAP_RECORDS:
        assert record["derived_citation"]["reference_precision"] in {
            "ennead.treatise.chapter",
            "ennead.treatise",
        }
        assert record["evidence"]["exact_base_letter_match_fraction"] >= 0.90
        assert record["byte_anchor"]["start"] < record["byte_anchor"]["end"]


def _already_applied_error(node: dict, meta: dict, record: dict) -> str | None:
    expected_anchor = {
        "source": TEXT_SOURCE,
        "file": TLG_FILE,
        "start_byte": record["byte_anchor"]["start"],
        "end_byte": record["byte_anchor"]["end"],
        "offset_semantics": "half-open exact-match envelope",
    }
    checks = [
        (meta.get("canonical_ref"), record["new_canonical_ref"], "canonical_ref"),
        (meta.get("cts_urn"), record["new_cts_urn"], "cts_urn"),
        (meta.get("reference_precision"), REFERENCE_PRECISION, "reference_precision"),
        (meta.get("tlg_anchor"), expected_anchor, "tlg_anchor"),
        (node.get("label"), record["new_label"], "label"),
    ]
    for actual, expected, field in checks:
        if actual != expected:
            return f"stamped node has {field}={actual!r}, expected {expected!r}"
    if meta.get("needs_reference_remapping"):
        return "stamped node still has needs_reference_remapping=true"
    if description_sha256(node) != record["evidence"]["description_sha256"]:
        return "stamped node description hash differs from the audited description"
    return None


def rewrite(nodes: list[dict]) -> tuple[Counter, Counter, list[str]]:
    nodes_by_id = {node_id(node): node for node in nodes}
    done: Counter = Counter()
    skipped: Counter = Counter()
    details: list[str] = []

    for record in PLOTINUS_REMAP_RECORDS:
        wanted_id = record["node_id"]
        node = nodes_by_id.get(wanted_id)
        if node is None:
            skipped["precondition blocked"] += 1
            details.append(f"{wanted_id}: node missing")
            continue
        meta = metadata(node)

        if meta.get(STAMP):
            error = _already_applied_error(node, meta, record)
            if error:
                skipped["precondition blocked"] += 1
                details.append(f"{wanted_id}: {error}")
            else:
                skipped["already applied"] += 1
            continue

        precondition_error = None
        if meta.get("needs_reference_remapping") is not True:
            precondition_error = "needs_reference_remapping is not true"
        elif meta.get("source_fragment_index") != record["source_fragment_index"]:
            precondition_error = (
                f"source_fragment_index={meta.get('source_fragment_index')!r}, "
                f"expected {record['source_fragment_index']}"
            )
        elif meta.get("canonical_ref") is not None:
            precondition_error = (
                f"canonical_ref={meta.get('canonical_ref')!r}, expected null"
            )
        elif meta.get("cts_urn") != TLG_WORK_URN:
            precondition_error = (
                f"cts_urn={meta.get('cts_urn')!r}, expected {TLG_WORK_URN!r}"
            )
        elif meta.get("language") != "grc":
            precondition_error = f"language={meta.get('language')!r}, expected 'grc'"
        elif meta.get(LINGUISTIC_STAMP) != "flag_plotinus_fragment_refs":
            precondition_error = "linguistic repair flagging stamp missing or changed"
        elif description_sha256(node) != record["evidence"]["description_sha256"]:
            precondition_error = "description hash differs from the audited Greek"

        if precondition_error:
            skipped["precondition blocked"] += 1
            details.append(f"{wanted_id}: {precondition_error}")
            continue

        meta["canonical_ref"] = record["new_canonical_ref"]
        meta["cts_urn"] = record["new_cts_urn"]
        meta["reference_precision"] = REFERENCE_PRECISION
        meta["tlg_anchor"] = {
            "source": TEXT_SOURCE,
            "file": TLG_FILE,
            "start_byte": record["byte_anchor"]["start"],
            "end_byte": record["byte_anchor"]["end"],
            "offset_semantics": "half-open exact-match envelope",
        }
        citation = record["derived_citation"]
        meta["reference_derivation"] = {
            "method": CITATION_SELECTION_METHOD,
            "reference_precision": REFERENCE_PRECISION,
            "citation_span_start": citation["citation_span_start"],
            "citation_span_end": citation["citation_span_end"],
            "dominant_exact_letter_fraction": citation[
                "dominant_exact_letter_fraction"
            ],
            "exact_base_letter_match_fraction": record["evidence"][
                "exact_base_letter_match_fraction"
            ],
            "idt_txt_block_validation": (
                f"{IDT_VALIDATION['boundary_matches']}/"
                f"{IDT_VALIDATION['block_count']}"
            ),
        }
        meta.pop("needs_reference_remapping", None)
        meta[STAMP] = "canonical_reference_derived_from_tlg2000_idt"
        meta[f"{STAMP}_note"] = (
            f"Reference-only remap from {TLG_FILE} half-open exact-match envelope "
            f"{record['byte_anchor']['start']}-{record['byte_anchor']['end']}; "
            "description unchanged"
        )
        node["label"] = record["new_label"]
        set_metadata(node, meta)
        done["nodes"] += 1

    for unresolved in UNRESOLVABLE_RECORDS:
        skipped["unresolvable"] += 1
        details.append(
            f"{unresolved['node_id']}: unresolvable — {unresolved['reason']}"
        )
    return done, skipped, details


def check_invariants(
    nodes: list[dict], edges: list[dict], before_descriptions_digest: str
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
    assert descriptions_digest(nodes) == before_descriptions_digest, (
        "a node description changed during this reference-only wave"
    )

    by_id = {node_id(node): node for node in nodes}
    incomplete = []
    for record in PLOTINUS_REMAP_RECORDS:
        node = by_id.get(record["node_id"])
        if node is None:
            incomplete.append(record["node_id"])
            continue
        meta = metadata(node)
        if (
            meta.get(STAMP) != "canonical_reference_derived_from_tlg2000_idt"
            or meta.get("canonical_ref") != record["new_canonical_ref"]
            or meta.get("cts_urn") != record["new_cts_urn"]
            or meta.get("reference_precision") != REFERENCE_PRECISION
            or meta.get("needs_reference_remapping")
            or node.get("label") != record["new_label"]
            or description_sha256(node)
            != record["evidence"]["description_sha256"]
        ):
            incomplete.append(record["node_id"])
    assert not incomplete, f"{len(incomplete)} resolvable Plotinus nodes incomplete"

    target_nodes = [node for node in nodes if TARGET_ID.fullmatch(node_id(node))]
    assert len(target_nodes) == RECORD_COUNT
    still_flagged = [
        node_id(node)
        for node in target_nodes
        if metadata(node).get("needs_reference_remapping")
    ]
    assert len(still_flagged) == len(UNRESOLVABLE_RECORDS)

    return {
        "unique_node_ids": len(ids),
        "dangling_edges": len(dangling),
        "split_edge_endpoints": len(split),
        "duplicate_triples": len(triples) - len(set(triples)),
        "remapped_nodes": len(PLOTINUS_REMAP_RECORDS),
        "unresolvable_nodes": len(UNRESOLVABLE_RECORDS),
        "descriptions_changed": 0,
        "offset_discontinuities": len(OFFSET_DISCONTINUITIES),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="validate only (default)")
    mode.add_argument("--write", action="store_true", help="write selected nodes.jsonl")
    parser.add_argument(
        "--data-dir",
        help=(
            "directory containing nodes.jsonl and edges.jsonl; "
            f"or set {DATA_DIR_ENV}"
        ),
    )
    args = parser.parse_args()

    check_wave_data()
    nodes_path, edges_path = resolve_paths(args.data_dir)
    for path in (nodes_path, edges_path):
        if not path.is_file():
            parser.error(f"data file not found: {path}")

    nodes = read_jsonl(nodes_path)
    edges = read_jsonl(edges_path)
    before_digest = descriptions_digest(nodes)
    done, skipped, details = rewrite(nodes)
    blocked = skipped["precondition blocked"]
    if blocked:
        print(f"mode: {'write' if args.write else 'dry-run'}")
        print(f"records: {RECORD_COUNT}")
        print(f"resolvable: {len(PLOTINUS_REMAP_RECORDS)}")
        print(f"unresolvable: {len(UNRESOLVABLE_RECORDS)}")
        print(f"nodes done: {done['nodes']}")
        print(f"precondition blocked: {blocked}")
        print("blocked details:")
        for detail in details[:20]:
            print(f"  {detail}")
        if len(details) > 20:
            print(f"  ... {len(details) - 20} more")
        print("write: blocked")
        return 1

    invariants = check_invariants(nodes, edges, before_digest)
    changes = done["nodes"]
    print(f"mode: {'write' if args.write else 'dry-run'}")
    print(f"records: {RECORD_COUNT}")
    print(f"resolvable: {len(PLOTINUS_REMAP_RECORDS)}")
    print(f"unresolvable: {len(UNRESOLVABLE_RECORDS)}")
    print(f"nodes done: {done['nodes']}")
    print(f"already applied: {skipped['already applied']}")
    print(f"precondition blocked: {blocked}")
    print(f"descriptions changed: {invariants['descriptions_changed']}")
    print(
        "invariants: OK "
        f"(unique ids={invariants['unique_node_ids']}; "
        f"dangling={invariants['dangling_edges']}; "
        f"split endpoints={invariants['split_edge_endpoints']}; "
        f"duplicate triples={invariants['duplicate_triples']}; "
        f"remapped={invariants['remapped_nodes']}; "
        f"unresolvable={invariants['unresolvable_nodes']}; "
        f"description changes={invariants['descriptions_changed']}; "
        f"offset discontinuities={invariants['offset_discontinuities']})"
    )

    if not args.write:
        print("write: disabled (--dry-run default)")
        return 0
    if changes == 0:
        print("write: no-op (0 changes)")
        return 0

    backup = Path(str(nodes_path) + BACKUP_SUFFIX)
    if not backup.exists():
        shutil.copyfile(nodes_path, backup)
    write_jsonl(nodes_path, nodes)
    print(f"wrote: {nodes_path}")
    print(f"backup: {backup}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
