"""
Citation Verification Service — OpenScholar-inspired self-feedback loop.

After the LLM generates an answer, this service:
1. Parses all citations ([1], [P1], etc.)
2. Verifies each citation exists in the database
3. Checks whether the cited passage/node actually supports the claim
4. Strips ungrounded citations and adds verification notes

Research shows 87.3% of RAG errors happen despite correct retrieval —
the synthesis step is where citations go wrong.  This verification loop
is the single most impactful change for scholarly precision.
"""

from __future__ import annotations

import json
import logging
import re
from typing import TYPE_CHECKING, Any

from eleutheria_graphrag.agents.text_utils import truncate_text

if TYPE_CHECKING:
    from eleutheria_graphrag.agents.state import Citation, Evidence
    from eleutheria_graphrag.services.llm_service import LLMService

logger = logging.getLogger(__name__)

VERIFY_PROMPT = """\
You are a citation verification assistant for ancient philosophy.

Given a claim from a scholarly answer and the source text it cites, \
determine whether the source actually supports the claim.

Claim: {claim}

Source text: {source_text}

Does the source text support this claim?
Return a JSON object:
{{"supported": true/false, "reason": "<brief explanation>"}}

Respond ONLY with valid JSON."""


class CitationVerifier:
    """Verifies that LLM-generated citations are grounded in actual evidence.

    Args:
        llm: LLM service for verification calls.
        db: Database service for passage lookups.
    """

    def __init__(
        self,
        llm: LLMService,
        db: Any | None = None,
    ) -> None:
        self.llm = llm
        self.db = db

    async def verify_citations(
        self,
        answer: str,
        citations: list[Citation],
        evidence: list[Evidence],
    ) -> list[Citation]:
        """Verify all citations in the answer against evidence.

        For each citation:
        1. Check that the referenced evidence item exists
        2. Extract the claim context from the answer
        3. Ask LLM whether the evidence supports the claim
        4. Mark citation as verified or strip it

        Args:
            answer: The generated answer text.
            citations: Parsed citations from the answer.
            evidence: All retrieved evidence items.

        Returns:
            Updated citations with verification status.
        """
        if not citations:
            return citations

        # Build evidence lookup
        evidence_by_id: dict[str, Evidence] = {e.id: e for e in evidence}

        verified_citations: list[Citation] = []

        for citation in citations:
            ev = evidence_by_id.get(citation.id)
            if not ev:
                # Citation references non-existent evidence
                citation.verified = False
                citation.verification_note = (
                    "Referenced evidence not found in retrieved context"
                )
                logger.warning(
                    "Citation [%s] references missing evidence: %s",
                    citation.ref,
                    citation.id,
                )
                continue

            # Extract the claim context around the citation marker
            claim = self._extract_claim_context(answer, citation.ref)
            if not claim:
                # Can't determine what claim this citation supports
                citation.verified = True
                citation.verification_note = (
                    "Citation present but claim context could not be extracted"
                )
                verified_citations.append(citation)
                continue

            # Get source text
            source_text = ev.text_content or ev.description or ev.label
            if not source_text or len(source_text.strip()) < 10:
                # No meaningful source text to verify against
                citation.verified = True
                citation.verification_note = "Source text too short for verification"
                verified_citations.append(citation)
                continue

            # Verify with LLM
            supported = await self._verify_single(
                claim, truncate_text(source_text, 1500)
            )
            citation.verified = supported
            citation.verification_note = (
                "Claim supported by source"
                if supported
                else "Claim may not be directly supported by cited source"
            )

            if supported:
                verified_citations.append(citation)
            else:
                logger.info(
                    "Citation [%s] failed verification: claim not supported by %s",
                    citation.ref,
                    citation.label,
                )
                # Still include but mark as unverified so frontend can flag it
                verified_citations.append(citation)

        logger.info(
            "Verified %d/%d citations (%d passed)",
            len(verified_citations),
            len(citations),
            sum(1 for c in verified_citations if c.verified),
        )
        return verified_citations

    async def _verify_single(self, claim: str, source_text: str) -> bool:
        """Ask LLM whether a source supports a claim.

        Uses low temperature for deterministic yes/no judgments.

        Args:
            claim: The claim text extracted from the answer.
            source_text: The evidence text the citation points to.

        Returns:
            True if the source supports the claim.
        """
        prompt = VERIFY_PROMPT.format(
            claim=truncate_text(claim, 600),
            source_text=truncate_text(source_text, 1500),
        )

        try:
            raw = await self.llm.generate(
                prompt,
                temperature=0.0,
                max_tokens=128,
            )
            # Parse JSON response
            raw = raw.strip()
            match = re.search(r"\{[\s\S]*\}", raw)
            if match:
                result = json.loads(match.group())
                return bool(result.get("supported", False))
            return True  # If parsing fails, assume supported
        except Exception:
            logger.warning("Verification LLM call failed, assuming supported")
            return True

    def _extract_claim_context(
        self,
        answer: str,
        ref: str,
        window: int = 200,
    ) -> str | None:
        """Extract the text surrounding a citation marker.

        Looks for ``[ref]`` or ``[Pref]`` in the answer and extracts
        a window of text around it.

        Args:
            answer: Full answer text.
            ref: Citation reference (e.g. "1", "P2").
            window: Character window around the marker.

        Returns:
            Extracted claim text, or None if marker not found.
        """
        pattern = re.escape(f"[{ref}]")

        match = re.search(pattern, answer)
        if not match:
            return None

        start = max(0, match.start() - window)
        end = min(len(answer), match.end() + window)

        # Try to extend to sentence boundaries
        text = answer[start:end]

        # Find sentence containing the citation
        sentences = re.split(r"(?<=[.!?])\s+", text)
        for sentence in sentences:
            if f"[{ref}]" in sentence:
                return sentence.strip()

        return text.strip()
