"""
EleutherIA Knowledge Graph Package

Knowledge graph framework for ancient philosophy on free will.
"""

from eleutheria_kg.models.kg import KGEdge, KGNode

__version__ = "2.0.0"
__all__ = [
    "KGAnalytics",
    "KGCache",
    "KGNode",
    "KGEdge",
]


def __getattr__(name: str):
    """Lazy-load optional service classes.

    Semantic tooling imports ``eleutheria_kg.semantic`` without needing
    NetworkX or cache backends. Importing those services eagerly makes
    RDF/SHACL command-line tools fail in minimal CI environments.
    """
    if name == "KGAnalytics":
        from eleutheria_kg.services.analytics import KGAnalytics

        return KGAnalytics
    if name == "KGCache":
        from eleutheria_kg.services.cache import KGCache

        return KGCache
    raise AttributeError(f"module 'eleutheria_kg' has no attribute {name!r}")
