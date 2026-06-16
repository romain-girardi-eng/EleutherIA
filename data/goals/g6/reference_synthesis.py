"""Reference draft — Dialectical Scholarly Synthesis (G6 Scholar-RAG core).

BLUEPRINT ARTIFACT — NOT WIRED INTO THE LIVE TREE.

This file is the reference implementation of the synthesis module that REPLACES
the facet template + DraftClaimLedger->build_render_prompt->RenderGroundedAnswer
chain (graph_nodes.py L580-680 prompt, L3575-3733 fallback template, L4169+ 220-char
pastes, L4250-4380 facet claim region, L5189-5497 ledger->prompt). It runs ONE LLM
call over a ``ControversyMap`` and emits cite-as-you-write prose; a deterministic
post-pass parses the inline markers back into a ``ClaimLedgerItem[]`` so the
provenance ledger becomes a byproduct of the prose, not its input.

Import paths and the exact pydantic models (ControversyMap, ControversyFrame,
GroundedPosition, DialecticalLink, PassageRef) are the ones defined by stage M3 in
``agents/state.py``; here they are referenced by name. ``SCHOLAR_SYNTHESIS_MODEL``
resolution and the KIMI temperature clamp live in ``services/llm_service.py`` (M6).

The serialiser, the prompt, the call, and the ledger-extractor are all in this file
so a reviewer can read the whole synthesis seam in one place. In the live tree they
land as: ``DialecticalSynthesis`` graph node + ``DIALECTICAL_SYNTHESIS_PROMPT``
constant + ``build_provenance_ledger`` post-pass.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# In the live tree these come from agents.state (M3) and services.llm_service (M6).
# Imported here by name only; this artifact is not executed.
from eleutheria_graphrag.agents.state import (  # type: ignore[import-not-found]
    ClaimLedgerItem,
    ClaimStatus,
    ControversyFrame,
    ControversyMap,
    GroundedPosition,
    PassageRef,
    RAGState,
)
from eleutheria_graphrag.services.llm_service import (  # type: ignore[import-not-found]
    LLMService,
    resolve_scholar_synthesis_model,  # new in M6
)

# ----------------------------------------------------------------------------
# 1. The synthesis prompt (replaces RENDER_ANSWER_PROMPT, graph_nodes.py:580-680)
# ----------------------------------------------------------------------------

DIALECTICAL_SYNTHESIS_SYSTEM = """\
You are a historian of ancient philosophy writing for a specialist audience \
(Cambridge-Companion register). You reason DIALECTICALLY over a CONTROVERSY MAP: a \
structured record of contending scholarly positions and the primary texts they \
fight over.

You attribute every interpretive claim to a named scholar with a page reference. \
You ground every claim about an ancient author in a quoted primary passage. You hedge \
where the evidence underdetermines the question. You never adjudicate a dispute the \
field has not settled.

Modern categories — "libertarian free will", "compatibilism", "incompatibilism", \
"hard/soft determinism", "the will" as a faculty, "the free-will problem", \
"indeterminist" — are scholarly CHARACTERISATIONS. They may appear ONLY inside an \
attributed position ("what Bobzien terms…", "on Frede's reading…"), NEVER asserted \
in your own voice as ancient fact.

You never write Greek or Latin that is not present verbatim in the provided passages. \
If a phrase is not in the map, paraphrase it in English instead. You quote contested \
primary text in the original AND English at the point the scholars argue over it.

CITE AS YOU WRITE. Every interpretive sentence carries an inline marker drawn from \
the map you are given, using exactly these forms:
  [P_<id>: <holder>, <publication+page>]   for an attributed position
  [edge: <relation> P_<from>-><P_to>]      for a dialectical link you invoke
  [passage_<id>: <author>, <ref>]          for a quoted/cited primary passage
Use only ids that appear in the map. Never invent an id.\
"""

# The reasoning steps are MANDATED in the user prompt so they drive reasoning_content
# on K2.x (the model weighs before writing).
DIALECTICAL_SYNTHESIS_TEMPLATE = """\
{map_markdown}

------------------------------------------------------------------------------
REASON (this becomes your private scratch; it is not the answer):

1. THESIS SELECTION. From the frames, state the SHAPE of the answer — which fault \
lines actually dominate the live scholarship — NOT a doctrinal verdict.
2. MAP THE FAULT LINES. Per frame: name the >=2 opposing positions and the edge that \
opposes them. A frame with only one surfaced position is incomplete — say so.
3. LOCATE THE PRIMARY ANCHOR. Per position, find the dossier passage it argues over. \
If none, mark "interpretation without surfaced primary grounding" and hedge harder.
4. WEIGH, DON'T DECIDE — AND DETECT TALKING-PAST. Note where positions GENUINELY \
conflict vs. talk past each other (different object of choice, different dating of \
"the will", different sense of the term). Note who responds_to whom. DO NOT pick a \
winner.
5. CHECK ANACHRONISM. Flag every modern label; voice it as "what X calls…", never \
"the Stoics held compatibilism."
6. PLAN STRUCTURE FROM THE FRAMES PRESENT — one movement per fault line for a \
survey; chronological for a genealogy; point-by-point for a comparison. Never a fixed \
Definition/Textual-Basis/Counterpoint template.

------------------------------------------------------------------------------
WRITE the scholarly answer ({shape}):

- Open with a THESIS SENTENCE that answers the actual question: {question}
- One movement per fault line; adaptive headings DERIVED FROM FRAME TITLES.
- Every interpretive sentence carries an inline citation marker AS YOU WRITE IT.
- Quote contested primary text in original + English where the scholars argue over it.
- Hedge with the field's own markers ("Bobzien argues…, though Frede contends…").
- Close with what remains GENUINELY OPEN.
{coverage_note}\
"""


# ----------------------------------------------------------------------------
# 2. Map serialiser — turns the typed ControversyMap into the prompt's markdown
#    (edges are FIRST-CLASS rows; no truncation; original+English passages)
# ----------------------------------------------------------------------------


def _fmt_position(p: GroundedPosition) -> str:
    pub = p.publication or "publication not recorded"
    page = f", {p.page_grounding}" if p.page_grounding else ""
    return f"  [P_{p.position_id}]  {p.holder} ({pub}{page}):\n              {p.claim}"


def _fmt_passage(pr: PassageRef) -> str:
    # FULL text — no truncate_text. Original + English both emitted.
    lines = [
        f"  [passage_{pr.passage_id}] {pr.author}, {pr.work} {pr.canonical_ref} —",
        f"    {pr.language.upper() if pr.language else 'GR'}: {pr.original_text}",
    ]
    if pr.english_text:
        lines.append(f"    EN: {pr.english_text}")
    return "\n".join(lines)


def _fmt_frame(frame: ControversyFrame) -> str:
    blocks = [f'## FRAME {frame.frame_id} — "{frame.title}" (period: {frame.period})']
    blocks.append("POSITIONS:")
    blocks.extend(_fmt_position(p) for p in frame.positions)
    blocks.append("DIALECTIC (flat links, star-tolerant):")
    if frame.links:
        for link in frame.links:
            gloss = f"        ({link.gloss})" if link.gloss else ""
            blocks.append(
                f"  P_{link.from_id}  --{link.relation}-->  "
                f"P_{link.to_id}{gloss}"
            )
    else:
        blocks.append("  (no surfaced dialectical edges — frame is one-sided; flag it)")
    if frame.contested_passages:
        blocks.append("CONTESTED PRIMARY TEXT:")
        blocks.extend(_fmt_passage(pr) for pr in frame.contested_passages)
    return "\n".join(blocks)


def serialize_controversy_map(cmap: ControversyMap) -> str:
    """Render the ControversyMap as the structured markdown the prompt consumes.

    This is the ``## Controversy Frames`` layer (M3) hoisted into the synthesis
    input. Edges are explicit rows, so the prompt is structurally unable to be
    edge-blind. Nothing is truncated.
    """
    out = [f"## QUESTION  {cmap.question_frame}   (detected shape: {cmap.shape})", ""]
    # frames already ordered by incident_edge_count desc (raw count — NO score)
    for frame in cmap.frames:
        out.append(_fmt_frame(frame))
        out.append("")
    if cmap.exegesis_units:
        out.append("## STANDALONE PRIMARY TEXT (not bound to a frame):")
        out.extend(_fmt_passage(pr) for pr in cmap.exegesis_units)
        out.append("")
    if cmap.coverage_gaps:
        out.append("## COVERAGE GAPS  (planner named, retrieval under-filled):")
        out.extend(f"  - {g}" for g in cmap.coverage_gaps)
    return "\n".join(out)


# ----------------------------------------------------------------------------
# 3. The synthesis call (ONE LLM call, reasoning_content enabled)
# ----------------------------------------------------------------------------


@dataclass
class SynthesisResult:
    prose: str
    reasoning_trace: str  # reasoning_content, streamed as "thinking…" by the heartbeat
    model_used: str
    ledger: list[ClaimLedgerItem]  # byproduct, parsed from the prose (build_provenance_ledger)


async def synthesize_dialectical(
    state: RAGState,
    cmap: ControversyMap,
    llm: LLMService,
    *,
    max_tokens: int = 8000,  # >=5000 mandatory: reasoning eats the budget
    budget_tier: str = "standard",
) -> SynthesisResult:
    """Core G6 synthesis. Reason over the ControversyMap, emit cite-as-you-write prose.

    Signature is the live ``DialecticalSynthesis.run`` body. Inputs:
      - ``cmap``: the dossier (frames + exegesis units + coverage gaps), fully grounded,
        full bilingual passages, page-grounded positions, raw incident_edge_count order.
      - ``llm``: the shared LLMService; provider chosen by SCHOLAR_SYNTHESIS_MODEL.
    Output: prose + reasoning trace + the extracted ledger.

    No facet template, no pre-built ledger feeds this. The prose IS the source of
    truth; ``build_provenance_ledger`` indexes it afterwards.
    """
    provider, model_id = resolve_scholar_synthesis_model()  # M6 resolver

    coverage_note = ""
    if cmap.coverage_gaps:
        coverage_note = (
            "\n- One frame or more was thinly retrieved (see COVERAGE GAPS). State that "
            "coverage limit explicitly in prose; do not pad it with unrelated material."
        )

    map_markdown = serialize_controversy_map(cmap)
    user_prompt = DIALECTICAL_SYNTHESIS_TEMPLATE.format(
        map_markdown=map_markdown,
        shape=cmap.shape,
        question=cmap.question_frame,
        coverage_note=coverage_note,
    )

    # temperature is clamped to 1.0 for KIMI inside _openai_compatible_payload (M6).
    # We pass temperature=0.3 for non-KIMI fallbacks; the service overrides for KIMI.
    response = await llm.generate(
        prompt=user_prompt,
        system_prompt=DIALECTICAL_SYNTHESIS_SYSTEM,
        temperature=0.3,
        max_tokens=max_tokens,
        thinking_mode=(budget_tier == "deep"),  # routes to thinking_model (k2.7-code)
        model_override=model_id,
        provider_override=provider,
    )

    prose = (response.content or "").strip()
    reasoning_trace = getattr(response, "reasoning_content", "") or ""
    ledger = build_provenance_ledger(prose, cmap)

    return SynthesisResult(
        prose=prose,
        reasoning_trace=reasoning_trace,
        model_used=getattr(response, "model_used", model_id),
        ledger=ledger,
    )


# ----------------------------------------------------------------------------
# 4. Provenance ledger as a BYPRODUCT (reverses F8) — deterministic post-pass
#    Demotes DraftClaimLedger from a generative pre-step to this parser.
# ----------------------------------------------------------------------------

_MARKER_RE = re.compile(
    r"\[(?P<kind>P|edge|passage)_?(?P<body>[^\]]+)\]"
)

# Modern-label lexicon (MEMORY Phase 11/12). Used to tag claims as needing
# attribution; the anti-anachronism gate (M5) consumes the same list.
ANACHRONISTIC_LEXICON = (
    "libertarian",
    "compatibilism",
    "compatibilist",
    "incompatibilism",
    "incompatibilist",
    "hard determinism",
    "soft determinism",
    "the will",
    "free-will problem",
    "free will problem",
    "invention of the will",
    "indeterminist",
)


def _classify_claim(sentence: str, kind: str) -> str:
    """Tag each extracted claim (research §8) so the referee applies type rules."""
    low = sentence.lower()
    if kind == "passage":
        return "assertion"  # grounded-in-text claim; substring + NLI check
    if kind in {"P", "edge"}:
        return "attributed_position"
    if any(tok in low for tok in ANACHRONISTIC_LEXICON):
        return "interpretation"
    return "interpretation"


def _split_sentences(prose: str) -> list[str]:
    # Cheap, deterministic. Keeps the marker attached to its sentence.
    parts = re.split(r"(?<=[.!?])\s+(?=[A-ZΑ-Ω])", prose)
    return [p.strip() for p in parts if p.strip()]


def build_provenance_ledger(
    prose: str, cmap: ControversyMap
) -> list[ClaimLedgerItem]:
    """Parse inline [P_*]/[edge:*]/[passage_*] markers out of the finished prose and
    resolve each to its ControversyMap entry. Emits ClaimLedgerItem[] for the UI
    reference map and ProgrammaticVerify / CitationVerifierV2.

    Markers that resolve to a real map id become SUPPORTED ledger items; markers that
    DON'T resolve are emitted UNVERIFIED and hard-rejected by the referee (M5). The
    prose is the source of truth; this is its index.
    """
    # Build resolution tables from the map.
    pos_by_id: dict[str, GroundedPosition] = {}
    passage_by_id: dict[str, PassageRef] = {}
    for frame in cmap.frames:
        for p in frame.positions:
            pos_by_id[p.position_id] = p
        for pr in frame.contested_passages:
            passage_by_id[pr.passage_id] = pr
    for pr in cmap.exegesis_units:
        passage_by_id[pr.passage_id] = pr
    for pid, pr in cmap.provenance.items():
        passage_by_id[pid] = pr

    items: list[ClaimLedgerItem] = []
    for sentence in _split_sentences(prose):
        for m in _MARKER_RE.finditer(sentence):
            kind = m.group("kind")
            body = m.group("body").strip()
            # body forms:  P_<id>: ...   |  edge: <rel> ...   |  passage_<id>: ...
            ref_id = body.split(":", 1)[0].strip().lstrip("_")
            evidence_class = _classify_claim(sentence, kind)

            resolved = False
            quote_original = None
            quote_translation = None
            evidence_ids: list[str] = []

            if kind == "P" and ref_id in pos_by_id:
                resolved = True
                evidence_ids = [pos_by_id[ref_id].holder_node_id]
            elif kind == "passage" and ref_id in passage_by_id:
                resolved = True
                pr = passage_by_id[ref_id]
                evidence_ids = [pr.passage_id]
                quote_original = pr.original_text  # FULL, not truncated
                quote_translation = pr.english_text
            elif kind == "edge":
                resolved = True  # edges resolve structurally; checked by completeness critic

            items.append(
                ClaimLedgerItem(
                    claim=sentence,
                    evidence_ids=evidence_ids,
                    evidence_class=evidence_class,
                    quote_original=quote_original,
                    quote_translation=quote_translation,
                    support_type="passage" if kind == "passage" else "position",
                    confidence=0.8 if resolved else 0.0,
                    status=ClaimStatus.SUPPORTED if resolved else ClaimStatus.UNVERIFIED,
                )
            )
    return items


# ----------------------------------------------------------------------------
# 5. Content gate (replaces the ~10k-char floor, graph_nodes.py:3987-3993).
#    A correct 600-word survey passes; a template paste never does.
# ----------------------------------------------------------------------------


def passes_content_gate(prose: str, cmap: ControversyMap) -> bool:
    """Replace the length floor with a CONTENT gate: does the answer name >=1 fault
    line with both sides + >=1 primary citation? (architecture §4.5)."""
    if not prose.strip():
        return False
    # >=1 edge marker (a fault line invoked) and >=1 passage marker (primary grounding)
    has_edge = "[edge:" in prose or "--opposes-->" in prose or " opposes " in prose
    has_edge = has_edge or bool(re.search(r"\[edge[:_]", prose))
    has_passage_cite = bool(re.search(r"\[passage_", prose))
    # anti-template guard: the dead template string must never appear
    template_leak = "frames the issue as" in prose
    return bool(has_edge and has_passage_cite and not template_leak)


# ----------------------------------------------------------------------------
# 6. Degraded mode — a reasoned hedge, never a template (architecture §4.5).
# ----------------------------------------------------------------------------


async def synthesize_degraded(
    cmap: ControversyMap, llm: LLMService
) -> str:
    """When synthesis fails or frames are thin: a SHORTER reasoned answer over whatever
    frames assembled, explicitly stating its coverage limit in prose. Never a node-paste.
    """
    gaps = "; ".join(cmap.coverage_gaps) if cmap.coverage_gaps else "none recorded"
    degraded_prompt = (
        serialize_controversy_map(cmap)
        + "\n\nWrite a SHORT, honest scholarly answer over only the frames that "
        "assembled. State explicitly which fault lines were thinly covered in this "
        f"run (gaps: {gaps}). Attribute every position; ground in quoted text where "
        "available; do not pad. This is a scholar's hedge, not a survey."
    )
    provider, model_id = resolve_scholar_synthesis_model()
    response = await llm.generate(
        prompt=degraded_prompt,
        system_prompt=DIALECTICAL_SYNTHESIS_SYSTEM,
        temperature=0.3,
        max_tokens=4000,
        model_override=model_id,
        provider_override=provider,
    )
    return (response.content or "").strip()
