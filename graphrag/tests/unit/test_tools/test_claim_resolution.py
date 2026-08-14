"""Fallback claim/holder rendering in build_controversy_frame.

The incident: when a position node carried no ``stance``/``claim``/``thesis``
metadata, ``_resolve_claim`` dumped the raw KG ``description`` verbatim into the
rendered answer — including French curator boilerplate ("Avertissement
méthodologique…"), ``[Vérif. …]`` tags and ``*(Phase N)*`` annotations.
"""

from __future__ import annotations

from eleutheria_graphrag.agents.tools.build_controversy_frame import (
    BuildControversyFrameTool,
    _first_substantive_sentence,
)

_BOILERPLATE = (
    "**Avertissement méthodologique** — Ce nœud a été enrichi lors de la "
    "campagne de curation ; les attributions restent à confirmer.\n\n"
    "Alexander of Aphrodisias argues that the Stoic account of fate destroys "
    "the up-to-us. *(Phase 12)* [Vérif. Bobzien 1998, p. 375]"
)


class TestFirstSubstantiveSentence:
    def test_skips_leading_bold_boilerplate_paragraph(self):
        result = _first_substantive_sentence(_BOILERPLATE)
        assert "Avertissement méthodologique" not in result
        assert result.startswith("Alexander of Aphrodisias argues")

    def test_strips_curator_annotations(self):
        result = _first_substantive_sentence(_BOILERPLATE)
        assert "(Phase 12)" not in result
        assert "Vérif." not in result
        assert "[" not in result

    def test_caps_length(self):
        result = _first_substantive_sentence("word " * 400)
        assert len(result) <= 301

    def test_keeps_the_first_sentence_only(self):
        text = (
            "The Stoic account of fate is compatible with what is up to us. "
            "A second sentence that should not appear."
        )
        result = _first_substantive_sentence(text)
        assert result == (
            "The Stoic account of fate is compatible with what is up to us."
        )

    def test_returns_empty_for_empty_input(self):
        assert _first_substantive_sentence("") == ""
        assert _first_substantive_sentence("   ") == ""

    def test_falls_back_to_the_body_when_every_paragraph_is_bold_led(self):
        text = "**Note** — the position holds that fate is not necessity."
        result = _first_substantive_sentence(text)
        assert "**" not in result
        assert "fate is not necessity" in result


class TestResolveClaim:
    resolve = staticmethod(BuildControversyFrameTool._resolve_claim)

    def test_prefers_stance_metadata(self):
        node = {"description": _BOILERPLATE, "label": "L"}
        claim = self.resolve(node, {"stance": "Fate does not destroy the up-to-us."})
        assert claim == "Fate does not destroy the up-to-us."

    def test_prefers_conclusion_text_over_description(self):
        """The argument's own upshot beats the curated description."""
        node = {"description": _BOILERPLATE, "label": "L"}
        claim = self.resolve(
            node, {"conclusion": {"text": "Therefore fate is not necessity."}}
        )
        assert claim == "Therefore fate is not necessity."

    def test_accepts_a_bare_string_conclusion(self):
        node = {"description": _BOILERPLATE, "label": "L"}
        claim = self.resolve(node, {"conclusion": "Therefore fate is not necessity."})
        assert claim == "Therefore fate is not necessity."

    def test_description_fallback_is_cleaned_not_dumped(self):
        """THE regression: the raw description used to ship verbatim."""
        node = {"description": _BOILERPLATE, "label": "Alexander on fate"}
        claim = self.resolve(node, {})
        assert "Avertissement méthodologique" not in claim
        assert "(Phase 12)" not in claim
        assert "Vérif." not in claim
        assert claim.startswith("Alexander of Aphrodisias argues")
        assert len(claim) <= 301

    def test_falls_back_to_the_label_when_description_is_unusable(self):
        node = {"description": "   ", "label": "Alexander on fate"}
        assert self.resolve(node, {}) == "Alexander on fate"

    def test_returns_empty_when_nothing_is_available(self):
        assert self.resolve({}, {}) == ""
