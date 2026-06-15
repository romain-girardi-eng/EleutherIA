"""Pluggable LLM providers for the vanilla-RAG baseline.

The provider is selected by the ``G2_LLM_PROVIDER`` env var. The code imports
and runs WITHOUT any API key (so the file is testable on a key-less machine):
the default ``extractive`` provider needs no key and just stitches the supplied
context, which keeps the service usable as a deterministic smoke test. Real
providers read the same env keys as the production ``LLMService`` so a machine
already configured for EleutherIA works unchanged.

Providers
---------
- ``extractive``  (default, no key) — returns the context passages joined with
  their ``[P#]`` markers. Lets the harness exercise the full FTS→answer path
  and score citations without burning tokens.
- ``openai``      — any OpenAI-compatible Chat Completions endpoint. Configured
  by ``G2_OPENAI_BASE_URL`` + ``G2_OPENAI_API_KEY`` + ``G2_OPENAI_MODEL``.
  Use this for OpenRouter / Moonshot / Fireworks / local vLLM, etc.
- ``openrouter``  — convenience preset of ``openai`` (OPENROUTER_API_KEY).
- ``moonshot``    — convenience preset of ``openai`` (MOONSHOT_API_KEY, Kimi).
- ``gemini``      — Google Generative Language API (GEMINI_API_KEY).

Each provider exposes ``generate(system, user) -> str``. Network calls use
``httpx`` (already a dependency). No SDKs required.
"""

from __future__ import annotations

import os
from typing import Protocol

import httpx

_TIMEOUT = float(os.environ.get("G2_LLM_TIMEOUT", "120"))


class Provider(Protocol):
    name: str

    def generate(self, system: str, user: str) -> str: ...


class ExtractiveProvider:
    """No-LLM fallback: echo the user prompt's context block verbatim.

    Deterministic and key-free. The user prompt already contains the numbered
    ``[P#]`` context, so returning it keeps every claim trivially grounded in a
    cited passage — a clean retrieval-only floor for the comparison.
    """

    name = "extractive"

    def generate(self, system: str, user: str) -> str:
        marker = "CONTEXT PASSAGES"
        idx = user.find(marker)
        body = user[idx:] if idx != -1 else user
        return (
            "[extractive baseline — no LLM synthesis]\n"
            + body.strip()
        )


class OpenAICompatProvider:
    """OpenAI-compatible /chat/completions (OpenRouter, Moonshot, vLLM, ...)."""

    name = "openai"

    def __init__(self, base_url: str, api_key: str, model: str) -> None:
        if not api_key:
            raise RuntimeError(
                f"{self.name}: missing API key. Set the appropriate *_API_KEY env var."
            )
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model

    def generate(self, system: str, user: str) -> str:
        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0.0,
        }
        headers = {"Authorization": f"Bearer {self.api_key}"}
        with httpx.Client(timeout=_TIMEOUT) as client:
            resp = client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
        return data["choices"][0]["message"]["content"] or ""


class GeminiProvider:
    """Google Generative Language API (generateContent)."""

    name = "gemini"

    def __init__(self, api_key: str, model: str, base_url: str) -> None:
        if not api_key:
            raise RuntimeError("gemini: missing GEMINI_API_KEY.")
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")

    def generate(self, system: str, user: str) -> str:
        url = f"{self.base_url}/models/{self.model}:generateContent"
        payload = {
            "system_instruction": {"parts": [{"text": system}]},
            "contents": [{"role": "user", "parts": [{"text": user}]}],
            "generationConfig": {"temperature": 0.0},
        }
        with httpx.Client(timeout=_TIMEOUT) as client:
            resp = client.post(
                url, json=payload, params={"key": self.api_key}
            )
            resp.raise_for_status()
            data = resp.json()
        candidates = data.get("candidates") or []
        if not candidates:
            return ""
        parts = candidates[0].get("content", {}).get("parts", [])
        return "".join(p.get("text", "") for p in parts)


def build_provider() -> Provider:
    """Instantiate the provider named by ``G2_LLM_PROVIDER`` (default extractive)."""
    name = os.environ.get("G2_LLM_PROVIDER", "extractive").strip().lower()

    if name == "extractive":
        return ExtractiveProvider()

    if name == "openai":
        return OpenAICompatProvider(
            base_url=os.environ.get("G2_OPENAI_BASE_URL", "https://api.openai.com/v1"),
            api_key=os.environ.get("G2_OPENAI_API_KEY", ""),
            model=os.environ.get("G2_OPENAI_MODEL", "gpt-4o-mini"),
        )

    if name == "openrouter":
        return OpenAICompatProvider(
            base_url=os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
            api_key=os.environ.get("OPENROUTER_API_KEY", ""),
            model=os.environ.get("G2_OPENAI_MODEL", "openai/gpt-4o-mini"),
        )

    if name == "moonshot":
        return OpenAICompatProvider(
            base_url=os.environ.get("MOONSHOT_BASE_URL", "https://api.moonshot.ai/v1"),
            api_key=os.environ.get("MOONSHOT_API_KEY", ""),
            model=os.environ.get("G2_OPENAI_MODEL", "kimi-k2-thinking"),
        )

    if name == "gemini":
        return GeminiProvider(
            api_key=os.environ.get("GEMINI_API_KEY", ""),
            model=os.environ.get("G2_OPENAI_MODEL", "gemini-2.5-flash"),
            base_url=os.environ.get(
                "G2_GEMINI_BASE_URL",
                "https://generativelanguage.googleapis.com/v1beta",
            ),
        )

    raise ValueError(
        f"Unknown G2_LLM_PROVIDER={name!r}. "
        "Use one of: extractive, openai, openrouter, moonshot, gemini."
    )
