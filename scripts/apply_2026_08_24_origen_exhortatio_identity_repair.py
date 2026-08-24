#!/usr/bin/env python3
"""Prepare/apply Origen Exhortatio ad martyrium identity repair (Wave 0.2).

The 51 corpus texts are already Origen's *Exhortatio ad martyrium* and are
exact (after NFC normalization) to the pinned OpenGreekAndLatin edition
``tlg2042.tlg007.perseus-grc1``.  The remaining defect is an old Clement /
Protrepticus identity collision in the corpus manifest, two contradictory work
nodes, and the stable-but-misleading passage node ids
``passage_clement_protr_1..51``.

Dry-run is the default and writes nothing.  ``--write`` is deliberately
available for the later authorized cut-over only.  Before any write it:

* verifies SHA-256-pinned OGL catalogs for Origen and Clement;
* verifies all 51 local texts against the pinned OGL TEI;
* constructs the 51-id alias remap wholly in memory;
* remaps node ids, all 102 edge endpoints, 51 snapshot citations, and the 51
  corpus parity pointers as one validated cohort;
* preserves every corpus passage UUID, text, canonical reference and CTS locus;
* emits deterministic before-image quarantine and alias/audit artifacts.

No registry shard is changed by this wave.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import shutil
import tempfile
import unicodedata
import urllib.request
import xml.etree.ElementTree as ET
from collections import Counter
from collections.abc import Callable
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_ROOT = ROOT / "data"

STAMP = "origen_exhortatio_identity_repair_2026_08_24"
UPDATED_AT = "2026-08-24 06:00:00+00:00"
DECIDED_AT = "2026-08-24T06:00:00Z"

ORIGEN_WORK_NODE = "work_origen_exhortation_martyrdom"
CLEMENT_WORK_NODE = "work_clement_protrepticus"
ORIGEN_PERSON_NODE = "person_origen_alexandria_185_254ce_s9t0u1v2"
CLEMENT_PERSON_NODE = "person_clement_alexandria"

ORIGEN_WORK_URN = "urn:cts:greekLit:tlg2042.tlg007"
ORIGEN_EDITION_URN = f"{ORIGEN_WORK_URN}.perseus-grc1"
CLEMENT_WORK_URN = "urn:cts:greekLit:tlg0555.tlg001"
CLEMENT_EDITION_URN = f"{CLEMENT_WORK_URN}.1st1K-grc1"
CORPUS_CANONICAL_ID = "urn_cts_greeklit_tlg2042_tlg007_grc"

NODE_ALIASES = {
    f"passage_clement_protr_{section}": f"passage_origen_exh_mart_{section}"
    for section in range(1, 52)
}
OLD_NODE_IDS = frozenset(NODE_ALIASES)
NEW_NODE_IDS = frozenset(NODE_ALIASES.values())

OGL_COMMIT = "7881c563436f52fb3550e6daa6df94be1b83b0e3"
OGL_BASE = (
    "https://raw.githubusercontent.com/OpenGreekAndLatin/First1KGreek/"
    f"{OGL_COMMIT}/data"
)
OGL_URLS = {
    "origen_cts": f"{OGL_BASE}/tlg2042/tlg007/__cts__.xml",
    "origen_tei": (
        f"{OGL_BASE}/tlg2042/tlg007/"
        "tlg2042.tlg007.perseus-grc1.xml"
    ),
    "clement_cts": f"{OGL_BASE}/tlg0555/tlg001/__cts__.xml",
}
OGL_SHA256 = {
    "origen_cts": "cc1a2aed4c7807ae514dd155c3a3bac0afe7f4b745df51a4d167373f598229c0",
    "origen_tei": "dedb6ae89519545a0ab274061c858a0549760bb3ac97223a5f744130c13fb83b",
    "clement_cts": "d13512707fe1e4a4f38ab8201f2dc91d08c55959fdde3fec762278b4ec7ee5dd",
}

# Exact before-image cohorts at the read-only audit cut.  These make the
# migration fail closed if a target changed while another wave was running.
LEGACY_TARGET_SHA256 = {
    "work_nodes": "2435e8596767a7f1d88163d5430e334e38f3a418f043b19d0a1b7205903420ab",
    "passage_nodes": "aff2700d23f8718710197a37fdcdeda68afef6a322e7a261ddddc89dd5480caa",
    "edges": "2623a5ed8a29da583187c32d7df2616edfe7e0c3307436ca4cf2aa74118f7b69",
    "citations": "72d835bf22b496a11f541f5431a2a18cf132e7b54c907d9380e5a900ade61168",
    "passages": "29ab9395074a4bd4476623f250b0d43036bf8ed9df5590d72d84f5843dfc2759",
    "manifest": "01ca0c8bc1174be977c5618e73e60d733103a0a690f9e7ba9f26e215f9c21133",
}
EXPECTED_PASSAGE_EVIDENCE_SHA256 = (
    "ef7930e8f2213ed21e36587cbe5b568ab393db8de0b3d9d8d1f6fe71c341b3ef"
)
EXPECTED_PASSAGE_UUIDS_SHA256 = (
    "79f6d341b552a20f78cd43bac8b3eef43067e0c626ad537ca435b750182e4a01"
)
EXPECTED_PASSAGE_TEXTS_RAW_SHA256 = (
    "86fee4ca89a0616e2c568e844e3d3168f53632b5f69a8ede34ed22db8c695860"
)

REPORT_RELATIVE = "audit/2026-08-24_origen_exhortatio_identity_repair.json"
QUARANTINE_RELATIVE = (
    "audit/2026-08-24_origen_exhortatio_identity_quarantine.jsonl"
)
ALIASES_RELATIVE = "audit/2026-08-24_origen_exhortatio_node_aliases.json"
TRANSACTION_PREFIX = ".origen-exhortatio-wave-0-2-"
TRANSACTION_JOURNAL = "transaction.json"


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def node_id(node: dict[str, Any]) -> str:
    return str(node.get("id") or node.get("node_id") or "")


def metadata(node: dict[str, Any]) -> dict[str, Any]:
    value = node.get("metadata")
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            return {}
    return copy.deepcopy(value) if isinstance(value, dict) else {}


def set_metadata(node: dict[str, Any], value: dict[str, Any]) -> None:
    if isinstance(node.get("metadata"), str):
        node["metadata"] = json.dumps(value, ensure_ascii=False, sort_keys=True)
    else:
        node["metadata"] = value


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_text(value: str) -> str:
    return sha256_bytes(value.encode("utf-8"))


def nfc(value: str) -> str:
    return unicodedata.normalize("NFC", value)


def canonical_digest(value: Any) -> str:
    raw = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return sha256_bytes(raw)


def expected_old_node(section: int) -> str:
    return f"passage_clement_protr_{section}"


def expected_new_node(section: int) -> str:
    return f"passage_origen_exh_mart_{section}"


def expected_ref(section: int) -> str:
    return f"Exh. mart. {section}"


def expected_cts(section: int) -> str:
    # Preserve the already-correct work-level CTS loci in this identity-only wave.
    return f"{ORIGEN_WORK_URN}:{section}"


def passage_rows(passages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = [
        row
        for row in passages
        if row.get("work_canonical_id") == CORPUS_CANONICAL_ID
    ]
    return sorted(rows, key=lambda row: int(row.get("sequence_number") or 0))


def target_manifest_rows(manifest: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        row for row in manifest if row.get("canonical_id") == CORPUS_CANONICAL_ID
    ]


def target_node_mode(nodes: list[dict[str, Any]]) -> str:
    ids = {node_id(node) for node in nodes}
    old = ids & OLD_NODE_IDS
    new = ids & NEW_NODE_IDS
    if old == OLD_NODE_IDS and not new:
        return "legacy"
    if new == NEW_NODE_IDS and not old:
        return "repaired"
    raise RuntimeError(
        "mixed/incomplete Exhortatio alias cohort: "
        f"old={len(old)}/51 new={len(new)}/51"
    )


def _target_cohorts(
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    passages: list[dict[str, Any]],
    citations: list[dict[str, Any]],
    manifest: list[dict[str, Any]],
    *,
    mode: str,
) -> dict[str, list[dict[str, Any]]]:
    active_ids = OLD_NODE_IDS if mode == "legacy" else NEW_NODE_IDS
    return {
        "work_nodes": sorted(
            (
                node
                for node in nodes
                if node_id(node) in {ORIGEN_WORK_NODE, CLEMENT_WORK_NODE}
            ),
            key=node_id,
        ),
        "passage_nodes": sorted(
            (node for node in nodes if node_id(node) in active_ids), key=node_id
        ),
        "edges": sorted(
            (
                edge
                for edge in edges
                if str(edge.get("source") or edge.get("source_id") or "")
                in active_ids
                or str(edge.get("target") or edge.get("target_id") or "")
                in active_ids
            ),
            key=lambda edge: str(edge.get("edge_id") or ""),
        ),
        "citations": sorted(
            (
                row
                for row in citations
                if str(row.get("kg_node_id") or "") in active_ids
            ),
            key=lambda row: (
                str(row.get("passage_id") or ""),
                str(row.get("kg_node_id") or ""),
            ),
        ),
        "passages": passage_rows(passages),
        "manifest": sorted(
            target_manifest_rows(manifest),
            key=lambda row: str(row.get("canonical_id") or ""),
        ),
    }


def validate_legacy_preimage(
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    passages: list[dict[str, Any]],
    citations: list[dict[str, Any]],
    manifest: list[dict[str, Any]],
) -> None:
    cohorts = _target_cohorts(
        nodes, edges, passages, citations, manifest, mode="legacy"
    )
    actual = {label: canonical_digest(rows) for label, rows in cohorts.items()}
    if actual != LEGACY_TARGET_SHA256:
        drift = {
            label: {"actual": actual[label], "expected": expected}
            for label, expected in LEGACY_TARGET_SHA256.items()
            if actual[label] != expected
        }
        raise RuntimeError(f"Exhortatio legacy preimage drift: {drift}")


def immutable_passage_evidence(passages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    evidence: list[dict[str, Any]] = []
    for row in passage_rows(passages):
        section = int(row.get("sequence_number") or 0)
        evidence.append(
            {
                "canonical_ref": row.get("canonical_ref"),
                "cts_urn": row.get("cts_urn"),
                "passage_id": row.get("passage_id"),
                "section": section,
                "text_sha256_nfc": sha256_text(
                    nfc(str(row.get("text_content") or ""))
                ),
            }
        )
    return evidence


def validate_immutable_passages(passages: list[dict[str, Any]]) -> None:
    rows = passage_rows(passages)
    if len(rows) != 51:
        raise RuntimeError(f"expected 51 Exhortatio corpus passages, found {len(rows)}")
    if [int(row.get("sequence_number") or 0) for row in rows] != list(range(1, 52)):
        raise RuntimeError("Exhortatio corpus sequence is not exactly 1..51")
    for section, row in enumerate(rows, 1):
        if row.get("canonical_ref") != expected_ref(section):
            raise RuntimeError(f"unexpected Exhortatio ref at section {section}")
        if row.get("cts_urn") != expected_cts(section):
            raise RuntimeError(f"unexpected Exhortatio CTS at section {section}")
    if canonical_digest(immutable_passage_evidence(passages)) != (
        EXPECTED_PASSAGE_EVIDENCE_SHA256
    ):
        raise RuntimeError("Exhortatio UUID/ref/CTS/text evidence cohort drift")
    uuid_digest = sha256_text(
        "\n".join(str(row.get("passage_id") or "") for row in rows)
    )
    if uuid_digest != EXPECTED_PASSAGE_UUIDS_SHA256:
        raise RuntimeError("Exhortatio passage UUID cohort drift")
    raw_text_digest = sha256_text(
        "\n".join(str(row.get("text_content") or "") for row in rows)
    )
    if raw_text_digest != EXPECTED_PASSAGE_TEXTS_RAW_SHA256:
        raise RuntimeError("Exhortatio raw text cohort drift")


def validate_topology(
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    passages: list[dict[str, Any]],
    citations: list[dict[str, Any]],
    manifest: list[dict[str, Any]],
    *,
    mode: str,
) -> dict[str, int]:
    active_ids = OLD_NODE_IDS if mode == "legacy" else NEW_NODE_IDS
    by_node: dict[str, dict[str, Any]] = {}
    for node in nodes:
        wanted = node_id(node)
        if not wanted or wanted in by_node:
            raise RuntimeError(f"empty/duplicate KG node id: {wanted!r}")
        if (
            wanted
            in {
                ORIGEN_WORK_NODE,
                CLEMENT_WORK_NODE,
                *active_ids,
            }
            and node.get("id") != node.get("node_id")
        ):
            raise RuntimeError(f"id/node_id mismatch: {wanted}")
        by_node[wanted] = node

    corpus = {str(row.get("passage_id") or ""): row for row in passages}
    if len(corpus) != len(passages):
        raise RuntimeError("duplicate corpus passage ids")
    rows = passage_rows(passages)
    for section, row in enumerate(rows, 1):
        wanted_node = (
            expected_old_node(section)
            if mode == "legacy"
            else expected_new_node(section)
        )
        node = by_node.get(wanted_node)
        if node is None:
            raise RuntimeError(f"missing Exhortatio passage node: {wanted_node}")
        data = metadata(node)
        if (
            data.get("author") != "Origen of Alexandria"
            or data.get("language") != "grc"
            or data.get("work_title") != "Exhortatio ad martyrium"
            or data.get("work_canonical_id") != ORIGEN_WORK_URN
            or data.get("canonical_ref") != expected_ref(section)
            or data.get("cts_urn") != expected_cts(section)
            or data.get("db_passage_id") != row.get("passage_id")
        ):
            raise RuntimeError(f"Exhortatio passage metadata mismatch: {wanted_node}")
        if nfc(str(node.get("description") or "")) != nfc(
            str(row.get("text_content") or "")
        ):
            raise RuntimeError(f"Exhortatio snapshot text mismatch: {wanted_node}")
        parity = row.get("parity_propagation_2026_08_17")
        if not isinstance(parity, dict) or parity.get("kg_node_id") != wanted_node:
            raise RuntimeError(f"Exhortatio corpus parity pointer mismatch: {section}")
        if mode == "repaired":
            if data.get("legacy_node_ids") != [expected_old_node(section)]:
                raise RuntimeError(f"missing legacy alias on {wanted_node}")
            if "id_debt" in data:
                raise RuntimeError(f"stale id debt on {wanted_node}")

    target_edges = [
        edge
        for edge in edges
        if str(edge.get("source") or edge.get("source_id") or "") in active_ids
        or str(edge.get("target") or edge.get("target_id") or "") in active_ids
    ]
    if len(target_edges) != 102:
        raise RuntimeError(f"expected 102 Exhortatio edges, found {len(target_edges)}")
    edge_ids = [str(edge.get("edge_id") or "") for edge in edges]
    if len(edge_ids) != len(set(edge_ids)):
        raise RuntimeError("duplicate KG edge ids")
    expected_pairs = set()
    for section in range(1, 52):
        source = (
            expected_old_node(section)
            if mode == "legacy"
            else expected_new_node(section)
        )
        expected_pairs.add((source, "authored_by", ORIGEN_PERSON_NODE))
        expected_pairs.add((source, "part_of", ORIGEN_WORK_NODE))
    actual_pairs = set()
    for edge in target_edges:
        source = str(edge.get("source") or "")
        target = str(edge.get("target") or "")
        if source != str(edge.get("source_id") or ""):
            raise RuntimeError(f"source/source_id mismatch: {edge.get('edge_id')}")
        if target != str(edge.get("target_id") or ""):
            raise RuntimeError(f"target/target_id mismatch: {edge.get('edge_id')}")
        actual_pairs.add((source, str(edge.get("relation") or ""), target))
    if actual_pairs != expected_pairs:
        raise RuntimeError("Exhortatio authored_by/part_of cohort mismatch")

    target_citations = [
        row for row in citations if str(row.get("kg_node_id") or "") in active_ids
    ]
    if len(target_citations) != 51 or any(
        row.get("citation_type") != "snapshot_passage_node"
        for row in target_citations
    ):
        raise RuntimeError("Exhortatio snapshot citation cohort mismatch")
    expected_snapshots = {
        (
            expected_old_node(section)
            if mode == "legacy"
            else expected_new_node(section),
            str(rows[section - 1].get("passage_id") or ""),
        )
        for section in range(1, 52)
    }
    actual_snapshots = {
        (str(row.get("kg_node_id") or ""), str(row.get("passage_id") or ""))
        for row in target_citations
    }
    if actual_snapshots != expected_snapshots:
        raise RuntimeError("Exhortatio snapshot mapping is not bijective")

    children_of_clement = {
        str(edge.get("source") or "")
        for edge in edges
        if edge.get("relation") == "part_of"
        and str(edge.get("target") or "") == CLEMENT_WORK_NODE
    }
    if children_of_clement:
        raise RuntimeError(f"Clement Protrepticus is not empty: {children_of_clement}")

    target_manifest = target_manifest_rows(manifest)
    if len(target_manifest) != 1:
        raise RuntimeError("Exhortatio corpus manifest row is not unique")
    return {
        "work_nodes": 2,
        "passage_nodes": 51,
        "corpus_passages": 51,
        "snapshot_citations": 51,
        "authored_by_edges": 51,
        "part_of_edges": 51,
        "manifest_rows": 1,
        "clement_corpus_children": 0,
    }


def validate_repaired(
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    passages: list[dict[str, Any]],
    citations: list[dict[str, Any]],
    manifest: list[dict[str, Any]],
) -> dict[str, int]:
    validate_immutable_passages(passages)
    counts = validate_topology(
        nodes, edges, passages, citations, manifest, mode="repaired"
    )
    by_node = {node_id(node): node for node in nodes}
    origen = metadata(by_node[ORIGEN_WORK_NODE])
    if (
        origen.get("canonical_id") != ORIGEN_WORK_URN
        or origen.get("work_canonical_id") != ORIGEN_WORK_URN
        or origen.get("cts_urn") != ORIGEN_EDITION_URN
        or origen.get("needs_text_ingestion") is not False
        or origen.get("passage_count") != 51
    ):
        raise RuntimeError("Origen Exhortatio work identity/coverage is incomplete")
    clement = metadata(by_node[CLEMENT_WORK_NODE])
    if (
        clement.get("canonical_id") != CLEMENT_WORK_URN
        or clement.get("work_canonical_id") != CLEMENT_WORK_URN
        or clement.get("cts_urn") != CLEMENT_EDITION_URN
        or clement.get("needs_text_ingestion") is not True
        or clement.get("passage_count") != 0
    ):
        raise RuntimeError("Clement Protrepticus work is not empty/correctly identified")

    row = target_manifest_rows(manifest)[0]
    if (
        row.get("author") != "Origen"
        or row.get("title") != "Exhortatio ad martyrium"
        or row.get("work_urn") != ORIGEN_WORK_URN
        or row.get("cts_urn") != ORIGEN_EDITION_URN
        or row.get("source") != f"scaife:{ORIGEN_EDITION_URN}"
        or row.get("language") != "grc"
        or row.get("passages") != 51
    ):
        raise RuntimeError("Exhortatio manifest repair contract is incomplete")
    if any(
        row.get("canonical_id") == CORPUS_CANONICAL_ID
        and row.get("author") == "Clement of Alexandria"
        for row in manifest
    ):
        raise RuntimeError("stale Clement attribution remains in target manifest")

    node_ids = {node_id(node) for node in nodes}
    for edge in edges:
        if str(edge.get("source") or "") not in node_ids:
            raise RuntimeError(f"dangling KG edge source: {edge.get('edge_id')}")
        if str(edge.get("target") or "") not in node_ids:
            raise RuntimeError(f"dangling KG edge target: {edge.get('edge_id')}")
    passage_ids = {str(row.get("passage_id") or "") for row in passages}
    for row in citations:
        if str(row.get("kg_node_id") or "") not in node_ids:
            raise RuntimeError(f"dangling citation KG node: {row}")
        if str(row.get("passage_id") or "") not in passage_ids:
            raise RuntimeError(f"dangling citation passage: {row}")
    return counts


def _remap_exact_alias_values(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _remap_exact_alias_values(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_remap_exact_alias_values(item) for item in value]
    if isinstance(value, str):
        return NODE_ALIASES.get(value, value)
    return value


def _repair_work_nodes(nodes: list[dict[str, Any]]) -> None:
    by_node = {node_id(node): node for node in nodes}
    origen = by_node[ORIGEN_WORK_NODE]
    origen_meta = metadata(origen)
    origen_meta.update(
        {
            "author": "Origen of Alexandria",
            "author_id": ORIGEN_PERSON_NODE,
            "canonical_id": ORIGEN_WORK_URN,
            "work_canonical_id": ORIGEN_WORK_URN,
            "cts_urn": ORIGEN_EDITION_URN,
            "corpus_canonical_id": CORPUS_CANONICAL_ID,
            "language": "grc",
            "needs_text_ingestion": False,
            "passage_count": 51,
            "corpus_coverage": {
                "status": "complete_chapters_1_51",
                "passages": 51,
                "text_identity": "NFC-exact to pinned OGL edition",
            },
            "citation_verdict": "corrected",
            "citation_verified": True,
            "verified_reference": (
                "Origen, Exhortatio ad martyrium 1-51; Paul Koetschau (ed.), "
                "Origenes Werke I (GCS 2), Leipzig 1899; OGL edition "
                f"{ORIGEN_EDITION_URN}, commit {OGL_COMMIT}."
            ),
            STAMP: {
                "decision": "51 exact corpus children restored to this work",
                "previous_false_state": (
                    "work metadata said the children were Clement Protrepticus and "
                    "that no Exhortatio text was ingested"
                ),
                "decided_at": DECIDED_AT,
            },
        }
    )
    origen_meta["factual_corrections_2026_08_17_note"] = (
        "Corrected by Wave 0.2: the 51 existing children are Origen, Exhortatio "
        "ad martyrium 1-51 and are NFC-exact to the pinned OGL Greek edition."
    )
    set_metadata(origen, origen_meta)
    origen["updated_at"] = UPDATED_AT

    clement = by_node[CLEMENT_WORK_NODE]
    clement_meta = metadata(clement)
    clement_meta.pop("ingestion_debt_2026_08_17_canonical_derived", None)
    clement_meta.update(
        {
            "canonical_id": CLEMENT_WORK_URN,
            "work_canonical_id": CLEMENT_WORK_URN,
            "cts_urn": CLEMENT_EDITION_URN,
            "language": "grc",
            "needs_text_ingestion": True,
            "passage_count": 0,
            "corpus_coverage": {
                "status": "absent",
                "passages": 0,
                "note": "No Clement Protrepticus text belongs to this work yet.",
            },
            "citation_verdict": "corrected",
            "citation_verified": True,
            "verified_reference": (
                "Clement of Alexandria, Protrepticus; OGL work "
                f"{CLEMENT_WORK_URN}, Stählin 1905 edition "
                f"{CLEMENT_EDITION_URN}, commit {OGL_COMMIT}."
            ),
            STAMP: {
                "decision": "empty Clement work corrected to tlg0555.tlg001",
                "excluded_corpus_identity": CORPUS_CANONICAL_ID,
                "decided_at": DECIDED_AT,
            },
        }
    )
    set_metadata(clement, clement_meta)
    clement["updated_at"] = UPDATED_AT


def _repair_passage_alias_metadata(nodes: list[dict[str, Any]]) -> None:
    by_node = {node_id(node): node for node in nodes}
    for section in range(1, 52):
        new_id = expected_new_node(section)
        old_id = expected_old_node(section)
        node = by_node[new_id]
        data = metadata(node)
        data.pop("id_debt", None)
        data.update(
            {
                "legacy_node_ids": [old_id],
                "source_edition_urn": ORIGEN_EDITION_URN,
                "citation_verdict": "corrected",
                "citation_verified": True,
                STAMP: {
                    "alias_from": old_id,
                    "alias_to": new_id,
                    "atomic_surfaces": [
                        "kg_node",
                        "kg_edges",
                        "corpus_citations",
                        "corpus_parity_pointer",
                    ],
                    "decided_at": DECIDED_AT,
                },
            }
        )
        set_metadata(node, data)
        node["label"] = f"Origen, Exhortation to Martyrdom {section}"
        node["updated_at"] = UPDATED_AT


def _repair_manifest(manifest: list[dict[str, Any]]) -> None:
    row = target_manifest_rows(manifest)[0]
    row.update(
        {
            "author": "Origen",
            "title": "Exhortatio ad martyrium",
            "work_urn": ORIGEN_WORK_URN,
            "cts_urn": ORIGEN_EDITION_URN,
            "source": f"scaife:{ORIGEN_EDITION_URN}",
            "language": "grc",
            "edition": (
                "Paul Koetschau (ed.), Origenes Werke I, GCS 2 "
                "(Leipzig: Hinrichs, 1899)"
            ),
            "license": "CC BY-SA 4.0",
            "source_commit": OGL_COMMIT,
            "passages": 51,
            "identity_repair_2026_08_24": {
                "authority": "OpenGreekAndLatin First1KGreek",
                "catalog_url": OGL_URLS["origen_cts"],
                "previous_author": "Clement of Alexandria",
                "previous_title": "Protrepticus",
                "distinguished_from": CLEMENT_WORK_URN,
            },
        }
    )


def _quarantine_records(
    original: tuple[list[dict[str, Any]], ...],
    repaired: tuple[list[dict[str, Any]], ...],
) -> list[dict[str, Any]]:
    names = ("nodes", "edges", "passages", "citations", "manifest")
    records: list[dict[str, Any]] = []
    for name, before_rows, after_rows in zip(names, original, repaired, strict=True):
        if len(before_rows) != len(after_rows):
            raise RuntimeError(f"{name} row count changed during identity repair")
        for before, after in zip(before_rows, after_rows, strict=True):
            if before == after:
                continue
            if name == "nodes":
                wanted = node_id(before)
                if wanted in OLD_NODE_IDS:
                    reason = "legacy Clement-prefixed passage node id remapped"
                    alias_to = NODE_ALIASES[wanted]
                    record_type = "kg_passage_node_before"
                elif wanted in {ORIGEN_WORK_NODE, CLEMENT_WORK_NODE}:
                    reason = "work identity/coverage corrected"
                    alias_to = None
                    record_type = "kg_work_node_before"
                else:
                    raise RuntimeError(f"unexpected changed KG node: {wanted}")
            elif name == "edges":
                reason = "endpoint remapped through the 51-id alias cohort"
                alias_to = None
                record_type = "kg_edge_before"
            elif name == "passages":
                reason = "corpus parity pointer remapped; UUID/text/ref/CTS preserved"
                alias_to = None
                record_type = "corpus_passage_before"
            elif name == "citations":
                reason = "snapshot kg_node_id remapped through alias cohort"
                alias_to = None
                record_type = "corpus_citation_before"
            else:
                reason = "stale Clement/Protrepticus manifest identity corrected"
                alias_to = None
                record_type = "corpus_manifest_before"
            item: dict[str, Any] = {
                "record_type": record_type,
                "reason": reason,
                "record": before,
            }
            if alias_to:
                item["alias_to"] = alias_to
            records.append(item)
    return records


def transform(
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
    list[dict[str, Any]],
    Counter[str],
    str,
]:
    mode = target_node_mode(nodes)
    validate_immutable_passages(passages)
    validate_topology(
        nodes, edges, passages, citations, manifest, mode=mode
    )
    if mode == "repaired":
        validate_repaired(nodes, edges, passages, citations, manifest)
        return (
            copy.deepcopy(nodes),
            copy.deepcopy(edges),
            copy.deepcopy(passages),
            copy.deepcopy(citations),
            copy.deepcopy(manifest),
            [],
            Counter(),
            mode,
        )
    validate_legacy_preimage(nodes, edges, passages, citations, manifest)

    original = (
        copy.deepcopy(nodes),
        copy.deepcopy(edges),
        copy.deepcopy(passages),
        copy.deepcopy(citations),
        copy.deepcopy(manifest),
    )
    nodes = _remap_exact_alias_values(copy.deepcopy(nodes))
    edges = _remap_exact_alias_values(copy.deepcopy(edges))
    passages = _remap_exact_alias_values(copy.deepcopy(passages))
    citations = _remap_exact_alias_values(copy.deepcopy(citations))
    manifest = copy.deepcopy(manifest)

    _repair_work_nodes(nodes)
    _repair_passage_alias_metadata(nodes)
    _repair_manifest(manifest)
    validate_repaired(nodes, edges, passages, citations, manifest)

    repaired = (nodes, edges, passages, citations, manifest)
    quarantine = _quarantine_records(original, repaired)
    changed = Counter(row["record_type"] for row in quarantine)
    return (*repaired, quarantine, changed, mode)


def fetch_url(url: str) -> bytes:
    request = urllib.request.Request(
        url, headers={"User-Agent": "EleutherIA-Origen-Wave-0.2/1.0"}
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read()


def _cts_facts(raw: bytes) -> tuple[str, str, str]:
    root = ET.fromstring(raw)
    ns = {"ti": "http://chs.harvard.edu/xmlns/cts"}
    title = str(root.findtext("ti:title", namespaces=ns) or "")
    edition = root.find("ti:edition", ns)
    if edition is None:
        raise RuntimeError("OGL CTS catalog lacks an edition")
    return (
        str(root.get("urn") or ""),
        title,
        str(edition.get("urn") or ""),
    )


def _origen_tei_chapters(raw: bytes) -> tuple[str, str, str, dict[int, str]]:
    root = ET.fromstring(raw)
    ns = {"tei": "http://www.tei-c.org/ns/1.0"}
    title = str(root.findtext(".//tei:titleStmt/tei:title", namespaces=ns) or "")
    author = str(root.findtext(".//tei:titleStmt/tei:author", namespaces=ns) or "")
    edition = root.find(".//tei:div[@type='edition']", ns)
    licence = root.find(".//tei:availability/tei:licence", ns)
    if edition is None or licence is None:
        raise RuntimeError("OGL Exhortatio TEI lacks edition/licence")
    chapters: dict[int, str] = {}
    for chapter in edition.findall("./tei:div[@subtype='chapter']", ns):
        section = int(str(chapter.get("n") or "0"))
        chapters[section] = " ".join("".join(chapter.itertext()).split())
    return (
        title,
        author,
        str(edition.get("n") or ""),
        chapters,
    )


def verify_authority_snapshot(passages: list[dict[str, Any]]) -> dict[str, Any]:
    """Verify pinned work identities and all 51 local Greek texts."""

    fetched = {label: fetch_url(url) for label, url in OGL_URLS.items()}
    for label, raw in fetched.items():
        actual = sha256_bytes(raw)
        if actual != OGL_SHA256[label]:
            raise RuntimeError(
                f"pinned OGL {label} SHA-256 drift: {actual} != {OGL_SHA256[label]}"
            )
    origen_cts = _cts_facts(fetched["origen_cts"])
    clement_cts = _cts_facts(fetched["clement_cts"])
    if origen_cts != (
        ORIGEN_WORK_URN,
        "Exhortatio ad martyrium",
        ORIGEN_EDITION_URN,
    ):
        raise RuntimeError(f"unexpected OGL Origen catalog: {origen_cts}")
    if clement_cts != (
        CLEMENT_WORK_URN,
        "Protrepticus",
        CLEMENT_EDITION_URN,
    ):
        raise RuntimeError(f"unexpected OGL Clement catalog: {clement_cts}")

    title, author, edition, chapters = _origen_tei_chapters(fetched["origen_tei"])
    if (
        title != "Exhortatio ad martyrium"
        or author != "Origenes"
        or edition != ORIGEN_EDITION_URN
        or sorted(chapters) != list(range(1, 52))
    ):
        raise RuntimeError("unexpected OGL Exhortatio TEI identity/coverage")
    rows = passage_rows(passages)
    proofs: list[dict[str, Any]] = []
    for section, row in enumerate(rows, 1):
        local_text = " ".join(str(row.get("text_content") or "").split())
        if nfc(local_text) != nfc(chapters[section]):
            raise RuntimeError(f"local Exhortatio differs from OGL at section {section}")
        proofs.append(
            {
                "section": section,
                "passage_id": row.get("passage_id"),
                "text_sha256_nfc": sha256_text(nfc(local_text)),
            }
        )
    return {
        "authority": "OpenGreekAndLatin First1KGreek",
        "authority_commit": OGL_COMMIT,
        "catalog_facts": {
            ORIGEN_WORK_URN: "Exhortatio ad martyrium",
            CLEMENT_WORK_URN: "Protrepticus",
            "selected_edition": ORIGEN_EDITION_URN,
        },
        "files": [
            {"label": label, "sha256": OGL_SHA256[label], "url": OGL_URLS[label]}
            for label in sorted(OGL_URLS)
        ],
        "selected_passages": 51,
        "selected_passage_proofs_sha256": canonical_digest(proofs),
        "text_verdict": "51/51 NFC-exact",
        "license": "CC BY-SA 4.0 (OGL TEI availability declaration)",
        "verified_at": DECIDED_AT,
        "verdict": "pass",
    }


def render_jsonl_preserving_unchanged(
    path: Path,
    before: list[dict[str, Any]],
    after: list[dict[str, Any]],
) -> bytes:
    original_lines = [
        line
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if len(original_lines) != len(before) or len(before) != len(after):
        raise RuntimeError(f"row-count drift while staging {path}")
    output = [
        original_line
        if old == new
        else json.dumps(new, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        for original_line, old, new in zip(
            original_lines, before, after, strict=True
        )
    ]
    return ("\n".join(output) + "\n").encode("utf-8")


def file_sha256(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def core_file_hashes(paths: dict[str, Path]) -> dict[str, str]:
    return {name: file_sha256(path) for name, path in paths.items()}


def _assert_core_hashes(
    paths: dict[str, Path], expected: dict[str, str], *, phase: str
) -> None:
    actual = core_file_hashes(paths)
    if actual != expected:
        drift = {
            name: {"expected": expected.get(name), "actual": actual.get(name)}
            for name in sorted(set(expected) | set(actual))
            if expected.get(name) != actual.get(name)
        }
        raise RuntimeError(f"concurrent core-file drift at {phase}: {drift}")


def _assert_artifacts_absent(artifact_paths: list[Path], *, phase: str) -> None:
    existing = [str(path) for path in artifact_paths if path.exists()]
    if existing:
        raise RuntimeError(
            f"refusing to overwrite Wave 0.2 audit artifacts at {phase}: {existing}"
        )


def _write_fsync(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as handle:
        handle.write(content)
        handle.flush()
        os.fsync(handle.fileno())


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _replace_file(source: Path, target: Path) -> None:
    """Injection seam used by rollback tests; production delegates to os.replace."""

    os.replace(source, target)


def _write_transaction_journal(path: Path, journal: dict[str, Any]) -> None:
    _write_fsync(
        path,
        (
            json.dumps(journal, ensure_ascii=False, indent=2, sort_keys=True)
            + "\n"
        ).encode("utf-8"),
    )
    _fsync_directory(path.parent)


def _expected_artifact_paths(data_root: Path) -> set[Path]:
    return {
        (data_root / REPORT_RELATIVE).resolve(),
        (data_root / QUARANTINE_RELATIVE).resolve(),
        (data_root / ALIASES_RELATIVE).resolve(),
    }


def recover_interrupted_transactions(
    *, data_root: Path, core_paths: dict[str, Path]
) -> list[dict[str, Any]]:
    """Recover a journaled hard interruption before starting a new write.

    Dry-run never calls this function.  A committed transaction whose process
    died only during cleanup is verified and its staging directory is removed.
    Any prepared/committing transaction is rolled back from fsynced backups.
    Unknown or malformed staging directories are refused, never guessed at.
    """

    recovered: list[dict[str, Any]] = []
    allowed_core = {path.resolve() for path in core_paths.values()}
    allowed_artifacts = _expected_artifact_paths(data_root)
    for stage_root in sorted(data_root.glob(f"{TRANSACTION_PREFIX}*")):
        if not stage_root.is_dir():
            raise RuntimeError(f"unexpected transaction path: {stage_root}")
        journal_path = stage_root / TRANSACTION_JOURNAL
        if not journal_path.exists():
            raise RuntimeError(
                f"orphan Wave 0.2 stage has no recovery journal: {stage_root}"
            )
        journal = json.loads(journal_path.read_text(encoding="utf-8"))
        if journal.get("wave") != STAMP:
            raise RuntimeError(f"foreign transaction journal: {journal_path}")
        entries = journal.get("entries")
        if not isinstance(entries, list) or len(entries) != 8:
            raise RuntimeError(f"invalid transaction journal entries: {journal_path}")
        targets = {Path(str(entry.get("target") or "")).resolve() for entry in entries}
        if targets != allowed_core | allowed_artifacts:
            raise RuntimeError(f"transaction journal target scope mismatch: {journal_path}")

        state = str(journal.get("state") or "")
        all_new = all(
            target.exists()
            and file_sha256(target) == str(entry.get("new_sha256") or "")
            for entry in entries
            for target in [Path(str(entry["target"])).resolve()]
        )
        if state == "committed" and all_new:
            shutil.rmtree(stage_root)
            _fsync_directory(data_root)
            recovered.append(
                {"stage": str(stage_root), "action": "completed_cleanup"}
            )
            continue
        if state not in {"prepared", "committing", "committed"}:
            raise RuntimeError(
                f"transaction journal has non-recoverable state {state!r}: {journal_path}"
            )

        rollback_errors: list[str] = []
        for entry in reversed(entries):
            target = Path(str(entry["target"])).resolve()
            existed = bool(entry.get("existed"))
            try:
                if existed:
                    pre_sha = str(entry.get("pre_sha256") or "")
                    if target.exists() and file_sha256(target) == pre_sha:
                        continue
                    backup_name = str(entry.get("backup") or "")
                    backup = stage_root / backup_name
                    if not backup.exists():
                        raise RuntimeError(f"recovery backup missing: {backup}")
                    if file_sha256(backup) != pre_sha:
                        raise RuntimeError(f"recovery backup hash mismatch: {backup}")
                    _replace_file(backup, target)
                else:
                    # An originally absent artifact may never have reached its
                    # commit turn, in which case even data/audit need not exist.
                    # There is nothing to restore or fsync in that branch.
                    if not target.exists():
                        continue
                    target.unlink()
                _fsync_directory(target.parent)
            except Exception as error:  # pragma: no cover - catastrophic path
                rollback_errors.append(f"{target}: {error}")
        expected = {
            label.removeprefix("core-"): str(entry.get("pre_sha256") or "")
            for entry in entries
            for label in [str(entry.get("label") or "")]
            if label.startswith("core-")
        }
        try:
            _assert_core_hashes(core_paths, expected, phase="journal recovery")
            remaining_artifacts = [
                str(path) for path in allowed_artifacts if path.exists()
            ]
            if remaining_artifacts:
                raise RuntimeError(
                    f"journal recovery left audit artifacts: {remaining_artifacts}"
                )
        except Exception as error:  # pragma: no cover - catastrophic path
            rollback_errors.append(str(error))
        if rollback_errors:
            raise RuntimeError(
                f"interrupted transaction recovery incomplete at {stage_root}: "
                f"{rollback_errors}"
            )
        shutil.rmtree(stage_root)
        _fsync_directory(data_root)
        recovered.append({"stage": str(stage_root), "action": "rolled_back"})
    return recovered


def commit_transaction(
    *,
    data_root: Path,
    core_paths: dict[str, Path],
    expected_core_hashes: dict[str, str],
    core_contents: dict[str, bytes],
    artifact_contents: dict[Path, bytes],
    before_commit: Callable[[], None] | None = None,
) -> None:
    """Stage, fsync and commit the core+audit cohort with best-effort rollback.

    A POSIX filesystem cannot atomically rename eight independent files in one
    syscall.  This function supplies the strongest local equivalent available:
    optimistic concurrency hashes, fully fsynced staged payloads and backups,
    a second hash/artifact gate immediately before the first replace, and
    reverse-order rollback plus hash verification if any replace fails.
    """

    if set(core_contents) != set(core_paths):
        raise RuntimeError("transaction core content/path keys differ")
    artifact_paths = sorted(artifact_contents, key=str)
    _assert_artifacts_absent(artifact_paths, phase="pre-stage")
    _assert_core_hashes(
        core_paths, expected_core_hashes, phase="pre-stage"
    )

    stage_root = Path(tempfile.mkdtemp(prefix=TRANSACTION_PREFIX, dir=data_root))
    entries: list[dict[str, Any]] = []
    cleanup_stage = True
    committed: list[dict[str, Any]] = []
    try:
        ordered_targets: list[tuple[str, Path, bytes, bool]] = [
            (f"core-{name}", core_paths[name], core_contents[name], True)
            for name in ("nodes", "edges", "passages", "citations", "manifest")
        ] + [
            (f"artifact-{index}", path, artifact_contents[path], False)
            for index, path in enumerate(artifact_paths)
        ]
        for index, (label, target, new_content, must_exist) in enumerate(
            ordered_targets
        ):
            existed = target.exists()
            if must_exist and not existed:
                raise RuntimeError(f"required transaction target missing: {target}")
            staged_path = stage_root / f"new-{index:02d}-{label}"
            _write_fsync(staged_path, new_content)
            backup_path: Path | None = None
            if existed:
                original = target.read_bytes()
                if must_exist:
                    name = label.removeprefix("core-")
                    actual = sha256_bytes(original)
                    if actual != expected_core_hashes[name]:
                        raise RuntimeError(
                            f"concurrent core-file drift while backing up {name}"
                        )
                backup_path = stage_root / f"backup-{index:02d}-{label}"
                _write_fsync(backup_path, original)
            entries.append(
                {
                    "label": label,
                    "target": target,
                    "staged": staged_path,
                    "backup": backup_path,
                    "existed": existed,
                    "pre_sha256": file_sha256(target) if existed else None,
                    "new_sha256": sha256_bytes(new_content),
                }
            )
        _fsync_directory(stage_root)

        journal = {
            "wave": STAMP,
            "state": "prepared",
            "created_at": DECIDED_AT,
            "committed_labels": [],
            "entries": [
                {
                    "label": str(entry["label"]),
                    "target": str(Path(entry["target"]).resolve()),
                    "backup": (
                        Path(entry["backup"]).name
                        if isinstance(entry["backup"], Path)
                        else None
                    ),
                    "existed": bool(entry["existed"]),
                    "pre_sha256": entry["pre_sha256"],
                    "new_sha256": entry["new_sha256"],
                }
                for entry in entries
            ],
        }
        journal_path = stage_root / TRANSACTION_JOURNAL
        _write_transaction_journal(journal_path, journal)

        if before_commit is not None:
            before_commit()
        _assert_artifacts_absent(artifact_paths, phase="pre-commit")
        _assert_core_hashes(
            core_paths, expected_core_hashes, phase="pre-commit"
        )

        journal["state"] = "committing"
        _write_transaction_journal(journal_path, journal)
        # From this point a BaseException/hard process interruption must retain
        # the fsynced journal+backups for the next authorized --write recovery.
        cleanup_stage = False
        try:
            for entry in entries:
                target = entry["target"]
                target.parent.mkdir(parents=True, exist_ok=True)
                _replace_file(entry["staged"], target)
                committed.append(entry)
                _fsync_directory(target.parent)
                journal["committed_labels"].append(str(entry["label"]))
                _write_transaction_journal(journal_path, journal)
        except Exception as commit_error:
            rollback_errors: list[str] = []
            for entry in reversed(committed):
                target = entry["target"]
                try:
                    if entry["existed"]:
                        backup = entry["backup"]
                        if not isinstance(backup, Path) or not backup.exists():
                            raise RuntimeError("rollback backup missing")
                        _replace_file(backup, target)
                    else:
                        target.unlink(missing_ok=True)
                    _fsync_directory(target.parent)
                except Exception as rollback_error:  # pragma: no cover - catastrophic path
                    rollback_errors.append(f"{target}: {rollback_error}")

            try:
                _assert_core_hashes(
                    core_paths, expected_core_hashes, phase="post-rollback"
                )
                unexpected_artifacts = [
                    str(path) for path in artifact_paths if path.exists()
                ]
                if unexpected_artifacts:
                    raise RuntimeError(
                        f"rollback left audit artifacts: {unexpected_artifacts}"
                    )
            except Exception as verification_error:  # pragma: no cover - catastrophic path
                rollback_errors.append(str(verification_error))
            if rollback_errors:
                cleanup_stage = False
                raise RuntimeError(
                    "transaction commit failed and rollback is incomplete; "
                    f"stage retained at {stage_root}; commit={commit_error}; "
                    f"rollback={rollback_errors}"
                ) from commit_error
            cleanup_stage = True
            raise RuntimeError(
                f"transaction commit failed; rollback succeeded: {commit_error}"
            ) from commit_error

        journal["state"] = "committed"
        _write_transaction_journal(journal_path, journal)
        cleanup_stage = True
    finally:
        if cleanup_stage:
            shutil.rmtree(stage_root, ignore_errors=True)
            _fsync_directory(data_root)


def alias_artifact() -> dict[str, Any]:
    return {
        "artifact_type": "kg_node_alias_map",
        "wave": STAMP,
        "decision": "rename misleading Clement-prefixed ids without changing evidence",
        "aliases": [
            {"legacy_node_id": old, "canonical_node_id": NODE_ALIASES[old]}
            for old in sorted(OLD_NODE_IDS, key=lambda value: int(value.rsplit("_", 1)[1]))
        ],
        "alias_count": 51,
        "atomic_surfaces": [
            "data/kg/nodes.jsonl",
            "data/kg/edges.jsonl",
            "data/corpus/citations.jsonl",
            "data/corpus/passages.jsonl#parity_propagation_2026_08_17.kg_node_id",
        ],
        "external_resolution_policy": (
            "Each canonical node retains metadata.legacy_node_ids; deployment must "
            "load this alias map before changing public deep-link resolution."
        ),
    }


def _paths(data_root: Path) -> dict[str, Path]:
    return {
        "nodes": data_root / "kg/nodes.jsonl",
        "edges": data_root / "kg/edges.jsonl",
        "passages": data_root / "corpus/passages.jsonl",
        "citations": data_root / "corpus/citations.jsonl",
        "manifest": data_root / "corpus/manifest.jsonl",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--write",
        action="store_true",
        help="apply after explicit Wave 0.2 authorization; dry-run is default",
    )
    parser.add_argument("--data-root", type=Path, default=DEFAULT_DATA_ROOT)
    args = parser.parse_args(argv)
    data_root = args.data_root.expanduser().resolve()
    paths = _paths(data_root)
    recovered_transactions = (
        recover_interrupted_transactions(data_root=data_root, core_paths=paths)
        if args.write
        else []
    )
    pre_read_hashes = core_file_hashes(paths)
    original = (
        read_jsonl(paths["nodes"]),
        read_jsonl(paths["edges"]),
        read_jsonl(paths["passages"]),
        read_jsonl(paths["citations"]),
        read_jsonl(paths["manifest"]),
    )
    result = transform(*original)
    nodes, edges, passages, citations, manifest, quarantine, changed, source_mode = (
        result
    )
    authority = verify_authority_snapshot(passages)
    validation = validate_repaired(nodes, edges, passages, citations, manifest)
    summary = {
        "wave": STAMP,
        "mode": "write" if args.write else "dry-run",
        "source_state": source_mode,
        "write_performed": False,
        "aliases": 51,
        "changed_records": dict(sorted(changed.items())),
        "changed_records_total": sum(changed.values()),
        "quarantine_records": len(quarantine),
        "recovered_transactions": recovered_transactions,
        "authority_verification": authority,
        "validation": validation,
        "preserved": {
            "passage_uuids": 51,
            "passage_texts": 51,
            "canonical_refs": 51,
            "cts_loci": 51,
        },
    }
    if not args.write:
        print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    if not changed:
        summary["already_applied"] = True
        print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
        return 0

    repaired = (nodes, edges, passages, citations, manifest)
    quarantine_text = "\n".join(
        json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        for row in quarantine
    ) + "\n"
    committed_summary = copy.deepcopy(summary)
    committed_summary["write_performed"] = True
    committed_summary["pre_write_core_sha256"] = pre_read_hashes
    committed_summary["non_target_policy"] = (
        "No registry, bibliography, frontend, backend, GraphRAG, or non-target work "
        "record is changed."
    )
    core_contents = {
        name: render_jsonl_preserving_unchanged(paths[name], before_rows, after_rows)
        for name, before_rows, after_rows in zip(
            ("nodes", "edges", "passages", "citations", "manifest"),
            original,
            repaired,
            strict=True,
        )
    }
    artifact_contents = {
        data_root / QUARANTINE_RELATIVE: quarantine_text.encode("utf-8"),
        data_root / ALIASES_RELATIVE: (
            json.dumps(alias_artifact(), ensure_ascii=False, indent=2, sort_keys=True)
            + "\n"
        ).encode("utf-8"),
        data_root / REPORT_RELATIVE: (
            json.dumps(
                committed_summary, ensure_ascii=False, indent=2, sort_keys=True
            )
            + "\n"
        ).encode("utf-8"),
    }
    # The artifact gate is intentionally before the transaction as an early,
    # readable failure. commit_transaction repeats it immediately pre-commit.
    _assert_artifacts_absent(list(artifact_contents), phase="main pre-commit")
    commit_transaction(
        data_root=data_root,
        core_paths=paths,
        expected_core_hashes=pre_read_hashes,
        core_contents=core_contents,
        artifact_contents=artifact_contents,
    )
    print(
        json.dumps(
            committed_summary, ensure_ascii=False, indent=2, sort_keys=True
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
