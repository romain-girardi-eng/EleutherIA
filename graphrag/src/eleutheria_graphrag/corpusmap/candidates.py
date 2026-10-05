"""Question-time candidates from the CorpusMap (paper §3.4 and §B.3).

Rank Entity Pages by BM25 over name, type, overview, key facts and aliases,
pool the documents linked to the top pages, rerank the pool by BM25 over
document title and content, and hand the top ones to the agent as file
references only (id + title, no content). In the paper's Table 8 this
"candidate entity-linked docs" setting gives the best quality per token;
without candidates the agent explores the map itself and spends 2.4x the
tokens of the raw-corpus baseline.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from eleutheria_graphrag.corpusmap.bm25 import BM25, tokenize
from eleutheria_graphrag.corpusmap.builder import CorpusMap

# Bulk "corpus holdings" passages are not pooled: a person page would
# otherwise flood the pool with thousands of untranslated passages.
_POOL_CAP_PER_PAGE = 400


@dataclass
class Candidates:
    pages: list[tuple[str, str]]  # (entity_id, label)
    documents: list[tuple[str, str, str]]  # (doc_id, type, title)
    passages: list[tuple[str, str]] = field(default_factory=list)  # (passage_id, title)

    def render(self) -> str:
        lines = [
            "CorpusMap candidates (titles only; read them to see content):",
            "Entity pages:",
        ]
        lines += [f"- {eid} — {label}" for eid, label in self.pages]
        lines.append("Documents linked to those entities:")
        lines += [
            f"- {did} ({dtype}) — {title[:110]}" for did, dtype, title in self.documents
        ]
        if self.passages:
            lines.append("Passages matching the question's wording (full-text search):")
            lines += [
                f"- {pid} (passage) — {title[:110]}" for pid, title in self.passages
            ]
        return "\n".join(lines)


def select_candidates(
    cmap: CorpusMap,
    question: str,
    n_pages: int = 5,
    n_docs: int = 10,
    n_passages: int = 0,
) -> Candidates:
    """Entity pages, their best-matching linked documents and, optionally,
    the ``n_passages`` best full-text passage hits not already listed.

    The passage leg covers what the entity route misses in the deterministic
    A/B: passages named by their locus ("De fato 41"), whose wording the
    question repeats but whose entity pages hold hundreds of documents.
    """
    top_pages = cmap.search_pages(question, k=n_pages)
    pool: list[str] = []
    seen: set[str] = set()
    for eid, _ in top_pages:
        page = cmap.pages[eid]
        for did in (page.facts + page.evidence)[:_POOL_CAP_PER_PAGE]:
            if did not in seen and did in cmap.docs:
                seen.add(did)
                pool.append(did)
    docs: list[tuple[str, str, str]] = []
    if pool:
        index = BM25([tokenize(cmap.docs[d].text) for d in pool])
        for i, _ in index.top(tokenize(question), n_docs):
            d = cmap.docs[pool[i]]
            docs.append((d.doc_id, d.type, d.title))
    passages: list[tuple[str, str]] = []
    if n_passages:
        listed = {d for d, _, _ in docs}
        for pid, _ in cmap.search_passages(question, k=n_passages + len(listed)):
            if pid not in listed and len(passages) < n_passages:
                passages.append((pid, cmap.docs[pid].title))
    return Candidates(
        [(eid, cmap.pages[eid].label) for eid, _ in top_pages], docs, passages
    )
