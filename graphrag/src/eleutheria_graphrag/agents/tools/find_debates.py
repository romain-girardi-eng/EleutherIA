"""find_debates tool — the missing relational entry point (Scholar-RAG M1).

The legacy 8 tools are entity-centric: they can find a *person* or a *concept*
but never surface the scholarly *disagreement* layer (the 33 ``debate`` /
``controversy`` / ``position`` nodes + 312 dialectical edges the facet template
never touched). This tool exposes that layer, ranked most-contested-first, so the
agent's FIRST move on any "open debates / controversies / X vs Y / origins"
question is to see the live fault lines rather than reading entity descriptions.

VECTORLESS by construction: ranking is ``lexical-overlap (ts_rank analogue) +
0.15 * least(incoming-dialectical-edge-degree, 40)`` over the in-memory KG —
exactly the SQL in ARCHITECTURE §2.2, evaluated against ``deps.node_lookup`` /
``deps.incoming_edges`` (the snapshot the other vectorless tools already use). No
embeddings anywhere.

Gated by ``ELEUTHERIA_SCHOLAR_RAG``: registered only when the flag is on, so the
default pipeline never sees it.
"""

from __future__ import annotations

import logging
import re
from typing import Any

from pydantic import BaseModel, Field

from eleutheria_graphrag.agents.dependencies import Deps

logger = logging.getLogger(__name__)

_TERM_RE = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿ\u0370-\u03FF\u1F00-\u1FFF']+")

# Node types that represent a scholarly disagreement locus.
DEBATE_TYPES: frozenset[str] = frozenset({"debate", "controversy", "position"})

# Edges whose INCOMING degree signals "how contested is this node" (§2.2 SQL).
CONTESTEDNESS_RELATIONS: frozenset[str] = frozenset(
    {
        "participates_in",
        "contributes_to",
        "has_position",
        "opposes",
        "critiques",
        "responds_to",
    }
)

# Edges that, incident on a debate node, name a participant.
_PARTICIPANT_RELATIONS: frozenset[str] = frozenset(
    {"participates_in", "has_position", "contributes_to", "advanced_in"}
)

# Edges that name a fault line directly (for opposing_pairs surfacing).
_OPPOSING_RELATIONS: frozenset[str] = frozenset(
    {"opposes", "critiques", "refutes", "contrasts_with", "responds_to"}
)


class DebateSummary(BaseModel):
    debate_id: str
    label: str
    type: str
    summary: str = Field(default="", description="Truncated debate description")
    period: str | None = None
    participant_ids: list[str] = Field(default_factory=list)
    opposing_pairs: list[tuple[str, str]] = Field(
        default_factory=list,
        description="(from_id, to_id) pairs from incident dialectical edges",
    )
    grounded_passage_count: int = 0
    degree: int = Field(
        0, description="Incoming dialectical-edge degree (contestedness)"
    )
    score: float = 0.0


class FindDebatesResult(BaseModel):
    debates: list[DebateSummary]
    total_found: int


class FindDebatesTool:
    """Find the scholarly debates / controversies / positions about a topic.

    Returns them most-contested-first so the model sees the live fault lines up
    top. Pure SQL/KG-adjacency ranking — no embeddings.
    """

    def __init__(self, deps: Deps) -> None:
        self._deps = deps

    @property
    def name(self) -> str:
        return "find_debates"

    @property
    def description(self) -> str:
        return (
            "Find the scholarly DEBATES, controversies, and contending positions "
            "about a topic — the disagreement layer of the knowledge graph "
            "(encoded as opposes / critiques / responds_to edges). USE THIS FIRST "
            "for any question about open debates, controversies, origins, or 'X vs "
            "Y' comparisons, before reading entity descriptions. Returns debates "
            "ranked most-contested-first, each with its participants and the "
            "opposing pairs. Then call build_controversy_frame on a debate or "
            "position to assemble its full fault line."
        )

    @property
    def parameters_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": "The topic to find debates about "
                    "(e.g. 'free will', 'discovery of the will', 'fate')",
                },
                "period_filter": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Restrict to these historical periods "
                    "(e.g. exclude Modern/Contemporary for an antiquity question)",
                },
                "limit": {
                    "type": "integer",
                    "default": 8,
                    "minimum": 1,
                    "maximum": 20,
                },
            },
            "required": ["topic"],
        }

    async def execute(self, args: dict[str, Any]) -> FindDebatesResult:
        topic = args["topic"]
        period_filter = args.get("period_filter") or None
        limit = min(max(args.get("limit", 8), 1), 20)

        period_set = (
            {p.strip().lower() for p in period_filter if p and p.strip()}
            if period_filter
            else None
        )

        topic_terms = {t.lower() for t in _TERM_RE.findall(topic) if len(t) > 2}
        topic_lower = topic.lower()

        scored: list[tuple[DebateSummary, float]] = []
        for node_id, node in self._deps.node_lookup.items():
            node_type = (node.get("type") or "").lower()
            if node_type not in DEBATE_TYPES:
                continue
            if (
                period_set is not None
                and (node.get("period") or "").lower() not in period_set
            ):
                continue

            label = (node.get("label") or "").lower()
            desc = (node.get("description") or "").lower()

            # ts_rank analogue: lexical overlap over label + description.
            lex = self._lexical_score(topic_lower, topic_terms, label, desc)

            degree = self._contestedness_degree(node_id)

            # ARCHITECTURE §2.2: ORDER BY lex + 0.15 * least(degree, 40).
            score = lex + 0.15 * min(degree, 40)
            if lex <= 0.0 and degree == 0:
                continue

            participant_ids = self._participant_ids(node_id)
            opposing_pairs = self._opposing_pairs(node_id)
            grounded = self._grounded_passage_count(node_id)

            scored.append(
                (
                    DebateSummary(
                        debate_id=node_id,
                        label=node.get("label", ""),
                        type=node.get("type", ""),
                        summary=(node.get("description") or "")[:300],
                        period=node.get("period"),
                        participant_ids=participant_ids,
                        opposing_pairs=opposing_pairs,
                        grounded_passage_count=grounded,
                        degree=degree,
                        score=round(score, 4),
                    ),
                    score,
                )
            )

        scored.sort(key=lambda x: x[1], reverse=True)
        debates = [d[0] for d in scored[:limit]]
        return FindDebatesResult(debates=debates, total_found=len(scored))

    # ── ranking helpers ──────────────────────────────────────────────────

    @staticmethod
    def _lexical_score(
        topic_lower: str, topic_terms: set[str], label: str, desc: str
    ) -> float:
        if not topic_terms:
            return 0.0
        if topic_lower and topic_lower in label:
            return 1.0
        label_terms = {t.lower() for t in _TERM_RE.findall(label) if len(t) > 2}
        desc_terms = {t.lower() for t in _TERM_RE.findall(desc[:500]) if len(t) > 2}
        label_overlap = len(topic_terms & label_terms)
        desc_overlap = len(topic_terms & desc_terms)
        if label_overlap == 0 and desc_overlap == 0:
            return 0.0
        return min(1.0, 0.4 * label_overlap + 0.1 * desc_overlap)

    def _contestedness_degree(self, node_id: str) -> int:
        """Incoming dialectical-edge degree — the §2.2 LEFT JOIN count."""
        count = 0
        for edge in self._deps.incoming_edges.get(node_id, []):
            if (edge.get("relation") or "") in CONTESTEDNESS_RELATIONS:
                count += 1
        for edge in self._deps.outgoing_edges.get(node_id, []):
            # has_position points debate -> position; count it as contestedness.
            if (edge.get("relation") or "") in CONTESTEDNESS_RELATIONS:
                count += 1
        return count

    def _participant_ids(self, node_id: str) -> list[str]:
        seen: list[str] = []
        for edge in self._deps.incoming_edges.get(node_id, []):
            if (edge.get("relation") or "") in _PARTICIPANT_RELATIONS:
                src = edge.get("source", "")
                if src and src not in seen:
                    seen.append(src)
        for edge in self._deps.outgoing_edges.get(node_id, []):
            if (edge.get("relation") or "") in {"has_position"}:
                tgt = edge.get("target", "")
                if tgt and tgt not in seen:
                    seen.append(tgt)
        return seen[:25]

    def _opposing_pairs(self, node_id: str) -> list[tuple[str, str]]:
        """Direct fault-line pairs incident on the debate node (may be empty).

        Empty here is expected for the two empty debate nodes — those recover
        their pairs through build_controversy_frame's fallback, not here.
        """
        pairs: list[tuple[str, str]] = []
        seen: set[tuple[str, str]] = set()
        for edge in self._deps.outgoing_edges.get(node_id, []):
            if (edge.get("relation") or "") in _OPPOSING_RELATIONS:
                key = (node_id, edge.get("target", ""))
                if key not in seen and key[1]:
                    seen.add(key)
                    pairs.append(key)
        return pairs

    def _grounded_passage_count(self, node_id: str) -> int:
        count = 0
        for edge in self._deps.incoming_edges.get(node_id, []):
            src = edge.get("source", "")
            src_type = (self._deps.node_lookup.get(src, {}).get("type") or "").lower()
            if src_type == "passage":
                count += 1
        return count
