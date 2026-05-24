"""Tests for scripts/corpus_github_fetch.py — TDD: written before implementation."""
from __future__ import annotations

import textwrap

import pytest

from scripts.corpus_github_fetch import github_xml_urls, parse_passages

# ---------------------------------------------------------------------------
# github_xml_urls
# ---------------------------------------------------------------------------

PERSEUS_GREEK = "https://raw.githubusercontent.com/PerseusDL/canonical-greekLit/master/data"
FIRST1K_GREEK = "https://raw.githubusercontent.com/OpenGreekAndLatin/First1KGreek/master/data"
PERSEUS_LATIN = "https://raw.githubusercontent.com/PerseusDL/canonical-latinLit/master/data"


def test_greek_perseus_version_first_url():
    urn = "urn:cts:greekLit:tlg0004.tlg001.perseus-grc2"
    urls = github_xml_urls(urn)
    assert urls[0] == (
        f"{PERSEUS_GREEK}/tlg0004/tlg001/tlg0004.tlg001.perseus-grc2.xml"
    )


def test_greek_perseus_version_has_fallback_to_first1k():
    urn = "urn:cts:greekLit:tlg0004.tlg001.perseus-grc2"
    urls = github_xml_urls(urn)
    assert len(urls) == 2
    assert urls[1] == (
        f"{FIRST1K_GREEK}/tlg0004/tlg001/tlg0004.tlg001.perseus-grc2.xml"
    )


def test_greek_first1k_version_routes_first1k_first():
    urn = "urn:cts:greekLit:tlg2022.tlg001.1st1kgreek-grc1"
    urls = github_xml_urls(urn)
    assert urls[0] == (
        f"{FIRST1K_GREEK}/tlg2022/tlg001/tlg2022.tlg001.1st1kgreek-grc1.xml"
    )
    # fallback to canonical-greekLit
    assert urls[1] == (
        f"{PERSEUS_GREEK}/tlg2022/tlg001/tlg2022.tlg001.1st1kgreek-grc1.xml"
    )


def test_latin_routes_to_canonical_latinlit():
    urn = "urn:cts:latinLit:phi1017.phi015.perseus-lat2"
    urls = github_xml_urls(urn)
    assert len(urls) == 1
    assert urls[0] == (
        f"{PERSEUS_LATIN}/phi1017/phi015/phi1017.phi015.perseus-lat2.xml"
    )


# ---------------------------------------------------------------------------
# parse_passages — inline TEI fixture
# ---------------------------------------------------------------------------

TEI_FIXTURE = textwrap.dedent("""\
    <?xml version="1.0" encoding="UTF-8"?>
    <TEI xmlns="http://www.tei-c.org/ns/1.0">
      <teiHeader>
        <encodingDesc>
          <refsDecl n="CTS">
            <cRefPattern n="section"
              matchPattern="(\\w+).(\\w+)"
              replacementPattern="#xpath(/TEI/text/body/div/div[@n='$1']/div[@n='$2'])">
              <p>This pointer pattern extracts section.</p>
            </cRefPattern>
            <cRefPattern n="chapter"
              matchPattern="(\\w+)"
              replacementPattern="#xpath(/TEI/text/body/div/div[@n='$1'])">
              <p>This pointer pattern extracts chapter.</p>
            </cRefPattern>
          </refsDecl>
        </encodingDesc>
      </teiHeader>
      <text>
        <body>
          <div type="edition" n="work">
            <div type="textpart" subtype="chapter" n="1">
              <div type="textpart" subtype="section" n="1">
                Τί δέ ἐστιν ἐλευθερία;
                <note>editorial note to strip</note>
              </div>
              <div type="textpart" subtype="section" n="2">
                Ἀρχὴ παιδεύσεως ἡ τῶν ὀνομάτων ἐπίσκεψις.
              </div>
            </div>
            <div type="textpart" subtype="chapter" n="2">
              <div type="textpart" subtype="section" n="1">
                Ὁ Ζεὺς οὐκ ἦν δυνατὸς ἐλευθεροῦν αὐτόν.
                <bibl>ref to strip</bibl>
              </div>
            </div>
          </div>
        </body>
      </text>
    </TEI>
""").encode("utf-8")


def test_parse_passages_returns_correct_refs():
    passages = parse_passages(TEI_FIXTURE, "urn:cts:greekLit:tlg0004.tlg001.perseus-grc2")
    refs = [p["cts_urn"].split(":")[-1] for p in passages]
    assert refs == ["1.1", "1.2", "2.1"]


def test_parse_passages_strips_note_content():
    passages = parse_passages(TEI_FIXTURE, "urn:cts:greekLit:tlg0004.tlg001.perseus-grc2")
    # The first passage has a <note>; its text should NOT contain "editorial note"
    assert "editorial note" not in passages[0]["text_content"]
    assert "editorial note to strip" not in passages[0]["text_content"]


def test_parse_passages_strips_bibl_content():
    passages = parse_passages(TEI_FIXTURE, "urn:cts:greekLit:tlg0004.tlg001.perseus-grc2")
    assert "ref to strip" not in passages[2]["text_content"]


def test_parse_passages_preserves_greek_text():
    passages = parse_passages(TEI_FIXTURE, "urn:cts:greekLit:tlg0004.tlg001.perseus-grc2")
    assert "Τί δέ ἐστιν ἐλευθερία" in passages[0]["text_content"]
    assert "Ἀρχὴ παιδεύσεως" in passages[1]["text_content"]


def test_parse_passages_full_cts_urn():
    passages = parse_passages(TEI_FIXTURE, "urn:cts:greekLit:tlg0004.tlg001.perseus-grc2")
    assert passages[0]["cts_urn"] == "urn:cts:greekLit:tlg0004.tlg001.perseus-grc2:1.1"


def test_parse_passages_level_override():
    # level=1 → stop at chapter depth (div n="1", n="2")
    passages = parse_passages(
        TEI_FIXTURE,
        "urn:cts:greekLit:tlg0004.tlg001.perseus-grc2",
        level=1,
    )
    refs = [p["cts_urn"].split(":")[-1] for p in passages]
    assert refs == ["1", "2"]


# ---------------------------------------------------------------------------
# Verse fixture (lines as leaf)
# ---------------------------------------------------------------------------

TEI_VERSE_FIXTURE = textwrap.dedent("""\
    <?xml version="1.0" encoding="UTF-8"?>
    <TEI xmlns="http://www.tei-c.org/ns/1.0">
      <teiHeader>
        <encodingDesc>
          <refsDecl n="CTS">
            <cRefPattern n="line"
              matchPattern="(\\w+).(\\w+)"
              replacementPattern="#xpath(/TEI/text/body/div/div[@n='$1']/l[@n='$2'])">
              <p>Extracts line.</p>
            </cRefPattern>
            <cRefPattern n="book"
              matchPattern="(\\w+)"
              replacementPattern="#xpath(/TEI/text/body/div/div[@n='$1'])">
              <p>Extracts book.</p>
            </cRefPattern>
          </refsDecl>
        </encodingDesc>
      </teiHeader>
      <text>
        <body>
          <div type="edition" n="poem">
            <div type="textpart" subtype="book" n="1">
              <l n="1">Μῆνιν ἄειδε θεά,</l>
              <l n="2">Πηληϊάδεω Ἀχιλῆος</l>
            </div>
          </div>
        </body>
      </text>
    </TEI>
""").encode("utf-8")


def test_parse_passages_verse_lines():
    passages = parse_passages(
        TEI_VERSE_FIXTURE,
        "urn:cts:greekLit:tlg0012.tlg001.perseus-grc2",
    )
    refs = [p["cts_urn"].split(":")[-1] for p in passages]
    assert refs == ["1.1", "1.2"]
    assert "Μῆνιν" in passages[0]["text_content"]
