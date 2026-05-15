"""Tests for progressive render-quality thresholds + expand retry.

The render pipeline classifies LLM prose into three bands:

- ``strict``     — ≥ min_chars, ≥ required_sections, ≥ 3 citations/section.
                   Polished fully, ``render_answer_mode = "llm"``.
- ``llm_short``  — ≥ 1,800 chars, ≥ max(3, required_sections-1) sections,
                   ≥ 2 citations/section. Polished lightly,
                   ``render_answer_mode = "llm_short"``. **Not** a fallback.
- ``inadequate`` — below the llm_short floor → mechanical fallback,
                   ``render_answer_mode = "fallback"``.

When the first draft lands in ``llm_short`` or ``inadequate``, the renderer
issues a one-shot expand retry. ``expand_retry_count`` is recorded on
``state.metadata``.
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from eleutheria_graphrag.agents.graph_nodes import (
    ProgrammaticVerify,
    RenderGroundedAnswer,
    _answer_shape_metrics,
    _classify_render_quality,
    _render_requirements,
)
from eleutheria_graphrag.agents.state import (
    ClaimLedgerItem,
    ClaimStatus,
    ContextPack,
    DossierFacet,
    EvidenceBundle,
    RAGState,
)

from .conftest import make_ctx, make_deps

# ---------------------------------------------------------------------------
# Helpers — build a state that requires 4 sections, min_chars=2,800.
# ---------------------------------------------------------------------------


def _four_facet_state() -> RAGState:
    """State requiring 4 sections (matches the prod Bobzien/Frede trace)."""
    state = RAGState(question="Compare Bobzien and Frede on Stoic compatibilism.")
    state.scholarly_dossier.facets = [
        DossierFacet(
            facet_id=f"facet_{i}",
            title=f"Section {i}",
            question=f"Q{i}",
            primary_bundle_ids=["b1" if i % 2 else "b2"],
        )
        for i in range(1, 5)
    ]
    state.context_pack = ContextPack(
        bundle_refs={"b1": "P1", "b2": "P2"},
        passage_bundles=[
            EvidenceBundle(
                bundle_id="b1",
                work_id="w1",
                work_title="De Fato",
                author="Cicero",
                original_passage_id="p1",
                original_text="fatum est series causarum",
                translation_text="fate is a sequence of causes",
                token_estimate=20,
            ),
            EvidenceBundle(
                bundle_id="b2",
                work_id="w2",
                work_title="Discourses",
                author="Epictetus",
                original_passage_id="p2",
                original_text="τὸ ἐφ' ἡμῖν",
                translation_text="what is up to us",
                token_estimate=10,
            ),
        ],
    )
    state.claim_ledger = [
        ClaimLedgerItem(
            claim=f"Claim {i}",
            evidence_ids=["b1" if i % 2 else "b2"],
            facet_id=f"facet_{i}",
            quote_original="fatum est series causarum" if i % 2 else "τὸ ἐφ' ἡμῖν",
            quote_translation=(
                "fate is a sequence of causes" if i % 2 else "what is up to us"
            ),
            support_type="passage",
            confidence=0.9,
            status=ClaimStatus.SUPPORTED,
        )
        for i in range(1, 5)
    ]
    return state


def _section(title: str, body: str) -> str:
    return f"### {title}\n{body}\n"


def _build_answer(
    section_count: int,
    body_chars_per_section: int,
    citations_per_section: int,
    quote_blocks_per_section: int = 1,
) -> str:
    sections = []
    for i in range(1, section_count + 1):
        # Pad body to target char length.
        body = "Lorem ipsum dolor sit amet, consectetur adipiscing elit. " * max(
            1, body_chars_per_section // 60
        )
        # Add the requested number of inline citation markers.
        markers = " ".join(f"[P{j}]" for j in range(1, citations_per_section + 1))
        body = body + " " + markers
        # Add block quotes (mandatory dual-language format).
        quote_lines = []
        for q in range(quote_blocks_per_section):
            quote_lines.append(f"> Original quote {i}.{q} [P{q + 1}]")
            quote_lines.append(f'> "Translation {i}.{q}" [P{q + 1}]')
        quotes = "\n".join(quote_lines)
        sections.append(_section(f"Section {i}", body + ("\n" + quotes if quotes else "")))
    return "Opening thesis. [P1]\n\n" + "\n".join(sections)


# ---------------------------------------------------------------------------
# Pure-function tests for _classify_render_quality.
# ---------------------------------------------------------------------------


class TestClassifyRenderQuality:
    def test_strict_band_when_long_dense_and_well_cited(self):
        state = _four_facet_state()
        reqs = _render_requirements(state)
        # 4 supported facets → 4 required sections. Hard floor ≥ 2,800
        # (matches the prod Bobzien/Frede trace requirement).
        assert reqs["required_sections"] == 4
        assert reqs["min_chars"] >= 2800

        # Build an answer that comfortably clears whatever min_chars is.
        # ~1,400 chars/section × 4 sections, 3 citations/section, 1 block
        # quote/section → strict.
        answer = _build_answer(
            section_count=4,
            body_chars_per_section=1400,
            citations_per_section=3,
            quote_blocks_per_section=1,
        )
        band, metrics = _classify_render_quality(state, answer)
        assert band == "strict", (
            f"expected strict, got {band} "
            f"(chars={metrics['chars']} vs min={reqs['min_chars']}, "
            f"sections={metrics['section_headers']}, "
            f"citations={metrics['inline_citations']})"
        )
        assert metrics["chars"] >= reqs["min_chars"]
        assert metrics["section_headers"] >= 4
        assert metrics["inline_citations"] >= 12

    def test_llm_short_band_when_prose_is_good_but_short(self):
        """Mid-band: 1,800-2,799 chars, 3 sections, 2 citations/section."""
        state = _four_facet_state()
        answer = _build_answer(
            section_count=3, body_chars_per_section=650, citations_per_section=2
        )
        band, metrics = _classify_render_quality(state, answer)
        assert band == "llm_short", (
            f"expected llm_short, got {band} "
            f"(chars={metrics['chars']}, sections={metrics['section_headers']}, "
            f"citations={metrics['inline_citations']})"
        )
        assert 1800 <= metrics["chars"] < 2800
        assert metrics["section_headers"] >= 3

    def test_inadequate_band_when_too_short(self):
        state = _four_facet_state()
        # Way under the floor.
        answer = "### One section\nA single short sentence. [P1]"
        band, _metrics = _classify_render_quality(state, answer)
        assert band == "inadequate"

    def test_inadequate_when_empty(self):
        state = _four_facet_state()
        band, _ = _classify_render_quality(state, "")
        assert band == "inadequate"
        band, _ = _classify_render_quality(state, "   \n\n   ")
        assert band == "inadequate"


# ---------------------------------------------------------------------------
# _answer_shape_metrics — verify the new inline_citations counter.
# ---------------------------------------------------------------------------


class TestAnswerShapeMetrics:
    def test_counts_inline_citation_markers(self):
        answer = (
            "### A\nClaim one [P1]. Claim two [N2]. Claim three [12].\n"
            "### B\nAnother [P3]."
        )
        metrics = _answer_shape_metrics(answer)
        assert metrics["inline_citations"] == 4
        assert metrics["section_headers"] == 2


# ---------------------------------------------------------------------------
# Integration tests for the expand-retry loop in RenderGroundedAnswer.
# ---------------------------------------------------------------------------


class TestExpandRetry:
    @pytest.mark.asyncio
    async def test_expand_retry_promotes_short_to_strict(self):
        """First draft = llm_short (~2,000 chars). Expand call returns a
        strict-band answer. Final mode is 'llm', expand_retry_count == 1."""
        state = _four_facet_state()
        short_draft = _build_answer(
            section_count=3, body_chars_per_section=650, citations_per_section=2
        )
        long_expanded = _build_answer(
            section_count=4,
            body_chars_per_section=1400,
            citations_per_section=3,
            quote_blocks_per_section=1,
        )
        polished = long_expanded + "\n\n(polished)"

        deps = make_deps()
        deps.llm.generate = AsyncMock(
            side_effect=[short_draft, long_expanded, polished]
        )
        ctx = make_ctx(state, deps)

        result = await RenderGroundedAnswer().run(ctx)

        assert isinstance(result, ProgrammaticVerify)
        assert state.metadata["expand_retry_count"] == 1
        assert state.metadata["render_answer_mode"] == "llm"
        assert state.metadata.get("scholarly_polish_mode") == "llm"
        # Three calls: render → expand → polish.
        assert deps.llm.generate.call_count == 3

    @pytest.mark.asyncio
    async def test_expand_retry_keeps_short_when_expansion_does_not_promote(self):
        """First draft = llm_short. Expansion stays in llm_short band but
        is longer → accepted. Final mode = 'llm_short', polish runs."""
        state = _four_facet_state()
        short_draft = _build_answer(
            section_count=3, body_chars_per_section=650, citations_per_section=2
        )
        slightly_longer = _build_answer(
            section_count=3, body_chars_per_section=750, citations_per_section=2
        )

        deps = make_deps()
        deps.llm.generate = AsyncMock(
            side_effect=[short_draft, slightly_longer, slightly_longer]
        )
        ctx = make_ctx(state, deps)

        await RenderGroundedAnswer().run(ctx)

        assert state.metadata["expand_retry_count"] == 1
        assert state.metadata["render_answer_mode"] == "llm_short"
        # Light polish ran — NOT skipped.
        assert state.metadata.get("scholarly_polish_mode") == "llm_short"
        # render → expand → polish.
        assert deps.llm.generate.call_count == 3

    @pytest.mark.asyncio
    async def test_expand_retry_falls_back_when_still_inadequate(self):
        """First draft = inadequate. Expansion still inadequate → fallback,
        polish is skipped, render_answer_mode = 'fallback'."""
        state = _four_facet_state()
        tiny_draft = "### S1\nTiny. [P1]"
        still_tiny = "### S1\nStill tiny. [P1]"

        deps = make_deps()
        deps.llm.generate = AsyncMock(side_effect=[tiny_draft, still_tiny])
        ctx = make_ctx(state, deps)

        await RenderGroundedAnswer().run(ctx)

        assert state.metadata["expand_retry_count"] == 1
        assert state.metadata["render_answer_mode"] == "fallback"
        # Polish must NOT run for an inadequate draft.
        assert state.metadata.get("scholarly_polish_mode", "skipped") == "skipped"
        # Only render + expand were attempted — no polish call.
        assert deps.llm.generate.call_count == 2

    @pytest.mark.asyncio
    async def test_strict_first_draft_skips_expand_retry(self):
        """When the first draft already lands in the strict band, no
        expand retry runs (cost saving). Polish still runs."""
        state = _four_facet_state()
        strict_draft = _build_answer(
            section_count=4,
            body_chars_per_section=1400,
            citations_per_section=3,
            quote_blocks_per_section=1,
        )
        polished = strict_draft + "\n\n(polished)"

        deps = make_deps()
        deps.llm.generate = AsyncMock(side_effect=[strict_draft, polished])
        ctx = make_ctx(state, deps)

        await RenderGroundedAnswer().run(ctx)

        assert state.metadata["expand_retry_count"] == 0
        assert state.metadata["render_answer_mode"] == "llm"
        assert state.metadata.get("scholarly_polish_mode") == "llm"
        # render → polish only.
        assert deps.llm.generate.call_count == 2
