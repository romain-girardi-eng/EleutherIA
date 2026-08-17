#!/usr/bin/env python3
"""Plan data and deterministic policy for inverse-edge normalization.

The canonical JSONL graph stores one asserted direction only.  This module is
read-only: it loads the ontology, identifies pairs where one edge is the
declared inverse of the other, and chooses the survivor deterministically.

It is imported by ``apply_2026_08_17_inverse_normalization.py`` and can also be
run directly to inspect the current plan without changing any file.
"""

from __future__ import annotations

import argparse
import collections
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_NODES = ROOT / "data" / "kg" / "nodes.jsonl"
DEFAULT_EDGES = ROOT / "data" / "kg" / "edges.jsonl"
DEFAULT_ONTOLOGY = ROOT / "knowledge graph" / "ontology" / "edge_types.json"

STAMP = "inverse_normalization_2026_08_17"
BAK_SUFFIX = ".bak-inverse_norm"

# ``active`` and ``reserved`` are asserted relations. ``reserved_inverse`` is
# explicitly inverse-only, and deprecated aliases lose to a live relation.
STATUS_RANK = {
    "active": 0,
    "reserved": 0,
    "reserved_inverse": 1,
    "deprecated": 2,
}


@dataclass(frozen=True)
class PairPlan:
    """One survivor/doomed pair with apply-time preconditions."""

    survivor_id: str
    survivor_source: str
    survivor_relation: str
    survivor_target: str
    doomed_id: str
    doomed_source: str
    doomed_relation: str
    doomed_target: str

    def as_dict(self) -> dict[str, str]:
        return asdict(self)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            if not isinstance(row, dict):
                raise ValueError(f"{path}:{line_no}: JSON object expected")
            rows.append(row)
    return rows


def load_edge_types(path: Path = DEFAULT_ONTOLOGY) -> dict[str, dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    edge_types = payload.get("edge_types")
    if not isinstance(edge_types, dict):
        raise ValueError(f"{path}: edge_types object missing")
    return edge_types


def edge_triple(edge: dict[str, Any]) -> tuple[str, str, str]:
    return (
        str(edge.get("source") or edge.get("source_id") or ""),
        str(edge.get("relation") or ""),
        str(edge.get("target") or edge.get("target_id") or ""),
    )


def _status_rank(definition: dict[str, Any]) -> int:
    return STATUS_RANK.get(str(definition.get("status") or "active"), 0)


def canonical_relation(
    relation_a: str,
    relation_b: str,
    edge_types: dict[str, dict[str, Any]],
) -> str:
    """Choose the ontology-primary member of an inverse relation pair.

    Priority is: non-inverse/non-deprecated status; sole declaring member;
    finally JSON ontology order.  The last tie-break is stable because Python
    preserves JSON object order.  Self-inverse relations keep their name and
    are canonicalized by endpoints in :func:`build_plan`.
    """

    if relation_a == relation_b:
        return relation_a
    if relation_a not in edge_types or relation_b not in edge_types:
        # An inverse name need not have its own entry.  Such a relation cannot
        # pass R11 as asserted data, but the declaring ontology member remains
        # the deterministic primary member for policy reporting.
        if (
            relation_a in edge_types
            and edge_types[relation_a].get("inverse") == relation_b
        ):
            return relation_a
        if (
            relation_b in edge_types
            and edge_types[relation_b].get("inverse") == relation_a
        ):
            return relation_b
        return min(relation_a, relation_b)

    definition_a = edge_types[relation_a]
    definition_b = edge_types[relation_b]
    rank_a = _status_rank(definition_a)
    rank_b = _status_rank(definition_b)
    if rank_a != rank_b:
        return relation_a if rank_a < rank_b else relation_b

    a_declares_b = definition_a.get("inverse") == relation_b
    b_declares_a = definition_b.get("inverse") == relation_a
    if a_declares_b != b_declares_a:
        return relation_a if a_declares_b else relation_b

    order = {relation: index for index, relation in enumerate(edge_types)}
    return relation_a if order[relation_a] < order[relation_b] else relation_b


def policy_rows(
    edge_types: dict[str, dict[str, Any]],
) -> list[dict[str, str]]:
    """Return one policy row for every declared inverse relation pair."""

    rows: list[dict[str, str]] = []
    seen: set[frozenset[str]] = set()
    for relation, definition in edge_types.items():
        inverse = str(definition.get("inverse") or "")
        if not inverse:
            continue
        pair_key = frozenset((relation, inverse))
        if pair_key in seen:
            continue
        seen.add(pair_key)
        if relation == inverse:
            canonical = f"{relation}; source < target"
            reason = "symétrique: extrémités lexicales"
        else:
            canonical_relation_name = canonical_relation(relation, inverse, edge_types)
            canonical = canonical_relation_name
            other = inverse if canonical_relation_name == relation else relation
            canonical_definition = edge_types.get(canonical_relation_name, {})
            other_definition = edge_types.get(other, {})
            if _status_rank(canonical_definition) < _status_rank(other_definition):
                reason = "membre non inverse/non déprécié"
            elif bool(canonical_definition.get("inverse") == other) != bool(
                other_definition.get("inverse") == canonical_relation_name
            ):
                reason = "membre déclarant seul l’inverse"
            else:
                reason = "ordre primaire de edge_types.json"
        rows.append(
            {
                "relation": relation,
                "inverse": inverse,
                "canonical": canonical,
                "reason": reason,
            }
        )
    return rows


def _reverse_declarers(
    edge_types: dict[str, dict[str, Any]],
) -> dict[str, set[str]]:
    reverse: dict[str, set[str]] = collections.defaultdict(set)
    for relation, definition in edge_types.items():
        inverse = definition.get("inverse")
        if inverse:
            reverse[str(inverse)].add(relation)
    return reverse


def _counterpart_relations(
    relation: str,
    edge_types: dict[str, dict[str, Any]],
    reverse_declarers: dict[str, set[str]],
) -> set[str]:
    counterparts = set(reverse_declarers.get(relation, set()))
    inverse = edge_types.get(relation, {}).get("inverse")
    if inverse:
        counterparts.add(str(inverse))
    return counterparts


def build_plan(
    edges: list[dict[str, Any]],
    edge_types: dict[str, dict[str, Any]],
) -> list[PairPlan]:
    """Find disjoint materialized inverse pairs and choose their survivor."""

    triples: dict[tuple[str, str, str], dict[str, Any]] = {}
    edge_ids: set[str] = set()
    for edge in edges:
        triple = edge_triple(edge)
        if not all(triple):
            raise ValueError(f"malformed edge: {edge.get('edge_id', '?')}")
        if triple in triples:
            raise ValueError(f"duplicate triple before planning: {triple}")
        triples[triple] = edge
        edge_id = str(edge.get("edge_id") or "")
        if not edge_id:
            raise ValueError(f"edge has no edge_id: {triple}")
        if edge_id in edge_ids:
            raise ValueError(f"duplicate edge_id: {edge_id}")
        edge_ids.add(edge_id)

    reverse_declarers = _reverse_declarers(edge_types)
    seen_pairs: set[tuple[str, str]] = set()
    used_edges: set[str] = set()
    plan: list[PairPlan] = []

    for edge in edges:
        source, relation, target = edge_triple(edge)
        if relation not in edge_types or source == target:
            continue
        for inverse in sorted(
            _counterpart_relations(relation, edge_types, reverse_declarers)
        ):
            twin = triples.get((target, inverse, source))
            if twin is None or twin is edge:
                continue
            edge_id = str(edge["edge_id"])
            twin_id = str(twin["edge_id"])
            pair_key = tuple(sorted((edge_id, twin_id)))
            if pair_key in seen_pairs:
                continue
            seen_pairs.add(pair_key)

            if relation == inverse:
                survivor, doomed = (edge, twin) if source < target else (twin, edge)
            else:
                canonical = canonical_relation(relation, inverse, edge_types)
                survivor, doomed = (
                    (edge, twin) if relation == canonical else (twin, edge)
                )

            survivor_id = str(survivor["edge_id"])
            doomed_id = str(doomed["edge_id"])
            if survivor_id in used_edges or doomed_id in used_edges:
                raise ValueError(
                    "ambiguous inverse materialization: an edge belongs to multiple "
                    f"pairs ({survivor_id}, {doomed_id})"
                )
            used_edges.update((survivor_id, doomed_id))
            survivor_triple = edge_triple(survivor)
            doomed_triple = edge_triple(doomed)
            plan.append(
                PairPlan(
                    survivor_id=survivor_id,
                    survivor_source=survivor_triple[0],
                    survivor_relation=survivor_triple[1],
                    survivor_target=survivor_triple[2],
                    doomed_id=doomed_id,
                    doomed_source=doomed_triple[0],
                    doomed_relation=doomed_triple[1],
                    doomed_target=doomed_triple[2],
                )
            )

    return sorted(
        plan,
        key=lambda item: (
            item.survivor_relation,
            item.survivor_source,
            item.survivor_target,
            item.survivor_id,
        ),
    )


def metadata_dict(edge: dict[str, Any]) -> dict[str, Any]:
    value = edge.get("metadata")
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            return {}
    return value if isinstance(value, dict) else {}


def missing_metadata_keys(
    survivor: dict[str, Any], doomed: dict[str, Any]
) -> list[str]:
    survivor_metadata = metadata_dict(survivor)
    doomed_metadata = metadata_dict(doomed)
    empty = (None, "", [], {})
    return sorted(
        key
        for key, value in doomed_metadata.items()
        if value not in empty
        and (key not in survivor_metadata or survivor_metadata.get(key) in empty)
    )


def summarize_plan(edges: list[dict[str, Any]], plan: list[PairPlan]) -> dict[str, Any]:
    by_id = {str(edge["edge_id"]): edge for edge in edges}
    per_relation = collections.Counter(item.survivor_relation for item in plan)
    per_direction = collections.Counter(
        (item.survivor_relation, item.doomed_relation) for item in plan
    )
    candidate_samples: list[dict[str, Any]] = []
    merge_count = 0
    for item in plan:
        missing = missing_metadata_keys(by_id[item.survivor_id], by_id[item.doomed_id])
        if missing:
            merge_count += 1
            candidate_samples.append(
                {
                    **item.as_dict(),
                    "metadata_keys_copied": missing,
                }
            )
    merge_samples: list[dict[str, Any]] = []
    sampled_relations: set[str] = set()
    for sample in candidate_samples:
        relation = str(sample["survivor_relation"])
        if relation not in sampled_relations:
            merge_samples.append(sample)
            sampled_relations.add(relation)
        if len(merge_samples) == 10:
            break
    if len(merge_samples) < 10:
        sampled_ids = {str(sample["survivor_id"]) for sample in merge_samples}
        merge_samples.extend(
            sample
            for sample in candidate_samples
            if str(sample["survivor_id"]) not in sampled_ids
        )
        merge_samples = merge_samples[:10]
    return {
        "edges_before": len(edges),
        "pairs": len(plan),
        "edges_after": len(edges) - len(plan),
        "survivors_with_missing_metadata": merge_count,
        "counts_per_relation": dict(sorted(per_relation.items())),
        "counts_per_direction": {
            f"{survivor} <- {doomed}": count
            for (survivor, doomed), count in sorted(per_direction.items())
        },
        "merge_samples": merge_samples,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--edges", type=Path, default=DEFAULT_EDGES)
    parser.add_argument("--ontology", type=Path, default=DEFAULT_ONTOLOGY)
    parser.add_argument(
        "--json", action="store_true", help="print the full plan as JSON"
    )
    args = parser.parse_args()

    edges = read_jsonl(args.edges)
    edge_types = load_edge_types(args.ontology)
    plan = build_plan(edges, edge_types)
    summary = summarize_plan(edges, plan)
    if args.json:
        print(
            json.dumps(
                {
                    "policy": policy_rows(edge_types),
                    "summary": summary,
                    "pairs": [item.as_dict() for item in plan],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        print("inverse-normalization plan (read-only)")
        print(
            f"edges {summary['edges_before']} -> {summary['edges_after']}; "
            f"materialized inverse pairs: {summary['pairs']}"
        )
        for relation, count in summary["counts_per_relation"].items():
            print(f"  {relation}: {count}")
        print(
            "survivors missing metadata supplied by twin: "
            f"{summary['survivors_with_missing_metadata']}"
        )
        print("read-only: nothing written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
