from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts import kg_extend_verbatim_quotes as vq

LIT = "04_Littérature_secondaire"


def _sentence(tag: str, n: int) -> str:
    words = [f"{tag}{n}w{k}" for k in range(1, 12)]
    words[0] = words[0].capitalize()
    return " ".join(words) + "."


def _para(tag: str, sentences: int, indent: str = "") -> list[str]:
    """One paragraph of ``sentences`` sentences, wrapped two per line."""
    lines: list[str] = []
    for n in range(0, sentences, 2):
        chunk = " ".join(_sentence(tag, m) for m in range(n, min(n + 2, sentences)))
        lines.append((indent if not lines else "") + chunk)
    return lines


FRONT = [
    "---",
    "source_pdf: fixture.pdf",
    "extraction_method: native",
    "---",
    "",
    "# Fixture",
]


def _doc_lines() -> list[str]:
    lines = list(FRONT)
    # page 1 (printed 10): heading, two paragraphs, a footnote block
    lines += ["\x0c                 RUNNING HEAD                 10", ""]
    lines += ["2.1 A Numbered Heading", ""]
    lines += _para("alpha", 6)
    lines += _para("beta", 6, indent="   ")
    lines += ["1 First footnote text on page ten.", "2 Second footnote text here."]
    # page 2 (printed 11): a paragraph continued, blank-separated paragraph
    lines += ["\x0c                 RUNNING HEAD                 11", ""]
    lines += _para("gamma", 6)
    lines += [""]
    lines += _para("delta", 6)
    lines += ["3 Third footnote on page eleven."]
    # page 3 (printed 12): heading then paragraph
    lines += ["\x0c                 RUNNING HEAD                 12", ""]
    lines += ["3. ANOTHER HEADING", ""]
    lines += _para("epsilon", 6)
    lines += [""]
    lines += _para("zeta", 6)
    # page 4 (printed 13)
    lines += ["\x0c                 RUNNING HEAD                 13", ""]
    lines += _para("eta", 6)
    return lines


def _find(doc: vq.SourceDoc, token: str) -> int:
    for i, line in enumerate(doc.lines):
        if token in line:
            return i
    raise AssertionError(token)


def test_word_count_and_sentence_truncation() -> None:
    text = " ".join(_sentence("s", n) for n in range(60))
    assert vq.word_count(text) == 60 * 11
    cut = vq.truncate_at_sentence(text, 500)
    assert vq.word_count(cut) <= 500
    assert cut.endswith(".")
    assert vq.word_count(cut) == 495  # 45 whole sentences of 11 words


def test_join_lines_hyphenation_respects_attested_compounds() -> None:
    lines = ["the con-", "trast is with two-", "ways thinking"]
    assert vq.join_lines(lines) == "the contrast is with twoways thinking"
    assert (
        vq.join_lines(lines, {"two-ways"}) == "the contrast is with two-ways thinking"
    )


def test_units_paragraphs_headings_and_notes() -> None:
    doc = vq.analyse(_doc_lines())
    kinds = [(u.kind, u.text.split()[0]) for u in doc.units]
    assert ("heading", "2.1") in kinds
    assert ("heading", "3.") in kinds
    paragraphs = [u.text.split()[0] for u in doc.units if u.kind == "paragraph"]
    # indentation, blank lines and page breaks each open a new paragraph
    assert paragraphs == [
        "Alpha0w1",
        "Beta0w1",
        "Gamma0w1",
        "Delta0w1",
        "Epsilon0w1",
        "Zeta0w1",
        "Eta0w1",
    ]
    notes = [u.text for u in doc.units if u.kind == "note"]
    assert notes == [
        "1 First footnote text on page ten.",
        "2 Second footnote text here.",
        "3 Third footnote on page eleven.",
    ]
    head_line = _find(doc, "RUNNING HEAD                 11")
    assert doc.kind_of_line[head_line] == "ff"
    assert doc.page_numbers == {1: 10, 2: 11, 3: 12, 4: 13}


def test_expand_never_includes_footnotes_or_running_heads() -> None:
    doc = vq.analyse(_doc_lines())
    anchor = _find(doc, "Beta2w1")
    extract = vq.expand(doc, [(anchor, anchor)])
    assert extract is not None
    assert "footnote" not in extract.text
    assert "RUNNING HEAD" not in extract.text
    assert "Beta2w1" in extract.text and "Alpha0w1" in extract.text


def test_expand_stops_at_heading() -> None:
    doc = vq.analyse(_doc_lines())
    anchor = _find(doc, "Epsilon1w1")
    extract = vq.expand(doc, [(anchor, anchor)])
    assert extract is not None
    assert "Epsilon0w1" in extract.text and "Zeta0w1" in extract.text
    # the heading "3. ANOTHER HEADING" separates delta (page 2) from epsilon
    assert "delta" not in extract.text and "ANOTHER HEADING" not in extract.text


def test_expand_stays_within_one_page_of_anchor() -> None:
    doc = vq.analyse(_doc_lines())
    anchor = _find(doc, "Alpha1w1")
    extract = vq.expand(doc, [(anchor, anchor)], limit=5000)
    assert extract is not None
    assert "gamma" in extract.text  # page 2 is within the window
    assert "epsilon" not in extract.text  # page 3 is not


def test_footnote_anchor_returns_the_note() -> None:
    doc = vq.analyse(_doc_lines())
    anchor = _find(doc, "Second footnote")
    extract = vq.expand(doc, [(anchor, anchor)])
    assert extract is not None
    assert extract.anchor_kind == "note"
    assert extract.text == "2 Second footnote text here."


def test_cap_at_sentence_boundary_keeps_anchor_sentence() -> None:
    lines = list(FRONT) + ["\x0c   HEAD   1", ""] + _para("long", 60)
    doc = vq.analyse(lines)
    anchor = _find(doc, "Long40w1")
    extract = vq.expand(doc, [(anchor, anchor)])
    assert extract is not None
    assert extract.truncated
    assert extract.words <= vq.MAX_WORDS
    assert extract.text.endswith(".")
    assert "Long40w1" in extract.text


def test_locate_quote_tolerates_hyphenation_and_quotes() -> None:
    lines = list(FRONT) + [
        "\x0c   HEAD   1",
        "",
        "In the end, as the previous chapter showed, the whole argument turns on self-",
        "determination and “freedom” of the agent, and on nothing else in the world.",
    ]
    doc = vq.analyse(lines)
    quote = 'argument turns on self-determination and "freedom" of the agent'
    found = vq.locate_quote(doc, quote, None)
    assert found is not None
    first, last, method = found
    assert "self-" in doc.lines[first] and "determination" in doc.lines[last]
    assert method == "full_quote"


def test_citation_regex_accepts_brackets_in_file_names() -> None:
    parsed = vq.parse_citation(
        "[04_Apologistes_Justin/[Théologie historique 82] Pouderon - A.md:12-14] (p. 3)"
    )
    assert parsed == (
        "04_Apologistes_Justin/[Théologie historique 82] Pouderon - A.md",
        (12, 14),
    )


@pytest.fixture
def fixture_fonds(tmp_path: Path) -> tuple[vq.Fonds, str]:
    page_map_io = vq.load_page_map_io(vq.DEFAULT_THESIS_ROOT)
    if page_map_io is None:
        pytest.skip("thesis page_map_io.py not available on this machine")
    lit = tmp_path / LIT
    (lit / "01_Test").mkdir(parents=True)
    rel = "01_Test/Fixture_2020.md"
    lines = _doc_lines()
    (lit / rel).write_text("\n".join(lines), encoding="utf-8")
    ff = [i + 1 for i, line in enumerate(lines) if line.startswith("\x0c")]
    pages = [
        {
            "page": n + 1,
            "pdf_page": n + 1,
            "citation_page": 10 + n,
            "citation_method": "page_labels",
            "citation_confidence": 0.98,
            "start_line": start,
            "confidence": 0.99,
            "method": "formfeed",
        }
        for n, start in enumerate(ff)
    ]
    (lit / "page_map.json").write_text(
        json.dumps({"meta": {}, "files": {rel: {"pages": pages}}}), encoding="utf-8"
    )
    (lit / "page_map_audit.json").write_text(
        json.dumps({"files": {rel: {"status": "passed"}}}), encoding="utf-8"
    )
    return vq.Fonds(tmp_path, page_map_io), rel


def test_page_computation_uses_page_map_io(fixture_fonds: tuple[vq.Fonds, str]) -> None:
    fonds, rel = fixture_fonds
    doc = fonds.doc(rel)
    anchor = _find(doc, "Gamma1w1")
    info = fonds.page_for_line(rel, anchor + 1)
    assert info.printed == 11
    assert info.physical == 2
    assert info.method == "page_map+running_head"
    assert vq.format_pages(10, 11) == "pp. 10-11"
    assert vq.format_pages("xi", "xi") == "p. xi"


def test_running_head_used_when_page_map_audit_failed(
    fixture_fonds: tuple[vq.Fonds, str],
) -> None:
    fonds, rel = fixture_fonds
    fonds.page_map_audit[rel]["status"] = "failed"
    doc = fonds.doc(rel)
    anchor = _find(doc, "Epsilon1w1")
    info = fonds.page_for_line(rel, anchor + 1)
    assert info.printed == 12
    assert info.method == "running_head"


def test_process_node_and_manifest_rows(fixture_fonds: tuple[vq.Fonds, str]) -> None:
    fonds, rel = fixture_fonds
    doc = fonds.doc(rel)
    anchor = _find(doc, "Beta1w1")
    node = {
        "id": "scholarly_argument_fixture_0",
        "metadata": {
            "scholarly_work_id": "pub_fixture_2020",
            "quote_verbatim": "old short quote",
            "scholarly_audit": {
                "wave": 9,
                "evidence": [
                    {
                        "quote": "Beta1w1 beta1w2 beta1w3 beta1w4 beta1w5 beta1w6",
                        "citation": f"[{rel}:{anchor + 1}] (Fixture 2020, p. 10)",
                    }
                ],
            },
        },
    }
    result = vq.process_node(node, fonds, {})
    assert result.status == "extended", result.reason
    fields = result.fields
    assert fields["quote_words"] <= vq.MAX_WORDS
    assert fields["quote_pages"] == "pp. 10-11"
    assert fields["quote_lines"].startswith("L")
    assert fields["quote_verbatim_previous"] == "old short quote"
    assert fields["quote_source_file"] == rel
    assert len(fields["quote_source_sha256"]) == 64
    assert "footnote" not in fields["quote_verbatim"]

    manifest = vq.build_manifest(
        [result],
        fonds,
        reviewed_by="tester",
        reviewed_at="2026-08-29T00:00:00+00:00",
        text_sha=lambda text: "0" * 64,
    )
    assert len(manifest["artifacts"]) == 1
    artifact = manifest["artifacts"][0]
    assert artifact["publication_id"] == "pub_fixture_2020"
    assert artifact["review_status"] == vq.REVIEWED == "reviewed"
    physical = [page["physical_page"] for page in artifact["pages"]]
    assert physical == sorted(set(physical)) == [1, 2]
    assert [page["printed_page"] for page in artifact["pages"]] == ["10", "11"]
    assert all(
        vq.word_count(page["text_content"]) <= vq.MAX_WORDS
        for page in artifact["pages"]
    )
    assert manifest["extracts"][0]["node_id"] == "scholarly_argument_fixture_0"
