#!/usr/bin/env python3
"""Prepare the fail-closed Tatian Oratio ad Graecos P0 repair.

The checked-out corpus has three editorial/machine composites masquerading as
Greek chapters 7, 8, and 11. This dry-run-first migration replaces only those
three texts with complete chapters from the pinned Otto 1851 Perseus/Scaife
manifestation, while preserving the other thirty-nine corpus texts exactly.

The untouched rows are honestly described as exact *first TEI segments*, not
as complete chapters. SAPERE 28 (Nesselrath 2016) is used only for copyright-
bounded collation, page mapping, and attributed modern interpretation. Its
variant readings never overwrite the Otto manifestation.

Writes are disabled against the repository data root unless both ``--write``
and ``--production-write-approved`` are provided. Multi-file writes use a
stable snapshot A, fsynced stages/backups, a durable journal, rollback, and
hard-crash recovery. No deployment is performed.
"""

from __future__ import annotations

import argparse
import copy
import fcntl
import hashlib
import importlib.util
import json
import os
import re
import shutil
import sys
import tempfile
import unicodedata
import urllib.request
import uuid
import xml.etree.ElementTree as ET
from collections import Counter
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_ROOT = ROOT / "data"
DEFAULT_AUTHORITY = (
    ROOT / "tests/fixtures/tatian_otto1851_release_1.1.32401591783.json"
)
AUTHORITY_FIXTURE_SHA256 = (
    "3c3234a87671514c2a6a70c6908df07a82c361f9305a0e17a2a37a4b12d0f1b6"
)
AUDIT_DOC = ROOT / "docs/academic/2026-08-24-tatian-sapere28-pdf-audit.md"
AUDIT_DOC_SHA256 = "8952855ac632d2b6ad935293e71fe5f9d5a59e3ed017ea1652097844eb018024"
INDEPENDENT_REVIEW_V2 = (
    ROOT / "docs/academic/2026-08-24-tatian-p0-independent-review-v2.md"
)
INDEPENDENT_REVIEW_V2_SHA256 = (
    "303f9bd876c6645625071d0eb06a664106d3c0d46e80ed28cb4900eb7f7ce731"
)
HILDEBRANDT_REPORT = (
    ROOT / "data/audit/2026-08-24_hildebrandt_p0_repair.json"
)
HILDEBRANDT_REPORT_SHA256 = (
    "cb30674aff6f4a6012cbb4a6266b9d1b49138da615c14147837f29820dfec59c"
)
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

STAMP = "tatian_p0_repair_2026_08_24"
UPDATED_AT = "2026-08-24 09:00:00+00:00"

MANIFEST_ID = "urn_cts_greeklit_tlg1766_tlg001_grc"
WORK_URN = "urn:cts:greekLit:tlg1766.tlg001"
VERSION_URN = f"{WORK_URN}.perseus-grc1"
WORK_NODE = "work_tatian_oratio"
PERSON_NODE = "person_tatian"
ARGUMENT_ABOVE = "argument_tatian_above_fate"
ARGUMENT_FREEWILL = "argument_tatian_freewill_paradox"

TARGET_PASSAGES = {
    7: "a36c2d9d-9306-4b6f-979a-b8922f7e5d04",
    8: "8ac4c3f3-aab5-4680-80fc-5bc76ee466b0",
    11: "f8ceab87-f393-4ca6-aceb-e28dd1346abe",
}
OTHER_EVIDENCE_PASSAGES = {
    9: "e06ffb4e-a568-4982-94d2-506db13f472a",
    15: "fdefee1b-2430-4ed0-acc2-88f48f2fc875",
}
EXACT_NODES = {
    7: "passage_tatian_orat_7",
    8: "passage_tatian_orat_8_otto1851_exact",
    11: "passage_tatian_orat_11",
}
SYNTHESIS_NODE = "passage_tatian_orat_8_9"
SYNTHESIS_UNSAFE_EDGE_IDS = frozenset(
    {
        "origen-lit-005",
        "reading-a-124",
        "reading-a-127",
        "8cb6fd24-023e-4199-af8b-a4f823589cce",
    }
)
MACHINE_NODES = (
    "passage_tatian_orat_7_en",
    "passage_tatian_orat_8_9_en",
    "passage_tatian_orat_11_en",
)
FINE_NODES = (
    "passage_tatian_7_1",
    "passage_tatian_7_2",
    "passage_tatian_8_1",
    "passage_tatian_9_1",
    "passage_tatian_11_1",
    "passage_tatian_11_2",
)

OTTO_SOURCE_ID = "src_ed_tatian_otto1851_perseus_grc1"
TIMOTIN_SOURCE_ID = "src_sec_timotin_2016_tatian"
STRUTWOLF_SOURCE_ID = "src_sec_strutwolf_lakmann_2016_tatian_soul"
ISSUE_ID = "issue_tatian_oratio_mixed_editorial_snapshots_20260824"
WAVE_ID = "wave_00_known_factual_blockers"
TATIAN_OPEN_DEBT = [
    "Thirty-nine corpus rows are first-segment excerpts, not full chapters.",
    "Full edition-variant collation is incomplete.",
    "No authorized human translation manifestation is registered.",
    "Secondary interpretations remain in_review.",
    "Independent, adversarial, and human sign-off remain pending.",
]

ANCIENT_EVIDENCE_IDS = {
    "tat_p01": "ev_anc_tatian_orat_7_2_autexousion",
    "tat_p02": "ev_anc_tatian_orat_7_3_foreknowledge",
    "tat_p03": "ev_anc_tatian_orat_8_1_demonic_fate",
    "tat_p04": "ev_anc_tatian_orat_9_3_above_fate",
    "tat_p05": "ev_anc_tatian_orat_11_4_autexousion_loss",
    "tat_p06": "ev_anc_tatian_orat_15_9_demonic_law",
}
TIMOTIN_EVIDENCE_ID = "ev_sec_timotin_tatian_pp267_286"
STRUTWOLF_EVIDENCE_ID = "ev_sec_strutwolf_lakmann_tatian_pp233_234"

SAPERE_PDF_RELATIVE = Path(
    "literature_acquisition/SAPERE28_Tatian_Rede_an_die_Griechen_2016_OA.pdf"
)
SAPERE_SHA256 = "33f355b55cb446273498b2557022e52c3e83a1f75aea84ec136eb31ea5aea4db"
SAPERE_RIGHTS = (
    "Mohr Siebeck copyright 2016; used only for page mapping, collation, and "
    "attributed paraphrase. No open licence or republication permission inferred."
)

QUARANTINE_RELATIVE = Path("audit/2026-08-24_tatian_p0_quarantine.jsonl")
REPORT_RELATIVE = Path("audit/2026-08-24_tatian_p0_repair.json")
TRANSACTION_RELATIVE = Path("audit/.tatian_p0_transaction")
LOCK_RELATIVE = Path("audit/.tatian_p0.lock")

INPUT_RELATIVES: dict[str, Path] = {
    "nodes": Path("kg/nodes.jsonl"),
    "edges": Path("kg/edges.jsonl"),
    "passages": Path("corpus/passages.jsonl"),
    "citations": Path("corpus/citations.jsonl"),
    "manifest": Path("corpus/manifest.jsonl"),
    "registry_sources": Path(
        "goals/sota/registry/sources/seed_priority_20260824.jsonl"
    ),
    "registry_evidence": Path(
        "goals/sota/registry/evidence/seed_priority_20260824.jsonl"
    ),
    "registry_issues": Path(
        "goals/sota/registry/issues/seed_known_20260824.jsonl"
    ),
    "registry_waves": Path(
        "goals/sota/registry/waves/priority_20260824.jsonl"
    ),
    "sapere_pdf": SAPERE_PDF_RELATIVE,
}
MUTABLE_LABELS = (
    "nodes",
    "edges",
    "passages",
    "citations",
    "manifest",
    "registry_sources",
    "registry_evidence",
    "registry_issues",
    "registry_waves",
)

INPUT_BEFORE_SHA256 = {
    "nodes": "07adbfa2826e4c23a15f95dcae1504e1f2a0ac228433cee5835f1fe14b046e4d",
    "edges": "31ac588b16faacf6de7b6fd1d23d247e790c3bea1d3655a91dacea3cc8ccda2c",
    "passages": "4e2e7b8789de06f3b3cf897c3f9b6d63bc92db5ee24657dabee6c9ba510f51ec",
    "citations": "07f0ff46bc162fe69e86b7187f28653886e0bdcf3e863b0790e9f016b13c25ee",
    "manifest": "aa4d446f32b5d47d4fb3d002dec3b49398862f8f3f8515b6076655ea8e414cd6",
    "registry_sources": "54b02bc1ce94680f18b8e22e92f6a2aa4a21f0dd48a71e9a9eac168d9fd80d1e",
    "registry_evidence": "0d360b28689f260c00717462778a48c124d2992521a87165733df4044304f1e0",
    "registry_issues": "e265e74f274d3d62cb1b411bfe939229d88682859a0554349c30658e50738818",
    "registry_waves": "2cf060fc4aa38a0a6c7f17c01030c22e81e3e8b29cc4acb68989be9f1b432989",
}

INPUT_AFTER_SHA256 = {
    "nodes": "60082c52cddfa3e5441a2ae491af2d9c00c386f4f9ed8a8c4b836390a4e24f83",
    "edges": "2e417ac429988f1df282fbb0576f34b51e327479d0043738b9cf073715de6b72",
    "passages": "e8e79f62fb27198f3bfa93755a9f0615ad79e67037eaedd0d61fed5453f176f3",
    "citations": "3aea9ad22b6fe42c78429ce68fbb041c57d532e530463a01b18353d7c11a9c64",
    "manifest": "2e2bf033c11ae48af93902be02816a86de9d4c8422cd6800c6f388cab8f5026e",
    "registry_sources": "cc34488366f86d56726e99c1113195f2e8c128f2f44f2b1535d0dabdcd8cf7ac",
    "registry_evidence": "90aaa8fab0d4c5fbbb830b60f38d992514b6d5a512a0698397042cc090aa2307",
    "registry_issues": "5dca524033ebe628d5d9cd3431ebeddd9e8830314e430440d057a22e73d8ef17",
    "registry_waves": "6083cf65579d935441200440160d0a1d398a74c792c1b0bde869d65d9cf5db1c",
}

EXPECTED_OUTPUT_RELATIVES = {
    *(str(INPUT_RELATIVES[label]) for label in MUTABLE_LABELS),
    str(QUARANTINE_RELATIVE),
    str(REPORT_RELATIVE),
}

EXPECTED_TATIAN_CORPUS_PASSAGE_IDS = {
    "04a012aa-e662-42ed-ab7e-004ff86e51d1",
    "0dc1c27a-4c07-4540-8c7a-9848bcb4ee68",
    "16167cda-9952-4a24-885b-13f0fb7a30fa",
    "245a8d4a-d402-45a8-a7b9-4650e012dc89",
    "2a478a19-77cd-4314-b70e-3e2a55ab187d",
    "330b4bfc-0ccf-4c06-a01d-4f8c806688df",
    "3c51df53-54a3-48c1-8267-52a5ed93ba5a",
    "3f5fbd39-c23a-4938-9d87-13351dbf093e",
    "47437519-565e-46f1-88e4-9afdea50a3f5",
    "4a581196-c2d3-4bb9-92fe-7c55f3ece6e9",
    "4b57006b-8b41-4f31-b14e-7f54da609bba",
    "54589fa1-0cec-4232-ab37-df72db119bf5",
    "56fa068a-e845-49fa-add0-09158e4b5770",
    "662575cf-8db2-4467-8e69-8531e3b466c3",
    "6c3385fb-38b2-4e14-87df-620631b1d377",
    "6dcfe239-6fde-462c-a74e-2ddb0e65308e",
    "7cf1609f-5ce4-4bf4-b66d-91721f99c02e",
    "808cc931-ec5a-4c61-a138-4c54d483d08c",
    "890918ec-e7fb-466f-b755-f99239a71e3a",
    "8ac4c3f3-aab5-4680-80fc-5bc76ee466b0",
    "8cc979d7-e5d6-4880-8f97-7a26800feae0",
    "8e412b53-504c-4cfb-8dcd-83f58847eb4c",
    "915a040a-cd74-4fc9-91a6-06e2f17788bd",
    "9a953cc1-de90-466f-9ce0-f8821e85288d",
    "9e1a5801-cd3b-4b1b-b0d5-612affb90ce2",
    "a169384a-e491-4fcd-840e-1103b01c3328",
    "a36c2d9d-9306-4b6f-979a-b8922f7e5d04",
    "ab9edfce-b97c-44a2-9343-b1e162a28b6e",
    "b8c7e7f9-3548-4c86-ae4e-8a2701c31b6b",
    "bea30080-5319-4bcf-a3d0-4c8801b3608b",
    "c684c41a-cabe-400c-826d-25befaae0490",
    "c6a0a5e4-c139-4a26-b079-8b740b701704",
    "c8077aeb-d9ed-4b34-93b7-9c0b1caf801f",
    "ce388f19-6e52-49ef-aa10-39d8eab8da96",
    "d20522bc-0c07-4dcc-81ad-8c2d1f52949b",
    "d6337b3b-5df2-4060-b6ca-7c0851a6a138",
    "e06ffb4e-a568-4982-94d2-506db13f472a",
    "e3643908-0865-44e0-a5d4-56ea9f56a62e",
    "e3a3a853-296a-48f0-9791-fc732546f900",
    "f11e9e25-be9a-45f0-a24b-3d1145183027",
    "f8ceab87-f393-4ca6-aceb-e28dd1346abe",
    "fdefee1b-2430-4ed0-acc2-88f48f2fc875",
}

EXPECTED_RECORD_DIFF_IDS: dict[str, dict[str, list[str]]] = {
    "nodes": {
        "added": [EXACT_NODES[8]],
        "removed": [],
        "modified": sorted(
            {
                ARGUMENT_ABOVE,
                ARGUMENT_FREEWILL,
                PERSON_NODE,
                WORK_NODE,
                SYNTHESIS_NODE,
                *MACHINE_NODES,
                *FINE_NODES,
                EXACT_NODES[7],
                EXACT_NODES[11],
            }
        ),
    },
    "edges": {
        "added": sorted(
            {
                "3ec7b28c-3ccb-5704-93f8-9d346704b733",
                "784ee6d9-0f59-50ca-b244-3765c1111e3d",
            }
        ),
        "removed": sorted(
            {
                "3d77ec6c-0c99-4523-b86e-fdb48785f536",
                "78428983-9305-49f6-81d2-a848e5ff8f05",
                "1d8e8b3b-8ce5-4f31-8188-99132eab9138",
                *SYNTHESIS_UNSAFE_EDGE_IDS,
            }
        ),
        "modified": sorted(
            {
                "f648fc54-f651-4366-88f5-14fcb60b4b7c",
                "9a8f1ea8-194f-4fa6-a87d-93776b419c09",
                "ac602938-2750-4fcf-b5a1-3b8919d845eb",
                "76ee1c2d-f19c-47b1-89f4-8f43a6ad4b0b",
                "d82a72e7-6369-4956-99ec-36712baee3b5",
                "da752f22-d8c0-4637-8b10-d324233a83bf",
                "261db5f1-6dbf-440a-83cd-9302804db185",
                "18c26961-0d7d-4e1a-9e61-f056e4c05786",
                "0c5e94f9-136a-4612-a172-9e8f155c7e33",
                "c26ecb0a-ea54-493a-a31f-150f4042af53",
                "ca17b1cf-2277-46b4-8ee8-f8f62be70b4c",
            }
        ),
    },
    "passages": {
        "added": [],
        "removed": [],
        "modified": sorted(EXPECTED_TATIAN_CORPUS_PASSAGE_IDS),
    },
    "citations": {
        "added": sorted(
            {
                "\x1f".join(
                    (EXACT_NODES[8], TARGET_PASSAGES[8], "snapshot_passage_node")
                ),
                "\x1f".join(
                    (ARGUMENT_ABOVE, OTHER_EVIDENCE_PASSAGES[9], "grounded_in")
                ),
            }
        ),
        "removed": sorted(
            "\x1f".join((node, passage, "snapshot_passage_node"))
            for node, passage in {
                (MACHINE_NODES[0], TARGET_PASSAGES[7]),
                (SYNTHESIS_NODE, TARGET_PASSAGES[8]),
                (MACHINE_NODES[1], TARGET_PASSAGES[8]),
                (MACHINE_NODES[2], TARGET_PASSAGES[11]),
            }
        ),
        "modified": sorted(
            "\x1f".join(
                (EXACT_NODES[chapter], TARGET_PASSAGES[chapter], "snapshot_passage_node")
            )
            for chapter in (7, 11)
        ),
    },
    "manifest": {
        "added": [],
        "removed": [],
        "modified": [MANIFEST_ID],
    },
    "registry_sources": {
        "added": sorted({OTTO_SOURCE_ID, STRUTWOLF_SOURCE_ID}),
        "removed": [],
        "modified": [TIMOTIN_SOURCE_ID],
    },
    "registry_evidence": {
        "added": sorted({*ANCIENT_EVIDENCE_IDS.values(), STRUTWOLF_EVIDENCE_ID}),
        "removed": [],
        "modified": [TIMOTIN_EVIDENCE_ID],
    },
    "registry_issues": {
        "added": [ISSUE_ID],
        "removed": [],
        "modified": [],
    },
    "registry_waves": {
        "added": [],
        "removed": [],
        "modified": [WAVE_ID],
    },
}
EXPECTED_RECORD_DIFF_DIGESTS = {
    "nodes": "b160124409a6f0d06a11a6a3b6ca3631a657ef6400f8a4e05d9be7e0a570b1ea",
    "edges": "ade0a43bb46d35e5326b86862786da515473457421b3740b5a9e7ca3e3833a0e",
    "passages": "c69faa59c100493b8cb54e930adca568c8738be8ab89b8de1ce3a616f0ecd3e1",
    "citations": "cb0fdd49b26cf0182a209a76b7d494638381a2909496aef8b9621e620c5a5a3f",
    "manifest": "14d7eb3547c34c740bf55694674ff0457dd7494fb3b4925b7fd4fcd407f57066",
    "registry_sources": "f6f61057f05af38ee8926fba3ce53eb4f9f6b6fbc0fb74a0e248cc73b5158d07",
    "registry_evidence": "b146e7bb550ac0eb6a2f0cc448c3e93c0dda36330a090d91d578819eee6232c5",
    "registry_issues": "39adfaa388a21dfc162f387206a81e67c5f7fba40038c1f91016071d72098edf",
    "registry_waves": "511757bd468c1a30cad138f6f5de095d63cd8df6f9e2ef74dfb9ae8a3ad0b0c7",
}

TEI_NS = {"tei": "http://www.tei-c.org/ns/1.0"}


@dataclass(frozen=True)
class Authority:
    source: dict[str, Any]
    first_segment_hashes: dict[int, str]
    first_segment_numbers: dict[int, str]
    exact_evidence_segments: dict[str, dict[str, Any]]
    replacement_chapters: dict[int, str]
    mode: str


@dataclass(frozen=True)
class DataSnapshot:
    data_root: Path
    rows: dict[str, list[dict[str, Any]]]
    raw: dict[str, bytes]
    optional_artifacts: dict[Path, bytes | None]


@dataclass
class RepairResult:
    rows: dict[str, list[dict[str, Any]]]
    quarantine: list[dict[str, Any]]
    report: dict[str, Any]
    changes: Counter[str]
    validation: dict[str, Any]
    mode: str


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", value)).strip()


def text_hash(value: str) -> str:
    return hashlib.sha256(normalize_text(value).encode("utf-8")).hexdigest()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def snapshot_input_state(snapshot: DataSnapshot) -> str:
    hashes = {label: sha256_bytes(snapshot.raw[label]) for label in MUTABLE_LABELS}
    if hashes == INPUT_BEFORE_SHA256:
        return "before"
    if all(not value.startswith("__") for value in INPUT_AFTER_SHA256.values()) and (
        hashes == INPUT_AFTER_SHA256
    ):
        return "after"
    mismatches = {
        label: {
            "actual": hashes[label],
            "before": INPUT_BEFORE_SHA256[label],
            "after": INPUT_AFTER_SHA256[label],
        }
        for label in MUTABLE_LABELS
        if hashes[label]
        not in {INPUT_BEFORE_SHA256[label], INPUT_AFTER_SHA256[label]}
    }
    raise RuntimeError(
        "Tatian frozen input hashes do not match a complete before/after state: "
        + canonical_json(mismatches)
    )


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def record_hash(value: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def rows_from_bytes(raw: bytes) -> list[dict[str, Any]]:
    return [json.loads(line) for line in raw.decode("utf-8").splitlines() if line.strip()]


def node_id(row: dict[str, Any]) -> str:
    return str(row.get("node_id") or row.get("id") or "")


def edge_id(row: dict[str, Any]) -> str:
    return str(row.get("edge_id") or "")


def edge_source(row: dict[str, Any]) -> str:
    return str(row.get("source") or row.get("source_id") or "")


def edge_target(row: dict[str, Any]) -> str:
    return str(row.get("target") or row.get("target_id") or "")


def citation_key(row: dict[str, Any]) -> str:
    return "\x1f".join(
        (
            str(row.get("kg_node_id") or ""),
            str(row.get("passage_id") or ""),
            str(row.get("citation_type") or ""),
        )
    )


def metadata(row: dict[str, Any]) -> dict[str, Any]:
    value = row.get("metadata")
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            return {}
    return copy.deepcopy(value) if isinstance(value, dict) else {}


def set_metadata(row: dict[str, Any], value: dict[str, Any]) -> None:
    if isinstance(row.get("metadata"), str):
        row["metadata"] = json.dumps(value, ensure_ascii=False, sort_keys=True)
    else:
        row["metadata"] = value


def require_unique(
    rows: list[dict[str, Any]], field: str, wanted: str
) -> dict[str, Any]:
    matches = [row for row in rows if str(row.get(field) or "") == wanted]
    if len(matches) != 1:
        raise RuntimeError(f"expected one {field}={wanted!r}; found {len(matches)}")
    return matches[0]


def require_node(rows: list[dict[str, Any]], wanted: str) -> dict[str, Any]:
    matches = [row for row in rows if node_id(row) == wanted]
    if len(matches) != 1:
        raise RuntimeError(f"expected one node {wanted!r}; found {len(matches)}")
    return matches[0]


def append_unique(values: list[Any], value: Any) -> list[Any]:
    output = copy.deepcopy(values)
    if value not in output:
        output.append(copy.deepcopy(value))
    return output


def deterministic_id(*parts: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "eleutheria:" + ":".join(parts)))


def tei_local_name(element: ET.Element) -> str:
    return str(element.tag).rsplit("}", 1)[-1]


def inline_reading_text(element: ET.Element) -> str:
    """Return one TEI reading block without inventing inline boundaries.

    ``itertext`` includes descendant text and inline-element tails in document
    order. Normalization is deliberately the pre-existing NFC/whitespace policy;
    no spaces are inserted around inline markup such as ``milestone``, ``lb`` or
    ``hi``.
    """

    return normalize_text("".join(element.itertext()))


def chapter_semantic_blocks(element: ET.Element) -> list[str]:
    """Extract ordered chapter blocks while preserving TEI reading text.

    The pinned Otto TEI places all chapter reading text in numbered ``seg``
    elements. The walker also retains any meaningful paragraph/block text or
    tails outside a ``seg`` as separate blocks, so a future authority revision
    cannot silently drop them. Whitespace-only ``p``/``pb`` tails are ignored.
    """

    blocks: list[str] = []
    seen_segments = 0

    def append(value: str | None) -> None:
        if value is None:
            return
        normalized = normalize_text(value)
        if normalized:
            blocks.append(normalized)

    def walk(container: ET.Element) -> None:
        nonlocal seen_segments
        if tei_local_name(container) == "seg":
            append(inline_reading_text(container))
            seen_segments += 1
            return
        append(container.text)
        for child in list(container):
            walk(child)
            append(child.tail)

    walk(element)
    expected_segments = len(element.findall(".//tei:seg", TEI_NS))
    if seen_segments != expected_segments:
        raise RuntimeError(
            "authority TEI segment traversal drift: "
            f"expected {expected_segments}, saw {seen_segments}"
        )
    return blocks


def join_semantic_blocks(blocks: list[str]) -> str:
    """Join non-empty semantic blocks with exactly one ASCII space."""

    normalized = [normalize_text(block) for block in blocks if normalize_text(block)]
    return " ".join(normalized)


def validate_semantic_block_join(blocks: list[str], joined: str) -> None:
    expected = join_semantic_blocks(blocks)
    if joined != expected:
        raise RuntimeError(
            "authority semantic block boundary defect: expected one space "
            "between every adjacent TEI seg/block"
        )


def chapter_reading_text(element: ET.Element) -> str:
    blocks = chapter_semantic_blocks(element)
    if not blocks:
        raise RuntimeError("authority chapter contains no reading blocks")
    joined = join_semantic_blocks(blocks)
    validate_semantic_block_join(blocks, joined)
    return joined


def parse_authority_xml(
    raw: bytes,
) -> tuple[
    dict[int, str],
    dict[int, tuple[str, str]],
    dict[int, list[tuple[str, str]]],
]:
    root = ET.fromstring(raw)
    chapters: dict[int, str] = {}
    first_segments: dict[int, tuple[str, str]] = {}
    segment_texts: dict[int, list[tuple[str, str]]] = {}
    for element in root.findall(
        ".//tei:div[@type='textpart'][@subtype='chapter']", TEI_NS
    ):
        chapter = int(str(element.get("n")))
        if chapter in chapters:
            raise RuntimeError(f"duplicate authority chapter {chapter}")
        segments = element.findall(".//tei:seg", TEI_NS)
        if not segments:
            raise RuntimeError(f"authority chapter {chapter} lacks TEI segments")
        chapters[chapter] = chapter_reading_text(element)
        segment_texts[chapter] = [
            (str(segment.get("n") or ""), inline_reading_text(segment))
            for segment in segments
        ]
        segment = segments[0]
        if not segment.get("n"):
            raise RuntimeError(f"authority chapter {chapter} lacks first segment")
        first_segments[chapter] = (
            str(segment.get("n")),
            inline_reading_text(segment),
        )
    if set(chapters) != set(range(1, 43)):
        raise RuntimeError("authority TEI does not contain exactly chapters 1..42")
    return chapters, first_segments, segment_texts


def load_authority(
    fixture_path: Path = DEFAULT_AUTHORITY,
    authority_xml: Path | None = None,
) -> Authority:
    fixture_raw = fixture_path.read_bytes()
    if sha256_bytes(fixture_raw) != AUTHORITY_FIXTURE_SHA256:
        raise RuntimeError("Tatian authority fixture SHA-256 drift")
    payload = json.loads(fixture_raw.decode("utf-8"))
    source = payload.get("source") or {}
    if (
        source.get("tei_sha256")
        != "bfe1671160c9155552055a24bd86345d2efb5392cd03e70a947d4a7a9ce00e4a"
        or source.get("cts_sha256")
        != "df7b14a2b0db327787fea20a6a659104808f87a07e8c9017fec0e7a5775579d8"
        or source.get("release") != "1.1.32401591783"
        or source.get("annotated_tag_object")
        != "1c0e443edec985b9834db888b21d73cde35315ec"
        or source.get("commit")
        != "78f9df37d694a9e0e92de2963f2fa8852e49efb6"
        or source.get("version_urn") != VERSION_URN
        or source.get("chapter_count") != 42
        or source.get("license") != "CC BY-SA 4.0"
        or source.get("normalization")
        != (
            "Unicode NFC plus collapsed XML whitespace; numbered TEI seg blocks "
            "joined with one space; descendant reading text retained and markup omitted"
        )
    ):
        raise RuntimeError("Tatian authority fixture identity drift")
    first_hashes = {
        int(key): str(value)
        for key, value in (payload.get("first_segment_sha256_nfc") or {}).items()
    }
    first_numbers = {
        int(key): str(value)
        for key, value in (payload.get("first_segment_n") or {}).items()
    }
    replacement = {
        int(key): normalize_text(str(value))
        for key, value in (payload.get("replacement_full_chapters") or {}).items()
    }
    exact_evidence_segments = copy.deepcopy(
        payload.get("exact_evidence_segments") or {}
    )
    if set(first_hashes) != set(range(1, 43)) or set(first_numbers) != set(
        range(1, 43)
    ):
        raise RuntimeError("authority fixture does not cover 42 first segments")
    if set(replacement) != set(TARGET_PASSAGES):
        raise RuntimeError("authority fixture replacement scope is not chapters 7/8/11")
    if set(exact_evidence_segments) != {"15.9"}:
        raise RuntimeError("authority fixture exact evidence segment scope drift")
    segment_15_9 = exact_evidence_segments["15.9"]
    if (
        segment_15_9.get("chapter") != 15
        or segment_15_9.get("segment_n") != "26"
        or segment_15_9.get("sha256_nfc")
        != "c1c7d081eb9fed87d936019df642d1b6bdbae222eed64a7e6ad855d0ce6e6730"
        or segment_15_9.get("required_marker") != "θανάτου νόμους"
    ):
        raise RuntimeError("authority fixture Tatian 15.9 segment identity drift")
    if authority_xml is not None:
        raw = authority_xml.read_bytes()
        if sha256_bytes(raw) != source["tei_sha256"]:
            raise RuntimeError("authority TEI SHA-256 mismatch")
        chapters, first_segments, segment_texts = parse_authority_xml(raw)
        for chapter, expected in first_hashes.items():
            segment_number, segment_text = first_segments[chapter]
            if segment_number != first_numbers[chapter] or text_hash(segment_text) != expected:
                raise RuntimeError(f"authority first-segment drift at chapter {chapter}")
        for chapter, expected in replacement.items():
            if chapters[chapter] != expected:
                raise RuntimeError(f"authority full-chapter drift at chapter {chapter}")
        candidates = [
            text
            for number, text in segment_texts[15]
            if number == segment_15_9["segment_n"]
        ]
        if (
            len(candidates) != 1
            or text_hash(candidates[0]) != segment_15_9["sha256_nfc"]
            or segment_15_9["required_marker"] not in candidates[0]
        ):
            raise RuntimeError("authority Tatian 15.9 exact TEI segment drift")
        mode = "full_tei_verified"
    else:
        mode = "derived_fixture_pinned_to_raw_tei_sha256"
    return Authority(
        source=copy.deepcopy(source),
        first_segment_hashes=first_hashes,
        first_segment_numbers=first_numbers,
        exact_evidence_segments=exact_evidence_segments,
        replacement_chapters=replacement,
        mode=mode,
    )


def fetch_pinned_authority(authority: Authority) -> bytes:
    request = urllib.request.Request(
        str(authority.source["tei_url"]),
        headers={"User-Agent": "EleutherIA-Tatian-P0-audit/1.0"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:  # noqa: S310
        raw = response.read()
    if sha256_bytes(raw) != authority.source["tei_sha256"]:
        raise RuntimeError("downloaded Tatian authority SHA-256 mismatch")
    return raw


def load_citability_policy() -> tuple[Any, Any]:
    path = ROOT / "graphrag/src/eleutheria_graphrag/agents/citability.py"
    name = "_eleutheria_tatian_repair_citability"
    module = sys.modules.get(name)
    if module is None:
        spec = importlib.util.spec_from_file_location(name, path)
        if spec is None or spec.loader is None:
            raise RuntimeError("cannot load central citability policy")
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
    return module.CitabilityTier, module.evidence_policy


def passage_chapter(row: dict[str, Any]) -> int:
    urn = str(row.get("cts_urn") or "")
    match = re.fullmatch(re.escape(VERSION_URN) + r":(\d+)", urn)
    if match is None:
        raise RuntimeError(f"unexpected Tatian corpus CTS URN: {urn!r}")
    return int(match.group(1))


def source_provenance(authority: Authority) -> dict[str, Any]:
    return {
        "repository": authority.source["repository"],
        "release": authority.source["release"],
        "commit": authority.source["commit"],
        "source_url": authority.source["tei_url"],
        "source_tei_sha256": authority.source["tei_sha256"],
        "edition": authority.source["edition"],
        "license": authority.source["license"],
        "normalization": authority.source["normalization"],
        "authority_fixture_sha256": AUTHORITY_FIXTURE_SHA256,
        "independent_fail_v2_sha256": INDEPENDENT_REVIEW_V2_SHA256,
    }


def desired_corpus_passage(
    row: dict[str, Any], chapter: int, authority: Authority
) -> dict[str, Any]:
    wanted = copy.deepcopy(row)
    if chapter in TARGET_PASSAGES:
        wanted["text_content"] = authority.replacement_chapters[chapter]
        wanted["canonical_ref"] = f"Orat. {chapter}"
        alignment = "exact_full_tei_chapter"
        source_segment = None
    else:
        if text_hash(str(row.get("text_content") or "")) != authority.first_segment_hashes[
            chapter
        ]:
            raise RuntimeError(
                f"untouched Tatian chapter {chapter} is not the pinned first TEI segment"
            )
        alignment = "exact_first_tei_segment_legacy_chapter_excerpt"
        source_segment = authority.first_segment_numbers[chapter]
    wanted.update(
        {
            "edition_urn": VERSION_URN,
            "language": "grc",
            "manifestation_id": MANIFEST_ID,
            "passage_role": "original",
            "source_alignment_status": alignment,
            "source_commit": authority.source["commit"],
            "source_license": authority.source["license"],
            "source_release": authority.source["release"],
            "source_tei_sha256": authority.source["tei_sha256"],
            "source_tei_url": authority.source["tei_url"],
            "text_sha256_nfc": text_hash(str(wanted["text_content"])),
            "work_urn": WORK_URN,
        }
    )
    if source_segment is None:
        wanted.pop("source_segment_n", None)
    else:
        wanted["source_segment_n"] = source_segment
    return wanted


def desired_manifest(row: dict[str, Any], authority: Authority) -> dict[str, Any]:
    wanted = copy.deepcopy(row)
    wanted.update(
        {
            "artifact_sha256": authority.source["tei_sha256"],
            "artifact_status": "public_canonical_pinned_release",
            "author": "Tatian",
            "canonical_id": MANIFEST_ID,
            "cts_urn": VERSION_URN,
            "edition": authority.source["edition"],
            "ingest_class": "pinned_perseus_tei_mixed_granularity",
            "language": "grc",
            "license": authority.source["license"],
            "passage_role": "original",
            "passages": 42,
            "source": authority.source["tei_url"],
            "source_commit": authority.source["commit"],
            "source_release": authority.source["release"],
            "status": "in_corpus",
            "title": "Oratio ad Graecos",
            "work_urn": WORK_URN,
            "cohort_granularity": {
                "full_chapter_passages": sorted(TARGET_PASSAGES),
                "first_segment_legacy_excerpts": sorted(
                    set(range(1, 43)) - set(TARGET_PASSAGES)
                ),
                "coverage_status": "partial_mixed_granularity",
                "warning": (
                    "Thirty-nine rows are exact first TEI segments, not complete "
                    "chapters; only chapters 7, 8, and 11 are complete chapters."
                ),
            },
            "sapere_collation": {
                "artifact": f"data/{SAPERE_PDF_RELATIVE}",
                "sha256": SAPERE_SHA256,
                "purpose": "page_map_and_variant_collation_only",
                "rights": SAPERE_RIGHTS,
                "text_source_for_manifestation": False,
            },
        }
    )
    return wanted


def desired_exact_node(
    current: dict[str, Any] | None,
    chapter: int,
    passage: dict[str, Any],
    authority: Authority,
) -> dict[str, Any]:
    if current is None:
        node: dict[str, Any] = {
            "alternative_names": "[]",
            "created_at": UPDATED_AT,
            "description": passage["text_content"],
            "id": EXACT_NODES[chapter],
            "label": f"Tatian, Oratio ad Graecos {chapter} — Otto 1851 exact Greek chapter",
            "metadata": {},
            "node_id": EXACT_NODES[chapter],
            "period": "Patristic",
            "role": None,
            "school": "Christian Apologetics",
            "type": "passage",
            "updated_at": UPDATED_AT,
        }
    else:
        node = copy.deepcopy(current)
        node["label"] = (
            f"Tatian, Oratio ad Graecos {chapter} — Otto 1851 exact Greek chapter"
        )
        node["description"] = passage["text_content"]
        node["updated_at"] = UPDATED_AT
    data = metadata(node)
    for key in (
        "database_verified",
        "greek_text_excerpt",
        "note",
        "passage_ids",
        "passage_range",
        "reference",
        "source_verified",
    ):
        data.pop(key, None)
    data.update(
        {
            STAMP: True,
            "attestation_type": "direct",
            "author": "Tatian",
            "canonical_ref": f"Orat. {chapter}",
            "citability": "citable",
            "corpus_passage_id": passage["passage_id"],
            "cts_urn": passage["cts_urn"],
            "db_passage_id": passage["passage_id"],
            "edition": authority.source["edition"],
            "edition_urn": VERSION_URN,
            "language": "grc",
            "manifestation_id": MANIFEST_ID,
            "passage_id": passage["passage_id"],
            "passage_role": "original",
            "primary_text_status": "pinned_public_critical_edition",
            "source_commit": authority.source["commit"],
            "source_license": authority.source["license"],
            "source_release": authority.source["release"],
            "source_tei_sha256": authority.source["tei_sha256"],
            "source_tei_url": authority.source["tei_url"],
            "text_content_sha256_nfc": passage["text_sha256_nfc"],
            "work_canonical_id": WORK_URN,
            "work_title": "Oratio ad Graecos",
        }
    )
    set_metadata(node, data)
    return node


def desired_synthesis_node(row: dict[str, Any]) -> dict[str, Any]:
    wanted = copy.deepcopy(row)
    wanted["label"] = "Editorial synthesis: Tatian, Oratio 8–9 (discovery only)"
    wanted["description"] = (
        "EDITORIAL SYNTHESIS — NOT AN EXACT PRIMARY-SOURCE SNAPSHOT. Tatian "
        "connects demonic astral fate in chapter 8 with the Christian claim to "
        "be above fate in chapter 9. Cite the exact Otto chapter 8 node and the "
        "exact chapter-9 segment separately."
    )
    wanted["updated_at"] = UPDATED_AT
    data = metadata(wanted)
    for key in (
        "cts_urn",
        "database_verified",
        "passage_id",
        "passage_ids",
        "passage_range",
        "source_verified",
    ):
        data.pop(key, None)
    data.update(
        {
            STAMP: True,
            "attestation_type": "editorial_synthesis",
            "citable_as_primary": False,
            "citability": "discoverable_only",
            "editorial_author": "EleutherIA",
            "language": "eng",
            "passage_role": "editorial_synthesis",
            "primary_node_ids": [EXACT_NODES[8], "passage_tatian_9_1"],
            "related_corpus_passage_ids": [
                TARGET_PASSAGES[8],
                OTHER_EVIDENCE_PASSAGES[9],
            ],
            "source_identity_status": "editorial_not_a_manifestation",
            "work_canonical_id": WORK_URN,
        }
    )
    set_metadata(wanted, data)
    return wanted


def desired_machine_node(row: dict[str, Any]) -> dict[str, Any]:
    wanted = copy.deepcopy(row)
    wanted["updated_at"] = UPDATED_AT
    data = metadata(wanted)
    for key in ("cts_urn", "db_passage_id", "passage_id", "corpus_passage_id"):
        data.pop(key, None)
    data.update(
        {
            STAMP: True,
            "attestation_type": "editorial_translation",
            "citable_as_primary": False,
            "citability": "blocked",
            "citation_blocked": True,
            "language": "eng",
            "passage_role": "editorial_translation",
            "source_identity_status": "machine_translation_not_primary_evidence",
            "translation_type": "machine",
            "work_canonical_id": WORK_URN,
        }
    )
    set_metadata(wanted, data)
    return wanted


def desired_fine_node(row: dict[str, Any]) -> dict[str, Any]:
    wanted = copy.deepcopy(row)
    wanted["updated_at"] = UPDATED_AT
    data = metadata(wanted)
    wanted_id = node_id(wanted)
    if wanted_id == "passage_tatian_7_1":
        if "τῶν ἀνδρῶν κατασκευῆς" not in wanted["description"] and not data.get(
            STAMP
        ):
            raise RuntimeError("Tatian 7 fine-node corruption precondition drift")
        wanted["description"] = wanted["description"].replace(
            "τῶν ἀνδρῶν κατασκευῆς", "τῶν ἀνθρώπων κατασκευῆς"
        )
        wanted["label"] = "Tatian, Oratio 7.1–7.2 (SAPERE collation; key claim 7.2)"
        data.update(
            {
                "canonical_ref": "Orat. 7.1–7.2 (SAPERE)",
                "key_claim_ref": "Orat. 7.2 (SAPERE)",
                "variant_against_otto1851": {
                    "otto": "τῶν ἀνδρῶν κατασκευῆς",
                    "sapere_nesselrath": "τῶν ἀνθρώπων κατασκευῆς",
                },
            }
        )
    elif wanted_id == "passage_tatian_11_1":
        if "πλουσιώτατοι σιώτατοι" not in wanted["description"] and not data.get(STAMP):
            raise RuntimeError("Tatian 11 fine-node duplication precondition drift")
        wanted["description"] = wanted["description"].replace(
            "πλουσιώτατοι σιώτατοι", "πλουσιώτατοι"
        )
        wanted["label"] = "Tatian, Oratio 11.1–11.3 (SAPERE collation)"
        data.update(
            {
                "canonical_ref": "Orat. 11.1–11.3 (SAPERE)",
                "variant_against_otto1851": {
                    "otto": "πλουσιώτατοι σιώτατοι",
                    "sapere_nesselrath": "πλουσιώτατοι",
                },
            }
        )
    elif wanted_id == "passage_tatian_7_2":
        data["sapere_ref_range"] = "Orat. 7.3–7.5"
        data["key_claim_ref"] = "Orat. 7.3 (SAPERE)"
    elif wanted_id == "passage_tatian_9_1":
        data["sapere_ref_range"] = "Orat. 9.1–9.3"
        data["key_claim_ref"] = "Orat. 9.3 (SAPERE)"
    elif wanted_id == "passage_tatian_11_2":
        wanted["label"] = "Tatian, Oratio 11.4 (SAPERE collation)"
        data["canonical_ref"] = "Orat. 11.4 (SAPERE)"
        data["key_claim_ref"] = "Orat. 11.4 (SAPERE)"
    elif wanted_id == "passage_tatian_8_1":
        data["key_claim_ref"] = "Orat. 8.1 (SAPERE)"
    if wanted_id in {
        "passage_tatian_7_1",
        "passage_tatian_7_2",
        "passage_tatian_8_1",
        "passage_tatian_11_1",
        "passage_tatian_11_2",
    }:
        for key in ("db_passage_id", "passage_id", "corpus_passage_id"):
            data.pop(key, None)
        data.update(
            {
                "citability": "discoverable_only",
                "edition_context": "SAPERE 28 / Nesselrath 2016 collation",
                "manifestation_id": "tatian_sapere28_2016_collation_only",
                "passage_role": "edition_collation_excerpt",
                "rights": SAPERE_RIGHTS,
                "snapshot_eligible": False,
            }
        )
    data[STAMP] = True
    set_metadata(wanted, data)
    return wanted


def desired_person_node(row: dict[str, Any]) -> dict[str, Any]:
    wanted = copy.deepcopy(row)
    wanted["updated_at"] = UPDATED_AT
    wanted["description"] = (
        "Tatian the Syrian (fl. c. 150–180 CE) authored the Oratio ad Graecos. "
        "In SAPERE's numbering, Or. 7.2 links praise and blame with creatures "
        "made self-determining; 7.3 contrasts foreknowledge with fate; 8.1 "
        "calls demonic astral fate unjust; 9.3 says Christians are above fate; "
        "and 11.4 says self-determination caused human loss while agents can "
        "again reject manifested evil. These are source-locus claims, not a "
        "complete modern theory of the will."
    )
    data = metadata(wanted)
    for key in ("citation_verified", "verified_reference"):
        data.pop(key, None)
    data.update(
        {
            STAMP: True,
            "citation_verdict": "identity_checked_mixed_granularity_claims_in_review",
            "claim_review_status": (
                "source_loci_bounded_independent_adversarial_human_review_pending"
            ),
            "primary_loci_sapere": {
                "autexousion_praise_blame": "Orat. 7.2",
                "foreknowledge_not_fate": "Orat. 7.3",
                "demonic_fate_unjust": "Orat. 8.1",
                "above_fate": "Orat. 9.3",
                "autexousion_loss_rejection": "Orat. 11.4",
            },
            "edition_scope_note": (
                "Locus numbering follows SAPERE 28; corpus text manifestation "
                "is separately identified as Otto 1851/Perseus."
            ),
        }
    )
    for key in (
        "frede_2011_role",
        "frede_2011_judgement",
        "frede_2011_chapter_treatment",
        "verified_reference",
    ):
        data.pop(key, None)
    set_metadata(wanted, data)
    return wanted


def desired_work_node(row: dict[str, Any], authority: Authority) -> dict[str, Any]:
    wanted = copy.deepcopy(row)
    wanted["updated_at"] = UPDATED_AT
    wanted["description"] = (
        "Tatian's Oratio ad Graecos is preserved here through a pinned Otto "
        "1851 Perseus Greek manifestation. Direct loci relevant to agency are "
        "SAPERE 7.2, 7.3, 8.1, 9.3, 11.4, and 15.9. Modern claims about "
        "post-lapsarian freedom and demonic astral efficacy remain attributed "
        "secondary interpretations, not unqualified primary-text conclusions."
    )
    data = metadata(wanted)
    for key in ("citation_verified", "verified_reference"):
        data.pop(key, None)
    data.update(
        {
            STAMP: True,
            "citation_verdict": "work_identity_checked_mixed_granularity_claims_in_review",
            "claim_review_status": (
                "partial_corpus_independent_adversarial_human_review_pending"
            ),
            "canonical_id": WORK_URN,
            "edition_urn": VERSION_URN,
            "manifestation_id": MANIFEST_ID,
            "source_commit": authority.source["commit"],
            "source_release": authority.source["release"],
            "source_tei_sha256": authority.source["tei_sha256"],
            "work_canonical_id": WORK_URN,
            "key_passages": [
                "Orat. 7.2",
                "Orat. 7.3",
                "Orat. 8.1",
                "Orat. 9.3",
                "Orat. 11.4",
                "Orat. 15.9",
            ],
        }
    )
    set_metadata(wanted, data)
    return wanted


def desired_argument_above(row: dict[str, Any]) -> dict[str, Any]:
    wanted = copy.deepcopy(row)
    wanted["updated_at"] = UPDATED_AT
    wanted["label"] = "Tatian on demonic fate and being above fate (Orat. 8.1; 9.3)"
    wanted["description"] = (
        "DIRECT: Tatian says demons introduced an unjust astral fate (8.1), "
        "and Christians are above fate after recognizing the one unwandering "
        "master and rejecting fate's legislators (9.3). ATTRIBUTED READING: "
        "Timotin argues that Tatian subordinates rather than simply denies "
        "astral influence, locating it in demonic domination. The precise "
        "mechanism of liberation and broader incompatibilist classification "
        "remain reconstructed and unsettled."
    )
    data = metadata(wanted)
    data.update(
        {
            STAMP: True,
            "source": "Orat. 8.1 and 9.3 (SAPERE numbering)",
            "premises": [
                {
                    "id": "P1",
                    "text": "Demons introduced an astral scheme called fate, which Tatian calls very unjust.",
                    "attestation": "direct",
                    "evidence_role": "primary_text",
                    "locus": "Orat. 8.1",
                    "primary_sources": [EXACT_NODES[8]],
                    "secondary_sources": [],
                },
                {
                    "id": "P2",
                    "text": "The judge/judged, murderer/murdered, and rich/poor are presented as products of the same fate.",
                    "attestation": "direct",
                    "evidence_role": "primary_text",
                    "locus": "Orat. 8.1",
                    "primary_sources": [EXACT_NODES[8]],
                    "secondary_sources": [],
                },
                {
                    "id": "P3",
                    "text": "Christians say they are above fate and reject its legislators in relation to the one unwandering master.",
                    "attestation": "direct",
                    "evidence_role": "primary_text",
                    "locus": "Orat. 9.3",
                    "primary_sources": ["passage_tatian_9_1"],
                    "secondary_sources": [],
                },
                {
                    "id": "P4",
                    "text": "Tatian does not simply deny astral influence; Timotin interprets it as subordinated to demonic domination.",
                    "attestation": "reported_interpretation",
                    "evidence_role": "secondary_in_review",
                    "locus": "Timotin 2016, pp. 278–281",
                    "primary_sources": [],
                    "secondary_sources": [TIMOTIN_EVIDENCE_ID],
                },
                {
                    "id": "P5",
                    "text": "The exact causal mechanism and a modern incompatibilist classification are reconstructions, not direct wording.",
                    "attestation": "reconstructed",
                    "evidence_role": "editorial_reconstruction",
                    "primary_sources": [],
                    "secondary_sources": [],
                },
            ],
            "conclusion": {
                "text": "Tatian directly claims that Christians are above fate; the mechanism is described religiously and demonologically.",
                "attestation": "direct_with_reconstructed_mechanism_excluded",
                "locus": "Orat. 9.3",
                "primary_sources": ["passage_tatian_9_1"],
                "secondary_sources": [TIMOTIN_EVIDENCE_ID],
            },
            "validity_assessment": {
                "formally_valid": "not_adjudicated",
                "scholarly_consensus": "not_claimed",
                "rationale": (
                    "Direct source claims are separated from Timotin's attributed "
                    "reading and from unverified logical reconstruction."
                ),
            },
            "citation_verdict": "in_review_after_source_recollation",
            "citation_verified": False,
            "citability": "discoverable_only",
            "ancient_attestation_locus_classicus": [EXACT_NODES[8], "passage_tatian_9_1"],
            "engaged_by_scholars": [TIMOTIN_EVIDENCE_ID],
        }
    )
    for key in ("verified_reference", "evidence_status", "structured_v2_model"):
        data.pop(key, None)
    set_metadata(wanted, data)
    return wanted


def desired_argument_freewill(row: dict[str, Any]) -> dict[str, Any]:
    wanted = copy.deepcopy(row)
    wanted["updated_at"] = UPDATED_AT
    wanted["label"] = "Tatian on self-determination, loss, and rejecting evil (Orat. 11.4)"
    wanted["description"] = (
        "DIRECT: Tatian says humans were not made for death, die through "
        "themselves, were lost through self-determination, and those who "
        "manifested evil can reject it again (11.4). ATTRIBUTED READING: "
        "Strutwolf and Lakmann interpret freedom as persisting to some degree "
        "after the fall and grounding imputability and possible return. The "
        "stronger claim that free will itself is the means of salvation is not "
        "established by the present source."
    )
    data = metadata(wanted)
    direct_sources = [EXACT_NODES[11]]
    data.update(
        {
            STAMP: True,
            "source": "Orat. 11.4 (SAPERE numbering)",
            "premises": [
                {
                    "id": "P1",
                    "text": "Humans were not made for death and die through themselves.",
                    "attestation": "direct",
                    "evidence_role": "primary_text",
                    "locus": "Orat. 11.4",
                    "primary_sources": direct_sources,
                    "secondary_sources": [],
                },
                {
                    "id": "P2",
                    "text": "Self-determination caused human loss, and those who manifested evil can reject it again.",
                    "attestation": "direct",
                    "evidence_role": "primary_text",
                    "locus": "Orat. 11.4",
                    "primary_sources": direct_sources,
                    "secondary_sources": [],
                },
                {
                    "id": "P3",
                    "text": "Freedom persists to some degree after the fall and grounds imputability and possible return.",
                    "attestation": "reported_interpretation",
                    "evidence_role": "secondary_in_review",
                    "locus": "Strutwolf/Lakmann 2016, pp. 233–234",
                    "primary_sources": [],
                    "secondary_sources": [STRUTWOLF_EVIDENCE_ID],
                },
                {
                    "id": "P4",
                    "text": "Whether the same capacity is itself a means of salvation remains reconstructed and unverified.",
                    "attestation": "reconstructed",
                    "evidence_role": "editorial_reconstruction",
                    "primary_sources": [],
                    "secondary_sources": [],
                },
            ],
            "conclusion": {
                "text": "The direct text connects self-determination with loss and retains the possibility of rejecting manifested evil; it does not by itself define free will as salvation's means.",
                "attestation": "direct_scope_with_secondary_interpretation_separated",
                "locus": "Orat. 11.4",
                "primary_sources": direct_sources,
                "secondary_sources": [STRUTWOLF_EVIDENCE_ID],
            },
            "validity_assessment": {
                "formally_valid": "not_adjudicated",
                "scholarly_consensus": "not_claimed",
                "rationale": (
                    "The primary wording, attributed modern interpretation, and "
                    "editorial reconstruction are separately typed."
                ),
            },
            "citation_verdict": "in_review_after_source_recollation",
            "citation_verified": False,
            "citability": "discoverable_only",
            "ancient_attestation_locus_classicus": EXACT_NODES[11],
            "engaged_by_scholars": [STRUTWOLF_EVIDENCE_ID],
        }
    )
    for key in ("verified_reference", "verification_notes", "structured_v2_model"):
        data.pop(key, None)
    set_metadata(wanted, data)
    return wanted


def otto_source_record(authority: Authority) -> dict[str, Any]:
    return {
        "record_type": "source",
        "source_id": OTTO_SOURCE_ID,
        "source_kind": "critical_edition",
        "display_label": "Tatian, Oratio ad Graecos — Otto 1851 / Perseus grc1",
        "canonical_title": "Oratio ad Graecos",
        "creators": ["Tatian", "Johann Carl Theodor Otto (editor)"],
        "date_display": "1851",
        "languages": ["grc"],
        "traditions": ["greek_christian"],
        "topics": ["choice_will", "fate_necessity", "astrology_divination"],
        "scope_decision": "include_core",
        "identity_status": "authority_verified",
        "canonical_identifiers": {
            "cts_urn": VERSION_URN,
            "repository": authority.source["repository"],
            "release": authority.source["release"],
            "commit": authority.source["commit"],
        },
        "acquisition": {
            "status": "public_canonical",
            "manifest_publication_dirs": [],
            "artifacts": [
                {
                    "locator": authority.source["tei_url"],
                    "role": "tei",
                    "sha256": authority.source["tei_sha256"],
                },
                {
                    "locator": authority.source["cts_url"],
                    "role": "catalog_record",
                    "sha256": authority.source["cts_sha256"],
                },
            ],
        },
        "coverage": {
            "state": "partial",
            "kg_node_ids": [
                WORK_NODE,
                EXACT_NODES[7],
                EXACT_NODES[8],
                EXACT_NODES[11],
                "passage_tatian_9_1",
                "passage_tatian_15_1",
            ],
            "basis": (
                "Chapters 7, 8, and 11 are exact full chapters; the other "
                "thirty-nine corpus rows remain exact first-segment excerpts. "
                f"Corpus manifestation {MANIFEST_ID}; full-work atomic coverage "
                "and edition-variant review remain open."
            ),
            "last_audited": "2026-08-24",
        },
        "provenance": [
            {
                "locator": "tests/fixtures/tatian_otto1851_release_1.1.32401591783.json",
                "role": "test_report",
                "sha256": AUTHORITY_FIXTURE_SHA256,
            },
            {
                "locator": "docs/academic/2026-08-24-tatian-sapere28-pdf-audit.md",
                "role": "audit_report",
                "sha256": AUDIT_DOC_SHA256,
            },
            {
                "locator": "docs/academic/2026-08-24-tatian-p0-independent-review-v2.md",
                "role": "audit_report",
                "sha256": INDEPENDENT_REVIEW_V2_SHA256,
            },
        ],
        "notes": (
            "Perseus TEI header declares CC BY-SA 4.0. SAPERE is not the text "
            "source for this manifestation. Coverage points to corpus manifestation "
            f"{MANIFEST_ID}."
        ),
    }


def desired_timotin_source(row: dict[str, Any]) -> dict[str, Any]:
    wanted = copy.deepcopy(row)
    wanted.update(
        {
            "display_label": "Andrei Timotin, Gott und die Dämonen bei Tatian",
            "canonical_title": "Gott und die Dämonen bei Tatian",
            "date_display": "2016",
            "languages": ["deu"],
            "scope_decision": "include_core",
            "identity_status": "bibliography_verified",
            "canonical_identifiers": {
                "container_title": "Gegen falsche Götter und falsche Bildung. Tatian, Rede an die Griechen",
                "series": "SAPERE 28",
                "printed_pages": "267-286",
                "isbn": "978-3-16-152821-7",
                "eisbn": "978-3-16-156427-7",
            },
            "acquisition": {
                "status": "archived_verified",
                "manifest_publication_dirs": [],
                "artifacts": [
                    {
                        "locator": f"data/{SAPERE_PDF_RELATIVE}",
                        "role": "source_file",
                        "sha256": SAPERE_SHA256,
                    }
                ],
            },
            "coverage": {
                "state": "partial",
                "kg_node_ids": [ARGUMENT_ABOVE],
                "basis": (
                    "The astrology/demonology claim at printed pp. 278-281 is "
                    "page-mapped and in review; the complete essay is not atomized."
                ),
                "last_audited": "2026-08-24",
            },
            "provenance": [
                {
                    "locator": "docs/academic/2026-08-24-tatian-sapere28-pdf-audit.md",
                    "role": "audit_report",
                }
            ],
            "notes": SAPERE_RIGHTS,
        }
    )
    return wanted


def strutwolf_source_record() -> dict[str, Any]:
    return {
        "record_type": "source",
        "source_id": STRUTWOLF_SOURCE_ID,
        "source_kind": "secondary_publication",
        "display_label": "Strutwolf and Lakmann, Tatians Seelenlehre",
        "canonical_title": "Tatians Seelenlehre im Kontext der zeitgenössischen Philosophie",
        "creators": ["Holger Strutwolf", "Marie-Luise Lakmann"],
        "date_display": "2016",
        "languages": ["deu"],
        "traditions": ["greek_christian"],
        "topics": ["choice_will", "moral_responsibility", "soul_psychology"],
        "scope_decision": "include_core",
        "identity_status": "bibliography_verified",
        "canonical_identifiers": {
            "container_title": "Gegen falsche Götter und falsche Bildung. Tatian, Rede an die Griechen",
            "series": "SAPERE 28",
            "printed_pages": "225-244",
            "isbn": "978-3-16-152821-7",
            "eisbn": "978-3-16-156427-7",
        },
        "acquisition": {
            "status": "archived_verified",
            "manifest_publication_dirs": [],
            "artifacts": [
                {
                    "locator": f"data/{SAPERE_PDF_RELATIVE}",
                    "role": "source_file",
                    "sha256": SAPERE_SHA256,
                }
            ],
        },
        "coverage": {
            "state": "partial",
            "kg_node_ids": [ARGUMENT_FREEWILL],
            "basis": (
                "The post-lapsarian freedom interpretation at printed pp. 233-234 "
                "is page-mapped and in review; the complete essay is not atomized."
            ),
            "last_audited": "2026-08-24",
        },
        "provenance": [
            {
                "locator": "docs/academic/2026-08-24-tatian-sapere28-pdf-audit.md",
                "role": "audit_report",
            }
        ],
        "notes": SAPERE_RIGHTS,
    }


def ancient_evidence_records(authority: Authority) -> list[dict[str, Any]]:
    evidence_text_hashes = {
        "tat_p01": text_hash(authority.replacement_chapters[7]),
        "tat_p02": text_hash(authority.replacement_chapters[7]),
        "tat_p03": text_hash(authority.replacement_chapters[8]),
        "tat_p04": authority.first_segment_hashes[9],
        "tat_p05": text_hash(authority.replacement_chapters[11]),
        "tat_p06": authority.exact_evidence_segments["15.9"]["sha256_nfc"],
    }
    specs = (
        (
            "tat_p01",
            "At Oratio 7.2, Tatian links self-determining creation and freedom of choice with justified praise and blame.",
            "Oratio ad Graecos 7.2 (SAPERE numbering)",
            48,
            59,
            TARGET_PASSAGES[7],
            EXACT_NODES[7],
        ),
        (
            "tat_p02",
            "At Oratio 7.3, Tatian contrasts foreknowledge based on autonomous choosers' judgment with fate.",
            "Oratio ad Graecos 7.3 (SAPERE numbering)",
            48,
            59,
            TARGET_PASSAGES[7],
            EXACT_NODES[7],
        ),
        (
            "tat_p03",
            "At Oratio 8.1, Tatian says demons introduced an astral fate that he calls very unjust.",
            "Oratio ad Graecos 8.1 (SAPERE numbering)",
            50,
            61,
            TARGET_PASSAGES[8],
            EXACT_NODES[8],
        ),
        (
            "tat_p04",
            "At Oratio 9.3, Tatian says Christians are above fate and reject its legislators in relation to the one unwandering master.",
            "Oratio ad Graecos 9.3 (SAPERE numbering)",
            52,
            63,
            OTHER_EVIDENCE_PASSAGES[9],
            "passage_tatian_9_1",
        ),
        (
            "tat_p05",
            "At Oratio 11.4, Tatian says humans die through themselves, were lost through self-determination, and can reject manifested evil again.",
            "Oratio ad Graecos 11.4 (SAPERE numbering)",
            (56, 58),
            (67, 69),
            TARGET_PASSAGES[11],
            EXACT_NODES[11],
        ),
        (
            "tat_p06",
            "At Oratio 15.9, Tatian attributes laws of death to demons acting according to their self-determination and calls humans to conversion.",
            "Oratio ad Graecos 15.9 (SAPERE numbering)",
            66,
            77,
            None,
            WORK_NODE,
        ),
    )
    rows: list[dict[str, Any]] = []
    for key, claim, locus, printed, pdf, passage_id, target_node in specs:
        printed_range = (
            {"start": printed[0], "end": printed[1]}
            if isinstance(printed, tuple)
            else {"start": printed, "end": printed}
        )
        pdf_range = (
            {"start": pdf[0], "end": pdf[1]}
            if isinstance(pdf, tuple)
            else {"start": pdf, "end": pdf}
        )
        quotation: dict[str, Any] = {
            "status": "collated",
            "language": "grc",
            "text_sha256": evidence_text_hashes[key],
        }
        if passage_id is not None:
            quotation["corpus_passage_ids"] = [passage_id]
        exact_segment_note = (
            " Exact authority block: Otto/Perseus TEI chapter 15, seg n=26; "
            "the current chapter-15 corpus row is only first seg n=24 and is not linked."
            if key == "tat_p06"
            else ""
        )
        rows.append(
            {
                "record_type": "evidence",
                "evidence_id": ANCIENT_EVIDENCE_IDS[key],
                "source_id": OTTO_SOURCE_ID,
                "evidence_kind": "ancient_passage",
                "claim_text": claim,
                "attestation": "direct",
                "claim_status": "in_review",
                "locator": {
                    "canonical_locus": locus,
                    "edition_or_witness": (
                        authority.source["edition"]
                        + ("; exact TEI seg n=26" if key == "tat_p06" else "")
                    ),
                    "printed_pages": printed_range,
                    "pdf_pages": pdf_range,
                    "page_map_status": "visually_verified",
                },
                "quotation": quotation,
                "kg_targets": [target_node],
                "required_verification": [
                    "bibliographic_identity",
                    "locus_or_page",
                    "textual_exactness",
                    "semantic_entailment",
                    "attribution",
                    "independent_review",
                    "adversarial_review",
                ],
                "notes": (
                    "Text is Otto/Perseus; SAPERE supplies locus/page collation "
                    "only. The hash covers a complete Otto chapter for Tatian "
                    "P01/P02/P03/P05 and an exact first-segment legacy excerpt for "
                    "P04; P06 hashes exact TEI chapter-15 seg n=26. No SAPERE text "
                    "or translation is reproduced. Claim "
                    "remains in review pending independent and adversarial validation."
                    + exact_segment_note
                ),
            }
        )
    return rows


def desired_timotin_evidence(row: dict[str, Any]) -> dict[str, Any]:
    wanted = copy.deepcopy(row)
    wanted.update(
        {
            "claim_text": (
                "Timotin interprets Tatian's anti-astrology demonologically: "
                "astral/horoscopic influence is subordinated to demonic domination, "
                "and devotion to the one God grounds deliverance; Tatian does not "
                "simply deny every astral efficacy."
            ),
            "claim_status": "in_review",
            "locator": {
                "printed_pages": {"start": 278, "end": 281},
                "pdf_pages": {"start": 289, "end": 292},
                "page_map_status": "visually_verified",
            },
            "quotation": {
                "status": "paraphrase_only",
                "language": "deu",
            },
            "kg_targets": [ARGUMENT_ABOVE],
            "notes": (
                "No essay text is republished; independent review remains pending. "
                + SAPERE_RIGHTS
            ),
        }
    )
    return wanted


def strutwolf_evidence_record() -> dict[str, Any]:
    return {
        "record_type": "evidence",
        "evidence_id": STRUTWOLF_EVIDENCE_ID,
        "source_id": STRUTWOLF_SOURCE_ID,
        "evidence_kind": "secondary_claim",
        "claim_text": (
            "Strutwolf and Lakmann interpret freedom as persisting to some degree "
            "after the fall, grounding imputability and the possibility of return, "
            "while noting tension with Tatian's pessimistic anthropology."
        ),
        "attestation": "reported_interpretation",
        "claim_status": "in_review",
        "locator": {
            "printed_pages": {"start": 233, "end": 234},
            "pdf_pages": {"start": 244, "end": 245},
            "page_map_status": "visually_verified",
        },
        "quotation": {
            "status": "paraphrase_only",
            "language": "deu",
        },
        "kg_targets": [ARGUMENT_FREEWILL],
        "required_verification": [
            "bibliographic_identity",
            "locus_or_page",
            "semantic_entailment",
            "attribution",
            "independent_review",
            "adversarial_review",
        ],
        "notes": (
            "No essay text is republished; claim remains in review. " + SAPERE_RIGHTS
        ),
    }


def issue_record() -> dict[str, Any]:
    return {
        "record_type": "issue",
        "issue_id": ISSUE_ID,
        "issue_type": "source_text_divergence",
        "severity": "critical",
        "factual_risk": True,
        "status": "open",
        "summary": (
            "Three Tatian corpus UUIDs contain editorial/machine composites; six "
            "false snapshots expose them as exact Greek evidence; public loci and "
            "two arguments conflate direct text with unreviewed reconstruction."
        ),
        "affected_ids": [
            OTTO_SOURCE_ID,
            TIMOTIN_SOURCE_ID,
            STRUTWOLF_SOURCE_ID,
            *ANCIENT_EVIDENCE_IDS.values(),
            TIMOTIN_EVIDENCE_ID,
            STRUTWOLF_EVIDENCE_ID,
            PERSON_NODE,
            WORK_NODE,
            ARGUMENT_ABOVE,
            ARGUMENT_FREEWILL,
            EXACT_NODES[7],
            EXACT_NODES[8],
            EXACT_NODES[11],
            SYNTHESIS_NODE,
            *MACHINE_NODES,
        ],
        "evidence_artifacts": [
            {
                "locator": "docs/academic/2026-08-24-tatian-sapere28-pdf-audit.md",
                "role": "audit_report",
                "sha256": AUDIT_DOC_SHA256,
            },
            {
                "locator": "tests/fixtures/tatian_otto1851_release_1.1.32401591783.json",
                "role": "test_report",
                "sha256": AUTHORITY_FIXTURE_SHA256,
            },
            {
                "locator": "docs/academic/2026-08-24-tatian-p0-independent-review-v2.md",
                "role": "audit_report",
                "sha256": INDEPENDENT_REVIEW_V2_SHA256,
            },
            {
                "locator": "data/audit/2026-08-24_tatian_p0_repair.json",
                "role": "audit_report",
            },
            {
                "locator": "data/audit/2026-08-24_tatian_p0_quarantine.jsonl",
                "role": "audit_report",
            },
        ],
        "resolution_criteria": (
            "Apply the exact Otto chapter repair; keep SAPERE variants edition-"
            "specific; prove one citable snapshot per corpus row; retain partial "
            "coverage until all thirty-nine first-segment excerpts are replaced or "
            "honestly re-manifested; complete independent, adversarial, and human "
            f"review. Corpus manifestation {MANIFEST_ID} and passage IDs "
            f"{sorted(TARGET_PASSAGES.values())} remain affected. Open debt: full "
            "edition-variant collation, an authorized human translation, replacement "
            "or honest manifestation of thirty-nine first-segment excerpts, and "
            "review of secondary interpretations."
        ),
    }


def desired_wave(row: dict[str, Any]) -> dict[str, Any]:
    wanted = copy.deepcopy(row)
    for source_id in (OTTO_SOURCE_ID, TIMOTIN_SOURCE_ID, STRUTWOLF_SOURCE_ID):
        wanted["source_ids"] = append_unique(wanted["source_ids"], source_id)
    for evidence_id in (
        *ANCIENT_EVIDENCE_IDS.values(),
        TIMOTIN_EVIDENCE_ID,
        STRUTWOLF_EVIDENCE_ID,
    ):
        wanted["evidence_ids"] = append_unique(wanted["evidence_ids"], evidence_id)
    wanted["issue_ids"] = append_unique(wanted["issue_ids"], ISSUE_ID)
    wanted["exit_criteria"] = append_unique(
        wanted["exit_criteria"],
        (
            "Tatian's Otto manifestation has no editorial/machine text, exact "
            "snapshots are bijective, SAPERE variants remain edition-specific, and "
            "the open mixed-granularity/secondary-review debt stays explicit."
        ),
    )
    return wanted


def quarantine_record(
    record_type: str, record: dict[str, Any], reason: str
) -> dict[str, Any]:
    return {
        "record_type": record_type,
        "reason": reason,
        "record_sha256": record_hash(record),
        "record": copy.deepcopy(record),
    }


def exact_record_diff(
    before: dict[str, list[dict[str, Any]]],
    after: dict[str, list[dict[str, Any]]],
) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for label in MUTABLE_LABELS:
        key = JSONL_KEYS[label]
        old = {key(row): row for row in before[label]}
        new = {key(row): row for row in after[label]}
        if len(old) != len(before[label]) or len(new) != len(after[label]):
            raise RuntimeError(f"duplicate Tatian record identity in {label}")
        added = {
            identifier: {"after": record_hash(new[identifier])}
            for identifier in sorted(set(new) - set(old))
        }
        removed = {
            identifier: {"before": record_hash(old[identifier])}
            for identifier in sorted(set(old) - set(new))
        }
        modified = {
            identifier: {
                "before": record_hash(old[identifier]),
                "after": record_hash(new[identifier]),
            }
            for identifier in sorted(set(old) & set(new))
            if old[identifier] != new[identifier]
        }
        result[label] = {
            "added": added,
            "removed": removed,
            "modified": modified,
        }
    return result


def record_diff_ids(
    diff: dict[str, dict[str, Any]],
) -> dict[str, dict[str, list[str]]]:
    return {
        label: {
            operation: sorted(records)
            for operation, records in operations.items()
        }
        for label, operations in diff.items()
    }


def validate_frozen_record_diff(
    diff: dict[str, dict[str, Any]], *, state: str
) -> None:
    ids = record_diff_ids(diff)
    digests = {
        label: hashlib.sha256(canonical_json(operations).encode("utf-8")).hexdigest()
        for label, operations in diff.items()
    }
    if state == "after":
        if any(
            operation_ids
            for operations in ids.values()
            for operation_ids in operations.values()
        ):
            raise RuntimeError("applied Tatian state is not record-idempotent")
        return
    if EXPECTED_RECORD_DIFF_IDS and ids != EXPECTED_RECORD_DIFF_IDS:
        raise RuntimeError("Tatian exact changed-record set drift")
    if EXPECTED_RECORD_DIFF_DIGESTS and digests != EXPECTED_RECORD_DIFF_DIGESTS:
        raise RuntimeError("Tatian before/after record hash digest drift")


def add_or_validate(
    rows: list[dict[str, Any]],
    *,
    field: str,
    wanted: dict[str, Any],
    absence_type: str,
    count_key: str,
    quarantine: list[dict[str, Any]],
    changes: Counter[str],
) -> None:
    identifier = str(wanted[field])
    matches = [row for row in rows if str(row.get(field) or "") == identifier]
    if not matches:
        rows.append(copy.deepcopy(wanted))
        quarantine.append({"record_type": absence_type, field: identifier})
        changes[count_key] += 1
        return
    if len(matches) != 1 or matches[0] != wanted:
        raise RuntimeError(f"partial/conflicting new record {field}={identifier!r}")


def replace_if_changed(
    current: dict[str, Any],
    wanted: dict[str, Any],
    *,
    record_type: str,
    reason: str,
    count_key: str,
    quarantine: list[dict[str, Any]],
    changes: Counter[str],
) -> None:
    if current == wanted:
        return
    quarantine.append(quarantine_record(record_type, current, reason))
    current.clear()
    current.update(wanted)
    changes[count_key] += 1


def transform(snapshot: DataSnapshot, authority: Authority) -> RepairResult:
    input_state = snapshot_input_state(snapshot)
    rows = copy.deepcopy(snapshot.rows)
    quarantine: list[dict[str, Any]] = []
    changes: Counter[str] = Counter()

    if sha256_bytes(snapshot.raw["sapere_pdf"]) != SAPERE_SHA256:
        raise RuntimeError("SAPERE 28 PDF hash drift")
    if (
        not AUDIT_DOC.is_file()
        or sha256_bytes(AUDIT_DOC.read_bytes()) != AUDIT_DOC_SHA256
    ):
        raise RuntimeError("Tatian SAPERE audit document hash drift")
    if (
        not INDEPENDENT_REVIEW_V2.is_file()
        or sha256_bytes(INDEPENDENT_REVIEW_V2.read_bytes())
        != INDEPENDENT_REVIEW_V2_SHA256
    ):
        raise RuntimeError("Tatian independent FAIL v2 report hash drift")
    if (
        not HILDEBRANDT_REPORT.is_file()
        or sha256_bytes(HILDEBRANDT_REPORT.read_bytes())
        != HILDEBRANDT_REPORT_SHA256
    ):
        raise RuntimeError("Tatian post-Hildebrandt rebase report hash drift")

    corpus = [
        row
        for row in rows["passages"]
        if row.get("work_canonical_id") == MANIFEST_ID
    ]
    if len(corpus) != 42:
        raise RuntimeError(f"expected 42 Tatian corpus rows; found {len(corpus)}")
    by_chapter: dict[int, dict[str, Any]] = {}
    for row in corpus:
        chapter = passage_chapter(row)
        if chapter in by_chapter:
            raise RuntimeError(f"duplicate Tatian corpus chapter {chapter}")
        by_chapter[chapter] = row
    if set(by_chapter) != set(range(1, 43)):
        raise RuntimeError("Tatian corpus chapter membership is not 1..42")

    for chapter in range(1, 43):
        current = by_chapter[chapter]
        wanted = desired_corpus_passage(current, chapter, authority)
        replace_if_changed(
            current,
            wanted,
            record_type="corpus_passage_before",
            reason=(
                "replace contaminated composite with exact full Otto chapter"
                if chapter in TARGET_PASSAGES
                else "add honest first-segment identity/hash/provenance"
            ),
            count_key=(
                "corpus_full_chapters_restored"
                if chapter in TARGET_PASSAGES
                else "corpus_first_segments_enriched"
            ),
            quarantine=quarantine,
            changes=changes,
        )

    manifest = require_unique(rows["manifest"], "canonical_id", MANIFEST_ID)
    replace_if_changed(
        manifest,
        desired_manifest(manifest, authority),
        record_type="corpus_manifest_before",
        reason="pin Otto manifestation and declare mixed granularity/SAPERE rights",
        count_key="manifest_rows_updated",
        quarantine=quarantine,
        changes=changes,
    )

    nodes_by_id = {node_id(row): row for row in rows["nodes"]}
    for wanted_id in (
        PERSON_NODE,
        WORK_NODE,
        ARGUMENT_ABOVE,
        ARGUMENT_FREEWILL,
        EXACT_NODES[7],
        EXACT_NODES[11],
        SYNTHESIS_NODE,
        *MACHINE_NODES,
        *FINE_NODES,
    ):
        if wanted_id not in nodes_by_id:
            raise RuntimeError(f"required Tatian node missing: {wanted_id}")

    for chapter in (7, 11):
        current = nodes_by_id[EXACT_NODES[chapter]]
        wanted = desired_exact_node(current, chapter, by_chapter[chapter], authority)
        replace_if_changed(
            current,
            wanted,
            record_type="kg_node_before",
            reason=f"replace composite with exact Otto chapter {chapter} node",
            count_key="exact_nodes_updated",
            quarantine=quarantine,
            changes=changes,
        )

    existing_ch8 = nodes_by_id.get(EXACT_NODES[8])
    wanted_ch8 = desired_exact_node(existing_ch8, 8, by_chapter[8], authority)
    if existing_ch8 is None:
        rows["nodes"].append(wanted_ch8)
        nodes_by_id[EXACT_NODES[8]] = wanted_ch8
        quarantine.append(
            {"record_type": "kg_node_absence_before", "node_id": EXACT_NODES[8]}
        )
        changes["exact_nodes_added"] += 1
    elif existing_ch8 != wanted_ch8:
        raise RuntimeError("partial/conflicting exact Tatian chapter-8 node")

    synthesis = nodes_by_id[SYNTHESIS_NODE]
    replace_if_changed(
        synthesis,
        desired_synthesis_node(synthesis),
        record_type="kg_node_before",
        reason="demote mixed chapter 8-9 synthesis to discovery-only",
        count_key="synthesis_nodes_demoted",
        quarantine=quarantine,
        changes=changes,
    )
    for wanted_id in MACHINE_NODES:
        current = nodes_by_id[wanted_id]
        replace_if_changed(
            current,
            desired_machine_node(current),
            record_type="kg_node_before",
            reason="block machine translation and remove primary identity",
            count_key="machine_nodes_blocked",
            quarantine=quarantine,
            changes=changes,
        )
    for wanted_id in FINE_NODES:
        current = nodes_by_id[wanted_id]
        replace_if_changed(
            current,
            desired_fine_node(current),
            record_type="kg_node_before",
            reason="correct SAPERE locus/variant without mutating Otto manifestation",
            count_key="fine_nodes_recollated",
            quarantine=quarantine,
            changes=changes,
        )
    for wanted_id, builder, count_key in (
        (PERSON_NODE, desired_person_node, "person_nodes_updated"),
        (
            ARGUMENT_ABOVE,
            desired_argument_above,
            "argument_nodes_atomized",
        ),
        (
            ARGUMENT_FREEWILL,
            desired_argument_freewill,
            "argument_nodes_atomized",
        ),
    ):
        current = nodes_by_id[wanted_id]
        replace_if_changed(
            current,
            builder(current),
            record_type="kg_node_before",
            reason="correct public loci and separate direct/secondary/reconstructed claims",
            count_key=count_key,
            quarantine=quarantine,
            changes=changes,
        )
    work = nodes_by_id[WORK_NODE]
    replace_if_changed(
        work,
        desired_work_node(work, authority),
        record_type="kg_node_before",
        reason="pin work manifestation and correct public loci",
        count_key="work_nodes_updated",
        quarantine=quarantine,
        changes=changes,
    )

    removable_snapshot_pairs = {
        (MACHINE_NODES[0], TARGET_PASSAGES[7]),
        (SYNTHESIS_NODE, TARGET_PASSAGES[8]),
        (MACHINE_NODES[1], TARGET_PASSAGES[8]),
        (MACHINE_NODES[2], TARGET_PASSAGES[11]),
    }
    revalidated_snapshot_pairs = {
        (EXACT_NODES[7], TARGET_PASSAGES[7]): 7,
        (EXACT_NODES[11], TARGET_PASSAGES[11]): 11,
    }
    citations_out: list[dict[str, Any]] = []
    for citation in rows["citations"]:
        pair = (
            str(citation.get("kg_node_id") or ""),
            str(citation.get("passage_id") or ""),
        )
        if (
            citation.get("citation_type") == "snapshot_passage_node"
            and pair in removable_snapshot_pairs
        ):
            quarantine.append(
                quarantine_record(
                    "corpus_citation_before",
                    citation,
                    "remove false/double Tatian snapshot",
                )
            )
            changes["false_snapshots_removed"] += 1
            continue
        chapter = revalidated_snapshot_pairs.get(pair)
        if (
            citation.get("citation_type") == "snapshot_passage_node"
            and chapter is not None
        ):
            wanted_citation = {
                "citation_type": "snapshot_passage_node",
                "confidence": 1.0,
                "kg_node_id": EXACT_NODES[chapter],
                "notes": f"{STAMP}: exact pinned Otto full chapter",
                "passage_id": TARGET_PASSAGES[chapter],
            }
            if citation != wanted_citation:
                quarantine.append(
                    quarantine_record(
                        "corpus_citation_before",
                        citation,
                        "revalidate formerly false Tatian snapshot after exact node repair",
                    )
                )
                changes["false_snapshots_revalidated"] += 1
            citations_out.append(wanted_citation)
            continue
        citations_out.append(citation)
    rows["citations"] = citations_out
    desired_citations = [
        {
            "citation_type": "snapshot_passage_node",
            "confidence": 1.0,
            "kg_node_id": EXACT_NODES[chapter],
            "notes": f"{STAMP}: exact pinned Otto full chapter",
            "passage_id": TARGET_PASSAGES[chapter],
        }
        for chapter in (7, 8, 11)
    ]
    desired_citations.append(
        {
            "citation_type": "grounded_in",
            "confidence": 1.0,
            "kg_node_id": ARGUMENT_ABOVE,
            "notes": f"{STAMP}: direct above-fate wording at SAPERE 9.3",
            "passage_id": OTHER_EVIDENCE_PASSAGES[9],
        }
    )
    citation_index = {citation_key(row): row for row in rows["citations"]}
    for wanted in desired_citations:
        key = citation_key(wanted)
        current = citation_index.get(key)
        if current is None:
            rows["citations"].append(wanted)
            citation_index[key] = wanted
            quarantine.append(
                {"record_type": "corpus_citation_absence_before", "citation_key": key}
            )
            changes["citations_added"] += 1
        elif current != wanted:
            raise RuntimeError(f"partial/conflicting desired Tatian citation: {key}")

    edges_out: list[dict[str, Any]] = []
    for edge in rows["edges"]:
        identifier = edge_id(edge)
        if identifier in {
            "3d77ec6c-0c99-4523-b86e-fdb48785f536",
            "78428983-9305-49f6-81d2-a848e5ff8f05",
            "1d8e8b3b-8ce5-4f31-8188-99132eab9138",
        } | SYNTHESIS_UNSAFE_EDGE_IDS:
            quarantine.append(
                quarantine_record(
                    "kg_edge_before",
                    edge,
                    (
                        "remove invalid argument hierarchy/source edge or unsafe "
                        "primary/authorship edge to the editorial synthesis"
                    ),
                )
            )
            changes["edges_removed"] += 1
            continue
        wanted = copy.deepcopy(edge)
        if identifier in {
            "f648fc54-f651-4366-88f5-14fcb60b4b7c",
            "9a8f1ea8-194f-4fa6-a87d-93776b419c09",
            "ac602938-2750-4fcf-b5a1-3b8919d845eb",
        }:
            wanted["target"] = EXACT_NODES[8]
            wanted["target_id"] = EXACT_NODES[8]
            data = metadata(wanted)
            data.update(
                {
                    STAMP: True,
                    "evidence_role": "exact_primary_chapter_8",
                }
            )
            set_metadata(wanted, data)
        elif (
            edge_source(wanted) in MACHINE_NODES
            and wanted.get("relation") == "translation_of"
        ):
            data = metadata(wanted)
            data.update(
                {
                    STAMP: True,
                    "evidence_role": "blocked_editorial_machine_translation",
                    "citable": False,
                }
            )
            set_metadata(wanted, data)
        elif edge_source(wanted) == SYNTHESIS_NODE or edge_target(wanted) == SYNTHESIS_NODE:
            data = metadata(wanted)
            data.update(
                {
                    STAMP: True,
                    "evidence_role": "editorial_discovery_only_not_exact",
                    "citable_as_primary": False,
                }
            )
            set_metadata(wanted, data)
        if wanted != edge:
            quarantine.append(
                quarantine_record(
                    "kg_edge_before", edge, "revalidate Tatian primary/editorial edge scope"
                )
            )
            changes["edges_updated"] += 1
        edges_out.append(wanted)
    rows["edges"] = edges_out

    desired_edges = [
        {
            "created_at": UPDATED_AT,
            "edge_id": deterministic_id(EXACT_NODES[8], "authored_by", PERSON_NODE),
            "metadata": {STAMP: True, "source": "pinned Otto 1851 TEI"},
            "relation": "authored_by",
            "source": EXACT_NODES[8],
            "source_id": EXACT_NODES[8],
            "target": PERSON_NODE,
            "target_id": PERSON_NODE,
            "weight": 1.0,
        },
        {
            "created_at": UPDATED_AT,
            "edge_id": deterministic_id(EXACT_NODES[8], "part_of", WORK_NODE),
            "metadata": {STAMP: True, "source": "pinned Otto 1851 TEI"},
            "relation": "part_of",
            "source": EXACT_NODES[8],
            "source_id": EXACT_NODES[8],
            "target": WORK_NODE,
            "target_id": WORK_NODE,
            "weight": 1.0,
        },
    ]
    edges_by_id = {edge_id(row): row for row in rows["edges"]}
    for wanted in desired_edges:
        current = edges_by_id.get(wanted["edge_id"])
        if current is None:
            rows["edges"].append(wanted)
            edges_by_id[wanted["edge_id"]] = wanted
            quarantine.append(
                {"record_type": "kg_edge_absence_before", "edge_id": wanted["edge_id"]}
            )
            changes["edges_added"] += 1
        elif current != wanted:
            raise RuntimeError(f"partial/conflicting desired Tatian edge: {wanted['edge_id']}")

    sources = rows["registry_sources"]
    add_or_validate(
        sources,
        field="source_id",
        wanted=otto_source_record(authority),
        absence_type="registry_source_absence_before",
        count_key="registry_sources_added",
        quarantine=quarantine,
        changes=changes,
    )
    timotin_source = require_unique(sources, "source_id", TIMOTIN_SOURCE_ID)
    replace_if_changed(
        timotin_source,
        desired_timotin_source(timotin_source),
        record_type="registry_source_before",
        reason="verify SAPERE chapter identity/page map/rights without full coverage claim",
        count_key="registry_sources_updated",
        quarantine=quarantine,
        changes=changes,
    )
    add_or_validate(
        sources,
        field="source_id",
        wanted=strutwolf_source_record(),
        absence_type="registry_source_absence_before",
        count_key="registry_sources_added",
        quarantine=quarantine,
        changes=changes,
    )

    evidence = rows["registry_evidence"]
    for wanted in ancient_evidence_records(authority):
        add_or_validate(
            evidence,
            field="evidence_id",
            wanted=wanted,
            absence_type="registry_evidence_absence_before",
            count_key="registry_evidence_added",
            quarantine=quarantine,
            changes=changes,
        )
    timotin_evidence = require_unique(evidence, "evidence_id", TIMOTIN_EVIDENCE_ID)
    replace_if_changed(
        timotin_evidence,
        desired_timotin_evidence(timotin_evidence),
        record_type="registry_evidence_before",
        reason="page-map and cautiously type Timotin interpretation",
        count_key="registry_evidence_updated",
        quarantine=quarantine,
        changes=changes,
    )
    add_or_validate(
        evidence,
        field="evidence_id",
        wanted=strutwolf_evidence_record(),
        absence_type="registry_evidence_absence_before",
        count_key="registry_evidence_added",
        quarantine=quarantine,
        changes=changes,
    )
    add_or_validate(
        rows["registry_issues"],
        field="issue_id",
        wanted=issue_record(),
        absence_type="registry_issue_absence_before",
        count_key="registry_issues_added",
        quarantine=quarantine,
        changes=changes,
    )
    wave = require_unique(rows["registry_waves"], "wave_id", WAVE_ID)
    replace_if_changed(
        wave,
        desired_wave(wave),
        record_type="registry_wave_before",
        reason="register open Tatian critical repair/review debt",
        count_key="registry_waves_updated",
        quarantine=quarantine,
        changes=changes,
    )

    record_diff = exact_record_diff(snapshot.rows, rows)
    validate_frozen_record_diff(record_diff, state=input_state)
    validation = validate_result(rows, authority)
    validation["registry_schema_debt"] = normative_registry_schema_gate(
        snapshot.data_root, snapshot.rows, rows
    )
    validation["input_state"] = input_state
    validation["record_diff"] = record_diff
    validation["record_diff_ids"] = record_diff_ids(record_diff)
    validation["record_diff_digests"] = {
        label: hashlib.sha256(canonical_json(operations).encode("utf-8")).hexdigest()
        for label, operations in record_diff.items()
    }
    before_findings = _snapshot_findings(snapshot.rows)
    after_findings = _snapshot_findings(rows)
    before_fingerprints = {row["fingerprint"] for row in before_findings}
    novel = [row for row in after_findings if row["fingerprint"] not in before_fingerprints]
    if novel:
        raise RuntimeError(f"Tatian repair creates {len(novel)} new snapshot violations")
    validation.update(
        {
            "snapshot_global_before": len(before_findings),
            "snapshot_global_after": len(after_findings),
            "snapshot_global_new_fingerprints": 0,
        }
    )

    artifact_state = _artifact_state(snapshot)
    if artifact_state == "partial":
        raise RuntimeError("Tatian report/quarantine are partially present")
    mode = "planned" if changes else "already_applied"
    if changes and artifact_state != "absent":
        raise RuntimeError("Tatian output artifacts exist before first application")
    if not changes and artifact_state != "present":
        raise RuntimeError("Tatian data is repaired but report/quarantine are absent")

    report = build_report(snapshot, authority, changes, quarantine, validation, mode)
    return RepairResult(
        rows=rows,
        quarantine=quarantine,
        report=report,
        changes=changes,
        validation=validation,
        mode=mode,
    )


def normative_registry_schema_gate(
    data_root: Path,
    before_rows: dict[str, list[dict[str, Any]]],
    after_rows: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    from jsonschema import Draft7Validator

    sota_root = data_root / "goals/sota"
    registry_root = sota_root / "registry"
    schema = json.loads(
        (sota_root / "registry.schema.json").read_text(encoding="utf-8")
    )
    configs = {
        "source": ("sources", "source_id"),
        "evidence": ("evidence", "evidence_id"),
        "issue": ("issues", "issue_id"),
        "verification": ("verifications", "verification_id"),
        "wave": ("waves", "wave_id"),
    }

    def collect(directory: str, key: str) -> dict[str, dict[str, Any]]:
        result: dict[str, dict[str, Any]] = {}
        for path in sorted((registry_root / directory).glob("*.jsonl")):
            for row in read_jsonl(path):
                identifier = str(row[key])
                if identifier in result:
                    raise RuntimeError(f"duplicate registry identity: {identifier}")
                result[identifier] = row
        return result

    before = {
        record_type: collect(directory, key)
        for record_type, (directory, key) in configs.items()
    }
    after = copy.deepcopy(before)
    target = {
        "source": ("registry_sources", "source_id"),
        "evidence": ("registry_evidence", "evidence_id"),
        "issue": ("registry_issues", "issue_id"),
        "wave": ("registry_waves", "wave_id"),
    }
    touched: dict[str, set[str]] = {record_type: set() for record_type in configs}
    for record_type, (label, key) in target.items():
        old_map = {str(row[key]): row for row in before_rows[label]}
        new_map = {str(row[key]): row for row in after_rows[label]}
        for identifier in old_map:
            after[record_type].pop(identifier, None)
        after[record_type].update(new_map)
        touched[record_type] = {
            identifier
            for identifier in set(old_map) | set(new_map)
            if old_map.get(identifier) != new_map.get(identifier)
        }
    validators = {
        record_type: Draft7Validator(
            {
                "$schema": "http://json-schema.org/draft-07/schema#",
                "$defs": schema["$defs"],
                "$ref": f"#/$defs/{record_type}",
            }
        )
        for record_type in configs
    }

    def error_set(
        collections: dict[str, dict[str, dict[str, Any]]],
    ) -> set[tuple[Any, ...]]:
        found: set[tuple[Any, ...]] = set()
        for record_type, records in collections.items():
            for identifier, row in records.items():
                for error in validators[record_type].iter_errors(row):
                    found.add(
                        (
                            record_type,
                            identifier,
                            tuple(error.absolute_path),
                            error.validator,
                            error.message,
                        )
                    )
        return found

    baseline_errors = error_set(before)
    preview_errors = error_set(after)
    if new_errors := preview_errors - baseline_errors:
        raise RuntimeError(
            "Tatian preview creates normative registry debt: "
            + canonical_json(sorted(new_errors))
        )
    touched_errors = []
    for record_type, identifiers in touched.items():
        for identifier in identifiers:
            record = after[record_type].get(identifier)
            if record is None:
                continue
            touched_errors.extend(
                f"{record_type}:{identifier}:{error.message}"
                for error in validators[record_type].iter_errors(record)
            )
    if touched_errors:
        raise RuntimeError(
            "Tatian touched registry records violate normative schema: "
            + canonical_json(touched_errors)
        )
    return {
        "baseline_errors": len(baseline_errors),
        "preview_errors": len(preview_errors),
        "new_errors": 0,
        "removed_errors": len(baseline_errors - preview_errors),
        "touched_record_count": sum(len(values) for values in touched.values()),
        "touched_record_errors": 0,
    }


def _snapshot_findings(rows: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    from scripts.check_snapshot_passage_integrity import audit_integrity

    return audit_integrity(rows["nodes"], rows["passages"], rows["citations"])


def validate_result(
    rows: dict[str, list[dict[str, Any]]], authority: Authority
) -> dict[str, Any]:
    nodes = rows["nodes"]
    edges = rows["edges"]
    passages = rows["passages"]
    citations = rows["citations"]
    manifest = rows["manifest"]
    sources = rows["registry_sources"]
    evidence = rows["registry_evidence"]
    issues = rows["registry_issues"]
    waves = rows["registry_waves"]

    corpus = [row for row in passages if row.get("work_canonical_id") == MANIFEST_ID]
    if len(corpus) != 42:
        raise RuntimeError("Tatian repaired corpus is not 42 rows")
    by_chapter = {passage_chapter(row): row for row in corpus}
    for chapter in TARGET_PASSAGES:
        row = by_chapter[chapter]
        if (
            row.get("passage_id") != TARGET_PASSAGES[chapter]
            or normalize_text(str(row.get("text_content") or ""))
            != authority.replacement_chapters[chapter]
            or row.get("source_alignment_status") != "exact_full_tei_chapter"
            or row.get("canonical_ref") != f"Orat. {chapter}"
        ):
            raise RuntimeError(f"Tatian exact full chapter {chapter} validation failed")
    first_segment_count = 0
    for chapter in set(range(1, 43)) - set(TARGET_PASSAGES):
        row = by_chapter[chapter]
        if (
            text_hash(str(row.get("text_content") or ""))
            != authority.first_segment_hashes[chapter]
            or row.get("source_alignment_status")
            != "exact_first_tei_segment_legacy_chapter_excerpt"
            or row.get("source_segment_n") != authority.first_segment_numbers[chapter]
        ):
            raise RuntimeError(f"Tatian legacy first segment {chapter} validation failed")
        first_segment_count += 1
    for row in corpus:
        if (
            row.get("language") != "grc"
            or row.get("passage_role") != "original"
            or row.get("manifestation_id") != MANIFEST_ID
            or row.get("edition_urn") != VERSION_URN
            or row.get("text_sha256_nfc") != text_hash(str(row.get("text_content") or ""))
            or row.get("source_tei_sha256") != authority.source["tei_sha256"]
        ):
            raise RuntimeError(f"Tatian corpus provenance incomplete: {row.get('passage_id')}")

    manifestation = require_unique(manifest, "canonical_id", MANIFEST_ID)
    granularity = manifestation.get("cohort_granularity") or {}
    if (
        manifestation.get("cts_urn") != VERSION_URN
        or manifestation.get("artifact_sha256") != authority.source["tei_sha256"]
        or manifestation.get("license") != "CC BY-SA 4.0"
        or granularity.get("full_chapter_passages") != [7, 8, 11]
        or len(granularity.get("first_segment_legacy_excerpts") or []) != 39
        or granularity.get("coverage_status") != "partial_mixed_granularity"
        or (manifestation.get("sapere_collation") or {}).get("text_source_for_manifestation")
        is not False
    ):
        raise RuntimeError("Tatian manifestation identity/granularity/rights failed")

    nodes_by_id = {node_id(row): row for row in nodes}
    passages_by_id = {str(row.get("passage_id") or ""): row for row in passages}
    snapshot_rows = [
        row
        for row in citations
        if row.get("citation_type") == "snapshot_passage_node"
        and row.get("passage_id") in {item["passage_id"] for item in corpus}
    ]
    by_snapshot_passage: Counter[str] = Counter(
        str(row.get("passage_id") or "") for row in snapshot_rows
    )
    by_snapshot_node: Counter[str] = Counter(
        str(row.get("kg_node_id") or "") for row in snapshot_rows
    )
    if len(snapshot_rows) != 42 or any(
        by_snapshot_passage[row["passage_id"]] != 1 for row in corpus
    ):
        raise RuntimeError("Tatian corpus snapshots are not passage-bijective")
    for snapshot in snapshot_rows:
        passage_id = str(snapshot["passage_id"])
        wanted_node = str(snapshot["kg_node_id"])
        node = nodes_by_id.get(wanted_node)
        if (
            node is None
            or normalize_text(str(node.get("description") or ""))
            != normalize_text(str(passages_by_id[passage_id]["text_content"]))
            or by_snapshot_node[wanted_node] != 1
        ):
            raise RuntimeError(f"Tatian snapshot text/node mismatch: {passage_id}")
    expected_exact_pairs = {
        (EXACT_NODES[chapter], TARGET_PASSAGES[chapter]) for chapter in TARGET_PASSAGES
    }
    actual_pairs = {
        (str(row.get("kg_node_id") or ""), str(row.get("passage_id") or ""))
        for row in snapshot_rows
    }
    if not expected_exact_pairs.issubset(actual_pairs):
        raise RuntimeError("Tatian exact repaired chapter snapshots are absent")
    if any(
        str(row.get("kg_node_id") or "") in {*MACHINE_NODES, SYNTHESIS_NODE}
        for row in snapshot_rows
    ):
        raise RuntimeError("machine/synthesis Tatian snapshot survived")

    CitabilityTier, evidence_policy = load_citability_policy()
    for wanted_id in MACHINE_NODES:
        data = metadata(nodes_by_id[wanted_id])
        if (
            data.get("citability") != "blocked"
            or data.get("translation_type") != "machine"
            or evidence_policy(nodes_by_id[wanted_id]).tier is not CitabilityTier.BLOCKED
        ):
            raise RuntimeError(f"Tatian machine node is not blocked: {wanted_id}")
    synthesis_data = metadata(nodes_by_id[SYNTHESIS_NODE])
    if (
        synthesis_data.get("citability") != "discoverable_only"
        or evidence_policy(nodes_by_id[SYNTHESIS_NODE]).tier
        is not CitabilityTier.DISCOVERABLE_ONLY
    ):
        raise RuntimeError("Tatian chapter 8-9 synthesis is not discovery-only")
    for wanted_id in (ARGUMENT_ABOVE, ARGUMENT_FREEWILL):
        data = metadata(nodes_by_id[wanted_id])
        if (
            data.get("citability") != "discoverable_only"
            or evidence_policy(nodes_by_id[wanted_id]).tier
            is not CitabilityTier.DISCOVERABLE_ONLY
        ):
            raise RuntimeError(f"Tatian argument is still runtime-citable: {wanted_id}")
    for chapter, wanted_id in EXACT_NODES.items():
        data = metadata(nodes_by_id[wanted_id])
        if (
            data.get("citability") != "citable"
            or data.get("manifestation_id") != MANIFEST_ID
            or data.get("text_content_sha256_nfc")
            != by_chapter[chapter]["text_sha256_nfc"]
            or evidence_policy(nodes_by_id[wanted_id]).tier
            is not CitabilityTier.CITABLE
        ):
            raise RuntimeError(f"Tatian exact node {chapter} is incomplete")

    corpus7 = normalize_text(by_chapter[7]["text_content"])
    exact7 = normalize_text(nodes_by_id[EXACT_NODES[7]]["description"])
    fine7 = normalize_text(nodes_by_id["passage_tatian_7_1"]["description"])
    corpus11 = normalize_text(by_chapter[11]["text_content"])
    exact11 = normalize_text(nodes_by_id[EXACT_NODES[11]]["description"])
    fine11 = normalize_text(nodes_by_id["passage_tatian_11_1"]["description"])
    if (
        "τῶν ἀνδρῶν κατασκευῆς" not in corpus7
        or "τῶν ἀνδρῶν κατασκευῆς" not in exact7
        or "τῶν ἀνθρώπων κατασκευῆς" not in fine7
        or "τῶν ἀνθρώπων κατασκευῆς" in corpus7
        or "πλουσιώτατοι σιώτατοι" not in corpus11
        or "πλουσιώτατοι σιώτατοι" not in exact11
        or "πλουσιώτατοι σιώτατοι" in fine11
    ):
        raise RuntimeError("Otto/SAPERE Tatian variant boundary was collapsed")

    public_serialized = "\n".join(
        canonical_json(nodes_by_id[wanted])
        for wanted in (PERSON_NODE, WORK_NODE, ARGUMENT_ABOVE, ARGUMENT_FREEWILL)
    )
    forbidden = (
        "Or. 7.1 declares",
        "Christians are liberated from fate through knowledge",
        "unique to the Apologists",
        "free will both destroys and saves",
        "means of human salvation",
        "standard scholarly topos",
    )
    if any(value.lower() in public_serialized.lower() for value in forbidden):
        raise RuntimeError("stale Tatian locus/overclaim remains public")
    for wanted_id in (PERSON_NODE, WORK_NODE):
        public_data = metadata(nodes_by_id[wanted_id])
        if "citation_verified" in public_data or "verified_reference" in public_data:
            raise RuntimeError(
                f"Tatian public node retains generic verified fields: {wanted_id}"
            )
        if public_data.get("citation_verdict") == "verified":
            raise RuntimeError(f"Tatian public node retains verified verdict: {wanted_id}")
    above = metadata(nodes_by_id[ARGUMENT_ABOVE])
    freewill = metadata(nodes_by_id[ARGUMENT_FREEWILL])
    for argument in (above, freewill):
        roles = {premise.get("evidence_role") for premise in argument.get("premises", [])}
        if not {
            "primary_text",
            "secondary_in_review",
            "editorial_reconstruction",
        }.issubset(roles):
            raise RuntimeError("Tatian argument evidence roles are not atomized")
        if argument.get("citation_verified") is not False:
            raise RuntimeError("Tatian argument falsely claims completed verification")

    forbidden_edge_ids = {
        "3d77ec6c-0c99-4523-b86e-fdb48785f536",
        "78428983-9305-49f6-81d2-a848e5ff8f05",
        "1d8e8b3b-8ce5-4f31-8188-99132eab9138",
    } | SYNTHESIS_UNSAFE_EDGE_IDS
    if forbidden_edge_ids & {edge_id(row) for row in edges}:
        raise RuntimeError("invalid Tatian argument hierarchy/source edge survived")
    above_primary_targets = {
        edge_target(row)
        for row in edges
        if edge_source(row) == ARGUMENT_ABOVE
        and row.get("relation") in {"cites_primary_source", "grounded_in"}
    }
    if not above_primary_targets or not above_primary_targets <= {
        EXACT_NODES[8],
        "passage_tatian_8_1",
        "passage_tatian_9_1",
    }:
        raise RuntimeError("above-fate argument retains a broad/foreign primary target")
    if any(
        edge_target(row) == SYNTHESIS_NODE
        and row.get("relation") == "cites_primary_source"
        for row in edges
    ):
        raise RuntimeError("active primary edge still targets Tatian editorial synthesis")
    if any(
        edge_source(row) == SYNTHESIS_NODE and row.get("relation") == "authored_by"
        for row in edges
    ):
        raise RuntimeError("editorial Tatian synthesis still has an ancient authored_by edge")
    exact_ch8_edges = {
        (edge_source(row), str(row.get("relation") or ""), edge_target(row))
        for row in edges
        if edge_source(row) == EXACT_NODES[8]
    }
    if exact_ch8_edges != {
        (EXACT_NODES[8], "authored_by", PERSON_NODE),
        (EXACT_NODES[8], "part_of", WORK_NODE),
    }:
        raise RuntimeError("Tatian exact chapter-8 structural edges are incomplete")

    otto_source = require_unique(sources, "source_id", OTTO_SOURCE_ID)
    timotin_source = require_unique(sources, "source_id", TIMOTIN_SOURCE_ID)
    strutwolf_source = require_unique(sources, "source_id", STRUTWOLF_SOURCE_ID)
    if (
        otto_source["coverage"]["state"] != "partial"
        or otto_source["acquisition"]["status"] != "public_canonical"
        or timotin_source["coverage"]["state"] != "partial"
        or strutwolf_source["coverage"]["state"] != "partial"
        or timotin_source.get("notes") != SAPERE_RIGHTS
        or strutwolf_source.get("notes") != SAPERE_RIGHTS
    ):
        raise RuntimeError("Tatian registry source coverage/rights are overstated")
    evidence_by_id = {
        str(row.get("evidence_id") or ""): row for row in evidence
    }
    for evidence_id in (
        *ANCIENT_EVIDENCE_IDS.values(),
        TIMOTIN_EVIDENCE_ID,
        STRUTWOLF_EVIDENCE_ID,
    ):
        record = evidence_by_id.get(evidence_id)
        if record is None or record.get("claim_status") != "in_review":
            raise RuntimeError(f"Tatian evidence is absent or falsely closed: {evidence_id}")
    evidence_15_9 = evidence_by_id[ANCIENT_EVIDENCE_IDS["tat_p06"]]
    if (
        evidence_15_9.get("quotation", {}).get("text_sha256")
        != authority.exact_evidence_segments["15.9"]["sha256_nfc"]
        or evidence_15_9.get("quotation", {}).get("corpus_passage_ids")
        is not None
        or evidence_15_9.get("kg_targets") != [WORK_NODE]
        or "seg n=26"
        not in str(evidence_15_9.get("locator", {}).get("edition_or_witness") or "")
    ):
        raise RuntimeError("Tatian 15.9 evidence is not aligned to exact TEI seg n=26")
    issue = require_unique(issues, "issue_id", ISSUE_ID)
    if issue.get("status") != "open" or issue.get("severity") != "critical":
        raise RuntimeError("Tatian critical registry issue is not open")
    wave = require_unique(waves, "wave_id", WAVE_ID)
    if ISSUE_ID not in wave.get("issue_ids", []):
        raise RuntimeError("Tatian issue is absent from factual-blocker wave")

    from scripts.check_corpus_invariants import find_violations as corpus_violations
    from scripts.check_kg_corpus_locus_parity import (
        find_violations as parity_violations,
    )
    from scripts.check_kg_work_child_canonical import find_mismatches
    from scripts.check_kg_work_id_uniqueness import collect_work_groups, find_collisions

    corpus_findings = corpus_violations(
        passages, citations, {node_id(row) for row in nodes}
    )
    if any(corpus_findings.values()):
        raise RuntimeError(
            "corpus invariant gate failed: "
            + canonical_json(
                {key: len(value) for key, value in corpus_findings.items()}
            )
        )
    shared, parity_findings = parity_violations(
        nodes,
        passages,
        citations,
        prefixes=tuple(EXACT_NODES.values()),
    )
    if shared != 3 or parity_findings:
        raise RuntimeError("Tatian exact-node parity gate failed")
    work_child = find_mismatches(nodes, edges, manifest)
    work_id = find_collisions(collect_work_groups(nodes, edges))
    if work_child or work_id:
        raise RuntimeError("Tatian repair creates work identity/canonical debt")
    return {
        "corpus_rows": len(corpus),
        "full_chapters": len(TARGET_PASSAGES),
        "first_segment_legacy_excerpts": first_segment_count,
        "snapshots": len(snapshot_rows),
        "machine_snapshots": 0,
        "synthesis_snapshots": 0,
        "corpus_violations": 0,
        "parity_shared_checked": shared,
        "parity_violations": 0,
        "work_child_mismatches": len(work_child),
        "work_id_collisions": len(work_id),
        "registry_issue_status": "open",
        "authority_mode": authority.mode,
    }


def _artifact_state(snapshot: DataSnapshot) -> str:
    values = snapshot.optional_artifacts.values()
    if all(value is None for value in values):
        return "absent"
    if all(value is not None for value in values):
        return "present"
    return "partial"


def build_report(
    snapshot: DataSnapshot,
    authority: Authority,
    changes: Counter[str],
    quarantine: list[dict[str, Any]],
    validation: dict[str, Any],
    mode: str,
) -> dict[str, Any]:
    return {
        "artifact_type": "eleutheria.tatian_p0_repair",
        "schema_version": "1.0",
        "stamp": STAMP,
        "generated_at": "2026-08-24T09:00:00Z",
        "mode": mode,
        "authority": {
            **source_provenance(authority),
            "authority_mode": authority.mode,
            "chapter_count": 42,
            "fixture_sha256": AUTHORITY_FIXTURE_SHA256,
        },
        "repair_scope": {
            "full_chapters_restored": sorted(TARGET_PASSAGES),
            "first_segment_legacy_excerpts_unchanged": sorted(
                set(range(1, 43)) - set(TARGET_PASSAGES)
            ),
            "false_snapshots": {
                "removed": 4,
                "revalidated_after_exact_node_repair": 2,
                "new_exact_chapter8": 1,
            },
            "sapere_variant_boundary": {
                "otto_chapter7": "τῶν ἀνδρῶν κατασκευῆς",
                "sapere_fine_node7": "τῶν ἀνθρώπων κατασκευῆς",
                "otto_chapter11": "πλουσιώτατοι σιώτατοι",
                "sapere_fine_node11": "πλουσιώτατοι",
                "cross_edition_normalization": "forbidden",
            },
        },
        "sapere": {
            "artifact": f"data/{SAPERE_PDF_RELATIVE}",
            "sha256": SAPERE_SHA256,
            "rights": SAPERE_RIGHTS,
            "uses": ["page_map", "variant_collation", "attributed_paraphrase"],
            "text_republication": False,
        },
        "changes": dict(sorted(changes.items())),
        "quarantine_records": len(quarantine),
        "validation": validation,
        "snapshot_a_sha256": {
            label: sha256_bytes(raw) for label, raw in sorted(snapshot.raw.items())
        },
        "output_sha256_preview": dict(sorted(INPUT_AFTER_SHA256.items())),
        "rebase_provenance": {
            "base": "post_hildebrandt_p0_2026_08_24",
            "hildebrandt_report": str(HILDEBRANDT_REPORT.relative_to(ROOT)),
            "hildebrandt_report_sha256": HILDEBRANDT_REPORT_SHA256,
        },
        "open_debt": TATIAN_OPEN_DEBT,
        "scope_exclusions": [
            "No deployment or remote data mutation.",
            "No Sorabji, Long/Sedley, or eval file mutation.",
            (
                "No Hildebrandt record, bibliography/report, acquisition builder, "
                "or literature/scholarly manifest mutation."
            ),
            "No independent, adversarial, or human PASS is asserted.",
            "The thirty-nine legacy excerpts are not relabelled as full chapters.",
        ],
    }


def _optional_read(path: Path) -> bytes | None:
    try:
        return path.read_bytes()
    except FileNotFoundError:
        return None


def load_data_snapshot(data_root: Path) -> DataSnapshot:
    paths = {label: data_root / relative for label, relative in INPUT_RELATIVES.items()}
    first = {label: path.read_bytes() for label, path in paths.items()}
    optional_paths = {
        QUARANTINE_RELATIVE: data_root / QUARANTINE_RELATIVE,
        REPORT_RELATIVE: data_root / REPORT_RELATIVE,
    }
    first_optional = {
        relative: _optional_read(path) for relative, path in optional_paths.items()
    }
    second = {label: path.read_bytes() for label, path in paths.items()}
    second_optional = {
        relative: _optional_read(path) for relative, path in optional_paths.items()
    }
    if first != second or first_optional != second_optional:
        raise RuntimeError("concurrent write detected while loading Tatian snapshot A")
    rows = {
        label: rows_from_bytes(raw)
        for label, raw in first.items()
        if label != "sapere_pdf"
    }
    return DataSnapshot(
        data_root=data_root.resolve(),
        rows=rows,
        raw=first,
        optional_artifacts=first_optional,
    )


def _jsonl_preserving(
    original: bytes,
    rows: list[dict[str, Any]],
    key: Callable[[dict[str, Any]], str],
    label: str,
) -> bytes:
    desired = {key(row): row for row in rows}
    if len(desired) != len(rows) or "" in desired:
        raise RuntimeError(f"duplicate/empty desired keys for {label}")
    output: list[str] = []
    seen: set[str] = set()
    for line in original.decode("utf-8").splitlines():
        if not line.strip():
            continue
        old = json.loads(line)
        identifier = key(old)
        replacement = desired.get(identifier)
        if replacement is None:
            continue
        seen.add(identifier)
        output.append(line if old == replacement else canonical_json(replacement))
    for row in rows:
        identifier = key(row)
        if identifier not in seen:
            output.append(canonical_json(row))
    return ("\n".join(output) + "\n").encode("utf-8")


JSONL_KEYS: dict[str, Callable[[dict[str, Any]], str]] = {
    "nodes": node_id,
    "edges": edge_id,
    "passages": lambda row: str(row.get("passage_id") or ""),
    "citations": citation_key,
    "manifest": lambda row: str(row.get("canonical_id") or ""),
    "registry_sources": lambda row: str(row.get("source_id") or ""),
    "registry_evidence": lambda row: str(row.get("evidence_id") or ""),
    "registry_issues": lambda row: str(row.get("issue_id") or ""),
    "registry_waves": lambda row: str(row.get("wave_id") or ""),
}


def build_outputs(
    data_root: Path, snapshot: DataSnapshot, result: RepairResult
) -> dict[Path, bytes]:
    if not result.changes:
        return {}
    outputs: dict[Path, bytes] = {}
    for label in MUTABLE_LABELS:
        payload = _jsonl_preserving(
            snapshot.raw[label], result.rows[label], JSONL_KEYS[label], label
        )
        if payload != snapshot.raw[label]:
            outputs[data_root / INPUT_RELATIVES[label]] = payload
    outputs[data_root / QUARANTINE_RELATIVE] = (
        "\n".join(canonical_json(row) for row in result.quarantine) + "\n"
    ).encode("utf-8")
    outputs[data_root / REPORT_RELATIVE] = (
        json.dumps(result.report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    relative_outputs = {
        str(path.resolve().relative_to(data_root.resolve())) for path in outputs
    }
    if relative_outputs != EXPECTED_OUTPUT_RELATIVES:
        raise RuntimeError(
            "Tatian output path set drift: "
            + canonical_json(sorted(relative_outputs ^ EXPECTED_OUTPUT_RELATIVES))
        )
    if all(not value.startswith("__") for value in INPUT_AFTER_SHA256.values()):
        for label in MUTABLE_LABELS:
            payload = outputs[data_root / INPUT_RELATIVES[label]]
            if sha256_bytes(payload) != INPUT_AFTER_SHA256[label]:
                raise RuntimeError(f"Tatian frozen output hash drift: {label}")
    return outputs


def _fsync_directory(directory: Path) -> None:
    descriptor = os.open(directory, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _write_fsynced(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as handle:
        handle.write(content)
        handle.flush()
        os.fsync(handle.fileno())
    _fsync_directory(path.parent)


def _stage_bytes(target: Path, content: bytes) -> Path:
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "wb", dir=target.parent, prefix=".tatian-stage-", delete=False
    ) as handle:
        temporary = Path(handle.name)
        handle.write(content)
        handle.flush()
        os.fsync(handle.fileno())
    _fsync_directory(target.parent)
    return temporary


def _replace_staged_file(staged: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    os.replace(staged, target)
    _fsync_directory(target.parent)


def _remove_file(path: Path) -> None:
    path.unlink(missing_ok=True)
    _fsync_directory(path.parent)


def _allowed_targets() -> set[str]:
    return {
        str(INPUT_RELATIVES[label]) for label in MUTABLE_LABELS
    } | {str(QUARANTINE_RELATIVE), str(REPORT_RELATIVE)}


def _safe_target(data_root: Path, relative: str) -> Path:
    root = data_root.resolve()
    target = (root / relative).resolve()
    if root not in target.parents or relative not in _allowed_targets():
        raise RuntimeError(f"unsafe/out-of-scope Tatian transaction target: {relative}")
    return target


def _journal_path(data_root: Path) -> Path:
    return data_root / TRANSACTION_RELATIVE / "journal.json"


def _write_journal(path: Path, journal: dict[str, Any]) -> None:
    payload = (
        json.dumps(journal, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    staged = _stage_bytes(path, payload)
    _replace_staged_file(staged, path)


def _cleanup_transaction(data_root: Path) -> None:
    transaction = data_root / TRANSACTION_RELATIVE
    if not transaction.exists():
        return
    if transaction.resolve() != (data_root / TRANSACTION_RELATIVE).resolve():
        raise RuntimeError("unsafe Tatian transaction cleanup")
    shutil.rmtree(transaction)
    _fsync_directory(transaction.parent)


def _verify_snapshot_a(data_root: Path, snapshot: DataSnapshot) -> None:
    for label, expected in snapshot.raw.items():
        if (data_root / INPUT_RELATIVES[label]).read_bytes() != expected:
            raise RuntimeError(f"Tatian snapshot-A drift: {label}")
    for relative, expected in snapshot.optional_artifacts.items():
        if _optional_read(data_root / relative) != expected:
            raise RuntimeError(f"Tatian snapshot-A artifact drift: {relative}")


def _entry_matches(data_root: Path, entry: dict[str, Any], which: str) -> bool:
    target = _safe_target(data_root, str(entry["target"]))
    current = _optional_read(target)
    expected = entry[f"{which}_sha256"]
    if expected is None:
        return current is None
    return current is not None and sha256_bytes(current) == expected


def _restore_entries(data_root: Path, journal: dict[str, Any]) -> None:
    foreign = []
    for entry in journal["entries"]:
        if _entry_matches(data_root, entry, "before") or _entry_matches(
            data_root, entry, "after"
        ):
            continue
        target = _safe_target(data_root, str(entry["target"]))
        current = _optional_read(target)
        foreign.append(
            {
                "target": entry["target"],
                "actual_sha256": sha256_bytes(current) if current is not None else None,
                "before_sha256": entry["before_sha256"],
                "after_sha256": entry["after_sha256"],
            }
        )
    if foreign:
        blocked = copy.deepcopy(journal)
        blocked["state"] = "recovery_blocked_foreign_drift"
        blocked["foreign_drift"] = foreign
        _write_journal(_journal_path(data_root), blocked)
        raise RuntimeError(
            "Tatian foreign drift blocks rollback: " + canonical_json(foreign)
        )
    journal["state"] = "rolling_back"
    journal.pop("foreign_drift", None)
    _write_journal(_journal_path(data_root), journal)
    transaction = data_root / TRANSACTION_RELATIVE
    for entry in reversed(journal["entries"]):
        if _entry_matches(data_root, entry, "before"):
            continue
        target = _safe_target(data_root, str(entry["target"]))
        before_hash = entry["before_sha256"]
        if before_hash is None:
            if target.exists():
                _remove_file(target)
            continue
        backup = transaction / str(entry["backup"])
        raw = backup.read_bytes()
        if sha256_bytes(raw) != before_hash:
            raise RuntimeError(f"Tatian backup hash mismatch: {backup}")
        staged = _stage_bytes(target, raw)
        _replace_staged_file(staged, target)
    if not all(_entry_matches(data_root, entry, "before") for entry in journal["entries"]):
        raise RuntimeError("Tatian rollback verification failed")
    _cleanup_transaction(data_root)


def recover_incomplete_transaction_locked(data_root: Path) -> str:
    transaction = data_root / TRANSACTION_RELATIVE
    if not transaction.exists():
        return "none"
    journal_path = _journal_path(data_root)
    if not journal_path.exists():
        _cleanup_transaction(data_root)
        return "orphan_prejournal_stage_removed"
    journal = json.loads(journal_path.read_text(encoding="utf-8"))
    if journal.get("transaction_id") != STAMP:
        raise RuntimeError("foreign journal at Tatian transaction path")
    entries = journal.get("entries")
    if not isinstance(entries, list) or not entries:
        raise RuntimeError("invalid Tatian transaction journal")
    for entry in entries:
        _safe_target(data_root, str(entry.get("target") or ""))
    state = str(journal.get("state") or "")
    all_before = all(_entry_matches(data_root, entry, "before") for entry in entries)
    all_after = all(_entry_matches(data_root, entry, "after") for entry in entries)
    if state == "prepared":
        if not all_before:
            raise RuntimeError("prepared Tatian transaction touched a target")
        _cleanup_transaction(data_root)
        return "prepared_stage_removed"
    if state == "committed":
        if not all_after:
            raise RuntimeError("committed Tatian transaction target drift")
        _cleanup_transaction(data_root)
        return "committed_cleanup_finished"
    if state in {"committing", "rolling_back", "recovery_blocked_foreign_drift"}:
        if state == "committing" and all_after:
            journal["state"] = "committed"
            _write_journal(journal_path, journal)
            _cleanup_transaction(data_root)
            return "commit_finished"
        if all_before:
            _cleanup_transaction(data_root)
            return "already_rolled_back"
        _restore_entries(data_root, journal)
        return "partial_commit_rolled_back"
    raise RuntimeError(f"unknown Tatian transaction state: {state!r}")


@contextmanager
def transaction_lock(data_root: Path) -> Iterator[None]:
    path = data_root / LOCK_RELATIVE
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("a+b") as handle:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            yield
    finally:
        path.unlink(missing_ok=True)
        _fsync_directory(path.parent)


def recover_incomplete_transaction(data_root: Path) -> str:
    with transaction_lock(data_root):
        return recover_incomplete_transaction_locked(data_root)


def commit_result_locked(
    data_root: Path, snapshot: DataSnapshot, result: RepairResult
) -> None:
    outputs = build_outputs(data_root, snapshot, result)
    if not outputs:
        return
    transaction = data_root / TRANSACTION_RELATIVE
    if transaction.exists():
        raise RuntimeError("unrecovered Tatian transaction exists")
    transaction.mkdir(parents=True)
    backup_dir = transaction / "backup"
    stage_dir = transaction / "stage"
    backup_dir.mkdir()
    stage_dir.mkdir()
    _fsync_directory(transaction.parent)
    entries: list[dict[str, Any]] = []
    try:
        for index, (target, payload) in enumerate(
            sorted(outputs.items(), key=lambda item: str(item[0]))
        ):
            relative = str(target.resolve().relative_to(data_root.resolve()))
            _safe_target(data_root, relative)
            before = _optional_read(target)
            backup_rel: str | None = None
            if before is not None:
                backup = backup_dir / f"{index:02d}.before"
                _write_fsynced(backup, before)
                backup_rel = str(backup.relative_to(transaction))
            staged = stage_dir / f"{index:02d}.after"
            _write_fsynced(staged, payload)
            entries.append(
                {
                    "target": relative,
                    "before_sha256": sha256_bytes(before) if before is not None else None,
                    "after_sha256": sha256_bytes(payload),
                    "backup": backup_rel,
                    "stage": str(staged.relative_to(transaction)),
                }
            )
        journal = {
            "transaction_id": STAMP,
            "state": "prepared",
            "created_at": "2026-08-24T09:00:00Z",
            "entries": entries,
            "committed_targets": [],
        }
        _write_journal(_journal_path(data_root), journal)
        _verify_snapshot_a(data_root, snapshot)
        journal["state"] = "committing"
        _write_journal(_journal_path(data_root), journal)
        for entry in entries:
            if not _entry_matches(data_root, entry, "before"):
                raise RuntimeError(
                    f"Tatian target drift immediately before replace: {entry['target']}"
                )
            staged = transaction / str(entry["stage"])
            target = _safe_target(data_root, str(entry["target"]))
            _replace_staged_file(staged, target)
            journal["committed_targets"].append(entry["target"])
            _write_journal(_journal_path(data_root), journal)
        if not all(_entry_matches(data_root, entry, "after") for entry in entries):
            raise RuntimeError("Tatian post-commit hash verification failed")
        journal["state"] = "committed"
        _write_journal(_journal_path(data_root), journal)
        _cleanup_transaction(data_root)
    except Exception:
        journal_path = _journal_path(data_root)
        if journal_path.exists():
            _restore_entries(
                data_root, json.loads(journal_path.read_text(encoding="utf-8"))
            )
        else:
            _cleanup_transaction(data_root)
        raise


def write_result(data_root: Path, snapshot: DataSnapshot, result: RepairResult) -> None:
    with transaction_lock(data_root):
        recovery = recover_incomplete_transaction_locked(data_root)
        if recovery != "none":
            raise RuntimeError("recovered prior Tatian transaction; reload snapshot A")
        commit_result_locked(data_root, snapshot, result)


def validate_existing_artifacts(snapshot: DataSnapshot) -> None:
    report_raw = snapshot.optional_artifacts[REPORT_RELATIVE]
    quarantine_raw = snapshot.optional_artifacts[QUARANTINE_RELATIVE]
    if report_raw is None or quarantine_raw is None:
        raise RuntimeError("applied Tatian repair lacks audit artifacts")
    report = json.loads(report_raw.decode("utf-8"))
    if report.get("stamp") != STAMP or report.get("validation", {}).get(
        "full_chapters"
    ) != 3:
        raise RuntimeError("applied Tatian report drift")
    if not rows_from_bytes(quarantine_raw):
        raise RuntimeError("applied Tatian quarantine is empty")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--data-root", type=Path, default=DEFAULT_DATA_ROOT)
    parser.add_argument("--authority-fixture", type=Path, default=DEFAULT_AUTHORITY)
    parser.add_argument("--authority-xml", type=Path)
    parser.add_argument(
        "--production-write-approved",
        action="store_true",
        help="required with --write against the repository data root",
    )
    args = parser.parse_args(argv)
    if args.write and args.dry_run:
        parser.error("--write and --dry-run are mutually exclusive")
    data_root = args.data_root.expanduser().resolve()
    if (
        args.write
        and data_root == DEFAULT_DATA_ROOT.resolve()
        and not args.production_write_approved
    ):
        parser.error("production Tatian write requires explicit root approval")
    if not args.write and (data_root / TRANSACTION_RELATIVE).exists():
        raise RuntimeError("dry-run will not mutate an incomplete Tatian transaction")

    authority = load_authority(args.authority_fixture, args.authority_xml)
    if args.write:
        with transaction_lock(data_root):
            recovery = recover_incomplete_transaction_locked(data_root)
            snapshot = load_data_snapshot(data_root)
            result = transform(snapshot, authority)
            if result.changes:
                commit_result_locked(data_root, snapshot, result)
        if recovery != "none":
            print("recovery:", recovery)
    else:
        snapshot = load_data_snapshot(data_root)
        result = transform(snapshot, authority)

    print("Tatian Oratio ad Graecos P0 repair")
    print("mode:", "WRITE" if args.write else "DRY-RUN")
    print("state:", result.mode)
    print("authority:", authority.mode)
    print("changes:", canonical_json(dict(sorted(result.changes.items()))))
    print("quarantine records:", len(result.quarantine))
    print("validation:", canonical_json(result.validation))
    if not args.write:
        print("dry-run: nothing written")
        return 0
    if not result.changes:
        validate_existing_artifacts(snapshot)
        print("already applied: no files written")
    else:
        print("transaction committed locally; no deployment")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
