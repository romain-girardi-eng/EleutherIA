import json
from unittest.mock import MagicMock, patch

from eleutheria_kg.services.snapshot import (
    load_kg_snapshot,
    snapshot_available,
    snapshot_public_url,
    upload_snapshot_dir,
    upload_snapshot_file,
)


def test_load_kg_snapshot_normalizes_jsonl(tmp_path):
    snapshot_dir = tmp_path / "kg"
    snapshot_dir.mkdir()
    (snapshot_dir / "nodes.jsonl").write_text(
        json.dumps(
            {
                "node_id": "concept_fate",
                "label": "Fate",
                "type": "concept",
                "metadata": '{"school_affiliation": "Stoicism"}',
            }
        )
        + "\n"
        + json.dumps(
            {
                "id": "passage_1",
                "label": "Passage",
                "type": "passage",
                "metadata": {"author": "Plutarch"},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (snapshot_dir / "edges.jsonl").write_text(
        json.dumps(
            {
                "source_id": "concept_fate",
                "target_id": "passage_1",
                "relation": "evidenced_by",
                "metadata": {"weight": "0.8"},
            }
        )
        + "\n",
        encoding="utf-8",
    )

    assert snapshot_available(snapshot_dir)
    kg = load_kg_snapshot(snapshot_dir)

    assert kg["nodes"][0]["id"] == "concept_fate"
    assert kg["nodes"][0]["school"] == "Stoicism"
    assert kg["edges"][0]["source"] == "concept_fate"
    assert kg["edges"][0]["target"] == "passage_1"
    assert kg["edges"][0]["weight"] == 0.8


def test_upload_snapshot_file_no_config(monkeypatch, tmp_path):
    """No Supabase env => upload returns False without raising."""
    for var in (
        "ELEUTHERIA_SUPABASE_STORAGE_URL",
        "ELEUTHERIA_SUPABASE_STORAGE_KEY",
        "SUPABASE_URL",
        "SUPABASE_SERVICE_KEY",
        "SUPABASE_SERVICE_ROLE_KEY",
    ):
        monkeypatch.delenv(var, raising=False)

    file_path = tmp_path / "nodes.jsonl"
    file_path.write_text("{}\n", encoding="utf-8")

    assert upload_snapshot_file(file_path) is False


def test_upload_snapshot_file_uploads_with_upsert(monkeypatch, tmp_path):
    monkeypatch.setenv("ELEUTHERIA_SUPABASE_STORAGE_URL", "https://example.supabase.co")
    monkeypatch.setenv("ELEUTHERIA_SUPABASE_STORAGE_KEY", "service-role-key")
    monkeypatch.setenv("KG_SNAPSHOT_BUCKET", "kg-snapshots")

    file_path = tmp_path / "nodes.jsonl"
    file_path.write_text('{"id":"x"}\n', encoding="utf-8")

    fake_response = MagicMock()
    fake_response.status_code = 200
    fake_response.text = ""

    with patch("httpx.put", return_value=fake_response) as fake_put:
        ok = upload_snapshot_file(file_path)

    assert ok is True
    fake_put.assert_called_once()
    args, kwargs = fake_put.call_args
    assert args[0].endswith("/storage/v1/object/kg-snapshots/nodes.jsonl")
    headers = kwargs["headers"]
    assert headers["x-upsert"] == "true"
    assert headers["Authorization"] == "Bearer service-role-key"
    assert headers["Content-Type"] == "application/x-ndjson"


def test_upload_snapshot_file_returns_false_on_http_error(monkeypatch, tmp_path):
    monkeypatch.setenv("ELEUTHERIA_SUPABASE_STORAGE_URL", "https://example.supabase.co")
    monkeypatch.setenv("ELEUTHERIA_SUPABASE_STORAGE_KEY", "service-role-key")

    file_path = tmp_path / "edges.jsonl"
    file_path.write_text("{}\n", encoding="utf-8")

    fake_response = MagicMock()
    fake_response.status_code = 500
    fake_response.text = "boom"

    with patch("httpx.put", return_value=fake_response):
        assert upload_snapshot_file(file_path) is False


def test_upload_snapshot_dir_iterates_files(monkeypatch, tmp_path):
    monkeypatch.setenv("ELEUTHERIA_SUPABASE_STORAGE_URL", "https://example.supabase.co")
    monkeypatch.setenv("ELEUTHERIA_SUPABASE_STORAGE_KEY", "service-role-key")

    snapshot_dir = tmp_path / "kg"
    snapshot_dir.mkdir()
    (snapshot_dir / "nodes.jsonl").write_text("{}\n", encoding="utf-8")
    (snapshot_dir / "edges.jsonl").write_text("{}\n", encoding="utf-8")
    (snapshot_dir / "stats.json").write_text("{}\n", encoding="utf-8")
    (snapshot_dir / "nested").mkdir()  # subdirs are ignored

    fake_response = MagicMock()
    fake_response.status_code = 200
    fake_response.text = ""

    with patch("httpx.put", return_value=fake_response) as fake_put:
        results = upload_snapshot_dir(snapshot_dir)

    assert set(results) == {"nodes.jsonl", "edges.jsonl", "stats.json"}
    assert all(results.values())
    assert fake_put.call_count == 3


def test_snapshot_public_url(monkeypatch):
    monkeypatch.setenv("ELEUTHERIA_SUPABASE_STORAGE_URL", "https://example.supabase.co")
    monkeypatch.setenv("ELEUTHERIA_SUPABASE_STORAGE_KEY", "service-role-key")
    monkeypatch.delenv("KG_SNAPSHOT_BUCKET", raising=False)

    assert (
        snapshot_public_url("nodes.jsonl")
        == "https://example.supabase.co/storage/v1/object/public/kg-snapshots/nodes.jsonl"
    )


def test_snapshot_public_url_none_when_unconfigured(monkeypatch):
    for var in (
        "ELEUTHERIA_SUPABASE_STORAGE_URL",
        "ELEUTHERIA_SUPABASE_STORAGE_KEY",
        "SUPABASE_URL",
        "SUPABASE_SERVICE_KEY",
        "SUPABASE_SERVICE_ROLE_KEY",
    ):
        monkeypatch.delenv(var, raising=False)

    assert snapshot_public_url("nodes.jsonl") is None
