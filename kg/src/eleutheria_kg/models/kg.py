"""
Pydantic models for knowledge graph entities.

These models represent nodes and edges in the EleutherIA knowledge graph.
"""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class KGNode(BaseModel):
    """
    A node in the knowledge graph.

    Nodes represent entities like philosophers, concepts, arguments, and works.
    """

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Unique node identifier")
    label: str = Field(..., description="Display label")
    type: str = Field(..., description="Node type (Person, Concept, Argument, etc.)")
    description: str | None = Field(None, description="Full description")
    period: str | None = Field(None, description="Historical period")
    school: str | None = Field(None, description="Philosophical school")
    role: str | None = Field(None, description="Role in the knowledge graph")
    source: str | None = Field(None, description="Data source")
    metadata: dict[str, Any] | None = Field(None, description="Additional metadata")

    # For visualization
    community_id: int | None = Field(None, description="Community assignment")
    centrality: float | None = Field(None, description="Centrality score")


class KGEdge(BaseModel):
    """
    An edge in the knowledge graph.

    Edges represent relationships between nodes (argues_for, influences, etc.).
    """

    model_config = ConfigDict(from_attributes=True)

    id: str | None = Field(None, description="Edge identifier")
    source: str = Field(..., description="Source node ID")
    target: str = Field(..., description="Target node ID")
    relation: str = Field(..., description="Relationship type")
    description: str | None = Field(None, description="Relationship description")
    weight: float = Field(1.0, ge=0.0, description="Edge weight")
    metadata: dict[str, Any] | None = Field(None, description="Additional metadata")


class Community(BaseModel):
    """
    A community of related nodes.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="Community ID")
    name: str | None = Field(None, description="Community name/label")
    color: str = Field(..., description="Display color (hex)")
    node_count: int = Field(..., ge=0, description="Number of nodes")
    node_ids: list[str] = Field(default_factory=list, description="Member node IDs")
    central_nodes: list[str] = Field(
        default_factory=list, description="Most central nodes in community"
    )


class CentralityResult(BaseModel):
    """
    Centrality calculation result.
    """

    model_config = ConfigDict(from_attributes=True)

    metric: str = Field(..., description="Centrality metric used")
    scores: dict[str, float] = Field(..., description="Node ID to score mapping")
    top_nodes: list[dict[str, Any]] = Field(
        default_factory=list, description="Top nodes by centrality"
    )


class KGStatistics(BaseModel):
    """
    Knowledge graph statistics.
    """

    model_config = ConfigDict(from_attributes=True)

    total_nodes: int = Field(..., ge=0)
    total_edges: int = Field(..., ge=0)
    density: float = Field(..., ge=0.0, le=1.0)
    connected_components: int = Field(..., ge=0)
    avg_degree: float = Field(..., ge=0.0)
    node_types: dict[str, int] = Field(default_factory=dict)
    edge_types: dict[str, int] = Field(default_factory=dict)
