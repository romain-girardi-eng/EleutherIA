"""Regression: /kg/nodes?search= must tolerate null label/description.

The live KG contains nodes whose ``description`` key is present but null;
``n.get("description", "").lower()`` raised AttributeError on them and the
endpoint returned 500 for any search query.
"""

import pytest

pytest.importorskip("fastapi")

from fastapi import Response  # noqa: E402

from eleutheria_kg.api.routes import list_nodes  # noqa: E402
from eleutheria_kg.services.analytics import KGAnalytics  # noqa: E402

NODES = [
    {"id": "a", "type": "concept", "label": "Fate", "description": None},
    {"id": "b", "type": "concept", "label": None, "description": "on fate"},
    {"id": "c", "type": "concept", "label": "Virtue", "description": "aretê"},
]


@pytest.mark.asyncio
async def test_search_skips_null_label_and_description() -> None:
    analytics = KGAnalytics({"nodes": NODES, "edges": []})
    result = await list_nodes(
        response=Response(),
        analytics=analytics,
        node_type=None,
        period=None,
        school=None,
        search="fate",
        limit=100,
        offset=0,
    )
    assert [n["id"] for n in result] == ["a", "b"]
