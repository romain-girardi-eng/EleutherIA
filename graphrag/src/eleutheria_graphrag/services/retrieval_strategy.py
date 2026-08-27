"""Retrieval strategies for the DiscoverCorpus FSM node."""

from __future__ import annotations

import logging
import os
import re
import time
from typing import TYPE_CHECKING, Any, NamedTuple, Protocol

from eleutheria_graphrag.services.snapshot_retrieval import node_is_passage

if TYPE_CHECKING:
    from eleutheria_graphrag.services.lemma_expansion import LemmaExpander

logger = logging.getLogger(__name__)

TERM_RE = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿ\u0370-\u03FF\u1F00-\u1FFF']+")
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
RELATED_PASSAGE_CITATION_TYPE = "related_passage_non_exact"

_ALLOWED_PASSAGE_ROLES = {"original", "translation", "paraphrase"}
_PASSAGE_ROLE_ENV = "ELEUTHERIA_PASSAGE_ROLE_FILTER"


def passage_role_condition(alias: str = "p") -> str:
    """SQL predicate restricting primary-text retrieval to one passage role.

    Defaults to ``original`` so translation/paraphrase stub rows never feed
    ancient-text evidence. Override with ``ELEUTHERIA_PASSAGE_ROLE_FILTER``
    (a role name, or ``all`` to disable). The value is validated against a
    closed allowlist before being inlined into SQL.
    """
    role = os.environ.get(_PASSAGE_ROLE_ENV, "original").strip().lower()
    if role in {"", "all", "any", "off"}:
        return "TRUE"
    if role not in _ALLOWED_PASSAGE_ROLES:
        role = "original"
    return f"{alias}.passage_role = '{role}'"


class StepResult(NamedTuple):
    """Hits plus the errors a retrieval step absorbed while producing them."""

    hits: list[str]
    errors: list[str]


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
        # Cached once per strategy instance; None means "not probed yet".
        self._oga_passage_id_capable: bool | None = None

    def deterministic(self) -> SQLStrategy:
        """Same strategy without the LLM lemma expansion (Step 0).

        Used by the graph-seed step, which only consumes seed *nodes*: lemma
        expansion feeds the passage-anchor steps and is the one non-deterministic
        (and slow) part of discovery. The capability probe cache is shared.
        """
        if self._lemma_expander is None:
            return self
        clone = SQLStrategy(min_bundles=self._min_bundles, lemma_expander=None)
        clone._oga_passage_id_capable = self._oga_passage_id_capable
        return clone

    async def discover_seeds(
        self,
        queries: list[str],
        deps: Any,
        node_limit: int = 100,  # noqa: ARG002 — protocol compliance
    ) -> tuple[list[str], list[str]]:
        seed_ids: list[str] = []
        passage_anchor_ids: list[str] = []
        errors: list[str] = []
        state = getattr(deps, "state", None)

        def _finish() -> tuple[list[str], list[str]]:
            # Public contract unchanged — partial failures surface through
            # ``state.metadata['retrieval_errors']`` when a state is attached.
            if errors and state is not None:
                metadata = getattr(state, "metadata", None)
                if isinstance(metadata, dict):
                    metadata.setdefault("retrieval_errors", []).extend(errors)
            return _dedup(seed_ids), _dedup(passage_anchor_ids[:12])

        # Step 0 — lemma expansion (best-effort; falls through silently)
        expanded_terms, expand_errors = await self._expand_lemmas(queries)
        errors.extend(expand_errors)

        # Step 1 — tree routing: if a query mentions a known work/author, pull
        # chapter-level passages directly from the tree before generic search.
        tree_passage_ids, tree_errors = await self._step_tree(queries, deps)
        errors.extend(tree_errors)
        if tree_passage_ids:
            passage_anchor_ids.extend(
                pid for pid in tree_passage_ids if pid not in passage_anchor_ids
            )

        # Step 2 — direct passage_citations via kg_nodes label/description match
        matched_node_ids, label_errors = await self._step_label_match(queries, deps)
        errors.extend(label_errors)
        if matched_node_ids:
            citations, citation_errors = await self._fetch_citations(
                matched_node_ids, deps
            )
            errors.extend(citation_errors)
            seed_ids.extend(matched_node_ids)
            # A non-exact relation remains useful for discovery, but passing its
            # raw passage UUID would lose the relation type in the next stage and
            # accidentally turn it back into quotation evidence.  Keep the KG
            # node as the anchor so passage-row protection can strip its text.
            passage_anchor_ids.extend(
                str(c["kg_node_id"])
                if c.get("citation_type") == RELATED_PASSAGE_CITATION_TYPE
                else str(c["passage_id"])
                for c in citations
            )

            # 1-hop graph expansion from in-memory edges, ontology-aware
            # by default — records inferred (inverseOf) triples in
            # ``deps.state`` when the caller attaches one.
            expanded = self._expand_1hop(matched_node_ids, deps, state=state)
            seed_ids.extend(nid for nid in expanded if nid not in seed_ids)

        if len(passage_anchor_ids) >= self._min_bundles:
            return _finish()

        # Step 3 — lemmatic lookup against oga_tokens using expanded terms
        lemma_passage_ids, lemma_errors = await self._step_lemma_lookup(
            expanded_terms, deps
        )
        errors.extend(lemma_errors)
        passage_anchor_ids.extend(
            pid for pid in lemma_passage_ids if pid not in passage_anchor_ids
        )

        if len(passage_anchor_ids) >= self._min_bundles:
            return _finish()

        # Step 4 — HybridSearch (FTS + lemmatic with RRF)
        if deps.search is not None:
            hybrid_ids, hybrid_errors = await self._step_hybrid_search(queries, deps)
            errors.extend(hybrid_errors)
            seed_ids.extend(nid for nid in hybrid_ids if nid not in seed_ids)
            passage_anchor_ids.extend(
                nid for nid in hybrid_ids if nid not in passage_anchor_ids
            )

        return _finish()

    # ------------------------------------------------------------------
    # Step implementations
    # ------------------------------------------------------------------

    async def _expand_lemmas(self, queries: list[str]) -> StepResult:
        if self._lemma_expander is None:
            return StepResult([], [])
        joined = " ".join(q.strip() for q in queries if q and q.strip())
        if not joined:
            return StepResult([], [])
        try:
            return StepResult(
                await self._lemma_expander.expand(joined, max_lemmas=8), []
            )
        except Exception as exc:
            logger.warning(
                "Lemma expansion failed for queries %r", queries, exc_info=True
            )
            return StepResult([], [f"lemma_expansion: {exc}"])

    async def _step_tree(self, queries: list[str], deps: Any) -> StepResult:
        """Resolve any work/author titles in the query via TreeIndexService.

        Returns a list of passage IDs from the resolved works' opening sections.
        """
        tree = getattr(deps, "tree_index", None)
        if tree is None:
            return StepResult([], [])

        candidates = _author_work_candidates(queries)
        if not candidates:
            return StepResult([], [])

        try:
            work_ids = await tree.resolve_work_ids(candidates)
        except Exception as exc:
            logger.warning("TreeIndex.resolve_work_ids failed", exc_info=True)
            return StepResult([], [f"tree_resolve: {exc}"])

        if not work_ids:
            return StepResult([], [])

        # Surface a handful of passages from each matched work via a direct
        # passage lookup (cheaper than fully loading the tree for a coarse seed).
        placeholders = ", ".join(f"${i + 1}" for i in range(len(work_ids)))
        sql = f"""
            SELECT p.passage_id
            FROM {DB_SCHEMA}.passages p
            WHERE p.work_id::text = ANY(ARRAY[{placeholders}])
              AND {passage_role_condition("p")}
            ORDER BY p.sequence_number
            LIMIT 12
        """
        try:
            rows = await deps.db.fetch(sql, *work_ids)
        except Exception as exc:
            logger.warning("Tree-routed passage fetch failed", exc_info=True)
            return StepResult([], [f"tree_passages: {exc}"])
        return StepResult([str(r["passage_id"]) for r in rows], [])

    async def _step_label_match(self, queries: list[str], deps: Any) -> StepResult:
        """Find kg_nodes matching query terms. Prioritizes label matches over description."""
        errors: list[str] = []
        seen: set[str] = set()
        patterns: list[str] = []
        for q in queries:
            for term in q.split():
                low = term.lower()
                if len(term) >= 3 and low not in seen:
                    seen.add(low)
                    patterns.append(f"%{term}%")
        if not patterns:
            return StepResult([], [])
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
        except Exception as exc:
            logger.warning("SQLStrategy label match failed", exc_info=True)
            errors.append(f"label_match: {exc}")
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
                except Exception as exc:
                    logger.warning(
                        "SQLStrategy description match failed", exc_info=True
                    )
                    errors.append(f"description_match: {exc}")

        return StepResult(result_ids, errors)

    async def _fetch_citations(
        self, node_ids: list[str], deps: Any
    ) -> tuple[list[dict[str, Any]], list[str]]:
        """Fetch passage_citations for given node IDs, ordered by confidence."""
        if not node_ids:
            return [], []

        placeholders = ", ".join(f"${i + 1}" for i in range(len(node_ids)))
        sql = f"""
            SELECT passage_id, kg_node_id, citation_type, confidence
            FROM {DB_SCHEMA}.passage_citations
            WHERE kg_node_id = ANY(ARRAY[{placeholders}])
            ORDER BY confidence DESC
            LIMIT 100
        """
        try:
            return await deps.db.fetch(sql, *node_ids), []
        except Exception as exc:
            logger.warning("SQLStrategy fetch_citations failed", exc_info=True)
            return [], [f"fetch_citations: {exc}"]

    def _expand_1hop(
        self,
        node_ids: list[str],
        deps: Any,
        *,
        ontology_aware: bool = True,
        state: Any | None = None,
    ) -> list[str]:
        """Expand seed nodes by 1 hop using in-memory edge dicts.

        When ``ontology_aware`` is True (default, Phase D activation),
        also include neighbors reachable via the declared inverse of
        each outgoing relation (e.g. for an edge ``A wrote B``, also
        surface targets that A is connected to by ``authored_by``).
        This costs one extra dict lookup per edge — no rdflib graph
        load required at query time, so the perf hit is negligible.

        When ``state`` is supplied and an inferred neighbour is
        materialised by inverseOf, the derived triple is recorded in
        ``state.inferred_edges`` so :class:`DraftClaimLedger` can
        attach a proof chain later. Records the *derived* triple
        ``(node, inverse_relation, neighbour)`` keyed by the inverse
        relation that surfaced it.
        """
        expanded: list[str] = []
        outgoing = getattr(deps, "outgoing_edges", {})
        incoming = getattr(deps, "incoming_edges", {})

        inverse_index: dict[str, str] = {}
        if ontology_aware:
            try:
                from eleutheria_kg.semantic.vocab import CLEAN_INVERSE_PAIRS

                for a, b in CLEAN_INVERSE_PAIRS:
                    inverse_index.setdefault(a, b)
                    inverse_index.setdefault(b, a)
            except Exception:  # noqa: BLE001
                # Semantic layer unavailable — fall back to plain 1-hop.
                inverse_index = {}

        inferred_sink: set[tuple[str, str, str]] | None = None
        if state is not None:
            sink = getattr(state, "inferred_edges", None)
            if isinstance(sink, set):
                inferred_sink = sink

        for nid in node_ids:
            for edge in outgoing.get(nid, []):
                target = edge.get("target") or edge.get("target_id", "")
                if target and target not in expanded:
                    expanded.append(target)
            for edge in incoming.get(nid, []):
                source = edge.get("source") or edge.get("source_id", "")
                if source and source not in expanded:
                    expanded.append(source)

            # Ontology-aware extension: for every asserted edge with a
            # declared inverse, record the inferred reverse triple.
            # Two directions matter:
            #   (a) incoming  (s, rel, nid) ⇒ derived (nid, inv(rel), s)
            #   (b) outgoing  (nid, rel, t) ⇒ derived (t, inv(rel), nid)
            # Plain 1-hop already returns the *neighbours* either way;
            # the ontology-aware layer's job is to surface that the
            # reverse triple exists in the OWL-RL closure so the proof
            # chain consumer can reconstruct it later.
            if inverse_index:
                for edge in incoming.get(nid, []):
                    rel = edge.get("relation", "")
                    derived_rel = inverse_index.get(rel)
                    if not derived_rel:
                        continue
                    source = edge.get("source") or edge.get("source_id", "")
                    if source and source not in expanded:
                        expanded.append(source)
                    if inferred_sink is not None and source:
                        inferred_sink.add((nid, derived_rel, source))
                for edge in outgoing.get(nid, []):
                    rel = edge.get("relation", "")
                    derived_rel = inverse_index.get(rel)
                    if not derived_rel:
                        continue
                    target = edge.get("target") or edge.get("target_id", "")
                    if inferred_sink is not None and target:
                        inferred_sink.add((target, derived_rel, nid))

        return expanded[:50]

    async def _oga_has_passage_id(self, deps: Any) -> bool:
        """Probe (once) whether ``oga_tokens.passage_id`` exists.

        Keeps the code safe to deploy before the
        ``20260610_01_add_passage_id_to_oga_tokens.sql`` migration runs.
        Probe failures are not cached so a transient outage does not pin
        the degraded path for the process lifetime.
        """
        if self._oga_passage_id_capable is not None:
            return self._oga_passage_id_capable
        sql = """
            SELECT 1
            FROM information_schema.columns
            WHERE table_schema = $1
              AND table_name = 'oga_tokens'
              AND column_name = 'passage_id'
        """
        try:
            rows = await deps.db.fetch(sql, DB_SCHEMA)
        except Exception:
            logger.warning(
                "oga_tokens.passage_id capability probe failed", exc_info=True
            )
            return False
        self._oga_passage_id_capable = bool(rows)
        return self._oga_passage_id_capable

    async def _step_lemma_lookup(
        self, expanded_terms: list[str], deps: Any
    ) -> StepResult:
        """Look up passage IDs by lemma stems against ``oga_tokens.lemma``."""
        if not expanded_terms:
            return StepResult([], [])

        # Filter to stems that look indexable. Skip pure stopwords and 1-char items.
        stems = [
            t for t in expanded_terms if len(t) >= 3 and t.lower() not in STOP_TERMS
        ][:16]
        if not stems:
            return StepResult([], [])

        patterns = [f"{stem}%" for stem in stems]
        placeholders = ", ".join(f"${i + 1}" for i in range(len(patterns)))
        role_cond = passage_role_condition("p")

        if await self._oga_has_passage_id(deps):
            # Passage-level anchoring: rank passages by distinct matched lemmas.
            sql = f"""
                SELECT t.passage_id
                FROM {DB_SCHEMA}.oga_tokens t
                JOIN {DB_SCHEMA}.passages p ON p.passage_id = t.passage_id
                WHERE t.lemma ILIKE ANY(ARRAY[{placeholders}])
                  AND {role_cond}
                GROUP BY t.passage_id
                ORDER BY count(DISTINCT t.lemma) DESC
                LIMIT 40
            """
        else:
            logger.warning(
                "oga_tokens.passage_id missing — lemma lookup degrades to a "
                "work-level join returning arbitrary passages per work; apply "
                "migration 20260610_01_add_passage_id_to_oga_tokens.sql"
            )
            sql = f"""
                SELECT DISTINCT p.passage_id
                FROM {DB_SCHEMA}.oga_tokens t
                JOIN {DB_SCHEMA}.passages p ON p.work_id = t.work_id
                WHERE t.lemma ILIKE ANY(ARRAY[{placeholders}])
                  AND {role_cond}
                LIMIT 40
            """
        try:
            rows = await deps.db.fetch(sql, *patterns)
        except Exception as exc:
            logger.warning("SQLStrategy lemma lookup failed", exc_info=True)
            return StepResult([], [f"lemma_lookup: {exc}"])
        return StepResult([str(r["passage_id"]) for r in rows], [])

    async def _step_hybrid_search(self, queries: list[str], deps: Any) -> StepResult:
        """Use HybridSearchService for FTS + lemmatic search."""
        all_ids: list[str] = []
        errors: list[str] = []
        for query in queries[:3]:
            try:
                results = await deps.search.hybrid_search(query, limit=30)
                for r in results:
                    pid = r.get("passage_id") or r.get("id")
                    if pid and pid not in all_ids:
                        all_ids.append(pid)
            except Exception as exc:
                logger.warning(
                    "SQLStrategy hybrid_search failed for %r",
                    query,
                    exc_info=True,
                )
                errors.append(f"hybrid_search[{query!r}]: {exc}")
        return StepResult(all_ids, errors)


class SnapshotStrategy:
    """In-memory retrieval over the loaded KG snapshot."""

    def __init__(self, min_passages: int = 4) -> None:
        self._min_passages = min_passages

    async def discover_seeds(
        self,
        queries: list[str],
        deps: Any,
        node_limit: int = 100,
        *,
        deadline: float | None = None,
    ) -> tuple[list[str], list[str]]:
        """Score every snapshot node against the query terms.

        The scan is CPU-bound with no await point, so a caller's
        ``asyncio.wait_for`` cannot interrupt it: pass a ``time.monotonic()``
        ``deadline`` and the scan stops there, returning what it has scored
        so far (best first). Only the graph-seed step passes one.
        """
        node_lookup = getattr(deps, "node_lookup", {}) or {}
        if not node_lookup:
            return [], []

        query_terms = _query_terms(queries)
        if not query_terms:
            return [], []

        scored: list[tuple[float, str]] = []
        for node_id, node in node_lookup.items():
            if deadline is not None and time.monotonic() >= deadline:
                logger.debug(
                    "SnapshotStrategy: deadline hit after %d nodes", len(scored)
                )
                break
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
    except (TypeError, ValueError) as _exc:
        del _exc
        score = 1.0
    relation = edge.get("relation")
    if relation in {"evidenced_by", "grounded_in", "source_for"}:
        score += 0.3
    elif relation in {"discusses", "part_of", "authored_by"}:
        score += 0.1
    return score
