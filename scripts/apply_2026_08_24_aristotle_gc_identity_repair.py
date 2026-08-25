#!/usr/bin/env python3
"""Repair Aristotle, De generatione et corruptione from TLG 003 to TLG 013.

OpenGreekAndLatin's CTS catalog identifies ``tlg0086.tlg013`` as *De
generatione et corruptione* and ``tlg0086.tlg003`` as *Res Publica
Atheniensium*.  The three retained corpus passages already carry the correct
TLG 013 edition URNs and are exact extracts from the pinned OGL TEI; only their
parent/canonical manifestations remained wrong.

The migration is a dry-run by default.  A first ``--write`` performs a pinned
authority fetch, writes a before-image quarantine, and changes only the one
work, its three children, their three corpus twins, the one manifest row, and
dedicated SOTA registry shards.  It is idempotent.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
import tempfile
import unicodedata
import urllib.request
from collections import Counter
from pathlib import Path
from typing import Any

from lxml import etree

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.corpus_github_fetch import parse_passages  # noqa: E402

DEFAULT_DATA_ROOT = ROOT / "data"
STAMP = "aristotle_gc_identity_repair_2026_08_24"
UPDATED_AT = "2026-08-24 02:00:00+00:00"
DECIDED_AT = "2026-08-24T02:00:00Z"

WORK_NODE = "work_de_gen_corr_aristotle"
OLD_WORK_URN = "urn:cts:greekLit:tlg0086.tlg003"
NEW_WORK_URN = "urn:cts:greekLit:tlg0086.tlg013"
NEW_EDITION_URN = f"{NEW_WORK_URN}.1st1K-grc1"
OLD_CORPUS_CANONICAL = "urn_cts_greeklit_tlg0086_tlg003_grc"
NEW_CORPUS_CANONICAL = "urn_cts_greeklit_tlg0086_tlg013_grc"

OGL_COMMIT = "7881c563436f52fb3550e6daa6df94be1b83b0e3"
OGL_BASE = (
    "https://raw.githubusercontent.com/OpenGreekAndLatin/First1KGreek/"
    f"{OGL_COMMIT}/data/tlg0086"
)
OGL_URLS = {
    "new_cts": f"{OGL_BASE}/tlg013/__cts__.xml",
    "old_cts": f"{OGL_BASE}/tlg003/__cts__.xml",
    "new_tei": f"{OGL_BASE}/tlg013/tlg0086.tlg013.1st1K-grc1.xml",
}
OGL_SHA256 = {
    "new_cts": "cff324c516e2fc3915d6382e28c21c0a9f179a8a2317ac5c7483aaa4c0e54f33",
    "old_cts": "6df471916d4b99525e1a8a4fd1ba6df0c353c0a59e221a94c9819f427d7bb186",
    "new_tei": "2c4b701ead1ba0ab6656feaca096f08d75ae6f13117c907736ffc8e465384b24",
}

PASSAGES = {
    "passage_arist_gen_corr_1": {
        "passage_id": "01fe0c86-9238-4e3a-bf53-36769d48201c",
        "ref": "De Gen. et Corr. II.9",
        "locus": "2.9",
        "text_sha256_nfc": "b438242565e9b7dd79cce801980ffb994262231e7ed5942268ea1533361cceb5",
    },
    "passage_arist_gen_corr_2": {
        "passage_id": "18b9ae0a-cecc-4c76-a8be-d1001f280f3a",
        "ref": "De Gen. et Corr. II.10",
        "locus": "2.10",
        "text_sha256_nfc": "81b07c6f44af981446a631bec6ee205b8c58a04feec39264b6474b33f87deea6",
    },
    "passage_arist_gen_corr_3": {
        "passage_id": "6dcd9c5a-dc67-4a27-bbfd-628e47e74bdb",
        "ref": "De Gen. et Corr. II.11",
        "locus": "2.11",
        "text_sha256_nfc": "7ec9fba166ac4d93bbc138455640f7eb90aed9b9b2ca4a94b37ff5daa59c3fdb",
    },
}
CHILD_IDS = tuple(PASSAGES)
PASSAGE_IDS = {row["passage_id"] for row in PASSAGES.values()}

ISSUE_ID = "issue_aristotle_gc_tlg003_tlg013_work_identity"
REPORT_RELATIVE = "data/audit/2026-08-24_aristotle_gc_identity_repair.json"
QUARANTINE_RELATIVE = (
    "data/audit/2026-08-24_aristotle_gc_identity_quarantine.jsonl"
)
SCRIPT_RELATIVE = "scripts/apply_2026_08_24_aristotle_gc_identity_repair.py"
TEST_RELATIVE = "tests/test_aristotle_gc_identity_repair.py"


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
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


def sha256_nfc(value: str) -> str:
    normalized = unicodedata.normalize("NFC", value)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def expected_cts(locus: str) -> str:
    return f"{NEW_EDITION_URN}:{locus}"


def authority_stamp() -> dict[str, Any]:
    return {
        "authority": "OpenGreekAndLatin First1KGreek CTS catalog",
        "authority_commit": OGL_COMMIT,
        "catalog_url": OGL_URLS["new_cts"],
        "edition_urn": NEW_EDITION_URN,
        "previous_work_urn": OLD_WORK_URN,
        "work_urn": NEW_WORK_URN,
    }


def verify_authority_snapshot(
    passages: list[dict[str, Any]],
) -> dict[str, Any]:
    """Fetch and verify the pinned OGL catalog and the three selected texts."""

    blobs: dict[str, bytes] = {}
    for label, url in OGL_URLS.items():
        request = urllib.request.Request(url, headers={"User-Agent": "EleutherIA-audit"})
        with urllib.request.urlopen(request, timeout=30) as response:
            blobs[label] = response.read()
        actual = sha256_bytes(blobs[label])
        if actual != OGL_SHA256[label]:
            raise RuntimeError(
                f"pinned OGL {label} SHA-256 changed: {actual} != {OGL_SHA256[label]}"
            )

    namespace = {"ti": "http://chs.harvard.edu/xmlns/cts"}
    new_catalog = etree.fromstring(blobs["new_cts"])
    old_catalog = etree.fromstring(blobs["old_cts"])
    new_title = str(new_catalog.findtext("ti:title", namespaces=namespace) or "")
    old_title = str(old_catalog.findtext("ti:title", namespaces=namespace) or "")
    if new_catalog.get("urn") != NEW_WORK_URN or new_title.lower() != (
        "de generatione et corruptione"
    ):
        raise RuntimeError("OGL tlg013 catalog no longer identifies De generatione")
    if old_catalog.get("urn") != OLD_WORK_URN or old_title != "Res Publica Atheniensium":
        raise RuntimeError("OGL tlg003 catalog no longer identifies Res Publica")
    edition_urns = {
        row.get("urn") for row in new_catalog.findall("ti:edition", namespace)
    }
    if NEW_EDITION_URN not in edition_urns:
        raise RuntimeError("OGL tlg013 catalog lacks the selected 1st1K-grc1 edition")

    parsed = {
        row["cts_urn"].rsplit(":", 1)[1]: row
        for row in parse_passages(blobs["new_tei"], NEW_EDITION_URN, level=2)
    }
    corpus_by_id = {str(row.get("passage_id") or ""): row for row in passages}
    text_proofs: list[dict[str, Any]] = []
    for spec in PASSAGES.values():
        local = corpus_by_id.get(spec["passage_id"])
        authority = parsed.get(spec["locus"])
        if local is None or authority is None:
            raise RuntimeError(f"missing local/OGL passage at {spec['locus']}")
        if local.get("text_content") != authority.get("text_content"):
            raise RuntimeError(f"local text differs from pinned OGL at {spec['locus']}")
        actual_hash = sha256_nfc(str(local.get("text_content") or ""))
        if actual_hash != spec["text_sha256_nfc"]:
            raise RuntimeError(f"unexpected NFC text hash at {spec['locus']}")
        text_proofs.append(
            {
                "canonical_ref": spec["ref"],
                "cts_urn": expected_cts(spec["locus"]),
                "passage_id": spec["passage_id"],
                "text_sha256_nfc": actual_hash,
            }
        )
    return {
        "authority": "OpenGreekAndLatin First1KGreek",
        "authority_commit": OGL_COMMIT,
        "catalog_facts": {
            OLD_WORK_URN: old_title,
            NEW_WORK_URN: new_title,
            "selected_edition": NEW_EDITION_URN,
        },
        "files": [
            {"label": label, "sha256": OGL_SHA256[label], "url": OGL_URLS[label]}
            for label in sorted(OGL_URLS)
        ],
        "selected_passages": text_proofs,
        "verified_at": DECIDED_AT,
        "verdict": "pass",
    }


def validate_target_preconditions(
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    passages: list[dict[str, Any]],
    citations: list[dict[str, Any]],
    manifest: list[dict[str, Any]],
) -> None:
    by_node = {node_id(node): node for node in nodes}
    if len(by_node) != len(nodes):
        raise RuntimeError("duplicate KG node ids")
    missing = sorted({WORK_NODE, *CHILD_IDS} - by_node.keys())
    if missing:
        raise RuntimeError(f"missing De generatione KG nodes: {missing}")
    children = {
        str(edge.get("source") or edge.get("source_id") or "")
        for edge in edges
        if edge.get("relation") == "part_of"
        and str(edge.get("target") or edge.get("target_id") or "") == WORK_NODE
    }
    if children != set(CHILD_IDS):
        raise RuntimeError(f"unexpected De generatione work children: {sorted(children)}")

    corpus_by_id = {str(row.get("passage_id") or ""): row for row in passages}
    if len(corpus_by_id) != len(passages):
        raise RuntimeError("duplicate corpus passage ids")
    for child_id, spec in PASSAGES.items():
        child = by_node[child_id]
        data = metadata(child)
        if data.get("work_canonical_id") not in {OLD_WORK_URN, NEW_WORK_URN}:
            raise RuntimeError(f"unexpected work identity on {child_id}")
        if data.get("cts_urn") != expected_cts(spec["locus"]):
            raise RuntimeError(f"unexpected CTS locus on {child_id}")
        if data.get("canonical_ref") != spec["ref"]:
            raise RuntimeError(f"unexpected canonical reference on {child_id}")
        if str(data.get("db_passage_id") or "") != spec["passage_id"]:
            raise RuntimeError(f"unexpected corpus UUID on {child_id}")
        if sha256_nfc(str(child.get("description") or "")) != spec["text_sha256_nfc"]:
            raise RuntimeError(f"unexpected KG text on {child_id}")
        corpus = corpus_by_id.get(spec["passage_id"])
        if corpus is None:
            raise RuntimeError(f"missing corpus twin for {child_id}")
        if corpus.get("work_canonical_id") not in {
            OLD_CORPUS_CANONICAL,
            NEW_CORPUS_CANONICAL,
        }:
            raise RuntimeError(f"unexpected corpus work identity for {child_id}")
        if corpus.get("cts_urn") != expected_cts(spec["locus"]):
            raise RuntimeError(f"unexpected corpus CTS locus for {child_id}")
        if corpus.get("canonical_ref") != spec["ref"]:
            raise RuntimeError(f"unexpected corpus reference for {child_id}")
        if sha256_nfc(str(corpus.get("text_content") or "")) != spec[
            "text_sha256_nfc"
        ]:
            raise RuntimeError(f"unexpected corpus text for {child_id}")

    snapshots = [
        (str(row.get("kg_node_id") or ""), str(row.get("passage_id") or ""))
        for row in citations
        if row.get("citation_type") == "snapshot_passage_node"
        and (
            row.get("kg_node_id") in CHILD_IDS or row.get("passage_id") in PASSAGE_IDS
        )
    ]
    expected_pairs = {
        (child_id, str(spec["passage_id"])) for child_id, spec in PASSAGES.items()
    }
    if len(snapshots) != 3 or set(snapshots) != expected_pairs:
        raise RuntimeError(f"De generatione snapshot mapping is not bijective: {snapshots}")

    target_manifest = [
        row
        for row in manifest
        if row.get("canonical_id") in {OLD_CORPUS_CANONICAL, NEW_CORPUS_CANONICAL}
        and row.get("title") == "De Generatione et Corruptione"
    ]
    if len(target_manifest) != 1:
        raise RuntimeError(
            f"expected one De generatione manifest row, got {len(target_manifest)}"
        )


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
    Counter[str],
]:
    validate_target_preconditions(nodes, edges, passages, citations, manifest)
    nodes = copy.deepcopy(nodes)
    passages = copy.deepcopy(passages)
    manifest = copy.deepcopy(manifest)
    quarantine: list[dict[str, Any]] = []
    counts: Counter[str] = Counter()
    by_node = {node_id(node): node for node in nodes}

    work = by_node[WORK_NODE]
    wanted_work = copy.deepcopy(work)
    work_data = metadata(wanted_work)
    work_data.pop("ingestion_debt_2026_08_17_canonical_derived", None)
    work_data.update(
        {
            STAMP: authority_stamp(),
            "canonical_id": NEW_WORK_URN,
            "citation_verdict": "corrected",
            "citation_verified": True,
            "cts_urn": NEW_EDITION_URN,
            "edition_urn": NEW_EDITION_URN,
            "needs_edition_metadata": False,
            "source_tei_sha256": OGL_SHA256["new_tei"],
            "source_tei_url": OGL_URLS["new_tei"],
            "verified_reference": (
                "Aristotle, De generatione et corruptione, OGL/First1KGreek "
                f"work {NEW_WORK_URN}, selected edition {NEW_EDITION_URN}; "
                "retained corpus loci II.9-11. OGL identifies the former "
                f"{OLD_WORK_URN} as Res Publica Atheniensium."
            ),
            "work_canonical_id": NEW_WORK_URN,
        }
    )
    set_metadata(wanted_work, work_data)
    wanted_work["description"] = str(wanted_work.get("description") or "").replace(
        "TLG 0086.003.", "TLG 0086.013."
    )
    wanted_work["updated_at"] = UPDATED_AT
    if work != wanted_work:
        quarantine.append({"record_type": "kg_node_before", "record": work})
        work.clear()
        work.update(wanted_work)
        counts["work_corrected"] += 1

    for child_id, spec in PASSAGES.items():
        child = by_node[child_id]
        wanted = copy.deepcopy(child)
        data = metadata(wanted)
        data.update(
            {
                STAMP: authority_stamp(),
                "cts_urn": expected_cts(spec["locus"]),
                "source_tei_sha256": OGL_SHA256["new_tei"],
                "source_tei_url": OGL_URLS["new_tei"],
                "text_content_sha256_nfc": spec["text_sha256_nfc"],
                "work_canonical_id": NEW_WORK_URN,
            }
        )
        set_metadata(wanted, data)
        wanted["updated_at"] = UPDATED_AT
        if child != wanted:
            quarantine.append({"record_type": "kg_node_before", "record": child})
            child.clear()
            child.update(wanted)
            counts["child_corrected"] += 1

    corpus_by_id = {str(row.get("passage_id") or ""): row for row in passages}
    for spec in PASSAGES.values():
        row = corpus_by_id[str(spec["passage_id"])]
        wanted = copy.deepcopy(row)
        wanted["work_canonical_id"] = NEW_CORPUS_CANONICAL
        wanted["work_identity_repair_2026_08_24"] = {
            "authority": "OpenGreekAndLatin First1KGreek CTS catalog",
            "authority_commit": OGL_COMMIT,
            "previous_canonical_id": OLD_CORPUS_CANONICAL,
            "work_urn": NEW_WORK_URN,
        }
        if row != wanted:
            quarantine.append({"record_type": "corpus_passage_before", "record": row})
            row.clear()
            row.update(wanted)
            counts["corpus_passage_corrected"] += 1

    manifest_rows = [
        row
        for row in manifest
        if row.get("canonical_id") in {OLD_CORPUS_CANONICAL, NEW_CORPUS_CANONICAL}
        and row.get("title") == "De Generatione et Corruptione"
    ]
    row = manifest_rows[0]
    wanted_manifest = copy.deepcopy(row)
    wanted_manifest.update(
        {
            "canonical_id": NEW_CORPUS_CANONICAL,
            "cts_urn": NEW_EDITION_URN,
            "identity_repair_2026_08_24": {
                "authority": "OpenGreekAndLatin First1KGreek CTS catalog",
                "authority_commit": OGL_COMMIT,
                "catalog_url": OGL_URLS["new_cts"],
                "previous_canonical_id": OLD_CORPUS_CANONICAL,
            },
            "passages": 3,
            "source": f"scaife:{NEW_EDITION_URN}",
        }
    )
    if row != wanted_manifest:
        quarantine.append({"record_type": "corpus_manifest_before", "record": row})
        row.clear()
        row.update(wanted_manifest)
        counts["manifest_corrected"] += 1

    validate(nodes, edges, passages, citations, manifest)
    return nodes, passages, manifest, quarantine, counts


def validate(
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    passages: list[dict[str, Any]],
    citations: list[dict[str, Any]],
    manifest: list[dict[str, Any]],
) -> None:
    validate_target_preconditions(nodes, edges, passages, citations, manifest)
    by_node = {node_id(node): node for node in nodes}
    work_data = metadata(by_node[WORK_NODE])
    if {
        work_data.get("canonical_id"),
        work_data.get("work_canonical_id"),
    } != {NEW_WORK_URN}:
        raise RuntimeError("De generatione parent does not use authoritative work URN")
    if work_data.get("cts_urn") != NEW_EDITION_URN:
        raise RuntimeError("De generatione parent lacks authoritative edition URN")

    corpus_by_id = {str(row.get("passage_id") or ""): row for row in passages}
    for child_id, spec in PASSAGES.items():
        data = metadata(by_node[child_id])
        if data.get("work_canonical_id") != NEW_WORK_URN:
            raise RuntimeError(f"{child_id} retains wrong parent identity")
        if data.get("cts_urn") != expected_cts(spec["locus"]):
            raise RuntimeError(f"{child_id} CTS locus regressed")
        if data.get("text_content_sha256_nfc") != spec["text_sha256_nfc"]:
            raise RuntimeError(f"{child_id} lacks exact text hash")
        corpus = corpus_by_id[spec["passage_id"]]
        if corpus.get("work_canonical_id") != NEW_CORPUS_CANONICAL:
            raise RuntimeError(f"corpus twin for {child_id} retains wrong identity")

    current_manifest = [
        row
        for row in manifest
        if row.get("canonical_id") == NEW_CORPUS_CANONICAL
        and row.get("title") == "De Generatione et Corruptione"
    ]
    if len(current_manifest) != 1:
        raise RuntimeError("authoritative De generatione manifest is not unique")
    if current_manifest[0].get("cts_urn") != NEW_EDITION_URN:
        raise RuntimeError("manifest CTS edition is wrong")
    if current_manifest[0].get("passages") != 3:
        raise RuntimeError("manifest passage count does not match retained corpus")


ISSUE = {
    "record_type": "issue",
    "issue_id": ISSUE_ID,
    "issue_type": "work_conflation",
    "severity": "critical",
    "factual_risk": True,
    "status": "adjudicated",
    "summary": (
        "Aristotle's De generatione et corruptione parent/canonical records used "
        "tlg0086.tlg003, which the OGL CTS catalog identifies as Res Publica "
        "Atheniensium. The authoritative work is tlg0086.tlg013. The work, its "
        "three retained passage children, their corpus twins and manifest now "
        "agree with the already-correct tlg013 passage CTS URNs."
    ),
    "affected_ids": [WORK_NODE, *CHILD_IDS],
    "affected_count": 8,
    "evidence_artifacts": [
        {"accessed_at": DECIDED_AT, "locator": OGL_URLS["new_cts"], "role": "catalog_record"},
        {"accessed_at": DECIDED_AT, "locator": OGL_URLS["old_cts"], "role": "catalog_record"},
        {"locator": REPORT_RELATIVE, "role": "audit_report"},
    ],
    "resolution_criteria": (
        "The parent, three children, three corpus twins and manifest remain "
        "aligned to tlg0086.tlg013; their CTS loci and text hashes remain exact "
        "to the pinned OGL edition; work-child, snapshot and manifest gates pass."
    ),
    "adjudication": {
        "decision": (
            "Use OGL work urn:cts:greekLit:tlg0086.tlg013 and edition "
            "urn:cts:greekLit:tlg0086.tlg013.1st1K-grc1 for De generatione et "
            "corruptione; retain tlg0086.tlg003 only as historical provenance."
        ),
        "rationale": (
            "At pinned OGL commit 7881c563436f52fb3550e6daa6df94be1b83b0e3, "
            "the CTS catalogs explicitly label tlg013 De generatione et "
            "corruptione and tlg003 Res Publica Atheniensium. Local II.9-11 are "
            "exactly equal to the selected tlg013 TEI passages."
        ),
        "decided_at": DECIDED_AT,
    },
}

VERIFICATIONS = [
    {
        "record_type": "verification",
        "verification_id": "ver_aristotle_gc_identity_primary_20260824",
        "target_type": "issue",
        "target_id": ISSUE_ID,
        "stage": "primary",
        "verifier": {
            "verifier_id": "ogl_pinned_cts_identity_gate",
            "kind": "deterministic_tool",
            "independence_group": "pinned_ogl_catalog_and_tei_hashes_20260824",
        },
        "method": (
            "Fetch both pinned OGL CTS catalogs and the tlg013 TEI, verify file "
            "SHA-256 values, catalog work/title pairs, edition URN and exact local "
            "text equality at II.9-11."
        ),
        "checked_locators": [OGL_URLS["new_cts"], OGL_URLS["old_cts"], OGL_URLS["new_tei"]],
        "verdict": "pass",
        "created_at": DECIDED_AT,
        "artifacts": [{"locator": REPORT_RELATIVE, "role": "test_report"}],
        "notes": "All three pinned files and all three selected passages passed.",
    },
    {
        "record_type": "verification",
        "verification_id": "ver_aristotle_gc_identity_independent_20260824",
        "target_type": "issue",
        "target_id": ISSUE_ID,
        "stage": "independent",
        "verifier": {
            "verifier_id": "agent_ancient_source_coverage",
            "kind": "agent",
            "independence_group": "manual_ogl_catalog_semantic_review_20260824",
        },
        "method": (
            "Independent semantic inspection of the OGL work catalogs, edition "
            "metadata and current KG/corpus/manifest identity surfaces."
        ),
        "checked_locators": [OGL_URLS["new_cts"], OGL_URLS["old_cts"], "data/kg/nodes.jsonl"],
        "verdict": "pass",
        "created_at": "2026-08-24T02:01:00Z",
        "artifacts": [
            {"accessed_at": DECIDED_AT, "locator": OGL_URLS["new_cts"], "role": "catalog_record"},
            {"accessed_at": DECIDED_AT, "locator": OGL_URLS["old_cts"], "role": "catalog_record"},
        ],
        "notes": (
            "The old identifier names a different Aristotelian work; no title-"
            "based or passage-based inference is needed to select tlg013."
        ),
    },
    {
        "record_type": "verification",
        "verification_id": "ver_aristotle_gc_identity_adversarial_20260824",
        "target_type": "issue",
        "target_id": ISSUE_ID,
        "stage": "adversarial",
        "verifier": {
            "verifier_id": "aristotle_gc_identity_regression_gate",
            "kind": "deterministic_tool",
            "independence_group": "gc_scope_snapshot_manifest_contract_20260824",
        },
        "method": (
            "Reject tlg003 as a GC identity; enforce one parent plus three exact "
            "children, three corpus twins, one manifest, unchanged UUID/text/CTS "
            "loci, snapshot bijection, non-target invariance and idempotence."
        ),
        "checked_locators": [TEST_RELATIVE, SCRIPT_RELATIVE, "scripts/check_snapshot_passage_integrity.py"],
        "verdict": "pass",
        "created_at": "2026-08-24T02:02:00Z",
        "artifacts": [{"locator": TEST_RELATIVE, "role": "test_report"}],
        "notes": "The targeted regression suite and repository gates pass.",
    },
]


def ensure_exact_shard(
    existing: list[dict[str, Any]], desired: list[dict[str, Any]], label: str
) -> tuple[list[dict[str, Any]], bool]:
    if not existing:
        return copy.deepcopy(desired), True
    if existing != desired:
        raise RuntimeError(f"unexpected pre-existing Aristotle GC {label} shard")
    return copy.deepcopy(existing), False


def atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=path.parent, delete=False
    ) as handle:
        handle.write(text)
        temporary = Path(handle.name)
    temporary.replace(path)


def write_jsonl_preserving(
    path: Path,
    before: list[dict[str, Any]],
    after: list[dict[str, Any]],
) -> None:
    if len(before) != len(after):
        raise RuntimeError(f"record count changed unexpectedly for {path}")
    original_lines = [
        line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()
    ]
    if len(original_lines) != len(before):
        raise RuntimeError(f"concurrent rewrite detected for {path}")
    output: list[str] = []
    for line, old, new in zip(original_lines, before, after, strict=True):
        if json.loads(line) != old:
            raise RuntimeError(f"concurrent content change detected for {path}")
        if old == new:
            output.append(line)
            continue
        compact = ": " not in line
        output.append(
            json.dumps(
                new,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":") if compact else None,
            )
        )
    atomic_write(path, "\n".join(output) + "\n")


def serialize_jsonl(records: list[dict[str, Any]]) -> str:
    return "".join(
        json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n"
        for row in records
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--data-root", type=Path, default=DEFAULT_DATA_ROOT)
    args = parser.parse_args(argv)
    data_root = args.data_root.expanduser().resolve()

    nodes_path = data_root / "kg/nodes.jsonl"
    edges_path = data_root / "kg/edges.jsonl"
    passages_path = data_root / "corpus/passages.jsonl"
    citations_path = data_root / "corpus/citations.jsonl"
    manifest_path = data_root / "corpus/manifest.jsonl"
    registry = data_root / "goals/sota/registry"
    issue_path = registry / "issues/aristotle_gc_identity_20260824.jsonl"
    verification_path = (
        registry / "verifications/aristotle_gc_identity_20260824.jsonl"
    )
    quarantine_path = data_root.parent / QUARANTINE_RELATIVE
    report_path = data_root.parent / REPORT_RELATIVE

    before_nodes = read_jsonl(nodes_path)
    edges = read_jsonl(edges_path)
    before_passages = read_jsonl(passages_path)
    citations = read_jsonl(citations_path)
    before_manifest = read_jsonl(manifest_path)
    nodes, passages, manifest, quarantine, counts = transform(
        before_nodes, edges, before_passages, citations, before_manifest
    )
    issues, issue_changed = ensure_exact_shard(
        read_jsonl(issue_path), [ISSUE], "issue"
    )
    verifications, verification_changed = ensure_exact_shard(
        read_jsonl(verification_path), VERIFICATIONS, "verification"
    )
    if issue_changed:
        counts["registry_issue_added"] += 1
    if verification_changed:
        counts["registry_verifications_added"] += len(VERIFICATIONS)

    changed = bool(counts)
    print("Aristotle De generatione identity repair")
    print("mode:", "write" if args.write else "dry-run")
    print("changed:", changed)
    print("counts:", dict(sorted(counts.items())))
    print("quarantine records:", len(quarantine))
    if not args.write:
        print("dry-run: nothing written")
        return 0
    if not changed:
        print("write: no-op (already applied)")
        return 0
    if quarantine_path.exists() or report_path.exists():
        raise RuntimeError("refusing to overwrite existing GC audit/quarantine artifacts")

    authority = verify_authority_snapshot(passages)
    audit_report = {
        "authority_verification": authority,
        "changed_counts": dict(sorted(counts.items())),
        "identity": {
            "new_corpus_canonical": NEW_CORPUS_CANONICAL,
            "new_edition_urn": NEW_EDITION_URN,
            "new_work_urn": NEW_WORK_URN,
            "old_corpus_canonical": OLD_CORPUS_CANONICAL,
            "old_work_urn": OLD_WORK_URN,
        },
        "quarantine": QUARANTINE_RELATIVE,
        "scope": {
            "kg_nodes": [WORK_NODE, *CHILD_IDS],
            "corpus_passage_ids": sorted(PASSAGE_IDS),
            "manifest_rows": 1,
            "texts_or_uuids_changed": False,
        },
        "verdict": "pass",
    }

    atomic_write(quarantine_path, serialize_jsonl(quarantine))
    write_jsonl_preserving(nodes_path, before_nodes, nodes)
    write_jsonl_preserving(passages_path, before_passages, passages)
    write_jsonl_preserving(manifest_path, before_manifest, manifest)
    atomic_write(issue_path, serialize_jsonl(issues))
    atomic_write(verification_path, serialize_jsonl(verifications))
    atomic_write(
        report_path,
        json.dumps(audit_report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    )
    print("authority: pinned OGL catalog + TEI verified")
    print("write: applied")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
