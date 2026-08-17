#!/usr/bin/env python3
"""Apply the data-layer repairs from the 2026-08-17 cold audit.

Dry-run is the default.  ``--write`` is required to mutate the selected data
root.  A data root contains ``kg/*.jsonl``, ``corpus/*.jsonl`` and the derived
``stats.json``/``stats.md`` files.  Every mutation is guarded by audited field
or hash preconditions; backups are created before atomic replacement.

Usage:
    python3 scripts/apply_2026_08_17_cold_audit_data_repairs.py
    python3 scripts/apply_2026_08_17_cold_audit_data_repairs.py --write
    python3 scripts/apply_2026_08_17_cold_audit_data_repairs.py \
        --data-root /tmp/eleutheria-data --write
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import shutil
import sys
import uuid
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from data_2026_08_17_cold_audit_data_repairs import (  # noqa: E402
    BACKUP_SUFFIX,
    GALEN_DE_PLACITIS_URN,
    GALEN_NATURAL_FACULTIES_URN,
    GALEN_NEW_WORK_ID,
    GALEN_OLD_WORK_ID,
    GALEN_PASSAGES,
    GALEN_PRIMARY_SOURCE,
    METHODIUS_BAD_PASSAGE_URN,
    METHODIUS_NEW_WORK_ID,
    METHODIUS_OLD_WORK_ID,
    METHODIUS_SPAN_PREFIX,
    METHODIUS_WORK_URN,
    PLOTINUS_REMAP_RECORDS,
    SIMPLICIUS_CANONICAL_URN,
    SIMPLICIUS_STALE_URN,
    SIMPLICIUS_WORK_ID,
    STAMP,
    SYTSMA_CANONICAL_ID,
    SYTSMA_DUPLICATE_ID,
    SYTSMA_ORIGENALITY_ID,
    THEOPHRASTUS_MISFILED_CORPUS_IDS,
    THEOPHRASTUS_MISFILED_NODES,
    check_payload,
    derive_fedou_contamination,
    derive_methodius_spans,
    metadata,
    node_id,
    set_metadata,
    sha256_text,
)

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATA_ROOT = ROOT / "data"
DATA_ROOT_ENV = "COLD_AUDIT_DATA_ROOT"
METHODIUS_OLD_KG_WORK_ID = "urn:cts:greekLit:tlg2959.tlg001"


class RepairBlocked(RuntimeError):
    """Raised when a scholarly or structural precondition no longer holds."""


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def _atomic_text(path: Path, text: str) -> None:
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(text, encoding="utf-8")
    os.replace(temporary, path)


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    _atomic_text(
        path,
        "".join(
            json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n"
            for row in rows
        ),
    )


def canonical_json(row: dict[str, Any]) -> str:
    return json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def edge_triple(edge: dict[str, Any]) -> tuple[str, str, str]:
    return (
        str(edge.get("source") or ""),
        str(edge.get("relation") or ""),
        str(edge.get("target") or ""),
    )


def _set_edge_source(edge: dict[str, Any], source: str) -> None:
    edge["source"] = source
    edge["source_id"] = source


def _set_edge_target(edge: dict[str, Any], target: str) -> None:
    edge["target"] = target
    edge["target_id"] = target


def _record_changed(before: str, row: dict[str, Any]) -> bool:
    return before != canonical_json(row)


def rewrite_plotinus_corpus(
    nodes: list[dict[str, Any]],
    passages: list[dict[str, Any]],
    citations: list[dict[str, Any]],
    changes: Counter[str],
) -> None:
    nodes_by_id = {node_id(node): node for node in nodes}
    passages_by_id = {str(row.get("passage_id")): row for row in passages}

    for record in PLOTINUS_REMAP_RECORDS:
        wanted = record["node_id"]
        node = nodes_by_id.get(wanted)
        if node is None:
            raise RepairBlocked(f"Plotinus node missing: {wanted}")
        data = metadata(node)
        if data.get("canonical_ref") != record["new_canonical_ref"]:
            raise RepairBlocked(f"Plotinus KG canonical_ref drift: {wanted}")
        if data.get("cts_urn") != record["new_cts_urn"]:
            raise RepairBlocked(f"Plotinus KG cts_urn drift: {wanted}")
        if sha256_text(str(node.get("description") or "")) != record["evidence"][
            "description_sha256"
        ]:
            raise RepairBlocked(f"Plotinus byte-anchored description drift: {wanted}")
        anchor = data.get("tlg_anchor") or {}
        if (
            anchor.get("start_byte") != record["byte_anchor"]["start"]
            or anchor.get("end_byte") != record["byte_anchor"]["end"]
        ):
            raise RepairBlocked(f"Plotinus byte anchor drift: {wanted}")

        passage_id = str(data.get("db_passage_id") or "")
        passage = passages_by_id.get(passage_id)
        if passage is None:
            raise RepairBlocked(f"Plotinus corpus twin missing: {wanted}/{passage_id}")
        links = [
            row
            for row in citations
            if row.get("kg_node_id") == wanted
            and row.get("passage_id") == passage_id
        ]
        if len(links) != 1:
            raise RepairBlocked(
                f"Plotinus citation mapping {wanted}/{passage_id}: {len(links)} rows"
            )

        new_ref = record["new_canonical_ref"]
        new_urn = record["new_cts_urn"]
        if passage.get("canonical_ref") == new_ref and passage.get("cts_urn") == new_urn:
            continue
        source_index = record["source_fragment_index"]
        old_ref = f"Enn. VI.9.{source_index}"
        old_urn = (
            "urn:cts:greekLit:tlg2000.tlg001.perseus-grc1:"
            f"6.9.{source_index}"
        )
        if passage.get("canonical_ref") != old_ref or passage.get("cts_urn") != old_urn:
            raise RepairBlocked(
                f"Plotinus corpus precondition drift: {wanted} has "
                f"{passage.get('canonical_ref')!r}/{passage.get('cts_urn')!r}"
            )
        passage["canonical_ref"] = new_ref
        passage["cts_urn"] = new_urn
        changes["plotinus_corpus_twins"] += 1


def quarantine_fedou(
    nodes: list[dict[str, Any]], changes: Counter[str]
) -> tuple[dict[str, Any], ...]:
    records = derive_fedou_contamination(nodes)
    if not records:
        raise RepairBlocked("no Fédou-contaminated Origenality rows derived")
    nodes_by_id = {node_id(node): node for node in nodes}
    for record in records:
        node = nodes_by_id[record["node_id"]]
        if sha256_text(str(node.get("description") or "")) != record[
            "description_sha256"
        ]:
            raise RepairBlocked(f"Fédou description drift: {record['node_id']}")
        data = metadata(node)
        before = canonical_json(node)
        data["origenality_relevance"] = "reject"
        data["integrity_status"] = "origenality_bibliographic_span_contamination"
        data["quarantine_reason"] = record["reason"]
        data[STAMP] = "quarantined_fedou_false_core"
        set_metadata(node, data)
        if _record_changed(before, node):
            changes["fedou_quarantined"] += 1
    return records


def merge_sytsma(
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    changes: Counter[str],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    nodes_by_id = {node_id(node): node for node in nodes}
    duplicate = nodes_by_id.get(SYTSMA_DUPLICATE_ID)
    canonical = nodes_by_id.get(SYTSMA_CANONICAL_ID)
    if canonical is None:
        raise RepairBlocked("canonical, already-read Sytsma node is missing")
    canonical_data = metadata(canonical)

    if duplicate is None:
        if canonical_data.get(STAMP) != "merged_sytsma_dissertation_alias":
            raise RepairBlocked("Sytsma duplicate absent without merge stamp")
        if any(
            SYTSMA_DUPLICATE_ID in (edge.get("source"), edge.get("target"))
            for edge in edges
        ):
            raise RepairBlocked("Sytsma duplicate edges survive without its node")
        return nodes, edges

    duplicate_data = metadata(duplicate)
    duplicate_ids = set(duplicate_data.get("origenality_ids") or [])
    if SYTSMA_ORIGENALITY_ID not in duplicate_ids:
        raise RepairBlocked("Sytsma duplicate lost its Origenality identifier")
    if duplicate_data.get("bibliographic_type") != "dissertation":
        raise RepairBlocked("Sytsma duplicate is no longer identified as a dissertation")
    if "2018" not in str(canonical_data.get("phd_version") or ""):
        raise RepairBlocked("canonical Sytsma node lost its 2018 phd_version evidence")

    touching = [
        edge
        for edge in edges
        if edge.get("source") == SYTSMA_DUPLICATE_ID
        or edge.get("target") == SYTSMA_DUPLICATE_ID
    ]
    if len(touching) != 3 or any(
        edge.get("source") != SYTSMA_DUPLICATE_ID for edge in touching
    ):
        raise RepairBlocked(
            f"Sytsma duplicate edge precondition changed ({len(touching)} touching)"
        )

    origenality_ids = list(canonical_data.get("origenality_ids") or [])
    if SYTSMA_ORIGENALITY_ID not in origenality_ids:
        origenality_ids.append(SYTSMA_ORIGENALITY_ID)
    canonical_data["origenality_ids"] = sorted(set(origenality_ids))
    records = dict(canonical_data.get("origenality_records") or {})
    records[SYTSMA_ORIGENALITY_ID] = {
        "authors": duplicate_data.get("authors") or [duplicate_data.get("author")],
        "year": duplicate_data.get("year"),
        "title": duplicate_data.get("title"),
        "themes": duplicate_data.get("origenality_themes") or [],
        "relevance": duplicate_data.get("origenality_relevance"),
        "catalogues": (duplicate_data.get("provenance") or {}).get("catalogues", []),
        "merged_as": "phd_version",
    }
    canonical_data["origenality_records"] = records
    aliases = list(canonical_data.get("edition_aliases") or [])
    alias = {
        "former_node_id": SYTSMA_DUPLICATE_ID,
        "title": duplicate_data.get("title"),
        "year": duplicate_data.get("year"),
        "bibliographic_type": duplicate_data.get("bibliographic_type"),
        "origenality_id": SYTSMA_ORIGENALITY_ID,
        "relation": "phd_version",
    }
    if alias not in aliases:
        aliases.append(alias)
    canonical_data["edition_aliases"] = aliases
    canonical_data[STAMP] = "merged_sytsma_dissertation_alias"
    set_metadata(canonical, canonical_data)

    nodes = [node for node in nodes if node_id(node) != SYTSMA_DUPLICATE_ID]
    rewired: list[dict[str, Any]] = []
    existing = {
        edge_triple(edge)
        for edge in edges
        if edge.get("source") != SYTSMA_DUPLICATE_ID
        and edge.get("target") != SYTSMA_DUPLICATE_ID
    }
    for edge in edges:
        if edge.get("source") != SYTSMA_DUPLICATE_ID:
            rewired.append(edge)
            continue
        _set_edge_source(edge, SYTSMA_CANONICAL_ID)
        data = edge.get("metadata") if isinstance(edge.get("metadata"), dict) else {}
        data[STAMP] = "rewired_from_sytsma_dissertation_duplicate"
        edge["metadata"] = data
        if edge_triple(edge) in existing:
            changes["sytsma_duplicate_edges_dropped"] += 1
            continue
        existing.add(edge_triple(edge))
        rewired.append(edge)
        changes["sytsma_edges_rewired"] += 1
    changes["sytsma_nodes_merged"] += 1
    return nodes, rewired


def fix_simplicius(nodes: list[dict[str, Any]], changes: Counter[str]) -> None:
    nodes_by_id = {node_id(node): node for node in nodes}
    node = nodes_by_id.get(SIMPLICIUS_WORK_ID)
    if node is None:
        raise RepairBlocked("Simplicius work node missing")
    data = metadata(node)
    if data.get("canonical_id") != SIMPLICIUS_CANONICAL_URN:
        raise RepairBlocked("Simplicius canonical_id drift")
    if "4013" not in str(data.get("verified_reference") or ""):
        raise RepairBlocked("Simplicius verified_reference lost TLG4013 evidence")
    if "work_canonical_id" not in data:
        if data.get(STAMP) != "dropped_stale_theophrastus_work_id":
            raise RepairBlocked("Simplicius stale field absent without repair stamp")
        return
    if data.get("work_canonical_id") != SIMPLICIUS_STALE_URN:
        raise RepairBlocked("Simplicius work_canonical_id changed unexpectedly")
    data.pop("work_canonical_id", None)
    data.pop("ingestion_debt_2026_08_17_canonical_derived", None)
    data[STAMP] = "dropped_stale_theophrastus_work_id"
    data[f"{STAMP}_note"] = (
        "Removed tlg0093.tlg001 derived from the nine deleted Theophrastus "
        "passages; canonical_id tlg4013.tlg001 remains authoritative."
    )
    set_metadata(node, data)
    changes["simplicius_work_ids_fixed"] += 1


def _galen_new_work(old_work: dict[str, Any]) -> dict[str, Any]:
    node = copy.deepcopy(old_work)
    node["id"] = GALEN_NEW_WORK_ID
    node["node_id"] = GALEN_NEW_WORK_ID
    node["label"] = "Galen, De naturalibus facultatibus"
    node["description"] = (
        "Galen, De naturalibus facultatibus (Περὶ φυσικῶν δυνάμεων), "
        "books I-III."
    )
    set_metadata(
        node,
        {
            "author": "Galen",
            "language": "grc",
            "canonical_id": GALEN_NATURAL_FACULTIES_URN,
            "work_canonical_id": GALEN_NATURAL_FACULTIES_URN,
            "auto_generated": False,
            "citation_verdict": "corrected",
            "citation_verified": True,
            "verified_reference": (
                "Galen, De naturalibus facultatibus (Peri physikon dynameon), "
                "books 1-3; TLG 0057.010; ed. K. G. Kühn, Claudii Galeni "
                "Opera Omnia II, Leipzig 1821; digital text: "
                f"{GALEN_PRIMARY_SOURCE}."
            ),
            STAMP: "created_after_primary_text_readjudication",
        },
    )
    return node


def fix_galen(
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    passages: list[dict[str, Any]],
    changes: Counter[str],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    nodes_by_id = {node_id(node): node for node in nodes}
    passages_by_id = {str(row.get("passage_id")): row for row in passages}
    old_work = nodes_by_id.get(GALEN_OLD_WORK_ID)
    new_work = nodes_by_id.get(GALEN_NEW_WORK_ID)
    if old_work is None:
        raise RepairBlocked("Galen De placitis work node missing")

    old_data = metadata(old_work)
    if old_data.get("canonical_id") != GALEN_DE_PLACITIS_URN:
        raise RepairBlocked("Galen De placitis canonical_id drift")
    if new_work is not None:
        if metadata(new_work).get(STAMP) != "created_after_primary_text_readjudication":
            raise RepairBlocked("Galen natural-faculties work exists without repair stamp")
        return nodes, edges
    if old_data.get("work_canonical_id") != GALEN_NATURAL_FACULTIES_URN:
        raise RepairBlocked("Galen stale derived work_canonical_id drift")

    part_edges = {
        str(edge.get("source")): edge
        for edge in edges
        if edge.get("relation") == "part_of"
        and edge.get("target") == GALEN_OLD_WORK_ID
    }
    if set(part_edges) != {record["node_id"] for record in GALEN_PASSAGES}:
        raise RepairBlocked("Galen part_of population changed since adjudication")

    for record in GALEN_PASSAGES:
        node = nodes_by_id.get(record["node_id"])
        passage = passages_by_id.get(record["passage_id"])
        if node is None or passage is None:
            raise RepairBlocked(f"Galen book {record['book']} twin missing")
        if sha256_text(str(node.get("description") or "")) != record[
            "description_sha256"
        ]:
            raise RepairBlocked(f"Galen book {record['book']} KG text drift")
        if sha256_text(str(passage.get("text_content") or "")) != record[
            "corpus_text_sha256"
        ]:
            raise RepairBlocked(f"Galen book {record['book']} corpus text drift")
        if not str(node.get("description") or "").startswith(record["opening"]):
            raise RepairBlocked(f"Galen book {record['book']} opening mismatch")
        expected_book_urn = (
            f"{GALEN_NATURAL_FACULTIES_URN}.1st1K-grc1:{record['book']}"
        )
        if metadata(node).get("cts_urn") != expected_book_urn:
            raise RepairBlocked(f"Galen book {record['book']} CTS work mismatch")

    old_data.pop("work_canonical_id", None)
    old_data.pop("ingestion_debt_2026_08_17_canonical_derived", None)
    old_data["needs_text_ingestion"] = True
    old_data[STAMP] = "detached_misfiled_natural_faculties_books"
    old_data[f"{STAMP}_note"] = (
        "The three former children are complete books 1-3 of De naturalibus "
        "facultatibus (TLG0057.tlg010), verified from their Greek openings; "
        "De placitis (TLG0057.tlg032) now has no corpus text."
    )
    set_metadata(old_work, old_data)

    new_work = _galen_new_work(old_work)
    nodes.append(new_work)
    nodes_by_id[GALEN_NEW_WORK_ID] = new_work
    changes["galen_work_nodes_created"] += 1

    author_target = "person_galen_pergamon_129_216ce"
    authored = {
        "created_at": "2026-08-17 00:00:00+00:00",
        "edge_id": str(
            uuid.uuid5(
                uuid.NAMESPACE_URL,
                f"eleutheria:{GALEN_NEW_WORK_ID}:authored_by:{author_target}",
            )
        ),
        "metadata": {
            "auto_generated": False,
            STAMP: "natural_faculties_work_adjudication",
        },
        "relation": "authored_by",
        "source": GALEN_NEW_WORK_ID,
        "source_id": GALEN_NEW_WORK_ID,
        "target": author_target,
        "target_id": author_target,
        "weight": 1.0,
    }
    edges.append(authored)
    changes["galen_edges_created"] += 1

    for record in GALEN_PASSAGES:
        node = nodes_by_id[record["node_id"]]
        passage = passages_by_id[record["passage_id"]]
        book = record["book"]
        canonical_ref = f"Nat. Fac. {record['chapters']}"
        cts_urn = (
            f"{GALEN_NATURAL_FACULTIES_URN}.1st1K-grc1:{record['chapters']}"
        )
        node["label"] = f"Galen, De naturalibus facultatibus, {canonical_ref}"
        data = metadata(node)
        data["work_title"] = "De naturalibus facultatibus"
        data["canonical_ref"] = canonical_ref
        data["cts_urn"] = cts_urn
        data["work_canonical_id"] = GALEN_NATURAL_FACULTIES_URN
        data[STAMP] = "readjudicated_as_de_naturalibus_facultatibus"
        data[f"{STAMP}_evidence"] = {
            "source": GALEN_PRIMARY_SOURCE,
            "book": book,
            "description_sha256": record["description_sha256"],
        }
        set_metadata(node, data)
        passage["canonical_ref"] = canonical_ref
        passage["cts_urn"] = cts_urn
        edge = part_edges[record["node_id"]]
        _set_edge_target(edge, GALEN_NEW_WORK_ID)
        edge_data = (
            edge.get("metadata") if isinstance(edge.get("metadata"), dict) else {}
        )
        edge_data[STAMP] = "readjudicated_as_de_naturalibus_facultatibus"
        edge["metadata"] = edge_data
        changes["galen_passage_twins_fixed"] += 1
        changes["galen_part_of_edges_rewired"] += 1
    return nodes, edges


def fix_methodius(
    nodes: list[dict[str, Any]],
    passages: list[dict[str, Any]],
    citations: list[dict[str, Any]],
    manifest: list[dict[str, Any]],
    changes: Counter[str],
) -> tuple[dict[str, Any], ...]:
    records = derive_methodius_spans(passages, nodes)
    manifest_rows = [
        row
        for row in manifest
        if row.get("canonical_id") in {METHODIUS_OLD_WORK_ID, METHODIUS_NEW_WORK_ID}
        and row.get("title") == "De Libero Arbitrio"
    ]
    if len(manifest_rows) != 1:
        raise RepairBlocked(
            f"Methodius manifest precondition: {len(manifest_rows)} matching rows"
        )
    manifest_row = manifest_rows[0]
    if len(records) != int(manifest_row.get("passages") or 0):
        raise RepairBlocked(
            "Methodius derived span count differs from the corpus manifest: "
            f"{len(records)} vs {manifest_row.get('passages')}"
        )
    if len({record["source_span_id"] for record in records}) != len(records):
        raise RepairBlocked("Methodius source_span_id derivation is not unique")

    nodes_by_id = {node_id(node): node for node in nodes}
    passages_by_id = {str(row.get("passage_id")): row for row in passages}
    citation_pairs = {
        (str(row.get("passage_id")), str(row.get("kg_node_id")))
        for row in citations
    }
    for record in records:
        node = nodes_by_id[record["node_id"]]
        passage = passages_by_id[record["passage_id"]]
        if sha256_text(str(node.get("description") or "")) != record[
            "node_description_sha256"
        ]:
            raise RepairBlocked(f"Methodius KG text drift: {record['node_id']}")
        if sha256_text(str(passage.get("text_content") or "")) != record[
            "passage_text_sha256"
        ]:
            raise RepairBlocked(f"Methodius corpus text drift: {record['passage_id']}")
        if (record["passage_id"], record["node_id"]) not in citation_pairs:
            raise RepairBlocked(f"Methodius twin citation missing: {record['node_id']}")

        before_passage = canonical_json(passage)
        passage["cts_urn"] = METHODIUS_WORK_URN
        passage["work_canonical_id"] = METHODIUS_NEW_WORK_ID
        passage["source_span_id"] = record["source_span_id"]
        passage[STAMP] = "demoted_to_work_urn_plus_source_span"
        if _record_changed(before_passage, passage):
            changes["methodius_corpus_spans_fixed"] += 1

        data = metadata(node)
        if data.get("cts_urn") not in {
            f"{METHODIUS_WORK_URN}:1.1",
            METHODIUS_WORK_URN,
        }:
            raise RepairBlocked(f"Methodius KG CTS precondition drift: {record['node_id']}")
        if data.get("work_canonical_id") not in {
            METHODIUS_OLD_KG_WORK_ID,
            METHODIUS_WORK_URN,
        }:
            raise RepairBlocked(
                f"Methodius KG work id precondition drift: {record['node_id']}"
            )
        before_node = canonical_json(node)
        data["cts_urn"] = METHODIUS_WORK_URN
        data["work_canonical_id"] = METHODIUS_WORK_URN
        data["source_span_id"] = record["source_span_id"]
        data["reference_precision"] = "work_urn_plus_source_span"
        data[STAMP] = "demoted_to_work_urn_plus_source_span"
        set_metadata(node, data)
        if _record_changed(before_node, node):
            changes["methodius_kg_twins_fixed"] += 1

    before_manifest = canonical_json(manifest_row)
    manifest_row["canonical_id"] = METHODIUS_NEW_WORK_ID
    manifest_row["cts_urn"] = METHODIUS_WORK_URN
    manifest_row["source"] = "GCS 27 (1917) apparatus extraction"
    manifest_row["source_span_id_scheme"] = f"{METHODIUS_SPAN_PREFIX}NNN"
    manifest_row[STAMP] = "demoted_to_work_urn_plus_source_span"
    if _record_changed(before_manifest, manifest_row):
        changes["methodius_manifest_fixed"] += 1
    return records


def clean_citations(
    citations: list[dict[str, Any]],
    nodes: list[dict[str, Any]],
    passages: list[dict[str, Any]],
    changes: Counter[str],
) -> list[dict[str, Any]]:
    seen: set[str] = set()
    deduplicated: list[dict[str, Any]] = []
    for citation in citations:
        key = canonical_json(citation)
        if key in seen:
            changes["exact_citation_rows_deduplicated"] += 1
            continue
        seen.add(key)
        deduplicated.append(citation)

    node_ids = {node_id(node) for node in nodes}
    passage_ids = {str(row.get("passage_id")) for row in passages}
    cleaned: list[dict[str, Any]] = []
    expected_nodes = set(THEOPHRASTUS_MISFILED_NODES)
    expected_passages = set(THEOPHRASTUS_MISFILED_CORPUS_IDS)
    removed_pairs: set[tuple[str, str]] = set()
    unexpected: list[dict[str, Any]] = []
    for citation in deduplicated:
        kg_node_id = str(citation.get("kg_node_id") or "")
        passage_id = str(citation.get("passage_id") or "")
        if kg_node_id in node_ids and passage_id in passage_ids:
            cleaned.append(citation)
            continue
        if kg_node_id in expected_nodes and passage_id in expected_passages:
            removed_pairs.add((passage_id, kg_node_id))
            changes["theophrastus_dangling_citations_removed"] += 1
            continue
        unexpected.append(citation)
    if unexpected:
        raise RepairBlocked(
            f"{len(unexpected)} unexpected dangling citations remain; first="
            f"{unexpected[0]!r}"
        )
    if removed_pairs and (
        {node for _, node in removed_pairs} != expected_nodes
        or {passage for passage, _ in removed_pairs} != expected_passages
    ):
        raise RepairBlocked("Theophrastus dangling citation population is incomplete")
    return cleaned


def touched_locus_parity(
    nodes: list[dict[str, Any]], passages: list[dict[str, Any]]
) -> tuple[int, list[str]]:
    prefixes = (
        "passage_plotinus_vi_9_",
        "passage_meth_dla_",
        "passage_galen_plac_",
    )
    passages_by_id = {str(row.get("passage_id")): row for row in passages}
    compared = 0
    errors: list[str] = []
    for node in nodes:
        wanted = node_id(node)
        if not wanted.startswith(prefixes):
            continue
        data = metadata(node)
        passage_id = str(data.get("db_passage_id") or "")
        if not passage_id:
            continue
        passage = passages_by_id.get(passage_id)
        if passage is None:
            errors.append(f"{wanted}: missing corpus twin {passage_id}")
            continue
        compared += 1
        for field in ("canonical_ref", "cts_urn"):
            if data.get(field) != passage.get(field):
                errors.append(
                    f"{wanted}: {field} KG={data.get(field)!r} "
                    f"corpus={passage.get(field)!r}"
                )
    return compared, errors


def check_invariants(
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    passages: list[dict[str, Any]],
    citations: list[dict[str, Any]],
    manifest: list[dict[str, Any]],
    before_descriptions: dict[str, str],
    before_corpus_text: dict[str, str],
    fedou_records: tuple[dict[str, Any], ...],
    methodius_records: tuple[dict[str, Any], ...],
) -> dict[str, int]:
    node_ids = [node_id(node) for node in nodes]
    if len(node_ids) != len(set(node_ids)):
        raise AssertionError("duplicate node ids")
    present = set(node_ids)
    dangling_edges = [
        edge
        for edge in edges
        if edge.get("source") not in present or edge.get("target") not in present
    ]
    if dangling_edges:
        raise AssertionError(f"{len(dangling_edges)} dangling edges")
    split_edges = [
        edge
        for edge in edges
        if edge.get("source") != edge.get("source_id")
        or edge.get("target") != edge.get("target_id")
    ]
    if split_edges:
        raise AssertionError(f"{len(split_edges)} split edge endpoints")
    triples = [edge_triple(edge) for edge in edges]
    if len(triples) != len(set(triples)):
        raise AssertionError("duplicate edge triples")

    passage_ids = [str(row.get("passage_id")) for row in passages]
    if len(passage_ids) != len(set(passage_ids)):
        raise AssertionError("duplicate corpus passage ids")
    full_citations = [canonical_json(row) for row in citations]
    if len(full_citations) != len(set(full_citations)):
        raise AssertionError("duplicate exact citation rows")
    citation_triples = [
        (
            row.get("passage_id"),
            row.get("kg_node_id"),
            row.get("citation_type"),
        )
        for row in citations
    ]
    if len(citation_triples) != len(set(citation_triples)):
        raise AssertionError("duplicate citation triplets")
    dangling_citations = [
        row
        for row in citations
        if row.get("passage_id") not in set(passage_ids)
        or row.get("kg_node_id") not in present
    ]
    if dangling_citations:
        raise AssertionError(f"{len(dangling_citations)} dangling citations")

    nodes_by_id = {node_id(node): node for node in nodes}
    for wanted, digest in before_descriptions.items():
        if wanted == SYTSMA_DUPLICATE_ID:
            continue
        node = nodes_by_id.get(wanted)
        if node is None or sha256_text(str(node.get("description") or "")) != digest:
            raise AssertionError(f"existing node description changed: {wanted}")
    passages_by_id = {str(row.get("passage_id")): row for row in passages}
    for passage_id, digest in before_corpus_text.items():
        row = passages_by_id.get(passage_id)
        if row is None or sha256_text(str(row.get("text_content") or "")) != digest:
            raise AssertionError(f"corpus text changed: {passage_id}")

    for record in PLOTINUS_REMAP_RECORDS:
        node = nodes_by_id[record["node_id"]]
        data = metadata(node)
        passage = passages_by_id[str(data["db_passage_id"])]
        if (
            passage.get("canonical_ref") != record["new_canonical_ref"]
            or passage.get("cts_urn") != record["new_cts_urn"]
        ):
            raise AssertionError(f"Plotinus parity incomplete: {record['node_id']}")

    for record in fedou_records:
        data = metadata(nodes_by_id[record["node_id"]])
        if (
            data.get("origenality_relevance") != "reject"
            or data.get("integrity_status")
            != "origenality_bibliographic_span_contamination"
        ):
            raise AssertionError(f"Fédou quarantine incomplete: {record['node_id']}")

    if SYTSMA_DUPLICATE_ID in present:
        raise AssertionError("Sytsma duplicate node survives")
    if any(
        SYTSMA_DUPLICATE_ID in (edge.get("source"), edge.get("target"))
        for edge in edges
    ):
        raise AssertionError("Sytsma duplicate edges survive")
    canonical_sytsma = metadata(nodes_by_id[SYTSMA_CANONICAL_ID])
    if SYTSMA_ORIGENALITY_ID not in canonical_sytsma.get("origenality_ids", []):
        raise AssertionError("Sytsma Origenality alias was not merged")

    simplicius = metadata(nodes_by_id[SIMPLICIUS_WORK_ID])
    if "work_canonical_id" in simplicius or (
        simplicius.get("canonical_id") != SIMPLICIUS_CANONICAL_URN
    ):
        raise AssertionError("Simplicius internal work id remains contradictory")

    old_galen = metadata(nodes_by_id[GALEN_OLD_WORK_ID])
    new_galen = metadata(nodes_by_id[GALEN_NEW_WORK_ID])
    if "work_canonical_id" in old_galen:
        raise AssertionError("Galen De placitis retained the derived tlg010 id")
    if new_galen.get("canonical_id") != GALEN_NATURAL_FACULTIES_URN:
        raise AssertionError("Galen natural-faculties work id is wrong")
    galen_parts = {
        edge.get("source")
        for edge in edges
        if edge.get("relation") == "part_of"
        and edge.get("target") == GALEN_NEW_WORK_ID
    }
    if galen_parts != {record["node_id"] for record in GALEN_PASSAGES}:
        raise AssertionError("Galen books were not re-homed together")

    derived_after = derive_methodius_spans(passages, nodes)
    if len(derived_after) != len(methodius_records):
        raise AssertionError("Methodius source-span population changed")
    for record in derived_after:
        node_data = metadata(nodes_by_id[record["node_id"]])
        passage = passages_by_id[record["passage_id"]]
        if (
            node_data.get("cts_urn") != METHODIUS_WORK_URN
            or passage.get("cts_urn") != METHODIUS_WORK_URN
            or node_data.get("source_span_id") != record["source_span_id"]
            or passage.get("source_span_id") != record["source_span_id"]
        ):
            raise AssertionError(f"Methodius span incomplete: {record['node_id']}")
    if any(
        row.get("cts_urn") == METHODIUS_BAD_PASSAGE_URN for row in passages
    ):
        raise AssertionError("wrong Sosiphanes Methodius URN survives")

    compared, parity_errors = touched_locus_parity(nodes, passages)
    if parity_errors:
        raise AssertionError(
            f"{len(parity_errors)} touched KG/corpus locus mismatches; "
            f"first={parity_errors[0]}"
        )
    if compared != len(PLOTINUS_REMAP_RECORDS) + len(methodius_records) + len(
        GALEN_PASSAGES
    ):
        raise AssertionError(f"unexpected touched parity population: {compared}")

    return {
        "unique_node_ids": len(node_ids),
        "edges": len(edges),
        "unique_passage_ids": len(passage_ids),
        "citations": len(citations),
        "dangling_edges": len(dangling_edges),
        "dangling_citations": len(dangling_citations),
        "duplicate_citation_rows": len(full_citations) - len(set(full_citations)),
        "locus_pairs_checked": compared,
        "fedou_quarantined": len(fedou_records),
        "methodius_source_spans": len(methodius_records),
        "manifest_rows": len(manifest),
    }


def build_stats(
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    passages: list[dict[str, Any]],
    citations: list[dict[str, Any]],
    manifest: list[dict[str, Any]],
) -> dict[str, Any]:
    from gen_stats import ontology_stats

    node_types = Counter(str(node.get("type", "unknown")) for node in nodes)
    relations = Counter(str(edge.get("relation", "unknown")) for edge in edges)
    works_with_text = {
        str(row.get("work_canonical_id"))
        for row in passages
        if row.get("work_canonical_id")
    }
    manifest_status = Counter(
        str(row.get("status", "unknown")) for row in manifest
    )
    return {
        "generated_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
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
            "edge_relations_in_use": len(relations),
            "node_type_counts": dict(node_types.most_common()),
            "edge_relation_counts": dict(relations.most_common()),
        },
        "corpus": {
            "passages": len(passages),
            "works_with_text": len(works_with_text),
            "passage_citations": len(citations),
            "manifest_entries": len(manifest),
            "manifest_status_counts": dict(manifest_status.most_common()),
        },
        "ontology": ontology_stats(),
    }


def mutate(
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    passages: list[dict[str, Any]],
    citations: list[dict[str, Any]],
    manifest: list[dict[str, Any]],
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    Counter[str],
    tuple[dict[str, Any], ...],
    tuple[dict[str, Any], ...],
]:
    changes: Counter[str] = Counter()
    rewrite_plotinus_corpus(nodes, passages, citations, changes)
    fedou_records = quarantine_fedou(nodes, changes)
    nodes, edges = merge_sytsma(nodes, edges, changes)
    fix_simplicius(nodes, changes)
    nodes, edges = fix_galen(nodes, edges, passages, changes)
    methodius_records = fix_methodius(
        nodes, passages, citations, manifest, changes
    )
    citations = clean_citations(citations, nodes, passages, changes)
    return (
        nodes,
        edges,
        passages,
        citations,
        manifest,
        changes,
        fedou_records,
        methodius_records,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="validate only (default)")
    mode.add_argument("--write", action="store_true", help="write selected data root")
    parser.add_argument(
        "--data-root",
        help=(
            "directory containing kg/ and corpus/; "
            f"or set {DATA_ROOT_ENV}"
        ),
    )
    args = parser.parse_args()

    check_payload()
    selected = args.data_root or os.environ.get(DATA_ROOT_ENV)
    data_root = (
        Path(selected).expanduser().resolve() if selected else DEFAULT_DATA_ROOT
    )
    paths = {
        "nodes": data_root / "kg" / "nodes.jsonl",
        "edges": data_root / "kg" / "edges.jsonl",
        "passages": data_root / "corpus" / "passages.jsonl",
        "citations": data_root / "corpus" / "citations.jsonl",
        "manifest": data_root / "corpus" / "manifest.jsonl",
        "stats_json": data_root / "stats.json",
        "stats_md": data_root / "stats.md",
    }
    for key in ("nodes", "edges", "passages", "citations", "manifest"):
        if not paths[key].is_file():
            parser.error(f"data file not found: {paths[key]}")

    nodes = read_jsonl(paths["nodes"])
    edges = read_jsonl(paths["edges"])
    passages = read_jsonl(paths["passages"])
    citations = read_jsonl(paths["citations"])
    manifest = read_jsonl(paths["manifest"])
    before_counts = {
        "nodes": len(nodes),
        "edges": len(edges),
        "passages": len(passages),
        "citations": len(citations),
    }
    before_descriptions = {
        node_id(node): sha256_text(str(node.get("description") or ""))
        for node in nodes
    }
    before_corpus_text = {
        str(row.get("passage_id")): sha256_text(str(row.get("text_content") or ""))
        for row in passages
    }

    try:
        (
            nodes,
            edges,
            passages,
            citations,
            manifest,
            changes,
            fedou_records,
            methodius_records,
        ) = mutate(nodes, edges, passages, citations, manifest)
        invariants = check_invariants(
            nodes,
            edges,
            passages,
            citations,
            manifest,
            before_descriptions,
            before_corpus_text,
            fedou_records,
            methodius_records,
        )

        second = mutate(
            copy.deepcopy(nodes),
            copy.deepcopy(edges),
            copy.deepcopy(passages),
            copy.deepcopy(citations),
            copy.deepcopy(manifest),
        )
        second_changes = second[5]
        if sum(second_changes.values()):
            raise AssertionError(f"idempotence failed: {dict(second_changes)}")
    except (RepairBlocked, AssertionError, ValueError) as exc:
        print(f"mode: {'write' if args.write else 'dry-run'}")
        print(f"precondition/invariant: BLOCKED — {exc}")
        print("write: blocked")
        return 1

    stats = build_stats(nodes, edges, passages, citations, manifest)
    print(f"mode: {'write' if args.write else 'dry-run'}")
    print(
        "rows: "
        f"nodes {before_counts['nodes']} -> {len(nodes)}; "
        f"edges {before_counts['edges']} -> {len(edges)}; "
        f"passages {before_counts['passages']} -> {len(passages)}; "
        f"citations {before_counts['citations']} -> {len(citations)}"
    )
    print("changes:")
    for key in sorted(changes):
        print(f"  {key}: {changes[key]}")
    print(
        "derived populations: "
        f"Fédou={len(fedou_records)}; "
        f"Methodius={len(methodius_records)}; "
        f"Plotinus={len(PLOTINUS_REMAP_RECORDS)}; "
        f"Galen={len(GALEN_PASSAGES)}"
    )
    print(
        "invariants: OK "
        f"(nodes={invariants['unique_node_ids']}; edges={invariants['edges']}; "
        f"passages={invariants['unique_passage_ids']}; "
        f"citations={invariants['citations']}; "
        f"dangling edges={invariants['dangling_edges']}; "
        f"dangling citations={invariants['dangling_citations']}; "
        f"duplicate citation rows={invariants['duplicate_citation_rows']}; "
        f"locus pairs={invariants['locus_pairs_checked']}; "
        f"Methodius spans={invariants['methodius_source_spans']})"
    )
    print(
        "predicted stats: "
        f"nodes={stats['kg']['nodes']} edges={stats['kg']['edges']} "
        f"works={stats['kg']['works']} publications="
        f"{stats['kg']['node_type_counts'].get('publication', 0)} "
        f"passages={stats['corpus']['passages']} "
        f"citations={stats['corpus']['passage_citations']}"
    )
    print("idempotence: OK (second pass: 0 changes)")

    if not args.write:
        print("write: disabled (--dry-run default)")
        return 0
    if sum(changes.values()) == 0:
        print("write: no-op (0 changes)")
        return 0

    from gen_stats import markdown_snippet

    writable = (
        paths["nodes"],
        paths["edges"],
        paths["passages"],
        paths["citations"],
        paths["manifest"],
        paths["stats_json"],
        paths["stats_md"],
    )
    for path in writable:
        if path.exists():
            backup = Path(str(path) + BACKUP_SUFFIX)
            if not backup.exists():
                shutil.copyfile(path, backup)
    write_jsonl(paths["nodes"], nodes)
    write_jsonl(paths["edges"], edges)
    write_jsonl(paths["passages"], passages)
    write_jsonl(paths["citations"], citations)
    write_jsonl(paths["manifest"], manifest)
    _atomic_text(
        paths["stats_json"],
        json.dumps(stats, indent=2, ensure_ascii=False) + "\n",
    )
    _atomic_text(paths["stats_md"], markdown_snippet(stats))
    print("wrote:")
    for path in writable:
        print(f"  {path}")
    print(f"backups: *{BACKUP_SUFFIX}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
