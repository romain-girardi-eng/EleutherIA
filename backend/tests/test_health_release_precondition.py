import importlib
from types import SimpleNamespace

from fastapi.testclient import TestClient

RELEASE_ID = "kg-sha256-" + "a" * 64


class _Database:
    def is_connected(self) -> bool:
        return True

    async def fetchrow(self, _query: str) -> dict[str, int]:
        return {"n": 3}


class _Analytics:
    def get_release_metadata(self) -> dict[str, str | int]:
        return {
            "release_id": RELEASE_ID,
            "served_total_nodes": 3,
            "served_total_edges": 2,
            "served_total_asserted_edges": 1,
        }


def _client(monkeypatch) -> TestClient:
    monkeypatch.setenv("JWT_SECRET_KEY", "a" * 64)
    main = importlib.import_module("backend.main")
    services = SimpleNamespace(
        db=_Database(),
        analytics=_Analytics(),
        graphrag=SimpleNamespace(_kg_loaded=True),
        kg_source="database",
    )
    monkeypatch.setattr(main.deps, "services", services)
    return TestClient(main.create_app(), raise_server_exceptions=True)


def test_health_exposes_and_accepts_the_served_release(monkeypatch) -> None:
    response = _client(monkeypatch).get(
        "/api/health", params={"expected_release_id": RELEASE_ID}
    )

    assert response.status_code == 200
    assert response.json()["release_id"] == RELEASE_ID
    assert response.headers["x-eleutheria-kg-release-id"] == RELEASE_ID
    assert response.json()["served_total_nodes"] == 3
    assert response.json()["served_total_edges"] == 2


def test_health_rejects_a_different_release_before_cutover(monkeypatch) -> None:
    response = _client(monkeypatch).get(
        "/api/health", params={"expected_release_id": "kg-sha256-" + "b" * 64}
    )

    assert response.status_code == 409
    assert response.json()["detail"] == {
        "code": "kg_release_mismatch",
        "requested_release_id": "kg-sha256-" + "b" * 64,
        "served_release_id": RELEASE_ID,
    }


def test_cors_allows_only_the_eleutheria_pages_preview_family(monkeypatch) -> None:
    client = _client(monkeypatch)
    allowed = client.options(
        "/api/health",
        headers={
            "Origin": "https://ef8c8d0c.eleutheria.pages.dev",
            "Access-Control-Request-Method": "GET",
        },
    )
    rejected = client.options(
        "/api/health",
        headers={
            "Origin": "https://eleutheria.pages.dev.attacker.example",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert allowed.status_code == 200
    assert (
        allowed.headers["access-control-allow-origin"]
        == "https://ef8c8d0c.eleutheria.pages.dev"
    )
    assert "access-control-allow-origin" not in rejected.headers
