"""Token usage + USD cost accounting for LLM calls.

Cost is computed per-call from the raw ``prompt_tokens`` /
``completion_tokens`` returned by the upstream provider. Prices are
expressed in USD per million tokens and can be overridden via env vars so
Romain can react to provider price changes without redeploying code:

    FIREWORKS_PRICE_INPUT_USD_PER_M   (default 0.85)
    FIREWORKS_PRICE_OUTPUT_USD_PER_M  (default 3.40)
    GEMINI_PRICE_INPUT_USD_PER_M      (default 1.25)
    GEMINI_PRICE_OUTPUT_USD_PER_M     (default 5.00)
    MOONSHOT_PRICE_INPUT_USD_PER_M    (default 0.85)
    MOONSHOT_PRICE_OUTPUT_USD_PER_M   (default 3.40)
    OPENROUTER_PRICE_INPUT_USD_PER_M  (default 0.50)
    OPENROUTER_PRICE_OUTPUT_USD_PER_M (default 1.50)

Sources verified November 2026:
- Fireworks Kimi K2.6 pricing:  https://fireworks.ai/models/fireworks/kimi-k2p6
- Gemini 2.5 Pro pricing:       https://ai.google.dev/gemini-api/docs/pricing
- Moonshot Kimi-latest pricing: https://platform.moonshot.ai/docs/pricing
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


# ONE-LINE K2.7 SWAP (ARCHITECTURE §K2.7): pricing is keyed by PROVIDER, not by
# model, so a Fireworks K2.7 inherits the "fireworks" row and a Moonshot K2.7 the
# "moonshot" row — no new key is needed unless K2.7 is priced differently, in
# which case add a "kimi-k2.7" row here and route it in get_provider_price.
_DEFAULTS: Final[dict[str, ProviderPrice]] = {
    "fireworks": ProviderPrice(input_per_m=0.85, output_per_m=3.40),
    "gemini": ProviderPrice(input_per_m=1.25, output_per_m=5.00),
    "kimi": ProviderPrice(input_per_m=0.85, output_per_m=3.40),
    "moonshot": ProviderPrice(input_per_m=0.85, output_per_m=3.40),
    "openrouter": ProviderPrice(input_per_m=0.50, output_per_m=1.50),
}

_ENV_PREFIX: Final[dict[str, str]] = {
    "fireworks": "FIREWORKS",
    "gemini": "GEMINI",
    "kimi": "MOONSHOT",
    "moonshot": "MOONSHOT",
    "openrouter": "OPENROUTER",
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
