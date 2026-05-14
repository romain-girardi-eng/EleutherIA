"""CredentialsBridge — fetch LLM API keys from the platform's CredentialsService.

When EXTERNAL_INTEGRATION=true and the platform Supabase settings are present,
provider keys (Gemini / Moonshot / OpenRouter) are loaded from the
`provider_credentials` table via the platform's CredentialsService.

When EXTERNAL_INTEGRATION is false or the bridge is misconfigured, the
bridge falls back to plain environment variables, preserving local-dev
behaviour.

Keys are cached in-process for the lifetime of the bridge instance —
LLM keys do not rotate often enough to need short-TTL caching.

Lookup convention (the platform side):
    user_id  = "eleutheria-system"
    app_name = "eleutheria"
    source   = "gemini" | "moonshot" | "openrouter"
"""

from __future__ import annotations

import logging
import os
from typing import Literal

from backend.integrations.pragma import the platformSettings, get_pragma_settings

logger = logging.getLogger(__name__)

LLMProvider = Literal["gemini", "moonshot", "openrouter"]

ELEUTHERIA_USER_ID = "eleutheria-system"
ELEUTHERIA_APP_NAME = "eleutheria"

_PROVIDER_ENV_KEYS: dict[str, str] = {
    "gemini": "GEMINI_API_KEY",
    "moonshot": "MOONSHOT_API_KEY",
    "openrouter": "OPENROUTER_API_KEY",
}

# Try to import credentials-provider lazily. The dependency is optional in local
# dev (Phase C add). Import errors are deferred to first-use so the module
# imports cleanly without the package installed.
try:
    from credentials_provider.services.credentials_service import (  # type: ignore[import-not-found, unused-ignore]
        CredentialsService,
    )

    _EXTERNAL_COMMON_AVAILABLE = True
    _EXTERNAL_COMMON_IMPORT_ERROR: ImportError | None = None
except ImportError as exc:  # pragma: no cover - exercised on machines without the dep
    CredentialsService = None  # type: ignore[assignment, misc, unused-ignore]
    _EXTERNAL_COMMON_AVAILABLE = False
    _EXTERNAL_COMMON_IMPORT_ERROR = exc


class CredentialsBridge:
    """Resolve provider API keys from the platform or fall back to env vars."""

    def __init__(self, settings: the platformSettings | None = None) -> None:
        self._settings = settings or get_pragma_settings()
        self._cache: dict[str, str | None] = {}

    @property
    def pragma_enabled(self) -> bool:
        """True iff the platform integration is configured end-to-end."""
        s = self._settings
        return bool(
            s.pragma_integration
            and s.pragma_supabase_url
            and s.pragma_supabase_service_key
        )

    async def get_llm_key(self, provider: LLMProvider) -> str | None:
        """Return the API key for `provider`, or None if unavailable.

        the platform-mode lookup happens once per provider per process; subsequent
        calls hit an in-memory cache.
        """
        if provider in self._cache:
            return self._cache[provider]

        key: str | None
        if self.pragma_enabled:
            key = await self._fetch_from_pragma(provider)
            if key is None:
                # Fall back to env if the platform has no entry for this provider.
                key = os.getenv(_PROVIDER_ENV_KEYS[provider])
        else:
            key = os.getenv(_PROVIDER_ENV_KEYS[provider])

        self._cache[provider] = key
        return key

    async def _fetch_from_pragma(self, provider: LLMProvider) -> str | None:
        if not _EXTERNAL_COMMON_AVAILABLE:
            raise RuntimeError(
                "EXTERNAL_INTEGRATION=true but credentials-provider is not installed. "
                "Install via `pip install 'credentials-provider @ git+ssh://"
                "git@private-org/private-repo.git"
                "#subdirectory=modules/shared/credentials-provider'`."
            ) from _EXTERNAL_COMMON_IMPORT_ERROR

        s = self._settings
        assert s.pragma_supabase_url and s.pragma_supabase_service_key

        try:
            async with CredentialsService(  # type: ignore[misc, unused-ignore]
                supabase_url=s.pragma_supabase_url,
                supabase_key=s.pragma_supabase_service_key,
                encryption_key=s.credentials_encryption_key,
            ) as creds:
                api_key: str | None = await creds.get_api_key(
                    user_id=ELEUTHERIA_USER_ID,
                    app_name=ELEUTHERIA_APP_NAME,
                    source=provider,
                )
                return api_key
        except Exception:
            logger.exception(
                "CredentialsService lookup failed for provider=%s", provider
            )
            return None

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
