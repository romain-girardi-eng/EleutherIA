"""Shared fixtures for agent tool tests."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock

import pytest

from eleutheria_graphrag.agents.dependencies import Deps


def _build_mock_deps() -> Deps:
    """Build a Deps with in-memory KG data for testing."""
    # Minimal KG: 8 nodes, ~15 edges
    node_lookup = {
        "person_origen": {
            "id": "person_origen",
            "label": "Origen of Alexandria",
            "type": "person",
            "description": "Early Christian theologian (c. 185-254 CE) who developed systematic arguments for free will",
            "period": "Roman Imperial",
            "school": "Christian Platonism",
            "metadata": {"birth": "c. 185 CE", "death": "c. 254 CE"},
        },
        "person_plato": {
            "id": "person_plato",
            "label": "Plato",
            "type": "person",
            "description": "Classical Greek philosopher, founder of the Academy",
            "period": "Classical Greek",
            "school": "Platonism",
            "metadata": {"birth": "c. 428 BCE", "death": "c. 348 BCE"},
        },
        "person_chrysippus": {
            "id": "person_chrysippus",
            "label": "Chrysippus of Soli",
            "type": "person",
            "description": "Third head of the Stoic school, systematized Stoic logic and physics",
            "period": "Hellenistic",
            "school": "Stoicism",
            "metadata": {},
        },
        "concept_autexousion": {
            "id": "concept_autexousion",
            "label": "Autexousion (self-determination)",
            "type": "concept",
            "description": "The power of self-determination, central to patristic free will theory",
            "period": "Roman Imperial",
            "school": None,
            "metadata": {},
        },
        "concept_fate": {
            "id": "concept_fate",
            "label": "Fate (Heimarmene)",
            "type": "concept",
            "description": "The Stoic concept of universal causal determinism",
            "period": "Hellenistic",
            "school": "Stoicism",
            "metadata": {},
        },
        "work_de_principiis": {
            "id": "work_de_principiis",
            "label": "De Principiis",
            "type": "work",
            "description": "Origen's systematic theological work, Book III on free will",
            "period": "Roman Imperial",
            "school": None,
            "metadata": {"author": "Origen"},
        },
        "school_middle_platonism": {
            "id": "school_middle_platonism",
            "label": "Middle Platonism",
            "type": "school",
            "description": "Philosophical movement (1st c. BCE - 3rd c. CE) bridging Plato and Neoplatonism",
            "period": "Roman Imperial",
            "school": None,
            "metadata": {},
        },
        "argument_cylinder": {
            "id": "argument_cylinder",
            "label": "Cylinder argument",
            "type": "argument",
            "description": "Chrysippus's analogy of the cylinder to explain co-fated causes",
            "period": "Hellenistic",
            "school": "Stoicism",
            "metadata": {},
        },
    }

    outgoing_edges: dict[str, list[dict[str, Any]]] = {
        "person_origen": [
            {
                "source": "person_origen",
                "target": "concept_autexousion",
                "relation": "discusses",
                "weight": 1.0,
                "metadata": {},
                "description": "",
            },
            {
                "source": "person_origen",
                "target": "work_de_principiis",
                "relation": "authored",
                "weight": 1.0,
                "metadata": {},
                "description": "",
            },
            {
                "source": "person_origen",
                "target": "school_middle_platonism",
                "relation": "influenced_by",
                "weight": 0.8,
                "metadata": {},
                "description": "",
            },
        ],
        "person_plato": [
            {
                "source": "person_plato",
                "target": "concept_fate",
                "relation": "discusses",
                "weight": 0.5,
                "metadata": {},
                "description": "",
            },
        ],
        "person_chrysippus": [
            {
                "source": "person_chrysippus",
                "target": "concept_fate",
                "relation": "discusses",
                "weight": 1.0,
                "metadata": {},
                "description": "",
            },
            {
                "source": "person_chrysippus",
                "target": "argument_cylinder",
                "relation": "created",
                "weight": 1.0,
                "metadata": {},
                "description": "",
            },
        ],
        "school_middle_platonism": [
            {
                "source": "school_middle_platonism",
                "target": "person_plato",
                "relation": "founded_by",
                "weight": 0.3,
                "metadata": {},
                "description": "",
            },
        ],
    }

    incoming_edges: dict[str, list[dict[str, Any]]] = {
        "concept_autexousion": [
            {
                "source": "person_origen",
                "target": "concept_autexousion",
                "relation": "discusses",
                "weight": 1.0,
                "metadata": {},
                "description": "",
            },
        ],
        "concept_fate": [
            {
                "source": "person_plato",
                "target": "concept_fate",
                "relation": "discusses",
                "weight": 0.5,
                "metadata": {},
                "description": "",
            },
            {
                "source": "person_chrysippus",
                "target": "concept_fate",
                "relation": "discusses",
                "weight": 1.0,
                "metadata": {},
                "description": "",
            },
        ],
        "work_de_principiis": [
            {
                "source": "person_origen",
                "target": "work_de_principiis",
                "relation": "authored",
                "weight": 1.0,
                "metadata": {},
                "description": "",
            },
        ],
        "school_middle_platonism": [
            {
                "source": "person_origen",
                "target": "school_middle_platonism",
                "relation": "influenced_by",
                "weight": 0.8,
                "metadata": {},
                "description": "",
            },
        ],
        "argument_cylinder": [
            {
                "source": "person_chrysippus",
                "target": "argument_cylinder",
                "relation": "created",
                "weight": 1.0,
                "metadata": {},
                "description": "",
            },
        ],
        "person_plato": [
            {
                "source": "school_middle_platonism",
                "target": "person_plato",
                "relation": "founded_by",
                "weight": 0.3,
                "metadata": {},
                "description": "",
            },
        ],
    }

    pagerank_scores = {
        "person_origen": 0.15,
        "person_plato": 0.12,
        "person_chrysippus": 0.10,
        "concept_autexousion": 0.08,
        "concept_fate": 0.11,
        "work_de_principiis": 0.06,
        "school_middle_platonism": 0.09,
        "argument_cylinder": 0.05,
    }

    # Mock services
    db = AsyncMock()
    llm = AsyncMock()

    deps = Deps(
        db=db,
        llm=llm,
        node_lookup=node_lookup,
        outgoing_edges=outgoing_edges,
        incoming_edges=incoming_edges,
        pagerank_scores=pagerank_scores,
    )

    return deps


@pytest.fixture
def mock_deps() -> Deps:
    """Provide mock Deps with a small in-memory KG."""
    return _build_mock_deps()
