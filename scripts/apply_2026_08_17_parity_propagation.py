#!/usr/bin/env python3
"""Propagate established KG locus truth to audited corpus twin families.

Dry-run is the default.  ``--write`` is required to replace
``data/corpus/passages.jsonl``.  The script never writes KG data, never changes
``text_content``, and leaves citations byte-for-byte unchanged.

Usage:
    python3 scripts/apply_2026_08_17_parity_propagation.py
    python3 scripts/apply_2026_08_17_parity_propagation.py --write
    python3 scripts/apply_2026_08_17_parity_propagation.py \
        --data-root /path/to/data
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
from data_2026_08_17_parity_propagation import (  # noqa: E402
    APPLIED_PASSAGES_SHA256,
    BACKUP_SUFFIX,
    BASELINE_FILE_SHA256,
    EXPECTED_AFTER,
    EXPECTED_BEFORE,
    EXPECTED_FIELD_CHANGES,
    EXPECTED_FIXED_VIOLATIONS,
    EXPECTED_REPAIR_ROWS,
    FAMILY_EVIDENCE,
    ROOT,
    STAMP,
    PlanError,
    RepairRecord,
    build_repair_records,
    metadata,
    node_id,
    read_jsonl,
    sha256_text,
)

DEFAULT_DATA_ROOT = ROOT / "data"


class ApplyBlocked(RuntimeError):
    """Raised when a precondition or invariant has moved."""


def canonical_json(value: Any) -> str:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_path(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def jsonl_bytes(rows: list[dict[str, Any]]) -> bytes:
    return "".join(
        json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n"
        for row in rows
    ).encode("utf-8")


def atomic_write(path: Path, payload: bytes) -> None:
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_bytes(payload)
    os.replace(temporary, path)


def parity_summary(
    shared: int, violations: list[dict[str, Any]]
) -> dict[str, int]:
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
) -> dict[str, int]:
    shared, violations = find_violations(nodes, passages, citations)
    return parity_summary(shared, violations)


def text_digest(passages: list[dict[str, Any]]) -> str:
    digest = hashlib.sha256()
    for row in passages:
        digest.update(str(row.get("passage_id") or "").encode("utf-8"))
        digest.update(b"\0")
        digest.update(str(row.get("text_content") or "").encode("utf-8"))
        digest.update(b"\0")
    return digest.hexdigest()


def validate_source_hashes(data_root: Path) -> str:
    actual_nodes = sha256_path(data_root / "kg" / "nodes.jsonl")
    actual_passages = sha256_path(data_root / "corpus" / "passages.jsonl")
    actual_citations = sha256_path(data_root / "corpus" / "citations.jsonl")
    if actual_nodes != BASELINE_FILE_SHA256["kg/nodes.jsonl"]:
        raise ApplyBlocked("data/kg/nodes.jsonl is outside the audited snapshot")
    if actual_citations != BASELINE_FILE_SHA256["corpus/citations.jsonl"]:
        raise ApplyBlocked("data/corpus/citations.jsonl is outside the audited snapshot")
    if actual_passages == BASELINE_FILE_SHA256["corpus/passages.jsonl"]:
        return "baseline"
    if actual_passages == APPLIED_PASSAGES_SHA256:
        return "applied"
    raise ApplyBlocked("data/corpus/passages.jsonl is neither baseline nor applied state")


def _check_record_context(
    record: RepairRecord,
    nodes_by_id: dict[str, dict[str, Any]],
    passages_by_id: dict[str, dict[str, Any]],
    citation_counts: Counter,
) -> tuple[dict[str, Any], dict[str, Any]]:
    node = nodes_by_id.get(record.node_id)
    if node is None:
        raise ApplyBlocked(f"{record.node_id}: KG node missing")
    data = metadata(node)
    for field, expected in record.expected_kg.items():
        if data.get(field) != expected:
            raise ApplyBlocked(
                f"{record.node_id}: KG {field}={data.get(field)!r}, "
                f"expected {expected!r}"
            )
    passage = passages_by_id.get(record.passage_id)
    if passage is None:
        raise ApplyBlocked(f"{record.node_id}: corpus twin missing")
    if citation_counts[(record.passage_id, record.node_id)] != 1:
        raise ApplyBlocked(
            f"{record.node_id}/{record.passage_id}: twin citation count is "
            f"{citation_counts[(record.passage_id, record.node_id)]}"
        )
    if sha256_text(str(passage.get("text_content") or "")) != record.text_sha256:
        raise ApplyBlocked(f"{record.passage_id}: ancient text precondition drift")
    return node, passage


def _desired_state_error(record: RepairRecord, passage: dict[str, Any]) -> str | None:
    for field, desired in record.desired_corpus.items():
        if passage.get(field) != desired:
            return f"{field}={passage.get(field)!r}, expected {desired!r}"
    for field in record.remove_fields:
        if field in passage:
            return f"{field} should be absent"
    return None


def rewrite(
    nodes: list[dict[str, Any]],
    passages: list[dict[str, Any]],
    citations: list[dict[str, Any]],
    records: tuple[RepairRecord, ...],
) -> tuple[Counter, list[str]]:
    nodes_by_id = {node_id(node): node for node in nodes}
    passages_by_id = {
        str(row.get("passage_id") or ""): row for row in passages
    }
    citation_counts = Counter(
        (
            str(row.get("passage_id") or ""),
            str(row.get("kg_node_id") or ""),
        )
        for row in citations
    )
    counts: Counter = Counter()
    details: list[str] = []

    for record in records:
        _, passage = _check_record_context(
            record, nodes_by_id, passages_by_id, citation_counts
        )
        existing_stamp = passage.get(STAMP)
        if existing_stamp is not None:
            if existing_stamp != record.stamp_value:
                raise ApplyBlocked(f"{record.passage_id}: parity stamp drift")
            error = _desired_state_error(record, passage)
            if error:
                raise ApplyBlocked(
                    f"{record.passage_id}: stamped row is inconsistent: {error}"
                )
            counts["already_applied"] += 1
            continue

        for field, expected in record.expected_corpus.items():
            if passage.get(field) != expected:
                raise ApplyBlocked(
                    f"{record.passage_id}: corpus {field}={passage.get(field)!r}, "
                    f"expected {expected!r}"
                )
        for field in record.remove_fields:
            if field not in passage:
                raise ApplyBlocked(
                    f"{record.passage_id}: expected removable field {field}"
                )

        for field, desired in record.desired_corpus.items():
            if passage.get(field) != desired:
                passage[field] = desired
                counts[field] += 1
        for field in record.remove_fields:
            passage.pop(field)
            counts[field + "_removed"] += 1
        passage[STAMP] = record.stamp_value
        counts["rows_changed"] += 1
        counts["family__" + record.family] += 1
        details.append(
            f"{record.family}: {record.node_id} -> {record.passage_id}"
        )
    return counts, details


def validate_mutation_scope(
    before: list[dict[str, Any]], after: list[dict[str, Any]]
) -> None:
    if len(before) != len(after):
        raise ApplyBlocked("corpus passage row count changed")
    allowed = {"canonical_ref", "cts_urn", "work_canonical_id", STAMP}
    for old, new in zip(before, after, strict=True):
        if old.get("passage_id") != new.get("passage_id"):
            raise ApplyBlocked("corpus passage order or id changed")
        old_rest = {key: value for key, value in old.items() if key not in allowed}
        new_rest = {key: value for key, value in new.items() if key not in allowed}
        if old_rest != new_rest:
            raise ApplyBlocked(
                f"{old.get('passage_id')}: a non-locus corpus field changed"
            )


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
        help="directory containing kg/, corpus/ and audit/",
    )
    parser.add_argument("--max-details", type=int, default=0)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    data_root = args.data_root.expanduser().resolve()
    passages_path = data_root / "corpus" / "passages.jsonl"
    citations_path = data_root / "corpus" / "citations.jsonl"
    state = validate_source_hashes(data_root)

    nodes = read_jsonl(data_root / "kg" / "nodes.jsonl")
    passages = read_jsonl(passages_path)
    citations = read_jsonl(citations_path)
    original_passages = copy.deepcopy(passages)
    original_citations_bytes = citations_path.read_bytes()
    original_text_digest = text_digest(passages)

    before = compute_parity(nodes, passages, citations)
    expected_before = EXPECTED_BEFORE if state == "baseline" else EXPECTED_AFTER
    if before != expected_before:
        raise ApplyBlocked(f"before-parity drift: {before}")

    try:
        records = build_repair_records(nodes, passages, citations, data_root)
    except PlanError as error:
        raise ApplyBlocked(str(error)) from error
    if len(records) != EXPECTED_REPAIR_ROWS:
        raise ApplyBlocked(f"repair plan has {len(records)} rows")

    counts, details = rewrite(nodes, passages, citations, records)
    validate_mutation_scope(original_passages, passages)
    if text_digest(passages) != original_text_digest:
        raise ApplyBlocked("ancient text digest changed")
    if citations_path.read_bytes() != original_citations_bytes:
        raise ApplyBlocked("citations changed during the in-memory rewrite")

    after = compute_parity(nodes, passages, citations)
    if after != EXPECTED_AFTER:
        raise ApplyBlocked(f"after-parity drift: {after}")
    fixed = before["violations"] - after["violations"]
    expected_fixed = EXPECTED_FIXED_VIOLATIONS if state == "baseline" else 0
    if fixed != expected_fixed:
        raise ApplyBlocked(f"fixed violation count is {fixed}, expected {expected_fixed}")

    if state == "baseline":
        observed_fields = {
            "canonical_ref": counts["canonical_ref"],
            "cts_urn": counts["cts_urn"],
            "work_canonical_id_removed": counts["work_canonical_id_removed"],
        }
        if observed_fields != EXPECTED_FIELD_CHANGES:
            raise ApplyBlocked(f"field-change count drift: {observed_fields}")

    # A second in-memory pass must be a complete no-op.
    second_records = build_repair_records(nodes, passages, citations, data_root)
    second_counts, _ = rewrite(nodes, passages, citations, second_records)
    if second_counts["rows_changed"] != 0:
        raise ApplyBlocked("idempotence check changed rows on the second pass")
    if second_counts["already_applied"] != EXPECTED_REPAIR_ROWS:
        raise ApplyBlocked("idempotence check did not recognise every stamped row")

    output = jsonl_bytes(passages)
    output_sha256 = sha256_bytes(output)
    if output_sha256 != APPLIED_PASSAGES_SHA256:
        raise ApplyBlocked(
            f"deterministic output hash drift: {output_sha256}"
        )

    print(f"mode: {'write' if args.write else 'dry-run'}")
    print(f"source state: {state}")
    print(format_parity("before", before))
    print(
        f"plan: rows={len(records)}, changed={counts['rows_changed']}, "
        f"already_applied={counts['already_applied']}"
    )
    for family in sorted(FAMILY_EVIDENCE):
        print(
            f"  {family}: {counts['family__' + family]} changed; "
            f"evidence={FAMILY_EVIDENCE[family]}"
        )
    print(
        "fields: "
        f"canonical_ref={counts['canonical_ref']}, "
        f"cts_urn={counts['cts_urn']}, "
        f"work_canonical_id_removed={counts['work_canonical_id_removed']}"
    )
    print(format_parity("after", after))
    print(
        "invariants: OK "
        f"(text_digest={original_text_digest}; citations_changed=0; "
        f"second_pass_changed=0; output_sha256={output_sha256})"
    )
    for line in details[: max(0, args.max_details)]:
        print("  " + line)

    if not args.write:
        print("write: disabled (--dry-run default; use --write to apply)")
        return 0
    if counts["rows_changed"] == 0:
        print("write: no-op (all repair rows already stamped)")
        return 0

    backup = passages_path.with_name(passages_path.name + BACKUP_SUFFIX)
    if backup.exists():
        raise ApplyBlocked(f"backup already exists: {backup}")
    shutil.copy2(passages_path, backup)
    atomic_write(passages_path, output)
    if sha256_path(passages_path) != APPLIED_PASSAGES_SHA256:
        raise ApplyBlocked("written passages hash differs from verified output")
    print(f"wrote: {passages_path}")
    print(f"backup: {backup}")
    print("citations: unchanged")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
