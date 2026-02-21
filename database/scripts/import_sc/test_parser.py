"""Tests for the SC source file parser."""

from __future__ import annotations

import textwrap

import pytest

from .parser import (
    _clean_text,
    _extract_section_title,
    _group_into_chapters,
    _parse_header,
    _parse_reference,
    _split_blocks,
    _split_header_body,
)
from .models import SCParagraph


# ---------------------------------------------------------------------------
# Header parsing
# ---------------------------------------------------------------------------


class TestParseHeader:
    def test_standard_header_with_sc_prefix(self):
        header = textwrap.dedent("""\
            SC 132
            AUTEUR: Origenes
            OEUVRE: Contre Celse, Livre I
            TITRE ORIGINAL: Contra Celsum, Liber I
            LIVRE 1
            PARAGRAPHES: 88
            DATE: 23.01.2026 01:58:52
        """)
        fields = _parse_header(header)
        assert fields["sc_number"] == "132"
        assert fields["auteur"] == "Origenes"
        assert fields["oeuvre"] == "Contre Celse, Livre I"
        assert fields["titre_original"] == "Contra Celsum, Liber I"
        assert fields["livre"] == "1"
        assert fields["paragraphes"] == "88"

    def test_header_without_sc_prefix(self):
        header = textwrap.dedent("""\
            AUTEUR: Iustinus martyr
            OEUVRE: Apologie
            TITRE ORIGINAL: Apologia
            LIVRE 1
            PARAGRAPHES: 108
            DATE: 23.01.2026 00:46:13
        """)
        fields = _parse_header(header)
        assert "sc_number" not in fields
        assert fields["auteur"] == "Iustinus martyr"
        assert fields["paragraphes"] == "108"

    def test_header_with_traducteur(self):
        header = textwrap.dedent("""\
            SC 464
            AUTEUR: Pamphilus Caesariensis
            OEUVRE: Apologie pour Origène
            TRADUCTEUR: Rufinus Aquileiensis
            LIVRE 1
            PARAGRAPHES: 265
        """)
        fields = _parse_header(header)
        assert fields["traducteur"] == "Rufinus Aquileiensis"

    def test_sc_number_bis(self):
        header = "SC 10bis\nAUTEUR: Ignatius\n"
        fields = _parse_header(header)
        assert fields["sc_number"] == "10bis"


# ---------------------------------------------------------------------------
# Header/body splitting
# ---------------------------------------------------------------------------


class TestSplitHeaderBody:
    def test_splits_at_first_ref(self):
        content = "AUTEUR: Test\nOEUVRE: Work\n\n[par.: 1]\n\nSome text\n"
        header, body = _split_header_body(content)
        assert "AUTEUR: Test" in header
        assert body.startswith("[par.: 1]")

    def test_splits_at_named_ref(self):
        content = "AUTEUR: Test\n\n[salutation]\n\nText here\n"
        header, body = _split_header_body(content)
        assert "AUTEUR: Test" in header
        assert body.startswith("[salutation]")


# ---------------------------------------------------------------------------
# Block splitting
# ---------------------------------------------------------------------------


class TestSplitBlocks:
    def test_standard_blocks(self):
        body = (
            "[par.: 1]\n\nText one\n\n"
            "==================================================\n\n"
            "[par.: 2]\n\nText two\n\n"
            "==================================================\n"
        )
        blocks = _split_blocks(body)
        assert len(blocks) == 2
        assert "[par.: 1]" in blocks[0]
        assert "[par.: 2]" in blocks[1]

    def test_empty_blocks_filtered(self):
        body = (
            "[par.: 1]\n\nText\n\n"
            "==================================================\n\n"
            "==================================================\n"
        )
        blocks = _split_blocks(body)
        assert len(blocks) == 1


# ---------------------------------------------------------------------------
# Reference parsing
# ---------------------------------------------------------------------------


class TestParseReference:
    # Format A
    def test_format_a_paragraph(self):
        assert _parse_reference("par.: 1", "A") == (None, "1")

    def test_format_a_high_number(self):
        assert _parse_reference("par.: 88", "A") == (None, "88")

    # Format B
    def test_format_b_full(self):
        assert _parse_reference("liv.: 3, chap.: 1, par.: 2", "B") == ("1", "2")

    def test_format_b_extracts_chapter_only(self):
        ch, par = _parse_reference("liv.: 4, chap.: 3, par.: 1", "B")
        assert ch == "3"
        assert par == "1"

    # Format C
    def test_format_c_justin(self):
        ch, par = _parse_reference("première apologie, chap.: 4", "C")
        assert ch == "4"
        assert par is None

    def test_format_c_high_chapter(self):
        ch, par = _parse_reference("première apologie, chap.: 68", "C")
        assert ch == "68"

    def test_format_c_deuxieme_apologie(self):
        """Deuxième apologie chapters get II. prefix to avoid collisions."""
        ch, par = _parse_reference("deuxième apologie, chap.: 1", "C")
        assert ch == "II.1"
        assert par is None

    def test_format_c_deuxieme_high_chapter(self):
        ch, par = _parse_reference("deuxième apologie, chap.: 15", "C")
        assert ch == "II.15"

    # Format D variants
    def test_format_d_chap_par(self):
        assert _parse_reference("chap.: 4, par.: 2-3", "D") == ("4", "2-3")

    def test_format_d_chap_par_single(self):
        assert _parse_reference("chap.: 1, par.: 3", "D") == ("1", "3")

    def test_format_d_chap_only(self):
        assert _parse_reference("chap.: 5", "D") == ("5", None)

    def test_format_d_salutation(self):
        ch, par = _parse_reference("salutation", "D")
        assert ch == "salutation"
        assert par is None

    def test_format_d_dedication(self):
        ch, par = _parse_reference("dédication", "D")
        assert ch == "dédication"
        assert par is None

    def test_format_d_no_format(self):
        assert _parse_reference("no: 42", "D") == (None, "42")

    def test_format_d_no_range(self):
        assert _parse_reference("no: 78-79", "D") == (None, "78-79")

    def test_format_d_page(self):
        assert _parse_reference("page: 5", "D") == (None, "5")

    def test_format_d_page_range(self):
        assert _parse_reference("page: 10-11", "D") == (None, "10-11")

    def test_format_d_cap_aristides(self):
        ref = "I. Roman de Barlaam, A. discours, cap.: 1, par.: 1-2"
        ch, par = _parse_reference(ref, "D")
        assert ch == "1"
        assert par == "1-2"

    def test_format_d_introduction_par(self):
        ch, par = _parse_reference("introduction, par.: 1-3", "D")
        assert ch == "introduction"
        assert par == "1-3"

    def test_format_d_chap_with_desc_par(self):
        ref = "chap.: 1 (il faut dire la cause), par.: 1-2"
        ch, par = _parse_reference(ref, "D")
        assert ch == "1"
        assert par == "1-2"

    def test_format_d_par_only(self):
        """[par.: N] in Format D context (e.g., Pamphile)."""
        assert _parse_reference("par.: 1", "D") == (None, "1")

    def test_format_d_par_high_number(self):
        assert _parse_reference("par.: 188", "D") == (None, "188")


# ---------------------------------------------------------------------------
# Text cleaning
# ---------------------------------------------------------------------------


class TestCleanText:
    def test_remove_page_markers(self):
        text = "Some text --- 126 ---more text"
        cleaned = _clean_text(text, "A")
        assert "--- 126 ---" not in cleaned
        assert "Some text" in cleaned
        assert "more text" in cleaned

    def test_remove_section_titles(self):
        text = "### ΤΟΜΟΣ ΠΡΩΤΟΣ ###\n\nActual text here"
        cleaned = _clean_text(text, "A")
        assert "ΤΟΜΟΣ" not in cleaned
        assert "Actual text here" in cleaned

    def test_strip_traduction(self):
        text = (
            "--- SOURCE ---\nGreek text here\n\n"
            "--- TRADUCTION ---\nFrench translation\n"
        )
        cleaned = _clean_text(text, "B")
        assert "Greek text here" in cleaned
        assert "French translation" not in cleaned
        assert "--- SOURCE ---" not in cleaned

    def test_remove_source_marker(self):
        text = "--- SOURCE ---\nGreek text"
        cleaned = _clean_text(text, "B")
        assert "--- SOURCE ---" not in cleaned
        assert "Greek text" in cleaned

    def test_rejoin_hyphenation(self):
        text = "τοσοῦ-\nτον μέντοι"
        cleaned = _clean_text(text, "A")
        assert "τοσοῦτον μέντοι" in cleaned

    def test_normalize_whitespace(self):
        text = "First\n\n\n\n\nSecond"
        cleaned = _clean_text(text, "A")
        assert "\n\n\n" not in cleaned
        assert "First\n\nSecond" in cleaned

    def test_preserve_greek_diacritics(self):
        text = "Ἐπεὶ δὲ ἐν τῷ κηρύγματι"
        cleaned = _clean_text(text, "A")
        assert cleaned == text

    def test_preserve_inline_page_markers_gone(self):
        text = "--- 78 ---1. [Πρῶτον τῷ Κέλσῳ] text --- 80 ---more"
        cleaned = _clean_text(text, "A")
        assert "--- 78 ---" not in cleaned
        assert "--- 80 ---" not in cleaned
        assert "Πρῶτον" in cleaned


class TestExtractSectionTitle:
    def test_single_title(self):
        text = "### ΤΟΜΟΣ ΠΡΩΤΟΣ ###\nText"
        title = _extract_section_title(text)
        assert title == "ΤΟΜΟΣ ΠΡΩΤΟΣ"

    def test_multiple_titles(self):
        text = "### PART ONE ###\n### CHAPTER ###\nText"
        title = _extract_section_title(text)
        assert "PART ONE" in title
        assert "CHAPTER" in title

    def test_no_title(self):
        text = "Just regular text"
        assert _extract_section_title(text) is None


# ---------------------------------------------------------------------------
# Chapter grouping
# ---------------------------------------------------------------------------


class TestGroupIntoChapters:
    def test_format_a_each_para_own_chapter(self):
        paras = [
            SCParagraph(raw_ref="[par.: 1]", chapter=None, paragraph="1", text="t1", sequence=0),
            SCParagraph(raw_ref="[par.: 2]", chapter=None, paragraph="2", text="t2", sequence=1),
        ]
        chapters = _group_into_chapters(paras, "A")
        assert len(chapters) == 2
        assert chapters[0].chapter_ref == "1"
        assert chapters[1].chapter_ref == "2"

    def test_format_d_group_by_chapter(self):
        paras = [
            SCParagraph(raw_ref="[chap.: 1, par.: 1]", chapter="1", paragraph="1", text="t1", sequence=0),
            SCParagraph(raw_ref="[chap.: 1, par.: 2]", chapter="1", paragraph="2", text="t2", sequence=1),
            SCParagraph(raw_ref="[chap.: 2]", chapter="2", paragraph=None, text="t3", sequence=2),
        ]
        chapters = _group_into_chapters(paras, "D")
        assert len(chapters) == 2
        assert chapters[0].chapter_ref == "1"
        assert chapters[0].paragraph_count == 2
        assert chapters[1].chapter_ref == "2"

    def test_format_d_named_section_own_chapter(self):
        paras = [
            SCParagraph(raw_ref="[salutation]", chapter="salutation", paragraph=None, text="t1", sequence=0),
            SCParagraph(raw_ref="[chap.: 1, par.: 1]", chapter="1", paragraph="1", text="t2", sequence=1),
        ]
        chapters = _group_into_chapters(paras, "D")
        assert len(chapters) == 2
        assert chapters[0].chapter_ref == "salutation"

    def test_no_chapter_each_own_group(self):
        """When chapter is None (e.g., [no: N]), each para gets its own chapter."""
        paras = [
            SCParagraph(raw_ref="[no: 1]", chapter=None, paragraph="1", text="t1", sequence=0),
            SCParagraph(raw_ref="[no: 2]", chapter=None, paragraph="2", text="t2", sequence=1),
        ]
        chapters = _group_into_chapters(paras, "D")
        assert len(chapters) == 2
        assert chapters[0].chapter_ref == "1"
        assert chapters[1].chapter_ref == "2"
