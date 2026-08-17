"""
Legacy FSM-only pydantic-graph nodes (ELEUTHERIA_AGENT_MODE=fsm fallback).

The production pipeline (react mode) uses only ClassifyQueryType,
DraftClaimLedger, RenderGroundedAnswer and ProgrammaticVerify, which live in
``graph_nodes`` together with the shared helpers. This module holds the
nodes that are reachable exclusively through the legacy 12-node FSM entry
point (``ScholarlyAgent._run_fsm``):

    ExpandQuery -> DiscoverCorpus -> BuildResearchNotebook -> PlanReading
      -> TreeNavigateWorks -> ExpandEvidenceBundles -> SeekCounterEvidence
      -> EvidenceSufficiency

plus their FSM-only orchestration helpers and the historical compatibility
wrappers. The code is moved verbatim from ``graph_nodes`` — shared helpers
are imported back from there.
"""

from __future__ import annotations

import asyncio
import logging
import re
import time as _time
from dataclasses import dataclass
from typing import Any

from pydantic_graph import BaseNode, End, GraphRunContext

from eleutheria_graphrag.agents.dependencies import Deps
from eleutheria_graphrag.agents.graph_nodes import (
    COUNTER_EVIDENCE_PROMPT,
    EXPAND_QUERY_PROMPT,
    FRAME_RESEARCH_PROMPT,
    READING_PLAN_PROMPT,
    SYSTEM_PROMPT,
    TREE_NAVIGATION_PROMPT,
    ClassifyQueryType,
    DraftClaimLedger,
    ProgrammaticVerify,
    _append_reasoning_step,
    _batch_fetch_translations,
    _build_context_from_evidence,
    _build_context_pack,
    _build_scholarly_dossier,
    _bundle_academic_features,
    _bundle_prompt_dict,
    _candidate_work_titles,
    _default_expansion,
    _default_research_facets,
    _ensure_notebook,
    _expand_graph,
    _fetch_passages_for_nodes,
    _make_answer,
    _make_evidence_from_node,
    _merge_expansion_terms,
    _normalize_notebook_facets,
    _parse_json,
    _quality_badge_from_state,
    _render_answer_fallback,
    _resolve_model_api_id,
    _search_queries,
    _select_passage_anchors,
    _should_minimize_llm_calls,
    _supplemental_passage_bundles,
    _trace_stage,
    _verify_answer_programmatically,
    assess_evidence_sufficiency,
)
from eleutheria_graphrag.agents.state import (
    Evidence,
    EvidenceBundle,
    EvidenceLayer,
    EvidenceSource,
    RAGState,
    ReadingDecision,
    ReadingNote,
    ResearchToolCall,
    RetrievalBudget,
    ScholarlyAnswer,
)
from eleutheria_graphrag.agents.structured_models import (
    CounterEvidenceResult,
    ExpansionTerms,
    ReadingPlanResult,
    ResearchFrame,
    TreeNavigationResult,
)
from eleutheria_graphrag.agents.text_utils import truncate_json, truncate_text
from eleutheria_graphrag.services.retrieval_strategy import (
    SnapshotStrategy,
    SQLStrategy,
)
from eleutheria_graphrag.services.snapshot_retrieval import db_is_connected

logger = logging.getLogger(__name__)


async def _discover_corpus(ctx: GraphRunContext[RAGState, Deps]) -> None:
    """Shared discovery step used by the active pipeline."""
    state = ctx.state
    budget = state.retrieval_budget
    queries = _search_queries(state)
    trace_payload: dict[str, Any] = {
        "queries": queries,
        "semantic_hits": [],
        "seed_node_ids": [],
        "passage_anchor_ids": [],
        "linked_passages": [],
    }
    if not queries:
        _trace_stage(state, "discover_corpus", trace_payload)
        return

    # --- Strategy-based corpus discovery ---
    limit = budget.node_search_limit()

    # Vectorless pipeline: SQL when database is connected, snapshot otherwise.
    # The legacy "vector" mode is silently treated as "auto" for backward
    # compatibility with stored request payloads.
    strategy = ctx.deps.retrieval_strategy
    if strategy is None:
        if db_is_connected(ctx.deps.db):
            strategy = SQLStrategy(min_bundles=4)
            logger.info("Using SQLStrategy (database-backed retrieval)")
        else:
            strategy = SnapshotStrategy(min_passages=4)
            logger.info("Using SnapshotStrategy (snapshot fallback)")

    seed_ids: list[str] = []
    passage_anchor_ids: list[str] = []

    if strategy is not None:
        # Expose the live RAGState on Deps so the retrieval strategy can
        # record ontology-aware inferred edges for proof-chain emission.
        # Reset on each discovery pass — stale inferences would be wrong.
        ctx.deps.state = state
        if not isinstance(getattr(state, "inferred_edges", None), set):
            state.inferred_edges = set()
        seed_ids, passage_anchor_ids = await strategy.discover_seeds(
            queries=queries,
            deps=ctx.deps,
            node_limit=limit,
        )

        # If the configured strategy returned nothing, fall back to the
        # remaining surface (snapshot when DB is unavailable, SQL otherwise).
        if not seed_ids:
            if db_is_connected(ctx.deps.db) and not isinstance(strategy, SQLStrategy):
                logger.info(
                    "Primary strategy returned no seeds, retrying via SQLStrategy"
                )
                fallback: SQLStrategy | SnapshotStrategy = SQLStrategy(min_bundles=4)
                fallback_mode = "sql"
            elif not db_is_connected(ctx.deps.db) and not isinstance(
                strategy, SnapshotStrategy
            ):
                logger.info(
                    "Primary strategy returned no seeds, retrying via SnapshotStrategy"
                )
                fallback = SnapshotStrategy(min_passages=4)
                fallback_mode = "snapshot"
            else:
                fallback = None  # type: ignore[assignment]
                fallback_mode = ""

            if fallback is not None:
                seed_ids, passage_anchor_ids = await fallback.discover_seeds(
                    queries=queries,
                    deps=ctx.deps,
                    node_limit=limit,
                )
                state.metadata["retrieval_mode_used"] = fallback_mode
            else:
                state.metadata["retrieval_mode_used"] = (
                    "sql" if isinstance(strategy, SQLStrategy) else "snapshot"
                )
        else:
            state.metadata["retrieval_mode_used"] = (
                "sql"
                if isinstance(strategy, SQLStrategy)
                else "snapshot"
                if isinstance(strategy, SnapshotStrategy)
                else state.retrieval_mode
            )

        # Filter seeds to those in node_lookup and build evidence
        existing = state.all_node_ids()
        valid_seeds: list[str] = []
        valid_anchors: list[str] = []
        for node_id in seed_ids:
            if node_id in existing or node_id not in ctx.deps.node_lookup:
                continue
            evidence = _make_evidence_from_node(
                node_id,
                ctx.deps.node_lookup[node_id],
                source=EvidenceSource.SEMANTIC_SEARCH,
            )
            if evidence.evidence_tier == "blocked":
                continue
            if (
                evidence.layer == EvidenceLayer.PRIMARY
                and evidence.evidence_tier == "citable"
            ):
                state.primary_evidence.append(evidence)
            else:
                state.secondary_evidence.append(evidence)
            existing.add(node_id)
            valid_seeds.append(node_id)
            if (
                evidence.layer == EvidenceLayer.PRIMARY
                and evidence.evidence_tier == "citable"
                and evidence.type.lower() != "passage"
                and len(valid_anchors) < 12
            ):
                valid_anchors.append(node_id)

        seed_ids = valid_seeds
        passage_anchor_ids = _select_passage_anchors(
            valid_anchors, passage_anchor_ids, ctx.deps.node_lookup
        )

        state.seed_node_ids = list(dict.fromkeys(state.seed_node_ids + seed_ids))
        state.metadata["passage_anchor_ids"] = passage_anchor_ids
        trace_payload["seed_node_ids"] = state.seed_node_ids[:20]

        _record_tool_call(
            state,
            tool_name="search_entities",
            stage_id="discover_corpus",
            query=" | ".join(queries[:4]),
            rationale=f"strategy-based discovery ({state.metadata.get('retrieval_mode_used', 'auto')})",
            selected_ids=seed_ids[:20],
            details={
                "queries": queries[:8],
                "hit_count": len(seed_ids),
            },
        )
        if seed_ids:
            _record_reading_decision(
                state,
                stage_id="discover_corpus",
                decision_type="seed_selection",
                title="Select high-value seed nodes",
                rationale="Strategy-selected seeds become the starting corpus map.",
                selected_ids=seed_ids[:20],
            )

    traversal_limit = state.retrieval_budget.traversal_node_limit()
    try:
        if ctx.deps.traversal and state.seed_node_ids:
            expanded_ids = ctx.deps.traversal.expand(
                seed_ids=state.seed_node_ids,
                max_nodes=traversal_limit,
                score_threshold=0.03,
            )
        else:
            expanded_ids = _expand_graph(
                ctx.deps,
                state.seed_node_ids,
                depth=2,
                max_nodes=traversal_limit,
            )
    except Exception:
        expanded_ids = _expand_graph(
            ctx.deps,
            state.seed_node_ids,
            depth=2,
            max_nodes=traversal_limit,
        )

    _record_tool_call(
        state,
        tool_name="expand_graph_context",
        stage_id="discover_corpus",
        rationale="expand immediate KG neighborhood around seed nodes",
        selected_ids=list(expanded_ids)[:20],
        details={
            "seed_count": len(state.seed_node_ids),
            "expanded_count": len(expanded_ids),
            "traversal_limit": traversal_limit,
        },
    )

    for node_id in expanded_ids:
        if node_id in existing or node_id not in ctx.deps.node_lookup:
            continue
        evidence = _make_evidence_from_node(
            node_id,
            ctx.deps.node_lookup[node_id],
            source=EvidenceSource.GRAPH_TRAVERSAL,
        )
        if evidence.evidence_tier == "blocked":
            continue
        if (
            evidence.layer == EvidenceLayer.PRIMARY
            and evidence.evidence_tier == "citable"
        ):
            state.primary_evidence.append(evidence)
        else:
            state.secondary_evidence.append(evidence)
        existing.add(node_id)

    state.context_node_ids = list(existing)

    if not passage_anchor_ids:
        passage_anchor_ids = state.seed_node_ids[:12]
    if not passage_anchor_ids:
        passage_anchor_ids = state.context_node_ids[:8]
    state.metadata["passage_anchor_ids"] = passage_anchor_ids
    trace_payload["passage_anchor_ids"] = passage_anchor_ids
    if passage_anchor_ids:
        _record_reading_decision(
            state,
            stage_id="discover_corpus",
            decision_type="passage_anchor_selection",
            title="Choose passage anchors",
            rationale="Prefer primary non-passage nodes to fetch linked textual evidence.",
            selected_ids=passage_anchor_ids[:12],
        )

    try:
        linked_passages = await _fetch_passages_for_nodes(
            ctx.deps,
            passage_anchor_ids,
            limit=max(10, min(60, state.retrieval_budget.passage_bundle_limit() // 3)),
        )
    except Exception:
        linked_passages = []

    _record_tool_call(
        state,
        tool_name="read_linked_passages",
        stage_id="discover_corpus",
        rationale="fetch passages linked to the strongest anchor nodes",
        selected_ids=[
            str(row.get("passage_id"))
            for row in linked_passages[:16]
            if row.get("passage_id")
        ],
        details={
            "anchor_ids": passage_anchor_ids[:12],
            "linked_count": len(linked_passages),
        },
    )

    for row in linked_passages:
        pid = str(row["passage_id"])
        if pid in existing:
            continue
        evidence = Evidence(
            id=pid,
            label=f"{row['author']}, {row['title']} {row['canonical_ref'] or ''}".strip(),
            type="passage",
            layer=EvidenceLayer.PRIMARY,
            source=EvidenceSource.PASSAGE_CITATION,
            description=truncate_text(row.get("text_content", ""), 700),
            passage_id=pid,
            canonical_ref=row.get("canonical_ref"),
            author=row.get("author"),
            work_id=row.get("work_id"),
            work_title=row.get("title"),
            text_content=row.get("text_content"),
            confidence=row.get("confidence"),
            language=row.get("language"),
            evidence_tier=row.get("evidence_tier", "citable"),
            evidence_notice=row.get("evidence_notice", ""),
        )
        target = (
            state.primary_evidence
            if evidence.evidence_tier == "citable"
            else state.secondary_evidence
        )
        target.append(evidence)
        existing.add(pid)

    state.passages_used = len(
        [ev for ev in state.primary_evidence if ev.type == "passage"]
    )
    state.accumulated_context = _build_context_from_evidence(state.all_evidence())
    trace_payload["linked_passages"] = [
        {
            "passage_id": str(row["passage_id"]),
            "title": row.get("title"),
            "author": row.get("author"),
            "canonical_ref": row.get("canonical_ref"),
            "language": row.get("language"),
            "confidence": row.get("confidence"),
        }
        for row in linked_passages[:12]
    ]
    _trace_stage(state, "discover_corpus", trace_payload)


def _record_tool_call(
    state: RAGState,
    *,
    tool_name: str,
    stage_id: str,
    status: str = "complete",
    query: str | None = None,
    rationale: str | None = None,
    work_id: str | None = None,
    work_title: str | None = None,
    section_path: str | None = None,
    selected_ids: list[str] | None = None,
    details: dict[str, Any] | None = None,
) -> None:
    notebook = _ensure_notebook(state)
    resolved_ids = list(selected_ids or [])
    notebook.tool_calls.append(
        ResearchToolCall(
            tool_call_id=f"{stage_id}:{tool_name}:{len(notebook.tool_calls) + 1}",
            tool_name=tool_name,
            stage_id=stage_id,
            status=status,
            query=query,
            rationale=rationale,
            work_id=work_id,
            work_title=work_title,
            section_path=section_path,
            selected_ids=resolved_ids,
            detail_count=len(resolved_ids),
            details=details or {},
        )
    )


def _record_reading_decision(
    state: RAGState,
    *,
    stage_id: str,
    decision_type: str,
    title: str,
    rationale: str = "",
    facet_id: str | None = None,
    selected_ids: list[str] | None = None,
    rejected_ids: list[str] | None = None,
    supporting_refs: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    notebook = _ensure_notebook(state)
    notebook.reading_decisions.append(
        ReadingDecision(
            decision_id=f"{stage_id}:{decision_type}:{len(notebook.reading_decisions) + 1}",
            stage_id=stage_id,
            decision_type=decision_type,
            title=title,
            rationale=rationale,
            facet_id=facet_id,
            selected_ids=list(selected_ids or []),
            rejected_ids=list(rejected_ids or []),
            supporting_refs=list(supporting_refs or []),
            metadata=metadata or {},
        )
    )


def _selected_section_summary(
    node: Any, work_id: str, parent_path: str = ""
) -> list[dict[str, Any]]:
    """Flatten a tree node recursively into section summary dicts."""
    current_path = f"{parent_path} > {node.title}" if parent_path else node.title
    result = [
        {
            "work_id": work_id,
            "node_id": node.node_id,
            "title": node.title,
            "path": getattr(node, "path", None) or current_path,
            "summary": node.summary,
            "abstract": getattr(node, "abstract", None) or node.summary,
            "canonical_refs": getattr(node, "canonical_refs", []) or [],
            "translation_available": getattr(node, "translation_available", False),
            "quote_density": getattr(node, "quote_density", 0.0),
            "token_estimate": getattr(node, "token_estimate", 0),
            "start_passage": node.start_passage,
            "end_passage": node.end_passage,
        }
    ]
    for child in node.nodes:
        result.extend(_selected_section_summary(child, work_id, current_path))
    return result


def _heuristic_select_sections(
    question: str, sections: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    query_terms = {
        token
        for token in re.findall(
            r"[A-Za-zÀ-ÖØ-öø-ÿ\u0370-\u03FF\u1F00-\u1FFF]+", question.lower()
        )
        if len(token) > 3
    }
    scored: list[tuple[int, dict[str, Any]]] = []
    for section in sections:
        haystack = " ".join(
            str(section.get(key, "")).lower()
            for key in ("title", "summary", "abstract", "path")
        )
        score = sum(1 for term in query_terms if term in haystack)
        if score or not query_terms:
            scored.append((score, section))
    if not scored:
        return sections[: min(6, len(sections))]
    scored.sort(key=lambda item: item[0], reverse=True)
    return [section for _, section in scored[: min(8, len(scored))]]


async def _navigate_sections_with_llm(
    ctx: GraphRunContext[RAGState, Deps],
    *,
    question: str,
    work_title: str,
    author: str,
    work_id: str,
    sections: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    payload = [
        {
            "work_id": work_id,
            "node_id": section["node_id"],
            "title": section["title"],
            "path": section["path"],
            "summary": section["summary"],
            "abstract": section.get("abstract", ""),
            "canonical_refs": section.get("canonical_refs", []),
        }
        for section in sections
    ]
    prompt = TREE_NAVIGATION_PROMPT.format(
        question=question,
        work_title=work_title,
        author=author,
        sections_json=truncate_json(payload, 12000),
    )
    state = ctx.state
    model_api_id = _resolve_model_api_id(state)
    try:
        _t0 = _time.time()
        raw = await ctx.deps.llm.generate(
            prompt,
            system_prompt=SYSTEM_PROMPT,
            temperature=0.0,
            max_tokens=1200,
            thinking_mode=True,
            cache_key=f"tree-nav::{work_id}",
            cache_prefix="tree_navigation_v1",
            model_override=model_api_id,
            tier="utility",
        )
        _dur = int((_time.time() - _t0) * 1000)
        parsed = TreeNavigationResult.model_validate(_parse_json(raw))
        selected_ids = {item.node_id for item in parsed.selected_nodes}
        selected = [
            section for section in sections if section["node_id"] in selected_ids
        ]
        _append_reasoning_step(
            state,
            "TreeNavigateWorks",
            ctx.deps.llm.last_model_used or state.selected_model,
            prompt[:200],
            len(prompt) // 4,
            raw,
            duration_ms=_dur,
            parsed_result={"work_id": work_id, "selected_count": len(selected)},
        )
        return selected or _heuristic_select_sections(question, sections)
    except Exception:
        _append_reasoning_step(
            state,
            "TreeNavigateWorks",
            None,
            prompt[:200],
            len(prompt) // 4,
            "",
            skipped=True,
            skip_reason=f"LLM call failed for work {work_id}, heuristic fallback",
        )
        return _heuristic_select_sections(question, sections)


async def _build_research_frame(ctx: GraphRunContext[RAGState, Deps]) -> None:
    state = ctx.state
    model_api_id = _resolve_model_api_id(state)
    notebook = _ensure_notebook(state)
    if notebook.question_frame:
        notebook.facets = _normalize_notebook_facets(state, notebook.facets)
        return

    corpus_scope = "\n".join(
        sorted({ev.label for ev in state.all_evidence() if ev.label})[:20]
    )
    if _should_minimize_llm_calls(state):
        notebook.question_frame = state.question
        notebook.facets = _default_research_facets(state)
        if not state.sub_queries:
            state.sub_queries = [state.question]
        if not notebook.competing_hypotheses:
            notebook.competing_hypotheses = [
                f"The main answer is textually well supported for: {state.question}",
                f"The evidence is more fragmented or interpretive for: {state.question}",
            ]
        notebook.open_questions = state.sub_queries[:3]
        _append_reasoning_step(
            state,
            "BuildResearchNotebook",
            None,
            "",
            0,
            "",
            skipped=True,
            skip_reason="minimal-llm mode",
        )
    else:
        _frame_prompt = FRAME_RESEARCH_PROMPT.format(
            question=state.question,
            corpus_scope=corpus_scope or "(none)",
        )
        try:
            _t0 = _time.time()
            raw = await ctx.deps.llm.generate(
                _frame_prompt,
                system_prompt=SYSTEM_PROMPT,
                temperature=0.0,
                max_tokens=800,
                thinking_mode=True,
                cache_key="research-frame",
                cache_prefix="research_frame_v1",
                model_override=model_api_id,
                tier="utility",
            )
            _dur = int((_time.time() - _t0) * 1000)
            framed = ResearchFrame.model_validate(_parse_json(raw))
            notebook.question_frame = framed.question_frame
            notebook.facets = _normalize_notebook_facets(state, framed.facets)
            notebook.open_questions = framed.open_questions[:5]
            notebook.competing_hypotheses = framed.competing_hypotheses[:4]
            if framed.sub_questions:
                state.sub_queries = framed.sub_questions[:4]
            _append_reasoning_step(
                state,
                "BuildResearchNotebook",
                ctx.deps.llm.last_model_used or state.selected_model,
                _frame_prompt[:200],
                len(_frame_prompt) // 4,
                raw,
                duration_ms=_dur,
                parsed_result={
                    "question_frame": framed.question_frame,
                    "facet_count": len(framed.facets),
                },
            )
        except Exception:
            notebook.question_frame = state.question
            notebook.facets = _default_research_facets(state)
            if not state.sub_queries:
                state.sub_queries = [state.question]
            if not notebook.competing_hypotheses:
                notebook.competing_hypotheses = [
                    f"The main answer is textually well supported for: {state.question}",
                    f"The evidence is more fragmented or interpretive for: {state.question}",
                ]
            notebook.open_questions = state.sub_queries[:3]
            _append_reasoning_step(
                state,
                "BuildResearchNotebook",
                None,
                _frame_prompt[:200],
                len(_frame_prompt) // 4,
                "",
                skipped=True,
                skip_reason="LLM call failed, heuristic fallback",
            )

    if not notebook.facets:
        notebook.facets = _default_research_facets(state)
    notebook.corpus_scope = sorted(
        {ev.label for ev in state.all_evidence() if ev.label}
    )[:40]
    notebook.work_priorities = _candidate_work_titles(state)[
        : state.retrieval_budget.candidate_work_limit()
    ]
    _record_reading_decision(
        state,
        stage_id="research_notebook",
        decision_type="facet_plan",
        title="Plan scholarly reading facets",
        rationale="The notebook frames the question into research facets before hierarchical reading.",
        selected_ids=[facet.facet_id for facet in notebook.facets[:8]],
        metadata={
            "question_frame": notebook.question_frame,
            "work_priorities": notebook.work_priorities[:12],
        },
    )
    _build_scholarly_dossier(state)
    _trace_stage(
        state,
        "research_notebook",
        {
            "question_frame": notebook.question_frame,
            "facets": [
                {
                    "facet_id": facet.facet_id,
                    "title": facet.title,
                    "priority": facet.priority,
                    "required_support": facet.required_support,
                }
                for facet in notebook.facets
            ],
            "sub_queries": state.sub_queries[:8],
            "competing_hypotheses": notebook.competing_hypotheses[:6],
            "work_priorities": notebook.work_priorities[:12],
        },
    )


async def _plan_reading(ctx: GraphRunContext[RAGState, Deps]) -> None:
    state = ctx.state
    model_api_id = _resolve_model_api_id(state)
    notebook = _ensure_notebook(state)
    candidate_titles = notebook.work_priorities[
        : state.retrieval_budget.candidate_work_limit()
    ]
    planned_work_titles = candidate_titles
    planned_facet_ids = [facet.facet_id for facet in notebook.facets[:4]]
    rationale = "heuristic reading plan"
    mode = "heuristic"

    if candidate_titles and not _should_minimize_llm_calls(state):
        _plan_prompt = READING_PLAN_PROMPT.format(
            question_frame=notebook.question_frame or state.question,
            work_titles="\n".join(f"- {title}" for title in candidate_titles[:12]),
            facets_json=truncate_json(
                [
                    {
                        "facet_id": facet.facet_id,
                        "title": facet.title,
                        "question": facet.question,
                        "priority": facet.priority,
                    }
                    for facet in notebook.facets[:8]
                ],
                6000,
            ),
        )
        try:
            _t0 = _time.time()
            raw = await ctx.deps.llm.generate(
                _plan_prompt,
                system_prompt=SYSTEM_PROMPT,
                temperature=0.0,
                max_tokens=700,
                thinking_mode=True,
                cache_key="reading-plan",
                cache_prefix="reading_plan_v1",
                model_override=model_api_id,
                tier="utility",
            )
            _dur = int((_time.time() - _t0) * 1000)
            parsed = ReadingPlanResult.model_validate(_parse_json(raw))
            normalized_titles = [
                title for title in parsed.work_titles if title in candidate_titles
            ]
            if normalized_titles:
                planned_work_titles = normalized_titles + [
                    title
                    for title in candidate_titles
                    if title not in normalized_titles
                ]
            normalized_facets = [
                facet_id
                for facet_id in parsed.facet_ids
                if any(facet.facet_id == facet_id for facet in notebook.facets)
            ]
            if normalized_facets:
                planned_facet_ids = normalized_facets
            rationale = parsed.rationale or rationale
            mode = "llm"
            _append_reasoning_step(
                state,
                "PlanReading",
                ctx.deps.llm.last_model_used or state.selected_model,
                _plan_prompt[:200],
                len(_plan_prompt) // 4,
                raw,
                duration_ms=_dur,
                parsed_result={
                    "work_count": len(normalized_titles),
                    "facet_count": len(normalized_facets),
                },
            )
        except Exception:
            mode = "heuristic"
            _append_reasoning_step(
                state,
                "PlanReading",
                None,
                "",
                0,
                "",
                skipped=True,
                skip_reason="LLM call failed, heuristic fallback",
            )
    else:
        _append_reasoning_step(
            state,
            "PlanReading",
            None,
            "",
            0,
            "",
            skipped=True,
            skip_reason="no candidates or minimal-llm mode",
        )

    planned_work_titles = planned_work_titles[
        : state.retrieval_budget.candidate_work_limit()
    ]
    planned_facet_ids = planned_facet_ids[: min(6, len(planned_facet_ids))]
    state.metadata["planned_work_titles"] = planned_work_titles
    state.metadata["planned_facet_ids"] = planned_facet_ids
    notebook.work_priorities = planned_work_titles
    if planned_facet_ids:
        facet_by_id = {facet.facet_id: facet for facet in notebook.facets}
        notebook.facets = [
            facet_by_id[facet_id]
            for facet_id in planned_facet_ids
            if facet_id in facet_by_id
        ] + [
            facet
            for facet in notebook.facets
            if facet.facet_id not in set(planned_facet_ids)
        ]
    _record_tool_call(
        state,
        tool_name="plan_reading",
        stage_id="reading_plan",
        status=mode,
        query=notebook.question_frame or state.question,
        rationale=rationale,
        selected_ids=planned_work_titles[:12],
        details={"planned_facet_ids": planned_facet_ids[:8]},
    )
    _record_reading_decision(
        state,
        stage_id="reading_plan",
        decision_type="reading_order",
        title="Prioritize works and facets before hierarchical reading",
        rationale=rationale,
        selected_ids=planned_work_titles[:12],
        metadata={"planned_facet_ids": planned_facet_ids[:8]},
    )
    _trace_stage(
        state,
        "reading_plan",
        {
            "mode": mode,
            "planned_work_titles": planned_work_titles[:12],
            "planned_facet_ids": planned_facet_ids[:8],
            "rationale": rationale,
        },
    )


@dataclass
class ClassifyComplexity(BaseNode[RAGState, Deps, ScholarlyAnswer]):
    """Legacy compatibility node delegating to query-type classification."""

    async def run(
        self,
        ctx: GraphRunContext[RAGState, Deps],
    ) -> ExpandQuery:
        return await ClassifyQueryType().run(ctx)


@dataclass
class ExpandQuery(BaseNode[RAGState, Deps, ScholarlyAnswer]):
    """Expand the query and seed philological metadata."""

    async def run(
        self,
        ctx: GraphRunContext[RAGState, Deps],
    ) -> DiscoverCorpus:
        state = ctx.state
        model_api_id = _resolve_model_api_id(state)
        fallback_expansion = _default_expansion(state.question)
        if not state.pipeline_config.use_expansion or _should_minimize_llm_calls(state):
            state.expanded_query = state.question
            state.expansion_terms = fallback_expansion
            state.metadata["expanded_query"] = state.expanded_query
            _append_reasoning_step(
                state,
                "ExpandQuery",
                None,
                "",
                0,
                "",
                skipped=True,
                skip_reason="expansion disabled or minimal-llm mode",
            )
            _trace_stage(
                state,
                "expand_query",
                {
                    "mode": "heuristic",
                    "expanded_query": state.expanded_query,
                    "philosophers": fallback_expansion.philosophers[:8],
                    "concepts": fallback_expansion.concepts[:8],
                    "schools": fallback_expansion.schools[:8],
                    "periods": fallback_expansion.periods[:6],
                },
            )
            return DiscoverCorpus()

        _expand_prompt = EXPAND_QUERY_PROMPT.format(question=state.question)
        mode = "llm"
        try:
            _t0 = _time.time()
            raw = await ctx.deps.llm.generate(
                _expand_prompt,
                system_prompt=SYSTEM_PROMPT,
                temperature=0.0,
                max_tokens=800,
                cache_key="query-expansion",
                cache_prefix="query_expansion_v1",
                model_override=model_api_id,
                tier="utility",
            )
            _dur = int((_time.time() - _t0) * 1000)
            expansion = _merge_expansion_terms(
                ExpansionTerms.model_validate(_parse_json(raw)),
                fallback_expansion,
            )
            _append_reasoning_step(
                state,
                "ExpandQuery",
                ctx.deps.llm.last_model_used or state.selected_model,
                _expand_prompt[:200],
                len(_expand_prompt) // 4,
                raw,
                duration_ms=_dur,
                parsed_result={"expanded_query": expansion.expanded_query or ""},
            )
        except Exception:
            expansion = fallback_expansion
            mode = "fallback"
            _append_reasoning_step(
                state,
                "ExpandQuery",
                None,
                _expand_prompt[:200],
                len(_expand_prompt) // 4,
                "",
                skipped=True,
                skip_reason="LLM call failed, fallback expansion",
            )

        state.expansion_terms = expansion
        state.expanded_query = expansion.expanded_query or state.question
        state.metadata["expanded_query"] = state.expanded_query
        _trace_stage(
            state,
            "expand_query",
            {
                "mode": mode,
                "expanded_query": state.expanded_query,
                "philosophers": expansion.philosophers[:8],
                "concepts": expansion.concepts[:8],
                "schools": expansion.schools[:8],
                "periods": expansion.periods[:6],
            },
        )
        return DiscoverCorpus()


@dataclass
class DiscoverCorpus(BaseNode[RAGState, Deps, ScholarlyAnswer]):
    """Broad discovery over KG nodes and linked passages."""

    async def run(
        self,
        ctx: GraphRunContext[RAGState, Deps],
    ) -> BuildResearchNotebook:
        _t0 = _time.time()
        await _discover_corpus(ctx)
        _dur = int((_time.time() - _t0) * 1000)
        _append_reasoning_step(
            ctx.state,
            "DiscoverCorpus",
            None,
            "",
            0,
            "",
            skipped=True,
            skip_reason="no LLM call (strategy-based retrieval)",
            duration_ms=_dur,
        )
        return BuildResearchNotebook()


@dataclass
class BuildResearchNotebook(BaseNode[RAGState, Deps, ScholarlyAnswer]):
    """Create the explicit notebook used by later reasoning stages."""

    async def run(
        self,
        ctx: GraphRunContext[RAGState, Deps],
    ) -> PlanReading:
        await _build_research_frame(ctx)
        return PlanReading()


@dataclass
class PlanReading(BaseNode[RAGState, Deps, ScholarlyAnswer]):
    """Plan work/facet reading order before tree navigation."""

    async def run(
        self,
        ctx: GraphRunContext[RAGState, Deps],
    ) -> TreeNavigateWorks:
        await _plan_reading(ctx)
        return TreeNavigateWorks()


@dataclass
class TreeNavigateWorks(BaseNode[RAGState, Deps, ScholarlyAnswer]):
    """Navigate work trees recursively before loading many passages."""

    async def run(
        self,
        ctx: GraphRunContext[RAGState, Deps],
    ) -> ExpandEvidenceBundles:
        state = ctx.state
        state.metadata["selected_sections"] = []

        if not ctx.deps.tree_index or not state.pipeline_config.use_tree_reasoning:
            _skip_reason = (
                "tree reasoning unavailable"
                if not ctx.deps.tree_index
                else "tree reasoning disabled by config"
            )
            _append_reasoning_step(
                state,
                "TreeNavigateWorks",
                None,
                "",
                0,
                "",
                skipped=True,
                skip_reason=_skip_reason,
            )
            _trace_stage(
                state,
                "tree_navigation",
                {
                    "mode": "skipped",
                    "reason": _skip_reason,
                    "candidate_work_titles": state.research_notebook.work_priorities[
                        : state.retrieval_budget.candidate_work_limit()
                    ],
                    "selected_sections": [],
                },
            )
            return ExpandEvidenceBundles()

        work_titles = _candidate_work_titles(state)
        if not work_titles:
            return ExpandEvidenceBundles()
        _record_tool_call(
            state,
            tool_name="search_works",
            stage_id="tree_navigation",
            query=state.research_notebook.question_frame or state.question,
            rationale="prioritize works before opening hierarchical indices",
            selected_ids=work_titles[: state.retrieval_budget.candidate_work_limit()],
            details={"candidate_count": len(work_titles)},
        )

        try:
            work_ids = await ctx.deps.tree_index.resolve_work_ids(
                work_titles[: state.retrieval_budget.candidate_work_limit()]
            )
            indices = await ctx.deps.tree_index.load_indices(
                work_ids[: state.retrieval_budget.candidate_work_limit()]
            )
        except Exception:
            logger.warning("Tree navigation unavailable")
            return ExpandEvidenceBundles()

        selected_sections: list[dict[str, Any]] = []
        minimize_llm = _should_minimize_llm_calls(state)
        question = state.research_notebook.question_frame or state.question

        # Pre-process each index: record tool call, build sections, collect LLM tasks
        per_index_data: list[
            tuple[Any, list[dict[str, Any]], list[dict[str, Any]]]
        ] = []
        for index in indices:
            _record_tool_call(
                state,
                tool_name="open_work_tree",
                stage_id="tree_navigation",
                rationale="inspect the hierarchical section index before reading passages",
                work_id=index.work_id,
                work_title=index.title,
                selected_ids=[node.node_id for node in index.nodes[:12]],
                details={
                    "root_node_count": len(index.nodes),
                    "author": index.author,
                },
            )
            flat_sections: list[dict[str, Any]] = []
            for node in index.nodes:
                flat_sections.extend(_selected_section_summary(node, index.work_id))
            top_sections = flat_sections[
                : state.retrieval_budget.section_summary_limit()
            ]
            per_index_data.append((index, flat_sections, top_sections))

        # Launch LLM navigation calls in parallel (skip indices with no sections)
        _nav_semaphore = asyncio.Semaphore(10)

        async def _limited_nav(idx: int, coro: Any) -> tuple[int, list[dict[str, Any]]]:
            async with _nav_semaphore:
                return idx, await coro

        nav_coros: list[Any] = []
        nav_index_map: dict[
            int, int
        ] = {}  # maps coro position -> per_index_data position
        for i, (index, flat_sections, top_sections) in enumerate(per_index_data):
            if not flat_sections:
                continue
            if minimize_llm:
                continue  # handled synchronously below
            coro_pos = len(nav_coros)
            nav_index_map[coro_pos] = i
            nav_coros.append(
                _limited_nav(
                    i,
                    _navigate_sections_with_llm(
                        ctx,
                        question=question,
                        work_title=index.title,
                        author=index.author,
                        work_id=index.work_id,
                        sections=top_sections,
                    ),
                )
            )

        # Gather parallel LLM results
        llm_results: dict[int, list[dict[str, Any]]] = {}
        if nav_coros:
            raw_results = await asyncio.gather(*nav_coros, return_exceptions=True)
            for result in raw_results:
                if isinstance(result, Exception):
                    logger.warning("Tree navigation failed for a work: %s", result)
                    continue
                idx, chosen = result
                llm_results[idx] = chosen

        # Post-process all indices
        for i, (index, flat_sections, top_sections) in enumerate(per_index_data):
            if not flat_sections:
                continue

            if minimize_llm:
                chosen = _heuristic_select_sections(question, top_sections)
                section_mode = "heuristic"
            elif i in llm_results:
                chosen = llm_results[i]
                section_mode = "llm"
            else:
                # LLM call failed for this index, fall back to heuristic
                chosen = _heuristic_select_sections(question, top_sections)
                section_mode = "heuristic"

            selected_sections.extend(chosen)
            _record_tool_call(
                state,
                tool_name="select_work_sections",
                stage_id="tree_navigation",
                status=section_mode,
                rationale="choose the most promising sections before expanding into passages",
                work_id=index.work_id,
                work_title=index.title,
                selected_ids=[section["node_id"] for section in chosen[:12]],
                details={
                    "candidate_sections": len(top_sections),
                    "selected_count": len(chosen),
                },
            )
            if chosen:
                _record_reading_decision(
                    state,
                    stage_id="tree_navigation",
                    decision_type="section_selection",
                    title=f"Select sections in {index.title}",
                    rationale="Prioritize sections whose summaries best cover the framed research facets.",
                    selected_ids=[section["node_id"] for section in chosen[:12]],
                    rejected_ids=[
                        section["node_id"]
                        for section in top_sections
                        if section["node_id"]
                        not in {item["node_id"] for item in chosen}
                    ][:12],
                    metadata={
                        "work_id": index.work_id,
                        "work_title": index.title,
                        "paths": [section.get("path") for section in chosen[:8]],
                    },
                )

        state.metadata["selected_sections"] = selected_sections
        state.research_notebook.work_priorities = work_titles[
            : state.retrieval_budget.candidate_work_limit()
        ]
        _trace_stage(
            state,
            "tree_navigation",
            {
                "candidate_work_titles": work_titles[
                    : state.retrieval_budget.candidate_work_limit()
                ],
                "selected_sections": [
                    {
                        "work_id": section["work_id"],
                        "node_id": section["node_id"],
                        "path": section.get("path"),
                        "title": section.get("title"),
                    }
                    for section in selected_sections[:20]
                ],
            },
        )
        return ExpandEvidenceBundles()


@dataclass
class ExpandEvidenceBundles(BaseNode[RAGState, Deps, ScholarlyAnswer]):
    """Load passages for selected sections and pair translations when possible."""

    async def run(
        self,
        ctx: GraphRunContext[RAGState, Deps],
    ) -> SeekCounterEvidence:
        _t0 = _time.time()
        state = ctx.state
        bundles: list[EvidenceBundle] = []
        seen_bundle_ids = state.bundle_ids()
        selected_sections = state.metadata.get("selected_sections", [])
        translation_pairs: list[dict[str, Any]] = []

        if ctx.deps.tree_index and selected_sections:
            work_ids = {section["work_id"] for section in selected_sections}
            indices = await ctx.deps.tree_index.load_indices(list(work_ids))
            indices_by_id = {index.work_id: index for index in indices}

            # --- Phase 1: batch extract passages (one DB call per section) ---
            per_limit = max(
                4,
                min(
                    40,
                    state.retrieval_budget.passage_bundle_limit()
                    // max(1, len(selected_sections)),
                ),
            )
            section_rows: list[tuple[dict[str, Any], list[dict[str, Any]]]] = []
            for section in selected_sections:
                index = indices_by_id.get(section["work_id"])
                if not index:
                    continue
                try:
                    rows = await ctx.deps.tree_index.extract_passages(
                        index,
                        [section["node_id"]],
                        limit=per_limit,
                    )
                except Exception:
                    continue
                _record_tool_call(
                    state,
                    tool_name="read_section",
                    stage_id="evidence_bundles",
                    rationale="expand the selected section into concrete passage bundles",
                    work_id=index.work_id,
                    work_title=index.title,
                    section_path=section.get("path"),
                    selected_ids=[
                        str(row.get("passage_id"))
                        for row in rows[:16]
                        if row.get("passage_id")
                    ],
                    details={
                        "node_id": section["node_id"],
                        "selected_count": len(rows),
                    },
                )
                section_rows.append((section, rows))

            # --- Phase 2: collect all unique passage IDs, batch-fetch translations ---
            all_passage_ids: list[str] = []
            for _section, rows in section_rows:
                for row in rows:
                    bundle_id = f"{row['work_id']}::{row['passage_id']}"
                    if bundle_id not in seen_bundle_ids:
                        all_passage_ids.append(str(row["passage_id"]))

            translations_map = (
                await _batch_fetch_translations(ctx.deps, all_passage_ids)
                if all_passage_ids
                else {}
            )

            # --- Phase 3: build bundles using pre-fetched translations ---
            for _section, rows in section_rows:
                for row in rows:
                    bundle_id = f"{row['work_id']}::{row['passage_id']}"
                    if bundle_id in seen_bundle_ids:
                        continue
                    pid = str(row["passage_id"])
                    translation = translations_map.get(pid)
                    if translation:
                        translation_pairs.append(
                            {
                                "original_passage_id": pid,
                                "translation_passage_id": str(
                                    translation.get("passage_id")
                                )
                                if translation.get("passage_id")
                                else None,
                                "translation_node_id": translation.get("kg_node_id"),
                                "section_path": section.get("path"),
                            }
                        )
                    original_text = row.get("text_content") or ""
                    translation_text = (
                        translation.get("text_content") if translation else None
                    )
                    bundle = EvidenceBundle(
                        bundle_id=bundle_id,
                        work_id=str(row["work_id"]),
                        work_title=row.get("title", ""),
                        author=row.get("author"),
                        section_path=section.get("path", ""),
                        canonical_ref=row.get("canonical_ref"),
                        original_passage_id=pid,
                        translation_passage_id=(
                            str(translation["passage_id"])
                            if translation and translation.get("passage_id")
                            else None
                        ),
                        original_text=original_text,
                        translation_text=translation_text,
                        language=row.get("language"),
                        token_estimate=RetrievalBudget.estimate_tokens(
                            "\n".join(
                                part
                                for part in (original_text, translation_text)
                                if part
                            )
                        ),
                        evidence_role="primary_support",
                        source=EvidenceSource.TREE_REASONING,
                        metadata={
                            "sequence_number": row.get("sequence_number"),
                            "translation_available": bool(translation_text),
                            "translation_source": translation.get("source")
                            if translation
                            else None,
                            "translation_node_id": translation.get("kg_node_id")
                            if translation
                            else None,
                        },
                    )
                    bundles.append(bundle)
                    seen_bundle_ids.add(bundle_id)

        if translation_pairs:
            _record_tool_call(
                state,
                tool_name="fetch_translation_pair",
                stage_id="evidence_bundles",
                rationale="pair original-language passages with their linked translations",
                selected_ids=[
                    item["translation_passage_id"] or item["translation_node_id"]
                    for item in translation_pairs[:20]
                    if item["translation_passage_id"] or item["translation_node_id"]
                ],
                details={
                    "pair_count": len(translation_pairs),
                    "pairs": translation_pairs[:12],
                },
            )

        supplemental = await _supplemental_passage_bundles(
            ctx, bundles, seen_bundle_ids
        )
        if supplemental:
            _record_tool_call(
                state,
                tool_name="read_passage_bundle",
                stage_id="evidence_bundles",
                rationale="supplement tree-selected evidence with directly linked high-value passages",
                selected_ids=[bundle.bundle_id for bundle in supplemental[:16]],
                details={"supplemental_count": len(supplemental)},
            )
        bundles.extend(supplemental)

        state.evidence_bundles.extend(bundles)
        for bundle in state.evidence_bundles:
            bundle.metadata.update(
                {
                    key: value
                    for key, value in _bundle_academic_features(bundle, state).items()
                    if value not in (None, False, "", [])
                }
            )
        state.passages_used = len(state.evidence_bundles)
        notebook = _ensure_notebook(state)
        for bundle in bundles:
            notebook.reading_notes.append(
                ReadingNote(
                    note_id=bundle.bundle_id,
                    thesis=f"{bundle.work_title} contributes direct textual evidence.",
                    work_id=bundle.work_id,
                    section_path=bundle.section_path,
                    evidence_ids=[bundle.bundle_id],
                )
            )
        _build_scholarly_dossier(state)
        state.context_pack = _build_context_pack(state)
        state.accumulated_context = state.context_pack.prompt_context
        if bundles:
            _record_reading_decision(
                state,
                stage_id="evidence_bundles",
                decision_type="bundle_acceptance",
                title="Accept evidence bundles into the dossier",
                rationale="Bundles are retained when they add direct text, testimony, or counter-evidence for the active facets.",
                selected_ids=[bundle.bundle_id for bundle in bundles[:20]],
                supporting_refs=[
                    state.context_pack.bundle_refs.get(
                        bundle.bundle_id, bundle.bundle_id
                    )
                    for bundle in bundles[:12]
                    if state.context_pack.bundle_refs.get(bundle.bundle_id)
                ],
                metadata={
                    "bundle_count": len(bundles),
                    "work_titles": list(
                        dict.fromkeys(bundle.work_title for bundle in bundles[:12])
                    ),
                },
            )
        _trace_stage(
            state,
            "evidence_bundles",
            {
                "bundle_count": len(state.evidence_bundles),
                "bundle_sample": [
                    {
                        "bundle_id": bundle.bundle_id,
                        "work_title": bundle.work_title,
                        "author": bundle.author,
                        "source": bundle.source.value,
                        "canonical_ref": bundle.canonical_ref,
                        "translation_source": bundle.metadata.get("translation_source"),
                    }
                    for bundle in state.evidence_bundles[:20]
                ],
            },
        )
        _append_reasoning_step(
            state,
            "ExpandEvidenceBundles",
            None,
            "",
            0,
            "",
            skipped=True,
            skip_reason="no LLM call (passage expansion)",
            duration_ms=int((_time.time() - _t0) * 1000),
            parsed_result={"bundle_count": len(state.evidence_bundles)},
        )
        return SeekCounterEvidence()


@dataclass
class SeekCounterEvidence(BaseNode[RAGState, Deps, ScholarlyAnswer]):
    """Mark bundles that complicate the main hypotheses."""

    async def run(
        self,
        ctx: GraphRunContext[RAGState, Deps],
    ) -> EvidenceSufficiency:
        state = ctx.state
        model_api_id = _resolve_model_api_id(state)
        notebook = _ensure_notebook(state)
        if (
            _should_minimize_llm_calls(state)
            or not state.evidence_bundles
            or not notebook.competing_hypotheses
        ):
            _append_reasoning_step(
                state,
                "SeekCounterEvidence",
                None,
                "",
                0,
                "",
                skipped=True,
                skip_reason="minimal-llm mode or insufficient bundles",
            )
            _trace_stage(
                state,
                "counter_evidence",
                {
                    "mode": "skipped",
                    "selected_count": 0,
                    "rationale": "minimal-llm mode or insufficient bundles",
                    "bundle_ids": [],
                },
            )
            return EvidenceSufficiency()

        payload = [
            _bundle_prompt_dict(
                bundle,
                state.context_pack.bundle_refs.get(bundle.bundle_id, bundle.bundle_id),
            )
            for bundle in state.context_pack.passage_bundles[:20]
        ]
        _counter_prompt = COUNTER_EVIDENCE_PROMPT.format(
            question_frame=notebook.question_frame or state.question,
            hypotheses="\n".join(
                f"- {item}" for item in notebook.competing_hypotheses[:4]
            ),
            bundles_json=truncate_json(payload, 9000),
        )
        try:
            _t0 = _time.time()
            raw = await ctx.deps.llm.generate(
                _counter_prompt,
                system_prompt=SYSTEM_PROMPT,
                temperature=0.0,
                max_tokens=600,
                thinking_mode=True,
                cache_key="counter-evidence",
                cache_prefix="counter_evidence_v1",
                model_override=model_api_id,
                tier="utility",
            )
            _dur = int((_time.time() - _t0) * 1000)
            parsed = CounterEvidenceResult.model_validate(_parse_json(raw))
            selected = set(parsed.bundle_ids)
            rationale = parsed.rationale
            mode = "llm"
            _append_reasoning_step(
                state,
                "SeekCounterEvidence",
                ctx.deps.llm.last_model_used or state.selected_model,
                _counter_prompt[:200],
                len(_counter_prompt) // 4,
                raw,
                duration_ms=_dur,
                parsed_result={"selected_count": len(selected), "rationale": rationale},
            )
        except Exception:
            selected = {
                bundle.bundle_id
                for bundle in state.evidence_bundles[1:3]
                if bundle.author != state.evidence_bundles[0].author
            }
            rationale = "heuristic author divergence"
            mode = "heuristic"
            _append_reasoning_step(
                state,
                "SeekCounterEvidence",
                None,
                _counter_prompt[:200],
                len(_counter_prompt) // 4,
                "",
                skipped=True,
                skip_reason="LLM call failed, heuristic fallback",
            )

        if selected:
            for bundle in state.evidence_bundles:
                if bundle.bundle_id in selected:
                    bundle.evidence_role = "counter_evidence"
                    bundle.metadata["evidence_class"] = "counter_evidence"
            notebook.counter_evidence.append(rationale)
            _build_scholarly_dossier(state)
            state.context_pack = _build_context_pack(state)
            state.accumulated_context = state.context_pack.prompt_context
            _record_reading_decision(
                state,
                stage_id="counter_evidence",
                decision_type="counter_evidence_selection",
                title="Mark counter-evidence bundles",
                rationale=rationale,
                selected_ids=sorted(selected)[:12],
                supporting_refs=[
                    state.context_pack.bundle_refs.get(bundle_id, bundle_id)
                    for bundle_id in sorted(selected)[:12]
                    if state.context_pack.bundle_refs.get(bundle_id)
                ],
            )
        _trace_stage(
            state,
            "counter_evidence",
            {
                "mode": mode,
                "selected_count": len(selected),
                "bundle_ids": sorted(selected)[:8],
                "rationale": rationale,
            },
        )
        return EvidenceSufficiency()


@dataclass
class EvidenceSufficiency(BaseNode[RAGState, Deps, ScholarlyAnswer]):
    """Single sufficiency gate after bundle expansion."""

    async def run(
        self,
        ctx: GraphRunContext[RAGState, Deps],
    ) -> DraftClaimLedger | DiscoverCorpus:
        state = ctx.state
        notebook = _ensure_notebook(state)
        score, sufficient, reason, refinement = await assess_evidence_sufficiency(
            state, ctx.deps
        )

        if (
            not sufficient
            and state.iteration < 1
            and state.pipeline_config.use_tree_reasoning
            and refinement
        ):
            state.iteration += 1
            state.sub_queries = [refinement]
            notebook.uncertainties.append(reason)
            _record_reading_decision(
                state,
                stage_id="evidence_sufficiency",
                decision_type="refine_search",
                title="Refine the corpus search",
                rationale=reason,
                selected_ids=[refinement],
                metadata={"score": round(score, 4)},
            )
            return DiscoverCorpus()

        if not sufficient:
            notebook.uncertainties.append(reason)
        return DraftClaimLedger()


# ---------------------------------------------------------------------------
# Legacy compatibility wrappers
# ---------------------------------------------------------------------------


@dataclass
class DirectKGLookup(DiscoverCorpus):
    """Compatibility alias for the old direct-lookup node."""


@dataclass
class HybridRetrieve(DiscoverCorpus):
    """Compatibility alias for the old hybrid-retrieval node."""


@dataclass
class DecomposeQuery(BaseNode[RAGState, Deps, ScholarlyAnswer]):
    """Compatibility wrapper that seeds sub-queries before discovery."""

    async def run(
        self,
        ctx: GraphRunContext[RAGState, Deps],
    ) -> SearchPrimarySources:
        state = ctx.state
        if not state.sub_queries:
            state.sub_queries = [state.expanded_query or state.question]
        return SearchPrimarySources()


@dataclass
class SearchPrimarySources(DiscoverCorpus):
    """Compatibility alias for the old primary-source search node."""


@dataclass
class EvaluateSufficiency(BaseNode[RAGState, Deps, ScholarlyAnswer]):
    """Compatibility wrapper that routes into the new notebook/tree flow."""

    async def run(
        self,
        ctx: GraphRunContext[RAGState, Deps],
    ) -> TreeNavigateWorks:
        await _build_research_frame(ctx)
        return TreeNavigateWorks()


@dataclass
class SearchSecondarySources(SeekCounterEvidence):
    """Compatibility alias mapping to counter-evidence search."""


@dataclass
class TreeReasoningRetrieve(TreeNavigateWorks):
    """Compatibility alias for old tree-reasoning node."""


@dataclass
class CRAGValidate(EvidenceSufficiency):
    """Compatibility alias for the new single sufficiency gate."""


@dataclass
class DualRerank(ExpandEvidenceBundles):
    """Compatibility alias; bundle expansion subsumes reranking pressure."""


@dataclass
class FetchPassagesAndLayer(ExpandEvidenceBundles):
    """Compatibility alias for bundle expansion and context packing."""


@dataclass
class Synthesize(DraftClaimLedger):
    """Compatibility alias for claim-ledger drafting."""


@dataclass
class SynthesizeWithHierarchy(DraftClaimLedger):
    """Compatibility alias for hierarchical claim-ledger drafting."""


@dataclass
class VerifyCitations(ProgrammaticVerify):
    """Compatibility alias for programmatic verification."""


@dataclass
class SelfRAGEvaluate(BaseNode[RAGState, Deps, ScholarlyAnswer]):
    """Compatibility wrapper returning the final answer immediately."""

    async def run(
        self,
        ctx: GraphRunContext[RAGState, Deps],
    ) -> End[ScholarlyAnswer]:
        if not ctx.state.citations and ctx.state.raw_answer:
            answer, citations = _verify_answer_programmatically(ctx.state)
            ctx.state.raw_answer = answer
            ctx.state.citations = citations
        ctx.state.quality_badge = _quality_badge_from_state(ctx.state)
        return End(_make_answer(ctx.state))


@dataclass
class RefineSynthesis(BaseNode[RAGState, Deps, ScholarlyAnswer]):
    """Compatibility wrapper that re-renders from the ledger."""

    async def run(
        self,
        ctx: GraphRunContext[RAGState, Deps],
    ) -> VerifyCitations:
        ctx.state.self_rag_iterations += 1
        ctx.state.raw_answer = _render_answer_fallback(ctx.state)
        return VerifyCitations()
