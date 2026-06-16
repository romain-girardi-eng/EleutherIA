"""F5 regression tests — the cache version is DERIVED, not hand-bumped.

Before F5, ``_CACHE_SCHEMA_VERSION`` was a hand-bumped constant: a prompt/logic
change that should have invalidated the cache silently replayed stale pre-fix
answers (it masked GOAL-7 grounding fixes and cost real debugging time). The
fix derives the version segment from a hash of the live synthesis prompt + an
optional build SHA, so ANY prompt change auto-invalidates the cache — while the
manual base segment stays an explicit override lever.

These tests stub the prompt fingerprint / env so they never import graphrag or
touch Postgres.
"""

from __future__ import annotations

import backend.services.answer_cache as ac
from backend.services.answer_cache import AnswerCache


def _reset_memo() -> None:
    """Clear the per-process memo on ``_effective_cache_version``."""
    if hasattr(ac._effective_cache_version, "_value"):
        delattr(ac._effective_cache_version, "_value")


def test_effective_version_includes_manual_base_and_prompt_fingerprint(
    monkeypatch,
) -> None:
    monkeypatch.setattr(ac, "_CACHE_SCHEMA_VERSION", "v3")
    monkeypatch.setattr(ac, "_synthesis_prompt_fingerprint", lambda: "deadbeef0000")
    monkeypatch.delenv(ac._BUILD_SHA_ENV, raising=False)
    _reset_memo()
    assert ac._effective_cache_version() == "v3.deadbeef0000"


def test_cache_version_changes_when_synthesis_prompt_changes(monkeypatch) -> None:
    """The core F5 guarantee: edit the prompt -> every prior cache row MISSES."""
    monkeypatch.setattr(ac, "_CACHE_SCHEMA_VERSION", "v3")
    monkeypatch.delenv(ac._BUILD_SHA_ENV, raising=False)

    monkeypatch.setattr(ac, "_synthesis_prompt_fingerprint", lambda: "aaaaaaaaaaaa")
    _reset_memo()
    key_before = AnswerCache.cache_key("q", "gemini-3.1-pro", "auto", "fast")

    # Simulate editing DIALECTICAL_SYNTHESIS_SYSTEM / _TEMPLATE: the fingerprint
    # changes, so the derived version — and the whole cache key — must change.
    monkeypatch.setattr(ac, "_synthesis_prompt_fingerprint", lambda: "bbbbbbbbbbbb")
    _reset_memo()
    key_after = AnswerCache.cache_key("q", "gemini-3.1-pro", "auto", "fast")

    assert key_before != key_after


def test_cache_version_changes_when_build_sha_changes(monkeypatch) -> None:
    """A code rollout (build SHA) that doesn't touch the prompt also invalidates."""
    monkeypatch.setattr(ac, "_CACHE_SCHEMA_VERSION", "v3")
    monkeypatch.setattr(ac, "_synthesis_prompt_fingerprint", lambda: "cccccccccccc")

    monkeypatch.setenv(ac._BUILD_SHA_ENV, "sha-one-aaaa")
    _reset_memo()
    key_one = AnswerCache.cache_key("q", "m", "auto", "fast")

    monkeypatch.setenv(ac._BUILD_SHA_ENV, "sha-two-bbbb")
    _reset_memo()
    key_two = AnswerCache.cache_key("q", "m", "auto", "fast")

    assert key_one != key_two


def test_manual_base_override_still_invalidates(monkeypatch) -> None:
    """The manual base segment remains a working override lever."""
    monkeypatch.setattr(ac, "_synthesis_prompt_fingerprint", lambda: "dddddddddddd")
    monkeypatch.delenv(ac._BUILD_SHA_ENV, raising=False)

    monkeypatch.setattr(ac, "_CACHE_SCHEMA_VERSION", "v3")
    _reset_memo()
    key_v3 = AnswerCache.cache_key("q", "m", "auto", "fast")

    monkeypatch.setattr(ac, "_CACHE_SCHEMA_VERSION", "v4")
    _reset_memo()
    key_v4 = AnswerCache.cache_key("q", "m", "auto", "fast")

    assert key_v3 != key_v4


def test_prompt_fingerprint_degrades_without_graphrag(monkeypatch) -> None:
    """Standalone (no graphrag) must not crash key derivation — stable marker."""
    import builtins

    real_import = builtins.__import__

    def _no_graphrag(name, *args, **kwargs):
        if name.startswith("eleutheria_graphrag"):
            raise ModuleNotFoundError(name)
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", _no_graphrag)
    assert ac._synthesis_prompt_fingerprint() == "noprompt"
