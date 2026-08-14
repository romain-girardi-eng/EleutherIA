from eleutheria_graphrag.services.llm_service import LLMService, ModelProvider


def _svc(preferred: ModelProvider = ModelProvider.CODEX) -> LLMService:
    svc = LLMService.__new__(LLMService)
    svc.preferred_provider = preferred
    return svc


def test_llm_service_accepts_model_override_param():
    """generate() signature accepts model_override."""
    import inspect

    sig = inspect.signature(LLMService.generate)
    assert "model_override" in sig.parameters


def test_resolve_model_override_codex():
    """``gpt-*`` ids route to the Codex proxy."""
    provider, model_id = _svc()._resolve_model_override("gpt-5.6-sol")
    assert provider == ModelProvider.CODEX
    assert model_id == "gpt-5.6-sol"


def test_resolve_model_override_claude():
    """``claude-*`` ids route to the Claude proxy."""
    provider, model_id = _svc()._resolve_model_override("claude-opus-5")
    assert provider == ModelProvider.CLAUDE
    assert model_id == "claude-opus-5"


def test_resolve_model_override_gemini():
    """``gemini-*`` ids route to Gemini direct."""
    provider, model_id = _svc()._resolve_model_override("gemini-3.1-pro-preview")
    assert provider == ModelProvider.GEMINI
    assert model_id == "gemini-3.1-pro-preview"


def test_resolve_model_override_explicit_provider_prefix():
    """``provider:model`` wins over prefix routing."""
    provider, model_id = _svc()._resolve_model_override("claude:some-custom-head")
    assert provider == ModelProvider.CLAUDE
    assert model_id == "some-custom-head"


def test_resolve_model_override_unknown_falls_back_to_preferred():
    """An unrecognised id is served by the primary proxy, not mis-routed."""
    provider, model_id = _svc(ModelProvider.CODEX)._resolve_model_override("mystery-1")
    assert provider == ModelProvider.CODEX
    assert model_id == "mystery-1"
