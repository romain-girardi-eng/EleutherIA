"""
Counter-Evidence Hunter — adversarial sub-agent.

For each claim in a synthesized draft, this service actively searches the
corpus and KG for passages, arguments, or scholar positions that contradict,
qualify, or complicate it. The output is fed back into the synthesizer for a
v2 pass that explicitly engages with the opposition.

This is the most epistemically valuable sub-agent: it forces the synthesizer
out of a one-sided reading.

Design notes:
- Uses the same MCP-tool surface as the rest of the pipeline (search_passages,
  explore_subgraph, get_neighbors, get_node_detail). Tools are passed in via a
  duck-typed toolset (any object exposing the right `*_tool` attributes) so
  the service is easy to unit-test with mocks.
- Runs claims in parallel with an asyncio.gather + semaphore (concurrency cap
  defaults to 5, configurable). The hunter LLM call is one per claim.
- Filters out low-force findings before returning — passing mentions of the
  topic are not opposition.
- Strict JSON parsing with defensive fallback. Never trusts the LLM to invent
  citation ids; cross-checks every finding against tool results.
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


# Opposition-flavoured KG edge relations. Drawn from the EleutherIA ontology
# (`knowledge graph/ontology/edge_types.json`). `qualifies` and `presupposes`
# also surface "yes, but…" nuance the synthesizer often glosses over.
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

    The real ScholarlyAgent constructs these from `Deps`; tests pass in mocks.
    """

    search_passages: _ToolLike
    explore_subgraph: _ToolLike
    get_neighbors: _ToolLike | None = None
    get_node_detail: _ToolLike | None = None


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
        """For each major claim, search for opposing testimonia in parallel."""
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
    # Single claim hunt
    # ------------------------------------------------------------------

    async def _hunt_one_bounded(self, claim: ClaimUnit) -> ClaimFinding:
        async with self._sem:
            return await self._hunt_one(claim)

    async def _hunt_one(self, claim: ClaimUnit) -> ClaimFinding:
        passage_hits = await self._search_opposing_passages(claim)
        kg_edges = await self._walk_opposition_edges(claim)

        if not passage_hits and not kg_edges:
            return ClaimFinding(
                claim_id=claim.claim_id,
                claim_text=claim.claim_text,
                opposing_testimonia=[],
            )

        # Build allow-lists so we can reject hallucinated ids from the LLM.
        valid_passage_ids = {
            p["passage_id"] for p in passage_hits if p.get("passage_id")
        }
        valid_node_ids = {e["target"] for e in kg_edges if e.get("target")}
        valid_node_ids.update(e["source"] for e in kg_edges if e.get("source"))

        raw = await self._classify_with_llm(claim, passage_hits, kg_edges)
        testimonia = self._parse_and_validate(
            raw,
            valid_passage_ids=valid_passage_ids,
            valid_node_ids=valid_node_ids,
        )

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

    # ------------------------------------------------------------------
    # Retrieval: passages
    # ------------------------------------------------------------------

    async def _search_opposing_passages(
        self,
        claim: ClaimUnit,
    ) -> list[dict[str, Any]]:
        """Run multiple negation-flavoured searches in parallel.

        We don't ask the corpus for "against X" — passages don't carry meta
        sentiment. Instead we vary the query with contrast prompts and let the
        LLM classifier decide which hits actually oppose the claim.
        """
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

        # Deduplicate by passage_id while preserving order
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
        """Phrase a single claim from multiple contrast angles."""
        text = claim.claim_text.strip()
        # Strip a trailing period for cleaner concatenation
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
        """Coerce a SearchPassagesResult-like object into plain dicts."""
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

    # ------------------------------------------------------------------
    # Retrieval: KG opposition edges
    # ------------------------------------------------------------------

    async def _walk_opposition_edges(
        self,
        claim: ClaimUnit,
    ) -> list[dict[str, Any]]:
        """Expand seed nodes via PPR and filter their edges for opposition relations."""
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

        # If get_neighbors is available, refine: for each seed, fetch real edges
        # and keep only the opposition-flavoured ones.
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

        # Fallback: surface every nearby node as a potential "alternative",
        # tagged with a generic relation so the LLM can still classify it.
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
        """Coerce a get_neighbors response into a flat list of edge dicts."""
        if hasattr(neighbour_result, "model_dump"):
            neighbour_result = neighbour_result.model_dump()
        if isinstance(neighbour_result, dict):
            return list(neighbour_result.get("edges", []) or [])
        return []

    # ------------------------------------------------------------------
    # LLM classification
    # ------------------------------------------------------------------

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
    # Parsing & validation
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_and_validate(
        raw: str,
        *,
        valid_passage_ids: set[str],
        valid_node_ids: set[str],
    ) -> list[OpposingTestimony]:
        """Parse JSON, then filter out hallucinated ids and weak findings."""
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
            # Reject hallucinated citation ids. Allow null for either field.
            if pid and pid not in valid_passage_ids:
                continue
            if nid and nid not in valid_node_ids:
                continue
            if not pid and not nid:
                # Must anchor to at least one real id
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
            summary_lines.append(
                f"- [{f.claim_id}] {f.claim_text[:120]} → {len(f.opposing_testimonia)} "
                f"testimonia ({forces})"
            )
        prompt = AGGREGATE_PROMPT_TEMPLATE.format(
            findings_summary="\n".join(summary_lines)
        )
        try:
            text = await self.llm.generate(prompt, temperature=0.2, max_tokens=200)
        except Exception:
            logger.warning("Aggregate summary LLM call failed", exc_info=True)
            return f"Found {sum(len(f.opposing_testimonia) for f in findings)} opposing testimonia across {len(findings)} claims."
        return text.strip()


# ---------------------------------------------------------------------------
# Two-pass synthesizer integration helpers
# ---------------------------------------------------------------------------


def format_report_for_synthesizer(report: CounterEvidenceReport) -> str:
    """Render a CounterEvidenceReport as a prompt block for synthesizer v2.

    The synthesizer is instructed to engage with each finding explicitly
    ("However, against this view…", "This must be qualified by…").
    """
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
            anchor = t.passage_id or t.source_node_id or "?"
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
    """Run the hunt while yielding per-finding SSE events.

    Wires `hunter.on_finding` to a queue so findings stream as they're
    discovered, then yields the final `counter_evidence_complete` event.
    """
    queue: asyncio.Queue[dict[str, Any] | None] = asyncio.Queue()

    async def _push(evt: dict[str, Any]) -> None:
        await queue.put(evt)

    hunter.on_finding = _push

    async def _runner() -> CounterEvidenceReport:
        try:
            return await hunter.hunt(draft)
        finally:
            await queue.put(None)  # sentinel

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
    # Narrowed by caller, kept as a function for mypy.
    return value  # type: ignore[return-value]


def _cast_force(value: str) -> TestimonyForce:
    return value  # type: ignore[return-value]
