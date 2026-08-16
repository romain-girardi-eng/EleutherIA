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
import os
from typing import Any

from eleutheria_graphrag.agents.prompt_budget import (
    NODE_DESCRIPTION_TOKEN_CAP,
    PASSAGE_TOKEN_FLOOR,
    cap_description,
    excerpt_within_budget,
    passage_token_cap,
    query_terms,
)
from eleutheria_graphrag.agents.state import (
    AnswerShape,
    ControversyFrame,
    ControversyMap,
    PassageRef,
)
from eleutheria_graphrag.services.token_budget import estimate_tokens

logger = logging.getLogger(__name__)

# F3: the per-frame contested-passage budget handed to build_controversy_frame.
# Raised 12 -> 18 so MORE quotable-Greek primary passages survive retrieval into
# the map (the corpus holds ~560 Epictetus passages; only ~1 was reaching the
# prose). build_controversy_frame round-robins by author and ranks quotable-Greek
# first WITHIN each author group, so a larger budget surfaces ≥2 quotable-Greek
# passages per dominant fault line instead of starving the holder's own author.
# ``ELEUTHERIA_SCHOLAR_CONTESTED_BUDGET`` overrides (clamped to [6, 24]).
_CONTESTED_PASSAGE_BUDGET_DEFAULT = 18


def _contested_passage_budget() -> int:
    """Per-frame contested-passage budget (F3); clamped to [6, 24]."""
    raw = os.getenv("ELEUTHERIA_SCHOLAR_CONTESTED_BUDGET")
    if raw:
        try:
            return max(6, min(24, int(raw)))
        except ValueError:
            pass
    return _CONTESTED_PASSAGE_BUDGET_DEFAULT


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

        frame_result = await build_frame_tool.execute(
            {"seed_id": seed_id, "max_passages": _contested_passage_budget()}
        )
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
    # Observability (GOAL-7): how many primary passages actually reached the
    # synthesis, broken down by author, so a "no primary text quoted" answer can
    # be traced to retrieval (empty pool) vs synthesis (pool ignored).
    _all_passages = [
        pref for frame in cmap.frames for pref in frame.contested_passages
    ] + list(cmap.exegesis_units)
    _by_author: dict[str, int] = {}
    for _p in _all_passages:
        _by_author[(_p.author or "?").strip()] = (
            _by_author.get((_p.author or "?").strip(), 0) + 1
        )
    logger.info(
        "ControversyMap assembled: %d frames, %d contested + %d exegesis passages; "
        "authors=%s",
        len(cmap.frames),
        sum(len(f.contested_passages) for f in cmap.frames),
        len(cmap.exegesis_units),
        _by_author,
    )
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


def _fmt_position_line(pos: Any, *, terms: frozenset[str] = frozenset()) -> str:
    pub = pos.publication or "publication not recorded"
    page = f", {pos.page_grounding}" if pos.page_grounding else ""
    holder = pos.holder or pos.position_id
    # A position's ``claim`` falls back to the node's KG ``description``, and
    # curated nodes carry whole-essay descriptions. Cap that contribution: it is
    # prose ABOUT the evidence, never a citable quotation.
    claim = cap_description(
        (pos.claim or "").strip(), NODE_DESCRIPTION_TOKEN_CAP, terms=terms
    )
    return f"  [P_{pos.position_id}] {holder} ({pub}{page}): {claim}"


def _fmt_link_line(link: Any) -> str:
    gloss = f"  ({link.gloss})" if getattr(link, "gloss", None) else ""
    return f"  P_{link.from_id} --{link.relation}--> P_{link.to_id}{gloss}"


def _fmt_passage_block(
    pref: PassageRef,
    *,
    cap_tokens: int | None = None,
    terms: frozenset[str] = frozenset(),
) -> list[str]:
    """One bilingual passage block, capped by EXCERPT SELECTION.

    Original + English are each fitted to ``cap_tokens`` (default
    :func:`passage_token_cap`) by :func:`excerpt_within_budget`: a passage that
    fits is emitted verbatim and untruncated (failure-map F5 intact), while a
    full-book passage node (80-123k chars) contributes its relevant lines ±
    context with the elision marked. Cutting is at sentence/line boundaries
    only, so a quotation is never severed mid-phrase.
    """
    cap = passage_token_cap() if cap_tokens is None else max(0, cap_tokens)
    lang = (pref.language or "grc").upper()
    head = (
        f"  [passage_{pref.passage_id}] "
        f"{pref.author or 'unknown'}, {pref.work or ''} {pref.canonical_ref}".rstrip()
    )
    original, orig_excerpted = excerpt_within_budget(
        pref.original_text, cap, terms=terms
    )
    lines = [f"{head} —", f"    {lang}: {original}"]
    if pref.english_text:
        english, _ = excerpt_within_budget(pref.english_text, cap, terms=terms)
        lines.append(f"    EN: {english}")
    if orig_excerpted:
        lines.append(
            "    (excerpt of a longer passage — quote only what is shown above)"
        )
    return lines


def serialize_controversy_frames(
    frames: list[ControversyFrame],
    *,
    cap_tokens: int | None = None,
    terms: frozenset[str] = frozenset(),
    keep_ids: set[str] | None = None,
) -> str:
    """Render frames as the ``## Controversy Frames`` markdown layer.

    Edges are FIRST-CLASS rows (``A --opposes--> B``), so any prompt that
    consumes this layer is structurally unable to be edge-blind. Passage blocks
    are emitted verbatim when they fit the per-passage cap and as a marked
    excerpt window when they do not; ``keep_ids`` (when given) restricts which
    passages are rendered at all — that is the whole-prompt budget's lever.
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
            block.extend(_fmt_position_line(p, terms=terms) for p in frame.positions)
        else:
            block.append("  (no surfaced positions — frame is empty; flag it)")
        block.append("DIALECTIC (flat links, star-tolerant):")
        if frame.links:
            block.extend(_fmt_link_line(link) for link in frame.links)
        else:
            block.append("  (no surfaced dialectical edges — one-sided; flag it)")
        rendered = [
            pref
            for pref in frame.contested_passages
            if keep_ids is None or pref.passage_id in keep_ids
        ]
        if rendered:
            block.append("CONTESTED PRIMARY TEXT:")
            for pref in rendered:
                block.extend(
                    _fmt_passage_block(pref, cap_tokens=cap_tokens, terms=terms)
                )
        blocks.append("\n".join(block))
    return "## Controversy Frames\n" + "\n\n".join(blocks)


def render_controversy_frames_layer(
    cmap: ControversyMap,
    *,
    cap_tokens: int | None = None,
    keep_ids: set[str] | None = None,
) -> str:
    """Full ``## Controversy Frames`` layer including standalone exegesis + gaps.

    Standalone exegesis units are DEDUPED against the contested passages: a
    passage already quoted inside a frame is never re-embedded here, so the map
    cannot pay for the same full text twice.
    """
    terms = query_terms(cmap.question_frame)
    parts: list[str] = []
    frames_md = serialize_controversy_frames(
        cmap.frames, cap_tokens=cap_tokens, terms=terms, keep_ids=keep_ids
    )
    if frames_md:
        parts.append(frames_md)
    contested_ids = {
        pref.passage_id for frame in cmap.frames for pref in frame.contested_passages
    }
    exegesis = [
        pref
        for pref in cmap.exegesis_units
        if pref.passage_id not in contested_ids
        and (keep_ids is None or pref.passage_id in keep_ids)
    ]
    if exegesis:
        ex_lines = ["## Standalone Primary Text (not bound to a frame)"]
        seen: set[str] = set()
        for pref in exegesis:
            if pref.passage_id in seen:
                continue
            seen.add(pref.passage_id)
            ex_lines.extend(
                _fmt_passage_block(pref, cap_tokens=cap_tokens, terms=terms)
            )
        parts.append("\n".join(ex_lines))
    if cmap.coverage_gaps:
        gap_lines = ["## Coverage Gaps (planner named, retrieval under-filled)"]
        gap_lines.extend(f"  - {g}" for g in cmap.coverage_gaps)
        parts.append("\n".join(gap_lines))
    return "\n\n".join(parts)


# ── whole-prompt budget fitting ──────────────────────────────────────────────


def _budget_passage_order(cmap: ControversyMap) -> list[PassageRef]:
    """Passages in packing priority order, deduped by id.

    Round-robin ACROSS frames (frames are already ordered by raw incident-edge
    count, passages within a frame quotable-Greek-first), so a squeezed budget
    starves every fault line evenly instead of emptying the last one. Standalone
    exegesis units follow, since a frame-bound passage is the better anchor.
    """
    ordered: list[PassageRef] = []
    seen: set[str] = set()
    depth = max((len(f.contested_passages) for f in cmap.frames), default=0)
    for i in range(depth):
        for frame in cmap.frames:
            if i >= len(frame.contested_passages):
                continue
            pref = frame.contested_passages[i]
            if pref.passage_id in seen:
                continue
            seen.add(pref.passage_id)
            ordered.append(pref)
    for pref in cmap.exegesis_units:
        if pref.passage_id in seen:
            continue
        seen.add(pref.passage_id)
        ordered.append(pref)
    return ordered


def fit_controversy_frames_layer(
    cmap: ControversyMap, budget_tokens: int
) -> tuple[str, dict[str, int]]:
    """Render the frames layer inside ``budget_tokens``.

    Two levers, applied in order:

    1. **Per-passage cap** — every passage block is capped by excerpt selection,
       tightened below :data:`PASSAGE_TOKEN_CAP_DEFAULT` (never below
       :data:`PASSAGE_TOKEN_FLOOR`) when many passages must share the budget.
    2. **Passage selection** — with the cap at its floor and the budget still
       short, the lowest-priority passages are dropped whole rather than every
       passage being shaved into an unquotable stub. At least one passage
       always survives when the map has any.

    Returns ``(layer_markdown, stats)`` where ``stats`` carries
    ``passages_total`` / ``passages_kept`` / ``cap_tokens`` / ``tokens`` for the
    composition log.
    """
    ordered = _budget_passage_order(cmap)
    total = len(ordered)
    # Structural cost first: headers, positions, links, gaps — everything except
    # the passage bodies. The remainder is what the primary text may spend.
    scaffold = render_controversy_frames_layer(cmap, cap_tokens=0, keep_ids=set())
    scaffold_tokens = estimate_tokens(scaffold)
    remaining = max(0, budget_tokens - scaffold_tokens)

    if not total:
        return scaffold, {
            "passages_total": 0,
            "passages_kept": 0,
            "cap_tokens": 0,
            "tokens": scaffold_tokens,
        }

    terms = query_terms(cmap.question_frame)
    default_cap = passage_token_cap()

    def _fill(cap: int) -> tuple[set[str], int]:
        keep: set[str] = set()
        used = 0
        for pref in ordered:
            block = "\n".join(_fmt_passage_block(pref, cap_tokens=cap, terms=terms))
            cost = estimate_tokens(block)
            if keep and used + cost > remaining:
                break
            keep.add(pref.passage_id)
            used += cost
        return keep, used

    # Try the full per-passage cap first: most maps fit it outright, and then
    # NOTHING is excerpted beyond the source cap. Only when the whole set does
    # not fit do we tighten the cap (never below the floor) and, if that is
    # still short, drop the lowest-priority passages whole.
    cap = default_cap
    keep, _used = _fill(cap)
    if len(keep) < total:
        # Original + English each cost up to ``cap``, hence the 2x.
        cap = max(PASSAGE_TOKEN_FLOOR, min(default_cap, remaining // (2 * total)))
        keep, _used = _fill(cap)

    layer = render_controversy_frames_layer(cmap, cap_tokens=cap, keep_ids=keep)
    return layer, {
        "passages_total": total,
        "passages_kept": len(keep),
        "cap_tokens": cap,
        "tokens": estimate_tokens(layer),
    }
