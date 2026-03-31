"""
Scholarly Agent facade — orchestrates the GraphRAG pipeline.

Supports two modes via ELEUTHERIA_AGENT_MODE env var:
  - "fsm" (default): Original 12-node pydantic-graph pipeline
  - "react": New ReAct agent loop with tools (Phase 2)
"""

from __future__ import annotations

import json
import logging
import os
import re
from collections.abc import AsyncIterator
from typing import Any

from pydantic_graph import Graph

from eleutheria_graphrag.agents.dependencies import Deps
from eleutheria_graphrag.agents.graph_nodes import (
    BuildResearchNotebook,
    ClassifyQueryType,
    DiscoverCorpus,
    DraftClaimLedger,
    EvidenceSufficiency,
    ExpandEvidenceBundles,
    ExpandQuery,
    PlanReading,
    ProgrammaticVerify,
    RenderGroundedAnswer,
    SeekCounterEvidence,
    TreeNavigateWorks,
)
from eleutheria_graphrag.agents.state import RAGState, ScholarlyAnswer

_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.;·?!])\s+")
logger = logging.getLogger(__name__)

AGENT_MODE = os.getenv("ELEUTHERIA_AGENT_MODE", "react")

# FSM graph (kept for fsm mode and as fallback)
scholarly_graph = Graph(
    nodes=[
        ClassifyQueryType,
        ExpandQuery,
        DiscoverCorpus,
        BuildResearchNotebook,
        PlanReading,
        TreeNavigateWorks,
        ExpandEvidenceBundles,
        SeekCounterEvidence,
        EvidenceSufficiency,
        DraftClaimLedger,
        RenderGroundedAnswer,
        ProgrammaticVerify,
    ],
)


class ScholarlyAgent:
    """High-level facade over the GraphRAG pipeline.

    In 'fsm' mode, runs the full pydantic-graph FSM.
    In 'react' mode, runs: ClassifyQueryType → AgentLoop → Synthesis.
    """

    def __init__(self, deps: Deps) -> None:
        self.deps = deps

    async def query(
        self,
        question: str,
        *,
        max_iterations: int = 5,
        selected_model: str = "gemini-3.1-pro",
        retrieval_mode: str = "auto",
        agent_mode: str | None = None,
    ) -> ScholarlyAnswer:
        mode = agent_mode or AGENT_MODE

        state = RAGState(
            question=question,
            max_iterations=max_iterations,
            selected_model=selected_model,
            retrieval_mode=retrieval_mode,
        )

        if mode == "react":
            return await self._run_react(state)
        return await self._run_fsm(state)

    async def _run_fsm(self, state: RAGState) -> ScholarlyAnswer:
        """Run the original pydantic-graph FSM pipeline."""
        result = await scholarly_graph.run(
            ClassifyQueryType(),
            state=state,
            deps=self.deps,
        )
        return result.output

    async def _run_react(self, state: RAGState) -> ScholarlyAnswer:
        """Run the new ReAct agent pipeline.

        Phase 1: ClassifyQueryType (deterministic)
        Phase 2: AgentLoop (ReAct with tools)
        Phase 3: DraftClaimLedger → RenderGroundedAnswer → ProgrammaticVerify
        """
        from pydantic_graph import End, GraphRunContext

        from eleutheria_graphrag.agents.react_loop import AgentLoop
        from eleutheria_graphrag.agents.sse_emitter import NullEmitter
        from eleutheria_graphrag.agents.tools import build_tool_registry

        # Phase 1: Classify query type
        classify_node = ClassifyQueryType()
        ctx = GraphRunContext(state=state, deps=self.deps)
        await classify_node.run(ctx)
        logger.info(
            "Query classified: type=%s, complexity=%s",
            state.query_type,
            state.complexity,
        )

        # Phase 2: Agent loop
        tools = build_tool_registry(self.deps)
        emitter = NullEmitter()
        agent = AgentLoop(
            deps=self.deps,
            state=state,
            tools=tools,
            emitter=emitter,
        )
        await agent.run()
        logger.info(
            "Agent loop completed: %d calls, %d evidence, %d bundles",
            agent.calls_made,
            len(agent.evidence.primary_evidence)
            + len(agent.evidence.secondary_evidence),
            len(agent.evidence.evidence_bundles),
        )

        # Phase 3: Synthesis (reuse existing FSM nodes)
        # Run DraftClaimLedger → RenderGroundedAnswer → ProgrammaticVerify
        draft_node = DraftClaimLedger()
        ctx = GraphRunContext(state=state, deps=self.deps)
        await draft_node.run(ctx)

        render_node = RenderGroundedAnswer()
        ctx = GraphRunContext(state=state, deps=self.deps)
        await render_node.run(ctx)

        verify_node = ProgrammaticVerify()
        ctx = GraphRunContext(state=state, deps=self.deps)
        result = await verify_node.run(ctx)

        # ProgrammaticVerify returns End(output=ScholarlyAnswer)
        if isinstance(result, End):
            answer = result.data
        else:
            from eleutheria_graphrag.agents.graph_nodes import _make_answer

            answer = _make_answer(state)

        # Phase 3.5: Programmatic passage injection
        # If the LLM failed to include quotation blocks, inject them deterministically
        answer = self._inject_passage_quotations(answer, state)

        # Phase 4: Text verification DISABLED — too many false positives
        # removing legitimate Greek text retrieved from evidence bundles.
        # TODO: rework to whitelist evidence bundle text before DB search.
        return answer

    @staticmethod
    def _inject_passage_quotations(
        answer: ScholarlyAnswer, state: Any
    ) -> ScholarlyAnswer:
        """Programmatic injection of passage quotations when the LLM omits them.

        If the rendered answer has fewer than 2 blockquote sections with Greek/Latin
        text, we append a "Primary Textual Evidence" section with the best evidence
        bundles — original text + translation, properly attributed.

        This is 100% deterministic — no LLM calls.
        """
        import re as _re

        text = answer.answer
        # Count existing Greek blockquotes (lines starting with > containing Greek chars)
        greek_quote_count = len(
            _re.findall(
                r"^>\s*.*[\u0370-\u03FF\u1F00-\u1FFF]",
                text,
                _re.MULTILINE,
            )
        )

        if greek_quote_count >= 2:
            return answer  # LLM already included quotations

        bundles = state.evidence_bundles
        if not bundles:
            return answer

        # Build quotation blocks from the best evidence bundles
        sections: list[str] = []
        seen_works: set[str] = set()

        for bundle in bundles:
            if not bundle.original_text or len(bundle.original_text.strip()) < 20:
                continue
            work_key = bundle.work_title or bundle.work_id
            if work_key in seen_works:
                continue
            seen_works.add(work_key)

            # Build the quotation block
            author = bundle.author or "Unknown"
            ref = bundle.canonical_ref or ""
            title = bundle.work_title or "Unknown work"
            original = bundle.original_text.strip()
            # Truncate very long passages
            if len(original) > 600:
                original = original[:600] + "..."

            block = f"> {original} ({author}, *{title}* {ref})"

            if bundle.translation_text:
                trans = bundle.translation_text.strip()
                if len(trans) > 600:
                    trans = trans[:600] + "..."
                block += f'\n> "{trans}"'

            ref_marker = ""
            if (
                bundle.bundle_id
                and state.context_pack
                and state.context_pack.bundle_refs
            ):
                ref_marker = state.context_pack.bundle_refs.get(bundle.bundle_id, "")
                if ref_marker:
                    ref_marker = f" [{ref_marker}]"

            block += ref_marker
            sections.append(block)

            if len(sections) >= 5:
                break

        if not sections:
            return answer

        # Append the primary sources section
        injection = "\n\n## Primary Textual Evidence\n\n" + "\n\n".join(sections)
        new_text = text.rstrip() + injection

        return answer.model_copy(
            update={
                "answer": new_text,
                "metadata": {
                    **answer.metadata,
                    "passage_injection": {
                        "injected": len(sections),
                        "reason": f"LLM produced only {greek_quote_count} Greek quotation(s), minimum is 2",
                    },
                },
            }
        )

    async def _verify_ancient_text(self, answer: ScholarlyAnswer) -> ScholarlyAnswer:
        """Deterministic verification: Greek/Latin text must be in the DB.

        Short technical terms (≤ 4 words) pass automatically.
        Longer extracts are checked against the passages table.
        Unverified text is flagged or removed.
        """
        from eleutheria_graphrag.agents.text_verifier import (
            sanitize_answer,
            verify_greek_text,
        )

        try:
            verification = await verify_greek_text(
                answer.answer,
                self.deps.db,
            )
            if not verification.all_verified:
                sanitized = sanitize_answer(answer.answer, verification)
                answer = answer.model_copy(
                    update={
                        "answer": sanitized,
                        "metadata": {
                            **answer.metadata,
                            "text_verification": {
                                "verified": len(verification.verified_extracts),
                                "unverified": len(verification.unverified_extracts),
                                "misattributed": len(
                                    verification.misattributed_extracts
                                ),
                                "unverified_texts": [
                                    {
                                        "text": e.text[:100],
                                        "words": e.word_count,
                                        "action": e.action,
                                    }
                                    for e in verification.unverified_extracts
                                ],
                                "misattributed_texts": [
                                    {
                                        "text": e.text[:80],
                                        "claimed": e.claimed_work,
                                        "actual": e.actual_work,
                                        "actual_ref": e.actual_ref,
                                        "action": e.action,
                                    }
                                    for e in verification.misattributed_extracts
                                ],
                            },
                        },
                    }
                )
                logger.warning(
                    "Text verification: %d verified, %d unverified",
                    len(verification.verified_extracts),
                    len(verification.unverified_extracts),
                )
            else:
                answer = answer.model_copy(
                    update={
                        "metadata": {
                            **answer.metadata,
                            "text_verification": {
                                "verified": len(verification.verified_extracts),
                                "unverified": 0,
                                "status": "all_verified",
                            },
                        },
                    }
                )
        except Exception:
            logger.warning("Text verification failed", exc_info=True)

        return answer

    async def query_dict(
        self,
        question: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        answer = await self.query(question, **kwargs)
        return {
            "answer": answer.answer,
            "question": answer.question,
            "citations": [c.model_dump() for c in answer.citations],
            "seed_nodes": answer.seed_nodes,
            "context_nodes": answer.context_nodes,
            "passages_used": answer.passages_used,
            "llm_model": self.deps.llm.last_model_used,
            "llm_provider": self.deps.llm.last_provider_used,
            "metadata": {
                **answer.metadata,
                "complexity": answer.complexity.value,
                "iterations": answer.iterations,
                "sub_queries": answer.sub_queries,
                "query_type": getattr(answer.query_type, "value", answer.query_type),
                "quality_badge": answer.quality_badge,
                "grounding_policy": answer.grounding_policy.value,
                "claim_ledger_size": len(answer.claim_ledger),
            },
        }

    async def query_stream(
        self,
        question: str,
        *,
        max_iterations: int = 5,
        selected_model: str = "gemini-3.1-pro",
        retrieval_mode: str = "auto",
        agent_mode: str | None = None,
    ) -> AsyncIterator[str]:
        mode = agent_mode or AGENT_MODE

        if mode == "react":
            async for event_json in self._stream_react(
                question,
                max_iterations=max_iterations,
                selected_model=selected_model,
                retrieval_mode=retrieval_mode,
            ):
                yield event_json
            return

        # FSM fallback: run full query then chunk
        answer = await self.query(
            question,
            max_iterations=max_iterations,
            selected_model=selected_model,
            retrieval_mode=retrieval_mode,
            agent_mode=agent_mode,
        )
        async for chunk in self._chunk_answer(answer):
            yield chunk

    async def _stream_react(
        self,
        question: str,
        *,
        max_iterations: int = 5,
        selected_model: str = "gemini-3.1-pro",
        retrieval_mode: str = "auto",
    ) -> AsyncIterator[str]:
        """Stream ReAct agent events as JSON strings.

        Emits agent_thinking, tool_start, tool_result events in real time,
        then the final answer as answer_chunk + complete events.
        """
        import asyncio

        from pydantic_graph import End, GraphRunContext

        from eleutheria_graphrag.agents.react_loop import AgentLoop
        from eleutheria_graphrag.agents.sse_emitter import SSEEmitter
        from eleutheria_graphrag.agents.tools import build_tool_registry

        state = RAGState(
            question=question,
            max_iterations=max_iterations,
            selected_model=selected_model,
            retrieval_mode=retrieval_mode,
        )

        # Phase 1: Classify
        yield json.dumps(
            {"type": "status", "message": "Classifying query...", "data": {"step": 0}}
        )
        classify_node = ClassifyQueryType()
        ctx = GraphRunContext(state=state, deps=self.deps)
        await classify_node.run(ctx)
        yield json.dumps(
            {
                "type": "status",
                "message": f"Query classified: {state.complexity.value}",
                "data": {"step": 1},
            }
        )

        # Phase 2: Agent loop with real-time SSE
        queue: asyncio.Queue[dict[str, Any] | None] = asyncio.Queue()
        emitter = SSEEmitter(queue)
        tools = build_tool_registry(self.deps)

        agent = AgentLoop(
            deps=self.deps,
            state=state,
            tools=tools,
            emitter=emitter,
        )

        # Run agent in background task, yield events as they arrive
        agent_task = asyncio.create_task(self._run_agent_and_close(agent, emitter))

        while True:
            event = await queue.get()
            if event is None:
                break  # Agent finished
            yield json.dumps(event, default=str)

        # Wait for agent task to complete (should already be done)
        await agent_task

        # Phase 3: Synthesis
        yield json.dumps(
            {
                "type": "status",
                "message": "Synthesizing answer...",
                "data": {"step": 99},
            }
        )

        draft_node = DraftClaimLedger()
        ctx = GraphRunContext(state=state, deps=self.deps)
        await draft_node.run(ctx)

        render_node = RenderGroundedAnswer()
        ctx = GraphRunContext(state=state, deps=self.deps)
        await render_node.run(ctx)

        verify_node = ProgrammaticVerify()
        ctx = GraphRunContext(state=state, deps=self.deps)
        result = await verify_node.run(ctx)

        if isinstance(result, End):
            answer = result.data
        else:
            from eleutheria_graphrag.agents.graph_nodes import _make_answer

            answer = _make_answer(state)

        # Phase 3.5: Programmatic passage injection
        answer = self._inject_passage_quotations(answer, state)

        # Phase 4: Text verification DISABLED (false positives)

        # Stream the answer in chunks
        async for chunk in self._chunk_answer(answer):
            yield chunk

    @staticmethod
    async def _run_agent_and_close(agent: Any, emitter: Any) -> None:
        """Run the agent loop and close the emitter when done."""
        try:
            await agent.run()
        except Exception as e:
            logger.error("Agent loop error: %s", e, exc_info=True)
            await emitter.emit_error(str(e))
        finally:
            await emitter.close()

    async def _chunk_answer(self, answer: ScholarlyAnswer) -> AsyncIterator[str]:
        """Chunk a ScholarlyAnswer into answer_chunk + complete SSE events."""
        text = answer.answer
        paragraphs = re.split(r"\n\n+", text)
        for i, para in enumerate(paragraphs):
            if i > 0:
                yield "\n\n"
            if len(para) <= 500:
                yield para
            else:
                sentences = _SENTENCE_SPLIT_RE.split(para)
                buffer = ""
                for sent in sentences:
                    if buffer and len(buffer) + len(sent) + 1 > 500:
                        yield buffer
                        buffer = sent
                    else:
                        buffer = f"{buffer} {sent}" if buffer else sent
                if buffer:
                    yield buffer

        complete_data = {
            "answer": answer.answer,
            "question": answer.question,
            "citations": [c.model_dump() for c in answer.citations],
            "seed_nodes": answer.seed_nodes,
            "context_nodes": answer.context_nodes,
            "passages_used": answer.passages_used,
            "llm_model": self.deps.llm.last_model_used,
            "llm_provider": self.deps.llm.last_provider_used,
            "metadata": {
                **answer.metadata,
                "complexity": answer.complexity.value,
                "iterations": answer.iterations,
                "sub_queries": answer.sub_queries,
                "query_type": getattr(answer.query_type, "value", answer.query_type),
                "quality_badge": answer.quality_badge,
                "grounding_policy": answer.grounding_policy.value,
                "claim_ledger_size": len(answer.claim_ledger),
            },
        }
        yield json.dumps({"type": "complete", "data": complete_data}, default=str)
