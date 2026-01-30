"""
Pydantic models for GraphRAG queries and responses.
"""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class QueryRequest(BaseModel):
    """Request model for GraphRAG query."""

    model_config = ConfigDict(from_attributes=True)

    question: str = Field(..., min_length=3, description="User question")
    semantic_k: int = Field(10, ge=1, le=50, description="Semantic search results")
    graph_depth: int = Field(2, ge=1, le=4, description="Graph traversal depth")
    max_context_nodes: int = Field(30, ge=5, le=100, description="Max nodes in context")
    include_passages: bool = Field(True, description="Include ancient passages")
    stream: bool = Field(False, description="Enable streaming response")


class Citation(BaseModel):
    """A citation reference in the answer."""

    model_config = ConfigDict(from_attributes=True)

    ref: str = Field(..., description="Reference marker (e.g., '1', 'P2')")
    type: str = Field(..., description="Citation type: 'node' or 'passage'")
    id: str = Field(..., description="Node or passage ID")
    label: str = Field(..., description="Display label")
    confidence: float | None = Field(None, ge=0.0, le=1.0, description="Citation confidence")


class QueryResponse(BaseModel):
    """Response model for GraphRAG query."""

    model_config = ConfigDict(from_attributes=True)

    answer: str = Field(..., description="Generated answer")
    question: str = Field(..., description="Original question")
    citations: list[Citation] = Field(default_factory=list, description="Extracted citations")
    seed_nodes: list[str] = Field(default_factory=list, description="Semantic search seed nodes")
    context_nodes: list[str] = Field(default_factory=list, description="All context nodes")
    passages_used: int = Field(0, ge=0, description="Number of passages in context")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
