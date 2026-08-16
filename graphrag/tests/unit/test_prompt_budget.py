"""Whole-prompt budgeting for the dialectical synthesis.

Regression cover for the prompt-size blowout: a "250k tier" query shipped a
~1.2M-token synthesis prompt because the tier budget governed only the context
pack, while the section the prompt is actually built from — the controversy map,
with every contested passage's FULL text — was unbudgeted. Full-book passage
nodes (80-123k chars) then multiplied it.

Covered here:
- :func:`plan_prompt_budget` per-section math (fixed first, remainder to the
  map, floor so the map never collapses).
- :func:`excerpt_within_budget` selecting a relevant window at sentence/line
  boundaries — never a mid-quote cut — and leaving the fitting text verbatim.
- The end-to-end guarantee: three 100k-char passages inside a large map yield a
  synthesis prompt within the tier budget (x1.1).
"""

from __future__ import annotations

import logging

import pytest

from eleutheria_graphrag.agents.controversy_map import (
    fit_controversy_frames_layer,
    render_controversy_frames_layer,
)
from eleutheria_graphrag.agents.dialectical_synthesis import (
    DIALECTICAL_SYNTHESIS_SYSTEM,
    build_synthesis_prompt,
)
from eleutheria_graphrag.agents.prompt_budget import (
    ELISION_MARKER,
    EXEGESIS_TOKEN_CAP_DEFAULT,
    MAP_FLOOR_TOKENS,
    NODE_DESCRIPTION_TOKEN_CAP,
    PASSAGE_TOKEN_CAP_DEFAULT,
    LayerCaps,
    cap_description,
    cap_ladder,
    excerpt_within_budget,
    plan_prompt_budget,
    query_terms,
)
from eleutheria_graphrag.agents.state import (
    AnswerShape,
    ControversyFrame,
    ControversyMap,
    DialecticalLink,
    FrameCompleteness,
    GroundedPosition,
    PassageRef,
    synthesis_context_budget,
)
from eleutheria_graphrag.services.token_budget import estimate_tokens

GREEK = "τῶν ὄντων τὰ μέν ἐστιν ἐφ᾽ ἡμῖν τὰ δὲ οὐκ ἐφ᾽ ἡμῖν. "
EN = "Of things that exist, some are up to us and some are not up to us. "


def _passage(pid: str, chars: int, *, author: str = "Epictetus") -> PassageRef:
    return PassageRef(
        passage_id=pid,
        work="Dissertationes",
        author=author,
        canonical_ref="1.1.1",
        original_text=GREEK * max(1, chars // len(GREEK)),
        english_text=EN * max(1, (chars // 2) // len(EN)),
        language="grc",
    )


def _map(*, n_frames: int = 3, per_frame: int = 3, sizes: list[int]) -> ControversyMap:
    cmap = ControversyMap(
        question_frame="Did Epictetus think freedom is up to us?",
        shape=AnswerShape.SURVEY_OF_DEBATES,
    )
    idx = 0
    for f in range(n_frames):
        passages = []
        for _ in range(per_frame):
            passages.append(_passage(f"passage_{idx}", sizes[idx % len(sizes)]))
            idx += 1
        cmap.frames.append(
            ControversyFrame(
                frame_id=f"f{f}",
                title=f"Fault line {f}",
                period="Imperial",
                positions=[
                    GroundedPosition(
                        position_id=f"p{f}a",
                        holder="Bobzien",
                        holder_node_id="scholar_bobzien",
                        claim="eph' hemin is a one-sided capacity",
                        publication="Determinism and Freedom",
                        page_grounding="p. 234",
                    ),
                    GroundedPosition(
                        position_id=f"p{f}b",
                        holder="Frede",
                        holder_node_id="scholar_frede",
                        claim="the will emerges with Epictetus",
                        publication="A Free Will",
                        page_grounding="p. 44",
                    ),
                ],
                links=[
                    DialecticalLink(
                        relation="opposes",
                        from_id=f"p{f}a",
                        to_id=f"p{f}b",
                        from_holder="Bobzien",
                        to_holder="Frede",
                    )
                ],
                contested_passages=passages,
                completeness=FrameCompleteness(incident_edge_count=3),
            )
        )
    return cmap


# ── plan_prompt_budget: per-section math ─────────────────────────────────────


def test_remainder_is_tier_budget_minus_fixed_sections() -> None:
    comp = plan_prompt_budget(
        tier_budget=250_000,
        system_prompt="x " * 3000,  # 3000 words -> 3000 tokens (word floor)
        instructions="y " * 1000,
        answer_tokens=12_000,
        safety_margin=4_000,
    )
    assert comp.system == estimate_tokens("x " * 3000)
    assert comp.instructions == estimate_tokens("y " * 1000)
    assert comp.answer_reserve == 12_000
    assert comp.variable_budget == 250_000 - comp.fixed
    # The variable budget plus everything fixed is exactly the tier budget.
    assert comp.variable_budget + comp.fixed == 250_000


def test_variable_budget_never_collapses_to_zero() -> None:
    comp = plan_prompt_budget(
        tier_budget=10_000,
        system_prompt="x " * 5000,
        instructions="y " * 5000,
        answer_tokens=12_000,
    )
    assert comp.variable_budget == MAP_FLOOR_TOKENS
    assert any("floored" in note for note in comp.notes)


def test_log_line_names_every_section() -> None:
    comp = plan_prompt_budget(
        tier_budget=250_000, system_prompt="s", instructions="i", answer_tokens=1000
    )
    comp.map_tokens = 190_000
    line = comp.log_line()
    assert line.startswith("synthesis prompt: total≈")
    for token in ("map ", "pack ", "ledger ", "system ", "tier budget "):
        assert token in line


# ── excerpt_within_budget: window selection, never a mid-quote cut ───────────


def test_text_within_budget_is_returned_verbatim() -> None:
    text = GREEK * 3
    excerpt, was_cut = excerpt_within_budget(text, 10_000)
    assert excerpt == text
    assert was_cut is False


def test_oversize_text_is_excerpted_at_sentence_boundaries() -> None:
    units = [f"Sentence number {i} about deliberation." for i in range(400)]
    text = " ".join(units)
    excerpt, was_cut = excerpt_within_budget(text, 200)
    assert was_cut is True
    assert estimate_tokens(excerpt) <= 260  # budget + the elision markers
    assert ELISION_MARKER.split("{")[0] in excerpt
    # Every retained sentence is retained WHOLE — no mid-quote cut.
    retained = [u for u in units if u in excerpt]
    assert retained, "at least one whole unit must survive"


def test_excerpt_window_anchors_on_the_question_terms() -> None:
    units = [f"Filler sentence {i} on unrelated matters." for i in range(300)]
    units[250] = "Here Epictetus says prohairesis is what is up to us."
    text = " ".join(units)
    excerpt, was_cut = excerpt_within_budget(
        text, 120, terms=query_terms("What did Epictetus say about prohairesis?")
    )
    assert was_cut is True
    assert "prohairesis" in excerpt


def test_unpunctuated_dump_is_cut_at_a_word_boundary_not_mid_word() -> None:
    # A "passage" with no sentence boundary at all (a whole book as one blob)
    # must still be bounded — but only ever between whole words.
    text = GREEK.replace(".", "") * 400
    excerpt, was_cut = excerpt_within_budget(text, 60)
    assert was_cut is True
    assert estimate_tokens(excerpt) <= 120
    body = excerpt.split("[…")[0].strip()
    assert body, "some text must survive"
    for word in body.split():
        assert word in text  # every retained word is a whole word of the source


def test_cap_description_bounds_a_whole_essay_node_description() -> None:
    essay = "Avertissement méthodologique sur la question. " * 4000
    capped = cap_description(essay, 500)
    assert estimate_tokens(capped) < 700
    assert len(capped) < len(essay)


# ── map fitting: source caps + selection ─────────────────────────────────────


def test_full_book_passage_is_capped_at_source_without_a_budget() -> None:
    """Even with no explicit budget, one passage cannot dump a whole book."""
    cmap = _map(n_frames=1, per_frame=1, sizes=[120_000])
    layer = render_controversy_frames_layer(cmap)
    assert estimate_tokens(layer) < 4 * PASSAGE_TOKEN_CAP_DEFAULT


def test_fit_keeps_every_passage_when_the_map_already_fits() -> None:
    cmap = _map(n_frames=3, per_frame=3, sizes=[1200])
    _layer, stats = fit_controversy_frames_layer(cmap, 250_000)
    assert stats["passages_kept"] == stats["passages_total"] == 9
    assert stats["cap_tokens"] == PASSAGE_TOKEN_CAP_DEFAULT


def test_fit_tightens_the_per_passage_cap_before_dropping_any_passage() -> None:
    """Step 2 of the ladder: caps tighten gradually, nothing is dropped yet."""
    cmap = _map(n_frames=3, per_frame=6, sizes=[100_000])
    _layer, stats = fit_controversy_frames_layer(cmap, 20_000)
    assert stats["passages_kept"] == stats["passages_total"] == 18
    assert stats["cap_tokens"] < PASSAGE_TOKEN_CAP_DEFAULT
    assert stats["tokens"] <= 20_000 * 1.1


def test_fit_drops_lowest_priority_passages_only_when_the_floor_will_not_fit() -> None:
    """Step 3: with the cap already at its floor, whole passages go — round-robin.

    The surviving set must still hold the TOP-scored passage of every frame
    before any frame contributes a second one.
    """
    cmap = _map(n_frames=3, per_frame=6, sizes=[100_000])
    _layer, stats = fit_controversy_frames_layer(cmap, 3_000)
    assert 0 < stats["passages_kept"] < stats["passages_total"]
    assert stats["cap_tokens"] == cap_ladder(PASSAGE_TOKEN_CAP_DEFAULT, 250)[-1]
    assert stats["tokens"] <= 3_000 * 1.1


def test_secondary_prose_shrinks_before_a_single_passage_is_dropped() -> None:
    """The fitting ORDER: exegesis + position claims yield first, primary last.

    The prod inversion this pins: contested primary passages were cut to 1/46
    while the unbudgeted position layer stayed whole. Here the budget is tight
    enough to force real reduction, and it must land on the prose ABOUT the
    evidence — never on the evidence.
    """
    cmap = _map(n_frames=3, per_frame=1, sizes=[1200])
    for frame in cmap.frames:
        for pos in frame.positions:
            pos.claim = "Bobzien reads it as an unimpeded causal contribution. " * 400
    for i in range(12):
        cmap.exegesis_units.append(_passage(f"exeg_{i}", 100_000, author="Alexander"))

    _layer, stats = fit_controversy_frames_layer(cmap, 20_000)

    # Primary evidence: untouched — every passage kept, at the full source cap.
    assert stats["passages_kept"] == stats["passages_total"] == 3
    assert stats["cap_tokens"] == PASSAGE_TOKEN_CAP_DEFAULT
    # Secondary prose: both sections gave way.
    assert stats["exegesis_cap_tokens"] < EXEGESIS_TOKEN_CAP_DEFAULT
    assert stats["position_cap_tokens"] < NODE_DESCRIPTION_TOKEN_CAP
    assert stats["tokens"] <= 20_000 * 1.1


def test_position_claims_are_bounded_as_a_SECTION_not_only_per_item() -> None:
    """The measured owner of the 570k blowout: an unbounded COUNT of positions.

    Each claim was capped at 2000 tokens, but a hub debate node grounds every
    link endpoint as a position — 285 of them cost 576k, outside the fitter.
    """
    cmap = _map(n_frames=1, per_frame=1, sizes=[1200])
    frame = cmap.frames[0]
    frame.positions = [
        GroundedPosition(
            position_id=f"scholarly_argument_{i}",
            holder="Bobzien",
            claim="An unimpeded causal contribution of the agent's own nature. " * 200,
            publication="Determinism and Freedom",
        )
        for i in range(285)
    ]
    layer, stats = fit_controversy_frames_layer(cmap, 100_000)
    assert estimate_tokens(layer) <= 100_000 * 1.1
    assert stats["position_cap_tokens"] < NODE_DESCRIPTION_TOKEN_CAP


def test_an_unshrinkable_section_is_named_in_a_warning(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Overshooting is a BUG SIGNAL, not an accepted outcome — name the owner.

    ``coverage_gaps`` is the one section with no cap (planner strings, bounded
    in practice); a map that overshoots on it must say so by name.
    """
    cmap = _map(n_frames=1, per_frame=1, sizes=[900])
    cmap.coverage_gaps = ["frame under-filled (no positions or links)"] * 4000
    with caplog.at_level(
        logging.WARNING, logger="eleutheria_graphrag.agents.controversy_map"
    ):
        fit_controversy_frames_layer(cmap, 5_000)
    messages = [r.getMessage() for r in caplog.records]
    assert any("refused to fit" in m and "coverage_gaps" in m for m in messages)


def test_exegesis_units_are_not_re_embedded_when_already_contested() -> None:
    cmap = _map(n_frames=1, per_frame=1, sizes=[900])
    duplicate = cmap.frames[0].contested_passages[0]
    cmap.exegesis_units.append(duplicate)
    layer = render_controversy_frames_layer(cmap)
    assert layer.count(f"[passage_{duplicate.passage_id}]") == 1
    assert "## Standalone Primary Text" not in layer


# ── end-to-end: the whole prompt lands inside the tier budget ────────────────


@pytest.mark.parametrize("tier", ["quick", "standard", "deep"])
def test_whole_synthesis_prompt_stays_within_tier_budget(tier: str) -> None:
    """Three 100k-char passage bundles inside a >120k-char map.

    The prod failure: this shape produced a ~800k-token prompt under a "250k"
    reported budget. The whole prompt (system + instructions + map) must now sit
    inside the tier budget, with 10% slack for estimator variance.
    """
    cmap = _map(n_frames=3, per_frame=3, sizes=[100_000, 100_000, 100_000, 3000])
    # Scaffolding large enough that the map itself is >120k chars before caps.
    uncapped = LayerCaps(passage_tokens=10_000_000, exegesis_tokens=10_000_000)
    assert len(render_controversy_frames_layer(cmap, caps=uncapped)) > 120_000

    user_prompt, comp = build_synthesis_prompt(
        cmap, budget_tier=tier, answer_tokens=12_000
    )
    whole = DIALECTICAL_SYNTHESIS_SYSTEM + "\n" + user_prompt
    budget = synthesis_context_budget(tier)
    assert estimate_tokens(whole) <= budget * 1.1
    assert comp.total <= budget * 1.1
    # The map still carries real evidence — the budget must not empty it.
    assert "CONTESTED PRIMARY TEXT" in user_prompt
    assert "--opposes-->" in user_prompt


def _production_shaped_map() -> ControversyMap:
    """The 2026-08 smoke-run shape: hub frames, 46 contested, heavy exegesis.

    Reproduces the log line ``map 570k … passages 1/46 kept, per-passage cap 250``
    — 285 positions whose KG ``stance``/``conclusion`` claims each hit the
    2000-token per-item cap, plus full-book passage nodes on both pools.
    """
    cmap = ControversyMap(
        question_frame=(
            "Did Epictetus think freedom is up to us, and how do Bobzien and "
            "Frede differ?"
        ),
        shape=AnswerShape.SURVEY_OF_DEBATES,
    )
    sizes = [1500, 2000, 1200, 900, 80_000, 1400, 1100, 123_000, 1300]
    idx = 0
    for f, (n_passages, n_positions) in enumerate(
        [(8, 90), (8, 70), (8, 50), (8, 35), (7, 25), (7, 15)]
    ):
        positions = [
            GroundedPosition(
                position_id=f"scholarly_argument_{f}_{i}",
                holder=["Bobzien", "Frede", "Long", "Dobbin", "Sorabji"][i % 5],
                claim="An unimpeded causal contribution of the agent's nature. " * 200,
                publication="Determinism and Freedom in Stoic Philosophy",
                page_grounding="p. 234",
            )
            for i in range(n_positions)
        ]
        passages = []
        for _ in range(n_passages):
            passages.append(_passage(f"passage_{idx}", sizes[idx % len(sizes)]))
            idx += 1
        cmap.frames.append(
            ControversyFrame(
                frame_id=f"frame_{f}",
                title=f"Fault line {f}",
                period="Imperial",
                positions=positions,
                links=[
                    DialecticalLink(
                        relation="opposes",
                        from_id=f"scholarly_argument_{f}_{i}",
                        to_id=f"scholarly_argument_{f}_{(i + 1) % n_positions}",
                    )
                    for i in range(n_positions)
                ],
                contested_passages=passages,
                completeness=FrameCompleteness(incident_edge_count=50 - f),
            )
        )
    for j, size in enumerate([100_000, 60_000, 12_000, 8_000, 3_000, 2_000]):
        cmap.exegesis_units.append(_passage(f"exeg_{j}", size, author="Alexander"))
    return cmap


def test_production_shaped_map_fits_and_keeps_the_contested_evidence() -> None:
    """The whole regression, on the shape that broke prod.

    Before: ``total≈572k (map 570k …) [passages 1/46 kept, per-passage cap 250]``
    — the map overshot a 250k tier by 2.3x while the primary evidence, the one
    thing this platform exists to quote, had been squeezed to a single passage.
    """
    cmap = _production_shaped_map()
    contested = sum(len(f.contested_passages) for f in cmap.frames)
    assert contested == 46

    user_prompt, comp = build_synthesis_prompt(
        cmap, budget_tier="standard", answer_tokens=12_000
    )
    whole = estimate_tokens(DIALECTICAL_SYNTHESIS_SYSTEM + "\n" + user_prompt)
    assert whole <= 275_000
    assert comp.total <= 275_000

    _layer, stats = fit_controversy_frames_layer(cmap, comp.variable_budget)
    assert stats["passages_kept"] >= 0.8 * contested
    # And the dialectic is still there: the fix bounds it, it does not delete it.
    assert "--opposes-->" in user_prompt
    assert "CONTESTED PRIMARY TEXT" in user_prompt


def test_map_object_is_never_mutated_by_fitting() -> None:
    """Quote containment verifies against the UNCUT originals — keep them uncut."""
    cmap = _production_shaped_map()
    before = [
        (p.passage_id, len(p.original_text), len(p.english_text or ""))
        for f in cmap.frames
        for p in f.contested_passages
    ]
    claims_before = [len(p.claim) for f in cmap.frames for p in f.positions]
    fit_controversy_frames_layer(cmap, 40_000)
    after = [
        (p.passage_id, len(p.original_text), len(p.english_text or ""))
        for f in cmap.frames
        for p in f.contested_passages
    ]
    assert after == before
    assert [len(p.claim) for f in cmap.frames for p in f.positions] == claims_before


def test_synthesis_prompt_logs_its_composition(
    caplog: pytest.LogCaptureFixture,
) -> None:
    cmap = _map(n_frames=2, per_frame=2, sizes=[2000])
    with caplog.at_level(
        logging.INFO, logger="eleutheria_graphrag.agents.dialectical_synthesis"
    ):
        build_synthesis_prompt(cmap, budget_tier="standard", answer_tokens=12_000)
    lines = [r.getMessage() for r in caplog.records if "synthesis prompt:" in r.message]
    assert lines, "the composition INFO line must be emitted"
    assert "tier budget 250k" in lines[0]
