"""
Counter-Evidence Hunter v2 — adversarial sub-agent across 5 dimensions.

v1 surfaced only direct passage contradiction. v2 audits each claim along
five orthogonal axes of disagreement and runs them in parallel:

  1. Passage contradiction      — corpus says the opposite (v1, retained)
  2. Scholar critique           — modern scholar engages_with(critiques|opposes)
                                  the claim's position (Wave 6: 164 scholars,
                                  ~5,800 engagement edges)
  3. Period shift               — later school / period reacts to the claim via
                                  member_of(school) + responds_to / revises /
                                  precedes edges
  4. Doxographical alternative  — same fragment has rival modern reconstructions
                                  (Bobzien vs Salles vs Sharples on Chrysippus
                                  cylinder, etc.)
  5. Consensus dispute          — scholarly_consensus_topics flags an
                                  unresolved methodological dispute touching
                                  the claim's concepts/persons

Each dimension is independent; one missing dimension never fails the hunt.
The ``consensus_dispute`` dimension is gated on a sibling-workstream table
(scholarly_consensus_topics) and degrades silently when absent.

Design notes:
- Same MCP-tool surface as v1, plus ``query_scholarly_consensus`` for the
  consensus dimension. The toolset is duck-typed for unit tests.
- All five dimensions run via asyncio.gather; the per-claim semaphore caps
  in-flight claims at ``concurrency`` (default 5).
- Strict id validation: hallucinated passage_ids / node_ids are still
  rejected. New dimension fields (scholar, school, fragment, topic_slug) are
  populated only when the tool actually returned them.
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
from collections.abc import AsyncIterator, Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any, Protocol

from eleutheria_graphrag.models.counter_evidence import (
    ClaimFinding,
    ClaimUnit,
    CounterEvidenceReport,
    OpposingTestimony,
    SynthesizedDraft,
    TestimonyForce,
    TestimonyType,
)
from eleutheria_graphrag.services.llm_service import LLMService

logger = logging.getLogger(__name__)


# Opposition-flavoured KG edge relations. Drawn from the EleutherIA ontology.
OPPOSITION_EDGES: tuple[str, ...] = (
    "critiques",
    "argues_against",
    "refutes",
    "rejects",
    "contrasts_with",
    "opposes",
    "qualifies",
    "disagrees_with",
)

# engages_with stances that count as disagreement (Wave 6 scholar enrichment).
SCHOLAR_OPPOSITION_STANCES: frozenset[str] = frozenset(
    {"critiques", "opposes", "qualifies"}
)

# Edges that signal a chronological / school-level reaction to an earlier claim.
PERIOD_SHIFT_EDGES: tuple[str, ...] = (
    "responds_to",
    "revises",
    "precedes",
    "follows",
    "extends",
    "qualifies",
    "critiques",
)


HUNT_PROMPT_TEMPLATE = """\
You are a philosophical devil's advocate for the EleutherIA scholarly pipeline.

A synthesizer has produced this claim:

  CLAIM: {claim_text}
  ANCHORS: {anchors}

You have run searches over the corpus and KG. Below are the raw results.
Classify each piece of evidence and return strict JSON.

Type:
  - contradiction = source denies the claim
  - qualification = source adds a limit the synthesizer missed
  - alternative   = rival school / scholar / position

Force:
  - strong   = explicit sustained argument by a primary or major authority
  - moderate = clear but brief counter-argument
  - weak     = passing mention only — discard, do NOT return weak findings

Raw passage hits:
{passage_hits}

Raw KG opposition edges (source -- relation --> target):
{kg_edges}

Return ONLY this JSON shape (no markdown, no commentary):
{{
  "opposing_testimonia": [
    {{
      "type": "contradiction|qualification|alternative",
      "source": "<author, work, locus or scholar name>",
      "source_node_id": "<KG node id or null>",
      "passage_id": "<passage id or null>",
      "excerpt": "<verbatim excerpt from the tool results>",
      "force": "strong|moderate",
      "brief_reasoning": "<one sentence>"
    }}
  ]
}}

If nothing in the raw results genuinely opposes the claim, return an empty list.
Never invent ids or excerpts. Echo only what appears in the raw results above."""


AGGREGATE_PROMPT_TEMPLATE = """\
You audited a synthesized draft for missing counter-evidence. Findings per claim:

{findings_summary}

In 2-3 sentences, name where the draft is most one-sided and which claims
most need rebalancing. Be specific. No preamble."""


# ---------------------------------------------------------------------------
# Tool protocol — what the hunter needs from the agent toolset
# ---------------------------------------------------------------------------


class _ToolLike(Protocol):
    async def execute(self, args: dict[str, Any]) -> Any: ...


@dataclass
class MCPToolset:
    """Duck-typed bundle of the MCP tools the hunter calls.

    The real ScholarlyAgent constructs these from ``Deps``; tests pass in mocks.
    The new ``query_scholarly_consensus`` slot is optional — when absent the
    consensus dimension is skipped silently.
    """

    search_passages: _ToolLike
    explore_subgraph: _ToolLike
    get_neighbors: _ToolLike | None = None
    get_node_detail: _ToolLike | None = None
    query_scholarly_consensus: _ToolLike | None = None


# ---------------------------------------------------------------------------
# Event callback — for live SSE streaming back to the frontend
# ---------------------------------------------------------------------------

CounterEvidenceCallback = Callable[[dict[str, Any]], Awaitable[None]] | None


# ---------------------------------------------------------------------------
# Hunter
# ---------------------------------------------------------------------------


@dataclass
class CounterEvidenceHunter:
    """Adversarial search service. One hunt = one CounterEvidenceReport."""

    llm: LLMService
    tools: MCPToolset
    concurrency: int = 5
    max_passage_hits_per_claim: int = 6
    max_kg_hits_per_claim: int = 10
    max_scholar_hits_per_claim: int = 6
    max_period_shift_hits_per_claim: int = 6
    max_doxographical_hits_per_claim: int = 4
    max_consensus_hits_per_claim: int = 3
    on_finding: CounterEvidenceCallback = None  # async (event_dict) -> None
    _sem: asyncio.Semaphore = field(init=False)

    def __post_init__(self) -> None:
        # Hard cap concurrency to keep Fireworks under its rate limit.
        bounded = max(1, min(int(self.concurrency), 5))
        self._sem = asyncio.Semaphore(bounded)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def hunt(self, draft: SynthesizedDraft) -> CounterEvidenceReport:
        """For each major claim, audit all five dimensions in parallel."""
        if not draft.claims:
            return CounterEvidenceReport(
                per_claim_findings=[],
                aggregate_summary="No claims extracted from draft; nothing to audit.",
            )

        tasks = [self._hunt_one_bounded(claim) for claim in draft.claims]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        findings: list[ClaimFinding] = []
        for claim, result in zip(draft.claims, results, strict=False):
            if isinstance(result, BaseException):
                logger.warning(
                    "Counter-evidence hunt failed for claim %s: %s",
                    claim.claim_id,
                    result,
                )
                findings.append(
                    ClaimFinding(
                        claim_id=claim.claim_id,
                        claim_text=claim.claim_text,
                        opposing_testimonia=[],
                    )
                )
            else:
                findings.append(result)

        aggregate = await self._summarize(findings)
        return CounterEvidenceReport(
            per_claim_findings=findings,
            aggregate_summary=aggregate,
        )

    async def hunt_one(self, claim: ClaimUnit) -> ClaimFinding:
        """Public entry point for a single claim — useful for tests."""
        return await self._hunt_one_bounded(claim)

    # ------------------------------------------------------------------
    # Single claim hunt — runs all five dimensions in parallel
    # ------------------------------------------------------------------

    async def _hunt_one_bounded(self, claim: ClaimUnit) -> ClaimFinding:
        async with self._sem:
            return await self._hunt_one(claim)

    async def _hunt_one(self, claim: ClaimUnit) -> ClaimFinding:
        dim_results = await asyncio.gather(
            self.hunt_passage_contradiction(claim),
            self.hunt_scholar_critiques(claim),
            self.hunt_period_shifts(claim),
            self.hunt_doxographical_alternatives(claim),
            self.hunt_consensus_disputes(claim),
            return_exceptions=True,
        )

        testimonia: list[OpposingTestimony] = []
        for idx, res in enumerate(dim_results):
            if isinstance(res, BaseException):
                logger.warning(
                    "Counter-evidence dimension %d failed for %s: %s",
                    idx,
                    claim.claim_id,
                    res,
                )
                continue
            testimonia.extend(res)

        # Emit SSE events for live streaming
        if self.on_finding is not None:
            for t in testimonia:
                try:
                    await self.on_finding(
                        {
                            "type": "counter_evidence_found",
                            "claim_id": claim.claim_id,
                            "testimony_type": t.type,
                            "source": t.source,
                            "excerpt": t.excerpt,
                            "force": t.force,
                        }
                    )
                except Exception:
                    logger.warning("on_finding callback failed", exc_info=True)

        return ClaimFinding(
            claim_id=claim.claim_id,
            claim_text=claim.claim_text,
            opposing_testimonia=testimonia,
        )

    # ==================================================================
    # Dimension 1 — Passage contradiction (v1, retained)
    # ==================================================================

    async def hunt_passage_contradiction(
        self, claim: ClaimUnit
    ) -> list[OpposingTestimony]:
        passage_hits = await self._search_opposing_passages(claim)
        kg_edges = await self._walk_opposition_edges(claim)

        if not passage_hits and not kg_edges:
            return []

        valid_passage_ids = {
            p["passage_id"] for p in passage_hits if p.get("passage_id")
        }
        valid_node_ids = {e["target"] for e in kg_edges if e.get("target")}
        valid_node_ids.update(e["source"] for e in kg_edges if e.get("source"))

        raw = await self._classify_with_llm(claim, passage_hits, kg_edges)
        return self._parse_and_validate(
            raw,
            valid_passage_ids=valid_passage_ids,
            valid_node_ids=valid_node_ids,
        )

    # ------------------------------------------------------------------
    # Dimension 1 helpers — passage + KG retrieval
    # ------------------------------------------------------------------

    async def _search_opposing_passages(
        self,
        claim: ClaimUnit,
    ) -> list[dict[str, Any]]:
        queries = self._build_contrast_queries(claim)
        per_query_limit = max(
            2, self.max_passage_hits_per_claim // max(1, len(queries))
        )

        async def _one(query: str) -> list[dict[str, Any]]:
            try:
                result = await self.tools.search_passages.execute(
                    {"query": query, "limit": per_query_limit}
                )
            except Exception:
                logger.warning("search_passages failed for %r", query, exc_info=True)
                return []
            return self._normalize_passages(result)

        all_hits: list[dict[str, Any]] = []
        for hits in await asyncio.gather(*(_one(q) for q in queries)):
            all_hits.extend(hits)

        seen: set[str] = set()
        unique: list[dict[str, Any]] = []
        for hit in all_hits:
            pid = hit.get("passage_id") or ""
            if pid and pid not in seen:
                seen.add(pid)
                unique.append(hit)
        return unique[: self.max_passage_hits_per_claim]

    @staticmethod
    def _build_contrast_queries(claim: ClaimUnit) -> list[str]:
        text = claim.claim_text.strip()
        if text.endswith((".", ",", ";", "!", "?")):
            text = text[:-1]
        keyword_blob = " ".join(claim.keywords[:3]) if claim.keywords else text
        return [
            f"objections to: {text}",
            f"critique of {keyword_blob}",
            f"counter-argument {keyword_blob}",
        ]

    @staticmethod
    def _normalize_passages(result: Any) -> list[dict[str, Any]]:
        passages = getattr(result, "passages", None)
        if passages is None and isinstance(result, dict):
            passages = result.get("passages")
        if not passages:
            return []
        out: list[dict[str, Any]] = []
        for p in passages:
            if hasattr(p, "model_dump"):
                out.append(p.model_dump())
            elif isinstance(p, dict):
                out.append(p)
        return out

    async def _walk_opposition_edges(
        self,
        claim: ClaimUnit,
    ) -> list[dict[str, Any]]:
        seeds = claim.seed_node_ids[:5]
        if not seeds:
            return []

        try:
            result = await self.tools.explore_subgraph.execute(
                {"seed_node_ids": seeds, "top_k": 25}
            )
        except Exception:
            logger.warning("explore_subgraph failed", exc_info=True)
            return []

        nodes = getattr(result, "nodes", None) or []
        if hasattr(result, "model_dump"):
            nodes = result.model_dump().get("nodes", [])

        edges: list[dict[str, Any]] = []
        if self.tools.get_neighbors is not None:
            for seed in seeds:
                try:
                    nbr = await self.tools.get_neighbors.execute({"node_id": seed})
                except Exception:
                    continue
                raw_edges = self._extract_edges(nbr)
                for e in raw_edges:
                    relation = (e.get("relation") or "").lower()
                    if relation in OPPOSITION_EDGES:
                        edges.append(
                            {
                                "source": e.get("source") or seed,
                                "relation": relation,
                                "target": e.get("target") or e.get("neighbor_id") or "",
                                "label": e.get("label", ""),
                            }
                        )
                        if len(edges) >= self.max_kg_hits_per_claim:
                            return edges
            return edges

        for n in nodes[: self.max_kg_hits_per_claim]:
            data = n if isinstance(n, dict) else n.model_dump()
            edges.append(
                {
                    "source": seeds[0],
                    "relation": "neighbour",
                    "target": data.get("node_id", ""),
                    "label": data.get("label", ""),
                }
            )
        return edges

    @staticmethod
    def _extract_edges(neighbour_result: Any) -> list[dict[str, Any]]:
        if hasattr(neighbour_result, "model_dump"):
            neighbour_result = neighbour_result.model_dump()
        if isinstance(neighbour_result, dict):
            return list(neighbour_result.get("edges", []) or [])
        return []

    # ==================================================================
    # Dimension 2 — Scholar critique via engages_with(critiques|opposes)
    # ==================================================================

    async def hunt_scholar_critiques(self, claim: ClaimUnit) -> list[OpposingTestimony]:
        if self.tools.get_neighbors is None or not claim.seed_node_ids:
            return []

        seeds = claim.seed_node_ids[:5]
        scholar_edges: list[dict[str, Any]] = []

        async def _fetch(seed: str) -> list[dict[str, Any]]:
            try:
                nbr = await self.tools.get_neighbors.execute(  # type: ignore[union-attr]
                    {"node_id": seed, "relation_filter": "engages_with", "limit": 30}
                )
            except Exception:
                logger.debug("engages_with lookup failed for %s", seed, exc_info=True)
                return []
            return self._extract_edges(nbr)

        per_seed = await asyncio.gather(*(_fetch(s) for s in seeds))
        seen: set[tuple[str, str]] = set()
        for seed, edges in zip(seeds, per_seed, strict=False):
            for e in edges:
                metadata = e.get("metadata") or {}
                stance = (metadata.get("stance") or "").lower()
                if stance not in SCHOLAR_OPPOSITION_STANCES:
                    continue
                # Resolve the "other end" of the edge — the scholar.
                src = e.get("source") or ""
                tgt = e.get("target") or ""
                if src == seed:
                    scholar_node = tgt
                elif tgt == seed:
                    scholar_node = src
                else:
                    # Seed isn't on the edge; skip rather than mis-attribute.
                    continue
                if not scholar_node or scholar_node == seed:
                    continue
                key = (scholar_node, stance)
                if key in seen:
                    continue
                seen.add(key)
                scholar_edges.append(
                    {
                        "scholar_node_id": scholar_node,
                        "stance": stance,
                        "label": e.get("label") or "",
                        "scholarly_work": metadata.get("scholarly_work")
                        or metadata.get("publication")
                        or "",
                        "summary": metadata.get("summary")
                        or e.get("description")
                        or "",
                        "page_ref": metadata.get("page_ref")
                        or metadata.get("page")
                        or "",
                    }
                )
                if len(scholar_edges) >= self.max_scholar_hits_per_claim:
                    break
            if len(scholar_edges) >= self.max_scholar_hits_per_claim:
                break

        testimonia: list[OpposingTestimony] = []
        for hit in scholar_edges:
            summary = hit.get("summary") or hit.get("label") or ""
            if not summary:
                # Without a substantive summary, classify as moderate; never weak.
                summary = (
                    f"Scholar {hit['scholar_node_id']} {hit['stance']} the position."
                )
            force: TestimonyForce = (
                "strong" if hit["stance"] == "opposes" else "moderate"
            )
            testimonia.append(
                OpposingTestimony(
                    type="scholar_critique",
                    source=hit.get("label") or hit["scholar_node_id"],
                    source_node_id=hit["scholar_node_id"],
                    passage_id=None,
                    excerpt=summary[:600],
                    force=force,
                    brief_reasoning=(
                        f"engages_with(stance={hit['stance']}) "
                        f"on a node cited by the claim."
                    ),
                    scholar=hit["scholar_node_id"],
                    scholarly_work=hit.get("scholarly_work") or None,
                    stance=hit["stance"],
                    summary=summary,
                    page_ref=hit.get("page_ref") or None,
                )
            )
        return testimonia

    # ==================================================================
    # Dimension 3 — Period-shift detection
    # ==================================================================

    async def hunt_period_shifts(self, claim: ClaimUnit) -> list[OpposingTestimony]:
        if self.tools.get_neighbors is None or not claim.seed_node_ids:
            return []

        seeds = claim.seed_node_ids[:5]

        async def _fetch(seed: str) -> list[dict[str, Any]]:
            try:
                nbr = await self.tools.get_neighbors.execute(  # type: ignore[union-attr]
                    {"node_id": seed, "limit": 30}
                )
            except Exception:
                return []
            return self._extract_edges(nbr)

        per_seed = await asyncio.gather(*(_fetch(s) for s in seeds))

        # Resolve seed periods first so we can detect shifts.
        seed_periods: dict[str, str] = {}
        if self.tools.get_node_detail is not None:
            for seed in seeds:
                try:
                    detail = await self.tools.get_node_detail.execute({"node_id": seed})
                except Exception:
                    continue
                payload = (
                    detail.model_dump() if hasattr(detail, "model_dump") else detail
                )
                if isinstance(payload, dict):
                    period = payload.get("period")
                    if period:
                        seed_periods[seed] = str(period)

        testimonia: list[OpposingTestimony] = []
        seen_shifts: set[tuple[str, str]] = set()
        for seed, edges in zip(seeds, per_seed, strict=False):
            for e in edges:
                relation = (e.get("relation") or "").lower()
                if relation not in PERIOD_SHIFT_EDGES:
                    continue
                target = e.get("target") if e.get("source") == seed else e.get("source")
                if not target or target == seed:
                    continue
                target_period = await self._fetch_period(target)
                from_period = seed_periods.get(seed, "")
                if not target_period or target_period == from_period:
                    continue
                shift_key = (target, target_period)
                if shift_key in seen_shifts:
                    continue
                seen_shifts.add(shift_key)
                metadata = e.get("metadata") or {}
                school = metadata.get("school") or ""
                summary = (
                    metadata.get("summary")
                    or e.get("description")
                    or f"{target_period} thinkers react via {relation}."
                )
                testimonia.append(
                    OpposingTestimony(
                        type="period_shift",
                        source=e.get("label") or target,
                        source_node_id=target,
                        passage_id=None,
                        excerpt=summary[:600],
                        force="moderate",
                        brief_reasoning=(
                            f"{target_period} response to {from_period or 'earlier'} "
                            f"position via {relation}."
                        ),
                        from_period=from_period or None,
                        to_period=target_period,
                        school=school or None,
                        response_summary=summary,
                        evidence_passage_ids=list(
                            metadata.get("evidence_passage_ids") or []
                        ),
                    )
                )
                if len(testimonia) >= self.max_period_shift_hits_per_claim:
                    return testimonia
        return testimonia

    async def _fetch_period(self, node_id: str) -> str:
        if self.tools.get_node_detail is None:
            return ""
        try:
            detail = await self.tools.get_node_detail.execute({"node_id": node_id})
        except Exception:
            return ""
        payload = detail.model_dump() if hasattr(detail, "model_dump") else detail
        if isinstance(payload, dict):
            return str(payload.get("period") or "")
        return ""

    # ==================================================================
    # Dimension 4 — Doxographical alternative readings
    # ==================================================================

    async def hunt_doxographical_alternatives(
        self, claim: ClaimUnit
    ) -> list[OpposingTestimony]:
        if not claim.seed_node_ids or self.tools.get_node_detail is None:
            return []

        seeds = claim.seed_node_ids[:5]
        testimonia: list[OpposingTestimony] = []

        for seed in seeds:
            try:
                detail = await self.tools.get_node_detail.execute({"node_id": seed})
            except Exception:
                continue
            payload = detail.model_dump() if hasattr(detail, "model_dump") else detail
            if not isinstance(payload, dict):
                continue
            metadata = payload.get("metadata") or {}
            fragment = (
                metadata.get("fragment")
                or metadata.get("fragment_locus")
                or metadata.get("svf_ref")
                or metadata.get("dk_ref")
                or metadata.get("ls_ref")
                or ""
            )
            interpretations = (
                metadata.get("interpretations")
                or metadata.get("doxographical_alternatives")
                or metadata.get("alternative_readings")
                or []
            )
            if not fragment or not interpretations:
                continue
            for interp in interpretations:
                if not isinstance(interp, dict):
                    continue
                reading = (
                    interp.get("interpretation")
                    or interp.get("reading")
                    or interp.get("summary")
                    or ""
                )
                scholarly_source = (
                    interp.get("scholar")
                    or interp.get("source")
                    or interp.get("citation")
                    or ""
                )
                if not reading or not scholarly_source:
                    continue
                testimonia.append(
                    OpposingTestimony(
                        type="doxographical_alternative",
                        source=scholarly_source,
                        source_node_id=seed,
                        passage_id=None,
                        excerpt=reading[:600],
                        force="moderate",
                        brief_reasoning=(
                            f"Rival reconstruction of {fragment} by {scholarly_source}."
                        ),
                        fragment=str(fragment),
                        alternative_interpretation=reading,
                        scholarly_source=str(scholarly_source),
                    )
                )
                if len(testimonia) >= self.max_doxographical_hits_per_claim:
                    return testimonia
        return testimonia

    # ==================================================================
    # Dimension 5 — Scholarly consensus disputes (graceful degradation)
    # ==================================================================

    async def hunt_consensus_disputes(
        self, claim: ClaimUnit
    ) -> list[OpposingTestimony]:
        if self.tools.query_scholarly_consensus is None:
            return []
        if not claim.seed_node_ids:
            return []

        concepts = [n for n in claim.seed_node_ids if n.startswith("concept_")]
        persons = [n for n in claim.seed_node_ids if n.startswith("person_")]
        # If we can't classify, fall back to passing everything as concept ids.
        if not concepts and not persons:
            concepts = list(claim.seed_node_ids[:5])

        try:
            result = await self.tools.query_scholarly_consensus.execute(
                {
                    "concepts": concepts,
                    "persons": persons,
                    "limit": self.max_consensus_hits_per_claim,
                }
            )
        except Exception:
            logger.info("consensus DB not available", exc_info=True)
            return []

        payload = result.model_dump() if hasattr(result, "model_dump") else result
        if not isinstance(payload, dict):
            return []
        if payload.get("table_available") is False:
            logger.debug("consensus dimension skipped — table absent")
            return []
        topics = payload.get("topics") or []

        testimonia: list[OpposingTestimony] = []
        for topic in topics[: self.max_consensus_hits_per_claim]:
            if not isinstance(topic, dict):
                continue
            slug = topic.get("topic_slug")
            if not slug:
                continue
            warning = topic.get("methodological_warning") or topic.get("label") or ""
            positions = list(topic.get("positions") or [])
            testimonia.append(
                OpposingTestimony(
                    type="consensus_dispute",
                    source=topic.get("label") or slug,
                    source_node_id=None,
                    passage_id=None,
                    excerpt=warning[:600],
                    force="moderate",
                    brief_reasoning=(
                        "Unresolved scholarly dispute in scholarly_consensus_topics."
                    ),
                    topic_slug=str(slug),
                    methodological_warning=warning,
                    positions=positions,
                )
            )
        return testimonia

    # ==================================================================
    # LLM classification (used only by the passage-contradiction dim)
    # ==================================================================

    async def _classify_with_llm(
        self,
        claim: ClaimUnit,
        passage_hits: list[dict[str, Any]],
        kg_edges: list[dict[str, Any]],
    ) -> str:
        passage_summary = (
            "\n".join(
                f"  - [{p.get('passage_id', '?')}] "
                f"{(p.get('work_title') or '')[:80]}: "
                f"{(p.get('text_content') or '')[:280]}"
                for p in passage_hits
            )
            or "  (none)"
        )
        kg_summary = (
            "\n".join(
                f"  - {e.get('source', '?')} --{e.get('relation', '?')}--> "
                f"{e.get('target', '?')} ({e.get('label', '')})"
                for e in kg_edges
            )
            or "  (none)"
        )
        prompt = HUNT_PROMPT_TEMPLATE.format(
            claim_text=claim.claim_text,
            anchors=", ".join(claim.seed_node_ids) or "(none)",
            passage_hits=passage_summary,
            kg_edges=kg_summary,
        )
        return await self.llm.generate(prompt, temperature=0.4, max_tokens=900)

    # ------------------------------------------------------------------
    # Parsing & validation (passage-contradiction dim)
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_and_validate(
        raw: str,
        *,
        valid_passage_ids: set[str],
        valid_node_ids: set[str],
    ) -> list[OpposingTestimony]:
        if not raw:
            return []
        match = re.search(r"\{[\s\S]*\}", raw)
        if not match:
            return []
        try:
            payload = json.loads(match.group())
        except json.JSONDecodeError:
            logger.warning("Hunter returned invalid JSON; dropping payload")
            return []

        items = payload.get("opposing_testimonia") or []
        out: list[OpposingTestimony] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            ttype = item.get("type")
            force = item.get("force")
            if ttype not in ("contradiction", "qualification", "alternative"):
                continue
            if force not in ("strong", "moderate"):
                # Drop weak findings — system prompt forbids them.
                continue
            pid = item.get("passage_id")
            nid = item.get("source_node_id")
            if pid and pid not in valid_passage_ids:
                continue
            if nid and nid not in valid_node_ids:
                continue
            if not pid and not nid:
                continue
            out.append(
                OpposingTestimony(
                    type=_cast_type(ttype),
                    source=str(item.get("source", "")).strip() or "unknown",
                    source_node_id=nid or None,
                    passage_id=pid or None,
                    excerpt=str(item.get("excerpt", ""))[:600],
                    force=_cast_force(force),
                    brief_reasoning=str(item.get("brief_reasoning", "")).strip(),
                )
            )
        return out

    # ------------------------------------------------------------------
    # Aggregation
    # ------------------------------------------------------------------

    async def _summarize(self, findings: list[ClaimFinding]) -> str:
        if not findings or all(not f.opposing_testimonia for f in findings):
            return "No significant counter-evidence found in the corpus."
        summary_lines = []
        for f in findings:
            if not f.opposing_testimonia:
                continue
            forces = ",".join(t.force for t in f.opposing_testimonia)
            dims = ",".join(sorted({t.type for t in f.opposing_testimonia}))
            summary_lines.append(
                f"- [{f.claim_id}] {f.claim_text[:120]} → "
                f"{len(f.opposing_testimonia)} testimonia "
                f"({forces}; dims: {dims})"
            )
        prompt = AGGREGATE_PROMPT_TEMPLATE.format(
            findings_summary="\n".join(summary_lines)
        )
        try:
            text = await self.llm.generate(prompt, temperature=0.2, max_tokens=220)
        except Exception:
            logger.warning("Aggregate summary LLM call failed", exc_info=True)
            return (
                f"Found {sum(len(f.opposing_testimonia) for f in findings)} "
                f"opposing testimonia across {len(findings)} claims."
            )
        return text.strip()


# ---------------------------------------------------------------------------
# Two-pass synthesizer integration helpers
# ---------------------------------------------------------------------------


def format_report_for_synthesizer(report: CounterEvidenceReport) -> str:
    """Render a CounterEvidenceReport as a prompt block for synthesizer v2."""
    if not report.per_claim_findings:
        return ""
    lines: list[str] = [
        "## COUNTER-EVIDENCE (from adversarial sub-agent — engage with this)",
        "",
        "For your v2 revision, you MUST explicitly engage with each finding below.",
        "Use phrases like: 'However, against this view, X argues...',",
        "'This position must be qualified by Y, who notes...',",
        "'An alternative reading, defended by Z, holds that...'.",
        "",
    ]
    for f in report.per_claim_findings:
        if not f.opposing_testimonia:
            continue
        lines.append(f"### Claim [{f.claim_id}]: {f.claim_text}")
        for t in f.opposing_testimonia:
            anchor = t.passage_id or t.source_node_id or t.topic_slug or "?"
            lines.append(
                f"- [{t.force.upper()} {t.type}] {t.source} ({anchor}) — "
                f"{t.brief_reasoning}"
            )
            if t.excerpt:
                lines.append(f"    > {t.excerpt[:240]}")
        lines.append("")
    if report.aggregate_summary:
        lines.append(f"OVERALL: {report.aggregate_summary}")
    return "\n".join(lines)


async def stream_counter_evidence_events(
    hunter: CounterEvidenceHunter,
    draft: SynthesizedDraft,
) -> AsyncIterator[dict[str, Any]]:
    """Run the hunt while yielding per-finding SSE events."""
    queue: asyncio.Queue[dict[str, Any] | None] = asyncio.Queue()

    async def _push(evt: dict[str, Any]) -> None:
        await queue.put(evt)

    hunter.on_finding = _push

    async def _runner() -> CounterEvidenceReport:
        try:
            return await hunter.hunt(draft)
        finally:
            await queue.put(None)

    task = asyncio.create_task(_runner())
    while True:
        evt = await queue.get()
        if evt is None:
            break
        yield evt
    report = await task
    yield {
        "type": "counter_evidence_complete",
        "total_testimonia": report.total_testimonia,
        "aggregate_summary": report.aggregate_summary,
    }


# ---------------------------------------------------------------------------
# Tiny helpers (mypy-friendly literal casting)
# ---------------------------------------------------------------------------


def _cast_type(value: str) -> TestimonyType:
    return value  # type: ignore[return-value]


def _cast_force(value: str) -> TestimonyForce:
    return value  # type: ignore[return-value]
