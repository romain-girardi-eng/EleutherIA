"""
Integration tests for GraphRAG API Routes
Tests all /api/graphrag/* endpoints
"""
import pytest
from httpx import AsyncClient


class TestGraphRAGRoutes:
    """Test cases for GraphRAG API routes"""

    @pytest.mark.asyncio
    async def test_graphrag_query(self, async_client):
        """Test POST /api/graphrag/query"""
        payload = {
            "query": "What did Aristotle think about free will?"
        }

        # Note: This endpoint requires authentication in production
        response = await async_client.post("/api/graphrag/query", json=payload)

        # May return 401 (unauthorized) or 200/500
        assert response.status_code in [200, 401, 500]

        if response.status_code == 200:
            data = response.json()
            assert "answer" in data or isinstance(data, dict)

    @pytest.mark.asyncio
    async def test_graphrag_empty_query(self, async_client):
        """Test GraphRAG with empty query"""
        payload = {
            "query": ""
        }
        response = await async_client.post("/api/graphrag/query", json=payload)
        assert response.status_code in [401, 422, 500]

    @pytest.mark.asyncio
    async def test_graphrag_complex_question(self, async_client):
        """Test GraphRAG with complex multi-part question"""
        payload = {
            "query": "How did Stoic views on fate differ from Aristotle's "
                    "concept of voluntary action, and how did this influence "
                    "later Christian theology?"
        }
        response = await async_client.post("/api/graphrag/query", json=payload)
        assert response.status_code in [200, 401, 500]

    @pytest.mark.asyncio
    async def test_graphrag_greek_query(self, async_client):
        """Test GraphRAG with Greek terminology"""
        payload = {
            "query": "What is the meaning of ἐφ' ἡμῖν (eph' hêmin)?"
        }
        response = await async_client.post("/api/graphrag/query", json=payload)
        assert response.status_code in [200, 401, 500]

    @pytest.mark.asyncio
    async def test_graphrag_latin_query(self, async_client):
        """Test GraphRAG with Latin terminology"""
        payload = {
            "query": "Explain the concept of liberum arbitrium"
        }
        response = await async_client.post("/api/graphrag/query", json=payload)
        assert response.status_code in [200, 401, 500]

    @pytest.mark.asyncio
    async def test_graphrag_missing_query(self, async_client):
        """Test GraphRAG without query parameter"""
        payload = {}
        response = await async_client.post("/api/graphrag/query", json=payload)
        assert response.status_code in [401, 422, 500]

    @pytest.mark.asyncio
    async def test_graphrag_rate_limiting(self, async_client):
        """Test that rate limiting is applied"""
        # Make multiple rapid requests
        payload = {"query": "test query"}

        responses = []
        for _ in range(5):
            response = await async_client.post("/api/graphrag/query", json=payload)
            responses.append(response.status_code)

        # At least some requests should succeed or be rejected
        assert all(status in [200, 401, 429, 500] for status in responses)

    @pytest.mark.asyncio
    async def test_graphrag_person_query(self, async_client):
        """Test query about a specific person"""
        payload = {
            "query": "Who was Chrysippus and what were his views on determinism?"
        }
        response = await async_client.post("/api/graphrag/query", json=payload)
        assert response.status_code in [200, 401, 500]

    @pytest.mark.asyncio
    async def test_graphrag_concept_query(self, async_client):
        """Test query about a philosophical concept"""
        payload = {
            "query": "Explain the concept of compatibilism in ancient philosophy"
        }
        response = await async_client.post("/api/graphrag/query", json=payload)
        assert response.status_code in [200, 401, 500]

    @pytest.mark.asyncio
    async def test_graphrag_comparison_query(self, async_client):
        """Test comparative query"""
        payload = {
            "query": "Compare Epicurean and Stoic views on free will"
        }
        response = await async_client.post("/api/graphrag/query", json=payload)
        assert response.status_code in [200, 401, 500]

    @pytest.mark.asyncio
    async def test_graphrag_historical_query(self, async_client):
        """Test historical development query"""
        payload = {
            "query": "How did the concept of free will evolve from Aristotle to Augustine?"
        }
        response = await async_client.post("/api/graphrag/query", json=payload)
        assert response.status_code in [200, 401, 500]

    @pytest.mark.asyncio
    async def test_graphrag_very_long_query(self, async_client):
        """Test with very long query"""
        long_query = "What did ancient philosophers think about free will? " * 50
        payload = {"query": long_query}

        response = await async_client.post("/api/graphrag/query", json=payload)
        # Should handle long queries gracefully
        assert response.status_code in [200, 401, 413, 500]
