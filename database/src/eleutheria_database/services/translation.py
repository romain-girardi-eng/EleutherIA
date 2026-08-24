"""Passage translation service.

Pure, reusable translation logic extracted from
`database/scripts/batch_translate_passages.py` so that both the CLI script and
the Temporal `translate_passage_batch` activity can call into the same code.

No CLI concerns here — no argparse, no `sys.exit`, no file I/O. Inputs and
outputs are plain Python structures so the activity layer can wrap them in
Temporal's serialization.
"""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from collections.abc import Iterable
from dataclasses import dataclass

# Preferred path: the subscription-backed Gemini proxy (OpenAI-compatible,
# GEMINI_PROXY_BASE_URL/GEMINI_PROXY_API_KEY) — the paid AI Studio API is only
# used when no proxy is configured. TRANSLATION_MODEL overrides either default.
DEFAULT_MODEL = "gemini-2.5-flash"
PROXY_DEFAULT_MODEL = "gemini-3.5-flash-low"
GEMINI_API_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
)


def _proxy_base_url() -> str:
    return os.environ.get("GEMINI_PROXY_BASE_URL", "").strip().rstrip("/")


def resolve_translation_model() -> str:
    """Model id for translation calls: env override, else per-path default."""
    override = os.environ.get("TRANSLATION_MODEL", "").strip()
    if override:
        return override
    return PROXY_DEFAULT_MODEL if _proxy_base_url() else DEFAULT_MODEL


# Batch sizes tuned for Gemini Flash context limits.
DEFAULT_BATCH_SIZE = 10
DEFAULT_MAX_CHARS_PER_BATCH = 40_000

# Priority tiers (work canonical_id patterns). Kept here so the activity can
# resolve a priority code into a concrete list of URN prefixes without
# reaching into the CLI script.
PRIORITY_TIERS: dict[str, list[str]] = {
    "P0": [
        "urn:cts:latinLit:phi0474.phi054",  # Cicero De Fato (Perseus Catalog)
        "urn:cts:greekLit:tlg0557",  # Epictetus
        "urn:cts:greekLit:tlg0732",  # Alexander of Aphrodisias
    ],
    "P1": [
        "oga:tlg0086.tlg010",  # Aristotle NE
        "oga:tlg0086.tlg025",  # Aristotle Met
        "urn:cts:greekLit:tlg0086.tlg007",  # Aristotle DI
        "urn:cts:greekLit:tlg0059.tlg031",  # Plato Timaeus
        "urn:cts:greekLit:tlg0059.tlg004",  # Plato Phaedo
        "urn:cts:greekLit:tlg0059.tlg012",  # Plato Phaedrus
        "urn:cts:greekLit:tlg0007.tlg142",  # Plutarch De Fato
        "urn:cts:greekLit:tlg0007",  # Plutarch (all)
    ],
    "P2": [
        "urn:cts:latinLit:stoa0040.stoa003",  # Augustine DLA
        "urn:cts:latinLit:stoa0040.stoa001",  # Augustine CivDei
        "urn:cts:latinLit:phi2089.phi002",  # Boethius
        "urn:cts:greekLit:tlg2959.tlg001",  # Methodius
    ],
    "P3": [
        "urn:cts:greekLit:tlg0562.tlg001",  # Marcus Aurelius
        "urn:cts:latinLit:phi0550.phi001",  # Lucretius
        "urn:cts:greekLit:tlg0544",  # Sextus Empiricus
        "urn:cts:latinLit:phi1017.phi015",  # Seneca Ep.
    ],
}


@dataclass(frozen=True)
class PassageToTranslate:
    """A single original-language passage queued for translation."""

    node_id: str
    text: str
    language: str = "unknown"
    author: str = ""
    title: str = ""
    ref: str = ""


@dataclass(frozen=True)
class Translation:
    """A successful translation result."""

    node_id: str
    translation: str


@dataclass(frozen=True)
class BatchResult:
    """Outcome of translating a single batch."""

    translations: list[Translation]
    failed_node_ids: list[str]


def resolve_priority(priority: str) -> list[str]:
    """Return the work-canonical-id prefix list for a named priority tier."""
    tiers = PRIORITY_TIERS.get(priority)
    if not tiers:
        raise ValueError(f"Unknown priority tier '{priority}'")
    return list(tiers)


def build_translation_prompt(batch: Iterable[PassageToTranslate]) -> str:
    """Build a single Gemini prompt translating a batch into English."""
    batch_list = list(batch)
    if not batch_list:
        raise ValueError("Cannot build a prompt from an empty batch")

    lang = batch_list[0].language
    lang_name = {
        "grc": "Ancient Greek",
        "lat": "Latin",
        "heb": "Hebrew",
    }.get(lang, lang)

    prompt = (
        f"You are a classical philologist translating {lang_name} passages "
        "into English.\n\n"
        "INSTRUCTIONS:\n"
        "- Translate each passage faithfully into scholarly English\n"
        "- Preserve technical philosophical terms in transliteration where "
        "standard (e.g. heimarmene, pronoia, to eph' hêmin, autexousion)\n"
        "- Do NOT paraphrase, summarize, or add commentary\n"
        "- Do NOT add information not present in the original\n"
        "- For fragmentary or unclear text, translate what is there and mark "
        "lacunae with [...]\n"
        "- Keep the scholarly register appropriate for an academic philosophy "
        "reference work\n\n"
        "OUTPUT FORMAT:\n"
        "Return a JSON array. For each passage, output:\n"
        '{"id": "<node_id>", "en": "<English translation>"}\n\n'
        "PASSAGES TO TRANSLATE:\n"
    )
    for p in batch_list:
        ref_label = f" ({p.ref})" if p.ref else ""
        prompt += f"\n--- {p.node_id}{ref_label} ---\n{p.text}\n"
    return prompt


def call_gemini(prompt: str, api_key: str, model: str | None = None) -> str:
    """Call the translation model and return the text response.

    Prefers the subscription-backed OpenAI-compatible proxy when
    ``GEMINI_PROXY_BASE_URL`` is set; falls back to the native paid API
    otherwise. Kept as a small, synchronous urllib call so this module has no
    third-party HTTP dependency. The Temporal activity wraps this in a thread.
    """
    resolved_model = model or resolve_translation_model()
    proxy_base = _proxy_base_url()
    if proxy_base:
        return _call_openai_compatible(proxy_base, api_key, resolved_model, prompt)
    model = resolved_model
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is required to call the model")

    # API key goes in a header, never the URL — query strings end up in
    # proxy/server logs.
    url = GEMINI_API_URL.format(model=model)
    payload = json.dumps(
        {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": 65536,
                "responseMimeType": "application/json",
                "thinkingConfig": {"thinkingBudget": 0},
            },
        }
    ).encode()

    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": api_key,
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            data = json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.fp else ""
        raise RuntimeError(f"Gemini HTTP {e.code}: {body[:500]}") from e

    try:
        return str(data["candidates"][0]["content"]["parts"][0]["text"])
    except (KeyError, IndexError) as e:
        raise RuntimeError(
            f"Unexpected Gemini response: {json.dumps(data)[:500]}"
        ) from e


def _call_openai_compatible(
    base_url: str, api_key: str, model: str, prompt: str
) -> str:
    """POST the prompt to the proxy's /chat/completions and return the text."""
    if not api_key:
        raise RuntimeError("GEMINI_PROXY_API_KEY is required to call the proxy")
    payload = json.dumps(
        {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1,
            "max_tokens": 65536,
        }
    ).encode()
    req = urllib.request.Request(
        f"{base_url}/chat/completions",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            data = json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.fp else ""
        raise RuntimeError(f"Gemini proxy HTTP {e.code}: {body[:500]}") from e
    try:
        return str(data["choices"][0]["message"]["content"])
    except (KeyError, IndexError) as e:
        raise RuntimeError(
            f"Unexpected proxy response: {json.dumps(data)[:500]}"
        ) from e


def parse_translation_response(text: str) -> list[Translation]:
    """Parse Gemini's JSON response into Translation objects.

    Tolerant of markdown code fences and minor formatting drift; returns an
    empty list if nothing parseable is found.
    """
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
    if text.endswith("```"):
        text = text.rsplit("```", 1)[0]
    text = text.strip()

    items: list[dict] = []
    try:
        parsed = json.loads(text)
        if isinstance(parsed, list):
            items = parsed
    except json.JSONDecodeError:
        start = text.find("[")
        end = text.rfind("]") + 1
        if start >= 0 and end > start:
            try:
                parsed = json.loads(text[start:end])
                if isinstance(parsed, list):
                    items = parsed
            except json.JSONDecodeError:
                items = []
        if not items:
            for m in re.finditer(
                r'\{\s*"id"\s*:\s*"([^"]+)"\s*,\s*"en"\s*:\s*"((?:[^"\\]|\\.)*)"\s*\}',
                text,
            ):
                items.append(
                    {
                        "id": m.group(1),
                        "en": m.group(2).replace('\\"', '"').replace("\\n", "\n"),
                    }
                )

    results: list[Translation] = []
    for item in items:
        node_id = item.get("id", "") if isinstance(item, dict) else ""
        translation = item.get("en", "") if isinstance(item, dict) else ""
        if node_id and translation:
            results.append(Translation(node_id=node_id, translation=translation))
    return results


def batch_passages(
    passages: Iterable[PassageToTranslate],
    batch_size: int = DEFAULT_BATCH_SIZE,
    max_chars_per_batch: int = DEFAULT_MAX_CHARS_PER_BATCH,
) -> list[list[PassageToTranslate]]:
    """Split passages into prompt-sized batches respecting both length limits."""
    batches: list[list[PassageToTranslate]] = []
    current: list[PassageToTranslate] = []
    current_chars = 0

    for p in passages:
        text_len = len(p.text)
        if current and (
            len(current) >= batch_size or current_chars + text_len > max_chars_per_batch
        ):
            batches.append(current)
            current = []
            current_chars = 0
        current.append(p)
        current_chars += text_len

    if current:
        batches.append(current)
    return batches


def translate_batch(
    batch: list[PassageToTranslate],
    api_key: str,
    model: str = DEFAULT_MODEL,
) -> BatchResult:
    """Translate a single prepared batch and report any missing node_ids."""
    if not batch:
        return BatchResult(translations=[], failed_node_ids=[])

    prompt = build_translation_prompt(batch)
    response_text = call_gemini(prompt, api_key, model=model)
    translations = parse_translation_response(response_text)

    returned = {t.node_id for t in translations}
    expected = {p.node_id for p in batch}
    missing = sorted(expected - returned)
    return BatchResult(translations=translations, failed_node_ids=missing)


def get_api_key_from_env() -> str:
    """Key resolver: the proxy bearer key when proxied, else `GEMINI_API_KEY`."""
    if _proxy_base_url():
        key = os.environ.get("GEMINI_PROXY_API_KEY", "")
        if not key:
            raise RuntimeError(
                "GEMINI_PROXY_BASE_URL is set but GEMINI_PROXY_API_KEY is not"
            )
        return key
    key = os.environ.get("GEMINI_API_KEY", "")
    if not key:
        raise RuntimeError("GEMINI_API_KEY is not set in the environment")
    return key


__all__ = [
    "DEFAULT_MODEL",
    "DEFAULT_BATCH_SIZE",
    "DEFAULT_MAX_CHARS_PER_BATCH",
    "PRIORITY_TIERS",
    "PassageToTranslate",
    "Translation",
    "BatchResult",
    "resolve_priority",
    "build_translation_prompt",
    "call_gemini",
    "parse_translation_response",
    "batch_passages",
    "translate_batch",
    "get_api_key_from_env",
]
