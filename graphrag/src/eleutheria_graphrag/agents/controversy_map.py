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
import re
from collections.abc import Mapping
from typing import Any

from eleutheria_graphrag.agents.prompt_budget import (
    EXEGESIS_SECTION_SHARE,
    EXEGESIS_TOKEN_FLOOR,
    NODE_DESCRIPTION_TOKEN_CAP,
    PASSAGE_TOKEN_FLOOR,
    POSITION_SECTION_SHARE,
    POSITION_TOKEN_FLOOR,
    SCHOLAR_QUOTE_TOKEN_CAP,
    LayerCaps,
    cap_description,
    cap_ladder,
    excerpt_within_budget,
    exegesis_token_cap,
    passage_token_cap,
    query_terms,
)
from eleutheria_graphrag.agents.relevance_triage import (
    TriageItem,
    exegesis_key,
    passage_key,
    position_key,
    prioritize,
)
from eleutheria_graphrag.agents.relevance_triage import snippet as triage_snippet
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


#: Maximum length of a rendered source-rank bracket. A rank is a disclosure
#: label, not a bibliography entry — the full curated string stays in the KG.
_SOURCE_RANK_MAX = 80

#: Qualifiers that must survive condensation: they are the whole point of the
#: disclosure and are usually curated AFTER the em-dash, in the part we cut.
_SOURCE_RANK_QUALIFIERS: tuple[str, ...] = ("not peer-reviewed", "unverified")


def condense_source_rank(rank: str | None) -> str:
    """Condense a curated ``metadata.source_rank`` into a short bracket label.

    ``"MA thesis — University of British Columbia …, December 2016; not
    peer-reviewed"`` → ``"MA thesis, not peer-reviewed"``; ``"online essay — not
    peer-reviewed [unverified]"`` → ``"online essay, not peer-reviewed,
    unverified"``. Purely deterministic and SUBTRACTIVE — it only ever drops
    words that were curated, never adds a rank the KG did not state. Returns
    ``""`` for a missing/blank rank, which the caller renders as NO bracket at
    all (unstated, never "established").
    """
    text = " ".join((rank or "").split())
    if not text:
        return ""
    head = re.split(r"\s+[—–]\s+|;|\(|\[", text, maxsplit=1)[0].strip(" ,.-")
    if not head:
        head = text
    lowered = text.lower()
    parts = [head]
    for qualifier in _SOURCE_RANK_QUALIFIERS:
        if qualifier in lowered and qualifier not in head.lower():
            parts.append(qualifier)
    label = ", ".join(parts)
    if len(label) > _SOURCE_RANK_MAX:
        label = label[: _SOURCE_RANK_MAX - 1].rstrip() + "…"
    return label


def _fmt_position_line(
    pos: Any,
    *,
    cap_tokens: int = NODE_DESCRIPTION_TOKEN_CAP,
    terms: frozenset[str] = frozenset(),
) -> str:
    pub = pos.publication or "publication not recorded"
    page = f", {pos.page_grounding}" if pos.page_grounding else ""
    holder = pos.holder or pos.position_id
    # SOURCE RANK (senior-scholar disclosure): a curated bibliographic rank on
    # the position or its publication node rides in brackets right after the
    # citation, so the synthesis can disclose it on first citation and never
    # weigh grey literature as a peer-reviewed authority. Absent ⇒ no bracket,
    # which the synthesis prompt reads as UNSTATED, never as "established".
    rank = condense_source_rank(getattr(pos, "source_rank", None))
    rank_note = f" [{rank}]" if rank else ""
    formulation_count = int(getattr(pos, "same_thesis_formulation_count", 1) or 1)
    formulation_note = (
        f" [same thesis in {formulation_count} formulations]"
        if formulation_count > 1
        else ""
    )
    if getattr(pos, "evidence_tier", "citable") != "citable":
        notice = getattr(pos, "evidence_notice", "") or (
            "FLAGGED SOURCE — discovery only; do not cite as evidence"
        )
        return (
            f"  [P_{pos.position_id}] {holder} ({pub}{page}){rank_note}"
            f"{formulation_note}: {notice}"
        )
    # A position's ``claim`` falls back to the node's KG ``description``, and
    # curated nodes carry whole-essay descriptions. Cap that contribution: it is
    # prose ABOUT the evidence, never a citable quotation — which is why the
    # fitter tightens THIS before it touches a contested primary passage.
    claim = cap_description((pos.claim or "").strip(), max(0, cap_tokens), terms=terms)
    line = (
        f"  [P_{pos.position_id}] {holder} ({pub}{page}){rank_note}"
        f"{formulation_note}: {claim}"
    )
    # Curated verbatim quotation: emitted WHOLE on its own tagged line, or not
    # at all — never through an excerpt window (a spliced quote is a fabricated
    # one). The synthesis prompt permits quoting a scholar's words only from a
    # QUOTE_VERBATIM line, so its absence keeps the paraphrase-only discipline.
    quote = (getattr(pos, "quotation", None) or "").strip()
    if quote and estimate_tokens(quote) <= SCHOLAR_QUOTE_TOKEN_CAP:
        line += f'\n    QUOTE_VERBATIM: "{quote}"'
    return line


def _fmt_link_line(link: Any) -> str:
    if not getattr(link, "attested", True):
        return (
            f"  UNATTESTED EDGE DEBT (discovery only; do not assert): "
            f"P_{link.from_id} --{link.relation}--> P_{link.to_id}"
        )
    gloss = f"  ({link.gloss})" if getattr(link, "gloss", None) else ""
    return f"  P_{link.from_id} --{link.relation}--> P_{link.to_id}{gloss}"


def _fmt_flagged_passage_line(pref: PassageRef) -> str:
    where = " ".join(
        part
        for part in (pref.author, pref.work, pref.canonical_ref)
        if (part or "").strip()
    )
    notice = pref.evidence_notice or "FLAGGED TEXT — discovery only; do not quote"
    return f"  [flagged_{pref.passage_id}] {where or pref.passage_id}: {notice}"


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
    terms: frozenset[str] = frozenset(),
    caps: LayerCaps | None = None,
) -> str:
    """Render frames as the ``## Controversy Frames`` markdown layer.

    Edges are FIRST-CLASS rows (``A --opposes--> B``), so any prompt that
    consumes this layer is structurally unable to be edge-blind. Passage blocks
    are emitted verbatim when they fit the per-passage cap and as a marked
    excerpt window when they do not; ``caps`` (see :class:`LayerCaps`) carries
    every per-section cap and keep-set — the whole-prompt budget's levers.
    """
    if not frames:
        return ""
    caps = caps or LayerCaps()
    blocks: list[str] = []
    for frame in frames:
        block = [
            f'### FRAME {frame.frame_id} — "{frame.title}"'
            + (f" (period: {frame.period})" if frame.period else "")
        ]
        positions = [
            pos
            for pos in frame.positions
            if caps.position_keep_ids is None
            or pos.position_id in caps.position_keep_ids
        ]
        block.append("POSITIONS:")
        if positions:
            block.extend(
                _fmt_position_line(p, cap_tokens=caps.position_tokens, terms=terms)
                for p in positions
            )
            shed = len(frame.positions) - len(positions)
            if shed:
                block.append(
                    f"  ({shed} further surfaced positions omitted for prompt budget)"
                )
        elif frame.positions:
            block.append(
                f"  ({len(frame.positions)} surfaced positions omitted for prompt "
                "budget)"
            )
        else:
            block.append("  (no surfaced positions — frame is empty; flag it)")
        # A link whose endpoint was shed would dangle; keep the dialectic honest.
        rendered_ids = {p.position_id for p in positions}
        links = [
            link
            for link in frame.links
            if caps.position_keep_ids is None
            or (link.from_id in rendered_ids and link.to_id in rendered_ids)
        ]
        if caps.link_limit is not None:
            links = links[: max(0, caps.link_limit)]
        block.append("DIALECTIC (flat links, star-tolerant):")
        if links:
            block.extend(_fmt_link_line(link) for link in links)
            dropped = len(frame.links) - len(links)
            if dropped:
                block.append(
                    f"  ({dropped} further dialectical edges omitted for prompt budget)"
                )
        elif frame.links:
            block.append(
                f"  ({len(frame.links)} dialectical edges omitted for prompt budget)"
            )
        else:
            block.append("  (no surfaced dialectical edges — one-sided; flag it)")
        rendered = [
            pref
            for pref in frame.contested_passages
            if caps.passage_keep_ids is None or pref.passage_id in caps.passage_keep_ids
        ]
        if rendered:
            block.append("CONTESTED PRIMARY TEXT:")
            for pref in rendered:
                block.extend(
                    _fmt_passage_block(
                        pref, cap_tokens=caps.passage_tokens, terms=terms
                    )
                )
        if frame.flagged_passages:
            block.append("DISCOVERY-ONLY TEXTS (NEVER PRIMARY EVIDENCE):")
            block.extend(
                _fmt_flagged_passage_line(pref) for pref in frame.flagged_passages
            )
        blocks.append("\n".join(block))
    return "## Controversy Frames\n" + "\n\n".join(blocks)


def _exegesis_units(cmap: ControversyMap) -> list[PassageRef]:
    """Standalone exegesis units, deduped against contested passages and ids.

    A passage already quoted inside a frame is never re-embedded here, so the
    map cannot pay for the same full text twice.
    """
    contested_ids = {
        pref.passage_id for frame in cmap.frames for pref in frame.contested_passages
    }
    seen: set[str] = set()
    out: list[PassageRef] = []
    for pref in cmap.exegesis_units:
        if pref.passage_id in contested_ids or pref.passage_id in seen:
            continue
        seen.add(pref.passage_id)
        out.append(pref)
    return out


def render_controversy_frames_layer(
    cmap: ControversyMap,
    *,
    caps: LayerCaps | None = None,
) -> str:
    """Full ``## Controversy Frames`` layer including standalone exegesis + gaps.

    Pure rendering: ``caps`` decides what is shown and how tightly each section
    is excerpted, and the :class:`ControversyMap` itself is never mutated — the
    quote-containment gate still verifies against the uncut originals.
    """
    caps = caps or LayerCaps()
    terms = query_terms(cmap.question_frame)
    parts: list[str] = []
    frames_md = serialize_controversy_frames(cmap.frames, terms=terms, caps=caps)
    if frames_md:
        parts.append(frames_md)
    exegesis = [
        pref
        for pref in _exegesis_units(cmap)
        if caps.exegesis_keep_ids is None or pref.passage_id in caps.exegesis_keep_ids
    ]
    if exegesis:
        ex_lines = ["## Standalone Primary Text (not bound to a frame)"]
        cap = (
            exegesis_token_cap()
            if caps.exegesis_tokens is None
            else caps.exegesis_tokens
        )
        for pref in exegesis:
            ex_lines.extend(_fmt_passage_block(pref, cap_tokens=cap, terms=terms))
        parts.append("\n".join(ex_lines))
    if cmap.coverage_gaps:
        gap_lines = ["## Coverage Gaps (planner named, retrieval under-filled)"]
        gap_lines.extend(f"  - {g}" for g in cmap.coverage_gaps)
        parts.append("\n".join(gap_lines))
    return "\n\n".join(parts)


# ── relevance triage: the fitter's scoreable units ───────────────────────────


def _passage_snippet(pref: PassageRef, kind: str) -> str:
    """What the triage model reads for one passage (English preferred).

    English first because the utility model judges pertinence far better on the
    translation than on polytonic Greek; the original is the fallback. This text
    NEVER re-enters the prompt — it exists only to be scored.
    """
    where = (
        f"{pref.author or 'unknown'}, {pref.work or ''} {pref.canonical_ref}".strip()
    )
    body = (pref.english_text or pref.original_text or "").strip()
    return f"{kind} — {where}: {body}"


def collect_triage_items(cmap: ControversyMap) -> list[TriageItem]:
    """The units the triage may reorder, in the fitter's own default order.

    Three pools, matching the three things the fitter sheds:

    * every position claim (the measured owner of the prompt blowout — a real
      run surfaced 4,389 of them);
    * every standalone exegesis unit;
    * contested passages BEYOND each frame's top-scored one. A frame's first
      passage is deliberately absent: it is the frame's primary anchor and must
      survive whatever the triage thinks, so it is never even scored.
    """
    items: list[TriageItem] = []
    seen: set[str] = set()

    def _add(key: str, text: str) -> None:
        if key in seen or not text.strip():
            return
        seen.add(key)
        items.append(TriageItem(key=key, snippet=triage_snippet(text)))

    for _fidx, pos in _position_order(cmap):
        holder = pos.holder or pos.position_id
        publication = pos.publication or "publication not recorded"
        _add(
            position_key(pos.position_id),
            f"scholarly position — {holder} ({publication}): {(pos.claim or '').strip()}",
        )
    protected = {
        frame.contested_passages[0].passage_id
        for frame in cmap.frames
        if frame.contested_passages
    }
    for pref in _budget_passage_order(cmap):
        if pref.passage_id in protected:
            continue
        _add(passage_key(pref.passage_id), _passage_snippet(pref, "contested passage"))
    for pref in _exegesis_units(cmap):
        _add(exegesis_key(pref.passage_id), _passage_snippet(pref, "primary passage"))
    return items


# ── whole-prompt budget fitting ──────────────────────────────────────────────


def _budget_passage_order(cmap: ControversyMap) -> list[PassageRef]:
    """Contested passages in packing priority order, deduped by id.

    Round-robin ACROSS frames (frames are already ordered by raw incident-edge
    count, passages within a frame quotable-Greek-first), so a prefix of this
    list always holds the top-scored passage of EVERY frame before it holds any
    frame's second passage — a squeezed budget starves every fault line evenly
    instead of emptying the last one.

    Standalone exegesis units are NOT here: they are supporting text with their
    own section budget, shed before contested primary evidence is touched.
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
    return ordered


def _position_order(cmap: ControversyMap) -> list[tuple[int, Any]]:
    """``(frame_index, position)`` round-robin across frames, deduped by id."""
    ordered: list[tuple[int, Any]] = []
    seen: set[str] = set()
    depth = max((len(f.positions) for f in cmap.frames), default=0)
    for i in range(depth):
        for fidx, frame in enumerate(cmap.frames):
            if i >= len(frame.positions):
                continue
            pos = frame.positions[i]
            if pos.position_id in seen:
                continue
            seen.add(pos.position_id)
            ordered.append((fidx, pos))
    return ordered


def _dialectic_tokens(
    cmap: ControversyMap,
    *,
    cap: int,
    keep_ids: frozenset[str] | None,
    terms: frozenset[str],
) -> int:
    """Token cost of the position lines + the link rows they still support."""
    total = 0
    for frame in cmap.frames:
        positions = [
            pos
            for pos in frame.positions
            if keep_ids is None or pos.position_id in keep_ids
        ]
        total += estimate_tokens(
            *[_fmt_position_line(pos, cap_tokens=cap, terms=terms) for pos in positions]
        )
        rendered = {pos.position_id for pos in positions}
        total += estimate_tokens(
            *[
                _fmt_link_line(link)
                for link in frame.links
                if keep_ids is None
                or (link.from_id in rendered and link.to_id in rendered)
            ]
        )
    return total


def _passage_block_tokens(pref: PassageRef, *, cap: int, terms: frozenset[str]) -> int:
    return estimate_tokens(
        "\n".join(_fmt_passage_block(pref, cap_tokens=cap, terms=terms))
    )


def _fit_dialectic(
    cmap: ControversyMap,
    budget: int,
    terms: frozenset[str],
    relevance: Mapping[str, float] | None = None,
) -> tuple[int, frozenset[str] | None, int]:
    """Fit position claims + link rows into their section budget.

    THE measured owner of the prod blowout: a hub debate node grounds every link
    endpoint as a position, and each position's ``claim`` (KG ``stance`` /
    ``conclusion`` / ``description``) was capped only per-item at 2000 tokens —
    285 of them cost 576k, entirely outside the fitter, while the contested
    primary text it crowded out was cut to a single passage.

    Tightens the per-claim cap down :func:`cap_ladder` first; only with the cap
    at :data:`POSITION_TOKEN_FLOOR` and the section still over does it SHED
    positions, round-robin across frames so no fault line goes voiceless first.
    With triage ``relevance`` scores present the shed step keeps the
    highest-scoring claims and drops the lowest ones first, the round-robin order
    surviving as the tiebreak within a score band.
    Returns ``(cap, keep_ids_or_None, tokens)``.
    """
    ladder = cap_ladder(NODE_DESCRIPTION_TOKEN_CAP, POSITION_TOKEN_FLOOR)
    for cap in ladder:
        cost = _dialectic_tokens(cmap, cap=cap, keep_ids=None, terms=terms)
        if cost <= budget:
            return cap, None, cost
    cap = ladder[-1]
    incident: dict[str, list[Any]] = {}
    for frame in cmap.frames:
        for link in frame.links:
            incident.setdefault(link.from_id, []).append(link)
            incident.setdefault(link.to_id, []).append(link)
    keep: set[str] = set()
    used = 0
    for _fidx, pos in prioritize(
        _position_order(cmap),
        lambda pair: position_key(pair[1].position_id),
        relevance,
    ):
        pid = pos.position_id
        line = _fmt_position_line(pos, cap_tokens=cap, terms=terms)
        enabled = [
            link
            for link in incident.get(pid, [])
            if {link.from_id, link.to_id} <= (keep | {pid})
        ]
        delta = estimate_tokens(line, *[_fmt_link_line(link) for link in enabled])
        if keep and used + delta > budget:
            continue
        keep.add(pid)
        used += delta
    return cap, frozenset(keep), used


def _fit_exegesis(
    cmap: ControversyMap,
    budget: int,
    terms: frozenset[str],
    relevance: Mapping[str, float] | None = None,
) -> tuple[int, frozenset[str] | None, int]:
    """Fit standalone exegesis into its section budget (tighten, then shed).

    Exegesis is SUPPORTING primary text, not the fault line's contested
    evidence, so it gives way first: the per-unit cap walks down to
    :data:`EXEGESIS_TOKEN_FLOOR` and surplus units are then dropped whole —
    lowest triage score first when the stage ran.
    """
    default_cap = exegesis_token_cap()
    units = _exegesis_units(cmap)
    if not units:
        return default_cap, None, 0
    ladder = cap_ladder(default_cap, EXEGESIS_TOKEN_FLOOR)
    for cap in ladder:
        cost = sum(_passage_block_tokens(p, cap=cap, terms=terms) for p in units)
        if cost <= budget:
            return cap, None, cost
    cap = ladder[-1]
    keep: set[str] = set()
    used = 0
    for pref in prioritize(
        units, lambda pref: exegesis_key(pref.passage_id), relevance
    ):
        cost = _passage_block_tokens(pref, cap=cap, terms=terms)
        if used + cost > budget:
            continue
        keep.add(pref.passage_id)
        used += cost
    return cap, frozenset(keep), used


def _section_tokens(
    cmap: ControversyMap, caps: LayerCaps, terms: frozenset[str]
) -> dict[str, int]:
    """Final per-section accounting, for the over-budget warning."""
    passage_cap = (
        passage_token_cap() if caps.passage_tokens is None else caps.passage_tokens
    )
    exegesis_cap = (
        exegesis_token_cap() if caps.exegesis_tokens is None else caps.exegesis_tokens
    )
    contested = sum(
        _passage_block_tokens(pref, cap=passage_cap, terms=terms)
        for frame in cmap.frames
        for pref in frame.contested_passages
        if caps.passage_keep_ids is None or pref.passage_id in caps.passage_keep_ids
    )
    exegesis = sum(
        _passage_block_tokens(pref, cap=exegesis_cap, terms=terms)
        for pref in _exegesis_units(cmap)
        if caps.exegesis_keep_ids is None or pref.passage_id in caps.exegesis_keep_ids
    )
    dialectic = _dialectic_tokens(
        cmap, cap=caps.position_tokens, keep_ids=caps.position_keep_ids, terms=terms
    )
    gaps = estimate_tokens(*[f"  - {g}" for g in cmap.coverage_gaps])
    return {
        "dialectic": dialectic,
        "contested_passages": contested,
        "exegesis": exegesis,
        "coverage_gaps": gaps,
    }


def _relevance_passage_order(
    cmap: ControversyMap, relevance: Mapping[str, float] | None
) -> list[PassageRef]:
    """:func:`_budget_passage_order`, re-prioritised by triage score.

    INVARIANT — each frame's TOP-SCORED contested passage keeps its place at the
    head of the list whatever the triage says: it is the frame's primary anchor,
    and a fault line quoted with no primary text is a worse answer than one
    quoted with a slightly less pertinent passage. Only the tail (every frame's
    second passage onward) is reordered.
    """
    ordered = _budget_passage_order(cmap)
    if not relevance:
        return ordered
    anchors = {
        frame.contested_passages[0].passage_id
        for frame in cmap.frames
        if frame.contested_passages
    }
    head = [pref for pref in ordered if pref.passage_id in anchors]
    tail = [pref for pref in ordered if pref.passage_id not in anchors]
    return head + prioritize(tail, lambda pref: passage_key(pref.passage_id), relevance)


def fit_controversy_frames_layer(
    cmap: ControversyMap,
    budget_tokens: int,
    *,
    relevance: Mapping[str, float] | None = None,
) -> tuple[str, dict[str, int]]:
    """Render the frames layer inside ``budget_tokens``, primary text LAST to go.

    The reduction sequence is ordered by scholarly value — contested PRIMARY
    TEXT is the core evidence of this platform, so prose ABOUT the evidence
    yields first:

    1. **Dialectic section** (position claims + link rows, ≤
       :data:`POSITION_SECTION_SHARE` of the budget) — per-claim cap tightened
       down the ladder, then surplus positions shed round-robin across frames.
    2. **Standalone exegesis** (≤ :data:`EXEGESIS_SECTION_SHARE`) — per-unit cap
       tightened to :data:`EXEGESIS_TOKEN_FLOOR`, then units shed whole.
    3. **Contested passages** get everything left: their per-passage cap is
       tightened gradually, and only when even the floor cap will not fit are
       whole passages dropped — round-robin, so the top-scored passage of every
       frame survives before any frame gets a second one.

    ``relevance`` is the OPTIONAL side dict of triage scores
    (:mod:`eleutheria_graphrag.agents.relevance_triage`), keyed by the namespaced
    item ids. It changes NOTHING about the sequence above — only WHICH items go
    first inside each shed step: with scores present the lowest-scoring items are
    the ones dropped. ``None`` (the default, and the fallback whenever the triage
    stage is off or failed) keeps the lexical/round-robin ordering exactly.

    Never mutates ``cmap``: every reduction is a :class:`LayerCaps` rendering
    instruction, so the quote-containment gate keeps verifying against the uncut
    ``PassageRef.original_text``.

    Returns ``(layer_markdown, stats)``.
    """
    budget_tokens = max(0, budget_tokens)
    terms = query_terms(cmap.question_frame)

    pos_cap, pos_keep, _pos_tokens = _fit_dialectic(
        cmap, int(budget_tokens * POSITION_SECTION_SHARE), terms, relevance
    )
    ex_cap, ex_keep, _ex_tokens = _fit_exegesis(
        cmap, int(budget_tokens * EXEGESIS_SECTION_SHARE), terms, relevance
    )

    ordered = _relevance_passage_order(cmap, relevance)
    total = len(ordered)
    base = LayerCaps(
        position_tokens=pos_cap,
        position_keep_ids=pos_keep,
        exegesis_tokens=ex_cap,
        exegesis_keep_ids=ex_keep,
        passage_keep_ids=frozenset(),
    )
    scaffold_tokens = estimate_tokens(render_controversy_frames_layer(cmap, caps=base))
    remaining = max(0, budget_tokens - scaffold_tokens)

    passage_cap = passage_token_cap()
    keep: frozenset[str] = frozenset()
    if total:

        def _fill(cap: int) -> frozenset[str]:
            kept: list[str] = []
            used = 0
            for pref in ordered:
                cost = _passage_block_tokens(pref, cap=cap, terms=terms)
                if kept and used + cost > remaining:
                    break
                kept.append(pref.passage_id)
                used += cost
            return frozenset(kept)

        for cap in cap_ladder(passage_token_cap(), PASSAGE_TOKEN_FLOOR):
            passage_cap, keep = cap, _fill(cap)
            if len(keep) == total:
                break

    caps = LayerCaps(
        passage_tokens=passage_cap,
        passage_keep_ids=None if len(keep) == total else keep,
        position_tokens=pos_cap,
        position_keep_ids=pos_keep,
        exegesis_tokens=ex_cap,
        exegesis_keep_ids=ex_keep,
    )
    layer = render_controversy_frames_layer(cmap, caps=caps)
    layer_tokens = estimate_tokens(layer)

    exegesis_total = len(_exegesis_units(cmap))
    stats = {
        "passages_total": total,
        "passages_kept": len(keep),
        "cap_tokens": passage_cap,
        "exegesis_total": exegesis_total,
        "exegesis_kept": exegesis_total if ex_keep is None else len(ex_keep),
        "exegesis_cap_tokens": ex_cap,
        "positions_total": sum(len(f.positions) for f in cmap.frames),
        "positions_kept": (
            sum(len(f.positions) for f in cmap.frames)
            if pos_keep is None
            else len(pos_keep)
        ),
        "position_cap_tokens": pos_cap,
        "tokens": layer_tokens,
        "budget_tokens": budget_tokens,
    }
    if budget_tokens and layer_tokens > budget_tokens * 1.1:
        sections = _section_tokens(cmap, caps, terms)
        worst = max(sections, key=lambda name: sections[name])
        # A section that will not shrink is a BUG SIGNAL (an unbudgeted field),
        # not an accepted outcome — name it so the next one is found in one log.
        logger.warning(
            "controversy map layer refused to fit: %d tok vs budget %d "
            "(sections: %s; largest=%s). An unbudgeted section is leaking.",
            layer_tokens,
            budget_tokens,
            sections,
            worst,
        )
    return layer, stats
