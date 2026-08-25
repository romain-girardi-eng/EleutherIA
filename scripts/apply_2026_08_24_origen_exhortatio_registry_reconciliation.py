#!/usr/bin/env python3
"""Reconcile only the SOTA registry after Origen Exhortatio Wave 0.2.

Dry-run is the default.  ``--write`` updates three existing registry shards and
creates dedicated evidence/verification shards as one staged, fsynced cohort.
It never writes KG, corpus, manifest, bibliography, or data/audit files.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import shutil
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_ROOT = ROOT / "data/goals/sota/registry"

STAMP = "origen_exhortatio_registry_reconciliation_2026_08_24"
SOURCE_ID = "src_anc_origen_exhortatio_martyrium"
ISSUE_ID = "issue_origen_manifestation_language_and_witness_conflation"
WAVE_ID = "wave_00_known_factual_blockers"
EVIDENCE_ID = "ev_anc_origen_exhortatio_51_grc_ogl"

SOURCE_REL = Path("sources/origen_manifestations_20260824.jsonl")
ISSUE_REL = Path("issues/origen_manifestations_20260824.jsonl")
WAVE_REL = Path("waves/priority_20260824.jsonl")
EVIDENCE_REL = Path("evidence/origen_exhortatio_20260824.jsonl")
VERIFICATION_REL = Path("verifications/origen_exhortatio_20260824.jsonl")

LEGACY_FILE_SHA256 = {
    SOURCE_REL.as_posix(): "b7f1627c17088c9fd2bb02ba093da5ecac3a5feb3eb2c9a792d7b53c3f1ae77a",
    ISSUE_REL.as_posix(): "caa350a8c6b1fba4681bf35cac76345ac38d3506f7a90fdc30e0a43b02e78606",
    WAVE_REL.as_posix(): "5e029f085f32a70a91a260d9db35d1362f5763200c5a74a33da4ec20a83ccef4",
}

OGL_COMMIT = "7881c563436f52fb3550e6daa6df94be1b83b0e3"
OGL_CTS_SHA256 = "cc1a2aed4c7807ae514dd155c3a3bac0afe7f4b745df51a4d167373f598229c0"
OGL_TEI_SHA256 = "dedb6ae89519545a0ab274061c858a0549760bb3ac97223a5f744130c13fb83b"
REPAIR_REPORT_SHA256 = "044a7c776a704c908e8b4bbf2db84f9c21ccaa78a753e57663231876b9e6373c"
QUARANTINE_SHA256 = "de2c5787a3d0c5322949366d3e8c67a0a12c5d3327d64303a6a5436d16a08d55"
ALIASES_SHA256 = "338f2bfc7a069f21c1dd322f298bb42e2e43f603db27ff0f2397bf1d8402f613"
NFC_TEXT_COHORT_SHA256 = "3b6d41daf9d99ab2e0536d3c88b3da602497cde50b5ce0d61d0f48aab02b146d"

CORPUS_PASSAGE_IDS = [
    "f3484ad4-29bd-4576-9006-b50fcf34e6ec", "3a74341d-2463-4784-9904-b0c268647ef6",
    "f2d29d9f-7e79-4b02-ad01-45c64a646c12", "0b64edb9-b40c-4374-8a31-12a7c4fafed0",
    "f4eab684-51d7-4b7f-be9b-1d9b6f2fa798", "e2106d48-20d3-46d0-9132-c9c643abf50e",
    "d3b192ab-1f57-41fe-9db5-36b7746dd52f", "088c3ba8-b886-4bfd-b192-fa3399edeb7e",
    "15a3f7da-fac3-4128-a614-45b356a256e8", "2e0fec49-391e-4fd8-8eba-511646bc8e28",
    "f2772f49-e518-452b-8ca1-a3e30008060c", "775f2bdc-5ab3-4692-9370-db4a4f589431",
    "9789ad23-ebdc-4b11-9d53-d7563ed31fda", "79af92d0-5923-426e-a00d-94a795d43462",
    "7d5e584b-0eab-4bcd-9e71-fad76d5fa652", "977304bd-ebee-4881-afc5-61fc1a48c51e",
    "7d4fc416-a557-46bf-80c1-68ae4dca4508", "4fee25a2-1ee7-4c05-8410-165eac5faaaa",
    "07d19681-4a7b-404e-9767-6ad98a8e33db", "4efe0979-666f-42f2-8a85-8029f11d52e6",
    "b48344c2-e76b-4cc3-b60b-2ca0ddbce777", "960fd9c3-a762-49b5-ae4c-8780826a8e09",
    "6e820803-28ca-42e9-83f8-dedcde157ddc", "4772e0c9-571b-4b02-84a0-647834d362ca",
    "098dc50f-8503-4291-92fc-07839e2b3772", "f512b162-d7bb-4a91-9fb8-839f309c5c30",
    "18c4aba1-3e92-4e01-ab30-f0563625b260", "0e34969d-25ef-463d-a5f9-812fa1f2020c",
    "0720a88d-d8d5-487b-a48a-ddce0ab07a82", "ad6c95bc-6f50-4857-a554-09376b0e3957",
    "fd688027-ce45-480e-8cf8-e8a2863a245d", "aa027d83-7934-4624-9c25-866b2f536293",
    "cb09b449-9ac6-4813-b9f4-513c03766814", "df71675c-4929-4773-a428-2191471c518d",
    "5c788f80-077d-459d-82e9-3a35f93b232e", "c3693478-3183-47c7-932c-7e3009b1d345",
    "13761287-6589-42ad-9299-5a4d291d9851", "6ae75e33-8fc6-42ea-a4f7-d9a09f974ef6",
    "6bb9057d-4354-4ded-902c-84b511d51899", "f2df024b-93fc-4ab1-b63f-bb257e50ec2a",
    "b07726c0-5f96-4c35-9cc3-2397e7e7d5d9", "329853ad-7d4c-45a9-b9ce-fec1e1f1e81b",
    "c1b79f13-e8a0-4e23-b73a-dffe640637b2", "25ad2e37-1e2e-42a8-87c9-78e838693f44",
    "9ed367fe-8ba2-4384-8283-d50138be5ab0", "a322ed51-84b6-4ddc-a658-4a28c1bd0dc0",
    "4cab2d74-4fa7-46dc-b025-4d0ecfa39c61", "4603f28b-f8d9-4d65-b436-47a61aa58b4c",
    "bce2fd45-07d3-4e5b-8a64-72a7d6aac9ea", "dce15661-0ede-4077-a49f-487b60c4c80b",
    "742f54f8-141a-40ac-8965-0b5915f354bc",
]
PASSAGE_NODE_IDS = [f"passage_origen_exh_mart_{section}" for section in range(1, 52)]

LEGACY_SOURCE_BASIS = (
    "All 51 Greek chapter texts are NFC-exact to pinned OGL/Perseus, but the "
    "manifest remains mislabeled Clement/Protrepticus and two work nodes "
    "contradict the text identity."
)
LEGACY_ISSUE_SUMMARY = (
    "Ten current Origen manifestation cohorts conflate work identities, ancient "
    "witnesses, languages and translations. Exhortatio has exact Greek but a "
    "Clement/Protrepticus manifest; De principiis Greek is an indirect Philocalia "
    "21 witness while 23 _eng rows are French translations of Rufinus's Latin; "
    "all 51 Philocalia rows are French despite _grc/_eng and use false "
    "tlg028/pseudo-CTS; two Commentary on Romans Latin loci are recoverable but "
    "the manifest uses Contra Celsum/tlg012 and all four snapshots/English rows "
    "are false or mismatched."
)
LEGACY_RESOLUTION_CRITERIA = (
    "Apply the documented fail-closed order Exhortatio -> Romans Latin -> "
    "Philocalia -> De principiis: separate every work/witness/language/translator "
    "manifestation, quarantine mixed notes/resumes/pseudo-CTS and false snapshots, "
    "ingest exact Rufinus Latin before linking SC268 French, encode Philocalia "
    "source-work/compilers, replay semantic citations against the correct witness, "
    "preserve all explicit unknowns, and pass role/language/snapshot/dedup/staged/"
    "bootstrap plus independent/adversarial reviews."
)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def encode_jsonl(rows: list[dict[str, Any]]) -> bytes:
    return ("\n".join(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) for row in rows) + "\n").encode()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def file_sha256(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def find_one(rows: list[dict[str, Any]], key: str, value: str) -> dict[str, Any]:
    found = [row for row in rows if row.get(key) == value]
    if len(found) != 1:
        raise RuntimeError(f"expected one {key}={value}, found {len(found)}")
    return found[0]


def legacy_source_record(current: dict[str, Any]) -> dict[str, Any]:
    row = copy.deepcopy(current)
    row["acquisition"] = {
        "status": "public_canonical",
        "manifest_publication_dirs": [],
        "artifacts": [
            {
                "locator": "data/audit/2026-08-24_origen_manifestation_conflicts_readonly_audit.md",
                "role": "audit_report",
            }
        ],
    }
    row["coverage"] = {
        "state": "partial",
        "kg_node_ids": ["work_origen_exhortation_martyrdom"],
        "basis": LEGACY_SOURCE_BASIS,
        "last_audited": "2026-08-24",
    }
    row["provenance"] = [
        {
            "locator": "data/audit/2026-08-24_origen_manifestation_conflicts_readonly_audit.md",
            "role": "audit_report",
        },
        {
            "accessed_at": "2026-08-24T05:15:00Z",
            "locator": f"https://github.com/OpenGreekAndLatin/First1KGreek/blob/{OGL_COMMIT}/data/tlg2042/tlg007/__cts__.xml",
            "role": "authority_record",
        },
    ]
    row.pop("notes", None)
    return row


def legacy_issue_record(current: dict[str, Any]) -> dict[str, Any]:
    row = copy.deepcopy(current)
    row["status"] = "open"
    row["summary"] = LEGACY_ISSUE_SUMMARY
    row["affected_count"] = 10
    row["evidence_artifacts"] = [
        {
            "locator": "data/audit/2026-08-24_origen_manifestation_conflicts_readonly_audit.md",
            "role": "audit_report",
        },
        {
            "locator": "data/audit/2026-08-16_de_princ_iii_1_acquisition.md",
            "role": "audit_report",
        },
        {
            "accessed_at": "2026-08-24T05:15:00Z",
            "locator": f"https://github.com/OpenGreekAndLatin/First1KGreek/blob/{OGL_COMMIT}/data/tlg2042/tlg019/__cts__.xml",
            "role": "authority_record",
        },
    ]
    row["resolution_criteria"] = LEGACY_RESOLUTION_CRITERIA
    row.pop("adjudication", None)
    return row


def legacy_wave_record(current: dict[str, Any]) -> dict[str, Any]:
    row = copy.deepcopy(current)
    row["evidence_ids"] = [
        value for value in row["evidence_ids"] if value != EVIDENCE_ID
    ]
    return row


def source_record(current: dict[str, Any]) -> dict[str, Any]:
    row = copy.deepcopy(current)
    row["acquisition"] = {
        "status": "public_canonical",
        "manifest_publication_dirs": [],
        "artifacts": [
            {"locator": "data/audit/2026-08-24_origen_manifestation_conflicts_readonly_audit.md", "role": "audit_report"},
            {"locator": "data/audit/2026-08-24_origen_exhortatio_identity_repair.json", "role": "audit_report", "sha256": REPAIR_REPORT_SHA256},
            {"locator": "data/audit/2026-08-24_origen_exhortatio_identity_quarantine.jsonl", "role": "audit_report", "sha256": QUARANTINE_SHA256},
            {"locator": "data/audit/2026-08-24_origen_exhortatio_node_aliases.json", "role": "catalog_record", "sha256": ALIASES_SHA256},
        ],
    }
    row["coverage"] = {
        "state": "partial",
        "kg_node_ids": ["work_origen_exhortation_martyrdom", *PASSAGE_NODE_IDS],
        "basis": (
            "All 51 Greek chapters are NFC-exact to the pinned OGL/Perseus edition; "
            "the manifest and work identities are corrected, 51 Clement-prefixed ids "
            "are atomically aliased, snapshots/parity/work-child/loaders pass. Coverage "
            "remains partial because claim-level scholarly extraction of the complete "
            "treatise is not exhausted."
        ),
        "last_audited": "2026-08-24",
    }
    row["provenance"] = [
        {"locator": "data/audit/2026-08-24_origen_manifestation_conflicts_readonly_audit.md", "role": "audit_report"},
        {"locator": "data/audit/2026-08-24_origen_exhortatio_identity_repair.json", "role": "audit_report", "sha256": REPAIR_REPORT_SHA256},
        {"locator": "data/audit/2026-08-24_origen_exhortatio_node_aliases.json", "role": "catalog_record", "sha256": ALIASES_SHA256},
        {"accessed_at": "2026-08-24T05:15:00Z", "locator": f"https://github.com/OpenGreekAndLatin/First1KGreek/blob/{OGL_COMMIT}/data/tlg2042/tlg007/__cts__.xml", "role": "catalog_record", "sha256": OGL_CTS_SHA256},
        {"accessed_at": "2026-08-24T05:15:00Z", "locator": f"https://github.com/OpenGreekAndLatin/First1KGreek/blob/{OGL_COMMIT}/data/tlg2042/tlg007/tlg2042.tlg007.perseus-grc1.xml", "role": "tei", "sha256": OGL_TEI_SHA256},
    ]
    row["notes"] = (
        "Historical state retained: before Wave 0.2 the registry correctly warned "
        "that the 51 exact Greek chapters still sat behind a Clement/Protrepticus "
        "manifest and misleading passage ids. That identity defect is resolved; the "
        "broader Origen manifestation issue remains open."
    )
    return row


def issue_record(current: dict[str, Any]) -> dict[str, Any]:
    row = copy.deepcopy(current)
    row["status"] = "open"
    row["affected_count"] = 10
    row["summary"] = (
        "Historical opening scope: ten Origen manifestation cohorts conflated work "
        "identity, witness, language or translation. Progress on 2026-08-24: the one "
        "Exhortatio ad martyrium cohort is resolved (51 exact Greek chapters, correct "
        "manifest/work identities and atomic aliases). The issue remains open for the "
        "nine De principiis, Philocalia and Commentary on Romans cohorts: indirect "
        "Philocalia-21 transmission, Rufinus/modern-translation separation, false "
        "tlg028/tlg012/pseudo-CTS paths and mismatched snapshots still require repair."
    )
    additions = [
        {"locator": "data/audit/2026-08-24_origen_exhortatio_identity_repair.json", "role": "audit_report", "sha256": REPAIR_REPORT_SHA256},
        {"locator": "data/audit/2026-08-24_origen_exhortatio_node_aliases.json", "role": "catalog_record", "sha256": ALIASES_SHA256},
        {"locator": "tests/test_origen_exhortatio_identity_repair.py", "role": "test_report"},
    ]
    existing = {(item["locator"], item["role"]) for item in row["evidence_artifacts"]}
    row["evidence_artifacts"].extend(item for item in additions if (item["locator"], item["role"]) not in existing)
    row["resolution_criteria"] = (
        "Progress checkpoint: Exhortatio Wave 0.2 is resolved and independently plus "
        "adversarially verified; preserve that history. Keep this issue open until the "
        "remaining Romans Latin -> Philocalia -> De principiis sequence separates every "
        "work/witness/language/translator manifestation, quarantines mixed notes, false "
        "snapshots and tlg028/tlg012/pseudo-CTS paths, ingests exact Rufinus Latin before "
        "linking SC268 French, replays semantic citations, preserves explicit unknowns, "
        "and passes role/language/snapshot/dedup/staged/bootstrap plus independent and "
        "adversarial review."
    )
    row.pop("adjudication", None)
    return row


def evidence_record() -> dict[str, Any]:
    return {
        "record_type": "evidence",
        "evidence_id": EVIDENCE_ID,
        "source_id": SOURCE_ID,
        "evidence_kind": "ancient_passage",
        "claim_text": (
            "Origen's Exhortatio ad martyrium 1-51 is represented by 51 Greek corpus "
            "passages that are NFC-exact to the pinned OGL/Perseus edition."
        ),
        "attestation": "direct",
        "claim_status": "verified",
        "locator": {
            "canonical_locus": "Exhortatio ad martyrium 1-51",
            "edition_or_witness": f"OGL {OGL_COMMIT}, urn:cts:greekLit:tlg2042.tlg007.perseus-grc1",
            "page_map_status": "not_applicable",
        },
        "quotation": {
            "status": "collated",
            "language": "grc",
            "text_sha256": NFC_TEXT_COHORT_SHA256,
            "corpus_passage_ids": CORPUS_PASSAGE_IDS,
        },
        "kg_targets": ["work_origen_exhortation_martyrdom", *PASSAGE_NODE_IDS],
        "required_verification": [
            "bibliographic_identity", "locus_or_page", "textual_exactness",
            "attribution", "independent_review", "adversarial_review",
        ],
        "notes": (
            f"Hash method: SHA-256 of NFC(text 1) + newline + ... + NFC(text 51). "
            f"Pinned OGL hashes: __cts__={OGL_CTS_SHA256}; TEI={OGL_TEI_SHA256}. "
            f"Repair report={REPAIR_REPORT_SHA256}; aliases={ALIASES_SHA256}."
        ),
    }


def verification_records() -> list[dict[str, Any]]:
    base = {
        "record_type": "verification", "target_type": "evidence",
        "target_id": EVIDENCE_ID, "verdict": "pass",
        "created_at": "2026-08-24T07:30:00Z",
    }
    return [
        {**base, "verification_id": "ver_origen_exhortatio_51_primary_20260824", "stage": "primary", "verifier": {"verifier_id": "origen_exhortatio_ogl_text_gate", "kind": "deterministic_tool", "independence_group": "pinned_ogl_cts_tei_nfc_collation_20260824"}, "method": "Verify SHA-256-pinned OGL CTS/TEI identity and require 51/51 local Greek chapter texts to be NFC-exact.", "checked_locators": [f"https://github.com/OpenGreekAndLatin/First1KGreek/blob/{OGL_COMMIT}/data/tlg2042/tlg007/__cts__.xml", f"https://github.com/OpenGreekAndLatin/First1KGreek/blob/{OGL_COMMIT}/data/tlg2042/tlg007/tlg2042.tlg007.perseus-grc1.xml", "data/audit/2026-08-24_origen_exhortatio_identity_repair.json"], "artifacts": [{"locator": "data/audit/2026-08-24_origen_exhortatio_identity_repair.json", "role": "test_report", "sha256": REPAIR_REPORT_SHA256}], "notes": "Pinned identity and all 51 texts passed."},
        {**base, "verification_id": "ver_origen_exhortatio_51_independent_root_20260824", "stage": "independent", "verifier": {"verifier_id": "root_exhortatio_wave02_review", "kind": "agent", "independence_group": "root_postwrite_ogl_cardinality_review_20260824"}, "method": "Independently run the pinned OGL dry-run before write, the 18-test post-write suite, and inspect zero legacy ids plus all alias/edge/citation/parity cardinalities.", "checked_locators": ["scripts/apply_2026_08_24_origen_exhortatio_identity_repair.py", "tests/test_origen_exhortatio_identity_repair.py", "data/audit/2026-08-24_origen_exhortatio_node_aliases.json"], "artifacts": [{"locator": "tests/test_origen_exhortatio_identity_repair.py", "role": "test_report"}], "notes": "Root independently confirmed 51/51 OGL, 18/18 tests, 0 old active ids and 258 targeted before-images."},
        {**base, "verification_id": "ver_origen_exhortatio_51_adversarial_20260824", "stage": "adversarial", "verifier": {"verifier_id": "origen_exhortatio_regression_suite", "kind": "deterministic_tool", "independence_group": "transaction_snapshot_parity_loader_registry_gates_20260824"}, "method": "Reject authority/hash drift, partial alias cutover, text/UUID/ref/CTS mutation, dangling endpoints, snapshot/parity/work-child/loader drift, artifact overwrite, failed rollback or non-idempotence.", "checked_locators": ["tests/test_origen_exhortatio_identity_repair.py", "scripts/check_corpus_invariants.py", "scripts/check_snapshot_passage_integrity.py", "scripts/check_kg_corpus_locus_parity.py", "database/tests/unit/test_bootstrap_supabase.py", "database/tests/unit/test_deploy_data_staged.py"], "artifacts": [{"locator": "tests/test_origen_exhortatio_identity_repair.py", "role": "test_report"}], "notes": "Deterministic adversarial suite and targeted gates passed; Docker-only integration was unavailable, not failed."},
    ]


def transform(files: dict[Path, list[dict[str, Any]]]) -> tuple[dict[Path, list[dict[str, Any]]], Counter[str], str]:
    files = copy.deepcopy(files)
    source = find_one(files[SOURCE_REL], "source_id", SOURCE_ID)
    issue = find_one(files[ISSUE_REL], "issue_id", ISSUE_ID)
    wave = find_one(files[WAVE_REL], "wave_id", WAVE_ID)
    evidence_rows = files[EVIDENCE_REL]
    verification_rows = files[VERIFICATION_REL]
    if not evidence_rows and not verification_rows:
        mode = "legacy"
    elif len(evidence_rows) == 1 and len(verification_rows) == 3:
        mode = "reconciled"
    else:
        raise RuntimeError("mixed/incomplete Origen registry reconciliation shards")

    if mode == "legacy" and (
        source != legacy_source_record(source)
        or issue != legacy_issue_record(issue)
        or wave != legacy_wave_record(wave)
    ):
        raise RuntimeError("legacy Origen registry target records drifted")

    desired_source = source_record(source)
    desired_issue = issue_record(issue)
    desired_evidence = evidence_record()
    desired_verifications = verification_records()
    desired_wave = copy.deepcopy(wave)
    if EVIDENCE_ID not in desired_wave["evidence_ids"]:
        desired_wave["evidence_ids"].append(EVIDENCE_ID)

    if mode == "reconciled":
        if source != desired_source or issue != desired_issue or wave != desired_wave or evidence_rows != [desired_evidence] or verification_rows != desired_verifications:
            raise RuntimeError("reconciled Origen registry records drifted")
        return files, Counter(), mode

    source.clear()
    source.update(desired_source)
    issue.clear()
    issue.update(desired_issue)
    wave.clear()
    wave.update(desired_wave)
    files[EVIDENCE_REL] = [desired_evidence]
    files[VERIFICATION_REL] = desired_verifications
    changed = Counter({"source": 1, "issue": 1, "wave": 1, "evidence": 1, "verification": 3})
    validate(files)
    return files, changed, mode


def validate(files: dict[Path, list[dict[str, Any]]]) -> None:
    source = find_one(files[SOURCE_REL], "source_id", SOURCE_ID)
    issue = find_one(files[ISSUE_REL], "issue_id", ISSUE_ID)
    wave = find_one(files[WAVE_REL], "wave_id", WAVE_ID)
    evidence = find_one(files[EVIDENCE_REL], "evidence_id", EVIDENCE_ID)
    reviews = files[VERIFICATION_REL]
    if source["identity_status"] != "authority_verified" or source["coverage"]["state"] != "partial" or len(source["coverage"]["kg_node_ids"]) != 52:
        raise RuntimeError("source identity/coverage reconciliation incomplete")
    if "manifest remains mislabeled" in source["coverage"]["basis"]:
        raise RuntimeError("stale Exhortatio source basis remains")
    if issue["status"] != "open" or issue.get("affected_count") != 10 or "nine" not in issue["summary"]:
        raise RuntimeError("broader Origen issue was closed or lost progress history")
    if evidence["claim_status"] != "verified" or len(evidence["quotation"]["corpus_passage_ids"]) != 51 or len(evidence["kg_targets"]) != 52:
        raise RuntimeError("Exhortatio atomic evidence incomplete")
    if evidence["quotation"]["text_sha256"] != NFC_TEXT_COHORT_SHA256:
        raise RuntimeError("Exhortatio evidence cohort hash drift")
    if {row["stage"] for row in reviews} != {"primary", "independent", "adversarial"} or len({row["verifier"]["independence_group"] for row in reviews}) != 3:
        raise RuntimeError("evidence verification independence incomplete")
    if EVIDENCE_ID not in wave["evidence_ids"]:
        raise RuntimeError("Wave 00 does not reference Exhortatio evidence")


def _write_fsync(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as handle:
        handle.write(content)
        handle.flush()
        os.fsync(handle.fileno())


def _fsync_dir(path: Path) -> None:
    fd = os.open(path, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def commit_registry(root: Path, before_hashes: dict[Path, str], payloads: dict[Path, bytes]) -> None:
    for path, expected in before_hashes.items():
        if not path.exists() or file_sha256(path) != expected:
            raise RuntimeError(f"registry pre-write drift: {path}")
    new_paths = [path for path in payloads if path not in before_hashes]
    existing_new = [str(path) for path in new_paths if path.exists()]
    if existing_new:
        raise RuntimeError(
            f"refusing to overwrite new registry shards: {existing_new}"
        )
    stage = Path(tempfile.mkdtemp(prefix=".origen-exhortatio-registry-", dir=root))
    entries = []
    committed = []
    try:
        for index, target in enumerate(payloads):
            staged = stage / f"new-{index}"
            _write_fsync(staged, payloads[target])
            backup = None
            if target.exists():
                backup = stage / f"backup-{index}"
                _write_fsync(backup, target.read_bytes())
            entries.append((target, staged, backup))
        _fsync_dir(stage)
        for path, expected in before_hashes.items():
            if file_sha256(path) != expected:
                raise RuntimeError(f"registry concurrent drift: {path}")
        if any(path.exists() for path in new_paths):
            raise RuntimeError("new registry shard appeared concurrently")
        try:
            for target, staged, backup in entries:
                os.replace(staged, target)
                committed.append((target, backup))
                _fsync_dir(target.parent)
        except Exception as error:
            rollback_errors = []
            for target, backup in reversed(committed):
                try:
                    if backup is None:
                        target.unlink(missing_ok=True)
                    else:
                        os.replace(backup, target)
                    _fsync_dir(target.parent)
                except Exception as rollback:
                    rollback_errors.append(str(rollback))
            if rollback_errors:
                raise RuntimeError(
                    f"registry rollback incomplete: {rollback_errors}"
                ) from error
            raise RuntimeError(
                f"registry commit failed; rollback succeeded: {error}"
            ) from error
    finally:
        shutil.rmtree(stage, ignore_errors=True)
        _fsync_dir(root)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--registry-root", type=Path, default=REGISTRY_ROOT)
    args = parser.parse_args(argv)
    root = args.registry_root.resolve()
    paths = [SOURCE_REL, ISSUE_REL, WAVE_REL, EVIDENCE_REL, VERIFICATION_REL]
    files = {rel: read_jsonl(root / rel) for rel in paths}
    reconciled, changed, mode = transform(files)
    if mode == "reconciled":
        validate(reconciled)
    summary = {"mode": "write" if args.write else "dry-run", "source_state": mode, "changed": dict(changed), "changed_total": sum(changed.values()), "issue_status": "open", "coverage_state": "partial", "evidence_id": EVIDENCE_ID, "write_performed": False}
    if not args.write or not changed:
        print(json.dumps(summary, indent=2, sort_keys=True))
        return 0
    for rel, expected in LEGACY_FILE_SHA256.items():
        actual = file_sha256(root / rel)
        if actual != expected:
            raise RuntimeError(
                f"legacy registry file hash drift: {rel}: {actual}"
            )
    before = {root / rel: LEGACY_FILE_SHA256[rel.as_posix()] for rel in (SOURCE_REL, ISSUE_REL, WAVE_REL)}
    payloads = {root / rel: encode_jsonl(reconciled[rel]) for rel in paths}
    commit_registry(root, before, payloads)
    summary["write_performed"] = True
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
