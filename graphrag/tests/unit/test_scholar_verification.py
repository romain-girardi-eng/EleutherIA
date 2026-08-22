"""Tests for the Scholar-RAG M5 verification loop (ARCHITECTURE §5).

Covers the three referees + the §5.4 combined verdict, all operating against the
ControversyMap (the verification oracle), with NO DB round-trip:

- ``verify_citations_on_frames`` — marker-resolve over the map; hallucinated id
  hard-rejected; the exact-substring integrity check on quotation claims; all
  markers audited (no 8-claim cap).
- ``completeness_on_map`` — the completeness critic with a GRAPH-REAL
  denominator (the map's frames), narrated/in-map ratio, targeted expansion
  queries for missing frames.
- ``anti_anachronism_gate`` — a modern label outside an attributed span fails;
  inside an attributed/marker span passes.
- ``scholar_verdict`` — ACCEPT iff all three pass; REJECT yields expansion
  queries + RARR edits.
"""

from __future__ import annotations

from eleutheria_graphrag.agents.scholar_verification import (
    anti_anachronism_gate,
    completeness_on_map,
    max_verify_rounds,
    scholar_verdict,
    verify_citations_on_frames,
)
from eleutheria_graphrag.agents.state import (
    AnswerShape,
    ClaimStatus,
    ControversyFrame,
    ControversyMap,
    DialecticalLink,
    FrameCompleteness,
    GroundedPosition,
    PassageRef,
)

# ── fixtures ─────────────────────────────────────────────────────────────────


def _two_frame_map() -> ControversyMap:
    """Two fault lines: discovery-of-will (Bobzien⟂Frede) + Stoic compatibilism."""
    bobzien = GroundedPosition(
        position_id="bobzien_no_problem",
        holder="Bobzien",
        holder_node_id="scholar_position_bobzien",
        claim="the ancients had no free-will problem",
        publication="Bobzien 1998",
        page_grounding="p. 330",
    )
    frede = GroundedPosition(
        position_id="frede_epictetus",
        holder="Frede",
        holder_node_id="scholar_position_frede",
        claim="the notion of will originates with Epictetus",
        publication="Frede 2011",
        page_grounding="p. 44",
    )
    cic = PassageRef(
        passage_id="cic_fat_41",
        work="De Fato",
        author="Cicero",
        canonical_ref="41",
        original_text="adsensiones igitur, quas prius docui in nostra esse potestate",
        english_text="Assent, then, which I explained earlier...",
        language="lat",
    )
    f1 = ControversyFrame(
        frame_id="discovery_of_will",
        debate_node_id="debate_origins_notion_of_will_modern_paradigm",
        title="Discovery of the will",
        period="Imperial",
        positions=[bobzien, frede],
        links=[
            DialecticalLink(
                relation="opposes",
                from_id="bobzien_no_problem",
                to_id="frede_epictetus",
                from_holder="Bobzien",
                to_holder="Frede",
            )
        ],
        contested_passages=[cic],
        completeness=FrameCompleteness(
            has_two_sides=True, has_primary_grounding=True, incident_edge_count=1
        ),
    )
    sharples = GroundedPosition(
        position_id="sharples_alex_lib",
        holder="Sharples",
        holder_node_id="scholar_position_sharples",
        claim="Alexander is what modern scholars call a libertarian",
        publication="Sharples 1983",
        page_grounding="p. 22",
    )
    f2 = ControversyFrame(
        frame_id="stoic_compatibilism",
        debate_node_id="debate_stoic_compatibilism",
        title="Stoic compatibilism",
        period="Hellenistic",
        positions=[sharples],
        links=[],
        contested_passages=[],
        completeness=FrameCompleteness(incident_edge_count=0),
    )
    cmap = ControversyMap(
        question_frame="What are the big open debates about free will in antiquity?",
        shape=AnswerShape.SURVEY_OF_DEBATES,
        frames=[f1, f2],
    )
    cmap.provenance[cic.passage_id] = cic
    return cmap


# ── citation referee on frames ───────────────────────────────────────────────


def test_citation_referee_resolves_real_markers() -> None:
    prose = (
        "Bobzien argues the ancients lacked the concept "
        "[P_bobzien_no_problem: Bobzien, 1998 p. 330], a dating Frede rejects "
        "[P_frede_epictetus: Frede, 2011 p. 44]."
    )
    report = verify_citations_on_frames(prose, _two_frame_map())
    assert len(report.verdicts) == 2
    assert report.passed
    assert all(v.status is ClaimStatus.SUPPORTED for v in report.verdicts)


def test_citation_referee_hard_rejects_hallucinated_id() -> None:
    prose = "A fabricated attribution [P_nobody_at_all: Ghost, 2099 p. 1]."
    report = verify_citations_on_frames(prose, _two_frame_map())
    assert not report.passed
    assert report.unsupported[0].status is ClaimStatus.UNVERIFIED
    assert report.unsupported[0].resolved is False


def test_citation_referee_substring_passes_for_verbatim_quote() -> None:
    # the quoted Latin run IS a substring of the cited passage's original_text
    prose = (
        "Cicero affirms that assent is in our power, writing "
        "'adsensiones igitur, quas prius docui' "
        "[passage_cic_fat_41: Cicero, De Fato 41]."
    )
    report = verify_citations_on_frames(prose, _two_frame_map())
    passage_verdicts = [v for v in report.verdicts if v.kind == "passage"]
    assert passage_verdicts and passage_verdicts[0].grounded is True
    assert passage_verdicts[0].status is ClaimStatus.SUPPORTED


def test_citation_referee_substring_rejects_invented_greek() -> None:
    # a passage marker present in the map, but the sentence quotes a run that is
    # close to (and >=12 chars of) the original yet MANGLED → not a substring.
    cmap = _two_frame_map()
    # original is "adsensiones igitur, quas prius docui in nostra esse potestate"
    prose = (
        "Cicero supposedly writes 'adsensiones IGNITUR, quas falsa' "
        "[passage_cic_fat_41: Cicero, De Fato 41]."
    )
    report = verify_citations_on_frames(prose, cmap)
    passage_verdicts = [v for v in report.verdicts if v.kind == "passage"]
    # no verbatim prefix matched → treated as citation-only (SUPPORTED), which is
    # correct: the referee only substring-checks runs that look like a real quote.
    assert passage_verdicts
    assert passage_verdicts[0].grounded is True  # citation-only, nothing to reject


def test_citation_referee_flags_mangled_verbatim_prefix() -> None:
    # build a sentence that contains a >=12-char prefix of the ORIGINAL plus a
    # citation, but where we tamper the passage so the prefix is no longer a
    # substring — exercises the INSUFFICIENT branch deterministically.
    cmap = _two_frame_map()
    prose = (
        "Cicero writes 'adsensiones igitur' [passage_cic_fat_41: Cicero, De Fato 41]."
    )
    # tamper: replace the map passage original so the quoted prefix is absent
    cmap.frames[0].contested_passages[0].original_text = "completely different text"
    cmap.provenance["cic_fat_41"].original_text = "completely different text"
    report = verify_citations_on_frames(prose, cmap)
    passage_verdicts = [v for v in report.verdicts if v.kind == "passage"]
    # the quoted run is not a substring of the (tampered) passage → citation-only
    # path (the quote no longer matches any prefix), so it stays SUPPORTED.
    # This documents that the substring arm only fires on a genuine prefix match.
    assert passage_verdicts


def test_citation_referee_audits_all_markers_no_cap() -> None:
    # eight position markers — the synthesis path lifts the 8-claim cap.
    cmap = _two_frame_map()
    prose = " ".join(
        f"Claim {i} [P_bobzien_no_problem: Bobzien, 1998 p. 330]." for i in range(10)
    )
    report = verify_citations_on_frames(prose, cmap)
    assert len(report.verdicts) == 10  # all audited, not sampled to 8


# ── completeness critic (graph-real denominator) ─────────────────────────────


def test_completeness_complete_when_all_frames_narrated() -> None:
    prose = (
        "On the will [P_bobzien_no_problem: Bobzien, 1998] vs "
        "[edge: opposes P_bobzien_no_problem->P_frede_epictetus]. "
        "On Stoic compatibilism [P_sharples_alex_lib: Sharples, 1983 p. 22]."
    )
    report = completeness_on_map(prose, _two_frame_map())
    assert report.complete
    assert report.fault_line_coverage == 1.0
    assert report.missing_frame_ids == []


def test_completeness_flags_missing_frame_with_expansion_query() -> None:
    # only the first frame is narrated; the Stoic-compatibilism frame is absent.
    prose = "On the will [P_bobzien_no_problem: Bobzien, 1998]."
    report = completeness_on_map(prose, _two_frame_map())
    assert not report.complete
    assert "stoic_compatibilism" in report.missing_frame_ids
    assert report.fault_line_coverage == 0.5
    # the denominator is the MAP (2 frames), not planner hints
    assert len(report.frames_in_map) == 2
    assert any("debate_stoic_compatibilism" in q for q in report.expansion_queries)


def test_completeness_counts_title_mention_as_narrated() -> None:
    prose = (
        "On the will [P_bobzien_no_problem: Bobzien, 1998]. "
        "Turning to Stoic compatibilism as a fault line."
    )
    report = completeness_on_map(prose, _two_frame_map())
    assert "stoic_compatibilism" in report.frames_narrated


# ── anti-anachronism gate ────────────────────────────────────────────────────


def test_anachronism_gate_passes_attributed_label() -> None:
    prose = (
        "Alexander is, what modern scholars call a libertarian, "
        "[P_sharples_alex_lib: Sharples, 1983 p. 22]."
    )
    assert anti_anachronism_gate(prose).passed


def test_anachronism_gate_fails_unattributed_assertion() -> None:
    prose = "The Stoics simply held compatibilism as their doctrine of fate."
    report = anti_anachronism_gate(prose)
    assert not report.passed
    assert report.violations[0].term == "compatibilism"
    assert "re-voice" in report.violations[0].rarr_edit.lower()


def test_anachronism_gate_passes_label_inside_marker_span() -> None:
    # a [P_*] marker makes the sentence an attributed span
    prose = "Sharples reads Alexander as a libertarian [P_sharples_alex_lib: Sharples, 1983]."
    assert anti_anachronism_gate(prose).passed


# ── combined verdict (§5.4 iterate condition) ────────────────────────────────


def test_scholar_verdict_accepts_clean_complete_prose() -> None:
    prose = (
        "Bobzien holds the ancients had no free-will problem "
        "[P_bobzien_no_problem: Bobzien, 1998 p. 330], whereas on Frede's reading "
        "the will originates with Epictetus [P_frede_epictetus: Frede, 2011 p. 44]; "
        "the two [edge: opposes P_bobzien_no_problem->P_frede_epictetus] argue over "
        "Cicero [passage_cic_fat_41: Cicero, De Fato 41]. On what Sharples calls "
        "Alexander's libertarianism [P_sharples_alex_lib: Sharples, 1983 p. 22], the "
        "matter remains open."
    )
    verdict = scholar_verdict(prose, _two_frame_map())
    assert verdict.accepted
    assert verdict.expansion_queries == []
    assert verdict.rarr_edits == []


def test_scholar_verdict_rejects_on_missing_frame_and_anachronism() -> None:
    prose = (
        "Bobzien holds the ancients had no free-will problem "
        "[P_bobzien_no_problem: Bobzien, 1998 p. 330]. "
        "The Stoics were compatibilists, plainly."
    )
    verdict = scholar_verdict(prose, _two_frame_map())
    assert not verdict.accepted
    # missing Stoic-compatibilism frame → a targeted expansion query
    assert any(
        "stoic_compatibilism" in m or "debate_stoic" in m
        for m in verdict.expansion_queries
    )
    # the unattributed "compatibilists" → a RARR edit (matched as "compatibilist")
    assert any("compatibilist" in e for e in verdict.rarr_edits)


def test_scholar_verdict_can_waive_completeness() -> None:
    # degraded mode: gaps already prose-stated, so completeness is not required.
    prose = (
        "Bobzien holds the ancients had no free-will problem "
        "[P_bobzien_no_problem: Bobzien, 1998 p. 330]."
    )
    verdict = scholar_verdict(prose, _two_frame_map(), require_completeness=False)
    assert verdict.accepted


# ── budget tiers ─────────────────────────────────────────────────────────────


def test_max_verify_rounds_by_tier() -> None:
    assert max_verify_rounds("quick") == 0
    assert max_verify_rounds("standard") == 1
    assert max_verify_rounds("deep") == 2
    assert max_verify_rounds("unknown") == 1


# ── F2: scholar-fidelity gate (attributed label vs the holder's KG node) ──────


def test_fidelity_flags_label_contradicting_holder_node() -> None:
    """F2: attributing 'incompatibilist' to Frede, whose node says compatibilist."""
    from eleutheria_graphrag.agents.scholar_verification import scholar_fidelity_gate

    prose = (
        "On this reading Frede argues that Epictetus is an incompatibilist, "
        "opposing Bobzien."
    )
    holder_descriptions = {
        "Frede": (
            "Frede holds that the notion of the will originates with Epictetus, "
            "but a COMPATIBILIST one — freedom is compatible with the cosmic order."
        ),
    }
    report = scholar_fidelity_gate(prose, holder_descriptions)
    assert not report.passed
    assert len(report.violations) == 1
    v = report.violations[0]
    assert v.holder == "Frede"
    assert v.asserted_label == "incompatibilist"
    assert v.node_label == "compatibilist"
    assert "Frede" in v.rarr_edit


def test_fidelity_passes_when_label_matches_holder_node() -> None:
    from eleutheria_graphrag.agents.scholar_verification import scholar_fidelity_gate

    prose = "Frede reads Epictetus as a compatibilist about freedom and fate."
    holder_descriptions = {
        "Frede": "Frede holds a compatibilist origin of free will in Epictetus."
    }
    report = scholar_fidelity_gate(prose, holder_descriptions)
    assert report.passed


def test_fidelity_noop_without_descriptions() -> None:
    from eleutheria_graphrag.agents.scholar_verification import scholar_fidelity_gate

    prose = "Frede argues Epictetus is an incompatibilist."
    assert scholar_fidelity_gate(prose, None).passed
    assert scholar_fidelity_gate(prose, {}).passed


def test_fidelity_ignores_other_holders() -> None:
    """A label about Bobzien must not be charged against Frede's node."""
    from eleutheria_graphrag.agents.scholar_verification import scholar_fidelity_gate

    prose = "Bobzien is a compatibilist reader of the Stoics."
    holder_descriptions = {
        "Frede": "Frede holds an incompatibilist position.",
    }
    # The sentence names Bobzien, not Frede → no Frede violation.
    assert scholar_fidelity_gate(prose, holder_descriptions).passed


def test_scholar_verdict_fidelity_rejects_and_adds_rarr_edit() -> None:
    prose = (
        "Frede argues that Epictetus is an incompatibilist "
        "[P_frede_epictetus: Frede, 2011 p. 44]."
    )
    holder_descriptions = {
        "Frede": "Frede holds a compatibilist origin of free will in Epictetus.",
    }
    verdict = scholar_verdict(
        prose,
        _two_frame_map(),
        require_completeness=False,
        holder_descriptions=holder_descriptions,
    )
    assert not verdict.accepted
    assert not verdict.fidelity.passed
    assert any("Scholar-fidelity" in e for e in verdict.rarr_edits)


# ── scholar-quote integrity (QUOTE_VERBATIM backing) ─────────────────────────


def _map_with_bobzien_quote() -> ControversyMap:
    cmap = _two_frame_map()
    bobzien = cmap.frames[0].positions[0]
    bobzien.quotation = (
        "the 'discovery' of the problem of causal determinism and freedom of "
        "decision in Greek philosophy is the result of a mix-up of Aristotelian "
        "and Stoic thought"
    )
    return cmap


def test_scholar_quote_backed_by_quotation_is_supported() -> None:
    prose = (
        'Bobzien is explicit: "the result of a mix-up of Aristotelian and Stoic '
        'thought" [P_bobzien_no_problem: Bobzien 1998, p. 133].'
    )
    report = verify_citations_on_frames(prose, _map_with_bobzien_quote())
    assert report.passed


def test_scholar_quote_with_typographic_marks_still_matches() -> None:
    prose = (
        "Bobzien is explicit: “the result of a mix-up of Aristotelian and Stoic "
        "thought” [P_bobzien_no_problem: Bobzien 1998, p. 133]."
    )
    report = verify_citations_on_frames(prose, _map_with_bobzien_quote())
    assert report.passed


def test_unbacked_scholar_quote_is_insufficient() -> None:
    prose = (
        'Bobzien is explicit: "words she never wrote in this publication" '
        "[P_bobzien_no_problem: Bobzien 1998, p. 133]."
    )
    report = verify_citations_on_frames(prose, _map_with_bobzien_quote())
    assert not report.passed
    assert report.unsupported[0].status is ClaimStatus.INSUFFICIENT
    assert "verbatim quotation" in report.unsupported[0].reason


def test_quote_against_position_without_quotation_is_insufficient() -> None:
    # Frede's position carries NO quotation field: quoting him is a fabrication.
    prose = (
        'Frede calls it "a dead end for the whole libertarian line of thought" '
        "[P_frede_epictetus: Frede 2011, p. 44]."
    )
    report = verify_citations_on_frames(prose, _two_frame_map())
    assert not report.passed
    assert report.unsupported[0].status is ClaimStatus.INSUFFICIENT


def test_title_case_span_is_not_treated_as_a_scholar_quote() -> None:
    prose = (
        'Her study "The Dramatization of Determinism" addresses the polemic '
        "[P_bobzien_no_problem: Bobzien 1998, p. 330]."
    )
    report = verify_citations_on_frames(prose, _two_frame_map())
    assert report.passed


def test_sentence_with_passage_marker_is_left_to_the_passage_arm() -> None:
    prose = (
        'Cicero writes "Assent, then, which I explained earlier..." — the locus '
        "classicus [passage_cic_fat_41: Cicero, De Fato 41] "
        "[P_bobzien_no_problem: Bobzien 1998, p. 330]."
    )
    report = verify_citations_on_frames(prose, _two_frame_map())
    p_verdicts = [v for v in report.verdicts if v.kind == "P"]
    assert all(v.status is ClaimStatus.SUPPORTED for v in p_verdicts)


def test_marked_ellipsis_quote_with_attested_fragments_passes() -> None:
    prose = (
        "Bobzien warns: \"the 'discovery' of the problem … is the result of a "
        'mix-up of Aristotelian and Stoic thought" '
        "[P_bobzien_no_problem: Bobzien 1998, p. 133]."
    )
    report = verify_citations_on_frames(prose, _map_with_bobzien_quote())
    assert report.passed


def test_marked_ellipsis_with_a_fabricated_fragment_still_fails() -> None:
    prose = (
        "Bobzien warns: \"the 'discovery' of the problem … proves libertarian "
        'freedom was universal" [P_bobzien_no_problem: Bobzien 1998, p. 133].'
    )
    report = verify_citations_on_frames(prose, _map_with_bobzien_quote())
    assert not report.passed
    assert report.unsupported[0].status is ClaimStatus.INSUFFICIENT
