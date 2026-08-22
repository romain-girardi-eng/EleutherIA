#!/usr/bin/env python3
"""Apply the frozen 2026-08-18 R16 debt repair.

Dry-run is the default.  ``--write`` is the only mode that changes
``data/kg/edges.jsonl``.  The applier is deliberately edges-only: corpus data,
nodes, shared gates, and runtime code are never written.

Safety properties:

* the exact 518-edge id/triple/metadata baseline must match its frozen digest;
* every operation rechecks its own id, triple, and metadata hash;
* the projected graph must have zero unattested rendered fault-line edges;
* full node/edge/relation counts are asserted;
* the real R1-R18 checker is run before/after in memory, and non-R16 debt may
  not increase;
* ``--write`` creates ``edges.jsonl.bak-dialectic-zero-2026-08-18`` and uses
  an atomic replacement;
* a successful second run is a no-op.
"""

from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import os
import shutil
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from data_2026_08_18_dialectic_zero import (  # noqa: E402
    EDGES_PATH,
    EXPECTED_DELETED_COUNT,
    EXPECTED_EDGE_COUNT_AFTER,
    EXPECTED_EDGE_COUNT_BEFORE,
    EXPECTED_FAULT_LINES_AFTER,
    EXPECTED_NODE_COUNT,
    EXPECTED_RETAINED_COUNT,
    FAULT_LINE_RELATIONS,
    NODES_PATH,
    ROOT,
    STAMP,
    assert_frozen_baseline,
    build_plan,
    edge_is_attested,
    edge_metadata_sha256,
    metadata,
    node_id,
    read_jsonl,
    unattested_population,
)

RULES_CHECKER = ROOT / "scripts" / "check_ingestion_rules.py"
BACKUP_PATH = Path(f"{EDGES_PATH}.bak-dialectic-zero-2026-08-18")
TEMP_PATH = Path(f"{EDGES_PATH}.tmp-dialectic-zero-2026-08-18")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--write",
        action="store_true",
        help="write the projected edge snapshot (default: dry-run)",
    )
    mode.add_argument(
        "--dry-run",
        action="store_true",
        help="explicit spelling of the no-write default",
    )
    return parser.parse_args()


def set_metadata(obj: dict[str, Any], value: dict[str, Any]) -> None:
    """Preserve whether the row stores metadata as JSON text or an object."""

    if isinstance(obj.get("metadata"), str):
        obj["metadata"] = json.dumps(value, ensure_ascii=False)
    else:
        obj["metadata"] = value


def exact_precondition(edge: dict[str, Any], repair: Any) -> None:
    actual = (
        edge.get("edge_id"),
        edge.get("source"),
        edge.get("relation"),
        edge.get("target"),
        edge_metadata_sha256(edge),
    )
    expected = (
        repair.edge_id,
        repair.source,
        repair.relation,
        repair.target,
        repair.metadata_sha256,
    )
    if actual != expected:
        raise AssertionError(
            f"exact edge precondition moved for {repair.edge_id}: "
            f"{actual!r} != {expected!r}"
        )


def project_edges(
    edges: list[dict[str, Any]],
    plan: list[Any],
) -> list[dict[str, Any]]:
    by_id = {repair.edge_id: repair for repair in plan}
    projected: list[dict[str, Any]] = []
    seen: set[str] = set()

    for original in edges:
        edge = copy.deepcopy(original)
        edge_id = str(edge.get("edge_id") or "")
        repair = by_id.get(edge_id)
        if repair is None:
            projected.append(edge)
            continue

        exact_precondition(edge, repair)
        seen.add(edge_id)
        if repair.action == "delete":
            continue
        if repair.action != "retain" or not repair.attested_by:
            raise AssertionError(f"invalid repair action for {edge_id}: {repair}")

        data = metadata(edge)
        if data.get("attested_by"):
            raise AssertionError(f"{edge_id}: attestation appeared after planning")
        data["attested_by"] = repair.attested_by
        data[STAMP] = "retained"
        data[f"{STAMP}_basis"] = repair.bucket
        data[f"{STAMP}_rationale"] = repair.rationale
        set_metadata(edge, data)
        projected.append(edge)

    missing = sorted(set(by_id) - seen)
    if missing:
        raise AssertionError(f"planned edge ids disappeared: {missing[:5]}")
    return projected


def relation_counts(edges: list[dict[str, Any]]) -> dict[str, int]:
    counter = Counter(
        str(edge.get("relation"))
        for edge in edges
        if edge.get("relation") in FAULT_LINE_RELATIONS
    )
    return dict(sorted(counter.items()))


def assert_projected_graph(
    nodes: list[dict[str, Any]],
    before: list[dict[str, Any]],
    after: list[dict[str, Any]],
) -> None:
    assert len(nodes) == EXPECTED_NODE_COUNT
    assert len(before) == EXPECTED_EDGE_COUNT_BEFORE
    assert len(after) == EXPECTED_EDGE_COUNT_AFTER
    assert len(before) - len(after) == EXPECTED_DELETED_COUNT
    assert not unattested_population(after), "projected R16 debt is not zero"
    assert relation_counts(after) == EXPECTED_FAULT_LINES_AFTER

    before_ids = [str(edge.get("edge_id")) for edge in before]
    after_ids = [str(edge.get("edge_id")) for edge in after]
    assert len(before_ids) == len(set(before_ids)), "duplicate edge ids before"
    assert len(after_ids) == len(set(after_ids)), "duplicate edge ids after"

    node_ids = {node_id(node) for node in nodes}
    assert len(node_ids) == len(nodes), "duplicate node ids"
    unresolved = [
        str(edge.get("edge_id"))
        for edge in after
        if edge.get("source") not in node_ids or edge.get("target") not in node_ids
    ]
    assert not unresolved, f"unresolved endpoints after repair: {unresolved[:5]}"

    stamped = [edge for edge in after if metadata(edge).get(STAMP) == "retained"]
    assert len(stamped) == EXPECTED_RETAINED_COUNT
    assert all(edge_is_attested(edge) for edge in stamped)


def load_rules_checker(module_name: str) -> Any:
    spec = importlib.util.spec_from_file_location(module_name, RULES_CHECKER)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {RULES_CHECKER}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def gate_snapshot(
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    module_name: str,
) -> tuple[Counter[tuple[str, str, str, str]], Counter[str]]:
    checker = load_rules_checker(module_name)
    if frozenset(checker.DIALECTICAL_RELATIONS) != FAULT_LINE_RELATIONS:
        raise AssertionError("the shared rendered fault-line relation set moved")
    checker.check(nodes, edges, None, None)
    violations = Counter(tuple(item) for item in checker.violations)
    debt = Counter(checker.r16_debt_by_relation)
    return violations, debt


def assert_gate_non_regression(
    nodes: list[dict[str, Any]],
    before: list[dict[str, Any]],
    after: list[dict[str, Any]],
) -> tuple[int, int]:
    before_violations, before_r16 = gate_snapshot(
        nodes, before, "_dialectic_zero_gate_before"
    )
    after_violations, after_r16 = gate_snapshot(
        nodes, after, "_dialectic_zero_gate_after"
    )

    assert sum(before_r16.values()) == 518
    assert not after_r16, f"R16 checker still reports debt: {after_r16}"
    assert not any(key[0] == "R16_dialectic_unattested" for key in after_violations)

    before_non_r16 = Counter(
        {
            key: count
            for key, count in before_violations.items()
            if not key[0].startswith("R16")
        }
    )
    after_non_r16 = Counter(
        {
            key: count
            for key, count in after_violations.items()
            if not key[0].startswith("R16")
        }
    )
    new_violations = after_non_r16 - before_non_r16
    assert not new_violations, (
        "the projected repair introduced non-R16 gate violations: "
        f"{list(new_violations.items())[:5]}"
    )
    return sum(before_violations.values()), sum(after_violations.values())


def write_jsonl_atomic(path: Path, rows: list[dict[str, Any]]) -> None:
    if TEMP_PATH.exists():
        raise FileExistsError(f"refusing to reuse stale temporary file: {TEMP_PATH}")
    raw_rows: dict[str, tuple[dict[str, Any], str]] = {}
    order: list[str] = []
    with path.open(encoding="utf-8") as source:
        for line in source:
            if not line.strip():
                continue
            row = json.loads(line)
            edge_id = str(row.get("edge_id") or "")
            raw_rows[edge_id] = (row, line)
            order.append(edge_id)
    projected = {str(row.get("edge_id") or ""): row for row in rows}
    if len(projected) != len(rows):
        raise AssertionError("duplicate edge ids while writing dialectic-zero")
    try:
        with TEMP_PATH.open("x", encoding="utf-8") as handle:
            for edge_id in order:
                row = projected.get(edge_id)
                if row is None:
                    continue
                previous, raw_line = raw_rows[edge_id]
                if row == previous:
                    handle.write(raw_line)
                else:
                    handle.write(json.dumps(row, ensure_ascii=False) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(TEMP_PATH, path)
    finally:
        if TEMP_PATH.exists():
            TEMP_PATH.unlink()


def post_write_gate() -> None:
    result = subprocess.run(
        [sys.executable, str(RULES_CHECKER)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    print("--- check_ingestion_rules.py (written graph) ---")
    print(result.stdout.rstrip())
    if result.stderr:
        print(result.stderr.rstrip(), file=sys.stderr)
    if result.returncode != 0:
        raise RuntimeError(f"post-write ingestion gate failed: {result.returncode}")
    expected = "[DEBT] R16 existing unattested fault-line edges: 0"
    if expected not in result.stdout:
        raise AssertionError("post-write checker did not report R16 debt 0")


def already_complete(
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
) -> bool:
    if unattested_population(edges):
        return False
    # Idempotent no-op: do not insist on historical full counts if later valid
    # graph work has happened, but the shared R16 contract must remain clean.
    _, r16 = gate_snapshot(nodes, edges, "_dialectic_zero_gate_idempotent")
    assert not r16
    print("dialectic-zero: already complete; R16 debt is 0; no files written")
    return True


def main() -> int:
    if not __debug__:
        raise RuntimeError("refusing to run with assertions disabled (-O)")
    args = parse_args()
    nodes = read_jsonl(NODES_PATH)
    edges = read_jsonl(EDGES_PATH)

    if already_complete(nodes, edges):
        return 0

    plan = build_plan(nodes, edges)
    assert_frozen_baseline(nodes, edges, plan)
    projected = project_edges(edges, plan)
    assert_projected_graph(nodes, edges, projected)
    gate_before, gate_after = assert_gate_non_regression(nodes, edges, projected)

    print(
        "dialectic-zero dry projection: "
        f"nodes {len(nodes)} -> {len(nodes)}; "
        f"edges {len(edges)} -> {len(projected)}; "
        f"retained/attested {EXPECTED_RETAINED_COUNT}; "
        f"deleted {EXPECTED_DELETED_COUNT}; R16 debt 518 -> 0"
    )
    print(
        "R1-R18 full-graph findings: "
        f"{gate_before} -> {gate_after}; no non-R16 regression"
    )
    print("fault-line counts after:", json.dumps(relation_counts(projected)))

    if not args.write:
        print("dry-run: no files written")
        return 0

    if BACKUP_PATH.exists():
        raise FileExistsError(
            f"backup already exists; refusing to overwrite it: {BACKUP_PATH}"
        )
    shutil.copy2(EDGES_PATH, BACKUP_PATH)
    write_jsonl_atomic(EDGES_PATH, projected)

    written = read_jsonl(EDGES_PATH)
    assert_projected_graph(nodes, edges, written)
    post_write_gate()
    print(f"wrote: {EDGES_PATH}")
    print(f"backup: {BACKUP_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
