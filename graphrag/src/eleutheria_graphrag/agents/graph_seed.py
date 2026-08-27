"""Deterministic graph-seed step for the ReAct path.

The legacy FSM path (``legacy_fsm_nodes._discover_corpus``) always ran the
retrieval strategy and then ``WeightedTraversal.expand()`` before any LLM turn.
The ReAct path only touched the graph when the model chose to call
``explore_subgraph`` — so two runs of the same question could start from very
different evidence. This module restores the deterministic step in front of
the loop:

1. seeds = the nodes already seeded (entity works pass) + the strategy's
   ``discover_seeds`` output (SQL when wired, snapshot scoring otherwise);
2. ``WeightedTraversal`` expansion from those seeds, bounded by fixed
   ``max_nodes``/``score_threshold`` values and a wall-clock budget;
3. the seeds, the expanded nodes, the passage anchors the strategy returned
   directly and a bounded set of the nodes' linked passages are pushed
   through the same ``EvidenceCollector`` ingest paths the tools use
   (``search_nodes`` / ``explore_subgraph`` / ``read_passages``), so a later
   tool call by the model can never duplicate them.

Every failure degrades: the error lands in ``state.metadata['retrieval_errors']``
and the loop starts with whatever was gathered. ``ELEUTHERIA_GRAPH_SEED=false``
turns the step off; ``state.metadata['graph_seed']`` always records what
happened, and its presence is what makes the step run once per query (the
sufficiency continuation round re-enters the loop's ``run()``).

The ``Deps`` container is a process-wide singleton shared by concurrent
requests, so nothing per-request is ever written onto it: the strategy gets a
shallow per-request copy carrying the live ``RAGState``.
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
from dataclasses import dataclass, field, replace
from typing import TYPE_CHECKING, Any

from eleutheria_graphrag.agents.citability import CitabilityTier, evidence_policy
from eleutheria_graphrag.agents.graph_helpers import node_integrity_status
from eleutheria_graphrag.agents.tools.explore_subgraph import (
    ExploreSubgraphResult,
    SubgraphNode,
)
from eleutheria_graphrag.agents.tools.read_passages import (
    PassageSummary,
    ReadPassagesResult,
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

# ``WeightedTraversal.expand()``'s own defaults. The legacy FSM node expanded
# wider (adaptive ``traversal_node_limit()``, threshold 0.03); this step runs
# under a wall-clock budget before turn 0, so it keeps the tighter fixed bound
# and leaves the wider exploration to the model's own ``explore_subgraph``.
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
# Read slots held back for nodes the traversal added: without them a long
# seed list would take every slot and the expansion would never be read.
_EXPANDED_READ_QUOTA = 3
_PASSAGES_PER_ANCHOR = 3
# Passage anchors the strategy returns directly (passage UUIDs / passage
# nodes) — one batched fetch, capped like the legacy node's anchor list.
_MAX_DIRECT_ANCHORS = 12
_DIRECT_ANCHOR_NODE_ID = "graph_seed:passage_anchors"
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
    # ``truncated``: something was left undone (node cap or clock);
    # ``deadline_hit``: the wall-clock budget is what cut it.
    truncated: bool = False
    deadline_hit: bool = False
    passages: int = 0
    passage_anchors: int = 0

    def timed_out(self, state: RAGState, message: str) -> None:
        self.truncated = True
        self.deadline_hit = True
        _record_error(state, message)

    def as_metadata(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "seed_nodes": list(self.seed_nodes),
            "expanded_nodes": list(self.expanded_nodes),
            "edges_followed": self.edges_followed,
            "ms": self.ms,
            "truncated": self.truncated,
            "deadline_hit": self.deadline_hit,
            "passages": self.passages,
            "passage_anchors": self.passage_anchors,
        }


def _record_error(state: RAGState, message: str) -> None:
    state.metadata.setdefault("retrieval_errors", []).append(f"graph_seed: {message}")


def _node_type(node: dict[str, Any]) -> str:
    return str(node.get("type") or "").lower()


def _readable(node: dict[str, Any]) -> bool:
    """A node worth a ``read_passages`` slot: citable and not itself a passage."""
    if not node or _node_type(node) == "passage":
        return False
    return evidence_policy(node).tier is CitabilityTier.CITABLE


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
    deps: Deps, state: RAGState, *, deadline: float, report: GraphSeedReport
) -> tuple[list[str], list[str]]:
    """Run the retrieval strategy's seed discovery under the remaining budget.

    Returns ``(seed_node_ids, passage_anchor_ids)`` — the strategy's own
    contract; both lists are kept.
    """
    strategy = deps.retrieval_strategy
    if strategy is None:
        if not deps.node_lookup:
            return [], []
        strategy = SnapshotStrategy(min_passages=4)
    elif isinstance(strategy, SQLStrategy):
        # No LLM lemma expansion here: the step only needs seed nodes, and the
        # expansion is the one non-deterministic (and slow) part of discovery.
        strategy = strategy.deterministic()

    # Same contract as the legacy node — the strategy reads ``deps.state`` to
    # record ontology-aware inferred edges and its own partial failures — but
    # on a per-request shallow copy: ``deps`` is shared by concurrent requests
    # and must never carry one request's state.
    if not isinstance(getattr(state, "inferred_edges", None), set):
        state.inferred_edges = set()
    request_deps = replace(deps, state=state)

    remaining_s = deadline - time.monotonic()
    if remaining_s <= 0:
        report.timed_out(state, "budget exhausted before seed discovery")
        return [], []
    kwargs: dict[str, Any] = {}
    if isinstance(strategy, SnapshotStrategy):
        # CPU-bound scan with no await point: ``wait_for`` cannot interrupt
        # it, so the strategy checks the deadline itself.
        kwargs["deadline"] = deadline
    try:
        seed_ids, anchor_ids = await asyncio.wait_for(
            strategy.discover_seeds(
                queries=[state.question],
                deps=request_deps,
                node_limit=state.retrieval_budget.node_search_limit(),
                **kwargs,
            ),
            timeout=remaining_s,
        )
    except TimeoutError:
        report.timed_out(state, f"seed discovery timed out after {remaining_s:.2f}s")
        return [], []
    except Exception as exc:
        logger.warning("graph seed: seed discovery failed", exc_info=True)
        _record_error(state, f"seed discovery: {exc}")
        return [], []
    if time.monotonic() >= deadline:
        # Returned past the deadline: a partial snapshot scan, or a discovery
        # that ran the budget out — everything after it will be cut short.
        report.truncated = True
        report.deadline_hit = True
    return (
        [str(nid) for nid in seed_ids if nid],
        [str(pid) for pid in anchor_ids if pid],
    )


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
        remaining_s = deadline - time.monotonic()
        if remaining_s <= 0:
            report.timed_out(state, f"budget exhausted before read_passages[{node_id}]")
            break
        args = {"node_id": node_id, "limit": _PASSAGES_PER_ANCHOR}
        try:
            result = await asyncio.wait_for(reader.execute(args), timeout=remaining_s)
        except TimeoutError:
            report.timed_out(
                state, f"read_passages[{node_id}] timed out after {remaining_s:.2f}s"
            )
            break
        except Exception as exc:
            logger.warning(
                "graph seed: read_passages(%s) failed", node_id, exc_info=True
            )
            _record_error(state, f"read_passages[{node_id}]: {exc}")
            continue
        before = len(evidence.seen_passage_ids)
        evidence.ingest("read_passages", args, result)
        report.passages += len(evidence.seen_passage_ids) - before


async def _ingest_direct_anchors(
    deps: Deps,
    evidence: EvidenceCollector,
    state: RAGState,
    anchor_ids: list[str],
    *,
    deadline: float,
    report: GraphSeedReport,
) -> None:
    """Ingest the passage anchors the strategy returned directly.

    ``SQLStrategy`` returns raw ``passages.passage_id`` UUIDs (plus KG node
    ids for related-not-exact citations); ``SnapshotStrategy`` returns passage
    node ids. One batched fetch, the same resolver the legacy node used, then
    the ``read_passages`` ingest path (dedup on passage id, tiering kept).
    """
    anchors = [
        pid for pid in dict.fromkeys(anchor_ids) if pid not in evidence.seen_passage_ids
    ][:_MAX_DIRECT_ANCHORS]
    if not anchors:
        return
    report.passage_anchors = len(anchors)
    remaining_s = deadline - time.monotonic()
    if remaining_s <= 0:
        report.timed_out(state, "budget exhausted before the passage anchors")
        return
    # Local import: ``graph_nodes`` is the heavy FSM module and must not be
    # loaded just to import this step.
    from eleutheria_graphrag.agents.graph_nodes import _fetch_passages_for_nodes

    try:
        rows = await asyncio.wait_for(
            _fetch_passages_for_nodes(deps, anchors, limit=_MAX_DIRECT_ANCHORS),
            timeout=remaining_s,
        )
    except TimeoutError:
        report.timed_out(state, f"passage anchors timed out after {remaining_s:.2f}s")
        return
    except Exception as exc:
        logger.warning("graph seed: passage anchor fetch failed", exc_info=True)
        _record_error(state, f"passage anchors: {exc}")
        return
    passages = [
        PassageSummary(
            passage_id=str(row["passage_id"]),
            work_title=row.get("title") or "",
            author=row.get("author"),
            canonical_ref=row.get("canonical_ref"),
            language=row.get("language"),
            text_content=row.get("text_content") or "",
            confidence=float(row.get("confidence") or 0.0),
            evidence_tier=row.get("evidence_tier", "citable"),
            evidence_notice=row.get("evidence_notice", ""),
        )
        for row in rows
        if row.get("passage_id")
    ]
    if not passages:
        return
    before = len(evidence.seen_passage_ids)
    evidence.ingest(
        "read_passages",
        {"node_id": _DIRECT_ANCHOR_NODE_ID, "source": "graph_seed"},
        ReadPassagesResult(
            node_id=_DIRECT_ANCHOR_NODE_ID,
            node_label="Passage anchors from seed discovery",
            passages=passages,
        ),
    )
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
    discovered, direct_anchors = await _discover(
        deps, state, deadline=deadline, report=report
    )
    # The strategy's direct passage hits are evidence whether or not any seed
    # node survives the lookup filter — one batched fetch, ingested first.
    await _ingest_direct_anchors(
        deps, evidence, state, direct_anchors, deadline=deadline, report=report
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
    report.deadline_hit = report.deadline_hit or result.deadline_hit

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
    # Seeds read first, but ``_EXPANDED_READ_QUOTA`` slots are held back for
    # the nodes the traversal added, so a long seed list cannot starve them.
    seed_anchors = [nid for nid in seeds if _readable(node_lookup.get(nid, {}))]
    expanded_anchors = [
        nid for nid in report.expanded_nodes if _readable(node_lookup.get(nid, {}))
    ]
    reserved = min(_EXPANDED_READ_QUOTA, len(expanded_anchors))
    anchors = seed_anchors[: _MAX_PASSAGE_ANCHORS - reserved]
    anchors.extend(expanded_anchors[: _MAX_PASSAGE_ANCHORS - len(anchors)])
    await _read_passages(
        tools, evidence, state, anchors, deadline=deadline, report=report
    )

    return render_graph_seed_context(node_lookup, added_ids, passages=report.passages)
