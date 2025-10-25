# Backend Tests

Comprehensive test suite for the Ancient Free Will Database backend.

## Structure

```
tests/
├── conftest.py              # Shared fixtures and configuration
├── unit/                    # Unit tests for services
│   ├── test_llm_service.py
│   ├── test_hybrid_search.py
│   ├── test_kg_analytics.py
│   ├── test_auth_service.py
│   └── test_graphrag_service.py
├── integration/             # Integration tests for API routes
│   ├── test_kg_routes.py
│   ├── test_search_routes.py
│   └── test_graphrag_routes.py
└── README.md               # This file
```

## Running Tests

### All Tests
```bash
cd backend
pytest
```

### Unit Tests Only
```bash
pytest tests/unit/
```

### Integration Tests Only
```bash
pytest tests/integration/
```

### Specific Test File
```bash
pytest tests/unit/test_llm_service.py
```

### Specific Test Function
```bash
pytest tests/unit/test_llm_service.py::TestLLMService::test_health_check_ollama_available
```

### With Coverage Report
```bash
pytest --cov=api --cov=services --cov-report=html
```

Then open `htmlcov/index.html` in your browser.

### Verbose Output
```bash
pytest -v
```

### Stop on First Failure
```bash
pytest -x
```

### Run Failed Tests Only
```bash
pytest --lf
```

## Test Markers

Tests are marked for selective execution:

```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run only slow tests
pytest -m slow

# Skip slow tests
pytest -m "not slow"
```

## Writing Tests

### Unit Test Example

```python
import pytest
from unittest.mock import AsyncMock

class TestMyService:
    """Test cases for MyService"""

    @pytest.mark.asyncio
    async def test_my_function(self, mock_db_service):
        """Test description"""
        # Arrange
        mock_db_service.fetch.return_value = [{"id": 1}]

        # Act
        result = await my_service.get_data()

        # Assert
        assert result is not None
        mock_db_service.fetch.assert_called_once()
```

### Integration Test Example

```python
import pytest
from httpx import AsyncClient

class TestMyRoutes:
    """Test cases for my API routes"""

    @pytest.mark.asyncio
    async def test_endpoint(self, async_client):
        """Test description"""
        response = await async_client.get("/api/my-endpoint")
        assert response.status_code == 200
        data = response.json()
        assert "key" in data
```

## Fixtures

Available fixtures (defined in `conftest.py`):

- `mock_db_service` - Mocked DatabaseService
- `mock_qdrant_service` - Mocked QdrantService
- `mock_llm_service` - Mocked LLMService
- `sample_kg_data` - Sample knowledge graph data
- `sample_text_data` - Sample text data
- `sample_search_results` - Sample search results
- `sample_user_data` - Sample user data
- `test_app` - FastAPI test application
- `async_client` - Async HTTP client
- `sync_client` - Sync HTTP client

## Coverage Goals

- **Unit Tests**: >80% coverage for services
- **Integration Tests**: All API endpoints tested
- **Edge Cases**: Empty inputs, invalid data, errors

## Current Coverage

Run `pytest --cov` to see current coverage statistics.

## Continuous Integration

Tests run automatically via GitHub Actions on:
- Push to main branch
- Pull requests
- Manual workflow dispatch

See `.github/workflows/test.yml` for CI configuration.

## Dependencies

Test dependencies are in `requirements.txt`:
- `pytest>=7.4.0` - Testing framework
- `pytest-asyncio>=0.21.0` - Async test support
- `pytest-cov>=4.1.0` - Coverage reporting
- `pytest-mock>=3.12.0` - Mocking utilities
- `httpx>=0.25.0` - Async HTTP client

## Troubleshooting

### ImportError: No module named 'api'

Make sure you're running tests from the `backend/` directory:
```bash
cd backend
pytest
```

### Async tests not running

Ensure `pytest-asyncio` is installed and `asyncio_mode = auto` is in `pytest.ini`.

### Tests failing due to missing services

Some integration tests may fail if PostgreSQL or Qdrant are not running. Unit tests should always pass as they use mocks.

### Coverage not working

Install coverage dependencies:
```bash
pip install pytest-cov
```

## Best Practices

1. **Isolation**: Each test should be independent
2. **Mocking**: Use mocks for external services (DB, APIs)
3. **Naming**: Use descriptive test names that explain what's being tested
4. **Documentation**: Add docstrings to test classes and functions
5. **Assertions**: Use specific assertions with helpful messages
6. **Cleanup**: Tests should clean up after themselves
7. **Speed**: Keep tests fast (use mocks instead of real services)

## Contributing

When adding new features:

1. Write tests for new functionality
2. Ensure all tests pass: `pytest`
3. Check coverage: `pytest --cov`
4. Run linting: `flake8` and `black --check .`
5. Update this README if adding new test categories

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [Coverage.py](https://coverage.readthedocs.io/)
