#!/usr/bin/env python3
"""Check exact locus parity for KG passage nodes with declared corpus twins.

A shared passage is a KG ``passage`` whose ``metadata.db_passage_id`` resolves
to a corpus ``passage_id``.  For every such pair this gate checks the citation
link plus exact equality of ``canonical_ref`` and ``cts_urn``.

The full corpus still contains historical formatting and locus drift outside
the cold-audit repair scope.  Repeat ``--node-prefix`` to make an enforceable
cohort gate in CI; without prefixes the script reports every shared pair.

Exit policy:
  * report mode (default): print findings, exit 0;
  * ``--strict``: exit 1 on a missing twin/citation or any locus mismatch.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from collections.abc import Iterable
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_ROOT = ROOT / "data"


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


def find_violations(
    nodes: Iterable[dict[str, Any]],
    passages: Iterable[dict[str, Any]],
    citations: Iterable[dict[str, Any]],
    prefixes: tuple[str, ...] = (),
) -> tuple[int, list[dict[str, Any]]]:
    passages_by_id = {
        str(row.get("passage_id") or ""): row for row in passages
    }
    citation_pairs = {
        (str(row.get("passage_id") or ""), str(row.get("kg_node_id") or ""))
        for row in citations
    }
    shared = 0
    violations: list[dict[str, Any]] = []

    for node in nodes:
        wanted = node_id(node)
        if node.get("type") != "passage":
            continue
        if prefixes and not wanted.startswith(prefixes):
            continue
        data = metadata(node)
        passage_id = str(data.get("db_passage_id") or "")
        if not passage_id:
            continue
        passage = passages_by_id.get(passage_id)
        if passage is None:
            violations.append(
                {
                    "node_id": wanted,
                    "passage_id": passage_id,
                    "field": "passage_id",
                    "kg": passage_id,
                    "corpus": None,
                    "reason": "missing_corpus_twin",
                }
            )
            continue
        shared += 1
        if (passage_id, wanted) not in citation_pairs:
            violations.append(
                {
                    "node_id": wanted,
                    "passage_id": passage_id,
                    "field": "citation",
                    "kg": wanted,
                    "corpus": passage_id,
                    "reason": "missing_twin_citation",
                }
            )
        for field in ("canonical_ref", "cts_urn"):
            if data.get(field) == passage.get(field):
                continue
            violations.append(
                {
                    "node_id": wanted,
                    "passage_id": passage_id,
                    "field": field,
                    "kg": data.get(field),
                    "corpus": passage.get(field),
                    "reason": "locus_mismatch",
                }
            )
    return shared, violations


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--strict", action="store_true")
    parser.add_argument(
        "--data-root",
        type=Path,
        default=DEFAULT_DATA_ROOT,
        help="directory containing kg/ and corpus/",
    )
    parser.add_argument(
        "--node-prefix",
        action="append",
        default=[],
        help="limit to a KG node-id prefix; repeatable",
    )
    parser.add_argument("--max-examples", type=int, default=20)
    args = parser.parse_args(argv)

    data_root = args.data_root.expanduser().resolve()
    nodes = read_jsonl(data_root / "kg" / "nodes.jsonl")
    passages = read_jsonl(data_root / "corpus" / "passages.jsonl")
    citations = read_jsonl(data_root / "corpus" / "citations.jsonl")
    prefixes = tuple(args.node_prefix)
    shared, violations = find_violations(nodes, passages, citations, prefixes)
    reasons = Counter(row["reason"] for row in violations)
    fields = Counter(row["field"] for row in violations)

    print(f"scope: {', '.join(prefixes) if prefixes else 'all declared twins'}")
    print(f"shared passages checked: {shared}")
    print(f"violations: {len(violations)}")
    print(f"by reason: {dict(sorted(reasons.items()))}")
    print(f"by field: {dict(sorted(fields.items()))}")
    if violations:
        print("examples:")
        for row in violations[: max(0, args.max_examples)]:
            print(
                f"  {row['node_id']} / {row['passage_id']}: "
                f"{row['field']} KG={row['kg']!r} corpus={row['corpus']!r}"
            )
    if prefixes and shared == 0:
        print("selected cohort has no declared corpus twins -> FAIL")
        return 1
    if args.strict and violations:
        print("STRICT: KG/corpus locus parity failed")
        return 1
    print("parity: OK" if not violations else "parity: REPORT ONLY")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
