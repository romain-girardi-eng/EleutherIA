"""Retrieval strategies for the DiscoverCorpus FSM node."""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING, Any, Protocol

from eleutheria_graphrag.services.snapshot_retrieval import node_is_passage

if TYPE_CHECKING:
    from eleutheria_graphrag.services.lemma_expansion import LemmaExpander

logger = logging.getLogger(__name__)

TERM_RE = re.compile(r"[A-Za-zÀ-ÿἀ-῾']+")
STOP_TERMS = {
    "about",
    "after",
    "also",
    "and",
    "avec",
    "dans",
    "des",
    "for",
    "from",
    "how",
    "les",
    "mais",
    "pour",
    "sur",
    "that",
    "the",
    "their",
    "this",
    "what",
    "when",
    "where",
    "which",
    "with",
}


class RetrievalStrategy(Protocol):
    """Interface for corpus discovery — returns seed node IDs and passage anchor IDs."""

    async def discover_seeds(
        self,
        queries: list[str],
        deps: Any,
        node_limit: int = 100,
    ) -> tuple[list[str], list[str]]:
        """Returns (seed_node_ids, passage_anchor_ids)."""
        ...


DB_SCHEMA = "free_will"


def _dedup(items: list[str]) -> list[str]:
    return list(dict.fromkeys(items))


class SQLStrategy:
    """SQL-only retrieval with lemma expansion + tree routing + escalation.

    Pipeline:
        Step 0  — LLM-driven lemma expansion (if a ``LemmaExpander`` is wired).
        Step 1  — Author/work mention → ``TreeIndexService.resolve_work_ids()``
                  then surface chapter-level passages via the tree.
        Step 2  — ``kg_nodes`` label / description match → ``passage_citations``.
        Step 3  — Lemmatic search against ``oga_tokens.lemma`` using the
                  expanded lemma set.
        Step 4  — ``HybridSearchService`` (FTS + lemmatic via RRF).
    """

    def __init__(
        self,
        min_bundles: int = 4,
        lemma_expander: LemmaExpander | None = None,
    ) -> None:
        self._min_bundles = min_bundles
        self._lemma_expander = lemma_expander

    async def discover_seeds(
        self,
        queries: list[str],
        deps: Any,
        node_limit: int = 100,  # noqa: ARG002 — protocol compliance
    ) -> tuple[list[str], list[str]]:
        seed_ids: list[str] = []
        passage_anchor_ids: list[str] = []

        # Step 0 — lemma expansion (best-effort; falls through silently)
        expanded_terms = await self._expand_lemmas(queries)

        # Step 1 — tree routing: if a query mentions a known work/author, pull
        # chapter-level passages directly from the tree before generic search.
        tree_passage_ids = await self._step_tree(queries, deps)
        if tree_passage_ids:
            passage_anchor_ids.extend(
                pid for pid in tree_passage_ids if pid not in passage_anchor_ids
            )

        # Step 2 — direct passage_citations via kg_nodes label/description match
        matched_node_ids = await self._step_label_match(queries, deps)
        if matched_node_ids:
            citations = await self._fetch_citations(matched_node_ids, deps)
            seed_ids.extend(matched_node_ids)
            passage_anchor_ids.extend(c["kg_node_id"] for c in citations)

            # 1-hop graph expansion from in-memory edges
            expanded = self._expand_1hop(matched_node_ids, deps)
            seed_ids.extend(nid for nid in expanded if nid not in seed_ids)

        if len(passage_anchor_ids) >= self._min_bundles:
            return _dedup(seed_ids), _dedup(passage_anchor_ids[:12])

        # Step 3 — lemmatic lookup against oga_tokens using expanded terms
        lemma_passage_ids = await self._step_lemma_lookup(expanded_terms, deps)
        passage_anchor_ids.extend(
            pid for pid in lemma_passage_ids if pid not in passage_anchor_ids
        )

        if len(passage_anchor_ids) >= self._min_bundles:
            return _dedup(seed_ids), _dedup(passage_anchor_ids[:12])

        # Step 4 — HybridSearch (FTS + lemmatic with RRF)
        if deps.search is not None:
            hybrid_ids = await self._step_hybrid_search(queries, deps)
            seed_ids.extend(nid for nid in hybrid_ids if nid not in seed_ids)
            passage_anchor_ids.extend(
                nid for nid in hybrid_ids if nid not in passage_anchor_ids
            )

        return _dedup(seed_ids), _dedup(passage_anchor_ids[:12])

    # ------------------------------------------------------------------
    # Step implementations
    # ------------------------------------------------------------------

    async def _expand_lemmas(self, queries: list[str]) -> list[str]:
        if self._lemma_expander is None:
            return []
        joined = " ".join(q.strip() for q in queries if q and q.strip())
        if not joined:
            return []
        try:
            return await self._lemma_expander.expand(joined, max_lemmas=8)
        except Exception:
            logger.warning(
                "Lemma expansion failed for queries %r", queries, exc_info=True
            )
            return []

    async def _step_tree(self, queries: list[str], deps: Any) -> list[str]:
        """Resolve any work/author titles in the query via TreeIndexService.

        Returns a list of passage IDs from the resolved works' opening sections.
        """
        tree = getattr(deps, "tree_index", None)
        if tree is None:
            return []

        candidates = _author_work_candidates(queries)
        if not candidates:
            return []

        try:
            work_ids = await tree.resolve_work_ids(candidates)
        except Exception:
            logger.warning("TreeIndex.resolve_work_ids failed", exc_info=True)
            return []

        if not work_ids:
            return []

        # Surface a handful of passages from each matched work via a direct
        # passage lookup (cheaper than fully loading the tree for a coarse seed).
        placeholders = ", ".join(f"${i + 1}" for i in range(len(work_ids)))
        sql = f"""
            SELECT passage_id
            FROM {DB_SCHEMA}.passages
            WHERE work_id::text = ANY(ARRAY[{placeholders}])
            ORDER BY sequence_number
            LIMIT 12
        """
        try:
            rows = await deps.db.fetch(sql, *work_ids)
        except Exception:
            logger.warning("Tree-routed passage fetch failed", exc_info=True)
            return []
        return [str(r["passage_id"]) for r in rows]

    async def _step_label_match(self, queries: list[str], deps: Any) -> list[str]:
        """Find kg_nodes matching query terms. Prioritizes label matches over description."""
        seen: set[str] = set()
        patterns: list[str] = []
        for q in queries:
            for term in q.split():
                low = term.lower()
                if len(term) >= 3 and low not in seen:
                    seen.add(low)
                    patterns.append(f"%{term}%")
        if not patterns:
            return []
        patterns = patterns[:30]

        placeholders = ", ".join(f"${i + 1}" for i in range(len(patterns)))

        # Tier 1: Label matches — prioritize person/work nodes, then others.
        # Use a scoring approach: label match on person/work = highest priority.
        sql = f"""
            SELECT node_id, type,
                   CASE WHEN type IN ('person', 'work') THEN 2 ELSE 1 END AS priority
            FROM {DB_SCHEMA}.kg_nodes
            WHERE label ILIKE ANY(ARRAY[{placeholders}])
            ORDER BY priority DESC, length(label) ASC
            LIMIT 50
        """
        try:
            label_rows = await deps.db.fetch(sql, *patterns)
        except Exception:
            logger.warning("SQLStrategy label match failed", exc_info=True)
            label_rows = []

        result_ids = [r["node_id"] for r in label_rows]

        # Tier 2: Only search descriptions if label matches are insufficient.
        if len(result_ids) < self._min_bundles:
            long_patterns = [p for p in patterns if len(p) > 7]
            if long_patterns:
                desc_ph = ", ".join(f"${i + 1}" for i in range(len(long_patterns)))
                desc_sql = f"""
                    SELECT DISTINCT node_id
                    FROM {DB_SCHEMA}.kg_nodes
                    WHERE description ILIKE ANY(ARRAY[{desc_ph}])
                      AND type IN ('person', 'work', 'concept', 'argument', 'school')
                    LIMIT 30
                """
                try:
                    desc_rows = await deps.db.fetch(desc_sql, *long_patterns)
                    for r in desc_rows:
                        if r["node_id"] not in result_ids:
                            result_ids.append(r["node_id"])
                except Exception:
                    logger.warning(
                        "SQLStrategy description match failed", exc_info=True
                    )

        return result_ids

    async def _fetch_citations(
        self, node_ids: list[str], deps: Any
    ) -> list[dict[str, Any]]:
        """Fetch passage_citations for given node IDs, ordered by confidence."""
        if not node_ids:
            return []

        placeholders = ", ".join(f"${i + 1}" for i in range(len(node_ids)))
        sql = f"""
            SELECT passage_id, kg_node_id, confidence
            FROM {DB_SCHEMA}.passage_citations
            WHERE kg_node_id = ANY(ARRAY[{placeholders}])
            ORDER BY confidence DESC
            LIMIT 100
        """
        try:
            return await deps.db.fetch(sql, *node_ids)
        except Exception:
            logger.warning("SQLStrategy fetch_citations failed", exc_info=True)
            return []

    def _expand_1hop(self, node_ids: list[str], deps: Any) -> list[str]:
        """Expand seed nodes by 1 hop using in-memory edge dicts."""
        expanded: list[str] = []
        outgoing = getattr(deps, "outgoing_edges", {})
        incoming = getattr(deps, "incoming_edges", {})
        for nid in node_ids:
            for edge in outgoing.get(nid, []):
                target = edge.get("target") or edge.get("target_id", "")
                if target and target not in expanded:
                    expanded.append(target)
            for edge in incoming.get(nid, []):
                source = edge.get("source") or edge.get("source_id", "")
                if source and source not in expanded:
                    expanded.append(source)
        return expanded[:50]

    async def _step_lemma_lookup(
        self, expanded_terms: list[str], deps: Any
    ) -> list[str]:
        """Look up passage IDs by lemma stems against ``oga_tokens.lemma``."""
        if not expanded_terms:
            return []

        # Filter to stems that look indexable. Skip pure stopwords and 1-char items.
        stems = [
            t for t in expanded_terms if len(t) >= 3 and t.lower() not in STOP_TERMS
        ][:16]
        if not stems:
            return []

        patterns = [f"{stem}%" for stem in stems]
        placeholders = ", ".join(f"${i + 1}" for i in range(len(patterns)))

        sql = f"""
            SELECT DISTINCT p.passage_id
            FROM {DB_SCHEMA}.oga_tokens t
            JOIN {DB_SCHEMA}.passages p ON p.work_id = t.work_id
            WHERE t.lemma ILIKE ANY(ARRAY[{placeholders}])
            LIMIT 40
        """
        try:
            rows = await deps.db.fetch(sql, *patterns)
        except Exception:
            logger.warning("SQLStrategy lemma lookup failed", exc_info=True)
            return []
        return [str(r["passage_id"]) for r in rows]

    async def _step_hybrid_search(self, queries: list[str], deps: Any) -> list[str]:
        """Use HybridSearchService for FTS + lemmatic search."""
        all_ids: list[str] = []
        for query in queries[:3]:
            try:
                results = await deps.search.hybrid_search(query, limit=30)
                for r in results:
                    pid = r.get("passage_id") or r.get("id")
                    if pid and pid not in all_ids:
                        all_ids.append(pid)
            except Exception:
                logger.warning(
                    "SQLStrategy hybrid_search failed for %r",
                    query,
                    exc_info=True,
                )
        return all_ids


class SnapshotStrategy:
    """In-memory retrieval over the loaded KG snapshot."""

    def __init__(self, min_passages: int = 4) -> None:
        self._min_passages = min_passages

    async def discover_seeds(
        self,
        queries: list[str],
        deps: Any,
        node_limit: int = 100,
    ) -> tuple[list[str], list[str]]:
        node_lookup = getattr(deps, "node_lookup", {}) or {}
        if not node_lookup:
            return [], []

        query_terms = _query_terms(queries)
        if not query_terms:
            return [], []

        scored: list[tuple[float, str]] = []
        for node_id, node in node_lookup.items():
            score = self._score_node(node_id, node, query_terms, queries)
            if score <= 0:
                continue
            scored.append((score, node_id))

        scored.sort(key=lambda item: (-item[0], item[1]))

        seeds: list[str] = []
        anchors: list[str] = []
        for _score, node_id in scored:
            if node_id not in seeds:
                seeds.append(node_id)
            if node_is_passage(node_lookup.get(node_id)) and node_id not in anchors:
                anchors.append(node_id)
            elif not node_is_passage(node_lookup.get(node_id)):
                for passage_id in self._linked_passage_ids(deps, node_id):
                    if passage_id not in anchors:
                        anchors.append(passage_id)
                    if len(anchors) >= 12:
                        break

            if len(seeds) >= node_limit and len(anchors) >= self._min_passages:
                break

        # Prefer a compact mix of high-level seeds and direct passage anchors.
        return _dedup(seeds[:node_limit]), _dedup(anchors[:12])

    def _score_node(
        self,
        node_id: str,
        node: dict[str, Any],
        query_terms: list[str],
        queries: list[str],
    ) -> float:
        metadata = (
            node.get("metadata") if isinstance(node.get("metadata"), dict) else {}
        )
        label = str(node.get("label") or "")
        description = str(node.get("description") or "")
        haystack = " ".join(
            str(part or "")
            for part in (
                node_id,
                label,
                description[:2000],
                node.get("type"),
                node.get("period"),
                node.get("school"),
                metadata.get("author"),
                metadata.get("work_title"),
                metadata.get("source_work"),
                metadata.get("canonical_ref"),
                " ".join(str(item) for item in metadata.get("themes", []) or []),
                " ".join(str(item) for item in metadata.get("key_terms", []) or []),
            )
        ).lower()

        score = 0.0
        label_lower = label.lower()
        for query in queries:
            query_lower = query.lower()
            if query_lower and query_lower == label_lower:
                score += 8.0
            elif query_lower and query_lower in label_lower:
                score += 5.0
            elif query_lower and query_lower in haystack:
                score += 3.0

        for term in query_terms:
            if term in label_lower:
                score += 2.0
            elif term in haystack:
                score += 1.0

        node_type = str(node.get("type") or "").lower()
        if node_type in {"person", "concept", "argument", "work", "school"}:
            score *= 1.25
        elif node_type in {"passage", "quote"}:
            score *= 0.95

        return score

    def _linked_passage_ids(self, deps: Any, node_id: str) -> list[str]:
        linked: dict[str, float] = {}
        node_lookup = getattr(deps, "node_lookup", {}) or {}
        for edge in getattr(deps, "outgoing_edges", {}).get(node_id, []):
            target = str(edge.get("target") or "")
            if node_is_passage(node_lookup.get(target)):
                linked[target] = max(_edge_score(edge), linked.get(target, 0.0))
        for edge in getattr(deps, "incoming_edges", {}).get(node_id, []):
            source = str(edge.get("source") or "")
            if node_is_passage(node_lookup.get(source)):
                linked[source] = max(_edge_score(edge), linked.get(source, 0.0))
        return [
            node_id
            for node_id, _score in sorted(
                linked.items(), key=lambda item: (-item[1], item[0])
            )
        ]


def _query_terms(queries: list[str]) -> list[str]:
    terms: list[str] = []
    seen: set[str] = set()
    for query in queries:
        for term in TERM_RE.findall(query):
            low = term.lower()
            if len(low) <= 2 or low in STOP_TERMS or low in seen:
                continue
            seen.add(low)
            terms.append(low)
    return terms[:32]


def _author_work_candidates(queries: list[str]) -> list[str]:
    """Extract probable author/work-title candidates from a query.

    Heuristic: any capitalized word sequence of 1-4 tokens. This is intentionally
    over-inclusive — ``TreeIndexService.resolve_work_ids`` does the real
    title-match in the database.
    """
    candidates: list[str] = []
    seen: set[str] = set()
    pattern = re.compile(r"\b([A-Z][\wÀ-ÿἀ-῾'-]+(?:\s+[A-Z][\wÀ-ÿἀ-῾'-]+){0,3})\b")
    for query in queries:
        for match in pattern.finditer(query):
            value = match.group(1).strip()
            key = value.lower()
            if not value or key in seen or len(value) < 3:
                continue
            seen.add(key)
            candidates.append(value)
    return candidates[:16]


def _edge_score(edge: dict[str, Any]) -> float:
    metadata = edge.get("metadata") if isinstance(edge.get("metadata"), dict) else {}
    raw = metadata.get("confidence", edge.get("weight", metadata.get("weight", 1.0)))
    try:
        score = float(raw)
    except TypeError, ValueError:
        score = 1.0
    relation = edge.get("relation")
    if relation in {"evidenced_by", "grounded_in", "source_for"}:
        score += 0.3
    elif relation in {"discusses", "part_of", "authored_by"}:
        score += 0.1
    return score
