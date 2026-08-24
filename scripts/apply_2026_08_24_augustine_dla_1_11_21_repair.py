#!/usr/bin/env python3
"""Remove the false Augustine "coined liberum arbitrium" pseudo-passage.

The editorial node ``passage_aug_lib_arb_1_11_21`` was snapshot-linked both to
the real Latin corpus passage and to a second English synthesis with a wrong CTS
locus.  The synthesis also claimed that Augustine coined the phrase, despite
the KG's own earlier Tertullian evidence.  This wave preserves all removed rows
in audit quarantine, promotes the already-existing continuous Latin node as the
sole snapshot twin, and repoints valid graph relationships to it.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import tempfile
import unicodedata
from collections import Counter
from collections.abc import Callable
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_ROOT = ROOT / "data"
STAMP = "augustine_dla_1_11_21_repair_2026_08_24"
NOW = "2026-08-24 00:00:00+00:00"

EXACT_NODE = "passage_aug_dla_1_11_21"
CORRUPT_NODE = "passage_aug_lib_arb_1_11_21"
EXACT_PASSAGE = "c91f039f-2616-4c5c-ba9c-822e459d08b5"
CORRUPT_PASSAGE = "d4ed6968-8fc2-5db6-99d0-21ddaa69e583"
LIBERUM_CONCEPT = "concept_liberum_arbitrium_u3v4w5x6"

DROP_EDGE_IDS = {
    "702741ca-0723-4a57-a64b-39e053f42775",  # fake synthesis authored_by Augustine
    "03041720-0e30-4483-ae03-03d042eede06",  # fake synthesis part_of ancient work
    "e188caa4-b69b-4946-9eef-47704515d191",  # unsupported inter-work citation
}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def node_id(node: dict[str, Any]) -> str:
    return str(node.get("id") or node.get("node_id") or "")


def metadata(obj: dict[str, Any]) -> dict[str, Any]:
    value = obj.get("metadata")
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            return {}
    return copy.deepcopy(value) if isinstance(value, dict) else {}


def set_metadata(obj: dict[str, Any], value: dict[str, Any]) -> None:
    if isinstance(obj.get("metadata"), str):
        obj["metadata"] = json.dumps(value, ensure_ascii=False, sort_keys=True)
    else:
        obj["metadata"] = value


def replace_exact_value(value: Any, old: str, new: str) -> tuple[Any, int]:
    if isinstance(value, str):
        return (new, 1) if value == old else (value, 0)
    if isinstance(value, list):
        output: list[Any] = []
        count = 0
        for item in value:
            replaced, changed = replace_exact_value(item, old, new)
            output.append(replaced)
            count += changed
        return output, count
    if isinstance(value, dict):
        output: dict[str, Any] = {}
        count = 0
        for key, item in value.items():
            replaced, changed = replace_exact_value(item, old, new)
            output[key] = replaced
            count += changed
        return output, count
    return value, 0


def sha256_nfc(value: str) -> str:
    return hashlib.sha256(unicodedata.normalize("NFC", value).encode("utf-8")).hexdigest()


def transform(
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    passages: list[dict[str, Any]],
    citations: list[dict[str, Any]],
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    Counter[str],
]:
    nodes = copy.deepcopy(nodes)
    edges = copy.deepcopy(edges)
    passages = copy.deepcopy(passages)
    citations = copy.deepcopy(citations)
    counts: Counter[str] = Counter()
    quarantine: list[dict[str, Any]] = []
    by_node = {node_id(node): node for node in nodes}
    by_passage = {str(row.get("passage_id")): row for row in passages}

    if CORRUPT_NODE not in by_node and CORRUPT_PASSAGE not in by_passage:
        validate(nodes, edges, passages, citations)
        return nodes, edges, passages, citations, [], counts
    if EXACT_NODE not in by_node or EXACT_PASSAGE not in by_passage:
        raise RuntimeError("exact Augustine node or corpus passage is missing")
    if CORRUPT_NODE not in by_node or CORRUPT_PASSAGE not in by_passage:
        raise RuntimeError("partial prior repair detected; refusing to guess")

    exact = by_node[EXACT_NODE]
    corrupt = by_node[CORRUPT_NODE]
    corpus = by_passage[EXACT_PASSAGE]
    quarantine.extend(
        [
            {"record_type": "kg_node_before", "record": copy.deepcopy(exact)},
            {"record_type": "kg_node_removed", "record": copy.deepcopy(corrupt)},
            {
                "record_type": "corpus_passage_removed",
                "record": copy.deepcopy(by_passage[CORRUPT_PASSAGE]),
            },
        ]
    )

    exact["description"] = corpus["text_content"]
    exact["updated_at"] = NOW
    exact_data = metadata(exact)
    exact_data.pop("auto_generated", None)
    exact_data.update(
        {
            "attestation_type": "direct",
            "canonical_ref": corpus["canonical_ref"],
            "citable_as_primary": True,
            "corpus_passage_id": EXACT_PASSAGE,
            "cts_urn": corpus["cts_urn"],
            "db_passage_id": EXACT_PASSAGE,
            "language": "lat",
            "passage_id": EXACT_PASSAGE,
            "passage_role": "original",
            "text_content_sha256_nfc": sha256_nfc(corpus["text_content"]),
            STAMP: True,
            f"{STAMP}_status": "sole_exact_snapshot",
        }
    )
    set_metadata(exact, exact_data)
    counts["exact_node_corrected"] += 1

    repaired_nodes: list[dict[str, Any]] = []
    for node in nodes:
        if node_id(node) == CORRUPT_NODE:
            counts["corrupt_nodes_quarantined"] += 1
            continue
        replaced, changed = replace_exact_value(node, CORRUPT_NODE, EXACT_NODE)
        if changed:
            data = metadata(replaced)
            data[STAMP] = True
            data[f"{STAMP}_reference_updates"] = changed
            set_metadata(replaced, data)
            replaced["updated_at"] = NOW
            counts["node_references_repointed"] += changed
        repaired_nodes.append(replaced)
    nodes = repaired_nodes

    repaired_edges: list[dict[str, Any]] = []
    seen_triples: set[tuple[str, str, str]] = set()
    for edge in edges:
        touches = edge.get("source") == CORRUPT_NODE or edge.get("target") == CORRUPT_NODE
        if edge.get("edge_id") in DROP_EDGE_IDS:
            quarantine.append({"record_type": "kg_edge_removed", "record": edge})
            counts["edges_removed"] += 1
            continue
        if touches:
            quarantine.append({"record_type": "kg_edge_before_repoint", "record": copy.deepcopy(edge)})
            if edge.get("source") == CORRUPT_NODE:
                edge["source"] = EXACT_NODE
                edge["source_id"] = EXACT_NODE
            if edge.get("target") == CORRUPT_NODE:
                edge["target"] = EXACT_NODE
                edge["target_id"] = EXACT_NODE
            data = metadata(edge)
            data.update({STAMP: True, "source_scope": "exact Latin passage"})
            set_metadata(edge, data)
            counts["edges_repointed"] += 1
        edge, reference_updates = replace_exact_value(edge, CORRUPT_NODE, EXACT_NODE)
        if reference_updates and not touches:
            data = metadata(edge)
            data.update(
                {
                    STAMP: True,
                    f"{STAMP}_metadata_reference_updates": reference_updates,
                }
            )
            set_metadata(edge, data)
            counts["edge_metadata_references_repointed"] += reference_updates
        triple = (str(edge.get("source")), str(edge.get("relation")), str(edge.get("target")))
        if triple in seen_triples and touches:
            counts["duplicate_edges_dropped"] += 1
            continue
        seen_triples.add(triple)
        repaired_edges.append(edge)
    edges = repaired_edges

    passages = [
        row for row in passages if row.get("passage_id") != CORRUPT_PASSAGE
    ]
    counts["corrupt_corpus_rows_quarantined"] += 1

    repaired_citations: list[dict[str, Any]] = []
    for row in citations:
        if row.get("kg_node_id") == CORRUPT_NODE or row.get("passage_id") == CORRUPT_PASSAGE:
            quarantine.append({"record_type": "citation_removed", "record": row})
            counts["citations_removed"] += 1
            continue
        repaired_citations.append(row)
    citations = repaired_citations

    validate(nodes, edges, passages, citations)
    return nodes, edges, passages, citations, quarantine, counts


def validate(
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    passages: list[dict[str, Any]],
    citations: list[dict[str, Any]],
) -> None:
    by_node = {node_id(node): node for node in nodes}
    by_passage = {str(row.get("passage_id")): row for row in passages}
    if CORRUPT_NODE in by_node or CORRUPT_PASSAGE in by_passage:
        raise RuntimeError("corrupt Augustine synthesis remains queryable")
    exact = by_node.get(EXACT_NODE)
    corpus = by_passage.get(EXACT_PASSAGE)
    if exact is None or corpus is None or exact.get("description") != corpus.get("text_content"):
        raise RuntimeError("exact Augustine KG/corpus text parity failed")
    snapshots = [
        row
        for row in citations
        if row.get("citation_type") == "snapshot_passage_node"
        and row.get("passage_id") == EXACT_PASSAGE
    ]
    if len(snapshots) != 1 or snapshots[0].get("kg_node_id") != EXACT_NODE:
        raise RuntimeError(f"Augustine snapshot is not bijective: {snapshots}")
    serialized = "\n".join(json.dumps(row, ensure_ascii=False) for row in (*nodes, *edges, *citations))
    if CORRUPT_NODE in serialized or CORRUPT_PASSAGE in serialized:
        raise RuntimeError("dangling corrupt Augustine identifier survives")
    if "Augustine coins" in exact.get("description", "") or "First appearance" in exact.get("description", ""):
        raise RuntimeError("false Augustine coinage claim survives")
    concept = by_node.get(LIBERUM_CONCEPT)
    if concept is None or "Tertullian" not in concept.get("description", ""):
        raise RuntimeError("earlier Tertullian attestation is not represented")


def write_jsonl_preserving(
    path: Path, rows: list[dict[str, Any]], key: Callable[[dict[str, Any]], str]
) -> None:
    original = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    desired = {key(row): row for row in rows}
    if len(desired) != len(rows):
        raise RuntimeError(f"duplicate identities in {path}")
    seen: set[str] = set()
    output: list[str] = []
    for line in original:
        old = json.loads(line)
        wanted = key(old)
        if wanted not in desired:
            continue
        new = desired[wanted]
        output.append(line if old == new else json.dumps(new, ensure_ascii=False, sort_keys=True))
        seen.add(wanted)
    for wanted in sorted(desired.keys() - seen):
        output.append(json.dumps(desired[wanted], ensure_ascii=False, sort_keys=True))
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        tmp = Path(handle.name)
        handle.write("\n".join(output) + "\n")
    tmp.replace(path)


def write_citations_preserving(path: Path, rows: list[dict[str, Any]]) -> None:
    def canonical(row: dict[str, Any]) -> str:
        return json.dumps(
            row, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        )

    remaining = Counter(canonical(row) for row in rows)
    output: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        key = canonical(json.loads(line))
        if remaining[key] > 0:
            output.append(line)
            remaining[key] -= 1
    if any(remaining.values()):
        raise RuntimeError("citation writer cannot preserve newly added rows")
    path.write_text("\n".join(output) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--data-root", type=Path, default=DEFAULT_DATA_ROOT)
    args = parser.parse_args(argv)
    if args.write and args.dry_run:
        parser.error("--write and --dry-run are mutually exclusive")

    data_root = args.data_root.expanduser().resolve()
    paths = {
        "nodes": data_root / "kg/nodes.jsonl",
        "edges": data_root / "kg/edges.jsonl",
        "passages": data_root / "corpus/passages.jsonl",
        "citations": data_root / "corpus/citations.jsonl",
    }
    before = {name: read_jsonl(path) for name, path in paths.items()}
    nodes, edges, passages, citations, quarantine, counts = transform(
        before["nodes"], before["edges"], before["passages"], before["citations"]
    )
    print("Augustine DLA I.11.21 source-scope repair")
    print("mode:", "WRITE" if args.write else "DRY-RUN")
    for name, count in sorted(counts.items()):
        print(f"{name}: {count}")
    print(
        f"rows: nodes {len(before['nodes'])}->{len(nodes)}, "
        f"edges {len(before['edges'])}->{len(edges)}, "
        f"passages {len(before['passages'])}->{len(passages)}, "
        f"citations {len(before['citations'])}->{len(citations)}"
    )
    if not args.write:
        print("dry-run: nothing written (use --write to apply)")
        return 0
    if not counts:
        print("already applied: no files written")
        return 0
    write_jsonl_preserving(paths["nodes"], nodes, node_id)
    write_jsonl_preserving(paths["edges"], edges, lambda row: str(row.get("edge_id") or ""))
    write_jsonl_preserving(paths["passages"], passages, lambda row: str(row.get("passage_id") or ""))
    write_citations_preserving(paths["citations"], citations)
    quarantine_path = data_root / "audit/2026-08-24_augustine_dla_1_11_21_quarantine.jsonl"
    quarantine_path.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in quarantine),
        encoding="utf-8",
    )
    print("wrote:", *paths.values(), quarantine_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
