"""Model registry for multi-LLM routing.

Prices are NOT written down here: each entry derives ``pricing_input`` /
``pricing_output`` from :mod:`eleutheria_graphrag.services.llm_pricing`, which
is the single place a price is declared (and the same table the per-call cost
accounting uses). ``ModelInfo`` is built on access, so a
``*_PRICE_*_USD_PER_M`` env override is picked up without a restart.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from eleutheria_graphrag.services.llm_pricing import get_model_price
from eleutheria_graphrag.services.llm_service import (
    resolve_gemini_light_model,
    resolve_gemini_model,
)


@dataclass(frozen=True)
class ModelInfo:
    key: str
    api_id: str
    provider: str  # "codex" | "claude" | "gemini"
    context: int
    label: str
    tier: str  # "default" | "premium" | "value" | "budget"
    pricing_input: float  # USD per 1M tokens
    pricing_output: float


@dataclass(frozen=True)
class _ModelSpec:
    """Everything about a model EXCEPT its price (owned by llm_pricing)."""

    key: str
    api_id: str
    provider: str
    context: int
    label: str
    tier: str
    #: Optional resolver for the concrete API id, called at build time. Used
    #: where the deployment decides which id the provider actually serves (the
    #: Gemini rung: ``GEMINI_MODEL`` on the subscription proxy vs. the native
    #: ``-preview`` id), so the registry can never advertise an id the
    #: configured backend would reject. The user-facing ``label`` and the
    #: ``context`` window stay fixed.
    api_id_resolver: Callable[[str], str] | None = None


def _resolve_gemini_flash_model(default: str) -> str:
    """Return the deployed Gemini utility head, with a registry-safe fallback."""
    return resolve_gemini_light_model() or default


_SPECS: dict[str, _ModelSpec] = {
    "gpt-5.6-sol": _ModelSpec(
        key="gpt-5.6-sol",
        api_id="gpt-5.6-sol",
        provider="codex",
        # Measured through the production proxy: the Codex-subscription backend
        # hard-caps the effective window at ~207k tokens whatever the upstream
        # model nominally supports. 200k is the routed budget (see
        # PROVIDER_CONFIGS[CODEX]["max_input_tokens"]).
        context=200_000,
        label="GPT-5.6 Sol",
        tier="default",
    ),
    "claude-opus-5": _ModelSpec(
        key="claude-opus-5",
        api_id="claude-opus-5",
        provider="claude",
        context=1_000_000,
        label="Claude Opus 5",
        tier="premium",
    ),
    "claude-sonnet-5": _ModelSpec(
        key="claude-sonnet-5",
        api_id="claude-sonnet-5",
        provider="claude",
        context=1_000_000,
        label="Claude Sonnet 5",
        tier="value",
    ),
    "gemini-3.1-pro": _ModelSpec(
        key="gemini-3.1-pro",
        api_id="gemini-3.1-pro-preview",
        provider="gemini",
        context=1_000_000,
        label="Gemini 3.1 Pro",
        tier="budget",
        api_id_resolver=resolve_gemini_model,
    ),
    "gemini-3.7-flash-high": _ModelSpec(
        key="gemini-3.7-flash-high",
        api_id="gemini-3.7-flash-high",
        provider="gemini",
        context=1_000_000,
        label="Gemini 3.7 Flash High",
        tier="budget",
        api_id_resolver=_resolve_gemini_flash_model,
    ),
}

DEFAULT_MODEL = "gpt-5.6-sol"


def _build(spec: _ModelSpec) -> ModelInfo:
    api_id = (
        spec.api_id_resolver(spec.api_id)
        if spec.api_id_resolver is not None
        else spec.api_id
    )
    price = get_model_price(api_id, provider=spec.provider)
    return ModelInfo(
        key=spec.key,
        api_id=api_id,
        provider=spec.provider,
        context=spec.context,
        label=spec.label,
        tier=spec.tier,
        pricing_input=price.input_per_m,
        pricing_output=price.output_per_m,
    )


def get_model(key: str) -> ModelInfo:
    if key not in _SPECS:
        raise KeyError(f"Unknown model: {key!r}. Available: {list(_SPECS)}")
    return _build(_SPECS[key])


def list_models() -> list[ModelInfo]:
    return [_build(spec) for spec in _SPECS.values()]
