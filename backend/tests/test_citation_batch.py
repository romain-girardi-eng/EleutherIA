from __future__ import annotations

import json
from typing import Any

import pytest

from backend.routes.works_extras import (
    BatchCitationsRequest,
    batch_fetch_citations,
)


class _CitationDb:
    def __init__(self, *, related: bool) -> None:
        self.related = related
        self.citation_sql = ""

    async def fetch(self, sql: str, *_args: Any) -> list[dict[str, Any]]:
        self.citation_sql = sql
        return []

    async def fetchrow(self, _sql: str, node_id: str) -> dict[str, Any]:
        return {
            "label": "Related passage",
            "type": "passage",
            "description": "TEXT MUST NOT LEAK" if self.related else "Exact KG text",
            "metadata": json.dumps(
                {"parity_status": "related_not_exact_twin"} if self.related else {}
            ),
            "node_id": node_id,
        }


@pytest.mark.asyncio
async def test_batch_citations_refuses_non_exact_passage_text() -> None:
    db = _CitationDb(related=True)
    rows = await batch_fetch_citations(
        BatchCitationsRequest(ids=["passage_related"]), db
    )

    assert "pc.citation_type = 'snapshot_passage_node'" in db.citation_sql
    assert rows[0]["text"] == ""
    assert rows[0]["passage_ref"] == "Related passage"


@pytest.mark.asyncio
async def test_batch_citations_keeps_normal_kg_fallback() -> None:
    db = _CitationDb(related=False)
    rows = await batch_fetch_citations(BatchCitationsRequest(ids=["concept_x"]), db)

    assert rows[0]["text"] == "Exact KG text"
