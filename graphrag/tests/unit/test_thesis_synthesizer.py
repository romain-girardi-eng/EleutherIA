"""Tests for the structured-output synthesizer."""

from __future__ import annotations

import json
from typing import Any

import pytest

from eleutheria_graphrag.models.thesis_output import ThesisDraft
from eleutheria_graphrag.services.thesis_synthesizer import (
    SchemaValidationError,
    ThesisSynthesizer,
)

_VALID_PAYLOAD: dict[str, Any] = {
    "title": "Aristotle on the voluntary",
    "abstract": "Short abstract.",
    "sections": [
        {
            "heading": "Intro",
            "level": 1,
            "paragraphs": [{"text": "Some prose.", "footnote_refs": [1]}],
        }
    ],
    "footnotes": [
        {
            "n": 1,
            "text": "see locus",
            "citations": [
                {"passage_id": "p1", "work_label": "Eth. Nic.", "author": "Aristotle"}
            ],
        }
    ],
    "bibliography": [
        {"kind": "primary", "author": "Aristotle", "title": "Nicomachean Ethics", "year": 1894}
    ],
}


class _StubLLM:
    def __init__(self, responses: list[str]) -> None:
        self._responses = list(responses)
        self.calls: list[dict[str, Any]] = []

    async def chat(self, *, messages: list[dict[str, str]], **kwargs: Any) -> str:
        self.calls.append({"messages": messages, **kwargs})
        return self._responses.pop(0)


@pytest.mark.asyncio
async def test_synthesizer_validates_on_first_try() -> None:
    llm = _StubLLM([json.dumps(_VALID_PAYLOAD)])
    draft = await ThesisSynthesizer(llm).synthesize(
        question="What is the voluntary?",
        context="some retrieved passages",
    )
    assert isinstance(draft, ThesisDraft)
    assert llm.calls[0]["response_json_schema"]["title"] == "ThesisDraft"


@pytest.mark.asyncio
async def test_synthesizer_strips_code_fence() -> None:
    fenced = "```json\n" + json.dumps(_VALID_PAYLOAD) + "\n```"
    draft = await ThesisSynthesizer(_StubLLM([fenced])).synthesize(
        question="Q", context="C"
    )
    assert draft.title.startswith("Aristotle")


@pytest.mark.asyncio
async def test_synthesizer_retries_on_validation_error() -> None:
    invalid = json.dumps({"title": "x"})  # missing sections / footnotes / bibliography
    llm = _StubLLM([invalid, json.dumps(_VALID_PAYLOAD)])
    draft = await ThesisSynthesizer(llm, max_retries=1).synthesize(
        question="Q", context="C"
    )
    assert isinstance(draft, ThesisDraft)
    # Second call must carry a corrective user message.
    assert any("failed validation" in m["content"] for m in llm.calls[1]["messages"])


@pytest.mark.asyncio
async def test_synthesizer_gives_up_after_max_retries() -> None:
    invalid = json.dumps({"title": "x"})
    llm = _StubLLM([invalid, invalid, invalid])
    with pytest.raises(SchemaValidationError):
        await ThesisSynthesizer(llm, max_retries=2).synthesize(question="Q", context="C")
