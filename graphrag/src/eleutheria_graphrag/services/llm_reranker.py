"""LLM-based scholarly reranker with domain-aware criteria."""

from __future__ import annotations

import json
import logging
import re
from typing import TYPE_CHECKING

from eleutheria_graphrag.agents.prompts import delimit_retrieved_text
from eleutheria_graphrag.agents.state import Evidence
from eleutheria_graphrag.agents.text_utils import truncate_text

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from eleutheria_graphrag.services.llm_service import LLMService

MAX_CANDIDATES_PER_CALL = 30
TEXT_PREVIEW_LEN = 400

LLM_RERANK_PROMPT = """\
You are an expert in ancient philosophy, specializing in Greek and Roman \
debates about fate, free will, and moral responsibility.

TASK: Rate each passage's relevance to the research question on a scale of 0-100.

RESEARCH QUESTION: "{query}"

CANDIDATE PASSAGES:
{candidates}

SCORING GUIDELINES:
- 90-100: Directly addresses the question with specific relevant content
- 70-89: Highly relevant, discusses key concepts/philosophers mentioned
- 50-69: Moderately relevant, related topic but not directly answering
- 30-49: Tangentially relevant, mentions some related terms
- 0-29: Not relevant to the question

Return ONLY a valid JSON object (no markdown):
{{"rankings": [{{"id": 1, "score": 85, "reason": "Brief explanation"}}, ...]}}

Include ALL {count} passages in your rankings."""


class LLMRerankerService:
    """LLM-based scholarly reranking with domain-aware criteria."""

    def __init__(self, llm: LLMService) -> None:
        self.llm = llm

    async def rerank(
        self,
        query: str,
        evidence: list[Evidence],
        top_k: int = 15,
    ) -> list[Evidence]:
        """Rerank evidence using LLM scholarly evaluation."""
        candidates = evidence[:MAX_CANDIDATES_PER_CALL]

        # Format candidates for prompt
        formatted = []
        for i, ev in enumerate(candidates):
            text = truncate_text(
                ev.text_content or ev.description or ev.label, TEXT_PREVIEW_LEN
            )
            formatted.append(
                delimit_retrieved_text(
                    f'[{i + 1}] {ev.label}: "{text}"',
                    data_id=f"rerank-candidate:{i + 1}",
                )
            )

        prompt = LLM_RERANK_PROMPT.format(
            query=query,
            candidates="\n".join(formatted),
            count=len(candidates),
        )

        try:
            raw = await self.llm.generate(
                prompt, temperature=0.0, max_tokens=2048, tier="utility"
            )
            raw = raw.strip()
            match = re.search(r"\{[\s\S]*\}", raw)
            if match:
                raw = match.group(0)
            result = json.loads(raw)
            rankings = result.get("rankings", [])

            score_map: dict[int, tuple[int, str]] = {}
            for r in rankings:
                score_map[r["id"]] = (r["score"], r.get("reason", ""))

            for i, ev in enumerate(candidates):
                if (i + 1) in score_map:
                    ev.score = score_map[i + 1][0] / 100.0
                else:
                    ev.score = 0.5

        except Exception:
            logger.warning("LLM reranking failed, using fallback scores")
            for i, ev in enumerate(candidates):
                ev.score = (50 - i) / 100.0

        candidates.sort(key=lambda e: e.score, reverse=True)
        return candidates[:top_k]
