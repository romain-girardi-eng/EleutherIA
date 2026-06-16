"""
EvidenceCollector — accumulates tool results into RAGState-compatible structures.

Bridges the gap between the agent's tool calls and the synthesis phase
(DraftClaimLedger, RenderGroundedAnswer, ProgrammaticVerify) which expects
populated Evidence, EvidenceBundle, and ContextPack fields in RAGState.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any

from pydantic import BaseModel

from eleutheria_graphrag.agents.graph_helpers import node_integrity_status
from eleutheria_graphrag.agents.state import (
    DIALECTICAL_RELATIONS,
    ContextPack,
    DialecticalEdge,
    Evidence,
    EvidenceBundle,
    EvidenceSource,
    RAGState,
    ResearchNotebook,
    ResearchToolCall,
    RetrievalBudget,
    ScholarlyDossier,
)

logger = logging.getLogger(__name__)


class ToolCallRecord(BaseModel):
    """Audit trail entry for a single tool call."""

    call_id: str
    tool_name: str
    args: dict[str, Any]
    reason: str = ""
    result_summary: str = ""
    node_count: int = 0
    passage_count: int = 0
    duration_ms: int = 0


class EvidenceCollector:
    """Accumulates evidence from agent tool calls."""

    def __init__(self) -> None:
        self.seen_node_ids: set[str] = set()
        self.seen_passage_ids: set[str] = set()
        self.primary_evidence: list[Evidence] = []
        self.secondary_evidence: list[Evidence] = []
        self.evidence_bundles: list[EvidenceBundle] = []
        self.seed_node_ids: list[str] = []
        self.context_node_ids: list[str] = []
        self.inferred_edges: set[tuple[str, str, str]] = set()
        self.dialectical_edges: list[DialecticalEdge] = []
        self._seen_dialectical: set[tuple[str, str, str]] = set()
        self.tool_calls: list[ToolCallRecord] = []

    def ingest(self, tool_name: str, _args: dict[str, Any], result: BaseModel) -> None:
        """Route tool results to appropriate evidence lists."""
        result_dict = result.model_dump()

        if tool_name == "search_nodes":
            self._ingest_search_nodes(result_dict)
        elif tool_name == "explore_subgraph":
            self._ingest_explore_subgraph(result_dict)
        elif tool_name == "get_neighbors":
            self._ingest_get_neighbors(result_dict)
        elif tool_name in ("read_passages", "search_passages"):
            self._ingest_passages(result_dict, tool_name)
        elif tool_name == "get_node_detail":
            self._ingest_node_detail(result_dict)
        elif tool_name == "infer_transitive":
            self._ingest_infer_transitive(result_dict)
        # read_work_section doesn't directly produce evidence

    def record_call(
        self,
        tool_name: str,
        args: dict[str, Any],
        reason: str,
        result_summary: str,
        node_count: int = 0,
        passage_count: int = 0,
        duration_ms: int = 0,
    ) -> None:
        """Record a tool call for the audit trail."""
        self.tool_calls.append(
            ToolCallRecord(
                call_id=f"tc_{len(self.tool_calls) + 1}",
                tool_name=tool_name,
                args=args,
                reason=reason,
                result_summary=result_summary,
                node_count=node_count,
                passage_count=passage_count,
                duration_ms=duration_ms,
            )
        )

    def _record_dialectical_edge(
        self,
        *,
        source_id: str,
        relation: str,
        target_id: str,
        direction: str = "",
        weight: float | None = None,
        source_label: str = "",
        target_label: str = "",
        source_type: str = "",
        target_type: str = "",
    ) -> None:
        """Retain a disagreement-bearing edge (Scholar-RAG M0b).

        Keeps BOTH endpoints + ``relation`` + ``direction`` — the data the old
        ``_ingest_get_neighbors`` dropped (failure-map F1, the "0 edges" root
        cause). Only relations in ``DIALECTICAL_RELATIONS`` are retained;
        duplicate (source, relation, target) triples are collapsed.
        """
        rel = (relation or "").strip()
        if not source_id or not target_id or rel not in DIALECTICAL_RELATIONS:
            return
        key = (source_id, rel, target_id)
        if key in self._seen_dialectical:
            return
        self._seen_dialectical.add(key)
        self.dialectical_edges.append(
            DialecticalEdge(
                source_id=source_id,
                relation=rel,
                target_id=target_id,
                direction=direction,
                weight=weight,
                source_label=source_label,
                target_label=target_label,
                source_type=source_type,
                target_type=target_type,
            )
        )

    def populate_state(self, state: RAGState) -> None:
        """Write accumulated evidence into RAGState for synthesis phase."""
        state.primary_evidence = self.primary_evidence
        state.secondary_evidence = self.secondary_evidence
        state.evidence_bundles = self.evidence_bundles
        state.seed_node_ids = self.seed_node_ids
        state.context_node_ids = self.context_node_ids
        state.dialectical_edges = self.dialectical_edges
        state.passages_used = len(self.evidence_bundles)
        if self.inferred_edges:
            if not isinstance(getattr(state, "inferred_edges", None), set):
                state.inferred_edges = set()
            state.inferred_edges.update(self.inferred_edges)

        # Leave context_pack.prompt_context empty — DraftClaimLedger will
        # call _build_context_pack(state) which builds the proper prompt
        # with P1/N1 reference markers from the evidence we populated.
        state.context_pack = ContextPack()

        # Build research notebook with tool call trail
        if not state.research_notebook:
            state.research_notebook = ResearchNotebook()
        state.research_notebook.tool_calls = [
            ResearchToolCall(
                tool_call_id=tc.call_id,
                tool_name=tc.tool_name,
                stage_id="agent_loop",
                query=tc.args.get("query") or tc.args.get("node_id", ""),
                rationale=tc.reason,
                detail_count=tc.node_count + tc.passage_count,
            )
            for tc in self.tool_calls
        ]

        # Build scholarly dossier (minimal — the synthesis nodes will enrich it)
        state.scholarly_dossier = ScholarlyDossier(
            question_frame=state.question,
            primary_bundle_ids=[b.bundle_id for b in self.evidence_bundles],
        )

    def _ingest_search_nodes(self, result: dict[str, Any]) -> None:
        """Ingest results from search_nodes tool."""
        for node in result.get("nodes", []):
            nid = node.get("node_id", "")
            if nid and nid not in self.seen_node_ids:
                self.seen_node_ids.add(nid)
                self.seed_node_ids.append(nid)
                self.primary_evidence.append(
                    Evidence(
                        id=nid,
                        label=node.get("label", ""),
                        type=node.get("type", ""),
                        description=node.get("description", ""),
                        score=node.get("score", 0.0),
                        source=EvidenceSource.SEMANTIC_SEARCH,
                        period=node.get("period"),
                        school=node.get("school"),
                    )
                )

    def _ingest_explore_subgraph(self, result: dict[str, Any]) -> None:
        """Ingest results from explore_subgraph tool.

        Today's ``ExploreSubgraphResult`` carries only ``nodes``, but the same
        dialectical-edge retention is applied to any ``edges`` the result may
        carry (Scholar-RAG M0b — subgraph results may grow an edge list), so a
        future edge-bearing subgraph never silently drops fault lines.
        """
        node_types = {
            n.get("node_id", ""): n.get("type", "") for n in result.get("nodes", [])
        }
        node_labels = {
            n.get("node_id", ""): n.get("label", "") for n in result.get("nodes", [])
        }
        for edge in result.get("edges", []):
            source_id = edge.get("source", "") or edge.get("source_id", "")
            target_id = edge.get("target", "") or edge.get("target_id", "")
            if not source_id or not target_id:
                continue
            self._record_dialectical_edge(
                source_id=source_id,
                relation=edge.get("relation", ""),
                target_id=target_id,
                direction=edge.get("direction", ""),
                weight=edge.get("weight"),
                source_label=node_labels.get(source_id, ""),
                target_label=node_labels.get(target_id, ""),
                source_type=node_types.get(source_id, ""),
                target_type=node_types.get(target_id, ""),
            )

        for node in result.get("nodes", []):
            nid = node.get("node_id", "")
            if nid and nid not in self.seen_node_ids:
                self.seen_node_ids.add(nid)
                self.context_node_ids.append(nid)
                self.secondary_evidence.append(
                    Evidence(
                        id=nid,
                        label=node.get("label", ""),
                        type=node.get("type", ""),
                        score=node.get("ppr_score", 0.0),
                        source=EvidenceSource.GRAPH_TRAVERSAL,
                    )
                )

    def _ingest_get_neighbors(self, result: dict[str, Any]) -> None:
        """Ingest results from get_neighbors tool.

        Retains the relation + direction + both endpoints of every dialectical
        edge (Scholar-RAG M0b) — the data the old collector dropped, keeping
        only ``edge_node_id`` (failure-map F1, the "0 edges used" root cause).
        """
        center_id = result.get("center_node", "")
        center_label = result.get("center_label", center_id)
        for edge in result.get("edges", []):
            nid = edge.get("edge_node_id", "")
            other_label = edge.get("label", "")
            other_type = edge.get("type", "")

            # Canonicalise source/target from the edge direction so the
            # retained triple matches the underlying KG orientation.
            direction = edge.get("direction", "")
            if direction == "incoming":
                source_id, source_label, source_type = nid, other_label, other_type
                target_id, target_label, target_type = (
                    center_id,
                    center_label,
                    "",
                )
            else:  # "outgoing" or unknown — treat center as the source
                source_id, source_label, source_type = (
                    center_id,
                    center_label,
                    "",
                )
                target_id, target_label, target_type = nid, other_label, other_type

            self._record_dialectical_edge(
                source_id=source_id,
                relation=edge.get("relation", ""),
                target_id=target_id,
                direction=direction,
                weight=edge.get("weight"),
                source_label=source_label,
                target_label=target_label,
                source_type=source_type,
                target_type=target_type,
            )

            if nid and nid not in self.seen_node_ids:
                self.seen_node_ids.add(nid)
                self.context_node_ids.append(nid)
                self.secondary_evidence.append(
                    Evidence(
                        id=nid,
                        label=other_label,
                        type=other_type,
                        source=EvidenceSource.GRAPH_TRAVERSAL,
                    )
                )

    def _ingest_passages(self, result: dict[str, Any], tool_name: str) -> None:
        """Ingest results from read_passages or search_passages tools."""
        passages_key = "passages"
        for p in result.get(passages_key, []):
            pid = p.get("passage_id", "")
            if pid and pid not in self.seen_passage_ids:
                self.seen_passage_ids.add(pid)
                text = p.get("text_content", "")
                translation = p.get("translation") or None
                self.evidence_bundles.append(
                    EvidenceBundle(
                        bundle_id=f"b_{uuid.uuid4().hex[:8]}",
                        work_id=p.get("work_id", ""),
                        work_title=p.get("work_title", ""),
                        author=p.get("author"),
                        canonical_ref=p.get("canonical_ref"),
                        original_passage_id=pid,
                        original_text=text,
                        translation_text=translation,
                        language=p.get("language"),
                        # The context pack emits original AND translation in
                        # full, so the budget must count both.
                        token_estimate=RetrievalBudget.estimate_tokens(
                            "\n".join(part for part in (text, translation) if part)
                        ),
                        source=(
                            EvidenceSource.PASSAGE_CITATION
                            if tool_name == "read_passages"
                            else EvidenceSource.HYBRID_SEARCH
                        ),
                    )
                )

    def _ingest_node_detail(self, result: dict[str, Any]) -> None:
        """Ingest results from get_node_detail tool."""
        nid = result.get("node_id", "")
        if nid and nid not in self.seen_node_ids:
            self.seen_node_ids.add(nid)
            self.context_node_ids.append(nid)
            # Defense-in-depth: the tool already blanks integrity-flagged
            # descriptions, but the result carries metadata, so re-check
            # here — a flagged description must never enter Evidence (it
            # would whitelist its own Greek in the text verifier).
            description = (
                "" if node_integrity_status(result) else result.get("description", "")
            )
            self.primary_evidence.append(
                Evidence(
                    id=nid,
                    label=result.get("label", ""),
                    type=result.get("type", ""),
                    description=description,
                    source=EvidenceSource.DIRECT_LOOKUP,
                    period=result.get("period"),
                    school=result.get("school"),
                )
            )

    def _ingest_infer_transitive(self, result: dict[str, Any]) -> None:
        """Ingest ontology-derived nodes from infer_transitive."""
        start_id = str(result.get("start_node_id") or "")
        if start_id and start_id not in self.seen_node_ids:
            self.seen_node_ids.add(start_id)
            self.context_node_ids.append(start_id)
            self.secondary_evidence.append(
                Evidence(
                    id=start_id,
                    label=str(result.get("start_label") or start_id),
                    source=EvidenceSource.GRAPH_TRAVERSAL,
                    metadata={
                        "tool": "infer_transitive",
                        "relation": result.get("relation"),
                        "role": "start_node",
                    },
                )
            )

        for raw_edge in result.get("inferred_edges", []):
            if isinstance(raw_edge, (list, tuple)) and len(raw_edge) == 3:
                s_id, rel, o_id = (str(raw_edge[0]), str(raw_edge[1]), str(raw_edge[2]))
                if s_id and rel and o_id:
                    self.inferred_edges.add((s_id, rel, o_id))

        for node in result.get("derived_nodes", []):
            nid = str(node.get("node_id") or "")
            if not nid:
                continue
            raw_edge = node.get("inferred_edge")
            if isinstance(raw_edge, (list, tuple)) and len(raw_edge) == 3:
                s_id, rel, o_id = (str(raw_edge[0]), str(raw_edge[1]), str(raw_edge[2]))
                if s_id and rel and o_id:
                    self.inferred_edges.add((s_id, rel, o_id))
            if nid in self.seen_node_ids:
                continue
            self.seen_node_ids.add(nid)
            self.context_node_ids.append(nid)
            self.secondary_evidence.append(
                Evidence(
                    id=nid,
                    label=str(node.get("label") or nid),
                    type=str(node.get("type") or ""),
                    source=EvidenceSource.GRAPH_TRAVERSAL,
                    score=max(0.0, 1.0 / max(1, int(node.get("distance") or 1))),
                    metadata={
                        "tool": "infer_transitive",
                        "relation": result.get("relation"),
                        "inverse_relation": result.get("inverse_relation"),
                        "distance": node.get("distance"),
                        "derivation": node.get("derivation") or [],
                        "inferred_edge": node.get("inferred_edge"),
                    },
                )
            )
