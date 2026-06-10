"""Unit tests for the translation service's Gemini call plumbing."""

from __future__ import annotations

import io
import json
import urllib.request
from typing import Any

import pytest

from eleutheria_database.services.translation import call_gemini


class _FakeResponse(io.BytesIO):
    def __enter__(self) -> _FakeResponse:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()


def test_call_gemini_key_in_header_not_url(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, Any] = {}

    def fake_urlopen(
        req: urllib.request.Request, timeout: int = 0  # noqa: ARG001
    ) -> _FakeResponse:
        captured["url"] = req.full_url
        captured["headers"] = dict(req.header_items())
        body = {
            "candidates": [{"content": {"parts": [{"text": '[{"id":"x","en":"y"}]'}]}}]
        }
        return _FakeResponse(json.dumps(body).encode())

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)

    result = call_gemini("prompt", api_key="not-a-real-key")
    assert result == '[{"id":"x","en":"y"}]'
    # Regression: the API key must travel in a header, never the query string.
    assert "not-a-real-key" not in captured["url"]
    assert "key=" not in captured["url"]
    headers = {k.lower(): v for k, v in captured["headers"].items()}
    assert headers["x-goog-api-key"] == "not-a-real-key"


def test_call_gemini_requires_key() -> None:
    with pytest.raises(RuntimeError, match="GEMINI_API_KEY"):
        call_gemini("prompt", api_key="")
