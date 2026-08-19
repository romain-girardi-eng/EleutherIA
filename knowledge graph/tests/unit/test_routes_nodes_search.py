"""Regression: /kg/nodes?search= must tolerate null label/description.

The live KG contains nodes whose ``description`` key is present but null;
``n.get("description", "").lower()`` raised AttributeError on them and the
endpoint returned 500 for any search query.
"""

from types import SimpleNamespace

import pytest

pytest.importorskip("fastapi")

from eleutheria_kg.api.routes import list_nodes  # noqa: E402

NODES = [
    {"id": "a", "type": "concept", "label": "Fate", "description": None},
    {"id": "b", "type": "concept", "label": None, "description": "on fate"},
    {"id": "c", "type": "concept", "label": "Virtue", "description": "aretê"},
]


@pytest.mark.asyncio
async def test_search_skips_null_label_and_description() -> None:
    analytics = SimpleNamespace(kg_data={"nodes": NODES})
    result = await list_nodes(
        analytics=analytics,  # type: ignore[arg-type]
        node_type=None,
        period=None,
        school=None,
        search="fate",
        limit=100,
        offset=0,
    )
    assert [n["id"] for n in result] == ["a", "b"]
