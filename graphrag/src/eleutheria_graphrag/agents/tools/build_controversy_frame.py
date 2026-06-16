"""build_controversy_frame tool — the dossier-unit retriever (Scholar-RAG M1).

The novel core of the debate-first retrieval. Given a ``debate`` /
``controversy`` node OR a ``scholar_position_*`` / ``scholarly_argument_*`` node,
it assembles ONE ready-to-synthesise ``ControversyFrame`` (ARCHITECTURE §2.2 /
§3.1): the contending positions (each attributed to a holder, with publication +
page grounding read off node metadata, never invented), the flat star-tolerant
dialectical links between them, and the contested primary passages paired with
their English ``_en`` translation via ``has_translation``/``translation_of``.

The non-negotiable piece both judges flagged: the **empty-debate-node fallback**.
Two of the four headline debate nodes carry NO dialectical out-edges and/or 0
grounded passages — the fault-line ``opposes`` edges hang off the *position* /
``scholarly_argument_*`` nodes, not the debate node. When the seed is such an
empty debate, the tool:

  1. lexically matches participants (debate label/desc -> scholar_* /
     scholar_position_* / scholarly_argument_* nodes);
  2. hops via the ``argument_*`` / ``scholarly_argument_*`` clusters
     (``contributes_to`` / ``participates_in`` / ``discusses`` bridges);
  3. re-seeds on the recovered position/argument nodes and merges their
     ``opposes`` / ``critiques`` / ``responds_to`` edges back under the debate.

VECTORLESS: every step is KG adjacency + lexical match + ``has_translation``
join. No embeddings. Gated by ``ELEUTHERIA_SCHOLAR_RAG`` at registration.
"""

from __future__ import annotations

import logging
import re
from typing import Any

from pydantic import BaseModel

from eleutheria_graphrag.agents.dependencies import Deps
from eleutheria_graphrag.agents.state import (
    ControversyFrame,
    DialecticalLink,
    FrameCompleteness,
    GroundedPosition,
    PassageRef,
)
from eleutheria_graphrag.services.snapshot_retrieval import (
    normalize_mapping,
    passage_row_from_node,
    translation_for_passage,
)

logger = logging.getLogger(__name__)

_TERM_RE = re.compile(r"[A-Za-zÀ-ÿἀ-῾']+")

# Flat, star-tolerant dialectical relations (ARCHITECTURE §2.1 / §3.2).
_FAULT_LINE_RELATIONS: frozenset[str] = frozenset(
    {
        "opposes",
        "critiques",
        "responds_to",
        "refutes",
        "contrasts_with",
        "agrees_with",
        "supports",
    }
)

# Relations connecting a debate node to its participants / arguments (bridges).
_BRIDGE_RELATIONS: frozenset[str] = frozenset(
    {"participates_in", "contributes_to", "has_position", "advanced_in", "discusses"}
)

# Node types whose nodes can hold a scholarly position.
_POSITION_TYPES: frozenset[str] = frozenset(
    {"position", "argument", "person", "scholar", "school"}
)

_POSITION_ID_PREFIXES: tuple[str, ...] = (
    "scholar_position_",
    "scholarly_argument_",
    "argument_",
    "argument_cafma_",
)

# Stop-words for lexical participant matching against the debate label/desc.
_STOP_TERMS: frozenset[str] = frozenset(
    {
        "the",
        "and",
        "for",
        "with",
        "modern",
        "scholarly",
        "paradigm",
        "debate",
        "controversy",
        "question",
        "tradition",
        "problem",
        "notion",
        "anti",
        "vs",
        "versus",
        "about",
        "free",
        "will",
        "fate",
        "between",
    }
)


class BuildControversyFrameResult(BaseModel):
    """The assembled frame plus a flag for whether the fallback was needed."""

    frame: ControversyFrame
    used_fallback: bool = False
    note: str = ""


class BuildControversyFrameTool:
    """Assemble one ControversyFrame from a debate or position seed node."""

    def __init__(self, deps: Deps) -> None:
        self._deps = deps

    @property
    def name(self) -> str:
        return "build_controversy_frame"

    @property
    def description(self) -> str:
        return (
            "Assemble the full CONTROVERSY FRAME for one scholarly fault line. "
            "Pass a debate/controversy node OR a position/argument node (the "
            "fault-line opposes edges often hang off the position nodes, not the "
            "debate). Returns the contending positions — each with its holder, "
            "publication, and page grounding — the dialectical links between them "
            "(A --opposes--> B), and the contested primary passages paired with "
            "their English translation. If the debate node is empty, an automatic "
            "fallback recovers the fault line via the participant/argument cluster."
        )

    @property
    def parameters_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "seed_id": {
                    "type": "string",
                    "description": "A debate / controversy / position / argument "
                    "node ID to build the controversy frame from",
                },
                "max_passages": {
                    "type": "integer",
                    "default": 6,
                    "minimum": 0,
                    "maximum": 12,
                },
            },
            "required": ["seed_id"],
        }

    async def execute(self, args: dict[str, Any]) -> BuildControversyFrameResult:
        seed_id = args["seed_id"]
        max_passages = min(max(args.get("max_passages", 6), 0), 12)

        node = self._deps.node_lookup.get(seed_id)
        if node is None:
            empty = ControversyFrame(frame_id=f"frame_{seed_id}", title=seed_id)
            return BuildControversyFrameResult(
                frame=empty, used_fallback=False, note=f"seed '{seed_id}' not found"
            )

        node_type = (node.get("type") or "").lower()
        is_debate = node_type in {"debate", "controversy"}

        # 1. Direct one-hop dialectical edges on the seed (both directions).
        direct_links = self._dialectical_links(seed_id)

        used_fallback = False
        note = ""
        position_ids: set[str] = set()

        if is_debate:
            # Participants / arguments attached to the debate are candidate poles.
            position_ids |= self._bridge_position_ids(seed_id)
            # The empty-debate fallback: no direct fault line on the debate node.
            if not direct_links:
                used_fallback = True
                fallback_ids = self._lexical_participants(node)
                position_ids |= fallback_ids
                # Re-seed on the recovered position/argument nodes: collect THEIR
                # fault-line edges and merge them back under the debate.
                for pid in list(position_ids):
                    direct_links.extend(self._dialectical_links(pid))
                note = (
                    "empty debate node — recovered fault line via "
                    "participant/argument cluster fallback"
                )
        else:
            # Seed is itself a position/argument node: it IS a pole.
            position_ids.add(seed_id)

        # Every endpoint of a recovered link is also a position to ground.
        for link in direct_links:
            position_ids.add(link.from_id)
            position_ids.add(link.to_id)
        position_ids.discard(seed_id if is_debate else "")

        # 2. Deduplicate links (one per (from, relation, to)).
        links = self._dedup_links(direct_links)

        # 3. Ground each position (holder + publication + page from metadata).
        positions = [
            self._ground_position(pid)
            for pid in sorted(position_ids)
            if self._is_groundable(pid)
        ]
        # Attach holder labels onto the links now that positions are resolved.
        holder_by_id = {p.position_id: p.holder for p in positions}
        for link in links:
            link.from_holder = holder_by_id.get(link.from_id, link.from_holder)
            link.to_holder = holder_by_id.get(link.to_id, link.to_holder)

        # 4. Contested primary passages (debate + positions), paired with _en.
        contested = self._contested_passages(seed_id, position_ids, max_passages)
        for pos in positions:
            pos_passage_ids = self._passage_ids_for_node(pos.position_id)
            for pref in contested:
                if (
                    pref.passage_id in pos_passage_ids
                    and pref.passage_id not in pos.primary_support
                ):
                    pos.primary_support.append(pref.passage_id)

        # 5. Completeness signals (booleans + raw count — no score).
        completeness = self._completeness(positions, links, contested)

        frame = ControversyFrame(
            frame_id=f"frame_{seed_id}",
            debate_node_id=seed_id if is_debate else None,
            title=node.get("label", seed_id),
            period=node.get("period", "") or "",
            positions=positions,
            links=links,
            contested_passages=contested,
            completeness=completeness,
            used_fallback=used_fallback,
        )
        return BuildControversyFrameResult(
            frame=frame, used_fallback=used_fallback, note=note
        )

    # ── traversal ────────────────────────────────────────────────────────

    def _dialectical_links(self, node_id: str) -> list[DialecticalLink]:
        """One-hop fault-line edges incident on ``node_id``, canonicalised."""
        links: list[DialecticalLink] = []
        for edge in self._deps.outgoing_edges.get(node_id, []):
            rel = edge.get("relation") or ""
            if rel in _FAULT_LINE_RELATIONS:
                links.append(
                    DialecticalLink(
                        relation=rel, from_id=node_id, to_id=edge.get("target", "")
                    )
                )
        for edge in self._deps.incoming_edges.get(node_id, []):
            rel = edge.get("relation") or ""
            if rel in _FAULT_LINE_RELATIONS:
                links.append(
                    DialecticalLink(
                        relation=rel, from_id=edge.get("source", ""), to_id=node_id
                    )
                )
        return [link for link in links if link.from_id and link.to_id]

    def _bridge_position_ids(self, debate_id: str) -> set[str]:
        """Participants / arguments directly attached to a debate node."""
        ids: set[str] = set()
        for edge in self._deps.incoming_edges.get(debate_id, []):
            if (edge.get("relation") or "") in _BRIDGE_RELATIONS:
                ids.add(edge.get("source", ""))
        for edge in self._deps.outgoing_edges.get(debate_id, []):
            if (edge.get("relation") or "") in {"has_position", "discusses"}:
                ids.add(edge.get("target", ""))
        ids.discard("")
        return ids

    def _lexical_participants(self, debate_node: dict[str, Any]) -> set[str]:
        """Fallback: lexically match scholar/position/argument nodes to the debate.

        ARCHITECTURE §2.2 step 1. Matches the debate's distinctive terms (holder
        surnames etc.) against position/argument node labels + descriptions, then
        expands one argument-cluster hop to recover the fault-line carriers.
        """
        label = (debate_node.get("label") or "").lower()
        desc = (debate_node.get("description") or "").lower()
        terms = {
            t.lower()
            for t in _TERM_RE.findall(f"{label} {desc[:600]}")
            if len(t) > 3 and t.lower() not in _STOP_TERMS
        }
        if not terms:
            return set()

        matched: set[str] = set()
        for nid, node in self._deps.node_lookup.items():
            if not nid.startswith(_POSITION_ID_PREFIXES) and not nid.startswith(
                "scholar_"
            ):
                continue
            haystack = (
                f"{(node.get('label') or '')} {(node.get('description') or '')[:300]}"
            ).lower()
            node_terms = {t.lower() for t in _TERM_RE.findall(haystack) if len(t) > 3}
            if terms & node_terms:
                matched.add(nid)

        # Argument-cluster hop: for each matched node, pull its fault-line
        # neighbours (the re-seed step) so star-shaped disputes surface fully.
        expanded: set[str] = set(matched)
        for nid in matched:
            for edge in self._deps.outgoing_edges.get(nid, []):
                if (edge.get("relation") or "") in _FAULT_LINE_RELATIONS:
                    expanded.add(edge.get("target", ""))
            for edge in self._deps.incoming_edges.get(nid, []):
                if (edge.get("relation") or "") in _FAULT_LINE_RELATIONS:
                    expanded.add(edge.get("source", ""))
        expanded.discard("")
        return expanded

    @staticmethod
    def _dedup_links(links: list[DialecticalLink]) -> list[DialecticalLink]:
        seen: set[tuple[str, str, str]] = set()
        out: list[DialecticalLink] = []
        for link in links:
            key = (link.from_id, link.relation, link.to_id)
            if key not in seen and link.from_id != link.to_id:
                seen.add(key)
                out.append(link)
        return out

    def _is_groundable(self, node_id: str) -> bool:
        node = self._deps.node_lookup.get(node_id)
        if node is None:
            return False
        node_type = (node.get("type") or "").lower()
        if node_type == "passage":
            return False
        return node_type in _POSITION_TYPES or node_id.startswith(_POSITION_ID_PREFIXES)

    # ── grounding ────────────────────────────────────────────────────────

    def _ground_position(self, node_id: str) -> GroundedPosition:
        node = self._deps.node_lookup.get(node_id, {})
        metadata = normalize_mapping(node.get("metadata"))

        holder, holder_node_id, holder_type = self._resolve_holder(
            node_id, node, metadata
        )
        publication, publication_node_id = self._resolve_publication(node_id, metadata)
        page = self._resolve_page(metadata)
        claim = self._resolve_claim(node, metadata)

        return GroundedPosition(
            position_id=node_id,
            holder=holder,
            holder_node_id=holder_node_id,
            holder_type=holder_type,
            claim=claim,
            publication=publication,
            publication_node_id=publication_node_id,
            page_grounding=page,
        )

    def _resolve_holder(
        self, node_id: str, node: dict[str, Any], metadata: dict[str, Any]
    ) -> tuple[str, str, str]:
        node_type = (node.get("type") or "").lower()
        if node_type in {"person", "scholar"}:
            period = (node.get("period") or "").lower()
            htype = (
                "modern_scholar"
                if period in {"modern", "contemporary"}
                else "ancient_author"
            )
            return node.get("label", node_id), node_id, htype
        if node_type == "school":
            return node.get("label", node_id), node_id, "school"

        # Position / argument node: holder is a linked scholar/person.
        scholar_id = metadata.get("scholar_id") or ""
        if scholar_id and scholar_id in self._deps.node_lookup:
            sn = self._deps.node_lookup[scholar_id]
            return sn.get("label", scholar_id), scholar_id, "modern_scholar"
        for relation in ("advanced_in", "created_by", "authored_by", "has_position"):
            for edge in self._deps.outgoing_edges.get(node_id, []):
                if edge.get("relation") == relation:
                    tgt = edge.get("target", "")
                    tn = self._deps.node_lookup.get(tgt, {})
                    if (tn.get("type") or "").lower() in {"person", "scholar"}:
                        return tn.get("label", tgt), tgt, "modern_scholar"
            for edge in self._deps.incoming_edges.get(node_id, []):
                if edge.get("relation") == relation:
                    src = edge.get("source", "")
                    sn = self._deps.node_lookup.get(src, {})
                    if (sn.get("type") or "").lower() in {"person", "scholar"}:
                        return sn.get("label", src), src, "modern_scholar"
        # Derive a holder name from the label ("Frede: ...", "Ramelli: ...").
        label = node.get("label", node_id)
        derived = label.split(":")[0].strip() if ":" in label else label
        return derived, "", "modern_scholar"

    def _resolve_publication(
        self, node_id: str, metadata: dict[str, Any]
    ) -> tuple[str | None, str | None]:
        # Edge to a publication node.
        for edge in self._deps.outgoing_edges.get(node_id, []):
            if edge.get("relation") in {"advanced_in", "published_in", "appears_in"}:
                tgt = edge.get("target", "")
                tn = self._deps.node_lookup.get(tgt, {})
                if (tn.get("type") or "").lower() in {"publication", "scholarly_work"}:
                    return tn.get("label", tgt), tgt
        for edge in self._deps.incoming_edges.get(node_id, []):
            if edge.get("relation") in {"contributes_to", "advances"}:
                src = edge.get("source", "")
                sn = self._deps.node_lookup.get(src, {})
                if (sn.get("type") or "").lower() in {"publication", "scholarly_work"}:
                    return sn.get("label", src), src
        ref = metadata.get("key_work_reference")
        if isinstance(ref, str) and ref:
            return ref, None
        return None, None

    @staticmethod
    def _resolve_page(metadata: dict[str, Any]) -> str | None:
        """Page grounding from node metadata — None when absent (never invented)."""
        for key in ("page_grounding", "pages", "page", "locus", "page_reference"):
            value = metadata.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        return None

    @staticmethod
    def _resolve_claim(node: dict[str, Any], metadata: dict[str, Any]) -> str:
        for key in ("stance", "claim", "thesis"):
            value = metadata.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        return (node.get("description") or node.get("label") or "").strip()

    # ── passages ─────────────────────────────────────────────────────────

    def _passage_ids_for_node(self, node_id: str) -> set[str]:
        ids: set[str] = set()
        for edge in self._deps.incoming_edges.get(node_id, []):
            src = edge.get("source", "")
            if (
                self._deps.node_lookup.get(src, {}).get("type") or ""
            ).lower() == "passage":
                ids.add(src)
        for edge in self._deps.outgoing_edges.get(node_id, []):
            tgt = edge.get("target", "")
            if (
                self._deps.node_lookup.get(tgt, {}).get("type") or ""
            ).lower() == "passage":
                ids.add(tgt)
        return ids

    # Bridge node types one hop carries the seed/position to its passages
    # (argument --discusses--> concept --has_passage--> passage). Capped to
    # bound latency: at most _MAX_BRIDGE_NODES bridges are walked, and the
    # total passages returned never exceeds the caller's ``limit``.
    _BRIDGE_NODE_TYPES: frozenset[str] = frozenset({"concept", "argument"})
    _MAX_BRIDGE_NODES: int = 8

    def _passage_ids_via_concepts(self, node_id: str, limit: int) -> list[str]:
        """Two-hop passage discovery: node -> concept/argument bridge -> passage.

        Walks outgoing edges from ``node_id`` to neighbours whose type is in
        ``_BRIDGE_NODE_TYPES``, then for each bridge calls the existing
        one-hop ``_passage_ids_for_node``. Returns a deduped, ORDERED list.
        Fan-out is bounded: at most ``_MAX_BRIDGE_NODES`` bridges and at most
        ``limit`` passages total — no live DB calls, pure KG adjacency.
        """
        if limit <= 0:
            return []
        bridge_ids: list[str] = []
        bridge_seen: set[str] = set()
        for edge in self._deps.outgoing_edges.get(node_id, []):
            tgt = edge.get("target", "")
            if not tgt or tgt in bridge_seen:
                continue
            tgt_type = (self._deps.node_lookup.get(tgt, {}).get("type") or "").lower()
            if tgt_type in self._BRIDGE_NODE_TYPES:
                bridge_seen.add(tgt)
                bridge_ids.append(tgt)
                if len(bridge_ids) >= self._MAX_BRIDGE_NODES:
                    break

        passage_ids: list[str] = []
        seen: set[str] = set()
        for bridge_id in bridge_ids:
            for pid in sorted(self._passage_ids_for_node(bridge_id)):
                if pid not in seen:
                    seen.add(pid)
                    passage_ids.append(pid)
                    if len(passage_ids) >= limit:
                        return passage_ids
        return passage_ids

    def _contested_passages(
        self, seed_id: str, position_ids: set[str], limit: int
    ) -> list[PassageRef]:
        if limit <= 0:
            return []
        passage_ids: list[str] = []
        seen: set[str] = set()
        for nid in [seed_id, *sorted(position_ids)]:
            for pid in sorted(self._passage_ids_for_node(nid)):
                if pid not in seen:
                    seen.add(pid)
                    passage_ids.append(pid)
                    if len(passage_ids) >= limit:
                        break
            if len(passage_ids) >= limit:
                break

        # Second pass: many seed/position nodes have NO direct passage edge —
        # their primary passages sit one concept/argument hop further
        # (argument --discusses--> concept --has_passage--> passage). 1-hop
        # direct passages stay FIRST (priority); only fill the remainder.
        if len(passage_ids) < limit:
            for nid in [seed_id, *sorted(position_ids)]:
                remaining = limit - len(passage_ids)
                if remaining <= 0:
                    break
                for pid in self._passage_ids_via_concepts(nid, remaining):
                    if pid not in seen:
                        seen.add(pid)
                        passage_ids.append(pid)
                        if len(passage_ids) >= limit:
                            break

        refs: list[PassageRef] = []
        for pid in passage_ids:
            row = passage_row_from_node(self._deps, pid)
            if row is None:
                continue
            translation = translation_for_passage(self._deps, pid)
            refs.append(
                PassageRef(
                    passage_id=pid,
                    work=row.get("title") or "",
                    author=row.get("author") or "",
                    canonical_ref=row.get("canonical_ref") or "",
                    cts_urn=(row.get("metadata") or {}).get("cts_urn"),
                    original_text=row.get("text_content") or "",
                    english_text=(
                        translation.get("text_content") if translation else None
                    ),
                    language=row.get("language") or "",
                )
            )
        return refs

    @staticmethod
    def _completeness(
        positions: list[GroundedPosition],
        links: list[DialecticalLink],
        contested: list[PassageRef],
    ) -> FrameCompleteness:
        attacked: set[str] = {link.to_id for link in links}
        attackers: set[str] = {link.from_id for link in links}
        defenders = {p.position_id for p in positions} - attackers
        has_two_sides = bool(positions) and bool(attacked)
        has_orphan_attack = bool(attackers) and not defenders and bool(positions)
        return FrameCompleteness(
            has_two_sides=has_two_sides,
            has_orphan_attack=has_orphan_attack,
            has_primary_grounding=bool(contested),
            incident_edge_count=len(links),
        )
