"""explore_subgraph tool — PPR-based broad exploration from seed nodes."""

from __future__ import annotations

import logging
from collections import defaultdict, deque
from typing import Any

from pydantic import BaseModel

from eleutheria_graphrag.agents.dependencies import Deps

logger = logging.getLogger(__name__)


class SubgraphNode(BaseModel):
    node_id: str
    label: str
    type: str
    ppr_score: float = 0.0
    distance_from_seed: int = 0


class ExploreSubgraphResult(BaseModel):
    nodes: list[SubgraphNode]
    seed_count: int


class ExploreSubgraphTool:
    """PPR-based broad exploration from seed nodes (HippoRAG-inspired).

    Runs a lightweight Personalized PageRank on the in-memory KG graph
    starting from the given seed nodes. Returns the top-K most relevant
    nodes in the surrounding subgraph. Single step, no LLM calls.
    """

    def __init__(self, deps: Deps) -> None:
        self._deps = deps

    @property
    def name(self) -> str:
        return "explore_subgraph"

    @property
    def description(self) -> str:
        return (
            "Explore the knowledge graph broadly starting from seed nodes. "
            "Uses Personalized PageRank to find the most relevant and connected "
            "nodes in the subgraph surrounding the seeds. Good for discovering "
            "how entities are related when you don't know the exact connections. "
            "No LLM calls — fast single-step exploration."
        )

    @property
    def parameters_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "seed_node_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "1-5 seed node IDs to start exploration from",
                    "minItems": 1,
                    "maxItems": 5,
                },
                "top_k": {
                    "type": "integer",
                    "default": 20,
                    "minimum": 5,
                    "maximum": 50,
                },
            },
            "required": ["seed_node_ids"],
        }

    async def execute(self, args: dict[str, Any]) -> ExploreSubgraphResult:
        seed_ids = args["seed_node_ids"][:5]
        top_k = min(max(args.get("top_k", 20), 5), 50)

        # Validate seeds exist
        valid_seeds = [s for s in seed_ids if s in self._deps.node_lookup]
        if not valid_seeds:
            return ExploreSubgraphResult(nodes=[], seed_count=0)

        # Run lightweight PPR
        scores = self._personalized_pagerank(
            seeds=valid_seeds,
            alpha=0.15,  # Restart probability (standard PPR value)
            max_iterations=20,
            tolerance=1e-6,
        )

        # Compute BFS distance from any seed
        distances = self._bfs_distances(valid_seeds, max_depth=4)

        # Build result, excluding seed nodes themselves
        scored_nodes: list[tuple[SubgraphNode, float]] = []
        for node_id, ppr_score in scores.items():
            if node_id in valid_seeds:
                continue  # Exclude seeds from results
            node = self._deps.node_lookup.get(node_id, {})
            if not node:
                continue
            # Skip passage nodes (too many, not useful at this level)
            if (node.get("type") or "").lower() == "passage":
                continue

            scored_nodes.append(
                (
                    SubgraphNode(
                        node_id=node_id,
                        label=node.get("label", ""),
                        type=node.get("type", ""),
                        ppr_score=round(ppr_score, 6),
                        distance_from_seed=distances.get(node_id, 99),
                    ),
                    ppr_score,
                )
            )

        # Sort by PPR score descending
        scored_nodes.sort(key=lambda x: x[1], reverse=True)
        nodes = [n[0] for n in scored_nodes[:top_k]]

        return ExploreSubgraphResult(
            nodes=nodes,
            seed_count=len(valid_seeds),
        )

    def _personalized_pagerank(
        self,
        seeds: list[str],
        alpha: float = 0.15,
        max_iterations: int = 20,
        tolerance: float = 1e-6,
    ) -> dict[str, float]:
        """Lightweight PPR on the in-memory KG.

        Uses power iteration. The personalization vector is uniform
        over the seed nodes: each seed gets 1/len(seeds).
        """
        # Build adjacency: node_id → list of (neighbor_id, weight)
        all_nodes: set[str] = set()
        adjacency: dict[str, list[tuple[str, float]]] = defaultdict(list)

        for src, edges in self._deps.outgoing_edges.items():
            all_nodes.add(src)
            for edge in edges:
                tgt = edge.get("target", "")
                w = edge.get("weight", 1.0)
                all_nodes.add(tgt)
                adjacency[src].append((tgt, w))

        for tgt, edges in self._deps.incoming_edges.items():
            all_nodes.add(tgt)
            for edge in edges:
                src = edge.get("source", "")
                all_nodes.add(src)
                # Already captured via outgoing

        if not all_nodes:
            return {}

        # Personalization vector
        n_seeds = len(seeds)
        personalization: dict[str, float] = dict.fromkeys(seeds, 1.0 / n_seeds)

        # Initialize scores
        scores: dict[str, float] = {n: personalization.get(n, 0.0) for n in all_nodes}

        # Power iteration
        for _ in range(max_iterations):
            new_scores: dict[str, float] = {}
            max_diff = 0.0

            for node in all_nodes:
                # Teleport component
                rank = alpha * personalization.get(node, 0.0)

                # Walk component: sum of (neighbor_score × edge_weight / out_degree)
                for neighbor, _weight in adjacency.get(node, []):
                    out_degree = len(adjacency.get(neighbor, []))
                    if out_degree > 0:
                        # Reverse direction: score flows FROM neighbor TO node
                        pass

                new_scores[node] = rank

            # Score flows: for each node, distribute its score to neighbors
            for node in all_nodes:
                neighbors = adjacency.get(node, [])
                if not neighbors:
                    # Dangling node: distribute evenly to seeds
                    share = (1.0 - alpha) * scores.get(node, 0.0) / n_seeds
                    for s in seeds:
                        new_scores[s] = new_scores.get(s, 0.0) + share
                else:
                    total_weight = sum(w for _, w in neighbors)
                    if total_weight > 0:
                        for tgt, w in neighbors:
                            share = (
                                (1.0 - alpha) * scores.get(node, 0.0) * w / total_weight
                            )
                            new_scores[tgt] = new_scores.get(tgt, 0.0) + share

            # Convergence check
            max_diff = max(
                abs(new_scores.get(n, 0.0) - scores.get(n, 0.0)) for n in all_nodes
            )
            scores = new_scores

            if max_diff < tolerance:
                break

        return scores

    def _bfs_distances(self, seeds: list[str], max_depth: int = 4) -> dict[str, int]:
        """BFS from seeds to compute shortest distance."""
        distances: dict[str, int] = dict.fromkeys(seeds, 0)
        queue: deque[tuple[str, int]] = deque((s, 0) for s in seeds)

        while queue:
            node_id, depth = queue.popleft()
            if depth >= max_depth:
                continue

            # Expand outgoing + incoming
            for edge in self._deps.outgoing_edges.get(node_id, []):
                tgt = edge.get("target", "")
                if tgt not in distances:
                    distances[tgt] = depth + 1
                    queue.append((tgt, depth + 1))

            for edge in self._deps.incoming_edges.get(node_id, []):
                src = edge.get("source", "")
                if src not in distances:
                    distances[src] = depth + 1
                    queue.append((src, depth + 1))

        return distances
