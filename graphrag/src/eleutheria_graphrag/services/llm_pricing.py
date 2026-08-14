"""Token usage + USD cost accounting for LLM calls.

Cost is computed per-call from the raw ``prompt_tokens`` /
``completion_tokens`` returned by the upstream provider. Prices are
expressed in USD per million tokens and can be overridden via env vars so
Romain can react to provider price changes without redeploying code:

    CODEX_PRICE_INPUT_USD_PER_M       (default 1.25)
    CODEX_PRICE_OUTPUT_USD_PER_M      (default 10.00)
    GEMINI_PRICE_INPUT_USD_PER_M      (default 1.25)
    GEMINI_PRICE_OUTPUT_USD_PER_M     (default 5.00)
    CLAUDE_PRICE_INPUT_USD_PER_M      (default 5.00)
    CLAUDE_PRICE_OUTPUT_USD_PER_M     (default 25.00)

The Codex and Claude proxies are CLI-subscription backed (no per-token
billing to us); their rows are list-price estimates so the cost rollup stays
comparable across providers.

- Gemini pricing: https://ai.google.dev/gemini-api/docs/pricing
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Final


@dataclass(frozen=True)
class ProviderPrice:
    """Per-million-token USD prices for one provider."""

    input_per_m: float
    output_per_m: float


# Pricing is keyed by PROVIDER, not by model. The two CLI-subscription proxies
# are flat-rate to us, so their rows are list-price estimates kept only so the
# cost rollup stays comparable across providers; override via the env vars.
_DEFAULTS: Final[dict[str, ProviderPrice]] = {
    "codex": ProviderPrice(input_per_m=1.25, output_per_m=10.00),
    "claude": ProviderPrice(input_per_m=5.00, output_per_m=25.00),
    "gemini": ProviderPrice(input_per_m=1.25, output_per_m=5.00),
}

_ENV_PREFIX: Final[dict[str, str]] = {
    "codex": "CODEX",
    "claude": "CLAUDE",
    "gemini": "GEMINI",
}

# Models whose list price differs from their provider's headline row, keyed by
# the model's api_id (what the provider is actually asked for). Consulted by
# :func:`get_model_price`; anything absent inherits the provider row above.
# This module is the SINGLE place any price is written down — the model
# registry derives its per-model pricing from here rather than repeating it.
_MODEL_DEFAULTS: Final[dict[str, ProviderPrice]] = {
    "claude-sonnet-4-6": ProviderPrice(input_per_m=3.00, output_per_m=15.00),
}


def _env_float(name: str, fallback: float) -> float:
    raw = os.getenv(name)
    if not raw:
        return fallback
    try:
        value = float(raw)
    except ValueError:
        return fallback
    return value if value >= 0 else fallback


def get_provider_price(provider: str) -> ProviderPrice:
    """Return current per-token price for ``provider``.

    Reads env overrides on every call — cheap and lets the operator change
    pricing without a restart.
    """
    key = provider.lower()
    default = _DEFAULTS.get(key, ProviderPrice(input_per_m=0.0, output_per_m=0.0))
    prefix = _ENV_PREFIX.get(key)
    if not prefix:
        return default
    return ProviderPrice(
        input_per_m=_env_float(f"{prefix}_PRICE_INPUT_USD_PER_M", default.input_per_m),
        output_per_m=_env_float(
            f"{prefix}_PRICE_OUTPUT_USD_PER_M", default.output_per_m
        ),
    )


def get_model_price(model_id: str, *, provider: str) -> ProviderPrice:
    """Return the list price for one concrete model.

    A model listed in :data:`_MODEL_DEFAULTS` (priced apart from its provider's
    headline row, e.g. Sonnet vs Opus) uses that row; every other model
    inherits :func:`get_provider_price`, env overrides included. Callers that
    only know the provider (per-call cost accounting) keep using
    :func:`get_provider_price`.
    """
    explicit = _MODEL_DEFAULTS.get(model_id)
    if explicit is not None:
        return explicit
    return get_provider_price(provider)


def estimate_cost_usd(
    *,
    provider: str,
    prompt_tokens: int,
    completion_tokens: int,
) -> float:
    """Return USD cost for one LLM call, rounded to 6 decimals."""
    price = get_provider_price(provider)
    cost = prompt_tokens * price.input_per_m + completion_tokens * price.output_per_m
    cost /= 1_000_000.0
    return round(max(cost, 0.0), 6)


@dataclass(frozen=True)
class TokenUsage:
    """Captured token usage + cost for a single LLM call.

    Immutable so it can be safely shared between the LLMService callback
    surface, the TraceWriter aggregator, and the SSE emitter.
    """

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    model: str
    provider: str
    estimated_cost_usd: float
    agent_id: str | None = None

    @classmethod
    def from_openai_usage(
        cls,
        usage: dict[str, object] | None,
        *,
        model: str,
        provider: str,
        agent_id: str | None = None,
    ) -> TokenUsage | None:
        """Build a TokenUsage from an OpenAI-shape ``usage`` dict.

        Returns None when the upstream omitted usage entirely (rare but
        seen on streaming responses without ``stream_options``).
        """
        if not isinstance(usage, dict):
            return None
        prompt = _coerce_int(usage.get("prompt_tokens"))
        completion = _coerce_int(usage.get("completion_tokens"))
        total = _coerce_int(usage.get("total_tokens")) or (prompt + completion)
        if prompt == 0 and completion == 0 and total == 0:
            return None
        cost = estimate_cost_usd(
            provider=provider, prompt_tokens=prompt, completion_tokens=completion
        )
        return cls(
            prompt_tokens=prompt,
            completion_tokens=completion,
            total_tokens=total,
            model=model,
            provider=provider,
            estimated_cost_usd=cost,
            agent_id=agent_id,
        )

    @classmethod
    def from_gemini_metadata(
        cls,
        metadata: dict[str, object] | None,
        *,
        model: str,
        agent_id: str | None = None,
    ) -> TokenUsage | None:
        """Build a TokenUsage from a Gemini ``usageMetadata`` block."""
        if not isinstance(metadata, dict):
            return None
        prompt = _coerce_int(metadata.get("promptTokenCount"))
        completion = _coerce_int(
            metadata.get("candidatesTokenCount") or metadata.get("responseTokenCount")
        )
        total = _coerce_int(metadata.get("totalTokenCount")) or (prompt + completion)
        if prompt == 0 and completion == 0 and total == 0:
            return None
        cost = estimate_cost_usd(
            provider="gemini",
            prompt_tokens=prompt,
            completion_tokens=completion,
        )
        return cls(
            prompt_tokens=prompt,
            completion_tokens=completion,
            total_tokens=total,
            model=model,
            provider="gemini",
            estimated_cost_usd=cost,
            agent_id=agent_id,
        )

    def to_event(self) -> dict[str, object]:
        """Serialize for the ``tokens_used`` SSE envelope."""
        return {
            "type": "tokens_used",
            "agent_id": self.agent_id or "unknown",
            "model": self.model,
            "provider": self.provider,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "estimated_cost_usd": self.estimated_cost_usd,
        }


def _coerce_int(value: object) -> int:
    if isinstance(value, bool):
        return 0
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return 0
    return 0
