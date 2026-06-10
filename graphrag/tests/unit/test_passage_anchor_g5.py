"""G5 regression tests — database passage UUIDs survive into bundles (bug C).

SQLStrategy returns raw ``passages.passage_id`` UUIDs as anchors. The
discovery step used to discard them because they are not KG node ids;
``_select_passage_anchors`` must keep them and
``_fetch_passages_for_nodes`` must resolve them directly against the
``passages`` table.
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from eleutheria_graphrag.agents.graph_nodes import (
    _fetch_passages_for_nodes,
    _select_passage_anchors,
)

from .conftest import make_deps

PASSAGE_UUID = "11111111-2222-3333-4444-555555555555"


class TestSelectPassageAnchors:
    def test_db_passage_uuids_survive(self) -> None:
        node_lookup = {"person_x": {"label": "X", "type": "person"}}
        anchors = _select_passage_anchors(
            valid_anchors=["person_x"],
            strategy_anchors=["person_x", PASSAGE_UUID, "unknown_node"],
            node_lookup=node_lookup,
        )
        assert anchors == ["person_x", PASSAGE_UUID]

    def test_uuid_only_anchors_not_discarded(self) -> None:
        anchors = _select_passage_anchors(
            valid_anchors=[],
            strategy_anchors=[PASSAGE_UUID],
            node_lookup={},
        )
        assert anchors == [PASSAGE_UUID]

    def test_non_uuid_unknown_ids_still_dropped(self) -> None:
        anchors = _select_passage_anchors(
            valid_anchors=[],
            strategy_anchors=["not_a_kg_node", "also-not-a-uuid"],
            node_lookup={},
        )
        assert anchors == []

    def test_caps_at_twelve(self) -> None:
        uuids = [f"{i:08d}-2222-3333-4444-555555555555" for i in range(20)]
        anchors = _select_passage_anchors([], uuids, {})
        assert len(anchors) == 12


class TestFetchPassagesForNodes:
    @pytest.mark.asyncio
    async def test_uuid_anchor_adds_direct_passage_arm(self) -> None:
        deps = make_deps(db_fetch_results=[])
        deps.db.fetch = AsyncMock(return_value=[])

        await _fetch_passages_for_nodes(deps, ["person_x", PASSAGE_UUID], limit=10)

        sql = deps.db.fetch.await_args.args[0]
        args = deps.db.fetch.await_args.args[1:]
        assert "UNION" in sql
        assert "p.passage_id::text IN" in sql
        # All anchors hit the citation arm; the UUID also hits the direct arm.
        assert args == ("person_x", PASSAGE_UUID, PASSAGE_UUID)

    @pytest.mark.asyncio
    async def test_kg_only_anchors_keep_single_arm(self) -> None:
        deps = make_deps(db_fetch_results=[])
        deps.db.fetch = AsyncMock(return_value=[])

        await _fetch_passages_for_nodes(deps, ["person_x"], limit=10)

        sql = deps.db.fetch.await_args.args[0]
        assert "UNION" not in sql
        assert deps.db.fetch.await_args.args[1:] == ("person_x",)

    @pytest.mark.asyncio
    async def test_role_filter_applied(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("ELEUTHERIA_PASSAGE_ROLE_FILTER", raising=False)
        deps = make_deps(db_fetch_results=[])
        deps.db.fetch = AsyncMock(return_value=[])

        await _fetch_passages_for_nodes(deps, [PASSAGE_UUID], limit=10)

        sql = deps.db.fetch.await_args.args[0]
        assert "p.passage_role = 'original'" in sql
