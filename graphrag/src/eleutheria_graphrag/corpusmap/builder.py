"""Build CorpusMap Entity Pages from the JSONL KG snapshot (no LLM, no DB).

The map is the bipartite graph G = (E ∪ D, L) of the paper: entity nodes
(persons, concepts, works, ...) linked to the document nodes (arguments,
syntheses, publications, passages, ...) that mention them. Entity–entity
edges are deliberately left out of the pages: the paper's ablation (§B.4)
finds they enlarge pages by 27–52% and raise input tokens by up to 28%
while changing document recall by only −2.6 to +0.2 points.
"""

from __future__ import annotations

import json
import re
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from eleutheria_graphrag.corpusmap.bm25 import BM25, tokenize

ENTITY_TYPES = frozenset(
    {
        "person",
        "concept",
        "work",
        "school",
        "debate",
        "controversy",
        "group",
        "position",
        "event",
    }
)
DOCUMENT_TYPES = frozenset(
    {"argument", "synthesis", "publication", "passage", "quote", "conceptual_evolution"}
)
# Structural edges that tie every passage of a work to its work and author.
# They are summarised per work ("corpus holdings") instead of listed one by one.
BULK_RELATIONS = frozenset(
    {"authored_by", "part_of", "has_section", "has_chapter", "contains"}
)
# Same exclusion as the eval snapshot runner: non-exact passage relations are not evidence.
BLOCKED_CITATION_TYPES = frozenset({"related_passage_non_exact"})
_DOC_ORDER = {
    "synthesis": 0,
    "argument": 1,
    "conceptual_evolution": 2,
    "quote": 3,
    "publication": 4,
}
NAME_WEIGHT = 2.0
# Split after a sentence end, but not after "Ch." / "Fat." style abbreviations:
# require the sentence so far to be at least 40 characters.
_SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")


def _first_sentence(text: str, limit: int) -> str:
    text = " ".join((text or "").split())
    head = text
    for m in _SENTENCE_RE.finditer(text):
        if m.start() >= 40:
            head = text[: m.start()]
            break
    return head if len(head) <= limit else head[: limit - 1].rstrip() + "…"


def _aliases(raw: object) -> list[str]:
    if isinstance(raw, list):
        return [str(a) for a in raw if a]
    if isinstance(raw, str) and raw.strip().startswith("["):
        try:
            return [str(a) for a in json.loads(raw) if a]
        except json.JSONDecodeError:
            return []
    return []


@dataclass
class Document:
    doc_id: str
    type: str
    title: str
    text: str  # what BM25 reranks candidates on
    fact: str  # one source-attributed line shown on Entity Pages


@dataclass
class EntityPage:
    entity_id: str
    label: str
    type: str
    aliases: list[str]
    overview: str
    period: str | None
    school: str | None
    facts: list[str] = field(default_factory=list)  # document ids, scholarship first
    evidence: list[str] = field(default_factory=list)  # directly linked passage ids
    holdings: dict[str, list[str]] = field(
        default_factory=dict
    )  # work id -> passage ids

    @property
    def linked_documents(self) -> list[str]:
        out = list(self.facts) + list(self.evidence)
        for pids in self.holdings.values():
            out.extend(pids)
        return out


class CorpusMap:
    def __init__(
        self,
        pages: dict[str, EntityPage],
        docs: dict[str, Document],
        labels: dict[str, str],
    ):
        self.pages = pages
        self.docs = docs
        self.labels = labels
        self.doc_pages: dict[str, list[str]] = defaultdict(list)
        for eid, page in pages.items():
            for did in page.linked_documents:
                self.doc_pages[did].append(eid)
        self._passage_index: BM25 | None = None
        self._passage_ids: list[str] = []
        self._page_ids = list(pages)
        self._page_index = BM25(
            [tokenize(self._page_search_text(pages[e])) for e in self._page_ids]
        )
        # Names get their own index: BM25 length normalisation otherwise buries
        # the richest pages (a person with 300 linked arguments) under thin ones.
        self._name_index = BM25(
            [
                tokenize(" ".join([pages[e].label, *pages[e].aliases]))
                for e in self._page_ids
            ]
        )

    def _page_search_text(self, page: EntityPage) -> str:
        # Name, type, overview, key facts and aliases, as in the paper (§B.3).
        facts = " ".join(self.docs[d].fact for d in page.facts[:60] if d in self.docs)
        names = " ".join([page.label, *page.aliases])
        return f"{names} {names} {page.type} {page.overview} {facts}"

    def search_pages(self, query: str, k: int = 10) -> list[tuple[str, float]]:
        terms = tokenize(query)
        scores = self._page_index.scores(terms)
        for i, s in self._name_index.scores(terms).items():
            scores[i] = scores.get(i, 0.0) + NAME_WEIGHT * s
        ranked = sorted(scores.items(), key=lambda kv: (-kv[1], self._page_ids[kv[0]]))[
            :k
        ]
        return [(self._page_ids[i], s) for i, s in ranked]

    def search_passages(self, query: str, k: int = 5) -> list[tuple[str, float]]:
        """BM25 over every passage document (title, translation, original), built lazily."""
        if self._passage_index is None:
            self._passage_ids = [
                d for d, doc in self.docs.items() if doc.type == "passage"
            ]
            self._passage_index = BM25(
                [tokenize(self.docs[d].text) for d in self._passage_ids]
            )
        return [
            (self._passage_ids[i], s)
            for i, s in self._passage_index.top(tokenize(query), k)
        ]

    def render(
        self,
        entity_id: str,
        focus: str | None = None,
        max_facts: int = 25,
        max_evidence: int = 20,
    ) -> str:
        """Render one Entity Page as compact Markdown.

        ``focus`` ranks the key facts by BM25 against a question so a long page
        (Chrysippus has hundreds of linked arguments) still fits a small budget.
        """
        page = self.pages[entity_id]
        lines = [f"# {page.label} [{page.type}] id={page.entity_id}"]
        meta = [x for x in (page.period, page.school) if x]
        if page.aliases:
            lines.append("aka: " + "; ".join(page.aliases[:8]))
        if meta:
            lines.append(" · ".join(meta))
        lines.append(page.overview)

        fact_ids = [d for d in page.facts if d in self.docs]
        if focus and len(fact_ids) > max_facts:
            local = BM25([tokenize(self.docs[d].text) for d in fact_ids])
            scored = local.scores(tokenize(focus))
            fact_ids = sorted(
                fact_ids, key=lambda d: -scored.get(fact_ids.index(d), 0.0)
            )
        shown = fact_ids[:max_facts]
        lines.append(
            f"\n## Key facts ({len(shown)}/{len(fact_ids)}, each tagged with its source document)"
        )
        lines += [f"- [{d}] {self.docs[d].fact}" for d in shown]

        ev = [p for p in page.evidence if p in self.docs]
        if ev:
            lines.append(
                f"\n## Evidence passages ({min(len(ev), max_evidence)}/{len(ev)})"
            )
            lines += [f"- [{p}] {self.docs[p].fact}" for p in ev[:max_evidence]]
        if page.holdings:
            lines.append("\n## Corpus holdings (passages by work)")
            for wid, pids in sorted(page.holdings.items(), key=lambda kv: -len(kv[1]))[
                :12
            ]:
                refs = [
                    self.docs[p].title for p in pids[:1] + pids[-1:] if p in self.docs
                ]
                lines.append(
                    f"- {self.labels.get(wid, wid)} [{wid}]: {len(pids)} passages ({' … '.join(refs)})"
                )
        return "\n".join(lines)


def _load_jsonl(path: Path):
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                yield json.loads(line)


def build_corpus_map(
    kg_dir: Path | str = "data/kg",
    corpus_dir: Path | str | None = "data/corpus",
    allowed_passages: set[str] | None = None,
) -> CorpusMap:
    """Build the map from the JSONL snapshot (and the passage corpus when present)."""
    kg_dir = Path(kg_dir)
    nodes = list(_load_jsonl(kg_dir / "nodes.jsonl"))
    edges = list(_load_jsonl(kg_dir / "edges.jsonl"))
    passages, manifest, citations = load_corpus(corpus_dir)
    return build_corpus_map_from_rows(
        nodes, edges, passages, manifest, citations, allowed_passages
    )


def load_corpus(
    corpus_dir: Path | str | None,
) -> tuple[list[dict], list[dict], list[dict]]:
    """Read passages, manifest and citations from a corpus export; empty when absent."""
    if not corpus_dir or not (Path(corpus_dir) / "passages.jsonl").exists():
        return [], [], []
    corpus_dir = Path(corpus_dir)

    def rows(name: str) -> list[dict]:
        path = corpus_dir / name
        return list(_load_jsonl(path)) if path.exists() else []

    return rows("passages.jsonl"), rows("manifest.jsonl"), rows("citations.jsonl")


def build_corpus_map_from_rows(
    node_rows: list[dict],
    edges: list[dict],
    passage_rows: list[dict] | None = None,
    manifest_rows: list[dict] | None = None,
    citation_rows: list[dict] | None = None,
    allowed_passages: set[str] | None = None,
) -> CorpusMap:
    """Build the map from in-memory KG rows (DB or snapshot) and optional corpus rows.

    Passage documents are keyed by their corpus ``passage_id`` (the id gold
    sets and citations use); KG passage nodes are folded onto it through the
    ``snapshot_passage_node`` citations. Without corpus rows the KG passage
    nodes themselves are the passage documents. ``allowed_passages`` restricts
    corpus passages to a citable set (the central citability policy).
    """
    nodes = {(n.get("id") or n.get("node_id")): n for n in node_rows}
    labels = {nid: n.get("label") or nid for nid, n in nodes.items()}
    edges = [
        {
            **e,
            "source": e.get("source") or e.get("source_id"),
            "target": e.get("target") or e.get("target_id"),
        }
        for e in edges
    ]
    corpus = {p["passage_id"]: p for p in passage_rows or []}
    if allowed_passages is not None:
        corpus = {k: v for k, v in corpus.items() if k in allowed_passages}
    manifest = {
        m["canonical_id"]: m for m in manifest_rows or [] if m.get("canonical_id")
    }
    citations = [
        c
        for c in citation_rows or []
        if c.get("citation_type") not in BLOCKED_CITATION_TYPES
    ]

    # KG passage node -> corpus passage id.
    canon: dict[str, str] = {}
    for c in citations:
        if c["citation_type"] == "snapshot_passage_node" and c["passage_id"] in corpus:
            canon.setdefault(c["kg_node_id"], c["passage_id"])

    def cid(node_id: str) -> str:
        return canon.get(node_id, node_id)

    work_of: dict[str, str] = {}
    author_of: dict[str, str] = {}
    translation: dict[str, str] = {}
    for e in edges:
        s, t, r = e["source"], e["target"], e["relation"]
        if r == "part_of" and nodes.get(t, {}).get("type") == "work":
            work_of[cid(s)] = t
        elif r == "authored_by" and nodes.get(s, {}).get("type") == "passage":
            author_of[cid(s)] = t
        elif r == "translation_of":
            translation[cid(t)] = s  # target is the original, source its translation

    def trans_text(pid: str) -> str:
        tid = translation.get(pid)
        if not tid:
            return ""
        if tid in canon:
            return corpus[canon[tid]].get("text_content") or ""
        return nodes.get(tid, {}).get("description") or ""

    docs: dict[str, Document] = {}

    def add_passage(pid: str, ref: str, original: str, work_title: str) -> None:
        author = labels.get(author_of.get(pid, ""), "")
        work = labels.get(work_of.get(pid, ""), "") or work_title
        title = " ".join(x for x in (author, work, ref) if x)
        trans = trans_text(pid)
        gloss = _first_sentence(trans or original, 140)
        fact = f"{title} — “{gloss}”" if gloss else title
        docs[pid] = Document(
            pid, "passage", title, f"{title} {trans[:1200]} {original[:600]}", fact
        )

    for pid, p in corpus.items():
        m = manifest.get(p.get("work_canonical_id") or "", {})
        work_title = " ".join(x for x in (m.get("author"), m.get("title")) if x)
        add_passage(
            pid, p.get("canonical_ref") or "", p.get("text_content") or "", work_title
        )

    for nid, n in nodes.items():
        ntype = n.get("type")
        if ntype not in DOCUMENT_TYPES:
            continue
        desc = n.get("description") or ""
        if ntype == "passage":
            if nid in canon or (corpus and allowed_passages is not None):
                continue  # folded onto its corpus passage, or outside the citable set
            add_passage(nid, n.get("label") or "", desc, "")
        else:
            title = n.get("label") or nid
            fact = f"({ntype}) {title}: {_first_sentence(desc, 200)}"
            docs[nid] = Document(nid, ntype, title, f"{title} {desc[:1500]}", fact)

    pages: dict[str, EntityPage] = {}
    for nid, n in nodes.items():
        if n.get("type") in ENTITY_TYPES:
            desc = n.get("description") or ""
            pages[nid] = EntityPage(
                entity_id=nid,
                label=labels[nid],
                type=n["type"],
                aliases=_aliases(n.get("alternative_names")),
                overview=_first_sentence(desc, 600)
                if len(desc) > 600
                else " ".join(desc.split()),
                period=n.get("period"),
                school=n.get("school"),
            )

    facts: dict[str, set[str]] = defaultdict(set)
    evidence: dict[str, set[str]] = defaultdict(set)
    holdings: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    cited_by_doc: dict[str, set[str]] = defaultdict(set)

    def link(ent: str, doc: str, relation: str) -> None:
        if ent not in pages or doc not in docs:
            return
        if docs[doc].type != "passage":
            facts[ent].add(doc)
        elif relation in BULK_RELATIONS:
            holdings[ent][work_of.get(doc, ent)].add(doc)
        else:
            evidence[ent].add(doc)

    for e in edges:
        s, t, r = cid(e["source"]), cid(e["target"]), e["relation"]
        link(s, t, r)
        link(t, s, r)
        if (
            s in docs
            and t in docs
            and docs[t].type == "passage"
            and docs[s].type != "passage"
        ):
            cited_by_doc[s].add(t)
    for c in citations:
        if c["citation_type"] == "snapshot_passage_node":
            continue
        node, pid = c["kg_node_id"], c["passage_id"]
        if node in pages:
            link(node, pid, c["citation_type"])
        elif node in docs and pid in docs:
            cited_by_doc[node].add(pid)

    # A passage that a linked argument or synthesis cites as evidence for the
    # entity is evidence for the entity too (one resolved mention away).
    for eid in pages:
        for doc in list(facts[eid]):
            evidence[eid].update(p for p in cited_by_doc.get(doc, ()) if p in docs)

    kept: dict[str, EntityPage] = {}
    for eid, page in pages.items():
        page.facts = sorted(
            facts[eid], key=lambda d: (_DOC_ORDER.get(docs[d].type, 9), docs[d].title)
        )
        page.evidence = sorted(evidence[eid], key=lambda d: docs[d].title)
        page.holdings = {
            w: sorted(p, key=lambda d: docs[d].title) for w, p in holdings[eid].items()
        }
        # Keep only cross-document entities (linked to >= 2 documents), as in the paper.
        if len(page.linked_documents) >= 2:
            kept[eid] = page
    return CorpusMap(kept, docs, labels)
