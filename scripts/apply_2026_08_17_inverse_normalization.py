#!/usr/bin/env python3
"""Normalize materialized inverse KG edges to one canonical asserted direction.

Usage:
    python3 scripts/apply_2026_08_17_inverse_normalization.py
    python3 scripts/apply_2026_08_17_inverse_normalization.py --write
    python3 scripts/apply_2026_08_17_inverse_normalization.py \
        --nodes /tmp/kg/nodes.jsonl --edges /tmp/kg/edges.jsonl --write

Dry-run is the default.  ``--write`` creates ``edges.jsonl.bak-inverse_norm``
before an atomic replacement.  Re-running after a successful write is a no-op.
Every planned pair is re-verified immediately before mutation.
"""

from __future__ import annotations

import argparse
import copy
import json
import shutil
import tempfile
from pathlib import Path
from typing import Any

from data_2026_08_17_inverse_normalization import (
    BAK_SUFFIX,
    DEFAULT_EDGES,
    DEFAULT_NODES,
    DEFAULT_ONTOLOGY,
    STAMP,
    PairPlan,
    build_plan,
    edge_triple,
    load_edge_types,
    metadata_dict,
    read_jsonl,
    summarize_plan,
)

EMPTY_VALUES = (None, "", [], {})
UNION_METADATA_KEYS = {"attested_by", "note", "notes"}


def _json_key(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)


def _unique_values(values: list[Any]) -> list[Any]:
    seen: set[str] = set()
    result: list[Any] = []
    for value in values:
        key = _json_key(value)
        if key not in seen:
            seen.add(key)
            result.append(copy.deepcopy(value))
    return result


def _as_union_items(value: Any) -> list[Any]:
    if value in EMPTY_VALUES:
        return []
    return list(value) if isinstance(value, list) else [value]


def _merge_mapping(
    survivor: dict[str, Any],
    doomed: dict[str, Any],
    *,
    path: tuple[str, ...] = (),
) -> tuple[dict[str, Any], list[str], dict[str, Any]]:
    merged = copy.deepcopy(survivor)
    copied: list[str] = []
    conflicts: dict[str, Any] = {}
    for key, doomed_value in doomed.items():
        key_path = (*path, str(key))
        dotted = ".".join(key_path)
        survivor_value = merged.get(key)
        if key not in merged or survivor_value in EMPTY_VALUES:
            if doomed_value not in EMPTY_VALUES:
                merged[key] = copy.deepcopy(doomed_value)
                copied.append(dotted)
            continue
        if doomed_value in EMPTY_VALUES or survivor_value == doomed_value:
            continue
        if key in UNION_METADATA_KEYS:
            merged[key] = _unique_values(
                [*_as_union_items(survivor_value), *_as_union_items(doomed_value)]
            )
            copied.append(dotted)
        elif isinstance(survivor_value, dict) and isinstance(doomed_value, dict):
            child, child_copied, child_conflicts = _merge_mapping(
                survivor_value, doomed_value, path=key_path
            )
            merged[key] = child
            copied.extend(child_copied)
            conflicts.update(child_conflicts)
        elif key == "provenance":
            merged[key] = _unique_values(
                [*_as_union_items(survivor_value), *_as_union_items(doomed_value)]
            )
            copied.append(dotted)
        elif isinstance(survivor_value, list) and isinstance(doomed_value, list):
            merged[key] = _unique_values([*survivor_value, *doomed_value])
            copied.append(dotted)
        else:
            # Preserve the canonical value in place, and archive the doomed
            # value in the normalization stamp so metadata is not silently lost.
            conflicts[dotted] = copy.deepcopy(doomed_value)
    return merged, copied, conflicts


def _set_metadata(edge: dict[str, Any], metadata: dict[str, Any]) -> None:
    if isinstance(edge.get("metadata"), str):
        edge["metadata"] = json.dumps(metadata, ensure_ascii=False)
    else:
        edge["metadata"] = metadata


def merge_pair_metadata(
    survivor: dict[str, Any], doomed: dict[str, Any]
) -> tuple[list[str], dict[str, Any]]:
    merged, copied, conflicts = _merge_mapping(
        metadata_dict(survivor), metadata_dict(doomed)
    )
    stamp_payload: dict[str, Any] = {
        "doomed_edge_id": doomed["edge_id"],
        "doomed_relation": doomed["relation"],
        "metadata_keys_merged": sorted(set(copied)),
    }
    if conflicts:
        stamp_payload["doomed_metadata_conflicts"] = conflicts
    merged[STAMP] = stamp_payload
    _set_metadata(survivor, merged)
    return sorted(set(copied)), conflicts


def attestation_union(edges: list[dict[str, Any]]) -> set[str]:
    """Set-union of every metadata.attested_by item in the graph."""

    result: set[str] = set()
    for edge in edges:
        value = metadata_dict(edge).get("attested_by")
        for item in _as_union_items(value):
            result.add(_json_key(item))
    return result


def _validate_precondition(
    item: PairPlan,
    by_id: dict[str, dict[str, Any]],
    edge_types: dict[str, dict[str, Any]],
) -> tuple[dict[str, Any], dict[str, Any]]:
    survivor = by_id.get(item.survivor_id)
    doomed = by_id.get(item.doomed_id)
    if survivor is None or doomed is None:
        raise RuntimeError(
            f"precondition failed: pair disappeared ({item.survivor_id}, {item.doomed_id})"
        )
    expected_survivor = (
        item.survivor_source,
        item.survivor_relation,
        item.survivor_target,
    )
    expected_doomed = (
        item.doomed_source,
        item.doomed_relation,
        item.doomed_target,
    )
    if edge_triple(survivor) != expected_survivor:
        raise RuntimeError(
            f"precondition failed: survivor drifted {item.survivor_id}: "
            f"{edge_triple(survivor)} != {expected_survivor}"
        )
    if edge_triple(doomed) != expected_doomed:
        raise RuntimeError(
            f"precondition failed: doomed twin drifted {item.doomed_id}: "
            f"{edge_triple(doomed)} != {expected_doomed}"
        )
    if (
        item.survivor_source != item.doomed_target
        or item.survivor_target != item.doomed_source
    ):
        raise RuntimeError(
            f"precondition failed: endpoints no longer mirror for {item}"
        )
    declared = (
        edge_types.get(item.survivor_relation, {}).get("inverse")
        == item.doomed_relation
        or edge_types.get(item.doomed_relation, {}).get("inverse")
        == item.survivor_relation
    )
    if not declared:
        raise RuntimeError(
            f"precondition failed: ontology no longer declares pair {item}"
        )
    return survivor, doomed


def _assert_invariants(
    nodes: list[dict[str, Any]],
    before_edges: list[dict[str, Any]],
    after_edges: list[dict[str, Any]],
    edge_types: dict[str, dict[str, Any]],
    plan: list[PairPlan],
) -> None:
    node_ids = {
        str(node.get("id") or node.get("node_id") or "")
        for node in nodes
        if node.get("id") or node.get("node_id")
    }
    dangling = [
        edge
        for edge in after_edges
        if edge_triple(edge)[0] not in node_ids or edge_triple(edge)[2] not in node_ids
    ]
    assert not dangling, f"dangling edges: {[e.get('edge_id') for e in dangling[:5]]}"

    triples = [edge_triple(edge) for edge in after_edges]
    assert len(triples) == len(set(triples)), "duplicate triples"

    unpaired = [
        edge
        for edge in after_edges
        if edge.get("source") != edge.get("source_id")
        or edge.get("target") != edge.get("target_id")
    ]
    assert not unpaired, (
        "source/source_id or target/target_id disagree: "
        f"{[e.get('edge_id') for e in unpaired[:5]]}"
    )

    before_attestations = attestation_union(before_edges)
    after_attestations = attestation_union(after_edges)
    assert before_attestations == after_attestations, (
        "attested_by union changed: "
        f"lost={sorted(before_attestations - after_attestations)[:5]}, "
        f"added={sorted(after_attestations - before_attestations)[:5]}"
    )

    residual = build_plan(after_edges, edge_types)
    assert not residual, f"residual materialized inverse pairs: {len(residual)}"

    doomed_ids = {item.doomed_id for item in plan}
    survivor_ids = {item.survivor_id for item in plan}
    before_by_id = {str(edge["edge_id"]): edge for edge in before_edges}
    after_by_id = {str(edge["edge_id"]): edge for edge in after_edges}
    assert doomed_ids.isdisjoint(after_by_id), "a doomed inverse edge survived"
    for edge_id, edge in before_by_id.items():
        if edge_id not in doomed_ids | survivor_ids:
            assert after_by_id.get(edge_id) == edge, (
                f"unrelated edge changed: {edge_id}"
            )


def _write_jsonl_atomic(path: Path, rows: list[dict[str, Any]]) -> None:
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
        delete=False,
    ) as handle:
        temp_path = Path(handle.name)
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    temp_path.replace(path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--nodes", type=Path, default=DEFAULT_NODES)
    parser.add_argument("--edges", type=Path, default=DEFAULT_EDGES)
    parser.add_argument("--ontology", type=Path, default=DEFAULT_ONTOLOGY)
    parser.add_argument("--write", action="store_true", help="write after all checks")
    args = parser.parse_args()

    nodes = read_jsonl(args.nodes)
    original_edges = read_jsonl(args.edges)
    edge_types = load_edge_types(args.ontology)
    plan = build_plan(original_edges, edge_types)
    summary = summarize_plan(original_edges, plan)

    print(
        f"inverse normalization: edges {len(original_edges)} -> "
        f"{len(original_edges) - len(plan)}; pairs={len(plan)}"
    )
    for relation, count in summary["counts_per_relation"].items():
        print(f"  {relation}: {count}")

    if not plan:
        print("idempotence: no materialized inverse pair remains; nothing to do")
        print(
            "--write: no file changed" if args.write else "--dry-run: nothing written"
        )
        return 0

    edges = copy.deepcopy(original_edges)
    by_id = {str(edge["edge_id"]): edge for edge in edges}
    doomed_ids: set[str] = set()
    copied_fields = 0
    conflict_fields = 0

    # Re-verify every pair against the just-read apply-time state before the
    # first mutation.  A stale plan aborts atomically rather than partially.
    verified: list[tuple[PairPlan, dict[str, Any], dict[str, Any]]] = []
    for item in plan:
        survivor, doomed = _validate_precondition(item, by_id, edge_types)
        verified.append((item, survivor, doomed))

    for item, survivor, doomed in verified:
        copied, conflicts = merge_pair_metadata(survivor, doomed)
        copied_fields += len(copied)
        conflict_fields += len(conflicts)
        doomed_ids.add(item.doomed_id)

    edges = [edge for edge in edges if str(edge["edge_id"]) not in doomed_ids]
    _assert_invariants(nodes, original_edges, edges, edge_types, plan)

    print(f"metadata fields merged: {copied_fields}")
    print(f"metadata conflicts archived in stamp: {conflict_fields}")
    print("invariants: dangling=0; duplicate_triples=0; paired_ids=OK")
    print("invariant attested_by union: OK")
    print("residual materialized inverse pairs: 0")

    if not args.write:
        print("--dry-run (default): nothing written. Use --write to apply.")
        return 0

    backup = args.edges.with_name(args.edges.name + BAK_SUFFIX)
    if backup.exists():
        raise RuntimeError(f"refusing to overwrite existing backup: {backup}")
    shutil.copy2(args.edges, backup)
    _write_jsonl_atomic(args.edges, edges)
    print(f"backup: {backup}")
    print(f"wrote: {args.edges}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
