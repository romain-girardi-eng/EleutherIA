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


# Author key derived from a ``passage_<author>_*`` id when no richer signal
# exists. The segment after ``passage_`` up to the next underscore/digit is the
# author token (``passage_epict_1`` -> ``epict``, ``passage_alex_de_fato`` ->
# ``alex``). Used only as the LAST resort behind metadata/authored_by.
_PASSAGE_ID_AUTHOR_RE = re.compile(r"^passage_([A-Za-z]+)")


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
                    "maximum": 24,
                },
            },
            "required": ["seed_id"],
        }

    async def execute(self, args: dict[str, Any]) -> BuildControversyFrameResult:
        seed_id = args["seed_id"]
        max_passages = min(max(args.get("max_passages", 6), 0), 24)

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

    def _passage_author_key(self, passage_id: str) -> str:
        """Stable author key for a passage id (metadata > authored_by > id prefix).

        The round-robin grouping key. Prefers the passage node's ``author``
        metadata or its ``authored_by`` neighbour label; falls back to the
        ``passage_<author>_*`` id token so that ``passage_epict_*`` and
        ``passage_alex_*`` group apart even when metadata is sparse. Never
        fabricates: returns the id itself only when no author signal exists.
        """
        node = self._deps.node_lookup.get(passage_id, {})
        metadata = normalize_mapping(node.get("metadata"))
        author = metadata.get("author")
        if isinstance(author, str) and author.strip():
            return author.strip().lower()
        for edge in self._deps.outgoing_edges.get(passage_id, []):
            if (edge.get("relation") or "") == "authored_by":
                tgt = self._deps.node_lookup.get(edge.get("target", ""), {})
                label = tgt.get("label")
                if isinstance(label, str) and label.strip():
                    return label.strip().lower()
        match = _PASSAGE_ID_AUTHOR_RE.match(passage_id)
        if match:
            return match.group(1).lower()
        return passage_id.lower()

    def _greek_quality(self, pid: str) -> int:
        """Score a passage by how much QUOTABLE original-language text it carries.

        Returns the count of polytonic Greek (and basic Greek) characters in the
        passage's ``text_content``, so passages with substantial continuous Greek
        rank ahead of those with little or none. A metadata/reference-only block
        (``**Reference:** … **Author:** …``) carries NO quotable original text and
        is pushed to the bottom (``-1``) — quoting it verbatim would dump markdown
        metadata into the answer instead of Greek.
        """
        row = passage_row_from_node(self._deps, pid)
        if row is None:
            return 0
        return self._quotable_chars(
            row.get("text_content") or "", row.get("language") or ""
        )

    def _round_robin_by_author(
        self, passage_ids: list[str], priority_authors: frozenset[str]
    ) -> list[str]:
        """Interleave passage ids one-per-author so no author monopolises the cap.

        Groups ``passage_ids`` by :meth:`_passage_author_key` (stable order
        within each group), then emits round-robin. Authors whose key matches a
        frame-holder / question term in ``priority_authors`` are drained FIRST
        (relevance rank), so an Epictetus question surfaces Epictetus passages
        before unrelated authors even under a tight cap. Fully deterministic.
        """
        groups: dict[str, list[str]] = {}
        order: list[str] = []
        for pid in passage_ids:
            key = self._passage_author_key(pid)
            if key not in groups:
                groups[key] = []
                order.append(key)
            groups[key].append(pid)

        def _is_priority(key: str) -> bool:
            return any(term in key or key in term for term in priority_authors)

        priority_keys = [k for k in order if _is_priority(k)]
        other_keys = [k for k in order if not _is_priority(k)]
        ranked_order = priority_keys + other_keys

        # Within each author group, rank passages that carry QUOTABLE Greek/Latin
        # text ahead of reference/metadata-only blocks, so the synthesis surfaces
        # a passage it can actually quote in the original (not merely cite by
        # locus). A passage whose text_content is a '**Reference:** … **Author:**'
        # metadata block has nothing to quote — it must not win the slot over a
        # sibling that carries real original text.
        for key in ranked_order:
            groups[key].sort(key=self._greek_quality, reverse=True)

        out: list[str] = []
        cursors = dict.fromkeys(ranked_order, 0)
        remaining = sum(len(groups[k]) for k in ranked_order)
        while remaining:
            for key in ranked_order:
                idx = cursors[key]
                if idx < len(groups[key]):
                    out.append(groups[key][idx])
                    cursors[key] = idx + 1
                    remaining -= 1
        return out

    def _priority_authors(self, position_ids: set[str]) -> frozenset[str]:
        """Author terms that should rank first: the frame's grounded holders.

        Derives author tokens from each groundable position's holder label and
        from any ancient-author the position points at, lowercased. An Epictetus
        question reaches Epictetus passages because the holders (Dobbin/Long on
        Epictetus, or Epictetus himself) yield the ``epict`` token via the
        passages' own author key space — we match on whole label tokens too.
        """
        terms: set[str] = set()
        for pid in position_ids:
            pos = self._ground_position(pid) if self._is_groundable(pid) else None
            if pos is None:
                continue
            for source in (pos.holder, pos.claim):
                for tok in _TERM_RE.findall((source or "").lower()):
                    if len(tok) > 3 and tok not in _STOP_TERMS:
                        terms.add(tok)
        return frozenset(terms)

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

    def _passage_ids_via_concepts(
        self,
        node_id: str,
        limit: int,
        priority_authors: frozenset[str] = frozenset(),
    ) -> list[str]:
        """Two-hop passage discovery: node -> concept/argument bridge -> passage.

        Walks outgoing edges from ``node_id`` to neighbours whose type is in
        ``_BRIDGE_NODE_TYPES``, then for each bridge calls the existing
        one-hop ``_passage_ids_for_node``. Returns a deduped, ORDERED list.
        Fan-out is bounded: at most ``_MAX_BRIDGE_NODES`` bridges and at most
        ``limit`` passages total — no live DB calls, pure KG adjacency.

        Candidate ids are ordered by AUTHOR ROUND-ROBIN (relevance-ranked by
        ``priority_authors``) BEFORE the cap, so a single author (e.g. the
        alphabetically-first ``passage_alex_*``) cannot monopolise the slots and
        starve the holder's own author (the Epictetus-surfacing fix).
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

        candidates: list[str] = []
        seen: set[str] = set()
        for bridge_id in bridge_ids:
            for pid in sorted(self._passage_ids_for_node(bridge_id)):
                if pid not in seen:
                    seen.add(pid)
                    candidates.append(pid)
        ordered = self._round_robin_by_author(candidates, priority_authors)
        return ordered[:limit]

    def _contested_passages(
        self, seed_id: str, position_ids: set[str], limit: int
    ) -> list[PassageRef]:
        if limit <= 0:
            return []
        priority_authors = self._priority_authors(position_ids)
        passage_ids: list[str] = []
        seen: set[str] = set()

        # 1-hop direct passages stay FIRST (priority), but within that pass the
        # candidates are author round-robin'd + relevance-ranked so the cap is
        # shared across authors instead of filled by the alphabetically-first.
        direct_candidates: list[str] = []
        direct_seen: set[str] = set()
        for nid in [seed_id, *sorted(position_ids)]:
            for pid in sorted(self._passage_ids_for_node(nid)):
                if pid not in direct_seen:
                    direct_seen.add(pid)
                    direct_candidates.append(pid)
        for pid in self._round_robin_by_author(direct_candidates, priority_authors):
            if pid not in seen:
                seen.add(pid)
                passage_ids.append(pid)
                if len(passage_ids) >= limit:
                    break

        # Second pass: many seed/position nodes have NO direct passage edge —
        # their primary passages sit one concept/argument hop further
        # (argument --discusses--> concept --has_passage--> passage). Only fill
        # the remainder; the helper applies the same author round-robin.
        if len(passage_ids) < limit:
            for nid in [seed_id, *sorted(position_ids)]:
                remaining = limit - len(passage_ids)
                if remaining <= 0:
                    break
                for pid in self._passage_ids_via_concepts(
                    nid, remaining, priority_authors
                ):
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
        return self._quotable_greek_lead(refs)

    @staticmethod
    def _quotable_chars(text: str, language: str) -> int:
        """Quotable original-language character count (Greek OR Latin), shared.

        Greek (polytonic) scores by its Greek-letter count; a Latin original
        (``language`` starts ``la``) scores by its Latin-letter count — so clean
        LATIN passages (Cicero *De Fato*, Boethius, Seneca, Augustine — core
        fate/foreknowledge sources) are NOT demoted into the same partition as
        junk. A markdown ``**Reference:**``/``**Author:**``/``**Work:**`` metadata
        block OR a ``Greek: • … - gloss`` bullet row scores ``-1`` so it never
        leads — quoting either would dump markdown/gloss into scholarly prose.
        """
        low = text.lower()
        if (
            "**reference:**" in low
            or "**author:**" in low
            or "**work:**" in low
            or low.lstrip().startswith("greek:")
            or "•" in text
        ):
            return -1
        greek = sum(1 for ch in text if "Ͱ" <= ch <= "Ͽ" or "ἀ" <= ch <= "῿")
        if greek:
            return greek
        if language.lower().startswith("la"):
            return sum(1 for ch in text if ch.isalpha() and ord(ch) < 0x250)
        return 0

    @classmethod
    def _ref_greek_quotable_chars(cls, ref: PassageRef) -> int:
        """Quotable-original-text score for an assembled ref (Greek OR Latin).

        Reads the already-fetched ``original_text`` (no extra node lookup);
        delegates to :meth:`_quotable_chars` so passage-level and node-level
        ranking agree (gloss/reference junk sinks; clean Latin is not demoted).
        """
        return cls._quotable_chars(ref.original_text or "", ref.language or "")

    def _quotable_greek_lead(self, refs: list[PassageRef]) -> list[PassageRef]:
        """Reorder a frame's contested passages so QUOTABLE-GREEK ones lead (F3).

        STABLE partition: passages carrying substantial quotable Greek keep their
        relevance order but move ahead of reference/metadata-only blocks, so the
        synthesis sees ≥2 quotable-Greek primary passages per dominant fault line
        at the top of the dossier and can quote the strongest one per position
        (original + English) instead of merely citing a locus. Round-robin author
        relevance from ``_round_robin_by_author`` is preserved within the quotable
        and non-quotable partitions. Never drops a passage; never fabricates text.
        """
        if len(refs) <= 1:
            return refs
        quotable = [r for r in refs if self._ref_greek_quotable_chars(r) > 0]
        rest = [r for r in refs if self._ref_greek_quotable_chars(r) <= 0]
        return quotable + rest

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
