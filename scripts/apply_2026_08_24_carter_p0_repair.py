#!/usr/bin/env python3
"""Repair Carter's bibliographic identity, pagination semantics and KG wiring.

The local 56-page PDF is an author manuscript, not the typeset pages 49--88
of the published chapter.  This migration records both manifestations without
inventing a page concordance, corrects the one substantive FTN/FFN error,
removes the unsupported licence claim, and links all eight Carter arguments to
their publication.  It is dry-run by default and idempotent.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import tempfile
import uuid
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_ROOT = ROOT / "data"
STAMP = "carter_p0_repair_2026_08_24"
NOW = "2026-08-24 01:30:00+00:00"
NOW_ISO = "2026-08-24T01:30:00Z"

PUB_ID = "pub_carter_2024_fatalism_de_int_9"
SCHOLAR_ID = "scholar_carter_jason"
SOURCE_ID = "src_sec_carter_fatalism_de_int_9"
EVIDENCE_ID = "ev_sec_carter_de_int9_pp1_56"
IDENTITY_ISSUE_ID = "issue_carter_year_identity_conflict"
PAGE_ISSUE_ID = "issue_carter_author_ms_published_page_concordance"
WRONG_STANCE_EDGE_ID = "e29f76b8-29ac-485f-bacb-0dc13d46bdf0"

PDF_RELATIVE = "data/literature_acquisition/carter_2022_fatalism.pdf"
PDF_SHA256 = "609759c583384fb1d8c02845400be65e58374c3829cc82c6cb10460511ec716c"
AUTHORITY_URL = (
    "https://research-portal.st-andrews.ac.uk/en/publications/"
    "fatalism-and-false-futures-in-ide-interpretationei-9/"
)
DOI = "10.1093/oso/9780192885197.003.0002"

ARGUMENT_PAGES = {
    "argument_carter_2024_both_false_interpretation": "7",
    "argument_carter_2024_cost_contraries_not_contradictories": "49",
    "argument_carter_2024_first_fatalist_argument": "11-12",
    "argument_carter_2024_future_truth_necessity_gc": "31-32",
    "argument_carter_2024_objections_are_fatalist": "23",
    "argument_carter_2024_pb_lem_rcp_distinction": "2",
    "argument_carter_2024_post_an_212_retro_truth_denied": "47",
    "argument_carter_2024_second_fatalist_argument": "20",
}
ARGUMENT_SUPPORT_PAGES = {
    "argument_carter_2024_objections_are_fatalist": "23-36",
    "argument_carter_2024_pb_lem_rcp_distinction": "2; 24",
}
ARGUMENT_IDS = tuple(ARGUMENT_PAGES)
OBJECTIONS_ID = "argument_carter_2024_objections_are_fatalist"
PB_RCP_ID = "argument_carter_2024_pb_lem_rcp_distinction"

BIBTEX_KEY = "publication-2024-carter-fatalism-and-false-futures-in-de-interpretatione-9"
BIBTEX_ENTRY = """@incollection{publication-2024-carter-fatalism-and-false-futures-in-de-interpretatione-9,
  author = {Jason W. Carter},
  title = {Fatalism and False Futures in De Interpretatione 9},
  year = {2024},
  date = {2024-06-06},
  booktitle = {Oxford Studies in Ancient Philosophy},
  editor = {Rachana Kamtekar},
  publisher = {Oxford University Press},
  address = {Oxford},
  chapter = {2},
  pages = {49--88},
  volume = {63},
  number = {Winter 2022},
  doi = {10.1093/oso/9780192885197.003.0002},
  isbn = {9780192885197},
  url = {https://doi.org/10.1093/oso/9780192885197.003.0002},
  note = {Volume label Winter 2022; published 6 June 2024. EleutherIA KG node: pub_carter_2024_fatalism_de_int_9}
}
"""


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def node_id(node: dict[str, Any]) -> str:
    return str(node.get("id") or node.get("node_id") or "")


def record_id(record: dict[str, Any]) -> str:
    for key in (
        "evidence_id",
        "issue_id",
        "verification_id",
        "wave_id",
        "source_id",
    ):
        if record.get(key):
            return str(record[key])
    return ""


def metadata(obj: dict[str, Any]) -> dict[str, Any]:
    value = obj.get("metadata")
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            return {}
    return copy.deepcopy(value) if isinstance(value, dict) else {}


def set_metadata(obj: dict[str, Any], value: dict[str, Any]) -> None:
    if isinstance(obj.get("metadata"), str):
        obj["metadata"] = json.dumps(value, ensure_ascii=False, sort_keys=True)
    else:
        obj["metadata"] = value


def edge_id(source: str, relation: str, target: str) -> str:
    return str(
        uuid.uuid5(
            uuid.NAMESPACE_URL,
            f"https://eleutheria.example/kg/edge/{source}/{relation}/{target}",
        )
    )


def make_advanced_in(argument: str) -> dict[str, Any]:
    return {
        "confidence": 1.0,
        "created_at": NOW,
        "edge_id": edge_id(argument, "advanced_in", PUB_ID),
        "metadata": {
            STAMP: True,
            "auto_generated": False,
            "note": (
                "The argument is sourced to Carter's published OSAP chapter; "
                "claim-level locators remain author-manuscript pages until a "
                "published-page concordance is established."
            ),
            "published_page_map_status": "unmapped",
        },
        "relation": "advanced_in",
        "source": argument,
        "source_id": argument,
        "target": PUB_ID,
        "target_id": PUB_ID,
        "weight": 1.0,
    }


def desired_publication_metadata(old: dict[str, Any]) -> dict[str, Any]:
    value = copy.deepcopy(old)
    for key in (
        "journal",
        "license",
        "local_pdf_path",
        "publication_status",
        "season",
        "year_verification_note",
        "year_verified",
    ):
        value.pop(key, None)
    value.update(
        {
            STAMP: True,
            "author": "Jason W. Carter",
            "author_id": SCHOLAR_ID,
            "bibtex_key": BIBTEX_KEY,
            "book_title": "Oxford Studies in Ancient Philosophy",
            "chapter": "2",
            "citation_verdict": "corrected",
            "citation_verified": True,
            "container_title": "Oxford Studies in Ancient Philosophy",
            "doi": DOI,
            "editor": "Rachana Kamtekar",
            "isbn": "9780192885197",
            "item_type": "book_chapter",
            "language": "eng",
            "license_status": "no_explicit_reuse_license_found",
            "local_author_manuscript": {
                "created_at_pdf_metadata": "2024-01-24T11:20:56+01:00",
                "physical_pages": "1-56",
                "relative_path": PDF_RELATIVE,
                "sha256": PDF_SHA256,
            },
            "nominal_volume_label": "Winter 2022",
            "nominal_volume_year": 2022,
            "number": "Winter 2022",
            "page_correspondence": {
                "author_ms_pages": "1-56",
                "published_pages": "49-88",
                "status": "unmapped",
            },
            "pages": "49-88",
            "publication_date": "2024-06-06",
            "publication_year": 2024,
            "published_at": "2024-06-06",
            "published_page_range": "49-88",
            "publisher": "Oxford University Press",
            "publisher_location": "Oxford",
            "source_url": AUTHORITY_URL,
            "title": "Fatalism and False Futures in De Interpretatione 9",
            "type": "book_chapter",
            "verified_reference": (
                "Jason W. Carter, 'Fatalism and False Futures in De "
                "Interpretatione 9', in Rachana Kamtekar (ed.), Oxford "
                "Studies in Ancient Philosophy 63 (nominal volume label "
                "Winter 2022; published 6 June 2024), 49-88, DOI " + DOI + "."
            ),
            "verification_sources": [
                PDF_RELATIVE,
                AUTHORITY_URL,
                f"https://doi.org/{DOI}",
            ],
            "volume": "63",
            "year": 2024,
        }
    )
    return value


def desired_argument_metadata(
    argument_id: str, old: dict[str, Any]
) -> dict[str, Any]:
    value = copy.deepcopy(old)
    page = ARGUMENT_PAGES[argument_id]
    for key in ("page_or_loc", "page_range", "published_page", "published_pages"):
        value.pop(key, None)
    evidence = copy.deepcopy(value.get("verbatim_evidence") or {})
    old_page = evidence.pop("page", None)
    if old_page is not None and str(old_page) != page:
        raise RuntimeError(
            f"unexpected Carter author-ms page for {argument_id}: {old_page!r}"
        )
    evidence.update(
        {
            "author_ms_page": page,
            "published_page": None,
            "published_page_map_status": "unmapped",
        }
    )
    value.update(
        {
            STAMP: True,
            "author_ms_page": page,
            "citation_verdict": "corrected",
            "citation_verified": True,
            "content_verification_basis": "local_author_manuscript",
            "published_container_pages": "49-88",
            "published_page": None,
            "published_page_map_status": "unmapped",
            "scholarly_work_id": PUB_ID,
            "source_artifact_sha256": PDF_SHA256,
            "source_manifestation": "author_manuscript",
            "verification_status": (
                "content_checked_in_author_manuscript; "
                "claim-level published page unmapped"
            ),
            "verbatim_evidence": evidence,
            "verified_reference": (
                "Jason W. Carter, author manuscript, p. "
                f"{page} ({PDF_RELATIVE}, SHA-256 {PDF_SHA256}); published as "
                "'Fatalism and False Futures in De Interpretatione 9', "
                "Oxford Studies in Ancient Philosophy 63 (published 6 June "
                f"2024), 49-88, DOI {DOI}. The corresponding published page "
                "for this claim has not been established."
            ),
        }
    )
    support_pages = ARGUMENT_SUPPORT_PAGES.get(argument_id)
    if support_pages:
        value["author_ms_support_pages"] = support_pages
    if argument_id == OBJECTIONS_ID:
        value["semantic_correction"] = {
            "accepted": [
                "Future Truth Necessity for modally unqualified future singulars"
            ],
            "rejected_or_restricted": [
                "Future Falsity Necessity as a universal inference",
                "Rule of Contradictory Pairs for presently future contingent pairs",
            ],
            "note": (
                "Carter treats the two objections as fatalist arguments. Their "
                "unsoundness must not be stated as a rejection of FTN: he "
                "explicitly accepts FTN later in the author manuscript."
            ),
        }
    return value


OBJECTIONS_DESCRIPTION = (
    "Carter argues that the two objections to the both-false interpretation "
    "at De Interpretatione 9, 18b17-25 are additional fatalist arguments, not "
    "Aristotle speaking in propria persona. The first assumes the Rule of "
    "Contradictory Pairs (RCP), which is precisely the contested fatalist "
    "assumption. The second combines Future Truth Necessity (FTN) with Future "
    "Falsity Necessity (FFN). Carter later explicitly accepts FTN for modally "
    "unqualified future singular statements, but rejects the unrestricted FFN "
    "move from a statement's falsity to the opposite event's necessity. Future "
    "contingent contradictory pairs are temporary exceptions to RCP: both can "
    "be false because one expresses present necessity and the other present "
    "impossibility. The objection is therefore unsound through FFN/RCP, not "
    "through FTN."
)


def transform_graph(
    nodes: list[dict[str, Any]], edges: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], Counter[str]]:
    nodes = copy.deepcopy(nodes)
    edges = copy.deepcopy(edges)
    quarantine: list[dict[str, Any]] = []
    counts: Counter[str] = Counter()
    by_node = {node_id(node): node for node in nodes}
    required = {PUB_ID, SCHOLAR_ID, *ARGUMENT_IDS}
    missing = sorted(required - by_node.keys())
    if missing:
        raise RuntimeError(f"required Carter KG nodes missing: {missing}")

    publication = by_node[PUB_ID]
    wanted_pub_md = desired_publication_metadata(metadata(publication))
    wanted_pub = copy.deepcopy(publication)
    wanted_pub["description"] = (
        "Jason W. Carter's chapter offers a both-false interpretation of "
        "Aristotle's response to logical fatalism in De Interpretatione 9. It "
        "appears in Oxford Studies in Ancient Philosophy 63, whose nominal "
        "series label is Winter 2022, and was published by Oxford University "
        "Press on 6 June 2024 at pages 49-88. The local 56-page PDF is a "
        "distinct author manuscript; no claim-level concordance to the "
        "published pagination is asserted."
    )
    wanted_pub["label"] = "Fatalism and False Futures in De Interpretatione 9"
    wanted_pub["updated_at"] = NOW
    set_metadata(wanted_pub, wanted_pub_md)
    if publication != wanted_pub:
        quarantine.append({"record_type": "kg_node_before", "record": publication})
        publication.clear()
        publication.update(wanted_pub)
        counts["publication_corrected"] += 1

    for argument_id in ARGUMENT_IDS:
        argument = by_node[argument_id]
        wanted = copy.deepcopy(argument)
        if argument_id == OBJECTIONS_ID:
            wanted["description"] = OBJECTIONS_DESCRIPTION
        elif argument_id == "argument_carter_2024_both_false_interpretation":
            wanted["description"] = str(wanted.get("description") or "").replace(
                "Verbatim (p. 7)", "Verbatim (author manuscript p. 7)"
            )
        wanted["updated_at"] = NOW
        set_metadata(wanted, desired_argument_metadata(argument_id, metadata(argument)))
        if argument != wanted:
            quarantine.append({"record_type": "kg_node_before", "record": argument})
            argument.clear()
            argument.update(wanted)
            counts["argument_corrected"] += 1

    stance = [edge for edge in edges if edge.get("edge_id") == WRONG_STANCE_EDGE_ID]
    if len(stance) != 1:
        raise RuntimeError(
            f"expected one Carter stance edge {WRONG_STANCE_EDGE_ID}, got {len(stance)}"
        )
    stance_edge = stance[0]
    if stance_edge.get("relation") == "argues_for":
        quarantine.append({"record_type": "kg_edge_before", "record": stance_edge})
        stance_edge["relation"] = "argues_against"
        stance_edge["metadata"] = {
            **(stance_edge.get("metadata") or {}),
            STAMP: True,
            "correction": (
                "Carter attributes these objections to the fatalist and rejects "
                "their FFN/RCP inference; he does not endorse fatalism."
            ),
            "previous_relation": "argues_for",
        }
        counts["stance_edge_corrected"] += 1
    elif stance_edge.get("relation") != "argues_against":
        raise RuntimeError(
            f"unexpected Carter stance relation: {stance_edge.get('relation')!r}"
        )

    triples = {
        (str(edge.get("source")), str(edge.get("relation")), str(edge.get("target")))
        for edge in edges
    }
    for argument_id in ARGUMENT_IDS:
        triple = (argument_id, "advanced_in", PUB_ID)
        if triple not in triples:
            edges.append(make_advanced_in(argument_id))
            triples.add(triple)
            counts["advanced_in_added"] += 1

    validate_graph(nodes, edges)
    return nodes, edges, quarantine, counts


def validate_graph(nodes: list[dict[str, Any]], edges: list[dict[str, Any]]) -> None:
    by_node = {node_id(node): node for node in nodes}
    if len(by_node) != len(nodes):
        raise RuntimeError("duplicate KG node ids after Carter repair")
    publication = by_node[PUB_ID]
    pub_md = metadata(publication)
    assert pub_md["nominal_volume_year"] == 2022
    assert pub_md["publication_date"] == "2024-06-06"
    assert pub_md["pages"] == "49-88"
    assert pub_md["doi"] == DOI
    assert pub_md["page_correspondence"]["status"] == "unmapped"
    assert "license" not in pub_md
    assert "phronesis" not in str(publication).lower()

    triples = Counter(
        (
            str(edge.get("source")),
            str(edge.get("relation")),
            str(edge.get("target")),
        )
        for edge in edges
    )
    duplicates = [triple for triple, count in triples.items() if count > 1]
    if duplicates:
        raise RuntimeError(f"duplicate edge triples after Carter repair: {duplicates[:5]}")
    for argument_id, page in ARGUMENT_PAGES.items():
        md = metadata(by_node[argument_id])
        assert md["author_ms_page"] == page
        assert md["published_page"] is None
        assert md["published_page_map_status"] == "unmapped"
        assert md["verbatim_evidence"]["author_ms_page"] == page
        assert "page" not in md["verbatim_evidence"]
        assert md["scholarly_work_id"] == PUB_ID
        assert triples[(argument_id, "advanced_in", PUB_ID)] == 1
        assert "phronesis" not in str(by_node[argument_id]).lower()
    objections = metadata(by_node[OBJECTIONS_ID])["semantic_correction"]
    assert "Future Truth Necessity for modally unqualified future singulars" in objections[
        "accepted"
    ]
    stance = [edge for edge in edges if edge.get("edge_id") == WRONG_STANCE_EDGE_ID]
    assert len(stance) == 1 and stance[0]["relation"] == "argues_against"
    for edge in edges:
        if edge.get("source") not in by_node or edge.get("target") not in by_node:
            raise RuntimeError(f"dangling KG edge after Carter repair: {edge.get('edge_id')}")


def replace_bibtex_entry(text: str) -> tuple[str, str | None]:
    pattern = re.compile(
        rf"(?ms)^@\w+\{{{re.escape(BIBTEX_KEY)},\n.*?^\}}\n"
    )
    matches = list(pattern.finditer(text))
    if len(matches) != 1:
        raise RuntimeError(f"expected one Carter BibTeX entry, got {len(matches)}")
    old = matches[0].group(0)
    if old == BIBTEX_ENTRY:
        return text, None
    return text[: matches[0].start()] + BIBTEX_ENTRY + text[matches[0].end() :], old


def replace_record(
    records: list[dict[str, Any]], wanted_id: str, transform: Any
) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
    records = copy.deepcopy(records)
    matches = [record for record in records if record_id(record) == wanted_id]
    if len(matches) != 1:
        raise RuntimeError(f"expected one registry record {wanted_id}, got {len(matches)}")
    old = matches[0]
    new = transform(copy.deepcopy(old))
    if new == old:
        return records, None
    index = records.index(old)
    records[index] = new
    return records, old


def transform_source(record: dict[str, Any]) -> dict[str, Any]:
    record.update(
        {
            "creators": ["Jason W. Carter"],
            "date_display": "Volume 63 labelled Winter 2022; published 2024-06-06",
            "identity_status": "bibliography_verified",
            "canonical_identifiers": {
                "doi": DOI,
                "kg_publication_id": PUB_ID,
                "nominal_volume_label": "Winter 2022",
                "published_at": "2024-06-06",
                "published_pages": "49-88",
                "venue": "Oxford Studies in Ancient Philosophy 63",
            },
            "coverage": {
                "state": "partial",
                "kg_node_ids": [PUB_ID, *ARGUMENT_IDS],
                "basis": (
                    "Bibliographic identity and eight author-manuscript-grounded "
                    "arguments are represented. Claim-level correspondence to the "
                    "published pages 49-88 remains unmapped."
                ),
                "last_audited": "2026-08-24",
            },
            "provenance": [
                {
                    "locator": PDF_RELATIVE,
                    "role": "source_file",
                    "sha256": PDF_SHA256,
                },
                {
                    "accessed_at": NOW_ISO,
                    "locator": AUTHORITY_URL,
                    "role": "catalog_record",
                },
                {"locator": "data/kg/publications.bib", "role": "bibliography"},
            ],
            "notes": (
                "The local PDF is a 56-page author manuscript created on 24 "
                "January 2024. The published chapter occupies pp. 49-88, but no "
                "page-by-page concordance is asserted. Winter 2022 is the nominal "
                "volume label, not the publication date. No explicit reuse licence "
                "was found, so public access is not treated as permission to "
                "redistribute."
            ),
        }
    )
    return record


def transform_evidence(record: dict[str, Any]) -> dict[str, Any]:
    record.update(
        {
            "claim_text": (
                "Author-manuscript-grounded argument map for De Interpretatione "
                "9 and Posterior Analytics II.12; published page correspondence "
                "is not yet established."
            ),
            "claim_status": "in_review",
            "locator": {
                "canonical_locus": (
                    "local author manuscript pp. 1-56; published chapter pp. 49-88"
                ),
                "edition_or_witness": (
                    "Carter author manuscript, 56-page PDF, SHA-256 " + PDF_SHA256
                ),
                "pdf_pages": {"start": 1, "end": 56},
                "printed_pages": {"start": 49, "end": 88},
                "page_map_status": "unmapped",
            },
            "kg_targets": [
                PUB_ID,
                "work_de_interpretatione_aristotle_c350bce_e4f6g8h0",
                *ARGUMENT_IDS,
            ],
            "required_verification": [
                "locus_or_page",
                "semantic_entailment",
                "attribution",
                "independent_review",
                "adversarial_review",
            ],
            "notes": (
                "In this locator, pdf_pages means author-manuscript pages and "
                "printed_pages means the published container range. These are "
                "document-level extents, not a page concordance. Argument nodes "
                "therefore use author_ms_page and published_page=null."
            ),
        }
    )
    return record


def transform_identity_issue(record: dict[str, Any]) -> dict[str, Any]:
    record.update(
        {
            "status": "adjudicated",
            "summary": (
                "Carter's chapter belongs to Oxford Studies in Ancient Philosophy "
                "63, nominally labelled Winter 2022, and was published on 6 June "
                "2024 at pp. 49-88. The local file is a separate 56-page author "
                "manuscript."
            ),
            "affected_ids": [SOURCE_ID, EVIDENCE_ID, PUB_ID, *ARGUMENT_IDS],
            "evidence_artifacts": [
                {
                    "locator": PDF_RELATIVE,
                    "role": "source_file",
                    "sha256": PDF_SHA256,
                },
                {
                    "accessed_at": NOW_ISO,
                    "locator": AUTHORITY_URL,
                    "role": "catalog_record",
                },
                {"locator": "data/kg/publications.bib", "role": "bibliography"},
            ],
            "resolution_criteria": (
                "Adjudicated: distinguish nominal volume label, effective "
                "publication date, published container pages and local author "
                "manuscript. Claim-level page concordance is tracked separately."
            ),
            "adjudication": {
                "decision": (
                    "Use publication year 2024 and date 2024-06-06; retain Winter "
                    "2022 only as the nominal volume label; cite published pages "
                    "49-88; classify the local 56-page PDF as an author manuscript."
                ),
                "rationale": (
                    "The PDF title/author and metadata identify the local "
                    "manuscript. The St Andrews institutional record independently "
                    "identifies the peer-reviewed chapter, volume, nominal label, "
                    "publisher, publication date, pages and DOI."
                ),
                "decided_at": NOW_ISO,
            },
        }
    )
    return record


def transform_wave(record: dict[str, Any]) -> dict[str, Any]:
    if record["wave_id"] == "wave_00_known_factual_blockers":
        record["issue_ids"] = [
            PAGE_ISSUE_ID if value == IDENTITY_ISSUE_ID else value
            for value in record.get("issue_ids", [])
        ]
        record["exit_criteria"] = [
            (
                "Carter's bibliographic identity is adjudicated; all claim-level "
                "locators distinguish author-manuscript pages from published "
                "pages, and no unmapped published-page claim is exposed as verified."
                if "Carter bibliographic identity conflict" in value
                else value
            )
            for value in record.get("exit_criteria", [])
        ]
    if record["wave_id"] == "wave_02_wire_existing_scholarship":
        record["issue_ids"] = [
            PAGE_ISSUE_ID if value == IDENTITY_ISSUE_ID else value
            for value in record.get("issue_ids", [])
        ]
        record["blocked_by"] = [
            PAGE_ISSUE_ID if value == IDENTITY_ISSUE_ID else value
            for value in record.get("blocked_by", [])
        ]
    return record


PAGE_ISSUE = {
    "record_type": "issue",
    "issue_id": PAGE_ISSUE_ID,
    "issue_type": "provenance_gap",
    "severity": "high",
    "factual_risk": True,
    "status": "open",
    "summary": (
        "The local Carter artifact has author-manuscript pages 1-56 while the "
        "published chapter occupies pages 49-88; no claim-level concordance has "
        "been established."
    ),
    "affected_ids": [SOURCE_ID, EVIDENCE_ID, PUB_ID, *ARGUMENT_IDS],
    "evidence_artifacts": [
        {"locator": PDF_RELATIVE, "role": "source_file", "sha256": PDF_SHA256},
        {"accessed_at": NOW_ISO, "locator": AUTHORITY_URL, "role": "catalog_record"},
    ],
    "resolution_criteria": (
        "Acquire or inspect the published typeset chapter and visually map every "
        "author-manuscript page used by the eight claims to its published page. "
        "Until then, retain author_ms_page, published_page=null and "
        "published_page_map_status=unmapped."
    ),
}

VERIFICATIONS = [
    {
        "record_type": "verification",
        "verification_id": "ver_carter_identity_pdf_wave1_20260824",
        "target_type": "issue",
        "target_id": IDENTITY_ISSUE_ID,
        "stage": "primary",
        "verifier": {
            "verifier_id": "agent_pdf_gap_wave1",
            "kind": "agent",
            "independence_group": "pdf_full_read_carter_20260824",
        },
        "method": (
            "Full local-PDF inventory, metadata extraction, title-page reading and "
            "visual page inspection."
        ),
        "checked_locators": [PDF_RELATIVE],
        "verdict": "pass",
        "created_at": NOW_ISO,
        "artifacts": [
            {"locator": PDF_RELATIVE, "role": "source_file", "sha256": PDF_SHA256}
        ],
        "notes": (
            "Establishes that the local artifact is a 56-page Jason W. Carter "
            "author manuscript, not the published-page setting."
        ),
    },
    {
        "record_type": "verification",
        "verification_id": "ver_carter_identity_authority_recheck_20260824",
        "target_type": "issue",
        "target_id": IDENTITY_ISSUE_ID,
        "stage": "independent",
        "verifier": {
            "verifier_id": "agent_ancient_source_coverage",
            "kind": "agent",
            "independence_group": "institutional_authority_recheck_carter_20260824",
        },
        "method": (
            "Independent comparison of the local PDF metadata and title page with "
            "the St Andrews institutional publication record and DOI metadata."
        ),
        "checked_locators": [PDF_RELATIVE, AUTHORITY_URL, f"https://doi.org/{DOI}"],
        "verdict": "pass",
        "created_at": NOW_ISO,
        "artifacts": [
            {"locator": PDF_RELATIVE, "role": "source_file", "sha256": PDF_SHA256},
            {"accessed_at": NOW_ISO, "locator": AUTHORITY_URL, "role": "catalog_record"},
        ],
        "notes": (
            "Confirms OSAP 63, Winter 2022 as nominal label, effective publication "
            "2024-06-06, pp.49-88 and DOI. It does not establish page concordance."
        ),
    },
    {
        "record_type": "verification",
        "verification_id": "ver_carter_identity_adversarial_20260824",
        "target_type": "issue",
        "target_id": IDENTITY_ISSUE_ID,
        "stage": "adversarial",
        "verifier": {
            "verifier_id": "agent_ancient_source_coverage",
            "kind": "agent",
            "independence_group": "carter_failure_mode_audit_20260824",
        },
        "method": (
            "Attempted falsification across five confounders: nominal versus "
            "effective year, manuscript versus published pagination, Phronesis "
            "versus OSAP, article versus book chapter, and access versus licence."
        ),
        "checked_locators": [PDF_RELATIVE, AUTHORITY_URL, "data/kg/nodes.jsonl"],
        "verdict": "pass",
        "created_at": NOW_ISO,
        "artifacts": [
            {"locator": "scripts/apply_2026_08_24_carter_p0_repair.py", "role": "audit_report"},
            {"accessed_at": NOW_ISO, "locator": AUTHORITY_URL, "role": "catalog_record"},
        ],
        "notes": (
            "Identity survives the adversarial check. Page concordance and reuse "
            "licence remain explicitly unresolved and are not upgraded."
        ),
    },
]


def ensure_exact_shard(
    existing: list[dict[str, Any]], desired: list[dict[str, Any]], label: str
) -> tuple[list[dict[str, Any]], bool]:
    if not existing:
        return copy.deepcopy(desired), True
    if existing != desired:
        raise RuntimeError(f"unexpected pre-existing Carter {label} shard")
    return copy.deepcopy(existing), False


def transform_registry(
    sources: list[dict[str, Any]],
    evidence: list[dict[str, Any]],
    issues: list[dict[str, Any]],
    waves: list[dict[str, Any]],
    page_issues: list[dict[str, Any]],
    verifications: list[dict[str, Any]],
) -> tuple[dict[str, list[dict[str, Any]]], list[dict[str, Any]], Counter[str]]:
    quarantine: list[dict[str, Any]] = []
    counts: Counter[str] = Counter()
    sources, old = replace_record(sources, SOURCE_ID, transform_source)
    if old:
        quarantine.append({"record_type": "registry_source_before", "record": old})
        counts["registry_source_corrected"] += 1
    evidence, old = replace_record(evidence, EVIDENCE_ID, transform_evidence)
    if old:
        quarantine.append({"record_type": "registry_evidence_before", "record": old})
        counts["registry_evidence_corrected"] += 1
    issues, old = replace_record(issues, IDENTITY_ISSUE_ID, transform_identity_issue)
    if old:
        quarantine.append({"record_type": "registry_issue_before", "record": old})
        counts["registry_identity_issue_adjudicated"] += 1

    transformed_waves: list[dict[str, Any]] = []
    for record in copy.deepcopy(waves):
        before = copy.deepcopy(record)
        record = transform_wave(record)
        if record != before:
            quarantine.append({"record_type": "registry_wave_before", "record": before})
            counts["registry_wave_corrected"] += 1
        transformed_waves.append(record)
    waves = transformed_waves

    page_issues, changed = ensure_exact_shard(page_issues, [PAGE_ISSUE], "issue")
    if changed:
        counts["registry_page_issue_added"] += 1
    verifications, changed = ensure_exact_shard(
        verifications, VERIFICATIONS, "verification"
    )
    if changed:
        counts["registry_verifications_added"] += len(VERIFICATIONS)

    result = {
        "sources": sources,
        "evidence": evidence,
        "issues": issues,
        "waves": waves,
        "page_issues": page_issues,
        "verifications": verifications,
    }
    validate_registry(result)
    return result, quarantine, counts


def validate_registry(result: dict[str, list[dict[str, Any]]]) -> None:
    source = next(r for r in result["sources"] if record_id(r) == SOURCE_ID)
    assert source["identity_status"] == "bibliography_verified"
    assert source["canonical_identifiers"]["published_at"] == "2024-06-06"
    evidence = next(r for r in result["evidence"] if record_id(r) == EVIDENCE_ID)
    assert evidence["locator"]["pdf_pages"] == {"start": 1, "end": 56}
    assert evidence["locator"]["printed_pages"] == {"start": 49, "end": 88}
    assert evidence["locator"]["page_map_status"] == "unmapped"
    identity = next(
        r for r in result["issues"] if record_id(r) == IDENTITY_ISSUE_ID
    )
    assert identity["status"] == "adjudicated"
    assert result["page_issues"] == [PAGE_ISSUE]
    assert result["verifications"] == VERIFICATIONS
    wave2 = next(r for r in result["waves"] if r["wave_id"] == "wave_02_wire_existing_scholarship")
    assert PAGE_ISSUE_ID in wave2["blocked_by"]
    assert IDENTITY_ISSUE_ID not in wave2["blocked_by"]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def serialize_jsonl(records: list[dict[str, Any]], *, compact: bool) -> str:
    # JSON object order is semantically irrelevant, but retaining the parsed key
    # order keeps this Carter-only migration from churning unrelated JSONL rows.
    kwargs: dict[str, Any] = {"ensure_ascii": False, "sort_keys": False}
    if compact:
        kwargs["separators"] = (",", ":")
    return "".join(json.dumps(record, **kwargs) + "\n" for record in records)


def atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=path.parent, delete=False
    ) as handle:
        handle.write(text)
        temp_path = Path(handle.name)
    temp_path.replace(path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, default=DEFAULT_DATA_ROOT)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    data_root = args.data_root
    repo_root = data_root.parent

    pdf = repo_root / PDF_RELATIVE
    if not pdf.exists() or sha256_file(pdf) != PDF_SHA256:
        raise RuntimeError("Carter source PDF is missing or its SHA-256 changed")

    nodes_path = data_root / "kg/nodes.jsonl"
    edges_path = data_root / "kg/edges.jsonl"
    bib_path = data_root / "kg/publications.bib"
    registry = data_root / "goals/sota/registry"
    source_path = registry / "sources/seed_priority_20260824.jsonl"
    evidence_path = registry / "evidence/seed_priority_20260824.jsonl"
    issue_path = registry / "issues/seed_known_20260824.jsonl"
    wave_path = registry / "waves/priority_20260824.jsonl"
    page_issue_path = registry / "issues/carter_p0_20260824.jsonl"
    verification_path = registry / "verifications/carter_identity_20260824.jsonl"
    quarantine_path = data_root / "audit/2026-08-24_carter_p0_quarantine.jsonl"

    new_nodes, new_edges, quarantine, graph_counts = transform_graph(
        read_jsonl(nodes_path), read_jsonl(edges_path)
    )
    bib_before = bib_path.read_text(encoding="utf-8")
    bib_after, old_bib_entry = replace_bibtex_entry(bib_before)
    if old_bib_entry:
        quarantine.append(
            {"record_type": "bibtex_entry_before", "record": old_bib_entry}
        )
        graph_counts["bibtex_corrected"] += 1

    registry_result, registry_quarantine, registry_counts = transform_registry(
        read_jsonl(source_path),
        read_jsonl(evidence_path),
        read_jsonl(issue_path),
        read_jsonl(wave_path),
        read_jsonl(page_issue_path),
        read_jsonl(verification_path),
    )
    quarantine.extend(registry_quarantine)
    counts = graph_counts + registry_counts
    changed = bool(counts)

    print("mode:", "write" if args.write else "dry-run")
    print("changed:", changed)
    print("counts:", dict(sorted(counts.items())))
    print("quarantine records:", len(quarantine))
    print("advanced_in Carter edges:", counts.get("advanced_in_added", 0))

    if not args.write:
        return 0
    if not changed:
        print("write: no-op (already applied)")
        return 0
    if quarantine_path.exists():
        raise RuntimeError(
            f"refusing to overwrite existing Carter quarantine: {quarantine_path}"
        )

    atomic_write(nodes_path, serialize_jsonl(new_nodes, compact=False))
    atomic_write(edges_path, serialize_jsonl(new_edges, compact=False))
    atomic_write(bib_path, bib_after)
    atomic_write(source_path, serialize_jsonl(registry_result["sources"], compact=True))
    atomic_write(evidence_path, serialize_jsonl(registry_result["evidence"], compact=True))
    atomic_write(issue_path, serialize_jsonl(registry_result["issues"], compact=True))
    atomic_write(wave_path, serialize_jsonl(registry_result["waves"], compact=True))
    atomic_write(
        page_issue_path,
        serialize_jsonl(registry_result["page_issues"], compact=True),
    )
    atomic_write(
        verification_path,
        serialize_jsonl(registry_result["verifications"], compact=True),
    )
    atomic_write(quarantine_path, serialize_jsonl(quarantine, compact=True))
    print("write: applied")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
