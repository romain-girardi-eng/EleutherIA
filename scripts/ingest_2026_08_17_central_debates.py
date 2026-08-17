#!/usr/bin/env python3
"""Gate and optionally apply the six central-debate editorial frames.

Default execution is a dry-run.  It validates the additive delta, checks every
dialectical attestation, rejects duplicate triples in either direction, runs
``check_ingestion_rules.py --new-only`` in a temporary mirror, and executes the
real ``BuildControversyFrameTool`` before/after against a temporary KG copy.

The live renderer dependencies currently contain three legacy
``except TypeError, ValueError`` spellings which Python 3 cannot parse.  The
dry-run normalises only those exact spellings in memory (and in the temporary
gate mirror); no renderer, gate, KG, or corpus source file is modified.

If the delta adds ``opposes``, ``--apply`` also refuses unless the G6 reachability
probe already pins the exact post-apply count.  This script never updates that
pin itself.

Usage:
    python3 scripts/ingest_2026_08_17_central_debates.py
    python3 scripts/ingest_2026_08_17_central_debates.py --dry-run
    python3 scripts/ingest_2026_08_17_central_debates.py --apply
"""

from __future__ import annotations

import argparse
import asyncio
import collections
import importlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import types
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
NODES = ROOT / "data/kg/nodes.jsonl"
EDGES = ROOT / "data/kg/edges.jsonl"
DELTA = ROOT / "scripts/data_2026_08_17_central_debates.json"
GATE = ROOT / "scripts/check_ingestion_rules.py"
G6_PROBE = ROOT / "graphrag/tests/g6/test_reachability_probe.py"
RENDERER = (
    ROOT
    / "graphrag/src/eleutheria_graphrag/agents/tools/build_controversy_frame.py"
)
GRAPHRAG_PACKAGE = ROOT / "graphrag/src/eleutheria_graphrag"
EDGE_TYPES = ROOT / "knowledge graph/ontology/edge_types.json"

SELECTED_SEEDS: tuple[str, ...] = (
    "debate_alexander_stoics_determinism",
    "debate_discovery_of_will",
    "debate_christian_gnostic_freedom",
    "debate_prohairesis_meaning",
    "debate_carneadean_antiastrology_tradition",
    "debate_augustine_pelagius_grace",
)

EXPECTED_POSITION_LINKS: tuple[tuple[str, str], ...] = (
    (
        "scholarly_argument_ramelli_alexander_s_concept_of_to_eph__5",
        "central-debates-20260817-004",
    ),
    (
        "scholarly_position_frede_will_originates_epictetus",
        "526b2160-b08b-45e8-94d8-be8bd289fd8a",
    ),
    (
        "scholarly_argument_irwin_greek_concept_of_the_will_0",
        "b01bc633-7535-4545-b758-388541d423bb",
    ),
    (
        "position_linjamaa_valentinian_ethics_and_self_determination",
        "central-debates-20260817-014",
    ),
    (
        "position_long_epictetan_freedom_compliance_with_fate",
        "central-debates-20260817-021",
    ),
    (
        "position_furst_carneades_proto_voluntarist_self_motion",
        "central-debates-20260817-029",
    ),
    (
        "scholarly_argument_moller_augustine_target_plausible_not_decisive",
        "furst-markschies-126",
    ),
)

RENDERED_DIALECTICAL_RELATIONS: frozenset[str] = frozenset(
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
POSITION_SOURCE_RELATION = "argues_for"
PY2_EXCEPT = "except TypeError, ValueError:"
PY3_EXCEPT = "except (TypeError, ValueError):"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--apply",
        action="store_true",
        help="write the gated novel subset (default: dry-run)",
    )
    mode.add_argument(
        "--dry-run",
        action="store_true",
        help="validate only; this is already the default",
    )
    return parser.parse_args()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def metadata(record: dict[str, Any]) -> dict[str, Any]:
    value = record.get("metadata")
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            return {}
    return value if isinstance(value, dict) else {}


def triple(edge: dict[str, Any]) -> tuple[str, str, str]:
    return edge["source"], edge["relation"], edge["target"]


def attestation_present(edge: dict[str, Any]) -> bool:
    value = metadata(edge).get("attested_by")
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, list):
        return any(str(item).strip() for item in value)
    return False


def assert_delta_invariants(delta: dict[str, Any]) -> None:
    assert set(delta) == {"nodes", "edges"}, (
        "delta must contain exactly nodes and edges"
    )
    assert isinstance(delta["nodes"], list) and delta["nodes"], "empty node delta"
    assert isinstance(delta["edges"], list) and delta["edges"], "empty edge delta"

    node_ids = [node["id"] for node in delta["nodes"]]
    assert len(node_ids) == len(set(node_ids)), "duplicate node id within delta"
    node_id_set = set(node_ids)
    for node in delta["nodes"]:
        assert node["id"] == node.get("node_id"), (
            f"{node['id']}: id/node_id mismatch"
        )
        assert node.get("type") == "position", (
            f"{node['id']}: central editorial nodes must be positions"
        )
        assert str(node.get("label") or "").strip(), f"{node['id']}: missing label"
        assert str(node.get("description") or "").strip(), (
            f"{node['id']}: missing description"
        )
        provenance = metadata(node).get("provenance")
        assert isinstance(provenance, dict) and provenance.get("source"), (
            f"{node['id']}: metadata.provenance.source is required"
        )
        source_ids = provenance.get("source_node_ids")
        assert isinstance(source_ids, list) and source_ids, (
            f"{node['id']}: provenance.source_node_ids is required"
        )

    edge_ids = [edge["edge_id"] for edge in delta["edges"]]
    triples = [triple(edge) for edge in delta["edges"]]
    assert len(edge_ids) == len(set(edge_ids)), "duplicate edge id within delta"
    assert len(triples) == len(set(triples)), "duplicate edge triple within delta"

    triple_set = set(triples)
    for edge in delta["edges"]:
        required = {
            "edge_id",
            "source",
            "source_id",
            "relation",
            "target",
            "target_id",
            "metadata",
        }
        missing = required - set(edge)
        assert not missing, f"{edge.get('edge_id', '?')}: missing {sorted(missing)}"
        assert edge["source"] == edge["source_id"], (
            f"{edge['edge_id']}: source/source_id mismatch"
        )
        assert edge["target"] == edge["target_id"], (
            f"{edge['edge_id']}: target/target_id mismatch"
        )
        assert edge["source"] != edge["target"], (
            f"{edge['edge_id']}: self-edge forbidden"
        )
        reverse = (edge["target"], edge["relation"], edge["source"])
        assert reverse not in triple_set, (
            f"{edge['edge_id']}: reverse-direction duplicate within delta"
        )
        if edge["relation"] in RENDERED_DIALECTICAL_RELATIONS:
            assert attestation_present(edge), (
                f"{edge['edge_id']}: dialectical edge lacks metadata.attested_by"
            )
            proposition = metadata(edge).get("proposition")
            assert isinstance(proposition, str) and proposition.strip(), (
                f"{edge['edge_id']}: dialectical edge lacks metadata.proposition"
            )

    has_position_targets = {
        edge["target"]
        for edge in delta["edges"]
        if edge["relation"] == "has_position"
    }
    grounded_position_targets = {
        edge["target"]
        for edge in delta["edges"]
        if edge["relation"] == POSITION_SOURCE_RELATION
    }
    assert node_id_set <= has_position_targets, (
        "every new position must be attached to a debate via has_position"
    )
    assert node_id_set <= grounded_position_targets, (
        "every new position must be grounded by an existing argument via argues_for"
    )

    direct_dialectical_seeds: set[str] = set()
    for edge in delta["edges"]:
        if edge["relation"] not in RENDERED_DIALECTICAL_RELATIONS:
            continue
        if edge["source"] in SELECTED_SEEDS:
            direct_dialectical_seeds.add(edge["source"])
        if edge["target"] in SELECTED_SEEDS:
            direct_dialectical_seeds.add(edge["target"])
    assert direct_dialectical_seeds == set(SELECTED_SEEDS), (
        "each selected debate needs a direct incident dialectical edge so the "
        "renderer can take its non-fallback branch"
    )


def assert_ontology_endpoint_types(
    delta: dict[str, Any], existing_nodes: list[dict[str, Any]]
) -> None:
    payload = json.loads(EDGE_TYPES.read_text(encoding="utf-8"))
    edge_types = payload["edge_types"]
    node_types = {node["id"]: node.get("type") for node in existing_nodes}
    node_types.update({node["id"]: node.get("type") for node in delta["nodes"]})
    failures: list[str] = []
    for edge in delta["edges"]:
        relation = edge["relation"]
        specification = edge_types.get(relation)
        if specification is None:
            failures.append(f"{edge['edge_id']}: unknown relation {relation}")
            continue
        if specification.get("status") != "active":
            failures.append(
                f"{edge['edge_id']}: relation {relation} is "
                f"{specification.get('status')}"
            )
        source_type = node_types.get(edge["source"])
        target_type = node_types.get(edge["target"])
        if source_type not in specification.get("source_types", []):
            failures.append(
                f"{edge['edge_id']}: source type {source_type} invalid for {relation}"
            )
        if target_type not in specification.get("target_types", []):
            failures.append(
                f"{edge['edge_id']}: target type {target_type} invalid for {relation}"
            )
    if failures:
        raise AssertionError("ontology endpoint typing failed: " + "; ".join(failures))


def author_map(
    nodes: list[dict[str, Any]], edges: list[dict[str, Any]]
) -> dict[str, str]:
    authors: dict[str, str] = {}
    for node in nodes:
        md = metadata(node)
        scholar = md.get("scholar_id") or md.get("author_id")
        if isinstance(scholar, str) and scholar:
            authors[node["id"]] = scholar
        elif node.get("type") == "person":
            authors[node["id"]] = node["id"]
    for edge in edges:
        if edge.get("relation") in {"created_by", "authored_by"}:
            authors.setdefault(edge["source"], edge["target"])
    return authors


def pinned_opposes_count() -> int:
    source = G6_PROBE.read_text(encoding="utf-8")
    match = re.search(r"assert len\(all_opposes\) == (\d+)", source)
    if not match:
        raise AssertionError(f"cannot locate G6 opposes pin in {G6_PROBE}")
    return int(match.group(1))


def novel_subset(
    delta: dict[str, Any],
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], int, int]:
    existing_node_ids = {node["id"] for node in nodes}
    existing_edge_ids = {
        edge.get("edge_id"): triple(edge)
        for edge in edges
        if edge.get("edge_id")
    }
    existing_triples = {triple(edge) for edge in edges}

    new_nodes = [node for node in delta["nodes"] if node["id"] not in existing_node_ids]
    skipped_nodes = len(delta["nodes"]) - len(new_nodes)
    all_node_ids = existing_node_ids | {node["id"] for node in new_nodes}

    unresolved_provenance: list[tuple[str, str]] = []
    for node in new_nodes:
        provenance = metadata(node)["provenance"]
        for source_id in provenance["source_node_ids"]:
            if source_id not in all_node_ids:
                unresolved_provenance.append((node["id"], source_id))
    if unresolved_provenance:
        raise AssertionError(
            "unresolvable provenance source_node_ids: "
            f"{unresolved_provenance[:5]}"
        )

    new_edges: list[dict[str, Any]] = []
    skipped_edges = 0
    unresolved: list[tuple[str, str, str]] = []
    reverse_duplicates: list[tuple[str, str, str]] = []
    edge_id_collisions: list[str] = []
    seen_triples = set(existing_triples)

    for edge in delta["edges"]:
        edge_triple = triple(edge)
        if edge_triple in seen_triples:
            skipped_edges += 1
            continue
        prior = existing_edge_ids.get(edge["edge_id"])
        if prior is not None and prior != edge_triple:
            edge_id_collisions.append(edge["edge_id"])
            continue
        if edge["source"] not in all_node_ids or edge["target"] not in all_node_ids:
            unresolved.append(edge_triple)
            continue
        reverse = (edge["target"], edge["relation"], edge["source"])
        if (
            edge["relation"] in RENDERED_DIALECTICAL_RELATIONS
            and reverse in seen_triples
        ):
            reverse_duplicates.append(edge_triple)
            continue
        new_edges.append(edge)
        seen_triples.add(edge_triple)

    failures = [
        ("unresolvable endpoints", unresolved),
        ("reverse-direction dialectical duplicates", reverse_duplicates),
        ("edge-id collisions", edge_id_collisions),
    ]
    for label, rows in failures:
        if rows:
            print(f"FATAL: {len(rows)} {label}: {rows[:5]}")
    if any(rows for _, rows in failures):
        raise AssertionError("delta resolution failed")

    authors = author_map([*nodes, *new_nodes], [*edges, *new_edges])
    same_scholar_opposes: list[tuple[str, str, str]] = []
    for edge in new_edges:
        if edge["relation"] != "opposes":
            continue
        source_author = authors.get(edge["source"])
        target_author = authors.get(edge["target"])
        documented_retraction = metadata(edge).get("documented_self_retraction") is True
        if (
            source_author
            and source_author == target_author
            and not documented_retraction
        ):
            same_scholar_opposes.append(triple(edge))
    if same_scholar_opposes:
        raise AssertionError(
            "same-scholar opposes without documented self-retraction: "
            f"{same_scholar_opposes[:5]}"
        )

    return new_nodes, new_edges, skipped_nodes, skipped_edges


def normalise_legacy_except(source: str) -> tuple[str, int]:
    count = source.count(PY2_EXCEPT)
    return source.replace(PY2_EXCEPT, PY3_EXCEPT), count


def run_ingestion_gate(
    new_nodes: list[dict[str, Any]], new_edges: list[dict[str, Any]]
) -> tuple[subprocess.CompletedProcess[str], int]:
    """Run the repository gate from a temporary mirror.

    Only the parser-invalid exception spelling in the mirrored shared relation
    module is normalised.  The actual gate script and live source tree remain
    byte-for-byte untouched.
    """

    with tempfile.TemporaryDirectory(prefix="central-debates-gate-") as tmp_name:
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
        for name in (
            "edge_types.json",
            "period_scheme.json",
            "school_scheme.json",
        ):
            shutil.copy2(
                ROOT / "knowledge graph/ontology" / name,
                sandbox / "knowledge graph/ontology" / name,
            )

        shared_source = (
            ROOT
            / "graphrag/src/eleutheria_graphrag/agents/dialectical_relations.py"
        ).read_text(encoding="utf-8")
        shared_source, substitutions = normalise_legacy_except(shared_source)
        shared.write_text(shared_source, encoding="utf-8")

        subset = sandbox / "central_debates_novel.json"
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


def install_namespace_package(name: str, path: Path) -> None:
    module = types.ModuleType(name)
    module.__path__ = [str(path)]  # type: ignore[attr-defined]
    module.__package__ = name
    sys.modules[name] = module


def load_sanitised_module(name: str, path: Path) -> int:
    source, substitutions = normalise_legacy_except(path.read_text(encoding="utf-8"))
    module = types.ModuleType(name)
    module.__file__ = str(path)
    module.__package__ = name.rpartition(".")[0]
    sys.modules[name] = module
    exec(compile(source, str(path), "exec"), module.__dict__)
    return substitutions


def load_renderer() -> tuple[type[Any], type[Any], int]:
    """Load the actual renderer while bypassing package ``__init__`` side effects."""

    install_namespace_package("eleutheria_graphrag", GRAPHRAG_PACKAGE)
    install_namespace_package(
        "eleutheria_graphrag.agents", GRAPHRAG_PACKAGE / "agents"
    )
    install_namespace_package(
        "eleutheria_graphrag.agents.tools", GRAPHRAG_PACKAGE / "agents/tools"
    )
    install_namespace_package(
        "eleutheria_graphrag.services", GRAPHRAG_PACKAGE / "services"
    )

    substitutions = 0
    for module_name, relative in (
        (
            "eleutheria_graphrag.agents.dialectical_relations",
            "agents/dialectical_relations.py",
        ),
        ("eleutheria_graphrag.agents.citability", "agents/citability.py"),
        (
            "eleutheria_graphrag.agents.thesis_equivalence",
            "agents/thesis_equivalence.py",
        ),
    ):
        substitutions += load_sanitised_module(
            module_name, GRAPHRAG_PACKAGE / relative
        )

    dependencies = importlib.import_module("eleutheria_graphrag.agents.dependencies")
    renderer_module = importlib.import_module(
        "eleutheria_graphrag.agents.tools.build_controversy_frame"
    )
    assert Path(renderer_module.__file__).resolve() == RENDERER.resolve(), (
        "verification did not load the repository renderer"
    )
    return renderer_module.BuildControversyFrameTool, dependencies.Deps, substitutions


async def render_frames(
    renderer_type: type[Any],
    deps_type: type[Any],
    nodes_path: Path,
    edges_path: Path,
    seeds: tuple[str, ...] = SELECTED_SEEDS,
) -> dict[str, dict[str, Any]]:
    nodes = read_jsonl(nodes_path)
    edges = read_jsonl(edges_path)
    outgoing: dict[str, list[dict[str, Any]]] = collections.defaultdict(list)
    incoming: dict[str, list[dict[str, Any]]] = collections.defaultdict(list)
    for edge in edges:
        outgoing[edge["source"]].append(edge)
        incoming[edge["target"]].append(edge)
    deps = deps_type(
        db=None,
        llm=None,
        node_lookup={node["id"]: node for node in nodes},
        outgoing_edges=dict(outgoing),
        incoming_edges=dict(incoming),
        pagerank_scores={},
    )
    tool = renderer_type(deps)
    results: dict[str, dict[str, Any]] = {}
    for seed in seeds:
        output = await tool.execute({"seed_id": seed, "max_passages": 12})
        frame = output.frame
        results[seed] = {
            "used_fallback": output.used_fallback,
            "note": output.note,
            "positions": [position.position_id for position in frame.positions],
            "links": [
                {
                    "edge_id": link.edge_id,
                    "from": link.from_id,
                    "relation": link.relation,
                    "to": link.to_id,
                    "attested": link.attested,
                }
                for link in frame.links
            ],
            "passages": [
                passage.passage_id for passage in frame.contested_passages
            ],
            "flagged_passages": [
                passage.passage_id for passage in frame.flagged_passages
            ],
        }
    return results


def run_renderer_gate(
    new_nodes: list[dict[str, Any]], new_edges: list[dict[str, Any]]
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]], int, int]:
    renderer_type, deps_type, substitutions = load_renderer()
    before = asyncio.run(render_frames(renderer_type, deps_type, NODES, EDGES))

    with tempfile.TemporaryDirectory(prefix="central-debates-renderer-") as tmp_name:
        sandbox = Path(tmp_name)
        sandbox_nodes = sandbox / "nodes.jsonl"
        sandbox_edges = sandbox / "edges.jsonl"
        shutil.copy2(NODES, sandbox_nodes)
        shutil.copy2(EDGES, sandbox_edges)
        with sandbox_nodes.open("a", encoding="utf-8") as handle:
            for node in new_nodes:
                handle.write(json.dumps(node, ensure_ascii=False) + "\n")
        with sandbox_edges.open("a", encoding="utf-8") as handle:
            for edge in new_edges:
                handle.write(json.dumps(edge, ensure_ascii=False) + "\n")
        after = asyncio.run(
            render_frames(renderer_type, deps_type, sandbox_nodes, sandbox_edges)
        )
        position_seeds = tuple(dict.fromkeys(seed for seed, _ in EXPECTED_POSITION_LINKS))
        position_frames = asyncio.run(
            render_frames(
                renderer_type,
                deps_type,
                sandbox_nodes,
                sandbox_edges,
                position_seeds,
            )
        )

    failures: list[str] = []
    for seed in SELECTED_SEEDS:
        if after[seed]["used_fallback"]:
            failures.append(f"{seed}: lexical fallback still used")
        if len(after[seed]["positions"]) < 2:
            failures.append(f"{seed}: fewer than two rendered positions")
        if not after[seed]["links"]:
            failures.append(f"{seed}: no rendered direct dialectical link")
        if not all(link["attested"] for link in after[seed]["links"]):
            failures.append(f"{seed}: renderer exposed an unattested direct link")
        if not after[seed]["passages"]:
            failures.append(f"{seed}: no citable contested passage")
    if failures:
        raise AssertionError("renderer gate failed: " + "; ".join(failures))

    link_failures: list[str] = []
    for seed, edge_id in EXPECTED_POSITION_LINKS:
        matches = [
            link for link in position_frames[seed]["links"] if link["edge_id"] == edge_id
        ]
        if not matches:
            link_failures.append(f"{seed}: missing position link {edge_id}")
        elif not all(link["attested"] for link in matches):
            link_failures.append(f"{seed}: unattested position link {edge_id}")
    if link_failures:
        raise AssertionError(
            "position-link renderer gate failed: " + "; ".join(link_failures)
        )
    return before, after, substitutions, len(EXPECTED_POSITION_LINKS)


def write_jsonl_atomically(
    path: Path,
    existing: list[dict[str, Any]],
    novel: list[dict[str, Any]],
    backup_suffix: str,
) -> None:
    backup = path.with_name(path.name + backup_suffix)
    shutil.copy2(path, backup)
    fd, temp_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temp_path = Path(temp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            for record in [*existing, *novel]:
                handle.write(json.dumps(record, ensure_ascii=False) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, path)
    except Exception:
        temp_path.unlink(missing_ok=True)
        raise


def print_renderer_evidence(
    before: dict[str, dict[str, Any]], after: dict[str, dict[str, Any]]
) -> None:
    print("--- build_controversy_frame.py before/after ---")
    print(f"renderer: {RENDERER.relative_to(ROOT)}")
    for seed in SELECTED_SEEDS:
        before_frame, after_frame = before[seed], after[seed]
        before_path = (
            "lexical-participant fallback"
            if before_frame["used_fallback"]
            else "direct incident-dialectical path"
        )
        after_path = (
            "lexical-participant fallback"
            if after_frame["used_fallback"]
            else "direct incident-dialectical path"
        )
        print(
            f"{seed}: before fallback={before_frame['used_fallback']} "
            f"path={before_path}; after fallback={after_frame['used_fallback']} "
            f"path={after_path}; positions={len(after_frame['positions'])}; "
            f"links={len(after_frame['links'])}; "
            f"passages={len(after_frame['passages'])}"
        )


def main() -> int:
    args = parse_args()
    delta = json.loads(DELTA.read_text(encoding="utf-8"))
    assert_delta_invariants(delta)

    nodes = read_jsonl(NODES)
    edges = read_jsonl(EDGES)
    try:
        assert_ontology_endpoint_types(delta, nodes)
        new_nodes, new_edges, skipped_nodes, skipped_edges = novel_subset(
            delta, nodes, edges
        )
    except AssertionError as exc:
        print(f"FATAL: {exc}")
        print("nothing written")
        return 1

    print(f"delta: {len(delta['nodes'])} nodes / {len(delta['edges'])} edges")
    print(f"ontology endpoint typing: {len(delta['edges'])}/{len(delta['edges'])} active and valid")
    print(
        f"novel: {len(new_nodes)} nodes / {len(new_edges)} edges "
        f"(skipped existing: {skipped_nodes} nodes, {skipped_edges} edges)"
    )
    relation_counts = collections.Counter(edge["relation"] for edge in new_edges)
    print(
        "relations: "
        + ", ".join(
            f"{relation}={count}"
            for relation, count in sorted(relation_counts.items())
        )
    )

    current_opposes = sum(edge.get("relation") == "opposes" for edge in edges)
    novel_opposes = relation_counts.get("opposes", 0)
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
    if gate.returncode:
        print(f"FATAL: ingestion gate failed with exit {gate.returncode}")
        print("nothing written")
        return 1

    try:
        before, after, renderer_substitutions, position_link_count = run_renderer_gate(
            new_nodes, new_edges
        )
    except (AssertionError, ImportError, SyntaxError) as exc:
        print(f"FATAL: renderer gate failed: {exc}")
        print("nothing written")
        return 1
    print(
        "renderer dependency parser normalisations: "
        f"{renderer_substitutions} (in memory only; renderer unchanged)"
    )
    print_renderer_evidence(before, after)
    print("renderer gate: 6/6 direct path; 6/6 with >=2 positions; 6/6 citable passages")
    print(
        f"position-link gate: {position_link_count}/{position_link_count} attested "
        "position relations retrievable (reused and novel)"
    )

    if not args.apply:
        pin_note = ""
        if novel_opposes and g6_pin != post_apply_opposes:
            pin_note = (
                f"; future apply refused until G6 opposes pin changes "
                f"from {g6_pin} to {post_apply_opposes}"
            )
        print(f"dry-run: nothing written{pin_note}")
        return 0

    if novel_opposes and g6_pin != post_apply_opposes:
        print(
            f"FATAL: G6 opposes pin is {g6_pin}, but post-apply count is "
            f"{post_apply_opposes}; update the pin in the same change before --apply"
        )
        print("nothing written")
        return 1

    write_jsonl_atomically(
        NODES, nodes, new_nodes, ".bak-central_debates"
    )
    write_jsonl_atomically(
        EDGES, edges, new_edges, ".bak-central_debates"
    )
    print(f"applied: +{len(new_nodes)} nodes, +{len(new_edges)} edges")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
