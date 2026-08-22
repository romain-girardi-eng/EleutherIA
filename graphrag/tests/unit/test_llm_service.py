"""Tests for LLMService."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from eleutheria_graphrag.services.llm_service import (
    PROVIDER_CONFIGS,
    LLMService,
    ModelProvider,
    _redact_secrets,
    strict_json_schema,
)


class TestModelProvider:
    """Tests for ModelProvider enum."""

    def test_provider_values(self):
        """Test provider enum values."""
        assert ModelProvider.CODEX.value == "codex"
        assert ModelProvider.CLAUDE.value == "claude"
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
            assert llm.preferred_provider == ModelProvider.CODEX
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

    def test_detect_available_providers_codex(self):
        """Test detection with the Codex proxy key."""
        with patch.dict("os.environ", {"CODEX_PROXY_API_KEY": "test-key"}, clear=True):
            llm = LLMService()
            assert ModelProvider.CODEX in llm.available_providers

    def test_detect_available_providers_multiple(self):
        """Test detection with multiple API keys."""
        with patch.dict(
            "os.environ",
            {
                "CODEX_PROXY_API_KEY": "test-key",
                "GEMINI_API_KEY": "test-key-2",
            },
            clear=True,
        ):
            llm = LLMService()
            assert ModelProvider.CODEX in llm.available_providers
            assert ModelProvider.GEMINI in llm.available_providers

    def test_get_provider_preferred(self):
        """Test getting preferred provider when available."""
        with patch.dict("os.environ", {"CODEX_PROXY_API_KEY": "test-key"}, clear=True):
            llm = LLMService(preferred_provider=ModelProvider.CODEX)
            provider = llm._get_provider()
            assert provider == ModelProvider.CODEX

    def test_get_provider_fallback(self):
        """Test fallback when preferred not available."""
        with patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"}, clear=True):
            llm = LLMService(preferred_provider=ModelProvider.CODEX)
            provider = llm._get_provider()
            assert provider == ModelProvider.GEMINI

    def test_get_provider_thinking_override(self):
        """Thinking mode should respect an explicit provider override."""
        env = {
            "CODEX_PROXY_API_KEY": "codex-key",
            "CLAUDE_PROXY_API_KEY": "claude-key",
            "LLM_THINKING_PROVIDER": "claude",
        }
        with patch.dict("os.environ", env, clear=True):
            llm = LLMService(preferred_provider=ModelProvider.CODEX)
            provider = llm._get_provider(thinking_mode=True)
            assert provider == ModelProvider.CLAUDE

    def test_get_provider_skips_backoff_provider(self):
        """Preferred providers in cooldown should be skipped."""
        env = {
            "GEMINI_API_KEY": "gemini-key",
            "CLAUDE_PROXY_API_KEY": "claude-key",
            "LLM_THINKING_PROVIDER": "claude",
        }
        with patch.dict("os.environ", env, clear=True):
            llm = LLMService(preferred_provider=ModelProvider.GEMINI)
            llm._provider_backoff_until[ModelProvider.CLAUDE] = 9999999999.0
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
        with patch.dict("os.environ", {"CODEX_PROXY_API_KEY": "test-key"}, clear=True):
            llm = LLMService(preferred_provider=ModelProvider.CODEX)

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
        with patch.dict("os.environ", {"CODEX_PROXY_API_KEY": "test-key"}, clear=True):
            llm = LLMService(preferred_provider=ModelProvider.CODEX)

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
                model_override="gpt-5.6-sol",
            )
            # answer is content ONLY — reasoning excluded
            assert result == "The clean finished answer."
            assert "Let me think" not in result
            # reasoning surfaced on the side-channel for the trace
            assert llm.last_reasoning_content == "Let me think. The user wants X."

    @pytest.mark.asyncio
    async def test_generate_resets_stale_reasoning_content(self):
        """A non-reasoning call after a reasoning one must not surface stale scratch."""
        with patch.dict("os.environ", {"CODEX_PROXY_API_KEY": "test-key"}, clear=True):
            llm = LLMService(preferred_provider=ModelProvider.CODEX)
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
        with patch.dict("os.environ", {"CODEX_PROXY_API_KEY": "test-key"}, clear=True):
            llm = LLMService(preferred_provider=ModelProvider.CODEX)

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
            "CODEX_PROXY_API_KEY": "codex-key",
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
            codex_response = MagicMock()
            codex_response.json.return_value = {
                "choices": [{"message": {"content": "Fallback response"}}]
            }
            codex_response.raise_for_status = MagicMock()

            mock_client = AsyncMock()
            mock_client.post = AsyncMock(side_effect=[gemini_error, codex_response])
            llm._client = mock_client

            with patch("asyncio.sleep", new=AsyncMock()):
                result = await llm.generate("Test prompt")

            assert result == "Fallback response"
            assert llm.last_provider_used == ModelProvider.CODEX.value
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
            "CODEX_PROXY_API_KEY": "codex-key",
            "CLAUDE_PROXY_API_KEY": "claude-key",
        }
        with patch.dict("os.environ", env, clear=True):
            llm = LLMService(preferred_provider=ModelProvider.CODEX)

            codex_error = httpx.HTTPStatusError(
                "unauthorized",
                request=httpx.Request("POST", "https://example.com"),
                response=httpx.Response(
                    401, request=httpx.Request("POST", "https://example.com")
                ),
            )
            claude_response = MagicMock()
            claude_response.json.return_value = {
                "choices": [{"message": {"content": "Claude proxy response"}}]
            }
            claude_response.raise_for_status = MagicMock()

            mock_client = AsyncMock()
            mock_client.post = AsyncMock(
                side_effect=[codex_error, claude_response, claude_response]
            )
            llm._client = mock_client

            result = await llm.generate("Test prompt")
            assert result == "Claude proxy response"
            assert ModelProvider.CODEX in llm._disabled_providers

            # Second call should not attempt the Codex proxy again.
            second = await llm.generate("Second prompt")
            assert second == "Claude proxy response"
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
    """Provider configuration and env-override resolution."""

    def test_provider_config_codex(self):
        config = PROVIDER_CONFIGS[ModelProvider.CODEX]
        assert config["base_url"] == "http://cli-proxy-api:8317/v1"
        assert config["model"] == "gpt-5.6-sol"
        assert config["light_model"] == "gpt-5.6-terra"
        assert config["env_key"] == "CODEX_PROXY_API_KEY"
        assert config["reasoning_effort"] == "high"

    def test_provider_config_claude(self):
        config = PROVIDER_CONFIGS[ModelProvider.CLAUDE]
        assert config["base_url"] == "http://pragma-claude-proxy:8318/v1"
        assert config["model"] == "claude-opus-5"
        assert config["light_model"] == "claude-sonnet-5"
        assert config["env_key"] == "CLAUDE_PROXY_API_KEY"

    def test_provider_config_gemini(self):
        config = PROVIDER_CONFIGS[ModelProvider.GEMINI]
        assert config["base_url"].startswith(
            "https://generativelanguage.googleapis.com"
        )
        assert config["model"] == "gemini-3.1-pro-preview"
        assert config["env_key"] == "GEMINI_API_KEY"

    def test_removed_providers_are_gone(self):
        """Fireworks / Moonshot / OpenRouter must not come back by accident."""
        assert {p.value for p in ModelProvider} == {"codex", "claude", "gemini"}

    def test_resolve_config_uses_environment_base_url_override(self):
        env = {"CODEX_PROXY_BASE_URL": "https://proxy.example.com/v1/"}
        with patch.dict("os.environ", env, clear=True):
            config = LLMService._resolve_config(ModelProvider.CODEX)
        assert config["base_url"] == "https://proxy.example.com/v1"

    def test_resolve_config_uses_model_overrides(self):
        env = {
            "CODEX_MODEL": "gpt-6-preview",
            "CODEX_LIGHT_MODEL": "gpt-6-mini",
            "CODEX_REASONING_EFFORT": "medium",
        }
        with patch.dict("os.environ", env, clear=True):
            config = LLMService._resolve_config(ModelProvider.CODEX)
        assert config["model"] == "gpt-6-preview"
        assert config["light_model"] == "gpt-6-mini"
        assert config["reasoning_effort"] == "medium"

    def test_resolve_config_uses_claude_overrides(self):
        env = {
            "CLAUDE_PROXY_BASE_URL": "http://claude.internal:9000/v1",
            "CLAUDE_PROXY_MODEL": "claude-opus-5-1",
            "CLAUDE_PROXY_LIGHT_MODEL": "claude-haiku-5",
        }
        with patch.dict("os.environ", env, clear=True):
            config = LLMService._resolve_config(ModelProvider.CLAUDE)
        assert config["base_url"] == "http://claude.internal:9000/v1"
        assert config["model"] == "claude-opus-5-1"
        assert config["light_model"] == "claude-haiku-5"


class TestModelTiers:
    """The synthesis / utility tier concept."""

    def test_synthesis_tier_uses_the_full_model(self):
        config = LLMService._resolve_config(ModelProvider.CODEX)
        assert LLMService._model_for_request(config, tier="synthesis") == "gpt-5.6-sol"

    def test_utility_tier_uses_the_light_model(self):
        config = LLMService._resolve_config(ModelProvider.CODEX)
        assert LLMService._model_for_request(config, tier="utility") == "gpt-5.6-terra"

    def test_utility_tier_falls_back_to_full_model_without_light_model(self):
        """Gemini has no light model unless GEMINI_LIGHT_MODEL is set."""
        with patch.dict("os.environ", {}, clear=True):
            config = LLMService._resolve_config(ModelProvider.GEMINI)
        assert (
            LLMService._model_for_request(config, tier="utility")
            == "gemini-3.1-pro-preview"
        )

    def test_gemini_light_model_env_activates_the_utility_tier(self):
        with patch.dict(
            "os.environ", {"GEMINI_LIGHT_MODEL": "gemini-3-flash"}, clear=True
        ):
            config = LLMService._resolve_config(ModelProvider.GEMINI)
        assert LLMService._model_for_request(config, tier="utility") == "gemini-3-flash"

    def test_synthesis_tier_reasoning_effort_defaults_high(self):
        config = LLMService._resolve_config(ModelProvider.CODEX)
        effort = LLMService._reasoning_effort_for_request(
            ModelProvider.CODEX, config, tier="synthesis", override=None
        )
        assert effort == "high"

    def test_utility_tier_reasoning_effort_defaults_low(self):
        config = LLMService._resolve_config(ModelProvider.CODEX)
        effort = LLMService._reasoning_effort_for_request(
            ModelProvider.CODEX, config, tier="utility", override=None
        )
        assert effort == "low"

    def test_explicit_reasoning_effort_wins_over_tier(self):
        config = LLMService._resolve_config(ModelProvider.CODEX)
        effort = LLMService._reasoning_effort_for_request(
            ModelProvider.CODEX, config, tier="utility", override="high"
        )
        assert effort == "high"

    def test_claude_gets_no_reasoning_effort(self):
        """Only the Codex proxy is verified to honour reasoning_effort."""
        config = LLMService._resolve_config(ModelProvider.CLAUDE)
        effort = LLMService._reasoning_effort_for_request(
            ModelProvider.CLAUDE, config, tier="synthesis", override=None
        )
        assert effort is None

    @pytest.mark.asyncio
    async def test_generate_utility_tier_sends_light_model_and_low_effort(self):
        with patch.dict("os.environ", {"CODEX_PROXY_API_KEY": "test-key"}, clear=True):
            llm = LLMService(preferred_provider=ModelProvider.CODEX)
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "choices": [{"message": {"content": "cheap answer"}}]
            }
            mock_response.raise_for_status = MagicMock()
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            llm._client = mock_client

            await llm.generate("classify this", tier="utility", max_tokens=64)

            body = mock_client.post.call_args.kwargs["json"]
            assert body["model"] == "gpt-5.6-terra"
            assert body["reasoning_effort"] == "low"
            assert llm.last_model_used == "gpt-5.6-terra"

    @pytest.mark.asyncio
    async def test_generate_synthesis_tier_sends_full_model_and_high_effort(self):
        with patch.dict("os.environ", {"CODEX_PROXY_API_KEY": "test-key"}, clear=True):
            llm = LLMService(preferred_provider=ModelProvider.CODEX)
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "choices": [{"message": {"content": "scholarly answer"}}]
            }
            mock_response.raise_for_status = MagicMock()
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            llm._client = mock_client

            await llm.generate("synthesize", max_tokens=64)

            body = mock_client.post.call_args.kwargs["json"]
            assert body["model"] == "gpt-5.6-sol"
            assert body["reasoning_effort"] == "high"


class TestProviderRetryPolicy:
    """Fix 1 — account-level failures must fall through, not kill the loop."""

    @staticmethod
    def _status_error(status: int) -> httpx.HTTPStatusError:
        request = httpx.Request("POST", "https://example.com/v1/chat/completions")
        return httpx.HTTPStatusError(
            "boom", request=request, response=httpx.Response(status, request=request)
        )

    @pytest.mark.parametrize(
        "status", [401, 402, 403, 408, 409, 412, 425, 429, 500, 502, 503, 504]
    )
    def test_account_and_transient_statuses_retry_next_provider(self, status):
        assert (
            LLMService._should_retry_next_provider(self._status_error(status)) is True
        )

    @pytest.mark.parametrize("status", [400, 404, 422])
    def test_request_shape_errors_do_not_retry_next_provider(self, status):
        """Retrying a malformed request elsewhere cannot help."""
        assert (
            LLMService._should_retry_next_provider(self._status_error(status)) is False
        )

    def test_transport_errors_retry_next_provider(self):
        assert (
            LLMService._should_retry_next_provider(httpx.ConnectError("refused"))
            is True
        )
        assert LLMService._should_retry_next_provider(httpx.ReadTimeout("slow")) is True

    @pytest.mark.parametrize("status", [401, 402, 403, 412])
    def test_account_level_failures_disable_provider_for_the_session(self, status):
        """A suspended account must be skipped after ONE failure."""
        with patch.dict("os.environ", {"CODEX_PROXY_API_KEY": "k"}, clear=True):
            llm = LLMService()
        llm._mark_provider_invalid(ModelProvider.CODEX, self._status_error(status))
        assert ModelProvider.CODEX in llm._disabled_providers

    def test_rate_limit_backs_off_without_disabling(self):
        with patch.dict("os.environ", {"CODEX_PROXY_API_KEY": "k"}, clear=True):
            llm = LLMService()
        llm._mark_provider_invalid(ModelProvider.CODEX, self._status_error(429))
        assert ModelProvider.CODEX not in llm._disabled_providers
        assert llm._provider_in_backoff(ModelProvider.CODEX)

    @pytest.mark.asyncio
    async def test_generate_falls_through_on_412(self):
        """The regression: a 412 on the primary used to kill the whole loop."""
        env = {"CODEX_PROXY_API_KEY": "codex-key", "CLAUDE_PROXY_API_KEY": "claude-key"}
        with patch.dict("os.environ", env, clear=True):
            llm = LLMService(preferred_provider=ModelProvider.CODEX)
            claude_response = MagicMock()
            claude_response.json.return_value = {
                "choices": [{"message": {"content": "fallback answer"}}]
            }
            claude_response.raise_for_status = MagicMock()
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(
                side_effect=[self._status_error(412), claude_response]
            )
            llm._client = mock_client

            result = await llm.generate("Test prompt")

        assert result == "fallback answer"
        assert llm.last_provider_used == ModelProvider.CLAUDE.value
        assert ModelProvider.CODEX in llm._disabled_providers

    @pytest.mark.asyncio
    async def test_generate_falls_through_on_402(self):
        env = {"CODEX_PROXY_API_KEY": "codex-key", "CLAUDE_PROXY_API_KEY": "claude-key"}
        with patch.dict("os.environ", env, clear=True):
            llm = LLMService(preferred_provider=ModelProvider.CODEX)
            claude_response = MagicMock()
            claude_response.json.return_value = {
                "choices": [{"message": {"content": "fallback answer"}}]
            }
            claude_response.raise_for_status = MagicMock()
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(
                side_effect=[self._status_error(402), claude_response]
            )
            llm._client = mock_client

            result = await llm.generate("Test prompt")

        assert result == "fallback answer"
        assert llm.last_provider_used == ModelProvider.CLAUDE.value

    def test_format_provider_error_survives_unread_streamed_response(self):
        """Fix 5c — exc.response.text raises ResponseNotRead on a stream."""
        request = httpx.Request("POST", "https://example.com/v1/chat/completions")
        response = httpx.Response(500, request=request)
        # Simulate a streamed response whose body was never read.
        response.read = MagicMock(side_effect=httpx.ResponseNotRead())
        del response._content
        exc = httpx.HTTPStatusError("boom", request=request, response=response)

        formatted = LLMService._format_provider_error(exc)
        assert "500" in formatted


class TestSecretRedaction:
    """Fix 5 — API keys must never reach a log, an SSE frame or a trace row."""

    def test_redacts_key_query_param(self):
        msg = (
            "Client error '400 Bad Request' for url "
            "'https://generativelanguage.googleapis.com/v1beta/models/x:"
            "generateContent?key=AIzaSyD3481SECRETVALUE'"
        )
        redacted = _redact_secrets(msg)
        assert "AIzaSyD3481SECRETVALUE" not in redacted
        assert "key=REDACTED" in redacted

    def test_redacts_bearer_token(self):
        redacted = _redact_secrets("Authorization: Bearer sk-abc123def456ghi789")
        assert "sk-abc123def456ghi789" not in redacted
        assert "Bearer REDACTED" in redacted

    def test_redacts_alternate_secret_param_names(self):
        for param in ("api_key", "access_token", "token"):
            redacted = _redact_secrets(f"https://x.test/v1?{param}=SUPERSECRETVALUE")
            assert "SUPERSECRETVALUE" not in redacted

    def test_leaves_ordinary_text_alone(self):
        assert _redact_secrets("plain error message") == "plain error message"

    def test_format_provider_error_redacts_body(self):
        request = httpx.Request("POST", "https://example.com/v1?key=SECRETKEYVALUE")
        response = httpx.Response(
            400, request=request, text="failed for url https://x?key=SECRETKEYVALUE"
        )
        exc = httpx.HTTPStatusError("boom", request=request, response=response)
        assert "SECRETKEYVALUE" not in LLMService._format_provider_error(exc)

    @pytest.mark.asyncio
    async def test_gemini_key_travels_in_a_header_not_the_url(self):
        """Fix 5a — ?key= puts the credential inside every httpx error message."""
        with patch.dict("os.environ", {"GEMINI_API_KEY": "secret-key"}, clear=True):
            llm = LLMService(preferred_provider=ModelProvider.GEMINI)
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "candidates": [{"content": {"parts": [{"text": "hi"}]}}]
            }
            mock_response.raise_for_status = MagicMock()
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            llm._client = mock_client

            await llm.generate("Test prompt", max_tokens=16)

        call = mock_client.post.call_args
        assert "key" not in (call.kwargs.get("params") or {})
        assert call.kwargs["headers"]["x-goog-api-key"] == "secret-key"
        assert "secret-key" not in call.args[0]


class TestGeminiStreamRequestBody:
    """Fix 3 — the streaming path must use the ONE correct body builder."""

    @staticmethod
    def _fake_stream(lines: list[str], mock_client) -> None:
        response = MagicMock()
        response.status_code = 200
        response.raise_for_status = MagicMock()

        async def _aiter_lines():
            for line in lines:
                yield line

        response.aiter_lines = _aiter_lines
        ctx = MagicMock()
        ctx.__aenter__ = AsyncMock(return_value=response)
        ctx.__aexit__ = AsyncMock(return_value=False)
        mock_client.stream = MagicMock(return_value=ctx)

    @pytest.mark.asyncio
    async def test_stream_gemini_uses_system_instruction_not_a_fake_model_turn(self):
        """The fabricated {"role":"model","parts":[{"text":"Understood."}]} turn
        is rejected by gemini-3-* (no thoughtSignature) → 400."""
        with patch.dict("os.environ", {"GEMINI_API_KEY": "secret-key"}, clear=True):
            llm = LLMService(preferred_provider=ModelProvider.GEMINI)
            mock_client = AsyncMock()
            self._fake_stream(
                [
                    'data: {"candidates":[{"content":{"parts":[{"text":"hello"}]}}]}',
                ],
                mock_client,
            )
            llm._client = mock_client

            chunks = [
                c
                async for c in llm.stream(
                    "User prompt", system_prompt="You are a scholar."
                )
            ]

        assert chunks == ["hello"]
        body = mock_client.stream.call_args.kwargs["json"]
        assert body["systemInstruction"] == {"parts": [{"text": "You are a scholar."}]}
        assert body["contents"] == [
            {"role": "user", "parts": [{"text": "User prompt"}]}
        ]
        assert all(turn["role"] != "model" for turn in body["contents"])

    @pytest.mark.asyncio
    async def test_stream_gemini_shares_the_builder_with_the_blocking_path(self):
        """Both paths must produce byte-identical bodies for the same inputs."""
        config = LLMService._resolve_config(ModelProvider.GEMINI)
        expected = LLMService._build_gemini_request_body(
            prompt="User prompt",
            system_prompt="You are a scholar.",
            temperature=0.7,
            max_tokens=4096,
            cached_content=None,
            config=config,
        )

        with patch.dict("os.environ", {"GEMINI_API_KEY": "secret-key"}, clear=True):
            llm = LLMService(preferred_provider=ModelProvider.GEMINI)
            mock_client = AsyncMock()
            self._fake_stream([], mock_client)
            llm._client = mock_client
            async for _ in llm.stream(
                "User prompt", system_prompt="You are a scholar."
            ):
                pass

        assert mock_client.stream.call_args.kwargs["json"] == expected

    @pytest.mark.asyncio
    async def test_stream_gemini_key_is_a_header(self):
        with patch.dict("os.environ", {"GEMINI_API_KEY": "secret-key"}, clear=True):
            llm = LLMService(preferred_provider=ModelProvider.GEMINI)
            mock_client = AsyncMock()
            self._fake_stream([], mock_client)
            llm._client = mock_client
            async for _ in llm.stream("User prompt"):
                pass

        kwargs = mock_client.stream.call_args.kwargs
        assert kwargs["headers"]["x-goog-api-key"] == "secret-key"
        assert kwargs["params"] == {"alt": "sse"}

    @pytest.mark.asyncio
    async def test_stream_gemini_never_yields_thought_parts(self):
        """Chain-of-thought must not leak into the answer stream."""
        with patch.dict("os.environ", {"GEMINI_API_KEY": "secret-key"}, clear=True):
            llm = LLMService(preferred_provider=ModelProvider.GEMINI)
            mock_client = AsyncMock()
            self._fake_stream(
                [
                    'data: {"candidates":[{"content":{"parts":'
                    '[{"text":"scratch","thought":true}]}}]}',
                    'data: {"candidates":[{"content":{"parts":[{"text":"answer"}]}}]}',
                ],
                mock_client,
            )
            llm._client = mock_client
            chunks = [c async for c in llm.stream("User prompt")]

        assert chunks == ["answer"]

    @pytest.mark.asyncio
    async def test_stream_error_body_is_read_before_raise(self):
        """Fix 3 — the provider's error payload must survive raise_for_status."""
        with patch.dict("os.environ", {"GEMINI_API_KEY": "secret-key"}, clear=True):
            llm = LLMService(preferred_provider=ModelProvider.GEMINI)

            response = MagicMock()
            response.status_code = 400
            response.aread = AsyncMock(return_value=b'{"error":"bad request"}')
            response.raise_for_status = MagicMock(
                side_effect=httpx.HTTPStatusError(
                    "bad",
                    request=httpx.Request("POST", "https://x.test"),
                    response=httpx.Response(
                        400, request=httpx.Request("POST", "https://x.test")
                    ),
                )
            )
            ctx = MagicMock()
            ctx.__aenter__ = AsyncMock(return_value=response)
            ctx.__aexit__ = AsyncMock(return_value=False)
            mock_client = AsyncMock()
            mock_client.stream = MagicMock(return_value=ctx)
            llm._client = mock_client

            with pytest.raises(httpx.HTTPStatusError):
                async for _ in llm.stream("User prompt"):
                    pass

        response.aread.assert_awaited_once()


class TestGenerateWithToolsProviderLoop:
    """Fix 2 — the ReAct loop must survive a downed provider."""

    @staticmethod
    def _tool_response(text: str) -> MagicMock:
        response = MagicMock()
        response.status_code = 200
        response.json.return_value = {
            "choices": [{"message": {"role": "assistant", "content": text}}]
        }
        response.raise_for_status = MagicMock()
        return response

    def test_candidates_exclude_gemini(self):
        env = {
            "CODEX_PROXY_API_KEY": "codex-key",
            "CLAUDE_PROXY_API_KEY": "claude-key",
            "GEMINI_API_KEY": "gem-key",
        }
        with patch.dict("os.environ", env, clear=True):
            llm = LLMService(preferred_provider=ModelProvider.CODEX)
            candidates = llm._tool_call_candidates(None, tier="synthesis")

        providers = [p for p, _ in candidates]
        assert ModelProvider.GEMINI not in providers
        assert providers == [ModelProvider.CODEX, ModelProvider.CLAUDE]

    def test_model_override_leads_but_fallbacks_remain(self):
        env = {"CODEX_PROXY_API_KEY": "codex-key", "CLAUDE_PROXY_API_KEY": "claude-key"}
        with patch.dict("os.environ", env, clear=True):
            llm = LLMService(preferred_provider=ModelProvider.CODEX)
            candidates = llm._tool_call_candidates("claude-opus-5", tier="synthesis")

        assert candidates[0] == (ModelProvider.CLAUDE, "claude-opus-5")
        assert (ModelProvider.CODEX, "gpt-5.6-sol") in candidates

    @pytest.mark.asyncio
    async def test_falls_through_to_next_provider(self):
        env = {"CODEX_PROXY_API_KEY": "codex-key", "CLAUDE_PROXY_API_KEY": "claude-key"}
        with patch.dict("os.environ", env, clear=True):
            llm = LLMService(preferred_provider=ModelProvider.CODEX)
            request = httpx.Request("POST", "https://x.test")
            down = httpx.HTTPStatusError(
                "down", request=request, response=httpx.Response(503, request=request)
            )
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(
                side_effect=[down, self._tool_response("recovered")]
            )
            llm._client = mock_client

            with patch("asyncio.sleep", new=AsyncMock()):
                message = await llm.generate_with_tools(
                    messages=[{"role": "user", "content": "hi"}], tools=[]
                )

        assert message["content"] == "recovered"
        assert llm.last_provider_used == ModelProvider.CLAUDE.value

    @pytest.mark.asyncio
    async def test_raises_when_no_compatible_provider(self):
        with patch.dict("os.environ", {"GEMINI_API_KEY": "gem-key"}, clear=True):
            llm = LLMService(preferred_provider=ModelProvider.GEMINI)
            with pytest.raises(RuntimeError, match="tool-calling"):
                await llm.generate_with_tools(
                    messages=[{"role": "user", "content": "hi"}], tools=[]
                )

    @pytest.mark.asyncio
    async def test_sends_tools_and_reasoning_effort(self):
        with patch.dict("os.environ", {"CODEX_PROXY_API_KEY": "codex-key"}, clear=True):
            llm = LLMService(preferred_provider=ModelProvider.CODEX)
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=self._tool_response("ok"))
            llm._client = mock_client

            tools = [{"type": "function", "function": {"name": "search"}}]
            await llm.generate_with_tools(
                messages=[{"role": "user", "content": "hi"}], tools=tools
            )

        body = mock_client.post.call_args.kwargs["json"]
        assert body["tools"] == tools
        assert body["tool_choice"] == "auto"
        assert body["reasoning_effort"] == "high"


class TestSegmentedStreamProviderLoop:
    """Fix 4 — stream_segmented must not dead-end on one resolved provider."""

    def test_override_leads_and_fallbacks_follow(self):
        env = {
            "CODEX_PROXY_API_KEY": "codex-key",
            "CLAUDE_PROXY_API_KEY": "claude-key",
            "GEMINI_API_KEY": "gem-key",
        }
        with patch.dict("os.environ", env, clear=True):
            llm = LLMService(preferred_provider=ModelProvider.CODEX)
            candidates = llm._segmented_stream_candidates(
                "gpt-5.6-sol", tier="synthesis"
            )

        assert candidates[0] == (ModelProvider.CODEX, "gpt-5.6-sol")
        assert (ModelProvider.CLAUDE, "claude-opus-5") in candidates
        assert (ModelProvider.GEMINI, "gemini-3.1-pro-preview") in candidates

    def test_providers_without_a_key_are_skipped(self):
        with patch.dict("os.environ", {"CODEX_PROXY_API_KEY": "codex-key"}, clear=True):
            llm = LLMService(preferred_provider=ModelProvider.CODEX)
            candidates = llm._segmented_stream_candidates(None, tier="synthesis")

        assert [p for p, _ in candidates] == [ModelProvider.CODEX]

    @pytest.mark.asyncio
    async def test_raises_when_no_provider_configured(self):
        with patch.dict("os.environ", {}, clear=True):
            llm = LLMService()
            with pytest.raises(RuntimeError, match="No LLM provider available"):
                async for _ in llm.stream_segmented("prompt"):
                    pass

    @pytest.mark.asyncio
    async def test_failed_rung_falls_through_to_the_next_provider(self):
        env = {"CODEX_PROXY_API_KEY": "codex-key", "CLAUDE_PROXY_API_KEY": "claude-key"}
        with patch.dict("os.environ", env, clear=True):
            llm = LLMService(preferred_provider=ModelProvider.CODEX)

            request = httpx.Request("POST", "https://x.test")
            down = MagicMock()
            down.status_code = 503
            down.aread = AsyncMock(return_value=b"unavailable")
            down.raise_for_status = MagicMock(
                side_effect=httpx.HTTPStatusError(
                    "down",
                    request=request,
                    response=httpx.Response(503, request=request),
                )
            )
            down_ctx = MagicMock()
            down_ctx.__aenter__ = AsyncMock(return_value=down)
            down_ctx.__aexit__ = AsyncMock(return_value=False)

            good = MagicMock()
            good.status_code = 200
            good.raise_for_status = MagicMock()

            async def _aiter_lines():
                yield 'data: {"choices":[{"delta":{"content":"recovered"}}]}'
                yield "data: [DONE]"

            good.aiter_lines = _aiter_lines
            good_ctx = MagicMock()
            good_ctx.__aenter__ = AsyncMock(return_value=good)
            good_ctx.__aexit__ = AsyncMock(return_value=False)

            mock_client = AsyncMock()
            mock_client.stream = MagicMock(side_effect=[down_ctx, good_ctx])
            llm._client = mock_client

            segments = [s async for s in llm.stream_segmented("prompt")]

        assert segments == [("answer", "recovered")]
        assert llm.last_provider_used == ModelProvider.CLAUDE.value


class TestOpenAICompatiblePayload:
    """The shared OpenAI-compatible request body."""

    @staticmethod
    def _payload(provider: ModelProvider, **kwargs) -> dict:
        config = LLMService._resolve_config(provider)
        return LLMService._openai_compatible_payload(
            provider, "prompt", None, 0.3, 512, config, **kwargs
        )

    def test_reasoning_effort_only_attached_for_codex(self):
        assert (
            self._payload(ModelProvider.CODEX, reasoning_effort="high")[
                "reasoning_effort"
            ]
            == "high"
        )
        assert "reasoning_effort" not in self._payload(
            ModelProvider.CLAUDE, reasoning_effort="high"
        )

    def test_shared_helper_owns_the_codex_only_attachment(self):
        """Every path (generate/stream/tools) attaches via ONE helper."""
        codex: dict = {}
        LLMService._apply_reasoning_effort(codex, ModelProvider.CODEX, "medium")
        assert codex == {"reasoning_effort": "medium"}

        claude: dict = {}
        LLMService._apply_reasoning_effort(claude, ModelProvider.CLAUDE, "medium")
        assert claude == {}

        unset: dict = {}
        LLMService._apply_reasoning_effort(unset, ModelProvider.CODEX, None)
        assert unset == {}

    def test_prompt_cache_id_only_attached_for_codex(self):
        assert (
            self._payload(ModelProvider.CODEX, prompt_cache_id="eleutheria-x-v1")[
                "prompt_cache_id"
            ]
            == "eleutheria-x-v1"
        )
        assert "prompt_cache_id" not in self._payload(
            ModelProvider.CLAUDE, prompt_cache_id="eleutheria-x-v1"
        )

    def test_temperature_is_not_clamped(self):
        for provider in (ModelProvider.CODEX, ModelProvider.CLAUDE):
            assert self._payload(provider)["temperature"] == 0.3

    def test_strict_json_schema_is_attached(self):
        payload = self._payload(
            ModelProvider.CODEX, response_json_schema={"type": "object"}
        )
        assert payload["response_format"]["type"] == "json_schema"
        assert payload["response_format"]["json_schema"]["strict"] is True

    def test_claude_degrades_to_json_object_mode(self):
        """The Claude proxy only guarantees json_object — never send it a schema."""
        payload = self._payload(
            ModelProvider.CLAUDE, response_json_schema={"type": "object"}
        )
        assert payload["response_format"] == {"type": "json_object"}

    def test_json_object_mode_without_a_schema(self):
        payload = self._payload(
            ModelProvider.CODEX, response_mime_type="application/json"
        )
        assert payload["response_format"] == {"type": "json_object"}

    def test_response_format_absent_by_default(self):
        assert "response_format" not in self._payload(ModelProvider.CODEX)


class TestCodexSynthesisMaxTokensFloor:
    """F4 — reasoning tokens bill against max_tokens; the answer needs a floor."""

    @staticmethod
    def _payload(provider: ModelProvider, max_tokens: int, **kwargs) -> dict:
        config = LLMService._resolve_config(provider)
        return LLMService._openai_compatible_payload(
            provider, "prompt", None, 0.3, max_tokens, config, **kwargs
        )

    def test_small_synthesis_budget_is_raised_to_the_floor(self):
        """A 14k cap can be entirely eaten by a high-effort reasoning run."""
        payload = self._payload(ModelProvider.CODEX, 14000, tier="synthesis")
        assert payload["max_tokens"] == 32000

    def test_a_larger_caller_budget_is_never_lowered(self):
        payload = self._payload(ModelProvider.CODEX, 64000, tier="synthesis")
        assert payload["max_tokens"] == 64000

    def test_utility_tier_keeps_its_cheap_budget(self):
        payload = self._payload(ModelProvider.CODEX, 700, tier="utility")
        assert payload["max_tokens"] == 700

    def test_claude_small_verdict_budget_is_raised_to_its_floor(self):
        """A 700-token verifier call empties when opus-5 thinks past the cap."""
        payload = self._payload(ModelProvider.CLAUDE, 700, tier="synthesis")
        assert payload["max_tokens"] == 8000

    def test_claude_above_its_floor_is_untouched(self):
        payload = self._payload(ModelProvider.CLAUDE, 9000, tier="synthesis")
        assert payload["max_tokens"] == 9000

    def test_claude_env_override_sets_its_floor(self):
        with patch.dict("os.environ", {"CLAUDE_SYNTHESIS_MAX_TOKENS": "12000"}):
            payload = self._payload(ModelProvider.CLAUDE, 700, tier="synthesis")
        assert payload["max_tokens"] == 12000

    def test_claude_utility_tier_keeps_its_cheap_budget(self):
        payload = self._payload(ModelProvider.CLAUDE, 700, tier="utility")
        assert payload["max_tokens"] == 700

    def test_env_override_sets_the_floor(self):
        with patch.dict("os.environ", {"CODEX_SYNTHESIS_MAX_TOKENS": "48000"}):
            payload = self._payload(ModelProvider.CODEX, 9000, tier="synthesis")
        assert payload["max_tokens"] == 48000

    def test_unparseable_env_override_falls_back_to_the_default_floor(self):
        with patch.dict("os.environ", {"CODEX_SYNTHESIS_MAX_TOKENS": "not-a-number"}):
            payload = self._payload(ModelProvider.CODEX, 9000, tier="synthesis")
        assert payload["max_tokens"] == 32000

    @pytest.mark.asyncio
    async def test_generate_synthesis_call_carries_the_floor(self):
        with patch.dict("os.environ", {"CODEX_PROXY_API_KEY": "test-key"}, clear=True):
            llm = LLMService(preferred_provider=ModelProvider.CODEX)
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "choices": [{"message": {"content": "scholarly answer"}}]
            }
            mock_response.raise_for_status = MagicMock()
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            llm._client = mock_client

            await llm.generate("synthesize", max_tokens=12000)

            body = mock_client.post.call_args.kwargs["json"]
            assert body["max_tokens"] == 32000
            assert body["reasoning_effort"] == "high"


class TestStructuredOutputProviderFallback:
    """A 400 on a response_format call means THIS provider rejected it."""

    @staticmethod
    def _bad_request() -> httpx.HTTPStatusError:
        request = httpx.Request("POST", "https://example.com/v1/chat/completions")
        return httpx.HTTPStatusError(
            "bad request",
            request=request,
            response=httpx.Response(400, request=request),
        )

    def test_structured_call_advances_on_400(self):
        assert (
            LLMService._should_retry_next_provider(
                self._bad_request(), structured_output=True
            )
            is True
        )

    def test_plain_call_still_treats_400_as_fatal(self):
        assert LLMService._should_retry_next_provider(self._bad_request()) is False

    @pytest.mark.parametrize("status", [404, 422])
    def test_other_shape_errors_stay_fatal_even_when_structured(self, status):
        request = httpx.Request("POST", "https://example.com/v1/chat/completions")
        exc = httpx.HTTPStatusError(
            "boom", request=request, response=httpx.Response(status, request=request)
        )
        assert (
            LLMService._should_retry_next_provider(exc, structured_output=True) is False
        )

    @pytest.mark.asyncio
    async def test_schema_400_falls_through_to_the_next_provider(self):
        env = {"CODEX_PROXY_API_KEY": "k1", "CLAUDE_PROXY_API_KEY": "k2"}
        with patch.dict("os.environ", env, clear=True):
            llm = LLMService(preferred_provider=ModelProvider.CODEX)

            request = httpx.Request("POST", "https://example.com/v1/chat/completions")
            rejected = MagicMock()
            rejected.raise_for_status = MagicMock(
                side_effect=httpx.HTTPStatusError(
                    "unsupported response_format",
                    request=request,
                    response=httpx.Response(400, request=request),
                )
            )
            accepted = MagicMock()
            accepted.json.return_value = {"choices": [{"message": {"content": "{}"}}]}
            accepted.raise_for_status = MagicMock()

            mock_client = AsyncMock()
            mock_client.post = AsyncMock(side_effect=[rejected, accepted])
            llm._client = mock_client

            result = await llm.generate(
                "classify",
                response_json_schema={"type": "object"},
                max_tokens=256,
            )

        assert result == "{}"
        assert llm.last_provider_used == ModelProvider.CLAUDE.value


class TestPromptCacheId:
    """Agent-scoped prompt cache id."""

    def test_cache_id_composed_from_agent_id(self):
        with patch.dict("os.environ", {}, clear=True):
            assert (
                LLMService._prompt_cache_id("scholar-orchestrator")
                == "eleutheria-scholar-orchestrator-v1"
            )

    def test_cache_id_none_when_agent_id_missing(self):
        assert LLMService._prompt_cache_id(None) is None
        assert LLMService._prompt_cache_id("") is None

    def test_cache_id_respects_version_env(self):
        with patch.dict(
            "os.environ", {"ELEUTHERIA_PROMPT_CACHE_VERSION": "v9"}, clear=True
        ):
            assert LLMService._prompt_cache_id("agent") == "eleutheria-agent-v9"

    @pytest.mark.asyncio
    async def test_generate_propagates_agent_id_to_the_payload(self):
        env = {"CODEX_PROXY_API_KEY": "codex-key"}
        with patch.dict("os.environ", env, clear=True):
            llm = LLMService(preferred_provider=ModelProvider.CODEX)
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "choices": [{"message": {"content": "ok"}}]
            }
            mock_response.raise_for_status = MagicMock()
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            llm._client = mock_client

            await llm.generate("prompt", agent_id="concept-mapper", max_tokens=16)

        body = mock_client.post.call_args.kwargs["json"]
        assert body["prompt_cache_id"] == "eleutheria-concept-mapper-v1"


class TestPerProviderRequestConfig:
    """Every rung must speak to ITS OWN proxy — never the preferred one's.

    Regression guard for the prod incident where a ``claude-opus-5`` rung was
    suspected of posting to the Codex proxy: each resolved provider owns its
    base_url, key and model, on BOTH the model_override path and the
    fallback-loop path.
    """

    ENV = {
        "CODEX_PROXY_API_KEY": "codex-key",
        "CLAUDE_PROXY_API_KEY": "claude-key",
        "CODEX_PROXY_BASE_URL": "http://cli-proxy-api:8317/v1",
        "CLAUDE_PROXY_BASE_URL": "http://pragma-claude-proxy:8318/v1",
    }

    @staticmethod
    def _ok_response() -> MagicMock:
        response = MagicMock()
        response.json.return_value = {"choices": [{"message": {"content": "ok"}}]}
        response.raise_for_status = MagicMock()
        return response

    @pytest.mark.asyncio
    async def test_model_override_posts_to_the_claude_proxy(self):
        with patch.dict("os.environ", self.ENV, clear=True):
            llm = LLMService(preferred_provider=ModelProvider.CODEX)
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=self._ok_response())
            llm._client = mock_client

            await llm.generate("q", model_override="claude-opus-5", max_tokens=16)

        url = mock_client.post.call_args.args[0]
        assert url == "http://pragma-claude-proxy:8318/v1/chat/completions"
        headers = mock_client.post.call_args.kwargs["headers"]
        assert headers["Authorization"] == "Bearer claude-key"
        assert mock_client.post.call_args.kwargs["json"]["model"] == "claude-opus-5"
        assert llm.last_provider_used == ModelProvider.CLAUDE.value

    @pytest.mark.asyncio
    async def test_fallback_loop_claude_rung_posts_to_the_claude_proxy(self):
        with patch.dict("os.environ", self.ENV, clear=True):
            llm = LLMService(preferred_provider=ModelProvider.CODEX)
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(
                side_effect=[
                    httpx.ConnectError("codex proxy down"),
                    httpx.ConnectError("codex proxy down"),
                    self._ok_response(),
                ]
            )
            llm._client = mock_client

            with patch("asyncio.sleep", new=AsyncMock()):
                await llm.generate("q", max_tokens=16)

        codex_call, _retry, claude_call = mock_client.post.call_args_list
        assert codex_call.args[0] == "http://cli-proxy-api:8317/v1/chat/completions"
        assert codex_call.kwargs["headers"]["Authorization"] == "Bearer codex-key"
        assert claude_call.args[0] == (
            "http://pragma-claude-proxy:8318/v1/chat/completions"
        )
        assert claude_call.kwargs["headers"]["Authorization"] == "Bearer claude-key"
        assert claude_call.kwargs["json"]["model"] == "claude-opus-5"
        assert llm.last_provider_used == ModelProvider.CLAUDE.value


class TestStrictJsonSchemaSanitizer:
    """OpenAI strict structured outputs: additionalProperties + full required."""

    NESTED_SCHEMA: dict = {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "citations": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "urn": {"type": "string"},
                        "confidence": {"type": "number"},
                    },
                    "required": ["urn"],
                },
            },
            "verdict": {
                "anyOf": [
                    {"type": "object", "properties": {"ok": {"type": "boolean"}}},
                    {"type": "null"},
                ]
            },
        },
        "required": ["title"],
        "$defs": {
            "Note": {"type": "object", "properties": {"text": {"type": "string"}}}
        },
    }

    def test_every_object_level_is_sanitized(self):
        sanitized = strict_json_schema(self.NESTED_SCHEMA)

        assert sanitized["additionalProperties"] is False
        assert sanitized["required"] == ["title", "citations", "verdict"]

        item = sanitized["properties"]["citations"]["items"]
        assert item["additionalProperties"] is False
        assert item["required"] == ["urn", "confidence"]

        branch = sanitized["properties"]["verdict"]["anyOf"][0]
        assert branch["additionalProperties"] is False
        assert branch["required"] == ["ok"]
        assert sanitized["properties"]["verdict"]["anyOf"][1] == {"type": "null"}

        defs = sanitized["$defs"]["Note"]
        assert defs["additionalProperties"] is False
        assert defs["required"] == ["text"]

    def test_scalar_leaves_are_left_alone(self):
        sanitized = strict_json_schema(self.NESTED_SCHEMA)
        assert sanitized["properties"]["title"] == {"type": "string"}
        assert sanitized["properties"]["citations"]["type"] == "array"
        assert "additionalProperties" not in sanitized["properties"]["citations"]

    def test_callers_schema_is_never_mutated(self):
        import copy as _copy

        before = _copy.deepcopy(self.NESTED_SCHEMA)
        strict_json_schema(self.NESTED_SCHEMA)
        assert before == self.NESTED_SCHEMA

    def test_codex_payload_carries_the_sanitized_schema(self):
        config = LLMService._resolve_config(ModelProvider.CODEX)
        payload = LLMService._openai_compatible_payload(
            ModelProvider.CODEX,
            "prompt",
            None,
            0.3,
            512,
            config,
            response_json_schema=self.NESTED_SCHEMA,
        )
        schema = payload["response_format"]["json_schema"]["schema"]
        assert schema["additionalProperties"] is False
        assert schema["required"] == ["title", "citations", "verdict"]
        assert schema is not self.NESTED_SCHEMA
        assert "additionalProperties" not in self.NESTED_SCHEMA

    def test_claude_path_is_unaffected(self):
        config = LLMService._resolve_config(ModelProvider.CLAUDE)
        payload = LLMService._openai_compatible_payload(
            ModelProvider.CLAUDE,
            "prompt",
            None,
            0.3,
            512,
            config,
            response_json_schema=self.NESTED_SCHEMA,
        )
        assert payload["response_format"] == {"type": "json_object"}
        assert "additionalProperties" not in self.NESTED_SCHEMA

    def test_gemini_path_sends_the_raw_schema(self):
        body = LLMService._build_gemini_request_body(
            prompt="prompt",
            system_prompt=None,
            temperature=0.3,
            max_tokens=512,
            cached_content=None,
            config=LLMService._resolve_config(ModelProvider.GEMINI),
            response_mime_type="application/json",
            response_json_schema=self.NESTED_SCHEMA,
        )
        sent = body["generationConfig"]["responseJsonSchema"]
        assert sent == self.NESTED_SCHEMA
        assert "additionalProperties" not in sent


class TestContextOverflowFallback:
    """A 400 context_too_large is a per-model limit, not a malformed request."""

    @staticmethod
    def _overflow(body: str) -> httpx.HTTPStatusError:
        request = httpx.Request("POST", "https://example.com/v1/chat/completions")
        return httpx.HTTPStatusError(
            "bad request",
            request=request,
            response=httpx.Response(400, text=body, request=request),
        )

    @pytest.mark.parametrize(
        "body",
        [
            '{"error":{"code":"context_too_large"}}',
            '{"error":{"message":"Your input exceeds the context window of this model."}}',
        ],
    )
    def test_context_overflow_advances_to_the_next_provider(self, body):
        assert LLMService._should_retry_next_provider(self._overflow(body)) is True

    def test_other_400_bodies_stay_fatal(self):
        exc = self._overflow('{"error":{"message":"unknown provider for model x"}}')
        assert LLMService._should_retry_next_provider(exc) is False

    @pytest.mark.asyncio
    async def test_oversized_prompt_falls_through_to_gemini(self):
        env = {"CODEX_PROXY_API_KEY": "codex-key", "GEMINI_API_KEY": "gemini-key"}
        with patch.dict("os.environ", env, clear=True):
            llm = LLMService(preferred_provider=ModelProvider.CODEX)

            request = httpx.Request("POST", "https://example.com/v1/chat/completions")
            overflowed = MagicMock()
            overflowed.raise_for_status = MagicMock(
                side_effect=httpx.HTTPStatusError(
                    "context_too_large",
                    request=request,
                    response=httpx.Response(
                        400,
                        text='{"error":{"code":"context_too_large"}}',
                        request=request,
                    ),
                )
            )
            gemini = MagicMock()
            gemini.json.return_value = {
                "candidates": [{"content": {"parts": [{"text": "answer"}]}}]
            }
            gemini.raise_for_status = MagicMock()

            mock_client = AsyncMock()
            mock_client.post = AsyncMock(side_effect=[overflowed, gemini])
            llm._client = mock_client

            result = await llm.generate("a very long pack", max_tokens=256)

        assert result == "answer"
        assert llm.last_provider_used == ModelProvider.GEMINI.value


class TestSizeAwareProviderRouting:
    """Rungs whose context window cannot hold the prompt are skipped up front.

    The Codex subscription backend caps the effective window at ~207k tokens
    (prompt AND answer share it), so an oversized synthesis pack used to burn a
    round trip on a 400 ``context_too_large`` before reaching a 1M provider.
    """

    CODEX_URL = PROVIDER_CONFIGS[ModelProvider.CODEX]["base_url"]
    CLAUDE_URL = PROVIDER_CONFIGS[ModelProvider.CLAUDE]["base_url"]

    @staticmethod
    def _ok_response(content: str = "answer"):
        response = MagicMock()
        response.json.return_value = {"choices": [{"message": {"content": content}}]}
        response.raise_for_status = MagicMock()
        return response

    @staticmethod
    def _prompt_of_tokens(tokens: int) -> str:
        """A prompt the conservative estimator (chars // 3) prices at ~tokens."""
        return "λ" * (tokens * 3)

    def test_window_defaults(self):
        with patch.dict("os.environ", {}, clear=True):
            assert LLMService._max_input_tokens(ModelProvider.CODEX) == 200_000
            assert LLMService._max_input_tokens(ModelProvider.CLAUDE) == 1_000_000
            assert LLMService._max_input_tokens(ModelProvider.GEMINI) == 1_000_000

    def test_estimator_over_estimates_dense_greek(self):
        # ~3 chars/token on polytonic Greek: the estimate must not come in under.
        greek = "ἐφ᾽ ἡμῖν " * 1000
        assert LLMService._estimate_input_tokens(greek) >= len(greek) // 4
        assert LLMService._estimate_input_tokens("", None) == 0

    @pytest.mark.asyncio
    async def test_oversized_prompt_skips_codex_and_goes_to_claude(self):
        env = {
            "CODEX_PROXY_API_KEY": "codex-key",
            "CLAUDE_PROXY_API_KEY": "claude-key",
        }
        with patch.dict("os.environ", env, clear=True):
            llm = LLMService(preferred_provider=ModelProvider.CODEX)
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=self._ok_response())
            llm._client = mock_client

            result = await llm.generate(
                self._prompt_of_tokens(250_000), max_tokens=4096
            )

        assert result == "answer"
        assert llm.last_provider_used == ModelProvider.CLAUDE.value
        assert mock_client.post.call_count == 1
        assert mock_client.post.call_args.args[0].startswith(self.CLAUDE_URL)

    @pytest.mark.asyncio
    async def test_small_prompt_still_goes_to_codex_first(self):
        env = {
            "CODEX_PROXY_API_KEY": "codex-key",
            "CLAUDE_PROXY_API_KEY": "claude-key",
        }
        with patch.dict("os.environ", env, clear=True):
            llm = LLMService(preferred_provider=ModelProvider.CODEX)
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=self._ok_response())
            llm._client = mock_client

            result = await llm.generate("Short scholarly question", max_tokens=1024)

        assert result == "answer"
        assert llm.last_provider_used == ModelProvider.CODEX.value
        assert mock_client.post.call_args.args[0].startswith(self.CODEX_URL)

    @pytest.mark.asyncio
    async def test_when_no_window_fits_the_widest_provider_is_attempted(self):
        env = {
            "CODEX_PROXY_API_KEY": "codex-key",
            "CLAUDE_PROXY_API_KEY": "claude-key",
            "CODEX_MAX_INPUT_TOKENS": "1000",
            "CLAUDE_MAX_INPUT_TOKENS": "2000",
        }
        with patch.dict("os.environ", env, clear=True):
            llm = LLMService(preferred_provider=ModelProvider.CODEX)
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=self._ok_response())
            llm._client = mock_client

            result = await llm.generate(self._prompt_of_tokens(50_000), max_tokens=512)

        # Nobody fits — the request still goes out, on the widest rung.
        assert result == "answer"
        assert llm.last_provider_used == ModelProvider.CLAUDE.value
        assert mock_client.post.call_args.args[0].startswith(self.CLAUDE_URL)

    @pytest.mark.asyncio
    async def test_env_override_widens_the_codex_window(self):
        env = {
            "CODEX_PROXY_API_KEY": "codex-key",
            "CLAUDE_PROXY_API_KEY": "claude-key",
            "CODEX_MAX_INPUT_TOKENS": "900000",
        }
        with patch.dict("os.environ", env, clear=True):
            assert LLMService._max_input_tokens(ModelProvider.CODEX) == 900_000

            llm = LLMService(preferred_provider=ModelProvider.CODEX)
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=self._ok_response())
            llm._client = mock_client

            result = await llm.generate(
                self._prompt_of_tokens(250_000), max_tokens=4096
            )

        assert result == "answer"
        assert llm.last_provider_used == ModelProvider.CODEX.value
        assert mock_client.post.call_args.args[0].startswith(self.CODEX_URL)

    def test_invalid_env_override_falls_back_to_the_default(self):
        with patch.dict("os.environ", {"CODEX_MAX_INPUT_TOKENS": "nope"}, clear=True):
            assert LLMService._max_input_tokens(ModelProvider.CODEX) == 200_000
        with patch.dict("os.environ", {"CODEX_MAX_INPUT_TOKENS": "0"}, clear=True):
            assert LLMService._max_input_tokens(ModelProvider.CODEX) == 200_000

    @pytest.mark.asyncio
    async def test_tool_calling_skips_the_codex_rung_too(self):
        env = {
            "CODEX_PROXY_API_KEY": "codex-key",
            "CLAUDE_PROXY_API_KEY": "claude-key",
        }
        with patch.dict("os.environ", env, clear=True):
            llm = LLMService(preferred_provider=ModelProvider.CODEX)
            response = MagicMock()
            response.status_code = 200
            response.json.return_value = {
                "choices": [{"message": {"role": "assistant", "content": "ok"}}]
            }
            response.raise_for_status = MagicMock()
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=response)
            llm._client = mock_client

            message = await llm.generate_with_tools(
                messages=[
                    {"role": "user", "content": self._prompt_of_tokens(250_000)},
                ],
                tools=[],
                max_tokens=1024,
            )

        assert message["content"] == "ok"
        assert llm.last_provider_used == ModelProvider.CLAUDE.value
        assert mock_client.post.call_args.args[0].startswith(self.CLAUDE_URL)
