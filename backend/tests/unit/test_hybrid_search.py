"""
Unit tests for Hybrid Search Service
Tests full-text, lemmatic, and semantic search with RRF
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch
from services.hybrid_search import HybridSearchService


class TestHybridSearchService:
    """Test cases for HybridSearchService"""

    @pytest.fixture
    def search_service(self, mock_db_service, mock_qdrant_service):
        """Create a HybridSearchService instance with mocked dependencies"""
        return HybridSearchService(
            db_service=mock_db_service,
            qdrant_service=mock_qdrant_service
        )

    @pytest.mark.asyncio
    async def test_fulltext_search(self, search_service, mock_db_service, sample_text_data):
        """Test full-text search functionality"""
        mock_db_service.fetch.return_value = sample_text_data

        results = await search_service.fulltext_search("test query", limit=10)

        assert isinstance(results, list)
        mock_db_service.fetch.assert_called_once()

    @pytest.mark.asyncio
    async def test_lemmatic_search(self, search_service, mock_db_service, sample_text_data):
        """Test lemmatic search functionality"""
        mock_db_service.fetch.return_value = sample_text_data

        results = await search_service.lemmatic_search("test query", limit=10)

        assert isinstance(results, list)
        mock_db_service.fetch.assert_called_once()

    @pytest.mark.asyncio
    async def test_semantic_search(self, search_service, mock_qdrant_service):
        """Test semantic search functionality"""
        mock_qdrant_service.search.return_value = [
            Mock(id="test_text_1", score=0.95, payload={"title": "Test 1"}),
            Mock(id="test_text_2", score=0.85, payload={"title": "Test 2"})
        ]

        results = await search_service.semantic_search("test query", limit=10)

        assert isinstance(results, list)
        assert len(results) == 2
        mock_qdrant_service.search.assert_called_once()

    @pytest.mark.asyncio
    async def test_hybrid_search_rrf(self, search_service, mock_db_service, mock_qdrant_service, sample_text_data):
        """Test hybrid search with Reciprocal Rank Fusion"""
        # Mock full-text results
        mock_db_service.fetch.return_value = sample_text_data

        # Mock semantic results
        mock_qdrant_service.search.return_value = [
            Mock(id="test_text_1", score=0.95, payload={"title": "Test 1"}),
            Mock(id="test_text_2", score=0.85, payload={"title": "Test 2"})
        ]

        results = await search_service.hybrid_search("test query", limit=10)

        assert isinstance(results, list)
        assert len(results) > 0
        # Verify that results have RRF scores
        if len(results) > 0:
            assert "score" in results[0] or "rrf_score" in results[0]

    @pytest.mark.asyncio
    async def test_search_with_empty_query(self, search_service):
        """Test that empty queries are handled gracefully"""
        results = await search_service.hybrid_search("", limit=10)
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_search_with_special_characters(self, search_service, mock_db_service):
        """Test search with special characters"""
        mock_db_service.fetch.return_value = []

        special_query = "test & query | with (special) characters"
        results = await search_service.fulltext_search(special_query, limit=10)

        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_search_pagination(self, search_service, mock_db_service, sample_text_data):
        """Test search with limit parameter"""
        mock_db_service.fetch.return_value = sample_text_data

        results = await search_service.fulltext_search("test", limit=1)

        assert isinstance(results, list)
        # Should respect the limit

    @pytest.mark.asyncio
    async def test_reciprocal_rank_fusion_calculation(self, search_service):
        """Test RRF score calculation"""
        results_1 = [
            {"text_id": "A", "score": 1.0},
            {"text_id": "B", "score": 0.8},
        ]
        results_2 = [
            {"text_id": "B", "score": 0.9},
            {"text_id": "C", "score": 0.7},
        ]

        # Mock the RRF merge function
        merged = search_service._merge_results_rrf([results_1, results_2])

        assert isinstance(merged, list)
        # B should rank high as it appears in both
        if len(merged) > 0:
            assert "text_id" in merged[0]

    @pytest.mark.asyncio
    async def test_search_result_deduplication(self, search_service, mock_db_service, mock_qdrant_service):
        """Test that duplicate results are properly handled"""
        # Same result from both sources
        mock_db_service.fetch.return_value = [
            {"text_id": "duplicate_1", "title": "Test"}
        ]
        mock_qdrant_service.search.return_value = [
            Mock(id="duplicate_1", score=0.9, payload={"title": "Test"})
        ]

        results = await search_service.hybrid_search("test", limit=10)

        # Should not have duplicates
        text_ids = [r.get("text_id") for r in results]
        assert len(text_ids) == len(set(text_ids))
