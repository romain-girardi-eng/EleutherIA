from __future__ import annotations

import xml.etree.ElementTree as ET

from scripts.data_2026_08_18_clement_primary_grounding import (
    ARGUMENT_FAITH_NATURE,
    ARGUMENT_GRACE_ASSENT,
    EVIDENCE_TARGETS,
    TARGETS,
)
from scripts.ingest_2026_08_18_clement_primary_grounding import (
    passage_node_id,
    passage_uuid,
    reading_text,
    sequence_number,
)


def test_documented_scope_resolves_to_58_unique_cts_divisions() -> None:
    keys = [spec[:3] for spec in TARGETS]
    assert len(keys) == 58
    assert len(set(keys)) == 58

    # Amand's abbreviated II,11,1-2 is flat section 11, not chapter 11.
    assert (2, 3, 11) in keys
    # The broad locus is chapter II.6 through II.15, including its central
    # cooperation passage and the three older II.11 nodes.
    assert (2, 6, 26) in keys
    assert {(2, 11, section) for section in (50, 51, 52)} <= set(keys)
    assert (4, 23, 152) in keys
    assert (4, 24, 153) in keys
    assert (5, 13, 86) in keys


def test_evidence_targets_keep_the_two_arguments_distinct() -> None:
    assert EVIDENCE_TARGETS[ARGUMENT_FAITH_NATURE] == ((2, 3, 11),)
    assert (2, 3, 11) not in EVIDENCE_TARGETS[ARGUMENT_GRACE_ASSENT]
    assert EVIDENCE_TARGETS[ARGUMENT_GRACE_ASSENT] == (
        (2, 2, 8),
        (2, 6, 26),
        (2, 12, 54),
        (2, 12, 55),
        (4, 23, 152),
        (4, 24, 153),
        (5, 13, 86),
    )


def test_snapshot_uuid_matches_project_bootstrap_identity() -> None:
    assert passage_uuid(passage_node_id(2, 3, 11)) == (
        "5a221307-b0c5-5f9a-87b3-771fbd2f312b"
    )
    assert passage_uuid(passage_node_id(4, 24, 153)) == (
        "aae362b3-1b81-59fa-a5ce-e7f46a9edf07"
    )


def test_sequence_number_preserves_book_chapter_section_order() -> None:
    values = [
        sequence_number(1, 17, 84),
        sequence_number(2, 2, 8),
        sequence_number(2, 15, 71),
        sequence_number(4, 23, 147),
        sequence_number(5, 13, 86),
    ]
    assert values == sorted(values)
    assert len(set(values)) == len(values)


def test_tei_reading_uses_edited_lemma_and_excludes_deletion() -> None:
    element = ET.fromstring(
        "<p>alpha <del>deleted</del> beta "
        "<choice><sic>bad</sic><corr>good</corr></choice> "
        "<app><lem>lemma</lem><rdg>variant</rdg></app></p>"
    )
    assert " ".join(reading_text(element).split()) == "alpha beta good lemma"
