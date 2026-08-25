#!/usr/bin/env python3
"""Repair the Sorabji 1980 bibliography and bounded interpretation cluster.

The command is a dry-run by default. ``--write`` is required for repository
mutation.  It never edits ancient text, corpus passages, corpus manifests, or
snapshot baselines.

The repair:

* separates the intellectual publication from Duckworth 1980, Cornell 1980 /
  first Cornell paperback 1983, and Chicago 2006 manifestations;
* separates the source scan from its OCR derivative;
* corrects the exact order of Sorabji's eight Stoic retreat strategies;
* keeps three competing readings of Chrysippus' cylinder argument attributed;
* narrows proven over-assertions without replacing generic concepts with
  Sorabji's interpretation;
* registers short, paraphrase-only secondary evidence with open factual issues.

All changed records have canonical before-hash preconditions.  Removed edges,
changed records, and absence preconditions are preserved in a quarantine when
``--write`` is eventually authorized.  Unrelated raw JSONL lines are preserved.
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
STAMP = "sorabji_p0_2026_08_24"
NOW = "2026-08-24 08:00:00+00:00"
ACCESSED_AT = "2026-08-24T08:00:00Z"

SCAN_RELATIVE = "data/literature_acquisition/sorabji_1980_necessity_cause_blame.pdf"
OCR_RELATIVE = (
    "data/literature_acquisition/sorabji_1980_necessity_cause_blame_ocr.pdf"
)
AUDIT_RELATIVE = (
    "docs/academic/2026-08-24-sorabji-necessity-cause-blame-pdf-audit.md"
)
INDEPENDENT_REVIEW_RELATIVE = (
    "docs/academic/2026-08-24-sorabji-p0-independent-review.md"
)
SCRIPT_RELATIVE = "scripts/apply_2026_08_24_sorabji_p0_repair.py"
TEST_RELATIVE = "tests/test_sorabji_p0_repair.py"
PUBLICATIONS_BIB_RELATIVE = "data/kg/publications.bib"
PUBLICATIONS_BIB_REPORT_RELATIVE = "data/kg/publications_bibtex_report.json"
REPORT_RELATIVE = "data/audit/2026-08-24_sorabji_p0_repair.json"
QUARANTINE_RELATIVE = "data/audit/2026-08-24_sorabji_p0_quarantine.jsonl"
LOCK_RELATIVE = "data/audit/.sorabji_p0.lock"
JOURNAL_RELATIVE = "data/audit/.sorabji_p0_transaction.json"
BACKUP_DIR_RELATIVE = "data/audit/.sorabji_p0_transaction_backups"

SCAN_SHA256 = "be1f8fce483503d04504c73da30dc9bbcd52f5f8c04bd0e520cbd42fd4a3d500"
SCAN_MD5 = "fad1922c52969d334243888e0f9856a6"
SCAN_BYTES = 35_334_906
OCR_SHA256 = "022e9c6440f7a5e43f89c72205795165853ae85b97389b167027a3bf0e38b007"
OCR_MD5 = "e474ab26adb4f127a0445f1e2628ae28"
OCR_BYTES = 79_185_903
AUDIT_SHA256 = "1b02d8f0bc78bad2d18aa0ed378fb2456c879b3e4e942a3e638c49fb61dbe4af"
INDEPENDENT_REVIEW_SHA256 = (
    "59bd36d9ebe64994a9921cc4961da12d659a82d45888652ce8d0c3e666094e3b"
)

PUB_ID = "pub_sorabji_1980_necessity_cause_blame"
PERSON_ID = "person_sorabji_richard_contemporary"
POSITION_ID = "scholarly_position_sorabji_aristotle_indeterminist"
TAXONOMY_ID = "argument_chrysippus_causal_taxonomy"
CYLINDER_ARGUMENT_ID = "argument_cylinder_analogy_chrysippus_k1l2m3n4"
CYLINDER_CONCEPT_ID = "concept_cylinder_analogy_chrysippus_e5f6g7h8"
DOG_ID = "argument_the_dog_and_cart_argument_9ba60714"
MASTER_ID = "argument_the_master_argument_kurieuon_logos_355f4d3f"
CLINAMEN_ID = "concept_clinamen_atomic_swerve_epicurus_m3n4o5p6"
EPH_HEMIN_ID = "concept_eph_hemin_in_our_power_aristotle_d4e5f6g7"
STOIC_DEBATE_ID = "debate_stoic_compatibilism"

TOUCHED_NODE_IDS = frozenset(
    {
        PUB_ID,
        PERSON_ID,
        POSITION_ID,
        TAXONOMY_ID,
        CYLINDER_ARGUMENT_ID,
        CYLINDER_CONCEPT_ID,
        DOG_ID,
        MASTER_ID,
        CLINAMEN_ID,
        EPH_HEMIN_ID,
        STOIC_DEBATE_ID,
    }
)

INTERPRETIVE_NODE_IDS = frozenset(
    {
        POSITION_ID,
        TAXONOMY_ID,
        CYLINDER_ARGUMENT_ID,
        CYLINDER_CONCEPT_ID,
        DOG_ID,
        MASTER_ID,
        CLINAMEN_ID,
        EPH_HEMIN_ID,
        STOIC_DEBATE_ID,
    }
)

NODE_BEFORE_HASHES = {
    "argument_chrysippus_causal_taxonomy": "f6e618320b9352774a7b1de0b8cfb963dc1689e83222b639bf017de39a54d390",
    "argument_cylinder_analogy_chrysippus_k1l2m3n4": "0a1efdea08471ef0abb019d996dde03155f6e4c851290b4862554822d5174644",
    "argument_the_dog_and_cart_argument_9ba60714": "296f4243732fcfc53efd55aeb50c37523ccd097bbbe1332518b01111eb7b7c2d",
    "argument_the_master_argument_kurieuon_logos_355f4d3f": "481883bde073519894e48a5137582cd12e809ff29e083ba604babb0c57bf07bf",
    "scholarly_position_sorabji_aristotle_indeterminist": "a49db5b4943d91207289817bc6a4cdee53f55ec491a803625f71c80fdcd142b8",
    "concept_clinamen_atomic_swerve_epicurus_m3n4o5p6": "fe0ac5476daf1d92284ca9ce8f93a643b48fdfb93f62aba4df37d89195e306bf",
    "concept_cylinder_analogy_chrysippus_e5f6g7h8": "22f4e47fdc1a78621a1788fd652bd6063881eec1a517629f92c88cc94b630b47",
    "concept_eph_hemin_in_our_power_aristotle_d4e5f6g7": "331b3e8c08650f7ee845fa71c6d6a9bf842b60be2fdc0bddcdc6f26199c68cb4",
    "debate_stoic_compatibilism": "09cff2ea0b10c5345b77ba1cc4f1e0361aed6ae92e6bf689fd7bdc2e2a6134f9",
    "person_sorabji_richard_contemporary": "13086a513ab7015fd2a7cce61fa5dc81354d6d7bc407d3f0593a95a7c790211b",
    "pub_sorabji_1980_necessity_cause_blame": "33fe5e2d4eee78ff4d9a0f86dab95aae52728739a45132f33a831e060a5d524e",
}

NODE_AFTER_HASHES = {
    "argument_chrysippus_causal_taxonomy": "1f1fff7b798a8e49d3dfd5a0c9655f5de2498120c259016f717e6b3d8d29b34e",
    "argument_cylinder_analogy_chrysippus_k1l2m3n4": "3ec480b6dfae2647a7842e17cbb93c4bcd58ef6ad73fd872ed2acab6c01809b5",
    "argument_the_dog_and_cart_argument_9ba60714": "4717d9c3822f2421dfc942e435c3a930ca7c20cd3a3050a23da9288b2841ed1a",
    "argument_the_master_argument_kurieuon_logos_355f4d3f": "13df9ebcbee6f9a9d44310795649018b1bc07197dd83a7e3379bc4f5f6b90fa0",
    "concept_clinamen_atomic_swerve_epicurus_m3n4o5p6": "40f18bcb6817541b595bce1fa34544106c95abb185aca0966689ee2c686f0889",
    "concept_cylinder_analogy_chrysippus_e5f6g7h8": "f287bcefd1f14c48d68e07a99fc25a8a8391e711faf1f1d50acee180e14c5229",
    "concept_eph_hemin_in_our_power_aristotle_d4e5f6g7": "34cf91cf1d3d2edaafc1ed228b6609c7097a6deddda8734166141d6850f98208",
    "debate_stoic_compatibilism": "76405d4a1cdd4ed88d91e385dfccb5caebc931532b20a16dd3ba6374328944b3",
    "person_sorabji_richard_contemporary": "9cdfb3ccd247dc4631acfc9d11b59f614d060cc63f3804739aea73b73ccfff1b",
    "pub_sorabji_1980_necessity_cause_blame": "d68c19cbf17424e34d40d8ab6c27f10b6e35392d8c09e81661dfad991f3cb17b",
    "scholarly_position_sorabji_aristotle_indeterminist": "c06bdebdbd5d5c7f088baa690d5f64425d33526e04df67777a99755354b6b9d1",
}

DOG_EPICETUS_EDGE_HASHES = {
    "0615cd5b-95aa-4e00-9d2c-264f8fae0c3c": "d2931cbfebafcf6d8b729244dc68a497f7590553472d7a036d97343627d38e76",
    "69f8b629-1c14-4281-83f7-68c6ebaeb820": "0aa0b71b592929355218935296856591ca89e7ced4380403c5fb151e22aab057",
}

SORABJI_2017_ADVANCED_IN_HASHES = {
    "6661f6fc-0127-43e5-afc5-f121ce5f0df4": "191769deb3499c054e8d412b144aa9f6395e3ee09a9f36bd58cb0e555b55805d",
    "c3f17f1b-0be7-472c-a14c-149bd000370a": "755e00f87e3fa827d8f688440f05799aaf4042ac2a12ea8bf889f0497cf16f5c",
    "69c40146-ca70-42bd-a24e-59be64a4eb67": "804a2bfbd16b1d3ba1bfddeb4b740653e23fee829ce14121d05f483fee315f71",
    "212bc786-8fde-4862-af2f-d5298c0b700d": "6fd5b46a9f6d6468c7650b8bd85aa70498afb34028305e1e21270e58324d9189",
    "29ecc7f7-37a8-4914-8790-8403b5ae63d7": "26c2ba789e37c8043435f84210a9281af590df6fa755ceb338de5d033cea795e",
}

E2_BEFORE_SHA256 = "b074f4f9db0686cb7e00b22ab1e3c9ea13fdebf704f7392edc24cccba1622325"
E2_AFTER_SHA256 = "d84f98c3bce2859cc5ec36b9ea5785f5aa92240a05bb902bb6b970261f84e660"
SCHOLARLY_MANIFEST_BEFORE_SHA256 = (
    "09f29e367d7c7337ead88387481d7125312baaa68c554545bd4fa856c96c5fb6"
)
BIB_BEFORE_SHA256 = "aba1895c3ac49568b129d18c96e7543392f04c3ebb81fcbaf2d21e33b52406e9"
BIB_REPORT_BEFORE_SHA256 = (
    "137076a4635826407b5454a8b9fe6611b5548c736138e85930b2917c3fd80325"
)

REGISTRY_BEFORE_HASHES = {
    "src_sec_sorabji_1980_necessity": "6ff02bc4bc67ae348bdeae2835a0e4790dd395613ba46c48357a22dafdb2d216",
    "ev_sec_sorabji_sea_battle_pp91_103": "d4073580e37faa4b74ffd2a4a762b130e66f03a179f3720b70be0064cbde0575",
    "ev_sec_sorabji_ignorance_pp272_275": "0fc8249dc6984dfe16bfdfa7522110211d5fa86e406053dca590ae20c749c231",
    "wave_01_pdf_priority_new_knowledge": "ddb1651b3c230bb70f3c48611611d723e830df999aefab336ec33d3eac0886ae",
}

REGISTRY_AFTER_HASHES = {
    "src_sec_sorabji_1980_necessity": "2344e4d60038cc723373592ec93420353528604a3bba4bf64984eddd182630b0",
    "ev_sec_sorabji_sea_battle_pp91_103": "3125c1bb2768a3363b883020edead09b39b3c03071a4108c1ee0e6cdc294960c",
    "ev_sec_sorabji_ignorance_pp272_275": "11e8ccb934ddc63ced45686ca2427f1f5aea8c32a67b746c7ad1e87f402bc435",
    "wave_01_pdf_priority_new_knowledge": "12d6a8b0c87fa7f871f2dc5910b56573c90e653d2b26c865a62d36f8f8668a6f",
}

SOURCE_ID = "src_sec_sorabji_1980_necessity"
SOURCE_MANIFEST_DIR = "sorabji1980necessity"
SEA_EVIDENCE_ID = "ev_sec_sorabji_sea_battle_pp91_103"
IGNORANCE_EVIDENCE_ID = "ev_sec_sorabji_ignorance_pp272_275"
NEW_EVIDENCE_IDS = (
    "ev_sec_sorabji_bibliographic_manifestations_pdf4_5",
    "ev_sec_sorabji_eight_retreats_pp71_85",
    "ev_sec_sorabji_cylinder_three_readings_pp80_83",
    "ev_sec_sorabji_caused_not_necessitated_pp26_32",
    "ev_sec_sorabji_aristotle_action_pp228_238",
)
ALL_SORABJI_EVIDENCE_IDS = (SEA_EVIDENCE_ID, IGNORANCE_EVIDENCE_ID, *NEW_EVIDENCE_IDS)
MANIFESTATION_ISSUE_ID = "issue_sorabji_manifestation_conflation_20260824"
INTERPRETATION_ISSUE_ID = "issue_sorabji_interpretive_overassertions_20260824"
WAVE_ID = "wave_01_pdf_priority_new_knowledge"

CINII_DUCKWORTH = "https://ci.nii.ac.jp/ncid/BA04347273"
CINII_CORNELL = "https://ci.nii.ac.jp/ncid/BA37345728"
BIBLIOVAULT_CHICAGO = (
    "https://www.bibliovault.org/BV.book.epl?ISBN=9780226768243"
)

EIGHT_STRATEGIES = [
    "1: Cleanthes denies that every past truth is necessary",
    "2: Chrysippus denies that the impossible cannot follow from the possible",
    "3: denying unrestricted transmission of necessity from antecedent to consequent",
    "4: astrology restated with material implication",
    "5: Philonian possibility as aptitude or fitness",
    "6: internal versus external causes, including the cylinder analogy",
    "7: epistemic possibility based on ignorance of preventing factors",
    "8: alleged non-necessity because a future-tense proposition ceases to be true",
]

E2_PAGE_SCOPES = {
    "scholar_position_sorabji_aristotle_indeterminist": {
        "printed_pages": "229-234",
        "pdf_pages": "246-251",
    },
    "scholarly_argument_sorabji_cicero_on_free_will_vs_fate_4": {
        "printed_pages": "18; 78-82; 86 (1980 background only)",
        "pdf_pages": "35; 95-99; 103",
    },
    "new_2026_05_19_chrysippus_dog_cylinder_three_interpretations": {
        "printed_pages": "80-83",
        "pdf_pages": "97-100",
    },
    "new_2026_05_19_stoic_eight_attempts_to_retreat_from_necessity": {
        "printed_pages": "71-85",
        "pdf_pages": "88-102",
    },
    "new_2026_05_19_aristotle_int9_traditional_interpretation": {
        "printed_pages": "92-95",
        "pdf_pages": "109-112",
    },
    "new_2026_05_19_aristotle_alleged_nescience_of_determinism": {
        "printed_pages": "243-245",
        "pdf_pages": "260-262",
    },
    "new_2026_05_19_aristotle_voluntariness_negative_definition_three_versions": {
        "printed_pages": "257-263; 272-281",
        "pdf_pages": "274-280; 289-298",
    },
    "new_2026_05_19_lucretius_swerve_does_not_save_freedom": {
        "printed_pages": "18-19; 86",
        "pdf_pages": "35-36; 103",
    },
}

OLD_BIB_ENTRY = """@book{sorabji-1980-necessity-cause-and-blame-perspectives-on-aristotle-s-theory,
  author = {Richard Sorabji},
  title = {Necessity, Cause, and Blame: Perspectives on Aristotle's Theory},
  year = {1980},
  publisher = {Duckworth},
  isbn = {978-0226768243},
  note = {EleutherIA KG node: pub_sorabji_1980_necessity_cause_blame}
}"""

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
    return str(row.get("id") or row.get("node_id") or "")


def edge_id(row: dict[str, Any]) -> str:
    return str(row.get("edge_id") or "")


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


def rename_reference_bundle(
    data: dict[str, Any], *, target_key: str, status: str
) -> None:
    """Demote a legacy ``verified_reference`` without losing its before meaning."""

    legacy = data.pop("verified_reference", None)
    if legacy not in (None, ""):
        data[target_key] = {
            "references": legacy,
            "status": status,
        }


def mark_interpretive_discovery_only(data: dict[str, Any]) -> dict[str, Any]:
    data = copy.deepcopy(data)
    data["citability"] = "discoverable_only"
    rename_reference_bundle(
        data,
        target_key="reference_bundle_pending_recollation",
        status="secondary_bundle_pending_ancient_primary_recollation",
    )
    return data


def require_exact_record(
    row: dict[str, Any], wanted: str, before_hash: str
) -> None:
    if metadata(row).get(STAMP) is True:
        return
    actual = canonical_hash(row)
    if actual != before_hash:
        raise PreconditionsError(
            f"record drift for {wanted}: expected {before_hash}, actual {actual}"
        )


def manifestation_records() -> list[dict[str, Any]]:
    return [
        {
            "manifestation_id": "sorabji_ncb_duckworth_london_1980",
            "publisher": "Duckworth",
            "place": "London",
            "year": 1980,
            "extent": "xv, 326 p.",
            "isbns": ["0715613723", "0715615491"],
            "binding_assignment": "unresolved_do_not_infer",
            "authority": {
                "kind": "catalog_record",
                "locator": CINII_DUCKWORTH,
                "ncid": "BA04347273",
                "accessed_at": ACCESSED_AT,
            },
            "local_artifact": None,
        },
        {
            "manifestation_id": "sorabji_ncb_cornell_ithaca_1980_family",
            "publisher": "Cornell University Press",
            "place": "Ithaca, N.Y.",
            "year": 1980,
            "extent": "xv, 326 p., [1] leaf of plates",
            "hardback_isbn": "0801411629",
            "paperback": {
                "first_published": 1983,
                "isbn": "0801492440",
                "basis": "local copyright page, PDF 5",
            },
            "authority": {
                "kind": "catalog_record",
                "locator": CINII_CORNELL,
                "ncid": "BA37345728",
                "accessed_at": ACCESSED_AT,
            },
            "local_artifact": {
                "match_basis": (
                    "Cornell title/copyright pages and Cornell Paperbacks covers; "
                    "exact printing not stated"
                ),
                "printing_status": "unknown_not_inferred",
                "scan": {
                    "locator": SCAN_RELATIVE,
                    "sha256": SCAN_SHA256,
                    "md5": SCAN_MD5,
                    "byte_size": SCAN_BYTES,
                    "physical_pages": 344,
                },
                "ocr_derivative": {
                    "locator": OCR_RELATIVE,
                    "sha256": OCR_SHA256,
                    "md5": OCR_MD5,
                    "byte_size": OCR_BYTES,
                    "derivative_only": True,
                },
                "page_map": {
                    "rule": "pdf_page = printed_page + 17",
                    "applies_to_printed_pages": "3-326",
                    "implicit_folio_caveat": (
                        "printed 1-2 and some front-matter folios are inferred from "
                        "sequence because the folio is suppressed"
                    ),
                    "status": "visually_verified",
                },
            },
        },
        {
            "manifestation_id": "sorabji_ncb_chicago_2006",
            "publisher": "University of Chicago Press",
            "place": "Chicago",
            "year": 2006,
            "isbn_10": "0226768244",
            "isbn_13": "9780226768243",
            "authority": {
                "kind": "publisher_catalog_record",
                "locator": BIBLIOVAULT_CHICAGO,
                "accessed_at": ACCESSED_AT,
            },
            "local_artifact": None,
        },
    ]


def bibtex_manifestation_records() -> list[dict[str, Any]]:
    """Concrete records consumed by the canonical BibTeX exporter."""

    return [
        {
            "manifestation_id": "sorabji_ncb_duckworth_london_1980",
            "bibtex_key": "sorabji-1980-necessity-cause-and-blame-duckworth",
            "year": 1980,
            "publisher": "Duckworth",
            "address": "London",
            "isbn": "0715613723; 0715615491",
            "type": "book",
        },
        {
            "manifestation_id": "sorabji_ncb_cornell_ithaca_1980_hardback",
            "bibtex_key": "sorabji-1980-necessity-cause-and-blame-cornell",
            "year": 1980,
            "publisher": "Cornell University Press",
            "address": "Ithaca, N.Y.",
            "isbn": "0801411629",
            "type": "book",
        },
        {
            "manifestation_id": "sorabji_ncb_cornell_paperbacks_first_edition_1983",
            "bibtex_key": (
                "sorabji-1983-necessity-cause-and-blame-cornell-paperbacks"
            ),
            "year": 1983,
            "publisher": "Cornell University Press",
            "address": "Ithaca, N.Y.",
            "isbn": "0801492440",
            "type": "book",
        },
        {
            "manifestation_id": "sorabji_ncb_chicago_2006",
            "bibtex_key": "sorabji-2006-necessity-cause-and-blame-chicago",
            "year": 2006,
            "publisher": "University of Chicago Press",
            "address": "Chicago",
            "isbn": "9780226768243",
            "type": "book",
        },
    ]


def transform_person(row: dict[str, Any]) -> dict[str, Any]:
    row = copy.deepcopy(row)
    old = "(Duckworth, 1980 ; réimpression Bristol Classical Press, 2006)"
    new = (
        "(manifestations Duckworth et Cornell University Press, 1980 ; "
        "University of Chicago Press, 2006)"
    )
    if old not in str(row.get("description") or ""):
        raise PreconditionsError("Sorabji person description no longer has reviewed text")
    row["description"] = str(row["description"]).replace(old, new)
    data = metadata(row)
    data.pop("citation_verified", None)
    data.pop("verified", None)
    rename_reference_bundle(
        data,
        target_key="reference_bundle_catalog_checked",
        status="catalog_identity_checked_for_ncb_manifestations_only",
    )
    data["citation_verdict"] = "catalog_identity_checked_manifestations_separated"
    data[STAMP] = True
    data["bibliographic_correction"] = {
        "scope": "Necessity, Cause and Blame manifestations only",
        "duckworth_authority": CINII_DUCKWORTH,
        "cornell_authority": CINII_CORNELL,
        "chicago_2006_authority": BIBLIOVAULT_CHICAGO,
        "status": "catalog_identity_checked_manifestations_separated",
    }
    set_metadata(row, data)
    row["updated_at"] = NOW
    return row


def transform_publication(row: dict[str, Any]) -> dict[str, Any]:
    row = copy.deepcopy(row)
    row["description"] = (
        "Intellectual publication record for Richard Sorabji's 1980 monograph. "
        "Publisher, place, ISBN and local-artifact data are manifestation-specific."
    )
    data = metadata(row)
    for key in ("isbn", "place", "publisher", "verified"):
        data.pop(key, None)
    data.pop("citation_verified", None)
    data.pop("verified_reference", None)
    data.update(
        {
            STAMP: True,
            "publication_identity": "intellectual_publication",
            "first_publication_year": 1980,
            "manifestations": manifestation_records(),
            "bibtex_manifestations": bibtex_manifestation_records(),
            "citation_verdict": "corrected_manifestations_separated",
            "catalog_identity_status": "checked_manifestations_separated",
            "verification_status": (
                "catalog_identity_checked_manifestations_separated_local_printing_unknown"
            ),
            "verification_scope": (
                "intellectual title/author/year and listed manifestation identities; "
                "not the exact printing of the local Cornell scan"
            ),
            "reference_bundle_catalog_checked": {
                "status": "dual_1980_catalog_identity_checked",
                "references": (
                "Richard Sorabji, Necessity, Cause, and Blame: Perspectives on "
                "Aristotle's Theory (London: Duckworth, 1980; Ithaca, N.Y.: "
                "Cornell University Press, 1980). Edition-specific records are "
                "listed separately; Chicago 2006 is not an ISBN for the 1980 record."
                ),
            },
        }
    )
    set_metadata(row, data)
    row["updated_at"] = NOW
    return row


def replace_premise(data: dict[str, Any], premise_id: str, text: str) -> None:
    matches = [p for p in data.get("premises", []) if p.get("id") == premise_id]
    if len(matches) != 1:
        raise PreconditionsError(f"expected one premise {premise_id}")
    matches[0]["text"] = text
    matches[0]["attestation"] = "reconstructed"
    matches[0]["primary_sources"] = []
    matches[0]["secondary_sources"] = []


def visual_secondary_metadata(
    data: dict[str, Any], *, printed: str, pdf: str, status: str
) -> dict[str, Any]:
    data = copy.deepcopy(data)
    data.pop("citation_verified", None)
    data.pop("verified", None)
    data = mark_interpretive_discovery_only(data)
    data[STAMP] = True
    data["needs_evidence"] = True
    data["interpretation_status"] = status
    data["sorabji_1980_visual_evidence"] = {
        "publication_id": PUB_ID,
        "printed_pages": printed,
        "pdf_pages": pdf,
        "page_map_status": "visually_verified",
        "scan_sha256": SCAN_SHA256,
        "evidence_role": "secondary_interpretation_not_primary_attestation",
        "review_status": "pending_independent_adversarial_and_human_signoff",
    }
    data["page_support_status"] = "checked_against_local_source_scan"
    return data


def transform_position(row: dict[str, Any]) -> dict[str, Any]:
    row = copy.deepcopy(row)
    row["description"] = (
        "Sorabji's disputed 1980 reconstruction separates coincidences from "
        "other effects. He reads Metaphysics VI.3 as denying causes to "
        "coincidences, while arguing that other effects—including a constructed "
        "human-action example—may be caused without being necessitated. On this "
        "reading, the same human circumstances could have issued in another "
        "action without an uncaused fresh start, a separate faculty of will, or "
        "a break in the causal chain."
    )
    data = metadata(row)
    replace_premise(
        data,
        "P3",
        (
            "Sorabji reads Metaphysics VI.3 as denying causes to coincidences; "
            "his caused-without-necessitated model is instead applied to other "
            "effects, including his constructed example of human action."
        ),
    )
    replace_premise(
        data,
        "P4",
        (
            "Sorabji denies that Aristotle needs uncaused 'fresh starts' or a "
            "separate faculty of will, while still allowing that the same human "
            "circumstances could have issued in another action."
        ),
    )
    data["conclusion"]["text"] = (
        "Sorabji reconstructs Aristotle as allowing caused but non-necessitated "
        "human action without an uncaused break in the causal chain. This is a "
        "disputed modern interpretation, not primary-source or consensus status."
    )
    data = visual_secondary_metadata(
        data,
        printed="26-32; 228-242; 243-248",
        pdf="43-49; 245-259; 260-265",
        status="attributed_disputed_sorabji_interpretation",
    )
    data["key_work_reference"] = PUB_ID
    data["scholarly_work_id"] = PUB_ID
    data["citation_verdict"] = "source_checked_disputed_interpretation"
    data["verification_scope"] = (
        "Sorabji's secondary claim is visually page-checked; Aristotelian loci "
        "and scholarly consensus are not verified by this status."
    )
    data["reference_bundle_pending_recollation"] = {
        "references": (
            "Richard Sorabji, Necessity, Cause, and Blame (1980), pp. 26-32, "
            "228-242, 243-248; local Cornell scan PDF 43-49, 245-265."
        ),
        "status": "secondary_pages_checked_ancient_loci_pending_recollation",
    }
    set_metadata(row, data)
    row["updated_at"] = NOW
    return row


def cylinder_readings() -> list[dict[str, str]]:
    return [
        {
            "reading": "internal cause escapes necessity",
            "attributed_to": "Augustine's reading of Chrysippus",
        },
        {
            "reading": "responsibility is preserved despite acknowledged necessity",
            "attributed_to": "P. L. Donini's interpretation",
        },
        {
            "reading": (
                "necessity is denied only as imposed by fate understood as external causes"
            ),
            "attributed_to": "Michael Frede's interpretation",
        },
    ]


def transform_taxonomy(row: dict[str, Any]) -> dict[str, Any]:
    row = copy.deepcopy(row)
    row["description"] = (
        "Sorabji presents the Cicero and Gellius reports as distinguishing external conditions and "
        "internal causes of assent. External impressions are necessary conditions, "
        "not sufficient causes; character is internal. Sorabji distinguishes three "
        "competing readings of what this establishes and does not locate "
        "necessitation exclusively in auxiliary causes."
    )
    data = metadata(row)
    replace_premise(
        data,
        "P5",
        (
            "External impressions are reported as necessary but not sufficient "
            "conditions. Whether the total causal nexus necessitates assent depends "
            "on the disputed interpretation of Chrysippus."
        ),
    )
    data["conclusion"]["text"] = (
        "The taxonomy distinguishes external from internal causal contribution; "
        "its success in reconciling necessity and responsibility remains disputed."
    )
    data = visual_secondary_metadata(
        data,
        printed="64-69; 79-85",
        pdf="81-86; 96-102",
        status="source_loci_present_interpretation_disputed",
    )
    data["sorabji_1980_readings"] = cylinder_readings()
    data["sorabji_1980_conclusion"] = (
        "The eight Stoic retreats fail to escape commitment to necessity."
    )
    data["citation_verdict"] = "disputed_interpretation"
    data.pop("citation_verified", None)
    set_metadata(row, data)
    row["updated_at"] = NOW
    return row


def transform_cylinder_argument(row: dict[str, Any]) -> dict[str, Any]:
    row = copy.deepcopy(row)
    row["description"] = (
        "The cylinder analogy distinguishes an external push or impression from "
        "the cylinder's or agent's internal nature. Sorabji 1980, pp. 80-83, "
        "separates Augustine, Donini and Frede readings of the argument. He does "
        "not treat any one reading as established and concludes that the Stoic "
        "retreats fail to escape commitment to necessity."
    )
    data = metadata(row)
    data["conclusion"]["text"] = (
        "The analogy locates an internal causal contribution, but whether that "
        "preserves responsibility or escapes necessity is a disputed interpretation."
    )
    data = visual_secondary_metadata(
        data,
        printed="80-83",
        pdf="97-100",
        status="three_attributed_readings_no_single_adjudicated_doctrine",
    )
    data["sorabji_1980_readings"] = cylinder_readings()
    data["sorabji_1980_conclusion"] = (
        "The eight Stoic retreats fail to escape commitment to necessity."
    )
    data["citation_verdict"] = "source_loci_verified_interpretation_disputed"
    data.pop("citation_verified", None)
    set_metadata(row, data)
    row["updated_at"] = NOW
    return row


def transform_cylinder_concept(row: dict[str, Any]) -> dict[str, Any]:
    row = copy.deepcopy(row)
    row["description"] = (
        "Cicero and Gellius use the cylinder to distinguish an external initiating "
        "condition from internal nature. The further modal and moral conclusion is "
        "disputed. Sorabji 1980 distinguishes Augustine, Donini and Frede readings "
        "and concludes that the Stoic retreats do not escape necessity."
    )
    data = metadata(row)
    data = visual_secondary_metadata(
        data,
        printed="80-85",
        pdf="97-102",
        status="generic_concept_with_competing_interpretations",
    )
    data["typed_readings"] = cylinder_readings()
    data["citation_verdict"] = "source_loci_verified_interpretation_disputed"
    data.pop("citation_verified", None)
    data.pop("verified", None)
    set_metadata(row, data)
    row["updated_at"] = NOW
    return row


def transform_dog(row: dict[str, Any]) -> dict[str, Any]:
    row = copy.deepcopy(row)
    row["description"] = (
        "The dog tied to a moving cart follows willingly or is dragged, while the "
        "outcome remains necessary. The analogy contrasts consent with resistance; "
        "it does not by itself establish a power to choose an alternative outcome. "
        "Sorabji cites Hippolytus, Refutatio I.21, for the comparison."
    )
    data = metadata(row)
    data.pop("ancient_attestation_locus_classicus", None)
    data.pop("primary_source", None)
    data.pop("formulator", None)
    data.pop("targets", None)
    data.pop("legacy_premises", None)
    data.pop("verified_reference", None)
    data.pop("reference_bundle_pending_recollation", None)
    data["candidate_witness"] = {
        "reported_by_secondary": "Sorabji 1980, p. 70 (local PDF 87)",
        "candidate_source": "Hippolytus, Refutatio Omnium Haeresium I.21",
        "attributed_figures": ["Zeno of Citium", "Chrysippus of Soli"],
        "status": "pending_hippolytus_primary_recollation",
    }
    data["ancient_sources"] = [
        "Hippolytus, Refutatio Omnium Haeresium I.21 (candidate reported witness)",
        (
            "Seneca, Epistulae 107.11 is a related willing/dragged maxim, not "
            "the direct dog-and-cart report"
        ),
    ]
    data["premises"] = [
        {
            "id": "P1",
            "text": (
                "A dog tied to a moving cart follows the cart's motion whether "
                "willingly or while resisting."
            ),
            "attestation": "reconstructed_from_sorabji_report",
            "primary_sources": [],
            "secondary_sources": [PUB_ID],
        },
        {
            "id": "P2",
            "text": (
                "Following willingly combines consent with necessity; it does not "
                "show that another outcome was open."
            ),
            "attestation": "reconstructed_from_sorabji_report",
            "primary_sources": [],
            "secondary_sources": [PUB_ID],
        },
        {
            "id": "P3",
            "text": (
                "Resistance changes whether the dog is dragged, not the necessary "
                "result that it moves with the cart."
            ),
            "attestation": "reconstructed_from_sorabji_report",
            "primary_sources": [],
            "secondary_sources": [PUB_ID],
        },
        {
            "id": "P4",
            "text": (
                "The comparison illustrates consent versus resistance under a "
                "necessary result; no further agency thesis follows from it alone."
            ),
            "attestation": "interpretive_scope",
            "primary_sources": [],
            "secondary_sources": [PUB_ID],
        },
    ]
    data["conclusion"]["text"] = (
        "The analogy illustrates willing or unwilling accommodation to a necessary "
        "outcome; it does not itself prove alternative possibilities."
    )
    data = visual_secondary_metadata(
        data,
        printed="70; 87-88",
        pdf="87; 104-105",
        status="doxographical_analogy_interpretive_scope_disputed",
    )
    data["argument_form"] = "analogy"
    data["argument_type"] = "doxographical analogy pending primary recollation"
    data["interpretive_scope"] = (
        "consent or resistance under a necessary outcome; no alternative or "
        "general theory of agency is established"
    )
    data["validity_assessment"] = {
        "status": "not_assessed_pending_primary_recollation",
        "rationale": (
            "The record is an analogy reported through Sorabji; its candidate "
            "Hippolytan witness has not been recollated in this wave."
        ),
    }
    data["citation_verdict"] = "direct_witness_pending_recollation"
    data.pop("citation_verified", None)
    set_metadata(row, data)
    row["updated_at"] = NOW
    return row


def transform_master(row: dict[str, Any]) -> dict[str, Any]:
    row = copy.deepcopy(row)
    row["description"] = (
        "Diodorus Cronus' Master Argument about possibility and necessity is "
        "preserved in Epictetus, Discourses II.19. Sorabji calls Diodorus a "
        "dialectician and follows Sedley in rejecting a categorical Megarian-school "
        "classification. Detailed reconstructions remain hypothetical."
    )
    data = metadata(row)
    data.pop("citation_verified", None)
    data.pop("verified", None)
    data = mark_interpretive_discovery_only(data)
    data[STAMP] = True
    data["needs_evidence"] = True
    data["school_attribution_status"] = (
        "disputed_not_categorically_megarian; Sorabji 1980 follows Sedley 1977"
    )
    data["reconstruction_status"] = "premises_reported_detailed_argument_uncertain"
    data["sorabji_1980_visual_evidence"] = {
        "printed_pages": "104-110",
        "pdf_pages": "121-127",
        "scan_sha256": SCAN_SHA256,
        "page_map_status": "visually_verified",
        "review_status": "pending_primary_recollation_and_human_signoff",
    }
    data["citation_verdict"] = "source_locus_verified_school_and_reconstruction_disputed"
    data["verification_scope"] = "Epictetus locus, not school affiliation or a unique reconstruction"
    set_metadata(row, data)
    row["updated_at"] = NOW
    return row


def transform_clinamen(row: dict[str, Any]) -> dict[str, Any]:
    row = copy.deepcopy(row)
    row["description"] = (
        "The atomic swerve is most fully connected with freedom in Lucretius, "
        "De Rerum Natura II.216-293, while Cicero reports the Epicurean debate. "
        "This Sorabji evidence does not provide a surviving passage of Epicurus "
        "that explicitly states this motive. That motivation and "
        "the swerve's role in action remain disputed modern reconstructions."
    )
    data = metadata(row)
    data = mark_interpretive_discovery_only(data)
    data[STAMP] = True
    data["needs_evidence"] = True
    data["interpretation_status"] = "epicurus_lucretius_witnesses_must_be_distinguished"
    data["typed_attestations"] = [
        {
            "source": "Lucretius, De Rerum Natura II.216-293",
            "role": "extant Latin exposition connecting swerve and free voluntas",
        },
        {
            "source": "Cicero, De Fato 22-23 and De Natura Deorum I.69-70",
            "role": "hostile or argumentative report of Epicurean doctrine",
        },
        {
            "source": "Epicurus' surviving texts",
            "role": (
                "this Sorabji evidence supplies no explicit Epicurus passage "
                "stating the free-will motive"
            ),
        },
    ]
    data["sorabji_1980_visual_evidence"] = {
        "printed_pages": "18-19; 86",
        "pdf_pages": "35-36; 103",
        "scan_sha256": SCAN_SHA256,
        "page_map_status": "visually_verified",
        "evidence_role": "secondary framing and reported objection",
    }
    data["citation_verdict"] = "witnesses_distinguished_motive_disputed"
    data.pop("citation_verified", None)
    set_metadata(row, data)
    row["updated_at"] = NOW
    return row


def transform_eph_hemin(row: dict[str, Any]) -> dict[str, Any]:
    row = copy.deepcopy(row)
    row["description"] = (
        "**Étymologie** : τὸ ἐφ' ἡμῖν, syntagme attributif « ce qui est sur "
        "nous / en notre pouvoir » < ἐπί + datif pronom personnel 1ʳᵉ pl. "
        "Locution technique aristotélicienne (*EN* III.5) reprise par les "
        "Stoïciens et les Médio-Platoniciens.\n\n"
        "Cross-period concept node. In Sorabji's disputed 1980 reading, "
        "Aristotelian human eph' hemin implies a two-way possibility. The Stoic "
        "position he reports through Alexander and Nemesius permits action "
        "through us and according to impulse without an open alternative. Later "
        "one-sided and two-sided reconstructions remain disputed; this node "
        "states no single ancient doctrine or consensus."
    )
    data = metadata(row)
    data.pop("citation_verified", None)
    data.pop("verified", None)
    data = mark_interpretive_discovery_only(data)
    data[STAMP] = True
    data["needs_evidence"] = True
    data["interpretation_status"] = "composite_disputed_requires_source_specific_partitions"
    data["typed_readings"] = [
        {
            "assertor": "Richard Sorabji 1980",
            "claim": (
                "Aristotelian human eph' hemin implies a two-way possibility and "
                "supports an indeterminist interpretation."
            ),
            "printed_pages": "233-235",
            "pdf_pages": "250-252",
        },
        {
            "assertor": "Stoic position as reported by Alexander and Nemesius",
            "claim": (
                "An action can be through us and in accordance with impulse without "
                "an alternative action being possible."
            ),
            "printed_pages_in_sorabji_1980": "86; 252",
            "pdf_pages_in_sorabji_1980": "103; 269",
        },
        {
            "assertor": "Susanne Bobzien and later scholarship",
            "claim": "One-sided causative and two-sided potestative readings are disputed.",
            "status": "retain_as_modern_scholarly_interpretation",
        },
    ]
    data["scope_warning"] = (
        "This concept node is a cross-period map, not a single verified doctrine "
        "or scholarly consensus."
    )
    data["citation_verdict"] = "disputed_composite"
    data.pop("citation_verified", None)
    set_metadata(row, data)
    row["updated_at"] = NOW
    return row


def transform_debate(row: dict[str, Any]) -> dict[str, Any]:
    row = copy.deepcopy(row)
    row["description"] = (
        "Modern analytical debate node, not a single ancient doctrine. Sorabji "
        "1980 distinguishes Augustine, Donini and Frede readings of the cylinder, "
        "says the soft reply appears perhaps with Chrysippus, and judges the eight "
        "retreats unsuccessful. Compatibilism, one-sided eph' hemin and the moral "
        "success of the cylinder remain disputed pending primary recollation."
    )
    data = metadata(row)
    data.pop("citation_verified", None)
    data.pop("verified", None)
    data = mark_interpretive_discovery_only(data)
    data[STAMP] = True
    data["needs_evidence"] = True
    data["interpretation_status"] = "modern_analytic_category_with_disputed_reconstructions"
    data["typed_readings"] = cylinder_readings()
    data["sorabji_1980_position"] = {
        "claim": (
            "The soft reply appears perhaps with Chrysippus; Sorabji judges the "
            "eight attempts to escape necessity unsuccessful."
        ),
        "printed_pages": "85-88; 251-256",
        "pdf_pages": "102-105; 268-273",
        "scan_sha256": SCAN_SHA256,
        "status": "attributed_disputed_secondary_interpretation",
    }
    data["scope_warning"] = (
        "Do not treat compatibilism, one-sided eph' hemin, or the cylinder's moral "
        "success as one ancient consensus."
    )
    data["citation_verdict"] = "disputed_composite"
    data.pop("citation_verified", None)
    set_metadata(row, data)
    row["updated_at"] = NOW
    return row


NODE_TRANSFORMS: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {
    PERSON_ID: transform_person,
    PUB_ID: transform_publication,
    POSITION_ID: transform_position,
    TAXONOMY_ID: transform_taxonomy,
    CYLINDER_ARGUMENT_ID: transform_cylinder_argument,
    CYLINDER_CONCEPT_ID: transform_cylinder_concept,
    DOG_ID: transform_dog,
    MASTER_ID: transform_master,
    CLINAMEN_ID: transform_clinamen,
    EPH_HEMIN_ID: transform_eph_hemin,
    STOIC_DEBATE_ID: transform_debate,
}


def transform_nodes(
    rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], Counter[str]]:
    rows = copy.deepcopy(rows)
    by_id = {node_id(row): row for row in rows}
    if len(by_id) != len(rows):
        raise PreconditionsError("duplicate KG node id before Sorabji repair")
    missing = TOUCHED_NODE_IDS - by_id.keys()
    if missing:
        raise PreconditionsError(f"missing Sorabji touched nodes: {sorted(missing)}")
    quarantine: list[dict[str, Any]] = []
    counts: Counter[str] = Counter()
    for wanted in sorted(TOUCHED_NODE_IDS):
        current = by_id[wanted]
        if metadata(current).get(STAMP) is True:
            if canonical_hash(current) != NODE_AFTER_HASHES[wanted]:
                raise PreconditionsError(f"applied Sorabji node drift: {wanted}")
            continue
        desired = NODE_TRANSFORMS[wanted](current)
        require_exact_record(current, wanted, NODE_BEFORE_HASHES[wanted])
        quarantine.append(
            {"record_type": "kg_node_before", "record": copy.deepcopy(current)}
        )
        current.clear()
        current.update(desired)
        counts["kg_nodes_modified"] += 1
    validate_nodes(rows)
    return rows, quarantine, counts


def validate_nodes(rows: list[dict[str, Any]]) -> None:
    by_id = {node_id(row): row for row in rows}
    for wanted in TOUCHED_NODE_IDS:
        if metadata(by_id[wanted]).get(STAMP) is not True:
            raise RuntimeError(f"Sorabji stamp missing on {wanted}")
        data = metadata(by_id[wanted])
        if "citation_verified" in data or "verified" in data:
            raise RuntimeError(f"generic verified boolean survives on {wanted}")
        if "verified_reference" in data:
            raise RuntimeError(f"active verified_reference survives on {wanted}")
    for wanted in INTERPRETIVE_NODE_IDS:
        if metadata(by_id[wanted]).get("citability") != "discoverable_only":
            raise RuntimeError(f"interpretive node remains runtime-citable: {wanted}")
    pub_data = metadata(by_id[PUB_ID])
    if any(key in pub_data for key in ("isbn", "place", "publisher", "verified")):
        raise RuntimeError("abstract Sorabji publication retains manifestation fields")
    manifestations = pub_data.get("manifestations") or []
    if [row.get("manifestation_id") for row in manifestations] != [
        "sorabji_ncb_duckworth_london_1980",
        "sorabji_ncb_cornell_ithaca_1980_family",
        "sorabji_ncb_chicago_2006",
    ]:
        raise RuntimeError("Sorabji manifestations are not exactly separated")
    if manifestations[0].get("binding_assignment") != "unresolved_do_not_infer":
        raise RuntimeError("Duckworth bindings were inferred")
    if (
        manifestations[1].get("local_artifact", {}).get("printing_status")
        != "unknown_not_inferred"
    ):
        raise RuntimeError("local Cornell printing was inferred")
    bibtex_manifestations = pub_data.get("bibtex_manifestations") or []
    if bibtex_manifestations != bibtex_manifestation_records():
        raise RuntimeError("Sorabji canonical BibTeX manifestations are incomplete")
    if any(
        not row.get("publisher") or not row.get("year")
        for row in bibtex_manifestations
    ):
        raise RuntimeError("Sorabji BibTeX contains an abstract publisher-less book")
    haystack = json.dumps(
        [by_id[TAXONOMY_ID], by_id[CYLINDER_ARGUMENT_ID], by_id[CYLINDER_CONCEPT_ID]],
        ensure_ascii=False,
    ).lower()
    if "necessitated only by auxiliary causes" in haystack:
        raise RuntimeError("auxiliary-cause over-assertion survived")
    for wanted in (TAXONOMY_ID, CYLINDER_ARGUMENT_ID, CYLINDER_CONCEPT_ID):
        data = metadata(by_id[wanted])
        readings = data.get("sorabji_1980_readings") or data.get("typed_readings")
        if not isinstance(readings, list) or len(readings) != 3:
            raise RuntimeError(f"{wanted} lacks the three cylinder readings")
    if "megarian school" in str(by_id[MASTER_ID].get("description") or "").lower():
        raise RuntimeError("Diodorus remains categorically Megarian")
    if "can choose their attitude" in str(by_id[DOG_ID].get("description") or "").lower():
        raise RuntimeError("dog/cart still guarantees an alternative choice")
    dog_data = metadata(by_id[DOG_ID])
    if dog_data.get("primary_source") or dog_data.get("ancient_attestation_locus_classicus"):
        raise RuntimeError("dog/cart candidate witness is falsely primary-verified")
    if dog_data.get("candidate_witness", {}).get("status") != (
        "pending_hippolytus_primary_recollation"
    ):
        raise RuntimeError("dog/cart candidate witness is not fail-closed")
    if any(
        key in dog_data
        for key in ("formulator", "targets", "legacy_premises", "verified_reference")
    ):
        raise RuntimeError("dog/cart retains an active legacy assertion")
    if dog_data.get("argument_form") != "analogy":
        raise RuntimeError("dog/cart is not typed as an analogy")
    if dog_data.get("validity_assessment", {}).get("status") != (
        "not_assessed_pending_primary_recollation"
    ):
        raise RuntimeError("dog/cart validity remains affirmatively assessed")
    p2 = next(
        premise for premise in dog_data.get("premises", []) if premise.get("id") == "P2"
    )
    if "combines consent with necessity" not in str(p2.get("text") or ""):
        raise RuntimeError("dog/cart P2 does not preserve consent plus necessity")
    clinamen_text = str(by_id[CLINAMEN_ID].get("description") or "").lower()
    if "epicurus introduced the swerve explicitly" in clinamen_text:
        raise RuntimeError("Epicurus/Lucretius motive remains conflated")
    for wanted in (EPH_HEMIN_ID, STOIC_DEBATE_ID):
        data = metadata(by_id[wanted])
        if data.get("needs_evidence") is not True or "disputed" not in str(
            data.get("interpretation_status")
        ):
            raise RuntimeError(f"generic composite node not marked disputed: {wanted}")


def validate_eight_strategies(strategies: list[str]) -> None:
    if len(strategies) != 8:
        raise RuntimeError("Sorabji strategy order must contain exactly eight entries")
    prefixes = [str(value).split(":", 1)[0].strip() for value in strategies]
    if prefixes != [str(index) for index in range(1, 9)]:
        raise RuntimeError("Sorabji strategy numbers must be exactly 1 through 8")


def transform_edges(
    rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], Counter[str]]:
    rows = copy.deepcopy(rows)
    by_id = {edge_id(row): row for row in rows}
    if len(by_id) != len(rows):
        raise PreconditionsError("duplicate KG edge id before Sorabji repair")
    for wanted, expected in SORABJI_2017_ADVANCED_IN_HASHES.items():
        if wanted not in by_id or canonical_hash(by_id[wanted]) != expected:
            raise PreconditionsError(f"Sorabji 2017 provenance edge drift: {wanted}")
    quarantine: list[dict[str, Any]] = []
    counts: Counter[str] = Counter()
    retained: list[dict[str, Any]] = []
    seen_removed: set[str] = set()
    for row in rows:
        wanted = edge_id(row)
        if wanted in DOG_EPICETUS_EDGE_HASHES:
            if canonical_hash(row) != DOG_EPICETUS_EDGE_HASHES[wanted]:
                raise PreconditionsError(f"dog/Epictetus edge drift: {wanted}")
            quarantine.append(
                {"record_type": "kg_edge_removed", "record": copy.deepcopy(row)}
            )
            counts["kg_edges_removed"] += 1
            seen_removed.add(wanted)
            continue
        retained.append(row)
    if seen_removed not in (set(), set(DOG_EPICETUS_EDGE_HASHES)):
        raise PreconditionsError(f"partial dog/Epictetus edge state: {seen_removed}")
    validate_edges(retained)
    return retained, quarantine, counts


def validate_edges(rows: list[dict[str, Any]]) -> None:
    by_id = {edge_id(row): row for row in rows}
    if set(DOG_EPICETUS_EDGE_HASHES) & by_id.keys():
        raise RuntimeError("false dog/Epictetus primary edge survived")
    for wanted, expected in SORABJI_2017_ADVANCED_IN_HASHES.items():
        if wanted not in by_id or canonical_hash(by_id[wanted]) != expected:
            raise RuntimeError(f"Sorabji 2017 evidence edge changed: {wanted}")
    triples = Counter(
        (str(row.get("source")), str(row.get("relation")), str(row.get("target")))
        for row in rows
    )
    if any(count > 1 for count in triples.values()):
        raise RuntimeError("duplicate edge triple after Sorabji transform")


def move_ocr_review(patch: dict[str, Any]) -> None:
    keys = (
        "verified_against_ocr_version",
        "verification_confidence",
        "verified_at",
        "verified_by",
    )
    if "legacy_ocr_review" in patch:
        if any(key in patch for key in keys):
            raise PreconditionsError("partial e2 OCR-review migration")
        return
    patch["legacy_ocr_review"] = {key: patch.pop(key) for key in keys}


def e2_before_summary(payload: dict[str, Any]) -> dict[str, Any]:
    patches = payload.get("patches") or {}
    return {
        "record_type": "e2_patch_before_summary",
        "path": "data/kg/e2_patches/sorabji.json",
        "file_sha256": E2_BEFORE_SHA256,
        "canonical_json_sha256": canonical_hash(payload),
        "pdfs_consulted": payload.get("pdfs_consulted"),
        "pdf_quality_note_2026_05_19": payload.get("pdf_quality_note_2026_05_19"),
        "changed_patch_hashes": {
            key: canonical_hash(value)
            for key, value in patches.items()
            if key in E2_PAGE_SCOPES
        },
        "changed_non_quote_fields": {
            "eight_context": (
                patches.get(
                    "new_2026_05_19_stoic_eight_attempts_to_retreat_from_necessity",
                    {},
                ).get("context")
            ),
            "cicero_publication_id": patches.get(
                "scholarly_argument_sorabji_cicero_on_free_will_vs_fate_4", {}
            ).get("publication_id"),
            "cicero_wiring_recommendation": patches.get(
                "scholarly_argument_sorabji_cicero_on_free_will_vs_fate_4", {}
            ).get("wiring_recommendation"),
        },
        "copyright_note": (
            "Legacy quote text is not duplicated into quarantine; the file hash and "
            "per-patch hashes preserve the reviewed before-image."
        ),
    }


def transform_e2(
    payload: dict[str, Any], *, current_file_sha256: str
) -> tuple[dict[str, Any], list[dict[str, Any]], Counter[str]]:
    payload = copy.deepcopy(payload)
    if payload.get(STAMP) is True:
        if current_file_sha256 != E2_AFTER_SHA256:
            raise PreconditionsError("applied e2 Sorabji file drift")
        validate_e2(payload)
        return payload, [], Counter()
    if current_file_sha256 != E2_BEFORE_SHA256:
        raise PreconditionsError(
            f"e2 patch drift: expected {E2_BEFORE_SHA256}, actual {current_file_sha256}"
        )
    before = e2_before_summary(payload)
    consulted = [
        value
        for value in payload.get("pdfs_consulted", [])
        if "sorabji_1980_necessity_cause_blame.pdf" not in value
    ]
    payload["pdfs_consulted"] = [
        (
            f"{SCAN_RELATIVE} (source scan; SHA-256 {SCAN_SHA256}; MD5 {SCAN_MD5}; "
            "35,334,906 bytes; 344 PDF pages; visual authority)"
        ),
        (
            f"{OCR_RELATIVE} (OCR derivative; SHA-256 {OCR_SHA256}; MD5 {OCR_MD5}; "
            "79,185,903 bytes; 344 PDF pages; navigation only)"
        ),
        *consulted,
    ]
    payload["source_artifacts"] = {
        "source_scan": {
            "locator": SCAN_RELATIVE,
            "sha256": SCAN_SHA256,
            "md5": SCAN_MD5,
            "byte_size": SCAN_BYTES,
            "role": "visual_authority",
        },
        "ocr_derivative": {
            "locator": OCR_RELATIVE,
            "sha256": OCR_SHA256,
            "md5": OCR_MD5,
            "byte_size": OCR_BYTES,
            "role": "navigation_only",
        },
    }
    payload["page_map"] = {
        "rule": "pdf_page = printed_page + 17",
        "printed_range": "3-326",
        "status": "visually_verified",
        "implicit_folio_caveat": (
            "printed 1-2 and suppressed front-matter folios are inferred from sequence"
        ),
    }
    payload["runtime_exposure"] = "internal_audit_only"
    payload["reuse_status"] = "unverified_do_not_republish"
    payload["legacy_quotes_status"] = "retained_in_place_not_duplicated"
    payload["independent_review"] = {
        "artifact": INDEPENDENT_REVIEW_RELATIVE,
        "sha256": INDEPENDENT_REVIEW_SHA256,
        "verdict": "fail_no_apply",
        "status": "candidate_re_review_required_after_blocker_corrections",
    }
    payload["pdf_quality_note_2026_05_19"] = (
        "The OCR derivative is machine-readable but is not visual authority. The "
        "source scan was independently rendered and page-mapped on 2026-08-24. "
        "Greek OCR and extracted duplication remain unreliable."
    )
    for key, scope in E2_PAGE_SCOPES.items():
        patch = payload["patches"][key]
        move_ocr_review(patch)
        patch["pdf_source"] = SCAN_RELATIVE
        patch["ocr_derivative"] = OCR_RELATIVE
        patch["current_review"] = {
            **scope,
            "page_map_status": "visually_verified",
            "scan_sha256": SCAN_SHA256,
            "status": (
                "initial_visual_source_checked_independent_review_failed_"
                "candidate_re_review_required"
            ),
            "verification_scope": (
                "Sorabji's secondary text only; no ancient primary text or consensus"
            ),
        }
    eight = payload["patches"][
        "new_2026_05_19_stoic_eight_attempts_to_retreat_from_necessity"
    ]
    eight["strategy_order"] = EIGHT_STRATEGIES
    eight["context"] = (
        "Sorabji distinguishes the eight strategies in the stored order and concludes "
        "that the Stoic attempts do not escape commitment to necessity."
    )
    cylinder = payload["patches"][
        "new_2026_05_19_chrysippus_dog_cylinder_three_interpretations"
    ]
    cylinder["attributed_readings"] = cylinder_readings()
    cylinder["context"] = (
        "Sorabji distinguishes Augustine, Donini and Frede readings; he does not "
        "collapse them into one established Chrysippean doctrine and concludes that "
        "the eight retreats fail to escape necessity."
    )
    cicero = payload["patches"][
        "scholarly_argument_sorabji_cicero_on_free_will_vs_fate_4"
    ]
    cicero["publication_id"] = (
        "scholarly_work_sorabji_2017_freedom_and_will_graeco_roman_origins"
    )
    cicero["background_publication_id"] = PUB_ID
    cicero["evidence_scopes"] = {
        "sorabji_1980": {
            "role": "Stoic-necessity and Lucretian-swerve background only",
            "printed_pages": "18; 78-82; 86",
            "pdf_pages": "35; 95-99; 103",
            "visual_status": "checked_2026_08_24",
        },
        "sorabji_2017": {
            "role": "source of the explicit Cicero-echoes-Lucretius formulation",
            "review_status": "legacy_source_not_rechecked_in_this_wave",
        },
    }
    cicero.pop("needs_evidence_should_be_cleared", None)
    cicero["wiring_recommendation"] = (
        "Keep the KG argument advanced_in Sorabji 2017. Treat Sorabji 1980 only "
        "as separately page-mapped background evidence."
    )
    cicero["current_review"]["status"] = (
        "mixed_work_record_split_1980_background_checked_2017_claim_not_rechecked"
    )
    payload["summary"]["method"] = (
        "Legacy OCR search was retained as navigation history. The 2026-08-24 "
        "review used rendered source-scan pages, preserved source/OCR fingerprints, "
        "and did not treat OCR or long legacy quotations as visual authority."
    )
    payload[STAMP] = True
    payload["current_status"] = (
        "independent_review_failed_no_apply_candidate_re_review_required"
    )
    validate_e2(payload)
    return payload, [before], Counter({"e2_patch_modified": 1})


def validate_e2(payload: dict[str, Any]) -> None:
    if payload.get(STAMP) is not True:
        raise RuntimeError("e2 Sorabji repair stamp missing")
    artifacts = payload.get("source_artifacts") or {}
    if artifacts.get("source_scan", {}).get("sha256") != SCAN_SHA256:
        raise RuntimeError("e2 source scan hash is wrong")
    if artifacts.get("ocr_derivative", {}).get("sha256") != OCR_SHA256:
        raise RuntimeError("e2 OCR derivative hash is wrong")
    eight = payload["patches"][
        "new_2026_05_19_stoic_eight_attempts_to_retreat_from_necessity"
    ]
    validate_eight_strategies(EIGHT_STRATEGIES)
    if eight.get("strategy_order") != EIGHT_STRATEGIES:
        raise RuntimeError("e2 eight-strategy order is wrong")
    if payload.get("runtime_exposure") != "internal_audit_only":
        raise RuntimeError("e2 patch is not explicitly internal-only")
    if payload.get("reuse_status") != "unverified_do_not_republish":
        raise RuntimeError("e2 patch lacks a do-not-republish status")
    if payload.get("legacy_quotes_status") != "retained_in_place_not_duplicated":
        raise RuntimeError("e2 legacy quote handling is not explicit")
    independent = payload.get("independent_review") or {}
    if independent.get("verdict") != "fail_no_apply":
        raise RuntimeError("e2 independent FAIL report is not attached")
    for key in E2_PAGE_SCOPES:
        patch = payload["patches"][key]
        if any(
            field in patch
            for field in (
                "verified_against_ocr_version",
                "verification_confidence",
                "verified_at",
                "verified_by",
            )
        ):
            raise RuntimeError(f"legacy OCR status remains active in {key}")
        if patch.get("current_review", {}).get("scan_sha256") != SCAN_SHA256:
            raise RuntimeError(f"visual current review missing in {key}")
    cicero = payload["patches"][
        "scholarly_argument_sorabji_cicero_on_free_will_vs_fate_4"
    ]
    if cicero.get("publication_id") == PUB_ID:
        raise RuntimeError("1980 and 2017 Sorabji evidence remain conflated")


def scholarly_manifest_row() -> dict[str, Any]:
    return {
        "added_to_archive": "2026-08-24",
        "author": "Richard Sorabji",
        "bibtex_key": "sorabji-1983-necessity-cause-and-blame-cornell-paperbacks",
        "edition_used": (
            "Cornell Paperbacks, Cornell University Press, Ithaca, first paperback "
            "edition 1983; exact printing unknown"
        ),
        "ingestion_scope": (
            "Visually page-mapped priority chapters and seven atomic secondary "
            "evidence units; primary-source recollation and complete-book claim "
            "coverage remain incomplete."
        ),
        "isbn": None,
        "isbn_visible_on_copyright_page": {
            "cloth": "0-8014-1162-9",
            "paper": "0-8014-9244-0",
        },
        "kg_ingestion_batches": ["sorabji_p0_20260824"],
        "kg_ingestion_status": "partial",
        "kg_node_count": None,
        "kg_publication_id": PUB_ID,
        "language_primary": "en",
        "languages_secondary": ["el", "la"],
        "last_updated": "2026-08-24",
        "local_printing_year": None,
        "local_printing_status": "unknown_not_inferred",
        "manifest_schema_version": "2.0.0",
        "notes": (
            "Source scan and OCR derivative are separate. OCR is navigation-only. "
            "Local printing is not inferred."
        ),
        "ocr_engine": "OCRmyPDF 17.4.2 / Tesseract 5.5.2",
        "ocr_extracted_line_count_unreliable": 15_827,
        "ocr_extracted_word_count_unreliable": 166_001,
        "ocr_extraction_caveat": (
            "Counts come from machine extraction that contains duplicated blocks and "
            "Greek OCR errors; they are not authoritative content metrics."
        ),
        "ocr_pdf_md5": OCR_MD5,
        "ocr_pdf_sha256": OCR_SHA256,
        "ocr_pdf_size_bytes": OCR_BYTES,
        "page_count": 344,
        "pdf_md5": SCAN_MD5,
        "pdf_sha256": SCAN_SHA256,
        "pdf_size_bytes": SCAN_BYTES,
        "publication_dir": SOURCE_MANIFEST_DIR,
        "title": "Necessity, Cause and Blame: Perspectives on Aristotle's Theory",
        "year_edition_used": 1983,
        "year_original": 1980,
        STAMP: True,
    }


def transform_scholarly_manifest(
    rows: list[dict[str, Any]], *, current_file_sha256: str
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], Counter[str]]:
    rows = copy.deepcopy(rows)
    matches = [r for r in rows if r.get("publication_dir") == SOURCE_MANIFEST_DIR]
    desired = scholarly_manifest_row()
    if matches:
        if len(matches) != 1 or matches[0] != desired:
            raise PreconditionsError("partial or conflicting Sorabji scholarly manifest")
        return rows, [], Counter()
    if current_file_sha256 != SCHOLARLY_MANIFEST_BEFORE_SHA256:
        raise PreconditionsError("scholarly manifest drift before Sorabji registration")
    rows.append(desired)
    quarantine = [
        {
            "record_type": "scholarly_manifest_absence_before",
            "publication_dir": SOURCE_MANIFEST_DIR,
            "container_sha256": SCHOLARLY_MANIFEST_BEFORE_SHA256,
        }
    ]
    validate_scholarly_manifest(rows)
    return rows, quarantine, Counter({"scholarly_manifest_rows_added": 1})


def validate_scholarly_manifest(rows: list[dict[str, Any]]) -> None:
    from scripts.check_scholarly_sources_manifest import validate

    errors = validate(rows)
    if errors:
        raise RuntimeError(f"scholarly manifest invalid: {errors}")
    row = next(r for r in rows if r.get("publication_dir") == SOURCE_MANIFEST_DIR)
    if "word_count" in row or "line_count" in row:
        raise RuntimeError("OCR counts were presented as authoritative")
    if row.get("kg_ingestion_status") != "partial":
        raise RuntimeError("Sorabji scholarly manifest overstates coverage")
    if row.get("year_original") != 1980 or row.get("year_edition_used") != 1983:
        raise RuntimeError("Sorabji scholarly manifest edition year is wrong")
    if row.get("local_printing_year") is not None or row.get(
        "local_printing_status"
    ) != "unknown_not_inferred":
        raise RuntimeError("Sorabji local printing was inferred")


def transform_source_record(record: dict[str, Any]) -> dict[str, Any]:
    record = copy.deepcopy(record)
    record["canonical_identifiers"] = {
        "kg_publication_id": PUB_ID,
        "cinii_duckworth_ncid": "BA04347273",
        "cinii_cornell_ncid": "BA37345728",
    }
    record["acquisition"] = {
        "status": "archived_verified",
        "manifest_publication_dirs": [SOURCE_MANIFEST_DIR],
        "artifacts": [
            {"locator": SCAN_RELATIVE, "role": "source_file", "sha256": SCAN_SHA256},
            {"locator": OCR_RELATIVE, "role": "ocr", "sha256": OCR_SHA256},
            {"locator": AUDIT_RELATIVE, "role": "audit_report"},
        ],
    }
    record["coverage"] = {
        "state": "partial",
        "kg_node_ids": sorted(TOUCHED_NODE_IDS),
        "basis": (
            "Priority chapters and back matter are visually page-mapped and "
            "atomized. Coverage remains partial pending independent review, "
            "ancient-primary recollation, adversarial review and human signoff."
        ),
        "last_audited": "2026-08-24",
    }
    record["provenance"] = [
        {"locator": AUDIT_RELATIVE, "role": "audit_report"},
        {
            "locator": INDEPENDENT_REVIEW_RELATIVE,
            "role": "audit_report",
            "sha256": INDEPENDENT_REVIEW_SHA256,
        },
        {
            "accessed_at": ACCESSED_AT,
            "locator": CINII_DUCKWORTH,
            "role": "catalog_record",
        },
        {
            "accessed_at": ACCESSED_AT,
            "locator": CINII_CORNELL,
            "role": "catalog_record",
        },
        {
            "accessed_at": ACCESSED_AT,
            "locator": BIBLIOVAULT_CHICAGO,
            "role": "catalog_record",
        },
    ]
    record["notes"] = (
        "Local scan shows Cornell title/copyright and Cornell Paperbacks covers; "
        "first Cornell paperback is stated as 1983, but the local printing is not "
        "inferred. OCR is navigation-only, never visual authority. Artifact "
        "fingerprints (SHA-256/MD5/size) and the visual page map for printed pages "
        "3-326 were checked. That check does not establish publication rights, "
        "exact local printing, ancient primary text, or scholarly consensus."
    )
    return record


def evidence_record(
    evidence_id: str,
    *,
    kind: str,
    claim: str,
    attestation: str,
    printed: tuple[int, int] | None,
    pdf: tuple[int, int],
    targets: list[str],
    witness: str | None = None,
) -> dict[str, Any]:
    locator: dict[str, Any] = {
        "pdf_pages": {"start": pdf[0], "end": pdf[1]},
        "page_map_status": "visually_verified",
    }
    if printed:
        locator["printed_pages"] = {"start": printed[0], "end": printed[1]}
    if witness:
        locator["edition_or_witness"] = witness
    return {
        "record_type": "evidence",
        "evidence_id": evidence_id,
        "source_id": SOURCE_ID,
        "evidence_kind": kind,
        "claim_text": claim,
        "attestation": attestation,
        "claim_status": "in_review",
        "locator": locator,
        "quotation": {"status": "paraphrase_only", "language": "eng"},
        "kg_targets": targets,
        "required_verification": [
            "locus_or_page",
            "semantic_entailment",
            "attribution",
            "independent_review",
            "adversarial_review",
        ],
        "notes": (
            "Secondary-source page evidence only; no ancient primary source, "
            "consensus, or exact quotation is verified."
        ),
    }


def new_evidence_records() -> list[dict[str, Any]]:
    return [
        evidence_record(
            NEW_EVIDENCE_IDS[0],
            kind="bibliographic_fact",
            claim=(
                "The local artifact is Cornell; Duckworth 1980, Cornell 1980 / "
                "first paperback 1983, and Chicago 2006 have distinct publisher "
                "and ISBN data, while the local printing remains unknown."
            ),
            attestation="direct",
            printed=None,
            pdf=(4, 5),
            targets=[PUB_ID],
            witness="Local source scan title/copyright pages and catalog records",
        ),
        evidence_record(
            NEW_EVIDENCE_IDS[1],
            kind="secondary_claim",
            claim=(
                "Sorabji distinguishes eight Stoic retreat strategies in the exact "
                "stored order and concludes that they fail to escape necessity."
            ),
            attestation="reported_interpretation",
            printed=(71, 85),
            pdf=(88, 102),
            targets=[TAXONOMY_ID, STOIC_DEBATE_ID],
        ),
        evidence_record(
            NEW_EVIDENCE_IDS[2],
            kind="secondary_claim",
            claim=(
                "Sorabji distinguishes Augustine, Donini and Frede readings of the "
                "internal/external-cause argument and does not collapse them into "
                "one established Chrysippean doctrine."
            ),
            attestation="reported_interpretation",
            printed=(80, 83),
            pdf=(97, 100),
            targets=[CYLINDER_ARGUMENT_ID, CYLINDER_CONCEPT_ID, TAXONOMY_ID],
        ),
        evidence_record(
            NEW_EVIDENCE_IDS[3],
            kind="secondary_claim",
            claim=(
                "Sorabji argues that effects, explanations and human decisions may "
                "be caused without being necessitated."
            ),
            attestation="direct",
            printed=(26, 32),
            pdf=(43, 49),
            targets=[POSITION_ID],
        ),
        evidence_record(
            NEW_EVIDENCE_IDS[4],
            kind="secondary_claim",
            claim=(
                "Sorabji denies that Aristotle treats internal origin as an "
                "uncaused fresh start and reads voluntary action as not necessary "
                "all along while remaining caused."
            ),
            attestation="reported_interpretation",
            printed=(228, 238),
            pdf=(245, 255),
            targets=[POSITION_ID, "argument_aristotles_voluntary_action_argument_eph_hemin_e5dd9188"],
        ),
    ]


def update_existing_evidence(record: dict[str, Any]) -> dict[str, Any]:
    record = copy.deepcopy(record)
    wanted = record.get("evidence_id")
    if wanted == SEA_EVIDENCE_ID:
        record["claim_text"] = (
            "Sorabji presents the sea-battle discussion as an argument from past "
            "truth, distinguishes ancient rival interpretations, and resists a "
            "deterministic reading of Aristotle."
        )
        record["locator"] = {
            "printed_pages": {"start": 91, "end": 103},
            "pdf_pages": {"start": 108, "end": 120},
            "page_map_status": "visually_verified",
        }
    elif wanted == IGNORANCE_EVIDENCE_ID:
        record["claim_text"] = (
            "Sorabji distinguishes the ignorance/voluntariness analyses of EE II, "
            "NE V and NE III rather than treating them as one harmonized account."
        )
        record["locator"] = {
            "printed_pages": {"start": 272, "end": 275},
            "pdf_pages": {"start": 289, "end": 292},
            "page_map_status": "visually_verified",
        }
    else:
        raise PreconditionsError(f"unexpected existing evidence {wanted}")
    record["claim_status"] = "in_review"
    record["quotation"] = {"status": "paraphrase_only", "language": "eng"}
    record["notes"] = (
        "Visually checked against the source scan; independent and adversarial "
        "review remain pending. No ancient primary claim is verified."
    )
    return record


def new_issue_records() -> list[dict[str, Any]]:
    return [
        {
            "record_type": "issue",
            "issue_id": MANIFESTATION_ISSUE_ID,
            "issue_type": "bibliographic_identity",
            "severity": "high",
            "factual_risk": True,
            "status": "open",
            "summary": (
                "The intellectual publication carried a Chicago 2006 ISBN in a "
                "1980 Duckworth/Cornell record, while legacy provenance conflated "
                "the source scan with its OCR derivative. The attached independent "
                "v2 review remains FAIL-NO APPLY pending a v3 re-review."
            ),
            "affected_ids": [PUB_ID, PERSON_ID, SOURCE_ID, NEW_EVIDENCE_IDS[0]],
            "evidence_artifacts": [
                {"locator": AUDIT_RELATIVE, "role": "audit_report"},
                {
                    "locator": INDEPENDENT_REVIEW_RELATIVE,
                    "role": "audit_report",
                    "sha256": INDEPENDENT_REVIEW_SHA256,
                },
                {"locator": SCAN_RELATIVE, "role": "source_file", "sha256": SCAN_SHA256},
                {
                    "accessed_at": ACCESSED_AT,
                    "locator": CINII_DUCKWORTH,
                    "role": "catalog_record",
                },
                {
                    "accessed_at": ACCESSED_AT,
                    "locator": CINII_CORNELL,
                    "role": "catalog_record",
                },
                {
                    "accessed_at": ACCESSED_AT,
                    "locator": BIBLIOVAULT_CHICAGO,
                    "role": "catalog_record",
                },
            ],
            "resolution_criteria": (
                "Keep Duckworth 1980, Cornell 1980 / first paperback 1983 and "
                "Chicago 2006 metadata distinct; preserve unknown local printing; "
                "pass independent catalog/visual review and human signoff."
            ),
        },
        {
            "record_type": "issue",
            "issue_id": INTERPRETATION_ISSUE_ID,
            "issue_type": "disputed_interpretation",
            "severity": "high",
            "factual_risk": True,
            "status": "open",
            "summary": (
                "Legacy cylinder, causal-taxonomy, Diodorus, clinamen, dog/cart "
                "and composite eph-hemin records flattened disputed reconstructions, "
                "were runtime-citable, or retained active dog/cart assertions. The "
                "candidate repair narrows them, but primary recollation and a new "
                "independent review remain outstanding. The attached independent "
                "v2 verdict remains FAIL-NO APPLY. The E2 JSON is catalogued only "
                "as an internal legacy curation/evidence patch, not as an audit "
                "report or runtime source."
            ),
            "affected_ids": sorted(
                {
                    POSITION_ID,
                    TAXONOMY_ID,
                    CYLINDER_ARGUMENT_ID,
                    CYLINDER_CONCEPT_ID,
                    DOG_ID,
                    MASTER_ID,
                    CLINAMEN_ID,
                    EPH_HEMIN_ID,
                    STOIC_DEBATE_ID,
                    *ALL_SORABJI_EVIDENCE_IDS,
                }
            ),
            "evidence_artifacts": [
                {"locator": AUDIT_RELATIVE, "role": "audit_report"},
                {
                    "locator": INDEPENDENT_REVIEW_RELATIVE,
                    "role": "audit_report",
                    "sha256": INDEPENDENT_REVIEW_SHA256,
                },
                {
                    "locator": "data/kg/e2_patches/sorabji.json",
                    "role": "catalog_record",
                },
                {"locator": TEST_RELATIVE, "role": "test_report"},
            ],
            "resolution_criteria": (
                "Keep secondary interpretations attributed and disputed; recollate "
                "the cited ancient witnesses; pass independent visual review, "
                "adversarial tests and human scholarly signoff before any verified "
                "or consensus status."
            ),
        },
    ]


def primary_review(
    verification_id: str, *, target_type: str, target_id: str, stage: str
) -> dict[str, Any]:
    return {
        "record_type": "verification",
        "verification_id": verification_id,
        "target_type": target_type,
        "target_id": target_id,
        "stage": stage,
        "verifier": {
            "verifier_id": "agent_sorabji_pdf_audit",
            "kind": "agent",
            "independence_group": "visual_source_scan_page_map_20260824",
        },
        "method": (
            "Visual review of rendered source-scan pages, title/copyright, chapter "
            "ranges, bibliography and index; OCR used only for navigation."
        ),
        "checked_locators": [SCAN_RELATIVE, AUDIT_RELATIVE],
        "verdict": "pass",
        "created_at": ACCESSED_AT,
        "artifacts": [{"locator": AUDIT_RELATIVE, "role": "audit_report"}],
        "notes": (
            "Pass is limited to bibliographic/page-map and Sorabji secondary-text "
            "support. It is not independent review, adversarial review, ancient "
            "primary verification, consensus, or human signoff."
        ),
    }


def verification_records() -> list[dict[str, Any]]:
    # A pass record for the bounded page check is impossible unless the stored
    # representation really contains eight separately numbered strategies.
    validate_eight_strategies(EIGHT_STRATEGIES)
    records = [
        primary_review(
            "ver_sorabji_source_visual_identity_20260824",
            target_type="source",
            target_id=SOURCE_ID,
            stage="identity",
        )
    ]
    short = {
        SEA_EVIDENCE_ID: "sea_battle",
        IGNORANCE_EVIDENCE_ID: "ignorance",
        NEW_EVIDENCE_IDS[0]: "manifestations",
        NEW_EVIDENCE_IDS[1]: "eight_retreats",
        NEW_EVIDENCE_IDS[2]: "cylinder_readings",
        NEW_EVIDENCE_IDS[3]: "caused_not_necessitated",
        NEW_EVIDENCE_IDS[4]: "aristotle_action",
    }
    for target_id, suffix in short.items():
        records.append(
            primary_review(
                f"ver_sorabji_{suffix}_primary_20260824",
                target_type="evidence",
                target_id=target_id,
                stage="primary",
            )
        )
    return records


def replace_registry_record(
    rows: list[dict[str, Any]],
    *,
    key: str,
    wanted: str,
    before_hash: str,
    transform: Callable[[dict[str, Any]], dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
    rows = copy.deepcopy(rows)
    matches = [row for row in rows if row.get(key) == wanted]
    if len(matches) != 1:
        raise PreconditionsError(f"expected one registry {key}={wanted}")
    old = matches[0]
    desired = transform(old)
    actual_hash = canonical_hash(old)
    expected_after = REGISTRY_AFTER_HASHES.get(wanted)
    if expected_after is not None and actual_hash == expected_after:
        if old != desired:
            raise PreconditionsError(f"partial registry state for {wanted}")
        return rows, None
    if actual_hash != before_hash:
        raise PreconditionsError(f"registry record drift: {wanted}")
    rows[rows.index(old)] = desired
    return rows, old


def transform_registry(
    sources: list[dict[str, Any]],
    evidence: list[dict[str, Any]],
    issues: list[dict[str, Any]],
    waves: list[dict[str, Any]],
    verifications: list[dict[str, Any]],
) -> tuple[dict[str, list[dict[str, Any]]], list[dict[str, Any]], Counter[str]]:
    sources = copy.deepcopy(sources)
    evidence = copy.deepcopy(evidence)
    issues = copy.deepcopy(issues)
    waves = copy.deepcopy(waves)
    verifications = copy.deepcopy(verifications)
    quarantine: list[dict[str, Any]] = []
    counts: Counter[str] = Counter()
    sources, old = replace_registry_record(
        sources,
        key="source_id",
        wanted=SOURCE_ID,
        before_hash=REGISTRY_BEFORE_HASHES[SOURCE_ID],
        transform=transform_source_record,
    )
    if old:
        quarantine.append({"record_type": "registry_source_before", "record": old})
        counts["registry_sources_modified"] += 1
    for wanted in (SEA_EVIDENCE_ID, IGNORANCE_EVIDENCE_ID):
        evidence, old = replace_registry_record(
            evidence,
            key="evidence_id",
            wanted=wanted,
            before_hash=REGISTRY_BEFORE_HASHES[wanted],
            transform=update_existing_evidence,
        )
        if old:
            quarantine.append(
                {"record_type": "registry_evidence_before", "record": old}
            )
            counts["registry_evidence_modified"] += 1
    by_evidence = {row.get("evidence_id"): row for row in evidence}
    for record in new_evidence_records():
        wanted = record["evidence_id"]
        existing = by_evidence.get(wanted)
        if existing is not None:
            if existing != record:
                raise PreconditionsError(f"conflicting new evidence id: {wanted}")
            continue
        evidence.append(record)
        by_evidence[wanted] = record
        quarantine.append(
            {"record_type": "registry_evidence_absence_before", "evidence_id": wanted}
        )
        counts["registry_evidence_added"] += 1
    by_issue = {row.get("issue_id"): row for row in issues}
    for record in new_issue_records():
        wanted = record["issue_id"]
        existing = by_issue.get(wanted)
        if existing is not None:
            if existing != record:
                raise PreconditionsError(f"conflicting new issue id: {wanted}")
            continue
        issues.append(record)
        by_issue[wanted] = record
        quarantine.append(
            {"record_type": "registry_issue_absence_before", "issue_id": wanted}
        )
        counts["registry_issues_added"] += 1

    def update_wave(record: dict[str, Any]) -> dict[str, Any]:
        record = copy.deepcopy(record)
        for wanted in ALL_SORABJI_EVIDENCE_IDS:
            if wanted not in record["evidence_ids"]:
                record["evidence_ids"].append(wanted)
        for wanted in (MANIFESTATION_ISSUE_ID, INTERPRETATION_ISSUE_ID):
            if wanted not in record["issue_ids"]:
                record["issue_ids"].append(wanted)
            if wanted not in record["blocked_by"]:
                record["blocked_by"].append(wanted)
        criterion = (
            "Sorabji 1980 manifestations, page maps and bounded interpretations "
            "pass independent visual, adversarial and human review without "
            "upgrading ancient primary or consensus status."
        )
        if criterion not in record["exit_criteria"]:
            record["exit_criteria"].append(criterion)
        return record

    waves, old = replace_registry_record(
        waves,
        key="wave_id",
        wanted=WAVE_ID,
        before_hash=REGISTRY_BEFORE_HASHES[WAVE_ID],
        transform=update_wave,
    )
    if old:
        quarantine.append({"record_type": "registry_wave_before", "record": old})
        counts["registry_waves_modified"] += 1
    desired_verifications = verification_records()
    by_verification = {row.get("verification_id"): row for row in verifications}
    for record in desired_verifications:
        wanted = record["verification_id"]
        existing = by_verification.get(wanted)
        if existing is not None:
            if existing != record:
                raise PreconditionsError(f"conflicting verification id: {wanted}")
            continue
        verifications.append(record)
        by_verification[wanted] = record
        quarantine.append(
            {
                "record_type": "registry_verification_absence_before",
                "verification_id": wanted,
            }
        )
        counts["registry_primary_verifications_added"] += 1
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
    source = next(
        row for row in result["sources"] if row.get("source_id") == SOURCE_ID
    )
    if source.get("coverage", {}).get("state") != "partial":
        raise RuntimeError("Sorabji registry coverage is not partial")
    acquisition = source.get("acquisition", {})
    if acquisition.get("status") != "archived_verified":
        raise RuntimeError("Sorabji registry source is not fingerprinted")
    source_notes = str(source.get("notes") or "")
    if "fingerprints (SHA-256/MD5/size)" not in source_notes or (
        "visual page map for printed pages 3-326" not in source_notes
    ):
        raise RuntimeError("Sorabji source lacks typed fingerprint/page-map status")
    evidence = {
        row.get("evidence_id"): row
        for row in result["evidence"]
        if row.get("evidence_id") in ALL_SORABJI_EVIDENCE_IDS
    }
    if set(evidence) != set(ALL_SORABJI_EVIDENCE_IDS):
        raise RuntimeError("Sorabji evidence set is incomplete")
    for wanted, row in evidence.items():
        if row.get("claim_status") != "in_review":
            raise RuntimeError(f"Sorabji evidence falsely closed: {wanted}")
        if row.get("locator", {}).get("page_map_status") != "visually_verified":
            raise RuntimeError(f"Sorabji evidence lacks visual page map: {wanted}")
        if row.get("quotation", {}).get("status") != "paraphrase_only":
            raise RuntimeError(f"Sorabji evidence is not paraphrase-only: {wanted}")
        if "primary_source_verified" in row or "consensus" in row:
            raise RuntimeError(f"Sorabji evidence overstates status: {wanted}")
    issues = {
        row.get("issue_id"): row
        for row in result["issues"]
        if row.get("issue_id") in {MANIFESTATION_ISSUE_ID, INTERPRETATION_ISSUE_ID}
    }
    if set(issues) != {MANIFESTATION_ISSUE_ID, INTERPRETATION_ISSUE_ID}:
        raise RuntimeError("Sorabji issues are missing")
    if any(row.get("status") != "open" for row in issues.values()):
        raise RuntimeError("Sorabji factual issue was falsely closed")
    independent_artifacts = [
        artifact
        for issue in issues.values()
        for artifact in issue.get("evidence_artifacts", [])
        if artifact.get("locator") == INDEPENDENT_REVIEW_RELATIVE
    ]
    if len(independent_artifacts) != 2:
        raise RuntimeError("independent FAIL report is not attached fail-closed")
    interpretation_summary = str(issues[INTERPRETATION_ISSUE_ID].get("summary") or "")
    if "FAIL-NO APPLY" not in interpretation_summary or (
        "internal legacy curation/evidence patch" not in interpretation_summary
    ):
        raise RuntimeError("independent FAIL/E2 curation status is not explicit")
    reviews = [
        row
        for row in result["verifications"]
        if str(row.get("verification_id") or "").startswith("ver_sorabji_")
    ]
    if any(row.get("stage") in {"independent", "adversarial", "human_signoff"} for row in reviews):
        raise RuntimeError("unperformed Sorabji review was invented")
    if len(reviews) != 8:
        raise RuntimeError("expected exactly eight actual primary/identity reviews")
    wave = next(row for row in result["waves"] if row.get("wave_id") == WAVE_ID)
    if not {MANIFESTATION_ISSUE_ID, INTERPRETATION_ISSUE_ID} <= set(
        wave.get("blocked_by", [])
    ):
        raise RuntimeError("Sorabji wave is not blocked by open issues")


def canonical_sorabji_bibtex_block(publication_node: dict[str, Any]) -> str:
    from scripts.export_publications_bibtex import publication_entries_to_bibtex

    rendered = publication_entries_to_bibtex(publication_node)
    expected_ids = [row["manifestation_id"] for row in bibtex_manifestation_records()]
    actual_ids = [manifestation_id for _entry, _missing, manifestation_id in rendered]
    if actual_ids != expected_ids:
        raise RuntimeError("canonical exporter lost a Sorabji manifestation")
    if any(missing for _entry, missing, _manifestation_id in rendered):
        raise RuntimeError("canonical Sorabji BibTeX manifestation lacks required fields")
    return "\n\n".join(entry.rstrip("\n") for entry, _missing, _mid in rendered)


def transform_bib(
    text: str,
    report: dict[str, Any],
    *,
    current_sha256: str,
    report_sha256: str,
    publication_node: dict[str, Any],
    all_nodes: list[dict[str, Any]],
) -> tuple[str, dict[str, Any], list[dict[str, Any]], Counter[str]]:
    from scripts.export_publications_bibtex import (
        bibtex_entry_keys,
        build_companion_report,
    )

    desired = canonical_sorabji_bibtex_block(publication_node)
    already_transformed = desired in text and OLD_BIB_ENTRY not in text
    if already_transformed:
        candidate_text = text
    else:
        if current_sha256 != BIB_BEFORE_SHA256:
            raise PreconditionsError("publications.bib drift before Sorabji repair")
        if text.count(OLD_BIB_ENTRY) != 1:
            raise PreconditionsError("expected one exact Sorabji BibTeX entry")
        candidate_text = text.replace(OLD_BIB_ENTRY, desired)

    desired_report = build_companion_report(
        all_nodes,
        candidate_text,
        generation_mode="sorabji_manifestation_surgical_snapshot_transform",
        baseline_bibtex_sha256=BIB_BEFORE_SHA256,
    )
    candidate_keys = bibtex_entry_keys(candidate_text)
    if desired_report.get("entries_written") != len(candidate_keys) or (
        desired_report.get("entry_keys") != candidate_keys
    ):
        raise RuntimeError("BibTeX companion report does not describe candidate IDs")
    if desired_report.get("bibtex_sha256") != sha256_bytes(
        candidate_text.encode("utf-8")
    ):
        raise RuntimeError("BibTeX companion report hash is stale")

    if already_transformed:
        if report != desired_report:
            raise PreconditionsError("partial Sorabji BibTeX/report state")
        return text, report, [], Counter()
    if current_sha256 != BIB_BEFORE_SHA256:
        raise PreconditionsError("publications.bib drift before Sorabji repair")
    if report_sha256 != BIB_REPORT_BEFORE_SHA256:
        raise PreconditionsError("publications BibTeX companion report drift")
    quarantine = [
        {
            "record_type": "bib_entry_before",
            "bibtex_key": (
                "sorabji-1980-necessity-cause-and-blame-perspectives-on-"
                "aristotle-s-theory"
            ),
            "entry": OLD_BIB_ENTRY,
            "entry_sha256": sha256_bytes(OLD_BIB_ENTRY.encode("utf-8")),
        },
        {
            "record_type": "bibtex_report_before_summary",
            "file_sha256": BIB_REPORT_BEFORE_SHA256,
            "publication_count": report.get("publication_count"),
            "entries_written": report.get("entries_written"),
            "nodes_with_missing_fields": report.get("nodes_with_missing_fields"),
            "missing_ids_sha256": canonical_hash(
                [row.get("node_id") for row in report.get("missing", [])]
            ),
        },
    ]
    return (
        candidate_text,
        desired_report,
        quarantine,
        Counter({"bib_entries_modified": 1, "bibtex_reports_modified": 1}),
    )


def measured_baseline(
    root: Path,
    before_nodes: list[dict[str, Any]],
    before_edges: list[dict[str, Any]],
    after_nodes: list[dict[str, Any]],
    after_edges: list[dict[str, Any]],
) -> dict[str, Any]:
    from scripts import check_ingestion_rules
    from scripts.audit_sota_registry import audit_registry

    registry = audit_registry(root / "data/goals/sota", root)

    def debt(nodes: list[dict[str, Any]], edges: list[dict[str, Any]]) -> dict[str, int]:
        check_ingestion_rules.check(nodes, edges, None, None)
        current = list(check_ingestion_rules.violations)
        return {
            "block": sum(1 for row in current if row[1] == check_ingestion_rules.BLOCK),
            "warn": sum(1 for row in current if row[1] == check_ingestion_rules.WARN),
        }

    before_debt = debt(before_nodes, before_edges)
    after_debt = debt(after_nodes, after_edges)
    result = {
        "registry": {
            "structurally_valid": registry.get("structurally_valid"),
            "exit_ready": registry.get("exit_ready"),
            "errors": registry.get("errors", []),
        },
        "strict_ingestion_debt": {
            "before": before_debt,
            "after_preview": after_debt,
            "new_block_debt": max(0, after_debt["block"] - before_debt["block"]),
            "new_warn_debt": max(0, after_debt["warn"] - before_debt["warn"]),
        },
    }
    enforce_measured_baseline(result)
    return result


def enforce_measured_baseline(result: dict[str, Any]) -> None:
    registry = result.get("registry") or {}
    if registry.get("structurally_valid") is not True:
        errors = registry.get("errors") or ["unknown registry structural error"]
        raise PreconditionsError(f"global SOTA registry invalid: {errors}")
    debt = result.get("strict_ingestion_debt") or {}
    if int(debt.get("new_block_debt") or 0) > 0 or int(
        debt.get("new_warn_debt") or 0
    ) > 0:
        raise PreconditionsError(
            "Sorabji preview creates strict ingestion debt: "
            f"block={debt.get('new_block_debt')}, warn={debt.get('new_warn_debt')}"
        )


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
    original_lines = [
        line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()
    ]
    if len(original_lines) != len(before):
        raise PreconditionsError(f"line-count drift while staging {path}")
    desired = {key(row): row for row in after}
    if len(desired) != len(after):
        raise RuntimeError(f"duplicate identity in desired rows for {path}")
    output: list[str] = []
    seen: set[str] = set()
    for line, old in zip(original_lines, before, strict=True):
        wanted = key(old)
        if wanted not in desired:
            continue
        new = desired[wanted]
        output.append(
            line
            if old == new
            else json.dumps(new, ensure_ascii=False, sort_keys=True)
        )
        seen.add(wanted)
    for wanted in sorted(desired.keys() - seen):
        output.append(json.dumps(desired[wanted], ensure_ascii=False, sort_keys=True))
    return ("\n".join(output) + "\n").encode("utf-8")


def build_plan(root: Path = ROOT) -> RepairPlan:
    root = root.resolve()
    nodes_path = root / "data/kg/nodes.jsonl"
    edges_path = root / "data/kg/edges.jsonl"
    bib_path = root / PUBLICATIONS_BIB_RELATIVE
    bib_report_path = root / PUBLICATIONS_BIB_REPORT_RELATIVE
    e2_path = root / "data/kg/e2_patches/sorabji.json"
    manifest_path = root / "data/scholarly_sources/manifest.jsonl"
    sources_path = root / "data/goals/sota/registry/sources/seed_priority_20260824.jsonl"
    evidence_path = root / "data/goals/sota/registry/evidence/seed_priority_20260824.jsonl"
    issues_path = root / "data/goals/sota/registry/issues/seed_known_20260824.jsonl"
    waves_path = root / "data/goals/sota/registry/waves/priority_20260824.jsonl"
    verifications_path = root / "data/goals/sota/registry/verifications/sorabji_20260824.jsonl"

    if sha256_file(root / SCAN_RELATIVE) != SCAN_SHA256:
        raise PreconditionsError("Sorabji source scan hash drift")
    if sha256_file(root / OCR_RELATIVE) != OCR_SHA256:
        raise PreconditionsError("Sorabji OCR derivative hash drift")
    if sha256_file(root / AUDIT_RELATIVE) != AUDIT_SHA256:
        raise PreconditionsError("Sorabji PDF audit hash drift")
    if sha256_file(root / INDEPENDENT_REVIEW_RELATIVE) != INDEPENDENT_REVIEW_SHA256:
        raise PreconditionsError("Sorabji independent FAIL review hash drift")

    before_nodes = read_jsonl(nodes_path)
    before_edges = read_jsonl(edges_path)
    before_manifest = read_jsonl(manifest_path)
    before_sources = read_jsonl(sources_path)
    before_evidence = read_jsonl(evidence_path)
    before_issues = read_jsonl(issues_path)
    before_waves = read_jsonl(waves_path)
    before_verifications = read_jsonl(verifications_path)
    e2_bytes = e2_path.read_bytes()
    bib_bytes = bib_path.read_bytes()
    bib_report_bytes = bib_report_path.read_bytes()

    nodes, node_quarantine, node_counts = transform_nodes(before_nodes)
    edges, edge_quarantine, edge_counts = transform_edges(before_edges)
    e2, e2_quarantine, e2_counts = transform_e2(
        json.loads(e2_bytes), current_file_sha256=sha256_bytes(e2_bytes)
    )
    manifest, manifest_quarantine, manifest_counts = transform_scholarly_manifest(
        before_manifest, current_file_sha256=sha256_file(manifest_path)
    )
    registry, registry_quarantine, registry_counts = transform_registry(
        before_sources,
        before_evidence,
        before_issues,
        before_waves,
        before_verifications,
    )
    transformed_publication = next(row for row in nodes if node_id(row) == PUB_ID)
    bib, bib_report, bib_quarantine, bib_counts = transform_bib(
        bib_bytes.decode("utf-8"),
        json.loads(bib_report_bytes),
        current_sha256=sha256_bytes(bib_bytes),
        report_sha256=sha256_bytes(bib_report_bytes),
        publication_node=transformed_publication,
        all_nodes=nodes,
    )
    counts: Counter[str] = Counter()
    for current in (
        node_counts,
        edge_counts,
        e2_counts,
        manifest_counts,
        registry_counts,
        bib_counts,
    ):
        counts.update(current)
    quarantine = [
        *node_quarantine,
        *edge_quarantine,
        *e2_quarantine,
        *manifest_quarantine,
        *registry_quarantine,
        *bib_quarantine,
    ]
    outputs = {
        nodes_path: serialize_jsonl_preserving(nodes_path, before_nodes, nodes, node_id),
        edges_path: serialize_jsonl_preserving(edges_path, before_edges, edges, edge_id),
        bib_path: bib.encode("utf-8"),
        bib_report_path: (
            json.dumps(bib_report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        ).encode("utf-8"),
        e2_path: (
            json.dumps(e2, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        ).encode("utf-8"),
        manifest_path: serialize_jsonl_preserving(
            manifest_path,
            before_manifest,
            manifest,
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
    changed_paths = [
        str(path.relative_to(root))
        for path, payload in outputs.items()
        if current_bytes[path] != payload
    ]
    summary = {
        "mode": "dry_run",
        "status": "ready_for_independent_re_review_no_apply",
        "write_performed": False,
        "counts": dict(sorted(counts.items())),
        "touched_node_ids": sorted(TOUCHED_NODE_IDS),
        "removed_edge_ids": sorted(DOG_EPICETUS_EDGE_HASHES),
        "citation_rows_modified": 0,
        "corpus_files_modified": 0,
        "changed_paths": changed_paths,
        "quarantine_record_count": len(quarantine),
        "source_artifacts": {
            "scan_sha256": SCAN_SHA256,
            "ocr_sha256": OCR_SHA256,
            "audit_sha256": AUDIT_SHA256,
            "independent_review_sha256": INDEPENDENT_REVIEW_SHA256,
        },
        "before_record_hashes": {
            "nodes": NODE_BEFORE_HASHES,
            "edges_removed": DOG_EPICETUS_EDGE_HASHES,
            "sorabji_2017_edges_immutable": SORABJI_2017_ADVANCED_IN_HASHES,
            "registry": REGISTRY_BEFORE_HASHES,
            "e2_file": E2_BEFORE_SHA256,
            "scholarly_manifest_file": SCHOLARLY_MANIFEST_BEFORE_SHA256,
            "bib_file": BIB_BEFORE_SHA256,
            "bib_report_file": BIB_REPORT_BEFORE_SHA256,
        },
        "after_record_hashes": {
            "nodes": NODE_AFTER_HASHES,
            "registry_modified": REGISTRY_AFTER_HASHES,
            "e2_file": E2_AFTER_SHA256,
        },
        "output_sha256_preview": {
            str(path.relative_to(root)): sha256_bytes(payload)
            for path, payload in outputs.items()
        },
        "open_issue_ids": [MANIFESTATION_ISSUE_ID, INTERPRETATION_ISSUE_ID],
        "review_status": {
            "primary_visual": "recorded",
            "independent": "fail_no_apply_re_review_required",
            "adversarial": "not_performed_not_recorded",
            "human_signoff": "not_performed_not_recorded",
        },
        "bibliography_companion": {
            "baseline_bib_entry_count": sum(
                1
                for line in bib_bytes.decode("utf-8").splitlines()
                if line.startswith("@")
            ),
            "baseline_report_entry_count": json.loads(bib_report_bytes).get(
                "entries_written"
            ),
            "preview_bib_entry_count": bib_report.get("entries_written"),
            "preview_report_entry_count": bib_report.get("entries_written"),
            "preview_publication_node_count": bib_report.get("publication_count"),
            "preview_bibtex_sha256": bib_report.get("bibtex_sha256"),
            "preview_entry_keys_sha256": bib_report.get("entry_keys_sha256"),
            "baseline_entry_count_drift": abs(
                sum(
                    1
                    for line in bib_bytes.decode("utf-8").splitlines()
                    if line.startswith("@")
                )
                - int(json.loads(bib_report_bytes).get("entries_written") or 0)
            ),
            "preview_entry_count_drift": 0,
            "canonical_key_delta_explicit": True,
        },
        "measured_baseline": measured_baseline(
            root, before_nodes, before_edges, nodes, edges
        ),
    }
    if not counts:
        summary["status"] = "already_applied"
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
    drift: list[str] = []
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
    # Keep the durable journal until all private recovery material has gone.
    # If cleanup is interrupted, a committed journal can safely finish cleanup
    # on the next locked invocation without rolling back desired target bytes.
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
        raise PreconditionsError("pending Sorabji transaction requires recovery")
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
        entries: list[dict[str, Any]] = []
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
                    "backup": (
                        f"before/{backup_name}" if original is not None else None
                    ),
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
        # Staging never mutates a target.  Remove only our private material;
        # this is safe even when an injected BaseException models hard failure.
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
                raise RuntimeError(f"missing Sorabji recovery backup: {backup}")
            payload = backup.read_bytes()
            if sha256_bytes(payload) != entry.get("before_sha256"):
                raise RuntimeError(f"corrupt Sorabji recovery backup: {backup}")
            atomic_replace(target, payload)
        else:
            target.unlink(missing_ok=True)
            fsync_directory(target.parent)


def recover_transaction(root: Path) -> str:
    journal_path, backup_dir = journal_paths(root)
    if not journal_path.exists():
        if backup_dir.exists():
            # The committing state is durably journaled before any target
            # replacement, so a journal-less directory is only an orphaned
            # pre-journal stage.
            shutil.rmtree(backup_dir)
            fsync_directory(backup_dir.parent)
            return "orphaned_stage_discarded"
        return "none"
    journal = json.loads(journal_path.read_text(encoding="utf-8"))
    if journal.get("transaction_id") != STAMP:
        raise RuntimeError("foreign transaction journal at Sorabji path")
    if journal.get("state") == "prepared":
        # The durable state transition to ``committing`` precedes every target
        # replacement.  A prepared journal therefore owns only private stage
        # files and must not overwrite any concurrent target change.
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
                raise RuntimeError(f"staged Sorabji payload drift: {staged}")
            replace_path(staged, target)
            targets_replaced = True
            fsync_directory(target.parent)
            journal["committed_targets"].append(entry["target"])
            write_journal(journal_path, journal)
            if fail_after is not None and index >= fail_after:
                raise InjectedTransactionAbort("injected Sorabji hard abort")
        if post_validate:
            post_validate()
        journal["state"] = "committed"
        write_journal(journal_path, journal)
        commit_marked_durable = True
        cleanup_transaction_files(root)
    except BaseException:
        if commit_marked_durable:
            # Desired bytes and the committed journal are authoritative.  Leave
            # recovery material in place for the next locked cleanup attempt.
            raise
        # A pre-commit drift means no target has been replaced. Preserve the
        # concurrent writer's bytes and discard only our private stage.
        if not targets_replaced:
            cleanup_transaction_files(root)
            raise
        current = (
            json.loads(journal_path.read_text(encoding="utf-8"))
            if journal_path.exists()
            else journal
        )
        # CRITICAL: cleanup is deliberately *after* a complete restore.  If any
        # rollback operation fails, the durable journal and before backups must
        # survive so a second locked invocation can recover the transaction.
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
        raise PreconditionsError("refusing to overwrite Sorabji report/quarantine")
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
            raise RuntimeError(f"Sorabji post-write is not idempotent: {followup.counts}")

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
    """Return truthful observability state independently of the planning state."""

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
        raise RuntimeError("successful Sorabji write did not persist its report")
    applied = json.loads(report_path.read_text(encoding="utf-8"))
    if (
        applied.get("mode") != "write"
        or applied.get("status") != "applied_open_issues_pending_review"
        or applied.get("write_performed") is not True
    ):
        raise RuntimeError("persisted Sorabji write report has misleading status")
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
        plan = build_plan(root) if not args.write else None
        if args.write:
            plan = locked_write(root, fail_after=args.inject_failure_after)
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
            print(f"Sorabji repair BLOCKED: {exc}", file=sys.stderr)
        return 2
    assert plan is not None
    result_summary = cli_result_summary(root, plan, write_requested=args.write)
    if args.json:
        # JSON mode is a machine contract: exactly one document on stdout.
        print(json.dumps(result_summary, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print("Sorabji 1980 P0 repair")
        print("mode:", result_summary["mode"].upper())
        print("status:", result_summary["status"])
        for name, count in sorted(result_summary.get("counts", {}).items()):
            print(f"{name}: {count}")
        print("changed paths:", len(result_summary.get("changed_paths", [])))
        for path in result_summary.get("changed_paths", []):
            print(" -", path)
        print(
            "quarantine records:",
            result_summary.get("quarantine_record_count", len(plan.quarantine)),
        )
    if not args.write:
        if not args.json:
            print("dry-run: nothing written; --write requires second root approval")
        return 0
    if not args.json:
        if result_summary["write_performed"]:
            print("write complete; factual issues remain OPEN")
        else:
            print("already applied; no write performed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
