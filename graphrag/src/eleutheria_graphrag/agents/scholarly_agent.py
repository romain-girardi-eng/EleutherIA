"""
Scholarly Agent facade — orchestrates the GraphRAG pipeline.

Supports two modes via ELEUTHERIA_AGENT_MODE env var:
  - "fsm" (default): Original 12-node pydantic-graph pipeline
  - "react": New ReAct agent loop with tools (Phase 2)
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import time as _time_mod
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


def _claim_from_answer(answer_text: str, ref: str) -> str | None:
    """Extract the sentence containing citation ``[ref]`` from the answer.

    Returns ``None`` if the marker is absent. Used by the v2 verifier hook to
    pair each citation with the prose it is supposed to support.
    """
    if not answer_text or not ref:
        return None
    marker = f"[{ref}]"
    if marker not in answer_text:
        return None
    for sentence in _SENTENCE_SPLIT_RE.split(answer_text):
        if marker in sentence:
            return sentence.strip()
    return None


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

        from eleutheria_graphrag.agents.react_loop import build_agent_loop
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

        # Phase 2: Agent loop (native tool-calling or legacy text mode)
        tools = build_tool_registry(self.deps)
        emitter = NullEmitter()
        agent = build_agent_loop(
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

        # Phase 5: Adversarial citation verifier (v2). Optional — only runs
        # when ``deps.verifier_v2`` is wired. Degrades gracefully: any error
        # is logged and the unflagged draft is returned (the verifier never
        # crashes the pipeline).
        if self.deps.verifier_v2 is not None:
            try:
                answer = await self._run_citation_verifier_v2(answer)
            except Exception:
                logger.warning(
                    "CitationVerifierV2 failed — returning unflagged draft",
                    exc_info=True,
                )
        return answer

    async def _run_citation_verifier_v2(
        self, answer: ScholarlyAnswer
    ) -> ScholarlyAnswer:
        """Run the v2 adversarial verifier and attach its report to the answer."""
        from eleutheria_graphrag.models.verification import (
            DraftClaim,
            SynthesizedDraft,
        )

        verifier = self.deps.verifier_v2
        if verifier is None or not answer.citations:
            return answer

        # Map each Citation → DraftClaim. The ``claim`` is the surrounding
        # sentence in the rendered answer (best-effort) so the verifier has
        # something to audit even when the synthesizer didn't expose a
        # structured claim ledger.
        claims: list[DraftClaim] = []
        for citation in answer.citations:
            claim_text = (
                _claim_from_answer(answer.answer, citation.ref) or citation.label
            )
            claims.append(
                DraftClaim(
                    claim=claim_text,
                    citation_id=citation.id,
                    citation_kind="passage" if citation.type == "passage" else "node",
                )
            )

        draft = SynthesizedDraft(
            question=answer.question,
            answer_text=answer.answer,
            claims=claims,
        )
        report = await verifier.verify_draft(draft)

        # Merge per-citation verdicts back into Citation.verified for the
        # frontend. WEAK is reported as verified=False but kept; REJECTED and
        # MISSING are flagged for removal.
        verdicts = {c.citation_id: c for c in report.checks}
        updated_citations = []
        for citation in answer.citations:
            verdict = verdicts.get(citation.id)
            if verdict is None:
                updated_citations.append(citation)
                continue
            updated_citations.append(
                citation.model_copy(
                    update={
                        "verified": verdict.is_passing,
                        "verification_note": (
                            f"[{verdict.status.value}] {verdict.reasoning}"
                        ),
                    }
                )
            )

        return answer.model_copy(
            update={
                "citations": updated_citations,
                "metadata": {
                    **answer.metadata,
                    "citation_verifier_v2": {
                        "total": report.total,
                        "verified": report.verified,
                        "weak": report.weak,
                        "rejected": report.rejected,
                        "missing": report.missing,
                        "rejection_rate": report.rejection_rate,
                        "flagged_for_rewrite": report.flagged_for_rewrite,
                        "warning": report.warning,
                        "aborted": report.aborted,
                    },
                },
            }
        )

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
            "claim_ledger": [c.model_dump() for c in answer.claim_ledger],
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
        then the final answer as answer_chunk + complete events. Per-stage
        ``stage_complete`` events are emitted at each phase boundary so the
        frontend AgentTrace pane can render a latency stack.
        """
        import asyncio
        import time as _time

        from pydantic_graph import End, GraphRunContext

        from eleutheria_graphrag.agents.react_loop import build_agent_loop
        from eleutheria_graphrag.agents.sse_emitter import SSEEmitter
        from eleutheria_graphrag.agents.tools import build_tool_registry

        state = RAGState(
            question=question,
            max_iterations=max_iterations,
            selected_model=selected_model,
            retrieval_mode=retrieval_mode,
        )

        # Phase 1: Classify
        stage_started = _time.perf_counter()
        yield json.dumps(
            {"type": "status", "message": "Classifying query...", "data": {"step": 0}}
        )
        classify_node = ClassifyQueryType()
        ctx = GraphRunContext(state=state, deps=self.deps)
        await classify_node.run(ctx)
        classify_ms = int((_time.perf_counter() - stage_started) * 1000)
        yield json.dumps(
            {
                "type": "status",
                "message": f"Query classified: {state.complexity.value}",
                "data": {"step": 1},
            }
        )
        yield json.dumps(
            {
                "type": "stage_complete",
                "stage": "classify",
                "duration_ms": classify_ms,
                "metadata": {"complexity": state.complexity.value},
            }
        )

        # Phase 2: Agent loop with real-time SSE
        stage_started = _time.perf_counter()
        queue: asyncio.Queue[dict[str, Any] | None] = asyncio.Queue()
        emitter = SSEEmitter(queue)
        tools = build_tool_registry(self.deps)

        agent = build_agent_loop(
            deps=self.deps,
            state=state,
            tools=tools,
            emitter=emitter,
        )

        # Run agent in background task, yield events as they arrive
        agent_task = asyncio.create_task(self._run_agent_and_close(agent, emitter))

        tool_calls_observed = 0
        while True:
            event = await queue.get()
            if event is None:
                break  # Agent finished
            if isinstance(event, dict) and event.get("type") in {
                "tool_start",
                "tool_call",
            }:
                tool_calls_observed += 1
            yield json.dumps(event, default=str)

        # Wait for agent task to complete (should already be done)
        await agent_task

        agent_loop_ms = int((_time.perf_counter() - stage_started) * 1000)
        yield json.dumps(
            {
                "type": "stage_complete",
                "stage": "agent_loop",
                "duration_ms": agent_loop_ms,
                "metadata": {"tool_calls": tool_calls_observed},
            }
        )

        # Phase 3: Synthesis (two LLM calls — draft claim ledger then render
        # answer). Each one can run for 30-90 s on a doctoral-grade query;
        # without intermediate SSE traffic the Cloudflare tunnel drops the
        # connection at ~100 s of silence and the client never sees a
        # `complete` event. We wrap every long await with a heartbeat that
        # emits a status SSE every 10 s, both to keep the wire warm and to
        # show real progress in the UI.
        stage_started = _time.perf_counter()
        yield json.dumps(
            {
                "type": "status",
                "message": "Synthesizing answer...",
                "data": {"step": 99},
            }
        )

        ctx = GraphRunContext(state=state, deps=self.deps)
        async for hb in self._await_with_heartbeat(
            DraftClaimLedger().run(ctx),
            label="Drafting claim ledger",
            stage_id="draft_claim_ledger",
        ):
            yield hb

        ctx = GraphRunContext(state=state, deps=self.deps)
        async for hb in self._await_with_heartbeat(
            RenderGroundedAnswer().run(ctx),
            label="Rendering grounded answer",
            stage_id="render_grounded_answer",
        ):
            yield hb

        synthesis_ms = int((_time.perf_counter() - stage_started) * 1000)
        yield json.dumps(
            {
                "type": "stage_complete",
                "stage": "synthesis",
                "duration_ms": synthesis_ms,
            }
        )

        stage_started = _time.perf_counter()
        verify_node = ProgrammaticVerify()
        ctx = GraphRunContext(state=state, deps=self.deps)
        verify_result_holder: dict[str, Any] = {}
        async for hb in self._await_with_heartbeat(
            verify_node.run(ctx),
            label="Verifying citations",
            stage_id="verify",
            interval=8.0,
            result_into=verify_result_holder,
        ):
            yield hb
        result = verify_result_holder.get("value")
        verify_ms = int((_time.perf_counter() - stage_started) * 1000)
        yield json.dumps(
            {
                "type": "stage_complete",
                "stage": "verify",
                "duration_ms": verify_ms,
            }
        )

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

    async def _await_with_heartbeat(
        self,
        coro: Any,
        *,
        label: str,
        stage_id: str,
        interval: float = 10.0,
        result_into: dict[str, Any] | None = None,
    ) -> AsyncIterator[str]:
        """Run ``coro`` while yielding ``status`` SSE strings every ``interval`` s.

        Cloudflare tunnel idles out an SSE connection after ~100 s of
        silence, which used to drop doctoral-grade queries mid-synthesis.
        Wrapping the long awaits here keeps a steady drip of frames on the
        wire and surfaces real progress (elapsed seconds) to the UI.

        The coroutine's return value, if any, is stashed in
        ``result_into['value']`` for the caller (avoids re-running the
        coroutine just to get its result).
        """
        task = asyncio.create_task(coro)
        started = _time_mod.monotonic()
        # First-frame ping: clients see we entered this stage immediately.
        yield json.dumps(
            {
                "type": "status",
                "message": f"{label}…",
                "data": {"step": 99, "stage": stage_id, "elapsed_s": 0},
            }
        )
        try:
            while not task.done():
                try:
                    await asyncio.wait_for(asyncio.shield(task), timeout=interval)
                except TimeoutError:
                    elapsed = int(_time_mod.monotonic() - started)
                    yield json.dumps(
                        {
                            "type": "status",
                            "message": f"{label}… ({elapsed}s)",
                            "data": {
                                "step": 99,
                                "stage": stage_id,
                                "elapsed_s": elapsed,
                            },
                        }
                    )
        except Exception:
            # Cancel only if still running; let exception surface below.
            if not task.done():
                task.cancel()
            raise
        try:
            value = task.result()
        except Exception:
            logger.exception("Heartbeat-wrapped task %s failed", stage_id)
            raise
        if result_into is not None:
            result_into["value"] = value

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
