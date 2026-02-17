"""Tests for FetchPassagesAndLayer FSM node."""

import pytest

from eleutheria_graphrag.agents.graph_nodes import (
    FetchPassagesAndLayer,
    SearchSecondarySources,
    Synthesize,
)
from eleutheria_graphrag.agents.pipeline_config import QueryType
from eleutheria_graphrag.agents.state import Evidence, EvidenceLayer, RAGState

from .conftest import make_ctx, make_deps


class TestFetchPassagesAndLayer:
    @pytest.mark.asyncio
    async def test_routes_specific_entity_to_synthesize(self):
        """specific_entity → Synthesize (no secondary search needed)."""
        deps = make_deps()
        state = RAGState(question="Who was Chrysippus?")
        state.query_type = QueryType.SPECIFIC_ENTITY
        state.primary_evidence = [Evidence(id="n1", label="Chrysippus", type="Person")]
        ctx = make_ctx(state, deps)

        node = FetchPassagesAndLayer()
        result = await node.run(ctx)

        assert isinstance(result, Synthesize)

    @pytest.mark.asyncio
    async def test_routes_global_abstract_to_synthesize(self):
        """global_abstract → Synthesize (fetches passages but no secondary search)."""
        deps = make_deps()
        state = RAGState(question="What is Stoic fate?")
        state.query_type = QueryType.GLOBAL_ABSTRACT
        state.primary_evidence = [Evidence(id="n1", label="Fate", type="Concept")]
        ctx = make_ctx(state, deps)

        node = FetchPassagesAndLayer()
        result = await node.run(ctx)

        assert isinstance(result, Synthesize)

    @pytest.mark.asyncio
    async def test_routes_multi_hop_to_secondary_sources(self):
        """multi_hop → SearchSecondarySources (needs interpretive sources)."""
        deps = make_deps()
        state = RAGState(question="How did Stoic fate evolve?")
        state.query_type = QueryType.MULTI_HOP
        state.primary_evidence = [Evidence(id="n1", label="Fate", type="Concept")]
        ctx = make_ctx(state, deps)

        node = FetchPassagesAndLayer()
        result = await node.run(ctx)

        assert isinstance(result, SearchSecondarySources)

    @pytest.mark.asyncio
    async def test_routes_comparative_to_secondary_sources(self):
        """comparative → SearchSecondarySources."""
        deps = make_deps()
        state = RAGState(question="Compare Stoic and Epicurean fate")
        state.query_type = QueryType.COMPARATIVE
        state.primary_evidence = [Evidence(id="n1", label="Fate", type="Concept")]
        ctx = make_ctx(state, deps)

        node = FetchPassagesAndLayer()
        result = await node.run(ctx)

        assert isinstance(result, SearchSecondarySources)

    @pytest.mark.asyncio
    async def test_fetches_passages_from_db(self):
        """Node should fetch passages via db.fetch."""
        db_passages = [
            {
                "passage_id": 42,
                "text_content": "The Stoics say fate...",
                "canonical_ref": "SVF 2.912",
                "title": "SVF II",
                "author": "Chrysippus",
                "confidence": 0.9,
            }
        ]
        deps = make_deps(db_fetch_results=db_passages)
        state = RAGState(question="test")
        state.query_type = QueryType.SPECIFIC_ENTITY
        state.primary_evidence = [Evidence(id="chrysippus", label="Chrysippus", type="Person")]
        ctx = make_ctx(state, deps)

        node = FetchPassagesAndLayer()
        result = await node.run(ctx)

        assert isinstance(result, Synthesize)
        # Passages should be added to primary evidence
        passage_evidence = [e for e in ctx.state.primary_evidence if e.type == "passage"]
        assert len(passage_evidence) == 1
        assert ctx.state.passages_used == 1

    @pytest.mark.asyncio
    async def test_context_built(self):
        """FetchPassagesAndLayer should set accumulated_context."""
        deps = make_deps()
        state = RAGState(question="test")
        state.query_type = QueryType.SPECIFIC_ENTITY
        state.primary_evidence = [
            Evidence(id="n1", label="Chrysippus", type="Person", description="Stoic philosopher")
        ]
        ctx = make_ctx(state, deps)

        node = FetchPassagesAndLayer()
        await node.run(ctx)

        assert len(ctx.state.accumulated_context) > 0
