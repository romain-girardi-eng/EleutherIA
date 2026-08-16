"""The Gemini rung: OpenAI-compatible proxy vs. the native paid API.

``GEMINI_PROXY_BASE_URL`` switches the whole GEMINI provider onto the same
OpenAI-compatible code paths as the Codex and Claude proxies (bearer key,
``/chat/completions``, tool calling, streaming). With the variable unset the
historical native ``generativelanguage`` path must be byte-for-byte unchanged —
that is the half of this file that guards the fallback.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from eleutheria_graphrag.agents.dialectical_synthesis import (
    scholar_synthesis_fallback_chain,
)
from eleutheria_graphrag.services.llm_service import (
    GEMINI_PROXY_DEFAULT_LIGHT_MODEL,
    GEMINI_PROXY_DEFAULT_MODEL,
    UTILITY_TIER,
    LLMService,
    ModelProvider,
    gemini_proxy_enabled,
    resolve_gemini_light_model,
    resolve_gemini_model,
)
from eleutheria_graphrag.services.model_registry import get_model

PROXY = "http://pragma-gemini-proxy:8320/v1"

_PROXY_ENV = {
    "GEMINI_PROXY_BASE_URL": PROXY,
    "GEMINI_PROXY_API_KEY": "proxy-key",
    "GEMINI_MODEL": "gemini-3.1-pro-low",
    "GEMINI_LIGHT_MODEL": "gemini-3.7-flash-high",
}


class TestProxyDetection:
    def test_disabled_without_base_url(self):
        with patch.dict("os.environ", {}, clear=True):
            assert gemini_proxy_enabled() is False

    def test_enabled_with_base_url(self):
        with patch.dict("os.environ", {"GEMINI_PROXY_BASE_URL": PROXY}, clear=True):
            assert gemini_proxy_enabled() is True

    def test_dialect_switch(self):
        with patch.dict("os.environ", {}, clear=True):
            assert LLMService._speaks_openai_dialect(ModelProvider.GEMINI) is False
        with patch.dict("os.environ", _PROXY_ENV, clear=True):
            assert LLMService._speaks_openai_dialect(ModelProvider.GEMINI) is True
        # The two proxies are unconditional either way.
        with patch.dict("os.environ", {}, clear=True):
            assert LLMService._speaks_openai_dialect(ModelProvider.CODEX) is True
            assert LLMService._speaks_openai_dialect(ModelProvider.CLAUDE) is True


class TestModelResolution:
    def test_native_defaults_unchanged(self):
        with patch.dict("os.environ", {}, clear=True):
            assert resolve_gemini_model() == "gemini-3.1-pro-preview"
            # No light model natively: the pro model serves both tiers.
            assert resolve_gemini_light_model() == ""

    def test_proxy_defaults(self):
        with patch.dict("os.environ", {"GEMINI_PROXY_BASE_URL": PROXY}, clear=True):
            assert resolve_gemini_model() == GEMINI_PROXY_DEFAULT_MODEL
            assert resolve_gemini_light_model() == GEMINI_PROXY_DEFAULT_LIGHT_MODEL

    def test_env_always_wins(self):
        with patch.dict("os.environ", _PROXY_ENV, clear=True):
            assert resolve_gemini_model() == "gemini-3.1-pro-low"
            assert resolve_gemini_light_model() == "gemini-3.7-flash-high"

    def test_resolved_config_carries_proxy_url_and_models(self):
        with patch.dict("os.environ", _PROXY_ENV, clear=True):
            config = LLMService._resolve_config(ModelProvider.GEMINI)
            assert config["base_url"] == PROXY
            assert config["model"] == "gemini-3.1-pro-low"
            assert config["light_model"] == "gemini-3.7-flash-high"
            assert (
                LLMService._model_for_request(config, tier=UTILITY_TIER)
                == "gemini-3.7-flash-high"
            )

    def test_native_config_unchanged(self):
        with patch.dict("os.environ", {"GEMINI_API_KEY": "paid"}, clear=True):
            config = LLMService._resolve_config(ModelProvider.GEMINI)
            assert config["base_url"].startswith("https://generativelanguage")
            assert config["model"] == "gemini-3.1-pro-preview"
            assert "light_model" not in config

    def test_context_window_stays_1m(self):
        for env in ({}, _PROXY_ENV):
            with patch.dict("os.environ", env, clear=True):
                assert LLMService._max_input_tokens(ModelProvider.GEMINI) == 1_000_000
        with patch.dict(
            "os.environ",
            {**_PROXY_ENV, "GEMINI_MAX_INPUT_TOKENS": "500000"},
            clear=True,
        ):
            assert LLMService._max_input_tokens(ModelProvider.GEMINI) == 500_000

    def test_registry_api_id_follows_env(self):
        with patch.dict("os.environ", {}, clear=True):
            assert get_model("gemini-3.1-pro").api_id == "gemini-3.1-pro-preview"
        with patch.dict("os.environ", _PROXY_ENV, clear=True):
            info = get_model("gemini-3.1-pro")
            assert info.api_id == "gemini-3.1-pro-low"
            assert info.context == 1_000_000
            assert info.label == "Gemini 3.1 Pro"

    def test_synthesis_fallback_chain_uses_configured_model(self):
        with patch.dict("os.environ", {}, clear=True):
            assert scholar_synthesis_fallback_chain()[-1] == "gemini-3.1-pro-preview"
        with patch.dict("os.environ", _PROXY_ENV, clear=True):
            assert scholar_synthesis_fallback_chain()[-1] == "gemini-3.1-pro-low"


class TestApiKey:
    def test_proxy_key_used_when_proxy_configured(self):
        env = {**_PROXY_ENV, "GEMINI_API_KEY": "paid-key"}
        with patch.dict("os.environ", env, clear=True):
            llm = LLMService()
            assert llm._api_key_for(ModelProvider.GEMINI) == "proxy-key"

    def test_paid_key_never_leaks_to_the_proxy(self):
        """With the proxy on and no proxy key the rung is simply unavailable."""
        env = {"GEMINI_PROXY_BASE_URL": PROXY, "GEMINI_API_KEY": "paid-key"}
        with patch.dict("os.environ", env, clear=True):
            llm = LLMService()
            assert llm._api_key_for(ModelProvider.GEMINI) == ""
            assert ModelProvider.GEMINI not in llm.available_providers

    def test_native_key_used_without_proxy(self):
        with patch.dict("os.environ", {"GEMINI_API_KEY": "paid-key"}, clear=True):
            llm = LLMService()
            assert llm._api_key_for(ModelProvider.GEMINI) == "paid-key"
            assert ModelProvider.GEMINI in llm.available_providers


def _openai_response(text: str = "Proxy answer") -> MagicMock:
    response = MagicMock()
    response.json.return_value = {
        "choices": [{"message": {"content": text}}],
        "usage": {"prompt_tokens": 10, "completion_tokens": 5},
    }
    response.raise_for_status = MagicMock()
    return response


class TestRequestRouting:
    @pytest.mark.asyncio
    async def test_generate_uses_openai_chat_completions(self):
        with patch.dict("os.environ", _PROXY_ENV, clear=True):
            llm = LLMService(preferred_provider=ModelProvider.GEMINI)
            client = AsyncMock()
            client.post = AsyncMock(return_value=_openai_response())
            llm._client = client

            result = await llm.generate("Test prompt", system_prompt="sys")

            assert result == "Proxy answer"
            url = client.post.call_args.args[0]
            assert url == f"{PROXY}/chat/completions"
            headers = client.post.call_args.kwargs["headers"]
            assert headers["Authorization"] == "Bearer proxy-key"
            assert "x-goog-api-key" not in headers
            body = client.post.call_args.kwargs["json"]
            assert body["model"] == "gemini-3.1-pro-low"
            assert body["messages"][0] == {"role": "system", "content": "sys"}
            assert llm.last_provider_used == "gemini"

    @pytest.mark.asyncio
    async def test_utility_tier_uses_light_model(self):
        with patch.dict("os.environ", _PROXY_ENV, clear=True):
            llm = LLMService(preferred_provider=ModelProvider.GEMINI)
            client = AsyncMock()
            client.post = AsyncMock(return_value=_openai_response())
            llm._client = client

            await llm.generate("Test prompt", tier=UTILITY_TIER)

            body = client.post.call_args.kwargs["json"]
            assert body["model"] == "gemini-3.7-flash-high"

    @pytest.mark.asyncio
    async def test_structured_output_degrades_to_json_object(self):
        """The proxy is not guaranteed to honour json_schema — same rule as Claude."""
        with patch.dict("os.environ", _PROXY_ENV, clear=True):
            llm = LLMService(preferred_provider=ModelProvider.GEMINI)
            client = AsyncMock()
            client.post = AsyncMock(return_value=_openai_response('{"a": 1}'))
            llm._client = client

            await llm.generate(
                "Test prompt",
                response_json_schema={
                    "type": "object",
                    "properties": {"a": {"type": "number"}},
                },
            )

            body = client.post.call_args.kwargs["json"]
            assert body["response_format"] == {"type": "json_object"}

    @pytest.mark.asyncio
    async def test_model_override_routes_to_the_proxy(self):
        with patch.dict("os.environ", _PROXY_ENV, clear=True):
            llm = LLMService(preferred_provider=ModelProvider.CODEX)
            client = AsyncMock()
            client.post = AsyncMock(return_value=_openai_response())
            llm._client = client

            await llm.generate("Test prompt", model_override="gemini-3.1-pro-low")

            assert client.post.call_args.args[0] == f"{PROXY}/chat/completions"
            assert llm.last_provider_used == "gemini"

    @pytest.mark.asyncio
    async def test_tool_calling_includes_the_gemini_rung(self):
        with patch.dict("os.environ", _PROXY_ENV, clear=True):
            llm = LLMService(preferred_provider=ModelProvider.GEMINI)
            candidates = llm._tool_call_candidates(None, tier=UTILITY_TIER)
            assert (ModelProvider.GEMINI, "gemini-3.7-flash-high") in candidates

    def test_tool_calling_excludes_the_native_rung(self):
        with patch.dict("os.environ", {"GEMINI_API_KEY": "paid"}, clear=True):
            llm = LLMService(preferred_provider=ModelProvider.GEMINI)
            assert llm._tool_call_candidates(None, tier=UTILITY_TIER) == []

    @pytest.mark.asyncio
    async def test_native_path_untouched_without_the_proxy(self):
        """No proxy configured → the native generateContent call, unchanged."""
        with patch.dict("os.environ", {"GEMINI_API_KEY": "paid-key"}, clear=True):
            llm = LLMService(preferred_provider=ModelProvider.GEMINI)
            response = MagicMock()
            response.json.return_value = {
                "candidates": [{"content": {"parts": [{"text": "Native answer"}]}}]
            }
            response.raise_for_status = MagicMock()
            client = AsyncMock()
            client.post = AsyncMock(return_value=response)
            llm._client = client

            result = await llm.generate("Test prompt")

            assert result == "Native answer"
            url = client.post.call_args.args[0]
            assert url.endswith(
                "/models/gemini-3.1-pro-preview:generateContent"
            ) and url.startswith("https://generativelanguage")
            assert client.post.call_args.kwargs["headers"]["x-goog-api-key"] == (
                "paid-key"
            )

    @pytest.mark.asyncio
    async def test_stream_uses_the_openai_sse_path(self):
        with patch.dict("os.environ", _PROXY_ENV, clear=True):
            llm = LLMService(preferred_provider=ModelProvider.GEMINI)

            class _Stream:
                status_code = 200

                async def aiter_lines(self):
                    yield 'data: {"choices":[{"delta":{"content":"hel"}}]}'
                    yield 'data: {"choices":[{"delta":{"content":"lo"}}]}'
                    yield "data: [DONE]"

                def raise_for_status(self):
                    return None

            stream_cm = MagicMock()
            stream_cm.__aenter__ = AsyncMock(return_value=_Stream())
            stream_cm.__aexit__ = AsyncMock(return_value=False)
            client = MagicMock()
            client.stream = MagicMock(return_value=stream_cm)
            llm._client = client

            chunks = [chunk async for chunk in llm.stream("Test prompt")]

            assert "".join(chunks) == "hello"
            assert client.stream.call_args.args[1] == f"{PROXY}/chat/completions"
