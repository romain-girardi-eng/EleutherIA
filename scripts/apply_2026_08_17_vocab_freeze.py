#!/usr/bin/env python3
"""Validate or apply the 2026-08-17 controlled-vocabulary cleanup.

The default is a non-writing dry run.  ``--apply`` changes only the planned
``school`` assignments and their metadata mirrors, creates
``<nodes>.bak-vocab`` once, writes atomically, and is idempotent.  The period
field is never changed.

Examples:
    python3 scripts/apply_2026_08_17_vocab_freeze.py
    python3 scripts/apply_2026_08_17_vocab_freeze.py --nodes /tmp/nodes.jsonl --apply
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import tempfile
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from data_2026_08_17_vocab_freeze import (  # noqa: E402
    APOLOGETIC_MERGE,
    BACKUP_SUFFIX,
    PERIOD_COUNTS,
    SCHEME_VERSION,
    SCHOOL_COUNTS_AFTER,
    SCHOOL_COUNTS_BEFORE,
    SCHOOL_FIXES,
    STAMP_KEY,
)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_NODES = ROOT / "data" / "kg" / "nodes.jsonl"
DEFAULT_EDGES = ROOT / "data" / "kg" / "edges.jsonl"
PERIOD_SCHEME = ROOT / "knowledge graph" / "ontology" / "period_scheme.json"
SCHOOL_SCHEME = ROOT / "knowledge graph" / "ontology" / "school_scheme.json"


class PlanError(RuntimeError):
    """A frozen precondition or post-apply invariant failed."""


@dataclass
class Prepared:
    original_lines: list[str]
    output_lines: list[str]
    node_count: int
    changed_ids: list[str]
    already_applied_ids: list[str]
    school_field_changes: int
    metadata_school_changes: int
    before_school_counts: Counter[str]
    after_school_counts: Counter[str]
    before_off_scheme: dict[str, Counter[str]]
    after_off_scheme: dict[str, Counter[str]]


def node_id(node: dict[str, Any]) -> str:
    value = node.get("node_id") or node.get("id")
    if not isinstance(value, str) or not value:
        raise PlanError("node without a non-empty id/node_id")
    return value


def parse_metadata(node: dict[str, Any], identifier: str) -> tuple[dict[str, Any], str]:
    raw = node.get("metadata")
    if isinstance(raw, dict):
        return dict(raw), "dict"
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise PlanError(f"{identifier}: invalid JSON metadata: {exc}") from exc
        if not isinstance(parsed, dict):
            raise PlanError(
                f"{identifier}: metadata string does not decode to an object"
            )
        return parsed, "str"
    if raw is None:
        return {}, "none"
    raise PlanError(f"{identifier}: metadata must be an object, string, or null")


def install_metadata(
    node: dict[str, Any], metadata: dict[str, Any], representation: str
) -> None:
    if representation == "dict":
        node["metadata"] = metadata
    elif representation == "str":
        node["metadata"] = json.dumps(
            metadata, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        )
    elif representation == "none":
        node["metadata"] = metadata
    else:
        raise AssertionError(representation)


def read_nodes(
    path: Path,
) -> tuple[list[str], list[dict[str, Any]], dict[str, int]]:
    try:
        with path.open("r", encoding="utf-8", newline="") as handle:
            lines = handle.readlines()
    except OSError as exc:
        raise PlanError(f"cannot read {path}: {exc}") from exc

    nodes: list[dict[str, Any]] = []
    index: dict[str, int] = {}
    for line_number, line in enumerate(lines, 1):
        try:
            node = json.loads(line)
        except json.JSONDecodeError as exc:
            raise PlanError(f"{path}:{line_number}: invalid JSON: {exc}") from exc
        if not isinstance(node, dict):
            raise PlanError(f"{path}:{line_number}: node is not an object")
        identifier = node_id(node)
        if identifier in index:
            raise PlanError(f"duplicate node id: {identifier}")
        index[identifier] = len(nodes)
        nodes.append(node)
    return lines, nodes, index


def read_edge_triples(path: Path) -> set[tuple[str, str, str]]:
    triples: set[tuple[str, str, str]] = set()
    try:
        handle = path.open("r", encoding="utf-8")
    except OSError as exc:
        raise PlanError(f"cannot read {path}: {exc}") from exc
    with handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                edge = json.loads(line)
            except json.JSONDecodeError as exc:
                raise PlanError(f"{path}:{line_number}: invalid JSON: {exc}") from exc
            triples.add(
                (
                    str(edge.get("source", "")),
                    str(edge.get("relation", "")),
                    str(edge.get("target", "")),
                )
            )
    return triples


def load_scheme(path: Path, expected_id: str) -> tuple[dict[str, Any], set[str]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PlanError(f"cannot load scheme {path}: {exc}") from exc
    scheme = payload.get("scheme")
    concepts = payload.get("concepts")
    if not isinstance(scheme, dict) or scheme.get("id") != expected_id:
        raise PlanError(f"{path}: expected scheme.id={expected_id!r}")
    if scheme.get("version") != SCHEME_VERSION:
        raise PlanError(
            f"{path}: expected version {SCHEME_VERSION}, found {scheme.get('version')!r}"
        )
    if not isinstance(concepts, list) or not concepts:
        raise PlanError(f"{path}: concepts must be a non-empty list")
    labels: list[str] = []
    ids: list[str] = []
    for concept in concepts:
        if not isinstance(concept, dict):
            raise PlanError(f"{path}: concept is not an object")
        identifier = concept.get("id")
        label = concept.get("prefLabel")
        definition = concept.get("definition")
        if not all(
            isinstance(value, str) and value.strip() for value in (identifier, label)
        ):
            raise PlanError(f"{path}: every concept needs non-empty id and prefLabel")
        if not isinstance(definition, str) or not definition.strip():
            raise PlanError(f"{path}: {identifier} has no English definition")
        if "\n\n" in definition:
            raise PlanError(f"{path}: {identifier} definition is not one paragraph")
        ids.append(identifier)
        labels.append(label)
    if len(ids) != len(set(ids)) or len(labels) != len(set(labels)):
        raise PlanError(f"{path}: duplicate concept id or prefLabel")
    return payload, set(labels)


def school_counts(nodes: list[dict[str, Any]]) -> Counter[str]:
    return Counter(
        value
        for node in nodes
        if isinstance((value := node.get("school")), str) and value
    )


def period_counts(nodes: list[dict[str, Any]]) -> Counter[str]:
    return Counter(
        value
        for node in nodes
        if isinstance((value := node.get("period")), str) and value
    )


def off_scheme_counts(
    nodes: list[dict[str, Any]], period_values: set[str], school_values: set[str]
) -> dict[str, Counter[str]]:
    result = {"period": Counter(), "school": Counter()}
    for node in nodes:
        period = node.get("period")
        school = node.get("school")
        if period not in (None, "") and period not in period_values:
            result["period"][repr(period)] += 1
        if school not in (None, "") and school not in school_values:
            result["school"][repr(school)] += 1
    return result


def ids_digest(identifiers: list[str]) -> str:
    payload = "\n".join(sorted(identifiers)) + "\n"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def stamp_for(source: str, target: str, evidence_ref: str) -> dict[str, str]:
    return {
        "version": SCHEME_VERSION,
        "field": "school",
        "from": source,
        "to": target,
        "evidence": evidence_ref,
    }


def add_alternatives(metadata: dict[str, Any], alternatives: list[str]) -> None:
    existing = metadata.get("school_alternative_labels", [])
    if existing is None:
        existing = []
    if not isinstance(existing, list) or not all(
        isinstance(value, str) for value in existing
    ):
        raise PlanError("school_alternative_labels must be a list of strings")
    metadata["school_alternative_labels"] = list(
        dict.fromkeys([*existing, *alternatives])
    )


def validate_stamp(
    metadata: dict[str, Any], expected: dict[str, str], identifier: str
) -> None:
    actual = metadata.get(STAMP_KEY)
    if actual != expected:
        raise PlanError(
            f"{identifier}: canonical school value lacks the expected idempotence stamp"
        )


def validate_alternatives(
    metadata: dict[str, Any], expected: list[str], identifier: str
) -> None:
    actual = metadata.get("school_alternative_labels")
    if not isinstance(actual, list) or not set(expected).issubset(actual):
        raise PlanError(f"{identifier}: planned school alternatives are incomplete")


def apply_change(
    node: dict[str, Any],
    source: str,
    target: str,
    alternatives: list[str],
    evidence_ref: str,
) -> tuple[bool, bool]:
    identifier = node_id(node)
    metadata, representation = parse_metadata(node, identifier)
    school_changed = node.get("school") != target
    metadata_school_changed = metadata.get("school") != target
    node["school"] = target
    metadata["school"] = target
    add_alternatives(metadata, alternatives)
    metadata[STAMP_KEY] = stamp_for(source, target, evidence_ref)
    install_metadata(node, metadata, representation)
    return school_changed, metadata_school_changed


def validate_apologetic_scope(nodes: list[dict[str, Any]], indices: list[int]) -> None:
    spec = APOLOGETIC_MERGE
    identifiers = [node_id(nodes[index]) for index in indices]
    if len(indices) != spec["expected_count"]:
        raise PlanError(
            f"Apologetic scope: expected {spec['expected_count']} nodes, found {len(indices)}"
        )
    digest = ids_digest(identifiers)
    if digest != spec["expected_ids_sha256"]:
        raise PlanError(
            "Apologetic scope: sorted-ID digest changed; refusing a broadened or "
            f"narrowed merge ({digest})"
        )

    authors: Counter[str] = Counter()
    works: Counter[str] = Counter()
    for index in indices:
        node = nodes[index]
        identifier = node_id(node)
        metadata, _ = parse_metadata(node, identifier)
        if node.get("type") != spec["expected_type"]:
            raise PlanError(f"{identifier}: Apologetic target is not a passage")
        if node.get("period") != spec["expected_period"]:
            raise PlanError(f"{identifier}: Apologetic target is not Patristic")
        if metadata.get("school") not in (spec["from"], spec["to"]):
            raise PlanError(
                f"{identifier}: metadata.school is {metadata.get('school')!r}"
            )
        authors[str(metadata.get("author"))] += 1
        works[str(metadata.get("work_title"))] += 1
    if authors != Counter(spec["expected_authors"]):
        raise PlanError(f"Apologetic author precondition failed: {authors}")
    if works != Counter(spec["expected_works"]):
        raise PlanError(f"Apologetic work precondition failed: {works}")


def prepare(nodes_path: Path, edges_path: Path) -> Prepared:
    original_lines, nodes, index = read_nodes(nodes_path)
    edge_triples = read_edge_triples(edges_path)
    _, allowed_periods = load_scheme(PERIOD_SCHEME, "period")
    _, allowed_schools = load_scheme(SCHOOL_SCHEME, "school")

    original_nodes = [json.loads(line) for line in original_lines]
    original_ids = [node_id(node) for node in original_nodes]
    original_periods = [node.get("period") for node in original_nodes]
    before_school_counts = school_counts(nodes)
    before_off_scheme = off_scheme_counts(nodes, allowed_periods, allowed_schools)

    fresh_counts = Counter(SCHOOL_COUNTS_BEFORE)
    applied_counts = Counter(SCHOOL_COUNTS_AFTER)
    if before_school_counts not in (fresh_counts, applied_counts):
        raise PlanError(
            "school inventory differs from both the frozen pre-cleanup and "
            f"post-cleanup states: {before_school_counts}"
        )
    if period_counts(nodes) != Counter(PERIOD_COUNTS):
        raise PlanError("period inventory drifted from the frozen 2026-08-17 census")

    changed_ids: list[str] = []
    already_applied_ids: list[str] = []
    school_field_changes = 0
    metadata_school_changes = 0

    # Bulk lexical merge: source population on a fresh run, stamped population
    # on an idempotent rerun.  Any mixture is an unsafe partial application.
    spec = APOLOGETIC_MERGE
    source_indices = [
        idx for idx, node in enumerate(nodes) if node.get("school") == spec["from"]
    ]
    stamped_indices: list[int] = []
    expected_stamp = stamp_for(spec["from"], spec["to"], "APOLOGETIC_MERGE")
    for idx, node in enumerate(nodes):
        metadata, _ = parse_metadata(node, node_id(node))
        if metadata.get(STAMP_KEY) == expected_stamp:
            stamped_indices.append(idx)

    if source_indices and stamped_indices:
        raise PlanError("Apologetic merge is partially applied")
    if source_indices:
        validate_apologetic_scope(nodes, source_indices)
        for idx in source_indices:
            node = nodes[idx]
            changed, metadata_changed = apply_change(
                node,
                spec["from"],
                spec["to"],
                spec["alternative_labels"],
                "APOLOGETIC_MERGE",
            )
            changed_ids.append(node_id(node))
            school_field_changes += int(changed)
            metadata_school_changes += int(metadata_changed)
    else:
        validate_apologetic_scope(nodes, stamped_indices)
        for idx in stamped_indices:
            node = nodes[idx]
            identifier = node_id(node)
            metadata, _ = parse_metadata(node, identifier)
            if node.get("school") != spec["to"] or metadata.get("school") != spec["to"]:
                raise PlanError(
                    f"{identifier}: stamped Apologetic merge is inconsistent"
                )
            validate_stamp(metadata, expected_stamp, identifier)
            validate_alternatives(metadata, spec["alternative_labels"], identifier)
            already_applied_ids.append(identifier)

    # Node-specific rare values.
    for fix in SCHOOL_FIXES:
        identifier = fix["node_id"]
        if identifier not in index:
            raise PlanError(f"planned node missing: {identifier}")
        node = nodes[index[identifier]]
        metadata, _ = parse_metadata(node, identifier)
        expected = stamp_for(fix["from"], fix["to"], f"SCHOOL_FIXES:{identifier}")

        if node.get("school") == fix["to"]:
            if metadata.get("school") != fix["to"]:
                raise PlanError(
                    f"{identifier}: canonical top-level school but stale metadata"
                )
            validate_stamp(metadata, expected, identifier)
            validate_alternatives(metadata, fix["alternative_labels"], identifier)
            already_applied_ids.append(identifier)
            continue
        if node.get("school") != fix["from"]:
            raise PlanError(
                f"{identifier}: expected school {fix['from']!r}, found {node.get('school')!r}"
            )
        if metadata.get("school") != fix["expected_metadata_school"]:
            raise PlanError(
                f"{identifier}: expected metadata.school "
                f"{fix['expected_metadata_school']!r}, found {metadata.get('school')!r}"
            )
        if node.get("type") != fix["expected_type"]:
            raise PlanError(f"{identifier}: type precondition failed")
        if node.get("period") != fix["expected_period"]:
            raise PlanError(f"{identifier}: period precondition failed")
        if fix["description_contains"] not in str(node.get("description", "")):
            raise PlanError(f"{identifier}: description evidence precondition failed")
        for source, relation, target in fix["required_edges"]:
            if (source, relation, target) not in edge_triples:
                raise PlanError(
                    f"{identifier}: required evidence edge missing: "
                    f"{source} -[{relation}]-> {target}"
                )

        changed, metadata_changed = apply_change(
            node,
            fix["from"],
            fix["to"],
            fix["alternative_labels"],
            f"SCHOOL_FIXES:{identifier}",
        )
        changed_ids.append(identifier)
        school_field_changes += int(changed)
        metadata_school_changes += int(metadata_changed)

    output_lines = list(original_lines)
    changed_set = set(changed_ids)
    for idx, node in enumerate(nodes):
        identifier = node_id(node)
        if identifier in changed_set:
            output_lines[idx] = (
                json.dumps(node, ensure_ascii=False, sort_keys=True) + "\n"
            )

    # Structural and no-period-migration invariants.
    output_nodes = [json.loads(line) for line in output_lines]
    output_ids = [node_id(node) for node in output_nodes]
    if len(output_nodes) != len(original_nodes):
        raise PlanError("node count changed")
    if output_ids != original_ids:
        raise PlanError("node order or identifiers changed")
    if [node.get("period") for node in output_nodes] != original_periods:
        raise PlanError("period changed; this wave forbids every period migration")

    for idx, (before, after) in enumerate(
        zip(original_nodes, output_nodes, strict=True)
    ):
        identifier = original_ids[idx]
        if identifier not in changed_set:
            if output_lines[idx] != original_lines[idx]:
                raise PlanError(f"non-target line changed: {identifier}")
            continue
        before_copy = dict(before)
        after_copy = dict(after)
        before_copy.pop("school", None)
        after_copy.pop("school", None)
        before_metadata, before_rep = parse_metadata(before, identifier)
        after_metadata, after_rep = parse_metadata(after, identifier)
        before_copy.pop("metadata", None)
        after_copy.pop("metadata", None)
        if before_copy != after_copy:
            raise PlanError(f"non-school node content changed: {identifier}")
        if before_rep != after_rep:
            raise PlanError(f"metadata representation changed: {identifier}")
        allowed_metadata_changes = {
            "school",
            "school_alternative_labels",
            STAMP_KEY,
        }
        before_rest = {
            key: value
            for key, value in before_metadata.items()
            if key not in allowed_metadata_changes
        }
        after_rest = {
            key: value
            for key, value in after_metadata.items()
            if key not in allowed_metadata_changes
        }
        if before_rest != after_rest:
            raise PlanError(f"unplanned metadata changed: {identifier}")

    after_school_counts = school_counts(output_nodes)
    if after_school_counts != applied_counts:
        raise PlanError(f"projected school inventory mismatch: {after_school_counts}")
    if period_counts(output_nodes) != Counter(PERIOD_COUNTS):
        raise PlanError("period inventory changed during simulation")
    after_off_scheme = off_scheme_counts(output_nodes, allowed_periods, allowed_schools)
    if after_off_scheme["period"] or after_off_scheme["school"]:
        raise PlanError(
            f"off-scheme values remain after simulation: {after_off_scheme}"
        )

    planned_ids = {fix["node_id"] for fix in SCHOOL_FIXES}
    planned_ids.update(
        node_id(nodes[idx]) for idx in (source_indices or stamped_indices)
    )
    if len(planned_ids) != 940:
        raise PlanError(f"expected 940 planned node ids, found {len(planned_ids)}")
    if len(changed_ids) + len(already_applied_ids) != 940:
        raise PlanError("fresh plus already-applied scope does not total 940 nodes")

    return Prepared(
        original_lines=original_lines,
        output_lines=output_lines,
        node_count=len(nodes),
        changed_ids=changed_ids,
        already_applied_ids=already_applied_ids,
        school_field_changes=school_field_changes,
        metadata_school_changes=metadata_school_changes,
        before_school_counts=before_school_counts,
        after_school_counts=after_school_counts,
        before_off_scheme=before_off_scheme,
        after_off_scheme=after_off_scheme,
    )


def atomic_write(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            handle.writelines(lines)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def format_off_scheme(values: dict[str, Counter[str]]) -> str:
    parts: list[str] = []
    for field in ("period", "school"):
        for value, count in values[field].most_common():
            parts.append(f"{field}={value} ({count})")
    return ", ".join(parts) if parts else "none"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--nodes", type=Path, default=DEFAULT_NODES)
    parser.add_argument("--edges", type=Path, default=DEFAULT_EDGES)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="write the selected --nodes file (default: dry-run only)",
    )
    args = parser.parse_args()

    try:
        prepared = prepare(args.nodes, args.edges)
    except PlanError as exc:
        print(f"vocab-freeze: ERROR: {exc}", file=sys.stderr)
        return 1

    print(f"vocab-freeze: {args.nodes}")
    print(f"mode: {'APPLY' if args.apply else 'DRY-RUN'}")
    print(f"nodes: {prepared.node_count} -> {prepared.node_count}")
    print(
        f"planned nodes: {len(prepared.changed_ids) + len(prepared.already_applied_ids)}"
    )
    print(f"school assignments changed: {prepared.school_field_changes}")
    print(f"metadata.school values changed: {prepared.metadata_school_changes}")
    print(f"already applied: {len(prepared.already_applied_ids)}")
    print("period assignments changed: 0")
    print(
        f"school values: {len(prepared.before_school_counts)} -> {len(prepared.after_school_counts)}"
    )
    print(f"off-scheme before: {format_off_scheme(prepared.before_off_scheme)}")
    print(f"off-scheme after: {format_off_scheme(prepared.after_off_scheme)}")
    print("invariants: OK")

    if not args.apply:
        print("--dry-run: nothing written")
        return 0

    backup = args.nodes.with_suffix(args.nodes.suffix + BACKUP_SUFFIX)
    if not backup.exists():
        shutil.copy2(args.nodes, backup)
        print(f"backup: {backup}")
    else:
        print(f"backup: {backup} (kept existing)")
    atomic_write(args.nodes, prepared.output_lines)
    print(f"wrote: {args.nodes}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
