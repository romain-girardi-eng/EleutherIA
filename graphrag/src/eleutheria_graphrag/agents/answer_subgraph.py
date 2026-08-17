"""Curated answer subgraph — the small graph the UI shows for ONE answer.

The right panel promises "a curated knowledge graph for each answer". Before
this module the frontend only received ``reasoning_path.starting_nodes`` /
``expanded_nodes`` (flat id lists) and, since fix 10b, the KG edges whose two
endpoints both happened to be retrieved. That is a *retrieval dump*, not a map
of the debate the answer is about: no frames, no positions, no contested
passages, and nothing tying a node to why the question surfaced it.

This module builds the real thing from the two strongest sources of truth the
pipeline already produces:

1. the assembled :class:`ControversyMap` (fault-line frames -> grounded
   positions -> dialectical links -> contested primary passages), serialised
   at the agent seam into a compact, text-free ``skeleton``; and
2. the KG nodes actually activated during retrieval (seeds, context nodes and
   ``kg_node_activated`` events), joined against the in-memory KG so the real
   edges between them carry their real relation labels.

Everything is best-first and capped (``MAX_SUBGRAPH_NODES`` /
``MAX_SUBGRAPH_EDGES``) so the panel stays legible. The question anchor is the
only synthetic node. Every other serialised id, label and type is resolved
from the loaded KG snapshot. Structural links which the runtime needs for the
answer map but which have no direct KG triple are explicitly marked
``origin="runtime_inference"``; they are never passed off as KG edges.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from typing import Any

__all__ = [
    "MAX_SUBGRAPH_EDGES",
    "MAX_SUBGRAPH_NODES",
    "build_answer_subgraph",
    "serialize_controversy_map",
]

# Legibility caps for the panel-sized graph.
MAX_SUBGRAPH_NODES = 80
MAX_SUBGRAPH_EDGES = 160

# Claim/title text kept on the wire (the panel shows labels, not prose).
_CLAIM_CHARS = 180
_TITLE_CHARS = 120


def _clip(value: Any, limit: int) -> str:
    text = str(value or "").strip()
    if len(text) <= limit:
        return text
    return f"{text[: limit - 1].rstrip()}…"


def _compact(payload: dict[str, Any]) -> dict[str, Any]:
    """Drop empty/None fields so the wire payload stays small."""
    return {k: v for k, v in payload.items() if v not in (None, "", [], {})}


# ── map serialisation (agent seam) ───────────────────────────────────────────


def serialize_controversy_map(cmap: Any) -> dict[str, Any] | None:
    """Compact, text-free skeleton of a :class:`ControversyMap`.

    Kept deliberately small: ids, labels, relations and the position/passage
    wiring — never the untruncated Greek/Latin (the reader panel serves that).
    Returns ``None`` when no map was assembled, so the flag-OFF path stays
    byte-for-byte unchanged.
    """
    frames = getattr(cmap, "frames", None)
    if not frames:
        return None

    out_frames: list[dict[str, Any]] = []
    for frame in frames:
        positions = [
            {
                "position_id": str(getattr(p, "position_id", "") or ""),
                "holder": str(getattr(p, "holder", "") or ""),
                "holder_node_id": str(getattr(p, "holder_node_id", "") or ""),
                "holder_type": str(getattr(p, "holder_type", "") or ""),
                "claim": _clip(getattr(p, "claim", ""), _CLAIM_CHARS),
                "publication": _clip(getattr(p, "publication", "") or "", _TITLE_CHARS),
                "primary_support": [
                    str(pid)
                    for pid in (getattr(p, "primary_support", None) or [])
                    if pid
                ],
            }
            for p in (getattr(frame, "positions", None) or [])
            if getattr(p, "position_id", "")
        ]
        links = [
            {
                "relation": str(getattr(link, "relation", "") or "related_to"),
                "from_id": str(getattr(link, "from_id", "") or ""),
                "to_id": str(getattr(link, "to_id", "") or ""),
                "gloss": _clip(getattr(link, "gloss", "") or "", _TITLE_CHARS),
            }
            for link in (getattr(frame, "links", None) or [])
            if getattr(link, "from_id", "") and getattr(link, "to_id", "")
        ]
        passages = [
            {
                "passage_id": str(getattr(ref, "passage_id", "") or ""),
                "author": str(getattr(ref, "author", "") or ""),
                "work": str(getattr(ref, "work", "") or ""),
                "canonical_ref": str(getattr(ref, "canonical_ref", "") or ""),
                "cts_urn": getattr(ref, "cts_urn", None),
            }
            for ref in (getattr(frame, "contested_passages", None) or [])
            if getattr(ref, "passage_id", "")
        ]
        completeness = getattr(frame, "completeness", None)
        out_frames.append(
            {
                "frame_id": str(getattr(frame, "frame_id", "") or ""),
                "debate_node_id": getattr(frame, "debate_node_id", None),
                "title": _clip(getattr(frame, "title", ""), _TITLE_CHARS),
                "period": str(getattr(frame, "period", "") or ""),
                "incident_edge_count": int(
                    getattr(completeness, "incident_edge_count", 0) or 0
                ),
                "positions": positions,
                "links": links,
                "passages": passages,
            }
        )

    if not out_frames:
        return None
    return {"frames": out_frames}


# ── subgraph assembly ────────────────────────────────────────────────────────


class _Accumulator:
    """Ordered, capped accumulation for real KG ids plus the question anchor."""

    def __init__(self, max_nodes: int, max_edges: int) -> None:
        self.max_nodes = max_nodes
        self.max_edges = max_edges
        self.nodes: list[dict[str, Any]] = []
        self.edges: list[dict[str, Any]] = []
        self._node_ids: set[str] = set()
        self._edge_keys: set[tuple[str, str, str]] = set()
        self.candidate_nodes = 0
        self.candidate_edges = 0

    def add_node(self, node: dict[str, Any]) -> bool:
        node_id = node.get("id") or ""
        if not node_id:
            return False
        if node_id in self._node_ids:
            return True
        self.candidate_nodes += 1
        if len(self.nodes) >= self.max_nodes:
            return False
        self._node_ids.add(node_id)
        self.nodes.append(node)
        return True

    def has(self, node_id: str) -> bool:
        return node_id in self._node_ids

    def has_edge(self, source: str, target: str, relation: str | None = None) -> bool:
        if relation is not None:
            return (source, target, relation) in self._edge_keys
        return any(
            (left == source and right == target) or (left == target and right == source)
            for left, right, _ in self._edge_keys
        )

    def add_edge(self, source: str, target: str, relation: str, **extra: Any) -> bool:
        if not source or not target or source == target:
            return False
        if source not in self._node_ids or target not in self._node_ids:
            return False
        key = (source, target, relation)
        if key in self._edge_keys:
            return False
        self.candidate_edges += 1
        if len(self.edges) >= self.max_edges:
            return False
        self._edge_keys.add(key)
        edge = {"source": source, "target": target, "relation": relation}
        edge.update({k: v for k, v in extra.items() if v is not None and v != ""})
        self.edges.append(edge)
        return True


def _kg_node_payload(
    node_id: str,
    node_lookup: Mapping[str, Mapping[str, Any]],
    *,
    origin: str,
    score: float,
    root: bool = False,
) -> dict[str, Any]:
    meta = node_lookup.get(node_id) or {}
    payload: dict[str, Any] = {
        "id": node_id,
        "label": _clip(meta.get("label") or node_id, _TITLE_CHARS),
        "type": str(meta.get("type") or "concept"),
        "origin": origin,
        "score": score,
    }
    if root:
        payload["root"] = True
    detail = meta.get("period") or meta.get("school")
    if detail:
        payload["detail"] = _clip(detail, 60)
    return _compact(payload)


def _is_resolved_kg_node(
    node_id: str,
    node_lookup: Mapping[str, Mapping[str, Any]],
) -> bool:
    """A rendered KG node needs the snapshot's own human label and type."""
    node = node_lookup.get(node_id)
    return bool(node and node.get("label") and node.get("type"))


def build_answer_subgraph(
    *,
    skeleton: Mapping[str, Any] | None,
    question: str = "",
    seed_ids: Sequence[str] = (),
    context_ids: Sequence[str] = (),
    activated: Iterable[Mapping[str, Any]] | None = None,
    node_lookup: Mapping[str, Mapping[str, Any]] | None = None,
    outgoing_edges: Mapping[str, Sequence[Mapping[str, Any]]] | None = None,
    max_nodes: int = MAX_SUBGRAPH_NODES,
    max_edges: int = MAX_SUBGRAPH_EDGES,
) -> dict[str, Any]:
    """Assemble the curated per-answer subgraph.

    Best-first order (so the caps truncate the tail, never the substance): the
    question anchor -> real debate nodes -> real position-holder nodes -> real
    passages -> seed KG nodes -> remaining activated/context KG nodes.

    A lexical-fallback frame has no debate node and therefore mints no frame
    node. Its holders stand directly around the question. Real KG edges between
    included nodes are added first. Runtime-only question/frame/support links
    follow with an explicit ``runtime_inference`` origin.
    """
    lookup: Mapping[str, Mapping[str, Any]] = node_lookup or {}
    adjacency: Mapping[str, Sequence[Mapping[str, Any]]] = outgoing_edges or {}
    acc = _Accumulator(max_nodes, max_edges)

    acc.add_node(
        {
            "id": "question",
            "label": _clip(question or "Question", _TITLE_CHARS),
            "type": "question",
            "origin": "question_anchor",
            "score": 1.0,
            "root": True,
            "synthetic": True,
        }
    )

    frames = list((skeleton or {}).get("frames") or [])
    debate_ids: list[str] = []
    holder_ids: list[str] = []
    passage_ids: list[str] = []
    lexical_holder_ids: list[str] = []
    pending_inferred: list[tuple[str, str, str, dict[str, Any]]] = []

    # 1) The controversy map selects real KG nodes. It does not define a
    #    parallel answer-only ontology.
    for frame in frames:
        debate_id = str(frame.get("debate_node_id") or "")
        real_debate_id = debate_id if _is_resolved_kg_node(debate_id, lookup) else ""
        if real_debate_id:
            was_present = acc.has(real_debate_id)
            if (
                acc.add_node(
                    _kg_node_payload(
                        real_debate_id,
                        lookup,
                        origin="controversy_debate",
                        score=1.0,
                        root=True,
                    )
                )
                and not was_present
            ):
                debate_ids.append(real_debate_id)

        position_ids: dict[str, str] = {}
        for position in frame.get("positions") or []:
            pid = str(position.get("position_id") or "")
            if not pid:
                continue
            holder_id = str(position.get("holder_node_id") or "")
            # Some legacy/fallback positions could not resolve a person/school.
            # Their own position/argument id is still a real KG node and is the
            # only safe fallback. Unresolved ids are dropped, never fabricated.
            real_holder_id = (
                holder_id
                if _is_resolved_kg_node(holder_id, lookup)
                else pid
                if _is_resolved_kg_node(pid, lookup)
                else ""
            )
            if not real_holder_id:
                continue
            was_present = acc.has(real_holder_id)
            payload = _kg_node_payload(
                real_holder_id,
                lookup,
                origin="position_holder",
                score=0.9,
                root=not real_debate_id,
            )
            claim = _clip(position.get("claim") or "", _CLAIM_CHARS)
            publication = _clip(position.get("publication") or "", _TITLE_CHARS)
            if claim:
                payload["detail"] = claim
            if publication:
                payload["publication"] = publication
            if not acc.add_node(payload):
                continue
            if not was_present:
                holder_ids.append(real_holder_id)
            position_ids[pid] = real_holder_id
            if real_debate_id:
                pending_inferred.append(
                    (
                        real_debate_id,
                        real_holder_id,
                        "has_position",
                        {"frame_id": frame.get("frame_id")},
                    )
                )
            elif real_holder_id not in lexical_holder_ids:
                lexical_holder_ids.append(real_holder_id)

        # The map can project a position-level relation onto holder nodes. That
        # projection is useful, but it is not a KG triple unless the same edge
        # exists between the selected holder ids; mark it accordingly later.
        for link in frame.get("links") or []:
            source = position_ids.get(str(link.get("from_id") or ""))
            target = position_ids.get(str(link.get("to_id") or ""))
            if source and target:
                pending_inferred.append(
                    (
                        source,
                        target,
                        str(link.get("relation") or "related_to"),
                        {"gloss": link.get("gloss")},
                    )
                )

        # Contested passages, attached to the positions they ground.
        passages = {
            str(p.get("passage_id")): p
            for p in (frame.get("passages") or [])
            if p.get("passage_id")
        }
        supported: list[tuple[str, str]] = []
        for position in frame.get("positions") or []:
            pos_graph_id = position_ids.get(str(position.get("position_id") or ""))
            if not pos_graph_id:
                continue
            for pid in position.get("primary_support") or []:
                if str(pid) in passages:
                    supported.append((pos_graph_id, str(pid)))

        ordered_passage_ids = [passage_id for _, passage_id in supported]
        ordered_passage_ids += [
            passage_id
            for passage_id in passages
            if passage_id not in set(ordered_passage_ids)
        ]
        supported_passage_ids = {passage_id for _, passage_id in supported}
        for passage_id in dict.fromkeys(ordered_passage_ids):
            if not _is_resolved_kg_node(passage_id, lookup):
                continue
            passage = passages[passage_id]
            was_present = acc.has(passage_id)
            payload = _kg_node_payload(
                passage_id,
                lookup,
                origin="contested_passage",
                score=0.7,
            )
            if passage.get("cts_urn"):
                payload["cts_urn"] = passage.get("cts_urn")
            if acc.add_node(payload) and not was_present:
                passage_ids.append(passage_id)
            if passage_id not in supported_passage_ids and real_debate_id:
                pending_inferred.append(
                    (
                        real_debate_id,
                        passage_id,
                        "contested_passage",
                        {"frame_id": frame.get("frame_id")},
                    )
                )

        for holder_node_id, passage_id in supported:
            if acc.has(passage_id):
                pending_inferred.append((holder_node_id, passage_id, "grounded_in", {}))

    # 2) KG nodes actually activated during retrieval.
    seeds = [str(nid) for nid in seed_ids if nid]
    seed_set = set(seeds)
    activated_ids: list[str] = []
    for item in activated or []:
        nid = str(item.get("id") or item.get("node_id") or "")
        if not nid:
            continue
        activated_ids.append(nid)

    kg_order = list(
        dict.fromkeys(
            [*seeds, *activated_ids, *(str(nid) for nid in context_ids if nid)]
        )
    )
    kg_node_count = 0
    for nid in kg_order:
        if acc.has(nid) or not _is_resolved_kg_node(nid, lookup):
            continue
        is_seed = nid in seed_set
        payload = _kg_node_payload(
            nid,
            lookup,
            origin="seed" if is_seed else "activated",
            score=1.0 if is_seed else 0.5,
            root=is_seed,
        )
        if payload["label"] == nid:
            # Nothing resolved this id to a human-readable label. A raw node id
            # must never render (GOAL-8 deleak rule), so leave it out entirely
            # rather than drawing an unnamed box.
            continue
        if acc.add_node(payload):
            kg_node_count += 1

    # 3) Prefer and fully identify real KG edges between included real nodes.
    real_node_ids = {str(node["id"]) for node in acc.nodes if node["id"] != "question"}
    for source in [node["id"] for node in acc.nodes if node["id"] != "question"]:
        for edge in adjacency.get(str(source), ()) or ():
            target = str(edge.get("target") or "")
            if target not in real_node_ids:
                continue
            acc.add_edge(
                str(source),
                target,
                str(edge.get("relation") or "related_to"),
                origin="kg",
                edge_id=edge.get("edge_id"),
                gloss=_clip(edge.get("description") or "", _TITLE_CHARS) or None,
            )

    # 4) The synthetic question anchor is explicit, as are any runtime-only
    #    structural projections needed to keep the answer map readable.
    for debate_id in debate_ids:
        acc.add_edge(
            "question",
            debate_id,
            "frames_question",
            origin="runtime_inference",
        )
    for holder_id in lexical_holder_ids:
        acc.add_edge(
            "question",
            holder_id,
            "frames_question",
            origin="runtime_inference",
        )
    if not debate_ids and not lexical_holder_ids:
        for seed_id in seeds:
            if acc.has(seed_id):
                acc.add_edge(
                    "question",
                    seed_id,
                    "retrieved_for_question",
                    origin="runtime_inference",
                )

    for source, target, relation, extra in pending_inferred:
        if acc.has_edge(source, target, relation):
            continue
        # A real edge in either direction already communicates debate
        # membership/support for the radial clustering; do not draw a second,
        # answer-inferred edge on top of it. Dialectical relations are stricter:
        # if that exact relation is absent, retain it only as an inference.
        is_dialectical = relation not in {
            "has_position",
            "grounded_in",
            "contested_passage",
        }
        if not is_dialectical and acc.has_edge(source, target):
            continue
        acc.add_edge(
            source,
            target,
            relation,
            origin="runtime_inference",
            **extra,
        )

    truncated = acc.candidate_nodes > len(acc.nodes) or acc.candidate_edges > len(
        acc.edges
    )
    return {
        "nodes": acc.nodes,
        "edges": acc.edges,
        "stats": {
            "node_count": len(acc.nodes),
            "edge_count": len(acc.edges),
            "frame_count": len(debate_ids),
            "position_count": len(holder_ids),
            "passage_count": len(passage_ids),
            "kg_node_count": kg_node_count,
            "candidate_nodes": acc.candidate_nodes,
            "candidate_edges": acc.candidate_edges,
            "truncated": truncated,
        },
    }
