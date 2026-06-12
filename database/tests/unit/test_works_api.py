"""Tests for translation provenance labeling in the works API."""

from __future__ import annotations

from uuid import uuid4

import pytest

from eleutheria_database.api.works import derive_translation_source, list_passages


class TestDeriveTranslationSource:
    def test_no_translation_node_returns_none(self):
        assert derive_translation_source(False, None) is None

    def test_machine_metadata_labels_ai_generated(self):
        assert derive_translation_source(True, "machine") == "ai_generated"

    def test_missing_metadata_falls_back_to_unknown_not_scholarly(self):
        assert derive_translation_source(True, None) == "unknown"

    def test_explicit_type_passes_through(self):
        assert derive_translation_source(True, "scholarly") == "scholarly"


class _FakeDb:
    def __init__(self, rows: list[dict]) -> None:
        self.rows = rows
        self.last_sql: str | None = None

    async def fetch(self, sql: str, *_params) -> list[dict]:
        self.last_sql = sql
        return self.rows

    async def fetchrow(self, sql: str, *_params) -> dict:
        return {"total": len(self.rows)}


@pytest.mark.asyncio
async def test_list_passages_labels_translations_from_metadata():
    rows = [
        {
            "passage_id": str(uuid4()),
            "text_content": "original text",
            "translation_text": "machine english",
            "translation_language": "en",
            "translation_node_id": "passage_x_en",
            "translation_type": "machine",
            "kg_node_count": 1,
        },
        {
            "passage_id": str(uuid4()),
            "text_content": "original text",
            "translation_text": "english of unknown origin",
            "translation_language": "en",
            "translation_node_id": "passage_y_en",
            "translation_type": None,
            "kg_node_count": 1,
        },
        {
            "passage_id": str(uuid4()),
            "text_content": "original text",
            "translation_text": None,
            "translation_language": None,
            "translation_node_id": None,
            "translation_type": None,
            "kg_node_count": 0,
        },
    ]
    db = _FakeDb(rows)

    work_id = uuid4()
    response = await list_passages(
        work_id=work_id,
        db=db,
        book=None,
        chapter=None,
        include_translations=True,
        limit=100,
        offset=0,
    )

    # Readers paginate against {"passages": [...], "total": N}
    assert response["work_id"] == str(work_id)
    assert response["total"] == len(rows)
    result = response["passages"]

    assert result[0]["translation_source"] == "ai_generated"
    assert result[1]["translation_source"] == "unknown"
    assert result[2]["translation_source"] is None
    # The old node_id heuristic mislabeled every _en node as scholarly.
    assert db.last_sql is not None
    assert "_ai_" not in db.last_sql
