"""The shared ``[edge: …]`` marker grammar: one parser, one scrubber.

Fixtures are modelled on the markers production answers actually carried
(spaces around the arrow, a line break inside the marker, punctuation before
the closing bracket, a hyphenated relation, ``edge_`` for ``edge:``): every
spelling must parse to the same link and must leave no ``[edge`` behind.
"""

from __future__ import annotations

import pytest

from eleutheria_graphrag.agents.edge_markers import (
    EDGE_MARKER_RE,
    parse_edge_marker,
    strip_edge_markers,
)

PRODUCTION_SAMPLE = (
    "Against this stands Dobbin, who reads Epictetus as opening a genuine "
    "preserve of freedom [edge: opposes "
    "P_position_dobbin_epictetan_inner_preserve_immune_to_fate->"
    "P_position_long_epictetus_fate_internalised]. Long reads the same texts "
    "as internalising fate."
)

# ── parser ───────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "body",
    [
        "opposes P_a->P_b",
        ": opposes P_a->P_b",  # the ledger's generic regex keeps the colon
        "opposes P_a -> P_b",
        "opposes  P_a  ->  P_b ",
        "opposes\nP_a->P_b",
        "opposes P_a->\nP_b",
        "opposes P_a->P_b.",
        "opposes P_a->P_b,",
        "opposes P_a->P_b)",
        "opposes P_a-->P_b",
        "opposes P_a → P_b",
        "opposes P_a => P_b",
        "opposes: P_a->P_b",
        "Opposes P_a->P_b",
        "P_a opposes P_b",
    ],
)
def test_parse_reads_the_same_link_off_every_spelling(body: str) -> None:
    edge = parse_edge_marker(body)
    assert edge is not None
    assert edge.key == ("opposes", "a", "b")


def test_parse_normalises_a_hyphenated_relation_to_graph_vocabulary() -> None:
    edge = parse_edge_marker("is-refined-by P_a->P_b")
    assert edge is not None
    assert edge.relation == "is_refined_by"


def test_parse_keeps_long_snake_case_ids_whole() -> None:
    match = EDGE_MARKER_RE.search(PRODUCTION_SAMPLE)
    assert match is not None
    edge = parse_edge_marker(match.group("body"))
    assert edge is not None
    assert edge.from_id == "position_dobbin_epictetan_inner_preserve_immune_to_fate"
    assert edge.to_id == "position_long_epictetus_fate_internalised"


@pytest.mark.parametrize("body", ["", "opposes", "opposes P_a", "P_a->P_b", "x y z"])
def test_parse_rejects_a_body_without_two_endpoints(body: str) -> None:
    assert parse_edge_marker(body) is None


# ── locating ─────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "marker",
    [
        "[edge: opposes P_a->P_b]",
        "[edge:opposes P_a->P_b]",
        "[edge_ opposes P_a->P_b]",
        "[Edge: opposes P_a->P_b]",
        "[ edge : opposes P_a -> P_b ]",
        "[edge: opposes\nP_a->P_b]",
    ],
)
def test_marker_regex_finds_every_spelling(marker: str) -> None:
    assert EDGE_MARKER_RE.search(f"prose {marker} prose") is not None


def test_marker_regex_never_swallows_the_neighbouring_cite() -> None:
    text = "[edge: opposes P_a->P_b] [P_a: Bobzien, 1998 p. 330]"
    match = EDGE_MARKER_RE.search(text)
    assert match is not None
    assert match.group(0) == "[edge: opposes P_a->P_b]"


# ── scrubbing ────────────────────────────────────────────────────────────────


def test_strip_removes_the_production_sample_and_keeps_its_link() -> None:
    scrub = strip_edge_markers(PRODUCTION_SAMPLE)
    assert scrub.text == (
        "Against this stands Dobbin, who reads Epictetus as opening a genuine "
        "preserve of freedom. Long reads the same texts as internalising fate."
    )
    assert scrub.count == 1
    assert [e.key for e in scrub.edges] == [
        (
            "opposes",
            "position_dobbin_epictetan_inner_preserve_immune_to_fate",
            "position_long_epictetus_fate_internalised",
        )
    ]


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        # spaces around the arrow, mid-sentence
        ("the two [edge: opposes P_a -> P_b] argue.", "the two argue."),
        # line-wrapped marker
        ("the two [edge: opposes\nP_a->P_b] argue.", "the two argue."),
        # punctuation before the closing bracket, marker before the period
        ("the two positions [edge: opposes P_a->P_b.].", "the two positions."),
        # marker followed by a comma
        ("the two [edge: is-refined-by P_a --> P_b], then.", "the two, then."),
        # marker opening a line
        ("[edge: opposes P_a->P_b] Frede replies.", "Frede replies."),
        # marker closing a line
        ("Frede replies [edge: opposes P_a->P_b]\nNext.", "Frede replies\nNext."),
        # marker glued to both words
        ("X[edge: opposes P_a->P_b]Y", "X Y"),
        # two markers in a row
        ("X [edge: opposes P_a->P_b] [edge: opposes P_b->P_a] Y", "X Y"),
        # subject-verb-object body
        ("Frame [edge: P_a opposes P_b] (Bobzien 1998).", "Frame (Bobzien 1998)."),
    ],
)
def test_strip_tidies_the_whitespace_the_marker_sat_in(
    text: str, expected: str
) -> None:
    assert strip_edge_markers(text).text == expected


def test_strip_handles_headings_and_blockquotes() -> None:
    text = (
        "## Where the fault line runs [edge: opposes P_a->P_b]\n"
        "> Bobzien against Frede [edge_ opposes P_a→P_b] on assent.\n"
        "- a bullet [edge: opposes P_a->P_b]\n"
    )
    scrub = strip_edge_markers(text)
    assert scrub.text == (
        "## Where the fault line runs\n> Bobzien against Frede on assent.\n- a bullet\n"
    )
    assert scrub.count == 3


def test_strip_removes_a_marker_alone_on_its_line_with_the_line() -> None:
    assert strip_edge_markers("Alone:\n[edge: opposes P_a->P_b]\nNext.").text == (
        "Alone:\nNext."
    )


def test_strip_removes_a_marker_the_model_never_closed() -> None:
    scrub = strip_edge_markers("cut off here [edge: opposes P_a->P_b")
    assert scrub.text == "cut off here"
    assert scrub.count == 1
    assert scrub.edges == ()


def test_strip_leaves_reader_facing_cites_untouched() -> None:
    text = (
        "Bobzien [P_bobzien_no_problem: Bobzien, 1998 p. 330] on "
        "[passage_cic_fat_41: Cicero, De Fato 41] and a legacy ref [P1]."
    )
    scrub = strip_edge_markers(text)
    assert scrub.text == text
    assert scrub.count == 0


def test_strip_is_idempotent_and_leaves_no_edge_text() -> None:
    text = (
        "A [edge: opposes P_a -> P_b] B [edge: opposes\nP_b->P_a.] C "
        "[Edge: refines P_c-->P_d]\n[edge: opposes P_a->P_b"
    )
    once = strip_edge_markers(text)
    assert "[edge" not in once.text.lower()
    assert once.count == 4
    twice = strip_edge_markers(once.text)
    assert twice.text == once.text
    assert twice.count == 0


def test_strip_returns_text_without_brackets_unchanged() -> None:
    assert strip_edge_markers("no brackets at all").text == "no brackets at all"
    assert strip_edge_markers("").text == ""
