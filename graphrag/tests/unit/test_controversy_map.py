"""Tests for the Scholar-RAG M3 ControversyMap assembly + serialisation.

Covers:
- ``assemble_controversy_map`` driving find_debates -> build_controversy_frame,
  ordering frames by raw incident-edge count (NO score), recording coverage gaps
  for under-filled frames, and indexing provenance.
- ``serialize_controversy_frames`` emitting first-class ``A --opposes--> B`` edge
  rows + bilingual contested passages (the F2 edge-slot fix), untruncated.
- The context-pack ``## Controversy Frames`` layer being inert without the flag
  and present with it.
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from eleutheria_graphrag.agents.controversy_map import (
    assemble_controversy_map,
    render_controversy_frames_layer,
    serialize_controversy_frames,
)
from eleutheria_graphrag.agents.state import (
    AnswerShape,
    ControversyFrame,
    ControversyMap,
    DialecticalLink,
    FrameCompleteness,
    GroundedPosition,
    PassageRef,
)
from eleutheria_graphrag.agents.tools.build_controversy_frame import (
    BuildControversyFrameResult,
)
from eleutheria_graphrag.agents.tools.find_debates import (
    DebateSummary,
    FindDebatesResult,
)


def _frame(
    fid: str,
    title: str,
    *,
    n_links: int,
    positions: list[GroundedPosition] | None = None,
    passages: list[PassageRef] | None = None,
) -> ControversyFrame:
    links = [
        DialecticalLink(
            relation="opposes",
            from_id=f"{fid}_a{i}",
            to_id=f"{fid}_b{i}",
            from_holder="A",
            to_holder="B",
        )
        for i in range(n_links)
    ]
    return ControversyFrame(
        frame_id=fid,
        debate_node_id=fid,
        title=title,
        positions=positions or [],
        links=links,
        contested_passages=passages or [],
        completeness=FrameCompleteness(incident_edge_count=n_links),
    )


# ── assembly ─────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_assemble_orders_frames_by_incident_edge_count() -> None:
    find_tool = AsyncMock()
    find_tool.execute.return_value = FindDebatesResult(
        debates=[
            DebateSummary(debate_id="d_small", label="small", type="debate"),
            DebateSummary(debate_id="d_big", label="big", type="debate"),
        ],
        total_found=2,
    )

    frame_map = {
        "d_small": _frame("d_small", "Small", n_links=1),
        "d_big": _frame("d_big", "Big", n_links=4),
    }

    build_tool = AsyncMock()

    async def _build(args: dict[str, str]) -> BuildControversyFrameResult:
        return BuildControversyFrameResult(frame=frame_map[args["seed_id"]])

    build_tool.execute.side_effect = _build

    cmap = await assemble_controversy_map(
        "open debates about fate",
        find_tool,
        build_tool,
        shape=AnswerShape.SURVEY_OF_DEBATES,
    )
    assert [f.frame_id for f in cmap.frames] == ["d_big", "d_small"]
    assert cmap.shape == AnswerShape.SURVEY_OF_DEBATES


@pytest.mark.asyncio
async def test_assemble_records_coverage_gap_for_empty_frame() -> None:
    find_tool = AsyncMock()
    find_tool.execute.return_value = FindDebatesResult(
        debates=[DebateSummary(debate_id="d_empty", label="empty", type="debate")],
        total_found=1,
    )
    build_tool = AsyncMock()
    build_tool.execute.return_value = BuildControversyFrameResult(
        frame=ControversyFrame(frame_id="d_empty", title="Empty")
    )
    cmap = await assemble_controversy_map("x", find_tool, build_tool)
    assert cmap.frames == []
    assert any("under-filled" in g for g in cmap.coverage_gaps)


@pytest.mark.asyncio
async def test_assemble_indexes_provenance() -> None:
    pref = PassageRef(
        passage_id="passage_alex_fat_12",
        author="Alexander",
        original_text="Ἀναιρουμένου δὲ",
        english_text="Since deliberation is abolished",
        language="grc",
    )
    find_tool = AsyncMock()
    find_tool.execute.return_value = FindDebatesResult(
        debates=[DebateSummary(debate_id="d1", label="d1", type="debate")],
        total_found=1,
    )
    build_tool = AsyncMock()
    build_tool.execute.return_value = BuildControversyFrameResult(
        frame=_frame("d1", "D1", n_links=1, passages=[pref])
    )
    cmap = await assemble_controversy_map("x", find_tool, build_tool)
    assert "passage_alex_fat_12" in cmap.provenance
    assert cmap.provenance["passage_alex_fat_12"].english_text


# ── serialisation (the F2 edge-slot fix) ─────────────────────────────────────


def test_serialize_emits_first_class_edge_rows() -> None:
    pos_a = GroundedPosition(
        position_id="p_frede",
        holder="Michael Frede",
        publication="Frede 2011, A Free Will",
        page_grounding="pp. 153-174",
        claim="The will originates with Epictetus.",
    )
    pos_b = GroundedPosition(
        position_id="p_dihle",
        holder="Albrecht Dihle",
        publication="Dihle 1982",
        claim="The will is a Christian innovation.",
    )
    link = DialecticalLink(
        relation="opposes",
        from_id="p_frede",
        to_id="p_dihle",
        from_holder="Frede",
        to_holder="Dihle",
        gloss="Frede dates emergence earlier than Augustine",
    )
    passage = PassageRef(
        passage_id="alex_fat_12",
        author="Alexander",
        work="De Fato",
        canonical_ref="12",
        original_text="Ἀναιρουμένου δὲ ὡς ἐδείχθη τοῦ βουλεύσασθαι",
        english_text="Since deliberation is abolished on their account",
        language="grc",
    )
    frame = ControversyFrame(
        frame_id="f1",
        title="When did the will emerge?",
        period="Imperial",
        positions=[pos_a, pos_b],
        links=[link],
        contested_passages=[passage],
        completeness=FrameCompleteness(incident_edge_count=1),
    )
    md = serialize_controversy_frames([frame])
    assert "## Controversy Frames" in md
    # The edge is a first-class row — the prompt cannot be edge-blind.
    assert "P_p_frede --opposes--> P_p_dihle" in md
    # Holder + page grounding both present.
    assert "Michael Frede" in md
    assert "pp. 153-174" in md
    # Bilingual contested passage, untruncated.
    assert "Ἀναιρουμένου δὲ ὡς ἐδείχθη τοῦ βουλεύσασθαι" in md
    assert "Since deliberation is abolished on their account" in md


def test_serialize_flags_one_sided_frame() -> None:
    frame = ControversyFrame(frame_id="f_lonely", title="One-sided", positions=[])
    md = serialize_controversy_frames([frame])
    assert "flag it" in md


def test_serialize_empty_frames_yields_empty_string() -> None:
    assert serialize_controversy_frames([]) == ""


def test_render_layer_includes_gaps_and_exegesis() -> None:
    cmap = ControversyMap(
        question_frame="x",
        frames=[_frame("f1", "F1", n_links=2)],
        exegesis_units=[
            PassageRef(
                passage_id="cic_fat_41",
                author="Cicero",
                original_text="…",
                language="lat",
            )
        ],
        coverage_gaps=["Carneadean transmission was thin"],
    )
    layer = render_controversy_frames_layer(cmap)
    assert "## Controversy Frames" in layer
    assert "## Standalone Primary Text" in layer
    assert "## Coverage Gaps" in layer
    assert "Carneadean transmission was thin" in layer


# ── context-pack edge layer: inert without the flag, present with it ─────────


def _state_with_map():
    from eleutheria_graphrag.agents.state import RAGState

    state = RAGState()
    state.question = "open debates about free will"
    state.controversy_map = ControversyMap(
        question_frame="open debates about free will",
        frames=[
            _frame(
                "f1",
                "When did the will emerge?",
                n_links=2,
                positions=[
                    GroundedPosition(
                        position_id="p_frede",
                        holder="Michael Frede",
                        publication="Frede 2011",
                        claim="Will originates with Epictetus.",
                    )
                ],
            )
        ],
    )
    return state


def test_context_pack_omits_frames_without_flag(monkeypatch) -> None:
    from eleutheria_graphrag.agents.graph_nodes import _build_context_pack

    monkeypatch.delenv("ELEUTHERIA_SCHOLAR_RAG", raising=False)
    pack = _build_context_pack(_state_with_map())
    assert pack.controversy_frames == []
    assert "## Controversy Frames" not in pack.prompt_context


def test_context_pack_includes_frames_with_flag(monkeypatch) -> None:
    from eleutheria_graphrag.agents.graph_nodes import _build_context_pack

    monkeypatch.setenv("ELEUTHERIA_SCHOLAR_RAG", "1")
    pack = _build_context_pack(_state_with_map())
    assert len(pack.controversy_frames) == 1
    assert "## Controversy Frames" in pack.prompt_context
    assert "Michael Frede" in pack.prompt_context
