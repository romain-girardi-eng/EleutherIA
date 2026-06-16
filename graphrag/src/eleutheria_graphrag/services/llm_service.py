"""
LLM Service - Unified interface for multiple LLM providers.

Supports Fireworks (Kimi K2.6, primary), Gemini 3, Moonshot Kimi, and
OpenRouter with automatic fallback and rate limiting.
"""

import asyncio
import hashlib
import logging
import os
import re
import time
from collections import defaultdict
from collections.abc import AsyncIterator, Awaitable, Callable
from enum import Enum
from typing import Any, Literal, cast

import httpx

from eleutheria_graphrag.services.llm_pricing import TokenUsage

logger = logging.getLogger(__name__)


TokenUsageCallback = Callable[[TokenUsage], Awaitable[None]]


class RateLimiter:
    """Simple in-memory rate limiter with sliding window."""

    def __init__(self, requests_per_minute: int = 60) -> None:
        self.requests_per_minute = requests_per_minute
        self._requests: dict[str, list[float]] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def acquire(self, key: str = "default") -> bool:
        """Check if request is allowed and record it."""
        async with self._lock:
            now = time.time()
            window_start = now - 60

            # Clean old requests
            self._requests[key] = [
                ts for ts in self._requests[key] if ts > window_start
            ]

            # Check rate limit
            if len(self._requests[key]) >= self.requests_per_minute:
                return False

            # Record this request
            self._requests[key].append(now)
            return True

    async def wait_if_needed(self, key: str = "default") -> None:
        """Wait until a request is allowed."""
        while not await self.acquire(key):
            await asyncio.sleep(1.0)


class ModelProvider(Enum):
    """Supported LLM providers."""

    FIREWORKS = "fireworks"
    KIMI = "kimi"
    OPENROUTER = "openrouter"
    GEMINI = "gemini"


# Provider configurations
PROVIDER_CONFIGS = {
    ModelProvider.FIREWORKS: {
        "base_url": "https://api.fireworks.ai/inference/v1",
        "model": "accounts/fireworks/models/kimi-k2p7-code",
        "thinking_model": "accounts/fireworks/models/kimi-k2p7-code",
        "env_key": "FIREWORKS_API_KEY",
        "base_url_env": "FIREWORKS_BASE_URL",
        "model_env": "FIREWORKS_MODEL",
        "thinking_model_env": "FIREWORKS_THINKING_MODEL",
        "rate_limit": 60,
    },
    ModelProvider.GEMINI: {
        "base_url": "https://generativelanguage.googleapis.com/v1beta",
        "model": "gemini-3.1-pro-preview",  # Upgraded: most capable model
        "env_key": "GEMINI_API_KEY",
        "thinking_budget_env": "GEMINI_THINKING_BUDGET",
        "include_thoughts_env": "GEMINI_INCLUDE_THOUGHTS",
        "rate_limit": 30,  # Pro model has lower rate limits
    },
    ModelProvider.OPENROUTER: {
        "base_url": "https://openrouter.ai/api/v1",
        "model": "qwen/qwen3.6-plus-preview:free",  # Free tier: strong instruction-following
        "thinking_model": "qwen/qwen3.6-plus-preview:free",
        "env_key": "OPENROUTER_API_KEY",
        "base_url_env": "OPENROUTER_BASE_URL",
        "model_env": "OPENROUTER_MODEL",
        "thinking_model_env": "OPENROUTER_THINKING_MODEL",
        "provider_only_env": "OPENROUTER_PROVIDER_ONLY",
        "provider_order_env": "OPENROUTER_PROVIDER_ORDER",
        "reasoning_effort_env": "OPENROUTER_REASONING_EFFORT",
        "referer_env": "OPENROUTER_HTTP_REFERER",
        "title_env": "OPENROUTER_APP_NAME",
        "rate_limit": 60,
    },
    # KIMI = Moonshot-direct, an OPT-IN provider. Disabled by default (no key
    # configured) per Romain's Fireworks-only constraint. ONE-LINE K2.7 SWAP
    # point (ARCHITECTURE §K2.7) — do NOT apply until K2.7 is wanted on Moonshot:
    #   "model":          "kimi-k2.7-code-highspeed",   # primary synthesis
    #   "thinking_model": "kimi-k2.7-code",             # deep tier
    #   add "model_env": "MOONSHOT_MODEL", "thinking_model_env":
    #       "MOONSHOT_THINKING_MODEL" for overridability.
    # The mandatory temperature=1.0 clamp already lives in
    # _openai_compatible_payload, so the swap needs no further change there.
    ModelProvider.KIMI: {
        "base_url": "https://api.moonshot.ai/v1",
        "model": "kimi-latest",
        "thinking_model": "kimi-latest",
        "env_key": "MOONSHOT_API_KEY",
        "base_url_env": "MOONSHOT_BASE_URL",
        "rate_limit": 20,  # requests per minute
    },
}


class LLMService:
    """
    Unified LLM service with multi-provider support, fallback, and rate limiting.

    Usage:
        llm = LLMService(preferred_provider=ModelProvider.GEMINI)

        # Non-streaming
        response = await llm.generate("What is Stoic fate?")

        # Streaming
        async for chunk in llm.stream("What is Stoic fate?"):
            print(chunk, end="")

        # With thinking mode
        response = await llm.generate("Complex question", thinking_mode=True)
    """

    def __init__(
        self,
        preferred_provider: ModelProvider = ModelProvider.FIREWORKS,
        timeout: float = 120.0,
        enable_rate_limiting: bool = True,
        gemini_api_key: str | None = None,
        moonshot_api_key: str | None = None,
        openrouter_api_key: str | None = None,
        fireworks_api_key: str | None = None,
    ) -> None:
        """
        Initialize LLM service.

        Args:
            preferred_provider: Primary provider to use (default: Fireworks / Kimi K2.6)
            timeout: Request timeout in seconds
            enable_rate_limiting: Whether to enforce rate limits
            gemini_api_key: Optional Gemini key (else read from GEMINI_API_KEY)
            moonshot_api_key: Optional Moonshot/Kimi key (else MOONSHOT_API_KEY)
            openrouter_api_key: Optional OpenRouter key (else OPENROUTER_API_KEY)
            fireworks_api_key: Optional Fireworks key (else FIREWORKS_API_KEY)
        """
        self.preferred_provider = preferred_provider
        self.timeout = timeout
        self._client: httpx.AsyncClient | None = None
        self._rate_limiters: dict[ModelProvider, RateLimiter] = {}
        self.last_model_used: str = ""
        self.last_provider_used: str = ""
        # Thinking models (e.g. Fireworks deepseek-v4-pro, kimi-k2-thinking) return
        # their chain-of-thought in a SEPARATE ``reasoning_content`` field, leaving
        # ``content`` a clean finished answer. We surface that here as a side-channel
        # so callers can route it to the SSE reasoning/trace channel WITHOUT it
        # leaking into the answer. Empty for non-reasoning models (k2p6, gemini).
        # Set on every successful generate()/stream() call (reset at the start).
        self.last_reasoning_content: str = ""
        self.last_token_usage: TokenUsage | None = None
        self._token_usage_callback: TokenUsageCallback | None = None
        self._prompt_cache_names: dict[str, str] = {}
        self._prompt_cache_expiry: dict[str, float] = {}
        self._prompt_cache_backoff_until: float = 0.0
        self._disabled_providers: set[ModelProvider] = set()
        self._provider_backoff_until: dict[ModelProvider, float] = {}

        # Explicit per-provider keys take precedence over environment vars.
        self._provider_keys: dict[ModelProvider, str] = {}
        if gemini_api_key:
            self._provider_keys[ModelProvider.GEMINI] = gemini_api_key
        if moonshot_api_key:
            self._provider_keys[ModelProvider.KIMI] = moonshot_api_key
        if openrouter_api_key:
            self._provider_keys[ModelProvider.OPENROUTER] = openrouter_api_key
        if fireworks_api_key:
            self._provider_keys[ModelProvider.FIREWORKS] = fireworks_api_key

        # Initialize rate limiters
        if enable_rate_limiting:
            for provider in ModelProvider:
                config = PROVIDER_CONFIGS[provider]
                rate_limit = cast(int, config.get("rate_limit", 60))
                self._rate_limiters[provider] = RateLimiter(
                    requests_per_minute=rate_limit
                )

        # Determine available providers
        self.available_providers = self._detect_available_providers()
        if not self.available_providers:
            logger.warning("No LLM providers configured - set API keys in environment")

    def set_token_usage_callback(self, callback: TokenUsageCallback | None) -> None:
        """Register an async callback fired after every successful LLM call.

        Called with a :class:`TokenUsage` carrying prompt / completion token
        counts, provider, model, and USD cost estimate. Used by the
        :class:`TraceWriter` to aggregate running totals and stream
        ``tokens_used`` SSE events to the UI.
        """
        self._token_usage_callback = callback

    async def _emit_token_usage(self, usage: TokenUsage | None) -> None:
        """Record + forward a single TokenUsage observation, swallowing errors.

        Dispatches to two sinks (independent; both are best-effort):

        1. The per-instance callback set via ``set_token_usage_callback`` —
           used by the opencode proxy path which owns the writer directly.
        2. The active :class:`TraceWriter` exposed through the
           ``active_trace_writer`` ContextVar — used by the SSE
           ``/query/stream`` path where the writer lives in the request task
           tree rather than on the LLM service singleton.
        """
        if usage is None:
            return
        self.last_token_usage = usage

        callback = self._token_usage_callback
        if callback is not None:
            try:
                await callback(usage)
            except Exception:  # noqa: BLE001 — never fail a query because of telemetry
                logger.exception("token usage callback failed")

        # Late import keeps graphrag importable without backend on the path
        # (e.g. notebook/CLI use).
        try:
            from backend.services.trace_writer import active_trace_writer
        except Exception:  # noqa: BLE001
            return
        writer = active_trace_writer.get()
        if writer is None:
            return
        try:
            await writer.record_token_usage(agent_id=usage.agent_id, usage=usage)
        except Exception:  # noqa: BLE001
            logger.exception("active TraceWriter.record_token_usage failed")

    def _api_key_for(self, provider: ModelProvider) -> str:
        """Return the API key for ``provider``: explicit override first, env fallback."""
        explicit = self._provider_keys.get(provider)
        if explicit:
            return explicit
        config = PROVIDER_CONFIGS[provider]
        env_key = cast(str, config["env_key"])
        return os.getenv(env_key) or ""

    def _detect_available_providers(self) -> list[ModelProvider]:
        """Detect which providers have API keys configured."""
        available = []
        for provider in ModelProvider:
            if self._api_key_for(provider):
                available.append(provider)
                logger.info(f"LLM provider available: {provider.value}")
        return available

    @staticmethod
    def _resolve_config(provider: ModelProvider) -> dict[str, Any]:
        """Return provider config with environment overrides applied."""
        config = dict(PROVIDER_CONFIGS[provider])
        base_url_env = cast(str | None, config.get("base_url_env"))
        if base_url_env:
            base_url = os.getenv(base_url_env)
            if base_url:
                config["base_url"] = base_url.rstrip("/")
        model_env = cast(str | None, config.get("model_env"))
        if model_env:
            model = os.getenv(model_env)
            if model:
                config["model"] = model
        thinking_model_env = cast(str | None, config.get("thinking_model_env"))
        if thinking_model_env:
            thinking_model = os.getenv(thinking_model_env)
            if thinking_model:
                config["thinking_model"] = thinking_model
        provider_only_env = cast(str | None, config.get("provider_only_env"))
        if provider_only_env:
            provider_only = LLMService._split_csv_env(os.getenv(provider_only_env))
            if provider_only:
                config["provider_only"] = provider_only
        provider_order_env = cast(str | None, config.get("provider_order_env"))
        if provider_order_env:
            provider_order = LLMService._split_csv_env(os.getenv(provider_order_env))
            if provider_order:
                config["provider_order"] = provider_order
        reasoning_effort_env = cast(str | None, config.get("reasoning_effort_env"))
        if reasoning_effort_env:
            reasoning_effort = os.getenv(reasoning_effort_env)
            if reasoning_effort:
                config["reasoning_effort"] = reasoning_effort
        referer_env = cast(str | None, config.get("referer_env"))
        if referer_env:
            referer = os.getenv(referer_env)
            if referer:
                config["http_referer"] = referer
        title_env = cast(str | None, config.get("title_env"))
        if title_env:
            app_name = os.getenv(title_env)
            if app_name:
                config["app_name"] = app_name
        thinking_budget_env = cast(str | None, config.get("thinking_budget_env"))
        if thinking_budget_env:
            thinking_budget = os.getenv(thinking_budget_env)
            if thinking_budget not in (None, ""):
                try:
                    config["thinking_budget"] = int(thinking_budget)
                except ValueError:
                    logger.warning(
                        "Invalid %s=%s", thinking_budget_env, thinking_budget
                    )
        include_thoughts_env = cast(str | None, config.get("include_thoughts_env"))
        if include_thoughts_env:
            include_thoughts = os.getenv(include_thoughts_env)
            if include_thoughts:
                config["include_thoughts"] = include_thoughts.strip().lower() in {
                    "1",
                    "true",
                    "yes",
                }
        return config

    @staticmethod
    def _split_csv_env(value: str | None) -> list[str]:
        """Parse comma-separated environment variables."""
        if not value:
            return []
        return [item.strip() for item in value.split(",") if item.strip()]

    def _get_provider(self, thinking_mode: bool = False) -> ModelProvider | None:
        """
        Get the best available provider.

        Args:
            thinking_mode: If True, prefer the provider configured for heavier reasoning
        """
        if thinking_mode:
            thinking_provider_name = (
                os.getenv("LLM_THINKING_PROVIDER", "").strip().lower()
            )
            if thinking_provider_name:
                try:
                    thinking_provider = ModelProvider(thinking_provider_name)
                except ValueError:
                    thinking_provider = None
                if (
                    thinking_provider is not None
                    and thinking_provider in self.available_providers
                    and thinking_provider not in self._disabled_providers
                    and not self._provider_in_backoff(thinking_provider)
                ):
                    return thinking_provider

            if (
                ModelProvider.KIMI in self.available_providers
                and not self._provider_in_backoff(ModelProvider.KIMI)
            ):
                return ModelProvider.KIMI

        if (
            self.preferred_provider in self.available_providers
            and not self._provider_in_backoff(self.preferred_provider)
        ):
            return self.preferred_provider

        # Fallback chain: fireworks -> gemini -> openrouter -> kimi
        for provider in [
            ModelProvider.FIREWORKS,
            ModelProvider.GEMINI,
            ModelProvider.OPENROUTER,
            ModelProvider.KIMI,
        ]:
            if provider in self.available_providers and not self._provider_in_backoff(
                provider
            ):
                logger.info(f"Using fallback provider: {provider.value}")
                return provider

        return None

    def _provider_attempt_order(
        self, thinking_mode: bool = False
    ) -> list[ModelProvider]:
        """Return providers in the order they should be attempted."""
        preferred = self._get_provider(thinking_mode=thinking_mode)
        if preferred is None:
            return []

        if thinking_mode:
            base_order = [
                preferred,
                ModelProvider.FIREWORKS,
                ModelProvider.GEMINI,
                ModelProvider.OPENROUTER,
                ModelProvider.KIMI,
            ]
        else:
            base_order = [
                preferred,
                ModelProvider.FIREWORKS,
                ModelProvider.GEMINI,
                ModelProvider.KIMI,
                ModelProvider.OPENROUTER,
            ]

        ordered: list[ModelProvider] = []
        for provider in base_order:
            if (
                provider in self.available_providers
                and provider not in ordered
                and provider not in self._disabled_providers
                and not self._provider_in_backoff(provider)
            ):
                ordered.append(provider)
        return ordered

    def _provider_in_backoff(self, provider: ModelProvider) -> bool:
        until = self._provider_backoff_until.get(provider, 0.0)
        return time.time() < until

    @staticmethod
    def _model_for_request(
        provider: ModelProvider,
        config: dict[str, Any],
        *,
        thinking_mode: bool,
    ) -> str:
        """Return the concrete model id to use for this request."""
        if (
            provider
            in {
                ModelProvider.KIMI,
                ModelProvider.OPENROUTER,
                ModelProvider.FIREWORKS,
            }
            and thinking_mode
        ):
            thinking_model = cast(str | None, config.get("thinking_model"))
            if thinking_model:
                return thinking_model
        return cast(str, config["model"])

    @staticmethod
    def _openai_compatible_headers(
        provider: ModelProvider,
        api_key: str,
        config: dict[str, Any],
    ) -> dict[str, str]:
        """Build headers for OpenAI-compatible providers."""
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        if provider == ModelProvider.OPENROUTER:
            referer = cast(str | None, config.get("http_referer"))
            app_name = cast(str | None, config.get("app_name"))
            if referer:
                headers["HTTP-Referer"] = referer
            if app_name:
                headers["X-Title"] = app_name
        return headers

    @staticmethod
    def _openai_compatible_payload(
        provider: ModelProvider,
        prompt: str,
        system_prompt: str | None,
        temperature: float,
        max_tokens: int,
        config: dict[str, Any],
        *,
        prompt_cache_id: str | None = None,
        response_json_schema: dict[str, Any] | None = None,
        response_mime_type: str | None = None,
        schema_name: str = "structured_output",
    ) -> dict[str, Any]:
        """Build JSON payload for OpenAI-compatible providers.

        Fireworks supports a ``prompt_cache_id`` directive that caches the
        prompt prefix (system prompt + leading messages) across calls. We key
        the id on agent identity (scholar-orchestrator / concept-mapper / …)
        so the ~3-5k-token system prompt is paid for once per session, not
        once per call. See Fireworks docs: prompt caching reduces TTFT and
        per-call cost on repeated prefixes.

        When ``response_json_schema`` is provided we attach an OpenAI-style
        ``response_format={"type": "json_schema", ...}`` directive — Fireworks
        and Moonshot both honour this and constrain the model to valid JSON
        server-side. OpenRouter only guarantees ``{"type": "json_object"}``
        so we degrade gracefully there.
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload: dict[str, Any] = {
            "model": config["model"],
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        # KIMI/Moonshot 400s on any temperature other than 1.0 (mandatory clamp,
        # ARCHITECTURE §K2.7). Harmless today (KIMI/Moonshot stays opt-in,
        # disabled by default per Romain's Fireworks-only constraint); it makes
        # the K2.7-on-Moonshot swap one-line-ready without a future 400.
        if provider == ModelProvider.KIMI:
            payload["temperature"] = 1.0
        if provider == ModelProvider.FIREWORKS and prompt_cache_id:
            payload["prompt_cache_id"] = prompt_cache_id
        if provider == ModelProvider.OPENROUTER:
            provider_block: dict[str, Any] = {}
            provider_only = cast(list[str] | None, config.get("provider_only"))
            provider_order = cast(list[str] | None, config.get("provider_order"))
            if provider_only:
                provider_block["only"] = provider_only
            elif provider_order:
                provider_block["order"] = provider_order
            if provider_block:
                payload["provider"] = provider_block

            reasoning_effort = cast(str | None, config.get("reasoning_effort"))
            if reasoning_effort:
                payload["reasoning"] = {"effort": reasoning_effort}

        if response_json_schema is not None:
            if provider in (ModelProvider.FIREWORKS, ModelProvider.KIMI):
                payload["response_format"] = {
                    "type": "json_schema",
                    "json_schema": {
                        "name": schema_name,
                        "schema": response_json_schema,
                        "strict": True,
                    },
                }
            else:
                payload["response_format"] = {"type": "json_object"}
        elif response_mime_type == "application/json":
            payload["response_format"] = {"type": "json_object"}
        return payload

    @staticmethod
    def _should_retry_next_provider(exc: Exception) -> bool:
        """Whether a failure should fall through to the next provider."""
        if isinstance(
            exc,
            httpx.ConnectError
            | httpx.ReadTimeout
            | httpx.WriteError
            | httpx.RemoteProtocolError,
        ):
            return True
        if isinstance(exc, httpx.HTTPStatusError):
            status = exc.response.status_code
            return status in {401, 403, 408, 409, 425, 429, 500, 502, 503, 504}
        return False

    @staticmethod
    def _should_retry_same_provider(exc: Exception, attempt: int) -> bool:
        if attempt >= 1:
            return False
        if isinstance(
            exc,
            httpx.ConnectError
            | httpx.ReadTimeout
            | httpx.WriteError
            | httpx.RemoteProtocolError,
        ):
            return True
        if isinstance(exc, httpx.HTTPStatusError):
            return exc.response.status_code in {408, 425, 500, 502, 503, 504}
        return False

    @staticmethod
    def _retry_delay_seconds(exc: Exception) -> float:
        if isinstance(exc, httpx.HTTPStatusError):
            try:
                data = exc.response.json()
                retry_after_seconds = (
                    data.get("error", {}).get("metadata", {}).get("retry_after_seconds")
                )
                if retry_after_seconds is not None:
                    return max(1.0, float(retry_after_seconds))
            except Exception:
                pass
            retry_after = exc.response.headers.get("retry-after")
            if retry_after:
                try:
                    return max(1.0, float(retry_after))
                except ValueError:
                    pass
            text = exc.response.text or ""
            match = re.search(
                r"retry in ([0-9]+(?:\\.[0-9]+)?)s", text, flags=re.IGNORECASE
            )
            if match:
                try:
                    return max(1.0, float(match.group(1)))
                except ValueError:
                    pass
        return 5.0

    @staticmethod
    def _format_provider_error(exc: Exception) -> str:
        """Return a compact error string with HTTP status/body when available."""
        if isinstance(exc, httpx.HTTPStatusError):
            body = (exc.response.text or "").strip()
            body = re.sub(r"\s+", " ", body)
            if len(body) > 320:
                body = body[:317] + "..."
            return (
                f"{exc.response.status_code} {exc.__class__.__name__}: {body}"
                if body
                else f"{exc.response.status_code} {exc.__class__.__name__}"
            )
        return exc.__class__.__name__

    def _mark_provider_invalid(self, provider: ModelProvider, exc: Exception) -> None:
        if isinstance(exc, httpx.HTTPStatusError) and exc.response.status_code in {
            401,
            403,
        }:
            self._disabled_providers.add(provider)
            logger.warning(
                "Disabling LLM provider %s for this session after authentication failure",
                provider.value,
            )
            return
        if isinstance(exc, httpx.HTTPStatusError) and exc.response.status_code == 429:
            delay = min(max(30.0, self._retry_delay_seconds(exc)), 300.0)
            self._provider_backoff_until[provider] = time.time() + delay
            logger.warning(
                "Backing off LLM provider %s for %.1fs after rate limit",
                provider.value,
                delay,
            )

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client

    async def close(self) -> None:
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    def get_model_info(self) -> dict[str, str]:
        """Return the last-used provider and model names."""
        return {
            "provider": self.last_provider_used,
            "model": self.last_model_used,
        }

    def _cache_enabled(self) -> bool:
        """Whether Gemini provider-side prompt caching is enabled."""
        if time.time() < self._prompt_cache_backoff_until:
            return False
        return os.getenv("GEMINI_ENABLE_PROMPT_CACHE", "1").lower() not in {
            "0",
            "false",
            "no",
        }

    def _purge_expired_prompt_cache(self) -> None:
        """Drop expired cached-content handles from memory."""
        now = time.time()
        expired = [
            key for key, expiry in self._prompt_cache_expiry.items() if expiry <= now
        ]
        for key in expired:
            self._prompt_cache_names.pop(key, None)
            self._prompt_cache_expiry.pop(key, None)

    @staticmethod
    def _estimate_prompt_tokens(text: str) -> int:
        """Cheap token estimate used only to avoid invalid cache requests."""
        if not text:
            return 0
        # Gemini tokenizers vary by model; chars/4 is conservative enough to
        # skip clearly undersized prefixes without needing a full tokenizer.
        return max(1, len(text) // 4)

    @staticmethod
    def _minimum_cache_tokens(model_name: str) -> int:
        """Best-effort minimum for Gemini explicit cached contents."""
        normalized = model_name.lower()
        if "flash" in normalized:
            return 1024
        return 4096

    def _resolve_model_override(self, model_override: str) -> tuple[ModelProvider, str]:
        """Resolve a model override string to a provider and model ID.

        - ``accounts/fireworks/...`` is routed through Fireworks.
        - Other slash-containing IDs (e.g. ``anthropic/claude-sonnet-4.6``)
          go through OpenRouter.
        - Otherwise treated as a Gemini model.
        """
        if model_override.startswith("accounts/fireworks/"):
            return ModelProvider.FIREWORKS, model_override
        if "/" in model_override:
            return ModelProvider.OPENROUTER, model_override
        return ModelProvider.GEMINI, model_override

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        thinking_mode: bool = False,
        response_mime_type: str | None = None,
        response_json_schema: dict[str, Any] | None = None,
        cache_key: str | None = None,
        cache_prefix: str | None = None,
        cache_ttl_seconds: int = 900,
        model_override: str | None = None,
        agent_id: str | None = None,
        request_timeout: float | None = None,
    ) -> str:
        """
        Generate a response (non-streaming).

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            thinking_mode: If True, prefer the heavier reasoning path for the active provider
            request_timeout: Optional per-call HTTP timeout (seconds) that
                overrides the shared client timeout for THIS request only. Used
                by the Scholar-RAG dialectical synthesis (a slow thinking model
                whose generation can exceed the default 120 s client timeout).
                ``None`` keeps the client-level timeout (unchanged behaviour).

        Returns:
            Generated text
        """
        # Reset the reasoning side-channel so a non-reasoning model (or the Gemini
        # path, which never sets it) cannot surface a previous call's thinking.
        self.last_reasoning_content = ""
        # --- Model override: bypass the normal provider loop ---
        if model_override:
            override_provider, override_model = self._resolve_model_override(
                model_override
            )
            override_config = self._resolve_config(override_provider)
            override_api_key = self._api_key_for(override_provider)
            if override_api_key:
                try:
                    override_config["model"] = override_model
                    self.last_provider_used = override_provider.value
                    self.last_model_used = override_model

                    if override_provider == ModelProvider.GEMINI:
                        return await self._generate_gemini(
                            prompt,
                            system_prompt,
                            temperature,
                            max_tokens,
                            override_api_key,
                            override_config,
                            response_mime_type=response_mime_type,
                            response_json_schema=response_json_schema,
                            cache_key=cache_key,
                            cache_prefix=cache_prefix,
                            cache_ttl_seconds=cache_ttl_seconds,
                            request_timeout=request_timeout,
                        )
                    return await self._generate_openai_compatible(
                        override_provider,
                        prompt,
                        system_prompt,
                        temperature,
                        max_tokens,
                        override_api_key,
                        override_config,
                        agent_id=agent_id,
                        response_json_schema=response_json_schema,
                        response_mime_type=response_mime_type,
                        request_timeout=request_timeout,
                    )
                except Exception as exc:
                    logger.warning(
                        "Model override %s/%s failed (%s); falling back to provider loop",
                        override_provider.value,
                        override_model,
                        exc,
                    )

        providers = self._provider_attempt_order(thinking_mode=thinking_mode)
        if not providers:
            raise RuntimeError("No LLM provider available")

        last_exc: Exception | None = None
        for idx, provider in enumerate(providers):
            for attempt in range(2):
                try:
                    if provider in self._rate_limiters:
                        await self._rate_limiters[provider].wait_if_needed()

                    config = self._resolve_config(provider)
                    api_key = self._api_key_for(provider)

                    model_name = self._model_for_request(
                        provider,
                        config,
                        thinking_mode=thinking_mode,
                    )
                    request_config = dict(config)
                    request_config["model"] = model_name

                    self.last_provider_used = provider.value
                    self.last_model_used = model_name

                    if provider == ModelProvider.GEMINI:
                        return await self._generate_gemini(
                            prompt,
                            system_prompt,
                            temperature,
                            max_tokens,
                            api_key,
                            request_config,
                            response_mime_type=response_mime_type,
                            response_json_schema=response_json_schema,
                            cache_key=cache_key,
                            cache_prefix=cache_prefix,
                            cache_ttl_seconds=cache_ttl_seconds,
                            request_timeout=request_timeout,
                        )
                    return await self._generate_openai_compatible(
                        provider,
                        prompt,
                        system_prompt,
                        temperature,
                        max_tokens,
                        api_key,
                        request_config,
                        agent_id=agent_id,
                        response_json_schema=response_json_schema,
                        request_timeout=request_timeout,
                        response_mime_type=response_mime_type,
                    )
                except Exception as exc:
                    last_exc = exc
                    self._mark_provider_invalid(provider, exc)
                    if self._should_retry_same_provider(exc, attempt):
                        delay = self._retry_delay_seconds(exc)
                        logger.warning(
                            "LLM provider %s failed (%s); retrying once in %.1fs",
                            provider.value,
                            self._format_provider_error(exc),
                            delay,
                        )
                        await asyncio.sleep(delay)
                        continue
                    if idx == len(
                        providers
                    ) - 1 or not self._should_retry_next_provider(exc):
                        raise
                    logger.warning(
                        "LLM provider %s failed (%s); falling back to %s",
                        provider.value,
                        self._format_provider_error(exc),
                        providers[idx + 1].value,
                    )
                    break

        if last_exc:
            raise last_exc
        raise RuntimeError("No LLM provider available")

    async def generate_with_tools(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        *,
        tool_choice: str | dict[str, Any] = "auto",
        temperature: float = 0.1,
        max_tokens: int = 1024,
        model_override: str | None = None,
    ) -> dict[str, Any]:
        """OpenAI-style chat-completion with native tool-calling.

        Currently routes through the OpenAI-compatible providers (Fireworks /
        OpenRouter / Moonshot). Gemini is NOT supported on this path — Fireworks
        is the primary backend for tool-calling per the K2.6 spike.

        Args:
            messages: Full chat history in OpenAI format. Each message is one of
                ``{"role": "system"|"user"|"assistant"|"tool", ...}``.
                Assistant messages may carry ``tool_calls``; tool messages must
                carry ``tool_call_id`` and ``content``.
            tools: OpenAI ``[{"type": "function", "function": {...}}, ...]``.
            tool_choice: ``"auto"``, ``"none"``, ``"required"``, or
                ``{"type": "function", "function": {"name": ...}}``.
            temperature, max_tokens: standard sampling params.
            model_override: optional explicit model id.

        Returns:
            The first choice's ``message`` dict, e.g.::

                {"role": "assistant", "content": null,
                 "tool_calls": [{"id": "...", "type": "function",
                                 "function": {"name": "...",
                                              "arguments": "{...}"}}]}

            or ``{"role": "assistant", "content": "final answer text"}``.

        Raises:
            RuntimeError: when no compatible provider is available.
            httpx.HTTPStatusError: on non-2xx responses.
        """
        provider: ModelProvider
        model_name: str
        config: dict[str, Any]
        api_key: str

        if model_override:
            provider, model_name = self._resolve_model_override(model_override)
            if provider == ModelProvider.GEMINI:
                raise RuntimeError(
                    "generate_with_tools does not yet support Gemini — "
                    "pass a Fireworks or OpenRouter model_override."
                )
            config = dict(self._resolve_config(provider))
            api_key = self._api_key_for(provider)
            if not api_key:
                raise RuntimeError(f"No API key configured for {provider.value}")
            config["model"] = model_name
        else:
            # Pick the first available non-Gemini provider.
            candidates = [
                p for p in self._provider_attempt_order() if p != ModelProvider.GEMINI
            ]
            if not candidates:
                raise RuntimeError(
                    "No OpenAI-compatible provider available for tool-calling"
                )
            provider = candidates[0]
            config = dict(self._resolve_config(provider))
            api_key = self._api_key_for(provider)
            model_name = self._model_for_request(provider, config, thinking_mode=False)
            config["model"] = model_name

        self.last_provider_used = provider.value
        self.last_model_used = model_name

        if provider in self._rate_limiters:
            await self._rate_limiters[provider].wait_if_needed()

        client = await self._get_client()
        payload: dict[str, Any] = {
            "model": config["model"],
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "tools": tools,
            "tool_choice": tool_choice,
        }
        if provider == ModelProvider.OPENROUTER:
            provider_block: dict[str, Any] = {}
            provider_only = cast(list[str] | None, config.get("provider_only"))
            provider_order = cast(list[str] | None, config.get("provider_order"))
            if provider_only:
                provider_block["only"] = provider_only
            elif provider_order:
                provider_block["order"] = provider_order
            if provider_block:
                payload["provider"] = provider_block

        # Respect existing rate-limit backoff so we don't pile on after a 429.
        if self._provider_in_backoff(provider):
            wait = max(
                0.0, self._provider_backoff_until.get(provider, 0.0) - time.time()
            )
            logger.info(
                "generate_with_tools: %s in backoff for %.1fs; sleeping",
                provider.value,
                wait,
            )
            await asyncio.sleep(min(wait, 30.0))

        url = f"{config['base_url']}/chat/completions"
        headers = self._openai_compatible_headers(provider, api_key, config)
        response = await client.post(url, headers=headers, json=payload)

        # One graceful retry on 429 / 5xx to ride out short rate-limit bursts
        # (Fireworks free tier in particular). Honors Retry-After when present.
        if response.status_code in {408, 425, 429, 500, 502, 503, 504}:
            try:
                delay = self._retry_delay_seconds(
                    httpx.HTTPStatusError(
                        "transient", request=response.request, response=response
                    )
                )
            except Exception:  # pragma: no cover — defensive
                delay = 1.0
            logger.warning(
                "generate_with_tools: %s on %s, retrying once in %.1fs",
                response.status_code,
                provider.value,
                delay,
            )
            await asyncio.sleep(min(delay, 30.0))
            response = await client.post(url, headers=headers, json=payload)

        if response.status_code == 429:
            # Mark provider as in backoff so subsequent calls back off too.
            try:
                exc = httpx.HTTPStatusError(
                    "rate-limited", request=response.request, response=response
                )
                self._mark_provider_invalid(provider, exc)
            except Exception:  # pragma: no cover — defensive
                pass

        response.raise_for_status()
        data = response.json()
        try:
            message = data["choices"][0]["message"]
        except (KeyError, IndexError) as exc:  # pragma: no cover — defensive
            raise RuntimeError(
                f"Malformed response from {provider.value}: {data}"
            ) from exc
        usage = TokenUsage.from_openai_usage(
            data.get("usage") if isinstance(data, dict) else None,
            model=cast(str, config.get("model") or model_name),
            provider=provider.value,
        )
        await self._emit_token_usage(usage)
        return cast(dict[str, Any], message)

    async def _ensure_gemini_cached_content(
        self,
        *,
        api_key: str,
        config: dict[str, Any],
        cache_key: str,
        cache_prefix: str,
        system_prompt: str | None,
        ttl_seconds: int,
    ) -> str | None:
        """Create or reuse a Gemini cached-content prefix."""
        if not self._cache_enabled():
            return None

        minimum_tokens = self._minimum_cache_tokens(str(config["model"]))
        if self._estimate_prompt_tokens(cache_prefix) < minimum_tokens:
            logger.info(
                "Skipping Gemini prompt cache: prefix estimated at %s tokens, below minimum %s for %s",
                self._estimate_prompt_tokens(cache_prefix),
                minimum_tokens,
                config["model"],
            )
            return None

        self._purge_expired_prompt_cache()
        stable_key = hashlib.sha256(
            f"{config['model']}::{cache_key}::{system_prompt or ''}::{cache_prefix}".encode()
        ).hexdigest()
        cached_name = self._prompt_cache_names.get(stable_key)
        if cached_name:
            return cached_name

        client = await self._get_client()
        payload: dict[str, Any] = {
            "model": f"models/{config['model']}",
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": cache_prefix}],
                }
            ],
            "ttl": f"{ttl_seconds}s",
        }
        if system_prompt:
            payload["systemInstruction"] = {
                "parts": [{"text": system_prompt}],
            }

        try:
            response = await client.post(
                f"{config['base_url']}/cachedContents",
                params={"key": api_key},
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            name = cast(str | None, data.get("name"))
            if not name:
                return None
            self._prompt_cache_names[stable_key] = name
            self._prompt_cache_expiry[stable_key] = time.time() + ttl_seconds
            return name
        except Exception as exc:
            if (
                isinstance(exc, httpx.HTTPStatusError)
                and exc.response.status_code == 429
            ):
                self._prompt_cache_backoff_until = time.time() + 300
            logger.warning("Gemini prompt cache creation failed", exc_info=True)
            return None

    @staticmethod
    def _fireworks_cache_id(agent_id: str | None) -> str | None:
        """Compose the Fireworks prompt_cache_id from agent identity.

        Stable across calls so the cached prefix is reused. Includes a short
        version suffix so we can invalidate after a system-prompt rewrite by
        bumping ``ELEUTHERIA_PROMPT_CACHE_VERSION``.
        """
        if not agent_id:
            return None
        version = os.getenv("ELEUTHERIA_PROMPT_CACHE_VERSION", "v1")
        return f"eleutheria-{agent_id}-{version}"

    async def _generate_openai_compatible(
        self,
        provider: ModelProvider,
        prompt: str,
        system_prompt: str | None,
        temperature: float,
        max_tokens: int,
        api_key: str,
        config: dict[str, Any],
        *,
        agent_id: str | None = None,
        response_json_schema: dict[str, Any] | None = None,
        response_mime_type: str | None = None,
        schema_name: str = "structured_output",
        request_timeout: float | None = None,
    ) -> str:
        """Generate using OpenAI-compatible API (Fireworks, Kimi, OpenRouter)."""
        client = await self._get_client()

        response = await client.post(
            f"{config['base_url']}/chat/completions",
            headers=self._openai_compatible_headers(provider, api_key, config),
            json=self._openai_compatible_payload(
                provider,
                prompt,
                system_prompt,
                temperature,
                max_tokens,
                config,
                prompt_cache_id=self._fireworks_cache_id(agent_id),
                response_json_schema=response_json_schema,
                response_mime_type=response_mime_type,
                schema_name=schema_name,
            ),
            # Per-call timeout override: a slow thinking-model synthesis can run
            # well past the shared 120 s client timeout. ``None`` keeps the
            # client-level timeout (every other call site is unchanged).
            timeout=request_timeout if request_timeout is not None else self.timeout,
        )
        response.raise_for_status()
        data = response.json()
        message = data["choices"][0]["message"]
        # ``content`` is the clean finished answer. Thinking models (deepseek-v4-pro,
        # kimi-k2-thinking) additionally return their chain-of-thought in
        # ``reasoning_content`` — capture it on the side-channel ONLY (never folded
        # into the returned answer). Non-reasoning models omit the field → "".
        result: str = message.get("content") or ""
        self.last_reasoning_content = message.get("reasoning_content") or ""
        usage = TokenUsage.from_openai_usage(
            data.get("usage") if isinstance(data, dict) else None,
            model=cast(str, config.get("model") or ""),
            provider=provider.value,
            agent_id=agent_id,
        )
        await self._emit_token_usage(usage)
        return result

    async def _generate_gemini(
        self,
        prompt: str,
        system_prompt: str | None,
        temperature: float,
        max_tokens: int,
        api_key: str,
        config: dict[str, Any],
        response_mime_type: str | None = None,
        response_json_schema: dict[str, Any] | None = None,
        *,
        cache_key: str | None = None,
        cache_prefix: str | None = None,
        cache_ttl_seconds: int = 900,
        request_timeout: float | None = None,
    ) -> str:
        """Generate using Gemini API."""
        client = await self._get_client()
        post_timeout = request_timeout if request_timeout is not None else self.timeout
        cached_content = None
        if cache_key and cache_prefix:
            cached_content = await self._ensure_gemini_cached_content(
                api_key=api_key,
                config=config,
                cache_key=cache_key,
                cache_prefix=cache_prefix,
                system_prompt=system_prompt,
                ttl_seconds=cache_ttl_seconds,
            )

        body = self._build_gemini_request_body(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            cached_content=cached_content,
            config=config,
            response_mime_type=response_mime_type,
            response_json_schema=response_json_schema,
        )

        response = await client.post(
            f"{config['base_url']}/models/{config['model']}:generateContent",
            params={"key": api_key},
            json=body,
            timeout=post_timeout,
        )
        response.raise_for_status()
        data = response.json()
        result = self._extract_gemini_text(data)
        if result:
            usage = TokenUsage.from_gemini_metadata(
                data.get("usageMetadata") if isinstance(data, dict) else None,
                model=cast(str, config.get("model") or ""),
            )
            await self._emit_token_usage(usage)
            return result

        # Gemini thinking models may occasionally spend the full budget on
        # internal thought tokens and return no visible text parts. Retry once
        # with thinking disabled before surfacing an error.
        retry_prompt = (
            f"{cache_prefix}\n\n{prompt}" if cached_content and cache_prefix else prompt
        )
        retry_body = self._build_gemini_request_body(
            prompt=retry_prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max(max_tokens, 128),
            cached_content=None if cached_content and cache_prefix else cached_content,
            config=config,
            response_mime_type=response_mime_type,
            response_json_schema=response_json_schema,
        )
        retry_response = await client.post(
            f"{config['base_url']}/models/{config['model']}:generateContent",
            params={"key": api_key},
            json=retry_body,
            timeout=post_timeout,
        )
        retry_response.raise_for_status()
        retry_data = retry_response.json()
        retry_result = self._extract_gemini_text(retry_data)
        if retry_result:
            usage = TokenUsage.from_gemini_metadata(
                retry_data.get("usageMetadata")
                if isinstance(retry_data, dict)
                else None,
                model=cast(str, config.get("model") or ""),
            )
            await self._emit_token_usage(usage)
            return retry_result

        raise RuntimeError("Gemini returned no text content parts.")

    @staticmethod
    def _build_gemini_request_body(
        *,
        prompt: str,
        system_prompt: str | None,
        temperature: float,
        max_tokens: int,
        cached_content: str | None,
        config: dict[str, Any],
        response_mime_type: str | None = None,
        response_json_schema: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        contents = [{"role": "user", "parts": [{"text": prompt}]}]
        generation_config: dict[str, Any] = {
            "temperature": temperature,
            "maxOutputTokens": max_tokens,
        }
        if response_mime_type:
            generation_config["responseMimeType"] = response_mime_type
        if response_json_schema:
            generation_config["responseJsonSchema"] = response_json_schema

        thinking_budget = config.get("thinking_budget")
        include_thoughts = config.get("include_thoughts")
        if thinking_budget is not None or include_thoughts is not None:
            thinking_config: dict[str, Any] = {}
            if thinking_budget is not None:
                thinking_config["thinkingBudget"] = int(thinking_budget)
            if include_thoughts is not None:
                thinking_config["includeThoughts"] = bool(include_thoughts)
            generation_config["thinkingConfig"] = thinking_config

        body: dict[str, Any] = {
            "contents": contents,
            "generationConfig": generation_config,
        }
        if cached_content:
            body["cachedContent"] = cached_content
        elif system_prompt:
            body["systemInstruction"] = {"parts": [{"text": system_prompt}]}
        return body

    @staticmethod
    def _extract_gemini_text(data: dict[str, Any]) -> str:
        candidates = data.get("candidates") or []
        texts: list[str] = []
        fallback_texts: list[str] = []
        for candidate in candidates:
            content = candidate.get("content") or {}
            for part in content.get("parts") or []:
                text = part.get("text")
                if not text:
                    continue
                if part.get("thought"):
                    fallback_texts.append(text)
                else:
                    texts.append(text)
        if texts:
            return "\n".join(texts).strip()
        if fallback_texts:
            return "\n".join(fallback_texts).strip()
        return ""

    async def stream(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        thinking_mode: bool = False,
        model_override: str | None = None,
    ) -> AsyncIterator[str]:
        """
        Generate a streaming response.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            thinking_mode: If True, prefer the heavier reasoning path for the active provider
            model_override: Pin a specific provider/model (e.g. the user-selected
                model) instead of the default provider loop. Mirrors
                :meth:`generate`; falls back to the provider loop if the override
                fails before emitting any token.

        Yields:
            Text chunks as they're generated
        """
        # Reset the reasoning side-channel; the OpenAI-compatible stream path
        # accumulates ``reasoning_content`` deltas into it (answer chunks only are
        # yielded). Gemini streaming never sets it.
        self.last_reasoning_content = ""
        # --- Model override: bypass the normal provider loop (see generate). ---
        if model_override:
            override_provider, override_model = self._resolve_model_override(
                model_override
            )
            override_api_key = self._api_key_for(override_provider)
            if override_api_key:
                override_config = self._resolve_config(override_provider)
                override_config["model"] = override_model
                self.last_provider_used = override_provider.value
                self.last_model_used = override_model
                yielded = False
                try:
                    if override_provider == ModelProvider.GEMINI:
                        async for chunk in self._stream_gemini(
                            prompt,
                            system_prompt,
                            temperature,
                            max_tokens,
                            override_api_key,
                            override_config,
                        ):
                            yielded = True
                            yield chunk
                    else:
                        async for chunk in self._stream_openai_compatible(
                            override_provider,
                            prompt,
                            system_prompt,
                            temperature,
                            max_tokens,
                            override_api_key,
                            override_config,
                        ):
                            yielded = True
                            yield chunk
                    return
                except Exception as exc:
                    self._mark_provider_invalid(override_provider, exc)
                    # Once tokens are on the wire we can't restart cleanly.
                    if yielded:
                        raise
                    logger.warning(
                        "Streaming model override %s/%s failed (%s); "
                        "falling back to provider loop",
                        override_provider.value,
                        override_model,
                        self._format_provider_error(exc),
                    )

        providers = self._provider_attempt_order(thinking_mode=thinking_mode)
        if not providers:
            raise RuntimeError("No LLM provider available")

        last_exc: Exception | None = None
        for idx, provider in enumerate(providers):
            for attempt in range(2):
                yielded = False
                try:
                    if provider in self._rate_limiters:
                        await self._rate_limiters[provider].wait_if_needed()

                    config = self._resolve_config(provider)
                    api_key = self._api_key_for(provider)

                    model_name = self._model_for_request(
                        provider,
                        config,
                        thinking_mode=thinking_mode,
                    )
                    request_config = dict(config)
                    request_config["model"] = model_name

                    self.last_provider_used = provider.value
                    self.last_model_used = model_name

                    if provider == ModelProvider.GEMINI:
                        async for chunk in self._stream_gemini(
                            prompt,
                            system_prompt,
                            temperature,
                            max_tokens,
                            api_key,
                            request_config,
                        ):
                            yielded = True
                            yield chunk
                    else:
                        async for chunk in self._stream_openai_compatible(
                            provider,
                            prompt,
                            system_prompt,
                            temperature,
                            max_tokens,
                            api_key,
                            request_config,
                        ):
                            yielded = True
                            yield chunk
                    return
                except Exception as exc:
                    last_exc = exc
                    self._mark_provider_invalid(provider, exc)
                    if yielded:
                        raise
                    if self._should_retry_same_provider(exc, attempt):
                        delay = self._retry_delay_seconds(exc)
                        logger.warning(
                            "Streaming provider %s failed (%s); retrying once in %.1fs",
                            provider.value,
                            self._format_provider_error(exc),
                            delay,
                        )
                        await asyncio.sleep(delay)
                        continue
                    if idx == len(
                        providers
                    ) - 1 or not self._should_retry_next_provider(exc):
                        raise
                    logger.warning(
                        "Streaming provider %s failed (%s); falling back to %s",
                        provider.value,
                        self._format_provider_error(exc),
                        providers[idx + 1].value,
                    )
                    break

        if last_exc:
            raise last_exc

    async def _stream_openai_compatible(
        self,
        provider: ModelProvider,
        prompt: str,
        system_prompt: str | None,
        temperature: float,
        max_tokens: int,
        api_key: str,
        config: dict[str, Any],
    ) -> AsyncIterator[str]:
        """Stream using OpenAI-compatible API."""
        client = await self._get_client()

        async with client.stream(
            "POST",
            f"{config['base_url']}/chat/completions",
            headers=self._openai_compatible_headers(provider, api_key, config),
            json={
                **self._openai_compatible_payload(
                    provider,
                    prompt,
                    system_prompt,
                    temperature,
                    max_tokens,
                    config,
                ),
                "stream": True,
                # Ask the upstream to include a final ``usage`` chunk so we
                # can emit a tokens_used event even for streamed completions.
                "stream_options": {"include_usage": True},
            },
        ) as response:
            response.raise_for_status()
            stream_usage: dict[str, Any] | None = None
            reasoning_parts: list[str] = []
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]
                    if data == "[DONE]":
                        break
                    try:
                        import json

                        chunk = json.loads(data)
                        if isinstance(chunk, dict):
                            chunk_usage = chunk.get("usage")
                            if isinstance(chunk_usage, dict):
                                stream_usage = chunk_usage
                        # The final usage chunk (include_usage) carries an EMPTY
                        # choices list — `[][0]` would raise IndexError and abort
                        # the whole synthesis. Skip any choiceless chunk.
                        choices = chunk.get("choices") or []
                        if not choices:
                            continue
                        delta = choices[0].get("delta", {})
                        # Thinking models stream their chain-of-thought as
                        # ``reasoning_content`` deltas — accumulate them on the
                        # side-channel; NEVER yield them as answer chunks.
                        reasoning = delta.get("reasoning_content")
                        if reasoning:
                            reasoning_parts.append(reasoning)
                            self.last_reasoning_content = "".join(reasoning_parts)
                        content = delta.get("content", "")
                        if content:
                            yield content
                    except json.JSONDecodeError:
                        continue
            usage = TokenUsage.from_openai_usage(
                stream_usage,
                model=cast(str, config.get("model") or ""),
                provider=provider.value,
            )
            await self._emit_token_usage(usage)

    async def _stream_gemini(
        self,
        prompt: str,
        system_prompt: str | None,
        temperature: float,
        max_tokens: int,
        api_key: str,
        config: dict[str, Any],
    ) -> AsyncIterator[str]:
        """Stream using Gemini API."""
        client = await self._get_client()

        contents = []
        if system_prompt:
            contents.append({"role": "user", "parts": [{"text": system_prompt}]})
            contents.append({"role": "model", "parts": [{"text": "Understood."}]})
        contents.append({"role": "user", "parts": [{"text": prompt}]})

        async with client.stream(
            "POST",
            f"{config['base_url']}/models/{config['model']}:streamGenerateContent",
            params={"key": api_key, "alt": "sse"},
            json={
                "contents": contents,
                "generationConfig": {
                    "temperature": temperature,
                    "maxOutputTokens": max_tokens,
                },
            },
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    try:
                        import json

                        data = json.loads(line[6:])
                        text = (
                            data.get("candidates", [{}])[0]
                            .get("content", {})
                            .get("parts", [{}])[0]
                            .get("text", "")
                        )
                        if text:
                            yield text
                    except json.JSONDecodeError:
                        continue

    # ── Segmented stream: distinguishes reasoning deltas from answer deltas ───
    #
    # The plain ``stream()`` yields ONLY answer (``content``) deltas and folds
    # the chain-of-thought (``reasoning_content``) into the ``last_reasoning_content``
    # side-channel — so a caller can never stream the thinking LIVE. The Scholar-RAG
    # dialectical synthesis needs the reasoning deltas as they arrive (to drive the
    # right-panel AGENT REASONING workspace), kept STRICTLY apart from the answer
    # so reasoning text NEVER leaks into the answer. ``stream_segmented`` yields
    # ``("reasoning", delta)`` then ``("answer", delta)`` tuples on a single channel,
    # tagged by origin. deepseek emits reasoning deltas first, then content deltas.

    async def stream_segmented(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        model_override: str | None = None,
        request_timeout: float | None = None,
    ) -> AsyncIterator[tuple[Literal["reasoning", "answer"], str]]:
        """Stream a reasoning-model completion as TAGGED segments.

        Yields ``("reasoning", delta)`` for each ``reasoning_content`` delta and
        ``("answer", delta)`` for each ``content`` delta — the two NEVER mixed.
        ``self.last_reasoning_content`` still accumulates the full chain-of-thought
        (so the existing metadata trace continues to work). Only the
        OpenAI-compatible path (Fireworks/Moonshot/OpenRouter) emits reasoning;
        Gemini and any non-reasoning model simply yield ``("answer", …)`` deltas.

        Fireworks-only synthesis pins ``model_override`` (e.g. deepseek-v4-pro);
        ``request_timeout`` is the dedicated generous per-call HTTP timeout the
        slow thinking-model synthesis needs (mirrors :meth:`generate`). Raises on
        provider error after first token (the caller cannot restart mid-stream).
        """
        self.last_reasoning_content = ""
        provider, model = self._resolve_model_override(
            model_override or self.preferred_provider.value
        )
        api_key = self._api_key_for(provider)
        if not api_key:
            raise RuntimeError(
                f"No API key for provider {provider.value} (segmented stream)"
            )
        config = self._resolve_config(provider)
        config["model"] = model
        self.last_provider_used = provider.value
        self.last_model_used = model

        if provider == ModelProvider.GEMINI:
            async for chunk in self._stream_gemini(
                prompt, system_prompt, temperature, max_tokens, api_key, config
            ):
                yield ("answer", chunk)
            return

        async for segment in self._stream_openai_compatible_segmented(
            provider,
            prompt,
            system_prompt,
            temperature,
            max_tokens,
            api_key,
            config,
            request_timeout=request_timeout,
        ):
            yield segment

    async def _stream_openai_compatible_segmented(
        self,
        provider: ModelProvider,
        prompt: str,
        system_prompt: str | None,
        temperature: float,
        max_tokens: int,
        api_key: str,
        config: dict[str, Any],
        *,
        request_timeout: float | None = None,
    ) -> AsyncIterator[tuple[Literal["reasoning", "answer"], str]]:
        """OpenAI-compatible streaming that yields tagged reasoning/answer deltas.

        Mirrors :meth:`_stream_openai_compatible` but separates the two delta
        kinds: ``reasoning_content`` → ``("reasoning", …)`` (also accumulated on
        ``last_reasoning_content``), ``content`` → ``("answer", …)``. Honours a
        per-call ``request_timeout`` so the slow synthesis is never cut by the
        shared client timeout.
        """
        client = await self._get_client()
        post_timeout = request_timeout if request_timeout is not None else self.timeout

        async with client.stream(
            "POST",
            f"{config['base_url']}/chat/completions",
            headers=self._openai_compatible_headers(provider, api_key, config),
            json={
                **self._openai_compatible_payload(
                    provider,
                    prompt,
                    system_prompt,
                    temperature,
                    max_tokens,
                    config,
                ),
                "stream": True,
                "stream_options": {"include_usage": True},
            },
            timeout=post_timeout,
        ) as response:
            response.raise_for_status()
            stream_usage: dict[str, Any] | None = None
            reasoning_parts: list[str] = []
            async for line in response.aiter_lines():
                if not line.startswith("data: "):
                    continue
                data = line[6:]
                if data == "[DONE]":
                    break
                try:
                    import json

                    chunk = json.loads(data)
                except json.JSONDecodeError:
                    continue
                if not isinstance(chunk, dict):
                    continue
                chunk_usage = chunk.get("usage")
                if isinstance(chunk_usage, dict):
                    stream_usage = chunk_usage
                # The final usage chunk (include_usage) carries an EMPTY choices
                # list — `[][0]` would raise IndexError and abort the synthesis
                # (dropping the fully-streamed answer → fallback rung). Skip it.
                choices = chunk.get("choices") or []
                if not choices:
                    continue
                delta = choices[0].get("delta", {})
                # Reasoning deltas first (accumulate on the side-channel AND
                # surface live), then answer deltas — NEVER folded together.
                reasoning = delta.get("reasoning_content")
                if reasoning:
                    reasoning_parts.append(reasoning)
                    self.last_reasoning_content = "".join(reasoning_parts)
                    yield ("reasoning", reasoning)
                content = delta.get("content", "")
                if content:
                    yield ("answer", content)
            usage = TokenUsage.from_openai_usage(
                stream_usage,
                model=cast(str, config.get("model") or ""),
                provider=provider.value,
            )
            await self._emit_token_usage(usage)
