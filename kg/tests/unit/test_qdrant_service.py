"""Tests for Qdrant connection resolution."""

from eleutheria_kg.services.qdrant import _resolve_qdrant_connection


class TestResolveQdrantConnection:
    """Ensure cloud Qdrant wins over a stale localhost URL."""

    def test_prefers_cloud_host_over_localhost_url(self, monkeypatch):
        monkeypatch.setenv("QDRANT_URL", "http://localhost:6333")
        monkeypatch.setenv("QDRANT_HOST", "example.cloud.qdrant.io")
        monkeypatch.setenv("QDRANT_API_KEY", "secret")
        monkeypatch.setenv("QDRANT_HTTP_PORT", "6333")

        resolved = _resolve_qdrant_connection()

        assert resolved["mode"] == "cloud"
        assert resolved["url"] == "https://example.cloud.qdrant.io"
        assert resolved["api_key"] == "secret"

    def test_uses_explicit_qdrant_url_when_not_localhost(self, monkeypatch):
        monkeypatch.setenv("QDRANT_URL", "https://custom-qdrant.example")
        monkeypatch.setenv("QDRANT_HOST", "example.cloud.qdrant.io")
        monkeypatch.setenv("QDRANT_API_KEY", "secret")

        resolved = _resolve_qdrant_connection()

        assert resolved["mode"] == "url"
        assert resolved["url"] == "https://custom-qdrant.example"
