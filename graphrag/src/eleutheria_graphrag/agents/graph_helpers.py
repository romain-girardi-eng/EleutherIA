"""
Shared helper functions extracted from graph_nodes.py.

Used by both the pydantic-graph FSM nodes and the new ReAct agent loop.
"""

from __future__ import annotations

import json
import os
import re
import time as _time
from typing import Any

from eleutheria_graphrag.agents.state import RAGState, ReasoningStep
from eleutheria_graphrag.services.model_registry import get_model

DB_SCHEMA = os.getenv("ELEUTHERIA_DB_SCHEMA", "free_will")


def append_reasoning_step(
    state: RAGState,
    node_name: str,
    model: str | None,
    prompt_summary: str,
    full_prompt_tokens: int,
    raw_output: str,
    thinking: str | None = None,
    parsed_result: dict[str, Any] | None = None,
    skipped: bool = False,
    skip_reason: str | None = None,
    duration_ms: int = 0,
) -> None:
    """Append a ReasoningStep to the state's reasoning trace."""
    state.reasoning_trace.append(
        ReasoningStep(
            node_name=node_name,
            timestamp_ms=int(_time.time() * 1000),
            duration_ms=duration_ms,
            model=model,
            prompt_summary=prompt_summary[:200],
            full_prompt_tokens=full_prompt_tokens,
            raw_output=raw_output,
            thinking=thinking,
            parsed_result=parsed_result,
            skipped=skipped,
            skip_reason=skip_reason,
        )
    )


def resolve_model_api_id(state: RAGState) -> str | None:
    """Return model_override for non-default (non-Gemini) models."""
    try:
        model_info = get_model(state.selected_model)
        return model_info.api_id if model_info.provider == "openrouter" else None
    except KeyError:
        return None


def parse_json(text: str) -> Any:
    """Extract JSON from LLM output, stripping markdown code fences.

    Handles common LLM output quirks: smart quotes, trailing commas,
    NaN values, embedded code fences, and partial JSON extraction.
    """

    def _repair_json(candidate: str) -> str:
        candidate = (
            candidate.replace("\u201c", '"')
            .replace("\u201d", '"')
            .replace("\u2018", "'")
            .replace("\u2019", "'")
        )
        candidate = re.sub(r",(\s*[}\]])", r"\1", candidate)
        candidate = re.sub(r":\s*NaN\b", ": null", candidate)
        candidate = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", candidate)
        return candidate

    text = text.strip()
    if text.lower().startswith("json"):
        text = text[4:].lstrip(": \n\t")
    match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if match:
        text = match.group(1).strip()
    elif text.startswith("```"):
        text = re.sub(r"^```(?:json)?", "", text, count=1).strip()
        if text.endswith("```"):
            text = text[:-3].strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        repaired = _repair_json(text)
        if repaired != text:
            try:
                return json.loads(repaired)
            except json.JSONDecodeError:
                pass
        candidates: list[str] = []
        start_obj = text.find("{")
        start_arr = text.find("[")
        if start_obj != -1:
            end_obj = text.rfind("}")
            if end_obj != -1 and end_obj > start_obj:
                candidates.append(text[start_obj : end_obj + 1])
        if start_arr != -1:
            end_arr = text.rfind("]")
            if end_arr != -1 and end_arr > start_arr:
                candidates.append(text[start_arr : end_arr + 1])
        for candidate in candidates:
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                repaired = _repair_json(candidate)
                if repaired != candidate:
                    try:
                        return json.loads(repaired)
                    except json.JSONDecodeError:
                        pass
        raise
