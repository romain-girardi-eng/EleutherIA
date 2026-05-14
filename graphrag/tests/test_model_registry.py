# graphrag/tests/test_model_registry.py
from eleutheria_graphrag.services.model_registry import (
    get_model,
    list_models,
)


def test_get_known_model():
    info = get_model("gemini-3.1-pro")
    assert info.provider == "gemini"
    assert info.context == 1_000_000
    assert info.api_id == "gemini-3.1-pro-preview"


def test_get_unknown_model_raises():
    import pytest

    with pytest.raises(KeyError, match="unknown-model"):
        get_model("unknown-model")


def test_list_models_returns_all():
    models = list_models()
    assert len(models) >= 4
    keys = [m.key for m in models]
    assert "gemini-3.1-pro" in keys
    assert "claude-sonnet-4.6" in keys
    assert "qwen-3.5-plus" in keys
    assert "deepseek-r1" in keys


def test_model_context_sizes():
    assert get_model("gemini-3.1-pro").context == 1_000_000
    assert get_model("claude-sonnet-4.6").context == 1_000_000
    assert get_model("qwen-3.5-plus").context == 1_000_000
    assert get_model("deepseek-r1").context == 163_840


def test_openrouter_models_have_openrouter_provider():
    for key in ["claude-sonnet-4.6", "qwen-3.5-plus", "deepseek-r1"]:
        assert get_model(key).provider == "openrouter"
