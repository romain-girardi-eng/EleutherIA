"""Tests for provenance handling in create_passage_translations."""

from __future__ import annotations

import pytest
from database.scripts.create_passage_translations import (
    build_en_metadata,
    resolve_source_model,
)


class TestResolveSourceModel:
    def test_entry_source_model_wins_over_default(self):
        entry = {"node_id": "passage_x", "source_model": "gemini-2.5-flash-batch"}
        assert resolve_source_model(entry, "other-model") == "gemini-2.5-flash-batch"

    def test_falls_back_to_default_model(self):
        entry = {"node_id": "passage_x", "translation": "..."}
        assert resolve_source_model(entry, "gemini-2.5-flash-batch") == (
            "gemini-2.5-flash-batch"
        )

    def test_missing_model_raises(self):
        with pytest.raises(ValueError, match="source_model"):
            resolve_source_model({"node_id": "passage_x"}, None)


class TestBuildEnMetadata:
    def test_provenance_fields_use_resolved_model(self):
        meta = build_en_metadata(
            "passage_x",
            {"language": "grc", "work_title": "De Fato", "author": "Alexander"},
            "gemini-2.5-flash-batch",
        )
        assert meta["source_model"] == "gemini-2.5-flash-batch"
        assert meta["translation_type"] == "machine"
        assert meta["translation_source"] == "AI batch: gemini-2.5-flash-batch"
        assert meta["source_language"] == "grc"
        assert meta["original_node_id"] == "passage_x"
        assert meta["auto_generated"] is True

    def test_carries_over_optional_fields(self):
        meta = build_en_metadata(
            "passage_x",
            {"canonical_ref": "1.1", "db_passage_id": "abc"},
            "gemini-2.5-flash-batch",
        )
        assert meta["canonical_ref"] == "1.1"
        assert meta["source_passage_id"] == "abc"
