#!/usr/bin/env python3
"""Replace the mixed Ps.-Plutarch De fato corpus with pinned Perseus texts.

The legacy slice combined one complete twelve-section Greek extraction, a
second truncated twelve-section copy, and nineteen machine-generated English
analytical records carrying the foreign/invented CTS identity
``tlg9857.tlg062:1.1``.  It also exposed analytical KG dossiers as exact
snapshot passage nodes.

This repair keeps the already exact Greek UUIDs, ingests the published 1874
English translation as a distinct manifestation, creates exact KG snapshots
for the twelve CTS sections in each language, and quarantines the truncated,
machine-generated and false-twin records.  The older nineteen analytical
dossiers remain useful navigation objects but are explicitly non-citable and
have only ``related_passage_non_exact`` links.

The source XML is fetched only for the initial repair.  Both URLs are pinned to
one upstream commit and checked byte-for-byte against declared SHA-256 values
before parsing.  Once applied, validation and idempotence are offline.
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
import uuid
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_ROOT = ROOT / "data"

STAMP = "ps_plutarch_de_fato_text_repair_2026_08_24"
WORK_NODE = "work_plutarch_de_fato_complete"
AUTHOR_NODE = "person_pseudo_plutarch_2c_ce"
GENUINE_PLUTARCH_NODE = "person_plutarch_45_120ce_b9c2a8f3"
WORK_URN = "urn:cts:greekLit:tlg0007.tlg108"
GRC_MANIFEST_ID = "urn_cts_greeklit_tlg0007_tlg108_grc"
ENG_MANIFEST_ID = "urn_cts_greeklit_tlg0007_tlg108_eng"
GRC_VERSION = f"{WORK_URN}.perseus-grc2"
ENG_VERSION = f"{WORK_URN}.perseus-eng2"

UPSTREAM_COMMIT = "a065c359aab33c33bd17ddc2cac7d27fdc9cd870"
UPSTREAM_ROOT = (
    "https://raw.githubusercontent.com/PerseusDL/canonical-greekLit/"
    f"{UPSTREAM_COMMIT}/data/tlg0007/tlg108"
)
SOURCE_ARTIFACTS = {
    "grc": {
        "url": f"{UPSTREAM_ROOT}/tlg0007.tlg108.perseus-grc2.xml",
        "sha256": "4ee1c5ec029b0a2d93f426008573f1613842611c25c1c8f0fc311ef867952bd5",
        "version_urn": GRC_VERSION,
        "manifest_id": GRC_MANIFEST_ID,
        "language": "grc",
        "passage_role": "original",
        "edition": "Gregorios N. Bernardakis (ed.), Plutarchi Chaeronensis Moralia III, Teubner, 1891",
        "translator": None,
    },
    "eng": {
        "url": f"{UPSTREAM_ROOT}/tlg0007.tlg108.perseus-eng2.xml",
        "sha256": "62c2511190f70c204285a70f7f8f03703dfe12739516ca716c586f03c666828e",
        "version_urn": ENG_VERSION,
        "manifest_id": ENG_MANIFEST_ID,
        "language": "eng",
        "passage_role": "translation",
        "edition": "Plutarch's Morals V, William W. Goodwin (ed.), Little, Brown, 1874",
        "translator": "A. G. (as credited in the edition)",
    },
}

SECTION_SET_DIGESTS = {
    "grc": "a6b039b4a470355c7be21834334ace2fa62fec982d7926bd63e8f1d4735fadbd",
    "eng": "201b6608fa98dbbb4675d535960069af8a161ddd625cc4a5296c21b54c2d7bfd",
}

# Independently checked against the Stephanus milestones in the pinned Greek
# TEI.  This is a transcription table, not an inferred PDF concordance.
SECTION_STEPHANUS = {
    0: "568B–C",
    1: "568D–E",
    2: "568F",
    3: "569A–D",
    4: "569E–570B",
    5: "570C–E",
    6: "570F–571E",
    7: "571F–572E",
    8: "572F",
    9: "573A–574A",
    10: "574B–D",
    11: "574E–F",
}

GOOD_GREEK_UUIDS = {
    0: "bb77c929-a184-4ed6-a151-dcaae0f9c8ca",
    1: "c52dd6fb-b3a5-408b-a2d0-7a4f0e6b4117",
    2: "1ff2e855-0550-4906-a5eb-e38ab2aa6550",
    3: "4edfbd91-c78b-473a-a942-590912277595",
    4: "f31dc55d-6240-48eb-8017-4155e1b92978",
    5: "27229be5-146e-44b3-9635-b2aaeab917d2",
    6: "15cd3c13-ae01-43e2-b89f-724c52ac3894",
    7: "cfe568f8-fbeb-4ee9-bc6e-5f95bd08b445",
    8: "821bd3e4-c529-4553-9665-5b920143a140",
    9: "f7ce09d8-54e2-4ff0-9606-2421badd2018",
    10: "0b6bfaef-6e09-481f-babb-b918b83c9597",
    11: "9032ce99-10c6-4a59-941b-2e0f915e7069",
}

LEGACY_CORPUS_IDS = {
    "urn:cts:greekLit:tlg0007.tlg108",
    "urn_cts_greeklit_tlg0007_tlg108_grc",
    "urn_cts_greeklit_tlg0007_tlg099_eng",
}

LEGACY_CITATION_REMAP = {
    # Truncated duplicate Greek section 9 -> exact pinned Greek section 9.
    "664e54e0-4843-4a75-b431-e88be3733189": GOOD_GREEK_UUIDS[9],
    # Truncated duplicate Greek section 10 -> exact pinned Greek section 10.
    "8d7f87bf-2fe3-4875-8d30-cbdd47deafda": GOOD_GREEK_UUIDS[10],
    # Machine fine-section 17 covers the third-providence material in canonical
    # CTS section 10 -> published 1874 English section 10.
    "97041f33-3aee-585d-88f2-979341a59e68": str(
        uuid.uuid5(uuid.NAMESPACE_URL, f"{ENG_VERSION}:10")
    ),
}

# The three analytical dossiers that carry a primary_attestation align through
# their reviewed related_passage_non_exact citation to these exact CTS sections.
ANALYTICAL_PRIMARY_SECTION = {4: 3, 7: 6, 11: 7}

EXACT_NODE_RE = re.compile(r"^passage_ps_plutarch_de_fato_(grc|eng)_(\d+)$")
ANALYTICAL_NODE_RE = re.compile(r"^passage_plut_fat_(\d+)$")
REMOVED_NODE_RE = re.compile(r"^passage_plut_fat_(?:\d+_en|\d+_s\d+)$")
XML_SKIP = {"note", "pb", "milestone"}


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


def nfc_text(value: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", value)).strip()


def sha256_text(value: str) -> str:
    return hashlib.sha256(nfc_text(value).encode("utf-8")).hexdigest()


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def collect_reading_text(element: ET.Element) -> list[str]:
    """Render a reading text while excluding apparatus and preserving gaps."""
    output: list[str] = []
    if element.text:
        output.append(element.text)
    for child in element:
        name = local_name(child.tag)
        if name == "gap":
            output.append("[...]")
        elif name not in XML_SKIP:
            output.extend(collect_reading_text(child))
        if child.tail:
            output.append(child.tail)
    return output


def section_set_digest(sections: dict[int, str]) -> str:
    payload = "\n".join(f"{number}\t{sections[number]}" for number in sorted(sections))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def fetch_source_sections() -> dict[str, dict[int, str]]:
    result: dict[str, dict[int, str]] = {}
    for language, artifact in SOURCE_ARTIFACTS.items():
        request = urllib.request.Request(
            str(artifact["url"]),
            headers={"User-Agent": "EleutherIA-SOTA-source-repair/1.0"},
        )
        with urllib.request.urlopen(request, timeout=30) as response:  # noqa: S310
            raw = response.read()
        digest = hashlib.sha256(raw).hexdigest()
        if digest != artifact["sha256"]:
            raise RuntimeError(
                f"{language} upstream SHA-256 mismatch: {digest} != {artifact['sha256']}"
            )
        root = ET.fromstring(raw)
        sections: dict[int, str] = {}
        for element in root.iter():
            if local_name(element.tag) != "div" or element.get("type") != "textpart":
                continue
            number = int(str(element.get("n")))
            if number in sections:
                raise RuntimeError(f"duplicate {language} section {number}")
            sections[number] = nfc_text("".join(collect_reading_text(element)))
        if set(sections) != set(range(12)):
            raise RuntimeError(
                f"{language} source does not contain exact CTS sections 0..11"
            )
        if section_set_digest(sections) != SECTION_SET_DIGESTS[language]:
            raise RuntimeError(f"{language} section text digest mismatch")
        result[language] = sections
    return result


def exact_node_id(language: str, section: int) -> str:
    return f"passage_ps_plutarch_de_fato_{language}_{section}"


def english_uuid(section: int) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"{ENG_VERSION}:{section}"))


def passage_uuid(language: str, section: int) -> str:
    return GOOD_GREEK_UUIDS[section] if language == "grc" else english_uuid(section)


def deterministic_edge_id(source: str, relation: str, target: str) -> str:
    return str(
        uuid.uuid5(uuid.NAMESPACE_URL, f"eleutheria:{source}:{relation}:{target}")
    )


def make_passage(language: str, section: int, text: str) -> dict[str, Any]:
    artifact = SOURCE_ARTIFACTS[language]
    row: dict[str, Any] = {
        "canonical_ref": f"De fato {section} ({SECTION_STEPHANUS[section]})",
        "cts_urn": f"{artifact['version_urn']}:{section}",
        "edition_urn": artifact["version_urn"],
        "language": artifact["language"],
        "passage_id": passage_uuid(language, section),
        "passage_role": artifact["passage_role"],
        "sequence_number": section,
        "stephanus_range": SECTION_STEPHANUS[section],
        "source_artifact_sha256": artifact["sha256"],
        "source_commit": UPSTREAM_COMMIT,
        "source_url": artifact["url"],
        "text_content": text,
        "text_sha256": sha256_text(text),
        "work_canonical_id": artifact["manifest_id"],
        "work_urn": WORK_URN,
    }
    if language == "eng":
        row.update(
            {
                "aligned_to_manifestation": GRC_MANIFEST_ID,
                "source_language": "grc",
                "source_passage_id": GOOD_GREEK_UUIDS[section],
                "translation_type": "published_human",
                "translator": artifact["translator"],
                "translation_of_work": WORK_URN,
            }
        )
    else:
        row["tei_gap_rendering"] = "TEI <gap/> is rendered as [...]"
    return row


def make_exact_node(
    language: str, section: int, passage: dict[str, Any]
) -> dict[str, Any]:
    artifact = SOURCE_ARTIFACTS[language]
    qualifier = (
        "Greek — Bernardakis 1891"
        if language == "grc"
        else "English — A. G./Goodwin 1874"
    )
    data: dict[str, Any] = {
        "author": "Pseudo-Plutarch (transmitted under Plutarch's name)",
        "canonical_ref": passage["canonical_ref"],
        "citability": "citable",
        "cts_urn": passage["cts_urn"],
        "db_passage_id": passage["passage_id"],
        "edition": artifact["edition"],
        "edition_urn": artifact["version_urn"],
        "language": language,
        "passage_id": passage["passage_id"],
        "passage_role": artifact["passage_role"],
        "primary_text_status": (
            "published_critical_edition"
            if language == "grc"
            else "published_translation"
        ),
        "source_artifact_sha256": artifact["sha256"],
        "source_commit": UPSTREAM_COMMIT,
        "source_url": artifact["url"],
        "stephanus_range": SECTION_STEPHANUS[section],
        "text_sha256": passage["text_sha256"],
        "work_canonical_id": WORK_URN,
        "work_id": WORK_NODE,
        STAMP: True,
    }
    if language == "eng":
        data.update(
            {
                "aligned_to_manifestation": GRC_MANIFEST_ID,
                "original_node_id": exact_node_id("grc", section),
                "source_language": "grc",
                "translation_type": "published_human",
                "translation_source": artifact["edition"],
                "translator": artifact["translator"],
                "translation_of_work": WORK_URN,
                "source_passage_id": GOOD_GREEK_UUIDS[section],
            }
        )
    return {
        "alternative_names": "[]",
        "created_at": "2026-08-24 00:00:00+00:00",
        "description": passage["text_content"],
        "id": exact_node_id(language, section),
        "label": (
            f"Ps.-Plutarch, De fato §{section}, {SECTION_STEPHANUS[section]} "
            f"({qualifier})"
        ),
        "metadata": data,
        "node_id": exact_node_id(language, section),
        "period": "Roman Imperial",
        "role": None,
        "school": "Middle Platonist",
        "type": "passage",
        "updated_at": "2026-08-24 00:00:00+00:00",
    }


def make_manifest(language: str) -> dict[str, Any]:
    artifact = SOURCE_ARTIFACTS[language]
    title = "De fato (Περὶ εἱμαρμένης)" if language == "grc" else "Of Fate"
    row: dict[str, Any] = {
        "artifact_sha256": artifact["sha256"],
        "artifact_status": "public_canonical",
        "author": "Pseudo-Plutarch (manuscript attribution: Plutarch of Chaeronea)",
        "canonical_id": artifact["manifest_id"],
        "cts_urn": artifact["version_urn"],
        "edition": artifact["edition"],
        "ingest_class": "perseus_pinned_tei",
        "language": language,
        "license": "CC BY-SA 4.0",
        "passages": 12,
        "period": "Roman Imperial",
        "source": artifact["url"],
        "source_commit": UPSTREAM_COMMIT,
        "status": "in_corpus",
        "title": title,
        "work_urn": WORK_URN,
        "stephanus_range": "568B–574F",
    }
    if language == "eng":
        row.update(
            {
                "aligned_to_manifestation": GRC_MANIFEST_ID,
                "source_language": "grc",
                "translation_type": "published_human",
                "translator": artifact["translator"],
                "translation_of_work": WORK_URN,
                "source_publication_year": 1874,
            }
        )
    else:
        row["source_publication_year"] = 1891
    return row


def make_edge(source: str, relation: str, target: str) -> dict[str, Any]:
    return {
        "created_at": "2026-08-24 00:00:00+00:00",
        "edge_id": deterministic_edge_id(source, relation, target),
        "metadata": {STAMP: True},
        "relation": relation,
        "source": source,
        "source_id": source,
        "target": target,
        "target_id": target,
        "weight": 1.0,
    }


def is_false_genuine_plutarch_attribution(edge: dict[str, Any]) -> bool:
    source = str(edge.get("source_id") or edge.get("source") or "")
    target = str(edge.get("target_id") or edge.get("target") or "")
    relation = str(edge.get("relation") or "")
    return (source, relation, target) in {
        (GENUINE_PLUTARCH_NODE, "creates", WORK_NODE),
        (WORK_NODE, "authored_by", GENUINE_PLUTARCH_NODE),
    }


def is_legacy_ps_plutarch_passage(row: dict[str, Any]) -> bool:
    work = str(row.get("work_canonical_id") or "")
    cts = str(row.get("cts_urn") or "")
    return (
        work in LEGACY_CORPUS_IDS
        or (WORK_URN in cts or "tlg9857.tlg062" in cts)
        and (work.startswith("urn_cts_greeklit_tlg0007_tlg10") or work == WORK_URN)
    )


def current_state(
    nodes: list[dict[str, Any]],
    passages: list[dict[str, Any]],
    citations: list[dict[str, Any]],
    manifest: list[dict[str, Any]],
) -> bool:
    exact_nodes = [node for node in nodes if EXACT_NODE_RE.fullmatch(node_id(node))]
    corpus = [
        row
        for row in passages
        if row.get("work_canonical_id") in {GRC_MANIFEST_ID, ENG_MANIFEST_ID}
    ]
    manifests = [
        row
        for row in manifest
        if row.get("canonical_id") in {GRC_MANIFEST_ID, ENG_MANIFEST_ID}
    ]
    exact_citations = [
        row
        for row in citations
        if EXACT_NODE_RE.fullmatch(str(row.get("kg_node_id") or ""))
        and row.get("citation_type") == "snapshot_passage_node"
    ]
    removed_survive = any(REMOVED_NODE_RE.fullmatch(node_id(node)) for node in nodes)
    by_node = {node_id(node): node for node in exact_nodes}
    translations_linked = all(
        metadata(by_node.get(exact_node_id("eng", section), {})).get("original_node_id")
        == exact_node_id("grc", section)
        for section in range(12)
    )
    return (
        len(exact_nodes) == 24
        and len(corpus) == 24
        and len(manifests) == 2
        and len(exact_citations) == 24
        and translations_linked
        and not removed_survive
        and not any("tlg9857.tlg062" in str(row) for row in passages)
        and not any(
            row.get("work_canonical_id") == "urn_cts_greeklit_tlg0007_tlg099_eng"
            for row in passages
        )
        and not any(row.get("passage_id") in LEGACY_CITATION_REMAP for row in citations)
    )


def transform(
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    passages: list[dict[str, Any]],
    citations: list[dict[str, Any]],
    manifest: list[dict[str, Any]],
    source_sections: dict[str, dict[int, str]] | None = None,
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
    for node in nodes:
        match = EXACT_NODE_RE.fullmatch(node_id(node))
        if not match:
            continue
        language = match.group(1)
        section = int(match.group(2))
        data = metadata(node)
        before = copy.deepcopy(data)
        data["canonical_ref"] = f"De fato {section} ({SECTION_STEPHANUS[section]})"
        data["stephanus_range"] = SECTION_STEPHANUS[section]
        if language == "eng":
            data.update(
                {
                    "aligned_to_manifestation": GRC_MANIFEST_ID,
                    "original_node_id": exact_node_id("grc", section),
                    "source_passage_id": GOOD_GREEK_UUIDS[section],
                    "translation_of_work": WORK_URN,
                }
            )
            data.pop("translation_of_edition", None)
        qualifier = (
            "Greek — Bernardakis 1891"
            if language == "grc"
            else "English — A. G./Goodwin 1874"
        )
        wanted_label = (
            f"Ps.-Plutarch, De fato §{section}, {SECTION_STEPHANUS[section]} "
            f"({qualifier})"
        )
        if data != before or node.get("label") != wanted_label:
            set_metadata(node, data)
            node["label"] = wanted_label
            node["updated_at"] = "2026-08-24 00:00:00+00:00"
            followup_changed.append("normalize_exact_node:" + node_id(node))

    for node in nodes:
        match = ANALYTICAL_NODE_RE.fullmatch(node_id(node))
        if not match:
            continue
        dossier = int(match.group(1))
        exact_section = ANALYTICAL_PRIMARY_SECTION.get(dossier)
        data = metadata(node)
        if exact_section is None or not isinstance(
            data.get("primary_attestation"), dict
        ):
            continue
        wanted_attestation = {
            "transmitting_author": AUTHOR_NODE,
            "transmitting_work": WORK_NODE,
            "transmitting_passage": exact_node_id("grc", exact_section),
        }
        if data["primary_attestation"] != wanted_attestation:
            data["primary_attestation"] = wanted_attestation
            set_metadata(node, data)
            node["updated_at"] = "2026-08-24 00:00:00+00:00"
            followup_changed.append("normalize_primary_attestation:" + node_id(node))

    for row in passages:
        if row.get("work_canonical_id") not in {
            GRC_MANIFEST_ID,
            ENG_MANIFEST_ID,
        }:
            continue
        language = str(row.get("language") or "")
        try:
            section = int(row["sequence_number"])
        except KeyError, TypeError, ValueError:
            continue
        if section not in SECTION_STEPHANUS:
            continue
        before = copy.deepcopy(row)
        row["canonical_ref"] = f"De fato {section} ({SECTION_STEPHANUS[section]})"
        row["stephanus_range"] = SECTION_STEPHANUS[section]
        if language == "eng":
            row.update(
                {
                    "aligned_to_manifestation": GRC_MANIFEST_ID,
                    "source_passage_id": GOOD_GREEK_UUIDS[section],
                    "translation_of_work": WORK_URN,
                }
            )
            row.pop("translation_of_edition", None)
        if row != before:
            followup_changed.append(
                "normalize_corpus_passage:" + str(row.get("passage_id") or "")
            )

    for row in manifest:
        if row.get("canonical_id") not in {GRC_MANIFEST_ID, ENG_MANIFEST_ID}:
            continue
        before = copy.deepcopy(row)
        row["stephanus_range"] = "568B–574F"
        if row.get("language") == "eng":
            row.update(
                {
                    "aligned_to_manifestation": GRC_MANIFEST_ID,
                    "translation_of_work": WORK_URN,
                }
            )
            row.pop("translation_of", None)
        if row != before:
            followup_changed.append(
                "normalize_manifest:" + str(row.get("canonical_id") or "")
            )

    retained_edges: list[dict[str, Any]] = []
    for edge in edges:
        if is_false_genuine_plutarch_attribution(edge):
            followup_changed.append("remove_false_attribution:" + edge_id(edge))
            continue
        retained_edges.append(edge)
    edges = retained_edges
    existing_edge_keys = {
        (
            str(edge.get("source_id") or edge.get("source") or ""),
            str(edge.get("relation") or ""),
            str(edge.get("target_id") or edge.get("target") or ""),
        )
        for edge in edges
    }
    for section in range(12):
        key = (
            exact_node_id("eng", section),
            "translation_of",
            exact_node_id("grc", section),
        )
        if key not in existing_edge_keys:
            edges.append(make_edge(*key))
            existing_edge_keys.add(key)
            followup_changed.append(
                "add_translation_edge:" + exact_node_id("eng", section)
            )

    for row in citations:
        old_passage_id = str(row.get("passage_id") or "")
        new_passage_id = LEGACY_CITATION_REMAP.get(old_passage_id)
        if not new_passage_id:
            continue
        row["passage_id"] = new_passage_id
        row["repair_note"] = (
            "Legacy Ps.-Plutarch pointer remapped to the exact canonical CTS section; "
            "citation semantics remain discussion, not an exact snapshot claim."
        )
        followup_changed.append(
            "rewire_citation:" + str(row.get("kg_node_id") or "") + ":" + old_passage_id
        )

    if current_state(nodes, passages, citations, manifest):
        validate(nodes, edges, passages, citations, manifest)
        return nodes, edges, passages, citations, manifest, [], followup_changed

    sections = source_sections or fetch_source_sections()
    for language in ("grc", "eng"):
        if set(sections.get(language, {})) != set(range(12)):
            raise RuntimeError(f"incomplete supplied {language} source sections")
        normalized = {
            number: nfc_text(text) for number, text in sections[language].items()
        }
        if section_set_digest(normalized) != SECTION_SET_DIGESTS[language]:
            raise RuntimeError(f"supplied {language} section text digest mismatch")
        sections[language] = normalized

    changed: list[str] = []
    quarantine: list[dict[str, Any]] = []

    removed_node_ids = {
        node_id(node) for node in nodes if REMOVED_NODE_RE.fullmatch(node_id(node))
    }
    retained_nodes: list[dict[str, Any]] = []
    for node in nodes:
        wanted = node_id(node)
        if wanted in removed_node_ids or EXACT_NODE_RE.fullmatch(wanted):
            quarantine.append(
                {
                    "record_type": "kg_node",
                    "reason": (
                        "legacy machine translation or non-canonical fine segmentation"
                        if wanted in removed_node_ids
                        else "superseded exact snapshot from interrupted repair"
                    ),
                    "record": node,
                }
            )
            changed.append("remove_node:" + wanted)
            continue
        if ANALYTICAL_NODE_RE.fullmatch(wanted):
            data = metadata(node)
            data.pop("cts_urn", None)
            data.pop("passage_id", None)
            data.pop("db_passage_id", None)
            data.update(
                {
                    "citability": "non_citable",
                    "passage_role": "editorial_analysis",
                    "source_status": "analytical_dossier_not_exact_source_text",
                    "work_canonical_id": WORK_URN,
                    STAMP: {
                        "decision": "retain as analysis only; exact source is the pinned 12-section Perseus cohort",
                    },
                }
            )
            dossier = int(wanted.rsplit("_", 1)[-1])
            exact_section = ANALYTICAL_PRIMARY_SECTION.get(dossier)
            if exact_section is not None and isinstance(
                data.get("primary_attestation"), dict
            ):
                data["primary_attestation"] = {
                    "transmitting_author": AUTHOR_NODE,
                    "transmitting_work": WORK_NODE,
                    "transmitting_passage": exact_node_id("grc", exact_section),
                }
            set_metadata(node, data)
            node["label"] = re.sub(
                r"^Plutarch,",
                "Analytical dossier — Ps.-Plutarch,",
                str(node.get("label") or ""),
            )
            node["updated_at"] = "2026-08-24 00:00:00+00:00"
            changed.append("demote_analysis:" + wanted)
        if wanted == WORK_NODE:
            data = metadata(node)
            data.update(
                {
                    "canonical_id": WORK_URN,
                    "cts_edition_grc": GRC_VERSION,
                    "cts_translation_eng": ENG_VERSION,
                    "edition_greek": SOURCE_ARTIFACTS["grc"]["edition"],
                    "edition_english": SOURCE_ARTIFACTS["eng"]["edition"],
                    "needs_edition_metadata": False,
                    "source_commit": UPSTREAM_COMMIT,
                    "source_sha256_grc": SOURCE_ARTIFACTS["grc"]["sha256"],
                    "source_sha256_eng": SOURCE_ARTIFACTS["eng"]["sha256"],
                    "total_cts_sections": 12,
                    "legacy_analytical_segments": 19,
                    STAMP: True,
                }
            )
            data.pop("total_sections", None)
            data.pop("ingestion_debt_2026_08_17_canonical_derived", None)
            set_metadata(node, data)
            node["description"] = (
                "Pseudo-Plutarch, De fato (Περὶ εἱμαρμένης), Moralia 568B–574F, "
                "transmitted under Plutarch's name and conventionally assigned to an "
                "anonymous Middle Platonist. The pinned corpus uses Bernardakis' 1891 "
                "Greek edition and the published A. G./Goodwin 1874 English translation, "
                "each in the twelve canonical Perseus CTS sections 0–11. Section 6 "
                "(570F–571E) treats the possible, contingent, what is up to us, and choice; "
                "sections 9–10 (573A–574D) distinguish three levels of providence and their "
                "relations to fate. Interpretive claims about conditional fate, causal "
                "determination and autonomy remain attributed to their modern scholars "
                "rather than silently folded into the ancient text."
            )
            node["updated_at"] = "2026-08-24 00:00:00+00:00"
            changed.append("update_work:" + wanted)
        retained_nodes.append(node)

    exact_passages: dict[tuple[str, int], dict[str, Any]] = {}
    for language in ("grc", "eng"):
        for section in range(12):
            passage = make_passage(language, section, sections[language][section])
            exact_passages[(language, section)] = passage
            retained_nodes.append(make_exact_node(language, section, passage))
            changed.append("add_node:" + exact_node_id(language, section))
    nodes = retained_nodes

    kept_edges: list[dict[str, Any]] = []
    for edge in edges:
        source = str(edge.get("source_id") or edge.get("source") or "")
        target = str(edge.get("target_id") or edge.get("target") or "")
        if (
            source in removed_node_ids
            or target in removed_node_ids
            or EXACT_NODE_RE.fullmatch(source)
            or EXACT_NODE_RE.fullmatch(target)
            or is_false_genuine_plutarch_attribution(edge)
        ):
            quarantine.append(
                {
                    "record_type": "kg_edge",
                    "reason": "endpoint replaced or quarantined",
                    "record": edge,
                }
            )
            changed.append("remove_edge:" + edge_id(edge))
            continue
        kept_edges.append(edge)
    for language in ("grc", "eng"):
        for section in range(12):
            source = exact_node_id(language, section)
            kept_edges.append(make_edge(source, "part_of", WORK_NODE))
            kept_edges.append(make_edge(source, "authored_by", AUTHOR_NODE))
    for section in range(12):
        kept_edges.append(
            make_edge(
                exact_node_id("eng", section),
                "translation_of",
                exact_node_id("grc", section),
            )
        )
    edges = kept_edges

    good_greek_by_uuid = {
        str(row.get("passage_id")): row
        for row in passages
        if str(row.get("passage_id")) in set(GOOD_GREEK_UUIDS.values())
        and row.get("work_canonical_id") == WORK_URN
    }
    if set(good_greek_by_uuid) != set(GOOD_GREEK_UUIDS.values()):
        raise RuntimeError("the twelve exact legacy Greek UUIDs are not all available")
    kept_passages: list[dict[str, Any]] = []
    for row in passages:
        if is_legacy_ps_plutarch_passage(row) or row.get("work_canonical_id") in {
            GRC_MANIFEST_ID,
            ENG_MANIFEST_ID,
        }:
            quarantine.append(
                {
                    "record_type": "corpus_passage",
                    "reason": "replaced by pinned exact manifestation",
                    "record": row,
                }
            )
            changed.append("replace_corpus:" + str(row.get("passage_id") or ""))
            continue
        kept_passages.append(row)
    for language in ("grc", "eng"):
        for section in range(12):
            kept_passages.append(exact_passages[(language, section)])
    passages = kept_passages

    kept_citations: list[dict[str, Any]] = []
    for row in citations:
        kg_id = str(row.get("kg_node_id") or "")
        if kg_id in removed_node_ids or EXACT_NODE_RE.fullmatch(kg_id):
            quarantine.append(
                {
                    "record_type": "citation",
                    "reason": "node replaced or quarantined",
                    "record": row,
                }
            )
            changed.append("remove_citation:" + citation_key(row))
            continue
        if (
            ANALYTICAL_NODE_RE.fullmatch(kg_id)
            and row.get("citation_type") == "snapshot_passage_node"
        ):
            row["citation_type"] = "related_passage_non_exact"
            row["confidence"] = 1.0
            row["repair_note"] = (
                "Analytical 19-part dossier is not an exact twin of the canonical 12-section CTS text."
            )
            changed.append("demote_citation:" + kg_id)
        kept_citations.append(row)
    for language in ("grc", "eng"):
        for section in range(12):
            kept_citations.append(
                {
                    "citation_type": "snapshot_passage_node",
                    "confidence": 1.0,
                    "kg_node_id": exact_node_id(language, section),
                    "passage_id": passage_uuid(language, section),
                    "source_release": UPSTREAM_COMMIT,
                }
            )
    citations = kept_citations

    kept_manifest: list[dict[str, Any]] = []
    for row in manifest:
        canonical = str(row.get("canonical_id") or "")
        cts = str(row.get("cts_urn") or "")
        if canonical in LEGACY_CORPUS_IDS | {GRC_MANIFEST_ID, ENG_MANIFEST_ID} or (
            "tlg0007.tlg108" in cts or "tlg9857.tlg062" in cts
        ):
            quarantine.append(
                {
                    "record_type": "manifest",
                    "reason": "replaced by language-specific pinned manifestation",
                    "record": row,
                }
            )
            changed.append("replace_manifest:" + canonical)
            continue
        kept_manifest.append(row)
    kept_manifest.extend((make_manifest("grc"), make_manifest("eng")))
    manifest = kept_manifest

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
    if len(by_node) != len(nodes):
        raise RuntimeError("duplicate node id after Ps.-Plutarch repair")
    if len(by_passage) != len(passages):
        raise RuntimeError("duplicate passage UUID after Ps.-Plutarch repair")

    work = metadata(by_node.get(WORK_NODE, {}))
    if work.get("canonical_id") != WORK_URN or work.get("total_cts_sections") != 12:
        raise RuntimeError("Ps.-Plutarch work identity or CTS section count is wrong")
    if work.get("needs_edition_metadata") is not False:
        raise RuntimeError("Ps.-Plutarch work still claims missing edition metadata")

    corpus = [
        row
        for row in passages
        if row.get("work_canonical_id") in {GRC_MANIFEST_ID, ENG_MANIFEST_ID}
    ]
    if len(corpus) != 24:
        raise RuntimeError(
            f"expected 24 exact Ps.-Plutarch passages, found {len(corpus)}"
        )
    by_language = {
        language: {
            int(row["sequence_number"]): nfc_text(str(row["text_content"]))
            for row in corpus
            if row.get("language") == language
        }
        for language in ("grc", "eng")
    }
    for language in ("grc", "eng"):
        if set(by_language[language]) != set(range(12)):
            raise RuntimeError(
                f"{language} Ps.-Plutarch sections are not exactly 0..11"
            )
        if section_set_digest(by_language[language]) != SECTION_SET_DIGESTS[language]:
            raise RuntimeError(f"{language} Ps.-Plutarch corpus text digest mismatch")
    for row in corpus:
        section = int(row["sequence_number"])
        if (
            row.get("stephanus_range") != SECTION_STEPHANUS[section]
            or row.get("canonical_ref")
            != f"De fato {section} ({SECTION_STEPHANUS[section]})"
        ):
            raise RuntimeError(
                "Ps.-Plutarch section lacks its reviewed Stephanus locus"
            )
        if row.get("language") == "eng" and (
            row.get("source_passage_id") != GOOD_GREEK_UUIDS[section]
            or row.get("translation_of_work") != WORK_URN
            or row.get("aligned_to_manifestation") != GRC_MANIFEST_ID
            or row.get("translation_of_edition")
        ):
            raise RuntimeError(
                "published translation lacks source-passage/work alignment provenance"
            )
    if {row["passage_id"] for row in corpus if row.get("language") == "grc"} != set(
        GOOD_GREEK_UUIDS.values()
    ):
        raise RuntimeError("exact Greek UUID preservation failed")
    if any(
        "tlg9857.tlg062" in str(row)
        or row.get("work_canonical_id") == "urn_cts_greeklit_tlg0007_tlg099_eng"
        for row in passages
    ):
        raise RuntimeError("foreign Ps.-Plutarch work identity remains in corpus")

    exact_nodes = [node for node in nodes if EXACT_NODE_RE.fullmatch(node_id(node))]
    if len(exact_nodes) != 24:
        raise RuntimeError(
            f"expected 24 exact Ps.-Plutarch KG nodes, found {len(exact_nodes)}"
        )
    for node in exact_nodes:
        data = metadata(node)
        passage_id_value = str(data.get("passage_id") or "")
        passage = by_passage.get(passage_id_value)
        if passage is None or nfc_text(str(node.get("description") or "")) != nfc_text(
            str(passage.get("text_content") or "")
        ):
            raise RuntimeError(f"exact node text mismatch: {node_id(node)}")
        if data.get("citability") != "citable" or data.get(
            "text_sha256"
        ) != sha256_text(str(node.get("description") or "")):
            raise RuntimeError(f"exact node provenance mismatch: {node_id(node)}")
        match = EXACT_NODE_RE.fullmatch(node_id(node))
        if match:
            section = int(match.group(2))
            if (
                data.get("stephanus_range") != SECTION_STEPHANUS[section]
                or data.get("canonical_ref")
                != f"De fato {section} ({SECTION_STEPHANUS[section]})"
            ):
                raise RuntimeError(f"exact node lacks Stephanus locus: {node_id(node)}")
        if match and match.group(1) == "eng":
            section = int(match.group(2))
            if (
                data.get("original_node_id") != exact_node_id("grc", section)
                or data.get("source_passage_id") != GOOD_GREEK_UUIDS[section]
                or data.get("translation_of_work") != WORK_URN
                or data.get("aligned_to_manifestation") != GRC_MANIFEST_ID
                or data.get("translation_of_edition")
            ):
                raise RuntimeError(
                    f"published translation lacks original node: {node_id(node)}"
                )

    if any(REMOVED_NODE_RE.fullmatch(node_id(node)) for node in nodes):
        raise RuntimeError("legacy machine/fine Ps.-Plutarch nodes remain queryable")
    analyses = [node for node in nodes if ANALYTICAL_NODE_RE.fullmatch(node_id(node))]
    if len(analyses) != 19:
        raise RuntimeError(
            f"expected 19 retained analytical dossiers, found {len(analyses)}"
        )
    for node in analyses:
        data = metadata(node)
        if (
            data.get("citability") != "non_citable"
            or data.get("passage_role") != "editorial_analysis"
            or data.get("cts_urn")
            or data.get("passage_id")
            or data.get("db_passage_id")
        ):
            raise RuntimeError(
                f"analytical dossier can still masquerade as a passage: {node_id(node)}"
            )
        dossier = int(node_id(node).rsplit("_", 1)[-1])
        exact_section = ANALYTICAL_PRIMARY_SECTION.get(dossier)
        if exact_section is not None and data.get("primary_attestation") != {
            "transmitting_author": AUTHOR_NODE,
            "transmitting_work": WORK_NODE,
            "transmitting_passage": exact_node_id("grc", exact_section),
        }:
            raise RuntimeError(
                f"analytical dossier has false primary attribution: {node_id(node)}"
            )

    snapshot_by_node = {
        str(row.get("kg_node_id")): row
        for row in citations
        if row.get("citation_type") == "snapshot_passage_node"
        and EXACT_NODE_RE.fullmatch(str(row.get("kg_node_id") or ""))
    }
    if set(snapshot_by_node) != {node_id(node) for node in exact_nodes}:
        raise RuntimeError("exact Ps.-Plutarch snapshot citations are incomplete")
    if any(
        row.get("citation_type") == "snapshot_passage_node"
        for row in citations
        if ANALYTICAL_NODE_RE.fullmatch(str(row.get("kg_node_id") or ""))
    ):
        raise RuntimeError(
            "analytical Ps.-Plutarch dossier still has an exact snapshot citation"
        )
    if any(row.get("passage_id") in LEGACY_CITATION_REMAP for row in citations):
        raise RuntimeError("citation still points to a quarantined Ps.-Plutarch UUID")

    current_manifest = [
        row
        for row in manifest
        if row.get("canonical_id") in {GRC_MANIFEST_ID, ENG_MANIFEST_ID}
    ]
    if len(current_manifest) != 2 or {
        row.get("language") for row in current_manifest
    } != {
        "grc",
        "eng",
    }:
        raise RuntimeError(
            "Greek and English Ps.-Plutarch manifestations are not distinct"
        )
    for row in current_manifest:
        artifact = SOURCE_ARTIFACTS[str(row["language"])]
        if (
            row.get("artifact_sha256") != artifact["sha256"]
            or row.get("source_commit") != UPSTREAM_COMMIT
            or row.get("artifact_status") != "public_canonical"
            or row.get("passages") != 12
            or row.get("stephanus_range") != "568B–574F"
        ):
            raise RuntimeError("Ps.-Plutarch manifestation is not reproducibly pinned")
        if row.get("language") == "eng" and (
            row.get("translation_of_work") != WORK_URN
            or row.get("aligned_to_manifestation") != GRC_MANIFEST_ID
            or row.get("translation_of")
        ):
            raise RuntimeError(
                "English manifestation has an anachronistic edition claim"
            )

    edge_ids = [edge_id(row) for row in edges]
    if len(edge_ids) != len(set(edge_ids)):
        raise RuntimeError("duplicate edge id after Ps.-Plutarch repair")
    if any(is_false_genuine_plutarch_attribution(edge) for edge in edges):
        raise RuntimeError("Ps.-Plutarch work remains attributed to genuine Plutarch")
    for node in exact_nodes:
        wanted = node_id(node)
        relations = {
            (
                str(edge.get("relation")),
                str(edge.get("target_id") or edge.get("target")),
            )
            for edge in edges
            if str(edge.get("source_id") or edge.get("source")) == wanted
        }
        if not {("part_of", WORK_NODE), ("authored_by", AUTHOR_NODE)} <= relations:
            raise RuntimeError(f"exact node lacks work/author edges: {wanted}")
    translation_edges = {
        (
            str(edge.get("source_id") or edge.get("source") or ""),
            str(edge.get("target_id") or edge.get("target") or ""),
        )
        for edge in edges
        if edge.get("relation") == "translation_of"
        and EXACT_NODE_RE.fullmatch(
            str(edge.get("source_id") or edge.get("source") or "")
        )
    }
    expected_translation_edges = {
        (exact_node_id("eng", section), exact_node_id("grc", section))
        for section in range(12)
    }
    if translation_edges != expected_translation_edges:
        raise RuntimeError(
            "published English/Greek section alignment edges are incomplete"
        )


def write_preserving(
    path: Path,
    rows: list[dict[str, Any]],
    key: Callable[[dict[str, Any]], str],
) -> None:
    original = [
        line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()
    ]
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
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=path.parent, delete=False
    ) as handle:
        tmp = Path(handle.name)
        handle.write("\n".join(output) + "\n")
    tmp.replace(path)


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=path.parent, delete=False
    ) as handle:
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
    print("Ps.-Plutarch De fato text repair")
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
    write_preserving(
        paths["passages"], passages, lambda row: str(row.get("passage_id") or "")
    )
    write_preserving(paths["citations"], citations, citation_key)
    write_preserving(
        paths["manifest"], manifest, lambda row: str(row.get("canonical_id") or "")
    )

    quarantine_path = (
        data_root / "audit/2026-08-24_ps_plutarch_de_fato_quarantine.jsonl"
    )
    if quarantine or not quarantine_path.exists():
        write_jsonl(quarantine_path, quarantine)
    report_path = data_root / "audit/2026-08-24_ps_plutarch_de_fato_text_repair.json"
    report = {
        "authoritative_work_urn": WORK_URN,
        "changed_records": len(changed),
        "cts_sections_per_manifestation": 12,
        "exact_kg_snapshot_nodes": 24,
        "legacy_analytical_dossiers_retained_non_citable": 19,
        "quarantined_records": len(quarantine),
        "source_artifacts": SOURCE_ARTIFACTS,
        "source_commit": UPSTREAM_COMMIT,
        "status": "primary repair applied; independent and adversarial scholarly review still required",
        "text_set_sha256": SECTION_SET_DIGESTS,
    }
    if not quarantine and report_path.exists():
        previous = json.loads(report_path.read_text(encoding="utf-8"))
        report["quarantined_records"] = previous.get("quarantined_records", 0)
        report["followup_records_changed"] = len(changed)
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print("wrote:", *paths.values(), quarantine_path, report_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
