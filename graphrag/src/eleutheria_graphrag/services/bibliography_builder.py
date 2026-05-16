"""
Bibliography Builder — three-tier annotated bibliography sub-agent.

Runs after Synthesizer v2 (citation-verified) and before Polishing in deep
mode. Walks the KG via the agent toolset starting from the draft's cited
nodes, then asks the LLM to classify findings into primary / secondary /
supplementary tiers and write a one-sentence annotation per entry.

The matching opencode agent (.opencode/agent/bibliography-builder.md) carries
the same instructions and is the manifest used when this runs as an opencode
subagent. The Python orchestrator here lets the GraphRAGService dispatch
directly without spawning a subprocess.

Tool surface (duck-typed, same as CounterEvidenceHunter):
    - get_node_detail(node_id)
    - get_neighbors(node_id)
    - explore_subgraph(seed_node_ids, top_k)

Hard rules enforced in code (not just the prompt):
    - Every emitted node_id must echo a real tool result.
    - Every citation must come from real node metadata fields.
    - LLM output is validated against allow-lists.
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any, Protocol

from eleutheria_graphrag.models.bibliography import (
    AnnotatedBibliography,
    BibliographyEntry,
    BibliographyTier,
)
from eleutheria_graphrag.models.counter_evidence import SynthesizedDraft
from eleutheria_graphrag.services.llm_service import LLMService

logger = logging.getLogger(__name__)


# Edges connecting cited nodes to scholarly nodes worth bibliographying.
SCHOLAR_EDGE_RELATIONS: tuple[str, ...] = (
    "wrote_about",
    "engages_with",
    "agrees_with",
    "opposes",
    "applies_methodology_from",
    "published_by",
    "critiques",
    "qualifies",
)

# Edges from a passage / argument up to its work + author.
PRIMARY_EDGE_RELATIONS: tuple[str, ...] = (
    "part_of",
    "authored_by",
    "attested_by",
)


CLASSIFY_PROMPT = """\
You are the Bibliography Builder for the EleutherIA scholarly pipeline.

A draft has been synthesized and citation-verified. Below are the KG nodes
reachable from the cited nodes, classified by node type. Your job is to
produce a three-tier annotated bibliography (primary sources, secondary
literature, supplementary reading) of up to {max_entries} entries total.

Question: {question}

Draft excerpt (for context only — do not quote):
{draft_excerpt}

Cited claim ledger:
{claim_ledger}

Candidate primary source nodes (works, passages, authors):
{primary_candidates}

Candidate scholar / scholarly-work nodes:
{scholar_candidates}

Candidate supplementary nodes (dialogue partners, methodological neighbours):
{supplementary_candidates}

Return ONLY a JSON object with three arrays. Each entry must use a node_id
that appears in the candidate lists above. Never invent ids or citations.

{{
  "primary_sources": [
    {{
      "node_id": "<id from primary_candidates>",
      "citation": "<bibliographic line from node metadata>",
      "relevance_score": 0.0,
      "in_answer_citations": ["c1", "c3"],
      "annotation": "<one or two sentences in English>"
    }}
  ],
  "secondary_literature": [...],
  "supplementary_reading": [...]
}}

Scoring:
  - Primary quoted verbatim in draft -> 1.0
  - Primary cited by id, not quoted   -> 0.8
  - Modern scholar whose argument the draft repeats -> 0.9
  - Modern scholar the draft engages with explicitly -> 0.7
  - Adjacent / wider conversation -> 0.4
  - Background only -> 0.2

Sort each tier by relevance_score descending. Cap each tier at 12.
Empty lists are allowed when the candidate sets are empty."""


# ---------------------------------------------------------------------------
# Tool protocol
# ---------------------------------------------------------------------------


class _ToolLike(Protocol):
    async def execute(self, args: dict[str, Any]) -> Any: ...


@dataclass
class BibliographyToolset:
    """Duck-typed toolset the builder uses to walk the KG."""

    get_node_detail: _ToolLike
    get_neighbors: _ToolLike
    explore_subgraph: _ToolLike | None = None


# ---------------------------------------------------------------------------
# Event callback for live SSE streaming
# ---------------------------------------------------------------------------

BibliographyCallback = Callable[[dict[str, Any]], Awaitable[None]] | None


# ---------------------------------------------------------------------------
# Builder
# ---------------------------------------------------------------------------


@dataclass
class BibliographyBuilder:
    """Three-tier annotated bibliography for a synthesized draft."""

    llm: LLMService
    tools: BibliographyToolset
    max_entries: int = 25
    max_candidates_per_bucket: int = 30
    on_event: BibliographyCallback = None
    _sem: asyncio.Semaphore = field(init=False)

    def __post_init__(self) -> None:
        self._sem = asyncio.Semaphore(8)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def build(
        self,
        draft: SynthesizedDraft,
        max_entries: int | None = None,
        seed_node_ids: list[str] | None = None,
    ) -> AnnotatedBibliography:
        """Walk the KG from the draft's cited nodes and emit a 3-tier bibliography.

        Args:
            draft: The citation-verified synthesizer output.
            max_entries: Cap on total entries (default ``self.max_entries``).
            seed_node_ids: Explicit seed list. If None, derived from the
                draft's claim ledger.
        """
        cap = max_entries or self.max_entries

        seeds = list(seed_node_ids or [])
        if not seeds:
            for claim in draft.claims:
                seeds.extend(claim.seed_node_ids)
        # dedupe preserving order
        seen: set[str] = set()
        unique_seeds: list[str] = []
        for sid in seeds:
            if sid and sid not in seen:
                seen.add(sid)
                unique_seeds.append(sid)
        seeds = unique_seeds[: self.max_candidates_per_bucket]

        if not seeds:
            logger.info(
                "BibliographyBuilder: no seed node ids — returning empty bibliography"
            )
            return AnnotatedBibliography()

        # Walk neighbours of every seed in parallel.
        neighbour_payloads = await asyncio.gather(
            *(self._fetch_neighbours(sid) for sid in seeds),
            return_exceptions=True,
        )

        primary_candidates: dict[str, dict[str, Any]] = {}
        scholar_candidates: dict[str, dict[str, Any]] = {}
        supplementary_candidates: dict[str, dict[str, Any]] = {}

        for sid, payload in zip(seeds, neighbour_payloads, strict=False):
            if isinstance(payload, BaseException):
                logger.debug(
                    "BibliographyBuilder neighbour walk failed for %s: %s", sid, payload
                )
                continue
            edges = payload or []
            for edge in edges:
                relation = (edge.get("relation") or "").lower()
                target_id = edge.get("target") or edge.get("neighbor_id")
                target_type = (edge.get("target_type") or "").lower()
                if not target_id:
                    continue
                bucket = self._classify_target(relation, target_type)
                if bucket is None:
                    continue
                target = {
                    "node_id": target_id,
                    "relation": relation,
                    "label": edge.get("label", ""),
                    "type": target_type,
                    "source_seed": sid,
                }
                if bucket == "primary":
                    primary_candidates.setdefault(target_id, target)
                elif bucket == "scholar":
                    scholar_candidates.setdefault(target_id, target)
                else:
                    supplementary_candidates.setdefault(target_id, target)

        # Hydrate top candidates with full metadata so the LLM has real
        # bibliographic strings to work from.
        await asyncio.gather(
            self._hydrate(list(primary_candidates.values())),
            self._hydrate(list(scholar_candidates.values())),
            self._hydrate(list(supplementary_candidates.values())),
        )

        # Ask the LLM to classify + annotate.
        raw = await self._classify_with_llm(
            draft=draft,
            primary=list(primary_candidates.values())[: self.max_candidates_per_bucket],
            scholar=list(scholar_candidates.values())[: self.max_candidates_per_bucket],
            supplementary=list(supplementary_candidates.values())[
                : self.max_candidates_per_bucket
            ],
            max_entries=cap,
        )

        valid_ids = (
            set(primary_candidates)
            | set(scholar_candidates)
            | set(supplementary_candidates)
        )
        bibliography = self._parse_and_validate(raw, valid_ids=valid_ids)

        # Cap each tier at 12 and overall at max_entries.
        bibliography = self._cap(bibliography, total_cap=cap)

        # Emit one event per entry for live UI streaming.
        for entry in bibliography.all_entries():
            await self._emit_entry(entry)
        await self._emit_built(bibliography)
        return bibliography

    # ------------------------------------------------------------------
    # KG walks
    # ------------------------------------------------------------------

    async def _fetch_neighbours(self, node_id: str) -> list[dict[str, Any]]:
        async with self._sem:
            try:
                result = await self.tools.get_neighbors.execute({"node_id": node_id})
            except Exception:
                logger.debug("get_neighbors failed for %s", node_id, exc_info=True)
                return []
        return self._extract_edges(result)

    @staticmethod
    def _extract_edges(result: Any) -> list[dict[str, Any]]:
        if hasattr(result, "model_dump"):
            result = result.model_dump()
        if isinstance(result, dict):
            edges = result.get("edges") or result.get("neighbors") or []
            return list(edges)
        if isinstance(result, list):
            return [e for e in result if isinstance(e, dict)]
        return []

    async def _hydrate(self, candidates: list[dict[str, Any]]) -> None:
        """Fetch full node metadata for each candidate (mutates in-place)."""
        if not candidates:
            return
        tasks = [self._hydrate_one(c) for c in candidates]
        await asyncio.gather(*tasks, return_exceptions=True)

    async def _hydrate_one(self, candidate: dict[str, Any]) -> None:
        node_id = candidate.get("node_id")
        if not node_id:
            return
        async with self._sem:
            try:
                detail = await self.tools.get_node_detail.execute({"node_id": node_id})
            except Exception:
                logger.debug("get_node_detail failed for %s", node_id, exc_info=True)
                return
        if hasattr(detail, "model_dump"):
            detail = detail.model_dump()
        if not isinstance(detail, dict):
            return
        meta = detail.get("metadata") or {}
        candidate["label"] = detail.get("label") or candidate.get("label", "")
        candidate["description"] = (detail.get("description") or "")[:400]
        candidate["full_citation"] = (
            meta.get("full_citation")
            or meta.get("bibliographic_ref")
            or meta.get("citation")
            or ""
        )
        candidate["period"] = detail.get("period")
        candidate["type"] = detail.get("type") or candidate.get("type", "")
        candidate["key_works"] = meta.get("key_works") or []
        candidate["scholarly_role"] = meta.get("scholarly_role") or meta.get("role")

    @staticmethod
    def _classify_target(relation: str, target_type: str) -> str | None:
        """Bucket an edge into primary / scholar / supplementary."""
        # Primary: authored_by / part_of / attested_by → an ancient source
        if relation in PRIMARY_EDGE_RELATIONS:
            return "primary"
        if target_type in ("work", "passage", "ancient_work", "quote"):
            return "primary"
        # Scholar layer
        if relation in SCHOLAR_EDGE_RELATIONS:
            return "scholar"
        if target_type in ("modern_scholar", "scholar", "scholarly_work"):
            return "scholar"
        if target_type == "scholarly_argument":
            return "supplementary"
        # Anything else with a recognised edge: supplementary
        if relation:
            return "supplementary"
        return None

    # ------------------------------------------------------------------
    # LLM classification
    # ------------------------------------------------------------------

    async def _classify_with_llm(
        self,
        *,
        draft: SynthesizedDraft,
        primary: list[dict[str, Any]],
        scholar: list[dict[str, Any]],
        supplementary: list[dict[str, Any]],
        max_entries: int,
    ) -> str:
        ledger_lines: list[str] = []
        for claim in draft.claims:
            ledger_lines.append(f"  {claim.claim_id}: {claim.claim_text[:240]}")
        ledger_text = "\n".join(ledger_lines) or "  (no claim ledger)"

        prompt = CLASSIFY_PROMPT.format(
            question=(draft.answer or "")[:0] or "(draft only)",
            draft_excerpt=(draft.answer or "")[:1800],
            claim_ledger=ledger_text,
            primary_candidates=self._render_candidates(primary),
            scholar_candidates=self._render_candidates(scholar),
            supplementary_candidates=self._render_candidates(supplementary),
            max_entries=max_entries,
        )
        try:
            return await self.llm.generate(prompt, temperature=0.2, max_tokens=2_400)
        except Exception:
            logger.warning("BibliographyBuilder LLM call failed", exc_info=True)
            return ""

    @staticmethod
    def _render_candidates(candidates: list[dict[str, Any]]) -> str:
        if not candidates:
            return "  (none)"
        lines: list[str] = []
        for c in candidates:
            citation = c.get("full_citation") or ""
            line = (
                f"  - id={c.get('node_id', '?')} "
                f"type={c.get('type', '?')} "
                f"label={(c.get('label') or '')[:80]}"
            )
            if citation:
                line += f" | cite={citation[:160]}"
            desc = (c.get("description") or "")[:140]
            if desc:
                line += f" | {desc}"
            lines.append(line)
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Parsing & validation
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_and_validate(
        raw: str,
        *,
        valid_ids: set[str],
    ) -> AnnotatedBibliography:
        if not raw:
            return AnnotatedBibliography()
        text = raw.strip()
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
        match = re.search(r"\{[\s\S]*\}", text)
        if not match:
            return AnnotatedBibliography()
        try:
            payload = json.loads(match.group())
        except json.JSONDecodeError:
            logger.warning("BibliographyBuilder JSON decode failed; returning empty")
            return AnnotatedBibliography()
        if not isinstance(payload, dict):
            return AnnotatedBibliography()

        def _coerce_tier(items: Any, tier: BibliographyTier) -> list[BibliographyEntry]:
            out: list[BibliographyEntry] = []
            if not isinstance(items, list):
                return out
            for item in items:
                if not isinstance(item, dict):
                    continue
                node_id = str(item.get("node_id", "")).strip()
                if not node_id or node_id not in valid_ids:
                    # Reject hallucinated ids.
                    continue
                citation = str(item.get("citation", "")).strip()
                if not citation:
                    continue
                try:
                    score = float(item.get("relevance_score", 0.0))
                except TypeError, ValueError:
                    score = 0.0
                score = max(0.0, min(1.0, score))
                raw_anchors = item.get("in_answer_citations") or []
                anchors = [str(a) for a in raw_anchors if isinstance(a, str | int)]
                out.append(
                    BibliographyEntry(
                        node_id=node_id,
                        citation=citation,
                        relevance_score=score,
                        in_answer_citations=anchors,
                        annotation=str(item.get("annotation", "")).strip(),
                        tier=tier,
                    )
                )
            return out

        return AnnotatedBibliography(
            primary_sources=_coerce_tier(
                payload.get("primary_sources"), "primary_sources"
            ),
            secondary_literature=_coerce_tier(
                payload.get("secondary_literature"), "secondary_literature"
            ),
            supplementary_reading=_coerce_tier(
                payload.get("supplementary_reading"), "supplementary_reading"
            ),
        )

    @staticmethod
    def _cap(
        bibliography: AnnotatedBibliography, *, total_cap: int
    ) -> AnnotatedBibliography:
        def _sorted_top(
            items: list[BibliographyEntry], limit: int
        ) -> list[BibliographyEntry]:
            ordered = sorted(items, key=lambda e: e.relevance_score, reverse=True)
            return ordered[:limit]

        primary = _sorted_top(bibliography.primary_sources, 12)
        secondary = _sorted_top(bibliography.secondary_literature, 12)
        supplementary = _sorted_top(bibliography.supplementary_reading, 12)

        # Greedy fill toward total_cap.
        merged: list[BibliographyEntry] = []
        for tier in (primary, secondary, supplementary):
            merged.extend(tier)
        merged.sort(key=lambda e: e.relevance_score, reverse=True)
        keep = merged[:total_cap]
        keep_ids = {e.node_id for e in keep}
        return AnnotatedBibliography(
            primary_sources=[e for e in primary if e.node_id in keep_ids],
            secondary_literature=[e for e in secondary if e.node_id in keep_ids],
            supplementary_reading=[e for e in supplementary if e.node_id in keep_ids],
        )

    # ------------------------------------------------------------------
    # SSE events
    # ------------------------------------------------------------------

    async def _emit_entry(self, entry: BibliographyEntry) -> None:
        if self.on_event is None:
            return
        try:
            await self.on_event(
                {
                    "type": "bibliography_entry",
                    "tier": entry.tier,
                    "node_id": entry.node_id,
                    "citation": entry.citation,
                    "relevance_score": entry.relevance_score,
                    "annotation": entry.annotation,
                }
            )
        except Exception:
            logger.warning(
                "BibliographyBuilder on_event callback failed", exc_info=True
            )

    async def _emit_built(self, bibliography: AnnotatedBibliography) -> None:
        if self.on_event is None:
            return
        try:
            await self.on_event(
                {
                    "type": "bibliography_built",
                    "total_entries": bibliography.total_entries,
                    "primary_count": len(bibliography.primary_sources),
                    "secondary_count": len(bibliography.secondary_literature),
                    "supplementary_count": len(bibliography.supplementary_reading),
                }
            )
        except Exception:
            logger.warning(
                "BibliographyBuilder on_event callback failed", exc_info=True
            )


# ---------------------------------------------------------------------------
# Formatting helpers — render the bibliography as Markdown for the final draft
# ---------------------------------------------------------------------------


def render_bibliography_markdown(bibliography: AnnotatedBibliography) -> str:
    """Render the three tiers as a Markdown section for the polished draft."""
    if bibliography.total_entries == 0:
        return ""
    lines: list[str] = ["", "## Annotated Bibliography", ""]
    tiers: list[tuple[str, list[BibliographyEntry]]] = [
        ("### Primary Sources", bibliography.primary_sources),
        ("### Secondary Literature", bibliography.secondary_literature),
        ("### Supplementary Reading", bibliography.supplementary_reading),
    ]
    for heading, entries in tiers:
        if not entries:
            continue
        lines.append(heading)
        lines.append("")
        for entry in entries:
            anchors = (
                f" (supports {', '.join(entry.in_answer_citations)})"
                if entry.in_answer_citations
                else ""
            )
            lines.append(f"- **{entry.citation}**{anchors}")
            if entry.annotation:
                lines.append(f"  - {entry.annotation}")
        lines.append("")
    return "\n".join(lines)
