"""Tests for LLMService."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from eleutheria_graphrag.services.llm_service import (
    PROVIDER_CONFIGS,
    LLMService,
    ModelProvider,
)


class TestModelProvider:
    """Tests for ModelProvider enum."""

    def test_provider_values(self):
        """Test provider enum values."""
        assert ModelProvider.FIREWORKS.value == "fireworks"
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
            assert llm.preferred_provider == ModelProvider.FIREWORKS
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
        with patch.dict(
            "os.environ",
            {
                "MOONSHOT_API_KEY": "test-key",
                "GEMINI_API_KEY": "test-key-2",
            },
            clear=True,
        ):
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

    def test_get_provider_thinking_override(self):
        """Thinking mode should respect an explicit provider override."""
        env = {
            "MOONSHOT_API_KEY": "kimi-key",
            "OPENROUTER_API_KEY": "or-key",
            "LLM_THINKING_PROVIDER": "openrouter",
        }
        with patch.dict("os.environ", env, clear=True):
            llm = LLMService(preferred_provider=ModelProvider.KIMI)
            provider = llm._get_provider(thinking_mode=True)
            assert provider == ModelProvider.OPENROUTER

    def test_get_provider_skips_backoff_provider(self):
        """Preferred providers in cooldown should be skipped."""
        env = {
            "GEMINI_API_KEY": "gemini-key",
            "OPENROUTER_API_KEY": "or-key",
            "LLM_THINKING_PROVIDER": "openrouter",
        }
        with patch.dict("os.environ", env, clear=True):
            llm = LLMService(preferred_provider=ModelProvider.GEMINI)
            llm._provider_backoff_until[ModelProvider.OPENROUTER] = 9999999999.0
            provider = llm._get_provider(thinking_mode=True)
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

            result = await llm.generate("Test prompt", max_tokens=16)
            assert result == "Test response"
            # non-reasoning model: no reasoning_content side-channel
            assert llm.last_reasoning_content == ""

    @pytest.mark.asyncio
    async def test_generate_extracts_reasoning_content_separately(self):
        """A thinking model returns reasoning_content + content; the answer is
        content ONLY, reasoning is surfaced on the side-channel (not folded in)."""
        with patch.dict("os.environ", {"FIREWORKS_API_KEY": "test-key"}, clear=True):
            llm = LLMService(preferred_provider=ModelProvider.FIREWORKS)

            mock_response = MagicMock()
            mock_response.json.return_value = {
                "choices": [
                    {
                        "message": {
                            "content": "The clean finished answer.",
                            "reasoning_content": "Let me think. The user wants X.",
                        }
                    }
                ]
            }
            mock_response.raise_for_status = MagicMock()

            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            llm._client = mock_client

            result = await llm.generate(
                "Test prompt",
                max_tokens=16,
                model_override="accounts/fireworks/models/deepseek-v4-pro",
            )
            # answer is content ONLY — reasoning excluded
            assert result == "The clean finished answer."
            assert "Let me think" not in result
            # reasoning surfaced on the side-channel for the trace
            assert llm.last_reasoning_content == "Let me think. The user wants X."

    @pytest.mark.asyncio
    async def test_generate_resets_stale_reasoning_content(self):
        """A non-reasoning call after a reasoning one must not surface stale scratch."""
        with patch.dict("os.environ", {"FIREWORKS_API_KEY": "test-key"}, clear=True):
            llm = LLMService(preferred_provider=ModelProvider.FIREWORKS)
            llm.last_reasoning_content = "stale scratch from a prior thinking call"

            mock_response = MagicMock()
            mock_response.json.return_value = {
                "choices": [{"message": {"content": "Plain answer."}}]
            }
            mock_response.raise_for_status = MagicMock()
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            llm._client = mock_client

            result = await llm.generate("Test prompt", max_tokens=16)
            assert result == "Plain answer."
            assert llm.last_reasoning_content == ""

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

            await llm.generate(
                "User prompt", system_prompt="You are a helpful assistant."
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

            result = await llm.generate("Test prompt", max_tokens=16)
            assert result == "Gemini response"

    def test_retry_delay_seconds_reads_openrouter_retry_after_seconds(self):
        """Provider-specific retry hints should drive cooldowns."""
        request = httpx.Request("POST", "https://openrouter.ai/api/v1/chat/completions")
        response = httpx.Response(
            429,
            request=request,
            json={
                "error": {
                    "metadata": {
                        "retry_after_seconds": 42,
                    }
                }
            },
        )
        exc = httpx.HTTPStatusError("rate limited", request=request, response=response)

        assert LLMService._retry_delay_seconds(exc) == 42

    def test_should_not_retry_same_provider_on_rate_limit(self):
        """429s should fall through to the next provider instead of sleeping inline."""
        request = httpx.Request("POST", "https://openrouter.ai/api/v1/chat/completions")
        response = httpx.Response(
            429, request=request, json={"error": {"message": "rate limit"}}
        )
        exc = httpx.HTTPStatusError("rate limited", request=request, response=response)

        assert LLMService._should_retry_same_provider(exc, attempt=0) is False

    @pytest.mark.asyncio
    async def test_generate_gemini_passes_response_mime_type(self):
        """Gemini JSON-mode requests should set responseMimeType."""
        with patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"}, clear=True):
            llm = LLMService(preferred_provider=ModelProvider.GEMINI)

            mock_response = MagicMock()
            mock_response.json.return_value = {
                "candidates": [{"content": {"parts": [{"text": '{"ok":true}'}]}}]
            }
            mock_response.raise_for_status = MagicMock()

            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            llm._client = mock_client

            await llm.generate(
                "Return JSON",
                max_tokens=16,
                response_mime_type="application/json",
                response_json_schema={"type": "object"},
            )

            call_kwargs = mock_client.post.call_args.kwargs
            assert (
                call_kwargs["json"]["generationConfig"]["responseMimeType"]
                == "application/json"
            )
            assert call_kwargs["json"]["generationConfig"]["responseJsonSchema"] == {
                "type": "object"
            }

    def test_extract_gemini_text_prefers_visible_parts(self):
        """Gemini extraction should prefer visible text parts over thought parts."""
        data = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {"text": "internal", "thought": True},
                            {"text": "visible answer"},
                        ]
                    }
                }
            ]
        }
        assert LLMService._extract_gemini_text(data) == "visible answer"

    @pytest.mark.asyncio
    async def test_generate_gemini_retries_without_thinking_when_first_reply_is_empty(
        self,
    ):
        """Gemini should retry once with a larger output budget if the first reply has no visible parts."""
        with patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"}, clear=True):
            llm = LLMService(preferred_provider=ModelProvider.GEMINI)

            first_response = MagicMock()
            first_response.json.return_value = {
                "candidates": [{"content": {}, "finishReason": "MAX_TOKENS"}]
            }
            first_response.raise_for_status = MagicMock()

            second_response = MagicMock()
            second_response.json.return_value = {
                "candidates": [{"content": {"parts": [{"text": "Recovered response"}]}}]
            }
            second_response.raise_for_status = MagicMock()

            mock_client = AsyncMock()
            mock_client.post = AsyncMock(side_effect=[first_response, second_response])
            llm._client = mock_client

            result = await llm.generate("Test prompt", max_tokens=16)

            assert result == "Recovered response"
            assert mock_client.post.call_count == 2
            retry_body = mock_client.post.call_args_list[1].kwargs["json"]
            assert retry_body["generationConfig"]["maxOutputTokens"] == 128

    @pytest.mark.asyncio
    async def test_generate_gemini_uses_prompt_cache_when_requested(self):
        """Gemini generation should create and reuse cached prompt prefixes."""
        with patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"}, clear=True):
            llm = LLMService(preferred_provider=ModelProvider.GEMINI)
            long_prefix = "stable prefix " * 1600

            cache_response = MagicMock()
            cache_response.json.return_value = {"name": "cachedContents/test-cache"}
            cache_response.raise_for_status = MagicMock()

            generate_response = MagicMock()
            generate_response.json.return_value = {
                "candidates": [{"content": {"parts": [{"text": "Gemini response"}]}}]
            }
            generate_response.raise_for_status = MagicMock()

            mock_client = AsyncMock()
            mock_client.post = AsyncMock(
                side_effect=[cache_response, generate_response, generate_response]
            )
            llm._client = mock_client

            result = await llm.generate(
                "User prompt",
                system_prompt="Stable instructions",
                cache_key="render",
                cache_prefix=long_prefix,
            )
            assert result == "Gemini response"

            # Second call should reuse the cachedContent handle.
            await llm.generate(
                "User prompt 2",
                system_prompt="Stable instructions",
                cache_key="render",
                cache_prefix=long_prefix,
            )

            assert mock_client.post.call_count == 3
            cache_call = mock_client.post.call_args_list[0]
            assert "cachedContents" in cache_call.args[0]
            generate_call = mock_client.post.call_args_list[1]
            assert (
                generate_call.kwargs["json"]["cachedContent"]
                == "cachedContents/test-cache"
            )

    @pytest.mark.asyncio
    async def test_generate_gemini_skips_prompt_cache_when_prefix_too_short(self):
        """Gemini cache creation should be skipped for clearly undersized prefixes."""
        with patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"}, clear=True):
            llm = LLMService(preferred_provider=ModelProvider.GEMINI)

            generate_response = MagicMock()
            generate_response.json.return_value = {
                "candidates": [{"content": {"parts": [{"text": "Gemini response"}]}}]
            }
            generate_response.raise_for_status = MagicMock()

            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=generate_response)
            llm._client = mock_client

            result = await llm.generate(
                "User prompt",
                system_prompt="Stable instructions",
                cache_key="render",
                cache_prefix="short prefix",
            )

            assert result == "Gemini response"
            assert mock_client.post.call_count == 1
            call = mock_client.post.call_args
            assert "cachedContents" not in call.args[0]
            assert "cachedContent" not in call.kwargs["json"]

    @pytest.mark.asyncio
    async def test_generate_falls_back_to_next_provider_on_429(self):
        """Retryable provider failures should fall through to the next provider."""
        env = {
            "GEMINI_API_KEY": "gem-key",
            "MOONSHOT_API_KEY": "kimi-key",
        }
        with patch.dict("os.environ", env, clear=True):
            llm = LLMService(preferred_provider=ModelProvider.GEMINI)

            gemini_error = httpx.HTTPStatusError(
                "rate limited",
                request=httpx.Request("POST", "https://example.com"),
                response=httpx.Response(
                    429, request=httpx.Request("POST", "https://example.com")
                ),
            )
            kimi_response = MagicMock()
            kimi_response.json.return_value = {
                "choices": [{"message": {"content": "Fallback response"}}]
            }
            kimi_response.raise_for_status = MagicMock()

            mock_client = AsyncMock()
            mock_client.post = AsyncMock(side_effect=[gemini_error, kimi_response])
            llm._client = mock_client

            with patch("asyncio.sleep", new=AsyncMock()):
                result = await llm.generate("Test prompt")

            assert result == "Fallback response"
            assert llm.last_provider_used == ModelProvider.KIMI.value
            assert mock_client.post.call_count == 2

    @pytest.mark.asyncio
    async def test_generate_retries_same_provider_once_on_500(self):
        """Transient server failures should retry the same provider once before falling over."""
        with patch.dict("os.environ", {"GEMINI_API_KEY": "gem-key"}, clear=True):
            llm = LLMService(preferred_provider=ModelProvider.GEMINI)

            gemini_error = httpx.HTTPStatusError(
                "server error",
                request=httpx.Request("POST", "https://example.com"),
                response=httpx.Response(
                    500, request=httpx.Request("POST", "https://example.com")
                ),
            )
            success_response = MagicMock()
            success_response.json.return_value = {
                "candidates": [{"content": {"parts": [{"text": "Recovered response"}]}}]
            }
            success_response.raise_for_status = MagicMock()

            mock_client = AsyncMock()
            mock_client.post = AsyncMock(side_effect=[gemini_error, success_response])
            llm._client = mock_client

            with patch("asyncio.sleep", new=AsyncMock()) as sleep_mock:
                result = await llm.generate("Test prompt")

            assert result == "Recovered response"
            assert llm.last_provider_used == ModelProvider.GEMINI.value
            sleep_mock.assert_awaited()
            assert mock_client.post.call_count == 2

    @pytest.mark.asyncio
    async def test_generate_disables_invalid_provider_and_uses_next_one(self):
        """An unauthorized provider should be disabled and skipped for the rest of the session."""
        env = {
            "MOONSHOT_API_KEY": "kimi-key",
            "OPENROUTER_API_KEY": "or-key",
        }
        with patch.dict("os.environ", env, clear=True):
            llm = LLMService(preferred_provider=ModelProvider.KIMI)

            kimi_error = httpx.HTTPStatusError(
                "unauthorized",
                request=httpx.Request("POST", "https://example.com"),
                response=httpx.Response(
                    401, request=httpx.Request("POST", "https://example.com")
                ),
            )
            or_response = MagicMock()
            or_response.json.return_value = {
                "choices": [{"message": {"content": "OpenRouter response"}}]
            }
            or_response.raise_for_status = MagicMock()

            mock_client = AsyncMock()
            mock_client.post = AsyncMock(
                side_effect=[kimi_error, or_response, or_response]
            )
            llm._client = mock_client

            result = await llm.generate("Test prompt")
            assert result == "OpenRouter response"
            assert ModelProvider.KIMI in llm._disabled_providers

            # Second call should not attempt Kimi again.
            second = await llm.generate("Second prompt")
            assert second == "OpenRouter response"
            assert mock_client.post.call_count == 3

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
        assert config["base_url_env"] == "MOONSHOT_BASE_URL"
        assert config["model"] == "kimi-latest"
        assert config["thinking_model"] == "kimi-latest"

    def test_resolve_config_uses_environment_base_url_override(self):
        """Environment overrides should win over the provider default base URL."""
        with patch.dict(
            "os.environ",
            {
                "MOONSHOT_API_KEY": "test-key",
                "MOONSHOT_BASE_URL": "https://api.moonshot.ai/v1/",
            },
            clear=True,
        ):
            llm = LLMService(preferred_provider=ModelProvider.KIMI)
            config = llm._resolve_config(ModelProvider.KIMI)
            assert config["base_url"] == "https://api.moonshot.ai/v1"

    def test_model_for_request_uses_thinking_model_for_kimi(self):
        """Kimi should switch models when thinking mode is requested."""
        config = PROVIDER_CONFIGS[ModelProvider.KIMI]
        assert (
            LLMService._model_for_request(
                ModelProvider.KIMI,
                config,
                thinking_mode=True,
            )
            == "kimi-latest"
        )
        assert (
            LLMService._model_for_request(
                ModelProvider.KIMI,
                config,
                thinking_mode=False,
            )
            == "kimi-latest"
        )

    def test_provider_config_openrouter(self):
        """Test OpenRouter provider configuration."""
        config = PROVIDER_CONFIGS[ModelProvider.OPENROUTER]
        assert "openrouter" in config["base_url"]
        assert config["env_key"] == "OPENROUTER_API_KEY"
        assert config["thinking_model"] == "qwen/qwen3.6-plus-preview:free"

    def test_resolve_config_uses_openrouter_overrides(self):
        """OpenRouter env overrides should be reflected in the resolved config."""
        with patch.dict(
            "os.environ",
            {
                "OPENROUTER_API_KEY": "test-key",
                "OPENROUTER_THINKING_MODEL": "openai/gpt-oss-120b:nitro",
                "OPENROUTER_PROVIDER_ONLY": "cerebras",
                "OPENROUTER_REASONING_EFFORT": "low",
                "OPENROUTER_HTTP_REFERER": "https://free-will.app",
                "OPENROUTER_APP_NAME": "EleutherIA",
            },
            clear=True,
        ):
            llm = LLMService(preferred_provider=ModelProvider.OPENROUTER)
            config = llm._resolve_config(ModelProvider.OPENROUTER)
            assert config["thinking_model"] == "openai/gpt-oss-120b:nitro"
            assert config["provider_only"] == ["cerebras"]
            assert config["reasoning_effort"] == "low"
            assert config["http_referer"] == "https://free-will.app"
            assert config["app_name"] == "EleutherIA"

    def test_model_for_request_uses_thinking_model_for_openrouter(self):
        """OpenRouter should switch to its thinking model when requested."""
        config = PROVIDER_CONFIGS[ModelProvider.OPENROUTER]
        assert (
            LLMService._model_for_request(
                ModelProvider.OPENROUTER,
                config,
                thinking_mode=True,
            )
            == "qwen/qwen3.6-plus-preview:free"
        )
        assert (
            LLMService._model_for_request(
                ModelProvider.OPENROUTER,
                config,
                thinking_mode=False,
            )
            == "qwen/qwen3.6-plus-preview:free"
        )

    @pytest.mark.asyncio
    async def test_generate_openrouter_includes_provider_routing(self):
        """OpenRouter requests should include provider routing and reasoning controls."""
        env = {
            "OPENROUTER_API_KEY": "or-key",
            "OPENROUTER_THINKING_MODEL": "openai/gpt-oss-120b:nitro",
            "OPENROUTER_PROVIDER_ONLY": "cerebras",
            "OPENROUTER_REASONING_EFFORT": "low",
            "OPENROUTER_HTTP_REFERER": "https://free-will.app",
            "OPENROUTER_APP_NAME": "EleutherIA",
        }
        with patch.dict("os.environ", env, clear=True):
            llm = LLMService(preferred_provider=ModelProvider.OPENROUTER)

            mock_response = MagicMock()
            mock_response.json.return_value = {
                "choices": [{"message": {"content": "OpenRouter response"}}]
            }
            mock_response.raise_for_status = MagicMock()

            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            llm._client = mock_client

            result = await llm.generate("Test prompt", thinking_mode=True)

            assert result == "OpenRouter response"
            call = mock_client.post.call_args
            assert call.kwargs["json"]["model"] == "openai/gpt-oss-120b:nitro"
            assert call.kwargs["json"]["provider"] == {"only": ["cerebras"]}
            assert call.kwargs["json"]["reasoning"] == {"effort": "low"}
            assert call.kwargs["headers"]["HTTP-Referer"] == "https://free-will.app"
            assert call.kwargs["headers"]["X-Title"] == "EleutherIA"

    def test_provider_config_gemini(self):
        """Test Gemini provider configuration."""
        config = PROVIDER_CONFIGS[ModelProvider.GEMINI]
        assert "generativelanguage.googleapis.com" in config["base_url"]
        assert config["env_key"] == "GEMINI_API_KEY"


class TestFireworksProvider:
    """Tests for the Fireworks (Kimi K2.6) provider."""

    def test_provider_config_fireworks(self):
        """Fireworks provider config exposes Kimi K2.6 + OpenAI-compatible base URL."""
        config = PROVIDER_CONFIGS[ModelProvider.FIREWORKS]
        assert config["base_url"] == "https://api.fireworks.ai/inference/v1"
        assert config["model"] == "accounts/fireworks/models/kimi-k2p6"
        assert config["thinking_model"] == "accounts/fireworks/models/kimi-k2p6"
        assert config["env_key"] == "FIREWORKS_API_KEY"
        assert config["base_url_env"] == "FIREWORKS_BASE_URL"
        assert config["model_env"] == "FIREWORKS_MODEL"

    def test_detect_available_providers_fireworks(self):
        """Fireworks should be detected when FIREWORKS_API_KEY is set."""
        with patch.dict("os.environ", {"FIREWORKS_API_KEY": "fw_test"}, clear=True):
            llm = LLMService()
            assert ModelProvider.FIREWORKS in llm.available_providers

    def test_init_with_fireworks_key_kwarg(self):
        """Explicit fireworks_api_key kwarg should enable the provider without env."""
        with patch.dict("os.environ", {}, clear=True):
            llm = LLMService(fireworks_api_key="fw_explicit")
            assert ModelProvider.FIREWORKS in llm.available_providers
            assert llm._api_key_for(ModelProvider.FIREWORKS) == "fw_explicit"

    def test_get_provider_prefers_fireworks_by_default(self):
        """When all keys are present, the default preferred provider is Fireworks."""
        env = {
            "FIREWORKS_API_KEY": "fw_test",
            "GEMINI_API_KEY": "gem_test",
            "MOONSHOT_API_KEY": "kimi_test",
            "OPENROUTER_API_KEY": "or_test",
        }
        with patch.dict("os.environ", env, clear=True):
            llm = LLMService()
            assert llm._get_provider() == ModelProvider.FIREWORKS

    def test_resolve_config_uses_fireworks_overrides(self):
        """FIREWORKS_BASE_URL and FIREWORKS_MODEL env vars should override defaults."""
        with patch.dict(
            "os.environ",
            {
                "FIREWORKS_API_KEY": "fw_test",
                "FIREWORKS_BASE_URL": "https://fireworks.example/inference/v1/",
                "FIREWORKS_MODEL": "accounts/fireworks/models/test-model",
            },
            clear=True,
        ):
            llm = LLMService(preferred_provider=ModelProvider.FIREWORKS)
            config = llm._resolve_config(ModelProvider.FIREWORKS)
            assert config["base_url"] == "https://fireworks.example/inference/v1"
            assert config["model"] == "accounts/fireworks/models/test-model"

    def test_model_override_routes_fireworks_models_to_fireworks(self):
        """Model overrides starting with accounts/fireworks/ should route to Fireworks."""
        llm = LLMService()
        provider, model = llm._resolve_model_override(
            "accounts/fireworks/models/kimi-k2p6"
        )
        assert provider == ModelProvider.FIREWORKS
        assert model == "accounts/fireworks/models/kimi-k2p6"

    @pytest.mark.asyncio
    async def test_generate_fireworks_chat_completions(self):
        """Fireworks generate() should POST to /chat/completions with Kimi K2.6."""
        with patch.dict("os.environ", {"FIREWORKS_API_KEY": "fw_test"}, clear=True):
            llm = LLMService(preferred_provider=ModelProvider.FIREWORKS)

            mock_response = MagicMock()
            mock_response.json.return_value = {
                "choices": [{"message": {"content": "Kimi response"}}]
            }
            mock_response.raise_for_status = MagicMock()

            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            llm._client = mock_client

            result = await llm.generate("Test prompt", max_tokens=16)

            assert result == "Kimi response"
            assert llm.last_provider_used == ModelProvider.FIREWORKS.value
            assert llm.last_model_used == "accounts/fireworks/models/kimi-k2p6"
            call = mock_client.post.call_args
            assert (
                call.args[0] == "https://api.fireworks.ai/inference/v1/chat/completions"
            )
            assert call.kwargs["headers"]["Authorization"] == "Bearer fw_test"
            assert call.kwargs["json"]["model"] == "accounts/fireworks/models/kimi-k2p6"

    @pytest.mark.asyncio
    async def test_stream_fireworks_yields_sse_chunks(self):
        """Fireworks stream() should parse OpenAI-style SSE chunks."""
        with patch.dict("os.environ", {"FIREWORKS_API_KEY": "fw_test"}, clear=True):
            llm = LLMService(preferred_provider=ModelProvider.FIREWORKS)

            sse_lines = [
                'data: {"choices":[{"delta":{"content":"Hel"}}]}',
                'data: {"choices":[{"delta":{"content":"lo"}}]}',
                "data: [DONE]",
            ]

            class _FakeStream:
                async def __aenter__(self_inner):
                    return self_inner

                async def __aexit__(self_inner, exc_type, exc, tb):
                    return None

                def raise_for_status(self_inner):
                    return None

                async def aiter_lines(self_inner):
                    for line in sse_lines:
                        yield line

            mock_client = MagicMock()
            mock_client.stream = MagicMock(return_value=_FakeStream())
            llm._client = mock_client

            chunks: list[str] = []
            async for chunk in llm.stream("Hi", max_tokens=16):
                chunks.append(chunk)

            assert chunks == ["Hel", "lo"]
            call = mock_client.stream.call_args
            assert call.args[0] == "POST"
            assert (
                call.args[1] == "https://api.fireworks.ai/inference/v1/chat/completions"
            )
            assert call.kwargs["json"]["stream"] is True

    @pytest.mark.asyncio
    async def test_generate_falls_back_when_fireworks_fails(self):
        """A failing Fireworks call should fall through to the next provider."""
        env = {
            "FIREWORKS_API_KEY": "fw_test",
            "GEMINI_API_KEY": "gem_test",
        }
        with patch.dict("os.environ", env, clear=True):
            llm = LLMService(preferred_provider=ModelProvider.FIREWORKS)

            fireworks_error = httpx.HTTPStatusError(
                "rate limited",
                request=httpx.Request("POST", "https://api.fireworks.ai"),
                response=httpx.Response(
                    429,
                    request=httpx.Request("POST", "https://api.fireworks.ai"),
                ),
            )
            gemini_response = MagicMock()
            gemini_response.json.return_value = {
                "candidates": [{"content": {"parts": [{"text": "Gemini fallback"}]}}]
            }
            gemini_response.raise_for_status = MagicMock()

            mock_client = AsyncMock()
            mock_client.post = AsyncMock(side_effect=[fireworks_error, gemini_response])
            llm._client = mock_client

            with patch("asyncio.sleep", new=AsyncMock()):
                result = await llm.generate("Test prompt")

            assert result == "Gemini fallback"
            assert llm.last_provider_used == ModelProvider.GEMINI.value
            assert mock_client.post.call_count == 2


class TestFireworksPromptCache:
    """Fireworks prompt-caching directive (Wave 7 perf opt)."""

    def test_cache_id_composed_from_agent_id(self):
        with patch.dict(
            "os.environ",
            {"ELEUTHERIA_PROMPT_CACHE_VERSION": "v1"},
            clear=False,
        ):
            assert (
                LLMService._fireworks_cache_id("scholar-orchestrator")
                == "eleutheria-scholar-orchestrator-v1"
            )

    def test_cache_id_none_when_agent_id_missing(self):
        assert LLMService._fireworks_cache_id(None) is None
        assert LLMService._fireworks_cache_id("") is None

    def test_cache_id_respects_version_env(self):
        with patch.dict(
            "os.environ",
            {"ELEUTHERIA_PROMPT_CACHE_VERSION": "v7-2026-05-15"},
            clear=False,
        ):
            assert (
                LLMService._fireworks_cache_id("concept-mapper")
                == "eleutheria-concept-mapper-v7-2026-05-15"
            )

    def test_payload_includes_prompt_cache_id_for_fireworks(self):
        config = {"model": "accounts/fireworks/models/kimi-k2p6"}
        payload = LLMService._openai_compatible_payload(
            ModelProvider.FIREWORKS,
            prompt="user prompt",
            system_prompt="big system prompt",
            temperature=0.2,
            max_tokens=512,
            config=config,
            prompt_cache_id="eleutheria-scholar-orchestrator-v1",
        )
        assert payload["prompt_cache_id"] == "eleutheria-scholar-orchestrator-v1"
        # Sanity: system + user message preserved.
        assert payload["messages"][0]["role"] == "system"
        assert payload["messages"][1]["role"] == "user"

    def test_payload_omits_prompt_cache_id_for_non_fireworks(self):
        config = {"model": "kimi-latest"}
        payload = LLMService._openai_compatible_payload(
            ModelProvider.KIMI,
            prompt="x",
            system_prompt=None,
            temperature=0.7,
            max_tokens=64,
            config=config,
            prompt_cache_id="eleutheria-scholar-orchestrator-v1",
        )
        assert "prompt_cache_id" not in payload

    def test_payload_attaches_strict_json_schema_for_fireworks(self):
        schema = {
            "type": "object",
            "required": ["claims"],
            "properties": {"claims": {"type": "array"}},
        }
        config = {"model": "accounts/fireworks/models/kimi-k2p6"}
        payload = LLMService._openai_compatible_payload(
            ModelProvider.FIREWORKS,
            prompt="user prompt",
            system_prompt=None,
            temperature=0.0,
            max_tokens=512,
            config=config,
            response_json_schema=schema,
            schema_name="ClaimLedger",
        )
        assert payload["response_format"] == {
            "type": "json_schema",
            "json_schema": {
                "name": "ClaimLedger",
                "schema": schema,
                "strict": True,
            },
        }

    def test_payload_attaches_strict_json_schema_for_kimi_native(self):
        schema = {"type": "object", "properties": {}}
        payload = LLMService._openai_compatible_payload(
            ModelProvider.KIMI,
            prompt="x",
            system_prompt=None,
            temperature=0.0,
            max_tokens=64,
            config={"model": "kimi-latest"},
            response_json_schema=schema,
        )
        assert payload["response_format"]["type"] == "json_schema"

    def test_payload_falls_back_to_json_object_for_openrouter(self):
        payload = LLMService._openai_compatible_payload(
            ModelProvider.OPENROUTER,
            prompt="x",
            system_prompt=None,
            temperature=0.0,
            max_tokens=64,
            config={"model": "anthropic/claude-sonnet-4.6"},
            response_json_schema={"type": "object"},
        )
        assert payload["response_format"] == {"type": "json_object"}

    def test_payload_response_format_absent_by_default(self):
        payload = LLMService._openai_compatible_payload(
            ModelProvider.FIREWORKS,
            prompt="x",
            system_prompt=None,
            temperature=0.0,
            max_tokens=64,
            config={"model": "accounts/fireworks/models/kimi-k2p6"},
        )
        assert "response_format" not in payload

    def test_payload_omits_prompt_cache_id_when_unset(self):
        config = {"model": "accounts/fireworks/models/kimi-k2p6"}
        payload = LLMService._openai_compatible_payload(
            ModelProvider.FIREWORKS,
            prompt="x",
            system_prompt=None,
            temperature=0.2,
            max_tokens=64,
            config=config,
        )
        assert "prompt_cache_id" not in payload

    @pytest.mark.asyncio
    async def test_generate_propagates_agent_id_to_fireworks_payload(self):
        """When generate() is given agent_id, the Fireworks payload carries cache id."""
        with patch.dict("os.environ", {"FIREWORKS_API_KEY": "fw_test"}, clear=True):
            llm = LLMService(preferred_provider=ModelProvider.FIREWORKS)

            mock_response = MagicMock()
            mock_response.json.return_value = {
                "choices": [{"message": {"content": "ok"}}]
            }
            mock_response.raise_for_status = MagicMock()
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            llm._client = mock_client

            await llm.generate(
                "user prompt",
                system_prompt="system prompt",
                agent_id="scholar-orchestrator",
                max_tokens=16,
            )

            sent = mock_client.post.call_args.kwargs["json"]
            assert sent["prompt_cache_id"].startswith(
                "eleutheria-scholar-orchestrator-"
            )


class TestKimiTemperatureClamp:
    """M6: Moonshot/KIMI 400s on any temperature != 1.0 — the mandatory clamp."""

    def _payload(self, provider: ModelProvider, temperature: float) -> dict:
        return LLMService._openai_compatible_payload(
            provider,
            "user prompt",
            "system prompt",
            temperature,
            128,
            dict(PROVIDER_CONFIGS[provider]),
        )

    def test_kimi_temperature_clamped_to_one(self) -> None:
        payload = self._payload(ModelProvider.KIMI, 0.3)
        assert payload["temperature"] == 1.0

    def test_fireworks_temperature_not_clamped(self) -> None:
        payload = self._payload(ModelProvider.FIREWORKS, 0.3)
        assert payload["temperature"] == 0.3
