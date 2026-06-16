"""
CLI fixture for the Track P (Python-native) spike.

Runs a single question through the new native tool-calling ``NativeAgentLoop``
and prints every SSE event to stdout. Used to compare Track P vs Track O
outputs side-by-side outside of FastAPI.

Usage::

    .venv-py314/bin/python -m eleutheria_graphrag.agents.repl \
        --question "What does Aristotle say about voluntary action?"

The script reuses ``GraphRAGService`` to assemble all of the pipeline
dependencies (DB, KG, retrieval strategy, LLM) so the spike compares the
real production wiring.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import sys
import time
from typing import Any

logger = logging.getLogger("eleutheria.repl")


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a single GraphRAG query through the native tool-calling agent."
    )
    parser.add_argument("--question", "-q", required=True, help="The question.")
    parser.add_argument(
        "--output",
        "-o",
        default=None,
        help="Path to write the captured event log (defaults to stdout only).",
    )
    parser.add_argument(
        # ONE-LINE K2.7 SWAP (ARCHITECTURE §K2.7): when K2.7 lands on Fireworks,
        # change the default below to its Fireworks id. Do NOT point this at a
        # Moonshot id (Fireworks-only constraint).
        "--model",
        default=os.getenv(
            "ELEUTHERIA_DEFAULT_MODEL", "accounts/fireworks/models/kimi-k2p6"
        ),
        help="LLM model id (default: Fireworks Kimi K2.6).",
    )
    parser.add_argument(
        "--legacy",
        action="store_true",
        help="Force the legacy text-parsing AgentLoop (LLM_TOOL_CALLING_MODE=text).",
    )
    return parser.parse_args(argv)


async def _run(args: argparse.Namespace) -> int:
    if args.legacy:
        os.environ["LLM_TOOL_CALLING_MODE"] = "text"
    else:
        os.environ.setdefault("LLM_TOOL_CALLING_MODE", "native")

    # Lazy imports.
    from eleutheria_graphrag.agents.react_loop import (
        AgentLoop,
        NativeAgentLoop,
        build_agent_loop,
    )
    from eleutheria_graphrag.agents.sse_emitter import SSEEmitter
    from eleutheria_graphrag.agents.state import QueryComplexity, RAGState
    from eleutheria_graphrag.agents.tools import build_tool_registry
    from eleutheria_graphrag.services.graphrag_service import GraphRAGService

    db = _build_db()
    service = GraphRAGService(db_service=db)
    await service.load_kg()

    # Reach into the loaded ScholarlyAgent for ready-made deps.
    if service._agent is None:  # noqa: SLF001 — intentional for the spike
        raise RuntimeError("GraphRAGService.load_kg did not build an agent")
    deps = service._agent.deps  # noqa: SLF001

    tools = build_tool_registry(deps)
    state = RAGState(
        question=args.question,
        complexity=QueryComplexity.MEDIUM,
        selected_model=args.model,
    )

    queue: asyncio.Queue[dict[str, Any] | None] = asyncio.Queue()
    emitter = SSEEmitter(queue)
    loop = build_agent_loop(deps=deps, state=state, tools=tools, emitter=emitter)
    assert isinstance(loop, (NativeAgentLoop, AgentLoop))

    events: list[dict[str, Any]] = []
    tool_call_count = 0
    citation_count = 0
    t0 = time.monotonic()

    async def _consume() -> None:
        nonlocal tool_call_count, citation_count
        while True:
            event = await queue.get()
            if event is None:
                return
            events.append(event)
            etype = event.get("type")
            if etype == "tool_call":
                tool_call_count += 1
            elif etype == "citation_found":
                citation_count += 1
            print(json.dumps(event, ensure_ascii=False, default=str))

    consumer = asyncio.create_task(_consume())

    try:
        await loop.run()
    except Exception as exc:  # pragma: no cover
        logger.error("Agent loop failed: %s", exc, exc_info=True)
        await emitter.emit_error(str(exc))
    finally:
        await emitter.close()
        await consumer

    duration = time.monotonic() - t0
    answer = loop.final_answer or ""

    summary = {
        "type": "summary",
        "duration_seconds": round(duration, 2),
        "tool_calls": tool_call_count,
        "citation_events": citation_count,
        "answer_length": len(answer),
        "calls_made": loop.calls_made,
        "answer": answer,
    }
    print(json.dumps(summary, ensure_ascii=False, default=str))

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            for event in events:
                f.write(json.dumps(event, ensure_ascii=False, default=str) + "\n")
            f.write(json.dumps(summary, ensure_ascii=False, default=str) + "\n")
        logger.info("Wrote %d events to %s", len(events), args.output)

    return 0 if answer else 1


def _build_db() -> Any:
    """Construct an asyncpg-backed DB service from environment variables."""
    try:
        from eleutheria_database.services.db import DBService
    except ImportError:  # pragma: no cover — DB package optional offline
        logger.warning(
            "eleutheria_database not importable; running against KG snapshot"
        )
        return None

    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        logger.warning("DATABASE_URL not set; running against KG snapshot")
        return None
    return DBService(db_url)


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "WARNING"),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    args = _parse_args(argv)
    return asyncio.run(_run(args))


if __name__ == "__main__":
    sys.exit(main())
