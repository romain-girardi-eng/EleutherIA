"""
Structured-output synthesizer.

Wraps :class:`LLMService` so the synthesis call enforces conformance with the
``ThesisDraft`` schema via ``response_format=json_schema``. If validation
fails (e.g., the LLM omits a required field), the prompt is rebuilt with the
validation error and retried — bounded by ``max_retries``.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from pydantic import ValidationError

from eleutheria_graphrag.agents.prompts import delimit_retrieved_text
from eleutheria_graphrag.models.thesis_output import (
    ThesisDraft,
    thesis_draft_json_schema,
)

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = (
    "You are EleutherIA's scholarly synthesizer. You must emit a single JSON "
    "object validated against the ThesisDraft schema. No Markdown, no prose "
    "outside the JSON. Greek and Latin quotes must be VERBATIM from the "
    "retrieved passages — never reconstruct or paraphrase ancient text. "
    "Every claim must be backed by at least one citation."
)


class SchemaValidationError(RuntimeError):
    """Raised when the synthesizer cannot produce a valid ThesisDraft."""


def _coerce_payload(raw: str) -> dict[str, Any]:
    """Strip ```json fences and parse the LLM response."""

    text = raw.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else ""
        if text.endswith("```"):
            text = text[: -len("```")]
    text = text.strip()
    if not text:
        raise ValueError("empty LLM response")
    parsed = json.loads(text)
    if not isinstance(parsed, dict):
        raise ValueError("LLM response is not a JSON object")
    return parsed


class ThesisSynthesizer:
    """LLM-backed synthesizer that emits a validated ``ThesisDraft``.

    The synthesizer is intentionally thin — schema validation and retry are
    its only responsibilities. Retrieval, ranking and verification happen
    upstream.
    """

    def __init__(self, llm_service: Any, *, max_retries: int = 2) -> None:
        self.llm = llm_service
        self.max_retries = max_retries

    async def synthesize(
        self,
        *,
        question: str,
        context: str,
        title_hint: str | None = None,
    ) -> ThesisDraft:
        schema = thesis_draft_json_schema()
        messages: list[dict[str, str]] = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Question: {question}\n\n"
                    "Retrieved context (verbatim; do not alter):\n"
                    f"{delimit_retrieved_text(context, data_id='thesis-context')}\n\n"
                    f"Suggested title: {title_hint or question}\n\n"
                    "Emit a ThesisDraft JSON object."
                ),
            },
        ]
        last_error: str | None = None
        attempts = self.max_retries + 1
        for attempt in range(1, attempts + 1):
            if last_error:
                messages.append(
                    {
                        "role": "user",
                        "content": (
                            "The previous response failed validation: "
                            f"{last_error}\nRespond again with a corrected JSON object."
                        ),
                    }
                )
            raw = await self.llm.chat(
                messages=messages,
                response_json_schema=schema,
                temperature=0.2,
            )
            try:
                payload = _coerce_payload(raw)
                draft = ThesisDraft.model_validate(payload)
                logger.info("ThesisDraft validated on attempt %d", attempt)
                return draft
            except (ValueError, ValidationError) as exc:
                last_error = str(exc)
                logger.warning(
                    "ThesisDraft validation failed on attempt %d/%d: %s",
                    attempt,
                    attempts,
                    last_error,
                )
        raise SchemaValidationError(
            f"synthesizer failed after {attempts} attempts: {last_error}"
        )


__all__ = ["SYSTEM_PROMPT", "SchemaValidationError", "ThesisSynthesizer"]
