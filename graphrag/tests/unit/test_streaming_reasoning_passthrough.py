"""Live reasoning deltas: the per-provider opt-in and the one SSE reader.

Before this, a STREAMING request asked for nothing beyond the answer, and the
segmented parser only knew the flat legacy ``reasoning_content`` field — so the
Reasoning tab was empty on every Codex and Gemini-proxy run. Two halves are
guarded here:

* the request body carries each provider's verified opt-in
  (Codex ``reasoning: {"summary": "auto"}``, Gemini proxy
  ``include_reasoning: true``, Claude nothing) and ONLY when streaming;
* the OpenAI-compatible SSE reader turns whatever dialect comes back into
  ``("reasoning", …)`` segments, strictly apart from ``("answer", …)``.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from eleutheria_graphrag.services.llm_service import (
    SYNTHESIS_TIER,
    LLMService,
    ModelProvider,
    _reasoning_delta_text,
)

PROXY = "http://pragma-gemini-proxy:8320/v1"

_GEMINI_PROXY_ENV = {
    "GEMINI_PROXY_BASE_URL": PROXY,
    "GEMINI_PROXY_API_KEY": "proxy-key",
}


def _payload(provider: ModelProvider, *, streaming: bool) -> dict:
    config = LLMService._resolve_config(provider)
    return LLMService._openai_compatible_payload(
        provider,
        "prompt",
        "system",
        0.7,
        4096,
        config,
        reasoning_effort=LLMService._reasoning_effort_for_request(
            provider, config, tier=SYNTHESIS_TIER, override=None
        ),
        tier=SYNTHESIS_TIER,
        streaming=streaming,
    )


class TestReasoningOptInPayload:
    """Which providers get which live-reasoning directive, and when."""

    def test_codex_streaming_asks_for_a_reasoning_summary(self):
        with patch.dict("os.environ", {}, clear=True):
            body = _payload(ModelProvider.CODEX, streaming=True)
        assert body["reasoning"] == {"summary": "auto"}
        # The existing effort directive is untouched.
        assert body["reasoning_effort"] == "high"

    def test_codex_non_streaming_does_not(self):
        with patch.dict("os.environ", {}, clear=True):
            body = _payload(ModelProvider.CODEX, streaming=False)
        assert "reasoning" not in body
        assert body["reasoning_effort"] == "high"

    def test_gemini_proxy_streaming_asks_for_include_reasoning(self):
        with patch.dict("os.environ", _GEMINI_PROXY_ENV, clear=True):
            body = _payload(ModelProvider.GEMINI, streaming=True)
        assert body["include_reasoning"] is True
        # The Codex form is NOT what the Gemini proxy honours.
        assert "reasoning" not in body

    def test_gemini_proxy_non_streaming_does_not(self):
        with patch.dict("os.environ", _GEMINI_PROXY_ENV, clear=True):
            body = _payload(ModelProvider.GEMINI, streaming=False)
        assert "include_reasoning" not in body

    def test_native_gemini_rung_never_gets_the_proxy_directive(self):
        """Without a proxy the GEMINI rung does not speak this dialect at all."""
        with patch.dict("os.environ", {}, clear=True):
            body = _payload(ModelProvider.GEMINI, streaming=True)
        assert "include_reasoning" not in body
        assert "reasoning" not in body

    def test_claude_exposes_nothing_either_way(self):
        with patch.dict("os.environ", {}, clear=True):
            for streaming in (True, False):
                body = _payload(ModelProvider.CLAUDE, streaming=streaming)
                assert "reasoning" not in body
                assert "include_reasoning" not in body


class TestReasoningDeltaReader:
    """One reader for every dialect that streams thinking separately."""

    def test_flat_legacy_field(self):
        assert _reasoning_delta_text({"reasoning_content": "weighing"}) == "weighing"

    def test_responses_style_summary_object(self):
        assert (
            _reasoning_delta_text({"reasoning": {"summary": "weighing"}}) == "weighing"
        )

    def test_responses_style_content_parts(self):
        delta = {"reasoning": {"content": [{"text": "wei"}, {"text": "ghing"}]}}
        assert _reasoning_delta_text(delta) == "weighing"

    def test_bare_string_reasoning(self):
        assert _reasoning_delta_text({"reasoning": "weighing"}) == "weighing"

    def test_answer_only_delta_reads_as_empty(self):
        assert _reasoning_delta_text({"content": "Bobzien argues"}) == ""

    def test_unexpected_shapes_never_raise(self):
        assert _reasoning_delta_text(None) == ""
        assert _reasoning_delta_text({"reasoning": 17}) == ""
        assert _reasoning_delta_text({"reasoning": {"unknown": "x"}}) == ""


def _fake_stream(lines: list[str], mock_client) -> None:
    response = MagicMock()
    response.status_code = 200
    response.raise_for_status = MagicMock()

    async def _aiter_lines():
        for line in lines:
            yield line

    response.aiter_lines = _aiter_lines
    ctx = MagicMock()
    ctx.__aenter__ = AsyncMock(return_value=response)
    ctx.__aexit__ = AsyncMock(return_value=False)
    mock_client.stream = MagicMock(return_value=ctx)


def _delta_line(payload: str) -> str:
    return 'data: {"choices":[{"delta":' + payload + "}]}"


class TestSegmentedStreamEndToEnd:
    """``stream_segmented`` must tag reasoning apart from the answer."""

    @pytest.mark.asyncio
    async def test_codex_reasoning_content_becomes_reasoning_segments(self):
        with patch.dict("os.environ", {"CODEX_PROXY_API_KEY": "codex-key"}, clear=True):
            llm = LLMService(preferred_provider=ModelProvider.CODEX)
            mock_client = AsyncMock()
            _fake_stream(
                [
                    _delta_line('{"reasoning_content":"Checking Bobzien "}'),
                    _delta_line('{"reasoning_content":"against Frede."}'),
                    _delta_line('{"content":"Bobzien argues"}'),
                    "data: [DONE]",
                ],
                mock_client,
            )
            llm._client = mock_client

            segments = [seg async for seg in llm.stream_segmented("Question")]

        assert segments == [
            ("reasoning", "Checking Bobzien "),
            ("reasoning", "against Frede."),
            ("answer", "Bobzien argues"),
        ]
        # The side-channel still accumulates the whole chain-of-thought.
        assert llm.last_reasoning_content == "Checking Bobzien against Frede."
        body = mock_client.stream.call_args.kwargs["json"]
        assert body["reasoning"] == {"summary": "auto"}
        assert body["stream"] is True

    @pytest.mark.asyncio
    async def test_codex_responses_style_summary_deltas(self):
        """The proxy may nest the summary instead of flattening it."""
        with patch.dict("os.environ", {"CODEX_PROXY_API_KEY": "codex-key"}, clear=True):
            llm = LLMService(preferred_provider=ModelProvider.CODEX)
            mock_client = AsyncMock()
            _fake_stream(
                [
                    _delta_line('{"reasoning":{"summary":"Weighing the Stoics."}}'),
                    _delta_line('{"content":"Chrysippus"}'),
                    "data: [DONE]",
                ],
                mock_client,
            )
            llm._client = mock_client

            segments = [seg async for seg in llm.stream_segmented("Question")]

        assert segments == [
            ("reasoning", "Weighing the Stoics."),
            ("answer", "Chrysippus"),
        ]

    @pytest.mark.asyncio
    async def test_gemini_proxy_reasoning_deltas_and_request_body(self):
        env = {**_GEMINI_PROXY_ENV, "LLM_PROVIDER": "gemini"}
        with patch.dict("os.environ", env, clear=True):
            llm = LLMService(preferred_provider=ModelProvider.GEMINI)
            mock_client = AsyncMock()
            _fake_stream(
                [
                    _delta_line('{"reasoning_content":"Scanning the corpus."}'),
                    _delta_line('{"content":"Origen holds"}'),
                    "data: [DONE]",
                ],
                mock_client,
            )
            llm._client = mock_client

            segments = [seg async for seg in llm.stream_segmented("Question")]

        assert segments == [
            ("reasoning", "Scanning the corpus."),
            ("answer", "Origen holds"),
        ]
        body = mock_client.stream.call_args.kwargs["json"]
        assert body["include_reasoning"] is True

    @pytest.mark.asyncio
    async def test_plain_stream_keeps_reasoning_off_the_answer_channel(self):
        """``stream()`` yields answer deltas ONLY — reasoning stays side-channel."""
        with patch.dict("os.environ", {"CODEX_PROXY_API_KEY": "codex-key"}, clear=True):
            llm = LLMService(preferred_provider=ModelProvider.CODEX)
            mock_client = AsyncMock()
            _fake_stream(
                [
                    _delta_line('{"reasoning":{"summary":"thinking"}}'),
                    _delta_line('{"content":"answer"}'),
                    "data: [DONE]",
                ],
                mock_client,
            )
            llm._client = mock_client

            chunks = [c async for c in llm.stream("Question")]

        assert chunks == ["answer"]
        assert llm.last_reasoning_content == "thinking"
        assert mock_client.stream.call_args.kwargs["json"]["reasoning"] == {
            "summary": "auto"
        }
