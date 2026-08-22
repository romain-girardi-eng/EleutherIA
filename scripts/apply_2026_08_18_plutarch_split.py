#!/usr/bin/env python3
"""Apply the adjudicated Plutarch tlg135/tlg138 split.

Dry-run is the default.  ``--apply`` writes only after exact row-level
preconditions, source-family checks, work/child checks, locus-parity checks,
the R1-R18 delta gate, and a projected-state re-read all succeed.
"""

from __future__ import annotations

import argparse
import copy
import json
import shutil
import subprocess
import sys
import tempfile
from collections import Counter
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.check_kg_corpus_locus_parity import (  # noqa: E402
    find_violations as find_parity_violations,
)
from scripts.check_kg_work_child_canonical import (  # noqa: E402
    find_mismatches,
)
from scripts.check_kg_work_id_uniqueness import (  # noqa: E402
    collect_work_groups,
    find_collisions,
)
from scripts.data_2026_08_18_plutarch_split import (  # noqa: E402
    AUTHOR_ID,
    AUTHOR_NAME,
    EXPECTED_ALLOWLIST_ENTRY,
    NEW_AUTHORSHIP_EDGE_ID,
    NEW_WORK_ID,
    NEW_WORK_LABEL,
    OLD_TLG135_TITLE,
    OLD_WORK_ID,
    PASSAGES,
    PERSEUS_COMMIT,
    PERSEUS_FILES,
    STAMP_DATE,
    TLG135_CORPUS_ID,
    TLG135_GREEK_TITLE,
    TLG135_MORALIA_LOCUS,
    TLG135_TITLE,
    TLG135_WORK_URN,
    TLG138_CORPUS_ID,
    TLG138_TITLE,
    TLG138_WORK_URN,
    TLGE_IDT_SHA256,
    TLGE_TXT_SHA256,
    WAVE,
    inspect_repository,
    record_id,
    verify_local_tlge,
)

BACKUP_SUFFIX = ".bak-plutarch_split_2026_08_18"
FIXED_TIMESTAMP = "2026-08-18 00:00:00+00:00"
GATE_PATH = ROOT / "scripts/check_ingestion_rules.py"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument(
        "--skip-local-tlge",
        action="store_true",
        help="skip re-reading the independently hashed local TLG E files",
    )
    return parser.parse_args()


def key_node(row: dict[str, Any]) -> str:
    return record_id(row)


def key_edge(row: dict[str, Any]) -> str:
    return str(row.get("edge_id") or "")


def key_passage(row: dict[str, Any]) -> str:
    return str(row.get("passage_id") or "")


def key_manifest(row: dict[str, Any]) -> str:
    return str(row.get("canonical_id") or "")


def load_jsonl_with_raw(
    path: Path,
    key: Callable[[dict[str, Any]], str],
) -> tuple[list[dict[str, Any]], dict[str, tuple[dict[str, Any], str]]]:
    rows: list[dict[str, Any]] = []
    originals: dict[str, tuple[dict[str, Any], str]] = {}
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            row = json.loads(line)
            wanted = key(row)
            if not wanted or wanted in originals:
                raise ValueError(f"invalid/duplicate key in {path}:{line_number}")
            rows.append(row)
            originals[wanted] = (copy.deepcopy(row), line)
    return rows, originals


def render_jsonl(
    rows: list[dict[str, Any]],
    originals: dict[str, tuple[dict[str, Any], str]],
    key: Callable[[dict[str, Any]], str],
    *,
    compact: bool,
) -> bytes:
    rendered: list[str] = []
    seen: set[str] = set()
    for row in rows:
        wanted = key(row)
        if not wanted or wanted in seen:
            raise ValueError(f"invalid/duplicate output key: {wanted!r}")
        seen.add(wanted)
        original = originals.get(wanted)
        if original is not None and original[0] == row:
            rendered.append(original[1])
            continue
        kwargs: dict[str, Any] = {"ensure_ascii": False}
        if compact:
            kwargs["separators"] = (",", ":")
        rendered.append(json.dumps(row, **kwargs) + "\n")
    return "".join(rendered).encode("utf-8")


def parse_metadata_form(row: dict[str, Any]) -> tuple[dict[str, Any], str]:
    value = row.get("metadata") or {}
    if isinstance(value, dict):
        return copy.deepcopy(value), "dict"
    if isinstance(value, str):
        parsed = json.loads(value)
        if isinstance(parsed, dict):
            return parsed, "string"
    raise ValueError(f"unreadable metadata on {record_id(row)}")


def set_metadata_form(row: dict[str, Any], value: dict[str, Any], form: str) -> None:
    row["metadata"] = (
        json.dumps(value, ensure_ascii=False) if form == "string" else value
    )


def new_work_node() -> dict[str, Any]:
    source = PERSEUS_FILES["tlg135_catalogue"]
    tei = PERSEUS_FILES["tlg135_tei"]
    return {
        "alternative_names": json.dumps(
            [
                TLG135_GREEK_TITLE,
                "Epitome of On the Generation of the Soul in the Timaeus",
            ],
            ensure_ascii=False,
        ),
        "created_at": FIXED_TIMESTAMP,
        "description": (
            "Plutarch, Epitome libri de animae procreatione in Timaeo "
            f"({TLG135_GREEK_TITLE}), Moralia {TLG135_MORALIA_LOCUS}. The six "
            "sections epitomize the preceding De animae procreatione in Timaeo "
            "and treat Plato's account of world-soul formation, matter, number, "
            "and harmonic proportion."
        ),
        "id": NEW_WORK_ID,
        "label": NEW_WORK_LABEL,
        "metadata": {
            "author": AUTHOR_NAME,
            "cts_urn": TLG135_WORK_URN,
            "work_canonical_id": TLG135_CORPUS_ID,
            "language": "grc",
            "moralia_pages": TLG135_MORALIA_LOCUS,
            "title_grc": TLG135_GREEK_TITLE,
            "edition": (
                "Plutarchi Chaeronensis Moralia, vol. 6, ed. Grēgorios N. "
                "Vernardakēs (Leipzig: Teubner, 1895), Perseus perseus-grc2"
            ),
            "citation_verdict": "corrected",
            "citation_verified": True,
            "verified_reference": (
                f"Plutarch, {TLG135_TITLE}, Moralia {TLG135_MORALIA_LOCUS}; "
                f"{TLG135_WORK_URN}; local TLG0007.IDT work 135"
            ),
            "provenance": {
                "source": source["url"],
                "source_sha256": source["sha256"],
                "text_source": tei["url"],
                "text_source_sha256": tei["sha256"],
                "perseus_commit": PERSEUS_COMMIT,
                "local_tlge_idt_sha256": TLGE_IDT_SHA256,
                "local_tlge_txt_sha256": TLGE_TXT_SHA256,
                "ingested_at": STAMP_DATE,
                "ingest_script": "scripts/apply_2026_08_18_plutarch_split.py",
            },
            WAVE: {
                "adjudication": "distinct_work_not_second_edition",
                "previously_misattached_passages": 6,
                "true_de_communibus_work": TLG138_WORK_URN,
            },
        },
        "node_id": NEW_WORK_ID,
        "period": "Roman Imperial",
        "role": None,
        "school": None,
        "type": "work",
        "updated_at": FIXED_TIMESTAMP,
    }


def new_authorship_edge() -> dict[str, Any]:
    return {
        "created_at": FIXED_TIMESTAMP,
        "edge_id": NEW_AUTHORSHIP_EDGE_ID,
        "metadata": {
            "wave": WAVE,
            "source": PERSEUS_FILES["tlg135_catalogue"]["url"],
            "confidence": 1.0,
        },
        "relation": "authored_by",
        "source": NEW_WORK_ID,
        "source_id": NEW_WORK_ID,
        "target": AUTHOR_ID,
        "target_id": AUTHOR_ID,
        "weight": 1.0,
    }


def apply_transform(
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    manifest: list[dict[str, Any]],
    passages: list[dict[str, Any]],
    allowlist: dict[str, Any],
) -> dict[str, Any]:
    nodes_by_id = {key_node(row): row for row in nodes}
    edges_by_id = {key_edge(row): row for row in edges}
    passages_by_id = {key_passage(row): row for row in passages}
    manifest_by_id = {key_manifest(row): row for row in manifest}
    if NEW_WORK_ID in nodes_by_id or NEW_AUTHORSHIP_EDGE_ID in edges_by_id:
        raise ValueError("new Plutarch work/edge already exists in pre-repair state")

    changed_nodes: list[str] = []
    changed_edges: list[str] = []
    for spec in PASSAGES:
        sequence = spec["sequence"]
        node = nodes_by_id[spec["node_id"]]
        node_metadata, form = parse_metadata_form(node)
        expected_ref = str(sequence)
        if node_metadata.get("canonical_ref") != expected_ref:
            raise ValueError(
                f"{spec['node_id']}: expected old canonical_ref {expected_ref!r}"
            )
        if node_metadata.get("work_title") != OLD_TLG135_TITLE:
            raise ValueError(f"{spec['node_id']}: old work title drift")
        node["label"] = f"Plutarch, {TLG135_TITLE}, {sequence}"
        node["updated_at"] = FIXED_TIMESTAMP
        node_metadata.update(
            {
                "work_title": TLG135_TITLE,
                "canonical_ref": f"{TLG135_TITLE} {sequence}",
                "work_node_id": NEW_WORK_ID,
                "citation_verdict": "corrected",
                "citation_verified": True,
                "verified_reference": (
                    f"Plutarch, {TLG135_TITLE} {sequence}; "
                    f"{TLG135_WORK_URN}.perseus-grc2:{sequence}"
                ),
                WAVE: {
                    "previous_work_title": OLD_TLG135_TITLE,
                    "previous_parent": OLD_WORK_ID,
                    "corrected_parent": NEW_WORK_ID,
                },
            }
        )
        set_metadata_form(node, node_metadata, form)
        changed_nodes.append(spec["node_id"])

        edge = edges_by_id[spec["part_of_edge_id"]]
        if edge.get("target") != OLD_WORK_ID or edge.get("target_id") != OLD_WORK_ID:
            raise ValueError(f"{spec['part_of_edge_id']}: old target drift")
        edge_metadata = copy.deepcopy(edge.get("metadata") or {})
        if not isinstance(edge_metadata, dict):
            raise ValueError(f"{spec['part_of_edge_id']}: metadata is not an object")
        edge_metadata[WAVE] = {
            "previous_target": OLD_WORK_ID,
            "corrected_target": NEW_WORK_ID,
            "reason": "tlg135 is the Epitome, while De communibus is tlg138",
        }
        edge["metadata"] = edge_metadata
        edge["target"] = NEW_WORK_ID
        edge["target_id"] = NEW_WORK_ID
        changed_edges.append(spec["part_of_edge_id"])

        passage = passages_by_id[spec["passage_id"]]
        expected_corpus_ref = f"{OLD_TLG135_TITLE} {sequence}"
        if passage.get("canonical_ref") != expected_corpus_ref:
            raise ValueError(f"{spec['passage_id']}: old corpus ref drift")
        passage["canonical_ref"] = f"{TLG135_TITLE} {sequence}"

    nodes.append(new_work_node())
    edges.append(new_authorship_edge())

    row135 = manifest_by_id[TLG135_CORPUS_ID]
    if row135.get("title") != OLD_TLG135_TITLE or row135.get("cts_urn") != "":
        raise ValueError("tlg135 manifest old identity drift")
    row135["title"] = TLG135_TITLE
    row135["cts_urn"] = TLG135_WORK_URN

    row138 = manifest_by_id[TLG138_CORPUS_ID]
    if row138.get("title") != TLG138_TITLE:
        raise ValueError("tlg138 manifest title must remain unchanged")

    known = allowlist.get("known_ambiguities")
    if (
        not isinstance(known, dict)
        or known.get(OLD_WORK_ID) != EXPECTED_ALLOWLIST_ENTRY
    ):
        raise ValueError("exact Plutarch ambiguity allowlist entry drifted")
    del known[OLD_WORK_ID]
    if allowlist.get("version") != 1:
        raise ValueError("ambiguity allowlist version drifted")
    allowlist["version"] = 2
    allowlist["generated_at"] = STAMP_DATE

    return {
        "new_nodes": [NEW_WORK_ID],
        "new_edges": [NEW_AUTHORSHIP_EDGE_ID],
        "changed_nodes": changed_nodes,
        "changed_edges": changed_edges,
        "changed_corpus_passages": [spec["passage_id"] for spec in PASSAGES],
    }


def collision_signature(rows: list[dict[str, Any]]) -> dict[str, set[str]]:
    return {
        row["kg_work_id"]: {member["work_canonical_id"] for member in row["members"]}
        for row in rows
    }


def stable_stats(
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    passages: list[dict[str, Any]],
    citations: list[dict[str, Any]],
    manifest: list[dict[str, Any]],
    ontology_root: Path,
) -> dict[str, Any]:
    node_types = Counter(str(row.get("type", "unknown")) for row in nodes)
    edge_relations = Counter(str(row.get("relation", "unknown")) for row in edges)
    works_with_text = {
        str(row["work_canonical_id"])
        for row in passages
        if row.get("work_canonical_id")
    }
    manifest_status = Counter(str(row.get("status", "unknown")) for row in manifest)

    def ontology_count(filename: str, key: str) -> int | None:
        path = ontology_root / filename
        if not path.exists():
            return None
        payload = json.loads(path.read_text(encoding="utf-8"))
        values = payload.get(key) if isinstance(payload, dict) else payload
        return len(values) if isinstance(values, (dict, list)) else None

    return {
        "sources": {
            "kg": "data/kg/nodes.jsonl + data/kg/edges.jsonl",
            "corpus": "data/corpus/*.jsonl",
            "ontology": "knowledge graph/ontology/*.json",
        },
        "kg": {
            "nodes": len(nodes),
            "edges": len(edges),
            "works": node_types.get("work", 0),
            "passage_nodes": node_types.get("passage", 0),
            "node_types_in_use": len(node_types),
            "edge_relations_in_use": len(edge_relations),
            "node_type_counts": dict(node_types.most_common()),
            "edge_relation_counts": dict(edge_relations.most_common()),
        },
        "corpus": {
            "passages": len(passages),
            "works_with_text": len(works_with_text),
            "passage_citations": len(citations),
            "manifest_entries": len(manifest),
            "manifest_status_counts": dict(manifest_status.most_common()),
        },
        "ontology": {
            "node_types_defined": ontology_count("node_types.json", "node_types"),
            "edge_types_defined": ontology_count("edge_types.json", "edge_types"),
        },
    }


def render_stats_markdown(stats: dict[str, Any]) -> str:
    kg = stats["kg"]
    corpus = stats["corpus"]
    ontology = stats["ontology"]
    rows = [
        ("Knowledge graph nodes", f"{kg['nodes']:,}"),
        ("Knowledge graph edges", f"{kg['edges']:,}"),
        ("Ancient works (KG)", f"{kg['works']:,}"),
        ("Corpus text passages", f"{corpus['passages']:,}"),
        ("Passage citations", f"{corpus['passage_citations']:,}"),
        (
            "Node types (ontology / in use)",
            f"{ontology['node_types_defined']} / {kg['node_types_in_use']}",
        ),
        (
            "Edge types (ontology / in use)",
            f"{ontology['edge_types_defined']} / {kg['edge_relations_in_use']}",
        ),
    ]
    lines = [
        f"<!-- generated by scripts/gen_stats.py on {stats['generated_at']} -->",
        "| Metric | Count |",
        "|--------|-------|",
        *(f"| {label} | {value} |" for label, value in rows),
    ]
    return "\n".join(lines) + "\n"


def run_delta_gate(new_node: dict[str, Any], new_edge: dict[str, Any]) -> str:
    with tempfile.TemporaryDirectory(prefix="eleutheria-plutarch-gate-") as tmp:
        delta = Path(tmp) / "delta.json"
        delta.write_text(
            json.dumps({"nodes": [new_node], "edges": [new_edge]}, ensure_ascii=False),
            encoding="utf-8",
        )
        result = subprocess.run(
            [sys.executable, str(GATE_PATH), "--new-only", str(delta)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
    if result.returncode != 0 or "BLOCK: 0" not in result.stdout:
        raise ValueError(f"R1-R18 delta gate failed:\n{result.stdout}\n{result.stderr}")
    return result.stdout.strip()


def validate_projected(
    *,
    before_nodes: list[dict[str, Any]],
    before_edges: list[dict[str, Any]],
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    manifest: list[dict[str, Any]],
    passages: list[dict[str, Any]],
    citations: list[dict[str, Any]],
) -> dict[str, Any]:
    before_mismatches = find_mismatches(before_nodes, before_edges, manifest)
    if len(before_mismatches) != 1 or before_mismatches[0]["work_id"] != OLD_WORK_ID:
        raise ValueError(
            f"unexpected pre-repair mismatch population: {before_mismatches}"
        )
    after_mismatches = find_mismatches(nodes, edges, manifest)
    if after_mismatches:
        raise ValueError(f"projected work/child mismatches: {after_mismatches}")

    before_collisions = collision_signature(
        find_collisions(collect_work_groups(before_nodes, before_edges))
    )
    after_collisions = collision_signature(
        find_collisions(collect_work_groups(nodes, edges))
    )
    if after_collisions != before_collisions:
        raise ValueError(
            f"work-id collision set changed: {before_collisions} -> {after_collisions}"
        )

    selected = tuple(spec["node_id"] for spec in PASSAGES)
    _, before_parity = find_parity_violations(
        before_nodes, passages, citations, selected
    )
    expected_before = {
        (spec["node_id"], spec["passage_id"], "canonical_ref") for spec in PASSAGES
    }
    observed_before = {
        (row["node_id"], row["passage_id"], row["field"]) for row in before_parity
    }
    if observed_before != expected_before:
        raise ValueError(f"unexpected pre-repair locus parity: {before_parity}")
    _, after_parity = find_parity_violations(nodes, passages, citations, selected)
    if after_parity:
        raise ValueError(f"projected Plutarch locus parity failures: {after_parity}")

    node_ids = {record_id(row) for row in nodes}
    bad_endpoints = [
        row.get("edge_id")
        for row in edges
        if row.get("source") not in node_ids
        or row.get("target") not in node_ids
        or row.get("source") != row.get("source_id")
        or row.get("target") != row.get("target_id")
    ]
    if bad_endpoints:
        raise ValueError(f"edge endpoint gate failed: {bad_endpoints[:10]}")

    family_counts = Counter(row.get("work_canonical_id") for row in passages)
    if family_counts[TLG135_CORPUS_ID] != 6:
        raise ValueError("projected tlg135 corpus count is not six")
    if family_counts[TLG138_CORPUS_ID] != 50:
        raise ValueError("projected tlg138 corpus count is not fifty")
    manifest_by_id = {key_manifest(row): row for row in manifest}
    if manifest_by_id[TLG135_CORPUS_ID].get("title") != TLG135_TITLE:
        raise ValueError("projected tlg135 manifest title is wrong")
    if manifest_by_id[TLG138_CORPUS_ID].get("title") != TLG138_TITLE:
        raise ValueError("projected tlg138 manifest title changed")

    gate_output = run_delta_gate(
        next(row for row in nodes if record_id(row) == NEW_WORK_ID),
        next(row for row in edges if row.get("edge_id") == NEW_AUTHORSHIP_EDGE_ID),
    )
    return {
        "work_child_mismatches_before": len(before_mismatches),
        "work_child_mismatches_after": len(after_mismatches),
        "tlg135_parity_violations_before": len(before_parity),
        "tlg135_parity_violations_after": len(after_parity),
        "work_id_collisions": len(after_collisions),
        "ingestion_gate": gate_output,
    }


def projected_state_check(
    nodes_payload: bytes,
    edges_payload: bytes,
    manifest_payload: bytes,
    passages_payload: bytes,
    allowlist_payload: bytes,
) -> None:
    with tempfile.TemporaryDirectory(prefix="eleutheria-plutarch-projected-") as tmp:
        root = Path(tmp)
        targets = {
            root / "data/kg/nodes.jsonl": nodes_payload,
            root / "data/kg/edges.jsonl": edges_payload,
            root / "data/corpus/manifest.jsonl": manifest_payload,
            root / "data/corpus/passages.jsonl": passages_payload,
            root
            / "data/audit/kg_work_child_canonical_known_ambiguities.json": allowlist_payload,
        }
        for path, payload in targets.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(payload)
        result = inspect_repository(root)
        if result.get("state") != "applied":
            raise ValueError(f"projected re-read did not reach applied state: {result}")


def backup_once(path: Path) -> Path:
    backup = path.with_name(path.name + BACKUP_SUFFIX)
    if not backup.exists():
        shutil.copy2(path, backup)
    return backup


def write_atomically(payloads: dict[Path, bytes]) -> None:
    staged: dict[Path, Path] = {}
    try:
        for path, payload in payloads.items():
            temporary = path.with_name(path.name + ".tmp-plutarch-split")
            temporary.write_bytes(payload)
            staged[path] = temporary
        for path, temporary in staged.items():
            temporary.replace(path)
    finally:
        for temporary in staged.values():
            if temporary.exists():
                temporary.unlink()


def main() -> int:
    args = parse_args()
    root = args.root.expanduser().resolve()
    paths = {
        "nodes": root / "data/kg/nodes.jsonl",
        "edges": root / "data/kg/edges.jsonl",
        "manifest": root / "data/corpus/manifest.jsonl",
        "passages": root / "data/corpus/passages.jsonl",
        "citations": root / "data/corpus/citations.jsonl",
        "allowlist": root / "data/audit/kg_work_child_canonical_known_ambiguities.json",
        "stats_json": root / "data/stats.json",
        "stats_md": root / "data/stats.md",
    }
    try:
        source_evidence = None
        if not args.skip_local_tlge:
            source_evidence = verify_local_tlge()
        initial = inspect_repository(root)
        if initial["state"] == "applied":
            print(
                json.dumps(
                    {
                        "mode": "apply" if args.apply else "dry-run",
                        "state": "already_applied",
                        "changed": False,
                        "repository": initial,
                    },
                    ensure_ascii=False,
                    indent=2,
                    sort_keys=True,
                )
            )
            return 0

        nodes, original_nodes = load_jsonl_with_raw(paths["nodes"], key_node)
        edges, original_edges = load_jsonl_with_raw(paths["edges"], key_edge)
        manifest, original_manifest = load_jsonl_with_raw(
            paths["manifest"], key_manifest
        )
        passages, original_passages = load_jsonl_with_raw(
            paths["passages"], key_passage
        )
        citations = [
            json.loads(line)
            for line in paths["citations"].read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        allowlist = json.loads(paths["allowlist"].read_text(encoding="utf-8"))
        current_stats = json.loads(paths["stats_json"].read_text(encoding="utf-8"))

        before_nodes = copy.deepcopy(nodes)
        before_edges = copy.deepcopy(edges)
        before_stable_stats = stable_stats(
            before_nodes,
            before_edges,
            passages,
            citations,
            manifest,
            root / "knowledge graph/ontology",
        )
        if {k: v for k, v in current_stats.items() if k != "generated_at"} != (
            before_stable_stats
        ):
            raise ValueError("data/stats.json is stale before the Plutarch repair")
        expected_stats_md = render_stats_markdown(current_stats)
        if paths["stats_md"].read_text(encoding="utf-8") != expected_stats_md:
            raise ValueError("data/stats.md is stale before the Plutarch repair")

        delta = apply_transform(nodes, edges, manifest, passages, allowlist)
        gates = validate_projected(
            before_nodes=before_nodes,
            before_edges=before_edges,
            nodes=nodes,
            edges=edges,
            manifest=manifest,
            passages=passages,
            citations=citations,
        )

        generated_at = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        stats = {
            "generated_at": generated_at,
            **stable_stats(
                nodes,
                edges,
                passages,
                citations,
                manifest,
                root / "knowledge graph/ontology",
            ),
        }
        payloads = {
            paths["nodes"]: render_jsonl(
                nodes, original_nodes, key_node, compact=False
            ),
            paths["edges"]: render_jsonl(
                edges, original_edges, key_edge, compact=False
            ),
            paths["manifest"]: render_jsonl(
                manifest, original_manifest, key_manifest, compact=True
            ),
            paths["passages"]: render_jsonl(
                passages, original_passages, key_passage, compact=True
            ),
            paths["allowlist"]: (
                json.dumps(allowlist, ensure_ascii=False, indent=2) + "\n"
            ).encode("utf-8"),
            paths["stats_json"]: (
                json.dumps(stats, ensure_ascii=False, indent=2) + "\n"
            ).encode("utf-8"),
            paths["stats_md"]: render_stats_markdown(stats).encode("utf-8"),
        }
        projected_state_check(
            payloads[paths["nodes"]],
            payloads[paths["edges"]],
            payloads[paths["manifest"]],
            payloads[paths["passages"]],
            payloads[paths["allowlist"]],
        )
    except (KeyError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ABORT: {exc}")
        return 1

    summary = {
        "mode": "apply" if args.apply else "dry-run",
        "state_before": initial["state"],
        "state_after": "applied",
        "delta": delta,
        "gates": gates,
        "projected_counts": {
            "nodes": stats["kg"]["nodes"],
            "edges": stats["kg"]["edges"],
            "works": stats["kg"]["works"],
            "corpus_passages": stats["corpus"]["passages"],
        },
        "local_tlge_verified": source_evidence is not None,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    if not args.apply:
        print("dry-run: nothing written (use --apply)")
        return 0

    backups = {str(path): str(backup_once(path)) for path in payloads}
    write_atomically(payloads)
    final = inspect_repository(root)
    if final["state"] != "applied":
        raise RuntimeError(f"post-write state gate failed: {final}")
    print(
        json.dumps(
            {"status": "applied", "backups": backups},
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
