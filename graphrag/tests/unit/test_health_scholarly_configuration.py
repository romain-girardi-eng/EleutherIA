"""The health payload makes the effective scholarly cutover observable (C-02)."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from eleutheria_graphrag.api import routes

SCHOLARLY_ENV_KEYS = {
    "ELEUTHERIA_SCHOLAR_RAG",
    "ELEUTHERIA_REFEREE",
    "ELEUTHERIA_RELEVANCE_TRIAGE",
    "SCHOLAR_SYNTHESIS_MODEL",
    "SCHOLAR_SYNTHESIS_REASONING_EFFORT",
    "ELEUTHERIA_SCHOLAR_MAX_TOOL_CALLS",
    "ELEUTHERIA_SCHOLAR_SYNTHESIS_TIMEOUT",
    "ELEUTHERIA_SCHOLAR_RENDER_MAX_TOKENS",
    "ELEUTHERIA_SCHOLAR_CONTESTED_BUDGET",
    "ELEUTHERIA_TRIAGE_MODEL",
    "ELEUTHERIA_TRIAGE_TIMEOUT",
    "ELEUTHERIA_TRIAGE_MAX_ITEMS",
    "ELEUTHERIA_REFEREE_TIMEOUT",
    "ELEUTHERIA_REVISION_TIMEOUT",
    "ELEUTHERIA_REFEREE_MAP_TOKENS",
    "ELEUTHERIA_SYNTH_CONTEXT_TOKENS",
    "ELEUTHERIA_SYNTH_CONTEXT_TOKENS_QUICK",
    "ELEUTHERIA_SYNTH_CONTEXT_TOKENS_STANDARD",
}


@pytest.mark.asyncio
async def test_health_reports_default_off_scholarly_features(monkeypatch) -> None:
    for name in (
        "ELEUTHERIA_SCHOLAR_RAG",
        "ELEUTHERIA_REFEREE",
        "ELEUTHERIA_RELEVANCE_TRIAGE",
        "SCHOLAR_SYNTHESIS_MODEL",
    ):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr(routes, "_graphrag", None)

    payload = await routes.health()
    assert payload["status"] == "not_initialized"
    assert payload["scholarly_configuration"] == {
        "scholar_rag": False,
        "referee": False,
        "relevance_triage": False,
        "synthesis_model": "gpt-5.6-sol",
    }


@pytest.mark.asyncio
async def test_health_reports_effective_on_state_and_model(monkeypatch) -> None:
    monkeypatch.setenv("ELEUTHERIA_SCHOLAR_RAG", "true")
    monkeypatch.setenv("ELEUTHERIA_REFEREE", "1")
    monkeypatch.setenv("ELEUTHERIA_RELEVANCE_TRIAGE", "yes")
    monkeypatch.setenv("SCHOLAR_SYNTHESIS_MODEL", "claude-opus-5")
    monkeypatch.setattr(
        routes,
        "_graphrag",
        SimpleNamespace(_kg_loaded=True, node_lookup={"n": {}}),
    )

    payload = await routes.health()
    assert payload["status"] == "healthy"
    assert payload["nodes_count"] == 1
    assert payload["scholarly_configuration"] == {
        "scholar_rag": True,
        "referee": True,
        "relevance_triage": True,
        "synthesis_model": "claude-opus-5",
    }


def test_scholarly_runtime_keys_are_reproducible_in_examples_and_docs() -> None:
    root = Path(__file__).parents[3]
    paths = (
        root / ".env.example",
        root / "deploy" / "production" / ".env.example",
        root / "docs" / "development" / "scholarly-runtime-configuration.md",
    )
    for path in paths:
        text = path.read_text(encoding="utf-8")
        missing = {key for key in SCHOLARLY_ENV_KEYS if key not in text}
        assert not missing, f"{path}: undocumented scholarly keys: {sorted(missing)}"
