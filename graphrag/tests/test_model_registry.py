# graphrag/tests/test_model_registry.py
from eleutheria_graphrag.services.model_registry import (
    DEFAULT_MODEL,
    get_model,
    list_models,
)


def test_get_known_model():
    info = get_model("gpt-5.6-sol")
    assert info.provider == "codex"
    assert info.context == 200_000
    assert info.api_id == "gpt-5.6-sol"


def test_get_unknown_model_raises():
    import pytest

    with pytest.raises(KeyError, match="unknown-model"):
        get_model("unknown-model")


def test_list_models_returns_all():
    models = list_models()
    assert len(models) >= 4
    keys = [m.key for m in models]
    assert "gpt-5.6-sol" in keys
    assert "claude-opus-5" in keys
    assert "claude-sonnet-5" in keys
    assert "gemini-3.1-pro" in keys


def test_model_context_sizes():
    # The Codex subscription backend hard-caps the effective window at ~207k
    # tokens whatever the upstream model nominally supports.
    assert get_model("gpt-5.6-sol").context == 200_000
    assert get_model("claude-opus-5").context == 1_000_000
    assert get_model("claude-sonnet-5").context == 1_000_000
    assert get_model("gemini-3.1-pro").context == 1_000_000


def test_registry_only_uses_supported_providers():
    """Every registry entry must route to a live LLMService provider."""
    from eleutheria_graphrag.services.llm_service import ModelProvider

    supported = {p.value for p in ModelProvider}
    for model in list_models():
        assert model.provider in supported, model.key


def test_default_model_is_the_codex_synthesis_head():
    assert DEFAULT_MODEL == "gpt-5.6-sol"
    assert get_model(DEFAULT_MODEL).provider == "codex"


def test_pricing_comes_from_llm_pricing():
    """One place to update prices: the registry must not carry its own table."""
    from eleutheria_graphrag.services.llm_pricing import get_model_price

    for model in list_models():
        price = get_model_price(model.api_id, provider=model.provider)
        assert model.pricing_input == price.input_per_m, model.key
        assert model.pricing_output == price.output_per_m, model.key


def test_gemini_pricing_matches_the_provider_table():
    """The drifted row (2.00/12.00) is gone — llm_pricing is authoritative."""
    from eleutheria_graphrag.services.llm_pricing import get_provider_price

    price = get_provider_price("gemini")
    info = get_model("gemini-3.1-pro")
    assert (info.pricing_input, info.pricing_output) == (
        price.input_per_m,
        price.output_per_m,
    )


def test_price_env_override_reaches_the_registry(monkeypatch):
    """A price change is a single env var, not a code edit in two files."""
    monkeypatch.setenv("GEMINI_PRICE_INPUT_USD_PER_M", "7.5")
    assert get_model("gemini-3.1-pro").pricing_input == 7.5


def test_model_specific_price_beats_the_provider_row():
    """Sonnet is cheaper than Opus even though both are the claude provider."""
    sonnet = get_model("claude-sonnet-5")
    opus = get_model("claude-opus-5")
    assert sonnet.provider == opus.provider == "claude"
    assert sonnet.pricing_input < opus.pricing_input
    assert sonnet.pricing_output < opus.pricing_output


def test_model_info_shape_is_unchanged_for_the_frontend():
    info = get_model(DEFAULT_MODEL)
    assert set(info.__dataclass_fields__) == {
        "key",
        "api_id",
        "provider",
        "context",
        "label",
        "tier",
        "pricing_input",
        "pricing_output",
    }


def test_registry_api_ids_route_to_their_declared_provider():
    """A registry api_id must resolve back to the provider it claims."""
    from eleutheria_graphrag.services.llm_service import LLMService

    svc = LLMService.__new__(LLMService)
    svc.preferred_provider = None  # unused: every api_id must match a prefix
    for model in list_models():
        provider, model_id = svc._resolve_model_override(model.api_id)
        assert provider.value == model.provider, model.key
        assert model_id == model.api_id
