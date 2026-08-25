from __future__ import annotations

from collections import Counter
from pathlib import Path

from scripts.apply_2026_08_24_carter_p0_repair import (
    ARGUMENT_IDS,
    ARGUMENT_PAGES,
    ARGUMENT_SUPPORT_PAGES,
    BIBTEX_ENTRY,
    DOI,
    EVIDENCE_ID,
    IDENTITY_ISSUE_ID,
    OBJECTIONS_ID,
    PAGE_ISSUE,
    PAGE_ISSUE_ID,
    PUB_ID,
    SOURCE_ID,
    VERIFICATIONS,
    WRONG_STANCE_EDGE_ID,
    metadata,
    node_id,
    read_jsonl,
    replace_bibtex_entry,
    transform_graph,
    transform_registry,
    validate_graph,
    validate_registry,
)

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
REGISTRY = DATA / "goals/sota/registry"


def load_graph():
    return (
        read_jsonl(DATA / "kg/nodes.jsonl"),
        read_jsonl(DATA / "kg/edges.jsonl"),
    )


def load_registry():
    return (
        read_jsonl(REGISTRY / "sources/seed_priority_20260824.jsonl"),
        read_jsonl(REGISTRY / "evidence/seed_priority_20260824.jsonl"),
        read_jsonl(REGISTRY / "issues/seed_known_20260824.jsonl"),
        read_jsonl(REGISTRY / "waves/priority_20260824.jsonl"),
        read_jsonl(REGISTRY / "issues/carter_p0_20260824.jsonl"),
        read_jsonl(REGISTRY / "verifications/carter_identity_20260824.jsonl"),
    )


def test_carter_identity_semantics_and_provenance_are_corrected() -> None:
    nodes, edges, quarantine, _ = transform_graph(*load_graph())
    validate_graph(nodes, edges)
    by_node = {node_id(node): node for node in nodes}

    publication = metadata(by_node[PUB_ID])
    assert publication["type"] == "book_chapter"
    assert publication["doi"] == DOI
    assert publication["nominal_volume_year"] == 2022
    assert publication["publication_date"] == "2024-06-06"
    assert publication["pages"] == "49-88"
    assert publication["page_correspondence"] == {
        "author_ms_pages": "1-56",
        "published_pages": "49-88",
        "status": "unmapped",
    }
    assert "license" not in publication
    assert "phronesis" not in str(by_node[PUB_ID]).lower()

    for argument_id in ARGUMENT_IDS:
        argument = metadata(by_node[argument_id])
        assert argument["author_ms_page"] == ARGUMENT_PAGES[argument_id]
        assert argument["published_page"] is None
        assert argument["published_page_map_status"] == "unmapped"
        assert argument["verbatim_evidence"]["author_ms_page"] == (
            ARGUMENT_PAGES[argument_id]
        )
        assert "page" not in argument["verbatim_evidence"]
    for argument_id, pages in ARGUMENT_SUPPORT_PAGES.items():
        assert metadata(by_node[argument_id])["author_ms_support_pages"] == pages

    correction = metadata(by_node[OBJECTIONS_ID])["semantic_correction"]
    assert correction["accepted"] == [
        "Future Truth Necessity for modally unqualified future singulars"
    ]
    assert "Future Falsity Necessity as a universal inference" in (
        correction["rejected_or_restricted"]
    )
    stance = next(edge for edge in edges if edge["edge_id"] == WRONG_STANCE_EDGE_ID)
    assert stance["relation"] == "argues_against"
    assert sum(
        edge["relation"] == "advanced_in"
        and edge["source"] in ARGUMENT_IDS
        and edge["target"] == PUB_ID
        for edge in edges
    ) == 8
    if quarantine:
        assert all("record_type" in row and "record" in row for row in quarantine)


def test_carter_bibliography_is_targeted_and_idempotent() -> None:
    before = (DATA / "kg/publications.bib").read_text(encoding="utf-8")
    after, old = replace_bibtex_entry(before)
    assert BIBTEX_ENTRY in after
    assert "@incollection{" in BIBTEX_ENTRY
    assert "author = {Jason W. Carter}" in BIBTEX_ENTRY
    assert "date = {2024-06-06}" in BIBTEX_ENTRY
    assert "pages = {49--88}" in BIBTEX_ENTRY
    assert "Phronesis" not in BIBTEX_ENTRY
    assert "license" not in BIBTEX_ENTRY.lower()
    second, second_old = replace_bibtex_entry(after)
    assert second == after
    assert second_old is None
    if old is not None:
        assert old not in after


def test_carter_registry_keeps_unknown_page_concordance_open() -> None:
    result, quarantine, _ = transform_registry(*load_registry())
    validate_registry(result)

    source = next(row for row in result["sources"] if row.get("source_id") == SOURCE_ID)
    assert source["canonical_identifiers"]["published_at"] == "2024-06-06"
    evidence = next(
        row for row in result["evidence"] if row.get("evidence_id") == EVIDENCE_ID
    )
    assert evidence["locator"]["pdf_pages"] == {"start": 1, "end": 56}
    assert evidence["locator"]["printed_pages"] == {"start": 49, "end": 88}
    assert evidence["locator"]["page_map_status"] == "unmapped"
    identity = next(
        row for row in result["issues"] if row.get("issue_id") == IDENTITY_ISSUE_ID
    )
    assert identity["status"] == "adjudicated"
    assert result["page_issues"] == [PAGE_ISSUE]
    assert result["page_issues"][0]["issue_id"] == PAGE_ISSUE_ID
    assert result["page_issues"][0]["status"] == "open"
    assert result["verifications"] == VERIFICATIONS
    if quarantine:
        assert all("record_type" in row and "record" in row for row in quarantine)


def test_carter_repair_transforms_are_idempotent() -> None:
    first_graph = transform_graph(*load_graph())
    second_graph = transform_graph(first_graph[0], first_graph[1])
    assert second_graph[:2] == first_graph[:2]
    assert second_graph[2] == []
    assert second_graph[3] == Counter()

    first_registry = transform_registry(*load_registry())
    mapped = first_registry[0]
    second_registry = transform_registry(
        mapped["sources"],
        mapped["evidence"],
        mapped["issues"],
        mapped["waves"],
        mapped["page_issues"],
        mapped["verifications"],
    )
    assert second_registry[0] == mapped
    assert second_registry[1] == []
    assert second_registry[2] == Counter()
