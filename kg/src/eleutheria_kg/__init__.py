"""
EleutherIA Knowledge Graph Package

Knowledge graph framework for ancient philosophy on free will.
"""

from eleutheria_kg.services.analytics import KGAnalytics
from eleutheria_kg.services.qdrant import QdrantService
from eleutheria_kg.services.cache import KGCache
from eleutheria_kg.models.kg import KGNode, KGEdge

__version__ = "2.0.0"
__all__ = [
    "KGAnalytics",
    "QdrantService",
    "KGCache",
    "KGNode",
    "KGEdge",
]
