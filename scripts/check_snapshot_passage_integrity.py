#!/usr/bin/env python3
"""Audit KG/corpus snapshot identity, provenance and one-to-one linkage.

This gate deliberately exposes historical debt.  Until that debt reaches zero,
``--strict`` enforces a frozen fingerprint baseline (known items may disappear;
new ones may not appear).  ``--zero-debt`` is the final SOTA gate and fails on
any remaining violation.  Repeat ``--node-prefix`` to require a touched cohort
to be completely clean, independently of the legacy baseline.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import unicodedata
from collections import Counter, defaultdict
from collections.abc import Iterable
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_ROOT = ROOT / "data"
DEFAULT_BASELINE = ROOT / "data/audit/snapshot_passage_integrity_baseline.json"
PASSAGE_ID_KEYS = ("db_passage_id", "passage_id", "corpus_passage_id")
MIGRATION_CEILING_CODES = {"snapshot_passage_id_not_declared"}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def node_id(node: dict[str, Any]) -> str:
    return str(node.get("id") or node.get("node_id") or "")


def metadata(node: dict[str, Any]) -> dict[str, Any]:
    value = node.get("metadata")
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            return {}
    return value if isinstance(value, dict) else {}


def nfc(value: str | None) -> str:
    return unicodedata.normalize("NFC", value or "")


def sha256_text(value: str | None) -> str:
    return hashlib.sha256(nfc(value).encode("utf-8")).hexdigest()


def violation(
    code: str,
    *,
    node: str = "",
    passage: str = "",
    field: str = "",
    expected: Any = None,
    actual: Any = None,
) -> dict[str, Any]:
    row = {
        "code": code,
        "node_id": node,
        "passage_id": passage,
        "field": field,
        "expected": expected,
        "actual": actual,
    }
    canonical = json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    row["fingerprint"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return row


def audit_integrity(
    nodes: Iterable[dict[str, Any]],
    passages: Iterable[dict[str, Any]],
    citations: Iterable[dict[str, Any]],
) -> list[dict[str, Any]]:
    nodes = list(nodes)
    passages = list(passages)
    citations = list(citations)
    by_node = {node_id(node): node for node in nodes}
    by_passage = {str(row.get("passage_id") or ""): row for row in passages}
    violations: list[dict[str, Any]] = []

    snapshots = [
        row for row in citations if row.get("citation_type") == "snapshot_passage_node"
    ]
    by_snapshot_passage: dict[str, list[str]] = defaultdict(list)
    by_snapshot_node: dict[str, list[str]] = defaultdict(list)
    snapshot_pairs: set[tuple[str, str]] = set()
    for row in snapshots:
        passage = str(row.get("passage_id") or "")
        node = str(row.get("kg_node_id") or "")
        by_snapshot_passage[passage].append(node)
        by_snapshot_node[node].append(passage)
        snapshot_pairs.add((passage, node))
        if passage not in by_passage:
            violations.append(
                violation("snapshot_missing_corpus_passage", node=node, passage=passage)
            )
        if node not in by_node:
            violations.append(
                violation("snapshot_missing_kg_node", node=node, passage=passage)
            )

    # Per-member findings are monotonic: fixing one member removes a known
    # fingerprint instead of creating a different cluster fingerprint.
    for passage, members in by_snapshot_passage.items():
        if len(members) > 1:
            for node in members:
                violations.append(
                    violation(
                        "snapshot_passage_not_bijective",
                        node=node,
                        passage=passage,
                        expected=1,
                        actual=len(members),
                    )
                )
    for node, members in by_snapshot_node.items():
        if len(members) > 1:
            for passage in members:
                violations.append(
                    violation(
                        "snapshot_node_not_bijective",
                        node=node,
                        passage=passage,
                        expected=1,
                        actual=len(members),
                    )
                )

    for node, members in by_snapshot_node.items():
        kg_node = by_node.get(node)
        if kg_node is None:
            continue
        if kg_node.get("type") != "passage":
            for passage in members:
                violations.append(
                    violation(
                        "snapshot_target_not_passage_node",
                        node=node,
                        passage=passage,
                        expected="passage",
                        actual=kg_node.get("type"),
                    )
                )
        data = metadata(kg_node)
        verified_translation = (
            data.get("passage_role") == "translation"
            and data.get("translation_type") == "published_scholarly_translation"
            and data.get("verified_against_source") is True
        )
        if (
            data.get("attestation_type") == "editorial_synthesis"
            or data.get("passage_role") == "editorial_synthesis"
            or (data.get("citable_as_primary") is False and not verified_translation)
        ):
            for passage in members:
                violations.append(
                    violation(
                        "snapshot_editorial_or_non_primary",
                        node=node,
                        passage=passage,
                        actual={
                            "attestation_type": data.get("attestation_type"),
                            "passage_role": data.get("passage_role"),
                            "citable_as_primary": data.get("citable_as_primary"),
                        },
                    )
                )
        declared = {
            str(data.get(key)) for key in PASSAGE_ID_KEYS if data.get(key) not in (None, "")
        }
        if not declared:
            for passage in members:
                violations.append(
                    violation(
                        "snapshot_passage_id_not_declared", node=node, passage=passage
                    )
                )

    for kg_node in nodes:
        if kg_node.get("type") != "passage":
            continue
        wanted = node_id(kg_node)
        data = metadata(kg_node)
        declared = {
            str(data.get(key)) for key in PASSAGE_ID_KEYS if data.get(key) not in (None, "")
        }
        if not declared:
            continue
        if len(declared) > 1:
            violations.append(
                violation(
                    "declared_passage_id_conflict",
                    node=wanted,
                    field="|".join(PASSAGE_ID_KEYS),
                    expected="one distinct UUID",
                    actual=sorted(declared),
                )
            )
            continue
        passage_id = next(iter(declared))
        corpus = by_passage.get(passage_id)
        if corpus is None:
            violations.append(
                violation("declared_passage_missing_corpus", node=wanted, passage=passage_id)
            )
            continue
        if (passage_id, wanted) not in snapshot_pairs:
            violations.append(
                violation("declared_passage_missing_snapshot", node=wanted, passage=passage_id)
            )
        for field in ("canonical_ref", "cts_urn"):
            if data.get(field) is None:
                continue
            if nfc(str(data.get(field))) != nfc(str(corpus.get(field) or "")):
                violations.append(
                    violation(
                        f"declared_{field}_mismatch",
                        node=wanted,
                        passage=passage_id,
                        field=field,
                        expected=corpus.get(field),
                        actual=data.get(field),
                    )
                )
        declared_hash = data.get("text_content_sha256_nfc")
        if declared_hash:
            node_hash = sha256_text(str(kg_node.get("description") or ""))
            corpus_hash = sha256_text(str(corpus.get("text_content") or ""))
            if node_hash != declared_hash:
                violations.append(
                    violation(
                        "declared_text_hash_mismatch_node",
                        node=wanted,
                        passage=passage_id,
                        expected=declared_hash,
                        actual=node_hash,
                    )
                )
            if corpus_hash != declared_hash:
                violations.append(
                    violation(
                        "declared_text_hash_mismatch_corpus",
                        node=wanted,
                        passage=passage_id,
                        expected=declared_hash,
                        actual=corpus_hash,
                    )
                )
    return sorted(
        violations,
        key=lambda row: (
            row["code"], row["node_id"], row["passage_id"], row["fingerprint"]
        ),
    )


def make_baseline(violations: list[dict[str, Any]]) -> dict[str, Any]:
    counts = Counter(row["code"] for row in violations)
    fingerprints = sorted(
        row["fingerprint"]
        for row in violations
        if row["code"] not in MIGRATION_CEILING_CODES
    )
    return {
        "schema_version": "1.0.0",
        "generated_at": "2026-08-24",
        "policy": (
            "Known exact fingerprints may only disappear. Migration-ceiling codes may "
            "only decrease. Final target is an empty baseline and zero violations."
        ),
        "known_exact_fingerprints": fingerprints,
        "migration_debt_ceilings": {
            code: counts.get(code, 0) for code in sorted(MIGRATION_CEILING_CODES)
        },
        "counts_at_baseline": dict(sorted(counts.items())),
        "total_at_baseline": len(violations),
    }


def compare_baseline(
    violations: list[dict[str, Any]], baseline: dict[str, Any]
) -> tuple[list[dict[str, Any]], dict[str, tuple[int, int]]]:
    known = set(baseline.get("known_exact_fingerprints") or [])
    current_counts = Counter(row["code"] for row in violations)
    new_exact = [
        row
        for row in violations
        if row["code"] not in MIGRATION_CEILING_CODES
        and row["fingerprint"] not in known
    ]
    ceiling_breaches: dict[str, tuple[int, int]] = {}
    for code, ceiling in (baseline.get("migration_debt_ceilings") or {}).items():
        current = current_counts.get(code, 0)
        if current > int(ceiling):
            ceiling_breaches[code] = (current, int(ceiling))
    return new_exact, ceiling_breaches


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, default=DEFAULT_DATA_ROOT)
    parser.add_argument("--baseline", type=Path, default=DEFAULT_BASELINE)
    parser.add_argument("--strict", action="store_true", help="forbid debt growth")
    parser.add_argument("--zero-debt", action="store_true", help="require no violations")
    parser.add_argument("--write-baseline", action="store_true")
    parser.add_argument("--node-prefix", action="append", default=[])
    parser.add_argument("--max-examples", type=int, default=20)
    args = parser.parse_args(argv)

    data_root = args.data_root.expanduser().resolve()
    violations = audit_integrity(
        read_jsonl(data_root / "kg/nodes.jsonl"),
        read_jsonl(data_root / "corpus/passages.jsonl"),
        read_jsonl(data_root / "corpus/citations.jsonl"),
    )
    prefixes = tuple(args.node_prefix)
    scoped = (
        [row for row in violations if row["node_id"].startswith(prefixes)]
        if prefixes
        else violations
    )
    counts = Counter(row["code"] for row in scoped)
    print("scope:", ", ".join(prefixes) if prefixes else "all snapshots and declared twins")
    print("violations:", len(scoped))
    print("by code:", json.dumps(dict(sorted(counts.items())), sort_keys=True))
    for row in scoped[: max(0, args.max_examples)]:
        print(
            f"  {row['code']}: node={row['node_id']!r} "
            f"passage={row['passage_id']!r} field={row['field']!r}"
        )

    baseline_path = args.baseline.expanduser().resolve()
    if args.write_baseline:
        payload = make_baseline(violations)
        baseline_path.parent.mkdir(parents=True, exist_ok=True)
        baseline_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print("baseline written:", baseline_path)

    if prefixes and (args.strict or args.zero_debt):
        if scoped:
            print("COHORT STRICT: violations remain -> FAIL")
            return 1
        print("COHORT STRICT: zero violations -> OK")
        return 0
    if args.zero_debt:
        if violations:
            print("ZERO DEBT: violations remain -> FAIL")
            return 1
        print("ZERO DEBT: OK")
        return 0
    if args.strict:
        if not baseline_path.exists():
            print("STRICT: baseline missing -> FAIL")
            return 1
        baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
        new_exact, ceiling_breaches = compare_baseline(violations, baseline)
        print("new exact violations:", len(new_exact))
        print("migration ceiling breaches:", ceiling_breaches)
        if new_exact or ceiling_breaches:
            print("STRICT: integrity debt grew -> FAIL")
            return 1
        print("STRICT: no new debt; known debt may only shrink -> OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
