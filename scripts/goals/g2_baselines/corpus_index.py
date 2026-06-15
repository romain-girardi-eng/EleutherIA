"""Shared corpus loading + a dependency-free BM25 / FTS index.

Both g2 baselines (``bm25_service`` and ``vanilla_rag_service``) retrieve over
``data/corpus/passages.jsonl`` and must cite REAL ``passage_id`` values so the
eval harness (``tests/eval/run_eval.py``) can score citation P/R/F1 against the
gold ``expected_passages`` and judge ``gold_claims`` with CitationVerifierV2.

The index is intentionally self-contained:

- no ``rank_bm25`` (not installed) — Okapi BM25 implemented in ~40 lines;
- no PostgreSQL — we read the JSONL snapshot directly, which is also what the
  gold annotations were verified against.

Tokenisation is Unicode-aware (keeps Greek/Latin words) and accent-insensitive
for Greek, so a query like "autexousion" still ranks the αὐτεξούσιον passages.
"""

from __future__ import annotations

import json
import math
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

# Repo root = three parents up from this file (scripts/goals/g2_baselines/).
REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CORPUS = REPO_ROOT / "data" / "corpus" / "passages.jsonl"

_TOKEN_RE = re.compile(r"\w+", re.UNICODE)


def _strip_accents(text: str) -> str:
    """Fold diacritics so Greek polytonic matches a bare-stem query."""
    nfd = unicodedata.normalize("NFD", text)
    return "".join(ch for ch in nfd if unicodedata.category(ch) != "Mn")


def tokenize(text: str) -> list[str]:
    """Lowercase, accent-fold, split on Unicode word boundaries."""
    folded = _strip_accents(text.lower())
    return _TOKEN_RE.findall(folded)


@dataclass(frozen=True)
class Passage:
    passage_id: str
    cts_urn: str
    canonical_ref: str
    text_content: str
    work_canonical_id: str


@dataclass(frozen=True)
class ScoredPassage:
    passage: Passage
    score: float


class BM25Index:
    """Okapi BM25 over the passage corpus (k1=1.5, b=0.75)."""

    def __init__(
        self, passages: list[Passage], *, k1: float = 1.5, b: float = 0.75
    ) -> None:
        self.passages = passages
        self.k1 = k1
        self.b = b
        self._docs: list[list[str]] = [tokenize(p.text_content) for p in passages]
        self._doc_len = [len(d) for d in self._docs]
        self._avg_len = (sum(self._doc_len) / len(self._docs)) if self._docs else 0.0

        # term -> document frequency
        self._df: dict[str, int] = {}
        # per-doc term frequency maps
        self._tf: list[dict[str, int]] = []
        for doc in self._docs:
            tf: dict[str, int] = {}
            for term in doc:
                tf[term] = tf.get(term, 0) + 1
            self._tf.append(tf)
            for term in tf:
                self._df[term] = self._df.get(term, 0) + 1

        self._n = len(self._docs)

    def _idf(self, term: str) -> float:
        df = self._df.get(term, 0)
        if df == 0:
            return 0.0
        # BM25 idf with +1 to stay non-negative.
        return math.log(1 + (self._n - df + 0.5) / (df + 0.5))

    def search(self, query: str, k: int = 10) -> list[ScoredPassage]:
        q_terms = tokenize(query)
        if not q_terms or self._n == 0:
            return []
        # De-dupe query terms but keep idf weighting via unique set.
        unique_terms = list(dict.fromkeys(q_terms))
        idf = {t: self._idf(t) for t in unique_terms}

        scored: list[ScoredPassage] = []
        for i, p in enumerate(self.passages):
            tf = self._tf[i]
            dl = self._doc_len[i]
            denom_norm = self.k1 * (1 - self.b + self.b * dl / (self._avg_len or 1))
            score = 0.0
            for term in unique_terms:
                f = tf.get(term, 0)
                if f == 0:
                    continue
                score += idf[term] * (f * (self.k1 + 1)) / (f + denom_norm)
            if score > 0:
                scored.append(ScoredPassage(passage=p, score=score))

        scored.sort(key=lambda s: s.score, reverse=True)
        return scored[:k]


def load_passages(path: Path = DEFAULT_CORPUS) -> list[Passage]:
    """Read the corpus JSONL snapshot into typed records."""
    passages: list[Passage] = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            text = row.get("text_content") or ""
            pid = row.get("passage_id")
            if not pid or not text.strip():
                continue
            passages.append(
                Passage(
                    passage_id=pid,
                    cts_urn=row.get("cts_urn") or "",
                    canonical_ref=row.get("canonical_ref") or "",
                    text_content=text,
                    work_canonical_id=row.get("work_canonical_id") or "",
                )
            )
    return passages


def build_index(path: Path = DEFAULT_CORPUS) -> BM25Index:
    return BM25Index(load_passages(path))
