"""HyDE (Hypothetical Document Embeddings) service.

Generates a hypothetical scholarly passage for a query, embeds it,
and searches Qdrant with the hypothetical embedding to bridge the
semantic gap between question-style and answer-style text.
"""

from __future__ import annotations

import asyncio
import logging
import os
from typing import TYPE_CHECKING, Any

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from eleutheria_graphrag.services.llm_service import LLMService
    from eleutheria_kg.services.qdrant import QdrantService

HYDE_PROMPT = """\
You are an expert classicist specializing in ancient Greek and Roman \
philosophy, particularly debates about fate, free will, and moral \
responsibility.

Write a scholarly passage (150-200 words) that would perfectly answer \
this question: "{query}"

Requirements:
- Include specific philosophers by name (Chrysippus, Epictetus, Epicurus, \
Alexander of Aphrodisias, etc.)
- Include Greek philosophical terms with transliterations \
(e.g. εἱμαρμένη / heimarmenē, τὸ ἐφ' ἡμῖν / to eph' hēmin)
- Reference specific ancient works (De Fato, Meditations, etc.)
- Use academic register and precision

Write only the passage, no preamble."""

CONFIDENCE_DISCOUNT = 0.9


async def _get_embedding(text: str) -> list[float]:
    """Get embedding via Gemini embedding API."""
    import google.generativeai as genai

    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY required for embeddings")

    genai.configure(api_key=api_key)

    def _embed() -> list[float]:
        result = genai.embed_content(
            model="models/gemini-embedding-001",
            content=text,
        )
        return result["embedding"]

    return await asyncio.to_thread(_embed)


class HyDEService:
    """Hypothetical Document Embeddings for semantic gap bridging."""

    def __init__(self, llm: LLMService, qdrant: QdrantService) -> None:
        self.llm = llm
        self.qdrant = qdrant

    async def generate_hypothetical(self, query: str) -> str:
        """Generate a 150-200 word hypothetical scholarly passage."""
        prompt = HYDE_PROMPT.format(query=query)
        return await self.llm.generate(prompt, temperature=0.7, max_tokens=512)

    async def search_nodes(
        self, query: str, limit: int = 10
    ) -> list[dict[str, Any]]:
        """Generate hypothetical doc, embed it, search KG nodes."""
        hypothetical = await self.generate_hypothetical(query)
        embedding = await _get_embedding(hypothetical)
        results = await self.qdrant.search_nodes(embedding, limit=limit)

        # Apply confidence discount
        for r in results:
            r["score"] = r.get("score", 0.0) * CONFIDENCE_DISCOUNT

        return results

    @staticmethod
    def rrf_fusion(
        list_a: list[dict[str, Any]],
        list_b: list[dict[str, Any]],
        k: int = 60,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Reciprocal Rank Fusion of two result lists."""
        scores: dict[str, float] = {}
        items: dict[str, dict[str, Any]] = {}

        for rank, item in enumerate(list_a):
            item_id = item["id"]
            scores[item_id] = scores.get(item_id, 0.0) + 1.0 / (k + rank + 1)
            items[item_id] = item

        for rank, item in enumerate(list_b):
            item_id = item["id"]
            scores[item_id] = scores.get(item_id, 0.0) + 1.0 / (k + rank + 1)
            items[item_id] = item

        merged = []
        for item_id, rrf_score in sorted(
            scores.items(), key=lambda x: x[1], reverse=True
        ):
            entry = {**items[item_id], "rrf_score": rrf_score}
            merged.append(entry)

        return merged[:limit]
