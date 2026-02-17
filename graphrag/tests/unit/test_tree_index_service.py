"""Tests for PageIndex-inspired tree index service."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from eleutheria_graphrag.services.tree_index import (
    TreeIndexService,
    TreeNode,
    WorkTreeIndex,
)


class TestTreeNode:
    def test_leaf_node(self):
        n = TreeNode(
            node_id="df_001", title="Introduction",
            start_passage=1, end_passage=5,
            summary="Alexander introduces the debate...",
        )
        assert n.nodes == []
        assert n.start_passage == 1

    def test_nested_node(self):
        child = TreeNode(
            node_id="df_002", title="The Stoic Position",
            start_passage=1, end_passage=3,
            summary="Chrysippus's argument...",
        )
        parent = TreeNode(
            node_id="df_001", title="Book I",
            start_passage=1, end_passage=10,
            summary="Overview...",
            nodes=[child],
        )
        assert len(parent.nodes) == 1
        assert parent.nodes[0].node_id == "df_002"


class TestWorkTreeIndex:
    def test_construction(self):
        idx = WorkTreeIndex(
            work_id="de_fato",
            title="De Fato",
            author="Alexander of Aphrodisias",
            period="Imperial",
            total_passages=47,
            nodes=[],
        )
        assert idx.work_id == "de_fato"
        assert idx.total_passages == 47

    def test_serialization_roundtrip(self):
        idx = WorkTreeIndex(
            work_id="de_fato",
            title="De Fato",
            author="Alexander",
            total_passages=10,
            nodes=[
                TreeNode(
                    node_id="001", title="Intro",
                    start_passage=1, end_passage=5,
                    summary="Introduction...",
                )
            ],
        )
        data = idx.model_dump()
        restored = WorkTreeIndex.model_validate(data)
        assert restored.nodes[0].node_id == "001"


class TestTreeIndexService:
    @pytest.mark.asyncio
    async def test_load_indices_empty(self):
        db = MagicMock()
        db.fetch = AsyncMock(return_value=[])
        svc = TreeIndexService(db=db)
        result = await svc.load_indices([])
        assert result == []

    @pytest.mark.asyncio
    async def test_load_indices_returns_parsed(self):
        tree_data = WorkTreeIndex(
            work_id="de_fato", title="De Fato", author="Alexander",
            total_passages=10, nodes=[],
        ).model_dump()
        db = MagicMock()
        db.fetch = AsyncMock(return_value=[
            {"work_id": "de_fato", "tree_index": tree_data}
        ])
        svc = TreeIndexService(db=db)
        result = await svc.load_indices(["de_fato"])
        assert len(result) == 1
        assert isinstance(result[0], WorkTreeIndex)
        assert result[0].work_id == "de_fato"

    @pytest.mark.asyncio
    async def test_extract_passages(self):
        db = MagicMock()
        db.fetch = AsyncMock(return_value=[
            {"passage_id": "p1", "text_content": "Chrysippus argues...",
             "canonical_ref": "1.1", "title": "De Fato", "author": "Alexander"},
        ])
        svc = TreeIndexService(db=db)
        idx = WorkTreeIndex(
            work_id="de_fato", title="De Fato", author="Alexander",
            total_passages=10,
            nodes=[TreeNode(
                node_id="001", title="Intro",
                start_passage=1, end_passage=5,
                summary="Introduction...",
            )],
        )
        result = await svc.extract_passages(idx, ["001"])
        assert len(result) >= 1
