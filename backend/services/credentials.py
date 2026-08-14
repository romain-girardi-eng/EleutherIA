"""CredentialsBridge — resolve LLM API keys from the environment.

Provider keys (Codex proxy / Claude proxy / Gemini) are read from environment
variables and cached in-process. Keys do not rotate often enough to need
short-TTL caching.
"""

from __future__ import annotations

import os
from typing import Literal

LLMProvider = Literal["codex", "claude", "gemini"]

_PROVIDER_ENV_KEYS: dict[str, str] = {
    "codex": "CODEX_PROXY_API_KEY",
    "claude": "CLAUDE_PROXY_API_KEY",
    "gemini": "GEMINI_API_KEY",
}


class CredentialsBridge:
    """Resolve provider API keys from environment variables (cached)."""

    def __init__(self) -> None:
        self._cache: dict[str, str | None] = {}

    async def get_llm_key(self, provider: LLMProvider) -> str | None:
        """Return the API key for `provider`, or None if the env var is unset."""
        if provider not in self._cache:
            self._cache[provider] = os.getenv(_PROVIDER_ENV_KEYS[provider])
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
