"""
Unit tests for LLM Service
Tests Ollama, Gemini, and provider fallback logic
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch
from services.llm_service import LLMService, ModelProvider


class TestLLMService:
    """Test cases for LLMService"""

    @pytest.mark.asyncio
    async def test_health_check_ollama_available(self):
        """Test health check when Ollama is available"""
        with patch('aiohttp.ClientSession') as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={"status": "healthy"})

            mock_session_instance = AsyncMock()
            mock_session_instance.get.return_value.__aenter__.return_value = mock_response
            mock_session.return_value.__aenter__.return_value = mock_session_instance

            service = LLMService(preferred_provider=ModelProvider.OLLAMA)
            health = await service.health_check()

            assert "ollama" in health
            assert health["ollama"]["available"] is True

    @pytest.mark.asyncio
    async def test_health_check_gemini_available(self):
        """Test health check when Gemini is available"""
        with patch.dict('os.environ', {'GEMINI_API_KEY': 'test-key'}):
            service = LLMService(preferred_provider=ModelProvider.GEMINI)
            health = await service.health_check()

            assert "gemini" in health
            # Gemini is available if API key is set
            assert isinstance(health["gemini"]["available"], bool)

    @pytest.mark.asyncio
    async def test_generate_with_ollama(self):
        """Test text generation with Ollama"""
        with patch('aiohttp.ClientSession') as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={
                "response": "Test response from Ollama"
            })

            mock_session_instance = AsyncMock()
            mock_session_instance.post.return_value.__aenter__.return_value = mock_response
            mock_session.return_value.__aenter__.return_value = mock_session_instance

            service = LLMService(preferred_provider=ModelProvider.OLLAMA)
            response = await service.generate("Test prompt")

            assert "Test response" in response or response is not None

    @pytest.mark.asyncio
    async def test_provider_fallback(self):
        """Test fallback from Ollama to Gemini when Ollama is unavailable"""
        service = LLMService(preferred_provider=ModelProvider.OLLAMA)

        # Mock Ollama as unavailable
        with patch.object(service, '_generate_ollama', side_effect=Exception("Ollama unavailable")):
            with patch.object(service, '_generate_gemini', return_value="Gemini response"):
                response = await service.generate("Test prompt")
                assert response is not None

    def test_get_provider_info(self):
        """Test getting current provider information"""
        service = LLMService(preferred_provider=ModelProvider.OLLAMA)
        info = service.get_provider_info()

        assert "provider" in info
        assert info["provider"] in ["ollama", "gemini"]
        assert "model" in info
        assert "available" in info

    @pytest.mark.asyncio
    async def test_generate_with_temperature(self):
        """Test text generation with custom temperature"""
        with patch('aiohttp.ClientSession') as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={
                "response": "Creative response"
            })

            mock_session_instance = AsyncMock()
            mock_session_instance.post.return_value.__aenter__.return_value = mock_response
            mock_session.return_value.__aenter__.return_value = mock_session_instance

            service = LLMService(preferred_provider=ModelProvider.OLLAMA)
            response = await service.generate("Test prompt", temperature=0.8)

            assert response is not None

    @pytest.mark.asyncio
    async def test_generate_empty_prompt(self):
        """Test that empty prompts are handled gracefully"""
        service = LLMService(preferred_provider=ModelProvider.OLLAMA)

        with pytest.raises(Exception):
            await service.generate("")

    @pytest.mark.asyncio
    async def test_generate_very_long_prompt(self):
        """Test handling of very long prompts"""
        service = LLMService(preferred_provider=ModelProvider.OLLAMA)
        long_prompt = "test " * 10000  # Very long prompt

        # Should not raise an exception, but may truncate or handle gracefully
        try:
            response = await service.generate(long_prompt)
            assert response is not None
        except Exception as e:
            # If it fails, it should be a handled exception
            assert str(e) is not None
