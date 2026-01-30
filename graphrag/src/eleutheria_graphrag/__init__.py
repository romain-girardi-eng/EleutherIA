"""
EleutherIA GraphRAG Package

Graph-based Retrieval-Augmented Generation for scholarly Q&A.
"""

from eleutheria_graphrag.services.graphrag_service import GraphRAGService
from eleutheria_graphrag.services.llm_service import LLMService, ModelProvider
from eleutheria_graphrag.models.query import QueryRequest, QueryResponse

__version__ = "2.0.0"
__all__ = [
    "GraphRAGService",
    "LLMService",
    "ModelProvider",
    "QueryRequest",
    "QueryResponse",
]
