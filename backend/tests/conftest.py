"""
Pytest configuration and shared fixtures for backend tests
"""
import asyncio
import pytest
import os
from typing import AsyncGenerator, Dict, Any
from fastapi.testclient import TestClient
from httpx import AsyncClient
from unittest.mock import Mock, AsyncMock, MagicMock

# Set test environment
os.environ["TESTING"] = "true"
os.environ["BYPASS_AUTH"] = "true"


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_db_service():
    """Mock DatabaseService for testing"""
    mock = AsyncMock()
    mock.is_connected.return_value = True
    mock.connect = AsyncMock()
    mock.close = AsyncMock()
    mock.fetch = AsyncMock()
    mock.fetchrow = AsyncMock()
    mock.fetchval = AsyncMock()
    mock.execute = AsyncMock()
    return mock


@pytest.fixture
def mock_qdrant_service():
    """Mock QdrantService for testing"""
    mock = AsyncMock()
    mock.is_connected.return_value = True
    mock.connect = AsyncMock()
    mock.close = AsyncMock()
    mock.search = AsyncMock(return_value=[])
    mock.upsert = AsyncMock()
    return mock


@pytest.fixture
def mock_llm_service():
    """Mock LLMService for testing"""
    mock = AsyncMock()
    mock.generate = AsyncMock(return_value="This is a test response from the LLM.")
    mock.health_check = AsyncMock(return_value={
        "ollama": {"available": True, "model": "mistral:7b"},
        "gemini": {"available": True, "model": "gemini-2.0-flash-exp"}
    })
    mock.get_provider_info = Mock(return_value={
        "provider": "ollama",
        "model": "mistral:7b",
        "available": True
    })
    return mock


@pytest.fixture
def sample_kg_data() -> Dict[str, Any]:
    """Sample knowledge graph data for testing"""
    return {
        "metadata": {
            "title": "Test Ancient Free Will Database",
            "version": "1.0.0-test",
            "statistics": {
                "total_nodes": 3,
                "total_edges": 2
            }
        },
        "nodes": [
            {
                "id": "person_aristotle_test",
                "label": "Aristotle",
                "type": "person",
                "category": "philosopher",
                "description": "Ancient Greek philosopher",
                "period": "Classical Greek",
                "school": "Peripatetic",
                "dates": "384-322 BCE"
            },
            {
                "id": "concept_free_will_test",
                "label": "Free Will",
                "type": "concept",
                "category": "philosophical_concept",
                "description": "The concept of free will",
                "greek_term": "αὐτεξούσιον (autexousion)"
            },
            {
                "id": "work_ethics_test",
                "label": "Nicomachean Ethics",
                "type": "work",
                "category": "treatise",
                "description": "Aristotle's major ethical work"
            }
        ],
        "edges": [
            {
                "source": "person_aristotle_test",
                "target": "work_ethics_test",
                "relation": "authored"
            },
            {
                "source": "person_aristotle_test",
                "target": "concept_free_will_test",
                "relation": "discussed"
            }
        ]
    }


@pytest.fixture
def sample_text_data() -> list:
    """Sample text data for testing"""
    return [
        {
            "text_id": "test_text_1",
            "title": "Test Text 1",
            "author": "Test Author",
            "category": "Test Category",
            "language": "greek",
            "content": "Sample Greek text content",
            "lemmatized_content": "sample greek text content",
            "metadata": {"test": "metadata"}
        },
        {
            "text_id": "test_text_2",
            "title": "Test Text 2",
            "author": "Test Author",
            "category": "Test Category",
            "language": "latin",
            "content": "Sample Latin text content",
            "lemmatized_content": "sample latin text content",
            "metadata": {"test": "metadata"}
        }
    ]


@pytest.fixture
def sample_search_results():
    """Sample search results for testing"""
    return [
        {
            "text_id": "test_text_1",
            "title": "Test Text 1",
            "author": "Test Author",
            "snippet": "...sample text...",
            "score": 0.95,
            "rank": 1
        },
        {
            "text_id": "test_text_2",
            "title": "Test Text 2",
            "author": "Test Author",
            "snippet": "...another sample...",
            "score": 0.85,
            "rank": 2
        }
    ]


@pytest.fixture
def sample_user_data():
    """Sample user data for testing"""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword123"
    }


@pytest.fixture
async def test_app():
    """Create a test FastAPI application"""
    from api.main import app
    return app


@pytest.fixture
async def async_client(test_app) -> AsyncGenerator:
    """Create an async HTTP client for testing"""
    async with AsyncClient(app=test_app, base_url="http://test") as client:
        yield client


@pytest.fixture
def sync_client(test_app):
    """Create a synchronous test client"""
    return TestClient(test_app)
