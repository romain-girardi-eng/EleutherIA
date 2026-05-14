"""Tests for the thesis-grade structured output schema and renderer."""

from __future__ import annotations

import json
import re

import pytest

from eleutheria_graphrag.models.thesis_output import (
    BibliographyEntry,
    Citation,
    Footnote,
    Paragraph,
    Section,
    ThesisDraft,
    slugify_ascii,
)
from eleutheria_graphrag.services.thesis_renderer import (
    ThesisRenderer,
    export_draft,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_citation() -> Citation:
    return Citation(
        passage_id="passage_eth_nic_1110a4",
        cts_urn="urn:cts:greekLit:tlg0086.tlg010:1110a4",
        work_label="Nicomachean Ethics",
        author="Aristotle",
        edition="Bywater 1894",
        translation="Ross 1925",
        page_or_section="1110a4-6",
        quote_greek="δοκεῖ δὴ ἑκούσιον εἶναι οὗ ἡ ἀρχὴ ἐν αὐτῷ",
        quote_translation="An act seems voluntary when its origin is in the agent",
    )


@pytest.fixture
def sample_draft(sample_citation: Citation) -> ThesisDraft:
    return ThesisDraft(
        title="The Emergence of Free Will in Aristotle",
        abstract="A study of ἑκούσιον in Eth. Nic. III.",
        sections=[
            Section(
                heading="Introduction",
                level=1,
                paragraphs=[
                    Paragraph(
                        text="Aristotle's account of voluntary action grounds later debates.",
                        footnote_refs=[1],
                    )
                ],
            ),
            Section(
                heading="The voluntary",
                level=1,
                paragraphs=[
                    Paragraph(
                        text="The agent is the principle of the action.",
                        footnote_refs=[1, 2],
                    )
                ],
            ),
        ],
        footnotes=[
            Footnote(
                n=1,
                text="See the classical formulation.",
                citations=[sample_citation],
            ),
            Footnote(
                n=2,
                text="Bobzien situates this in Hellenistic debate.",
                citations=[
                    Citation(
                        passage_id="scholar_bobzien_1998_p234",
                        work_label="Determinism and Freedom in Stoic Philosophy",
                        author="Susanne Bobzien",
                        page_or_section="p. 234",
                        scholar_id="bobzien_1998",
                    )
                ],
            ),
        ],
        bibliography=[
            BibliographyEntry(
                kind="primary",
                author="Aristotle",
                title="Nicomachean Ethics",
                year=1894,
                edition="Ingram Bywater",
                publisher="Clarendon Press",
                cts_urn="urn:cts:greekLit:tlg0086.tlg010",
            ),
            BibliographyEntry(
                kind="secondary",
                author="Susanne Bobzien",
                title="Determinism and Freedom in Stoic Philosophy",
                year=1998,
                publisher="Oxford University Press",
            ),
        ],
    )


# ---------------------------------------------------------------------------
# Pydantic validation
# ---------------------------------------------------------------------------


def test_draft_validates(sample_draft: ThesisDraft) -> None:
    assert sample_draft.title.startswith("The Emergence")
    assert len(sample_draft.footnotes) == 2


def test_draft_rejects_empty_footnotes(sample_draft: ThesisDraft) -> None:
    payload = sample_draft.model_dump()
    payload["footnotes"] = []
    with pytest.raises(ValueError):
        ThesisDraft(**payload)


def test_draft_rejects_empty_bibliography(sample_draft: ThesisDraft) -> None:
    payload = sample_draft.model_dump()
    payload["bibliography"] = []
    with pytest.raises(ValueError):
        ThesisDraft(**payload)


def test_draft_rejects_duplicate_footnote_numbers(sample_citation: Citation) -> None:
    with pytest.raises(ValueError, match="duplicate footnote"):
        ThesisDraft(
            title="t",
            sections=[
                Section(
                    heading="s", paragraphs=[Paragraph(text="p", footnote_refs=[1])]
                )
            ],
            footnotes=[
                Footnote(n=1, text="a", citations=[sample_citation]),
                Footnote(n=1, text="b", citations=[sample_citation]),
            ],
            bibliography=[BibliographyEntry(kind="primary", author="x", title="y")],
        )


def test_draft_rejects_unknown_footnote_ref(sample_citation: Citation) -> None:
    with pytest.raises(ValueError, match="missing footnote"):
        ThesisDraft(
            title="t",
            sections=[
                Section(
                    heading="s", paragraphs=[Paragraph(text="p", footnote_refs=[99])]
                )
            ],
            footnotes=[Footnote(n=1, text="a", citations=[sample_citation])],
            bibliography=[BibliographyEntry(kind="primary", author="x", title="y")],
        )


def test_citation_requires_non_empty_passage_id() -> None:
    with pytest.raises(ValueError):
        Citation(passage_id="", work_label="X")


def test_footnote_requires_at_least_one_citation() -> None:
    with pytest.raises(ValueError):
        Footnote(n=1, text="x", citations=[])


# ---------------------------------------------------------------------------
# Slug / BibTeX key
# ---------------------------------------------------------------------------


def test_slugify_strips_greek_and_diacritics() -> None:
    assert slugify_ascii("Ἀριστοτέλης") == "anon"  # full greek collapses to empty
    assert slugify_ascii("Bobzien, Susanne") == "bobzien-susanne"
    assert slugify_ascii("Müller") == "muller"


def test_bibtex_key_derivation() -> None:
    entry = BibliographyEntry(
        kind="primary",
        author="Aristotle",
        title="Nicomachean Ethics",
        year=1894,
    )
    assert entry.bibtex_key == "aristotle-nicomachean-ethics-1894"


def test_bibtex_key_supplied_is_ascii_safe() -> None:
    entry = BibliographyEntry(
        kind="secondary",
        author="Müller",
        title="Foo",
        bibtex_key="Müller_2020",
    )
    assert entry.bibtex_key == "muller-2020"


def test_bibtex_keys_disambiguate_on_collision(sample_citation: Citation) -> None:
    draft = ThesisDraft(
        title="t",
        sections=[
            Section(heading="s", paragraphs=[Paragraph(text="p", footnote_refs=[1])])
        ],
        footnotes=[Footnote(n=1, text="a", citations=[sample_citation])],
        bibliography=[
            BibliographyEntry(
                kind="primary", author="Aristotle", title="Ethics", year=1894
            ),
            BibliographyEntry(
                kind="primary", author="Aristotle", title="Ethics", year=1894
            ),
        ],
    )
    keys = [e.bibtex_key for e in draft.bibliography]
    assert keys[0] != keys[1]
    assert keys[1].endswith("-2")


# ---------------------------------------------------------------------------
# Markdown rendering
# ---------------------------------------------------------------------------


def test_markdown_contains_footnote_pattern(sample_draft: ThesisDraft) -> None:
    md = ThesisRenderer().to_markdown(sample_draft)
    assert md.startswith("# The Emergence")
    assert "[^1]" in md
    assert "[^2]" in md
    assert "## Notes" in md
    # Greek verbatim must round-trip untouched (no fabrication / no re-encoding).
    assert "δοκεῖ δὴ ἑκούσιον" in md


def test_markdown_separates_primary_and_secondary(sample_draft: ThesisDraft) -> None:
    md = ThesisRenderer().to_markdown(sample_draft)
    assert "### Primary Sources" in md
    assert "### Secondary Literature" in md
    primary_idx = md.index("### Primary Sources")
    secondary_idx = md.index("### Secondary Literature")
    assert primary_idx < secondary_idx
    # Aristotle appears under primary, Bobzien under secondary.
    primary_section = md[primary_idx:secondary_idx]
    secondary_section = md[secondary_idx:]
    assert "Aristotle" in primary_section
    assert "Bobzien" in secondary_section


def test_markdown_supports_mla_style(sample_draft: ThesisDraft) -> None:
    md = ThesisRenderer().to_markdown(sample_draft, citation_style="mla")
    assert "Edited by Bywater 1894" in md or "Bywater 1894" in md


def test_markdown_supports_harvard_style(sample_draft: ThesisDraft) -> None:
    md = ThesisRenderer().to_markdown(sample_draft, citation_style="harvard")
    assert "Nicomachean Ethics" in md


# ---------------------------------------------------------------------------
# LaTeX rendering
# ---------------------------------------------------------------------------


def test_latex_wraps_greek(sample_draft: ThesisDraft) -> None:
    tex = ThesisRenderer().to_latex(sample_draft)
    assert "\\documentclass" in tex
    assert "\\section{Introduction}" in tex
    assert "\\textgreek{" in tex
    # The verbatim Greek must appear inside the wrap.
    assert re.search(r"\\textgreek\{[^}]*δοκεῖ", tex)
    assert "\\footnote{" in tex


def test_latex_escapes_specials() -> None:
    draft = ThesisDraft(
        title="A & B",
        sections=[
            Section(
                heading="Intro 50%",
                paragraphs=[Paragraph(text="cost is $5", footnote_refs=[1])],
            )
        ],
        footnotes=[
            Footnote(
                n=1,
                text="note",
                citations=[Citation(passage_id="p", work_label="W")],
            )
        ],
        bibliography=[BibliographyEntry(kind="primary", author="X", title="Y")],
    )
    tex = ThesisRenderer().to_latex(draft)
    assert "A \\& B" in tex
    assert "50\\%" in tex
    assert "\\$5" in tex


# ---------------------------------------------------------------------------
# BibTeX
# ---------------------------------------------------------------------------


def test_bibtex_has_ascii_keys(sample_draft: ThesisDraft) -> None:
    bib = ThesisRenderer().to_bibtex(sample_draft)
    assert "@book{aristotle-nicomachean-ethics-1894" in bib
    assert (
        "@article{susanne-bobzien-determinism-and-freedom-in-stoic-1998" in bib
    )  # truncated title slug
    # ASCII-only keys
    assert all(
        ord(c) < 128 for line in bib.splitlines() if line.startswith("@") for c in line
    )


def test_bibtex_roundtrip_preserves_metadata(sample_draft: ThesisDraft) -> None:
    bib = ThesisRenderer().to_bibtex(sample_draft)
    # Parse with a tiny ad-hoc reader (BibTeX deps too heavy for unit test).
    entries: dict[str, dict[str, str]] = {}
    current_key: str | None = None
    for line in bib.splitlines():
        line = line.strip().rstrip(",")
        if line.startswith("@"):
            current_key = line.split("{", 1)[1]
            entries[current_key] = {}
        elif "=" in line and current_key is not None:
            field, value = line.split("=", 1)
            value = value.strip().lstrip("{").rstrip("}")
            entries[current_key][field.strip()] = value
    # Aristotle entry retains author / year.
    aristotle = next(v for k, v in entries.items() if k.startswith("aristotle"))
    assert aristotle["author"] == "Aristotle"
    assert aristotle["year"] == "1894"
    assert "CTS:" in aristotle["note"]


# ---------------------------------------------------------------------------
# Zotero / RIS
# ---------------------------------------------------------------------------


def test_zotero_json_shape(sample_draft: ThesisDraft) -> None:
    zot = ThesisRenderer().to_zotero_json(sample_draft)
    assert "items" in zot
    assert len(zot["items"]) == 2
    book = next(i for i in zot["items"] if i["itemType"] == "book")
    assert book["title"] == "Nicomachean Ethics"
    creators = book["creators"]
    assert creators[0]["creatorType"] == "author"
    article = next(i for i in zot["items"] if i["itemType"] == "journalArticle")
    assert "Bobzien" in json.dumps(article["creators"])


def test_ris_export(sample_draft: ThesisDraft) -> None:
    ris = ThesisRenderer().to_ris(sample_draft)
    assert "TY  - BOOK" in ris
    assert "TY  - JOUR" in ris
    assert "AU  - Aristotle" in ris
    assert "ER  -" in ris


# ---------------------------------------------------------------------------
# Format dispatcher
# ---------------------------------------------------------------------------


def test_export_dispatcher_supports_all_formats(sample_draft: ThesisDraft) -> None:
    for fmt in ("markdown", "latex", "bibtex", "ris", "zotero", "json"):
        body, media_type = export_draft(sample_draft, fmt)  # type: ignore[arg-type]
        assert body
        assert media_type


def test_export_dispatcher_rejects_unknown_format(sample_draft: ThesisDraft) -> None:
    with pytest.raises(ValueError):
        export_draft(sample_draft, "pdf")  # type: ignore[arg-type]
