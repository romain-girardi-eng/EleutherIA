"""Unit tests for the claim-clause extraction behind the v2 verifier."""

from __future__ import annotations

from eleutheria_graphrag.services.claim_clause import (
    extract_claim_clause,
    find_marker_groups,
    marker_tokens,
    marker_units,
    paragraph_context,
    sentence_for_citation,
)

MULTI = (
    "Nascimento reads this as an argument that distinguishes the involuntary "
    "reception of impressions from the rational judgment governing their use "
    "[P1], whereas Fürst's 2022 dissertation places the same argument within "
    "Origen's campaign against determination [P2]."
)


class TestMarkerTokens:
    def test_render_refs_and_lists(self) -> None:
        assert marker_tokens("P1") == ["P1"]
        assert marker_tokens("N3") == ["N3"]
        assert marker_tokens("2") == ["2"]
        assert marker_tokens("P3, N1") == ["P3", "N1"]
        assert marker_tokens("P1-P3") == ["P1", "P2", "P3"]

    def test_dialectical_bodies_yield_the_bare_id(self) -> None:
        assert "frede_2011" in marker_tokens("P_frede_2011: Frede 2011, p. 44")
        assert "abc-123" in marker_tokens("passage_abc-123: Origen, Princ. 3.1")

    def test_units_split_a_list_but_keep_a_body_whole(self) -> None:
        assert marker_units("P3, N1") == [("P3",), ("N1",)]
        assert marker_units("P_frede_2011: Frede 2011") == [
            ("P_frede_2011: Frede 2011", "frede_2011")
        ]

    def test_prose_and_empty(self) -> None:
        assert marker_tokens("") == []
        assert marker_tokens("   ") == []


class TestMarkerGroups:
    def test_adjacent_markers_form_one_group(self) -> None:
        groups = find_marker_groups("Claim [P1] [P2], and more [N3].")
        assert [g.tokens for g in groups] == [("P1", "P2"), ("N3",)]

    def test_comma_separated_brackets_group(self) -> None:
        groups = find_marker_groups("Claim [P1], [P2]. Other [P3]")
        assert [g.tokens for g in groups] == [("P1", "P2"), ("P3",)]

    def test_bracketed_prose_is_not_a_marker(self) -> None:
        groups = find_marker_groups("A [sic] claim [P1].")
        assert [g.tokens for g in groups] == [("P1",)]

    def test_known_key_makes_a_nonstandard_marker(self) -> None:
        assert find_marker_groups("Eliasson argues [A1].") == []
        groups = find_marker_groups("Eliasson argues [A1].", known={"A1"})
        assert [g.tokens for g in groups] == [("A1",)]


class TestExtractClaimClause:
    def test_first_proposition_of_a_multi_source_sentence(self) -> None:
        clause = extract_claim_clause(MULTI, keys={"P1"})
        assert clause.marker_found
        assert clause.clause == (
            "Nascimento reads this as an argument that distinguishes the "
            "involuntary reception of impressions from the rational judgment "
            "governing their use"
        )
        assert "Fürst" not in clause.clause
        assert clause.companion_tokens == ("P2",)
        assert clause.sentence == MULTI

    def test_second_proposition_drops_the_leading_connective_comma(self) -> None:
        clause = extract_claim_clause(MULTI, keys={"P2"})
        assert clause.clause.startswith("whereas Fürst's 2022 dissertation")
        assert "Nascimento" not in clause.clause
        assert clause.companion_tokens == ("P1",)

    def test_multi_marker_bracket_shares_the_clause(self) -> None:
        sentence = (
            "Irwin objects that this may merely identify the absence of a "
            "voluntarist theory [N2], while Frede relocates the innovation to "
            "Epictetus [P3, N1]."
        )
        for key, other in (("P3", "N1"), ("N1", "P3")):
            clause = extract_claim_clause(sentence, keys={key})
            assert clause.clause == (
                "while Frede relocates the innovation to Epictetus"
            )
            # The other reference of the same bracket is another source.
            assert clause.companion_tokens == ("N2", other)
        assert extract_claim_clause(sentence, keys={"P3", "N1"}).own_tokens == (
            "P3",
            "N1",
        )

    def test_adjacent_markers_share_the_clause(self) -> None:
        sentence = (
            "Long expressly endorses Bobzien's judgment that Epictetus is not "
            "offering a new intervention [P_long_2002: Long 2002] "
            "[P_bobzien_1998: Bobzien 1998]."
        )
        clause = extract_claim_clause(sentence, keys={"bobzien_1998"})
        assert clause.clause == (
            "Long expressly endorses Bobzien's judgment that Epictetus is not "
            "offering a new intervention"
        )
        assert "long_2002" in clause.own_tokens
        # The adjacent marker shares the clause but is another source.
        assert clause.companion_tokens == ("P_long_2002: Long 2002", "long_2002")

    def test_dialectical_passage_marker_resolves_by_id(self) -> None:
        sentence = (
            "Origen writes that the cause lies in us [passage_9f1: Origen, "
            "Princ. 3.1.3], as Chrysippus had held [passage_7c2: Cicero, Fat. 43]."
        )
        clause = extract_claim_clause(sentence, keys={"7c2"})
        assert clause.clause == "as Chrysippus had held"
        assert clause.companion_tokens == ("passage_9f1: Origen, Princ. 3.1.3", "9f1")

    def test_trailing_inference_belongs_to_no_marker(self) -> None:
        sentence = (
            "“The faculty of assent is the power of confirming the "
            "impression.” [P1] Origen's vocabulary is therefore continuous "
            "with the Stoic analysis"
        )
        clause = extract_claim_clause(sentence, keys={"P1"})
        assert clause.clause == (
            "“The faculty of assent is the power of confirming the impression.”"
        )
        assert "Origen" not in clause.clause

    def test_marker_after_the_period(self) -> None:
        clause = extract_claim_clause("Chrysippus held X. [P1]", keys={"P1"})
        assert clause.clause == "Chrysippus held X."
        assert clause.marker_found

    def test_fragment_falls_back_to_the_sentence(self) -> None:
        clause = extract_claim_clause("Bobzien [N3].", keys={"N3"})
        assert clause.marker_found
        assert clause.clause == "Bobzien."

    def test_no_marker_falls_back_to_the_whole_sentence(self) -> None:
        clause = extract_claim_clause("A ledger claim without a marker.", keys={"P9"})
        assert not clause.marker_found
        assert clause.clause == "A ledger claim without a marker."
        assert clause.companion_tokens == ()

    def test_bracketed_prose_does_not_cut_the_clause(self) -> None:
        clause = extract_claim_clause("A [sic] claim about assent [P1].", keys={"P1"})
        assert clause.clause == "A [sic] claim about assent"


class TestSentenceForCitation:
    def test_marker_after_the_period_cites_the_preceding_sentence(self) -> None:
        text = "Chrysippus held X. [P1] Cleanthes held Y [P2]."
        assert sentence_for_citation(text, keys={"P1"}) == "Chrysippus held X. [P1]"
        assert sentence_for_citation(text, keys={"P2"}) == "Cleanthes held Y [P2]."

    def test_abbreviation_before_a_number_does_not_cut(self) -> None:
        text = "See p. 330 for the claim [P1]. Next [P2]."
        assert sentence_for_citation(text, keys={"P1"}) == (
            "See p. 330 for the claim [P1]."
        )

    def test_list_prefix_and_blockquote_are_stripped(self) -> None:
        text = "- First item [P1].\n> Quoted line [P2]."
        assert sentence_for_citation(text, keys={"P1"}) == "First item [P1]."
        assert sentence_for_citation(text, keys={"P2"}) == "Quoted line [P2]."

    def test_absent_marker(self) -> None:
        assert sentence_for_citation("No marker here.", keys={"P1"}) is None
        assert sentence_for_citation("", keys={"P1"}) is None


class TestParagraphContext:
    TEXT = "Intro.\n\nFirst sentence [P1]. Second [P2]. Third.\n\nOther paragraph."

    def test_returns_the_paragraph_holding_the_sentence(self) -> None:
        assert paragraph_context(self.TEXT, "Second [P2].") == (
            "First sentence [P1]. Second [P2]. Third."
        )

    def test_windows_a_long_paragraph_around_the_sentence(self) -> None:
        context = paragraph_context(self.TEXT, "Second [P2].", max_chars=20)
        assert "Second [P2]." in context
        assert len(context) <= 20

    def test_sentence_not_found(self) -> None:
        assert paragraph_context(self.TEXT, "Absent.") == ""
        assert paragraph_context("", "Second [P2].") == ""
