#!/usr/bin/env python3
"""Gate and optionally apply the 2026-08-17 reading-ingestion wave A.

Idempotently merges ``scripts/data_2026_08_17_reading_wave_a.json`` into
``data/kg/{nodes,edges}.jsonl`` and promotes an existing Origenality shell:

- existing node ids and edge triples are skipped;
- R2 identity keys are checked against the live snapshot before new people or
  publications are accepted;
- enrichment targets must exist and satisfy exact preconditions before fields
  such as ``citation_verdict`` and ``source_rank`` may be replaced;
- all endpoints must resolve and reverse dialectical duplicates are refused;
- the novel node/edge subset must pass ``check_ingestion_rules.py --new-only``
  with BLOCK 0 before anything is written;
- because this wave adds ``opposes`` edges, ``--apply`` also requires the G6
  reachability pin to equal the exact post-apply count;
- backups use suffix ``.bak-reading_a``.

Usage: python3 scripts/ingest_2026_08_17_reading_wave_a.py [--apply]
Default is dry-run.
"""
from __future__ import annotations

import argparse
import copy
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
NODES = ROOT / "data/kg/nodes.jsonl"
EDGES = ROOT / "data/kg/edges.jsonl"
DELTA = ROOT / "scripts/data_2026_08_17_reading_wave_a.json"
GATE = ROOT / "scripts/check_ingestion_rules.py"
G6_PROBE = ROOT / "graphrag/tests/g6/test_reachability_probe.py"
BAK_SUFFIX = ".bak-reading_a"
INGEST_SCRIPT = "scripts/ingest_2026_08_17_reading_wave_a.py"
PROMOTION_STAMP = "reading_wave_a_2026_08_17"
PY2_EXCEPT = "except TypeError, ValueError:"
PY3_EXCEPT = "except (TypeError, ValueError):"
DIALECTICAL_RELATIONS = {
    "opposes",
    "critiques",
    "responds_to",
    "refutes",
    "contrasts_with",
    "agrees_with",
    "supports",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="write the gated delta; otherwise perform a dry-run",
    )
    return parser.parse_args()


def read_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def metadata(node: dict) -> dict:
    value = node.get("metadata") or {}
    return json.loads(value) if isinstance(value, str) else value


def set_metadata(node: dict, value: dict) -> None:
    if isinstance(node.get("metadata"), str):
        node["metadata"] = json.dumps(value, ensure_ascii=False)
    else:
        node["metadata"] = value


def triple(edge: dict) -> tuple[str, str, str]:
    return (
        edge["source"],
        edge.get("relation") or edge.get("type"),
        edge["target"],
    )


def normalized(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value)
    asciiish = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+", " ", asciiish.lower()).strip()


def person_identity(node: dict) -> tuple[str, str]:
    return ("person", normalized(node.get("label") or ""))


def publication_identity(node: dict) -> tuple[str, ...]:
    md = metadata(node)
    doi = str(md.get("doi") or "").strip().lower()
    if doi:
        return ("publication-doi", doi)
    return (
        "publication-fallback",
        str(md.get("author_id") or ""),
        str(md.get("year") or ""),
        normalized(str(md.get("title") or node.get("label") or "")),
    )


def assert_delta_invariants(delta: dict) -> None:
    assert set(delta) == {"nodes", "edges", "enrichments"}, (
        "delta must contain nodes, edges, and enrichments only"
    )
    assert all(isinstance(delta[key], list) for key in delta)

    node_ids = [node["id"] for node in delta["nodes"]]
    assert len(node_ids) == len(set(node_ids)), "duplicate node id within delta"
    identity_keys: list[tuple[str, ...]] = []
    for node in delta["nodes"]:
        assert node["id"] == node["node_id"], f"id/node_id mismatch: {node['id']}"
        md = metadata(node)
        provenance = md.get("provenance")
        assert isinstance(provenance, dict), f"missing provenance: {node['id']}"
        assert provenance.get("source"), f"missing provenance source: {node['id']}"
        assert provenance.get("ingested_at"), f"missing ingested_at: {node['id']}"
        assert provenance.get("ingest_script") == INGEST_SCRIPT

        if node["type"] == "person":
            identity_keys.append(person_identity(node))
        elif node["type"] == "publication":
            identity_keys.append(publication_identity(node))
            assert md.get("citation_verdict") == "read_and_extracted"
            assert md.get("source_rank")
            assert str(md.get("source_file") or "").endswith(".pdf")
        elif node["type"] == "argument":
            assert node["id"].startswith("scholarly_argument_")
            assert md.get("scholar_id"), f"missing scholar_id: {node['id']}"
            assert md.get("scholarly_work_id"), (
                f"missing scholarly_work_id: {node['id']}"
            )
            assert md.get("page_range"), f"missing page_range: {node['id']}"
            source_file = str(md.get("source_file") or "")
            assert source_file.endswith(".pdf"), (
                f"source_file must be a PDF path: {node['id']}"
            )
            assert provenance["source"] == source_file, (
                f"source_file/provenance mismatch: {node['id']}"
            )
            ancient_run = re.search(r"[\u0370-\u03ff\u1f00-\u1fff]", node["description"])
            assert ancient_run is None, (
                f"generated argument description contains Greek script: {node['id']}"
            )
    assert len(identity_keys) == len(set(identity_keys)), (
        "duplicate person/publication identity key within delta"
    )

    edge_ids = [edge["edge_id"] for edge in delta["edges"]]
    assert len(edge_ids) == len(set(edge_ids)), "duplicate edge id within delta"
    triples = [triple(edge) for edge in delta["edges"]]
    assert len(triples) == len(set(triples)), "duplicate edge triple within delta"
    for edge in delta["edges"]:
        assert edge["source"] == edge["source_id"]
        assert edge["target"] == edge["target_id"]
        assert edge["source"] != edge["target"]
        if edge["relation"] in DIALECTICAL_RELATIONS:
            attestation = edge.get("metadata", {}).get("attested_by", "")
            assert attestation and re.search(
                r"\b(?:p{1,2}\.|pages?)\s*\d", attestation
            ), f"dialectical edge lacks paged attestation: {edge['edge_id']}"

    delta_triples = set(triples)
    for node in delta["nodes"]:
        if node["type"] != "argument":
            continue
        node_id = node["id"]
        md = metadata(node)
        assert (node_id, "created_by", md["scholar_id"]) in delta_triples
        assert (node_id, "advanced_in", md["scholarly_work_id"]) in delta_triples

    target_ids = [row["target_id"] for row in delta["enrichments"]]
    assert len(target_ids) == len(set(target_ids)), "duplicate enrichment target"
    for row in delta["enrichments"]:
        assert row.get("preconditions"), f"missing enrichment preconditions: {row}"
        updates = row.get("metadata") or {}
        assert updates.get("citation_verdict") == "read_and_extracted"
        assert updates.get("source_rank")
        assert str(updates.get("source_file") or "").endswith(".pdf")


def check_identity_collisions(
    delta_nodes: list[dict], existing_nodes: list[dict]
) -> list[str]:
    existing_people: dict[tuple[str, str], str] = {}
    existing_publications: dict[tuple[str, ...], str] = {}
    for node in existing_nodes:
        if node.get("type") == "person":
            existing_people.setdefault(person_identity(node), node["id"])
        elif node.get("type") == "publication":
            existing_publications.setdefault(publication_identity(node), node["id"])

    collisions: list[str] = []
    existing_ids = {node["id"] for node in existing_nodes}
    for node in delta_nodes:
        if node["id"] in existing_ids:
            continue
        if node["type"] == "person":
            other = existing_people.get(person_identity(node))
        elif node["type"] == "publication":
            other = existing_publications.get(publication_identity(node))
        else:
            other = None
        if other and other != node["id"]:
            collisions.append(f"{node['id']} duplicates {other}")
    return collisions


def enrichment_state(
    enrichments: list[dict], by_id: dict[str, dict]
) -> tuple[list[tuple[dict, dict]], int, list[str]]:
    ready: list[tuple[dict, dict]] = []
    already = 0
    failures: list[str] = []
    for row in enrichments:
        target_id = row["target_id"]
        target = by_id.get(target_id)
        if target is None:
            failures.append(f"{target_id}: target does not exist")
            continue
        md = metadata(target)
        updates = row.get("metadata") or {}
        if all(md.get(key) == value for key, value in updates.items()):
            already += 1
            continue

        preconditions = row.get("preconditions") or {}
        if target.get("type") != preconditions.get("type"):
            failures.append(
                f"{target_id}: type precondition expected "
                f"{preconditions.get('type')!r}, got {target.get('type')!r}"
            )
            continue
        if target.get("label") != preconditions.get("label"):
            failures.append(f"{target_id}: label precondition failed")
            continue
        mismatch = []
        for key, expected in (preconditions.get("metadata_equals") or {}).items():
            if md.get(key) != expected:
                mismatch.append(f"{key}: expected {expected!r}, got {md.get(key)!r}")
        if mismatch:
            failures.append(f"{target_id}: " + "; ".join(mismatch))
            continue
        ready.append((target, updates))
    return ready, already, failures


def pinned_opposes_count() -> int:
    source = G6_PROBE.read_text(encoding="utf-8")
    match = re.search(r"assert len\(all_opposes\) == (\d+)", source)
    if not match:
        raise AssertionError(f"cannot locate G6 opposes pin in {G6_PROBE}")
    return int(match.group(1))


def run_ingestion_gate(
    new_nodes: list[dict], new_edges: list[dict]
) -> tuple[subprocess.CompletedProcess[str], int]:
    """Run the repository gate in a temporary mirror.

    The live shared relation module currently contains one parser-invalid
    Python-2 exception spelling.  As in the established central-debates
    applier, only that exact spelling is normalized in the temporary mirrored
    dependency.  The repository gate itself and every live repository file
    remain byte-for-byte untouched.
    """

    with tempfile.TemporaryDirectory(prefix="reading-wave-a-gate-") as tmp_name:
        sandbox = Path(tmp_name)
        (sandbox / "scripts").mkdir(parents=True)
        (sandbox / "data/kg").mkdir(parents=True)
        (sandbox / "knowledge graph/ontology").mkdir(parents=True)
        shared = (
            sandbox
            / "graphrag/src/eleutheria_graphrag/agents/dialectical_relations.py"
        )
        shared.parent.mkdir(parents=True)

        shutil.copy2(GATE, sandbox / "scripts/check_ingestion_rules.py")
        shutil.copy2(NODES, sandbox / "data/kg/nodes.jsonl")
        shutil.copy2(EDGES, sandbox / "data/kg/edges.jsonl")
        for name in ("edge_types.json", "period_scheme.json", "school_scheme.json"):
            shutil.copy2(
                ROOT / "knowledge graph/ontology" / name,
                sandbox / "knowledge graph/ontology" / name,
            )

        shared_source = (
            ROOT
            / "graphrag/src/eleutheria_graphrag/agents/dialectical_relations.py"
        ).read_text(encoding="utf-8")
        substitutions = shared_source.count(PY2_EXCEPT)
        shared.write_text(
            shared_source.replace(PY2_EXCEPT, PY3_EXCEPT), encoding="utf-8"
        )

        subset = sandbox / "reading_wave_a_novel.json"
        subset.write_text(
            json.dumps(
                {"nodes": new_nodes, "edges": new_edges},
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        result = subprocess.run(
            [
                sys.executable,
                str(sandbox / "scripts/check_ingestion_rules.py"),
                "--new-only",
                str(subset),
            ],
            cwd=sandbox,
            capture_output=True,
            text=True,
            check=False,
        )
        return result, substitutions


def main() -> int:
    args = parse_args()
    delta = json.loads(DELTA.read_text(encoding="utf-8"))
    assert_delta_invariants(delta)

    nodes = read_jsonl(NODES)
    edges = read_jsonl(EDGES)
    by_id = {node["id"]: node for node in nodes}
    existing_ids = set(by_id)
    existing_triples = {triple(edge) for edge in edges}
    existing_edge_ids = {
        edge.get("edge_id") for edge in edges if edge.get("edge_id")
    }

    collisions = check_identity_collisions(delta["nodes"], nodes)
    if collisions:
        print(f"FATAL: {len(collisions)} R2 identity collisions: {collisions[:5]}")
        return 1

    new_nodes: list[dict] = []
    incompatible_existing: list[str] = []
    for node in delta["nodes"]:
        current = by_id.get(node["id"])
        if current is None:
            new_nodes.append(node)
        elif current.get("type") != node.get("type") or current.get("label") != node.get("label"):
            incompatible_existing.append(node["id"])
    if incompatible_existing:
        print(
            "FATAL: existing node ids have incompatible type/label: "
            f"{incompatible_existing[:5]}"
        )
        return 1

    all_ids = existing_ids | {node["id"] for node in delta["nodes"]}
    new_edges: list[dict] = []
    skipped_edges = 0
    unresolved: list[tuple[str, str, str]] = []
    edge_id_collisions: list[str] = []
    reverse_dialectical: list[tuple[str, str, str]] = []
    seen_triples = set(existing_triples)
    for edge in delta["edges"]:
        edge_triple = triple(edge)
        if edge_triple in seen_triples:
            skipped_edges += 1
            continue
        if edge["source"] not in all_ids or edge["target"] not in all_ids:
            unresolved.append(edge_triple)
            continue
        if edge["edge_id"] in existing_edge_ids:
            edge_id_collisions.append(edge["edge_id"])
            continue
        reverse = (edge["target"], edge["relation"], edge["source"])
        if edge["relation"] in DIALECTICAL_RELATIONS and reverse in seen_triples:
            reverse_dialectical.append(edge_triple)
            continue
        new_edges.append(edge)
        seen_triples.add(edge_triple)

    ready_enrichments, already_enriched, enrichment_failures = enrichment_state(
        delta["enrichments"], by_id
    )

    skipped_nodes = len(delta["nodes"]) - len(new_nodes)
    print(
        f"delta: {len(delta['nodes'])} nodes / {len(delta['edges'])} edges / "
        f"{len(delta['enrichments'])} enrichments"
    )
    print(
        f"novel: {len(new_nodes)} nodes / {len(new_edges)} edges "
        f"(skipped existing: {skipped_nodes} nodes, {skipped_edges} edges)"
    )
    print(
        f"promotions: ready={len(ready_enrichments)}, "
        f"already-applied={already_enriched}, failed={len(enrichment_failures)}"
    )

    failures: list[tuple[str, list]] = [
        ("unresolvable endpoints", unresolved),
        ("edge-id collisions", edge_id_collisions),
        ("reverse dialectical duplicates", reverse_dialectical),
        ("enrichment precondition failures", enrichment_failures),
    ]
    for label, rows in failures:
        if rows:
            print(f"FATAL: {len(rows)} {label}: {rows[:5]}")
    if any(rows for _, rows in failures):
        print("nothing written")
        return 1

    current_opposes = sum(edge.get("relation") == "opposes" for edge in edges)
    novel_opposes = sum(edge["relation"] == "opposes" for edge in new_edges)
    post_apply_opposes = current_opposes + novel_opposes
    g6_pin = pinned_opposes_count()
    print(
        f"opposes: current={current_opposes}, novel={novel_opposes}, "
        f"post-apply={post_apply_opposes}, g6-pin={g6_pin}"
    )

    gate, gate_substitutions = run_ingestion_gate(new_nodes, new_edges)
    print("--- check_ingestion_rules.py --new-only (temporary mirror) ---")
    print(
        "temporary parser normalisations: "
        f"{gate_substitutions} (shared dependency only; repository unchanged)"
    )
    if gate.stdout.strip():
        print(gate.stdout.rstrip())
    if gate.stderr.strip():
        print(gate.stderr.rstrip(), file=sys.stderr)
    if gate.returncode != 0:
        print("FATAL: ingestion gate failed on the novel subset - nothing written")
        return 1

    merged_nodes = nodes + new_nodes
    merged_ids = {node["id"] for node in merged_nodes}
    assert len(merged_ids) == len(merged_nodes), "duplicate node id after merge"
    assert all(
        edge["source"] in merged_ids and edge["target"] in merged_ids
        for edge in new_edges
    )

    if not args.apply:
        if novel_opposes:
            print(
                "dry-run: nothing written; future --apply requires the G6 "
                f"opposes pin to be {post_apply_opposes} (currently {g6_pin})"
            )
        else:
            print("dry-run: nothing written (use --apply)")
        return 0

    if novel_opposes and g6_pin != post_apply_opposes:
        print(
            f"FATAL: G6 opposes pin is {g6_pin}, but post-apply count is "
            f"{post_apply_opposes}; update the pin in the same commit before --apply"
        )
        print("nothing written")
        return 1

    if not new_nodes and not new_edges and not ready_enrichments:
        print("applied: no changes needed (delta already present)")
        return 0

    promoted_nodes = copy.deepcopy(merged_nodes)
    promoted_by_id = {node["id"]: node for node in promoted_nodes}
    for original_target, updates in ready_enrichments:
        target = promoted_by_id[original_target["id"]]
        md = dict(metadata(target))
        md.update(updates)
        md["reading_a_promotion_stamp"] = PROMOTION_STAMP
        set_metadata(target, md)
        target["updated_at"] = "2026-08-17 00:00:00+00:00"

    shutil.copy2(NODES, str(NODES) + BAK_SUFFIX)
    shutil.copy2(EDGES, str(EDGES) + BAK_SUFFIX)
    NODES.write_text(
        "".join(
            json.dumps(node, ensure_ascii=False) + "\n" for node in promoted_nodes
        ),
        encoding="utf-8",
    )
    with EDGES.open("a", encoding="utf-8") as handle:
        for edge in new_edges:
            handle.write(json.dumps(edge, ensure_ascii=False) + "\n")
    print(
        f"applied: +{len(new_nodes)} nodes, +{len(new_edges)} edges, "
        f"{len(ready_enrichments)} shell promotions"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
