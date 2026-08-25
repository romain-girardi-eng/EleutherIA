from __future__ import annotations

import hashlib
import unicodedata

import pytest

from scripts import check_ingestion_rules as rules


def person(node_id: str, label: str) -> dict:
    return {
        "id": node_id,
        "node_id": node_id,
        "type": "person",
        "label": label,
        "metadata": {},
    }


def r2_violations() -> list[tuple[str, str, str, str]]:
    return [row for row in rules.violations if row[0] == "R2_duplicate_identity"]


def test_whole_graph_reports_each_legacy_duplicate_group_once_as_warning() -> None:
    nodes = [person("person_first", "Same Scholar"), person("person_second", "Same Scholar")]

    rules.check(nodes, [], None, None)

    assert r2_violations() == [
        (
            "R2_duplicate_identity",
            rules.WARN,
            "person_first",
            "2 nodes share identity key ('person', ('same', 'scholar')): "
            "person_first, person_second",
        )
    ]


def test_ingestion_delta_still_blocks_existing_and_within_batch_duplicates() -> None:
    existing = person("person_existing", "Same Scholar")
    first = person("person_new_first", "Same Scholar")
    second = person("person_new_second", "Same Scholar")

    rules.check([existing, first, second], [], [first, second], [])

    r2 = r2_violations()
    assert len(r2) == 3
    assert {row[1] for row in r2} == {rules.BLOCK}
    assert sum("already held by person_existing" in row[3] for row in r2) == 2
    assert sum("duplicated within this batch" in row[3] for row in r2) == 1


def test_ingestion_delta_blocks_reusing_an_existing_node_id() -> None:
    existing = person("person_existing", "Existing Scholar")
    replacement = person("person_existing", "Renamed Scholar")

    rules.check([existing, replacement], [], [replacement], [])

    assert (
        "R2_duplicate_identity",
        rules.BLOCK,
        "person_existing",
        "node_id already exists in the graph — update the existing record, do not add it",
    ) in r2_violations()


def lost_source_translation(node_id: str) -> dict:
    description = "Ancient Latin text"
    return {
        "id": node_id,
        "node_id": node_id,
        "type": "passage",
        "label": "Irenaeus ancient Latin witness",
        "description": description,
        "metadata": {
            "canonical_locus": "IV.37.1",
            "language": "lat",
            "manifestation_id": "irenaeus_latin_witness",
            "passage_role": "translation",
            "review_status": "independently_collated",
            "scan_page_map_visually_verified": True,
            "scan_sha256": "c" * 64,
            "source_artifact_sha256": "a" * 64,
            "source_language": "grc",
            "source_locator": "SCO:Irenaeus/ancient-latin",
            "source_passage_status": "lost_continuous_greek_not_mapped",
            "text_content_sha256_nfc": hashlib.sha256(
                unicodedata.normalize("NFC", description).encode("utf-8")
            ).hexdigest(),
            "text_sha256": hashlib.sha256(
                unicodedata.normalize("NFC", description).encode("utf-8")
            ).hexdigest(),
            "pdf_page_range": "459-461",
            "printed_page_range": "918-922",
            "translation_type": "ancient_human_literal",
            "translator": "anonymous ancient Latin translator",
            "transmission_class": "ancient_latin_translation",
        },
    }


def test_collated_ancient_translation_can_declare_a_lost_source() -> None:
    witness = lost_source_translation("passage_irenaeus_latin")

    rules.check([witness], [], None, None)

    assert not [row for row in rules.violations if row[0].startswith("R7_")]


@pytest.mark.parametrize(
    ("field", "invalid_value"),
    [
        ("source_artifact_sha256", None),
        ("source_artifact_sha256", "g" * 64),
        ("scan_sha256", None),
        ("scan_sha256", "not-a-sha256"),
        ("text_content_sha256_nfc", None),
        ("text_content_sha256_nfc", "b" * 64),
        ("text_sha256", "b" * 64),
        ("source_locator", None),
        ("source_locator", "x"),
        ("pdf_page_range", None),
        ("pdf_page_range", "999-1"),
        ("printed_page_range", None),
        ("printed_page_range", "922-918"),
        ("translator", 42),
        ("manifestation_id", 42),
        ("canonical_locus", 42),
    ],
)
def test_lost_source_exception_remains_fail_closed_when_provenance_is_incomplete(
    field: str,
    invalid_value: object,
) -> None:
    witness = lost_source_translation("passage_irenaeus_incomplete")
    if invalid_value is None:
        witness["metadata"].pop(field)
    else:
        witness["metadata"][field] = invalid_value

    rules.check([witness], [], None, None)

    assert [row[0:3] for row in rules.violations if row[0].startswith("R7_")] == [
        (
            "R7_translation_without_original",
            rules.BLOCK,
            "passage_irenaeus_incomplete",
        )
    ]


def test_lost_source_exception_requires_a_passage_node() -> None:
    witness = lost_source_translation("passage_irenaeus_wrong_type")
    witness["type"] = "publication"

    rules.check([witness], [], None, None)

    assert [row[0:3] for row in rules.violations if row[0].startswith("R7_")] == [
        (
            "R7_translation_without_original",
            rules.BLOCK,
            "passage_irenaeus_wrong_type",
        )
    ]
