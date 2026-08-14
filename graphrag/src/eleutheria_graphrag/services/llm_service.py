"""
LLM Service - Unified interface for multiple LLM providers.

Provider chain (all OpenAI-compatible except Gemini):

1. **Codex proxy** (primary) — CLI-subscription proxy exposing
   ``/v1/chat/completions``; supports ``reasoning_effort``, native tool
   calling and SSE streaming.
2. **Claude proxy** (fallback) — same OpenAI-compatible shape.
3. **Gemini direct** (last resort) — the native ``generativelanguage`` API.

Each call picks a *tier*: ``"synthesis"`` (full academic quality — dialectical
synthesis, the final scholarly answer, the ReAct tool-calling loop) or
``"utility"`` (cheap internal subtasks — lemma expansion, planning, query
classification, citation verification). The tier selects the concrete model id
per provider so model ids are never scattered across call sites.
"""

import asyncio
import contextlib
import hashlib
import logging
import os
import re
import time
from collections import defaultdict
from collections.abc import AsyncIterator, Awaitable, Callable
from enum import Enum
from typing import Any, Literal, cast

import httpx

from eleutheria_graphrag.services.llm_pricing import TokenUsage

logger = logging.getLogger(__name__)


TokenUsageCallback = Callable[[TokenUsage], Awaitable[None]]

#: Model tier. ``"synthesis"`` = full academic quality, ``"utility"`` = cheap
#: internal subtask. Selects the concrete model id per provider.
ModelTier = Literal["synthesis", "utility"]

SYNTHESIS_TIER: ModelTier = "synthesis"
UTILITY_TIER: ModelTier = "utility"

#: What the BROWSER is told when a provider call fails. A raw provider
#: exception string can carry credentials (httpx embeds the request URL in the
#: message) and provider internals, and this text is streamed to the client AND
#: persisted; the real detail goes to the server log only. Single wording,
#: shared by the agents (scholarly_agent, react_loop) and the API routes.
CLIENT_LLM_ERROR_MESSAGE = (
    "A language-model provider was unavailable while answering. Please retry."
)

#: Codex synthesis-tier answer-budget floor (failure-map F4). With
#: ``CODEX_REASONING_EFFORT=high`` gpt-5.6-sol's reasoning tokens count against
#: ``max_tokens``, so a synthesis call capped at 9k-14k can end with
#: ``finish_reason=length`` and an EMPTY ``content``. Synthesis-tier Codex
#: payloads therefore never go out below this floor; a caller asking for MORE
#: keeps its own larger value.
CODEX_SYNTHESIS_MAX_TOKENS_ENV = "CODEX_SYNTHESIS_MAX_TOKENS"
CODEX_SYNTHESIS_MAX_TOKENS_DEFAULT = 32000


# Query-string secrets (Gemini historically took ``?key=``) end up inside
# httpx.HTTPStatusError messages, which are logged, streamed over SSE and
# persisted in query_traces. Everything that renders a provider error must go
# through _redact_secrets first.
_SECRET_QUERY_RE = re.compile(
    r"(?i)([?&])(key|api_key|apikey|access_token|token)=[^&\s\"'>]+"
)
_BEARER_RE = re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._\-]{8,}")


def _redact_secrets(message: str) -> str:
    """Strip API keys out of a message before it is logged or surfaced."""
    if not message:
        return message
    redacted = _SECRET_QUERY_RE.sub(r"\1\2=REDACTED", message)
    return _BEARER_RE.sub("Bearer REDACTED", redacted)


class RateLimiter:
    """Simple in-memory rate limiter with sliding window."""

    def __init__(self, requests_per_minute: int = 60) -> None:
        self.requests_per_minute = requests_per_minute
        self._requests: dict[str, list[float]] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def acquire(self, key: str = "default") -> bool:
        """Check if request is allowed and record it."""
        async with self._lock:
            now = time.time()
            window_start = now - 60

            # Clean old requests
            self._requests[key] = [
                ts for ts in self._requests[key] if ts > window_start
            ]

            # Check rate limit
            if len(self._requests[key]) >= self.requests_per_minute:
                return False

            # Record this request
            self._requests[key].append(now)
            return True

    async def wait_if_needed(self, key: str = "default") -> None:
        """Wait until a request is allowed."""
        while not await self.acquire(key):
            await asyncio.sleep(1.0)


class ModelProvider(Enum):
    """Supported LLM providers, in fallback order."""

    CODEX = "codex"
    CLAUDE = "claude"
    GEMINI = "gemini"


#: Providers speaking the OpenAI ``/chat/completions`` dialect (everything but
#: Gemini, which uses the native generativelanguage API).
OPENAI_COMPATIBLE_PROVIDERS = frozenset({ModelProvider.CODEX, ModelProvider.CLAUDE})

#: The canonical provider fallback order: Codex proxy → Claude proxy → Gemini.
PROVIDER_FALLBACK_ORDER: tuple[ModelProvider, ...] = (
    ModelProvider.CODEX,
    ModelProvider.CLAUDE,
    ModelProvider.GEMINI,
)


# Provider configurations.
#
# ``model``       — the synthesis-tier model (full academic quality).
# ``light_model`` — the utility-tier model (cheap internal subtasks).
PROVIDER_CONFIGS = {
    ModelProvider.CODEX: {
        # OpenAI-compatible CLI-subscription proxy on the prod docker network.
        "base_url": "http://cli-proxy-api:8317/v1",
        "model": "gpt-5.6-sol",
        "light_model": "gpt-5.4-mini",
        "env_key": "CODEX_PROXY_API_KEY",
        "base_url_env": "CODEX_PROXY_BASE_URL",
        "model_env": "CODEX_MODEL",
        "light_model_env": "CODEX_LIGHT_MODEL",
        "reasoning_effort_env": "CODEX_REASONING_EFFORT",
        "reasoning_effort": "high",
        "light_reasoning_effort": "low",
        "rate_limit": 60,
    },
    ModelProvider.CLAUDE: {
        # Same OpenAI-compatible shape, second CLI-subscription proxy.
        "base_url": "http://pragma-claude-proxy:8318/v1",
        "model": "claude-opus-5",
        "light_model": "claude-sonnet-4-6",
        "env_key": "CLAUDE_PROXY_API_KEY",
        "base_url_env": "CLAUDE_PROXY_BASE_URL",
        "model_env": "CLAUDE_PROXY_MODEL",
        "light_model_env": "CLAUDE_PROXY_LIGHT_MODEL",
        "rate_limit": 60,
    },
    ModelProvider.GEMINI: {
        "base_url": "https://generativelanguage.googleapis.com/v1beta",
        "model": "gemini-3.1-pro-preview",
        # Utility tier only when a flash model is explicitly configured;
        # otherwise the pro model serves both tiers.
        "light_model_env": "GEMINI_LIGHT_MODEL",
        "env_key": "GEMINI_API_KEY",
        "model_env": "GEMINI_MODEL",
        "thinking_budget_env": "GEMINI_THINKING_BUDGET",
        "include_thoughts_env": "GEMINI_INCLUDE_THOUGHTS",
        "rate_limit": 30,  # Pro model has lower rate limits
    },
}


#: Model-id prefix → provider, used to route a bare ``model_override``.
_MODEL_PREFIX_PROVIDERS: tuple[tuple[str, ModelProvider], ...] = (
    ("gpt-", ModelProvider.CODEX),
    ("codex", ModelProvider.CODEX),
    ("o3", ModelProvider.CODEX),
    ("o4", ModelProvider.CODEX),
    ("claude", ModelProvider.CLAUDE),
    ("gemini", ModelProvider.GEMINI),
)


class LLMService:
    """
    Unified LLM service with multi-provider support, fallback, and rate limiting.

    Usage:
        llm = LLMService(preferred_provider=ModelProvider.GEMINI)

        # Non-streaming
        response = await llm.generate("What is Stoic fate?")

        # Streaming
        async for chunk in llm.stream("What is Stoic fate?"):
            print(chunk, end="")

        # With thinking mode
        response = await llm.generate("Complex question", thinking_mode=True)
    """

    def __init__(
        self,
        preferred_provider: ModelProvider = ModelProvider.CODEX,
        timeout: float = 120.0,
        enable_rate_limiting: bool = True,
        gemini_api_key: str | None = None,
        codex_api_key: str | None = None,
        claude_api_key: str | None = None,
    ) -> None:
        """
        Initialize LLM service.

        Args:
            preferred_provider: Primary provider to use (default: Codex proxy)
            timeout: Request timeout in seconds
            enable_rate_limiting: Whether to enforce rate limits
            gemini_api_key: Optional Gemini key (else read from GEMINI_API_KEY)
            codex_api_key: Optional Codex-proxy key (else CODEX_PROXY_API_KEY)
            claude_api_key: Optional Claude-proxy key (else CLAUDE_PROXY_API_KEY)
        """
        self.preferred_provider = preferred_provider
        self.timeout = timeout
        self._client: httpx.AsyncClient | None = None
        self._rate_limiters: dict[ModelProvider, RateLimiter] = {}
        self.last_model_used: str = ""
        self.last_provider_used: str = ""
        # Thinking models (e.g. Fireworks deepseek-v4-pro, kimi-k2-thinking) return
        # their chain-of-thought in a SEPARATE ``reasoning_content`` field, leaving
        # ``content`` a clean finished answer. We surface that here as a side-channel
        # so callers can route it to the SSE reasoning/trace channel WITHOUT it
        # leaking into the answer. Empty for non-reasoning models (k2p6, gemini).
        # Set on every successful generate()/stream() call (reset at the start).
        self.last_reasoning_content: str = ""
        # The OpenAI ``finish_reason`` of the most recent stream: ``"stop"`` (the
        # model finished its answer), ``"length"`` (max_tokens hit — for a thinking
        # model whose reasoning_content shares the budget this is the empty-content
        # signature: the budget was eaten by reasoning before any answer delta), or
        # "" (never set / non-streaming). Read by the synthesis robustness path to
        # detect "length-truncated while reasoning" and trigger targeted recovery.
        self.last_finish_reason: str = ""
        self.last_token_usage: TokenUsage | None = None
        self._token_usage_callback: TokenUsageCallback | None = None
        self._prompt_cache_names: dict[str, str] = {}
        self._prompt_cache_expiry: dict[str, float] = {}
        self._prompt_cache_backoff_until: float = 0.0
        self._disabled_providers: set[ModelProvider] = set()
        self._provider_backoff_until: dict[ModelProvider, float] = {}

        # Explicit per-provider keys take precedence over environment vars.
        self._provider_keys: dict[ModelProvider, str] = {}
        if gemini_api_key:
            self._provider_keys[ModelProvider.GEMINI] = gemini_api_key
        if codex_api_key:
            self._provider_keys[ModelProvider.CODEX] = codex_api_key
        if claude_api_key:
            self._provider_keys[ModelProvider.CLAUDE] = claude_api_key

        # Initialize rate limiters
        if enable_rate_limiting:
            for provider in ModelProvider:
                config = PROVIDER_CONFIGS[provider]
                rate_limit = cast(int, config.get("rate_limit", 60))
                self._rate_limiters[provider] = RateLimiter(
                    requests_per_minute=rate_limit
                )

        # Determine available providers
        self.available_providers = self._detect_available_providers()
        if not self.available_providers:
            logger.warning("No LLM providers configured - set API keys in environment")

    def set_token_usage_callback(self, callback: TokenUsageCallback | None) -> None:
        """Register an async callback fired after every successful LLM call.

        Called with a :class:`TokenUsage` carrying prompt / completion token
        counts, provider, model, and USD cost estimate. Used by the
        :class:`TraceWriter` to aggregate running totals and stream
        ``tokens_used`` SSE events to the UI.
        """
        self._token_usage_callback = callback

    async def _emit_token_usage(self, usage: TokenUsage | None) -> None:
        """Record + forward a single TokenUsage observation, swallowing errors.

        Dispatches to two sinks (independent; both are best-effort):

        1. The per-instance callback set via ``set_token_usage_callback`` —
           used by the opencode proxy path which owns the writer directly.
        2. The active :class:`TraceWriter` exposed through the
           ``active_trace_writer`` ContextVar — used by the SSE
           ``/query/stream`` path where the writer lives in the request task
           tree rather than on the LLM service singleton.
        """
        if usage is None:
            return
        self.last_token_usage = usage

        callback = self._token_usage_callback
        if callback is not None:
            try:
                await callback(usage)
            except Exception:  # noqa: BLE001 — never fail a query because of telemetry
                logger.exception("token usage callback failed")

        # Late import keeps graphrag importable without backend on the path
        # (e.g. notebook/CLI use).
        try:
            from backend.services.trace_writer import active_trace_writer
        except Exception:  # noqa: BLE001
            return
        writer = active_trace_writer.get()
        if writer is None:
            return
        try:
            await writer.record_token_usage(agent_id=usage.agent_id, usage=usage)
        except Exception:  # noqa: BLE001
            logger.exception("active TraceWriter.record_token_usage failed")

    def _api_key_for(self, provider: ModelProvider) -> str:
        """Return the API key for ``provider``: explicit override first, env fallback."""
        explicit = self._provider_keys.get(provider)
        if explicit:
            return explicit
        config = PROVIDER_CONFIGS[provider]
        env_key = cast(str, config["env_key"])
        return os.getenv(env_key) or ""

    def _detect_available_providers(self) -> list[ModelProvider]:
        """Detect which providers have API keys configured."""
        available = []
        for provider in ModelProvider:
            if self._api_key_for(provider):
                available.append(provider)
                logger.info(f"LLM provider available: {provider.value}")
        return available

    @staticmethod
    def _resolve_config(provider: ModelProvider) -> dict[str, Any]:
        """Return provider config with environment overrides applied."""
        config = dict(PROVIDER_CONFIGS[provider])
        base_url_env = cast(str | None, config.get("base_url_env"))
        if base_url_env:
            base_url = os.getenv(base_url_env)
            if base_url:
                config["base_url"] = base_url.rstrip("/")
        model_env = cast(str | None, config.get("model_env"))
        if model_env:
            model = os.getenv(model_env)
            if model:
                config["model"] = model
        light_model_env = cast(str | None, config.get("light_model_env"))
        if light_model_env:
            light_model = os.getenv(light_model_env)
            if light_model:
                config["light_model"] = light_model
        reasoning_effort_env = cast(str | None, config.get("reasoning_effort_env"))
        if reasoning_effort_env:
            reasoning_effort = os.getenv(reasoning_effort_env)
            if reasoning_effort:
                config["reasoning_effort"] = reasoning_effort
        thinking_budget_env = cast(str | None, config.get("thinking_budget_env"))
        if thinking_budget_env:
            thinking_budget = os.getenv(thinking_budget_env)
            if thinking_budget not in (None, ""):
                try:
                    config["thinking_budget"] = int(thinking_budget)
                except ValueError:
                    logger.warning(
                        "Invalid %s=%s", thinking_budget_env, thinking_budget
                    )
        include_thoughts_env = cast(str | None, config.get("include_thoughts_env"))
        if include_thoughts_env:
            include_thoughts = os.getenv(include_thoughts_env)
            if include_thoughts:
                config["include_thoughts"] = include_thoughts.strip().lower() in {
                    "1",
                    "true",
                    "yes",
                }
        return config

    @staticmethod
    def _split_csv_env(value: str | None) -> list[str]:
        """Parse comma-separated environment variables."""
        if not value:
            return []
        return [item.strip() for item in value.split(",") if item.strip()]

    def _get_provider(self, thinking_mode: bool = False) -> ModelProvider | None:
        """
        Get the best available provider.

        Args:
            thinking_mode: If True, honour ``LLM_THINKING_PROVIDER`` before the
                normal preference (all three providers are reasoning-capable,
                so this is now only an operator escape hatch).
        """
        if thinking_mode:
            thinking_provider_name = (
                os.getenv("LLM_THINKING_PROVIDER", "").strip().lower()
            )
            if thinking_provider_name:
                try:
                    thinking_provider = ModelProvider(thinking_provider_name)
                except ValueError:
                    thinking_provider = None
                if (
                    thinking_provider is not None
                    and thinking_provider in self.available_providers
                    and thinking_provider not in self._disabled_providers
                    and not self._provider_in_backoff(thinking_provider)
                ):
                    return thinking_provider

        if (
            self.preferred_provider in self.available_providers
            and self.preferred_provider not in self._disabled_providers
            and not self._provider_in_backoff(self.preferred_provider)
        ):
            return self.preferred_provider

        # Fallback chain: codex -> claude -> gemini
        for provider in PROVIDER_FALLBACK_ORDER:
            if (
                provider in self.available_providers
                and provider not in self._disabled_providers
                and not self._provider_in_backoff(provider)
            ):
                logger.info(f"Using fallback provider: {provider.value}")
                return provider

        return None

    def _provider_attempt_order(
        self, thinking_mode: bool = False
    ) -> list[ModelProvider]:
        """Return providers in the order they should be attempted."""
        preferred = self._get_provider(thinking_mode=thinking_mode)
        if preferred is None:
            return []

        base_order = [preferred, *PROVIDER_FALLBACK_ORDER]

        ordered: list[ModelProvider] = []
        for provider in base_order:
            if (
                provider in self.available_providers
                and provider not in ordered
                and provider not in self._disabled_providers
                and not self._provider_in_backoff(provider)
            ):
                ordered.append(provider)
        return ordered

    def _provider_in_backoff(self, provider: ModelProvider) -> bool:
        until = self._provider_backoff_until.get(provider, 0.0)
        return time.time() < until

    @staticmethod
    def _model_for_request(
        config: dict[str, Any],
        *,
        tier: ModelTier = SYNTHESIS_TIER,
    ) -> str:
        """Return the concrete model id for this request's tier.

        Utility-tier calls take the provider's ``light_model`` when one is
        configured; otherwise they share the synthesis model (Gemini has no
        light model unless ``GEMINI_LIGHT_MODEL`` is set).
        """
        if tier == UTILITY_TIER:
            light_model = cast(str | None, config.get("light_model"))
            if light_model:
                return light_model
        return cast(str, config["model"])

    @staticmethod
    def _reasoning_effort_for_request(
        provider: ModelProvider,
        config: dict[str, Any],
        *,
        tier: ModelTier,
        override: str | None,
    ) -> str | None:
        """Resolve the ``reasoning_effort`` to send, if the provider takes one.

        An explicit caller override always wins; otherwise the tier decides
        (synthesis → the configured ``CODEX_REASONING_EFFORT``, utility →
        "low").

        NOTE — resolution is deliberately provider-agnostic for an explicit
        override (a caller pin is echoed back for any provider), but ONLY the
        Codex proxy is verified to honour the directive, so the *attachment*
        step drops it everywhere else. Every OpenAI-compatible payload must go
        through :meth:`_apply_reasoning_effort`, which owns that Codex-only
        rule; never write ``payload["reasoning_effort"]`` inline.
        """
        if override:
            return override
        if provider != ModelProvider.CODEX:
            return None
        if tier == UTILITY_TIER:
            return cast(str | None, config.get("light_reasoning_effort")) or "low"
        return cast(str | None, config.get("reasoning_effort")) or "high"

    @staticmethod
    def _apply_reasoning_effort(
        payload: dict[str, Any],
        provider: ModelProvider,
        effort: str | None,
    ) -> None:
        """Attach a resolved ``reasoning_effort`` to an OpenAI-compatible payload.

        The single place that decides whether the directive enters the request
        body: only the Codex proxy is verified to honour a top-level
        ``reasoning_effort``, so every other provider silently drops it. Shared
        by the generate, stream and tool-calling paths.
        """
        if effort and provider == ModelProvider.CODEX:
            payload["reasoning_effort"] = effort

    @staticmethod
    def _effective_max_tokens(
        provider: ModelProvider,
        tier: ModelTier,
        max_tokens: int,
    ) -> int:
        """Apply the Codex synthesis-tier answer-budget floor (F4).

        gpt-5.6-sol bills its chain-of-thought against ``max_tokens``; at
        ``CODEX_REASONING_EFFORT=high`` a 9k-14k cap can be entirely consumed
        by reasoning, returning ``finish_reason=length`` with empty content.
        Synthesis-tier Codex calls are therefore raised to at least
        ``CODEX_SYNTHESIS_MAX_TOKENS`` (default 32000). A caller that already
        asked for more keeps its larger value — the floor only ever raises.
        """
        if provider != ModelProvider.CODEX or tier != SYNTHESIS_TIER:
            return max_tokens
        floor = CODEX_SYNTHESIS_MAX_TOKENS_DEFAULT
        raw = os.getenv(CODEX_SYNTHESIS_MAX_TOKENS_ENV)
        if raw:
            try:
                parsed = int(raw)
            except ValueError:
                parsed = 0
            if parsed > 0:
                floor = parsed
        return max(max_tokens, floor)

    @staticmethod
    def _openai_compatible_headers(api_key: str) -> dict[str, str]:
        """Build headers for OpenAI-compatible providers."""
        return {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    @staticmethod
    def _gemini_headers(api_key: str) -> dict[str, str]:
        """Gemini auth header.

        The key travels in ``x-goog-api-key``, NEVER as a ``?key=`` query
        param: httpx embeds the full URL in HTTPStatusError messages, which
        are logged, streamed to the browser and persisted in query_traces.
        """
        return {
            "x-goog-api-key": api_key,
            "Content-Type": "application/json",
        }

    @staticmethod
    def _openai_compatible_payload(
        provider: ModelProvider,
        prompt: str,
        system_prompt: str | None,
        temperature: float,
        max_tokens: int,
        config: dict[str, Any],
        *,
        prompt_cache_id: str | None = None,
        response_json_schema: dict[str, Any] | None = None,
        response_mime_type: str | None = None,
        schema_name: str = "structured_output",
        reasoning_effort: str | None = None,
        tier: ModelTier = SYNTHESIS_TIER,
    ) -> dict[str, Any]:
        """Build JSON payload for OpenAI-compatible providers.

        Both CLI-subscription proxies speak the same dialect. The Codex proxy
        additionally honours a top-level ``reasoning_effort``
        ("low"|"medium"|"high") — verified live — which bounds the
        chain-of-thought so a long reasoning run cannot eat the whole
        ``max_tokens`` and empty the answer (failure-map F4). The same failure
        is guarded from the other side by :meth:`_effective_max_tokens`, which
        floors the synthesis-tier Codex budget.

        Structured output degrades per provider: the Codex proxy constrains
        generation server-side from a strict ``json_schema``; the Claude proxy
        only guarantees ``{"type": "json_object"}``, so it gets that (the
        schema requirements already live in the caller's prompt).

        ``prompt_cache_id`` is a no-op on providers that ignore it; it is only
        attached when the caller supplied an agent identity.
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload: dict[str, Any] = {
            "model": config["model"],
            "messages": messages,
            "temperature": temperature,
            "max_tokens": LLMService._effective_max_tokens(provider, tier, max_tokens),
        }
        LLMService._apply_reasoning_effort(payload, provider, reasoning_effort)
        if prompt_cache_id and provider == ModelProvider.CODEX:
            payload["prompt_cache_id"] = prompt_cache_id

        if response_json_schema is not None:
            if provider == ModelProvider.CODEX:
                payload["response_format"] = {
                    "type": "json_schema",
                    "json_schema": {
                        "name": schema_name,
                        "schema": response_json_schema,
                        "strict": True,
                    },
                }
            else:
                payload["response_format"] = {"type": "json_object"}
        elif response_mime_type == "application/json":
            payload["response_format"] = {"type": "json_object"}
        return payload

    #: Statuses that mean OUR request was malformed. Retrying the same request
    #: on another provider cannot help, so these alone stop the provider loop.
    #: Everything else (402 payment required, 412 precondition failed, 401/403,
    #: 429, 5xx …) is an account- or provider-level failure: fall through.
    _REQUEST_SHAPE_STATUSES = frozenset({400, 404, 422})

    @staticmethod
    def _should_retry_next_provider(
        exc: Exception, *, structured_output: bool = False
    ) -> bool:
        """Whether a failure should fall through to the next provider.

        ``structured_output`` marks a call that carried a ``response_format``
        directive. There a 400 usually means THIS provider rejected the
        directive, not that the request is universally malformed — the next
        provider (which gets a degraded ``json_object`` form) may well accept
        it, so the 400 advances instead of aborting. Plain calls keep the
        strict rule: a 400 is fatal.
        """
        if isinstance(exc, httpx.TransportError):
            return True
        if isinstance(exc, httpx.HTTPStatusError):
            status = exc.response.status_code
            if structured_output and status == 400:
                return True
            return status not in LLMService._REQUEST_SHAPE_STATUSES
        return False

    @staticmethod
    def _should_retry_same_provider(exc: Exception, attempt: int) -> bool:
        if attempt >= 1:
            return False
        if isinstance(exc, httpx.TransportError):
            return True
        if isinstance(exc, httpx.HTTPStatusError):
            return exc.response.status_code in {408, 425, 500, 502, 503, 504}
        return False

    @staticmethod
    def _safe_response_text(response: httpx.Response) -> str:
        """``response.text`` or "" — a streamed, unread response raises."""
        try:
            return response.text or ""
        except Exception:  # noqa: BLE001 — httpx.ResponseNotRead and friends
            return ""

    @staticmethod
    def _retry_delay_seconds(exc: Exception) -> float:
        if isinstance(exc, httpx.HTTPStatusError):
            try:
                data = exc.response.json()
                retry_after_seconds = (
                    data.get("error", {}).get("metadata", {}).get("retry_after_seconds")
                )
                if retry_after_seconds is not None:
                    return max(1.0, float(retry_after_seconds))
            except Exception:
                pass
            retry_after = exc.response.headers.get("retry-after")
            if retry_after:
                try:
                    return max(1.0, float(retry_after))
                except ValueError:
                    pass
            text = LLMService._safe_response_text(exc.response)
            match = re.search(
                r"retry in ([0-9]+(?:\\.[0-9]+)?)s", text, flags=re.IGNORECASE
            )
            if match:
                try:
                    return max(1.0, float(match.group(1)))
                except ValueError:
                    pass
        return 5.0

    @staticmethod
    def _format_provider_error(exc: Exception) -> str:
        """Return a compact, SECRET-FREE error string for logs.

        ``exc.response.text`` raises ``httpx.ResponseNotRead`` on a streamed
        response that was never read, so the body is best-effort only; the
        result always goes through :func:`_redact_secrets` because httpx puts
        the full request URL (historically carrying ``?key=``) in the message.
        """
        if isinstance(exc, httpx.HTTPStatusError):
            body = LLMService._safe_response_text(exc.response).strip()
            body = _redact_secrets(re.sub(r"\s+", " ", body))
            if len(body) > 320:
                body = body[:317] + "..."
            return (
                f"{exc.response.status_code} {exc.__class__.__name__}: {body}"
                if body
                else f"{exc.response.status_code} {exc.__class__.__name__}"
            )
        return exc.__class__.__name__

    def _mark_provider_invalid(self, provider: ModelProvider, exc: Exception) -> None:
        # 401/403 = bad credentials, 402 = payment required, 412 = precondition
        # failed (suspended account). All four are account-level and permanent
        # for this process: one failure disables the provider so the next call
        # goes straight to the fallback instead of paying the round-trip again.
        if isinstance(exc, httpx.HTTPStatusError) and exc.response.status_code in {
            401,
            402,
            403,
            412,
        }:
            self._disabled_providers.add(provider)
            logger.warning(
                "Disabling LLM provider %s for this session after account-level "
                "failure (HTTP %s)",
                provider.value,
                exc.response.status_code,
            )
            return
        if isinstance(exc, httpx.HTTPStatusError) and exc.response.status_code == 429:
            delay = min(max(30.0, self._retry_delay_seconds(exc)), 300.0)
            self._provider_backoff_until[provider] = time.time() + delay
            logger.warning(
                "Backing off LLM provider %s for %.1fs after rate limit",
                provider.value,
                delay,
            )

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client

    async def close(self) -> None:
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    def get_model_info(self) -> dict[str, str]:
        """Return the last-used provider and model names."""
        return {
            "provider": self.last_provider_used,
            "model": self.last_model_used,
        }

    def _cache_enabled(self) -> bool:
        """Whether Gemini provider-side prompt caching is enabled."""
        if time.time() < self._prompt_cache_backoff_until:
            return False
        return os.getenv("GEMINI_ENABLE_PROMPT_CACHE", "1").lower() not in {
            "0",
            "false",
            "no",
        }

    def _purge_expired_prompt_cache(self) -> None:
        """Drop expired cached-content handles from memory."""
        now = time.time()
        expired = [
            key for key, expiry in self._prompt_cache_expiry.items() if expiry <= now
        ]
        for key in expired:
            self._prompt_cache_names.pop(key, None)
            self._prompt_cache_expiry.pop(key, None)

    @staticmethod
    def _estimate_prompt_tokens(text: str) -> int:
        """Cheap token estimate used only to avoid invalid cache requests."""
        if not text:
            return 0
        # Gemini tokenizers vary by model; chars/4 is conservative enough to
        # skip clearly undersized prefixes without needing a full tokenizer.
        return max(1, len(text) // 4)

    @staticmethod
    def _minimum_cache_tokens(model_name: str) -> int:
        """Best-effort minimum for Gemini explicit cached contents."""
        normalized = model_name.lower()
        if "flash" in normalized:
            return 1024
        return 4096

    def _resolve_model_override(self, model_override: str) -> tuple[ModelProvider, str]:
        """Resolve a model override string to a provider and model ID.

        Accepts an explicit ``provider:model`` form (``codex:gpt-5.6-sol``) or a
        bare model id routed by prefix: ``gpt-*``/``o3*``/``o4*`` → Codex proxy,
        ``claude-*`` → Claude proxy, ``gemini-*`` → Gemini direct. Anything
        unrecognised falls back to the preferred provider so an unknown id can
        still be served by the primary proxy rather than mis-routed to Gemini.
        """
        raw = model_override.strip()
        prefix, sep, remainder = raw.partition(":")
        if sep and remainder:
            try:
                return ModelProvider(prefix.strip().lower()), remainder.strip()
            except ValueError:
                pass  # a colon inside a bare model id — fall through

        lowered = raw.lower()
        for model_prefix, provider in _MODEL_PREFIX_PROVIDERS:
            if lowered.startswith(model_prefix):
                return provider, raw
        return self.preferred_provider, raw

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        thinking_mode: bool = False,
        response_mime_type: str | None = None,
        response_json_schema: dict[str, Any] | None = None,
        cache_key: str | None = None,
        cache_prefix: str | None = None,
        cache_ttl_seconds: int = 900,
        model_override: str | None = None,
        agent_id: str | None = None,
        request_timeout: float | None = None,
        reasoning_effort: str | None = None,
        tier: ModelTier = SYNTHESIS_TIER,
    ) -> str:
        """
        Generate a response (non-streaming).

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            thinking_mode: If True, honour ``LLM_THINKING_PROVIDER`` first
            request_timeout: Optional per-call HTTP timeout (seconds) that
                overrides the shared client timeout for THIS request only. Used
                by the Scholar-RAG dialectical synthesis (a slow thinking model
                whose generation can exceed the default 120 s client timeout).
                ``None`` keeps the client-level timeout (unchanged behaviour).
            reasoning_effort: Explicit reasoning-budget cap
                ("low"|"medium"|"high"); overrides the tier default. Bounds the
                chain-of-thought so it cannot eat the whole ``max_tokens`` and
                empty the answer (failure-map F4).
            tier: ``"synthesis"`` for full academic quality, ``"utility"`` for
                cheap internal subtasks (lemma expansion, planning, query
                classification, citation verification).

        Returns:
            Generated text
        """
        # Reset the reasoning side-channel so a non-reasoning model (or the Gemini
        # path, which never sets it) cannot surface a previous call's thinking.
        self.last_reasoning_content = ""
        # --- Model override: bypass the normal provider loop ---
        if model_override:
            override_provider, override_model = self._resolve_model_override(
                model_override
            )
            override_config = self._resolve_config(override_provider)
            override_api_key = self._api_key_for(override_provider)
            if override_api_key:
                try:
                    override_config["model"] = override_model
                    self.last_provider_used = override_provider.value
                    self.last_model_used = override_model

                    if override_provider == ModelProvider.GEMINI:
                        return await self._generate_gemini(
                            prompt,
                            system_prompt,
                            temperature,
                            max_tokens,
                            override_api_key,
                            override_config,
                            response_mime_type=response_mime_type,
                            response_json_schema=response_json_schema,
                            cache_key=cache_key,
                            cache_prefix=cache_prefix,
                            cache_ttl_seconds=cache_ttl_seconds,
                            request_timeout=request_timeout,
                        )
                    return await self._generate_openai_compatible(
                        override_provider,
                        prompt,
                        system_prompt,
                        temperature,
                        max_tokens,
                        override_api_key,
                        override_config,
                        agent_id=agent_id,
                        response_json_schema=response_json_schema,
                        response_mime_type=response_mime_type,
                        request_timeout=request_timeout,
                        reasoning_effort=self._reasoning_effort_for_request(
                            override_provider,
                            override_config,
                            tier=tier,
                            override=reasoning_effort,
                        ),
                        tier=tier,
                    )
                except Exception as exc:
                    self._mark_provider_invalid(override_provider, exc)
                    logger.warning(
                        "Model override %s/%s failed (%s); falling back to provider loop",
                        override_provider.value,
                        override_model,
                        self._format_provider_error(exc),
                    )

        providers = self._provider_attempt_order(thinking_mode=thinking_mode)
        if not providers:
            raise RuntimeError("No LLM provider available")

        # A call carrying a response_format directive gets the relaxed 400
        # policy: the rejection is about the directive, not the request shape.
        structured_output = (
            response_json_schema is not None or response_mime_type == "application/json"
        )
        last_exc: Exception | None = None
        for idx, provider in enumerate(providers):
            for attempt in range(2):
                try:
                    if provider in self._rate_limiters:
                        await self._rate_limiters[provider].wait_if_needed()

                    config = self._resolve_config(provider)
                    api_key = self._api_key_for(provider)

                    model_name = self._model_for_request(config, tier=tier)
                    request_config = dict(config)
                    request_config["model"] = model_name

                    self.last_provider_used = provider.value
                    self.last_model_used = model_name

                    if provider == ModelProvider.GEMINI:
                        return await self._generate_gemini(
                            prompt,
                            system_prompt,
                            temperature,
                            max_tokens,
                            api_key,
                            request_config,
                            response_mime_type=response_mime_type,
                            response_json_schema=response_json_schema,
                            cache_key=cache_key,
                            cache_prefix=cache_prefix,
                            cache_ttl_seconds=cache_ttl_seconds,
                            request_timeout=request_timeout,
                        )
                    return await self._generate_openai_compatible(
                        provider,
                        prompt,
                        system_prompt,
                        temperature,
                        max_tokens,
                        api_key,
                        request_config,
                        agent_id=agent_id,
                        response_json_schema=response_json_schema,
                        request_timeout=request_timeout,
                        response_mime_type=response_mime_type,
                        reasoning_effort=self._reasoning_effort_for_request(
                            provider,
                            request_config,
                            tier=tier,
                            override=reasoning_effort,
                        ),
                        tier=tier,
                    )
                except Exception as exc:
                    last_exc = exc
                    self._mark_provider_invalid(provider, exc)
                    if self._should_retry_same_provider(exc, attempt):
                        delay = self._retry_delay_seconds(exc)
                        logger.warning(
                            "LLM provider %s failed (%s); retrying once in %.1fs",
                            provider.value,
                            self._format_provider_error(exc),
                            delay,
                        )
                        await asyncio.sleep(delay)
                        continue
                    if idx == len(providers) - 1 or not (
                        self._should_retry_next_provider(
                            exc, structured_output=structured_output
                        )
                    ):
                        raise
                    logger.warning(
                        "LLM provider %s failed (%s); falling back to %s",
                        provider.value,
                        self._format_provider_error(exc),
                        providers[idx + 1].value,
                    )
                    break

        if last_exc:
            raise last_exc
        raise RuntimeError("No LLM provider available")

    async def generate_with_tools(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        *,
        tool_choice: str | dict[str, Any] = "auto",
        temperature: float = 0.1,
        max_tokens: int = 1024,
        model_override: str | None = None,
        tier: ModelTier = SYNTHESIS_TIER,
        reasoning_effort: str | None = None,
    ) -> dict[str, Any]:
        """OpenAI-style chat-completion with native tool-calling.

        Routes through the OpenAI-compatible proxies (Codex, then Claude) with
        the SAME provider loop as :meth:`generate`, so the ReAct loop survives a
        downed provider instead of dying on the first candidate. Gemini stays
        excluded: it does not speak the OpenAI tools dialect.

        Args:
            messages: Full chat history in OpenAI format. Each message is one of
                ``{"role": "system"|"user"|"assistant"|"tool", ...}``.
                Assistant messages may carry ``tool_calls``; tool messages must
                carry ``tool_call_id`` and ``content``.
            tools: OpenAI ``[{"type": "function", "function": {...}}, ...]``.
            tool_choice: ``"auto"``, ``"none"``, ``"required"``, or
                ``{"type": "function", "function": {"name": ...}}``.
            temperature, max_tokens: standard sampling params.
            model_override: optional explicit model id; used as the FIRST rung,
                with the remaining providers still available as fallbacks.
            tier: model tier for the non-override rungs (the ReAct loop is a
                synthesis-tier caller).
            reasoning_effort: explicit override of the tier default.

        Returns:
            The first choice's ``message`` dict, e.g.::

                {"role": "assistant", "content": null,
                 "tool_calls": [{"id": "...", "type": "function",
                                 "function": {"name": "...",
                                              "arguments": "{...}"}}]}

            or ``{"role": "assistant", "content": "final answer text"}``.

        Raises:
            RuntimeError: when no compatible provider is available.
            httpx.HTTPStatusError: on non-2xx responses from the last rung.
        """
        candidates = self._tool_call_candidates(model_override, tier=tier)
        if not candidates:
            raise RuntimeError(
                "No OpenAI-compatible provider available for tool-calling"
            )

        last_exc: Exception | None = None
        for idx, (provider, model_name) in enumerate(candidates):
            try:
                return await self._generate_with_tools_once(
                    provider,
                    model_name,
                    messages,
                    tools,
                    tool_choice=tool_choice,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    reasoning_effort=reasoning_effort,
                    tier=tier,
                )
            except Exception as exc:
                last_exc = exc
                self._mark_provider_invalid(provider, exc)
                if idx == len(candidates) - 1 or not self._should_retry_next_provider(
                    exc
                ):
                    raise
                logger.warning(
                    "Tool-calling provider %s failed (%s); falling back to %s",
                    provider.value,
                    self._format_provider_error(exc),
                    candidates[idx + 1][0].value,
                )

        if last_exc:  # pragma: no cover — defensive
            raise last_exc
        raise RuntimeError("No OpenAI-compatible provider available for tool-calling")

    def _tool_call_candidates(
        self, model_override: str | None, *, tier: ModelTier
    ) -> list[tuple[ModelProvider, str]]:
        """Ordered (provider, model) rungs for the tool-calling path.

        The override (when it resolves to an OpenAI-compatible provider) leads;
        the normal attempt order supplies the fallbacks. Gemini is filtered out
        and providers without a key are skipped.
        """
        candidates: list[tuple[ModelProvider, str]] = []

        def _add(provider: ModelProvider, model: str) -> None:
            if provider not in OPENAI_COMPATIBLE_PROVIDERS:
                return
            if not self._api_key_for(provider):
                return
            if (provider, model) not in candidates:
                candidates.append((provider, model))

        if model_override:
            _add(*self._resolve_model_override(model_override))
        for provider in self._provider_attempt_order():
            config = self._resolve_config(provider)
            _add(provider, self._model_for_request(config, tier=tier))
        return candidates

    async def _generate_with_tools_once(
        self,
        provider: ModelProvider,
        model_name: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        *,
        tool_choice: str | dict[str, Any],
        temperature: float,
        max_tokens: int,
        reasoning_effort: str | None,
        tier: ModelTier,
    ) -> dict[str, Any]:
        """One tool-calling attempt against a single provider."""
        config = dict(self._resolve_config(provider))
        config["model"] = model_name
        api_key = self._api_key_for(provider)
        if not api_key:
            raise RuntimeError(f"No API key configured for {provider.value}")

        self.last_provider_used = provider.value
        self.last_model_used = model_name

        if provider in self._rate_limiters:
            await self._rate_limiters[provider].wait_if_needed()

        client = await self._get_client()
        payload: dict[str, Any] = {
            "model": model_name,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "tools": tools,
            "tool_choice": tool_choice,
        }
        self._apply_reasoning_effort(
            payload,
            provider,
            self._reasoning_effort_for_request(
                provider, config, tier=tier, override=reasoning_effort
            ),
        )

        # Respect existing rate-limit backoff so we don't pile on after a 429.
        if self._provider_in_backoff(provider):
            wait = max(
                0.0, self._provider_backoff_until.get(provider, 0.0) - time.time()
            )
            logger.info(
                "generate_with_tools: %s in backoff for %.1fs; sleeping",
                provider.value,
                wait,
            )
            await asyncio.sleep(min(wait, 30.0))

        url = f"{config['base_url']}/chat/completions"
        headers = self._openai_compatible_headers(api_key)
        response = await client.post(url, headers=headers, json=payload)

        # One graceful retry on 429 / 5xx to ride out short rate-limit bursts.
        # Honors Retry-After when present.
        if response.status_code in {408, 425, 429, 500, 502, 503, 504}:
            try:
                delay = self._retry_delay_seconds(
                    httpx.HTTPStatusError(
                        "transient", request=response.request, response=response
                    )
                )
            except Exception:  # pragma: no cover — defensive
                delay = 1.0
            logger.warning(
                "generate_with_tools: %s on %s, retrying once in %.1fs",
                response.status_code,
                provider.value,
                delay,
            )
            await asyncio.sleep(min(delay, 30.0))
            response = await client.post(url, headers=headers, json=payload)

        if response.status_code == 429:
            # Mark provider as in backoff so subsequent calls back off too.
            try:
                exc = httpx.HTTPStatusError(
                    "rate-limited", request=response.request, response=response
                )
                self._mark_provider_invalid(provider, exc)
            except Exception:  # pragma: no cover — defensive
                pass

        response.raise_for_status()
        data = response.json()
        try:
            message = data["choices"][0]["message"]
        except (KeyError, IndexError) as exc:  # pragma: no cover — defensive
            raise RuntimeError(f"Malformed response from {provider.value}") from exc
        usage = TokenUsage.from_openai_usage(
            data.get("usage") if isinstance(data, dict) else None,
            model=model_name,
            provider=provider.value,
        )
        await self._emit_token_usage(usage)
        return cast(dict[str, Any], message)

    async def _ensure_gemini_cached_content(
        self,
        *,
        api_key: str,
        config: dict[str, Any],
        cache_key: str,
        cache_prefix: str,
        system_prompt: str | None,
        ttl_seconds: int,
    ) -> str | None:
        """Create or reuse a Gemini cached-content prefix."""
        if not self._cache_enabled():
            return None

        minimum_tokens = self._minimum_cache_tokens(str(config["model"]))
        if self._estimate_prompt_tokens(cache_prefix) < minimum_tokens:
            logger.info(
                "Skipping Gemini prompt cache: prefix estimated at %s tokens, below minimum %s for %s",
                self._estimate_prompt_tokens(cache_prefix),
                minimum_tokens,
                config["model"],
            )
            return None

        self._purge_expired_prompt_cache()
        stable_key = hashlib.sha256(
            f"{config['model']}::{cache_key}::{system_prompt or ''}::{cache_prefix}".encode()
        ).hexdigest()
        cached_name = self._prompt_cache_names.get(stable_key)
        if cached_name:
            return cached_name

        client = await self._get_client()
        payload: dict[str, Any] = {
            "model": f"models/{config['model']}",
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": cache_prefix}],
                }
            ],
            "ttl": f"{ttl_seconds}s",
        }
        if system_prompt:
            payload["systemInstruction"] = {
                "parts": [{"text": system_prompt}],
            }

        try:
            response = await client.post(
                f"{config['base_url']}/cachedContents",
                headers=self._gemini_headers(api_key),
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            name = cast(str | None, data.get("name"))
            if not name:
                return None
            self._prompt_cache_names[stable_key] = name
            self._prompt_cache_expiry[stable_key] = time.time() + ttl_seconds
            return name
        except Exception as exc:
            if (
                isinstance(exc, httpx.HTTPStatusError)
                and exc.response.status_code == 429
            ):
                self._prompt_cache_backoff_until = time.time() + 300
            logger.warning("Gemini prompt cache creation failed", exc_info=True)
            return None

    @staticmethod
    def _prompt_cache_id(agent_id: str | None) -> str | None:
        """Compose the OpenAI-compatible prompt_cache_id from agent identity.

        Stable across calls so the cached prefix is reused. Includes a short
        version suffix so we can invalidate after a system-prompt rewrite by
        bumping ``ELEUTHERIA_PROMPT_CACHE_VERSION``.
        """
        if not agent_id:
            return None
        version = os.getenv("ELEUTHERIA_PROMPT_CACHE_VERSION", "v1")
        return f"eleutheria-{agent_id}-{version}"

    async def _generate_openai_compatible(
        self,
        provider: ModelProvider,
        prompt: str,
        system_prompt: str | None,
        temperature: float,
        max_tokens: int,
        api_key: str,
        config: dict[str, Any],
        *,
        agent_id: str | None = None,
        response_json_schema: dict[str, Any] | None = None,
        response_mime_type: str | None = None,
        schema_name: str = "structured_output",
        request_timeout: float | None = None,
        reasoning_effort: str | None = None,
        tier: ModelTier = SYNTHESIS_TIER,
    ) -> str:
        """Generate using an OpenAI-compatible API (Codex / Claude proxies)."""
        client = await self._get_client()

        response = await client.post(
            f"{config['base_url']}/chat/completions",
            headers=self._openai_compatible_headers(api_key),
            json=self._openai_compatible_payload(
                provider,
                prompt,
                system_prompt,
                temperature,
                max_tokens,
                config,
                prompt_cache_id=self._prompt_cache_id(agent_id),
                response_json_schema=response_json_schema,
                response_mime_type=response_mime_type,
                schema_name=schema_name,
                reasoning_effort=reasoning_effort,
                tier=tier,
            ),
            # Per-call timeout override: a slow thinking-model synthesis can run
            # well past the shared 120 s client timeout. ``None`` keeps the
            # client-level timeout (every other call site is unchanged).
            timeout=request_timeout if request_timeout is not None else self.timeout,
        )
        response.raise_for_status()
        data = response.json()
        message = data["choices"][0]["message"]
        # ``content`` is the clean finished answer. Thinking models (deepseek-v4-pro,
        # kimi-k2-thinking) additionally return their chain-of-thought in
        # ``reasoning_content`` — capture it on the side-channel ONLY (never folded
        # into the returned answer). Non-reasoning models omit the field → "".
        result: str = message.get("content") or ""
        self.last_reasoning_content = message.get("reasoning_content") or ""
        usage = TokenUsage.from_openai_usage(
            data.get("usage") if isinstance(data, dict) else None,
            model=cast(str, config.get("model") or ""),
            provider=provider.value,
            agent_id=agent_id,
        )
        await self._emit_token_usage(usage)
        return result

    async def _generate_gemini(
        self,
        prompt: str,
        system_prompt: str | None,
        temperature: float,
        max_tokens: int,
        api_key: str,
        config: dict[str, Any],
        response_mime_type: str | None = None,
        response_json_schema: dict[str, Any] | None = None,
        *,
        cache_key: str | None = None,
        cache_prefix: str | None = None,
        cache_ttl_seconds: int = 900,
        request_timeout: float | None = None,
    ) -> str:
        """Generate using Gemini API."""
        client = await self._get_client()
        post_timeout = request_timeout if request_timeout is not None else self.timeout
        cached_content = None
        if cache_key and cache_prefix:
            cached_content = await self._ensure_gemini_cached_content(
                api_key=api_key,
                config=config,
                cache_key=cache_key,
                cache_prefix=cache_prefix,
                system_prompt=system_prompt,
                ttl_seconds=cache_ttl_seconds,
            )

        body = self._build_gemini_request_body(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            cached_content=cached_content,
            config=config,
            response_mime_type=response_mime_type,
            response_json_schema=response_json_schema,
        )

        response = await client.post(
            f"{config['base_url']}/models/{config['model']}:generateContent",
            headers=self._gemini_headers(api_key),
            json=body,
            timeout=post_timeout,
        )
        response.raise_for_status()
        data = response.json()
        result = self._extract_gemini_text(data)
        if result:
            usage = TokenUsage.from_gemini_metadata(
                data.get("usageMetadata") if isinstance(data, dict) else None,
                model=cast(str, config.get("model") or ""),
            )
            await self._emit_token_usage(usage)
            return result

        # Gemini thinking models may occasionally spend the full budget on
        # internal thought tokens and return no visible text parts. Retry once
        # with thinking disabled before surfacing an error.
        retry_prompt = (
            f"{cache_prefix}\n\n{prompt}" if cached_content and cache_prefix else prompt
        )
        retry_body = self._build_gemini_request_body(
            prompt=retry_prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max(max_tokens, 128),
            cached_content=None if cached_content and cache_prefix else cached_content,
            config=config,
            response_mime_type=response_mime_type,
            response_json_schema=response_json_schema,
        )
        retry_response = await client.post(
            f"{config['base_url']}/models/{config['model']}:generateContent",
            headers=self._gemini_headers(api_key),
            json=retry_body,
            timeout=post_timeout,
        )
        retry_response.raise_for_status()
        retry_data = retry_response.json()
        retry_result = self._extract_gemini_text(retry_data)
        if retry_result:
            usage = TokenUsage.from_gemini_metadata(
                retry_data.get("usageMetadata")
                if isinstance(retry_data, dict)
                else None,
                model=cast(str, config.get("model") or ""),
            )
            await self._emit_token_usage(usage)
            return retry_result

        raise RuntimeError("Gemini returned no text content parts.")

    @staticmethod
    def _build_gemini_request_body(
        *,
        prompt: str,
        system_prompt: str | None,
        temperature: float,
        max_tokens: int,
        cached_content: str | None,
        config: dict[str, Any],
        response_mime_type: str | None = None,
        response_json_schema: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        contents = [{"role": "user", "parts": [{"text": prompt}]}]
        generation_config: dict[str, Any] = {
            "temperature": temperature,
            "maxOutputTokens": max_tokens,
        }
        if response_mime_type:
            generation_config["responseMimeType"] = response_mime_type
        if response_json_schema:
            generation_config["responseJsonSchema"] = response_json_schema

        thinking_budget = config.get("thinking_budget")
        include_thoughts = config.get("include_thoughts")
        if thinking_budget is not None or include_thoughts is not None:
            thinking_config: dict[str, Any] = {}
            if thinking_budget is not None:
                thinking_config["thinkingBudget"] = int(thinking_budget)
            if include_thoughts is not None:
                thinking_config["includeThoughts"] = bool(include_thoughts)
            generation_config["thinkingConfig"] = thinking_config

        body: dict[str, Any] = {
            "contents": contents,
            "generationConfig": generation_config,
        }
        if cached_content:
            body["cachedContent"] = cached_content
        elif system_prompt:
            body["systemInstruction"] = {"parts": [{"text": system_prompt}]}
        return body

    @staticmethod
    def _extract_gemini_text(data: dict[str, Any]) -> str:
        candidates = data.get("candidates") or []
        texts: list[str] = []
        fallback_texts: list[str] = []
        for candidate in candidates:
            content = candidate.get("content") or {}
            for part in content.get("parts") or []:
                text = part.get("text")
                if not text:
                    continue
                if part.get("thought"):
                    fallback_texts.append(text)
                else:
                    texts.append(text)
        if texts:
            return "\n".join(texts).strip()
        if fallback_texts:
            return "\n".join(fallback_texts).strip()
        return ""

    async def stream(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        thinking_mode: bool = False,
        model_override: str | None = None,
        tier: ModelTier = SYNTHESIS_TIER,
    ) -> AsyncIterator[str]:
        """
        Generate a streaming response.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            thinking_mode: If True, honour ``LLM_THINKING_PROVIDER`` first
            model_override: Pin a specific provider/model (e.g. the user-selected
                model) instead of the default provider loop. Mirrors
                :meth:`generate`; falls back to the provider loop if the override
                fails before emitting any token.
            tier: ``"synthesis"`` or ``"utility"`` model tier.

        Yields:
            Text chunks as they're generated
        """
        # Reset the reasoning side-channel; the OpenAI-compatible stream path
        # accumulates ``reasoning_content`` deltas into it (answer chunks only are
        # yielded). Gemini streaming never sets it.
        self.last_reasoning_content = ""
        self.last_finish_reason = ""
        # --- Model override: bypass the normal provider loop (see generate). ---
        if model_override:
            override_provider, override_model = self._resolve_model_override(
                model_override
            )
            override_api_key = self._api_key_for(override_provider)
            if override_api_key:
                override_config = self._resolve_config(override_provider)
                override_config["model"] = override_model
                self.last_provider_used = override_provider.value
                self.last_model_used = override_model
                yielded = False
                try:
                    if override_provider == ModelProvider.GEMINI:
                        async for chunk in self._stream_gemini(
                            prompt,
                            system_prompt,
                            temperature,
                            max_tokens,
                            override_api_key,
                            override_config,
                        ):
                            yielded = True
                            yield chunk
                    else:
                        async for chunk in self._stream_openai_compatible(
                            override_provider,
                            prompt,
                            system_prompt,
                            temperature,
                            max_tokens,
                            override_api_key,
                            override_config,
                            tier=tier,
                        ):
                            yielded = True
                            yield chunk
                    return
                except Exception as exc:
                    self._mark_provider_invalid(override_provider, exc)
                    # Once tokens are on the wire we can't restart cleanly.
                    if yielded:
                        raise
                    logger.warning(
                        "Streaming model override %s/%s failed (%s); "
                        "falling back to provider loop",
                        override_provider.value,
                        override_model,
                        self._format_provider_error(exc),
                    )

        providers = self._provider_attempt_order(thinking_mode=thinking_mode)
        if not providers:
            raise RuntimeError("No LLM provider available")

        last_exc: Exception | None = None
        for idx, provider in enumerate(providers):
            for attempt in range(2):
                yielded = False
                try:
                    if provider in self._rate_limiters:
                        await self._rate_limiters[provider].wait_if_needed()

                    config = self._resolve_config(provider)
                    api_key = self._api_key_for(provider)

                    model_name = self._model_for_request(config, tier=tier)
                    request_config = dict(config)
                    request_config["model"] = model_name

                    self.last_provider_used = provider.value
                    self.last_model_used = model_name

                    if provider == ModelProvider.GEMINI:
                        async for chunk in self._stream_gemini(
                            prompt,
                            system_prompt,
                            temperature,
                            max_tokens,
                            api_key,
                            request_config,
                        ):
                            yielded = True
                            yield chunk
                    else:
                        async for chunk in self._stream_openai_compatible(
                            provider,
                            prompt,
                            system_prompt,
                            temperature,
                            max_tokens,
                            api_key,
                            request_config,
                            tier=tier,
                        ):
                            yielded = True
                            yield chunk
                    return
                except Exception as exc:
                    last_exc = exc
                    self._mark_provider_invalid(provider, exc)
                    if yielded:
                        raise
                    if self._should_retry_same_provider(exc, attempt):
                        delay = self._retry_delay_seconds(exc)
                        logger.warning(
                            "Streaming provider %s failed (%s); retrying once in %.1fs",
                            provider.value,
                            self._format_provider_error(exc),
                            delay,
                        )
                        await asyncio.sleep(delay)
                        continue
                    if idx == len(
                        providers
                    ) - 1 or not self._should_retry_next_provider(exc):
                        raise
                    logger.warning(
                        "Streaming provider %s failed (%s); falling back to %s",
                        provider.value,
                        self._format_provider_error(exc),
                        providers[idx + 1].value,
                    )
                    break

        if last_exc:
            raise last_exc

    async def _stream_openai_compatible(
        self,
        provider: ModelProvider,
        prompt: str,
        system_prompt: str | None,
        temperature: float,
        max_tokens: int,
        api_key: str,
        config: dict[str, Any],
        *,
        tier: ModelTier = SYNTHESIS_TIER,
        reasoning_effort: str | None = None,
    ) -> AsyncIterator[str]:
        """Stream using an OpenAI-compatible API (Codex / Claude proxies)."""
        client = await self._get_client()

        async with client.stream(
            "POST",
            f"{config['base_url']}/chat/completions",
            headers=self._openai_compatible_headers(api_key),
            json={
                **self._openai_compatible_payload(
                    provider,
                    prompt,
                    system_prompt,
                    temperature,
                    max_tokens,
                    config,
                    reasoning_effort=self._reasoning_effort_for_request(
                        provider, config, tier=tier, override=reasoning_effort
                    ),
                    tier=tier,
                ),
                "stream": True,
                # Ask the upstream to include a final ``usage`` chunk so we
                # can emit a tokens_used event even for streamed completions.
                "stream_options": {"include_usage": True},
            },
        ) as response:
            await self._raise_for_stream_status(response)
            stream_usage: dict[str, Any] | None = None
            reasoning_parts: list[str] = []
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]
                    if data == "[DONE]":
                        break
                    try:
                        import json

                        chunk = json.loads(data)
                        if isinstance(chunk, dict):
                            chunk_usage = chunk.get("usage")
                            if isinstance(chunk_usage, dict):
                                stream_usage = chunk_usage
                        # The final usage chunk (include_usage) carries an EMPTY
                        # choices list — `[][0]` would raise IndexError and abort
                        # the whole synthesis. Skip any choiceless chunk.
                        choices = chunk.get("choices") or []
                        if not choices:
                            continue
                        # Stash the finish_reason so a "length"-truncated stream
                        # (budget eaten by reasoning → no content) is detectable.
                        finish_reason = choices[0].get("finish_reason")
                        if finish_reason:
                            self.last_finish_reason = finish_reason
                        delta = choices[0].get("delta", {})
                        # Thinking models stream their chain-of-thought as
                        # ``reasoning_content`` deltas — accumulate them on the
                        # side-channel; NEVER yield them as answer chunks.
                        reasoning = delta.get("reasoning_content")
                        if reasoning:
                            reasoning_parts.append(reasoning)
                            self.last_reasoning_content = "".join(reasoning_parts)
                        content = delta.get("content", "")
                        if content:
                            yield content
                    except json.JSONDecodeError:
                        continue
            usage = TokenUsage.from_openai_usage(
                stream_usage,
                model=cast(str, config.get("model") or ""),
                provider=provider.value,
            )
            await self._emit_token_usage(usage)

    @staticmethod
    async def _raise_for_stream_status(response: httpx.Response) -> None:
        """``raise_for_status`` on a streamed response, body preserved.

        httpx will not have read the body of a streaming response, so
        ``exc.response.text`` would raise ``ResponseNotRead`` and the provider's
        error payload would be lost. Read it FIRST, then raise.
        """
        if response.status_code >= 400:
            with contextlib.suppress(Exception):
                await response.aread()
        response.raise_for_status()

    async def _stream_gemini(
        self,
        prompt: str,
        system_prompt: str | None,
        temperature: float,
        max_tokens: int,
        api_key: str,
        config: dict[str, Any],
        *,
        request_timeout: float | None = None,
    ) -> AsyncIterator[str]:
        """Stream using Gemini API.

        Shares :meth:`_build_gemini_request_body` with the blocking path: it is
        the ONE correct builder. The previous hand-rolled body faked a
        ``{"role": "model", "parts": [{"text": "Understood."}]}`` turn to carry
        the system prompt, which gemini-3-* rejects with 400 (no
        thoughtSignature on a synthesised model turn) and which dropped
        ``systemInstruction`` entirely.
        """
        client = await self._get_client()
        post_timeout = request_timeout if request_timeout is not None else self.timeout

        body = self._build_gemini_request_body(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            cached_content=None,
            config=config,
        )

        async with client.stream(
            "POST",
            f"{config['base_url']}/models/{config['model']}:streamGenerateContent",
            headers=self._gemini_headers(api_key),
            params={"alt": "sse"},
            json=body,
            timeout=post_timeout,
        ) as response:
            await self._raise_for_stream_status(response)
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    try:
                        import json

                        data = json.loads(line[6:])
                    except json.JSONDecodeError:
                        continue
                    text = self._extract_gemini_stream_text(data)
                    if text:
                        yield text

    @staticmethod
    def _extract_gemini_stream_text(data: dict[str, Any]) -> str:
        """Answer text out of one streamed Gemini chunk.

        Unlike :meth:`_extract_gemini_text` there is NO thought fallback: a
        chunk carrying only ``thought`` parts is chain-of-thought and must never
        be yielded as answer prose.
        """
        parts_text: list[str] = []
        for candidate in data.get("candidates") or []:
            content = candidate.get("content") or {}
            for part in content.get("parts") or []:
                text = part.get("text")
                if text and not part.get("thought"):
                    parts_text.append(text)
        return "".join(parts_text)

    # ── Segmented stream: distinguishes reasoning deltas from answer deltas ───
    #
    # The plain ``stream()`` yields ONLY answer (``content``) deltas and folds
    # the chain-of-thought (``reasoning_content``) into the ``last_reasoning_content``
    # side-channel — so a caller can never stream the thinking LIVE. The Scholar-RAG
    # dialectical synthesis needs the reasoning deltas as they arrive (to drive the
    # right-panel AGENT REASONING workspace), kept STRICTLY apart from the answer
    # so reasoning text NEVER leaks into the answer. ``stream_segmented`` yields
    # ``("reasoning", delta)`` then ``("answer", delta)`` tuples on a single channel,
    # tagged by origin. deepseek emits reasoning deltas first, then content deltas.

    async def stream_segmented(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        model_override: str | None = None,
        request_timeout: float | None = None,
        reasoning_effort: str | None = None,
        tier: ModelTier = SYNTHESIS_TIER,
    ) -> AsyncIterator[tuple[Literal["reasoning", "answer"], str]]:
        """Stream a reasoning-model completion as TAGGED segments.

        Yields ``("reasoning", delta)`` for each ``reasoning_content`` delta and
        ``("answer", delta)`` for each ``content`` delta — the two NEVER mixed.
        ``self.last_reasoning_content`` still accumulates the full chain-of-thought
        (so the existing metadata trace continues to work). Only the
        OpenAI-compatible path emits reasoning; Gemini and any non-reasoning
        model simply yield ``("answer", …)`` deltas.

        ``model_override`` becomes the FIRST rung; the normal provider attempt
        order supplies the fallbacks, so a downed rung falls through instead of
        dead-ending on a single resolved provider. ``request_timeout`` is the
        dedicated generous per-call HTTP timeout the slow synthesis needs.
        Raises on provider error after the first token (the caller cannot
        restart mid-stream).
        """
        self.last_reasoning_content = ""
        self.last_finish_reason = ""

        candidates = self._segmented_stream_candidates(model_override, tier=tier)
        if not candidates:
            raise RuntimeError("No LLM provider available (segmented stream)")

        for idx, (provider, model) in enumerate(candidates):
            api_key = self._api_key_for(provider)
            config = self._resolve_config(provider)
            config["model"] = model
            self.last_provider_used = provider.value
            self.last_model_used = model
            yielded = False
            try:
                if provider == ModelProvider.GEMINI:
                    async for chunk in self._stream_gemini(
                        prompt,
                        system_prompt,
                        temperature,
                        max_tokens,
                        api_key,
                        config,
                        request_timeout=request_timeout,
                    ):
                        yielded = True
                        yield ("answer", chunk)
                else:
                    async for segment in self._stream_openai_compatible_segmented(
                        provider,
                        prompt,
                        system_prompt,
                        temperature,
                        max_tokens,
                        api_key,
                        config,
                        request_timeout=request_timeout,
                        reasoning_effort=reasoning_effort,
                        tier=tier,
                    ):
                        yielded = True
                        yield segment
                return
            except Exception as exc:
                self._mark_provider_invalid(provider, exc)
                # Once deltas are on the wire we cannot restart cleanly.
                if (
                    yielded
                    or idx == len(candidates) - 1
                    or not self._should_retry_next_provider(exc)
                ):
                    raise
                logger.warning(
                    "Segmented stream %s/%s failed (%s); falling back to %s",
                    provider.value,
                    model,
                    self._format_provider_error(exc),
                    candidates[idx + 1][0].value,
                )

    def _segmented_stream_candidates(
        self, model_override: str | None, *, tier: ModelTier
    ) -> list[tuple[ModelProvider, str]]:
        """Ordered (provider, model) rungs for :meth:`stream_segmented`.

        The override leads (when its provider has a key); the normal attempt
        order supplies the remaining rungs so a dead override still falls
        through to Claude and then Gemini.
        """
        candidates: list[tuple[ModelProvider, str]] = []

        def _add(provider: ModelProvider, model: str) -> None:
            if not self._api_key_for(provider):
                return
            if (provider, model) not in candidates:
                candidates.append((provider, model))

        if model_override:
            _add(*self._resolve_model_override(model_override))
        for provider in self._provider_attempt_order(thinking_mode=True):
            config = self._resolve_config(provider)
            _add(provider, self._model_for_request(config, tier=tier))
        return candidates

    async def _stream_openai_compatible_segmented(
        self,
        provider: ModelProvider,
        prompt: str,
        system_prompt: str | None,
        temperature: float,
        max_tokens: int,
        api_key: str,
        config: dict[str, Any],
        *,
        request_timeout: float | None = None,
        reasoning_effort: str | None = None,
        tier: ModelTier = SYNTHESIS_TIER,
    ) -> AsyncIterator[tuple[Literal["reasoning", "answer"], str]]:
        """OpenAI-compatible streaming that yields tagged reasoning/answer deltas.

        Mirrors :meth:`_stream_openai_compatible` but separates the two delta
        kinds: ``reasoning_content`` → ``("reasoning", …)`` (also accumulated on
        ``last_reasoning_content``), ``content`` → ``("answer", …)``. Honours a
        per-call ``request_timeout`` so the slow synthesis is never cut by the
        shared client timeout.
        """
        client = await self._get_client()
        post_timeout = request_timeout if request_timeout is not None else self.timeout

        async with client.stream(
            "POST",
            f"{config['base_url']}/chat/completions",
            headers=self._openai_compatible_headers(api_key),
            json={
                **self._openai_compatible_payload(
                    provider,
                    prompt,
                    system_prompt,
                    temperature,
                    max_tokens,
                    config,
                    reasoning_effort=self._reasoning_effort_for_request(
                        provider, config, tier=tier, override=reasoning_effort
                    ),
                    tier=tier,
                ),
                "stream": True,
                "stream_options": {"include_usage": True},
            },
            timeout=post_timeout,
        ) as response:
            await self._raise_for_stream_status(response)
            stream_usage: dict[str, Any] | None = None
            reasoning_parts: list[str] = []
            async for line in response.aiter_lines():
                if not line.startswith("data: "):
                    continue
                data = line[6:]
                if data == "[DONE]":
                    break
                try:
                    import json

                    chunk = json.loads(data)
                except json.JSONDecodeError:
                    continue
                if not isinstance(chunk, dict):
                    continue
                chunk_usage = chunk.get("usage")
                if isinstance(chunk_usage, dict):
                    stream_usage = chunk_usage
                # The final usage chunk (include_usage) carries an EMPTY choices
                # list — `[][0]` would raise IndexError and abort the synthesis
                # (dropping the fully-streamed answer → fallback rung). Skip it.
                choices = chunk.get("choices") or []
                if not choices:
                    continue
                # Stash the finish_reason: a "length"-truncated stream with no
                # answer delta is the budget-eaten-by-reasoning signature the
                # synthesis robustness path keys its targeted recovery on.
                finish_reason = choices[0].get("finish_reason")
                if finish_reason:
                    self.last_finish_reason = finish_reason
                delta = choices[0].get("delta", {})
                # Reasoning deltas first (accumulate on the side-channel AND
                # surface live), then answer deltas — NEVER folded together.
                reasoning = delta.get("reasoning_content")
                if reasoning:
                    reasoning_parts.append(reasoning)
                    self.last_reasoning_content = "".join(reasoning_parts)
                    yield ("reasoning", reasoning)
                content = delta.get("content", "")
                if content:
                    yield ("answer", content)
            usage = TokenUsage.from_openai_usage(
                stream_usage,
                model=cast(str, config.get("model") or ""),
                provider=provider.value,
            )
            await self._emit_token_usage(usage)
