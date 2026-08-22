#!/usr/bin/env python3
"""Check that a KG work's canonical CTS identity matches its own passages.

This catches a different failure mode from ``check_kg_work_id_uniqueness``:
all children may agree with one another while the parent work node advertises
an entirely different work.  Only one-child-consensus cohorts are enforced;
known split-source ambiguities are allowlisted by exact identities.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
NODES_PATH = ROOT / "data/kg/nodes.jsonl"
EDGES_PATH = ROOT / "data/kg/edges.jsonl"
MANIFEST_PATH = ROOT / "data/corpus/manifest.jsonl"
DEFAULT_ALLOWLIST = ROOT / "data/audit/kg_work_child_canonical_known_ambiguities.json"

URN_RE = re.compile(r"urn:cts:(greekLit|latinLit):([^:\s]+)", re.IGNORECASE)
TLG_RE = re.compile(r"(tlg\d+)\W+(tlg\d+)", re.IGNORECASE)
STOA_RE = re.compile(r"(stoa\d+)\W+(stoa\d+|\d{3})", re.IGNORECASE)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def metadata(node: dict[str, Any]) -> dict[str, Any]:
    value = node.get("metadata") or {}
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            return {}
    return value if isinstance(value, dict) else {}


def canonical_cts(value: Any) -> str | None:
    """Normalize project CTS/First1K/slug spellings to a work-level CTS URN."""

    raw = str(value or "").strip()
    if not raw:
        return None
    match = URN_RE.search(raw)
    if match:
        namespace = "greekLit" if match.group(1).lower() == "greeklit" else "latinLit"
        parts = match.group(2).split(".")
        if len(parts) >= 2:
            return f"urn:cts:{namespace}:{parts[0]}.{parts[1]}"

    match = TLG_RE.search(raw.replace("_", "."))
    if match:
        return f"urn:cts:greekLit:{match.group(1).lower()}.{match.group(2).lower()}"
    match = STOA_RE.search(raw.replace("_", "."))
    if match:
        return f"urn:cts:latinLit:{match.group(1).lower()}.{match.group(2).lower()}"
    return None


def work_candidates(node: dict[str, Any]) -> set[str]:
    data = metadata(node)
    return {
        value
        for key in ("cts_urn", "work_canonical_id", "canonical_id")
        if (value := canonical_cts(data.get(key)))
    }


def passage_candidate(
    node: dict[str, Any], manifest_aliases: dict[str, str] | None = None
) -> str | None:
    data = metadata(node)
    # The gate deliberately requires the passage's explicit work identity.
    # Project-local corpus slugs are resolved only through one coherent
    # manifest alias; falling back to the passage CTS locus would turn
    # incomplete metadata into an inferred repair authority.
    raw = str(data.get("work_canonical_id") or "").strip()
    return canonical_cts(raw) or (manifest_aliases or {}).get(raw)


def manifest_candidates(row: dict[str, Any]) -> set[str]:
    return {
        value
        for key in ("cts_urn", "canonical_id", "source")
        if (value := canonical_cts(row.get(key)))
    }


def find_mismatches(
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    manifest: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    by_id = {str(node.get("id") or node.get("node_id") or ""): node for node in nodes}
    children: dict[str, list[str]] = defaultdict(list)
    for edge in edges:
        if edge.get("relation") != "part_of":
            continue
        source = str(edge.get("source") or edge.get("source_id") or "")
        target = str(edge.get("target") or edge.get("target_id") or "")
        if by_id.get(source, {}).get("type") != "passage":
            continue
        if by_id.get(target, {}).get("type") != "work":
            continue
        children[target].append(source)

    manifest_index: dict[str, list[dict[str, Any]]] = defaultdict(list)
    alias_candidates: dict[str, set[str]] = defaultdict(set)
    for row in manifest:
        candidates = manifest_candidates(row)
        if (
            len(candidates) != 1
            or row.get("status") != "in_corpus"
            or not isinstance(row.get("passages"), int)
            or row["passages"] <= 0
        ):
            continue
        for candidate in candidates:
            manifest_index[candidate].append(row)
            alias = str(row.get("canonical_id") or "").strip()
            if alias:
                alias_candidates[alias].add(candidate)
    manifest_aliases = {
        alias: next(iter(candidates))
        for alias, candidates in alias_candidates.items()
        if len(candidates) == 1
    }

    findings: list[dict[str, Any]] = []
    for work_id, child_ids in sorted(children.items()):
        child_candidates = [
            passage_candidate(by_id[child_id], manifest_aliases)
            for child_id in child_ids
        ]
        if any(candidate is None for candidate in child_candidates):
            continue
        counts = Counter(child_candidates)
        if len(counts) != 1:
            continue
        child_canonical, attested_children = next(iter(counts.items()))
        parent_candidates = work_candidates(by_id[work_id])
        if not parent_candidates or parent_candidates == {child_canonical}:
            continue
        matches = manifest_index.get(child_canonical, [])
        if len(matches) != 1:
            continue
        findings.append(
            {
                "work_id": work_id,
                "work_candidates": sorted(parent_candidates),
                "child_canonical": child_canonical,
                "attested_children": attested_children,
                "total_children": len(child_ids),
                "manifest_matches": [
                    {
                        "canonical_id": row.get("canonical_id"),
                        "title": row.get("title"),
                        "author": row.get("author"),
                    }
                    for row in matches
                ],
            }
        )
    return findings


def load_allowlist(path: Path) -> dict[str, dict[str, Any]]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload.get("known_ambiguities", {})


def is_allowlisted(finding: dict[str, Any], entry: dict[str, Any]) -> bool:
    return finding["child_canonical"] == entry.get("child_canonical") and finding[
        "work_candidates"
    ] == sorted(entry.get("work_candidates") or [])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--strict", action="store_true", help="ignore the allowlist")
    parser.add_argument("--allowlist", type=Path, default=DEFAULT_ALLOWLIST)
    args = parser.parse_args(argv)

    findings = find_mismatches(
        read_jsonl(NODES_PATH), read_jsonl(EDGES_PATH), read_jsonl(MANIFEST_PATH)
    )
    allowlist = {} if args.strict else load_allowlist(args.allowlist)
    known: list[dict[str, Any]] = []
    novel: list[dict[str, Any]] = []
    for finding in findings:
        entry = allowlist.get(finding["work_id"])
        (known if entry and is_allowlisted(finding, entry) else novel).append(finding)

    print(f"work/child canonical mismatches: {len(findings)}")
    for finding in findings:
        status = "KNOWN" if finding in known else "NEW"
        print(
            f"  [{status}] {finding['work_id']}: "
            f"work={finding['work_candidates']} children={finding['child_canonical']} "
            f"({finding['attested_children']}/{finding['total_children']})"
        )
    if known:
        print(f"known ambiguities: {len(known)}")
    if novel:
        print(f"NEW mismatches: {len(novel)} -> FAIL")
        return 1
    print("OK: no new work/child canonical mismatch")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
