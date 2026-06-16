"""Dialectical scholarly synthesis — the Scholar-RAG M4 core (ARCHITECTURE §4).

This module is the cutover seam. On the Scholar-RAG path it REPLACES the facet
template + ``DraftClaimLedger -> build_render_prompt -> RenderGroundedAnswer ->
_render_answer_fallback`` chain (failure-map F4/F5/F7/F8) with ONE LLM call over a
:class:`ControversyMap` that emits *cite-as-you-write* prose, plus a deterministic
post-pass that parses the inline markers back into a :class:`ClaimLedgerItem` list
(the provenance ledger is now a BYPRODUCT of the prose, not its input — F8 reversed).

Four pieces live here so the whole synthesis seam reads in one place:

1. The prompt — :data:`DIALECTICAL_SYNTHESIS_SYSTEM` + :data:`DIALECTICAL_SYNTHESIS_TEMPLATE`
   (replaces ``RENDER_ANSWER_PROMPT``; the hardcoded Bobzien⟂Frede example is gone —
   the dialectic comes from the serialised map's first-class edge rows).
2. :func:`serialize_controversy_map` — the ``## QUESTION`` header over the M3
   ``## Controversy Frames`` layer (edges as ``A --opposes--> B`` rows, bilingual
   passages untruncated). Reuses the M3 serialiser so there is one edge-slot truth.
3. :func:`synthesize_dialectical` — the single call (``DialecticalSynthesis.run`` body).
4. :func:`build_provenance_ledger` — the marker -> ledger parser (demotes
   ``DraftClaimLedger`` from generative pre-step to this post-pass).

Plus the new gates that replace the ~10k-char floor (failure-map F4/F9):
:func:`passes_content_gate` (a CONTENT gate: ≥1 fault line + ≥1 primary cite) and
:func:`synthesize_degraded` (a prose-stated reasoned hedge — NEVER a node-paste).

VECTORLESS throughout. Greek/Latin only ever flows verbatim from the map's
passages (the prompt forbids inventing it). Gated by ``ELEUTHERIA_SCHOLAR_RAG`` at
the call site; this module is import-safe and inert until a consumer invokes it.

MODEL: Fireworks-only for now (Romain's constraint). :func:`resolve_scholar_synthesis_model`
defaults to ``fireworks:deepseek-v4-pro`` — a TRUE thinking model that returns its
chain-of-thought in ``reasoning_content`` and a clean finished answer in ``content``
(it reads ``SCHOLAR_SYNTHESIS_MODEL`` but does not enable Moonshot here). The
synthesis routes ``reasoning_content`` (a side-channel on ``LLMService``) to the
trace, NEVER into the answer; the answer is ``content`` only. The agent ReAct
retrieval loop stays on the non-reasoning k2p6 instruct model.
"""

from __future__ import annotations

import logging
import os
import re
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any

from eleutheria_graphrag.agents.controversy_map import (
    render_controversy_frames_layer,
)
from eleutheria_graphrag.agents.state import (
    ClaimLedgerItem,
    ClaimStatus,
    ControversyMap,
    GroundedPosition,
    PassageRef,
)

logger = logging.getLogger(__name__)


# ── 1. The synthesis prompt (replaces RENDER_ANSWER_PROMPT) ──────────────────

DIALECTICAL_SYNTHESIS_SYSTEM = """\
You are a historian of ancient philosophy writing for a specialist audience \
(Cambridge-Companion register). You reason DIALECTICALLY over a CONTROVERSY MAP: a \
structured record of contending scholarly positions and the primary texts they \
fight over.

YOU ENTER A SCHOLARLY CONVERSATION. A real scholar's answer is not a summary of \
ancient doctrines — it is a DIALOGUE WITH OTHER SCHOLARS. Every interpretive move \
you make NAMES A MODERN SCHOLAR and sets their reading against another's: "Bobzien \
(1998: 234) argues … whereas Frede (2011: 44) holds …; Sharples (1983: 22) reads the \
same text differently again." You attribute every interpretive claim to a named \
scholar with a page reference, and you ground every claim about an ancient author in \
a quoted primary passage. Naming the contending scholars and their disagreement is \
NOT optional decoration — it is the substance of the answer. You hedge where the \
evidence underdetermines the question; you never adjudicate a dispute the field has \
not settled.

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
  [P_<id>: <holder> <year>, <publication> p.<n>]   for an attributed scholar position
  [edge: <relation> P_<from>->P_<to>]               for a dialectical link you invoke
  [passage_<id>: <author>, <ref>]                   for a quoted/cited primary passage
Every paragraph of interpretation MUST carry at least one [P_<id>: …] scholar marker. \
Use only ids that appear in the map. Never invent an id, a scholar, a publication, or \
a page number — if a position has no page in the map, cite it at work level only.

OUTPUT ONLY THE FINISHED SCHOLARLY PROSE. Do NOT narrate your process. Never write \
"Let me check", "Let's double-check the Greek", "Matches the text", "I will now", \
"First, I…", "Verifying…", or any self-check / meta-commentary. Your reasoning is \
private scratch; the reader sees only the essay.\
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
WRITE the scholarly answer ({shape}). This is a FULL, DETAILED, EXAMPLE-RICH survey, \
not a sketch. Be COMPLETE: cover EVERY fault line the map contains — leave none out. \
Aim for a long-form essay (several substantial paragraphs per fault line); use the \
whole space available. Requirements:

- Open with a THESIS SENTENCE that answers the actual question: {question}
- One movement per fault line; cover ALL frames present; adaptive headings DERIVED \
FROM FRAME TITLES. Do not collapse or skip a frame.
- In EACH movement: name the contending MODERN SCHOLARS and stage their disagreement \
explicitly ("Bobzien (1998: 234) argues …, whereas Frede (2011: 44) reads … and Dihle \
(1982: 123) instead …"). Every interpretive paragraph carries ≥1 inline [P_<id>: …] \
scholar marker AS YOU WRITE IT, plus the [edge: …] for the disagreement and the \
[passage_<id>: …] for its primary anchor. Give MULTIPLE concrete examples per frame.
- Quote contested primary text in original + English where the scholars argue over it.
- Where scholars genuinely conflict vs. merely talk past each other (different sense \
of "the will", different dating), SAY which — this is the scholar's added value.
- Hedge with the field's own markers ("Bobzien argues…, though Frede contends…").
- Close with a synthetic conclusion stating what remains GENUINELY OPEN, and resist \
any anachronistic verdict.

Write ONLY the essay. Do not include any planning, verification, or self-checking \
text; do not restate these instructions; do not narrate what you are doing.
{coverage_note}\
"""


# ── 2. Map serialiser (QUESTION header over the M3 edge-first frame layer) ────


def serialize_controversy_map(cmap: ControversyMap) -> str:
    """Render the ControversyMap as the structured markdown the prompt consumes.

    A ``## QUESTION`` header (question + detected shape) over the M3
    ``## Controversy Frames`` layer (:func:`render_controversy_frames_layer`):
    edges are explicit ``A --opposes--> B`` rows, so the prompt is structurally
    unable to be edge-blind; passages are bilingual and untruncated; standalone
    exegesis units and coverage gaps follow. One serialiser, one edge-slot truth.
    """
    shape = getattr(cmap.shape, "value", cmap.shape)
    out = [f"## QUESTION  {cmap.question_frame}   (detected shape: {shape})", ""]
    frames_layer = render_controversy_frames_layer(cmap)
    if frames_layer:
        out.append(frames_layer)
    return "\n".join(out).rstrip() + "\n"


# ── 3. The synthesis call (ONE LLM call) ─────────────────────────────────────


@dataclass
class SynthesisResult:
    """Output of the dialectical synthesis: prose + its parsed provenance index."""

    prose: str
    reasoning_trace: str = ""  # reasoning_content (M6); empty until then
    model_used: str = ""
    ledger: list[ClaimLedgerItem] = field(default_factory=list)
    degraded: bool = False  # True when the degraded-mode hedge produced the prose


# M6: the synthesis fallback chain (ARCHITECTURE §K2.7). Fireworks-only TODAY —
# the Moonshot K2.7 rungs are commented one-line-ready (see resolve_*_model and
# scholar_synthesis_fallback_chain). The live chain degrades within Fireworks/
# Gemini, never to Moonshot, per Romain's constraint.
#
# The synthesis runs on a TRUE THINKING model: ``deepseek-v4-pro`` returns its
# chain-of-thought in ``reasoning_content`` and a CLEAN finished scholarly answer
# in ``content`` (finish_reason=stop) — fixing the k2p6 failure where a
# non-reasoning instruct model emitted its scratchpad INLINE in ``content`` and
# hit max_tokens while still planning (finish_reason=length). The answer budget
# (max_tokens) now applies to ``content`` only; reasoning spends separate tokens.
#
# ONE-LINE K2-THINKING SWAP (enable once it lands on this Fireworks account —
# kimi-k2-thinking is currently 404 here, not enabled):
#   - set _SCHOLAR_SYNTHESIS_DEFAULT = "accounts/fireworks/models/kimi-k2-thinking"
#   (it also returns reasoning_content; no other wiring change needed).
_SCHOLAR_SYNTHESIS_DEFAULT = "accounts/fireworks/models/deepseek-v4-pro"
# _SCHOLAR_SYNTHESIS_DEFAULT = "accounts/fireworks/models/kimi-k2-thinking"  # when enabled
# k2p6 (non-reasoning instruct) is kept ONLY for the agent ReAct retrieval loop,
# not for synthesis — it inlines its scratchpad into content (the root-cause bug).
_SCHOLAR_SYNTHESIS_AGENT_LOOP_MODEL = "accounts/fireworks/models/kimi-k2p7-code"
_SCHOLAR_SYNTHESIS_GEMINI_FALLBACK = "gemini-3.1-pro-preview"

# Fireworks reasoning models that return their chain-of-thought in a SEPARATE
# ``reasoning_content`` field, leaving ``content`` a clean finished answer. For
# these the defensive ``strip_reasoning_leak`` post-pass is a NO-OP: the content
# is already clean, so running the stripper could only risk truncating a real
# answer. Non-reasoning models (k2p6) still get the stripper.
_REASONING_SEPARATED_MODELS: frozenset[str] = frozenset(
    {
        "accounts/fireworks/models/deepseek-v4-pro",
        "accounts/fireworks/models/kimi-k2-thinking",
    }
)


def model_separates_reasoning(model_id: str) -> bool:
    """True when ``model_id`` returns its chain-of-thought in ``reasoning_content``
    (so ``content`` is already clean and ``strip_reasoning_leak`` must NOT run)."""
    if not isinstance(model_id, str):
        return False
    return model_id.strip() in _REASONING_SEPARATED_MODELS


def resolve_scholar_synthesis_model() -> str:
    """Resolve the synthesis model id (M6 swap lands HERE, one line).

    Reads ``SCHOLAR_SYNTHESIS_MODEL`` (form ``provider:model`` or a bare model
    id). FIREWORKS-ONLY for now (Romain's constraint overrides the blueprint's
    Moonshot opt-in): any non-Fireworks request resolves to the Fireworks
    kimi-k2p6 default. Returns a ``model_override`` string accepted by
    ``LLMService.generate``/``stream`` (``accounts/fireworks/...`` → Fireworks).

    M6: lift the Fireworks guard + return ``(provider, model_id)`` once K2.7 is
    available on Fireworks. Until then this is a single-line change surface.
    """
    default = _SCHOLAR_SYNTHESIS_DEFAULT
    raw = (os.getenv("SCHOLAR_SYNTHESIS_MODEL") or "").strip()
    if not raw:
        return default
    provider, _, model_id = raw.partition(":")
    if not model_id:  # bare model id
        provider, model_id = "", provider
    if provider and provider.lower() != "fireworks":
        # Fireworks-only: ignore Moonshot/other opt-ins until M6 wires K2.7.
        logger.debug(
            "SCHOLAR_SYNTHESIS_MODEL=%s ignored (Fireworks-only); using default", raw
        )
        return default
    return model_id or default


def scholar_synthesis_fallback_chain() -> list[str]:
    """The synthesis ``model_override`` fallback chain (ARCHITECTURE §K2.7).

    TODAY, Fireworks-only (Romain's constraint — no Moonshot rung). The live chain
    is ``<resolved deepseek-v4-pro> -> fireworks/deepseek-v4-pro -> gemini-3.1-pro-preview``:
    a true thinking head (clean answer in ``content``, scratch in ``reasoning_content``)
    that degrades to Gemini, never to Moonshot. When kimi-k2-thinking is enabled on
    this Fireworks account, the resolved head simply becomes that id.

    The caller (M6 synthesis node) tries each override in order; each is a string
    ``LLMService.generate(model_override=...)`` already routes (Fireworks ids by
    prefix, the Gemini id as a bare model). Deduped, order preserved.
    """
    chain = [
        resolve_scholar_synthesis_model(),
        _SCHOLAR_SYNTHESIS_DEFAULT,
        _SCHOLAR_SYNTHESIS_GEMINI_FALLBACK,
    ]
    seen: set[str] = set()
    out: list[str] = []
    for m in chain:
        if m and m not in seen:
            seen.add(m)
            out.append(m)
    return out


# ── M6 budgets (ARCHITECTURE §6) — the flag-ON quality tier ──────────────────
#
# The Scholar-RAG path runs a higher tool-call budget and render-token cap than
# the legacy path. These are the §6 numbers, env-overridable. The synthesis node
# (M6 routing seam) reads them when ELEUTHERIA_SCHOLAR_RAG is on; the legacy path
# is untouched. The char-floor (graph_nodes.py:3987-3993) is REPLACED by the M4
# content gate (passes_content_gate) — length is no longer a quality proxy.

# Per-tier tool-call ceiling (raised for survey/transmission so a Bobzien⟂Frede +
# origins + Alexander + Carneadean survey can fetch its build_controversy_frame +
# bilingual read_passages calls). The real stop condition is the M5 completeness
# critic, not this blunt count.
_SCHOLAR_TOOL_CALL_BUDGETS: dict[str, int] = {
    "quick": 12,
    "standard": 24,
    "deep": 45,
}

# Per-tier synthesis render cap. >=5000 mandatory: reasoning eats the budget.
# Streaming cap must match the blocking path (the two must agree — §6); the M6
# wiring raises scholarly_agent._stream_render_max_tokens to this for flag-ON.
_SCHOLAR_RENDER_TOKENS: dict[str, int] = {
    "quick": 6000,
    "standard": 8000,
    "deep": 8000,
}


def scholar_tool_call_budget(budget_tier: str) -> int:
    """Flag-ON tool-call ceiling by tier (§6). ``ELEUTHERIA_SCHOLAR_MAX_TOOL_CALLS``
    overrides all tiers when set > 0."""
    raw = os.getenv("ELEUTHERIA_SCHOLAR_MAX_TOOL_CALLS")
    if raw:
        try:
            value = int(raw)
        except ValueError:
            value = 0
        if value > 0:
            return value
    return _SCHOLAR_TOOL_CALL_BUDGETS.get(budget_tier, 24)


# The synthesis runs a TRUE thinking model (deepseek-v4-pro): ~150–220 s of
# generation (large reasoning_content + answer) is normal, and a hard query can
# push past that. The shared LLM client times out at 120 s, which would cancel a
# healthy slow synthesis into the legacy facet-template fallback — the worst
# outcome. Give the synthesis LLM call a dedicated, generous per-request HTTP
# timeout (budget for up to ~300 s of generation) so it ALWAYS completes. This
# overrides ONLY the synthesis call; every other LLM call keeps the 120 s client
# timeout. ``ELEUTHERIA_SCHOLAR_SYNTHESIS_TIMEOUT`` overrides (seconds, clamped).
_SCHOLAR_SYNTHESIS_TIMEOUT_DEFAULT = 360.0


def scholar_synthesis_timeout() -> float:
    """Per-call HTTP timeout (seconds) for the dialectical synthesis LLM call.

    Defaults to 360 s — comfortably above the ~150–220 s deepseek-v4-pro thinking
    run and the ~300 s generation budget — so a slow-but-healthy synthesis is
    NEVER cut into the facet-template fallback. Override with
    ``ELEUTHERIA_SCHOLAR_SYNTHESIS_TIMEOUT`` (clamped to [120, 900])."""
    raw = os.getenv("ELEUTHERIA_SCHOLAR_SYNTHESIS_TIMEOUT")
    if raw:
        try:
            return max(120.0, min(900.0, float(raw)))
        except ValueError:
            pass
    return _SCHOLAR_SYNTHESIS_TIMEOUT_DEFAULT


def scholar_render_max_tokens(budget_tier: str) -> int:
    """Flag-ON synthesis render cap by tier (§6); clamped to [5000, 16000].

    Streaming and blocking paths MUST agree on this value (§6). Overridable with
    ``ELEUTHERIA_SCHOLAR_RENDER_MAX_TOKENS``.
    """
    raw = os.getenv("ELEUTHERIA_SCHOLAR_RENDER_MAX_TOKENS")
    if raw:
        try:
            return max(5000, min(16000, int(raw)))
        except ValueError:
            pass
    return _SCHOLAR_RENDER_TOKENS.get(budget_tier, 8000)


async def synthesize_dialectical(
    state: Any,
    cmap: ControversyMap,
    llm: Any,
    *,
    max_tokens: int = 8000,  # >=5000 mandatory: reasoning eats the budget
    budget_tier: str = "standard",
) -> SynthesisResult:
    """Core G6 synthesis. Reason over the ControversyMap, emit cite-as-you-write prose.

    The live ``DialecticalSynthesis.run`` body. No facet template and no pre-built
    ledger feed it: the prose IS the source of truth; :func:`build_provenance_ledger`
    indexes it afterwards. Inputs:
      - ``cmap``: the M3 dossier (frames + exegesis units + coverage gaps), fully
        grounded, full bilingual passages, page-grounded positions, raw
        ``incident_edge_count`` order.
      - ``llm``: the shared ``LLMService``; model chosen by
        :func:`resolve_scholar_synthesis_model` (Fireworks-only for now).
    Output: prose + reasoning trace + the extracted ledger.

    Never raises into the pipeline: an empty/failed call yields an empty-prose
    result the caller routes to :func:`synthesize_degraded`.

    ``budget_tier`` defaults from ``state.research_plan`` (the M2 plan) when the
    caller did not pin one — so a ``deep`` plan routes to the thinking model.
    """
    if budget_tier == "standard":
        plan = getattr(state, "research_plan", None)
        plan_tier = getattr(plan, "budget_tier", None)
        if plan_tier:
            budget_tier = plan_tier

    model_chain = scholar_synthesis_fallback_chain()
    model_id = model_chain[0]

    coverage_note = ""
    if cmap.coverage_gaps:
        coverage_note = (
            "\n- One frame or more was thinly retrieved (see COVERAGE GAPS). State "
            "that coverage limit explicitly in prose; do not pad it with unrelated "
            "material."
        )

    map_markdown = serialize_controversy_map(cmap)
    user_prompt = DIALECTICAL_SYNTHESIS_TEMPLATE.format(
        map_markdown=map_markdown,
        shape=getattr(cmap.shape, "value", cmap.shape),
        question=cmap.question_frame,
        coverage_note=coverage_note,
    )

    # Try each rung of the fallback chain in order; first non-empty prose wins
    # (ARCHITECTURE §K2.7 — Fireworks-only today; head is deepseek-v4-pro, a true
    # thinking model whose ``content`` is already a clean finished answer).
    prose = ""
    reasoning_trace = ""
    for candidate in model_chain:
        try:
            # The answer budget (max_tokens) applies to ``content`` only — thinking
            # models spend SEPARATE tokens on reasoning_content, so the answer is not
            # starved. Keep temperature at 0.3 (KIMI is clamped to 1.0 in the payload).
            raw = await llm.generate(
                user_prompt,
                system_prompt=DIALECTICAL_SYNTHESIS_SYSTEM,
                temperature=0.3,
                max_tokens=max_tokens,
                thinking_mode=(budget_tier == "deep"),
                model_override=candidate,
                # Dedicated generous per-call HTTP timeout: a slow thinking-model
                # synthesis must NEVER be cut by the 120 s client timeout into the
                # facet-template fallback (see scholar_synthesis_timeout docstring).
                request_timeout=scholar_synthesis_timeout(),
            )
            prose = (raw or "").strip()
        except Exception as exc:  # pragma: no cover - defensive, never raise upstream
            logger.warning(
                "dialectical synthesis call failed on %s (%s); trying next rung",
                candidate,
                exc,
            )
            prose = ""
        if prose:
            model_id = candidate
            # The chain-of-thought (reasoning_content) is a SIDE-CHANNEL on the
            # LLMService — route it to the trace, NEVER into the answer.
            reasoning_trace = getattr(llm, "last_reasoning_content", "") or ""
            break

    # Defensive chain-of-thought strip — ONLY for providers that inline reasoning
    # into ``content`` (e.g. k2p6). For a true thinking model (deepseek-v4-pro,
    # kimi-k2-thinking) ``content`` is already clean (reasoning is in
    # reasoning_content), so the stripper is a NO-OP that could only risk
    # truncating a clean answer — skip it.
    model_used = getattr(llm, "last_model_used", "") or model_id
    if prose and not model_separates_reasoning(model_used):
        prose = strip_reasoning_leak(prose)

    ledger = build_provenance_ledger(prose, cmap) if prose else []

    return SynthesisResult(
        prose=prose,
        reasoning_trace=reasoning_trace,
        model_used=model_used,
        ledger=ledger,
    )


# ── 3a. STREAMING synthesis — reasoning_content LIVE on its own channel ──────
#
# Identical inputs/prompt/budgets/timeout to ``synthesize_dialectical``, but it
# drives the LLM via ``llm.stream_segmented`` so the chain-of-thought arrives as
# deltas and can be surfaced LIVE in the AGENT REASONING workspace. The reasoning
# segments are forwarded to ``on_reasoning`` (a callback the caller wires to an
# SSE ``synthesis_reasoning`` event); the answer segments are accumulated into the
# clean ``content`` prose. The reasoning text NEVER enters the answer (separate
# channels by construction). deepseek emits reasoning deltas first, then content
# deltas. Same fallback chain (Fireworks-only today), same 360 s timeout; on a
# rung that yields no answer it tries the next. Never raises into the pipeline.

ReasoningCallback = Callable[[str], Awaitable[None]]


async def synthesize_dialectical_stream(
    state: Any,
    cmap: ControversyMap,
    llm: Any,
    *,
    on_reasoning: ReasoningCallback | None = None,
    max_tokens: int = 8000,
    budget_tier: str = "standard",
) -> SynthesisResult:
    """Streaming twin of :func:`synthesize_dialectical` (M6 live-reasoning path).

    Streams the synthesis so ``reasoning_content`` deltas can be surfaced LIVE.
    For each reasoning delta, ``on_reasoning(delta)`` is awaited (the caller emits
    a ``synthesis_reasoning`` SSE event); answer deltas are accumulated into the
    final prose. Returns the same :class:`SynthesisResult` as the blocking path
    (prose = the streamed ``content`` ONLY; reasoning_trace = the full
    chain-of-thought). The reasoning text is held STRICTLY apart from the answer.
    """
    if budget_tier == "standard":
        plan = getattr(state, "research_plan", None)
        plan_tier = getattr(plan, "budget_tier", None)
        if plan_tier:
            budget_tier = plan_tier

    model_chain = scholar_synthesis_fallback_chain()
    model_id = model_chain[0]

    coverage_note = ""
    if cmap.coverage_gaps:
        coverage_note = (
            "\n- One frame or more was thinly retrieved (see COVERAGE GAPS). State "
            "that coverage limit explicitly in prose; do not pad it with unrelated "
            "material."
        )

    map_markdown = serialize_controversy_map(cmap)
    user_prompt = DIALECTICAL_SYNTHESIS_TEMPLATE.format(
        map_markdown=map_markdown,
        shape=getattr(cmap.shape, "value", cmap.shape),
        question=cmap.question_frame,
        coverage_note=coverage_note,
    )

    prose = ""
    reasoning_trace = ""
    for candidate in model_chain:
        answer_parts: list[str] = []
        reasoning_parts: list[str] = []
        try:
            async for channel, delta in llm.stream_segmented(
                user_prompt,
                system_prompt=DIALECTICAL_SYNTHESIS_SYSTEM,
                temperature=0.3,
                max_tokens=max_tokens,
                model_override=candidate,
                request_timeout=scholar_synthesis_timeout(),
            ):
                if channel == "reasoning":
                    # LIVE reasoning — surface on its OWN channel, NEVER the answer.
                    reasoning_parts.append(delta)
                    if on_reasoning is not None and delta:
                        await on_reasoning(delta)
                elif channel == "answer" and delta:
                    answer_parts.append(delta)
        except Exception as exc:  # pragma: no cover - defensive, never raise upstream
            logger.warning(
                "dialectical streaming synthesis errored on %s (%s); "
                "salvaging %d streamed answer chars",
                candidate,
                exc,
                sum(len(p) for p in answer_parts),
            )
        # Salvage whatever streamed BEFORE the error: a late-stream failure (e.g.
        # a malformed final chunk) must never discard a fully-streamed answer.
        prose = "".join(answer_parts).strip()
        if prose:
            model_id = candidate
            # Prefer the accumulated reasoning deltas; fall back to the
            # side-channel the segmented stream also populates.
            reasoning_trace = "".join(reasoning_parts) or (
                getattr(llm, "last_reasoning_content", "") or ""
            )
            break

    model_used = getattr(llm, "last_model_used", "") or model_id
    # The answer is ``content`` only. For a reasoning-separated model the content
    # is already clean; for any other rung run the defensive stripper.
    if prose and not model_separates_reasoning(model_used):
        prose = strip_reasoning_leak(prose)

    ledger = build_provenance_ledger(prose, cmap) if prose else []

    return SynthesisResult(
        prose=prose,
        reasoning_trace=reasoning_trace,
        model_used=model_used,
        ledger=ledger,
    )


# ── 3b. Defensive chain-of-thought stripper (the reasoning-leak post-clean) ──
#
# Even with the prompt forbidding it, K2.x sometimes emits a trailing self-check
# ("Let's double check the Greek quotes… Matches the text.") or a leading planning
# preamble. This deterministic post-pass cuts those so they never reach the reader.
# It is conservative: it only removes lines/blocks that are unmistakably meta — a
# scholarly sentence about Bobzien is never touched.

# Phrases that open a meta-reasoning / self-verification block (case-insensitive,
# matched at the START of a line/sentence). Kept tight to avoid eating real prose.
_REASONING_LEAK_OPENERS: tuple[str, ...] = (
    "let's double",
    "let's check",
    "let's verify",
    "let me double",
    "let me check",
    "let me verify",
    "let me confirm",
    "let me re-read",
    "let me reread",
    "let me make sure",
    "let me ensure",
    "i'll double",
    "i will double",
    "i'll verify",
    "i will verify",
    "i'll check",
    "i will check",
    "now let me",
    "now i'll",
    "now i will",
    "first, i",
    "first i'll",
    "verifying the",
    "checking the",
    "double-checking",
    "double checking",
    "to verify",
    "as a check",
    "self-check",
    "(checking",
)

# Short trailing confirmations the model emits after a self-check.
_REASONING_LEAK_CONFIRMATIONS: tuple[str, ...] = (
    "matches the text",
    "matches the passage",
    "this matches",
    "that matches",
    "the quote matches",
    "all citations resolve",
    "all markers resolve",
    "everything checks out",
    "looks correct",
    "looks good",
    "the greek is correct",
    "the latin is correct",
    "verified.",
    "confirmed.",
)

_LEAK_HEADING_RE = re.compile(
    r"^\s*#{0,6}\s*(verification|self-?check|fact[- ]?check|checks?|"
    r"double[- ]?check|notes? to self|sanity check)\b",
    re.IGNORECASE,
)


def _is_reasoning_leak_line(line: str) -> bool:
    stripped = line.strip().lstrip("-*>").strip()
    if not stripped:
        return False
    low = stripped.lower()
    if _LEAK_HEADING_RE.match(line):
        return True
    if any(low.startswith(opener) for opener in _REASONING_LEAK_OPENERS):
        return True
    # A short line (not a real scholarly sentence) that is a bare confirmation.
    return len(stripped) <= 80 and any(
        conf in low for conf in _REASONING_LEAK_CONFIRMATIONS
    )


def strip_reasoning_leak(prose: str) -> str:
    """Cut residual chain-of-thought / self-verification from the finished prose.

    Defensive: the prompt already forbids meta-reasoning, but K2.x occasionally
    leaks a trailing "Let's double check the Greek… Matches the text." block or a
    leading "First, I'll…" preamble. This removes such lines/blocks
    deterministically. A genuine scholarly sentence (about a scholar, a text, a
    fault line) is never matched. Idempotent; never raises.
    """
    if not prose or not prose.strip():
        return prose
    lines = prose.splitlines()
    kept: list[str] = []
    in_leak_block = False
    for line in lines:
        if _is_reasoning_leak_line(line):
            # Open a leak block: drop this line and following non-blank lines that
            # are themselves meta or short confirmations, until a blank line or a
            # line that is clearly real prose (carries a citation marker / >100 ch).
            in_leak_block = True
            continue
        if in_leak_block:
            low = line.strip().lower()
            if not low:
                in_leak_block = False  # blank line closes the leak block
                continue
            # Real prose resumes (citation marker or a substantial sentence): keep.
            if (
                "[p_" in low
                or "[passage_" in low
                or "[edge" in low
                or "-->" in low
                or len(line.strip()) > 100
            ):
                in_leak_block = False
                kept.append(line)
                continue
            # Still inside the meta block — drop short bridging confirmations.
            if _is_reasoning_leak_line(line) or len(line.strip()) <= 80:
                continue
            in_leak_block = False
            kept.append(line)
        else:
            kept.append(line)
    cleaned = "\n".join(kept)
    # Collapse the runs of blank lines the excisions may have left.
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


# ── 4. Provenance ledger as a BYPRODUCT (reverses F8) — deterministic post-pass


_MARKER_RE = re.compile(r"\[(?P<kind>P|edge|passage)_?(?P<body>[^\]]+)\]")

# Modern-label lexicon (MEMORY Phase 11/12). Tags claims as needing attribution;
# the M5 anti-anachronism gate consumes the same list.
ANACHRONISTIC_LEXICON: tuple[str, ...] = (
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
    """Tag each extracted claim so the M5 referee applies the right type rules."""
    low = sentence.lower()
    if kind == "passage":
        return "assertion"  # grounded-in-text; substring + NLI check downstream
    if kind in {"P", "edge"}:
        return "attributed_position"
    if any(tok in low for tok in ANACHRONISTIC_LEXICON):
        return "interpretation"
    return "interpretation"


def _split_sentences(prose: str) -> list[str]:
    # Cheap, deterministic. Keeps the marker attached to its sentence.
    parts = re.split(r"(?<=[.!?])\s+(?=[A-ZΑ-Ω])", prose)
    return [p.strip() for p in parts if p.strip()]


def format_scholar_reference(pos: GroundedPosition) -> str:
    """A human-readable modern-scholarship reference for a position.

    "<Holder> — <Publication>, <page>" using only what the map carries (never
    invents a page). Used to make scholar positions FIRST-CLASS CITABLE items in
    the citation payload (the frontend CitationGenerator can export them), not
    only ancient passages.
    """
    holder = (pos.holder or pos.position_id).strip()
    parts: list[str] = [holder] if holder else []
    if pos.publication:
        parts.append(pos.publication.strip())
    if pos.page_grounding:
        parts.append(pos.page_grounding.strip())
    return ", ".join(p for p in parts if p) if parts else (pos.position_id or "")


def build_provenance_ledger(prose: str, cmap: ControversyMap) -> list[ClaimLedgerItem]:
    """Parse inline ``[P_*]``/``[edge:*]``/``[passage_*]`` markers out of the
    finished prose and resolve each to its ControversyMap entry.

    Emits a :class:`ClaimLedgerItem` list for the UI reference map and the M5
    referee. Markers resolving to a real map id become ``SUPPORTED``; markers that
    DON'T resolve are emitted ``UNVERIFIED`` (a hallucinated id) for the referee to
    hard-reject. The prose is the source of truth; this is its index.
    """
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
            quote_original: str | None = None
            quote_translation: str | None = None
            evidence_ids: list[str] = []

            if kind == "P" and ref_id in pos_by_id:
                resolved = True
                pos = pos_by_id[ref_id]
                evidence_ids = [pos.holder_node_id or pos.position_id]
                # Carry the modern-scholarship reference so the citation payload
                # can surface it as a FIRST-CLASS citable item (scholar+work+page),
                # not only ancient passages. quote_translation is the UI's display
                # string; for a position it holds the formatted scholar reference.
                quote_translation = format_scholar_reference(pos)
            elif kind == "passage" and ref_id in passage_by_id:
                resolved = True
                pr = passage_by_id[ref_id]
                evidence_ids = [pr.passage_id]
                quote_original = pr.original_text  # FULL, not truncated
                quote_translation = pr.english_text
            elif kind == "edge":
                # edges resolve structurally; the completeness critic (M5) checks them.
                resolved = True

            items.append(
                ClaimLedgerItem(
                    claim=sentence,
                    evidence_ids=evidence_ids,
                    evidence_class=evidence_class,
                    quote_original=quote_original,
                    quote_translation=quote_translation,
                    support_type="passage" if kind == "passage" else "position",
                    confidence=0.8 if resolved else 0.0,
                    status=(
                        ClaimStatus.SUPPORTED if resolved else ClaimStatus.UNVERIFIED
                    ),
                )
            )
    return items


# ── 5. Content gate (replaces the ~10k-char floor, failure-map F4/F9) ─────────


def passes_content_gate(prose: str, cmap: ControversyMap) -> bool:
    """Replace the length floor with a CONTENT gate (ARCHITECTURE §4.5).

    A correct 600-word survey passes; a node-paste template never does. Requires
    ≥1 fault line invoked (an ``[edge:…]`` / ``--relation-->`` marker) AND ≥1
    primary citation that RESOLVES to a passage in ``cmap`` (a fabricated
    ``[passage_…]`` id does not count), and rejects the dead facet-template string
    outright (it must never silently return).
    """
    if not prose.strip():
        return False
    # anti-template guard: the dead facet-template string must never appear
    if "frames the issue as" in prose:
        return False
    has_edge = bool(re.search(r"\[edge[:_]", prose)) or bool(
        re.search(r"--\s*\w+\s*-->", prose)
    )
    if not has_edge:
        return False
    # ≥1 primary citation grounded in the map (resolves to a real passage id),
    # so a paste citing a fabricated passage id cannot satisfy the gate.
    ledger = build_provenance_ledger(prose, cmap)
    has_grounded_passage = any(
        item.support_type == "passage" and item.status == ClaimStatus.SUPPORTED
        for item in ledger
    )
    return has_grounded_passage


# ── 6. Degraded mode — a reasoned hedge, NEVER a template (ARCHITECTURE §4.5) ─


async def synthesize_degraded(cmap: ControversyMap, llm: Any) -> str:
    """When synthesis fails or the content gate trips: a SHORTER reasoned answer
    over whatever frames assembled, explicitly stating its coverage limit in prose.

    Never a node-paste (this is the ``_render_answer_fallback`` replacement). On any
    LLM error returns an honest empty string for the caller to surface — still never
    a template.
    """
    gaps = "; ".join(cmap.coverage_gaps) if cmap.coverage_gaps else "none recorded"
    degraded_prompt = (
        serialize_controversy_map(cmap)
        + "\n\nWrite a SHORT, honest scholarly answer over only the frames that "
        "assembled. State explicitly which fault lines were thinly covered in this "
        f"run (gaps: {gaps}). Attribute every position; ground in quoted text where "
        "available; do not pad. This is a scholar's hedge, not a survey."
    )
    model_id = resolve_scholar_synthesis_model()
    try:
        raw = await llm.generate(
            degraded_prompt,
            system_prompt=DIALECTICAL_SYNTHESIS_SYSTEM,
            temperature=0.3,
            max_tokens=4000,
            model_override=model_id,
            request_timeout=scholar_synthesis_timeout(),
        )
        return strip_reasoning_leak((raw or "").strip())
    except Exception as exc:  # pragma: no cover - defensive, never raise upstream
        logger.warning("degraded synthesis call failed (%s); empty result", exc)
        return ""
