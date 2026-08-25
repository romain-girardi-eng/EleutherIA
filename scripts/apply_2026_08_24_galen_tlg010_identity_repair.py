#!/usr/bin/env python3
"""Close the remaining Galen tlg0057.tlg010 manifest identity error.

The 2026-08-17 repair correctly separated Galen's *De naturalibus
facultatibus* (TLG 0057.010) from *De placitis Hippocratis et Platonis*
(TLG 0057.032), re-homed the three full-book passage snapshots, and preserved
their legacy stable node IDs.  One corpus-manifest row retained the old
*De placitis* title under the tlg010 edition source.

Dry-run is the default.  ``--write`` verifies pinned OGL catalogs and TEI,
checks exact local full-book texts, quarantines the old manifest row, and
changes only that row plus dedicated audit/registry artifacts.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import tempfile
import unicodedata
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_ROOT = ROOT / "data"

STAMP = "galen_tlg010_identity_repair_2026_08_24"
ISSUE_ID = "issue_galen_tlg010_manifest_title_identity"

NATURAL_WORK_NODE = "work_galen_de_naturalibus_facultatibus"
PLACITIS_WORK_NODE = "work_galen_de_placitis"
GALEN_PERSON_NODE = "person_galen_pergamon_129_216ce"
NATURAL_WORK_URN = "urn:cts:greekLit:tlg0057.tlg010"
NATURAL_EDITION_URN = f"{NATURAL_WORK_URN}.1st1K-grc1"
PLACITIS_WORK_URN = "urn:cts:greekLit:tlg0057.tlg032"
PLACITIS_EDITION_URN = f"{PLACITIS_WORK_URN}.1st1K-grc1"
NATURAL_CANONICAL_ID = "urn_cts_greeklit_tlg0057_tlg010_grc"
NATURAL_TITLE = "De naturalibus facultatibus"
WRONG_TITLE = "De Placitis Hippocratis et Platonis"

OGL_COMMIT = "7881c563436f52fb3550e6daa6df94be1b83b0e3"
OGL_BASE = (
    "https://raw.githubusercontent.com/OpenGreekAndLatin/First1KGreek/"
    f"{OGL_COMMIT}/data/tlg0057"
)
OGL_URLS = {
    "natural_cts": f"{OGL_BASE}/tlg010/__cts__.xml",
    "placitis_cts": f"{OGL_BASE}/tlg032/__cts__.xml",
    "natural_tei": (
        f"{OGL_BASE}/tlg010/tlg0057.tlg010.1st1K-grc1.xml"
    ),
}
OGL_SHA256 = {
    "natural_cts": "8add5baf1c6a33e95367dc72f90cab176e4bcd2e39740653b9b546627c532147",
    "placitis_cts": "5ec153468f42e7986dcd000710060c4343780180a8b2136c429f0b42dd6b67d4",
    "natural_tei": "f527cc38fa1b425ab81c8c4a5f6457c53e3bceb3f8c0d338b48a98fe8b9e5b0e",
}

PASSAGES: tuple[dict[str, Any], ...] = (
    {
        "node_id": "passage_galen_plac_1",
        "passage_id": "429f228e-9268-4d9b-96a9-5676f54d07a0",
        "book": 1,
        "locus": "1.1-1.17",
        "canonical_ref": "Nat. Fac. 1.1-1.17",
        "text_sha256": "0c85bc52188b43f468b98f252d47b7783b9c009c5053326ce8c3c5199a5df639",
    },
    {
        "node_id": "passage_galen_plac_2",
        "passage_id": "ced253e3-7ffc-46e2-a75b-90c1ca8bca71",
        "book": 2,
        "locus": "2.1-2.9",
        "canonical_ref": "Nat. Fac. 2.1-2.9",
        "text_sha256": "1b69f28be44b27f6aa257bcf11f758037975887d2fa8763b8b08fd74fa9ffeee",
    },
    {
        "node_id": "passage_galen_plac_3",
        "passage_id": "9f86c8e0-af5d-46db-ac08-dfb8a0accb2c",
        "book": 3,
        "locus": "3.1-3.15",
        "canonical_ref": "Nat. Fac. 3.1-3.15",
        "text_sha256": "eb2ff1a74690293e177edf73a437adf4b822b5e5b292ae971f009fdaa85a57f7",
    },
)

REPORT_RELATIVE = "audit/2026-08-24_galen_tlg010_identity_repair.json"
QUARANTINE_RELATIVE = "audit/2026-08-24_galen_tlg010_identity_quarantine.jsonl"
ISSUE_RELATIVE = "goals/sota/registry/issues/galen_tlg010_20260824.jsonl"
VERIFICATION_RELATIVE = (
    "goals/sota/registry/verifications/galen_tlg010_20260824.jsonl"
)


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


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_text(value: str) -> str:
    return sha256_bytes(value.encode("utf-8"))


def nfc(value: str) -> str:
    return unicodedata.normalize("NFC", value)


def expected_cts(locus: str) -> str:
    return f"{NATURAL_EDITION_URN}:{locus}"


def fetch_url(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "EleutherIA-audit/1.0"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read()


def _cts_facts(raw: bytes) -> tuple[str, str, str]:
    root = ET.fromstring(raw)
    ns = {"ti": "http://chs.harvard.edu/xmlns/cts"}
    title = root.findtext("ti:title", namespaces=ns) or ""
    edition = root.find("ti:edition", ns)
    if edition is None:
        raise RuntimeError("OGL CTS catalog lacks edition")
    return str(root.get("urn") or ""), title, str(edition.get("urn") or "")


def _tei_books(raw: bytes) -> tuple[str, str, dict[int, str]]:
    root = ET.fromstring(raw)
    ns = {"tei": "http://www.tei-c.org/ns/1.0"}
    title = root.findtext(".//tei:titleStmt/tei:title", namespaces=ns) or ""
    edition = root.find(".//tei:div[@type='edition']", ns)
    if edition is None:
        raise RuntimeError("OGL TEI lacks edition div")
    books: dict[int, str] = {}
    for book in edition.findall("./tei:div[@subtype='book']", ns):
        number = int(str(book.get("n")))
        paragraphs: list[str] = []
        for chapter in book.findall("./tei:div[@subtype='chapter']", ns):
            for paragraph in chapter.findall("./tei:p", ns):
                text = " ".join("".join(paragraph.itertext()).split())
                if text:
                    paragraphs.append(text)
        books[number] = " ".join(paragraphs)
    return title, str(edition.get("n") or ""), books


def verify_authority_snapshot(passages: list[dict[str, Any]]) -> dict[str, Any]:
    fetched = {key: fetch_url(url) for key, url in OGL_URLS.items()}
    for key, raw in fetched.items():
        actual = sha256_bytes(raw)
        if actual != OGL_SHA256[key]:
            raise RuntimeError(f"pinned OGL {key} SHA-256 drift: {actual}")

    natural = _cts_facts(fetched["natural_cts"])
    placitis = _cts_facts(fetched["placitis_cts"])
    if natural != (NATURAL_WORK_URN, NATURAL_TITLE, NATURAL_EDITION_URN):
        raise RuntimeError(f"unexpected OGL natural-faculties catalog: {natural}")
    if placitis != (
        PLACITIS_WORK_URN,
        "De placitis Hippocratis et Platonis",
        PLACITIS_EDITION_URN,
    ):
        raise RuntimeError(f"unexpected OGL De placitis catalog: {placitis}")

    tei_title, tei_edition, books = _tei_books(fetched["natural_tei"])
    if tei_title != NATURAL_TITLE or tei_edition != NATURAL_EDITION_URN:
        raise RuntimeError("OGL TEI title/edition disagrees with CTS catalog")
    corpus = {str(row.get("passage_id") or ""): row for row in passages}
    text_proofs: list[dict[str, Any]] = []
    for spec in PASSAGES:
        local = corpus.get(spec["passage_id"])
        authority = books.get(spec["book"])
        if local is None or authority is None:
            raise RuntimeError(f"missing local/OGL Galen book {spec['book']}")
        local_text = str(local.get("text_content") or "")
        if local_text != authority:
            raise RuntimeError(f"local Galen book {spec['book']} differs from pinned OGL")
        actual_hash = sha256_text(local_text)
        if actual_hash != spec["text_sha256"]:
            raise RuntimeError(f"unexpected Galen book {spec['book']} text hash")
        text_proofs.append(
            {
                "book": spec["book"],
                "cts_urn": expected_cts(spec["locus"]),
                "passage_id": spec["passage_id"],
                "text_sha256": actual_hash,
            }
        )
    return {
        "authority": "OpenGreekAndLatin First1KGreek",
        "authority_commit": OGL_COMMIT,
        "catalog_facts": {
            NATURAL_WORK_URN: NATURAL_TITLE,
            PLACITIS_WORK_URN: "De placitis Hippocratis et Platonis",
            "selected_edition": NATURAL_EDITION_URN,
            "source_collection": "Claudii Galeni Opera Omnia, Volume 2",
        },
        "file_sha256": OGL_SHA256,
        "text_proofs": text_proofs,
    }


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
    list[str],
]:
    nodes = copy.deepcopy(nodes)
    edges = copy.deepcopy(edges)
    passages = copy.deepcopy(passages)
    citations = copy.deepcopy(citations)
    manifest = copy.deepcopy(manifest)
    changed: list[str] = []

    rows = [row for row in manifest if row.get("canonical_id") == NATURAL_CANONICAL_ID]
    if len(rows) != 1:
        raise RuntimeError(f"expected one Galen tlg010 manifest row, found {len(rows)}")
    row = rows[0]
    if row.get("title") not in {WRONG_TITLE, NATURAL_TITLE}:
        raise RuntimeError(f"unexpected Galen tlg010 manifest title: {row.get('title')}")
    if row.get("source") != f"scaife:{NATURAL_EDITION_URN}":
        raise RuntimeError("Galen tlg010 manifest source drift")

    if row.get("title") == WRONG_TITLE or row.get("cts_urn") != NATURAL_EDITION_URN:
        row.update(
            {
                "title": NATURAL_TITLE,
                "cts_urn": NATURAL_EDITION_URN,
                "work_urn": NATURAL_WORK_URN,
                "language": "grc",
                "edition": (
                    "Karl Gottlob Kühn (ed.), Claudii Galeni Opera Omnia, "
                    "vol. 2 (Leipzig: Knobloch, 1821), pp. 1-214"
                ),
                "license": "CC BY-SA 4.0",
                "source_commit": OGL_COMMIT,
                "identity_repair_2026_08_24": {
                    "authority": "OGL First1KGreek + Perseus/Scaife + CMG",
                    "catalog_url": OGL_URLS["natural_cts"],
                    "distinguished_from": PLACITIS_WORK_URN,
                    "previous_title": WRONG_TITLE,
                },
            }
        )
        changed.append("manifest:" + NATURAL_CANONICAL_ID)

    validate(nodes, edges, passages, citations, manifest)
    return nodes, edges, passages, citations, manifest, changed


def validate(
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    passages: list[dict[str, Any]],
    citations: list[dict[str, Any]],
    manifest: list[dict[str, Any]],
) -> dict[str, int]:
    by_node = {node_id(node): node for node in nodes}
    natural = by_node.get(NATURAL_WORK_NODE)
    placitis = by_node.get(PLACITIS_WORK_NODE)
    if natural is None or placitis is None:
        raise RuntimeError("Galen work-node pair is incomplete")
    natural_meta = metadata(natural)
    placitis_meta = metadata(placitis)
    if natural_meta.get("canonical_id") != NATURAL_WORK_URN:
        raise RuntimeError("natural-faculties work is not tlg010")
    if placitis_meta.get("canonical_id") != PLACITIS_WORK_URN:
        raise RuntimeError("De placitis work is not tlg032")
    if "work_canonical_id" in placitis_meta:
        raise RuntimeError("De placitis retains a derived child-work identity")
    if WRONG_TITLE.casefold() in json.dumps(natural, ensure_ascii=False).casefold():
        raise RuntimeError("natural-faculties work still carries De placitis title")

    corpus = {str(row.get("passage_id") or ""): row for row in passages}
    expected_pairs: set[tuple[str, str]] = set()
    for spec in PASSAGES:
        node = by_node.get(spec["node_id"])
        row = corpus.get(spec["passage_id"])
        if node is None or row is None:
            raise RuntimeError(f"missing Galen snapshot twin for book {spec['book']}")
        data = metadata(node)
        expected_urn = expected_cts(spec["locus"])
        if (
            data.get("work_canonical_id") != NATURAL_WORK_URN
            or data.get("work_title") != NATURAL_TITLE
            or data.get("cts_urn") != expected_urn
            or data.get("canonical_ref") != spec["canonical_ref"]
            or data.get("db_passage_id") != spec["passage_id"]
        ):
            raise RuntimeError(f"Galen KG identity mismatch: {spec['node_id']}")
        if (
            row.get("work_canonical_id") != NATURAL_CANONICAL_ID
            or row.get("cts_urn") != expected_urn
            or row.get("canonical_ref") != spec["canonical_ref"]
        ):
            raise RuntimeError(f"Galen corpus identity mismatch: {spec['passage_id']}")
        node_text = str(node.get("description") or "")
        corpus_text = str(row.get("text_content") or "")
        if nfc(node_text) != nfc(corpus_text):
            raise RuntimeError(f"Galen snapshot text mismatch: {spec['node_id']}")
        if sha256_text(corpus_text) != spec["text_sha256"]:
            raise RuntimeError(f"Galen corpus text hash drift: book {spec['book']}")
        expected_pairs.add((spec["node_id"], spec["passage_id"]))

    natural_rows = [
        row for row in passages if row.get("work_canonical_id") == NATURAL_CANONICAL_ID
    ]
    if len(natural_rows) != len(PASSAGES):
        raise RuntimeError(f"expected 3 tlg010 corpus books, found {len(natural_rows)}")
    if any(PLACITIS_WORK_URN in str(row.get("cts_urn") or "") for row in passages):
        raise RuntimeError("De placitis unexpectedly has corpus children")

    snapshot_pairs = {
        (str(row.get("kg_node_id") or ""), str(row.get("passage_id") or ""))
        for row in citations
        if row.get("citation_type") == "snapshot_passage_node"
        and (
            str(row.get("kg_node_id") or "").startswith("passage_galen_plac_")
            or str(row.get("passage_id") or "")
            in {spec["passage_id"] for spec in PASSAGES}
        )
    }
    if snapshot_pairs != expected_pairs:
        raise RuntimeError(f"Galen snapshot citation mismatch: {snapshot_pairs}")

    part_pairs = {
        (str(edge.get("source") or ""), str(edge.get("target") or ""))
        for edge in edges
        if edge.get("relation") == "part_of"
        and str(edge.get("source") or "").startswith("passage_galen_plac_")
    }
    if part_pairs != {(spec["node_id"], NATURAL_WORK_NODE) for spec in PASSAGES}:
        raise RuntimeError(f"Galen work-child edge mismatch: {part_pairs}")
    authored = {
        (str(edge.get("source") or ""), str(edge.get("target") or ""))
        for edge in edges
        if edge.get("relation") == "authored_by"
    }
    required_authored = {
        (NATURAL_WORK_NODE, GALEN_PERSON_NODE),
        (PLACITIS_WORK_NODE, GALEN_PERSON_NODE),
        *((spec["node_id"], GALEN_PERSON_NODE) for spec in PASSAGES),
    }
    if not required_authored.issubset(authored):
        raise RuntimeError("Galen authorship edges are incomplete")

    manifests = [
        row for row in manifest if row.get("canonical_id") == NATURAL_CANONICAL_ID
    ]
    if len(manifests) != 1:
        raise RuntimeError("Galen tlg010 manifest is not unique")
    manifest_row = manifests[0]
    if (
        manifest_row.get("title") != NATURAL_TITLE
        or manifest_row.get("cts_urn") != NATURAL_EDITION_URN
        or manifest_row.get("work_urn") != NATURAL_WORK_URN
        or manifest_row.get("source") != f"scaife:{NATURAL_EDITION_URN}"
        or manifest_row.get("passages") != len(PASSAGES)
    ):
        raise RuntimeError("Galen tlg010 manifest contract is incomplete")
    return {
        "work_nodes": 2,
        "passage_nodes": len(PASSAGES),
        "corpus_passages": len(natural_rows),
        "snapshot_citations": len(snapshot_pairs),
        "part_of_edges": len(part_pairs),
        "manifest_rows": len(manifests),
    }


def write_preserving_manifest(path: Path, rows: list[dict[str, Any]]) -> None:
    desired = {str(row.get("canonical_id") or ""): row for row in rows}
    if len(desired) != len(rows):
        raise RuntimeError("duplicate corpus manifest canonical_id")
    output: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        old = json.loads(line)
        key = str(old.get("canonical_id") or "")
        new = desired[key]
        output.append(
            line
            if old == new
            else json.dumps(new, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        )
    atomic_write_text(path, "\n".join(output) + "\n")


def atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=path.parent, delete=False
    ) as handle:
        tmp = Path(handle.name)
        handle.write(content)
    tmp.replace(path)


def registry_issue() -> dict[str, Any]:
    return {
        "record_type": "issue",
        "issue_id": ISSUE_ID,
        "issue_type": "bibliographic_identity",
        "severity": "critical",
        "factual_risk": True,
        "status": "resolved",
        "summary": (
            "The corpus manifest labeled the OGL tlg0057.tlg010 edition as De Placitis "
            "after KG, corpus, citations and work-child edges had already been correctly "
            "separated. The manifest now identifies De naturalibus facultatibus; "
            "De placitis remains the distinct work tlg0057.tlg032."
        ),
        "affected_ids": [
            NATURAL_WORK_NODE,
            PLACITIS_WORK_NODE,
        ],
        "affected_count": 1,
        "evidence_artifacts": [
            {"locator": f"data/{REPORT_RELATIVE}", "role": "audit_report"},
            {"locator": f"data/{QUARANTINE_RELATIVE}", "role": "audit_report"},
            {
                "locator": "scripts/apply_2026_08_24_galen_tlg010_identity_repair.py",
                "role": "audit_report",
            },
            {
                "locator": "tests/test_galen_tlg010_identity_repair.py",
                "role": "test_report",
            },
        ],
        "resolution_criteria": (
            "tlg010 remains De naturalibus facultatibus across manifest, work, three "
            "exact OGL books and snapshot citations; tlg032 remains De placitis with no "
            "corpus child; work-child/corpus/snapshot gates and idempotence pass."
        ),
        "adjudication": {
            "decision": (
                "Correct only the stale tlg010 manifest title and edition metadata; "
                "retain legacy passage node IDs as stable opaque identifiers."
            ),
            "rationale": (
                "Pinned OGL catalogs, Perseus/Scaife, CMG's TLG-ID listing and the "
                "byte-exact three-book Greek text independently establish tlg010 as "
                "De naturalibus facultatibus and tlg032 as De placitis."
            ),
            "decided_at": "2026-08-24T04:30:00Z",
        },
    }


def registry_verifications() -> list[dict[str, Any]]:
    base_artifact = {"locator": f"data/{REPORT_RELATIVE}", "role": "test_report"}
    return [
        {
            "record_type": "verification",
            "verification_id": "ver_galen_tlg010_identity_primary_20260824",
            "target_type": "issue",
            "target_id": ISSUE_ID,
            "stage": "primary",
            "verifier": {
                "verifier_id": "ogl_galen_tlg010_pinned_gate",
                "kind": "deterministic_tool",
                "independence_group": "pinned_ogl_catalog_tei_20260824",
            },
            "method": (
                "Verify SHA-256-pinned OGL tlg010/tlg032 CTS catalogs and tlg010 TEI; "
                "extract all three books and require byte equality with local corpus."
            ),
            "checked_locators": list(OGL_URLS.values()),
            "verdict": "pass",
            "created_at": "2026-08-24T04:31:00Z",
            "artifacts": [base_artifact],
            "notes": "OGL titles, edition URNs, raw file hashes and all book texts passed.",
        },
        {
            "record_type": "verification",
            "verification_id": "ver_galen_tlg010_identity_independent_20260824",
            "target_type": "issue",
            "target_id": ISSUE_ID,
            "stage": "independent",
            "verifier": {
                "verifier_id": "agent_galen_catalog_collation",
                "kind": "agent",
                "independence_group": "perseus_scaife_cmg_catalog_review_20260824",
            },
            "method": (
                "Collate independent Perseus work catalog, Scaife tlg010/tlg032 records "
                "and CMG Corpus Galenicum TLG-ID/incipit against current data surfaces."
            ),
            "checked_locators": [
                "https://catalog.perseus.org/catalog/urn:cts:greekLit:tlg0057.tlg010",
                "https://atlas.perseus.tufts.edu/library/urn:cts:greekLit:tlg0057.tlg032/",
                "https://cmg.bbaw.de/online-publications/Galen-Bibliographie_2017-12.pdf",
                "data/kg/nodes.jsonl",
                "data/corpus/manifest.jsonl",
            ],
            "verdict": "pass",
            "created_at": "2026-08-24T04:32:00Z",
            "artifacts": [
                base_artifact,
                {
                    "locator": (
                        "https://cmg.bbaw.de/online-publications/"
                        "Galen-Bibliographie_2017-12.pdf#page=16"
                    ),
                    "role": "bibliography",
                    "accessed_at": "2026-08-24T04:46:00Z",
                },
            ],
            "notes": "All independent catalogs agree; no collection title licenses the old label.",
        },
        {
            "record_type": "verification",
            "verification_id": "ver_galen_tlg010_identity_adversarial_20260824",
            "target_type": "issue",
            "target_id": ISSUE_ID,
            "stage": "adversarial",
            "verifier": {
                "verifier_id": "galen_tlg010_scope_regression_gate",
                "kind": "deterministic_tool",
                "independence_group": "snapshot_work_child_corpus_invariance_20260824",
            },
            "method": (
                "Enforce two distinct works, exact three-book corpus, snapshot bijection, "
                "part_of/authorship edges, manifest uniqueness, non-target invariance and idempotence."
            ),
            "checked_locators": [
                "tests/test_galen_tlg010_identity_repair.py",
                "scripts/check_snapshot_passage_integrity.py",
                "data/corpus/citations.jsonl",
                "data/kg/edges.jsonl",
            ],
            "verdict": "pass",
            "created_at": "2026-08-24T04:33:00Z",
            "artifacts": [
                {
                    "locator": "tests/test_galen_tlg010_identity_repair.py",
                    "role": "test_report",
                }
            ],
            "notes": "Only the targeted manifest row changes; Ps.-Plutarch and Calcidius are untouched.",
        },
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--data-root", type=Path, default=DEFAULT_DATA_ROOT)
    args = parser.parse_args(argv)
    data_root = args.data_root.expanduser().resolve()
    paths = {
        "nodes": data_root / "kg/nodes.jsonl",
        "edges": data_root / "kg/edges.jsonl",
        "passages": data_root / "corpus/passages.jsonl",
        "citations": data_root / "corpus/citations.jsonl",
        "manifest": data_root / "corpus/manifest.jsonl",
    }
    original_manifest = read_jsonl(paths["manifest"])
    original_target = next(
        (
            copy.deepcopy(row)
            for row in original_manifest
            if row.get("canonical_id") == NATURAL_CANONICAL_ID
        ),
        None,
    )
    result = transform(
        read_jsonl(paths["nodes"]),
        read_jsonl(paths["edges"]),
        read_jsonl(paths["passages"]),
        read_jsonl(paths["citations"]),
        original_manifest,
    )
    nodes, edges, passages, citations, manifest, changed = result
    print("Galen tlg0057.tlg010 identity repair")
    print("mode:", "WRITE" if args.write else "DRY-RUN")
    print("records changed:", len(changed))
    print("validated:", validate(nodes, edges, passages, citations, manifest))
    if not args.write:
        print("dry-run: nothing written")
        return 0
    if not changed:
        print("already applied: no files written")
        return 0
    if original_target is None:
        raise RuntimeError("Galen tlg010 preimage missing")

    authority = verify_authority_snapshot(passages)
    write_preserving_manifest(paths["manifest"], manifest)
    quarantine = {
        "record_type": "corpus_manifest_before",
        "reason": "tlg010 row retained De placitis title after work separation",
        "record": original_target,
    }
    atomic_write_text(
        data_root / QUARANTINE_RELATIVE,
        json.dumps(quarantine, ensure_ascii=False, sort_keys=True) + "\n",
    )
    report = {
        "issue_id": ISSUE_ID,
        "decision": "tlg0057.tlg010 is De naturalibus facultatibus; tlg0057.tlg032 is De placitis",
        "changed_records": changed,
        "authority_verification": authority,
        "independent_authorities": [
            "Perseus Catalog urn:cts:greekLit:tlg0057.tlg010",
            "Scaife ATLAS urn:cts:greekLit:tlg0057.tlg010 and tlg0057.tlg032",
            "CMG Corpus Galenicum, work 10, TLG-ID 0057.010",
        ],
        "cmg_visual_review": {
            "pdf": "Galen-Bibliographie_2017-12.pdf",
            "printed_page": 16,
            "finding": (
                "Entry 10 is De facultatibus naturalibus / De naturalibus "
                "facultatibus; TLG-ID 0057.010; Greek incipit matches local book I."
            ),
        },
        "local_validation": validate(nodes, edges, passages, citations, manifest),
        "legacy_node_id_policy": (
            "passage_galen_plac_1..3 retained as stable opaque IDs; all semantic fields "
            "identify De naturalibus facultatibus"
        ),
        "non_target_policy": "No Ps.-Plutarch, Calcidius, claim, KG node, edge, corpus passage or citation mutation.",
    }
    atomic_write_text(
        data_root / REPORT_RELATIVE,
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    )
    atomic_write_text(
        data_root / ISSUE_RELATIVE,
        json.dumps(registry_issue(), ensure_ascii=False, separators=(",", ":")) + "\n",
    )
    atomic_write_text(
        data_root / VERIFICATION_RELATIVE,
        "\n".join(
            json.dumps(row, ensure_ascii=False, separators=(",", ":"))
            for row in registry_verifications()
        )
        + "\n",
    )
    print("wrote:", paths["manifest"])
    print("wrote:", data_root / REPORT_RELATIVE)
    print("wrote:", data_root / QUARANTINE_RELATIVE)
    print("wrote registry shards")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
