"""Deterministic graph-seed step for the ReAct path.

The legacy FSM path (``legacy_fsm_nodes._discover_corpus``) always ran the
retrieval strategy and then ``WeightedTraversal.expand()`` before any LLM turn.
The ReAct path only touched the graph when the model chose to call
``explore_subgraph`` — so two runs of the same question could start from very
different evidence. This module restores the deterministic step in front of
the loop:

1. seeds = the nodes already seeded (entity works pass) + the strategy's
   ``discover_seeds`` output (SQL when wired, snapshot scoring otherwise);
2. ``WeightedTraversal`` expansion from those seeds, bounded by
   ``max_nodes``/``score_threshold`` (the legacy values) and a wall-clock
   budget;
3. the seeds, the expanded nodes and a bounded set of their linked passages
   are pushed through the same ``EvidenceCollector`` ingest paths the tools
   use (``search_nodes`` / ``explore_subgraph`` / ``read_passages``), so a
   later tool call by the model can never duplicate them.

Every failure degrades: the error lands in ``state.metadata['retrieval_errors']``
and the loop starts with whatever was gathered. ``ELEUTHERIA_GRAPH_SEED=false``
turns the step off; ``state.metadata['graph_seed']`` always records what
happened, and its presence is what makes the step run once per query (the
sufficiency continuation round re-enters the loop's ``run()``).
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from eleutheria_graphrag.agents.citability import CitabilityTier, evidence_policy
from eleutheria_graphrag.agents.graph_helpers import node_integrity_status
from eleutheria_graphrag.agents.tools.explore_subgraph import (
    ExploreSubgraphResult,
    SubgraphNode,
)
from eleutheria_graphrag.agents.tools.search_nodes import NodeSummary, SearchNodesResult
from eleutheria_graphrag.services.retrieval_strategy import (
    SnapshotStrategy,
    SQLStrategy,
)
from eleutheria_graphrag.services.weighted_traversal import (
    TraversalResult,
    WeightedTraversal,
)

if TYPE_CHECKING:
    from eleutheria_graphrag.agents.dependencies import Deps
    from eleutheria_graphrag.agents.evidence_collector import EvidenceCollector
    from eleutheria_graphrag.agents.state import RAGState
    from eleutheria_graphrag.agents.tools import ToolRegistry

logger = logging.getLogger(__name__)

GRAPH_SEED_ENV = "ELEUTHERIA_GRAPH_SEED"
GRAPH_SEED_BUDGET_ENV = "ELEUTHERIA_GRAPH_SEED_BUDGET_MS"

# Same bounds the legacy ``WeightedTraversal.expand()`` call used.
GRAPH_SEED_MAX_NODES = 30
GRAPH_SEED_SCORE_THRESHOLD = 0.05
# Wall-clock budget for the whole step (seed discovery + traversal + passages).
DEFAULT_BUDGET_MS = 2000
_MIN_BUDGET_MS = 50
_MAX_BUDGET_MS = 30_000
# Traversal starts from the best-ranked seeds only, so the node cap leaves room
# for the neighbourhood instead of being eaten by a long label-match list.
_MAX_TRAVERSAL_SEEDS = 10
# Passage reads are one DB round-trip each; keep the deterministic step cheap.
_MAX_PASSAGE_ANCHORS = 6
_PASSAGES_PER_ANCHOR = 3
_CONTEXT_LINES = 12


def graph_seed_enabled() -> bool:
    """``ELEUTHERIA_GRAPH_SEED`` — default ON; only an explicit off disables."""
    raw = os.getenv(GRAPH_SEED_ENV)
    if raw is None:
        return True
    return raw.strip().lower() not in {"0", "false", "no", "off"}


def graph_seed_budget_ms() -> int:
    """Wall-clock budget for the step, clamped to a sane range."""
    raw = os.getenv(GRAPH_SEED_BUDGET_ENV)
    if raw is None or not raw.strip():
        return DEFAULT_BUDGET_MS
    try:
        value = int(raw.strip())
    except ValueError:
        logger.warning("Invalid %s=%r, using default", GRAPH_SEED_BUDGET_ENV, raw)
        return DEFAULT_BUDGET_MS
    return max(_MIN_BUDGET_MS, min(_MAX_BUDGET_MS, value))


@dataclass
class GraphSeedReport:
    """What the step did — serialised onto ``state.metadata['graph_seed']``."""

    status: str = "ok"
    seed_nodes: list[str] = field(default_factory=list)
    expanded_nodes: list[str] = field(default_factory=list)
    edges_followed: int = 0
    ms: int = 0
    truncated: bool = False
    passages: int = 0

    def as_metadata(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "seed_nodes": list(self.seed_nodes),
            "expanded_nodes": list(self.expanded_nodes),
            "edges_followed": self.edges_followed,
            "ms": self.ms,
            "truncated": self.truncated,
            "passages": self.passages,
        }


def _record_error(state: RAGState, message: str) -> None:
    state.metadata.setdefault("retrieval_errors", []).append(f"graph_seed: {message}")


def _node_type(node: dict[str, Any]) -> str:
    return str(node.get("type") or "").lower()


def _node_summary(node_id: str, node: dict[str, Any]) -> NodeSummary | None:
    """Mirror ``SearchNodesTool``: tiered, integrity-flagged text withheld."""
    decision = evidence_policy(node)
    if decision.tier is CitabilityTier.BLOCKED:
        return None
    description = ""
    if decision.tier is CitabilityTier.CITABLE and not node_integrity_status(node):
        description = (node.get("description") or "")[:200]
    return NodeSummary(
        node_id=node_id,
        label=node.get("label", ""),
        type=node.get("type", ""),
        description=description,
        period=node.get("period"),
        school=node.get("school"),
        score=1.0,
        evidence_tier=decision.tier.value,
        evidence_notice=decision.prompt_notice,
    )


async def _discover(
    deps: Deps, state: RAGState, *, remaining_s: float, report: GraphSeedReport
) -> list[str]:
    """Run the retrieval strategy's seed discovery under the remaining budget."""
    strategy = deps.retrieval_strategy
    if strategy is None:
        if not deps.node_lookup:
            return []
        strategy = SnapshotStrategy(min_passages=4)
    elif isinstance(strategy, SQLStrategy):
        # No LLM lemma expansion here: the step only needs seed nodes, and the
        # expansion is the one non-deterministic (and slow) part of discovery.
        strategy = strategy.deterministic()

    # Same contract as the legacy node: expose the live state so SQLStrategy can
    # record ontology-aware inferred edges and its own partial failures.
    deps.state = state
    if not isinstance(getattr(state, "inferred_edges", None), set):
        state.inferred_edges = set()

    if remaining_s <= 0:
        report.truncated = True
        _record_error(state, "budget exhausted before seed discovery")
        return []
    try:
        seed_ids, _anchors = await asyncio.wait_for(
            strategy.discover_seeds(
                queries=[state.question],
                deps=deps,
                node_limit=state.retrieval_budget.node_search_limit(),
            ),
            timeout=remaining_s,
        )
    except TimeoutError:
        report.truncated = True
        _record_error(state, f"seed discovery timed out after {remaining_s:.2f}s")
        return []
    except Exception as exc:
        logger.warning("graph seed: seed discovery failed", exc_info=True)
        _record_error(state, f"seed discovery: {exc}")
        return []
    return [str(nid) for nid in seed_ids if nid]


def _traversal(deps: Deps) -> WeightedTraversal | None:
    if deps.traversal is not None:
        return deps.traversal
    if not deps.node_lookup:
        return None
    return WeightedTraversal(
        node_lookup=deps.node_lookup,
        outgoing_edges=deps.outgoing_edges,
        incoming_edges=deps.incoming_edges,
        pagerank_scores=deps.pagerank_scores,
    )


async def _read_passages(
    tools: ToolRegistry | None,
    evidence: EvidenceCollector,
    state: RAGState,
    anchors: list[str],
    *,
    deadline: float,
    report: GraphSeedReport,
) -> None:
    """Pull linked passages for the top anchors through the ``read_passages`` tool.

    Going through the tool (rather than a private fetch) is what keeps this
    idempotent with the model's own reads: ``EvidenceCollector`` dedups on
    passage id either way.
    """
    if tools is None:
        return
    reader = tools.get("read_passages")
    if reader is None:
        return
    for node_id in anchors:
        if time.monotonic() >= deadline:
            report.truncated = True
            break
        args = {"node_id": node_id, "limit": _PASSAGES_PER_ANCHOR}
        try:
            result = await reader.execute(args)
        except Exception as exc:
            logger.warning(
                "graph seed: read_passages(%s) failed", node_id, exc_info=True
            )
            _record_error(state, f"read_passages[{node_id}]: {exc}")
            continue
        before = len(evidence.seen_passage_ids)
        evidence.ingest("read_passages", args, result)
        report.passages += len(evidence.seen_passage_ids) - before


def render_graph_seed_context(
    node_lookup: dict[str, dict[str, Any]],
    added_ids: list[str],
    *,
    passages: int,
) -> str:
    """Prompt block naming what the step newly put in the evidence set."""
    if not added_ids:
        return ""
    shown = added_ids[:_CONTEXT_LINES]
    lines = [
        "Graph neighbourhood already seeded into the evidence set "
        f"({len(added_ids)} nodes, {passages} passages, by deterministic weighted "
        "traversal from the question's seed nodes — these are in hand; read "
        "their passages or move on rather than re-exploring them):"
    ]
    for node_id in shown:
        node = node_lookup.get(node_id, {})
        label = str(node.get("label") or node_id)[:72]
        lines.append(f"- {node_id} — {label} [{node.get('type', '')}]")
    if len(added_ids) > len(shown):
        lines.append(f"- ... and {len(added_ids) - len(shown)} more")
    return "\n".join(lines)


async def seed_graph_context(
    deps: Deps,
    state: RAGState,
    evidence: EvidenceCollector,
    tools: ToolRegistry | None = None,
) -> str:
    """Run the deterministic graph-seed step; return the prompt context block.

    Never raises into the loop: an unexpected failure is recorded on
    ``state.metadata['retrieval_errors']`` and ``state.metadata['graph_seed']``
    and the loop starts with whatever was already gathered.
    """
    if "graph_seed" in state.metadata:
        # Once per query: a continuation round re-enters ``run()`` with the
        # sufficiency feedback appended to the question — re-discovering seeds
        # from that text would only add noise, and the evidence is already in.
        return ""
    report = GraphSeedReport()
    if not graph_seed_enabled():
        report.status = "disabled"
        state.metadata["graph_seed"] = report.as_metadata()
        return ""

    started = time.monotonic()
    deadline = started + graph_seed_budget_ms() / 1000.0
    try:
        context = await _seed(deps, state, evidence, tools, deadline, report)
    except Exception as exc:  # noqa: BLE001 — the loop must start regardless
        logger.warning("graph seed step failed", exc_info=True)
        report.status = "error"
        _record_error(state, str(exc))
        context = ""
    report.ms = int((time.monotonic() - started) * 1000)
    state.metadata["graph_seed"] = report.as_metadata()
    logger.info(
        "graph seed: status=%s seeds=%d expanded=%d edges=%d passages=%d "
        "truncated=%s ms=%d",
        report.status,
        len(report.seed_nodes),
        len(report.expanded_nodes),
        report.edges_followed,
        report.passages,
        report.truncated,
        report.ms,
    )
    return context


async def _seed(
    deps: Deps,
    state: RAGState,
    evidence: EvidenceCollector,
    tools: ToolRegistry | None,
    deadline: float,
    report: GraphSeedReport,
) -> str:
    node_lookup = deps.node_lookup or {}

    # 1. Seeds: what is already seeded + strategy discovery (best-effort).
    discovered = await _discover(
        deps, state, remaining_s=deadline - time.monotonic(), report=report
    )
    candidates = list(
        dict.fromkeys([*evidence.seed_node_ids, *state.seed_node_ids, *discovered])
    )
    seeds = [nid for nid in candidates if nid in node_lookup][:GRAPH_SEED_MAX_NODES]
    if not seeds:
        report.status = "no_seeds"
        return ""

    # Newly discovered seeds enter through the search_nodes path (tiered, dedup).
    new_seed_summaries = [
        summary
        for nid in seeds
        if nid not in evidence.seen_node_ids
        and (summary := _node_summary(nid, node_lookup[nid])) is not None
    ]
    if new_seed_summaries:
        evidence.ingest(
            "search_nodes",
            {"query": state.question, "source": "graph_seed"},
            SearchNodesResult(
                nodes=new_seed_summaries, total_found=len(new_seed_summaries)
            ),
        )
    report.seed_nodes = list(seeds)
    added_ids = [s.node_id for s in new_seed_summaries]

    # 2. Bounded weighted traversal from the best-ranked seeds.
    traversal = _traversal(deps)
    if traversal is None:
        report.status = "no_graph"
        return render_graph_seed_context(node_lookup, added_ids, passages=0)
    result: TraversalResult = traversal.expand_with_stats(
        seeds[:_MAX_TRAVERSAL_SEEDS],
        max_nodes=GRAPH_SEED_MAX_NODES,
        score_threshold=GRAPH_SEED_SCORE_THRESHOLD,
        deadline=deadline,
    )
    report.edges_followed = result.edges_followed
    report.truncated = report.truncated or result.truncated

    # 3. Expanded nodes enter through the explore_subgraph path (dedup on id).
    # Passage nodes are skipped like the tool does; blocked nodes never enter.
    seed_set = set(seeds)
    subgraph_nodes: list[SubgraphNode] = []
    for nid in result.order:
        if nid in seed_set or nid in evidence.seen_node_ids:
            continue
        node = node_lookup.get(nid)
        if not node or _node_type(node) == "passage":
            continue
        if evidence_policy(node).tier is CitabilityTier.BLOCKED:
            continue
        subgraph_nodes.append(
            SubgraphNode(
                node_id=nid,
                label=node.get("label", ""),
                type=node.get("type", ""),
                ppr_score=0.0,
                distance_from_seed=1,
            )
        )
    if subgraph_nodes:
        evidence.ingest(
            "explore_subgraph",
            {"seed_node_ids": seeds[:_MAX_TRAVERSAL_SEEDS], "source": "graph_seed"},
            ExploreSubgraphResult(nodes=subgraph_nodes, seed_count=len(seeds)),
        )
    report.expanded_nodes = [n.node_id for n in subgraph_nodes]
    added_ids.extend(report.expanded_nodes)

    # 4. Linked passages for the top anchors — citable, non-passage nodes only.
    anchors: list[str] = []
    for nid in [*seeds, *report.expanded_nodes]:
        node = node_lookup.get(nid, {})
        if _node_type(node) == "passage":
            continue
        if evidence_policy(node).tier is not CitabilityTier.CITABLE:
            continue
        anchors.append(nid)
        if len(anchors) >= _MAX_PASSAGE_ANCHORS:
            break
    await _read_passages(
        tools, evidence, state, anchors, deadline=deadline, report=report
    )

    return render_graph_seed_context(node_lookup, added_ids, passages=report.passages)
