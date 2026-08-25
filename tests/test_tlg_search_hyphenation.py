"""The TLG index must not be broken by a line-break hyphen.

TLG beta-code files break words across lines with a hyphen followed by a
citation byte:

    A)N-\\x80QRW/PWN      ->  ἀνθρώπων
    PLHMME-\\x80LH/SWSI   ->  πλημμελήσωσι

The normaliser used to turn that hyphen into a word break, so a needle
spanning it returned ZERO hits on a word that is plainly in the file.

That is not a cosmetic bug. `tlg_search.py` is the tool this project uses to
decide whether a Greek string is attested — i.e. whether a node fabricated it.
A false negative there invites someone to "correct" an authentic reading out of
the corpus, which is the exact failure the Ancient Text Authenticity Policy
exists to prevent. Two nodes were nearly misjudged this way during the
2026-08-26 audit.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "tlg_search", ROOT / "scripts" / "tlg_search.py"
)
assert SPEC and SPEC.loader
tlg_search = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(tlg_search)

normalize = tlg_search.normalize_txt_bytes
needle = tlg_search.needle_to_beta_base


def norm(raw: bytes) -> str:
    return normalize(raw)[0]


def test_line_break_hyphen_rejoins_the_word() -> None:
    # Verbatim byte shape from TLG0645.TXT @130686 (Justin, 2 Apol.).
    assert "anqrwpwn" in norm(b"KAI\\ TW=N A)N-\x80QRW/PWN TH\\N")


def test_line_break_hyphen_with_newline_rejoins_the_word() -> None:
    assert "plhmmelhswsi" in norm(b"A)\\N PLHMME-\r\n\x81LH/SWSI TH\\N")


def test_a_real_word_boundary_is_still_a_boundary() -> None:
    parts = norm(b"TW=N A)GGE/LWN GE/NOS").split()
    assert parts == ["twn", "aggelwn", "genos"]


def test_in_word_diacritics_are_still_dropped_not_split() -> None:
    assert norm(b"AU)TECOU/SION").strip() == "autecousion"


def test_the_needle_and_the_index_agree_across_a_break() -> None:
    # This pairing is the actual contract: whatever the needle reduces to must
    # be findable in whatever the file reduces to.
    haystack = norm(b"DIKAI/WS U(PE\\R W(=N A)\\N PLHMME-\x80LH/SWSI TH\\N TIMWRI/AN")
    assert needle("ὑπὲρ ὧν ἂν πλημμελήσωσι τὴν τιμωρίαν") in haystack


def test_offset_map_stays_aligned_with_the_output() -> None:
    text, offsets = normalize(b"KAI\\ TW=N A)N-\x80QRW/PWN")
    assert len(text) == len(offsets)
    assert offsets == sorted(offsets)


def test_a_trailing_hyphen_with_no_following_letter_is_a_boundary() -> None:
    # Nothing to rejoin to: it must not swallow the end of the buffer.
    assert norm(b"GE/NOS-").strip() == "genos"
