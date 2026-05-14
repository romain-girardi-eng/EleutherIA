"""infer_transitive tool — ontology-aware transitive + inverse retrieval.

Given a starting node and a relation, returns all nodes reachable by
repeated application of the relation, plus the inverse-direction
neighbors when the ontology declares an inverse pair (e.g. ``part_of``
↔ ``contains``, ``wrote`` ↔ ``authored_by``).

Implementation note
-------------------
The Deps container already exposes ``outgoing_edges`` and
``incoming_edges`` dicts loaded from the canonical KG. For pure BFS
closure these are strictly faster than rebuilding an rdflib graph at
query time. We therefore avoid the rdflib path here and rely on the
inverse-pair declarations from :mod:`eleutheria_kg.semantic.vocab` to
know which relations to treat as ontology-inverse.

The ReAct tool's promise to the agent — "all part_of ancestors" — is
satisfied by following the ``part_of`` relation outgoing repeatedly,
and also by following its declared inverse ``contains`` incoming
repeatedly. Same logic for ``wrote`` / ``authored_by``.
"""

from __future__ import annotations

import logging
from collections import deque
from typing import Any

from pydantic import BaseModel, Field

from eleutheria_graphrag.agents.dependencies import Deps

logger = logging.getLogger(__name__)


# Build the inverse-pair index lazily; importing the kg package at module
# import time would be fine but the symmetric expansion below uses dicts
# of strings, not rdflib IRIs.
def _build_inverse_index() -> dict[str, str]:
    """Return a dict mapping each relation name to its declared inverse.

    Honors both directions of CLEAN_INVERSE_PAIRS. If a relation has no
    declared inverse, it is absent from the dict.
    """
    from eleutheria_kg.semantic.vocab import CLEAN_INVERSE_PAIRS

    index: dict[str, str] = {}
    for a, b in CLEAN_INVERSE_PAIRS:
        index.setdefault(a, b)
        index.setdefault(b, a)
    return index


_INVERSE_INDEX: dict[str, str] = _build_inverse_index()


# Relations the semantic layer treats as transitive. Must stay in sync
# with eleutheria_kg.semantic.inference._TRANSITIVE_PROPERTIES.
_TRANSITIVE_RELATIONS: frozenset[str] = frozenset(
    {"part_of", "contains", "belongs_to_corpus", "has_section", "has_chapter"}
)


class DerivedNode(BaseModel):
    node_id: str
    label: str
    type: str
    distance: int = Field(..., ge=1, description="Hop count from the start node")
    derivation: list[str] = Field(
        default_factory=list,
        description="Sequence of (relation, direction) labels traversed",
    )


class InferTransitiveResult(BaseModel):
    start_node_id: str
    start_label: str
    relation: str
    inverse_relation: str | None = None
    is_transitive: bool
    max_depth: int
    derived_nodes: list[DerivedNode]
    truncated: bool = Field(
        False, description="True if the BFS hit a per-call node cap"
    )


# A reasonable safety cap so the tool can't return 10k descendants of a
# corpus root in a single call. The agent can paginate by narrowing the
# relation or by calling get_neighbors directly.
_RESULT_CAP: int = 200


class InferTransitiveFactsTool:
    """Infer transitive facts from the knowledge graph.

    Given a node and a relation (e.g. ``part_of``, ``contains``,
    ``member_of``, ``authored_by``), returns all nodes reachable via
    repeated application of the relation, plus any inferred inverses.
    Use when asked for indirect chains like 'all works by author X' or
    'all passages within work Y'.
    """

    def __init__(self, deps: Deps) -> None:
        self._deps = deps

    @property
    def name(self) -> str:
        return "infer_transitive"

    @property
    def description(self) -> str:
        return (
            "Infer transitive facts from the knowledge graph. Given a node "
            "and a relation (e.g. part_of, contains, member_of, authored_by, "
            "wrote), returns all nodes reachable via repeated application "
            "of the relation plus any inverse-of neighbors declared in the "
            "ontology. Use this when the question is about indirect chains "
            "such as 'all works by author X', 'all passages within work Y', "
            "or 'every school that descends from school Z'. Transitive "
            "relations supported: part_of, contains, belongs_to_corpus, "
            "has_section, has_chapter. For non-transitive relations, returns "
            "the 1-hop outgoing + inverse-incoming neighbors."
        )

    @property
    def parameters_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "node_id": {
                    "type": "string",
                    "description": "The KG node ID to start inference from",
                },
                "relation": {
                    "type": "string",
                    "description": (
                        "The relation to traverse (e.g. part_of, contains, "
                        "wrote, authored_by, member_of)"
                    ),
                },
                "max_depth": {
                    "type": "integer",
                    "default": 5,
                    "minimum": 1,
                    "maximum": 10,
                    "description": "Maximum BFS hops; ignored for 1-hop relations",
                },
            },
            "required": ["node_id", "relation"],
        }

    async def execute(self, args: dict[str, Any]) -> InferTransitiveResult:
        node_id = args.get("node_id")
        relation = args.get("relation")
        max_depth = int(args.get("max_depth", 5))
        max_depth = max(1, min(max_depth, 10))

        if not node_id or not isinstance(node_id, str):
            raise ValueError("infer_transitive: 'node_id' must be a non-empty string")
        if not relation or not isinstance(relation, str):
            raise ValueError("infer_transitive: 'relation' must be a non-empty string")

        # Quick sanity check on the node — keeps error messages clean
        # instead of returning a baffling empty result.
        center = self._deps.node_lookup.get(node_id)
        if center is None:
            return InferTransitiveResult(
                start_node_id=node_id,
                start_label=node_id,
                relation=relation,
                inverse_relation=_INVERSE_INDEX.get(relation),
                is_transitive=relation in _TRANSITIVE_RELATIONS,
                max_depth=max_depth,
                derived_nodes=[],
            )

        inverse_relation = _INVERSE_INDEX.get(relation)
        is_transitive = relation in _TRANSITIVE_RELATIONS

        # BFS over (relation outgoing) ∪ (inverse-relation incoming).
        # Cap depth at 1 for non-transitive relations — the ontology
        # doesn't authorize chaining and chaining would be unsound.
        effective_depth = max_depth if is_transitive else 1

        visited: dict[str, DerivedNode] = {}
        queue: deque[tuple[str, int, list[str]]] = deque([(node_id, 0, [])])
        truncated = False

        outgoing = self._deps.outgoing_edges
        incoming = self._deps.incoming_edges

        while queue:
            cur_id, depth, path = queue.popleft()
            if depth >= effective_depth:
                continue

            # Forward edges via ``relation``
            for edge in outgoing.get(cur_id, []):
                if edge.get("relation") != relation:
                    continue
                tgt = edge.get("target") or edge.get("target_id", "")
                if not tgt or tgt == node_id or tgt in visited:
                    continue
                node = self._deps.node_lookup.get(tgt, {})
                new_path = [*path, f"{relation}→"]
                visited[tgt] = DerivedNode(
                    node_id=tgt,
                    label=node.get("label", tgt),
                    type=node.get("type", ""),
                    distance=depth + 1,
                    derivation=new_path,
                )
                if len(visited) >= _RESULT_CAP:
                    truncated = True
                    break
                queue.append((tgt, depth + 1, new_path))

            if truncated:
                break

            # Inverse edges: nodes that point at ``cur_id`` via
            # ``relation`` (we want to follow the inverse direction).
            if inverse_relation is not None:
                for edge in outgoing.get(cur_id, []):
                    # outgoing edges whose relation equals the inverse
                    # of the user-supplied one give nodes reachable via
                    # the materialized inverse direction.
                    if edge.get("relation") != inverse_relation:
                        continue
                    tgt = edge.get("target") or edge.get("target_id", "")
                    if not tgt or tgt == node_id or tgt in visited:
                        continue
                    node = self._deps.node_lookup.get(tgt, {})
                    new_path = [*path, f"{inverse_relation}→"]
                    visited[tgt] = DerivedNode(
                        node_id=tgt,
                        label=node.get("label", tgt),
                        type=node.get("type", ""),
                        distance=depth + 1,
                        derivation=new_path,
                    )
                    if len(visited) >= _RESULT_CAP:
                        truncated = True
                        break
                    queue.append((tgt, depth + 1, new_path))

                if truncated:
                    break

                # Genuinely-inverse direction A: incoming edges whose
                # relation matches the *forward* relation give nodes
                # ``s`` such that ``s relation cur_id``.
                for edge in incoming.get(cur_id, []):
                    if edge.get("relation") != relation:
                        continue
                    src = edge.get("source") or edge.get("source_id", "")
                    if not src or src == node_id or src in visited:
                        continue
                    node = self._deps.node_lookup.get(src, {})
                    new_path = [*path, f"←{relation}"]
                    visited[src] = DerivedNode(
                        node_id=src,
                        label=node.get("label", src),
                        type=node.get("type", ""),
                        distance=depth + 1,
                        derivation=new_path,
                    )
                    if len(visited) >= _RESULT_CAP:
                        truncated = True
                        break
                    queue.append((src, depth + 1, new_path))

                if truncated:
                    break

                # Genuinely-inverse direction B: incoming edges whose
                # relation is the *inverse* of the user-supplied one.
                # Example: user asks ``authored_by`` on work_x; an
                # incoming ``wrote`` edge from person_plato is the OWL-RL
                # justification for ``work_x authored_by person_plato``.
                for edge in incoming.get(cur_id, []):
                    if edge.get("relation") != inverse_relation:
                        continue
                    src = edge.get("source") or edge.get("source_id", "")
                    if not src or src == node_id or src in visited:
                        continue
                    node = self._deps.node_lookup.get(src, {})
                    new_path = [*path, f"←{inverse_relation}"]
                    visited[src] = DerivedNode(
                        node_id=src,
                        label=node.get("label", src),
                        type=node.get("type", ""),
                        distance=depth + 1,
                        derivation=new_path,
                    )
                    if len(visited) >= _RESULT_CAP:
                        truncated = True
                        break
                    queue.append((src, depth + 1, new_path))

                if truncated:
                    break

        # Stable sort: distance asc, then label.
        derived_sorted = sorted(
            visited.values(), key=lambda n: (n.distance, n.label, n.node_id)
        )

        return InferTransitiveResult(
            start_node_id=node_id,
            start_label=center.get("label", node_id),
            relation=relation,
            inverse_relation=inverse_relation,
            is_transitive=is_transitive,
            max_depth=effective_depth,
            derived_nodes=derived_sorted,
            truncated=truncated,
        )
