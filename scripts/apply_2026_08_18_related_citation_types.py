#!/usr/bin/env python3
"""Retype non-exact KG/corpus links without changing either text collection.

The 2026-08-18 parity adjudication demoted 289 former passage twins to
``metadata.parity_status=related_not_exact_twin``.  Their one-to-one corpus
links are useful for discovery, but they must not retain the exact-twin
``snapshot_passage_node`` citation type.

Dry-run is the default.  Pass ``--write`` to replace only
``data/corpus/citations.jsonl`` after all exact snapshot and corpus-integrity
checks pass.  Unchanged JSONL lines are retained byte-for-byte.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.check_corpus_invariants import find_violations  # noqa: E402

SOURCE_TYPE = "snapshot_passage_node"
TARGET_TYPE = "related_passage_non_exact"
PARITY_STATUS = "related_not_exact_twin"
EXPECTED_RELATED_NODES = 289
BACKUP_SUFFIX = ".bak-related_citation_types_2026_08_18"

# Exact coordinated-final snapshot audited on 2026-08-18.  The citation hash
# admits only the unapplied or fully applied state; mixed states are blocked.
EXPECTED_NODES_SHA256 = (
    "bdf75f26ddf27dca289b1a54b6b7007ea913c01d88ba43f49dd6129a47aff0b7"
)
EXPECTED_PASSAGES_SHA256 = (
    "7a0a484d1146206fbd8d3dfe4b9b2b21fa31a0649c870461a53c52c2961d71d2"
)
EXPECTED_CITATIONS_BEFORE_SHA256 = (
    "b98a37e7eaa9240f81161f858c1d088c1e9bab0fdf7ee08545e4d90ac4c3ede0"
)
EXPECTED_CITATIONS_AFTER_SHA256 = (
    "d3d74079b280c2038495e9e396dee8339331b9b764432c1669ef1e132e3d1293"
)
EXPECTED_NODE_IDS_SHA256 = (
    "5a669883a8c178d2fbfd0e5169424de59b685f41d36f2f4996a591201e9e5bda"
)
EXPECTED_PLAN_SHA256 = (
    "10d73492dcedcd80541d7e7dbc81c1e7061f8b4e79ae89c10fb35646b5d2bfde"
)
EXPECTED_SOURCE_ROWS_SHA256 = (
    "74ba53b646e08b09978b8faf9e9e02feda51c65a6cd8450bb40e078d53dd8922"
)
EXPECTED_TARGET_ROWS_SHA256 = (
    "ac377991b0fd2066db62b648aad423e225cc815216e9f66d0dafb7ff249f5ac4"
)


class ApplyBlocked(RuntimeError):
    """Raised when the audited snapshot or one-to-one mapping has drifted."""


@dataclass(frozen=True, slots=True)
class CitationChange:
    """One exact citation row whose type must change."""

    line_index: int
    node_id: str
    passage_id: str


@dataclass(frozen=True, slots=True)
class RetypePlan:
    """Validated all-source or all-target migration state."""

    state: str
    changes: tuple[CitationChange, ...]
    node_ids_sha256: str
    plan_sha256: str
    rows_sha256: str


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_path(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    )


def metadata(node: dict[str, Any]) -> dict[str, Any]:
    raw = node.get("metadata") or {}
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            decoded = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ApplyBlocked("invalid stringified KG metadata") from exc
        if isinstance(decoded, dict):
            return decoded
    raise ApplyBlocked("KG metadata is not an object")


def node_id(node: dict[str, Any]) -> str:
    return str(node.get("id") or node.get("node_id") or "")


def parse_jsonl_bytes(payload: bytes, *, label: str) -> tuple[list[bytes], list[dict]]:
    lines = payload.splitlines(keepends=True)
    rows: list[dict] = []
    for index, line in enumerate(lines):
        if not line.strip():
            raise ApplyBlocked(f"{label}: blank JSONL line at {index + 1}")
        try:
            row = json.loads(line.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ApplyBlocked(f"{label}: invalid JSONL line at {index + 1}") from exc
        if not isinstance(row, dict):
            raise ApplyBlocked(f"{label}: non-object JSONL line at {index + 1}")
        rows.append(row)
    return lines, rows


def read_jsonl(path: Path) -> tuple[list[bytes], list[dict]]:
    return parse_jsonl_bytes(path.read_bytes(), label=str(path))


def _digest_lines(lines: list[str]) -> str:
    return sha256_bytes(("\n".join(lines) + "\n").encode("utf-8"))


def _related_nodes(nodes: list[dict]) -> dict[str, str]:
    related: dict[str, str] = {}
    for node in nodes:
        data = metadata(node)
        if data.get("parity_status") != PARITY_STATUS:
            continue
        current_id = node_id(node)
        if not current_id or current_id in related:
            raise ApplyBlocked("related passage cohort has a missing/duplicate node id")
        if str(node.get("type") or "").strip().lower() != "passage":
            raise ApplyBlocked(f"{current_id}: related cohort member is not a passage")
        passage_id = str(data.get("related_corpus_passage_id") or "")
        if not passage_id:
            raise ApplyBlocked(f"{current_id}: related corpus passage id is missing")
        if data.get("db_passage_id"):
            raise ApplyBlocked(f"{current_id}: demoted node still claims an exact twin")
        legacy_passage_id = str(data.get("passage_id") or "")
        if legacy_passage_id and legacy_passage_id != passage_id:
            raise ApplyBlocked(
                f"{current_id}: legacy passage_id disagrees with related passage"
            )
        related[current_id] = passage_id
    return related


def build_plan(
    nodes: list[dict],
    citations: list[dict],
    *,
    expected_count: int = EXPECTED_RELATED_NODES,
    expected_node_ids_sha256: str | None = EXPECTED_NODE_IDS_SHA256,
    expected_plan_sha256: str | None = EXPECTED_PLAN_SHA256,
    expected_source_rows_sha256: str | None = EXPECTED_SOURCE_ROWS_SHA256,
    expected_target_rows_sha256: str | None = EXPECTED_TARGET_ROWS_SHA256,
) -> RetypePlan:
    """Validate and return the complete, never-partial citation retype plan."""

    related = _related_nodes(nodes)
    if len(related) != expected_count:
        raise ApplyBlocked(
            f"related passage cohort has {len(related)} nodes; expected {expected_count}"
        )

    ids_digest = _digest_lines(sorted(related))
    if expected_node_ids_sha256 and ids_digest != expected_node_ids_sha256:
        raise ApplyBlocked(f"related node-id cohort drift: {ids_digest}")

    rows_by_node: dict[str, list[tuple[int, dict]]] = defaultdict(list)
    for index, citation in enumerate(citations):
        cited_node = str(citation.get("kg_node_id") or "")
        if cited_node in related:
            rows_by_node[cited_node].append((index, citation))
        elif citation.get("citation_type") == TARGET_TYPE:
            raise ApplyBlocked(
                f"{cited_node}: {TARGET_TYPE} appears outside the audited cohort"
            )

    changes: list[CitationChange] = []
    source_rows = 0
    target_rows = 0
    cohort_rows: list[dict] = []
    plan_lines: list[str] = []
    for current_id in sorted(related):
        matches = rows_by_node.get(current_id, [])
        if len(matches) != 1:
            raise ApplyBlocked(
                f"{current_id}: expected exactly one citation row, found {len(matches)}"
            )
        line_index, citation = matches[0]
        related_passage_id = related[current_id]
        cited_passage_id = str(citation.get("passage_id") or "")
        if cited_passage_id != related_passage_id:
            raise ApplyBlocked(
                f"{current_id}: citation does not match related_corpus_passage_id"
            )
        citation_type = citation.get("citation_type")
        if citation_type == SOURCE_TYPE:
            source_rows += 1
        elif citation_type == TARGET_TYPE:
            target_rows += 1
        else:
            raise ApplyBlocked(
                f"{current_id}: unexpected citation_type={citation_type!r}"
            )
        cohort_rows.append(citation)
        changes.append(CitationChange(line_index, current_id, cited_passage_id))
        plan_lines.append(
            f"{current_id}\t{cited_passage_id}\t{SOURCE_TYPE}\t{TARGET_TYPE}"
        )

    if source_rows == expected_count and target_rows == 0:
        state = "baseline"
    elif target_rows == expected_count and source_rows == 0:
        state = "applied"
    else:
        raise ApplyBlocked(
            f"partial citation state: source={source_rows}, target={target_rows}"
        )

    plan_digest = _digest_lines(plan_lines)
    if expected_plan_sha256 and plan_digest != expected_plan_sha256:
        raise ApplyBlocked(f"citation plan drift: {plan_digest}")

    cohort_rows.sort(
        key=lambda row: (
            str(row.get("kg_node_id") or ""),
            str(row.get("passage_id") or ""),
            str(row.get("citation_type") or ""),
        )
    )
    rows_digest = _digest_lines([canonical_json(row) for row in cohort_rows])
    expected_rows_digest = (
        expected_source_rows_sha256
        if state == "baseline"
        else expected_target_rows_sha256
    )
    if expected_rows_digest and rows_digest != expected_rows_digest:
        raise ApplyBlocked(f"exact cohort-row drift: {rows_digest}")

    return RetypePlan(
        state=state,
        changes=tuple(changes),
        node_ids_sha256=ids_digest,
        plan_sha256=plan_digest,
        rows_sha256=rows_digest,
    )


def render_citations(
    raw_lines: list[bytes],
    citations: list[dict],
    plan: RetypePlan,
) -> bytes:
    """Replace only the JSON string value on audited source-state lines."""

    if len(raw_lines) != len(citations):
        raise ApplyBlocked("citation raw/parsed row count drift")
    output = list(raw_lines)
    source_token = json.dumps(SOURCE_TYPE).encode("utf-8")
    target_token = json.dumps(TARGET_TYPE).encode("utf-8")
    target_indices = {change.line_index for change in plan.changes}

    for change in plan.changes:
        raw = raw_lines[change.line_index]
        row = citations[change.line_index]
        if row.get("citation_type") == TARGET_TYPE:
            continue
        if raw.count(source_token) != 1:
            raise ApplyBlocked(
                f"{change.node_id}: exact source type token not found once"
            )
        output[change.line_index] = raw.replace(source_token, target_token, 1)

    rendered = b"".join(output)
    rendered_lines, rendered_rows = parse_jsonl_bytes(
        rendered, label="rendered citations"
    )
    if len(rendered_rows) != len(citations):
        raise ApplyBlocked("rendered citation row count changed")
    for index, (old, new) in enumerate(zip(citations, rendered_rows, strict=True)):
        if index not in target_indices:
            if rendered_lines[index] != raw_lines[index]:
                raise ApplyBlocked(f"untargeted citation line {index + 1} changed")
            continue
        expected = dict(old)
        expected["citation_type"] = TARGET_TYPE
        if new != expected:
            raise ApplyBlocked(f"target citation line {index + 1} changed beyond type")
    return rendered


def invariant_counts(violations: dict[str, list[dict]]) -> dict[str, int]:
    return {key: len(rows) for key, rows in violations.items()}


def validate_corpus_invariants(
    passages: list[dict], citations: list[dict], nodes: list[dict]
) -> dict[str, int]:
    node_ids = {node_id(node) for node in nodes}
    violations = find_violations(passages, citations, node_ids)
    counts = invariant_counts(violations)
    if any(counts.values()):
        raise ApplyBlocked(f"corpus invariant violations: {counts}")
    return counts


def atomic_write(path: Path, payload: bytes) -> None:
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_bytes(payload)
    os.replace(temporary, path)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    parser.add_argument(
        "--data-root",
        type=Path,
        default=ROOT / "data",
        help="directory containing kg/ and corpus/",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    data_root = args.data_root.expanduser().resolve()
    nodes_path = data_root / "kg" / "nodes.jsonl"
    passages_path = data_root / "corpus" / "passages.jsonl"
    citations_path = data_root / "corpus" / "citations.jsonl"

    nodes_hash = sha256_path(nodes_path)
    passages_hash = sha256_path(passages_path)
    citations_hash = sha256_path(citations_path)
    if nodes_hash != EXPECTED_NODES_SHA256:
        raise ApplyBlocked(f"KG node snapshot drift: {nodes_hash}")
    if passages_hash != EXPECTED_PASSAGES_SHA256:
        raise ApplyBlocked(f"corpus passage snapshot drift: {passages_hash}")
    if citations_hash not in {
        EXPECTED_CITATIONS_BEFORE_SHA256,
        EXPECTED_CITATIONS_AFTER_SHA256,
    }:
        raise ApplyBlocked(f"corpus citation snapshot drift: {citations_hash}")

    _node_lines, nodes = read_jsonl(nodes_path)
    _passage_lines, passages = read_jsonl(passages_path)
    citation_lines, citations = read_jsonl(citations_path)
    before_invariants = validate_corpus_invariants(passages, citations, nodes)
    plan = build_plan(nodes, citations)

    hash_state = (
        "baseline" if citations_hash == EXPECTED_CITATIONS_BEFORE_SHA256 else "applied"
    )
    if plan.state != hash_state:
        raise ApplyBlocked(
            f"citation hash says {hash_state}, cohort rows say {plan.state}"
        )

    output = render_citations(citation_lines, citations, plan)
    output_hash = sha256_bytes(output)
    if output_hash != EXPECTED_CITATIONS_AFTER_SHA256:
        raise ApplyBlocked(f"deterministic citation output drift: {output_hash}")
    _output_lines, output_rows = parse_jsonl_bytes(output, label="output citations")
    after_invariants = validate_corpus_invariants(passages, output_rows, nodes)
    if after_invariants != before_invariants:
        raise ApplyBlocked("corpus invariant result changed after citation retype")

    second_plan = build_plan(nodes, output_rows)
    second_output = render_citations(_output_lines, output_rows, second_plan)
    if second_plan.state != "applied" or second_output != output:
        raise ApplyBlocked("second in-memory pass is not an exact no-op")

    print(f"mode: {'write' if args.write else 'dry-run'}")
    print(f"source state: {plan.state}")
    print(f"plan: related_nodes={len(plan.changes)}, {SOURCE_TYPE} -> {TARGET_TYPE}")
    print(f"plan_sha256: {plan.plan_sha256}")
    print(f"node_ids_sha256: {plan.node_ids_sha256}")
    print(
        "corpus invariants: OK "
        f"({', '.join(f'{key}={value}' for key, value in after_invariants.items())})"
    )
    print(
        "scope: citations rows/cardinality/order preserved; "
        "KG nodes and corpus passages read-only"
    )
    print(f"output_sha256: {output_hash}")
    print("idempotency: second pass changed 0 bytes")

    if plan.state == "applied":
        print("write: no-op (verified fully applied state)")
        return 0
    if not args.write:
        print("write: disabled (dry-run default; use --write to apply)")
        return 0

    backup_path = citations_path.with_name(citations_path.name + BACKUP_SUFFIX)
    if backup_path.exists():
        raise ApplyBlocked(f"backup already exists: {backup_path}")
    if (
        sha256_path(nodes_path) != nodes_hash
        or sha256_path(passages_path) != passages_hash
    ):
        raise ApplyBlocked("read-only KG/corpus files changed during validation")
    if sha256_path(citations_path) != citations_hash:
        raise ApplyBlocked("citation file changed during validation")

    shutil.copy2(citations_path, backup_path)
    try:
        atomic_write(citations_path, output)
        if sha256_path(citations_path) != output_hash:
            raise ApplyBlocked("written citation hash differs from verified output")
        if sha256_path(nodes_path) != nodes_hash:
            raise ApplyBlocked("KG nodes changed during citation write")
        if sha256_path(passages_path) != passages_hash:
            raise ApplyBlocked("corpus passages changed during citation write")
    except Exception:
        atomic_write(citations_path, backup_path.read_bytes())
        raise

    print(f"wrote: {citations_path}")
    print(f"backup: {backup_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
