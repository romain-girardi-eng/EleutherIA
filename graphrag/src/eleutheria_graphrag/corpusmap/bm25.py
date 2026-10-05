"""Dependency-free Okapi BM25 used to rank Entity Pages and candidate documents."""

from __future__ import annotations

import math
import re
import unicodedata
from collections import Counter
from collections.abc import Sequence

_TOKEN_RE = re.compile(r"[^\W_]+", re.UNICODE)

# Small bilingual stop list: the queries are English or French, the KG text is
# mostly English with Greek and Latin terms that must survive tokenization.
_STOP = frozenset(
    [
        "a",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "by",
        "de",
        "des",
        "du",
        "for",
        "from",
        "has",
        "how",
        "in",
        "is",
        "it",
        "its",
        "la",
        "le",
        "les",
        "of",
        "on",
        "or",
        "que",
        "qui",
        "sa",
        "ses",
        "son",
        "that",
        "the",
        "their",
        "this",
        "to",
        "un",
        "une",
        "was",
        "what",
        "which",
        "who",
        "with",
        "does",
        "did",
        "do",
        "dans",
        "et",
        "en",
        "est",
        "il",
        "ils",
        "sur",
        "au",
        "aux",
        "par",
        "pour",
        "ce",
        "cette",
        "quel",
        "quelle",
    ]
)


def _fold(text: str) -> str:
    """Lowercase and strip diacritics so 'eph' hêmin' and polytonic accents match."""
    decomposed = unicodedata.normalize("NFD", text.lower())
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch))


def tokenize(text: str) -> list[str]:
    return [
        t for t in _TOKEN_RE.findall(_fold(text or "")) if len(t) > 1 and t not in _STOP
    ]


class BM25:
    def __init__(
        self, docs: Sequence[Sequence[str]], k1: float = 1.2, b: float = 0.75
    ) -> None:
        self.k1, self.b = k1, b
        self.tf = [Counter(d) for d in docs]
        self.len = [len(d) for d in docs]
        self.avgdl = (sum(self.len) / len(self.len)) if self.len else 0.0
        df: Counter[str] = Counter()
        for c in self.tf:
            df.update(c.keys())
        n = len(docs)
        self.idf = {t: math.log(1 + (n - f + 0.5) / (f + 0.5)) for t, f in df.items()}
        self.postings: dict[str, list[int]] = {}
        for i, c in enumerate(self.tf):
            for t in c:
                self.postings.setdefault(t, []).append(i)

    def scores(self, query: Sequence[str]) -> dict[int, float]:
        out: dict[int, float] = {}
        for t in set(query):
            idf = self.idf.get(t)
            if idf is None:
                continue
            for i in self.postings[t]:
                f = self.tf[i][t]
                norm = f + self.k1 * (
                    1 - self.b + self.b * self.len[i] / (self.avgdl or 1)
                )
                out[i] = out.get(i, 0.0) + idf * f * (self.k1 + 1) / norm
        return out

    def top(self, query: Sequence[str], k: int) -> list[tuple[int, float]]:
        return sorted(self.scores(query).items(), key=lambda kv: -kv[1])[:k]
