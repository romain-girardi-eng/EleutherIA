"""CorpusMap tools — search and read source-attributed Entity Pages.

Registered only when ``ELEUTHERIA_CORPUSMAP`` is on (see
``eleutheria_graphrag.corpusmap.runtime``).
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from eleutheria_graphrag.agents.dependencies import Deps
from eleutheria_graphrag.corpusmap.runtime import get_corpus_map


class EntityPageHit(BaseModel):
    entity_id: str
    label: str
    type: str
    linked_documents: int


class SearchEntityPagesResult(BaseModel):
    pages: list[EntityPageHit]


class EntityPageResult(BaseModel):
    entity_id: str
    found: bool = True
    page: str = ""


class SearchEntityPagesTool:
    """Find Entity Pages (persons, concepts, works, debates) by name, alias and content."""

    def __init__(self, deps: Deps) -> None:
        self._deps = deps

    @property
    def name(self) -> str:
        return "search_entity_pages"

    @property
    def description(self) -> str:
        return (
            "Search the CorpusMap: one Entity Page per person, concept, work, school or "
            "debate, ranked by name, aliases and the facts its linked documents state. "
            "Use it to find the right entity before read_entity_page."
        )

    @property
    def parameters_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Names, terms or a sub-question",
                },
                "limit": {"type": "integer", "minimum": 1, "maximum": 20, "default": 8},
            },
            "required": ["query"],
        }

    async def execute(self, args: dict[str, Any]) -> SearchEntityPagesResult:
        cmap = get_corpus_map(self._deps)
        if cmap is None:
            return SearchEntityPagesResult(pages=[])
        limit = max(1, min(int(args.get("limit") or 8), 20))
        return SearchEntityPagesResult(
            pages=[
                EntityPageHit(
                    entity_id=eid,
                    label=cmap.pages[eid].label,
                    type=cmap.pages[eid].type,
                    linked_documents=len(cmap.pages[eid].linked_documents),
                )
                for eid, _ in cmap.search_pages(str(args["query"]), k=limit)
            ]
        )


class ReadEntityPageTool:
    """Read one Entity Page: overview, aliases, source-tagged facts, evidence passages, holdings."""

    def __init__(self, deps: Deps) -> None:
        self._deps = deps

    @property
    def name(self) -> str:
        return "read_entity_page"

    @property
    def description(self) -> str:
        return (
            "Read the Entity Page of a person, concept, work, school or debate. It gathers "
            "what every linked document says about the entity, each fact tagged with its "
            "source document id, plus evidence passages and corpus holdings. Pass the "
            "question as focus to rank the facts. Open the listed ids with get_node_detail "
            "or read_passages before citing them."
        )

    @property
    def parameters_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "entity_id": {"type": "string", "description": "Entity node id"},
                "focus": {
                    "type": "string",
                    "description": "Question or sub-question used to rank facts",
                },
            },
            "required": ["entity_id"],
        }

    async def execute(self, args: dict[str, Any]) -> EntityPageResult:
        entity_id = str(args["entity_id"])
        cmap = get_corpus_map(self._deps)
        if cmap is None or entity_id not in cmap.pages:
            return EntityPageResult(entity_id=entity_id, found=False)
        return EntityPageResult(
            entity_id=entity_id, page=cmap.render(entity_id, focus=args.get("focus"))
        )
