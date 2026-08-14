"""Unit tests for CredentialsBridge (environment-backed)."""

from __future__ import annotations

import pytest

from backend.services.credentials import CredentialsBridge


@pytest.mark.asyncio
async def test_get_llm_key_reads_env(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "env-gemini-key")
    bridge = CredentialsBridge()

    assert await bridge.get_llm_key("gemini") == "env-gemini-key"


@pytest.mark.asyncio
async def test_get_llm_key_returns_none_when_unset(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    bridge = CredentialsBridge()

    assert await bridge.get_llm_key("gemini") is None


@pytest.mark.asyncio
async def test_get_llm_key_caches_after_first_lookup(monkeypatch):
    monkeypatch.setenv("CODEX_PROXY_API_KEY", "first-value")
    bridge = CredentialsBridge()

    first = await bridge.get_llm_key("codex")
    monkeypatch.setenv("CODEX_PROXY_API_KEY", "second-value")
    second = await bridge.get_llm_key("codex")

    assert first == "first-value"
    assert second == "first-value"


@pytest.mark.asyncio
async def test_invalidate_clears_cache(monkeypatch):
    monkeypatch.setenv("CLAUDE_PROXY_API_KEY", "first-value")
    bridge = CredentialsBridge()

    await bridge.get_llm_key("claude")
    monkeypatch.setenv("CLAUDE_PROXY_API_KEY", "second-value")
    bridge.invalidate()
    refreshed = await bridge.get_llm_key("claude")

    assert refreshed == "second-value"
