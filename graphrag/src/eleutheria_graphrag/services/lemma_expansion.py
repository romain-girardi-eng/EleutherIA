"""LLM-driven lemma expansion for vectorless retrieval.

Takes a natural-language query (e.g. "voluntary action in Aristotle") and
returns a small set of ancient Greek / Latin lemma stems plus English
semantic neighbors. The result feeds the lemmatic-search leg of
``SQLStrategy``, compensating for the loss of vector paraphrase coverage.

The expansion is intentionally compact (default <= 8 entries) so it can
be merged into existing FTS / lemma queries without blowing up the SQL
planner's predicate count. Results are cached in-process by raw query
string.
"""

from __future__ import annotations

import json
import logging
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from eleutheria_graphrag.services.llm_service import LLMService

logger = logging.getLogger(__name__)


_SYSTEM_PROMPT = """You are a classical-philology assistant for an ancient
philosophy knowledge graph (Greek and Latin, 6th c. BCE - 6th c. CE,
covering free will, fate, moral responsibility).

Given a user query, return a JSON object with a single key "lemmas".
The value is an array of short stems / forms (1-4 words each) that
together cover the query's semantic field. Mix:

- Greek lemma stems in polytonic Greek (e.g. "hekousi", "prohaires",
  "boul", "eph hemin", "autexous", "syn katathes"). Truncate to the
  invariant stem; do not add inflectional endings.
- Latin lemma stems where natural (e.g. "volunt", "liber arbitr",
  "fatum").
- English semantic neighbors of the query (e.g. for "voluntary
  action": "voluntary", "deliberate", "choice", "responsibility").

Hard rules:
- Return between 3 and the requested max number of lemmas.
- Do NOT invent ancient text. Lemmas are search keys, never quotations.
- No diacritics-stripping when you do use Greek script — keep polytonic.
- No explanation, no prose. JSON only.

Example output for "voluntary action in Aristotle":
{"lemmas": ["hekousi", "prohaires", "boul", "akon", "voluntary",
"deliberation", "choice"]}
"""


_JSON_BLOCK_RE = re.compile(r"\{.*\}", re.DOTALL)


class LemmaExpander:
    """LLM-driven query → lemma-set expander with in-process caching."""

    def __init__(self, llm: LLMService) -> None:
        self._llm = llm
        self._cache: dict[tuple[str, int], list[str]] = {}

    async def expand(self, query: str, max_lemmas: int = 8) -> list[str]:
        """Return the original query tokens plus LLM-derived lemma stems.

        The original query tokens are always included so callers can use the
        result as a drop-in replacement for naive whitespace tokenization.
        On any LLM failure, returns just the original tokens.
        """
        normalized = " ".join(query.strip().split())
        if not normalized:
            return []

        key = (normalized.lower(), max_lemmas)
        cached = self._cache.get(key)
        if cached is not None:
            return cached

        original_tokens = [t for t in normalized.split() if len(t) >= 2]
        lemmas: list[str] = []

        try:
            raw = await self._llm.generate(
                prompt=f'Query: "{normalized}"\nMax lemmas: {max_lemmas}',
                system_prompt=_SYSTEM_PROMPT,
                temperature=0.1,
                max_tokens=512,
                response_mime_type="application/json",
            )
            lemmas = self._parse_lemmas(raw, max_lemmas)
        except Exception:
            logger.warning(
                "LemmaExpander LLM call failed for %r — falling back to tokens",
                normalized,
                exc_info=True,
            )

        merged = _dedup_preserving_order(original_tokens + lemmas)
        # Hard cap including original tokens so SQL ANY() arrays stay sane.
        merged = merged[: max(max_lemmas * 2, len(original_tokens) + 1)]

        self._cache[key] = merged
        return merged

    @staticmethod
    def _parse_lemmas(raw: str, max_lemmas: int) -> list[str]:
        if not raw:
            return []
        text = raw.strip()
        match = _JSON_BLOCK_RE.search(text)
        if not match:
            return []
        try:
            parsed = json.loads(match.group(0))
        except json.JSONDecodeError:
            return []
        if not isinstance(parsed, dict):
            return []
        items = parsed.get("lemmas")
        if not isinstance(items, list):
            return []

        cleaned: list[str] = []
        for item in items:
            if not isinstance(item, str):
                continue
            token = item.strip()
            if not token or len(token) < 2:
                continue
            cleaned.append(token)
            if len(cleaned) >= max_lemmas:
                break
        return cleaned


def _dedup_preserving_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        key = item.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out
