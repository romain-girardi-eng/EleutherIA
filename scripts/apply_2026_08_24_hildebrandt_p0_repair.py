#!/usr/bin/env python3
"""Prepare the bounded Hildebrandt 2022 P0 provenance repair.

Dry-run is the default. Repository writes require both ``--write`` and
``--production-write-approved``. The repair corrects the local article's
bibliographic identity and rights, page-maps eight existing scholarly positions,
makes them discovery-only pending review, removes public contact data, repairs
stale Cicero work identifiers in citation notes, and registers the still-corrupt
Alexander De fato 8/11 source text as open debt without editing corpus text.

The multi-file write path uses Snapshot-A drift checks, fsynced stages/backups,
a durable journal, rollback, hard-crash recovery, and idempotence validation.
No deployment is performed.
"""

from __future__ import annotations

import argparse
import copy
import fcntl
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

STAMP = "hildebrandt_p0_repair_2026_08_24"
NOW = "2026-08-24 11:00:00+00:00"
ACCESSED_AT = "2026-08-24T11:00:00Z"

PDF_RELATIVE = "data/literature_acquisition/hildebrandt_2022_alexander_lazy_arguments.pdf"
PDF_SHA256 = "3a632d61028344ffcba880cebdc6678cfaa22ba456956f55715279928c749717"
PDF_BYTES = 343_020
PDF_PAGES = 20
AUDIT_RELATIVE = "docs/academic/2026-08-24-hildebrandt-lazy-arguments-pdf-audit.md"
AUDIT_SHA256 = "e2b262453c105e17694d15742b5eec5dd8055263609de011d2f9812bf6477331"
OFFICIAL_URL = "https://ojs.utlib.ee/index.php/spe/article/view/22849"

TITLE = "Alexander of Aphrodisias’ Lazy Arguments against Stoic Determinism"
AUTHOR = "Ronja Hildebrandt"
DOI = "10.12697/spe.2022.15.01"
ISSN = "1736-5899"
RIGHTS_STATEMENT = "© All Copyright Author"
MANIFESTATION_ID = "hildebrandt_2022_spe15_pdf_pp25_44_eng"
PUBLICATION_ID = "pub_hildebrandt_2022_alexander_lazy_arguments"
SCHOLAR_ID = "scholar_hildebrandt_ronja"
SOURCE_ID = "src_sec_hildebrandt_2022_lazy_arguments"
SCHOLARLY_PUBLICATION_DIR = "hildebrandt2022lazyarguments"
LITERATURE_ARTIFACT_ID = "lit_hildebrandt_2022_alexander_lazy_arguments"
BIBTEX_KEY = (
    "hildebrandt-2022-hildebrandt-2022-alexander-of-aphrodisias-"
    "lazy-arguments-against-stoic-determinism"
)

POSITION_IDS = (
    "scholarly_argument_hildebrandt_alexander_new_lazy_argument_risk",
    "scholarly_argument_hildebrandt_alexander_objections_fail_homonymy",
    "scholarly_argument_hildebrandt_average_rational_agent_laziness",
    "scholarly_argument_hildebrandt_chrysippus_cofated_response",
    "scholarly_argument_hildebrandt_chrysippus_cylinder_moral_responsibility",
    "scholarly_argument_hildebrandt_de_fato_xxi_risk_asymmetry",
    "scholarly_argument_hildebrandt_risk_obtains_even_if_determinism_true",
    "scholarly_argument_hildebrandt_traditional_lazy_argument_three_versions",
)

POSITION_SPECS: dict[str, dict[str, Any]] = {
    POSITION_IDS[0]: {
        "claim_ids": ["HIL-01"],
        "ranges": [(25, 27, 1, 3), (37, 42, 13, 18)],
        "description": (
            "Hildebrandt characterizes a named line of scholarship as treating "
            "Alexander's ordinary objections to Stoic determinism as unsuccessful, "
            "then argues that De fato XXI offers a comparatively more successful "
            "Lazy Argument. The assessment is Hildebrandt's thesis, not a measured "
            "scholarly consensus or a conclusive demonstration. Its modern risk "
            "framing concerns whether belief in determinism may give average rational "
            "agents reasons for laziness under uncertainty."
        ),
        "components": [
            {
                "claim_id": "HIL-01",
                "role": "hildebrandt_central_thesis_secondary_interpretation",
                "ancient_anchor": "Alexander, De fato 21, Bruns 191.2-26",
                "qualification": "comparatively more successful, not conclusively established",
            }
        ],
    },
    POSITION_IDS[1]: {
        "claim_ids": ["HIL-02"],
        "ranges": [(27, 30, 3, 6)],
        "description": (
            "Hildebrandt argues that several objections in Alexander, De fato 8-9, "
            "miss their target because 'contingent' is used in different senses: an "
            "Aristotelian sense tied to essence or proper cause and a Stoic sense tied "
            "to the causal state of the cosmos. This is her critical reconstruction. "
            "The De fato 8 corpus route remains textually corrupt and is not primary-"
            "verified by this secondary-source record."
        ),
        "components": [
            {
                "claim_id": "HIL-02",
                "role": "hildebrandt_critical_reconstruction",
                "ancient_anchor": "Alexander, De fato 8-9",
                "qualification": "secondary interpretation; De fato 8 recollation pending",
            }
        ],
    },
    POSITION_IDS[2]: {
        "claim_ids": ["HIL-07", "HIL-08"],
        "ranges": [(39, 41, 15, 17)],
        "description": (
            "Hildebrandt extends Alexander's argument to the epistemically limited "
            "average rational agent rather than the ideal Stoic sage. She adds reasons "
            "for motivational laziness beyond Alexander's stated reason; one is "
            "explicitly developed from Brennan 2005. These are Hildebrandt's and "
            "Brennan-derived extensions, not claims stated directly by Alexander."
        ),
        "components": [
            {
                "claim_id": "HIL-07",
                "role": "hildebrandt_interpretive_extension",
                "qualification": "average-agent target not directly attributed to Alexander",
            },
            {
                "claim_id": "HIL-08",
                "role": "hildebrandt_extension_partly_derived_from_brennan_2005",
                "qualification": "supplementary reasons beyond Alexander's text",
            },
        ],
    },
    POSITION_IDS[3]: {
        "claim_ids": ["HIL-04"],
        "ranges": [(32, 33, 8, 9)],
        "description": (
            "Hildebrandt reports the transmitted Chrysippean co-fatedness response to "
            "the traditional Lazy Argument: actions and deliberations belong to the "
            "causal nexus with their outcomes. Cicero, Origen, Seneca and Eusebius are "
            "transmitters or parallels; this node is a modern secondary synthesis, not "
            "an autograph statement by Chrysippus."
        ),
        "components": [
            {
                "claim_id": "HIL-04",
                "role": "reported_chrysippean_response_via_transmitters",
                "ancient_anchor": "Cicero, De fato 28-30; reported parallels",
                "qualification": "secondary synthesis of transmitted evidence",
            }
        ],
    },
    POSITION_IDS[4]: {
        "claim_ids": ["HIL-05"],
        "ranges": [(33, 37, 9, 13)],
        "description": (
            "Hildebrandt reconstructs a strengthened Stoic response from the cylinder "
            "material: external impetus and the agent's individual constitution play "
            "different causal roles in assent and action. The causal labels and moral-"
            "responsibility conclusion are assembled across Cicero, Aulus Gellius and "
            "other witnesses; they are not one direct ancient formulation."
        ),
        "components": [
            {
                "claim_id": "HIL-05",
                "role": "hildebrandt_multi_witness_reconstruction",
                "ancient_anchor": "Cicero, De fato 42-43; Aulus Gellius 7.2.11-13",
                "qualification": "causal terminology reconstructed across witnesses",
            }
        ],
    },
    POSITION_IDS[5]: {
        "claim_ids": ["HIL-06"],
        "ranges": [(37, 40, 13, 16)],
        "description": (
            "Hildebrandt reads Alexander, De fato XXI, as comparing asymmetric "
            "practical errors under uncertainty. The contrast between errors is "
            "directly anchored in Alexander; its formulation as a modern risk argument "
            "and comparison with Pascal's Wager are secondary interpretive framings."
        ),
        "components": [
            {
                "claim_id": "HIL-06a",
                "role": "direct_ancient_asymmetry_reported_by_hildebrandt",
                "ancient_anchor": "Alexander, De fato 21, Bruns 191.6-23",
                "qualification": "ancient contrast; corpus route not independently recollated here",
            },
            {
                "claim_id": "HIL-06b",
                "role": "modern_risk_framing",
                "qualification": "Hildebrandt/Weidemann interpretive comparison",
            },
        ],
    },
    POSITION_IDS[6]: {
        "claim_ids": ["HIL-09"],
        "ranges": [(41, 42, 17, 18)],
        "description": (
            "Hildebrandt extends the motivational-risk argument to the case in which "
            "Stoic determinism is true. She reports that she identifies no transmitted "
            "Stoic response to this developed version in the materials reviewed. That "
            "bounded negative finding is not proof of absolute historical absence."
        ),
        "components": [
            {
                "claim_id": "HIL-09",
                "role": "hildebrandt_interpretive_extension_and_bounded_negative_finding",
                "qualification": "no response identified in reviewed transmission, not absolute absence",
            }
        ],
    },
    POSITION_IDS[7]: {
        "claim_ids": ["HIL-03"],
        "ranges": [(30, 32, 6, 8)],
        "description": (
            "Hildebrandt distinguishes Alexander's first two Lazy-Argument versions: "
            "De fato XI concerns the uselessness of deliberation, while XVI concerns "
            "the uselessness of effort. The distinction is textually anchored but "
            "reported here through Hildebrandt; the De fato 11 corpus route contains a "
            "duplicated final segment and remains pending primary recollation."
        ),
        "components": [
            {
                "claim_id": "HIL-03",
                "role": "ancient_textual_distinction_reported_by_hildebrandt",
                "ancient_anchor": "Alexander, De fato 11 and 16",
                "qualification": "De fato 11 corpus text corrupt; primary verification pending",
            }
        ],
    },
}

AUTHOR_EDGE_IDS = frozenset(
    {
        "b6d69009-d1cb-4bd1-b44c-fb562654b2a6",
        "1237fc6b-a3b8-4684-906b-4bc8d3525d84",
        "0affa5c4-26c2-4a71-9fe8-ad13440a6ff3",
        "6fef95f3-6e44-4b0d-acb4-82a5a94708d5",
        "14e82705-9b98-437b-ac9c-a257a0e8da64",
        "cd00d396-8344-40ea-b7d3-ef15a0216cb0",
        "ae71b40d-2c01-420a-81f2-267e90312be9",
        "e047ae18-0211-4e6f-831f-eb83423542a9",
    }
)

DE_FATO_8_UUID = "dc2294ba-b234-4c98-b87d-797913eeb440"
DE_FATO_11_UUID = "af0813bf-6ed5-40b9-9f3a-0dbd820a0f58"
CITATION_TARGETS: dict[tuple[str, str, str], str] = {
    (POSITION_IDS[3], "8ba2536b-c925-490f-b37b-f48bde28a03f", "paraphrase"): "cicero_phi054",
    (POSITION_IDS[4], "0a1bf1ae-9888-4a9e-8da8-9ff3ae4c8f7e", "paraphrase"): "cicero_phi054",
    (POSITION_IDS[1], DE_FATO_8_UUID, "discussion"): "de_fato_8_open_debt",
    (POSITION_IDS[7], DE_FATO_11_UUID, "paraphrase"): "de_fato_11_open_debt",
}

DEBT_NOTES = {
    "de_fato_8_open_debt": (
        "Hildebrandt P0 2026-08-24: route retained as secondary discussion only; "
        "the corpus text contains visible duplications 'ἀργύριον ριον' and 'τὸ τὸ'. "
        "Primary recollation against Bruns/OGL is open."
    ),
    "de_fato_11_open_debt": (
        "Hildebrandt P0 2026-08-24: route retained as secondary paraphrase only; "
        "the corpus text duplicates its final segment around 'ὑφ’ ἡμῶν' and "
        "'ἐξουσίαν'. Primary recollation against Bruns/OGL is open."
    ),
}

EVIDENCE_IDS = {
    POSITION_IDS[0]: "ev_sec_hildebrandt_hil01_pp25_27",
    POSITION_IDS[1]: "ev_sec_hildebrandt_hil02_pp27_30",
    POSITION_IDS[2]: "ev_sec_hildebrandt_hil07_08_pp39_41",
    POSITION_IDS[3]: "ev_sec_hildebrandt_hil04_pp32_33",
    POSITION_IDS[4]: "ev_sec_hildebrandt_hil05_pp33_37",
    POSITION_IDS[5]: "ev_sec_hildebrandt_hil06_pp37_40",
    POSITION_IDS[6]: "ev_sec_hildebrandt_hil09_pp41_42",
    POSITION_IDS[7]: "ev_sec_hildebrandt_hil03_pp30_32",
}
HIL01_DEVELOPMENT_EVIDENCE_ID = "ev_sec_hildebrandt_hil01_pp37_42"
ALL_EVIDENCE_IDS = frozenset({*EVIDENCE_IDS.values(), HIL01_DEVELOPMENT_EVIDENCE_ID})
CLAIM_ISSUE_ID = "issue_hildebrandt_2022_claim_review_and_rights_20260824"
TEXT_ISSUE_ID = "issue_alexander_de_fato_8_11_text_corruption_20260824"
WAVE_SECONDARY = "wave_01_pdf_priority_new_knowledge"
WAVE_FACTUAL = "wave_00_known_factual_blockers"

SCRIPT_RELATIVE = "scripts/apply_2026_08_24_hildebrandt_p0_repair.py"
TEST_RELATIVE = "tests/test_hildebrandt_p0_repair.py"
NODES_RELATIVE = "data/kg/nodes.jsonl"
EDGES_RELATIVE = "data/kg/edges.jsonl"
CITATIONS_RELATIVE = "data/corpus/citations.jsonl"
BUILDER_RELATIVE = "scripts/build_literature_acquisition_manifest.py"
LITERATURE_RELATIVE = "data/literature_acquisition/manifest.jsonl"
SCHOLARLY_RELATIVE = "data/scholarly_sources/manifest.jsonl"
BIB_RELATIVE = "data/kg/publications.bib"
BIB_REPORT_RELATIVE = "data/kg/publications_bibtex_report.json"
SOURCES_RELATIVE = "data/goals/sota/registry/sources/seed_priority_20260824.jsonl"
EVIDENCE_RELATIVE = "data/goals/sota/registry/evidence/seed_priority_20260824.jsonl"
ISSUES_RELATIVE = "data/goals/sota/registry/issues/seed_known_20260824.jsonl"
WAVES_RELATIVE = "data/goals/sota/registry/waves/priority_20260824.jsonl"

REPORT_RELATIVE = "data/audit/2026-08-24_hildebrandt_p0_repair.json"
QUARANTINE_RELATIVE = "data/audit/2026-08-24_hildebrandt_p0_quarantine.jsonl"
LOCK_RELATIVE = "data/audit/.hildebrandt_p0.lock"
JOURNAL_RELATIVE = "data/audit/.hildebrandt_p0_transaction.json"
BACKUP_DIR_RELATIVE = "data/audit/.hildebrandt_p0_transaction_backups"

FILE_BEFORE_SHA256: dict[str, str] = {
    NODES_RELATIVE: "57fb90da476ebdf98bc59f4a0cb4bad0c4871d5d829c0dc05063b4752b6c8664",
    EDGES_RELATIVE: "22efd267ac194d67d23ffd9985d2c68d93e1cfb4129e1a91cc3fda4871fadd70",
    CITATIONS_RELATIVE: "3fa555efad53ad2795f04fb28959442e42630b4f33187c1c7a1b78890af0d248",
    BUILDER_RELATIVE: "59cbd46c4a9b62e3fc2497089cb2469dfc4a55916d9ef3f059ad639ab6b3eef3",
    LITERATURE_RELATIVE: "5c567015a2a064147efb4d9eaa64cf72e55432f42d0231f73758ea538858514d",
    SCHOLARLY_RELATIVE: "e326abbe07e78f6c8ca873e1ef99ab5ca77e64066a838bcf93ff360e466bcbe5",
    BIB_RELATIVE: "2bf6ea54d93bb86249997a076e73dde025b8e765e1edcab59f641ad77c5f4dcc",
    BIB_REPORT_RELATIVE: "66355e056418b9c446a278e9d29b0119d60628504f73bc10af08d73d155b6f72",
    SOURCES_RELATIVE: "ceba6d9e9ec188d943abdd345f0149dca017b70a82404f7d858774f812bcd650",
    EVIDENCE_RELATIVE: "41683cdb6df1b826dbc625853c08a3fcd66c0579a7ca96883c5e326ecd82cbe7",
    ISSUES_RELATIVE: "1aa809df5ebfc5f81d31963ce84fa37ab7563a4d61d9007fc7009399819a130a",
    WAVES_RELATIVE: "4b9cfecc1c3075900e681c56af5ef0278dc8d19ba66150f0b562cd58712a7bee",
}

FILE_AFTER_SHA256: dict[str, str] = {
    NODES_RELATIVE: "07adbfa2826e4c23a15f95dcae1504e1f2a0ac228433cee5835f1fe14b046e4d",
    EDGES_RELATIVE: "31ac588b16faacf6de7b6fd1d23d247e790c3bea1d3655a91dacea3cc8ccda2c",
    CITATIONS_RELATIVE: "07f0ff46bc162fe69e86b7187f28653886e0bdcf3e863b0790e9f016b13c25ee",
    BUILDER_RELATIVE: "d6519cf1192db6ae3dccb5ebc25599c145f5c472b88e2da4d821c4761333f9f6",
    LITERATURE_RELATIVE: "e1a5c1bf0ed25615005c9cd3107f3be25235b535faa563e5fa847eb5e9522933",
    SCHOLARLY_RELATIVE: "33f304aee1a3882c75f47e212bae778e64c23da6cb9f39cda0790416f0c9e9b6",
    BIB_RELATIVE: "e4cc9a15bdbe756446518a09f9a97f9405c98a7b54886de39afc07892941c44a",
    BIB_REPORT_RELATIVE: "7612db557443d1c6c27507a130aa283a115e8a765075b297a7c019ef6104b68a",
    SOURCES_RELATIVE: "54b02bc1ce94680f18b8e22e92f6a2aa4a21f0dd48a71e9a9eac168d9fd80d1e",
    EVIDENCE_RELATIVE: "0d360b28689f260c00717462778a48c124d2992521a87165733df4044304f1e0",
    ISSUES_RELATIVE: "e265e74f274d3d62cb1b411bfe939229d88682859a0554349c30658e50738818",
    WAVES_RELATIVE: "2cf060fc4aa38a0a6c7f17c01030c22e81e3e8b29cc4acb68989be9f1b432989",
}

IMMUTABLE_FILE_HASHES = {
    "data/corpus/passages.jsonl": "4e2e7b8789de06f3b3cf897c3f9b6d63bc92db5ee24657dabee6c9ba510f51ec",
    "data/corpus/manifest.jsonl": "aa4d446f32b5d47d4fb3d002dec3b49398862f8f3f8515b6076655ea8e414cd6",
    "data/kg/e2_patches/cary.json": "1fb574160b21f3b035dc29a818f4f0858664512a084ffc0b7834b255b001182e",
    "data/kg/e2_patches/sorabji.json": "d84f98c3bce2859cc5ec36b9ea5785f5aa92240a05bb902bb6b970261f84e660",
}

OLD_BUILDER_BLOCK = '''    "hildebrandt_2022_alexander_lazy_arguments.pdf": item(
        "hildebrandt_2022_alexander_lazy_arguments",
        "Alexander of Aphrodisias and the Lazy Argument", ["David Hildebrandt"], 2022,
        scope="core"
    ),'''

NEW_BUILDER_BLOCK = '''    "hildebrandt_2022_alexander_lazy_arguments.pdf": {
        **item(
            "hildebrandt_2022_alexander_lazy_arguments",
            "Alexander of Aphrodisias’ Lazy Arguments against Stoic Determinism",
            ["Ronja Hildebrandt"], 2022, role="source_file",
            audit_status="deep_read_wave1", scope="core"
        ),
        "manifestation_id": "hildebrandt_2022_spe15_pdf_pp25_44_eng",
        "doi": "10.12697/spe.2022.15.01",
        "journal": "Studia Philosophica Estonica",
        "volume": 15,
        "printed_page_range": {"start": 25, "end": 44},
        "pdf_page_range": {"start": 1, "end": 20},
        "page_map": "PDF page = printed page - 24",
        "access_status": "open_access",
        "access_url": "https://ojs.utlib.ee/index.php/spe/article/view/22849",
        "rights_statement": "© All Copyright Author",
        "license_status": "no_explicit_reuse_licence_archived",
        "reuse_status": "unverified_do_not_republish",
    },'''


class PreconditionsError(RuntimeError):
    """The reviewed before-image no longer matches the workspace."""


@dataclass(slots=True)
class RepairPlan:
    root: Path
    outputs: dict[Path, bytes]
    before_bytes: dict[Path, bytes | None]
    quarantine: list[dict[str, Any]]
    counts: Counter[str]
    summary: dict[str, Any]


def canonical_hash(value: Any) -> str:
    payload = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def node_id(row: dict[str, Any]) -> str:
    return str(row.get("node_id") or row.get("id") or "")


def edge_id(row: dict[str, Any]) -> str:
    return str(row.get("edge_id") or row.get("id") or "")


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
    if isinstance(value, dict):
        return copy.deepcopy(value)
    if isinstance(value, str) and value.strip():
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return {}
        return copy.deepcopy(parsed) if isinstance(parsed, dict) else {}
    return {}


def set_metadata(row: dict[str, Any], value: dict[str, Any]) -> None:
    row["metadata"] = value


def file_state(root: Path, relative: str) -> str:
    current = sha256_file(root / relative)
    if current == FILE_BEFORE_SHA256[relative]:
        return "before"
    expected = FILE_AFTER_SHA256[relative]
    if not expected.startswith("__") and current == expected:
        return "after"
    raise PreconditionsError(
        f"Hildebrandt file drift: {relative}; expected reviewed before/after, actual {current}"
    )


def page_ranges(spec: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "printed_pages": {"start": start, "end": end},
            "pdf_pages": {"start": pdf_start, "end": pdf_end},
            "page_map_status": "visually_verified_primary_audit_pending_independent_review",
        }
        for start, end, pdf_start, pdf_end in spec["ranges"]
    ]


def transform_position(row: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(row)
    wanted = node_id(result)
    spec = POSITION_SPECS[wanted]
    result["description"] = spec["description"]
    data = metadata(result)
    for key in (
        "page",
        "quote_verbatim",
        "verified_reference",
        "citation_verified",
        "e2_verified_at",
        "e2_verified_by",
        "e2_publication_id",
        "ingestion_debt_2026_08_17_schema_normalised",
    ):
        data.pop(key, None)
    data["publication_id"] = PUBLICATION_ID
    # Retain the canonical compatibility key consumed by the central ingestion
    # gate while also exposing the clearer publication_id field.
    data["scholarly_work_id"] = PUBLICATION_ID
    data["source_id"] = SOURCE_ID
    data["manifestation_id"] = MANIFESTATION_ID
    data["source_artifact"] = {
        "path": PDF_RELATIVE,
        "sha256": PDF_SHA256,
        "media_type": "application/pdf",
        "doi": DOI,
    }
    data["page_range"] = page_ranges(spec)
    data["claim_ids"] = spec["claim_ids"]
    data["claim_components"] = spec["components"]
    data["claim_status"] = "in_review"
    data["citability"] = "discoverable_only"
    data["confidence"] = "in_review_pending_independent_review"
    data["citation_verdict"] = "page_mapped_secondary_claim_pending_review"
    data["evidence_role"] = "secondary_scholarly_position"
    data["quotation_status"] = (
        "legacy_verbatim_removed_copyright_bounded_paraphrase_only"
    )
    data["rights"] = {
        "access_status": "open_access",
        "rights_statement": RIGHTS_STATEMENT,
        "license_status": "no_explicit_reuse_licence_archived",
        "reuse_status": "unverified_do_not_republish",
    }
    data["review_status"] = {
        "deep_read": "complete",
        "independent": "pending",
        "adversarial": "pending",
        "human_signoff": "pending",
        "primary_ancient_recollation": "pending",
    }
    data[STAMP] = True
    set_metadata(result, data)
    result["updated_at"] = NOW
    return result


def transform_publication(row: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(row)
    result["label"] = f"Hildebrandt 2022 — {TITLE}"
    result["description"] = (
        "Article in Studia Philosophica Estonica 15 (2022), pp. 25-44. "
        "Hildebrandt argues that Alexander's De fato XXI Lazy Argument is more "
        "successful than the ordinary objections she discusses, because belief in "
        "determinism may create motivational risk for epistemically limited agents. "
        "This is an attributed comparative assessment, not a measured consensus or "
        "a conclusive proof."
    )
    data = metadata(result)
    for key in (
        "license",
        "local_pdf_path",
        "citation_verified",
        "verified_reference",
    ):
        data.pop(key, None)
    data.update(
        {
            "title": TITLE,
            "author": AUTHOR,
            "year": 2022,
            "type": "article",
            "journal": "Studia Philosophica Estonica",
            "volume": 15,
            "pages": "25-44",
            "doi": DOI,
            "issn": ISSN,
            "url": OFFICIAL_URL,
            "bibtex_key": BIBTEX_KEY,
            "manifestation_id": MANIFESTATION_ID,
            "source_artifact_sha256": PDF_SHA256,
            "source_artifact_path": PDF_RELATIVE,
            "pdf_page_count": PDF_PAGES,
            "printed_page_range": {"start": 25, "end": 44},
            "pdf_page_range": {"start": 1, "end": 20},
            "page_map": {
                "rule": "PDF page = printed page - 24",
                "status": "visually_verified_primary_audit_pending_independent_review",
            },
            "access_status": "open_access",
            "rights_statement": RIGHTS_STATEMENT,
            "license_status": "no_explicit_reuse_licence_archived",
            "reuse_status": "unverified_do_not_republish",
            "deep_read_status": "complete_pending_independent_review",
            "citation_verdict": "bibliographic_identity_source_checked_claims_in_review",
            STAMP: True,
        }
    )
    set_metadata(result, data)
    result["updated_at"] = NOW
    return result


def transform_scholar(row: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(row)
    result["description"] = (
        "Scholar of ancient philosophy working on Stoic determinism, fate, moral "
        "responsibility and Alexander of Aphrodisias. The 2022 article records "
        "affiliations with Humboldt University Berlin and Technical University "
        "Dortmund; its acknowledgements time-bind a Humboldt visiting professorship "
        "to November 2022 through September 2023. These are historical publication "
        "contexts, not current-contact information."
    )
    data = metadata(result)
    for key in (
        "affiliations",
        "verification_sources",
        "citation_verified",
        "verified_reference",
        "citation_verdict",
    ):
        data.pop(key, None)
    data["affiliations_at_publication"] = [
        {
            "institution": "Technical University Dortmund, Department of Philosophy and Political Science",
            "temporal_scope": "affiliation printed in the 2022 article",
        },
        {
            "institution": "Humboldt University Berlin, Department of Philosophy",
            "temporal_scope": (
                "affiliation printed in the 2022 article; visiting professorship "
                "November 2022-September 2023 noted in acknowledgements"
            ),
        },
    ]
    data["identity_source"] = {
        "publication_id": PUBLICATION_ID,
        "manifestation_id": MANIFESTATION_ID,
        "source_artifact_sha256": PDF_SHA256,
        "status": "source_checked_time_bounded_no_contact_data",
    }
    data[STAMP] = True
    set_metadata(result, data)
    result["updated_at"] = NOW
    return result


def transform_nodes(
    rows: list[dict[str, Any]], *, state: str
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], Counter[str]]:
    by_id = {node_id(row): row for row in rows}
    if len(by_id) != len(rows):
        raise PreconditionsError("duplicate KG node identity")
    touched = {PUBLICATION_ID, SCHOLAR_ID, *POSITION_IDS}
    if missing := sorted(touched - by_id.keys()):
        raise PreconditionsError(f"missing Hildebrandt KG nodes: {missing}")
    result = copy.deepcopy(rows)
    quarantine: list[dict[str, Any]] = []
    for index, row in enumerate(result):
        wanted = node_id(row)
        if wanted == PUBLICATION_ID:
            desired = transform_publication(row)
        elif wanted == SCHOLAR_ID:
            desired = transform_scholar(row)
        elif wanted in POSITION_SPECS:
            desired = transform_position(row)
        else:
            continue
        if row != desired:
            result[index] = desired
            quarantine.append({"record_type": "kg_node_before", "record": row})
    changed = {
        node_id(old)
        for old, new in zip(rows, result, strict=True)
        if old != new
    }
    expected = touched if state == "before" else set()
    if changed != expected:
        raise PreconditionsError(
            f"Hildebrandt node diff mismatch: {sorted(changed ^ expected)}"
        )
    validate_nodes(result)
    return (
        result,
        quarantine,
        Counter({"kg_nodes_modified": len(changed)}) if changed else Counter(),
    )


def validate_nodes(rows: list[dict[str, Any]]) -> None:
    by_id = {node_id(row): row for row in rows}
    publication = metadata(by_id[PUBLICATION_ID])
    if publication.get("title") != TITLE or publication.get("author") != AUTHOR:
        raise RuntimeError("Hildebrandt publication identity is wrong")
    if publication.get("license_status") != "no_explicit_reuse_licence_archived":
        raise RuntimeError("Hildebrandt publication infers a reuse licence")
    if publication.get("reuse_status") != "unverified_do_not_republish":
        raise RuntimeError("Hildebrandt rights are not fail-closed")
    scholar_blob = json.dumps(by_id[SCHOLAR_ID], ensure_ascii=False)
    if any(value in scholar_blob for value in ("Emil-Figge", "44227", "@")):
        raise RuntimeError("Hildebrandt scholar node retains public contact data")
    for wanted in POSITION_IDS:
        data = metadata(by_id[wanted])
        if data.get("citability") != "discoverable_only":
            raise RuntimeError(f"Hildebrandt position remains citable: {wanted}")
        if data.get("claim_status") != "in_review":
            raise RuntimeError(f"Hildebrandt position overstates review: {wanted}")
        if data.get("manifestation_id") != MANIFESTATION_ID:
            raise RuntimeError(f"Hildebrandt manifestation missing: {wanted}")
        if data.get("page_range") != page_ranges(POSITION_SPECS[wanted]):
            raise RuntimeError(f"Hildebrandt page range wrong: {wanted}")
        forbidden = {
            "page",
            "quote_verbatim",
            "verified_reference",
            "citation_verified",
            "ingestion_debt_2026_08_17_schema_normalised",
        }
        if forbidden & data.keys():
            raise RuntimeError(f"Hildebrandt legacy verified fields survived: {wanted}")
    central = by_id[POSITION_IDS[0]]["description"].lower()
    if "against the scholarly consensus" in central or "one succeeds" in central:
        raise RuntimeError("Hildebrandt central thesis remains overstated")
    negative = by_id[POSITION_IDS[6]]["description"].lower()
    if "not proof of absolute historical absence" not in negative:
        raise RuntimeError("Hildebrandt negative finding is unbounded")


def transform_edges(
    rows: list[dict[str, Any]], *, state: str
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], Counter[str]]:
    by_id = {edge_id(row): row for row in rows}
    if len(by_id) != len(rows):
        raise PreconditionsError("duplicate KG edge identity")
    if missing := sorted(AUTHOR_EDGE_IDS - by_id.keys()):
        raise PreconditionsError(f"missing Hildebrandt author edges: {missing}")
    result = copy.deepcopy(rows)
    quarantine: list[dict[str, Any]] = []
    for index, row in enumerate(result):
        wanted = edge_id(row)
        if wanted not in AUTHOR_EDGE_IDS:
            continue
        desired = copy.deepcopy(row)
        source = str(desired.get("source_id") or desired.get("source") or "")
        target = str(desired.get("target_id") or desired.get("target") or "")
        if source not in POSITION_IDS or target != SCHOLAR_ID:
            raise PreconditionsError(f"unexpected Hildebrandt attribution edge: {wanted}")
        desired["relation"] = "authored_by"
        desired["metadata"] = {
            "attribution_scope": "modern_scholarly_position",
            "source_publication_id": PUBLICATION_ID,
            "manifestation_id": MANIFESTATION_ID,
            "source_artifact_sha256": PDF_SHA256,
            "claim_status": "in_review",
            "citability": "discoverable_only",
            STAMP: True,
        }
        if row != desired:
            result[index] = desired
            quarantine.append({"record_type": "kg_edge_before", "record": row})
    changed = {
        edge_id(old)
        for old, new in zip(rows, result, strict=True)
        if old != new
    }
    expected = set(AUTHOR_EDGE_IDS) if state == "before" else set()
    if changed != expected:
        raise PreconditionsError(
            f"Hildebrandt edge diff mismatch: {sorted(changed ^ expected)}"
        )
    validate_edges(result)
    return (
        result,
        quarantine,
        Counter({"kg_edges_modified": len(changed)}) if changed else Counter(),
    )


def validate_edges(rows: list[dict[str, Any]]) -> None:
    by_id = {edge_id(row): row for row in rows}
    for wanted in AUTHOR_EDGE_IDS:
        row = by_id[wanted]
        if row.get("relation") != "authored_by":
            raise RuntimeError(f"Hildebrandt edge direction wrong: {wanted}")
        if row.get("metadata", {}).get("claim_status") != "in_review":
            raise RuntimeError(f"Hildebrandt edge overstates review: {wanted}")
    position_authors = {
        str(row.get("source_id") or row.get("source")): str(
            row.get("target_id") or row.get("target")
        )
        for row in rows
        if str(row.get("source_id") or row.get("source")) in POSITION_IDS
        and row.get("relation") == "authored_by"
    }
    if position_authors != dict.fromkeys(POSITION_IDS, SCHOLAR_ID):
        raise RuntimeError("Hildebrandt position authorship is incomplete")


def append_note(note: str, addition: str) -> str:
    if addition in note:
        return note
    separator = " " if note and not note.endswith(" ") else ""
    return note + separator + addition


def transform_citations(
    rows: list[dict[str, Any]], *, state: str
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], Counter[str]]:
    keys = Counter(citation_key(row) for row in rows)
    expected_keys = {"\x1f".join(key) for key in CITATION_TARGETS}
    if missing := sorted(key for key in expected_keys if keys[key] != 1):
        raise PreconditionsError(f"Hildebrandt citation precondition mismatch: {missing}")
    result = copy.deepcopy(rows)
    quarantine: list[dict[str, Any]] = []
    for index, row in enumerate(result):
        pair = (
            str(row.get("kg_node_id") or ""),
            str(row.get("passage_id") or ""),
            str(row.get("citation_type") or ""),
        )
        action = CITATION_TARGETS.get(pair)
        if action is None:
            continue
        desired = copy.deepcopy(row)
        note = str(desired.get("notes") or "")
        if action == "cicero_phi054":
            note = note.replace("phi0474.phi049", "phi0474.phi054")
            note = note.replace("phi0474_phi049", "phi0474_phi054")
        else:
            note = append_note(note, DEBT_NOTES[action])
        desired["notes"] = note
        if row != desired:
            result[index] = desired
            quarantine.append(
                {"record_type": "corpus_citation_before", "record": row}
            )
    changed = {
        citation_key(old)
        for old, new in zip(rows, result, strict=True)
        if old != new
    }
    expected = expected_keys if state == "before" else set()
    if changed != expected:
        raise PreconditionsError(
            f"Hildebrandt citation diff mismatch: {sorted(changed ^ expected)}"
        )
    validate_citations(result)
    return (
        result,
        quarantine,
        Counter({"corpus_citations_modified": len(changed)}) if changed else Counter(),
    )


def validate_citations(rows: list[dict[str, Any]]) -> None:
    hildebrandt = [
        row for row in rows if str(row.get("kg_node_id") or "") in POSITION_IDS
    ]
    if len(hildebrandt) != 16:
        raise RuntimeError(f"expected 16 Hildebrandt citation routes; found {len(hildebrandt)}")
    if any(row.get("citation_type") == "direct" for row in hildebrandt):
        raise RuntimeError("Hildebrandt citation was promoted to direct")
    by_pair = {
        (
            str(row.get("kg_node_id")),
            str(row.get("passage_id")),
            str(row.get("citation_type")),
        ): row
        for row in hildebrandt
    }
    for pair, action in CITATION_TARGETS.items():
        note = str(by_pair[pair].get("notes") or "")
        if action == "cicero_phi054" and "phi049" in note:
            raise RuntimeError(f"stale Cicero phi049 survived: {pair}")
        if action.startswith("de_fato") and DEBT_NOTES[action] not in note:
            raise RuntimeError(f"De fato corruption debt missing: {pair}")


def desired_builder_bytes(current: bytes) -> bytes:
    text = current.decode("utf-8")
    if NEW_BUILDER_BLOCK in text and OLD_BUILDER_BLOCK not in text:
        return current
    if text.count(OLD_BUILDER_BLOCK) != 1:
        raise PreconditionsError("exact Hildebrandt builder block not found")
    return text.replace(OLD_BUILDER_BLOCK, NEW_BUILDER_BLOCK).encode("utf-8")


def execute_candidate_literature_builder(
    builder_bytes: bytes, root: Path
) -> list[dict[str, Any]]:
    namespace: dict[str, Any] = {
        "__file__": str(root / BUILDER_RELATIVE),
        "__name__": "hildebrandt_candidate_literature_builder",
    }
    exec(
        compile(builder_bytes.decode("utf-8"), str(root / BUILDER_RELATIVE), "exec"),
        namespace,
    )
    rows = namespace["build_manifest"]()
    if not isinstance(rows, list):
        raise RuntimeError("candidate literature builder returned no row list")
    return rows


def serialize_jsonl(rows: list[dict[str, Any]]) -> bytes:
    return (
        "".join(
            json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows
        )
    ).encode("utf-8")


def serialize_jsonl_preserving(
    path: Path,
    before: list[dict[str, Any]],
    after: list[dict[str, Any]],
    key: Callable[[dict[str, Any]], str],
) -> bytes:
    lines = [
        line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()
    ] if path.exists() else []
    if len(lines) != len(before):
        raise PreconditionsError(f"line-count drift while staging {path}")
    desired = {key(row): row for row in after}
    if len(desired) != len(after):
        raise RuntimeError(f"duplicate desired identity in {path}")
    output: list[str] = []
    seen: set[str] = set()
    for line, old in zip(lines, before, strict=True):
        wanted = key(old)
        if wanted not in desired:
            continue
        new = desired[wanted]
        output.append(
            line if old == new else json.dumps(new, ensure_ascii=False, sort_keys=True)
        )
        seen.add(wanted)
    for wanted in sorted(desired.keys() - seen):
        output.append(json.dumps(desired[wanted], ensure_ascii=False, sort_keys=True))
    return ("\n".join(output) + ("\n" if output else "")).encode("utf-8")


def transform_literature(
    root: Path,
    builder_before: bytes,
    manifest_before: list[dict[str, Any]],
    *,
    state: str,
) -> tuple[bytes, list[dict[str, Any]], list[dict[str, Any]], Counter[str]]:
    builder_after = desired_builder_bytes(builder_before)
    manifest_after = execute_candidate_literature_builder(builder_after, root)
    before_rows = {row["artifact_id"]: row for row in manifest_before}
    after_rows = {row["artifact_id"]: row for row in manifest_after}
    changed = {
        wanted
        for wanted in set(before_rows) & set(after_rows)
        if before_rows[wanted] != after_rows[wanted]
    }
    expected = {LITERATURE_ARTIFACT_ID} if state == "before" else set()
    if changed != expected or set(before_rows) != set(after_rows):
        raise PreconditionsError(
            f"literature builder diff escaped Hildebrandt row: {changed}"
        )
    row = after_rows[LITERATURE_ARTIFACT_ID]
    if row.get("creators") != [AUTHOR] or row.get("title") != TITLE:
        raise RuntimeError("Hildebrandt literature identity is wrong")
    if row.get("audit_status") != "deep_read_wave1":
        raise RuntimeError("Hildebrandt literature deep-read status missing")
    if row.get("license_status") != "no_explicit_reuse_licence_archived":
        raise RuntimeError("Hildebrandt literature manifest infers a licence")
    quarantine: list[dict[str, Any]] = []
    counts = Counter()
    if state == "before":
        quarantine.extend(
            [
                {
                    "record_type": "literature_manifest_row_before",
                    "record": before_rows[LITERATURE_ARTIFACT_ID],
                },
                {
                    "record_type": "literature_builder_before_summary",
                    "file_sha256": sha256_bytes(builder_before),
                    "old_block_sha256": sha256_bytes(OLD_BUILDER_BLOCK.encode()),
                },
            ]
        )
        counts.update(
            {"literature_builder_modified": 1, "literature_manifest_rows_modified": 1}
        )
    return builder_after, manifest_after, quarantine, counts


def scholarly_manifest_row() -> dict[str, Any]:
    return {
        "manifest_schema_version": "2.0.0",
        "publication_dir": SCHOLARLY_PUBLICATION_DIR,
        "bibtex_key": BIBTEX_KEY,
        "kg_publication_id": PUBLICATION_ID,
        "manifestation_id": MANIFESTATION_ID,
        "title": TITLE,
        "author": AUTHOR,
        "year_original": 2022,
        "year_edition_used": 2022,
        "edition_used": "Studia Philosophica Estonica 15 (2022), printed pages 25-44",
        "language_primary": "eng",
        "languages_secondary": ["grc", "lat"],
        "kg_ingestion_status": "partial",
        "ingestion_scope": (
            "Eight existing scholarly positions page-mapped and kept discovery-only; "
            "independent claim review and ancient-primary recollation remain incomplete."
        ),
        "kg_ingestion_batches": ["hildebrandt_p0_20260824"],
        "kg_node_count": 10,
        "added_to_archive": "2026-08-24",
        "last_updated": "2026-08-24",
        "pdf_sha256": PDF_SHA256,
        "pdf_size_bytes": PDF_BYTES,
        "page_count": PDF_PAGES,
        "printed_page_range": {"start": 25, "end": 44},
        "pdf_page_range": {"start": 1, "end": 20},
        "page_map": "PDF page = printed page - 24",
        "page_map_status": "visually_verified_primary_audit_pending_independent_review",
        "doi": DOI,
        "issn_online": ISSN,
        "journal": "Studia Philosophica Estonica",
        "volume": 15,
        "access_status": "open_access",
        "access_url": OFFICIAL_URL,
        "rights_statement": RIGHTS_STATEMENT,
        "license_status": "no_explicit_reuse_licence_archived",
        "reuse_status": "unverified_do_not_republish",
        "deep_read_status": "complete_pending_independent_review",
        "quotation_policy": "paraphrase_only_do_not_republish_article_text",
        STAMP: True,
    }


def transform_scholarly_manifest(
    rows: list[dict[str, Any]], *, state: str
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], Counter[str]]:
    result = copy.deepcopy(rows)
    desired = scholarly_manifest_row()
    matches = [
        row for row in result if row.get("publication_dir") == SCHOLARLY_PUBLICATION_DIR
    ]
    if not matches:
        if state != "before":
            raise PreconditionsError("applied Hildebrandt scholarly manifest disappeared")
        result.append(desired)
        quarantine = [
            {
                "record_type": "scholarly_manifest_absence_before",
                "publication_dir": SCHOLARLY_PUBLICATION_DIR,
            }
        ]
        counts = Counter({"scholarly_manifest_rows_added": 1})
    elif len(matches) == 1 and matches[0] == desired:
        quarantine = []
        counts = Counter()
    else:
        raise PreconditionsError("conflicting Hildebrandt scholarly manifest row")
    from scripts.check_scholarly_sources_manifest import validate

    errors = validate(result)
    if errors:
        raise RuntimeError(f"scholarly manifest invalid: {errors}")
    return result, quarantine, counts


def bib_entry(text: str, key: str) -> str:
    pattern = re.compile(
        rf"^@[A-Za-z]+\{{{re.escape(key)},\n.*?^\}}\n", re.MULTILINE | re.DOTALL
    )
    matches = pattern.findall(text)
    if len(matches) != 1:
        raise PreconditionsError(f"expected one BibTeX entry for {key}; found {len(matches)}")
    return matches[0]


def transform_bibliography(
    bib_before: bytes,
    report_before: bytes,
    nodes_after: list[dict[str, Any]],
    *,
    state: str,
) -> tuple[bytes, bytes, list[dict[str, Any]], Counter[str]]:
    from scripts.export_publications_bibtex import (
        bibtex_entry_keys,
        build_companion_report,
        publication_to_bibtex,
    )

    publication = next(row for row in nodes_after if node_id(row) == PUBLICATION_ID)
    desired_entry, missing = publication_to_bibtex(publication)
    if missing:
        raise RuntimeError(f"Hildebrandt BibTeX entry missing fields: {missing}")
    desired_key = bibtex_entry_keys(desired_entry)[0]
    if desired_key != BIBTEX_KEY:
        raise RuntimeError(f"Hildebrandt BibTeX key drift: {desired_key}")
    before_text = bib_before.decode("utf-8")
    current_entry = bib_entry(before_text, BIBTEX_KEY)
    bib_after_text = before_text.replace(current_entry, desired_entry)
    if before_text.count(current_entry) != 1:
        raise PreconditionsError("Hildebrandt BibTeX replacement is ambiguous")
    report = build_companion_report(
        nodes_after,
        bib_after_text,
        generation_mode="hildebrandt_bibliography_surgical_snapshot_transform",
        baseline_bibtex_sha256=FILE_BEFORE_SHA256[BIB_RELATIVE],
    )
    report_after = (
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    bib_after = bib_after_text.encode("utf-8")
    bib_changed = bib_before != bib_after
    report_changed = report_before != report_after
    expected = state == "before"
    if bib_changed != expected or report_changed != expected:
        raise PreconditionsError(
            f"Hildebrandt bibliography state mismatch: bib={bib_changed}, report={report_changed}"
        )
    if TITLE not in desired_entry or "Hildebrandt 2022 —" in desired_entry:
        raise RuntimeError("Hildebrandt BibTeX title remains a UI label")
    if report.get("bibtex_sha256") != sha256_bytes(bib_after):
        raise RuntimeError("Hildebrandt BibTeX report hash mismatch")
    quarantine: list[dict[str, Any]] = []
    counts = Counter()
    if state == "before":
        quarantine.extend(
            [
                {"record_type": "bibliography_entry_before", "raw_text": current_entry},
                {
                    "record_type": "bibliography_report_before",
                    "raw_text": report_before.decode("utf-8"),
                    "sha256": sha256_bytes(report_before),
                },
            ]
        )
        counts.update({"bibliography_entries_modified": 1, "bibliography_reports_modified": 1})
    return bib_after, report_after, quarantine, counts


def registry_source_record() -> dict[str, Any]:
    targets = [PUBLICATION_ID, SCHOLAR_ID, *POSITION_IDS]
    return {
        "record_type": "source",
        "source_id": SOURCE_ID,
        "source_kind": "secondary_publication",
        "display_label": "Hildebrandt, Alexander of Aphrodisias’ Lazy Arguments against Stoic Determinism",
        "canonical_title": TITLE,
        "creators": [AUTHOR],
        "date_display": "2022",
        "languages": ["eng", "grc", "lat"],
        "traditions": ["aristotelian_peripatetic", "stoic"],
        "topics": ["fate_necessity", "choice_will", "moral_responsibility", "lazy_argument"],
        "scope_decision": "include_core",
        "identity_status": "bibliography_verified",
        "canonical_identifiers": {
            "kg_publication_id": PUBLICATION_ID,
            "doi": DOI,
            "manifestation_id": MANIFESTATION_ID,
            "local_pdf_sha256": PDF_SHA256,
            "pages": "25-44",
        },
        "acquisition": {
            "status": "archived_verified",
            "manifest_publication_dirs": [SCHOLARLY_PUBLICATION_DIR],
            "artifacts": [
                {"locator": PDF_RELATIVE, "role": "source_file", "sha256": PDF_SHA256},
                {"locator": AUDIT_RELATIVE, "role": "audit_report", "sha256": AUDIT_SHA256},
                {"locator": OFFICIAL_URL, "role": "catalog_record", "accessed_at": ACCESSED_AT},
            ],
        },
        "coverage": {
            "state": "partial",
            "kg_node_ids": targets,
            "basis": (
                "The complete article is deep-read and eight positions are page-mapped, "
                "but independent/adversarial claim review and ancient-primary recollation "
                "remain incomplete."
            ),
            "last_audited": "2026-08-24",
        },
        "provenance": [
            {"locator": PDF_RELATIVE, "role": "source_file", "sha256": PDF_SHA256},
            {"locator": AUDIT_RELATIVE, "role": "audit_report", "sha256": AUDIT_SHA256},
            {"locator": OFFICIAL_URL, "role": "catalog_record", "accessed_at": ACCESSED_AT},
        ],
        "notes": (
            "Open public access is recorded separately from reuse rights. The PDF "
            "states © All Copyright Author and no explicit reuse licence is archived. "
            "Only copyright-safe paraphrases and locators are registered."
        ),
    }


def evidence_record(
    position_id: str,
    *,
    evidence_id: str | None = None,
    ranges_override: list[tuple[int, int, int, int]] | None = None,
) -> dict[str, Any]:
    spec = POSITION_SPECS[position_id]
    ranges = ranges_override or spec["ranges"]
    printed_label = ", ".join(
        str(start) if start == end else f"{start}-{end}"
        for start, end, _pdf_start, _pdf_end in ranges
    )
    pdf_label = ", ".join(
        str(start) if start == end else f"{start}-{end}"
        for _printed_start, _printed_end, start, end in ranges
    )
    locator: dict[str, Any] = {
        "canonical_locus": (
            f"Hildebrandt 2022, printed pp. {printed_label}; PDF pp. {pdf_label}"
        ),
        "edition_or_witness": MANIFESTATION_ID,
        "page_map_status": "visually_verified",
    }
    if len(ranges) == 1:
        start, end, pdf_start, pdf_end = ranges[0]
        locator["printed_pages"] = {"start": start, "end": end}
        locator["pdf_pages"] = {"start": pdf_start, "end": pdf_end}
    roles = "; ".join(component["role"] for component in spec["components"])
    return {
        "record_type": "evidence",
        "evidence_id": evidence_id or EVIDENCE_IDS[position_id],
        "source_id": SOURCE_ID,
        "evidence_kind": "secondary_claim",
        "claim_text": spec["description"],
        "attestation": "reported_interpretation",
        "claim_status": "in_review",
        "locator": locator,
        "quotation": {"status": "paraphrase_only", "language": "eng"},
        "kg_targets": [position_id],
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
            f"Evidence roles: {roles}. Copyright-safe paraphrase only; ancient loci "
            "remain routes for primary recollation, not direct verified evidence."
        ),
    }


def issue_records() -> list[dict[str, Any]]:
    artifacts = [
        {"locator": AUDIT_RELATIVE, "role": "audit_report", "sha256": AUDIT_SHA256},
        {"locator": PDF_RELATIVE, "role": "source_file", "sha256": PDF_SHA256},
    ]
    return [
        {
            "record_type": "issue",
            "issue_id": CLAIM_ISSUE_ID,
            "issue_type": "provenance_gap",
            "severity": "high",
            "factual_risk": True,
            "status": "open",
            "summary": (
                "The local Hildebrandt article identity, pages and rights are repaired, "
                "but eight scholarly positions remain secondary interpretations pending "
                "independent, adversarial and human review."
            ),
            "affected_ids": [SOURCE_ID, PUBLICATION_ID, SCHOLAR_ID, *POSITION_IDS],
            "affected_count": 11,
            "evidence_artifacts": artifacts,
            "resolution_criteria": (
                "Independently inspect printed pages 25-42, adjudicate attribution and "
                "semantic entailment for every position, retain paraphrase-only rights, "
                "and complete adversarial and human scholarly review before citability."
            ),
        },
        {
            "record_type": "issue",
            "issue_id": TEXT_ISSUE_ID,
            "issue_type": "source_text_divergence",
            "severity": "critical",
            "factual_risk": True,
            "status": "open",
            "summary": (
                f"Alexander De fato 8 corpus UUID {DE_FATO_8_UUID} contains visible "
                f"duplicated tokens and De fato 11 UUID {DE_FATO_11_UUID} duplicates "
                "a final segment. The routes remain useful for discovery, but cannot "
                "support direct primary verification."
            ),
            "affected_ids": [
                "src_anc_alexander_de_fato",
                "work_de_fato_alexander_c200ce_o6p7q8r9",
                POSITION_IDS[1],
                POSITION_IDS[7],
            ],
            "affected_count": 4,
            "evidence_artifacts": [
                {"locator": "data/corpus/passages.jsonl", "role": "catalog_record"},
                {"locator": AUDIT_RELATIVE, "role": "audit_report", "sha256": AUDIT_SHA256},
            ],
            "resolution_criteria": (
                "Recollate De fato 8 and 11 against the pinned OGL/Bruns edition, repair "
                "corpus text in a separate authorized transaction, preserve UUID/locus "
                "identity, and revalidate every dependent citation before primary use."
            ),
        },
    ]


def append_unique(values: list[str], value: str) -> list[str]:
    return values if value in values else [*values, value]


def desired_wave(row: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(row)
    wanted = result.get("wave_id")
    if wanted == WAVE_SECONDARY:
        result["source_ids"] = append_unique(result["source_ids"], SOURCE_ID)
        for evidence_id in sorted(ALL_EVIDENCE_IDS):
            result["evidence_ids"] = append_unique(result["evidence_ids"], evidence_id)
        result["issue_ids"] = append_unique(result["issue_ids"], CLAIM_ISSUE_ID)
        result["blocked_by"] = append_unique(result["blocked_by"], CLAIM_ISSUE_ID)
        result["exit_criteria"] = append_unique(
            result["exit_criteria"],
            (
                "Hildebrandt's eight positions retain exact page ranges, source roles, "
                "copyright-bounded paraphrases and discovery-only status until independent, "
                "adversarial and human review."
            ),
        )
    elif wanted == WAVE_FACTUAL:
        result["issue_ids"] = append_unique(result["issue_ids"], TEXT_ISSUE_ID)
        result["exit_criteria"] = append_unique(
            result["exit_criteria"],
            (
                "Alexander De fato 8 and 11 duplicated-text corruptions are recollated "
                "and repaired in a separate corpus transaction before direct citation."
            ),
        )
    return result


def transform_registry(
    sources: list[dict[str, Any]],
    evidence: list[dict[str, Any]],
    issues: list[dict[str, Any]],
    waves: list[dict[str, Any]],
    *,
    state: str,
) -> tuple[dict[str, list[dict[str, Any]]], list[dict[str, Any]], Counter[str]]:
    result = {
        "sources": copy.deepcopy(sources),
        "evidence": copy.deepcopy(evidence),
        "issues": copy.deepcopy(issues),
        "waves": copy.deepcopy(waves),
    }
    quarantine: list[dict[str, Any]] = []
    counts = Counter()

    source = registry_source_record()
    existing_source = next(
        (row for row in result["sources"] if row.get("source_id") == SOURCE_ID), None
    )
    if existing_source is None:
        if state != "before":
            raise PreconditionsError("applied Hildebrandt registry source disappeared")
        result["sources"].append(source)
        quarantine.append({"record_type": "registry_source_absence_before", "source_id": SOURCE_ID})
        counts["registry_sources_added"] = 1
    elif existing_source != source:
        raise PreconditionsError("conflicting Hildebrandt registry source")

    desired_evidence = {
        EVIDENCE_IDS[wanted]: evidence_record(
            wanted,
            ranges_override=(
                [POSITION_SPECS[wanted]["ranges"][0]]
                if wanted == POSITION_IDS[0]
                else None
            ),
        )
        for wanted in POSITION_IDS
    }
    desired_evidence[HIL01_DEVELOPMENT_EVIDENCE_ID] = evidence_record(
        POSITION_IDS[0],
        evidence_id=HIL01_DEVELOPMENT_EVIDENCE_ID,
        ranges_override=[POSITION_SPECS[POSITION_IDS[0]]["ranges"][1]],
    )
    existing_evidence = {row.get("evidence_id"): row for row in result["evidence"]}
    for evidence_id, row in desired_evidence.items():
        old = existing_evidence.get(evidence_id)
        if old is None:
            if state != "before":
                raise PreconditionsError(f"applied Hildebrandt evidence disappeared: {evidence_id}")
            result["evidence"].append(row)
            quarantine.append(
                {"record_type": "registry_evidence_absence_before", "evidence_id": evidence_id}
            )
            counts["registry_evidence_added"] += 1
        elif old != row:
            raise PreconditionsError(f"conflicting Hildebrandt evidence: {evidence_id}")

    desired_issues = {row["issue_id"]: row for row in issue_records()}
    existing_issues = {row.get("issue_id"): row for row in result["issues"]}
    for issue_id, row in desired_issues.items():
        old = existing_issues.get(issue_id)
        if old is None:
            if state != "before":
                raise PreconditionsError(f"applied Hildebrandt issue disappeared: {issue_id}")
            result["issues"].append(row)
            quarantine.append(
                {"record_type": "registry_issue_absence_before", "issue_id": issue_id}
            )
            counts["registry_issues_added"] += 1
        elif old != row:
            raise PreconditionsError(f"conflicting Hildebrandt issue: {issue_id}")

    wave_by_id = {row.get("wave_id"): row for row in result["waves"]}
    for wave_id in (WAVE_SECONDARY, WAVE_FACTUAL):
        old = wave_by_id.get(wave_id)
        if old is None:
            raise PreconditionsError(f"missing Hildebrandt target wave: {wave_id}")
        desired = desired_wave(old)
        if old != desired:
            result["waves"][result["waves"].index(old)] = desired
            quarantine.append({"record_type": "registry_wave_before", "record": old})
            counts["registry_waves_modified"] += 1

    if state == "after" and counts:
        raise PreconditionsError(f"Hildebrandt registry after-state not idempotent: {counts}")
    validate_registry(result)
    return result, quarantine, counts


def validate_registry(result: dict[str, list[dict[str, Any]]]) -> None:
    source = next(row for row in result["sources"] if row.get("source_id") == SOURCE_ID)
    if source.get("coverage", {}).get("state") != "partial":
        raise RuntimeError("Hildebrandt registry source overstates coverage")
    evidence = {
        row.get("evidence_id"): row
        for row in result["evidence"]
        if row.get("evidence_id") in ALL_EVIDENCE_IDS
    }
    if set(evidence) != set(ALL_EVIDENCE_IDS):
        raise RuntimeError("Hildebrandt registry evidence incomplete")
    if any(
        row.get("claim_status") != "in_review"
        or row.get("quotation", {}).get("status") != "paraphrase_only"
        for row in evidence.values()
    ):
        raise RuntimeError("Hildebrandt registry evidence overstates review/rights")
    issues = {
        row.get("issue_id"): row
        for row in result["issues"]
        if row.get("issue_id") in {CLAIM_ISSUE_ID, TEXT_ISSUE_ID}
    }
    if set(issues) != {CLAIM_ISSUE_ID, TEXT_ISSUE_ID} or any(
        row.get("status") != "open" for row in issues.values()
    ):
        raise RuntimeError("Hildebrandt issues are not open")
    secondary = next(row for row in result["waves"] if row.get("wave_id") == WAVE_SECONDARY)
    factual = next(row for row in result["waves"] if row.get("wave_id") == WAVE_FACTUAL)
    if CLAIM_ISSUE_ID not in secondary.get("blocked_by", []):
        raise RuntimeError("Hildebrandt secondary wave is not blocked")
    if TEXT_ISSUE_ID not in factual.get("issue_ids", []):
        raise RuntimeError("Alexander text debt is absent from the factual wave")
    if TEXT_ISSUE_ID in factual.get("blocked_by", []):
        raise RuntimeError("the active factual wave cannot be blocked by its own issue")


def normative_schema_gate(
    root: Path, result: dict[str, list[dict[str, Any]]]
) -> dict[str, Any]:
    from jsonschema import Draft7Validator

    schema = json.loads(
        (root / "data/goals/sota/registry.schema.json").read_text(encoding="utf-8")
    )
    configs = {
        "source": ("sources", "source_id"),
        "evidence": ("evidence", "evidence_id"),
        "issue": ("issues", "issue_id"),
        "verification": ("verifications", "verification_id"),
        "wave": ("waves", "wave_id"),
    }
    registry_root = root / "data/goals/sota/registry"

    def collect(directory: str, key: str) -> dict[str, dict[str, Any]]:
        found: dict[str, dict[str, Any]] = {}
        for path in sorted((registry_root / directory).glob("*.jsonl")):
            for row in read_jsonl(path):
                found[str(row[key])] = row
        return found

    before = {
        record_type: collect(directory, key)
        for record_type, (directory, key) in configs.items()
    }
    after = copy.deepcopy(before)
    replacement = {
        "source": (read_jsonl(root / SOURCES_RELATIVE), result["sources"]),
        "evidence": (read_jsonl(root / EVIDENCE_RELATIVE), result["evidence"]),
        "issue": (read_jsonl(root / ISSUES_RELATIVE), result["issues"]),
        "wave": (read_jsonl(root / WAVES_RELATIVE), result["waves"]),
    }
    for record_type, (old_rows, new_rows) in replacement.items():
        key = configs[record_type][1]
        for row in old_rows:
            after[record_type].pop(str(row[key]), None)
        for row in new_rows:
            after[record_type][str(row[key])] = row
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

    def errors(collections: dict[str, dict[str, dict[str, Any]]]) -> set[tuple[Any, ...]]:
        found: set[tuple[Any, ...]] = set()
        for record_type, rows in collections.items():
            for identifier, row in rows.items():
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

    before_errors = errors(before)
    after_errors = errors(after)
    if new := after_errors - before_errors:
        raise PreconditionsError(f"Hildebrandt preview creates registry schema debt: {sorted(new)}")
    touched = {
        "source": {SOURCE_ID},
        "evidence": set(ALL_EVIDENCE_IDS),
        "issue": {CLAIM_ISSUE_ID, TEXT_ISSUE_ID},
        "wave": {WAVE_SECONDARY, WAVE_FACTUAL},
    }
    touched_errors: list[str] = []
    for record_type, identifiers in touched.items():
        for identifier in identifiers:
            for error in validators[record_type].iter_errors(after[record_type][identifier]):
                touched_errors.append(f"{record_type}:{identifier}:{error.message}")
    if touched_errors:
        raise PreconditionsError(f"Hildebrandt touched registry invalid: {touched_errors}")
    return {
        "baseline_errors": len(before_errors),
        "preview_errors": len(after_errors),
        "new_errors": len(after_errors - before_errors),
        "removed_errors": len(before_errors - after_errors),
        "touched_record_errors": len(touched_errors),
    }


def strict_ingestion_debt(
    before_nodes: list[dict[str, Any]],
    before_edges: list[dict[str, Any]],
    after_nodes: list[dict[str, Any]],
    after_edges: list[dict[str, Any]],
) -> dict[str, Any]:
    from scripts import check_ingestion_rules

    def debt(nodes: list[dict[str, Any]], edges: list[dict[str, Any]]) -> dict[str, int]:
        check_ingestion_rules.check(nodes, edges, None, None)
        current = list(check_ingestion_rules.violations)
        return {
            "block": sum(1 for row in current if row[1] == check_ingestion_rules.BLOCK),
            "warn": sum(1 for row in current if row[1] == check_ingestion_rules.WARN),
        }

    before = debt(before_nodes, before_edges)
    after = debt(after_nodes, after_edges)
    if after["block"] > before["block"] or after["warn"] > before["warn"]:
        raise PreconditionsError(
            f"Hildebrandt preview creates strict debt: before={before}, after={after}"
        )
    return {"before": before, "after_preview": after}


def raw_line_map(path: Path, key: Callable[[dict[str, Any]], str]) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        wanted = key(row)
        if wanted in result:
            raise PreconditionsError(f"duplicate raw-line identity in {path}: {wanted}")
        result[wanted] = line
    return result


def attach_raw_before_images(root: Path, quarantine: list[dict[str, Any]]) -> None:
    maps = {
        "kg_node_before": raw_line_map(root / NODES_RELATIVE, node_id),
        "kg_edge_before": raw_line_map(root / EDGES_RELATIVE, edge_id),
        "corpus_citation_before": raw_line_map(root / CITATIONS_RELATIVE, citation_key),
        "literature_manifest_row_before": raw_line_map(
            root / LITERATURE_RELATIVE, lambda row: str(row.get("artifact_id") or "")
        ),
        "registry_wave_before": raw_line_map(
            root / WAVES_RELATIVE, lambda row: str(row.get("wave_id") or "")
        ),
    }
    keyers = {
        "kg_node_before": lambda row: node_id(row["record"]),
        "kg_edge_before": lambda row: edge_id(row["record"]),
        "corpus_citation_before": lambda row: citation_key(row["record"]),
        "literature_manifest_row_before": lambda row: str(row["record"]["artifact_id"]),
        "registry_wave_before": lambda row: str(row["record"]["wave_id"]),
    }
    for row in quarantine:
        kind = row.get("record_type")
        if kind in maps:
            row["raw_line"] = maps[kind][keyers[kind](row)]


def validate_immutable_files(root: Path) -> None:
    if sha256_file(root / PDF_RELATIVE) != PDF_SHA256:
        raise PreconditionsError("Hildebrandt PDF hash drift")
    if sha256_file(root / AUDIT_RELATIVE) != AUDIT_SHA256:
        raise PreconditionsError("Hildebrandt audit hash drift")
    for relative, expected in IMMUTABLE_FILE_HASHES.items():
        actual = sha256_file(root / relative)
        if actual != expected:
            raise PreconditionsError(
                f"immutable Hildebrandt dependency drift: {relative}: {actual}"
            )
    passages = read_jsonl(root / "data/corpus/passages.jsonl")
    by_id = {str(row.get("passage_id") or row.get("id") or ""): row for row in passages}
    if "ἀργύριον ριον" not in str(by_id[DE_FATO_8_UUID].get("text_content") or ""):
        raise PreconditionsError("De fato 8 corruption marker unexpectedly changed")
    if "ὑφ’ ἡμῶν μὴ ἔχειν ἡμᾶς τοιαύτην" not in str(
        by_id[DE_FATO_11_UUID].get("text_content") or ""
    ):
        raise PreconditionsError("De fato 11 corruption marker unexpectedly changed")


def build_plan(root: Path = ROOT) -> RepairPlan:
    root = root.resolve()
    validate_immutable_files(root)
    states = {relative: file_state(root, relative) for relative in FILE_BEFORE_SHA256}
    if len(set(states.values())) != 1:
        raise PreconditionsError(f"mixed Hildebrandt transaction state: {states}")
    state = next(iter(states.values()))

    paths = {relative: root / relative for relative in FILE_BEFORE_SHA256}
    before_nodes = read_jsonl(paths[NODES_RELATIVE])
    before_edges = read_jsonl(paths[EDGES_RELATIVE])
    before_citations = read_jsonl(paths[CITATIONS_RELATIVE])
    builder_before = paths[BUILDER_RELATIVE].read_bytes()
    before_literature = read_jsonl(paths[LITERATURE_RELATIVE])
    before_scholarly = read_jsonl(paths[SCHOLARLY_RELATIVE])
    bib_before = paths[BIB_RELATIVE].read_bytes()
    bib_report_before = paths[BIB_REPORT_RELATIVE].read_bytes()
    before_sources = read_jsonl(paths[SOURCES_RELATIVE])
    before_evidence = read_jsonl(paths[EVIDENCE_RELATIVE])
    before_issues = read_jsonl(paths[ISSUES_RELATIVE])
    before_waves = read_jsonl(paths[WAVES_RELATIVE])

    nodes, node_quarantine, node_counts = transform_nodes(before_nodes, state=state)
    edges, edge_quarantine, edge_counts = transform_edges(before_edges, state=state)
    citations, citation_quarantine, citation_counts = transform_citations(
        before_citations, state=state
    )
    builder, literature, literature_quarantine, literature_counts = transform_literature(
        root, builder_before, before_literature, state=state
    )
    scholarly, scholarly_quarantine, scholarly_counts = transform_scholarly_manifest(
        before_scholarly, state=state
    )
    bib, bib_report, bib_quarantine, bib_counts = transform_bibliography(
        bib_before, bib_report_before, nodes, state=state
    )
    registry, registry_quarantine, registry_counts = transform_registry(
        before_sources, before_evidence, before_issues, before_waves, state=state
    )

    schema_debt = normative_schema_gate(root, registry)
    ingestion_debt = strict_ingestion_debt(before_nodes, before_edges, nodes, edges)

    outputs = {
        paths[NODES_RELATIVE]: serialize_jsonl_preserving(
            paths[NODES_RELATIVE], before_nodes, nodes, node_id
        ),
        paths[EDGES_RELATIVE]: serialize_jsonl_preserving(
            paths[EDGES_RELATIVE], before_edges, edges, edge_id
        ),
        paths[CITATIONS_RELATIVE]: serialize_jsonl_preserving(
            paths[CITATIONS_RELATIVE], before_citations, citations, citation_key
        ),
        paths[BUILDER_RELATIVE]: builder,
        paths[LITERATURE_RELATIVE]: serialize_jsonl(literature),
        paths[SCHOLARLY_RELATIVE]: serialize_jsonl_preserving(
            paths[SCHOLARLY_RELATIVE],
            before_scholarly,
            scholarly,
            lambda row: str(row.get("publication_dir") or ""),
        ),
        paths[BIB_RELATIVE]: bib,
        paths[BIB_REPORT_RELATIVE]: bib_report,
        paths[SOURCES_RELATIVE]: serialize_jsonl_preserving(
            paths[SOURCES_RELATIVE],
            before_sources,
            registry["sources"],
            lambda row: str(row.get("source_id") or ""),
        ),
        paths[EVIDENCE_RELATIVE]: serialize_jsonl_preserving(
            paths[EVIDENCE_RELATIVE],
            before_evidence,
            registry["evidence"],
            lambda row: str(row.get("evidence_id") or ""),
        ),
        paths[ISSUES_RELATIVE]: serialize_jsonl_preserving(
            paths[ISSUES_RELATIVE],
            before_issues,
            registry["issues"],
            lambda row: str(row.get("issue_id") or ""),
        ),
        paths[WAVES_RELATIVE]: serialize_jsonl_preserving(
            paths[WAVES_RELATIVE],
            before_waves,
            registry["waves"],
            lambda row: str(row.get("wave_id") or ""),
        ),
    }
    current_bytes = {path: path.read_bytes() for path in outputs}
    if state == "before":
        for path, payload in outputs.items():
            expected = FILE_AFTER_SHA256[str(path.relative_to(root))]
            if not expected.startswith("__") and sha256_bytes(payload) != expected:
                raise RuntimeError(f"Hildebrandt frozen after hash mismatch: {path}")
    elif any(current_bytes[path] != payload for path, payload in outputs.items()):
        raise PreconditionsError("Hildebrandt after-state is not idempotent")

    counts = Counter()
    for current in (
        node_counts,
        edge_counts,
        citation_counts,
        literature_counts,
        scholarly_counts,
        bib_counts,
        registry_counts,
    ):
        counts.update(current)
    quarantine = [
        *node_quarantine,
        *edge_quarantine,
        *citation_quarantine,
        *literature_quarantine,
        *scholarly_quarantine,
        *bib_quarantine,
        *registry_quarantine,
    ]
    if state == "before":
        attach_raw_before_images(root, quarantine)
    changed_paths = [
        str(path.relative_to(root))
        for path, payload in outputs.items()
        if current_bytes[path] != payload
    ]
    summary = {
        "mode": "dry_run",
        "status": (
            "ready_for_independent_review_no_apply" if state == "before" else "already_applied"
        ),
        "write_performed": False,
        "counts": dict(sorted(counts.items())),
        "changed_paths": changed_paths,
        "touched_node_ids": sorted({PUBLICATION_ID, SCHOLAR_ID, *POSITION_IDS}),
        "modified_edge_ids": sorted(AUTHOR_EDGE_IDS),
        "modified_citation_keys": sorted("\x1f".join(key) for key in CITATION_TARGETS),
        "corpus_passage_rows_modified": 0,
        "verification_records_added": 0,
        "quarantine_record_count": len(quarantine),
        "source_artifacts": {
            "pdf_sha256": PDF_SHA256,
            "audit_sha256": AUDIT_SHA256,
            "doi": DOI,
        },
        "snapshot_a_file_sha256": {
            str(path.relative_to(root)): sha256_bytes(payload)
            for path, payload in current_bytes.items()
        },
        "output_sha256_preview": {
            str(path.relative_to(root)): sha256_bytes(payload)
            for path, payload in outputs.items()
        },
        "before_record_hashes": {
            "nodes": {
                node_id(row["record"]): canonical_hash(row["record"])
                for row in node_quarantine
            },
            "edges": {
                edge_id(row["record"]): canonical_hash(row["record"])
                for row in edge_quarantine
            },
            "citations": {
                citation_key(row["record"]): canonical_hash(row["record"])
                for row in citation_quarantine
            },
        },
        "after_record_hashes": {
            "nodes": {
                node_id(row): canonical_hash(row)
                for row in nodes
                if node_id(row) in {PUBLICATION_ID, SCHOLAR_ID, *POSITION_IDS}
            },
            "edges": {
                edge_id(row): canonical_hash(row)
                for row in edges
                if edge_id(row) in AUTHOR_EDGE_IDS
            },
            "citations": {
                citation_key(row): canonical_hash(row)
                for row in citations
                if (
                    str(row.get("kg_node_id") or ""),
                    str(row.get("passage_id") or ""),
                    str(row.get("citation_type") or ""),
                )
                in CITATION_TARGETS
            },
        },
        "registry_schema_debt": schema_debt,
        "strict_ingestion_debt": ingestion_debt,
        "open_issue_ids": [CLAIM_ISSUE_ID, TEXT_ISSUE_ID],
        "review_status": {
            "primary_deep_read": "recorded",
            "independent": "not_performed_not_recorded",
            "adversarial": "not_performed_not_recorded",
            "human_signoff": "not_performed_not_recorded",
        },
        "immutable_hashes": IMMUTABLE_FILE_HASHES,
    }
    return RepairPlan(
        root=root,
        outputs=outputs,
        before_bytes=current_bytes,
        quarantine=quarantine,
        counts=counts,
        summary=summary,
    )


class InjectedTransactionAbort(BaseException):
    """Test-only hard-abort analogue caught by the recovery boundary."""


replace_path = os.replace


def fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def write_fsynced(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
    fsync_directory(path.parent)


def atomic_replace(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("wb", dir=path.parent, delete=False) as handle:
        temporary = Path(handle.name)
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
    try:
        replace_path(temporary, path)
        fsync_directory(path.parent)
    finally:
        temporary.unlink(missing_ok=True)


def snapshot_gate(before_bytes: dict[Path, bytes | None], *, label: str) -> None:
    drift = []
    for path, expected in before_bytes.items():
        actual = path.read_bytes() if path.exists() else None
        if actual != expected:
            drift.append(str(path))
    if drift:
        raise PreconditionsError(f"{label} snapshot drift: {drift}")


def journal_paths(root: Path) -> tuple[Path, Path]:
    return root / JOURNAL_RELATIVE, root / BACKUP_DIR_RELATIVE


def write_journal(path: Path, payload: dict[str, Any]) -> None:
    atomic_replace(
        path,
        (json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode(),
    )


def cleanup_transaction_files(root: Path) -> None:
    journal_path, backup_dir = journal_paths(root)
    if backup_dir.exists():
        shutil.rmtree(backup_dir)
        fsync_directory(backup_dir.parent)
    journal_path.unlink(missing_ok=True)
    fsync_directory(journal_path.parent)


def prepare_transaction(
    root: Path,
    outputs: dict[Path, bytes],
    before_bytes: dict[Path, bytes | None],
) -> dict[str, Any]:
    journal_path, backup_dir = journal_paths(root)
    if journal_path.exists() or backup_dir.exists():
        raise PreconditionsError("pending Hildebrandt transaction requires recovery")
    snapshot_gate(before_bytes, label="pre-stage")
    before_dir = backup_dir / "before"
    staged_dir = backup_dir / "staged"
    try:
        before_dir.mkdir(parents=True)
        staged_dir.mkdir(parents=True)
        fsync_directory(backup_dir.parent)
        fsync_directory(backup_dir)
        fsync_directory(before_dir)
        fsync_directory(staged_dir)
        entries = []
        changed = [path for path, payload in outputs.items() if before_bytes[path] != payload]
        for index, path in enumerate(changed):
            relative = str(path.relative_to(root))
            original = before_bytes[path]
            backup_name = f"{index:03d}.before"
            staged_name = f"{index:03d}.staged"
            if original is not None:
                write_fsynced(before_dir / backup_name, original)
            write_fsynced(staged_dir / staged_name, outputs[path])
            entries.append(
                {
                    "target": relative,
                    "before_exists": original is not None,
                    "before_sha256": sha256_bytes(original) if original is not None else None,
                    "backup": f"before/{backup_name}" if original is not None else None,
                    "desired_sha256": sha256_bytes(outputs[path]),
                    "staged": f"staged/{staged_name}",
                }
            )
        journal = {
            "schema_version": "1.0.0",
            "transaction_id": STAMP,
            "state": "prepared",
            "committed_targets": [],
            "entries": entries,
        }
        write_journal(journal_path, journal)
        return journal
    except BaseException:
        if backup_dir.exists():
            shutil.rmtree(backup_dir)
            fsync_directory(backup_dir.parent)
        journal_path.unlink(missing_ok=True)
        fsync_directory(journal_path.parent)
        raise


def restore_from_journal(root: Path, journal: dict[str, Any]) -> None:
    _, backup_dir = journal_paths(root)
    for entry in reversed(journal.get("entries", [])):
        target = root / entry["target"]
        if entry.get("before_exists"):
            backup = backup_dir / str(entry["backup"])
            if not backup.is_file():
                raise RuntimeError(f"missing Hildebrandt recovery backup: {backup}")
            payload = backup.read_bytes()
            if sha256_bytes(payload) != entry.get("before_sha256"):
                raise RuntimeError(f"corrupt Hildebrandt recovery backup: {backup}")
            atomic_replace(target, payload)
        else:
            target.unlink(missing_ok=True)
            fsync_directory(target.parent)


def recover_transaction(root: Path) -> str:
    journal_path, backup_dir = journal_paths(root)
    if not journal_path.exists():
        if backup_dir.exists():
            shutil.rmtree(backup_dir)
            fsync_directory(backup_dir.parent)
            return "orphaned_stage_discarded"
        return "none"
    journal = json.loads(journal_path.read_text(encoding="utf-8"))
    if journal.get("transaction_id") != STAMP:
        raise RuntimeError("foreign transaction journal at Hildebrandt path")
    if journal.get("state") == "prepared":
        cleanup_transaction_files(root)
        return "prepared_stage_discarded"
    entries = journal.get("entries") or []
    desired_complete = all(
        (root / entry["target"]).is_file()
        and sha256_file(root / entry["target"]) == entry.get("desired_sha256")
        for entry in entries
    )
    before_complete = all(
        (
            (root / entry["target"]).is_file()
            and sha256_file(root / entry["target"]) == entry.get("before_sha256")
        )
        if entry.get("before_exists")
        else not (root / entry["target"]).exists()
        for entry in entries
    )
    if journal.get("state") == "committed" and desired_complete:
        cleanup_transaction_files(root)
        return "completed_cleanup"
    if journal.get("state") == "committing" and before_complete:
        cleanup_transaction_files(root)
        return "rolled_back_cleanup"
    restore_from_journal(root, journal)
    cleanup_transaction_files(root)
    return "rolled_back"


def transactional_replace(
    root: Path,
    outputs: dict[Path, bytes],
    before_bytes: dict[Path, bytes | None],
    *,
    fail_after: int | None = None,
    before_commit_hook: Callable[[], None] | None = None,
    post_validate: Callable[[], None] | None = None,
) -> None:
    journal_path, backup_dir = journal_paths(root)
    journal = prepare_transaction(root, outputs, before_bytes)
    targets_replaced = False
    commit_marked_durable = False
    try:
        if before_commit_hook:
            before_commit_hook()
        snapshot_gate(before_bytes, label="pre-commit")
        journal["state"] = "committing"
        write_journal(journal_path, journal)
        for index, entry in enumerate(journal["entries"], 1):
            target = root / entry["target"]
            staged = backup_dir / entry["staged"]
            if sha256_file(staged) != entry["desired_sha256"]:
                raise RuntimeError(f"staged Hildebrandt payload drift: {staged}")
            replace_path(staged, target)
            targets_replaced = True
            fsync_directory(target.parent)
            journal["committed_targets"].append(entry["target"])
            write_journal(journal_path, journal)
            if fail_after is not None and index >= fail_after:
                raise InjectedTransactionAbort("injected Hildebrandt hard abort")
        if post_validate:
            post_validate()
        journal["state"] = "committed"
        write_journal(journal_path, journal)
        commit_marked_durable = True
        cleanup_transaction_files(root)
    except BaseException:
        if commit_marked_durable:
            raise
        if not targets_replaced:
            cleanup_transaction_files(root)
            raise
        current = (
            json.loads(journal_path.read_text(encoding="utf-8"))
            if journal_path.exists()
            else journal
        )
        restore_from_journal(root, current)
        cleanup_transaction_files(root)
        raise


def apply_plan(
    plan: RepairPlan,
    *,
    fail_after: int | None = None,
    before_commit_hook: Callable[[], None] | None = None,
) -> None:
    if not plan.counts:
        return
    report_path = plan.root / REPORT_RELATIVE
    quarantine_path = plan.root / QUARANTINE_RELATIVE
    if report_path.exists() or quarantine_path.exists():
        raise PreconditionsError("refusing to overwrite Hildebrandt report/quarantine")
    applied_report = copy.deepcopy(plan.summary)
    applied_report.update(
        {
            "mode": "write",
            "status": "applied_open_issues_pending_review",
            "write_performed": True,
        }
    )
    outputs = dict(plan.outputs)
    outputs[report_path] = (
        json.dumps(applied_report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode()
    outputs[quarantine_path] = serialize_jsonl(plan.quarantine)
    snapshot_a = dict(plan.before_bytes)
    snapshot_a[report_path] = None
    snapshot_a[quarantine_path] = None

    def post_validate() -> None:
        followup = build_plan(plan.root)
        if followup.counts:
            raise RuntimeError(
                f"Hildebrandt post-write is not idempotent: {followup.counts}"
            )

    transactional_replace(
        plan.root,
        outputs,
        snapshot_a,
        fail_after=fail_after,
        before_commit_hook=before_commit_hook,
        post_validate=post_validate,
    )


def locked_write(root: Path, *, fail_after: int | None = None) -> RepairPlan:
    lock_path = root / LOCK_RELATIVE
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+b") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        recover_transaction(root)
        plan = build_plan(root)
        apply_plan(plan, fail_after=fail_after)
        fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
    return plan


def cli_result_summary(
    root: Path, plan: RepairPlan, *, write_requested: bool
) -> dict[str, Any]:
    if not write_requested:
        return copy.deepcopy(plan.summary)
    if not plan.counts:
        repeated = copy.deepcopy(plan.summary)
        repeated.update(
            {"mode": "write", "status": "already_applied", "write_performed": False}
        )
        return repeated
    report_path = root / REPORT_RELATIVE
    if not report_path.is_file():
        raise RuntimeError("successful Hildebrandt write did not persist its report")
    applied = json.loads(report_path.read_text(encoding="utf-8"))
    if (
        applied.get("mode") != "write"
        or applied.get("status") != "applied_open_issues_pending_review"
        or applied.get("write_performed") is not True
    ):
        raise RuntimeError("persisted Hildebrandt report has misleading status")
    return applied


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--production-write-approved", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--inject-failure-after", type=int, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    root = args.root.expanduser().resolve()
    if args.write and root == ROOT and not args.production_write_approved:
        blocked = {
            "mode": "write",
            "status": "blocked_explicit_production_approval_required",
            "write_performed": False,
            "error": "repository write requires --production-write-approved after root review",
        }
        print(json.dumps(blocked, ensure_ascii=False, indent=2, sort_keys=True))
        return 2
    try:
        plan = build_plan(root) if not args.write else locked_write(
            root, fail_after=args.inject_failure_after
        )
    except PreconditionsError as exc:
        blocked = {
            "mode": "write" if args.write else "dry_run",
            "status": "blocked_precondition_failed",
            "write_performed": False,
            "error": str(exc),
        }
        if args.json:
            print(json.dumps(blocked, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(f"Hildebrandt repair BLOCKED: {exc}", file=sys.stderr)
        return 2
    result = cli_result_summary(root, plan, write_requested=args.write)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print("Hildebrandt 2022 P0 repair")
        print("mode:", result["mode"].upper())
        print("status:", result["status"])
        for name, count in sorted(result.get("counts", {}).items()):
            print(f"{name}: {count}")
        print("changed paths:", len(result.get("changed_paths", [])))
        for path in result.get("changed_paths", []):
            print(" -", path)
        if not args.write:
            print("dry-run: nothing written; production write requires root approval")
        elif result["write_performed"]:
            print("write complete; Hildebrandt issues remain OPEN")
        else:
            print("already applied; no write performed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
