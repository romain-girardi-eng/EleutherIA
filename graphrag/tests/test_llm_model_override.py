import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from eleutheria_graphrag.services.llm_service import LLMService, ModelProvider


def test_llm_service_accepts_model_override_param():
    """generate() signature accepts model_override."""
    import inspect
    sig = inspect.signature(LLMService.generate)
    assert "model_override" in sig.parameters


def test_resolve_model_override_openrouter():
    """OpenRouter models contain '/'."""
    svc = LLMService.__new__(LLMService)
    provider, model_id = svc._resolve_model_override("anthropic/claude-sonnet-4.6")
    assert provider == ModelProvider.OPENROUTER
    assert model_id == "anthropic/claude-sonnet-4.6"


def test_resolve_model_override_gemini():
    """Gemini models don't contain '/'."""
    svc = LLMService.__new__(LLMService)
    provider, model_id = svc._resolve_model_override("gemini-3.1-pro-preview")
    assert provider == ModelProvider.GEMINI
    assert model_id == "gemini-3.1-pro-preview"
