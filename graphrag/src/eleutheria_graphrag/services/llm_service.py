"""
LLM Service - Unified interface for multiple LLM providers.

Supports Gemini 3 (primary), Kimi K2.5 Thinking (extended reasoning),
and OpenRouter with automatic fallback and rate limiting.
"""

import asyncio
import logging
import os
import time
from collections import defaultdict
from collections.abc import AsyncIterator
from enum import Enum
from typing import Any

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
    ModelProvider.KIMI: {
        "base_url": "https://api.moonshot.cn/v1",
        "model": "kimi-k2.5-thinking-preview",  # Extended reasoning model
        "env_key": "MOONSHOT_API_KEY",
        "rate_limit": 20,  # requests per minute
    },
    ModelProvider.OPENROUTER: {
        "base_url": "https://openrouter.ai/api/v1",
        "model": "google/gemini-3-flash",
        "env_key": "OPENROUTER_API_KEY",
        "rate_limit": 60,
    },
    ModelProvider.GEMINI: {
        "base_url": "https://generativelanguage.googleapis.com/v1beta",
        "model": "gemini-3-flash",  # Primary model
        "env_key": "GEMINI_API_KEY",
        "rate_limit": 60,
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

        # With thinking mode (uses Kimi K2.5 Thinking for extended reasoning)
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

        # Initialize rate limiters
        if enable_rate_limiting:
            for provider in ModelProvider:
                config = PROVIDER_CONFIGS[provider]
                self._rate_limiters[provider] = RateLimiter(
                    requests_per_minute=config.get("rate_limit", 60)
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
            if os.getenv(config["env_key"]):
                available.append(provider)
                logger.info(f"LLM provider available: {provider.value}")
        return available

    def _get_provider(self, thinking_mode: bool = False) -> ModelProvider | None:
        """
        Get the best available provider.

        Args:
            thinking_mode: If True, prefer Kimi K2.5 Thinking for extended reasoning
        """
        # For thinking mode, prefer Kimi K2.5 Thinking
        if thinking_mode and ModelProvider.KIMI in self.available_providers:
            return ModelProvider.KIMI

        if self.preferred_provider in self.available_providers:
            return self.preferred_provider

        # Fallback chain: gemini -> openrouter -> kimi
        for provider in [ModelProvider.GEMINI, ModelProvider.OPENROUTER, ModelProvider.KIMI]:
            if provider in self.available_providers:
                logger.info(f"Using fallback provider: {provider.value}")
                return provider

        return None

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

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        thinking_mode: bool = False,
    ) -> str:
        """
        Generate a response (non-streaming).

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            thinking_mode: If True, use Kimi K2.5 Thinking for extended reasoning

        Returns:
            Generated text
        """
        provider = self._get_provider(thinking_mode=thinking_mode)
        if not provider:
            raise RuntimeError("No LLM provider available")

        # Apply rate limiting
        if provider in self._rate_limiters:
            await self._rate_limiters[provider].wait_if_needed()

        config = PROVIDER_CONFIGS[provider]
        api_key = os.getenv(config["env_key"])

        if provider == ModelProvider.GEMINI:
            return await self._generate_gemini(
                prompt, system_prompt, temperature, max_tokens, api_key, config
            )
        else:
            return await self._generate_openai_compatible(
                prompt, system_prompt, temperature, max_tokens, api_key, config
            )

    async def _generate_openai_compatible(
        self,
        prompt: str,
        system_prompt: str | None,
        temperature: float,
        max_tokens: int,
        api_key: str,
        config: dict[str, Any],
    ) -> str:
        """Generate using OpenAI-compatible API (Kimi, OpenRouter)."""
        client = await self._get_client()

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = await client.post(
            f"{config['base_url']}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": config["model"],
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]

    async def _generate_gemini(
        self,
        prompt: str,
        system_prompt: str | None,
        temperature: float,
        max_tokens: int,
        api_key: str,
        config: dict[str, Any],
    ) -> str:
        """Generate using Gemini API."""
        client = await self._get_client()

        contents = []
        if system_prompt:
            contents.append({"role": "user", "parts": [{"text": system_prompt}]})
            contents.append({"role": "model", "parts": [{"text": "Understood."}]})
        contents.append({"role": "user", "parts": [{"text": prompt}]})

        response = await client.post(
            f"{config['base_url']}/models/{config['model']}:generateContent",
            params={"key": api_key},
            json={
                "contents": contents,
                "generationConfig": {
                    "temperature": temperature,
                    "maxOutputTokens": max_tokens,
                },
            },
        )
        response.raise_for_status()
        data = response.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]

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
            thinking_mode: If True, use Kimi K2.5 Thinking for extended reasoning

        Yields:
            Text chunks as they're generated
        """
        provider = self._get_provider(thinking_mode=thinking_mode)
        if not provider:
            raise RuntimeError("No LLM provider available")

        # Apply rate limiting
        if provider in self._rate_limiters:
            await self._rate_limiters[provider].wait_if_needed()

        config = PROVIDER_CONFIGS[provider]
        api_key = os.getenv(config["env_key"])

        if provider == ModelProvider.GEMINI:
            async for chunk in self._stream_gemini(
                prompt, system_prompt, temperature, max_tokens, api_key, config
            ):
                yield chunk
        else:
            async for chunk in self._stream_openai_compatible(
                prompt, system_prompt, temperature, max_tokens, api_key, config
            ):
                yield chunk

    async def _stream_openai_compatible(
        self,
        prompt: str,
        system_prompt: str | None,
        temperature: float,
        max_tokens: int,
        api_key: str,
        config: dict[str, Any],
    ) -> AsyncIterator[str]:
        """Stream using OpenAI-compatible API."""
        client = await self._get_client()

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        async with client.stream(
            "POST",
            f"{config['base_url']}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": config["model"],
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
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
                        content = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
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
