"""
Cross-Encoder Reranking Service.

Uses a cross-encoder model (BAAI/bge-reranker-v2-m3) to rerank evidence
after initial retrieval.  Cross-encoders see query AND evidence together
(not just embedding similarity), yielding ~33% precision improvement on
average, and up to ~47% on multi-hop queries.

The model is loaded once at startup and runs inference on CPU.
"""

from __future__ import annotations

import asyncio
import logging
import threading
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sentence_transformers import CrossEncoder

    from eleutheria_graphrag.agents.state import Evidence

logger = logging.getLogger(__name__)

# Default model — multilingual, handles Greek/Latin better than ms-marco
DEFAULT_MODEL = "BAAI/bge-reranker-v2-m3"
DEFAULT_SCORE_THRESHOLD = 0.3
DEFAULT_TOP_K = 20


class RerankerService:
    """Cross-encoder reranking service.

    Loads a ``sentence-transformers`` ``CrossEncoder`` model once and
    provides a ``rerank()`` method that scores (query, evidence_text)
    pairs and returns the top-k results.

    Args:
        model_name: HuggingFace model ID for the cross-encoder.
        top_k: Maximum number of evidence items to return.
        score_threshold: Minimum cross-encoder score to keep an item.
    """

    def __init__(
        self,
        model_name: str = DEFAULT_MODEL,
        top_k: int = DEFAULT_TOP_K,
        score_threshold: float = DEFAULT_SCORE_THRESHOLD,
    ) -> None:
        self.model_name = model_name
        self.top_k = top_k
        self.score_threshold = score_threshold
        self._model: CrossEncoder | None = None
        self._model_lock = threading.Lock()

    def _load_model(self) -> CrossEncoder:
        """Lazy-load the cross-encoder model (thread-safe)."""
        if self._model is None:
            with self._model_lock:
                # Double-check after acquiring lock
                if self._model is None:
                    from sentence_transformers import CrossEncoder

                    logger.info("Loading cross-encoder model: %s", self.model_name)
                    try:
                        self._model = CrossEncoder(self.model_name)
                    except Exception:
                        logger.exception("Failed to load cross-encoder model")
                        raise
                    logger.info("Cross-encoder model loaded")
        return self._model

    async def rerank(
        self,
        query: str,
        evidence: list[Evidence],
        top_k: int | None = None,
        score_threshold: float | None = None,
    ) -> list[Evidence]:
        """Rerank evidence items using the cross-encoder.

        Args:
            query: The user query to score against.
            evidence: List of ``Evidence`` items to rerank.
            top_k: Override default top-k.
            score_threshold: Override default score threshold.

        Returns:
            Reranked and filtered list of ``Evidence`` items,
            with ``score`` updated to the cross-encoder score.
        """
        if not evidence:
            return []

        top_k = top_k or self.top_k
        score_threshold = score_threshold or self.score_threshold

        model = self._load_model()

        # Build (query, document) pairs for scoring
        pairs: list[tuple[str, str]] = []
        for ev in evidence:
            # Use the most informative text available
            text = ev.text_content or ev.description or ev.label
            if not text:
                text = ev.label
            pairs.append((query, text[:512]))  # Truncate for efficiency

        # Score all pairs — run in thread to avoid blocking the event loop
        try:
            scores = await asyncio.to_thread(model.predict, pairs)
        except Exception:
            logger.exception("Cross-encoder prediction failed")
            return evidence[:top_k]

        # Combine scores with evidence
        scored = list(zip(scores, evidence, strict=True))
        scored.sort(key=lambda x: x[0], reverse=True)

        # Filter and limit
        results: list[Evidence] = []
        for score, ev in scored[:top_k]:
            if float(score) < score_threshold:
                break
            ev.score = float(score)
            results.append(ev)

        logger.info(
            "Reranked %d -> %d items (threshold=%.2f)",
            len(evidence),
            len(results),
            score_threshold,
        )
        return results
