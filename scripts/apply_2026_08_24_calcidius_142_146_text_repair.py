#!/usr/bin/env python3
"""Replace Calcidius In Timaeum 142-146 placeholders with verified Latin.

Source text is the checked 2005 CHMTL electronic transcription of Johann
Wrobel's public-domain 1876 edition, recovered from an immutable Internet
Archive snapshot.  Sections 142-146 were also visually collated against the
Google Books scan at printed pages 202-205 (PDF pages 231-234).

The repair distinguishes two genuine DigilibLT records (DLT000070 and the
later-edition record DLT000607) from the present CHMTL/Wrobel manifestation,
adopts the Perseus work identity
``urn:cts:latinLit:stoa0071b.stoa001``, and removes unsupported automatic school
memberships/classification.  Dry-run is the default; ``--write`` is explicit.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import tempfile
import unicodedata
import urllib.request
from collections.abc import Callable, Iterable
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_ROOT = ROOT / "data"

STAMP = "calcidius_142_146_text_repair_2026_08_24"
WORK_NODE = "work_calcidius_in_timaeum"
PERSON_NODE = "person_calcidius_4c_ce"
WORK_URN = "urn:cts:latinLit:stoa0071b.stoa001"
CATALOG_EDITION_URN = f"{WORK_URN}.opp-lat1"
MANIFEST_ID = "urn_cts_latinlit_stoa0071b_stoa001_wrobel1876_chmtl_lat"
CORRECT_DIGILIBLT_ID = "DLT000070"
OTHER_DIGILIBLT_ID = "DLT000607"
LEGACY_DIGILIBLT_MANIFEST_IDS = {
    "digiliblt:DLT000607",
    "digiliblt_dlt000607_lat",
}

SOURCE_TIMESTAMP = "20250321202539"
SOURCE_URL = (
    "https://web.archive.org/web/20250321202539id_/"
    "https://chmtl.indiana.edu/tml/3rd-5th/CHALTIM_TEXT.html"
)
SOURCE_SHA256 = "2a5003edb2ec4735ad9fd10e380eec5fc75af81566789a4482b0a180cf1e2879"
SOURCE_CREDIT = (
    "Thesaurus Musicarum Latinarum transcription prepared by Lisa Vest, "
    "checked by David Schneider and approved by Thomas J. Mathiesen (2005), "
    "from Wrobel 1876"
)

SCAN_VOLUME_ID = "fpVAJLZwKMgC"
SCAN_SHA256 = "c204c730d4c4d723f92dd0cf623ff0d08016c5893e3d476f4d4962df8dac3358"
SCAN_PAGE_COUNT = 445
SCAN_CATALOG_URL = f"https://books.google.com/books?id={SCAN_VOLUME_ID}"

SECTION_PAGES = {
    142: {"printed": "202", "pdf": "231"},
    143: {"printed": "203", "pdf": "232"},
    144: {"printed": "203-204", "pdf": "232-233"},
    145: {"printed": "204-205", "pdf": "233-234"},
    146: {"printed": "205", "pdf": "234"},
}

PASSAGE_IDS = {
    142: "11b8c41c-8dff-4d55-8845-7c9851faa90f",
    143: "80a1c7da-d510-43c5-9ef7-e31da2b117c3",
    144: "a0094051-4f1e-4c94-bf77-2e4690e8ea65",
    145: "8b4ee03b-8ecc-42b0-97ef-9cd93a16b971",
    146: "ba64e6bc-7c77-4162-b7cf-403be4427614",
}

NODE_IDS = {section: f"passage_calcid_{section}" for section in range(142, 147)}
TEXT_SET_SHA256 = "e13e2a82ed574543173a73e6c4a25390767a4b2a21187dd9baae60bb1c2a0e52"

REMOVED_SCHOOL_EDGES = {
    "9b3c625a-2469-40ab-baf7-c1886714e11a",  # auto member_of Academics
    "8a451d71-d54e-43b6-b396-4662283a1a25",  # auto member_of Neoplatonism
}

# These sections are Calcidius's commentary, even where they quote Plato.
# The edges were propagated from the formerly conflated Plato work.
REMOVED_FALSE_PLATO_AUTHOR_EDGES = {
    "6832e767-cc56-4171-ac32-1532378d76e4",
    "5251cef6-c447-41b4-8f66-6584c65f0c04",
    "40281ebe-37c6-42fd-a366-23d618e40625",
    "6a3e2381-c9ea-402d-9a2a-fbc236fca2d5",
    "cc0fb0cd-3c1f-4c54-bbd6-03dac738c30e",
}
REMOVED_UNSUPPORTED_EDGES = REMOVED_SCHOOL_EDGES | REMOVED_FALSE_PLATO_AUTHOR_EDGES

FOLLOWUP_QUARANTINE_RELATIVE = (
    "audit/2026-08-24_calcidius_142_146_independent_review_quarantine.jsonl"
)

ROMAN_TO_SECTION = {
    "CXLII": 142,
    "CXLIII": 143,
    "CXLIV": 144,
    "CXLV": 145,
    "CXLVI": 146,
}


class ParagraphParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.depth = 0
        self.current: list[str] = []
        self.paragraphs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        del attrs
        if tag.lower() == "p":
            if self.depth == 0:
                self.current = []
            self.depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() != "p" or self.depth == 0:
            return
        self.depth -= 1
        if self.depth == 0:
            self.paragraphs.append("".join(self.current))
            self.current = []

    def handle_data(self, data: str) -> None:
        if self.depth:
            self.current.append(data)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def node_id(node: dict[str, Any]) -> str:
    return str(node.get("node_id") or node.get("id") or "")


def edge_id(edge: dict[str, Any]) -> str:
    return str(edge.get("edge_id") or "")


def citation_key(row: dict[str, Any]) -> str:
    return "\x1f".join(
        (
            str(row.get("kg_node_id") or ""),
            str(row.get("passage_id") or ""),
            str(row.get("citation_type") or ""),
        )
    )


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


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", value)).strip()


def sha256_text(value: str) -> str:
    return hashlib.sha256(normalize_text(value).encode("utf-8")).hexdigest()


def section_set_digest(sections: dict[int, str]) -> str:
    payload = "\n".join(f"{section}\t{sections[section]}" for section in sorted(sections))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def parse_source_html(raw: bytes) -> dict[int, str]:
    parser = ParagraphParser()
    parser.feed(raw.decode("utf-8"))
    sections: dict[int, str] = {}
    roman_pattern = "|".join(sorted(ROMAN_TO_SECTION, key=len, reverse=True))
    for paragraph in parser.paragraphs:
        text = normalize_text(paragraph)
        text = re.sub(r"^\[(?:202|203|204|205)\]\s*", "", text)
        match = re.match(rf"^({roman_pattern})\.\s*(.*)$", text)
        if not match:
            continue
        section = ROMAN_TO_SECTION[match.group(1)]
        body = re.sub(r"\s*\[(?:202|203|204|205)\]\s*", " ", match.group(2))
        sections[section] = normalize_text(body)
    if set(sections) != set(range(142, 147)):
        raise RuntimeError(f"CHMTL source sections differ from 142-146: {sorted(sections)}")
    if section_set_digest(sections) != TEXT_SET_SHA256:
        raise RuntimeError("CHMTL Calcidius 142-146 text digest mismatch")
    return sections


def fetch_source_sections() -> dict[int, str]:
    request = urllib.request.Request(
        SOURCE_URL,
        headers={"User-Agent": "EleutherIA-SOTA-source-repair/1.0"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:  # noqa: S310
        raw = response.read()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != SOURCE_SHA256:
        raise RuntimeError(f"CHMTL archive SHA-256 mismatch: {digest}")
    return parse_source_html(raw)


def make_passage(section: int, text: str) -> dict[str, Any]:
    pages = SECTION_PAGES[section]
    return {
        "authority_edition_urn": CATALOG_EDITION_URN,
        "canonical_ref": f"In Tim. {section}",
        "cts_urn": f"{WORK_URN}:{section}",
        "electronic_source_credit": SOURCE_CREDIT,
        "language": "lat",
        "passage_id": PASSAGE_IDS[section],
        "passage_role": "original",
        "pdf_page_range": pages["pdf"],
        "printed_page_range": pages["printed"],
        "scan_page_map_visually_verified": True,
        "scan_sha256": SCAN_SHA256,
        "scan_volume_id": SCAN_VOLUME_ID,
        "sequence_number": section,
        "source_artifact_sha256": SOURCE_SHA256,
        "source_archive_timestamp": SOURCE_TIMESTAMP,
        "source_url": SOURCE_URL,
        "text_content": text,
        "text_sha256": sha256_text(text),
        "work_canonical_id": MANIFEST_ID,
        "work_urn": WORK_URN,
    }


def make_manifest() -> dict[str, Any]:
    return {
        "alternate_identifiers": {
            "digiliblt": CORRECT_DIGILIBLT_ID,
            "digiliblt_later_edition_record": OTHER_DIGILIBLT_ID,
            "dll_author": "a4544",
            "phi_author": "phi2028",
        },
        "artifact_sha256": SOURCE_SHA256,
        "artifact_status": "archived_verified",
        "author": "Calcidius (Chalcidius)",
        "authority_edition_urn": CATALOG_EDITION_URN,
        "canonical_id": MANIFEST_ID,
        "cts_urn": WORK_URN,
        "digiliblt_identity_note": (
            "DLT000070 and DLT000607 are distinct Calcidius records. The current "
            "manifestation is independently sourced from CHMTL/Wrobel 1876."
        ),
        "edition": "Johann Wrobel (ed.), Platonis Timaeus interprete Chalcidio cum eiusdem commentario, Teubner, 1876",
        "ingest_class": "checked_electronic_transcription_with_visual_scan_collation",
        "language": "lat",
        "license": "CHMTL transcription source credit retained; Wrobel 1876 public domain",
        "passages": 5,
        "period": "Late Antiquity",
        "scan_catalog_url": SCAN_CATALOG_URL,
        "scan_page_count": SCAN_PAGE_COUNT,
        "scan_sha256": SCAN_SHA256,
        "source": SOURCE_URL,
        "source_archive_timestamp": SOURCE_TIMESTAMP,
        "source_credit": SOURCE_CREDIT,
        "source_publication_year": 1876,
        "status": "in_corpus",
        "title": "Commentarius in Platonis Timaeum, sections 142-146",
        "work_urn": WORK_URN,
    }


def is_legacy_manifest(row: dict[str, Any]) -> bool:
    canonical = str(row.get("canonical_id") or "")
    return canonical in LEGACY_DIGILIBLT_MANIFEST_IDS or canonical == MANIFEST_ID


def current_state(
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    passages: list[dict[str, Any]],
    citations: list[dict[str, Any]],
    manifest: list[dict[str, Any]],
) -> bool:
    by_node = {node_id(node): node for node in nodes}
    corpus = [row for row in passages if row.get("work_canonical_id") == MANIFEST_ID]
    manifestations = [row for row in manifest if row.get("canonical_id") == MANIFEST_ID]
    snapshots = [
        row
        for row in citations
        if row.get("kg_node_id") in set(NODE_IDS.values())
        and row.get("citation_type") == "snapshot_passage_node"
    ]
    return (
        len(corpus) == 5
        and len(manifestations) == 1
        and len(snapshots) == 5
        and all(node_id_value in by_node for node_id_value in NODE_IDS.values())
        and metadata(by_node.get(WORK_NODE, {})).get("canonical_id") == WORK_URN
        and metadata(by_node.get(PERSON_NODE, {})).get("classification_status")
        == "platonist_author_exact_school_and_religious_affiliation_disputed"
        and by_node.get(PERSON_NODE, {}).get("school") in {None, ""}
        and not any(edge_id(edge) in REMOVED_SCHOOL_EDGES for edge in edges)
        and not any("to be fetched from digilibLT" in str(row) for row in passages)
        and not any(
            legacy in str(row.get("canonical_id") or "")
            for row in manifest
            for legacy in LEGACY_DIGILIBLT_MANIFEST_IDS
        )
    )


def apply_independent_followup(
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    manifest: list[dict[str, Any]],
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[str],
]:
    """Apply only defects demonstrated by the independent source review."""

    quarantine: list[dict[str, Any]] = []
    changed: list[str] = []
    by_node = {node_id(node): node for node in nodes}
    for _section, wanted_node_id in NODE_IDS.items():
        node = by_node[wanted_node_id]
        data = metadata(node)
        wanted_chars = len(str(node.get("description") or ""))
        wanted_words = len(str(node.get("description") or "").split())
        if (
            data.get("char_length") == wanted_chars
            and data.get("word_count") == wanted_words
            and "school" not in data
            and "doxographical_source" not in data
            and "doxographical_confidence" not in data
            and node.get("school") in {None, ""}
        ):
            continue
        quarantine.append(
            {
                "record_type": "kg_node_before",
                "reason": "stale placeholder counts and unsupported school metadata",
                "record": copy.deepcopy(node),
            }
        )
        data["char_length"] = wanted_chars
        data["word_count"] = wanted_words
        data.pop("school", None)
        data.pop("doxographical_source", None)
        data.pop("doxographical_confidence", None)
        set_metadata(node, data)
        node["school"] = None
        node["updated_at"] = "2026-08-24 04:40:00+00:00"
        changed.append("normalize_passage_metadata:" + wanted_node_id)

    work_node = by_node[WORK_NODE]
    work_data = metadata(work_node)
    wanted_identifiers = {
        "dll_catalog_linked_record": CORRECT_DIGILIBLT_ID,
        "digiliblt_later_edition_record": OTHER_DIGILIBLT_ID,
    }
    if (
        work_data.get("digiliblt_identifiers") != wanted_identifiers
        or work_data.get("digiliblt_id_status")
        != "distinct valid catalog/edition records; neither identifies this CHMTL/Wrobel manifestation"
    ):
        quarantine.append(
            {
                "record_type": "kg_node_before",
                "reason": "DigilibLT records were incorrectly treated as one right and one false identity",
                "record": copy.deepcopy(work_node),
            }
        )
        work_data["digiliblt_identifiers"] = wanted_identifiers
        work_data["digiliblt_id_status"] = (
            "distinct valid catalog/edition records; neither identifies this "
            "CHMTL/Wrobel manifestation"
        )
        set_metadata(work_node, work_data)
        work_node["updated_at"] = "2026-08-24 04:40:00+00:00"
        changed.append("clarify_digiliblt_records:" + WORK_NODE)

    retained_edges: list[dict[str, Any]] = []
    for edge in edges:
        if edge_id(edge) not in REMOVED_FALSE_PLATO_AUTHOR_EDGES:
            retained_edges.append(edge)
            continue
        if not (
            edge.get("relation") == "authored_by"
            and str(edge.get("source") or edge.get("source_id") or "")
            in set(NODE_IDS.values())
            and str(edge.get("target") or edge.get("target_id") or "")
            == "person_plato_428_348bce_a1b2c3d4"
        ):
            raise RuntimeError("expected false Plato-authorship edge changed shape")
        quarantine.append(
            {
                "record_type": "kg_edge",
                "reason": "Calcidius commentary section falsely attributed to Plato",
                "record": edge,
            }
        )
        changed.append("remove_false_plato_authorship:" + edge_id(edge))
    edges = retained_edges

    manifestations = [row for row in manifest if row.get("canonical_id") == MANIFEST_ID]
    if len(manifestations) != 1:
        raise RuntimeError("Calcidius manifestation missing during independent follow-up")
    manifestation = manifestations[0]
    alternate = copy.deepcopy(manifestation.get("alternate_identifiers") or {})
    if alternate.get("digiliblt_later_edition_record") != OTHER_DIGILIBLT_ID:
        quarantine.append(
            {
                "record_type": "manifest_before",
                "reason": "distinct later DigilibLT edition record was omitted",
                "record": copy.deepcopy(manifestation),
            }
        )
        alternate["digiliblt_later_edition_record"] = OTHER_DIGILIBLT_ID
        manifestation["alternate_identifiers"] = alternate
        manifestation["digiliblt_identity_note"] = (
            "DLT000070 and DLT000607 are distinct Calcidius records. The current "
            "manifestation is independently sourced from CHMTL/Wrobel 1876."
        )
        changed.append("clarify_manifest_digiliblt_records:" + MANIFEST_ID)

    return nodes, edges, manifest, quarantine, changed


def transform(
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    passages: list[dict[str, Any]],
    citations: list[dict[str, Any]],
    manifest: list[dict[str, Any]],
    source_sections: dict[int, str] | None = None,
) -> tuple[
    list[dict[str, Any]],
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
    followup_changed: list[str] = []
    by_node_before = {node_id(node): node for node in nodes}
    person_before = by_node_before.get(PERSON_NODE)
    if person_before is not None and person_before.get("school") not in {None, ""}:
        person_before["school"] = None
        person_before["updated_at"] = "2026-08-24 00:00:00+00:00"
        followup_changed.append("clear_off_scheme_school:" + PERSON_NODE)
    if current_state(nodes, edges, passages, citations, manifest):
        nodes, edges, manifest, followup_quarantine, independent_changed = (
            apply_independent_followup(nodes, edges, manifest)
        )
        followup_changed.extend(independent_changed)
        validate(nodes, edges, passages, citations, manifest)
        return (
            nodes,
            edges,
            passages,
            citations,
            manifest,
            followup_quarantine,
            followup_changed,
        )

    sections = {
        section: normalize_text(text)
        for section, text in (source_sections or fetch_source_sections()).items()
    }
    if set(sections) != set(range(142, 147)) or section_set_digest(sections) != TEXT_SET_SHA256:
        raise RuntimeError("supplied Calcidius source sections are incomplete or changed")

    changed: list[str] = []
    quarantine: list[dict[str, Any]] = []
    by_node = {node_id(node): node for node in nodes}

    for section, wanted_node_id in NODE_IDS.items():
        node = by_node.get(wanted_node_id)
        if node is None:
            raise RuntimeError(f"missing Calcidius passage node: {wanted_node_id}")
        quarantine.append(
            {"record_type": "kg_node_before", "reason": "placeholder replaced with verified Latin", "record": copy.deepcopy(node)}
        )
        passage = make_passage(section, sections[section])
        data = metadata(node)
        data.update(
            {
                "authority_edition_urn": CATALOG_EDITION_URN,
                "canonical_ref": passage["canonical_ref"],
                "char_length": len(sections[section]),
                "citability": "citable",
                "cts_urn": passage["cts_urn"],
                "db_passage_id": passage["passage_id"],
                "edition": make_manifest()["edition"],
                "language": "lat",
                "passage_id": passage["passage_id"],
                "passage_role": "original",
                "pdf_page_range": passage["pdf_page_range"],
                "printed_page_range": passage["printed_page_range"],
                "primary_text_status": "checked_public_domain_edition_transcription",
                "scan_page_map_visually_verified": True,
                "scan_sha256": SCAN_SHA256,
                "source_artifact_sha256": SOURCE_SHA256,
                "source_url": SOURCE_URL,
                "text_sha256": passage["text_sha256"],
                "word_count": len(sections[section].split()),
                "work_canonical_id": WORK_URN,
                "work_id": WORK_NODE,
                STAMP: True,
            }
        )
        data.pop("auto_generated", None)
        data.pop("school", None)
        data.pop("doxographical_source", None)
        data.pop("doxographical_confidence", None)
        set_metadata(node, data)
        node["description"] = sections[section]
        node["label"] = f"Calcidius, In Timaeum {section} (Wrobel 1876)"
        node["school"] = None
        node["updated_at"] = "2026-08-24 00:00:00+00:00"
        changed.append("node:" + wanted_node_id)

    work_node = by_node.get(WORK_NODE)
    if work_node is None:
        raise RuntimeError("missing Calcidius work node")
    quarantine.append(
        {"record_type": "kg_node_before", "reason": "work identity corrected", "record": copy.deepcopy(work_node)}
    )
    work_data = metadata(work_node)
    work_data.update(
        {
            "author": "Calcidius (Chalcidius)",
            "canonical_id": WORK_URN,
            "catalog_edition_urn": CATALOG_EDITION_URN,
            "digiliblt_id": CORRECT_DIGILIBLT_ID,
            "digiliblt_identifiers": {
                "dll_catalog_linked_record": CORRECT_DIGILIBLT_ID,
                "digiliblt_later_edition_record": OTHER_DIGILIBLT_ID,
            },
            "digiliblt_id_status": (
                "distinct valid catalog/edition records; neither identifies this "
                "CHMTL/Wrobel manifestation"
            ),
            "language": "lat",
            "source_artifact_sha256": SOURCE_SHA256,
            "source_scan_sha256": SCAN_SHA256,
            "work_canonical_id": WORK_URN,
            STAMP: True,
        }
    )
    work_data.pop("db_work_id", None)
    work_data.pop("ingestion_debt_2026_08_17_canonical_derived", None)
    set_metadata(work_node, work_data)
    work_node["description"] = (
        "Calcidius (Chalcidius), Commentarius in Platonis Timaeum, a Late Antique "
        "Latin translation-commentary conventionally dated to the fourth century, "
        "although the author's precise date, religious affiliation and philosophical "
        "classification remain disputed. The current evidence cohort is Wrobel 1876, "
        "sections 142-146, checked against printed pages 202-205."
    )
    work_node["updated_at"] = "2026-08-24 00:00:00+00:00"
    changed.append("node:" + WORK_NODE)

    person_node = by_node.get(PERSON_NODE)
    if person_node is None:
        raise RuntimeError("missing Calcidius person node")
    quarantine.append(
        {"record_type": "kg_node_before", "reason": "unsupported school/religion classification corrected", "record": copy.deepcopy(person_node)}
    )
    person_data = metadata(person_node)
    person_data.update(
        {
            "dates": "conventionally 4th century CE; exact dating disputed",
            "classification_status": "platonist_author_exact_school_and_religious_affiliation_disputed",
            "authority_identifiers": {
                "dll": "a4544",
                "viaf": "266558598",
                "phi": "phi2028",
                "digiliblt": "AUT000033",
            },
            STAMP: True,
        }
    )
    person_data.pop("school", None)
    set_metadata(person_node, person_data)
    person_node["description"] = (
        "Calcidius (Chalcidius) is the Late Antique Latin translator and commentator "
        "of Plato's Timaeus. He is conventionally placed in the fourth century, but "
        "his precise date, religious affiliation and exact Platonist classification "
        "remain disputed; the KG therefore does not assert Christian or Neoplatonist "
        "membership as fact."
    )
    person_node["school"] = None
    person_node["updated_at"] = "2026-08-24 00:00:00+00:00"
    changed.append("node:" + PERSON_NODE)

    retained_edges: list[dict[str, Any]] = []
    for edge in edges:
        if edge_id(edge) in REMOVED_UNSUPPORTED_EDGES:
            quarantine.append(
                {
                    "record_type": "kg_edge",
                    "reason": (
                        "unsupported automatic school membership"
                        if edge_id(edge) in REMOVED_SCHOOL_EDGES
                        else "Calcidius commentary section falsely attributed to Plato"
                    ),
                    "record": edge,
                }
            )
            changed.append("remove_edge:" + edge_id(edge))
            continue
        retained_edges.append(edge)
    edges = retained_edges

    retained_passages: list[dict[str, Any]] = []
    target_uuid_set = set(PASSAGE_IDS.values())
    for row in passages:
        if str(row.get("passage_id") or "") in target_uuid_set:
            quarantine.append(
                {"record_type": "corpus_passage", "reason": "placeholder replaced with verified Latin", "record": row}
            )
            changed.append("passage:" + str(row.get("passage_id")))
            continue
        retained_passages.append(row)
    retained_passages.extend(make_passage(section, sections[section]) for section in range(142, 147))
    passages = retained_passages

    retained_citations: list[dict[str, Any]] = []
    target_node_set = set(NODE_IDS.values())
    for row in citations:
        if str(row.get("kg_node_id") or "") in target_node_set:
            quarantine.append(
                {"record_type": "citation", "reason": "Calcidius exact snapshot rebuilt", "record": row}
            )
            changed.append("remove_citation:" + citation_key(row))
            continue
        retained_citations.append(row)
    for section, wanted_node_id in NODE_IDS.items():
        retained_citations.append(
            {
                "citation_type": "snapshot_passage_node",
                "confidence": 1.0,
                "kg_node_id": wanted_node_id,
                "passage_id": PASSAGE_IDS[section],
                "source_release": SOURCE_TIMESTAMP,
            }
        )
    citations = retained_citations

    retained_manifest: list[dict[str, Any]] = []
    for row in manifest:
        if is_legacy_manifest(row):
            quarantine.append(
                {"record_type": "manifest", "reason": "wrong DLT identity and placeholder cohort replaced", "record": row}
            )
            changed.append("manifest:" + str(row.get("canonical_id") or ""))
            continue
        retained_manifest.append(row)
    retained_manifest.append(make_manifest())
    manifest = retained_manifest

    validate(nodes, edges, passages, citations, manifest)
    quarantine.sort(
        key=lambda row: (
            str(row.get("record_type") or ""),
            json.dumps(row.get("record"), ensure_ascii=False, sort_keys=True),
        )
    )
    return nodes, edges, passages, citations, manifest, quarantine, changed


def validate(
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    passages: list[dict[str, Any]],
    citations: list[dict[str, Any]],
    manifest: list[dict[str, Any]],
) -> None:
    by_node = {node_id(node): node for node in nodes}
    by_passage = {str(row.get("passage_id") or ""): row for row in passages}
    if len(by_node) != len(nodes) or len(by_passage) != len(passages):
        raise RuntimeError("duplicate node or passage id after Calcidius repair")

    corpus = [row for row in passages if row.get("work_canonical_id") == MANIFEST_ID]
    if len(corpus) != 5 or {row.get("sequence_number") for row in corpus} != set(range(142, 147)):
        raise RuntimeError("Calcidius corpus is not exactly sections 142-146")
    section_texts = {int(row["sequence_number"]): normalize_text(row["text_content"]) for row in corpus}
    if section_set_digest(section_texts) != TEXT_SET_SHA256:
        raise RuntimeError("Calcidius current text digest is not the checked cohort")

    for section, wanted_node_id in NODE_IDS.items():
        node = by_node.get(wanted_node_id)
        passage = by_passage[PASSAGE_IDS[section]]
        if node is None or normalize_text(str(node.get("description") or "")) != normalize_text(
            str(passage.get("text_content") or "")
        ):
            raise RuntimeError(f"Calcidius exact twin mismatch: {wanted_node_id}")
        data = metadata(node)
        if (
            data.get("db_passage_id") != PASSAGE_IDS[section]
            or data.get("citability") != "citable"
            or data.get("passage_role") != "original"
            or data.get("text_sha256") != sha256_text(str(node.get("description") or ""))
            or data.get("scan_page_map_visually_verified") is not True
            or data.get("char_length") != len(str(node.get("description") or ""))
            or data.get("word_count")
            != len(str(node.get("description") or "").split())
            or data.get("school")
            or data.get("doxographical_source")
            or data.get("doxographical_confidence")
            or node.get("school") not in {None, ""}
        ):
            raise RuntimeError(f"Calcidius node provenance incomplete: {wanted_node_id}")

    snapshots = {
        str(row.get("kg_node_id")): str(row.get("passage_id"))
        for row in citations
        if row.get("citation_type") == "snapshot_passage_node"
        and str(row.get("kg_node_id") or "") in set(NODE_IDS.values())
    }
    if snapshots != {NODE_IDS[section]: PASSAGE_IDS[section] for section in range(142, 147)}:
        raise RuntimeError("Calcidius snapshot citations are incomplete")

    work_data = metadata(by_node.get(WORK_NODE, {}))
    if (
        work_data.get("canonical_id") != WORK_URN
        or work_data.get("digiliblt_id") != CORRECT_DIGILIBLT_ID
        or work_data.get("catalog_edition_urn") != CATALOG_EDITION_URN
    ):
        raise RuntimeError("Calcidius work identity remains wrong")
    person_data = metadata(by_node.get(PERSON_NODE, {}))
    if person_data.get("classification_status") != (
        "platonist_author_exact_school_and_religious_affiliation_disputed"
    ):
        raise RuntimeError("Calcidius person classification remains overconfident")
    if by_node.get(PERSON_NODE, {}).get("school") not in {None, ""}:
        raise RuntimeError("Calcidius person uses an unsupported school vocabulary value")
    if any(edge_id(edge) in REMOVED_UNSUPPORTED_EDGES for edge in edges):
        raise RuntimeError("unsupported Calcidius school or authorship edge remains")
    for section, wanted_node_id in NODE_IDS.items():
        authored_by = {
            str(edge.get("target") or edge.get("target_id") or "")
            for edge in edges
            if edge.get("relation") == "authored_by"
            and str(edge.get("source") or edge.get("source_id") or "")
            == wanted_node_id
        }
        if authored_by != {PERSON_NODE}:
            raise RuntimeError(
                f"Calcidius {section} authorship is not uniquely Calcidius: "
                f"{sorted(authored_by)}"
            )

    current_manifest = [row for row in manifest if row.get("canonical_id") == MANIFEST_ID]
    if len(current_manifest) != 1:
        raise RuntimeError("Calcidius exact manifestation is missing or duplicated")
    row = current_manifest[0]
    if (
        row.get("artifact_sha256") != SOURCE_SHA256
        or row.get("scan_sha256") != SCAN_SHA256
        or row.get("alternate_identifiers", {}).get("digiliblt") != CORRECT_DIGILIBLT_ID
        or row.get("alternate_identifiers", {}).get(
            "digiliblt_later_edition_record"
        )
        != OTHER_DIGILIBLT_ID
        or row.get("passages") != 5
    ):
        raise RuntimeError("Calcidius manifestation is not reproducibly fingerprinted")

    serialized_current = "\n".join(json.dumps(row, ensure_ascii=False) for row in corpus + current_manifest)
    if "to be fetched from digilibLT" in serialized_current:
        raise RuntimeError("Calcidius placeholder text remains")
    if any(
        legacy in str(row.get("canonical_id") or "")
        for row in current_manifest
        for legacy in LEGACY_DIGILIBLT_MANIFEST_IDS
    ):
        raise RuntimeError("legacy DigilibLT id remains the current manifestation id")


def write_preserving(
    path: Path,
    rows: list[dict[str, Any]],
    key: Callable[[dict[str, Any]], str],
) -> None:
    original = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    desired = {key(row): row for row in rows}
    if len(desired) != len(rows):
        raise RuntimeError(f"duplicate identity in {path}")
    seen: set[str] = set()
    output: list[str] = []
    for line in original:
        old = json.loads(line)
        wanted = key(old)
        if wanted not in desired:
            continue
        new = desired[wanted]
        compact = ": " not in line
        output.append(
            line
            if old == new
            else json.dumps(
                new,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":") if compact else None,
            )
        )
        seen.add(wanted)
    for wanted in sorted(desired.keys() - seen):
        compact = path.name in {"passages.jsonl", "citations.jsonl", "manifest.jsonl"}
        output.append(
            json.dumps(
                desired[wanted],
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":") if compact else None,
            )
        )
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        tmp = Path(handle.name)
        handle.write("\n".join(output) + "\n")
    tmp.replace(path)


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        tmp = Path(handle.name)
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    tmp.replace(path)


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
    result = transform(
        read_jsonl(paths["nodes"]),
        read_jsonl(paths["edges"]),
        read_jsonl(paths["passages"]),
        read_jsonl(paths["citations"]),
        read_jsonl(paths["manifest"]),
    )
    nodes, edges, passages, citations, manifest, quarantine, changed = result
    print("Calcidius In Timaeum 142-146 text repair")
    print("mode:", "WRITE" if args.write else "DRY-RUN")
    print("records changed:", len(changed))
    print("records quarantined:", len(quarantine))
    if not args.write:
        print("dry-run: nothing written")
        return 0
    if not changed:
        print("already applied: no files written")
        return 0

    write_preserving(paths["nodes"], nodes, node_id)
    write_preserving(paths["edges"], edges, edge_id)
    write_preserving(paths["passages"], passages, lambda row: str(row.get("passage_id") or ""))
    write_preserving(paths["citations"], citations, citation_key)
    write_preserving(paths["manifest"], manifest, lambda row: str(row.get("canonical_id") or ""))

    quarantine_path = data_root / "audit/2026-08-24_calcidius_142_146_quarantine.jsonl"
    followup_quarantine_path = data_root / FOLLOWUP_QUARANTINE_RELATIVE
    primary_quarantine_exists = quarantine_path.exists()
    if quarantine:
        if primary_quarantine_exists:
            if followup_quarantine_path.exists():
                raise RuntimeError("refusing to overwrite independent-review quarantine")
            write_jsonl(followup_quarantine_path, quarantine)
        else:
            write_jsonl(quarantine_path, quarantine)
    elif not primary_quarantine_exists:
        write_jsonl(quarantine_path, quarantine)
    report = {
        "authority_edition_urn": CATALOG_EDITION_URN,
        "changed_records": len(changed),
        "correct_digiliblt_id": CORRECT_DIGILIBLT_ID,
        "digiliblt_identifiers": {
            "dll_catalog_linked_record": CORRECT_DIGILIBLT_ID,
            "digiliblt_later_edition_record": OTHER_DIGILIBLT_ID,
            "status": (
                "distinct valid catalog/edition records; current manifestation "
                "is CHMTL/Wrobel"
            ),
        },
        "passage_sections": list(range(142, 147)),
        "quarantined_records": len(quarantine),
        "scan": {
            "catalog_url": SCAN_CATALOG_URL,
            "page_count": SCAN_PAGE_COUNT,
            "page_map": SECTION_PAGES,
            "sha256": SCAN_SHA256,
            "visually_verified": True,
        },
        "source": {
            "archive_timestamp": SOURCE_TIMESTAMP,
            "credit": SOURCE_CREDIT,
            "sha256": SOURCE_SHA256,
            "url": SOURCE_URL,
        },
        "independent_review": {
            "reviewer": "agent_ancient_source_coverage",
            "verdict": "pass_after_minimal_followup_patch",
            "wayback_source_redownloaded_sha256": SOURCE_SHA256,
            "wrobel_pages_visually_inspected": "202-205",
            "findings_repaired": [
                "stale placeholder character/word counts",
                "unsupported Middle Platonist passage labels",
                "five false Plato authored_by edges",
                "DLT000607 incorrectly described as a false identity rather than a distinct edition record",
            ],
        },
        "status": (
            "primary repair independently reviewed and patched; ready for registry adjudication"
        ),
        "text_set_sha256": TEXT_SET_SHA256,
        "legacy_manifest_id": "digiliblt_dlt000607_lat",
        "work_urn": WORK_URN,
    }
    report_path = data_root / "audit/2026-08-24_calcidius_142_146_text_repair.json"
    if report_path.exists():
        previous = json.loads(report_path.read_text(encoding="utf-8"))
        if primary_quarantine_exists:
            report["quarantined_records"] = previous.get("quarantined_records", 0)
        report["followup_records_changed"] = len(changed)
    if quarantine and primary_quarantine_exists:
        report["independent_review_followup"] = {
            "quarantine": str(followup_quarantine_path.relative_to(data_root.parent)),
            "quarantined_records": len(quarantine),
            "repairs": [
                "fresh char_length and word_count",
                "remove unsupported passage school labels",
                "remove five false Plato authored_by edges",
                "distinguish DLT000070 and DLT000607",
            ],
        }
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        "wrote:",
        *paths.values(),
        followup_quarantine_path if primary_quarantine_exists else quarantine_path,
        report_path,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
