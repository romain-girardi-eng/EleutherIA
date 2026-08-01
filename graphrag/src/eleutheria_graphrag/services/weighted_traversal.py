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
from typing import Any

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

        Args:
            seed_ids: Starting node IDs.
            edge_filter: If set, only follow edges whose ``relation``
                is in this set.
            max_nodes: Maximum total nodes to visit.
            score_threshold: Stop expanding neighbours below this score.

        Returns:
            Set of visited node IDs (includes seeds).
        """
        visited: set[str] = set()
        # Heap entries: (-score, node_id) — negative because heapq is min-heap
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

        for nid in seed_ids:
            if nid in self.node_lookup:
                visit(nid)
                heapq.heappush(heap, (-1.0, nid))  # Seeds get max score

        while heap and len(visited) < max_nodes:
            neg_score, node_id = heapq.heappop(heap)
            current_score = -neg_score

            if current_score < score_threshold:
                break

            # Expand outgoing edges
            for edge in self.outgoing_edges.get(node_id, []):
                target = edge["target"]
                if target in visited or target not in self.node_lookup:
                    continue
                relation = edge.get("relation", "")
                if edge_filter and relation not in edge_filter:
                    continue
                if community_saturated(target):
                    continue

                neighbour_score = self._score_edge(edge, target, current_score)
                if neighbour_score >= score_threshold:
                    visit(target)
                    heapq.heappush(heap, (-neighbour_score, target))

            # Expand incoming edges
            for edge in self.incoming_edges.get(node_id, []):
                source = edge["source"]
                if source in visited or source not in self.node_lookup:
                    continue
                relation = edge.get("relation", "")
                if edge_filter and relation not in edge_filter:
                    continue
                if community_saturated(source):
                    continue

                neighbour_score = self._score_edge(edge, source, current_score)
                if neighbour_score >= score_threshold:
                    visit(source)
                    heapq.heappush(heap, (-neighbour_score, source))

        logger.debug(
            "WeightedTraversal: %d seeds → %d nodes visited",
            len(seed_ids),
            len(visited),
        )
        return visited

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
