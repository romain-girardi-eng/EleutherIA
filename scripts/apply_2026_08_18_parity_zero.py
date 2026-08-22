#!/usr/bin/env python3
"""Reconcile or honestly demote every decidable residual parity mismatch.

Dry-run is the default.  ``--write`` is required to replace data files.  The
six Plutarch ``tlg135``/``tlg138`` rows are excluded because their source-level
adjudication is owned by a separate repair.

This script never changes KG descriptions, corpus ``text_content``, citations,
row order, or row cardinality.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import shutil
import sys
from collections import Counter
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from check_kg_corpus_locus_parity import find_violations  # noqa: E402
from data_2026_08_18_parity_zero import (  # noqa: E402
    APPLIED_NODES_SHA256,
    APPLIED_PASSAGES_SHA256,
    BACKUP_SUFFIX,
    BASELINE_FILE_SHA256,
    DEMOTE,
    EXCLUDED_PLUTARCH_NODE_IDS,
    EXPECTED_ACTION_NODES,
    EXPECTED_AFTER,
    EXPECTED_BEFORE,
    EXPECTED_FIELD_CHANGES,
    EXPECTED_FINAL,
    EXPECTED_FIXED_VIOLATIONS,
    EXPECTED_PLAN_SHA256,
    EXPECTED_REPAIR_NODES,
    FINAL_CITATIONS_SHA256,
    FINAL_NODES_SHA256,
    FINAL_PASSAGES_SHA256,
    ROOT,
    STAMP,
    PlanError,
    RepairRecord,
    build_repair_records,
    canonical_json,
    metadata,
    node_id,
    read_jsonl,
    record_digest,
    sha256_path,
    sha256_text,
)

DEFAULT_DATA_ROOT = ROOT / "data"


class ApplyBlocked(RuntimeError):
    """Raised when a precondition or postcondition no longer holds."""


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def render_jsonl_preserving_unchanged(
    path: Path,
    before: list[dict[str, Any]],
    after: list[dict[str, Any]],
    *,
    compact: bool,
) -> bytes:
    """Render changed rows only; return every unchanged source line verbatim."""

    raw_lines = [
        line for line in path.read_bytes().splitlines(keepends=True) if line.strip()
    ]
    if len(raw_lines) != len(before) or len(before) != len(after):
        raise ApplyBlocked(f"{path}: row count drift while rendering")
    parsed = [json.loads(line.decode("utf-8")) for line in raw_lines]
    if parsed != before:
        raise ApplyBlocked(f"{path}: in-memory baseline differs from raw JSONL")

    rendered: list[bytes] = []
    for old, new, raw in zip(before, after, raw_lines, strict=True):
        if new == old:
            rendered.append(raw)
            continue
        kwargs: dict[str, Any] = {"ensure_ascii": False}
        if compact:
            kwargs["separators"] = (",", ":")
        rendered.append((json.dumps(new, **kwargs) + "\n").encode("utf-8"))
    return b"".join(rendered)


def atomic_write(path: Path, payload: bytes) -> None:
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_bytes(payload)
    os.replace(temporary, path)


def _set_metadata(node: dict[str, Any], value: dict[str, Any]) -> None:
    if isinstance(node.get("metadata"), str):
        node["metadata"] = json.dumps(value, ensure_ascii=False)
    else:
        node["metadata"] = value


def parity_summary(shared: int, violations: list[dict[str, Any]]) -> dict[str, int]:
    reasons = Counter(row["reason"] for row in violations)
    fields = Counter(row["field"] for row in violations)
    missing_twins = reasons["missing_corpus_twin"]
    return {
        "declared_twins": shared + missing_twins,
        "shared_twins": shared,
        "violations": len(violations),
        "missing_twins": missing_twins,
        "missing_citations": reasons["missing_twin_citation"],
        "canonical_ref_mismatches": fields["canonical_ref"],
        "cts_urn_mismatches": fields["cts_urn"],
    }


def compute_parity(
    nodes: list[dict[str, Any]],
    passages: list[dict[str, Any]],
    citations: list[dict[str, Any]],
) -> tuple[dict[str, int], list[dict[str, Any]]]:
    shared, violations = find_violations(nodes, passages, citations)
    return parity_summary(shared, violations), violations


def _violation_keys(
    violations: list[dict[str, Any]],
) -> set[tuple[str, str, str, str]]:
    return {
        (
            str(row.get("node_id") or ""),
            str(row.get("passage_id") or ""),
            str(row.get("field") or ""),
            str(row.get("reason") or ""),
        )
        for row in violations
    }


def text_digest(nodes: list[dict[str, Any]], passages: list[dict[str, Any]]) -> str:
    digest = hashlib.sha256()
    for node in nodes:
        digest.update(node_id(node).encode("utf-8"))
        digest.update(b"\0")
        digest.update(str(node.get("description") or "").encode("utf-8"))
        digest.update(b"\0")
    for passage in passages:
        digest.update(str(passage.get("passage_id") or "").encode("utf-8"))
        digest.update(b"\0")
        digest.update(str(passage.get("text_content") or "").encode("utf-8"))
        digest.update(b"\0")
    return digest.hexdigest()


def validate_source_hashes(data_root: Path) -> str:
    nodes_hash = sha256_path(data_root / "kg" / "nodes.jsonl")
    passages_hash = sha256_path(data_root / "corpus" / "passages.jsonl")
    citations_hash = sha256_path(data_root / "corpus" / "citations.jsonl")
    if citations_hash not in {
        BASELINE_FILE_SHA256["corpus/citations.jsonl"],
        FINAL_CITATIONS_SHA256,
    }:
        raise ApplyBlocked(
            "data/corpus/citations.jsonl is outside the audited snapshot"
        )
    if (
        nodes_hash == BASELINE_FILE_SHA256["kg/nodes.jsonl"]
        and passages_hash == BASELINE_FILE_SHA256["corpus/passages.jsonl"]
    ):
        return "baseline"
    if (
        APPLIED_NODES_SHA256 != "TO_BE_FILLED"
        and APPLIED_PASSAGES_SHA256 != "TO_BE_FILLED"
        and nodes_hash == APPLIED_NODES_SHA256
        and passages_hash == APPLIED_PASSAGES_SHA256
    ):
        return "applied"
    if nodes_hash == FINAL_NODES_SHA256 and passages_hash == FINAL_PASSAGES_SHA256:
        return "final"
    raise ApplyBlocked(
        "KG/corpus files are neither the joint audited baseline nor the joint "
        "applied state (a mixed/partial state must be recovered from backups)"
    )


def _check_record_baseline(
    record: RepairRecord,
    node: dict[str, Any],
    passage: dict[str, Any] | None,
    related_passage: dict[str, Any] | None,
) -> None:
    data = metadata(node)
    if sha256_text(canonical_json(data)) != record.expected_node_metadata_sha256:
        raise ApplyBlocked(f"{record.node_id}: exact KG metadata precondition drift")
    if (
        sha256_text(str(node.get("description") or ""))
        != record.expected_description_sha256
    ):
        raise ApplyBlocked(f"{record.node_id}: ancient node description drift")
    if record.expected_passage_sha256 is None:
        if passage is not None:
            raise ApplyBlocked(f"{record.former_passage_id}: deleted twin reappeared")
    else:
        if passage is None:
            raise ApplyBlocked(f"{record.former_passage_id}: corpus twin disappeared")
        if sha256_text(canonical_json(passage)) != record.expected_passage_sha256:
            raise ApplyBlocked(f"{record.former_passage_id}: exact corpus row drift")
    if record.expected_related_passage_sha256 is not None:
        if related_passage is None:
            raise ApplyBlocked(f"{record.node_id}: related corpus row disappeared")
        if (
            sha256_text(canonical_json(related_passage))
            != record.expected_related_passage_sha256
        ):
            raise ApplyBlocked(f"{record.node_id}: related corpus row drift")


def _check_desired_record(
    record: RepairRecord,
    data: dict[str, Any],
    passage: dict[str, Any] | None,
) -> None:
    if data.get(STAMP) != record.stamp_value:
        raise ApplyBlocked(f"{record.node_id}: parity stamp drift")
    for field, desired in record.node_updates.items():
        if data.get(field) != desired:
            raise ApplyBlocked(
                f"{record.node_id}: {field}={data.get(field)!r}, expected {desired!r}"
            )
    for field in record.node_removals:
        if field in data:
            raise ApplyBlocked(f"{record.node_id}: {field} should be absent")
    if record.passage_updates:
        if passage is None:
            raise ApplyBlocked(f"{record.node_id}: desired corpus row missing")
        if passage.get(STAMP) != record.stamp_value:
            raise ApplyBlocked(f"{record.former_passage_id}: corpus stamp drift")
        for field, desired in record.passage_updates.items():
            if passage.get(field) != desired:
                raise ApplyBlocked(
                    f"{record.former_passage_id}: {field}={passage.get(field)!r}, "
                    f"expected {desired!r}"
                )


def rewrite(
    nodes: list[dict[str, Any]],
    passages: list[dict[str, Any]],
    records: tuple[RepairRecord, ...],
) -> tuple[Counter[str], list[str]]:
    nodes_by_id = {node_id(node): node for node in nodes}
    passages_by_id = {str(row.get("passage_id") or ""): row for row in passages}
    counts: Counter[str] = Counter()
    details: list[str] = []

    for record in records:
        node = nodes_by_id.get(record.node_id)
        if node is None:
            raise ApplyBlocked(f"{record.node_id}: KG node missing")
        passage = passages_by_id.get(record.former_passage_id)
        related_passage = (
            passages_by_id.get(record.related_passage_id)
            if record.related_passage_id is not None
            else None
        )
        data = metadata(node)
        existing_stamp = data.get(STAMP)
        if existing_stamp is not None:
            _check_desired_record(record, data, passage)
            counts["already_applied"] += 1
            continue

        _check_record_baseline(record, node, passage, related_passage)
        for field, desired in record.node_updates.items():
            if data.get(field) != desired:
                data[field] = desired
                counts["node__" + field] += 1
        for field in record.node_removals:
            if field not in data:
                raise ApplyBlocked(f"{record.node_id}: removable {field} absent")
            data.pop(field)
            counts["node__" + field + "__removed"] += 1
        data[STAMP] = record.stamp_value
        _set_metadata(node, data)
        counts["node_rows_changed"] += 1
        counts["action__" + record.action] += 1
        counts["family__" + record.family] += 1

        if record.passage_updates:
            if passage is None:
                raise ApplyBlocked(f"{record.former_passage_id}: corpus row missing")
            if STAMP in passage:
                raise ApplyBlocked(
                    f"{record.former_passage_id}: corpus stamp pre-exists"
                )
            for field, desired in record.passage_updates.items():
                if passage.get(field) != desired:
                    passage[field] = desired
                    counts["corpus__" + field] += 1
            passage[STAMP] = record.stamp_value
            counts["corpus_rows_changed"] += 1

        details.append(f"{record.action}: {record.node_id} ({record.family})")
    return counts, details


def validate_mutation_scope(
    original_nodes: list[dict[str, Any]],
    nodes: list[dict[str, Any]],
    original_passages: list[dict[str, Any]],
    passages: list[dict[str, Any]],
) -> None:
    if len(original_nodes) != len(nodes):
        raise ApplyBlocked("KG node row count changed")
    allowed_node_metadata = {
        "canonical_ref",
        "cts_urn",
        "db_passage_id",
        "related_corpus_passage_id",
        "former_corpus_passage_id",
        "parity_status",
        "parity_reason",
        STAMP,
    }
    for old, new in zip(original_nodes, nodes, strict=True):
        if node_id(old) != node_id(new):
            raise ApplyBlocked("KG node order or id changed")
        old_outer = {key: value for key, value in old.items() if key != "metadata"}
        new_outer = {key: value for key, value in new.items() if key != "metadata"}
        if old_outer != new_outer:
            raise ApplyBlocked(f"{node_id(old)}: non-metadata KG field changed")
        old_data = metadata(old)
        new_data = metadata(new)
        old_rest = {
            key: value
            for key, value in old_data.items()
            if key not in allowed_node_metadata
        }
        new_rest = {
            key: value
            for key, value in new_data.items()
            if key not in allowed_node_metadata
        }
        if old_rest != new_rest:
            raise ApplyBlocked(f"{node_id(old)}: non-parity metadata changed")

    if len(original_passages) != len(passages):
        raise ApplyBlocked("corpus passage row count changed")
    allowed_passage = {"cts_urn", STAMP}
    for old, new in zip(original_passages, passages, strict=True):
        if old.get("passage_id") != new.get("passage_id"):
            raise ApplyBlocked("corpus passage order or id changed")
        old_rest = {
            key: value for key, value in old.items() if key not in allowed_passage
        }
        new_rest = {
            key: value for key, value in new.items() if key not in allowed_passage
        }
        if old_rest != new_rest:
            raise ApplyBlocked(
                f"{old.get('passage_id')}: non-parity corpus field changed"
            )


def validate_counts(counts: Counter[str]) -> None:
    observed_fields = {
        "node_canonical_ref": counts["node__canonical_ref"],
        "node_cts_urn": counts["node__cts_urn"],
        "corpus_cts_urn": counts["corpus__cts_urn"],
        "db_passage_id_removed": counts["node__db_passage_id__removed"],
        "related_corpus_passage_id": counts["node__related_corpus_passage_id"],
        "former_corpus_passage_id": counts["node__former_corpus_passage_id"],
    }
    if observed_fields != EXPECTED_FIELD_CHANGES:
        raise ApplyBlocked(f"field-change count drift: {observed_fields}")
    observed_actions = {
        action: counts["action__" + action] for action in EXPECTED_ACTION_NODES
    }
    if observed_actions != EXPECTED_ACTION_NODES:
        raise ApplyBlocked(f"action count drift: {observed_actions}")
    if counts["node_rows_changed"] != EXPECTED_REPAIR_NODES:
        raise ApplyBlocked("not every repair node was stamped")
    if counts["corpus_rows_changed"] != 172:
        raise ApplyBlocked("Philo corpus row count drift")


def validate_applied_state(
    nodes: list[dict[str, Any]],
    passages: list[dict[str, Any]],
    citations: list[dict[str, Any]],
) -> None:
    summary, violations = compute_parity(nodes, passages, citations)
    if summary != EXPECTED_AFTER:
        raise ApplyBlocked(f"applied parity drift: {summary}")
    if {row["node_id"] for row in violations} != set(EXCLUDED_PLUTARCH_NODE_IDS):
        raise ApplyBlocked(
            "applied residue is not exactly the excluded Plutarch cohort"
        )
    stamped_nodes = [node for node in nodes if STAMP in metadata(node)]
    stamped_passages = [row for row in passages if STAMP in row]
    if len(stamped_nodes) != EXPECTED_REPAIR_NODES or len(stamped_passages) != 172:
        raise ApplyBlocked("applied stamp cardinality drift")
    demoted = [
        node for node in stamped_nodes if metadata(node)[STAMP].get("action") == DEMOTE
    ]
    if len(demoted) != EXPECTED_ACTION_NODES[DEMOTE]:
        raise ApplyBlocked("applied demotion cardinality drift")
    if any("db_passage_id" in metadata(node) for node in demoted):
        raise ApplyBlocked("a demoted row still declares an exact twin")


def validate_final_state(
    nodes: list[dict[str, Any]],
    passages: list[dict[str, Any]],
    citations: list[dict[str, Any]],
) -> None:
    summary, violations = compute_parity(nodes, passages, citations)
    if summary != EXPECTED_FINAL or violations:
        raise ApplyBlocked(f"coordinated final parity drift: {summary}")
    stamped_nodes = [node for node in nodes if STAMP in metadata(node)]
    stamped_passages = [row for row in passages if STAMP in row]
    if len(stamped_nodes) != EXPECTED_REPAIR_NODES or len(stamped_passages) != 172:
        raise ApplyBlocked("coordinated final stamp cardinality drift")
    demoted = [
        node for node in stamped_nodes if metadata(node)[STAMP].get("action") == DEMOTE
    ]
    if len(demoted) != EXPECTED_ACTION_NODES[DEMOTE]:
        raise ApplyBlocked("coordinated final demotion cardinality drift")
    plutarch = {
        node_id(node): metadata(node)
        for node in nodes
        if node_id(node) in EXCLUDED_PLUTARCH_NODE_IDS
    }
    if set(plutarch) != set(EXCLUDED_PLUTARCH_NODE_IDS):
        raise ApplyBlocked("coordinated final Plutarch cohort disappeared")
    if any(
        data.get("work_node_id") != "work_plutarch_epitome_animae_procreatione_timaeo"
        for data in plutarch.values()
    ):
        raise ApplyBlocked("coordinated final Plutarch parent drift")


def format_parity(label: str, values: dict[str, int]) -> str:
    return (
        f"{label}: violations={values['violations']} "
        f"(cts_urn={values['cts_urn_mismatches']}, "
        f"canonical_ref={values['canonical_ref_mismatches']}, "
        f"missing_twins={values['missing_twins']}, "
        f"missing_citations={values['missing_citations']}), "
        f"declared={values['declared_twins']}, shared={values['shared_twins']}"
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    parser.add_argument(
        "--data-root",
        type=Path,
        default=DEFAULT_DATA_ROOT,
        help="directory containing kg/, corpus/, and audit/",
    )
    parser.add_argument("--max-details", type=int, default=0)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    data_root = args.data_root.expanduser().resolve()
    nodes_path = data_root / "kg" / "nodes.jsonl"
    passages_path = data_root / "corpus" / "passages.jsonl"
    citations_path = data_root / "corpus" / "citations.jsonl"
    state = validate_source_hashes(data_root)

    nodes = read_jsonl(nodes_path)
    passages = read_jsonl(passages_path)
    citations = read_jsonl(citations_path)
    original_citations_bytes = citations_path.read_bytes()

    if state in {"applied", "final"}:
        if state == "applied":
            validate_applied_state(nodes, passages, citations)
            expected = EXPECTED_AFTER
        else:
            validate_final_state(nodes, passages, citations)
            expected = EXPECTED_FINAL
        print(f"mode: {'write' if args.write else 'dry-run'}")
        print(f"source state: {state}")
        print(format_parity("current", expected))
        print("plan: already applied; changed=0")
        print("write: no-op (verified applied hashes and stamps)")
        return 0

    original_nodes = copy.deepcopy(nodes)
    original_passages = copy.deepcopy(passages)
    original_text_digest = text_digest(nodes, passages)
    before, before_violations = compute_parity(nodes, passages, citations)
    if before != EXPECTED_BEFORE:
        raise ApplyBlocked(f"before-parity drift: {before}")

    try:
        records = build_repair_records(
            nodes, passages, citations, before_violations, data_root
        )
    except PlanError as error:
        raise ApplyBlocked(str(error)) from error
    plan_sha256 = record_digest(records)
    if plan_sha256 != EXPECTED_PLAN_SHA256:
        raise ApplyBlocked(f"repair plan digest drift: {plan_sha256}")

    counts, details = rewrite(nodes, passages, records)
    validate_counts(counts)
    validate_mutation_scope(original_nodes, nodes, original_passages, passages)
    if text_digest(nodes, passages) != original_text_digest:
        raise ApplyBlocked("ancient text/description digest changed")
    if citations_path.read_bytes() != original_citations_bytes:
        raise ApplyBlocked("citations changed during the in-memory rewrite")

    after, after_violations = compute_parity(nodes, passages, citations)
    if after != EXPECTED_AFTER:
        raise ApplyBlocked(f"after-parity drift: {after}")
    fixed = before["violations"] - after["violations"]
    if fixed != EXPECTED_FIXED_VIOLATIONS:
        raise ApplyBlocked(
            f"fixed {fixed} violations, expected {EXPECTED_FIXED_VIOLATIONS}"
        )
    before_keys = _violation_keys(before_violations)
    after_keys = _violation_keys(after_violations)
    if not after_keys < before_keys:
        raise ApplyBlocked("after-state introduced a new or unchanged full debt set")
    if {key[0] for key in after_keys} != set(EXCLUDED_PLUTARCH_NODE_IDS):
        raise ApplyBlocked(
            "residue is not exactly the separately owned Plutarch cohort"
        )

    second_counts, _ = rewrite(nodes, passages, records)
    if second_counts["already_applied"] != EXPECTED_REPAIR_NODES:
        raise ApplyBlocked("second pass did not recognize every stamped node")
    if sum(value for key, value in second_counts.items() if key != "already_applied"):
        raise ApplyBlocked(f"second pass was not a no-op: {second_counts}")

    nodes_output = render_jsonl_preserving_unchanged(
        nodes_path, original_nodes, nodes, compact=False
    )
    passages_output = render_jsonl_preserving_unchanged(
        passages_path, original_passages, passages, compact=True
    )
    nodes_output_sha256 = sha256_bytes(nodes_output)
    passages_output_sha256 = sha256_bytes(passages_output)
    if (
        APPLIED_NODES_SHA256 != "TO_BE_FILLED"
        and nodes_output_sha256 != APPLIED_NODES_SHA256
    ):
        raise ApplyBlocked(f"deterministic nodes hash drift: {nodes_output_sha256}")
    if (
        APPLIED_PASSAGES_SHA256 != "TO_BE_FILLED"
        and passages_output_sha256 != APPLIED_PASSAGES_SHA256
    ):
        raise ApplyBlocked(
            f"deterministic passages hash drift: {passages_output_sha256}"
        )

    print(f"mode: {'write' if args.write else 'dry-run'}")
    print("source state: baseline")
    print(format_parity("before", before))
    print(
        f"plan: nodes={len(records)}, violations_fixed={fixed}, "
        f"plan_sha256={plan_sha256}"
    )
    for action in sorted(EXPECTED_ACTION_NODES):
        print(f"  {action}: {counts['action__' + action]}")
    print(
        "fields: "
        f"node.canonical_ref={counts['node__canonical_ref']}, "
        f"node.cts_urn={counts['node__cts_urn']}, "
        f"corpus.cts_urn={counts['corpus__cts_urn']}, "
        f"db_passage_id_removed={counts['node__db_passage_id__removed']}"
    )
    print(format_parity("after", after))
    print(
        "residue: 6 canonical_ref mismatches in passage_plut_cn_1..6 "
        "(separate tlg135/tlg138 adjudication)"
    )
    print(
        "invariants: OK "
        f"(ancient_text_digest={original_text_digest}; citations_changed=0; "
        f"second_pass_changed=0; nodes_sha256={nodes_output_sha256}; "
        f"passages_sha256={passages_output_sha256})"
    )
    for line in details[: max(0, args.max_details)]:
        print("  " + line)

    if not args.write:
        print("write: disabled (dry-run default; use --write to apply)")
        return 0

    nodes_backup = nodes_path.with_name(nodes_path.name + BACKUP_SUFFIX)
    passages_backup = passages_path.with_name(passages_path.name + BACKUP_SUFFIX)
    existing = [path for path in (nodes_backup, passages_backup) if path.exists()]
    if existing:
        raise ApplyBlocked(f"backup already exists: {existing[0]}")
    shutil.copy2(nodes_path, nodes_backup)
    shutil.copy2(passages_path, passages_backup)
    try:
        atomic_write(passages_path, passages_output)
        atomic_write(nodes_path, nodes_output)
        if sha256_path(nodes_path) != nodes_output_sha256:
            raise ApplyBlocked("written nodes hash differs from verified output")
        if sha256_path(passages_path) != passages_output_sha256:
            raise ApplyBlocked("written passages hash differs from verified output")
    except Exception:
        atomic_write(nodes_path, nodes_backup.read_bytes())
        atomic_write(passages_path, passages_backup.read_bytes())
        raise
    print(f"wrote: {nodes_path}")
    print(f"wrote: {passages_path}")
    print(f"backup: {nodes_backup}")
    print(f"backup: {passages_backup}")
    print("citations: byte-for-byte unchanged")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
