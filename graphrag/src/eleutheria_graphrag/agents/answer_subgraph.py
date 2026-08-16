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
``MAX_SUBGRAPH_EDGES``) so the panel stays legible. NOTHING is invented: every
node and edge comes from the map or the KG snapshot.
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


def _passage_label(passage: Mapping[str, Any]) -> str:
    author = str(passage.get("author") or "").strip()
    ref = str(passage.get("canonical_ref") or "").strip()
    work = str(passage.get("work") or "").strip()
    parts = [p for p in (author, work if not ref else "", ref) if p]
    return _clip(" ".join(parts) or passage.get("passage_id", "passage"), _TITLE_CHARS)


def _holder_node_type(holder_type: str) -> str:
    if holder_type in {"school", "group"}:
        return "school"
    return "person"


class _Accumulator:
    """Ordered, capped node/edge accumulation with ref -> graph-id indexing."""

    def __init__(self, max_nodes: int, max_edges: int) -> None:
        self.max_nodes = max_nodes
        self.max_edges = max_edges
        self.nodes: list[dict[str, Any]] = []
        self.edges: list[dict[str, Any]] = []
        self._node_ids: set[str] = set()
        self._edge_keys: set[tuple[str, str, str]] = set()
        self.candidate_nodes = 0
        self.candidate_edges = 0
        # KG node id (or passage id) -> graph node id, for adjacency joins.
        self.by_ref: dict[str, str] = {}

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
        ref = node.get("ref")
        if ref and ref not in self.by_ref:
            self.by_ref[str(ref)] = node_id
        return True

    def has(self, node_id: str) -> bool:
        return node_id in self._node_ids

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
        edge.update({k: v for k, v in extra.items() if v})
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
        "ref": node_id,
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


def build_answer_subgraph(
    *,
    skeleton: Mapping[str, Any] | None,
    seed_ids: Sequence[str] = (),
    context_ids: Sequence[str] = (),
    activated: Iterable[Mapping[str, Any]] | None = None,
    node_lookup: Mapping[str, Mapping[str, Any]] | None = None,
    outgoing_edges: Mapping[str, Sequence[Mapping[str, Any]]] | None = None,
    max_nodes: int = MAX_SUBGRAPH_NODES,
    max_edges: int = MAX_SUBGRAPH_EDGES,
) -> dict[str, Any]:
    """Assemble the curated per-answer subgraph.

    Best-first order (so the caps truncate the tail, never the substance):
    controversy frames -> their positions -> the passages those positions are
    grounded in -> seed KG nodes -> the remaining activated/context KG nodes.
    Edges are the map's own dialectical links plus the real KG edges between
    any two included nodes.
    """
    lookup: Mapping[str, Mapping[str, Any]] = node_lookup or {}
    adjacency: Mapping[str, Sequence[Mapping[str, Any]]] = outgoing_edges or {}
    acc = _Accumulator(max_nodes, max_edges)

    frames = list((skeleton or {}).get("frames") or [])
    frame_count = 0
    position_count = 0
    passage_count = 0

    # 1) The controversy map: frames, positions, contested passages.
    for frame in frames:
        frame_id = str(frame.get("frame_id") or "")
        if not frame_id:
            continue
        debate_ref = frame.get("debate_node_id") or None
        frame_node_id = f"frame:{frame_id}"
        frame_added = acc.add_node(
            _compact(
                {
                    "id": frame_node_id,
                    "ref": str(debate_ref) if debate_ref else None,
                    "label": _clip(frame.get("title") or frame_id, _TITLE_CHARS),
                    "type": "debate",
                    "origin": "controversy_frame",
                    "score": 1.0,
                    "root": True,
                    "detail": _clip(frame.get("period") or "", 60) or None,
                }
            )
        )
        if not frame_added:
            continue
        frame_count += 1

        position_ids: dict[str, str] = {}
        for position in frame.get("positions") or []:
            pid = str(position.get("position_id") or "")
            if not pid:
                continue
            holder_ref = str(position.get("holder_node_id") or "") or None
            graph_id = f"pos:{pid}"
            if not acc.add_node(
                _compact(
                    {
                        "id": graph_id,
                        "ref": holder_ref,
                        "label": _clip(
                            position.get("holder") or position.get("claim") or pid,
                            _TITLE_CHARS,
                        ),
                        "type": _holder_node_type(
                            str(position.get("holder_type") or "")
                        ),
                        "origin": "position",
                        "score": 0.9,
                        "detail": position.get("claim") or None,
                        "publication": position.get("publication") or None,
                    }
                )
            ):
                continue
            position_count += 1
            position_ids[pid] = graph_id
            acc.add_edge(frame_node_id, graph_id, "has_position")

        # Dialectical links between the frame's positions (the fault line).
        for link in frame.get("links") or []:
            source = position_ids.get(str(link.get("from_id") or ""))
            target = position_ids.get(str(link.get("to_id") or ""))
            if source and target:
                acc.add_edge(
                    source,
                    target,
                    str(link.get("relation") or "related_to"),
                    gloss=link.get("gloss"),
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

        ordered_passage_ids = [pid for _, pid in supported]
        ordered_passage_ids += [
            pid for pid in passages if pid not in set(ordered_passage_ids)
        ]
        supported_passage_ids = {pid for _, pid in supported}
        for pid in dict.fromkeys(ordered_passage_ids):
            passage = passages[pid]
            if not acc.add_node(
                _compact(
                    {
                        "id": pid,
                        "ref": pid,
                        "label": _passage_label(passage),
                        "type": "passage",
                        "origin": "contested_passage",
                        "score": 0.7,
                        "detail": _clip(passage.get("work") or "", 60) or None,
                        "cts_urn": passage.get("cts_urn"),
                    }
                )
            ):
                continue
            passage_count += 1
            if pid not in supported_passage_ids:
                # Unattached contested passage: hang it off its frame so it is
                # never an orphan in the rendered graph.
                acc.add_edge(frame_node_id, pid, "contested_passage")

        for position_graph_id, pid in supported:
            acc.add_edge(position_graph_id, pid, "grounded_in")

    # 2) KG nodes actually activated during retrieval.
    seeds = [str(nid) for nid in seed_ids if nid]
    seed_set = set(seeds)
    activated_ids: list[str] = []
    activated_meta: dict[str, Mapping[str, Any]] = {}
    for item in activated or []:
        nid = str(item.get("id") or item.get("node_id") or "")
        if not nid:
            continue
        activated_ids.append(nid)
        activated_meta.setdefault(nid, item)

    kg_order = list(
        dict.fromkeys(
            [*seeds, *activated_ids, *(str(nid) for nid in context_ids if nid)]
        )
    )
    kg_node_count = 0
    for nid in kg_order:
        if acc.has(nid):
            continue
        is_seed = nid in seed_set
        payload = _kg_node_payload(
            nid,
            lookup,
            origin="seed" if is_seed else "activated",
            score=1.0 if is_seed else 0.5,
            root=is_seed,
        )
        meta = activated_meta.get(nid)
        if meta and (payload["label"] == nid or not lookup.get(nid)):
            payload["label"] = _clip(meta.get("label") or nid, _TITLE_CHARS)
            payload["type"] = str(
                meta.get("type") or meta.get("node_type") or "concept"
            )
        if payload["label"] == nid:
            # Nothing resolved this id to a human-readable label. A raw node id
            # must never render (GOAL-8 deleak rule), so leave it out entirely
            # rather than drawing an unnamed box.
            continue
        if acc.add_node(payload):
            kg_node_count += 1

    # 3) The real KG edges between any two included nodes (map holders too:
    #    a position carries its holder's node id as `ref`).
    for ref, graph_id in list(acc.by_ref.items()):
        for edge in adjacency.get(ref, ()) or ():
            target_ref = str(edge.get("target") or "")
            target_graph_id = acc.by_ref.get(target_ref)
            if not target_graph_id:
                continue
            acc.add_edge(
                graph_id,
                target_graph_id,
                str(edge.get("relation") or "related_to"),
                gloss=_clip(edge.get("description") or "", _TITLE_CHARS) or None,
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
            "frame_count": frame_count,
            "position_count": position_count,
            "passage_count": passage_count,
            "kg_node_count": kg_node_count,
            "candidate_nodes": acc.candidate_nodes,
            "candidate_edges": acc.candidate_edges,
            "truncated": truncated,
        },
    }
