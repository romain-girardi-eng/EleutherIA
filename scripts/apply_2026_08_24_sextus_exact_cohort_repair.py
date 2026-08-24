#!/usr/bin/env python3
"""Prepare the fail-closed Sextus PH/AM exact-cohort migration.

The legacy ``passage_sext_1..534`` snapshot is made of fixed-width OCR chunks.
It contains twelve proved cross-book/cross-work concatenations, six invalid
``Pr.`` pseudo-CTS loci, overlapping section boundaries, and independently
audited internal omissions.  This migration retires that active legacy cohort,
deduplicates the existing partial AM IX-X section ingest, and constructs a
single exact, section-level OGL cohort for both works.

Dry-run is the default and never writes.  ``--write`` is intended for tests on
an explicit copied ``--data-root``.  Production writes are additionally locked
behind ``--production-write-approved`` so the concurrent Irenaeus migration can
finish before Sextus touches shared JSONL data.

No registry file is written by this script.  The open registry issue remains
open until the future production application, independent review, and
adversarial gates have completed.
"""

from __future__ import annotations

import argparse
import copy
import fcntl
import hashlib
import json
import os
import re
import tempfile
import unicodedata
import urllib.request
import uuid
import xml.etree.ElementTree as ET
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_ROOT = ROOT / "data"

STAMP = "sextus_exact_cohort_repair_2026_08_24"
UPDATED_AT = "2026-08-24 05:30:00+00:00"
OGL_COMMIT = "7881c563436f52fb3550e6daa6df94be1b83b0e3"

PERSON_NODE = "person_sextus_empiricus_c160_210ce_d4f8a2b1"
PH_WORK_NODE = "work_sextus_outlines_pyrrhonism_f9a7c8e4"
AM_WORK_NODE = "work_sextus_adversus_mathematicos"
ARGUMENT_NODE = "argument_sextus_equipollence_argument_7d4b9e2a"

PH_WORK_URN = "urn:cts:greekLit:tlg0544.tlg001"
AM_WORK_URN = "urn:cts:greekLit:tlg0544.tlg002"
PH_EDITION_URN = f"{PH_WORK_URN}.1st1K-grc1"
AM_EDITION_URN = f"{AM_WORK_URN}.1st1K-grc1"
PH_CANONICAL_ID = "urn_cts_greeklit_tlg0544_tlg001_grc"
AM_CANONICAL_ID = "urn_cts_greeklit_tlg0544_tlg002_grc"

PH_TITLE = "Pyrrhoniae Hypotyposes (Πυρρώνειοι ὑποτυπώσεις)"
AM_TITLE = "Adversus Mathematicos (Books I-XI)"

OGL_BASE = (
    "https://raw.githubusercontent.com/OpenGreekAndLatin/First1KGreek/"
    f"{OGL_COMMIT}/data/tlg0544"
)
OGL_URLS = {
    "ph_cts": f"{OGL_BASE}/tlg001/__cts__.xml",
    "ph_tei": f"{OGL_BASE}/tlg001/tlg0544.tlg001.1st1K-grc1.xml",
    "am_cts": f"{OGL_BASE}/tlg002/__cts__.xml",
    "am_tei": f"{OGL_BASE}/tlg002/tlg0544.tlg002.1st1K-grc1.xml",
}
OGL_SHA256 = {
    "ph_cts": "f13598c93c843c9de4e71639c480c6d8f11bcecd2aa601a1818e60c179db79b6",
    "ph_tei": "6aa8ff81867ed4fa78b8681ff38cb3305a47a76cd1f61209da9f66ddb88a9ddc",
    "am_cts": "e8532aec4b64b6f2cf8b09dfc3cafde5662b93f9bdb6930884642faff7ce0659",
    "am_tei": "342c8623d25ef987af187ebe5053dbd8cd83dbd48e18711e8ef5c9dc22cf9278",
}

EXPECTED_BOOK_COUNTS = {
    "ph": {1: 241, 2: 259, 3: 281},
    "am": {
        1: 320,
        2: 113,
        3: 116,
        4: 34,
        5: 106,
        6: 68,
        7: 446,
        8: 481,
        9: 440,
        10: 351,
        11: 257,
    },
}
EXPECTED_SECTION_COUNTS = {"ph": 781, "am": 2732}
EXPECTED_EXACT_TOTAL = 3513
EXPECTED_LEGACY_TOTAL = 534
EXPECTED_LEGACY_INCIDENT_EDGES = 1072
EXPECTED_PARTIAL_EXACT_TOTAL = 791

# Fixed values are below Number.MAX_SAFE_INTEGER and are disjoint from the
# current global sequence space.  Validation also rejects any non-target
# collision before a migration can be written.
PH_SEQUENCE_BASE = 654_400_100_000_000
AM_SEQUENCE_BASE = 654_400_200_000_000

BOUNDARY_CONCAT_NODES = frozenset(
    {
        "passage_sext_41",
        "passage_sext_137",
        "passage_sext_205",
        "passage_sext_276",
        "passage_sext_336",
        "passage_sext_385",
        "passage_sext_420",
        "passage_sext_472",
        "passage_sext_489",
        "passage_sext_506",
        "passage_sext_511",
        "passage_sext_525",
    }
)
PSEUDO_PR_NODES = frozenset(f"passage_sext_{number}" for number in range(421, 427))
PROVED_QUARANTINE_NODES = BOUNDARY_CONCAT_NODES | PSEUDO_PR_NODES
LEGACY_NODE_RE = re.compile(r"passage_sext_(\d+)$")

QUARANTINE_RELATIVE = "audit/2026-08-24_sextus_exact_cohort_quarantine.jsonl"
PLAN_RELATIVE = "audit/2026-08-24_sextus_exact_cohort_plan.json"


@dataclass(frozen=True)
class WorkSpec:
    key: str
    work_urn: str
    edition_urn: str
    canonical_id: str
    work_node: str
    title: str
    ref_prefix: str
    sequence_base: int
    tei_key: str
    cts_key: str


WORKS = {
    "ph": WorkSpec(
        key="ph",
        work_urn=PH_WORK_URN,
        edition_urn=PH_EDITION_URN,
        canonical_id=PH_CANONICAL_ID,
        work_node=PH_WORK_NODE,
        title=PH_TITLE,
        ref_prefix="PH",
        sequence_base=PH_SEQUENCE_BASE,
        tei_key="ph_tei",
        cts_key="ph_cts",
    ),
    "am": WorkSpec(
        key="am",
        work_urn=AM_WORK_URN,
        edition_urn=AM_EDITION_URN,
        canonical_id=AM_CANONICAL_ID,
        work_node=AM_WORK_NODE,
        title=AM_TITLE,
        ref_prefix="M.",
        sequence_base=AM_SEQUENCE_BASE,
        tei_key="am_tei",
        cts_key="am_cts",
    ),
}


@dataclass(frozen=True)
class ExactSection:
    work_key: str
    book: int
    section: int
    text: str
    text_sha256_nfc: str

    @property
    def work(self) -> WorkSpec:
        return WORKS[self.work_key]

    @property
    def locus(self) -> str:
        return f"{self.book}.{self.section}"

    @property
    def cts_urn(self) -> str:
        return f"{self.work.edition_urn}:{self.locus}"

    @property
    def canonical_ref(self) -> str:
        return f"{self.work.ref_prefix} {self.locus}"

    @property
    def passage_id(self) -> str:
        return stable_uuid(f"passage:{self.cts_urn}")

    @property
    def node_id(self) -> str:
        return f"passage_sextus_{self.work_key}_{self.book}_{self.section}_ogl_{OGL_COMMIT[:8]}"

    @property
    def sequence_number(self) -> int:
        return self.work.sequence_base + self.book * 1_000 + self.section


@dataclass(frozen=True)
class AuthoritySnapshot:
    sections: tuple[ExactSection, ...]
    file_sha256: dict[str, str]
    catalog_facts: dict[str, dict[str, str]]

    @property
    def by_key(self) -> dict[tuple[str, int, int], ExactSection]:
        return {(row.work_key, row.book, row.section): row for row in self.sections}


@dataclass(frozen=True)
class RewireDecision:
    decision_id: str
    old_edge_id: str
    expected_source: str
    relation: str
    expected_target: str
    locus_endpoint: str
    replacement_loci: tuple[tuple[str, int, int], ...]
    rationale: str


@dataclass(frozen=True)
class CitationRewireDecision:
    decision_id: str
    kg_node_id: str
    citation_type: str
    confidence: float
    old_passage_id: str
    target_locus: tuple[str, int, int]
    rationale: str


# Every non-structural edge that would otherwise dangle, plus every broad
# work-level source_for edge, has an explicit semantic adjudication.  The
# Epi-Ison edge is removed without replacement because its target node itself
# records the Sextus link as a false positive.
REWIRE_DECISIONS = (
    RewireDecision(
        "school_pyrrhonism_definition",
        "abfe5162-4a97-4574-91c7-37f4e1fccc01",
        "school_pyrrhonism",
        "evidenced_by",
        "passage_sext_1",
        "target",
        (("ph", 1, 4),),
        "PH I.4 explicitly distinguishes skeptical philosophy and announces its account.",
    ),
    RewireDecision(
        "school_pyrrhonism_name",
        "b24764d2-9423-4932-8a89-894c9f56c0b6",
        "school_pyrrhonism",
        "evidenced_by",
        "passage_sext_2",
        "target",
        (("ph", 1, 7),),
        "PH I.7 names and explains the Pyrrhonian skeptical approach.",
    ),
    RewireDecision(
        "posidonius_philosophy_image",
        "c0ab4122-a22e-42be-abe4-4f614faeff89",
        "passage_sext_139",
        "discusses",
        "person_posidonius_apameia_135_51bce",
        "source",
        (("am", 7, 19),),
        "AM VII.19 is the exact section naming Posidonius in the legacy 139 span.",
    ),
    RewireDecision(
        "posidonius_timaeus",
        "85191dfa-b08a-4a6f-a329-4de96dfb1c46",
        "passage_sext_150",
        "discusses",
        "person_posidonius_apameia_135_51bce",
        "source",
        (("am", 7, 93),),
        "AM VII.93 is the exact section naming Posidonius's Timaeus exegesis.",
    ),
    RewireDecision(
        "equipollence_argument_general_method",
        "08ac4ed5-1d76-4ac7-9d8a-0b215d51cc44",
        PH_WORK_NODE,
        "source_for",
        ARGUMENT_NODE,
        "source",
        (("ph", 1, 8), ("ph", 1, 10)),
        "PH I.8 and I.10 directly define isostheneia, epochē, and the general method; the fate-specific application remains marked reconstructed.",
    ),
    RewireDecision(
        "epi_ison_false_positive",
        "3a85d8d1-7019-491c-9a9c-af7ff0c635d7",
        PH_WORK_NODE,
        "source_for",
        "concept_epi_ison_in_equal_parts_9e1e47f1",
        "source",
        (),
        "The concept node records this Sextus work link as false_positive_attested; remove it without replacement.",
    ),
    RewireDecision(
        "isostheneia_definition_and_effect",
        "735b0818-5304-41ca-84cc-a5fe3f4b0506",
        PH_WORK_NODE,
        "source_for",
        "concept_isostheneia_4b7e9c3a",
        "source",
        (("ph", 1, 8), ("ph", 1, 10), ("ph", 1, 26), ("ph", 1, 29)),
        "The selected exact sections cover definition, suspension, and the reported transition to tranquility.",
    ),
    RewireDecision(
        "pithanon_tripartite_criterion",
        "dbd74db2-089a-45ae-9c9d-c166cdf380ac",
        PH_WORK_NODE,
        "source_for",
        "concept_pithanon_8f3a6d2c",
        "source",
        (("am", 7, 166), ("am", 7, 169), ("am", 7, 176), ("am", 7, 181), ("am", 7, 184)),
        "AM VII.166, 169, 176, 181, and 184 directly establish the probable, uncontradicted, and fully examined criteria.",
    ),
    RewireDecision(
        "skeptical_agency_fourfold_observance",
        "3aa6a129-0c08-4f93-ac60-4468b352ec49",
        PH_WORK_NODE,
        "source_for",
        "concept_skeptical_agency_i9j0k1l2",
        "source",
        (("ph", 1, 21), ("ph", 1, 22), ("ph", 1, 23), ("ph", 1, 24)),
        "PH I.21-24 is the exact fourfold practical-observance locus named by the concept.",
    ),
)


CITATION_REWIRE_DECISIONS = (
    CitationRewireDecision(
        "citation_school_pyrrhonism_definition",
        "school_pyrrhonism",
        "evidenced_by",
        0.4,
        "a1426458-856d-4582-9368-ae5becf86bff",
        ("ph", 1, 4),
        "The legacy PH I.1-5 chunk is retired; PH I.4 is the exact section distinguishing skeptical philosophy.",
    ),
    CitationRewireDecision(
        "citation_school_pyrrhonism_name",
        "school_pyrrhonism",
        "evidenced_by",
        0.4,
        "2a03d1ba-0168-4763-9a0e-1211e3b5a331",
        ("ph", 1, 7),
        "The legacy PH I.5-9 chunk is retired; PH I.7 exactly names and explains the Pyrrhonian approach.",
    ),
    CitationRewireDecision(
        "citation_posidonius_philosophy_image",
        "person_posidonius_apameia_135_51bce",
        "discusses",
        1.0,
        "b4014b0a-ef66-4959-a4bf-7718758b6751",
        ("am", 7, 19),
        "AM VII.19 is the exact section naming Posidonius in the retired AM VII.11-19 chunk.",
    ),
    CitationRewireDecision(
        "citation_posidonius_timaeus",
        "person_posidonius_apameia_135_51bce",
        "discusses",
        1.0,
        "4261e21a-091a-40aa-a2e8-cd938be6f702",
        ("am", 7, 93),
        "AM VII.93 is the exact section naming Posidonius in the retired AM VII.88-93 chunk.",
    ),
)


@dataclass
class MigrationResult:
    nodes: list[dict[str, Any]]
    edges: list[dict[str, Any]]
    passages: list[dict[str, Any]]
    citations: list[dict[str, Any]]
    manifest: list[dict[str, Any]]
    quarantine: list[dict[str, Any]]
    changes: Counter[str]
    plan: dict[str, Any]


@dataclass(frozen=True)
class DataSnapshot:
    nodes: list[dict[str, Any]]
    edges: list[dict[str, Any]]
    passages: list[dict[str, Any]]
    citations: list[dict[str, Any]]
    manifest: list[dict[str, Any]]
    original_bytes: dict[str, bytes]

    @property
    def rows(self) -> tuple[
        list[dict[str, Any]],
        list[dict[str, Any]],
        list[dict[str, Any]],
        list[dict[str, Any]],
        list[dict[str, Any]],
    ]:
        return self.nodes, self.edges, self.passages, self.citations, self.manifest


def stable_uuid(value: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"eleutheria:{STAMP}:{value}"))


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def normalize_text(value: str) -> str:
    return " ".join(unicodedata.normalize("NFC", value).split())


def sha256_text(value: str) -> str:
    return hashlib.sha256(normalize_text(value).encode("utf-8")).hexdigest()


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


def edge_source(edge: dict[str, Any]) -> str:
    return str(edge.get("source_id") or edge.get("source") or "")


def edge_target(edge: dict[str, Any]) -> str:
    return str(edge.get("target_id") or edge.get("target") or "")


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


def citation_key(row: dict[str, Any]) -> str:
    return "\x1f".join(
        (
            str(row.get("kg_node_id") or ""),
            str(row.get("passage_id") or ""),
            str(row.get("citation_type") or ""),
        )
    )


def fetch_url(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "EleutherIA-Sextus-audit/1.0"})
    with urllib.request.urlopen(request, timeout=30) as response:  # noqa: S310
        return response.read()


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _section_text(element: ET.Element) -> str:
    parts: list[str] = []

    def walk(current: ET.Element) -> None:
        if current.text:
            parts.append(current.text)
        for child in current:
            if local_name(child.tag) not in {"note", "head"}:
                walk(child)
            if child.tail:
                parts.append(child.tail)

    walk(element)
    return normalize_text("".join(parts))


def _catalog_facts(raw: bytes) -> tuple[str, str, str]:
    root = ET.fromstring(raw)
    namespace = {"ti": "http://chs.harvard.edu/xmlns/cts"}
    title = root.findtext("ti:title", namespaces=namespace) or ""
    edition = root.find("ti:edition", namespace)
    if edition is None:
        raise RuntimeError("OGL CTS catalog lacks edition")
    return str(root.get("urn") or ""), title, str(edition.get("urn") or "")


def parse_tei_sections(
    raw: bytes, work_key: str, *, enforce_complete: bool = True
) -> dict[tuple[int, int], str]:
    """Extract canonical book.section text, excluding notes and headings.

    OGL PH has a documented structural wrinkle at the II/III boundary: a final
    sentence of PH II.259 is physically placed in PH book III, chapter 0, as
    ``section n=1``.  The real PH III.1 is then split over chapters 1 and 2.
    PH III.265 and III.273 are also split across adjacent chapter divs.  We
    route the chapter-0 fragment back to II.259 and concatenate repeated
    section numbers in document order.  This yields the scholarly 241/259/281
    section topology without dropping any main-text fragment.
    """

    if work_key not in WORKS:
        raise ValueError(f"unknown Sextus work key: {work_key}")
    root = ET.fromstring(raw)
    edition = next(
        (
            element
            for element in root.iter()
            if local_name(element.tag) == "div" and element.get("type") == "edition"
        ),
        None,
    )
    if edition is None or edition.get("n") != WORKS[work_key].edition_urn:
        raise RuntimeError(f"{work_key} TEI edition div is absent or mislabeled")

    collected: dict[tuple[int, int], list[str]] = {}

    def collect_section(
        section: ET.Element, *, book_number: int, chapter_number: str
    ) -> None:
        raw_number = str(section.get("n") or "")
        if not raw_number.isdigit():
            # TOCs and the PH codex endnote are metadata, not CTS text.
            return
        target_book = book_number
        target_section = int(raw_number)
        if work_key == "ph" and book_number == 3 and chapter_number == "0":
            if target_section != 1:
                raise RuntimeError("unexpected PH III chapter-0 section topology")
            target_book, target_section = 2, 259
        text = _section_text(section)
        if not text:
            raise RuntimeError(
                f"empty OGL section {work_key} {book_number}.{raw_number}"
            )
        collected.setdefault((target_book, target_section), []).append(text)

    for book in edition:
        if local_name(book.tag) != "div" or book.get("subtype") != "book":
            continue
        book_number = int(str(book.get("n")))
        for child in book:
            if local_name(child.tag) != "div":
                continue
            if child.get("subtype") == "section":
                collect_section(child, book_number=book_number, chapter_number="")
                continue
            if child.get("subtype") != "chapter":
                continue
            chapter_number = str(child.get("n") or "")
            for section in child.iter():
                if local_name(section.tag) == "div" and section.get("subtype") == "section":
                    collect_section(
                        section,
                        book_number=book_number,
                        chapter_number=chapter_number,
                    )

    merged = {key: normalize_text(" ".join(parts)) for key, parts in collected.items()}
    if enforce_complete:
        expected = EXPECTED_BOOK_COUNTS[work_key]
        actual = Counter(book for book, _section in merged)
        if dict(sorted(actual.items())) != expected:
            raise RuntimeError(
                f"{work_key} book cardinality drift: {dict(sorted(actual.items()))}"
            )
        for book, count in expected.items():
            numbers = {section for found_book, section in merged if found_book == book}
            if numbers != set(range(1, count + 1)):
                raise RuntimeError(f"{work_key} book {book} section topology is not contiguous")
    return merged


def authority_from_bytes(raw_files: dict[str, bytes]) -> AuthoritySnapshot:
    if set(raw_files) != set(OGL_URLS):
        raise RuntimeError(f"authority file set mismatch: {sorted(raw_files)}")
    for key, raw in raw_files.items():
        digest = sha256_bytes(raw)
        if digest != OGL_SHA256[key]:
            raise RuntimeError(f"pinned OGL {key} SHA-256 drift: {digest}")

    ph_facts = _catalog_facts(raw_files["ph_cts"])
    am_facts = _catalog_facts(raw_files["am_cts"])
    if ph_facts != (PH_WORK_URN, "Pyrrhoniae Hypotyposes", PH_EDITION_URN):
        raise RuntimeError(f"unexpected PH CTS catalog facts: {ph_facts}")
    if am_facts != (AM_WORK_URN, "Adversus Mathematicos", AM_EDITION_URN):
        raise RuntimeError(f"unexpected AM CTS catalog facts: {am_facts}")

    sections: list[ExactSection] = []
    for work_key in ("ph", "am"):
        parsed = parse_tei_sections(raw_files[WORKS[work_key].tei_key], work_key)
        for (book, section), text in sorted(parsed.items()):
            sections.append(
                ExactSection(
                    work_key=work_key,
                    book=book,
                    section=section,
                    text=text,
                    text_sha256_nfc=sha256_text(text),
                )
            )
    if len(sections) != EXPECTED_EXACT_TOTAL:
        raise RuntimeError(f"expected {EXPECTED_EXACT_TOTAL} exact sections, found {len(sections)}")
    return AuthoritySnapshot(
        sections=tuple(sections),
        file_sha256=copy.deepcopy(OGL_SHA256),
        catalog_facts={
            "ph": {"work_urn": ph_facts[0], "title": ph_facts[1], "edition_urn": ph_facts[2]},
            "am": {"work_urn": am_facts[0], "title": am_facts[1], "edition_urn": am_facts[2]},
        },
    )


def load_authority(authority_dir: Path | None = None) -> AuthoritySnapshot:
    if authority_dir is None:
        raw = {key: fetch_url(url) for key, url in OGL_URLS.items()}
    else:
        directory = authority_dir.expanduser().resolve()
        filenames = {
            "ph_cts": "ph-cts.xml",
            "ph_tei": "ph.xml",
            "am_cts": "am-cts.xml",
            "am_tei": "am.xml",
        }
        raw = {key: (directory / name).read_bytes() for key, name in filenames.items()}
    return authority_from_bytes(raw)


def make_passage(section: ExactSection) -> dict[str, Any]:
    return {
        "canonical_ref": section.canonical_ref,
        "char_length": len(section.text),
        "cts_urn": section.cts_urn,
        "ingest_class": "ogl_exact_section",
        "language": "grc",
        "passage_id": section.passage_id,
        "passage_role": "original",
        "sequence_number": section.sequence_number,
        "source_commit": OGL_COMMIT,
        "source_tei_sha256": OGL_SHA256[section.work.tei_key],
        "source_tei_url": OGL_URLS[section.work.tei_key],
        "text_content": section.text,
        "text_sha256_nfc": section.text_sha256_nfc,
        "word_count": len(section.text.split()),
        "work_canonical_id": section.work.canonical_id,
        "work_urn": section.work.work_urn,
    }


def make_node(section: ExactSection) -> dict[str, Any]:
    return {
        "alternative_names": "[]",
        "created_at": UPDATED_AT,
        "description": section.text,
        "id": section.node_id,
        "label": f"Sextus Empiricus, {section.work.title}, {section.canonical_ref}",
        "metadata": {
            STAMP: {
                "authority": "OpenGreekAndLatin First1KGreek",
                "authority_commit": OGL_COMMIT,
                "source_tei_sha256": OGL_SHA256[section.work.tei_key],
            },
            "attestation_type": "direct",
            "author": "Sextus Empiricus",
            "auto_generated": True,
            "canonical_ref": section.canonical_ref,
            "char_length": len(section.text),
            "cts_urn": section.cts_urn,
            "db_passage_id": section.passage_id,
            "language": "grc",
            "passage_role": "original",
            "school": "Skeptic",
            "text_sha256_nfc": section.text_sha256_nfc,
            "word_count": len(section.text.split()),
            "work_canonical_id": section.work.work_urn,
            "work_title": section.work.title,
        },
        "node_id": section.node_id,
        "period": "Roman Imperial",
        "role": None,
        "school": "Skeptic",
        "type": "passage",
        "updated_at": UPDATED_AT,
    }


def make_edge(
    source: str, relation: str, target: str, *, metadata_value: dict[str, Any] | None = None
) -> dict[str, Any]:
    return {
        "created_at": UPDATED_AT,
        "edge_id": stable_uuid(f"edge:{source}:{relation}:{target}"),
        "metadata": metadata_value or {STAMP: True},
        "relation": relation,
        "source": source,
        "source_id": source,
        "target": target,
        "target_id": target,
        "weight": 1.0,
    }


def make_snapshot_citation(section: ExactSection) -> dict[str, Any]:
    return {
        "citation_type": "snapshot_passage_node",
        "confidence": 1.0,
        "kg_node_id": section.node_id,
        "passage_id": section.passage_id,
    }


def make_rewired_citation(
    decision: CitationRewireDecision, authority: AuthoritySnapshot
) -> dict[str, Any]:
    section = _expected_section(authority, decision.target_locus)
    return {
        "citation_type": decision.citation_type,
        "confidence": decision.confidence,
        "kg_node_id": decision.kg_node_id,
        "passage_id": section.passage_id,
    }


def _legacy_number(value: str) -> int | None:
    match = LEGACY_NODE_RE.fullmatch(value)
    return int(match.group(1)) if match else None


def _is_current_exact_row(row: dict[str, Any]) -> bool:
    urn = str(row.get("cts_urn") or "")
    return urn.startswith(PH_EDITION_URN + ":") or urn.startswith(AM_EDITION_URN + ":")


def _quarantine_reason_for_legacy(node_name: str) -> str:
    if node_name in BOUNDARY_CONCAT_NODES:
        return "proved_cross_book_or_cross_work_concatenation"
    if node_name in PSEUDO_PR_NODES:
        return "proved_invalid_pseudo_pr_or_internal_heading_span"
    return "legacy_fixed_width_non_exact_superseded_by_complete_exact_cohort"


def quarantine_record(
    record_type: str, record: dict[str, Any], reason: str
) -> dict[str, Any]:
    return {
        "migration": STAMP,
        "reason": reason,
        "record": copy.deepcopy(record),
        "record_type": record_type,
    }


def _expected_section(authority: AuthoritySnapshot, locus: tuple[str, int, int]) -> ExactSection:
    try:
        return authority.by_key[locus]
    except KeyError as exc:
        raise RuntimeError(f"rewire target locus missing from authority: {locus}") from exc


def _validate_rewire_preconditions(edges: list[dict[str, Any]]) -> None:
    by_id = {edge_id(row): row for row in edges}
    if len(by_id) != len(edges):
        raise RuntimeError("duplicate KG edge ids")
    for decision in REWIRE_DECISIONS:
        edge = by_id.get(decision.old_edge_id)
        if edge is None:
            raise RuntimeError(f"missing rewire edge {decision.old_edge_id}")
        actual = (edge_source(edge), str(edge.get("relation") or ""), edge_target(edge))
        wanted = (decision.expected_source, decision.relation, decision.expected_target)
        if actual != wanted:
            raise RuntimeError(
                f"rewire edge drift for {decision.decision_id}: {actual} != {wanted}"
            )


def _input_context(
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    passages: list[dict[str, Any]],
    citations: list[dict[str, Any]],
    manifest: list[dict[str, Any]],
    authority: AuthoritySnapshot,
) -> dict[str, Any]:
    del manifest
    by_node = {node_id(row): row for row in nodes}
    if len(by_node) != len(nodes):
        raise RuntimeError("duplicate KG node ids")
    legacy = {
        name: row
        for name, row in by_node.items()
        if (number := _legacy_number(name)) is not None and 1 <= number <= EXPECTED_LEGACY_TOTAL
    }
    expected_legacy = {f"passage_sext_{number}" for number in range(1, EXPECTED_LEGACY_TOTAL + 1)}
    if set(legacy) != expected_legacy:
        raise RuntimeError(
            f"legacy Sextus node topology drift: found {len(legacy)} of {EXPECTED_LEGACY_TOTAL}"
        )

    legacy_citations = [
        row
        for row in citations
        if str(row.get("kg_node_id") or "") in expected_legacy
        and row.get("citation_type") == "snapshot_passage_node"
    ]
    citation_counts = Counter(str(row.get("kg_node_id") or "") for row in legacy_citations)
    if len(legacy_citations) != EXPECTED_LEGACY_TOTAL or set(citation_counts.values()) != {1}:
        raise RuntimeError("legacy Sextus snapshot citation mapping is not bijective")
    legacy_passage_ids = {str(row.get("passage_id") or "") for row in legacy_citations}
    corpus_by_id = {str(row.get("passage_id") or ""): row for row in passages}
    if len(corpus_by_id) != len(passages) or not legacy_passage_ids.issubset(corpus_by_id):
        raise RuntimeError("legacy Sextus corpus twins are missing or duplicated")

    legacy_non_snapshot_citations = [
        row
        for row in citations
        if str(row.get("passage_id") or "") in legacy_passage_ids
        and row.get("citation_type") != "snapshot_passage_node"
    ]
    expected_related = {
        citation_key(
            {
                "kg_node_id": decision.kg_node_id,
                "passage_id": decision.old_passage_id,
                "citation_type": decision.citation_type,
            }
        ): decision
        for decision in CITATION_REWIRE_DECISIONS
    }
    actual_related = {citation_key(row): row for row in legacy_non_snapshot_citations}
    if set(actual_related) != set(expected_related):
        raise RuntimeError(
            "legacy Sextus non-snapshot citation topology drift: "
            f"{sorted(actual_related)}"
        )
    for key, row in actual_related.items():
        decision = expected_related[key]
        if float(row.get("confidence")) != decision.confidence:
            raise RuntimeError(
                f"legacy Sextus citation confidence drift: {decision.decision_id}"
            )

    incident_edges = [
        row
        for row in edges
        if edge_source(row) in expected_legacy or edge_target(row) in expected_legacy
    ]
    if len(incident_edges) != EXPECTED_LEGACY_INCIDENT_EDGES:
        raise RuntimeError(
            f"legacy Sextus incident-edge drift: {len(incident_edges)} != {EXPECTED_LEGACY_INCIDENT_EDGES}"
        )
    structural = Counter(str(row.get("relation") or "") for row in incident_edges)
    if structural != Counter(
        {"authored_by": 534, "part_of": 534, "discusses": 2, "evidenced_by": 2}
    ):
        raise RuntimeError(f"legacy Sextus relation topology drift: {structural}")

    _validate_rewire_preconditions(edges)
    current_exact = [row for row in passages if _is_current_exact_row(row)]
    if len(current_exact) != EXPECTED_PARTIAL_EXACT_TOTAL:
        raise RuntimeError(
            f"partial exact Sextus cohort drift: {len(current_exact)} != {EXPECTED_PARTIAL_EXACT_TOTAL}"
        )
    book_counts: Counter[int] = Counter()
    authority_by_cts = {section.cts_urn: section for section in authority.sections}
    for row in current_exact:
        urn = str(row.get("cts_urn") or "")
        section = authority_by_cts.get(urn)
        if section is None or section.work_key != "am" or section.book not in {9, 10}:
            raise RuntimeError(f"unexpected row in partial exact Sextus cohort: {urn}")
        if normalize_text(str(row.get("text_content") or "")) != section.text:
            raise RuntimeError(f"existing exact Sextus text drift at {urn}")
        book_counts[section.book] += 1
    if book_counts != Counter({9: 440, 10: 351}):
        raise RuntimeError(f"partial exact book cardinality drift: {book_counts}")

    expected_new_nodes = {section.node_id for section in authority.sections}
    if expected_new_nodes & set(by_node):
        raise RuntimeError("partial target Sextus exact nodes already exist")
    expected_new_passages = {section.passage_id for section in authority.sections}
    collision = expected_new_passages & set(corpus_by_id)
    if collision:
        raise RuntimeError(f"deterministic Sextus passage-id collision: {sorted(collision)[:3]}")
    target_sequences = {section.sequence_number for section in authority.sections}
    non_target_sequences = {
        int(row["sequence_number"])
        for row in passages
        if row.get("passage_id") not in legacy_passage_ids
        and not _is_current_exact_row(row)
        and isinstance(row.get("sequence_number"), int)
    }
    if target_sequences & non_target_sequences:
        raise RuntimeError("deterministic Sextus sequence-number collision")

    for required in (PH_WORK_NODE, AM_WORK_NODE, PERSON_NODE, ARGUMENT_NODE):
        if required not in by_node:
            raise RuntimeError(f"missing required Sextus migration node: {required}")
    return {
        "legacy_nodes": legacy,
        "legacy_node_ids": expected_legacy,
        "legacy_citations": legacy_citations,
        "legacy_non_snapshot_citations": legacy_non_snapshot_citations,
        "legacy_passage_ids": legacy_passage_ids,
        "incident_edges": incident_edges,
        "current_exact": current_exact,
    }


def _enrich_work_node(node: dict[str, Any], spec: WorkSpec) -> dict[str, Any]:
    wanted = copy.deepcopy(node)
    data = metadata(wanted)
    data.update(
        {
            STAMP: {
                "authority": "OpenGreekAndLatin First1KGreek",
                "authority_commit": OGL_COMMIT,
                "catalog_url": OGL_URLS[spec.cts_key],
                "complete_exact_section_count": EXPECTED_SECTION_COUNTS[spec.key],
                "source_tei_sha256": OGL_SHA256[spec.tei_key],
                "zero_debt_cohort": True,
            },
            "canonical_id": spec.work_urn,
            "citation_verdict": "corrected",
            "citation_verified": True,
            "cts_urn": spec.edition_urn,
            "edition_urn": spec.edition_urn,
            "needs_edition_metadata": False,
            "source_tei_sha256": OGL_SHA256[spec.tei_key],
            "source_tei_url": OGL_URLS[spec.tei_key],
            "work_canonical_id": spec.work_urn,
        }
    )
    set_metadata(wanted, data)
    wanted["updated_at"] = UPDATED_AT
    return wanted


def _rewire_argument_node(node: dict[str, Any], authority: AuthoritySnapshot) -> dict[str, Any]:
    wanted = copy.deepcopy(node)
    data = metadata(wanted)
    premise_sources = {
        "P1": (("ph", 1, 8),),
        "P2": (("ph", 1, 8), ("ph", 1, 9), ("ph", 1, 10)),
        "P3": (),
        "P4": (),
        "P5": (("ph", 1, 10),),
        "P6": (("ph", 1, 8), ("ph", 1, 10)),
        "P7": (),
    }
    premises = data.get("premises")
    if not isinstance(premises, list):
        raise RuntimeError("Sextus equipollence argument premises are not structured")
    for premise in premises:
        premise_id = str(premise.get("id") or "")
        if premise_id not in premise_sources:
            raise RuntimeError(f"unexpected Sextus equipollence premise: {premise_id}")
        premise["primary_sources"] = [
            _expected_section(authority, locus).node_id for locus in premise_sources[premise_id]
        ]
        if not premise_sources[premise_id]:
            premise["attestation"] = "reconstructed"
    conclusion = data.get("conclusion")
    if not isinstance(conclusion, dict):
        raise RuntimeError("Sextus equipollence conclusion is not structured")
    conclusion["primary_sources"] = []
    conclusion["attestation"] = "reconstructed_application"
    data["primary_source_rewire_2026_08_24"] = {
        "decision": (
            "Direct premises now cite exact PH I.8-10 section nodes; the specific "
            "fate/free-will application remains explicitly reconstructed."
        ),
        "exact_source_nodes": sorted(
            {
                source
                for premise in premises
                for source in premise.get("primary_sources", [])
            }
        ),
    }
    set_metadata(wanted, data)
    wanted["updated_at"] = UPDATED_AT
    return wanted


def _manifest_row(row: dict[str, Any], spec: WorkSpec) -> dict[str, Any]:
    wanted = copy.deepcopy(row)
    wanted.update(
        {
            "author": "Sextus Empiricus",
            "canonical_id": spec.canonical_id,
            "cts_urn": spec.edition_urn,
            "division_scheme": "book.section",
            "ingest_class": "ogl_exact_section",
            "language": "grc",
            "license": "CC BY-SA 4.0",
            "passages": EXPECTED_SECTION_COUNTS[spec.key],
            "source": f"ogl:{spec.edition_urn}@{OGL_COMMIT}",
            "source_commit": OGL_COMMIT,
            "source_tei_sha256": OGL_SHA256[spec.tei_key],
            "source_url": OGL_URLS[spec.tei_key],
            "status": "in_corpus",
            "title": spec.title,
            "work_urn": spec.work_urn,
            "zero_debt_cohort": {
                "atomic_unit": "CTS book.section",
                "complete": True,
                "legacy_active_count": 0,
                "migration": STAMP,
            },
        }
    )
    return wanted


def _replacement_edges(
    authority: AuthoritySnapshot,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    edges: list[dict[str, Any]] = []
    plan_rows: list[dict[str, Any]] = []
    for decision in REWIRE_DECISIONS:
        replacements: list[dict[str, str]] = []
        for locus in decision.replacement_loci:
            section = _expected_section(authority, locus)
            if decision.locus_endpoint == "source":
                source, target = section.node_id, decision.expected_target
            elif decision.locus_endpoint == "target":
                source, target = decision.expected_source, section.node_id
            else:
                raise RuntimeError(f"invalid locus endpoint: {decision.locus_endpoint}")
            edge = make_edge(
                source,
                decision.relation,
                target,
                metadata_value={
                    STAMP: {
                        "decision_id": decision.decision_id,
                        "replaces_edge_id": decision.old_edge_id,
                        "verified_cts_urn": section.cts_urn,
                    },
                    "adjudication": decision.rationale,
                },
            )
            edges.append(edge)
            replacements.append(
                {
                    "edge_id": edge["edge_id"],
                    "source": source,
                    "target": target,
                    "verified_cts_urn": section.cts_urn,
                }
            )
        plan_rows.append(
            {
                "action": "remove_without_replacement" if not replacements else "replace",
                "decision_id": decision.decision_id,
                "old_edge_id": decision.old_edge_id,
                "rationale": decision.rationale,
                "replacements": replacements,
            }
        )
    ids = [edge_id(row) for row in edges]
    if len(ids) != len(set(ids)):
        raise RuntimeError("duplicate semantic replacement edge IDs")
    return edges, plan_rows


def _plan(
    changes: Counter[str],
    quarantine_count: int,
    rewire_rows: list[dict[str, Any]],
    citation_rewire_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "authority": {
            "commit": OGL_COMMIT,
            "file_sha256": OGL_SHA256,
            "urls": OGL_URLS,
        },
        "changes": dict(sorted(changes.items())),
        "current": {
            "dangling_non_snapshot_citations_to_retired_legacy": (
                4 if changes else 0
            ),
            "legacy_chunks": EXPECTED_LEGACY_TOTAL,
            "partial_exact_am_ix_x": EXPECTED_PARTIAL_EXACT_TOTAL,
            "proved_boundary_concatenations": len(BOUNDARY_CONCAT_NODES),
            "proved_pseudo_pr_or_heading_nodes": len(PSEUDO_PR_NODES),
        },
        "migration": STAMP,
        "production_write_locked_until_explicit_approval": True,
        "quarantine_records": quarantine_count,
        "rewire_decisions": rewire_rows,
        "citation_rewire_decisions": citation_rewire_rows,
        "target": {
            "active_legacy_chunks": 0,
            "am_exact_sections": EXPECTED_SECTION_COUNTS["am"],
            "exact_section_nodes": EXPECTED_EXACT_TOTAL,
            "exact_non_snapshot_citations": 4,
            "ph_exact_sections": EXPECTED_SECTION_COUNTS["ph"],
            "pseudo_pr_loci": 0,
            "snapshot_citations": EXPECTED_EXACT_TOTAL,
            "structural_edges": EXPECTED_EXACT_TOTAL * 2,
            "zero_debt": True,
        },
    }


def transform(
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    passages: list[dict[str, Any]],
    citations: list[dict[str, Any]],
    manifest: list[dict[str, Any]],
    authority: AuthoritySnapshot,
) -> MigrationResult:
    if len(authority.sections) != EXPECTED_EXACT_TOTAL:
        raise RuntimeError("authority snapshot does not contain the complete Sextus cohort")
    expected_node_ids = {section.node_id for section in authority.sections}
    current_node_ids = {node_id(row) for row in nodes}
    active_legacy_ids = {
        name
        for name in current_node_ids
        if (number := _legacy_number(name)) is not None and 1 <= number <= EXPECTED_LEGACY_TOTAL
    }
    present_target = expected_node_ids & current_node_ids
    if not active_legacy_ids and present_target == expected_node_ids:
        validate_zero_debt(nodes, edges, passages, citations, manifest, authority)
        return MigrationResult(
            nodes=copy.deepcopy(nodes),
            edges=copy.deepcopy(edges),
            passages=copy.deepcopy(passages),
            citations=copy.deepcopy(citations),
            manifest=copy.deepcopy(manifest),
            quarantine=[],
            changes=Counter(),
            plan=_plan(Counter(), 0, [], []),
        )
    if present_target:
        raise RuntimeError("partial Sextus exact-cohort application detected")

    context = _input_context(nodes, edges, passages, citations, manifest, authority)
    nodes_out = copy.deepcopy(nodes)
    edges_out = copy.deepcopy(edges)
    passages_out = copy.deepcopy(passages)
    citations_out = copy.deepcopy(citations)
    manifest_out = copy.deepcopy(manifest)
    quarantine: list[dict[str, Any]] = []
    changes: Counter[str] = Counter()

    legacy_ids: set[str] = context["legacy_node_ids"]
    legacy_passage_ids: set[str] = context["legacy_passage_ids"]
    legacy_snapshot_citation_keys = {
        citation_key(row) for row in context["legacy_citations"]
    }
    citation_decisions_by_old_key = {
        citation_key(
            {
                "kg_node_id": decision.kg_node_id,
                "passage_id": decision.old_passage_id,
                "citation_type": decision.citation_type,
            }
        ): decision
        for decision in CITATION_REWIRE_DECISIONS
    }
    legacy_related_citation_keys = {
        citation_key(row) for row in context["legacy_non_snapshot_citations"]
    }
    legacy_citation_keys = (
        legacy_snapshot_citation_keys | legacy_related_citation_keys
    )
    legacy_incident_edge_ids = {edge_id(row) for row in context["incident_edges"]}
    old_claim_edge_ids = {decision.old_edge_id for decision in REWIRE_DECISIONS}

    for row in nodes:
        name = node_id(row)
        if name in legacy_ids:
            quarantine.append(
                quarantine_record(
                    "kg_node_before", row, _quarantine_reason_for_legacy(name)
                )
            )
    nodes_out = [row for row in nodes_out if node_id(row) not in legacy_ids]
    changes["legacy_nodes_retired"] = len(legacy_ids)
    changes["proved_boundary_nodes_quarantined"] = len(BOUNDARY_CONCAT_NODES)
    changes["proved_pseudo_pr_nodes_quarantined"] = len(PSEUDO_PR_NODES)

    for row in passages:
        passage_id = str(row.get("passage_id") or "")
        if passage_id in legacy_passage_ids:
            legacy_node = next(
                str(citation.get("kg_node_id") or "")
                for citation in context["legacy_citations"]
                if citation.get("passage_id") == passage_id
            )
            quarantine.append(
                quarantine_record(
                    "corpus_passage_before",
                    row,
                    _quarantine_reason_for_legacy(legacy_node),
                )
            )
        elif _is_current_exact_row(row):
            quarantine.append(
                quarantine_record(
                    "corpus_passage_before",
                    row,
                    "deduplicate_partial_am_ix_x_into_complete_deterministic_exact_cohort",
                )
            )
    passages_out = [
        row
        for row in passages_out
        if str(row.get("passage_id") or "") not in legacy_passage_ids
        and not _is_current_exact_row(row)
    ]
    changes["legacy_passages_retired"] = len(legacy_passage_ids)
    changes["partial_exact_passages_replaced"] = len(context["current_exact"])

    for row in citations:
        key = citation_key(row)
        if key in legacy_citation_keys:
            decision = citation_decisions_by_old_key.get(key)
            reason = (
                f"citation_claim_by_claim_rewire:{decision.decision_id}"
                if decision is not None
                else _quarantine_reason_for_legacy(str(row.get("kg_node_id") or ""))
            )
            quarantine.append(
                quarantine_record(
                    "corpus_citation_before",
                    row,
                    reason,
                )
            )
    citations_out = [
        row for row in citations_out if citation_key(row) not in legacy_citation_keys
    ]
    changes["legacy_snapshot_citations_retired"] = len(
        legacy_snapshot_citation_keys
    )
    changes["legacy_non_snapshot_citations_rewired"] = len(
        legacy_related_citation_keys
    )

    for row in edges:
        identifier = edge_id(row)
        if identifier in legacy_incident_edge_ids:
            legacy_name = (
                edge_source(row) if edge_source(row) in legacy_ids else edge_target(row)
            )
            quarantine.append(
                quarantine_record(
                    "kg_edge_before", row, _quarantine_reason_for_legacy(legacy_name)
                )
            )
        elif identifier in old_claim_edge_ids:
            decision = next(
                item for item in REWIRE_DECISIONS if item.old_edge_id == identifier
            )
            quarantine.append(
                quarantine_record(
                    "kg_edge_before",
                    row,
                    f"claim_by_claim_rewire:{decision.decision_id}",
                )
            )
    edges_out = [
        row
        for row in edges_out
        if edge_id(row) not in legacy_incident_edge_ids
        and edge_id(row) not in old_claim_edge_ids
    ]
    changes["legacy_incident_edges_retired"] = len(legacy_incident_edge_ids)
    # Four old rewire edges are already part of the legacy incident set.
    changes["broad_work_claim_edges_retired"] = len(
        old_claim_edge_ids - legacy_incident_edge_ids
    )

    by_node_out = {node_id(row): row for row in nodes_out}
    for spec in WORKS.values():
        current = by_node_out[spec.work_node]
        wanted = _enrich_work_node(current, spec)
        if current != wanted:
            quarantine.append(
                quarantine_record(
                    "kg_node_before", current, "enrich_work_with_complete_exact_ogl_cohort"
                )
            )
            current.clear()
            current.update(wanted)
            changes["work_nodes_enriched"] += 1

    argument = by_node_out[ARGUMENT_NODE]
    wanted_argument = _rewire_argument_node(argument, authority)
    if argument != wanted_argument:
        quarantine.append(
            quarantine_record(
                "kg_node_before", argument, "claim_primary_sources_rewired_to_exact_sections"
            )
        )
        argument.clear()
        argument.update(wanted_argument)
        changes["argument_claim_nodes_rewired"] += 1

    exact_nodes = [make_node(section) for section in authority.sections]
    exact_passages = [make_passage(section) for section in authority.sections]
    exact_citations = [make_snapshot_citation(section) for section in authority.sections]
    rewired_citations = [
        make_rewired_citation(decision, authority)
        for decision in CITATION_REWIRE_DECISIONS
    ]
    citation_rewire_rows = [
        {
            "decision_id": decision.decision_id,
            "old_passage_id": decision.old_passage_id,
            "new_passage_id": make_rewired_citation(decision, authority)["passage_id"],
            "target_cts_urn": _expected_section(
                authority, decision.target_locus
            ).cts_urn,
            "kg_node_id": decision.kg_node_id,
            "citation_type": decision.citation_type,
            "confidence": decision.confidence,
            "rationale": decision.rationale,
        }
        for decision in CITATION_REWIRE_DECISIONS
    ]
    exact_edges: list[dict[str, Any]] = []
    for section in authority.sections:
        exact_edges.append(make_edge(section.node_id, "authored_by", PERSON_NODE))
        exact_edges.append(make_edge(section.node_id, "part_of", section.work.work_node))
    semantic_edges, rewire_rows = _replacement_edges(authority)

    existing_edge_ids = {edge_id(row) for row in edges_out}
    additions = exact_edges + semantic_edges
    collision = existing_edge_ids & {edge_id(row) for row in additions}
    if collision:
        raise RuntimeError(f"new Sextus edge-id collision: {sorted(collision)[:3]}")
    nodes_out.extend(exact_nodes)
    passages_out.extend(exact_passages)
    citations_out.extend(exact_citations)
    citations_out.extend(rewired_citations)
    edges_out.extend(additions)
    changes["exact_nodes_added"] = len(exact_nodes)
    changes["exact_passages_added"] = len(exact_passages)
    changes["exact_snapshot_citations_added"] = len(exact_citations)
    changes["exact_non_snapshot_citations_added"] = len(rewired_citations)
    changes["exact_structural_edges_added"] = len(exact_edges)
    changes["semantic_edges_added"] = len(semantic_edges)

    manifests = {
        spec.key: [
            row for row in manifest_out if row.get("canonical_id") == spec.canonical_id
        ]
        for spec in WORKS.values()
    }
    for spec in WORKS.values():
        rows = manifests[spec.key]
        if len(rows) != 1:
            raise RuntimeError(
                f"expected one {spec.key} corpus manifest row, found {len(rows)}"
            )
        current = rows[0]
        wanted = _manifest_row(current, spec)
        if current != wanted:
            quarantine.append(
                quarantine_record(
                    "corpus_manifest_before", current, "replace_mixed_or_partial_manifest"
                )
            )
            current.clear()
            current.update(wanted)
            changes["manifest_rows_rebuilt"] += 1

    changes["quarantine_records"] = len(quarantine)
    plan = _plan(
        changes,
        len(quarantine),
        rewire_rows,
        citation_rewire_rows,
    )
    validate_zero_debt(
        nodes_out,
        edges_out,
        passages_out,
        citations_out,
        manifest_out,
        authority,
    )
    return MigrationResult(
        nodes=nodes_out,
        edges=edges_out,
        passages=passages_out,
        citations=citations_out,
        manifest=manifest_out,
        quarantine=quarantine,
        changes=changes,
        plan=plan,
    )


def validate_zero_debt(
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    passages: list[dict[str, Any]],
    citations: list[dict[str, Any]],
    manifest: list[dict[str, Any]],
    authority: AuthoritySnapshot,
) -> dict[str, int]:
    by_node = {node_id(row): row for row in nodes}
    by_passage = {str(row.get("passage_id") or ""): row for row in passages}
    if len(by_node) != len(nodes) or len(by_passage) != len(passages):
        raise RuntimeError("duplicate node or passage IDs after Sextus migration")
    citation_keys = [citation_key(row) for row in citations]
    if len(citation_keys) != len(set(citation_keys)):
        raise RuntimeError("duplicate corpus citation triplets after Sextus migration")
    dangling_passages = [
        citation_key(row)
        for row in citations
        if str(row.get("passage_id") or "") not in by_passage
    ]
    dangling_nodes = [
        citation_key(row)
        for row in citations
        if str(row.get("kg_node_id") or "") not in by_node
    ]
    if dangling_passages or dangling_nodes:
        raise RuntimeError(
            "global corpus citation dangling references remain: "
            f"passages={len(dangling_passages)} nodes={len(dangling_nodes)}"
        )
    if any(
        (number := _legacy_number(name)) is not None and 1 <= number <= EXPECTED_LEGACY_TOTAL
        for name in by_node
    ):
        raise RuntimeError("active legacy Sextus nodes remain")

    expected_nodes = {section.node_id for section in authority.sections}
    expected_passages = {section.passage_id for section in authority.sections}
    if not expected_nodes.issubset(by_node) or not expected_passages.issubset(by_passage):
        raise RuntimeError("complete exact Sextus cohort is absent")
    exact_rows = [row for row in passages if _is_current_exact_row(row)]
    if len(exact_rows) != EXPECTED_EXACT_TOTAL:
        raise RuntimeError(f"exact Sextus passage count is {len(exact_rows)}")
    if {str(row.get("passage_id") or "") for row in exact_rows} != expected_passages:
        raise RuntimeError("non-deterministic or duplicate Sextus exact passage IDs remain")

    for section in authority.sections:
        node = by_node[section.node_id]
        row = by_passage[section.passage_id]
        data = metadata(node)
        if normalize_text(str(node.get("description") or "")) != section.text:
            raise RuntimeError(f"KG exact text mismatch at {section.cts_urn}")
        if normalize_text(str(row.get("text_content") or "")) != section.text:
            raise RuntimeError(f"corpus exact text mismatch at {section.cts_urn}")
        if (
            data.get("cts_urn") != section.cts_urn
            or data.get("work_canonical_id") != section.work.work_urn
            or data.get("db_passage_id") != section.passage_id
            or row.get("cts_urn") != section.cts_urn
            or row.get("work_canonical_id") != section.work.canonical_id
            or sha256_text(section.text) != section.text_sha256_nfc
        ):
            raise RuntimeError(f"exact identity mismatch at {section.cts_urn}")
        if ":Pr." in section.cts_urn:
            raise RuntimeError("pseudo-Pr CTS survived exact construction")

    snapshots = {
        (str(row.get("kg_node_id") or ""), str(row.get("passage_id") or ""))
        for row in citations
        if row.get("citation_type") == "snapshot_passage_node"
        and (
            str(row.get("kg_node_id") or "") in expected_nodes
            or str(row.get("passage_id") or "") in expected_passages
        )
    }
    wanted_snapshots = {(section.node_id, section.passage_id) for section in authority.sections}
    if snapshots != wanted_snapshots:
        raise RuntimeError("exact Sextus snapshot mapping is not bijective")

    expected_related = {
        citation_key(make_rewired_citation(decision, authority)): (
            make_rewired_citation(decision, authority),
            decision,
        )
        for decision in CITATION_REWIRE_DECISIONS
    }
    citations_by_key = {citation_key(row): row for row in citations}
    for decision in CITATION_REWIRE_DECISIONS:
        old_key = citation_key(
            {
                "kg_node_id": decision.kg_node_id,
                "passage_id": decision.old_passage_id,
                "citation_type": decision.citation_type,
            }
        )
        if old_key in citations_by_key:
            raise RuntimeError(
                f"legacy non-snapshot Sextus citation remains: {decision.decision_id}"
            )
    for key, (wanted, decision) in expected_related.items():
        actual = citations_by_key.get(key)
        if actual != wanted:
            raise RuntimeError(
                f"exact non-snapshot Sextus citation mismatch: {decision.decision_id}"
            )

    part_of = {
        (edge_source(row), edge_target(row))
        for row in edges
        if row.get("relation") == "part_of" and edge_source(row) in expected_nodes
    }
    authored = {
        (edge_source(row), edge_target(row))
        for row in edges
        if row.get("relation") == "authored_by" and edge_source(row) in expected_nodes
    }
    if part_of != {
        (section.node_id, section.work.work_node) for section in authority.sections
    }:
        raise RuntimeError("exact Sextus work-child edges are incomplete")
    if authored != {(section.node_id, PERSON_NODE) for section in authority.sections}:
        raise RuntimeError("exact Sextus authorship edges are incomplete")

    old_rewire_ids = {decision.old_edge_id for decision in REWIRE_DECISIONS}
    if old_rewire_ids & {edge_id(row) for row in edges}:
        raise RuntimeError("broad or legacy Sextus claim edges remain")
    semantic_edges, _rewire_rows = _replacement_edges(authority)
    if not {edge_id(row) for row in semantic_edges}.issubset(
        {edge_id(row) for row in edges}
    ):
        raise RuntimeError("claim-by-claim Sextus rewires are incomplete")

    argument_data = metadata(by_node[ARGUMENT_NODE])
    serialized_argument = json.dumps(argument_data, ensure_ascii=False)
    for premise in argument_data.get("premises", []):
        if PH_WORK_NODE in premise.get("primary_sources", []):
            raise RuntimeError("equipollence premise retains broad work-level sourcing")
    if argument_data.get("conclusion", {}).get("primary_sources"):
        raise RuntimeError("reconstructed equipollence conclusion is marked direct")
    if "reconstructed_application" not in serialized_argument:
        raise RuntimeError("fate-specific equipollence reconstruction is not explicit")

    manifest_counts: dict[str, int] = {}
    for spec in WORKS.values():
        rows = [row for row in manifest if row.get("canonical_id") == spec.canonical_id]
        if len(rows) != 1:
            raise RuntimeError(f"{spec.key} exact manifest is not unique")
        row = rows[0]
        if (
            row.get("cts_urn") != spec.edition_urn
            or row.get("passages") != EXPECTED_SECTION_COUNTS[spec.key]
            or row.get("zero_debt_cohort", {}).get("legacy_active_count") != 0
        ):
            raise RuntimeError(f"{spec.key} manifest is not zero-debt complete")
        manifest_counts[spec.key] = int(row["passages"])

    for spec in WORKS.values():
        data = metadata(by_node[spec.work_node])
        if (
            data.get("canonical_id") != spec.work_urn
            or data.get("edition_urn") != spec.edition_urn
            or data.get(STAMP, {}).get("complete_exact_section_count")
            != EXPECTED_SECTION_COUNTS[spec.key]
        ):
            raise RuntimeError(f"{spec.key} work node lacks exact cohort provenance")
    return {
        "am_sections": manifest_counts["am"],
        "authored_by_edges": len(authored),
        "exact_nodes": len(expected_nodes),
        "exact_non_snapshot_citations": len(expected_related),
        "exact_passages": len(exact_rows),
        "part_of_edges": len(part_of),
        "ph_sections": manifest_counts["ph"],
        "semantic_rewire_edges": len(semantic_edges),
        "snapshot_citations": len(snapshots),
    }


def _jsonl_content_preserving(
    original: bytes,
    rows: list[dict[str, Any]],
    key: Callable[[dict[str, Any]], str],
    label: str,
) -> str:
    desired = {key(row): row for row in rows}
    if len(desired) != len(rows):
        raise RuntimeError(f"duplicate desired keys for {label}")
    output: list[str] = []
    seen: set[str] = set()
    for line in original.decode("utf-8").splitlines():
        if not line.strip():
            continue
        old = json.loads(line)
        identifier = key(old)
        replacement = desired.get(identifier)
        if replacement is None:
            continue
        seen.add(identifier)
        output.append(
            line
            if old == replacement
            else json.dumps(replacement, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        )
    for row in rows:
        identifier = key(row)
        if identifier not in seen:
            output.append(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return "\n".join(output) + "\n"


def _fsync_directory(directory: Path) -> None:
    descriptor = os.open(directory, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _stage_bytes(target: Path, content: bytes) -> Path:
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "wb",
        dir=target.parent,
        prefix=".sextus-stage-",
        delete=False,
    ) as handle:
        temporary = Path(handle.name)
        handle.write(content)
        handle.flush()
        os.fsync(handle.fileno())
    return temporary


def _replace_staged_file(staged: Path, target: Path) -> None:
    os.replace(staged, target)
    _fsync_directory(target.parent)


def _restore_bytes(target: Path, content: bytes) -> None:
    staged = _stage_bytes(target, content)
    _replace_staged_file(staged, target)


def write_result(
    data_root: Path,
    result: MigrationResult,
    expected_originals: dict[str, bytes],
) -> None:
    paths = {
        "nodes": data_root / "kg/nodes.jsonl",
        "edges": data_root / "kg/edges.jsonl",
        "passages": data_root / "corpus/passages.jsonl",
        "citations": data_root / "corpus/citations.jsonl",
        "manifest": data_root / "corpus/manifest.jsonl",
    }
    if set(expected_originals) != set(paths):
        raise RuntimeError("Sextus write lacks the complete parsed snapshot A")
    contents = {
        "nodes": _jsonl_content_preserving(
            expected_originals["nodes"], result.nodes, node_id, "nodes"
        ),
        "edges": _jsonl_content_preserving(
            expected_originals["edges"], result.edges, edge_id, "edges"
        ),
        "passages": _jsonl_content_preserving(
            expected_originals["passages"],
            result.passages,
            lambda row: str(row.get("passage_id") or ""),
            "passages",
        ),
        "citations": _jsonl_content_preserving(
            expected_originals["citations"],
            result.citations,
            citation_key,
            "citations",
        ),
        "manifest": _jsonl_content_preserving(
            expected_originals["manifest"],
            result.manifest,
            lambda row: str(row.get("canonical_id") or ""),
            "manifest",
        ),
    }
    quarantine_path = data_root / QUARANTINE_RELATIVE
    plan_path = data_root / PLAN_RELATIVE
    if quarantine_path.exists() or plan_path.exists():
        raise RuntimeError("Sextus output artifact already exists before first write")
    quarantine_content = "\n".join(
        json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        for row in result.quarantine
    ) + "\n"
    plan_content = json.dumps(result.plan, ensure_ascii=False, indent=2, sort_keys=True) + "\n"

    target_payloads: list[tuple[str, Path, bytes, bytes | None]] = [
        (
            "quarantine",
            quarantine_path,
            quarantine_content.encode("utf-8"),
            None,
        ),
        ("plan", plan_path, plan_content.encode("utf-8"), None),
        *[
            (name, path, contents[name].encode("utf-8"), expected_originals[name])
            for name, path in paths.items()
        ],
    ]
    staged = {
        name: _stage_bytes(path, payload)
        for name, path, payload, _original in target_payloads
    }
    lock_path = data_root / "audit/.sextus-exact-cohort.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    replaced: list[tuple[str, Path, bytes | None]] = []
    try:
        with lock_path.open("a+b") as lock_handle:
            fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX)
            for _name, path, _payload, original in target_payloads:
                if original is None:
                    if path.exists():
                        raise RuntimeError(
                            f"Sextus output artifact appeared concurrently: {path}"
                        )
                elif path.read_bytes() != original:
                    raise RuntimeError(
                        f"concurrent write detected since parsed Sextus snapshot A: {path}"
                    )

            for name, path, _payload, original in target_payloads:
                # Compare immediately before every replace, not merely once at
                # the beginning of a multi-file commit.
                if original is None:
                    if path.exists():
                        raise RuntimeError(
                            f"Sextus output artifact appeared before replace: {path}"
                        )
                elif path.read_bytes() != original:
                    raise RuntimeError(
                        f"concurrent write detected immediately before replace: {path}"
                    )
                _replace_staged_file(staged[name], path)
                replaced.append((name, path, original))
    except Exception:
        for _name, path, original in reversed(replaced):
            if original is None:
                path.unlink(missing_ok=True)
                _fsync_directory(path.parent)
            else:
                _restore_bytes(path, original)
        raise
    finally:
        for temporary in staged.values():
            temporary.unlink(missing_ok=True)
        lock_path.unlink(missing_ok=True)
        _fsync_directory(lock_path.parent)


def load_data(data_root: Path) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
]:
    return load_data_snapshot(data_root).rows


def _rows_from_bytes(raw: bytes) -> list[dict[str, Any]]:
    return [json.loads(line) for line in raw.decode("utf-8").splitlines() if line.strip()]


def load_data_snapshot(data_root: Path) -> DataSnapshot:
    paths = {
        "nodes": data_root / "kg/nodes.jsonl",
        "edges": data_root / "kg/edges.jsonl",
        "passages": data_root / "corpus/passages.jsonl",
        "citations": data_root / "corpus/citations.jsonl",
        "manifest": data_root / "corpus/manifest.jsonl",
    }
    first = {name: path.read_bytes() for name, path in paths.items()}
    # A second read detects a writer that crossed the five-file snapshot read.
    # Those exact first bytes, rather than a later re-read, travel to commit.
    second = {name: path.read_bytes() for name, path in paths.items()}
    if first != second:
        raise RuntimeError("concurrent write detected while loading Sextus snapshot A")
    return DataSnapshot(
        nodes=_rows_from_bytes(first["nodes"]),
        edges=_rows_from_bytes(first["edges"]),
        passages=_rows_from_bytes(first["passages"]),
        citations=_rows_from_bytes(first["citations"]),
        manifest=_rows_from_bytes(first["manifest"]),
        original_bytes=first,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--data-root", type=Path, default=DEFAULT_DATA_ROOT)
    parser.add_argument("--authority-dir", type=Path)
    parser.add_argument(
        "--production-write-approved",
        action="store_true",
        help="Second production-only lock; use only after the concurrent Irenaeus migration finishes.",
    )
    args = parser.parse_args(argv)
    data_root = args.data_root.expanduser().resolve()
    production_root = DEFAULT_DATA_ROOT.resolve()
    if args.write and data_root == production_root and not args.production_write_approved:
        parser.error(
            "production Sextus write is locked until Irenaeus finishes; rerun dry-run now and use "
            "--production-write-approved only after explicit coordination approval"
        )

    authority = load_authority(args.authority_dir)
    snapshot = load_data_snapshot(data_root)
    result = transform(*snapshot.rows, authority)
    validation = validate_zero_debt(
        result.nodes,
        result.edges,
        result.passages,
        result.citations,
        result.manifest,
        authority,
    )
    print("Sextus PH/AM exact-cohort repair")
    print("mode:", "WRITE" if args.write else "DRY-RUN")
    print("authority commit:", OGL_COMMIT)
    print("source sections: PH=781 AM=2732 total=3513")
    print("changes:", json.dumps(dict(sorted(result.changes.items())), sort_keys=True))
    print("validated:", json.dumps(validation, sort_keys=True))
    print("claim rewires:", len(result.plan.get("rewire_decisions", [])))
    print("quarantine records:", len(result.quarantine))
    if not args.write:
        print("dry-run: nothing written")
        return 0
    if not result.changes:
        print("already applied: no files written")
        return 0
    write_result(data_root, result, snapshot.original_bytes)
    print("written copied data root:", data_root)
    print("registry: untouched")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
