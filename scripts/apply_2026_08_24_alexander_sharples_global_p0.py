#!/usr/bin/env python3
"""Prepare the global Alexander/Sharples P0 repair (dry-run by default).

This wave closes the false *global* closure left by the exact local De fato
12/20 repair.  It never edits corpus passage text or the six Sorabji/Long
overlap nodes.  Strong legacy reconstructions become discovery-only, direct
Alexander text is separated from reported Stoic positions and Sharples's
modern taxonomy, Sharples 1983 receives its own secondary-source identity,
and De fato 8/11 textual defects remain an open debt.

``--write`` is available only after independent review and explicit root
approval.  Dry-run remains the default, and a write against the repository root
requires both ``--write`` and ``--production-write-approved``.
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

STAMP = "alexander_sharples_global_p0_2026_08_24"
UPDATED_AT = "2026-08-24 10:00:00+00:00"
ACCESSED_AT = "2026-08-24T10:00:00Z"

SCRIPT_RELATIVE = "scripts/apply_2026_08_24_alexander_sharples_global_p0.py"
TEST_RELATIVE = "tests/test_alexander_sharples_global_p0.py"
AUDIT_RELATIVE = "docs/academic/2026-08-24-sharples-alexander-on-fate-pdf-audit.md"
PREVIEW_REPORT_RELATIVE = (
    "docs/data-audit/2026-08-24-alexander-sharples-global-p0-preview-v3.md"
)
INDEPENDENT_REVIEW_V2_RELATIVE = (
    "docs/academic/2026-08-24-alexander-sharples-global-p0-independent-review-v2.md"
)
INDEPENDENT_REVIEW_V2_SHA256 = (
    "1dada7cdccd0f4384c21d33dd7cb24969cb9781507d6355aebe448281b1c7f25"
)
REPAIR_REPORT_RELATIVE = "data/audit/2026-08-24_alexander_sharples_global_p0.json"
QUARANTINE_RELATIVE = (
    "data/audit/2026-08-24_alexander_sharples_global_p0_quarantine.jsonl"
)
LOCK_RELATIVE = "data/audit/.alexander_sharples_global_p0.lock"
JOURNAL_RELATIVE = "data/audit/.alexander_sharples_global_p0_transaction.json"
BACKUP_DIR_RELATIVE = "data/audit/.alexander_sharples_global_p0_backups"

SCAN_RELATIVE = "data/literature_acquisition/sharples_1983_alexander_de_fato.pdf"
OCR_RELATIVE = (
    "data/literature_acquisition/sharples_1983_alexander_de_fato_ocr.pdf"
)
SCAN_SHA256 = "7d42b5aba139136d8e32c12ab1c9946471066f95b05a5ce5357a420150810638"
OCR_SHA256 = "ec154e4d3607f887299ac3faf6ec1853b0a4da117eaa464d70331d7c55727ebb"
AUDIT_SHA256 = "7c1fbfcbabb5904c0a35818c5927c8f92913b05feaaf75fe19bbd9ad415efce0"
SCAN_BYTES = 17_913_871
OCR_BYTES = 78_655_916
PDF_PAGES = 161
TEI_RELATIVE = (
    "data/audit/primary_fetch/alexander_of_aphrodisias_"
    "alexander_of_aphrodisias_de_fato/tlg0732.tlg014.1st1K-grc1.xml"
)
TEI_SHA256 = "184b01f38061cfa00b276ed8d9580f3f842f564856851e4bcc124adcc2edbb2f"
BASE_AUDIT_ARTIFACT_SHA256 = {
    "data/audit/2026-08-24_hildebrandt_p0_repair.json": (
        "cb30674aff6f4a6012cbb4a6266b9d1b49138da615c14147837f29820dfec59c"
    ),
    "data/audit/2026-08-24_hildebrandt_p0_quarantine.jsonl": (
        "3f35c44a02a000db342097a274e50a0398b822c363fb13c59ce0a03a1cbb7714"
    ),
    "data/audit/2026-08-24_tatian_p0_repair.json": (
        "b832d77849e1de9a767457afd1cb773609adf58a3d0165d47a9489743f9ee98c"
    ),
    "data/audit/2026-08-24_tatian_p0_quarantine.jsonl": (
        "906013db5a2201252e67e2ff5b13ca88af1419c21c970a1cdddb9c5ad89963c7"
    ),
}

SAFE_AGENT_ID = "argument_agent_causation_alex"
TWO_WAY_ID = "argument_agent_causation_two_way_powers_alexander_q8r9s0t1"
INCOMPAT_ID = "argument_incompatibilism_alexander_p7q8r9s0"
COMMON_CAUSE_ID = "argument_common_cause_alex"
POWER_ID = "argument_power_contraries_alex"
PRAISE_ID = "argument_praise_blame_alex"
REACTIVE_ID = "argument_reactive_attitudes_alex"
MORAL_ID = "argument_moral_assessment_alex"
DELIBERATION_ID = "argument_deliberation_alex"
PROVIDENCE_ID = "argument_providence_freedom_alex"
SAVING_ID = "argument_saving_teaching_alex"
PERFORMATIVE_ID = "argument_performative_contradiction_alex"
WORK_ID = "work_de_fato_alexander_c200ce_o6p7q8r9"
PUBLICATION_ID = "pub_sharples_1983_alexander_fate"
LEGACY_PASSAGE_ID = "passage_alexander_de_fato_15"
LEGACY_PASSAGE_EN_ID = "passage_alexander_de_fato_15_en"
CANONICAL_PASSAGE_15 = "passage_alex_fat_15"

STRONG_ARGUMENT_IDS = frozenset(
    {
        TWO_WAY_ID,
        INCOMPAT_ID,
        COMMON_CAUSE_ID,
        POWER_ID,
        PRAISE_ID,
        REACTIVE_ID,
        MORAL_ID,
        DELIBERATION_ID,
        PROVIDENCE_ID,
        SAVING_ID,
        PERFORMATIVE_ID,
    }
)
TOUCHED_NODE_IDS = frozenset(
    {*STRONG_ARGUMENT_IDS, WORK_ID, PUBLICATION_ID, LEGACY_PASSAGE_ID, LEGACY_PASSAGE_EN_ID}
)
LONG_OVERLAP_NODE_IDS = frozenset(
    {
        "argument_chrysippus_causal_taxonomy",
        "argument_cylinder_analogy_chrysippus_k1l2m3n4",
        "concept_cylinder_analogy_chrysippus_e5f6g7h8",
        "argument_the_dog_and_cart_argument_9ba60714",
        "concept_clinamen_atomic_swerve_epicurus_m3n4o5p6",
        "debate_stoic_compatibilism",
    }
)

ANCIENT_SOURCE_ID = "src_anc_alexander_de_fato"
SECONDARY_SOURCE_ID = "src_sec_sharples_1983_alexander_on_fate"
OLD_LOCAL_ISSUE_ID = "issue_alexander_agent_causation_reconstruction"
GLOBAL_ISSUE_ID = "issue_alexander_global_reconstruction_overclosure_20260824"
TEXT_DEBT_ISSUE_ID = "issue_alexander_de_fato_8_11_text_recollation_20260824"
WAVE_ID = "wave_00b_alexander_sharples_global_followup"
SCHOLARLY_DIR = "sharples1983alexander"

EVIDENCE_IDS = tuple(f"ev_sec_sharples_1983_sha{index:02d}" for index in range(1, 15))

NODE_BEFORE_HASHES = {
    SAFE_AGENT_ID: "57943721410f03c551cc87ccd63d7ac610e1728d37243125429894d70ee203cf",
    TWO_WAY_ID: "8df6d1ff9b6fac3689ade1e231aca993eef8bdbc7896eb342ebddd9f3c7e6982",
    INCOMPAT_ID: "8c08def9534ca890e38a1e514fa34e040e89bb1db21ad8241b5f307f6d8f86aa",
    COMMON_CAUSE_ID: "6c6c6c8719b343b5f143133010f5126e31f320b871bf2247e96c5d40f2079ca2",
    POWER_ID: "a8f576b665cb5a9e88ae4b6fb6565ed841e943d828e8b1b2e67c0a571f65ac0a",
    PRAISE_ID: "d369a929e4b0c3a0a87d571b36681cc63bc1d558682a0da9a506f64dcb54d82d",
    REACTIVE_ID: "3e3e5406018c52527eae3541e259ce0e5ffe462ab5207147e9cc046d71f89e06",
    MORAL_ID: "2c3888cf5c89a74c1e92799e8cced7c6554f3fe6aba881d8b9dbf8d4ff670c08",
    DELIBERATION_ID: "87ab5489ebb92244db1033c3fae77edead13139d5bcb8c0cd5ee404ea4f18504",
    PROVIDENCE_ID: "849ed78556eaa4904a8fd7be388b9b0e8f557ff7aee8a9732cec26db9a107f46",
    SAVING_ID: "d398189bc522ea37591f86e419b07f1f7faa4a3aed1996a40b0466e1afe0f975",
    PERFORMATIVE_ID: "4d2ad99d48a10dc1e82f741ca5fb418ffaeb461f09d63c6b953425eee7a16ee3",
    WORK_ID: "60abcb5d0ec74e98464ed7cb73c690611103d7e68822c8251158bf2f6650124a",
    PUBLICATION_ID: "520e418870b1d758685dc28e08c72d3c37e39d72afa873e212c1d54e87e2d68b",
    LEGACY_PASSAGE_ID: "48572a2b17379a3d3ec3733d0193e9123d12debf06926e807b9bceb213faa399",
    LEGACY_PASSAGE_EN_ID: "3c940f9041b931019fcf37e314d1c4a1d1310813e75725ea6c9a7fc660ed4947",
}

NODE_AFTER_HASHES = {
    TWO_WAY_ID: "3de7a96ed65cf064b36985c1fcb981d663d50a3f482944b4deee9a46d70fe450",
    COMMON_CAUSE_ID: "fedfb8b20af6dd794f9a7973f0c571eb8c4ebabf696fee9340483ab104d00a17",
    DELIBERATION_ID: "eb64af014c87e61bd67a4018af2aab9aed38b0f02bb250d637f5eae7fa60a1fa",
    INCOMPAT_ID: "1cd936f3087a536c20592199215f4c698a39e52b301c5143d4f8dfd0cc24932f",
    MORAL_ID: "5323d7b05724302be1cb9e5f30e2f2125b62746b7307e5989a23fdee48d8bbb7",
    PERFORMATIVE_ID: "ebda888b88ea9fc5b052effbdccc44b4aeebc222660cf8ddc6facac84c35798a",
    POWER_ID: "a8bd671e0ecf370ae87c7ae100f832f85c73537cdbbc4dd7d24ebb87e6bc992d",
    PRAISE_ID: "ca38dfd3f778077045bd6dbd731fea084776ca0d51bebf44b5b763e7c1e89190",
    PROVIDENCE_ID: "2ebf39d8a195e944176a9063620e2d4ac478d4dea51da66eb7e0e0c5d857a8d2",
    REACTIVE_ID: "9baea277731df1d2a08e7f285e41c4e974c657a13bf7fe5bfc4b1b96b5f9741f",
    SAVING_ID: "ac462e7cf764d4f9ea1ea8a60345d2d4e465175373c832a876e968dee1017677",
    LEGACY_PASSAGE_ID: "5a351913c0ddf5723a3e2605528514b581a324a8a2196fe9c81358d07ca76633",
    LEGACY_PASSAGE_EN_ID: "7fab99cb567d894b27c75e030eb097879170bab1ff66466c4e37fa5654d95c3b",
    PUBLICATION_ID: "c6475aa45a507f5301b4868ab3c808a6321218a74e5e843e1d8855994e6a6156",
    WORK_ID: "e905b7fd3851236c4eca6dbe02d22ab69237304d0b2bb010f23d1058101e033b",
}
EDGE_BEFORE_COHORT_SHA256 = "ef35bc8267196b2edc20b683c243a4732b516fe2e08b8d4f0f5cc39c92af4d3b"
EDGE_AFTER_COHORT_SHA256 = "4a1378e7a7ef5cf186cf9081a69edf28605267fd71af6ffd46e2ec1c9d558901"
CITATION_BEFORE_COHORT_SHA256 = "68f2d38c8762209531165fa77f670aa3e41eb3082201945e0000ac9c5846f2d0"
CITATION_AFTER_COHORT_SHA256 = "af39f0bb5e358d1b7203afa280ed9b9a61e9c2e5579d30363622bfb4f6812250"
SCHOLARLY_MANIFEST_BEFORE_SHA256 = "33f304aee1a3882c75f47e212bae778e64c23da6cb9f39cda0790416f0c9e9b6"
BIB_BEFORE_SHA256 = "e4cc9a15bdbe756446518a09f9a97f9405c98a7b54886de39afc07892941c44a"
BIB_REPORT_BEFORE_SHA256 = "7612db557443d1c6c27507a130aa283a115e8a765075b297a7c019ef6104b68a"
CORPUS_PASSAGES_SHA256 = "e8e79f62fb27198f3bfa93755a9f0615ad79e67037eaedd0d61fed5453f176f3"
CORPUS_MANIFEST_SHA256 = "2e2bf033c11ae48af93902be02816a86de9d4c8422cd6800c6f388cab8f5026e"
FROZEN_FILE_BEFORE_SHA256: dict[str, str | None] = {
    "nodes": "60082c52cddfa3e5441a2ae491af2d9c00c386f4f9ed8a8c4b836390a4e24f83",
    "edges": "2e417ac429988f1df282fbb0576f34b51e327479d0043738b9cf073715de6b72",
    "citations": "3aea9ad22b6fe42c78429ce68fbb041c57d532e530463a01b18353d7c11a9c64",
    "passages": CORPUS_PASSAGES_SHA256,
    "corpus_manifest": CORPUS_MANIFEST_SHA256,
    "bib": BIB_BEFORE_SHA256,
    "bib_report": BIB_REPORT_BEFORE_SHA256,
    "scholarly_manifest": SCHOLARLY_MANIFEST_BEFORE_SHA256,
    "registry_sources": "cc34488366f86d56726e99c1113195f2e8c128f2f44f2b1535d0dabdcd8cf7ac",
    "registry_evidence": "90aaa8fab0d4c5fbbb830b60f38d992514b6d5a512a0698397042cc090aa2307",
    "registry_issues": "5dca524033ebe628d5d9cd3431ebeddd9e8830314e430440d057a22e73d8ef17",
    "registry_waves": None,
}
FROZEN_FILE_AFTER_SHA256: dict[str, str | None] = {
    "nodes": "92a0cd13dcab0d1749119e8ef0b772392e7920177096213deca2906e88821817",
    "edges": "b1ce4f5e594d846c0d64ad1a33b4e0b0970230c11641010df8ea9b58e8ebfd2a",
    "citations": "5bd6657adb6aa006bc12a33285c399e00fc7ab467932b603369e119bdc9e089a",
    "passages": CORPUS_PASSAGES_SHA256,
    "corpus_manifest": CORPUS_MANIFEST_SHA256,
    "bib": "3e21f88fe06e9e61d7444f724d66a1eabdadd2af27ec42dca22bd8651e94b825",
    "bib_report": "bba25a9d4d57dd9f82fe1eeb4b410f262312050345fb27fc9fb4b7cce2478e69",
    "scholarly_manifest": "c16553ff02c6cfdcd8402551bcd128fcf8cf0f6d5855a7b38d0be670fbe2a42e",
    "registry_sources": "511a4550dd3d61c36e5fa2b85fb0e0ad66f055141ba5ee4829256b62ea2e7d46",
    "registry_evidence": "165e13fb58e951c76b2efbdcfa17c1938166677af8f60b1d8e2fa5390d84c23c",
    "registry_issues": "188a746de924bf4086ecf66bbd812a332095e7c03e4b6f4d7b72034a93c0c509",
    "registry_waves": "76d3182a9c027e6272e46d6ed9a8c3a1b235e688963e4c05f38c0479ff264405",
}


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
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
            "utf-8"
        )
    ).hexdigest()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def frozen_file_state(paths: dict[str, Path]) -> str:
    actual = {
        label: sha256_file(paths[label]) if paths[label].is_file() else None
        for label in FROZEN_FILE_BEFORE_SHA256
    }
    if actual == FROZEN_FILE_BEFORE_SHA256:
        return "before"
    if actual == FROZEN_FILE_AFTER_SHA256:
        return "after"
    drift = {
        label: {
            "actual": actual[label],
            "before": FROZEN_FILE_BEFORE_SHA256[label],
            "after": FROZEN_FILE_AFTER_SHA256[label],
        }
        for label in actual
        if actual[label]
        not in {
            FROZEN_FILE_BEFORE_SHA256[label],
            FROZEN_FILE_AFTER_SHA256[label],
        }
    }
    raise PreconditionsError(
        "Alexander/Sharples frozen file snapshot drift: "
        + json.dumps(drift, sort_keys=True)
    )


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def node_id(row: dict[str, Any]) -> str:
    return str(row.get("node_id") or row.get("id") or "")


def edge_id(row: dict[str, Any]) -> str:
    return str(row.get("edge_id") or "")


def citation_key(row: dict[str, Any]) -> tuple[str, str, str]:
    return (
        str(row.get("kg_node_id") or ""),
        str(row.get("passage_id") or ""),
        str(row.get("citation_type") or ""),
    )


def metadata(row: dict[str, Any]) -> dict[str, Any]:
    value = row.get("metadata")
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            return {}
    return copy.deepcopy(value) if isinstance(value, dict) else {}


def set_metadata(row: dict[str, Any], data: dict[str, Any]) -> None:
    row["metadata"] = (
        json.dumps(data, ensure_ascii=False, sort_keys=True)
        if isinstance(row.get("metadata"), str)
        else data
    )


def spread_pdf_range(printed: tuple[int, int]) -> tuple[int, int]:
    """Map verified Arabic folios to the scan's double-page PDF spreads."""

    start, end = printed
    if start < 1 or end < start:
        raise PreconditionsError(f"invalid Sharples printed-page interval: {printed}")
    return (start // 2 + 5, end // 2 + 5)


def parse_page_ranges(value: str) -> list[tuple[int, int]]:
    ranges: list[tuple[int, int]] = []
    for component in value.split(";"):
        bounds = [int(item.strip()) for item in component.strip().split("-", 1)]
        ranges.append((bounds[0], bounds[-1]))
    return ranges


def validate_page_maps() -> dict[str, int]:
    evidence_checked = 0
    for evidence_id, spec in zip(EVIDENCE_IDS, EVIDENCE_SPECS, strict=True):
        expected = spread_pdf_range(spec["printed"])
        if spec["pdf"] != expected:
            raise PreconditionsError(
                f"Sharples evidence page-map drift: {evidence_id} "
                f"printed={spec['printed']} pdf={spec['pdf']} expected={expected}"
            )
        evidence_checked += 1
    argument_ranges_checked = 0
    for argument_id, spec in ARGUMENT_SPECS.items():
        printed = parse_page_ranges(spec["printed"])
        pdf = parse_page_ranges(spec["pdf"])
        expected = [spread_pdf_range(interval) for interval in printed]
        if pdf != expected:
            raise PreconditionsError(
                f"Sharples argument page-map drift: {argument_id} "
                f"printed={printed} pdf={pdf} expected={expected}"
            )
        argument_ranges_checked += len(printed)
    return {
        "evidence_intervals_checked": evidence_checked,
        "argument_intervals_checked": argument_ranges_checked,
    }


ARGUMENT_SPECS: dict[str, dict[str, Any]] = {
    TWO_WAY_ID: {
        "description": (
            "Legacy reconstruction, discovery only. Alexander's De fato 12 links "
            "deliberation with control of doing and not doing. Sharples classifies "
            "the broader conception as libertarian, but stresses that Alexander "
            "does not explain how open alternatives combine with rational action. "
            "No text here establishes an undetermined substance-cause, an ultimate "
            "originator, or termination of all prior causal explanation."
        ),
        "loci": ["De fato 12", "De fato 26-29"],
        "printed": "21-22; 57-58; 159-164",
        "pdf": "15-16; 33-34; 84-87",
        "sha_claims": ["SHA-05", "SHA-06", "SHA-13"],
    },
    INCOMPAT_ID: {
        "description": (
            "Modern incompatibilist reconstruction, discovery only. Alexander "
            "argues dialectically against Stoic fate and appeals to responsibility, "
            "deliberation and alternatives. Sharples warns that the Greek debate is "
            "framed by to eph' hemin rather than a ready-made modern free-will "
            "problem, and that Alexander is a partial and hostile Stoic witness."
        ),
        "loci": ["De fato 7-21"],
        "printed": "3-9; 18-22; 150-152",
        "pdf": "6-9; 14-16; 80-81",
        "sha_claims": ["SHA-02", "SHA-03", "SHA-04", "SHA-10"],
    },
    COMMON_CAUSE_ID: {
        "description": (
            "Legacy common-cause reconstruction, discovery only. De fato 22-25 "
            "discusses causal classifications, one cause of several effects and the "
            "Stoic chain. Sharples says this objection does not supply Alexander's "
            "own positive analysis of causation. It therefore does not establish a "
            "self-originating agent or an alternative global causal model."
        ),
        "loci": ["De fato 22-25"],
        "printed": "152-158",
        "pdf": "81-84",
        "sha_claims": ["SHA-12"],
    },
    POWER_ID: {
        "description": (
            "Bounded alternatives claim, discovery only. De fato 12 uses ordinary "
            "control of doing and not doing; Sharples reads Alexander's repeated "
            "power for opposites as unqualified. That modern classification does "
            "not by itself prove same-circumstance undetermined choice or a complete "
            "metaphysics of rational two-way powers."
        ),
        "loci": ["De fato 12", "De fato 26-29"],
        "printed": "21-22; 57-58; 159-164",
        "pdf": "15-16; 33-34; 84-87",
        "sha_claims": ["SHA-05", "SHA-13"],
    },
    DELIBERATION_ID: {
        "description": (
            "Dialectical deliberation cluster, discovery only. De fato 11-12 "
            "appeals to deliberation and what depends on us. Sharples treats the "
            "surrounding argument as polemical and does not infer an ultimate or "
            "uncaused agent. The De fato 11 TEI/OCR artifact remains open and must "
            "be recollated before direct citation."
        ),
        "loci": ["De fato 11-12"],
        "printed": "56-60; 139-143",
        "pdf": "33-35; 74-76",
        "sha_claims": ["SHA-06", "SHA-09"],
    },
    PRAISE_ID: {
        "description": (
            "Praise-and-blame argument cluster, discovery only. Alexander appeals "
            "to ordinary practices in De fato 16-20 and later character arguments. "
            "Sharples classifies these as standard anti-determinist moves whose "
            "force depends on a libertarian premise rejected by Stoic soft "
            "determinism; they are not a direct modern responsibility theory."
        ),
        "loci": ["De fato 16-20", "De fato 26-29"],
        "printed": "64-70; 150-164",
        "pdf": "37-40; 80-87",
        "sha_claims": ["SHA-10", "SHA-13"],
    },
    REACTIVE_ID: {
        "description": (
            "Modern reactive-attitudes comparison, discovery only. Alexander's "
            "polemical appeals to anger, gratitude, praise and blame may be compared "
            "with later analytic debates, but the Strawsonian taxonomy is not his "
            "text. Sharples also warns that Alexander presents Stoicism partially "
            "and assumes the disputed libertarian reading of responsibility."
        ),
        "loci": ["De fato 16", "De fato 26"],
        "printed": "18-22; 150-152; 159-164",
        "pdf": "14-16; 80-81; 84-87",
        "sha_claims": ["SHA-04", "SHA-10", "SHA-13"],
    },
    MORAL_ID: {
        "description": (
            "Moral-assessment reconstruction, discovery only. De fato 19-20 and "
            "26-29 connect assessment with choice and character, but Sharples finds "
            "a regress concerning responsibility for character and no completed "
            "causal explanation. The stronger ultimate-agent conclusion is not "
            "direct Alexander text."
        ),
        "loci": ["De fato 19-20", "De fato 26-29"],
        "printed": "69; 159-164",
        "pdf": "39; 84-87",
        "sha_claims": ["SHA-09", "SHA-13"],
    },
    PROVIDENCE_ID: {
        "description": (
            "Providence and foreknowledge cluster, discovery only. De fato II-VI "
            "presents fate as individual nature, while chapter XXX allows only the "
            "hypothesis that a god knows an agent can choose either way, not the "
            "future choice itself. Sharples identifies unresolved tensions; no "
            "complete providence-freedom harmony is established here."
        ),
        "loci": ["De fato 2-6", "De fato 30"],
        "printed": "23-24; 164-165",
        "pdf": "16-17; 87",
        "sha_claims": ["SHA-07", "SHA-14"],
    },
    SAVING_ID: {
        "description": (
            "Practical-risk argument cluster, discovery only. De fato 16-21 gives "
            "polemical consequences for human practices. Sharples calls chapter XXI "
            "a tour de force comparable to Pascal's wager, not a demonstrated "
            "metaphysical proof. The legacy chapter-39 saving-teaching synthesis is "
            "withdrawn pending exact locus review."
        ),
        "loci": ["De fato 16-21"],
        "printed": "150-152",
        "pdf": "80-81",
        "sha_claims": ["SHA-10", "SHA-11"],
    },
    PERFORMATIVE_ID: {
        "description": (
            "Performative-contradiction reconstruction, discovery only. Alexander "
            "argues that Stoic exhortation and assessment sit uneasily with his "
            "presentation of their doctrine. Sharples treats the practical chapters "
            "as depending on disputed libertarian and fatalistic assumptions, so the "
            "legacy claim is not a knock-down formal refutation."
        ),
        "loci": ["De fato 16-21", "De fato 33-38"],
        "printed": "150-152; 168-173",
        "pdf": "80-81; 89-91",
        "sha_claims": ["SHA-10"],
    },
}


def source_layers(spec: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "claim_role": "direct_alexander_text_candidate",
            "loci": spec["loci"],
            "status": "pending_primary_recollation_in_this_global_wave",
            "scope": (
                "Candidate Alexander loci only; no uncaused, ultimate or "
                "substance-cause thesis is asserted as direct."
            ),
        },
        {
            "claim_role": "reported_stoic_position",
            "status": "hostile_or_partial_report_requires_other_witnesses",
            "scope": "Alexander's Stoic reports are not treated as neutral Stoic doctrine.",
        },
        {
            "claim_role": "sharples_1983_interpretation",
            "publication_id": PUBLICATION_ID,
            "source_id": SECONDARY_SOURCE_ID,
            "printed_pages": spec["printed"],
            "pdf_pages": spec["pdf"],
            "audit_claim_ids": spec["sha_claims"],
            "scan_sha256": SCAN_SHA256,
            "status": "in_review",
        },
        {
            "claim_role": "modern_reconstruction",
            "status": "contested_not_direct_text",
            "excluded_direct_claims": [
                "uncaused choice",
                "ultimate agent or substance-cause",
                "termination of all prior sufficient causes",
                "template for all later agent-causal theories",
            ],
        },
    ]


def transform_strong_argument(row: dict[str, Any]) -> dict[str, Any]:
    row = copy.deepcopy(row)
    wanted = node_id(row)
    spec = ARGUMENT_SPECS[wanted]
    row["label"] = f"Legacy reconstruction (discovery only): {row['label']}"
    row["description"] = spec["description"]
    data = metadata(row)
    legacy_reference = data.pop("verified_reference", None)
    for key in (
        "citation_verified",
        "verified",
        "ancient_attestation_locus_classicus",
        "primary_source",
        "premises",
        "legacy_premises",
        "conclusion",
        "sources",
        "targets",
    ):
        data.pop(key, None)
    data.update(
        {
            STAMP: True,
            "citability": "discoverable_only",
            "needs_evidence": True,
            "citation_verdict": "global_reconstruction_reopened_discovery_only",
            "canonical_claim_node": SAFE_AGENT_ID,
            "claim_layers": source_layers(spec),
            "argument_form": "source_critical_claim_cluster",
            "argument_type": "attributed_layers_pending_primary_recollation",
            "conclusion": {
                "claim_role": "bounded_reconstruction",
                "status": "in_review",
                "text": (
                    "The named loci motivate an anti-determinist reconstruction, "
                    "but do not directly establish an uncaused or ultimate agent."
                ),
                "primary_sources": [],
                "secondary_sources": [PUBLICATION_ID],
            },
            "validity_assessment": {
                "status": "not_assessed_pending_primary_recollation",
                "rationale": (
                    "Sharples treats the work as dialectical and identifies "
                    "unresolved causal and argumentative gaps."
                ),
            },
            "global_issue_id": GLOBAL_ISSUE_ID,
        }
    )
    if legacy_reference:
        data["reference_bundle_pending_recollation"] = {
            "references": legacy_reference,
            "status": "legacy_bundle_not_directly_citable",
        }
    set_metadata(row, data)
    row["updated_at"] = UPDATED_AT
    return row


def transform_work(row: dict[str, Any]) -> dict[str, Any]:
    row = copy.deepcopy(row)
    row["description"] = (
        "Alexander's De fato is a direct authorial treatise whose positive account "
        "of fate as individual nature occupies chapters II-VI; chapters VII-XXXVIII "
        "are largely dialectical objections, reports and replies concerning "
        "determinism, contingency, deliberation and responsibility. Sharples 1983 "
        "uses modern labels such as libertarian while warning that Alexander is a "
        "partial and hostile Stoic witness and does not supply a complete causal "
        "analysis of rational alternatives. Medieval and later reception claims "
        "remain separate bibliographic questions."
    )
    data = metadata(row)
    legacy_reference = data.pop("verified_reference", None)
    data.pop("citation_verified", None)
    data.pop("verified", None)
    editions = [
        item
        for item in data.get("editions", [])
        if str(item.get("editor") or "").lower() != "sharples"
    ]
    data["editions"] = editions
    data["translations_commentaries"] = [
        {
            "publication_id": PUBLICATION_ID,
            "author": "R. W. Sharples",
            "year": 1983,
            "role": (
                "English translation and commentary with photographic facsimile "
                "of Bruns 1892 and separate textual notes"
            ),
            "not_a_new_critical_edition": True,
        }
    ]
    data.update(
        {
            STAMP: True,
            "citability": "discoverable_only",
            "needs_evidence": True,
            "citation_verdict": "global_interpretive_scope_reopened",
            "scope_layers": [
                {"role": "direct_work", "chapters": "I-XXXVIII"},
                {"role": "positive_fate_theory", "chapters": "II-VI"},
                {"role": "dialectical_critique", "chapters": "VII-XXXVIII"},
                {
                    "role": "sharples_modern_taxonomy",
                    "source_id": SECONDARY_SOURCE_ID,
                    "status": "in_review",
                },
            ],
            "global_issue_id": GLOBAL_ISSUE_ID,
        }
    )
    if legacy_reference:
        data["reference_bundle_mixed_pending_scope_review"] = legacy_reference
    set_metadata(row, data)
    row["updated_at"] = UPDATED_AT
    return row


def transform_publication(row: dict[str, Any]) -> dict[str, Any]:
    row = copy.deepcopy(row)
    row["description"] = (
        "R. W. Sharples, Alexander of Aphrodisias on Fate: Text, translation and "
        "commentary (London: Gerald Duckworth & Co. Ltd., 1983). The volume gives "
        "an English translation and commentary, followed by a photographic "
        "facsimile of Bruns's Greek text and separate notes where Sharples prefers "
        "another reading. It is not a newly constituted standard critical edition."
    )
    data = metadata(row)
    legacy_reference = data.pop("verified_reference", None)
    for key in ("citation_verified", "verified", "location"):
        data.pop(key, None)
    data.update(
        {
            STAMP: True,
            "author": "R. W. Sharples",
            "author_id": "scholar_sharples_robert",
            "title": (
                "Alexander of Aphrodisias on Fate: Text, Translation and Commentary"
            ),
            "subtitle": "Text, translation and commentary",
            "year": 1983,
            "type": "book",
            "publisher": "Gerald Duckworth & Co. Ltd.",
            "address": "London",
            "isbn": "0-7156-1589-0 (cased); 0-7156-1739-7 (paper)",
            "isbns_by_binding": {
                "cased": "0-7156-1589-0",
                "paper": "0-7156-1739-7",
            },
            "local_binding_status": "unknown_not_inferred",
            "publication_role": (
                "translation_commentary_with_photographic_bruns_facsimile"
            ),
            "greek_text_basis": (
                "photographic reprint of I. Bruns, Supplementum Aristotelicum "
                "2.1-2; divergent translation readings discussed in textual notes"
            ),
            "page_count": PDF_PAGES,
            "page_map": {
                "rule": "pdf_page = floor(printed_page / 2) + 5",
                "status": "visually_verified_for_arabic_folios",
                "layout": "scanned_spreads_after_cover",
            },
            "rights_status": "all_rights_reserved_internal_verification_only",
            "reuse_status": "unverified_do_not_republish",
            "source_scan_sha256": SCAN_SHA256,
            "ocr_derivative_sha256": OCR_SHA256,
            "citability": "discoverable_only",
            "needs_evidence": True,
            "citation_verdict": "bibliographic_identity_checked_content_in_review",
        }
    )
    if legacy_reference:
        data["reference_bundle_catalog_checked"] = {
            "references": legacy_reference,
            "status": "legacy_wording_corrected_manifestation_identity_checked",
        }
    set_metadata(row, data)
    row["updated_at"] = UPDATED_AT
    return row


def transform_legacy_passage(row: dict[str, Any], *, english: bool) -> dict[str, Any]:
    row = copy.deepcopy(row)
    row["description"] = (
        "Legacy machine-English derivative for De fato 15. It is not a reviewed "
        "translation and is retained only for discovery; use the Bruns/OGL Greek "
        "node passage_alex_fat_15 after source-specific recollation."
        if english
        else (
            "Legacy editorial composite for De fato 15, formerly mixing a short "
            "Greek excerpt, an English rendering and a modern agent-causation "
            "gloss. It is not an exact textual twin. The Bruns/OGL Greek sibling "
            "passage_alex_fat_15 is the candidate primary-text node."
        )
    )
    data = metadata(row)
    for key in (
        "database_verified",
        "translation_verified",
        "ancient_attestation_locus_classicus",
        "verified_reference",
        "cts_urn",
        "passage_id",
        "db_passage_id",
        "corpus_passage_id",
    ):
        data.pop(key, None)
    data.update(
        {
            STAMP: True,
            "citability": "non_citable" if english else "discoverable_only",
            "citation_verdict": "non_exact_legacy_composite",
            "passage_role": "editorial_translation" if english else "editorial_reconstruction",
            "exact_twin_status": "rejected",
            "canonical_candidate_node_id": CANONICAL_PASSAGE_15,
            "related_corpus_passage_id": (
                "3caacfbb-98a9-5207-a691-e24daea16ec1"
                if english
                else "6d9d85c8-ffa3-48f5-b5fe-9ef25cd19aa0"
            ),
            "snapshot_status": "removed_non_exact_duplicate",
            "global_issue_id": GLOBAL_ISSUE_ID,
        }
    )
    if english:
        data["translation_type"] = "machine"
        data["translation_status"] = "unreviewed_do_not_quote"
    set_metadata(row, data)
    row["updated_at"] = UPDATED_AT
    return row


NODE_TRANSFORMS: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {
    **dict.fromkeys(STRONG_ARGUMENT_IDS, transform_strong_argument),
    WORK_ID: transform_work,
    PUBLICATION_ID: transform_publication,
    LEGACY_PASSAGE_ID: lambda row: transform_legacy_passage(row, english=False),
    LEGACY_PASSAGE_EN_ID: lambda row: transform_legacy_passage(row, english=True),
}


def transform_nodes(
    rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], Counter[str]]:
    rows = copy.deepcopy(rows)
    by_id = {node_id(row): row for row in rows}
    if len(by_id) != len(rows):
        raise PreconditionsError("duplicate KG node id")
    if missing := TOUCHED_NODE_IDS - by_id.keys():
        raise PreconditionsError(f"missing Alexander/Sharples nodes: {sorted(missing)}")
    quarantine: list[dict[str, Any]] = []
    counts: Counter[str] = Counter()
    for wanted in sorted(TOUCHED_NODE_IDS):
        current = by_id[wanted]
        data = metadata(current)
        if data.get(STAMP) is True:
            expected = NODE_AFTER_HASHES.get(wanted)
            if expected and canonical_hash(current) != expected:
                raise PreconditionsError(f"applied node drift: {wanted}")
            continue
        expected = NODE_BEFORE_HASHES[wanted]
        if canonical_hash(current) != expected:
            raise PreconditionsError(f"node drift: {wanted}")
        desired = NODE_TRANSFORMS[wanted](current)
        quarantine.append({"record_type": "kg_node_before", "record": current})
        current.clear()
        current.update(desired)
        counts["kg_nodes_modified"] += 1
    validate_nodes(rows)
    return rows, quarantine, counts


def validate_nodes(rows: list[dict[str, Any]]) -> None:
    by_id = {node_id(row): row for row in rows}
    if metadata(by_id[SAFE_AGENT_ID]).get(STAMP) is True:
        raise RuntimeError("local exact 12/20 node was altered by global wave")
    for wanted in TOUCHED_NODE_IDS:
        data = metadata(by_id[wanted])
        if data.get(STAMP) is not True:
            raise RuntimeError(f"missing Alexander/Sharples stamp: {wanted}")
        if "citation_verified" in data or "verified_reference" in data:
            raise RuntimeError(f"active generic verification survives: {wanted}")
    for wanted in STRONG_ARGUMENT_IDS:
        data = metadata(by_id[wanted])
        if data.get("citability") != "discoverable_only":
            raise RuntimeError(f"strong reconstruction remains citable: {wanted}")
        if data.get("premises") or data.get("legacy_premises"):
            raise RuntimeError(f"legacy strong premises survive: {wanted}")
        conclusion = data.get("conclusion") or {}
        if conclusion.get("primary_sources"):
            raise RuntimeError(f"strong reconstruction remains directly grounded: {wanted}")
    publication = metadata(by_id[PUBLICATION_ID])
    if publication.get("publication_role") != (
        "translation_commentary_with_photographic_bruns_facsimile"
    ):
        raise RuntimeError("Sharples publication role remains wrong")
    if "the standard critical edition" in str(
        by_id[PUBLICATION_ID].get("description") or ""
    ).lower():
        raise RuntimeError("Sharples still described as the standard critical edition")
    work_text = str(by_id[WORK_ID].get("description") or "").lower()
    if "definitive ancient defense" in work_text or "must have no sufficient" in work_text:
        raise RuntimeError("De fato work description remains over-assertive")
    if metadata(by_id[LEGACY_PASSAGE_ID]).get("exact_twin_status") != "rejected":
        raise RuntimeError("De fato 15 composite remains an exact twin")


PUBLICATION_WORK_EDGE_ID = "912dc361-a7ed-48c8-a300-fe72c0dc050a"
LEGACY_COMPOSITE_GROUNDING_EDGE_ID = "4391002e-3d23-42ec-bb8f-15cb4a8c2bf7"


def old_support_edge(row: dict[str, Any]) -> bool:
    return (
        str(row.get("relation") or "") in {"cites_primary_source", "source_for"}
        and (str(row.get("source") or "") in STRONG_ARGUMENT_IDS
             or str(row.get("target") or "") in STRONG_ARGUMENT_IDS)
    )


def edge_cohort_digest(rows: list[dict[str, Any]]) -> str:
    return canonical_hash(sorted(rows, key=edge_id))


def transform_edges(
    rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], Counter[str], list[str]]:
    rows = copy.deepcopy(rows)
    ids = {edge_id(row) for row in rows}
    if len(ids) != len(rows):
        raise PreconditionsError("duplicate edge id")
    special = {PUBLICATION_WORK_EDGE_ID, LEGACY_COMPOSITE_GROUNDING_EDGE_ID}
    if PUBLICATION_WORK_EDGE_ID not in ids:
        raise PreconditionsError("missing Sharples/work semantic edge")
    old = [
        row
        for row in rows
        if (old_support_edge(row) or edge_id(row) in special)
        and metadata(row).get(STAMP) is not True
    ]
    applied = [row for row in rows if metadata(row).get(STAMP) is True]
    if old and applied:
        raise PreconditionsError("partial Alexander/Sharples edge state")
    quarantine: list[dict[str, Any]] = []
    counts: Counter[str] = Counter()
    touched: list[str] = []
    if old:
        if len(old) != 56:
            raise PreconditionsError(f"expected 56 Alexander/Sharples edges; found {len(old)}")
        if EDGE_BEFORE_COHORT_SHA256 != "PENDING_LONG_FREEZE" and (
            edge_cohort_digest(old) != EDGE_BEFORE_COHORT_SHA256
        ):
            raise PreconditionsError("Alexander/Sharples edge cohort drift")
        output: list[dict[str, Any]] = []
        for row in rows:
            identifier = edge_id(row)
            if not (old_support_edge(row) or identifier in special):
                output.append(row)
                continue
            if old_support_edge(row) or identifier == LEGACY_COMPOSITE_GROUNDING_EDGE_ID:
                quarantine.append(
                    {"record_type": "kg_edge_removed", "record": copy.deepcopy(row)}
                )
                touched.append(identifier)
                counts["kg_edges_removed"] += 1
                continue
            wanted = copy.deepcopy(row)
            data = metadata(wanted)
            data[STAMP] = True
            if identifier == PUBLICATION_WORK_EDGE_ID:
                data["note"] = (
                    "Sharples supplies an English translation and commentary with "
                    "a photographic Bruns facsimile; not a newly constituted "
                    "critical edition."
                )
                data["evidence_role"] = "secondary_translation_commentary"
            set_metadata(wanted, data)
            output.append(wanted)
            quarantine.append(
                {"record_type": "kg_edge_before", "record": copy.deepcopy(row)}
            )
            touched.append(identifier)
            counts["kg_edges_modified"] += 1
        rows = output
    else:
        if len(applied) != 1:
            raise PreconditionsError(
                f"expected one applied Alexander/Sharples edge; found {len(applied)}"
            )
        if EDGE_AFTER_COHORT_SHA256 != "PENDING_LONG_FREEZE" and (
            edge_cohort_digest(applied) != EDGE_AFTER_COHORT_SHA256
        ):
            raise PreconditionsError("applied Alexander/Sharples edge cohort drift")
    validate_edges(rows)
    return rows, quarantine, counts, sorted(touched or [edge_id(row) for row in applied])


def validate_edges(rows: list[dict[str, Any]]) -> None:
    if any(old_support_edge(row) for row in rows):
        raise RuntimeError("strong reconstruction retains direct primary edge")
    by_id = {edge_id(row): row for row in rows}
    if by_id[PUBLICATION_WORK_EDGE_ID].get("relation") != "interprets":
        raise RuntimeError("Sharples/work relation changed incorrectly")
    if metadata(by_id[PUBLICATION_WORK_EDGE_ID]).get("evidence_role") != (
        "secondary_translation_commentary"
    ):
        raise RuntimeError("Sharples publication edge still claims critical edition")
    if LEGACY_COMPOSITE_GROUNDING_EDGE_ID in by_id:
        raise RuntimeError("legacy De fato 15 composite remains grounding evidence")
    triples = Counter(
        (str(row.get("source")), str(row.get("relation")), str(row.get("target")))
        for row in rows
    )
    if any(value > 1 for value in triples.values()):
        raise RuntimeError("edge transform creates duplicate triples")


def old_strong_citation(row: dict[str, Any]) -> bool:
    return (
        str(row.get("kg_node_id") or "") in STRONG_ARGUMENT_IDS
        and row.get("citation_type") == "source_for"
    )


def legacy_snapshot_citation(row: dict[str, Any]) -> bool:
    return row.get("citation_type") == "snapshot_passage_node" and str(
        row.get("kg_node_id") or ""
    ) in {LEGACY_PASSAGE_ID, LEGACY_PASSAGE_EN_ID}


def citation_cohort_digest(rows: list[dict[str, Any]]) -> str:
    return canonical_hash(sorted(rows, key=citation_key))


def transform_citations(
    rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], Counter[str], list[str]]:
    rows = copy.deepcopy(rows)
    old = [row for row in rows if old_strong_citation(row) or legacy_snapshot_citation(row)]
    applied = [
        row
        for row in rows
        if row.get(STAMP) is True
        and str(row.get("kg_node_id") or "") in STRONG_ARGUMENT_IDS
    ]
    if old and applied:
        raise PreconditionsError("partial Alexander/Sharples citation state")
    quarantine: list[dict[str, Any]] = []
    counts: Counter[str] = Counter()
    touched: list[str] = []
    if old:
        if len(old) != 33:
            raise PreconditionsError(f"expected 33 Alexander citations; found {len(old)}")
        if CITATION_BEFORE_COHORT_SHA256 != "PENDING_LONG_FREEZE" and (
            citation_cohort_digest(old) != CITATION_BEFORE_COHORT_SHA256
        ):
            raise PreconditionsError("Alexander citation cohort drift")
        output: list[dict[str, Any]] = []
        for row in rows:
            key = "|".join(citation_key(row))
            if legacy_snapshot_citation(row):
                quarantine.append(
                    {"record_type": "corpus_citation_removed", "record": copy.deepcopy(row)}
                )
                touched.append(key)
                counts["corpus_citations_removed"] += 1
                continue
            if old_strong_citation(row):
                quarantine.append(
                    {"record_type": "corpus_citation_before", "record": copy.deepcopy(row)}
                )
                wanted = copy.deepcopy(row)
                wanted["previous_citation_type"] = "source_for"
                wanted["citation_type"] = "related_passage_non_exact"
                wanted["confidence"] = min(float(wanted.get("confidence") or 0.5), 0.5)
                wanted["review_status"] = "pending_primary_recollation"
                wanted["global_issue_id"] = GLOBAL_ISSUE_ID
                wanted[STAMP] = True
                output.append(wanted)
                touched.append(key)
                counts["corpus_citations_downgraded"] += 1
                continue
            output.append(row)
        rows = output
    else:
        if len(applied) != 31:
            raise PreconditionsError(
                f"expected 31 applied Alexander citations; found {len(applied)}"
            )
        if any(legacy_snapshot_citation(row) for row in rows):
            raise PreconditionsError("legacy De fato 15 snapshot survived")
        if CITATION_AFTER_COHORT_SHA256 != "PENDING_LONG_FREEZE" and (
            citation_cohort_digest(applied) != CITATION_AFTER_COHORT_SHA256
        ):
            raise PreconditionsError("applied Alexander citation cohort drift")
    validate_citations(rows)
    return (
        rows,
        quarantine,
        counts,
        sorted(touched or ["|".join(citation_key(row)) for row in applied]),
    )


def validate_citations(rows: list[dict[str, Any]]) -> None:
    if any(old_strong_citation(row) for row in rows):
        raise RuntimeError("strong Alexander source_for citation survived")
    if any(legacy_snapshot_citation(row) for row in rows):
        raise RuntimeError("non-exact De fato 15 snapshot survived")
    applied = [
        row
        for row in rows
        if row.get(STAMP) is True
        and str(row.get("kg_node_id") or "") in STRONG_ARGUMENT_IDS
    ]
    if any(row.get("citation_type") != "related_passage_non_exact" for row in applied):
        raise RuntimeError("Alexander citation downgrade is not runtime-safe")


def scholarly_manifest_row() -> dict[str, Any]:
    return {
        "added_to_archive": "2026-08-24",
        "author": "R. W. Sharples",
        "bibtex_key": "sharples-1983-alexander-of-aphrodisias-on-fate",
        "edition_used": (
            "Gerald Duckworth & Co. Ltd., London, 1983; English translation and "
            "commentary with photographic Bruns facsimile and textual notes"
        ),
        "ingestion_scope": (
            "Visually page-mapped identity, complete material structure, fourteen "
            "bounded secondary claims and the named Alexander reconstruction nodes; "
            "not complete-book claim coverage or primary-text replacement."
        ),
        "isbn": None,
        "isbn_visible_by_binding": {
            "cased": "0-7156-1589-0",
            "paper": "0-7156-1739-7",
        },
        "kg_ingestion_batches": ["alexander_sharples_global_p0_20260824"],
        "kg_ingestion_status": "partial",
        "kg_node_count": None,
        "kg_publication_id": PUBLICATION_ID,
        "language_primary": "en",
        "languages_secondary": ["grc"],
        "last_updated": "2026-08-24",
        "local_binding_status": "unknown_not_inferred",
        "manifest_schema_version": "2.0.0",
        "notes": (
            "The Greek pages are a photographic Bruns facsimile, not a new critical "
            "edition. The scan and OCR are internal verification artifacts only."
        ),
        "ocr_engine": "OCRmyPDF/Tesseract; version not established in this audit",
        "ocr_pdf_sha256": OCR_SHA256,
        "ocr_pdf_size_bytes": OCR_BYTES,
        "page_count": PDF_PAGES,
        "page_map": {
            "rule": "pdf_page = floor(printed_page / 2) + 5",
            "layout": "cover followed by scanned two-page spreads",
            "status": "visually_verified_for_arabic_folios",
        },
        "pdf_sha256": SCAN_SHA256,
        "pdf_size_bytes": SCAN_BYTES,
        "publication_dir": SCHOLARLY_DIR,
        "reuse_status": "unverified_do_not_republish",
        "rights": "all_rights_reserved_internal_verification_only",
        "title": "Alexander of Aphrodisias on Fate: Text, Translation and Commentary",
        "year_edition_used": 1983,
        "year_original": 1983,
    }


def transform_scholarly_manifest(
    rows: list[dict[str, Any]], *, current_sha256: str
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], Counter[str]]:
    rows = copy.deepcopy(rows)
    desired = scholarly_manifest_row()
    matches = [row for row in rows if row.get("publication_dir") == SCHOLARLY_DIR]
    if matches:
        if len(matches) != 1 or matches[0] != desired:
            raise PreconditionsError("conflicting Sharples scholarly manifest row")
        return rows, [], Counter()
    if SCHOLARLY_MANIFEST_BEFORE_SHA256 != "PENDING_LONG_FREEZE" and (
        current_sha256 != SCHOLARLY_MANIFEST_BEFORE_SHA256
    ):
        raise PreconditionsError("scholarly manifest drift before Sharples registration")
    rows.append(desired)
    return (
        rows,
        [
            {
                "record_type": "scholarly_manifest_absence_before",
                "publication_dir": SCHOLARLY_DIR,
                "container_sha256": current_sha256,
            }
        ],
        Counter({"scholarly_manifest_rows_added": 1}),
    )


def transform_ancient_source(row: dict[str, Any]) -> dict[str, Any]:
    row = copy.deepcopy(row)
    acquisition = copy.deepcopy(row["acquisition"])
    acquisition["artifacts"] = [
        artifact
        for artifact in acquisition.get("artifacts", [])
        if artifact.get("locator") == TEI_RELATIVE
    ]
    row["acquisition"] = acquisition
    row["coverage"] = {
        "state": "partial",
        "kg_node_ids": [WORK_ID, SAFE_AGENT_ID, "passage_alex_fat_12", "passage_alex_fat_20"],
        "basis": (
            "The direct Bruns/OGL De fato 12/20 cluster remains locally resolved. "
            "Sharples translation/commentary is registered as a distinct secondary "
            "source; other primary loci remain pending recollation."
        ),
        "last_audited": "2026-08-24",
    }
    row["notes"] = (
        "Alexander is the direct authorial transmitter and Bruns/OGL is the Greek "
        "text source. Sharples 1983 is not an artifact of this ancient source and "
        "is registered separately as secondary scholarship."
    )
    return row


def secondary_source_record() -> dict[str, Any]:
    return {
        "record_type": "source",
        "source_id": SECONDARY_SOURCE_ID,
        "source_kind": "secondary_publication",
        "display_label": "R. W. Sharples, Alexander of Aphrodisias on Fate (1983)",
        "canonical_title": (
            "Alexander of Aphrodisias on Fate: Text, Translation and Commentary"
        ),
        "creators": ["R. W. Sharples"],
        "date_display": "1983",
        "languages": ["eng", "grc"],
        "traditions": ["aristotelian_peripatetic"],
        "topics": [
            "fate_necessity",
            "causation",
            "choice_will",
            "moral_responsibility",
            "providence_foreknowledge",
        ],
        "scope_decision": "include_core",
        "identity_status": "bibliography_verified",
        "canonical_identifiers": {
            "kg_publication_id": PUBLICATION_ID,
            "isbn_cased": "0715615890",
            "isbn_paper": "0715617397",
        },
        "acquisition": {
            "status": "archived_verified",
            "manifest_publication_dirs": [SCHOLARLY_DIR],
            "artifacts": [
                {"locator": SCAN_RELATIVE, "role": "source_file", "sha256": SCAN_SHA256},
                {"locator": OCR_RELATIVE, "role": "ocr", "sha256": OCR_SHA256},
            ],
        },
        "coverage": {
            "state": "partial",
            "kg_node_ids": sorted({SAFE_AGENT_ID, *TOUCHED_NODE_IDS}),
            "basis": (
                "Identity, material structure and fourteen bounded interpretive "
                "claims are page-mapped. Ancient-primary recollation, complete-book "
                "atomization and independent/human review remain incomplete."
            ),
            "last_audited": "2026-08-24",
        },
        "provenance": [
            {"locator": AUDIT_RELATIVE, "role": "audit_report"},
            {"locator": SCAN_RELATIVE, "role": "source_file", "sha256": SCAN_SHA256},
        ],
        "notes": (
            "All rights reserved; internal verification only. PDF pages are scanned "
            "spreads; for verified Arabic folios PDF=floor(printed/2)+5. The Greek "
            "section is a photographic Bruns facsimile, not a new critical edition."
        ),
    }


EVIDENCE_SPECS: tuple[dict[str, Any], ...] = (
    {"claim": "Sharples presents De fato as a major surviving treatment of responsibility and determinism and as an important but hostile Stoic witness.", "printed": (19, 21), "pdf": (14, 15), "targets": [WORK_ID]},
    {"claim": "Sharples warns against automatically projecting the modern problem onto Plato or Aristotle and notes ambiguity between irregularity and lack of predetermination.", "printed": (3, 7), "pdf": (6, 8), "targets": [WORK_ID]},
    {"claim": "Sharples says the Greek debate is framed by responsibility, while libertarian and freedom are his modern analytical terms.", "printed": (8, 9), "pdf": (9, 9), "targets": [INCOMPAT_ID, WORK_ID]},
    {"claim": "Sharples treats Alexander as a partial and hostile source for Stoicism whose reports require comparison with other witnesses.", "printed": (18, 21), "pdf": (14, 15), "targets": [INCOMPAT_ID, REACTIVE_ID]},
    {"claim": "Sharples classifies Alexander as libertarian and reads his powers for opposites as unqualified, while noting that Alexander rejects causeless motion.", "printed": (21, 22), "pdf": (15, 16), "targets": [TWO_WAY_ID, POWER_ID, SAFE_AGENT_ID]},
    {"claim": "Sharples judges that Alexander does not solve how libertarian alternatives combine with rational explanation of action.", "printed": (146, 149), "pdf": (78, 79), "targets": [TWO_WAY_ID, DELIBERATION_ID]},
    {"claim": "Sharples distinguishes Alexander's individual-nature fate theory from a doctrine consciously formulated by Aristotle and notes tension in the species-to-individual transition.", "printed": (23, 24), "pdf": (16, 17), "targets": [WORK_ID, PROVIDENCE_ID]},
    {"claim": "Sharples says Alexander's chapter-XIV presentation can neglect or distort Stoic reason and assent and yields a potentially paradoxical responsibility contrast.", "printed": (144, 146), "pdf": (77, 78), "targets": [INCOMPAT_ID]},
    {"claim": "Sharples says calling the agent an origin in chapter XV does not resolve the determinism-versus-causeless-event dilemma or supply the needed causal analysis.", "printed": (146, 149), "pdf": (78, 79), "targets": [SAFE_AGENT_ID, TWO_WAY_ID, MORAL_ID]},
    {"claim": "Sharples judges several practical arguments in chapters XVI-XXI to depend on libertarian and fatalistic assumptions disputed by Stoic soft determinism.", "printed": (150, 152), "pdf": (80, 81), "targets": [PRAISE_ID, REACTIVE_ID, PERFORMATIVE_ID]},
    {"claim": "Sharples calls the chapter-XXI risk argument a tour de force comparable to Pascal's wager rather than an established demonstration.", "printed": (152, 152), "pdf": (81, 81), "targets": [SAVING_ID]},
    {"claim": "Sharples says chapter XXII can bracket causal distinctions for an objection but does not thereby provide Alexander's positive causal model.", "printed": (152, 153), "pdf": (81, 81), "targets": [COMMON_CAUSE_ID]},
    {"claim": "Sharples identifies a regress about responsibility for character in chapters XXVI-XXIX and leaves rational choice, character and alternatives unresolved.", "printed": (159, 164), "pdf": (84, 87), "targets": [TWO_WAY_ID, POWER_ID, MORAL_ID, PRAISE_ID]},
    {"claim": "Sharples reads chapter XXX's hypothetical divine knowledge as knowledge that an agent can choose either way, not knowledge of the actual future choice.", "printed": (164, 165), "pdf": (87, 87), "targets": [PROVIDENCE_ID]},
)


def evidence_records() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for evidence_id, spec in zip(EVIDENCE_IDS, EVIDENCE_SPECS, strict=True):
        rows.append(
            {
                "record_type": "evidence",
                "evidence_id": evidence_id,
                "source_id": SECONDARY_SOURCE_ID,
                "evidence_kind": "secondary_claim",
                "claim_text": spec["claim"],
                "attestation": "reported_interpretation",
                "claim_status": "in_review",
                "locator": {
                    "printed_pages": {"start": spec["printed"][0], "end": spec["printed"][1]},
                    "pdf_pages": {"start": spec["pdf"][0], "end": spec["pdf"][1]},
                    "page_map_status": "visually_verified",
                },
                "quotation": {"status": "paraphrase_only", "language": "eng"},
                "kg_targets": spec["targets"],
                "required_verification": [
                    "locus_or_page",
                    "semantic_entailment",
                    "attribution",
                    "independent_review",
                    "adversarial_review",
                ],
                "notes": (
                    "Copyright-bounded paraphrase only. This is Sharples's modern "
                    "interpretation/taxonomy, not direct Alexander text or consensus."
                ),
            }
        )
    return rows


def global_issue_record() -> dict[str, Any]:
    return {
        "record_type": "issue",
        "issue_id": GLOBAL_ISSUE_ID,
        "issue_type": "unsupported_reconstruction",
        "severity": "critical",
        "factual_risk": True,
        "status": "open",
        "summary": (
            "The locally adjudicated De fato 12/20 repair did not close the global "
            "Alexander cluster: active legacy nodes still asserted undetermined "
            "ultimate agent/substance causation as direct text. This linked issue "
            "keeps the global scope open while preserving the local 12/20 result."
        ),
        "affected_ids": sorted(
            {
                OLD_LOCAL_ISSUE_ID,
                SAFE_AGENT_ID,
                *TOUCHED_NODE_IDS,
                SECONDARY_SOURCE_ID,
                *EVIDENCE_IDS,
            }
        ),
        "evidence_artifacts": [
            {"locator": AUDIT_RELATIVE, "role": "audit_report"},
            {"locator": TEST_RELATIVE, "role": "test_report"},
        ],
        "resolution_criteria": (
            "Keep the 12/20 direct-text result local; make every stronger duplicate "
            "discovery-only, recollate each ancient locus, preserve reported Stoic "
            "and Sharples layers, and obtain independent/adversarial/human review."
        ),
    }


def text_debt_issue_record() -> dict[str, Any]:
    return {
        "record_type": "issue",
        "issue_id": TEXT_DEBT_ISSUE_ID,
        "issue_type": "source_text_divergence",
        "severity": "high",
        "factual_risk": True,
        "status": "open",
        "summary": (
            "De fato 8 and 11 retain observed OCR/TEI artifacts and incomplete "
            "language/role provenance. This wave changes no corpus passage text and "
            "does not promote either locus to exact primary evidence."
        ),
        "affected_ids": [ANCIENT_SOURCE_ID, WORK_ID, "passage_alex_fat_8", "passage_alex_fat_11"],
        "evidence_artifacts": [
            {"locator": AUDIT_RELATIVE, "role": "audit_report"},
            {"locator": TEI_RELATIVE, "role": "tei", "sha256": TEI_SHA256},
        ],
        "resolution_criteria": (
            "Recollate De fato 8 and 11 against the pinned Bruns TEI/facsimile, "
            "repair text only in a separately reviewed corpus wave, and rerun exact "
            "snapshot/parity gates."
        ),
    }


def wave_record() -> dict[str, Any]:
    return {
        "record_type": "wave",
        "wave_id": WAVE_ID,
        "label": "Global Alexander reconstruction and Sharples manifestation follow-up",
        "status": "blocked",
        "score_components": {
            "factual_risk": 1.0,
            "centrality": 0.95,
            "coverage_gap": 0.9,
            "source_readiness": 0.8,
            "controversy_value": 1.0,
        },
        "priority_score": 94.0,
        "source_ids": [ANCIENT_SOURCE_ID, SECONDARY_SOURCE_ID],
        "evidence_ids": list(EVIDENCE_IDS),
        "issue_ids": [GLOBAL_ISSUE_ID, TEXT_DEBT_ISSUE_ID],
        "blocked_by": [GLOBAL_ISSUE_ID, TEXT_DEBT_ISSUE_ID],
        "exit_criteria": [
            "Every strong reconstruction remains attributed and discovery-only.",
            "De fato 8/11 primary text debt is separately recollated without OCR/SAPERE conflation.",
            "Independent, adversarial and human scholarly review remain required.",
        ],
    }


REGISTRY_BEFORE_HASHES = {
    ANCIENT_SOURCE_ID: "5f2fd3b1e2615334f666d315737efad1f3ce1eab409d31ab69808489a3954cd5",
}
REGISTRY_AFTER_HASHES = {
    ANCIENT_SOURCE_ID: "cda97489e7f25ca452cf9d66e2281bfc6ce9ace72c309b18ffa414ad42c83c20",
}


def transform_registry_record(
    rows: list[dict[str, Any]],
    *,
    field: str,
    identifier: str,
    before_hash: str,
    after_hash: str,
    transform: Callable[[dict[str, Any]], dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
    rows = copy.deepcopy(rows)
    matches = [row for row in rows if row.get(field) == identifier]
    if len(matches) != 1:
        raise PreconditionsError(f"expected one registry {field}={identifier}")
    current = matches[0]
    desired = transform(current)
    actual = canonical_hash(current)
    if after_hash != "PENDING_LONG_FREEZE" and actual == after_hash:
        if current != desired:
            raise PreconditionsError(f"partial applied registry record: {identifier}")
        return rows, None
    if before_hash != "PENDING_LONG_FREEZE" and actual != before_hash:
        raise PreconditionsError(f"registry record drift: {identifier}")
    rows[rows.index(current)] = desired
    return rows, current


def add_exact_record(
    rows: list[dict[str, Any]], *, field: str, desired: dict[str, Any]
) -> tuple[bool, str]:
    identifier = str(desired[field])
    matches = [row for row in rows if str(row.get(field) or "") == identifier]
    if not matches:
        rows.append(copy.deepcopy(desired))
        return True, identifier
    if len(matches) != 1 or matches[0] != desired:
        raise PreconditionsError(f"conflicting new registry record: {identifier}")
    return False, identifier


def transform_registry(
    sources: list[dict[str, Any]],
    evidence: list[dict[str, Any]],
    issues: list[dict[str, Any]],
    waves: list[dict[str, Any]],
) -> tuple[dict[str, list[dict[str, Any]]], list[dict[str, Any]], Counter[str]]:
    sources, old_source = transform_registry_record(
        sources,
        field="source_id",
        identifier=ANCIENT_SOURCE_ID,
        before_hash=REGISTRY_BEFORE_HASHES[ANCIENT_SOURCE_ID],
        after_hash=REGISTRY_AFTER_HASHES[ANCIENT_SOURCE_ID],
        transform=transform_ancient_source,
    )
    evidence = copy.deepcopy(evidence)
    issues = copy.deepcopy(issues)
    waves = copy.deepcopy(waves)
    quarantine: list[dict[str, Any]] = []
    counts: Counter[str] = Counter()
    if old_source is not None:
        quarantine.append({"record_type": "registry_source_before", "record": old_source})
        counts["registry_sources_modified"] += 1
    added, identifier = add_exact_record(
        sources, field="source_id", desired=secondary_source_record()
    )
    if added:
        quarantine.append({"record_type": "registry_source_absence_before", "source_id": identifier})
        counts["registry_sources_added"] += 1
    for desired in evidence_records():
        added, identifier = add_exact_record(evidence, field="evidence_id", desired=desired)
        if added:
            quarantine.append({"record_type": "registry_evidence_absence_before", "evidence_id": identifier})
            counts["registry_evidence_added"] += 1
    for desired in (global_issue_record(), text_debt_issue_record()):
        added, identifier = add_exact_record(issues, field="issue_id", desired=desired)
        if added:
            quarantine.append({"record_type": "registry_issue_absence_before", "issue_id": identifier})
            counts["registry_issues_added"] += 1
    added, identifier = add_exact_record(waves, field="wave_id", desired=wave_record())
    if added:
        quarantine.append({"record_type": "registry_wave_absence_before", "wave_id": identifier})
        counts["registry_waves_added"] += 1
    result = {"sources": sources, "evidence": evidence, "issues": issues, "waves": waves}
    validate_registry(result)
    return result, quarantine, counts


def validate_registry(result: dict[str, list[dict[str, Any]]]) -> None:
    source = next(row for row in result["sources"] if row.get("source_id") == SECONDARY_SOURCE_ID)
    if source["coverage"]["state"] != "partial" or source["acquisition"]["status"] != "archived_verified":
        raise RuntimeError("Sharples secondary source overstates acquisition/coverage")
    evidence = {row.get("evidence_id"): row for row in result["evidence"] if row.get("evidence_id") in EVIDENCE_IDS}
    if set(evidence) != set(EVIDENCE_IDS):
        raise RuntimeError("Sharples evidence set is incomplete")
    if any(row.get("claim_status") != "in_review" for row in evidence.values()):
        raise RuntimeError("Sharples evidence was falsely closed")
    issues = {row.get("issue_id"): row for row in result["issues"] if row.get("issue_id") in {GLOBAL_ISSUE_ID, TEXT_DEBT_ISSUE_ID}}
    if set(issues) != {GLOBAL_ISSUE_ID, TEXT_DEBT_ISSUE_ID} or any(row.get("status") != "open" for row in issues.values()):
        raise RuntimeError("Alexander global/text issue is not open")
    wave = next(row for row in result["waves"] if row.get("wave_id") == WAVE_ID)
    if wave.get("status") != "blocked" or set(wave.get("blocked_by", [])) != {GLOBAL_ISSUE_ID, TEXT_DEBT_ISSUE_ID}:
        raise RuntimeError("Alexander follow-up wave is not fail-closed")


OLD_BIB_ENTRY = """@book{sharples-1983-alexander-of-aphrodisias-on-fate,
  author = {R.W. Sharples},
  title = {Alexander of Aphrodisias on Fate},
  year = {1983},
  publisher = {Duckworth},
  note = {EleutherIA KG node: pub_sharples_1983_alexander_fate}
}"""


def canonical_publication_bibtex(publication: dict[str, Any]) -> str:
    from scripts.export_publications_bibtex import publication_entries_to_bibtex

    entries = publication_entries_to_bibtex(publication)
    if len(entries) != 1 or entries[0][1] or entries[0][2] is not None:
        raise RuntimeError("Sharples BibTeX export is not one complete concrete entry")
    return entries[0][0].rstrip("\n")


def transform_bibliography(
    text: str,
    report: dict[str, Any],
    *,
    current_sha256: str,
    report_sha256: str,
    publication: dict[str, Any],
    all_nodes: list[dict[str, Any]],
) -> tuple[str, dict[str, Any], list[dict[str, Any]], Counter[str]]:
    from scripts.export_publications_bibtex import build_companion_report

    desired_entry = canonical_publication_bibtex(publication)
    already = desired_entry in text and OLD_BIB_ENTRY not in text
    if already:
        candidate = text
    else:
        if BIB_BEFORE_SHA256 != "PENDING_LONG_FREEZE" and current_sha256 != BIB_BEFORE_SHA256:
            raise PreconditionsError("publications.bib drift before Sharples repair")
        if text.count(OLD_BIB_ENTRY) != 1:
            raise PreconditionsError("expected one exact legacy Sharples BibTeX entry")
        candidate = text.replace(OLD_BIB_ENTRY, desired_entry)
    desired_report = build_companion_report(
        all_nodes,
        candidate,
        generation_mode="alexander_sharples_global_surgical_snapshot_transform",
        baseline_bibtex_sha256=current_sha256 if not already else BIB_BEFORE_SHA256,
    )
    if desired_report.get("bibtex_sha256") != sha256_bytes(candidate.encode("utf-8")):
        raise RuntimeError("Sharples BibTeX report hash mismatch")
    if already:
        if report != desired_report:
            raise PreconditionsError("partial Sharples BibTeX/report state")
        return text, report, [], Counter()
    if BIB_REPORT_BEFORE_SHA256 != "PENDING_LONG_FREEZE" and report_sha256 != BIB_REPORT_BEFORE_SHA256:
        raise PreconditionsError("BibTeX companion report drift")
    quarantine = [
        {
            "record_type": "bib_entry_before",
            "bibtex_key": "sharples-1983-alexander-of-aphrodisias-on-fate",
            "entry": OLD_BIB_ENTRY,
            "entry_sha256": sha256_bytes(OLD_BIB_ENTRY.encode("utf-8")),
        },
        {
            "record_type": "bibtex_report_before_summary",
            "file_sha256": report_sha256,
            "publication_count": report.get("publication_count"),
            "entries_written": report.get("entries_written"),
            "entry_keys_sha256": report.get("entry_keys_sha256"),
        },
    ]
    return (
        candidate,
        desired_report,
        quarantine,
        Counter({"bib_entries_modified": 1, "bibtex_reports_modified": 1}),
    )


def serialize_jsonl(rows: list[dict[str, Any]]) -> bytes:
    return (
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows)
    ).encode("utf-8")


def serialize_jsonl_preserving(
    path: Path,
    before: list[dict[str, Any]],
    after: list[dict[str, Any]],
    key: Callable[[dict[str, Any]], str],
) -> bytes:
    lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(lines) != len(before):
        raise PreconditionsError(f"line-count drift while serializing {path}")
    desired = {key(row): row for row in after}
    if len(desired) != len(after) or "" in desired:
        raise RuntimeError(f"duplicate/empty desired identity in {path}")
    output: list[str] = []
    seen: set[str] = set()
    for line, old in zip(lines, before, strict=True):
        identifier = key(old)
        wanted = desired.get(identifier)
        if wanted is None:
            continue
        output.append(line if old == wanted else json.dumps(wanted, ensure_ascii=False, sort_keys=True))
        seen.add(identifier)
    for identifier in sorted(desired.keys() - seen):
        output.append(json.dumps(desired[identifier], ensure_ascii=False, sort_keys=True))
    return ("\n".join(output) + "\n").encode("utf-8")


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
        return {
            "block": sum(1 for row in check_ingestion_rules.violations if row[1] == check_ingestion_rules.BLOCK),
            "warn": sum(1 for row in check_ingestion_rules.violations if row[1] == check_ingestion_rules.WARN),
        }

    before = debt(before_nodes, before_edges)
    after = debt(after_nodes, after_edges)
    result = {
        "registry": {
            "structurally_valid": registry.get("structurally_valid"),
            "errors": registry.get("errors", []),
            "exit_ready": registry.get("exit_ready"),
        },
        "strict_ingestion_debt": {
            "before": before,
            "after_preview": after,
            "new_block_debt": max(0, after["block"] - before["block"]),
            "new_warn_debt": max(0, after["warn"] - before["warn"]),
        },
    }
    if result["registry"]["structurally_valid"] is not True:
        raise PreconditionsError(f"global registry invalid: {result['registry']['errors']}")
    if result["strict_ingestion_debt"]["new_block_debt"] or result["strict_ingestion_debt"]["new_warn_debt"]:
        raise PreconditionsError(f"Alexander preview creates ingestion debt: {result}")
    return result


def integrity_gate_report(
    before_nodes: list[dict[str, Any]],
    before_edges: list[dict[str, Any]],
    before_citations: list[dict[str, Any]],
    after_nodes: list[dict[str, Any]],
    after_edges: list[dict[str, Any]],
    after_citations: list[dict[str, Any]],
    passages: list[dict[str, Any]],
    manifest: list[dict[str, Any]],
) -> dict[str, Any]:
    from scripts.check_corpus_invariants import find_violations as corpus_violations
    from scripts.check_kg_corpus_locus_parity import (
        find_violations as parity_violations,
    )
    from scripts.check_kg_work_child_canonical import find_mismatches
    from scripts.check_kg_work_id_uniqueness import collect_work_groups, find_collisions
    from scripts.check_snapshot_passage_integrity import audit_integrity

    before_snapshot = {
        str(row["fingerprint"])
        for row in audit_integrity(before_nodes, passages, before_citations)
    }
    after_snapshot_rows = audit_integrity(after_nodes, passages, after_citations)
    new_snapshot = [
        row
        for row in after_snapshot_rows
        if str(row["fingerprint"]) not in before_snapshot
    ]

    def corpus_keys(
        findings: dict[str, list[dict[str, Any]]],
    ) -> dict[str, set[tuple[str, str, str]]]:
        return {
            category: {
                (
                    str(
                        row.get("node_id")
                        or row.get("id")
                        or row.get("kg_node_id")
                        or ""
                    ),
                    str(row.get("passage_id") or ""),
                    str(row.get("citation_type") or ""),
                )
                for row in rows
            }
            for category, rows in findings.items()
        }

    before_corpus = corpus_keys(
        corpus_violations(before_nodes, passages, before_citations)
    )
    after_corpus = corpus_keys(corpus_violations(after_nodes, passages, after_citations))
    new_corpus = {
        category: sorted(
            after_corpus.get(category, set()) - before_corpus.get(category, set())
        )
        for category in before_corpus.keys() | after_corpus.keys()
        if after_corpus.get(category, set()) - before_corpus.get(category, set())
    }
    parity_shared, parity = parity_violations(
        after_nodes, passages, after_citations
    )
    work_child = find_mismatches(after_nodes, after_edges, manifest)
    work_id = find_collisions(collect_work_groups(after_nodes, after_edges))
    if new_snapshot or new_corpus or parity or work_child or work_id:
        raise PreconditionsError(
            "Alexander prospective corpus/snapshot/parity/work gate failed: "
            + json.dumps(
                {
                    "new_snapshot": new_snapshot,
                    "new_corpus": new_corpus,
                    "parity": parity,
                    "work_child": work_child,
                    "work_id": work_id,
                },
                ensure_ascii=False,
                sort_keys=True,
                default=str,
            )
        )
    return {
        "new_snapshot_fingerprints": 0,
        "new_corpus_violations": 0,
        "parity_shared_checked": parity_shared,
        "parity_violations": 0,
        "work_child_mismatches": 0,
        "work_id_collisions": 0,
    }


def build_plan(root: Path = ROOT) -> RepairPlan:
    root = root.resolve()
    paths = {
        "nodes": root / "data/kg/nodes.jsonl",
        "edges": root / "data/kg/edges.jsonl",
        "citations": root / "data/corpus/citations.jsonl",
        "passages": root / "data/corpus/passages.jsonl",
        "corpus_manifest": root / "data/corpus/manifest.jsonl",
        "bib": root / "data/kg/publications.bib",
        "bib_report": root / "data/kg/publications_bibtex_report.json",
        "scholarly_manifest": root / "data/scholarly_sources/manifest.jsonl",
        "registry_sources": root / "data/goals/sota/registry/sources/seed_priority_20260824.jsonl",
        "registry_evidence": root / "data/goals/sota/registry/evidence/seed_priority_20260824.jsonl",
        "registry_issues": root / "data/goals/sota/registry/issues/seed_known_20260824.jsonl",
        "registry_waves": root / "data/goals/sota/registry/waves/alexander_sharples_20260824.jsonl",
    }
    input_state = frozen_file_state(paths)
    page_map_validation = validate_page_maps()
    if sha256_file(root / SCAN_RELATIVE) != SCAN_SHA256:
        raise PreconditionsError("Sharples source scan hash drift")
    if sha256_file(root / OCR_RELATIVE) != OCR_SHA256:
        raise PreconditionsError("Sharples OCR hash drift")
    if sha256_file(root / AUDIT_RELATIVE) != AUDIT_SHA256:
        raise PreconditionsError("Sharples audit hash drift")
    if sha256_file(root / TEI_RELATIVE) != TEI_SHA256:
        raise PreconditionsError("Bruns/OGL TEI hash drift")
    if sha256_file(root / INDEPENDENT_REVIEW_V2_RELATIVE) != (
        INDEPENDENT_REVIEW_V2_SHA256
    ):
        raise PreconditionsError("Sharples independent semantic review drift")
    for relative, wanted_hash in BASE_AUDIT_ARTIFACT_SHA256.items():
        path = root / relative
        if not path.is_file() or sha256_file(path) != wanted_hash:
            raise PreconditionsError(f"post-Hildebrandt/Tatian base artifact drift: {relative}")

    before_nodes = read_jsonl(paths["nodes"])
    before_edges = read_jsonl(paths["edges"])
    before_citations = read_jsonl(paths["citations"])
    passage_bytes = paths["passages"].read_bytes()
    corpus_manifest_bytes = paths["corpus_manifest"].read_bytes()
    if sha256_bytes(passage_bytes) != CORPUS_PASSAGES_SHA256:
        raise PreconditionsError("Alexander read-only corpus passage dependency drift")
    if sha256_bytes(corpus_manifest_bytes) != CORPUS_MANIFEST_SHA256:
        raise PreconditionsError("Alexander read-only corpus manifest dependency drift")
    passages = read_jsonl(paths["passages"])
    corpus_manifest = read_jsonl(paths["corpus_manifest"])
    before_scholarly = read_jsonl(paths["scholarly_manifest"])
    before_sources = read_jsonl(paths["registry_sources"])
    before_evidence = read_jsonl(paths["registry_evidence"])
    before_issues = read_jsonl(paths["registry_issues"])
    before_waves = read_jsonl(paths["registry_waves"])
    bib_bytes = paths["bib"].read_bytes()
    bib_report_bytes = paths["bib_report"].read_bytes()

    nodes, node_q, node_counts = transform_nodes(before_nodes)
    edges, edge_q, edge_counts, touched_edges = transform_edges(before_edges)
    citations, citation_q, citation_counts, touched_citations = transform_citations(before_citations)
    scholarly, scholarly_q, scholarly_counts = transform_scholarly_manifest(
        before_scholarly, current_sha256=sha256_file(paths["scholarly_manifest"])
    )
    registry, registry_q, registry_counts = transform_registry(
        before_sources, before_evidence, before_issues, before_waves
    )
    publication = next(row for row in nodes if node_id(row) == PUBLICATION_ID)
    bib, bib_report, bib_q, bib_counts = transform_bibliography(
        bib_bytes.decode("utf-8"),
        json.loads(bib_report_bytes),
        current_sha256=sha256_bytes(bib_bytes),
        report_sha256=sha256_bytes(bib_report_bytes),
        publication=publication,
        all_nodes=nodes,
    )
    counts: Counter[str] = Counter()
    for current in (
        node_counts,
        edge_counts,
        citation_counts,
        scholarly_counts,
        registry_counts,
        bib_counts,
    ):
        counts.update(current)
    quarantine = [*node_q, *edge_q, *citation_q, *scholarly_q, *registry_q, *bib_q]

    outputs = {
        paths["nodes"]: serialize_jsonl_preserving(paths["nodes"], before_nodes, nodes, node_id),
        paths["edges"]: serialize_jsonl_preserving(paths["edges"], before_edges, edges, edge_id),
        paths["citations"]: serialize_jsonl_preserving(
            paths["citations"], before_citations, citations, lambda row: "\x1f".join(citation_key(row))
        ),
        paths["bib"]: bib.encode("utf-8"),
        paths["bib_report"]: (
            json.dumps(bib_report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        ).encode("utf-8"),
        paths["scholarly_manifest"]: serialize_jsonl_preserving(
            paths["scholarly_manifest"], before_scholarly, scholarly, lambda row: str(row.get("publication_dir") or "")
        ),
        paths["registry_sources"]: serialize_jsonl_preserving(
            paths["registry_sources"], before_sources, registry["sources"], lambda row: str(row.get("source_id") or "")
        ),
        paths["registry_evidence"]: serialize_jsonl_preserving(
            paths["registry_evidence"], before_evidence, registry["evidence"], lambda row: str(row.get("evidence_id") or "")
        ),
        paths["registry_issues"]: serialize_jsonl_preserving(
            paths["registry_issues"], before_issues, registry["issues"], lambda row: str(row.get("issue_id") or "")
        ),
        paths["registry_waves"]: serialize_jsonl(registry["waves"]),
    }
    before_bytes = {path: path.read_bytes() if path.exists() else None for path in outputs}
    before_bytes.update(
        {
            paths["passages"]: passage_bytes,
            paths["corpus_manifest"]: corpus_manifest_bytes,
        }
    )
    changed_paths = [
        str(path.relative_to(root)) for path, payload in outputs.items() if before_bytes[path] != payload
    ]
    baseline = measured_baseline(root, before_nodes, before_edges, nodes, edges)
    integrity_gates = integrity_gate_report(
        before_nodes,
        before_edges,
        before_citations,
        nodes,
        edges,
        citations,
        passages,
        corpus_manifest,
    )
    summary = {
        "mode": "dry_run",
        "input_state": input_state,
        "status": "ready_for_independent_review_no_apply" if counts else "already_applied",
        "write_performed": False,
        "counts": dict(sorted(counts.items())),
        "changed_paths": changed_paths,
        "touched_node_ids": sorted(TOUCHED_NODE_IDS),
        "untouched_local_exact_node_id": SAFE_AGENT_ID,
        "long_overlap_node_ids_immutable": sorted(LONG_OVERLAP_NODE_IDS),
        "touched_edge_ids": touched_edges,
        "touched_citation_keys": touched_citations,
        "corpus_passage_files_modified": 0,
        "corpus_manifest_files_modified": 0,
        "readonly_snapshot_dependencies": {
            "data/corpus/passages.jsonl": CORPUS_PASSAGES_SHA256,
            "data/corpus/manifest.jsonl": CORPUS_MANIFEST_SHA256,
        },
        "page_map_validation": page_map_validation,
        "quarantine_record_count": len(quarantine),
        "source_artifacts": {
            "scan_sha256": SCAN_SHA256,
            "ocr_sha256": OCR_SHA256,
            "audit_sha256": AUDIT_SHA256,
            "tei_sha256": TEI_SHA256,
            "prior_independent_v2_sha256": INDEPENDENT_REVIEW_V2_SHA256,
            "post_hildebrandt_tatian_base_artifacts": BASE_AUDIT_ARTIFACT_SHA256,
        },
        "before_record_hashes": {
            "nodes": {key: NODE_BEFORE_HASHES[key] for key in sorted(TOUCHED_NODE_IDS)},
            "safe_agent_node": NODE_BEFORE_HASHES[SAFE_AGENT_ID],
            "edge_cohort": EDGE_BEFORE_COHORT_SHA256,
            "citation_cohort": CITATION_BEFORE_COHORT_SHA256,
            "registry": REGISTRY_BEFORE_HASHES,
            "scholarly_manifest_file": SCHOLARLY_MANIFEST_BEFORE_SHA256,
            "bib_file": BIB_BEFORE_SHA256,
            "bib_report_file": BIB_REPORT_BEFORE_SHA256,
            "corpus_passages_file": CORPUS_PASSAGES_SHA256,
            "corpus_manifest_file": CORPUS_MANIFEST_SHA256,
        },
        "after_record_hashes": {
            "nodes": NODE_AFTER_HASHES,
            "edge_cohort": EDGE_AFTER_COHORT_SHA256,
            "citation_cohort": CITATION_AFTER_COHORT_SHA256,
            "registry": REGISTRY_AFTER_HASHES,
        },
        "output_sha256_preview": {
            str(path.relative_to(root)): sha256_bytes(payload) for path, payload in outputs.items()
        },
        "open_issue_ids": [GLOBAL_ISSUE_ID, TEXT_DEBT_ISSUE_ID],
        "reviews": {
            "primary_visual_audit": "recorded_as_input_report",
            "independent": "not_performed_not_recorded",
            "adversarial": "not_performed_not_recorded",
            "human_signoff": "not_performed_not_recorded",
        },
        "measured_baseline": baseline,
        "integrity_gates": integrity_gates,
    }
    return RepairPlan(
        root=root,
        outputs=outputs,
        before_bytes=before_bytes,
        quarantine=quarantine,
        counts=counts,
        summary=summary,
    )


class InjectedTransactionAbort(BaseException):
    """Test-only hard-crash analogue."""


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


def journal_paths(root: Path) -> tuple[Path, Path]:
    return root / JOURNAL_RELATIVE, root / BACKUP_DIR_RELATIVE


def write_journal(path: Path, journal: dict[str, Any]) -> None:
    atomic_replace(
        path,
        (json.dumps(journal, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode(
            "utf-8"
        ),
    )


def snapshot_gate(before: dict[Path, bytes | None], *, label: str) -> None:
    drift = []
    for path, expected in before.items():
        actual = path.read_bytes() if path.exists() else None
        if actual != expected:
            drift.append(str(path))
    if drift:
        raise PreconditionsError(f"{label} snapshot drift: {drift}")


def cleanup_transaction(root: Path) -> None:
    journal_path, backup_dir = journal_paths(root)
    if backup_dir.exists():
        shutil.rmtree(backup_dir)
        fsync_directory(backup_dir.parent)
    journal_path.unlink(missing_ok=True)
    fsync_directory(journal_path.parent)


def prepare_transaction(
    root: Path, outputs: dict[Path, bytes], before: dict[Path, bytes | None]
) -> dict[str, Any]:
    journal_path, backup_dir = journal_paths(root)
    if journal_path.exists() or backup_dir.exists():
        raise PreconditionsError("pending Alexander/Sharples transaction requires recovery")
    snapshot_gate(before, label="pre-stage")
    before_dir = backup_dir / "before"
    stage_dir = backup_dir / "stage"
    try:
        before_dir.mkdir(parents=True)
        stage_dir.mkdir(parents=True)
        fsync_directory(backup_dir.parent)
        fsync_directory(backup_dir)
        fsync_directory(before_dir)
        fsync_directory(stage_dir)
        entries = []
        changed = [path for path, payload in outputs.items() if before[path] != payload]
        for index, path in enumerate(changed):
            original = before[path]
            before_name = f"{index:03d}.before"
            stage_name = f"{index:03d}.after"
            if original is not None:
                write_fsynced(before_dir / before_name, original)
            write_fsynced(stage_dir / stage_name, outputs[path])
            entries.append(
                {
                    "target": str(path.relative_to(root)),
                    "before_exists": original is not None,
                    "before_sha256": sha256_bytes(original) if original is not None else None,
                    "backup": f"before/{before_name}" if original is not None else None,
                    "after_sha256": sha256_bytes(outputs[path]),
                    "stage": f"stage/{stage_name}",
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


def transaction_entry_state(root: Path, entry: dict[str, Any]) -> str:
    target = root / entry["target"]
    current = target.read_bytes() if target.is_file() else None
    before_matches = (
        current is not None
        and sha256_bytes(current) == entry.get("before_sha256")
        if entry.get("before_exists")
        else current is None
    )
    if before_matches:
        return "before"
    if current is not None and sha256_bytes(current) == entry.get("after_sha256"):
        return "after"
    return "foreign"


def restore_from_journal(root: Path, journal: dict[str, Any]) -> None:
    journal_path, backup_dir = journal_paths(root)
    journal["state"] = "rolling_back"
    write_journal(journal_path, journal)
    states = {
        str(entry["target"]): transaction_entry_state(root, entry)
        for entry in journal.get("entries", [])
    }
    foreign = sorted(target for target, state in states.items() if state == "foreign")
    if foreign:
        raise PreconditionsError(
            "refusing to overwrite foreign bytes during Alexander/Sharples rollback: "
            f"{foreign}"
        )
    for entry in reversed(journal.get("entries", [])):
        target = root / entry["target"]
        if states[str(entry["target"])] == "before":
            continue
        if entry.get("before_exists"):
            backup = backup_dir / entry["backup"]
            payload = backup.read_bytes()
            if sha256_bytes(payload) != entry.get("before_sha256"):
                raise RuntimeError(f"corrupt Alexander/Sharples backup: {backup}")
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
            return "orphan_stage_removed"
        return "none"
    journal = json.loads(journal_path.read_text(encoding="utf-8"))
    if journal.get("transaction_id") != STAMP:
        raise RuntimeError("foreign Alexander/Sharples transaction journal")
    entries = journal.get("entries") or []
    before_complete = all(
        (
            (root / entry["target"]).is_file()
            and sha256_file(root / entry["target"]) == entry.get("before_sha256")
        )
        if entry.get("before_exists")
        else not (root / entry["target"]).exists()
        for entry in entries
    )
    after_complete = all(
        (root / entry["target"]).is_file()
        and sha256_file(root / entry["target"]) == entry.get("after_sha256")
        for entry in entries
    )
    state = journal.get("state")
    if state == "prepared":
        if not before_complete:
            raise RuntimeError("prepared transaction touched a target")
        cleanup_transaction(root)
        return "prepared_stage_removed"
    if state == "committed" and after_complete:
        cleanup_transaction(root)
        return "committed_cleanup_finished"
    if state == "committing" and before_complete:
        cleanup_transaction(root)
        return "already_rolled_back"
    if state in {"committing", "rolling_back"}:
        restore_from_journal(root, journal)
        cleanup_transaction(root)
        return "partial_commit_rolled_back"
    raise RuntimeError(f"unknown Alexander/Sharples transaction state: {state!r}")


def transactional_replace(
    root: Path,
    outputs: dict[Path, bytes],
    before: dict[Path, bytes | None],
    *,
    fail_after: int | None = None,
    before_commit_hook: Callable[[], None] | None = None,
    post_validate: Callable[[], None] | None = None,
) -> None:
    journal_path, backup_dir = journal_paths(root)
    journal = prepare_transaction(root, outputs, before)
    targets_replaced = False
    commit_durable = False
    try:
        if before_commit_hook:
            before_commit_hook()
        snapshot_gate(before, label="pre-commit")
        journal["state"] = "committing"
        write_journal(journal_path, journal)
        for index, entry in enumerate(journal["entries"], 1):
            target = root / entry["target"]
            staged = backup_dir / entry["stage"]
            if transaction_entry_state(root, entry) != "before":
                raise PreconditionsError(
                    "Alexander/Sharples target drift immediately before replace: "
                    f"{entry['target']}"
                )
            if sha256_file(staged) != entry["after_sha256"]:
                raise RuntimeError("Alexander/Sharples staged payload drift")
            replace_path(staged, target)
            targets_replaced = True
            fsync_directory(target.parent)
            journal["committed_targets"].append(entry["target"])
            write_journal(journal_path, journal)
            if fail_after is not None and index >= fail_after:
                raise InjectedTransactionAbort("injected hard crash")
        if post_validate:
            post_validate()
        journal["state"] = "committed"
        write_journal(journal_path, journal)
        commit_durable = True
        cleanup_transaction(root)
    except BaseException:
        if commit_durable:
            raise
        if not targets_replaced:
            cleanup_transaction(root)
            raise
        current = json.loads(journal_path.read_text(encoding="utf-8"))
        # Never clean durable recovery material if restoration itself fails.
        restore_from_journal(root, current)
        cleanup_transaction(root)
        raise


def apply_plan(
    plan: RepairPlan,
    *,
    fail_after: int | None = None,
    before_commit_hook: Callable[[], None] | None = None,
) -> None:
    if not plan.counts:
        return
    report_path = plan.root / REPAIR_REPORT_RELATIVE
    quarantine_path = plan.root / QUARANTINE_RELATIVE
    if report_path.exists() or quarantine_path.exists():
        raise PreconditionsError("refusing to overwrite Alexander/Sharples audit artifacts")
    report = copy.deepcopy(plan.summary)
    report.update(
        {
            "mode": "write",
            "status": "applied_open_issues_pending_review",
            "write_performed": True,
        }
    )
    outputs = dict(plan.outputs)
    outputs[report_path] = (
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    outputs[quarantine_path] = serialize_jsonl(plan.quarantine)
    before = dict(plan.before_bytes)
    before[report_path] = None
    before[quarantine_path] = None

    def post_validate() -> None:
        followup = build_plan(plan.root)
        if followup.counts:
            raise RuntimeError(f"post-write is not idempotent: {followup.counts}")
        gates = followup.summary["integrity_gates"]
        if any(
            gates[key]
            for key in (
                "new_snapshot_fingerprints",
                "new_corpus_violations",
                "parity_violations",
                "work_child_mismatches",
                "work_id_collisions",
            )
        ):
            raise RuntimeError(f"post-write integrity gates failed: {gates}")

    transactional_replace(
        plan.root,
        outputs,
        before,
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
    return plan


def cli_summary(root: Path, plan: RepairPlan, *, write_requested: bool) -> dict[str, Any]:
    if not write_requested:
        return copy.deepcopy(plan.summary)
    if not plan.counts:
        result = copy.deepcopy(plan.summary)
        result.update({"mode": "write", "status": "already_applied", "write_performed": False})
        return result
    return json.loads((root / REPAIR_REPORT_RELATIVE).read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--write",
        action="store_true",
        help="apply the reviewed local transaction (repository root also requires approval)",
    )
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument(
        "--production-write-approved",
        action="store_true",
        help="explicit root authorization required for a repository-data write",
    )
    parser.add_argument("--inject-failure-after", type=int, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    root = args.root.expanduser().resolve()
    if args.write and root == ROOT.resolve() and not args.production_write_approved:
        parser.error("production write requires explicit root approval")
    try:
        plan = (
            locked_write(root, fail_after=args.inject_failure_after)
            if args.write
            else build_plan(root)
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
            print(f"Alexander/Sharples repair BLOCKED: {exc}", file=sys.stderr)
        return 2
    result = cli_summary(root, plan, write_requested=args.write)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print("Alexander/Sharples global P0")
        print("mode:", result["mode"].upper())
        print("status:", result["status"])
        print("changes:", json.dumps(result.get("counts", {}), sort_keys=True))
        print("changed paths:", len(result.get("changed_paths", [])))
        if args.write:
            print("write performed" if result["write_performed"] else "already applied")
        else:
            print("dry-run: nothing written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
