#!/usr/bin/env python3
"""Prepare the bounded Long-Sedley volume 2 P0 repair.

The command is a dry-run by default. ``--write`` is required for repository
mutation. It never edits corpus passages, corpus citations, BibTeX, the BibTeX
companion report, or E2 patches.

The repair separates the two-volume work, volume 2 intellectual role and local
scan manifestation; makes priority and interpretation claims discoverable-only;
registers three page-mapped secondary evidence units; and removes only exact LS
mapping errors visually established in the audited volume 2. Ancient loci remain
leads pending primary recollation.
"""

from __future__ import annotations

import argparse
import copy
import fcntl
import hashlib
import json
import os
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

STAMP = "long_sedley_vol2_p0_2026_08_24"
NOW = "2026-08-24 10:00:00+00:00"
ACCESSED_AT = "2026-08-24T10:00:00Z"

SCAN_RELATIVE = (
    "data/literature_acquisition/"
    "long_sedley_1987_hellenistic_philosophers_vol2.pdf"
)
SCAN_SHA256 = "af6fc6f55d30f1896d59e2898e989016043990a498f8ff8cd5e8850bbb5e84a8"
SCAN_MD5 = "d8c95fb77d88c968463786dbe3cb6dfa"
SCAN_BYTES = 24_371_131
SCAN_PAGES = 520
AUDIT_RELATIVE = "docs/academic/2026-08-24-long-sedley-volume2-pdf-audit.md"
AUDIT_SHA256 = "accfa4129672f0ae80a35f08ff4d315f2b3df306f7f2ef8124dda3da2392579c"

SCRIPT_RELATIVE = "scripts/apply_2026_08_24_long_sedley_vol2_p0_repair.py"
TEST_RELATIVE = "tests/test_long_sedley_vol2_p0_repair.py"
LITERATURE_BUILDER_RELATIVE = "scripts/build_literature_acquisition_manifest.py"
LITERATURE_MANIFEST_RELATIVE = "data/literature_acquisition/manifest.jsonl"
SCHOLARLY_MANIFEST_RELATIVE = "data/scholarly_sources/manifest.jsonl"
NODES_RELATIVE = "data/kg/nodes.jsonl"
EDGES_RELATIVE = "data/kg/edges.jsonl"
SOURCES_RELATIVE = (
    "data/goals/sota/registry/sources/seed_priority_20260824.jsonl"
)
EVIDENCE_RELATIVE = (
    "data/goals/sota/registry/evidence/seed_priority_20260824.jsonl"
)
ISSUES_RELATIVE = "data/goals/sota/registry/issues/seed_known_20260824.jsonl"
WAVES_RELATIVE = "data/goals/sota/registry/waves/priority_20260824.jsonl"
VERIFICATIONS_RELATIVE = (
    "data/goals/sota/registry/verifications/long_sedley_20260824.jsonl"
)

REPORT_RELATIVE = "data/audit/2026-08-24_long_sedley_vol2_p0_repair.json"
QUARANTINE_RELATIVE = (
    "data/audit/2026-08-24_long_sedley_vol2_p0_quarantine.jsonl"
)
LOCK_RELATIVE = "data/audit/.long_sedley_vol2_p0.lock"
JOURNAL_RELATIVE = "data/audit/.long_sedley_vol2_p0_transaction.json"
BACKUP_DIR_RELATIVE = "data/audit/.long_sedley_vol2_p0_transaction_backups"

WORK_ID = "scholarly_work_long_sedley_1987_hellenistic_philosophers"
COLLECTION_ID = "collection_ls"
POSITION_ID = "scholarly_position_long_sedley_epicurus_first_freewill"
LONG_ID = "scholar_long_anthony"
SEDLEY_ID = "scholar_sedley_david"

OVERLAP_NODE_IDS = frozenset(
    {
        "argument_chrysippus_causal_taxonomy",
        "argument_cylinder_analogy_chrysippus_k1l2m3n4",
        "concept_cylinder_analogy_chrysippus_e5f6g7h8",
        "argument_the_dog_and_cart_argument_9ba60714",
        "concept_clinamen_atomic_swerve_epicurus_m3n4o5p6",
        "debate_stoic_compatibilism",
    }
)

OVERLAP_BEFORE_HASHES = {
    "argument_chrysippus_causal_taxonomy": "1f1fff7b798a8e49d3dfd5a0c9655f5de2498120c259016f717e6b3d8d29b34e",
    "argument_cylinder_analogy_chrysippus_k1l2m3n4": "3ec480b6dfae2647a7842e17cbb93c4bcd58ef6ad73fd872ed2acab6c01809b5",
    "argument_the_dog_and_cart_argument_9ba60714": "4717d9c3822f2421dfc942e435c3a930ca7c20cd3a3050a23da9288b2841ed1a",
    "concept_clinamen_atomic_swerve_epicurus_m3n4o5p6": "40f18bcb6817541b595bce1fa34544106c95abb185aca0966689ee2c686f0889",
    "concept_cylinder_analogy_chrysippus_e5f6g7h8": "f287bcefd1f14c48d68e07a99fc25a8a8391e711faf1f1d50acee180e14c5229",
    "debate_stoic_compatibilism": "76405d4a1cdd4ed88d91e385dfccb5caebc931532b20a16dd3ba6374328944b3",
}

FALSE_LS_REFS_BY_NODE: dict[str, frozenset[str]] = {
    "passage_dl_lives_10_1_129": frozenset({"20A"}),
    "passage_cic_fat_48": frozenset({"20E"}),
    "passage_alex_fat_2": frozenset({"55N"}),
    "passage_cic_fat_34": frozenset({"55J", "55N"}),
    "passage_dl_lives_7_1_99": frozenset({"55A"}),
    "passage_dl_lives_7_1_116": frozenset({"55F"}),
    "passage_dl_lives_7_1_79": frozenset({"38G"}),
    "passage_dl_lives_7_1_82": frozenset({"20A"}),
    "passage_dl_lives_7_1_104": frozenset({"55D"}),
    "passage_dl_lives_7_1_156": frozenset({"62G"}),
    "passage_cic_fat_12": frozenset({"38H", "55K", "55L", "55R", "62H"}),
    "passage_cic_fat_39": frozenset(
        {"38E", "38H", "55I", "55K", "55L", "55N", "55R", "62B", "62D", "62H"}
    ),
    "passage_cic_fat_41": frozenset({"62D"}),
    "passage_cic_fat_42": frozenset({"62D", "62G"}),
    "passage_dl_lives_7_1_121": frozenset({"59A"}),
    "passage_gellius_na_vii_2_7_2_1": frozenset({"62D"}),
    "passage_gellius_na_vii_2_7_2_2": frozenset({"62D"}),
    "passage_gellius_na_vii_2_7_2_3": frozenset({"62D"}),
    "passage_gellius_na_vii_2_7_2_4": frozenset({"55K", "62D"}),
    "passage_gellius_na_vii_2_7_2_5": frozenset({"62D"}),
    "passage_gellius_na_vii_2_7_2_6": frozenset({"55I", "55N", "62C"}),
    "passage_gellius_na_vii_2_7_2_13": frozenset({"55K"}),
    "passage_gellius_na_vii_2_7_2_14": frozenset({"62D"}),
    "passage_gellius_na_vii_2_7_2_15": frozenset({"62D"}),
}

EXACT_LS_REFS_BY_NODE: dict[str, dict[str, Any]] = {
    "passage_dl_lives_10_1_133": {
        "reference": "20A",
        "printed_pages": "104",
        "pdf_pages": "112",
    },
    "passage_dl_lives_10_1_134": {
        "reference": "20A",
        "printed_pages": "104",
        "pdf_pages": "112",
    },
    "passage_cic_fat_21": {
        "reference": "20E",
        "printed_pages": "108-110",
        "pdf_pages": "116-118",
    },
    "passage_cic_fat_24": {
        "reference": "20E",
        "printed_pages": "108-110",
        "pdf_pages": "116-118",
    },
    "passage_cic_fat_25": {
        "reference": "20E",
        "printed_pages": "108-110",
        "pdf_pages": "116-118",
    },
    "passage_cic_fat_29": {
        "reference": "55S",
        "printed_pages": "340-341",
        "pdf_pages": "348-349",
    },
    "passage_gellius_na_vii_2_7_2_3": {
        "reference": "55K",
        "printed_pages": "337",
        "pdf_pages": "345",
    },
}

CORE_NODE_IDS = frozenset({WORK_ID, COLLECTION_ID, POSITION_ID, *OVERLAP_NODE_IDS})
TOUCHED_NODE_IDS = frozenset(
    {*CORE_NODE_IDS, *FALSE_LS_REFS_BY_NODE, *EXACT_LS_REFS_BY_NODE}
)

REMOVED_EDGE_IDS = frozenset(
    {
        "deepaudit-passage_dl_lives_10_1_129-partof-collection_ls",
        "deepaudit-passage_cic_fat_48-partof-collection_ls",
        "deepaudit-passage_alex_fat_2-partof-collection_ls",
        "deepaudit-passage_cic_fat_34-partof-collection_ls",
        "deepaudit-passage_dl_lives_7_1_99-partof-collection_ls",
        "deepaudit-passage_dl_lives_7_1_116-partof-collection_ls",
        "deepaudit-passage_dl_lives_7_1_79-partof-collection_ls",
        "deepaudit-passage_gellius_na_vii_2_7_2_1-partof-collection_ls",
        "deepaudit-passage_gellius_na_vii_2_7_2_2-partof-collection_ls",
        "deepaudit-passage_gellius_na_vii_2_7_2_4-partof-collection_ls",
        "deepaudit-passage_gellius_na_vii_2_7_2_5-partof-collection_ls",
        "deepaudit-passage_gellius_na_vii_2_7_2_14-partof-collection_ls",
        "deepaudit-passage_gellius_na_vii_2_7_2_15-partof-collection_ls",
    }
)
MODIFIED_EDGE_ID = "deepaudit-passage_gellius_na_vii_2_7_2_3-partof-collection_ls"

NEW_MAPPING_EDGE_IDS = {
    node_id: f"long-sedley-vol2-{node_id}-partof-collection_ls"
    for node_id in EXACT_LS_REFS_BY_NODE
    if node_id != "passage_gellius_na_vii_2_7_2_3"
}
WORK_SEDLEY_EDGE_ID = "long-sedley-vol2-work-authored-by-sedley"
NEW_EDGE_IDS = frozenset(
    {*NEW_MAPPING_EDGE_IDS.values(), WORK_SEDLEY_EDGE_ID}
)

AG026_EDGE_ID = "ag_026_advanced_in"
AG026_BEFORE_HASH = "095a6da3d6c6f5d31306322e14d3b532cc667dff48d3401f7e1863909a2c62bf"
LONG_AUTHORED_EDGE_ID = "19c5f906-84c0-4b28-a942-6eab6e1a6ff4"
LONG_CREATED_EDGE_ID = "7ba4e8ef-035a-49a9-84f3-2a1cdb92159c"

SOURCE_ID = "src_sec_long_sedley_1987_hp2"
LS20_EVIDENCE_ID = "ev_sec_long_sedley_section20_pp104_113"
OLD_FUSED_EVIDENCE_ID = "ev_sec_long_sedley_sections55_62_pp332_388"
LS55_EVIDENCE_ID = "ev_sec_long_sedley_section55_pp332_341"
LS62_EVIDENCE_ID = "ev_sec_long_sedley_section62_pp382_389"
ALL_LS_EVIDENCE_IDS = (LS20_EVIDENCE_ID, LS55_EVIDENCE_ID, LS62_EVIDENCE_ID)
ARCHIVE_GAP_ISSUE_ID = "issue_secondary_archive_manifest_gap_20260824"
MANIFESTATION_ISSUE_ID = (
    "issue_long_sedley_vol2_local_manifestation_unknown_20260824"
)
PRIORITY_ISSUE_ID = "issue_long_sedley_first_freewill_priority_20260824"
RECOLLATION_ISSUE_ID = "issue_long_sedley_ancient_loci_recollation_20260824"
NEW_ISSUE_IDS = (MANIFESTATION_ISSUE_ID, PRIORITY_ISSUE_ID, RECOLLATION_ISSUE_ID)
WAVE_ID = "wave_01_pdf_priority_new_knowledge"
SCHOLARLY_PUBLICATION_DIR = "long_sedley1987hp2"
LITERATURE_ARTIFACT_ID = "lit_long_sedley_1987_hellenistic_philosophers_vol2"

FILE_BEFORE_SHA256: dict[str, str | None] = {
    NODES_RELATIVE: "ef792eb6373ac0252a5d6bba5bde2c57d03178d8c1ca2e10e14f10817865a31f",
    EDGES_RELATIVE: "feaac9d40bb69d3a1b58755710a280fc6d108a9c240ce1a3278757a34017a1b9",
    LITERATURE_BUILDER_RELATIVE: "56fe44b570c16b6292d0de4c59d8eb84e60b713d8d4554950fbf389392822d57",
    LITERATURE_MANIFEST_RELATIVE: "751254bf082ab8b7029a6ed24b59ee4258157c20760a996f71a1d2956ef7de3f",
    SCHOLARLY_MANIFEST_RELATIVE: "6a1ea79b746afe8fbfc7b6fc0d7351bf74226d2347a5b75db674b24d80931c7a",
    SOURCES_RELATIVE: "64a3e50e0c583f9b13dd709663d84270653d312bee6b19a5118da2ee2768e034",
    EVIDENCE_RELATIVE: "5cda6240fd91518a4752437f7fab6601967c4f48be538fe7e0714803e00d4670",
    ISSUES_RELATIVE: "895582a6111e38d017337a636adcf51ebc5ae9d009a478bfba8b94aa5cb1f18a",
    WAVES_RELATIVE: "f210538c2e84c1ab79dc9e0aa5632c198254deb49dc411ddc9d24d2bfe8c8396",
    VERIFICATIONS_RELATIVE: None,
}

# Frozen after hashes are filled after the deterministic preview is built.
FILE_AFTER_SHA256: dict[str, str] = {
    NODES_RELATIVE: "57fb90da476ebdf98bc59f4a0cb4bad0c4871d5d829c0dc05063b4752b6c8664",
    EDGES_RELATIVE: "22efd267ac194d67d23ffd9985d2c68d93e1cfb4129e1a91cc3fda4871fadd70",
    LITERATURE_BUILDER_RELATIVE: "59cbd46c4a9b62e3fc2497089cb2469dfc4a55916d9ef3f059ad639ab6b3eef3",
    LITERATURE_MANIFEST_RELATIVE: "5c567015a2a064147efb4d9eaa64cf72e55432f42d0231f73758ea538858514d",
    SCHOLARLY_MANIFEST_RELATIVE: "e326abbe07e78f6c8ca873e1ef99ab5ca77e64066a838bcf93ff360e466bcbe5",
    SOURCES_RELATIVE: "ceba6d9e9ec188d943abdd345f0149dca017b70a82404f7d858774f812bcd650",
    EVIDENCE_RELATIVE: "41683cdb6df1b826dbc625853c08a3fcd66c0579a7ca96883c5e326ecd82cbe7",
    ISSUES_RELATIVE: "1aa809df5ebfc5f81d31963ce84fa37ab7563a4d61d9007fc7009399819a130a",
    WAVES_RELATIVE: "4b9cfecc1c3075900e681c56af5ef0278dc8d19ba66150f0b562cd58712a7bee",
    VERIFICATIONS_RELATIVE: "73fe479124cab654b28143ad9e3bf89c59af290752bb9ca3d379ff37bcea3dde",
}

IMMUTABLE_FILE_HASHES = {
    "data/kg/publications.bib": "2bf6ea54d93bb86249997a076e73dde025b8e765e1edcab59f641ad77c5f4dcc",
    "data/kg/publications_bibtex_report.json": "66355e056418b9c446a278e9d29b0119d60628504f73bc10af08d73d155b6f72",
    "data/kg/e2_patches/cary.json": "1fb574160b21f3b035dc29a818f4f0858664512a084ffc0b7834b255b001182e",
    "data/kg/e2_patches/sorabji.json": "d84f98c3bce2859cc5ec36b9ea5785f5aa92240a05bb902bb6b970261f84e660",
    "data/corpus/passages.jsonl": "4e2e7b8789de06f3b3cf897c3f9b6d63bc92db5ee24657dabee6c9ba510f51ec",
    "data/corpus/citations.jsonl": "3fa555efad53ad2795f04fb28959442e42630b4f33187c1c7a1b78890af0d248",
    "data/corpus/manifest.jsonl": "aa4d446f32b5d47d4fb3d002dec3b49398862f8f3f8515b6076655ea8e414cd6",
}

OLD_LONG_BUILDER_BLOCK = '''    "long_sedley_1987_hellenistic_philosophers_vol2.pdf": item(
        "long_sedley_1987_hellenistic_philosophers_vol2",
        "The Hellenistic Philosophers, Volume 2: Greek and Latin Texts",
        ["A. A. Long", "D. N. Sedley"], 1987, audit_status="deep_read_wave1", scope="core"
    ),'''

NEW_LONG_BUILDER_BLOCK = '''    "long_sedley_1987_hellenistic_philosophers_vol2.pdf": {
        **item(
            "long_sedley_1987_hellenistic_philosophers_vol2",
            "The Hellenistic Philosophers, Volume 2: Greek and Latin Texts",
            ["A. A. Long", "D. N. Sedley"], 1987, completeness="full",
            role="source_scan", audit_status="deep_read_wave1", scope="core"
        ),
        "content_completeness_scope": "scholarly main content from title page through bibliography",
        "physical_completeness": "incomplete",
        "physically_missing": ["front cover", "preliminaries i-ii"],
        "intellectual_work_id": "scholarly_work_long_sedley_1987_hellenistic_philosophers",
        "intellectual_volume": 2,
        "visible_reprint_line_latest_year": 1998,
        "exact_local_printing_status": "unknown_not_inferred",
        "binding_status": "unknown_cover_absent",
        "isbn_10_hardback": "0521255627",
        "isbn_10_paperback": "0521275571",
        "page_map": "printed body page = PDF page - 8",
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


def metadata(row: dict[str, Any]) -> dict[str, Any]:
    value = row.get("metadata")
    if isinstance(value, dict):
        return copy.deepcopy(value)
    if isinstance(value, str) and value.strip():
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return {}
        return parsed if isinstance(parsed, dict) else {}
    return {}


def set_metadata(row: dict[str, Any], value: dict[str, Any]) -> None:
    row["metadata"] = value


def file_state(root: Path, relative: str) -> str:
    path = root / relative
    current = sha256_file(path) if path.exists() else None
    if current == FILE_BEFORE_SHA256[relative]:
        return "before"
    expected_after = FILE_AFTER_SHA256[relative]
    if not expected_after.startswith("__") and current == expected_after:
        return "after"
    raise PreconditionsError(
        f"Long-Sedley file drift: {relative}; expected before/after, actual {current}"
    )


def ls_refs(row: dict[str, Any]) -> set[str]:
    data = metadata(row)
    result: set[str] = set()
    for item in data.get("fragment_collections") or []:
        if isinstance(item, dict) and item.get("collection") == "LS":
            result.add(str(item.get("reference") or ""))
    return result


def exact_ls_entry(spec: dict[str, Any]) -> dict[str, Any]:
    return {
        "collection": "LS",
        "editor": "Long-Sedley",
        "reference": spec["reference"],
        "year": 1987,
        "verification_source": (
            "Long-Sedley volume 2 visual audit: printed pp. "
            f"{spec['printed_pages']}, PDF {spec['pdf_pages']}"
        ),
        "manifestation_scope": "volume_2_exact_editorial_excerpt",
        "primary_recollation_status": "pending",
    }


def transform_passage_node(row: dict[str, Any]) -> dict[str, Any]:
    row = copy.deepcopy(row)
    wanted = node_id(row)
    false_refs = FALSE_LS_REFS_BY_NODE.get(wanted, frozenset())
    exact = EXACT_LS_REFS_BY_NODE.get(wanted)
    data = metadata(row)
    collections = []
    for item in data.get("fragment_collections") or []:
        if (
            isinstance(item, dict)
            and item.get("collection") == "LS"
            and str(item.get("reference") or "") in false_refs
        ):
            continue
        collections.append(copy.deepcopy(item))
    if exact and not any(
        isinstance(item, dict)
        and item.get("collection") == "LS"
        and item.get("reference") == exact["reference"]
        for item in collections
    ):
        collections.append(exact_ls_entry(exact))
    if collections:
        data["fragment_collections"] = collections
    else:
        data.pop("fragment_collections", None)
    data["long_sedley_ls_mapping_review"] = {
        "audit": AUDIT_RELATIVE,
        "scan_sha256": SCAN_SHA256,
        "removed_false_exact_references": sorted(false_refs),
        "exact_reference_added": exact["reference"] if exact else None,
        "status": "editorial_mapping_only_primary_recollation_pending",
    }
    set_metadata(row, data)
    row["updated_at"] = NOW
    return row


def transform_work(row: dict[str, Any]) -> dict[str, Any]:
    row = copy.deepcopy(row)
    row["description"] = (
        "Two-volume intellectual work by A. A. Long and D. N. Sedley. Volume 1 "
        "contains translations and philosophical exposition; volume 2 contains "
        "Greek and Latin texts with notes and bibliography. The local scan is "
        "volume 2 and carries a reprint line through 1998; exact printing and "
        "binding remain unknown."
    )
    data = metadata(row)
    if data.get("isbn") != "978-0521275569":
        raise PreconditionsError("unexpected Long-Sedley legacy ISBN")
    data.pop("citation_verified", None)
    data.pop("verified_reference", None)
    data["citation_verdict"] = (
        "two_volume_work_identity_verified_volume2_manifestation_bounded"
    )
    data["publication_identity"] = "two_volume_intellectual_work"
    data["author_ids"] = [LONG_ID, SEDLEY_ID]
    data["isbn_scope"] = (
        "legacy BibTeX projection: 9780521275569 is volume 1 paperback only, "
        "not a work-level or volume 2 ISBN"
    )
    data["volumes"] = [
        {
            "volume_number": 1,
            "intellectual_role": "English translations and philosophical commentary",
            "isbn_13_paperback": "9780521275569",
            "audit_status": "not_audited_in_this_transaction",
        },
        {
            "volume_number": 2,
            "title": "Greek and Latin Texts with Notes and Bibliography",
            "intellectual_role": "original-language texts, notes, selective apparatus and bibliography",
            "isbn_10_hardback": "0521255627",
            "isbn_10_paperback": "0521275571",
            "local_scan_manifestation": {
                "path": SCAN_RELATIVE,
                "sha256": SCAN_SHA256,
                "page_count": SCAN_PAGES,
                "visible_reprint_line_latest_year": 1998,
                "exact_printing_status": "unknown_not_inferred",
                "binding_status": "unknown_cover_absent",
                "content_scope": "title_page_through_bibliography",
                "physically_missing": ["front cover", "preliminaries i-ii"],
            },
        },
    ]
    data[STAMP] = True
    set_metadata(row, data)
    row["updated_at"] = NOW
    return row


def transform_collection(row: dict[str, Any]) -> dict[str, Any]:
    row = copy.deepcopy(row)
    English = (
        "Long and Sedley's two-volume reference work. Volume 1 supplies English "
        "translations and philosophical commentary; volume 2 supplies Greek and "
        "Latin texts, notes, selective apparatus and bibliography. Page numbers "
        "are volume-specific: LS 20/55/62 begin at 102/333/386 in volume 1, but "
        "the audited volume 2 units occupy 104-113, 332-341 and 382-389."
    )
    French = (
        "Ouvrage de référence en deux volumes de Long et Sedley. Le volume 1 "
        "contient les traductions anglaises et le commentaire philosophique; le "
        "volume 2 contient les textes grecs et latins, des notes, un apparat "
        "sélectif et la bibliographie. Les pages sont propres à chaque volume: "
        "LS 20/55/62 commencent à 102/333/386 au volume 1, tandis que les unités "
        "auditées du volume 2 couvrent 104-113, 332-341 et 382-389."
    )
    row["description"] = English
    data = metadata(row)
    data.pop("citation_verified", None)
    data.pop("verified_reference", None)
    data.pop("verification_notes", None)
    data["citation_verdict"] = (
        "volume2_visually_verified_volume1_commentary_pending_separate_audit"
    )
    data["description_en"] = English
    data["description_fr"] = French
    data["author_ids"] = [LONG_ID, SEDLEY_ID]
    data["volume_roles"] = {
        "volume_1": "translations and philosophical commentary",
        "volume_2": "Greek and Latin texts, notes, selective apparatus and bibliography",
    }
    data["section_page_maps"] = {
        "volume_1": {
            "LS20_start": 102,
            "LS55_start": 333,
            "LS62_start": 386,
            "status": "legacy_labels_pending_dedicated_volume1_audit",
        },
        "volume_2": {
            "LS20": {"printed_pages": "104-113", "pdf_pages": "112-121"},
            "LS55": {"printed_pages": "332-341", "pdf_pages": "340-349"},
            "LS62": {"printed_pages": "382-389", "pdf_pages": "390-397"},
            "status": "visually_verified",
            "scan_sha256": SCAN_SHA256,
        },
    }
    data[STAMP] = True
    set_metadata(row, data)
    row["updated_at"] = NOW
    return row


def transform_position(row: dict[str, Any]) -> dict[str, Any]:
    row = copy.deepcopy(row)
    row["description"] = (
        "Attributed and disputed historical-priority claim associated with Long "
        "and Sedley volume 1 section 20 and Huby 1967. The audited volume 2 does "
        "not establish that Epicurus first posed the free-will question. Its note "
        "treats the swerve at most as necessary, not sufficient or a demonstrated "
        "direct cause of each volition."
    )
    data = metadata(row)
    data.pop("citation_verified", None)
    data.pop("verified_reference", None)
    data.pop("evidence_url", None)
    data["citability"] = "discoverable_only"
    data["citation_verdict"] = (
        "attributed_disputed_priority_volume1_and_huby_audit_pending"
    )
    data["interpretation_status"] = "attributed_disputed_secondary_claim"
    data["needs_evidence"] = True
    data["confidence"] = "disputed_pending_source_audit"
    data["scholar_id"] = LONG_ID
    data["co_scholar_id"] = SEDLEY_ID
    data["stance"] = (
        "Epicurean priority is an attributed hypothesis; volume 2 does not verify "
        "priority, and its clinamen note supports necessity at most."
    )
    data["premises"] = [
        {
            "id": "P1",
            "text": "LS 20 groups evidence about necessity, developed agency, admonition and blame.",
            "attestation": "reported_interpretation",
            "primary_sources": [],
            "secondary_sources": [],
        },
        {
            "id": "P2",
            "text": "The volume 2 note treats the swerve at most as a necessary condition of free volition.",
            "attestation": "direct_editorial_note",
            "primary_sources": [],
            "secondary_sources": [],
        },
        {
            "id": "P3",
            "text": "A direct role for the swerve in each autonomous action is only an interpretive suggestion.",
            "attestation": "reported_interpretation",
            "primary_sources": [],
            "secondary_sources": [],
        },
        {
            "id": "P4",
            "text": "Volume 2 does not establish absolute historical priority for Epicurus.",
            "attestation": "negative",
            "primary_sources": [],
            "secondary_sources": [],
        },
        {
            "id": "P5",
            "text": "The volume 1 commentary and Huby 1967 require separate audit before the priority attribution can be assessed.",
            "attestation": "reconstructed",
            "primary_sources": [],
            "secondary_sources": [],
        },
        {
            "id": "P6",
            "text": "Stoic compatibilism is a disputed family of reconstructions, not one univocal ancient doctrine.",
            "attestation": "reported_interpretation",
            "primary_sources": [],
            "secondary_sources": [],
        },
    ]
    data["conclusion"] = {
        "text": (
            "The Epicurean priority claim remains attributed and disputed; volume "
            "2 alone neither verifies it nor makes the clinamen more than at most "
            "necessary: it is not a sufficient or demonstrated direct cause of volition."
        ),
        "primary_sources": [],
        "secondary_sources": [],
    }
    data["validity_assessment"] = {
        "formally_valid": "disputed",
        "scholarly_consensus": "disputed",
        "rationale": (
            "Historical priority depends on incomplete survival and on sources not "
            "audited here; the physical role of the swerve does not by itself yield "
            "a complete theory of action or responsibility."
        ),
    }
    data["volume1_claim_audit"] = {
        "edge_id": AG026_EDGE_ID,
        "status": "typed_pending_do_not_modify_edge",
        "required_sources": ["Long-Sedley volume 1 section 20", "Huby 1967"],
    }
    data["long_sedley_vol2_visual_evidence"] = {
        "sections": [
            {"section": "LS20", "printed_pages": "104-113", "pdf_pages": "112-121"}
        ],
        "evidence_role": "secondary_editorial_evidence_not_priority_verification",
        "scan_sha256": SCAN_SHA256,
        "status": "paraphrase_only_primary_sources_not_recollated",
    }
    data[STAMP] = True
    set_metadata(row, data)
    row["updated_at"] = NOW
    return row


def overlap_visual_evidence(wanted: str) -> dict[str, Any]:
    if wanted == "concept_clinamen_atomic_swerve_epicurus_m3n4o5p6":
        sections = [
            {"section": "LS20", "printed_pages": "104-113", "pdf_pages": "112-121"}
        ]
        qualification = (
            "clinamen at most necessary, not sufficient; direct involvement only suggested"
        )
    elif wanted == "argument_the_dog_and_cart_argument_9ba60714":
        sections = [
            {"section": "LS62A-B", "printed_pages": "382-383", "pdf_pages": "390-391"}
        ]
        qualification = "consent or resistance under necessity; no alternative established"
    elif wanted in {
        "argument_cylinder_analogy_chrysippus_k1l2m3n4",
        "concept_cylinder_analogy_chrysippus_e5f6g7h8",
    }:
        sections = [
            {"section": "LS62C-D", "printed_pages": "383-385", "pdf_pages": "391-393"}
        ]
        qualification = (
            "external initiating condition and internal nature; moral/modal success disputed"
        )
    else:
        sections = [
            {"section": "LS55", "printed_pages": "332-341", "pdf_pages": "340-349"},
            {"section": "LS62", "printed_pages": "382-389", "pdf_pages": "390-397"},
        ]
        qualification = "multiple witnesses and hostile reconstructions; no univocal compatibilism"
    return {
        "sections": sections,
        "qualification": qualification,
        "evidence_role": "volume2_secondary_editorial_apparatus",
        "source_boundary": (
            "volume 2 original-language texts and notes, not volume 1 translations/commentary"
        ),
        "primary_source_status": "ancient_loci_leads_not_primary_verified",
        "review_status": "pending_independent_adversarial_and_human_signoff",
        "quotation_status": "paraphrase_only",
        "scan_sha256": SCAN_SHA256,
        "audit": AUDIT_RELATIVE,
    }


def transform_overlap(row: dict[str, Any]) -> dict[str, Any]:
    row = copy.deepcopy(row)
    wanted = node_id(row)
    data = metadata(row)
    data["citability"] = "discoverable_only"
    data["needs_evidence"] = True
    data["long_sedley_vol2_visual_evidence"] = overlap_visual_evidence(wanted)
    if wanted == "argument_cylinder_analogy_chrysippus_k1l2m3n4":
        data["ancient_sources"] = [
            str(value).replace("7.2.6-14", "7.2.6-13")
            for value in data.get("ancient_sources") or []
        ]
        bundle = data.get("reference_bundle_pending_recollation")
        if isinstance(bundle, dict):
            bundle = copy.deepcopy(bundle)
            bundle["references"] = str(bundle.get("references") or "").replace(
                "7.2.6-14", "7.2.6-13"
            )
            data["reference_bundle_pending_recollation"] = bundle
    set_metadata(row, data)
    row["updated_at"] = NOW
    return row


def desired_node(row: dict[str, Any]) -> dict[str, Any]:
    wanted = node_id(row)
    if wanted == WORK_ID:
        return transform_work(row)
    if wanted == COLLECTION_ID:
        return transform_collection(row)
    if wanted == POSITION_ID:
        return transform_position(row)
    if wanted in OVERLAP_NODE_IDS:
        return transform_overlap(row)
    if wanted in FALSE_LS_REFS_BY_NODE or wanted in EXACT_LS_REFS_BY_NODE:
        return transform_passage_node(row)
    return copy.deepcopy(row)


def transform_nodes(
    rows: list[dict[str, Any]], *, state: str
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], Counter[str]]:
    by_id = {node_id(row): row for row in rows}
    if len(by_id) != len(rows):
        raise PreconditionsError("duplicate KG node identity")
    if missing := sorted(TOUCHED_NODE_IDS - by_id.keys()):
        raise PreconditionsError(f"missing Long-Sedley nodes: {missing}")
    if state == "before":
        overlap_hashes = {
            wanted: canonical_hash(by_id[wanted]) for wanted in OVERLAP_NODE_IDS
        }
        if overlap_hashes != OVERLAP_BEFORE_HASHES:
            raise PreconditionsError("post-Sorabji overlap hashes drifted")
    result = copy.deepcopy(rows)
    quarantine: list[dict[str, Any]] = []
    for index, row in enumerate(result):
        wanted = node_id(row)
        if wanted not in TOUCHED_NODE_IDS:
            continue
        before = copy.deepcopy(row)
        result[index] = desired_node(row)
        if state == "before":
            quarantine.append({"record_type": "kg_node_before", "record": before})
    validate_nodes(result)
    changed = {
        node_id(old)
        for old, new in zip(rows, result, strict=True)
        if old != new
    }
    expected = set(TOUCHED_NODE_IDS) if state == "before" else set()
    if changed != expected:
        raise RuntimeError(f"Long-Sedley node diff mismatch: {sorted(changed ^ expected)}")
    return (
        result,
        quarantine,
        Counter({"kg_nodes_modified": len(changed)}) if changed else Counter(),
    )


def validate_nodes(rows: list[dict[str, Any]]) -> None:
    by_id = {node_id(row): row for row in rows}
    work = metadata(by_id[WORK_ID])
    if work.get("publication_identity") != "two_volume_intellectual_work":
        raise RuntimeError("Long-Sedley work identity is not two-volume")
    if work.get("author_ids") != [LONG_ID, SEDLEY_ID]:
        raise RuntimeError("Long-Sedley work authors are wrong")
    if work.get("isbn") != "978-0521275569" or "volume 1" not in str(
        work.get("isbn_scope")
    ):
        raise RuntimeError("volume 1 ISBN scope is not explicit")
    volume2 = next(
        volume for volume in work.get("volumes", []) if volume.get("volume_number") == 2
    )
    if volume2.get("isbn_10_hardback") != "0521255627" or volume2.get(
        "isbn_10_paperback"
    ) != "0521275571":
        raise RuntimeError("volume 2 ISBNs are wrong")
    local = volume2.get("local_scan_manifestation") or {}
    if local.get("visible_reprint_line_latest_year") != 1998 or local.get(
        "binding_status"
    ) != "unknown_cover_absent":
        raise RuntimeError("local volume 2 manifestation is over-inferred")
    position = metadata(by_id[POSITION_ID])
    if position.get("citability") != "discoverable_only" or position.get(
        "needs_evidence"
    ) is not True:
        raise RuntimeError("priority position is not fail-closed")
    if any(key in position for key in ("citation_verified", "verified_reference")):
        raise RuntimeError("priority position retains generic verified fields")
    if position.get("volume1_claim_audit", {}).get("status") != (
        "typed_pending_do_not_modify_edge"
    ):
        raise RuntimeError("volume 1 priority edge is not typed pending")
    for wanted in OVERLAP_NODE_IDS:
        data = metadata(by_id[wanted])
        if data.get("citability") != "discoverable_only":
            raise RuntimeError(f"Long-Sedley overlap node became citable: {wanted}")
        visual = data.get("long_sedley_vol2_visual_evidence") or {}
        if visual.get("primary_source_status") != (
            "ancient_loci_leads_not_primary_verified"
        ):
            raise RuntimeError(f"volume 2 evidence overstates primary status: {wanted}")
    cylinder = metadata(by_id["argument_cylinder_analogy_chrysippus_k1l2m3n4"])
    if "7.2.6-14" in json.dumps(cylinder, ensure_ascii=False):
        raise RuntimeError("Gellius 62D still extends through paragraph 14")
    for wanted, refs in FALSE_LS_REFS_BY_NODE.items():
        surviving = ls_refs(by_id[wanted])
        if surviving & refs:
            raise RuntimeError(f"false LS reference survived on {wanted}")
    for wanted, spec in EXACT_LS_REFS_BY_NODE.items():
        if spec["reference"] not in ls_refs(by_id[wanted]):
            raise RuntimeError(f"exact LS reference missing on {wanted}")


def mapping_edge(node: str, edge: str, spec: dict[str, Any]) -> dict[str, Any]:
    return {
        "edge_id": edge,
        "relation": "part_of",
        "source": node,
        "source_id": node,
        "target": COLLECTION_ID,
        "target_id": COLLECTION_ID,
        "weight": 1.0,
        "created_at": NOW,
        "metadata": {
            "fragment_reference": spec["reference"],
            "mapping_kind": "printed_as_exact_excerpt",
            "source_volume": 2,
            "printed_pages": spec["printed_pages"],
            "pdf_pages": spec["pdf_pages"],
            "scan_sha256": SCAN_SHA256,
            "primary_recollation_status": "pending",
            STAMP: True,
        },
    }


def desired_modified_gellius_edge(old: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(old)
    spec = EXACT_LS_REFS_BY_NODE["passage_gellius_na_vii_2_7_2_3"]
    result["metadata"] = {
        "fragment_reference": "55K",
        "mapping_kind": "printed_as_exact_excerpt",
        "source_volume": 2,
        "printed_pages": spec["printed_pages"],
        "pdf_pages": spec["pdf_pages"],
        "scan_sha256": SCAN_SHA256,
        "primary_recollation_status": "pending",
        STAMP: True,
    }
    return result


def new_edge_records() -> list[dict[str, Any]]:
    records = [
        mapping_edge(node, edge, EXACT_LS_REFS_BY_NODE[node])
        for node, edge in sorted(NEW_MAPPING_EDGE_IDS.items())
    ]
    records.append(
        {
            "edge_id": WORK_SEDLEY_EDGE_ID,
            "relation": "authored_by",
            "source": WORK_ID,
            "source_id": WORK_ID,
            "target": SEDLEY_ID,
            "target_id": SEDLEY_ID,
            "weight": 1.0,
            "created_at": NOW,
            "metadata": {
                "role": "co_author",
                "basis": "volume 2 title page visually verified",
                "scan_sha256": SCAN_SHA256,
                STAMP: True,
            },
        }
    )
    return records


def transform_edges(
    rows: list[dict[str, Any]], *, state: str
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], Counter[str]]:
    by_id = {edge_id(row): row for row in rows}
    if len(by_id) != len(rows):
        raise PreconditionsError("duplicate KG edge identity")
    if state == "before":
        missing = sorted((REMOVED_EDGE_IDS | {MODIFIED_EDGE_ID}) - by_id.keys())
        present_new = sorted(NEW_EDGE_IDS & by_id.keys())
        if missing or present_new:
            raise PreconditionsError(
                f"Long-Sedley edge precondition mismatch: missing={missing}, new={present_new}"
            )
    result: list[dict[str, Any]] = []
    quarantine: list[dict[str, Any]] = []
    for row in rows:
        wanted = edge_id(row)
        if wanted in REMOVED_EDGE_IDS:
            if state == "before":
                quarantine.append({"record_type": "kg_edge_removed", "record": row})
            continue
        if wanted == MODIFIED_EDGE_ID:
            if state == "before":
                quarantine.append({"record_type": "kg_edge_before", "record": row})
            result.append(desired_modified_gellius_edge(row))
            continue
        result.append(copy.deepcopy(row))
    existing = {edge_id(row): row for row in result}
    desired_new = {edge_id(row): row for row in new_edge_records()}
    for wanted, row in desired_new.items():
        old = existing.get(wanted)
        if old is None:
            result.append(row)
            existing[wanted] = row
            if state == "before":
                quarantine.append(
                    {"record_type": "kg_edge_absence_before", "edge_id": wanted}
                )
        elif old != row:
            raise PreconditionsError(f"conflicting Long-Sedley new edge: {wanted}")
    validate_edges(result)
    before_map = {edge_id(row): row for row in rows}
    after_map = {edge_id(row): row for row in result}
    removed = set(before_map) - set(after_map)
    added = set(after_map) - set(before_map)
    modified = {
        wanted
        for wanted in set(before_map) & set(after_map)
        if before_map[wanted] != after_map[wanted]
    }
    expected = (
        (set(REMOVED_EDGE_IDS), set(NEW_EDGE_IDS), {MODIFIED_EDGE_ID})
        if state == "before"
        else (set(), set(), set())
    )
    if (removed, added, modified) != expected:
        raise RuntimeError(
            f"Long-Sedley edge diff mismatch: removed={removed}, added={added}, modified={modified}"
        )
    counts = Counter()
    if removed:
        counts["kg_edges_removed"] = len(removed)
        counts["kg_edges_added"] = len(added)
        counts["kg_edges_modified"] = len(modified)
    return result, quarantine, counts


def validate_edges(rows: list[dict[str, Any]]) -> None:
    by_id = {edge_id(row): row for row in rows}
    if REMOVED_EDGE_IDS & by_id.keys():
        raise RuntimeError("false Long-Sedley collection edge survived")
    if not by_id.keys() >= NEW_EDGE_IDS:
        raise RuntimeError("new Long-Sedley exact edges are incomplete")
    gellius = by_id[MODIFIED_EDGE_ID]
    if gellius.get("metadata", {}).get("fragment_reference") != "55K":
        raise RuntimeError("Gellius 7.2.3 was not remapped to LS 55K")
    if canonical_hash(by_id[AG026_EDGE_ID]) != AG026_BEFORE_HASH:
        raise RuntimeError("ag_026 volume 1 advanced_in edge changed")
    authored = {
        str(row.get("target_id") or row.get("target"))
        for row in rows
        if str(row.get("source_id") or row.get("source")) == WORK_ID
        and row.get("relation") == "authored_by"
    }
    if authored != {LONG_ID, SEDLEY_ID}:
        raise RuntimeError(f"Long-Sedley authored_by set is wrong: {authored}")
    triples = Counter(
        (str(row.get("source")), str(row.get("relation")), str(row.get("target")))
        for row in rows
    )
    if any(count > 1 for count in triples.values()):
        raise RuntimeError("duplicate edge triple after Long-Sedley transform")


def desired_builder_bytes(current: bytes) -> bytes:
    text = current.decode("utf-8")
    if NEW_LONG_BUILDER_BLOCK in text and OLD_LONG_BUILDER_BLOCK not in text:
        return current
    if text.count(OLD_LONG_BUILDER_BLOCK) != 1:
        raise PreconditionsError("exact Long-Sedley builder curation block not found")
    return text.replace(OLD_LONG_BUILDER_BLOCK, NEW_LONG_BUILDER_BLOCK).encode("utf-8")


def execute_candidate_literature_builder(
    builder_bytes: bytes, root: Path
) -> list[dict[str, Any]]:
    namespace: dict[str, Any] = {
        "__file__": str(root / LITERATURE_BUILDER_RELATIVE),
        "__name__": "long_sedley_candidate_literature_builder",
    }
    exec(
        compile(
            builder_bytes.decode("utf-8"),
            str(root / LITERATURE_BUILDER_RELATIVE),
            "exec",
        ),
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
    added = set(after_rows) - set(before_rows)
    removed = set(before_rows) - set(after_rows)
    expected = {LITERATURE_ARTIFACT_ID} if state == "before" else set()
    if changed != expected or added or removed:
        raise RuntimeError(
            f"literature builder diff escaped Long-Sedley row: changed={changed}, added={added}, removed={removed}"
        )
    row = after_rows[LITERATURE_ARTIFACT_ID]
    if row.get("content_completeness") != "full" or row.get(
        "physical_completeness"
    ) != "incomplete":
        raise RuntimeError("literature completeness scopes are not separated")
    if row.get("visible_reprint_line_latest_year") != 1998 or row.get(
        "binding_status"
    ) != "unknown_cover_absent":
        raise RuntimeError("literature manifestation over-infers printing/binding")
    if row.get("isbn_10_hardback") != "0521255627" or row.get(
        "isbn_10_paperback"
    ) != "0521275571":
        raise RuntimeError("literature manifest volume 2 ISBNs are wrong")
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
                    "old_block_sha256": sha256_bytes(
                        OLD_LONG_BUILDER_BLOCK.encode("utf-8")
                    ),
                },
            ]
        )
        counts["literature_builder_modified"] = 1
        counts["literature_manifest_rows_modified"] = 1
    return builder_after, manifest_after, quarantine, counts


def scholarly_manifest_row() -> dict[str, Any]:
    return {
        "manifest_schema_version": "2.0.0",
        "publication_dir": SCHOLARLY_PUBLICATION_DIR,
        "bibtex_key": "publication-1987-the-hellenistic-philosophers-2-vols",
        "kg_publication_id": WORK_ID,
        "title": "The Hellenistic Philosophers, Volume 2: Greek and Latin Texts with Notes and Bibliography",
        "author": "A. A. Long and D. N. Sedley",
        "year_original": 1987,
        "year_edition_used": 1998,
        "edition_used": (
            "Volume 2 scan with visible reprint line through 1998; exact local "
            "printing and binding unknown"
        ),
        "language_primary": "grc",
        "languages_secondary": ["la", "en"],
        "kg_ingestion_status": "partial",
        "ingestion_scope": (
            "Bibliographic identity, page map, LS20/LS55/LS62 secondary evidence "
            "and bounded exact editorial mappings; no primary recollation or "
            "complete volume 1 commentary audit."
        ),
        "kg_ingestion_batches": ["long_sedley_vol2_p0_20260824"],
        "kg_node_count": None,
        "added_to_archive": "2026-08-24",
        "last_updated": "2026-08-24",
        "pdf_sha256": SCAN_SHA256,
        "pdf_md5": SCAN_MD5,
        "pdf_size_bytes": SCAN_BYTES,
        "page_count": SCAN_PAGES,
        "page_map": "printed body page = PDF page - 8",
        "page_map_status": "visually_verified",
        "content_completeness": "full_scholarly_main_content",
        "physical_completeness": "incomplete_cover_and_preliminaries_i_ii_absent",
        "local_printing_year": None,
        "local_printing_status": "reprint_line_through_1998_exact_printing_unknown",
        "binding_status": "unknown_cover_absent",
        "isbn_10_hardback": "0521255627",
        "isbn_10_paperback": "0521275571",
        "reuse_status": "unverified_do_not_republish",
        "quotation_policy": "internal_pointers_and_paraphrases_only",
        STAMP: True,
    }


def transform_scholarly_manifest(
    rows: list[dict[str, Any]], *, state: str
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], Counter[str]]:
    result = copy.deepcopy(rows)
    desired = scholarly_manifest_row()
    matches = [row for row in result if row.get("publication_dir") == SCHOLARLY_PUBLICATION_DIR]
    if not matches:
        result.append(desired)
        if state != "before":
            raise PreconditionsError("applied scholarly manifest row disappeared")
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
        raise PreconditionsError("conflicting Long-Sedley scholarly manifest row")
    from scripts.check_scholarly_sources_manifest import validate

    errors = validate(result)
    if errors:
        raise RuntimeError(f"scholarly manifest invalid: {errors}")
    return result, quarantine, counts


def transform_source_record(record: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(record)
    result["canonical_identifiers"] = {
        "kg_two_volume_work_id": WORK_ID,
        "isbn_10_volume2_hardback": "0521255627",
        "isbn_10_volume2_paperback": "0521275571",
        "local_scan_sha256": SCAN_SHA256,
    }
    result["acquisition"] = {
        "status": "archived_verified",
        "manifest_publication_dirs": [SCHOLARLY_PUBLICATION_DIR],
        "artifacts": [
            {"locator": SCAN_RELATIVE, "role": "source_file", "sha256": SCAN_SHA256},
            {"locator": AUDIT_RELATIVE, "role": "audit_report", "sha256": AUDIT_SHA256},
        ],
    }
    result["coverage"] = {
        "state": "partial",
        "kg_node_ids": sorted(TOUCHED_NODE_IDS),
        "basis": (
            "Volume 2 bibliographic identity and LS20, LS55 and LS62 page maps "
            "are visually checked. Exact editorial mappings are bounded; volume 1 "
            "commentary and all ancient primary loci remain pending."
        ),
        "last_audited": "2026-08-24",
    }
    result["provenance"] = [
        {"locator": SCAN_RELATIVE, "role": "source_file", "sha256": SCAN_SHA256},
        {"locator": AUDIT_RELATIVE, "role": "audit_report", "sha256": AUDIT_SHA256},
    ]
    result["notes"] = (
        "The local artifact is volume 2. The visible printing history extends "
        "through 1998, but exact printing and binding are not inferred because the "
        "cover is absent. Main scholarly content is continuous from title page "
        "through bibliography; physical preliminaries i-ii are absent. Volume 2 is "
        "editorial secondary evidence, not independent ancient-primary collation."
    )
    return result


def evidence_record(
    evidence_id: str,
    *,
    section: str,
    printed: tuple[int, int],
    pdf: tuple[int, int],
    claim: str,
    targets: list[str],
) -> dict[str, Any]:
    return {
        "record_type": "evidence",
        "evidence_id": evidence_id,
        "source_id": SOURCE_ID,
        "evidence_kind": "secondary_claim",
        "claim_text": claim,
        "attestation": "reported_interpretation",
        "claim_status": "in_review",
        "locator": {
            "canonical_locus": f"Long-Sedley volume 2 section {section}",
            "edition_or_witness": (
                "Volume 2 original-language texts and editorial notes; local scan "
                "with reprint line through 1998"
            ),
            "printed_pages": {"start": printed[0], "end": printed[1]},
            "pdf_pages": {"start": pdf[0], "end": pdf[1]},
            "page_map_status": "visually_verified",
        },
        "quotation": {"status": "paraphrase_only", "language": "eng"},
        "kg_targets": targets,
        "required_verification": [
            "locus_or_page",
            "textual_exactness",
            "semantic_entailment",
            "attribution",
            "independent_review",
            "adversarial_review",
        ],
        "notes": (
            "Copyright-safe secondary-source paraphrase. Ancient witnesses and "
            "parallel collection numbers are leads, not primary-verified evidence."
        ),
    }


def desired_evidence_records() -> list[dict[str, Any]]:
    return [
        evidence_record(
            LS20_EVIDENCE_ID,
            section="20",
            printed=(104, 113),
            pdf=(112, 121),
            claim=(
                "Section 20 assembles the Epicurean responsibility dossier. Its "
                "editorial note treats the swerve at most as necessary, not "
                "sufficient, and does not establish Epicurean historical priority."
            ),
            targets=[POSITION_ID, "concept_clinamen_atomic_swerve_epicurus_m3n4o5p6"],
        ),
        evidence_record(
            LS55_EVIDENCE_ID,
            section="55",
            printed=(332, 341),
            pdf=(340, 349),
            claim=(
                "Section 55 is a multi-witness dossier on Stoic causation and fate. "
                "Transmitters and critics must remain distinct; it does not state "
                "one univocal compatibilist doctrine."
            ),
            targets=["argument_chrysippus_causal_taxonomy", "debate_stoic_compatibilism"],
        ),
        evidence_record(
            LS62_EVIDENCE_ID,
            section="62",
            printed=(382, 389),
            pdf=(390, 397),
            claim=(
                "Section 62 distinguishes the external initiating condition and "
                "the agent's internal nature, while hostile and later witnesses "
                "leave the modal and moral success of that account disputed."
            ),
            targets=[
                "argument_chrysippus_causal_taxonomy",
                "argument_cylinder_analogy_chrysippus_k1l2m3n4",
                "concept_cylinder_analogy_chrysippus_e5f6g7h8",
                "argument_the_dog_and_cart_argument_9ba60714",
                "debate_stoic_compatibilism",
            ],
        ),
    ]


def desired_issue_records() -> list[dict[str, Any]]:
    common_artifacts = [
        {"locator": AUDIT_RELATIVE, "role": "audit_report", "sha256": AUDIT_SHA256},
        {"locator": SCAN_RELATIVE, "role": "source_file", "sha256": SCAN_SHA256},
    ]
    return [
        {
            "record_type": "issue",
            "issue_id": MANIFESTATION_ISSUE_ID,
            "issue_type": "bibliographic_identity",
            "severity": "medium",
            "factual_risk": True,
            "status": "open",
            "summary": (
                "The scan shows volume 2 and a reprint line through 1998, but the "
                "missing cover prevents identification of exact printing and binding."
            ),
            "affected_ids": [SOURCE_ID, WORK_ID],
            "evidence_artifacts": common_artifacts,
            "resolution_criteria": (
                "Collate against a physical copy with cover and full preliminaries; "
                "do not infer an exact post-1998 printing or binding."
            ),
        },
        {
            "record_type": "issue",
            "issue_id": PRIORITY_ISSUE_ID,
            "issue_type": "disputed_interpretation",
            "severity": "high",
            "factual_risk": True,
            "status": "open",
            "summary": (
                "Volume 2 does not verify that Epicurus first posed the free-will "
                "question. The claim remains attributed and disputed pending volume "
                "1 and Huby; the clinamen is at most necessary, not sufficient."
            ),
            "affected_ids": [
                POSITION_ID,
                "concept_clinamen_atomic_swerve_epicurus_m3n4o5p6",
            ],
            "evidence_artifacts": common_artifacts,
            "resolution_criteria": (
                "Audit Long-Sedley volume 1 section 20 and Huby 1967, compare the "
                "Bobzien/O'Keefe objections, and independently adjudicate priority "
                "without upgrading a merely necessary condition to a direct cause."
            ),
        },
        {
            "record_type": "issue",
            "issue_id": RECOLLATION_ISSUE_ID,
            "issue_type": "coverage_gap",
            "severity": "high",
            "factual_risk": True,
            "status": "open",
            "summary": (
                "Exact LS sigla are repaired only where volume 2 and an existing KG "
                "passage align. Most LS20/55/62 units and all ancient texts still "
                "require independent primary recollation."
            ),
            "affected_ids": sorted(
                {
                    COLLECTION_ID,
                    *FALSE_LS_REFS_BY_NODE,
                    *EXACT_LS_REFS_BY_NODE,
                    *OVERLAP_NODE_IDS,
                }
            ),
            "affected_count": len(
                {COLLECTION_ID, *FALSE_LS_REFS_BY_NODE, *EXACT_LS_REFS_BY_NODE, *OVERLAP_NODE_IDS}
            ),
            "evidence_artifacts": common_artifacts,
            "resolution_criteria": (
                "Recollate every ancient locus against an identified critical "
                "edition, model transmitters separately and create no missing "
                "passage unit solely from the sourcebook mapping."
            ),
        },
    ]


def verification_records() -> list[dict[str, Any]]:
    verifier = {
        "verifier_id": "agent_long_sedley_volume2_visual_audit_20260824",
        "kind": "agent",
        "independence_group": "long_sedley_primary_visual_audit",
    }
    source_artifacts = [
        {"locator": AUDIT_RELATIVE, "role": "audit_report", "sha256": AUDIT_SHA256},
        {"locator": SCAN_RELATIVE, "role": "source_file", "sha256": SCAN_SHA256},
    ]
    records = [
        {
            "record_type": "verification",
            "verification_id": "ver_long_sedley_vol2_source_identity_20260824",
            "target_type": "source",
            "target_id": SOURCE_ID,
            "stage": "identity",
            "verifier": verifier,
            "method": "Visual title, copyright, contents and pagination review",
            "checked_locators": ["PDF 1-8", "PDF 484-520"],
            "verdict": "pass",
            "created_at": ACCESSED_AT,
            "artifacts": source_artifacts,
            "notes": (
                "Pass is limited to volume identity, visible reprint line, hashes "
                "and page map; it is not independent review or primary recollation."
            ),
        }
    ]
    pages = {
        LS20_EVIDENCE_ID: "printed 104-113 / PDF 112-121",
        LS55_EVIDENCE_ID: "printed 332-341 / PDF 340-349",
        LS62_EVIDENCE_ID: "printed 382-389 / PDF 390-397",
    }
    suffix = {
        LS20_EVIDENCE_ID: "ls20",
        LS55_EVIDENCE_ID: "ls55",
        LS62_EVIDENCE_ID: "ls62",
    }
    for target in ALL_LS_EVIDENCE_IDS:
        records.append(
            {
                "record_type": "verification",
                "verification_id": f"ver_long_sedley_vol2_{suffix[target]}_primary_20260824",
                "target_type": "evidence",
                "target_id": target,
                "stage": "primary",
                "verifier": verifier,
                "method": "Two-pass visual review of the modern sourcebook pages",
                "checked_locators": [pages[target]],
                "verdict": "pass",
                "created_at": ACCESSED_AT,
                "artifacts": source_artifacts,
                "notes": (
                    "Primary stage here means direct inspection of Long-Sedley "
                    "volume 2 only; ancient primary text, independent review, "
                    "adversarial review and human signoff remain unperformed."
                ),
            }
        )
    return records


def transform_registry(
    sources: list[dict[str, Any]],
    evidence: list[dict[str, Any]],
    issues: list[dict[str, Any]],
    waves: list[dict[str, Any]],
    verifications: list[dict[str, Any]],
    *,
    state: str,
) -> tuple[dict[str, list[dict[str, Any]]], list[dict[str, Any]], Counter[str]]:
    sources = copy.deepcopy(sources)
    evidence = copy.deepcopy(evidence)
    issues = copy.deepcopy(issues)
    waves = copy.deepcopy(waves)
    verifications = copy.deepcopy(verifications)
    quarantine: list[dict[str, Any]] = []
    counts = Counter()

    source_matches = [row for row in sources if row.get("source_id") == SOURCE_ID]
    if len(source_matches) != 1:
        raise PreconditionsError("expected one Long-Sedley registry source")
    source_before = source_matches[0]
    source_after = transform_source_record(source_before)
    sources[sources.index(source_before)] = source_after
    if state == "before":
        quarantine.append({"record_type": "registry_source_before", "record": source_before})
        counts["registry_sources_modified"] = 1

    by_evidence = {row.get("evidence_id"): row for row in evidence}
    if LS20_EVIDENCE_ID not in by_evidence:
        raise PreconditionsError("Long-Sedley LS20 registry evidence missing")
    old_ls20 = by_evidence[LS20_EVIDENCE_ID]
    desired_by_id = {row["evidence_id"]: row for row in desired_evidence_records()}
    evidence[evidence.index(old_ls20)] = desired_by_id[LS20_EVIDENCE_ID]
    old_fused = by_evidence.get(OLD_FUSED_EVIDENCE_ID)
    if old_fused is not None:
        evidence.remove(old_fused)
    for wanted in (LS55_EVIDENCE_ID, LS62_EVIDENCE_ID):
        existing = next((row for row in evidence if row.get("evidence_id") == wanted), None)
        if existing is None:
            evidence.append(desired_by_id[wanted])
        elif existing != desired_by_id[wanted]:
            raise PreconditionsError(f"conflicting Long-Sedley evidence: {wanted}")
    if state == "before":
        if old_fused is None:
            raise PreconditionsError("fused Long-Sedley registry evidence already absent")
        quarantine.extend(
            [
                {"record_type": "registry_evidence_before", "record": old_ls20},
                {"record_type": "registry_evidence_removed", "record": old_fused},
                {"record_type": "registry_evidence_absence_before", "evidence_id": LS55_EVIDENCE_ID},
                {"record_type": "registry_evidence_absence_before", "evidence_id": LS62_EVIDENCE_ID},
            ]
        )
        counts.update(
            {
                "registry_evidence_modified": 1,
                "registry_evidence_removed": 1,
                "registry_evidence_added": 2,
            }
        )

    by_issue = {row.get("issue_id"): row for row in issues}
    archive_issue = by_issue.get(ARCHIVE_GAP_ISSUE_ID)
    if archive_issue is None:
        raise PreconditionsError("secondary archive gap issue missing")
    archive_after = copy.deepcopy(archive_issue)
    archive_after["affected_ids"] = [
        wanted for wanted in archive_after.get("affected_ids", []) if wanted != SOURCE_ID
    ]
    issues[issues.index(archive_issue)] = archive_after
    desired_issues = {row["issue_id"]: row for row in desired_issue_records()}
    for wanted, row in desired_issues.items():
        existing = next((item for item in issues if item.get("issue_id") == wanted), None)
        if existing is None:
            issues.append(row)
        elif existing != row:
            raise PreconditionsError(f"conflicting Long-Sedley issue: {wanted}")
    if state == "before":
        quarantine.append({"record_type": "registry_issue_before", "record": archive_issue})
        for wanted in NEW_ISSUE_IDS:
            quarantine.append(
                {"record_type": "registry_issue_absence_before", "issue_id": wanted}
            )
        counts["registry_issues_modified"] = 1
        counts["registry_issues_added"] = 3

    wave_matches = [row for row in waves if row.get("wave_id") == WAVE_ID]
    if len(wave_matches) != 1:
        raise PreconditionsError("Long-Sedley registry wave missing")
    wave_before = wave_matches[0]
    wave_after = copy.deepcopy(wave_before)
    wave_after["evidence_ids"] = [
        wanted
        for wanted in wave_after.get("evidence_ids", [])
        if wanted != OLD_FUSED_EVIDENCE_ID
    ]
    for wanted in ALL_LS_EVIDENCE_IDS:
        if wanted not in wave_after["evidence_ids"]:
            wave_after["evidence_ids"].append(wanted)
    for wanted in NEW_ISSUE_IDS:
        if wanted not in wave_after["issue_ids"]:
            wave_after["issue_ids"].append(wanted)
        if wanted not in wave_after["blocked_by"]:
            wave_after["blocked_by"].append(wanted)
    criterion = (
        "Long-Sedley volume 2 remains separated from volume 1 commentary; exact "
        "printing/binding, priority claims and ancient loci pass independent, "
        "adversarial and human review before citability is upgraded."
    )
    if criterion not in wave_after["exit_criteria"]:
        wave_after["exit_criteria"].append(criterion)
    waves[waves.index(wave_before)] = wave_after
    if state == "before":
        quarantine.append({"record_type": "registry_wave_before", "record": wave_before})
        counts["registry_waves_modified"] = 1

    desired_verifications = verification_records()
    existing_verifications = {
        row.get("verification_id"): row for row in verifications
    }
    for row in desired_verifications:
        wanted = row["verification_id"]
        old = existing_verifications.get(wanted)
        if old is None:
            verifications.append(row)
            existing_verifications[wanted] = row
            if state == "before":
                quarantine.append(
                    {"record_type": "registry_verification_absence_before", "verification_id": wanted}
                )
        elif old != row:
            raise PreconditionsError(f"conflicting Long-Sedley verification: {wanted}")
    if state == "before":
        counts["registry_primary_verifications_added"] = len(desired_verifications)

    result = {
        "sources": sources,
        "evidence": evidence,
        "issues": issues,
        "waves": waves,
        "verifications": verifications,
    }
    validate_registry(result)
    return result, quarantine, counts


def validate_registry(result: dict[str, list[dict[str, Any]]]) -> None:
    source = next(row for row in result["sources"] if row.get("source_id") == SOURCE_ID)
    if source.get("coverage", {}).get("state") != "partial":
        raise RuntimeError("Long-Sedley registry coverage is not partial")
    if source.get("acquisition", {}).get("status") != "archived_verified":
        raise RuntimeError("Long-Sedley registry acquisition is not reconciled")
    evidence = {
        row.get("evidence_id"): row
        for row in result["evidence"]
        if row.get("evidence_id") in set(ALL_LS_EVIDENCE_IDS)
    }
    if set(evidence) != set(ALL_LS_EVIDENCE_IDS):
        raise RuntimeError("Long-Sedley evidence split is incomplete")
    if any(
        row.get("claim_status") != "in_review"
        or row.get("quotation", {}).get("status") != "paraphrase_only"
        or row.get("locator", {}).get("page_map_status") != "visually_verified"
        for row in evidence.values()
    ):
        raise RuntimeError("Long-Sedley evidence is not fail-closed")
    if any(row.get("evidence_id") == OLD_FUSED_EVIDENCE_ID for row in result["evidence"]):
        raise RuntimeError("fused LS55/LS62 evidence survived")
    issues = {
        row.get("issue_id"): row
        for row in result["issues"]
        if row.get("issue_id") in set(NEW_ISSUE_IDS)
    }
    if set(issues) != set(NEW_ISSUE_IDS) or any(
        row.get("status") != "open" for row in issues.values()
    ):
        raise RuntimeError("Long-Sedley issues are not open")
    reviews = [
        row
        for row in result["verifications"]
        if str(row.get("verification_id") or "").startswith("ver_long_sedley_")
    ]
    if len(reviews) != 4 or any(
        row.get("stage") in {"independent", "adversarial", "human_signoff"}
        for row in reviews
    ):
        raise RuntimeError("Long-Sedley review stages are overstated")
    wave = next(row for row in result["waves"] if row.get("wave_id") == WAVE_ID)
    if not set(NEW_ISSUE_IDS) <= set(wave.get("blocked_by", [])):
        raise RuntimeError("Long-Sedley wave is not blocked by open issues")


def normative_schema_gate(
    root: Path,
    result: dict[str, list[dict[str, Any]]],
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

    def collect(record_type: str, directory: str, key: str) -> dict[str, dict[str, Any]]:
        found: dict[str, dict[str, Any]] = {}
        for path in sorted((registry_root / directory).glob("*.jsonl")):
            for row in read_jsonl(path):
                found[str(row[key])] = row
        return found

    before = {
        record_type: collect(record_type, directory, key)
        for record_type, (directory, key) in configs.items()
    }
    after = copy.deepcopy(before)
    target_before = {
        "source": read_jsonl(root / SOURCES_RELATIVE),
        "evidence": read_jsonl(root / EVIDENCE_RELATIVE),
        "issue": read_jsonl(root / ISSUES_RELATIVE),
        "verification": read_jsonl(root / VERIFICATIONS_RELATIVE),
        "wave": read_jsonl(root / WAVES_RELATIVE),
    }
    target_after = {
        "source": result["sources"],
        "evidence": result["evidence"],
        "issue": result["issues"],
        "verification": result["verifications"],
        "wave": result["waves"],
    }
    for record_type, (_directory, key) in configs.items():
        for row in target_before[record_type]:
            after[record_type].pop(str(row[key]), None)
        for row in target_after[record_type]:
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
        raise PreconditionsError(f"Long-Sedley preview creates registry schema debt: {sorted(new)}")
    touched = {
        "source": {SOURCE_ID},
        "evidence": set(ALL_LS_EVIDENCE_IDS),
        "issue": {ARCHIVE_GAP_ISSUE_ID, *NEW_ISSUE_IDS},
        "verification": {row["verification_id"] for row in verification_records()},
        "wave": {WAVE_ID},
    }
    touched_errors: list[str] = []
    for record_type, identifiers in touched.items():
        for identifier in identifiers:
            for error in validators[record_type].iter_errors(after[record_type][identifier]):
                touched_errors.append(f"{record_type}:{identifier}:{error.message}")
    if touched_errors:
        raise PreconditionsError(f"Long-Sedley touched registry records invalid: {touched_errors}")
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
            f"Long-Sedley preview creates strict debt: before={before}, after={after}"
        )
    return {"before": before, "after_preview": after}


def validate_immutable_files(root: Path) -> None:
    if sha256_file(root / SCAN_RELATIVE) != SCAN_SHA256:
        raise PreconditionsError("Long-Sedley scan hash drift")
    if sha256_file(root / AUDIT_RELATIVE) != AUDIT_SHA256:
        raise PreconditionsError("Long-Sedley audit hash drift")
    for relative, expected in IMMUTABLE_FILE_HASHES.items():
        actual = sha256_file(root / relative)
        if actual != expected:
            raise PreconditionsError(
                f"immutable Long-Sedley dependency drift: {relative}: {actual}"
            )
    cary = json.loads((root / "data/kg/e2_patches/cary.json").read_text(encoding="utf-8"))
    patch = (cary.get("patches") or {}).get(
        "scholarly_argument_cary_hellenistic_positions_on_deter_6"
    )
    if not isinstance(patch, dict) or "102" not in str(patch.get("quote_verbatim") or ""):
        raise PreconditionsError("Cary volume 1 claim was unexpectedly rewritten")


def build_plan(root: Path = ROOT) -> RepairPlan:
    root = root.resolve()
    validate_immutable_files(root)
    states = {relative: file_state(root, relative) for relative in FILE_BEFORE_SHA256}
    if len(set(states.values())) != 1:
        raise PreconditionsError(f"mixed Long-Sedley transaction state: {states}")
    state = next(iter(states.values()))

    nodes_path = root / NODES_RELATIVE
    edges_path = root / EDGES_RELATIVE
    builder_path = root / LITERATURE_BUILDER_RELATIVE
    literature_path = root / LITERATURE_MANIFEST_RELATIVE
    scholarly_path = root / SCHOLARLY_MANIFEST_RELATIVE
    sources_path = root / SOURCES_RELATIVE
    evidence_path = root / EVIDENCE_RELATIVE
    issues_path = root / ISSUES_RELATIVE
    waves_path = root / WAVES_RELATIVE
    verifications_path = root / VERIFICATIONS_RELATIVE

    before_nodes = read_jsonl(nodes_path)
    before_edges = read_jsonl(edges_path)
    builder_bytes = builder_path.read_bytes()
    before_literature = read_jsonl(literature_path)
    before_scholarly = read_jsonl(scholarly_path)
    before_sources = read_jsonl(sources_path)
    before_evidence = read_jsonl(evidence_path)
    before_issues = read_jsonl(issues_path)
    before_waves = read_jsonl(waves_path)
    before_verifications = read_jsonl(verifications_path)

    nodes, node_quarantine, node_counts = transform_nodes(before_nodes, state=state)
    edges, edge_quarantine, edge_counts = transform_edges(before_edges, state=state)
    builder, literature, literature_quarantine, literature_counts = transform_literature(
        root, builder_bytes, before_literature, state=state
    )
    scholarly, scholarly_quarantine, scholarly_counts = transform_scholarly_manifest(
        before_scholarly, state=state
    )
    registry, registry_quarantine, registry_counts = transform_registry(
        before_sources,
        before_evidence,
        before_issues,
        before_waves,
        before_verifications,
        state=state,
    )

    from scripts.export_publications_bibtex import build_publication_export

    if build_publication_export(copy.deepcopy(before_nodes)) != build_publication_export(
        copy.deepcopy(nodes)
    ):
        raise RuntimeError("Long-Sedley node changes alter canonical BibTeX export")

    schema_debt = normative_schema_gate(root, registry)
    ingestion_debt = strict_ingestion_debt(before_nodes, before_edges, nodes, edges)

    outputs = {
        nodes_path: serialize_jsonl_preserving(nodes_path, before_nodes, nodes, node_id),
        edges_path: serialize_jsonl_preserving(edges_path, before_edges, edges, edge_id),
        builder_path: builder,
        literature_path: serialize_jsonl(literature),
        scholarly_path: serialize_jsonl_preserving(
            scholarly_path,
            before_scholarly,
            scholarly,
            lambda row: str(row.get("publication_dir") or ""),
        ),
        sources_path: serialize_jsonl_preserving(
            sources_path,
            before_sources,
            registry["sources"],
            lambda row: str(row.get("source_id") or ""),
        ),
        evidence_path: serialize_jsonl_preserving(
            evidence_path,
            before_evidence,
            registry["evidence"],
            lambda row: str(row.get("evidence_id") or ""),
        ),
        issues_path: serialize_jsonl_preserving(
            issues_path,
            before_issues,
            registry["issues"],
            lambda row: str(row.get("issue_id") or ""),
        ),
        waves_path: serialize_jsonl_preserving(
            waves_path,
            before_waves,
            registry["waves"],
            lambda row: str(row.get("wave_id") or ""),
        ),
        verifications_path: serialize_jsonl(registry["verifications"]),
    }
    current_bytes = {
        path: path.read_bytes() if path.exists() else None for path in outputs
    }
    if state == "before":
        for path, payload in outputs.items():
            expected = FILE_AFTER_SHA256[str(path.relative_to(root))]
            if not expected.startswith("__") and sha256_bytes(payload) != expected:
                raise RuntimeError(f"Long-Sedley frozen after hash mismatch: {path}")
    else:
        if any(current_bytes[path] != payload for path, payload in outputs.items()):
            raise PreconditionsError("Long-Sedley after-state is not idempotent")

    counts = Counter()
    for current in (
        node_counts,
        edge_counts,
        literature_counts,
        scholarly_counts,
        registry_counts,
    ):
        counts.update(current)
    quarantine = [
        *node_quarantine,
        *edge_quarantine,
        *literature_quarantine,
        *scholarly_quarantine,
        *registry_quarantine,
    ]
    changed_paths = [
        str(path.relative_to(root))
        for path, payload in outputs.items()
        if current_bytes[path] != payload
    ]
    summary = {
        "mode": "dry_run",
        "status": (
            "ready_for_independent_re_review_no_apply"
            if state == "before"
            else "already_applied"
        ),
        "write_performed": False,
        "counts": dict(sorted(counts.items())),
        "changed_paths": changed_paths,
        "touched_node_ids": sorted(TOUCHED_NODE_IDS),
        "removed_edge_ids": sorted(REMOVED_EDGE_IDS),
        "modified_edge_ids": [MODIFIED_EDGE_ID],
        "added_edge_ids": sorted(NEW_EDGE_IDS),
        "citation_rows_modified": 0,
        "corpus_files_modified": 0,
        "bibtex_files_modified": 0,
        "e2_files_modified": 0,
        "quarantine_record_count": len(quarantine),
        "source_artifacts": {
            "scan_sha256": SCAN_SHA256,
            "scan_md5": SCAN_MD5,
            "audit_sha256": AUDIT_SHA256,
        },
        "snapshot_a_file_sha256": {
            str(path.relative_to(root)): (
                sha256_bytes(payload) if payload is not None else None
            )
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
            "edges_removed": {
                edge_id(row["record"]): canonical_hash(row["record"])
                for row in edge_quarantine
                if row["record_type"] == "kg_edge_removed"
            },
            "edges_modified": {
                edge_id(row["record"]): canonical_hash(row["record"])
                for row in edge_quarantine
                if row["record_type"] == "kg_edge_before"
            },
        },
        "after_record_hashes": {
            "nodes": {
                node_id(row): canonical_hash(row)
                for row in nodes
                if node_id(row) in TOUCHED_NODE_IDS
            },
            "edges_modified_or_added": {
                edge_id(row): canonical_hash(row)
                for row in edges
                if edge_id(row) in ({MODIFIED_EDGE_ID} | set(NEW_EDGE_IDS))
            },
        },
        "registry_schema_debt": schema_debt,
        "strict_ingestion_debt": ingestion_debt,
        "open_issue_ids": list(NEW_ISSUE_IDS),
        "review_status": {
            "primary_visual": "recorded",
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
        tmp = Path(handle.name)
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
    try:
        replace_path(tmp, path)
        fsync_directory(path.parent)
    finally:
        tmp.unlink(missing_ok=True)


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
        (json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode(
            "utf-8"
        ),
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
        raise PreconditionsError("pending Long-Sedley transaction requires recovery")
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
        changed = [
            path for path, payload in outputs.items() if before_bytes[path] != payload
        ]
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
                    "before_sha256": (
                        sha256_bytes(original) if original is not None else None
                    ),
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
                raise RuntimeError(f"missing Long-Sedley recovery backup: {backup}")
            payload = backup.read_bytes()
            if sha256_bytes(payload) != entry.get("before_sha256"):
                raise RuntimeError(f"corrupt Long-Sedley recovery backup: {backup}")
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
        raise RuntimeError("foreign transaction journal at Long-Sedley path")
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
                raise RuntimeError(f"staged Long-Sedley payload drift: {staged}")
            replace_path(staged, target)
            targets_replaced = True
            fsync_directory(target.parent)
            journal["committed_targets"].append(entry["target"])
            write_journal(journal_path, journal)
            if fail_after is not None and index >= fail_after:
                raise InjectedTransactionAbort("injected Long-Sedley hard abort")
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
        raise PreconditionsError("refusing to overwrite Long-Sedley report/quarantine")
    applied_report = copy.deepcopy(plan.summary)
    applied_report["mode"] = "write"
    applied_report["status"] = "applied_open_issues_pending_review"
    applied_report["write_performed"] = True
    outputs = dict(plan.outputs)
    outputs[report_path] = (
        json.dumps(applied_report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    outputs[quarantine_path] = serialize_jsonl(plan.quarantine)
    snapshot_a = dict(plan.before_bytes)
    snapshot_a[report_path] = None
    snapshot_a[quarantine_path] = None

    def post_validate() -> None:
        followup = build_plan(plan.root)
        if followup.counts:
            raise RuntimeError(
                f"Long-Sedley post-write is not idempotent: {followup.counts}"
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
        repeated["mode"] = "write"
        repeated["status"] = "already_applied"
        repeated["write_performed"] = False
        return repeated
    report_path = root / REPORT_RELATIVE
    if not report_path.is_file():
        raise RuntimeError("successful Long-Sedley write did not persist its report")
    applied = json.loads(report_path.read_text(encoding="utf-8"))
    if (
        applied.get("mode") != "write"
        or applied.get("status") != "applied_open_issues_pending_review"
        or applied.get("write_performed") is not True
    ):
        raise RuntimeError("persisted Long-Sedley report has misleading status")
    return applied


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--inject-failure-after", type=int, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    root = args.root.expanduser().resolve()
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
            print(f"Long-Sedley repair BLOCKED: {exc}", file=sys.stderr)
        return 2
    result = cli_result_summary(root, plan, write_requested=args.write)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print("Long-Sedley volume 2 P0 repair")
        print("mode:", result["mode"].upper())
        print("status:", result["status"])
        for name, count in sorted(result.get("counts", {}).items()):
            print(f"{name}: {count}")
        print("changed paths:", len(result.get("changed_paths", [])))
        for path in result.get("changed_paths", []):
            print(" -", path)
        print(
            "quarantine records:",
            result.get("quarantine_record_count", len(plan.quarantine)),
        )
        if not args.write:
            print("dry-run: nothing written; --write requires root approval")
        elif result["write_performed"]:
            print("write complete; Long-Sedley issues remain OPEN")
        else:
            print("already applied; no write performed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
