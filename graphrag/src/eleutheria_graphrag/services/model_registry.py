"""Model registry for multi-LLM routing."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ModelInfo:
    key: str
    api_id: str
    provider: str  # "gemini" | "openrouter"
    context: int
    label: str
    tier: str  # "default" | "premium" | "value" | "budget"
    pricing_input: float  # USD per 1M tokens
    pricing_output: float


_REGISTRY: dict[str, ModelInfo] = {
    "gemini-3.1-pro": ModelInfo(
        key="gemini-3.1-pro",
        api_id="gemini-3.1-pro-preview",
        provider="gemini",
        context=1_000_000,
        label="Gemini 3.1 Pro",
        tier="default",
        pricing_input=2.00,
        pricing_output=12.00,
    ),
    "claude-sonnet-4.6": ModelInfo(
        key="claude-sonnet-4.6",
        api_id="anthropic/claude-sonnet-4.6",
        provider="openrouter",
        context=1_000_000,
        label="Claude Sonnet 4.6",
        tier="premium",
        pricing_input=3.00,
        pricing_output=15.00,
    ),
    "qwen-3.5-plus": ModelInfo(
        key="qwen-3.5-plus",
        api_id="qwen/qwen3.5-plus-02-15",
        provider="openrouter",
        context=1_000_000,
        label="Qwen 3.5 Plus",
        tier="value",
        pricing_input=0.26,
        pricing_output=1.56,
    ),
    "deepseek-r1": ModelInfo(
        key="deepseek-r1",
        api_id="deepseek/deepseek-r1-0528",
        provider="openrouter",
        context=163_840,
        label="DeepSeek R1",
        tier="budget",
        pricing_input=0.45,
        pricing_output=2.15,
    ),
}

DEFAULT_MODEL = "gemini-3.1-pro"


def get_model(key: str) -> ModelInfo:
    if key not in _REGISTRY:
        raise KeyError(f"Unknown model: {key!r}. Available: {list(_REGISTRY)}")
    return _REGISTRY[key]


def list_models() -> list[ModelInfo]:
    return list(_REGISTRY.values())
