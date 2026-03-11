"""Tests for CitationVerifier service."""

from unittest.mock import AsyncMock

import pytest

from eleutheria_graphrag.agents.state import Citation, Evidence
from eleutheria_graphrag.services.citation_verifier import CitationVerifier


def _make_llm(response: str = '{"supported": true, "reason": "ok"}') -> AsyncMock:
    """Create a mock LLM service."""
    llm = AsyncMock()
    llm.generate = AsyncMock(return_value=response)
    return llm


def _make_evidence() -> list[Evidence]:
    return [
        Evidence(
            id="n1",
            label="Chrysippus",
            type="Person",
            description="Stoic philosopher known for his work on fate and determinism",
        ),
        Evidence(
            id="p1",
            label="SVF 2.912",
            type="passage",
            text_content="He argues that fate is a sequence of causes that cannot be broken.",
        ),
    ]


def _make_citations() -> list[Citation]:
    return [
        Citation(ref="1", type="node", id="n1", label="Chrysippus"),
        Citation(ref="P1", type="passage", id="p1", label="SVF 2.912"),
    ]


class TestCitationVerifier:
    """Tests for CitationVerifier."""

    @pytest.mark.asyncio
    async def test_empty_citations(self):
        llm = _make_llm()
        verifier = CitationVerifier(llm=llm)
        result = await verifier.verify_citations("answer", [], [])
        assert result == []
        llm.generate.assert_not_called()

    @pytest.mark.asyncio
    async def test_all_verified(self):
        llm = _make_llm('{"supported": true, "reason": "matches"}')
        verifier = CitationVerifier(llm=llm)
        evidence = _make_evidence()
        citations = _make_citations()

        answer = "Chrysippus [1] argued that fate is causal [P1]."
        result = await verifier.verify_citations(answer, citations, evidence)

        assert len(result) == 2
        assert all(c.verified for c in result)

    @pytest.mark.asyncio
    async def test_unsupported_citation(self):
        llm = _make_llm('{"supported": false, "reason": "claim not in source"}')
        verifier = CitationVerifier(llm=llm)
        evidence = _make_evidence()
        citations = _make_citations()

        answer = "Chrysippus [1] denied free will [P1]."
        result = await verifier.verify_citations(answer, citations, evidence)

        # Both still included, but marked unverified
        assert len(result) == 2
        assert all(not c.verified for c in result)
        assert "not be directly supported" in result[0].verification_note

    @pytest.mark.asyncio
    async def test_missing_evidence(self):
        llm = _make_llm()
        verifier = CitationVerifier(llm=llm)
        evidence = []  # No evidence at all
        citations = [Citation(ref="1", type="node", id="n1", label="X")]

        result = await verifier.verify_citations("text [1]", citations, evidence)

        # Missing evidence → citation dropped (not appended to verified list)
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_short_source_text(self):
        llm = _make_llm()
        verifier = CitationVerifier(llm=llm)
        evidence = [Evidence(id="n1", label="X", description="short")]
        citations = [Citation(ref="1", type="node", id="n1", label="X")]

        answer = "Claim about X [1]."
        result = await verifier.verify_citations(answer, citations, evidence)

        assert len(result) == 1
        assert result[0].verified is True
        assert "too short" in result[0].verification_note
        llm.generate.assert_not_called()

    @pytest.mark.asyncio
    async def test_claim_context_not_found(self):
        llm = _make_llm()
        verifier = CitationVerifier(llm=llm)
        evidence = _make_evidence()
        citations = [Citation(ref="99", type="node", id="n1", label="Chrysippus")]

        # Citation ref [99] doesn't appear in answer text
        answer = "Some text without the citation marker."
        result = await verifier.verify_citations(answer, citations, evidence)

        assert len(result) == 1
        assert result[0].verified is True
        assert "could not be extracted" in result[0].verification_note

    @pytest.mark.asyncio
    async def test_llm_failure_assumes_supported(self):
        llm = AsyncMock()
        llm.generate = AsyncMock(side_effect=RuntimeError("LLM down"))
        verifier = CitationVerifier(llm=llm)
        evidence = _make_evidence()
        citations = [Citation(ref="1", type="node", id="n1", label="Chrysippus")]

        answer = "Chrysippus [1] was a philosopher."
        result = await verifier.verify_citations(answer, citations, evidence)

        assert len(result) == 1
        assert result[0].verified is True

    @pytest.mark.asyncio
    async def test_json_in_markdown_fence(self):
        llm = _make_llm('```json\n{"supported": true, "reason": "ok"}\n```')
        verifier = CitationVerifier(llm=llm)
        evidence = _make_evidence()
        citations = [Citation(ref="1", type="node", id="n1", label="Chrysippus")]

        answer = "Chrysippus [1] worked on fate."
        result = await verifier.verify_citations(answer, citations, evidence)

        assert result[0].verified is True


class TestExtractClaimContext:
    """Tests for _extract_claim_context helper."""

    def test_finds_citation_in_sentence(self):
        verifier = CitationVerifier(llm=AsyncMock())
        answer = "First sentence. Chrysippus argued for determinism [1]. Third sentence."
        claim = verifier._extract_claim_context(answer, "1")
        assert claim is not None
        assert "[1]" in claim

    def test_finds_passage_citation(self):
        verifier = CitationVerifier(llm=AsyncMock())
        answer = "The passage states [P1] that fate is causal."
        claim = verifier._extract_claim_context(answer, "P1")
        assert claim is not None
        assert "[P1]" in claim

    def test_returns_none_for_missing(self):
        verifier = CitationVerifier(llm=AsyncMock())
        answer = "No citations here."
        claim = verifier._extract_claim_context(answer, "99")
        assert claim is None

    def test_window_extraction(self):
        verifier = CitationVerifier(llm=AsyncMock())
        long_text = "A" * 500 + " citation [1] here. " + "B" * 500
        claim = verifier._extract_claim_context(long_text, "1", window=50)
        assert claim is not None
        assert len(claim) < 500  # Not the whole text
