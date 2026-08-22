#!/usr/bin/env python3
"""Frozen evidence policy for eliminating the historical R16 debt.

The live graph contained 518 edges in Scholar-RAG's rendered fault-line
relation set without ``metadata.attested_by``.  This module audits that closed
population.  It never treats a date, confidence score, generic bibliography,
or mere thematic similarity as evidence for a directed relation.

Retentions require one of three things:

* an existing edge field that states the relation and gives a page/locus;
* a primary passage locus already carried by the source endpoint; or
* a citation-verified source argument/work/synthesis whose verified reference
  gives a locus and whose target is the concept/school/debate it instantiates.

Everything else is deleted by the companion applier.  The baseline digest
freezes every edge id, triple, and metadata object before any edit is allowed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
NODES_PATH = ROOT / "data" / "kg" / "nodes.jsonl"
EDGES_PATH = ROOT / "data" / "kg" / "edges.jsonl"

STAMP = "dialectic_zero_2026_08_18"

FAULT_LINE_RELATIONS = frozenset(
    {
        "opposes",
        "critiques",
        "responds_to",
        "refutes",
        "contrasts_with",
        "agrees_with",
        "supports",
    }
)

EXPECTED_NODE_COUNT = 20_271
EXPECTED_EDGE_COUNT_BEFORE = 50_169
EXPECTED_UNATTESTED_COUNT = 518
EXPECTED_EDGE_COUNT_AFTER = 49_840
EXPECTED_RETAINED_COUNT = 189
EXPECTED_DELETED_COUNT = 329

EXPECTED_UNATTESTED_BY_RELATION = {
    "agrees_with": 5,
    "contrasts_with": 5,
    "critiques": 263,
    "opposes": 5,
    "responds_to": 59,
    "supports": 181,
}

EXPECTED_PLAN_BY_RELATION = {
    "agrees_with": {"retain": 4, "delete": 1},
    "contrasts_with": {"retain": 0, "delete": 5},
    "critiques": {"retain": 98, "delete": 165},
    "opposes": {"retain": 2, "delete": 3},
    "responds_to": {"retain": 11, "delete": 48},
    "supports": {"retain": 74, "delete": 107},
}

EXPECTED_FAULT_LINES_AFTER = {
    "agrees_with": 22,
    "contrasts_with": 3,
    "critiques": 122,
    "opposes": 21,
    "responds_to": 18,
    "supports": 74,
}

# Filled from the exact canonical payload produced by ``--print-constants``.
EXPECTED_UNATTESTED_BASELINE_SHA256 = (
    "0721cef735a6858c92801d3a821a3f2933e308a80bc56c14ee0e73a2d0180b3d"
)
EXPECTED_PLAN_SHA256 = (
    "6c0af062192dbd8b61d8a0d4976207367c5a0beb44b1626d1ab3d638cb31988d"
)

# The 2026-08-17 repair explicitly found no attestation for these two edges.
# A page mentioned in the audit note is a negative finding, not evidence.
KNOWN_NEGATIVE_EDGE_IDS = frozenset(
    {
        "9fba7de0-3c0e-4a63-b563-aa94572fe7b1",
        "d319ccd0-b346-4fb1-9342-6e5fdc654782",
    }
)

# These whole-work loci directly identify their opponent.  They are retained
# deliberately rather than by a broad title/year heuristic.
MANUAL_LOCUS_SPECS: dict[str, tuple[str, str]] = {
    "ca145b96-6ac5-4846-b107-419e457cfb90": (
        "target_verified_reference",
        "Origen's Contra Celsum is an explicit answer to Celsus' True Doctrine",
    ),
    "r3_5_critiques": (
        "edge_basis",
        "the cited work is De aeternitate mundi contra Proclum",
    ),
    "r3_6_critiques": (
        "edge_basis",
        "the cited work is De aeternitate mundi contra Aristotelem",
    ),
    "cdff07f3-7298-496d-ba62-47f53b87c430": (
        "publication_and_summary",
        "the article is a full, explicitly identified refutation of Huby",
    ),
}

# Ordered: use the most evidence-specific field when more than one qualifies.
DIRECT_EVIDENCE_KEYS = (
    "amand_evidence",
    "amand_source",
    "dihle_source",
    "verification_source",
    "relation_basis",
    "furst_source",
    "destree2014_source",
    "basis",
    "pages",
    "summary",
    "frede_note",
    "evidence",
    "source",
    "rationale",
    "note",
)

# Years alone do not match.  ``fragm`` and similar abbreviations require a
# following locator, preventing prose such as "fragments preserved" from being
# mistaken for a citation.
LOCATOR_RE = re.compile(
    r"""(?ix)(?:
        \bpp?\.?\s*(?:~?\d{1,3}|[ivxlcdm]{1,8})\b
      | \bpages?\s*\d
      | \b(?:ch(?:apter)?|lect(?:ure)?|bk|book|hom|frag(?:m)?|q|§|n)\.?
          \b\s*(?:[ivxlcdm]{1,8}|\d{1,3})\b
      | \b[IVXLCDM]{1,8}\.\d+(?:[.\-–]\d+)*
      | \b\d{1,3}\.\d+(?:\.\d+)*
      | \b\d{1,3}:\d+(?:[-–]\d+)?
      | \b\d{2,3}[a-z]\d+
      | urn:cts:
      | \b(?:Fat|Orat|Apol|Adv|HE|NA|ST|SCG|CCSL|PL)\.?
          \s*[IVXLCDM\d]
      | \b(?:18|19|20)\d{2}\s*[:,]\s*\d{1,3}
    )"""
)


@dataclass(frozen=True)
class Repair:
    """One exact, evidence-reviewed operation."""

    edge_id: str
    source: str
    relation: str
    target: str
    metadata_sha256: str
    action: str
    bucket: str
    attested_by: str | None
    rationale: str


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def node_id(node: dict[str, Any]) -> str:
    return str(node.get("node_id") or node.get("id") or "")


def metadata(obj: dict[str, Any]) -> dict[str, Any]:
    value = obj.get("metadata")
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            return {}
    return value if isinstance(value, dict) else {}


def canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode()).hexdigest()


def edge_metadata_sha256(edge: dict[str, Any]) -> str:
    """Hash the metadata in its exact stored shape, string or object."""

    return sha256_json(edge.get("metadata"))


def edge_is_attested(edge: dict[str, Any]) -> bool:
    value = metadata(edge).get("attested_by")
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, list):
        return any(str(item).strip() for item in value)
    return False


def unattested_population(
    edges: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        edge
        for edge in edges
        if edge.get("relation") in FAULT_LINE_RELATIONS and not edge_is_attested(edge)
    ]


def baseline_payload(population: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Freeze the exact id/triple/metadata preconditions for all 518 edges."""

    return sorted(
        (
            {
                "edge_id": edge.get("edge_id"),
                "source": edge.get("source"),
                "relation": edge.get("relation"),
                "target": edge.get("target"),
                "metadata": edge.get("metadata"),
            }
            for edge in population
        ),
        key=lambda row: str(row["edge_id"]),
    )


def has_locator(value: Any) -> bool:
    return isinstance(value, str) and bool(LOCATOR_RE.search(value))


def direct_edge_evidence(edge: dict[str, Any]) -> tuple[str, str] | None:
    data = metadata(edge)
    for key in DIRECT_EVIDENCE_KEYS:
        value = data.get(key)
        if has_locator(value):
            return key, value
    return None


def primary_locus(node: dict[str, Any]) -> str | None:
    data = metadata(node)
    locator = (
        data.get("canonical_ref")
        or data.get("reference")
        or data.get("cts_urn")
        or data.get("synthesis_of_urn")
    )
    if not isinstance(locator, str) or not locator.strip():
        return None
    parts = [str(node.get("label") or node_id(node)), locator.strip()]
    urn = data.get("cts_urn") or data.get("synthesis_of_urn")
    if isinstance(urn, str) and urn.strip() and urn.strip() not in parts:
        parts.append(urn.strip())
    return "; ".join(dict.fromkeys(parts))


def verified_reference(node: dict[str, Any]) -> str | None:
    value = metadata(node).get("verified_reference")
    return value if has_locator(value) else None


def manual_locus(
    edge: dict[str, Any],
    source_node: dict[str, Any],
    target_node: dict[str, Any],
) -> tuple[str, str] | None:
    spec = MANUAL_LOCUS_SPECS.get(str(edge.get("edge_id")))
    if spec is None:
        return None
    mode, rationale = spec
    if mode == "target_verified_reference":
        evidence = metadata(target_node).get("verified_reference")
    elif mode == "edge_basis":
        evidence = metadata(edge).get("basis")
    elif mode == "publication_and_summary":
        publication = metadata(source_node).get("verified_reference")
        summary = metadata(edge).get("summary")
        evidence = f"{publication} Relation note: {summary}"
    else:  # pragma: no cover - the closed mapping above makes this unreachable
        raise AssertionError(f"unknown manual-locus mode: {mode}")
    if not isinstance(evidence, str) or not evidence.strip():
        raise AssertionError(f"manual locus disappeared for {edge.get('edge_id')}")
    return evidence.strip(), rationale


def classify_edge(
    edge: dict[str, Any],
    nodes: dict[str, dict[str, Any]],
) -> tuple[str, str, str | None, str]:
    """Return action, bucket, attestation, and editorial rationale."""

    edge_id = str(edge["edge_id"])
    source_node = nodes[edge["source"]]
    target_node = nodes[edge["target"]]
    source_data = metadata(source_node)
    edge_data = metadata(edge)
    source_type = source_node.get("type") or source_node.get("node_type")
    target_type = target_node.get("type") or target_node.get("node_type")

    if edge_id in KNOWN_NEGATIVE_EDGE_IDS:
        return (
            "delete",
            "known_negative",
            None,
            "the prior source audit expressly found no attestation",
        )

    manual = manual_locus(edge, source_node, target_node)
    if manual is not None:
        evidence, rationale = manual
        return "retain", "manual_whole_work_locus", evidence, rationale

    direct = direct_edge_evidence(edge)
    if direct is not None:
        key, evidence = direct
        if key == "pages":
            # A bare page such as "437 n.15" is precise but not self-contained.
            # Prefix only the existing source label; no bibliographic fact is
            # inferred or added.
            evidence = f"{source_node.get('label')}; {evidence}"
        return (
            "retain",
            "edge_locator",
            evidence,
            f"existing metadata.{key} states this relation at a page/locus",
        )

    if source_type == "passage":
        if edge.get("relation") == "responds_to":
            return (
                "delete",
                "comparative_not_response",
                None,
                "shared subject matter is not evidence of a historical response",
            )
        evidence = primary_locus(source_node)
        if evidence is not None:
            return (
                "retain",
                "primary_locus",
                evidence,
                "the source passage and its canonical locus directly ground the link",
            )

    reference = verified_reference(source_node)
    citation_ok = source_data.get("citation_verified") is True and source_data.get(
        "citation_verdict"
    ) in {"verified", "corrected"}

    if source_type == "synthesis" and reference is not None:
        primary_support = (
            edge.get("relation") == "supports"
            and target_type == "argument"
            and edge_data.get("relevance") == "primary"
        )
        frede_dihle = (
            edge.get("relation") == "critiques"
            and edge.get("target") == "scholar_albrecht_dihle"
        )
        if source_data.get("citation_verified") is True and (
            primary_support or frede_dihle
        ):
            return (
                "retain",
                "verified_endpoint_locus",
                reference,
                "the verified synthesis endpoint gives the precise pages/loci",
            )

    if (
        source_type == "argument"
        and target_type in {"concept", "school", "debate"}
        and citation_ok
        and reference is not None
    ):
        return (
            "retain",
            "verified_endpoint_locus",
            reference,
            "the verified argument endpoint gives the precise pages/loci",
        )

    if (
        source_type == "work"
        and target_type in {"concept", "school", "work", "argument"}
        and citation_ok
        and reference is not None
    ):
        return (
            "retain",
            "verified_endpoint_locus",
            reference,
            "the verified work endpoint gives the precise pages/loci",
        )

    return (
        "delete",
        "no_relation_specific_attestation",
        None,
        "no page/locus in existing provenance attests this directed relation",
    )


def build_plan(
    nodes_list: list[dict[str, Any]],
    edges: list[dict[str, Any]],
) -> list[Repair]:
    nodes = {node_id(node): node for node in nodes_list}
    if len(nodes) != len(nodes_list):
        raise AssertionError("duplicate node ids prevent an exact repair plan")

    population = unattested_population(edges)
    repairs: list[Repair] = []
    for edge in sorted(population, key=lambda row: str(row.get("edge_id"))):
        edge_id = str(edge.get("edge_id") or "")
        if not edge_id:
            raise AssertionError("unattested fault-line edge without edge_id")
        if edge["source"] not in nodes or edge["target"] not in nodes:
            raise AssertionError(f"unresolved endpoint on {edge_id}")
        action, bucket, attestation, rationale = classify_edge(edge, nodes)
        repairs.append(
            Repair(
                edge_id=edge_id,
                source=str(edge["source"]),
                relation=str(edge["relation"]),
                target=str(edge["target"]),
                metadata_sha256=edge_metadata_sha256(edge),
                action=action,
                bucket=bucket,
                attested_by=attestation,
                rationale=rationale,
            )
        )
    if len({repair.edge_id for repair in repairs}) != len(repairs):
        raise AssertionError("duplicate edge ids prevent an exact repair plan")
    return repairs


def plan_payload(plan: list[Repair]) -> list[dict[str, Any]]:
    return [
        {
            "edge_id": repair.edge_id,
            "source": repair.source,
            "relation": repair.relation,
            "target": repair.target,
            "metadata_sha256": repair.metadata_sha256,
            "action": repair.action,
            "bucket": repair.bucket,
            "attested_by": repair.attested_by,
            "rationale": repair.rationale,
        }
        for repair in plan
    ]


def plan_counts(plan: list[Repair]) -> dict[str, dict[str, int]]:
    counts: dict[str, dict[str, int]] = {}
    for relation in sorted(FAULT_LINE_RELATIONS):
        row = Counter(repair.action for repair in plan if repair.relation == relation)
        if row:
            counts[relation] = {"retain": row["retain"], "delete": row["delete"]}
    return counts


def assert_frozen_baseline(
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    plan: list[Repair],
) -> None:
    population = unattested_population(edges)
    by_relation = Counter(str(edge.get("relation")) for edge in population)
    baseline_digest = sha256_json(baseline_payload(population))
    current_plan_digest = sha256_json(plan_payload(plan))

    assert len(nodes) == EXPECTED_NODE_COUNT, (
        f"node count moved: {len(nodes)} != {EXPECTED_NODE_COUNT}"
    )
    assert len(edges) == EXPECTED_EDGE_COUNT_BEFORE, (
        f"edge count moved: {len(edges)} != {EXPECTED_EDGE_COUNT_BEFORE}"
    )
    assert len(population) == EXPECTED_UNATTESTED_COUNT
    assert dict(sorted(by_relation.items())) == EXPECTED_UNATTESTED_BY_RELATION
    assert baseline_digest == EXPECTED_UNATTESTED_BASELINE_SHA256, (
        "the exact id/triple/metadata baseline moved: "
        f"{baseline_digest} != {EXPECTED_UNATTESTED_BASELINE_SHA256}"
    )
    assert len(plan) == EXPECTED_UNATTESTED_COUNT
    assert sum(repair.action == "retain" for repair in plan) == (
        EXPECTED_RETAINED_COUNT
    )
    assert sum(repair.action == "delete" for repair in plan) == (EXPECTED_DELETED_COUNT)
    assert plan_counts(plan) == EXPECTED_PLAN_BY_RELATION
    assert current_plan_digest == EXPECTED_PLAN_SHA256, (
        f"repair plan moved: {current_plan_digest} != {EXPECTED_PLAN_SHA256}"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--details",
        action="store_true",
        help="print the per-edge audit as tab-separated rows",
    )
    parser.add_argument(
        "--print-constants",
        action="store_true",
        help="print frozen digests while authoring this additive checkpoint",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    nodes = read_jsonl(NODES_PATH)
    edges = read_jsonl(EDGES_PATH)
    population = unattested_population(edges)
    plan = build_plan(nodes, edges)

    if args.print_constants:
        print(
            "EXPECTED_UNATTESTED_BASELINE_SHA256 =",
            sha256_json(baseline_payload(population)),
        )
        print("EXPECTED_PLAN_SHA256 =", sha256_json(plan_payload(plan)))
        print("plan_counts =", canonical_json(plan_counts(plan)))
        print(
            "actions =",
            canonical_json(Counter(repair.action for repair in plan)),
        )
        print(
            "buckets =",
            canonical_json(Counter(repair.bucket for repair in plan)),
        )
        return 0

    assert_frozen_baseline(nodes, edges, plan)
    print(
        "dialectic-zero: "
        f"{len(plan)} audited; {EXPECTED_RETAINED_COUNT} retain; "
        f"{EXPECTED_DELETED_COUNT} delete; projected R16 debt 0"
    )
    print("by relation:", canonical_json(plan_counts(plan)))

    if args.details:
        print("action\trelation\tedge_id\tsource\ttarget\tbucket\trationale")
        for repair in plan:
            print(
                "\t".join(
                    (
                        repair.action,
                        repair.relation,
                        repair.edge_id,
                        repair.source,
                        repair.target,
                        repair.bucket,
                        repair.rationale,
                    )
                )
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
