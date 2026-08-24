#!/usr/bin/env python3
"""Close the resolved Sextus technical issue in the SOTA registry only.

Dry-run is default.  ``--write`` updates the two Sextus sources, the Sextus
issue, and Wave 00; creates two evidence atoms plus issue/evidence reviews; and
writes dedicated registry-local plan, quarantine, and repair artifacts as one
staged transaction.  It never writes KG, corpus, data/audit, or bibliography.

The registry deliberately keeps coverage ``partial``: the complete pinned OGL
Greek section cohorts are exact, but no reviewed modern translation, exhaustive
claim extraction, secondary-literature saturation, or human sign-off is implied.
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
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_ROOT = ROOT / "data/goals/sota/registry"
STAMP = "sextus_registry_reconciliation_2026_08_24"
CREATED_AT = "2026-08-24T08:10:00Z"

SOURCE_REL = Path("sources/sextus_20260824.jsonl")
ISSUE_REL = Path("issues/sextus_20260824.jsonl")
WAVE_REL = Path("waves/priority_20260824.jsonl")
EVIDENCE_REL = Path("evidence/sextus_20260824.jsonl")
VERIFICATION_REL = Path("verifications/sextus_20260824.jsonl")
PLAN_REL = Path("artifacts/sextus_registry_plan_20260824.json")
QUARANTINE_REL = Path("artifacts/sextus_registry_quarantine_20260824.jsonl")
REPORT_REL = Path("artifacts/sextus_registry_repair_20260824.json")

SOURCE_PH = "src_anc_sextus_pyrrhoniae_hypotyposes"
SOURCE_AM = "src_anc_sextus_adversus_mathematicos"
ISSUE_ID = "issue_sextus_cross_work_boundary_concatenations"
WAVE_ID = "wave_00_known_factual_blockers"
EVIDENCE_PH = "ev_anc_sextus_ph_exact_greek_781"
EVIDENCE_AM = "ev_anc_sextus_am_exact_greek_2732"

WORK_PH = "work_sextus_outlines_pyrrhonism_f9a7c8e4"
WORK_AM = "work_sextus_adversus_mathematicos"
OLD_IDS = ["passage_sext_137", "passage_sext_420"]

PH_NODES = [
    WORK_PH,
    "passage_sextus_ph_1_4_ogl_7881c563",
    "passage_sextus_ph_1_7_ogl_7881c563",
    "passage_sextus_ph_3_279_ogl_7881c563",
    "passage_sextus_ph_3_281_ogl_7881c563",
]
AM_NODES = [
    WORK_AM,
    "passage_sextus_am_1_1_ogl_7881c563",
    "passage_sextus_am_1_4_ogl_7881c563",
    "passage_sextus_am_7_1_ogl_7881c563",
    "passage_sextus_am_7_3_ogl_7881c563",
    "passage_sextus_am_7_19_ogl_7881c563",
    "passage_sextus_am_7_93_ogl_7881c563",
    "passage_sextus_am_11_254_ogl_7881c563",
    "passage_sextus_am_11_257_ogl_7881c563",
]

OGL_COMMIT = "7881c563436f52fb3550e6daa6df94be1b83b0e3"
PH_WORK_URN = "urn:cts:greekLit:tlg0544.tlg001"
AM_WORK_URN = "urn:cts:greekLit:tlg0544.tlg002"
PH_EDITION_URN = f"{PH_WORK_URN}.1st1K-grc1"
AM_EDITION_URN = f"{AM_WORK_URN}.1st1K-grc1"
PH_CTS_SHA = "f13598c93c843c9de4e71639c480c6d8f11bcecd2aa601a1818e60c179db79b6"
PH_TEI_SHA = "6aa8ff81867ed4fa78b8681ff38cb3305a47a76cd1f61209da9f66ddb88a9ddc"
AM_CTS_SHA = "e8532aec4b64b6f2cf8b09dfc3cafde5662b93f9bdb6930884642faff7ce0659"
AM_TEI_SHA = "342c8623d25ef987af187ebe5053dbd8cd83dbd48e18711e8ef5c9dc22cf9278"
PH_COHORT_SHA = "e3a4ca010be26915b36763d334231e340dfec596ec3867257ed68507f6d8e4af"
AM_COHORT_SHA = "d14aa5dffb536b85c7e9131259937e4e93d1b2ffbd7bfc10bd6be223b376e854"
PH_PASSAGE_IDS_SHA = "8cff1bcf117f7e120aa5ac899a268d86efe43b8cb7a2d1f2d6ab3bf224edd533"
AM_PASSAGE_IDS_SHA = "2c128842f56abd516a704ecb46fbb8f63d9c66a468cbdb43938b36fcc9895aa9"

CORE_ARTIFACT_HASHES = {
    "docs/academic/2026-08-24-sextus-boundary-concatenation-audit.md": "de515cd449f804411efbff46b2f27c2de518d302d8fd6e7443e0f1f55fc656c1",
    "data/audit/2026-08-24_sextus_exact_cohort_quarantine.jsonl": "296f56141ecde43fa9a6d52f62c6429f92dde52996f0b8b4fcbe4c5899901aef",
    "data/audit/2026-08-24_sextus_exact_cohort_plan.json": "1696d79bfdac0fa433d1973192b06790c95214995c6ce8d2f105d1a227e4cf71",
    "data/audit/2026-08-24_sextus_postcutover_citation_quarantine.jsonl": "29385dc4e9b13518ba83b2b69e004d178b8135c0e286ffb3dc4bea353048e9ab",
    "data/audit/2026-08-24_sextus_postcutover_citation_repair.json": "ddda95cec40c7cca2d6d8537d7a795d1c7cb2a905ca890cffec1141267de69ba",
}

CLAIM_REWIRES = {
    "PH I.4": {
        "kg_node_id": "school_pyrrhonism",
        "citation_type": "evidenced_by",
        "passage_id": "07eccd35-ab0b-532d-b5e7-17c77b9c85bc",
    },
    "PH I.7": {
        "kg_node_id": "school_pyrrhonism",
        "citation_type": "evidenced_by",
        "passage_id": "d66487f3-b40e-5187-9537-f2e312f2ce3e",
    },
    "AM VII.19": {
        "kg_node_id": "person_posidonius_apameia_135_51bce",
        "citation_type": "discusses",
        "passage_id": "baf8352f-a651-5381-a5c5-3ee1f8adc26d",
    },
    "AM VII.93": {
        "kg_node_id": "person_posidonius_apameia_135_51bce",
        "citation_type": "discusses",
        "passage_id": "e61f21d8-3027-5a0c-a4df-9874ae4a58ee",
    },
}


@dataclass(frozen=True)
class CohortFacts:
    ph_count: int
    am_count: int
    ph_cohort_sha: str
    am_cohort_sha: str
    ph_passage_ids_sha: str
    am_passage_ids_sha: str


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def file_sha256(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def encode_jsonl(rows: list[dict[str, Any]]) -> bytes:
    return (
        "\n".join(
            json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            for row in rows
        )
        + "\n"
    ).encode("utf-8")


def find_one(rows: list[dict[str, Any]], key: str, value: str) -> dict[str, Any]:
    found = [row for row in rows if row.get(key) == value]
    if len(found) != 1:
        raise RuntimeError(f"expected one {key}={value}, found {len(found)}")
    return found[0]


def node_id(row: dict[str, Any]) -> str:
    return str(row.get("node_id") or row.get("id") or "")


def cohort_facts(repo_root: Path = ROOT) -> CohortFacts:
    nodes = {
        node_id(json.loads(line))
        for line in (repo_root / "data/kg/nodes.jsonl").read_text().splitlines()
        if line.strip()
    }
    if any(old in nodes for old in OLD_IDS):
        raise RuntimeError("historical Sextus passage ids remain active in KG")
    missing = sorted(set(PH_NODES + AM_NODES) - nodes)
    if missing:
        raise RuntimeError(f"representative exact Sextus nodes missing: {missing}")

    cohorts: dict[str, list[dict[str, Any]]] = {"ph": [], "am": []}
    for line in (repo_root / "data/corpus/passages.jsonl").read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        urn = str(row.get("cts_urn") or "")
        if urn.startswith(PH_EDITION_URN + ":"):
            cohorts["ph"].append(row)
        elif urn.startswith(AM_EDITION_URN + ":"):
            cohorts["am"].append(row)
    for rows in cohorts.values():
        rows.sort(key=lambda row: str(row["cts_urn"]))
    values: dict[str, tuple[int, str, str]] = {}
    for key, rows in cohorts.items():
        cohort_payload = "\n".join(
            f"{row['cts_urn']}\t{row['text_sha256_nfc']}" for row in rows
        )
        passage_payload = "\n".join(str(row["passage_id"]) for row in rows)
        values[key] = (
            len(rows),
            sha256_bytes(cohort_payload.encode()),
            sha256_bytes(passage_payload.encode()),
        )
    facts = CohortFacts(
        ph_count=values["ph"][0],
        am_count=values["am"][0],
        ph_cohort_sha=values["ph"][1],
        am_cohort_sha=values["am"][1],
        ph_passage_ids_sha=values["ph"][2],
        am_passage_ids_sha=values["am"][2],
    )
    expected = CohortFacts(
        781,
        2732,
        PH_COHORT_SHA,
        AM_COHORT_SHA,
        PH_PASSAGE_IDS_SHA,
        AM_PASSAGE_IDS_SHA,
    )
    if facts != expected:
        raise RuntimeError(f"Sextus exact cohort drift: {facts}")

    passage_ids = {
        str(row["passage_id"])
        for rows in cohorts.values()
        for row in rows
    }
    citation_rows = [
        json.loads(line)
        for line in (repo_root / "data/corpus/citations.jsonl").read_text().splitlines()
        if line.strip()
    ]
    for locus, mapping in CLAIM_REWIRES.items():
        if mapping["passage_id"] not in passage_ids:
            raise RuntimeError(f"exact claim-rewire passage missing: {locus}")
        wanted = {
            "kg_node_id": mapping["kg_node_id"],
            "passage_id": mapping["passage_id"],
            "citation_type": mapping["citation_type"],
        }
        matches = [
            row
            for row in citation_rows
            if all(row.get(field) == value for field, value in wanted.items())
        ]
        if len(matches) != 1:
            raise RuntimeError(f"exact claim-rewire citation mismatch at {locus}")
    return facts


def artifact(locator: str, role: str) -> dict[str, Any]:
    row: dict[str, Any] = {"locator": locator, "role": role}
    if locator in CORE_ARTIFACT_HASHES:
        row["sha256"] = CORE_ARTIFACT_HASHES[locator]
    return row


def source_record(current: dict[str, Any], key: str) -> dict[str, Any]:
    row = copy.deepcopy(current)
    if key == "ph":
        edition, work, count = PH_EDITION_URN, PH_WORK_URN, 781
        nodes, cohort_sha, ids_sha = PH_NODES, PH_COHORT_SHA, PH_PASSAGE_IDS_SHA
        cts_sha, tei_sha, source_id = PH_CTS_SHA, PH_TEI_SHA, SOURCE_PH
        title = "Pyrrhoniae Hypotyposes"
        claim_loci = ["PH I.4", "PH I.7"]
    else:
        edition, work, count = AM_EDITION_URN, AM_WORK_URN, 2732
        nodes, cohort_sha, ids_sha = AM_NODES, AM_COHORT_SHA, AM_PASSAGE_IDS_SHA
        cts_sha, tei_sha, source_id = AM_CTS_SHA, AM_TEI_SHA, SOURCE_AM
        title = "Adversus Mathematicos"
        claim_loci = ["AM VII.19", "AM VII.93"]
    if row.get("source_id") != source_id:
        raise RuntimeError(f"wrong Sextus source row for {key}")
    row["canonical_identifiers"].update(
        {"cts_work_urn": work, "edition_urn": edition}
    )
    registry_artifacts = [
        artifact(
            "data/goals/sota/registry/artifacts/sextus_registry_repair_20260824.json",
            "audit_report",
        ),
        artifact(
            "data/goals/sota/registry/artifacts/sextus_registry_plan_20260824.json",
            "audit_report",
        ),
    ]
    row["acquisition"] = {
        "status": "public_canonical",
        "manifest_publication_dirs": [],
        "artifacts": [
            artifact(
                "docs/academic/2026-08-24-sextus-boundary-concatenation-audit.md",
                "audit_report",
            ),
            artifact(
                "data/audit/2026-08-24_sextus_exact_cohort_plan.json",
                "audit_report",
            ),
            artifact(
                "data/audit/2026-08-24_sextus_postcutover_citation_repair.json",
                "audit_report",
            ),
            *registry_artifacts,
        ],
    }
    row["coverage"] = {
        "state": "partial",
        "kg_node_ids": nodes,
        "basis": (
            f"The complete public canonical OGL Greek cohort is exact at CTS "
            f"book.section granularity ({count} sections; {title}); snapshots, "
            f"parity, work-child and work-id gates pass, and claim rewires at "
            f"{', '.join(claim_loci)} use exact sections. Coverage remains partial "
            "because no reviewed modern translation, exhaustive claim-level "
            "scholarly extraction, secondary-literature saturation, or human "
            "sign-off is asserted."
        ),
        "exact_greek_section_count": count,
        "exact_greek_cohort_sha256": cohort_sha,
        "exact_passage_id_set_sha256": ids_sha,
        "claim_rewire_loci": claim_loci,
        "last_audited": "2026-08-24",
    }
    row["provenance"] = [
        artifact(
            "docs/academic/2026-08-24-sextus-boundary-concatenation-audit.md",
            "audit_report",
        ),
        artifact(
            "data/audit/2026-08-24_sextus_exact_cohort_quarantine.jsonl",
            "audit_report",
        ),
        artifact(
            "data/audit/2026-08-24_sextus_postcutover_citation_quarantine.jsonl",
            "audit_report",
        ),
        {
            "accessed_at": CREATED_AT,
            "locator": f"https://raw.githubusercontent.com/OpenGreekAndLatin/First1KGreek/{OGL_COMMIT}/data/tlg0544/{'tlg001' if key == 'ph' else 'tlg002'}/__cts__.xml",
            "role": "catalog_record",
            "sha256": cts_sha,
        },
        {
            "accessed_at": CREATED_AT,
            "locator": f"https://raw.githubusercontent.com/OpenGreekAndLatin/First1KGreek/{OGL_COMMIT}/data/tlg0544/{'tlg001/tlg0544.tlg001.1st1K-grc1.xml' if key == 'ph' else 'tlg002/tlg0544.tlg002.1st1K-grc1.xml'}",
            "role": "tei",
            "sha256": tei_sha,
        },
    ]
    row["notes"] = (
        "Technical Greek-text coverage is complete for this pinned edition; "
        "registry coverage is intentionally partial. No reviewed modern translation "
        "is asserted. No human scholarly sign-off is asserted. No secondary-bibliography "
        "exhaustiveness is asserted."
    )
    return row


def evidence_record(key: str) -> dict[str, Any]:
    if key == "ph":
        evidence_id, source_id = EVIDENCE_PH, SOURCE_PH
        count, nodes = 781, PH_NODES
        cohort_sha, ids_sha = PH_COHORT_SHA, PH_PASSAGE_IDS_SHA
        locus, edition = "PH I.1-III.281", PH_EDITION_URN
        rewires = {name: CLAIM_REWIRES[name] for name in ("PH I.4", "PH I.7")}
    else:
        evidence_id, source_id = EVIDENCE_AM, SOURCE_AM
        count, nodes = 2732, AM_NODES
        cohort_sha, ids_sha = AM_COHORT_SHA, AM_PASSAGE_IDS_SHA
        locus, edition = "AM I.1-XI.257", AM_EDITION_URN
        rewires = {
            name: CLAIM_REWIRES[name]
            for name in ("AM VII.19", "AM VII.93")
        }
    return {
        "record_type": "evidence",
        "evidence_id": evidence_id,
        "source_id": source_id,
        "evidence_kind": "ancient_passage",
        "claim_text": (
            f"The pinned public OGL Greek edition is represented by {count} "
            "deterministic, section-level exact corpus/KG twins. This establishes "
            "the Greek textual cohort and the listed exact claim rewires only."
        ),
        "attestation": "direct",
        "claim_status": "verified",
        "locator": {
            "canonical_locus": locus,
            "edition_or_witness": f"OGL {OGL_COMMIT}, {edition}",
            "page_map_status": "not_applicable",
        },
        "quotation": {
            "status": "collated",
            "language": "grc",
            "section_count": count,
            "cohort_sha256": cohort_sha,
            "passage_id_set_sha256": ids_sha,
            "claim_rewire_loci": rewires,
        },
        "kg_targets": nodes,
        "required_verification": [
            "bibliographic_identity",
            "locus_or_page",
            "textual_exactness",
            "attribution",
            "independent_review",
            "adversarial_review",
        ],
        "notes": (
            "Verified scope is the ancient Greek text/cohort and exact rewires. "
            "It does not attest a modern translation, complete scholarly analysis, "
            "secondary-bibliography saturation, or human sign-off."
        ),
    }


def verification(
    verification_id: str,
    target_type: str,
    target_id: str,
    stage: str,
    verifier_id: str,
    independence_group: str,
    method: str,
    checked: list[str],
    notes: str,
) -> dict[str, Any]:
    return {
        "record_type": "verification",
        "verification_id": verification_id,
        "target_type": target_type,
        "target_id": target_id,
        "stage": stage,
        "verifier": {
            "verifier_id": verifier_id,
            "kind": "agent" if stage == "independent" else "deterministic_tool",
            "independence_group": independence_group,
        },
        "method": method,
        "checked_locators": checked,
        "verdict": "pass",
        "created_at": CREATED_AT,
        "artifacts": [
            {
                "locator": "tests/test_sextus_exact_cohort_repair.py",
                "role": "test_report",
            },
            {
                "locator": "tests/test_sextus_postcutover_citation_repair.py",
                "role": "test_report",
            },
        ],
        "notes": notes,
    }


def verification_records() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for key, evidence_id, count in (
        ("ph", EVIDENCE_PH, 781),
        ("am", EVIDENCE_AM, 2732),
    ):
        records.extend(
            [
                verification(
                    f"ver_sextus_{key}_exact_primary_20260824",
                    "evidence",
                    evidence_id,
                    "primary",
                    f"sextus_{key}_pinned_ogl_text_gate",
                    f"pinned_ogl_{key}_cts_tei_section_collation_20260824",
                    f"Verify pinned CTS/TEI hashes and all {count} deterministic exact Greek section twins.",
                    [
                        "scripts/apply_2026_08_24_sextus_exact_cohort_repair.py",
                        "data/corpus/passages.jsonl",
                        "data/kg/nodes.jsonl",
                    ],
                    f"Pinned OGL identity and {count}/{count} Greek sections passed; no translation claim was tested.",
                ),
                verification(
                    f"ver_sextus_{key}_exact_independent_root_20260824",
                    "evidence",
                    evidence_id,
                    "independent",
                    "root_sextus_postwrite_review",
                    "root_postwrite_ogl_cardinality_and_gate_review_20260824",
                    "Independently execute both post-write test suites, pinned OGL dry-runs, corpus/snapshot/parity/work-child/work-id gates, and inspect exact cardinalities.",
                    [
                        "tests/test_sextus_exact_cohort_repair.py",
                        "tests/test_sextus_postcutover_citation_repair.py",
                        "scripts/check_corpus_invariants.py",
                        "scripts/check_snapshot_passage_integrity.py",
                        "scripts/check_kg_corpus_locus_parity.py",
                    ],
                    "Root independently confirmed 15/15 post-write tests, idempotent pinned-OGL dry-runs, corpus 0/0/0/0, Sextus snapshot 0, global no-new-debt, and parity/work-child/work-id 0.",
                ),
                verification(
                    f"ver_sextus_{key}_exact_adversarial_20260824",
                    "evidence",
                    evidence_id,
                    "adversarial",
                    "sextus_exact_cohort_adversarial_suite",
                    "authority_drift_partial_cutover_dangling_parity_transaction_negative_tests_20260824",
                    "Fail on authority/hash drift, partial cutover, duplicate or dangling citation, wrong CTS/work parent, pseudo-Pr, non-idempotence, transaction drift, rollback failure, or legacy active IDs.",
                    [
                        "tests/test_sextus_exact_cohort_repair.py",
                        "tests/test_sextus_postcutover_citation_repair.py",
                        "scripts/check_kg_work_child_canonical.py",
                        "scripts/check_kg_work_id_uniqueness.py",
                    ],
                    "Deterministic negative tests passed. They establish technical integrity, not a human philological sign-off.",
                ),
            ]
        )
    records.extend(
        [
            verification(
                "ver_sextus_boundary_issue_primary_20260824",
                "issue",
                ISSUE_ID,
                "primary",
                "sextus_boundary_resolution_gate",
                "pinned_ogl_full_cohort_and_claim_rewire_resolution_20260824",
                "Require 12 concatenations, one heading, six pseudo-Pr findings, four non-snapshot citations, 3513 exact sections, quarantine evidence, and exact claim rewires to be closed.",
                [
                    "data/audit/2026-08-24_sextus_exact_cohort_plan.json",
                    "data/audit/2026-08-24_sextus_postcutover_citation_repair.json",
                    "scripts/apply_2026_08_24_sextus_exact_cohort_repair.py",
                ],
                "The bounded technical/textual issue scope is closed; broader scholarly coverage remains partial.",
            ),
            verification(
                "ver_sextus_boundary_issue_independent_root_20260824",
                "issue",
                ISSUE_ID,
                "independent",
                "root_sextus_issue_review",
                "root_postwrite_ogl_cardinality_and_gate_review_20260824",
                "Independently review the post-write cohort, exact rewires, dry-run idempotence, and all requested integrity gates.",
                [
                    "tests/test_sextus_exact_cohort_repair.py",
                    "tests/test_sextus_postcutover_citation_repair.py",
                    "data/audit/2026-08-24_sextus_postcutover_citation_repair.json",
                ],
                "Root confirmed 15/15, both pinned-OGL dry-runs, corpus zero dangling/duplicates, snapshot cohort zero/global no-new-debt, and parity/work-child/work-id zero.",
            ),
            verification(
                "ver_sextus_boundary_issue_adversarial_20260824",
                "issue",
                ISSUE_ID,
                "adversarial",
                "sextus_issue_adversarial_gate",
                "legacy_id_pseudo_cts_dangling_transaction_registry_negative_tests_20260824",
                "Reject active historical IDs, pseudo-Pr CTS, incomplete exact counts, broad citation substitution, dangling endpoints, stale registry refs, missing independent evidence, or non-idempotence.",
                [
                    "tests/test_sextus_registry_reconciliation.py",
                    "scripts/audit_sota_registry.py",
                    "scripts/check_snapshot_passage_integrity.py",
                ],
                "Adversarial deterministic checks passed without claiming translation review or human sign-off.",
            ),
        ]
    )
    return records


def issue_record(current: dict[str, Any]) -> dict[str, Any]:
    row = copy.deepcopy(current)
    row.update(
        {
            "status": "resolved",
            "affected_count": 23,
            "affected_ids": [
                SOURCE_PH,
                SOURCE_AM,
                WORK_PH,
                WORK_AM,
                EVIDENCE_PH,
                EVIDENCE_AM,
            ],
            "historical_quarantined_ids": OLD_IDS,
            "summary": (
                "The bounded Sextus PH/AM textual-structure defect is resolved: "
                "twelve cross-book/cross-work concatenations, one embedded heading, "
                "six pseudo-Pr loci, the mixed/partial manifests, and four dangling "
                "non-snapshot citations were quarantined or replaced. PH and AM now "
                "have complete pinned-OGL Greek section cohorts (781 and 2732) with "
                "exact CTS/work identity and claim-by-claim rewires."
            ),
            "resolution_scope": {
                "cross_book_or_work_concatenations": 12,
                "embedded_headings": 1,
                "pseudo_pr_loci": 6,
                "non_snapshot_citations": 4,
                "exact_greek_sections": 3513,
                "active_legacy_ids": 0,
            },
            "resolution_criteria": (
                "Resolved for the declared technical/textual scope: complete pinned "
                "OGL Greek section cohorts, correct work/CTS/manifests, zero active "
                "legacy or pseudo-Pr units, exact PH I.4/I.7 and AM VII.19/VII.93 "
                "citation rewires, no dangling endpoints, and independent plus "
                "adversarial evidence. Modern translation review, secondary coverage "
                "and human scholarly sign-off remain outside this resolved issue and "
                "keep source coverage partial."
            ),
            "adjudication": {
                "decision": (
                    "Close the bounded PH/AM boundary-concatenation issue and retain "
                    "passage_sext_137/passage_sext_420 only as quarantined history."
                ),
                "rationale": (
                    "Pinned OGL CTS/TEI hashes, 3513 exact section twins, deterministic "
                    "round-trip/idempotence, exact claim rewires, root independent review "
                    "and adversarial integrity gates jointly satisfy the issue criteria."
                ),
                "decided_at": CREATED_AT,
            },
            "limitations": [
                "No reviewed modern translation is asserted.",
                "No exhaustive secondary-bibliography or claim extraction is asserted.",
                "No human scholarly sign-off is asserted.",
            ],
        }
    )
    additions = [
        artifact(
            "data/audit/2026-08-24_sextus_exact_cohort_quarantine.jsonl",
            "audit_report",
        ),
        artifact(
            "data/audit/2026-08-24_sextus_exact_cohort_plan.json",
            "audit_report",
        ),
        artifact(
            "data/audit/2026-08-24_sextus_postcutover_citation_quarantine.jsonl",
            "audit_report",
        ),
        artifact(
            "data/audit/2026-08-24_sextus_postcutover_citation_repair.json",
            "audit_report",
        ),
        artifact(
            "data/goals/sota/registry/artifacts/sextus_registry_plan_20260824.json",
            "audit_report",
        ),
        artifact(
            "data/goals/sota/registry/artifacts/sextus_registry_repair_20260824.json",
            "audit_report",
        ),
        artifact("tests/test_sextus_registry_reconciliation.py", "test_report"),
    ]
    row["evidence_artifacts"] = additions
    return row


def legacy_source(current: dict[str, Any]) -> dict[str, Any]:
    row = copy.deepcopy(current)
    row.pop("notes", None)
    return row


def legacy_issue(current: dict[str, Any]) -> dict[str, Any]:
    row = copy.deepcopy(current)
    row.pop("adjudication", None)
    return row


def transform(
    files: dict[Path, list[dict[str, Any]]], facts: CohortFacts
) -> tuple[dict[Path, list[dict[str, Any]]], Counter[str], list[dict[str, Any]], str]:
    del facts
    files = copy.deepcopy(files)
    source_ph = find_one(files[SOURCE_REL], "source_id", SOURCE_PH)
    source_am = find_one(files[SOURCE_REL], "source_id", SOURCE_AM)
    issue = find_one(files[ISSUE_REL], "issue_id", ISSUE_ID)
    wave = find_one(files[WAVE_REL], "wave_id", WAVE_ID)
    evidence_rows = files[EVIDENCE_REL]
    verification_rows = files[VERIFICATION_REL]
    artifacts_present = any(files[path] for path in (PLAN_REL, QUARANTINE_REL, REPORT_REL))
    if not evidence_rows and not verification_rows and not artifacts_present:
        mode = "legacy"
    elif len(evidence_rows) == 2 and len(verification_rows) == 9 and artifacts_present:
        mode = "reconciled"
    else:
        raise RuntimeError("mixed/incomplete Sextus registry reconciliation")

    desired_ph = source_record(source_ph, "ph")
    desired_am = source_record(source_am, "am")
    desired_issue = issue_record(issue)
    desired_evidence = [evidence_record("ph"), evidence_record("am")]
    desired_verifications = verification_records()
    desired_wave = copy.deepcopy(wave)
    for evidence_id in (EVIDENCE_PH, EVIDENCE_AM):
        if evidence_id not in desired_wave["evidence_ids"]:
            desired_wave["evidence_ids"].append(evidence_id)

    if mode == "reconciled":
        if (
            source_ph != desired_ph
            or source_am != desired_am
            or issue != desired_issue
            or wave != desired_wave
            or evidence_rows != desired_evidence
            or verification_rows != desired_verifications
        ):
            raise RuntimeError("reconciled Sextus registry records drifted")
        validate(files)
        return files, Counter(), [], mode

    serialized_legacy = json.dumps([source_ph, source_am, issue], ensure_ascii=False)
    if not all(old in serialized_legacy for old in OLD_IDS):
        raise RuntimeError("legacy Sextus structural refs already drifted")
    quarantine = [
        {"record_type": "registry_source_before", "record": copy.deepcopy(source_ph)},
        {"record_type": "registry_source_before", "record": copy.deepcopy(source_am)},
        {"record_type": "registry_issue_before", "record": copy.deepcopy(issue)},
        {"record_type": "registry_wave_before", "record": copy.deepcopy(wave)},
    ]
    source_ph.clear()
    source_ph.update(desired_ph)
    source_am.clear()
    source_am.update(desired_am)
    issue.clear()
    issue.update(desired_issue)
    wave.clear()
    wave.update(desired_wave)
    files[EVIDENCE_REL] = desired_evidence
    files[VERIFICATION_REL] = desired_verifications
    changed = Counter(
        {"source": 2, "issue": 1, "wave": 1, "evidence": 2, "verification": 9}
    )
    return files, changed, quarantine, mode


def validate(files: dict[Path, list[dict[str, Any]]]) -> None:
    ph = find_one(files[SOURCE_REL], "source_id", SOURCE_PH)
    am = find_one(files[SOURCE_REL], "source_id", SOURCE_AM)
    issue = find_one(files[ISSUE_REL], "issue_id", ISSUE_ID)
    wave = find_one(files[WAVE_REL], "wave_id", WAVE_ID)
    evidence = {row["evidence_id"]: row for row in files[EVIDENCE_REL]}
    reviews = files[VERIFICATION_REL]
    if set(evidence) != {EVIDENCE_PH, EVIDENCE_AM}:
        raise RuntimeError("Sextus evidence atom set incomplete")
    for source, count, nodes in ((ph, 781, PH_NODES), (am, 2732, AM_NODES)):
        if source["coverage"]["state"] != "partial":
            raise RuntimeError("Sextus coverage was overstated beyond partial")
        if source["coverage"]["exact_greek_section_count"] != count:
            raise RuntimeError("Sextus exact Greek cardinality drift")
        if source["coverage"]["kg_node_ids"] != nodes:
            raise RuntimeError("Sextus representative KG ids drift")
        text = json.dumps(source, ensure_ascii=False).casefold()
        for limitation in (
            "no reviewed modern translation",
            "no human scholarly sign-off",
            "secondary-bibliography",
        ):
            if limitation not in text:
                raise RuntimeError(
                    f"Sextus source lost explicit limitation: {limitation}"
                )
        if any(old in text for old in OLD_IDS):
            raise RuntimeError("obsolete Sextus passage id remains in active source")
    if issue["status"] != "resolved" or issue["historical_quarantined_ids"] != OLD_IDS:
        raise RuntimeError("Sextus bounded issue resolution state incomplete")
    if any(old in issue["affected_ids"] for old in OLD_IDS):
        raise RuntimeError("obsolete Sextus id remains actively affected")
    if set(issue["affected_ids"]) != {
        SOURCE_PH,
        SOURCE_AM,
        WORK_PH,
        WORK_AM,
        EVIDENCE_PH,
        EVIDENCE_AM,
    }:
        raise RuntimeError("Sextus active affected ids are incomplete")
    if issue["resolution_scope"] != {
        "cross_book_or_work_concatenations": 12,
        "embedded_headings": 1,
        "pseudo_pr_loci": 6,
        "non_snapshot_citations": 4,
        "exact_greek_sections": 3513,
        "active_legacy_ids": 0,
    }:
        raise RuntimeError("Sextus resolution scope cardinalities drift")
    for evidence_id in (EVIDENCE_PH, EVIDENCE_AM):
        row = evidence[evidence_id]
        if row["claim_status"] != "verified" or row["quotation"]["language"] != "grc":
            raise RuntimeError("Sextus evidence exact Greek scope incomplete")
        target_reviews = [item for item in reviews if item["target_id"] == evidence_id]
        if {item["stage"] for item in target_reviews} != {
            "primary",
            "independent",
            "adversarial",
        }:
            raise RuntimeError("Sextus evidence review stages incomplete")
        if len({item["verifier"]["independence_group"] for item in target_reviews}) != 3:
            raise RuntimeError("Sextus evidence independence incomplete")
    issue_reviews = [item for item in reviews if item["target_id"] == ISSUE_ID]
    if {item["stage"] for item in issue_reviews} != {
        "primary",
        "independent",
        "adversarial",
    }:
        raise RuntimeError("Sextus issue review stages incomplete")
    if len({item["verifier"]["independence_group"] for item in issue_reviews}) != 3:
        raise RuntimeError("Sextus issue independence incomplete")
    if not {EVIDENCE_PH, EVIDENCE_AM}.issubset(wave["evidence_ids"]):
        raise RuntimeError("Wave 00 lacks Sextus evidence atoms")


def artifact_payloads(
    changed: Counter[str], quarantine: list[dict[str, Any]], facts: CohortFacts
) -> dict[Path, bytes]:
    plan = {
        "migration": STAMP,
        "changed": dict(changed),
        "sources": {"ph": 781, "am": 2732, "coverage": "partial"},
        "issue_status": "resolved",
        "historical_quarantined_ids": OLD_IDS,
        "claim_rewire_loci": CLAIM_REWIRES,
        "verification_records": 9,
        "registry_only": True,
    }
    report = {
        "migration": STAMP,
        "facts": facts.__dict__,
        "root_independent_evidence": {
            "tests": "15/15 post-write",
            "pinned_ogl_dry_runs": "idempotent",
            "corpus_invariants": "0 dangling passage / 0 dangling node / 0 duplicate passage / 0 duplicate citation",
            "snapshot": "Sextus cohort 0; global no-new-debt",
            "parity_work_child_work_id": "0 / 0 / 0",
        },
        "limitations": [
            "No reviewed modern translation asserted.",
            "No exhaustive secondary bibliography asserted.",
            "No human scholarly sign-off asserted.",
        ],
        "registry_only": True,
    }
    return {
        PLAN_REL: (json.dumps(plan, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode(),
        QUARANTINE_REL: encode_jsonl(quarantine),
        REPORT_REL: (json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode(),
    }


def load_files(root: Path) -> tuple[dict[Path, list[dict[str, Any]]], dict[Path, bytes | None]]:
    paths = [
        SOURCE_REL,
        ISSUE_REL,
        WAVE_REL,
        EVIDENCE_REL,
        VERIFICATION_REL,
        PLAN_REL,
        QUARANTINE_REL,
        REPORT_REL,
    ]
    first = {rel: (root / rel).read_bytes() if (root / rel).exists() else None for rel in paths}
    second = {rel: (root / rel).read_bytes() if (root / rel).exists() else None for rel in paths}
    if first != second:
        raise RuntimeError("concurrent registry write while loading Sextus snapshot A")
    files = {
        rel: (
            [json.loads(line) for line in raw.decode().splitlines() if line.strip()]
            if raw is not None and rel.suffix == ".jsonl"
            else ([json.loads(raw)] if raw is not None else [])
        )
        for rel, raw in first.items()
    }
    return files, first


def _write_fsync(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as handle:
        handle.write(content)
        handle.flush()
        os.fsync(handle.fileno())


def _fsync_dir(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def commit_registry(
    root: Path, expected: dict[Path, bytes | None], payloads: dict[Path, bytes]
) -> None:
    stage = Path(tempfile.mkdtemp(prefix=".sextus-registry-", dir=root))
    entries: list[tuple[Path, Path, Path | None]] = []
    committed: list[tuple[Path, Path | None]] = []
    try:
        for index, (rel, payload) in enumerate(payloads.items()):
            target = root / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            staged = stage / f"new-{index}"
            _write_fsync(staged, payload)
            backup = None
            if expected[rel] is not None:
                backup = stage / f"backup-{index}"
                _write_fsync(backup, expected[rel] or b"")
            entries.append((target, staged, backup))
        _fsync_dir(stage)
        for rel, before in expected.items():
            target = root / rel
            current = target.read_bytes() if target.exists() else None
            if current != before:
                raise RuntimeError(f"registry drift since snapshot A: {target}")
        try:
            for target, staged, backup in entries:
                rel = target.relative_to(root)
                current = target.read_bytes() if target.exists() else None
                if current != expected[rel]:
                    raise RuntimeError(f"registry drift immediately before replace: {target}")
                os.replace(staged, target)
                committed.append((target, backup))
                _fsync_dir(target.parent)
        except Exception as error:
            rollback_errors: list[str] = []
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
                    f"Sextus registry rollback incomplete: {rollback_errors}"
                ) from error
            raise RuntimeError(
                f"Sextus registry commit failed; rollback succeeded: {error}"
            ) from error
    finally:
        shutil.rmtree(stage, ignore_errors=True)
        _fsync_dir(root)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--registry-root", type=Path, default=REGISTRY_ROOT)
    args = parser.parse_args(argv)
    root = args.registry_root.expanduser().resolve()
    facts = cohort_facts(ROOT)
    files, snapshot = load_files(root)
    transformed, changed, quarantine, mode = transform(files, facts)
    artifact_rows = artifact_payloads(changed, quarantine, facts)
    if mode == "legacy":
        transformed[PLAN_REL] = [json.loads(artifact_rows[PLAN_REL])]
        transformed[QUARANTINE_REL] = [
            json.loads(line)
            for line in artifact_rows[QUARANTINE_REL].decode().splitlines()
            if line.strip()
        ]
        transformed[REPORT_REL] = [json.loads(artifact_rows[REPORT_REL])]
    validate(transformed)
    summary = {
        "mode": "write" if args.write else "dry-run",
        "source_state": mode,
        "changed": dict(changed),
        "changed_total": sum(changed.values()),
        "issue_status": "resolved",
        "coverage_state": "partial",
        "evidence_ids": [EVIDENCE_PH, EVIDENCE_AM],
        "write_performed": False,
    }
    if not args.write or not changed:
        print(json.dumps(summary, indent=2, sort_keys=True))
        return 0
    payloads = {
        SOURCE_REL: encode_jsonl(transformed[SOURCE_REL]),
        ISSUE_REL: encode_jsonl(transformed[ISSUE_REL]),
        WAVE_REL: encode_jsonl(transformed[WAVE_REL]),
        EVIDENCE_REL: encode_jsonl(transformed[EVIDENCE_REL]),
        VERIFICATION_REL: encode_jsonl(transformed[VERIFICATION_REL]),
        **artifact_rows,
    }
    commit_registry(root, snapshot, payloads)
    summary["write_performed"] = True
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
