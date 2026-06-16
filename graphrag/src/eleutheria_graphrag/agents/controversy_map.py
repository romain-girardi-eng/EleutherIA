"""ControversyMap assembly + serialisation (Scholar-RAG M3, ARCHITECTURE §3).

The dossier is one typed :class:`ControversyMap`: a list of
:class:`ControversyFrame`s ordered by RAW ``incident_edge_count`` (NO score, NO
DF-QuAD, NO base_strength/contestedness float — amputation 1), a pool of
standalone exegesis passages, and the planner patterns retrieval under-filled
(the completeness critic's denominator substrate).

Two responsibilities live here:

1. :func:`assemble_controversy_map` — drives ``find_debates`` then
   ``build_controversy_frame`` over each surfaced fault line, dedupes/orders the
   frames, and records coverage gaps. Frame assembly itself (the ``_en`` join,
   page-grounding, empty-debate fallback) is done by the M1
   ``build_controversy_frame`` tool; this is the orchestration that turns its
   per-frame output into the whole map.

2. :func:`serialize_controversy_frames` / :func:`render_controversy_frames_layer`
   — the ``## Controversy Frames`` context-pack layer (failure-map F2 fix):
   positions with holder + page, the dialectical links as ``A --critiques--> B``
   lines, and the contested passages (original + English, untruncated). The
   synthesis prompt is then STRUCTURALLY unable to be edge-blind.

VECTORLESS throughout (the underlying tools are KG adjacency + lexical + a
``has_translation`` join). Gated by ``ELEUTHERIA_SCHOLAR_RAG`` at the call site;
this module is import-safe and inert until invoked.
"""

from __future__ import annotations

import logging
from typing import Any

from eleutheria_graphrag.agents.state import (
    AnswerShape,
    ControversyFrame,
    ControversyMap,
    PassageRef,
)

logger = logging.getLogger(__name__)


# ── assembly ─────────────────────────────────────────────────────────────────


async def assemble_controversy_map(
    question: str,
    find_debates_tool: Any,
    build_frame_tool: Any,
    *,
    shape: AnswerShape = AnswerShape.SURVEY_OF_DEBATES,
    max_frames: int = 6,
    period_filter: list[str] | None = None,
) -> ControversyMap:
    """Drive find_debates -> build_controversy_frame over each fault line.

    Returns a fully-assembled :class:`ControversyMap` ordered by raw
    ``incident_edge_count`` (desc) with a ``provenance`` index of every
    contested passage. Frames that come back with neither a position nor a
    dialectical link are dropped and recorded as a coverage gap so the
    completeness critic (M5) has a real denominator.
    """
    cmap = ControversyMap(question_frame=question, shape=shape)

    debates_result = await find_debates_tool.execute(
        {
            "topic": question,
            "period_filter": period_filter,
            "limit": max_frames,
        }
    )
    debates = getattr(debates_result, "debates", []) or []

    seen_seeds: set[str] = set()
    for debate in debates:
        seed_id = getattr(debate, "debate_id", None) or (
            debate.get("debate_id") if isinstance(debate, dict) else None
        )
        if not seed_id or seed_id in seen_seeds:
            continue
        seen_seeds.add(seed_id)

        frame_result = await build_frame_tool.execute({"seed_id": seed_id})
        frame = getattr(frame_result, "frame", None)
        if frame is None:
            cmap.coverage_gaps.append(
                f"build_controversy_frame on {seed_id} returned no frame"
            )
            continue
        if not frame.positions and not frame.links:
            cmap.coverage_gaps.append(
                f"frame {seed_id} under-filled (no positions or links)"
            )
            continue

        cmap.frames.append(frame)
        for pref in frame.contested_passages:
            cmap.provenance.setdefault(pref.passage_id, pref)

    cmap.order_frames()
    cmap.frames = cmap.frames[:max_frames]
    _fold_author_passages_into_exegesis(cmap)
    return cmap


def _fold_author_passages_into_exegesis(cmap: ControversyMap) -> None:
    """Build the second passage pool the citation resolver expects (A3, GOAL-7).

    For each :class:`GroundedPosition` carrying a resolvable named ancient
    author, fold that author's already-fetched contested passages into
    ``cmap.exegesis_units`` so they are reachable as standalone exegesis even
    when a frame's holder is a modern scholar. Reuses passages already on the
    frames — NO new DB calls — and dedupes against every contested passage and
    against units already pooled.
    """
    contested_ids: set[str] = {
        pref.passage_id for frame in cmap.frames for pref in frame.contested_passages
    }
    pooled_ids: set[str] = {pref.passage_id for pref in cmap.exegesis_units}
    for frame in cmap.frames:
        authors = {
            (pos.holder or "").strip().lower()
            for pos in frame.positions
            if pos.holder_type == "ancient_author" and (pos.holder or "").strip()
        }
        if not authors:
            continue
        for pref in frame.contested_passages:
            pid = pref.passage_id
            if pid in pooled_ids:
                continue
            author = (pref.author or "").strip().lower()
            if author and any(author in a or a in author for a in authors):
                cmap.exegesis_units.append(pref)
                pooled_ids.add(pid)
    # exegesis is a standalone pool; do not re-add what is already contested.
    cmap.exegesis_units = [
        pref for pref in cmap.exegesis_units if pref.passage_id not in contested_ids
    ]


def attach_frames(
    cmap: ControversyMap, frames: list[ControversyFrame]
) -> ControversyMap:
    """Merge already-built frames into a map (subagent-distillation path, §3.3).

    Used when each ``build_controversy_frame`` ran as an isolated retrieval
    subagent and returned only a distilled :class:`ControversyFrame`; the lead
    never sees raw tool chatter. Dedupes by ``frame_id``, re-indexes provenance,
    re-orders by raw incident-edge count.
    """
    existing = {f.frame_id for f in cmap.frames}
    for frame in frames:
        if frame.frame_id in existing:
            continue
        existing.add(frame.frame_id)
        cmap.frames.append(frame)
        for pref in frame.contested_passages:
            cmap.provenance.setdefault(pref.passage_id, pref)
    cmap.order_frames()
    return cmap


# ── serialisation: the ## Controversy Frames context-pack layer (F2 fix) ─────


def _fmt_position_line(pos: Any) -> str:
    pub = pos.publication or "publication not recorded"
    page = f", {pos.page_grounding}" if pos.page_grounding else ""
    holder = pos.holder or pos.position_id
    claim = (pos.claim or "").strip()
    return f"  [P_{pos.position_id}] {holder} ({pub}{page}): {claim}"


def _fmt_link_line(link: Any) -> str:
    gloss = f"  ({link.gloss})" if getattr(link, "gloss", None) else ""
    return f"  P_{link.from_id} --{link.relation}--> P_{link.to_id}{gloss}"


def _fmt_passage_block(pref: PassageRef) -> list[str]:
    # FULL text — no truncation (failure-map F5). Original + English both.
    lang = (pref.language or "grc").upper()
    head = (
        f"  [passage_{pref.passage_id}] "
        f"{pref.author or 'unknown'}, {pref.work or ''} {pref.canonical_ref}".rstrip()
    )
    lines = [f"{head} —", f"    {lang}: {pref.original_text}"]
    if pref.english_text:
        lines.append(f"    EN: {pref.english_text}")
    return lines


def serialize_controversy_frames(frames: list[ControversyFrame]) -> str:
    """Render frames as the ``## Controversy Frames`` markdown layer.

    Edges are FIRST-CLASS rows (``A --opposes--> B``), so any prompt that
    consumes this layer is structurally unable to be edge-blind. Nothing is
    truncated (1M / 262k context makes truncation unnecessary).
    """
    if not frames:
        return ""
    blocks: list[str] = []
    for frame in frames:
        block = [
            f'### FRAME {frame.frame_id} — "{frame.title}"'
            + (f" (period: {frame.period})" if frame.period else "")
        ]
        block.append("POSITIONS:")
        if frame.positions:
            block.extend(_fmt_position_line(p) for p in frame.positions)
        else:
            block.append("  (no surfaced positions — frame is empty; flag it)")
        block.append("DIALECTIC (flat links, star-tolerant):")
        if frame.links:
            block.extend(_fmt_link_line(link) for link in frame.links)
        else:
            block.append("  (no surfaced dialectical edges — one-sided; flag it)")
        if frame.contested_passages:
            block.append("CONTESTED PRIMARY TEXT:")
            for pref in frame.contested_passages:
                block.extend(_fmt_passage_block(pref))
        blocks.append("\n".join(block))
    return "## Controversy Frames\n" + "\n\n".join(blocks)


def render_controversy_frames_layer(cmap: ControversyMap) -> str:
    """Full ``## Controversy Frames`` layer including standalone exegesis + gaps."""
    parts: list[str] = []
    frames_md = serialize_controversy_frames(cmap.frames)
    if frames_md:
        parts.append(frames_md)
    if cmap.exegesis_units:
        ex_lines = ["## Standalone Primary Text (not bound to a frame)"]
        for pref in cmap.exegesis_units:
            ex_lines.extend(_fmt_passage_block(pref))
        parts.append("\n".join(ex_lines))
    if cmap.coverage_gaps:
        gap_lines = ["## Coverage Gaps (planner named, retrieval under-filled)"]
        gap_lines.extend(f"  - {g}" for g in cmap.coverage_gaps)
        parts.append("\n".join(gap_lines))
    return "\n\n".join(parts)
