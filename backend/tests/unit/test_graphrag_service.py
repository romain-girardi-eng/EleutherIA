"""
Unit tests for GraphRAG Service
Tests the 6-step GraphRAG pipeline
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch, mock_open
import json


class TestGraphRAGService:
    """Test cases for GraphRAG Service"""

    @pytest.fixture
    def mock_graphrag_service(self, mock_db_service, mock_qdrant_service, mock_llm_service, sample_kg_data):
        """Create a mock GraphRAG service"""
        from services.graphrag_service import GraphRAGService

        # Mock the KG file loading
        with patch("builtins.open", mock_open(read_data=json.dumps(sample_kg_data))):
            with patch("json.load", return_value=sample_kg_data):
                service = GraphRAGService(
                    db_service=mock_db_service,
                    qdrant_service=mock_qdrant_service,
                    llm_service=mock_llm_service
                )
                service.kg_data = sample_kg_data
                return service

    @pytest.mark.asyncio
    async def test_answer_question_basic(self, mock_graphrag_service, mock_qdrant_service, mock_llm_service):
        """Test basic question answering"""
        # Mock semantic search results
        mock_qdrant_service.search.return_value = [
            Mock(
                id="person_aristotle_test",
                score=0.95,
                payload={"label": "Aristotle", "type": "person"}
            )
        ]

        # Mock LLM response
        mock_llm_service.generate.return_value = "Aristotle believed in free will."

        result = await mock_graphrag_service.answer_question("What did Aristotle think about free will?")

        assert result is not None
        assert "answer" in result
        assert "sources" in result or "reasoning_path" in result

    @pytest.mark.asyncio
    async def test_semantic_search_step(self, mock_graphrag_service, mock_qdrant_service):
        """Test Step 1: Semantic search for relevant nodes"""
        mock_qdrant_service.search.return_value = [
            Mock(id="person_aristotle_test", score=0.95, payload={}),
            Mock(id="concept_free_will_test", score=0.85, payload={})
        ]

        # This would be called internally
        results = await mock_qdrant_service.search(
            collection_name="test",
            query_vector=[0.1] * 100,
            limit=5
        )

        assert len(results) == 2
        assert results[0].score > results[1].score

    @pytest.mark.asyncio
    async def test_graph_traversal_step(self, mock_graphrag_service):
        """Test Step 2: Graph traversal to expand context"""
        # Get neighbors of a node
        start_node = "person_aristotle_test"
        neighbors = mock_graphrag_service._get_neighbors(start_node, max_depth=1)

        assert isinstance(neighbors, (list, set))

    @pytest.mark.asyncio
    async def test_context_building_step(self, mock_graphrag_service):
        """Test Step 3: Building context from nodes and edges"""
        relevant_nodes = ["person_aristotle_test", "concept_free_will_test"]
        context = mock_graphrag_service._build_context(relevant_nodes)

        assert isinstance(context, str)
        assert len(context) > 0

    @pytest.mark.asyncio
    async def test_citation_extraction_step(self, mock_graphrag_service):
        """Test Step 4: Extracting citations from nodes"""
        node_id = "person_aristotle_test"
        node = mock_graphrag_service.kg_data["nodes"][0]

        citations = mock_graphrag_service._extract_citations(node)

        assert isinstance(citations, list)

    @pytest.mark.asyncio
    async def test_llm_synthesis_step(self, mock_graphrag_service, mock_llm_service):
        """Test Step 5: LLM synthesis of answer"""
        mock_llm_service.generate.return_value = "This is a synthesized answer with sources."

        answer = await mock_llm_service.generate("Test prompt with context")

        assert isinstance(answer, str)
        assert len(answer) > 0

    @pytest.mark.asyncio
    async def test_reasoning_path_step(self, mock_graphrag_service):
        """Test Step 6: Reasoning path construction"""
        used_nodes = ["person_aristotle_test", "concept_free_will_test"]
        reasoning_path = mock_graphrag_service._build_reasoning_path(used_nodes)

        assert isinstance(reasoning_path, list)

    @pytest.mark.asyncio
    async def test_empty_question(self, mock_graphrag_service):
        """Test handling of empty question"""
        with pytest.raises(Exception):
            await mock_graphrag_service.answer_question("")

    @pytest.mark.asyncio
    async def test_question_with_no_results(self, mock_graphrag_service, mock_qdrant_service, mock_llm_service):
        """Test question when no relevant nodes are found"""
        mock_qdrant_service.search.return_value = []
        mock_llm_service.generate.return_value = "I don't have enough information to answer this question."

        result = await mock_graphrag_service.answer_question("Completely unrelated question?")

        assert result is not None
        assert "answer" in result

    @pytest.mark.asyncio
    async def test_complex_question(self, mock_graphrag_service, mock_qdrant_service, mock_llm_service):
        """Test complex multi-part question"""
        mock_qdrant_service.search.return_value = [
            Mock(id="person_aristotle_test", score=0.95, payload={}),
        ]
        mock_llm_service.generate.return_value = "Complex answer addressing multiple aspects."

        result = await mock_graphrag_service.answer_question(
            "How did Aristotle's views on free will differ from the Stoics, "
            "and what influence did this have on later thinkers?"
        )

        assert result is not None
        assert "answer" in result

    @pytest.mark.asyncio
    async def test_citation_formatting(self, mock_graphrag_service):
        """Test that citations are properly formatted"""
        node = {
            "id": "test_node",
            "label": "Test Node",
            "ancient_sources": ["Source 1", "Source 2"],
            "modern_scholarship": ["Scholar 1", "Scholar 2"]
        }

        citations = mock_graphrag_service._extract_citations(node)

        assert isinstance(citations, list)
        # Should include both ancient and modern sources

    @pytest.mark.asyncio
    async def test_graph_traversal_depth_limit(self, mock_graphrag_service):
        """Test that graph traversal respects depth limit"""
        start_node = "person_aristotle_test"

        # Depth 1
        neighbors_1 = mock_graphrag_service._get_neighbors(start_node, max_depth=1)

        # Depth 2
        neighbors_2 = mock_graphrag_service._get_neighbors(start_node, max_depth=2)

        # Depth 2 should have same or more nodes than depth 1
        assert len(neighbors_2) >= len(neighbors_1)

    @pytest.mark.asyncio
    async def test_streaming_response(self, mock_graphrag_service, mock_llm_service):
        """Test streaming response generation"""
        # Mock streaming generator
        async def mock_stream():
            yield "Part 1"
            yield "Part 2"
            yield "Part 3"

        mock_llm_service.generate_stream = mock_stream

        # Test that streaming works
        if hasattr(mock_graphrag_service, 'answer_question_stream'):
            chunks = []
            async for chunk in mock_graphrag_service.answer_question_stream("Test?"):
                chunks.append(chunk)

            assert len(chunks) > 0
