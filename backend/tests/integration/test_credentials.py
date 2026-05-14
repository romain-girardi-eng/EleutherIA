"""Unit-level integration tests for CredentialsBridge.

These tests exercise the fallback and the platform-mode dispatch paths without
hitting the network. The real round-trip against a the platform Supabase test
project is a separate manual smoke test documented in
`docs/development/integration.md`.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.integrations.pragma import the platformSettings
from backend.services import credentials as creds_module
from backend.services.credentials import CredentialsBridge


def _disabled_settings() -> the platformSettings:
    return the platformSettings(
        pragma_integration=False,
        credentials_encryption_key=None,
        pragma_supabase_url=None,
        pragma_supabase_service_key=None,
    )


def _enabled_settings() -> the platformSettings:
    return the platformSettings(
        pragma_integration=True,
        credentials_encryption_key="test-encryption-key",
        pragma_supabase_url="https://pragma.example.com",
        pragma_supabase_service_key="service-role-key",
    )


@pytest.mark.asyncio
async def test_get_llm_key_falls_back_to_env_when_disabled(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "env-gemini-key")
    bridge = CredentialsBridge(settings=_disabled_settings())

    assert bridge.pragma_enabled is False
    assert await bridge.get_llm_key("gemini") == "env-gemini-key"


@pytest.mark.asyncio
async def test_get_llm_key_returns_none_when_neither_pragma_nor_env(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    bridge = CredentialsBridge(settings=_disabled_settings())

    assert await bridge.get_llm_key("gemini") is None


@pytest.mark.asyncio
async def test_get_llm_key_caches_after_first_lookup(monkeypatch):
    monkeypatch.setenv("MOONSHOT_API_KEY", "first-value")
    bridge = CredentialsBridge(settings=_disabled_settings())

    first = await bridge.get_llm_key("moonshot")
    monkeypatch.setenv("MOONSHOT_API_KEY", "second-value")
    second = await bridge.get_llm_key("moonshot")

    assert first == "first-value"
    assert second == "first-value"


@pytest.mark.asyncio
async def test_invalidate_clears_cache(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "first-value")
    bridge = CredentialsBridge(settings=_disabled_settings())

    await bridge.get_llm_key("openrouter")
    monkeypatch.setenv("OPENROUTER_API_KEY", "second-value")
    bridge.invalidate()
    refreshed = await bridge.get_llm_key("openrouter")

    assert refreshed == "second-value"


@pytest.mark.asyncio
async def test_get_llm_key_raises_when_pragma_enabled_but_eleutheria_missing(monkeypatch):
    """When credentials-provider is missing AND pragma is on, raise at first use."""
    monkeypatch.setenv("GEMINI_API_KEY", "env-fallback-key")
    monkeypatch.setattr(creds_module, "_EXTERNAL_COMMON_AVAILABLE", False)
    monkeypatch.setattr(
        creds_module, "_EXTERNAL_COMMON_IMPORT_ERROR", ImportError("credentials-provider")
    )
    bridge = CredentialsBridge(settings=_enabled_settings())

    with pytest.raises(RuntimeError, match="credentials-provider"):
        await bridge.get_llm_key("gemini")


@pytest.mark.asyncio
async def test_get_llm_key_uses_pragma_when_enabled(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "should-not-be-used")
    monkeypatch.setattr(creds_module, "_EXTERNAL_COMMON_AVAILABLE", True)

    fake_service = MagicMock()
    fake_service.get_api_key = AsyncMock(return_value="from-pragma")
    fake_service.__aenter__ = AsyncMock(return_value=fake_service)
    fake_service.__aexit__ = AsyncMock(return_value=None)

    with patch.object(
        creds_module, "CredentialsService", MagicMock(return_value=fake_service)
    ):
        bridge = CredentialsBridge(settings=_enabled_settings())
        result = await bridge.get_llm_key("gemini")

    assert result == "from-pragma"
    fake_service.get_api_key.assert_awaited_once_with(
        user_id="eleutheria-system",
        app_name="eleutheria",
        source="gemini",
    )


@pytest.mark.asyncio
async def test_get_llm_key_falls_back_to_env_if_pragma_returns_none(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "env-fallback")
    monkeypatch.setattr(creds_module, "_EXTERNAL_COMMON_AVAILABLE", True)

    fake_service = MagicMock()
    fake_service.get_api_key = AsyncMock(return_value=None)
    fake_service.__aenter__ = AsyncMock(return_value=fake_service)
    fake_service.__aexit__ = AsyncMock(return_value=None)

    with patch.object(
        creds_module, "CredentialsService", MagicMock(return_value=fake_service)
    ):
        bridge = CredentialsBridge(settings=_enabled_settings())
        result = await bridge.get_llm_key("gemini")

    assert result == "env-fallback"
