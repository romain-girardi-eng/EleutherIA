#!/usr/bin/env python3
"""Gate and optionally apply the Clement primary-grounding wave.

The source text is copied from a hash-pinned local TEI re-encoding of Otto
Stahlin's GCS edition.  The operation closes the documented Stromateis gap,
adds matching corpus rows, removes six known false evidence links, and
repoints the two affected arguments to the exact passages that support them.

Default is a non-writing dry-run.  Use ``--apply`` only after every reported
gate is green.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
import uuid
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scripts.check_corpus_invariants import (  # noqa: E402
    find_violations as corpus_violations,
)
from scripts.check_kg_corpus_locus_parity import (  # noqa: E402
    find_violations as parity_violations,
)
from scripts.data_2026_08_18_clement_primary_grounding import (  # noqa: E402
    ARGUMENT_FAITH_NATURE,
    ARGUMENT_GRACE_ASSENT,
    CORPUS_WORK_ID,
    CTS_BASE,
    EVIDENCE_TARGETS,
    PDF_PUBLIC_SOURCE_PATH,
    PDF_SHA256,
    PERSON_ID,
    PUBLIC_SOURCE_PATH,
    TARGETS,
    WAVE,
    WORK_ID,
    WRONG_ARGUMENT_IDS,
    WRONG_EDGE_IDS,
    WRONG_PASSAGE_IDS,
    XML_RELATIVE_SOURCE,
    XML_SHA256,
)

NODES_PATH = ROOT / "data/kg/nodes.jsonl"
EDGES_PATH = ROOT / "data/kg/edges.jsonl"
PASSAGES_PATH = ROOT / "data/corpus/passages.jsonl"
CITATIONS_PATH = ROOT / "data/corpus/citations.jsonl"
MANIFEST_PATH = ROOT / "data/corpus/manifest.jsonl"
GATE_PATH = ROOT / "scripts/check_ingestion_rules.py"

DEFAULT_SHAL_ROOT = Path("/Users/romaingirardi/Desktop/DOCTORAT/Doctorat SHAL")
DEFAULT_XML_SOURCE = DEFAULT_SHAL_ROOT / XML_RELATIVE_SOURCE

TEI_NS = "http://www.tei-c.org/ns/1.0"
NS = {"tei": TEI_NS}
INGEST_SCRIPT = "scripts/ingest_2026_08_18_clement_primary_grounding.py"
BACKUP_SUFFIX = ".bak-clement_grounding_2026_08_18"
SNAPSHOT_UUID_NS = uuid.UUID("d46efc36-9f19-45fb-9b8d-8a4d3e4d2728")
EDGE_UUID_NS = uuid.UUID("0c2501d7-74aa-4de0-823d-54f6214ab2a8")
EDITION = (
    "Otto Stahlin, Clemens Alexandrinus II: Stromata I-VI, "
    "GCS 15 (Leipzig, 1906), TEI re-encoding tlg0555.tlg004.perseus-grc2"
)

ROMAN = {1: "I", 2: "II", 3: "III", 4: "IV", 5: "V", 6: "VI"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="write the gated wave; default is a dry-run",
    )
    parser.add_argument(
        "--xml-source",
        type=Path,
        default=DEFAULT_XML_SOURCE,
        help="path to the hash-pinned Clement Stromata TEI file",
    )
    return parser.parse_args()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    """Write changed rows while preserving byte formatting of unchanged rows."""

    def key(row: dict[str, Any]) -> Any:
        if path == NODES_PATH:
            return ("node", node_id(row))
        if path == EDGES_PATH:
            return ("edge", str(row.get("edge_id") or ""))
        if path == PASSAGES_PATH:
            return ("passage", str(row.get("passage_id") or ""))
        if path == CITATIONS_PATH:
            return (
                "citation",
                str(row.get("passage_id") or ""),
                str(row.get("kg_node_id") or ""),
                str(row.get("citation_type") or ""),
            )
        if path == MANIFEST_PATH:
            return ("manifest", str(row.get("canonical_id") or ""))
        raise ValueError(f"no JSONL identity key for {path}")

    old_rows: dict[Any, tuple[dict[str, Any], str]] = {}
    old_order: list[Any] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            parsed = json.loads(line)
            wanted_key = key(parsed)
            old_rows[wanted_key] = (parsed, line)
            old_order.append(wanted_key)

    new_rows = {key(row): row for row in rows}
    if len(new_rows) != len(rows):
        raise ValueError(f"duplicate JSONL identity key while writing {path}")

    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        written: set[Any] = set()
        for wanted_key in old_order:
            row = new_rows.get(wanted_key)
            if row is None:
                continue
            previous, raw_line = old_rows[wanted_key]
            if row == previous:
                handle.write(raw_line)
            else:
                handle.write(json.dumps(row, ensure_ascii=False))
                handle.write("\n")
            written.add(wanted_key)
        for row in rows:
            wanted_key = key(row)
            if wanted_key in written:
                continue
            handle.write(json.dumps(row, ensure_ascii=False))
            handle.write("\n")
            written.add(wanted_key)
    temporary.replace(path)


def parse_metadata(node: dict[str, Any]) -> tuple[dict[str, Any], str]:
    value = node.get("metadata")
    if isinstance(value, dict):
        return copy.deepcopy(value), "dict"
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return {}, "opaque"
        if isinstance(parsed, dict):
            return parsed, "string"
    return {}, "none"


def set_metadata(node: dict[str, Any], value: dict[str, Any], form: str) -> None:
    node["metadata"] = (
        json.dumps(value, ensure_ascii=False) if form == "string" else value
    )


def node_id(node: dict[str, Any]) -> str:
    return str(node.get("id") or node.get("node_id") or "")


def edge_triple(edge: dict[str, Any]) -> tuple[str, str, str]:
    return (
        str(edge.get("source") or edge.get("source_id") or ""),
        str(edge.get("relation") or edge.get("type") or ""),
        str(edge.get("target") or edge.get("target_id") or ""),
    )


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def reading_text(element: ET.Element) -> str:
    """Return the TEI reading text: include additions, exclude deletions/notes.

    ``choice`` and ``app`` are resolved to one edited reading rather than
    concatenating mutually exclusive variants.
    """

    tag = local_name(element.tag)
    if tag in {"del", "note", "fw"}:
        return ""
    if tag == "choice":
        children = list(element)
        for preferred in ("corr", "reg", "expan", "orig", "sic", "abbr"):
            chosen = next(
                (child for child in children if local_name(child.tag) == preferred),
                None,
            )
            if chosen is not None:
                return reading_text(chosen)
    if tag == "app":
        lemma = next(
            (child for child in element if local_name(child.tag) == "lem"), None
        )
        return reading_text(lemma) if lemma is not None else ""

    parts = [element.text or ""]
    for child in element:
        parts.append(reading_text(child))
        parts.append(child.tail or "")
    return "".join(parts)


def edition_root(xml_source: Path) -> ET.Element:
    tree = ET.parse(xml_source)
    body = tree.getroot().find("tei:text/tei:body", NS)
    if body is None:
        raise ValueError("TEI has no text/body")
    edition = body.find("tei:div", NS)
    if edition is None or edition.get("type") != "edition":
        raise ValueError("TEI body has no edition div")
    return edition


def extract_sections(
    edition: ET.Element,
) -> dict[tuple[int, int, int], dict[str, Any]]:
    wanted = {(book, chapter, section) for book, chapter, section, _ in TARGETS}
    found: dict[tuple[int, int, int], dict[str, Any]] = {}
    for book_div in edition.findall("tei:div", NS):
        if book_div.get("subtype") != "book":
            continue
        book = int(book_div.get("n", "0"))
        for chapter_div in book_div.findall("tei:div", NS):
            chapter = int(chapter_div.get("n", "0"))
            for section_div in chapter_div.findall("tei:div", NS):
                section = int(section_div.get("n", "0"))
                key = (book, chapter, section)
                if key not in wanted:
                    continue
                text = re.sub(r"\s+", " ", reading_text(section_div)).strip()
                raw_text = re.sub(r"\s+", " ", "".join(section_div.itertext())).strip()
                markers = [
                    str(item.get("n"))
                    for item in section_div.iter(f"{{{TEI_NS}}}milestone")
                    if item.get("unit") == "subsection" and item.get("n")
                ]
                found[key] = {
                    "text": text,
                    "raw_text": raw_text,
                    "subsections": ["1", *markers],
                }
    missing = sorted(wanted - set(found))
    empty = sorted(key for key, value in found.items() if not value["text"])
    if missing or empty:
        raise ValueError(f"TEI target failure: missing={missing}, empty={empty}")
    if len(found) != 58:
        raise ValueError(f"expected 58 target divisions, found {len(found)}")
    return found


def passage_node_id(book: int, chapter: int, section: int) -> str:
    return f"passage_clement_strom_{book}_{chapter}_{section}"


def passage_uuid(node_name: str) -> str:
    return str(uuid.uuid5(SNAPSHOT_UUID_NS, f"snapshot:passage:{node_name}"))


def canonical_ref(book: int, chapter: int, section: int) -> str:
    return f"Strom. {ROMAN[book]}.{chapter}.{section}"


def cts_urn(book: int, chapter: int, section: int) -> str:
    return f"{CTS_BASE}:{book}.{chapter}.{section}"


def sequence_number(book: int, chapter: int, section: int) -> int:
    # Unlike the legacy helper, this preserves the Roman book level.
    return book * 1_000_000 + chapter * 1_000 + section


def provenance(reference: str) -> dict[str, Any]:
    return {
        "source": PUBLIC_SOURCE_PATH,
        "source_sha256": XML_SHA256,
        "source_reference": reference,
        "ingested_at": "2026-08-18",
        "ingest_script": INGEST_SCRIPT,
    }


def build_node(
    spec: tuple[int, int, int, str], extracted: dict[str, Any], now: str
) -> dict[str, Any]:
    book, chapter, section, printed_reference = spec
    wanted_id = passage_node_id(book, chapter, section)
    ref = canonical_ref(book, chapter, section)
    wanted_urn = cts_urn(book, chapter, section)
    text = extracted["text"]
    metadata = {
        "attestation_type": "direct",
        "author": "Clement of Alexandria",
        "author_id": PERSON_ID,
        "book": book,
        "chapter": chapter,
        "section": section,
        "subsections_present": extracted["subsections"],
        "canonical_ref": ref,
        "traditional_reference": printed_reference,
        "cts_urn": wanted_urn,
        "work_canonical_id": CORPUS_WORK_ID,
        "corpus_work_canonical_id": CORPUS_WORK_ID,
        "db_passage_id": passage_uuid(wanted_id),
        "corpus_passage_id": passage_uuid(wanted_id),
        "language": "grc",
        "passage_role": "original",
        "period": "Patristic",
        "school": "Christian Platonism",
        "work_title": "Stromateis",
        "edition": EDITION,
        "source": PUBLIC_SOURCE_PATH,
        "source_local_path": PUBLIC_SOURCE_PATH,
        "source_pdf": PDF_PUBLIC_SOURCE_PATH,
        "source_pdf_sha256": PDF_SHA256,
        "source_rank": "critical_edition",
        "citation_verdict": "verified",
        "citation_verified": True,
        "verified_reference": f"Clement, {ref}; {EDITION}",
        "word_count": len(text.split()),
        "char_length": len(text),
        "created_by": WAVE,
        "provenance": provenance(printed_reference),
        WAVE: True,
    }
    if (book, chapter, section) == (2, 3, 11):
        metadata["is_amand_b9_clement_witness"] = True
        metadata["amand_reference"] = (
            "Strom. II, 11, 1-2 = full CTS hierarchy II.3.11.1-2"
        )
    return {
        "alternative_names": "[]",
        "created_at": now,
        "description": text,
        "id": wanted_id,
        "label": f"Clement of Alexandria, {ref}",
        "metadata": metadata,
        "node_id": wanted_id,
        "period": "Patristic",
        "role": None,
        "school": "Christian Platonism",
        "type": "passage",
        "updated_at": now,
    }


def deterministic_edge_id(source: str, relation: str, target: str) -> str:
    return str(uuid.uuid5(EDGE_UUID_NS, f"{WAVE}:{source}:{relation}:{target}"))


def build_edge(
    source: str, relation: str, target: str, now: str, metadata: dict[str, Any]
) -> dict[str, Any]:
    return {
        "created_at": now,
        "edge_id": deterministic_edge_id(source, relation, target),
        "metadata": {"wave": WAVE, **metadata},
        "relation": relation,
        "source": source,
        "source_id": source,
        "target": target,
        "target_id": target,
        "weight": 1.0,
    }


def expected_wrong_triples() -> set[tuple[str, str, str]]:
    old_targets = {passage_node_id(2, 11, section) for section in (50, 51, 52)}
    return {
        (argument, "evidenced_by", target)
        for argument in WRONG_ARGUMENT_IDS
        for target in old_targets
    }


def transform(
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    passages: list[dict[str, Any]],
    citations: list[dict[str, Any]],
    manifest: list[dict[str, Any]],
    sections: dict[tuple[int, int, int], dict[str, Any]],
    now: str,
) -> dict[str, Any]:
    by_id = {node_id(node): node for node in nodes}
    required = {WORK_ID, PERSON_ID, ARGUMENT_FAITH_NATURE, ARGUMENT_GRACE_ASSENT}
    missing_required = sorted(required - set(by_id))
    if missing_required:
        raise ValueError(f"missing required KG nodes: {missing_required}")

    target_specs = {spec[:3]: spec for spec in TARGETS}
    if len(target_specs) != 58:
        raise ValueError("TARGETS must contain 58 unique CTS divisions")

    new_nodes: list[dict[str, Any]] = []
    for key, spec in target_specs.items():
        wanted_id = passage_node_id(*key)
        existing = by_id.get(wanted_id)
        if existing is not None:
            existing_meta, _ = parse_metadata(existing)
            if existing_meta.get("cts_urn") != cts_urn(*key):
                raise ValueError(f"existing target has wrong CTS URN: {wanted_id}")
            if existing.get("description") not in {
                sections[key]["text"],
                sections[key]["raw_text"],
            }:
                raise ValueError(
                    f"existing target text differs from pinned TEI: {wanted_id}"
                )
            continue
        node = build_node(spec, sections[key], now)
        nodes.append(node)
        by_id[wanted_id] = node
        new_nodes.append(node)

    if len(new_nodes) > 55:
        raise ValueError(f"too many new Clement nodes: {len(new_nodes)}")

    # Remove only the six pre-adjudicated false evidence edges.
    wrong_triples = expected_wrong_triples()
    removed_edges: list[dict[str, Any]] = []
    kept_edges: list[dict[str, Any]] = []
    for edge in edges:
        if edge.get("edge_id") not in WRONG_EDGE_IDS:
            kept_edges.append(edge)
            continue
        if edge_triple(edge) not in wrong_triples:
            raise ValueError(f"wrong-edge precondition failed: {edge.get('edge_id')}")
        removed_edges.append(edge)
    edges[:] = kept_edges
    if len(removed_edges) > 6:
        raise ValueError(f"too many removed KG edges: {len(removed_edges)}")
    remaining_wrong = wrong_triples & {edge_triple(edge) for edge in edges}
    if remaining_wrong:
        raise ValueError(
            f"false evidence edges remain after correction: {remaining_wrong}"
        )

    existing_triples = {edge_triple(edge) for edge in edges}
    new_edges: list[dict[str, Any]] = []
    for key, spec in target_specs.items():
        wanted_id = passage_node_id(*key)
        for relation, target, note in (
            ("part_of", WORK_ID, "section belongs to Clement's Stromateis"),
            ("authored_by", PERSON_ID, "direct authorship in the critical edition"),
        ):
            triple = (wanted_id, relation, target)
            if triple in existing_triples:
                continue
            edge = build_edge(
                wanted_id,
                relation,
                target,
                now,
                {
                    "note": note,
                    "provenance": provenance(spec[3]),
                },
            )
            edges.append(edge)
            new_edges.append(edge)
            existing_triples.add(triple)

    for argument_id, targets in EVIDENCE_TARGETS.items():
        for target in targets:
            target_id = passage_node_id(*target)
            if target_id not in by_id:
                raise ValueError(
                    f"missing evidence target after transform: {target_id}"
                )
            triple = (argument_id, "evidenced_by", target_id)
            if triple in existing_triples:
                continue
            ref = canonical_ref(*target)
            edge = build_edge(
                argument_id,
                "evidenced_by",
                target_id,
                now,
                {
                    "attested_by": ref,
                    "correction": "replaces false links to Strom. II.11.50-52",
                    "provenance": provenance(ref),
                },
            )
            edges.append(edge)
            new_edges.append(edge)
            existing_triples.add(triple)

    # Add the 55 new corpus passages and normalize sequence ordering for every
    # Clement Stromata row, including the six older ones.
    passage_by_id = {str(row.get("passage_id")): row for row in passages}
    passage_by_urn = {str(row.get("cts_urn")): row for row in passages}
    new_passages: list[dict[str, Any]] = []
    for key in target_specs:
        wanted_node_id = passage_node_id(*key)
        wanted_pid = passage_uuid(wanted_node_id)
        wanted_urn = cts_urn(*key)
        wanted_ref = canonical_ref(*key)
        existing = passage_by_id.get(wanted_pid)
        if existing is None:
            other = passage_by_urn.get(wanted_urn)
            if other is not None:
                raise ValueError(
                    f"CTS URN already belongs to another corpus UUID: {wanted_urn}"
                )
            row = {
                "passage_id": wanted_pid,
                "canonical_ref": wanted_ref,
                "cts_urn": wanted_urn,
                "sequence_number": sequence_number(*key),
                "text_content": sections[key]["text"],
                "work_canonical_id": CORPUS_WORK_ID,
            }
            passages.append(row)
            passage_by_id[wanted_pid] = row
            passage_by_urn[wanted_urn] = row
            new_passages.append(row)
        else:
            expected = {
                "canonical_ref": wanted_ref,
                "cts_urn": wanted_urn,
                "work_canonical_id": CORPUS_WORK_ID,
            }
            for field, value in expected.items():
                if existing.get(field) != value:
                    raise ValueError(
                        f"existing corpus target differs at {wanted_pid}.{field}"
                    )
            if existing.get("text_content") not in {
                sections[key]["text"],
                sections[key]["raw_text"],
            }:
                raise ValueError(
                    f"existing corpus target differs at {wanted_pid}.text_content"
                )
            existing["sequence_number"] = sequence_number(*key)

    for row in passages:
        if row.get("work_canonical_id") != CORPUS_WORK_ID:
            continue
        match = re.fullmatch(
            re.escape(CTS_BASE) + r":(\d+)\.(\d+)\.(\d+)",
            str(row.get("cts_urn") or ""),
        )
        if match:
            row["sequence_number"] = sequence_number(
                *(int(part) for part in match.groups())
            )

    if len(new_passages) > 55:
        raise ValueError(f"too many new Clement corpus rows: {len(new_passages)}")

    # Link every Clement passage node to its exact corpus twin, including the
    # six older passages that previously had only an implicit snapshot link.
    for node in nodes:
        wanted_id = node_id(node)
        if not wanted_id.startswith("passage_clement_strom_"):
            continue
        node_meta, form = parse_metadata(node)
        previous_meta = copy.deepcopy(node_meta)
        wanted_urn = str(node_meta.get("cts_urn") or "")
        passage = passage_by_urn.get(wanted_urn)
        if passage is None or passage.get("work_canonical_id") != CORPUS_WORK_ID:
            continue
        node_meta.update(
            {
                "db_passage_id": passage["passage_id"],
                "corpus_passage_id": passage["passage_id"],
                "work_canonical_id": CORPUS_WORK_ID,
                "corpus_work_canonical_id": CORPUS_WORK_ID,
                WAVE: True,
            }
        )
        if node_meta != previous_meta:
            node["updated_at"] = now
            set_metadata(node, node_meta, form)

    # Work identity and the once-truncated verification reference are repaired.
    work = by_id[WORK_ID]
    work_meta, work_form = parse_metadata(work)
    previous_work_meta = copy.deepcopy(work_meta)
    work_meta.update(
        {
            "cts_urn": "urn:cts:greekLit:tlg0555.tlg004",
            "work_canonical_id": CORPUS_WORK_ID,
            "corpus_work_canonical_id": CORPUS_WORK_ID,
            "citation_verdict": "verified",
            "citation_verified": True,
            "verified_reference": (
                "Clement of Alexandria, Stromateis, 8 books; Otto Stahlin, "
                "GCS 15 (I-VI, 1906) and GCS 17 (VII-VIII, 1909); local TEI "
                "re-encoding tlg0555.tlg004.perseus-grc2 verified against the "
                "GCS 15 print on 2026-08-18."
            ),
            "primary_grounding": {
                "source": PUBLIC_SOURCE_PATH,
                "source_sha256": XML_SHA256,
                "passage_nodes": 61,
                "wave": WAVE,
            },
            WAVE: True,
        }
    )
    if work_meta != previous_work_meta:
        work["updated_at"] = now
        set_metadata(work, work_meta, work_form)

    grace = by_id[ARGUMENT_GRACE_ASSENT]
    grace_meta, grace_form = parse_metadata(grace)
    previous_grace_meta = copy.deepcopy(grace_meta)
    grace_meta.update(
        {
            "citation_verdict": "corrected",
            "citation_verified": True,
            "verified_reference": (
                "Clement, Stromateis II.2.8.3-4 (GCS 15 p.117), II.6.26.1-5 "
                "(pp.126-127), II.12.54-55 (pp.142-143), IV.23.152.2 (p.315), "
                "IV.24.153.1 (p.316), and V.13.86 (p.383), verified against "
                "the hash-pinned Stahlin GCS print and TEI on 2026-08-18."
            ),
            "evidence_repaired_by": WAVE,
        }
    )
    if grace_meta != previous_grace_meta:
        grace["updated_at"] = now
        set_metadata(grace, grace_meta, grace_form)

    faith = by_id[ARGUMENT_FAITH_NATURE]
    faith_meta, faith_form = parse_metadata(faith)
    previous_faith_meta = copy.deepcopy(faith_meta)
    faith_meta.update(
        {
            "citation_verdict": "corrected",
            "citation_verified": True,
            "verified_reference": (
                "Clement, Stromateis II, continuous section 11.1-2 = full CTS "
                "hierarchy II.3.11 (Stahlin GCS 15 pp.118.21-119.3), verified "
                "against the hash-pinned print and TEI on 2026-08-18; Amand "
                "1945/1973 pp.272-273."
            ),
            "evidence_repaired_by": WAVE,
        }
    )
    if faith_meta != previous_faith_meta:
        faith["updated_at"] = now
        set_metadata(faith, faith_meta, faith_form)

    # Remove only the six false argument citations, retaining the three
    # snapshot_passage_node citations for II.11.50-52.
    removed_citations: list[dict[str, Any]] = []
    kept_citations: list[dict[str, Any]] = []
    for citation in citations:
        is_wrong = (
            citation.get("passage_id") in WRONG_PASSAGE_IDS
            and citation.get("kg_node_id") in WRONG_ARGUMENT_IDS
            and citation.get("citation_type") == "evidenced_by"
        )
        if is_wrong:
            removed_citations.append(citation)
        else:
            kept_citations.append(citation)
    citations[:] = kept_citations
    if len(removed_citations) > 6:
        raise ValueError(f"too many removed corpus citations: {len(removed_citations)}")

    citation_triples = {
        (
            str(row.get("passage_id") or ""),
            str(row.get("kg_node_id") or ""),
            str(row.get("citation_type") or ""),
        )
        for row in citations
    }
    new_citations: list[dict[str, Any]] = []

    remaining_wrong_citations = {
        (
            str(row.get("passage_id") or ""),
            str(row.get("kg_node_id") or ""),
            str(row.get("citation_type") or ""),
        )
        for row in citations
        if row.get("passage_id") in WRONG_PASSAGE_IDS
        and row.get("kg_node_id") in WRONG_ARGUMENT_IDS
        and row.get("citation_type") == "evidenced_by"
    }
    if remaining_wrong_citations:
        raise ValueError(
            f"false corpus citations remain after correction: {remaining_wrong_citations}"
        )

    for key in target_specs:
        wanted_id = passage_node_id(*key)
        triple = (passage_uuid(wanted_id), wanted_id, "snapshot_passage_node")
        if triple not in citation_triples:
            row = {
                "citation_type": triple[2],
                "confidence": 1.0,
                "kg_node_id": triple[1],
                "passage_id": triple[0],
            }
            citations.append(row)
            new_citations.append(row)
            citation_triples.add(triple)

    for argument_id, targets in EVIDENCE_TARGETS.items():
        for target in targets:
            target_node = passage_node_id(*target)
            triple = (passage_uuid(target_node), argument_id, "evidenced_by")
            if triple in citation_triples:
                continue
            row = {
                "citation_type": triple[2],
                "confidence": 1.0,
                "kg_node_id": triple[1],
                "passage_id": triple[0],
            }
            citations.append(row)
            new_citations.append(row)
            citation_triples.add(triple)

    manifest_matches = [
        row for row in manifest if row.get("canonical_id") == CORPUS_WORK_ID
    ]
    if len(manifest_matches) != 1:
        raise ValueError(
            f"expected one Clement Stromata manifest row, got {len(manifest_matches)}"
        )
    manifest_row = manifest_matches[0]
    manifest_row.update(
        {
            "passages": sum(
                row.get("work_canonical_id") == CORPUS_WORK_ID for row in passages
            ),
            "source": (
                "local TEI: tlg0555.tlg004.perseus-grc2, Stahlin GCS 15 "
                "(I-VI, 1906); primary-grounding wave 2026-08-18"
            ),
            "ingest_class": "tlg_local_critical_edition",
            "status": "in_corpus",
        }
    )
    if manifest_row["passages"] != 61:
        raise ValueError(
            f"expected 61 Clement corpus passages, got {manifest_row['passages']}"
        )

    return {
        "new_nodes": new_nodes,
        "new_edges": new_edges,
        "removed_edges": removed_edges,
        "new_passages": new_passages,
        "new_citations": new_citations,
        "removed_citations": removed_citations,
    }


def assert_unique(rows: list[dict[str, Any]], field: str, label: str) -> None:
    values = [str(row.get(field) or "") for row in rows]
    duplicates = [value for value, count in Counter(values).items() if count > 1]
    if duplicates:
        raise ValueError(f"duplicate {label}: {duplicates[:10]}")


def validate_state(
    before: dict[str, list[dict[str, Any]]],
    after: dict[str, list[dict[str, Any]]],
    delta: dict[str, Any],
) -> dict[str, Any]:
    nodes = after["nodes"]
    edges = after["edges"]
    passages = after["passages"]
    citations = after["citations"]

    assert_unique(nodes, "id", "node ids")
    assert_unique(edges, "edge_id", "edge ids")
    assert_unique(passages, "passage_id", "passage ids")
    edge_triples = [edge_triple(edge) for edge in edges]
    if len(edge_triples) != len(set(edge_triples)):
        raise ValueError("duplicate edge triples after transform")

    node_ids = {node_id(node) for node in nodes}
    missing_endpoints = [
        edge.get("edge_id")
        for edge in edges
        if edge_triple(edge)[0] not in node_ids or edge_triple(edge)[2] not in node_ids
    ]
    if missing_endpoints:
        raise ValueError(f"missing edge endpoints: {missing_endpoints[:10]}")

    corpus_debt = corpus_violations(passages, citations, node_ids)
    corpus_counts = {name: len(rows) for name, rows in corpus_debt.items()}
    if any(corpus_counts.values()):
        raise ValueError(f"corpus invariants failed: {corpus_counts}")

    _, before_parity = parity_violations(
        before["nodes"], before["passages"], before["citations"]
    )
    shared, after_parity = parity_violations(nodes, passages, citations)
    before_signature = {
        (row["node_id"], row["passage_id"], row["field"], row["reason"])
        for row in before_parity
    }
    after_signature = {
        (row["node_id"], row["passage_id"], row["field"], row["reason"])
        for row in after_parity
    }
    new_parity = sorted(after_signature - before_signature)
    if new_parity:
        raise ValueError(f"new KG/corpus parity violations: {new_parity[:10]}")
    removed_parity = before_signature - after_signature
    if any(
        not signature[0].startswith("passage_clement_strom_")
        for signature in removed_parity
    ):
        raise ValueError(
            "this wave must not silently rewrite unrelated legacy parity debt: "
            f"{sorted(removed_parity)[:10]}"
        )

    # Enforce R1-R18 against only the novel graph delta.
    with tempfile.TemporaryDirectory(prefix="eleutheria-clement-gate-") as tmp:
        delta_path = Path(tmp) / "delta.json"
        delta_path.write_text(
            json.dumps(
                {"nodes": delta["new_nodes"], "edges": delta["new_edges"]},
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        gate = subprocess.run(
            [sys.executable, str(GATE_PATH), "--new-only", str(delta_path)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
    if gate.returncode != 0:
        raise ValueError(f"R1-R18 delta gate failed:\n{gate.stdout}\n{gate.stderr}")
    if "BLOCK: 0" not in gate.stdout:
        raise ValueError(f"R1-R18 gate did not report BLOCK 0:\n{gate.stdout}")

    return {
        "corpus_counts": corpus_counts,
        "parity_violations": len(after_parity),
        "shared_twins": shared,
        "gate_output": gate.stdout.strip(),
    }


def backup_once(path: Path) -> Path:
    backup = path.with_name(path.name + BACKUP_SUFFIX)
    if not backup.exists():
        shutil.copy2(path, backup)
    return backup


def main() -> int:
    args = parse_args()
    xml_source = args.xml_source.expanduser().resolve()
    if not xml_source.exists():
        print(f"ABORT: source XML not found: {xml_source}")
        return 1
    actual_hash = sha256(xml_source)
    if actual_hash != XML_SHA256:
        print(
            "ABORT: source XML hash mismatch; refusing to ingest a different edition\n"
            f"expected {XML_SHA256}\nactual   {actual_hash}"
        )
        return 1

    try:
        sections = extract_sections(edition_root(xml_source))
        before = {
            "nodes": read_jsonl(NODES_PATH),
            "edges": read_jsonl(EDGES_PATH),
            "passages": read_jsonl(PASSAGES_PATH),
            "citations": read_jsonl(CITATIONS_PATH),
            "manifest": read_jsonl(MANIFEST_PATH),
        }
        after = copy.deepcopy(before)
        now = datetime.now(UTC).isoformat(sep=" ")
        delta = transform(
            after["nodes"],
            after["edges"],
            after["passages"],
            after["citations"],
            after["manifest"],
            sections,
            now,
        )
        validation = validate_state(before, after, delta)
    except (AssertionError, OSError, ValueError, ET.ParseError) as exc:
        print(f"ABORT: {exc}")
        return 1

    summary = {
        "mode": "apply" if args.apply else "dry-run",
        "source_sha256": actual_hash,
        "targets": len(TARGETS),
        "new_nodes": len(delta["new_nodes"]),
        "new_edges": len(delta["new_edges"]),
        "removed_edges": len(delta["removed_edges"]),
        "new_corpus_passages": len(delta["new_passages"]),
        "new_corpus_citations": len(delta["new_citations"]),
        "removed_corpus_citations": len(delta["removed_citations"]),
        "counts": {
            name: [len(before[name]), len(after[name])]
            for name in ("nodes", "edges", "passages", "citations")
        },
        "shared_twins_after": validation["shared_twins"],
        "parity_violations_after": validation["parity_violations"],
        "corpus_invariants": validation["corpus_counts"],
    }

    print(validation["gate_output"])
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))

    if not args.apply:
        print("dry-run: nothing written (use --apply after review)")
        return 0

    paths = {
        "nodes": NODES_PATH,
        "edges": EDGES_PATH,
        "passages": PASSAGES_PATH,
        "citations": CITATIONS_PATH,
        "manifest": MANIFEST_PATH,
    }
    backups = {name: str(backup_once(path)) for name, path in paths.items()}
    for name, path in paths.items():
        write_jsonl(path, after[name])
    print(json.dumps({"status": "applied", "backups": backups}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
