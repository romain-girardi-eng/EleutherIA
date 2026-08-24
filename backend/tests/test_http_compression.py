import importlib

from fastapi.testclient import TestClient
from starlette.middleware.gzip import GZipMiddleware


def test_api_origin_compresses_large_json_and_keeps_gzip_configured(monkeypatch) -> None:
    monkeypatch.setenv("JWT_SECRET_KEY", "a" * 64)
    main = importlib.import_module("backend.main")
    application = main.create_app()

    gzip = next(
        middleware
        for middleware in application.user_middleware
        if middleware.cls is GZipMiddleware
    )
    assert gzip.kwargs["minimum_size"] == 1024
    assert gzip.kwargs["compresslevel"] == 6

    # OpenAPI is a deterministic, sufficiently large JSON response that does
    # not require starting database/GraphRAG services for this middleware gate.
    client = TestClient(application, raise_server_exceptions=True)
    response = client.get("/openapi.json", headers={"Accept-Encoding": "gzip"})
    assert response.status_code == 200
    assert response.headers["content-encoding"] == "gzip"
    assert "Accept-Encoding" in response.headers["vary"]
