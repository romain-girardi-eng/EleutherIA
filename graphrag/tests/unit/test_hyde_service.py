"""Tests for HyDE (Hypothetical Document Embeddings) service."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from eleutheria_graphrag.services.hyde_service import HyDEService


@pytest.fixture
def llm():
    mock = MagicMock()
    mock.generate = AsyncMock(return_value="Chrysippus argued that fate...")
    return mock


@pytest.fixture
def qdrant():
    mock = MagicMock()
    mock.search_nodes = AsyncMock(return_value=[
        {"id": "chrysippus", "score": 0.92, "label": "Chrysippus"},
        {"id": "fate", "score": 0.88, "label": "Heimarmenē"},
    ])
    return mock


@pytest.fixture
def service(llm, qdrant):
    return HyDEService(llm=llm, qdrant=qdrant)


class TestGenerateHypothetical:
    @pytest.mark.asyncio
    async def test_returns_text(self, service):
        with patch(
            "eleutheria_graphrag.services.hyde_service._get_embedding",
            new_callable=AsyncMock,
            return_value=[0.1] * 768,
        ):
            result = await service.generate_hypothetical("What is Stoic fate?")
            assert isinstance(result, str)
            assert len(result) > 0

    @pytest.mark.asyncio
    async def test_llm_called_with_prompt(self, service, llm):
        with patch(
            "eleutheria_graphrag.services.hyde_service._get_embedding",
            new_callable=AsyncMock,
            return_value=[0.1] * 768,
        ):
            await service.generate_hypothetical("What is Stoic fate?")
            llm.generate.assert_called_once()
            prompt = llm.generate.call_args[0][0]
            assert "scholarly passage" in prompt.lower() or "classicist" in prompt.lower()


class TestSearchNodes:
    @pytest.mark.asyncio
    async def test_returns_results(self, service, qdrant):
        with patch(
            "eleutheria_graphrag.services.hyde_service._get_embedding",
            new_callable=AsyncMock,
            return_value=[0.1] * 768,
        ):
            results = await service.search_nodes("What is Stoic fate?", limit=5)
            assert len(results) == 2
            qdrant.search_nodes.assert_called_once()

    @pytest.mark.asyncio
    async def test_applies_confidence_discount(self, service):
        with patch(
            "eleutheria_graphrag.services.hyde_service._get_embedding",
            new_callable=AsyncMock,
            return_value=[0.1] * 768,
        ):
            results = await service.search_nodes("What is Stoic fate?")
            # HyDE results get 0.9x discount
            assert results[0]["score"] == pytest.approx(0.92 * 0.9, rel=0.01)


class TestRRFFusion:
    @pytest.mark.asyncio
    async def test_merge_deduplicates(self, service):
        standard = [
            {"id": "a", "score": 0.9},
            {"id": "b", "score": 0.8},
        ]
        hyde = [
            {"id": "b", "score": 0.85},
            {"id": "c", "score": 0.7},
        ]
        merged = service.rrf_fusion(standard, hyde, k=60, limit=10)
        ids = [r["id"] for r in merged]
        assert len(ids) == len(set(ids))  # no duplicates
        assert "b" in ids  # shared item present

    @pytest.mark.asyncio
    async def test_rrf_k60(self, service):
        standard = [{"id": "a", "score": 0.9}]
        hyde = [{"id": "a", "score": 0.8}]
        merged = service.rrf_fusion(standard, hyde, k=60, limit=10)
        # a appears in both lists at rank 0: score = 2 * 1/(60+1)
        expected = 2.0 / 61.0
        assert merged[0]["rrf_score"] == pytest.approx(expected, rel=0.01)
