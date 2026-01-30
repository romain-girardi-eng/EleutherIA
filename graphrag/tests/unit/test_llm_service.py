"""Tests for LLMService."""

from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from eleutheria_graphrag.services.llm_service import (
    LLMService,
    ModelProvider,
    PROVIDER_CONFIGS,
)


class TestModelProvider:
    """Tests for ModelProvider enum."""

    def test_provider_values(self):
        """Test provider enum values."""
        assert ModelProvider.KIMI.value == "kimi"
        assert ModelProvider.OPENROUTER.value == "openrouter"
        assert ModelProvider.GEMINI.value == "gemini"

    def test_all_providers_have_config(self):
        """Test all providers have configuration."""
        for provider in ModelProvider:
            assert provider in PROVIDER_CONFIGS
            config = PROVIDER_CONFIGS[provider]
            assert "base_url" in config
            assert "model" in config
            assert "env_key" in config


class TestLLMService:
    """Tests for LLMService class."""

    def test_init_default(self):
        """Test default initialization."""
        with patch.dict("os.environ", {}, clear=True):
            llm = LLMService()
            assert llm.preferred_provider == ModelProvider.GEMINI
            assert llm.timeout == 120.0
            assert llm._client is None

    def test_init_custom_provider(self):
        """Test initialization with custom provider."""
        llm = LLMService(preferred_provider=ModelProvider.GEMINI, timeout=60.0)
        assert llm.preferred_provider == ModelProvider.GEMINI
        assert llm.timeout == 60.0

    def test_detect_available_providers_none(self):
        """Test detection when no API keys set."""
        with patch.dict("os.environ", {}, clear=True):
            llm = LLMService()
            assert len(llm.available_providers) == 0

    def test_detect_available_providers_kimi(self):
        """Test detection with Kimi API key."""
        with patch.dict("os.environ", {"MOONSHOT_API_KEY": "test-key"}, clear=True):
            llm = LLMService()
            assert ModelProvider.KIMI in llm.available_providers

    def test_detect_available_providers_multiple(self):
        """Test detection with multiple API keys."""
        with patch.dict("os.environ", {
            "MOONSHOT_API_KEY": "test-key",
            "GEMINI_API_KEY": "test-key-2",
        }, clear=True):
            llm = LLMService()
            assert ModelProvider.KIMI in llm.available_providers
            assert ModelProvider.GEMINI in llm.available_providers

    def test_get_provider_preferred(self):
        """Test getting preferred provider when available."""
        with patch.dict("os.environ", {"MOONSHOT_API_KEY": "test-key"}, clear=True):
            llm = LLMService(preferred_provider=ModelProvider.KIMI)
            provider = llm._get_provider()
            assert provider == ModelProvider.KIMI

    def test_get_provider_fallback(self):
        """Test fallback when preferred not available."""
        with patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"}, clear=True):
            llm = LLMService(preferred_provider=ModelProvider.KIMI)
            provider = llm._get_provider()
            assert provider == ModelProvider.GEMINI

    def test_get_provider_none_available(self):
        """Test when no provider available."""
        with patch.dict("os.environ", {}, clear=True):
            llm = LLMService()
            provider = llm._get_provider()
            assert provider is None

    @pytest.mark.asyncio
    async def test_close(self):
        """Test closing HTTP client."""
        llm = LLMService()
        mock_client = AsyncMock()
        llm._client = mock_client

        await llm.close()
        mock_client.aclose.assert_called_once()
        assert llm._client is None

    @pytest.mark.asyncio
    async def test_generate_no_provider(self):
        """Test generate raises when no provider available."""
        with patch.dict("os.environ", {}, clear=True):
            llm = LLMService()

            with pytest.raises(RuntimeError, match="No LLM provider available"):
                await llm.generate("Test prompt")

    @pytest.mark.asyncio
    async def test_generate_openai_compatible(self):
        """Test generate with OpenAI-compatible API."""
        with patch.dict("os.environ", {"MOONSHOT_API_KEY": "test-key"}, clear=True):
            llm = LLMService(preferred_provider=ModelProvider.KIMI)

            mock_response = MagicMock()
            mock_response.json.return_value = {
                "choices": [{"message": {"content": "Test response"}}]
            }
            mock_response.raise_for_status = MagicMock()

            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            llm._client = mock_client

            result = await llm.generate("Test prompt")
            assert result == "Test response"

    @pytest.mark.asyncio
    async def test_generate_with_system_prompt(self):
        """Test generate with system prompt."""
        with patch.dict("os.environ", {"MOONSHOT_API_KEY": "test-key"}, clear=True):
            llm = LLMService(preferred_provider=ModelProvider.KIMI)

            mock_response = MagicMock()
            mock_response.json.return_value = {
                "choices": [{"message": {"content": "Response"}}]
            }
            mock_response.raise_for_status = MagicMock()

            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            llm._client = mock_client

            result = await llm.generate(
                "User prompt",
                system_prompt="You are a helpful assistant."
            )

            # Verify system prompt was included in messages
            call_kwargs = mock_client.post.call_args.kwargs
            messages = call_kwargs["json"]["messages"]
            assert len(messages) == 2
            assert messages[0]["role"] == "system"
            assert messages[1]["role"] == "user"

    @pytest.mark.asyncio
    async def test_generate_gemini(self):
        """Test generate with Gemini API."""
        with patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"}, clear=True):
            llm = LLMService(preferred_provider=ModelProvider.GEMINI)

            mock_response = MagicMock()
            mock_response.json.return_value = {
                "candidates": [{"content": {"parts": [{"text": "Gemini response"}]}}]
            }
            mock_response.raise_for_status = MagicMock()

            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            llm._client = mock_client

            result = await llm.generate("Test prompt")
            assert result == "Gemini response"

    @pytest.mark.asyncio
    async def test_stream_no_provider(self):
        """Test stream raises when no provider available."""
        with patch.dict("os.environ", {}, clear=True):
            llm = LLMService()

            with pytest.raises(RuntimeError, match="No LLM provider available"):
                async for _ in llm.stream("Test prompt"):
                    pass


class TestLLMServiceConfiguration:
    """Tests for LLM service configuration."""

    def test_provider_config_kimi(self):
        """Test Kimi provider configuration."""
        config = PROVIDER_CONFIGS[ModelProvider.KIMI]
        assert "moonshot" in config["base_url"]
        assert config["env_key"] == "MOONSHOT_API_KEY"

    def test_provider_config_openrouter(self):
        """Test OpenRouter provider configuration."""
        config = PROVIDER_CONFIGS[ModelProvider.OPENROUTER]
        assert "openrouter" in config["base_url"]
        assert config["env_key"] == "OPENROUTER_API_KEY"

    def test_provider_config_gemini(self):
        """Test Gemini provider configuration."""
        config = PROVIDER_CONFIGS[ModelProvider.GEMINI]
        assert "generativelanguage.googleapis.com" in config["base_url"]
        assert config["env_key"] == "GEMINI_API_KEY"
