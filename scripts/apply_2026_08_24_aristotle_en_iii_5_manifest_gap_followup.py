#!/usr/bin/env python3
"""Close the EN III.5 1113b7-8 manifestation gap without widening text scope.

The first 2026-08-24 locus repair made the Greek and Bobzien English passages
exact and bijective, but left the verified English UUID inside a heterogeneous
17-row legacy slug that had no corpus-manifest row. This follow-up splits the
one verified Bobzien excerpt into its own manifestation and registers the other
16 English research records as unresolved, discovery-only, and non-citable.

Only the two exact 1113b7-8 corpus rows and the paired English KG node are
enriched. Their text, UUID, reference, CTS locus, and sequence are immutable.
No edition-level CTS URN, source artifact fingerprint, open licence, or
republication permission is inferred.

Dry-run is the default and does not write. Writes use a stable snapshot A,
fsynced stages and backups, a durable transaction journal, hard-crash recovery,
and record-level preconditions. Production writes additionally require the
explicit ``--production-write-approved`` flag.
"""

from __future__ import annotations

import argparse
import copy
import fcntl
import hashlib
import importlib.util
import json
import os
import shutil
import sys
import tempfile
import unicodedata
from collections import Counter
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_ROOT = ROOT / "data"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
GRAPHRAG_SRC = ROOT / "graphrag" / "src"
if str(GRAPHRAG_SRC) not in sys.path:
    sys.path.insert(0, str(GRAPHRAG_SRC))

STAMP = "aristotle_en_iii_5_manifest_gap_followup_2026_08_24"
LEGACY_LOCUS_STAMP = "aristotle_en_iii_5_locus_repair_2026_08_24"
UPDATED_AT = "2026-08-24 06:00:00+00:00"

GREEK_NODE_1113 = "passage_aristotle_en_iii_5_1113b7"
ENGLISH_NODE_1113 = "passage_aristotle_en_iii_5_1113b7_en"
GREEK_NODE_1114 = "passage_aristotle_en_iii_5_1114b1"
ENGLISH_NODE_1114 = "passage_aristotle_en_iii_5_1114b1_en"
PUBLICATION_NODE = "pub_bobzien_2013_found_in_translation"

PASSAGE_1113_GRC = "1e336c5e-391c-5613-a59d-b83d2bcc5523"
PASSAGE_1113_ENG = "88ac0d42-994e-5dee-9df0-7069da06cc60"
PASSAGE_1114_GRC = "28b16b62-34cb-4db0-a445-c778d696cb4e"
PASSAGE_1114_ENG = "1da67f00-a117-5916-94e8-0238afb57bfb"

REF_1113_GRC = "EN III.5, 1113b7-8 (ἐφ’ ἡμῖν)"
REF_1113_ENG = "EN III.5, 1113b7-8 (ἐφ’ ἡμῖν) (English)"
URN_III_5 = "urn:cts:greekLit:tlg0086.tlg010:3.5"
WORK_URN = "urn:cts:greekLit:tlg0086.tlg010"
KG_WORK_CANONICAL_ID = "oga:tlg0086.tlg010.perseus-grc2"

GREEK_MANIFEST_ID = "oga_tlg0086_tlg010_perseus_grc2_grc"
LEGACY_ENGLISH_MANIFEST_ID = "oga_tlg0086_tlg010_perseus_grc2_eng"
BOBZIEN_MANIFEST_ID = "aristotle_en_iii5_1113b7_8_bobzien2013_eng"

LEGACY_ENGLISH_PASSAGE_IDS = (
    "1da67f00-a117-5916-94e8-0238afb57bfb",
    "2624d01b-9c90-5c8e-83e0-9f971c3d8a1d",
    "275806ac-fb76-5337-a9bd-645d42abb936",
    "4754455c-5b83-512a-8801-6fb8c3e392e2",
    "4ab60f2c-e933-5e1c-ad40-93ce3a11af6c",
    "5dc946fb-4834-50ba-91d4-a4d8bfa2b762",
    "6cdfce83-dd68-57a2-8ee6-f1a8f0a6e7fe",
    "85f47628-9274-5e5c-9e47-8bbd0da45cb5",
    "8de4e65b-f1ab-5b9b-b6dc-bccf3ecea55d",
    "93b96f9d-6c8a-5c3b-bc68-0d1231ba11a6",
    "9c4192f5-4afa-5538-9742-b82055fd6a57",
    "a51e9324-ba0f-528b-ab33-f975ab7839ce",
    "de9a9a3a-33dd-5705-88cb-f3d1525362a3",
    "e3215c66-9598-5679-868b-22318a0c6e62",
    "fc58cfb9-7a6e-5e6f-a766-b775a6256ba8",
    "fe098e5c-6727-5cee-8ff0-31a16392e489",
)
LEGACY_ENGLISH_NODE_IDS = (
    "passage_arist_en_3_10_en",
    "passage_arist_en_3_11_en",
    "passage_arist_en_3_12_en",
    "passage_arist_en_3_1_en",
    "passage_arist_en_3_2_en",
    "passage_arist_en_3_3_en",
    "passage_arist_en_3_4_en",
    "passage_arist_en_3_6_en",
    "passage_arist_en_3_7_en",
    "passage_arist_en_3_8_en",
    "passage_arist_en_3_9_en",
    "passage_aristotle_en_iii_1_1110a4_en",
    "passage_aristotle_en_iii_1_1111a22_en",
    "passage_aristotle_en_iii_3_1112a15_en",
    "passage_aristotle_en_iii_3_1112b11_en",
    "passage_aristotle_en_iii_5_1114b1_en",
)
LEGACY_PASSAGES_BEFORE_DIGEST = (
    "1886380348fde09a0d826c2c9b18013abf0611192654a4af647702a624780fad"
)
LEGACY_NODES_BEFORE_DIGEST = (
    "30af8f3ca168e00de40c2b32b5b0619e7fb347fbddff4d38d30e71d425761741"
)

ANCIENT_SOURCE_ID = "src_anc_aristotle_nicomachean_ethics"
BOBZIEN_SOURCE_ID = "src_sec_bobzien_2013_found_translation"
ANCIENT_EVIDENCE_ID = "ev_anc_aristotle_en_iii5_1113b7_8_repair"
BOBZIEN_EVIDENCE_ID = "ev_sec_bobzien_translation_pp103_115"
RESOLVED_ISSUE_ID = "issue_aristotle_en_1113b7_shared_uuid_contamination"
LEGACY_ISSUE_ID = "issue_aristotle_en_book3_legacy_english_identity_unresolved"
WAVE_00 = "wave_00_known_factual_blockers"
WAVE_01 = "wave_01_pdf_priority_new_knowledge"

DOI = "10.1093/acprof:oso/9780199679430.003.0004"
PUBLICATION_LABEL = (
    "Susanne Bobzien, ‘Found in Translation: Aristotle’s Nicomachean Ethics "
    "3.5, 1113b7–8, and Its Reception’, Oxford Studies in Ancient Philosophy "
    "45 (2013), 103–148, translation (I)"
)
RIGHTS_CAVEAT = (
    "Copyrighted scholarly excerpt; no open licence, artifact-level licence, "
    "or republication permission is asserted or inferred."
)
NO_ARTIFACT = "source_artifact_not_registered_no_fingerprint_inferred"

GREEK_1113 = (
    "ἐν οἷς γὰρ ἐφ’ ἡμῖν τὸ πράττειν, καὶ τὸ μὴ πράττειν, "
    "καὶ ἐν οἷς τὸ μή, καὶ τὸ ναί·"
)
ENGLISH_1113 = (
    "For, where to act is up to us, also to not act is up to us, and where "
    "to not act is up to us, also to act is up to us."
)

QUARANTINE_RELATIVE = Path(
    "audit/2026-08-24_aristotle_en_iii_5_manifest_gap_quarantine.jsonl"
)
REPORT_RELATIVE = Path(
    "audit/2026-08-24_aristotle_en_iii_5_manifest_gap_repair.json"
)
TRANSACTION_RELATIVE = Path("audit/.aristotle_en_iii_5_manifest_gap_transaction")
LOCK_RELATIVE = Path("audit/.aristotle_en_iii_5_manifest_gap.lock")

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
    "registry_verifications": Path(
        "goals/sota/registry/verifications/wave00_aristotle_bobzien_20260824.jsonl"
    ),
    "publications_bib": Path("kg/publications.bib"),
}

MUTABLE_LABELS = (
    "nodes",
    "passages",
    "manifest",
    "registry_sources",
    "registry_evidence",
    "registry_issues",
    "registry_waves",
    "registry_verifications",
)

EXPECTED_BEFORE_RECORD_HASHES = {
    ("passage_id", PASSAGE_1113_GRC): (
        "37baaf4104b82ab703fad3d9fc5c78cac387d36f24d94c15e700fe3af77b59eb"
    ),
    ("passage_id", PASSAGE_1113_ENG): (
        "02399ef4399bf0685a25a5d65ff32bbd8d2973318827c98b3b7a337322fe9f0c"
    ),
    ("canonical_id", GREEK_MANIFEST_ID): (
        "c33bdfeaf4af2a05e8857a1faf50814efc07671a370cb30e7a42e016c0f7ef1f"
    ),
    ("node_id", ENGLISH_NODE_1113): (
        "be5b3bca473ed192d2f896aa00db26a6e41abf02e124d7ab505ded186af38174"
    ),
    ("source_id", ANCIENT_SOURCE_ID): (
        "7c2e5699059d873e3324c67e6bb5743d0b056ddfd7e180ba817663116291134d"
    ),
    ("source_id", BOBZIEN_SOURCE_ID): (
        "d6a796bab97ff4449fd1cd98791187574cfdb5ad1bc295b5bb80ead1adb13dc5"
    ),
    ("evidence_id", ANCIENT_EVIDENCE_ID): (
        "0856b2a9876869c35feca93cffbe26478e8539752989ec8eb9a8b098e72af69b"
    ),
    ("evidence_id", BOBZIEN_EVIDENCE_ID): (
        "ad22dba29533411a555450573a388a0c7e3e8edcce2534427f6000f5e239084e"
    ),
    ("issue_id", RESOLVED_ISSUE_ID): (
        "acef8c8d041a3956920373dafadd85fc2b084dda38b5976e101c94fb67f1c46e"
    ),
    ("wave_id", WAVE_00): (
        "cf0c67b6216c444e6d937801e7d1d7e347e22c30990e2d2f3f714e5955a3f46b"
    ),
    ("wave_id", WAVE_01): (
        "5422733b2e2469e7f9a87ed6d99d71518e468121cbb17a57378448a56ede4c19"
    ),
}

NEW_VERIFICATIONS = (
    {
        "record_type": "verification",
        "verification_id": "ver_bobzien_2013_manifest_identity_20260824",
        "target_type": "source",
        "target_id": BOBZIEN_SOURCE_ID,
        "stage": "identity",
        "verifier": {
            "verifier_id": "bobzien_doi_publication_node_audit",
            "kind": "agent",
            "independence_group": "publisher_bibliography_manifest_split_20260824",
        },
        "method": (
            "Cross-check the DOI, publication node, bibliography entry, exact "
            "translation label and passage-scoped manifestation identity."
        ),
        "checked_locators": [
            "data/kg/nodes.jsonl",
            "data/kg/publications.bib",
            str(REPORT_RELATIVE).replace("audit/", "data/audit/"),
        ],
        "verdict": "pass",
        "created_at": "2026-08-24T06:01:00Z",
        "artifacts": [
            {
                "locator": str(REPORT_RELATIVE).replace("audit/", "data/audit/"),
                "role": "audit_report",
            }
        ],
        "notes": (
            "Identity verification is bibliographic and passage-scoped; no full "
            "article artifact or open licence was inferred."
        ),
    },
    {
        "record_type": "verification",
        "verification_id": "ver_bobzien_2013_translation_primary_20260824",
        "target_type": "evidence",
        "target_id": BOBZIEN_EVIDENCE_ID,
        "stage": "primary",
        "verifier": {
            "verifier_id": "bobzien_translation_i_source_collation",
            "kind": "agent",
            "independence_group": "source_excerpt_and_locus_collation_20260824",
        },
        "method": (
            "Collate translation (I), its exact English text hash, Aristotle "
            "1113b7-8 and the separately registered Greek corpus UUID."
        ),
        "checked_locators": [
            "data/corpus/passages.jsonl",
            "data/kg/nodes.jsonl",
            "data/kg/publications.bib",
        ],
        "verdict": "pass",
        "created_at": "2026-08-24T06:02:00Z",
        "artifacts": [
            {"locator": "data/corpus/passages.jsonl", "role": "catalog_record"}
        ],
        "notes": "The verified unit is the short translation (I) excerpt only.",
    },
    {
        "record_type": "verification",
        "verification_id": "ver_bobzien_2013_translation_adversarial_20260824",
        "target_type": "evidence",
        "target_id": BOBZIEN_EVIDENCE_ID,
        "stage": "adversarial",
        "verifier": {
            "verifier_id": "aristotle_manifest_gap_regression_gate",
            "kind": "deterministic_tool",
            "independence_group": "split_rights_cts_transaction_eval_gate_20260824",
        },
        "method": (
            "Reject heterogeneous Bobzien attribution, invented edition CTS, "
            "artifact or licence inference, target-field mutation, snapshot drift, "
            "partial commits, non-idempotence, and strict eval-admission failure."
        ),
        "checked_locators": [
            "tests/test_aristotle_en_iii_5_manifest_gap_followup.py",
            "scripts/apply_2026_08_24_aristotle_en_iii_5_manifest_gap_followup.py",
        ],
        "verdict": "pass",
        "created_at": "2026-08-24T06:04:00Z",
        "artifacts": [
            {
                "locator": "tests/test_aristotle_en_iii_5_manifest_gap_followup.py",
                "role": "test_report",
            }
        ],
        "notes": "The deterministic suite proves exactly one Bobzien row and sixteen unresolved rows.",
    },
    {
        "record_type": "verification",
        "verification_id": "ver_aristotle_legacy_english_issue_primary_20260824",
        "target_type": "issue",
        "target_id": LEGACY_ISSUE_ID,
        "stage": "primary",
        "verifier": {
            "verifier_id": "eval_manifest_gap_cohort_audit",
            "kind": "agent",
            "independence_group": "full_slug_membership_and_source_scope_20260824",
        },
        "method": (
            "Enumerate every corpus row under the legacy English slug and compare "
            "its source identity with the one verified Bobzien translation."
        ),
        "checked_locators": [
            "data/corpus/passages.jsonl",
            "data/corpus/manifest.jsonl",
            str(REPORT_RELATIVE).replace("audit/", "data/audit/"),
        ],
        "verdict": "supports_issue",
        "created_at": "2026-08-24T06:05:00Z",
        "artifacts": [
            {
                "locator": str(REPORT_RELATIVE).replace("audit/", "data/audit/"),
                "role": "audit_report",
            }
        ],
        "notes": "Sixteen source-unresolved English research records remain open debt and non-citable.",
    },
    {
        "record_type": "verification",
        "verification_id": "ver_aristotle_1113_manifest_followup_regression_20260824",
        "target_type": "issue",
        "target_id": RESOLVED_ISSUE_ID,
        "stage": "regression",
        "verifier": {
            "verifier_id": "aristotle_resolved_issue_followup_gate",
            "kind": "deterministic_tool",
            "independence_group": "resolved_locus_manifest_regression_20260824",
        },
        "method": (
            "Re-run exact-text, bijective snapshot, manifestation split, registry "
            "and strict eval-admission checks without reopening the repaired locus."
        ),
        "checked_locators": [
            "tests/test_aristotle_en_iii_5_manifest_gap_followup.py",
            str(REPORT_RELATIVE).replace("audit/", "data/audit/"),
        ],
        "verdict": "pass",
        "created_at": "2026-08-24T06:06:00Z",
        "artifacts": [
            {
                "locator": "tests/test_aristotle_en_iii_5_manifest_gap_followup.py",
                "role": "test_report",
            }
        ],
        "notes": "The locus repair remains resolved; the separate legacy-16 identity issue stays open.",
    },
)


@dataclass(frozen=True)
class DataSnapshot:
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


def nfc(value: str) -> str:
    return unicodedata.normalize("NFC", value)


def text_hash(value: str) -> str:
    return hashlib.sha256(nfc(value).encode("utf-8")).hexdigest()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


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


def node_id(node: dict[str, Any]) -> str:
    return str(node.get("node_id") or node.get("id") or "")


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


def require_unique(
    rows: list[dict[str, Any]], field: str, wanted: str
) -> dict[str, Any]:
    matches = [row for row in rows if str(row.get(field) or "") == wanted]
    if len(matches) != 1:
        raise RuntimeError(f"expected one {field}={wanted!r}; found {len(matches)}")
    return matches[0]


def require_node(nodes: list[dict[str, Any]], wanted: str) -> dict[str, Any]:
    matches = [row for row in nodes if node_id(row) == wanted]
    if len(matches) != 1:
        raise RuntimeError(f"expected one node {wanted!r}; found {len(matches)}")
    return matches[0]


def append_unique(values: list[Any], value: Any) -> list[Any]:
    output = copy.deepcopy(values)
    if value not in output:
        output.append(copy.deepcopy(value))
    return output


def _provenance_entry(locator: str, role: str) -> dict[str, str]:
    return {"locator": locator, "role": role}


def desired_greek_passage(row: dict[str, Any]) -> dict[str, Any]:
    wanted = copy.deepcopy(row)
    wanted.update(
        {
            "citability": "citable",
            "language": "grc",
            "manifestation_id": GREEK_MANIFEST_ID,
            "passage_role": "original",
            "text_sha256_nfc": text_hash(GREEK_1113),
            "work_urn": WORK_URN,
            "provenance": {
                "artifact_status": NO_ARTIFACT,
                "edition_statement": "Bywater (OCT), as declared by the paired KG node",
                "kg_node_id": GREEK_NODE_1113,
                "registry_evidence_id": ANCIENT_EVIDENCE_ID,
                "registry_source_id": ANCIENT_SOURCE_ID,
                "source_kind": "published_critical_text",
            },
        }
    )
    return wanted


def desired_english_passage(row: dict[str, Any]) -> dict[str, Any]:
    wanted = copy.deepcopy(row)
    wanted.update(
        {
            "aligned_to_manifestation": GREEK_MANIFEST_ID,
            "citability": "citable",
            "language": "eng",
            "manifestation_id": BOBZIEN_MANIFEST_ID,
            "passage_role": "translation",
            "rights": RIGHTS_CAVEAT,
            "source_artifact_status": NO_ARTIFACT,
            "source_doi": DOI,
            "source_language": "grc",
            "source_passage_id": PASSAGE_1113_GRC,
            "source_publication_id": PUBLICATION_NODE,
            "text_sha256_nfc": text_hash(ENGLISH_1113),
            "translation_label": "translation (I)",
            "translation_of_work": WORK_URN,
            "translation_source": PUBLICATION_LABEL,
            "translation_type": "published_scholarly_translation",
            "translator": "Susanne Bobzien",
            "work_canonical_id": BOBZIEN_MANIFEST_ID,
            "work_urn": WORK_URN,
            "provenance": {
                "artifact_status": NO_ARTIFACT,
                "kg_node_id": ENGLISH_NODE_1113,
                "publication_node_id": PUBLICATION_NODE,
                "registry_evidence_id": BOBZIEN_EVIDENCE_ID,
                "registry_source_id": BOBZIEN_SOURCE_ID,
                "translation_label": "translation (I)",
            },
        }
    )
    return wanted


def desired_legacy_passage(row: dict[str, Any]) -> dict[str, Any]:
    wanted = copy.deepcopy(row)
    wanted.update(
        {
            "citability": "discoverable_only",
            "identity_status": "source_identity_unresolved",
            "language": "eng",
            "manifestation_id": LEGACY_ENGLISH_MANIFEST_ID,
            "passage_role": "unresolved_english_research_record",
        }
    )
    return wanted


def desired_legacy_node(row: dict[str, Any]) -> dict[str, Any]:
    wanted = copy.deepcopy(row)
    wanted["updated_at"] = UPDATED_AT
    data = metadata(wanted)
    data.update(
        {
            STAMP: True,
            f"{STAMP}_status": "legacy_source_identity_unresolved",
            "citability": "discoverable_only",
            "identity_status": "source_identity_unresolved",
            "language": "eng",
            "manifestation_id": LEGACY_ENGLISH_MANIFEST_ID,
            "passage_role": "unresolved_english_research_record",
        }
    )
    set_metadata(wanted, data)
    return wanted


def cohort_digest(rows: list[dict[str, Any]]) -> str:
    payload = "\n".join(canonical_json(row) for row in rows)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def load_citability_policy() -> tuple[Any, Any]:
    """Load the real central policy without importing optional GraphRAG runtime."""

    module_name = "_eleutheria_aristotle_repair_citability"
    module = sys.modules.get(module_name)
    if module is None:
        path = GRAPHRAG_SRC / "eleutheria_graphrag" / "agents" / "citability.py"
        spec = importlib.util.spec_from_file_location(module_name, path)
        if spec is None or spec.loader is None:
            raise RuntimeError("cannot load central citability policy")
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
    return module.CitabilityTier, module.evidence_policy


def desired_english_node(row: dict[str, Any]) -> dict[str, Any]:
    wanted = copy.deepcopy(row)
    wanted["updated_at"] = UPDATED_AT
    data = metadata(wanted)
    data.pop("edition", None)
    data.update(
        {
            STAMP: True,
            f"{STAMP}_status": "exact_bobzien_manifestation_split",
            "aligned_to_manifestation": GREEK_MANIFEST_ID,
            "citability": "citable",
            "edition_identity_status": (
                "underlying_work_cts_only_no_edition_urn_asserted"
            ),
            "intellectual_work_cts_urn": WORK_URN,
            "manifestation_id": BOBZIEN_MANIFEST_ID,
            "rights": RIGHTS_CAVEAT,
            "source_artifact_status": NO_ARTIFACT,
            "source_corpus_passage_id": PASSAGE_1113_GRC,
            "source_publication_id": PUBLICATION_NODE,
            "translation_label": "translation (I)",
            "translation_of_work": WORK_URN,
            "work_canonical_id": KG_WORK_CANONICAL_ID,
        }
    )
    set_metadata(wanted, data)
    return wanted


def desired_greek_manifest(row: dict[str, Any]) -> dict[str, Any]:
    wanted = copy.deepcopy(row)
    wanted.update(
        {
            "artifact_status": NO_ARTIFACT,
            "language": "grc",
            "passage_role": "original",
            "passages": 117,
            "work_urn": WORK_URN,
        }
    )
    return wanted


def desired_bobzien_manifest() -> dict[str, Any]:
    return {
        "aligned_to_manifestation": GREEK_MANIFEST_ID,
        "artifact_status": NO_ARTIFACT,
        "author": "Aristotle",
        "canonical_id": BOBZIEN_MANIFEST_ID,
        "cts_urn": WORK_URN,
        "doi": DOI,
        "edition_status": "no_edition_level_cts_identifier_asserted",
        "ingest_class": "manual_published_translation_excerpt",
        "language": "eng",
        "license": "none_asserted_do_not_infer",
        "passage_ids": [PASSAGE_1113_ENG],
        "passage_role": "translation",
        "passages": 1,
        "period": "Classical Greek",
        "rights": RIGHTS_CAVEAT,
        "source": f"https://doi.org/{DOI}",
        "source_language": "grc",
        "source_publication_id": PUBLICATION_NODE,
        "status": "in_corpus",
        "title": "Nicomachean Ethics III.5, 1113b7-8 — Bobzien translation (I)",
        "translation_label": "translation (I)",
        "translation_of_work": WORK_URN,
        "translation_type": "published_scholarly_translation",
        "translator": "Susanne Bobzien",
        "work_urn": WORK_URN,
    }


def desired_legacy_manifest(legacy_ids: list[str]) -> dict[str, Any]:
    return {
        "artifact_status": "unknown_not_registered",
        "author": "Aristotle (aboutness only; record provenance unresolved)",
        "canonical_id": LEGACY_ENGLISH_MANIFEST_ID,
        "citable": False,
        "cts_urn": WORK_URN,
        "identity_note": (
            "These sixteen legacy English research records are not attributed "
            "to Susanne Bobzien or to a named published translation."
        ),
        "ingest_class": "discovery_only",
        "language": "eng",
        "license": "unknown_not_inferred",
        "passage_ids": legacy_ids,
        "passage_role": "unresolved_english_research_record",
        "passages": 16,
        "period": "Classical Greek",
        "source": "",
        "status": "identity_unresolved_non_citable",
        "title": "Nicomachean Ethics III — unresolved legacy English research cohort",
        "translator": "unknown_not_established",
        "work_urn": WORK_URN,
    }


def desired_ancient_source(row: dict[str, Any]) -> dict[str, Any]:
    wanted = copy.deepcopy(row)
    coverage = copy.deepcopy(wanted["coverage"])
    coverage["state"] = "partial"
    coverage["kg_node_ids"] = append_unique(
        coverage.get("kg_node_ids", []), GREEK_NODE_1113
    )
    coverage["corpus_manifestation_ids"] = [GREEK_MANIFEST_ID]
    coverage["corpus_passage_ids"] = [PASSAGE_1113_GRC]
    coverage["basis"] = (
        "The work node and the exact Greek 1113b7-8 locus are registered, but "
        "claim-level and edition-artifact completeness has not been demonstrated."
    )
    coverage["last_audited"] = "2026-08-24"
    wanted["coverage"] = coverage
    wanted["provenance"] = append_unique(
        wanted["provenance"],
        _provenance_entry(
            "data/audit/2026-08-24_aristotle_en_iii_5_manifest_gap_repair.json",
            "audit_report",
        ),
    )
    wanted["notes"] = (
        "Abstract ancient work. The exact 1113b7-8 Greek row has a text hash, "
        "but no source artifact fingerprint is registered or inferred."
    )
    return wanted


def desired_bobzien_source(row: dict[str, Any]) -> dict[str, Any]:
    wanted = copy.deepcopy(row)
    coverage = copy.deepcopy(wanted["coverage"])
    coverage["state"] = "partial"
    coverage["kg_node_ids"] = append_unique(
        coverage.get("kg_node_ids", []), ENGLISH_NODE_1113
    )
    coverage["corpus_manifestation_ids"] = [BOBZIEN_MANIFEST_ID]
    coverage["corpus_passage_ids"] = [PASSAGE_1113_ENG]
    coverage["basis"] = (
        "Bibliographic identity and the short translation (I) at EN III.5 "
        "1113b7-8 are verified and registered as one passage-scoped manifestation. "
        "The full article artifact, printed-to-PDF page map, and atomic reception-"
        "history coverage remain incomplete."
    )
    coverage["last_audited"] = "2026-08-24"
    wanted["coverage"] = coverage
    wanted["provenance"] = append_unique(
        wanted["provenance"],
        _provenance_entry(
            "data/audit/2026-08-24_aristotle_en_iii_5_manifest_gap_repair.json",
            "audit_report",
        ),
    )
    wanted["notes"] = (
        "Distinct from Bobzien's 2014 chapters. Only corpus UUID "
        f"{PASSAGE_1113_ENG} is attributed to the 2013 translation (I). "
        f"{RIGHTS_CAVEAT}"
    )
    return wanted


def desired_ancient_evidence(row: dict[str, Any]) -> dict[str, Any]:
    wanted = copy.deepcopy(row)
    wanted["translation_alignment"] = {
        "aligned_to_manifestation": GREEK_MANIFEST_ID,
        "english_corpus_passage_id": PASSAGE_1113_ENG,
        "english_manifestation_id": BOBZIEN_MANIFEST_ID,
        "english_text_sha256_nfc": text_hash(ENGLISH_1113),
        "publication_node_id": PUBLICATION_NODE,
        "rights": RIGHTS_CAVEAT,
        "source_evidence_id": BOBZIEN_EVIDENCE_ID,
        "translation_label": "translation (I)",
        "translator": "Susanne Bobzien",
    }
    wanted["notes"] = (
        "The Greek and Bobzien English UUIDs are distinct and aligned. The "
        "translation has its own one-passage manifestation; sixteen unrelated "
        "legacy English research rows are excluded from that attribution."
    )
    return wanted


def desired_bobzien_evidence(row: dict[str, Any]) -> dict[str, Any]:
    wanted = copy.deepcopy(row)
    wanted.update(
        {
            "attestation": "direct_translation",
            "claim_status": "in_review",
            "claim_text": (
                "Bobzien's translation (I) renders EN III.5, 1113b7-8 as a "
                "vice-versa relation between acting and not acting being up to us."
            ),
            "kg_targets": [
                ENGLISH_NODE_1113,
                "argument_bobzien_2013_1113b7_8_vice_versa_translation",
            ],
            "locator": {
                "article_pages": {"start": 103, "end": 148},
                "canonical_locus": "Nicomachean Ethics III.5, 1113b7-8",
                "page_map_status": "unmapped",
                "printed_pages": {"start": 103, "end": 115},
                "translation_label": "translation (I)",
            },
            "quotation": {
                "corpus_passage_ids": [PASSAGE_1113_ENG],
                "language": "eng",
                "rights": RIGHTS_CAVEAT,
                "status": "exact_short_translation_text_verified",
                "text_sha256": text_hash(ENGLISH_1113),
            },
            "review_state": {
                "exact_short_text": "verified",
                "publication_identity": "verified",
                "source_label": "translation (I) verified",
                "independent_review": "pending_root_review",
                "printed_page_concordance": "pending",
                "full_artifact": "missing",
            },
            "notes": (
                "The translation label and exact short text are verified; no "
                "exact printed-to-PDF page concordance, full artifact fingerprint, "
                "open licence, or broader article-completeness claim is made."
            ),
        }
    )
    return wanted


def desired_resolved_issue(row: dict[str, Any]) -> dict[str, Any]:
    wanted = copy.deepcopy(row)
    wanted["affected_ids"] = append_unique(
        append_unique(wanted.get("affected_ids", []), BOBZIEN_SOURCE_ID),
        LEGACY_ISSUE_ID,
    )
    wanted["affected_count"] = len(wanted["affected_ids"])
    wanted["evidence_artifacts"] = append_unique(
        append_unique(
            wanted["evidence_artifacts"],
            {
                "locator": "data/audit/2026-08-24_aristotle_en_iii_5_manifest_gap_repair.json",
                "role": "audit_report",
            },
        ),
        {
            "locator": "data/audit/2026-08-24_aristotle_en_iii_5_manifest_gap_quarantine.jsonl",
            "role": "audit_report",
        },
    )
    followup = {
        "followup_id": "followup_aristotle_1113b7_manifest_gap_20260824",
        "discovered_by": "strict eval gold manifestation admission",
        "discovery": (
            "The exact Bobzien English UUID still shared an unmanifested, "
            "heterogeneous 17-row legacy slug after the locus repair."
        ),
        "opened_issue_id": LEGACY_ISSUE_ID,
        "bobzien_manifestation_id": BOBZIEN_MANIFEST_ID,
        "legacy_manifestation_id": LEGACY_ENGLISH_MANIFEST_ID,
        "resolution": (
            "Split the verified Bobzien row into a one-passage manifestation, "
            "register the other sixteen as unresolved/non-citable, and preserve "
            "all text, UUID, reference, CTS locus, and sequence values."
        ),
        "resolved_at": "2026-08-24T06:00:00Z",
        "status": "resolved_with_separate_legacy_issue_open",
    }
    existing = [
        item
        for item in wanted.get("followups", [])
        if item.get("followup_id") != followup["followup_id"]
    ]
    wanted["followups"] = [*existing, followup]
    wanted["resolution_criteria"] = (
        "Maintain one-to-one snapshots for 1113b7-8 and 1114b1-12; preserve "
        "the exact texts and hashes; keep the Bobzien translation in its own "
        "manifestation; never attribute the unresolved legacy-16 cohort to Bobzien."
    )
    return wanted


def desired_legacy_issue(legacy_ids: list[str]) -> dict[str, Any]:
    return {
        "record_type": "issue",
        "issue_id": LEGACY_ISSUE_ID,
        "issue_type": "provenance_gap",
        "severity": "high",
        "factual_risk": True,
        "status": "open",
        "summary": (
            "Sixteen legacy English Nicomachean Ethics III research records have "
            "no established translator, source publication, licence, or coherent "
            "translation manifestation identity. They are discovery-only and non-citable."
        ),
        "affected_ids": [ANCIENT_SOURCE_ID, *LEGACY_ENGLISH_NODE_IDS],
        "affected_corpus_ids": [LEGACY_ENGLISH_MANIFEST_ID, *legacy_ids],
        "affected_count": 17,
        "affected_id_count": 17,
        "affected_record_count": 16,
        "affected_count_note": (
            "Seventeen identifiers comprise one manifestation identifier plus "
            "sixteen corpus passage UUIDs; the affected corpus-record count is sixteen."
        ),
        "evidence_artifacts": [
            {"locator": "data/corpus/passages.jsonl", "role": "catalog_record"},
            {"locator": "data/corpus/manifest.jsonl", "role": "catalog_record"},
            {
                "locator": "data/audit/2026-08-24_aristotle_en_iii_5_manifest_gap_repair.json",
                "role": "audit_report",
            },
        ],
        "resolution_criteria": (
            "Adjudicate each of the sixteen rows against a named source; assign "
            "source-specific manifestations or quarantine it; establish rights and "
            "artifact provenance without inference; retain non-citability until complete."
        ),
    }


def desired_wave_00(row: dict[str, Any]) -> dict[str, Any]:
    wanted = copy.deepcopy(row)
    wanted["source_ids"] = append_unique(wanted["source_ids"], BOBZIEN_SOURCE_ID)
    wanted["evidence_ids"] = append_unique(wanted["evidence_ids"], BOBZIEN_EVIDENCE_ID)
    wanted["issue_ids"] = append_unique(wanted["issue_ids"], LEGACY_ISSUE_ID)
    replacement = (
        "Aristotle EN III.5 1113b7-8 and 1114b1-12 have distinct verified corpus "
        "passages and snapshots; Bobzien translation (I) has a one-passage "
        "manifestation, while the separate legacy-16 English cohort stays "
        "non-citable pending source adjudication."
    )
    criteria = [
        value
        for value in wanted["exit_criteria"]
        if not value.startswith("Aristotle EN III.5 1113b7-8 and 1114b1-12")
    ]
    wanted["exit_criteria"] = [*criteria[:2], replacement, *criteria[2:]]
    return wanted


def desired_wave_01(row: dict[str, Any]) -> dict[str, Any]:
    wanted = copy.deepcopy(row)
    wanted["issue_ids"] = append_unique(wanted["issue_ids"], LEGACY_ISSUE_ID)
    wanted["blocked_by"] = [
        value
        for value in wanted["blocked_by"]
        if value != RESOLVED_ISSUE_ID
    ]
    wanted["blocked_by"] = append_unique(wanted["blocked_by"], LEGACY_ISSUE_ID)
    criterion = (
        "The one-passage Bobzien translation manifestation remains distinct from "
        "the unresolved legacy-16 English cohort; the split does not imply full "
        "article acquisition, page mapping, artifact fingerprinting, or open rights."
    )
    wanted["exit_criteria"] = append_unique(wanted["exit_criteria"], criterion)
    return wanted


def _quarantine_record(
    record_type: str, record: dict[str, Any], reason: str
) -> dict[str, Any]:
    return {
        "record_type": record_type,
        "reason": reason,
        "record_sha256": record_hash(record),
        "record": copy.deepcopy(record),
    }


def _replace_existing(
    rows: list[dict[str, Any]],
    *,
    field: str,
    wanted_id: str,
    builder: Callable[[dict[str, Any]], dict[str, Any]],
    quarantine_type: str,
    reason: str,
    count_key: str,
    quarantine: list[dict[str, Any]],
    changes: Counter[str],
) -> None:
    current = require_unique(rows, field, wanted_id)
    wanted = builder(current)
    if current == wanted:
        return
    expected_hash = EXPECTED_BEFORE_RECORD_HASHES[(field, wanted_id)]
    if record_hash(current) != expected_hash:
        raise RuntimeError(
            f"target record drift for {field}={wanted_id!r}; refusing partial repair"
        )
    quarantine.append(_quarantine_record(quarantine_type, current, reason))
    current.clear()
    current.update(wanted)
    changes[count_key] += 1


def _add_exact(
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
        raise RuntimeError(f"partial or conflicting new record {field}={identifier!r}")


def _immutable_tuple(row: dict[str, Any]) -> tuple[Any, ...]:
    return (
        row.get("passage_id"),
        row.get("text_content"),
        row.get("canonical_ref"),
        row.get("cts_urn"),
        row.get("sequence_number"),
    )


def _audit_authorities(nodes: list[dict[str, Any]], publications_bib: str) -> None:
    greek = require_node(nodes, GREEK_NODE_1113)
    english = require_node(nodes, ENGLISH_NODE_1113)
    publication = require_node(nodes, PUBLICATION_NODE)
    greek_data = metadata(greek)
    english_data = metadata(english)
    publication_data = metadata(publication)
    if greek.get("description") != GREEK_1113 or greek_data.get(
        "text_content_sha256_nfc"
    ) != text_hash(GREEK_1113):
        raise RuntimeError("paired Greek KG node text/hash drift")
    if english.get("description") != ENGLISH_1113 or english_data.get(
        "text_content_sha256_nfc"
    ) != text_hash(ENGLISH_1113):
        raise RuntimeError("paired English KG node text/hash drift")
    if (
        publication.get("label")
        != "Found in Translation: Aristotle’s Nicomachean Ethics 3.5, 1113b7–8, and Its Reception"
        or publication_data.get("author") != "Susanne Bobzien"
        or publication_data.get("doi") != DOI
        or publication_data.get("year") != 2013
        or publication_data.get("pages") != "103-148"
    ):
        raise RuntimeError("Bobzien publication authority facts drift")
    required_bib = (
        "@incollection{bobzien-2013-found-in-translation",
        "author = {Susanne Bobzien}",
        "pages = {103-148}",
        f"doi = {{{DOI}}}",
    )
    if any(value not in publications_bib for value in required_bib):
        raise RuntimeError("Bobzien bibliography authority entry is incomplete")


def _snapshot_target_violations(
    violations: list[dict[str, Any]], target_nodes: set[str]
) -> list[dict[str, Any]]:
    return [row for row in violations if row.get("node_id") in target_nodes]


def _validate_eval_admission(
    nodes: list[dict[str, Any]],
    passages: list[dict[str, Any]],
    manifest: list[dict[str, Any]],
) -> dict[str, Any]:
    from tests.eval.run_eval import QueryCase, validate_gold_against_snapshot

    class InMemoryCatalog:
        def __init__(self) -> None:
            self.passages = {
                str(row.get("passage_id") or ""): row for row in passages
            }
            self.manifestation_ids = {
                str(row.get("canonical_id") or "") for row in manifest
            }
            self.node_types = {
                node_id(row): str(row.get("type") or "").lower() for row in nodes
            }

        def identity(self, passage_id: str) -> dict[str, Any] | None:
            row = self.passages.get(passage_id)
            if row is None:
                return None
            return {
                "passage_id": passage_id,
                "work_canonical_id": row.get("work_canonical_id"),
                "canonical_ref": row.get("canonical_ref"),
                "cts_urn": row.get("cts_urn"),
                "language": row.get("language"),
            }

    case = QueryCase(
        id="repair_aristotle_en_1113b_manifest_split",
        query="Retrieve Aristotle EN III.5 1113b7-8 in Greek and Bobzien translation (I).",
        query_type="fact",
        difficulty="hard",
        expected_manifestations=[GREEK_MANIFEST_ID, BOBZIEN_MANIFEST_ID],
        expected_passages=[PASSAGE_1113_GRC, PASSAGE_1113_ENG],
        expected_passage_identities={
            PASSAGE_1113_GRC: {
                "work_canonical_id": GREEK_MANIFEST_ID,
                "canonical_ref": REF_1113_GRC,
                "cts_urn": URN_III_5,
                "language": "grc",
            },
            PASSAGE_1113_ENG: {
                "work_canonical_id": BOBZIEN_MANIFEST_ID,
                "canonical_ref": REF_1113_ENG,
                "cts_urn": URN_III_5,
                "language": "eng",
            },
        },
        provenance={"proof_test": "tests/test_aristotle_en_iii_5_manifest_gap_followup.py"},
    )
    result = validate_gold_against_snapshot([case], InMemoryCatalog())
    if result["status"] != "valid" or result["invalid_gold_count"] != 0:
        raise RuntimeError("strict eval gold admission did not validate")
    return {
        "case_id": case.id,
        "invalid_gold_count": 0,
        "status": "valid",
    }


def validate_result(
    rows: dict[str, list[dict[str, Any]]], publications_bib: str
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
    verifications = rows["registry_verifications"]

    _audit_authorities(nodes, publications_bib)
    by_passage = {str(row.get("passage_id") or ""): row for row in passages}
    greek = by_passage[PASSAGE_1113_GRC]
    english = by_passage[PASSAGE_1113_ENG]
    if _immutable_tuple(greek) != (
        PASSAGE_1113_GRC,
        GREEK_1113,
        REF_1113_GRC,
        URN_III_5,
        5111300070008,
    ) or _immutable_tuple(english) != (
        PASSAGE_1113_ENG,
        ENGLISH_1113,
        REF_1113_ENG,
        URN_III_5,
        5111300070008,
    ):
        raise RuntimeError("immutable 1113b7-8 corpus identity changed")
    if (
        greek.get("language") != "grc"
        or greek.get("passage_role") != "original"
        or greek.get("text_sha256_nfc") != text_hash(GREEK_1113)
        or english.get("language") != "eng"
        or english.get("passage_role") != "translation"
        or english.get("text_sha256_nfc") != text_hash(ENGLISH_1113)
        or english.get("work_canonical_id") != BOBZIEN_MANIFEST_ID
        or english.get("source_passage_id") != PASSAGE_1113_GRC
        or english.get("rights") != RIGHTS_CAVEAT
    ):
        raise RuntimeError("target corpus enrichment is incomplete")

    manifestations = {
        str(row.get("canonical_id") or ""): row for row in manifest
    }
    if len(manifestations) != len(manifest):
        raise RuntimeError("duplicate corpus manifestation canonical_id")
    greek_manifest = manifestations[GREEK_MANIFEST_ID]
    bobzien_manifest = manifestations[BOBZIEN_MANIFEST_ID]
    legacy_manifest = manifestations[LEGACY_ENGLISH_MANIFEST_ID]
    if (
        greek_manifest.get("passages") != 117
        or greek_manifest.get("language") != "grc"
        or greek_manifest.get("passage_role") != "original"
        or bobzien_manifest != desired_bobzien_manifest()
    ):
        raise RuntimeError("Greek/Bobzien manifestation contract failed")
    if (
        bobzien_manifest.get("cts_urn") != WORK_URN
        or "edition_urn" in bobzien_manifest
        or any(
            key in bobzien_manifest
            for key in ("artifact_sha256", "source_artifact_sha256")
        )
    ):
        raise RuntimeError("Bobzien manifestation invents edition/artifact authority")

    bobzien_rows = [
        row for row in passages if row.get("work_canonical_id") == BOBZIEN_MANIFEST_ID
    ]
    legacy_rows = [
        row
        for row in passages
        if row.get("work_canonical_id") == LEGACY_ENGLISH_MANIFEST_ID
    ]
    if [row.get("passage_id") for row in bobzien_rows] != [PASSAGE_1113_ENG]:
        raise RuntimeError("Bobzien manifestation is not exactly one passage")
    if len(legacy_rows) != 16:
        raise RuntimeError(f"legacy English cohort is not exactly 16 rows: {len(legacy_rows)}")
    legacy_ids = sorted(str(row["passage_id"]) for row in legacy_rows)
    if legacy_manifest != desired_legacy_manifest(legacy_ids):
        raise RuntimeError("legacy English manifestation is not fail-closed")
    for row in legacy_rows:
        serialized = canonical_json(row).lower()
        if (
            row.get("manifestation_id") == BOBZIEN_MANIFEST_ID
            or row.get("translator") == "Susanne Bobzien"
            or row.get("source_publication_id") == PUBLICATION_NODE
            or DOI in serialized
        ):
            raise RuntimeError(
                f"legacy row {row.get('passage_id')} is falsely attributed to Bobzien"
            )
        if (
            row.get("citability") != "discoverable_only"
            or row.get("passage_role") != "unresolved_english_research_record"
            or row.get("identity_status") != "source_identity_unresolved"
            or row.get("manifestation_id") != LEGACY_ENGLISH_MANIFEST_ID
            or row.get("language") != "eng"
        ):
            raise RuntimeError(
                f"legacy row {row.get('passage_id')} lacks fail-closed markers"
            )

    CitabilityTier, evidence_policy = load_citability_policy()

    legacy_snapshot_nodes = {
        str(row.get("passage_id") or ""): str(row.get("kg_node_id") or "")
        for row in citations
        if row.get("citation_type") == "snapshot_passage_node"
        and row.get("passage_id") in set(legacy_ids)
    }
    if len(legacy_snapshot_nodes) != 16:
        raise RuntimeError("legacy snapshot policy cohort is incomplete")
    by_node = {node_id(row): row for row in nodes}
    for row in legacy_rows:
        passage_id = str(row["passage_id"])
        node = by_node[legacy_snapshot_nodes[passage_id]]
        node_data = metadata(node)
        if (
            evidence_policy(row).tier is not CitabilityTier.DISCOVERABLE_ONLY
            or evidence_policy(node).tier is CitabilityTier.CITABLE
            or node_data.get("citability") != "discoverable_only"
            or node_data.get("passage_role")
            != "unresolved_english_research_record"
            or node_data.get("manifestation_id") != LEGACY_ENGLISH_MANIFEST_ID
        ):
            raise RuntimeError(
                f"central evidence policy still permits legacy row/node {passage_id}"
            )
    if evidence_policy(english).tier is not CitabilityTier.CITABLE:
        raise RuntimeError("exact Bobzien translation is not citable")

    english_node = require_node(nodes, ENGLISH_NODE_1113)
    english_node_data = metadata(english_node)
    if (
        english_node.get("description") != ENGLISH_1113
        or english_node_data.get("manifestation_id") != BOBZIEN_MANIFEST_ID
        or english_node_data.get("work_canonical_id") != KG_WORK_CANONICAL_ID
        or english_node_data.get("intellectual_work_cts_urn") != WORK_URN
        or english_node_data.get("cts_urn") != URN_III_5
        or "edition" in english_node_data
        or "edition_urn" in english_node_data
    ):
        raise RuntimeError("English KG node manifestation/work separation failed")

    ancient_source = require_unique(sources, "source_id", ANCIENT_SOURCE_ID)
    bobzien_source = require_unique(sources, "source_id", BOBZIEN_SOURCE_ID)
    if (
        ancient_source["coverage"]["state"] != "partial"
        or bobzien_source["coverage"]["state"] != "partial"
        or bobzien_source["acquisition"]["status"] != "missing"
        or bobzien_source["coverage"].get("corpus_manifestation_ids")
        != [BOBZIEN_MANIFEST_ID]
    ):
        raise RuntimeError("registry source coverage was overstated")
    bobzien_evidence = require_unique(evidence, "evidence_id", BOBZIEN_EVIDENCE_ID)
    if (
        bobzien_evidence.get("claim_status") != "in_review"
        or bobzien_evidence.get("quotation", {}).get("corpus_passage_ids")
        != [PASSAGE_1113_ENG]
        or bobzien_evidence.get("quotation", {}).get("rights") != RIGHTS_CAVEAT
        or bobzien_evidence.get("review_state", {}).get("independent_review")
        != "pending_root_review"
    ):
        raise RuntimeError("Bobzien evidence is not exactly passage-scoped")
    resolved_issue = require_unique(issues, "issue_id", RESOLVED_ISSUE_ID)
    legacy_issue = require_unique(issues, "issue_id", LEGACY_ISSUE_ID)
    if resolved_issue.get("status") != "resolved" or not any(
        item.get("opened_issue_id") == LEGACY_ISSUE_ID
        for item in resolved_issue.get("followups", [])
    ):
        raise RuntimeError("resolved issue follow-up is missing")
    if (
        legacy_issue.get("status") != "open"
        or legacy_issue.get("affected_count") != 17
        or legacy_issue.get("affected_record_count") != 16
        or set(legacy_issue.get("affected_corpus_ids", [])[1:]) != set(legacy_ids)
    ):
        raise RuntimeError("legacy-16 issue is incomplete")
    wave_01 = require_unique(waves, "wave_id", WAVE_01)
    if (
        RESOLVED_ISSUE_ID in wave_01.get("blocked_by", [])
        or LEGACY_ISSUE_ID not in wave_01.get("blocked_by", [])
    ):
        raise RuntimeError("wave blocked_by still points at the resolved issue")
    verification_by_id = {
        str(row.get("verification_id") or ""): row for row in verifications
    }
    for wanted in NEW_VERIFICATIONS:
        if verification_by_id.get(str(wanted["verification_id"])) != wanted:
            raise RuntimeError(f"registry verification drift: {wanted['verification_id']}")

    from scripts.check_corpus_invariants import find_violations as corpus_violations
    from scripts.check_kg_corpus_locus_parity import (
        find_violations as parity_violations,
    )
    from scripts.check_kg_work_child_canonical import find_mismatches
    from scripts.check_kg_work_id_uniqueness import collect_work_groups, find_collisions
    from scripts.check_snapshot_passage_integrity import audit_integrity

    corpus = corpus_violations(passages, citations, {node_id(row) for row in nodes})
    if any(corpus.values()):
        raise RuntimeError(
            "corpus invariant gate failed: "
            + canonical_json({key: len(value) for key, value in corpus.items()})
        )
    target_nodes = {GREEK_NODE_1113, ENGLISH_NODE_1113}
    snapshot_findings = _snapshot_target_violations(
        audit_integrity(nodes, passages, citations), target_nodes
    )
    if snapshot_findings:
        raise RuntimeError("target snapshot integrity gate failed")
    shared, parity_findings = parity_violations(
        nodes,
        passages,
        citations,
        prefixes=(GREEK_NODE_1113, ENGLISH_NODE_1113),
    )
    if shared != 2 or parity_findings:
        raise RuntimeError("target KG/corpus parity gate failed")
    work_child = find_mismatches(nodes, edges, manifest)
    if work_child:
        raise RuntimeError("work-child canonical gate failed")
    work_id_collisions = find_collisions(collect_work_groups(nodes, edges))
    if work_id_collisions:
        raise RuntimeError("work-id uniqueness gate failed")
    eval_validation = _validate_eval_admission(nodes, passages, manifest)

    return {
        "bobzien_manifestation_rows": len(bobzien_rows),
        "corpus_violations": 0,
        "eval_gold_admission": eval_validation,
        "legacy_unresolved_rows": len(legacy_rows),
        "legacy_non_citable_snapshot_nodes": len(legacy_snapshot_nodes),
        "manifestations": {
            "bobzien": BOBZIEN_MANIFEST_ID,
            "greek": GREEK_MANIFEST_ID,
            "legacy_unresolved": LEGACY_ENGLISH_MANIFEST_ID,
        },
        "parity_shared_checked": shared,
        "registry_coverage": "partial",
        "snapshot_target_violations": 0,
        "work_child_mismatches": 0,
        "work_id_collisions": 0,
    }


def _artifacts_state(snapshot: DataSnapshot) -> str:
    values = snapshot.optional_artifacts
    if all(value is None for value in values.values()):
        return "absent"
    if all(value is not None for value in values.values()):
        return "present"
    return "partial"


def transform(snapshot: DataSnapshot) -> RepairResult:
    rows = copy.deepcopy(snapshot.rows)
    publications_bib = snapshot.raw["publications_bib"].decode("utf-8")
    _audit_authorities(rows["nodes"], publications_bib)
    quarantine: list[dict[str, Any]] = []
    changes: Counter[str] = Counter()

    legacy_before = sorted(
        str(row["passage_id"])
        for row in rows["passages"]
        if row.get("work_canonical_id") == LEGACY_ENGLISH_MANIFEST_ID
        and row.get("passage_id") != PASSAGE_1113_ENG
    )
    if len(legacy_before) != 16:
        raise RuntimeError(
            f"expected sixteen non-Bobzien legacy English rows; found {len(legacy_before)}"
        )
    if tuple(legacy_before) != LEGACY_ENGLISH_PASSAGE_IDS:
        raise RuntimeError("legacy English passage membership drift")

    legacy_passage_rows = [
        require_unique(rows["passages"], "passage_id", passage_id)
        for passage_id in LEGACY_ENGLISH_PASSAGE_IDS
    ]
    desired_legacy_passages = [
        desired_legacy_passage(row) for row in legacy_passage_rows
    ]
    if legacy_passage_rows != desired_legacy_passages:
        if cohort_digest(legacy_passage_rows) != LEGACY_PASSAGES_BEFORE_DIGEST:
            raise RuntimeError("legacy English corpus cohort is partially changed or drifted")
        for current, wanted in zip(
            legacy_passage_rows, desired_legacy_passages, strict=True
        ):
            quarantine.append(
                _quarantine_record(
                    "corpus_passage_before",
                    current,
                    "make unresolved English research row discoverable-only",
                )
            )
            current.clear()
            current.update(wanted)
        changes["legacy_corpus_rows_failclosed"] += len(legacy_passage_rows)

    snapshots = [
        row
        for row in rows["citations"]
        if row.get("citation_type") == "snapshot_passage_node"
        and row.get("passage_id") in set(LEGACY_ENGLISH_PASSAGE_IDS)
    ]
    if len(snapshots) != 16 or len(
        {str(row.get("passage_id") or "") for row in snapshots}
    ) != 16:
        raise RuntimeError("legacy English snapshot mapping is not bijective")
    mapped_node_ids = tuple(sorted(str(row.get("kg_node_id") or "") for row in snapshots))
    if mapped_node_ids != LEGACY_ENGLISH_NODE_IDS:
        raise RuntimeError("legacy English snapshot node membership drift")
    legacy_node_rows = [require_node(rows["nodes"], wanted) for wanted in mapped_node_ids]
    desired_legacy_nodes = [desired_legacy_node(row) for row in legacy_node_rows]
    if legacy_node_rows != desired_legacy_nodes:
        if cohort_digest(legacy_node_rows) != LEGACY_NODES_BEFORE_DIGEST:
            raise RuntimeError("legacy English KG cohort is partially changed or drifted")
        for current, wanted in zip(legacy_node_rows, desired_legacy_nodes, strict=True):
            quarantine.append(
                _quarantine_record(
                    "kg_node_before",
                    current,
                    "make unresolved English snapshot node discoverable-only",
                )
            )
            current.clear()
            current.update(wanted)
        changes["legacy_kg_nodes_failclosed"] += len(legacy_node_rows)

    _replace_existing(
        rows["passages"],
        field="passage_id",
        wanted_id=PASSAGE_1113_GRC,
        builder=desired_greek_passage,
        quarantine_type="corpus_passage_before",
        reason="add explicit Greek language/role/hash/provenance only",
        count_key="corpus_passages_enriched",
        quarantine=quarantine,
        changes=changes,
    )
    _replace_existing(
        rows["passages"],
        field="passage_id",
        wanted_id=PASSAGE_1113_ENG,
        builder=desired_english_passage,
        quarantine_type="corpus_passage_before",
        reason="split exact Bobzien translation into its own manifestation",
        count_key="corpus_passages_enriched",
        quarantine=quarantine,
        changes=changes,
    )
    _replace_existing(
        rows["nodes"],
        field="node_id",
        wanted_id=ENGLISH_NODE_1113,
        builder=desired_english_node,
        quarantine_type="kg_node_before",
        reason="declare Bobzien manifestation separately from intellectual work CTS",
        count_key="kg_nodes_enriched",
        quarantine=quarantine,
        changes=changes,
    )
    _replace_existing(
        rows["manifest"],
        field="canonical_id",
        wanted_id=GREEK_MANIFEST_ID,
        builder=desired_greek_manifest,
        quarantine_type="corpus_manifest_before",
        reason="correct count 116->117 and add minimal language/role provenance",
        count_key="manifest_rows_enriched",
        quarantine=quarantine,
        changes=changes,
    )
    _add_exact(
        rows["manifest"],
        field="canonical_id",
        wanted=desired_bobzien_manifest(),
        absence_type="corpus_manifest_absence_before",
        count_key="manifest_rows_added",
        quarantine=quarantine,
        changes=changes,
    )
    _add_exact(
        rows["manifest"],
        field="canonical_id",
        wanted=desired_legacy_manifest(legacy_before),
        absence_type="corpus_manifest_absence_before",
        count_key="manifest_rows_added",
        quarantine=quarantine,
        changes=changes,
    )

    registry_changes = (
        (
            "registry_sources",
            "source_id",
            ANCIENT_SOURCE_ID,
            desired_ancient_source,
            "registry_source_before",
            "register exact Greek locus while retaining partial coverage",
            "registry_sources_updated",
        ),
        (
            "registry_sources",
            "source_id",
            BOBZIEN_SOURCE_ID,
            desired_bobzien_source,
            "registry_source_before",
            "register one exact translation without claiming full acquisition",
            "registry_sources_updated",
        ),
        (
            "registry_evidence",
            "evidence_id",
            ANCIENT_EVIDENCE_ID,
            desired_ancient_evidence,
            "registry_evidence_before",
            "link distinct Greek and Bobzien manifestations",
            "registry_evidence_updated",
        ),
        (
            "registry_evidence",
            "evidence_id",
            BOBZIEN_EVIDENCE_ID,
            desired_bobzien_evidence,
            "registry_evidence_before",
            "verify the short translation unit without overstating page mapping",
            "registry_evidence_updated",
        ),
        (
            "registry_issues",
            "issue_id",
            RESOLVED_ISSUE_ID,
            desired_resolved_issue,
            "registry_issue_before",
            "record eval-discovered manifestation follow-up",
            "registry_issues_updated",
        ),
        (
            "registry_waves",
            "wave_id",
            WAVE_00,
            desired_wave_00,
            "registry_wave_before",
            "record exact split and remaining legacy debt",
            "registry_waves_updated",
        ),
        (
            "registry_waves",
            "wave_id",
            WAVE_01,
            desired_wave_01,
            "registry_wave_before",
            "replace stale resolved blocker with the open legacy-16 issue",
            "registry_waves_updated",
        ),
    )
    for (
        label,
        field,
        wanted_id,
        builder,
        quarantine_type,
        reason,
        count_key,
    ) in registry_changes:
        _replace_existing(
            rows[label],
            field=field,
            wanted_id=wanted_id,
            builder=builder,
            quarantine_type=quarantine_type,
            reason=reason,
            count_key=count_key,
            quarantine=quarantine,
            changes=changes,
        )

    _add_exact(
        rows["registry_issues"],
        field="issue_id",
        wanted=desired_legacy_issue(legacy_before),
        absence_type="registry_issue_absence_before",
        count_key="registry_issues_added",
        quarantine=quarantine,
        changes=changes,
    )
    for verification in NEW_VERIFICATIONS:
        _add_exact(
            rows["registry_verifications"],
            field="verification_id",
            wanted=verification,
            absence_type="registry_verification_absence_before",
            count_key="registry_verifications_added",
            quarantine=quarantine,
            changes=changes,
        )

    validation = validate_result(rows, publications_bib)
    from scripts.check_snapshot_passage_integrity import audit_integrity

    before_snapshot_findings = audit_integrity(
        snapshot.rows["nodes"],
        snapshot.rows["passages"],
        snapshot.rows["citations"],
    )
    after_snapshot_findings = audit_integrity(
        rows["nodes"], rows["passages"], rows["citations"]
    )
    before_fingerprints = {
        str(row.get("fingerprint") or "") for row in before_snapshot_findings
    }
    new_fingerprints = [
        row
        for row in after_snapshot_findings
        if str(row.get("fingerprint") or "") not in before_fingerprints
    ]
    if new_fingerprints:
        raise RuntimeError(
            f"global snapshot gate gained {len(new_fingerprints)} new fingerprints"
        )
    validation.update(
        {
            "manifest_membership_violations": 0,
            "registry_structural_applied_copy_gate": (
                "tests/test_aristotle_en_iii_5_manifest_gap_followup.py"
            ),
            "snapshot_global_after": len(after_snapshot_findings),
            "snapshot_global_before": len(before_snapshot_findings),
            "snapshot_global_new_fingerprints": 0,
        }
    )
    artifact_state = _artifacts_state(snapshot)
    if artifact_state == "partial":
        raise RuntimeError("audit report/quarantine are in a partial state")
    mode = "planned" if changes else "already_applied"
    if changes and artifact_state != "absent":
        raise RuntimeError("repair outputs already exist before first application")
    if not changes and artifact_state != "present":
        raise RuntimeError("data is repaired but audit report/quarantine are absent")

    report = {
        "artifact_type": "eleutheria.aristotle_en_iii5_manifest_gap_repair",
        "schema_version": "1.0",
        "stamp": STAMP,
        "generated_at": "2026-08-24T06:00:00Z",
        "mode": mode,
        "discovery": {
            "trigger": "strict eval gold rejected the missing English manifestation",
            "greek_manifest_before_count": 116,
            "greek_corpus_count": 117,
            "legacy_english_slug_before_count": 17,
            "verified_bobzien_rows": 1,
            "unresolved_legacy_rows": 16,
        },
        "authority": {
            "publication_node_id": PUBLICATION_NODE,
            "publication": PUBLICATION_LABEL,
            "doi": DOI,
            "translation_label": "translation (I)",
            "source_artifact_status": NO_ARTIFACT,
            "rights": RIGHTS_CAVEAT,
        },
        "manifestation_split": {
            "bobzien": {
                "canonical_id": BOBZIEN_MANIFEST_ID,
                "passage_ids": [PASSAGE_1113_ENG],
                "cts_identity": WORK_URN,
                "edition_cts_status": "not_asserted",
            },
            "greek": {
                "canonical_id": GREEK_MANIFEST_ID,
                "passages": 117,
            },
            "legacy_unresolved": {
                "canonical_id": LEGACY_ENGLISH_MANIFEST_ID,
                "citability": "discoverable_only_on_rows_and_snapshot_nodes",
                "passage_ids": legacy_before,
                "status": "identity_unresolved_non_citable",
            },
        },
        "immutability": {
            "fields_unchanged": [
                "text_content",
                "passage_id",
                "canonical_ref",
                "cts_urn",
                "sequence_number",
            ],
            "greek_text_sha256_nfc": text_hash(GREEK_1113),
            "english_text_sha256_nfc": text_hash(ENGLISH_1113),
        },
        "registry": {
            "bobzien_source_coverage": "partial",
            "full_article_acquisition": "missing",
            "legacy_issue_id": LEGACY_ISSUE_ID,
            "resolved_issue_followup": RESOLVED_ISSUE_ID,
        },
        "snapshot_a_sha256": {
            label: sha256_bytes(raw) for label, raw in sorted(snapshot.raw.items())
        },
        "changes": dict(sorted(changes.items())),
        "quarantine_records": len(quarantine),
        "validation": validation,
        "scope_exclusions": [
            "No eval file was edited.",
            "No remote deployment was performed.",
            "No edge, citation, publication, passage text, UUID, reference, CTS locus, or sequence was changed.",
            "The sixteen legacy English rows and snapshot nodes were fail-closed/classified, not source-repaired.",
        ],
    }
    return RepairResult(
        rows=rows,
        quarantine=quarantine,
        report=report,
        changes=changes,
        validation=validation,
        mode=mode,
    )


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
        raise RuntimeError("concurrent write detected while loading snapshot A")
    rows = {
        label: rows_from_bytes(raw)
        for label, raw in first.items()
        if label != "publications_bib"
    }
    return DataSnapshot(rows=rows, raw=first, optional_artifacts=first_optional)


def _jsonl_content_preserving(
    original: bytes,
    rows: list[dict[str, Any]],
    key: Callable[[dict[str, Any]], str],
    label: str,
) -> bytes:
    desired = {key(row): row for row in rows}
    if len(desired) != len(rows) or "" in desired:
        raise RuntimeError(f"duplicate or empty desired keys for {label}")
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
    "passages": lambda row: str(row.get("passage_id") or ""),
    "manifest": lambda row: str(row.get("canonical_id") or ""),
    "registry_sources": lambda row: str(row.get("source_id") or ""),
    "registry_evidence": lambda row: str(row.get("evidence_id") or ""),
    "registry_issues": lambda row: str(row.get("issue_id") or ""),
    "registry_waves": lambda row: str(row.get("wave_id") or ""),
    "registry_verifications": lambda row: str(row.get("verification_id") or ""),
}


def build_outputs(
    data_root: Path, snapshot: DataSnapshot, result: RepairResult
) -> dict[Path, bytes]:
    if not result.changes:
        return {}
    outputs: dict[Path, bytes] = {}
    for label in MUTABLE_LABELS:
        payload = _jsonl_content_preserving(
            snapshot.raw[label], result.rows[label], JSONL_KEYS[label], label
        )
        if payload != snapshot.raw[label]:
            outputs[data_root / INPUT_RELATIVES[label]] = payload
    quarantine_payload = (
        "\n".join(canonical_json(row) for row in result.quarantine) + "\n"
    ).encode("utf-8")
    outputs[data_root / QUARANTINE_RELATIVE] = quarantine_payload
    outputs[data_root / REPORT_RELATIVE] = (
        json.dumps(result.report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
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
        "wb", dir=target.parent, prefix=".aristotle-en-stage-", delete=False
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


def _safe_target(data_root: Path, relative: str) -> Path:
    root = data_root.resolve()
    target = (root / relative).resolve()
    if root not in target.parents:
        raise RuntimeError(f"transaction target escapes data root: {relative!r}")
    allowed = {
        str(INPUT_RELATIVES[label]) for label in MUTABLE_LABELS
    } | {str(QUARANTINE_RELATIVE), str(REPORT_RELATIVE)}
    if relative not in allowed:
        raise RuntimeError(f"transaction target is outside repair scope: {relative!r}")
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
    expected = (data_root / TRANSACTION_RELATIVE).resolve()
    if transaction.resolve() != expected or transaction == data_root:
        raise RuntimeError("refusing unsafe transaction cleanup")
    shutil.rmtree(transaction)
    _fsync_directory(transaction.parent)


def _verify_snapshot_a(data_root: Path, snapshot: DataSnapshot) -> None:
    for label, expected in snapshot.raw.items():
        path = data_root / INPUT_RELATIVES[label]
        if path.read_bytes() != expected:
            raise RuntimeError(f"snapshot-A drift before commit: {path}")
    for relative, expected in snapshot.optional_artifacts.items():
        if _optional_read(data_root / relative) != expected:
            raise RuntimeError(f"snapshot-A artifact drift before commit: {relative}")


def _entry_matches(data_root: Path, entry: dict[str, Any], which: str) -> bool:
    target = _safe_target(data_root, str(entry["target"]))
    expected = entry[f"{which}_sha256"]
    current = _optional_read(target)
    if expected is None:
        return current is None
    return current is not None and sha256_bytes(current) == expected


def _restore_entries(data_root: Path, journal: dict[str, Any]) -> None:
    journal["state"] = "rolling_back"
    _write_journal(_journal_path(data_root), journal)
    transaction = data_root / TRANSACTION_RELATIVE
    for entry in reversed(journal["entries"]):
        target = _safe_target(data_root, str(entry["target"]))
        before_hash = entry["before_sha256"]
        if before_hash is None:
            if target.exists():
                _remove_file(target)
            continue
        backup = transaction / str(entry["backup"])
        raw = backup.read_bytes()
        if sha256_bytes(raw) != before_hash:
            raise RuntimeError(f"transaction backup hash mismatch: {backup}")
        staged = _stage_bytes(target, raw)
        _replace_staged_file(staged, target)
    if not all(_entry_matches(data_root, entry, "before") for entry in journal["entries"]):
        raise RuntimeError("transaction rollback verification failed")
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
        raise RuntimeError("foreign transaction journal at Aristotle repair path")
    entries = journal.get("entries")
    if not isinstance(entries, list) or not entries:
        raise RuntimeError("invalid Aristotle transaction journal entries")
    for entry in entries:
        _safe_target(data_root, str(entry.get("target") or ""))
    state = str(journal.get("state") or "")
    all_before = all(_entry_matches(data_root, entry, "before") for entry in entries)
    all_after = all(_entry_matches(data_root, entry, "after") for entry in entries)
    if state == "prepared":
        if not all_before:
            raise RuntimeError("prepared transaction touched a target unexpectedly")
        _cleanup_transaction(data_root)
        return "prepared_stage_removed"
    if state == "committed":
        if not all_after:
            raise RuntimeError("committed transaction targets no longer match journal")
        _cleanup_transaction(data_root)
        return "committed_cleanup_finished"
    if state in {"committing", "rolling_back"}:
        if all_after:
            journal["state"] = "committed"
            _write_journal(journal_path, journal)
            _cleanup_transaction(data_root)
            return "commit_finished"
        if all_before:
            _cleanup_transaction(data_root)
            return "already_rolled_back"
        _restore_entries(data_root, journal)
        return "partial_commit_rolled_back"
    raise RuntimeError(f"unknown Aristotle transaction state {state!r}")


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
        raise RuntimeError("unrecovered Aristotle transaction exists")
    transaction.mkdir(parents=True)
    _fsync_directory(transaction.parent)
    backup_dir = transaction / "backup"
    stage_dir = transaction / "stage"
    backup_dir.mkdir()
    stage_dir.mkdir()
    _fsync_directory(transaction)

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
            "created_at": "2026-08-24T06:00:00Z",
            "committed_targets": [],
            "entries": entries,
        }
        _write_journal(_journal_path(data_root), journal)
        _verify_snapshot_a(data_root, snapshot)
        journal["state"] = "committing"
        _write_journal(_journal_path(data_root), journal)
        for entry in entries:
            if not _entry_matches(data_root, entry, "before"):
                raise RuntimeError(
                    f"target drift immediately before replace: {entry['target']}"
                )
            staged = transaction / str(entry["stage"])
            target = _safe_target(data_root, str(entry["target"]))
            _replace_staged_file(staged, target)
            journal["committed_targets"].append(entry["target"])
            _write_journal(_journal_path(data_root), journal)
        if not all(_entry_matches(data_root, entry, "after") for entry in entries):
            raise RuntimeError("post-commit target hash verification failed")
        journal["state"] = "committed"
        _write_journal(_journal_path(data_root), journal)
        _cleanup_transaction(data_root)
    except Exception:
        journal_path = _journal_path(data_root)
        if journal_path.exists():
            current = json.loads(journal_path.read_text(encoding="utf-8"))
            _restore_entries(data_root, current)
        else:
            _cleanup_transaction(data_root)
        raise


def write_result(data_root: Path, snapshot: DataSnapshot, result: RepairResult) -> None:
    with transaction_lock(data_root):
        recovery = recover_incomplete_transaction_locked(data_root)
        if recovery != "none":
            raise RuntimeError(
                "recovered an earlier transaction; reload snapshot A before writing"
            )
        commit_result_locked(data_root, snapshot, result)


def _validate_existing_artifacts(snapshot: DataSnapshot) -> None:
    report_raw = snapshot.optional_artifacts[REPORT_RELATIVE]
    quarantine_raw = snapshot.optional_artifacts[QUARANTINE_RELATIVE]
    if report_raw is None or quarantine_raw is None:
        raise RuntimeError("applied repair lacks report/quarantine")
    report = json.loads(report_raw.decode("utf-8"))
    if (
        report.get("stamp") != STAMP
        or report.get("manifestation_split", {}).get("bobzien", {}).get("canonical_id")
        != BOBZIEN_MANIFEST_ID
    ):
        raise RuntimeError("applied audit report drift")
    quarantine = rows_from_bytes(quarantine_raw)
    if not quarantine or not any(
        row.get("record_type") == "corpus_passage_before" for row in quarantine
    ):
        raise RuntimeError("applied before-image quarantine drift")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="apply transaction")
    parser.add_argument("--dry-run", action="store_true", help="explicit no-op default")
    parser.add_argument("--data-root", type=Path, default=DEFAULT_DATA_ROOT)
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
        parser.error(
            "production write requires explicit approval and "
            "--production-write-approved"
        )

    if not args.write and (data_root / TRANSACTION_RELATIVE).exists():
        raise RuntimeError(
            "incomplete transaction present; dry-run will not mutate it, use an "
            "approved --write invocation to recover"
        )

    if args.write:
        with transaction_lock(data_root):
            recovery = recover_incomplete_transaction_locked(data_root)
            snapshot = load_data_snapshot(data_root)
            result = transform(snapshot)
            if result.changes:
                commit_result_locked(data_root, snapshot, result)
        if recovery != "none":
            print("recovery:", recovery)
    else:
        snapshot = load_data_snapshot(data_root)
        result = transform(snapshot)

    print("Aristotle EN III.5 manifestation-gap follow-up")
    print("mode:", "WRITE" if args.write else "DRY-RUN")
    print("state:", result.mode)
    print("changes:", canonical_json(dict(sorted(result.changes.items()))))
    print("quarantine records:", len(result.quarantine))
    print("validation:", canonical_json(result.validation))
    if not args.write:
        print("dry-run: nothing written")
        return 0
    if not result.changes:
        _validate_existing_artifacts(snapshot)
        print("already applied: no files written")
    else:
        print("transaction committed locally; no remote deployment")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
