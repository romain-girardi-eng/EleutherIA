"""
Weighted Graph Traversal — priority-queue BFS with edge/node scoring.

Replaces the naive BFS in the old pipeline with a Dijkstra-like expansion
that considers:
- Edge weights (already stored in DB, previously ignored)
- Edge type relevance (argumentative edges weighted higher for
  philosophical questions)
- Target node centrality (PageRank, pre-computed by KGAnalytics)

The traversal stops when the score drops below a threshold, rather than
at a fixed depth, allowing adaptive exploration.

When nodes carry a ``community_id`` (Leiden/Louvain assignment computed by
KGAnalytics in the knowledge-graph package and copied onto snapshot nodes),
expansion caps how many results may come from any single community so that
retrieval doesn't return a handful of near-duplicate neighbours from one
cluster. ``community_id`` is optional — nodes without it are never capped,
so this is a no-op on snapshots/tests that don't carry community data.
"""

from __future__ import annotations

import heapq
import logging
import time
from typing import Any, NamedTuple

logger = logging.getLogger(__name__)

# Topical-diversity prior: max nodes visited from any single community during
# one expansion. Only enforced for nodes that actually carry a community_id;
# nodes without one (the common case when analytics hasn't been run) are
# never capped.
_COMMUNITY_DIVERSITY_CAP = 4

# ---------------------------------------------------------------------------
# Edge-type relevance multipliers by category
# ---------------------------------------------------------------------------

# Higher multipliers → prefer these edges during traversal
EDGE_CATEGORY_MULTIPLIERS: dict[str, float] = {
    "argumentative": 1.5,  # argues_for, argues_against, refutes, responds_to
    "intellectual": 1.2,  # influences, influenced_by, taught_by, teaches
    "doctrinal": 1.3,  # holds_position, endorses, rejects
    "semantic": 1.1,  # discusses, defines, related_to, contrasts_with
    "authorship": 1.0,  # wrote, authored_by
    "textual": 1.0,  # preserves, preserved_in
    "citation": 0.9,  # cites, cited_by
    "structural": 0.7,  # contains, part_of
    "affiliation": 0.8,  # belongs_to_school, has_member, founded
    "hermeneutic": 0.6,  # interprets, interpreted_by — lower for primary traversal
    "debate": 1.0,  # participates_in, has_participant
    "temporal": 0.5,  # contemporary_of, precedes, follows
}

# Mapping from relation name to category
RELATION_TO_CATEGORY: dict[str, str] = {
    "argues_for": "argumentative",
    "argues_against": "argumentative",
    "refutes": "argumentative",
    "responds_to": "argumentative",
    "influences": "intellectual",
    "influenced_by": "intellectual",
    "taught_by": "intellectual",
    "teaches": "intellectual",
    "belongs_to_school": "affiliation",
    "has_member": "affiliation",
    "founded": "affiliation",
    "founded_by": "affiliation",
    "wrote": "authorship",
    "authored_by": "authorship",
    "cites": "citation",
    "cited_by": "citation",
    "preserves": "textual",
    "preserved_in": "textual",
    "contains": "structural",
    "part_of": "structural",
    "discusses": "semantic",
    "discussed_in": "semantic",
    "defines": "semantic",
    "defined_by": "semantic",
    "related_to": "semantic",
    "contrasts_with": "semantic",
    "holds_position": "doctrinal",
    "endorses": "doctrinal",
    "rejects": "doctrinal",
    "participates_in": "debate",
    "has_participant": "debate",
    "interprets": "hermeneutic",
    "interpreted_by": "hermeneutic",
    "contemporary_of": "temporal",
    "precedes": "temporal",
    "follows": "temporal",
}


class TraversalResult(NamedTuple):
    """Outcome of one bounded expansion.

    ``truncated`` is True whenever the frontier was abandoned before it was
    exhausted — by the node cap or by the wall-clock deadline (``deadline_hit``
    tells the two apart). ``edges_followed`` counts the edges that actually
    admitted a new node. ``order`` lists ``visited`` by priority: the nodes
    popped from the frontier in pop order, then whatever the frontier still
    held, best score first (node id breaks ties) — never the raw edge order.
    """

    visited: set[str]
    edges_followed: int
    truncated: bool
    deadline_hit: bool
    order: list[str]


class WeightedTraversal:
    """Priority-queue graph traversal with edge/node scoring.

    Args:
        node_lookup: Mapping of node_id → node dict.
        outgoing_edges: Mapping of node_id → list of outgoing edge dicts.
        incoming_edges: Mapping of node_id → list of incoming edge dicts.
        pagerank_scores: Pre-computed PageRank scores (node_id → float).
    """

    def __init__(
        self,
        node_lookup: dict[str, dict[str, Any]],
        outgoing_edges: dict[str, list[dict[str, Any]]],
        incoming_edges: dict[str, list[dict[str, Any]]],
        pagerank_scores: dict[str, float] | None = None,
    ) -> None:
        self.node_lookup = node_lookup
        self.outgoing_edges = outgoing_edges
        self.incoming_edges = incoming_edges
        self.pagerank = pagerank_scores or {}

        # Normalise PageRank to [0, 1] for scoring
        if self.pagerank:
            max_pr = max(self.pagerank.values()) or 1.0
            self._norm_pagerank = {
                nid: score / max_pr for nid, score in self.pagerank.items()
            }
        else:
            self._norm_pagerank = {}

    def expand(
        self,
        seed_ids: list[str],
        *,
        edge_filter: set[str] | None = None,
        max_nodes: int = 30,
        score_threshold: float = 0.05,
    ) -> set[str]:
        """Expand from seed nodes using weighted priority-queue BFS.

        Historical FSM contract: seeds are always admitted and a popped node's
        neighbours are admitted together, so the result may overshoot
        ``max_nodes`` by one node's degree. Use :meth:`expand_with_stats` for
        a hard bound.

        Args:
            seed_ids: Starting node IDs.
            edge_filter: If set, only follow edges whose ``relation``
                is in this set.
            max_nodes: Soft cap on the total nodes to visit.
            score_threshold: Stop expanding neighbours below this score.

        Returns:
            Set of visited node IDs (includes seeds).
        """
        return self.expand_with_stats(
            seed_ids,
            edge_filter=edge_filter,
            max_nodes=max_nodes,
            score_threshold=score_threshold,
            strict_cap=False,
        ).visited

    def expand_with_stats(
        self,
        seed_ids: list[str],
        *,
        edge_filter: set[str] | None = None,
        max_nodes: int = 30,
        score_threshold: float = 0.05,
        deadline: float | None = None,
        strict_cap: bool = True,
    ) -> TraversalResult:
        """Same expansion as :meth:`expand`, with bookkeeping and a deadline.

        ``deadline`` is a ``time.monotonic()`` timestamp; it is checked before
        every pop and before every admission, so a long adjacency list cannot
        outlive it. Once it passes, the frontier is abandoned and the nodes
        visited so far are returned with ``deadline_hit`` set.

        ``strict_cap`` (the default) makes ``max_nodes`` a hard bound:
        capacity is checked before every admission, seeds included, and a
        node's neighbours are admitted best score first (node id breaks
        ties), so the visited set does not depend on the order the edges were
        loaded in. ``strict_cap=False`` keeps the historical FSM behaviour
        used by :meth:`expand`: seeds always admitted, neighbours admitted in
        edge order, the cap only checked between pops.
        """
        visited: set[str] = set()
        order: list[str] = []
        edges_followed = 0
        deadline_hit = False
        cap_hit = False
        # Heap entries: (-score, node_id) — negative because heapq is min-heap;
        # the node id is the stable tie-breaker.
        heap: list[tuple[float, str]] = []
        # Community diversity prior: counts only track nodes with a known
        # community_id, so graphs/snapshots without community data never hit
        # the cap (dict.get default keeps this a no-op).
        community_counts: dict[Any, int] = {}

        def visit(node_id: str) -> None:
            visited.add(node_id)
            community = self._community_id(node_id)
            if community is not None:
                community_counts[community] = community_counts.get(community, 0) + 1

        def community_saturated(node_id: str) -> bool:
            community = self._community_id(node_id)
            if community is None:
                return False
            return community_counts.get(community, 0) >= _COMMUNITY_DIVERSITY_CAP

        def deadline_passed() -> bool:
            return deadline is not None and time.monotonic() >= deadline

        for nid in seed_ids:
            if nid not in self.node_lookup or nid in visited:
                continue
            if strict_cap and len(visited) >= max_nodes:
                cap_hit = True
                break
            visit(nid)
            heapq.heappush(heap, (-1.0, nid))  # Seeds get max score

        while heap and not cap_hit and len(visited) < max_nodes:
            if deadline_passed():
                deadline_hit = True
                break
            neg_score, node_id = heapq.heappop(heap)
            current_score = -neg_score

            if current_score < score_threshold:
                heapq.heappush(heap, (neg_score, node_id))
                break
            order.append(node_id)

            candidates = self._candidates(node_id, current_score, visited, edge_filter)
            if strict_cap:
                candidates.sort(key=lambda item: (-item[0], item[1]))
            for neighbour_score, neighbour in candidates:
                if neighbour in visited or neighbour_score < score_threshold:
                    continue
                if community_saturated(neighbour):
                    continue
                if deadline_passed():
                    deadline_hit = True
                    break
                if strict_cap and len(visited) >= max_nodes:
                    cap_hit = True
                    break
                visit(neighbour)
                edges_followed += 1
                heapq.heappush(heap, (-neighbour_score, neighbour))
            if deadline_hit:
                break

        # Whatever the frontier still holds is visited too; list it by
        # priority so ``order`` never reflects the raw edge order.
        order.extend(nid for _neg, nid in sorted(heap))

        # The frontier is only "exhausted" when the heap drained on its own;
        # leaving nodes behind because of the cap or the clock is a truncation.
        truncated = (
            deadline_hit or cap_hit or (bool(heap) and len(visited) >= max_nodes)
        )
        logger.debug(
            "WeightedTraversal: %d seeds → %d nodes visited (%d edges, truncated=%s)",
            len(seed_ids),
            len(visited),
            edges_followed,
            truncated,
        )
        return TraversalResult(visited, edges_followed, truncated, deadline_hit, order)

    def _candidates(
        self,
        node_id: str,
        current_score: float,
        visited: set[str],
        edge_filter: set[str] | None,
    ) -> list[tuple[float, str]]:
        """Score the unvisited neighbours of ``node_id``, outgoing then incoming.

        A neighbour reachable through several edges appears once per edge;
        the admission loop keeps the first one it accepts.
        """
        candidates: list[tuple[float, str]] = []
        for edge in self.outgoing_edges.get(node_id, []):
            target = edge["target"]
            if target in visited or target not in self.node_lookup:
                continue
            if edge_filter and edge.get("relation", "") not in edge_filter:
                continue
            candidates.append((self._score_edge(edge, target, current_score), target))
        for edge in self.incoming_edges.get(node_id, []):
            source = edge["source"]
            if source in visited or source not in self.node_lookup:
                continue
            if edge_filter and edge.get("relation", "") not in edge_filter:
                continue
            candidates.append((self._score_edge(edge, source, current_score), source))
        return candidates

    def _community_id(self, node_id: str) -> Any | None:
        """Return the node's community_id if present, else None.

        Defensive against nodes stored as plain dicts (the normal case) or
        as objects (e.g. Pydantic models) — and against community_id simply
        being absent, which is the expected state until KGAnalytics output
        is threaded into the snapshot.
        """
        node = self.node_lookup.get(node_id)
        if node is None:
            return None
        if isinstance(node, dict):
            return node.get("community_id")
        return getattr(node, "community_id", None)

    def _score_edge(
        self,
        edge: dict[str, Any],
        target_id: str,
        parent_score: float,
    ) -> float:
        """Compute a composite score for traversing an edge.

        ``score = parent_score * edge_weight * type_multiplier * (0.5 + centrality)``

        The 0.5 base ensures nodes with no centrality data still get visited.
        """
        # Edge weight (stored in DB, default 1.0)
        edge_weight = float(edge.get("weight", 1.0))

        # Type relevance multiplier
        relation = edge.get("relation", "")
        category = RELATION_TO_CATEGORY.get(relation, "semantic")
        type_multiplier = EDGE_CATEGORY_MULTIPLIERS.get(category, 1.0)

        # Target node centrality
        centrality = self._norm_pagerank.get(target_id, 0.0)

        # Decay factor so scores decrease with distance
        decay = 0.7

        return parent_score * edge_weight * type_multiplier * (0.5 + centrality) * decay
