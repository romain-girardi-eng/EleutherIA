"""Deterministic, key-free retrieval over the checked-out snapshots.

This is an evaluation baseline, not a production answer path.  It reads the
same corpus/KG JSONL exports that gold identifiers refer to and exposes two
bounded strategies:

``snapshot-lexical``
    Unicode/accent-folded BM25 passages plus lexical KG node matching.

``snapshot-ppr-directed`` / ``snapshot-ppr-bidirectional``
    The same lexical seeds followed by query-personalized PageRank. Directed
    mode follows source→target; bidirectional mode traverses each asserted row
    both ways without fabricating an inverse relation. Linked passages are
    fused with BM25 results.

Neither strategy generates prose or citations.  The caller must therefore
leave generation/citation metrics null rather than crediting retrieval hits as
citations.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import re
import sys
import time
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_PASSAGES = REPO_ROOT / "data" / "corpus" / "passages.jsonl"
DEFAULT_NODES = REPO_ROOT / "data" / "kg" / "nodes.jsonl"
DEFAULT_EDGES = REPO_ROOT / "data" / "kg" / "edges.jsonl"
DEFAULT_CITATIONS = REPO_ROOT / "data" / "corpus" / "citations.jsonl"
DEFAULT_MANIFEST = REPO_ROOT / "data" / "corpus" / "manifest.jsonl"
CENTRAL_CITABILITY_POLICY = (
    REPO_ROOT
    / "graphrag"
    / "src"
    / "eleutheria_graphrag"
    / "agents"
    / "citability.py"
)

SUPPORTED_STRATEGIES = {
    "snapshot-lexical",
    "snapshot-ppr-directed",
    "snapshot-ppr-bidirectional",
}
BLOCKED_CITATION_TYPES = {"related_passage_non_exact"}
_TOKEN_RE = re.compile(r"\w+", re.UNICODE)
_IDENTITY_STOPWORDS = frozenset(
    {"a", "an", "and", "book", "de", "in", "of", "on", "the", "to", "work"}
)

PASSAGE_IDENTITY_FIELDS = (
    "passage_id",
    "manifestation_id",
    "work_canonical_id",
    "work_urn",
    "intellectual_work_cts_urn",
    "canonical_ref",
    "cts_urn",
    "language",
    "translator",
    "translation_label",
    "translation_source",
    "translation_source_doi",
    "translation_type",
    "source",
    "source_language",
    "source_publication_id",
    "publication_id",
    "publication_node_id",
    "source_doi",
    "doi",
    "aligned_to_manifestation",
    "translation_of_work",
)
MANIFEST_IDENTITY_FIELDS = (
    "canonical_id",
    "work_urn",
    "cts_urn",
    "language",
    "translator",
    "translation_label",
    "translation_type",
    "source_publication_id",
    "publication_id",
    "publication_node_id",
    "doi",
    "source",
    "title",
    "author",
    "translation_of_work",
    "aligned_to_manifestation",
)
PROVENANCE_IDENTITY_FIELDS = (
    "kg_node_id",
    "publication_node_id",
    "registry_evidence_id",
    "registry_source_id",
    "translation_label",
    "source_publication_id",
    "source_doi",
    "doi",
    "translator",
)


def load_citability_policy() -> tuple[Any, Any, Any]:
    """Load the true central policy without importing optional GraphRAG deps."""

    module_name = "_eleutheria_eval_snapshot_citability"
    module = sys.modules.get(module_name)
    if module is None:
        spec = importlib.util.spec_from_file_location(
            module_name, CENTRAL_CITABILITY_POLICY
        )
        if spec is None or spec.loader is None:
            raise RuntimeError(
                f"cannot load central citability policy: {CENTRAL_CITABILITY_POLICY}"
            )
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
    return module.CitabilityTier, module.evidence_policy, module.stricter_decision


def _dedup_strings(values: list[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))


def tokenize(text: str) -> list[str]:
    folded = unicodedata.normalize("NFD", text.lower())
    accentless = "".join(
        character
        for character in folded
        if unicodedata.category(character) != "Mn"
    )
    return _TOKEN_RE.findall(accentless)


def _identity_terms(text: str) -> set[str]:
    return {
        term
        for term in tokenize(text)
        if len(term) >= 3 and term not in _IDENTITY_STOPWORDS
    }


def _field_strings(row: dict[str, Any], fields: tuple[str, ...]) -> list[str]:
    values: list[str] = []
    for field in fields:
        value = row.get(field)
        if isinstance(value, str) and value.strip():
            values.append(value)
        elif isinstance(value, (int, float)):
            values.append(str(value))
        elif isinstance(value, list):
            values.extend(str(item) for item in value if str(item).strip())
    return values


def _passage_search_text(
    row: dict[str, Any], manifest_rows: list[dict[str, Any]]
) -> str:
    """Combine text with generic identity/provenance metadata for retrieval."""

    identity = _field_strings(row, PASSAGE_IDENTITY_FIELDS)
    provenance = row.get("provenance")
    if isinstance(provenance, dict):
        identity.extend(_field_strings(provenance, PROVENANCE_IDENTITY_FIELDS))
    for manifest in manifest_rows:
        identity.extend(_field_strings(manifest, MANIFEST_IDENTITY_FIELDS))
    # Identity terms are intentionally weighted above prose terms. This lets a
    # query name an exact manifestation, translator, DOI, or source label while
    # ordinary content queries still use the complete passage text.
    identity_text = " ".join(identity)
    return " ".join(
        (
            str(row.get("text_content") or ""),
            identity_text,
            identity_text,
            identity_text,
        )
    )


@dataclass(frozen=True)
class Passage:
    passage_id: str
    cts_urn: str
    canonical_ref: str
    text_content: str
    work_canonical_id: str
    manifestation_id: str
    language: str
    search_text: str


@dataclass(frozen=True)
class ScoredPassage:
    passage: Passage
    score: float


class BM25Index:
    """Small dependency-free Okapi BM25 implementation."""

    def __init__(
        self, passages: list[Passage], *, k1: float = 1.5, b: float = 0.75
    ) -> None:
        self.passages = passages
        self.k1 = k1
        self.b = b
        documents = [tokenize(passage.search_text) for passage in passages]
        self._lengths = [len(document) for document in documents]
        self._average_length = (
            sum(self._lengths) / len(self._lengths) if self._lengths else 0.0
        )
        self._term_frequencies: list[dict[str, int]] = []
        self._document_frequencies: dict[str, int] = defaultdict(int)
        self._postings: dict[str, list[tuple[int, int]]] = defaultdict(list)
        for index, document in enumerate(documents):
            frequencies: dict[str, int] = defaultdict(int)
            for term in document:
                frequencies[term] += 1
            self._term_frequencies.append(dict(frequencies))
            for term, frequency in frequencies.items():
                self._document_frequencies[term] += 1
                self._postings[term].append((index, frequency))

    def search(self, query: str, *, k: int = 10) -> list[ScoredPassage]:
        terms = list(dict.fromkeys(tokenize(query)))
        count = len(self.passages)
        if not terms or not count:
            return []
        scores: dict[int, float] = defaultdict(float)
        for term in terms:
            postings = self._postings.get(term, ())
            if not postings:
                continue
            document_frequency = self._document_frequencies[term]
            inverse_frequency = math.log(
                1
                + (count - document_frequency + 0.5)
                / (document_frequency + 0.5)
            )
            for index, frequency in postings:
                length = self._lengths[index]
                normalization = self.k1 * (
                    1
                    - self.b
                    + self.b * length / (self._average_length or 1.0)
                )
                scores[index] += (
                    inverse_frequency
                    * frequency
                    * (self.k1 + 1)
                    / (frequency + normalization)
                )
        scored = [
            ScoredPassage(self.passages[index], score)
            for index, score in scores.items()
            if score > 0
        ]
        scored.sort(key=lambda value: (-value.score, value.passage.passage_id))
        return scored[:k]


def _manifest_index(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    index: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        canonical_id = str(row.get("canonical_id") or "")
        if canonical_id:
            index[canonical_id].append(row)
    return dict(index)


def _passages_from_rows(
    passage_rows: list[dict[str, Any]],
    manifest_rows: list[dict[str, Any]],
    *,
    allowed_passage_ids: set[str] | None = None,
) -> list[Passage]:
    passages: list[Passage] = []
    manifests = _manifest_index(manifest_rows)
    for row in passage_rows:
        passage_id = str(row.get("passage_id") or "")
        text = str(row.get("text_content") or "")
        if (
            not passage_id
            or not text.strip()
            or (
                allowed_passage_ids is not None
                and passage_id not in allowed_passage_ids
            )
        ):
            continue
        manifestation_id = str(
            row.get("manifestation_id") or row.get("work_canonical_id") or ""
        )
        manifest_candidates: list[dict[str, Any]] = []
        for identifier in dict.fromkeys(
            (
                manifestation_id,
                str(row.get("work_canonical_id") or ""),
            )
        ):
            manifest_candidates.extend(manifests.get(identifier, []))
        passages.append(
            Passage(
                passage_id=passage_id,
                cts_urn=str(row.get("cts_urn") or ""),
                canonical_ref=str(row.get("canonical_ref") or ""),
                text_content=text,
                work_canonical_id=str(row.get("work_canonical_id") or ""),
                manifestation_id=manifestation_id,
                language=str(row.get("language") or ""),
                search_text=_passage_search_text(row, manifest_candidates),
            )
        )
    return passages


def build_index(path: Path, manifest_path: Path = DEFAULT_MANIFEST) -> BM25Index:
    passage_rows = _read_jsonl(path)
    manifest_rows = _read_jsonl(manifest_path) if manifest_path.is_file() else []
    CitabilityTier, evidence_policy, _stricter_decision = load_citability_policy()
    allowed = {
        str(row.get("passage_id") or "")
        for row in passage_rows
        if evidence_policy(row).tier is CitabilityTier.CITABLE
    }
    return BM25Index(
        _passages_from_rows(
            passage_rows, manifest_rows, allowed_passage_ids=allowed
        )
    )


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                value = json.loads(line)
                if isinstance(value, dict):
                    rows.append(value)
    return rows


def _node_id(row: dict[str, Any]) -> str:
    return str(row.get("node_id") or row.get("id") or "")


def _edge_endpoint(row: dict[str, Any], name: str) -> str:
    return str(row.get(name) or row.get(f"{name}_id") or "")


def _metadata(row: dict[str, Any]) -> dict[str, Any]:
    value = row.get("metadata")
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return {}
        return parsed if isinstance(parsed, dict) else {}
    return {}


def _is_asserted_edge(row: dict[str, Any]) -> bool:
    """Exclude only rows explicitly marked inferred/derived.

    The export currently contains materialized asserted rows without an
    ``asserted`` flag.  Absence of a flag therefore means asserted-for-this-
    snapshot; no inverse or transitive edge is synthesized by this runner.
    """

    metadata = _metadata(row)
    if row.get("asserted") is False or metadata.get("asserted") is False:
        return False
    return not any(
        value is True
        for value in (
            row.get("inferred"),
            row.get("derived"),
            metadata.get("inferred"),
            metadata.get("derived"),
        )
    )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


@dataclass(frozen=True)
class NodeHit:
    node_id: str
    score: float
    node_type: str
    label: str


@dataclass(frozen=True)
class SnapshotRetrieval:
    entity_ids: list[str]
    work_ids: list[str]
    manifestation_ids: list[str]
    passage_ids: list[str]
    latency_ms: float
    trace: dict[str, Any]


class SnapshotIndex:
    """One immutable in-memory view of the corpus and KG exports."""

    def __init__(
        self,
        *,
        passages_path: Path = DEFAULT_PASSAGES,
        nodes_path: Path = DEFAULT_NODES,
        edges_path: Path = DEFAULT_EDGES,
        citations_path: Path = DEFAULT_CITATIONS,
        manifest_path: Path = DEFAULT_MANIFEST,
    ) -> None:
        required = (passages_path, nodes_path, edges_path, citations_path)
        missing = [str(path) for path in required if not path.is_file()]
        if missing:
            raise FileNotFoundError(
                "snapshot retrieval inputs missing: " + ", ".join(missing)
            )

        self.paths = {
            "passages": passages_path,
            "nodes": nodes_path,
            "edges": edges_path,
            "citations": citations_path,
            "manifest": manifest_path,
        }
        self.file_hashes = {
            name: _sha256(path)
            for name, path in self.paths.items()
            if path.is_file()
        }
        snapshot_material = json.dumps(
            self.file_hashes,
            sort_keys=True,
            separators=(",", ":"),
        )
        self.snapshot_sha256 = hashlib.sha256(
            snapshot_material.encode("utf-8")
        ).hexdigest()

        self.CitabilityTier, self._evidence_policy, self._stricter_decision = (
            load_citability_policy()
        )
        self.citability_policy_sha256 = _sha256(CENTRAL_CITABILITY_POLICY)
        manifest_rows = _read_jsonl(manifest_path) if manifest_path.is_file() else []
        node_rows = _read_jsonl(nodes_path)
        self.nodes: dict[str, dict[str, Any]] = {
            _node_id(row): row for row in node_rows if _node_id(row)
        }
        self.node_policy = {
            node_id: self._evidence_policy(row)
            for node_id, row in self.nodes.items()
        }
        citation_rows = _read_jsonl(citations_path)
        snapshot_nodes_by_passage: dict[str, list[str]] = defaultdict(list)
        for row in citation_rows:
            if row.get("citation_type") != "snapshot_passage_node":
                continue
            passage_id = str(row.get("passage_id") or "")
            node_id = str(row.get("kg_node_id") or "")
            if passage_id and node_id and node_id not in snapshot_nodes_by_passage[passage_id]:
                snapshot_nodes_by_passage[passage_id].append(node_id)

        passage_rows = _read_jsonl(passages_path)
        citable_passage_ids: set[str] = set()
        self.passage_exclusions: list[dict[str, Any]] = []
        for row in passage_rows:
            passage_id = str(row.get("passage_id") or "")
            if not passage_id:
                continue
            checks: list[dict[str, Any]] = []
            decisions = []
            passage_decision = self._evidence_policy(row)
            decisions.append(passage_decision)
            checks.append(
                {
                    "scope": "corpus_passage",
                    "tier": str(passage_decision.tier),
                    "reason": passage_decision.reason,
                    "marker": passage_decision.marker,
                }
            )
            for node_id in snapshot_nodes_by_passage.get(passage_id, []):
                node = self.nodes.get(node_id)
                if node is None:
                    continue
                node_decision = self.node_policy[node_id]
                decisions.append(node_decision)
                checks.append(
                    {
                        "scope": "snapshot_node",
                        "node_id": node_id,
                        "tier": str(node_decision.tier),
                        "reason": node_decision.reason,
                        "marker": node_decision.marker,
                    }
                )
            final = self._stricter_decision(*decisions)
            if final.tier is self.CitabilityTier.CITABLE:
                citable_passage_ids.add(passage_id)
                continue
            self.passage_exclusions.append(
                {
                    "passage_id": passage_id,
                    "tier": str(final.tier),
                    "reason": final.reason,
                    "marker": final.marker,
                    "checks": checks,
                }
            )
        self.passage_exclusions.sort(key=lambda row: row["passage_id"])
        self.passage_exclusions_by_id = {
            row["passage_id"]: row for row in self.passage_exclusions
        }
        excluded_passage_ids = set(self.passage_exclusions_by_id)
        self.excluded_passage_index = BM25Index(
            _passages_from_rows(
                passage_rows,
                manifest_rows,
                allowed_passage_ids=excluded_passage_ids,
            )
        )
        self.passage_exclusion_tiers = dict(
            sorted(Counter(row["tier"] for row in self.passage_exclusions).items())
        )
        self.passage_exclusion_markers = dict(
            sorted(
                Counter(row["marker"] for row in self.passage_exclusions).items()
            )
        )
        self.passage_index = BM25Index(
            _passages_from_rows(
                passage_rows,
                manifest_rows,
                allowed_passage_ids=citable_passage_ids,
            )
        )
        self.passages: dict[str, Passage] = {
            passage.passage_id: passage for passage in self.passage_index.passages
        }

        self.non_citable_nodes = sorted(
            (
                {
                    "node_id": node_id,
                    "tier": str(decision.tier),
                    "reason": decision.reason,
                    "marker": decision.marker,
                }
                for node_id, decision in self.node_policy.items()
                if str(self.nodes[node_id].get("type") or "").lower()
                not in {"passage", "quote"}
                and decision.tier is not self.CitabilityTier.CITABLE
            ),
            key=lambda row: row["node_id"],
        )
        self._term_nodes: dict[str, dict[str, float]] = defaultdict(dict)
        self._work_identity_terms: dict[str, tuple[set[str], set[str]]] = {}
        self._build_node_index()

        self.node_passages: dict[str, list[str]] = defaultdict(list)
        for row in citation_rows:
            citation_type = str(row.get("citation_type") or "")
            if citation_type in BLOCKED_CITATION_TYPES:
                continue
            node_id = str(row.get("kg_node_id") or "")
            passage_id = str(row.get("passage_id") or "")
            if (
                node_id
                and passage_id in self.passages
                and passage_id not in self.node_passages[node_id]
            ):
                self.node_passages[node_id].append(passage_id)

        self._edge_rows = _read_jsonl(edges_path)
        self.asserted_edge_count = sum(_is_asserted_edge(row) for row in self._edge_rows)
        self.excluded_inferred_edge_count = len(self._edge_rows) - self.asserted_edge_count
        self._adjacency: dict[
            str, dict[str, list[tuple[str, float]]]
        ] = {}

    def _build_node_index(self) -> None:
        for node_id, row in self.nodes.items():
            if str(row.get("type") or "").lower() in {"passage", "quote"}:
                # Passage text has its own BM25 index.  Indexing it again as a
                # KG entity would dominate seeds and double memory use.
                continue
            metadata = _metadata(row)
            node_type = str(row.get("type") or "").lower()
            label_parts = [
                str(row.get("label") or ""),
                str(row.get("alternative_names") or ""),
                str(metadata.get("work_title") or ""),
                str(metadata.get("author") or ""),
                " ".join(str(value) for value in metadata.get("key_terms", []) or []),
            ]
            description = str(row.get("description") or "")
            weights: dict[str, float] = defaultdict(float)
            for term in tokenize(" ".join(label_parts)):
                weights[term] += 4.0
            for term in tokenize(description):
                weights[term] += 1.0
            for term, weight in weights.items():
                self._term_nodes[term][node_id] = weight
            if node_type == "work":
                self._work_identity_terms[node_id] = (
                    _identity_terms(str(row.get("label") or "")),
                    _identity_terms(
                        str(row.get("author") or metadata.get("author") or "")
                    ),
                )

    def lexical_nodes(
        self,
        query: str,
        *,
        limit: int,
        node_types: set[str] | None = None,
    ) -> list[NodeHit]:
        terms = list(dict.fromkeys(tokenize(query)))
        scores: dict[str, float] = defaultdict(float)
        n_docs = max(1, len(self.nodes))
        for term in terms:
            postings = self._term_nodes.get(term, {})
            if not postings:
                continue
            idf = math.log(1 + n_docs / len(postings))
            for node_id, weight in postings.items():
                scores[node_id] += idf * weight

        query_terms = set(terms)
        for node_id, (title_terms, author_terms) in self._work_identity_terms.items():
            title_overlap = title_terms & query_terms
            author_overlap = author_terms & query_terms
            if title_overlap and author_overlap:
                # An author + title conjunction is a high-precision identity
                # signal (e.g. Alexander + De fato) that generic prose term
                # frequency must not drown out.
                scores[node_id] += (
                    80.0
                    + 20.0 * len(title_overlap) / max(1, len(title_terms))
                    + 20.0 * len(author_overlap) / max(1, len(author_terms))
                )
            elif title_terms and title_terms.issubset(query_terms):
                scores[node_id] += 60.0

        ranked = sorted(scores.items(), key=lambda item: (-item[1], item[0]))
        hits: list[NodeHit] = []
        for node_id, score in ranked:
            row = self.nodes[node_id]
            node_type = str(row.get("type") or "unknown").lower()
            if node_types is not None and node_type not in node_types:
                continue
            hits.append(
                NodeHit(
                    node_id=node_id,
                    score=round(score, 8),
                    node_type=node_type,
                    label=str(row.get("label") or node_id),
                )
            )
            if len(hits) >= limit:
                break
        return hits

    def _ensure_adjacency(
        self, mode: str
    ) -> dict[str, list[tuple[str, float]]]:
        if mode not in {"asserted_directed", "asserted_bidirectional"}:
            raise ValueError(f"unsupported PPR adjacency mode: {mode}")
        if mode in self._adjacency:
            return self._adjacency[mode]
        adjacency: dict[str, list[tuple[str, float]]] = defaultdict(list)
        for row in self._edge_rows:
            if not _is_asserted_edge(row):
                continue
            source = _edge_endpoint(row, "source")
            target = _edge_endpoint(row, "target")
            if not source or not target:
                continue
            try:
                weight = float(row.get("weight") or 1.0)
            except (TypeError, ValueError):
                weight = 1.0
            if weight <= 0:
                weight = 1.0
            adjacency[source].append((target, weight))
            if mode == "asserted_bidirectional":
                # Traversal access in both directions over the SAME asserted
                # row.  This does not assert or emit an inverse relation.
                adjacency[target].append((source, weight))
        for source in adjacency:
            adjacency[source].sort(key=lambda item: item[0])
        self._adjacency[mode] = dict(adjacency)
        return self._adjacency[mode]

    def personalized_pagerank(
        self,
        seeds: list[str],
        *,
        alpha: float = 0.15,
        iterations: int = 20,
        tolerance: float = 1e-9,
        adjacency_mode: str = "asserted_directed",
    ) -> dict[str, float]:
        """Sparse directed PPR with deterministic tie/order behavior."""

        valid = list(dict.fromkeys(seed for seed in seeds if seed in self.nodes))
        if not valid:
            return {}
        adjacency = self._ensure_adjacency(adjacency_mode)
        teleport = 1.0 / len(valid)
        scores = dict.fromkeys(valid, teleport)

        for _ in range(iterations):
            next_scores: dict[str, float] = defaultdict(float)
            for seed in valid:
                next_scores[seed] += alpha * teleport
            for node_id, score in scores.items():
                neighbors = adjacency.get(node_id, [])
                if not neighbors:
                    share = (1.0 - alpha) * score * teleport
                    for seed in valid:
                        next_scores[seed] += share
                    continue
                total_weight = sum(weight for _, weight in neighbors)
                for target, weight in neighbors:
                    next_scores[target] += (
                        (1.0 - alpha) * score * weight / total_weight
                    )
            keys = set(scores) | set(next_scores)
            delta = sum(abs(next_scores.get(k, 0.0) - scores.get(k, 0.0)) for k in keys)
            scores = dict(next_scores)
            if delta < tolerance:
                break
        return scores

    def passage_identity(self, passage_id: str) -> dict[str, Any] | None:
        passage = self.passages.get(passage_id)
        if passage is None:
            return None
        return {
            "passage_id": passage.passage_id,
            "work_canonical_id": passage.work_canonical_id,
            "manifestation_id": passage.manifestation_id,
            "canonical_ref": passage.canonical_ref,
            "cts_urn": passage.cts_urn,
            "language": passage.language,
        }

    def retrieve(
        self,
        query: str,
        *,
        strategy: str,
        passage_k: int = 12,
        node_k: int = 30,
        seed_k: int = 5,
    ) -> SnapshotRetrieval:
        if strategy not in SUPPORTED_STRATEGIES:
            raise ValueError(f"unsupported snapshot strategy: {strategy}")
        if passage_k < 1 or node_k < 1 or seed_k < 1:
            raise ValueError("passage_k, node_k, and seed_k must be positive")

        started = time.perf_counter()
        bm25_hits = self.passage_index.search(query, k=max(passage_k * 2, passage_k))
        exclusion_trace_limit = max(32, passage_k * 2)
        excluded_bm25_hits = self.excluded_passage_index.search(
            query, k=exclusion_trace_limit
        )
        lexical_hits = self.lexical_nodes(query, limit=max(node_k, seed_k))
        # Identity retrieval is its own bounded leg: highly connected argument
        # and concept nodes must not consume every slot before an explicitly
        # named work can enter the work channel. These hits are discovery
        # identities only; passage citability remains governed separately by
        # the central fail-closed evidence policy.
        identity_work_k = min(3, node_k)
        lexical_work_hits = self.lexical_nodes(
            query,
            limit=identity_work_k,
            node_types={"work"},
        )
        selected_hits = lexical_hits[:node_k]
        ppr_trace: list[dict[str, Any]] = []

        if strategy.startswith("snapshot-ppr-"):
            seed_ids = [hit.node_id for hit in lexical_hits[:seed_k]]
            adjacency_mode = (
                "asserted_bidirectional"
                if strategy == "snapshot-ppr-bidirectional"
                else "asserted_directed"
            )
            ppr = self.personalized_pagerank(
                seed_ids, adjacency_mode=adjacency_mode
            )
            ranked_ppr = sorted(ppr.items(), key=lambda item: (-item[1], item[0]))
            ppr_hits: list[NodeHit] = []
            for node_id, score in ranked_ppr:
                row = self.nodes.get(node_id)
                if row is None or str(row.get("type") or "").lower() in {
                    "passage",
                    "quote",
                }:
                    continue
                hit = NodeHit(
                    node_id=node_id,
                    score=round(score, 10),
                    node_type=str(row.get("type") or "unknown").lower(),
                    label=str(row.get("label") or node_id),
                )
                ppr_hits.append(hit)
                ppr_trace.append(
                    {
                        "node_id": hit.node_id,
                        "score": hit.score,
                        "type": hit.node_type,
                        "label": hit.label,
                    }
                )
                if len(ppr_hits) >= node_k:
                    break
            selected_hits = list(
                {
                    hit.node_id: hit
                    for hit in [*lexical_hits[:seed_k], *ppr_hits]
                }.values()
            )[:node_k]

        # Reciprocal-rank fusion keeps lexical passage relevance and graph
        # evidence links visible without pretending their raw scores share a
        # scale.  Stable id tie-breaking makes the result byte-reproducible
        # apart from the explicitly measured latency field.
        fused: dict[str, dict[str, float]] = defaultdict(
            lambda: {"bm25_rr": 0.0, "graph_rr": 0.0}
        )
        for rank, hit in enumerate(bm25_hits, start=1):
            fused[hit.passage.passage_id]["bm25_rr"] = 1.0 / (60 + rank)

        graph_passages: list[str] = []
        for node_rank, hit in enumerate(selected_hits, start=1):
            for passage_rank, passage_id in enumerate(
                self.node_passages.get(hit.node_id, []), start=1
            ):
                graph_passages.append(passage_id)
                fused[passage_id]["graph_rr"] += 1.0 / (
                    60 + node_rank + passage_rank - 1
                )

        fused_ranking = sorted(
            fused.items(),
            key=lambda item: (
                -(item[1]["bm25_rr"] + item[1]["graph_rr"]),
                item[0],
            ),
        )
        lexical_reservation = min(
            len(bm25_hits), max(1, passage_k // 2)
        )
        selected_passage_ids = {
            hit.passage.passage_id for hit in bm25_hits[:lexical_reservation]
        }
        for passage_id, _parts in fused_ranking:
            if len(selected_passage_ids) >= passage_k:
                break
            selected_passage_ids.add(passage_id)
        ranked_passages = [
            item for item in fused_ranking if item[0] in selected_passage_ids
        ][:passage_k]
        passage_ids = [passage_id for passage_id, _ in ranked_passages]

        entity_ids = [
            hit.node_id for hit in selected_hits if hit.node_type != "work"
        ]
        work_ids = _dedup_strings(
            [
                *(hit.node_id for hit in lexical_work_hits),
                *(hit.node_id for hit in selected_hits if hit.node_type == "work"),
            ]
        )[:identity_work_k]
        manifestation_ids = _dedup_strings(
            [
                self.passages[passage_id].manifestation_id
                for passage_id in passage_ids
                if self.passages[passage_id].manifestation_id
            ]
        )

        elapsed_ms = round((time.perf_counter() - started) * 1000.0, 3)
        trace = {
            "strategy": strategy,
            "query": query,
            "config": {
                "passage_k": passage_k,
                "node_k": node_k,
                "seed_k": seed_k,
                "ppr_alpha": 0.15 if strategy.startswith("snapshot-ppr-") else None,
                "ppr_iterations": 20 if strategy.startswith("snapshot-ppr-") else None,
                "adjacency_mode": (
                    "asserted_bidirectional"
                    if strategy == "snapshot-ppr-bidirectional"
                    else "asserted_directed"
                    if strategy == "snapshot-ppr-directed"
                    else None
                ),
                "edge_semantics": (
                    "same asserted export rows; bidirectional mode adds traversal "
                    "access, never an inverse relation"
                ),
                "asserted_edge_count": self.asserted_edge_count,
                "excluded_inferred_edge_count": self.excluded_inferred_edge_count,
                "citability_policy_sha256": self.citability_policy_sha256,
                "lexical_passage_reservation": lexical_reservation,
                "identity_work_k": identity_work_k,
            },
            "evidence_policy": {
                "policy_path": str(CENTRAL_CITABILITY_POLICY.relative_to(REPO_ROOT)),
                "policy_sha256": self.citability_policy_sha256,
                "citable_passage_count": len(self.passages),
                "excluded_passage_count": len(self.passage_exclusions),
                "excluded_passage_tiers": self.passage_exclusion_tiers,
                "excluded_passage_markers": self.passage_exclusion_markers,
                "query_exclusion_trace_limit": exclusion_trace_limit,
                "query_excluded_passage_count": len(excluded_bm25_hits),
                "query_excluded_passage_ids": [
                    hit.passage.passage_id for hit in excluded_bm25_hits
                ],
                "query_excluded_passages": [
                    {
                        **self.passage_exclusions_by_id[hit.passage.passage_id],
                        "lexical_score": round(hit.score, 10),
                    }
                    for hit in excluded_bm25_hits
                ],
                "non_citable_node_count": len(self.non_citable_nodes),
                "non_citable_nodes": self.non_citable_nodes,
            },
            "lexical_nodes": [
                {
                    "node_id": hit.node_id,
                    "score": hit.score,
                    "type": hit.node_type,
                    "label": hit.label,
                }
                for hit in lexical_hits[:node_k]
            ],
            "lexical_work_identities": [
                {
                    "node_id": hit.node_id,
                    "score": hit.score,
                    "type": hit.node_type,
                    "label": hit.label,
                }
                for hit in lexical_work_hits
            ],
            "ppr_nodes": ppr_trace,
            "bm25_passages": [
                {
                    "passage_id": hit.passage.passage_id,
                    "score": round(hit.score, 10),
                    "work_canonical_id": hit.passage.work_canonical_id,
                    "manifestation_id": hit.passage.manifestation_id,
                    "canonical_ref": hit.passage.canonical_ref,
                    "language": hit.passage.language,
                }
                for hit in bm25_hits
            ],
            "graph_linked_passages": list(dict.fromkeys(graph_passages)),
            "fused_passages": [
                {
                    "passage_id": passage_id,
                    "score": round(parts["bm25_rr"] + parts["graph_rr"], 10),
                    **{key: round(value, 10) for key, value in parts.items()},
                    "identity": self.passage_identity(passage_id),
                }
                for passage_id, parts in ranked_passages
            ],
        }
        return SnapshotRetrieval(
            entity_ids=entity_ids,
            work_ids=work_ids,
            manifestation_ids=manifestation_ids,
            passage_ids=passage_ids,
            latency_ms=elapsed_ms,
            trace=trace,
        )


__all__ = [
    "DEFAULT_CITATIONS",
    "DEFAULT_EDGES",
    "DEFAULT_MANIFEST",
    "DEFAULT_NODES",
    "DEFAULT_PASSAGES",
    "SUPPORTED_STRATEGIES",
    "SnapshotIndex",
    "SnapshotRetrieval",
]
