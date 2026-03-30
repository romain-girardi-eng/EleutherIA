"""
LLM Service - Unified interface for multiple LLM providers.

Supports Gemini 3, Moonshot Kimi, and OpenRouter with automatic fallback
and rate limiting.
"""

import asyncio
import hashlib
import logging
import os
import re
import time
from collections import defaultdict
from collections.abc import AsyncIterator
from enum import Enum
from typing import Any, cast

import httpx

logger = logging.getLogger(__name__)


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

    KIMI = "kimi"
    OPENROUTER = "openrouter"
    GEMINI = "gemini"


# Provider configurations
PROVIDER_CONFIGS = {
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
        "model": "google/gemini-3-flash-preview",  # Fallback: fast model
        "thinking_model": "openai/gpt-oss-120b:nitro",
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
        preferred_provider: ModelProvider = ModelProvider.GEMINI,
        timeout: float = 120.0,
        enable_rate_limiting: bool = True,
    ) -> None:
        """
        Initialize LLM service.

        Args:
            preferred_provider: Primary provider to use (default: Gemini 3)
            timeout: Request timeout in seconds
            enable_rate_limiting: Whether to enforce rate limits
        """
        self.preferred_provider = preferred_provider
        self.timeout = timeout
        self._client: httpx.AsyncClient | None = None
        self._rate_limiters: dict[ModelProvider, RateLimiter] = {}
        self.last_model_used: str = ""
        self.last_provider_used: str = ""
        self._prompt_cache_names: dict[str, str] = {}
        self._prompt_cache_expiry: dict[str, float] = {}
        self._prompt_cache_backoff_until: float = 0.0
        self._disabled_providers: set[ModelProvider] = set()
        self._provider_backoff_until: dict[ModelProvider, float] = {}

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

    def _detect_available_providers(self) -> list[ModelProvider]:
        """Detect which providers have API keys configured."""
        available = []
        for provider in ModelProvider:
            config = PROVIDER_CONFIGS[provider]
            env_key = cast(str, config["env_key"])
            if os.getenv(env_key):
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
                    logger.warning("Invalid %s=%s", thinking_budget_env, thinking_budget)
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
            thinking_provider_name = os.getenv("LLM_THINKING_PROVIDER", "").strip().lower()
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

        # Fallback chain: gemini -> openrouter -> kimi
        for provider in [
            ModelProvider.GEMINI,
            ModelProvider.OPENROUTER,
            ModelProvider.KIMI,
        ]:
            if provider in self.available_providers and not self._provider_in_backoff(provider):
                logger.info(f"Using fallback provider: {provider.value}")
                return provider

        return None

    def _provider_attempt_order(self, thinking_mode: bool = False) -> list[ModelProvider]:
        """Return providers in the order they should be attempted."""
        preferred = self._get_provider(thinking_mode=thinking_mode)
        if preferred is None:
            return []

        if thinking_mode:
            base_order = [
                preferred,
                ModelProvider.GEMINI,
                ModelProvider.OPENROUTER,
                ModelProvider.KIMI,
            ]
        else:
            base_order = [
                preferred,
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
        if provider in {ModelProvider.KIMI, ModelProvider.OPENROUTER} and thinking_mode:
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
    ) -> dict[str, Any]:
        """Build JSON payload for OpenAI-compatible providers."""
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
        return payload

    @staticmethod
    def _should_retry_next_provider(exc: Exception) -> bool:
        """Whether a failure should fall through to the next provider."""
        if isinstance(
            exc,
            httpx.ConnectError | httpx.ReadTimeout | httpx.WriteError | httpx.RemoteProtocolError,
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
            httpx.ConnectError | httpx.ReadTimeout | httpx.WriteError | httpx.RemoteProtocolError,
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
                    data.get("error", {})
                    .get("metadata", {})
                    .get("retry_after_seconds")
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
            match = re.search(r"retry in ([0-9]+(?:\\.[0-9]+)?)s", text, flags=re.IGNORECASE)
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
            return f"{exc.response.status_code} {exc.__class__.__name__}: {body}" if body else f"{exc.response.status_code} {exc.__class__.__name__}"
        return exc.__class__.__name__

    def _mark_provider_invalid(self, provider: ModelProvider, exc: Exception) -> None:
        if isinstance(exc, httpx.HTTPStatusError) and exc.response.status_code in {401, 403}:
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

        If the string contains '/' (e.g. 'anthropic/claude-sonnet-4.6'), it is
        routed through OpenRouter.  Otherwise it is treated as a Gemini model.
        """
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
    ) -> str:
        """
        Generate a response (non-streaming).

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            thinking_mode: If True, prefer the heavier reasoning path for the active provider

        Returns:
            Generated text
        """
        # --- Model override: bypass the normal provider loop ---
        if model_override:
            override_provider, override_model = self._resolve_model_override(model_override)
            override_config = self._resolve_config(override_provider)
            override_env_key = cast(str, override_config["env_key"])
            override_api_key = os.getenv(override_env_key) or ""
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
                        )
                    return await self._generate_openai_compatible(
                        override_provider,
                        prompt,
                        system_prompt,
                        temperature,
                        max_tokens,
                        override_api_key,
                        override_config,
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
                    env_key = cast(str, config["env_key"])
                    api_key = os.getenv(env_key) or ""

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
                        )
                    return await self._generate_openai_compatible(
                        provider,
                        prompt,
                        system_prompt,
                        temperature,
                        max_tokens,
                        api_key,
                        request_config,
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
                    if idx == len(providers) - 1 or not self._should_retry_next_provider(exc):
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
            if isinstance(exc, httpx.HTTPStatusError) and exc.response.status_code == 429:
                self._prompt_cache_backoff_until = time.time() + 300
            logger.warning("Gemini prompt cache creation failed", exc_info=True)
            return None

    async def _generate_openai_compatible(
        self,
        provider: ModelProvider,
        prompt: str,
        system_prompt: str | None,
        temperature: float,
        max_tokens: int,
        api_key: str,
        config: dict[str, Any],
    ) -> str:
        """Generate using OpenAI-compatible API (Kimi, OpenRouter)."""
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
            ),
        )
        response.raise_for_status()
        data = response.json()
        result: str = data["choices"][0]["message"]["content"]
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
    ) -> str:
        """Generate using Gemini API."""
        client = await self._get_client()
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
        )
        response.raise_for_status()
        data = response.json()
        result = self._extract_gemini_text(data)
        if result:
            return result

        # Gemini thinking models may occasionally spend the full budget on
        # internal thought tokens and return no visible text parts. Retry once
        # with thinking disabled before surfacing an error.
        retry_prompt = (
            f"{cache_prefix}\n\n{prompt}"
            if cached_content and cache_prefix
            else prompt
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
        )
        retry_response.raise_for_status()
        retry_data = retry_response.json()
        retry_result = self._extract_gemini_text(retry_data)
        if retry_result:
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
    ) -> AsyncIterator[str]:
        """
        Generate a streaming response.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            thinking_mode: If True, prefer the heavier reasoning path for the active provider

        Yields:
            Text chunks as they're generated
        """
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
                    env_key = cast(str, config["env_key"])
                    api_key = os.getenv(env_key) or ""

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
                    if idx == len(providers) - 1 or not self._should_retry_next_provider(exc):
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
            },
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]
                    if data == "[DONE]":
                        break
                    try:
                        import json

                        chunk = json.loads(data)
                        content = (
                            chunk.get("choices", [{}])[0]
                            .get("delta", {})
                            .get("content", "")
                        )
                        if content:
                            yield content
                    except json.JSONDecodeError:
                        continue

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
