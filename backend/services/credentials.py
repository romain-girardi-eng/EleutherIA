"""CredentialsBridge — resolve LLM API keys from the environment.

Provider keys (Codex proxy / Claude proxy / Gemini) are read from environment
variables and cached in-process. Keys do not rotate often enough to need
short-TTL caching.

The Gemini rung has two backends and therefore two keys. When
``GEMINI_PROXY_BASE_URL`` is set the rung is the subscription proxy and its
bearer is ``GEMINI_PROXY_API_KEY``; the paid AI Studio ``GEMINI_API_KEY`` must
never be handed to it. The value returned here is passed to ``LLMService`` as
an explicit override, which wins over the service's own env lookup, so the
choice has to be made HERE or the paid key would silently reach the proxy.
"""

from __future__ import annotations

import os
from typing import Literal

from eleutheria_graphrag.services.llm_service import (
    GEMINI_PROXY_API_KEY_ENV,
    gemini_proxy_enabled,
)

LLMProvider = Literal["codex", "claude", "gemini"]

_GEMINI_PROXY_KEY_ENV: str = GEMINI_PROXY_API_KEY_ENV

_PROVIDER_ENV_KEYS: dict[str, str] = {
    "codex": "CODEX_PROXY_API_KEY",
    "claude": "CLAUDE_PROXY_API_KEY",
    "gemini": "GEMINI_API_KEY",
}


def _env_key_for(provider: str) -> str:
    if provider == "gemini" and gemini_proxy_enabled():
        return _GEMINI_PROXY_KEY_ENV
    return _PROVIDER_ENV_KEYS[provider]


class CredentialsBridge:
    """Resolve provider API keys from environment variables (cached)."""

    def __init__(self) -> None:
        self._cache: dict[str, str | None] = {}

    async def get_llm_key(self, provider: LLMProvider) -> str | None:
        """Return the API key for `provider`, or None if the env var is unset."""
        if provider not in self._cache:
            self._cache[provider] = os.getenv(_env_key_for(provider))
        return self._cache[provider]

    def invalidate(self, provider: LLMProvider | None = None) -> None:
        """Clear cached keys. Pass None to clear all providers."""
        if provider is None:
            self._cache.clear()
        else:
            self._cache.pop(provider, None)


_bridge: CredentialsBridge | None = None


def get_credentials_bridge() -> CredentialsBridge:
    """Return the process-wide CredentialsBridge (lazy)."""
    global _bridge
    if _bridge is None:
        _bridge = CredentialsBridge()
    return _bridge
