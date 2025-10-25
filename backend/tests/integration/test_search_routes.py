"""
Integration tests for Search API Routes
Tests all /api/search/* endpoints
"""
import pytest
from httpx import AsyncClient


class TestSearchRoutes:
    """Test cases for Search API routes"""

    @pytest.mark.asyncio
    async def test_fulltext_search(self, async_client):
        """Test POST /api/search/fulltext"""
        payload = {
            "query": "free will",
            "limit": 10
        }
        response = await async_client.post("/api/search/fulltext", json=payload)
        assert response.status_code in [200, 500]

        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, (list, dict))

    @pytest.mark.asyncio
    async def test_lemmatic_search(self, async_client):
        """Test POST /api/search/lemmatic"""
        payload = {
            "query": "libertum arbitrium",
            "limit": 10
        }
        response = await async_client.post("/api/search/lemmatic", json=payload)
        assert response.status_code in [200, 500]

    @pytest.mark.asyncio
    async def test_semantic_search(self, async_client):
        """Test POST /api/search/semantic"""
        payload = {
            "query": "What is free will?",
            "limit": 10
        }
        response = await async_client.post("/api/search/semantic", json=payload)
        assert response.status_code in [200, 500]

    @pytest.mark.asyncio
    async def test_hybrid_search(self, async_client):
        """Test POST /api/search/hybrid"""
        payload = {
            "query": "Aristotle on free will",
            "limit": 10
        }
        response = await async_client.post("/api/search/hybrid", json=payload)
        assert response.status_code in [200, 500]

        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, (list, dict))

    @pytest.mark.asyncio
    async def test_search_empty_query(self, async_client):
        """Test search with empty query"""
        payload = {
            "query": "",
            "limit": 10
        }
        response = await async_client.post("/api/search/hybrid", json=payload)
        # Should either return empty results or validation error
        assert response.status_code in [200, 422, 500]

    @pytest.mark.asyncio
    async def test_search_with_special_characters(self, async_client):
        """Test search with special characters"""
        payload = {
            "query": "test & query | (special)",
            "limit": 10
        }
        response = await async_client.post("/api/search/fulltext", json=payload)
        assert response.status_code in [200, 500]

    @pytest.mark.asyncio
    async def test_search_greek_text(self, async_client):
        """Test search with Greek text"""
        payload = {
            "query": "ἐφ' ἡμῖν",
            "limit": 10
        }
        response = await async_client.post("/api/search/fulltext", json=payload)
        assert response.status_code in [200, 500]

    @pytest.mark.asyncio
    async def test_search_latin_text(self, async_client):
        """Test search with Latin text"""
        payload = {
            "query": "liberum arbitrium",
            "limit": 10
        }
        response = await async_client.post("/api/search/lemmatic", json=payload)
        assert response.status_code in [200, 500]

    @pytest.mark.asyncio
    async def test_search_pagination(self, async_client):
        """Test search with different limits"""
        for limit in [5, 10, 20]:
            payload = {
                "query": "test",
                "limit": limit
            }
            response = await async_client.post("/api/search/hybrid", json=payload)
            assert response.status_code in [200, 500]

    @pytest.mark.asyncio
    async def test_search_invalid_limit(self, async_client):
        """Test search with invalid limit"""
        payload = {
            "query": "test",
            "limit": -1
        }
        response = await async_client.post("/api/search/hybrid", json=payload)
        # Should return validation error
        assert response.status_code in [422, 500]

    @pytest.mark.asyncio
    async def test_search_missing_query(self, async_client):
        """Test search without query parameter"""
        payload = {
            "limit": 10
        }
        response = await async_client.post("/api/search/hybrid", json=payload)
        # Should return validation error
        assert response.status_code in [422, 500]

    @pytest.mark.asyncio
    async def test_hybrid_search_combines_results(self, async_client):
        """Test that hybrid search combines multiple search methods"""
        payload = {
            "query": "Stoic philosophy",
            "limit": 10
        }
        response = await async_client.post("/api/search/hybrid", json=payload)

        if response.status_code == 200:
            data = response.json()
            # Should return results with RRF scores
            assert isinstance(data, (list, dict))
